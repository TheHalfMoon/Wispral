#!/usr/bin/env python3
"""Composite attempt verifier for historical B2P08 and recovery B2R04/B2R05."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
LEGACY_VERIFIER = PUBLIC / "verify_attempt_manifest_legacy.py"
B2R04_VERIFIER = PUBLIC / "verify_b2r04_attempt_freeze.py"
B2R05_VERIFIER = PUBLIC / "verify_b2r05.py"


class CompositeVerificationError(RuntimeError):
    """Raised when one required attempt/recovery verifier cannot be loaded."""


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CompositeVerificationError(f"unable to load verifier: {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_verifier(path: Path, name: str) -> None:
    module = load_module(path, name)
    main = getattr(module, "main", None)
    if not callable(main):
        raise CompositeVerificationError(f"verifier has no callable main(): {path.relative_to(ROOT)}")
    result = main()
    if result not in (None, 0):
        raise CompositeVerificationError(
            f"verifier returned non-zero status {result}: {path.relative_to(ROOT)}"
        )


def main() -> int:
    run_verifier(LEGACY_VERIFIER, "wispral_b2p08_attempt_freeze_legacy")
    run_verifier(B2R04_VERIFIER, "wispral_b2r04_attempt_freeze")
    run_verifier(B2R05_VERIFIER, "wispral_b2r05_execution_evidence")
    print("B2P08_B2R04_AND_B2R05_ATTEMPT_VERIFIER=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
