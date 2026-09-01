#!/usr/bin/env python3
"""Adversarial regression checks for the 000B2 frozen-registry readiness gate."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator_module():
    path = HERE / "validate_attempt_manifest.py"
    spec = importlib.util.spec_from_file_location("b2_validator_registry_regression", path)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load B2 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_error(validator, manifest: dict, needle: str) -> None:
    errors, _ = validator.validate(manifest, False)
    if not any(needle in error for error in errors):
        raise AssertionError(f"expected validation error containing {needle!r}; got {errors!r}")


def expect_blocker(validator, manifest: dict, needle: str) -> None:
    errors, blockers = validator.validate(manifest, False)
    if errors:
        raise AssertionError(f"unexpected structural errors while checking blocker: {errors!r}")
    if not any(needle in blocker for blocker in blockers):
        raise AssertionError(f"expected readiness blocker containing {needle!r}; got {blockers!r}")


def main() -> int:
    validator = validator_module()
    draft = load(HERE / "examples" / "draft-attempt-manifest.json")

    errors, blockers = validator.validate(draft, False)
    if errors:
        raise AssertionError(f"baseline blocked draft is structurally invalid: {errors!r}")
    if not blockers:
        raise AssertionError("baseline blocked draft unexpectedly has no B2 blockers")

    runtime_drift = copy.deepcopy(draft)
    runtime_drift["candidates"][0]["runtime_revision"] = "0" * 40
    expect_error(validator, runtime_drift, "runtime_revision drift")

    c0_drift = copy.deepcopy(draft)
    c0_drift["candidates"][0]["c0"]["family"]["keyterms"] = ["preferred_test_entity"]
    expect_error(validator, c0_drift, "c0 does not exactly match frozen methodology")

    missing_cell = copy.deepcopy(draft)
    missing_cell["candidates"] = missing_cell["candidates"][:-1]
    expect_error(validator, missing_cell, "omitted without allowed pre-freeze exclusion")

    unregistered = copy.deepcopy(draft)
    unregistered["candidates"][0]["candidate_id"] = "unregistered-fast-model"
    expect_error(validator, unregistered, "not in qualified-candidates.json")

    smoke_without_evidence = copy.deepcopy(draft)
    smoke_without_evidence["candidates"][0]["operational_qualification"] = {
        "status": "SMOKE_PASS",
        "evidence_sha256": None,
        "canonical_waiver_revision": None,
    }
    expect_blocker(validator, smoke_without_evidence, "smoke PASS evidence not pinned")

    ready_errors, _ = validator.validate(draft, True)
    if not any("manifest not frozen" in error for error in ready_errors):
        raise AssertionError("--require-ready must fail while manifest remains unfrozen")

    print("VERIFY_B2_REGISTRY_GATE=PASS")
    print("B2_READY=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
