#!/usr/bin/env python3
"""Fail-closed verifier for the current 000B2 entry-readiness ledger."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "000b2-entry"
READINESS = HERE / "readiness.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_MAIN = "db0a10ab4c9ee2436a5b921d0ff8af96f58cef38"
EXPECTED_BLOCKERS = {
    "human developer-speech participant/media authority is absent",
    "authorized human corpus, consent records, speaker-disjoint split manifests, and frozen primary test manifest are absent",
    "scorer canonical revision is pending entry-preparation merge",
    "same-attempt FFmpeg 9.0.1 binary/version/config capture is absent",
    "same-attempt execution environment and hardware fingerprint are absent",
    "final B2 attempt manifest is not frozen",
}
NONCLAIMS = {
    "primary_test_decoding_performed": False,
    "human_speech_used_in_entry_preparation": False,
    "comparative_ranking_present": False,
    "accuracy_claim_present": False,
    "performance_claim_present": False,
    "product_runtime_or_product_code_added": False,
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def require_file(relative: str, label: str) -> Path:
    path = ROOT / relative
    if not path.is_file():
        fail(f"{label} missing: {relative}")
    return path


def require_gate(gates: dict[str, Any], name: str) -> dict[str, Any]:
    gate = gates.get(name)
    if not isinstance(gate, dict):
        fail(f"readiness gate missing or malformed: {name}")
    return gate


def verify() -> None:
    record = load(READINESS)
    if not isinstance(record, dict):
        fail("readiness record must be an object")
    if record.get("schema_version") != "000b2-entry-readiness-v1":
        fail("readiness schema drift")
    if record.get("recorded_date") != "2026-09-01":
        fail("readiness recorded date drift")
    if record.get("canonical_main_at_preparation_start") != EXPECTED_MAIN:
        fail("preparation canonical main drift")
    if not SHA40.fullmatch(str(record.get("canonical_main_at_preparation_start", ""))):
        fail("canonical main is not a full lowercase Git SHA")
    if record.get("b1_disposition") != "VERIFIED":
        fail("B1 must remain VERIFIED")
    if record.get("b2_disposition") != "BLOCKED_EXTERNAL" or record.get("b2_ready") is not False:
        fail("B2 must remain BLOCKED_EXTERNAL and not ready")
    for field, expected in NONCLAIMS.items():
        if record.get(field) is not expected:
            fail(f"non-claim drift: {field}")

    blockers = record.get("remaining_blockers")
    if not isinstance(blockers, list) or len(blockers) != len(EXPECTED_BLOCKERS):
        fail("remaining blocker list cardinality drift")
    if any(not isinstance(item, str) for item in blockers) or set(blockers) != EXPECTED_BLOCKERS:
        fail("remaining blocker set drift")
    if len(set(blockers)) != len(blockers):
        fail("remaining blocker list contains duplicates")

    gates = record.get("gates")
    if not isinstance(gates, dict):
        fail("readiness gates missing")
    if set(gates) != {
        "artifact_materialization",
        "operational_qualification",
        "scorer",
        "preprocessing",
        "execution_environment",
        "human_developer_speech_authority",
        "human_corpus_and_splits",
        "attempt_manifest",
    }:
        fail("readiness gate allowlist drift")

    materialization = require_gate(gates, "artifact_materialization")
    if materialization.get("status") != "RESOLVED":
        fail("artifact materialization must be resolved")
    if materialization.get("workflow_run_id") != 33519579512:
        fail("artifact materialization run drift")
    if materialization.get("workflow_head_sha") != "3d4325b7c9b13e6696326f3d2c8a6cfe501d9e12":
        fail("artifact materialization head drift")
    require_file(str(materialization.get("evidence_path")), "materialization evidence")
    require_file(str(materialization.get("factual_amendment_path")), "artifact amendment")

    smoke = require_gate(gates, "operational_qualification")
    if smoke.get("status") != "RESOLVED_SMOKE_PASS":
        fail("operational qualification must be a bounded smoke PASS")
    if smoke.get("workflow_run_id") != 33522881549:
        fail("operational smoke run drift")
    if smoke.get("workflow_head_sha") != "3cdaea6f0c5867a9595e70c50c130f375b25ac2c":
        fail("operational smoke head drift")
    if smoke.get("candidate_cells") != 6:
        fail("operational smoke must cover exactly six candidate cells")
    if smoke.get("input_class") != "DETERMINISTIC_SYNTHETIC_NON_SPEECH":
        fail("operational smoke input class drift")
    if smoke.get("primary_ranking_eligible") is not False:
        fail("operational smoke cannot become primary-ranking evidence")
    require_file(str(smoke.get("evidence_path")), "operational smoke evidence")

    scorer = require_gate(gates, "scorer")
    if scorer.get("status") != "CANONICAL_REVISION_PENDING_MERGE":
        fail("scorer must remain pending canonical merge")
    if scorer.get("verification_baseline_workflow_run_id") != 33523779606:
        fail("scorer verification baseline provenance drift")
    if "latest_verified_workflow_run_id" in scorer:
        fail("self-updating latest-run scorer provenance was reintroduced")
    note = scorer.get("note")
    if not isinstance(note, str) or "stable verification baseline" not in note:
        fail("scorer verification baseline semantics missing")
    for key in ("implementation_path", "config_path", "verifier_path"):
        require_file(str(scorer.get(key)), f"scorer {key}")

    preprocessing = require_gate(gates, "preprocessing")
    if preprocessing.get("status") != "SAME_ATTEMPT_CAPTURE_REQUIRED" or preprocessing.get("resolved") is not False:
        fail("preprocessing must remain unresolved pending same-attempt capture")
    if preprocessing.get("required_tool") != "FFmpeg 9.0.1":
        fail("preprocessing tool drift")
    require_file(str(preprocessing.get("contract_path")), "preprocessing contract")
    require_file(str(preprocessing.get("capture_tool_path")), "preprocessing capture tool")

    environment = require_gate(gates, "execution_environment")
    if environment.get("status") != "SAME_ATTEMPT_CAPTURE_REQUIRED" or environment.get("resolved") is not False:
        fail("execution environment must remain unresolved pending same-attempt capture")
    if environment.get("github_hosted_performance_mode") != "DIAGNOSTIC_ONLY":
        fail("hosted-runner performance boundary drift")
    require_file(str(environment.get("contract_path")), "environment contract")
    require_file(str(environment.get("capture_tool_path")), "environment capture tool")

    human = require_gate(gates, "human_developer_speech_authority")
    if human.get("status") != "BLOCKED_EXTERNAL" or human.get("resolved") is not False:
        fail("human developer-speech authority must remain external and unresolved")
    required = human.get("required")
    if not isinstance(required, list) or len(required) < 8:
        fail("human authority requirements were weakened")

    corpus = require_gate(gates, "human_corpus_and_splits")
    if corpus.get("status") != "BLOCKED_EXTERNAL" or corpus.get("resolved") is not False:
        fail("human corpus gate must remain external and unresolved")
    if corpus.get("requires_human_authority_first") is not True:
        fail("human corpus gate lost authority dependency")

    manifest = require_gate(gates, "attempt_manifest")
    if manifest.get("status") != "NOT_FROZEN" or manifest.get("frozen") is not False:
        fail("attempt manifest must remain not frozen")
    if manifest.get("primary_test_decoding_started") is not False:
        fail("primary decoding started before readiness")
    require_file(str(manifest.get("generator_path")), "attempt manifest generator")
    require_file(str(manifest.get("validator_path")), "attempt manifest validator")

    next_action = record.get("next_action")
    if not isinstance(next_action, str) or "Do not execute B2 primary human-speech decoding" not in next_action:
        fail("readiness next action no longer fails closed")

    current = (ROOT / "specs" / "CURRENT.md").read_text(encoding="utf-8")
    if "`000B2-unbiased-stt-bakeoff`\n\nState: `BLOCKED_EXTERNAL`" not in current:
        fail("canonical CURRENT.md no longer records B2 BLOCKED_EXTERNAL")


def main() -> int:
    try:
        verify()
    except (AssertionError, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"VERIFY_000B2_ENTRY_READINESS=FAIL: {exc}", file=sys.stderr)
        return 1
    print("VERIFY_000B2_ENTRY_READINESS=PASS")
    print("B2_DISPOSITION=BLOCKED_EXTERNAL")
    print("B2_READY=NO")
    print("PRIMARY_TEST_DECODING=NO")
    print("HUMAN_SPEECH_ENTRY_PREPARATION=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())