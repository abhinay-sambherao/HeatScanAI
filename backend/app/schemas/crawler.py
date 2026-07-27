"""Pydantic schemas for crawler endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class CrawlerRunResponse(BaseModel):
    """Response when a crawler run is triggered."""

    job_id: uuid.UUID
    status: str
    message: str


class CrawlerLogOut(BaseModel):
    """Crawler log entry."""

    id: uuid.UUID
    started_at: datetime
    finished_at: Optional[datetime] = None
    records_count: int
    status: str
    error_message: Optional[str] = None
    category: Optional[str] = None

    model_config = {"from_attributes": True}


class CrawlerLogList(BaseModel):
    """Paginated crawler log list."""

    items: List[CrawlerLogOut]
    total: int
