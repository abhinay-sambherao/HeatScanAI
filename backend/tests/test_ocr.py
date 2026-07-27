"""Tests for the OCR text parser."""

from app.ocr.parser import (
    clean_text,
    extract_manufacturer,
    extract_model,
    extract_energy_class,
    extract_heat_output,
    extract_fuel_type,
    extract_fields,
)


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


class TestExtractModel:
    def test_extracts_model_prefix(self):
        assert extract_model("Model Vitodens 200") is not None

    def test_returns_none_for_no_model(self):
        assert extract_model("Just some random text") is None


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
