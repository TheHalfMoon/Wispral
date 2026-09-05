#!/usr/bin/env python3
"""Verify the bounded B2R03 ATTEMPT-002 preexecution evidence rebinding."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
RECOVERY_READINESS = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CURRENT_STATE = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
STATE = PUBLIC / "attempt-002-preexecution-state.json"
REBIND = PUBLIC / "b2r03-preexecution-rebinding.json"
HISTORICAL_ATTEMPT = PUBLIC / "attempt-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
ENVIRONMENT = PUBLIC / "execution-environment.json"
B2R02 = PUBLIC / "b2r02-moonshine-streaming-qualification.json"
HARNESS = PUBLIC / "moonshine_streaming_c0.py"

ATTEMPT_001 = "000B2-PUBLIC-ATTEMPT-001"
ATTEMPT_002 = "000B2-PUBLIC-ATTEMPT-002"
CANONICAL_AUTHORITY_BASE = "ddbb2a86966107857fd3f8983b2bee6cf47b810c"
B2R02_MERGE = "8dc723efff01fd4461688962a2891bf9e8841f4d"
B2R02_RUN = 33991218657
SUBSET_SHA256 = "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb"
SUBSET_FREEZE_SHA256 = "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242"
CANDIDATE_REGISTRY_SHA256 = "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f"
CANDIDATE_REVALIDATION_SHA256 = "aeca7b824d14388271b04c2dad953cecf5c47cd53cf3f70b766f4fe4dcac54b8"
METHODOLOGY_SHA256 = "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df"
SCORER_SHA256 = "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1"
SCORER_CONFIG_SHA256 = "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3"
WER_ADAPTER_SHA256 = "581a0e4b0bb91d55a252b92871dbb1246b5fbc4466a5d94bceb35862744fc023"
PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
PREPROCESSING_BLOB = "89cbb28b7961042a1793c694692fe822c9414370"
ENVIRONMENT_SHA256 = "2b8b521c28c771293648cbf86c7c1b20e820bacfc065074d7cfe2555745387ed"
ENVIRONMENT_BLOB = "caf814bcb5e42fd769e6df1d9a54c1164535f86c"
ENVIRONMENT_ID = "x86_64:AMD EPYC 9V74 80-Core Processor:3e80c2c63bf88d13"
HARDWARE_FINGERPRINT_SHA256 = "3e80c2c63bf88d13a10c358feaa250672a5250fb9cbc90e59bdb397912cac5cd"
B2R02_BLOB = "90fb99d2c6ef1d7cd9d698e70a9e0a9837155bce"
HARNESS_SHA256 = "c0f0093cda7ca036c8a97178364b3840ce7093386a8cb711ccef5f183a4453c0"
MOONSHINE_REVISION = "234f60faa0eb388b01cdf7e60aca232af37aefda"
MODEL_ASSET_REVISION = "quantized_26_08_21"


class VerifyError(RuntimeError):
    """Fail-closed B2R03 verification error."""


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
    relative = path.relative_to(ROOT).as_posix()
    return git_output("rev-parse", f"HEAD:{relative}")


def exact_claim_guards(value: Any, *, include_attempt_freeze: bool) -> None:
    require(isinstance(value, dict), "claim guards must be an object")
    expected = {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "comparative_performance_authorized": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
    }
    if include_attempt_freeze:
        expected.update({
            "attempt_002_frozen": False,
            "attempt_002_primary_decode_authorized": False,
            "b2r04_authorized": False,
        })
    else:
        expected.update({
            "attempt_002_primary_decode_authorized": False,
            "b2r04_authorized": False,
        })
    require(value == expected, "B2R03 claim-guard drift")


def verify_recovery_authority() -> None:
    readiness = load_json(RECOVERY_READINESS)
    require(readiness.get("completed_recovery_tasks") == ["B2R01", "B2R02"], "canonical recovery prefix drift")
    require(readiness.get("active_recovery_unit") == "B2R03", "B2R03 is not the canonical active unit")
    require(readiness.get("qualified_workflow_change_paths") == [], "B2R03 must not inherit workflow-change authority")
    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict), "replacement attempt authority missing")
    require(replacement.get("attempt_id") == ATTEMPT_002, "replacement attempt id drift")
    require(replacement.get("required") is True, "ATTEMPT-002 requirement weakened")
    require(replacement.get("frozen") is False, "ATTEMPT-002 frozen before B2R04")
    require(replacement.get("primary_decode_entry_open") is False, "ATTEMPT-002 primary decoding opened before B2R04")

    tasks = TASKS.read_text(encoding="utf-8")
    require("- [x] `B2R01`" in tasks and "- [x] `B2R02`" in tasks, "recovery predecessors are not complete")
    require("- [ ] `B2R03`" in tasks, "B2R03 task must remain pending before reconciliation")
    require("- [ ] `B2R04`" in tasks, "B2R04 must remain unauthorized during B2R03 task execution")
    current = CURRENT.read_text(encoding="utf-8")
    state = CURRENT_STATE.read_text(encoding="utf-8")
    for text, label in ((current, "CURRENT"), (state, "CURRENT_STATE")):
        require("**Active recovery unit:** `B2R03`" in text, f"{label} does not authorize B2R03")
        require(str(B2R02_RUN) in text and B2R02_MERGE in text, f"{label} lost B2R02 transition proof")
    require("B2R04" in current and "unauthorized" in current.lower(), "CURRENT does not preserve B2R04 closure")


def verify_state(require_git: bool) -> dict[str, Any]:
    state = load_json(STATE)
    require(set(state) == {
        "schema_version", "task", "lane", "attempt_id", "phase", "frozen",
        "candidate_decoding_started", "primary_decoding_started", "canonical_authority_base",
        "recovery_predecessor", "preserved_identities", "claim_guards",
    }, "ATTEMPT-002 preexecution state key drift")
    require(state.get("schema_version") == "000b2-public-attempt-002-preexecution-state-v1", "state schema drift")
    require(state.get("task") == "B2R03" and state.get("lane") == "PUBLIC_CORPUS", "state task/lane drift")
    require(state.get("attempt_id") == ATTEMPT_002, "state attempt id drift")
    require(state.get("phase") == "PRE_PRIMARY_CAPTURE", "state phase drift")
    require(state.get("frozen") is False, "B2R03 must not freeze ATTEMPT-002")
    require(state.get("candidate_decoding_started") is False, "candidate decoding started during B2R03")
    require(state.get("primary_decoding_started") is False, "primary decoding started during B2R03")
    require(state.get("canonical_authority_base") == CANONICAL_AUTHORITY_BASE, "state canonical authority base drift")
    require(state.get("recovery_predecessor") == {
        "task": "B2R02",
        "canonical_task_merge": B2R02_MERGE,
        "post_merge_recovery_run_id": B2R02_RUN,
    }, "state recovery predecessor drift")
    require(state.get("preserved_identities") == {
        "subset_manifest_sha256": SUBSET_SHA256,
        "subset_freeze_digest_sha256": SUBSET_FREEZE_SHA256,
        "candidate_registry_sha256": CANDIDATE_REGISTRY_SHA256,
        "candidate_revalidation_sha256": CANDIDATE_REVALIDATION_SHA256,
        "frozen_methodology_sha256": METHODOLOGY_SHA256,
        "core_scorer_sha256": SCORER_SHA256,
        "core_config_sha256": SCORER_CONFIG_SHA256,
        "public_wer_adapter_sha256": WER_ADAPTER_SHA256,
        "corrected_moonshine_harness_sha256": HARNESS_SHA256,
    }, "state preserved identity drift")
    exact_claim_guards(state.get("claim_guards"), include_attempt_freeze=False)
    if require_git:
        require(len(git_blob(STATE)) == 40, "ATTEMPT-002 state is not committed")
    return state


def verify_historical_sources(require_git: bool) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    attempt = load_json(HISTORICAL_ATTEMPT)
    preprocessing = load_json(PREPROCESSING)
    environment = load_json(ENVIRONMENT)
    b2r02 = load_json(B2R02)

    require(attempt.get("attempt_id") == ATTEMPT_001 and attempt.get("frozen") is True, "historical ATTEMPT-001 manifest drift")
    authority = attempt.get("authority")
    require(isinstance(authority, dict), "historical attempt authority missing")
    subset = authority.get("subset")
    preprocessing_authority = authority.get("preprocessing")
    env_authority = authority.get("execution_environment")
    candidates = authority.get("candidate_revalidation")
    require(isinstance(subset, dict) and subset.get("sha256") == SUBSET_SHA256, "historical subset binding drift")
    require(isinstance(subset, dict) and subset.get("freeze_digest_sha256") == SUBSET_FREEZE_SHA256, "historical subset freeze digest drift")
    require(isinstance(candidates, dict) and candidates.get("sha256") == CANDIDATE_REVALIDATION_SHA256, "historical candidate revalidation binding drift")
    require(isinstance(preprocessing_authority, dict) and preprocessing_authority.get("sha256") == PREPROCESSING_SHA256, "historical preprocessing binding drift")
    require(isinstance(env_authority, dict) and env_authority.get("sha256") == ENVIRONMENT_SHA256, "historical environment binding drift")
    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict) and candidate_set.get("registry_sha256") == CANDIDATE_REGISTRY_SHA256, "candidate registry drift")
    require(candidate_set.get("frozen_methodology_sha256") == METHODOLOGY_SHA256, "frozen methodology drift")
    scoring = attempt.get("scoring")
    require(isinstance(scoring, dict), "historical scoring block missing")
    require(scoring.get("core_scorer_sha256") == SCORER_SHA256, "core scorer drift")
    require(scoring.get("core_config_sha256") == SCORER_CONFIG_SHA256, "core scorer config drift")
    require(scoring.get("public_wer_adapter_sha256") == WER_ADAPTER_SHA256, "public WER adapter drift")
    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "historical decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "C0 repository context drift")
    require(contract.get("c0_test_specific_context") == "OFF", "C0 test-specific context drift")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific audio transform drift")

    require(sha256_file(PREPROCESSING) == PREPROCESSING_SHA256, "preprocessing evidence bytes drift")
    prep_attempt = preprocessing.get("attempt")
    execution = preprocessing.get("execution")
    require(isinstance(prep_attempt, dict) and prep_attempt.get("attempt_id") == ATTEMPT_001, "preprocessing source attempt drift")
    require(isinstance(execution, dict), "preprocessing execution evidence missing")
    require(execution.get("preprocessed_file_count") == 240, "preprocessing record count drift")
    require(execution.get("all_source_hashes_reverified") is True, "preprocessing source hashes are not verified")
    require(execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "preprocessing output contract drift")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240, "preprocessing does not preserve 240 exact records")

    require(sha256_file(ENVIRONMENT) == ENVIRONMENT_SHA256, "environment evidence bytes drift")
    env = environment.get("environment")
    require(isinstance(env, dict), "environment payload missing")
    require(env.get("environment_id") == ENVIRONMENT_ID, "environment id drift")
    require(env.get("hardware_fingerprint_sha256") == HARDWARE_FINGERPRINT_SHA256, "hardware fingerprint drift")
    require(env.get("performance_mode") == "DIAGNOSTIC", "environment performance mode drift")
    require(env.get("comparative_performance_authorized") is False, "environment comparative performance authority drift")
    ordering = env.get("ordering")
    require(isinstance(ordering, dict) and ordering.get("attempt_id") == ATTEMPT_001, "environment source attempt drift")
    require(ordering.get("attempt_time_authority") is False, "historical environment cannot create chronology authority")
    require(ordering.get("independent_chronology_attestation") is False, "historical environment chronology attestation drift")

    require(b2r02.get("task") == "B2R02", "B2R02 qualification task drift")
    require(b2r02.get("harness_sha256") == HARNESS_SHA256, "corrected Moonshine harness binding drift")
    runtime = b2r02.get("runtime_model_identity_basis")
    require(isinstance(runtime, dict), "B2R02 runtime/model identity basis missing")
    require(runtime.get("runtime_revision") == MOONSHINE_REVISION, "Moonshine runtime revision drift")
    require(runtime.get("runtime_distribution") == "moonshine-voice", "Moonshine distribution drift")
    require(runtime.get("runtime_distribution_version") == "0.1.5", "Moonshine distribution version drift")
    require(runtime.get("model_asset_revision") == MODEL_ASSET_REVISION, "Moonshine model asset revision drift")
    b2r02_guards = b2r02.get("claim_guards")
    require(isinstance(b2r02_guards, dict), "B2R02 claim guards missing")
    require(b2r02_guards.get("primary_decode_performed") is False, "B2R02 unexpectedly performed primary decode")
    require(b2r02_guards.get("attempt_002_primary_decode_authorized") is False, "B2R02 opened ATTEMPT-002 primary decoding")
    require(sha256_file(HARNESS) == HARNESS_SHA256, "corrected Moonshine harness bytes drift")

    if require_git:
        require(git_blob(PREPROCESSING) == PREPROCESSING_BLOB, "historical preprocessing git blob drift")
        require(git_blob(ENVIRONMENT) == ENVIRONMENT_BLOB, "historical environment git blob drift")
        require(git_blob(B2R02) == B2R02_BLOB, "B2R02 qualification git blob drift")
    return attempt, preprocessing, environment, b2r02


def verify_rebinding(state: dict[str, Any], require_git: bool) -> None:
    evidence = load_json(REBIND)
    require(set(evidence) == {
        "schema_version", "task", "lane", "state", "attempt",
        "preprocessing_rebinding", "execution_environment_rebinding",
        "preserved_identity_guards", "corrected_c0_binding", "claim_guards",
    }, "B2R03 rebinding evidence key drift")
    require(evidence.get("schema_version") == "000b2-public-b2r03-preexecution-rebinding-v1", "rebinding schema drift")
    require(evidence.get("task") == "B2R03" and evidence.get("lane") == "PUBLIC_CORPUS", "rebinding task/lane drift")
    require(evidence.get("state") == "ATTEMPT_002_PREEXECUTION_EVIDENCE_BOUND", "rebinding state drift")

    attempt = evidence.get("attempt")
    require(isinstance(attempt, dict), "rebinding attempt block missing")
    require(attempt.get("attempt_id") == ATTEMPT_002, "rebinding attempt id drift")
    require(attempt.get("phase") == "PRE_PRIMARY_CAPTURE", "rebinding phase drift")
    require(attempt.get("canonical_authority_base") == CANONICAL_AUTHORITY_BASE, "rebinding authority base drift")
    require(attempt.get("candidate_decoding_started") is False, "candidate decoding started during rebinding")
    require(attempt.get("primary_decoding_started") is False, "primary decoding started during rebinding")
    require(attempt.get("frozen") is False, "B2R03 rebinding froze ATTEMPT-002")
    require(attempt.get("preexecution_state_path") == "research/000b2-public/attempt-002-preexecution-state.json", "state path drift")
    require(attempt.get("preexecution_state_sha256") == sha256_file(STATE), "state digest binding drift")
    if require_git:
        require(attempt.get("preexecution_state_git_blob_sha1") == git_blob(STATE), "state git-blob binding drift")

    prep = evidence.get("preprocessing_rebinding")
    require(isinstance(prep, dict), "preprocessing rebinding missing")
    require(prep.get("reuse_mode") == "CRYPTOGRAPHIC_PROVENANCE_REBIND", "preprocessing reuse mode drift")
    require(prep.get("source_attempt_id") == ATTEMPT_001 and prep.get("bound_attempt_id") == ATTEMPT_002, "preprocessing attempt rebinding drift")
    require(prep.get("source_evidence_path") == "research/000b2-public/preprocessing-capture.json", "preprocessing source path drift")
    require(prep.get("source_evidence_sha256") == PREPROCESSING_SHA256, "preprocessing source digest drift")
    require(prep.get("source_evidence_git_blob_sha1") == PREPROCESSING_BLOB, "preprocessing source git blob drift")
    require(prep.get("preprocessed_file_count") == 240, "preprocessing rebind count drift")
    require(prep.get("all_source_hashes_reverified") is True, "preprocessing rebind lost source-hash proof")
    require(prep.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "preprocessing rebind lost output-format proof")
    require(prep.get("source_chronology_reused") is False, "preprocessing rebinding must not reuse source chronology")
    require(prep.get("no_result_driven_input_change") is True, "preprocessing rebinding permits result-driven change")

    environment = evidence.get("execution_environment_rebinding")
    require(isinstance(environment, dict), "environment rebinding missing")
    require(environment.get("reuse_mode") == "CRYPTOGRAPHIC_PROVENANCE_REBIND", "environment reuse mode drift")
    require(environment.get("source_attempt_id") == ATTEMPT_001 and environment.get("bound_attempt_id") == ATTEMPT_002, "environment attempt rebinding drift")
    require(environment.get("source_evidence_path") == "research/000b2-public/execution-environment.json", "environment source path drift")
    require(environment.get("source_evidence_sha256") == ENVIRONMENT_SHA256, "environment source digest drift")
    require(environment.get("source_evidence_git_blob_sha1") == ENVIRONMENT_BLOB, "environment source git blob drift")
    require(environment.get("environment_id") == ENVIRONMENT_ID, "environment rebind id drift")
    require(environment.get("hardware_fingerprint_sha256") == HARDWARE_FINGERPRINT_SHA256, "environment rebind fingerprint drift")
    require(environment.get("performance_mode") == "DIAGNOSTIC", "environment rebind performance mode drift")
    require(environment.get("comparative_performance_authorized") is False, "environment rebind opened comparative performance")
    require(environment.get("source_chronology_reused") is False, "environment rebind must not reuse chronology")
    require(environment.get("fresh_hardware_claim_created") is False, "environment rebind fabricates fresh hardware evidence")
    require(environment.get("candidate_run_runtime_observations_must_be_preserved_separately") is True, "candidate runtime observation boundary weakened")

    identities = evidence.get("preserved_identity_guards")
    require(identities == {
        "subset_manifest_sha256": SUBSET_SHA256,
        "subset_freeze_digest_sha256": SUBSET_FREEZE_SHA256,
        "candidate_registry_sha256": CANDIDATE_REGISTRY_SHA256,
        "candidate_revalidation_sha256": CANDIDATE_REVALIDATION_SHA256,
        "frozen_methodology_sha256": METHODOLOGY_SHA256,
        "core_scorer_sha256": SCORER_SHA256,
        "core_config_sha256": SCORER_CONFIG_SHA256,
        "public_wer_adapter_sha256": WER_ADAPTER_SHA256,
        "c0_repository_context": "OFF",
        "c0_test_specific_context": "OFF",
        "candidate_specific_audio_transform": "OFF",
    }, "preserved B2R03 identity guard drift")
    require(state["preserved_identities"]["subset_manifest_sha256"] == identities["subset_manifest_sha256"], "state/evidence subset binding mismatch")
    require(state["preserved_identities"]["corrected_moonshine_harness_sha256"] == HARNESS_SHA256, "state corrected harness binding mismatch")

    corrected = evidence.get("corrected_c0_binding")
    require(corrected == {
        "qualification_path": "research/000b2-public/b2r02-moonshine-streaming-qualification.json",
        "qualification_git_blob_sha1": B2R02_BLOB,
        "harness_path": "research/000b2-public/moonshine_streaming_c0.py",
        "harness_sha256": HARNESS_SHA256,
        "runtime_revision": MOONSHINE_REVISION,
        "runtime_distribution": "moonshine-voice",
        "runtime_distribution_version": "0.1.5",
        "model_asset_revision": MODEL_ASSET_REVISION,
    }, "corrected C0 binding drift")
    exact_claim_guards(evidence.get("claim_guards"), include_attempt_freeze=True)


def verify_no_primary_outputs() -> None:
    for relative in (
        "research/000b2-public/raw",
        "research/000b2-public/preprocessed",
        "research/000b2-public/transcripts",
        "research/000b2-public/attempt-002-raw",
        "research/000b2-public/attempt-002-transcripts",
        "research/000b2-public/attempt-002-results.json",
    ):
        require(not (ROOT / relative).exists(), f"primary/output surface exists during B2R03: {relative}")


def verify(*, require_git: bool = True) -> None:
    verify_recovery_authority()
    state = verify_state(require_git)
    verify_historical_sources(require_git)
    verify_rebinding(state, require_git)
    verify_no_primary_outputs()
    print("B2R03_PREEXECUTION_REBINDING=PASS")
    print("B2R03_PREPROCESSING_REUSE_MODE=CRYPTOGRAPHIC_PROVENANCE_REBIND")
    print("B2R03_ENVIRONMENT_REUSE_MODE=CRYPTOGRAPHIC_PROVENANCE_REBIND")
    print("B2R03_FRESH_HARDWARE_CLAIM_CREATED=NO")
    print("B2R03_SOURCE_CHRONOLOGY_REUSED=NO")
    print("ATTEMPT_002_FROZEN=NO")
    print("ATTEMPT_002_PRIMARY_DECODE_AUTHORIZED=NO")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filesystem-only", action="store_true", help="Skip Git blob checks; intended only for isolated syntax/fixture validation.")
    args = parser.parse_args()
    try:
        verify(require_git=not args.filesystem_only)
        return 0
    except (VerifyError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"B2R03_PREEXECUTION_REBINDING=FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"B2R03_PREEXECUTION_REBINDING=FAIL: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
