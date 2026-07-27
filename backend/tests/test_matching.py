"""Tests for the matching engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.matching_service import _fuzzy_score, find_matches


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
