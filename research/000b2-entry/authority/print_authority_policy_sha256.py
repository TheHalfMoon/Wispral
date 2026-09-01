#!/usr/bin/env python3
"""Print the canonical 000B2 authority-policy fingerprint without attesting consent.

This helper reuses the existing consent-record verifier's frozen projection.
It does not authorize recording, accept media, or attest participant consent.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFIER = HERE / "verify_consent_records.py"
DEFAULT_AUTHORITY = HERE / "authority-package.json"


def load_consent_verifier():
    if VERIFIER.is_symlink() or not VERIFIER.is_file():
        raise ValueError("canonical consent-record verifier missing or symlinked")
    spec = importlib.util.spec_from_file_location("wispral_b2_consent_records", VERIFIER)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load canonical consent-record verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def self_test(module) -> None:
    package = module.synthetic_package()
    digest = module.authority_policy_fingerprint(package)
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise AssertionError("authority policy fingerprint is not lowercase SHA-256")

    mutated = dict(package)
    mutated["recording_purpose"] = package["recording_purpose"] + " Material change."
    if module.authority_policy_fingerprint(mutated) == digest:
        raise AssertionError("material policy drift did not change authority fingerprint")

    invalid = dict(package)
    invalid["retention_rule"] = None
    try:
        module.authority_policy_fingerprint(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("incomplete authority policy was fingerprinted")

    print("AUTHORITY_POLICY_FINGERPRINT_HELPER_SELF_TEST=PASS")
    print("PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_HELPER")
    print("B2_PRIMARY_RECORDING_AUTHORIZED_BY_THIS_HELPER=NO")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-package", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        module = load_consent_verifier()
        if args.self_test:
            self_test(module)
            return 0
        package = module.load(args.authority_package, "authority package")
        digest = module.authority_policy_fingerprint(package)
    except (AssertionError, OSError, TypeError, ValueError) as exc:
        print(f"AUTHORITY_POLICY_FINGERPRINT=FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"AUTHORITY_POLICY_SHA256={digest}")
    print("PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_HELPER")
    print("B2_PRIMARY_RECORDING_AUTHORIZED_BY_THIS_HELPER=NO")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
