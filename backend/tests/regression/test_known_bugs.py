from pathlib import Path
from unittest.mock import Mock

import pytest

from tests.support.corpus import DOCUMENT_A, make_chunk, scope_corpus
from tests.support.failures import INGESTION_STAGES, inject_ingestion_failure, ingestion_artifacts


pytestmark = pytest.mark.regression


def test_document_specific_search_excludes_other_documents(isolated_runtime):
    from app.rag.vectordb import search_chunks, store_chunks
    store_chunks(scope_corpus() + [make_chunk(DOCUMENT_A, user_id=8, index=1)])
    result = search_chunks("normalization", user_id=7, top_k=5, document_id=DOCUMENT_A)
    metadata = result["metadatas"][0]
    assert metadata, "Fixture must return candidates"
    assert all(item["user_id"] == 7 for item in metadata)
    assert all(item["document_id"] == DOCUMENT_A for item in metadata)
    assert len(metadata) == 2


def test_global_search_includes_all_owner_documents_only(isolated_runtime):
    from app.rag.vectordb import search_chunks, store_chunks
    from tests.support.corpus import DOCUMENT_B

    store_chunks(scope_corpus())
    result = search_chunks("normalization", user_id=7, top_k=5)
    metadata = result["metadatas"][0]
    assert len(metadata) == 4
    assert all(item["user_id"] == 7 for item in metadata)
    assert {item["document_id"] for item in metadata} == {DOCUMENT_A, DOCUMENT_B}


def test_numeric_document_id_is_rejected_at_uuid_contract(auth_client, user, document_factory, monkeypatch):
    from app.api import chat
    document = document_factory(user.id)
    assert str(document.id) != document.document_uuid
    calls = []

    def answer(**kwargs):
        calls.append(kwargs)
        return {"question": kwargs["question"], "answer": "mock", "sources": []}
    monkeypatch.setattr(chat, "chat_with_documents", answer)
    # Protects the UUID boundary from the former Chat.jsx numeric payload.
    response = auth_client.post("/api/chat", json={"question": "Explain normalization", "document_id": str(document.id)})
    assert response.status_code == 422
    assert calls == []


def test_empty_retrieval_returns_a_response_without_crashing(monkeypatch):
    from app.services import chat_service
    prompt = Mock(side_effect=AssertionError("Prompt must not be built without context"))
    generate = Mock(side_effect=AssertionError("LLM must not be called without context"))
    monkeypatch.setattr(chat_service, "build_prompt", prompt)
    monkeypatch.setattr(chat_service, "generate_answer", generate)
    result = chat_service.chat_with_documents("Question without uploaded documents", user_id=7)
    assert result == {
        "question": "Question without uploaded documents",
        "answer": chat_service.NO_CONTEXT_ANSWER,
        "sources": [],
    }
    assert result["sources"] == []
    prompt.assert_not_called()
    generate.assert_not_called()


def test_missing_chunk_lookup_returns_empty_results():
    from app.rag.vectordb import get_chunk_by_id
    assert get_chunk_by_id("missing-chunk")["ids"] == []


def test_missing_chunk_api_returns_404(auth_client):
    response = auth_client.get("/api/chunk/missing-chunk")
    assert response.status_code == 404
    assert response.json() == {"detail": "Chunk not found"}


def test_sql_chunk_ids_match_chroma_ids(auth_client, db, isolated_runtime, pdf_bytes):
    from app.db.models.chunk import Chunk
    response = auth_client.post("/api/upload", files={"file": ("study.pdf", pdf_bytes, "application/pdf")})
    assert response.status_code == 200, response.text
    sql_ids = {row.chroma_id for row in db.query(Chunk).all()}
    vector_ids = set(isolated_runtime.collection.get()["ids"])
    assert sql_ids and len(sql_ids) == len(vector_ids)
    assert sql_ids == vector_ids


@pytest.mark.parametrize("stage", INGESTION_STAGES)
def test_failed_ingestion_removes_all_created_artifacts(stage, auth_client, db, isolated_runtime, monkeypatch, pdf_bytes):
    inject_ingestion_failure(monkeypatch, stage)
    response = auth_client.post("/api/upload", files={"file": ("study.pdf", pdf_bytes, "application/pdf")})
    assert response.status_code == 500, response.text
    artifacts = ingestion_artifacts(db, isolated_runtime)
    assert not any(artifacts.values()), f"Artifacts after {stage} failure: {artifacts}"


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
    assert len(set(states)) == 1, f"SQL, file, vector existence after cleanup: {states}"


def test_delete_vector_failure_restores_file_database_and_vectors(
    auth_client, user, db, document_factory, isolated_runtime, monkeypatch
):
    from app.api import upload
    from app.db.models.document import Document
    from app.rag.vectordb import store_chunks

    document = document_factory(user.id)
    document_id = document.id
    path = Path(document.file_path)
    store_chunks([make_chunk(document.document_uuid, user.id)])
    delete_vectors = upload.delete_document_chunks

    def accepted_then_failed(document_uuid):
        delete_vectors(document_uuid)
        raise RuntimeError("vector delete acknowledgement")

    monkeypatch.setattr(upload, "delete_document_chunks", accepted_then_failed)

    response = auth_client.delete(f"/api/delete/{document.document_uuid}")
    assert response.status_code == 500
    db.expire_all()
    assert db.get(Document, document_id) is not None
    assert path.exists()
    assert isolated_runtime.collection.count() == 1


def test_successful_delete_is_safe_to_retry(auth_client, user, document_factory, isolated_runtime):
    from app.rag.vectordb import store_chunks

    document = document_factory(user.id)
    store_chunks([make_chunk(document.document_uuid, user.id)])
    assert auth_client.delete(f"/api/delete/{document.document_uuid}").status_code == 200
    assert auth_client.delete(f"/api/delete/{document.document_uuid}").status_code == 404
    assert isolated_runtime.collection.count() == 0


def test_post_commit_filesystem_failure_is_reported_for_manual_recovery(
    auth_client, user, db, document_factory, isolated_runtime, monkeypatch
):
    from app.db.models.document import Document
    from app.rag.vectordb import store_chunks

    document = document_factory(user.id)
    document_uuid = document.document_uuid
    document_id = document.id
    original_unlink = Path.unlink
    store_chunks([make_chunk(document_uuid, user.id)])

    def fail_staged_unlink(path, *args, **kwargs):
        if path.parent.name == f".{document_uuid}.deleting":
            raise OSError("synthetic locked file")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_staged_unlink)
    response = auth_client.delete(f"/api/delete/{document_uuid}")
    assert response.status_code == 500
    assert "recovery procedure" in response.json()["detail"]
    db.expire_all()
    assert db.get(Document, document_id) is None
    assert isolated_runtime.collection.count() == 0
    assert (isolated_runtime.root / "uploads" / f".{document_uuid}.deleting").exists()
    assert auth_client.delete(f"/api/delete/{document_uuid}").status_code == 404
