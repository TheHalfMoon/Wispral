#!/usr/bin/env python3
"""Preserve legacy workflow-contract verification and enforce the active B2R03 gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "research" / "000b2-public" / "verify_workflow_contracts_legacy.py"
B2R03 = ROOT / "research" / "000b2-public" / "verify_b2r03_preexecution_rebinding.py"
READINESS = ROOT / "research" / "000b2-public" / "recovery-readiness.json"


def run_verifier(path: Path) -> None:
    subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        check=True,
        timeout=180,
    )


def active_recovery_unit() -> str | None:
    value = json.loads(READINESS.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("B2R03_WORKFLOW_GATE=FAIL: recovery readiness must be an object")
    active = value.get("active_recovery_unit")
    if active is not None and not isinstance(active, str):
        raise SystemExit("B2R03_WORKFLOW_GATE=FAIL: active_recovery_unit must be a string or null")
    return active


def main() -> None:
    run_verifier(LEGACY)
    active = active_recovery_unit()
    if active == "B2R03":
        if not B2R03.is_file():
            raise SystemExit("B2R03_WORKFLOW_GATE=FAIL: active B2R03 verifier is missing")
        run_verifier(B2R03)
        print("B2R03_WORKFLOW_GATE=ENFORCED")
    else:
        print(f"B2R03_WORKFLOW_GATE=NOT_APPLICABLE active_recovery_unit={active!r}")


if __name__ == "__main__":
    main()
