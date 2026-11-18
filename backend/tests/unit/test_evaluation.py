import hashlib
import json

import pytest
from langchain_core.documents import Document


pytestmark = pytest.mark.unit


def record(question_id="q-1", *, answerable=True, document_id="doc-a", page=1):
    return {
        "question_id": question_id,
        "question": f"What does unique token {hashlib.sha256(question_id.encode()).hexdigest()} mean?",
        "document_scope_uuid": document_id,
        "expected_answer": "Synthetic expected answer" if answerable else None,
        "answerable": answerable,
        "relevant_document_ids": [document_id] if answerable else [],
        "relevant_page_numbers": [page] if answerable else [],
        "supporting_spans": [{"document_id": document_id, "page": page, "text": f"supporting synthetic evidence {question_id}"}] if answerable else [],
        "category": "direct_factual" if answerable else "unanswerable",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "approved",
        "reviewer_notes": "Synthetic unit-test label",
    }


def test_dataset_validation_rejects_missing_duplicate_and_near_duplicate_records():
    from app.evaluation.dataset import DatasetValidationError, validate_dataset

    with pytest.raises(DatasetValidationError, match="missing fields"):
        validate_dataset([{"question_id": "broken"}])
    duplicate = record("same")
    with pytest.raises(DatasetValidationError, match="duplicate question_id"):
        validate_dataset([duplicate, dict(duplicate)])
    left, right = record("left"), record("right")
    right["question"] = left["question"] + "?"
    with pytest.raises(DatasetValidationError, match="near-duplicate"):
        validate_dataset([left, right])


def test_unanswerable_and_missing_answer_labels_are_validated():
    from app.evaluation.dataset import DatasetValidationError, validate_dataset

    validate_dataset([record("unanswerable", answerable=False)])
    missing = record("missing")
    missing["expected_answer"] = ""
    with pytest.raises(DatasetValidationError, match="requires expected_answer"):
        validate_dataset([missing])


def test_deterministic_split_sizes_hashes_and_document_leakage_prevention():
    from app.evaluation.dataset import split_dataset

    records = []
    for document_index in range(10):
        for question_index in range(10):
            item = record(f"d{document_index}-q{question_index}", document_id=f"doc-{document_index}")
            records.append(item)
    first, first_meta = split_dataset(records, seed=17, enforce_category_targets=False)
    second, second_meta = split_dataset(list(reversed(records)), seed=17, enforce_category_targets=False)
    assert {name: len(items) for name, items in first.items()} == {
        "development": 20, "validation": 30, "held_out_test": 50,
    }
    assert first_meta["question_ids"] == second_meta["question_ids"]
    assert first_meta["split_hashes"] == second_meta["split_hashes"]
    assert first_meta["document_groups_split_due_to_capacity"] == []
    document_splits = {}
    for split, items in first.items():
        for item in items:
            document_splits.setdefault(item["relevant_document_ids"][0], set()).add(split)
    assert all(len(splits) == 1 for splits in document_splits.values())


def test_split_reports_capacity_forced_overlapping_document_leakage():
    from app.evaluation.dataset import split_dataset

    records = [record(f"overlap-{index}", document_id=f"doc-{index}") for index in range(6)]
    records[0]["relevant_document_ids"] = ["doc-0", "shared"]
    records[1]["relevant_document_ids"] = ["doc-1", "shared"]
    records[2]["relevant_document_ids"] = ["doc-2", "shared"]
    records[0]["document_scope_uuid"] = None
    records[1]["document_scope_uuid"] = None
    records[2]["document_scope_uuid"] = None
    records[0]["supporting_spans"][0]["text"] = "shared repeated passage"
    records[1]["supporting_spans"][0]["text"] = "shared repeated passage"
    _, metadata = split_dataset(
        records, seed=3, sizes=(2, 2, 2), enforce_category_targets=False,
    )
    assert metadata["document_groups_split_due_to_capacity"]
    assert any(
        {"overlap-0", "overlap-1", "overlap-2"}.issubset(set(group))
        for group in metadata["document_groups_split_due_to_capacity"]
    )


def test_retrieval_metric_formulas_duplicates_multiple_passages_and_empty():
    from app.evaluation.metrics import aggregate_retrieval, retrieval_metrics

    item = record()
    item["supporting_spans"].append({"document_id": "doc-a", "page": 2, "text": "second evidence", "relevance_grade": 2})
    results = [
        {"chunk_id": "c1", "document_id": "doc-a", "page": 1, "content": "supporting synthetic evidence q-1"},
        {"chunk_id": "c1", "document_id": "doc-a", "page": 1, "content": "duplicate"},
        {"chunk_id": "c2", "document_id": "wrong", "page": 1, "content": "noise"},
        {"chunk_id": "c3", "document_id": "doc-a", "page": 2, "content": "second evidence"},
    ]
    metrics = retrieval_metrics(item, results)
    assert metrics["hit_at_5"] == 1
    assert metrics["precision_at_5"] == pytest.approx(2 / 5)
    assert metrics["recall_at_5"] == 1
    assert metrics["mrr_at_10"] == 1
    assert 0 < metrics["ndcg_at_5"] <= 1
    assert retrieval_metrics(item, [])["recall_at_5"] == 0
    unanswerable = retrieval_metrics(record(answerable=False), results)
    assert unanswerable["eligible"] is False
    assert aggregate_retrieval([])["hit_at_5"] is None


def test_citation_validity_scope_user_and_missing_reference_checks():
    from app.evaluation.metrics import citation_validity

    stored = {"c1": {"metadata": {"document_id": "doc-a", "page": 1, "user_id": 7}}}
    sources = [
        {"chunk_id": "c1", "document_id": "doc-a", "page": 1},
        {"chunk_id": "missing", "document_id": "doc-a", "page": 1},
        {"chunk_id": "c1", "document_id": "doc-a", "page": 2},
    ]
    result = citation_validity(sources, stored.get, expected_user_id=7, document_scope_uuid="doc-a")
    assert result["valid"] == 1 and result["invalid"] == 2
    assert {error["error"] for error in result["errors"]} == {"missing_chunk", "metadata_mismatch"}
    isolation = citation_validity(sources[:1], stored.get, expected_user_id=8, document_scope_uuid="doc-a")
    assert isolation["errors"][0]["error"] == "user_isolation_violation"


def test_abstention_and_human_scores_are_distinct():
    from app.evaluation.metrics import abstention_metrics, aggregate_human_scores

    no_context = "No context"
    result = abstention_metrics([
        (record("u", answerable=False), no_context),
        (record("a"), no_context),
        (record("m", answerable=False), "unsupported answer"),
    ], no_context)
    assert result == {"eligible": 3, "correct_abstentions": 1, "false_abstentions": 1, "missed_abstentions": 1}
    scores = aggregate_human_scores([
        {"human_scores": {"factual_correctness": 1, "faithfulness": 0.5}},
        {"human_scores": {"factual_correctness": 0}},
    ])
    assert scores["factual_correctness"] == {"reviewed": 2, "mean": 0.5}
    assert scores["faithfulness"] == {"reviewed": 1, "mean": 0.5}


def test_runner_outputs_metadata_results_and_files(tmp_path):
    from app.evaluation.runner import run_evaluation, write_outputs

    item = record()
    chunk = Document(page_content="supporting synthetic evidence q-1", metadata={
        "chunk_id": "c1", "document_id": "doc-a", "page": 1, "user_id": 7, "score": 0.9,
    })
    run = run_evaluation(
        [item], split_name="development", dataset_version="synthetic-v1",
        corpus_hash="synthetic-corpus", user_id=7,
        retrieve_fn=lambda **kwargs: [chunk],
        rerank_fn=lambda **kwargs: kwargs["chunks"],
        lookup_fn=lambda chunk_id: {"metadata": chunk.metadata, "content": chunk.page_content},
    )
    assert run["sample_count"] == 1
    assert run["configuration"]["answer_generation_enabled"] is False
    assert run["retrieval_metrics"]["hit_at_5"] == 1
    assert run["answer_quality"]["factual_correctness"]["mean"] is None
    assert run["per_question"][0]["answer"] is None
    paths = write_outputs(run, tmp_path)
    assert all((tmp_path / name).exists() for name in (
        "evaluation-results.json", "evaluation-results.csv", "evaluation-summary.md",
    ))
    assert set(paths) == {"json", "csv", "markdown"}
    assert json.loads((tmp_path / "evaluation-results.json").read_text())["run_id"] == run["run_id"]


def test_empty_approved_dataset_runner_is_safe():
    from app.evaluation.runner import run_evaluation

    run = run_evaluation(
        [], split_name="development", dataset_version="empty", corpus_hash="empty",
        user_id=7,
    )
    assert run["sample_count"] == 0
    assert run["retrieval_metrics"]["hit_at_5"] is None
