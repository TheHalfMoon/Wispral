#!/usr/bin/env python3
"""Verify B2R05 ATTEMPT-002 moonshine-compact primary execution evidence without scoring."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
DECODER = PUBLIC / "decode_b2r05.py"
EVIDENCE_DEFAULT = PUBLIC / "b2r05-moonshine-compact.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"

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
EXPECTED_WORKFLOW = "Internal B2R05 ATTEMPT-002 Moonshine Compact Capture"
EXPECTED_WORKFLOW_PATH = ".github/workflows/internal-b2r05-capture.yml"
EXPECTED_EXECUTION_REF = "refs/heads/execution/000b2-b2r05-moonshine-compact"
EXPECTED_RECORDS = 240
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class VerifyError(ValueError):
    """Raised when B2R05 evidence fails closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)


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


def canonical_digest(value: dict[str, Any]) -> str:
    copy = dict(value)
    copy.pop("evidence_payload_sha256", None)
    raw = (json.dumps(copy, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_decoder() -> Any:
    spec = importlib.util.spec_from_file_location("wispral_b2r05_decoder", DECODER)
    require(spec is not None and spec.loader is not None, "unable to load B2R05 decoder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_decoder_structure() -> None:
    source = DECODER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(DECODER))

    forbidden = "transcribe_" + "without_streaming"
    require(forbidden not in source, "historical non-streaming Moonshine API appears in B2R05 decoder")
    require("score_public_wer" not in source, "B2R05 decoder imports or references the public scorer")
    require("scorer.py" not in source, "B2R05 decoder references core scoring implementation")
    require("reference_text" not in source and "reference_manifest" not in source, "B2R05 decoder references scoring references")

    calls: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            calls.append(func.attr)
        elif isinstance(func, ast.Name):
            calls.append(func.id)
    require("transcribe_streaming_c0" in calls, "corrected streaming C0 harness call missing")
    require("create_transcriber" in calls, "corrected transcriber construction missing")

    decoder = load_decoder()
    decoder.verify_authority()
    records = decoder.preprocessing_records()
    require(len(records) == EXPECTED_RECORDS, "frozen preprocessing record count drift")


def trace_requirements(trace: Any, frame_count: int, utterance: str) -> None:
    require(isinstance(trace, dict), f"{utterance}: streaming trace missing")
    require(trace.get("speech_samples") == frame_count, f"{utterance}: speech sample count drift")
    chunks = trace.get("speech_chunk_samples")
    require(isinstance(chunks, list) and chunks, f"{utterance}: speech chunk trace malformed")
    require(all(isinstance(value, int) and 0 < value <= 8000 for value in chunks), f"{utterance}: speech chunk size drift")
    require(sum(chunks) == frame_count, f"{utterance}: speech chunk sum drift")
    if len(chunks) > 1:
        require(all(value == 8000 for value in chunks[:-1]), f"{utterance}: non-final chunk is not exactly 8000 samples")
    require(trace.get("zero_pad_samples") == 10560, f"{utterance}: final zero suffix drift")
    require(trace.get("sample_rate_hz") == 16000, f"{utterance}: trace sample rate drift")
    require(trace.get("stream_started") is True, f"{utterance}: stream-start trace missing")
    require(trace.get("stream_stopped") is True, f"{utterance}: stream-stop trace missing")


def verify_evidence(path: Path) -> None:
    evidence = load(path)
    require(evidence.get("schema_version") == "000b2-public-attempt-002-cell-evidence-v1", "B2R05 evidence schema drift")
    require(evidence.get("task") == TASK, "B2R05 task id drift")
    require(evidence.get("lane") == "PUBLIC_CORPUS", "B2R05 lane drift")
    require(evidence.get("state") == "PRIMARY_CELL_EXECUTION_CAPTURED_UNSCORED", "B2R05 evidence state drift")

    attempt = evidence.get("attempt", {})
    require(attempt.get("attempt_id") == ATTEMPT_ID, "ATTEMPT-002 id drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_ATTEMPT_FREEZE, "ATTEMPT-002 freeze digest drift")
    require(attempt.get("frozen") is True, "ATTEMPT-002 not frozen in evidence")

    authority = evidence.get("authority", {})
    require(authority.get("canonical_base") == EXPECTED_AUTHORITY_BASE, "B2R05 canonical authority base drift")
    require(authority.get("active_recovery_unit") == TASK, "B2R05 active authority drift")
    require(authority.get("completed_recovery_tasks") == ["B2R01", "B2R02", "B2R03", "B2R04"], "B2R05 predecessor prefix drift")
    expected_hashes = {
        "b2r03_rebinding_sha256": EXPECTED_B2R03_SHA256,
        "preprocessing_sha256": EXPECTED_PREPROCESSING_SHA256,
        "subset_sha256": EXPECTED_SUBSET_SHA256,
        "corrected_c0_harness_sha256": EXPECTED_HARNESS_SHA256,
        "candidate_registry_sha256": EXPECTED_REGISTRY_SHA256,
        "frozen_methodology_sha256": EXPECTED_FROZEN_METHOD_SHA256,
        "core_scorer_sha256": EXPECTED_CORE_SCORER_SHA256,
        "core_config_sha256": EXPECTED_CORE_CONFIG_SHA256,
        "public_wer_adapter_sha256": EXPECTED_PUBLIC_WER_SHA256,
    }
    for key, expected in expected_hashes.items():
        require(authority.get(key) == expected, f"B2R05 authority hash drift: {key}")
    require(authority.get("decoder_path") == "research/000b2-public/decode_b2r05.py", "decoder path drift")
    require(authority.get("verifier_path") == "research/000b2-public/verify_b2r05.py", "verifier path drift")
    require(authority.get("decoder_sha256") == sha256_file(DECODER), "captured decoder bytes differ from verifier revision")
    require(authority.get("verifier_sha256") == sha256_file(Path(__file__)), "captured verifier bytes differ from verifier revision")

    candidate = evidence.get("candidate", {})
    require(candidate.get("cell_index") == 1, "candidate cell index drift")
    require(candidate.get("candidate_id") == CANDIDATE_ID, "candidate id drift")
    require(candidate.get("family") == "moonshine", "candidate family drift")
    require(candidate.get("runtime_revision") == EXPECTED_RUNTIME_REVISION, "Moonshine runtime revision drift")
    require(candidate.get("runtime_distribution") == "moonshine-voice", "Moonshine runtime distribution drift")
    require(candidate.get("runtime_distribution_version") == EXPECTED_RUNTIME_VERSION, "Moonshine runtime version drift")
    require(candidate.get("model_asset_revision") == EXPECTED_MODEL_ASSET_REVISION, "Moonshine model asset revision drift")
    contract = candidate.get("streaming_contract", {})
    require(contract == {
        "speech_chunk_samples": 8000,
        "zero_pad_samples": 10560,
        "sample_rate_hz": 16000,
        "transcription_interval_seconds": 0.5,
        "vad_threshold": 0.0,
        "repository_context": "OFF",
        "test_specific_context": "OFF",
        "keyterms": [],
    }, "corrected Moonshine streaming C0 contract drift")

    execution = evidence.get("execution", {})
    revision = execution.get("repository_revision")
    require(isinstance(revision, str) and HEX40.fullmatch(revision) is not None, "execution revision malformed")
    require(execution.get("workflow_path") == EXPECTED_WORKFLOW_PATH, "execution workflow path drift")
    workflow_sha = execution.get("workflow_sha256")
    require(isinstance(workflow_sha, str) and HEX64.fullmatch(workflow_sha) is not None, "execution workflow digest malformed")
    require(execution.get("input_record_count") == EXPECTED_RECORDS, "input record count drift")
    decoded = execution.get("decoded_record_count")
    failed = execution.get("failed_record_count")
    require(isinstance(decoded, int) and isinstance(failed, int) and decoded >= 0 and failed >= 0, "decode counts malformed")
    require(decoded + failed == EXPECTED_RECORDS, "decode accounting drift")
    require(execution.get("aggregate_timing_role") == "DIAGNOSTIC_ONLY_NOT_COMPARATIVE", "aggregate timing role drift")
    require(isinstance(execution.get("aggregate_decode_wall_seconds"), (int, float)), "aggregate diagnostic timing missing")

    runtime = execution.get("runtime_observations", {})
    require(runtime.get("capture_kind") == "GITHUB_HOSTED_DIAGNOSTIC", "runtime capture kind drift")
    require(runtime.get("performance_mode") == "DIAGNOSTIC", "runtime performance mode drift")
    require(runtime.get("comparative_performance_authorized") is False, "comparative performance opened")
    github = runtime.get("github", {})
    require(github.get("repository") == "TheHalfMoon/Wispral", "GitHub repository identity drift")
    require(github.get("workflow") == EXPECTED_WORKFLOW, "GitHub workflow identity drift")
    require(github.get("event_name") == "push", "execution event must be push")
    require(github.get("ref") == EXPECTED_EXECUTION_REF, "execution branch ref drift")
    require(github.get("sha") == revision, "runtime SHA differs from captured repository revision")
    require(isinstance(github.get("run_id"), int) and github["run_id"] > 0, "GitHub run id missing")
    require(isinstance(github.get("run_attempt"), int) and github["run_attempt"] > 0, "GitHub run attempt missing")
    runner = runtime.get("runner", {})
    require(runner.get("os") == "Linux", "execution runner OS drift")
    require(runner.get("arch") == "X64", "execution runner architecture drift")
    toolchain = runtime.get("toolchain", {})
    require(toolchain.get("python") == "3.12.14", "execution Python version drift")
    require(toolchain.get("moonshine_distribution") == EXPECTED_RUNTIME_VERSION, "installed Moonshine release drift")
    source_build = runtime.get("moonshine_source_build_identity", {})
    require(source_build.get("source_revision") == EXPECTED_RUNTIME_REVISION, "source-build Moonshine revision drift")
    require(source_build.get("release") == "v0.1.5", "source-build Moonshine release drift")
    require(source_build.get("runtime_origin") == "PINNED_SOURCE_CHECKOUT_BUILD", "Moonshine runtime origin drift")
    for key in ("source_tree", "python_source_manifest_sha256", "native_library_sha256", "onnxruntime_sha256", "cmake_cache_sha256"):
        value = source_build.get(key)
        pattern = HEX40 if key == "source_tree" else HEX64
        require(isinstance(value, str) and pattern.fullmatch(value) is not None, f"source-build identity malformed: {key}")

    pre = load(PREPROCESSING)
    source_records = pre.get("execution", {}).get("records")
    require(isinstance(source_records, list) and len(source_records) == EXPECTED_RECORDS, "preprocessing record ledger drift")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == EXPECTED_RECORDS, "execution record ledger drift")

    seen: set[str] = set()
    for index, (source, observed) in enumerate(zip(source_records, records, strict=True)):
        require(isinstance(source, dict) and isinstance(observed, dict), f"record {index}: malformed")
        utterance = source.get("utterance_id")
        require(isinstance(utterance, str) and utterance not in seen, f"record {index}: duplicate or malformed utterance")
        seen.add(utterance)
        require(observed.get("utterance_id") == utterance, f"{utterance}: execution order/identity drift")
        require(observed.get("source_partition") == source.get("source_partition"), f"{utterance}: source partition drift")
        inp = observed.get("input", {})
        require(inp.get("canonical_preprocessed_file_sha256") == source.get("canonical_preprocessed_file_sha256"), f"{utterance}: input digest drift")
        require(inp.get("canonical_preprocessed_bytes") == source.get("canonical_preprocessed_bytes"), f"{utterance}: input byte count drift")
        frame_count = source.get("wav_frame_count")
        require(inp.get("wav_frame_count") == frame_count, f"{utterance}: frame count drift")
        require(inp.get("wav_sample_rate_hz") == 16000, f"{utterance}: sample rate drift")

        status = observed.get("status")
        require(status in {"DECODED", "FAILED"}, f"{utterance}: status malformed")
        raw_lines = observed.get("raw_lines")
        require(isinstance(raw_lines, list) and all(isinstance(line, str) for line in raw_lines), f"{utterance}: raw lines malformed")
        require(observed.get("raw_transcript") == "\n".join(raw_lines), f"{utterance}: raw transcript reconstruction drift")
        failure = observed.get("failure")
        trace = observed.get("streaming_trace")
        if status == "DECODED":
            require(failure is None, f"{utterance}: decoded record contains failure")
            require(observed.get("result_was_none") is False, f"{utterance}: decoded record has no result")
            trace_requirements(trace, frame_count, utterance)
        else:
            require(isinstance(failure, dict), f"{utterance}: failed record lacks failure evidence")
            require(isinstance(failure.get("type"), str), f"{utterance}: failure type missing")
            require(isinstance(failure.get("message"), str), f"{utterance}: failure message missing")
            require(isinstance(failure.get("traceback"), str), f"{utterance}: failure traceback missing")
            if trace is not None:
                trace_requirements(trace, frame_count, utterance)
        runtime_obs = observed.get("runtime_observation", {})
        require(runtime_obs.get("timing_role") == "DIAGNOSTIC_ONLY_NOT_COMPARATIVE", f"{utterance}: timing role drift")
        require(isinstance(runtime_obs.get("decode_wall_seconds"), (int, float)), f"{utterance}: diagnostic timing missing")

    preservation = evidence.get("preservation", {})
    require(preservation == {
        "raw_transcripts_preserved": True,
        "failures_preserved": True,
        "runtime_observations_preserved": True,
        "exact_run_identity_preserved": True,
        "frozen_input_identities_preserved": True,
        "references_loaded_for_scoring": False,
        "scoring_performed": False,
        "candidate_ranking_performed": False,
        "result_driven_changes_performed": False,
    }, "B2R05 preservation contract drift")

    guards = evidence.get("claim_guards", {})
    require(guards == {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "comparative_performance_authorized": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
        "b2r06_authorized": False,
    }, "B2R05 claim guards drift")

    evidence_digest = evidence.get("evidence_payload_sha256")
    require(isinstance(evidence_digest, str) and HEX64.fullmatch(evidence_digest) is not None, "evidence payload digest malformed")
    require(evidence_digest == canonical_digest(evidence), "evidence payload digest mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--evidence", type=Path, default=EVIDENCE_DEFAULT)
    args = parser.parse_args()
    try:
        verify_decoder_structure()
        if not args.static_only:
            require(args.evidence.is_file() and not args.evidence.is_symlink(), "B2R05 evidence file missing or unsafe")
            verify_evidence(args.evidence)
        print("B2R05_VERIFICATION=PASS")
        return 0
    except (VerifyError, OSError, ValueError, SyntaxError) as exc:
        print(f"B2R05_VERIFICATION=FAIL:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
