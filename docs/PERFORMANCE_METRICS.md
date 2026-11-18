# Performance metrics

Status: Phase 3, 2026-11-18. Instrumentation is local, privacy-safe, and disabled
by default. It does not change upload or chat response bodies.

## Configuration

| Setting | Default | Meaning |
|---|---|---|
| `PERFORMANCE_METRICS_ENABLED` | `false` | Explicitly enables JSONL writes |
| `PERFORMANCE_METRICS_PATH` | `metrics/performance.jsonl` | Local output path |
| `PERFORMANCE_METRICS_MAX_BYTES` | `5242880` | Rotate before the next write after this size |
| `PERFORMANCE_METRICS_BACKUPS` | `3` | Numbered rotated files retained |
| `PERFORMANCE_PROVIDER_MODE` | `real` | Provider class, such as `real` or `mocked` |
| `PERFORMANCE_MEASUREMENT_CLASS` | `unclassified` | Dataset class such as `synthetic` or `production-like` |
| `PERFORMANCE_RUN_TEMPERATURE` | null | Optional `cold`/`warm` run label |

Writes are serialized by a process-local lock and use one compact JSON object per
line. Rotation is also process-local. Multiple workers writing the same file are
unsupported; configure a distinct file per worker or leave metrics disabled.
Writer and rotation errors are logged and never fail the application request.

## Event schema

Every event contains schema version, random request ID, UTC timestamp, operation
(`chat` or `ingestion`), stage durations in milliseconds, total duration,
privacy-safe counts, success, failure category/stage, configured provider mode,
optional cold/warm label, actual model names, optional deployment-provided Git
revision, and cleanup outcome. Skipped stages are JSON `null`, never zero.

Events never contain questions, prompts, filenames, paths, PDF content, chunks,
answers, emails, tokens, credentials, or user IDs.

Chat stages are exclusive boundaries around query embedding, Chroma query, BM25,
hybrid fusion, cross-encoder reranking, prompt construction, and Gemini. Total
duration covers the complete authenticated backend route. Candidate and final-
source counts are included.

Ingestion stages cover streamed file storage, PDF content validation, parsing,
OCR, chunking, batch embedding, Chroma add, and SQL flush/commit. OCR is subtracted
from parsing so stage aggregates do not double-count it. Total duration covers the
complete upload route including compensation. Counts include bytes, retained pages,
and chunks; `ocr_used` and cleanup outcome are recorded without document identity.

All timings use `time.perf_counter()`. Stage and total timers finalize through
`finally` paths, including exceptions.

## Analysis

From `backend/`:

```powershell
.\venv\Scripts\python.exe -m scripts.performance_metrics metrics/performance.jsonl `
  --csv metrics/performance.csv `
  --markdown metrics/performance-summary.md
```

The analyzer validates required fields, reports malformed line numbers, exports
flattened CSV, and groups by operation, measurement class, provider mode, and cold/warm label. These
groups are never combined. Null stage values are excluded. Mean is arithmetic
mean; p50/p90/p95 use nearest rank: sorted value at `ceil(p/100 * n)`.

Ingestion throughput is calculated per event as `pages / total seconds` and
`(bytes / 1,048,576) / total seconds`, then averaged within an isolated group.
Every output includes sample counts and units. An empty group produces null
statistics rather than invented zeros.

## Synchronous behavior

FastAPI upload is declared async but file validation, PyMuPDF parsing, OCR,
embedding, Chroma, and SQL operations execute synchronously in its request task.
Chat is a synchronous route; embedding, retrieval, reranking, prompt building,
and Gemini are synchronous. Phase 3 measures these boundaries and does not move
them to workers or background jobs.
