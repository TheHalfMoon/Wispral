#!/usr/bin/env python3
"""Canonical entrypoint for the 000B2 bounded operational smoke harness.

The initial harness revision used a stale local name for the already-canonical
`b2_entry_size_bytes` amendment field. This entrypoint binds the harness to the
canonical amendment schema without modifying historical evidence or weakening
artifact verification.
"""

from __future__ import annotations

import json
from pathlib import Path

import operational_smoke as smoke


def canonical_amendment_sizes() -> dict[tuple[str, str], int]:
    amendment_path = Path(__file__).resolve().parent / "artifact-size-amendment.json"
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    if amendment.get("schema_version") != "000b2-entry-artifact-amendment-v1":
        raise RuntimeError("artifact amendment schema drift")
    result: dict[tuple[str, str], int] = {}
    for item in amendment.get("corrections", []):
        key = (item["candidate_id"], item["path"])
        if key in result:
            raise RuntimeError(f"duplicate artifact amendment: {key}")
        historical = item["historical_b1_size_bytes"]
        corrected = item["b2_entry_size_bytes"]
        if not isinstance(historical, int) or not isinstance(corrected, int) or corrected <= 0:
            raise RuntimeError(f"invalid artifact amendment sizes: {key}")
        result[key] = corrected
    return result


smoke.amendment_sizes = canonical_amendment_sizes

if __name__ == "__main__":
    raise SystemExit(smoke.main())
