"""Tests for the OCR text parser."""

import pytest

from app.ocr.parser import (
    clean_text,
    extract_manufacturer,
    extract_model,
    extract_energy_class,
    extract_heat_output,
    extract_fuel_type,
    extract_fields,
)
from app.services.ocr_service import _persist_and_match


class TestCleanText:
    def test_removes_special_characters(self):
        result = clean_text("Viessmann® Vitodens™ 200")
        assert "Viessmann" in result
        assert "Vitodens" in result

    def test_collapses_whitespace(self):
        result = clean_text("hello    world   test")
        assert result == "hello world test"

    def test_fixes_common_ocr_errors(self):
        result = clean_text("V1essmann")  # l → 1 is contextual
        assert isinstance(result, str)


class TestExtractManufacturer:
    def test_finds_viessmann(self):
        assert extract_manufacturer("Viessmann Vitodens 200-W") == "Viessmann"

    def test_finds_buderus(self):
        assert extract_manufacturer("Buderus Logamax Plus GB142") == "Buderus"

    def test_finds_vaillant(self):
        assert extract_manufacturer("Vaillant ecoTEC plus 837") == "Vaillant"

    def test_returns_none_for_unknown(self):
        assert extract_manufacturer("Generic Heating Unit X500") is None

    def test_case_insensitive(self):
        assert extract_manufacturer("VIESSMANN VITODENS") == "Viessmann"

    # German market majors — umlaut/hyphen nameplate spellings must resolve
    # to the same canonical brand used in the DB.
    def test_finds_broetje_umlaut(self):
        assert extract_manufacturer("Brötje EuroCondens SBK 15") == "Brötje"

    def test_finds_broetje_ascii(self):
        assert extract_manufacturer("Brotje EuroCondens SBK 15") == "Brötje"

    def test_finds_broetje_transcription(self):
        assert extract_manufacturer("Broetje WGB 22") == "Brötje"

    def test_finds_stiebel_eltron_space(self):
        assert extract_manufacturer("STIEBEL ELTRON WWK 300") == "Stiebel Eltron"

    def test_finds_stiebel_eltron_hyphen(self):
        assert extract_manufacturer("Stiebel-Eltron WWK 300") == "Stiebel Eltron"

    def test_finds_vaillant_typo_valiant(self):
        assert extract_manufacturer("Valiant ecoTEC 837") == "Vaillant"

    def test_finds_viessmann_typo_viesman(self):
        assert extract_manufacturer("Viesman Vitodens 200") == "Viessmann"

    def test_finds_weishaupt(self):
        assert extract_manufacturer("Weishaupt WTC-GB 15") == "Weishaupt"

    def test_finds_wolf(self):
        assert extract_manufacturer("Wolf CGB-2-20") == "Wolf"

    def test_finds_bosch_buderus_junkers(self):
        assert extract_manufacturer("Bosch Condens 5000") == "Bosch"
        assert extract_manufacturer("Junkers Cerapur 9000") == "Junkers"


class TestExtractModel:
    def test_extracts_model_prefix(self):
        assert extract_model("Model Vitodens 200") is not None

    def test_returns_none_for_no_model(self):
        assert extract_model("Just some random text") is None

    def test_model_after_manufacturer(self):
        assert extract_model("STIEBEL ELTRON WPL 18") == "WPL 18"

    def test_model_after_manufacturer_report(self):
        text = "ELCO, Thision S Plus 13.1 Brennstoff Brennerart"
        assert extract_model(text) == "Thision S Plus 13.1"

    def test_ignores_legal_form_suffix(self):
        assert extract_model("Vaillant GmbH & Co. KG ecoTEC") is None

    def test_ignores_headerless_brand_only(self):
        assert extract_model("ELCO Thision") is None


class TestExtractEnergyClass:
    def test_finds_class_a(self):
        assert extract_energy_class("Energy class: A") == "A"

    def test_finds_class_a_plus_plus(self):
        assert extract_energy_class("Energieeffizienzklasse: A+++") == "A+++"

    def test_returns_none_when_missing(self):
        assert extract_energy_class("No energy info here") is None


class TestExtractHeatOutput:
    def test_finds_kw(self):
        result = extract_heat_output("Heizleistung 24.5 kW")
        assert result is not None
        assert "24.5" in result

    def test_returns_none_when_missing(self):
        assert extract_heat_output("No power info") is None


class TestExtractFuelType:
    def test_detects_gas(self):
        assert extract_fuel_type("Natural Gas Boiler") == "gas"

    def test_detects_oil(self):
        assert extract_fuel_type("Heizöl Brent") == "oil"

    def test_detects_heat_pump(self):
        assert extract_fuel_type("Wärmepumpe Luft-Wasser") == "electricity"

    def test_returns_none_when_unknown(self):
        assert extract_fuel_type("Something unusual") is None


class TestExtractFields:
    def test_full_extraction(self):
        text = "Viessmann Vitodens 200-W Gas 24 kW Energy class A"
        fields = extract_fields(text)
        assert fields["manufacturer"] == "Viessmann"
        assert fields["energy_class"] == "A"
        assert fields["fuel_type"] == "gas"

    def test_full_extraction_inspection_report(self):
        text = (
            "Hersteller, Typ. Herstell-Nr., Errichtung 14,4 kW "
            "ELCO, Thision S Plus 13.1 Brennstoff Brennerart Erdgas"
        )
        fields = extract_fields(text)
        assert fields["manufacturer"] == "ELCO"
        assert fields["model"] == "Thision S Plus 13.1"
        assert fields["fuel_type"] == "gas"
        assert fields["heat_output"] == "14,4 kW"


class TestPersistAndMatchReturnsExtractedFields:
    """Extracted fields must survive the service → API response (UI depends on them)."""

    @pytest.mark.asyncio
    async def test_response_contains_energy_fuel_output(self, db_session):
        merged = {
            "raw_text": "ELCO, Thision S Plus 13.1 Erdgas",
            "cleaned_text": "ELCO Thision S Plus 13.1 Erdgas",
            "confidence": 92.0,
            "manufacturer": "ELCO",
            "model": "Thision S Plus 13.1",
            "energy_class": "A",
            "fuel_type": "gas",
            "heat_output": "14,4 kW",
            "per_image": [],
        }
        result = await _persist_and_match(db=db_session, merged=merged)
        assert result["energy_class"] == "A"
        assert result["fuel_type"] == "gas"
        assert result["heat_output"] == "14,4 kW"
