#!/usr/bin/env python3
"""Materialize and cryptographically verify the bounded B2P02 OpenSLR archives.

This script intentionally does not extract or retain the large upstream archives in Git.
It rechecks the official OpenSLR MD5 manifest, streams the exact archive bytes to a
temporary work directory, verifies MD5, computes SHA-256, writes a small observation
record, and prints machine-readable evidence lines for the GitHub Actions log.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROVENANCE_PATH = ROOT / "research/000b2-public/corpus-source.json"
TASKS_PATH = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
CHUNK_SIZE = 4 * 1024 * 1024
MAX_ATTEMPTS = 3
USER_AGENT = "Wispral-B2P02/1.0 (+https://github.com/TheHalfMoon/Wispral)"


def fail(message: str) -> None:
    raise SystemExit(f"B2P02_MATERIALIZATION=FAIL: {message}")


def request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def fetch_text(url: str) -> tuple[str, str]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request(url), timeout=120) as response:
                data = response.read()
                return data.decode("utf-8"), response.geturl()
        except Exception as exc:  # noqa: BLE001 - network boundary is deliberately fail-closed.
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(attempt * 2)
    fail(f"unable to fetch text resource {url}: {last_error}")
    raise AssertionError("unreachable")


def parse_official_md5(manifest: str, required_names: set[str]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for raw_line in manifest.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        digest = parts[0].lower()
        name = parts[-1].lstrip("*")
        if name in required_names:
            if name in observed:
                fail(f"duplicate official MD5 entry for {name}")
            if len(digest) != 32 or any(ch not in "0123456789abcdef" for ch in digest):
                fail(f"invalid official MD5 entry for {name}: {digest!r}")
            observed[name] = digest
    if set(observed) != required_names:
        fail(f"official checksum manifest missing required archives: {sorted(required_names - set(observed))}")
    return observed


def stream_archive(url: str, destination: Path) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        md5 = hashlib.md5(usedforsecurity=False)
        sha256 = hashlib.sha256()
        byte_count = 0
        resolved_url = url
        expected_length: int | None = None
        destination.unlink(missing_ok=True)
        try:
            with urllib.request.urlopen(request(url), timeout=120) as response, destination.open("wb") as output:
                resolved_url = response.geturl()
                content_length = response.headers.get("Content-Length")
                if content_length is not None:
                    expected_length = int(content_length)
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    output.write(chunk)
                    md5.update(chunk)
                    sha256.update(chunk)
                    byte_count += len(chunk)
            if expected_length is not None and byte_count != expected_length:
                fail(
                    f"content-length mismatch for {destination.name}: "
                    f"expected {expected_length}, observed {byte_count}"
                )
            return {
                "resolved_url": resolved_url,
                "bytes": byte_count,
                "md5": md5.hexdigest(),
                "sha256": sha256.hexdigest(),
            }
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001 - network boundary is deliberately fail-closed.
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(attempt * 2)
    fail(f"unable to materialize {url}: {last_error}")
    raise AssertionError("unreachable")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected JSON object at {path.relative_to(ROOT)}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()

    provenance = load_json(PROVENANCE_PATH)
    resource = provenance.get("resource")
    partitions = provenance.get("partitions")
    if not isinstance(resource, dict) or not isinstance(partitions, list):
        fail("corpus-source resource/partitions shape is invalid")

    checksum_manifest = resource.get("checksum_manifest")
    if not isinstance(checksum_manifest, str) or not checksum_manifest.startswith("https://www.openslr.org/"):
        fail("checksum manifest must be the canonical OpenSLR HTTPS resource")

    partition_by_name: dict[str, dict[str, Any]] = {}
    for item in partitions:
        if not isinstance(item, dict):
            fail("partition record must be an object")
        name = item.get("name")
        if not isinstance(name, str):
            fail("partition name must be a string")
        if name in partition_by_name:
            fail(f"duplicate partition {name}")
        partition_by_name[name] = item

    required_names = {"test-clean.tar.gz", "test-other.tar.gz"}
    if set(partition_by_name) != required_names:
        fail(f"unexpected partition set: {sorted(partition_by_name)}")

    manifest_text, manifest_resolved_url = fetch_text(checksum_manifest)
    official_md5 = parse_official_md5(manifest_text, required_names)
    for name, digest in official_md5.items():
        recorded = partition_by_name[name].get("official_md5")
        if recorded != digest:
            fail(f"canonical official MD5 drift for {name}: repo={recorded!r}, upstream={digest!r}")

    tasks = TASKS_PATH.read_text(encoding="utf-8")
    b2p02_complete = "- [x] `B2P02`" in tasks

    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    observations: list[dict[str, Any]] = []

    for name in sorted(required_names):
        item = partition_by_name[name]
        source_url = f"https://www.openslr.org/resources/12/{name}"
        destination = args.work_dir / name
        observed = stream_archive(source_url, destination)
        if observed["md5"] != item["official_md5"]:
            fail(
                f"official MD5 mismatch for {name}: "
                f"expected {item['official_md5']}, observed {observed['md5']}"
            )

        recorded_sha256 = item.get("archive_sha256")
        if b2p02_complete:
            if item.get("materialized") is not True:
                fail(f"completed B2P02 requires materialized=true for {name}")
            if not isinstance(recorded_sha256, str) or len(recorded_sha256) != 64:
                fail(f"completed B2P02 requires recorded archive_sha256 for {name}")
            if observed["sha256"] != recorded_sha256:
                fail(
                    f"recorded SHA-256 mismatch for {name}: "
                    f"expected {recorded_sha256}, observed {observed['sha256']}"
                )

        observation = {
            "name": name,
            "source_url": source_url,
            "resolved_url": observed["resolved_url"],
            "bytes": observed["bytes"],
            "official_md5": item["official_md5"],
            "observed_md5": observed["md5"],
            "observed_sha256": observed["sha256"],
        }
        observations.append(observation)
        print(
            "B2P02_ARCHIVE "
            f"name={name} bytes={observed['bytes']} md5={observed['md5']} "
            f"sha256={observed['sha256']} source_url={source_url}"
        )
        destination.unlink(missing_ok=True)

    record = {
        "schema_version": "000b2-public-archive-materialization-observation-v1",
        "task": "B2P02",
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "revision": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "runner_os": os.environ.get("RUNNER_OS"),
        "runner_arch": os.environ.get("RUNNER_ARCH"),
        "checksum_manifest": checksum_manifest,
        "checksum_manifest_resolved_url": manifest_resolved_url,
        "archive_bytes_retained_in_repository": False,
        "archives": observations,
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.rmtree(args.work_dir, ignore_errors=True)
    print(f"B2P02_OBSERVATION={args.output}")
    print("B2P02_MATERIALIZATION=PASS")


if __name__ == "__main__":
    main()
