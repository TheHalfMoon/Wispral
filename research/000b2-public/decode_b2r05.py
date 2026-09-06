#!/usr/bin/env python3
"""Execute B2R05 moonshine-compact under frozen ATTEMPT-002 streaming C0."""

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
sys.path.insert(0, str(PUBLIC))

import operational_smoke  # noqa: E402
import operational_smoke_entry  # noqa: E402
import moonshine_streaming_c0 as c0  # noqa: E402

RECOVERY_READINESS = PUBLIC / "recovery-readiness.json"
ATTEMPT_002 = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
REBINDING = PUBLIC / "b2r03-preexecution-rebinding.json"
B2R02_VERIFIER = PUBLIC / "verify_b2r02_moonshine_streaming.py"
B2R04_VERIFIER = PUBLIC / "verify_b2r04_attempt_freeze.py"

SCHEMA = "000b2-public-b2r05-decode-v1"
TASK = "B2R05"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-002"
CANDIDATE_ID = "moonshine-compact"
EXPECTED_AUTHORITY_BASE = "9c777ae4f4aaf8387cf54bfa4e8afe80e053ff69"
EXPECTED_FREEZE_DIGEST = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
EXPECTED_PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
EXPECTED_SUBSET_SHA256 = "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb"
EXPECTED_REGISTRY_SHA256 = "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f"
EXPECTED_C0_SHA256 = "c0f0093cda7ca036c8a97178364b3840ce7093386a8cb711ccef5f183a4453c0"
EXPECTED_UTTERANCES = 240
SHA40 = set("0123456789abcdef")


class DecodeError(ValueError):
    """Raised when B2R05 authority or execution invariants fail closed."""


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


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def git_head() -> str:
    head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    ).stdout.strip()
    require(len(head) == 40 and all(ch in SHA40 for ch in head), "repository HEAD is not a SHA-1 commit id")
    return head


def validate_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    freeze_verifier = operational_smoke_entry.load_module("wispral_b2r05_b2r04_verifier", B2R04_VERIFIER)
    freeze_verifier.verify_manifest()
    require(freeze_verifier.verify_authority() == "CANONICAL_FROZEN", "B2R04 canonical freeze authority is not active")

    readiness = load_json(RECOVERY_READINESS, "recovery readiness")
    require(readiness.get("state") == "RECOVERY_READY", "recovery lane is not ready")
    require(readiness.get("active_recovery_unit") == TASK, "B2R05 is not the active recovery unit")
    require(readiness.get("completed_recovery_tasks") == ["B2R01", "B2R02", "B2R03", "B2R04"], "recovery predecessor prefix drift")
    require(readiness.get("qualified_workflow_change_paths") == [], "B2R05 unexpectedly authorizes workflow drift")
    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict), "replacement attempt authority missing")
    require(replacement.get("attempt_id") == ATTEMPT_ID, "replacement attempt identity drift")
    require(replacement.get("frozen") is True, "ATTEMPT-002 is not frozen")
    require(replacement.get("primary_decode_entry_open") is True, "ATTEMPT-002 primary decode entry is closed")
    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "recovery claim guards missing")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech claim guard drift")
    require(guards.get("comparative_result_available") is False, "comparative result became available before scoring")
    require(guards.get("production_stt_selected") is False, "production STT selected before scoring")
    require(guards.get("product_code_authorized") is False, "product code authorized during recovery")

    attempt = load_json(ATTEMPT_002, "ATTEMPT-002 manifest")
    require(attempt.get("attempt_id") == ATTEMPT_ID, "ATTEMPT-002 id drift")
    require(attempt.get("frozen") is True and attempt.get("phase") == "PRE_PRIMARY_FROZEN", "ATTEMPT-002 freeze state drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_FREEZE_DIGEST, "ATTEMPT-002 freeze digest drift")
    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "ATTEMPT-002 candidate set missing")
    require(candidate_set.get("candidate_ids") == [
        "moonshine-compact",
        "moonshine-balanced",
        "whispercpp-compact",
        "whispercpp-balanced",
        "sherpa-onnx-compact",
        "sherpa-onnx-balanced",
    ], "ATTEMPT-002 candidate order drift")
    require(candidate_set.get("registry_sha256") == EXPECTED_REGISTRY_SHA256, "candidate registry binding drift")
    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "ATTEMPT-002 decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context is not OFF")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context is not OFF")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific audio transform is not OFF")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio invariant drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation invariant drift")
    corrected = attempt.get("corrected_c0")
    require(isinstance(corrected, dict), "corrected C0 binding missing")
    require(corrected.get("harness_sha256") == EXPECTED_C0_SHA256, "corrected C0 harness binding drift")
    require(sha256_file(PUBLIC / "moonshine_streaming_c0.py") == EXPECTED_C0_SHA256, "corrected C0 harness bytes drift")
    require(corrected.get("runtime_revision") == c0.EXPECTED_RUNTIME_REVISION, "Moonshine runtime revision drift")
    require(corrected.get("runtime_distribution_version") == c0.EXPECTED_RUNTIME_VERSION, "Moonshine runtime version drift")
    require(corrected.get("model_asset_revision") == c0.EXPECTED_MODEL_ASSET_REVISION, "Moonshine model asset revision drift")

    preprocessing = load_json(PREPROCESSING, "preprocessing evidence")
    require(sha256_file(PREPROCESSING) == EXPECTED_PREPROCESSING_SHA256, "preprocessing evidence bytes drift")
    execution = preprocessing.get("execution")
    require(isinstance(execution, dict), "preprocessing execution block missing")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == EXPECTED_UTTERANCES, "preprocessing record count drift")
    require(execution.get("all_source_hashes_reverified") is True, "source hashes were not reverified by frozen preprocessing evidence")
    require(execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "preprocessing format invariant drift")

    rebinding = load_json(REBINDING, "B2R03 preexecution rebinding")
    require(sha256_file(REBINDING) == EXPECTED_REBINDING_SHA256, "B2R03 rebinding bytes drift")
    require(rebinding.get("task") == "B2R03", "B2R03 rebinding task drift")
    require(rebinding.get("attempt", {}).get("attempt_id") == ATTEMPT_ID, "B2R03 attempt binding drift")
    preserved = rebinding.get("preserved_identity_guards")
    require(isinstance(preserved, dict), "B2R03 preserved identities missing")
    require(preserved.get("subset_manifest_sha256") == EXPECTED_SUBSET_SHA256, "subset identity drift")
    require(preserved.get("candidate_registry_sha256") == EXPECTED_REGISTRY_SHA256, "candidate identity drift")
    require(preserved.get("c0_repository_context") == "OFF", "B2R03 repository context drift")
    require(preserved.get("c0_test_specific_context") == "OFF", "B2R03 test-specific context drift")
    require(preserved.get("candidate_specific_audio_transform") == "OFF", "B2R03 candidate-specific transform drift")
    environment = rebinding.get("execution_environment_rebinding")
    require(isinstance(environment, dict), "B2R03 environment rebinding missing")
    require(environment.get("bound_attempt_id") == ATTEMPT_ID, "B2R03 environment attempt binding drift")
    require(environment.get("performance_mode") == "DIAGNOSTIC", "B2R03 environment timing semantics drift")
    require(environment.get("comparative_performance_authorized") is False, "comparative timing unexpectedly authorized")
    return readiness, attempt, preprocessing, rebinding


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


def runtime_provenance(build_identity: dict[str, Any], rebinding: dict[str, Any]) -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    require(run_id.isdigit() and int(run_id) > 0, "GITHUB_RUN_ID missing or invalid")
    require(run_attempt.isdigit() and int(run_attempt) > 0, "GITHUB_RUN_ATTEMPT missing or invalid")
    environment = rebinding["execution_environment_rebinding"]
    return {
        "repository_revision": git_head(),
        "github_repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "github_run_id": int(run_id),
        "github_run_attempt": int(run_attempt),
        "github_job": os.environ.get("GITHUB_JOB", ""),
        "github_ref": os.environ.get("GITHUB_REF", ""),
        "runner_os": os.environ.get("RUNNER_OS", ""),
        "runner_arch": os.environ.get("RUNNER_ARCH", ""),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.system(),
        "runtime_build_identity": build_identity,
        "b2r03_environment_id": environment.get("environment_id"),
        "b2r03_hardware_fingerprint_sha256": environment.get("hardware_fingerprint_sha256"),
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def execute(work_dir: Path, preprocessed_root: Path) -> dict[str, Any]:
    _, attempt, preprocessing, rebinding = validate_authority()
    indexed = build_preprocessing_index(preprocessing)

    family, config = operational_smoke.candidate_record(CANDIDATE_ID)
    require(family.get("family") == "moonshine", "candidate cell 1 family drift")
    require(family.get("runtime", {}).get("revision") == c0.EXPECTED_RUNTIME_REVISION, "candidate runtime revision drift")
    require(config.get("id") == CANDIDATE_ID and config.get("tier") == "COMPACT", "candidate cell 1 configuration drift")

    verifier = operational_smoke_entry.load_module("wispral_b2r05_b2r02_verifier", B2R02_VERIFIER)
    verifier.verify_canonical_authority(c0)
    verifier.verify_structural_harness(c0)
    verifier.verify_qualification_evidence()
    source_root = operational_smoke_entry.verified_pinned_moonshine_source(work_dir, verifier)
    runtime_root, build_identity = operational_smoke_entry.source_bound_moonshine_runtime(work_dir, source_root, verifier)
    ModelArch, Transcriber, download_model_from_info, find_model_info = operational_smoke_entry.import_source_bound_moonshine(
        runtime_root, build_identity
    )

    arch = ModelArch.SMALL_STREAMING
    model_info = find_model_info("en", arch)
    model_path, observed_arch = download_model_from_info(
        model_info,
        cache_root=work_dir / "moonshine-cache",
        include_word_timestamps=False,
    )
    require(observed_arch == arch, "Moonshine architecture drift")
    require(Path(model_path).name == c0.EXPECTED_MODEL_ASSET_REVISION, "Moonshine model asset revision drift")
    artifacts = operational_smoke.verify_artifacts(CANDIDATE_ID, config, Path(model_path))

    records: list[dict[str, Any]] = []
    total_start = time.perf_counter()
    with c0.create_transcriber(Transcriber, model_path=model_path, model_arch=arch) as transcriber:
        for uid in sorted(indexed):
            source = indexed[uid]
            partition = source.get("source_partition")
            require(isinstance(partition, str) and partition in {"test-clean", "test-other"}, f"partition drift: {uid}")
            wav_path = preprocessed_root / partition / f"{uid}.wav"
            require(wav_path.is_file() and not wav_path.is_symlink(), f"preprocessed WAV missing or unsafe: {uid}")
            observed_sha = sha256_file(wav_path)
            require(observed_sha == source.get("canonical_preprocessed_file_sha256"), f"preprocessed WAV SHA-256 drift: {uid}")
            require(wav_path.stat().st_size == source.get("canonical_preprocessed_bytes"), f"preprocessed WAV size drift: {uid}")
            audio = operational_smoke.read_wav_float(wav_path)
            started = time.perf_counter()
            try:
                result, trace = c0.transcribe_streaming_c0(transcriber, audio)
                raw_lines = [str(line.text) for line in result.lines]
                record = {
                    "utterance_id": uid,
                    "source_partition": partition,
                    "canonical_preprocessed_file_sha256": observed_sha,
                    "status": "DECODED",
                    "raw_lines": raw_lines,
                    "raw_transcript": " ".join(raw_lines).strip(),
                    "failure": None,
                    "feed_trace": {
                        "speech_samples": trace.speech_samples,
                        "speech_chunk_samples": list(trace.speech_chunk_samples),
                        "zero_pad_samples": trace.zero_pad_samples,
                        "sample_rate_hz": trace.sample_rate_hz,
                        "stream_started": trace.stream_started,
                        "stream_stopped": trace.stream_stopped,
                    },
                    "decode_wall_seconds": round(time.perf_counter() - started, 9),
                }
            except Exception as error:
                record = {
                    "utterance_id": uid,
                    "source_partition": partition,
                    "canonical_preprocessed_file_sha256": observed_sha,
                    "status": "FAILED",
                    "raw_lines": [],
                    "raw_transcript": "",
                    "failure": {"type": type(error).__name__, "message": str(error)[:2000]},
                    "feed_trace": None,
                    "decode_wall_seconds": round(time.perf_counter() - started, 9),
                }
            records.append(record)

    decoded = sum(row["status"] == "DECODED" for row in records)
    failed = len(records) - decoded
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA,
        "task": TASK,
        "state": "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED",
        "attempt_id": ATTEMPT_ID,
        "candidate": {
            "cell_index": 1,
            "candidate_id": CANDIDATE_ID,
            "family": "moonshine",
            "tier": "COMPACT",
            "runtime_revision": c0.EXPECTED_RUNTIME_REVISION,
            "runtime_distribution": c0.EXPECTED_RUNTIME_DISTRIBUTION,
            "runtime_distribution_version": c0.EXPECTED_RUNTIME_VERSION,
            "model_arch": int(arch),
            "model_asset_revision": Path(model_path).name,
            "artifacts": artifacts,
        },
        "authority": {
            "canonical_authority_base": EXPECTED_AUTHORITY_BASE,
            "attempt_manifest_path": "research/000b2-public/attempt-002-manifest.json",
            "attempt_manifest_sha256": sha256_file(ATTEMPT_002),
            "attempt_freeze_digest_sha256": attempt["freeze_digest_sha256"],
            "preprocessing_capture_path": "research/000b2-public/preprocessing-capture.json",
            "preprocessing_capture_sha256": sha256_file(PREPROCESSING),
            "b2r03_rebinding_path": "research/000b2-public/b2r03-preexecution-rebinding.json",
            "b2r03_rebinding_sha256": sha256_file(REBINDING),
            "corrected_c0_harness_path": "research/000b2-public/moonshine_streaming_c0.py",
            "corrected_c0_harness_sha256": sha256_file(PUBLIC / "moonshine_streaming_c0.py"),
        },
        "c0_controls": {
            "repository_context_used": False,
            "test_specific_context_used": False,
            "candidate_specific_audio_transform_used": False,
            "keyterms": [],
            "context": None,
            "feed_chunk_samples": c0.FEED_CHUNK_SAMPLES,
            "feed_chunk_ms": c0.FEED_CHUNK_MS,
            "final_zero_pad_samples": c0.FINAL_ZERO_PAD_SAMPLES,
            "final_zero_pad_ms": c0.FINAL_ZERO_PAD_MS,
            "transcription_interval_seconds": c0.TRANSCRIPTION_INTERVAL_SECONDS,
            "vad_threshold": c0.MOONSHINE_C0_OPTIONS["vad_threshold"],
            "identical_frozen_audio_required_across_candidates": True,
        },
        "run": runtime_provenance(build_identity, rebinding),
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
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "comparative_result_available": False,
            "comparative_performance_authorized": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
            "b2r06_authorized": False,
        },
    }
    evidence["evidence_payload_sha256"] = hashlib.sha256(canonical_json_bytes(evidence)).hexdigest()
    return evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--preprocessed-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        evidence = execute(args.work_dir.resolve(), args.preprocessed_root.resolve())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(canonical_json_bytes(evidence))
    except (DecodeError, OSError, subprocess.SubprocessError, RuntimeError, ValueError) as error:
        print(f"B2R05_EXECUTION=FAIL: {error}", file=sys.stderr)
        return 1
    print(f"B2R05_EXECUTION=PASS:{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
