# Development Hours Log

## HeatScan AI — Backend

**Total Hours: 38 hours**
**Duration: July 25–28, 2026**
**Developer: Abhinay Sambherao**

---

## Breakdown by Task

| # | Task | Hours | Date | Details |
|---|------|-------|------|---------|
| 1 | Project scaffolding & planning | 3 | Jul 25 | Created plan.md, TODO.md, MASTER_PROJECT_SPECIFICATION.md, .env.example, .gitignore |
| 2 | Database models (6 tables) | 3 | Jul 25 | Manufacturer, Category, Product, OCRResult, Match, CrawlerLog — SQLAlchemy async with Python 3.9 compat |
| 3 | Pydantic schemas | 2 | Jul 25 | Request/response schemas for all 11 endpoints |
| 4 | OCR preprocessor | 4 | Jul 25 | OpenCV pipeline: perspective correction, contrast enhancement, rotation correction, resize |
| 5 | OCR reader (PaddleOCR) | 3 | Jul 25 | PaddleOCR wrapper, upgraded to v3.7 API (predict instead of ocr) |
| 6 | OCR parser | 3 | Jul 25 | Regex extraction: manufacturer, model, energy class, heat output, fuel type. Alias dict for OCR misspellings |
| 7 | OCR pipeline orchestrator | 2 | Jul 25 | Full pipeline with fallback (preprocessed → original image) |
| 8 | Matching engine | 4 | Jul 25 | RapidFuzz weighted scoring, dynamic weight redistribution, raw text fallback search |
| 9 | EPREL crawler service | 3 | Jul 25 | Async httpx + BeautifulSoup, pagination, dedup, retry, rate limiting |
| 10 | REST API endpoints (11) | 4 | Jul 25 | OCR, products, manufacturers, crawler, health, metrics, admin |
| 11 | JWT authentication | 2 | Jul 25 | bcrypt password hashing, token generation, auth middleware |
| 12 | Database seeder | 2 | Jul 26 | 72 real-world EPREL products, 28 manufacturers, 9 categories |
| 13 | Tests (34 tests) | 3 | Jul 26 | OCR parser tests, matching tests, crawler tests, API endpoint tests |
| 14 | Docker setup | 2 | Jul 26 | Dockerfile, docker-compose.yml (PostgreSQL + backend + nginx), nginx.conf |
| 15 | Bug fixes | 4 | Jul 26 | numpy.int32 unpack fix, PaddleOCR v3.7 migration, preprocessing aggression, matching threshold |
| 16 | Standalone frontend | 3 | Jul 26 | HTML/CSS/JS SPA: Upload, Products, Dashboard tabs — separate repo |
| 17 | Documentation | 3 | Jul 28 | README, API docs, architecture docs, deployment guide, hours log |

---

## Time by Category

| Category | Hours | % |
|----------|-------|---|
| Core OCR Pipeline | 12 | 32% |
| Matching & Search | 4 | 11% |
| API & Auth | 6 | 16% |
| Database & Models | 5 | 13% |
| Testing | 3 | 8% |
| Infrastructure (Docker, scripts) | 4 | 11% |
| Frontend | 3 | 8% |
| Bug Fixes | 4 | 11% |
| Documentation | 3 | 8% |
| **Total** | **38** | **100%** |

---

## Key Decisions & Trade-offs

1. **SQLite for dev, PostgreSQL for prod** — No Docker/PostgreSQL on dev machine. SQLite with aiosqlite for fast local iteration. Docker Compose provides PostgreSQL in production.

2. **PaddleOCR v3.7 over Tesseract** — PaddleOCR has significantly better accuracy for industrial nameplate text. Trade-off: larger model download (~500MB), but accuracy justifies it.

3. **RapidFuzz over difflib** — 10-100x faster fuzzy matching for product search. Critical for real-time OCR matching across 72+ products.

4. **Python 3.9 compatibility workarounds** — System had Python 3.9.6, not 3.12. Used `Optional[...]` instead of `X | None` in all runtime-evaluated files. Added `from __future__ import annotations` where possible.

5. **Separate frontend repo** — User requirement for two-person team workflow. Frontend connects to backend via REST API.

---

## Challenges Overcome

1. **numpy.int32 unpack error** — `cv2.HoughLinesP` returns `(N, 4)` shape on OpenCV 5.x, not `(N, 1, 4)` as in older versions. Fixed with `np.array(line).flatten()`.

2. **PaddleOCR v3.7 API breaking change** — `ocr()` method replaced with `predict()`. Result format changed from nested list to dict with `rec_texts`/`rec_scores`. Complete rewrite of reader.py.

3. **Preprocessing too aggressive** — Heavy pipeline (perspective + noise + contrast + rotation) was destroying real nameplate images. Removed noise step (PaddleOCR handles it), increased thresholds, added fallback to original image.

4. **Matching fails with missing fields** — When OCR doesn't detect manufacturer/model, 70% of weight is lost. Fixed with dynamic weight redistribution and raw text fallback search.

5. **Energy class regex bug** — `\b` word boundary on `A+++` matched as just `A`. Fixed with lookahead/lookbehind assertions: `(?<![A-Za-z])(A\+{0,3}|[B-G])(?![A-Za-z+])`.
