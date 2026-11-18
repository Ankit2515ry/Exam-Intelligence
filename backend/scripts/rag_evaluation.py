"""CLI for dataset validation, splitting, and explicitly authorized evaluation."""

import argparse
import hashlib
import json
from pathlib import Path

from app.evaluation.dataset import split_dataset, validate_dataset


def load_dataset(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "records" not in payload:
        raise ValueError("Dataset must contain dataset_version and records")
    return payload


def hash_corpus(path):
    root = Path(path)
    digest = hashlib.sha256()
    files = sorted(item for item in root.rglob("*.pdf") if item.is_file())
    if not files:
        raise ValueError("Corpus directory contains no PDFs")
    for item in files:
        digest.update(item.relative_to(root).as_posix().encode("utf-8"))
        digest.update(hashlib.sha256(item.read_bytes()).digest())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", nargs="?")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--run-pilot", action="store_true")
    parser.add_argument("--manifest")
    parser.add_argument("--inventory-corpus")
    parser.add_argument("--manifest-output")
    parser.add_argument("--split-output")
    parser.add_argument("--split", choices=["development", "validation", "held_out_test"])
    parser.add_argument("--corpus-hash")
    parser.add_argument("--corpus-dir")
    parser.add_argument("--corpus-version")
    parser.add_argument("--user-id", type=int)
    parser.add_argument("--output", default="evaluation_results")
    parser.add_argument("--generate-answers", action="store_true")
    parser.add_argument("--seed", type=int, default=20261118)
    args = parser.parse_args()
    if args.inventory_corpus:
        from app.evaluation.corpus import inventory_corpus, write_manifest

        if not args.corpus_version or not args.manifest_output:
            parser.error("--inventory-corpus requires --corpus-version and --manifest-output")
        manifest = inventory_corpus(args.inventory_corpus, args.corpus_version)
        write_manifest(manifest, args.manifest_output)
        print(json.dumps({
            "manifest": args.manifest_output,
            "pdf_count": len(manifest["files"]),
            "invalid_pdf_count": len(manifest["invalid_files"]),
            "duplicate_sha256_groups": manifest["duplicate_sha256_groups"],
        }, indent=2))
        return
    if not args.dataset:
        parser.error("dataset is required unless --inventory-corpus is used")
    payload = load_dataset(args.dataset)
    records = validate_dataset(payload["records"])
    if args.pilot:
        from app.evaluation.corpus import PilotValidationError, validate_pilot

        if not args.manifest or not args.corpus_dir:
            parser.error("--pilot requires --manifest and --corpus-dir")
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        try:
            report = validate_pilot(records, manifest, args.corpus_dir)
        except PilotValidationError as exc:
            print(str(exc))
            raise SystemExit(1) from None
        print(json.dumps(report, indent=2))
        if not args.run_pilot:
            return
        if args.generate_answers:
            parser.error("Pilot preparation does not permit --generate-answers")
        if not report["ready_for_pilot_run"]:
            parser.error("Pilot is not ready: resolve validation warnings/errors and approvals")
        corpus_hash = args.corpus_hash or hash_corpus(args.corpus_dir)
        if args.user_id is None or not args.corpus_version:
            parser.error("--run-pilot requires --user-id and --corpus-version")
        from app.evaluation.runner import run_evaluation, write_outputs

        run = run_evaluation(
            records, split_name="pilot", dataset_version=payload.get("dataset_version", "unversioned"),
            corpus_hash=corpus_hash, corpus_version=args.corpus_version,
            user_id=args.user_id, generate_answers=False,
        )
        print(json.dumps(write_outputs(run, args.output), indent=2))
        return
    if args.validate and not args.split_output and not args.split:
        print(json.dumps({"valid": True, "records": len(records)}))
        return
    splits, metadata = split_dataset(records, seed=args.seed)
    if args.split_output:
        target = Path(args.split_output)
        target.mkdir(parents=True, exist_ok=True)
        for name, items in splits.items():
            (target / f"{name}.json").write_text(json.dumps({"dataset_version": payload.get("dataset_version"), "records": items}, indent=2), encoding="utf-8")
        (target / "split-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if args.split:
        from app.evaluation.runner import run_evaluation, write_outputs

        corpus_hash = args.corpus_hash or (hash_corpus(args.corpus_dir) if args.corpus_dir else None)
        if args.user_id is None or not corpus_hash or not args.corpus_version:
            parser.error("--split evaluation requires --user-id, --corpus-version, and --corpus-hash or --corpus-dir")
        run = run_evaluation(
            splits[args.split], split_name=args.split,
            dataset_version=payload.get("dataset_version", "unversioned"),
            corpus_hash=corpus_hash, user_id=args.user_id,
            corpus_version=args.corpus_version,
            generate_answers=args.generate_answers,
        )
        print(json.dumps(write_outputs(run, args.output), indent=2))


if __name__ == "__main__":
    main()
