# Deployment Guide

## Local Development (No Docker)

Requirements: Python 3.9+, pip

```bash
cd backend
pip install -r requirements.txt
python -m scripts.seed_db
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Uses SQLite at `backend/heatscan.db` (auto-created).

## Production (Docker)

Requirements: Docker, Docker Compose

```bash
cd docker

# Set environment variables
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -hex 16)

# Start services
docker compose --profile prod up -d
```

This starts:
- **PostgreSQL 16** on port 5432
- **Backend** on port 8000
- **Nginx** reverse proxy on port 80

### First-time setup

```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Seed database
docker compose exec backend python -m scripts.seed_db
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql+asyncpg://... | Async PostgreSQL URL |
| JWT_SECRET_KEY | change-me | Secret for JWT signing |
| JWT_EXPIRE_MINUTES | 1440 | Token lifetime (24h) |
| ALLOWED_ORIGINS | http://localhost:3000,http://localhost:8000 | CORS origins |
| EPREL_BASE_URL | https://eprel.ec.europa.eu | EPREL API URL |
| MAX_UPLOAD_SIZE_MB | 20 | Max upload size |
| OCR_CONFIDENCE_THRESHOLD | 0.5 | Min OCR confidence |
| LOG_LEVEL | INFO | Logging level |

## Backup

Daily automated backup (cron):

```bash
# Add to crontab
0 2 * * * /path/to/scripts/backup_db.sh
```

Backups saved to `backups/` directory as `heatscan_YYYYMMDD.sql.gz`.

## Monitoring

- Health check: `GET /health`
- Metrics: `GET /metrics`
- Logs: structured JSON via structlog

## Scaling

For high-traffic deployments:
1. Add Redis for caching (OCR results, product queries)
2. Use Celery for async OCR processing
3. Add read replicas for PostgreSQL
4. Deploy multiple backend instances behind load balancer
