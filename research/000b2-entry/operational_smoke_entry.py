#!/usr/bin/env python3
"""Canonical entrypoint for the bounded 000B2 operational smoke harness."""

from __future__ import annotations

import json
from pathlib import Path

import operational_smoke as smoke
from verify_materialization import correction_map

HERE = Path(__file__).resolve().parent
AMENDMENT = HERE / "artifact-size-amendment.json"
EXPECTED_CORRECTIONS = {
    ("sherpa-onnx-compact", "tokens.txt"),
    ("sherpa-onnx-balanced", "tokens.txt"),
}


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


smoke.amendment_sizes = canonical_amendment_sizes

if __name__ == "__main__":
    raise SystemExit(smoke.main())
