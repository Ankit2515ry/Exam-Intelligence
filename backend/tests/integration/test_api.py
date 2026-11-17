from pathlib import Path
from unittest.mock import Mock

import pytest

from tests.support.corpus import make_chunk


pytestmark = pytest.mark.integration


def test_root_and_health_routes_use_real_application(client):
    assert client.get("/").json()["status"] == "running"
    assert client.get("/health/live").json() == {"status": "alive"}
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok", "vector_store": "ok"}}


@pytest.mark.parametrize("method,path", [
    ("get", "/api/documents"), ("post", "/api/upload"),
    ("post", "/api/chat"), ("get", "/api/chunk/example"),
    ("get", "/api/view/example"), ("get", "/api/chunks/example"),
    ("delete", "/api/delete/example"),
])
def test_protected_endpoints_require_a_token(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_signup_login_and_bearer_authentication(client, db):
    from app.db.models.user import User
    signup = client.post("/auth/auth/signup", json={
        "name": "Student", "email": "Student@Example.com", "password": "study-pass",
    })
    assert signup.status_code == 200
    saved = db.query(User).one()
    assert saved.email == "student@example.com"
    assert saved.hashed_password != "study-pass"
    login = client.post("/auth/auth/login", data={"username": "STUDENT@example.com", "password": "study-pass"})
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/documents", headers=headers).status_code == 200


def test_duplicate_signup_and_invalid_login(client):
    data = {"name": "Student", "email": "student@example.com", "password": "study-pass"}
    assert client.post("/auth/auth/signup", json=data).status_code == 200
    assert client.post("/auth/auth/signup", json=data).status_code == 400
    assert client.post("/auth/auth/login", data={"username": data["email"], "password": "wrong"}).status_code == 401
    assert client.post("/auth/auth/login", data={"username": "missing@example.com", "password": "wrong"}).status_code == 401
    assert client.get("/api/documents", headers={"Authorization": "Bearer invalid"}).status_code == 401


@pytest.mark.parametrize("patch_data", [{"email": "invalid"}, {"password": "short"}])
def test_signup_validation(client, patch_data):
    data = {"name": "Student", "email": "student@example.com", "password": "study-pass"}
    data.update(patch_data)
    assert client.post("/auth/auth/signup", json=data).status_code == 422


def test_document_list_only_contains_owner_documents(auth_client, user, user_factory, document_factory):
    own = document_factory(user.id)
    other = document_factory(user_factory("other@example.com").id)
    response = auth_client.get("/api/documents")
    assert response.status_code == 200
    assert [doc["document_uuid"] for doc in response.json()] == [own.document_uuid]
    assert other.document_uuid not in response.text


@pytest.mark.parametrize("method,prefix", [("get", "view"), ("get", "chunks"), ("delete", "delete")])
def test_document_ownership_checks(auth_client, user_factory, document_factory, method, prefix):
    other = document_factory(user_factory("other@example.com").id)
    assert getattr(auth_client, method)(f"/api/{prefix}/{other.document_uuid}").status_code == 403
    assert getattr(auth_client, method)(f"/api/{prefix}/missing-document").status_code == 404


def test_upload_chat_sources_view_and_delete(auth_client, user, db, isolated_runtime, pdf_bytes):
    from app.db.models.document import Document
    from app.db.models.chunk import Chunk
    upload = auth_client.post("/api/upload", files={"file": ("study.pdf", pdf_bytes, "application/pdf")})
    assert upload.status_code == 200, upload.text
    data = upload.json()["document"]
    assert data["total_pages"] == 1
    assert data["total_chunks"] == isolated_runtime.collection.count() > 0
    assert db.query(Chunk).count() == data["total_chunks"]
    assert auth_client.get(f"/api/view/{data['document_uuid']}").content == pdf_bytes
    chunks = auth_client.get(f"/api/chunks/{data['document_uuid']}")
    assert len(chunks.json()["ids"]) == data["total_chunks"]
    first = chunks.json()["ids"][0]
    assert auth_client.get(f"/api/chunk/{first}").status_code == 200
    answer = auth_client.post("/api/chat", json={"question": "Explain normalization", "document_id": data["document_uuid"]})
    assert answer.status_code == 200, answer.text
    assert answer.json()["answer"] == "Mock answer for isolated tests."
    assert answer.json()["sources"]
    assert all(source["document_id"] == data["document_uuid"] for source in answer.json()["sources"])
    path = Path(db.get(Document, data["id"]).file_path)
    assert auth_client.delete(f"/api/delete/{data['document_uuid']}").status_code == 200
    assert db.query(Document).count() == db.query(Chunk).count() == isolated_runtime.collection.count() == 0
    assert not path.exists()


def test_upload_rejects_non_pdf_without_artifacts(auth_client, isolated_runtime, db):
    from tests.support.failures import ingestion_artifacts
    response = auth_client.post("/api/upload", files={"file": ("notes.txt", b"notes", "text/plain")})
    assert response.status_code == 400
    assert not any(ingestion_artifacts(db, isolated_runtime).values())


def test_chunk_ownership(auth_client, user, isolated_runtime):
    from app.rag.vectordb import store_chunks
    chunk = make_chunk(user_id=user.id + 1)
    store_chunks([chunk])
    assert auth_client.get(f"/api/chunk/{chunk['chunk_id']}").status_code == 403


def test_chat_request_response_contract(auth_client, user, document_factory, monkeypatch):
    from app.api import chat
    document = document_factory(user.id)
    calls = []

    def answer(**kwargs):
        calls.append(kwargs)
        return {"question": kwargs["question"], "answer": "mock", "sources": []}
    monkeypatch.setattr(chat, "chat_with_documents", answer)
    response = auth_client.post("/api/chat", json={
        "question": "Explain",
        "top_k": 2,
        "document_id": document.document_uuid,
    })
    assert response.json() == {"question": "Explain", "answer": "mock", "sources": []}
    assert calls == [{
        "question": "Explain",
        "user_id": user.id,
        "document_id": document.document_uuid,
    }]
    assert auth_client.post("/api/chat", json={}).status_code == 422


def test_chat_global_scope_passes_no_document_filter(auth_client, user, monkeypatch):
    from app.api import chat
    calls = []

    def answer(**kwargs):
        calls.append(kwargs)
        return {"question": kwargs["question"], "answer": "mock", "sources": []}

    monkeypatch.setattr(chat, "chat_with_documents", answer)
    response = auth_client.post("/api/chat", json={"question": "Explain"})
    assert response.status_code == 200
    assert calls == [{"question": "Explain", "user_id": user.id, "document_id": None}]


def test_chat_empty_owned_document_returns_no_context(
    auth_client,
    user,
    document_factory,
    isolated_runtime,
):
    from app.services.chat_service import NO_CONTEXT_ANSWER
    from app.rag import llm_service

    document = document_factory(user.id)
    response = auth_client.post("/api/chat", json={
        "question": "Question without indexed context",
        "document_id": document.document_uuid,
    })
    assert response.status_code == 200
    assert response.json() == {
        "question": "Question without indexed context",
        "answer": NO_CONTEXT_ANSWER,
        "sources": [],
    }
    assert llm_service.model.prompts == []


def test_chat_selected_document_requires_ownership(
    auth_client,
    user_factory,
    document_factory,
    monkeypatch,
):
    from app.api import chat
    other_user = user_factory("other-chat-owner@example.com")
    other_document = document_factory(other_user.id)
    service = Mock(side_effect=AssertionError("Unauthorized documents must not reach retrieval"))
    monkeypatch.setattr(chat, "chat_with_documents", service)

    forbidden = auth_client.post("/api/chat", json={
        "question": "Explain",
        "document_id": other_document.document_uuid,
    })
    assert forbidden.status_code == 403
    assert forbidden.json() == {"detail": "Access denied"}

    missing = auth_client.post("/api/chat", json={
        "question": "Explain",
        "document_id": "33333333-3333-4333-8333-333333333333",
    })
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Document not found"}
    service.assert_not_called()
