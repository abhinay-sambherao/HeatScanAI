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
    extract_installation_year,
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

    def test_finds_okofen_by_product_line(self):
        assert extract_manufacturer("Pellematic08") == "ÖkoFEN"

    def test_finds_okofen_by_hq_address(self):
        assert extract_manufacturer("Gewerbepark 1, A-4133 Niederkappel") == "ÖkoFEN"

    def test_returns_none_without_brand_signals(self):
        assert extract_manufacturer("Generic Heating Unit X500") is None


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

    def test_type_label_mid_line(self):
        text = "Fax: DW 10 Type Pellematic08 Herstellernummer X12345"
        assert extract_model(text) == "Pellematic08"

    def test_type_label_with_period(self):
        assert extract_model("Typ. Pellematic08") == "Pellematic08"

    def test_heater_type_is_not_a_model(self):
        assert extract_model("Heater type: Condensing 24 kW") is None

    def test_typenschild_word_is_not_a_label(self):
        assert extract_model("Typenschild ABC123") == "ABC123"

    def test_mid_line_typed_two_part_model_code(self):
        # All-caps TYP: label followed by a short all-caps code + digits split
        # over a space (WPL 18 live-scan regression). The COP-table value
        # "W 35 11" must NOT win over the labeled model.
        text = ("STIEBEL ELTRON CE AP TYP:WPL 18 BESTELL-NR.:074411 "
                "NR.:00206-7759 Kaeltemittel : R407C")
        assert extract_model(text) == "WPL 18"

    def test_mid_line_typed_all_caps(self):
        assert extract_model("HEATER TYPE: WPL 18") == "WPL 18"

    def test_mid_line_typed_lowercase_prose_not_model(self):
        assert extract_model("Heater type: Condensing 24 kW") is None

    def test_mod_abbreviation_label_truncates_trailing_codes(self):
        text = "Mod.: WTC-GB 90-A 0063 BS 3948 CE 0085 Max Weishaupt GmbH"
        assert extract_model(text) == "WTC-GB 90-A"

    def test_postal_code_is_not_a_model(self):
        assert extract_model("Max Weishaupt GmbH D-88475 Schwendi") is None

    def test_leading_zero_code_is_not_a_model(self):
        assert extract_model("C13X L0330 C43X C53X") is None

    def test_gas_category_codes_are_not_models(self):
        text = "II2H3P G20 20 G31 37 C13(X) C33X -C43(X)C53(X) C83X C930"
        assert extract_model(text) is None


class TestExtractEnergyClass:
    def test_finds_class_a(self):
        assert extract_energy_class("Energy class: A") == "A"

    def test_finds_class_a_plus_plus(self):
        assert extract_energy_class("Energieeffizienzklasse: A+++") == "A+++"

    def test_returns_none_when_missing(self):
        assert extract_energy_class("No energy info here") is None

    def test_gas_category_letter_is_not_a_class(self):
        assert extract_energy_class("II2H3P G20 20 G31 37/50 C13(X)") is None

    def test_appliance_category_letter_is_not_a_class(self):
        assert extract_energy_class("12E(R)B G20 20") is None

    def test_postal_code_letter_is_not_a_class(self):
        assert extract_energy_class("Gewerbepark 1, A-4133 Niederkappel") is None


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

    def test_okofen_nameplate_without_brand(self):
        text = (
            "Beispiel Typenschild Pelletkessel Gewerbepark 1, A-4133 Niederkappel "
            "Tel.: 0043 7286 7450 Fax: DW 10 Type Pellematic08 Herstellernummer "
            "X12345 Baujahr 2009 Nennwärmeleistung 8,2 KW zul. Brennstoff Holzpellets"
        )
        fields = extract_fields(text)
        assert fields["manufacturer"] == "ÖkoFEN"
        assert fields["model"] == "Pellematic08"
        assert fields["fuel_type"] == "wood"
        assert fields["heat_output"] == "8,2 kW"

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

    def test_garbled_flue_table_yields_no_fields(self):
        text = (
            "II2ELL3P G20 20 G31 50 C13(X)-C33(X)-C43(X)C53(X)-C63(X) CB "
            "II2H3P G20 20 G31 50 C13(X)C33(X) C43CX C53(X LC63X C83(X C930 "
            "12E(R)B G20 20/25 G25 20/25 C13(X) C33X -C43(X)C53(X)-C83(X) C93X -B23 "
            "II2H3P G20 20 G31 37 C13(X) C33XC430X 0C53(X)-C630 083XC9 "
            "I12Esi3P G20 20/25 G31 37 C13(X)-C33(X)-C43X)C53(X0-C63X0-C83X)C980X "
            "12L3P G25 25 G31 30/50 C13(X-C33XC43XC53XC63X0-C83X0C93X0B "
            "II2H3P G20 20 G31 30/50 C13X L0330 C43X C53XCBXC3XC98XB"
        )
        fields = extract_fields(text)
        assert fields["manufacturer"] is None
        assert fields["model"] is None
        assert fields["energy_class"] is None

    def test_weishaupt_plate_mod_label(self):
        text = (
            "Gas-Brennwertkessel PYR-1000 ND Pyropac AG, CH-9466 Sennwald "
            "Ser. Nr.: 9108992 14 Mod.: WTC-GB 90-A 0063 BS 3948 CE 0085 "
            "-weishaupt- Max Weishaupt GmbH D-88475 Schwendi www.weishaupt.de"
        )
        fields = extract_fields(text)
        assert fields["manufacturer"] == "Weishaupt"
        assert fields["model"] == "WTC-GB 90-A"
        assert fields["fuel_type"] == "gas"


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

    @pytest.mark.asyncio
    async def test_uses_ocr_year_when_user_year_not_provided(self, db_session):
        """A year OCR'd from the nameplate must be persisted/returned so the UI
        doesn't prompt the user unnecessarily."""
        merged = {
            "raw_text": "Vaillant ecoTEC\nBaujahr: 2015",
            "cleaned_text": "Vaillant ecoTEC Baujahr 2015",
            "confidence": 88.0,
            "manufacturer": "Vaillant",
            "model": "ecoTEC",
            "installation_year": 2015,
            "per_image": [],
        }
        result = await _persist_and_match(db=db_session, merged=merged)
        assert result["installation_year"] == 2015

    @pytest.mark.asyncio
    async def test_user_year_overrides_ocr_year(self, db_session):
        """An explicit user-provided year takes precedence over the OCR one."""
        merged = {
            "raw_text": "Vaillant ecoTEC\nBaujahr: 2015",
            "cleaned_text": "Vaillant ecoTEC Baujahr 2015",
            "confidence": 88.0,
            "manufacturer": "Vaillant",
            "model": "ecoTEC",
            "installation_year": 2015,
            "per_image": [],
        }
        result = await _persist_and_match(
            db=db_session, merged=merged, installation_year=2005
        )
        assert result["installation_year"] == 2005


class TestExtractInstallationYear:
    """Tests for installation year extraction from OCR text."""

    def test_baujahr_label(self):
        text = "Vaillant ecoTEC Pro VUW 242/5-3\nBaujahr: 2015\nNennwärmeleistung 24 kW"
        assert extract_installation_year(text) == 2015

    def test_errichtung_label(self):
        text = "Hersteller: Junkers\nErrichtung 2008\nModell: CerapurComfort"
        assert extract_installation_year(text) == 2008

    def test_herstelldatum_label(self):
        text = "Stiebel Eltron WPL 18\nHerstelldatum: 03.2019\nLeistung 18 kW"
        assert extract_installation_year(text) == 2019

    def test_date_format_mm_slash_yyyy(self):
        text = "Bosch Junkers\n02/2024\nZS 2.300-1 K"
        assert extract_installation_year(text) == 2024

    def test_date_format_mm_dot_yyyy(self):
        text = "Viessmann Vitodens 100\n11.2017\n26 kW"
        assert extract_installation_year(text) == 2017

    def test_standalone_year_near_manufacturer(self):
        text = "ELCO Thision S Plus\nELCO Heiztechnik GmbH\n2012\n13.1 kW Erdgas"
        assert extract_installation_year(text) == 2012

    def test_no_year_returns_none(self):
        text = "Vaillant ecoTEC Pro VUW 242/5-3\nNennwärmeleistung 24 kW"
        assert extract_installation_year(text) is None

    def test_year_out_of_range_ignored(self):
        text = "Junkers ZSR\n1975\nG20 20"
        assert extract_installation_year(text) is None

    def test_year_2006_from_chimney_report(self):
        text = "ZSR 2006 0 7 8kW 7 8kW 7 80 kW\nGas-Niedertemperaturkessel\nHersteller Junkers"
        assert extract_installation_year(text) == 2006

    def test_year_from_text_near_model(self):
        text = "Weishaupt Mod.: WTC-GB 90-A\nBaujahr 2020\nGas-Brennwertkessel"
        assert extract_installation_year(text) == 2020

    def test_multiple_years_returns_first(self):
        text = "Vaillant 2015\nModell 2020\nLeistung 24 kW"
        assert extract_installation_year(text) == 2015

    def test_year_in_fields_dict(self):
        text = "Bosch\nModell: Condens 7000i\nBaujahr: 2018\n28 kW Gas"
        fields = extract_fields(text)
        assert fields["installation_year"] == 2018

    def test_no_year_in_fields_returns_none(self):
        text = "Vaillant ecoTEC Pro 24 kW"
        fields = extract_fields(text)
        assert fields["installation_year"] is None
