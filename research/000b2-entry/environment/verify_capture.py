#!/usr/bin/env python3
"""Regression checks for the B2 execution-environment capture boundary."""

from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load_module():
    spec = importlib.util.spec_from_file_location("wispral_b2_environment_capture", HERE / "capture.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import environment capture")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    capture = load_module()
    revision = "0" * 40
    evidence = capture.capture(revision, "DIAGNOSTIC")
    require(evidence["schema_version"] == "000b2-execution-environment-v1", "schema drift")
    require(evidence["canonical_wispral_revision"] == revision, "revision drift")
    require(evidence["performance_mode"] == "DIAGNOSTIC", "performance-mode drift")
    require(evidence["comparative_performance_authorized"] is False, "comparative performance became authorized")
    require(evidence["primary_test_decoding_started"] is False, "capture claims primary decoding started")
    require(bool(SHA256.fullmatch(evidence["hardware_fingerprint_sha256"])), "hardware fingerprint malformed")
    require(isinstance(evidence["environment_id"], str) and bool(evidence["environment_id"]), "environment id missing")

    old_actions = os.environ.get("GITHUB_ACTIONS")
    old_runner_environment = os.environ.get("RUNNER_ENVIRONMENT")
    try:
        os.environ["GITHUB_ACTIONS"] = "true"
        os.environ["RUNNER_ENVIRONMENT"] = "github-hosted"
        try:
            capture.capture(revision, "CONTROLLED")
        except ValueError as exc:
            require("cannot be declared CONTROLLED" in str(exc), "unexpected hosted-control rejection")
        else:
            raise AssertionError("GitHub-hosted CONTROLLED capture was accepted")

        os.environ["GITHUB_ACTIONS"] = "false"
        os.environ.pop("RUNNER_ENVIRONMENT", None)
        non_hosted = capture.capture(revision, "CONTROLLED")
        require(non_hosted["performance_mode"] == "CONTROLLED", "GITHUB_ACTIONS=false misclassified as hosted")
        require(non_hosted["runner"]["github_actions"] is False, "false GitHub Actions marker misparsed")
    finally:
        if old_actions is None:
            os.environ.pop("GITHUB_ACTIONS", None)
        else:
            os.environ["GITHUB_ACTIONS"] = old_actions
        if old_runner_environment is None:
            os.environ.pop("RUNNER_ENVIRONMENT", None)
        else:
            os.environ["RUNNER_ENVIRONMENT"] = old_runner_environment

    for bad_revision in ("", "abc", "A" * 40, "g" * 40):
        try:
            capture.capture(bad_revision, "DIAGNOSTIC")
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid canonical revision accepted: {bad_revision!r}")

    print("VERIFY_000B2_ENVIRONMENT_CAPTURE=PASS")
    print("ASSERT_OPTIMIZATION_SAFE=YES")
    print("GITHUB_HOSTED_CONTROLLED=REJECTED")
    print("GITHUB_ACTIONS_FALSE=NON_HOSTED")
    print("COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())