#!/usr/bin/env python3
"""Execute bounded B2E03 C0 decoding for the frozen whispercpp-compact cell."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
READINESS_PATH = PUBLIC / "readiness.json"
ATTEMPT_MANIFEST_PATH = PUBLIC / "attempt-manifest.json"
PREPROCESSING_CAPTURE_PATH = PUBLIC / "preprocessing-capture.json"
CURRENT_PATH = ROOT / "specs" / "CURRENT.md"
TASKS_PATH = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"

SCHEMA = "000b2-public-b2e03-decode-v1"
TASK = "B2E03"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-001"
CANDIDATE_ID = "whispercpp-compact"
CANDIDATE_CELL_INDEX = 3
EXPECTED_AUTHORITY_BASE = "b326397cdd29fbb132b9c438ba2178626558efab"
EXPECTED_ATTEMPT_FREEZE = "af4d5009e293daef5d8f629ca91af653f5f591448cd94d4555473a51e2d1da86"
EXPECTED_PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_RUNTIME_REPOSITORY = "ggml-org/whisper.cpp"
EXPECTED_RUNTIME_REVISION = "371b5a7561823ab2bb32142d2751e35e7534727b"
EXPECTED_MODEL_SOURCE_REPOSITORY = "ggerganov/whisper.cpp"
EXPECTED_MODEL_SOURCE_REVISION = "80da2d8bfee42b0e836fc3a9890373e5defc00a6"
EXPECTED_MODEL_NAME = "ggml-base.en.bin"
EXPECTED_MODEL_BYTES = 147964211
EXPECTED_MODEL_SHA256 = "a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002"
EXPECTED_UTTERANCES = 240
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class DecodeError(ValueError):
    """Raised when B2E03 authority, identity, or execution invariants fail closed."""


def require(condition: bool, message: str) -> None:
    """Fail closed with a stable B2E03-specific error."""
    if not condition:
        raise DecodeError(message)


def load_json(path: Path, label: str) -> dict[str, Any]:
    """Load one required JSON object."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DecodeError(f"unable to load {label}: {path}: {error}") from error
    require(isinstance(value, dict), f"{label} root must be an object")
    return value


def sha256_file(path: Path) -> str:
    """Return the SHA-256 of a file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize canonical JSON bytes used by execution-evidence payload digests."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def git_head() -> str:
    """Resolve the repository revision from the repository root, never caller cwd."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    ).stdout.strip()
    require(SHA40.fullmatch(head) is not None, "repository HEAD is not a SHA-1 commit id")
    return head


def git_revision(repo: Path) -> str:
    """Resolve and validate an external git source revision."""
    revision = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    ).stdout.strip()
    require(SHA40.fullmatch(revision) is not None, "whisper.cpp source HEAD is not a SHA-1 commit id")
    return revision


def validate_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate exact B2E03-only authority and every frozen predecode boundary."""
    attempt = load_json(ATTEMPT_MANIFEST_PATH, "frozen attempt manifest")
    freeze_digest = attempt.get("freeze_digest_sha256")
    require(
        isinstance(freeze_digest, str) and SHA64.fullmatch(freeze_digest) is not None,
        "attempt freeze digest missing or malformed",
    )
    require(freeze_digest == EXPECTED_ATTEMPT_FREEZE, "attempt freeze digest drift")

    candidate_set_preflight = attempt.get("candidate_set")
    require(isinstance(candidate_set_preflight, dict), "attempt candidate set missing")
    candidate_ids_preflight = candidate_set_preflight.get("candidate_ids")
    require(
        isinstance(candidate_ids_preflight, list)
        and len(candidate_ids_preflight) > 2
        and candidate_ids_preflight[2] == CANDIDATE_ID,
        "candidate cell 3 drift",
    )

    readiness = load_json(READINESS_PATH, "public readiness")
    require(readiness.get("state") == "READY", "public B2 lane is not READY")
    require(readiness.get("completed_through") == "B2E02", "B2E03 authority requires canonical completion through B2E02")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Execute B2E03 only:"), "B2E03 is not the sole canonical next action")
    require("whispercpp-compact" in next_action, "B2E03 candidate identity missing from canonical next action")
    require("Do not begin B2E04 or any later candidate cell until B2E03 is canonical." in next_action, "B2E04 successor boundary missing from canonical next action")

    current = CURRENT_PATH.read_text(encoding="utf-8")
    tasks = TASKS_PATH.read_text(encoding="utf-8")
    require("current bounded execution unit `B2E03`" in current, "CURRENT does not own B2E03 frontier")
    require("B2E03 (`whispercpp-compact`) is the sole current bounded execution unit" in current, "CURRENT B2E03 sole-unit authority missing")
    require("B2E04 and all later candidate cells remain unauthorized" in current, "CURRENT B2E04+ closure missing")
    require("- [x] `B2E01` Decode the frozen P0 public-human subset with candidate cell 1 under C0." in tasks, "B2E01 predecessor task state drift")
    require("- [x] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0." in tasks, "B2E02 predecessor task state drift")
    require("- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0." in tasks, "B2E03 task state drift")
    require("- [ ] `B2E04` Decode the identical frozen P0 subset with candidate cell 4 under C0." in tasks, "B2E04 task state drift")

    require(attempt.get("schema_version") == "000b2-public-attempt-manifest-v1", "attempt manifest schema drift")
    require(attempt.get("attempt_id") == ATTEMPT_ID, "attempt id drift")
    require(attempt.get("frozen") is True, "attempt manifest is not frozen")
    require(attempt.get("phase") == "PRE_PRIMARY_FROZEN", "attempt phase drift")
    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "attempt candidate set missing")
    candidate_ids = candidate_set.get("candidate_ids")
    require(isinstance(candidate_ids, list) and len(candidate_ids) == 6 and candidate_ids[2] == CANDIDATE_ID, "candidate cell 3 drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership became mutable")

    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "attempt decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context is not OFF")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context is not OFF")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific audio transform is not OFF")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio invariant drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation invariant drift")
    require(contract.get("candidate_decoding_started") is False, "historical frozen predecode manifest was rewritten")
    require(contract.get("primary_decoding_started") is False, "historical frozen predecode manifest was rewritten")

    claims = attempt.get("claims")
    require(isinstance(claims, dict), "attempt claim guards missing")
    require(claims.get("comparative_performance_authorized") is False, "comparative performance became authorized")
    require(claims.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(claims.get("production_stt_selected") is False, "production STT selected early")
    require(claims.get("product_code_authorized") is False, "product code authorized early")

    require(sha256_file(PREPROCESSING_CAPTURE_PATH) == EXPECTED_PREPROCESSING_SHA256, "preprocessing capture bytes drift")
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
    """Index the 240 frozen preprocessing records by utterance id."""
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


def verify_runtime_identity(whisper_source: Path, cli_path: Path, model_path: Path) -> dict[str, Any]:
    """Verify pinned whisper.cpp source, CLI identity, and model bytes before decoding."""
    require(whisper_source.is_dir(), "whisper.cpp source directory missing")
    require(cli_path.is_file() and not cli_path.is_symlink(), "whisper-cli missing or unsafe")
    require(os.access(cli_path, os.X_OK), "whisper-cli is not executable")
    require(model_path.is_file() and not model_path.is_symlink(), "whisper model missing or unsafe")
    require(model_path.name == EXPECTED_MODEL_NAME, "whisper model filename drift")
    require(model_path.stat().st_size == EXPECTED_MODEL_BYTES, "whisper model byte-size drift")
    require(sha256_file(model_path) == EXPECTED_MODEL_SHA256, "whisper model SHA-256 drift")

    source_revision = git_revision(whisper_source)
    require(source_revision == EXPECTED_RUNTIME_REVISION, "whisper.cpp source revision drift")
    subprocess.run(
        ["git", "-C", str(whisper_source), "diff", "--quiet", "HEAD", "--"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    version_output = subprocess.run(
        [str(cli_path), "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    ).stdout
    require("whisper.cpp version:" in version_output, "whisper-cli version output drift")
    return {
        "runtime_repository": EXPECTED_RUNTIME_REPOSITORY,
        "source_revision": source_revision,
        "cli_binary_sha256": sha256_file(cli_path),
        "version_output_sha256": sha256_bytes(version_output.encode("utf-8")),
        "model_source_repository": EXPECTED_MODEL_SOURCE_REPOSITORY,
        "model_source_revision": EXPECTED_MODEL_SOURCE_REVISION,
        "model_name": EXPECTED_MODEL_NAME,
        "model_bytes": EXPECTED_MODEL_BYTES,
        "model_sha256": EXPECTED_MODEL_SHA256,
    }


def runtime_provenance() -> dict[str, Any]:
    """Capture bounded GitHub-hosted execution provenance without making performance claims."""
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
        "execution_surface": "GITHUB_HOSTED_UBUNTU24",
        "preprocessing_container_image": os.environ.get("B2E03_PREPROCESSING_CONTAINER_IMAGE", ""),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.system(),
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def execute(
    work_dir: Path,
    preprocessed_root: Path,
    whisper_source: Path,
    cli_path: Path,
    model_path: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Decode all 240 frozen P0 WAVs in one pinned whisper-cli process."""
    _, attempt, preprocessing = validate_authority()
    indexed = build_preprocessing_index(preprocessing)
    runtime = verify_runtime_identity(whisper_source, cli_path, model_path)

    work_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir = work_dir / "transcripts"
    if transcript_dir.exists():
        shutil.rmtree(transcript_dir)
    transcript_dir.mkdir(parents=True)

    ordered: list[tuple[str, dict[str, Any], Path, Path]] = []
    command = [
        str(cli_path),
        "-m", str(model_path),
        "-t", "4",
        "-l", "en",
        "-ng",
        "-nfa",
        "-nf",
        "-nt",
        "-np",
        "-otxt",
    ]
    for uid in sorted(indexed):
        source = indexed[uid]
        partition = source.get("source_partition")
        require(isinstance(partition, str) and partition in {"test-clean", "test-other"}, f"partition drift: {uid}")
        wav_path = preprocessed_root / partition / f"{uid}.wav"
        require(wav_path.is_file() and not wav_path.is_symlink(), f"preprocessed WAV missing or unsafe: {uid}")
        observed_sha = sha256_file(wav_path)
        require(observed_sha == source.get("canonical_preprocessed_file_sha256"), f"preprocessed WAV SHA-256 drift: {uid}")
        require(wav_path.stat().st_size == source.get("canonical_preprocessed_bytes"), f"preprocessed WAV size drift: {uid}")
        output_prefix = transcript_dir / uid
        command.extend(["-f", str(wav_path), "-of", str(output_prefix)])
        ordered.append((uid, source, wav_path, output_prefix))

    started = time.perf_counter()
    batch_timed_out = False
    batch_exit_code: int | None
    batch_output = ""
    try:
        proc = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
        )
        batch_exit_code = proc.returncode
        batch_output = proc.stdout or ""
    except subprocess.TimeoutExpired as error:
        batch_timed_out = True
        batch_exit_code = None
        captured = error.stdout or b""
        if isinstance(captured, bytes):
            batch_output = captured.decode("utf-8", errors="replace")
        else:
            batch_output = str(captured)

    records: list[dict[str, Any]] = []
    for uid, source, _wav_path, output_prefix in ordered:
        output_path = Path(str(output_prefix) + ".txt")
        if output_path.is_file() and not output_path.is_symlink():
            raw_output = output_path.read_text(encoding="utf-8", errors="strict")
            raw_lines = raw_output.splitlines()
            records.append(
                {
                    "utterance_id": uid,
                    "source_partition": source["source_partition"],
                    "canonical_preprocessed_file_sha256": source["canonical_preprocessed_file_sha256"],
                    "status": "DECODED",
                    "raw_lines": raw_lines,
                    "raw_transcript": " ".join(line.strip() for line in raw_lines).strip(),
                    "failure": None,
                    "decode_wall_seconds": None,
                }
            )
        else:
            failure_type = "BATCH_TIMEOUT" if batch_timed_out else "MISSING_TRANSCRIPT_OUTPUT"
            records.append(
                {
                    "utterance_id": uid,
                    "source_partition": source["source_partition"],
                    "canonical_preprocessed_file_sha256": source["canonical_preprocessed_file_sha256"],
                    "status": "FAILED",
                    "raw_lines": [],
                    "raw_transcript": "",
                    "failure": {
                        "type": failure_type,
                        "message": (
                            "whisper-cli batch exceeded the bounded timeout"
                            if batch_timed_out
                            else f"whisper-cli produced no transcript file; batch exit code={batch_exit_code}"
                        ),
                    },
                    "decode_wall_seconds": None,
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
            "cell_index": CANDIDATE_CELL_INDEX,
            "candidate_id": CANDIDATE_ID,
            "family": "whisper.cpp",
            "tier": "COMPACT",
            **runtime,
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
            "initial_prompt_used": False,
            "prompt_carryover_used": False,
            "repository_context_used": False,
            "test_specific_context_used": False,
            "grammar_used": False,
            "candidate_specific_audio_transform_used": False,
            "identical_frozen_audio_required_across_candidates": True,
            "cli_flags": ["-t", "4", "-l", "en", "-ng", "-nfa", "-nf", "-nt", "-np", "-otxt"],
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
            "timing_granularity": "BATCH_ONLY_DIAGNOSTIC",
            "total_decode_wall_seconds": round(time.perf_counter() - started, 9),
            "batch_exit_code": batch_exit_code,
            "batch_timed_out": batch_timed_out,
            "batch_diagnostic_output_sha256": sha256_bytes(batch_output.encode("utf-8")),
            "batch_diagnostic_output_retained": False,
            "records": records,
        },
        "claim_guards": {
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "public_audiobook_speech_represents_developer_speech": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
            "comparative_performance_authorized": False,
        },
    }
    unsigned = canonical_json_bytes(evidence)
    evidence["evidence_payload_sha256"] = sha256_bytes(unsigned)
    return evidence


def write_evidence(value: dict[str, Any], output: Path) -> None:
    """Write one bounded evidence file after all authority checks have passed."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--preprocessed-root", type=Path, required=True)
    parser.add_argument("--whisper-source", type=Path, required=True)
    parser.add_argument("--cli", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=5400)
    args = parser.parse_args()
    try:
        require(args.timeout_seconds >= 60, "timeout bound must be at least 60 seconds")
        evidence = execute(
            args.work_dir,
            args.preprocessed_root,
            args.whisper_source,
            args.cli,
            args.model,
            args.timeout_seconds,
        )
        write_evidence(evidence, args.output)
        print("B2E03_EXECUTION=PASS")
        print(f"B2E03_INPUTS={evidence['execution']['input_count']}")
        print(f"B2E03_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2E03_FAILURES={evidence['execution']['failure_count']}")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        print("COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
        print("PRODUCTION_STT_SELECTED=NO")
        print("PRODUCT_CODE_AUTHORIZED=NO")
        return 0
    except (DecodeError, OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"B2E03_EXECUTION=FAIL: {error}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
