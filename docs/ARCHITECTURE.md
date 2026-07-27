# Architecture

## System Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│  FastAPI      │────▶│  PostgreSQL   │
│  (SPA HTML)  │     │  Backend      │     │  (prod)       │
└─────────────┘     │              │     │  SQLite (dev)  │
                    │  ┌─────────┐ │     └──────────────┘
                    │  │  OCR    │ │
                    │  │ Pipeline│ │     ┌──────────────┐
                    │  └─────────┘ │────▶│  EPREL API    │
                    │              │     │  (crawler)    │
                    │  ┌─────────┐ │     └──────────────┘
                    │  │Matching │ │
                    │  │ Engine  │ │
                    │  └─────────┘ │
                    └──────────────┘
```

## OCR Pipeline Flow

```
Image Upload
    │
    ▼
┌─────────────────┐
│  Load from bytes │  cv2.imdecode
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Resize for OCR  │  Max 1500px side
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Perspective Correct  │  Find largest rectangle contour
└────────┬────────────┘  Warp if >30% of image area
         │
         ▼
┌─────────────────────┐
│ Contrast Enhancement │  CLAHE on L channel (LAB)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Rotation Correction  │  HoughLinesP → median angle
└────────┬────────────┘  Rotate if >2°
         │
         ▼
┌─────────────────────┐
│    PaddleOCR v3.7   │  PP-OCRv6 detection + recognition
└────────┬────────────┘
         │
         ▼  (if <10 chars detected)
┌─────────────────────┐
│  Fallback: Original  │  Resize only, no preprocessing
│  Image OCR           │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Parse Text          │  Regex extraction
│  - Manufacturer      │  Alias dict for misspellings
│  - Model             │  MODEL_PATTERNS
│  - Energy Class      │  A+++/A++/A+/A/B-G
│  - Heat Output       │  \d+\.?\d*\s*kW
│  - Fuel Type         │  Keyword matching
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Match Products      │  RapidFuzz weighted scoring
│  - Manufacturer 35%  │  token_sort_ratio
│  - Model 35%         │  Dynamic weight redistribution
│  - Energy 10%        │  Raw text fallback search
│  - Fuel 10%          │
│  - Output 10%        │
└─────────────────────┘
```

## Database Schema

```
manufacturers ──────┐
                     ├──▶ products ──────▶ matches ◀──── ocr_results
categories ──────────┘
```

| Table | Records | Purpose |
|-------|---------|---------|
| manufacturers | 28 | Viessmann, Vaillant, Bosch, Daikin, etc. |
| categories | 9 | Gas boilers, heat pumps, biomass, solar, etc. |
| products | 72 | Real EPREL product data with specs |
| ocr_results | varies | Each upload creates one record |
| matches | varies | Top 5 matches per OCR result |
| crawler_logs | varies | EPREL crawler run history |

## Matching Algorithm

The matching engine uses RapidFuzz's `token_sort_ratio` for fuzzy string comparison. Each product is scored against the OCR-extracted fields:

```
composite = (mfr_score × 0.35) + (model_score × 0.35) + 
            (energy_score × 0.10) + (fuel_score × 0.10) + 
            (output_score × 0.10)
```

**Dynamic redistribution:** When manufacturer or model are None (OCR didn't detect them), their weight is redistributed proportionally to the remaining fields. This ensures partial matches still rank products.

**Raw text fallback:** If structured extraction fails, the raw OCR text is compared against product model names using `fuzz.partial_ratio`. This catches cases where OCR reads the model name correctly but the parser misses it.

## Security

- JWT tokens with 24-hour expiry
- bcrypt password hashing
- File upload validation (type + size limits)
- CORS configuration
- Rate limiting on crawler endpoints
