#!/usr/bin/env python3
"""Bind the B2 readiness ledger to the fail-closed human authority contract."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / "research" / "000b2-entry"
READINESS = HERE / "readiness.json"
VERIFIER = HERE / "authority" / "verify_authority.py"
EXPECTED_REQUIRED = [
    "participant consent scope",
    "recording purpose",
    "public redistribution decision",
    "repository storage policy",
    "retention rule",
    "deletion and withdrawal procedure before freeze",
    "derivative benchmark artifact permission",
    "privacy constraints",
    "prohibited-content policy",
]
EXPECTED_PATHS = {
    "authority_schema_path": "research/000b2-entry/authority/authority-package.schema.json",
    "authority_package_path": "research/000b2-entry/authority/authority-package.json",
    "authority_template_path": "research/000b2-entry/authority/authority-package.template.json",
    "authority_verifier_path": "research/000b2-entry/authority/verify_authority.py",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def load_authority_verifier():
    spec = importlib.util.spec_from_file_location("wispral_b2_authority", VERIFIER)
    if spec is None or spec.loader is None:
        fail("cannot load canonical authority verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify() -> None:
    record = json.loads(READINESS.read_text(encoding="utf-8"))
    gates = record.get("gates")
    if not isinstance(gates, dict):
        fail("readiness gates missing")
    human = gates.get("human_developer_speech_authority")
    if not isinstance(human, dict):
        fail("human authority gate missing")
    if human.get("status") != "BLOCKED_EXTERNAL" or human.get("resolved") is not False:
        fail("human authority gate must remain BLOCKED_EXTERNAL")
    if human.get("required") != EXPECTED_REQUIRED:
        fail("human authority requirement list drift")
    for field, expected in EXPECTED_PATHS.items():
        if human.get(field) != expected:
            fail(f"human authority path drift: {field}")
        path = ROOT / expected
        if path.is_symlink() or not path.is_file():
            fail(f"human authority path missing or symlinked: {expected}")
    note = human.get("note")
    if not isinstance(note, str) or "remains NOT_AUTHORIZED" not in note:
        fail("human authority note no longer records blocked package state")
    if "Repository-owner approval is not participant/media authority" not in note:
        fail("repository-owner non-substitution boundary missing")

    authority = load_authority_verifier()
    package = authority.load(ROOT / EXPECTED_PATHS["authority_package_path"])
    errors = authority.verify_package(package, require_authorized=False)
    if errors:
        fail("canonical authority package is invalid: " + "; ".join(errors))
    if package.get("authority_status") != "NOT_AUTHORIZED":
        fail("current readiness ledger cannot claim blocked authority while package is AUTHORIZED")

    blockers = record.get("remaining_blockers")
    if not isinstance(blockers, list) or "human developer-speech participant/media authority is absent" not in blockers:
        fail("human authority blocker disappeared from readiness ledger")
    if record.get("b2_disposition") != "BLOCKED_EXTERNAL" or record.get("b2_ready") is not False:
        fail("B2 readiness advanced before human authority")
    if record.get("primary_test_decoding_performed") is not False:
        fail("primary decoding claim advanced before human authority")


def main() -> int:
    try:
        verify()
    except (AssertionError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"VERIFY_000B2_AUTHORITY_READINESS=FAIL: {exc}", file=sys.stderr)
        return 1
    print("VERIFY_000B2_AUTHORITY_READINESS=PASS")
    print("AUTHORITY_PACKAGE=NOT_AUTHORIZED")
    print("B2_READY=NO")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
