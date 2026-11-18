# Phase 3 synthetic performance baseline

Measured 2026-11-18 during the authoritative pytest coverage run. These are
test-environment measurements, not production latency or model performance.

## Environment

- Windows `10.0.26300`, Python 3.11.9
- Git revision `3baf6f57e612b1bfd42799e0c88cb003e1348415`
- One warm ingestion sample and one warm chat sample
- 948-byte, one-page synthetic text PDF producing three chunks
- Temporary SQLite, ephemeral Chroma, deterministic fake SentenceTransformer,
  fake cross-encoder, and fake Gemini
- No OCR invocation, network access, PostgreSQL, persistent Chroma, or real Gemini
- Zero measured request errors

## Recorded samples

| Operation/stage | Samples | Duration ms |
|---|---:|---:|
| Ingestion total | 1 | 58.189 |
| Upload validation | 1 | 17.460 |
| File storage | 1 | 1.010 |
| PDF parsing excluding OCR | 1 | 4.414 |
| OCR | 0 | NOT EXECUTED (`null`) |
| Chunking | 1 | 0.262 |
| Mock embedding generation | 1 | 0.185 |
| Ephemeral Chroma storage | 1 | 7.671 |
| SQLite persistence/commit | 1 | 23.201 |
| Chat total | 1 | 9.696 |
| Mock query embedding | 1 | 0.127 |
| Ephemeral Chroma search | 1 | 4.539 |
| BM25 | 1 | 0.316 |
| Hybrid fusion | 1 | 0.073 |
| Mock cross-encoder reranking | 1 | 0.048 |
| Prompt construction | 1 | 0.021 |
| Mock Gemini call | 1 | 0.014 |

The chat retrieved three candidates and returned three sources. With one sample,
p50, p90, p95, and mean all equal that sample; this is arithmetic, not evidence
of a latency distribution. The mocked Gemini timing must not be described as
Gemini response latency.

Observed synthetic ingestion throughput was approximately 17.185 pages/second
and 0.0155 MiB/second, calculated from total route duration. These values reflect
a tiny fixture and mocked providers and are unsuitable for capacity claims.

## Not measured

- Real Gemini latency, timeout rate, quota behavior, or regional variance
- Real SentenceTransformer/cross-encoder inference latency or cold model loading
- Tesseract OCR latency or accuracy
- PostgreSQL commit latency and transaction contention
- Persistent Chroma indexing/search/restart behavior
- Concurrent requests, multiple workers, throughput saturation, CPU, GPU, memory,
  network, or production file sizes

Measuring these requires an approved isolated benchmark environment, representative
fixtures, explicit provider authorization, cache/cold-start protocol, concurrency
profile, and repeated samples. No unavailable value is inferred here.
