#!/usr/bin/env python3
"""Execute bounded B2R09 C0 decoding for the frozen sherpa-onnx-compact cell."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import decode_b2r07 as base

ROOT = base.ROOT
PUBLIC = base.PUBLIC
ENTRY = base.ENTRY
READINESS_PATH = base.READINESS_PATH
ATTEMPT_MANIFEST_PATH = base.ATTEMPT_MANIFEST_PATH
PREPROCESSING_CAPTURE_PATH = base.PREPROCESSING_CAPTURE_PATH
REBINDING_PATH = base.REBINDING_PATH
FROZEN_METHODOLOGY_PATH = base.FROZEN_METHODOLOGY_PATH
CANDIDATE_REGISTRY_PATH = base.CANDIDATE_REGISTRY_PATH
CANONICAL_CURRENT_PATH = base.CANONICAL_CURRENT_PATH
CURRENT_PATH = base.CURRENT_PATH
TASKS_PATH = base.TASKS_PATH

SCHEMA = "000b2-public-b2r09-decode-v1"
TASK = "B2R09"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-002"
CANDIDATE_ID = "sherpa-onnx-compact"
EXPECTED_AUTHORITY_BASE = "737e2fa0422e0d1aa0dd4d5bdc0473d51cec624c"
EXPECTED_RUNTIME_RELEASE = "v1.13.7"
EXPECTED_RUNTIME_REVISION = "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e"
EXPECTED_DISTRIBUTION_VERSION = "1.13.7"
EXPECTED_MODEL_REPOSITORY = "csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26"
EXPECTED_ONNX_REVISION = "6037ea07e3abfe599ad00d418968bcf9656e7472"
EXPECTED_BPE_REVISION = "672fbf1b30579d6585301139bb363f42a0ad4a24"
EXPECTED_FREEZE = base.EXPECTED_FREEZE
EXPECTED_PREPROCESSING = base.EXPECTED_PREPROCESSING
EXPECTED_REBINDING = base.EXPECTED_REBINDING
EXPECTED_FROZEN_METHODOLOGY = base.EXPECTED_FROZEN_METHODOLOGY
EXPECTED_REGISTRY = base.EXPECTED_REGISTRY
EXPECTED_UTTERANCES = base.EXPECTED_UTTERANCES
FINAL_ZERO_SAMPLES = 10560
EXPECTED_CANDIDATE_IDS = base.EXPECTED_CANDIDATE_IDS
EXPECTED_ARTIFACTS = {
    "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx": (71083163, "563fde436d16cf7607cf408cd6b30909819d03162652ef389c2450ced3f45ac1", EXPECTED_ONNX_REVISION),
    "decoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx": (1307236, "98da299f471e38bb4e1a8df579b8cc9122d6039576a77e357b3c60f17dd83b02", EXPECTED_ONNX_REVISION),
    "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx": (259335, "d944208d660d67c8d72cd2acaeac971fa5ceb8c80e76c1968148846fedd6e297", EXPECTED_ONNX_REVISION),
    "bpe.model": (244865, "c53433de083c4a6ad12d034550ef22de68cec62c4f58932a7b6b8b2f1e743fa5", EXPECTED_BPE_REVISION),
    "tokens.txt": (5048, "49e3c2646595fd907228b3c6787069658f67b17377c60aeb8619c4551b2316fb", EXPECTED_ONNX_REVISION),
}


def require(condition: bool, message: str) -> None:
    base.require(condition, message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


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
    require(candidate_ids[4] == CANDIDATE_ID, "candidate cell 5 drift")
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
    require(readiness.get("active_recovery_unit") == TASK, "B2R09 is not the active recovery unit")
    require(
        readiness.get("completed_recovery_tasks")
        == ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05", "B2R06", "B2R07", "B2R08"],
        "B2R09 predecessor ledger drift",
    )
    require(readiness.get("qualified_workflow_change_paths") == [], "B2R09 unexpectedly authorizes workflow drift")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Qualify B2R09 only:"), "B2R09 is not the sole canonical next action")
    require(CANDIDATE_ID in next_action, "B2R09 candidate identity missing from canonical next action")
    require("Keep B2R10" in next_action, "B2R10 successor boundary missing from canonical next action")
    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict) and replacement.get("attempt_id") == ATTEMPT_ID, "replacement attempt identity drift")
    require(replacement.get("frozen") is True and replacement.get("primary_decode_entry_open") is True, "ATTEMPT-002 primary entry is not open")
    guards = readiness.get("claim_guards")
    require(guards == {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
    }, "recovery claim guards drift")

    tasks = TASKS_PATH.read_text(encoding="utf-8")
    current = CURRENT_PATH.read_text(encoding="utf-8")
    canonical_current = CANONICAL_CURRENT_PATH.read_text(encoding="utf-8")
    require("- [x] `B2R08`" in tasks and "- [ ] `B2R09`" in tasks and "- [ ] `B2R10`" in tasks, "B2R08/B2R09/B2R10 task boundary drift")
    require("active recovery unit `B2R09`" in current, "CURRENT does not own B2R09 frontier")
    require("**Active recovery unit:** `B2R09`" in canonical_current, "canonical CURRENT_STATE does not own B2R09 frontier")

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


def distribution_manifest() -> tuple[str, int]:
    distribution = importlib.metadata.distribution("sherpa-onnx")
    files = distribution.files or []
    rows: list[str] = []
    for item in sorted(files, key=lambda value: str(value)):
        path = Path(distribution.locate_file(item))
        if path.is_file() and not path.is_symlink():
            rows.append(f"{item}\t{base.sha256_file(path)}")
    require(rows, "sherpa-onnx distribution manifest is empty")
    return sha256_bytes(("\n".join(rows) + "\n").encode("utf-8")), len(rows)


def runtime_provenance() -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    require(run_id.isdigit() and int(run_id) > 0, "GITHUB_RUN_ID missing or invalid")
    require(run_attempt.isdigit() and int(run_attempt) > 0, "GITHUB_RUN_ATTEMPT missing or invalid")
    version = importlib.metadata.version("sherpa-onnx")
    require(version == EXPECTED_DISTRIBUTION_VERSION, "sherpa-onnx distribution version drift")
    manifest_sha, manifest_count = distribution_manifest()
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
        "sherpa_onnx_distribution": "sherpa-onnx",
        "sherpa_onnx_distribution_version": version,
        "sherpa_onnx_distribution_manifest_sha256": manifest_sha,
        "sherpa_onnx_distribution_file_count": manifest_count,
        "canonical_runtime_release": EXPECTED_RUNTIME_RELEASE,
        "canonical_runtime_revision": EXPECTED_RUNTIME_REVISION,
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def verify_candidate(model_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    family, config = base.operational_smoke.candidate_record(CANDIDATE_ID)
    require(family.get("family") == "sherpa-onnx", "candidate cell 5 family drift")
    runtime = family.get("runtime", {})
    require(runtime.get("release") == EXPECTED_RUNTIME_RELEASE, "sherpa runtime release drift")
    require(runtime.get("revision") == EXPECTED_RUNTIME_REVISION, "sherpa runtime revision drift")
    model_source = family.get("model_source", {})
    require(model_source.get("repository") == EXPECTED_MODEL_REPOSITORY, "sherpa model repository drift")
    require(model_source.get("onnx_revision") == EXPECTED_ONNX_REVISION, "sherpa ONNX revision drift")
    require(model_source.get("head_observed") == EXPECTED_BPE_REVISION, "sherpa BPE revision drift")
    require(model_source.get("chunk_size") == 16 and model_source.get("left_context_frames") == 128, "sherpa streaming geometry drift")
    require(config.get("id") == CANDIDATE_ID and config.get("tier") == "COMPACT", "candidate cell 5 configuration drift")
    require(config.get("model") == "INT8 ONNX", "candidate cell 5 model label drift")
    c0 = config.get("c0", {})
    require(c0.get("language") == "en" and c0.get("hotwords") == "OFF" and c0.get("repository_context") == "OFF" and c0.get("grammar") == "OFF", "sherpa C0 contract drift")

    observed = base.operational_smoke.verify_artifacts(CANDIDATE_ID, config, model_root)
    require(len(observed) == len(EXPECTED_ARTIFACTS), "candidate artifact cardinality drift")
    by_path = {row["path"]: row for row in observed}
    require(set(by_path) == set(EXPECTED_ARTIFACTS), "candidate artifact membership drift")
    rows: list[dict[str, Any]] = []
    for path, (size, digest, revision) in EXPECTED_ARTIFACTS.items():
        row = by_path[path]
        require(row.get("size_bytes") == size and row.get("sha256") == digest, f"candidate artifact identity drift: {path}")
        rows.append({"path": path, "size_bytes": size, "sha256": digest, "source_revision": revision})
    return family, config, rows


def execute(preprocessed_root: Path, model_root: Path) -> dict[str, Any]:
    _, attempt, preprocessing = validate_authority()
    indexed = base.build_preprocessing_index(preprocessing)
    family, config, artifacts = verify_candidate(model_root)

    import numpy as np
    import sherpa_onnx

    encoder = base.operational_smoke.find_artifact(model_root, "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx")
    decoder = base.operational_smoke.find_artifact(model_root, "decoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx")
    joiner = base.operational_smoke.find_artifact(model_root, "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx")
    tokens = base.operational_smoke.find_artifact(model_root, "tokens.txt")

    recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=str(tokens),
        encoder=str(encoder),
        decoder=str(decoder),
        joiner=str(joiner),
        num_threads=4,
        provider="cpu",
        sample_rate=16000,
        feature_dim=80,
        decoding_method="greedy_search",
        max_active_paths=4,
        lm="",
        lm_scale=0.1,
        lodr_fst="",
        lodr_scale=-0.1,
        hotwords_file="",
        hotwords_score=1.5,
        modeling_unit="",
        bpe_vocab="",
        blank_penalty=0.0,
    )

    records: list[dict[str, Any]] = []
    total_start = time.perf_counter()
    for uid in sorted(indexed):
        source = indexed[uid]
        partition = source.get("source_partition")
        require(isinstance(partition, str) and partition in {"test-clean", "test-other"}, f"partition drift: {uid}")
        wav_path = preprocessed_root / partition / f"{uid}.wav"
        require(wav_path.is_file() and not wav_path.is_symlink(), f"preprocessed WAV missing or unsafe: {uid}")
        require(base.sha256_file(wav_path) == source.get("canonical_preprocessed_file_sha256"), f"preprocessed WAV SHA-256 drift: {uid}")
        require(wav_path.stat().st_size == source.get("canonical_preprocessed_bytes"), f"preprocessed WAV size drift: {uid}")

        started = time.perf_counter()
        try:
            audio = np.asarray(base.operational_smoke.read_wav_float(wav_path), dtype=np.float32)
            stream = recognizer.create_stream()
            stream.accept_waveform(16000, audio)
            stream.accept_waveform(16000, np.zeros(FINAL_ZERO_SAMPLES, dtype=np.float32))
            stream.input_finished()
            decode_steps = 0
            while recognizer.is_ready(stream):
                recognizer.decode_stream(stream)
                decode_steps += 1
                if decode_steps > 10000:
                    raise RuntimeError("sherpa decode exceeded decode-step safety bound")
            result = recognizer.get_result(stream)
            transcript = getattr(result, "text", "") or ""
            require(isinstance(transcript, str), f"sherpa transcript type drift: {uid}")
            records.append({
                "utterance_id": uid,
                "source_partition": partition,
                "canonical_preprocessed_file_sha256": source["canonical_preprocessed_file_sha256"],
                "status": "DECODED",
                "raw_transcript": transcript,
                "failure": None,
                "decode_steps": decode_steps,
                "speech_sample_count": int(audio.shape[0]),
                "speech_samples_delivered": int(audio.shape[0]),
                "zero_suffix_samples_delivered": FINAL_ZERO_SAMPLES,
                "elapsed_seconds_diagnostic": time.perf_counter() - started,
            })
        except Exception as error:  # preserve bounded per-record failures instead of hiding them
            records.append({
                "utterance_id": uid,
                "source_partition": partition,
                "canonical_preprocessed_file_sha256": source["canonical_preprocessed_file_sha256"],
                "status": "FAILED",
                "raw_transcript": "",
                "failure": {"type": type(error).__name__, "message": str(error)},
                "decode_steps": None,
                "speech_sample_count": None,
                "speech_samples_delivered": None,
                "zero_suffix_samples_delivered": None,
                "elapsed_seconds_diagnostic": time.perf_counter() - started,
            })

    decoded_count = sum(row["status"] == "DECODED" for row in records)
    failure_count = sum(row["status"] == "FAILED" for row in records)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "task": TASK,
        "state": "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED",
        "attempt_id": ATTEMPT_ID,
        "candidate": {
            "cell_index": 5,
            "candidate_id": CANDIDATE_ID,
            "family": "sherpa-onnx",
            "tier": "COMPACT",
            "model": "INT8 ONNX",
            "runtime_release": EXPECTED_RUNTIME_RELEASE,
            "runtime_revision": EXPECTED_RUNTIME_REVISION,
            "model_repository": EXPECTED_MODEL_REPOSITORY,
            "onnx_revision": EXPECTED_ONNX_REVISION,
            "bpe_revision": EXPECTED_BPE_REVISION,
            "artifacts": artifacts,
        },
        "authority": {
            "canonical_authority_base": EXPECTED_AUTHORITY_BASE,
            "attempt_freeze_digest_sha256": EXPECTED_FREEZE,
            "preprocessing_capture_sha256": EXPECTED_PREPROCESSING,
            "preexecution_rebinding_sha256": EXPECTED_REBINDING,
            "frozen_methodology_sha256": EXPECTED_FROZEN_METHODOLOGY,
            "candidate_registry_sha256": EXPECTED_REGISTRY,
        },
        "run": runtime_provenance(),
        "c0_controls": {
            "language": "en",
            "num_threads": 4,
            "provider": "cpu",
            "sample_rate_hz": 16000,
            "feature_dim": 80,
            "decoding_method": "greedy_search",
            "max_active_paths": 4,
            "chunk_size": 16,
            "left_context_frames": 128,
            "lm": "",
            "lodr_fst": "",
            "hotwords_file": "",
            "modeling_unit": "",
            "bpe_vocab": "",
            "blank_penalty": 0.0,
            "repository_context_used": False,
            "test_specific_context_used": False,
            "candidate_specific_audio_transform_used": False,
            "identical_frozen_audio_required_across_candidates": True,
            "finalization_zero_pad_samples": FINAL_ZERO_SAMPLES,
        },
        "execution": {
            "input_count": len(records),
            "decoded_count": decoded_count,
            "failure_count": failure_count,
            "all_frozen_input_hashes_reverified": True,
            "reference_transcripts_loaded_by_decoder": False,
            "accuracy_scoring_performed": False,
            "comparative_ranking_present": False,
            "performance_claim_present": False,
            "total_elapsed_seconds_diagnostic": time.perf_counter() - total_start,
            "records": records,
        },
        "claim_guards": {
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "comparative_result_available": False,
            "comparative_performance_authorized": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
            "b2r10_authorized": False,
        },
    }
    require(payload["execution"]["input_count"] == EXPECTED_UTTERANCES, "B2R09 execution input count drift")
    require(decoded_count + failure_count == EXPECTED_UTTERANCES, "B2R09 execution accounting drift")
    payload["evidence_payload_sha256"] = sha256_bytes(canonical_json_bytes(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preprocessed-root", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = execute(args.preprocessed_root, args.model_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"B2R09_EVIDENCE_SHA256={base.sha256_file(args.output)}")
    print(f"B2R09_PAYLOAD_SHA256={evidence['evidence_payload_sha256']}")
    print(f"B2R09_DECODED={evidence['execution']['decoded_count']}")
    print(f"B2R09_FAILURES={evidence['execution']['failure_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
