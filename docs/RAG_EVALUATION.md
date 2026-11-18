# RAG evaluation framework

Status: Phase 4, 2026-11-18. This is an offline framework. It adds no HTTP route
and changes no retrieval, chunking, embedding, ranking, reranking, or prompt logic.

## Retrieval evaluation

The runner calls production `retrieve_relevant_chunks`, then production `rerank`,
and evaluates the first five results. It does not reimplement either algorithm.
The current BM25 stage can return at most five candidates, so MRR@10 observes up
to the ranked results production actually supplies.

For rank cutoff `k=5`:

- Hit@5: 1 if any returned unique chunk matches a labeled support unit, else 0.
- Precision@5: relevant unique returned chunks divided by 5.
- Recall@5: distinct supporting spans covered divided by labeled spans.
- MRR@10: reciprocal rank of the first relevant unique result, otherwise 0.
- nDCG@5: graded DCG divided by ideal DCG; default relevance grade is 1.

A chunk matches when document UUID and page agree and its normalized content
contains the labeled span (or vice versa). Duplicate chunk IDs count once. Missing
metadata cannot match. Questions with no relevance labels, normally unanswerable
questions, are excluded from retrieval means rather than scored as false zeros.
This Precision@5 is conventional label-based retrieval precision, not LLM-judged
context precision.

## Answer and citation evaluation

Answer generation is off unless `--generate-answers` is supplied. That option can
make real Gemini calls depending on configuration and must not be used without
provider approval. The framework never uses an LLM judge automatically.

Generated outputs retain answers and source metadata for human review. Available
deterministic checks cover correct/false/missed abstention and citation existence,
document/page agreement, selected-document scope, and expected user ownership.
Factual correctness, faithfulness, and citation support remain null until reviewed
with the rubric in [EVALUATION_DATASET.md](EVALUATION_DATASET.md).

## Experiment record

Each JSON result records run ID, UTC timestamp, Git SHA, dataset version/hash,
split, corpus hash, actual configured models, chunk size/overlap, candidate count,
final top-k, fusion weights, generation flag, sample count, metrics, retrieval
latency, errors, exclusions, and per-question ranked results. CSV and Markdown
outputs accompany it. Phase 3 performance metrics may be enabled independently.

## Phase 4D: Pilot dataset and retrieval label granularity

As of Phase 4D (2026-11-18), the evaluation framework has a prepared and validated pilot dataset:

- **Dataset File:** `backend/evaluation/private/pilot-v1.json` (version `pilot-v1`).
- **Question Count:** 15 questions (`Q01`–`Q15`).
- **Target Documents:**
  - `10 RAG Architectures.pdf` (`cbd60b93-0e2b-4e19-b8ad-d63461eac601`): 5 questions (Q01–Q05).
  - `DBMS.pdf` (`f513d63e-e487-4d83-b40a-af81169662de`): 5 questions (Q06–Q10).
  - `Operating-Systems.pdf` (`6c04513a-30bd-4fea-814c-9f07c1e9c0b7`): 5 questions (Q11–Q15).
- **Category Composition:** `direct_factual`: 7, `paraphrased_semantic`: 2, `multi_step_reasoning`: 4, `unanswerable`: 2.
- **Answerability:** 13 answerable questions, 2 unanswerable questions (Q05 on 10 RAG Architectures and Q10 on DBMS).
- **Human Review Sheet:** Documented in [EVALUATION_REVIEW.md](EVALUATION_REVIEW.md).
- **Relevance Granularity:** In `app.evaluation.metrics.result_relevance`, a retrieved chunk is scored as relevant if and only if:
  1. `chunk.document_id == unit.document_id`
  2. `chunk.page == unit.page`
  3. `_normalize(span) in _normalize(chunk.content) or _normalize(chunk.content) in _normalize(span)`
  Matching document ID or page alone without text overlap scores zero relevance. Every span in `pilot-v1.json` was verified against both the physical PDF page text and the indexed ChromaDB chunk text boundaries.
- **Reviewer Status:** All 15 records were formally approved (`reviewer_status: "approved"`).
- **Mandatory Approval Barrier:** The runner enforces `require_approved=True` and `validate_pilot` enforces `ready_for_pilot_run: all(record["reviewer_status"] == "approved")`.

## Phase 4E: Empirical Pilot Retrieval Evaluation Run

The official pilot retrieval evaluation was executed on 2026-11-18 using:
```powershell
cd backend
.\venv\Scripts\python.exe scripts/rag_evaluation.py evaluation/private/pilot-v1.json --pilot --run-pilot --manifest evaluation/private/corpus-v1-selection.json --corpus-dir evaluation/corpus/corpus-v1 --corpus-version corpus-v1 --user-id 1 --output evaluation/results/pilot-v1
```

- **Run ID:** `a79bc81a-bd63-4e21-8c96-4b8f8d4bf3df`
- **Output Artifacts:** Emitted to `backend/evaluation/results/pilot-v1/` (`evaluation-results.json`, `evaluation-results.csv`, `evaluation-results.md`).
- **Isolation:** Executed exclusively against the dedicated `exam_intelligence_evaluation` database and `backend/evaluation/private/chroma-corpus-v1` vector store.
- **Empirical Metrics:**
  - **Hit@5:** **84.62%** (11/13 eligible answerable questions)
  - **Precision@5:** **20.00%** (0.2000)
  - **Recall@5:** **66.67%** (0.6667)
  - **MRR@10:** **0.7372**
  - **nDCG@5:** **0.6586**
  - **Latency:** Total run duration **1,080.21 ms**; Mean per-query latency **64.37 ms**; Median **60.15 ms**; Warm range **46.60 – 66.02 ms** (Cold start: 144.64 ms).
  - **Generation:** Zero Gemini API calls; answer generation explicitly disabled.
  - **Errors:** 0 errors, 0 exceptions across all 15 questions.
- **Final Resume Bullets:** Synthesized in Google XYZ format and documented in [RESUME_FINAL.md](RESUME_FINAL.md).

## Commands

Retrieval-only validation-set evaluation:

```powershell
cd backend
.\venv\Scripts\python.exe -m scripts.rag_evaluation evaluation/private/gold-v1.json `
  --split validation --corpus-version <corpus-version> `
  --corpus-dir evaluation/corpus/<corpus-version> --user-id <isolated-user-id> `
  --output evaluation/results/baseline-v1
```

Answer evaluation adds `--generate-answers` only after explicit approval. Do not
use production user data or point the runner at production stores by default.

## Reproducibility requirements

Pin Git SHA, dataset/corpus versions and hashes, model versions, environment,
database/vector snapshots, seed, split metadata, and generation authorization.
Run development while building the framework, validation for predeclared checks,
and held-out exactly once for final reporting. Never tune on held-out metrics.

## Phase 4B leakage review

The original tuple grouping could separate records whose document sets only
partially overlapped, and it did not connect identical support text copied into
different document records. Splitting now builds connected components: records
sharing any relevant/scoped document or exact normalized supporting passage stay
together. Near-duplicate questions are rejected before splitting.

Exact 20/30/50 capacity can still force an oversized connected component across
splits. Such question IDs are written to
`document_groups_split_due_to_capacity`; a real dataset with any entry there must
be reviewed before treating validation or held-out results as independent. Other
remaining risks are semantically equivalent passages with different wording,
incorrect human UUID/page labels, and editions of a document with different hashes.
