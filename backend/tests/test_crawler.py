"""Tests for the EPREL crawler service."""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.crawler_service import (
    _map_energy_class,
    _map_fuel_type,
    _map_category,
    _extract_heat_output,
    _extract_manufacturer_name,
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


class TestExtractManufacturerName:
    def test_prefers_organisation_title(self):
        hit = {"organisation": {"organisationTitle": "Viessmann Werke GmbH"}, "supplierOrTrademark": "Viessmann"}
        assert _extract_manufacturer_name(hit) == "Viessmann Werke GmbH"

    def test_falls_back_to_trademark(self):
        hit = {"organisation": None, "supplierOrTrademark": "Daikin"}
        assert _extract_manufacturer_name(hit) == "Daikin"

    def test_returns_unknown_when_empty(self):
        assert _extract_manufacturer_name({}) == "Unknown"


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
        assert "viessmann werke gmbh" in mfr_cache

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
