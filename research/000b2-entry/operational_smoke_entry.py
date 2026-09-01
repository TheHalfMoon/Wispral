#!/usr/bin/env python3
"""Canonical entrypoint for the bounded 000B2 operational smoke harness."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import operational_smoke as smoke
from verify_materialization import correction_map

HERE = Path(__file__).resolve().parent
AMENDMENT = HERE / "artifact-size-amendment.json"
EXPECTED_CORRECTIONS = {
    ("sherpa-onnx-compact", "tokens.txt"),
    ("sherpa-onnx-balanced", "tokens.txt"),
}
ORIGINAL_RUN_WHISPER = smoke.run_whisper


def canonical_amendment_sizes() -> dict[tuple[str, str], int]:
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    if not isinstance(amendment, dict):
        raise RuntimeError("artifact amendment must be a JSON object")
    corrections = correction_map(amendment)
    if set(corrections) != EXPECTED_CORRECTIONS:
        raise RuntimeError("artifact amendment correction scope drift")
    result: dict[tuple[str, str], int] = {}
    for key, item in corrections.items():
        if item.get("source_revision") != "6037ea07e3abfe599ad00d418968bcf9656e7472":
            raise RuntimeError(f"artifact amendment source revision drift: {key}")
        if item.get("historical_b1_size_bytes") != 5050 or item.get("b2_entry_size_bytes") != 5048:
            raise RuntimeError(f"artifact amendment size drift: {key}")
        result[key] = 5048
    return result


def observed_whisper_source_revision(cli_path: Path) -> str:
    cli = cli_path.resolve(strict=True)
    if cli.name != "whisper-cli" or cli.parent.name != "bin" or cli.parent.parent.name != "build":
        raise RuntimeError("whisper CLI path is not the canonical source-tree build/bin/whisper-cli path")
    source_root = cli.parents[2]
    git_dir = source_root / ".git"
    if not git_dir.exists():
        raise RuntimeError("whisper CLI source checkout has no Git identity")
    observed = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    ).stdout.strip()
    if len(observed) != 40 or any(char not in "0123456789abcdef" for char in observed):
        raise RuntimeError("whisper CLI source revision is malformed")
    cache = source_root / "build" / "CMakeCache.txt"
    if cache.is_symlink() or not cache.is_file():
        raise RuntimeError("whisper CMake build identity is missing")
    expected_home = f"CMAKE_HOME_DIRECTORY:INTERNAL={source_root}"
    if expected_home not in cache.read_text(encoding="utf-8", errors="strict").splitlines():
        raise RuntimeError("whisper CMake build is not bound to the observed source checkout")
    return observed


def bound_run_whisper(
    candidate_id: str,
    model_path: Path,
    cli_path: Path,
    wav_path: Path,
    source_revision: str,
) -> dict:
    family, _ = smoke.candidate_record(candidate_id)
    expected = family.get("runtime", {}).get("revision")
    observed = observed_whisper_source_revision(cli_path)
    if observed != expected:
        raise RuntimeError("whisper CLI source checkout differs from frozen B1 runtime revision")
    if source_revision != observed:
        raise RuntimeError("caller-supplied whisper revision differs from independently observed CLI source")
    return ORIGINAL_RUN_WHISPER(candidate_id, model_path, cli_path, wav_path, observed)


smoke.amendment_sizes = canonical_amendment_sizes
smoke.run_whisper = bound_run_whisper

if __name__ == "__main__":
    raise SystemExit(smoke.main())
