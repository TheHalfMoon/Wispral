#!/usr/bin/env python3
"""Capture exact FFmpeg attempt-time identity before any primary decode."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "contract.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(binary: Path) -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("tool_version") != "9.0.1":
        raise ValueError("preprocessing contract version drift")
    resolved = binary.resolve(strict=True)
    version = subprocess.run(
        [str(resolved), "-version"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout
    first_line = version.decode("utf-8", errors="strict").splitlines()[0]
    if not first_line.startswith("ffmpeg version 9.0.1"):
        raise ValueError(f"FFmpeg version mismatch: {first_line}")
    return {
        "schema_version": "000b2-preprocessing-evidence-v1",
        "tool": "FFmpeg",
        "tool_version": "9.0.1",
        "source_commit": contract["source_commit"],
        "binary_path": str(resolved),
        "binary_sha256": file_sha256(resolved),
        "version_output_sha256": sha256_bytes(version),
        "version_first_line": first_line,
        "contract_sha256": file_sha256(CONTRACT),
        "primary_test_decoding_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = capture(args.ffmpeg)
    except (OSError, ValueError, subprocess.CalledProcessError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"CAPTURE_000B2_PREPROCESSING=FAIL: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CAPTURE_000B2_PREPROCESSING=PASS")
    print("PRIMARY_TEST_DECODING_STARTED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
