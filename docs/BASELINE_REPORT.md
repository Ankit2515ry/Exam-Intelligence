# Phase 1 baseline report

Review date: 2026-11-17. This report preserves the Phase 1 baseline and records the
Phase 2A correctness comparison. Machine-readable measurements now represent the
Phase 2A implementation in [baseline_results.json](baseline_results.json); the test
design and limits remain in [TESTING_STRATEGY.md](TESTING_STRATEGY.md).

## Phase 2A results: document-specific retrieval and chat correctness

The authoritative backend run completed with **55 passed, 7 strict expected
failures, 0 failed, 0 errors, 0 unexpected passes, 0 skipped, and 1 warning in
11.42 seconds**. A second complete run without coverage completed with the same
test outcomes in 8.70 seconds. The suite now contains 62 cases: five former xfails
are normal passing regressions, and three ownership/global/no-context guards were
added.

Coverage remains **82% displayed**: 845 statements, 687 covered lines, 158 missing
lines, 81.79% combined exact coverage, 81.30% statement coverage, and 85.34%
branch coverage (99 of 116 branches). The single warning remains Starlette's
TestClient deprecation notice.

Frontend verification passed:

| Command | Result |
|---|---|
| `npm.cmd run lint` | Exit 0; no reported errors or warnings |
| `npm.cmd run build -- --outDir node_modules/.cache/phase2a-build` | Exit 0; 1,807 modules transformed; completed in 832 ms |

The following strict expected failures became normal passing regression tests:

- `test_document_specific_search_excludes_other_documents`
- `test_numeric_document_id_is_rejected_at_uuid_contract`
- `test_empty_retrieval_returns_a_response_without_crashing`
- `test_missing_chunk_lookup_returns_empty_results`
- `test_missing_chunk_api_returns_404`

Additional tests now verify that global scope searches every owned document while
excluding other users, that the route forwards no global document filter, that an
owned document with no indexed context returns without an LLM call, and that
another user's selected document is rejected before retrieval. A missing
owned-document UUID returns 404; a valid UUID belonging to another user returns
403. Canonical UUIDv4 request validation rejects the former numeric ID payload
with 422.

### Synthetic before/after comparison

The same controlled document-membership fixture was used before and after. These
values measure metadata isolation only and are not production retrieval accuracy.

| Measurement | Phase 1 | Phase 2A |
|---|---:|---:|
| Owner chunks available across two documents | 4 | 4 |
| Requested-document chunks available | 2 | 2 |
| Chunks returned for selected document | 4 | 2 |
| Requested-document matches | 2 | 2 |
| Document-scope precision | 0.50 | 1.00 |
| Other-document fraction | 0.50 | 0.00 |
| Other-user fraction | 0.00 | 0.00 |
| Prompt builds for five final chunks | 5 | 1 |

The selected-document query now combines authenticated integer user ID and
document UUID in Chroma's metadata filter. Global scope retains the user-only
filter. The fixed regression also inserts a different user's chunk carrying the
selected UUID and confirms that it is excluded.

When retrieval returns no chunks, the service now returns the existing response
shape with the original question, an empty `sources` list, and:

```text
I could not find relevant information in the uploaded documents.
```

The prompt builder and Gemini service are not called on that path. With context,
the prompt is built once and Gemini is called once. Missing chunk lookup now
returns an empty Chroma result to the route, which produces HTTP 404 while the
existing ownership check still protects present chunks.

### Remaining strict expected failures

Seven expected failures remain and were intentionally left unchanged:

- BUG-05: SQL `chroma_id` values do not match actual Chroma chunk IDs.
- BUG-06 parse failure: document row and PDF remain.
- BUG-06 embedding failure: document row and PDF remain.
- BUG-06 vector-write failure: document row, PDF, and vectors remain.
- BUG-06 first SQL-write failure: document row, PDF, and vectors remain.
- BUG-06 second SQL-write failure: one SQL chunk plus document, PDF, and vectors remain.
- BUG-06D: deletion cleanup can leave SQL state after PDF/vector removal.

Phase 2A did not change chunking, embeddings, BM25, hybrid fusion, reranking,
prompt content, candidate counts, ingestion transactions, or chunk-ID persistence.

## Phase 1 execution summary (historical)

The authoritative backend command was run from `backend/`:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q --tb=short --cov=app --cov-branch --cov-report=term-missing --cov-report=json:tests/artifacts/coverage.json --junitxml=tests/artifacts/junit.xml --baseline-output=../docs/baseline_results.json
```

Result: **exit code 0; 46 passed, 12 strict expected failures, 0 failed, 0 errors,
0 unexpected passes, 0 skipped, and 1 warning in 10.73 seconds.** The one warning
is Starlette's deprecation notice for its current `httpx` TestClient integration;
it did not fail a test.

Coverage was collected across all 52 backend application files, including
unimported namespace-package files:

| Measure | Result |
|---|---:|
| Statements | 812 |
| Covered lines | 658 |
| Missing lines | 154 |
| Combined line/branch display | 82% (81.58% exact) |
| Statement coverage | 81.03% |
| Branches | 100 |
| Covered branches | 86 |
| Branch coverage | 86.00% |

Expected-failure paths and mocked external-model paths count toward coverage, so
coverage is an execution measure rather than a correctness or quality score. No
coverage threshold was invented after seeing these results.

For explicit bug evidence, the regression suite was also executed with expected-
failure handling disabled:

```powershell
.\venv\Scripts\python.exe -B -m pytest -m regression --runxfail -q --tb=line
```

That command intentionally returned **exit code 1: 12 failed, 46 deselected, and
1 warning in 3.48 seconds**. Each failure corresponded to one of the documented
defect invariants. The normal suite keeps those cases as strict xfails, so a fixed
case that unexpectedly passes will also make the suite fail until it is reviewed.

Frontend verification from `frontend/exam_intelligence/`:

| Command | Result |
|---|---|
| `npm.cmd run lint` before repair | Exit 1; 1 error, 0 warnings |
| `npm.cmd run lint` after repair | Exit 0; no reported errors or warnings |
| `npm.cmd run build -- --outDir node_modules/.cache/phase1-build` | Exit 0; 1,807 modules transformed; completed in 1.04s |

The production build emitted `index.html` 0.46 kB, CSS 17.08 kB, and JavaScript
370.27 kB (uncompressed values reported by Vite). This verifies compilation only;
it is not a browser-performance measurement.

All eight synthetic measurement groups were identical across two full suite runs.
This is a reproducibility check of the fixtures and doubles, not evidence that
real-model results are deterministic.

## Phase 1 original health-test limitations (historical)

The retained three tests correctly verify the response shape and call behavior for
liveness, successful readiness, and a mocked database failure. Their dependency
functions are mocked, and they mount only the health router on a small FastAPI app.
They therefore did not verify application assembly, real `SELECT 1`, real Chroma
`count`, vector-only failure, both dependencies failing, recovery, authentication,
ingestion, retrieval, or any external model behavior.

Phase 1 adds actual application mounting, temporary SQL plus in-memory Chroma for
successful readiness, both single-dependency failures, simultaneous failures, and
recovery. It still makes no claim about a live PostgreSQL server, persistent Chroma
after restart, Gemini availability, or Tesseract availability.

## Phase 1 confirmed defects (historical)

| ID | Test evidence | Current result |
|---|---|---|
| BUG-01 | `test_document_specific_search_excludes_other_documents` | A document-scoped query returned four same-user chunks: two requested-document matches and two chunks from another document. User isolation remained intact in this fixture. |
| BUG-02 | `test_numeric_document_id_is_rejected_at_uuid_contract` | The API accepted numeric string `"1"`, returned HTTP 200, and forwarded it as `document_id`; Chroma metadata uses document UUIDs. |
| BUG-03 | `test_empty_retrieval_returns_a_response_without_crashing` | Empty retrieval raised `UnboundLocalError` because `prompt` was never assigned. |
| BUG-04 | `test_missing_chunk_lookup_returns_empty_results` and `test_missing_chunk_api_returns_404` | Direct lookup raised `IndexError`; the endpoint returned HTTP 500 rather than the intended 404. |
| BUG-05 | `test_sql_chunk_ids_match_chroma_ids` | The generated PDF produced three SQL and three Chroma chunks, but zero SQL `chroma_id` values matched Chroma IDs. |
| BUG-06 | Five parameterized ingestion-failure tests | Parse/embedding failures left a document row and PDF. Vector-write and SQL failures also left four vectors; failure at the second SQL chunk left one committed SQL chunk. |
| BUG-06D | `test_cleanup_failure_preserves_consistent_document_state` | A nonempty document directory caused deletion to fail after vectors and PDF were removed, while the SQL document remained. |

At the Phase 1 checkpoint these were reproduction tests rather than implemented
fixes. Phase 2A has since repaired BUG-01 through BUG-04. The numeric-ID test
exercises the HTTP contract using the former `Chat.jsx` value shape; it is not a
browser test.

## Phase 1 reproducible synthetic baseline (historical)

The harness loads no local `.env`, does not open production SQL/Chroma paths, uses
temporary SQLite files and a fresh in-memory Chroma collection per case, generates
its PDF in memory, replaces embedding/reranking/Gemini constructors with deterministic
doubles, and blocks outbound network/DNS access. These measurements describe that
controlled system only.

### Retrieval scope

The corpus had five chunks: four owned by the queried user, split evenly across
two documents, plus one chunk owned by another user. A request for document A with
`k=5` returned the four owner chunks:

| Measure | Result |
|---|---:|
| Returned chunks | 4 |
| Requested-document matches | 2 |
| Document-scope precision | 0.50 |
| Other-document fraction | 0.50 |
| Other-user fraction | 0.00 |

This measures metadata membership only. It is not semantic precision, recall, MRR,
nDCG, answer accuracy, faithfulness, or citation correctness.

### Candidate flow

With 10 owner chunks and two other-user chunks in the controlled collection, the
observed pipeline was:

```text
12 total chunks -> 10 user-filtered vector candidates -> 5 BM25 survivors
-> 5 hybrid survivors -> 5 cross-encoder candidates -> 5 context/source chunks
-> 1 mocked LLM call
```

The requested vector count was 10. The final context contained 348 characters.
The complete prompt was built five times because the current prompt construction
is inside the selected-chunk loop. Only the final copy was sent once to the model.

### Generated-PDF ingestion

The one-page, 948-byte synthetic text PDF produced:

| Measure | Result |
|---|---:|
| Retained text pages | 1 |
| SQL chunks | 3 |
| Chroma chunks | 3 |
| Minimum chunk length | 159 characters |
| Maximum chunk length | 237 characters |
| Mean chunk length | 210.33 characters |
| Matching SQL/Chroma IDs | 0 of 3 (0.00) |

This path used the real PyMuPDF parser, text cleaner, splitter, SQL CRUD and
Chroma collection. Embeddings were deterministic test doubles. It did not invoke
Tesseract or Gemini.

### Ingestion failure artifacts

Every injected failure returned HTTP 500. Counts remaining after each request:

| Failure point | Document rows | SQL chunks | Chroma chunks | PDF files |
|---|---:|---:|---:|---:|
| Parse | 1 | 0 | 0 | 1 |
| Embedding | 1 | 0 | 0 | 1 |
| Vector write accepted, then acknowledgement failure | 1 | 0 | 4 | 1 |
| First SQL chunk write | 1 | 0 | 4 | 1 |
| Second SQL chunk write | 1 | 1 | 4 | 1 |

The accepted-write fault is a controlled failure injection demonstrating absent
compensation. It is not a measured Chroma outage scenario.

## Measurements unavailable in Phase 1

No values are reported for the following because the needed corpus, labels,
environment, or authorization was not available:

| Unmeasured item | Reason |
|---|---|
| Retrieval precision/recall, MRR, MAP, nDCG | No approved versioned corpus with human relevance judgments; model doubles cannot measure semantic relevance. |
| Answer correctness and exam usefulness | No reference answers, grading rubric, subject coverage, or human evaluation. |
| Groundedness, faithfulness, hallucination rate | No claim-level evidence labels or evaluator protocol; Gemini was intentionally mocked. |
| Citation precision/recall | No claim-to-passage citation labels; returned sources are context candidates, not verified citations. |
| OCR accuracy | No scanned-PDF ground truth and no real Tesseract run in the isolated suite. |
| Real embedding/reranker/LLM latency | External models were mocked to prevent downloads and network calls. Mock timing would be meaningless. |
| End-to-end latency, throughput and concurrency | No specified hardware, cache state, network, worker count, load profile or percentile protocol. |
| Memory, CPU/GPU and model startup cost | No stable deployment hardware or profiler protocol. |
| PostgreSQL-specific behavior | Tests use temporary SQLite; no isolated PostgreSQL service or migration fixture was configured. |
| Persistent Chroma recovery and multi-worker safety | Tests use an ephemeral collection; no isolated restart/multi-process environment was supplied. |
| Live deployment availability and topology | The repository has a frontend Render manifest but no verified backend hosting inventory or live URLs. |
| Browser interaction and accessibility | Lint/build are not browser automation, visual inspection, accessibility audit, or device testing. |
| Production data volume/error rate | Production stores and logs were deliberately excluded and never queried. |

Future values should be measured only after defining a permitted test corpus,
labels, hardware, model versions, cache protocol, concurrency, and reporting
percentiles. Production user data should not be treated as a default benchmark.

## Frontend lint defect and scoped repair

Before modification, `npm run lint` failed at `src/pages/Dashboard.jsx:156` with
`react-hooks/set-state-in-effect`. The effect called `loadDocs()`, a component-local
async helper that eventually invoked `setDocuments`; the configured rule traced
that state update back to the effect. The initial flow also had no cleanup to
ignore an asynchronous response after unmount.

This cause and the initial **1 error, 0 warnings** result were written here before
editing the component. The repair starts the initial request inside the effect,
updates state from the promise completion, and uses a cleanup flag to ignore stale
responses. The existing `loadDocs` helper still refreshes after upload and deletion.
No route, API contract, user-facing feature, or RAG behavior was changed.

## Recommendations after Phase 2A

1. Store each actual Chroma chunk ID in its SQL row and reconcile existing data if
   any production records depend on the incorrect references.
2. Design ingestion/deletion compensation and transaction boundaries before coding:
   avoid per-chunk commits, record processing state if needed, and make retries or
   reconciliation safe across SQL, Chroma and filesystem stores.
3. Rerun the complete suite and regenerate baseline JSON after every approved fix.
4. Agree on a representative, permitted evaluation corpus and scoring protocol
   before changing chunking, retrieval, ranking, prompting, or model selection.

Phase 2A stops here. Phase 2B and Phase 2C have not been implemented.
