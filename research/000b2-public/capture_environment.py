#!/usr/bin/env python3
"""Capture B2P07 public-lane execution-environment evidence without opening later gates."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT_STATE_REL = Path("research/000b2-public/predecode-attempt-state.json")
PREPROCESSING_REL = Path("research/000b2-public/preprocessing-capture.json")
READINESS_REL = Path("research/000b2-public/readiness.json")
ENV_CONTRACT_REL = Path("research/000b2-entry/environment/contract.json")
ENV_CAPTURE_PRIMITIVE_REL = Path("research/000b2-entry/environment/capture.py")
ENV_VERIFY_PRIMITIVE_REL = Path("research/000b2-entry/environment/verify_capture.py")
CAPTURE_WORKFLOW_REL = Path(".github/workflows/internal-b2p07-environment-capture.yml")
CAPTURE_WORKFLOW_REVISION = "4211ba2eca5ffa8e49088a5ae432bd0da9b7177c"
CAPTURE_WORKFLOW_SHA256 = "53a5cf266c2b40b6286cca3498d6188ee6fa84041a32e11cdd1dfda49e0ddbeb"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-001"
ATTEMPT_CANONICAL_REVISION = "e8841a68a7e37c7e4dd26ff73fe2566661c468b0"
ATTEMPT_STATE_SHA256 = "2392ab6694ab56facd8eb1f00c095a5727e51cae90d6553e0eca32b7626a85de"
PREPROCESSING_EVIDENCE_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
B2P06_CANONICAL_MERGE = "3dceadd984ff307ce55745bf5f289890a2fac261"
B2P06_RECONCILIATION_MERGE = "a45e69f3f03094c947104438ac1f0b2aa124b295"
RAW_CAPTURE_SCHEMA_VERSION = "000b2-public-environment-capture-v1"
SEALED_CAPTURE_SCHEMA_VERSION = "000b2-public-environment-capture-v2"
RECORDED_CAPTURE_JOB_ID = 100981596254
RECORDED_ARTIFACT_ID = 9931671160
RECORDED_ARTIFACT_NAME = "b2p07-environment-4211ba2eca5ffa8e49088a5ae432bd0da9b7177c"
RECORDED_ARTIFACT_ZIP_DIGEST = "sha256:ff527e3864159bdfb2199047306a0ead6387a5cc1b7748acc1de946753d77d9b"
RECORDED_PROVENANCE_STATUS = "RECORDED_GITHUB_API_METADATA_NOT_REQUERIED_BY_VERIFIER"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class CaptureError(RuntimeError):
    """Fail-closed B2P07 capture error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CaptureError(message)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CaptureError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_bytes(relative: Path) -> bytes:
    root = ROOT.resolve(strict=True)
    path = root / relative
    require(not path.is_symlink(), f"symlink forbidden for authority input: {relative}")
    resolved = path.resolve(strict=True)
    require(resolved.is_relative_to(root), f"authority input escapes repository: {relative}")
    require(resolved.is_file(), f"authority input is not a regular file: {relative}")
    return resolved.read_bytes()


def load_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureError(f"invalid JSON in {label}: {exc}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def load_capture_primitive():
    path = ROOT / ENV_CAPTURE_PRIMITIVE_REL
    spec = importlib.util.spec_from_file_location("wispral_b2p07_environment_primitive", path)
    require(spec is not None and spec.loader is not None, "environment capture primitive cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_head() -> str:
    try:
        value = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise CaptureError(f"cannot resolve capture revision: {exc}") from exc
    require(SHA40_RE.fullmatch(value) is not None, "capture revision is malformed")
    return value


def positive_env_int(name: str) -> int:
    raw = os.environ.get(name, "")
    require(raw.isdigit() and int(raw) > 0, f"{name} missing or malformed")
    return int(raw)


def seal_recorded_github_provenance(evidence: dict[str, Any]) -> dict[str, Any]:
    """Add post-capture GitHub job/artifact metadata without changing captured payload fields."""
    require(evidence.get("schema_version") == RAW_CAPTURE_SCHEMA_VERSION, "raw capture schema drift before provenance seal")
    provenance = evidence.get("capture_provenance")
    require(isinstance(provenance, dict), "raw capture provenance missing before seal")
    require(
        set(provenance)
        == {
            "repository_revision",
            "event_name",
            "github_run_id",
            "github_run_attempt",
            "github_job",
            "workflow_name",
            "github_ref",
            "capture_kind",
        },
        "raw capture provenance keys drift before seal",
    )
    sealed = json.loads(json.dumps(evidence))
    sealed["schema_version"] = SEALED_CAPTURE_SCHEMA_VERSION
    sealed_provenance = sealed["capture_provenance"]
    sealed_provenance.update(
        {
            "github_job_id": RECORDED_CAPTURE_JOB_ID,
            "artifact_id": RECORDED_ARTIFACT_ID,
            "artifact_name": RECORDED_ARTIFACT_NAME,
            "artifact_zip_digest": RECORDED_ARTIFACT_ZIP_DIGEST,
            "provenance_status": RECORDED_PROVENANCE_STATUS,
        }
    )
    return sealed


def verify_authority(*, allow_reconciled: bool = False) -> dict[str, Any]:
    """Verify the canonical B2P07 entry frontier and return exact authority identities."""
    attempt_raw = safe_bytes(ATTEMPT_STATE_REL)
    preprocessing_raw = safe_bytes(PREPROCESSING_REL)
    readiness_raw = safe_bytes(READINESS_REL)
    contract_raw = safe_bytes(ENV_CONTRACT_REL)
    primitive_raw = safe_bytes(ENV_CAPTURE_PRIMITIVE_REL)
    primitive_verify_raw = safe_bytes(ENV_VERIFY_PRIMITIVE_REL)

    require(sha256_bytes(attempt_raw) == ATTEMPT_STATE_SHA256, "public predecode attempt-state bytes drift")
    require(sha256_bytes(preprocessing_raw) == PREPROCESSING_EVIDENCE_SHA256, "canonical B2P06 preprocessing evidence bytes drift")

    state = load_object(attempt_raw, "public predecode attempt state")
    require(state.get("schema_version") == "000b2-public-predecode-attempt-state-v1", "attempt-state schema drift")
    require(state.get("attempt_id") == ATTEMPT_ID, "attempt identity drift")
    require(state.get("canonical_wispral_revision") == ATTEMPT_CANONICAL_REVISION, "attempt canonical revision drift")
    require(state.get("phase") == "PRE_PRIMARY_CAPTURE", "attempt phase drift")
    require(state.get("primary_test_decoding_started") is False, "primary decoding started before B2P07")
    require(state.get("candidate_decoding_started") is False, "candidate decoding started before B2P07")

    preprocessing = load_object(preprocessing_raw, "canonical B2P06 preprocessing evidence")
    attempt = preprocessing.get("attempt")
    require(isinstance(attempt, dict), "B2P06 attempt binding missing")
    require(attempt.get("attempt_id") == ATTEMPT_ID, "B2P06 attempt identity drift")
    require(attempt.get("attempt_state_sha256") == ATTEMPT_STATE_SHA256, "B2P06 attempt-state binding drift")
    require(attempt.get("canonical_wispral_revision") == ATTEMPT_CANONICAL_REVISION, "B2P06 attempt revision drift")
    require(attempt.get("candidate_decoding_started") is False, "B2P06 evidence declares candidate decoding")
    require(attempt.get("primary_test_decoding_started") is False, "B2P06 evidence declares primary decoding")
    preprocessing_guards = preprocessing.get("claim_guards")
    require(isinstance(preprocessing_guards, dict), "B2P06 claim guards missing")
    require(preprocessing_guards.get("b2p07_execution_environment_captured") is False, "B2P06 evidence must predate B2P07 capture")
    require(preprocessing_guards.get("b2p08_attempt_manifest_frozen") is False, "B2P08 freeze occurred before B2P07")

    readiness = load_object(readiness_raw, "public readiness")
    require(readiness.get("state") == "READY", "public readiness must remain READY")
    completed_through = readiness.get("completed_through")
    public = readiness.get("public_human_baseline")
    preprocessing_state = readiness.get("preprocessing")
    environment_state = readiness.get("execution_environment")
    attempt_state = readiness.get("attempt_manifest")
    guards = readiness.get("claim_guards")
    require(isinstance(public, dict) and public.get("candidate_decoding_started") is False, "candidate decoding must remain closed")
    require(isinstance(preprocessing_state, dict) and preprocessing_state.get("resolved") is True, "B2P06 preprocessing must be resolved")
    require(isinstance(environment_state, dict), "execution environment readiness missing")
    require(environment_state.get("hosted_runner_performance_mode") == "DIAGNOSTIC_ONLY", "hosted-runner policy drift")
    require(isinstance(attempt_state, dict), "attempt-manifest readiness missing")
    require(attempt_state.get("primary_decoding_started") is False, "primary decoding started before B2P07")
    require(isinstance(guards, dict), "claim guards missing")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(guards.get("production_stt_selected") is False, "production STT selected before B2P07")
    require(guards.get("product_code_authorized") is False, "product code authorized before B2P07")
    next_action = readiness.get("next_action")
    if completed_through == "B2P06":
        require(attempt_state.get("frozen") is False, "B2P08 attempt must remain unfrozen at the B2P06 frontier")
        require(environment_state.get("resolved") is False, "B2P07 readiness must remain unresolved until canonical reconciliation")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P07 only:"), "B2P07 is not the sole authorized next action")
        require("Do not begin B2P08 attempt freeze or candidate decoding until B2P07 is canonical." in next_action, "B2P07 successor boundary drift")
    elif allow_reconciled and completed_through in {"B2P07", "B2P08", "B2E01"}:
        require(environment_state.get("resolved") is True, "later reconciliation must preserve B2P07 environment resolution")
        if completed_through == "B2P07":
            require(attempt_state.get("frozen") is False, "B2P08 attempt froze before B2P08 reconciliation")
            require(isinstance(next_action, str) and next_action.startswith("Execute B2P08 only:"), "B2P07 reconciliation must authorize B2P08 only")
            require("Do not begin candidate or primary decoding until B2P08 is canonical." in next_action, "B2P08 successor boundary drift")
        elif completed_through == "B2P08":
            require(attempt_state.get("frozen") is True, "B2P08 reconciliation must mark attempt frozen")
            require(isinstance(next_action, str) and next_action.startswith("Execute B2E01 only:"), "B2P08 reconciliation must authorize B2E01 only")
            require("Do not begin B2E02 or any later candidate cell until B2E01 is canonical." in next_action, "B2E01 successor boundary drift")
        else:
            require(attempt_state.get("frozen") is True, "post-B2E01 reconciliation must preserve the frozen attempt")
            require(isinstance(next_action, str) and next_action.startswith("Execute B2E02 only:"), "B2E01 reconciliation must authorize B2E02 only")
            require("Do not begin B2E03 or any later candidate cell until B2E02 is canonical." in next_action, "B2E02 successor boundary drift")
    else:
        raise CaptureError(f"B2P07 authority phase unsupported: completed_through={completed_through!r}, allow_reconciled={allow_reconciled}")

    contract = load_object(contract_raw, "environment contract")
    policy = contract.get("performance_claim_policy")
    require(isinstance(policy, dict), "environment performance policy missing")
    require(policy.get("github_hosted_runner") == "DIAGNOSTIC_ONLY", "environment hosted-runner policy drift")
    require(policy.get("controlled_required_for_comparative_performance") is True, "controlled-performance requirement drift")
    require(policy.get("comparative_performance_authorized_by_this_contract") is False, "environment contract unexpectedly authorizes comparative performance")

    return {
        "attempt_state_path": str(ATTEMPT_STATE_REL),
        "attempt_state_sha256": ATTEMPT_STATE_SHA256,
        "preprocessing_evidence_path": str(PREPROCESSING_REL),
        "preprocessing_evidence_sha256": PREPROCESSING_EVIDENCE_SHA256,
        "b2p06_canonical_merge": B2P06_CANONICAL_MERGE,
        "b2p06_reconciliation_merge": B2P06_RECONCILIATION_MERGE,
        "environment_contract_path": str(ENV_CONTRACT_REL),
        "environment_contract_sha256": sha256_bytes(contract_raw),
        "capture_primitive_path": str(ENV_CAPTURE_PRIMITIVE_REL),
        "capture_primitive_sha256": sha256_bytes(primitive_raw),
        "capture_primitive_verifier_path": str(ENV_VERIFY_PRIMITIVE_REL),
        "capture_primitive_verifier_sha256": sha256_bytes(primitive_verify_raw),
        "capture_workflow_path_at_revision": str(CAPTURE_WORKFLOW_REL),
        "capture_workflow_sha256": CAPTURE_WORKFLOW_SHA256,
    }


def capture_public_environment() -> dict[str, Any]:
    authority = verify_authority()
    revision = git_head()
    expected_revision = os.environ.get("B2P07_REVISION")
    require(expected_revision == revision, "B2P07 exact revision environment does not match checkout")
    require(os.environ.get("GITHUB_ACTIONS", "").lower() == "true", "B2P07 canonical capture must execute in GitHub Actions")
    require(os.environ.get("RUNNER_ENVIRONMENT", "").lower() != "self-hosted", "this bounded B2P07 capture is intended for GitHub-hosted DIAGNOSTIC evidence")

    primitive = load_capture_primitive()
    attempt_raw = safe_bytes(ATTEMPT_STATE_REL)
    try:
        environment = primitive.capture(attempt_raw, "DIAGNOSTIC")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise CaptureError(f"environment primitive failed: {exc}") from exc

    require(environment.get("performance_mode") == "DIAGNOSTIC", "hosted capture did not remain DIAGNOSTIC")
    runner = environment.get("runner")
    require(isinstance(runner, dict) and runner.get("github_actions") is True and runner.get("github_hosted") is True, "capture was not identified as GitHub-hosted")
    require(environment.get("comparative_performance_authorized") is False, "hosted capture cannot authorize comparative performance")

    provenance = {
        "repository_revision": revision,
        "event_name": os.environ.get("GITHUB_EVENT_NAME"),
        "github_run_id": positive_env_int("GITHUB_RUN_ID"),
        "github_run_attempt": positive_env_int("GITHUB_RUN_ATTEMPT"),
        "github_job": os.environ.get("GITHUB_JOB"),
        "workflow_name": os.environ.get("GITHUB_WORKFLOW"),
        "github_ref": os.environ.get("GITHUB_REF"),
        "capture_kind": "GITHUB_HOSTED_DIAGNOSTIC",
    }
    require(provenance["event_name"] == "push", "canonical B2P07 evidence capture must originate from a push run")
    require(isinstance(provenance["github_job"], str) and provenance["github_job"], "GITHUB_JOB missing")
    require(isinstance(provenance["workflow_name"], str) and provenance["workflow_name"], "GITHUB_WORKFLOW missing")

    return {
        "schema_version": RAW_CAPTURE_SCHEMA_VERSION,
        "task": "B2P07",
        "lane": "PUBLIC_CORPUS",
        "authority": authority,
        "capture_provenance": provenance,
        "environment": environment,
        "claim_guards": {
            "performance_mode": "DIAGNOSTIC",
            "comparative_performance_authorized": False,
            "b2p08_attempt_manifest_frozen": False,
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = capture_public_environment()
    except (CaptureError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"B2P07_PUBLIC_ENVIRONMENT_CAPTURE=FAIL: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("B2P07_PUBLIC_ENVIRONMENT_CAPTURE=PASS")
    print(f"B2P07_CAPTURE_REVISION={evidence['capture_provenance']['repository_revision']}")
    print(f"B2P07_CAPTURE_RUN_ID={evidence['capture_provenance']['github_run_id']}")
    print(f"B2P07_ENVIRONMENT_ID={evidence['environment']['environment_id']}")
    print("B2P07_PERFORMANCE_MODE=DIAGNOSTIC")
    print("B2P07_COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
    print("B2P08_ATTEMPT_MANIFEST_FROZEN=NO")
    print("CANDIDATE_DECODING_STARTED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
