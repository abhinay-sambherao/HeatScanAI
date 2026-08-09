"""Persistent OCR worker process.

Reads length-prefixed PNG frames on stdin, runs PaddleOCR.predict(), and
writes a length-prefixed JSON response on fd 3.

PaddlePaddle on macOS arm64 segfaults from time to time (its thread pool
crashes even while idle). By running OCR in its own process, such a native
crash can only kill this worker - never the API server - and the reader
respawns it on the next request.
"""

import json
import os
import struct
import sys

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from paddleocr import PaddleOCR  # noqa: E402

_HEADER = struct.Struct(">Q")
_ocr = None


def _get_ocr():
    """Lazy-initialize PaddleOCR with a single inference thread.

    Single-threading Paddle is the primary mitigation for its thread-pool
    crashes on Apple Silicon.
    """
    global _ocr
    if _ocr is None:
        import paddle

        try:
            paddle.set_num_threads(1)
        except AttributeError:  # paddle >= 3.0 moved it under base.core
            from paddle.base import core

            core.set_num_threads(1)
        _ocr = PaddleOCR(lang="en")
    return _ocr


def _read_exact(n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sys.stdin.buffer.read(n - len(buf))
        if not chunk:
            return buf
        buf += chunk
    return buf


def _process_frame(png: bytes) -> dict:
    """Decode one PNG frame and run OCR on it."""
    img = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"ok": False, "error": "invalid image data"}
    results = _get_ocr().predict(img)
    texts, confidences = [], []
    for result in results or []:
        for text, score in zip(
            result.get("rec_texts", []), result.get("rec_scores", [])
        ):
            texts.append(text)
            confidences.append(float(score))
    full_text = " ".join(texts)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return {"ok": True, "text": full_text, "confidence": avg_conf}


def main() -> int:
    """Serve OCR requests forever. Exit cleanly on EOF."""
    proto_fd = int(os.environ.get("OCR_PROTO_FD", "3"))
    proto = os.fdopen(proto_fd, "wb")  # protocol channel, separate from stdout logs
    while True:
        header = _read_exact(_HEADER.size)
        if len(header) < _HEADER.size:
            return 0
        (size,) = _HEADER.unpack(header)
        payload = _read_exact(size)
        if len(payload) < size:
            return 0
        try:
            response = _process_frame(payload)
        except Exception as exc:  # keep serving; never die on one bad frame
            response = {"ok": False, "error": str(exc)}
        data = json.dumps(response).encode("utf-8")
        proto.write(_HEADER.pack(len(data)) + data)
        proto.flush()


if __name__ == "__main__":
    sys.exit(main())
