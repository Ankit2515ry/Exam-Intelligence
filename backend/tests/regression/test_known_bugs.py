from pathlib import Path

import pytest

from tests.support.corpus import DOCUMENT_A, scope_corpus
from tests.support.failures import INGESTION_STAGES, inject_ingestion_failure, ingestion_artifacts
from tests.support.known_bugs import KnownDefect, expect


pytestmark = pytest.mark.regression


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="BUG-01: vector search ignores document_id")
def test_document_specific_search_excludes_other_documents(isolated_runtime):
    from app.rag.vectordb import search_chunks, store_chunks
    store_chunks(scope_corpus())
    result = search_chunks("normalization", user_id=7, top_k=5, document_id=DOCUMENT_A)
    metadata = result["metadatas"][0]
    assert metadata, "Fixture must return candidates"
    assert all(item["user_id"] == 7 for item in metadata)
    expect(all(item["document_id"] == DOCUMENT_A for item in metadata),
           f"Other documents returned: {[item['document_id'] for item in metadata]}")


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="BUG-02: numeric UI selection is accepted at UUID boundary")
def test_numeric_document_id_is_rejected_at_uuid_contract(auth_client, user, document_factory, monkeypatch):
    from app.api import chat
    document = document_factory(user.id)
    assert str(document.id) != document.document_uuid
    calls = []

    def answer(**kwargs):
        calls.append(kwargs)
        return {"question": kwargs["question"], "answer": "mock", "sources": []}
    monkeypatch.setattr(chat, "chat_with_documents", answer)
    # Replays the current Chat.jsx option value (SQL id), without claiming a browser test.
    response = auth_client.post("/api/chat", json={"question": "Explain normalization", "document_id": str(document.id)})
    expect(response.status_code == 422,
           f"UUID contract accepted numeric id: HTTP {response.status_code}, service calls={calls}")


@pytest.mark.xfail(strict=True, raises=UnboundLocalError, reason="BUG-03: no prompt exists when retrieval is empty")
def test_empty_retrieval_returns_a_response_without_crashing():
    from app.services.chat_service import chat_with_documents
    result = chat_with_documents("Question without uploaded documents", user_id=7)
    assert result["sources"] == []


@pytest.mark.xfail(strict=True, raises=IndexError, reason="BUG-04: missing metadata indexed before empty check")
def test_missing_chunk_lookup_returns_empty_results():
    from app.rag.vectordb import get_chunk_by_id
    assert get_chunk_by_id("missing-chunk")["ids"] == []


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="BUG-04: missing chunk API returns 500 instead of 404")
def test_missing_chunk_api_returns_404(auth_client):
    response = auth_client.get("/api/chunk/missing-chunk")
    expect(response.status_code == 404, f"Missing chunk returned HTTP {response.status_code}")


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="BUG-05: SQL chroma_id is generated independently")
def test_sql_chunk_ids_match_chroma_ids(auth_client, db, isolated_runtime, pdf_bytes):
    from app.db.models.chunk import Chunk
    response = auth_client.post("/api/upload", files={"file": ("study.pdf", pdf_bytes, "application/pdf")})
    assert response.status_code == 200, response.text
    sql_ids = {row.chroma_id for row in db.query(Chunk).all()}
    vector_ids = set(isolated_runtime.collection.get()["ids"])
    assert sql_ids and len(sql_ids) == len(vector_ids)
    expect(sql_ids == vector_ids, "No reliable SQL-to-Chroma chunk reference is stored")


@pytest.mark.parametrize("stage", INGESTION_STAGES)
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="BUG-06: failed ingestion leaves durable artifacts")
def test_failed_ingestion_removes_all_created_artifacts(stage, auth_client, db, isolated_runtime, monkeypatch, pdf_bytes):
    inject_ingestion_failure(monkeypatch, stage)
    response = auth_client.post("/api/upload", files={"file": ("study.pdf", pdf_bytes, "application/pdf")})
    assert response.status_code == 500, response.text
    artifacts = ingestion_artifacts(db, isolated_runtime)
    expect(not any(artifacts.values()), f"Artifacts after {stage} failure: {artifacts}")


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="BUG-06D: directory cleanup failure leaves partial deletion")
def test_cleanup_failure_preserves_consistent_document_state(auth_client, user, db, document_factory, isolated_runtime):
    from app.db.models.document import Document
    from app.rag.vectordb import store_chunks
    from tests.support.corpus import make_chunk
    document = document_factory(user.id)
    document_id = document.id
    path = Path(document.file_path)
    (path.parent / "extra.txt").write_text("synthetic cleanup obstacle", encoding="utf-8")
    store_chunks([make_chunk(document.document_uuid, user.id)])
    response = auth_client.delete(f"/api/delete/{document.document_uuid}")
    assert response.status_code in (200, 500)
    # The route uses another session; query fresh state rather than our identity map.
    db.expire_all()
    states = [db.get(Document, document_id) is not None, path.exists(), isolated_runtime.collection.count() > 0]
    expect(len(set(states)) == 1, f"SQL, file, vector existence after cleanup: {states}")
