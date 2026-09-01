#!/usr/bin/env python3
"""Regression checks for the B2 execution-environment capture boundary."""

from __future__ import annotations

import importlib.util
import os
import re
import tempfile
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


def main() -> int:
    capture = load_module()
    revision = "0" * 40
    evidence = capture.capture(revision, "DIAGNOSTIC")
    assert evidence["schema_version"] == "000b2-execution-environment-v1"
    assert evidence["canonical_wispral_revision"] == revision
    assert evidence["performance_mode"] == "DIAGNOSTIC"
    assert evidence["comparative_performance_authorized"] is False
    assert evidence["primary_test_decoding_started"] is False
    assert SHA256.fullmatch(evidence["hardware_fingerprint_sha256"])
    assert isinstance(evidence["environment_id"], str) and evidence["environment_id"]

    old = os.environ.get("GITHUB_ACTIONS")
    os.environ["GITHUB_ACTIONS"] = "true"
    try:
        try:
            capture.capture(revision, "CONTROLLED")
        except ValueError as exc:
            assert "cannot be declared CONTROLLED" in str(exc)
        else:
            raise AssertionError("GitHub-hosted CONTROLLED capture was accepted")
    finally:
        if old is None:
            os.environ.pop("GITHUB_ACTIONS", None)
        else:
            os.environ["GITHUB_ACTIONS"] = old

    for bad_revision in ("", "abc", "A" * 40, "g" * 40):
        try:
            capture.capture(bad_revision, "DIAGNOSTIC")
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid canonical revision accepted: {bad_revision!r}")

    print("VERIFY_000B2_ENVIRONMENT_CAPTURE=PASS")
    print("GITHUB_HOSTED_CONTROLLED=REJECTED")
    print("COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
