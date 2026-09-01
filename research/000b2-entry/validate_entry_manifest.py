#!/usr/bin/env python3
"""Amendment-aware, fail-closed validator for B2 attempt manifests.

The B2 manifest remains schema-compatible with the frozen B1 manifest shape. The
pre-attempt amendment and materialization evidence stay separate canonical files;
the manifest carries their effective artifact bytes/SHA values and is anchored by
its canonical Wispral revision.
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

ROOT = Path(__file__).resolve().parents[2]
B1 = ROOT / "research" / "000b1"
HERE = ROOT / "research" / "000b2-entry"
REGISTRY = B1 / "qualified-candidates.json"
SCHEMA = B1 / "schemas" / "attempt-manifest.schema.json"
MATERIALIZED = HERE / "materialized-artifacts.json"
AMENDMENT = HERE / "artifact-size-amendment.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_b1_validator():
    path = B1 / "validate_attempt_manifest.py"
    spec = importlib.util.spec_from_file_location("wispral_b1_attempt_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load B1 attempt validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
            canonical = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
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
                errors.append(f"{path}: additional properties forbidden: {', '.join(extra)}")
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
        for config in family.get("configurations", []):
            if not isinstance(config, dict):
                raise ValueError("qualified-candidates configuration malformed")
            candidate_id = config.get("id")
            for artifact in config.get("artifacts", []):
                if not isinstance(artifact, dict):
                    raise ValueError("qualified-candidates artifact malformed")
                if artifact.get("sha256") is None:
                    result.add((candidate_id, artifact.get("path")))
    if len(result) != 18:
        raise ValueError(f"frozen pending-artifact set drift: expected 18, got {len(result)}")
    return result


def materialized_map() -> dict[tuple[str, str], dict[str, Any]]:
    evidence = load(MATERIALIZED)
    if not isinstance(evidence, dict):
        raise ValueError("materialized evidence must be a JSON object")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("materialized artifact mapping missing")
    for candidate_id, paths in artifacts.items():
        if not isinstance(paths, dict):
            raise ValueError(f"materialized candidate mapping malformed: {candidate_id}")
        for path, row in paths.items():
            if not isinstance(row, dict):
                raise ValueError(f"materialized row malformed: {candidate_id}:{path}")
            key = (candidate_id, path)
            if key in result:
                raise ValueError(f"duplicate materialized artifact: {key}")
            result[key] = row
    expected = expected_pending_keys()
    if set(result) != expected:
        raise ValueError(
            f"materialized evidence does not cover frozen pending set: "
            f"missing={sorted(expected - set(result))}, extra={sorted(set(result) - expected)}"
        )
    return result


def corrections() -> dict[tuple[str, str], dict[str, Any]]:
    amendment = load(AMENDMENT)
    if not isinstance(amendment, dict):
        raise ValueError("artifact-size amendment must be a JSON object")
    if amendment.get("status") != "PRE_ATTEMPT_CORRECTION":
        raise ValueError("artifact-size amendment status drift")
    if amendment.get("primary_test_decoding_performed") is not False:
        raise ValueError("artifact-size amendment follows primary decoding")
    if amendment.get("comparative_ranking_present") is not False:
        raise ValueError("artifact-size amendment follows comparative ranking")
    result = {(row["candidate_id"], row["path"]): row for row in amendment["corrections"]}
    if set(result) - expected_pending_keys():
        raise ValueError("artifact-size amendment targets non-pending artifact")
    return result


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
                errors.append(f"{key} size differs from materialized evidence")
            if artifact.get("sha256") != evidence["sha256"]:
                errors.append(f"{key} SHA-256 differs from materialized evidence")
            if not SHA256.fullmatch(str(artifact.get("sha256", ""))):
                errors.append(f"{key} materialized SHA-256 malformed")

    expected_pending = expected_pending_keys()
    if seen_materialized != expected_pending:
        errors.append("entry manifest does not carry the complete frozen pending-artifact set")

    historical = copy.deepcopy(manifest)
    for candidate in historical.get("candidates", []):
        candidate_id = candidate.get("candidate_id")
        for artifact in candidate.get("artifacts", []):
            correction = amended.get((candidate_id, artifact.get("path")))
            if correction:
                artifact["size_bytes"] = correction["historical_b1_size_bytes"]

    b1 = load_b1_validator()
    b1_errors, b1_blockers = b1.validate(historical, require_ready=False)
    errors.extend(f"B1: {message}" for message in b1_errors)
    blockers = list(b1_blockers)

    blockers = [blocker for blocker in blockers if not blocker.endswith("SHA-256 not materialized")]
    if seen_materialized != expected_pending:
        blockers.append("materialized artifact evidence incomplete")

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
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
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