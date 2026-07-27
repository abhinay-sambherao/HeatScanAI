# HeatScan AI — Backend

Production-ready Python/FastAPI backend for OCR-powered heating system identification and EPREL product matching.

## Overview

HeatScan AI uses computer vision and OCR to identify heating systems from nameplate photos, then matches them against the EU EPREL (Energy Label Products) database. Built for energy consultants, heating installers, and HVAC professionals.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL (prod) / SQLite (dev) |
| ORM | SQLAlchemy 2.0 (async) |
| OCR | PaddleOCR v3.7 |
| Image Processing | OpenCV |
| Fuzzy Matching | RapidFuzz |
| Crawler | httpx + BeautifulSoup |
| Auth | JWT (PyJWT + bcrypt) |
| Testing | pytest + pytest-asyncio |
| Containerization | Docker + Docker Compose |

## Features

- **OCR Pipeline** — Upload a heating system nameplate photo → automatic text extraction → manufacturer/model/energy class detection
- **Product Matching** — Fuzzy matching against 72+ real EPREL products across 9 categories
- **EPREL Crawler** — Async web scraper to pull product data from the EU EPREL database
- **Admin Dashboard** — Metrics, scan history, manufacturer breakdown
- **JWT Authentication** — Secure API access with role-based permissions
- **REST API** — 11 endpoints covering OCR, products, manufacturers, crawler, health, admin

## Quick Start

```bash
# Clone
git clone https://github.com/abhinay-sambherao/HeatScanAI.git
cd HeatScanAI/backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example ../.env

# Seed database
python -m scripts.seed_db

# Run server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Server runs at `http://127.0.0.1:8000`
Swagger docs at `http://127.0.0.1:8000/docs`

## Project Structure

```
HeatScanAI/
├── backend/
│   ├── app/
│   │   ├── api/            # Route handlers (11 endpoints)
│   │   │   ├── ocr.py      # POST /ocr — upload & analyze nameplate
│   │   │   ├── products.py # GET /products — search & list
│   │   │   ├── manufacturers.py
│   │   │   ├── crawler.py  # POST /crawler/run, GET /crawler/logs
│   │   │   ├── health.py   # GET /health, GET /metrics
│   │   │   └── admin.py    # GET /admin/dashboard, /admin/ocr-history
│   │   ├── models/         # SQLAlchemy ORM models (6 tables)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic
│   │   │   ├── ocr_service.py
│   │   │   ├── matching_service.py  # RapidFuzz weighted scoring
│   │   │   ├── crawler_service.py
│   │   │   └── product_service.py
│   │   ├── ocr/            # OCR pipeline
│   │   │   ├── preprocessor.py  # OpenCV: perspective, contrast, rotation
│   │   │   ├── reader.py       # PaddleOCR wrapper
│   │   │   ├── parser.py       # Regex: manufacturer, model, energy class
│   │   │   └── pipeline.py     # Orchestrator with fallback
│   │   ├── core/           # Security, logging, exceptions
│   │   ├── config.py       # pydantic-settings
│   │   ├── database.py     # SQLAlchemy async engine
│   │   └── main.py         # FastAPI app factory
│   ├── tests/              # 34 tests (OCR, matching, crawler, API)
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── docker/                 # Production Docker setup
│   ├── docker-compose.yml  # PostgreSQL + backend + nginx
│   └── nginx/nginx.conf
├── scripts/
│   ├── seed_db.py          # Database seeder (72 products, 28 manufacturers)
│   └── backup_db.sh        # Daily PostgreSQL backup
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── HOURS.md
├── .env.example
├── MASTER_PROJECT_SPECIFICATION.md
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ocr` | Upload nameplate image for OCR analysis |
| GET | `/products` | List/search products (paginated) |
| GET | `/products/{id}` | Get product details |
| GET | `/manufacturers` | List manufacturers with product counts |
| POST | `/crawler/run` | Trigger EPREL crawler |
| GET | `/crawler/logs` | Get crawler run history |
| GET | `/health` | Health check |
| GET | `/metrics` | System metrics |
| GET | `/admin/dashboard` | Admin dashboard stats |
| GET | `/admin/ocr-history` | Recent OCR scan history |
| POST | `/auth/login` | JWT authentication |

## Database

6 tables: `manufacturers`, `categories`, `products`, `ocr_results`, `matches`, `crawler_logs`

Seeded with 72 real-world products across:
- 20 gas boilers (Viessmann, Vaillant, Bosch, Buderus, Worcester Bosch...)
- 5 oil boilers
- 16 air-to-water heat pumps
- 10 ground-source heat pumps
- 2 exhaust-air heat pumps
- 3 combination heaters
- 4 biomass boilers
- 3 solar thermal collectors
- 2 warm air heaters

## Testing

```bash
cd backend
pytest tests/ -v
# 34 passed in 0.55s
```

## Docker (Production)

```bash
docker compose --profile prod up -d
```

Starts PostgreSQL 16 + backend + nginx reverse proxy.

## Development

Local dev uses SQLite (no Docker required). The server auto-creates tables on startup.

```bash
cd backend
uvicorn app.main:app --reload
```

## License

Private — EVH Hackathon Project
