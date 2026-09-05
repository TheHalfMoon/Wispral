#!/usr/bin/env python3
"""Verify bounded B2E03 whispercpp-compact C0 execution evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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

EXPECTED_BASE = "b326397cdd29fbb132b9c438ba2178626558efab"
EXPECTED_ATTEMPT_FREEZE = "af4d5009e293daef5d8f629ca91af653f5f591448cd94d4555473a51e2d1da86"
EXPECTED_PREPROCESSING = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_RUNTIME_REVISION = "371b5a7561823ab2bb32142d2751e35e7534727b"
EXPECTED_MODEL_SOURCE_REVISION = "80da2d8bfee42b0e836fc3a9890373e5defc00a6"
EXPECTED_MODEL_NAME = "ggml-base.en.bin"
EXPECTED_MODEL_BYTES = 147964211
EXPECTED_MODEL_SHA256 = "a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002"
EXPECTED_CLI_FLAGS = ["-t", "4", "-l", "en", "-ng", "-nfa", "-nf", "-nt", "-np", "-otxt"]
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class VerifyError(ValueError):
    """Raised when B2E03 evidence or authority fails closed."""


def require(condition: bool, message: str) -> None:
    """Fail closed with a stable verifier message."""
    if not condition:
        raise VerifyError(message)


def load(path: Path) -> dict[str, Any]:
    """Load one required JSON object."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise VerifyError(f"unable to load {path}: {error}") from error
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def sha(path: Path) -> str:
    """Return one file SHA-256."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    """Serialize canonical JSON for payload-digest checks."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def static_frontier() -> None:
    """Require B2E03-only canonical authority and immutable frozen-attempt state."""
    readiness = load(READINESS)
    tasks = TASKS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    require(readiness.get("state") == "READY", "public lane is not READY")
    require(readiness.get("completed_through") == "B2E02", "B2E03 requires canonical completion through B2E02")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Execute B2E03 only:"), "B2E03 is not sole next action")
    require("whispercpp-compact" in next_action, "B2E03 candidate identity missing")
    require("Do not begin B2E04 or any later candidate cell until B2E03 is canonical." in next_action, "B2E04+ closure missing")
    for item in (
        "- [x] `B2E01` Decode the frozen P0 public-human subset with candidate cell 1 under C0.",
        "- [x] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0.",
    ):
        require(item in tasks, "B2E03 predecessor completion drift")
    require("- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0." in tasks, "B2E03 task must remain pending during execution qualification")
    require("- [ ] `B2E04` Decode the identical frozen P0 subset with candidate cell 4 under C0." in tasks, "B2E04 must remain unauthorized")
    require("current bounded execution unit `B2E03`" in current, "CURRENT B2E03 frontier drift")
    require("B2E03 (`whispercpp-compact`) is the sole current bounded execution unit" in current, "CURRENT B2E03 sole-unit authority missing")
    require("B2E04 and all later candidate cells remain unauthorized" in current, "CURRENT B2E04+ closure missing")

    attempt = load(ATTEMPT)
    require(attempt.get("frozen") is True, "attempt is not frozen")
    require(attempt.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-001", "attempt id drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_ATTEMPT_FREEZE, "attempt freeze digest drift")
    candidate_set = attempt.get("candidate_set")
    require(isinstance(candidate_set, dict), "candidate set missing")
    ids = candidate_set.get("candidate_ids")
    require(isinstance(ids, list) and len(ids) == 6 and ids[2] == "whispercpp-compact", "candidate cell 3 drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership became mutable")
    contract = attempt.get("decoding_contract")
    require(isinstance(contract, dict), "decoding contract missing")
    require(contract.get("c0_repository_context") == "OFF", "repository context drift")
    require(contract.get("c0_test_specific_context") == "OFF", "test-specific context drift")
    require(contract.get("candidate_specific_audio_transform") == "OFF", "candidate-specific transform drift")
    require(contract.get("identical_frozen_audio_required_across_candidates") is True, "identical frozen audio invariant drift")
    require(contract.get("candidate_decoding_started") is False and contract.get("primary_decoding_started") is False, "historical frozen predecode manifest mutated")
    require(sha(PREPROCESSING) == EXPECTED_PREPROCESSING, "preprocessing bytes drift")


def preprocessing_index() -> dict[str, dict[str, Any]]:
    """Return the exact 240-record frozen preprocessing index."""
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
    """Verify the self-authenticating canonical JSON payload digest."""
    recorded = evidence.get("evidence_payload_sha256")
    require(isinstance(recorded, str) and SHA64.fullmatch(recorded) is not None, "payload digest missing or malformed")
    unsigned = dict(evidence)
    unsigned.pop("evidence_payload_sha256", None)
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == recorded, "payload digest mismatch")


def verify_evidence(evidence_path: Path) -> dict[str, Any]:
    """Verify one generated or committed B2E03 evidence payload without scoring it."""
    static_frontier()
    evidence = load(evidence_path)
    verify_payload(evidence)
    require(evidence.get("schema_version") == "000b2-public-b2e03-decode-v1", "schema drift")
    require(evidence.get("task") == "B2E03", "task drift")
    require(evidence.get("state") == "C0_PRIMARY_DECODE_CAPTURED", "state drift")
    require(evidence.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-001", "attempt id drift")

    candidate = evidence.get("candidate")
    require(isinstance(candidate, dict), "candidate block missing")
    require(candidate.get("cell_index") == 3, "candidate cell index drift")
    require(candidate.get("candidate_id") == "whispercpp-compact", "candidate id drift")
    require(candidate.get("family") == "whisper.cpp", "candidate family drift")
    require(candidate.get("tier") == "COMPACT", "candidate tier drift")
    require(candidate.get("runtime_repository") == "ggml-org/whisper.cpp", "runtime repository drift")
    require(candidate.get("source_revision") == EXPECTED_RUNTIME_REVISION, "runtime revision drift")
    require(isinstance(candidate.get("cli_binary_sha256"), str) and SHA64.fullmatch(candidate["cli_binary_sha256"]) is not None, "CLI digest malformed")
    require(isinstance(candidate.get("version_output_sha256"), str) and SHA64.fullmatch(candidate["version_output_sha256"]) is not None, "version-output digest malformed")
    require(candidate.get("model_source_repository") == "ggerganov/whisper.cpp", "model source repository drift")
    require(candidate.get("model_source_revision") == EXPECTED_MODEL_SOURCE_REVISION, "model source revision drift")
    require(candidate.get("model_name") == EXPECTED_MODEL_NAME, "model name drift")
    require(candidate.get("model_bytes") == EXPECTED_MODEL_BYTES, "model byte-size drift")
    require(candidate.get("model_sha256") == EXPECTED_MODEL_SHA256, "model SHA-256 drift")

    authority = evidence.get("authority")
    require(isinstance(authority, dict), "authority block missing")
    require(authority.get("canonical_authority_base") == EXPECTED_BASE, "authority base drift")
    require(authority.get("attempt_manifest_path") == "research/000b2-public/attempt-manifest.json", "attempt path drift")
    require(authority.get("attempt_manifest_sha256") == sha(ATTEMPT), "attempt bytes drift")
    require(authority.get("attempt_freeze_digest_sha256") == EXPECTED_ATTEMPT_FREEZE, "attempt freeze binding drift")
    require(authority.get("preprocessing_capture_path") == "research/000b2-public/preprocessing-capture.json", "preprocessing path drift")
    require(authority.get("preprocessing_capture_sha256") == EXPECTED_PREPROCESSING, "preprocessing binding drift")

    controls = evidence.get("c0_controls")
    require(isinstance(controls, dict), "C0 controls missing")
    require(controls.get("language") == "en", "language drift")
    for key in (
        "initial_prompt_used",
        "prompt_carryover_used",
        "repository_context_used",
        "test_specific_context_used",
        "grammar_used",
        "candidate_specific_audio_transform_used",
    ):
        require(controls.get(key) is False, f"C0 control enabled: {key}")
    require(controls.get("identical_frozen_audio_required_across_candidates") is True, "identical-audio C0 invariant drift")
    require(controls.get("cli_flags") == EXPECTED_CLI_FLAGS, "whisper-cli C0 flag set drift")

    run = evidence.get("run")
    require(isinstance(run, dict), "run provenance missing")
    require(isinstance(run.get("repository_revision"), str) and SHA40.fullmatch(run["repository_revision"]) is not None, "repository revision malformed")
    require(run.get("github_repository") == "TheHalfMoon/Wispral", "GitHub repository provenance drift")
    require(isinstance(run.get("github_run_id"), int) and run["github_run_id"] > 0, "GitHub run id malformed")
    require(isinstance(run.get("github_run_attempt"), int) and run["github_run_attempt"] > 0, "GitHub run attempt malformed")
    require(run.get("github_job") == "capture-b2e03", "GitHub job provenance drift")
    require(run.get("execution_surface") == "GITHUB_HOSTED_UBUNTU24", "execution surface drift")
    require(isinstance(run.get("preprocessing_container_image"), str) and run["preprocessing_container_image"], "preprocessing container identity missing")
    require(run.get("timing_semantics") == "DIAGNOSTIC_ONLY", "timing semantics drift")
    require(run.get("comparative_performance_authorized") is False, "comparative performance became authorized")

    claim_guards = evidence.get("claim_guards")
    require(isinstance(claim_guards, dict), "claim guards missing")
    require(claim_guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(claim_guards.get("public_audiobook_speech_represents_developer_speech") is False, "public speech mislabeled as developer speech")
    require(claim_guards.get("production_stt_selected") is False, "production STT selected early")
    require(claim_guards.get("product_code_authorized") is False, "product code authorized early")
    require(claim_guards.get("comparative_performance_authorized") is False, "comparative performance authorized early")

    execution = evidence.get("execution")
    require(isinstance(execution, dict), "execution block missing")
    require(execution.get("input_count") == 240, "input count drift")
    decoded = execution.get("decoded_count")
    failed = execution.get("failure_count")
    require(isinstance(decoded, int) and isinstance(failed, int) and decoded + failed == 240, "decode/failure count drift")
    require(execution.get("all_frozen_input_hashes_reverified") is True, "input-hash reverification missing")
    require(execution.get("reference_transcripts_loaded_by_decoder") is False, "decoder loaded reference transcripts")
    require(execution.get("accuracy_scoring_performed") is False, "accuracy scoring occurred during B2E03")
    require(execution.get("comparative_ranking_present") is False, "comparative ranking occurred during B2E03")
    require(execution.get("performance_claim_present") is False, "performance claim occurred during B2E03")
    require(execution.get("timing_granularity") == "BATCH_ONLY_DIAGNOSTIC", "timing granularity drift")
    require(isinstance(execution.get("total_decode_wall_seconds"), (int, float)) and execution["total_decode_wall_seconds"] >= 0, "batch timing malformed")
    require(isinstance(execution.get("batch_timed_out"), bool), "batch timeout flag malformed")
    require(execution.get("batch_exit_code") is None or isinstance(execution.get("batch_exit_code"), int), "batch exit code malformed")
    require(isinstance(execution.get("batch_diagnostic_output_sha256"), str) and SHA64.fullmatch(execution["batch_diagnostic_output_sha256"]) is not None, "batch diagnostic digest malformed")
    require(execution.get("batch_diagnostic_output_retained") is False, "batch diagnostic output was retained")

    expected = preprocessing_index()
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240, "execution record cardinality drift")
    seen: set[str] = set()
    observed_decoded = 0
    observed_failed = 0
    for row in records:
        require(isinstance(row, dict), "execution record malformed")
        require(set(row) == {
            "utterance_id",
            "source_partition",
            "canonical_preprocessed_file_sha256",
            "status",
            "raw_lines",
            "raw_transcript",
            "failure",
            "decode_wall_seconds",
        }, "execution record key set drift")
        uid = row.get("utterance_id")
        require(isinstance(uid, str) and uid in expected and uid not in seen, "execution utterance identity drift")
        seen.add(uid)
        source = expected[uid]
        require(row.get("source_partition") == source.get("source_partition"), f"source partition drift: {uid}")
        require(row.get("canonical_preprocessed_file_sha256") == source.get("canonical_preprocessed_file_sha256"), f"input digest drift: {uid}")
        require(row.get("decode_wall_seconds") is None, f"per-utterance timing unexpectedly asserted: {uid}")
        status = row.get("status")
        require(status in {"DECODED", "FAILED"}, f"decode status drift: {uid}")
        require(isinstance(row.get("raw_lines"), list) and all(isinstance(item, str) for item in row["raw_lines"]), f"raw lines malformed: {uid}")
        require(isinstance(row.get("raw_transcript"), str), f"raw transcript malformed: {uid}")
        if status == "DECODED":
            observed_decoded += 1
            require(row.get("failure") is None, f"decoded row has failure: {uid}")
        else:
            observed_failed += 1
            failure = row.get("failure")
            require(isinstance(failure, dict), f"failed row missing failure object: {uid}")
            require(isinstance(failure.get("type"), str) and failure["type"], f"failure type missing: {uid}")
            require(isinstance(failure.get("message"), str), f"failure message malformed: {uid}")
    require(len(seen) == 240, "execution membership drift")
    require(observed_decoded == decoded and observed_failed == failed, "record/count reconciliation drift")
    return evidence


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()
    try:
        if args.static_only:
            static_frontier()
            print("B2E03_STATIC_FRONTIER=PASS")
        else:
            evidence = verify_evidence(args.evidence)
            print("B2E03_EVIDENCE=PASS")
            print(f"B2E03_INPUTS={evidence['execution']['input_count']}")
            print(f"B2E03_DECODED={evidence['execution']['decoded_count']}")
            print(f"B2E03_FAILURES={evidence['execution']['failure_count']}")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        print("COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
        print("PRODUCTION_STT_SELECTED=NO")
        print("PRODUCT_CODE_AUTHORIZED=NO")
        return 0
    except (VerifyError, OSError, ValueError) as error:
        print(f"B2E03_EVIDENCE=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
