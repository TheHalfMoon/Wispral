#!/usr/bin/env python3
"""Qualify the pre-merge B2R13 recovery activation without fabricating post-merge state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import verify_attempt_002_invalidation as proof

ROOT = Path(__file__).resolve().parents[2]
READINESS = ROOT / "research/000b2-public/recovery-attempt-003-readiness.json"
TASKS = ROOT / "specs/000B2-public-corpus-bakeoff/recovery-v2-tasks.md"
CURRENT = ROOT / "specs/CURRENT.md"
TASK_ORDER = proof.TASK_ORDER


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"B2R13_ACTIVATION=FAIL: {message}")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} root must be an object")
    return value


def verify_activation_frontier() -> None:
    readiness = load(READINESS)
    require(readiness.get("schema_version") == "000b2-public-attempt-003-recovery-readiness-v1", "successor readiness schema drift")
    require(readiness.get("state") == "RECOVERY_READY", "successor recovery must be RECOVERY_READY")
    require(readiness.get("task_order") == TASK_ORDER, "successor recovery task order drift")
    require(readiness.get("task_content_policies") == proof.expected_task_content_policies(), "successor task content policy drift")
    require(readiness.get("completed_recovery_tasks") == [], "B2R13 activation candidate must not pre-complete recovery tasks")
    require(readiness.get("active_recovery_unit") == "B2R13", "B2R13 must be the sole active successor unit")
    require(readiness.get("transition_proofs") == [], "B2R13 activation candidate must not fabricate transition proofs")

    historical = readiness.get("historical_recovery_snapshot")
    require(isinstance(historical, dict), "historical recovery snapshot must be an object")
    require(historical.get("completed_through") == "B2R09", "historical ATTEMPT-002 snapshot completion drift")
    require(historical.get("active_unit_at_invalidation") == "B2R10", "historical ATTEMPT-002 active-unit drift")
    require(historical.get("active_execution_authority") is False, "legacy ATTEMPT-002 state must not retain execution authority")

    invalidated = readiness.get("invalidated_attempt")
    require(isinstance(invalidated, dict), "invalidated_attempt must be an object")
    require(invalidated.get("attempt_id") == proof.ATTEMPT_ID, "invalidated attempt id drift")
    require(invalidated.get("comparative_scoring_eligible") is False, "ATTEMPT-002 scoring must remain closed")
    require(invalidated.get("candidate_superiority_claim_eligible") is False, "ATTEMPT-002 superiority claims must remain closed")
    require(invalidated.get("new_primary_decode_authorized") is False, "ATTEMPT-002 new primary decode must remain closed")

    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict), "replacement_attempt must be an object")
    require(replacement.get("attempt_id") == proof.ATTEMPT_003_ID, "replacement attempt id drift")
    require(replacement.get("required") is True, "ATTEMPT-003 must be required")
    require(replacement.get("frozen") is False, "ATTEMPT-003 must not be frozen during B2R13 activation")
    require(replacement.get("primary_decode_entry_open") is False, "ATTEMPT-003 primary decode must remain closed during B2R13 activation")

    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "claim_guards must be an object")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(guards.get("comparative_result_available") is False, "comparative result must remain unavailable")
    require(guards.get("production_stt_selected") is False, "production STT must remain unselected")
    require(guards.get("product_code_authorized") is False, "product code must remain unauthorized")

    ledger = proof.parse_task_ledger(TASKS.read_text(encoding="utf-8"))
    require([task for task, _ in ledger] == TASK_ORDER, "successor task ledger membership/order drift")
    require(not any(checked for _, checked in ledger), "B2R13 activation task ledger must remain entirely unchecked before reconciliation")

    current = CURRENT.read_text(encoding="utf-8")
    for marker in (
        "**ATTEMPT-002 status:** `INVALIDATED_MATERIAL_EXECUTION_DRIFT`",
        "**Successor recovery authority:** `specs/000B2-public-corpus-bakeoff/recovery-v2.md`",
        "**Active successor recovery unit:** `B2R13`",
        "**ATTEMPT-003 frozen:** `false`",
        "**ATTEMPT-003 primary decode entry open:** `false`",
    ):
        require(marker in current, f"specs/CURRENT.md missing activation marker: {marker}")

    require("`000B2-unbiased-stt-bakeoff`\n\nState: `BLOCKED_EXTERNAL`" in current, "historical private B2 blocker must remain present")
    require("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT" in current, "human evidence absence marker must remain present")
    require("production_stt_selected=false" in current, "production selection guard must remain present")
    require("product_code_authorized=false" in current, "product-code guard must remain present")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sherpa-source", type=Path)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    require(not (args.static_only and args.sherpa_source), "choose either --static-only or --sherpa-source")

    proof.verify_historical_bytes()
    proof.verify_attempt_manifest()
    proof.verify_b2r09_binding()
    proof.verify_invalidation_record()
    verify_activation_frontier()

    if args.sherpa_source is not None:
        proof.verify_sherpa_source(args.sherpa_source.resolve())
        print("SHERPA_PINNED_API=PASS")
    else:
        require(args.static_only, "use --sherpa-source for pinned-source proof or --static-only for bounded offline structure verification")
        print("SHERPA_PINNED_API=NOT_RUN_STATIC_ONLY")

    print("B2R13_ACTIVATION=PASS")
    print("ATTEMPT_002_INVALIDATION=PASS")
    print("ATTEMPT_002_HISTORICAL_BYTES=PASS")
    print("ACTIVE_SUCCESSOR_RECOVERY_UNIT=B2R13")
    print("ATTEMPT_003_PRIMARY_DECODE_AUTHORIZED=NO")
    print("COMPARATIVE_RESULT_AVAILABLE=NO")
    print("PRODUCTION_STT_SELECTED=NO")
    print("PRODUCT_CODE_AUTHORIZED=NO")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")


if __name__ == "__main__":
    main()
