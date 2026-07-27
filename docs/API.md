# API Reference

Base URL: `http://127.0.0.1:8000`

## Authentication

All admin endpoints require a JWT token.

```
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "changeme"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

Use token in headers: `Authorization: Bearer <token>`

---

## OCR

### POST /ocr

Upload a heating system nameplate image for OCR analysis.

**Request:**
```
Content-Type: multipart/form-data

file: <image file> (JPEG, PNG, WebP, PDF — max 20MB)
```

**Response:**
```json
{
  "ocr_result_id": "uuid",
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
    }
  ],
  "created_at": "2026-07-26T21:04:11"
}
```

**cURL example:**
```bash
curl -X POST http://127.0.0.1:8000/ocr \
  -F "file=@nameplate.jpg"
```

---

## Products

### GET /products

List and search products with pagination.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| search | string | "" | Search by model or EPREL ID |
| page | int | 1 | Page number |
| page_size | int | 20 | Results per page |

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "eprel_id": "EPREL-006",
      "model": "ecoTEC plus 837 VUW",
      "energy_class": "A",
      "fuel_type": "gas",
      "manufacturer_name": "Vaillant"
    }
  ],
  "total": 72,
  "page": 1,
  "page_size": 20
}
```

### GET /products/{id}

Get a single product by ID.

---

## Manufacturers

### GET /manufacturers

List all manufacturers with product counts.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Viessmann",
    "product_count": 8
  }
]
```

---

## Crawler

### POST /crawler/run

Trigger the EPREL web crawler to fetch new products.

**Headers:** `Authorization: Bearer <token>`

### GET /crawler/logs

Get crawler run history.

---

## Health & Metrics

### GET /health

```json
{"status": "healthy", "service": "evh-heatscan"}
```

### GET /metrics

```json
{
  "products": 72,
  "manufacturers": 28,
  "total_scans": 0,
  "crawler_runs": 0,
  "last_scan": null
}
```

---

## Admin

### GET /admin/dashboard

**Headers:** `Authorization: Bearer <token>`

```json
{
  "total_products": 72,
  "total_manufacturers": 28,
  "total_scans": 0,
  "average_confidence": 0.0,
  "last_crawl": null,
  "failed_crawler_jobs": 0
}
```

### GET /admin/ocr-history

**Headers:** `Authorization: Bearer <token>`

```json
{
  "items": [
    {
      "id": "uuid",
      "filename": "nameplate.jpg",
      "confidence": 84.54,
      "created_at": "2026-07-26T21:04:11"
    }
  ]
}
```

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
| 400 | Invalid file type or size |
| 401 | Missing or invalid auth token |
| 404 | Resource not found |
| 500 | Internal server error (OCR failure, DB error) |
