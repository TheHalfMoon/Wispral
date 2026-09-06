#!/usr/bin/env python3
"""Execute ATTEMPT-002 recovery cell B2R05 (moonshine-compact) without scoring."""

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
import traceback
import wave
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
ENTRY = ROOT / "research" / "000b2-entry"
if str(ENTRY) not in sys.path:
    sys.path.insert(0, str(ENTRY))

import operational_smoke_entry as entry

TASK = "B2R05"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-002"
CANDIDATE_ID = "moonshine-compact"
EXPECTED_AUTHORITY_BASE = "9c777ae4f4aaf8387cf54bfa4e8afe80e053ff69"
EXPECTED_ATTEMPT_FREEZE = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
EXPECTED_HARNESS_SHA256 = "c0f0093cda7ca036c8a97178364b3840ce7093386a8cb711ccef5f183a4453c0"
EXPECTED_B2R03_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
EXPECTED_PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_SUBSET_SHA256 = "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb"
EXPECTED_REGISTRY_SHA256 = "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f"
EXPECTED_FROZEN_METHOD_SHA256 = "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df"
EXPECTED_CORE_SCORER_SHA256 = "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1"
EXPECTED_CORE_CONFIG_SHA256 = "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3"
EXPECTED_PUBLIC_WER_SHA256 = "581a0e4b0bb91d55a252b92871dbb1246b5fbc4466a5d94bceb35862744fc023"
EXPECTED_RUNTIME_REVISION = "234f60faa0eb388b01cdf7e60aca232af37aefda"
EXPECTED_RUNTIME_VERSION = "0.1.5"
EXPECTED_MODEL_ASSET_REVISION = "quantized_26_08_21"
EXPECTED_RECORDS = 240
EXECUTION_WORKFLOW_PATH = ".github/workflows/internal-b2r05-capture.yml"
DECODER_PATH = PUBLIC / "decode_b2r05.py"
VERIFIER_PATH = PUBLIC / "verify_b2r05.py"

ATTEMPT_MANIFEST = PUBLIC / "attempt-002-manifest.json"
RECOVERY_READINESS = PUBLIC / "recovery-readiness.json"
B2R03 = PUBLIC / "b2r03-preexecution-rebinding.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
SUBSET = PUBLIC / "subset-manifest.json"
HARNESS = PUBLIC / "moonshine_streaming_c0.py"
B2R02_VERIFIER = PUBLIC / "verify_b2r02_moonshine_streaming.py"
CURRENT = ROOT / "specs" / "CURRENT.md"
CURRENT_STATE = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"


class ExecutionError(RuntimeError):
    """Raised when frozen B2R05 execution authority or evidence drifts."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutionError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object expected: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: dict[str, Any]) -> str:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    return sha256_bytes(raw)


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def command_output(*args: str) -> str:
    return subprocess.run(
        list(args),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout.strip()


def verify_file(path: Path, expected_sha256: str, label: str) -> None:
    require(path.is_file() and not path.is_symlink(), f"{label} missing or unsafe")
    require(sha256_file(path) == expected_sha256, f"{label} digest drift")


def verify_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    head = git_output("rev-parse", "HEAD")
    require(git_output("merge-base", EXPECTED_AUTHORITY_BASE, head) == EXPECTED_AUTHORITY_BASE, "B2R05 authority base is not an ancestor")

    readiness = load(RECOVERY_READINESS)
    require(readiness.get("state") == "RECOVERY_READY", "recovery readiness state drift")
    require(readiness.get("active_recovery_unit") == TASK, "B2R05 is not the active recovery unit")
    require(
        readiness.get("completed_recovery_tasks") == ["B2R01", "B2R02", "B2R03", "B2R04"],
        "recovery completed prefix drift",
    )
    replacement = readiness.get("replacement_attempt", {})
    require(replacement.get("attempt_id") == ATTEMPT_ID, "replacement attempt id drift")
    require(replacement.get("required") is True, "ATTEMPT-002 is not required")
    require(replacement.get("frozen") is True, "ATTEMPT-002 is not frozen")
    require(replacement.get("primary_decode_entry_open") is True, "primary decode entry is not open")
    require(readiness.get("qualified_workflow_change_paths") == [], "workflow-change authority drift")
    guards = readiness.get("claim_guards", {})
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human speech claim guard drift")
    require(guards.get("comparative_result_available") is False, "comparative result guard opened early")
    require(guards.get("production_stt_selected") is False, "production selection guard opened early")
    require(guards.get("product_code_authorized") is False, "product authority guard opened early")

    current = CURRENT.read_text(encoding="utf-8")
    current_state = CURRENT_STATE.read_text(encoding="utf-8")
    tasks = TASKS.read_text(encoding="utf-8")
    for text, label in ((current, "CURRENT"), (current_state, "CURRENT_STATE")):
        require("**Active recovery unit:** `B2R05`" in text, f"{label} does not authorize B2R05")
    require("- [ ] `B2R05`" in tasks, "B2R05 task state is not pending")
    for task in ("B2R06", "B2R07", "B2R08", "B2R09", "B2R10", "B2R11", "B2R12"):
        require(f"- [ ] `{task}`" in tasks, f"{task} opened before B2R05 completion")

    manifest = load(ATTEMPT_MANIFEST)
    require(manifest.get("attempt_id") == ATTEMPT_ID, "ATTEMPT-002 manifest id drift")
    require(manifest.get("frozen") is True, "ATTEMPT-002 manifest is not frozen")
    require(manifest.get("phase") == "PRE_PRIMARY_FROZEN", "ATTEMPT-002 phase drift")
    require(manifest.get("freeze_digest_sha256") == EXPECTED_ATTEMPT_FREEZE, "ATTEMPT-002 freeze digest drift")
    candidate_set = manifest.get("candidate_set", {})
    require(candidate_set.get("candidate_ids", [None])[0] == CANDIDATE_ID, "candidate cell 1 drift")
    require(candidate_set.get("count") == 6, "candidate count drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership opened after freeze")
    require(candidate_set.get("registry_sha256") == EXPECTED_REGISTRY_SHA256, "candidate registry identity drift")
    require(candidate_set.get("frozen_methodology_sha256") == EXPECTED_FROZEN_METHOD_SHA256, "frozen methodology identity drift")

    corrected = manifest.get("corrected_c0", {})
    require(corrected.get("harness_path") == "research/000b2-public/moonshine_streaming_c0.py", "corrected harness path drift")
    require(corrected.get("harness_sha256") == EXPECTED_HARNESS_SHA256, "corrected harness digest drift")
    require(corrected.get("runtime_revision") == EXPECTED_RUNTIME_REVISION, "Moonshine revision drift")
    require(corrected.get("runtime_distribution") == "moonshine-voice", "Moonshine distribution drift")
    require(corrected.get("runtime_distribution_version") == EXPECTED_RUNTIME_VERSION, "Moonshine distribution version drift")
    require(corrected.get("model_asset_revision") == EXPECTED_MODEL_ASSET_REVISION, "Moonshine model asset revision drift")

    contract = manifest.get("decoding_contract", {})
    require(contract.get("c0_repository_context") == "OFF", "repository context opened")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context opened")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific audio transform opened")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical audio guard drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw output preservation guard drift")
    require(contract.get("candidate_run_runtime_observations_must_be_preserved_separately") is True, "runtime observation guard drift")

    scoring = manifest.get("scoring", {})
    require(scoring.get("core_scorer_sha256") == EXPECTED_CORE_SCORER_SHA256, "core scorer identity drift")
    require(scoring.get("core_config_sha256") == EXPECTED_CORE_CONFIG_SHA256, "scorer config identity drift")
    require(scoring.get("public_wer_adapter_sha256") == EXPECTED_PUBLIC_WER_SHA256, "public WER adapter identity drift")
    require(scoring.get("result_driven_changes_allowed") is False, "result-driven changes opened")

    verify_file(HARNESS, EXPECTED_HARNESS_SHA256, "corrected C0 harness")
    verify_file(B2R03, EXPECTED_B2R03_SHA256, "B2R03 preexecution rebinding")
    verify_file(PREPROCESSING, EXPECTED_PREPROCESSING_SHA256, "preprocessing capture")
    verify_file(SUBSET, EXPECTED_SUBSET_SHA256, "subset manifest")

    b2r03 = load(B2R03)
    require(b2r03.get("attempt", {}).get("attempt_id") == ATTEMPT_ID, "B2R03 attempt binding drift")
    require(b2r03.get("preprocessing_rebinding", {}).get("preprocessed_file_count") == EXPECTED_RECORDS, "B2R03 input count drift")
    require(b2r03.get("preprocessing_rebinding", {}).get("no_result_driven_input_change") is True, "B2R03 result-driven guard drift")
    require(
        b2r03.get("execution_environment_rebinding", {}).get("candidate_run_runtime_observations_must_be_preserved_separately") is True,
        "B2R03 runtime-observation preservation drift",
    )
    require(b2r03.get("execution_environment_rebinding", {}).get("comparative_performance_authorized") is False, "B2R03 comparative timing opened")
    preserved = b2r03.get("preserved_identity_guards", {})
    require(preserved.get("subset_manifest_sha256") == EXPECTED_SUBSET_SHA256, "B2R03 subset identity drift")
    require(preserved.get("candidate_registry_sha256") == EXPECTED_REGISTRY_SHA256, "B2R03 candidate registry drift")
    require(preserved.get("frozen_methodology_sha256") == EXPECTED_FROZEN_METHOD_SHA256, "B2R03 frozen methodology drift")
    require(preserved.get("c0_repository_context") == "OFF", "B2R03 repository context drift")
    require(preserved.get("c0_test_specific_context") == "OFF", "B2R03 test-specific context drift")
    require(preserved.get("candidate_specific_audio_transform") == "OFF", "B2R03 candidate-specific transform drift")

    return readiness, manifest, b2r03


def preprocessing_records() -> list[dict[str, Any]]:
    capture = load(PREPROCESSING)
    execution = capture.get("execution", {})
    require(execution.get("preprocessed_file_count") == EXPECTED_RECORDS, "preprocessing capture record count drift")
    require(execution.get("all_source_hashes_reverified") is True, "preprocessing source hashes were not reverified")
    require(execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "preprocessing audio contract drift")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == EXPECTED_RECORDS, "preprocessing records malformed")
    seen: set[str] = set()
    for record in records:
        require(isinstance(record, dict), "preprocessing record must be an object")
        utterance = record.get("utterance_id")
        require(isinstance(utterance, str) and utterance not in seen, "duplicate or malformed utterance id")
        seen.add(utterance)
        require(record.get("wav_channels") == 1, f"{utterance}: channel drift")
        require(record.get("wav_sample_rate_hz") == 16000, f"{utterance}: sample-rate drift")
        require(record.get("wav_sample_width_bytes") == 2, f"{utterance}: sample-width drift")
        require(record.get("wav_compression_type") == "NONE", f"{utterance}: compression drift")
    return records


def verify_preprocessed_wav(path: Path, record: dict[str, Any]) -> None:
    utterance = record["utterance_id"]
    require(path.is_file() and not path.is_symlink(), f"{utterance}: preprocessed WAV missing or unsafe")
    require(path.stat().st_size == record["canonical_preprocessed_bytes"], f"{utterance}: preprocessed byte count drift")
    require(sha256_file(path) == record["canonical_preprocessed_file_sha256"], f"{utterance}: preprocessed digest drift")
    with wave.open(str(path), "rb") as handle:
        require(handle.getnchannels() == 1, f"{utterance}: WAV channels drift")
        require(handle.getframerate() == 16000, f"{utterance}: WAV sample rate drift")
        require(handle.getsampwidth() == 2, f"{utterance}: WAV sample width drift")
        require(handle.getnframes() == record["wav_frame_count"], f"{utterance}: WAV frame count drift")
        require(handle.getcomptype() == "NONE", f"{utterance}: WAV compression drift")


def cpu_model() -> str | None:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        return None
    for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("model name") and ":" in line:
            return line.split(":", 1)[1].strip()
    return None


def memory_bytes() -> int | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        return None
    for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("MemTotal:"):
            fields = line.split()
            if len(fields) >= 2 and fields[1].isdigit():
                return int(fields[1]) * 1024
    return None


def runtime_observations(build_identity: dict[str, Any]) -> dict[str, Any]:
    return {
        "capture_kind": "GITHUB_HOSTED_DIAGNOSTIC",
        "performance_mode": "DIAGNOSTIC",
        "comparative_performance_authorized": False,
        "github": {
            "repository": os.environ.get("GITHUB_REPOSITORY"),
            "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "workflow_ref": os.environ.get("GITHUB_WORKFLOW_REF"),
            "event_name": os.environ.get("GITHUB_EVENT_NAME"),
            "ref": os.environ.get("GITHUB_REF"),
            "sha": os.environ.get("GITHUB_SHA"),
            "run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
            "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]) if os.environ.get("GITHUB_RUN_ATTEMPT") else None,
            "job": os.environ.get("GITHUB_JOB"),
        },
        "runner": {
            "os": os.environ.get("RUNNER_OS"),
            "arch": os.environ.get("RUNNER_ARCH"),
            "environment": os.environ.get("RUNNER_ENVIRONMENT"),
            "image_os": os.environ.get("ImageOS"),
            "image_version": os.environ.get("ImageVersion"),
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "uname": " ".join(platform.uname()),
            "cpu_model": cpu_model(),
            "logical_cpu_count": os.cpu_count(),
            "memory_bytes": memory_bytes(),
        },
        "toolchain": {
            "python": platform.python_version(),
            "git": command_output("git", "--version"),
            "cmake": command_output("cmake", "--version").splitlines()[0],
            "moonshine_distribution": importlib.metadata.version("moonshine-voice"),
        },
        "moonshine_source_build_identity": build_identity,
    }


def execute(work_dir: Path, preprocessed_root: Path) -> dict[str, Any]:
    readiness, manifest, b2r03 = verify_authority()
    records = preprocessing_records()

    family, config = entry.smoke.candidate_record(CANDIDATE_ID)
    require(family.get("family") == "moonshine", "candidate family drift")
    require(config.get("id") == CANDIDATE_ID, "candidate configuration drift")

    harness = entry.load_module("wispral_b2r05_streaming_harness", HARNESS)
    verifier = entry.load_module("wispral_b2r05_streaming_verifier", B2R02_VERIFIER)
    verifier.verify_canonical_authority(harness)
    verifier.verify_structural_harness(harness)
    verifier.verify_qualification_evidence()

    source_root = entry.verified_pinned_moonshine_source(work_dir, verifier)
    runtime_root, build_identity = entry.source_bound_moonshine_runtime(work_dir, source_root, verifier)
    require(build_identity.get("source_revision") == EXPECTED_RUNTIME_REVISION, "source-built Moonshine revision drift")
    require(build_identity.get("release") == "v0.1.5", "source-built Moonshine release drift")
    require(build_identity.get("runtime_origin") == "PINNED_SOURCE_CHECKOUT_BUILD", "Moonshine runtime origin drift")

    ModelArch, Transcriber, download_model_from_info, find_model_info = entry.import_source_bound_moonshine(
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
    require(Path(model_path).name == EXPECTED_MODEL_ASSET_REVISION, "Moonshine model asset revision drift")
    entry.smoke.verify_artifacts(CANDIDATE_ID, config, Path(model_path))

    observed: list[dict[str, Any]] = []
    total_wall_seconds = 0.0

    with harness.create_transcriber(Transcriber, model_path=model_path, model_arch=arch) as transcriber:
        for record in records:
            utterance = record["utterance_id"]
            wav_path = preprocessed_root / record["source_partition"] / f"{utterance}.wav"
            verify_preprocessed_wav(wav_path, record)
            audio = entry.smoke.read_wav_float(wav_path)

            started = time.perf_counter()
            result = None
            trace = None
            failure: dict[str, Any] | None = None
            try:
                result, trace = harness.transcribe_streaming_c0(transcriber, audio)
            except Exception as exc:
                failure = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                }
            elapsed = time.perf_counter() - started
            total_wall_seconds += elapsed

            raw_lines: list[str] = []
            if result is not None:
                raw_lines = [str(line.text) for line in result.lines]

            observed_record: dict[str, Any] = {
                "utterance_id": utterance,
                "source_partition": record["source_partition"],
                "input": {
                    "canonical_preprocessed_file_sha256": record["canonical_preprocessed_file_sha256"],
                    "canonical_preprocessed_bytes": record["canonical_preprocessed_bytes"],
                    "wav_frame_count": record["wav_frame_count"],
                    "wav_sample_rate_hz": 16000,
                },
                "status": "FAILED" if failure is not None else "DECODED",
                "raw_lines": raw_lines,
                "raw_transcript": "\n".join(raw_lines),
                "result_was_none": result is None,
                "failure": failure,
                "runtime_observation": {
                    "decode_wall_seconds": round(elapsed, 9),
                    "timing_role": "DIAGNOSTIC_ONLY_NOT_COMPARATIVE",
                },
                "streaming_trace": asdict(trace) if trace is not None else None,
            }
            observed.append(observed_record)

    workflow_path = ROOT / EXECUTION_WORKFLOW_PATH
    require(workflow_path.is_file() and not workflow_path.is_symlink(), "execution workflow missing on capture branch")

    payload: dict[str, Any] = {
        "schema_version": "000b2-public-attempt-002-cell-evidence-v1",
        "task": TASK,
        "lane": "PUBLIC_CORPUS",
        "state": "PRIMARY_CELL_EXECUTION_CAPTURED_UNSCORED",
        "attempt": {
            "attempt_id": ATTEMPT_ID,
            "manifest_path": "research/000b2-public/attempt-002-manifest.json",
            "manifest_sha256": sha256_file(ATTEMPT_MANIFEST),
            "freeze_digest_sha256": EXPECTED_ATTEMPT_FREEZE,
            "frozen": True,
        },
        "authority": {
            "canonical_base": EXPECTED_AUTHORITY_BASE,
            "recovery_readiness_path": "research/000b2-public/recovery-readiness.json",
            "recovery_readiness_sha256": sha256_file(RECOVERY_READINESS),
            "active_recovery_unit": TASK,
            "completed_recovery_tasks": readiness["completed_recovery_tasks"],
            "b2r03_rebinding_path": "research/000b2-public/b2r03-preexecution-rebinding.json",
            "b2r03_rebinding_sha256": sha256_file(B2R03),
            "preprocessing_path": "research/000b2-public/preprocessing-capture.json",
            "preprocessing_sha256": sha256_file(PREPROCESSING),
            "subset_path": "research/000b2-public/subset-manifest.json",
            "subset_sha256": sha256_file(SUBSET),
            "corrected_c0_harness_path": "research/000b2-public/moonshine_streaming_c0.py",
            "corrected_c0_harness_sha256": sha256_file(HARNESS),
            "candidate_registry_sha256": manifest["candidate_set"]["registry_sha256"],
            "frozen_methodology_sha256": manifest["candidate_set"]["frozen_methodology_sha256"],
            "core_scorer_sha256": manifest["scoring"]["core_scorer_sha256"],
            "core_config_sha256": manifest["scoring"]["core_config_sha256"],
            "public_wer_adapter_sha256": manifest["scoring"]["public_wer_adapter_sha256"],
            "decoder_path": "research/000b2-public/decode_b2r05.py",
            "decoder_sha256": sha256_file(DECODER_PATH),
            "verifier_path": "research/000b2-public/verify_b2r05.py",
            "verifier_sha256": sha256_file(VERIFIER_PATH),
        },
        "candidate": {
            "cell_index": 1,
            "candidate_id": CANDIDATE_ID,
            "family": family.get("family"),
            "tier": config.get("tier"),
            "runtime_revision": EXPECTED_RUNTIME_REVISION,
            "runtime_distribution": "moonshine-voice",
            "runtime_distribution_version": EXPECTED_RUNTIME_VERSION,
            "model_asset_revision": EXPECTED_MODEL_ASSET_REVISION,
            "streaming_contract": {
                "speech_chunk_samples": harness.SPEECH_CHUNK_SAMPLES,
                "zero_pad_samples": harness.FINAL_ZERO_PAD_SAMPLES,
                "sample_rate_hz": harness.SAMPLE_RATE_HZ,
                "transcription_interval_seconds": harness.TRANSCRIPTION_INTERVAL_SECONDS,
                "vad_threshold": harness.MOONSHINE_C0_OPTIONS["vad_threshold"],
                "repository_context": "OFF",
                "test_specific_context": "OFF",
                "keyterms": [],
            },
        },
        "execution": {
            "repository_revision": git_output("rev-parse", "HEAD"),
            "workflow_path": EXECUTION_WORKFLOW_PATH,
            "workflow_sha256": sha256_file(workflow_path),
            "input_record_count": len(records),
            "decoded_record_count": sum(item["status"] == "DECODED" for item in observed),
            "failed_record_count": sum(item["status"] == "FAILED" for item in observed),
            "records": observed,
            "runtime_observations": runtime_observations(build_identity),
            "aggregate_decode_wall_seconds": round(total_wall_seconds, 9),
            "aggregate_timing_role": "DIAGNOSTIC_ONLY_NOT_COMPARATIVE",
        },
        "preservation": {
            "raw_transcripts_preserved": True,
            "failures_preserved": True,
            "runtime_observations_preserved": True,
            "exact_run_identity_preserved": True,
            "frozen_input_identities_preserved": True,
            "references_loaded_for_scoring": False,
            "scoring_performed": False,
            "candidate_ranking_performed": False,
            "result_driven_changes_performed": False,
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
    payload["evidence_payload_sha256"] = canonical_digest(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--preprocessed-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authority-only", action="store_true")
    args = parser.parse_args()

    try:
        verify_authority()
        if args.authority_only:
            print("B2R05_AUTHORITY=PASS")
            return 0
        payload = execute(args.work_dir, args.preprocessed_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"B2R05_EXECUTION=PASS:{args.output}")
        return 0
    except (ExecutionError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"B2R05_EXECUTION=FAIL:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
