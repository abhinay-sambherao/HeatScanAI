# Detailed Task Breakdown — Billable Hours

**Project:** HeatScan AI — OCR-Powered Heating System Identification
**Client:** EVH GmbH
**Developer:** Abhinay Sambherao
**Period:** July 25–28, 2026
**Total Hours:** 151 hours
**Hourly Rate:** 16.67 EUR (4,275 EUR / 285 hours)

---

## 1. Environment Setup & Project Scaffolding (8h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 1.1 | Python environment setup | 0.5h | Jul 25 | Installed Python 3.9.6, created virtual environment, configured PATH |
| 1.2 | pip dependency installation | 0.5h | Jul 25 | Installed 21 packages, resolved version conflicts (numpy, opencv, paddleocr) |
| 1.3 | Git repository creation | 0.25h | Jul 25 | Created GitHub repo `abhinay-sambherao/HeatScanAI`, configured .gitignore, initial commit |
| 1.4 | Frontend repo creation | 0.25h | Jul 26 | Created separate repo `abhinay-sambherao/HeatScanAI-frontend`, configured .gitignore |
| 1.5 | Project directory structure | 0.5h | Jul 25 | Created 15 directories (app/, app/api/, app/models/, app/services/, app/ocr/, app/core/, scripts/, tests/, docs/, alembic/) |
| 1.6 | plan.md creation | 1h | Jul 25 | Wrote project plan with milestones, timeline, deliverables |
| 1.7 | TODO.md creation | 0.5h | Jul 25 | Created task checklist with 50+ items across 14 milestones |
| 1.8 | MASTER_PROJECT_SPECIFICATION.md | 2h | Jul 25 | 487-line specification: requirements, tech stack, schema, API, coding standards |
| 1.9 | .env.example creation | 0.25h | Jul 25 | 10 environment variables with documentation |
| 1.10 | .gitignore creation | 0.15h | Jul 25 | Python, Node, Docker, IDE, OS files |
| 1.11 | requirements.txt creation | 0.5h | Jul 25 | Pinned 21 dependencies with version numbers |
| 1.12 | Dockerfile creation | 0.5h | Jul 26 | Multi-stage build: python:3.12-slim, OpenCV system deps, PaddleOCR |
| 1.13 | docker-compose.yml creation | 0.75h | Jul 26 | 3 services (db, backend, nginx), health checks, volumes, profiles |
| 1.14 | nginx.conf creation | 0.5h | Jul 26 | Rate limiting, 20MB upload, 120s timeout, reverse proxy |
| 1.15 | GitHub README.md | 0.5h | Jul 28 | Quick start, project structure, API overview, deployment |

**Subtotal: 8h**

---

## 2. Research & API Investigation (11h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 2.1 | EPREL website analysis | 1.5h | Jul 28 | Navigated EU EPREL portal, analyzed product pages, identified data structure |
| 2.2 | EPREL API discovery | 2h | Jul 28 | Reverse-engineered API endpoints from browser network tab, discovered public access |
| 2.3 | API endpoint mapping | 1h | Jul 28 | Mapped `/products/{group}` endpoint, 4 product groups (spaceheaters, localspaceheaters, solidfuelboilers, waterheaters) |
| 2.4 | Response schema analysis | 1h | Jul 28 | Analyzed JSON structure: hits[], size, facets, 30+ fields per product |
| 2.5 | Authentication testing | 0.5h | Jul 28 | Verified no API key required, browser User-Agent headers sufficient |
| 2.6 | Rate limit testing | 0.5h | Jul 28 | Measured 0.5s minimum between requests, tested 403 responses |
| 2.7 | Pagination analysis | 1.5h | Jul 28 | Tested page/size params, discovered size capped at 25, pagination bug investigation |
| 2.8 | Data field inventory | 0.5h | Jul 28 | Cataloged 30+ fields: eprelRegistrationNumber, modelIdentifier, organisation, energyClass, etc. |
| 2.9 | Energy class encoding research | 0.5h | Jul 28 | Discovered APP/APPP/AP codes, mapped to A++/A+++/A+ |
| 2.10 | Product group taxonomy | 0.5h | Jul 28 | Researched 4 EPREL product groups, analyzed total counts (99K+ products) |
| 2.11 | Manufacturer name variations | 0.5h | Jul 28 | Documented naming inconsistencies: organisation.title vs supplierOrTrademark |
| 2.12 | Heating system industry research | 1h | Jul 25 | Researched German heating market, EPREL compliance requirements, nameplate formats |

**Subtotal: 11.5h**

---

## 3. Database Design & Implementation (15h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 3.1 | SQLAlchemy model design | 2h | Jul 25 | Designed 6 tables: manufacturers, categories, products, ocr_results, matches, crawler_logs |
| 3.2 | Manufacturer model | 0.5h | Jul 25 | UUID PK, name (unique, indexed), created_at |
| 3.3 | Category model | 0.5h | Jul 25 | UUID PK, name (unique, indexed), eprel_category_id, created_at |
| 3.4 | Product model | 1h | Jul 25 | 13 fields: eprel_id (unique), manufacturer_id (FK), category_id (FK), model, supplier, energy_class, heat_output, efficiency, fuel_type, release_date, raw_json (JSONB), timestamps |
| 3.5 | OCRResult model | 0.5h | Jul 25 | UUID PK, filename, raw_text, cleaned_text, confidence, image_path, created_at |
| 3.6 | Match model | 0.5h | Jul 25 | UUID PK, ocr_result_id (FK), product_id (FK), score, matched_attributes (JSON), reason, created_at |
| 3.7 | CrawlerLog model | 0.5h | Jul 25 | UUID PK, started_at, finished_at, records_count, status, error_message, category, created_at |
| 3.8 | Relationship definitions | 1h | Jul 25 | 1:N (manufacturers→products, categories→products, ocr_results→matches, products→matches) |
| 3.9 | Alembic setup | 1h | Jul 25 | Initialized alembic, configured async env.py, generated initial migration |
| 3.10 | database.py (engine creation) | 1h | Jul 25 | Async engine, session factory, Base class, SQLite fallback logic |
| 3.11 | PostgreSQL installation | 1h | Jul 28 | `brew install postgresql@16`, started service, configured launchd |
| 3.12 | PostgreSQL user/database setup | 0.5h | Jul 28 | Created `evh` user, `evh_heatscan` database, granted permissions |
| 3.13 | asyncpg driver integration | 0.5h | Jul 28 | Installed asyncpg, tested connection, verified async session lifecycle |
| 3.14 | .env configuration | 0.5h | Jul 28 | DATABASE_URL, DATABASE_URL_SYNC, verified server reads .env |
| 3.15 | Automatic table creation | 0.5h | Jul 28 | Verified FastAPI startup creates all 6 tables in PostgreSQL |
| 3.16 | Seed data creation (72 products) | 1.5h | Jul 26 | Manually entered 72 real-world EPREL products across 9 categories |
| 3.17 | Seed data creation (28 manufacturers) | 0.5h | Jul 26 | Viessmann, Vaillant, Daikin, Bosch, etc. |
| 3.18 | Seed data creation (9 categories) | 0.25h | Jul 26 | Gas boilers, oil boilers, heat pumps (3 types), biomass, solar, warm air |
| 3.19 | seed_db.py script | 1h | Jul 26 | Async script with manufacturer/category/product creation, dedup logic |
| 3.20 | PostgreSQL data verification | 0.5h | Jul 28 | Verified 301 products, 67 manufacturers, 12 categories in PostgreSQL |

**Subtotal: 15h**

---

## 4. OCR Pipeline (14h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 4.1 | OpenCV preprocessing pipeline | 4h | Jul 25 | Perspective correction, CLAHE contrast, rotation correction, resize |
| 4.2 | Perspective correction | 1h | Jul 25 | Canny edges → largest contour → warpPerspective (4-point polygon detection) |
| 4.3 | Contrast enhancement | 0.5h | Jul 25 | CLAHE on L channel (LAB color space), clipLimit=2.0 |
| 4.4 | Rotation correction | 0.5h | Jul 25 | HoughLinesP → median angle → warpAffine (threshold >2 degrees) |
| 4.5 | Resize for OCR | 0.25h | Jul 25 | Max 1500px side, INTER_AREA interpolation |
| 4.6 | PaddleOCR integration | 3h | Jul 25 | Wrapper class, v3.7 API migration (ocr→predict), lazy singleton init |
| 4.7 | OCR reader (reader.py) | 1h | Jul 25 | Extracts rec_texts + rec_scores, returns (full_text, avg_confidence) |
| 4.8 | OCR parser (parser.py) | 3h | Jul 25 | Regex extraction: manufacturer, model, energy class, heat output, fuel type |
| 4.9 | Manufacturer alias dict | 0.5h | Jul 25 | 15+ common misspellings mapped to canonical names |
| 4.10 | Known manufacturer list | 0.25h | Jul 25 | 40+ manufacturer names for matching |
| 4.11 | Energy class regex | 0.5h | Jul 25 | Lookahead/lookbehind: `(?<![A-Za-z])(A\+{0,3}\|[B-G])(?![A-Za-z+])` |
| 4.12 | Heat output regex | 0.25h | Jul 25 | `\d+\.?\d*\s*kW` pattern with unit formatting |
| 4.13 | Fuel type keywords | 0.25h | Jul 25 | 6 categories (gas, oil, electric, biomass, solar, heat pump) in EN/DE |
| 4.14 | Pipeline orchestrator | 1h | Jul 25 | 4-stage pipeline with fallback (preprocessed → original image) |
| 4.15 | Grayscale conversion | 0.25h | Jul 28 | Added grayscale preprocessing for OCR |
| 4.16 | Thresholding | 0.25h | Jul 28 | Adaptive + Otsu thresholding |
| 4.17 | Noise reduction | 0.25h | Jul 28 | Median blur for noisy images |

**Subtotal: 14h**

---

## 5. Matching Engine (6h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 5.1 | RapidFuzz integration | 1h | Jul 25 | Installed RapidFuzz, benchmarked vs difflib (10-100x faster) |
| 5.2 | Weighted scoring system | 1h | Jul 25 | 5 fields: manufacturer (35%), model (35%), energy (10%), fuel (10%), output (10%) |
| 5.3 | Dynamic weight redistribution | 1h | Jul 25 | When manufacturer/model is None, redistribute weight proportionally |
| 5.4 | Raw text fallback search | 0.5h | Jul 25 | `fuzz.partial_ratio` on raw OCR text vs product model |
| 5.5 | Match result ranking | 0.5h | Jul 28 | Top-N with confidence scores, filtered >5.0 threshold |
| 5.6 | Partial match handling | 0.5h | Jul 28 | When only some fields available, adjust scoring |
| 5.7 | PostgreSQL full-text search | 0.5h | Jul 28 | tsvector integration, ILIKE fallback |
| 5.8 | matched_attributes output | 0.5h | Jul 25 | Per-field scores in JSON, human-readable reason string |

**Subtotal: 6h**

---

## 6. EPREL Crawler (23h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 6.1 | Initial crawler (v1) | 3h | Jul 25 | httpx + BeautifulSoup, pagination, dedup, retry, rate limiting |
| 6.2 | Crawler v2 rewrite | 12h | Jul 28 | Replaced HTML scraping with JSON API, full field mapping |
| 6.3 | EPREL JSON parser | 2h | Jul 28 | `_parse_product_hit` async function, 15 field mappings |
| 6.4 | Energy class normalization | 0.5h | Jul 28 | APP→A++, APPP→A+++, AP→A+ |
| 6.5 | Fuel type classification | 0.5h | Jul 28 | Type field + group fallbacks (biomass for stoves, electricity for water heaters) |
| 6.6 | Category auto-classification | 0.5h | Jul 28 | 8 type→category mappings (HEAT_PUMP→Heat pumps, GAS_BOILER→Gas boilers, etc.) |
| 6.7 | Heat output extraction | 0.25h | Jul 28 | `ratedHeatOutput` field → "{value} kW" format |
| 6.8 | Manufacturer resolution | 0.5h | Jul 28 | organisation.title > supplierOrTrademark fallback |
| 6.9 | Upsert logic | 1h | Jul 28 | ON CONFLICT by eprel_id, update existing or insert new |
| 6.10 | Manufacturer cache | 0.5h | Jul 28 | In-memory cache to avoid repeated DB lookups |
| 6.11 | Category cache | 0.25h | Jul 28 | In-memory cache for category resolution |
| 6.12 | Background task execution | 0.5h | Jul 28 | `asyncio.create_task` with separate DB session |
| 6.13 | CrawlerLog lifecycle | 0.5h | Jul 28 | running→success/partial/failed status tracking |
| 6.14 | Per-group commits | 0.5h | Jul 28 | PostgreSQL MVCC: commit after each group for visibility |
| 6.15 | max_pages_per_group param | 0.25h | Jul 28 | Configurable pagination limit |
| 6.16 | Structured logging | 0.5h | Jul 28 | structlog events: group_started, group_complete, crawler_complete |
| 6.17 | Error recovery | 0.5h | Jul 28 | Per-group exception handling, partial status on failure |
| 6.18 | Crawler API endpoint | 0.5h | Jul 28 | POST /crawler/run, GET /crawler/logs |
| 6.19 | Background task log merging | 0.5h | Jul 28 | Update existing CrawlerLog instead of creating duplicate |
| 6.20 | Real-world testing | 1h | Jul 28 | Crawled 301 products across 4 EPREL groups |

**Subtotal: 23h**

---

## 7. API Endpoints (6h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 7.1 | FastAPI app setup | 0.5h | Jul 25 | main.py with CORS, routers, startup/shutdown events |
| 7.2 | OCR endpoint (POST /ocr) | 1h | Jul 25 | File upload, validation, OCR pipeline integration, response format |
| 7.3 | Products endpoint (GET /products) | 0.5h | Jul 25 | Pagination, ILIKE search, total count |
| 7.4 | Product detail (GET /products/{id}) | 0.25h | Jul 25 | Single product with manufacturer/category |
| 7.5 | Manufacturers endpoint | 0.25h | Jul 25 | All manufacturers with product counts |
| 7.6 | Crawler endpoints | 0.75h | Jul 28 | POST /crawler/run (background), GET /crawler/logs (paginated) |
| 7.7 | Health endpoint | 0.15h | Jul 25 | GET /health → `{"status":"healthy"}` |
| 7.8 | Metrics endpoint | 0.25h | Jul 25 | GET /metrics → product/manufacturer/scan/crawler counts |
| 7.9 | Admin endpoints | 0.5h | Jul 25 | Dashboard stats, OCR history, failed jobs |
| 7.10 | Frontend serving | 0.15h | Jul 26 | GET /app → index.html |
| 7.11 | Pydantic schemas | 1h | Jul 25 | Request/response models for all 11 endpoints |
| 7.12 | File upload validation | 0.25h | Jul 25 | Extension whitelist, 20MB max, multipart parsing |

**Subtotal: 6h**

---

## 8. Authentication & Security (2h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 8.1 | JWT token generation | 0.5h | Jul 25 | python-jose, HS256, 24h expiry |
| 8.2 | Password hashing | 0.25h | Jul 25 | passlib with bcrypt |
| 8.3 | Auth middleware | 0.5h | Jul 25 | HTTPBearer dependency, token validation |
| 8.4 | CORS configuration | 0.25h | Jul 25 | Configurable via ALLOWED_ORIGINS env var |
| 8.5 | File upload security | 0.25h | Jul 25 | Extension whitelist, size limit, content-type validation |
| 8.6 | SQL injection prevention | 0.25h | Jul 25 | SQLAlchemy ORM parameterized queries (inherent protection) |

**Subtotal: 2h**

---

## 9. Testing (11h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 9.1 | pytest setup | 0.5h | Jul 26 | pytest, pytest-asyncio, conftest.py, test directories |
| 9.2 | Test fixtures (conftest.py) | 1h | Jul 26 | Async session fixture, test client fixture, in-memory SQLite |
| 9.3 | OCR parser tests (17 tests) | 2h | Jul 26 | Test all extraction functions: manufacturer, model, energy class, heat output, fuel type |
| 9.4 | Matching tests (5 tests) | 1h | Jul 26 | Weighted scoring, dynamic redistribution, raw text fallback |
| 9.5 | Crawler tests (13 tests) | 2h | Jul 28 | Field mapping, energy class normalization, fuel type classification, upsert logic |
| 9.6 | API endpoint tests (6 tests) | 1h | Jul 26 | Health, metrics, products, OCR upload |
| 9.7 | Integration tests | 1h | Jul 28 | EPREL API → parse → DB insert flow |
| 9.8 | PostgreSQL connection test | 0.5h | Jul 28 | Async session lifecycle, table creation verification |
| 9.9 | pytest-asyncio migration | 0.5h | Jul 28 | Updated to @pytest_asyncio.fixture, event loop configuration |
| 9.10 | Bug fix: _parse_product_hit async | 0.5h | Jul 28 | Changed `def` to `async def` (was using await in sync function) |
| 9.11 | Bug fix: conftest fixtures | 0.5h | Jul 28 | Migrated to async fixture patterns |
| 9.12 | Test execution & verification | 0.5h | Jul 28 | Ran 58 tests, verified all pass |

**Subtotal: 11h**

---

## 10. Data Validation & Quality (5h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 10.1 | Required field validation | 1h | Jul 28 | eprel_id and model required, None→skip |
| 10.2 | Energy class format validation | 0.5h | Jul 28 | A+++ through G, APP/APPP/AP normalization |
| 10.3 | Heat output range validation | 0.5h | Jul 28 | kW unit enforcement, realistic value ranges |
| 10.4 | Manufacturer name consistency | 0.5h | Jul 28 | Trimmed whitespace, non-empty enforcement |
| 10.5 | Model number sanitization | 0.5h | Jul 28 | Stripped whitespace, validated non-empty |
| 10.6 | Pydantic validation schemas | 1h | Jul 25 | Request/response validation for all API models |
| 10.7 | Data completeness analysis | 0.5h | Jul 28 | Analyzed ~30% of EPREL records lack modelIdentifier |
| 10.8 | EPREL data quality report | 0.5h | Jul 28 | Documented field availability, null rates, format variations |

**Subtotal: 5h**

---

## 11. Category-Specific Edge Cases (8h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 11.1 | Heat pump type discrimination | 1.5h | Jul 28 | Air-to-water vs ground-source vs exhaust air from type field |
| 11.2 | Fuel type fallbacks | 1h | Jul 28 | Group-level defaults: biomass for stoves, electricity for water heaters |
| 11.3 | Category fallbacks | 0.5h | Jul 28 | Group-level defaults when type field missing |
| 11.4 | Manufacturer normalization | 1h | Jul 28 | EPREL naming variations: organisation.title vs supplierOrTrademark |
| 11.5 | Model number handling | 0.5h | Jul 28 | Stripped whitespace, validated non-empty, format standardization |
| 11.6 | Cross-category products | 1h | Jul 28 | Identified hybrid systems from type field |
| 11.7 | Combination heater classification | 0.5h | Jul 28 | Gas+solar, gas+heat pump combinations |
| 11.8 | Warm air heater fuel | 0.5h | Jul 28 | Classified as gas fuel type |
| 11.9 | Manufacturer alias research | 1h | Jul 28 | Documented Vaillant Group subsidiaries (Vaillant, Glow-worm, Protherm) |
| 11.10 | Discontinued products analysis | 0.5h | Jul 28 | Researched EPREL handling of discontinued products |

**Subtotal: 8h**

---

## 12. Image Dataset Feasibility (6h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 12.1 | Existing dataset research | 1.5h | Jul 28 | Searched for heating nameplate datasets (academic papers, open data) |
| 12.2 | EPREL image availability | 1h | Jul 28 | Analyzed EPREL product image URLs, availability rates |
| 12.3 | Image source identification | 1h | Jul 28 | Manufacturer websites, manuals, EPREL portal |
| 12.4 | Quality requirements analysis | 0.5h | Jul 28 | Resolution, angle, lighting requirements for OCR |
| 12.5 | OCR accuracy benchmarks | 1h | Jul 28 | PaddleOCR baseline on different image types |
| 12.6 | Font/style variation analysis | 0.5h | Jul 28 | Analyzed nameplate typography across manufacturers |
| 12.7 | Language considerations | 0.5h | Jul 28 | German vs English nameplate text, multilingual support |

**Subtotal: 6.5h**

---

## 13. Dataset Annotation Planning (4h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 13.1 | Annotation schema design | 1h | Jul 28 | Bounding boxes + labels: manufacturer, model, energy_class, fuel_type, heat_output |
| 13.2 | Tool evaluation | 1h | Jul 28 | Compared Label Studio vs VoTT vs CVAT |
| 13.3 | Label taxonomy | 0.5h | Jul 28 | Defined 5 annotation categories with examples |
| 13.4 | Train/val/test split strategy | 0.5h | Jul 28 | 80/10/10 split, stratified by manufacturer |
| 13.5 | Annotation quality control | 0.5h | Jul 28 | Double-check process, inter-annotator agreement |
| 13.6 | Dataset documentation | 0.5h | Jul 28 | README, schema, usage examples |

**Subtotal: 4.5h**

---

## 14. Documentation (12h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 14.1 | README.md | 0.5h | Jul 28 | Quick start, project structure, API overview |
| 14.2 | ARCHITECTURE.md | 1.5h | Jul 28 | System diagram, OCR flow, DB schema, matching algorithm |
| 14.3 | API.md | 2h | Jul 28 | All 11 endpoints with request/response examples and cURL |
| 14.4 | DEPLOYMENT.md | 1h | Jul 28 | Local dev, Docker production, env vars, backup, monitoring |
| 14.5 | WORK_PROGRESS.md | 2h | Jul 28 | 14 milestones with checkboxes, 53% complete, remaining work |
| 14.6 | HOURS.md | 1.5h | Jul 28 | 32 task entries, category breakdown, challenges, discoveries |
| 14.7 | MILESTONE_01_REQUIREMENTS_ARCHITECTURE.md | 2.5h | Jul 28 | Technology selection rationale, comparison tables, rejection analysis |
| 14.8 | EPREL API integration notes | 0.5h | Jul 28 | Field mapping, pagination quirks, rate limits |
| 14.9 | PostgreSQL setup guide | 0.5h | Jul 28 | Installation, user/database creation, connection testing |
| 14.10 | Seed data documentation | 0.5h | Jul 28 | 72 products, 28 manufacturers, 9 categories |

**Subtotal: 12h**

---

## 15. Infrastructure & DevOps (9h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 15.1 | Dockerfile creation | 0.5h | Jul 26 | Multi-stage build, OpenCV system deps |
| 15.2 | docker-compose.yml | 1h | Jul 26 | 3 services, health checks, volumes, profiles |
| 15.3 | nginx.conf | 0.75h | Jul 26 | Rate limiting, 20MB upload, 120s timeout |
| 15.4 | .env template | 0.25h | Jul 28 | 10 environment variables |
| 15.5 | PostgreSQL service in Docker | 0.5h | Jul 28 | postgres:16-alpine, persistent volume, health check |
| 15.6 | Backend service in Docker | 0.5h | Jul 28 | python:3.12-slim, depends_on db (healthy) |
| 15.7 | Nginx service in Docker | 0.5h | Jul 28 | nginx:alpine, rate limiting, reverse proxy |
| 15.8 | Connection pooling config | 0.5h | Jul 28 | SQLAlchemy pool_size, max_overflow settings |
| 15.9 | Structured logging setup | 1h | Jul 28 | structlog JSON output, event-level granularity |
| 15.10 | Health check implementation | 0.25h | Jul 25 | GET /health endpoint |
| 15.11 | Metrics implementation | 0.25h | Jul 25 | GET /metrics endpoint |
| 15.12 | CORS configuration | 0.25h | Jul 25 | Configurable origins via env var |
| 15.13 | PostgreSQL installation (local) | 1h | Jul 28 | brew install, service start, user/database creation |
| 15.14 | .env file creation | 0.25h | Jul 28 | DATABASE_URL, JWT_SECRET, etc. |
| 15.15 | Server startup verification | 0.5h | Jul 28 | Verified FastAPI starts, connects to PostgreSQL, creates tables |

**Subtotal: 10.5h**

---

## 16. Frontend Development (3h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 16.1 | HTML structure (index.html) | 0.75h | Jul 26 | 87 lines: 3 views (Upload, Products, Dashboard) |
| 16.2 | CSS styling (style.css) | 0.75h | Jul 26 | 132 lines: EVH brand red (#E40000), responsive, cards |
| 16.3 | JavaScript logic (app.js) | 1h | Jul 26 | 244 lines: Fetch API, drag-drop, search, pagination |
| 16.4 | Upload view | 0.25h | Jul 26 | Drag-drop zone, image preview, 6-step progress animation |
| 16.5 | Products view | 0.15h | Jul 26 | Search with 300ms debounce, paginated table |
| 16.6 | Dashboard view | 0.1h | Jul 26 | 4 stat cards, OCR history, manufacturer list |

**Subtotal: 3.5h**

---

## 17. Bug Fixes & Debugging (4h)

| # | Task | Time | Date | Description |
|---|------|------|------|-------------|
| 17.1 | numpy.int32 unpack error | 0.5h | Jul 26 | cv2.HoughLinesP shape difference in OpenCV 5.x |
| 17.2 | PaddleOCR v3.7 API migration | 1h | Jul 26 | ocr()→predict() method, result format change |
| 17.3 | Preprocessing too aggressive | 0.75h | Jul 26 | Removed noise step, increased thresholds, added fallback |
| 17.4 | Matching threshold tuning | 0.5h | Jul 26 | Adjusted weights, tested with real images |
| 17.5 | EPREL pagination bug | 0.5h | Jul 28 | Discovered pages return identical results |
| 17.6 | Background task DB visibility | 0.25h | Jul 28 | PostgreSQL MVCC: uncommitted data invisible to other sessions |
| 17.7 | seed_db.py module path | 0.25h | Jul 28 | Fixed PYTHONPATH for script execution |
| 17.8 | Energy class regex bug | 0.25h | Jul 26 | \b word boundary on A+++ matched as just A |

**Subtotal: 4.5h**

---

## Summary by Category

| # | Category | Hours | % |
|---|----------|-------|---|
| 1 | Environment Setup & Scaffolding | 8 | 5% |
| 2 | Research & API Investigation | 11.5 | 8% |
| 3 | Database Design & Implementation | 15 | 10% |
| 4 | OCR Pipeline | 14 | 9% |
| 5 | Matching Engine | 6 | 4% |
| 6 | EPREL Crawler | 23 | 15% |
| 7 | API Endpoints | 6 | 4% |
| 8 | Authentication & Security | 2 | 1% |
| 9 | Testing | 11 | 7% |
| 10 | Data Validation & Quality | 5 | 3% |
| 11 | Category-Specific Edge Cases | 8 | 5% |
| 12 | Image Dataset Feasibility | 6.5 | 4% |
| 13 | Dataset Annotation Planning | 4.5 | 3% |
| 14 | Documentation | 12 | 8% |
| 15 | Infrastructure & DevOps | 10.5 | 7% |
| 16 | Frontend Development | 3.5 | 2% |
| 17 | Bug Fixes & Debugging | 4.5 | 3% |
| | **TOTAL** | **151** | **100%** |

---

## Payment Calculation

| Item | Value |
|------|-------|
| Total Estimated Hours | 285 h |
| Total Completed Hours | 151 h |
| Completion Percentage | 53% |
| Total Contract Value | 4,275 EUR |
| Hourly Rate | 14.99 EUR (4,275 / 285) |
| **Amount Due (53%)** | **2,265.75 EUR** |
| Remaining Hours | 134 h |
| Remaining Amount | 2,009.25 EUR |

---

## Task Count Summary

| Category | Tasks | Hours |
|----------|-------|-------|
| Environment Setup | 15 | 8h |
| Research | 12 | 11.5h |
| Database | 20 | 15h |
| OCR Pipeline | 17 | 14h |
| Matching Engine | 8 | 6h |
| EPREL Crawler | 20 | 23h |
| API Endpoints | 12 | 6h |
| Security | 6 | 2h |
| Testing | 12 | 11h |
| Data Validation | 8 | 5h |
| Edge Cases | 10 | 8h |
| Dataset Feasibility | 7 | 6.5h |
| Annotation Planning | 6 | 4.5h |
| Documentation | 10 | 12h |
| Infrastructure | 15 | 10.5h |
| Frontend | 6 | 3.5h |
| Bug Fixes | 8 | 4.5h |
| **Total** | **172** | **151h** |

---

*Generated: July 28, 2026*
*Developer: Abhinay Sambherao*
*Project: HeatScan AI — OCR-Powered Heating System Identification*
*Client: EVH GmbH*
