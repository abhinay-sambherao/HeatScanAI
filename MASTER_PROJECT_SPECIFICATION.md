# MASTER_PROJECT_SPECIFICATION.md

# EVH Heating OCR & EPREL Intelligence Platform
Version: 1.0

> This document is the single source of truth for OpenCode. Implement exactly as specified.

---

# 1. Executive Summary

## Objective

Develop a production-ready AI platform for EVH that allows a customer or consultant to upload a photo of a heating system nameplate and automatically:

1. Detect the label.
2. Read the text using OCR.
3. Identify manufacturer and model.
4. Match against an EPREL-backed PostgreSQL database.
5. Return structured product information with confidence score.
6. Expose all functionality through REST APIs.

This is NOT a hackathon prototype.

The software should be modular, scalable and maintainable.

---

# Business Goals

Primary Deliverables

- EPREL data crawler
- PostgreSQL database
- OCR pipeline
- Matching engine
- REST API
- Admin dashboard
- Docker deployment
- AWS deployment
- Complete documentation

Success Metrics

- OCR extraction accuracy >80% on agreed evaluation dataset.
- API response <2 s for lookup.
- Modular architecture.
- Fully documented source code.

---

# Tech Stack

Backend
- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

Database
- PostgreSQL

OCR
- PaddleOCR
- OpenCV
- Pillow

Matching
- RapidFuzz

Crawler
- httpx
- BeautifulSoup (only where permitted)
- AsyncIO

Deployment
- Docker
- Docker Compose
- Nginx
- AWS EC2

Testing
- pytest

---

# Folder Structure

```
evh-platform/
 backend/
 frontend/
 crawler/
 matching/
 ocr/
 database/
 scripts/
 docker/
 docs/
 tests/
```

---

# Functional Requirements

## OCR

Input:
JPEG PNG WEBP PDF

Pipeline

Upload

↓

Perspective correction

↓

Noise removal

↓

Contrast enhancement

↓

Rotation correction

↓

OCR

↓

Regex cleanup

↓

Manufacturer extraction

↓

Model extraction

↓

Database lookup

↓

Confidence score

↓

JSON response

---

# Matching Engine

Use RapidFuzz.

Search priority

1 Manufacturer

2 Model

3 Product family

4 Remaining OCR tokens

Return

Top 5 matches

Confidence score

Matched attributes

Reason for match

---

# EPREL Crawler

Build a crawler that:

- Supports all requested categories.
- Handles pagination.
- Stores normalized data.
- Supports incremental updates.
- Logs failures.
- Retries transient failures.
- Can resume interrupted jobs.

Never duplicate products.

---

# PostgreSQL Schema

Manufacturers

- id
- name

Categories

- id
- name

Products

- id
- eprel_id
- manufacturer_id
- category_id
- model
- supplier
- energy_class
- heat_output
- efficiency
- fuel_type
- release_date
- raw_json

OCRResults

- id
- filename
- raw_text
- cleaned_text
- confidence

Matches

- id
- ocr_result_id
- product_id
- score

CrawlerLogs

- id
- started_at
- finished_at
- records
- status

---

# API

POST /ocr

Returns

```
{
 "manufacturer":"",
 "model":"",
 "confidence":0.95,
 "matches":[]
}
```

GET /products/{id}

GET /manufacturers

POST /crawler/run

GET /health

GET /metrics

---

# Admin Dashboard

Features

- OCR history
- Search products
- Trigger crawler
- View logs
- View failed jobs
- Statistics

---

# Security

- JWT Authentication
- HTTPS
- Environment variables
- File validation
- SQL injection prevention
- Input sanitization
- Structured logging

---

# Coding Standards

- Type hints everywhere
- Docstrings
- Black formatting
- Ruff linting
- SOLID principles
- Dependency Injection where appropriate

---

# Testing

Unit Tests

Integration Tests

OCR Tests

Crawler Tests

API Tests

Performance Tests

Target

80%+ coverage

---

# Docker

Provide

Dockerfile

docker-compose.yml

Development profile

Production profile

Persistent PostgreSQL volume

---

# AWS

Deploy using

EC2

Docker Compose

Nginx Reverse Proxy

SSL

Automatic restart

Daily PostgreSQL backup

---

# Documentation

Generate

README

API documentation

Architecture documentation

Deployment guide

Developer guide

Database guide

OCR guide

Crawler guide

Troubleshooting guide

---

# Timeline

Week 1

- Architecture
- Database schema
- FastAPI skeleton
- Docker
- Project setup

Week 2

- EPREL crawler
- PostgreSQL integration
- Import pipeline

Week 3

- OCR pipeline
- Matching engine
- APIs

Week 4

- Dashboard
- Testing
- Documentation
- Deployment

---

# OpenCode Instructions

You are the lead software engineer.

Rules

- Never generate placeholder implementations.
- Every endpoint must be production-ready.
- Write reusable code.
- Separate business logic from API layer.
- Add tests for every feature.
- Keep modules loosely coupled.
- Every function must include typing.
- Every public function must include docstrings.
- Write clean commit-sized code.
- Prefer composition over inheritance.
- Avoid duplicated logic.
- Use configuration files.
- Build incrementally.

Implementation Order

1 Project scaffold
2 Docker
3 Database
4 Alembic
5 FastAPI
6 EPREL crawler
7 OCR
8 Matching
9 REST API
10 Dashboard
11 Tests
12 Documentation
13 Production deployment

Definition of Done

The project is complete when:

✓ OCR extracts text reliably.
✓ Matching identifies products.
✓ EPREL sync works.
✓ PostgreSQL is populated.
✓ APIs are documented.
✓ Docker deployment succeeds.
✓ Tests pass.
✓ Documentation is complete.
✓ Code is production-ready.

Future Roadmap (not in current scope)

- HeatScan AI recommendations
- LLM assistant
- RAG over heating documentation
- Predictive maintenance
- Customer portal
- Analytics dashboards
- Digital Twin
