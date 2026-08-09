"""Tests for the daily EPREL re-crawl scheduler."""

import datetime

import pytest

from app.scheduler import DailyCrawlerScheduler


class TestNextRunDelay:
    def test_delay_positive_and_within_a_day(self):
        delay = DailyCrawlerScheduler._next_run_delay(3, 0)
        assert 0 < delay <= 24 * 3600

    def test_past_time_schedules_tomorrow(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        past_hour = (now.hour - 1) % 24
        delay = DailyCrawlerScheduler._next_run_delay(past_hour, 0)
        assert 0 < delay <= 24 * 3600


class TestSchedulerLifecycle:
    def test_disabled_start_creates_no_task(self):
        sched = DailyCrawlerScheduler(False)
        sched.start()
        assert sched._task is None

    @pytest.mark.asyncio
    async def test_enabled_start_stop_cancels_cleanly(self):
        sched = DailyCrawlerScheduler(True, hour=3, minute=0)
        sched.start()
        assert sched._task is not None
        await sched.stop()
        assert sched._task is None

    @pytest.mark.asyncio
    async def test_concurrent_guard_skips_without_resetting(self):
        sched = DailyCrawlerScheduler(True, hour=3, minute=0)
        sched._running = True
        await sched._run_once()
        assert sched._running is True
