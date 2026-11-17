# Phase 1 baseline report

Review date: 2026-11-17. Phase 1 records current behavior. It does not repair the
business-logic defects or change the RAG algorithm. Machine-readable measurements
are in [baseline_results.json](baseline_results.json); the test design and limits
are in [TESTING_STRATEGY.md](TESTING_STRATEGY.md).

## Execution summary

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

## Original health-test limitations

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

## Confirmed defects

| ID | Test evidence | Current result |
|---|---|---|
| BUG-01 | `test_document_specific_search_excludes_other_documents` | A document-scoped query returned four same-user chunks: two requested-document matches and two chunks from another document. User isolation remained intact in this fixture. |
| BUG-02 | `test_numeric_document_id_is_rejected_at_uuid_contract` | The API accepted numeric string `"1"`, returned HTTP 200, and forwarded it as `document_id`; Chroma metadata uses document UUIDs. |
| BUG-03 | `test_empty_retrieval_returns_a_response_without_crashing` | Empty retrieval raised `UnboundLocalError` because `prompt` was never assigned. |
| BUG-04 | `test_missing_chunk_lookup_returns_empty_results` and `test_missing_chunk_api_returns_404` | Direct lookup raised `IndexError`; the endpoint returned HTTP 500 rather than the intended 404. |
| BUG-05 | `test_sql_chunk_ids_match_chroma_ids` | The generated PDF produced three SQL and three Chroma chunks, but zero SQL `chroma_id` values matched Chroma IDs. |
| BUG-06 | Five parameterized ingestion-failure tests | Parse/embedding failures left a document row and PDF. Vector-write and SQL failures also left four vectors; failure at the second SQL chunk left one committed SQL chunk. |
| BUG-06D | `test_cleanup_failure_preserves_consistent_document_state` | A nonempty document directory caused deletion to fail after vectors and PDF were removed, while the SQL document remained. |

These are reproduction tests. Their desired invariants are proposals for Phase 2,
not fixes implemented in Phase 1. The numeric-ID test exercises the current HTTP
contract using the value shape produced by `Chat.jsx`; it is not a browser test.

## Reproducible synthetic baseline

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

## Phase 2 recommendations

1. Make document UUID the canonical UI/API/vector identifier, validate it at the
   boundary, verify ownership, and combine user plus document filters in Chroma.
2. Define explicit empty-retrieval and missing-chunk contracts, then remove the
   associated strict xfails only after those tests pass normally.
3. Store each actual Chroma chunk ID in its SQL row and reconcile existing data if
   any production records depend on the incorrect references.
4. Design ingestion/deletion compensation and transaction boundaries before coding:
   avoid per-chunk commits, record processing state if needed, and make retries or
   reconciliation safe across SQL, Chroma and filesystem stores.
5. Rerun the complete suite and regenerate baseline JSON after every approved fix.
6. Agree on a representative, permitted evaluation corpus and scoring protocol
   before changing chunking, retrieval, ranking, prompting, or model selection.

Phase 1 stops here. None of these business-logic or RAG changes has been implemented.
