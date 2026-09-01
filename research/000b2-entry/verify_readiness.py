#!/usr/bin/env python3
"""Fail-closed verifier for the current 000B2 entry-readiness ledger."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "000b2-entry"
READINESS = HERE / "readiness.json"
CLOSEOUT = HERE / "canonical-closeout.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
PREPARATION_START_MAIN = "db0a10ab4c9ee2436a5b921d0ff8af96f58cef38"
ENTRY_EVIDENCE_MERGE = "49d0f31408ab36f285f5e61228b54a72ca0aec07"
QUALIFIED_CANDIDATE_HEAD = "69b66bc433a146c2146e2b7fec264a8f4ed50ae9"
TRUSTED_BASE_SHA = "248208cffa666a485fe58b7467fdbb2ec7e8b820"
TRUSTED_RUN_ID = 33537242680
TRUSTED_JOB_ID = 99954441750
EXPECTED_BLOCKERS = {
    "human developer-speech participant/media authority is absent",
    "authorized human corpus, consent records, speaker-disjoint split manifests, and frozen primary test manifest are absent",
    "accepted attempt-bound FFmpeg 9.0.1 binary/version/config identity and preprocessing execution evidence is absent",
    "accepted attempt-bound execution environment and hardware fingerprint evidence is absent",
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
EXPECTED_FILES = {
    "materialization evidence": "research/000b2-entry/materialized-artifacts.json",
    "artifact amendment": "research/000b2-entry/artifact-size-amendment.json",
    "operational smoke evidence": "research/000b2-entry/operational-smoke-evidence.json",
    "scorer implementation_path": "research/000b2-entry/scorer.py",
    "scorer config_path": "research/000b2-entry/scorer-config.json",
    "scorer verifier_path": "research/000b2-entry/verify_scorer.py",
    "preprocessing contract": "research/000b2-entry/preprocessing/contract.json",
    "preprocessing capture tool": "research/000b2-entry/preprocessing/capture.py",
    "environment contract": "research/000b2-entry/environment/contract.json",
    "environment capture tool": "research/000b2-entry/environment/capture.py",
    "attempt manifest generator": "research/000b2-entry/prepare_attempt_manifest.py",
    "attempt manifest validator": "research/000b2-entry/validate_entry_manifest.py",
}
CONTENT_VERIFIERS = {
    "research/000b2-entry/verify_materialization.py": "VERIFY_000B2_MATERIALIZATION=PASS",
    "research/000b2-entry/verify_operational_smoke.py": "VERIFY_000B2_OPERATIONAL_SMOKE=PASS",
    "research/000b2-entry/verify_scorer.py": "VERIFY_000B2_SCORER=PASS",
}
STALE_BLOCKER_TEXT = (
    "Moonshine payload SHA-256 materialization remains incomplete",
    "sherpa-onnx `tokens.txt` SHA-256 materialization remains incomplete",
    "each selected candidate still needs bounded non-primary operational smoke PASS",
    "scorer implementation/revision/configuration is not frozen",
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def require_file(relative: Any, label: str) -> Path:
    expected = EXPECTED_FILES.get(label)
    if expected is None:
        fail(f"readiness verifier has no allowlisted path for {label}")
    if not isinstance(relative, str) or relative != expected:
        fail(f"{label} path drift: expected {expected!r}, got {relative!r}")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        fail(f"{label} path escapes repository root: {relative}")
    path = ROOT / rel
    if path.is_symlink():
        fail(f"{label} must not be a symlink: {relative}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        fail(f"{label} missing: {relative}: {exc}")
    root_resolved = ROOT.resolve(strict=True)
    if not resolved.is_relative_to(root_resolved) or not resolved.is_file():
        fail(f"{label} is not a regular repository file: {relative}")
    return resolved


def run_content_verifier(relative: str) -> None:
    marker = CONTENT_VERIFIERS.get(relative)
    if marker is None:
        fail(f"content verifier is not allowlisted: {relative}")
    path = ROOT / relative
    if path.is_symlink() or not path.is_file():
        fail(f"content verifier missing or symlinked: {relative}")
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    if proc.returncode != 0 or marker not in proc.stdout.splitlines():
        detail = proc.stdout.strip() or f"exit={proc.returncode}"
        fail(f"content verifier failed for {relative}: {detail}")


def require_gate(gates: dict[str, Any], name: str) -> dict[str, Any]:
    gate = gates.get(name)
    if not isinstance(gate, dict):
        fail(f"readiness gate missing or malformed: {name}")
    return gate


def verify_closeout() -> None:
    closeout = load(CLOSEOUT)
    if not isinstance(closeout, dict):
        fail("entry closeout must be an object")
    if closeout.get("schema_version") != "000b2-entry-closeout-v1":
        fail("entry closeout schema drift")
    if closeout.get("recorded_date") != "2026-09-01":
        fail("entry closeout date drift")
    if closeout.get("disposition") != "BLOCKED_EXTERNAL" or closeout.get("b2_ready") is not False:
        fail("entry closeout must preserve B2 BLOCKED_EXTERNAL")
    if closeout.get("primary_test_decoding_authorized") is not False:
        fail("entry closeout cannot authorize primary decoding")
    if closeout.get("entry_preparation_evidence_merge") != ENTRY_EVIDENCE_MERGE:
        fail("entry closeout evidence merge drift")
    if closeout.get("qualified_candidate_head") != QUALIFIED_CANDIDATE_HEAD:
        fail("entry closeout qualified head drift")

    authority = closeout.get("trusted_authority_merges")
    if not isinstance(authority, dict):
        fail("entry closeout trusted authority missing")
    if authority.get("trusted_base_authority") != "32135294675a372653843560623067d9ad3822d6":
        fail("trusted-base authority merge drift")
    if authority.get("live_base_refresh_fix") != TRUSTED_BASE_SHA:
        fail("live-base refresh authority drift")

    proof = closeout.get("trusted_runtime_proof")
    if not isinstance(proof, dict):
        fail("entry closeout trusted runtime proof missing")
    expected_proof = {
        "workflow": "000B2 Trusted Materialization Authority",
        "run_id": TRUSTED_RUN_ID,
        "job_id": TRUSTED_JOB_ID,
        "trusted_base_sha": TRUSTED_BASE_SHA,
        "candidate_head_sha": QUALIFIED_CANDIDATE_HEAD,
        "artifact_identity_status": "PASS",
        "materialized_artifact_records": 18,
        "process_attestation": "NOT_PROVIDED_BY_THIS_GATE",
    }
    for key, expected in expected_proof.items():
        if proof.get(key) != expected:
            fail(f"entry closeout trusted proof drift: {key}")

    blockers = closeout.get("remaining_blockers")
    if not isinstance(blockers, list) or set(blockers) != EXPECTED_BLOCKERS:
        fail("entry closeout blocker set drift")
    if len(blockers) != len(set(blockers)):
        fail("entry closeout blockers contain duplicates")

    nonclaims = closeout.get("non_claims")
    if not isinstance(nonclaims, dict):
        fail("entry closeout non-claims missing")
    for field, expected in NONCLAIMS.items():
        if nonclaims.get(field) is not expected:
            fail(f"entry closeout non-claim drift: {field}")
    if nonclaims.get("stt_winner_selected") is not False:
        fail("entry closeout selected an STT winner")


def verify() -> None:
    record = load(READINESS)
    if not isinstance(record, dict):
        fail("readiness record must be an object")
    if record.get("schema_version") != "000b2-entry-readiness-v1":
        fail("readiness schema drift")
    if record.get("recorded_date") != "2026-09-01":
        fail("readiness recorded date drift")
    if record.get("canonical_main_at_preparation_start") != PREPARATION_START_MAIN:
        fail("preparation canonical main drift")
    if not SHA40.fullmatch(str(record.get("canonical_main_at_preparation_start", ""))):
        fail("preparation main is not a full lowercase Git SHA")
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
    if materialization.get("canonical_trusted_reproduction_run_id") != TRUSTED_RUN_ID:
        fail("canonical trusted materialization run drift")
    if materialization.get("canonical_trusted_base_sha") != TRUSTED_BASE_SHA:
        fail("canonical trusted materialization base drift")
    if materialization.get("canonical_candidate_head_sha") != QUALIFIED_CANDIDATE_HEAD:
        fail("canonical trusted materialization candidate drift")
    require_file(materialization.get("evidence_path"), "materialization evidence")
    require_file(materialization.get("factual_amendment_path"), "artifact amendment")
    run_content_verifier("research/000b2-entry/verify_materialization.py")

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
    require_file(smoke.get("evidence_path"), "operational smoke evidence")
    run_content_verifier("research/000b2-entry/verify_operational_smoke.py")

    scorer = require_gate(gates, "scorer")
    if scorer.get("status") != "CANONICAL":
        fail("scorer must be canonical after entry-preparation merge")
    if scorer.get("canonical_revision") != ENTRY_EVIDENCE_MERGE:
        fail("scorer canonical revision drift")
    if scorer.get("verification_baseline_workflow_run_id") != 33523779606:
        fail("scorer verification baseline provenance drift")
    if "latest_verified_workflow_run_id" in scorer:
        fail("self-updating latest-run scorer provenance was reintroduced")
    note = scorer.get("note")
    if not isinstance(note, str) or "became canonical" not in note:
        fail("scorer canonical semantics missing")
    for key in ("implementation_path", "config_path", "verifier_path"):
        require_file(scorer.get(key), f"scorer {key}")
    run_content_verifier("research/000b2-entry/verify_scorer.py")

    preprocessing = require_gate(gates, "preprocessing")
    if preprocessing.get("status") != "SAME_ATTEMPT_CAPTURE_REQUIRED" or preprocessing.get("resolved") is not False:
        fail("preprocessing must remain unresolved pending accepted attempt evidence")
    if preprocessing.get("required_tool") != "FFmpeg 9.0.1":
        fail("preprocessing tool drift")
    require_file(preprocessing.get("contract_path"), "preprocessing contract")
    require_file(preprocessing.get("capture_tool_path"), "preprocessing capture tool")

    environment = require_gate(gates, "execution_environment")
    if environment.get("status") != "SAME_ATTEMPT_CAPTURE_REQUIRED" or environment.get("resolved") is not False:
        fail("execution environment must remain unresolved pending accepted attempt evidence")
    if environment.get("github_hosted_performance_mode") != "DIAGNOSTIC_ONLY":
        fail("hosted-runner performance boundary drift")
    require_file(environment.get("contract_path"), "environment contract")
    require_file(environment.get("capture_tool_path"), "environment capture tool")

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
    require_file(manifest.get("generator_path"), "attempt manifest generator")
    require_file(manifest.get("validator_path"), "attempt manifest validator")

    next_action = record.get("next_action")
    if not isinstance(next_action, str) or "Do not execute B2 primary human-speech decoding" not in next_action:
        fail("readiness next action no longer fails closed")

    verify_closeout()

    current = (ROOT / "specs" / "CURRENT.md").read_text(encoding="utf-8")
    if "`000B2-unbiased-stt-bakeoff`\n\nState: `BLOCKED_EXTERNAL`" not in current:
        fail("canonical CURRENT.md no longer records B2 BLOCKED_EXTERNAL")
    for stale in STALE_BLOCKER_TEXT:
        if stale in current:
            fail(f"canonical CURRENT.md retains resolved blocker: {stale}")

    current_state = (ROOT / "docs" / "canonical" / "CURRENT_STATE.md").read_text(encoding="utf-8")
    for stale in STALE_BLOCKER_TEXT:
        if stale in current_state:
            fail(f"canonical CURRENT_STATE.md retains resolved blocker: {stale}")


def main() -> int:
    try:
        verify()
    except (
        AssertionError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"VERIFY_000B2_ENTRY_READINESS=FAIL: {exc}", file=sys.stderr)
        return 1
    print("VERIFY_000B2_ENTRY_READINESS=PASS")
    print("ENTRY_PREPARATION=CLOSED_CANONICAL")
    print("SCORER=CANONICAL")
    print("B2_DISPOSITION=BLOCKED_EXTERNAL")
    print("B2_READY=NO")
    print("PRIMARY_TEST_DECODING=NO")
    print("HUMAN_SPEECH_ENTRY_PREPARATION=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
