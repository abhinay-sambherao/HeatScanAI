"""Stub OCR worker used by tests to exercise the reader protocol.

Reads length-prefixed frames from stdin and replies on fd 3 with canned
JSON, mirroring app/ocr/ocr_worker.py - without loading PaddleOCR.
"""

import json
import os
import struct
import sys

_HEADER = struct.Struct(">Q")


def _read_exact(n):
    buf = b""
    while len(buf) < n:
        chunk = sys.stdin.buffer.read(n - len(buf))
        if not chunk:
            return buf
        buf += chunk
    return buf


def main():
    proto_fd = int(os.environ.get("OCR_PROTO_FD", "3"))
    proto = os.fdopen(proto_fd, "wb")
    while True:
        header = _read_exact(_HEADER.size)
        if len(header) < _HEADER.size:
            return 0
        (size,) = _HEADER.unpack(header)
        payload = _read_exact(size)
        if len(payload) < size:
            return 0
        data = json.dumps({"ok": True, "text": "Stiebel Eltron WPL 18", "confidence": 0.97}).encode("utf-8")
        proto.write(_HEADER.pack(len(data)) + data)
        proto.flush()


if __name__ == "__main__":
    sys.exit(main())
