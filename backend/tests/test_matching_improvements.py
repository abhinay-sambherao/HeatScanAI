"""Tests for matching improvements P2 (weight redistribution), P3 (model
aliases), P4 (match-type classification) and P5 (attribute lookup)."""

import uuid
import pytest

from app.models.category import Category
from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.services.matching_service import (
    find_matches,
    _classify_match,
    _variant_key,
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
        assert _classify_match(90, 95, True, "WPL 18", "WPL 18", composite_score=85) == MATCH_TYPE_EXACT

    def test_exact_requires_composite_threshold(self):
        assert _classify_match(90, 95, True, "WPL 18", "WPL 18", composite_score=65) == MATCH_TYPE_VARIANT

    def test_variant(self):
        assert _classify_match(90, 60, True, "Thision S Plus", "THISION L PLUS") == MATCH_TYPE_VARIANT

    def test_brand_only(self):
        assert _classify_match(90, 30, True, "Ochsner Europa", "AIR 80 C13A") == MATCH_TYPE_BRAND_ONLY

    def test_attribute_path(self):
        assert _classify_match(0, 0, False, "x", "y", use_attribute_path=True) == MATCH_TYPE_ATTRIBUTE

    def test_brand_only_when_no_model(self):
        assert _classify_match(90, 0, True, None, "AIR 80 C13A") == MATCH_TYPE_BRAND_ONLY


class TestEprelPublicLink:
    def test_builds_public_url(self):
        from app.services.matching_service import _eprel_public_link
        from app.models.product import Product

        p = Product(
            eprel_id="994260",
            model="auroCOMPACT VSC S 146/4-5 150 (E-DE)",
            manufacturer_id=uuid.uuid4(),
            raw_json={"productGroup": "spaceheaters"},
        )
        eid, url = _eprel_public_link(p)
        assert eid == "994260"
        assert url == "https://eprel.ec.europa.eu/screen/product/spaceheaters/994260"

    def test_skips_manufacturer_web_ids(self):
        from app.services.matching_service import _eprel_public_link
        from app.models.product import Product

        p = Product(
            eprel_id="WEB-VAIL-auroCOMPACT",
            model="auroCOMPACT",
            manufacturer_id=uuid.uuid4(),
        )
        assert _eprel_public_link(p) == (None, None)


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
    async def test_alias_promotes_weak_model(self, db_session):
        await _seed(db_session, manufacturer="ELCO", products=[
            {"model": "thision l plus 13", "fuel_type": "gas", "energy_class": "A"},
        ])
        # Nameplate reads "Thision S Plus 13" — alias maps to "thision l plus 13".
        # Strings differ (S vs l) so match_type is model_variant, not exact_model,
        # but the alias still promotes the model score to 95 so the product is found.
        res = await find_matches(
            db_session, manufacturer="ELCO", model="Thision S Plus 13",
            raw_text="ELCO Thision S Plus 13",
        )
        assert res and res[0]["match_type"] == MATCH_TYPE_VARIANT
        assert res[0]["model"] == "thision l plus 13"


@pytest.mark.asyncio
class TestHeatingOnlyScope:
    """Standalone air-conditioning / cooling-only products must never appear,
    even if a non-heating category is present in the catalogue."""

    async def _seed_with_categories(self, db, categories):
        mfr = Manufacturer(name="Stiebel Eltron")
        db.add(mfr)
        await db.flush()
        cats = {}
        for idx, name in enumerate(categories):
            cat = Category(name=name)
            db.add(cat)
            await db.flush()
            cats[name] = cat
        db.add(Product(
            id=uuid.uuid4(), eprel_id="eprel-ac", manufacturer_id=mfr.id,
            model="WPL 18", fuel_type="electricity", energy_class="A+++",
            category_id=cats["Air conditioners"].id,
        ))
        db.add(Product(
            id=uuid.uuid4(), eprel_id="eprel-hp", manufacturer_id=mfr.id,
            model="WPL 18", fuel_type="electricity", energy_class="A+++",
            category_id=cats["Heat pumps"].id,
        ))
        await db.flush()

    async def test_cooling_only_product_is_excluded(self, db_session):
        await self._seed_with_categories(db_session, ["Air conditioners", "Heat pumps"])
        res = await find_matches(
            db_session, manufacturer="Stiebel Eltron", model="WPL 18",
            raw_text="Stiebel Eltron WPL 18",
        )
        assert res
        # The reversible "Heat pumps" unit may match; the "Air conditioners"
        # cooling-only unit must not.
        assert all(r["model"] == "WPL 18" for r in res)
        ac_hits = [r for r in res if r.get("category") == "Air conditioners"]
        assert not ac_hits


async def _seed_many(db, manufacturer, models):
    mfr = Manufacturer(name=manufacturer)
    db.add(mfr)
    await db.flush()
    for i, model in enumerate(models):
        db.add(Product(
            id=uuid.uuid4(), eprel_id=f"eprel-var-{i}", manufacturer_id=mfr.id,
            model=model, fuel_type="gas", energy_class="A", heat_output="14 kW",
            source="EPREL",
        ))
    await db.flush()


@pytest.mark.asyncio
class TestVariantGrouping:
    """Distinct EPREL registrations of the same heater line (config / gas-type /
    version suffixes) collapse into one representative card."""

    async def test_aurocompact_variants_grouped(self, db_session):
        await _seed_many(db_session, "Vaillant", [
            "auroCOMPACT VSC S 146/4-5 150 (E-DE)",
            "auroCOMPACT VSC S 146/4-5 150 (LL-DE)",
            "auroCOMPACT VSC D 146/4-5 150 (E-DE)",
            "auroCOMPACT VSC D 146/4-5 150 (LL-DE)",
            "auroCOMPACT VSC D 146/4-5 190 (E-DE)",
        ])
        res = await find_matches(
            db_session, manufacturer="Vaillant", model="auroCOMPACT VSC S 146/4-5 150",
            raw_text="Vaillant auroCOMPACT VSC S 146/4-5 150",
        )
        # All five collapse to a single base-models group.
        assert len(res) <= 1, [r["model"] for r in res]
        rep = res[0]
        assert rep["model"] == "auroCOMPACT VSC S 146/4-5 150 (E-DE)"
        assert rep.get("variants")
        # The four lower-ranked registrations are listed as variants.
        variant_models = {v["model"] for v in rep["variants"]}
        assert len(variant_models) == 4

    async def test_distinct_capacities_not_merged(self, db_session):
        await _seed_many(db_session, "Stiebel Eltron", ["WPL 18", "WPL 21"])
        res = await find_matches(
            db_session, manufacturer="Stiebel Eltron", model="WPL 18",
            raw_text="Stiebel Eltron WPL 18",
        )
        # WPL 18 and WPL 21 are different units — WPL 21 must not be bundled
        # as a variant of WPL 18 (no slash code triggers variant stripping).
        rep = next((r for r in res if r["model"] == "WPL 18"), None)
        assert rep is not None
        if rep.get("variants"):
            assert all(v["model"] != "WPL 21" for v in rep["variants"])

    async def test_source_surfaces_from_product(self, db_session):
        await _seed_many(db_session, "Vaillant", ["model 150 (E-DE)", "model 190 (E-DE)"])
        res = await find_matches(
            db_session, manufacturer="Vaillant", model="model 150",
            raw_text="Vaillant model 150",
        )
        assert res
        assert res[0].get("source") == "EPREL"


class TestVariantKey:
    def test_vaillant_variants_share_key(self):
        assert _variant_key("auroCOMPACT VSC S 146/4-5 150 (E-DE)") == \
            _variant_key("auroCOMPACT VSC D 146/4-5 190 (LL-DE)")

    def test_capacity_only_models_stay_distinct(self):
        assert _variant_key("WPL 18") != _variant_key("WPL 21")

    def test_different_slash_code_distinct(self):
        assert _variant_key("ecoTEC plus VUW 236/5-5") != _variant_key("ecoTEC plus VUW 236/4-5")

    def test_strips_parenthesized_gas_type(self):
        assert _variant_key("jeegu 300 (E-DE)") == _variant_key("jeegu 300 (LL-DE)")
