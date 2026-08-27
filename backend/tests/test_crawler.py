"""Tests for the EPREL crawler service."""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.crawler_service import (
    _map_energy_class,
    _map_fuel_type,
    _map_category,
    _extract_heat_output,
    _extract_kw,
    _extract_manufacturer_name,
    _is_plausible_model,
    _kw_in_range,
    _parse_product_hit,
)


class TestMapEnergyClass:
    def test_maps_app_to_a_plus_plus(self):
        assert _map_energy_class("APP") == "A++"

    def test_maps_appp_to_a_plus_plus_plus(self):
        assert _map_energy_class("APPP") == "A+++"

    def test_maps_ap_to_a_plus(self):
        assert _map_energy_class("AP") == "A+"

    def test_passes_through_standard_classes(self):
        assert _map_energy_class("A") == "A"
        assert _map_energy_class("B") == "B"
        assert _map_energy_class("C") == "C"

    def test_returns_none_for_none(self):
        assert _map_energy_class(None) is None

    def test_returns_none_for_empty(self):
        assert _map_energy_class("") is None


class TestMapFuelType:
    def test_heat_pump_is_electricity(self):
        assert _map_fuel_type("HEAT_PUMP", "spaceheaters") == "electricity"

    def test_gas_boiler(self):
        assert _map_fuel_type("GAS_BOILER", "spaceheaters") == "gas"

    def test_oil_boiler(self):
        assert _map_fuel_type("OIL_BOILER", "spaceheaters") == "oil"

    def test_biomass_boiler(self):
        assert _map_fuel_type("BIOMASS_BOILER", "spaceheaters") == "biomass"

    def test_fallback_for_localspaceheaters(self):
        assert _map_fuel_type(None, "localspaceheaters") == "biomass"

    def test_fallback_for_solidfuelboilers(self):
        assert _map_fuel_type(None, "solidfuelboilers") == "biomass"

    def test_fallback_for_waterheaters(self):
        assert _map_fuel_type(None, "waterheaters") == "electricity"


class TestMapCategory:
    def test_heat_pump_category(self):
        assert _map_category("HEAT_PUMP", "spaceheaters") == "Heat pumps"

    def test_gas_boiler_category(self):
        assert _map_category("GAS_BOILER", "spaceheaters") == "Gas boilers"

    def test_fallback_for_solidfuelboilers(self):
        assert _map_category(None, "solidfuelboilers") == "Biomass boilers"

    def test_fallback_for_waterheaters(self):
        assert _map_category(None, "waterheaters") == "Water heaters"


class TestExtractHeatOutput:
    def test_extracts_output(self):
        hit = {"ratedHeatOutput": 25.0}
        assert _extract_heat_output(hit) == "25.0 kW"

    def test_returns_none_when_missing(self):
        assert _extract_heat_output({}) is None

    def test_returns_none_for_none_value(self):
        assert _extract_heat_output({"ratedHeatOutput": None}) is None


class TestExtractKw:
    def test_parses_number(self):
        assert _extract_kw(14.4) == 14.4

    def test_parses_int(self):
        assert _extract_kw(10) == 10.0

    def test_parses_formatted_string(self):
        assert _extract_kw("17.2 kW") == 17.2

    def test_parses_comma_decimal(self):
        assert _extract_kw("8,2 kW") == 8.2

    def test_returns_none_when_unparseable(self):
        assert _extract_kw(None) is None
        assert _extract_kw("n/a") is None


class TestKwInRange:
    def test_exact_match_within_tolerance(self):
        assert _kw_in_range(11.0, 11.5)

    def test_outside_tolerance_rejected(self):
        assert not _kw_in_range(11.0, 25.0)

    def test_relative_band_scales_for_large_outputs(self):
        assert _kw_in_range(84.3, 90.0)
        assert not _kw_in_range(84.3, 50.0)

    def test_minimum_absolute_band_for_small_units(self):
        assert _kw_in_range(2.2, 3.8)  # 2kW band, not percentage-driven
        assert not _kw_in_range(2.2, 6.0)

    def test_boundary_is_inclusive(self):
        assert _kw_in_range(10.0, 12.5)  # exactly 25%
        assert not _kw_in_range(10.0, 12.6)


class TestExtractManufacturerName:
    def test_prefers_brand_over_registrant(self):
        hit = {"organisation": {"organisationTitle": "TECNILIMA - EQUIPAMENTOS E SERVICOS LDA"}, "supplierOrTrademark": "Wertec"}
        assert _extract_manufacturer_name(hit) == "Wertec"

    def test_falls_back_to_trademark_owner(self):
        hit = {"organisation": {"organisationTitle": "Some Importer"}, "supplierOrTrademark": None, "trademarkOwner": "Daikin"}
        assert _extract_manufacturer_name(hit) == "Daikin"

    def test_falls_back_to_registrant_normalized(self):
        # Registrant legal entity is normalized to the canonical brand.
        hit = {"organisation": {"organisationTitle": "Viessmann Werke GmbH"}, "supplierOrTrademark": None}
        assert _extract_manufacturer_name(hit) == "Viessmann"

    def test_normalizes_legal_entity_brand(self):
        # supplierOrTrademark may itself be a legal entity; normalizer maps it.
        hit = {"supplierOrTrademark": "Viessmann Climate Solutions SE"}
        assert _extract_manufacturer_name(hit) == "Viessmann"

    def test_returns_unknown_when_empty(self):
        assert _extract_manufacturer_name({}) == "Unknown"


class TestIsPlausibleModel:
    def test_valid_models(self):
        assert _is_plausible_model("Vitodens 200-W") is True
        assert _is_plausible_model("ECOMBI 24M") is True

    def test_trivial_codes_rejected(self):
        assert _is_plausible_model("a") is False
        assert _is_plausible_model("AC") is False
        assert _is_plausible_model("10") is False
        assert _is_plausible_model("2C") is False

    def test_pure_numeric_rejected(self):
        assert _is_plausible_model("900") is False
        assert _is_plausible_model("2024") is False

    def test_composition_rejected(self):
        assert _is_plausible_model("Wolf Sonnenpaket COB-15; Kollektor") is False
        assert _is_plausible_model("Package Boiler; 2x Collector") is False

    def test_empty_rejected(self):
        assert _is_plausible_model("") is False
        assert _is_plausible_model(None) is False


class TestParseProductHit:
    @pytest.mark.asyncio
    async def test_parses_valid_hit(self, db_session):
        hit = {
            "eprelRegistrationNumber": "12345",
            "modelIdentifier": "Vitodens 200-W",
            "organisation": {"organisationTitle": "Viessmann Werke GmbH"},
            "supplierOrTrademark": "Viessmann",
            "energyClass": "A",
            "ratedHeatOutput": 24.0,
            "type": "GAS_BOILER",
        }
        mfr_cache = {}
        cat_cache = {}
        result = await _parse_product_hit(hit, "spaceheaters", mfr_cache, cat_cache, db_session)

        assert result is not None
        assert result["eprel_id"] == "12345"
        assert result["model"] == "Vitodens 200-W"
        assert result["energy_class"] == "A"
        assert result["heat_output"] == "24.0 kW"
        assert result["fuel_type"] == "gas"
        assert result["manufacturer_id"] is not None
        assert result["supplier"] == "Viessmann Werke GmbH"
        assert "viessmann" in mfr_cache

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_eprel_id(self, db_session):
        hit = {"modelIdentifier": "Test", "eprelRegistrationNumber": None}
        result = await _parse_product_hit(hit, "spaceheaters", {}, {}, db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_model(self, db_session):
        hit = {"eprelRegistrationNumber": "123", "modelIdentifier": ""}
        result = await _parse_product_hit(hit, "spaceheaters", {}, {}, db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_caches_manufacturers(self, db_session):
        hit = {
            "eprelRegistrationNumber": "99999",
            "modelIdentifier": "Test Model",
            "organisation": {"organisationTitle": "Test Mfr"},
            "supplierOrTrademark": "Test",
            "type": "HEAT_PUMP",
        }
        mfr_cache = {}
        cat_cache = {}
        await _parse_product_hit(hit, "spaceheaters", mfr_cache, cat_cache, db_session)
        await _parse_product_hit(hit, "spaceheaters", mfr_cache, cat_cache, db_session)
        assert len(mfr_cache) == 1


class TestSearchAndAddProductGroupFilter:
    """On-demand EPREL search must be restricted to the groups that match the
    detected fuel type, instead of querying every group (up to 8x fewer
    API requests per OCR scan)."""

    @pytest.mark.asyncio
    async def test_restricts_groups_by_fuel_type(self, db_session):
        from app.services import crawler_service as cs

        queried = []

        async def fake_fetch_page(client, group_slug, page, limit=cs.PAGE_SIZE):
            queried.append(group_slug)
            return {"size": 0, "hits": []}

        with patch.object(cs, "_fetch_page", side_effect=fake_fetch_page):
            with patch.object(cs.httpx, "AsyncClient") as ac:
                ac.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                ac.return_value.__aexit__ = AsyncMock(return_value=False)
                await cs.search_and_add_product(
                    db_session, manufacturer="Truma", model="S 3004", fuel_type="gas"
                )

        assert queried == ["spaceheaters", "spaceheaters", "spaceheaters"]

    @pytest.mark.asyncio
    async def test_searches_all_groups_when_fuel_unknown(self, db_session):
        from app.services import crawler_service as cs

        queried = []

        async def fake_fetch_page(client, group_slug, page, limit=cs.PAGE_SIZE):
            queried.append(group_slug)
            return {"size": 0, "hits": []}

        with patch.object(cs, "_fetch_page", side_effect=fake_fetch_page):
            with patch.object(cs.httpx, "AsyncClient") as ac:
                ac.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                ac.return_value.__aexit__ = AsyncMock(return_value=False)
                await cs.search_and_add_product(db_session, manufacturer="Truma", model="S 3004")

        expected = len(cs.EPREL_PRODUCT_GROUPS + cs.EPREL_EXTRA_GROUPS)
        assert len(queried) == expected * 3
        assert len(set(queried)) == expected
