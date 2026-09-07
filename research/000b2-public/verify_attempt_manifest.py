#!/usr/bin/env python3
"""Composite attempt verifier for historical B2P08 and recovery B2R04/B2R05/B2R06/B2R07/B2R08/B2R09."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from types import ModuleType
ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
VERIFIERS = [
    (PUBLIC / "verify_attempt_manifest_legacy.py", "wispral_b2p08_attempt_freeze_legacy"),
    (PUBLIC / "verify_b2r04_attempt_freeze.py", "wispral_b2r04_attempt_freeze"),
    (PUBLIC / "verify_b2r05.py", "wispral_b2r05_execution_evidence"),
    (PUBLIC / "verify_b2r06.py", "wispral_b2r06_execution_evidence"),
    (PUBLIC / "verify_b2r07.py", "wispral_b2r07_execution_evidence"),
    (PUBLIC / "verify_b2r08.py", "wispral_b2r08_execution_evidence"),
    (PUBLIC / "verify_b2r09.py", "wispral_b2r09_execution_evidence"),
]
class CompositeVerificationError(RuntimeError): pass
def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise CompositeVerificationError(f"unable to load verifier: {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
def run_verifier(path: Path, name: str) -> None:
    module = load_module(path, name); main = getattr(module, "main", None)
    if not callable(main): raise CompositeVerificationError(f"verifier has no callable main(): {path.relative_to(ROOT)}")
    result = main()
    if result not in (None, 0): raise CompositeVerificationError(f"verifier returned non-zero status {result}: {path.relative_to(ROOT)}")
def main() -> int:
    for path, name in VERIFIERS: run_verifier(path, name)
    print("B2P08_B2R04_B2R05_B2R06_B2R07_B2R08_AND_B2R09_ATTEMPT_VERIFIER=PASS"); return 0
if __name__ == "__main__": raise SystemExit(main())
