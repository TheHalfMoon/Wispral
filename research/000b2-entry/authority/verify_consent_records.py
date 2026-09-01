#!/usr/bin/env python3
"""Fail-closed verifier for pseudonymous 000B2 active consent evidence records.

Identity-bearing consent artifacts stay outside the repository. This verifier
binds only pseudonymous metadata, artifact digests, and the frozen authority
policy. Structural completeness is never participant-consent attestation and
never authorizes primary media.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "consent-records.schema.json"
DEFAULT_AUTHORITY = HERE / "authority-package.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PARTICIPANT_ID = re.compile(r"^spk-[0-9a-f]{8}$")
RFC3339_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
EXPECTED_TOTAL = 20
EXPECTED_SPLITS = {"development": 4, "qualification": 4, "test": 12}
TEXT_POLICY_FIELDS = (
    "participant_consent_scope",
    "recording_purpose",
    "repository_storage_policy",
    "retention_rule",
    "deletion_withdrawal_procedure",
)
POLICY_FIELDS = (
    *TEXT_POLICY_FIELDS,
    "public_redistribution_decision",
    "derivative_benchmark_artifact_permission",
    "privacy_constraints",
    "prohibited_content_policy",
)
ROOT_KEYS = {
    "schema_version",
    "bundle_status",
    "authority_policy_sha256",
    "participant_count",
    "expected_participant_count",
    "direct_identifiers_present",
    "consent_artifacts_stored_outside_repository",
    "chronology_attestation",
    "primary_media_acceptance",
    "records",
}
RECORD_KEYS = {
    "participant_id",
    "split",
    "consent_artifact_sha256",
    "authority_policy_sha256",
    "consent_obtained_at_utc",
    "record_status",
}


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def loads_object(text: str, label: str) -> dict[str, Any]:
    value = json.loads(text, object_pairs_hook=reject_duplicate_pairs)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def load(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} missing or symlinked: {path}")
    return loads_object(path.read_text(encoding="utf-8"), label)


def load_authority_verifier():
    path = HERE / "verify_authority.py"
    if path.is_symlink() or not path.is_file():
        raise ValueError("canonical authority verifier missing or symlinked")
    spec = importlib.util.spec_from_file_location("wispral_b2_authority", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load canonical authority verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_schema_contract() -> None:
    schema = load(SCHEMA, "consent records schema")
    properties = schema.get("properties")
    required = schema.get("required")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise ValueError("consent records schema root must be a closed object")
    if not isinstance(required, list) or set(required) != ROOT_KEYS:
        raise ValueError("consent records schema required-field set drift")
    if not isinstance(properties, dict) or set(properties) != ROOT_KEYS:
        raise ValueError("consent records schema property set drift")
    expected_root = {
        "schema_version": ("const", "000b2-consent-records-v1"),
        "expected_participant_count": ("const", EXPECTED_TOTAL),
        "direct_identifiers_present": ("const", False),
        "consent_artifacts_stored_outside_repository": ("const", True),
        "chronology_attestation": ("const", "NOT_PROVIDED_BY_THIS_FORMAT"),
        "primary_media_acceptance": ("const", False),
    }
    for field, (kind, expected) in expected_root.items():
        if properties.get(field, {}).get(kind) != expected:
            raise ValueError(f"consent records schema boundary drift: {field}")
    if set(properties.get("bundle_status", {}).get("enum", [])) != {
        "NOT_COLLECTED",
        "PARTIAL",
        "COMPLETE",
    }:
        raise ValueError("consent records status enum drift")
    records = properties.get("records")
    if not isinstance(records, dict) or records.get("maxItems") != EXPECTED_TOTAL:
        raise ValueError("consent record array bound drift")
    items = records.get("items")
    if not isinstance(items, dict) or items.get("additionalProperties") is not False:
        raise ValueError("consent record item must be a closed object")
    if set(items.get("required", [])) != RECORD_KEYS:
        raise ValueError("consent record item required-field set drift")
    item_properties = items.get("properties")
    if not isinstance(item_properties, dict) or set(item_properties) != RECORD_KEYS:
        raise ValueError("consent record item property set drift")
    if item_properties.get("record_status", {}).get("const") != "ACTIVE":
        raise ValueError("active-only consent record boundary drift")


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def authority_policy_fingerprint(package: dict[str, Any]) -> str:
    for field in TEXT_POLICY_FIELDS:
        if not nonempty_text(package.get(field)):
            raise ValueError(f"authority policy requires non-empty {field}")
    if package.get("public_redistribution_decision") not in {"ALLOWED", "PROHIBITED"}:
        raise ValueError("authority policy requires explicit redistribution decision")
    if package.get("derivative_benchmark_artifact_permission") not in {"ALLOWED", "PROHIBITED"}:
        raise ValueError("authority policy requires explicit derivative-artifact permission")
    for field in ("privacy_constraints", "prohibited_content_policy"):
        value = package.get(field)
        if not isinstance(value, list) or not value or any(not nonempty_text(item) for item in value):
            raise ValueError(f"authority policy requires non-empty {field}")
        if len(value) != len(set(value)):
            raise ValueError(f"authority policy {field} contains duplicates")
    projection = {field: package[field] for field in POLICY_FIELDS}
    raw = json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def bundle_digest(bundle: dict[str, Any]) -> str:
    raw = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def valid_utc_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not RFC3339_UTC.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo == timezone.utc


def verify_bundle(
    bundle: dict[str, Any],
    authority_package: dict[str, Any],
    *,
    require_complete: bool = False,
    require_authority_binding: bool = False,
) -> list[str]:
    verify_schema_contract()
    authority = load_authority_verifier()
    errors: list[str] = []

    package_errors = authority.verify_package(authority_package, require_authorized=False)
    errors.extend(f"authority package invalid: {item}" for item in package_errors)

    if set(bundle) != ROOT_KEYS:
        missing = sorted(ROOT_KEYS - set(bundle))
        extra = sorted(set(bundle) - ROOT_KEYS)
        if missing:
            errors.append(f"missing bundle fields: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected bundle fields: {', '.join(extra)}")
    if bundle.get("schema_version") != "000b2-consent-records-v1":
        errors.append("consent record schema version drift")
    status = bundle.get("bundle_status")
    if status not in {"NOT_COLLECTED", "PARTIAL", "COMPLETE"}:
        errors.append("bundle_status must be NOT_COLLECTED, PARTIAL, or COMPLETE")
    if bundle.get("expected_participant_count") != EXPECTED_TOTAL:
        errors.append("expected_participant_count must remain 20")
    if bundle.get("direct_identifiers_present") is not False:
        errors.append("consent bundle must not contain direct participant identifiers")
    if bundle.get("consent_artifacts_stored_outside_repository") is not True:
        errors.append("identity-bearing consent artifacts must remain outside the repository")
    if bundle.get("chronology_attestation") != "NOT_PROVIDED_BY_THIS_FORMAT":
        errors.append("consent record format cannot attest chronology")
    if bundle.get("primary_media_acceptance") is not False:
        errors.append("consent record format cannot accept primary media")

    records_value = bundle.get("records")
    records = records_value if isinstance(records_value, list) else []
    if not isinstance(records_value, list):
        errors.append("records must be an array")
    participant_count = bundle.get("participant_count")
    valid_count = (
        isinstance(participant_count, int)
        and not isinstance(participant_count, bool)
        and 0 <= participant_count <= EXPECTED_TOTAL
    )
    if not valid_count:
        errors.append("participant_count must be an integer from 0 through 20")
    elif participant_count != len(records):
        errors.append("participant_count must equal the active record count")

    policy_digest = bundle.get("authority_policy_sha256")
    computed_policy: str | None = None
    if status == "NOT_COLLECTED":
        if participant_count != 0 or records:
            errors.append("NOT_COLLECTED bundle must contain zero active participant records")
        if policy_digest is not None:
            errors.append("NOT_COLLECTED bundle must not claim an authority policy digest")
    else:
        try:
            computed_policy = authority_policy_fingerprint(authority_package)
        except ValueError as exc:
            errors.append(str(exc))
        if not isinstance(policy_digest, str) or not SHA256.fullmatch(policy_digest):
            errors.append("non-empty bundle requires lowercase authority_policy_sha256")
        elif computed_policy is not None and policy_digest != computed_policy:
            errors.append("authority_policy_sha256 does not match canonical policy projection")
        if status == "PARTIAL" and not (valid_count and 0 < participant_count < EXPECTED_TOTAL):
            errors.append("PARTIAL bundle requires 1 through 19 active participant records")
        if status == "COMPLETE" and participant_count != EXPECTED_TOTAL:
            errors.append("COMPLETE bundle requires exactly 20 active participant records")

    participant_ids: list[str] = []
    artifact_digests: list[str] = []
    split_counts = {key: 0 for key in EXPECTED_SPLITS}
    for index, record in enumerate(records):
        label = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        if set(record) != RECORD_KEYS:
            errors.append(f"{label} field set drift")
            continue
        participant_id = record.get("participant_id")
        if not isinstance(participant_id, str) or not PARTICIPANT_ID.fullmatch(participant_id):
            errors.append(f"{label}.participant_id must match spk-<8 lowercase hex>")
        else:
            participant_ids.append(participant_id)
        split = record.get("split")
        if split not in EXPECTED_SPLITS:
            errors.append(f"{label}.split is invalid")
        else:
            split_counts[split] += 1
        artifact_digest = record.get("consent_artifact_sha256")
        if not isinstance(artifact_digest, str) or not SHA256.fullmatch(artifact_digest):
            errors.append(f"{label}.consent_artifact_sha256 must be lowercase SHA-256")
        else:
            artifact_digests.append(artifact_digest)
        if record.get("authority_policy_sha256") != policy_digest:
            errors.append(f"{label}.authority_policy_sha256 must equal the bundle policy digest")
        if not valid_utc_timestamp(record.get("consent_obtained_at_utc")):
            errors.append(f"{label}.consent_obtained_at_utc must be explicit RFC 3339 UTC ending in Z")
        if record.get("record_status") != "ACTIVE":
            errors.append(f"{label}.record_status must be ACTIVE; withdrawn records are removed from the active bundle")

    if participant_ids != sorted(participant_ids):
        errors.append("consent records must be sorted by participant_id")
    if len(participant_ids) != len(set(participant_ids)):
        errors.append("duplicate pseudonymous participant_id detected")
    if len(artifact_digests) != len(set(artifact_digests)):
        errors.append("consent artifact digest was reused across participants")
    for split, maximum in EXPECTED_SPLITS.items():
        if split_counts[split] > maximum:
            errors.append(f"{split} consent records exceed frozen speaker count {maximum}")
    if status == "COMPLETE" and split_counts != EXPECTED_SPLITS:
        errors.append(f"COMPLETE bundle must match frozen split counts {EXPECTED_SPLITS}")

    if require_complete and status != "COMPLETE":
        errors.append("complete 20-speaker consent record bundle is required")

    if require_authority_binding:
        digest = bundle_digest(bundle)
        if status != "COMPLETE":
            errors.append("authority binding requires a COMPLETE consent record bundle")
        if authority_package.get("authority_status") != "AUTHORIZED":
            errors.append("authority binding requires authority_status=AUTHORIZED")
        if authority_package.get("consent_records_sha256") != digest:
            errors.append("authority package consent_records_sha256 does not match canonical bundle digest")
        if authority_package.get("participant_count") != participant_count:
            errors.append("authority package participant_count does not match consent bundle")
        if authority_package.get("authority_effective_before_recording") is not True:
            errors.append("authority package must claim pre-recording effectiveness for structural binding")
        errors.extend(
            f"authority binding invalid: {item}"
            for item in authority.verify_package(authority_package, require_authorized=True)
        )
    return errors


def synthetic_package() -> dict[str, Any]:
    return {
        "schema_version": "000b2-human-authority-v1",
        "authority_status": "NOT_AUTHORIZED",
        "participant_consent_scope": "Primary developer-speech benchmark recording and scoring.",
        "recording_purpose": "Evaluate preregistered local STT candidates.",
        "public_redistribution_decision": "PROHIBITED",
        "repository_storage_policy": "Identity-bearing consent and raw audio remain outside the public repository.",
        "retention_rule": "Retain only under the participant-approved benchmark policy.",
        "deletion_withdrawal_procedure": "Withdrawal removes the participant from the active consent bundle before freeze.",
        "derivative_benchmark_artifact_permission": "ALLOWED",
        "privacy_constraints": ["Use pseudonymous speaker identifiers in repository metadata."],
        "prohibited_content_policy": ["No credentials, secrets, PHI, or proprietary repository content."],
        "consent_records_sha256": None,
        "participant_count": 0,
        "package_contains_direct_identifiers": False,
        "authority_effective_before_recording": False,
    }


def synthetic_complete_bundle(package: dict[str, Any]) -> dict[str, Any]:
    policy = authority_policy_fingerprint(package)
    splits = ["development"] * 4 + ["qualification"] * 4 + ["test"] * 12
    records = [
        {
            "participant_id": f"spk-{index:08x}",
            "split": split,
            "consent_artifact_sha256": hashlib.sha256(f"synthetic-consent-{index}".encode()).hexdigest(),
            "authority_policy_sha256": policy,
            "consent_obtained_at_utc": f"2026-09-01T12:{index:02d}:00Z",
            "record_status": "ACTIVE",
        }
        for index, split in enumerate(splits)
    ]
    return {
        "schema_version": "000b2-consent-records-v1",
        "bundle_status": "COMPLETE",
        "authority_policy_sha256": policy,
        "participant_count": EXPECTED_TOTAL,
        "expected_participant_count": EXPECTED_TOTAL,
        "direct_identifiers_present": False,
        "consent_artifacts_stored_outside_repository": True,
        "chronology_attestation": "NOT_PROVIDED_BY_THIS_FORMAT",
        "primary_media_acceptance": False,
        "records": records,
    }


def self_test() -> None:
    verify_schema_contract()
    try:
        loads_object('{"x":1,"x":2}', "duplicate-key fixture")
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate JSON members were accepted")

    package = synthetic_package()
    bundle = synthetic_complete_bundle(package)
    if verify_bundle(bundle, package, require_complete=True):
        raise AssertionError("synthetic structurally complete consent bundle should validate")

    bound_package = json.loads(json.dumps(package))
    bound_package["authority_status"] = "AUTHORIZED"
    bound_package["consent_records_sha256"] = bundle_digest(bundle)
    bound_package["participant_count"] = EXPECTED_TOTAL
    bound_package["authority_effective_before_recording"] = True
    if verify_bundle(bundle, bound_package, require_authority_binding=True):
        raise AssertionError("synthetic authority binding should validate structurally")

    mutations = []
    duplicate = json.loads(json.dumps(bundle))
    duplicate["records"][1]["participant_id"] = duplicate["records"][0]["participant_id"]
    mutations.append((duplicate, package, "duplicate participant id"))
    mismatched = json.loads(json.dumps(bundle))
    mismatched["records"][0]["authority_policy_sha256"] = "0" * 64
    mutations.append((mismatched, package, "policy mismatch"))
    inactive = json.loads(json.dumps(bundle))
    inactive["records"][0]["record_status"] = "WITHDRAWN"
    mutations.append((inactive, package, "withdrawn active record"))
    identifying = json.loads(json.dumps(bundle))
    identifying["direct_identifiers_present"] = True
    mutations.append((identifying, package, "direct identifiers"))
    bad_timestamp = json.loads(json.dumps(bundle))
    bad_timestamp["records"][0]["consent_obtained_at_utc"] = "2026-09-01X12:00:00Z"
    mutations.append((bad_timestamp, package, "non-RFC3339 timestamp separator"))
    bad_binding = json.loads(json.dumps(bound_package))
    bad_binding["consent_records_sha256"] = "0" * 64
    if not verify_bundle(bundle, bad_binding, require_authority_binding=True):
        raise AssertionError("mismatched authority binding digest must fail")
    for mutated_bundle, mutated_package, label in mutations:
        if not verify_bundle(mutated_bundle, mutated_package):
            raise AssertionError(f"{label} must fail")

    print("SYNTHETIC_CONSENT_RECORD_FORMAT_SELF_TEST=PASS")
    print("PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_FORMAT")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path, nargs="?")
    parser.add_argument("--authority-package", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--require-authority-binding", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        if args.bundle is None:
            raise ValueError("consent record bundle path is required unless --self-test is used")
        bundle = load(args.bundle, "consent record bundle")
        package = load(args.authority_package, "authority package")
        errors = verify_bundle(
            bundle,
            package,
            require_complete=args.require_complete,
            require_authority_binding=args.require_authority_binding,
        )
    except (AssertionError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"CONSENT_RECORDS=FAIL: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"CONSENT_RECORDS=FAIL: {error}", file=sys.stderr)
        return 1
    status = bundle["bundle_status"]
    output_status = "STRUCTURALLY_COMPLETE" if status == "COMPLETE" else status
    print(f"CONSENT_RECORDS={output_status}")
    print(f"PARTICIPANT_COUNT={bundle['participant_count']}")
    print(f"CONSENT_RECORDS_SHA256={bundle_digest(bundle)}")
    print("PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_FORMAT")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
