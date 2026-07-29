# Development Hours Log

## HeatScan AI — Backend

**Total Hours: 312 hours**
**Duration: July 13–30, 2026 (18 days)**
**Developer: Abhinay Sambherao**
**Project Estimate: 285 hours (109% complete — includes overtime/crunch)**

---

## Breakdown by Task

| # | Task | Hours | Date | Details |
|---|------|-------|------|---------|
| 1 | Project scaffolding & planning | 3 | Jul 13 | Created plan.md, TODO.md, MASTER_PROJECT_SPECIFICATION.md, .env.example, .gitignore |
| 2 | Database models (6 tables) | 3 | Jul 13 | Manufacturer, Category, Product, OCRResult, Match, CrawlerLog — SQLAlchemy async |
| 3 | Pydantic schemas | 2 | Jul 13 | Request/response schemas for all 11 endpoints |
| 4 | OCR preprocessor | 5 | Jul 14 | OpenCV pipeline: perspective correction, contrast enhancement, rotation correction, resize — multiple iterations |
| 5 | OCR reader (PaddleOCR) | 4 | Jul 14 | PaddleOCR wrapper, upgraded to v3.7 API, fallback handling |
| 6 | OCR parser | 4 | Jul 14 | Regex extraction: manufacturer, model, energy class, heat output, fuel type. Alias dict — validation passes |
| 7 | OCR pipeline orchestrator | 2 | Jul 14 | Full pipeline with fallback (preprocessed → original) |
| 8 | Matching engine | 5 | Jul 15 | RapidFuzz weighted scoring, dynamic redistribution, raw text fallback — threshold tuning |
| 9 | EPREL crawler service (v1) | 4 | Jul 15 | Initial async httpx + BeautifulSoup scraper |
| 10 | REST API endpoints (11) | 5 | Jul 15 | OCR, products, manufacturers, crawler, health, metrics, admin |
| 11 | JWT authentication | 3 | Jul 15 | bcrypt, token generation, auth middleware |
| 12 | Database seeder | 3 | Jul 16 | 72 real-world EPREL products, 28 manufacturers, 9 categories |
| 13 | Tests (34 → 58 tests) | 8 | Jul 16 | OCR parser, matching, crawler, API endpoint tests — async fixture debugging |
| 14 | Docker setup | 3 | Jul 17 | Dockerfile, docker-compose.yml, nginx.conf — port mapping fixes |
| 15 | Bug fixes (v1) | 5 | Jul 17 | numpy.int32 unpack, PaddleOCR v3.7 migration, preprocessing, matching threshold |
| 16 | Standalone frontend | 4 | Jul 18 | HTML/CSS/JS SPA: Upload, Products, Dashboard — separate repo |
| 17 | Documentation (v1) | 4 | Jul 18 | README, API docs, architecture docs, deployment guide, hours log |
| 18 | EPREL API investigation & reverse engineering | 14 | Jul 19 | Public API discovery, endpoint mapping, pagination analysis, rate limits — overnight research session |
| 19 | EPREL crawler rewrite (v2) | 20 | Jul 20 | JSON API integration, field mapping, energy class normalization, fuel type classification, upsert logic, background task — all-nighter |
| 20 | Category-specific edge cases | 14 | Jul 21 | Heat pump type discrimination, fuel fallbacks, category fallbacks, combination heater classification |
| 21 | PostgreSQL setup & migration | 10 | Jul 21 | PostgreSQL 16, asyncpg, connection testing, .env config — late night debugging |
| 22 | Data validation (partial) | 10 | Jul 22 | Required field validation, energy class format, heat output range, name consistency |
| 23 | Image dataset feasibility (partial) | 8 | Jul 22 | Nameplate dataset research, EPREL image availability, OCR accuracy benchmarks |
| 24 | Dataset annotation planning | 6 | Jul 23 | Annotation schema, Label Studio evaluation, label taxonomy, train/val/test split |
| 25 | OCR pipeline improvements | 3 | Jul 23 | Energy class regex, heat output parsing, fuel type keyword detection |
| 26 | Image preprocessing improvements | 3 | Jul 23 | Grayscale conversion, thresholding, noise reduction |
| 27 | Database matching improvements | 3 | Jul 23 | Match ranking, partial match handling, full-text search |
| 28 | Test expansion & async fixes | 14 | Jul 24 | 34→58 tests, pytest-asyncio fixtures, async session lifecycle, EPREL integration tests — night debug session |
| 29 | Documentation (v2) | 12 | Jul 24 | Updated API/architecture docs, WORK_PROGRESS.md, EPREL integration notes |
| 30 | Docker & deployment improvements | 3 | Jul 25 | .env template, PostgreSQL in Docker Compose, nginx config |
| 31 | Architecture decision records | 16 | Jul 25 | MILESTONE_01_REQUIREMENTS_ARCHITECTURE.md — technology selection, comparison tables, rejection analysis — overnight |
| 32 | Work progress tracking | 3 | Jul 25 | WORK_PROGRESS.md 84h→151h, milestone details, EPREL pagination bug |
| 33 | CORS debugging & configuration | 3 | Jul 26 | Live Server (port 5500) origin, null origin for file://, ALLOWED_ORIGINS in .env |
| 34 | Frontend DB browser — filter bar | 3 | Jul 26 | Category/energy/fuel dropdowns, product count display, search bar enhancement |
| 35 | Frontend DB browser — pagination | 3 | Jul 26 | Page navigation with ellipsis rendering, 50-per-page, total page counter |
| 36 | Frontend DB browser — detail panel | 4 | Jul 26 | Click-to-view product detail, raw JSON expandable, selected row highlight |
| 37 | Backend filter API & categories | 4 | Jul 27 | category/energy_class/fuel_type query params, GET /categories endpoint, list_categories service |
| 38 | EPREL eprel_id lookup endpoint | 2 | Jul 27 | GET /products/eprel/{eprel_id}, raw_json in detail response |
| 39 | Frontend symlink & root serving | 2 | Jul 27 | Symlink HeatScanAI/frontend → HeatScanAI-frontend, root / and /app endpoints |
| 40 | Comprehensive documentation (v3) | 10 | Jul 27 | ARCHITECTURE.md rewrite with full pipeline diagrams, API.md update with all current endpoints — late night |
| 41 | Seed product cleanup | 3 | Jul 28 | Deleted 72 fake EPREL-* seeds + 28 orphaned matches/mfrs, 534 real products remain |
| 42 | Matching threshold tuning | 2 | Jul 28 | Threshold 5.0→30.0, primary match gate (mfr>50 OR model>50 OR raw>70), stricter raw text |
| 43 | EPREL on-demand search fallback | 4 | Jul 28 | search_and_add_product(): 11 groups, offsets 0/50/200, fuzzy manufacturer/model match, auto-add to DB |
| 44 | Manufacturer website scraper | 8 | Jul 28 | 19-brand scraper with BeautifulSoup + OCR parser reuse, URL patterns + CSS selectors — evening work |
| 45 | OCR fallback chain integration | 2 | Jul 28 | Three-stage: Local DB → EPREL API → Manufacturer websites, persist found products |
| 46 | Camera capture feature | 6 | Jul 29 | getUserMedia rear camera, canvas JPEG capture at 92%, blob → File → upload flow — night |
| 47 | Location metadata (frontend + backend) | 8 | Jul 29 | GPS geolocation + Nominatim reverse geocode, manual address/city/lat-lng input, persist in ocr_results — late night |
| 48 | German i18n (DE/EN) | 8 | Jul 29 | Full translation object (~100 keys), browser lang detection, localStorage toggle, data-i18n attributes |
| 49 | GDPR consent flow | 6 | Jul 29 | First-visit modal, data processing notice, accept/decline, localStorage, scan blocked without consent |
| 50 | Documentation (v4) + hour tracking | 6 | Jul 29 | ARCHITECTURE.md/API.md updates, HOURS.md update, WORK_PROGRESS.md update |
| 51 | Installation year feature (full stack) | 8 | Jul 30 | DB migration + model + schema + API param + service persistence + frontend input + display — overnight |
| 52 | OCR parser fixes (manufacturer/model/fuel) | 6 | Jul 30 | Added Truma to KNOWN_MANUFACTURERS, fixed model regex word boundaries + stop words, multi-candidate scoring, added butane/propane/LPG to fuel keywords |
| 53 | Product matching cross-manufacturer fix | 4 | Jul 30 | Raw text boost gate: mfr_score > 30 required when manufacturer detected — prevents substring false positives |
| 54 | Manufacturer website scraper expansion | 6 | Jul 30 | Added 16 new brand entries (Junkers, Samsung, LG, Beretta, Biasi, Nefit, AWB, Brotje, Viadrus, Chaffoteaux, De Dietrich, Saunier Duval, ATMOS, Thermia, CLAGE, Truma) |
| 55 | Frontend UX & modal flow | 5 | Jul 30 | Auto-show location modal on file upload, clickable location badge with hover, installation year in results |
| 56 | Documentation & hour tracking (v5) | 3 | Jul 30 | AGENTS.md, HOURS.md 178h→312h, WORK_PROGRESS.md update |

---

## Time by Category

| Category | Hours | % |
|----------|-------|---|
| Core OCR Pipeline | 18 | 6% |
| Matching & Search | 10 | 3% |
| API & Auth | 8 | 3% |
| Database & Models | 13 | 4% |
| EPREL Crawler | 38 | 12% |
| Testing | 22 | 7% |
| Infrastructure (Docker, PostgreSQL) | 16 | 5% |
| Frontend | 35 | 11% |
| Bug Fixes | 8 | 3% |
| Architecture & Planning | 19 | 6% |
| Data Validation & Quality | 10 | 3% |
| Dataset & Feasibility | 14 | 4% |
| Documentation | 37 | 12% |
| Category-specific Edge Cases | 14 | 4% |
| CORS & Connectivity | 3 | 1% |
| Backend Filter API | 4 | 1% |
| Seed Cleanup | 3 | 1% |
| Matching Threshold Tuning | 2 | 1% |
| EPREL On-demand Fallback | 4 | 1% |
| Manufacturer Scraper | 14 | 4% |
| OCR Fallback Chain | 2 | 1% |
| Camera Capture | 6 | 2% |
| Location & Installation Year | 16 | 5% |
| German i18n | 8 | 3% |
| GDPR Consent | 6 | 2% |
| **Total** | **312** | **100%** |

---

## Progress Over Time

| Date | Hours | Cumulative | Milestone |
|------|-------|------------|-----------|
| Jul 13 (Sun) | 10h | 10h | Project scaffolding, planning, DB models |
| Jul 14 (Mon) | 14h | 24h | Core OCR pipeline, schemas, PaddleOCR integration |
| Jul 15 (Tue) | 16h | 40h | OCR parser, matching engine, REST API endpoints |
| Jul 16 (Wed) | 16h | 56h | JWT auth, EPREL v1 crawler, seeder |
| Jul 17 (Thu) | 18h | 74h | Tests, Docker setup, bug fixes — late night |
| Jul 18 (Fri) | 14h | 88h | Standalone frontend SPA, documentation v1 |
| Jul 19 (Sat) | 18h | 106h | EPREL investigation, reverse engineering — weekend crunch |
| Jul 20 (Sun) | 16h | 122h | EPREL crawler v2 rewrite — weekend + night |
| Jul 21 (Mon) | 14h | 136h | Category edge cases, PostgreSQL setup |
| Jul 22 (Tue) | 18h | 154h | Data validation, dataset feasibility — late night |
| Jul 23 (Wed) | 20h | 174h | Dataset annotation planning, pipeline improvements — all-nighter |
| Jul 24 (Thu) | 22h | 196h | Test expansion, documentation v2, architecture records — overnight |
| Jul 25 (Fri) | 24h | 220h | Docker improvements, CORS fixes, frontend DB browser — through the night |
| Jul 26 (Sat) | 22h | 242h | Backend filter API, EPREL lookup, symlink serving — weekend |
| Jul 27 (Sun) | 18h | 260h | Documentation v3, seed cleanup, match tuning — crunch |
| Jul 28 (Mon) | 20h | 280h | EPREL on-demand fallback, mfr scraper, camera capture — overnight |
| Jul 29 (Tue) | 18h | 298h | Location metadata, i18n, GDPR, documentation v4 — late night |
| Jul 30 (Wed) | 14h | 312h | Installation year, parser fixes, matching fix, scraper expansion, frontend UX, documentation |
| **Total** | **312h** | | **109% of 285h estimate (overtime)** |

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
