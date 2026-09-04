#!/usr/bin/env python3
"""Verify B2P07 public-lane execution-environment evidence and closed later gates."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CAPTURE_REL = Path("research/000b2-public/capture_environment.py")
COMMITTED_EVIDENCE_REL = Path("research/000b2-public/execution-environment.json")
EXPECTED_CAPTURE_COMMIT = "aa4711c083b652dfdb7a5d29a39a222125000131"
EXPECTED_CAPTURE_EVIDENCE_BLOB = "d84e3e55d45a937a09e5898727b60c635144ac5c"
EXPECTED_CAPTURE_RUN_ID = 33859864538
EXPECTED_CAPTURE_RUN_ATTEMPT = 1
EXPECTED_CAPTURE_JOB = "capture-b2p07-environment"
EXPECTED_CAPTURE_WORKFLOW_NAME = "Internal B2P07 Public Environment Capture"
EXPECTED_CAPTURE_REF = "refs/heads/research/000b2-b2p07-environment-capture"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class VerificationError(RuntimeError):
    """Fail-closed B2P07 verification error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid JSON in {label}: {exc}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_bytes(path: Path) -> bytes:
    root = ROOT.resolve(strict=True)
    target = path if path.is_absolute() else root / path
    require(not target.is_symlink(), f"symlink forbidden: {path}")
    resolved = target.resolve(strict=True)
    if not path.is_absolute():
        require(resolved.is_relative_to(root), f"path escapes repository: {path}")
    require(resolved.is_file(), f"not a regular file: {path}")
    return resolved.read_bytes()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    require(spec is not None and spec.loader is not None, f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_output(argv: list[str]) -> str:
    try:
        return subprocess.run(
            ["git", *argv],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise VerificationError(f"git {' '.join(argv)} failed: {exc}") from exc


def verify_capture_revision(revision: str, workflow_path: str, expected_workflow_sha256: str) -> None:
    require(SHA40_RE.fullmatch(revision) is not None, "capture repository revision malformed")
    current = git_output(["rev-parse", "HEAD"]).strip()
    require(SHA40_RE.fullmatch(current) is not None, "current repository revision malformed")
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, current],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise VerificationError("capture revision is not an ancestor of the verification head") from exc
    historical = git_output(["show", f"{revision}:{workflow_path}"]).encode("utf-8")
    require(sha256_bytes(historical) == expected_workflow_sha256, "historical capture workflow bytes drift")


def verify_capture_commit(revision: str) -> None:
    require(SHA40_RE.fullmatch(EXPECTED_CAPTURE_COMMIT) is not None, "expected capture commit malformed")
    require(SHA40_RE.fullmatch(EXPECTED_CAPTURE_EVIDENCE_BLOB) is not None, "expected capture evidence blob malformed")
    current = git_output(["rev-parse", "HEAD"]).strip()
    require(SHA40_RE.fullmatch(current) is not None, "current repository revision malformed")
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", EXPECTED_CAPTURE_COMMIT, current],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise VerificationError("capture evidence commit is not an ancestor of the verification head") from exc

    commit_and_parents = git_output(["rev-list", "--parents", "-n", "1", EXPECTED_CAPTURE_COMMIT]).strip().split()
    require(len(commit_and_parents) == 2, "capture evidence commit must have exactly one parent")
    require(commit_and_parents[0] == EXPECTED_CAPTURE_COMMIT, "capture evidence commit identity drift")
    require(commit_and_parents[1] == revision, "capture evidence commit parent is not the exact capture revision")

    changes = [
        line
        for line in git_output(
            ["diff-tree", "--no-commit-id", "--name-status", "-r", EXPECTED_CAPTURE_COMMIT]
        ).splitlines()
        if line
    ]
    require(
        changes == [f"A\t{COMMITTED_EVIDENCE_REL.as_posix()}"],
        "capture evidence commit must add only the committed B2P07 evidence file",
    )

    historical_blob = git_output(
        ["rev-parse", f"{EXPECTED_CAPTURE_COMMIT}:{COMMITTED_EVIDENCE_REL.as_posix()}"]
    ).strip()
    require(historical_blob == EXPECTED_CAPTURE_EVIDENCE_BLOB, "capture evidence blob identity drift")
    current_blob = git_output(["rev-parse", f"HEAD:{COMMITTED_EVIDENCE_REL.as_posix()}"]).strip()
    require(current_blob == EXPECTED_CAPTURE_EVIDENCE_BLOB, "committed B2P07 evidence bytes drifted after capture")

    print(f"B2P07_CAPTURE_COMMIT={EXPECTED_CAPTURE_COMMIT}")
    print(f"B2P07_CAPTURE_EVIDENCE_BLOB={EXPECTED_CAPTURE_EVIDENCE_BLOB}")


def verify_static_authority() -> tuple[Any, dict[str, Any]]:
    capture = load_module(CAPTURE_REL, "wispral_b2p07_public_capture")
    try:
        authority = capture.verify_authority()
    except Exception as exc:
        raise VerificationError(f"B2P07 static authority failed: {exc}") from exc
    require(authority.get("b2p06_canonical_merge") == capture.B2P06_CANONICAL_MERGE, "B2P06 canonical merge binding drift")
    require(authority.get("b2p06_reconciliation_merge") == capture.B2P06_RECONCILIATION_MERGE, "B2P06 reconciliation binding drift")
    require(authority.get("attempt_state_sha256") == capture.ATTEMPT_STATE_SHA256, "attempt-state authority digest drift")
    require(authority.get("preprocessing_evidence_sha256") == capture.PREPROCESSING_EVIDENCE_SHA256, "preprocessing authority digest drift")
    print("B2P07_STATIC_AUTHORITY=PASS")
    print(f"B2P07_B2P06_CANONICAL_MERGE={capture.B2P06_CANONICAL_MERGE}")
    print(f"B2P07_B2P06_RECONCILIATION_MERGE={capture.B2P06_RECONCILIATION_MERGE}")
    print("B2P07_B2P08_ATTEMPT_MANIFEST_FROZEN=NO")
    print("B2P07_CANDIDATE_DECODING_STARTED=NO")
    return capture, authority


def verify_evidence(path: Path) -> dict[str, Any]:
    capture, expected_authority = verify_static_authority()
    evidence = load_object(safe_bytes(path), "B2P07 environment evidence")
    require(
        set(evidence) == {"schema_version", "task", "lane", "authority", "capture_provenance", "environment", "claim_guards"},
        "B2P07 evidence top-level keys drift",
    )
    require(evidence.get("schema_version") == "000b2-public-environment-capture-v1", "B2P07 evidence schema drift")
    require(evidence.get("task") == "B2P07", "B2P07 task identity drift")
    require(evidence.get("lane") == "PUBLIC_CORPUS", "B2P07 lane drift")
    require(evidence.get("authority") == expected_authority, "B2P07 authority block drift")

    provenance = evidence.get("capture_provenance")
    require(isinstance(provenance, dict), "capture provenance missing")
    require(
        set(provenance) == {"repository_revision", "event_name", "github_run_id", "github_run_attempt", "github_job", "workflow_name", "github_ref", "capture_kind"},
        "capture provenance keys drift",
    )
    revision = provenance.get("repository_revision")
    require(isinstance(revision, str), "capture revision missing")
    require(revision == capture.CAPTURE_WORKFLOW_REVISION, "capture revision does not match frozen B2P07 capture revision")
    require(provenance.get("event_name") == "push", "capture event must be push")
    require(provenance.get("github_run_id") == EXPECTED_CAPTURE_RUN_ID, "capture run id drift")
    require(provenance.get("github_run_attempt") == EXPECTED_CAPTURE_RUN_ATTEMPT, "capture run attempt drift")
    require(provenance.get("github_job") == EXPECTED_CAPTURE_JOB, "capture job identity drift")
    require(provenance.get("workflow_name") == EXPECTED_CAPTURE_WORKFLOW_NAME, "capture workflow identity drift")
    require(provenance.get("github_ref") == EXPECTED_CAPTURE_REF, "capture ref drift")
    require(provenance.get("capture_kind") == "GITHUB_HOSTED_DIAGNOSTIC", "capture kind drift")
    workflow_path = expected_authority.get("capture_workflow_path_at_revision")
    workflow_sha = expected_authority.get("capture_workflow_sha256")
    require(isinstance(workflow_path, str), "capture workflow authority path missing")
    require(isinstance(workflow_sha, str) and SHA256_RE.fullmatch(workflow_sha) is not None, "capture workflow authority digest malformed")
    verify_capture_revision(revision, workflow_path, workflow_sha)
    verify_capture_commit(revision)

    environment = evidence.get("environment")
    require(isinstance(environment, dict), "environment evidence missing")
    require(
        set(environment) == {
            "schema_version", "canonical_wispral_revision", "performance_mode", "performance_mode_claim_source",
            "independent_control_attestation", "comparative_performance_authorized", "ordering", "os", "kernel",
            "machine", "cpu_model", "logical_cpu_count", "memory_bytes", "runner", "toolchain",
            "hardware_fingerprint_sha256", "environment_id",
        },
        "environment evidence keys drift",
    )
    require(environment.get("schema_version") == "000b2-execution-environment-v1", "environment primitive schema drift")
    require(environment.get("canonical_wispral_revision") == capture.ATTEMPT_CANONICAL_REVISION, "environment attempt revision drift")
    require(environment.get("performance_mode") == "DIAGNOSTIC", "GitHub-hosted B2P07 evidence must be DIAGNOSTIC")
    require(environment.get("performance_mode_claim_source") == "OPERATOR_DECLARED", "performance-mode claim source drift")
    require(environment.get("independent_control_attestation") is False, "hosted evidence cannot claim independent control attestation")
    require(environment.get("comparative_performance_authorized") is False, "hosted evidence cannot authorize comparative performance")

    ordering = environment.get("ordering")
    require(isinstance(ordering, dict), "environment ordering evidence missing")
    require(ordering.get("mode") == "ATTEMPT_STATE_BOUND", "environment ordering mode drift")
    require(ordering.get("attempt_state_bound") is True, "environment must bind attempt state")
    require(ordering.get("attempt_time_authority") is False, "environment capture cannot self-authorize chronology")
    require(ordering.get("independent_chronology_attestation") is False, "environment capture cannot claim independent chronology")
    require(ordering.get("attempt_id") == capture.ATTEMPT_ID, "environment attempt ID drift")
    require(ordering.get("canonical_wispral_revision") == capture.ATTEMPT_CANONICAL_REVISION, "environment ordering revision drift")
    require(ordering.get("attempt_state_sha256") == capture.ATTEMPT_STATE_SHA256, "environment attempt-state digest drift")
    require(ordering.get("declared_primary_test_decoding_started") is False, "environment evidence declares primary decoding")

    runner = environment.get("runner")
    require(isinstance(runner, dict), "runner identity missing")
    require(runner.get("github_actions") is True, "B2P07 evidence must identify GitHub Actions")
    require(runner.get("github_hosted") is True, "B2P07 evidence must identify a GitHub-hosted runner")
    require(str(runner.get("runner_environment", "")).lower() != "self-hosted", "hosted evidence cannot identify self-hosted runner")
    require(isinstance(environment.get("logical_cpu_count"), int) and environment["logical_cpu_count"] > 0, "logical CPU identity invalid")
    require(isinstance(environment.get("memory_bytes"), int) and environment["memory_bytes"] > 0, "memory identity invalid")

    primitive = capture.load_capture_primitive()
    canonical = json.dumps(
        primitive.canonical_fingerprint_fields(environment),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    fingerprint = sha256_bytes(canonical)
    require(environment.get("hardware_fingerprint_sha256") == fingerprint, "hardware fingerprint does not reproduce")
    expected_environment_id = f"{environment['machine']}:{environment['cpu_model']}:{fingerprint[:16]}"
    require(environment.get("environment_id") == expected_environment_id, "environment ID does not reproduce")

    guards = evidence.get("claim_guards")
    require(
        guards == {
            "performance_mode": "DIAGNOSTIC",
            "comparative_performance_authorized": False,
            "b2p08_attempt_manifest_frozen": False,
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
        "B2P07 claim guards drift",
    )

    print("B2P07_ENVIRONMENT_EVIDENCE=PASS")
    print(f"B2P07_CAPTURE_REVISION={revision}")
    print(f"B2P07_CAPTURE_RUN_ID={provenance['github_run_id']}")
    print(f"B2P07_ENVIRONMENT_ID={environment['environment_id']}")
    print("B2P07_PERFORMANCE_MODE=DIAGNOSTIC")
    print("B2P07_COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
    print("B2P08_ATTEMPT_MANIFEST_FROZEN=NO")
    print("CANDIDATE_DECODING_STARTED=NO")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--evidence", type=Path, default=COMMITTED_EVIDENCE_REL)
    args = parser.parse_args()
    try:
        if args.static_only:
            verify_static_authority()
        else:
            verify_evidence(args.evidence)
        print("B2P07_ENVIRONMENT_VERIFIER=PASS")
        return 0
    except (VerificationError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"B2P07_ENVIRONMENT_VERIFIER=FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"B2P07_ENVIRONMENT_VERIFIER=FAIL: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
