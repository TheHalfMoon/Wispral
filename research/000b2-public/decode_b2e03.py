#!/usr/bin/env python3
"""Execute bounded B2E03 C0 decoding for the frozen whispercpp-compact cell."""

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

READINESS_PATH = PUBLIC / "readiness.json"
ATTEMPT_MANIFEST_PATH = PUBLIC / "attempt-manifest.json"
PREPROCESSING_CAPTURE_PATH = PUBLIC / "preprocessing-capture.json"
CURRENT_PATH = ROOT / "specs" / "CURRENT.md"
TASKS_PATH = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
ADAPTER_SOURCE_PATH = PUBLIC / "whispercpp-adapter" / "adapter.cpp"
ADAPTER_CMAKE_PATH = PUBLIC / "whispercpp-adapter" / "CMakeLists.txt"

SCHEMA = "000b2-public-b2e03-decode-v1"
TASK = "B2E03"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-001"
CANDIDATE_ID = "whispercpp-compact"
EXPECTED_AUTHORITY_BASE = "b326397cdd29fbb132b9c438ba2178626558efab"
EXPECTED_RUNTIME_REVISION = "371b5a7561823ab2bb32142d2751e35e7534727b"
EXPECTED_RUNTIME_TREE = "3d7ce4f956997cfa325c7556533aba5604278463"
EXPECTED_MODEL_SOURCE_REVISION = "80da2d8bfee42b0e836fc3a9890373e5defc00a6"
EXPECTED_MODEL_NAME = "ggml-base.en.bin"
EXPECTED_MODEL_BYTES = 147964211
EXPECTED_MODEL_SHA256 = "a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002"
EXPECTED_FREEZE = "af4d5009e293daef5d8f629ca91af653f5f591448cd94d4555473a51e2d1da86"
EXPECTED_PREPROCESSING = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_UTTERANCES = 240
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
    """Raised when B2E03 authority or execution invariants fail closed."""


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
    attempt = load_json(ATTEMPT_MANIFEST_PATH, "frozen attempt manifest")
    require(attempt.get("schema_version") == "000b2-public-attempt-manifest-v1", "attempt manifest schema drift")
    require(attempt.get("attempt_id") == ATTEMPT_ID, "attempt id drift")
    require(attempt.get("frozen") is True, "attempt manifest is not frozen")
    require(attempt.get("phase") == "PRE_PRIMARY_FROZEN", "attempt phase drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_FREEZE, "attempt freeze digest drift")

    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "attempt candidate set missing")
    candidate_ids = candidate_set.get("candidate_ids")
    require(candidate_ids == EXPECTED_CANDIDATE_IDS, "frozen candidate set drift")
    require(candidate_ids[2] == CANDIDATE_ID, "candidate cell 3 drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership became mutable")

    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "attempt decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context is not OFF")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context is not OFF")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific audio transform is not OFF")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio invariant drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation invariant drift")
    require(contract.get("candidate_decoding_started") is False, "historical predecode manifest was rewritten")
    require(contract.get("primary_decoding_started") is False, "historical predecode manifest was rewritten")

    readiness = load_json(READINESS_PATH, "public readiness")
    require(readiness.get("state") == "READY", "public B2 lane is not READY")
    require(readiness.get("completed_through") == "B2E02", "B2E03 authority requires canonical completion through B2E02")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Execute B2E03 only:"), "B2E03 is not the sole canonical next action")
    require("whispercpp-compact" in next_action, "B2E03 candidate identity missing from canonical next action")
    require("Do not begin B2E04" in next_action, "B2E04 successor boundary missing from canonical next action")

    tasks = TASKS_PATH.read_text(encoding="utf-8")
    current = CURRENT_PATH.read_text(encoding="utf-8")
    require("current bounded execution unit `B2E03`" in current, "CURRENT does not own B2E03 frontier")
    require("B2E03 (`whispercpp-compact`) is the sole current bounded execution unit" in current, "CURRENT B2E03 sole-unit authority missing")
    require("- [x] `B2E01` Decode the frozen P0 public-human subset with candidate cell 1 under C0." in tasks, "B2E01 predecessor task drift")
    require("- [x] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0." in tasks, "B2E02 predecessor task drift")
    require("- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0." in tasks, "B2E03 task state drift")
    require("- [ ] `B2E04` Decode the identical frozen P0 subset with candidate cell 4 under C0." in tasks, "B2E04 successor task drift")

    preprocessing = load_json(PREPROCESSING_CAPTURE_PATH, "B2P06 preprocessing capture")
    require(sha256_file(PREPROCESSING_CAPTURE_PATH) == EXPECTED_PREPROCESSING, "preprocessing capture bytes drift")
    require(preprocessing.get("schema_version") == "000b2-public-preprocessing-capture-v1", "preprocessing capture schema drift")
    execution = preprocessing.get("execution")
    require(isinstance(execution, dict), "preprocessing execution block missing")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == EXPECTED_UTTERANCES, "preprocessing record count drift")
    require(execution.get("all_source_hashes_reverified") is True, "source hashes were not reverified in B2P06")
    require(execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "frozen preprocessing format invariant missing")
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
        "preprocessing_container_image": os.environ.get("B2E03_CONTAINER_IMAGE", ""),
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def parse_adapter_output(path: Path, expected_ids: set[str]) -> dict[str, dict[str, Any]]:
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
        require(isinstance(uid, str) and uid in expected_ids and uid not in rows, f"adapter utterance identity drift: {uid}")
        require(row.get("status") in {"DECODED", "FAILED"}, f"adapter status drift: {uid}")
        require(isinstance(row.get("raw_lines"), list) and all(isinstance(value, str) for value in row["raw_lines"]), f"adapter raw lines malformed: {uid}")
        require(isinstance(row.get("raw_transcript"), str), f"adapter raw transcript malformed: {uid}")
        require(isinstance(row.get("stream_iteration_count"), int) and row["stream_iteration_count"] >= 0, f"adapter iteration count malformed: {uid}")
        require(row["stream_iteration_count"] == len(row["raw_lines"]), f"adapter iteration accounting drift: {uid}")
        require(isinstance(row.get("decode_wall_seconds"), (int, float)) and row["decode_wall_seconds"] >= 0, f"adapter timing malformed: {uid}")
        if row["status"] == "DECODED":
            require(row.get("failure") is None, f"decoded adapter row has failure: {uid}")
            require(row["stream_iteration_count"] > 0, f"decoded adapter row has no iterations: {uid}")
        else:
            require(isinstance(row.get("failure"), dict), f"failed adapter row lacks failure evidence: {uid}")
        rows[uid] = row
    require(set(rows) == expected_ids, "adapter output membership drift")
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
    input_list = work_dir / "b2e03-inputs.tsv"
    adapter_output = work_dir / "b2e03-adapter-output.jsonl"
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
    adapter_rows = parse_adapter_output(adapter_output, set(indexed))

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
                "decode_wall_seconds": observed["decode_wall_seconds"],
            }
        )

    decoded = sum(row["status"] == "DECODED" for row in records)
    failed = len(records) - decoded
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA,
        "task": TASK,
        "state": "C0_PRIMARY_DECODE_CAPTURED",
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
            "attempt_manifest_path": "research/000b2-public/attempt-manifest.json",
            "attempt_manifest_sha256": sha256_file(ATTEMPT_MANIFEST_PATH),
            "attempt_freeze_digest_sha256": attempt["freeze_digest_sha256"],
            "preprocessing_capture_path": "research/000b2-public/preprocessing-capture.json",
            "preprocessing_capture_sha256": sha256_file(PREPROCESSING_CAPTURE_PATH),
        },
        "c0_controls": {
            "language": "en",
            "threads": 4,
            "step_ms": 500,
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
            "finalization_zero_pad_samples": 10560,
        },
        "run": runtime_provenance(),
        "execution": {
            "input_count": len(records),
            "decoded_count": decoded,
            "failure_count": failed,
            "all_frozen_input_hashes_reverified": True,
            "reference_transcripts_loaded_by_decoder": False,
            "accuracy_scoring_performed": False,
            "comparative_ranking_present": False,
            "performance_claim_present": False,
            "total_decode_wall_seconds": round(time.perf_counter() - total_start, 9),
            "records": records,
        },
        "claim_guards": {
            "candidate_decoding_started": True,
            "primary_decoding_started": True,
            "completed_through": "B2E03_EXECUTION_ONLY",
            "b2e04_authorized": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "production_stt_selected": False,
            "product_code_authorized": False,
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
        print("B2E03_EXECUTION=CAPTURED")
        print(f"B2E03_SOURCE_REVISION={evidence['run']['repository_revision']}")
        print(f"B2E03_INPUTS={evidence['execution']['input_count']}")
        print(f"B2E03_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2E03_FAILURES={evidence['execution']['failure_count']}")
        print("B2E04_AUTHORIZED=NO")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        return 0
    except (DecodeError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"B2E03_EXECUTION=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
