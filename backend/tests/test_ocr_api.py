"""Tests for OCR API response serialization."""
from __future__ import annotations

import uuid

from app.api.ocr import _match_to_schema


def test_match_to_schema_includes_source_and_variants():
    m = {
        "product_id": uuid.uuid4(),
        "manufacturer": "Vaillant",
        "model": "auroCOMPACT VSC S 146/4-5 150 (E-DE)",
        "source": "EPREL",
        "variants": [
            {"model": "auroCOMPACT VSC D 146/4-5 150 (LL-DE)", "score": 91.0},
        ],
        "energy_class": "A",
        "fuel_type": "gas",
        "heat_output": "24 kW",
        "score": 95.0,
        "match_type": "exact_model",
        "matched_attributes": {},
        "reason": "Manufacturer match",
    }
    out = _match_to_schema(m)
    assert out.source == "EPREL"
    assert out.variants is not None
    assert len(out.variants) == 1
    assert out.variants[0].model.startswith("auroCOMPACT")


def test_match_to_schema_includes_retail_fields():
    m = {
        "product_id": None,
        "manufacturer": "Vaillant",
        "model": "ecoTEC exclusive 837/5-5",
        "name": "Vaillant ecoTEC exclusive 837/5-5",
        "source": "heizungsdiscount24",
        "match_type": "retail",
        "retail_url": "https://example.com/product",
        "retail_price": 2698.0,
        "retail_currency": "EUR",
        "retail_source": "heizungsdiscount24",
        "score": 88.0,
        "reason": "Retail listing",
    }
    out = _match_to_schema(m)
    assert out.product_id is None
    assert out.retail_url == "https://example.com/product"
    assert out.retail_price == 2698.0
    assert out.retail_currency == "EUR"
    assert out.retail_source == "heizungsdiscount24"
