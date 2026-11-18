# Exam Intelligence development progress

Updated: 2026-11-17. The root `PROJECT_PROGRESS.md` remains the earlier learning
checklist. This file tracks implementation phases and verified deliverables.

## Phase 1: testing foundation, baseline, architecture

- [x] Review the three original health tests and document their limits.
- [x] Add pytest discovery, markers, test dependencies and full-source coverage configuration.
- [x] Install pre-import isolation: no `.env`, live stores, model downloads or outbound services.
- [x] Use per-test temporary SQL files, real in-memory Chroma and synthetic PDFs.
- [x] Add unit and real-app HTTP tests for authentication, ownership and document lifecycle.
- [x] Add strict regressions for all six requested bug categories.
- [x] Exercise five ingestion failure stages and partial deletion after directory cleanup fails.
- [x] Record synthetic scope, candidate-count, parser/chunker and artifact metrics in JSON.
- [x] List unavailable quality/performance/deployment measurements with reasons.
- [x] Write current-architecture HLD and LLD, separating proposed repairs.
- [x] Document the frontend lint failure before editing the effect.
- [x] Repair only Dashboard's initial request effect; verify lint and build.
- [x] Preserve the RAG algorithm, business-logic defects and existing upload.py edit.

The Phase 1 suite contained 58 cases: 46 passing and 12 strict expected failures.
See [BASELINE_REPORT.md](BASELINE_REPORT.md) for the preserved Phase 1 snapshot and
the current Phase 2A comparison.

## Files delivered

New testing files:

- `backend/.coveragerc`
- `backend/pytest.ini`
- `backend/requirements-test.txt`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/unit/test_rag.py`
- `backend/tests/unit/test_safety_and_auth.py`
- `backend/tests/integration/test_api.py`
- `backend/tests/integration/test_health_dependencies.py`
- `backend/tests/regression/test_known_bugs.py`
- `backend/tests/evaluation/test_baseline.py`
- `backend/tests/support/__init__.py`
- `backend/tests/support/doubles.py`
- `backend/tests/support/corpus.py`
- `backend/tests/support/failures.py`
- `backend/tests/support/known_bugs.py`

New documentation/evidence:

- `docs/HLD.md`
- `docs/LLD.md`
- `docs/PROJECT_PROGRESS.md`
- `docs/BASELINE_REPORT.md`
- `docs/TESTING_STRATEGY.md`
- `docs/baseline_results.json`

Modified existing files:

- `backend/.gitignore`: ignore generated coverage/test evidence.
- `frontend/exam_intelligence/src/pages/Dashboard.jsx`: scoped lint repair.
- `README.md`: documentation links and pytest instructions.
- `PROJECT_PROGRESS.md`: pointer to this phase tracker; old learning checklist retained.

Generated local evidence/build output is ignored: `backend/.coverage`,
`backend/tests/artifacts/`, and the frontend's
`node_modules/.cache/phase1-build/`. Test dependencies were installed only into
the existing backend virtual environment. `backend/requirements.txt` is unchanged.

The pre-existing `backend/app/api/upload.py` trailing-whitespace worktree change
is preserved. No backend application-source file was edited in Phase 1.

## Phase 2A: document-specific retrieval and chat correctness

- [x] Send `document_uuid` from the chat selector instead of the SQL integer ID.
- [x] Validate selected IDs as canonical UUIDv4 values.
- [x] Verify the selected document exists and belongs to the authenticated user.
- [x] Apply both user ID and document UUID in document-scoped Chroma queries.
- [x] Preserve user-only filtering for global-scope queries.
- [x] Build the grounded prompt once when context exists.
- [x] Return the existing response contract without calling Gemini when retrieval is empty.
- [x] Return HTTP 404 for missing chunks while preserving existing ownership validation.
- [x] Convert only BUG-01 through BUG-04 strict xfails into normal regressions.
- [x] Regenerate the synthetic baseline and run backend, frontend lint, and frontend build checks.

Phase 2A modified these application files:

- `backend/app/models/chat.py`
- `backend/app/api/chat.py`
- `backend/app/rag/vectordb.py`
- `backend/app/services/chat_service.py`
- `frontend/exam_intelligence/src/pages/Chat.jsx`

It also updated:

- `backend/tests/regression/test_known_bugs.py`
- `backend/tests/integration/test_api.py`
- `backend/tests/evaluation/test_baseline.py`
- `docs/PROJECT_PROGRESS.md`
- `docs/BASELINE_REPORT.md`
- `docs/HLD.md`
- `docs/LLD.md`
- `docs/baseline_results.json`

Final Phase 2A verification: **55 passed, 7 strict expected failures, 0 failed,
0 errors, and 1 warning**. Displayed coverage remains **82%**. Frontend lint and
production build pass. Five former xfails now pass normally; three new guards
cover global-scope retrieval, selected-document ownership, and the HTTP no-context path.

Synthetic document isolation changed from 2 requested-document matches among 4
returned chunks (0.50 scope precision) to 2 among 2 (1.00). The other-user fraction
remained 0.00. Prompt construction changed from five calls to one for the five-
context fixture. These values are controlled fixture measurements, not production
accuracy.

## Phase 2B: PDF upload security, validation, and OCR portability

- [x] Enforce a configurable byte limit while streaming rather than buffering the upload.
- [x] Validate the PDF signature and parse every page before creating a database record.
- [x] Reject empty, malformed/corrupt, encrypted, MIME-mismatched, and oversized PDFs.
- [x] Treat the client filename as display metadata only and reject path/absolute-name input.
- [x] Store new PDFs at a server-generated `<UPLOAD_DIR>/<document UUID>/document.pdf` path.
- [x] Remove staged files and directories when pre-database validation fails.
- [x] Configure Tesseract with `TESSERACT_CMD`, otherwise resolve `tesseract` through `PATH`.
- [x] Keep text PDFs independent of OCR and emit a clear OCR error only when OCR is required.
- [x] Close PyMuPDF documents, pixmaps, byte streams, PIL images, and uploaded streams.
- [x] Add isolated synthetic upload/OCR tests and rerun all Phase 2A regressions.

Phase 2B application and test files:

- `backend/app/config/settings.py`
- `backend/app/api/upload.py`
- `backend/app/rag/parser.py`
- `backend/tests/conftest.py`
- `backend/tests/integration/test_upload_security.py` (new)
- `backend/tests/unit/test_rag.py`

Documentation/evidence updated: `docs/HLD.md`, `docs/LLD.md`,
`docs/BASELINE_REPORT.md`, this file, and `docs/baseline_results.json`.

Final verification: **70 passed, 7 strict expected failures, 0 failed, 0 errors,
and 1 warning**. Displayed coverage is **83%**. Frontend lint and production build
pass. These are isolated synthetic tests; no production files, PostgreSQL,
persistent Chroma, Gemini, or real Tesseract process was accessed.

## Phase 2C: cross-store consistency and recoverable deletion

- [x] Use each generated chunk UUID as both the Chroma ID and SQL `Chunk.chroma_id`.
- [x] Flush documents/chunks in one SQL transaction and commit once per upload.
- [x] Roll SQL back and compensate Chroma/filesystem after ingestion failures.
- [x] Convert all seven remaining strict xfails into passing regressions.
- [x] Stage document directories by rename before deletion.
- [x] Snapshot/restore vectors when deletion fails before SQL commit.
- [x] Refuse deletion before mutation when unexpected directory contents exist.
- [x] Report post-commit filesystem cleanup failure instead of claiming success.
- [x] Add retry, restoration, orphan recovery, and read-only audit tests.
- [x] Add `backend/scripts/check_chunk_consistency.py`; it never writes.

Final verification: **81 passed, 0 xfailed, 0 failed, 0 errors, and 1 warning**.
Displayed coverage is **82%**. Frontend lint and production build pass. No schema,
RAG algorithm, frontend source, or production data was changed.

## Remaining work: awaiting approval

- [ ] Audit legacy IDs in read-only mode and review results before any repair.
- [ ] If approved, back up all stores and design an idempotent reconciliation command with rollback.
- [ ] Agree on a representative evaluation corpus and real-model measurement protocol.
- [ ] Consider ranking/chunking/prompt changes only after obtaining that quality baseline.

At the Phase 2C checkpoint, no Phase 3 work, schema migration, legacy repair,
ranking change, production operation, or deployment had been included.

## Phase 3: performance instrumentation and measurement infrastructure

- [x] Time seven chat stages, eight ingestion stages, and both total route durations.
- [x] Record private IDs, UTC timestamps, safe counts, status, failure classification,
  model names, provider class, optional cold/warm label, and available revision.
- [x] Keep skipped stages null and finalize timers on exception paths.
- [x] Add disabled-by-default rotating JSONL output with a process-local lock.
- [x] Add validation, malformed-line reporting, CSV export, grouped statistics,
  throughput calculations, and Markdown output.
- [x] Return HTTP 502 for Gemini/provider failures instead of a false successful answer.
- [x] Test timeout, quota, provider, privacy, writer-failure, percentile, empty-data,
  throughput, grouping, and all prior regression behavior.
- [x] Capture an isolated two-event synthetic baseline with mocked providers.

Final verification: **92 passed, 0 xfailed, 0 failed, 0 errors, and 1 warning**.
Displayed coverage is **83%**. Frontend lint and production build pass. No retrieval
optimization, external monitoring, cache, worker, dashboard, or Phase 4 work was added.

## Phase 4: gold dataset and objective RAG evaluation

- [x] Define a strict 100-question schema and empty, non-fabricated template.
- [x] Validate labels, approval state, duplicate IDs, and near-duplicate questions.
- [x] Enforce the 45/20/10/15/10 category allocation for final splitting.
- [x] Create deterministic 20/30/50 splits with seeds, IDs, hashes, and leakage reporting.
- [x] Implement Hit@5, Precision@5, Recall@5, MRR@10, and graded nDCG@5.
- [x] Use document/page/supporting-span relevance rather than chunk IDs as ground truth.
- [x] Add citation existence, metadata, scope, and cross-user validity checks.
- [x] Add abstention metrics and separate human correctness/faithfulness/support fields.
- [x] Reuse production retrieval and reranking in an offline runner.
- [x] Keep answer generation explicitly disabled unless requested.
- [x] Emit JSON, CSV, Markdown, run metadata, errors, exclusions, and latency.
- [x] Add synthetic-only framework tests and baseline evidence.

Genuine RAG accuracy remains **NOT MEASURED** because no approved PDFs or human
labels were provided. No RAG parameter, HTTP contract, frontend code, or Phase 5
functionality was changed.

Final Phase 4 verification: **101 passed, 0 xfailed, 0 failed, 0 errors, and
1 warning**. Displayed coverage is **83%**. Frontend lint and production build pass.

## Phase 4B: real-corpus and pilot preparation

- [x] Add a read-only PDF inventory with filename, SHA-256, bytes, and page count.
- [x] Add duplicate-file detection before isolated indexing.
- [x] Add an empty 10–15 record pilot template; no answers were fabricated.
- [x] Add pilot validation without weakening final 100-question/quota rules.
- [x] Validate manifest UUIDs, page bounds, supporting passages, scope, and approvals.
- [x] Add retrieval-only pilot execution and explicitly reject Gemini generation.
- [x] Group overlapping documents and repeated exact passages to reduce split leakage.
- [x] Document isolated upload/UUID/page verification and exact PowerShell commands.

No real PDFs or labels were present, so the pilot was not executed and genuine
quality remains NOT MEASURED. Phase 5 was not started.

Final Phase 4B verification: **104 passed, 0 xfailed, 0 failed, 0 errors, and
1 warning**. Displayed coverage remains **83%**. Frontend lint and production
build pass; no frontend source changed.

## Phase 4B: isolated evaluation bootstrap

- [x] Add explicit evaluation-environment loading that overrides regular `.env`.
- [x] Split preflight into infrastructure and full account-readiness modes.
- [x] Create `exam_intelligence_evaluation` without modifying `exam_intelligence`.
- [x] Create only private evaluation Chroma, upload, and chunks directories.
- [x] Initialize the schema and create one dedicated evaluation application account.
- [x] Verify zero documents/vectors/uploads and account absence from the regular DB.
- [x] Add a launch guard that rejects any regular-resource fallback.

The isolated environment is ready but the selected corpus remains entirely
unindexed. PDF indexing, Gemini calls, Phase 5, and retrieval changes remain out
of scope pending approval.

## Phase 4C: controlled evaluation corpus indexing — Step 1 & Step 2

- [x] Correct preflight readiness logic in `backend/scripts/evaluation_preflight.py` to separate initial bootstrap zero-document checking from ongoing evaluation full readiness.
- [x] Report evaluation account document count dynamically without requiring ongoing count to remain zero.
- [x] Add regression tests verifying preflight succeeds with zero, one, and multiple documents, and rejects bad DB, storage paths, or cross-database leakage.
- [x] Re-verify full evaluation isolation preflight against `exam_intelligence_evaluation`.
- [x] Index PDF #1 (`10 RAG Architectures.pdf`, 8 physical pages, 8 retained pages, 34 chunks, UUID `cbd60b93-0e2b-4e19-b8ad-d63461eac601`) in Step 1.
- [x] Index remaining 9 approved PDFs sequentially in Step 2: `SQL Notes by Apna College.pdf`, `CMC_Unit-I.pdf`, `MWC-A2.pdf`, `SQL (notes).pdf`, `MWC-A1.pdf`, `DBMS.pdf`, `Operating-Systems.pdf`, `OOPs.pdf`, and `DBMS_NOTES.pdf`.
- [x] Configure `TESSERACT_CMD` in evaluation environment for scanned PDFs (`MWC-A1.pdf`, `MWC-A2.pdf`, `OOPs.pdf`, `DBMS_NOTES.pdf`).
- [x] Verify API returns canonical UUIDs, owner ID 1, isolated storage paths, retained pages, and nonempty chunks for all 10 documents.
- [x] Verify exact SQL-to-Chroma consistency: 3,449 chunks in `exam_intelligence_evaluation` match 3,449 vectors in `chroma-corpus-v1` with 100% ID set equality.
- [x] Update private manifests (`corpus-v1-selection.json` and `corpus-v1-manifest.json`) marking all 10 PDFs `indexed` with assigned UUIDs and chunk counts. 0 pending documents remain in the selected corpus.
- [x] Record empirical performance telemetry for all 10 ingestions in `backend/evaluation/private/metrics-corpus-v1.jsonl`: 73,203.7 ms cumulative ingestion duration across 796 pages (10.87 pages/sec overall throughput, 30,728.2 ms embedding duration, 33,550.7 ms OCR duration across 4 OCR documents).
- [x] Re-run operational preflight: passes with `document_count = 10`.
- [x] Re-verify test suite: 107 tests pass.

Genuine RAG accuracy remains **NOT MEASURED** pending pilot/gold dataset authoring. All 10 selected PDFs are fully indexed. No Gemini calls were made.

## Phase 4D: evaluation dataset preparation and validation

- [x] Reconcile Phase 4C performance documentation: confirmed raw per-document chunk counts ($514 \text{ OCR} + 2,935 \text{ text-rich} = 3,449 \text{ total}$) and corrected text-rich chunk subtotal in `docs/PERFORMANCE_BASELINE.md` from 2,885 to 2,935.
- [x] Read and inspect existing dataset schema (`app/evaluation/dataset.py`), pilot template, and review draft (`backend/evaluation/private/pilot_questions_review.md`).
- [x] Convert review draft into standard evaluation schema at `backend/evaluation/private/pilot-v1.json` with 15 questions (`Q01` through `Q15`).
- [x] Map document UUIDs to indexed evaluation PDFs (`10 RAG Architectures.pdf`: 5, `DBMS.pdf`: 5, `Operating-Systems.pdf`: 5).
- [x] Verify evidence on physical PDF pages via PyMuPDF text extraction; align verbatim text and bullets (`\u200b`, `\x07`) to eliminate extraction discrepancies.
- [x] Inspect retrieval label granularity: confirmed that relevance in `app.evaluation.metrics.result_relevance` is evaluated strictly at the supporting text span level within document UUID and page boundaries, not coarse document-level matching.
- [x] Dual-verify all supporting spans against indexed ChromaDB chunk boundaries: mapped 100% of the 15 questions to indexed chunk UUIDs and chunk indices in `backend/evaluation/private/chunk_mapping_results.json`.
- [x] Evaluate unanswerable candidates: confirmed U01 is genuinely unanswerable across the complete 8-page text of `10 RAG Architectures.pdf` (0 occurrences of Gemini, Google, worldwide, 2025); evaluated U02 against `DBMS.pdf` and proposed realistic alternative.
- [x] Run pilot dataset validator (`backend/scripts/rag_evaluation.py --pilot`): verified **0 errors and 15 draft warnings**.
- [x] Verify safety halt on unapproved pilot execution: verified runner strictly blocks execution (`ready_for_pilot_run: false`, `require_approved=True`) until human review and approval.
- [x] Ensure all 107 existing backend tests continue to pass. Zero Gemini calls made; no RAG algorithms modified.
