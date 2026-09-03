#!/usr/bin/env python3
"""Execute the bounded B2P06 public-corpus preprocessing capture without decoding STT candidates."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any

import freeze_subset_manifest

ROOT = Path(__file__).resolve().parents[2]
SUBSET_MANIFEST_PATH = ROOT / "research/000b2-public/subset-manifest.json"
ATTEMPT_STATE_PATH = ROOT / "research/000b2-public/predecode-attempt-state.json"
PREPROCESSING_CONTRACT_PATH = ROOT / "research/000b2-entry/preprocessing/contract.json"
PREPROCESSING_CAPTURE_PATH = ROOT / "research/000b2-entry/preprocessing/capture.py"

B2P04_MANIFEST_SHA256 = "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb"
B2P04_FREEZE_DIGEST_SHA256 = "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242"
B2P05_CANONICAL_MERGE = "49538990fb4cf8223e9321261925206ed7ff5cee"
B2P05_FRONTIER_RECONCILIATION_MERGE = "e8841a68a7e37c7e4dd26ff73fe2566661c468b0"
EXPECTED_ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-001"
EXPECTED_COMMAND_TEMPLATE = (
    "ffmpeg -nostdin -hide_banner -loglevel error -i INPUT -map_metadata -1 "
    "-vn -sn -dn -ac 1 -ar 16000 -c:a pcm_s16le OUTPUT.wav"
)
EXPECTED_BEHAVIOR_CONFIG_FLAGS = (
    "--disable-everything",
    "--disable-doc",
    "--disable-debug",
    "--disable-ffplay",
    "--disable-ffprobe",
    "--disable-network",
    "--disable-autodetect",
    "--disable-x86asm",
    "--enable-protocol=file",
    "--enable-demuxer=flac,wav",
    "--enable-muxer=wav",
    "--enable-decoder=flac,pcm_s16le,pcm_s24le,pcm_s32le,pcm_f32le",
    "--enable-encoder=pcm_s16le",
    "--enable-parser=flac",
    "--enable-filter=aresample,aformat",
    "--enable-swresample",
)
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class PreprocessingError(ValueError):
    """Raised when B2P06 cannot prove one bounded preprocessing execution."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PreprocessingError(message)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreprocessingError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (OSError, json.JSONDecodeError) as error:
        raise PreprocessingError(f"unable to load {label}: {path}: {error}") from error
    require(isinstance(value, dict), f"{label} root must be an object")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def render_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_capture_module():
    spec = importlib.util.spec_from_file_location("wispral_b2_preprocessing_capture", PREPROCESSING_CAPTURE_PATH)
    if spec is None or spec.loader is None:
        raise PreprocessingError("cannot import canonical preprocessing capture tool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_attempt_state() -> tuple[dict[str, Any], bytes]:
    raw = ATTEMPT_STATE_PATH.read_bytes()
    state = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)
    require(isinstance(state, dict), "attempt state root must be an object")
    require(
        set(state)
        == {
            "schema_version",
            "attempt_id",
            "canonical_wispral_revision",
            "phase",
            "primary_test_decoding_started",
            "candidate_decoding_started",
            "b2p04_freeze_digest_sha256",
            "b2p04_manifest_sha256",
        },
        "attempt state key set drift",
    )
    require(state.get("schema_version") == "000b2-public-predecode-attempt-state-v1", "attempt state schema drift")
    require(state.get("attempt_id") == EXPECTED_ATTEMPT_ID, "attempt id drift")
    revision = state.get("canonical_wispral_revision")
    require(isinstance(revision, str) and SHA40.fullmatch(revision) is not None, "canonical revision malformed")
    require(revision == B2P05_FRONTIER_RECONCILIATION_MERGE, "attempt state must bind the canonical B2P06 authority base")
    require(state.get("phase") == "PRE_PRIMARY_CAPTURE", "attempt phase drift")
    require(state.get("primary_test_decoding_started") is False, "primary decoding already started")
    require(state.get("candidate_decoding_started") is False, "candidate decoding already started")
    require(state.get("b2p04_freeze_digest_sha256") == B2P04_FREEZE_DIGEST_SHA256, "attempt B2P04 freeze binding drift")
    require(state.get("b2p04_manifest_sha256") == B2P04_MANIFEST_SHA256, "attempt B2P04 manifest binding drift")
    return state, raw


def validate_subset_manifest() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = load_json(SUBSET_MANIFEST_PATH, "B2P04 subset manifest")
    require(sha256_file(SUBSET_MANIFEST_PATH) == B2P04_MANIFEST_SHA256, "B2P04 manifest byte identity drift")
    require(manifest.get("freeze_digest_sha256") == B2P04_FREEZE_DIGEST_SHA256, "B2P04 freeze digest field drift")
    require(freeze_subset_manifest.freeze_digest(manifest) == B2P04_FREEZE_DIGEST_SHA256, "B2P04 freeze digest reproduction drift")
    require(manifest.get("frozen") is True, "B2P04 manifest must remain frozen")
    require(manifest.get("state") == "FROZEN_SOURCE_MEMBERSHIP", "B2P04 manifest state drift")
    boundary = manifest.get("preprocessing_boundary")
    require(isinstance(boundary, dict), "B2P04 preprocessing boundary missing")
    require(boundary.get("status") == "NOT_CAPTURED_B2P06", "B2P04 historical preprocessing boundary must remain immutable")
    require(boundary.get("canonical_preprocessed_file_sha256_present") is False, "B2P04 manifest must not be rewritten with B2P06 output hashes")
    require(boundary.get("later_binding_must_reference_freeze_digest") is True, "B2P04 later-binding rule drift")
    guards = manifest.get("claim_guards")
    require(isinstance(guards, dict), "B2P04 claim guards missing")
    require(guards.get("candidate_decoding_started") is False, "B2P04 candidate decoding guard drift")
    require(guards.get("primary_decoding_started") is False, "B2P04 primary decoding guard drift")

    membership = manifest.get("membership")
    require(isinstance(membership, dict), "B2P04 membership missing")
    require(membership.get("kind") == "SOURCE_FLAC_IDENTITIES_AND_REFERENCE_TRANSCRIPTS", "B2P04 membership kind drift")
    require(membership.get("total_speakers") == 24, "B2P04 speaker count drift")
    require(membership.get("total_utterances") == 240, "B2P04 utterance count drift")
    partitions = membership.get("partitions")
    require(isinstance(partitions, list) and len(partitions) == 2, "B2P04 partition count drift")

    indexed: dict[str, dict[str, Any]] = {}
    for partition in partitions:
        require(isinstance(partition, dict), "B2P04 partition must be an object")
        speakers = partition.get("speakers")
        require(isinstance(speakers, list), "B2P04 speakers must be a list")
        for speaker in speakers:
            require(isinstance(speaker, dict), "B2P04 speaker must be an object")
            utterances = speaker.get("utterances")
            require(isinstance(utterances, list), "B2P04 utterances must be a list")
            for utterance in utterances:
                require(isinstance(utterance, dict), "B2P04 utterance must be an object")
                utterance_id = utterance.get("utterance_id")
                source_path = utterance.get("source_audio_path")
                source_sha = utterance.get("source_file_sha256")
                require(isinstance(utterance_id, str) and utterance_id, "utterance id missing")
                require(utterance_id not in indexed, f"duplicate utterance id: {utterance_id}")
                require(isinstance(source_path, str) and source_path.startswith("LibriSpeech/"), f"source path malformed: {utterance_id}")
                require(isinstance(source_sha, str) and SHA64.fullmatch(source_sha) is not None, f"source SHA-256 malformed: {utterance_id}")
                indexed[utterance_id] = utterance
    require(len(indexed) == 240, "B2P04 indexed utterance count drift")
    return manifest, indexed


def validate_contract() -> dict[str, Any]:
    contract = load_json(PREPROCESSING_CONTRACT_PATH, "canonical preprocessing contract")
    require(contract.get("schema_version") == "000b2-preprocessing-capture-v1", "preprocessing contract schema drift")
    require(contract.get("status") == "PREPARED_ATTEMPT_CAPTURE_REQUIRED", "preprocessing contract status drift")
    require(contract.get("tool") == "FFmpeg", "preprocessing tool drift")
    require(contract.get("tool_version") == "9.0.1", "preprocessing version drift")
    require(contract.get("source_tag") == "n9.0.1", "preprocessing source tag drift")
    require(contract.get("source_commit") == "bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa", "preprocessing source commit drift")
    require(contract.get("canonical_format") == "PCM_WAV", "canonical format drift")
    require(contract.get("sample_rate_hz") == 16000, "sample rate drift")
    require(contract.get("channels") == 1, "channel contract drift")
    require(contract.get("sample_format") == "PCM_S16LE", "sample format drift")
    require(contract.get("denoising") == "NONE", "denoising contract drift")
    require(contract.get("loudness_normalization") == "NONE", "normalization contract drift")
    require(contract.get("semantic_silence_trim") == "NONE", "silence-trim contract drift")
    require(contract.get("command_template") == EXPECTED_COMMAND_TEMPLATE, "FFmpeg command template drift")
    require(contract.get("resolved") is False, "historical toolchain contract must not be rewritten as attempt evidence")
    return contract


def runtime_build_configuration(ffmpeg: Path) -> dict[str, Any]:
    output = subprocess.run(
        [str(ffmpeg), "-buildconf"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    ).stdout.decode("utf-8", errors="strict")
    observed_flags = [line.strip() for line in output.splitlines() if line.strip().startswith("--")]
    behavior_flags = [flag for flag in observed_flags if not flag.startswith("--prefix=")]
    require(len(observed_flags) == len(behavior_flags) + 1, "FFmpeg build configuration must contain exactly one ignored prefix flag")
    require(behavior_flags == list(EXPECTED_BEHAVIOR_CONFIG_FLAGS), "FFmpeg behavior-affecting build configuration drift")
    return {
        "behavior_flags": list(EXPECTED_BEHAVIOR_CONFIG_FLAGS),
        "behavior_flags_sha256": sha256_bytes(canonical_json_bytes(list(EXPECTED_BEHAVIOR_CONFIG_FLAGS))),
        "prefix_ignored_as_non_behavioral": True,
    }


def preprocess_one(ffmpeg: Path, source: Path, output: Path) -> dict[str, Any]:
    require(source.is_file() and not source.is_symlink(), f"source FLAC missing or unsafe: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists(), f"preprocessing output collision: {output}")
    subprocess.run(
        [
            str(ffmpeg),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-map_metadata",
            "-1",
            "-vn",
            "-sn",
            "-dn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(output),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    require(output.is_file() and not output.is_symlink(), f"preprocessing output missing or unsafe: {output}")
    with wave.open(str(output), "rb") as wav:
        channels = wav.getnchannels()
        sample_width_bytes = wav.getsampwidth()
        sample_rate_hz = wav.getframerate()
        frame_count = wav.getnframes()
        compression_type = wav.getcomptype()
    require(channels == 1, "preprocessed WAV channel count drift")
    require(sample_width_bytes == 2, "preprocessed WAV sample width drift")
    require(sample_rate_hz == 16000, "preprocessed WAV sample rate drift")
    require(frame_count > 0, "preprocessed WAV must contain audio frames")
    require(compression_type == "NONE", "preprocessed WAV compression drift")
    return {
        "canonical_preprocessed_file_sha256": sha256_file(output),
        "canonical_preprocessed_bytes": output.stat().st_size,
        "wav_channels": channels,
        "wav_sample_width_bytes": sample_width_bytes,
        "wav_sample_rate_hz": sample_rate_hz,
        "wav_frame_count": frame_count,
        "wav_compression_type": compression_type,
    }


def execute(ffmpeg: Path, work_dir: Path) -> dict[str, Any]:
    state, state_raw = validate_attempt_state()
    _, membership = validate_subset_manifest()
    contract = validate_contract()

    capture_module = load_capture_module()
    ffmpeg_identity = capture_module.capture(
        ffmpeg,
        attempt_state_path=ATTEMPT_STATE_PATH,
        qualification_only=False,
    )
    ordering = ffmpeg_identity.get("ordering")
    require(isinstance(ordering, dict), "FFmpeg capture ordering missing")
    require(ordering.get("mode") == "ATTEMPT_STATE_BOUND", "FFmpeg identity is not attempt-state-bound")
    require(ordering.get("attempt_state_bound") is True, "FFmpeg attempt-state binding missing")
    require(ordering.get("independent_chronology_attestation") is False, "FFmpeg capture fabricated independent chronology")
    require(ordering.get("attempt_id") == EXPECTED_ATTEMPT_ID, "FFmpeg capture attempt id drift")
    require(ordering.get("canonical_wispral_revision") == B2P05_FRONTIER_RECONCILIATION_MERGE, "FFmpeg capture authority revision drift")
    require(ordering.get("attempt_state_sha256") == sha256_bytes(state_raw), "FFmpeg capture attempt-state digest drift")
    require(ordering.get("declared_primary_test_decoding_started") is False, "FFmpeg capture declares primary decode started")
    build_configuration = runtime_build_configuration(ffmpeg)

    work_dir.mkdir(parents=True, exist_ok=True)
    provenance, archive_rows = freeze_subset_manifest.validate_provenance()
    archive_observations = freeze_subset_manifest.fetch_verify_and_extract(work_dir, archive_rows)
    require(len(archive_observations) == 2, "archive observation count drift")
    extraction_root = work_dir / "extracted"
    output_root = work_dir / "preprocessed"

    records: list[dict[str, Any]] = []
    for utterance_id in sorted(membership):
        row = membership[utterance_id]
        source_path = extraction_root / str(row["source_audio_path"])
        require(sha256_file(source_path) == row["source_file_sha256"], f"source FLAC SHA-256 drift: {utterance_id}")
        output_path = output_root / str(row["source_partition"]) / f"{utterance_id}.wav"
        observed = preprocess_one(ffmpeg, source_path, output_path)
        records.append(
            {
                "utterance_id": utterance_id,
                "source_partition": row["source_partition"],
                "source_audio_path": row["source_audio_path"],
                "source_file_sha256": row["source_file_sha256"],
                **observed,
            }
        )

    require(len(records) == 240, "preprocessed record count drift")
    ffmpeg_record = {
        "tool": ffmpeg_identity["tool"],
        "tool_version": ffmpeg_identity["tool_version"],
        "source_tag": ffmpeg_identity["source_tag"],
        "source_commit": ffmpeg_identity["source_commit"],
        "binary_sha256": ffmpeg_identity["binary_sha256"],
        "version_output_sha256": ffmpeg_identity["version_output_sha256"],
        "version_first_line": ffmpeg_identity["version_first_line"],
        "contract_path": "research/000b2-entry/preprocessing/contract.json",
        "contract_sha256": ffmpeg_identity["contract_sha256"],
        "build_configuration": build_configuration,
    }
    evidence: dict[str, Any] = {
        "schema_version": "000b2-public-preprocessing-capture-v1",
        "task": "B2P06",
        "state": "ATTEMPT_BOUND_PREPROCESSING_CAPTURE",
        "attempt": {
            "attempt_id": state["attempt_id"],
            "phase": state["phase"],
            "canonical_wispral_revision": state["canonical_wispral_revision"],
            "attempt_state_path": "research/000b2-public/predecode-attempt-state.json",
            "attempt_state_sha256": sha256_bytes(state_raw),
            "candidate_decoding_started": False,
            "primary_test_decoding_started": False,
            "independent_chronology_attestation": False,
        },
        "authority": {
            "b2p04_manifest_path": "research/000b2-public/subset-manifest.json",
            "b2p04_manifest_sha256": B2P04_MANIFEST_SHA256,
            "b2p04_freeze_digest_sha256": B2P04_FREEZE_DIGEST_SHA256,
            "b2p05_candidate_revalidation_merge": B2P05_CANONICAL_MERGE,
            "b2p05_frontier_reconciliation_merge": B2P05_FRONTIER_RECONCILIATION_MERGE,
        },
        "ffmpeg": ffmpeg_record,
        "preprocessing_contract": {
            "canonical_format": contract["canonical_format"],
            "sample_rate_hz": contract["sample_rate_hz"],
            "channels": contract["channels"],
            "sample_format": contract["sample_format"],
            "denoising": contract["denoising"],
            "loudness_normalization": contract["loudness_normalization"],
            "semantic_silence_trim": contract["semantic_silence_trim"],
            "command_template": contract["command_template"],
        },
        "execution": {
            "source_membership_count": len(membership),
            "preprocessed_file_count": len(records),
            "all_source_hashes_reverified": True,
            "all_outputs_verified_pcm_s16le_mono_16000hz": True,
            "raw_preprocessed_audio_retained_in_repository": False,
            "records": records,
        },
        "claim_guards": {
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "production_stt_selected": False,
            "product_code_authorized": False,
            "b2p07_execution_environment_captured": False,
            "b2p08_attempt_manifest_frozen": False,
        },
    }
    return evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        ffmpeg = args.ffmpeg.resolve(strict=True)
        require(ffmpeg.is_file(), "FFmpeg path must be a regular file")
        evidence = execute(ffmpeg, args.work_dir)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(render_json(evidence))
        print("B2P06_PREPROCESSING_EXECUTION=PASS")
        print(f"B2P06_ATTEMPT_ID={evidence['attempt']['attempt_id']}")
        print(f"B2P06_B2P04_FREEZE_DIGEST={B2P04_FREEZE_DIGEST_SHA256}")
        print(f"B2P06_PREPROCESSED_FILES={evidence['execution']['preprocessed_file_count']}")
        print("B2P06_CANDIDATE_DECODING_STARTED=NO")
        print("B2P06_PRIMARY_DECODING_STARTED=NO")
        print("B2P07_EXECUTION_ENVIRONMENT_CAPTURED=NO")
        print("B2P08_ATTEMPT_MANIFEST_FROZEN=NO")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        print("PRODUCT_CODE_AUTHORIZED=NO")
        return 0
    except (
        OSError,
        PreprocessingError,
        freeze_subset_manifest.FreezeError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        UnicodeDecodeError,
        json.JSONDecodeError,
        wave.Error,
    ) as error:
        print(f"B2P06_PREPROCESSING_EXECUTION=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
