#!/usr/bin/env python3
"""Deterministic B2 scorer frozen before primary developer-speech decoding.

The scorer uses reference annotations only after a candidate hypothesis exists. Its
entity vocabulary is scorer-only evidence and MUST NOT be exposed to C0 decoders.
No network, model, repository resolver, or candidate-specific behavior is used.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "scorer-config.json"
ALLOWED_OUTCOMES = {
    "SUCCESS",
    "TIMEOUT",
    "RUNTIME_ERROR",
    "INVALID_OUTPUT",
    "MISSING_OUTPUT",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def is_word_char(char: str) -> bool:
    return char == "_" or char.isalnum()


def boundary_ok(text: str, start: int, end: int, target: str) -> bool:
    if target and is_word_char(target[0]) and start > 0 and is_word_char(text[start - 1]):
        return False
    if target and is_word_char(target[-1]) and end < len(text) and is_word_char(text[end]):
        return False
    return True


def all_occurrences(text: str, target: str):
    start = 0
    while True:
        index = text.find(target, start)
        if index < 0:
            return
        end = index + len(target)
        if boundary_ok(text, index, end, target):
            yield index, end
        start = index + 1


def detect_entities(hypothesis: str, vocabulary: set[str]) -> list[str]:
    text = nfc(hypothesis)
    candidates: list[tuple[int, int, str]] = []
    for raw in vocabulary:
        target = nfc(raw)
        if not target:
            continue
        for start, end in all_occurrences(text, target):
            candidates.append((start, end, target))

    chosen: list[tuple[int, int, str]] = []
    for start, end, target in sorted(candidates, key=lambda item: (-len(item[2]), item[0], item[2])):
        if any(not (end <= left or start >= right) for left, right, _ in chosen):
            continue
        chosen.append((start, end, target))
    chosen.sort(key=lambda item: (item[0], item[1], item[2]))
    return [target for _, _, target in chosen]


def levenshtein_ops(reference: list[str], hypothesis: list[str]) -> list[str]:
    rows = len(reference) + 1
    cols = len(hypothesis) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            if reference[i - 1] == hypothesis[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j - 1] + 1,
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                )

    operations: list[str] = []
    i = len(reference)
    j = len(hypothesis)
    while i or j:
        if i and j and reference[i - 1] == hypothesis[j - 1] and dp[i][j] == dp[i - 1][j - 1]:
            operations.append("MATCH")
            i -= 1
            j -= 1
            continue
        options: list[tuple[int, int, str]] = []
        if i and j:
            options.append((dp[i - 1][j - 1] + 1, 0, "SUBSTITUTION"))
        if i:
            options.append((dp[i - 1][j] + 1, 1, "DELETION"))
        if j:
            options.append((dp[i][j - 1] + 1, 2, "INSERTION"))
        _, _, operation = min(option for option in options if option[0] == dp[i][j])
        operations.append(operation)
        if operation == "SUBSTITUTION":
            i -= 1
            j -= 1
        elif operation == "DELETION":
            i -= 1
        else:
            j -= 1
    operations.reverse()
    return operations


def ordinary_tokens(text: str) -> list[str]:
    normalized = nfc(text).casefold()
    chars = []
    for char in normalized:
        category = unicodedata.category(char)
        chars.append(" " if category.startswith(("P", "S")) else char)
    return "".join(chars).split()


def annotation_entities(annotation: dict[str, Any]) -> list[dict[str, Any]]:
    entities = annotation.get("entities")
    if not isinstance(entities, list):
        raise ValueError(f"{annotation.get('utterance_id')} entities must be a list")
    ordered = sorted(entities, key=lambda e: (e["start_char"], e["end_char"], e["entity_id"]))
    transcript = annotation["reference_transcript"]
    for entity in ordered:
        start = entity["start_char"]
        end = entity["end_char"]
        if not (0 <= start < end <= len(transcript)):
            raise ValueError(f"invalid entity span for {annotation['utterance_id']}:{entity['entity_id']}")
        if transcript[start:end] != entity["exact_text"]:
            raise ValueError(f"entity exact_text/span mismatch for {annotation['utterance_id']}:{entity['entity_id']}")
        normalization = entity.get("normalization")
        if not isinstance(normalization, dict) or normalization.get("allowed") is not False or normalization.get("rule") is not None:
            raise ValueError(
                f"founding scorer requires normalization.allowed=false/rule=null: "
                f"{annotation['utterance_id']}:{entity['entity_id']}"
            )
    return ordered


def build_vocabulary(annotations: list[dict[str, Any]]) -> set[str]:
    vocabulary: set[str] = set()
    for annotation in annotations:
        for entity in annotation_entities(annotation):
            vocabulary.add(nfc(entity["exact_text"]))
            distractors = entity.get("distractors")
            if not isinstance(distractors, list):
                raise ValueError(f"distractors must be a list: {annotation['utterance_id']}:{entity['entity_id']}")
            vocabulary.update(nfc(item) for item in distractors if isinstance(item, str) and item)
    return vocabulary


def ratio(numerator: int, denominator: int):
    return None if denominator == 0 else numerator / denominator


def score(annotations: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    if config.get("implementation_id") != "wispral-000b2-deterministic-scorer-v1":
        raise ValueError("scorer config implementation_id drift")

    annotation_by_id: dict[str, dict[str, Any]] = {}
    for annotation in annotations:
        utterance_id = annotation.get("utterance_id")
        if not isinstance(utterance_id, str) or not utterance_id or utterance_id in annotation_by_id:
            raise ValueError("annotation utterance_id missing/duplicate")
        annotation_entities(annotation)
        annotation_by_id[utterance_id] = annotation

    prediction_by_id: dict[str, dict[str, Any]] = {}
    for prediction in predictions:
        utterance_id = prediction.get("utterance_id")
        if utterance_id in prediction_by_id:
            raise ValueError("prediction utterance_id duplicate")
        if utterance_id not in annotation_by_id:
            raise ValueError(f"prediction has unknown utterance_id: {utterance_id}")
        outcome = prediction.get("outcome")
        if outcome not in ALLOWED_OUTCOMES:
            raise ValueError(f"invalid outcome for {utterance_id}: {outcome}")
        hypothesis = prediction.get("hypothesis")
        if not isinstance(hypothesis, str):
            raise ValueError(f"hypothesis must be string: {utterance_id}")
        prediction_by_id[utterance_id] = prediction

    if set(prediction_by_id) != set(annotation_by_id):
        missing = sorted(set(annotation_by_id) - set(prediction_by_id))
        raise ValueError(f"missing predictions: {missing}")

    vocabulary = build_vocabulary(annotations)
    exact_correct = 0
    reference_entities = 0
    entity_substitutions = 0
    entity_deletions = 0
    false_entity_insertions = 0
    collateral_substitutions = 0
    collateral_deletions = 0
    collateral_insertions = 0
    collateral_reference_words = 0
    failures = 0

    per_utterance = []
    for utterance_id in sorted(annotation_by_id):
        annotation = annotation_by_id[utterance_id]
        prediction = prediction_by_id[utterance_id]
        outcome = prediction["outcome"]
        hypothesis = prediction["hypothesis"] if outcome == "SUCCESS" else ""
        if outcome != "SUCCESS":
            failures += 1

        ref_sequence = [nfc(entity["exact_text"]) for entity in annotation_entities(annotation)]
        hyp_sequence = detect_entities(hypothesis, vocabulary)
        entity_ops = levenshtein_ops(ref_sequence, hyp_sequence)
        matches = entity_ops.count("MATCH")
        substitutions = entity_ops.count("SUBSTITUTION")
        deletions = entity_ops.count("DELETION")
        insertions = entity_ops.count("INSERTION")
        exact_correct += matches
        reference_entities += len(ref_sequence)
        entity_substitutions += substitutions
        entity_deletions += deletions
        false_entity_insertions += insertions

        collateral_ops: list[str] = []
        if annotation.get("panel") == "GENERAL_COLLATERAL":
            ref_words = ordinary_tokens(annotation["reference_transcript"])
            hyp_words = ordinary_tokens(hypothesis)
            collateral_ops = levenshtein_ops(ref_words, hyp_words)
            collateral_substitutions += collateral_ops.count("SUBSTITUTION")
            collateral_deletions += collateral_ops.count("DELETION")
            collateral_insertions += collateral_ops.count("INSERTION")
            collateral_reference_words += len(ref_words)

        per_utterance.append(
            {
                "utterance_id": utterance_id,
                "outcome": outcome,
                "reference_entity_count": len(ref_sequence),
                "detected_hypothesis_entities": hyp_sequence,
                "entity_operations": entity_ops,
                "collateral_operations": collateral_ops,
            }
        )

    collateral_errors = collateral_substitutions + collateral_deletions + collateral_insertions
    result = {
        "schema_version": "000b2-score-result-v1",
        "scorer_implementation_id": config["implementation_id"],
        "utterance_count": len(annotations),
        "failure_count": failures,
        "failure_rate": ratio(failures, len(annotations)),
        "developer_entity_reference_count": reference_entities,
        "developer_entity_exact_correct": exact_correct,
        "developer_entity_exact_accuracy": ratio(exact_correct, reference_entities),
        "developer_entity_normalized_correct": exact_correct,
        "developer_entity_normalized_accuracy": ratio(exact_correct, reference_entities),
        "entity_substitutions": entity_substitutions,
        "entity_deletions": entity_deletions,
        "false_entity_insertions": false_entity_insertions,
        "collateral_reference_words": collateral_reference_words,
        "collateral_substitutions": collateral_substitutions,
        "collateral_deletions": collateral_deletions,
        "collateral_insertions": collateral_insertions,
        "collateral_wer": ratio(collateral_errors, collateral_reference_words),
        "per_utterance": per_utterance,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    annotations = load_json(args.annotations)
    predictions = load_json(args.predictions)
    if not isinstance(annotations, list) or not isinstance(predictions, list):
        raise SystemExit("annotations and predictions must both be JSON arrays")
    result = score(annotations, predictions)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCORER=PASS")
    print(f"OUTPUT={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
