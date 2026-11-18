"""Gold-dataset validation, deterministic splitting, and hashing."""

from collections import defaultdict
from difflib import SequenceMatcher
import hashlib
import json
import random
import re

CATEGORIES = {
    "direct_factual", "paraphrased_semantic", "multi_step_reasoning",
    "unanswerable", "cross_document_isolation",
}
REVIEW_STATUSES = {"draft", "in_review", "approved", "rejected"}
CATEGORY_TARGETS = {
    "direct_factual": 45,
    "paraphrased_semantic": 20,
    "multi_step_reasoning": 10,
    "unanswerable": 15,
    "cross_document_isolation": 10,
}
REQUIRED = {
    "question_id", "question", "document_scope_uuid", "expected_answer",
    "answerable", "relevant_document_ids", "relevant_page_numbers",
    "supporting_spans", "category", "ocr_scanned", "mathematical",
    "reviewer_status", "reviewer_notes",
}


class DatasetValidationError(ValueError):
    pass


def canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_question(question):
    return re.sub(r"[^a-z0-9 ]+", "", " ".join(question.lower().split()))


def _leakage_groups(records):
    """Connect records sharing any document or exact supporting passage."""
    parents = list(range(len(records)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    document_sets = [set(record["relevant_document_ids"]) | ({record["document_scope_uuid"]} if record["document_scope_uuid"] else set()) for record in records]
    passage_sets = [{
        " ".join(span["text"].lower().split())
        for span in record["supporting_spans"]
    } for record in records]
    for left in range(len(records)):
        for right in range(left + 1, len(records)):
            if document_sets[left] & document_sets[right] or passage_sets[left] & passage_sets[right]:
                union(left, right)
    groups = defaultdict(list)
    for index, record in enumerate(records):
        groups[find(index)].append(record)
    return list(groups.values())


def validate_dataset(records, require_approved=False):
    errors, seen_ids, normalized = [], set(), []
    if not isinstance(records, list):
        raise DatasetValidationError("Dataset root must be a JSON array")
    for index, record in enumerate(records):
        prefix = f"record[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        missing = sorted(REQUIRED - record.keys())
        if missing:
            errors.append(f"{prefix}: missing fields {missing}")
            continue
        question_id = record["question_id"]
        if not isinstance(question_id, str) or not question_id.strip():
            errors.append(f"{prefix}: invalid question_id")
        elif question_id in seen_ids:
            errors.append(f"{prefix}: duplicate question_id {question_id}")
        seen_ids.add(question_id)
        if not isinstance(record["question"], str) or not record["question"].strip():
            errors.append(f"{prefix}: question must be nonempty")
        if record["category"] not in CATEGORIES:
            errors.append(f"{prefix}: unsupported category")
        if record["reviewer_status"] not in REVIEW_STATUSES:
            errors.append(f"{prefix}: unsupported reviewer_status")
        if require_approved and record["reviewer_status"] != "approved":
            errors.append(f"{prefix}: record is not approved")
        for field in ("answerable", "ocr_scanned", "mathematical"):
            if not isinstance(record[field], bool):
                errors.append(f"{prefix}: {field} must be boolean")
        for field in ("relevant_document_ids", "relevant_page_numbers", "supporting_spans"):
            if not isinstance(record[field], list):
                errors.append(f"{prefix}: {field} must be an array")
        if record["document_scope_uuid"] is not None and not isinstance(record["document_scope_uuid"], str):
            errors.append(f"{prefix}: document_scope_uuid must be string or null")
        if isinstance(record["relevant_document_ids"], list) and not all(isinstance(value, str) and value for value in record["relevant_document_ids"]):
            errors.append(f"{prefix}: relevant_document_ids must contain nonempty strings")
        if isinstance(record["relevant_page_numbers"], list) and not all(isinstance(value, int) and value >= 1 for value in record["relevant_page_numbers"]):
            errors.append(f"{prefix}: relevant_page_numbers must contain positive integers")
        if record["answerable"]:
            if not isinstance(record["expected_answer"], str) or not record["expected_answer"].strip():
                errors.append(f"{prefix}: answerable record requires expected_answer")
            if not record["supporting_spans"]:
                errors.append(f"{prefix}: answerable record requires supporting_spans")
        elif record["expected_answer"] not in (None, ""):
            errors.append(f"{prefix}: unanswerable expected_answer must be null or empty")
        for span in record["supporting_spans"] if isinstance(record["supporting_spans"], list) else []:
            if not isinstance(span, dict) or not {"document_id", "page", "text"}.issubset(span):
                errors.append(f"{prefix}: malformed supporting span")
            elif not isinstance(span["page"], int) or span["page"] < 1 or not str(span["text"]).strip():
                errors.append(f"{prefix}: invalid supporting span labels")
        normalized.append((question_id, _normalized_question(record["question"])))
    for index, (left_id, left) in enumerate(normalized):
        for right_id, right in normalized[index + 1:]:
            if left == right or SequenceMatcher(None, left, right).ratio() >= 0.92:
                errors.append(f"near-duplicate questions: {left_id} and {right_id}")
    if errors:
        raise DatasetValidationError("\n".join(errors))
    return records


def split_dataset(records, seed=20261118, sizes=(20, 30, 50), enforce_category_targets=True):
    validate_dataset(records)
    names = ("development", "validation", "held_out_test")
    if len(records) != sum(sizes):
        raise DatasetValidationError(f"Expected {sum(sizes)} records for requested split sizes")
    if enforce_category_targets:
        counts = {category: sum(record["category"] == category for record in records) for category in CATEGORIES}
        if counts != CATEGORY_TARGETS:
            raise DatasetValidationError(f"Category counts do not match target allocation: {counts}")
    targets = dict(zip(names, sizes))
    rng = random.Random(seed)
    groups = sorted(_leakage_groups(records), key=lambda group: tuple(record["question_id"] for record in group))
    rng.shuffle(groups)
    output = {name: [] for name in names}
    leaked_groups = []
    for group in groups:
        candidates = [name for name in names if len(output[name]) + len(group) <= targets[name]]
        if candidates:
            chosen = max(candidates, key=lambda name: targets[name] - len(output[name]))
            output[chosen].extend(group)
        else:
            leaked_groups.append([record["question_id"] for record in group])
            for record in group:
                chosen = max(names, key=lambda name: targets[name] - len(output[name]))
                output[chosen].append(record)
    for name in names:
        output[name].sort(key=lambda record: record["question_id"])
        if len(output[name]) != targets[name]:
            raise DatasetValidationError("Unable to satisfy exact split sizes")
    metadata = {
        "seed": seed,
        "dataset_hash": canonical_hash(records),
        "split_sizes": targets,
        "split_hashes": {name: canonical_hash([r["question_id"] for r in output[name]]) for name in names},
        "question_ids": {name: [r["question_id"] for r in output[name]] for name in names},
        "document_groups_split_due_to_capacity": leaked_groups,
        "held_out_policy": "Never use held_out_test results to tune retrieval parameters",
    }
    return output, metadata
