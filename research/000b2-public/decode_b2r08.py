#!/usr/bin/env python3
"""Execute bounded B2R08 C0 decoding for the frozen whispercpp-balanced cell."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import decode_b2r07 as base

ROOT = base.ROOT
PUBLIC = base.PUBLIC
READINESS_PATH = base.READINESS_PATH
ATTEMPT_MANIFEST_PATH = base.ATTEMPT_MANIFEST_PATH
PREPROCESSING_CAPTURE_PATH = base.PREPROCESSING_CAPTURE_PATH
REBINDING_PATH = base.REBINDING_PATH
FROZEN_METHODOLOGY_PATH = base.FROZEN_METHODOLOGY_PATH
CANDIDATE_REGISTRY_PATH = base.CANDIDATE_REGISTRY_PATH
CANONICAL_CURRENT_PATH = base.CANONICAL_CURRENT_PATH
CURRENT_PATH = base.CURRENT_PATH
TASKS_PATH = base.TASKS_PATH

SCHEMA = "000b2-public-b2r08-decode-v1"
TASK = "B2R08"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-002"
CANDIDATE_ID = "whispercpp-balanced"
EXPECTED_AUTHORITY_BASE = "4fc35e9d14f949b90dbee58ddf243a36859e02bd"
EXPECTED_RUNTIME_REVISION = "371b5a7561823ab2bb32142d2751e35e7534727b"
EXPECTED_RUNTIME_TREE = "3d7ce4f956997cfa325c7556533aba5604278463"
EXPECTED_MODEL_SOURCE_REVISION = "80da2d8bfee42b0e836fc3a9890373e5defc00a6"
EXPECTED_MODEL_NAME = "ggml-small.en.bin"
EXPECTED_MODEL_BYTES = 487614201
EXPECTED_MODEL_SHA256 = "c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d"
EXPECTED_FREEZE = base.EXPECTED_FREEZE
EXPECTED_PREPROCESSING = base.EXPECTED_PREPROCESSING
EXPECTED_REBINDING = base.EXPECTED_REBINDING
EXPECTED_FROZEN_METHODOLOGY = base.EXPECTED_FROZEN_METHODOLOGY
EXPECTED_REGISTRY = base.EXPECTED_REGISTRY
EXPECTED_UTTERANCES = base.EXPECTED_UTTERANCES
REGULAR_CHUNK_SAMPLES = base.REGULAR_CHUNK_SAMPLES
FINAL_ZERO_SAMPLES = base.FINAL_ZERO_SAMPLES
FINAL_ZERO_CHUNKS = base.FINAL_ZERO_CHUNKS
RAW_TRANSCRIPT_MATERIALIZATION = base.RAW_TRANSCRIPT_MATERIALIZATION
EXPECTED_CANDIDATE_IDS = base.EXPECTED_CANDIDATE_IDS
ADAPTER_TIMEOUT_SECONDS = 21600

# Rebind only helper-level identities. The B2R07 execution path itself is never called.
base.TASK = TASK
base.CANDIDATE_ID = CANDIDATE_ID
base.EXPECTED_AUTHORITY_BASE = EXPECTED_AUTHORITY_BASE
base.EXPECTED_RUNTIME_REVISION = EXPECTED_RUNTIME_REVISION
base.EXPECTED_RUNTIME_TREE = EXPECTED_RUNTIME_TREE
base.EXPECTED_MODEL_SOURCE_REVISION = EXPECTED_MODEL_SOURCE_REVISION
base.EXPECTED_MODEL_NAME = EXPECTED_MODEL_NAME
base.EXPECTED_MODEL_BYTES = EXPECTED_MODEL_BYTES
base.EXPECTED_MODEL_SHA256 = EXPECTED_MODEL_SHA256


def require(condition: bool, message: str) -> None:
    base.require(condition, message)


def validate_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    attempt = base.load_json(ATTEMPT_MANIFEST_PATH, "frozen ATTEMPT-002 manifest")
    require(attempt.get("schema_version") == "000b2-public-attempt-002-manifest-v1", "ATTEMPT-002 schema drift")
    require(attempt.get("attempt_id") == ATTEMPT_ID, "ATTEMPT-002 id drift")
    require(attempt.get("frozen") is True and attempt.get("phase") == "PRE_PRIMARY_FROZEN", "ATTEMPT-002 freeze state drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_FREEZE, "ATTEMPT-002 freeze digest drift")

    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "ATTEMPT-002 candidate set missing")
    candidate_ids = candidate_set.get("candidate_ids")
    require(candidate_ids == EXPECTED_CANDIDATE_IDS, "frozen candidate set drift")
    require(candidate_ids[3] == CANDIDATE_ID, "candidate cell 4 drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership became mutable")
    require(candidate_set.get("frozen_methodology_sha256") == EXPECTED_FROZEN_METHODOLOGY, "frozen methodology binding drift")
    require(candidate_set.get("registry_sha256") == EXPECTED_REGISTRY, "candidate registry binding drift")
    require(base.sha256_file(FROZEN_METHODOLOGY_PATH) == EXPECTED_FROZEN_METHODOLOGY, "frozen methodology bytes drift")
    require(base.sha256_file(CANDIDATE_REGISTRY_PATH) == EXPECTED_REGISTRY, "candidate registry bytes drift")

    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "ATTEMPT-002 decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context is not OFF")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context is not OFF")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific audio transform is not OFF")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio invariant drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation invariant drift")

    readiness = base.load_json(READINESS_PATH, "recovery readiness")
    require(readiness.get("state") == "RECOVERY_READY", "recovery lane is not ready")
    require(readiness.get("active_recovery_unit") == TASK, "B2R08 is not the active recovery unit")
    require(
        readiness.get("completed_recovery_tasks")
        == ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05", "B2R06", "B2R07"],
        "B2R08 predecessor ledger drift",
    )
    require(readiness.get("qualified_workflow_change_paths") == [], "B2R08 unexpectedly authorizes workflow drift")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Qualify B2R08 only:"), "B2R08 is not the sole canonical next action")
    require("whispercpp-balanced" in next_action, "B2R08 candidate identity missing from canonical next action")
    require("Keep B2R09" in next_action, "B2R09 successor boundary missing from canonical next action")
    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict) and replacement.get("attempt_id") == ATTEMPT_ID, "replacement attempt identity drift")
    require(replacement.get("frozen") is True and replacement.get("primary_decode_entry_open") is True, "ATTEMPT-002 primary entry is not open")
    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "recovery claim guards missing")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "developer-speech claim guard drift")
    require(guards.get("comparative_result_available") is False, "comparative result opened before scoring")
    require(guards.get("production_stt_selected") is False, "production STT selected during recovery")
    require(guards.get("product_code_authorized") is False, "product code authorized during recovery")

    tasks = TASKS_PATH.read_text(encoding="utf-8")
    current = CURRENT_PATH.read_text(encoding="utf-8")
    canonical_current = CANONICAL_CURRENT_PATH.read_text(encoding="utf-8")
    require("- [x] `B2R07`" in tasks and "- [ ] `B2R08`" in tasks and "- [ ] `B2R09`" in tasks, "B2R07/B2R08/B2R09 task boundary drift")
    require("active recovery unit `B2R08`" in current, "CURRENT does not own B2R08 frontier")
    require("**Active recovery unit:** `B2R08`" in canonical_current, "canonical CURRENT_STATE does not own B2R08 frontier")

    preprocessing = base.load_json(PREPROCESSING_CAPTURE_PATH, "B2P06 preprocessing capture")
    require(base.sha256_file(PREPROCESSING_CAPTURE_PATH) == EXPECTED_PREPROCESSING, "preprocessing capture bytes drift")
    execution = preprocessing.get("execution")
    require(isinstance(execution, dict), "preprocessing execution block missing")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == EXPECTED_UTTERANCES, "preprocessing record count drift")
    require(execution.get("all_source_hashes_reverified") is True, "source hashes were not reverified in B2P06")
    require(execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "frozen preprocessing format invariant missing")

    rebinding = base.load_json(REBINDING_PATH, "B2R03 preexecution rebinding")
    require(base.sha256_file(REBINDING_PATH) == EXPECTED_REBINDING, "B2R03 rebinding bytes drift")
    require(rebinding.get("task") == "B2R03", "B2R03 rebinding task drift")
    require(rebinding.get("attempt", {}).get("attempt_id") == ATTEMPT_ID, "B2R03 attempt binding drift")
    preserved = rebinding.get("preserved_identity_guards")
    require(isinstance(preserved, dict), "B2R03 preserved identity guards missing")
    require(preserved.get("subset_manifest_sha256") == "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb", "subset identity drift")
    require(preserved.get("candidate_registry_sha256") == EXPECTED_REGISTRY, "candidate identity drift")
    require(preserved.get("c0_repository_context") == "OFF" and preserved.get("c0_test_specific_context") == "OFF", "B2R03 C0 context drift")
    environment = rebinding.get("execution_environment_rebinding")
    require(isinstance(environment, dict), "B2R03 environment rebinding missing")
    require(environment.get("bound_attempt_id") == ATTEMPT_ID, "B2R03 environment attempt binding drift")
    require(environment.get("performance_mode") == "DIAGNOSTIC", "B2R03 timing semantics drift")
    require(environment.get("comparative_performance_authorized") is False, "comparative timing unexpectedly authorized")
    return readiness, attempt, preprocessing


def runtime_provenance() -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    require(run_id.isdigit() and int(run_id) > 0, "GITHUB_RUN_ID missing or invalid")
    require(run_attempt.isdigit() and int(run_attempt) > 0, "GITHUB_RUN_ATTEMPT missing or invalid")
    return {
        "repository_revision": base.git_head(),
        "github_repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "github_run_id": int(run_id),
        "github_run_attempt": int(run_attempt),
        "github_job": os.environ.get("GITHUB_JOB", ""),
        "runner_os": os.environ.get("RUNNER_OS", ""),
        "runner_arch": os.environ.get("RUNNER_ARCH", ""),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.system(),
        "preprocessing_container_image": os.environ.get("B2R08_CONTAINER_IMAGE", ""),
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def execute(
    work_dir: Path,
    preprocessed_root: Path,
    model_path: Path,
    adapter: Path,
    build_identity_path: Path,
) -> dict[str, Any]:
    _, attempt, preprocessing = validate_authority()
    indexed = base.build_preprocessing_index(preprocessing)

    family, config = base.operational_smoke.candidate_record(CANDIDATE_ID)
    require(family.get("family") == "whisper.cpp", "candidate cell 4 family drift")
    require(family.get("runtime", {}).get("revision") == EXPECTED_RUNTIME_REVISION, "whisper.cpp runtime revision drift")
    require(family.get("model_source", {}).get("revision") == EXPECTED_MODEL_SOURCE_REVISION, "whisper.cpp model-source revision drift")
    require(config.get("id") == CANDIDATE_ID and config.get("tier") == "BALANCED", "candidate cell 4 configuration drift")
    require(config.get("model") == EXPECTED_MODEL_NAME, "candidate cell 4 model name drift")
    require(model_path.is_file() and not model_path.is_symlink(), "whisper.cpp model file missing or unsafe")
    require(model_path.name == EXPECTED_MODEL_NAME, "whisper.cpp model filename drift")
    require(model_path.stat().st_size == EXPECTED_MODEL_BYTES, "whisper.cpp model size drift")
    require(base.sha256_file(model_path) == EXPECTED_MODEL_SHA256, "whisper.cpp model SHA-256 drift")
    artifacts = base.operational_smoke.verify_artifacts(CANDIDATE_ID, config, model_path.parent)
    require(len(artifacts) == 1 and artifacts[0].get("sha256") == EXPECTED_MODEL_SHA256, "candidate artifact verification drift")

    require(adapter.is_file() and not adapter.is_symlink(), "whisper.cpp adapter binary missing or unsafe")
    build_identity = base.validate_build_identity(build_identity_path, adapter)

    work_dir.mkdir(parents=True, exist_ok=True)
    input_list = work_dir / "b2r08-inputs.tsv"
    adapter_output = work_dir / "b2r08-adapter-output.jsonl"
    lines: list[str] = []
    for uid in sorted(indexed):
        source = indexed[uid]
        partition = source.get("source_partition")
        require(isinstance(partition, str) and partition in {"test-clean", "test-other"}, f"partition drift: {uid}")
        wav_path = preprocessed_root / partition / f"{uid}.wav"
        require(wav_path.is_file() and not wav_path.is_symlink(), f"preprocessed WAV missing or unsafe: {uid}")
        require("\t" not in uid and "\t" not in str(wav_path), "tab unsafe for adapter input list")
        require(base.sha256_file(wav_path) == source.get("canonical_preprocessed_file_sha256"), f"preprocessed WAV SHA-256 drift: {uid}")
        require(wav_path.stat().st_size == source.get("canonical_preprocessed_bytes"), f"preprocessed WAV size drift: {uid}")
        lines.append(f"{uid}\t{wav_path}\n")
    input_list.write_text("".join(lines), encoding="utf-8")

    total_start = time.perf_counter()
    proc = subprocess.run(
        [str(adapter), "--model", str(model_path), "--input-list", str(input_list), "--output", str(adapter_output)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=ADAPTER_TIMEOUT_SECONDS,
    )
    require(proc.returncode == 0, f"whisper.cpp adapter failed with exit code {proc.returncode}: {proc.stdout[-4000:]}")
    adapter_rows = base.parse_adapter_output(adapter_output, indexed)

    records: list[dict[str, Any]] = []
    for uid in sorted(indexed):
        source = indexed[uid]
        observed = adapter_rows[uid]
        records.append(
            {
                "utterance_id": uid,
                "source_partition": source["source_partition"],
                "canonical_preprocessed_file_sha256": source["canonical_preprocessed_file_sha256"],
                "status": observed["status"],
                "raw_lines": observed["raw_lines"],
                "raw_transcript": observed["raw_transcript"],
                "failure": observed["failure"],
                "stream_iteration_count": observed["stream_iteration_count"],
                "speech_sample_count": observed["speech_sample_count"],
                "speech_samples_delivered": observed["speech_samples_delivered"],
                "regular_speech_chunk_count": observed["regular_speech_chunk_count"],
                "final_speech_chunk_samples": observed["final_speech_chunk_samples"],
                "zero_suffix_samples_delivered": observed["zero_suffix_samples_delivered"],
                "zero_suffix_chunks_delivered": observed["zero_suffix_chunks_delivered"],
                "decode_wall_seconds": observed["decode_wall_seconds"],
            }
        )

    decoded = sum(row["status"] == "DECODED" for row in records)
    failed = len(records) - decoded
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA,
        "task": TASK,
        "state": "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED",
        "attempt_id": ATTEMPT_ID,
        "candidate": {
            "cell_index": 4,
            "candidate_id": CANDIDATE_ID,
            "family": "whisper.cpp",
            "tier": "BALANCED",
            "runtime_revision": EXPECTED_RUNTIME_REVISION,
            "runtime_source_tree": EXPECTED_RUNTIME_TREE,
            "model_source_revision": EXPECTED_MODEL_SOURCE_REVISION,
            "model": EXPECTED_MODEL_NAME,
            "artifacts": artifacts,
            "adapter_build_identity": build_identity,
            "streaming_semantics_observed": True,
        },
        "authority": {
            "canonical_authority_base": EXPECTED_AUTHORITY_BASE,
            "attempt_manifest_path": "research/000b2-public/attempt-002-manifest.json",
            "attempt_manifest_sha256": base.sha256_file(ATTEMPT_MANIFEST_PATH),
            "attempt_freeze_digest_sha256": attempt["freeze_digest_sha256"],
            "preprocessing_capture_path": "research/000b2-public/preprocessing-capture.json",
            "preprocessing_capture_sha256": base.sha256_file(PREPROCESSING_CAPTURE_PATH),
        },
        "c0_controls": {
            "language": "en",
            "threads": 4,
            "step_ms": 500,
            "regular_chunk_samples": REGULAR_CHUNK_SAMPLES,
            "final_speech_chunk_preserved": True,
            "length_ms": 5000,
            "keep_ms": 200,
            "max_tokens": 0,
            "audio_ctx": 0,
            "beam_size": -1,
            "sampling": "GREEDY",
            "temperature_fallback": "OFF",
            "translate": False,
            "keep_context": False,
            "initial_prompt": None,
            "prompt_carryover": False,
            "vad": False,
            "timestamps": False,
            "single_segment": True,
            "use_gpu": False,
            "flash_attention": False,
            "repository_context_used": False,
            "test_specific_context_used": False,
            "candidate_specific_audio_transform_used": False,
            "identical_frozen_audio_required_across_candidates": True,
            "finalization_zero_pad_samples": FINAL_ZERO_SAMPLES,
            "zero_suffix_chunk_samples": FINAL_ZERO_CHUNKS,
            "raw_transcript_materialization": RAW_TRANSCRIPT_MATERIALIZATION,
        },
        "execution_orchestration": {
            "policy": "PREDECLARED_WALL_CLOCK_GUARD",
            "adapter_timeout_seconds": ADAPTER_TIMEOUT_SECONDS,
            "timeout_semantics": "EXECUTION_WALL_CLOCK_GUARD_ONLY_NOT_A_C0_OR_SCORING_PARAMETER",
            "adapter_invocation_count": 1,
            "adapter_process_partitioning": "SINGLE_PROCESS_FULL_FROZEN_INPUT_LIST",
            "candidate_order_changed": False,
            "frozen_input_order_changed": False,
            "c0_controls_changed": False,
        },
        "run": runtime_provenance(),
        "execution": {
            "input_count": len(records),
            "decoded_count": decoded,
            "failure_count": failed,
            "all_frozen_input_hashes_reverified": True,
            "all_speech_samples_delivered_for_decoded_records": all(
                row["status"] != "DECODED" or row["speech_samples_delivered"] == row["speech_sample_count"] for row in records
            ),
            "all_zero_suffix_samples_delivered_for_decoded_records": all(
                row["status"] != "DECODED" or row["zero_suffix_samples_delivered"] == FINAL_ZERO_SAMPLES for row in records
            ),
            "reference_transcripts_loaded_by_decoder": False,
            "accuracy_scoring_performed": False,
            "comparative_ranking_present": False,
            "performance_claim_present": False,
            "total_decode_wall_seconds": round(time.perf_counter() - total_start, 9),
            "records": records,
        },
        "claim_guards": {
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "comparative_result_available": False,
            "comparative_performance_authorized": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
            "b2r09_authorized": False,
        },
    }
    evidence["evidence_payload_sha256"] = base.sha256_bytes(base.canonical_json_bytes(evidence))
    return evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--preprocessed-root", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--adapter", required=True, type=Path)
    parser.add_argument("--build-identity", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        evidence = execute(args.work_dir, args.preprocessed_root, args.model, args.adapter, args.build_identity)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("B2R08_EXECUTION=CAPTURED")
        print(f"B2R08_SOURCE_REVISION={evidence['run']['repository_revision']}")
        print(f"B2R08_INPUTS={evidence['execution']['input_count']}")
        print(f"B2R08_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2R08_FAILURES={evidence['execution']['failure_count']}")
        print("B2R09_AUTHORIZED=NO")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        return 0
    except (base.DecodeError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"B2R08_EXECUTION=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
