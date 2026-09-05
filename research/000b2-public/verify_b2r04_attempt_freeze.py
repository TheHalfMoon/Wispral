#!/usr/bin/env python3
"""Verify the B2R04 ATTEMPT-002 freeze without opening primary decoding."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
MANIFEST = PUBLIC / "attempt-002-manifest.json"
FREEZER = PUBLIC / "freeze_attempt_002_manifest.py"
RECOVERY = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CURRENT_STATE = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
HARNESS = PUBLIC / "moonshine_streaming_c0.py"
PUBLIC_WER = PUBLIC / "score_public_wer.py"

ATTEMPT_002 = "000B2-PUBLIC-ATTEMPT-002"
B2R03_RECONCILIATION = "cd527d7e5a8361ff01cb11b85fe552986f44e742"
HISTORICAL_ATTEMPT_001_BLOB = "411b67d95d3c06264742c7a9d00eea10ac7f9bb6"
LEGACY_ATTEMPT_VERIFIER_BLOB = "7678ba756241bf1cdd29df0126b3527f5f1274d7"
CORRECTED_C0_HARNESS_BLOB = "9012f30133df31e88cd489e7612d7991ac0cce25"
CORRECTED_C0_HARNESS_SHA256 = "c0f0093cda7ca036c8a97178364b3840ce7093386a8cb711ccef5f183a4453c0"
PUBLIC_WER_BLOB = "f5719cee1f3dfee1c84d7a5e4c7c25620ded1e2d"
PUBLIC_WER_SHA256 = "581a0e4b0bb91d55a252b92871dbb1246b5fbc4466a5d94bceb35862744fc023"
FREEZE_DIGEST = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
RECOVERY_TASKS = tuple(f"B2R{index:02d}" for index in range(1, 13))
PRIMARY_DECODE_TASKS = set(RECOVERY_TASKS[4:10])
B2R04_TASK_PATHS = {
    "research/000b2-public/attempt-002-manifest.json",
    "research/000b2-public/freeze_attempt_002_manifest.py",
    "research/000b2-public/verify_attempt_manifest.py",
    "research/000b2-public/verify_attempt_manifest_legacy.py",
    "research/000b2-public/verify_b2r04_attempt_freeze.py",
}


class VerifyError(RuntimeError):
    """Fail-closed B2R04 verification error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain one object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise VerifyError(f"git {' '.join(args)} failed: {exc}") from exc


def git_blob(path: str) -> str:
    return git_output("rev-parse", f"HEAD:{path}")


def changed_paths(base: str, head: str = "HEAD") -> set[str]:
    return {line for line in git_output("diff", "--name-only", base, head).splitlines() if line}


def load_freezer():
    spec = importlib.util.spec_from_file_location("wispral_b2r04_freezer", FREEZER)
    require(spec is not None and spec.loader is not None, "unable to load B2R04 freezer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed_prefix(tasks: str) -> list[str]:
    completed: list[str] = []
    pending_seen = False
    for task in RECOVERY_TASKS:
        matches = [line for line in tasks.splitlines() if f"`{task}`" in line]
        require(len(matches) == 1, f"{task} must appear exactly once in recovery task ledger")
        line = matches[0]
        if line.startswith("- [x]"):
            require(not pending_seen, f"recovery task ordering skipped a predecessor before {task}")
            completed.append(task)
        elif line.startswith("- [ ]"):
            pending_seen = True
        else:
            raise VerifyError(f"malformed checklist state for {task}")
    return completed


def verify_frozen_dependency_bytes() -> None:
    require(sha256_file(HARNESS) == CORRECTED_C0_HARNESS_SHA256, "corrected Moonshine C0 harness SHA-256 drift")
    require(
        git_blob("research/000b2-public/moonshine_streaming_c0.py") == CORRECTED_C0_HARNESS_BLOB,
        "corrected Moonshine C0 harness Git blob drift",
    )
    require(sha256_file(PUBLIC_WER) == PUBLIC_WER_SHA256, "public WER adapter SHA-256 drift")
    require(
        git_blob("research/000b2-public/score_public_wer.py") == PUBLIC_WER_BLOB,
        "public WER adapter Git blob drift",
    )
    require(
        git_blob("research/000b2-public/verify_attempt_manifest_legacy.py") == LEGACY_ATTEMPT_VERIFIER_BLOB,
        "legacy B2P08 attempt verifier is not the exact historical blob",
    )


def verify_manifest() -> None:
    verify_frozen_dependency_bytes()
    freezer = load_freezer()
    expected = freezer.build_manifest()
    observed = load_json(MANIFEST)
    require(observed == expected, "ATTEMPT-002 manifest semantic drift")
    require(MANIFEST.read_bytes() == freezer.render_json(expected), "ATTEMPT-002 manifest byte drift")
    require(observed.get("freeze_digest_sha256") == FREEZE_DIGEST, "ATTEMPT-002 freeze digest drift")
    require(observed.get("freeze_digest_sha256") == freezer.freeze_digest(observed), "ATTEMPT-002 freeze digest mismatch")
    require(observed.get("schema_version") == "000b2-public-attempt-002-manifest-v1", "manifest schema drift")
    require(observed.get("task") == "B2R04", "manifest task drift")
    require(observed.get("attempt_id") == ATTEMPT_002, "manifest attempt id drift")
    require(observed.get("phase") == "PRE_PRIMARY_FROZEN", "manifest phase drift")
    require(observed.get("frozen") is True, "ATTEMPT-002 evidence is not frozen")

    decoding = observed.get("decoding_contract")
    claims = observed.get("claims")
    require(isinstance(decoding, dict), "decoding contract missing")
    require(decoding.get("candidate_decoding_started") is False, "candidate decoding started before B2R04 freeze")
    require(decoding.get("primary_decoding_started") is False, "primary decoding started before B2R04 freeze")
    require(decoding.get("identical_frozen_audio_required_across_candidates") is True, "identical-audio invariant drift")
    require(decoding.get("c0_repository_context") == "OFF", "C0 repository context drift")
    require(decoding.get("c0_test_specific_context") == "OFF", "C0 test-specific context drift")
    require(decoding.get("candidate_specific_audio_transform") == "OFF", "candidate-specific transform drift")
    require(decoding.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation weakened")
    require(
        decoding.get("candidate_run_runtime_observations_must_be_preserved_separately") is True,
        "candidate runtime observation preservation weakened",
    )
    require(isinstance(claims, dict), "manifest claim guards missing")
    require(claims.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human evidence guard drift")
    require(claims.get("comparative_result_available") is False, "comparative result exists at freeze")
    require(claims.get("comparative_performance_authorized") is False, "comparative performance authorized at freeze")
    require(claims.get("human_developer_speech_ranking_authorized") is False, "human ranking authorized at freeze")
    require(claims.get("production_stt_selected") is False, "production STT selected at freeze")
    require(claims.get("product_code_authorized") is False, "product code authorized at freeze")
    require(claims.get("b2r05_authorized") is False, "B2R05 was authorized at freeze time")


def verify_authority() -> str:
    readiness = load_json(RECOVERY)
    tasks = TASKS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    current_state = CURRENT_STATE.read_text(encoding="utf-8")
    completed = completed_prefix(tasks)
    authority_completed = readiness.get("completed_recovery_tasks")
    active = readiness.get("active_recovery_unit")
    replacement = readiness.get("replacement_attempt")

    require(isinstance(authority_completed, list), "recovery completed-task ledger malformed")
    require(authority_completed == completed, "task ledger and recovery authority disagree")
    require(isinstance(replacement, dict), "replacement attempt authority missing")
    require(replacement.get("attempt_id") == ATTEMPT_002, "replacement attempt id drift")
    require(replacement.get("required") is True, "replacement attempt requirement weakened")
    require(readiness.get("qualified_workflow_change_paths") == [], "B2R04 must not inherit workflow-change authority")
    require(
        git_blob("research/000b2-public/attempt-manifest.json") == HISTORICAL_ATTEMPT_001_BLOB,
        "historical ATTEMPT-001 manifest bytes drift",
    )
    git_output("merge-base", "--is-ancestor", B2R03_RECONCILIATION, "HEAD")

    if active == "B2R04":
        require(completed == ["B2R01", "B2R02", "B2R03"], "B2R04 task stage recovery prefix drift")
        require(replacement.get("frozen") is False, "canonical authority froze ATTEMPT-002 before B2R04 reconciliation")
        require(replacement.get("primary_decode_entry_open") is False, "primary decode entry opened before B2R04 reconciliation")
        require("- [ ] `B2R04`" in tasks, "B2R04 must remain pending in task PR")
        require("- [ ] `B2R05`" in tasks, "B2R05 must remain pending during B2R04 task PR")
        require(
            changed_paths(B2R03_RECONCILIATION) == B2R04_TASK_PATHS,
            "B2R04 task stage contains paths outside the exact qualified five-file freeze scope",
        )
        for text, label in ((current, "CURRENT"), (current_state, "CURRENT_STATE")):
            require("**Canonical recovery predecessor:** `B2R03`" in text, f"{label} recovery predecessor drift")
            require("**Active recovery unit:** `B2R04`" in text, f"{label} does not authorize B2R04")
            require("6904fa7dd55e35c08e76044a18ebf9a95c65e038" in text, f"{label} lost B2R03 task merge proof")
            require("33995766496" in text, f"{label} lost B2R03 post-merge recovery proof")
        forbidden = (
            PUBLIC / "attempt-002-transcripts",
            PUBLIC / "attempt-002-results.json",
            PUBLIC / "b2r05-moonshine-compact.json",
        )
        require(all(not path.exists() for path in forbidden), "primary ATTEMPT-002 output surface exists before B2R04 reconciliation")
        return "TASK_STAGE"

    require("B2R04" in completed, "B2R04 is neither active nor canonically completed")
    require(completed[:4] == ["B2R01", "B2R02", "B2R03", "B2R04"], "B2R04 canonical recovery prefix drift")
    require(replacement.get("frozen") is True, "canonical authority lost ATTEMPT-002 frozen state")
    expected_open = active in PRIMARY_DECODE_TASKS
    require(replacement.get("primary_decode_entry_open") is expected_open, "primary decode entry authority drift")
    require("- [x] `B2R04`" in tasks, "B2R04 canonical task ledger is not checked")
    return "CANONICAL_FROZEN"


def main() -> int:
    verify_manifest()
    mode = verify_authority()
    print("B2R04_ATTEMPT_002_FREEZE=PASS")
    print(f"B2R04_FREEZE_DIGEST={FREEZE_DIGEST}")
    print("ATTEMPT_002_FROZEN_EVIDENCE=YES")
    print("ATTEMPT_002_CANDIDATE_DECODING_STARTED_AT_FREEZE=NO")
    print("ATTEMPT_002_PRIMARY_DECODING_STARTED_AT_FREEZE=NO")
    print(f"B2R04_AUTHORITY_MODE={mode}")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerifyError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"B2R04_ATTEMPT_002_FREEZE=FAIL: {exc}") from exc
