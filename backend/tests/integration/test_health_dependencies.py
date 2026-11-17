import pytest


pytestmark = pytest.mark.integration


@pytest.mark.parametrize("database_down,vector_down", [(True, False), (False, True), (True, True)])
def test_readiness_checks_both_dependencies_and_recovers(client, monkeypatch, database_down, vector_down):
    from app.api import health
    calls = []

    def check(name, down):
        calls.append(name)
        if down:
            raise RuntimeError(f"synthetic {name} failure")
    with monkeypatch.context() as context:
        context.setattr(health, "_check_database", lambda: check("database", database_down))
        context.setattr(health, "_check_vector_store", lambda: check("vector_store", vector_down))
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert calls == ["database", "vector_store"]
    assert response.json()["checks"] == {
        "database": "unavailable" if database_down else "ok",
        "vector_store": "unavailable" if vector_down else "ok",
    }
    assert client.get("/health/ready").status_code == 200
