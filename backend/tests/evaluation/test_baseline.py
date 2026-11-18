from statistics import mean
import json
import platform
import subprocess
import sys
from langchain_core.documents import Document

import pytest

from tests.support.corpus import DOCUMENT_A, DOCUMENT_B, make_chunk, scope_corpus
from tests.support.failures import INGESTION_STAGES, inject_ingestion_failure, ingestion_artifacts


pytestmark = pytest.mark.evaluation


def test_document_scope_baseline(isolated_runtime, record_baseline):
    from app.rag.vectordb import search_chunks, store_chunks
    corpus = scope_corpus()
    store_chunks(corpus)
    results = search_chunks("normalization", user_id=7, top_k=5, document_id=DOCUMENT_A)
    metadata = results["metadatas"][0]
    matching = sum(item["document_id"] == DOCUMENT_A for item in metadata)
    other_user = sum(item["user_id"] != 7 for item in metadata)
    report = {
        "corpus_chunks": len(corpus), "owner_chunks": 4, "requested_document_chunks": 2,
        "requested_k": 5, "returned_chunks": len(metadata),
        "requested_document_matches": matching,
        "document_scope_precision": matching / len(metadata),
        "other_document_fraction": (len(metadata) - matching) / len(metadata),
        "other_user_fraction": other_user / len(metadata),
        "scope": "Document membership only; no semantic relevance labels or real embeddings",
    }
    record_baseline("document_scope", report)
    assert len(metadata) == 2 and matching == 2 and other_user == 0


def test_pipeline_candidate_and_generation_counts(isolated_runtime, monkeypatch, record_baseline):
    from app.rag import vectordb, retriever, llm_service
    from app.services import chat_service
    vectordb.store_chunks([make_chunk(DOCUMENT_A, 7, index) for index in range(10)] +
                         [make_chunk(DOCUMENT_B, 8, index) for index in range(2)])
    counts = {"corpus_chunks": 12, "owner_chunks": 10, "prompt_build_calls": 0}
    search = retriever.search_chunks
    keywords = retriever.bm25_search
    combine = retriever.combine_scores
    rerank = chat_service.rerank
    prompt = chat_service.build_prompt

    def observe_search(**kwargs):
        result = search(**kwargs)
        counts["requested_vector_k"] = kwargs["top_k"]
        counts["vector_candidates"] = len(result["ids"][0])
        return result

    def observe_keywords(**kwargs):
        result = keywords(**kwargs)
        counts["bm25_survivors"] = len(result)
        return result

    def observe_combine(chunks):
        result = combine(chunks)
        counts["hybrid_survivors"] = len(result)
        return result

    def observe_rerank(**kwargs):
        counts["cross_encoder_candidates"] = len(kwargs["chunks"])
        return rerank(**kwargs)

    def observe_prompt(**kwargs):
        counts["prompt_build_calls"] += 1
        counts["context_chunks"] = len(kwargs["retrieved_chunks"])
        counts["context_characters"] = len("\n\n".join(chunk.page_content for chunk in kwargs["retrieved_chunks"]))
        return prompt(**kwargs)

    monkeypatch.setattr(retriever, "search_chunks", observe_search)
    monkeypatch.setattr(retriever, "bm25_search", observe_keywords)
    monkeypatch.setattr(retriever, "combine_scores", observe_combine)
    monkeypatch.setattr(chat_service, "rerank", observe_rerank)
    monkeypatch.setattr(chat_service, "build_prompt", observe_prompt)
    result = chat_service.chat_with_documents("normalization", user_id=7)
    counts["returned_sources"] = len(result["sources"])
    counts["llm_calls"] = len(llm_service.model.prompts)
    record_baseline("pipeline_counts", counts)
    assert counts["vector_candidates"] == 10
    assert counts["bm25_survivors"] == counts["hybrid_survivors"] == counts["cross_encoder_candidates"] == 5
    assert counts["context_chunks"] == counts["returned_sources"] == 5
    assert counts["prompt_build_calls"] == 1
    assert counts["llm_calls"] == 1


def test_generated_pdf_ingestion_baseline(auth_client, db, isolated_runtime, pdf_bytes, record_baseline):
    from app.db.models.chunk import Chunk
    response = auth_client.post("/api/upload", files={"file": ("synthetic.pdf", pdf_bytes, "application/pdf")})
    assert response.status_code == 200, response.text
    document = response.json()["document"]
    rows = db.query(Chunk).all()
    vector_ids = set(isolated_runtime.collection.get()["ids"])
    matches = sum(row.chroma_id in vector_ids for row in rows)
    lengths = [len(row.content) for row in rows]
    record_baseline("generated_pdf", {
        "pdf_bytes": len(pdf_bytes), "retained_text_pages": document["total_pages"],
        "sql_chunks": len(rows), "vector_chunks": len(vector_ids),
        "chunk_characters_min": min(lengths), "chunk_characters_max": max(lengths),
        "chunk_characters_mean": mean(lengths),
        "sql_chroma_id_matches": matches, "sql_chroma_id_match_fraction": matches / len(rows),
        "scope": "Generated one-page text PDF, real parser/splitter/CRUD/Chroma, mocked embedding model",
    })
    assert len(rows) == len(vector_ids) > 0
    assert matches == len(rows)


@pytest.mark.parametrize("stage", INGESTION_STAGES)
def test_ingestion_failure_artifact_baseline(stage, auth_client, db, isolated_runtime, monkeypatch, pdf_bytes, record_baseline):
    inject_ingestion_failure(monkeypatch, stage)
    response = auth_client.post("/api/upload", files={"file": ("synthetic.pdf", pdf_bytes, "application/pdf")})
    artifacts = ingestion_artifacts(db, isolated_runtime)
    record_baseline(f"ingestion_failure_{stage}", {"http_status": response.status_code, **artifacts})
    assert response.status_code == 500
    assert not any(artifacts.values())


def test_synthetic_instrumentation_baseline(
    auth_client, user, isolated_runtime, pdf_bytes, monkeypatch, tmp_path, record_baseline
):
    from app.config import settings

    metrics_path = tmp_path / "synthetic-performance.jsonl"
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False,
    ).stdout.strip() or None
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_ENABLED", True)
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_PATH", str(metrics_path))
    monkeypatch.setattr(settings, "PERFORMANCE_PROVIDER_MODE", "mocked")
    monkeypatch.setattr(settings, "PERFORMANCE_MEASUREMENT_CLASS", "synthetic")
    monkeypatch.setattr(settings, "PERFORMANCE_RUN_TEMPERATURE", "warm")
    if revision:
        monkeypatch.setenv("GIT_COMMIT_SHA", revision)

    upload = auth_client.post(
        "/api/upload", files={"file": ("synthetic.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_uuid = upload.json()["document"]["document_uuid"]
    chat = auth_client.post("/api/chat", json={
        "question": "Explain normalization", "document_id": document_uuid,
    })
    assert chat.status_code == 200

    events = [json.loads(line) for line in metrics_path.read_text(encoding="utf-8").splitlines()]
    assert [event["operation"] for event in events] == ["ingestion", "chat"]
    assert all(event["success"] is True for event in events)
    assert all(event["provider_mode"] == "mocked" for event in events)
    assert all(event["total_duration_ms"] > 0 for event in events)
    record_baseline("performance_synthetic", {
        "scope": "Deterministic isolated test environment; mocked embedding, reranker, and Gemini providers",
        "operating_system": platform.platform(),
        "python": sys.version.split()[0],
        "code_revision": revision,
        "sample_count": len(events),
        "fixture_pdf_bytes": len(pdf_bytes),
        "events": [{
            "operation": event["operation"],
            "total_duration_ms": event["total_duration_ms"],
            "durations_ms": event["durations_ms"],
            "counts": event["counts"],
            "success": event["success"],
            "provider_mode": event["provider_mode"],
            "measurement_class": event["measurement_class"],
            "run_temperature": event["run_temperature"],
        } for event in events],
        "error_count": 0,
    })


def test_synthetic_rag_quality_framework_baseline(record_baseline):
    from app.evaluation.runner import run_evaluation

    def make_record(question_id, document_id, page, answerable=True):
        return {
            "question_id": question_id,
            "question": f"Synthetic framework question {question_id} with unique evidence token",
            "document_scope_uuid": document_id,
            "expected_answer": "Synthetic reference" if answerable else None,
            "answerable": answerable,
            "relevant_document_ids": [document_id] if answerable else [],
            "relevant_page_numbers": [page] if answerable else [],
            "supporting_spans": [{"document_id": document_id, "page": page, "text": f"evidence {question_id}"}] if answerable else [],
            "category": "direct_factual" if answerable else "unanswerable",
            "ocr_scanned": False,
            "mathematical": False,
            "reviewer_status": "approved",
            "reviewer_notes": "Synthetic framework test only",
        }

    records = [
        make_record("synthetic-alpha-19f4", "doc-a", 1),
        make_record("synthetic-beta-83d2", "doc-b", 2),
        make_record("synthetic-unanswerable-5ac7", "doc-c", 1, answerable=False),
    ]

    def retrieve(question, user_id, top_k, document_id):
        question_id = next(record["question_id"] for record in records if record["question"] == question)
        if "unanswerable" in question_id:
            return []
        record = next(record for record in records if record["question_id"] == question_id)
        return [Document(
            page_content=f"evidence {question_id}",
            metadata={"chunk_id": f"chunk-{question_id}", "document_id": record["document_scope_uuid"], "page": record["relevant_page_numbers"][0], "user_id": user_id},
        )]

    chunks = {}
    for record in records[:2]:
        chunks[f"chunk-{record['question_id']}"] = {"metadata": {
            "document_id": record["document_scope_uuid"],
            "page": record["relevant_page_numbers"][0],
            "user_id": 7,
        }}
    run = run_evaluation(
        records, split_name="synthetic", dataset_version="synthetic-framework-v1",
        corpus_hash="synthetic-corpus", user_id=7, retrieve_fn=retrieve,
        rerank_fn=lambda **kwargs: kwargs["chunks"], lookup_fn=chunks.get,
    )
    record_baseline("rag_quality_synthetic", {
        "scope": "Framework verification only; deterministic synthetic labels and retrieval, no real model accuracy",
        "sample_count": run["sample_count"],
        "retrieval_metrics": run["retrieval_metrics"],
        "answer_quality": run["answer_quality"],
        "abstention": run["abstention"],
        "errors": len(run["errors"]),
    })
    assert run["retrieval_metrics"] == {
        "eligible_questions": 2,
        "excluded_no_relevance_labels": 1,
        "hit_at_5": 1.0,
        "precision_at_5": 0.2,
        "recall_at_5": 1.0,
        "mrr_at_10": 1.0,
        "ndcg_at_5": 1.0,
    }
    assert run["answer_quality"]["factual_correctness"]["mean"] is None
    assert run["abstention"]["eligible"] == 0
