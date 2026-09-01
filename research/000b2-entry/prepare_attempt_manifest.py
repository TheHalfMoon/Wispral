#!/usr/bin/env python3
"""Generate a non-frozen B2 entry manifest from canonical B1 authority and entry evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B1 = ROOT / "research" / "000b1"
HERE = ROOT / "research" / "000b2-entry"
DRAFT = B1 / "examples" / "draft-attempt-manifest.json"
MATERIALIZED = HERE / "materialized-artifacts.json"
SMOKE_EVIDENCE = HERE / "operational-smoke-evidence.json"
SCORER_CONFIG = HERE / "scorer-config.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_CANDIDATES = {
    "moonshine-compact",
    "moonshine-balanced",
    "whispercpp-compact",
    "whispercpp-balanced",
    "sherpa-onnx-compact",
    "sherpa-onnx-balanced",
}

sys.path.insert(0, str(HERE))
from validate_entry_manifest import validate_entry  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_smoke_cells() -> dict[str, dict]:
    evidence = load(SMOKE_EVIDENCE)
    if not isinstance(evidence, dict):
        raise SystemExit("operational smoke evidence must be a JSON object")
    qualification = evidence.get("qualification")
    if not isinstance(qualification, dict) or qualification.get("status") != "SMOKE_PASS":
        raise SystemExit("operational smoke aggregate is not SMOKE_PASS")
    cells = evidence.get("candidate_evidence")
    if not isinstance(cells, list):
        raise SystemExit("operational smoke candidate evidence must be an array")
    result: dict[str, dict] = {}
    for cell in cells:
        if not isinstance(cell, dict):
            raise SystemExit("operational smoke cell must be an object")
        candidate_id = cell.get("candidate_id")
        digest = cell.get("evidence_payload_sha256")
        if candidate_id not in EXPECTED_CANDIDATES or candidate_id in result:
            raise SystemExit(f"unexpected or duplicate operational smoke candidate: {candidate_id}")
        if cell.get("status") != "SMOKE_PASS" or cell.get("execution", {}).get("decode_completed") is not True:
            raise SystemExit(f"operational smoke cell is not a completed PASS: {candidate_id}")
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
                raise SystemExit(f"operational smoke cell violates non-primary boundary: {candidate_id}:{field}")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise SystemExit(f"operational smoke evidence digest malformed: {candidate_id}")
        result[candidate_id] = cell
    if set(result) != EXPECTED_CANDIDATES:
        raise SystemExit("operational smoke evidence does not cover the exact six-cell allowlist")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-revision", required=True)
    parser.add_argument("--scorer-revision")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not SHA40.fullmatch(args.canonical_revision):
        raise SystemExit("--canonical-revision must be a 40-hex Git SHA")
    if args.scorer_revision is not None and not SHA40.fullmatch(args.scorer_revision):
        raise SystemExit("--scorer-revision must be a 40-hex Git SHA")

    manifest = load(DRAFT)
    evidence = load(MATERIALIZED)
    smoke_cells = verified_smoke_cells()
    if not isinstance(manifest, dict) or not isinstance(evidence, dict):
        raise SystemExit("draft/evidence must be JSON objects")

    manifest["attempt_id"] = "B2-ENTRY-DRAFT-NOT-AUTHORIZED"
    manifest["canonical_wispral_revision"] = args.canonical_revision
    manifest["qualified_candidates_sha256"] = file_sha256(B1 / "qualified-candidates.json")
    manifest["frozen_methodology_sha256"] = file_sha256(B1 / "frozen-methodology.json")
    manifest["frozen"] = False
    manifest["freeze_digest_sha256"] = None
    manifest["primary_test_decoding_started"] = False

    materialized = {}
    for candidate_id, paths in evidence["artifacts"].items():
        for path, row in paths.items():
            materialized[(candidate_id, path)] = row

    seen = set()
    for candidate in manifest["candidates"]:
        candidate_id = candidate["candidate_id"]
        for artifact in candidate["artifacts"]:
            key = (candidate_id, artifact["path"])
            row = materialized.get(key)
            if row is not None:
                artifact["size_bytes"] = row["size_bytes"]
                artifact["sha256"] = row["sha256"]
                seen.add(key)
        cell = smoke_cells[candidate_id]
        candidate["operational_qualification"] = {
            "status": "SMOKE_PASS",
            "evidence_sha256": cell["evidence_payload_sha256"],
            "canonical_waiver_revision": None,
        }
    if seen != set(materialized):
        missing = sorted(set(materialized) - seen)
        raise SystemExit(f"materialized evidence not represented in B1 draft: {missing}")

    manifest["scorer"]["config_sha256"] = file_sha256(SCORER_CONFIG)
    manifest["scorer"]["revision"] = args.scorer_revision
    manifest["claims"]["comparative_performance_authorized"] = False
    manifest["claims"]["human_developer_speech_ranking_authorized"] = False
    manifest["corpus"]["synthetic_primary_ranking"] = False

    errors, blockers = validate_entry(manifest, require_ready=False)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("ENTRY_MANIFEST_DRAFT=PASS")
    print("OPERATIONAL_QUALIFICATION=SMOKE_PASS")
    print("FROZEN=NO")
    print("PRIMARY_TEST_DECODING=NO")
    print("HUMAN_RANKING_AUTHORIZED=NO")
    for blocker in blockers:
        print(f"BLOCKER={blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())