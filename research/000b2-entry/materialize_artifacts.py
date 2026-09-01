#!/usr/bin/env python3
"""Materialize B1-qualified artifacts whose SHA-256 remained pending.

This is a non-decoding B2 entry-preparation tool. It downloads exact preregistered
payloads, verifies byte size, computes SHA-256, and emits a JSON evidence report.
A narrowly scoped pre-attempt amendment may correct discovered metadata without
rewriting the historical B1 registry. It does not load models or inspect primary
audio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "research" / "000b1" / "qualified-candidates.json"
AMENDMENT = ROOT / "research" / "000b2-entry" / "artifact-size-amendment.json"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def correction_map(amendment: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    if amendment.get("schema_version") != "000b2-entry-artifact-amendment-v1":
        raise RuntimeError("artifact-size amendment schema drift")
    if amendment.get("status") != "PRE_ATTEMPT_CORRECTION":
        raise RuntimeError("artifact-size amendment is not pre-attempt")
    if amendment.get("primary_test_decoding_performed") is not False:
        raise RuntimeError("artifact-size amendment cannot follow primary decoding")
    if amendment.get("comparative_ranking_present") is not False:
        raise RuntimeError("artifact-size amendment cannot follow comparative ranking")
    corrections = amendment.get("corrections")
    if not isinstance(corrections, list) or not corrections:
        raise RuntimeError("artifact-size amendment corrections missing")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for correction in corrections:
        if not isinstance(correction, dict):
            raise RuntimeError("artifact-size correction must be an object")
        key = (str(correction.get("candidate_id")), str(correction.get("path")))
        if key in result:
            raise RuntimeError(f"duplicate artifact-size correction: {key}")
        result[key] = correction
    return result


def pending_entries(registry: dict[str, Any]):
    for family in registry["families"]:
        family_name = family["family"]
        for cfg in family["configurations"]:
            for artifact in cfg["artifacts"]:
                if artifact.get("sha256") is not None:
                    continue
                if family_name == "moonshine":
                    url = f"{cfg['artifact_base_url'].rstrip('/')}/{artifact['path']}"
                elif family_name == "sherpa-onnx":
                    source_revision = artifact.get("source_revision")
                    if not source_revision:
                        raise RuntimeError(f"missing source revision for {cfg['id']}:{artifact['path']}")
                    base = family["model_source"]["base_url"].rstrip("/")
                    url = f"{base}/{source_revision}/{artifact['path']}"
                else:
                    raise RuntimeError(f"unsupported pending-artifact family: {family_name}")
                yield family_name, cfg, artifact, url


def effective_size(
    candidate_id: str,
    artifact: dict[str, Any],
    corrections: dict[tuple[str, str], dict[str, Any]],
    used: set[tuple[str, str]],
) -> int:
    historical = artifact["size_bytes"]
    key = (candidate_id, artifact["path"])
    correction = corrections.get(key)
    if correction is None:
        return historical
    if correction.get("historical_b1_size_bytes") != historical:
        raise RuntimeError(f"amendment historical size does not match B1 registry for {key}")
    if correction.get("source_revision") != artifact.get("source_revision"):
        raise RuntimeError(f"amendment source revision does not match B1 registry for {key}")
    corrected = correction.get("b2_entry_size_bytes")
    if not isinstance(corrected, int) or corrected <= 0:
        raise RuntimeError(f"invalid corrected B2 entry size for {key}")
    used.add(key)
    return corrected


def download(url: str, destination: Path, expected_size: int) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Wispral-000B2-entry-materializer/1"})
    h = hashlib.sha256()
    observed = 0
    try:
        with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as out:
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    declared = int(content_length)
                except ValueError as exc:
                    raise RuntimeError(f"invalid Content-Length from {url}: {content_length!r}") from exc
                if declared > expected_size:
                    raise RuntimeError(
                        f"declared artifact size exceeds expected size for {url}: "
                        f"expected {expected_size}, declared {declared}"
                    )
            while True:
                chunk = response.read(min(1024 * 1024, expected_size - observed + 1))
                if not chunk:
                    break
                observed += len(chunk)
                if observed > expected_size:
                    raise RuntimeError(
                        f"artifact exceeded expected size while downloading {url}: "
                        f"expected {expected_size}, observed > {expected_size}"
                    )
                out.write(chunk)
                h.update(chunk)
        if observed != expected_size:
            raise RuntimeError(
                f"artifact size mismatch for {url}: expected {expected_size}, observed {observed}"
            )
        return observed, h.hexdigest()
    finally:
        if destination.exists():
            destination.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path(".materialized-000b2"))
    args = parser.parse_args()

    registry = load_json(REGISTRY)
    amendment = load_json(AMENDMENT)
    corrections = correction_map(amendment)
    used_corrections: set[tuple[str, str]] = set()
    args.work_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for family_name, cfg, artifact, url in pending_entries(registry):
        expected_size = effective_size(cfg["id"], artifact, corrections, used_corrections)
        safe = f"{cfg['id']}--{artifact['path'].replace('/', '__')}"
        destination = args.work_dir / safe
        observed_size, sha256 = download(url, destination, expected_size)
        rows.append(
            {
                "candidate_id": cfg["id"],
                "family": family_name,
                "tier": cfg["tier"],
                "path": artifact["path"],
                "source_url": url,
                "source_revision": artifact.get("source_revision"),
                "historical_b1_size_bytes": artifact["size_bytes"],
                "expected_size_bytes": expected_size,
                "observed_size_bytes": observed_size,
                "sha256": sha256,
                "registry_sha256_status": artifact.get("sha256_status"),
                "pre_attempt_size_amended": expected_size != artifact["size_bytes"],
            }
        )

    if used_corrections != set(corrections):
        unused = sorted(set(corrections) - used_corrections)
        raise RuntimeError(f"unused or non-pending artifact-size amendments: {unused}")

    report: dict[str, Any] = {
        "schema_version": "000b2-materialization-v1",
        "purpose": "B2_ENTRY_PREPARATION_NON_DECODING",
        "primary_test_decoding_performed": False,
        "comparative_ranking_present": False,
        "registry_path": str(REGISTRY.relative_to(ROOT)),
        "registry_sha256": file_sha256(REGISTRY),
        "amendment_path": str(AMENDMENT.relative_to(ROOT)),
        "amendment_sha256": file_sha256(AMENDMENT),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "artifacts": sorted(rows, key=lambda row: (row["candidate_id"], row["path"])),
    }
    canonical = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    report["report_payload_sha256"] = bytes_sha256(canonical)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"MATERIALIZED_PENDING_ARTIFACTS={len(rows)}")
    print(f"PRE_ATTEMPT_SIZE_CORRECTIONS={len(used_corrections)}")
    print("PRIMARY_TEST_DECODING=NO")
    print("COMPARATIVE_RANKING=NO")
    print(f"REPORT={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())