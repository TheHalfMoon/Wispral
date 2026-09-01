#!/usr/bin/env python3
"""Verify durable and optional live B2 entry materialization evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "research" / "000b1" / "qualified-candidates.json"
AMENDMENT = ROOT / "research" / "000b2-entry" / "artifact-size-amendment.json"
EVIDENCE = ROOT / "research" / "000b2-entry" / "materialized-artifacts.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must be a JSON object")
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def correction_map(amendment: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    if amendment.get("schema_version") != "000b2-entry-artifact-amendment-v1":
        raise AssertionError("amendment schema drift")
    if amendment.get("status") != "PRE_ATTEMPT_CORRECTION":
        raise AssertionError("amendment status drift")
    if amendment.get("primary_test_decoding_performed") is not False:
        raise AssertionError("amendment follows primary decoding")
    rows = amendment.get("corrections")
    if not isinstance(rows, list) or len(rows) != 2:
        raise AssertionError("expected exactly two tokens.txt size corrections")
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise AssertionError("correction must be object")
        key = (row.get("candidate_id"), row.get("path"))
        if key in result:
            raise AssertionError("duplicate correction")
        result[key] = row
    expected_keys = {
        ("sherpa-onnx-compact", "tokens.txt"),
        ("sherpa-onnx-balanced", "tokens.txt"),
    }
    if set(result) != expected_keys:
        raise AssertionError("artifact-size amendment scope drift")
    for key, row in result.items():
        if row.get("source_revision") != "6037ea07e3abfe599ad00d418968bcf9656e7472":
            raise AssertionError(f"source revision drift for {key}")
        if row.get("historical_b1_size_bytes") != 5050 or row.get("b2_entry_size_bytes") != 5048:
            raise AssertionError(f"size amendment drift for {key}")
    return result


def expected_pending(registry: dict[str, Any], corrections: dict[tuple[str, str], dict[str, Any]]):
    expected: dict[tuple[str, str], dict[str, Any]] = {}
    for family in registry["families"]:
        family_name = family["family"]
        for cfg in family["configurations"]:
            for artifact in cfg["artifacts"]:
                if artifact.get("sha256") is not None:
                    continue
                key = (cfg["id"], artifact["path"])
                size = artifact["size_bytes"]
                correction = corrections.get(key)
                amended = correction is not None
                if correction:
                    if correction["historical_b1_size_bytes"] != size:
                        raise AssertionError(f"amendment historical size mismatch for {key}")
                    if correction["source_revision"] != artifact.get("source_revision"):
                        raise AssertionError(f"amendment source revision mismatch for {key}")
                    size = correction["b2_entry_size_bytes"]
                if family_name == "moonshine":
                    source_url = f"{cfg['artifact_base_url'].rstrip('/')}/{artifact['path']}"
                elif family_name == "sherpa-onnx":
                    source_url = (
                        f"{family['model_source']['base_url'].rstrip('/')}/"
                        f"{artifact['source_revision']}/{artifact['path']}"
                    )
                else:
                    raise AssertionError(f"unexpected pending family {family_name}")
                expected[key] = {
                    "size_bytes": size,
                    "source_revision": artifact.get("source_revision"),
                    "source_url": source_url,
                    "pre_attempt_size_amended": amended,
                }
    return expected


def flattened_evidence(evidence: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result = {}
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, dict):
        raise AssertionError("materialized artifacts mapping missing")
    for candidate_id, paths in artifacts.items():
        if not isinstance(paths, dict):
            raise AssertionError(f"candidate evidence not a mapping: {candidate_id}")
        for path, row in paths.items():
            if not isinstance(row, dict):
                raise AssertionError(f"artifact evidence not a mapping: {candidate_id}:{path}")
            result[(candidate_id, path)] = row
    return result


def verify_static() -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    registry = load(REGISTRY)
    amendment = load(AMENDMENT)
    evidence = load(EVIDENCE)
    corrections = correction_map(amendment)
    expected = expected_pending(registry, corrections)

    if evidence.get("schema_version") != "000b2-materialized-artifacts-v1":
        raise AssertionError("materialization evidence schema drift")
    if evidence.get("purpose") != "B2_ENTRY_PREPARATION_NON_DECODING":
        raise AssertionError("materialization purpose drift")
    if evidence.get("primary_test_decoding_performed") is not False:
        raise AssertionError("materialization evidence implies primary decoding")
    if evidence.get("comparative_ranking_present") is not False:
        raise AssertionError("materialization evidence implies comparative ranking")
    if evidence.get("registry_sha256") != file_sha256(REGISTRY):
        raise AssertionError("materialization evidence registry digest drift")
    if evidence.get("amendment_sha256") != file_sha256(AMENDMENT):
        raise AssertionError("materialization evidence amendment digest drift")

    workflow = evidence.get("source_workflow")
    if workflow != {
        "conclusion": "success",
        "head_sha": "3d4325b7c9b13e6696326f3d2c8a6cfe501d9e12",
        "name": "000B2 Entry Materialization",
        "raw_report_payload_sha256": "9baba4058dd700d0975adc4588a5eaddcf9e3fefc29bd158fc3341984cc33042",
        "run_id": 33519579512,
        "run_number": 3,
        "uploaded_artifact_id": 9805070727,
        "uploaded_artifact_zip_sha256": "27fe1819696e56c8b31d25b5fe9618aab7ee566c3db700e259c41a1103762c08",
    }:
        raise AssertionError("source workflow evidence drift")

    actual = flattened_evidence(evidence)
    if set(actual) != set(expected):
        raise AssertionError(f"materialized pending set drift: expected {len(expected)}, got {len(actual)}")
    if len(actual) != 18:
        raise AssertionError("expected exactly 18 pending artifact records")
    for key, wanted in expected.items():
        row = actual[key]
        for field, value in wanted.items():
            if row.get(field) != value:
                raise AssertionError(f"{key} {field} drift")
        if not isinstance(row.get("sha256"), str) or not SHA256.fullmatch(row["sha256"]):
            raise AssertionError(f"{key} SHA-256 missing/malformed")

    if actual[("sherpa-onnx-compact", "tokens.txt")]["sha256"] != "49e3c2646595fd907228b3c6787069658f67b17377c60aeb8619c4551b2316fb":
        raise AssertionError("sherpa tokens.txt SHA-256 drift")
    if actual[("sherpa-onnx-balanced", "tokens.txt")]["sha256"] != actual[("sherpa-onnx-compact", "tokens.txt")]["sha256"]:
        raise AssertionError("shared sherpa tokens.txt payload differs by tier")
    if actual[("moonshine-compact", "tokenizer.bin")]["sha256"] != actual[("moonshine-balanced", "tokenizer.bin")]["sha256"]:
        raise AssertionError("shared Moonshine tokenizer differs by tier")
    return actual, evidence


def verify_live_report(path: Path, committed: dict[tuple[str, str], dict[str, Any]]) -> None:
    live = load(path)
    if live.get("schema_version") != "000b2-materialization-v1":
        raise AssertionError("live materialization report schema drift")
    if live.get("primary_test_decoding_performed") is not False or live.get("comparative_ranking_present") is not False:
        raise AssertionError("live materialization crossed non-decoding boundary")
    payload_digest = live.get("report_payload_sha256")
    if not isinstance(payload_digest, str) or not SHA256.fullmatch(payload_digest):
        raise AssertionError("live report payload digest missing")
    digest_input = dict(live)
    digest_input.pop("report_payload_sha256")
    calculated = hashlib.sha256(
        (json.dumps(digest_input, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    if calculated != payload_digest:
        raise AssertionError("live report payload digest mismatch")

    live_rows = {}
    for row in live.get("artifacts", []):
        key = (row.get("candidate_id"), row.get("path"))
        live_rows[key] = row
    if set(live_rows) != set(committed):
        raise AssertionError("live materialization artifact set differs from committed evidence")
    for key, expected in committed.items():
        row = live_rows[key]
        if row.get("observed_size_bytes") != expected["size_bytes"]:
            raise AssertionError(f"live size drift for {key}")
        if row.get("sha256") != expected["sha256"]:
            raise AssertionError(f"live SHA-256 drift for {key}")
        if row.get("source_url") != expected["source_url"]:
            raise AssertionError(f"live source URL drift for {key}")
        if row.get("source_revision") != expected["source_revision"]:
            raise AssertionError(f"live source revision drift for {key}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-report", type=Path)
    args = parser.parse_args()
    try:
        committed, _ = verify_static()
        if args.live_report:
            verify_live_report(args.live_report, committed)
    except (AssertionError, KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"VERIFY_000B2_MATERIALIZATION=FAIL: {exc}", file=sys.stderr)
        return 1
    print("VERIFY_000B2_MATERIALIZATION=PASS")
    print("MATERIALIZED_ARTIFACT_RECORDS=18")
    print("PRIMARY_TEST_DECODING=NO")
    print("COMPARATIVE_RANKING=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
