from pathlib import Path
from unittest.mock import ANY, Mock

import fitz
import pytest

from tests.support.failures import ingestion_artifacts


pytestmark = pytest.mark.integration


def assert_no_upload_artifacts(db, isolated_runtime):
    assert not any(ingestion_artifacts(db, isolated_runtime).values())
    assert list((isolated_runtime.root / "uploads").rglob("*")) == []


def test_valid_pdf_uses_generated_storage_path_and_preserves_display_name(
    auth_client,
    db,
    isolated_runtime,
    monkeypatch,
    pdf_bytes,
):
    from app.api import upload
    from app.db.models.document import Document

    ingest = Mock(return_value={"total_pages": 1, "total_chunks": 0})
    monkeypatch.setattr(upload, "ingest_document", ingest)
    response = auth_client.post(
        "/api/upload",
        files={"file": ("Exam Notes.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["message"] == "PDF uploaded successfully"
    assert body["document"]["filename"] == "Exam Notes.pdf"
    assert body["document"]["total_pages"] == 1
    assert body["document"]["total_chunks"] == 0

    document = db.query(Document).one()
    stored_path = Path(document.file_path).resolve()
    upload_root = (isolated_runtime.root / "uploads").resolve()
    assert stored_path.is_relative_to(upload_root)
    assert stored_path.name == "document.pdf"
    assert stored_path.parent.name == document.document_uuid
    assert document.filename == document.title == "Exam Notes.pdf"
    assert stored_path.read_bytes() == pdf_bytes
    ingest.assert_called_once_with(
        file_path=str(stored_path),
        db=ANY,
        document_db_id=document.id,
        document_uuid=document.document_uuid,
        user_id=document.uploaded_by,
    )


def test_invalid_mime_type_is_rejected_without_artifacts(
    auth_client,
    db,
    isolated_runtime,
    pdf_bytes,
):
    response = auth_client.post(
        "/api/upload",
        files={"file": ("notes.pdf", pdf_bytes, "text/plain")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF files are allowed"}
    assert_no_upload_artifacts(db, isolated_runtime)


def test_spoofed_pdf_content_is_rejected_without_artifacts(
    auth_client,
    db,
    isolated_runtime,
):
    response = auth_client.post(
        "/api/upload",
        files={"file": ("spoofed.pdf", b"this is plain text", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded content is not a PDF"}
    assert_no_upload_artifacts(db, isolated_runtime)


def test_oversized_pdf_is_rejected_while_streaming(
    auth_client,
    db,
    isolated_runtime,
    monkeypatch,
    pdf_bytes,
):
    from app.api import upload

    monkeypatch.setattr(upload, "MAX_PDF_UPLOAD_SIZE_BYTES", len(pdf_bytes) - 1)
    response = auth_client.post(
        "/api/upload",
        files={"file": ("large.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 413
    assert "maximum upload size" in response.json()["detail"]
    assert str(len(pdf_bytes) - 1) in response.json()["detail"]
    assert_no_upload_artifacts(db, isolated_runtime)


def test_empty_pdf_is_rejected_without_artifacts(auth_client, db, isolated_runtime):
    response = auth_client.post(
        "/api/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "PDF file is empty"}
    assert_no_upload_artifacts(db, isolated_runtime)


def test_corrupted_pdf_is_rejected_without_artifacts(auth_client, db, isolated_runtime):
    response = auth_client.post(
        "/api/upload",
        files={"file": ("broken.pdf", b"%PDF-1.7\nbroken xref", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "PDF is malformed or corrupted"}
    assert_no_upload_artifacts(db, isolated_runtime)


def test_encrypted_pdf_is_rejected_without_artifacts(auth_client, db, isolated_runtime):
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), "Encrypted synthetic document")
        encrypted_pdf = document.tobytes(
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="owner-password",
            user_pw="user-password",
        )

    response = auth_client.post(
        "/api/upload",
        files={"file": ("encrypted.pdf", encrypted_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Encrypted PDFs are not supported"}
    assert_no_upload_artifacts(db, isolated_runtime)


@pytest.mark.parametrize(
    "filename",
    [
        "../escape.pdf",
        "..\\escape.pdf",
        "/tmp/escape.pdf",
        "C:\\temp\\escape.pdf",
    ],
)
def test_traversal_and_absolute_filenames_are_rejected(filename):
    from app.api.upload import _safe_display_filename
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        _safe_display_filename(filename)
    assert error.value.status_code == 400
    assert error.value.detail == "Invalid PDF filename"


def test_path_traversal_upload_is_rejected_without_artifacts(
    auth_client,
    db,
    isolated_runtime,
    pdf_bytes,
):
    response = auth_client.post(
        "/api/upload",
        files={"file": ("../escape.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid PDF filename"}
    assert_no_upload_artifacts(db, isolated_runtime)


def test_validation_failure_closes_pdf_before_cleanup(
    auth_client,
    db,
    isolated_runtime,
):
    response = auth_client.post(
        "/api/upload",
        files={"file": ("broken.pdf", b"%PDF-1.7\ninvalid", "application/pdf")},
    )
    assert response.status_code == 400
    assert_no_upload_artifacts(db, isolated_runtime)

    # On Windows, this rename fails if validation left the upload root locked.
    upload_root = isolated_runtime.root / "uploads"
    renamed_root = isolated_runtime.root / "uploads-renamed"
    upload_root.rename(renamed_root)
    assert renamed_root.is_dir()
