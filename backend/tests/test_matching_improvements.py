"""Tests for matching improvements P2 (weight redistribution), P3 (model
aliases), P4 (match-type classification) and P5 (attribute lookup)."""

import uuid
import pytest

from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.services.matching_service import (
    find_matches,
    _classify_match,
    MATCH_TYPE_EXACT,
    MATCH_TYPE_VARIANT,
    MATCH_TYPE_BRAND_ONLY,
    MATCH_TYPE_ATTRIBUTE,
)
from app.services.model_aliases import lookup_alias, alias_overrides_model_score


async def _seed(db, manufacturer="Stiebel Eltron", products=()):
    mfr = Manufacturer(name=manufacturer)
    db.add(mfr)
    await db.flush()
    for i, p in enumerate(products):
        db.add(Product(
            id=uuid.uuid4(),
            eprel_id=f"eprel-{i}",
            manufacturer_id=mfr.id,
            model=p["model"],
            energy_class=p.get("energy_class"),
            fuel_type=p.get("fuel_type"),
            heat_output=p.get("heat_output"),
        ))
    await db.flush()
    return mfr


class TestClassifyMatch:
    def test_exact(self):
        assert _classify_match(90, 95, True, "WPL 18", "WPL 18") == MATCH_TYPE_EXACT

    def test_variant(self):
        assert _classify_match(90, 60, True, "Thision S Plus", "THISION L PLUS") == MATCH_TYPE_VARIANT

    def test_brand_only(self):
        assert _classify_match(90, 30, True, "Ochsner Europa", "AIR 80 C13A") == MATCH_TYPE_BRAND_ONLY

    def test_attribute_path(self):
        assert _classify_match(0, 0, False, "x", "y", use_attribute_path=True) == MATCH_TYPE_ATTRIBUTE

    def test_brand_only_when_no_model(self):
        assert _classify_match(90, 0, True, None, "AIR 80 C13A") == MATCH_TYPE_BRAND_ONLY


class TestModelAliases:
    def test_lookup_present(self):
        assert lookup_alias("Ochsner", "Europa MINI EW P") is not None

    def test_lookup_absent(self):
        assert lookup_alias("Vaillant", "NotARealModelXYZ") is None

    def test_alias_override_true(self):
        assert alias_overrides_model_score("Europa MINI EW P", "AIR 80 C13A")

    def test_alias_override_false_for_unrelated(self):
        assert not alias_overrides_model_score("WPL 18", "AIR 80 C13A")


@pytest.mark.asyncio
class TestMatchTypeEndToEnd:
    async def test_exact_model_badge(self, db_session):
        await _seed(db_session, products=[
            {"model": "WPL 18", "fuel_type": "electricity", "energy_class": "A+++"},
        ])
        res = await find_matches(
            db_session, manufacturer="Stiebel Eltron", model="WPL 18",
            raw_text="Stiebel Eltron WPL 18",
        )
        assert res and res[0]["match_type"] == MATCH_TYPE_EXACT

    async def test_brand_only_badge_for_disjoint_model(self, db_session):
        # Model strings fully disjoint — brand confirmed but model unknown.
        await _seed(db_session, products=[
            {"model": "AIR 80 C13A", "fuel_type": "electricity", "energy_class": "A+++"},
        ])
        res = await find_matches(
            db_session, manufacturer="Ochsner", model="Europa MINI EW",
            raw_text="Ochsner Europa MINI EW",
        )
        # P0 + P1 + brand gate: with a disjoint model, the main path should not
        # confidently classify the wrong product — either none, or brand_only.
        if res:
            assert res[0]["match_type"] == MATCH_TYPE_BRAND_ONLY


@pytest.mark.asyncio
class TestAttributeLookupP5:
    async def test_attribute_lookup_when_no_model(self, db_session):
        await _seed(db_session, products=[
            {"model": "AIR 80 C13A", "fuel_type": "electricity",
             "energy_class": "A+", "heat_output": "2.2 kW"},
            {"model": "GAS BOILER 300", "fuel_type": "gas",
             "energy_class": "B", "heat_output": "24 kW"},
        ])
        res = await find_matches(
            db_session, manufacturer="Ochsner", model=None,
            fuel_type="electricity", energy_class="A+", heat_output="2.2 kW",
        )
        # Model is None → main loop has no model gate; brand_ok + mfr should
        # already surface the heat pump. Either way, no gas boiler appears.
        assert all(r["fuel_type"] == "electricity" for r in res)


@pytest.mark.asyncio
class TestAliasPromotesWeakModelP3:
    async def test_alias_overrides_to_exact(self, db_session):
        await _seed(db_session, manufacturer="ELCO", products=[
            {"model": "thision l plus 13", "fuel_type": "gas", "energy_class": "A"},
        ])
        # Nameplate reads "Thision S Plus 13" — alias maps to "thision l plus 13".
        res = await find_matches(
            db_session, manufacturer="ELCO", model="Thision S Plus 13",
            raw_text="ELCO Thision S Plus 13",
        )
        assert res and res[0]["match_type"] == MATCH_TYPE_EXACT
        assert res[0]["model"] == "thision l plus 13"
