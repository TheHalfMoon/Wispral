#!/usr/bin/env python3
"""Verify B2R15 ATTEMPT-003 preprocessing/environment cryptographic rebinding."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research/000b2-public"
TASK = "B2R15"
AUTHORITY_BASE = "ae349f7ef28e8ffd08ee8f54d1727ef80684a31a"
PREPROCESSING = PUBLIC / "b2r15-preprocessing-rebinding.json"
ENVIRONMENT = PUBLIC / "b2r15-environment-rebinding.json"
PROVENANCE = PUBLIC / "b2r15-provenance.json"
READINESS = PUBLIC / "recovery-attempt-003-readiness.json"

SOURCE_BINDINGS = {
    "research/000b2-public/preprocessing-capture.json": ("89cbb28b7961042a1793c694692fe822c9414370", "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"),
    "research/000b2-public/execution-environment.json": ("caf814bcb5e42fd769e6df1d9a54c1164535f86c", "2b8b521c28c771293648cbf86c7c1b20e820bacfc065074d7cfe2555745387ed"),
    "research/000b2-public/b2r03-preexecution-rebinding.json": ("49ba712b6a71ae69313c06b724833de1a95099b4", None),
    "research/000b2-public/b2r14-sherpa-result-harness.py": ("7f0d76bf2490a254d515409d39585f6c9296cfa9", None),
    "research/000b2-public/b2r14-harness-qualification.json": ("b9c5b807c0a98e990991213f517b7e43854c17c5", None),
    "research/000b2-public/verify_b2r14.py": ("c5536ae06597652552108d08be50b7b647f4ac8f", None),
}
PRESERVED = {
    "subset_manifest_sha256": "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb",
    "subset_freeze_digest_sha256": "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242",
    "candidate_registry_sha256": "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f",
    "candidate_revalidation_sha256": "aeca7b824d14388271b04c2dad953cecf5c47cd53cf3f70b766f4fe4dcac54b8",
    "frozen_methodology_sha256": "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df",
    "core_scorer_sha256": "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1",
    "core_config_sha256": "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3",
    "public_wer_adapter_sha256": "581a0e4b0bb91d55a252b92871dbb1246b5fbc4466a5d94bceb35862744fc023",
}
EXPECTED_PREPROCESSING = {
    "schema_version": "000b2-public-b2r15-preprocessing-rebinding-v1",
    "task": TASK,
    "lane": "PUBLIC_CORPUS",
    "state": "ATTEMPT_003_PREPROCESSING_CRYPTOGRAPHICALLY_REBOUND",
    "attempt_id": "000B2-PUBLIC-ATTEMPT-003",
    "canonical_authority_base": AUTHORITY_BASE,
    "reuse_mode": "CRYPTOGRAPHIC_PROVENANCE_REBIND",
    "source_attempt_id": "000B2-PUBLIC-ATTEMPT-001",
    "source_evidence_path": "research/000b2-public/preprocessing-capture.json",
    "source_evidence_sha256": SOURCE_BINDINGS["research/000b2-public/preprocessing-capture.json"][1],
    "source_evidence_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/preprocessing-capture.json"][0],
    "historical_rebinding_path": "research/000b2-public/b2r03-preexecution-rebinding.json",
    "historical_rebinding_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/b2r03-preexecution-rebinding.json"][0],
    "preprocessed_file_count": 240,
    "all_source_hashes_reverified_by_source_evidence": True,
    "all_outputs_verified_pcm_s16le_mono_16000hz_by_source_evidence": True,
    "source_chronology_reused": False,
    "source_audio_bytes_changed": False,
    "preprocessed_audio_bytes_changed": False,
    "subset_membership_changed": False,
    "no_result_driven_input_change": True,
    "preserved_identity_guards": {
        **PRESERVED,
        "c0_repository_context": "OFF",
        "c0_test_specific_context": "OFF",
        "candidate_specific_audio_transform": "OFF",
    },
    "claim_guards": {
        "attempt_003_frozen": False,
        "primary_decode_entry_open": False,
        "primary_decoding_started": False,
        "scoring_allowed": False,
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
    },
}
EXPECTED_ENVIRONMENT = {
    "schema_version": "000b2-public-b2r15-environment-rebinding-v1",
    "task": TASK,
    "lane": "PUBLIC_CORPUS",
    "state": "ATTEMPT_003_ENVIRONMENT_CRYPTOGRAPHICALLY_REBOUND",
    "attempt_id": "000B2-PUBLIC-ATTEMPT-003",
    "canonical_authority_base": AUTHORITY_BASE,
    "reuse_mode": "CRYPTOGRAPHIC_PROVENANCE_REBIND",
    "source_attempt_id": "000B2-PUBLIC-ATTEMPT-001",
    "source_evidence_path": "research/000b2-public/execution-environment.json",
    "source_evidence_sha256": SOURCE_BINDINGS["research/000b2-public/execution-environment.json"][1],
    "source_evidence_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/execution-environment.json"][0],
    "historical_rebinding_path": "research/000b2-public/b2r03-preexecution-rebinding.json",
    "historical_rebinding_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/b2r03-preexecution-rebinding.json"][0],
    "environment_id": "x86_64:AMD EPYC 9V74 80-Core Processor:3e80c2c63bf88d13",
    "hardware_fingerprint_sha256": "3e80c2c63bf88d13a10c358feaa250672a5250fb9cbc90e59bdb397912cac5cd",
    "performance_mode": "DIAGNOSTIC",
    "comparative_performance_authorized": False,
    "source_chronology_reused": False,
    "fresh_hardware_claim_created": False,
    "future_candidate_runtime_observations_must_be_preserved_separately": True,
    "b2r14_harness_binding": {
        "harness_path": "research/000b2-public/b2r14-sherpa-result-harness.py",
        "harness_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/b2r14-sherpa-result-harness.py"][0],
        "qualification_path": "research/000b2-public/b2r14-harness-qualification.json",
        "qualification_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/b2r14-harness-qualification.json"][0],
        "verifier_path": "research/000b2-public/verify_b2r14.py",
        "verifier_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/verify_b2r14.py"][0],
        "corrective_task_merge": "e07e9bf7b7bdff3fdb41cc421140a9d6bdd8b3ca",
        "corrective_post_merge_recovery_run_id": 34246855454,
        "reconciliation_merge": AUTHORITY_BASE,
        "reconciliation_post_merge_recovery_run_id": 34269999940,
    },
    "claim_guards": EXPECTED_PREPROCESSING["claim_guards"],
}
EXPECTED_PROVENANCE = {
    "schema_version": "000b2-public-b2r15-provenance-v1",
    "task": TASK,
    "lane": "PUBLIC_CORPUS",
    "attempt_id": "000B2-PUBLIC-ATTEMPT-003",
    "canonical_authority_base": AUTHORITY_BASE,
    "predecessor": {
        "task": "B2R14",
        "corrective_task_base": "2f4212228f24e40fbd03cfc59ab4774df94c0cc3",
        "qualified_corrective_head": "c60751c43a2523879814d691011d5dd6d3d1e119",
        "corrective_task_merge": "e07e9bf7b7bdff3fdb41cc421140a9d6bdd8b3ca",
        "corrective_post_merge_recovery_run_id": 34246855454,
        "reconciliation_head": "4313ceb3ace7d5f2f793cea5b7baa1a00abd2cdb",
        "reconciliation_merge": AUTHORITY_BASE,
        "reconciliation_post_merge_recovery_run_id": 34269999940,
    },
    "rebinding_policy": {
        "mode": "CRYPTOGRAPHIC_PROVENANCE_REBIND",
        "new_primary_material_access": False,
        "primary_decode_performed": False,
        "scoring_performed": False,
        "fresh_hardware_claim_created": False,
        "candidate_changed": False,
        "subset_changed": False,
        "scorer_changed": False,
        "normalization_changed": False,
        "c0_changed": False,
        "b2r14_harness_changed": False,
    },
    "source_evidence": {
        "preprocessing_path": "research/000b2-public/preprocessing-capture.json",
        "preprocessing_sha256": SOURCE_BINDINGS["research/000b2-public/preprocessing-capture.json"][1],
        "preprocessing_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/preprocessing-capture.json"][0],
        "environment_path": "research/000b2-public/execution-environment.json",
        "environment_sha256": SOURCE_BINDINGS["research/000b2-public/execution-environment.json"][1],
        "environment_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/execution-environment.json"][0],
        "historical_rebinding_path": "research/000b2-public/b2r03-preexecution-rebinding.json",
        "historical_rebinding_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/b2r03-preexecution-rebinding.json"][0],
    },
    "preserved_identity_guards": {
        **PRESERVED,
        "b2r14_harness_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/b2r14-sherpa-result-harness.py"][0],
        "b2r14_qualification_git_blob_sha1": SOURCE_BINDINGS["research/000b2-public/b2r14-harness-qualification.json"][0],
        "c0_repository_context": "OFF",
        "c0_test_specific_context": "OFF",
        "candidate_specific_audio_transform": "OFF",
    },
    "claim_guards": {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
        "attempt_003_frozen": False,
        "primary_decode_entry_open": False,
    },
}


class VerifyError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise VerifyError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources() -> None:
    for rel, (blob, digest) in SOURCE_BINDINGS.items():
        path = ROOT / rel
        require(path.is_file(), f"source missing: {rel}")
        require(git("hash-object", rel) == blob, f"source blob drift: {rel}")
        require(git("rev-parse", f"{AUTHORITY_BASE}:{rel}") == blob, f"authority-base source drift: {rel}")
        if digest is not None:
            require(sha256(path) == digest, f"source SHA-256 drift: {rel}")


def verify_frontier() -> None:
    r = load(READINESS)
    require(r.get("state") == "RECOVERY_READY", "successor recovery not ready")
    completed = r.get("completed_recovery_tasks")
    active = r.get("active_recovery_unit")
    require(isinstance(completed, list), "completed task ledger malformed")
    require("B2R14" in completed, "predecessor completion missing")
    if active != TASK:
        require(TASK in completed, "B2R15 is neither active nor completed")
    replacement = r.get("replacement_attempt", {})
    require(replacement.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-003", "attempt identity drift")
    require(replacement.get("frozen") is False, "attempt froze inside B2R15")
    require(replacement.get("primary_decode_entry_open") is False, "primary decode opened inside B2R15")


def verify_preprocessing() -> None:
    p = load(PREPROCESSING)
    require(p == EXPECTED_PREPROCESSING, "preprocessing rebinding record drift")


def verify_environment() -> None:
    e = load(ENVIRONMENT)
    require(e == EXPECTED_ENVIRONMENT, "environment rebinding record drift")


def verify_provenance() -> None:
    p = load(PROVENANCE)
    require(p == EXPECTED_PROVENANCE, "provenance rebinding record drift")


def main() -> int:
    verify_sources()
    verify_frontier()
    verify_preprocessing()
    verify_environment()
    verify_provenance()
    print("B2R15_REBINDING=PASS")
    print("B2R15_PRIMARY_DECODE=NO")
    print("B2R15_SCORING=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
