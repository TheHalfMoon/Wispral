#!/usr/bin/env python3
"""Capture a B2 execution-environment fingerprint before primary decoding.

This tool records identity only. A GitHub-hosted or otherwise uncontrolled
capture is DIAGNOSTIC and cannot authorize comparative performance claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command_output(argv: list[str]) -> str:
    try:
        return subprocess.run(
            argv,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "UNAVAILABLE"


def linux_cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if not path.is_file():
        return platform.processor() or "UNAVAILABLE"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("model name") and ":" in line:
            return line.split(":", 1)[1].strip()
    return platform.processor() or "UNAVAILABLE"


def linux_memory_bytes() -> int | None:
    path = Path("/proc/meminfo")
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("MemTotal:"):
            fields = line.split()
            if len(fields) >= 2 and fields[1].isdigit():
                return int(fields[1]) * 1024
    return None


def canonical_fingerprint_fields(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "os": evidence["os"],
        "kernel": evidence["kernel"],
        "machine": evidence["machine"],
        "cpu_model": evidence["cpu_model"],
        "logical_cpu_count": evidence["logical_cpu_count"],
        "memory_bytes": evidence["memory_bytes"],
        "runner": evidence["runner"],
        "toolchain": evidence["toolchain"],
    }


def capture(canonical_revision: str, performance_mode: str) -> dict[str, Any]:
    if not SHA40.fullmatch(canonical_revision):
        raise ValueError("canonical revision must be a 40-character lowercase Git SHA")
    if performance_mode not in {"DIAGNOSTIC", "CONTROLLED"}:
        raise ValueError("performance_mode must be DIAGNOSTIC or CONTROLLED")

    github_hosted = bool(os.environ.get("GITHUB_ACTIONS"))
    if github_hosted and performance_mode == "CONTROLLED":
        raise ValueError("GitHub Actions environment cannot be declared CONTROLLED")

    evidence: dict[str, Any] = {
        "schema_version": "000b2-execution-environment-v1",
        "canonical_wispral_revision": canonical_revision,
        "performance_mode": performance_mode,
        "comparative_performance_authorized": False,
        "primary_test_decoding_started": False,
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
        },
        "kernel": command_output(["uname", "-a"]),
        "machine": platform.machine(),
        "cpu_model": linux_cpu_model(),
        "logical_cpu_count": os.cpu_count(),
        "memory_bytes": linux_memory_bytes(),
        "runner": {
            "github_actions": github_hosted,
            "runner_os": os.environ.get("RUNNER_OS"),
            "runner_arch": os.environ.get("RUNNER_ARCH"),
            "runner_environment": os.environ.get("RUNNER_ENVIRONMENT"),
            "image_os": os.environ.get("ImageOS"),
            "image_version": os.environ.get("ImageVersion"),
        },
        "toolchain": {
            "python": platform.python_version(),
            "git": command_output(["git", "--version"]),
            "cmake": command_output(["cmake", "--version"]).splitlines()[0],
        },
    }
    canonical = json.dumps(
        canonical_fingerprint_fields(evidence),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    evidence["hardware_fingerprint_sha256"] = sha256_bytes(canonical)
    evidence["environment_id"] = (
        f"{evidence['machine']}:{evidence['cpu_model']}:{evidence['hardware_fingerprint_sha256'][:16]}"
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-revision", required=True)
    parser.add_argument("--performance-mode", default="DIAGNOSTIC")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = capture(args.canonical_revision, args.performance_mode)
    except ValueError as exc:
        print(f"CAPTURE_000B2_ENVIRONMENT=FAIL: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CAPTURE_000B2_ENVIRONMENT=PASS")
    print(f"PERFORMANCE_MODE={evidence['performance_mode']}")
    print("COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
    print("PRIMARY_TEST_DECODING_STARTED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
