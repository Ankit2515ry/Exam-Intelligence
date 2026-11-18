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

## Phase 4C Step 1 & 2: Real evaluation corpus indexing measurements

Measured 2026-11-18 during controlled evaluation indexing of all 10 approved evaluation PDFs.

- **Corpus Summary:** 10 PDFs, 796 physical pages, 796 retained pages, 80,519,988 bytes (~76.79 MiB), 3,449 chunks.
- **Environment:** Windows 10, Python 3.11.9, PostgreSQL (`exam_intelligence_evaluation`), persistent Chroma (`chroma-corpus-v1`), local SentenceTransformer (`all-MiniLM-L6-v2`) on CPU, Tesseract OCR v5.5.0 (`C:\Program Files\Tesseract-OCR\tesseract.exe`). Zero Gemini API calls.
- **Telemetry Source:** `backend/evaluation/private/metrics-corpus-v1.jsonl` (10 verified successful ingestion events).

### Full 10-Document Ingestion Performance

| # | Filename | Size (B) | Pages | Chunks | Total (ms) | Parsing (ms) | OCR (ms) | Embed (ms) | Chroma (ms) | SQL (ms) | OCR Used |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 10 RAG Architectures.pdf | 1,151,668 | 8 | 34 | 506.6 | 20.8 | - | 371.0 | 58.4 | 34.8 | False |
| 2 | SQL Notes by Apna College.pdf | 267,819 | 29 | 175 | 1,477.2 | 34.2 | - | 1,203.9 | 121.7 | 98.7 | False |
| 3 | CMC_Unit-I.pdf | 1,199,250 | 32 | 97 | 747.2 | 43.0 | - | 560.1 | 72.8 | 46.8 | False |
| 4 | MWC-A2.pdf | 3,755,856 | 6 | 32 | 5,677.2 | 597.8 | 4,400.8 | 521.9 | 96.5 | 37.4 | True |
| 5 | SQL (notes).pdf | 3,928,431 | 59 | 66 | 707.0 | 75.2 | - | 516.0 | 51.2 | 35.6 | False |
| 6 | MWC-A1.pdf | 5,042,608 | 6 | 44 | 6,389.5 | 736.2 | 5,147.9 | 419.0 | 39.4 | 24.2 | True |
| 7 | DBMS.pdf | 15,645,017 | 231 | 1,148 | 12,381.4 | 384.3 | - | 10,846.6 | 570.7 | 495.3 | False |
| 8 | Operating-Systems.pdf | 15,957,855 | 258 | 1,415 | 14,003.5 | 507.7 | - | 12,109.6 | 658.7 | 612.1 | False |
| 9 | OOPs.pdf | 16,011,978 | 121 | 301 | 4,923.3 | 305.1 | 1,437.0 | 2,800.1 | 190.3 | 134.7 | True |
| 10 | DBMS_NOTES.pdf | 17,559,506 | 46 | 137 | 26,390.8 | 2,228.6 | 22,565.0 | 1,380.1 | 110.7 | 68.4 | True |
| **Total** | **All 10 Documents** | **80,519,988** | **796** | **3,449** | **73,203.7** | **4,933.0** | **33,550.7** | **30,728.2** | **1,970.4** | **1,588.0** | **4 / 10** |

### Empirical Ingestion Throughput

- **Overall Ingestion Throughput:**
  - Page throughput: **10.87 pages/second** (796 pages / 73.204 s)
  - Data throughput: **1.10 MiB/second** (76.79 MiB / 73.204 s)
  - Chunk throughput: **47.11 chunks/second** (3,449 chunks / 73.204 s)
- **Text-Rich Documents (No OCR, 6 docs, 617 pages, 2,885 chunks):**
  - Cumulative ingestion duration: **29,822.9 ms** (~29.82 s)
  - Page throughput: **20.69 pages/second** (617 pages / 29.823 s)
  - Embedding duration: **25,607.2 ms** (85.86% of text ingestion time)
- **Scanned / Mixed OCR Documents (4 docs, 179 pages, 514 chunks):**
  - Cumulative ingestion duration: **43,380.8 ms** (~43.38 s)
  - Cumulative OCR duration: **33,550.7 ms** (77.34% of OCR-document ingestion time)
  - Embedding duration: **5,121.0 ms** (11.80%)
- **Stage Breakdown Across Entire Corpus:**
  - OCR Execution: 45.83% of total corpus ingestion time (33.55 s)
  - Local Embedding Generation: 41.98% of total corpus ingestion time (30.73 s)
  - PDF Parsing: 6.74% (4.93 s)
  - Chroma Vector Storage: 2.69% (1.97 s)
  - PostgreSQL Persistence: 2.17% (1.59 s)
  - File I/O & Validation: 0.59% (0.43 s)

## Not measured

- Real Gemini latency, timeout rate, quota behavior, or regional variance (generation disabled)
- Genuine retrieval accuracy (Recall@K, Precision@K, MRR@K, nDCG@K) pending labeled gold evaluation questions
- Real SentenceTransformer cross-encoder inference latency or cold model loading in production
- Multi-worker concurrent request saturation, GPU acceleration, or network latency
