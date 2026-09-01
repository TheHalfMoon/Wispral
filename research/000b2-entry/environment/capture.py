#!/usr/bin/env python3
"""Capture a B2 execution-environment fingerprint for one declared attempt state.

The capture binds environment identity to one immutable PRE_PRIMARY_CAPTURE state
snapshot. It does not independently prove when that snapshot was authored or that
no prohibited work occurred before it; chronology remains a separate execution and
review gate. The requested performance mode is operator-declared metadata, not an
independent control attestation. GitHub-hosted captures are forced to DIAGNOSTIC.
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


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_attempt_state_bytes(raw: bytes) -> dict[str, Any]:
    value = json.loads(
        raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs
    )
    if not isinstance(value, dict):
        raise ValueError("attempt state must be a JSON object")
    attempt_id = value.get("attempt_id")
    revision = value.get("canonical_wispral_revision")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise ValueError("attempt state attempt_id missing")
    if not isinstance(revision, str) or not SHA40.fullmatch(revision):
        raise ValueError("attempt state canonical revision missing/malformed")
    if value.get("phase") != "PRE_PRIMARY_CAPTURE":
        raise ValueError("attempt state phase must be PRE_PRIMARY_CAPTURE")
    if value.get("primary_test_decoding_started") is not False:
        raise ValueError("environment identity state declares primary decoding started")
    return value


def command_output(argv: list[str]) -> str:
    try:
        output = subprocess.run(
            argv,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "UNAVAILABLE"
    return output or "UNAVAILABLE"


def linux_cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if not path.is_file():
        return platform.processor() or "UNAVAILABLE"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("model name") and ":" in line:
            value = line.split(":", 1)[1].strip()
            return value or "UNAVAILABLE"
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


def require_complete_identity(evidence: dict[str, Any]) -> None:
    if evidence["kernel"] == "UNAVAILABLE":
        raise ValueError("uname identity unavailable")
    if not evidence["machine"]:
        raise ValueError("machine architecture unavailable")
    if evidence["cpu_model"] == "UNAVAILABLE":
        raise ValueError("CPU model unavailable")
    if (
        not isinstance(evidence["logical_cpu_count"], int)
        or evidence["logical_cpu_count"] <= 0
    ):
        raise ValueError("logical CPU count unavailable")
    if not isinstance(evidence["memory_bytes"], int) or evidence["memory_bytes"] <= 0:
        raise ValueError("memory identity unavailable")
    for name in ("git", "cmake"):
        value = evidence["toolchain"].get(name)
        if not isinstance(value, str) or not value or value == "UNAVAILABLE":
            raise ValueError(f"required toolchain identity unavailable: {name}")


def capture(attempt_state_raw: bytes, performance_mode: str) -> dict[str, Any]:
    state = load_attempt_state_bytes(attempt_state_raw)
    canonical_revision = state["canonical_wispral_revision"]
    if performance_mode not in {"DIAGNOSTIC", "CONTROLLED"}:
        raise ValueError("performance_mode must be DIAGNOSTIC or CONTROLLED")

    github_actions = os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true"
    runner_environment = os.environ.get("RUNNER_ENVIRONMENT", "").strip().lower()
    github_hosted = github_actions and runner_environment != "self-hosted"
    if github_hosted and performance_mode == "CONTROLLED":
        raise ValueError("GitHub-hosted Actions environment cannot be declared CONTROLLED")

    cmake_output = command_output(["cmake", "--version"])
    evidence: dict[str, Any] = {
        "schema_version": "000b2-execution-environment-v1",
        "canonical_wispral_revision": canonical_revision,
        "performance_mode": performance_mode,
        "performance_mode_claim_source": "OPERATOR_DECLARED",
        "independent_control_attestation": False,
        "comparative_performance_authorized": False,
        "ordering": {
            "mode": "ATTEMPT_STATE_BOUND",
            "attempt_state_bound": True,
            "attempt_time_authority": False,
            "independent_chronology_attestation": False,
            "attempt_id": state["attempt_id"],
            "canonical_wispral_revision": canonical_revision,
            "attempt_state_sha256": sha256_bytes(attempt_state_raw),
            "declared_primary_test_decoding_started": False,
        },
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
            "github_actions": github_actions,
            "github_hosted": github_hosted,
            "runner_os": os.environ.get("RUNNER_OS"),
            "runner_arch": os.environ.get("RUNNER_ARCH"),
            "runner_environment": os.environ.get("RUNNER_ENVIRONMENT"),
            "image_os": os.environ.get("ImageOS"),
            "image_version": os.environ.get("ImageVersion"),
        },
        "toolchain": {
            "python": platform.python_version(),
            "git": command_output(["git", "--version"]),
            "cmake": cmake_output.splitlines()[0]
            if cmake_output != "UNAVAILABLE"
            else "UNAVAILABLE",
        },
    }
    require_complete_identity(evidence)
    canonical = json.dumps(
        canonical_fingerprint_fields(evidence),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    evidence["hardware_fingerprint_sha256"] = sha256_bytes(canonical)
    evidence["environment_id"] = (
        f"{evidence['machine']}:{evidence['cpu_model']}:"
        f"{evidence['hardware_fingerprint_sha256'][:16]}"
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-state", type=Path, required=True)
    parser.add_argument("--performance-mode", default="DIAGNOSTIC")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.attempt_state.is_symlink():
            raise ValueError("attempt state must not be a symlink")
        state_path = args.attempt_state.resolve(strict=True)
        if not state_path.is_file():
            raise ValueError("attempt state must be a regular file")
        state_raw = state_path.read_bytes()
        evidence = capture(state_raw, args.performance_mode)
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"CAPTURE_000B2_ENVIRONMENT=FAIL: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CAPTURE_000B2_ENVIRONMENT=PASS")
    print(f"ATTEMPT_ID={evidence['ordering']['attempt_id']}")
    print("ATTEMPT_STATE_BOUND=YES")
    print("INDEPENDENT_CHRONOLOGY_ATTESTATION=NO")
    print(f"PERFORMANCE_MODE={evidence['performance_mode']}")
    print("PERFORMANCE_MODE_CLAIM_SOURCE=OPERATOR_DECLARED")
    print("INDEPENDENT_CONTROL_ATTESTATION=NO")
    print("COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
