#!/usr/bin/env python3
"""Capture exact FFmpeg identity for B2 qualification or an authorized attempt.

An attempt-bound capture proves that the emitted evidence refers to one immutable
attempt-state snapshot. It does not independently prove when that snapshot was
created or whether prohibited work occurred before it; chronology remains a
separate execution/review gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "contract.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_TOOL_VERSION = "9.0.1"
EXPECTED_SOURCE_TAG = "n9.0.1"
EXPECTED_SOURCE_COMMIT = "bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa"


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json_object(raw: bytes, label: str) -> dict[str, Any]:
    value = json.loads(
        raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs
    )
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def load_attempt_state_bytes(raw: bytes) -> dict[str, Any]:
    value = load_json_object(raw, "attempt state")
    attempt_id = value.get("attempt_id")
    revision = value.get("canonical_wispral_revision")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise ValueError("attempt state attempt_id missing")
    if not isinstance(revision, str) or not SHA40.fullmatch(revision):
        raise ValueError("attempt state canonical revision missing/malformed")
    if value.get("phase") != "PRE_PRIMARY_CAPTURE":
        raise ValueError("attempt state phase must be PRE_PRIMARY_CAPTURE")
    if value.get("primary_test_decoding_started") is not False:
        raise ValueError("preprocessing identity state declares primary decoding started")
    return value


def capture(
    binary: Path, *, attempt_state_path: Path | None, qualification_only: bool
) -> dict[str, Any]:
    if qualification_only == (attempt_state_path is not None):
        raise ValueError(
            "select exactly one of qualification-only or attempt-state-bound capture"
        )
    contract = load_json_object(CONTRACT.read_bytes(), "preprocessing contract")
    if contract.get("tool_version") != EXPECTED_TOOL_VERSION:
        raise ValueError("preprocessing contract version drift")
    if contract.get("source_tag") != EXPECTED_SOURCE_TAG:
        raise ValueError("preprocessing contract source tag drift")
    if contract.get("source_commit") != EXPECTED_SOURCE_COMMIT:
        raise ValueError("preprocessing contract source commit drift")

    resolved = binary.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("FFmpeg binary must be a regular file")
    version = subprocess.run(
        [str(resolved), "-version"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    ).stdout
    decoded = version.decode("utf-8", errors="strict")
    lines = decoded.splitlines()
    if not lines:
        raise ValueError("FFmpeg version output is empty")
    first_line = lines[0].strip()
    fields = first_line.split()
    if (
        len(fields) < 3
        or fields[0] != "ffmpeg"
        or fields[1] != "version"
        or fields[2] != EXPECTED_SOURCE_TAG
    ):
        raise ValueError(f"FFmpeg release-tag identity mismatch: {first_line}")

    ordering: dict[str, Any]
    if qualification_only:
        ordering = {
            "mode": "QUALIFICATION_ONLY",
            "attempt_state_bound": False,
            "attempt_time_authority": False,
            "independent_chronology_attestation": False,
            "primary_decode_ordering_claim": False,
        }
    else:
        assert attempt_state_path is not None
        if attempt_state_path.is_symlink():
            raise ValueError("attempt state must not be a symlink")
        state_path = attempt_state_path.resolve(strict=True)
        if not state_path.is_file():
            raise ValueError("attempt state must be a regular file")
        # One immutable byte snapshot is both validated and hashed. This proves binding
        # to those bytes, not independent chronology or when the snapshot was authored.
        state_raw = state_path.read_bytes()
        state = load_attempt_state_bytes(state_raw)
        ordering = {
            "mode": "ATTEMPT_STATE_BOUND",
            "attempt_state_bound": True,
            "attempt_time_authority": False,
            "independent_chronology_attestation": False,
            "attempt_id": state["attempt_id"],
            "canonical_wispral_revision": state["canonical_wispral_revision"],
            "attempt_state_sha256": sha256_bytes(state_raw),
            "declared_primary_test_decoding_started": False,
        }

    return {
        "schema_version": "000b2-preprocessing-evidence-v1",
        "tool": "FFmpeg",
        "tool_version": EXPECTED_TOOL_VERSION,
        "source_tag": EXPECTED_SOURCE_TAG,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "binary_path": str(resolved),
        "binary_sha256": file_sha256(resolved),
        "version_output_sha256": sha256_bytes(version),
        "version_first_line": first_line,
        "contract_sha256": file_sha256(CONTRACT),
        "ordering": ordering,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--qualification-only", action="store_true")
    mode.add_argument("--attempt-state", type=Path)
    args = parser.parse_args()
    try:
        evidence = capture(
            args.ffmpeg,
            attempt_state_path=args.attempt_state,
            qualification_only=args.qualification_only,
        )
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        print(f"CAPTURE_000B2_PREPROCESSING=FAIL: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CAPTURE_000B2_PREPROCESSING=PASS")
    print(f"CAPTURE_MODE={evidence['ordering']['mode']}")
    print(
        "ATTEMPT_STATE_BOUND="
        f"{'YES' if evidence['ordering']['attempt_state_bound'] else 'NO'}"
    )
    print("INDEPENDENT_CHRONOLOGY_ATTESTATION=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
