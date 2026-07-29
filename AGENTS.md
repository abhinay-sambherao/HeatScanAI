# Changes Summary

## 1. Installation Year Capture

### Backend (`HeatScanAI/backend/`)

| File | Change |
|---|---|
| `app/models/ocr_result.py` | Added `installation_year: Mapped[Optional[int]]` column (+ `Integer` import) |
| `app/schemas/ocr.py` | Added `installation_year` to `OCRResponse` |
| `app/api/ocr.py` | Added `installation_year: Optional[int] = Form(None)` param, passed to service, included in response |
| `app/services/ocr_service.py` | Added `installation_year` param to `process_upload()`, persisted to `OCRResult`, returned in dict |
| `app/api/admin.py` | Added `installation_year` to admin history response |

### Database
- `ALTER TABLE ocr_results ADD COLUMN installation_year INTEGER;`

### Frontend (`HeatScanAI-frontend/`)

| File | Change |
|---|---|
| `index.html` | Installation year input moved to main modal body (always visible when modal opens). Removed duplicate from manual form. |
| `js/app.js` | Added `installation_year` to `locationData` object. Modal opens automatically after every file upload (not just camera). Installation year read from DOM in `closeLocation()`. Preview badge now clickable to reopen modal. Sent via FormData to API. Displayed in scan results. |
| `css/style.css` | Added cursor pointer + hover effects for location badge, italic style for "add" state. |

## 2. OCR Parser Fixes

**File: `HeatScanAI/backend/app/ocr/parser.py`**

| Issue | Fix |
|---|---|
| Manufacturer "Not detected" for Truma | Added `"Truma"` to `KNOWN_MANUFACTURERS` list |
| Model "Truma S 3004 Serial no." — too long, included "Serial no." suffix | Added `\b` word boundaries and stop words (`Serial`, `S/N`, `No`, `Pin`) to the explicit model label regex. Restricted `Type`/`Typ` matching to start-of-string or after punctuation to avoid matching "Heater type:". |
| Model "DE65" — matched UK postcode as false positive | Replaced simple `re.search()` with multi-candidate collection. Filters candidates with <3 digit content, picks the most digit-rich one. |
| Fuel type not detected for LPG/butane/propane | Added `butane`, `propane`, `lpg` to gas keywords |

## 3. Product Matching Fix

**File: `HeatScanAI/backend/app/services/matching_service.py`**

| Issue | Fix |
|---|---|
| Cross-manufacturer false positive (TECNILIMA electric heater matched to Truma gas heater via raw text substring "W12-300") | Raw text boost (`raw_score * 0.5`) now requires `mfr_score > 30` when manufacturer is detected. Prevents substring matches from overriding a clear manufacturer mismatch. |

## 4. Manufacturer Website Scraper

**File: `HeatScanAI/backend/app/services/manufacturer_scraper.py`**

| Change | Details |
|---|---|
| Added scraper entries for all missing manufacturers | 16 new entries with German/European search URLs: Junkers, Samsung, LG, Beretta, Biasi, Nefit, AWB, Brotje, Viadrus, Chaffoteaux, De Dietrich, Saunier Duval, ATMOS, Thermia, CLAGE, Truma |
| Generic fallback preserved | Unknown manufacturers still get `{name}.com` as a fallback |
