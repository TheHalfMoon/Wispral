#!/usr/bin/env python3
"""Regression gate for the frozen B2 deterministic scorer."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from scorer import score  # noqa: E402

EXPECTED_CONFIG_SHA256 = "b088d041246d6399481baf165f8bd0ac027b400ece8df8dcd42ac4e74b0c31b0"


def entity(entity_id: str, cls: str, transcript: str, exact: str, distractors: list[str]):
    start = transcript.index(exact)
    return {
        "entity_id": entity_id,
        "class": cls,
        "start_char": start,
        "end_char": start + len(exact),
        "exact_text": exact,
        "spoken_form": None,
        "normalization": {"allowed": False, "rule": None},
        "binding": {"expected_repository_entity": None, "ambiguous": False},
        "distractors": distractors,
    }


def fixture():
    d1 = "open src/lib.rs then run --check"
    d2 = "call parse_config"
    annotations = [
        {
            "utterance_id": "d1",
            "panel": "DEVELOPER_ENTITY",
            "split": "qualification",
            "speaker_id": "fixture",
            "reference_transcript": d1,
            "entities": [
                entity("d1-path", "FILE_PATH", d1, "src/lib.rs", ["src/libs.rs"]),
                entity("d1-flag", "CLI_FLAG", d1, "--check", ["--checked"]),
            ],
        },
        {
            "utterance_id": "d2",
            "panel": "DEVELOPER_ENTITY",
            "split": "qualification",
            "speaker_id": "fixture",
            "reference_transcript": d2,
            "entities": [entity("d2-id", "IDENTIFIER", d2, "parse_config", ["parse_configs"])],
        },
        {
            "utterance_id": "c1",
            "panel": "GENERAL_COLLATERAL",
            "split": "qualification",
            "speaker_id": "fixture",
            "reference_transcript": "Hello, world!",
            "entities": [],
        },
        {
            "utterance_id": "c2",
            "panel": "GENERAL_COLLATERAL",
            "split": "qualification",
            "speaker_id": "fixture",
            "reference_transcript": "Build passes.",
            "entities": [],
        },
    ]
    predictions = [
        {"utterance_id": "d1", "outcome": "SUCCESS", "hypothesis": "open src/lib.rs then run --checked"},
        {"utterance_id": "d2", "outcome": "SUCCESS", "hypothesis": "call parse_configs then src/lib.rs"},
        {"utterance_id": "c1", "outcome": "SUCCESS", "hypothesis": "hello word"},
        {"utterance_id": "c2", "outcome": "TIMEOUT", "hypothesis": "ignored output"},
    ]
    return annotations, predictions


def fail(message: str):
    raise AssertionError(message)


def config_digest(config: dict) -> str:
    payload = (json.dumps(config, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    try:
        annotations, predictions = fixture()
        result = score(annotations, predictions)
        expected = {
            "utterance_count": 4,
            "failure_count": 1,
            "failure_rate": 0.25,
            "developer_entity_reference_count": 3,
            "developer_entity_exact_correct": 1,
            "developer_entity_exact_accuracy": 1 / 3,
            "developer_entity_normalized_correct": 1,
            "developer_entity_normalized_accuracy": 1 / 3,
            "entity_substitutions": 2,
            "entity_deletions": 0,
            "false_entity_insertions": 1,
            "false_entity_insertion_rate": 1 / 3,
            "collateral_reference_words": 4,
            "collateral_substitutions": 1,
            "collateral_deletions": 2,
            "collateral_insertions": 0,
            "collateral_wer": 0.75,
        }
        for key, value in expected.items():
            if result.get(key) != value:
                fail(f"fixture metric drift for {key}: expected {value!r}, got {result.get(key)!r}")

        if result.get("scorer_implementation_id") != "wispral-000b2-deterministic-scorer-v1":
            fail("implementation id drift")

        # Word-edge guard: the expected identifier must not match as a prefix of its distractor.
        d2_result = next(row for row in result["per_utterance"] if row["utterance_id"] == "d2")
        if d2_result["detected_hypothesis_entities"][:1] != ["parse_configs"]:
            fail("longest/boundary entity detection drift")

        # Failure output must be ignored and treated as empty so failures remain in denominators.
        c2_result = next(row for row in result["per_utterance"] if row["utterance_id"] == "c2")
        if c2_result["collateral_operations"] != ["DELETION", "DELETION"]:
            fail("non-success hypothesis was not treated as empty")

        # Founding normalized view is intentionally conservative and cannot be enabled ad hoc.
        changed = copy.deepcopy(annotations)
        changed[0]["entities"][0]["normalization"] = {"allowed": True, "rule": "LOWERCASE"}
        try:
            score(changed, predictions)
        except ValueError:
            pass
        else:
            fail("normalization inflation bypass accepted")

        # B1 annotation authority requires entity_id uniqueness within each utterance.
        duplicate_entity_id = copy.deepcopy(annotations)
        duplicate_entity_id[0]["entities"][1]["entity_id"] = duplicate_entity_id[0]["entities"][0]["entity_id"]
        try:
            score(duplicate_entity_id, predictions)
        except ValueError:
            pass
        else:
            fail("duplicate annotation entity_id was accepted")

        # Missing predictions and unknown candidate output must fail rather than disappear.
        try:
            score(annotations, predictions[:-1])
        except ValueError:
            pass
        else:
            fail("missing prediction was dropped")

        extra = copy.deepcopy(predictions)
        extra.append({"utterance_id": "unknown", "outcome": "SUCCESS", "hypothesis": "x"})
        try:
            score(annotations, extra)
        except ValueError:
            pass
        else:
            fail("unknown prediction was accepted")

        config = json.loads((HERE / "scorer-config.json").read_text(encoding="utf-8"))
        if config_digest(config) != EXPECTED_CONFIG_SHA256:
            fail("scorer config semantic digest drift")
        if config.get("entity_scoring", {}).get("decoder_visibility") is not False:
            fail("scorer-only vocabulary became decoder-visible")
        if config.get("entity_scoring", {}).get("normalization") != "DISABLED_EXACT_EQUALS_NORMALIZED":
            fail("entity normalization policy drift")
        if config.get("entity_scoring", {}).get("false_entity_insertion_rate") != "FALSE_ENTITY_INSERTIONS_OVER_TOTAL_REFERENCE_ENTITIES":
            fail("false entity insertion rate denominator drift")
        if config.get("entity_scoring", {}).get("zero_reference_entity_rate") is not None:
            fail("zero-reference entity rate policy drift")
        if config.get("ordinary_wer", {}).get("panels") != ["GENERAL_COLLATERAL"]:
            fail("ordinary WER panel drift")
        if "false_entity_insertion_rate" not in config.get("metrics", []):
            fail("false entity insertion rate missing from metric contract")
    except (AssertionError, ValueError, KeyError, TypeError, OSError, json.JSONDecodeError, StopIteration) as exc:
        print(f"VERIFY_000B2_SCORER=FAIL: {exc}", file=sys.stderr)
        return 1

    print("VERIFY_000B2_SCORER=PASS")
    print("ENTITY_NORMALIZATION=OFF")
    print("FALSE_ENTITY_INSERTION_RATE=FALSE_ENTITY_INSERTIONS_OVER_TOTAL_REFERENCE_ENTITIES")
    print("SCORER_VOCABULARY_DECODER_VISIBILITY=NO")
    print("PRIMARY_TEST_DECODING=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
