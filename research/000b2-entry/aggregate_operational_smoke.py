#!/usr/bin/env python3
"""Aggregate and fail-closed verify all six non-primary operational smoke cells."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from verify_operational_smoke import expected_artifacts, verify as verify_aggregate

EXPECTED = {
    "moonshine-compact": ("moonshine", "COMPACT"),
    "moonshine-balanced": ("moonshine", "BALANCED"),
    "whispercpp-compact": ("whisper.cpp", "COMPACT"),
    "whispercpp-balanced": ("whisper.cpp", "BALANCED"),
    "sherpa-onnx-compact": ("sherpa-onnx", "COMPACT"),
    "sherpa-onnx-balanced": ("sherpa-onnx", "BALANCED"),
}
CELL_SCHEMA = "000b2-operational-smoke-cell-v1"
AGGREGATE_SCHEMA = "000b2-operational-smoke-evidence-v1"
EXPECTED_SYNTHETIC = {
    "channels": 1,
    "generator": "wispral-deterministic-multitone-v1",
    "sample_format": "PCM_S16LE",
    "sample_rate_hz": 16000,
    "samples": 32000,
    "sha256": "860debf008a4702098968ca7b113ea8df7ee0188c9ca08c7c1e9437466876c38",
    "synthetic_non_speech": True,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_digest(obj: dict[str, Any], field: str) -> str:
    clone = dict(obj)
    clone.pop(field, None)
    raw = (json.dumps(clone, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return sha256_bytes(raw)


def require_execution(candidate_id: str, family: str, cell: dict[str, Any]) -> None:
    execution = cell.get("execution")
    if not isinstance(execution, dict) or execution.get("decode_completed") is not True:
        raise RuntimeError(f"decode path did not complete for {candidate_id}")
    if family == "moonshine":
        if execution.get("stream_api_executed") is not True:
            raise RuntimeError(f"Moonshine stream execution marker missing for {candidate_id}")
    elif family == "sherpa-onnx":
        if execution.get("online_transducer_api_executed") is not True:
            raise RuntimeError(f"sherpa online transducer execution marker missing for {candidate_id}")
    elif family == "whisper.cpp":
        if execution.get("whisper_cli_executed") is not True or execution.get("exit_code") != 0:
            raise RuntimeError(f"whisper CLI execution marker missing/failed for {candidate_id}")
    else:
        raise RuntimeError(f"unexpected family: {family}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cells: dict[str, dict[str, Any]] = {}
    for path in sorted(args.input_dir.rglob("*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(obj, dict) or obj.get("schema_version") != CELL_SCHEMA:
            continue
        candidate_id = obj.get("candidate_id")
        if candidate_id in cells:
            raise RuntimeError(f"duplicate smoke evidence for {candidate_id}")
        cells[candidate_id] = obj

    if set(cells) != set(EXPECTED):
        missing = sorted(set(EXPECTED) - set(cells))
        extra = sorted(set(cells) - set(EXPECTED))
        raise RuntimeError(f"smoke candidate set mismatch: missing={missing}, extra={extra}")

    frozen_artifacts = expected_artifacts()
    normalized: list[dict[str, Any]] = []
    for candidate_id in sorted(cells):
        cell = cells[candidate_id]
        family, tier = EXPECTED[candidate_id]
        if cell.get("family") != family or cell.get("tier") != tier:
            raise RuntimeError(f"identity/tier drift for {candidate_id}")
        if cell.get("status") != "SMOKE_PASS":
            raise RuntimeError(f"smoke did not pass for {candidate_id}")
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
                raise RuntimeError(f"{candidate_id} violates non-primary boundary: {field}")
        if cell.get("synthetic_input") != EXPECTED_SYNTHETIC:
            raise RuntimeError(f"{candidate_id} synthetic input differs from frozen smoke identity")
        expected_payload = payload_digest(cell, "evidence_payload_sha256")
        if cell.get("evidence_payload_sha256") != expected_payload:
            raise RuntimeError(f"{candidate_id} evidence payload digest mismatch")

        artifacts = cell.get("artifacts")
        if not isinstance(artifacts, list):
            raise RuntimeError(f"{candidate_id} artifact evidence missing")
        observed: dict[str, tuple[int, str]] = {}
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise RuntimeError(f"{candidate_id} malformed artifact evidence")
            path = artifact.get("path")
            digest = artifact.get("sha256")
            size = artifact.get("size_bytes")
            if not isinstance(path, str) or path in observed:
                raise RuntimeError(f"{candidate_id} duplicate/missing artifact path")
            if not isinstance(digest, str) or len(digest) != 64:
                raise RuntimeError(f"{candidate_id}:{path} SHA-256 malformed")
            if not isinstance(size, int) or size <= 0:
                raise RuntimeError(f"{candidate_id}:{path} size invalid")
            observed[path] = (size, digest)
        if observed != frozen_artifacts[candidate_id]:
            raise RuntimeError(f"{candidate_id} artifacts differ from frozen/materialized authority")
        require_execution(candidate_id, family, cell)
        normalized.append(cell)

    report: dict[str, Any] = {
        "schema_version": AGGREGATE_SCHEMA,
        "purpose": "B2_ENTRY_OPERATIONAL_QUALIFICATION_NON_PRIMARY",
        "source_workflow": {
            "name": "000B2 Operational Smoke",
            "head_sha": os.environ.get("GITHUB_SHA"),
            "run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
            "run_number": int(os.environ["GITHUB_RUN_NUMBER"]) if os.environ.get("GITHUB_RUN_NUMBER") else None,
        },
        "qualification": {
            "status": "SMOKE_PASS",
            "candidate_count": len(normalized),
            "candidate_ids": sorted(cells),
            "synthetic_input_sha256": EXPECTED_SYNTHETIC["sha256"],
        },
        "primary_test_decoding_performed": False,
        "human_speech_used": False,
        "comparative_ranking_present": False,
        "accuracy_scoring_performed": False,
        "performance_claim_present": False,
        "candidate_evidence": normalized,
    }
    raw = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    report["evidence_payload_sha256"] = sha256_bytes(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    workflow = report["source_workflow"]
    if not isinstance(workflow.get("head_sha"), str) or workflow.get("run_id") is None or workflow.get("run_number") is None:
        raise RuntimeError("workflow provenance is incomplete; aggregate publication is forbidden")
    verify_aggregate(args.output, workflow)

    print("OPERATIONAL_SMOKE=PASS")
    print("AGGREGATE_VERIFICATION=PASS")
    print("CANDIDATES=6")
    print("PRIMARY_TEST_DECODING=NO")
    print("HUMAN_SPEECH=NO")
    print("COMPARATIVE_RANKING=NO")
    print("ACCURACY_SCORING=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
