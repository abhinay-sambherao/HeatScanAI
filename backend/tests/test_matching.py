"""Tests for the matching engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.matching_service import _fuzzy_score, _brand_consistent, find_matches


class TestFuzzyScore:
    def test_identical_strings(self):
        assert _fuzzy_score("Viessmann", "Viessmann") == 100.0

    def test_partial_match(self):
        score = _fuzzy_score("Viessmann", "Viessmann Vitodens")
        assert 50 < score < 100

    def test_no_match(self):
        score = _fuzzy_score("Viessmann", "Buderus")
        assert score < 50

    def test_none_handling(self):
        assert _fuzzy_score(None, "test") == 0.0
        assert _fuzzy_score("test", None) == 0.0
        assert _fuzzy_score(None, None) == 0.0

    def test_case_insensitive(self):
        assert _fuzzy_score("VIESSMANN", "viessmann") == 100.0


class TestBrandConsistent:
    """Fuzzy brand scoring alone cannot separate truma/terma/termia/trane —
    hard evidence (substring / presence in raw OCR text) must be used."""

    def test_detected_word_in_brand_with_suffix(self):
        assert _brand_consistent("Vaillant GmbH", "Vaillant", None)

    def test_detected_multiword_brand_leading_word(self):
        assert _brand_consistent("Truma", "Truma Gerätetechnik GmbH", None)

    def test_brand_in_raw_text(self):
        assert _brand_consistent("Buderus Heiztechnik", "Buderus",
                                 "Buderus Logano G124 25 kW nameplate")

    def test_truma_vs_termia_rejected(self):
        assert not _brand_consistent("TERMIA", "Truma",
                                     "Truma S 3004 heater type gas caravan")

    def test_truma_vs_terma_rejected(self):
        assert not _brand_consistent("Terma", "Truma",
                                     "Truma S 3004 heater type gas caravan")

    def test_truma_vs_trane_rejected(self):
        assert not _brand_consistent("TRANE", "Truma",
                                     "Truma S 3004 heater type gas caravan")

    def test_substring_within_longer_word_rejected(self):
        assert not _brand_consistent("Trumac", "Truma", None)

    def test_none_handling(self):
        assert not _brand_consistent(None, "Truma", None)
        assert not _brand_consistent("Truma", None, None)
