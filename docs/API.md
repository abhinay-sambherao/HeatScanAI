# API Reference

Base URL: `http://127.0.0.1:8000`

---

## Health & Metrics

### GET /health

Simple health check. No auth required.

```json
{"status": "healthy", "service": "evh-heatscan"}
```

### GET /metrics

System metrics. No auth required.

```json
{
  "products": 606,
  "manufacturers": 182,
  "total_scans": 0,
  "crawler_runs": 2,
  "last_scan": null
}
```

| Field | Description |
|-------|-------------|
| products | Total products in database |
| manufacturers | Total manufacturers |
| total_scans | Number of OCR scans performed |
| crawler_runs | Number of EPREL crawler runs |
| last_scan | ISO timestamp of most recent scan |

---

## OCR

### POST /ocr

Upload a heating system nameplate image for OCR analysis. No auth required.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | JPEG, PNG, WebP, or PDF. Max 20MB. |
| latitude | float | No | GPS latitude of photo location |
| longitude | float | No | GPS longitude of photo location |
| address | string | No | Street address of photo location |
| city | string | No | City of photo location |

**Response:** `200 OK`

```json
{
  "ocr_result_id": "a1b2c3d4-...",
  "manufacturer": "Vaillant",
  "model": "ecoTEC plus 837 VUW",
  "confidence": 84.54,
  "raw_text": "Vaillant ecoTEC plus 837 30 kW Energy Class A",
  "cleaned_text": "Vaillant ecoTEC plus 837 30 kW Energy Class A",
  "matches": [
    {
      "product_id": "uuid",
      "manufacturer": "Vaillant",
      "model": "ecoTEC plus 837 VUW",
      "energy_class": "A",
      "fuel_type": "gas",
      "heat_output": "30 kW",
      "score": 84.62,
      "matched_attributes": {
        "manufacturer": {"score": 100.0, "target": "Vaillant"},
        "energy_class": {"score": 100.0, "target": "A"},
        "heat_output": {"score": 100.0, "target": "30 kW"},
        "raw_text_match": {"score": 85.0, "target": "ecoTEC plus 837 VUW"}
      },
      "reason": "Manufacturer match: Vaillant (100%); Raw text match: ecoTEC plus 837 VUW (85%)"
    },
    {
      "product_id": null,
      "manufacturer": "Vaillant",
      "model": "ecoTEC exclusive 837/5-5",
      "name": "Vaillant ecoTEC exclusive 837/5-5 Brennwert-Kombigerät",
      "match_type": "retail",
      "retail_url": "https://www.heizungsdiscount24.de/gas-heizung/vaillant-ecotec-exclusive-837-5-5.html",
      "retail_price": 2698.0,
      "retail_currency": "EUR",
      "retail_source": "heizungsdiscount24",
      "score": 92.0,
      "reason": "Retail listing (heizungsdiscount24): 2698.0 EUR @ https://…"
    }
  ],
  "latitude": 51.1657,
  "longitude": 10.4515,
  "address": "123 Main St",
  "city": "Berlin",
  "created_at": "2026-07-26T21:04:11"
}
```

| Field | Description |
|-------|-------------|
| ocr_result_id | UUID for the OCR record |
| manufacturer | Extracted manufacturer name (or null) |
| model | Extracted model number (or null) |
| confidence | Overall OCR confidence (0–100) |
| raw_text | Raw text from PaddleOCR |
| cleaned_text | After regex cleanup |
| matches | Top product matches (sorted by score). EPREL matches have a `product_id`; retail-enrichment entries have `match_type: "retail"` plus `name`, `retail_url`, `retail_price`, `retail_currency`, `retail_source` and a null `product_id` |
| latitude | GPS latitude (or null) |
| longitude | GPS longitude (or null) |
| address | Street address (or null) |
| city | City (or null) |
| created_at | ISO timestamp |

**Match fields:**

| Field | Description |
|-------|-------------|
| product_id | UUID of matched product |
| manufacturer | Manufacturer name from DB |
| model | Product model from DB |
| energy_class | Energy efficiency class |
| fuel_type | Fuel type |
| heat_output | Heat output in kW |
| score | Composite match score (0–100) |
| matched_attributes | Per-attribute scores with targets |
| reason | Human-readable match explanation |

**cURL:**
```bash
# Basic scan
curl -X POST http://127.0.0.1:8000/ocr -F "file=@nameplate.jpg"

# Scan with location metadata
curl -X POST http://127.0.0.1:8000/ocr \
  -F "file=@nameplate.jpg" \
  -F "latitude=51.1657" \
  -F "longitude=10.4515" \
  -F "city=Berlin" \
  -F "address=123 Main St"
```

**Errors:**

| Status | Meaning |
|--------|---------|
| 400 | Invalid file type (not JPEG/PNG/WebP/PDF) or >20MB |
| 500 | OCR pipeline failure |

---

## Products

### GET /products

List and search products with pagination and filters. No auth required.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| search | string | — | Search by model or EPREL ID (partial match) |
| page | int | 1 | Page number (1-indexed) |
| page_size | int | 20 | Results per page (1–100) |
| category | string | — | Filter by category name (e.g., "Gas boilers") |
| energy_class | string | — | Filter by energy class (e.g., "A++", "A") |
| fuel_type | string | — | Filter by fuel type (e.g., "gas", "electricity") |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "87766586-...",
      "eprel_id": "EPREL-001",
      "model": "Vitodens 200-W B2HA",
      "energy_class": "A",
      "fuel_type": "gas",
      "manufacturer_name": "Viessmann",
      "category_name": "Gas boilers",
      "heat_output": "24 kW"
    }
  ],
  "total": 606,
  "page": 1,
  "page_size": 50
}
```

**Examples:**

```bash
# Search by model
curl "http://127.0.0.1:8000/products?search=Vitodens&page_size=5"

# Filter by category + energy class
curl "http://127.0.0.1:8000/products?category=Heat%20pumps&energy_class=A%2B%2B%2B"

# Filter by fuel type
curl "http://127.0.0.1:8000/products?fuel_type=gas&page_size=100"
```

### GET /products/{uuid}

Get full product details by internal UUID. No auth required.

**Response:** `200 OK`

```json
{
  "id": "87766586-...",
  "eprel_id": "EPREL-001",
  "manufacturer_name": "Viessmann",
  "category_name": "Gas boilers",
  "model": "Vitodens 200-W B2HA",
  "supplier": "Viessmann",
  "energy_class": "A",
  "heat_output": "24 kW",
  "efficiency": null,
  "fuel_type": "gas",
  "release_date": null,
  "created_at": "2026-07-26T...",
  "raw_json": null
}
```

For EPREL-crawled products, `raw_json` contains the full EPREL API response.

### GET /products/eprel/{eprel_id}

Get full product details by EPREL registration number. No auth required.

Same response format as `GET /products/{uuid}`. Looks up by the human-readable EPREL ID (e.g., `66804`, `EPREL-001`).

**Errors:**

| Status | Meaning |
|--------|---------|
| 404 | Product not found |

---

## Categories

### GET /categories

List all product categories with product counts. No auth required.

```json
[
  {"name": "Biomass boilers", "product_count": 55},
  {"name": "Combination heaters", "product_count": 3},
  {"name": "Gas boilers", "product_count": 27},
  {"name": "Heat pumps", "product_count": 87},
  {"name": "Heat pumps - Air-to-water", "product_count": 16}
]
```

---

## Manufacturers

### GET /manufacturers

List all manufacturers with product counts. No auth required.

```json
[
  {
    "id": "uuid",
    "name": "Viessmann",
    "product_count": 8,
    "created_at": "2026-07-26T..."
  }
]
```

---

## Crawler

### POST /crawler/run

Trigger the EPREL crawler to fetch new products. Runs asynchronously in background.

**Requires authentication** (JWT token).

**Query Parameters:**

| Param | Type | Default | Max | Description |
|-------|------|---------|-----|-------------|
| max_pages | int | 40 | 10000 | Pages per group (1 page = 25 products; 0 = full group) |
| include_extras | bool | false | — | Also crawl control/solar groups (off by default) |
| groups | str | — | — | Comma-separated group slugs to crawl (e.g. `spaceheaters,waterheaters`). Overrides `include_extras`. Enables incremental runs without re-downloading already-crawled exports. |

**Response:** `202 Accepted`

```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Crawler job queued (max_pages=40/group). Check /crawler/logs for status."
}
```

Check job status via `GET /crawler/logs`.

**Behavior:**
- Full pagination: walks every offset until the end of each group (no lossy sampling)
- Crawls 5 core groups by default: space heaters, local space heaters, solid fuel boilers, water heaters, hot water storage tanks
- `include_extras=true` additionally crawls control/solar groups (temperature controls, solar devices)
- Package registrations (space heater packages, solid fuel boiler packages, water heater packages) are compositions — not nameplate-matchable single units — and are excluded entirely
- Respects EPREL rate limit (4 req/s, 0.25s delay)
- Upserts products (never duplicates by eprel_id); commits after every page
- Manufacturer attribution uses the nameplate brand (`supplierOrTrademark`), not the EPREL registrant (`organisation`)
- Creates/updates manufacturers and categories as needed

**cURL:**
```bash
curl -X POST "http://127.0.0.1:8000/crawler/run?max_pages=0" \
  -H "Authorization: Bearer <token>"

# Incremental: only fetch the control/solar groups
curl -X POST "http://127.0.0.1:8000/crawler/run?max_pages=0&groups=spaceheatertemperaturecontrol,spaceheatersolardevice,waterheatersolardevices" \
  -H "Authorization: Bearer <token>"
```

### POST /crawler/retail

Trigger a retail **enrichment** crawl (heizungsdiscount24.de) into the
`retail_products` table. Reads the shop's product sitemaps, filters to
heating-relevant categories (air-conditioning is explicitly excluded), extracts
each product's JSON-LD `Product` block (brand/model/name/price), and stores the
reseller URL. Runs asynchronously and logs progress under `category=retail`.

**Requires authentication** (JWT token).

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 0 | Max product pages to fetch (0 = full crawl, ~11.6k heating products) |

**Response:** same shape as `/crawler/run` (job id, status `queued`, message).

```bash
curl -X POST "http://127.0.0.1:8000/crawler/retail?limit=0" \
  -H "Authorization: Bearer <token>"
```

### GET /crawler/logs

Get paginated crawler run history.

**Requires authentication** (JWT token).

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Results per page |

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "started_at": "2026-07-29T10:00:00",
      "finished_at": "2026-07-29T10:15:00",
      "records_count": 305,
      "status": "success",
      "error_message": null,
      "category": "all"
    }
  ],
  "total": 1
}
```

| Status | Meaning |
|--------|---------|
| queued | Job created, waiting to start |
| running | Crawler actively fetching data |
| success | All groups completed without errors |
| partial | Some groups failed (check error_message) |
| failed | Crawler could not start |

---

## Admin

### GET /admin/dashboard

Summary statistics. **Requires auth** (JWT token).

```json
{
  "total_products": 606,
  "total_manufacturers": 182,
  "total_scans": 0,
  "average_confidence": 0.0,
  "last_crawl": {
    "status": "success",
    "records": 305,
    "finished_at": "2026-07-29T10:15:00"
  },
  "failed_crawler_jobs": 0
}
```

### GET /admin/ocr-history

Paginated OCR scan history. **Requires auth** (JWT token).

**Query Parameters:** `page` (int, default 1), `page_size` (int, default 20, max 100).

```json
{
  "items": [
    {
      "id": "uuid",
      "filename": "nameplate.jpg",
      "confidence": 84.54,
      "latitude": 51.1657,
      "longitude": 10.4515,
      "address": "123 Main St",
      "city": "Berlin",
      "created_at": "2026-07-26T21:04:11"
    }
  ],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

### GET /admin/failed-jobs

List failed/partial crawler jobs. **Requires auth** (JWT token).

```json
{
  "items": [
    {
      "id": "uuid",
      "started_at": "2026-07-29T10:00:00",
      "finished_at": "2026-07-29T10:15:00",
      "records_count": 100,
      "status": "partial",
      "error_message": "Solid fuel boilers: timeout",
      "category": "all"
    }
  ]
}
```

---

## Authentication

### POST /auth/login

Get a JWT token for admin endpoints.

```json
{
  "username": "admin",
  "password": "changeme"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

Use the token in subsequent requests as:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Token expires after 24 hours (configurable via `JWT_EXPIRE_MINUTES`).

---

## Error Responses

All errors follow the format:

```json
{
  "detail": "Error description"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Invalid file type/size, bad parameters |
| 401 | Missing or invalid JWT token |
| 404 | Resource not found (product, endpoint) |
| 500 | Internal server error (OCR failure, DB error, crawler failure) |

---

## Rate Limiting

- **EPREL API crawler:** 4 requests/second (0.25s delay between calls)
- **OCR endpoint:** No artificial limit (PaddleOCR processes serially)
- **Frontend API calls:** No rate limiting implemented
