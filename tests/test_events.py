"""Tests for event scheduling and duration parsing."""

import pytest

from rnetsim.fabric.events import EventScheduler, parse_duration


class TestParseDuration:
    def test_seconds(self):
        assert parse_duration("10s") == 10.0

    def test_minutes(self):
        assert parse_duration("5m") == 300.0

    def test_hours(self):
        assert parse_duration("1h") == 3600.0

    def test_compound_minutes_seconds(self):
        assert parse_duration("2m30s") == 150.0

    def test_compound_hours_minutes(self):
        assert parse_duration("1h30m") == 5400.0

    def test_full_compound(self):
        assert parse_duration("1h2m3s") == 3723.0

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid duration"):
            parse_duration("foobar")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Invalid duration"):
            parse_duration("")

    def test_decimal_values(self):
        assert parse_duration("1.5m") == 90.0

    def test_case_insensitive(self):
        assert parse_duration("5M") == 300.0
        assert parse_duration("10S") == 10.0


class TestEventScheduler:
    def test_initial_state(self):
        scheduler = EventScheduler()
        assert scheduler._running is False
        assert len(scheduler._tasks) == 0

    def test_cancel_all_clears_tasks(self):
        scheduler = EventScheduler()
        scheduler._running = True
        scheduler.cancel_all()
        assert scheduler._running is False
        assert len(scheduler._tasks) == 0
