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


def fingerprint(module, package: dict) -> str:
    module.verify_schema_contract()
    authority = module.load_authority_verifier()
    errors = authority.verify_package(package, require_authorized=False)
    if errors:
        raise ValueError("authority package invalid: " + "; ".join(errors))
    return module.authority_policy_fingerprint(package)


def must_reject(module, package: dict, label: str) -> None:
    try:
        fingerprint(module, package)
    except ValueError:
        return
    raise AssertionError(f"{label} was fingerprinted")


def self_test(module) -> None:
    package = module.synthetic_package()
    digest = fingerprint(module, package)
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise AssertionError("authority policy fingerprint is not lowercase SHA-256")

    mutated = dict(package)
    mutated["recording_purpose"] = package["recording_purpose"] + " Material change."
    if fingerprint(module, mutated) == digest:
        raise AssertionError("material policy drift did not change authority fingerprint")

    incomplete = dict(package)
    incomplete["retention_rule"] = None
    must_reject(module, incomplete, "incomplete authority policy")

    extra = dict(package)
    extra["unexpected_field"] = "not allowed"
    must_reject(module, extra, "authority package with extra field")

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
        digest = fingerprint(module, package)
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
