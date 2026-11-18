"""Credential-safe, read-only isolation preflight for evaluation environments."""

import argparse
import json
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def _resolved(value, backend_root, fallback):
    path = Path(value or fallback)
    return (path if path.is_absolute() else backend_root / path).resolve()


def _values(evaluation_env):
    if not evaluation_env:
        raise RuntimeError("--evaluation-env is required; regular .env fallback is forbidden")
    path = Path(evaluation_env).resolve()
    if not path.is_file():
        raise RuntimeError("Evaluation environment file does not exist")
    values = {key: value for key, value in dotenv_values(path).items() if value is not None}
    if values.get("EXAM_INTELLIGENCE_EVALUATION_MODE") != "true":
        raise RuntimeError("Evaluation environment marker is missing")
    return values, path


def collect_preflight_report(
    evaluation_env,
    mode="full",
    expected_database="exam_intelligence_evaluation",
    expected_vector_dir="evaluation/private/chroma-corpus-v1",
    expected_upload_dir="evaluation/private/uploads-corpus-v1",
    verify_regular_env=None,
    require_empty=False,
    backend_root=None,
    engine_override=None,
    regular_engine_override=None,
):
    if backend_root is None:
        backend_root = Path(__file__).resolve().parents[1]
    else:
        backend_root = Path(backend_root).resolve()

    values, environment_path = _values(evaluation_env)
    raw_database_url = values.get("DATABASE_URL")
    if not raw_database_url:
        raise RuntimeError("Evaluation DATABASE_URL is missing")
    database_url = make_url(raw_database_url)
    vector_path = _resolved(values.get("VECTOR_DB_DIR"), backend_root, "chroma_db")
    upload_path = _resolved(values.get("UPLOAD_DIR"), backend_root, "uploads")
    expected_vector = _resolved(expected_vector_dir, backend_root, expected_vector_dir)
    expected_upload = _resolved(expected_upload_dir, backend_root, expected_upload_dir)

    engine = engine_override or create_engine(raw_database_url)
    evaluation_user_email = values.get("EVALUATION_USER_EMAIL")
    evaluation_user_id = values.get("EVALUATION_USER_ID")
    try:
        with engine.connect() as connection:
            if engine.dialect.name == "sqlite":
                current_database = database_url.database
                users_table_exists = connection.execute(
                    text("select 1 from sqlite_master where type='table' and name='users'")
                ).scalar() is not None
                documents_table_exists = connection.execute(
                    text("select 1 from sqlite_master where type='table' and name='documents'")
                ).scalar() is not None
                chunks_table_exists = connection.execute(
                    text("select 1 from sqlite_master where type='table' and name='chunks'")
                ).scalar() is not None
            else:
                current_database = connection.execute(text("select current_database()")).scalar_one()
                users_table_exists = connection.execute(
                    text("select to_regclass('public.users') is not null")
                ).scalar_one()
                documents_table_exists = connection.execute(
                    text("select to_regclass('public.documents') is not null")
                ).scalar_one()
                chunks_table_exists = connection.execute(
                    text("select to_regclass('public.chunks') is not null")
                ).scalar_one()

            evaluation_user_exists = False
            evaluation_user_document_count = None
            if users_table_exists and evaluation_user_email:
                evaluation_user_exists = connection.execute(
                    text("select exists(select 1 from users where email=:email)"),
                    {"email": evaluation_user_email},
                ).scalar_one()
                if evaluation_user_exists and documents_table_exists:
                    evaluation_user_document_count = connection.execute(
                        text("select count(*) from documents where uploaded_by=(select id from users where email=:email)"),
                        {"email": evaluation_user_email},
                    ).scalar_one()
            elif users_table_exists and evaluation_user_id:
                evaluation_user_exists = connection.execute(
                    text("select exists(select 1 from users where id=:user_id)"),
                    {"user_id": int(evaluation_user_id)},
                ).scalar_one()
                if evaluation_user_exists and documents_table_exists:
                    evaluation_user_document_count = connection.execute(
                        text("select count(*) from documents where uploaded_by=:user_id"),
                        {"user_id": int(evaluation_user_id)},
                    ).scalar_one()
    finally:
        if engine_override is None:
            engine.dispose()

    account_absent_from_regular_database = None
    regular_database = None
    if verify_regular_env:
        regular_values = dotenv_values(Path(verify_regular_env).resolve())
        regular_url = regular_values.get("DATABASE_URL")
        if not regular_url:
            raise RuntimeError("Regular environment DATABASE_URL is missing")
        regular_engine = regular_engine_override or create_engine(regular_url)
        try:
            with regular_engine.connect() as connection:
                if regular_engine.dialect.name == "sqlite":
                    regular_database = make_url(regular_url).database
                    users_table = connection.execute(
                        text("select 1 from sqlite_master where type='table' and name='users'")
                    ).scalar() is not None
                else:
                    regular_database = connection.execute(text("select current_database()")).scalar_one()
                    users_table = connection.execute(
                        text("select to_regclass('public.users') is not null")
                    ).scalar_one()

                if users_table and evaluation_user_email:
                    account_absent_from_regular_database = not connection.execute(
                        text("select exists(select 1 from users where email=:email)"),
                        {"email": evaluation_user_email},
                    ).scalar_one()
                else:
                    account_absent_from_regular_database = True
        finally:
            if regular_engine_override is None:
                regular_engine.dispose()

    checks = {
        "evaluation_marker": values.get("EXAM_INTELLIGENCE_EVALUATION_MODE") == "true",
        "database_name_matches": database_url.database == expected_database,
        "connected_database_matches": current_database == expected_database,
        "vector_path_matches": vector_path == expected_vector,
        "upload_path_matches": upload_path == expected_upload,
        "vector_differs_from_default": vector_path != (backend_root / "chroma_db").resolve(),
        "upload_differs_from_default": upload_path != (backend_root / "uploads").resolve(),
        "evaluation_env_explicit": bool(environment_path),
    }

    if mode in ("bootstrap", "full"):
        checks.update({
            "schema_initialized": bool(users_table_exists and documents_table_exists and chunks_table_exists),
            "evaluation_user_target_configured": bool(evaluation_user_id or evaluation_user_email),
            "evaluation_user_exists_in_connected_database": bool(evaluation_user_exists),
        })
        if mode == "bootstrap" or require_empty:
            checks["evaluation_user_has_no_documents"] = (evaluation_user_document_count == 0)
        if verify_regular_env:
            checks["evaluation_user_absent_from_regular_database"] = bool(account_absent_from_regular_database)

    return {
        "mode": mode,
        "current": {
            "database_scheme": database_url.get_backend_name(),
            "database_host": database_url.host,
            "database_port": database_url.port,
            "configured_database": database_url.database,
            "connected_database": current_database,
            "vector_path": str(vector_path),
            "upload_path": str(upload_path),
            "evaluation_environment_file": str(environment_path),
            "credentials": "redacted",
        },
        "regular_database_account_check": {
            "database": regular_database,
            "evaluation_account_absent": account_absent_from_regular_database,
        } if verify_regular_env else None,
        "evaluation_account": {
            "document_count": evaluation_user_document_count,
        } if mode in ("bootstrap", "full") else None,
        "checks": checks,
        "ready": all(checks.values()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-env", required=True)
    parser.add_argument("--mode", choices=("infrastructure", "bootstrap", "full"), default="full")
    parser.add_argument("--expected-database", default="exam_intelligence_evaluation")
    parser.add_argument("--expected-vector-dir", default="evaluation/private/chroma-corpus-v1")
    parser.add_argument("--expected-upload-dir", default="evaluation/private/uploads-corpus-v1")
    parser.add_argument("--verify-regular-env")
    parser.add_argument("--require-empty", action="store_true", help="Require evaluation user to own zero documents")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    report = collect_preflight_report(
        evaluation_env=args.evaluation_env,
        mode=args.mode,
        expected_database=args.expected_database,
        expected_vector_dir=args.expected_vector_dir,
        expected_upload_dir=args.expected_upload_dir,
        verify_regular_env=args.verify_regular_env,
        require_empty=args.require_empty,
    )
    print(json.dumps(report, indent=2))
    if args.require_ready and not report["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
