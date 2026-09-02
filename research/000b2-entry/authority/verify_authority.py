#!/usr/bin/env python3
"""Fail-closed verifier for 000B2 human developer-speech authority metadata.

This verifier validates a non-identifying authority sidecar. It does not create,
collect, or infer participant consent. An AUTHORIZED result is valid only when
all contract fields are explicitly populated and bound to consent-record digests.
It never accepts primary media or authorizes primary decoding.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "authority-package.schema.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_KEYS = {
    "schema_version",
    "authority_status",
    "participant_consent_scope",
    "recording_purpose",
    "public_redistribution_decision",
    "repository_storage_policy",
    "retention_rule",
    "deletion_withdrawal_procedure",
    "derivative_benchmark_artifact_permission",
    "privacy_constraints",
    "prohibited_content_policy",
    "consent_records_sha256",
    "participant_count",
    "package_contains_direct_identifiers",
    "authority_effective_before_recording",
}
REQUIRED_TEXT = (
    "participant_consent_scope",
    "recording_purpose",
    "repository_storage_policy",
    "retention_rule",
    "deletion_withdrawal_procedure",
)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def load(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs
    )
    if not isinstance(value, dict):
        raise ValueError("authority package must be a JSON object")
    return value


def verify_schema_contract() -> None:
    schema = load(SCHEMA)
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise ValueError("authority schema root must be closed object")
    required = schema.get("required")
    properties = schema.get("properties")
    if not isinstance(required, list) or set(required) != EXPECTED_KEYS:
        raise ValueError("authority schema required-field set drift")
    if not isinstance(properties, dict) or set(properties) != EXPECTED_KEYS:
        raise ValueError("authority schema property set drift")
    if properties.get("schema_version", {}).get("const") != "000b2-human-authority-v1":
        raise ValueError("authority schema version const drift")
    if set(properties.get("authority_status", {}).get("enum", [])) != {"NOT_AUTHORIZED", "AUTHORIZED"}:
        raise ValueError("authority schema status enum drift")
    if properties.get("package_contains_direct_identifiers", {}).get("const") is not False:
        raise ValueError("authority schema direct-identifier boundary drift")


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def verify_package(package: dict[str, Any], require_authorized: bool = False) -> list[str]:
    verify_schema_contract()
    errors: list[str] = []
    if set(package) != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - set(package))
        extra = sorted(set(package) - EXPECTED_KEYS)
        if missing:
            errors.append(f"missing authority fields: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected authority fields: {', '.join(extra)}")

    if package.get("schema_version") != "000b2-human-authority-v1":
        errors.append("authority schema version drift")
    status = package.get("authority_status")
    if status not in {"NOT_AUTHORIZED", "AUTHORIZED"}:
        errors.append("authority_status must be NOT_AUTHORIZED or AUTHORIZED")
    if package.get("package_contains_direct_identifiers") is not False:
        errors.append("authority package must not contain direct participant identifiers")

    for field in REQUIRED_TEXT:
        value = package.get(field)
        if value is not None and not _nonempty_text(value):
            errors.append(f"{field} must be null or a non-empty string")

    for field in (
        "public_redistribution_decision",
        "derivative_benchmark_artifact_permission",
    ):
        if package.get(field) not in {None, "ALLOWED", "PROHIBITED"}:
            errors.append(f"{field} must be null, ALLOWED, or PROHIBITED")

    if not isinstance(package.get("authority_effective_before_recording"), bool):
        errors.append("authority_effective_before_recording must be boolean")

    participant_count = package.get("participant_count")
    if not isinstance(participant_count, int) or isinstance(participant_count, bool) or participant_count < 0:
        errors.append("participant_count must be a non-negative integer")

    for field in ("privacy_constraints", "prohibited_content_policy"):
        value = package.get(field)
        if not isinstance(value, list) or any(not _nonempty_text(item) for item in value):
            errors.append(f"{field} must be an array of non-empty strings")
        elif len(value) != len(set(value)):
            errors.append(f"{field} contains duplicates")

    consent_digest = package.get("consent_records_sha256")
    if consent_digest is not None and not SHA256.fullmatch(str(consent_digest)):
        errors.append("consent_records_sha256 must be null or lowercase SHA-256")

    if status == "AUTHORIZED":
        for field in REQUIRED_TEXT:
            if not _nonempty_text(package.get(field)):
                errors.append(f"AUTHORIZED authority requires non-empty {field}")
        if package.get("public_redistribution_decision") not in {"ALLOWED", "PROHIBITED"}:
            errors.append("AUTHORIZED authority requires explicit redistribution decision")
        if package.get("derivative_benchmark_artifact_permission") not in {"ALLOWED", "PROHIBITED"}:
            errors.append("AUTHORIZED authority requires explicit derivative-artifact permission")
        if not package.get("privacy_constraints"):
            errors.append("AUTHORIZED authority requires privacy constraints")
        if not package.get("prohibited_content_policy"):
            errors.append("AUTHORIZED authority requires prohibited-content policy")
        if not isinstance(participant_count, int) or participant_count < 1:
            errors.append("AUTHORIZED authority requires at least one participant")
        if not SHA256.fullmatch(str(consent_digest or "")):
            errors.append("AUTHORIZED authority requires consent_records_sha256")
        if package.get("authority_effective_before_recording") is not True:
            errors.append("AUTHORIZED authority must be effective before recording")
    else:
        if package.get("authority_effective_before_recording") is not False:
            errors.append("NOT_AUTHORIZED package cannot claim pre-recording authority")
        if participant_count != 0:
            errors.append("NOT_AUTHORIZED template must not claim participants")
        if consent_digest is not None:
            errors.append("NOT_AUTHORIZED template must not claim consent records")

    if require_authorized and status != "AUTHORIZED":
        errors.append("human developer-speech authority is not authorized")
    return errors


def self_test() -> None:
    verify_schema_contract()
    base = {
        "schema_version": "000b2-human-authority-v1",
        "authority_status": "AUTHORIZED",
        "participant_consent_scope": "Primary developer-speech benchmark recording and scoring.",
        "recording_purpose": "Evaluate preregistered local STT candidates.",
        "public_redistribution_decision": "PROHIBITED",
        "repository_storage_policy": "Audio remains outside the public repository.",
        "retention_rule": "Retain until benchmark closeout, then delete under the recorded policy.",
        "deletion_withdrawal_procedure": "Participants may withdraw before attempt freeze.",
        "derivative_benchmark_artifact_permission": "ALLOWED",
        "privacy_constraints": ["No direct identifiers in benchmark metadata."],
        "prohibited_content_policy": ["No credentials, secrets, PHI, or proprietary code."],
        "consent_records_sha256": "0" * 64,
        "participant_count": 1,
        "package_contains_direct_identifiers": False,
        "authority_effective_before_recording": True,
    }
    if verify_package(base, require_authorized=True):
        raise AssertionError("synthetic structurally authorized fixture should validate")
    mutated = dict(base)
    mutated["authority_effective_before_recording"] = False
    if not verify_package(mutated, require_authorized=True):
        raise AssertionError("missing pre-recording authority must fail")
    mutated = dict(base)
    mutated["consent_records_sha256"] = None
    if not verify_package(mutated, require_authorized=True):
        raise AssertionError("missing consent digest must fail")
    mutated = dict(base)
    mutated["authority_status"] = "NOT_AUTHORIZED"
    mutated["participant_count"] = 0
    mutated["consent_records_sha256"] = None
    mutated["authority_effective_before_recording"] = False
    mutated["recording_purpose"] = 7
    if not verify_package(mutated):
        raise AssertionError("NOT_AUTHORIZED type drift must fail")
    print("SYNTHETIC_AUTHORITY_CONTRACT_SELF_TEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path, nargs="?")
    parser.add_argument("--require-authorized", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        if args.package is None:
            raise ValueError("authority package path is required unless --self-test is used")
        package = load(args.package)
        errors = verify_package(package, require_authorized=args.require_authorized)
    except (AssertionError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"AUTHORITY_PACKAGE=FAIL: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"AUTHORITY_PACKAGE=FAIL: {error}", file=sys.stderr)
        return 1
    status = package["authority_status"]
    print(f"AUTHORITY_PACKAGE={status}")
    print("PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_VERIFIER")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
