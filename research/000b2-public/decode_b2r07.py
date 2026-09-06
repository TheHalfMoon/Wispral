#!/usr/bin/env python3
"""Execute bounded B2R07 C0 decoding for the frozen whispercpp-compact cell."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
ENTRY = ROOT / "research" / "000b2-entry"
sys.path.insert(0, str(ENTRY))

import operational_smoke  # noqa: E402

READINESS_PATH = PUBLIC / "recovery-readiness.json"
ATTEMPT_MANIFEST_PATH = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING_CAPTURE_PATH = PUBLIC / "preprocessing-capture.json"
REBINDING_PATH = PUBLIC / "b2r03-preexecution-rebinding.json"
FROZEN_METHODOLOGY_PATH = ROOT / "research" / "000b1" / "frozen-methodology.json"
CANDIDATE_REGISTRY_PATH = ROOT / "research" / "000b1" / "qualified-candidates.json"
CANONICAL_CURRENT_PATH = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
CURRENT_PATH = ROOT / "specs" / "CURRENT.md"
TASKS_PATH = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
ADAPTER_SOURCE_PATH = PUBLIC / "whispercpp-adapter" / "adapter.cpp"
ADAPTER_CMAKE_PATH = PUBLIC / "whispercpp-adapter" / "CMakeLists.txt"

SCHEMA = "000b2-public-b2r07-decode-v1"
TASK = "B2R07"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-002"
CANDIDATE_ID = "whispercpp-compact"
EXPECTED_AUTHORITY_BASE = "16104eacf2d571276452d173ddb54c089faccd0e"
EXPECTED_RUNTIME_REVISION = "371b5a7561823ab2bb32142d2751e35e7534727b"
EXPECTED_RUNTIME_TREE = "3d7ce4f956997cfa325c7556533aba5604278463"
EXPECTED_MODEL_SOURCE_REVISION = "80da2d8bfee42b0e836fc3a9890373e5defc00a6"
EXPECTED_MODEL_NAME = "ggml-base.en.bin"
EXPECTED_MODEL_BYTES = 147964211
EXPECTED_MODEL_SHA256 = "a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002"
EXPECTED_FREEZE = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
EXPECTED_PREPROCESSING = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_REBINDING = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
EXPECTED_FROZEN_METHODOLOGY = "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df"
EXPECTED_REGISTRY = "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f"
EXPECTED_UTTERANCES = 240
REGULAR_CHUNK_SAMPLES = 8000
FINAL_ZERO_SAMPLES = 10560
FINAL_ZERO_CHUNKS = [8000, 2560]
RAW_TRANSCRIPT_MATERIALIZATION = "STREAM_CPP_COMMIT_EVERY_9_PLUS_FINAL_PENDING"
EXPECTED_CANDIDATE_IDS = [
    "moonshine-compact",
    "moonshine-balanced",
    "whispercpp-compact",
    "whispercpp-balanced",
    "sherpa-onnx-compact",
    "sherpa-onnx-balanced",
]
SHA40 = set("0123456789abcdef")


class DecodeError(ValueError):
    """Raised when B2R07 authority or execution invariants fail closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DecodeError(message)


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DecodeError(f"unable to load {label}: {path}: {error}") from error
    require(isinstance(value, dict), f"{label} root must be an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def reconstruct_stream_text(iterations: list[str]) -> str:
    result = ""
    for committed in range(9, len(iterations) + 1, 9):
        result += iterations[committed - 1] + "\n"
    if iterations and len(iterations) % 9:
        result += iterations[-1]
    return result


def git_head() -> str:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    ).stdout.strip()
    require(len(head) == 40 and all(ch in SHA40 for ch in head), "repository HEAD is not a SHA-1 commit id")
    return head


def validate_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    attempt = load_json(ATTEMPT_MANIFEST_PATH, "frozen ATTEMPT-002 manifest")
    require(attempt.get("schema_version") == "000b2-public-attempt-002-manifest-v1", "ATTEMPT-002 schema drift")
    require(attempt.get("attempt_id") == ATTEMPT_ID, "ATTEMPT-002 id drift")
    require(attempt.get("frozen") is True and attempt.get("phase") == "PRE_PRIMARY_FROZEN", "ATTEMPT-002 freeze state drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_FREEZE, "ATTEMPT-002 freeze digest drift")

    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "ATTEMPT-002 candidate set missing")
    candidate_ids = candidate_set.get("candidate_ids")
    require(candidate_ids == EXPECTED_CANDIDATE_IDS, "frozen candidate set drift")
    require(candidate_ids[2] == CANDIDATE_ID, "candidate cell 3 drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership became mutable")
    require(candidate_set.get("frozen_methodology_sha256") == EXPECTED_FROZEN_METHODOLOGY, "frozen methodology binding drift")
    require(candidate_set.get("registry_sha256") == EXPECTED_REGISTRY, "candidate registry binding drift")
    require(sha256_file(FROZEN_METHODOLOGY_PATH) == EXPECTED_FROZEN_METHODOLOGY, "frozen methodology bytes drift")
    require(sha256_file(CANDIDATE_REGISTRY_PATH) == EXPECTED_REGISTRY, "candidate registry bytes drift")

    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "ATTEMPT-002 decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context is not OFF")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context is not OFF")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific audio transform is not OFF")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio invariant drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation invariant drift")

    readiness = load_json(READINESS_PATH, "recovery readiness")
    require(readiness.get("state") == "RECOVERY_READY", "recovery lane is not ready")
    require(readiness.get("active_recovery_unit") == TASK, "B2R07 is not the active recovery unit")
    require(readiness.get("completed_recovery_tasks") == ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05", "B2R06"], "B2R07 predecessor ledger drift")
    require(readiness.get("qualified_workflow_change_paths") == [], "B2R07 unexpectedly authorizes workflow drift")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Qualify B2R07 only:"), "B2R07 is not the sole canonical next action")
    require("whispercpp-compact" in next_action, "B2R07 candidate identity missing from canonical next action")
    require("Keep B2R08" in next_action, "B2R08 successor boundary missing from canonical next action")
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
    require("- [x] `B2R06`" in tasks and "- [ ] `B2R07`" in tasks and "- [ ] `B2R08`" in tasks, "B2R06/B2R07/B2R08 task boundary drift")
    require("active recovery unit `B2R07`" in current, "CURRENT does not own B2R07 frontier")
    require("**Active recovery unit:** `B2R07`" in canonical_current, "canonical CURRENT_STATE does not own B2R07 frontier")

    preprocessing = load_json(PREPROCESSING_CAPTURE_PATH, "B2P06 preprocessing capture")
    require(sha256_file(PREPROCESSING_CAPTURE_PATH) == EXPECTED_PREPROCESSING, "preprocessing capture bytes drift")
    execution = preprocessing.get("execution")
    require(isinstance(execution, dict), "preprocessing execution block missing")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == EXPECTED_UTTERANCES, "preprocessing record count drift")
    require(execution.get("all_source_hashes_reverified") is True, "source hashes were not reverified in B2P06")
    require(execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "frozen preprocessing format invariant missing")

    rebinding = load_json(REBINDING_PATH, "B2R03 preexecution rebinding")
    require(sha256_file(REBINDING_PATH) == EXPECTED_REBINDING, "B2R03 rebinding bytes drift")
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

def build_preprocessing_index(preprocessing: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = preprocessing["execution"]["records"]
    indexed: dict[str, dict[str, Any]] = {}
    for row in records:
        require(isinstance(row, dict), "preprocessing record must be an object")
        uid = row.get("utterance_id")
        require(isinstance(uid, str) and uid, "preprocessing utterance id missing")
        require(uid not in indexed, f"duplicate preprocessing utterance id: {uid}")
        indexed[uid] = row
    require(len(indexed) == EXPECTED_UTTERANCES, "preprocessing index cardinality drift")
    return indexed


def validate_build_identity(path: Path, adapter: Path) -> dict[str, Any]:
    identity = load_json(path, "whisper.cpp build identity")
    require(identity.get("schema_version") == "000b2-whisper-build-identity-v2", "build identity schema drift")
    require(identity.get("source_revision") == EXPECTED_RUNTIME_REVISION, "whisper.cpp source revision drift")
    require(identity.get("source_tree") == EXPECTED_RUNTIME_TREE, "whisper.cpp source tree drift")
    require(identity.get("build_type") == "Release", "whisper.cpp build type drift")
    require(identity.get("ggml_cuda") == "OFF" and identity.get("ggml_metal") == "OFF", "GPU build flags drift")
    require(identity.get("whisper_build_tests") == "OFF" and identity.get("whisper_build_examples") == "OFF", "bounded build flags drift")
    require(identity.get("target") == "wispral-whispercpp-c0", "adapter build target drift")
    require(identity.get("adapter_source_path") == "research/000b2-public/whispercpp-adapter/adapter.cpp", "adapter source path drift")
    require(identity.get("adapter_cmake_path") == "research/000b2-public/whispercpp-adapter/CMakeLists.txt", "adapter CMake path drift")
    require(identity.get("adapter_source_sha256") == sha256_file(ADAPTER_SOURCE_PATH), "adapter source bytes drift")
    require(identity.get("adapter_cmake_sha256") == sha256_file(ADAPTER_CMAKE_PATH), "adapter CMake bytes drift")
    require(identity.get("adapter_binary_sha256") == sha256_file(adapter), "adapter binary digest drift")
    for key in ("cmake_cache_sha256", "compiler_version_sha256", "cmake_version_sha256"):
        value = identity.get(key)
        require(isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value), f"malformed build identity digest: {key}")
    return identity


def runtime_provenance() -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    require(run_id.isdigit() and int(run_id) > 0, "GITHUB_RUN_ID missing or invalid")
    require(run_attempt.isdigit() and int(run_attempt) > 0, "GITHUB_RUN_ATTEMPT missing or invalid")
    return {
        "repository_revision": git_head(),
        "github_repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "github_run_id": int(run_id),
        "github_run_attempt": int(run_attempt),
        "github_job": os.environ.get("GITHUB_JOB", ""),
        "runner_os": os.environ.get("RUNNER_OS", ""),
        "runner_arch": os.environ.get("RUNNER_ARCH", ""),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.system(),
        "preprocessing_container_image": os.environ.get("B2R07_CONTAINER_IMAGE", ""),
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def parse_adapter_output(path: Path, expected: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise DecodeError(f"unable to read adapter output: {error}") from error
    require(len(lines) == EXPECTED_UTTERANCES, "adapter output cardinality drift")
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise DecodeError(f"malformed adapter JSONL: {error}") from error
        require(isinstance(row, dict), "adapter row must be an object")
        uid = row.get("utterance_id")
        require(isinstance(uid, str) and uid in expected and uid not in rows, f"adapter utterance identity drift: {uid}")
        require(row.get("status") in {"DECODED", "FAILED"}, f"adapter status drift: {uid}")
        require(isinstance(row.get("raw_lines"), list) and all(isinstance(value, str) for value in row["raw_lines"]), f"adapter raw lines malformed: {uid}")
        require(isinstance(row.get("raw_transcript"), str), f"adapter raw transcript malformed: {uid}")
        require(row["raw_transcript"] == reconstruct_stream_text(row["raw_lines"]), f"adapter raw stream reconstruction drift: {uid}")
        require(isinstance(row.get("stream_iteration_count"), int) and row["stream_iteration_count"] >= 0, f"adapter iteration count malformed: {uid}")
        require(row["stream_iteration_count"] == len(row["raw_lines"]), f"adapter iteration accounting drift: {uid}")
        require(isinstance(row.get("decode_wall_seconds"), (int, float)) and row["decode_wall_seconds"] >= 0, f"adapter timing malformed: {uid}")

        speech_count = row.get("speech_sample_count")
        speech_delivered = row.get("speech_samples_delivered")
        regular_chunks = row.get("regular_speech_chunk_count")
        final_chunk = row.get("final_speech_chunk_samples")
        zero_delivered = row.get("zero_suffix_samples_delivered")
        zero_chunks = row.get("zero_suffix_chunks_delivered")
        require(speech_count == expected[uid].get("wav_frame_count"), f"adapter speech sample count drift: {uid}")
        require(isinstance(speech_delivered, int) and 0 <= speech_delivered <= speech_count, f"adapter speech delivery accounting drift: {uid}")
        require(regular_chunks == speech_count // REGULAR_CHUNK_SAMPLES, f"adapter regular speech chunk count drift: {uid}")
        require(final_chunk == speech_count % REGULAR_CHUNK_SAMPLES, f"adapter final speech chunk drift: {uid}")
        require(isinstance(zero_delivered, int) and 0 <= zero_delivered <= FINAL_ZERO_SAMPLES, f"adapter zero-suffix delivery accounting drift: {uid}")
        require(isinstance(zero_chunks, int) and 0 <= zero_chunks <= len(FINAL_ZERO_CHUNKS), f"adapter zero-suffix chunk accounting drift: {uid}")
        planned_iterations = regular_chunks + (1 if final_chunk else 0) + len(FINAL_ZERO_CHUNKS)
        require(row["stream_iteration_count"] <= planned_iterations, f"adapter stream iteration count exceeds frozen feed schedule: {uid}")

        if row["status"] == "DECODED":
            require(row.get("failure") is None, f"decoded adapter row has failure: {uid}")
            require(row["stream_iteration_count"] == planned_iterations, f"decoded adapter row did not execute full frozen feed schedule: {uid}")
            require(speech_delivered == speech_count, f"decoded adapter row did not preserve full speech feed: {uid}")
            require(zero_delivered == FINAL_ZERO_SAMPLES, f"decoded adapter row did not deliver full zero suffix: {uid}")
            require(zero_chunks == len(FINAL_ZERO_CHUNKS), f"decoded adapter row zero-suffix chunk count drift: {uid}")
        else:
            require(isinstance(row.get("failure"), dict), f"failed adapter row lacks failure evidence: {uid}")
        rows[uid] = row
    require(set(rows) == set(expected), "adapter output membership drift")
    return rows


def execute(
    work_dir: Path,
    preprocessed_root: Path,
    model_path: Path,
    adapter: Path,
    build_identity_path: Path,
) -> dict[str, Any]:
    _, attempt, preprocessing = validate_authority()
    indexed = build_preprocessing_index(preprocessing)

    family, config = operational_smoke.candidate_record(CANDIDATE_ID)
    require(family.get("family") == "whisper.cpp", "candidate cell 3 family drift")
    require(family.get("runtime", {}).get("revision") == EXPECTED_RUNTIME_REVISION, "whisper.cpp runtime revision drift")
    require(family.get("model_source", {}).get("revision") == EXPECTED_MODEL_SOURCE_REVISION, "whisper.cpp model-source revision drift")
    require(config.get("id") == CANDIDATE_ID and config.get("tier") == "COMPACT", "candidate cell 3 configuration drift")
    require(config.get("model") == EXPECTED_MODEL_NAME, "candidate cell 3 model name drift")
    require(model_path.is_file() and not model_path.is_symlink(), "whisper.cpp model file missing or unsafe")
    require(model_path.name == EXPECTED_MODEL_NAME, "whisper.cpp model filename drift")
    require(model_path.stat().st_size == EXPECTED_MODEL_BYTES, "whisper.cpp model size drift")
    require(sha256_file(model_path) == EXPECTED_MODEL_SHA256, "whisper.cpp model SHA-256 drift")
    artifacts = operational_smoke.verify_artifacts(CANDIDATE_ID, config, model_path.parent)
    require(len(artifacts) == 1 and artifacts[0].get("sha256") == EXPECTED_MODEL_SHA256, "candidate artifact verification drift")

    require(adapter.is_file() and not adapter.is_symlink(), "whisper.cpp adapter binary missing or unsafe")
    build_identity = validate_build_identity(build_identity_path, adapter)

    work_dir.mkdir(parents=True, exist_ok=True)
    input_list = work_dir / "b2r07-inputs.tsv"
    adapter_output = work_dir / "b2r07-adapter-output.jsonl"
    lines: list[str] = []
    for uid in sorted(indexed):
        source = indexed[uid]
        partition = source.get("source_partition")
        require(isinstance(partition, str) and partition in {"test-clean", "test-other"}, f"partition drift: {uid}")
        wav_path = preprocessed_root / partition / f"{uid}.wav"
        require(wav_path.is_file() and not wav_path.is_symlink(), f"preprocessed WAV missing or unsafe: {uid}")
        require("\t" not in uid and "\t" not in str(wav_path), "tab unsafe for adapter input list")
        observed_sha = sha256_file(wav_path)
        require(observed_sha == source.get("canonical_preprocessed_file_sha256"), f"preprocessed WAV SHA-256 drift: {uid}")
        require(wav_path.stat().st_size == source.get("canonical_preprocessed_bytes"), f"preprocessed WAV size drift: {uid}")
        lines.append(f"{uid}\t{wav_path}\n")
    input_list.write_text("".join(lines), encoding="utf-8")

    total_start = time.perf_counter()
    proc = subprocess.run(
        [
            str(adapter),
            "--model",
            str(model_path),
            "--input-list",
            str(input_list),
            "--output",
            str(adapter_output),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=5400,
    )
    require(proc.returncode == 0, f"whisper.cpp adapter failed with exit code {proc.returncode}: {proc.stdout[-4000:]}")
    adapter_rows = parse_adapter_output(adapter_output, indexed)

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
            "cell_index": 3,
            "candidate_id": CANDIDATE_ID,
            "family": "whisper.cpp",
            "tier": "COMPACT",
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
            "attempt_manifest_sha256": sha256_file(ATTEMPT_MANIFEST_PATH),
            "attempt_freeze_digest_sha256": attempt["freeze_digest_sha256"],
            "preprocessing_capture_path": "research/000b2-public/preprocessing-capture.json",
            "preprocessing_capture_sha256": sha256_file(PREPROCESSING_CAPTURE_PATH),
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
        "run": runtime_provenance(),
        "execution": {
            "input_count": len(records),
            "decoded_count": decoded,
            "failure_count": failed,
            "all_frozen_input_hashes_reverified": True,
            "all_speech_samples_delivered_for_decoded_records": all(
                row["status"] != "DECODED" or row["speech_samples_delivered"] == row["speech_sample_count"]
                for row in records
            ),
            "all_zero_suffix_samples_delivered_for_decoded_records": all(
                row["status"] != "DECODED" or row["zero_suffix_samples_delivered"] == FINAL_ZERO_SAMPLES
                for row in records
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
            "b2r08_authorized": False,
        },
    }
    evidence["evidence_payload_sha256"] = sha256_bytes(canonical_json_bytes(evidence))
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
        evidence = execute(
            args.work_dir,
            args.preprocessed_root,
            args.model,
            args.adapter,
            args.build_identity,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("B2R07_EXECUTION=CAPTURED")
        print(f"B2R07_SOURCE_REVISION={evidence['run']['repository_revision']}")
        print(f"B2R07_INPUTS={evidence['execution']['input_count']}")
        print(f"B2R07_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2R07_FAILURES={evidence['execution']['failure_count']}")
        print("B2R08_AUTHORIZED=NO")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        return 0
    except (DecodeError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"B2R07_EXECUTION=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
