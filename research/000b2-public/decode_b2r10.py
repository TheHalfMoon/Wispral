#!/usr/bin/env python3
"""Execute B2R10 sherpa-onnx-balanced under frozen ATTEMPT-002 C0."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
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

RECOVERY_READINESS = PUBLIC / "recovery-readiness.json"
ATTEMPT_002 = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
REBINDING = PUBLIC / "b2r03-preexecution-rebinding.json"
OPERATIONAL_SMOKE = ENTRY / "operational-smoke-evidence.json"

SCHEMA = "000b2-public-b2r10-decode-v1"
TASK = "B2R10"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-002"
CANDIDATE_ID = "sherpa-onnx-balanced"
EXPECTED_AUTHORITY_BASE = "d1447a3a3aa9cef1490747b0a8b288e16465e95b"
EXPECTED_FREEZE_DIGEST = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
EXPECTED_PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
EXPECTED_REGISTRY_SHA256 = "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f"
EXPECTED_RUNTIME_REVISION = "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e"
EXPECTED_RUNTIME_VERSION = "1.13.7"
EXPECTED_ONNX_REVISION = "6037ea07e3abfe599ad00d418968bcf9656e7472"
EXPECTED_AUX_REVISION = "672fbf1b30579d6585301139bb363f42a0ad4a24"
EXPECTED_UTTERANCES = 240
SAMPLE_RATE = 16000
REGULAR_CHUNK_SAMPLES = 8000
FINAL_ZERO_CHUNKS = [8000, 2560]
FINAL_ZERO_SAMPLES = sum(FINAL_ZERO_CHUNKS)
SHA40 = set("0123456789abcdef")


class DecodeError(ValueError):
    """Raised when B2R10 authority or execution invariants fail closed."""


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


def validate_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    readiness = load_json(RECOVERY_READINESS, "recovery readiness")
    require(readiness.get("state") == "RECOVERY_READY", "recovery lane is not ready")
    require(readiness.get("active_recovery_unit") == TASK, "B2R10 is not the active recovery unit")
    require(
        readiness.get("completed_recovery_tasks") == [f"B2R{i:02d}" for i in range(1, 10)],
        "B2R10 predecessor ledger drift",
    )
    require(readiness.get("qualified_workflow_change_paths") == [], "B2R10 unexpectedly authorizes workflow drift")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Qualify B2R10 only:"), "B2R10 next action drift")
    require("sherpa-onnx-balanced" in next_action and "Keep B2R11" in next_action, "B2R10/B2R11 authority boundary drift")

    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict), "replacement attempt authority missing")
    require(
        replacement.get("attempt_id") == ATTEMPT_ID and replacement.get("frozen") is True,
        "ATTEMPT-002 authority drift",
    )
    require(replacement.get("primary_decode_entry_open") is True, "ATTEMPT-002 primary decode entry is closed")
    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "recovery claim guards missing")
    require(
        guards
        == {
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "comparative_result_available": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
        "recovery claim guards drift",
    )

    attempt = load_json(ATTEMPT_002, "ATTEMPT-002 manifest")
    require(attempt.get("attempt_id") == ATTEMPT_ID and attempt.get("frozen") is True, "ATTEMPT-002 freeze state drift")
    require(attempt.get("phase") == "PRE_PRIMARY_FROZEN", "ATTEMPT-002 phase drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_FREEZE_DIGEST, "ATTEMPT-002 freeze digest drift")
    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "candidate set missing")
    require(
        candidate_set.get("candidate_ids")
        == [
            "moonshine-compact",
            "moonshine-balanced",
            "whispercpp-compact",
            "whispercpp-balanced",
            "sherpa-onnx-compact",
            "sherpa-onnx-balanced",
        ],
        "candidate order drift",
    )
    require(candidate_set.get("registry_sha256") == EXPECTED_REGISTRY_SHA256, "candidate registry binding drift")
    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context is not OFF")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context is not OFF")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific transform is not OFF")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio guard drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation guard drift")

    preprocessing = load_json(PREPROCESSING, "preprocessing evidence")
    require(sha256_file(PREPROCESSING) == EXPECTED_PREPROCESSING_SHA256, "preprocessing evidence bytes drift")
    execution = preprocessing.get("execution")
    require(isinstance(execution, dict), "preprocessing execution block missing")
    require(execution.get("all_source_hashes_reverified") is True, "source hashes were not reverified")
    require(execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "preprocessed format guard drift")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == EXPECTED_UTTERANCES, "preprocessing record count drift")

    rebinding = load_json(REBINDING, "B2R03 rebinding")
    require(sha256_file(REBINDING) == EXPECTED_REBINDING_SHA256, "B2R03 rebinding bytes drift")
    require(rebinding.get("attempt", {}).get("attempt_id") == ATTEMPT_ID, "B2R03 attempt binding drift")
    preserved = rebinding.get("preserved_identity_guards")
    require(isinstance(preserved, dict), "B2R03 preserved identities missing")
    require(preserved.get("candidate_registry_sha256") == EXPECTED_REGISTRY_SHA256, "B2R03 candidate identity drift")
    require(preserved.get("c0_repository_context") == "OFF", "B2R03 repository context drift")
    require(preserved.get("c0_test_specific_context") == "OFF", "B2R03 test context drift")
    require(preserved.get("candidate_specific_audio_transform") == "OFF", "B2R03 audio transform drift")
    return attempt, preprocessing, rebinding


def verify_operational_qualification() -> dict[str, Any]:
    evidence = load_json(OPERATIONAL_SMOKE, "operational smoke evidence")
    rows = evidence.get("candidate_evidence")
    require(isinstance(rows, list), "operational smoke candidate evidence missing")
    matches = [row for row in rows if isinstance(row, dict) and row.get("candidate_id") == CANDIDATE_ID]
    require(len(matches) == 1, "exact sherpa balanced smoke evidence missing")
    row = matches[0]
    require(row.get("status") == "SMOKE_PASS", "sherpa balanced operational smoke did not pass")
    require(row.get("runtime_revision") == EXPECTED_RUNTIME_REVISION, "sherpa runtime revision drift")
    require(
        row.get("runtime") == {"distribution": "sherpa-onnx", "version": EXPECTED_RUNTIME_VERSION},
        "sherpa runtime package drift",
    )
    require(row.get("primary_test_decoding_performed") is False, "operational smoke accessed primary material")
    require(row.get("accuracy_scoring_performed") is False, "operational smoke performed accuracy scoring")
    require(row.get("comparative_ranking_present") is False, "operational smoke contains ranking")
    return row


def preprocessing_index(preprocessing: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    order: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    for row in preprocessing["execution"]["records"]:
        require(isinstance(row, dict), "preprocessing record must be object")
        uid = row.get("utterance_id")
        require(isinstance(uid, str) and uid and uid not in indexed, f"preprocessing identity drift: {uid}")
        order.append(uid)
        indexed[uid] = row
    require(len(order) == EXPECTED_UTTERANCES and len(indexed) == EXPECTED_UTTERANCES, "preprocessing membership drift")
    return order, indexed


def runtime_provenance(runtime_identity: dict[str, Any], rebinding: dict[str, Any]) -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    require(run_id.isdigit() and int(run_id) > 0, "GITHUB_RUN_ID missing")
    require(run_attempt.isdigit() and int(run_attempt) > 0, "GITHUB_RUN_ATTEMPT missing")
    environment = rebinding.get("execution_environment_rebinding", {})
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
        "runtime_identity": runtime_identity,
        "b2r03_environment_id": environment.get("environment_id"),
        "b2r03_hardware_fingerprint_sha256": environment.get("hardware_fingerprint_sha256"),
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def execute(model_root: Path, preprocessed_root: Path, runtime_source: Path) -> dict[str, Any]:
    _, preprocessing, rebinding = validate_authority()
    smoke = verify_operational_qualification()
    order, indexed = preprocessing_index(preprocessing)

    family, config = operational_smoke.candidate_record(CANDIDATE_ID)
    require(family.get("family") == "sherpa-onnx", "candidate family drift")
    require(family.get("runtime", {}).get("revision") == EXPECTED_RUNTIME_REVISION, "candidate runtime revision drift")
    require(family.get("model_source", {}).get("onnx_revision") == EXPECTED_ONNX_REVISION, "model ONNX revision drift")
    require(config.get("id") == CANDIDATE_ID and config.get("tier") == "BALANCED", "candidate cell 6 identity drift")

    artifacts = operational_smoke.verify_artifacts(CANDIDATE_ID, config, model_root)
    require(artifacts == smoke.get("artifacts"), "materialized artifact identity differs from accepted smoke evidence")
    expected_names = {row["path"] for row in artifacts}
    require(
        expected_names
        == {
            "encoder-epoch-99-avg-1-chunk-16-left-128.onnx",
            "decoder-epoch-99-avg-1-chunk-16-left-128.onnx",
            "joiner-epoch-99-avg-1-chunk-16-left-128.onnx",
            "bpe.model",
            "tokens.txt",
        },
        "sherpa balanced artifact set drift",
    )

    runtime_version = importlib.metadata.version("sherpa-onnx")
    require(runtime_version == EXPECTED_RUNTIME_VERSION, "sherpa-onnx distribution version drift")
    source_revision = subprocess.run(
        ["git", "-C", str(runtime_source), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    ).stdout.strip()
    require(source_revision == EXPECTED_RUNTIME_REVISION, "pinned sherpa source revision drift")
    source_tree = subprocess.run(
        ["git", "-C", str(runtime_source), "rev-parse", "HEAD^{tree}"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    ).stdout.strip()
    subprocess.run(["git", "-C", str(runtime_source), "diff", "--quiet", "HEAD", "--"], check=True, timeout=10)

    import numpy as np
    import sherpa_onnx

    encoder = operational_smoke.find_artifact(model_root, "encoder-epoch-99-avg-1-chunk-16-left-128.onnx")
    decoder = operational_smoke.find_artifact(model_root, "decoder-epoch-99-avg-1-chunk-16-left-128.onnx")
    joiner = operational_smoke.find_artifact(model_root, "joiner-epoch-99-avg-1-chunk-16-left-128.onnx")
    tokens = operational_smoke.find_artifact(model_root, "tokens.txt")

    recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=str(tokens),
        encoder=str(encoder),
        decoder=str(decoder),
        joiner=str(joiner),
        num_threads=4,
        provider="cpu",
        sample_rate=SAMPLE_RATE,
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
    for uid in order:
        source = indexed[uid]
        partition = source.get("source_partition")
        require(partition in {"test-clean", "test-other"}, f"partition drift: {uid}")
        wav_path = preprocessed_root / str(partition) / f"{uid}.wav"
        require(wav_path.is_file() and not wav_path.is_symlink(), f"preprocessed WAV missing or unsafe: {uid}")
        observed_sha = sha256_file(wav_path)
        require(observed_sha == source.get("canonical_preprocessed_file_sha256"), f"preprocessed WAV SHA-256 drift: {uid}")
        require(wav_path.stat().st_size == source.get("canonical_preprocessed_bytes"), f"preprocessed WAV size drift: {uid}")
        audio = np.asarray(operational_smoke.read_wav_float(wav_path), dtype=np.float32)
        started = time.perf_counter()
        try:
            stream = recognizer.create_stream()
            snapshots: list[str] = []
            speech_chunks: list[int] = []
            decode_steps = 0
            for offset in range(0, len(audio), REGULAR_CHUNK_SAMPLES):
                chunk = audio[offset : offset + REGULAR_CHUNK_SAMPLES]
                stream.accept_waveform(SAMPLE_RATE, chunk)
                speech_chunks.append(int(len(chunk)))
                while recognizer.is_ready(stream):
                    recognizer.decode_stream(stream)
                    decode_steps += 1
                    require(decode_steps <= 10000, f"decode-step safety bound exceeded: {uid}")
                text = str(getattr(recognizer.get_result(stream), "text", "") or "")
                if not snapshots or snapshots[-1] != text:
                    snapshots.append(text)
            for zero_count in FINAL_ZERO_CHUNKS:
                stream.accept_waveform(SAMPLE_RATE, np.zeros(zero_count, dtype=np.float32))
                while recognizer.is_ready(stream):
                    recognizer.decode_stream(stream)
                    decode_steps += 1
                    require(decode_steps <= 10000, f"decode-step safety bound exceeded: {uid}")
                text = str(getattr(recognizer.get_result(stream), "text", "") or "")
                if not snapshots or snapshots[-1] != text:
                    snapshots.append(text)
            stream.input_finished()
            while recognizer.is_ready(stream):
                recognizer.decode_stream(stream)
                decode_steps += 1
                require(decode_steps <= 10000, f"decode-step safety bound exceeded: {uid}")
            raw_transcript = str(getattr(recognizer.get_result(stream), "text", "") or "")
            if not snapshots or snapshots[-1] != raw_transcript:
                snapshots.append(raw_transcript)
            record = {
                "utterance_id": uid,
                "source_partition": partition,
                "canonical_preprocessed_file_sha256": observed_sha,
                "status": "DECODED",
                "raw_stream_snapshots": snapshots,
                "raw_transcript": raw_transcript,
                "failure": None,
                "feed_trace": {
                    "sample_rate_hz": SAMPLE_RATE,
                    "speech_chunk_samples": speech_chunks,
                    "speech_samples": int(len(audio)),
                    "zero_suffix_chunk_samples": FINAL_ZERO_CHUNKS,
                    "zero_suffix_samples": FINAL_ZERO_SAMPLES,
                    "decode_steps": decode_steps,
                    "input_finished": True,
                },
            }
        except Exception as error:
            record = {
                "utterance_id": uid,
                "source_partition": partition,
                "canonical_preprocessed_file_sha256": observed_sha,
                "status": "FAILED",
                "raw_stream_snapshots": [],
                "raw_transcript": "",
                "failure": {"type": type(error).__name__, "message": str(error)[:2000]},
                "feed_trace": None,
            }
        record["decode_wall_seconds"] = time.perf_counter() - started
        records.append(record)

    decoded = sum(row["status"] == "DECODED" for row in records)
    failed = len(records) - decoded
    runtime_identity = {
        "distribution": "sherpa-onnx",
        "version": runtime_version,
        "source_revision": source_revision,
        "source_tree": source_tree,
        "module_file": str(Path(sherpa_onnx.__file__).name),
        "module_file_sha256": sha256_file(Path(sherpa_onnx.__file__)),
    }
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA,
        "task": TASK,
        "attempt_id": ATTEMPT_ID,
        "state": "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED",
        "candidate": {
            "cell_index": 6,
            "candidate_id": CANDIDATE_ID,
            "family": "sherpa-onnx",
            "tier": "BALANCED",
            "model": "FP32 ONNX",
            "runtime_revision": EXPECTED_RUNTIME_REVISION,
            "runtime_distribution": "sherpa-onnx",
            "runtime_distribution_version": EXPECTED_RUNTIME_VERSION,
            "model_onnx_revision": EXPECTED_ONNX_REVISION,
            "model_aux_revision": EXPECTED_AUX_REVISION,
            "artifacts": artifacts,
        },
        "authority": {
            "canonical_authority_base": EXPECTED_AUTHORITY_BASE,
            "attempt_manifest_path": "research/000b2-public/attempt-002-manifest.json",
            "attempt_manifest_sha256": sha256_file(ATTEMPT_002),
            "attempt_freeze_digest_sha256": EXPECTED_FREEZE_DIGEST,
            "preprocessing_capture_path": "research/000b2-public/preprocessing-capture.json",
            "preprocessing_capture_sha256": EXPECTED_PREPROCESSING_SHA256,
            "b2r03_rebinding_path": "research/000b2-public/b2r03-preexecution-rebinding.json",
            "b2r03_rebinding_sha256": EXPECTED_REBINDING_SHA256,
            "operational_smoke_path": "research/000b2-entry/operational-smoke-evidence.json",
            "operational_smoke_candidate_payload_sha256": smoke.get("evidence_payload_sha256"),
        },
        "c0_controls": {
            "language": "en",
            "threads": 4,
            "provider": "cpu",
            "sample_rate_hz": SAMPLE_RATE,
            "feature_dim": 80,
            "decoding_method": "greedy_search",
            "max_active_paths": 4,
            "feed_chunk_ms": 500,
            "feed_chunk_samples": REGULAR_CHUNK_SAMPLES,
            "final_zero_pad_samples": FINAL_ZERO_SAMPLES,
            "final_zero_chunk_samples": FINAL_ZERO_CHUNKS,
            "hotwords": [],
            "language_model": None,
            "repository_context_used": False,
            "test_specific_context_used": False,
            "candidate_specific_audio_transform_used": False,
            "identical_frozen_audio_required_across_candidates": True,
        },
        "run": runtime_provenance(runtime_identity, rebinding),
        "execution": {
            "input_count": len(records),
            "decoded_count": decoded,
            "failure_count": failed,
            "records": records,
            "all_frozen_input_hashes_reverified": True,
            "reference_transcripts_loaded_by_decoder": False,
            "accuracy_scoring_performed": False,
            "comparative_ranking_present": False,
            "performance_claim_present": False,
        },
        "claim_guards": {
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "comparative_result_available": False,
            "comparative_performance_authorized": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
            "b2r11_authorized": False,
            "b2r12_authorized": False,
        },
    }
    evidence["evidence_payload_sha256"] = hashlib.sha256(canonical_json_bytes(evidence)).hexdigest()
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--preprocessed-root", type=Path, required=True)
    parser.add_argument("--runtime-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = execute(args.model_root.resolve(), args.preprocessed_root.resolve(), args.runtime_source.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("B2R10_EVIDENCE=PASS")
    print(f"B2R10_INPUTS={evidence['execution']['input_count']}")
    print(f"B2R10_DECODED={evidence['execution']['decoded_count']}")
    print(f"B2R10_FAILURES={evidence['execution']['failure_count']}")
    print("B2R11_AUTHORIZED=NO")
    print("B2R12_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
