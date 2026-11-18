import os
from pathlib import Path
import socket

import pytest


pytestmark = pytest.mark.unit


def test_test_runtime_cannot_use_production_stores(isolated_runtime):
    from app.config import settings
    from app.db import database
    from tests.conftest import ISOLATION_ROOT
    assert database.engine.dialect.name == "sqlite"
    assert Path(database.engine.url.database).is_relative_to(isolated_runtime.root)
    assert Path(settings.UPLOAD_DIR).is_relative_to(isolated_runtime.root)
    assert os.environ["GOOGLE_API_KEY"] == "test-key-no-network"
    assert Path(os.environ["VECTOR_DB_DIR"]).is_relative_to(ISOLATION_ROOT)
    assert isolated_runtime.collection.count() == 0
    with pytest.raises(RuntimeError, match="Network disabled"):
        socket.create_connection(("example.com", 443))
    with socket.socket() as sock:
        with pytest.raises(RuntimeError, match="Network disabled"):
            sock.connect(("127.0.0.1", 5432))
    with pytest.raises(RuntimeError, match="Network disabled"):
        socket.getaddrinfo("example.com", 443)


def test_password_hash_and_token_validation():
    from app.auth.hashing import hash_password, verify_password
    from app.auth.jwt_handler import create_access_token, verify_token
    from jose import jwt
    from app.auth import jwt_handler
    hashed = hash_password("study-pass")
    assert hashed != "study-pass"
    assert verify_password("study-pass", hashed)
    assert not verify_password("different", hashed)
    assert verify_token(create_access_token({"sub": "student@example.com"})) == "student@example.com"
    assert verify_token("invalid") is None
    expired = jwt.encode({"sub": "student@example.com", "exp": 0}, jwt_handler.SECRET_KEY, algorithm=jwt_handler.ALGORITHM)
    assert verify_token(expired) is None


def test_explicit_evaluation_environment_overrides_regular_dotenv(monkeypatch, tmp_path):
    from app.config.environment import load_application_environment

    evaluation_env = tmp_path / "evaluation.env"
    evaluation_env.write_text(
        "EXAM_INTELLIGENCE_EVALUATION_MODE=true\nDATABASE_URL=postgresql://evaluation-only\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://regular-only")
    monkeypatch.setenv("EVALUATION_ENV_FILE", str(evaluation_env))

    load_application_environment()

    assert os.environ["DATABASE_URL"] == "postgresql://evaluation-only"


def test_chunk_consistency_audit_is_read_only(auth_client, db, isolated_runtime, pdf_bytes):
    from app.db.models.chunk import Chunk
    from scripts.check_chunk_consistency import collect_consistency_report

    response = auth_client.post(
        "/api/upload",
        files={"file": ("study.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    before_sql = db.query(Chunk).count()
    before_vectors = isolated_runtime.collection.count()

    report = collect_consistency_report(db, isolated_runtime.collection)

    assert report["mode"] == "read-only"
    assert report["sql_chunk_count"] == before_sql
    assert report["vector_chunk_count"] == before_vectors
    assert report["matching_id_count"] == before_sql
    assert report["sql_ids_missing_from_chroma"] == []
    assert report["chroma_ids_missing_from_sql"] == []
    assert db.query(Chunk).count() == before_sql
    assert isolated_runtime.collection.count() == before_vectors


def test_evaluation_preflight_readiness_with_zero_one_and_multiple_documents(tmp_path):
    from sqlalchemy import create_engine, text
    from scripts.evaluation_preflight import collect_preflight_report

    db_path = tmp_path / "preflight_eval.sqlite"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    with engine.connect() as conn:
        conn.execute(text("create table users (id integer primary key, email text)"))
        conn.execute(text("create table documents (id integer primary key, uploaded_by integer)"))
        conn.execute(text("create table chunks (id integer primary key, document_id integer)"))
        conn.execute(text("insert into users (id, email) values (1, 'eval@test.invalid')"))
        conn.commit()

    regular_db_path = tmp_path / "preflight_reg.sqlite"
    regular_engine = create_engine(f"sqlite:///{regular_db_path.as_posix()}")
    with regular_engine.connect() as conn:
        conn.execute(text("create table users (id integer primary key, email text)"))
        conn.commit()

    reg_env = tmp_path / "regular.env"
    reg_env.write_text(f"DATABASE_URL=sqlite:///{regular_db_path.as_posix()}\n", encoding="utf-8")

    vector_dir = tmp_path / "private_chroma"
    vector_dir.mkdir()
    upload_dir = tmp_path / "private_uploads"
    upload_dir.mkdir()

    eval_env = tmp_path / "eval.env"
    eval_env.write_text(
        f"EXAM_INTELLIGENCE_EVALUATION_MODE=true\n"
        f"DATABASE_URL=sqlite:///{db_path.as_posix()}\n"
        f"VECTOR_DB_DIR={vector_dir.as_posix()}\n"
        f"UPLOAD_DIR={upload_dir.as_posix()}\n"
        f"EVALUATION_USER_EMAIL=eval@test.invalid\n"
        f"EVALUATION_USER_ID=1\n",
        encoding="utf-8",
    )

    expected_db = db_path.as_posix()
    report_zero = collect_preflight_report(
        evaluation_env=str(eval_env),
        mode="full",
        expected_database=expected_db,
        expected_vector_dir=str(vector_dir),
        expected_upload_dir=str(upload_dir),
        verify_regular_env=str(reg_env),
        backend_root=tmp_path,
        engine_override=engine,
        regular_engine_override=regular_engine,
    )
    assert report_zero["ready"] is True
    assert report_zero["evaluation_account"]["document_count"] == 0
    assert "evaluation_user_has_no_documents" not in report_zero["checks"]

    report_bootstrap_zero = collect_preflight_report(
        evaluation_env=str(eval_env),
        mode="bootstrap",
        expected_database=expected_db,
        expected_vector_dir=str(vector_dir),
        expected_upload_dir=str(upload_dir),
        verify_regular_env=str(reg_env),
        backend_root=tmp_path,
        engine_override=engine,
        regular_engine_override=regular_engine,
    )
    assert report_bootstrap_zero["ready"] is True
    assert report_bootstrap_zero["checks"]["evaluation_user_has_no_documents"] is True

    # Add 1 document
    with engine.connect() as conn:
        conn.execute(text("insert into documents (id, uploaded_by) values (101, 1)"))
        conn.commit()

    report_one = collect_preflight_report(
        evaluation_env=str(eval_env),
        mode="full",
        expected_database=expected_db,
        expected_vector_dir=str(vector_dir),
        expected_upload_dir=str(upload_dir),
        verify_regular_env=str(reg_env),
        backend_root=tmp_path,
        engine_override=engine,
        regular_engine_override=regular_engine,
    )
    assert report_one["ready"] is True
    assert report_one["evaluation_account"]["document_count"] == 1

    report_bootstrap_one = collect_preflight_report(
        evaluation_env=str(eval_env),
        mode="bootstrap",
        expected_database=expected_db,
        expected_vector_dir=str(vector_dir),
        expected_upload_dir=str(upload_dir),
        verify_regular_env=str(reg_env),
        backend_root=tmp_path,
        engine_override=engine,
        regular_engine_override=regular_engine,
    )
    assert report_bootstrap_one["ready"] is False
    assert report_bootstrap_one["checks"]["evaluation_user_has_no_documents"] is False

    # Add multiple documents
    with engine.connect() as conn:
        conn.execute(text("insert into documents (id, uploaded_by) values (102, 1), (103, 1)"))
        conn.commit()

    report_multi = collect_preflight_report(
        evaluation_env=str(eval_env),
        mode="full",
        expected_database=expected_db,
        expected_vector_dir=str(vector_dir),
        expected_upload_dir=str(upload_dir),
        verify_regular_env=str(reg_env),
        backend_root=tmp_path,
        engine_override=engine,
        regular_engine_override=regular_engine,
    )
    assert report_multi["ready"] is True
    assert report_multi["evaluation_account"]["document_count"] == 3

    # Reject incorrect database name
    report_bad_db = collect_preflight_report(
        evaluation_env=str(eval_env),
        mode="full",
        expected_database="wrong_database_name",
        expected_vector_dir=str(vector_dir),
        expected_upload_dir=str(upload_dir),
        verify_regular_env=str(reg_env),
        backend_root=tmp_path,
        engine_override=engine,
        regular_engine_override=regular_engine,
    )
    assert report_bad_db["ready"] is False
    assert report_bad_db["checks"]["database_name_matches"] is False

    # Reject default storage paths
    report_default_path = collect_preflight_report(
        evaluation_env=str(eval_env),
        mode="full",
        expected_database=expected_db,
        expected_vector_dir=str(vector_dir),
        expected_upload_dir=str(upload_dir),
        verify_regular_env=str(reg_env),
        backend_root=vector_dir.parent,  # causes vector_dir to be chroma_db if matching name
        engine_override=engine,
        regular_engine_override=regular_engine,
    )

    # Reject if evaluation user is present in regular database
    with regular_engine.connect() as conn:
        conn.execute(text("insert into users (id, email) values (99, 'eval@test.invalid')"))
        conn.commit()

    report_leaked = collect_preflight_report(
        evaluation_env=str(eval_env),
        mode="full",
        expected_database=expected_db,
        expected_vector_dir=str(vector_dir),
        expected_upload_dir=str(upload_dir),
        verify_regular_env=str(reg_env),
        backend_root=tmp_path,
        engine_override=engine,
        regular_engine_override=regular_engine,
    )
    assert report_leaked["ready"] is False
    assert report_leaked["checks"]["evaluation_user_absent_from_regular_database"] is False

