"""Tests for the OCR pipeline variant merging."""

import cv2
import numpy as np

from app.ocr.pipeline import _merge_ocr_results, run_pipeline


def _image_bytes():
    img = np.full((120, 800, 3), 255, np.uint8)
    return cv2.imencode(".png", img)[1].tobytes()


class TestMergeOcrResults:
    def test_dedupes_lines_and_takes_max_confidence(self):
        text, conf = _merge_ocr_results(
            [("Alpha 123\nBeta 456", 0.9), ("Alpha 123\nGamma 789", 0.8)]
        )
        assert text.count("Alpha 123") == 1
        assert "Beta 456" in text and "Gamma 789" in text
        assert conf == 0.9

    def test_empty_results(self):
        assert _merge_ocr_results([]) == ("", 0.0)


class TestRunPipeline:
    def test_recovers_plate_when_preprocessed_only_reads_table(self, monkeypatch):
        """The motivating case: preprocessed OCR sees only the gas/flue table,
        but the upscaled variant reads the nameplate."""
        table = "II2H3P G20 20 G31 37 C13(X)-C33(X)-C43(X)C53(X) C83X C930"
        plate = "Gas-Brennwertkessel Pyropac AG CH-9466 Sennwald Mod.: WTC-GB 90-A 0063 -weishaupt-"

        calls = {"n": 0}

        def fake_extract(img):
            calls["n"] += 1
            return (table, 0.95) if calls["n"] == 1 else (plate, 0.85)

        monkeypatch.setattr("app.ocr.pipeline.extract_text", fake_extract)
        result = run_pipeline(_image_bytes())

        assert calls["n"] == 3
        assert result["manufacturer"] == "Weishaupt"
        assert result["model"] == "WTC-GB 90-A"
        assert result["fuel_type"] == "gas"
        assert result["confidence"] == 95.0

    def test_fast_path_skips_extra_variants_when_parse_is_sufficient(self, monkeypatch):
        def fake_extract(img):
            return ("Stiebel Eltron WPL 18", 0.97)

        calls = {"n": 0}

        def counting_extract(img):
            calls["n"] += 1
            return fake_extract(img)

        monkeypatch.setattr("app.ocr.pipeline.extract_text", counting_extract)
        result = run_pipeline(_image_bytes())

        assert calls["n"] == 1
        assert result["manufacturer"] == "Stiebel Eltron"
        assert result["model"] == "WPL 18"
        assert result["confidence"] == 97.0

    def test_worker_failure_does_not_crash_pipeline(self, monkeypatch):
        table = "II2H3P G20 20 G31 37 C13(X)-C33(X)"
        calls = {"n": 0}

        def flaky_extract(img):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("OCR worker unavailable")
            return (table, 0.9)

        monkeypatch.setattr("app.ocr.pipeline.extract_text", flaky_extract)
        result = run_pipeline(_image_bytes())

        assert result["raw_text"] == table
        assert result["model"] is None
