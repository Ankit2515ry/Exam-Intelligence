"""Privacy-safe, best-effort JSONL performance instrumentation."""

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
import json
import logging
import os
from pathlib import Path
import threading
import time
import uuid

from app.config import settings

logger = logging.getLogger(__name__)
_current_event = ContextVar("performance_event", default=None)
_write_lock = threading.Lock()

STAGES = {
    "chat": (
        "query_embedding", "vector_search", "bm25", "hybrid_fusion",
        "reranking", "prompt_construction", "gemini_api",
    ),
    "ingestion": (
        "upload_validation", "file_storage", "pdf_parsing", "ocr",
        "chunking", "embedding_generation", "chroma_storage", "sql_persistence",
    ),
}


def _models():
    return {
        "embedding": "all-MiniLM-L6-v2",
        "reranker": settings.RERANK_MODEL,
        "llm": settings.LLM_MODEL,
    }


def new_event(operation):
    return {
        "schema_version": 1,
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "durations_ms": {name: None for name in STAGES[operation]},
        "total_duration_ms": None,
        "counts": {},
        "success": None,
        "failure_category": None,
        "failure_stage": None,
        "models": _models(),
        "provider_mode": settings.PERFORMANCE_PROVIDER_MODE,
        "measurement_class": settings.PERFORMANCE_MEASUREMENT_CLASS,
        "run_temperature": settings.PERFORMANCE_RUN_TEMPERATURE,
        "code_revision": os.getenv("GIT_COMMIT_SHA") or os.getenv("RENDER_GIT_COMMIT"),
        "cleanup_outcome": None,
    }


def current_event():
    return _current_event.get()


def set_value(key, value):
    event = current_event()
    if event is not None:
        event[key] = value


def set_count(key, value):
    event = current_event()
    if event is not None:
        event["counts"][key] = int(value)


@contextmanager
def stage(name):
    event = current_event()
    if event is None or name not in event["durations_ms"]:
        yield
        return
    started = time.perf_counter()
    try:
        yield
    except Exception:
        event["failure_stage"] = name
        raise
    finally:
        elapsed = max(0.0, (time.perf_counter() - started) * 1000)
        previous = event["durations_ms"][name]
        event["durations_ms"][name] = elapsed if previous is None else previous + elapsed


def _failure_category(exc):
    cause = exc
    while cause is not None:
        if hasattr(cause, "category"):
            return cause.category
        cause = cause.__cause__
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "timeout" in name or "timeout" in text:
        return "timeout"
    if "quota" in name or "quota" in text or "resourceexhausted" in name:
        return "quota"
    if exc.__class__.__name__ == "LLMProviderError":
        return "provider"
    return "application"


def instrument_operation(operation):
    def decorator(function):
        @wraps(function)
        async def async_wrapper(*args, **kwargs):
            event = new_event(operation)
            token = _current_event.set(event)
            started = time.perf_counter()
            try:
                result = await function(*args, **kwargs)
                event["success"] = True
                return result
            except Exception as exc:
                event["success"] = False
                event["failure_category"] = _failure_category(exc)
                raise
            finally:
                event["total_duration_ms"] = max(0.0, (time.perf_counter() - started) * 1000)
                _current_event.reset(token)
                write_event(event)

        @wraps(function)
        def sync_wrapper(*args, **kwargs):
            event = new_event(operation)
            token = _current_event.set(event)
            started = time.perf_counter()
            try:
                result = function(*args, **kwargs)
                event["success"] = True
                return result
            except Exception as exc:
                event["success"] = False
                event["failure_category"] = _failure_category(exc)
                raise
            finally:
                event["total_duration_ms"] = max(0.0, (time.perf_counter() - started) * 1000)
                _current_event.reset(token)
                write_event(event)

        return async_wrapper if __import__("inspect").iscoroutinefunction(function) else sync_wrapper
    return decorator


def _rotate(path):
    if not path.exists() or path.stat().st_size < settings.PERFORMANCE_METRICS_MAX_BYTES:
        return
    backups = settings.PERFORMANCE_METRICS_BACKUPS
    if backups == 0:
        path.unlink(missing_ok=True)
        return
    oldest = path.with_name(f"{path.name}.{backups}")
    oldest.unlink(missing_ok=True)
    for index in range(backups - 1, 0, -1):
        source = path.with_name(f"{path.name}.{index}")
        if source.exists():
            source.replace(path.with_name(f"{path.name}.{index + 1}"))
    path.replace(path.with_name(f"{path.name}.1"))


def write_event(event):
    if not settings.PERFORMANCE_METRICS_ENABLED:
        return
    try:
        path = Path(settings.PERFORMANCE_METRICS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, separators=(",", ":"), sort_keys=True)
        with _write_lock:
            _rotate(path)
            with path.open("a", encoding="utf-8") as stream:
                stream.write(line + "\n")
    except Exception:
        logger.exception("Performance metric write failed; application behavior is unchanged")
