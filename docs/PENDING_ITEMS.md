# Pending Items & Technical Debt

Status of known outstanding work as of **2026-08-05** (DB snapshot: 132,440 products).
Each item documents: problem, root cause, fix, files touched, acceptance criteria, and status.

| # | Item | Priority | Status |
|---|------|----------|--------|
| 1 | On-demand EPREL search ignores detected fuel type | High | Done |
| 2 | Generic matches for brands absent from DB | Medium | Verified resolved |
| 3 | Frontend location accuracy (Nominatim zoom) | Medium | Verified |
| 4 | AGENTS.md stale / missing change entries | Medium | Done |
| 5 | 2 `test_api.py` event-loop failures | High | Done |
| 6 | No scheduled daily EPREL refresh | Medium | Done |
| 7 | 2-digit German model codes filtered | Low | Verified by design |

---

## 1. On-demand EPREL search ignores detected fuel type

**Priority:** High — directly reduces "excess API use".

### Problem
When no local match is found, `search_and_add_product()` in
`app/services/crawler_service.py` queries the EPREL list endpoint for **all**
groups (`EPREL_PRODUCT_GROUPS + EPREL_EXTRA_GROUPS` = 8 groups) × 3 pages =
**up to 24 HTTP requests per OCR scan**. The OCR pipeline already detects a fuel
type (gas/oil/electricity/biomass/solar) in most cases, which narrows the relevant
EPREL group to 1–2, but this signal is discarded.

### Root cause
`search_and_add_product()` is called from `ocr_service.py` with only
`manufacturer` and `model` (`ocr_service.py:161`). The `fuel_to_groups` mapping
already exists in `crawler_service.py` (lines ~540) but is dead code — the branch
`if model and manufacturer: pass  # search all groups` never uses it.

### Fix
- Add `fuel_type: str | None = None` parameter to `search_and_add_product()`.
- When `fuel_type` is in `fuel_to_groups`, search only those group slugs;
  otherwise keep searching all groups (backwards compatible).
- Pass `fuel_type=merged.get("fuel_type")` from `ocr_service.py`.

### Files
- `app/services/crawler_service.py` — `search_and_add_product()`
- `app/services/ocr_service.py` — call site (line ~161)

### Acceptance criteria
- With `fuel_type="gas"`, EPREL list requests are made only for `spaceheaters`
  (1 group → 3 requests), never the other 7 groups.
- With `fuel_type=None`, behavior unchanged (all groups searched).
- `fuel_to_groups` dead branch removed.

---

## 2. Generic matches for brands absent from the DB

**Priority:** Medium.

### Problem
A scanned unit whose brand is not in the local DB at all (e.g. **Truma** — a
caravan heater, 0 Truma products) previously returned junk generic matches such
as "TERMIA КОP 30,0" / "Ecotermal 011084" / "Dream Maker PS 300".

### Root cause
The old eligibility gate passed products on a *moderate fuzzy brand score alone*
(`mfr_score > 50`). 5-letter brand collisions make token-sort unusable there:
`truma` vs `terma` = 80, `truma` vs `trane` = 60, `truma` vs `termia` = 73.

### Fix (already implemented)
`_brand_consistent()` in `app/services/matching_service.py` requires **hard
evidence** instead of fuzzy scores:
1. detected manufacturer's leading word appears as a whole word in the product
   brand ("Vaillant" → "Vaillant GmbH"), or
2. the product brand's leading word appears verbatim in the OCR raw text
   (the nameplate itself is ground truth).

Fuzzy `mfr_score >= 90`, strong-long-model (`>=80`, len ≥ 8) and near-verbatim
raw (`>=90`) paths remain. Verified result: **Truma S 3004 → 0 matches**;
legit brand+model sweeps still pass 12/12.

### Status
**Verified resolved.** Regression tests in `tests/test_matching.py`
(`TestBrandConsistent`, 8 cases) + 3 failing → passing history documented in
AGENTS.md §5. No further action.

---

## 3. Frontend location accuracy (Nominatim zoom)

**Priority:** Medium.

### Problem
The location badge showed the wrong locality (`halle` instead of `Wahlen` /
`Marktplatz 24, Halle (Saale)`). Nominatim reverse geocoding was called with
`zoom=10`, which only returns the coarse municipality/district, not the real
village/street.

### Root cause
`HeatScanAI-frontend/js/app.js` (getLocationSummary) called
`https://nominatim.openstreetmap.org/reverse?lat=..&lon=..&zoom=10&format=json`.
At zoom 10 the response contains only `address.city`/`address.municipality`.

### Fix (already implemented)
- Reverse geocode now uses `zoom=18` (street-level).
- Extraction preference: `address.city || town || village || municipality ||
  city_district || suburb || county || state`.
- Verified live: zoom 10 → "Kirtorf" only; zoom 18 → "Wahlen",
  "Marktplatz 24, Halle (Saale)".

### Status
Verified live against Nominatim using the exact frontend code path:
`Wahlen, Kirtorf` → zoom 10 "Kirtorf", zoom 18 "Wahlen" (street `Neustädter Weg`);
`Marktplatz 24, Halle (Saale)` → road `Marktplatz`. A browser GPS scan
(hard refresh `Cmd+Shift+R`) is still recommended to confirm end-to-end.

---

## 4. AGENTS.md stale / missing change entries

**Priority:** Medium.

### Problem
`AGENTS.md` §5 still states *"Full model-name crawl in progress: space heaters
57,571 …"* — the crawl is complete. Recent work is undocumented in the summary:
extras crawl (+2,034), DB cleanup, matching gate tightening, location fix,
`groups` crawler param.

### Fix
Rewrite §5 "Verified result" with the final numbers and add a change log for the
latest session. (Section 6 "German Market Focus" already added.)

### Acceptance criteria
- No "in progress" statements contradicting the completed crawl.
- All recent changes listed with file references.

---

## 5. Two `test_api.py` event-loop failures

**Priority:** High — keeps the suite green.

### Problem
`pytest tests/` reports:
```
FAILED tests/test_api.py::test_manufacturers_empty  - RuntimeError: Event loop is closed
FAILED tests/test_api.py::test_admin_dashboard     - RuntimeError: Task <Task pending ...> got Future attached to a different loop
```

### Root cause
`app/database.py` creates one module-level async engine
(`create_async_engine(DB_URL, pool_pre_ping=True)`). The default
`AsyncAdaptedQueuePool` **reuses asyncpg connections across event loops**.
`test_api.py` uses `@pytest.mark.anyio`, which gives each test its own event
loop, so a pooled connection created on a previous test's loop fails on the next
test's checkout (`do_ping` → "attached to a different loop" → "Event loop is
closed"). Tests fail only in a full-file run (isolation passes) because the bad
reuse is timing-dependent.

### Fix
In `app/database.py`, detect the pytest process and use `poolclass=NullPool`
(no pooled connections survive across loops) and skip `pool_pre_ping`:

```python
import sys
from sqlalchemy.pool import NullPool
_running_tests = "pytest" in sys.modules
engine = create_async_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=not _running_tests,
    poolclass=NullPool if _running_tests else None,
)
```

Production (uvicorn) is unaffected — `pytest` is never in `sys.modules` there.

### Acceptance criteria
- `python3 -m pytest tests/` → 100% pass (all 77 tests).

---

## 6. No scheduled daily EPREL refresh

**Priority:** Medium.

### Problem
EPREL publishes fresh export ZIPs daily. The DB is a manual snapshot; new
registrations never arrive automatically.

### Fix
Add an optional asyncio scheduler started from the FastAPI lifespan
(`app/main.py`). Daily at a configurable UTC time it runs
`run_crawler(db, max_pages_per_group=0)` (full re-crawl, idempotent upsert by
`eprel_id`). Disabled by default:

- `CRAWL_SCHEDULE_ENABLED: bool = False`
- `CRAWL_SCHEDULE_HOUR: int = 3` (UTC)
- `CRAWL_SCHEDULE_MINUTE: int = 0`

New module `app/scheduler.py`: `DailyCrawlerScheduler` with start/stop, next-run
delay computation, concurrent-run guard, and error logging.

### Acceptance criteria
- With env `CRAWL_SCHEDULE_ENABLED=true`, the app runs one crawl per day at the
  configured time; shutdown cancels the loop cleanly.
- With the flag unset (default), no background task is created.
- Idempotent: re-running over an up-to-date DB adds 0 rows.

---

## 7. 2-digit German model codes filtered

**Priority:** Low.

### Problem
OCR model extraction (`app/ocr/parser.py::extract_model`) drops candidates with
fewer than 3 digit characters, so short German boiler models like **"SBK 15"**
or **"WGB 22"** are not extracted from *unlabelled* nameplate text
(→ `model: None`; matching falls back to brand + raw text).

### Root cause
The `num_digits < 3` filter is load-bearing: it prevents the **"DE65 5BG"** UK
postcode false positive. `"SBK 15"` and `"DE65"` have the same shape (2 letters +
2 digits), so they are indistinguishable without context.

### Current state (verified)
- **Labeled** nameplates work: `Typ: SBK 15` → `"SBK 15"` (via `MODEL_PATTERNS`,
  which is not digit-filtered).
- **Unlabeled** `Brötje EuroCondens SBK 15` → `None` (generic path, filtered).
- `Foston DE65 5BG` → `None` (correctly rejected).

### Recommendation
**Keep by design.** Relaxing the generic filter re-opens the postcode bug.
If 2-digit extraction is ever required, scope it to label context only
(`Typ:`/`Model:`/`Modell:`), which already works. Mark resolved/decided; no code
change.

---

## Verification / regression notes

- Matching gate: `truma`/`termia`/`trane`/`terma` must never match (`TestBrandConsistent`).
- Crawler: `COUNT(*) = COUNT(DISTINCT eprel_id)`; no `;`/`Paket` composition brands.
- German majors: OCR resolves `Brötje` (umlaut/ASCII/transcription) and
  `STIEBEL-ELTRON` (hyphen/space) to canonical DB brands.
- Model extraction: `Typ: SBK 15` → `SBK 15`; `DE65 5BG` → `None`.
