"""Unit tests for structured logging and build log."""

import json

import pydantic
import pytest
import structlog

from pygramattic_reports.config.settings import LoggingConfig
from pygramattic_reports.logging import BuildLog, BuildLogEntry, get_logger, setup_logging
from pygramattic_reports.models.base import generate_id, now_utc

# ---- setup_logging ----


class TestSetupLogging:
    def test_setup_text_format(self):
        config = LoggingConfig(level="DEBUG", format="text")
        setup_logging(config)
        structlog.reset_defaults()

    def test_setup_json_format(self):
        config = LoggingConfig(level="INFO", format="json")
        setup_logging(config)
        structlog.reset_defaults()

    def test_setup_with_defaults(self):
        config = LoggingConfig()
        setup_logging(config)
        structlog.reset_defaults()


# ---- get_logger ----


class TestGetLogger:
    def test_returns_logger(self):
        config = LoggingConfig()
        setup_logging(config)
        logger = get_logger("test_module")
        assert logger is not None
        structlog.reset_defaults()

    def test_logger_has_module_binding(self, capsys):
        config = LoggingConfig(level="DEBUG", format="json")
        setup_logging(config)
        logger = get_logger("loaders")
        logger.info("test message")
        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output["module"] == "loaders"
        assert output["event"] == "test message"
        assert output["level"] == "info"
        structlog.reset_defaults()


# ---- BuildLogEntry ----


class TestBuildLogEntry:
    def test_create_entry(self):
        ts = now_utc()
        entry = BuildLogEntry(
            timestamp=ts,
            level="info",
            module="loaders",
            message="Loaded file",
        )
        assert entry.timestamp == ts
        assert entry.level == "info"
        assert entry.module == "loaders"
        assert entry.message == "Loaded file"
        assert entry.context == {}

    def test_entry_with_context(self):
        entry = BuildLogEntry(
            timestamp=now_utc(),
            level="warning",
            module="builder",
            message="Slow query",
            context={"duration_ms": 500},
        )
        assert entry.context["duration_ms"] == 500

    def test_entry_is_frozen(self):
        entry = BuildLogEntry(
            timestamp=now_utc(),
            level="info",
            module="test",
            message="frozen check",
        )
        with pytest.raises(pydantic.ValidationError):
            entry.level = "error"  # type: ignore[misc]


# ---- BuildLog ----


class TestBuildLog:
    def test_create_build_log(self):
        build_log = BuildLog(
            build_id=generate_id(),
            started_at=now_utc(),
        )
        assert build_log.status == "in_progress"
        assert build_log.entries == []
        assert build_log.completed_at is None

    def test_add_entry(self):
        build_log = BuildLog(
            build_id=generate_id(),
            started_at=now_utc(),
        )
        build_log.add_entry("info", "loaders", "Loaded CSV", rows=100)
        assert len(build_log.entries) == 1
        assert build_log.entries[0].level == "info"
        assert build_log.entries[0].module == "loaders"
        assert build_log.entries[0].message == "Loaded CSV"
        assert build_log.entries[0].context["rows"] == 100

    def test_finalize(self):
        build_log = BuildLog(
            build_id=generate_id(),
            started_at=now_utc(),
        )
        build_log.finalize("completed")
        assert build_log.status == "completed"
        assert build_log.completed_at is not None

    def test_counter_defaults(self):
        build_log = BuildLog(
            build_id=generate_id(),
            started_at=now_utc(),
        )
        assert build_log.sections_generated == 0
        assert build_log.sections_skipped == 0
        assert build_log.ai_calls == 0
        assert build_log.ai_failures == 0
        assert build_log.charts_generated == 0
        assert build_log.charts_failed == 0

    def test_counters_mutable(self):
        build_log = BuildLog(
            build_id=generate_id(),
            started_at=now_utc(),
        )
        build_log.sections_generated = 5
        build_log.ai_calls = 3
        assert build_log.sections_generated == 5
        assert build_log.ai_calls == 3

    def test_serializes_to_json(self):
        build_log = BuildLog(
            build_id="test-build-001",
            started_at=now_utc(),
        )
        build_log.add_entry("info", "loaders", "Started")
        build_log.finalize("completed")

        data = json.loads(build_log.model_dump_json())
        assert data["build_id"] == "test-build-001"
        assert data["status"] == "completed"
        assert data["completed_at"] is not None
        assert len(data["entries"]) == 1
        assert data["entries"][0]["level"] == "info"

    def test_multiple_entries_ordered(self):
        build_log = BuildLog(
            build_id=generate_id(),
            started_at=now_utc(),
        )
        build_log.add_entry("info", "loaders", "Step 1")
        build_log.add_entry("warning", "builder", "Step 2")
        build_log.add_entry("error", "charts", "Step 3")

        assert len(build_log.entries) == 3
        assert build_log.entries[0].message == "Step 1"
        assert build_log.entries[1].message == "Step 2"
        assert build_log.entries[2].message == "Step 3"
