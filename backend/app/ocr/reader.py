"""PaddleOCR wrapper for text extraction from preprocessed images.

OCR runs in a persistent subprocess (app.ocr.ocr_worker) so a native crash
in PaddlePaddle - which historically segfaults on macOS arm64 - can never
take down the API server. If the worker dies it is respawned automatically
on the next request.

Wire protocol: length-prefixed (8-byte big-endian) frames. Requests are PNG
bytes on the worker's stdin; responses are UTF-8 JSON on fd 3, so any stray
logs Paddle prints to stdout cannot corrupt the channel.
"""

from __future__ import annotations

import json
import os
import select
import struct
import subprocess
import sys
import threading

import numpy as np

_WORKER_MODULE = "app.ocr.ocr_worker"
_HEADER = struct.Struct(">Q")
_RESPONSE_TIMEOUT = 300.0  # generous: the first call downloads the OCR models

_proc: subprocess.Popen | None = None
_resp_stream = None
_lock = threading.Lock()


def _ensure_proc() -> None:
    """Spawn the worker process if it is not running."""
    global _proc, _resp_stream
    if _proc is not None and _proc.poll() is None:
        return
    read_fd, write_fd = os.pipe()
    env = dict(os.environ)
    env["OCR_PROTO_FD"] = str(write_fd)
    try:
        _proc = subprocess.Popen(
            [sys.executable, "-m", _WORKER_MODULE],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            pass_fds=(write_fd,),
            env=env,
        )
    finally:
        os.close(write_fd)
    _resp_stream = os.fdopen(read_fd, "rb", buffering=0)  # raw: select + read share fd state


def _teardown() -> None:
    """Kill the worker and reset state (called after a worker failure)."""
    global _proc, _resp_stream
    if _proc is not None:
        try:
            _proc.kill()
        except OSError:
            pass
    _proc = None
    if _resp_stream is not None:
        try:
            _resp_stream.close()
        except OSError:
            pass
    _resp_stream = None


def _read_exact(n: int) -> bytes | None:
    """Read exactly n bytes from the response stream, or None on EOF/timeout."""
    chunks = []
    remaining = n
    while remaining > 0:
        ready, _, _ = select.select([_resp_stream], [], [], _RESPONSE_TIMEOUT)
        if not ready:
            return None
        chunk = _resp_stream.read(remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _request(png: bytes) -> dict:
    """Send one image to the worker and await its JSON response.

    Retries once with a freshly spawned worker if the current one fails.
    """
    with _lock:
        try:
            _ensure_proc()
            _send_frame(png)
            response = _recv_frame()
            if response is not None:
                return response
        except Exception:
            pass
        # Worker crashed or closed the pipe: respawn and retry once.
        _teardown()
        _ensure_proc()
        _send_frame(png)
        response = _recv_frame()
        if response is None:
            raise RuntimeError("OCR worker unavailable")
        return response


def _send_frame(png: bytes) -> None:
    _proc.stdin.write(_HEADER.pack(len(png)) + png)
    _proc.stdin.flush()


def _recv_frame() -> dict | None:
    header = _read_exact(_HEADER.size)
    if header is None:
        return None
    (size,) = _HEADER.unpack(header)
    payload = _read_exact(size)
    if payload is None:
        return None
    try:
        return json.loads(payload.decode("utf-8"))
    except ValueError:
        return None


def extract_text(img: np.ndarray) -> tuple:
    """Run PaddleOCR on a preprocessed image.

    Returns:
        Tuple of (full extracted text, average confidence score).
    """
    ok, png = _cv2_imencode(img)
    if not ok:
        return "", 0.0
    response = _request(png)
    if response is None:
        raise RuntimeError("OCR worker unavailable")
    if not response.get("ok"):
        return "", 0.0
    return response.get("text", ""), float(response.get("confidence", 0.0))


def _cv2_imencode(img: np.ndarray) -> tuple:
    """Encode an image array to PNG bytes (cv2 imported lazily)."""
    import cv2

    ok, png = cv2.imencode(".png", img)
    return bool(ok), png.tobytes()
