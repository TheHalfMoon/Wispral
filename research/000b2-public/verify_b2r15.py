#!/usr/bin/env python3
"""Verify the bounded B2R15 ATTEMPT-003 preprocessing/environment provenance rebinding."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
READINESS = PUBLIC / "recovery-attempt-003-readiness.json"
CURRENT = ROOT / "specs" / "CURRENT.md"
CURRENT_STATE = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"

PREPROCESSING_SOURCE = PUBLIC / "preprocessing-capture.json"
ENVIRONMENT_SOURCE = PUBLIC / "execution-environment.json"
PREPROCESSING_REBIND = PUBLIC / "b2r15-preprocessing-rebinding.json"
ENVIRONMENT_REBIND = PUBLIC / "b2r15-environment-rebinding.json"
PROVENANCE = PUBLIC / "b2r15-provenance.json"
B2R14_HARNESS = PUBLIC / "b2r14-sherpa-result-harness.py"
B2R14_QUALIFICATION = PUBLIC / "b2r14-harness-qualification.json"

TASK = "B2R15"
ATTEMPT_001 = "000B2-PUBLIC-ATTEMPT-001"
ATTEMPT_003 = "000B2-PUBLIC-ATTEMPT-003"
AUTHORITY_BASE = "ae349f7ef28e8ffd08ee8f54d1727ef80684a31a"
B2R14_TASK_MERGE = "e07e9bf7b7bdff3fdb41cc421140a9d6bdd8b3ca"
B2R14_POSTMERGE_RUN = 34246855454
B2R14_RECONCILIATION_MERGE = AUTHORITY_BASE

PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
PREPROCESSING_BLOB = "89cbb28b7961042a1793c694692fe822c9414370"
PREPROCESSING_CAPTURE_MERGE = "3dceadd984ff307ce55745bf5f289890a2fac261"
PREPROCESSING_POSTMERGE_RUN = 33814736588

ENVIRONMENT_SHA256 = "2b8b521c28c771293648cbf86c7c1b20e820bacfc065074d7cfe2555745387ed"
ENVIRONMENT_BLOB = "caf814bcb5e42fd769e6df1d9a54c1164535f86c"
ENVIRONMENT_CAPTURE_MERGE = "4bd5306fa1d274d7b822b73e26172dd9c7058319"
ENVIRONMENT_POSTMERGE_RUN = 33864082394
ENVIRONMENT_ID = "x86_64:AMD EPYC 9V74 80-Core Processor:3e80c2c63bf88d13"
HARDWARE_FINGERPRINT_SHA256 = "3e80c2c63bf88d13a10c358feaa250672a5250fb9cbc90e59bdb397912cac5cd"

PREPROCESSING_REBIND_SHA256 = "c44bbbf6d20aaec671d48c083eb76cfb6889a3c50486bd9da94c25b2b8f8039f"
PREPROCESSING_REBIND_BLOB = "697d3a19d8b48805e445157c07a333866e03c4cc"
ENVIRONMENT_REBIND_SHA256 = "0a6b32abae50da0d3d16f850a8e59edde0cb24f9489ce726054d6cf06e03532c"
ENVIRONMENT_REBIND_BLOB = "628965b646c763ccd031370187730c359c6aaf83"

B2R14_HARNESS_SHA256 = "388b1480de6caed4adaad5d88cf3d275a5a4b1d35bd99e00f466581958886e39"
B2R14_HARNESS_BLOB = "7f0d76bf2490a254d515409d39585f6c9296cfa9"
B2R14_QUALIFICATION_BLOB = "b9c5b807c0a98e990991213f517b7e43854c17c5"
SHERPA_VERSION = "1.13.7"
SHERPA_REVISION = "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e"
SHERPA_PATH = "sherpa-onnx/python/sherpa_onnx/online_recognizer.py"
SHERPA_BLOB = "18b49aaf40dc6e43606c63c9633762e8f573876b"

IDENTITIES = {
    "subset_manifest_sha256": "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb",
    "subset_freeze_digest_sha256": "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242",
    "candidate_registry_sha256": "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f",
    "candidate_revalidation_sha256": "aeca7b824d14388271b04c2dad953cecf5c47cd53cf3f70b766f4fe4dcac54b8",
    "frozen_methodology_sha256": "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df",
    "core_scorer_sha256": "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1",
    "core_config_sha256": "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3",
    "public_wer_adapter_sha256": "581a0e4b0bb91d55a252b92871dbb1246b5fbc4466a5d94bceb35862744fc023",
    "c0_repository_context": "OFF",
    "c0_test_specific_context": "OFF",
    "candidate_specific_audio_transform": "OFF",
}

EXPECTED_SCOPE = [
    ".github/workflows/000b2-public-b2r15-rebinding.yml",
    "research/000b2-public/b2r15-preprocessing-rebinding.json",
    "research/000b2-public/b2r15-environment-rebinding.json",
    "research/000b2-public/b2r15-provenance.json",
    "research/000b2-public/verify_b2r15.py",
]

EXPECTED_GUARDS = {
    "human_developer_speech_accuracy_evidence": "ABSENT",
    "comparative_result_available": False,
    "comparative_performance_authorized": False,
    "production_stt_selected": False,
    "product_code_authorized": False,
    "attempt_003_frozen": False,
    "attempt_003_primary_decode_authorized": False,
    "scoring_performed": False,
}


class VerifyError(RuntimeError):
    """Fail-closed B2R15 verification error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerifyError(f"unable to read {path.relative_to(ROOT)}: {exc}") from exc
    require(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain one JSON object")
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


def git_blob(path: Path) -> str:
    return git_output("rev-parse", f"HEAD:{path.relative_to(ROOT).as_posix()}")


def verify_authority() -> None:
    readiness = load_json(READINESS)
    require(readiness.get("completed_recovery_tasks") == ["B2R13", "B2R14"], "canonical recovery prefix drift")
    require(readiness.get("active_recovery_unit") == TASK, "B2R15 is not the sole active recovery unit")

    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict), "replacement attempt authority missing")
    require(replacement.get("attempt_id") == ATTEMPT_003, "replacement attempt id drift")
    require(replacement.get("required") is True, "replacement attempt requirement weakened")
    require(replacement.get("frozen") is False, "replacement attempt froze before B2R15")
    require(replacement.get("primary_decode_entry_open") is False, "primary decode entry opened during B2R15")

    proofs = readiness.get("transition_proofs")
    require(isinstance(proofs, list) and proofs, "transition proofs missing")
    predecessor = proofs[-1]
    require(isinstance(predecessor, dict), "predecessor transition proof malformed")
    require(predecessor.get("completed_task") == "B2R14", "B2R15 predecessor task drift")
    require(predecessor.get("canonical_task_merge") == B2R14_TASK_MERGE, "B2R14 task merge drift")
    require(predecessor.get("post_merge_recovery_run_id") == B2R14_POSTMERGE_RUN, "B2R14 post-merge proof drift")
    require(predecessor.get("successor_task") == TASK, "B2R14 transition does not authorize B2R15")

    scopes = readiness.get("task_candidate_scopes")
    require(isinstance(scopes, dict) and scopes.get(TASK) == EXPECTED_SCOPE, "B2R15 exact candidate scope drift")
    policies = readiness.get("task_content_policies")
    require(isinstance(policies, dict), "task content policy map missing")
    require(
        policies.get(TASK)
        == {
            "required_verifier": "research/000b2-public/verify_b2r15.py",
            "primary_decode_allowed": False,
            "scoring_allowed": False,
            "comparative_publish_allowed": False,
            "production_selection_allowed": False,
            "product_code_allowed": False,
            "foreign_successor_task_references_allowed": False,
        },
        "B2R15 content policy drift",
    )

    for path, label in ((CURRENT, "CURRENT"), (CURRENT_STATE, "CURRENT_STATE")):
        text = path.read_text(encoding="utf-8")
        require("**Active successor recovery unit:** `B2R15`" in text, f"{label} does not authorize B2R15")
        require(f"`{B2R14_TASK_MERGE}`" in text, f"{label} lost B2R14 task merge proof")
        require(f"`{B2R14_POSTMERGE_RUN}`" in text, f"{label} lost B2R14 post-merge proof")
        require("**ATTEMPT-003 frozen:** `false`" in text, f"{label} does not preserve unfrozen state")
        require("**ATTEMPT-003 primary decode entry open:** `false`" in text, f"{label} opens primary decoding")


def verify_historical_sources(require_git: bool) -> None:
    preprocessing = load_json(PREPROCESSING_SOURCE)
    require(sha256_file(PREPROCESSING_SOURCE) == PREPROCESSING_SHA256, "historical preprocessing bytes drift")
    attempt = preprocessing.get("attempt")
    execution = preprocessing.get("execution")
    require(isinstance(attempt, dict) and attempt.get("attempt_id") == ATTEMPT_001, "preprocessing source attempt drift")
    require(isinstance(execution, dict), "preprocessing execution evidence missing")
    require(execution.get("preprocessed_file_count") == 240, "preprocessing file count drift")
    require(execution.get("all_source_hashes_reverified") is True, "preprocessing source hashes not reverified")
    require(
        execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True,
        "preprocessing output format contract drift",
    )
    require(execution.get("raw_preprocessed_audio_retained_in_repository") is False, "raw preprocessing retention drift")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240, "preprocessing exact-record set drift")

    environment = load_json(ENVIRONMENT_SOURCE)
    require(sha256_file(ENVIRONMENT_SOURCE) == ENVIRONMENT_SHA256, "historical environment bytes drift")
    env = environment.get("environment")
    require(isinstance(env, dict), "environment payload missing")
    require(env.get("environment_id") == ENVIRONMENT_ID, "environment id drift")
    require(env.get("hardware_fingerprint_sha256") == HARDWARE_FINGERPRINT_SHA256, "hardware fingerprint drift")
    require(env.get("performance_mode") == "DIAGNOSTIC", "environment performance mode drift")
    require(env.get("comparative_performance_authorized") is False, "comparative performance authority drift")
    ordering = env.get("ordering")
    require(isinstance(ordering, dict) and ordering.get("attempt_id") == ATTEMPT_001, "environment source attempt drift")
    require(ordering.get("attempt_time_authority") is False, "historical environment gained attempt-time authority")
    require(ordering.get("independent_chronology_attestation") is False, "historical chronology claim drift")

    if require_git:
        require(git_blob(PREPROCESSING_SOURCE) == PREPROCESSING_BLOB, "historical preprocessing Git blob drift")
        require(git_blob(ENVIRONMENT_SOURCE) == ENVIRONMENT_BLOB, "historical environment Git blob drift")


def verify_preprocessing_rebind(require_git: bool) -> None:
    document = load_json(PREPROCESSING_REBIND)
    require(document.get("schema_version") == "000b2-public-b2r15-preprocessing-rebinding-v1", "preprocessing schema drift")
    require(document.get("task") == TASK and document.get("lane") == "PUBLIC_CORPUS", "preprocessing task/lane drift")
    require(document.get("state") == "ATTEMPT_003_PREPROCESSING_EVIDENCE_BOUND", "preprocessing state drift")

    attempt = document.get("attempt")
    require(
        attempt
        == {
            "source_attempt_id": ATTEMPT_001,
            "bound_attempt_id": ATTEMPT_003,
            "reuse_mode": "CRYPTOGRAPHIC_PROVENANCE_REBIND",
            "fresh_capture_performed": False,
            "source_chronology_reused": False,
            "fresh_chronology_claim_created": False,
            "frozen": False,
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
        },
        "preprocessing attempt semantics drift",
    )
    require(
        document.get("source_evidence")
        == {
            "path": "research/000b2-public/preprocessing-capture.json",
            "sha256": PREPROCESSING_SHA256,
            "git_blob_sha1": PREPROCESSING_BLOB,
            "canonical_capture_merge": PREPROCESSING_CAPTURE_MERGE,
            "post_merge_validation_run_id": PREPROCESSING_POSTMERGE_RUN,
            "preprocessed_file_count": 240,
            "all_source_hashes_reverified": True,
            "all_outputs_verified_pcm_s16le_mono_16000hz": True,
            "raw_preprocessed_audio_retained_in_repository": False,
        },
        "preprocessing source-evidence binding drift",
    )
    require(document.get("preserved_identity_guards") == IDENTITIES, "preprocessing preserved identity drift")
    require(document.get("claim_guards") == EXPECTED_GUARDS, "preprocessing claim guards drift")
    require(sha256_file(PREPROCESSING_REBIND) == PREPROCESSING_REBIND_SHA256, "preprocessing rebinding bytes drift")
    if require_git:
        require(git_blob(PREPROCESSING_REBIND) == PREPROCESSING_REBIND_BLOB, "preprocessing rebinding Git blob drift")


def verify_environment_rebind(require_git: bool) -> None:
    document = load_json(ENVIRONMENT_REBIND)
    require(document.get("schema_version") == "000b2-public-b2r15-environment-rebinding-v1", "environment schema drift")
    require(document.get("task") == TASK and document.get("lane") == "PUBLIC_CORPUS", "environment task/lane drift")
    require(document.get("state") == "ATTEMPT_003_EXECUTION_ENVIRONMENT_EVIDENCE_BOUND", "environment state drift")

    attempt = document.get("attempt")
    require(
        attempt
        == {
            "source_attempt_id": ATTEMPT_001,
            "bound_attempt_id": ATTEMPT_003,
            "reuse_mode": "CRYPTOGRAPHIC_PROVENANCE_REBIND",
            "fresh_capture_performed": False,
            "source_chronology_reused": False,
            "fresh_chronology_claim_created": False,
            "fresh_hardware_claim_created": False,
            "fresh_runtime_capture_claim_created": False,
            "frozen": False,
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
        },
        "environment attempt semantics drift",
    )
    require(
        document.get("source_evidence")
        == {
            "path": "research/000b2-public/execution-environment.json",
            "sha256": ENVIRONMENT_SHA256,
            "git_blob_sha1": ENVIRONMENT_BLOB,
            "canonical_capture_merge": ENVIRONMENT_CAPTURE_MERGE,
            "post_merge_validation_run_id": ENVIRONMENT_POSTMERGE_RUN,
            "capture_kind": "GITHUB_HOSTED_DIAGNOSTIC",
            "environment_id": ENVIRONMENT_ID,
            "hardware_fingerprint_sha256": HARDWARE_FINGERPRINT_SHA256,
            "performance_mode": "DIAGNOSTIC",
            "comparative_performance_authorized": False,
            "candidate_run_runtime_observations_must_be_preserved_separately": True,
        },
        "environment source-evidence binding drift",
    )
    require(document.get("claim_guards") == EXPECTED_GUARDS, "environment claim guards drift")
    require(sha256_file(ENVIRONMENT_REBIND) == ENVIRONMENT_REBIND_SHA256, "environment rebinding bytes drift")
    if require_git:
        require(git_blob(ENVIRONMENT_REBIND) == ENVIRONMENT_REBIND_BLOB, "environment rebinding Git blob drift")


def verify_provenance(require_git: bool) -> None:
    document = load_json(PROVENANCE)
    require(document.get("schema_version") == "000b2-public-b2r15-provenance-v1", "provenance schema drift")
    require(document.get("task") == TASK and document.get("lane") == "PUBLIC_CORPUS", "provenance task/lane drift")
    require(document.get("state") == "ATTEMPT_003_PREEXECUTION_EVIDENCE_REBOUND", "provenance state drift")
    require(
        document.get("authority")
        == {
            "canonical_authority_base": AUTHORITY_BASE,
            "active_attempt_id": ATTEMPT_003,
            "predecessor_task": "B2R14",
            "predecessor_canonical_task_merge": B2R14_TASK_MERGE,
            "predecessor_post_merge_recovery_run_id": B2R14_POSTMERGE_RUN,
            "predecessor_reconciliation_merge": B2R14_RECONCILIATION_MERGE,
        },
        "provenance authority binding drift",
    )
    require(
        document.get("rebinding_artifacts")
        == {
            "preprocessing": {
                "path": "research/000b2-public/b2r15-preprocessing-rebinding.json",
                "sha256": PREPROCESSING_REBIND_SHA256,
                "git_blob_sha1": PREPROCESSING_REBIND_BLOB,
            },
            "execution_environment": {
                "path": "research/000b2-public/b2r15-environment-rebinding.json",
                "sha256": ENVIRONMENT_REBIND_SHA256,
                "git_blob_sha1": ENVIRONMENT_REBIND_BLOB,
            },
        },
        "provenance sibling-artifact binding drift",
    )

    historical = document.get("historical_sources")
    require(isinstance(historical, dict), "historical source provenance missing")
    require(
        historical.get("preprocessing")
        == {
            "path": "research/000b2-public/preprocessing-capture.json",
            "sha256": PREPROCESSING_SHA256,
            "git_blob_sha1": PREPROCESSING_BLOB,
            "source_attempt_id": ATTEMPT_001,
            "canonical_capture_merge": PREPROCESSING_CAPTURE_MERGE,
            "post_merge_validation_run_id": PREPROCESSING_POSTMERGE_RUN,
        },
        "historical preprocessing provenance drift",
    )
    require(
        historical.get("execution_environment")
        == {
            "path": "research/000b2-public/execution-environment.json",
            "sha256": ENVIRONMENT_SHA256,
            "git_blob_sha1": ENVIRONMENT_BLOB,
            "source_attempt_id": ATTEMPT_001,
            "canonical_capture_merge": ENVIRONMENT_CAPTURE_MERGE,
            "post_merge_validation_run_id": ENVIRONMENT_POSTMERGE_RUN,
            "performance_mode": "DIAGNOSTIC",
            "comparative_performance_authorized": False,
        },
        "historical environment provenance drift",
    )

    require(
        document.get("preserved_b2r14_harness_identity")
        == {
            "harness_path": "research/000b2-public/b2r14-sherpa-result-harness.py",
            "harness_git_blob_sha1": B2R14_HARNESS_BLOB,
            "harness_sha256": B2R14_HARNESS_SHA256,
            "qualification_path": "research/000b2-public/b2r14-harness-qualification.json",
            "qualification_git_blob_sha1": B2R14_QUALIFICATION_BLOB,
            "runtime_distribution": "sherpa-onnx",
            "runtime_version": SHERPA_VERSION,
            "runtime_revision": SHERPA_REVISION,
            "runtime_source_path": SHERPA_PATH,
            "runtime_source_git_blob_sha1": SHERPA_BLOB,
        },
        "B2R14 harness identity drift",
    )
    require(
        document.get("evidence_semantics")
        == {
            "mode": "CRYPTOGRAPHIC_PROVENANCE_REBIND",
            "fresh_preprocessing_capture_performed": False,
            "fresh_environment_capture_performed": False,
            "historical_capture_chronology_reused_as_fresh": False,
            "fresh_hardware_claim_created": False,
            "fresh_runtime_capture_claim_created": False,
            "candidate_run_runtime_observations_must_be_preserved_separately": True,
            "no_result_driven_input_change": True,
        },
        "B2R15 evidence semantics drift",
    )
    require(
        document.get("claim_guards")
        == {
            **EXPECTED_GUARDS,
            "primary_decode_performed": False,
        },
        "provenance claim guards drift",
    )

    require(sha256_file(B2R14_HARNESS) == B2R14_HARNESS_SHA256, "B2R14 harness bytes drift")
    qualification = load_json(B2R14_QUALIFICATION)
    pinned = qualification.get("pinned_runtime")
    require(isinstance(pinned, dict), "B2R14 pinned runtime missing")
    require(pinned.get("version") == SHERPA_VERSION, "B2R14 runtime version drift")
    require(pinned.get("revision") == SHERPA_REVISION, "B2R14 runtime revision drift")
    require(pinned.get("source_path") == SHERPA_PATH, "B2R14 runtime source path drift")
    require(pinned.get("source_git_blob_sha1") == SHERPA_BLOB, "B2R14 runtime source blob drift")

    if require_git:
        require(git_blob(B2R14_HARNESS) == B2R14_HARNESS_BLOB, "B2R14 harness Git blob drift")
        require(git_blob(B2R14_QUALIFICATION) == B2R14_QUALIFICATION_BLOB, "B2R14 qualification Git blob drift")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify B2R15 ATTEMPT-003 evidence rebinding.")
    parser.add_argument("--require-git", action="store_true", help="Require exact committed Git blob identities.")
    args = parser.parse_args()

    try:
        verify_authority()
        verify_historical_sources(args.require_git)
        verify_preprocessing_rebind(args.require_git)
        verify_environment_rebind(args.require_git)
        verify_provenance(args.require_git)
    except VerifyError as exc:
        print(f"B2R15_REBINDING=FAIL: {exc}")
        return 1

    print("B2R15_REBINDING=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
