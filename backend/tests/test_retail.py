"""Tests for the retail marketplace crawler (heizungsdiscount24) and the
retail enrichment matcher."""

import uuid
import pytest

from app.models.retail_product import RetailProduct
from app.services import retail_crawler
from app.services.retail_crawler import (
    _is_heating_url,
    parse_product_jsonld,
    extract_retail_product,
    _extract_model,
)
from app.services.matching_service import find_retail_matches


VA_PAGE = """
<html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"HeizungsDiscount24 GmbH"}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Vaillant auroCOMPACT VSC S 146/4-5 190 Brennwert-Kompaktger\u00e4t","brand":{"@type":"Brand","name":"Vaillant"},"sku":"Vaillant-VSC-S-146-4-5-190-0010015611","mpn":"0010015611","offers":{"price":"3498.00","priceCurrency":"EUR"}}</script>
</head></html>
"""

GARBLED_PAGE = "<html><body>Keine strukturierten Daten</body></html>"


class TestHeatingFilter:
    def test_gas_heizung_included(self):
        assert _is_heating_url("https://www.heizungsdiscount24.de/gas-heizung/vaillant-aurocompact.html")

    def test_klimaanlagen_excluded(self):
        assert not _is_heating_url("https://www.heizungsdiscount24.de/klimaanlagen/daikin-split.html")

    def test_non_heating_excluded(self):
        assert not _is_heating_url("https://www.heizungsdiscount24.de/zubehoer/rohr.html")


class TestParseJsonLd:
    def test_extracts_product_block(self):
        data = parse_product_jsonld(VA_PAGE)
        assert data is not None
        assert data["@type"] == "Product"
        assert data["mpn"] == "0010015611"

    def test_no_product_block(self):
        assert parse_product_jsonld(GARBLED_PAGE) is None


class TestExtractRetailProduct:
    def test_vaillant_aurocompact(self):
        rec = extract_retail_product(
            VA_PAGE, "https://www.heizungsdiscount24.de/vaillant-aurocompact-0010015611"
        )
        assert rec is not None
        assert rec["brand"] == "Vaillant"
        assert rec["model"] == "auroCOMPACT VSC S 146/4-5 190"
        assert rec["mpn"] == "0010015611"
        assert rec["price"] == 3498.0
        assert rec["currency"] == "EUR"
        assert rec["source"] == "heizungsdiscount24"

    def test_garbled_page_yields_none(self):
        assert extract_retail_product(GARBLED_PAGE, "https://x.de/y") is None


class TestExtractModel:
    def test_vaillant_designation(self):
        assert _extract_model(
            "Vaillant auroCOMPACT VSC S 146/4-5 190 Brennwert-Kompaktgerät", "Vaillant", None
        ) == "auroCOMPACT VSC S 146/4-5 190"

    def test_buderus_code_fallback(self):
        assert _extract_model("Buderus Logamax plus GB172i-24", "Buderus", None) == "GB172i-24"

    def test_heatpump_space_separated(self):
        assert _extract_model("Stiebel Eltron WPL 18 A Wärmepumpe", "Stiebel Eltron", None) == "WPL 18"

    def test_mpn_fallback(self):
        assert _extract_model("", None, "0010015611") == "0010015611"


class TestFindRetailMatches:
    async def _seed(self, db, **kw):
        rec = RetailProduct(
            brand=kw.pop("brand", "Vaillant"),
            model=kw.pop("model", "auroCOMPACT VSC S 146/4-5 190"),
            name=kw.pop("name", "Vaillant auroCOMPACT VSC S 146/4-5 190"),
            url=kw.pop("url", "https://www.heizungsdiscount24.de/vaillant-aurocompact"),
            mpn=kw.pop("mpn", "0010015611"),
            price=kw.pop("price", 3498.0),
            currency=kw.pop("currency", "EUR"),
        )
        db.add(rec)
        await db.flush()
        return rec

    @pytest.mark.asyncio
    async def test_exact_brand_model(self, db_session):
        await self._seed(db_session)
        res = await find_retail_matches(
            db_session, manufacturer="Vaillant", model="auroCOMPACT VSC S 146/4-5 190"
        )
        assert res
        assert res[0]["match_type"] == "retail"
        assert res[0]["retail_url"].startswith("https://www.heizungsdiscount24.de")
        assert res[0]["retail_price"] == 3498.0

    @pytest.mark.asyncio
    async def test_brand_good_model_wrong_rejected(self, db_session):
        await self._seed(db_session)
        res = await find_retail_matches(
            db_session, manufacturer="Vaillant", model="UNRELATED MODEL XYZ"
        )
        assert not res

    @pytest.mark.asyncio
    async def test_no_input_returns_empty(self, db_session):
        await self._seed(db_session)
        assert await find_retail_matches(db_session, None, None) == []
