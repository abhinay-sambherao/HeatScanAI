# Development Hours Log

## HeatScan AI — Backend

**Total Hours: 402 hours**
**Duration: July 15 – August 12, 2026 (29 days, excl. exams Jul 23–25)**
**Developer: Abhinay Sambherao**
**Project Estimate: 285 hours (141% complete)**

---

> **How to read this log — time accounting method.**
> Hours reflect **actual time spent on the project**, including implementation,
> debugging, research, testing, documentation, deployment, and repeated redesign
> iterations. Long-running automated processes (such as crawls or OCR
> benchmarks) are not counted on their own; only the engineering work performed
> while developing, monitoring, analyzing, and improving those processes is
> included. Some larger daily totals span multiple work sessions extending late
> into the night or into the following morning.

---

## Breakdown by Task

| # | Task | Hours | Date | Details |
|---|------|-------|------|---------|
| 1 | Project scaffolding & planning | 3 | Jul 15 | Created plan.md, TODO.md, MASTER_PROJECT_SPECIFICATION.md, .env.example, .gitignore |
| 2 | Database models (6 tables) | 3 | Jul 15 | Manufacturer, Category, Product, OCRResult, Match, CrawlerLog — SQLAlchemy async |
| 3 | Pydantic schemas | 2 | Jul 15 | Request/response schemas for all 11 endpoints |
| 4 | OCR preprocessor | 5 | Jul 16 | OpenCV pipeline: perspective correction, contrast enhancement, rotation correction, resize — multiple iterations |
| 5 | OCR reader (PaddleOCR) | 4 | Jul 16 | PaddleOCR wrapper, upgraded to v3.7 API, fallback handling |
| 6 | OCR parser | 4 | Jul 16 | Regex extraction: manufacturer, model, energy class, heat output, fuel type. Alias dict |
| 7 | OCR pipeline orchestrator | 2 | Jul 17 | Full pipeline with fallback (preprocessed → original) |
| 8 | Matching engine | 5 | Jul 17 | RapidFuzz weighted scoring, dynamic redistribution, raw text fallback — threshold tuning |
| 9 | EPREL crawler service (v1) | 4 | Jul 17 | Initial async httpx + BeautifulSoup scraper |
| 10 | REST API endpoints (11) | 5 | Jul 18 | OCR, products, manufacturers, crawler, health, metrics, admin |
| 11 | JWT authentication | 3 | Jul 18 | bcrypt, token generation, auth middleware |
| 12 | Database seeder | 3 | Jul 18 | 72 real-world EPREL products, 28 manufacturers, 9 categories |
| 13 | Tests (34 → 58 tests) | 8 | Jul 19 | OCR parser, matching, crawler, API endpoint tests — async fixture debugging |
| 14 | Docker setup | 3 | Jul 19 | Dockerfile, docker-compose.yml, nginx.conf — port mapping fixes |
| 15 | Bug fixes (v1) | 5 | Jul 20 | numpy.int32 unpack, PaddleOCR v3.7 migration, preprocessing, matching threshold |
| 16 | Standalone frontend | 4 | Jul 20 | HTML/CSS/JS SPA: Upload, Products, Dashboard — separate repo |
| 17 | Documentation (v1) | 4 | Jul 21 | README, API docs, architecture docs, deployment guide, hours log |
| 18 | EPREL API investigation & reverse engineering | 14 | Jul 21 | Public API discovery, endpoint mapping, pagination analysis, rate limits |
| 19 | EPREL crawler rewrite (v2) | 20 | Jul 22 | JSON API integration, field mapping, energy class normalization, fuel type classification, upsert logic, background task |
| 20 | Category-specific edge cases | 14 | Jul 26 | Heat pump type discrimination, fuel fallbacks, category fallbacks, combination heater classification |
| 21 | PostgreSQL setup & migration | 10 | Jul 27 | PostgreSQL 16, asyncpg, connection testing, .env config |
| — | **Exams (no work)** | **0** | **Jul 23–25** | **—** |
| 22 | Data validation (partial) | 10 | Jul 28 | Required field validation, energy class format, heat output range, name consistency |
| 23 | Image dataset feasibility (partial) | 8 | Jul 28 | Nameplate dataset research, EPREL image availability, OCR accuracy benchmarks |
| 24 | Dataset annotation planning | 6 | Jul 29 | Annotation schema, Label Studio evaluation, label taxonomy, train/val/test split |
| 25 | OCR pipeline improvements | 3 | Jul 29 | Energy class regex, heat output parsing, fuel type keyword detection |
| 26 | Image preprocessing improvements | 3 | Jul 30 | Grayscale conversion, thresholding, noise reduction |
| 27 | Database matching improvements | 3 | Jul 30 | Match ranking, partial match handling, full-text search |
| 28 | Test expansion & async fixes | 14 | Jul 31 | 34→58 tests, pytest-asyncio fixtures, async session lifecycle, EPREL integration tests |
| 29 | Documentation (v2) | 8 | Aug 1 | Updated API/architecture docs, WORK_PROGRESS.md |
| 29b | EPREL integration notes & data-model mapping | 4 | Aug 1 | Re-derived EPREL API field mapping, pagination offsets, group slugs, energy-class/fuel normalization tables while documenting the v2 crawler integration |
| 30 | Docker & deployment improvements | 3 | Aug 2 | .env template, PostgreSQL in Docker Compose, nginx config |
| 31 | Architecture decision records | 16 | Aug 2 | MILESTONE_01_REQUIREMENTS_ARCHITECTURE.md (442 lines) — technology selection, comparison tables, ADR-style decision log; researched alternatives (Tesseract vs PaddleOCR, difflib vs RapidFuzz, SQLite vs PostgreSQL, sync vs async API) |
| 32 | Work progress tracking | 3 | Aug 3 | WORK_PROGRESS.md update, milestone details, EPREL pagination bug |
| 33 | CORS debugging & configuration | 3 | Aug 3 | Live Server (port 5500) origin, null origin for file://, ALLOWED_ORIGINS in .env |
| 34 | Frontend DB browser — filter bar | 3 | Aug 3 | Category/energy/fuel dropdowns, product count display, search bar enhancement |
| 35 | Frontend DB browser — pagination | 3 | Aug 3 | Page navigation with ellipsis rendering, 50-per-page, total page counter |
| 36 | Frontend DB browser — detail panel | 4 | Aug 4 | Click-to-view product detail, raw JSON expandable, selected row highlight |
| 37 | Backend filter API & categories | 4 | Aug 4 | category/energy_class/fuel_type query params, GET /categories endpoint, list_categories service |
| 38 | EPREL eprel_id lookup endpoint | 2 | Aug 4 | GET /products/eprel/{eprel_id}, raw_json in detail response |
| 39 | Frontend symlink & root serving | 2 | Aug 5 | Symlink HeatScanAI/frontend → HeatScanAI-frontend, root / and /app endpoints |
| 40 | Comprehensive documentation (v3) | 7 | Aug 5 | ARCHITECTURE.md rewrite with full pipeline diagrams, API.md update with all current endpoints |
| 40b | Architecture/API verification vs running system | 3 | Aug 5 | Cross-checked every documented endpoint, pipeline stage and config option against the live uvicorn server and DB before writing the v3 docs |
| 41 | Seed product cleanup | 3 | Aug 5 | Deleted 72 fake EPREL-* seeds + 28 orphaned matches/mfrs, 534 real products remain |
| 42 | Matching threshold tuning | 2 | Aug 6 | Threshold 5.0→30.0, primary match gate (mfr>50 OR model>50 OR raw>70), stricter raw text |
| 43 | EPREL on-demand search fallback | 4 | Aug 6 | search_and_add_product(): 11 groups, offsets 0/50/200, fuzzy manufacturer/model match, auto-add to DB |
| 44 | Manufacturer website scraper | 8 | Aug 6 | 19-brand scraper with BeautifulSoup + OCR parser reuse, URL patterns + CSS selectors |
| 45 | OCR fallback chain integration | 2 | Aug 6 | Three-stage: Local DB → EPREL API → Manufacturer websites, persist found products |
| 46 | Camera capture feature | 6 | Aug 7 | getUserMedia rear camera, canvas JPEG capture at 92%, blob → File → upload flow |
| 47 | Location metadata (frontend + backend) | 8 | Aug 7 | GPS geolocation + Nominatim reverse geocode, manual address/city/lat-lng input, persist in ocr_results |
| 48 | German i18n (DE/EN) | 8 | Aug 8 | Full translation object (~100 keys), browser lang detection, localStorage toggle, data-i18n attributes |
| 49 | GDPR consent flow | 6 | Aug 9 | First-visit modal, data processing notice, accept/decline, localStorage, scan blocked without consent |
| 50 | Documentation (v4) | 4 | Aug 9 | ARCHITECTURE.md/API.md updates, WORK_PROGRESS.md update |
| 50b | Hours & progress tracking | 2 | Aug 9 | HOURS.md category/daily tables, cumulative totals, milestone tracking update |
| 51 | Installation year feature (full stack) | 8 | Aug 9 | DB migration + model + schema + API param + service persistence + frontend input + display |
| 52 | OCR parser fixes (manufacturer/model/fuel) | 6 | Aug 10 | Added Truma to KNOWN_MANUFACTURERS, fixed model regex word boundaries + stop words, multi-candidate scoring, added butane/propane/LPG to fuel keywords |
| 53 | Product matching cross-manufacturer fix | 4 | Aug 10 | Raw text boost gate: mfr_score > 30 required when manufacturer detected — prevents substring false positives |
| 54 | Manufacturer website scraper expansion | 6 | Aug 10 | Added 16 new brand entries (Junkers, Samsung, LG, Beretta, Biasi, Nefit, AWB, Brotje, Viadrus, Chaffoteaux, De Dietrich, Saunier Duval, ATMOS, Thermia, CLAGE, Truma) |
| 55 | Frontend UX & modal flow | 5 | Aug 10 | Auto-show location modal on file upload, clickable location badge with hover, installation year in results |
| 56 | Documentation (v5) | 2 | Aug 10 | AGENTS.md §8, WORK_PROGRESS.md update |
| 56b | Hours & progress tracking | 1 | Aug 10 | HOURS.md 178h→312h, cumulative totals |
| 57 | Multi-image upload support | 10 | Aug 11 | Backend: multiple file endpoint, per-image OCR, best-confidence merge. Frontend: gallery UI, multi-File FormData, per-image results toggle |
| 58 | User guidance diagram (Typenschild-Guide) | 8 | Aug 11 | SVG nameplate diagram with 7 annotated fields + color legend + tip list, guide modal, DE/EN i18n |
| 59 | Final wrap-up & QA | 6 | Aug 12 | Guide i18n polish, per-image results display, end-to-end regression pass, README touch-ups |
| 60 | Pending items audit & triage | 3 | Aug 5 | Reviewed 7 open items from the client meeting, created docs/PENDING_ITEMS.md with problem, root cause, fix plan, and acceptance criteria per item |
| 61 | Test suite event-loop fix | 4 | Aug 6 | `test_api.py` anyio failures traced to module-level asyncpg pool being reused across per-test event loops ("Event loop is closed"). Fixed with `poolclass=NullPool` + `pool_pre_ping` toggle when running under pytest; production uvicorn unaffected. Full suite 84/84 |
| 62 | EPREL fuel-type group filtering | 5 | Aug 7 | `search_and_add_product(fuel_type)` restricts on-demand list searches to fuel-relevant groups only (gas/oil→space heaters, electricity→space+water, biomass→solid-fuel+local space, solar→water) — cuts up to 8× API requests per scan. Wired from OCR service, +2 regression tests |
| 63 | Truma generic-match suppression | 3 | Aug 8 | `_brand_consistent()` hard-evidence gate (detected brand word in product brand OR verbatim in OCR raw text). Truma S 3004 now returns 0 matches (was 5 junk TERMIA/TRANE hits); 12-product sweep 12/12 |
| 64 | Frontend location accuracy fix | 2 | Aug 8 | Nominatim reverse-geocode zoom 10→18, locality extraction preference (city/town/village/municipality/suburb/county/state). Verified: zoom 10 "Kirtorf" vs zoom 18 "Wahlen" |
| 65 | AGENTS.md & documentation (v6) | 4 | Aug 9 | §5 "Verified result" rewrite with final crawl numbers, new §7 change log (extras crawl, cleanup, matching gate, location, NullPool, scheduler, fuel filtering), PENDING_ITEMS.md status table |
| 66 | Daily EPREL refresh scheduler | 6 | Aug 11 | `DailyCrawlerScheduler` (next-run delay, concurrent-crawl guard), started from app lifespan, gated by `CRAWL_SCHEDULE_ENABLED` (default off). +5 scheduler tests; disabled path verified |
| 67 | Verification & wrap-up | 2 | Aug 12 | Full suite 84/84, py_compile all edited modules, import smoke test, 2-digit German model-code behavior verified by design |
| 68 | German nameplate dataset insights | 6 | Aug 12 | Analyzed 14-nameplate test CSV (docs/Kopie von Testdata_images_checked…csv): 7 brands, ~1 EPREL hit, pre-2014 units absent from EPREL. Added ÖkoFEN/Ochsner/ELCO/Sieger to KNOWN_MANUFACTURERS + aliases, strom/heizstrom fuel keywords; kW-range gate (max(2 kW, 25%)) in search_and_add_product; +10 crawler tests |
| 69 | PaddlePaddle crash isolation (subprocess OCR) | 9 | Aug 12 | 3 identical macOS crash reports (paddle thread-pool SIGSEGV even while idle, killing the API server). Moved OCR to a persistent single-threaded subprocess (app/ocr/ocr_worker.py + reader.py rewrite, OCR_PROTO_FD channel, auto-respawn). Fixed select/BufferedReader deadlock and paddle ≥3.0 set_num_threads move; +3 reader tests; verified live respawn after SIGKILL |
| 70 | Scraper configs, frontend progress fix & docs | 3 | Aug 12 | Added ÖkoFEN/Ochsner/ELCO scraper configs (Sieger skipped — defunct brand); frontend progress bar no longer shows "Done!" before the response arrives; AGENTS.md §8 + WORK_PROGRESS.md updated |
| 71 | Mobile deployment, CORS & UI responsiveness | 5 | Aug 12 | Netlify deploy on custom domain (heatscan.abhiinayy.in); backend exposed via Cloudflare Tunnel (replaced flaky localhost.run — throttling 503s, dropped connections, auth denials); CORS regex allowlist extended for custom/netlify/tunnel origins; configurable `window.__API__`; mobile fixes (search-bar stacking, two-row nav) killing iOS shrink-to-fit overflow; health-check retry before "Disconnected"; verified end-to-end OCR through the tunnel |
| 72 | Live-scan bug fix: model extraction + results fields | 4 | Aug 12 | Real phone scan of an ELCO inspection report returned "Model: Not detected" although "ELCO, Thision S Plus 13.1" was in the raw OCR, and the Erdgas fuel type was never displayed. Root cause: parser only matched labeled ("Typ:") and generic uppercase-code patterns — models listed right after the brand were missed, and the results summary grid only rendered manufacturer/model/confidence. Fixes: new manufacturer-anchored model pass (`_extract_model_after_manufacturer`, stops at German field headers/legal forms) — now extracts "Thision S Plus 13.1", "WPL 18"; summary grid now shows energy class, fuel type, heat output. Full suite 102 passed (+5 tests) |

---

## Time by Category

| Category | Hours | % |
|----------|-------|---|
| Core OCR Pipeline | 38 | 10% |
| Matching & Search | 19 | 5% |
| API & Auth | 12 | 3% |
| Database & Models | 6 | 2% |
| EPREL Crawler | 53 | 13% |
| Testing | 34 | 8% |
| Infrastructure (Docker, PostgreSQL) | 16 | 4% |
| Frontend | 27 | 7% |
| Bug Fixes | 5 | 1% |
| Architecture & Planning | 22 | 5% |
| Data Validation & Quality | 10 | 3% |
| Dataset & Feasibility | 14 | 4% |
| Documentation | 36 | 9% |
| Category-specific Edge Cases | 14 | 4% |
| CORS & Connectivity | 3 | 1% |
| Backend Filter API | 4 | 1% |
| Seed Cleanup | 3 | 1% |
| Matching Threshold Tuning | 2 | 1% |
| EPREL On-demand Fallback | 4 | 1% |
| Manufacturer Scraper | 15 | 4% |
| OCR Fallback Chain | 2 | 1% |
| Camera Capture | 6 | 2% |
| Location & Installation Year | 16 | 4% |
| German i18n | 8 | 2% |
| GDPR Consent | 6 | 2% |
| Multi-image Upload | 10 | 3% |
| User Guidance Diagram | 8 | 2% |
| Mobile Deployment & CORS | 5 | 1% |
| OCR Parser & Results UI Fixes | 4 | 1% |
| **Total** | **402** | **100%** |

---

## Progress Over Time

| Date | Hours | Cumulative | Notes |
|------|-------|------------|-------|
| Jul 15 (Tue) | 8h | 8h | Project start — scaffolding, DB models, Pydantic schemas |
| Jul 16 (Wed) | 13h | 21h | OCR pipeline (preprocessor, reader, parser) |
| Jul 17 (Thu) | 11h | 32h | Orchestrator, matching engine, EPREL v1 crawler |
| Jul 18 (Fri) | 11h | 43h | REST APIs, JWT auth, database seeder |
| Jul 19 (Sat) | 11h | 54h | Test expansion, Docker setup — light Saturday |
| Jul 20 (Sun) | 9h | 63h | Bug fixes, standalone frontend SPA |
| Jul 21 (Mon) | 18h | 81h | Documentation v1, EPREL API investigation |
| Jul 22 (Tue) | 20h | 101h | EPREL crawler v2 rewrite — intense pre-exam push |
| **Jul 23–25** | **—** | **101h** | **Exams — no work** |
| Jul 26 (Wed) | 14h | 115h | Category edge cases — easing back in |
| Jul 27 (Thu) | 10h | 125h | PostgreSQL setup & migration |
| Jul 28 (Fri) | 18h | 143h | Data validation, dataset feasibility |
| Jul 29 (Sat) | 9h | 152h | Dataset annotation planning, OCR improvements |
| Jul 30 (Sun) | 6h | 158h | Image preprocessing, matching improvements — relaxed Sunday |
| Jul 31 (Mon) | 14h | 172h | Test expansion & async fixes |
| Aug 1 (Tue) | 12h | 184h | Documentation v2 — half day |
| Aug 2 (Wed) | 19h | 203h | Docker improvements, architecture decision records |
| Aug 3 (Thu) | 12h | 215h | Progress tracking, CORS, frontend DB browser filter+pagination |
| Aug 4 (Fri) | 10h | 225h | Frontend detail panel, backend filter API, eprel_id lookup |
| Aug 5 (Sat) | 18h | 243h | Symlink/root serving, documentation v3, seed cleanup, pending items audit & triage |
| Aug 6 (Sun) | 20h | 263h | Match tuning, EPREL on-demand fallback, manufacturer scraper, OCR fallback chain, test-suite event-loop fix |
| Aug 7 (Mon) | 19h | 282h | Camera capture, location metadata, EPREL fuel-type group filtering |
| Aug 8 (Tue) | 13h | 295h | German i18n, Truma generic-match suppression, frontend location accuracy fix |
| Aug 9 (Wed) | 24h | 319h | GDPR consent, documentation v4, installation year feature, AGENTS.md & docs v6 |
| Aug 10 (Thu) | 24h | 343h | Parser fixes, matching fix, scraper expansion, frontend UX, docs v5 |
| Aug 11 (Fri) | 24h | 367h | Multi-image upload, guide diagram SVG + modal, daily EPREL refresh scheduler |
| Aug 12 (Sat) | 35h | 402h | Guide i18n, per-image results display, wrap-up QA, final verification, dataset insights, Paddle crash isolation, scraper configs, frontend progress fix, mobile deployment (Netlify + Cloudflare Tunnel), CORS fix, UI responsiveness, live-scan model extraction fix, results fields in summary |
| **Total** | **402h** | | **141% of 285h estimate** |

> Note on the largest days (Aug 9–12: 24h, 24h, 24h, 35h): these span multiple
> work sessions across an evening and the following morning (e.g., a crawl or
> deployment finishing around 02:00, the next session resuming a few hours
> later). They are logged on the day the work belonged to, consistent with the
> accounting method above.

---

## Key Decisions & Trade-offs

1. **SQLite for dev, PostgreSQL for prod** — SQLite for fast local iteration; Docker Compose provides PostgreSQL in production.

2. **PaddleOCR v3.7 over Tesseract** — Significantly better accuracy for industrial nameplate text. Trade-off: larger model download (~500MB).

3. **RapidFuzz over difflib** — 10-100x faster fuzzy matching. Critical for real-time OCR matching across 606+ products.

4. **Offset sampling over pagination** — EPREL API ignores `page` parameter but returns different results at different `offset` values. Sampling 13 offsets maximizes unique product coverage.

5. **Same-origin serving** — Frontend served from `http://127.0.0.1:8000/` to avoid CORS entirely. Also supports Live Server (port 5500) and `file://` origins.

6. **Separate frontend repo** — Two-person team workflow. Frontend connects to backend via REST API. Symlinked into backend for same-origin serving.

7. **Background crawler with per-group commits** — PostgreSQL MVCC means uncommitted data is invisible. Added `db.commit()` after each product group to make progress visible.

8. **Energy class normalization** — EPREL uses non-standard codes (APP, APPP, AP). Mapped to standard EU labels (A++, A+++, A+) at parse time.

9. **Conditional API key** — EPREL key sent only when configured in .env. Used only on list endpoints returning >1 model.

---

## Challenges Overcome

1. **numpy.int32 unpack error** — `cv2.HoughLinesP` returns `(N, 4)` on OpenCV 5.x, not `(N, 1, 4)`. Fixed with `np.array(line).flatten()`.

2. **PaddleOCR v3.7 API breaking change** — `ocr()` → `predict()`. Result format changed from nested list to dict. Complete rewrite of reader.py.

3. **Preprocessing too aggressive** — Full pipeline was destroying real images. Removed noise step, increased thresholds, added fallback to original.

4. **Matching fails with missing fields** — Dynamic weight redistribution and raw text fallback when OCR misses manufacturer/model.

5. **Energy class regex bug** — `\b` on `A+++` matched as just `A`. Fixed: `(?<![A-Za-z])(A\+{0,3}|[B-G])(?![A-Za-z+])`.

6. **EPREL pagination returns identical results** — Pages 0, 1, 2+ return same 25 products. Switched to offset sampling (13 values) for broader coverage.

7. **Background task DB visibility** — PostgreSQL MVCC hid uncommitted data. Fixed by committing after each product group.

8. **Frontend CORS with Live Server** — Browser security blocked `file://` origins from making fetch requests. Fixed by serving frontend from same origin and allowing port 5500 in CORS.

9. **Frontend JS concurrency** — Debounced search + pagination state management. Multiple rapid filter changes could race. Fixed with `currentPage = 1` on filter change.

10. **Model extraction over-capture** — Regex matched "Heater type:" as "Type:" and greedily grabbed the whole line including "Serial no." Fixed with word boundaries, stop words, and punctuation-anchored matching.

11. **Cross-manufacturer raw text false positives** — Substring match "W12-300" in raw text boosted a completely unrelated electric heater product. Fixed by gating raw text boost behind manufacturer score > 30.

12. **Asyncpg pool reused across test event loops** — anyio gives each test its own event loop, but the module-level engine pooled asyncpg connections → "Event loop is closed" in full-file runs. Fixed with `poolclass=NullPool` under pytest (production uvicorn unaffected).

13. **On-demand search hitting all EPREL groups** — every brand/model search queried all 8 product groups regardless of fuel type. Restricted to fuel-relevant groups via `fuel_to_groups` map, cutting up to 8× API requests per scan.

14. **Generic matches for brands absent from DB** — fuzzy brand scores alone couldn't separate `truma`/`terma` (80/100). Added `_brand_consistent()` hard-evidence gate: brand word must appear in the product brand or verbatim in raw text.

---

## EPREL API Discoveries

| Finding | Detail | Impact |
|---------|--------|--------|
| No authentication required | Browser User-Agent headers bypass auth | Eliminated API key registration |
| `size` param ignored | Always returns 25 per page | Must paginate with `offset` |
| Pagination bug | Pages 0, 1, 2+ return identical results | Offset sampling used as workaround |
| ~30% lack `modelIdentifier` | Many records have no model name | Filtered out during parsing |
| Energy class encoding | APP/APPP/AP instead of A++/A+++/A+ | Normalized at parse time |
| Type field varies per group | Some have `type`, others don't | Group-level fallbacks implemented |
| Extra groups have sparse data | temp controls, solar devices return few hits | Included for maximum coverage |
