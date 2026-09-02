#!/usr/bin/env python3
"""Trusted-base verifier for frozen 000B2 participant-facing materials.

The verifier executes only from a trusted canonical checkout. Candidate pull
requests are read as inert data at an immutable exact head SHA. It freezes the
project-controlled participant information/consent template and recording-entry
checklist against the already frozen participant policy. It never attests real
consent, external approval, chronology, recording authority, media provenance,
corpus acceptance, or B2 readiness.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
POLICY_VERIFIER_PATH = ".github/trusted/verify_000b2_participant_policy.py"
INFO_PATH = "research/000b2-entry/authority/participant-information-consent.template.md"
CHECKLIST_PATH = "research/000b2-entry/authority/recording-entry-checklist.template.md"
FREEZE_PATH = "research/000b2-entry/authority/participant-materials-freeze.json"
POLICY_SHA256 = "454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811"
INFO_SHA256 = "dd4143145674473ea56122a7e7e23cfc95c08cb99840b451b190bc92fb3d93b6"
CHECKLIST_SHA256 = "eb6af6f09940cdb7a41efdf798458059561a31021320ca997671906ea9e36fe3"
MATERIALS_SHA256 = "45d43256e7914dc35f97ac9704a3139e92a53f145eb0239f65fa0b7f4c2eb320"

EXPECTED_MATERIALS = {
    "participant_information_consent_template": {
        "path": INFO_PATH,
        "sha256": INFO_SHA256,
    },
    "recording_entry_checklist_template": {
        "path": CHECKLIST_PATH,
        "sha256": CHECKLIST_SHA256,
    },
}

EXPECTED_FREEZE = {
    "schema_version": "000b2-participant-materials-freeze-v1",
    "recorded_date": "2026-09-02",
    "materials_status": "FROZEN_OWNER_TEMPLATES",
    "authority_policy_sha256": POLICY_SHA256,
    "materials_sha256": MATERIALS_SHA256,
    "materials": EXPECTED_MATERIALS,
    "participant_consent_attested": False,
    "recording_authorized": False,
    "primary_media_accepted": False,
    "primary_test_decoding_authorized": False,
    "b2_ready": False,
    "note": "This record freezes participant-facing and operator-entry templates only. It does not attest real consent, external approval, chronology, recording authority, media provenance, corpus acceptance, or B2 readiness.",
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


def read_local_optional(root: Path, relative: str) -> str | None:
    path = root / relative
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        fail(f"candidate path is not a regular file: {relative}")
    root_resolved = root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root_resolved):
        fail(f"candidate file escapes candidate root: {relative}")
    return resolved.read_text(encoding="utf-8")


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
            "User-Agent": "Wispral-trusted-participant-materials/1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def read_remote_optional(repo: str, head_sha: str, relative: str, token: str) -> str | None:
    validate_repo_name(repo)
    if SHA40.fullmatch(head_sha) is None:
        fail("candidate head SHA malformed")
    quoted = urllib.parse.quote(relative, safe="/")
    url = f"https://api.github.com/repos/{repo}/contents/{quoted}?ref={head_sha}"
    try:
        payload = github_request(url, token)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if not isinstance(payload, dict) or payload.get("type") != "file":
        fail(f"candidate path is not a regular file: {relative}")
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        fail(f"candidate file encoding unsupported: {relative}")
    compact = "".join(payload["content"].split())
    raw = base64.b64decode(compact, validate=True)
    return raw.decode("utf-8")


def material_projection_digest() -> str:
    canonical = json.dumps(
        EXPECTED_MATERIALS,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def base_materials_are_frozen(base_root: Path) -> bool:
    states = []
    for relative in (INFO_PATH, CHECKLIST_PATH, FREEZE_PATH):
        path = base_root / relative
        if path.is_symlink():
            fail(f"trusted-base participant-material path is symlinked: {relative}")
        states.append(path.is_file())
    if any(states) and not all(states):
        fail("trusted base contains a partial participant-material freeze")
    return all(states)


def verify_material_texts(
    base_root: Path,
    policy_status: str,
    info_text: str | None,
    checklist_text: str | None,
    freeze_text: str | None,
) -> str:
    if policy_status != "FROZEN_TRUSTED":
        fail("participant materials require the trusted frozen participant policy")

    present = [info_text is not None, checklist_text is not None, freeze_text is not None]
    base_frozen = base_materials_are_frozen(base_root)

    if not any(present):
        if base_frozen:
            fail("candidate removed canonical participant materials")
        return "NOT_YET_CANONICAL"

    if not all(present):
        fail("candidate participant materials are partial")

    assert info_text is not None
    assert checklist_text is not None
    assert freeze_text is not None

    info_digest = hashlib.sha256(info_text.encode("utf-8")).hexdigest()
    checklist_digest = hashlib.sha256(checklist_text.encode("utf-8")).hexdigest()
    if info_digest != INFO_SHA256:
        fail(f"participant information/consent template drift: {info_digest}")
    if checklist_digest != CHECKLIST_SHA256:
        fail(f"recording-entry checklist template drift: {checklist_digest}")
    if material_projection_digest() != MATERIALS_SHA256:
        fail("trusted participant-material projection digest constant is inconsistent")

    freeze = load_json_text(freeze_text, "candidate participant-material freeze")
    if freeze != EXPECTED_FREEZE:
        fail("candidate participant-material freeze record drift")
    if freeze.get("authority_policy_sha256") != POLICY_SHA256:
        fail("participant materials are not bound to the frozen participant policy")
    if freeze.get("materials_sha256") != MATERIALS_SHA256:
        fail("participant-material freeze does not bind the trusted material set")
    if freeze.get("participant_consent_attested") is not False:
        fail("participant-material templates cannot attest real consent")
    if freeze.get("recording_authorized") is not False:
        fail("participant-material templates cannot authorize recording")
    if freeze.get("primary_media_accepted") is not False:
        fail("participant-material templates cannot accept primary media")
    if freeze.get("primary_test_decoding_authorized") is not False:
        fail("participant-material templates cannot authorize primary decoding")
    if freeze.get("b2_ready") is not False:
        fail("participant-material templates cannot advance B2 readiness")
    return "FROZEN_TRUSTED"


def verify_local(base_root: Path, candidate_root: Path) -> str:
    policy = load_module(base_root, POLICY_VERIFIER_PATH, "wispral_trusted_materials_policy")
    policy_status = policy.verify_local(base_root, candidate_root)
    return verify_material_texts(
        base_root,
        policy_status,
        read_local_optional(candidate_root, INFO_PATH),
        read_local_optional(candidate_root, CHECKLIST_PATH),
        read_local_optional(candidate_root, FREEZE_PATH),
    )


def verify_remote(base_root: Path, repo: str, head_sha: str, token: str) -> str:
    policy = load_module(base_root, POLICY_VERIFIER_PATH, "wispral_trusted_materials_policy")
    policy_status = policy.verify_remote(base_root, repo, head_sha, token)
    return verify_material_texts(
        base_root,
        policy_status,
        read_remote_optional(repo, head_sha, INFO_PATH, token),
        read_remote_optional(repo, head_sha, CHECKLIST_PATH, token),
        read_remote_optional(repo, head_sha, FREEZE_PATH, token),
    )


def emit(status: str) -> None:
    print(f"PARTICIPANT_MATERIALS={status}")
    print(f"AUTHORITY_POLICY_SHA256={POLICY_SHA256}")
    if status == "FROZEN_TRUSTED":
        print(f"PARTICIPANT_MATERIALS_SHA256={MATERIALS_SHA256}")
        print(f"PARTICIPANT_INFORMATION_SHA256={INFO_SHA256}")
        print(f"RECORDING_ENTRY_CHECKLIST_SHA256={CHECKLIST_SHA256}")
    print("PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_GATE")
    print("B2_PRIMARY_RECORDING_AUTHORIZED=NO")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    print("PRIMARY_TEST_DECODING_AUTHORIZED=NO")
    print("B2_READY=NO")


def expect_failure(callable_, label: str) -> None:
    try:
        callable_()
    except (AssertionError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return
    fail(f"self-test mutation was accepted: {label}")


def self_test(base_root: Path) -> None:
    initial = verify_local(base_root, base_root)
    if initial not in {"NOT_YET_CANONICAL", "FROZEN_TRUSTED"}:
        fail("unexpected canonical participant-material state")

    if material_projection_digest() != MATERIALS_SHA256:
        fail("trusted material-set digest self-test failed")

    expect_failure(
        lambda: verify_material_texts(
            base_root,
            "FROZEN_TRUSTED",
            "partial",
            None,
            None,
        ),
        "partial participant material set",
    )

    if initial == "FROZEN_TRUSTED":
        info = read_local_optional(base_root, INFO_PATH)
        checklist = read_local_optional(base_root, CHECKLIST_PATH)
        freeze = read_local_optional(base_root, FREEZE_PATH)
        assert info is not None and checklist is not None and freeze is not None
        verify_material_texts(base_root, "FROZEN_TRUSTED", info, checklist, freeze)
        expect_failure(
            lambda: verify_material_texts(
                base_root,
                "FROZEN_TRUSTED",
                info + "\nDRIFT\n",
                checklist,
                freeze,
            ),
            "participant information drift",
        )
        expect_failure(
            lambda: verify_material_texts(
                base_root,
                "FROZEN_TRUSTED",
                info,
                checklist + "\nDRIFT\n",
                freeze,
            ),
            "recording checklist drift",
        )

    print("TRUSTED_PARTICIPANT_MATERIALS_SELF_TEST=PASS")


def list_open_prs(base_root: Path, repo: str, token: str) -> list[tuple[int, str, str]]:
    policy = load_module(base_root, POLICY_VERIFIER_PATH, "wispral_trusted_materials_prs")
    return policy.list_open_prs(repo, token)


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
            prs = list_open_prs(base_root, repo, token)
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
        print(f"TRUSTED_000B2_PARTICIPANT_MATERIALS=FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
