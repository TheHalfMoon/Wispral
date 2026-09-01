#!/usr/bin/env python3
"""Bind the B2 readiness ledger to the fail-closed human authority contract."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / "research" / "000b2-entry"
READINESS = HERE / "readiness.json"
VERIFIER = HERE / "authority" / "verify_authority.py"
STRUCTURE_PROOF = HERE / "authority" / "canonical-structural-gate.json"
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
    "canonical_structure_proof_path": "research/000b2-entry/authority/canonical-structural-gate.json",
    "trusted_structure_verifier_path": ".github/trusted/verify_000b2_human_authority.py",
    "trusted_structure_workflow_path": ".github/workflows/000b2-trusted-human-authority.yml",
}
AUTHORITY_INTAKE_MERGE = "f71df132f963056b3321fe38b94ed88d6a0dfd89"
TRUSTED_STRUCTURE_MERGE = "8cc8b1a22edd9268a49b3ad16c4d3ee8c0d6d586"
TRUSTED_STRUCTURE_PUSH_RUN = 33542411499


def fail(message: str) -> None:
    raise AssertionError(message)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    if not isinstance(value, dict):
        fail(f"JSON object required: {path}")
    return value


def load_authority_verifier():
    spec = importlib.util.spec_from_file_location("wispral_b2_authority", VERIFIER)
    if spec is None or spec.loader is None:
        fail("cannot load canonical authority verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_structure_proof() -> None:
    proof = load_json(STRUCTURE_PROOF)
    if proof.get("schema_version") != "000b2-authority-structure-closeout-v1":
        fail("authority structure proof schema drift")
    if proof.get("recorded_date") != "2026-09-01":
        fail("authority structure proof date drift")
    if proof.get("disposition") != "STRUCTURE_CANONICAL_AUTHORITY_EXTERNAL":
        fail("authority structure proof disposition drift")
    for field in ("b2_ready", "primary_media_acceptance", "participant_consent_attested"):
        if proof.get(field) is not False:
            fail(f"authority structure proof advanced forbidden field: {field}")

    intake = proof.get("authority_intake")
    if not isinstance(intake, dict):
        fail("authority intake proof missing")
    expected_intake = {
        "pull_request": 14,
        "exact_head_sha": "20961174b5b4603806a6d79963e3bc9e624f5995",
        "exact_head_entry_contracts_run_id": 33541279600,
        "canonical_merge_sha": AUTHORITY_INTAKE_MERGE,
        "postmerge_entry_contracts_run_id": 33541475726,
        "canonical_package_status": "NOT_AUTHORIZED",
    }
    for key, expected in expected_intake.items():
        if intake.get(key) != expected:
            fail(f"authority intake proof drift: {key}")

    trusted = proof.get("trusted_structure_gate")
    if not isinstance(trusted, dict):
        fail("trusted structure proof missing")
    expected_trusted = {
        "pull_request": 15,
        "exact_head_sha": "1516f65cb763a7b50e3f2fa9ebd98ea53d253771",
        "exact_head_bootstrap_run_id": 33542254408,
        "canonical_merge_sha": TRUSTED_STRUCTURE_MERGE,
        "postmerge_push_run_id": TRUSTED_STRUCTURE_PUSH_RUN,
        "candidate_code_execution": False,
        "candidate_data_transport": "GITHUB_CONTENTS_API_EXACT_HEAD_SHA",
        "base_refresh": "EVERY_MAIN_PUSH_REVERIFIES_OPEN_MAIN_TARGETING_PRS",
        "participant_consent_attestation": "NOT_PROVIDED_BY_THIS_GATE",
    }
    for key, expected in expected_trusted.items():
        if trusted.get(key) != expected:
            fail(f"trusted structure proof drift: {key}")

    review = proof.get("review_reconciliation")
    if not isinstance(review, dict):
        fail("authority structure review reconciliation missing")
    if review.get("unavailable_or_silent_review_represented_as_approval") is not False:
        fail("authority structure proof misrepresents unavailable review as approval")

    nonclaims = proof.get("non_claims")
    if not isinstance(nonclaims, dict) or not nonclaims:
        fail("authority structure non-claims missing")
    if any(value is not False for value in nonclaims.values()):
        fail("authority structure proof contains a positive forbidden claim")
    next_action = proof.get("next_action")
    if not isinstance(next_action, str) or "Structural verification alone cannot authorize primary media" not in next_action:
        fail("authority structure proof lost structural-only boundary")


def verify() -> None:
    record = load_json(READINESS)
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
    if human.get("authority_intake_canonical_revision") != AUTHORITY_INTAKE_MERGE:
        fail("authority intake canonical revision drift")
    if human.get("trusted_structure_canonical_revision") != TRUSTED_STRUCTURE_MERGE:
        fail("trusted authority structure canonical revision drift")
    if human.get("trusted_structure_postmerge_run_id") != TRUSTED_STRUCTURE_PUSH_RUN:
        fail("trusted authority structure postmerge run drift")
    if human.get("structural_verification_scope") != "NO_PARTICIPANT_CONSENT_ATTESTATION":
        fail("trusted authority structure scope drift")
    note = human.get("note")
    if not isinstance(note, str) or "package remains NOT_AUTHORIZED" not in note:
        fail("human authority note no longer records blocked package state")
    if "no participant-consent attestation" not in note:
        fail("human authority note lost structural-only trust boundary")
    if "Repository-owner approval is not participant/media authority" not in note:
        fail("repository-owner non-substitution boundary missing")

    authority = load_authority_verifier()
    package = authority.load(ROOT / EXPECTED_PATHS["authority_package_path"])
    package_errors = authority.verify_package(package, require_authorized=False)
    if package_errors:
        fail("canonical authority package is invalid: " + "; ".join(package_errors))
    if package.get("authority_status") != "NOT_AUTHORIZED":
        fail("current readiness ledger cannot claim blocked authority while package is AUTHORIZED")

    template = authority.load(ROOT / EXPECTED_PATHS["authority_template_path"])
    template_errors = authority.verify_package(template, require_authorized=False)
    if template_errors:
        fail("authority template is invalid: " + "; ".join(template_errors))
    if template.get("authority_status") != "NOT_AUTHORIZED":
        fail("authority template must never ship as AUTHORIZED")
    if template.get("participant_count") != 0 or template.get("consent_records_sha256") is not None:
        fail("authority template must not contain participant or consent evidence")
    if template.get("authority_effective_before_recording") is not False:
        fail("authority template cannot claim pre-recording authority")

    verify_structure_proof()

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
    print("AUTHORITY_STRUCTURE=CANONICAL")
    print("PARTICIPANT_CONSENT_ATTESTATION=NO")
    print("B2_READY=NO")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
