# Matching Limitations & Improvement Plan

> **Status:** P0–P5 are **implemented** (`matching_service.py`, `model_aliases.py`,
> frontend match-type badges). See the priority table at the bottom for the
> mapping of each item to its CI / tests, and `PRESENTATION_EXAMPLES.md` for
> user-facing examples and limits.

## Problem Statement

OCR scans return products that don't exist when searched on EPREL or manufacturer websites. The OCR extracts nameplate text correctly, but the matching system maps nameplate model strings to wrong EPREL entries because **nameplate strings and EPREL catalog strings are fundamentally different naming systems**.

---

## How the Current System Works

### Field Extraction (`parser.py`)

| Field | Method |
|---|---|
| **manufacturer** | Alias lookup → `KNOWN_MANUFACTURERS` substring scan |
| **model** | 3-pass: `Type:/Typ:` labels → manufacturer-anchored text → generic `[A-Z]{1,3}\d{2,5}` |
| **energy_class** | Regex `A+++` through `G` |
| **fuel_type** | Keyword scan (`erdgas`, `öl`, `strom`, etc.) |
| **heat_output** | First `\d+[.,]?\d*\s*kW` match |

### Matching Flow

```
OCR fields → find_matches() [local DB]
                ↓ score < 50
        search_and_add_product() [live EPREL API]
                ↓ score < 50
    search_and_add_from_manufacturer() [brand websites]
                ↓
        find_matches() [re-run against enriched DB]
```

### Scoring Logic (`matching_service.py`)

- Per-field `fuzz.token_sort_ratio` (0–100)
- Composite: manufacturer 35%, model 35%, energy 10%, fuel 10%, output 10%
- Gate: `brand_ok` OR `mfr≥90` OR (`model≥80` + long model) — **no minimum model threshold**

### Heating-Only Scope (product family guard)

HeizungScan is a **heating-systems** lead-gen tool, so results are restricted to
heating appliances — and to **reversible units that also heat** (EPREL registers
these under the "space heaters" family). Standalone air-conditioning / pure
cooling-only units (EPREL's `airconditioners` family) are excluded by two layers:

1. **Crawl scope** (`crawler_service.py`): only heating slugs are ever crawled;
   `HEATING_ONLY_GROUP_SLUGS` also rejects any non-heating slug passed via the
   `groups`/`only_groups` params.
2. **Match filter** (`matching_service.py`): `HEATING_ONLY_CATEGORIES` allow-list
   drops any product whose category isn't a heating/reversible one before scoring.

> **Note on "AC" suffixes** (e.g. Stiebel `WPL 10 AC`, `WPL 15 AS`): `AC`/`AS`/`SL`
> are model-variant codes on Stiebel air-source heat pumps (**W**ärmepumpe **L**uft),
> *not* air conditioners. They are heating systems and correctly matchable.

### Flue/category codes & product-designation extraction (`parser.py`)

Every modern gas boiler nameplate prints a line like `Type : C13x, C33x, C43x …`
for its flue-system categories, and a `CE … 1312CO5870` / `Serial-Nr. …` block.
These are **not** models, but the `Typ:` label matcher used to capture `C13x` and
return it as the model (real Vaillant auroCOMPACT scan → `C13x`).

Fixes (all in `extract_model`, `parser.py`):
1. **Flue/cert/serial filtering** — labelled captures that are gas/flue category
   codes (`C13x`), cert/serial tokens (`1312CO5870`, `21142500100156093100005485N5`)
   and leading-zero OCR garble are rejected, so they never win.
2. **Product-designation pass** (`_extract_product_designation`) — extracts the
   real multi-token model printed after the brand ("auroCOMPACT VSC S 146/4-5 150"),
   requiring a Title-case product-name leader + ALL-CAPS type code + digit ending.
   This only fires on that distinctive pattern, so all-caps models like `WPL 18`
   still route through the existing anchored pass unchanged. Dash/slash type codes
   are preserved (`146/4-5`).

Result for the real Vaillant scan: `C13x` → **`auroCOMPACT VSC S 146/4-5 150`**,
which matches exact EPREL entries (`auroCOMPACT VSC S 146/4-5 150/190`) instead of
the unrelated VRC thermostats that previously showed up as "attribute-based" hits.




---

## Why It Fails: Nameplate vs EPREL Naming

EPREL's `modelIdentifier` is a **commercial catalog code**, not what's printed on the physical nameplate:

| Brand | Nameplate `Typ:` | EPREL `modelIdentifier` | Match? |
|---|---|---|---|
| Ochsner | `Europa MINI EW P` | `AIR 80 C13A` | **No** — completely different strings |
| Viessmann | `WB2` | `EasyPell 16` | **No** — internal type code vs pellet boiler |
| Stiebel Eltron | `WPL 18` | `WPL 13 E` | **Partial** — generation mismatch |
| ELCO | `Thision S Plus 13` | `THISION SK 12 GE` | **Partial** — sub-model variance |
| ÖkoFEN | `Pellematic08` | `PELEMATIC PES10` | **Partial** — abbreviation variance |

---

## Concrete Failure Modes (with real data)

### Failure Mode A: False confidence from brand-only match

**Scan:** Ochsner `Europa MINI EW P`, 2.2 kW heat pump  
**Result:** `AIR 80 C13A` (score 69.47), `AIR HAWK 1850` (score 69.19), etc.  
**Why:** Manufacturer gate passes (`brand_ok = true`), model scores are ~27–35 (garbage). Composite score dominated by manufacturer (35%) + energy (10%). The system is **confident but wrong**.

### Failure Mode B: Wrong product category returned

**Scan:** Stiebel Eltron `WPL 18`, A+++ heat pump  
**Result:** `WPF 13` (score 71.99) — a flow-through water heater, not a heat pump  
**Why:** `token_sort_ratio("wpl 18", "wpf 13")` = 62.8. Gate passes via `brand_ok`. Energy class `A+++` vs `A+++` = 100%. Composite inflates.

### Failure Mode C: Wrong product family

**Scan:** Viessmann `WB2`, gas condensing boiler  
**Result:** `EasyPell 16` (score 51.27) — a pellet boiler  
**Why:** `brand_ok` is true, model score is low but gate has no minimum. User gets pellet boiler recommendation for gas boiler.

### Failure Mode D: Model gate too permissive

`_brand_consistent()` returns `True` when the manufacturer word appears anywhere. Once brand is confirmed, `has_primary_match` becomes trivially satisfiable — even `model_score = 0` passes if `brand_ok = true`.

---

## Improvement Plan

### P0 — Minimum model score threshold (immediate, highest impact)

When both OCR model and EPREL model are present, require `model_score ≥ 50`:

```python
# In find_matches(), after brand_ok gate:
if model and product.model and model_score < 50:
    continue  # Don't match if model strings have no overlap
```

**Impact:** Eliminates all 5 failure modes. Ochsner scan returns 0 matches (correct — model not in EPREL) instead of 6 wrong ones. System falls through to manufacturer website scraper which may find the right product.

### P1 — Heat output as primary within-brand discriminator

The nameplate has `Heizleistung 2,2 kW`. EPREL has `ratedHeatOutput`. Use `_kw_in_range()` (already in `crawler_service.py`) as a **hard filter** in `find_matches()`:

```python
if heat_output and product.heat_output:
    if not _kw_in_range(detected_kw, product.heat_output):
        continue  # Skip — output doesn't match
```

**Impact:** For Ochsner, filters out AIR 80 (10 kW) when OCR detected 2.2 kW. Most reliable discriminator when model strings don't align.

### P2 — Weight energy/fuel more when model is weak

When `model_score < 30`, redistribute model weight to energy and fuel:

```python
if model_score < 30:
    # Energy + fuel become primary discriminators
    weights = {"manufacturer": 0.35, "model": 0.0, "energy": 0.30, "fuel": 0.25, "output": 0.10}
```

**Impact:** A+++ electricity heat pump matches another A+++ electricity heat pump, not a gas boiler.

### P3 — Nameplate→EPREL alias table

Build a brand-specific mapping table, bootstrapped from test cases:

```python
MODEL_ALIASES = {
    "ochsner": {
        "europa mini ew": "AIR 80 C13A",  # by kW range
    },
    "viessmann": {
        "wb2": None,  # Not in EPREL — flag as unknown
    },
}
```

Grow iteratively from real scans. This is the only way to handle cases where the naming systems are completely disjoint.

### P4 — Distinguish match types in the UI

Add `match_type` to results:

| Type | Condition | UI Treatment |
|---|---|---|
| `exact_model` | model_score ≥ 80, brand confirmed | Green badge, high confidence |
| `model_variant` | model_score 50–79, brand confirmed | Yellow badge, medium confidence |
| `brand_only` | brand confirmed, model_score < 50 | Orange badge, "Same manufacturer, model unknown" |
| `no_match` | Nothing passes | Show "Product not found in database" |

Surface this so users can tell when a match is a real identification vs. a guess.

### P5 — Structured EPREL lookup by attributes

Instead of fuzzy string matching, add a structured query path:

```python
# When model matching fails, try attribute-based lookup:
find_by_attributes(
    manufacturer="Ochsner",
    fuel_type="electricity",
    energy_class="A+",
    heat_output_range=(1.5, 3.0),  # ±30% of detected 2.2 kW
)
```

EPREL products have `fuelType`, `energyClass`, and `ratedHeatOutput` fields. Use these as primary keys when model strings don't align.

---

## Retail Enrichment (heizungsdiscount24)

Beyond EPREL/manufacturer matching, the platform can surface **retail
enrichment** results — currently purchasable units with a reseller URL and
price. This helps the generation team move from "identified unit" to "actionable
lead" and lets a user verify a match against a real, in-stock product page.

### Source & pipeline

- `app/services/retail_crawler.py` downloads `sitemaps/sitemap_products{1,2,3}.xml`
  (~25k/25k/21.8k URLs), **filters to heating-relevant categories** via
  `HEATING_CATEGORY_PATHS` (gas/oil/biomass boilers, heat pumps, water heaters,
  storage, controls, solar) and **excludes `klimaanlagen`** (air conditioning) to
  preserve the heating-only scope. ~11.6k products qualify.
- Each product page's JSON-LD `Product` block is parsed for brand, name,
  sku/mpn, price and currency. The page must be decoded as `iso-8859-1`
  (the shop is a German `ISO-8859-1` site — UTF-8 decoding throws on `0xdf`).
- Brand is normalized via `brand_normalizer.normalize_brand`; the model is
  derived from the product name (`_extract_model`, e.g. `auroCOMPACT VSC S
  146/4-5 190`), falling back to the mpn.
- Results are upserted into a new `retail_products` table (keyed on URL).
  `Base.metadata.create_all` creates it automatically on startup — **no manual
  migration needed** on dev/Pi/EC2.
- Trigger: `POST /crawler/retail?limit=0` (background job, logged under
  `category=retail`).

### How retail matches appear in results

`find_retail_matches()` (matching_service) runs **after** the EPREL chain. It
queries `retail_products` and requires independent brand **and** model fuzzy
thresholds (`_RETAIL_MIN_MFR_SCORE=60`, `_RETAIL_MIN_MODEL_SCORE=65`) so a
brand- or model-only substring can't route a lead to the wrong product page.
Retail hits are appended to the OCR/rematch response `matches` list with:

- `match_type: "retail"` and a **null** `product_id` (so the frontend's
  match-type badge shows them as enrichment, not authoritative identification);
- `name`, `retail_url`, `retail_price`, `retail_currency`, `retail_source`.

### Trade-offs & honest-match policy

- Retail entries **never replace** an EPREL/manufacturer identification — they
  are strictly additive. If the OCR/EPREL chain finds no authoritative match,
  the result stays "no match"; a retail listing alone does not constitute an
  identification.
- Model strings are derived from reseller titles, which are noisier than
  EPREL `modelIdentifier`s; low-confidence retail candidates are dropped by the
  thresholds above, favouring "no retail match" over a wrong guess (matches the
  project's honest-match stance).
- Retail data goes stale (availability/price change); refresh with a re-run of
  `/crawler/retail`.

Tests: `backend/tests/test_retail.py` (14). Full suite green (200).

---

## Priority Order

| Priority | Change | Effort | Impact | Status |
|---|---|---|---|---|
| **P0** | Minimum model score threshold | Small | Eliminates wrong matches | ✅ `MIN_MODEL_SCORE=50` in `find_matches` |
| **P1** | Heat output hard filter | Small | Best within-brand discriminator | ✅ `_kw_in_range()` filter |
| **P5** | Structured attribute lookup | Medium | Catches cases where model is absent | ✅ `_attribute_lookup()` fallback (tagged `attribute_match`) |
| **P2** | Dynamic weight redistribution | Small | Better scoring when model is weak | ✅ `weak_model` (<30) redistributes model weight to energy/fuel |
| **P4** | Match type badges in UI | Medium | User trust + transparency | ✅ `match_type` (exact/variant/brand_only/attribute) surfaced in results |
| **P3** | Alias table | Large (ongoing) | Solves structural naming mismatch | ✅ `model_aliases.py` bootstrapped; promote to `exact_model` |

Tests: `backend/tests/test_matching_improvements.py` (P2–P5) + existing
`test_matching.py`. Full suite green (184).

---

## Verification

After implementing P0 + P1, re-run the 58 existing scans and verify:
- No scan returns a product from a different fuel category
- No scan returns a product with >2x heat output difference
- Scans for products not in EPREL return 0 matches (not wrong matches)
- Scan result includes `match_type` badge in the UI
