# Phase 4 evaluation baseline

## Phase 4C Step 2 indexing status

- **Selected Corpus:** 10 PDFs, 796 physical pages, ~76.79 MiB.
- **Indexed Corpus:** Exactly 10 PDFs indexed and verified (796 physical pages, 796 retained pages, 3,449 chunks).
- **Pending Corpus:** 0 PDFs, 0 physical pages.
- **Cross-Store Consistency:** 3,449 SQL chunks in `exam_intelligence_evaluation` == 3,449 ChromaDB vectors in `chroma-corpus-v1` (100% ID set equality).
- **Pilot/Gold Questions:** 0 labeled.

## Genuine RAG quality

**NOT MEASURED.** No human reference answers, relevant passages,
or 100-question reviewed dataset have yet been evaluated against the indexed PDF.
No real Gemini or paid evaluator call was made. Therefore this phase reports no
genuine Hit@5, precision, recall, MRR, nDCG, correctness, faithfulness,
citation-support, or abstention percentage.

## Synthetic framework verification

The isolated test contains three explicitly synthetic records: two answerable and
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
