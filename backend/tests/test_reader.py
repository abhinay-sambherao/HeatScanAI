"""Tests for the subprocess-isolated OCR reader and Paddle crash isolation."""

import numpy as np
import pytest

import app.ocr.reader as reader


@pytest.fixture(autouse=True)
def stub_worker(monkeypatch):
    """Point the reader at the test stub worker instead of PaddleOCR."""
    reader._teardown()
    monkeypatch.setattr(reader, "_WORKER_MODULE", "tests.stub_ocr_worker")
    yield
    reader._teardown()


def _dummy_image() -> np.ndarray:
    return np.full((64, 128, 3), 255, dtype=np.uint8)


class TestReaderProtocol:
    def test_extract_text_roundtrip(self):
        text, confidence = reader.extract_text(_dummy_image())
        assert text == "Stiebel Eltron WPL 18"
        assert confidence == pytest.approx(0.97)

    def test_worker_respawned_after_crash(self, monkeypatch):
        calls = {"n": 0}

        def flaky_request(png):
            calls["n"] += 1
            if calls["n"] == 1:
                reader._teardown()  # simulate worker dying mid-request
            return {"ok": True, "text": "Vaillant auroCOMPACT", "confidence": 0.9}

        monkeypatch.setattr(reader, "_request", flaky_request)
        text, _ = reader.extract_text(_dummy_image())
        assert text == "Vaillant auroCOMPACT"

    def test_worker_unavailable_raises(self, monkeypatch):
        def dead_request(png):
            reader._teardown()
            return None

        monkeypatch.setattr(reader, "_request", dead_request)
        with pytest.raises(RuntimeError):
            reader.extract_text(_dummy_image())
