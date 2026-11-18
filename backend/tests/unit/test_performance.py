import json

import pytest


pytestmark = pytest.mark.unit


def _enable_metrics(monkeypatch, tmp_path):
    from app.config import settings
    path = tmp_path / "performance.jsonl"
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_ENABLED", True)
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_PATH", str(path))
    monkeypatch.setattr(settings, "PERFORMANCE_PROVIDER_MODE", "mocked")
    monkeypatch.setattr(settings, "PERFORMANCE_MEASUREMENT_CLASS", "synthetic")
    return path


def test_timing_event_is_nonnegative_private_and_uses_null_for_skipped(monkeypatch, tmp_path):
    from app.observability.performance import instrument_operation, set_count, stage

    path = _enable_metrics(monkeypatch, tmp_path)

    @instrument_operation("chat")
    def measured(question, email, answer):
        with stage("query_embedding"):
            set_count("retrieved_candidates", 2)
        return "ok"

    assert measured("secret question", "private@example.com", "secret answer") == "ok"
    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["total_duration_ms"] >= 0
    assert event["durations_ms"]["query_embedding"] >= 0
    assert event["durations_ms"]["gemini_api"] is None
    assert event["success"] is True
    serialized = json.dumps(event)
    assert "secret question" not in serialized
    assert "private@example.com" not in serialized
    assert "secret answer" not in serialized


def test_exception_still_writes_timing_and_failure_stage(monkeypatch, tmp_path):
    from app.observability.performance import instrument_operation, stage

    path = _enable_metrics(monkeypatch, tmp_path)

    @instrument_operation("chat")
    def measured():
        with stage("vector_search"):
            raise TimeoutError("synthetic timeout")

    with pytest.raises(TimeoutError):
        measured()
    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["success"] is False
    assert event["failure_category"] == "timeout"
    assert event["failure_stage"] == "vector_search"
    assert event["durations_ms"]["vector_search"] >= 0
    assert event["total_duration_ms"] >= event["durations_ms"]["vector_search"]


def test_writer_failure_does_not_break_application(monkeypatch, tmp_path):
    from app.config import settings
    from app.observability.performance import instrument_operation

    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_ENABLED", True)
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_PATH", str(tmp_path))

    @instrument_operation("chat")
    def measured():
        return "still works"

    assert measured() == "still works"


def test_analysis_handles_malformed_percentiles_empty_data_and_grouping(tmp_path):
    from scripts.performance_metrics import (
        export_csv, latency_stats, load_events, markdown_report, percentile, summarize,
    )

    assert percentile([1, 2, 3, 4], 50) == 2
    assert percentile([1, 2, 3, 4], 95) == 4
    assert percentile([], 95) is None
    assert latency_stats([])["samples"] == 0

    base = {
        "schema_version": 1, "request_id": "one", "timestamp": "2026-11-18T00:00:00Z",
        "operation": "ingestion", "durations_ms": {}, "total_duration_ms": 2000,
        "success": True, "provider_mode": "mocked", "run_temperature": "warm",
        "measurement_class": "synthetic",
        "counts": {"retained_pages": 4, "uploaded_bytes": 1048576},
    }
    path = tmp_path / "input.jsonl"
    path.write_text(json.dumps(base) + "\nnot-json\n" + json.dumps({**base, "request_id": "two", "provider_mode": "real"}) + "\n", encoding="utf-8")
    events, malformed = load_events(path)
    groups = summarize(events)
    assert len(events) == 2 and len(malformed) == 1
    assert len(groups) == 2
    mocked = next(group for group in groups if group["provider_mode"] == "mocked")
    assert mocked["throughput"]["pages_per_second_mean"] == 2
    assert mocked["throughput"]["mib_per_second_mean"] == 0.5
    csv_path = tmp_path / "metrics.csv"
    export_csv(events, csv_path)
    assert "total_duration_ms" in csv_path.read_text(encoding="utf-8")
    assert "Nearest" not in markdown_report(groups, len(malformed))
    assert "Malformed JSONL records: 1" in markdown_report(groups, len(malformed))


def test_metrics_writer_rotates_with_bounded_retention(monkeypatch, tmp_path):
    from app.config import settings
    from app.observability.performance import instrument_operation

    path = _enable_metrics(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_MAX_BYTES", 1)
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_BACKUPS", 1)

    @instrument_operation("chat")
    def measured():
        return True

    measured()
    measured()
    measured()
    assert path.exists()
    assert path.with_name("performance.jsonl.1").exists()
    assert not path.with_name("performance.jsonl.2").exists()
