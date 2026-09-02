#!/usr/bin/env python3
"""Verify the frozen owner-controlled 000B2 participant policy remains fail-closed.

This verifier freezes project-controlled policy text only. It does not attest
participant consent, recording authority, media provenance, or B2 readiness.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
AUTHORITY = HERE / "authority-package.json"
FREEZE = HERE / "authority-policy-freeze.json"
CONSENT_VERIFIER = HERE / "verify_consent_records.py"
AUTHORITY_VERIFIER = HERE / "verify_authority.py"
EXPECTED_DIGEST = "454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811"

EXPECTED_POLICY = {
    "participant_consent_scope": "Consent covers one Wispral 000B2 developer-speech benchmark participation: recording preregistered benchmark utterances, local preprocessing, C0 STT decoding, deterministic scoring, pseudonymous transcript/timing/error artifacts, and aggregate benchmark reporting. It excludes model training, voice-biometric identification, unrelated secondary research, public raw-audio release, and any reuse outside this scope without new consent.",
    "recording_purpose": "Evaluate preregistered local speech-to-text candidates for Wispral 000B2 under the frozen benchmark design; measure recognition quality and bounded operational behavior before any product dependency selection.",
    "repository_storage_policy": "Identity-bearing consent artifacts, identity-to-pseudonym mappings, contact details, withdrawal evidence, and raw human audio remain outside the public repository. GitHub may contain only schema-permitted pseudonymous metadata, cryptographic digests, non-identifying derived text/metrics allowed by consent, and aggregate reports.",
    "retention_rule": "Retain raw human audio and identity-bearing consent/authority records only for the minimum period needed to complete and independently review 000B2, and no later than 90 days after canonical 000B2 closeout; delete earlier when an effective pre-freeze withdrawal requires it. Pseudonymous benchmark evidence may remain after closeout only within the participant-approved derivative-artifact scope.",
    "deletion_withdrawal_procedure": "Before final attempt freeze, a participant may withdraw through the external consent channel. Stop new collection and use, remove the participant from the active consent bundle and active corpus, delete their raw audio from active benchmark storage, remove attributable derivatives from the active benchmark corpus, recompute affected digests and manifests, and keep B2 blocked until the frozen design is restored. Preserve only the minimum off-repository evidence needed to prove that the withdrawal request was honored.",
    "public_redistribution_decision": "PROHIBITED",
    "derivative_benchmark_artifact_permission": "ALLOWED",
    "privacy_constraints": [
        "Use independently generated pseudonymous participant ids; never derive them from names, emails, phone numbers, account ids, or other direct identifiers.",
        "Do not place raw human audio, signatures, identity-bearing consent artifacts, identity mappings, contact information, or withdrawal evidence in the public repository.",
        "Do not use recordings for model training, speaker identification, voice biometrics, advertising, profiling, or unrelated secondary research without new explicit participant consent.",
        "Limit repository-visible derived artifacts to non-identifying transcripts, timing/error metadata, cryptographic digests, and aggregate benchmark reports within the consented scope.",
        "Apply data minimization: collect only benchmark speech and metadata required by the frozen 000B2 design.",
    ],
    "prohibited_content_policy": [
        "Do not record credentials, secrets, authentication tokens, private keys, or security-sensitive values.",
        "Do not record PHI, medical records, financial account data, government identifiers, home addresses, or other sensitive personal data.",
        "Do not record proprietary source code, confidential employer/client information, unreleased product information, or content the participant is not authorized to disclose.",
        "Benchmark utterances must be preregistered developer-speech prompts and must not solicit personal disclosures.",
        "If prohibited content is spoken accidentally, stop intake for that item and exclude the media from the active corpus under the external handling procedure.",
    ],
}

EXPECTED_FREEZE = {
    "schema_version": "000b2-authority-policy-freeze-v1",
    "recorded_date": "2026-09-02",
    "policy_status": "FROZEN_OWNER_POLICY",
    "authority_package_path": "research/000b2-entry/authority/authority-package.json",
    "authority_policy_sha256": EXPECTED_DIGEST,
    "authority_status": "NOT_AUTHORIZED",
    "participant_count": 0,
    "consent_records_sha256": None,
    "authority_effective_before_recording": False,
    "participant_consent_attested": False,
    "recording_authorized": False,
    "primary_media_accepted": False,
    "primary_test_decoding_authorized": False,
    "public_raw_audio_redistribution": False,
    "model_training_authorized": False,
    "note": "This record freezes only the project-controlled participant policy projection. It does not attest participant consent, consent chronology, recording authority, media provenance, corpus acceptance, or B2 readiness.",
}


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or symlinked JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def load_module(path: Path, name: str):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or symlinked verifier: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify() -> None:
    authority = load_json(AUTHORITY)
    freeze = load_json(FREEZE)
    authority_module = load_module(AUTHORITY_VERIFIER, "wispral_policy_freeze_authority")
    consent_module = load_module(CONSENT_VERIFIER, "wispral_policy_freeze_consent")

    authority_errors = authority_module.verify_package(authority, require_authorized=False)
    if authority_errors:
        raise AssertionError("authority package invalid: " + "; ".join(authority_errors))

    if authority.get("authority_status") != "NOT_AUTHORIZED":
        raise AssertionError("policy freeze must not authorize participant/media authority")
    if authority.get("participant_count") != 0:
        raise AssertionError("policy freeze must keep participant_count=0")
    if authority.get("consent_records_sha256") is not None:
        raise AssertionError("policy freeze must not claim consent records")
    if authority.get("authority_effective_before_recording") is not False:
        raise AssertionError("policy freeze must not claim pre-recording authority")
    if authority.get("package_contains_direct_identifiers") is not False:
        raise AssertionError("policy freeze must not contain direct identifiers")

    actual_policy = {key: authority.get(key) for key in EXPECTED_POLICY}
    if actual_policy != EXPECTED_POLICY:
        raise AssertionError("frozen participant policy text drift")

    digest = consent_module.authority_policy_fingerprint(authority)
    if digest != EXPECTED_DIGEST:
        raise AssertionError(f"authority policy digest drift: {digest}")

    if freeze != EXPECTED_FREEZE:
        raise AssertionError("authority policy freeze record drift")
    if freeze["authority_policy_sha256"] != digest:
        raise AssertionError("freeze record does not bind exact authority policy digest")


def main() -> int:
    try:
        verify()
    except (AssertionError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"VERIFY_000B2_AUTHORITY_POLICY_FREEZE=FAIL: {exc}", file=sys.stderr)
        return 1

    print("VERIFY_000B2_AUTHORITY_POLICY_FREEZE=PASS")
    print(f"AUTHORITY_POLICY_SHA256={EXPECTED_DIGEST}")
    print("POLICY_STATUS=FROZEN_OWNER_POLICY")
    print("AUTHORITY_PACKAGE=NOT_AUTHORIZED")
    print("PARTICIPANT_COUNT=0")
    print("PARTICIPANT_CONSENT_ATTESTATION=NO")
    print("B2_PRIMARY_RECORDING_AUTHORIZED=NO")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    print("PRIMARY_TEST_DECODING_AUTHORIZED=NO")
    print("PUBLIC_RAW_AUDIO_REDISTRIBUTION=NO")
    print("MODEL_TRAINING_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
