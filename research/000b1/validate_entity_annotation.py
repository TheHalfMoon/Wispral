#!/usr/bin/env python3
"""Fail-closed semantic validator for Wispral 000B1 entity annotations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(annotation: dict) -> list[str]:
    errors: list[str] = []
    transcript = annotation.get("reference_transcript")
    entities = annotation.get("entities")
    if not isinstance(transcript, str) or not transcript:
        return ["reference_transcript must be a non-empty string"]
    if not isinstance(entities, list):
        return ["entities must be an array"]

    seen_ids: set[str] = set()
    for index, entity in enumerate(entities):
        prefix = f"entities[{index}]"
        if not isinstance(entity, dict):
            errors.append(f"{prefix} must be an object")
            continue
        entity_id = entity.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id:
            errors.append(f"{prefix}.entity_id missing")
        elif entity_id in seen_ids:
            errors.append(f"{prefix}.entity_id duplicate")
        else:
            seen_ids.add(entity_id)

        start = entity.get("start_char")
        end = entity.get("end_char")
        exact_text = entity.get("exact_text")
        if not isinstance(start, int) or not isinstance(end, int):
            errors.append(f"{prefix} span offsets must be integers")
            continue
        if start < 0 or end <= start:
            errors.append(f"{prefix} must satisfy 0 <= start_char < end_char")
            continue
        if end > len(transcript):
            errors.append(f"{prefix}.end_char exceeds reference_transcript length")
            continue
        if not isinstance(exact_text, str) or not exact_text:
            errors.append(f"{prefix}.exact_text must be non-empty")
            continue
        observed = transcript[start:end]
        if observed != exact_text:
            errors.append(
                f"{prefix}.exact_text does not match reference_transcript span: "
                f"expected {observed!r}, got {exact_text!r}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotation", type=Path)
    args = parser.parse_args()
    errors = validate(load(args.annotation))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("ENTITY_ANNOTATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
