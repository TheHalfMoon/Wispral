#!/usr/bin/env python3
"""Trusted structural verifier for 000B2 human-authority candidate state.

The verifier deliberately proves only repository structure and fail-closed state.
It never attests that participant consent is genuine and never authorizes media.
Candidate code is not executed.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
PACKAGE_PATH = "research/000b2-entry/authority/authority-package.json"
READINESS_PATH = "research/000b2-entry/readiness.json"
CURRENT_PATH = "specs/CURRENT.md"
CURRENT_STATE_PATH = "docs/canonical/CURRENT_STATE.md"
HUMAN_BLOCKER = "human developer-speech participant/media authority is absent"
B2_MARKER = "`000B2-unbiased-stt-bakeoff`\n\nState: `BLOCKED_EXTERNAL`"
CURRENT_STATE_MARKER = "**Blocked successor:** `000B2-unbiased-stt-bakeoff` — `BLOCKED_EXTERNAL`"


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


def load_authority_verifier(base_root: Path):
    path = base_root / "research/000b2-entry/authority/verify_authority.py"
    if path.is_symlink() or not path.is_file():
        fail("trusted-base authority verifier missing or symlinked")
    spec = importlib.util.spec_from_file_location("wispral_trusted_authority", path)
    if spec is None or spec.loader is None:
        fail("cannot load trusted-base authority verifier")
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


def github_request(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Wispral-trusted-human-authority/1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def read_remote_file(repo: str, head_sha: str, relative: str, token: str) -> str:
    if not SHA40.fullmatch(head_sha):
        fail("candidate head SHA malformed")
    quoted = urllib.parse.quote(relative, safe="/")
    url = f"https://api.github.com/repos/{repo}/contents/{quoted}?ref={head_sha}"
    payload = github_request(url, token)
    if not isinstance(payload, dict) or payload.get("type") != "file":
        fail(f"candidate path is not a regular file: {relative}")
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        fail(f"candidate file encoding unsupported: {relative}")
    try:
        raw = base64.b64decode(payload["content"], validate=True)
        return raw.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        fail(f"candidate file decoding failed for {relative}: {exc}")


def verify_candidate_texts(
    base_root: Path,
    package_text: str,
    readiness_text: str,
    current_text: str,
    current_state_text: str,
) -> str:
    authority = load_authority_verifier(base_root)
    package = load_json_text(package_text, "candidate authority package")
    package_errors = authority.verify_package(package, require_authorized=False)
    if package_errors:
        fail("candidate authority package invalid under trusted base: " + "; ".join(package_errors))
    status = package.get("authority_status")
    if status not in {"AUTHORIZED", "NOT_AUTHORIZED"}:
        fail("trusted verifier returned unknown authority status")
    if status == "AUTHORIZED":
        authorized_errors = authority.verify_package(package, require_authorized=True)
        if authorized_errors:
            fail("candidate AUTHORIZED package failed trusted structural requirements: " + "; ".join(authorized_errors))

    readiness = load_json_text(readiness_text, "candidate readiness")
    if readiness.get("b2_disposition") != "BLOCKED_EXTERNAL" or readiness.get("b2_ready") is not False:
        fail("candidate advanced B2 before independently attested participant authority")
    if readiness.get("primary_test_decoding_performed") is not False:
        fail("candidate claims primary decoding before independently attested participant authority")
    gates = readiness.get("gates")
    if not isinstance(gates, dict):
        fail("candidate readiness gates missing")
    human = gates.get("human_developer_speech_authority")
    if not isinstance(human, dict):
        fail("candidate human authority gate missing")
    if human.get("status") != "BLOCKED_EXTERNAL" or human.get("resolved") is not False:
        fail("candidate human authority gate advanced without independent attestation")
    blockers = readiness.get("remaining_blockers")
    if not isinstance(blockers, list) or HUMAN_BLOCKER not in blockers:
        fail("candidate removed the external human authority blocker")
    if B2_MARKER not in current_text:
        fail("candidate CURRENT.md no longer records B2 BLOCKED_EXTERNAL")
    if CURRENT_STATE_MARKER not in current_state_text:
        fail("candidate CURRENT_STATE.md no longer records B2 BLOCKED_EXTERNAL")
    return str(status)


def verify_local(base_root: Path, candidate_root: Path) -> str:
    return verify_candidate_texts(
        base_root,
        read_local_file(candidate_root, PACKAGE_PATH),
        read_local_file(candidate_root, READINESS_PATH),
        read_local_file(candidate_root, CURRENT_PATH),
        read_local_file(candidate_root, CURRENT_STATE_PATH),
    )


def verify_remote(base_root: Path, repo: str, head_sha: str, token: str) -> str:
    return verify_candidate_texts(
        base_root,
        read_remote_file(repo, head_sha, PACKAGE_PATH, token),
        read_remote_file(repo, head_sha, READINESS_PATH, token),
        read_remote_file(repo, head_sha, CURRENT_PATH, token),
        read_remote_file(repo, head_sha, CURRENT_STATE_PATH, token),
    )


def list_open_prs(repo: str, token: str) -> list[tuple[int, str]]:
    url = f"https://api.github.com/repos/{repo}/pulls?state=open&base=main&per_page=100"
    payload = github_request(url, token)
    if not isinstance(payload, list):
        fail("open PR response malformed")
    result: list[tuple[int, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            fail("open PR item malformed")
        number = item.get("number")
        head_sha = item.get("head", {}).get("sha") if isinstance(item.get("head"), dict) else None
        if not isinstance(number, int) or not isinstance(head_sha, str) or not SHA40.fullmatch(head_sha):
            fail("open PR identity malformed")
        result.append((number, head_sha))
    return result


def emit(status: str) -> None:
    print(f"STRUCTURAL_AUTHORITY_PACKAGE={'PASS' if status == 'AUTHORIZED' else 'BLOCKED'}")
    print(f"AUTHORITY_PACKAGE={status}")
    print("CANDIDATE_B2_EXTERNAL_BLOCK=PASS")
    print("PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_GATE")
    print("B2_READY=NO")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-root", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--candidate-root", type=Path)
    source.add_argument("--head-sha")
    source.add_argument("--reverify-open-prs", action="store_true")
    parser.add_argument("--repo")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    args = parser.parse_args()
    try:
        base_root = args.base_root.resolve(strict=True)
        if args.candidate_root is not None:
            status = verify_local(base_root, args.candidate_root.resolve(strict=True))
            emit(status)
            return 0

        repo = args.repo
        if not isinstance(repo, str) or "/" not in repo:
            fail("--repo owner/name is required for remote verification")
        token = os.environ.get(args.token_env, "")
        if not token:
            fail(f"token environment variable is empty: {args.token_env}")

        if args.reverify_open_prs:
            prs = list_open_prs(repo, token)
            print(f"OPEN_PR_COUNT={len(prs)}")
            for number, head_sha in prs:
                print(f"REVERIFY_PR={number}")
                print(f"CANDIDATE_HEAD_SHA={head_sha}")
                status = verify_remote(base_root, repo, head_sha, token)
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
        ValueError,
        TypeError,
        json.JSONDecodeError,
        urllib.error.URLError,
    ) as exc:
        print(f"TRUSTED_000B2_HUMAN_AUTHORITY=FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
