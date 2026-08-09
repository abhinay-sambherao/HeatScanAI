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

## 5. EPREL Data Quality — Manufacturer Attribution & Model List

### Problem (from client meeting, Jul 30)

- "tecnilima - Equipamentos e Serviços Lda W12-300" could not be identified as a heating system.
  Verified: the product is real (EPREL registration `1777662`, water heaters, model `W12-300`, brand **Wertec**).
  Tecnilima is the Portuguese *importer* that registered it — it is not the manufacturer.
- "Weishaupt WarmAir 3000" is fictional — it only existed as demo seed data in `scripts/seed_db.py` with a fake EPREL ID (`EPREL-062`). It was never in the live database.

### Root cause

`_extract_manufacturer_name()` in `backend/app/services/crawler_service.py` preferred the EPREL
registrant (`organisation.organisationTitle`, often an importer) over the nameplate brand
(`supplierOrTrademark`). 502 of 534 live products were mis-attributed.

### Fixes

| File | Change |
|---|---|
| `backend/app/services/crawler_service.py` | `_extract_manufacturer_name()` now returns brand (`supplierOrTrademark` → `trademarkOwner` → `organisation`). `supplier` field now stores the registrant. Upsert also refreshes `manufacturer_id`. `run_crawler()` rewritten for full pagination (walks every offset; commits per page; rollback on group failure) instead of lossy offset sampling. Core groups now 5 (added `hotwaterstoragetanks`); package/control groups moved to `include_extras` (off by default). Fixed missing `return log`. |
| `backend/app/api/crawler.py` | Added `include_extras` query param to `POST /crawler/run`. |
| `scripts/audit_manufacturers.py` | NEW: audits/fixes manufacturer attribution from stored `raw_json`. Dry-run by default; `--apply` writes. Skips package-description "brands" (contains `;` / `Paket` / >60 chars). |
| `scripts/seed_db.py` | Removed fabricated Weishaupt products (`WarmAir 3000`, `GSW 200 HL`, `LGB 20-40T`) and the `Weishaupt` seed manufacturer. |
| `backend/tests/test_crawler.py` | Updated manufacturer-extraction tests to brand-first behavior. |
| `docs/API.md` | Updated `POST /crawler/run` params and behavior. |

### Verified result

- `eprel_id 1777662` now: manufacturer **Wertec**, supplier `TECNILIMA - EQUIPAMENTOS E SERVICOS LDA`.
- 469 manufacturer re-attributions applied; 25 package products skipped (junk brand text).
- Full crawl complete: **128,378 records** (space 65,500 / local space 31,754 / solid fuel 8,118 /
  water 14,856 / storage tanks 8,456); 893 null-model/package records skipped. Products table
  132,440 after extra-group crawl and cleanup (see §7).

## 7. Data Completion, Cleanup & Pipeline Hardening

### Extra groups + incremental crawl

| File | Change |
|---|---|
| `backend/app/services/crawler_service.py` | `EPREL_EXTRA_GROUPS` now holds only real single products: temperature controls + 2× solar devices. Package groups (`spaceheaterpackages` ~111k, `solidfuelboilerpackages`, `waterheaterpackages`) are **excluded entirely** — they store composition strings in `supplierOrTrademark`, not nameplate-matchable units. Added `only_groups` param to `run_crawler` so incremental runs skip already-crawled groups (avoids re-downloading exports). Added category fallbacks: `spaceheatertemperaturecontrol`→"Temperature controls", `spaceheatersolardevice`/`waterheatersolardevices`→"Solar thermal collectors". |
| `backend/app/api/crawler.py` | `POST /crawler/run` accepts `groups` (comma-separated slugs, overrides `include_extras`). |
| `docs/API.md` | Documented `groups` param + incremental example. |

Result: **+2,034 products** (controls 1,028 / solar 203 / water-solar 803). DB = 132,442
(distinct eprel_id = row count, zero duplicates).

### DB cleanup (backup `/tmp/evh_backup/evh_heatscan_pre_cleanup_20260805.sql.gz`)

- Deleted 62 **orphan manufacturers** (0 products — registrant legal names superseded by
  brand-first attribution, e.g. `Bosch Thermotechnik GmbH` → `Bosch`).
- Deleted 2 **test records** (`a` name+model "a", `PTC TESTİNG` model "A" — EPREL test entries
  from a certification body). Kept DAYGAS/GOLDMASTER/İNOKSAN/KUAS etc. (real brands registered
  *via* the testing body as agent).
- Normalized `A.O. smith` → `A.O. Smith` (81 products).
- Kept long legal names (DEFRO, Ulrich Brunner) — they are real manufacturers, not junk.

### Matching gate tightening (Truma false-positive fix)

`backend/app/services/matching_service.py`: `_brand_consistent()` replaces fuzzy-brand-only
eligibility with hard evidence (detected-manufacturer word in product brand, or product brand
verbatim in OCR raw text). Fuzzy `mfr>=90`, strong-long-model `>=80`, near-verbatim raw `>=90`
paths kept. Verified: **Truma S 3004 → 0 matches** (was 5 junk TERMIA/TRANE/Terma hits);
12-product sweep 12/12; regression tests in `tests/test_matching.py::TestBrandConsistent`.

### Frontend location accuracy

`HeatScanAI-frontend/js/app.js`: Nominatim reverse-geocode `zoom=10`→`zoom=18`; locality
extraction preference `city‖town‖village‖municipality‖city_district‖suburb‖county‖state`.
Verified: zoom 10 → "Kirtorf"; zoom 18 → "Wahlen", "Marktplatz 24, Halle (Saale)".
**Verified** live against Nominatim: `Wahlen, Kirtorf` zoom 10 → "Kirtorf", zoom 18 → "Wahlen"
(street `Neustädter Weg`); `Marktplatz 24, Halle (Saale)` → road `Marktplatz`. A browser GPS run
is still recommended to confirm end-to-end.

### Test suite green (was 2 pre-existing failures)

`backend/app/database.py`: engine uses `poolclass=NullPool` + no `pool_pre_ping` when running
under pytest (anyio gives each test its own event loop; the default pool reused asyncpg
connections across loops → "Event loop is closed"). **84/84 tests pass** (+2 crawler
group-filter, +5 scheduler).

### Daily refresh scheduler (optional, off by default)

New `backend/app/scheduler.py` `DailyCrawlerScheduler`, started from `app/main.py` lifespan,
runs the full crawl daily at `CRAWL_SCHEDULE_HOUR:MINUTE` UTC. Gated by
`CRAWL_SCHEDULE_ENABLED` (default false). Config fields in `app/config.py`; tests in
`tests/test_scheduler.py`.

### On-demand EPREL search restricted by fuel type

`search_and_add_product()` (crawler_service) now takes `fuel_type` and only queries the
groups relevant to it (`fuel_to_groups`), cutting up to 8× API requests per scan when the
fuel is known. Wired from `ocr_service.py`. Unknown fuel → all groups (unchanged). Tests:
`tests/test_crawler.py::TestSearchAndAddProductGroupFilter`.

### Verified by design (no change)

- **2-digit German models** ("SBK 15", "WGB 22"): label path (`Typ:`/`Model:`) works; the
  unlabeled generic path intentionally filters them to keep the DE65-postcode fix.
- **Uncategorized rows**: 20,758 `BOILER`/`COGENERATION`/empty-type products have no fuel
  field in EPREL; left unmapped deliberately. `LOW_TEMPERATURE_HEAT_PUMP`→"Heat pumps"
  backfilled 3,893 rows.
- **Generic matches for absent brands** (e.g. Truma): already suppressed by `_brand_consistent`.

## 6. German Market Focus

### Market context

~90% of installed heating systems in Germany come from a small set of German brands.
The "Big Three" — **Bosch Group (Bosch/Buderus/Junkers), Vaillant, Viessmann** — cover
roughly 50–65% of the market; adding **Stiebel Eltron, Wolf, Weishaupt, Brötje** reaches ~90%.
Algorithms (OCR brand detection, website scraper) prioritize these brands.

### Changes

| File | Change |
|---|---|
| `backend/app/ocr/parser.py` | `KNOWN_MANUFACTURERS` reordered so the 7 German majors are checked first. Added umlaut/hyphen nameplate spellings: `Brötje`, `Broetje`, `Stiebel-Eltron` (keep ASCII `Brotje` too). `MANUFACTURER_ALIASES` deduped and expanded for the majors (OCR garble: `valiant`/`vaillat`→Vaillant, `viesman`/`viesmann`/`vissmann`→Viessmann, `brötje`/`broetje`/`brotje`→Brötje, `stiebel-eltron`→Stiebel Eltron). |
| `backend/app/services/manufacturer_scraper.py` | Added `brötje` config key (same broetje.de URLs as `brotje`) so the canonical OCR output still finds the site config. |
| `backend/tests/test_ocr.py` | +11 regression tests: umlaut/ASCII/transcription Brötje, hyphen/space Stiebel Eltron, Vaillant/Viessmann OCR typos, Weishaupt/Wolf, Bosch/Junkers. |

### Note

DB already stores the canonical names: `Brötje` (529 products), `STIEBEL ELTRON` (811).
Model extraction intentionally still filters <3-digit codes (e.g. `SBK 15`) to avoid the
fixed DE65-postcode / short-fragment false positives; nameplate `Typ:`/`Model:` labels
still resolve those.

## 8. German Nameplate Dataset Insights & OCR Crash Isolation

### Dataset analysis (`docs/Kopie von Testdata_images_checked.xlsx - Tabelle1.csv`)

14 German nameplate test cases, 7 brands (Buderus, Sieger, Viessmann×4, ELCO, Junkers,
Ochsner, ÖkoFEN, Stiebel Eltron, Vaillant), only ~1 clean EPREL hit. Pre-2014 units are
legally absent from EPREL → the fallback chain (Local DB → EPREL → website) does most of
the work. Top miss reasons: model-string variance (`Vitodens 300-15 40/30`, `Thision S Plus`
vs `L PLUS`) and 4 brands missing from the pipeline entirely.

| File | Change |
|---|---|
| `backend/app/ocr/parser.py` | Added `ÖkoFEN`/`OekoFEN`, `Ochsner`/`Ochsner Wärmepumpen`, `ELCO`, `Sieger` to `KNOWN_MANUFACTURERS`; aliases `ökofen`/`oekofen`→ÖkoFEN, `ochsner`→Ochsner, `elco`→ELCO, `sieger`→Sieger. Added `strom`/`heizstrom` to electricity `FUEL_KEYWORDS` (fixes nameplate `Stom` typo case). |
| `backend/app/services/crawler_service.py` | `heat_output` param on `search_and_add_product`; new `_extract_kw` (numbers, `17.2 kW`, comma decimals) and `_kw_in_range` (band = `max(2.0 kW, 0.25 * detected)`); EPREL hits with `ratedHeatOutput` outside the band are skipped before fuzzy matching. |
| `backend/app/services/ocr_service.py` | Passes `heat_output` from OCR fields into `search_and_add_product`. |
| `backend/app/services/manufacturer_scraper.py` | Added configs for `ökofen` (oekofen.com/de-de), `ochsner` (ochsner.com/de-de), `elco` (elco.net/de). Sieger has **no config**: the brand is discontinued and its former domains redirect to a parked page / Bosch Home Comfort. |
| `backend/tests/test_crawler.py` | +`TestExtractKw` (5), +`TestKwInRange` (5). |

### PaddlePaddle crash isolation (macOS "Python quit unexpectedly")

Three identical crash reports (`~/Library/Logs/DiagnosticReports/Python-2026-08-0{3,5,6}*.ips`)
showed `SIGSEGV`/`EXC_CRASH` inside `paddle::framework::ThreadPoolTempl<...>::WorkerLoop`
while the server was idle in uvicorn — PaddlePaddle 3.3.1 segfaults on Apple Silicon even
when not doing inference, killing the whole API process. OCR now runs in a **persistent
subprocess** so a native crash can only kill the worker:

| File | Change |
|---|---|
| `backend/app/ocr/ocr_worker.py` | NEW. Single-threaded Paddle (`set_num_threads(1)`, with paddle ≥3.0 fallback to `paddle.base.core.set_num_threads`), lazy `PaddleOCR(lang="en")`, length-prefixed (8-byte BE) PNG frames on stdin, JSON reply on fd from `OCR_PROTO_FD` (default 3), per-frame try/except. |
| `backend/app/ocr/reader.py` | Rewritten as subprocess client: `Popen([sys.executable, "-m", app.ocr.ocr_worker], stdin=PIPE, stdout/stderr=DEVNULL, pass_fds=(write_fd,), env=OCR_PROTO_FD)`, respawn+retry once on worker death. Response pipe opened **unbuffered** (`os.fdopen(read_fd, "rb", buffering=0)`) — a buffered reader over-read the pipe so `select` saw an empty fd and `_read_exact` hung. |
| `backend/tests/stub_ocr_worker.py`, `backend/tests/test_reader.py` | NEW. Paddle-free echo worker + 3 tests (roundtrip, respawn-after-crash, unavailable-raises). |

Verified live with the real Paddle worker: "stiebel Eltron WPL 18" @ 97.9% in ~3.3s; after
`SIGKILL` the parent survives and a fresh worker is respawned and OCR still works.
Full suite **97 passed** (84 + 10 kW tests + 3 reader tests).
