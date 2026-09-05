#!/usr/bin/env python3
"""Fail closed on B2P06 attempt-bound public-corpus preprocessing evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import preprocess_subset

ROOT = Path(__file__).resolve().parents[2]
READINESS_PATH = ROOT / "research/000b2-public/readiness.json"
TASKS_PATH = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
CURRENT_PATH = ROOT / "specs/CURRENT.md"
COMMITTED_EVIDENCE_PATH = ROOT / "research/000b2-public/preprocessing-capture.json"
SHA64 = re.compile(r"^[0-9a-f]{64}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"B2P06_PREPROCESSING_CAPTURE=FAIL: {message}")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"B2P06_PREPROCESSING_CAPTURE=FAIL: unable to load {label}: {error}") from error
    require(isinstance(value, dict), f"{label} root must be an object")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def validate_frontier() -> None:
    state, _ = preprocess_subset.validate_attempt_state()
    _, membership = preprocess_subset.validate_subset_manifest()
    contract = preprocess_subset.validate_contract()
    require(len(membership) == 240, "B2P04 membership count drift")
    require(state["candidate_decoding_started"] is False, "attempt state candidate decoding guard drift")
    require(state["primary_test_decoding_started"] is False, "attempt state primary decoding guard drift")
    require(contract["resolved"] is False, "historical preprocessing contract must remain unresolved")

    readiness = load_json(READINESS_PATH, "public readiness")
    require(readiness.get("state") == "READY", "public lane readiness drift")
    completed = readiness.get("completed_through")
    require(completed in {"B2P05", "B2P06", "B2P07", "B2P08", "B2E01", "B2E02"}, "B2P06 verifier is valid through the B2E02-reconciled frontier")
    public = readiness.get("public_human_baseline")
    require(isinstance(public, dict), "public_human_baseline missing")
    require(public.get("subset_manifest_frozen") is True, "B2P04 subset must remain frozen")
    require(public.get("candidate_decoding_started") is False, "candidate decoding already started")
    preprocessing = readiness.get("preprocessing")
    require(isinstance(preprocessing, dict), "preprocessing readiness missing")
    require(preprocessing.get("required_tool") == "FFmpeg 9.0.1", "preprocessing tool readiness drift")
    require(preprocessing.get("attempt_bound_capture_required") is True, "attempt-bound preprocessing requirement drift")
    environment = readiness.get("execution_environment")
    require(isinstance(environment, dict), "execution environment readiness missing")
    if completed in {"B2P07", "B2P08", "B2E01", "B2E02"}:
        require(environment.get("resolved") is True, "B2P07+ reconciliation must preserve environment resolution")
    else:
        require(environment.get("resolved") is False, "B2P07 must remain unresolved before B2P07 reconciliation")
    attempt = readiness.get("attempt_manifest")
    require(isinstance(attempt, dict), "attempt manifest readiness missing")
    require(attempt.get("frozen") is (completed in {"B2P08", "B2E01", "B2E02"}), "B2P08 freeze state must remain frozen through B2E01 reconciliation")
    require(attempt.get("primary_decoding_started") is False, "primary decoding already started")
    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "claim guards missing")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(guards.get("production_stt_selected") is False, "production STT selected early")
    require(guards.get("product_code_authorized") is False, "product code authorized early")

    tasks = TASKS_PATH.read_text(encoding="utf-8")
    current = CURRENT_PATH.read_text(encoding="utf-8")
    if completed == "B2P05":
        require(preprocessing.get("resolved") is False, "B2P06 must not be marked resolved before canonicalization")
        require("- [ ] `B2P06`" in tasks, "B2P06 task must remain open during execution candidate")
        require("- [ ] `B2P07`" in tasks, "B2P07 task must remain closed")
        require("Execute B2P06 only" in str(readiness.get("next_action")), "readiness must authorize B2P06 only")
        require("Execute and canonically qualify `B2P06` only" in current, "CURRENT must authorize B2P06 only")
    elif completed == "B2P06":
        require(preprocessing.get("resolved") is True, "canonical B2P06 reconciliation must mark preprocessing resolved")
        require("- [x] `B2P06`" in tasks, "canonical B2P06 task must be complete")
        require("- [ ] `B2P07`" in tasks, "B2P07 must remain open")
        require("B2P07" in str(readiness.get("next_action")), "canonical B2P06 reconciliation must advance to B2P07")
    else:
        require(preprocessing.get("resolved") is True, "B2P07+ reconciliation must preserve preprocessing resolution")
        require("- [x] `B2P06`" in tasks, "B2P06 must remain complete")
        require("- [x] `B2P07`" in tasks, "B2P07 must remain complete")
        if completed == "B2P07":
            require("- [ ] `B2P08`" in tasks, "B2P08 must remain open at the B2P07 frontier")
            require("Execute B2P08 only" in str(readiness.get("next_action")), "B2P07 reconciliation must advance to B2P08")
            require("Execute and canonically qualify `B2P08` only" in current, "CURRENT must authorize B2P08 only")
        elif completed == "B2P08":
            require("- [x] `B2P08`" in tasks, "B2P08 reconciliation must mark B2P08 complete")
            require("- [ ] `B2E01`" in tasks, "B2E01 must remain pending before execution")
            require("- [ ] `B2E02`" in tasks, "B2E02 must remain unauthorized")
            require("Execute B2E01 only" in str(readiness.get("next_action")), "B2P08 reconciliation must advance to B2E01")
            require("Execute and canonically qualify `B2E01` only" in current, "CURRENT must authorize B2E01 only")
        elif completed == "B2E01":
            require("- [x] `B2E01`" in tasks, "B2E01 reconciliation must mark B2E01 complete")
            require("- [ ] `B2E02`" in tasks, "B2E02 must remain pending before execution")
            require("Execute B2E02 only" in str(readiness.get("next_action")), "B2E01 reconciliation must advance to B2E02")
            require("Execute and canonically qualify `B2E02` only" in current, "CURRENT must authorize B2E02 only")
        else:
            require("- [x] `B2E02`" in tasks, "B2E02 reconciliation must mark B2E02 complete")
            require("- [ ] `B2E03`" in tasks, "B2E03 must remain pending before execution")
            require("Execute B2E03 only" in str(readiness.get("next_action")), "B2E02 reconciliation must advance to B2E03")
            require("Execute and canonically qualify `B2E03` only" in current, "CURRENT must authorize B2E03 only")


def validate_evidence(path: Path) -> dict[str, Any]:
    evidence = load_json(path, "B2P06 preprocessing evidence")
    require(
        set(evidence)
        == {
            "schema_version",
            "task",
            "state",
            "attempt",
            "authority",
            "ffmpeg",
            "preprocessing_contract",
            "execution",
            "claim_guards",
        },
        "evidence top-level key set drift",
    )
    require(evidence.get("schema_version") == "000b2-public-preprocessing-capture-v1", "evidence schema drift")
    require(evidence.get("task") == "B2P06", "evidence task drift")
    require(evidence.get("state") == "ATTEMPT_BOUND_PREPROCESSING_CAPTURE", "evidence state drift")

    state, state_raw = preprocess_subset.validate_attempt_state()
    _, membership = preprocess_subset.validate_subset_manifest()
    contract = preprocess_subset.validate_contract()

    attempt = evidence.get("attempt")
    require(isinstance(attempt, dict), "attempt evidence missing")
    require(
        set(attempt)
        == {
            "attempt_id",
            "phase",
            "canonical_wispral_revision",
            "attempt_state_path",
            "attempt_state_sha256",
            "candidate_decoding_started",
            "primary_test_decoding_started",
            "independent_chronology_attestation",
        },
        "attempt evidence key set drift",
    )
    require(attempt.get("attempt_id") == state["attempt_id"], "attempt id mismatch")
    require(attempt.get("phase") == "PRE_PRIMARY_CAPTURE", "attempt phase mismatch")
    require(attempt.get("canonical_wispral_revision") == preprocess_subset.B2P05_FRONTIER_RECONCILIATION_MERGE, "attempt authority revision mismatch")
    require(attempt.get("attempt_state_path") == "research/000b2-public/predecode-attempt-state.json", "attempt state path drift")
    require(attempt.get("attempt_state_sha256") == sha256_bytes(state_raw), "attempt state digest mismatch")
    require(attempt.get("candidate_decoding_started") is False, "evidence candidate decoding guard drift")
    require(attempt.get("primary_test_decoding_started") is False, "evidence primary decoding guard drift")
    require(attempt.get("independent_chronology_attestation") is False, "B2P06 must not fabricate independent chronology attestation")

    authority = evidence.get("authority")
    require(isinstance(authority, dict), "authority evidence missing")
    require(
        authority
        == {
            "b2p04_manifest_path": "research/000b2-public/subset-manifest.json",
            "b2p04_manifest_sha256": preprocess_subset.B2P04_MANIFEST_SHA256,
            "b2p04_freeze_digest_sha256": preprocess_subset.B2P04_FREEZE_DIGEST_SHA256,
            "b2p05_candidate_revalidation_merge": preprocess_subset.B2P05_CANONICAL_MERGE,
            "b2p05_frontier_reconciliation_merge": preprocess_subset.B2P05_FRONTIER_RECONCILIATION_MERGE,
        },
        "authority binding drift",
    )

    ffmpeg = evidence.get("ffmpeg")
    require(isinstance(ffmpeg, dict), "FFmpeg evidence missing")
    require(
        set(ffmpeg)
        == {
            "tool",
            "tool_version",
            "source_tag",
            "source_commit",
            "binary_sha256",
            "version_output_sha256",
            "version_first_line",
            "contract_path",
            "contract_sha256",
            "build_configuration",
        },
        "FFmpeg evidence key set drift",
    )
    require(ffmpeg.get("tool") == "FFmpeg", "FFmpeg tool drift")
    require(ffmpeg.get("tool_version") == "9.0.1", "FFmpeg version drift")
    require(ffmpeg.get("source_tag") == "n9.0.1", "FFmpeg source tag drift")
    require(ffmpeg.get("source_commit") == "bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa", "FFmpeg source commit drift")
    for key in ("binary_sha256", "version_output_sha256", "contract_sha256"):
        value = ffmpeg.get(key)
        require(isinstance(value, str) and SHA64.fullmatch(value) is not None, f"FFmpeg {key} malformed")
    require(ffmpeg.get("contract_path") == "research/000b2-entry/preprocessing/contract.json", "FFmpeg contract path drift")
    require(ffmpeg.get("contract_sha256") == preprocess_subset.sha256_file(preprocess_subset.PREPROCESSING_CONTRACT_PATH), "FFmpeg contract digest mismatch")
    require(isinstance(ffmpeg.get("version_first_line"), str) and str(ffmpeg["version_first_line"]).startswith("ffmpeg version n9.0.1"), "FFmpeg release-tag line drift")
    build = ffmpeg.get("build_configuration")
    require(isinstance(build, dict), "FFmpeg build configuration missing")
    require(
        set(build) == {"behavior_flags", "behavior_flags_sha256", "prefix_ignored_as_non_behavioral"},
        "FFmpeg build configuration key set drift",
    )
    require(build.get("behavior_flags") == list(preprocess_subset.EXPECTED_BEHAVIOR_CONFIG_FLAGS), "FFmpeg behavior flags drift")
    require(
        build.get("behavior_flags_sha256")
        == sha256_bytes(canonical_json_bytes(list(preprocess_subset.EXPECTED_BEHAVIOR_CONFIG_FLAGS))),
        "FFmpeg behavior flag digest drift",
    )
    require(build.get("prefix_ignored_as_non_behavioral") is True, "FFmpeg prefix boundary drift")

    pre = evidence.get("preprocessing_contract")
    require(isinstance(pre, dict), "preprocessing contract evidence missing")
    require(
        pre
        == {
            "canonical_format": contract["canonical_format"],
            "sample_rate_hz": contract["sample_rate_hz"],
            "channels": contract["channels"],
            "sample_format": contract["sample_format"],
            "denoising": contract["denoising"],
            "loudness_normalization": contract["loudness_normalization"],
            "semantic_silence_trim": contract["semantic_silence_trim"],
            "command_template": contract["command_template"],
        },
        "preprocessing contract evidence drift",
    )

    execution = evidence.get("execution")
    require(isinstance(execution, dict), "execution evidence missing")
    require(
        set(execution)
        == {
            "source_membership_count",
            "preprocessed_file_count",
            "all_source_hashes_reverified",
            "all_outputs_verified_pcm_s16le_mono_16000hz",
            "raw_preprocessed_audio_retained_in_repository",
            "records",
        },
        "execution evidence key set drift",
    )
    require(execution.get("source_membership_count") == 240, "execution source count drift")
    require(execution.get("preprocessed_file_count") == 240, "execution output count drift")
    require(execution.get("all_source_hashes_reverified") is True, "source hash reverification missing")
    require(execution.get("all_outputs_verified_pcm_s16le_mono_16000hz") is True, "WAV structural verification missing")
    require(execution.get("raw_preprocessed_audio_retained_in_repository") is False, "raw preprocessed audio retention boundary drift")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240, "preprocessing record count drift")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        require(isinstance(record, dict), "preprocessing record must be an object")
        require(
            set(record)
            == {
                "utterance_id",
                "source_partition",
                "source_audio_path",
                "source_file_sha256",
                "canonical_preprocessed_file_sha256",
                "canonical_preprocessed_bytes",
                "wav_channels",
                "wav_sample_width_bytes",
                "wav_sample_rate_hz",
                "wav_frame_count",
                "wav_compression_type",
            },
            "preprocessing record key set drift",
        )
        utterance_id = record.get("utterance_id")
        require(isinstance(utterance_id, str) and utterance_id in membership, f"unexpected utterance id: {utterance_id!r}")
        require(utterance_id not in indexed, f"duplicate preprocessing utterance id: {utterance_id}")
        source = membership[utterance_id]
        require(record.get("source_partition") == source["source_partition"], f"source partition drift: {utterance_id}")
        require(record.get("source_audio_path") == source["source_audio_path"], f"source path drift: {utterance_id}")
        require(record.get("source_file_sha256") == source["source_file_sha256"], f"source SHA-256 drift: {utterance_id}")
        output_sha = record.get("canonical_preprocessed_file_sha256")
        require(isinstance(output_sha, str) and SHA64.fullmatch(output_sha) is not None, f"output SHA-256 malformed: {utterance_id}")
        require(isinstance(record.get("canonical_preprocessed_bytes"), int) and record["canonical_preprocessed_bytes"] > 44, f"output byte count invalid: {utterance_id}")
        require(record.get("wav_channels") == 1, f"WAV channels drift: {utterance_id}")
        require(record.get("wav_sample_width_bytes") == 2, f"WAV sample width drift: {utterance_id}")
        require(record.get("wav_sample_rate_hz") == 16000, f"WAV sample rate drift: {utterance_id}")
        require(isinstance(record.get("wav_frame_count"), int) and record["wav_frame_count"] > 0, f"WAV frame count invalid: {utterance_id}")
        require(record.get("wav_compression_type") == "NONE", f"WAV compression drift: {utterance_id}")
        indexed[utterance_id] = record
    require(set(indexed) == set(membership), "preprocessing evidence does not cover exact B2P04 membership")
    require(records == sorted(records, key=lambda row: str(row["utterance_id"])), "preprocessing records must be deterministically ordered")

    guards = evidence.get("claim_guards")
    require(isinstance(guards, dict), "evidence claim guards missing")
    require(
        guards
        == {
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "production_stt_selected": False,
            "product_code_authorized": False,
            "b2p07_execution_environment_captured": False,
            "b2p08_attempt_manifest_frozen": False,
        },
        "evidence claim guards drift",
    )
    return evidence


def compare_committed(generated: Path) -> None:
    require(COMMITTED_EVIDENCE_PATH.is_file(), "committed preprocessing evidence is missing; use the uploaded probe artifact and commit it before qualification")
    generated_bytes = generated.read_bytes()
    committed_bytes = COMMITTED_EVIDENCE_PATH.read_bytes()
    if generated_bytes != committed_bytes:
        print(f"B2P06_GENERATED_SHA256={sha256_bytes(generated_bytes)}")
        print(f"B2P06_COMMITTED_SHA256={sha256_bytes(committed_bytes)}")
        raise SystemExit("B2P06_PREPROCESSING_CAPTURE=FAIL: committed preprocessing evidence is not byte-identical to exact-head regeneration")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--compare-committed", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require(sum(value is not None and value is not False for value in (args.static_only, args.evidence, args.compare_committed)) == 1, "select exactly one verification mode")
    validate_frontier()
    if args.static_only:
        print("B2P06_STATIC_FRONTIER=PASS")
        print("B2P06_B2P04_FREEZE_BINDING=PASS")
        print("B2P06_CANDIDATE_DECODING_STARTED=NO")
        print("B2P07_EXECUTION_ENVIRONMENT_CAPTURED=NO")
        print("B2P08_ATTEMPT_MANIFEST_FROZEN=NO")
        return 0
    if args.evidence is not None:
        validate_evidence(args.evidence)
        print("B2P06_GENERATED_EVIDENCE=PASS")
        print("B2P06_PREPROCESSED_FILE_COUNT=240")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        return 0
    assert args.compare_committed is not None
    validate_evidence(args.compare_committed)
    compare_committed(args.compare_committed)
    validate_evidence(COMMITTED_EVIDENCE_PATH)
    print("B2P06_COMMITTED_EVIDENCE=PASS")
    print(f"B2P06_COMMITTED_EVIDENCE_SHA256={sha256_bytes(COMMITTED_EVIDENCE_PATH.read_bytes())}")
    print("B2P06_CANDIDATE_DECODING_STARTED=NO")
    print("B2P07_EXECUTION_ENVIRONMENT_CAPTURED=NO")
    print("B2P08_ATTEMPT_MANIFEST_FROZEN=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
