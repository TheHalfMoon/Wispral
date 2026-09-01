#!/usr/bin/env python3
"""Materialize only B1-qualified artifacts whose SHA-256 remained pending.

This is a non-decoding B2 entry-preparation tool. It downloads exact preregistered
payloads, verifies byte size, computes SHA-256, and emits a JSON evidence report.
It does not load models or inspect any primary benchmark audio.
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


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def download(url: str, destination: Path) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Wispral-000B2-entry-materializer/1"})
    h = hashlib.sha256()
    observed = 0
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            h.update(chunk)
            observed += len(chunk)
    return observed, h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path(".materialized-000b2"))
    args = parser.parse_args()

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    args.work_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for family_name, cfg, artifact, url in pending_entries(registry):
        safe = f"{cfg['id']}--{artifact['path'].replace('/', '__')}"
        destination = args.work_dir / safe
        observed_size, sha256 = download(url, destination)
        expected_size = artifact["size_bytes"]
        if observed_size != expected_size:
            raise RuntimeError(
                f"size mismatch for {cfg['id']}:{artifact['path']}: "
                f"expected {expected_size}, observed {observed_size}"
            )
        rows.append(
            {
                "candidate_id": cfg["id"],
                "family": family_name,
                "tier": cfg["tier"],
                "path": artifact["path"],
                "source_url": url,
                "source_revision": artifact.get("source_revision"),
                "expected_size_bytes": expected_size,
                "observed_size_bytes": observed_size,
                "sha256": sha256,
                "registry_sha256_status": artifact.get("sha256_status"),
            }
        )
        destination.unlink()

    report: dict[str, Any] = {
        "schema_version": "000b2-materialization-v1",
        "purpose": "B2_ENTRY_PREPARATION_NON_DECODING",
        "primary_test_decoding_performed": False,
        "comparative_ranking_present": False,
        "registry_path": str(REGISTRY.relative_to(ROOT)),
        "registry_sha256": file_sha256(REGISTRY),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "artifacts": sorted(rows, key=lambda row: (row["candidate_id"], row["path"])),
    }
    canonical = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    report["report_payload_sha256"] = bytes_sha256(canonical)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"MATERIALIZED_PENDING_ARTIFACTS={len(rows)}")
    print("PRIMARY_TEST_DECODING=NO")
    print("COMPARATIVE_RANKING=NO")
    print(f"REPORT={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
