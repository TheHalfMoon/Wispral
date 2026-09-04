#!/usr/bin/env python3
"""Deterministic public-corpus WER adapter for the frozen B2 P0 subset.

This adapter reuses the canonical B2 scorer's NFC/casefold/punctuation/whitespace
normalization and unit-cost Levenshtein implementation. It never supplies
reference text or vocabulary to a decoder and performs no network access.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/000b2-public"
SCORER_PATH = ROOT / "research/000b2-entry/scorer.py"
SCORER_CONFIG_PATH = ROOT / "research/000b2-entry/scorer-config.json"
DEFAULT_SUBSET = HERE / "subset-manifest.json"
EXPECTED_SUBSET_FREEZE_DIGEST = "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242"
EXPECTED_CORE_SCORER_SHA256 = "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1"
EXPECTED_CORE_CONFIG_SHA256 = "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3"
ALLOWED_OUTCOMES = {
    "SUCCESS",
    "TIMEOUT",
    "RUNTIME_ERROR",
    "INVALID_OUTPUT",
    "MISSING_OUTPUT",
}


class PublicWerError(ValueError):
    """Raised when public WER inputs violate the frozen scoring contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicWerError(message)


def load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicWerError(f"unable to load {label}: {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def verify_core_scorer_identity() -> None:
    require(
        sha256_file(SCORER_PATH) == EXPECTED_CORE_SCORER_SHA256,
        "canonical B2 scorer implementation bytes drift",
    )
    require(
        sha256_file(SCORER_CONFIG_PATH) == EXPECTED_CORE_CONFIG_SHA256,
        "canonical B2 scorer config bytes drift",
    )


def load_core_scorer():
    verify_core_scorer_identity()
    spec = importlib.util.spec_from_file_location("wispral_b2_core_scorer", SCORER_PATH)
    require(spec is not None and spec.loader is not None, "unable to load canonical B2 scorer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_normalization_contract() -> dict[str, Any]:
    verify_core_scorer_identity()
    config = load_json(SCORER_CONFIG_PATH, "scorer config")
    require(isinstance(config, dict), "scorer config root must be an object")
    ordinary = config.get("ordinary_wer")
    source_contract = {
        "panels": ["GENERAL_COLLATERAL"],
        "unicode_representation": "NFC",
        "casefold": True,
        "punctuation_and_symbol_categories_to_space": ["P", "S"],
        "whitespace": "COLLAPSE_AND_SPLIT",
        "algorithm": "UNIT_COST_LEVENSHTEIN",
    }
    require(ordinary == source_contract, "canonical ordinary-WER normalization drift")
    return {key: value for key, value in source_contract.items() if key != "panels"}


def subset_freeze_digest(subset: dict[str, Any]) -> str:
    projection = copy.deepcopy(subset)
    require("freeze_digest_sha256" in projection, "public P0 subset freeze digest field missing")
    projection["freeze_digest_sha256"] = None
    return hashlib.sha256(canonical_json_bytes(projection)).hexdigest()


def verify_canonical_subset(subset: dict[str, Any]) -> None:
    require(subset.get("frozen") is True, "public P0 subset must remain frozen")
    require(
        subset.get("freeze_digest_sha256") == EXPECTED_SUBSET_FREEZE_DIGEST,
        "public P0 subset declared freeze digest drift",
    )
    require(
        subset_freeze_digest(subset) == EXPECTED_SUBSET_FREEZE_DIGEST,
        "public P0 subset content identity drift",
    )


def flatten_references(subset: dict[str, Any]) -> dict[str, str]:
    membership = subset.get("membership")
    require(isinstance(membership, dict), "subset membership missing")
    partitions = membership.get("partitions")
    require(isinstance(partitions, list), "subset partitions missing")
    references: dict[str, str] = {}
    for partition in partitions:
        require(isinstance(partition, dict), "subset partition must be an object")
        speakers = partition.get("speakers")
        require(isinstance(speakers, list), "subset speakers missing")
        for speaker in speakers:
            require(isinstance(speaker, dict), "subset speaker must be an object")
            utterances = speaker.get("utterances")
            require(isinstance(utterances, list), "subset utterances missing")
            for row in utterances:
                require(isinstance(row, dict), "subset utterance must be an object")
                utterance_id = row.get("utterance_id")
                reference = row.get("reference_transcript")
                require(isinstance(utterance_id, str) and utterance_id, "utterance_id missing")
                require(isinstance(reference, str), f"reference transcript missing: {utterance_id}")
                require(utterance_id not in references, f"duplicate subset utterance_id: {utterance_id}")
                references[utterance_id] = reference
    require(len(references) == 240, f"public P0 subset must contain exactly 240 utterances, found {len(references)}")
    return references


def ratio(numerator: int, denominator: int):
    return None if denominator == 0 else numerator / denominator


def score_predictions(
    subset: dict[str, Any],
    predictions: list[dict[str, Any]],
    *,
    require_canonical_subset: bool = True,
) -> dict[str, Any]:
    normalization = verify_normalization_contract()
    if require_canonical_subset:
        verify_canonical_subset(subset)
    core = load_core_scorer()
    references = flatten_references(subset)

    by_id: dict[str, dict[str, Any]] = {}
    for row in predictions:
        require(isinstance(row, dict), "prediction row must be an object")
        utterance_id = row.get("utterance_id")
        require(isinstance(utterance_id, str) and utterance_id in references, f"unknown prediction utterance_id: {utterance_id!r}")
        require(utterance_id not in by_id, f"duplicate prediction utterance_id: {utterance_id}")
        outcome = row.get("outcome")
        require(outcome in ALLOWED_OUTCOMES, f"invalid outcome for {utterance_id}: {outcome!r}")
        hypothesis = row.get("hypothesis")
        require(isinstance(hypothesis, str), f"hypothesis must be a string: {utterance_id}")
        if outcome != "SUCCESS":
            require(hypothesis == "", f"non-success hypothesis must be empty: {utterance_id}")
        by_id[utterance_id] = row

    missing = sorted(set(references) - set(by_id))
    extra = sorted(set(by_id) - set(references))
    require(not missing, f"missing predictions: {missing[:8]}{'...' if len(missing) > 8 else ''}")
    require(not extra, f"unexpected predictions: {extra[:8]}{'...' if len(extra) > 8 else ''}")

    substitutions = deletions = insertions = reference_words = failures = 0
    per_utterance: list[dict[str, Any]] = []
    for utterance_id in sorted(references):
        row = by_id[utterance_id]
        outcome = row["outcome"]
        hypothesis = row["hypothesis"] if outcome == "SUCCESS" else ""
        if outcome != "SUCCESS":
            failures += 1
        ref_tokens = core.ordinary_tokens(references[utterance_id])
        hyp_tokens = core.ordinary_tokens(hypothesis)
        ops = core.levenshtein_ops(ref_tokens, hyp_tokens)
        s = ops.count("SUBSTITUTION")
        d = ops.count("DELETION")
        i = ops.count("INSERTION")
        substitutions += s
        deletions += d
        insertions += i
        reference_words += len(ref_tokens)
        per_utterance.append(
            {
                "utterance_id": utterance_id,
                "outcome": outcome,
                "reference_word_count": len(ref_tokens),
                "substitutions": s,
                "deletions": d,
                "insertions": i,
                "errors": s + d + i,
            }
        )

    errors = substitutions + deletions + insertions
    return {
        "schema_version": "000b2-public-p0-wer-v1",
        "utterance_count": len(references),
        "failure_count": failures,
        "failure_rate": ratio(failures, len(references)),
        "reference_words": reference_words,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
        "errors": errors,
        "wer": ratio(errors, reference_words),
        "normalization": normalization,
        "per_utterance": per_utterance,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", type=Path, default=DEFAULT_SUBSET)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    subset = load_json(args.subset, "subset manifest")
    predictions = load_json(args.predictions, "predictions")
    require(isinstance(subset, dict), "subset manifest root must be an object")
    require(isinstance(predictions, list), "predictions root must be an array")
    result = score_predictions(subset, predictions)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("B2P08_PUBLIC_WER_ADAPTER=PASS")
    print(f"UTTERANCES={result['utterance_count']}")
    print(f"REFERENCE_WORDS={result['reference_words']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
