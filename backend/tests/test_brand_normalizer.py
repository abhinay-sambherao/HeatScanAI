"""Tests for the brand normalizer.

The normalizer maps EPREL's inconsistent manufacturer names (legal entities,
registrants, case variants) to canonical brand names, and validates that a
brand/model string is plausible (rejects composition/junk).
"""

from app.services.brand_normalizer import (
    normalize_brand,
    is_valid_brand,
    extract_brand_from_raw,
)


class TestNormalizeBrand:
    def test_viessmann_legal_entity_to_brand(self):
        assert normalize_brand("Viessmann Climate Solutions SE") == "Viessmann"
        assert normalize_brand("Viessmann Werke GmbH & Co. KG") == "Viessmann"
        assert normalize_brand("Viessmann Werke GmbH & Co KG") == "Viessmann"
        assert normalize_brand("Viessmann") == "Viessmann"

    def test_kwb_multiple_variants(self):
        assert normalize_brand("KWB Energiesysteme GmbH") == "KWB"
        assert normalize_brand("KWB - Kraft und Wärme aus Biomasse GmbH") == "KWB"
        assert normalize_brand("KWB Kraft und Wärme aus Biomasse") == "KWB"

    def test_case_normalization(self):
        assert normalize_brand("MIDEA") == "Midea"
        assert normalize_brand("JØTUL") == "Jøtul"
        assert normalize_brand("DIMPLEX") == "Dimplex"

    def test_mitsubishi_variants(self):
        assert normalize_brand("Mitsubishi Electric Hydronics & IT Cooling Systems S.P.A.") == "Mitsubishi Electric"
        assert normalize_brand("MITSUBISHI HEAVY INDUSTRIES AIR CONDITIONING EUROPE LTD.") == "Mitsubishi Electric"

    def test_czech_brands(self):
        assert normalize_brand("Družstevní závody Dražice - strojírna s.r.o.") == "Dražice"
        assert normalize_brand("Fröling Heizkessel- und Behälterbau Ges.m.b.H.") == "Fröling"

    def test_short_known_brand_allowed(self):
        assert normalize_brand("LG") == "LG"
        assert normalize_brand("AWB") == "AWB"

    def test_unknown_brand_preserved(self):
        assert normalize_brand("SomeUnknownBrand") == "SomeUnknownBrand"

    def test_empty_returns_none(self):
        assert normalize_brand("") is None
        assert normalize_brand("   ") is None
        assert normalize_brand(None) is None

    def test_trivial_junk_returns_none(self):
        assert normalize_brand("a") is None
        assert normalize_brand("AC") is None
        assert normalize_brand("10") is None
        assert normalize_brand("02") is None

    def test_composition_returns_none(self):
        assert normalize_brand("Wolf Sonnenpaket COB-15; Kollektor") is None
        assert normalize_brand("Package Boiler; 2x Collector") is None

    def test_long_legal_entity_rejected(self):
        # >60 chars legal entity name is rejected as too long to be a brand
        long_name = "Ulrich Brunner Ofen- und Heiztechnik Gesellschaft für Guß- und Stahlkonstruktionen mbH"
        assert normalize_brand(long_name) is None


class TestIsValidBrand:
    def test_valid_brands(self):
        assert is_valid_brand("Viessmann") is True
        assert is_valid_brand("Buderus") is True
        assert is_valid_brand("KWB") is True

    def test_short_brands_exempt_when_known(self):
        assert is_valid_brand("LG") is True
        assert is_valid_brand("AWB") is True

    def test_trivial_codes_rejected(self):
        assert is_valid_brand("a") is False
        assert is_valid_brand("AC") is False
        assert is_valid_brand("10") is False

    def test_composition_rejected(self):
        assert is_valid_brand("Wolf Paket COB-15; Kollektor") is False

    def test_empty_rejected(self):
        assert is_valid_brand("") is False
        assert is_valid_brand(None) is False


class TestExtractBrandFromRaw:
    def test_uses_supplier_or_trademark(self):
        raw = {
            "supplierOrTrademark": "Viessmann Climate Solutions SE",
            "organisation": {"organisationTitle": "Viessmann Werke GmbH & Co. KG"},
        }
        assert extract_brand_from_raw(raw) == "Viessmann"

    def test_prefers_brand_over_registrant(self):
        raw = {
            "supplierOrTrademark": "Wertec",
            "organisation": {"organisationTitle": "TECNILIMA - EQUIPAMENTOS E SERVICOS LDA"},
        }
        assert extract_brand_from_raw(raw) == "Wertec"

    def test_falls_back_to_owner(self):
        raw = {"supplierOrTrademark": "", "trademarkOwner": "Buderus"}
        assert extract_brand_from_raw(raw) == "Buderus"

    def test_falls_back_to_registrant(self):
        raw = {
            "supplierOrTrademark": "",
            "organisation": {"organisationTitle": "Daikin Europe N.V."},
        }
        assert extract_brand_from_raw(raw) == "Daikin"

    def test_no_valid_brand_returns_none(self):
        raw = {"supplierOrTrademark": "a"}
        assert extract_brand_from_raw(raw) is None
