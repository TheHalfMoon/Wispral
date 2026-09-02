#!/usr/bin/env python3
"""Trusted-base verifier for the frozen 000B2 participant policy.

The verifier executes only from a trusted canonical checkout. Candidate pull
requests are read as inert data at an immutable exact head SHA. This gate can
freeze project-controlled policy text, but it never attests participant consent,
recording authority, media provenance, or B2 readiness.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
PACKAGE_PATH = "research/000b2-entry/authority/authority-package.json"
FREEZE_PATH = "research/000b2-entry/authority/authority-policy-freeze.json"
READINESS_PATH = "research/000b2-entry/readiness.json"
CURRENT_PATH = "specs/CURRENT.md"
CURRENT_STATE_PATH = "docs/canonical/CURRENT_STATE.md"
AUTHORITY_VERIFIER_PATH = "research/000b2-entry/authority/verify_authority.py"
CONSENT_VERIFIER_PATH = "research/000b2-entry/authority/verify_consent_records.py"
EXPECTED_DIGEST = "454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811"
HUMAN_BLOCKER = "human developer-speech participant/media authority is absent"
B2_MARKER = "`000B2-unbiased-stt-bakeoff`\n\nState: `BLOCKED_EXTERNAL`"
CURRENT_STATE_MARKER = "**Blocked successor:** `000B2-unbiased-stt-bakeoff` — `BLOCKED_EXTERNAL`"

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

PREFREEZE_POLICY = {
    "participant_consent_scope": None,
    "recording_purpose": None,
    "repository_storage_policy": None,
    "retention_rule": None,
    "deletion_withdrawal_procedure": None,
    "public_redistribution_decision": None,
    "derivative_benchmark_artifact_permission": None,
    "privacy_constraints": [],
    "prohibited_content_policy": [],
}

EXPECTED_FREEZE = {
    "schema_version": "000b2-authority-policy-freeze-v1",
    "recorded_date": "2026-09-02",
    "policy_status": "FROZEN_OWNER_POLICY",
    "authority_package_path": PACKAGE_PATH,
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


def fail(message: str) -> None:
    raise AssertionError(message)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def load_json_text(text: str, label: str) -> dict[str, Any]:
    value = json.loads(text, object_pairs_hook=reject_duplicate_pairs)
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def load_module(base_root: Path, relative: str, name: str):
    path = base_root / relative
    if path.is_symlink() or not path.is_file():
        fail(f"trusted-base verifier missing or symlinked: {relative}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"cannot load trusted-base verifier: {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_local_file(root: Path, relative: str) -> str:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        fail(f"candidate file missing or symlinked: {relative}")
    root_resolved = root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root_resolved):
        fail(f"candidate file escapes candidate root: {relative}")
    return resolved.read_text(encoding="utf-8")


def read_local_optional(root: Path, relative: str) -> str | None:
    path = root / relative
    if not path.exists():
        return None
    return read_local_file(root, relative)


def validate_repo_name(repo: str) -> None:
    if REPO_NAME.fullmatch(repo) is None:
        fail("repository name must be owner/name using GitHub-safe characters")


def github_request(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Wispral-trusted-participant-policy/1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def read_remote_file(repo: str, head_sha: str, relative: str, token: str) -> str:
    validate_repo_name(repo)
    if SHA40.fullmatch(head_sha) is None:
        fail("candidate head SHA malformed")
    quoted = urllib.parse.quote(relative, safe="/")
    url = f"https://api.github.com/repos/{repo}/contents/{quoted}?ref={head_sha}"
    payload = github_request(url, token)
    if not isinstance(payload, dict) or payload.get("type") != "file":
        fail(f"candidate path is not a regular file: {relative}")
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        fail(f"candidate file encoding unsupported: {relative}")
    compact = "".join(payload["content"].split())
    raw = base64.b64decode(compact, validate=True)
    return raw.decode("utf-8")


def read_remote_optional(repo: str, head_sha: str, relative: str, token: str) -> str | None:
    try:
        return read_remote_file(repo, head_sha, relative, token)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def base_policy_is_frozen(base_root: Path) -> bool:
    path = base_root / FREEZE_PATH
    if path.is_symlink():
        fail("trusted-base policy freeze path is symlinked")
    return path.is_file()


def verify_candidate_texts(
    base_root: Path,
    package_text: str,
    freeze_text: str | None,
    readiness_text: str,
    current_text: str,
    current_state_text: str,
) -> str:
    authority_module = load_module(base_root, AUTHORITY_VERIFIER_PATH, "wispral_trusted_policy_authority")
    consent_module = load_module(base_root, CONSENT_VERIFIER_PATH, "wispral_trusted_policy_consent")
    package = load_json_text(package_text, "candidate authority package")
    errors = authority_module.verify_package(package, require_authorized=False)
    if errors:
        fail("candidate authority package invalid under trusted base: " + "; ".join(errors))

    if package.get("authority_status") != "NOT_AUTHORIZED":
        fail("participant policy freeze cannot authorize participant/media authority")
    if package.get("participant_count") != 0:
        fail("participant policy freeze must keep participant_count=0")
    if package.get("consent_records_sha256") is not None:
        fail("participant policy freeze must not claim consent records")
    if package.get("authority_effective_before_recording") is not False:
        fail("participant policy freeze must not claim pre-recording authority")
    if package.get("package_contains_direct_identifiers") is not False:
        fail("participant policy freeze must not contain direct identifiers")

    actual_policy = {key: package.get(key) for key in EXPECTED_POLICY}
    base_frozen = base_policy_is_frozen(base_root)
    if freeze_text is None:
        if base_frozen:
            fail("candidate removed canonical participant policy freeze")
        if actual_policy != PREFREEZE_POLICY:
            fail("candidate changed participant policy without trusted freeze record")
        policy_status = "NOT_YET_CANONICAL"
    else:
        freeze = load_json_text(freeze_text, "candidate participant policy freeze")
        if actual_policy != EXPECTED_POLICY:
            fail("candidate participant policy differs from trusted frozen projection")
        digest = consent_module.authority_policy_fingerprint(package)
        if digest != EXPECTED_DIGEST:
            fail(f"candidate participant policy digest drift: {digest}")
        if freeze != EXPECTED_FREEZE:
            fail("candidate participant policy freeze record drift")
        if freeze.get("authority_policy_sha256") != digest:
            fail("candidate freeze record does not bind exact trusted policy digest")
        policy_status = "FROZEN_TRUSTED"

    readiness = load_json_text(readiness_text, "candidate readiness")
    if readiness.get("b2_disposition") != "BLOCKED_EXTERNAL" or readiness.get("b2_ready") is not False:
        fail("candidate advanced B2 while participant/media authority remains external")
    if readiness.get("primary_test_decoding_performed") is not False:
        fail("candidate claims primary decoding before participant/media authority")
    gates = readiness.get("gates")
    if not isinstance(gates, dict):
        fail("candidate readiness gates missing")
    human = gates.get("human_developer_speech_authority")
    if not isinstance(human, dict):
        fail("candidate human authority gate missing")
    if human.get("status") != "BLOCKED_EXTERNAL" or human.get("resolved") is not False:
        fail("candidate human authority gate advanced without real participant authority")
    blockers = readiness.get("remaining_blockers")
    if not isinstance(blockers, list) or HUMAN_BLOCKER not in blockers:
        fail("candidate removed the external human authority blocker")
    if B2_MARKER not in current_text:
        fail("candidate CURRENT.md no longer records B2 BLOCKED_EXTERNAL")
    if CURRENT_STATE_MARKER not in current_state_text:
        fail("candidate CURRENT_STATE.md no longer records B2 BLOCKED_EXTERNAL")
    return policy_status


def verify_local(base_root: Path, candidate_root: Path) -> str:
    return verify_candidate_texts(
        base_root,
        read_local_file(candidate_root, PACKAGE_PATH),
        read_local_optional(candidate_root, FREEZE_PATH),
        read_local_file(candidate_root, READINESS_PATH),
        read_local_file(candidate_root, CURRENT_PATH),
        read_local_file(candidate_root, CURRENT_STATE_PATH),
    )


def verify_remote(base_root: Path, repo: str, head_sha: str, token: str) -> str:
    return verify_candidate_texts(
        base_root,
        read_remote_file(repo, head_sha, PACKAGE_PATH, token),
        read_remote_optional(repo, head_sha, FREEZE_PATH, token),
        read_remote_file(repo, head_sha, READINESS_PATH, token),
        read_remote_file(repo, head_sha, CURRENT_PATH, token),
        read_remote_file(repo, head_sha, CURRENT_STATE_PATH, token),
    )


def list_open_prs(repo: str, token: str) -> list[tuple[int, str, str]]:
    validate_repo_name(repo)
    url = f"https://api.github.com/repos/{repo}/pulls?state=open&base=main&per_page=100"
    payload = github_request(url, token)
    if not isinstance(payload, list):
        fail("open PR response malformed")
    if len(payload) == 100:
        fail("open PR list reached pagination limit; refusing incomplete revalidation")
    result: list[tuple[int, str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            fail("open PR item malformed")
        number = item.get("number")
        head = item.get("head")
        if not isinstance(number, int) or not isinstance(head, dict):
            fail("open PR identity malformed")
        head_sha = head.get("sha")
        head_repo = head.get("repo")
        head_repo_name = head_repo.get("full_name") if isinstance(head_repo, dict) else None
        if (
            not isinstance(head_sha, str)
            or SHA40.fullmatch(head_sha) is None
            or not isinstance(head_repo_name, str)
        ):
            fail("open PR head identity malformed")
        validate_repo_name(head_repo_name)
        result.append((number, head_repo_name, head_sha))
    return result


def emit(status: str) -> None:
    print(f"PARTICIPANT_POLICY={status}")
    if status == "FROZEN_TRUSTED":
        print(f"AUTHORITY_POLICY_SHA256={EXPECTED_DIGEST}")
    print("AUTHORITY_PACKAGE=NOT_AUTHORIZED")
    print("PARTICIPANT_COUNT=0")
    print("PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_GATE")
    print("B2_PRIMARY_RECORDING_AUTHORIZED=NO")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    print("PRIMARY_TEST_DECODING_AUTHORIZED=NO")
    print("B2_READY=NO")
    print("PUBLIC_RAW_AUDIO_REDISTRIBUTION=NO")
    print("MODEL_TRAINING_AUTHORIZED=NO")


def expect_failure(callable_, label: str) -> None:
    try:
        callable_()
    except (AssertionError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return
    fail(f"self-test mutation was accepted: {label}")


def self_test(base_root: Path) -> None:
    initial = verify_local(base_root, base_root)
    if initial not in {"NOT_YET_CANONICAL", "FROZEN_TRUSTED"}:
        fail("unexpected canonical participant policy state")

    with tempfile.TemporaryDirectory() as tmp:
        candidate = Path(tmp) / "candidate"
        for relative in (PACKAGE_PATH, READINESS_PATH, CURRENT_PATH, CURRENT_STATE_PATH):
            source = base_root / relative
            target = candidate / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

        package_path = candidate / PACKAGE_PATH
        package = load_json_text(package_path.read_text(encoding="utf-8"), "self-test package")
        package.update(EXPECTED_POLICY)
        package["authority_status"] = "NOT_AUTHORIZED"
        package["participant_count"] = 0
        package["consent_records_sha256"] = None
        package["authority_effective_before_recording"] = False
        package["package_contains_direct_identifiers"] = False
        package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        freeze_path = candidate / FREEZE_PATH
        freeze_path.parent.mkdir(parents=True, exist_ok=True)
        freeze_path.write_text(json.dumps(EXPECTED_FREEZE, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        frozen = verify_local(base_root, candidate)
        if frozen != "FROZEN_TRUSTED":
            fail("synthetic frozen candidate was not trusted")

        drifted = dict(package)
        drifted["recording_purpose"] = str(package["recording_purpose"]) + " drift"
        package_path.write_text(json.dumps(drifted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        expect_failure(lambda: verify_local(base_root, candidate), "policy drift")

        package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        freeze_path.unlink()
        expect_failure(lambda: verify_local(base_root, candidate), "populated policy without freeze")

        freeze_path.write_text(json.dumps(EXPECTED_FREEZE, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        authorized = dict(package)
        authorized["authority_status"] = "AUTHORIZED"
        authorized["participant_count"] = 20
        authorized["consent_records_sha256"] = "0" * 64
        authorized["authority_effective_before_recording"] = True
        package_path.write_text(json.dumps(authorized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        expect_failure(lambda: verify_local(base_root, candidate), "policy freeze self-authorized")

    print("TRUSTED_PARTICIPANT_POLICY_SELF_TEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-root", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--candidate-root", type=Path)
    source.add_argument("--head-sha")
    source.add_argument("--reverify-open-prs", action="store_true")
    source.add_argument("--self-test", action="store_true")
    parser.add_argument("--repo")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    args = parser.parse_args()

    try:
        base_root = args.base_root.resolve(strict=True)
        if args.self_test:
            self_test(base_root)
            return 0
        if args.candidate_root is not None:
            status = verify_local(base_root, args.candidate_root.resolve(strict=True))
            emit(status)
            return 0

        repo = args.repo
        if not isinstance(repo, str):
            fail("--repo owner/name is required for remote verification")
        validate_repo_name(repo)
        token = os.environ.get(args.token_env, "")
        if not token:
            fail(f"token environment variable is empty: {args.token_env}")

        if args.reverify_open_prs:
            prs = list_open_prs(repo, token)
            print(f"OPEN_PR_COUNT={len(prs)}")
            for number, head_repo, head_sha in prs:
                print(f"REVERIFY_PR={number}")
                print(f"CANDIDATE_REPOSITORY={head_repo}")
                print(f"CANDIDATE_HEAD_SHA={head_sha}")
                status = verify_remote(base_root, head_repo, head_sha, token)
                emit(status)
            print("OPEN_PR_REVERIFICATION=PASS")
            return 0

        if not isinstance(args.head_sha, str):
            fail("--head-sha is required for remote candidate verification")
        status = verify_remote(base_root, repo, args.head_sha, token)
        emit(status)
        return 0
    except (
        AssertionError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        urllib.error.URLError,
    ) as exc:
        print(f"TRUSTED_000B2_PARTICIPANT_POLICY=FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
