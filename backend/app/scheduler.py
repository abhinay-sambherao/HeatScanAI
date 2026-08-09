"""Daily EPREL re-crawl scheduler.

Runs the full export-based crawler once per day at a configured UTC time so
the local product table keeps up with EPREL's daily export updates. Disabled
by default (see Settings.CRAWL_SCHEDULE_ENABLED).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from app.core.logging import get_logger
from app.database import async_session_factory
from app.services.crawler_service import run_crawler

logger = get_logger("scheduler")


class DailyCrawlerScheduler:
    """Asyncio task that triggers a full crawl once per day at a set UTC time."""

    def __init__(self, enabled: bool, hour: int = 3, minute: int = 0) -> None:
        self.enabled = enabled
        self.hour = hour
        self.minute = minute
        self._task: asyncio.Task | None = None
        self._running = False

    @staticmethod
    def _next_run_delay(hour: int, minute: int) -> float:
        """Seconds until the next occurrence of hour:minute UTC (tomorrow if past)."""
        now = datetime.now(timezone.utc)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return (target - now).total_seconds()

    async def _run_once(self) -> None:
        """Run one full crawl. Skips if a previous crawl is still running."""
        if self._running:
            logger.warning("scheduler_skipped_concurrent")
            return
        self._running = True
        try:
            async with async_session_factory() as db:
                log = await run_crawler(db, max_pages_per_group=0)
                await db.commit()
                logger.info(
                    "scheduler_crawl_complete",
                    status=log.status,
                    records=log.records_count,
                    errors=log.error_message,
                )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("scheduler_crawl_failed", error=str(exc))
        finally:
            self._running = False

    async def _loop(self) -> None:
        while True:
            delay = self._next_run_delay(self.hour, self.minute)
            logger.info("scheduler_next_run", in_seconds=delay)
            await asyncio.sleep(delay)
            await self._run_once()

    def start(self) -> None:
        """Start the background loop. No-op when disabled or already started."""
        if not self.enabled:
            logger.info("scheduler_disabled")
            return
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._loop())
        logger.info("scheduler_started", hour=self.hour, minute=self.minute)

    async def stop(self) -> None:
        """Cancel the background loop."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("scheduler_stopped")
