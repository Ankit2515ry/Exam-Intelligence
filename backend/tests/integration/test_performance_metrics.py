import json
from unittest.mock import Mock

import pytest

from tests.support.corpus import make_chunk


pytestmark = pytest.mark.integration


@pytest.mark.parametrize("failure,category", [
    (TimeoutError("provider timeout"), "timeout"),
    (RuntimeError("quota exceeded"), "quota"),
    (RuntimeError("provider unavailable"), "provider"),
])
def test_provider_failure_returns_502_and_records_truthful_metric(
    failure, category, auth_client, user, document_factory, isolated_runtime,
    monkeypatch, tmp_path,
):
    from app.config import settings
    from app.rag import llm_service
    from app.rag.vectordb import store_chunks

    path = tmp_path / f"{category}.jsonl"
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_ENABLED", True)
    monkeypatch.setattr(settings, "PERFORMANCE_METRICS_PATH", str(path))
    monkeypatch.setattr(settings, "PERFORMANCE_PROVIDER_MODE", "mocked")
    document = document_factory(user.id)
    store_chunks([make_chunk(document.document_uuid, user.id)])
    provider = Mock()
    provider.generate_content.side_effect = failure
    monkeypatch.setattr(llm_service, "model", provider)

    response = auth_client.post("/api/chat", json={
        "question": "Explain normalization",
        "document_id": document.document_uuid,
    })

    assert response.status_code == 502
    assert response.json() == {"detail": "AI provider request failed"}
    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["success"] is False
    assert event["failure_category"] == category
    assert event["failure_stage"] == "gemini_api"
    assert event["durations_ms"]["gemini_api"] >= 0
    assert event["counts"]["final_source_chunks"] == 1
