#!/usr/bin/env python3
"""Fail-closed verifier for durable B2 non-primary operational smoke evidence."""

from __future__ import annotations

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


def verify() -> None:
    evidence = load(EVIDENCE)
    if evidence.get("schema_version") != "000b2-operational-smoke-evidence-v1":
        fail("aggregate smoke schema drift")
    if evidence.get("purpose") != "B2_ENTRY_OPERATIONAL_QUALIFICATION_NON_PRIMARY":
        fail("aggregate smoke purpose drift")
    if evidence.get("source_workflow") != EXPECTED_WORKFLOW:
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
    if set(qualification.get("candidate_ids", [])) != set(EXPECTED_CELLS):
        fail("aggregate smoke candidate allowlist drift")
    if qualification.get("synthetic_input_sha256") != EXPECTED_SYNTHETIC_SHA:
        fail("aggregate synthetic input digest drift")

    if evidence.get("evidence_payload_sha256") != digest_without(evidence, "evidence_payload_sha256"):
        fail("aggregate evidence payload digest mismatch")

    expected = expected_artifacts()
    cells = evidence.get("candidate_evidence")
    if not isinstance(cells, list) or len(cells) != 6:
        fail("candidate evidence must contain exactly six cells")
    seen: set[str] = set()
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

        runtime_revision = cell.get("runtime_revision")
        if not isinstance(runtime_revision, str) or not SHA40.fullmatch(runtime_revision):
            fail(f"runtime revision malformed: {candidate_id}")
        execution = cell.get("execution")
        if not isinstance(execution, dict) or execution.get("decode_completed") is not True:
            fail(f"decode path did not complete: {candidate_id}")

    if seen != set(EXPECTED_CELLS):
        fail("six-cell smoke allowlist incomplete")


def main() -> int:
    try:
        verify()
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
