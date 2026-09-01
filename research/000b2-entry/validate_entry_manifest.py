#!/usr/bin/env python3
"""Amendment-aware, fail-closed validator for B2 attempt manifests.

The B2 manifest remains schema-compatible with the frozen B1 manifest shape. The
bounded artifact amendment and materialization evidence stay separate files; the
manifest carries their effective artifact bytes/SHA values and is anchored by its
canonical Wispral revision. This wrapper additionally refuses B2 readiness while
the live checkout's canonical specification frontier is anything other than READY.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from verify_materialization import correction_map, verify_static

ROOT = Path(__file__).resolve().parents[2]
B1 = ROOT / "research" / "000b1"
HERE = ROOT / "research" / "000b2-entry"
REGISTRY = B1 / "qualified-candidates.json"
SCHEMA = B1 / "schemas" / "attempt-manifest.schema.json"
AMENDMENT = HERE / "artifact-size-amendment.json"
CURRENT = ROOT / "specs" / "CURRENT.md"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
B2_FRONTIER_MARKER = "`000B2-unbiased-stt-bakeoff`"


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def load(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs
    )


def load_b1_validator():
    path = B1 / "validate_attempt_manifest.py"
    spec = importlib.util.spec_from_file_location("wispral_b1_attempt_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load B1 attempt validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_b2_frontier_state() -> str:
    """Read the B2 state from the same checkout being validated, failing closed."""
    text = CURRENT.read_text(encoding="utf-8")
    start = text.find(B2_FRONTIER_MARKER)
    if start < 0:
        raise ValueError("canonical CURRENT.md is missing the B2 frontier marker")
    section = text[start : start + 1024]
    match = re.search(r"(?:^|\n)State: `([A-Z_]+)`(?:\n|$)", section)
    if match is None:
        raise ValueError("canonical CURRENT.md is missing the B2 frontier state")
    return match.group(1)


def type_matches(value: Any, wanted: str) -> bool:
    if wanted == "object":
        return isinstance(value, dict)
    if wanted == "array":
        return isinstance(value, list)
    if wanted == "string":
        return isinstance(value, str)
    if wanted == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if wanted == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if wanted == "boolean":
        return isinstance(value, bool)
    if wanted == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {wanted}")


def validate_schema(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    wanted = schema.get("type")
    if wanted is not None:
        types = wanted if isinstance(wanted, list) else [wanted]
        if not any(type_matches(value, item) for item in types):
            return [f"{path}: expected schema type {types}, got {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value differs from frozen const")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value not in frozen enum")

    if isinstance(value, str):
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append(f"{path}: string does not match frozen pattern")

    if isinstance(value, int) and not isinstance(value, bool):
        if isinstance(schema.get("minimum"), (int, float)) and value < schema["minimum"]:
            errors.append(f"{path}: integer below frozen minimum")

    if isinstance(value, list):
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
            errors.append(f"{path}: array shorter than minItems")
        if schema.get("uniqueItems") is True:
            canonical = [
                json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value
            ]
            if len(canonical) != len(set(canonical)):
                errors.append(f"{path}: array violates uniqueItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, item_schema, f"{path}[{index}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{path}: missing required field {key}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                errors.append(
                    f"{path}: additional properties forbidden: {', '.join(extra)}"
                )
        for key, child in properties.items():
            if key in value and isinstance(child, dict):
                errors.extend(validate_schema(value[key], child, f"{path}.{key}"))
    return errors


def expected_pending_keys() -> set[tuple[str, str]]:
    registry = load(REGISTRY)
    if not isinstance(registry, dict):
        raise ValueError("qualified-candidates registry must be an object")
    result: set[tuple[str, str]] = set()
    families = registry.get("families")
    if not isinstance(families, list):
        raise ValueError("qualified-candidates families missing")
    for family in families:
        if not isinstance(family, dict):
            raise ValueError("qualified-candidates family malformed")
        configurations = family.get("configurations")
        if not isinstance(configurations, list):
            raise ValueError("qualified-candidates configurations malformed")
        for config in configurations:
            if not isinstance(config, dict):
                raise ValueError("qualified-candidates configuration malformed")
            candidate_id = config.get("id")
            artifacts = config.get("artifacts")
            if not isinstance(candidate_id, str) or not isinstance(artifacts, list):
                raise ValueError("qualified-candidates candidate/artifacts malformed")
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    raise ValueError("qualified-candidates artifact malformed")
                if artifact.get("sha256") is None:
                    path = artifact.get("path")
                    if not isinstance(path, str) or not path:
                        raise ValueError("qualified-candidates pending artifact path malformed")
                    key = (candidate_id, path)
                    if key in result:
                        raise ValueError(f"duplicate frozen pending artifact: {key}")
                    result.add(key)
    if len(result) != 18:
        raise ValueError(
            f"frozen pending-artifact set drift: expected 18, got {len(result)}"
        )
    return result


def materialized_map() -> dict[tuple[str, str], dict[str, Any]]:
    verified, _ = verify_static()
    expected = expected_pending_keys()
    if set(verified) != expected:
        raise ValueError(
            "verified materialization authority differs from frozen pending set"
        )
    return verified


def corrections() -> dict[tuple[str, str], dict[str, Any]]:
    # verify_static() binds amendment schema/scope/provenance and every materialized
    # row to the current B1 registry. It proves facts, not candidate-authored chronology.
    verify_static()
    amendment = load(AMENDMENT)
    if not isinstance(amendment, dict):
        raise ValueError("artifact-size amendment must be a JSON object")
    result = correction_map(amendment)
    if set(result) - expected_pending_keys():
        raise ValueError("artifact-size amendment targets non-pending artifact")
    return result


def add_blocker(blockers: list[str], message: str) -> None:
    if message not in blockers:
        blockers.append(message)


def validate_entry(manifest: dict[str, Any], require_ready: bool = False):
    errors: list[str] = []
    schema = load(SCHEMA)
    if not isinstance(schema, dict):
        errors.append("attempt manifest schema must be an object")
        return errors, []
    errors.extend(validate_schema(manifest, schema))

    materialized = materialized_map()
    amended = corrections()
    seen_materialized: set[tuple[str, str]] = set()
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list):
        candidates = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = candidate.get("candidate_id")
        artifacts = candidate.get("artifacts")
        if not isinstance(artifacts, list):
            continue
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            key = (candidate_id, artifact.get("path"))
            evidence = materialized.get(key)
            if evidence is None:
                continue
            seen_materialized.add(key)
            if artifact.get("size_bytes") != evidence["size_bytes"]:
                errors.append(
                    f"{key} size differs from verified materialized evidence"
                )
            if artifact.get("sha256") != evidence["sha256"]:
                errors.append(
                    f"{key} SHA-256 differs from verified materialized evidence"
                )
            if not SHA256.fullmatch(str(artifact.get("sha256", ""))):
                errors.append(f"{key} materialized SHA-256 malformed")

    expected_pending = expected_pending_keys()
    if seen_materialized != expected_pending:
        errors.append(
            "entry manifest does not carry the complete frozen pending-artifact set"
        )

    historical = copy.deepcopy(manifest)
    historical_candidates = historical.get("candidates")
    if isinstance(historical_candidates, list):
        for candidate in historical_candidates:
            if not isinstance(candidate, dict):
                continue
            candidate_id = candidate.get("candidate_id")
            artifacts = candidate.get("artifacts")
            if not isinstance(artifacts, list):
                continue
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    continue
                correction = amended.get((candidate_id, artifact.get("path")))
                if correction:
                    artifact["size_bytes"] = correction["historical_b1_size_bytes"]

    b1 = load_b1_validator()
    b1_errors, b1_blockers = b1.validate(historical, require_ready=False)
    errors.extend(f"B1: {message}" for message in b1_errors)
    blockers = list(b1_blockers)

    blockers = [
        blocker
        for blocker in blockers
        if not blocker.endswith("SHA-256 not materialized")
    ]
    if seen_materialized != expected_pending:
        add_blocker(blockers, "materialized artifact evidence incomplete")

    frontier_state = canonical_b2_frontier_state()
    if frontier_state != "READY":
        add_blocker(
            blockers, f"canonical B2 frontier is {frontier_state}, not READY"
        )

    if require_ready and blockers:
        errors.extend(f"BLOCKER: {blocker}" for blocker in blockers)
    return errors, blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    try:
        manifest = load(args.manifest)
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")
        errors, blockers = validate_entry(manifest, require_ready=args.require_ready)
    except (
        AssertionError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("ENTRY_STRUCTURE=PASS")
    print(f"B2_READY={'NO' if blockers else 'YES'}")
    for blocker in blockers:
        print(f"BLOCKER={blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
