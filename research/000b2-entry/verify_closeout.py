#!/usr/bin/env python3
"""Fail-closed verifier for the canonical 000B2 entry-preparation closeout."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "000b2-entry"
CLOSEOUT = HERE / "canonical-closeout.json"
READINESS = HERE / "readiness.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

ENTRY_EVIDENCE_MERGE = "49d0f31408ab36f285f5e61228b54a72ca0aec07"
QUALIFIED_CANDIDATE_HEAD = "69b66bc433a146c2146e2b7fec264a8f4ed50ae9"
TRUSTED_BASE_AUTHORITY = "32135294675a372653843560623067d9ad3822d6"
LIVE_BASE_REFRESH_FIX = "248208cffa666a485fe58b7467fdbb2ec7e8b820"

EXPECTED_TOP_LEVEL = {
    "schema_version",
    "recorded_date",
    "disposition",
    "b2_ready",
    "primary_test_decoding_authorized",
    "entry_preparation_evidence_merge",
    "qualified_candidate_head",
    "exact_head_qualification",
    "trusted_authority_merges",
    "trusted_runtime_proof",
    "review_reconciliation",
    "resolved_entry_gates",
    "prepared_but_not_attempt_evidence",
    "remaining_blockers",
    "non_claims",
    "next_action",
}

EXPECTED_EXACT_HEAD_QUALIFICATION = {
    "entry_materialization_run_id": 33535368632,
    "entry_contracts_run_id": 33535368635,
    "operational_smoke_run_id": 33535368633,
    "preprocessing_toolchain_run_id": 33535368733,
}
EXPECTED_TRUSTED_AUTHORITY = {
    "trusted_base_authority": TRUSTED_BASE_AUTHORITY,
    "live_base_refresh_fix": LIVE_BASE_REFRESH_FIX,
}
EXPECTED_TRUSTED_RUNTIME = {
    "workflow": "000B2 Trusted Materialization Authority",
    "run_id": 33537242680,
    "job_id": 99954441750,
    "trusted_base_sha": LIVE_BASE_REFRESH_FIX,
    "candidate_head_sha": QUALIFIED_CANDIDATE_HEAD,
    "artifact_identity_status": "PASS",
    "materialized_artifact_records": 18,
    "process_attestation": "NOT_PROVIDED_BY_THIS_GATE",
}
EXPECTED_REVIEW_RECONCILIATION = {
    "independent_findings_present": True,
    "all_findings_reconciled": True,
    "all_review_threads_resolved": True,
    "stale_review_represented_as_fresh_approval": False,
}
EXPECTED_RESOLVED_GATES = {
    "all B1-pending candidate artifact SHA-256 identities are materialized and canonically reproduced",
    "all six selected candidate cells have bounded deterministic synthetic non-speech SMOKE_PASS evidence",
    "scorer implementation, configuration, and verifier are canonical at the entry-preparation evidence merge",
}
EXPECTED_PREPARED_ONLY = {
    "FFmpeg 9.0.1 qualification and attempt-state-bound preprocessing capture tooling",
    "attempt-state-bound execution-environment capture tooling",
}
EXPECTED_BLOCKERS = {
    "human developer-speech participant/media authority is absent",
    "authorized human corpus, consent records, speaker-disjoint split manifests, and frozen primary test manifest are absent",
    "accepted attempt-bound FFmpeg 9.0.1 binary/version/config identity and preprocessing execution evidence is absent",
    "accepted attempt-bound execution environment and hardware fingerprint evidence is absent",
    "final B2 attempt manifest is not frozen",
}
EXPECTED_NONCLAIMS = {
    "primary_test_decoding_performed": False,
    "human_speech_used_in_entry_preparation": False,
    "comparative_ranking_present": False,
    "accuracy_claim_present": False,
    "performance_claim_present": False,
    "product_runtime_or_product_code_added": False,
    "stt_winner_selected": False,
}
EXPECTED_NEXT_ACTION = (
    "Preserve B2 as BLOCKED_EXTERNAL. Establish real participant/media authority and an authorized "
    "frozen human corpus first; then create a separately reviewable authorized attempt that captures "
    "preprocessing and execution-environment evidence before primary decoding, freezes the final "
    "manifest, and rechecks readiness from canonical main."
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def require_exact_mapping(value: Any, expected: dict[str, Any], label: str) -> None:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    if set(value) != set(expected):
        fail(f"{label} key set drift")
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def require_exact_string_set(value: Any, expected: set[str], label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        fail(f"{label} must be a string array")
    if len(value) != len(expected) or len(set(value)) != len(value) or set(value) != expected:
        fail(f"{label} set drift")


def verify() -> None:
    closeout = load(CLOSEOUT)
    if not isinstance(closeout, dict):
        fail("entry closeout must be an object")
    if set(closeout) != EXPECTED_TOP_LEVEL:
        fail("entry closeout top-level key set drift")
    if closeout.get("schema_version") != "000b2-entry-closeout-v1":
        fail("entry closeout schema drift")
    if closeout.get("recorded_date") != "2026-09-01":
        fail("entry closeout date drift")
    if closeout.get("disposition") != "BLOCKED_EXTERNAL" or closeout.get("b2_ready") is not False:
        fail("entry closeout must preserve B2 BLOCKED_EXTERNAL")
    if closeout.get("primary_test_decoding_authorized") is not False:
        fail("entry closeout cannot authorize primary decoding")

    evidence_merge = closeout.get("entry_preparation_evidence_merge")
    qualified_head = closeout.get("qualified_candidate_head")
    if evidence_merge != ENTRY_EVIDENCE_MERGE or not SHA40.fullmatch(str(evidence_merge)):
        fail("entry-preparation evidence merge drift")
    if qualified_head != QUALIFIED_CANDIDATE_HEAD or not SHA40.fullmatch(str(qualified_head)):
        fail("qualified candidate head drift")

    require_exact_mapping(
        closeout.get("exact_head_qualification"),
        EXPECTED_EXACT_HEAD_QUALIFICATION,
        "exact-head qualification",
    )
    require_exact_mapping(
        closeout.get("trusted_authority_merges"),
        EXPECTED_TRUSTED_AUTHORITY,
        "trusted authority merges",
    )
    require_exact_mapping(
        closeout.get("trusted_runtime_proof"),
        EXPECTED_TRUSTED_RUNTIME,
        "trusted runtime proof",
    )
    require_exact_mapping(
        closeout.get("review_reconciliation"),
        EXPECTED_REVIEW_RECONCILIATION,
        "review reconciliation",
    )
    require_exact_string_set(closeout.get("resolved_entry_gates"), EXPECTED_RESOLVED_GATES, "resolved entry gates")
    require_exact_string_set(
        closeout.get("prepared_but_not_attempt_evidence"),
        EXPECTED_PREPARED_ONLY,
        "prepared-but-not-attempt evidence",
    )
    require_exact_string_set(closeout.get("remaining_blockers"), EXPECTED_BLOCKERS, "remaining blockers")
    require_exact_mapping(closeout.get("non_claims"), EXPECTED_NONCLAIMS, "non-claims")
    if closeout.get("next_action") != EXPECTED_NEXT_ACTION:
        fail("entry closeout next action drift")

    readiness = load(READINESS)
    if not isinstance(readiness, dict):
        fail("readiness record must be an object")
    if readiness.get("b2_disposition") != "BLOCKED_EXTERNAL" or readiness.get("b2_ready") is not False:
        fail("readiness record disagrees with closeout disposition")
    require_exact_string_set(readiness.get("remaining_blockers"), EXPECTED_BLOCKERS, "readiness blockers")
    scorer = readiness.get("gates", {}).get("scorer")
    if not isinstance(scorer, dict) or scorer.get("status") != "CANONICAL":
        fail("readiness scorer is not canonical")
    if scorer.get("canonical_revision") != ENTRY_EVIDENCE_MERGE:
        fail("readiness scorer canonical revision drift")


def main() -> int:
    try:
        verify()
    except (AssertionError, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"VERIFY_000B2_ENTRY_CLOSEOUT=FAIL: {exc}", file=sys.stderr)
        return 1
    print("VERIFY_000B2_ENTRY_CLOSEOUT=PASS")
    print("ENTRY_PREPARATION=CLOSED_CANONICAL")
    print("B2_DISPOSITION=BLOCKED_EXTERNAL")
    print("PRIMARY_TEST_DECODING_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
