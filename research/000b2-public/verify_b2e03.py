#!/usr/bin/env python3
"""Verify bounded B2E03 whispercpp-compact C0 execution evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
DEFAULT_EVIDENCE = PUBLIC / "b2e03-whispercpp-compact.json"
ATTEMPT = PUBLIC / "attempt-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
READINESS = PUBLIC / "readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
ADAPTER_SOURCE = PUBLIC / "whispercpp-adapter" / "adapter.cpp"
ADAPTER_CMAKE = PUBLIC / "whispercpp-adapter" / "CMakeLists.txt"

EXPECTED_BASE = "b326397cdd29fbb132b9c438ba2178626558efab"
EXPECTED_ATTEMPT_FREEZE = "af4d5009e293daef5d8f629ca91af653f5f591448cd94d4555473a51e2d1da86"
EXPECTED_PREPROCESSING = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_RUNTIME_REVISION = "371b5a7561823ab2bb32142d2751e35e7534727b"
EXPECTED_RUNTIME_TREE = "3d7ce4f956997cfa325c7556533aba5604278463"
EXPECTED_MODEL_SOURCE_REVISION = "80da2d8bfee42b0e836fc3a9890373e5defc00a6"
EXPECTED_MODEL_NAME = "ggml-base.en.bin"
EXPECTED_MODEL_BYTES = 147964211
EXPECTED_MODEL_SHA256 = "a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002"
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
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class VerifyError(ValueError):
    """Raised when B2E03 evidence or authority fails closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise VerifyError(f"unable to load {path}: {error}") from error
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def validate_frontier(readiness: dict[str, Any], tasks: str, current: str, attempt: dict[str, Any]) -> None:
    require(readiness.get("state") == "READY", "public lane is not READY")
    completed = readiness.get("completed_through")
    next_action = readiness.get("next_action")

    if completed == "B2E02":
        require(isinstance(next_action, str) and next_action.startswith("Execute B2E03 only:"), "B2E03 is not sole pre-reconciliation next action")
        require("whispercpp-compact" in next_action, "B2E03 candidate identity missing")
        require("Do not begin B2E04" in next_action, "B2E04+ closure missing before B2E03 reconciliation")
        require("- [x] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0." in tasks, "B2E02 predecessor completion drift")
        require("- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0." in tasks, "B2E03 task must remain pending during execution qualification")
        require("- [ ] `B2E04` Decode the identical frozen P0 subset with candidate cell 4 under C0." in tasks, "B2E04 must remain unauthorized")
        require("current bounded execution unit `B2E03`" in current, "CURRENT B2E03 frontier drift")
        require("B2E03 (`whispercpp-compact`) is the sole current bounded execution unit" in current, "CURRENT B2E03 sole-unit authority missing")
        require("B2E04 and all later candidate cells remain unauthorized" in current, "CURRENT B2E04+ closure missing")
    elif completed == "B2E03":
        require(isinstance(next_action, str) and next_action.startswith("Execute B2E04 only:"), "B2E04 is not sole post-B2E03 next action")
        require("whispercpp-balanced" in next_action, "B2E04 candidate identity missing")
        require("Do not begin B2E05" in next_action, "B2E05+ closure missing after B2E03 reconciliation")
        require("- [x] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0." in tasks, "B2E03 canonical completion drift")
        require("- [ ] `B2E04` Decode the identical frozen P0 subset with candidate cell 4 under C0." in tasks, "B2E04 task frontier drift")
        require("current bounded execution unit `B2E04`" in current, "CURRENT B2E04 frontier drift")
        require("B2E04 (`whispercpp-balanced`) is the sole current bounded execution unit" in current, "CURRENT B2E04 sole-unit authority missing")
        require("B2E05 and all later candidate cells remain unauthorized" in current, "CURRENT B2E05+ closure missing")
    else:
        require("- [x] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0." in tasks, "later canonical state lost B2E03 completion")

    require("- [x] `B2E01` Decode the frozen P0 public-human subset with candidate cell 1 under C0." in tasks, "B2E01 predecessor completion drift")
    require("- [x] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0." in tasks, "B2E02 predecessor completion drift")

    require(attempt.get("schema_version") == "000b2-public-attempt-manifest-v1", "attempt schema drift")
    require(attempt.get("frozen") is True, "attempt is not frozen")
    require(attempt.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-001", "attempt id drift")
    require(attempt.get("phase") == "PRE_PRIMARY_FROZEN", "attempt phase drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_ATTEMPT_FREEZE, "attempt freeze digest drift")
    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "candidate set missing")
    require(candidate_set.get("candidate_ids") == EXPECTED_CANDIDATE_IDS, "frozen candidate set drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership became mutable")
    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context drift")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context drift")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific transform drift")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio invariant drift")
    require(contract.get("raw_outputs_and_failures_must_be_preserved") is True, "raw-output preservation invariant drift")
    require(contract.get("candidate_decoding_started") is False and contract.get("primary_decoding_started") is False, "historical frozen predecode manifest mutated")
    claims = attempt.get("claims")
    require(isinstance(claims, dict), "attempt claim guards missing")
    require(claims.get("comparative_performance_authorized") is False, "comparative performance became authorized")
    require(claims.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(claims.get("production_stt_selected") is False and claims.get("product_code_authorized") is False, "product authority opened early")


def expect_rejection(label: str, readiness: dict[str, Any], tasks: str, current: str, attempt: dict[str, Any]) -> None:
    try:
        validate_frontier(readiness, tasks, current, attempt)
    except VerifyError:
        return
    raise VerifyError(f"authority mutation did not fail closed: {label}")


def static_frontier() -> None:
    readiness = load(READINESS)
    tasks = TASKS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    attempt = load(ATTEMPT)
    validate_frontier(readiness, tasks, current, attempt)
    require(sha(PREPROCESSING) == EXPECTED_PREPROCESSING, "preprocessing bytes drift")

    completed = readiness.get("completed_through")
    if completed == "B2E02":
        bad_readiness = copy.deepcopy(readiness)
        bad_readiness["completed_through"] = "B2E01"
        expect_rejection("predecessor frontier", bad_readiness, tasks, current, attempt)

        bad_readiness = copy.deepcopy(readiness)
        bad_readiness["next_action"] = str(bad_readiness["next_action"]).replace("Do not begin B2E04", "Begin B2E04")
        expect_rejection("successor closure", bad_readiness, tasks, current, attempt)

        bad_tasks = tasks.replace(
            "- [x] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0.",
            "- [ ] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0.",
        )
        expect_rejection("B2E02 completion", readiness, bad_tasks, current, attempt)

        bad_current = current.replace("B2E04 and all later candidate cells remain unauthorized", "later frontier altered")
        expect_rejection("CURRENT successor closure", readiness, tasks, bad_current, attempt)
    elif completed == "B2E03":
        bad_readiness = copy.deepcopy(readiness)
        bad_readiness["next_action"] = str(bad_readiness["next_action"]).replace("Do not begin B2E05", "Begin B2E05")
        expect_rejection("post-reconciliation successor closure", bad_readiness, tasks, current, attempt)

        bad_tasks = tasks.replace(
            "- [x] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0.",
            "- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0.",
        )
        expect_rejection("B2E03 completion", readiness, bad_tasks, current, attempt)

        bad_current = current.replace("B2E05 and all later candidate cells remain unauthorized", "later frontier altered")
        expect_rejection("CURRENT post-reconciliation closure", readiness, tasks, bad_current, attempt)
    else:
        bad_tasks = tasks.replace(
            "- [x] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0.",
            "- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0.",
        )
        expect_rejection("historical B2E03 completion", readiness, bad_tasks, current, attempt)

    bad_attempt = copy.deepcopy(attempt)
    bad_attempt["freeze_digest_sha256"] = "0" * 64
    expect_rejection("attempt freeze digest", readiness, tasks, current, bad_attempt)

    bad_attempt = copy.deepcopy(attempt)
    bad_attempt["candidate_set"]["candidate_ids"][2] = "whispercpp-balanced"
    expect_rejection("candidate cell identity", readiness, tasks, current, bad_attempt)


def preprocessing_index() -> dict[str, dict[str, Any]]:
    records = load(PREPROCESSING).get("execution", {}).get("records")
    require(isinstance(records, list) and len(records) == 240, "preprocessing cardinality drift")
    result: dict[str, dict[str, Any]] = {}
    for row in records:
        require(isinstance(row, dict), "preprocessing row malformed")
        uid = row.get("utterance_id")
        require(isinstance(uid, str) and uid and uid not in result, "preprocessing utterance identity drift")
        result[uid] = row
    require(len(result) == 240, "duplicate preprocessing utterance id")
    return result


def verify_payload(evidence: dict[str, Any]) -> None:
    recorded = evidence.get("evidence_payload_sha256")
    require(isinstance(recorded, str) and SHA64.fullmatch(recorded) is not None, "payload digest missing or malformed")
    unsigned = dict(evidence)
    unsigned.pop("evidence_payload_sha256", None)
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == recorded, "payload digest mismatch")


def verify_build_identity(identity: dict[str, Any]) -> None:
    require(identity.get("schema_version") == "000b2-whisper-build-identity-v2", "build identity schema drift")
    require(identity.get("source_revision") == EXPECTED_RUNTIME_REVISION, "runtime source revision drift")
    require(identity.get("source_tree") == EXPECTED_RUNTIME_TREE, "runtime source tree drift")
    require(identity.get("build_type") == "Release", "build type drift")
    require(identity.get("ggml_cuda") == "OFF" and identity.get("ggml_metal") == "OFF", "GPU build flags drift")
    require(identity.get("whisper_build_tests") == "OFF" and identity.get("whisper_build_examples") == "OFF", "bounded build flags drift")
    require(identity.get("target") == "wispral-whispercpp-c0", "adapter target drift")
    require(identity.get("adapter_source_path") == "research/000b2-public/whispercpp-adapter/adapter.cpp", "adapter source path drift")
    require(identity.get("adapter_cmake_path") == "research/000b2-public/whispercpp-adapter/CMakeLists.txt", "adapter CMake path drift")
    require(identity.get("adapter_source_sha256") == sha(ADAPTER_SOURCE), "adapter source digest drift")
    require(identity.get("adapter_cmake_sha256") == sha(ADAPTER_CMAKE), "adapter CMake digest drift")
    for key in ("adapter_binary_sha256", "cmake_cache_sha256", "compiler_version_sha256", "cmake_version_sha256"):
        value = identity.get(key)
        require(isinstance(value, str) and SHA64.fullmatch(value) is not None, f"build identity digest malformed: {key}")


def reconstruct_stream_text(iterations: list[str]) -> str:
    result = ""
    for committed in range(9, len(iterations) + 1, 9):
        result += iterations[committed - 1] + "\n"
    if iterations and len(iterations) % 9:
        result += iterations[-1]
    return result


def verify_evidence(evidence_path: Path) -> dict[str, Any]:
    static_frontier()
    evidence = load(evidence_path)
    verify_payload(evidence)
    require(evidence.get("schema_version") == "000b2-public-b2e03-decode-v1", "schema drift")
    require(evidence.get("task") == "B2E03" and evidence.get("state") == "C0_PRIMARY_DECODE_CAPTURED", "task/state drift")
    require(evidence.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-001", "attempt id drift")

    candidate = evidence.get("candidate")
    require(isinstance(candidate, dict), "candidate block missing")
    require(candidate.get("cell_index") == 3 and candidate.get("candidate_id") == "whispercpp-compact", "candidate cell 3 drift")
    require(candidate.get("family") == "whisper.cpp" and candidate.get("tier") == "COMPACT", "candidate family/tier drift")
    require(candidate.get("runtime_revision") == EXPECTED_RUNTIME_REVISION, "runtime revision drift")
    require(candidate.get("runtime_source_tree") == EXPECTED_RUNTIME_TREE, "runtime tree drift")
    require(candidate.get("model_source_revision") == EXPECTED_MODEL_SOURCE_REVISION, "model source revision drift")
    require(candidate.get("model") == EXPECTED_MODEL_NAME, "model name drift")
    artifacts = candidate.get("artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 1, "candidate artifact cardinality drift")
    artifact = artifacts[0]
    require(isinstance(artifact, dict), "candidate artifact malformed")
    require(artifact.get("path") == EXPECTED_MODEL_NAME, "candidate artifact path drift")
    require(artifact.get("size_bytes") == EXPECTED_MODEL_BYTES, "candidate artifact size drift")
    require(artifact.get("sha256") == EXPECTED_MODEL_SHA256, "candidate artifact digest drift")
    build_identity = candidate.get("adapter_build_identity")
    require(isinstance(build_identity, dict), "adapter build identity missing")
    verify_build_identity(build_identity)
    require(candidate.get("streaming_semantics_observed") is True, "streaming semantics were not observed")

    authority = evidence.get("authority")
    require(isinstance(authority, dict), "authority block missing")
    require(authority.get("canonical_authority_base") == EXPECTED_BASE, "authority base drift")
    require(authority.get("attempt_manifest_path") == "research/000b2-public/attempt-manifest.json", "attempt path drift")
    require(authority.get("attempt_manifest_sha256") == sha(ATTEMPT), "attempt bytes drift")
    require(authority.get("attempt_freeze_digest_sha256") == EXPECTED_ATTEMPT_FREEZE, "attempt freeze binding drift")
    require(authority.get("preprocessing_capture_path") == "research/000b2-public/preprocessing-capture.json", "preprocessing path drift")
    require(authority.get("preprocessing_capture_sha256") == EXPECTED_PREPROCESSING, "preprocessing binding drift")

    require(evidence.get("c0_controls") == {
        "audio_ctx": 0,
        "beam_size": -1,
        "candidate_specific_audio_transform_used": False,
        "final_speech_chunk_preserved": True,
        "finalization_zero_pad_samples": FINAL_ZERO_SAMPLES,
        "flash_attention": False,
        "identical_frozen_audio_required_across_candidates": True,
        "initial_prompt": None,
        "keep_context": False,
        "keep_ms": 200,
        "language": "en",
        "length_ms": 5000,
        "max_tokens": 0,
        "prompt_carryover": False,
        "raw_transcript_materialization": RAW_TRANSCRIPT_MATERIALIZATION,
        "regular_chunk_samples": REGULAR_CHUNK_SAMPLES,
        "repository_context_used": False,
        "sampling": "GREEDY",
        "single_segment": True,
        "step_ms": 500,
        "temperature_fallback": "OFF",
        "test_specific_context_used": False,
        "threads": 4,
        "timestamps": False,
        "translate": False,
        "use_gpu": False,
        "vad": False,
        "zero_suffix_chunk_samples": FINAL_ZERO_CHUNKS,
    }, "frozen whisper.cpp C0 controls drift")

    run = evidence.get("run")
    require(isinstance(run, dict), "run provenance missing")
    source = run.get("repository_revision")
    require(isinstance(source, str) and SHA40.fullmatch(source) is not None, "repository revision malformed")
    subprocess.run(["git", "cat-file", "-e", f"{source}^{{commit}}"], cwd=ROOT, check=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", source, "HEAD"], cwd=ROOT, check=True)
    require(run.get("github_repository") == "TheHalfMoon/Wispral", "GitHub repository provenance drift")
    require(isinstance(run.get("github_run_id"), int) and run["github_run_id"] > 0, "GitHub run id malformed")
    require(isinstance(run.get("github_run_attempt"), int) and run["github_run_attempt"] > 0, "GitHub run attempt malformed")
    require(run.get("github_job") == "capture-b2e03", "GitHub job provenance drift")
    require(isinstance(run.get("preprocessing_container_image"), str) and run["preprocessing_container_image"], "preprocessing container identity missing")
    require(run.get("timing_semantics") == "DIAGNOSTIC_ONLY", "timing semantics drift")
    require(run.get("comparative_performance_authorized") is False, "comparative performance became authorized")

    execution = evidence.get("execution")
    require(isinstance(execution, dict), "execution block missing")
    require(execution.get("input_count") == 240, "input count drift")
    decoded = execution.get("decoded_count")
    failed = execution.get("failure_count")
    require(isinstance(decoded, int) and isinstance(failed, int) and decoded + failed == 240, "decode/failure count drift")
    require(execution.get("all_frozen_input_hashes_reverified") is True, "input-hash reverification missing")
    require(execution.get("all_speech_samples_delivered_for_decoded_records") is True, "speech feed completeness attestation missing")
    require(execution.get("all_zero_suffix_samples_delivered_for_decoded_records") is True, "zero-suffix feed completeness attestation missing")
    for key in ("reference_transcripts_loaded_by_decoder", "accuracy_scoring_performed", "comparative_ranking_present", "performance_claim_present"):
        require(execution.get(key) is False, f"forbidden execution claim: {key}")
    require(isinstance(execution.get("total_decode_wall_seconds"), (int, float)) and execution["total_decode_wall_seconds"] >= 0, "total timing malformed")

    expected = preprocessing_index()
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240, "execution record cardinality drift")
    record_keys = {
        "utterance_id",
        "source_partition",
        "canonical_preprocessed_file_sha256",
        "status",
        "raw_lines",
        "raw_transcript",
        "failure",
        "stream_iteration_count",
        "speech_sample_count",
        "speech_samples_delivered",
        "regular_speech_chunk_count",
        "final_speech_chunk_samples",
        "zero_suffix_samples_delivered",
        "zero_suffix_chunks_delivered",
        "decode_wall_seconds",
    }
    seen: set[str] = set()
    observed_decoded = 0
    observed_failed = 0
    for row in records:
        require(isinstance(row, dict) and set(row) == record_keys, "execution record key set drift")
        uid = row.get("utterance_id")
        require(isinstance(uid, str) and uid in expected and uid not in seen, f"utterance identity drift: {uid}")
        seen.add(uid)
        require(row.get("source_partition") == expected[uid].get("source_partition"), f"partition drift: {uid}")
        require(row.get("canonical_preprocessed_file_sha256") == expected[uid].get("canonical_preprocessed_file_sha256"), f"input digest drift: {uid}")
        lines = row.get("raw_lines")
        require(isinstance(lines, list) and all(isinstance(value, str) for value in lines), f"raw iteration lines malformed: {uid}")
        require(row.get("stream_iteration_count") == len(lines), f"stream iteration accounting drift: {uid}")
        require(row.get("raw_transcript") == reconstruct_stream_text(lines), f"effective stream transcript reconstruction drift: {uid}")
        require(isinstance(row.get("decode_wall_seconds"), (int, float)) and row["decode_wall_seconds"] >= 0, f"timing malformed: {uid}")

        speech_count = row.get("speech_sample_count")
        speech_delivered = row.get("speech_samples_delivered")
        regular_chunks = row.get("regular_speech_chunk_count")
        final_chunk = row.get("final_speech_chunk_samples")
        zero_delivered = row.get("zero_suffix_samples_delivered")
        zero_chunks = row.get("zero_suffix_chunks_delivered")
        require(speech_count == expected[uid].get("wav_frame_count"), f"speech sample count drift: {uid}")
        require(isinstance(speech_delivered, int) and 0 <= speech_delivered <= speech_count, f"speech delivery accounting drift: {uid}")
        require(regular_chunks == speech_count // REGULAR_CHUNK_SAMPLES, f"regular speech chunk count drift: {uid}")
        require(final_chunk == speech_count % REGULAR_CHUNK_SAMPLES, f"final speech chunk drift: {uid}")
        require(isinstance(zero_delivered, int) and 0 <= zero_delivered <= FINAL_ZERO_SAMPLES, f"zero-suffix delivery accounting drift: {uid}")
        require(isinstance(zero_chunks, int) and 0 <= zero_chunks <= len(FINAL_ZERO_CHUNKS), f"zero-suffix chunk accounting drift: {uid}")
        planned_iterations = regular_chunks + (1 if final_chunk else 0) + len(FINAL_ZERO_CHUNKS)
        require(row["stream_iteration_count"] <= planned_iterations, f"stream iteration count exceeds frozen schedule: {uid}")

        if row.get("status") == "DECODED":
            observed_decoded += 1
            require(row.get("failure") is None, f"decoded row has failure: {uid}")
            require(row["stream_iteration_count"] == planned_iterations, f"decoded row did not execute full frozen feed schedule: {uid}")
            require(speech_delivered == speech_count, f"decoded row did not preserve final speech feed: {uid}")
            require(zero_delivered == FINAL_ZERO_SAMPLES, f"decoded row did not receive full zero suffix: {uid}")
            require(zero_chunks == len(FINAL_ZERO_CHUNKS), f"decoded row zero-suffix chunk count drift: {uid}")
        elif row.get("status") == "FAILED":
            observed_failed += 1
            require(isinstance(row.get("failure"), dict), f"failure evidence missing: {uid}")
        else:
            raise VerifyError(f"unknown decode status: {uid}")
    require(len(seen) == 240 and observed_decoded == decoded and observed_failed == failed, "execution accounting drift")

    require(evidence.get("claim_guards") == {
        "b2e04_authorized": False,
        "candidate_decoding_started": True,
        "completed_through": "B2E03_EXECUTION_ONLY",
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "primary_decoding_started": True,
        "product_code_authorized": False,
        "production_stt_selected": False,
    }, "B2E03 claim guards drift")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    try:
        static_frontier()
        if args.static_only:
            print("B2E03_STATIC=PASS")
            print("B2E03_AUTHORITY_REGRESSIONS=PASS")
            print("B2E04_AUTHORIZED=NO")
            return 0
        evidence = verify_evidence(args.evidence)
        print("B2E03_EVIDENCE=PASS")
        print(f"B2E03_SOURCE_REVISION={evidence['run']['repository_revision']}")
        print(f"B2E03_INPUTS={evidence['execution']['input_count']}")
        print(f"B2E03_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2E03_FAILURES={evidence['execution']['failure_count']}")
        print("B2E04_AUTHORIZED=NO")
        return 0
    except (VerifyError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"B2E03_EVIDENCE=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
