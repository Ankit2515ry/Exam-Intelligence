# Exam Intelligence — Verified Resume Bullets & Metrics

Empirical engineering achievements measured during the Exam Intelligence RAG modernization. All numbers are backed by reproducible test runs and recorded evaluation telemetry.

---

## Google XYZ Resume Format

> **Accomplished [X], measured by [Y], by doing [Z].**

### Bullet 1: Hybrid RAG Retrieval Quality & Latency
- **Accomplished [X]:** Engineered and benchmarked a hybrid RAG retrieval pipeline integrating dense semantic vector search, BM25 keyword ranking, and cross-encoder reranking.
- **Measured by [Y]:** Achieved **84.6% Hit@5**, **0.74 MRR@10**, **66.7% Recall@5**, and **64.4 ms** average retrieval latency across a 796-page academic evaluation corpus.
- **By doing [Z]:** Implemented weighted score fusion (0.7 vector / 0.3 BM25), recursive character chunking with 50-character overlap, and an offline evaluation harness validating sub-chunk ground-truth passage alignment.

### Bullet 2: PDF Ingestion Throughput, OCR & Cross-Store Data Integrity
- **Accomplished [X]:** Built an isolated streaming PDF ingestion and OCR engine with transactional compensation and cross-store consistency across PostgreSQL and ChromaDB.
- **Measured by [Y]:** Indexed **796 physical pages (3,449 chunks)** across 10 course textbooks in **73.2s (10.9 pages/sec aggregate throughput)** with **100% SQL-to-Chroma chunk ID set equality** and zero orphan vectors.
- **By doing [Z]:** Implemented streaming header/signature validation, layout-aware PyMuPDF block extraction with automatic Tesseract OCR fallback, and single-transaction rollbacks on failure.

### Bullet 3: Reliability, Security Hardening & Automated Testing
- **Accomplished [X]:** Hardened multi-tenant security, document ownership isolation, and error compensation across document lifecycle operations.
- **Measured by [Y]:** Maintained **107 passing backend automated tests** with 83% code coverage and zero regressions across six identified bug categories.
- **By doing [Z]:** Built a cryptographic environment preflight auditor, enforced strict UUIDv4 ownership validation across API endpoints and vector queries, and implemented staged two-phase physical file deletion.

---

## LaTeX Implementation

Compatible with standard LaTeX resume templates (e.g., Jake's Resume / Overleaf `resumeProjectHeading` and `resumeItemListStart`):

```latex
\resumeProjectHeading
    {\textbf{Exam Intelligence} $|$ \emph{Python, FastAPI, PostgreSQL, ChromaDB, SentenceTransformers, BM25, PyMuPDF}}{2026}
    \resumeItemListStart
      \resumeItem{Engineered a hybrid RAG retrieval pipeline combining dense semantic search (\emph{all-MiniLM-L6-v2}), BM25 keyword retrieval, and cross-encoder reranking, achieving \textbf{84.6\% Hit@5}, \textbf{0.74 MRR@10}, and \textbf{64.4 ms} average retrieval latency across an evaluation corpus of 796 pages.}
      \resumeItem{Architected an isolated streaming PDF ingestion pipeline with Tesseract OCR fallback and transactional compensation, indexing \textbf{796 pages (3,449 chunks)} across 10 documents in \textbf{73.2s (10.9 pages/sec)} with \textbf{100\% SQL-to-Chroma vector consistency} and zero orphan records.}
      \resumeItem{Hardened multi-tenant security and cross-store data lifecycle by implementing strict UUID ownership guards and transactional rollbacks, verified by \textbf{107 automated regression tests} (83\% backend coverage) and cryptographic environment preflight audits.}
    \resumeItemListEnd
```

---

## Verified Metric Summary Table

| Category | Metric | Verified Value | Evidence Source |
|---|---|---:|---|
| **Retrieval Quality** | Hit Rate @ 5 | **84.62%** (0.8462) | `backend/evaluation/results/pilot-v1/evaluation-results.json` |
| **Retrieval Quality** | Mean Reciprocal Rank (MRR@10) | **0.7372** | `backend/evaluation/results/pilot-v1/evaluation-results.json` |
| **Retrieval Quality** | Recall @ 5 | **66.67%** (0.6667) | `backend/evaluation/results/pilot-v1/evaluation-results.json` |
| **Retrieval Quality** | Precision @ 5 | **20.00%** (0.2000) | `backend/evaluation/results/pilot-v1/evaluation-results.json` |
| **Retrieval Quality** | nDCG @ 5 | **0.6586** | `backend/evaluation/results/pilot-v1/evaluation-results.json` |
| **Retrieval Latency** | Mean Query Latency | **64.37 ms** | `backend/evaluation/results/pilot-v1/evaluation-results.json` |
| **Retrieval Latency** | Median Query Latency | **60.15 ms** | `backend/evaluation/results/pilot-v1/evaluation-results.json` |
| **Retrieval Latency** | Warm Latency Range | **46.60 – 66.02 ms** | `backend/evaluation/results/pilot-v1/evaluation-results.json` |
| **Ingestion Volume** | Total Physical Pages Indexed | **796 pages** | `backend/evaluation/private/corpus-v1-selection.json` |
| **Ingestion Volume** | Total Searchable Chunks | **3,449 chunks** | `backend/evaluation/private/chroma-corpus-v1` |
| **Ingestion Speed** | Total Sequential Ingestion Time | **73.20 seconds** | `backend/evaluation/private/metrics-corpus-v1.jsonl` |
| **Ingestion Speed** | Ingestion Page Throughput | **10.87 pages/sec** | `backend/evaluation/private/metrics-corpus-v1.jsonl` |
| **Data Integrity** | SQL–Chroma ID Consistency | **100% (3,449 / 3,449)** | `backend/scripts/verify_full_evaluation_corpus.py` |
| **Test Suite** | Backend Regression Tests | **107 passed, 0 failed** | Pytest test suite (`backend/tests`) |
| **Code Coverage** | Backend Test Coverage | **83%** | Authoritative pytest coverage report |
