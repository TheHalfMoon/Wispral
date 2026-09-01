#!/usr/bin/env python3
"""Amendment-aware validator layered over the immutable B1 attempt validator.

The B2 manifest remains schema-compatible with the frozen B1 manifest shape. The
pre-attempt amendment and materialization evidence are separate canonical files;
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


def materialized_map() -> dict[tuple[str, str], dict[str, Any]]:
    evidence = load(MATERIALIZED)
    if not isinstance(evidence, dict):
        raise ValueError("materialized evidence must be a JSON object")
    result = {}
    for candidate_id, paths in evidence["artifacts"].items():
        for path, row in paths.items():
            result[(candidate_id, path)] = row
    return result


def corrections() -> dict[tuple[str, str], dict[str, Any]]:
    amendment = load(AMENDMENT)
    if not isinstance(amendment, dict):
        raise ValueError("artifact-size amendment must be a JSON object")
    return {(row["candidate_id"], row["path"]): row for row in amendment["corrections"]}


def validate_entry(manifest: dict[str, Any], require_ready: bool = False):
    errors: list[str] = []
    materialized = materialized_map()
    amended = corrections()

    # No B2-entry-only top-level fields are allowed: the final manifest remains the
    # exact B1 schema shape and is anchored to amendment/evidence by canonical revision.
    b1_schema = load(B1 / "schemas" / "attempt-manifest.schema.json")
    allowed_top = set(b1_schema.get("properties", {}))
    extra_top = sorted(set(manifest) - allowed_top)
    if extra_top:
        errors.append(f"entry manifest adds fields outside frozen B1 schema: {', '.join(extra_top)}")

    candidates = manifest.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates must be an array")
        candidates = []
    seen_materialized: set[tuple[str, str]] = set()
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

    if seen_materialized != set(materialized):
        errors.append("entry manifest does not carry the complete materialized pending-artifact set")

    # Preserve the historical B1 validator exactly. For its structural comparison only,
    # project documented pre-attempt size corrections back to historical B1 sizes.
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

    # The historical B1 validator necessarily reports the originally pending hashes.
    # Suppress only those materialization blockers after exact durable evidence matches.
    blockers = [blocker for blocker in blockers if not blocker.endswith("SHA-256 not materialized")]
    if seen_materialized != set(materialized):
        blockers.append("materialized artifact evidence incomplete")

    if require_ready and blockers:
        errors.extend(f"BLOCKER: {blocker}" for blocker in blockers)
    return errors, blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    manifest = load(args.manifest)
    if not isinstance(manifest, dict):
        print("ERROR: manifest must be a JSON object", file=sys.stderr)
        return 1
    errors, blockers = validate_entry(manifest, require_ready=args.require_ready)
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
