"""Read-only, credential-safe evaluation isolation preflight."""

import argparse
import json
import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def _effective(name, dotenv):
    return os.environ.get(name) or dotenv.get(name)


def _resolved(value, backend_root, fallback):
    path = Path(value or fallback)
    return (path if path.is_absolute() else backend_root / path).resolve()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-database", default="exam_intelligence_evaluation")
    parser.add_argument("--expected-vector-dir", default="evaluation/private/chroma-corpus-v1")
    parser.add_argument("--expected-upload-dir", default="evaluation/private/uploads-corpus-v1")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[1]
    dotenv = dotenv_values(backend_root / ".env")
    raw_database_url = _effective("DATABASE_URL", dotenv)
    if not raw_database_url:
        raise SystemExit("DATABASE_URL is not configured")
    database_url = make_url(raw_database_url)
    vector_path = _resolved(_effective("VECTOR_DB_DIR", dotenv), backend_root, "chroma_db")
    upload_path = _resolved(_effective("UPLOAD_DIR", dotenv), backend_root, "uploads")
    expected_vector = _resolved(args.expected_vector_dir, backend_root, args.expected_vector_dir)
    expected_upload = _resolved(args.expected_upload_dir, backend_root, args.expected_upload_dir)

    engine = create_engine(raw_database_url)
    evaluation_user_email = _effective("EVALUATION_USER_EMAIL", dotenv)
    evaluation_user_id = _effective("EVALUATION_USER_ID", dotenv)
    try:
        with engine.connect() as connection:
            current_database = connection.execute(text("select current_database()" )).scalar_one()
            evaluation_exists = connection.execute(
                text("select exists(select 1 from pg_database where datname=:name)"),
                {"name": args.expected_database},
            ).scalar_one()
            users_table_exists = connection.execute(
                text("select to_regclass('public.users') is not null")
            ).scalar_one()
            evaluation_user_exists = False
            if users_table_exists and evaluation_user_email:
                evaluation_user_exists = connection.execute(
                    text("select exists(select 1 from users where email=:email)"),
                    {"email": evaluation_user_email},
                ).scalar_one()
            elif users_table_exists and evaluation_user_id:
                evaluation_user_exists = connection.execute(
                    text("select exists(select 1 from users where id=:user_id)"),
                    {"user_id": int(evaluation_user_id)},
                ).scalar_one()
    finally:
        engine.dispose()

    checks = {
        "database_name_matches": database_url.database == args.expected_database,
        "connected_database_matches": current_database == args.expected_database,
        "vector_path_matches": vector_path == expected_vector,
        "upload_path_matches": upload_path == expected_upload,
        "vector_differs_from_default": vector_path != (backend_root / "chroma_db").resolve(),
        "upload_differs_from_default": upload_path != (backend_root / "uploads").resolve(),
        "evaluation_user_target_configured": bool(evaluation_user_id or evaluation_user_email),
        "evaluation_user_exists_in_connected_database": bool(evaluation_user_exists),
    }
    report = {
        "current": {
            "database_scheme": database_url.get_backend_name(),
            "database_host": database_url.host,
            "database_port": database_url.port,
            "configured_database": database_url.database,
            "connected_database": current_database,
            "vector_path": str(vector_path),
            "upload_path": str(upload_path),
            "credentials": "redacted",
        },
        "proposed": {
            "database": args.expected_database,
            "database_already_exists": bool(evaluation_exists),
            "vector_path": str(expected_vector),
            "upload_path": str(expected_upload),
        },
        "checks": checks,
        "ready_for_indexing": all(checks.values()),
    }
    print(json.dumps(report, indent=2))
    if args.require_ready and not report["ready_for_indexing"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
