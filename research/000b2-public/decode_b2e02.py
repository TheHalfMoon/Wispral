#!/usr/bin/env python3
"""Execute bounded B2E02 C0 decoding for the frozen moonshine-balanced cell."""

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

READINESS_PATH = PUBLIC / "readiness.json"
ATTEMPT_MANIFEST_PATH = PUBLIC / "attempt-manifest.json"
PREPROCESSING_CAPTURE_PATH = PUBLIC / "preprocessing-capture.json"
CURRENT_PATH = ROOT / "specs" / "CURRENT.md"
TASKS_PATH = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"

SCHEMA = "000b2-public-b2e02-decode-v1"
TASK = "B2E02"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-001"
CANDIDATE_ID = "moonshine-balanced"
EXPECTED_AUTHORITY_BASE = "116dbd1734e01ec1280d6b530f0cb1dec867feb1"
EXPECTED_RUNTIME_REVISION = "234f60faa0eb388b01cdf7e60aca232af37aefda"
EXPECTED_RUNTIME_VERSION = "0.1.5"
EXPECTED_MODEL_ASSET_ROOT = "quantized_26_08_21"
EXPECTED_UTTERANCES = 240
SHA40 = set("0123456789abcdef")


class DecodeError(ValueError):
    """Raised when B2E02 authority or execution invariants fail closed."""


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
        while chunk := handle.read(1024 * 1024):
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
    # Validate the immutable attempt identity shape before execution-frontier authority.
    # This is a side-effect-free preflight: a malformed freeze digest must fail closed
    # for the specific provenance reason even after B2E02 has become canonical, while
    # a valid manifest still cannot execute B2E02 once the frontier has advanced.
    attempt = load_json(ATTEMPT_MANIFEST_PATH, "frozen attempt manifest")
    freeze_digest = attempt.get("freeze_digest_sha256")
    require(
        isinstance(freeze_digest, str)
        and len(freeze_digest) == 64
        and all(ch in SHA40 for ch in freeze_digest),
        "attempt freeze digest missing or malformed",
    )

    readiness = load_json(READINESS_PATH, "public readiness")
    require(readiness.get("state") == "READY", "public B2 lane is not READY")
    require(readiness.get("completed_through") == "B2E01", "B2E02 authority requires canonical completion through B2E01")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Execute B2E02 only:"), "B2E02 is not the sole canonical next action")
    require("moonshine-balanced" in next_action, "B2E02 candidate identity missing from canonical next action")
    require("Do not begin B2E03" in next_action, "B2E03 successor boundary missing from canonical next action")

    current = CURRENT_PATH.read_text(encoding="utf-8")
    tasks = TASKS_PATH.read_text(encoding="utf-8")
    require("current bounded execution unit `B2E02`" in current, "CURRENT does not own B2E02 frontier")
    require("B2E02 (`moonshine-balanced`) is the sole current bounded execution unit" in current, "CURRENT B2E02 sole-unit authority missing")
    require("- [x] `B2E01` Decode the frozen P0 public-human subset with candidate cell 1 under C0." in tasks, "B2E01 predecessor task state drift")
    require("- [ ] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0." in tasks, "B2E02 task state drift")
    require("- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0." in tasks, "B2E03 task state drift")

    require(attempt.get("schema_version") == "000b2-public-attempt-manifest-v1", "attempt manifest schema drift")
    require(attempt.get("attempt_id") == ATTEMPT_ID, "attempt id drift")
    require(attempt.get("frozen") is True, "attempt manifest is not frozen")
    require(attempt.get("phase") == "PRE_PRIMARY_FROZEN", "attempt phase drift")
    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "attempt candidate set missing")
    candidate_ids = candidate_set.get("candidate_ids")
    require(
        isinstance(candidate_ids, list) and len(candidate_ids) > 1 and candidate_ids[1] == CANDIDATE_ID,
        "candidate cell 2 drift",
    )
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership became mutable")
    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "attempt decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context is not OFF")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context is not OFF")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific audio transform is not OFF")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio invariant drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation invariant drift")
    require(contract.get("candidate_decoding_started") is False, "frozen predecode manifest was rewritten after decoding")
    require(contract.get("primary_decoding_started") is False, "frozen predecode manifest was rewritten after decoding")
    preprocessing = load_json(PREPROCESSING_CAPTURE_PATH, "B2P06 preprocessing capture")
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
        "container_image": os.environ.get("B2E02_CONTAINER_IMAGE", ""),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.system(),
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def execute(work_dir: Path, preprocessed_root: Path) -> dict[str, Any]:
    _, attempt, preprocessing = validate_authority()
    indexed = build_preprocessing_index(preprocessing)

    family, config = operational_smoke.candidate_record(CANDIDATE_ID)
    require(family.get("family") == "moonshine", "candidate cell 2 family drift")
    require(family.get("runtime", {}).get("revision") == EXPECTED_RUNTIME_REVISION, "Moonshine runtime revision drift")
    require(config.get("id") == CANDIDATE_ID and config.get("tier") == "BALANCED", "candidate cell 2 configuration drift")

    version = importlib.metadata.version("moonshine-voice")
    require(version == EXPECTED_RUNTIME_VERSION, f"moonshine-voice version drift: {version}")
    from moonshine_voice import ModelArch, Transcriber
    from moonshine_voice.download import download_model_from_info, find_model_info

    arch = ModelArch.MEDIUM_STREAMING
    model_info = find_model_info("en", arch)
    model_path, observed_arch = download_model_from_info(
        model_info,
        cache_root=work_dir / "moonshine-cache",
        include_word_timestamps=False,
    )
    require(observed_arch == arch, "Moonshine architecture drift")
    require(Path(model_path).name == EXPECTED_MODEL_ASSET_ROOT, "Moonshine model asset root drift")
    artifacts = operational_smoke.verify_artifacts(CANDIDATE_ID, config, Path(model_path))

    records: list[dict[str, Any]] = []
    total_start = time.perf_counter()
    with Transcriber(model_path=model_path, model_arch=arch, update_interval=0.5) as transcriber:
        transcriber.set_keyterms([])
        transcriber.set_context(None)
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
                result = transcriber.transcribe_without_streaming(audio)
                raw_lines = [str(line.text) for line in result.lines]
                record = {
                    "utterance_id": uid,
                    "source_partition": partition,
                    "canonical_preprocessed_file_sha256": observed_sha,
                    "status": "DECODED",
                    "raw_lines": raw_lines,
                    "raw_transcript": " ".join(raw_lines).strip(),
                    "failure": None,
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
                    "failure": {
                        "type": type(error).__name__,
                        "message": str(error)[:2000],
                    },
                    "decode_wall_seconds": round(time.perf_counter() - started, 9),
                }
            records.append(record)

    decoded = sum(row["status"] == "DECODED" for row in records)
    failed = len(records) - decoded
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA,
        "task": TASK,
        "state": "C0_PRIMARY_DECODE_CAPTURED",
        "attempt_id": ATTEMPT_ID,
        "candidate": {
            "cell_index": 2,
            "candidate_id": CANDIDATE_ID,
            "family": "moonshine",
            "tier": "BALANCED",
            "runtime_revision": EXPECTED_RUNTIME_REVISION,
            "runtime_distribution": "moonshine-voice",
            "runtime_version": version,
            "model_arch": int(arch),
            "model_asset_root": Path(model_path).name,
            "artifacts": artifacts,
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
            "repository_context_used": False,
            "test_specific_context_used": False,
            "candidate_specific_audio_transform_used": False,
            "keyterms": [],
            "context": None,
            "identical_frozen_audio_required_across_candidates": True,
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
            "completed_through": "B2E02_EXECUTION_ONLY",
            "b2e03_authorized": False,
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
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        evidence = execute(args.work_dir, args.preprocessed_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("B2E02_EXECUTION=CAPTURED")
        print(f"B2E02_SOURCE_REVISION={evidence['run']['repository_revision']}")
        print(f"B2E02_INPUTS={evidence['execution']['input_count']}")
        print(f"B2E02_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2E02_FAILURES={evidence['execution']['failure_count']}")
        print("B2E03_AUTHORIZED=NO")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        return 0
    except (DecodeError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"B2E02_EXECUTION=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
