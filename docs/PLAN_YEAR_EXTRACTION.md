# Plan: Auto-extract Installation Year + Prompt if Missing

## Goal
After OCR scan, the system should:
1. **Extract installation/manufacture year** from the nameplate image automatically
2. If year is found → use it immediately in matching
3. If year is NOT found → show matches first (without year), then prompt the user for the year
4. When user provides year → re-run matching with year data and update results

## Current State
- Year is **NOT extracted** from OCR text (parser returns no year)
- Year is **NOT used** in matching (`find_matches()` has no year param)
- Year is collected **before** scanning via the Location modal (user manually enters it)
- Year is stored in DB but has zero effect on matching/scoring

---

## Backend Changes

### 1. `backend/app/ocr/parser.py` — Add year extraction

Add `extract_installation_year(text)` function that searches for year patterns in context:
- `Baujahr: 2006` / `Baujahr 2006`
- `Errichtung 2006` / `Errichtung: 2006`
- `Herstelldatum: 02/2024` / `Herstellungsdatum 2024`
- `Jahr: 2015`
- Standalone 4-digit year (1980–2030) near manufacturer/model lines (within ±2 lines of "Junkers" or "Hersteller")
- The existing `_YEAR_RE` (`^(?:19|20)\d{2}$`) already exists but is only used to **reject** years from model candidates

Include in `extract_fields()` return dict:
```python
{
    "manufacturer": ...,
    "model": ...,
    "energy_class": ...,
    "heat_output": ...,
    "fuel_type": ...,
    "installation_year": 2006,  # NEW — or None
}
```

### 2. `backend/app/services/matching_service.py` — Use year in matching

Add `installation_year` parameter to `find_matches()`:
- Filter out EPREL products whose `release_date` is after the installation year (a 2006 boiler can't use a 2020 product)
- Add a year-proximity bonus to scoring: products released within ±3 years of installation get a small score boost
- Products with no `release_date` in DB are not penalized (many older products lack this field)

### 3. `backend/app/services/ocr_service.py` — Pass year through matching

Update `_persist_and_match()` to pass `installation_year` to all three `find_matches()` calls (initial, EPREL fallback, manufacturer website fallback).

### 4. `backend/app/api/ocr.py` — Add rematch endpoint

New endpoint: `POST /ocr/{ocr_result_id}/rematch`
- Accepts `installation_year: int` as form param
- Re-runs `find_matches()` with the year data
- Updates the OCR result in DB with the year
- Returns updated matches

### 5. `backend/app/schemas/ocr.py` — Add rematch response schema

```python
class RematchResponse(BaseModel):
    ocr_result_id: str
    installation_year: int
    matches: list[OCRMatchResult]
```

---

## Frontend Changes

### 6. `frontend/js/app.js` — Post-scan year prompt

In `renderResults(data)`:
- After rendering results, check if `data.installation_year` is null
- If null → show an inline year prompt below the results:
  ```html
  <div class="year-prompt card">
    <p>Konnten wir das Baujahr nicht自动erkennen. Kennen Sie das Baujahr Ihrer Heizung?</p>
    <div class="year-prompt-input">
      <input type="number" id="year-prompt-input" min="1980" max="2030" placeholder="z.B. 2010">
      <button onclick="submitYearPrompt()">Bestätigen</button>
      <button onclick="skipYearPrompt()">Überspringen</button>
    </div>
  </div>
  ```

### 7. `frontend/js/app.js` — Year prompt handlers

New functions:
- `submitYearPrompt()`:
  - Reads year from input
  - Calls `POST /ocr/{ocr_result_id}/rematch` with the year
  - Updates `window._lastScanData` with new matches + year
  - Re-renders results (year prompt disappears, results update)
  
- `skipYearPrompt()`:
  - Hides the year prompt
  - Results stay as-is (without year)

### 8. `frontend/js/app.js` — Auto-populate year from OCR

In `runOCR()` response handling:
- If `data.installation_year` is present → store in `locationData` and display
- If null → year prompt appears (step 6)

### 9. `frontend/css/style.css` — Year prompt styling

Style the inline year prompt card to match the CD (heizungcheck branding).

---

## Files to Change

| File | Change |
|---|---|
| `backend/app/ocr/parser.py` | Add `extract_installation_year()`, include in `extract_fields()` |
| `backend/app/services/matching_service.py` | Add `installation_year` param to `find_matches()`, year-based filtering |
| `backend/app/services/ocr_service.py` | Pass year to `find_matches()` calls |
| `backend/app/api/ocr.py` | Add `POST /ocr/{id}/rematch` endpoint |
| `backend/app/schemas/ocr.py` | Add `RematchResponse` schema |
| `backend/tests/test_ocr.py` | Tests for year extraction |
| `frontend/js/app.js` | Year prompt in `renderResults()`, `submitYearPrompt()`, `skipYearPrompt()` |
| `frontend/css/style.css` | Year prompt styling |

---

## UX Flow

```
Upload image(s)
    ↓
OCR runs → extracts: manufacturer, model, energy_class, fuel_type, heat_output, installation_year
    ↓
Matching starts immediately (with year if found, without if not)
    ↓
Results displayed
    ↓
If installation_year is null:
    → Show inline prompt: "Couldn't detect year. Do you know it?"
    → [Input] [Confirm] [Skip]
    → User enters year → POST /ocr/{id}/rematch → results update
If installation_year found:
    → Year shown in address box (no prompt needed)
```

---

## Estimated Effort
- Backend parser: ~30 min
- Backend matching + rematch endpoint: ~1 hr
- Frontend year prompt: ~30 min
- Testing: ~30 min
- **Total: ~2.5 hours**
