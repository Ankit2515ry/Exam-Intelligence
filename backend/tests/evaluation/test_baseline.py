from statistics import mean

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
    assert matches == 0


@pytest.mark.parametrize("stage", INGESTION_STAGES)
def test_ingestion_failure_artifact_baseline(stage, auth_client, db, isolated_runtime, monkeypatch, pdf_bytes, record_baseline):
    inject_ingestion_failure(monkeypatch, stage)
    response = auth_client.post("/api/upload", files={"file": ("synthetic.pdf", pdf_bytes, "application/pdf")})
    artifacts = ingestion_artifacts(db, isolated_runtime)
    record_baseline(f"ingestion_failure_{stage}", {"http_status": response.status_code, **artifacts})
    assert response.status_code == 500
    assert artifacts["documents"] == artifacts["pdf_files"] == 1
    assert artifacts["sql_chunks"] == (1 if stage == "sql_second" else 0)
    if stage in ("parse", "embedding"):
        assert artifacts["vector_chunks"] == 0
    else:
        assert artifacts["vector_chunks"] > 0
