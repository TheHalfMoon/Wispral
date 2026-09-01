#!/usr/bin/env python3
"""Regression checks for 000B1 entity annotation semantic invariants."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module():
    path = HERE / "validate_entity_annotation.py"
    spec = importlib.util.spec_from_file_location("entity_annotation_validator", path)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load entity annotation validator")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def base_annotation() -> dict:
    return {
        "utterance_id": "utt-001",
        "panel": "DEVELOPER_ENTITY",
        "split": "qualification",
        "speaker_id": "speaker-q-01",
        "reference_transcript": "open src/main.rs now",
        "entities": [
            {
                "entity_id": "entity-001",
                "class": "FILE_PATH",
                "start_char": 5,
                "end_char": 16,
                "exact_text": "src/main.rs",
                "normalization": {"allowed": False, "rule": None},
                "binding": {"expected_repository_entity": "src/main.rs", "ambiguous": False},
                "distractors": [],
            }
        ],
    }


def expect_error(validator, annotation: dict, needle: str) -> None:
    errors = validator.validate(annotation)
    if not any(needle in error for error in errors):
        raise AssertionError(f"expected {needle!r}; got {errors!r}")


def main() -> int:
    validator = module()
    valid = base_annotation()
    if validator.validate(valid):
        raise AssertionError("valid annotation failed semantic validation")

    empty_span = copy.deepcopy(valid)
    empty_span["entities"][0]["end_char"] = empty_span["entities"][0]["start_char"]
    expect_error(validator, empty_span, "start_char < end_char")

    reversed_span = copy.deepcopy(valid)
    reversed_span["entities"][0]["end_char"] = 2
    expect_error(validator, reversed_span, "start_char < end_char")

    out_of_bounds = copy.deepcopy(valid)
    out_of_bounds["entities"][0]["end_char"] = 999
    expect_error(validator, out_of_bounds, "exceeds reference_transcript length")

    wrong_text = copy.deepcopy(valid)
    wrong_text["entities"][0]["exact_text"] = "src/lib.rs"
    expect_error(validator, wrong_text, "does not match reference_transcript span")

    duplicate_id = copy.deepcopy(valid)
    duplicate_id["entities"].append(copy.deepcopy(duplicate_id["entities"][0]))
    expect_error(validator, duplicate_id, "entity_id duplicate")

    print("VERIFY_ENTITY_ANNOTATION_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
