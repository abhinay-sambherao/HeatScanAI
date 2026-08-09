# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (HeatScanAI-frontend/)                                │
│  Single-page HTML app (DE/EN i18n · GDPR consent first)        │
│  Views: Upload (camera + file) | Products | Dashboard           │
│  Served via: http://127.0.0.1:8000/ (same origin)              │
│  Lang: browser default DE, toggle EN/DE in nav                  │
│  Consent: GDPR modal before first scan                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │ fetch() — same origin, no CORS needed
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI Backend (port 8000)                                     │
│                                                                  │
│  ┌──────────────┐    ┌─────────────────┐    ┌────────────────┐ │
│  │  OCR Pipeline │───▶│  Matching Engine │───▶│  PostgreSQL    │ │
│  │  (PaddleOCR)  │    │  (RapidFuzz)     │    │  (534 prods)   │ │
│  └──────────────┘    └─────────────────┘    └────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Fallback Chain                                              │ │
│  │  Local DB (534) → EPREL API (on-demand search)              │ │
│  │  → Manufacturer websites (19 brands, BeautifulSoup)          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  API Endpoints                                              │ │
│  │  /ocr · /products · /products/eprel/{id} · /categories     │ │
│  │  /manufacturers · /crawler/run · /crawler/logs             │ │
│  │  /health · /metrics · /admin/dashboard · /admin/ocr-history│ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## OCR Pipeline (End-to-End)

```
Upload (JPEG/PNG/WebP/PDF, max 20MB)
    │
    ├─ POST /ocr (multipart/form-data)
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  1. PREPROCESSOR (OpenCV)                                        │
│                                                                  │
│  ┌─────────────────────┐                                         │
│  │ load_from_bytes()    │  cv2.imdecode → numpy array            │
│  └─────────┬───────────┘                                         │
│            ▼                                                      │
│  ┌─────────────────────┐                                         │
│  │ resize_for_ocr()     │  Max 1500px on longest side            │
│  │                      │  Preserves aspect ratio                │
│  └─────────┬───────────┘                                         │
│            ▼                                                      │
│  ┌─────────────────────┐                                         │
│  │ correct_perspective()│  Find largest rectangular contour      │
│  │                      │  via Canny + contour detection         │
│  │                      │  Apply warpPerspective if >30% area    │
│  └─────────┬───────────┘                                         │
│            ▼                                                      │
│  ┌─────────────────────┐                                         │
│  │ enhance_contrast()   │  CLAHE on L channel in LAB color space │
│  │                      │  clipLimit=2.0, tileGridSize=8×8       │
│  └─────────┬───────────┘                                         │
│            ▼                                                      │
│  ┌─────────────────────┐                                         │
│  │ correct_rotation()   │  HoughLinesP → detect dominant angle   │
│  │                      │  Rotate only if median angle > 2°      │
│  └─────────────────────┘                                         │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. TEXT EXTRACTION (PaddleOCR v3.7)                             │
│                                                                  │
│  PaddleOCR PP-OCRv6 model (English)                              │
│  Lazy-initialized singleton (loaded once, reused)                │
│  Returns: list of (text, confidence) pairs                       │
│                                                                  │
│  Each text + score is aggregated into:                           │
│  - full_text: "Vaillant ecoTEC plus 837 30 kW Class A"          │
│  - avg_confidence: 0.875 → 87.5%                                 │
│                                                                  │
│  FALLBACK: If preprocessed image yields <10 chars,               │
│  re-run OCR on original (resized-only) image.                    │
│  This handles cases where preprocessing degrades the image.      │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. PARSER (Regex Extraction)                                    │
│                                                                  │
│  clean_text():                                                   │
│  - Remove non-alphanumeric noise (except spaces, hyphens, dots)  │
│  - Normalize "0"→"O" between letters (OCR artifact fix)          │
│  - Normalize "l"→"1" before digits                               │
│                                                                  │
│  Manufacturer:                                                   │
│  - Check MANUFACTURER_ALIASES dict first (common OCR typos)      │
│    e.g., "villent" → "Vaillant", "viessman" → "Viessmann"       │
│  - Fallback: scan KNOWN_MANUFACTURERS list (37 brands)           │
│  - Case-insensitive matching                                     │
│                                                                  │
│  Model:                                                          │
│  - Pattern 1: "Model:" / "Modell:" / "Type:" / "Typ:" prefix    │
│  - Pattern 2: Alphanumeric codes like "VUW 837/4"               │
│                                                                  │
│  Energy Class:                                                   │
│  - Regex: A+++ / A++ / A+ / A–G                                 │
│  - Case-insensitive, word-boundary anchored                      │
│                                                                  │
│  Heat Output:                                                    │
│  - Regex: digits followed by "kW" (case-insensitive)             │
│  - Returns "30 kW" format                                        │
│                                                                  │
│  Fuel Type:                                                      │
│  - Keyword matching against 6 categories:                        │
│    gas, oil, electricity, wood/biomass, solar, district_heating  │
│  - Supports German keywords (Erdgas, Öl, Wärmepumpe, etc.)      │
│  - Case-insensitive substring search                             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. MATCHING ENGINE (RapidFuzz)                                  │
│                                                                  │
│  For each product in database (606 total):                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  fuzz.token_sort_ratio(query, target) for each field:       │ │
│  │  - Manufacturer × 0.35 weight                               │ │
│  │  - Model × 0.35 weight                                      │ │
│  │  - Energy class × 0.10 weight                               │ │
│  │  - Fuel type × 0.10 weight                                  │ │
│  │  - Heat output × 0.10 weight                                │ │
│  │                                                             │ │
│  │  Dynamic redistribution: If manufacturer is None (OCR       │ │
│  │  didn't detect it), its 0.35 weight is redistributed to     │ │
│  │  the remaining fields proportionally.                       │ │
│  │                                                             │ │
│  │  Raw text fallback: fuzz.partial_ratio(raw_text, model)     │ │
│  │  Blended into composite score (up to 50% boost).            │ │
│  │  This catches cases where the parser misses a field but     │ │
│  │  the raw OCR text contains the model name.                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Results sorted by score (descending), top 5 returned.           │
│  Products with composite < 5.0 are filtered out.                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  5. PERSISTENCE                                                  │
│                                                                  │
│  - OCRResult saved to ocr_results table (+ location metadata)    │
│  - Top 5 Matches saved to matches table (linked to OCR + Product)│
│  - Response returned to frontend with all fields + match details │
└──────────────────────────────────────────────────────────────────┘
```

---

## EPREL Crawler

```
POST /crawler/run (triggers background task)
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  1. Create CrawlerLog entry (status="queued")                    │
│  2. Background task starts (_run_crawler_background)             │
│  3. httpx.AsyncClient with:                                      │
│     - User-Agent: FastAPI-HeatScanAI/1.0                        │
│     - X-API-KEY: (from .env, if set)                            │
│     - Rate limit: 4 req/s (0.25s delay between requests)        │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. For each of 11 product groups (in order):                    │
│                                                                  │
│  Core groups (4):                                                │
│  - spaceheaters (heat pumps, gas, oil, combination)              │
│  - localspaceheaters (stoves, fireplaces)                        │
│  - solidfuelboilers (biomass, pellet)                            │
│  - waterheaters                                                  │
│                                                                  │
│  Extra groups (7):                                               │
│  - solidfuelboilerpackages                                       │
│  - spaceheaterpackages                                           │
│  - spaceheatertemperaturecontrol                                 │
│  - spaceheatersolardevice                                        │
│  - waterheaterpackages                                           │
│  - hotwaterstoragetanks                                          │
│  - waterheatersolardevices                                       │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  5. For each group, fetch 13 offset samples:                     │
│                                                                  │
│  OFFSET_SAMPLES = [0, 25, 50, 100, 500, 1000, 2000,             │
│                    5000, 7500, 10000, 15000, 25000, 50000]       │
│                                                                  │
│  WHY OFFSET SAMPLING?                                            │
│  EPREL API ignores the page parameter (always returns same      │
│  page 1 results). But different offset values return different   │
│  product sets. We sample a wide range to maximize unique         │
│  product discovery.                                              │
│                                                                  │
│  Each request: GET /api/products/{group}?offset={n}&size=25      │
│  Response contains up to 25 products per page.                   │
│  11 groups × 13 offsets × 25 products = max ~3,575 products     │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  6. For each hit (product), PARSING:                             │
│                                                                  │
│  Extract fields from EPREL JSON:                                 │
│  - eprelRegistrationNumber → eprel_id (unique key)              │
│  - modelIdentifier → model                                       │
│  - organisation.organisationTitle → manufacturer name            │
│  - energyClass → mapped via _map_energy_class():                 │
│    "APPP" → "A+++", "APP" → "A++", "AP" → "A+"                 │
│  - type → mapped to category via EPREL_TYPE_TO_CATEGORY          │
│    "HEAT_PUMP" → "Heat pumps", "GAS_BOILER" → "Gas boilers"    │
│  - type → mapped to fuel via EPREL_TYPE_TO_FUEL                  │
│    "HEAT_PUMP" → "electricity", "GAS_BOILER" → "gas"           │
│  - ratedHeatOutput → formatted as "24 kW"                       │
│  - supplierOrTrademark → supplier                                │
│                                                                  │
│  For groups without type field, fallback to group-level          │
│  defaults (GROUP_FUEL_FALLBACK, GROUP_CATEGORY_FALLBACK).        │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  7. UPSERT to database:                                          │
│                                                                  │
│  Manufacturer lookup/cache:                                      │
│  - Check manufacturer_cache dict (per run)                       │
│  - If not cached, query DB by name                               │
│  - If not in DB, create new Manufacturer row                     │
│                                                                  │
│  Category lookup/cache (same pattern as manufacturer):           │
│  - Name matched from EPREL type mapping                          │
│                                                                  │
│  Product upsert:                                                 │
│  - Check if eprel_id exists in DB                                │
│  - EXISTS → update model, supplier, energy_class,                │
│              heat_output, fuel_type, category_id, raw_json       │
│  - NEW → insert with fresh UUID                                  │
│                                                                  │
│  Never duplicates by eprel_id.                                   │
│  Raw JSON stored in raw_json column for debugging.               │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  8. Complete:                                                    │
│  - CrawlerLog updated: status, records_count, finished_at        │
│  - Status: "success" (no errors), "partial" (some groups failed) │
│  - Last run: 305 new records → 606 total products                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌────────────────┐       ┌──────────────────┐      ┌────────────────────┐
│  manufacturers  │       │   categories      │      │   crawler_logs      │
│────────────────│       │──────────────────│      │────────────────────│
│  id (UUID, PK)  │──┐   │  id (UUID, PK)     │─┐   │  id (UUID, PK)      │
│  name (unique)  │  │   │  name (unique)     │ │   │  started_at         │
│  created_at     │  │   │  eprel_category_id │ │   │  finished_at        │
└────────────────┘  │   │  created_at        │ │   │  records_count      │
                    │   └────────────────────┘ │   │  status              │
                    │                           │   │  error_message       │
                    ▼                           ▼   │  category            │
               ┌────────────────────────────────────┐  │  created_at         │
               │  products                          │  └────────────────────┘
               │───────────────────────────────────│
               │  id (UUID, PK)                     │
               │  eprel_id (unique, indexed)        │
               │  manufacturer_id (FK → mfrs)      │
               │  category_id (FK → categories)     │
               │  model (indexed)                   │
               │  supplier                          │
               │  energy_class                      │
               │  heat_output                       │
               │  efficiency                        │
               │  fuel_type                         │
               │  release_date                      │
               │  raw_json (JSON→dict)              │
               │  created_at                        │
               │  updated_at                        │
               └──────────┬─────────────────────────┘
                          │
                          ▼
                ┌────────────────────┐      ┌────────────────────┐
                │  matches           │      │  ocr_results       │
                │───────────────────│      │───────────────────│
                │  id (UUID, PK)     │      │  id (UUID, PK)     │
                │  ocr_result_id(FK) │◀─────│  filename           │
                │  product_id (FK)   │      │  raw_text           │
                │  score             │      │  cleaned_text       │
                │  matched_attributes│      │  confidence         │
                │  reason            │      │  image_path         │
                │  created_at        │      │  latitude (opt)     │
                └────────────────────┘      │  longitude (opt)    │
                                            │  address (opt)      │
                                            │  city (opt)         │
                                            │  created_at         │
                                            └────────────────────┘
```

**Current Row Counts (as of July 29, 2026):**

| Table | Count | Notes |
|-------|-------|-------|
| manufacturers | ~200 | Viessmann, Vaillant, Bosch, Daikin, etc. |
| categories | 11 | Gas boilers, heat pumps, biomass, solar, etc. |
| products | 534 | All real EPREL (72 fake seeds deleted) |
| ocr_results | — | Created per upload (+ location metadata) |
| matches | — | 5 per OCR result |
| crawler_logs | — | One per crawler run |

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend framework | FastAPI | 0.115.6 |
| ASGI server | Uvicorn | 0.34.0 |
| ORM | SQLAlchemy (async) | 2.0.36 |
| Database | PostgreSQL (asyncpg) | 0.30.0 |
| OCR engine | PaddleOCR (PP-OCRv6) | 3.7.0 |
| DL framework | PaddlePaddle | 3.3.1 |
| Image processing | OpenCV | 4.10.0 |
| Fuzzy matching | RapidFuzz | 3.11.0 |
| HTTP client | httpx | 0.28.1 |
| Validation | Pydantic | 2.10.4 |
| Logging | structlog | 24.4.0 |
| Frontend | Plain HTML/CSS/JS | — |
| Auth | python-jose (JWT) | 3.3.0 |

---

## Key Design Decisions

1. **Offset sampling over pagination**: EPREL API ignores `page` parameter but returns different results at different `offset` values. Sampling 13 offsets maximizes unique product coverage.

2. **Lazy PaddleOCR singleton**: PaddleOCR model (~80MB) loaded once on first OCR request, reused for all subsequent scans.

3. **Preprocessing fallback**: If preprocessed image yields <10 chars, falls back to original resized image. This handles cases where CLAHE or perspective correction degrades the image.

4. **Dynamic weight redistribution**: Missing OCR fields don't sink the matching score — weights are redistributed to detected fields.

5. **Raw text fallback**: Even when structured extraction fails, the raw OCR text is fuzzy-matched against product model names as a safety net.

6. **Same-origin serving**: Frontend served from `http://127.0.0.1:8000/` to avoid CORS entirely in production use.

7. **Conditional API key**: EPREL API key sent only when configured, used only on list endpoints returning >1 model per EPREL specification.

8. **German-first i18n**: Default language is German (browser detection), with EN/DE toggle stored in localStorage. All UI strings in a single `translations` object.

9. **GDPR consent flow**: First-visit modal explains data processing (images, OCR, location). Scan blocked until consent given. Consent stored in localStorage, revocable via nav button.

10. **Camera capture**: Uses `getUserMedia` with `facingMode: environment` for rear camera. Captures JPEG frame via `<canvas>` at 92% quality.

11. **Location metadata**: Three input modes (GPS geolocation + reverse geocode via Nominatim, manual street/city/lat-lng, skip). Stored per scan in `ocr_results.latitude/longitude/address/city`.

12. **Three-stage fallback chain**: Local DB → EPREL API (fast, structured) → Manufacturer websites (19 brands, best-effort scraping). Both fallbacks auto-add products to DB for future scans.
