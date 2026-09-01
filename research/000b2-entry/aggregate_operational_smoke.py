#!/usr/bin/env python3
"""Aggregate and fail-closed verify all six non-primary operational smoke cells."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_digest(obj: dict[str, Any], field: str) -> str:
    clone = dict(obj)
    clone.pop(field, None)
    raw = (json.dumps(clone, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return sha256_bytes(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cells: dict[str, dict[str, Any]] = {}
    for path in sorted(args.input_dir.rglob("*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        if obj.get("schema_version") != CELL_SCHEMA:
            continue
        candidate_id = obj.get("candidate_id")
        if candidate_id in cells:
            raise RuntimeError(f"duplicate smoke evidence for {candidate_id}")
        cells[candidate_id] = obj

    if set(cells) != set(EXPECTED):
        missing = sorted(set(EXPECTED) - set(cells))
        extra = sorted(set(cells) - set(EXPECTED))
        raise RuntimeError(f"smoke candidate set mismatch: missing={missing}, extra={extra}")

    synthetic_digests: set[str] = set()
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
        synthetic = cell.get("synthetic_input")
        if not isinstance(synthetic, dict) or synthetic.get("synthetic_non_speech") is not True:
            raise RuntimeError(f"{candidate_id} lacks synthetic non-speech attestation")
        digest = synthetic.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise RuntimeError(f"{candidate_id} synthetic digest malformed")
        synthetic_digests.add(digest)
        expected_payload = payload_digest(cell, "evidence_payload_sha256")
        if cell.get("evidence_payload_sha256") != expected_payload:
            raise RuntimeError(f"{candidate_id} evidence payload digest mismatch")
        artifacts = cell.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise RuntimeError(f"{candidate_id} artifact evidence missing")
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise RuntimeError(f"{candidate_id} malformed artifact evidence")
            digest = artifact.get("sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                raise RuntimeError(f"{candidate_id}:{artifact.get('path')} SHA-256 malformed")
            if not isinstance(artifact.get("size_bytes"), int) or artifact["size_bytes"] <= 0:
                raise RuntimeError(f"{candidate_id}:{artifact.get('path')} size invalid")
        normalized.append(cell)

    if len(synthetic_digests) != 1:
        raise RuntimeError("all candidates must use byte-identical synthetic smoke WAV")

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
            "synthetic_input_sha256": next(iter(synthetic_digests)),
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
    print("OPERATIONAL_SMOKE=PASS")
    print("CANDIDATES=6")
    print("PRIMARY_TEST_DECODING=NO")
    print("HUMAN_SPEECH=NO")
    print("COMPARATIVE_RANKING=NO")
    print("ACCURACY_SCORING=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
