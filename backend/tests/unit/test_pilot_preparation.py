import hashlib

import fitz
import pytest


pytestmark = pytest.mark.unit


def _pdf(path, text="Exact supporting passage for pilot validation."):
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), text)
        document.save(path)


def _record(index, document_uuid, status="approved"):
    return {
        "question_id": f"pilot-{index:02d}",
        "question": f"Pilot question with unique token {hashlib.sha256(str(index).encode()).hexdigest()}?",
        "document_scope_uuid": document_uuid,
        "expected_answer": "Reviewer-supplied pilot answer",
        "answerable": True,
        "relevant_document_ids": [document_uuid],
        "relevant_page_numbers": [1],
        "supporting_spans": [{
            "document_id": document_uuid,
            "page": 1,
            "text": "Exact supporting passage for pilot validation.",
        }],
        "category": "direct_factual",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": status,
        "reviewer_notes": "Synthetic pilot validator fixture",
    }


def test_corpus_inventory_records_hash_size_pages_and_duplicate_files(tmp_path):
    from app.evaluation.corpus import inventory_corpus

    corpus = tmp_path / "corpus-v1"
    corpus.mkdir()
    _pdf(corpus / "first.pdf")
    (corpus / "duplicate.pdf").write_bytes((corpus / "first.pdf").read_bytes())
    manifest = inventory_corpus(corpus, "corpus-v1")
    assert len(manifest["files"]) == 2
    assert all(entry["size_bytes"] > 0 for entry in manifest["files"])
    assert all(len(entry["sha256"]) == 64 for entry in manifest["files"])
    assert all(entry["physical_page_count"] == 1 for entry in manifest["files"])
    assert manifest["invalid_files"] == []
    assert manifest["duplicate_sha256_groups"] == [["duplicate.pdf", "first.pdf"]]


def test_corpus_inventory_reports_invalid_pdf_without_aborting(tmp_path):
    from app.evaluation.corpus import inventory_corpus

    corpus = tmp_path / "corpus-v1"
    corpus.mkdir()
    _pdf(corpus / "valid.pdf")
    (corpus / "invalid.pdf").write_bytes(b"not a PDF")
    manifest = inventory_corpus(corpus, "corpus-v1")
    assert [entry["filename"] for entry in manifest["files"]] == ["valid.pdf"]
    assert manifest["invalid_files"][0]["filename"] == "invalid.pdf"
    assert manifest["invalid_files"][0]["size_bytes"] == 9


def test_pilot_validation_checks_manifest_pages_passages_and_approval(tmp_path):
    from app.evaluation.corpus import PilotValidationError, inventory_corpus, validate_pilot

    corpus = tmp_path / "corpus-v1"
    corpus.mkdir()
    _pdf(corpus / "approved.pdf")
    manifest = inventory_corpus(corpus, "corpus-v1")
    document_uuid = "11111111-1111-4111-8111-111111111111"
    manifest["files"][0].update({"document_uuid": document_uuid, "index_status": "indexed"})
    records = [_record(index, document_uuid) for index in range(10)]
    report = validate_pilot(records, manifest, corpus)
    assert report["record_count"] == report["approved_count"] == 10
    assert report["ready_for_pilot_run"] is True
    assert report["final_100_question_rules_applied"] is False
    assert any("Repeated supporting passages" in warning for warning in report["warnings"])

    bad_page = [_record(20, document_uuid)]
    bad_page[0]["relevant_page_numbers"] = [2]
    bad_page[0]["supporting_spans"][0]["page"] = 2
    with pytest.raises(PilotValidationError, match="exceeds"):
        validate_pilot(bad_page, manifest, corpus)

    draft = [_record(index + 30, document_uuid, status="draft") for index in range(10)]
    draft_report = validate_pilot(draft, manifest, corpus)
    assert draft_report["ready_for_pilot_run"] is False
    assert draft_report["approved_count"] == 0
