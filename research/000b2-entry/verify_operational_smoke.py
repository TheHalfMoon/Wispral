#!/usr/bin/env python3
"""Fail-closed verifier for durable or freshly aggregated B2 smoke evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "000b2-entry"
B1 = ROOT / "research" / "000b1"
EVIDENCE = HERE / "operational-smoke-evidence.json"
REGISTRY = B1 / "qualified-candidates.json"
MATERIALIZED = HERE / "materialized-artifacts.json"
AMENDMENT = HERE / "artifact-size-amendment.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_CELLS = {
    "moonshine-balanced": ("moonshine", "BALANCED"),
    "moonshine-compact": ("moonshine", "COMPACT"),
    "sherpa-onnx-balanced": ("sherpa-onnx", "BALANCED"),
    "sherpa-onnx-compact": ("sherpa-onnx", "COMPACT"),
    "whispercpp-balanced": ("whisper.cpp", "BALANCED"),
    "whispercpp-compact": ("whisper.cpp", "COMPACT"),
}
EXPECTED_WORKFLOW = {
    "name": "000B2 Operational Smoke",
    "head_sha": "3cdaea6f0c5867a9595e70c50c130f375b25ac2c",
    "run_id": 33522881549,
    "run_number": 2,
}
EXPECTED_SYNTHETIC_SHA = "860debf008a4702098968ca7b113ea8df7ee0188c9ca08c7c1e9437466876c38"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def digest_without(obj: dict[str, Any], field: str) -> str:
    clone = dict(obj)
    clone.pop(field, None)
    raw = (json.dumps(clone, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def expected_artifacts() -> dict[str, dict[str, tuple[int, str]]]:
    registry = load(REGISTRY)
    materialized = load(MATERIALIZED)
    amendment = load(AMENDMENT)
    corrected_sizes = {
        (row["candidate_id"], row["path"]): row["b2_entry_size_bytes"]
        for row in amendment["corrections"]
    }
    materialized_rows = {
        (candidate_id, path): row
        for candidate_id, paths in materialized["artifacts"].items()
        for path, row in paths.items()
    }
    result: dict[str, dict[str, tuple[int, str]]] = {}
    for family in registry["families"]:
        for config in family["configurations"]:
            candidate_id = config["id"]
            artifacts: dict[str, tuple[int, str]] = {}
            for artifact in config["artifacts"]:
                path = artifact["path"]
                key = (candidate_id, path)
                size = corrected_sizes.get(key, artifact["size_bytes"])
                digest = artifact.get("sha256")
                if digest is None:
                    row = materialized_rows.get(key)
                    if row is None:
                        fail(f"missing materialized artifact authority for {candidate_id}:{path}")
                    if row["size_bytes"] != size:
                        fail(f"materialized size authority drift for {candidate_id}:{path}")
                    digest = row["sha256"]
                artifacts[path] = (size, digest)
            result[candidate_id] = artifacts
    return result


def expected_runtime_revisions() -> dict[str, str]:
    registry = load(REGISTRY)
    revisions: dict[str, str] = {}
    for family in registry["families"]:
        family_name = family.get("family")
        runtime = family.get("runtime")
        if not isinstance(family_name, str) or not isinstance(runtime, dict):
            fail("qualified candidate family/runtime malformed")
        revision = runtime.get("revision")
        if not isinstance(revision, str) or not SHA40.fullmatch(revision):
            fail(f"qualified runtime revision malformed: {family_name}")
        if family_name in revisions:
            fail(f"duplicate runtime family authority: {family_name}")
        revisions[family_name] = revision
    if set(revisions) != {"moonshine", "whisper.cpp", "sherpa-onnx"}:
        fail("qualified runtime family authority drift")
    return revisions


def verify_runtime(candidate_id: str, family: str, cell: dict[str, Any], expected_revision: str) -> None:
    runtime_revision = cell.get("runtime_revision")
    if runtime_revision != expected_revision:
        fail(f"runtime revision differs from frozen B1 authority: {candidate_id}")
    if not SHA40.fullmatch(runtime_revision):
        fail(f"runtime revision malformed: {candidate_id}")

    runtime = cell.get("runtime")
    if not isinstance(runtime, dict):
        fail(f"runtime evidence missing: {candidate_id}")
    if family == "moonshine":
        if runtime.get("distribution") != "moonshine-voice" or runtime.get("version") != "0.1.5":
            fail(f"Moonshine runtime identity drift: {candidate_id}")
        expected_arch = 4 if candidate_id == "moonshine-compact" else 5
        if runtime.get("model_arch") != expected_arch or runtime.get("model_asset_root") != "quantized_26_08_21":
            fail(f"Moonshine model runtime identity drift: {candidate_id}")
        if runtime.get("source_repository") != "moonshine-ai/moonshine":
            fail(f"Moonshine source repository identity drift: {candidate_id}")
        if runtime.get("source_revision") != expected_revision:
            fail(f"Moonshine source-built runtime revision drift: {candidate_id}")
        if runtime.get("runtime_origin") != "PINNED_SOURCE_CHECKOUT_BUILD":
            fail(f"Moonshine runtime is not bound to pinned source build: {candidate_id}")
        if runtime.get("build_type") != "Release":
            fail(f"Moonshine source build type drift: {candidate_id}")
        source_tree = runtime.get("source_tree")
        if not isinstance(source_tree, str) or not SHA40.fullmatch(source_tree):
            fail(f"Moonshine source tree identity missing/malformed: {candidate_id}")
        for field in (
            "python_source_manifest_sha256",
            "native_library_sha256",
            "onnxruntime_sha256",
            "cmake_cache_sha256",
        ):
            value = runtime.get(field)
            if not isinstance(value, str) or not SHA256.fullmatch(value):
                fail(f"Moonshine source-build {field} missing/malformed: {candidate_id}")
    elif family == "sherpa-onnx":
        if runtime != {"distribution": "sherpa-onnx", "version": "1.13.7"}:
            fail(f"sherpa runtime identity drift: {candidate_id}")
    elif family == "whisper.cpp":
        if runtime.get("source_revision") != expected_revision:
            fail(f"whisper source revision differs from B1 authority: {candidate_id}")
        for field in ("cli_binary_sha256", "version_output_sha256"):
            value = runtime.get(field)
            if not isinstance(value, str) or not SHA256.fullmatch(value):
                fail(f"whisper runtime {field} missing/malformed: {candidate_id}")
    else:
        fail(f"unexpected runtime family: {family}")


def verify_execution(candidate_id: str, family: str, cell: dict[str, Any]) -> None:
    execution = cell.get("execution")
    if not isinstance(execution, dict) or execution.get("decode_completed") is not True:
        fail(f"decode path did not complete: {candidate_id}")
    if family == "moonshine":
        if execution.get("stream_api_executed") is not True:
            fail(f"Moonshine stream execution marker missing: {candidate_id}")
        required_true = (
            "b2r02_streaming_c0_harness_executed",
            "b2r02_static_verifier_executed",
            "b2r02_pinned_upstream_source_verified",
            "b2r02_runtime_built_from_verified_source",
            "b2r02_runtime_imported_from_verified_source_copy",
        )
        for field in required_true:
            if execution.get(field) is not True:
                fail(f"Moonshine B2R02 source/runtime proof missing: {candidate_id}:{field}")
        if execution.get("speech_samples") != 32000:
            fail(f"Moonshine B2R02 speech-sample trace drift: {candidate_id}")
        if execution.get("speech_chunk_samples") != [8000, 8000, 8000, 8000]:
            fail(f"Moonshine B2R02 feed schedule drift: {candidate_id}")
        if execution.get("final_zero_pad_samples") != 10560:
            fail(f"Moonshine B2R02 zero-suffix drift: {candidate_id}")
        if execution.get("sample_rate_hz") != 16000:
            fail(f"Moonshine B2R02 sample-rate drift: {candidate_id}")
        if execution.get("transcription_interval_seconds") != 0.5:
            fail(f"Moonshine B2R02 transcription interval drift: {candidate_id}")
        if execution.get("vad_threshold") != 0.0:
            fail(f"Moonshine B2R02 VAD threshold drift: {candidate_id}")
        if execution.get("repository_context_used") is not False or execution.get("keyterms_used") is not False:
            fail(f"Moonshine B2R02 bias guard drift: {candidate_id}")
        if execution.get("transcript_text_retained") is not False:
            fail(f"Moonshine B2R02 transcript retention drift: {candidate_id}")
    elif family == "sherpa-onnx":
        if execution.get("online_transducer_api_executed") is not True:
            fail(f"sherpa online transducer execution marker missing: {candidate_id}")
        decode_steps = execution.get("decode_steps")
        if not isinstance(decode_steps, int) or decode_steps <= 0 or decode_steps > 10000:
            fail(f"sherpa decode-step evidence malformed: {candidate_id}")
    elif family == "whisper.cpp":
        if execution.get("whisper_cli_executed") is not True or execution.get("exit_code") != 0:
            fail(f"whisper CLI execution marker missing/failed: {candidate_id}")
        if execution.get("captured_output_retained") is not False:
            fail(f"whisper transcript-retention boundary drift: {candidate_id}")
    else:
        fail(f"unexpected execution family: {family}")


def verify(evidence_path: Path = EVIDENCE, expected_workflow: dict[str, Any] | None = None) -> None:
    evidence = load(evidence_path)
    workflow_authority = EXPECTED_WORKFLOW if expected_workflow is None else expected_workflow
    if evidence.get("schema_version") != "000b2-operational-smoke-evidence-v1":
        fail("aggregate smoke schema drift")
    if evidence.get("purpose") != "B2_ENTRY_OPERATIONAL_QUALIFICATION_NON_PRIMARY":
        fail("aggregate smoke purpose drift")
    if evidence.get("source_workflow") != workflow_authority:
        fail("aggregate smoke workflow provenance drift")
    for field in (
        "primary_test_decoding_performed",
        "human_speech_used",
        "comparative_ranking_present",
        "accuracy_scoring_performed",
        "performance_claim_present",
    ):
        if evidence.get(field) is not False:
            fail(f"aggregate smoke violates non-primary boundary: {field}")

    qualification = evidence.get("qualification")
    if not isinstance(qualification, dict):
        fail("qualification record missing")
    if qualification.get("status") != "SMOKE_PASS":
        fail("aggregate smoke is not PASS")
    if qualification.get("candidate_count") != 6:
        fail("aggregate smoke candidate count drift")
    candidate_ids = qualification.get("candidate_ids")
    if not isinstance(candidate_ids, list) or len(candidate_ids) != 6 or set(candidate_ids) != set(EXPECTED_CELLS):
        fail("aggregate smoke candidate allowlist drift")
    if qualification.get("synthetic_input_sha256") != EXPECTED_SYNTHETIC_SHA:
        fail("aggregate synthetic input digest drift")

    if evidence.get("evidence_payload_sha256") != digest_without(evidence, "evidence_payload_sha256"):
        fail("aggregate evidence payload digest mismatch")

    expected = expected_artifacts()
    runtime_revisions = expected_runtime_revisions()
    cells = evidence.get("candidate_evidence")
    if not isinstance(cells, list) or len(cells) != 6:
        fail("candidate evidence must contain exactly six cells")
    seen: set[str] = set()
    moonshine_build_identity: dict[str, Any] | None = None
    for cell in cells:
        if not isinstance(cell, dict):
            fail("candidate evidence cell must be an object")
        candidate_id = cell.get("candidate_id")
        if candidate_id not in EXPECTED_CELLS or candidate_id in seen:
            fail(f"unexpected or duplicate candidate evidence: {candidate_id}")
        seen.add(candidate_id)
        family, tier = EXPECTED_CELLS[candidate_id]
        if cell.get("family") != family or cell.get("tier") != tier:
            fail(f"candidate identity/tier drift: {candidate_id}")
        if cell.get("schema_version") != "000b2-operational-smoke-cell-v1":
            fail(f"cell schema drift: {candidate_id}")
        if cell.get("purpose") != "B2_ENTRY_OPERATIONAL_QUALIFICATION_NON_PRIMARY":
            fail(f"cell purpose drift: {candidate_id}")
        if cell.get("status") != "SMOKE_PASS":
            fail(f"cell smoke is not PASS: {candidate_id}")
        for field in (
            "primary_test_decoding_performed",
            "human_speech_used",
            "comparative_ranking_present",
            "accuracy_scoring_performed",
            "performance_claim_present",
            "transcript_text_retained",
            "repository_context_used",
        ):
            if cell.get(field) is not False:
                fail(f"{candidate_id} violates non-primary boundary: {field}")
        synthetic = cell.get("synthetic_input")
        if not isinstance(synthetic, dict):
            fail(f"synthetic input missing: {candidate_id}")
        if synthetic != {
            "channels": 1,
            "generator": "wispral-deterministic-multitone-v1",
            "sample_format": "PCM_S16LE",
            "sample_rate_hz": 16000,
            "samples": 32000,
            "sha256": EXPECTED_SYNTHETIC_SHA,
            "synthetic_non_speech": True,
        }:
            fail(f"synthetic input contract drift: {candidate_id}")
        if cell.get("evidence_payload_sha256") != digest_without(cell, "evidence_payload_sha256"):
            fail(f"cell evidence payload digest mismatch: {candidate_id}")

        artifacts = cell.get("artifacts")
        if not isinstance(artifacts, list):
            fail(f"artifact evidence missing: {candidate_id}")
        observed: dict[str, tuple[int, str]] = {}
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                fail(f"malformed artifact evidence: {candidate_id}")
            path = artifact.get("path")
            digest = artifact.get("sha256")
            size = artifact.get("size_bytes")
            if not isinstance(path, str) or path in observed:
                fail(f"duplicate/missing artifact path: {candidate_id}")
            if not isinstance(size, int) or size <= 0:
                fail(f"invalid artifact size: {candidate_id}:{path}")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                fail(f"invalid artifact SHA-256: {candidate_id}:{path}")
            observed[path] = (size, digest)
        if observed != expected[candidate_id]:
            fail(f"artifact evidence differs from preregistered/materialized authority: {candidate_id}")

        verify_runtime(candidate_id, family, cell, runtime_revisions[family])
        verify_execution(candidate_id, family, cell)
        if family == "moonshine":
            runtime = cell["runtime"]
            identity = {
                key: runtime[key]
                for key in (
                    "source_repository",
                    "source_revision",
                    "source_tree",
                    "runtime_origin",
                    "python_source_manifest_sha256",
                    "native_library_sha256",
                    "onnxruntime_sha256",
                    "cmake_cache_sha256",
                    "build_type",
                )
            }
            if moonshine_build_identity is None:
                moonshine_build_identity = identity
            elif identity != moonshine_build_identity:
                fail("Moonshine compact/balanced source-build identity differs")

    if seen != set(EXPECTED_CELLS):
        fail("six-cell smoke allowlist incomplete")
    if moonshine_build_identity is None:
        fail("Moonshine source-build aggregate identity missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--expected-head-sha")
    parser.add_argument("--expected-run-id", type=int)
    parser.add_argument("--expected-run-number", type=int)
    args = parser.parse_args()
    dynamic = any(
        value is not None
        for value in (
            args.evidence,
            args.expected_head_sha,
            args.expected_run_id,
            args.expected_run_number,
        )
    )
    if dynamic and not all(
        value is not None
        for value in (
            args.evidence,
            args.expected_head_sha,
            args.expected_run_id,
            args.expected_run_number,
        )
    ):
        parser.error("fresh aggregate verification requires evidence, head SHA, run id, and run number")

    evidence_path = EVIDENCE
    expected_workflow = None
    if dynamic:
        if not SHA40.fullmatch(args.expected_head_sha):
            parser.error("--expected-head-sha must be a full lowercase Git SHA")
        evidence_path = args.evidence
        expected_workflow = {
            "name": "000B2 Operational Smoke",
            "head_sha": args.expected_head_sha,
            "run_id": args.expected_run_id,
            "run_number": args.expected_run_number,
        }
    try:
        verify(evidence_path, expected_workflow)
    except (AssertionError, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"VERIFY_000B2_OPERATIONAL_SMOKE=FAIL: {exc}", file=sys.stderr)
        return 1
    print("VERIFY_000B2_OPERATIONAL_SMOKE=PASS")
    print("CANDIDATES=6")
    print("OPERATIONAL_QUALIFICATION=SMOKE_PASS")
    print("PRIMARY_TEST_DECODING=NO")
    print("HUMAN_SPEECH=NO")
    print("COMPARATIVE_RANKING=NO")
    print("ACCURACY_SCORING=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
