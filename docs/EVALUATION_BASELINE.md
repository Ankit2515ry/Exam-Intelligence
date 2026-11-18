# Phase 4 evaluation baseline

## Phase 4C Step 2 indexing status

- **Selected Corpus:** 10 PDFs, 796 physical pages, ~76.79 MiB.
- **Indexed Corpus:** Exactly 10 PDFs indexed and verified (796 physical pages, 796 retained pages, 3,449 chunks).
- **Pending Corpus:** 0 PDFs, 0 physical pages.
- **Cross-Store Consistency:** 3,449 SQL chunks in `exam_intelligence_evaluation` == 3,449 ChromaDB vectors in `chroma-corpus-v1` (100% ID set equality).
- **Pilot Dataset:** 15 approved questions (13 answerable, 2 unanswerable) across 3 core course textbooks.

## Empirical Pilot Retrieval Baseline (Phase 4E)

Measured on 2026-11-18 using the isolated evaluation runner (`backend/scripts/rag_evaluation.py --pilot --run-pilot`) against `backend/evaluation/private/pilot-v1.json` on the isolated evaluation stores (`exam_intelligence_evaluation` and `chroma-corpus-v1`).

| Retrieval Metric | Measured Value | Notes / Denominator |
|---|---:|---|
| **Hit@5** | **84.62%** (0.8462) | 11 / 13 eligible answerable questions |
| **Precision@5** | **20.00%** (0.2000) | Label-based passage overlap precision (1 chunk / 5 retrieved) |
| **Recall@5** | **66.67%** (0.6667) | Supporting span coverage at k=5 |
| **MRR@10** | **0.7372** | Mean reciprocal rank of first relevant chunk |
| **nDCG@5** | **0.6586** | Normalized discounted cumulative gain (binary relevance grade 1) |
| **Total Evaluation Execution Time** | **1,080.21 ms** | Offline evaluation run across all 15 questions |
| **Mean Retrieval Latency** | **64.37 ms** | Dense vector search + BM25 keyword fusion + cross-encoder rerank |
| **Median Retrieval Latency** | **60.15 ms** | Median query latency |
| **Warm Retrieval Latency** | **46.60 – 66.02 ms** | Range after initial cold-start query (cold start: 144.64 ms) |
| **Eligible Records Evaluated** | 13 | 2 unanswerable questions excluded from retrieval denominators |
| **Unanswerable Questions** | 2 | Evaluated for abstention (retrieval metrics not penalized) |
| **Runner Errors / Exceptions** | 0 | 100% clean execution |

### Quality Dimensions Not Measured
- **Generation Quality / Faithfulness / Factuality:** **NOT MEASURED.** Real Gemini generation was intentionally disabled (`--generate-answers` was omitted) to guarantee zero API cost and strict local evaluation.
- **Full Gold Dataset:** The pilot represents 15 approved questions. The full 100-question gold standard dataset (`gold-v1.json`) with deterministic splits remains for future scaled benchmarking.

## Synthetic framework verification

The isolated test suite contains three explicitly synthetic records: two answerable and
one unanswerable. Retrieval is deterministic and mocked; it returns one correct
passage for each answerable record and none for the unanswerable record.

| Measurement | Synthetic result |
|---|---:|
| Records | 3 |
| Retrieval-eligible records | 2 |
| Hit@5 | 1.00 |
| Precision@5 | 0.20 |
| Recall@5 | 1.00 |
| MRR@10 | 1.00 |
| nDCG@5 | 1.00 |
| Runner errors | 0 |
| Human answer scores | NOT MEASURED |
| Abstention metrics | NOT MEASURED; generation disabled |

These numbers prove metric arithmetic and runner wiring only. They are not Exam
Intelligence accuracy, do not use real embeddings/reranking, and must not be used
in a resume accuracy claim.

## Inputs required for a real baseline

Provide 8–12 representative course/exam PDFs in
`backend/evaluation/corpus/<corpus-version>/`. Include at least two documents with
overlapping or conflicting facts; include scanned and mathematical documents only
if those capabilities should be measured. Do not use private production uploads.

Create 100 reviewed records in `backend/evaluation/private/gold-v1.json` using the
committed schema/template and 45/20/10/15/10 category allocation. Label stable
document UUIDs, visible PDF pages, shortest sufficient spans, reference answers,
scope, and review status. Then validate and split before indexing the corpus into
an isolated SQL/Chroma environment.

Real Gemini is unnecessary for retrieval metrics. It is necessary only for the
generator-specific correctness, faithfulness, citation-support, and abstention
baseline. One generated answer normally means at least one provider call per
evaluated question, plus retries if deliberately configured. Exact cost cannot be
stated without the then-current provider pricing, token counts, and approved run
plan; estimate those before enabling generation.
