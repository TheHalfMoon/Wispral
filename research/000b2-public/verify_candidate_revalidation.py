#!/usr/bin/env python3
"""Verify B2P05 candidate identity revalidation without decoding audio."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = ROOT / "research/000b2-public/candidate-revalidation.json"
REGISTRY_PATH = ROOT / "research/000b1/qualified-candidates.json"
MATERIALIZED_PATH = ROOT / "research/000b2-entry/materialized-artifacts.json"
READINESS_PATH = ROOT / "research/000b2-public/readiness.json"
TRUSTED_VERIFIER_PATH = ROOT / ".github/trusted/verify_000b2_materialization.py"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_IDS = {
    "moonshine-compact",
    "moonshine-balanced",
    "whispercpp-compact",
    "whispercpp-balanced",
    "sherpa-onnx-compact",
    "sherpa-onnx-balanced",
}


class RevalidationError(RuntimeError):
    """Fail-closed B2P05 verification error."""


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys so authority inputs remain unambiguous."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RevalidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_object(path: Path) -> dict[str, Any]:
    """Load one regular UTF-8 JSON authority file with duplicate-key rejection."""
    if path.is_symlink() or not path.is_file():
        raise RevalidationError(f"authority input is not a regular file: {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RevalidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise RevalidationError(f"authority input must be an object: {path.relative_to(ROOT)}")
    return value


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a bounded repository authority file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    """Raise a stable fail-closed error when a B2P05 invariant is false."""
    if not condition:
        raise RevalidationError(message)


def family_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the exact three canonical candidate families without duplicates."""
    families = registry.get("families")
    require(isinstance(families, list), "candidate registry families missing")
    result: dict[str, dict[str, Any]] = {}
    for family in families:
        require(isinstance(family, dict), "candidate family must be an object")
        name = family.get("family")
        require(isinstance(name, str) and name not in result, "candidate family identity drift")
        result[name] = family
    require(set(result) == {"moonshine", "whisper.cpp", "sherpa-onnx"}, "candidate family set drift")
    return result


def verify_static_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    """Verify exact B2P05 authority, six-cell membership, pins, and closed later gates."""
    evidence = load_object(EVIDENCE_PATH)
    registry = load_object(REGISTRY_PATH)
    materialized = load_object(MATERIALIZED_PATH)
    readiness = load_object(READINESS_PATH)

    require(evidence.get("schema_version") == "000b2-public-candidate-revalidation-v1", "B2P05 evidence schema drift")
    require(evidence.get("task") == "B2P05", "B2P05 task identity drift")
    require(evidence.get("canonical_base_sha") == "6135cd67c1b31e0be0b82ba202b6a6770d34b68d", "B2P05 canonical base drift")
    registry_sha = sha256_file(REGISTRY_PATH)
    require(SHA256_RE.fullmatch(registry_sha) is not None, "candidate registry SHA-256 malformed")
    require(evidence.get("candidate_registry_sha256") == registry_sha, "candidate registry byte digest drift")
    require(materialized.get("registry_sha256") == registry_sha, "materialized artifact evidence is not bound to canonical registry")

    candidate_ids = evidence.get("candidate_ids")
    require(isinstance(candidate_ids, list) and len(candidate_ids) == len(set(candidate_ids)), "candidate ID list malformed")
    require(set(candidate_ids) == EXPECTED_IDS, "candidate ID allowlist drift")

    families = family_map(registry)
    registry_ids: set[str] = set()
    for name, family in families.items():
        configurations = family.get("configurations")
        require(isinstance(configurations, list) and len(configurations) == 2, f"{name} configuration cardinality drift")
        for config in configurations:
            require(isinstance(config, dict), f"{name} configuration malformed")
            candidate_id = config.get("id")
            require(isinstance(candidate_id, str) and candidate_id not in registry_ids, "duplicate registry candidate ID")
            registry_ids.add(candidate_id)
            c0 = config.get("c0")
            require(isinstance(c0, dict) and c0.get("language") == "en", f"{candidate_id} C0 language drift")
            require(c0.get("repository_context") == "OFF", f"{candidate_id} repository context must remain OFF")
            for field in ("keyterms", "grammar", "initial_prompt", "prompt_carryover", "hotwords"):
                if field in c0:
                    require(c0.get(field) == "OFF", f"{candidate_id} C0 {field} must remain OFF")
    require(registry_ids == EXPECTED_IDS, "canonical registry candidate membership drift")

    pins = evidence.get("runtime_pins")
    require(isinstance(pins, dict) and set(pins) == set(families), "runtime pin family set drift")
    for name, family in families.items():
        runtime = family.get("runtime")
        pin = pins[name]
        require(isinstance(runtime, dict) and isinstance(pin, dict), f"{name} runtime pin malformed")
        for field in ("repository", "release", "revision"):
            require(pin.get(field) == runtime.get(field), f"{name} runtime {field} drift")
        revision = pin.get("revision")
        require(isinstance(revision, str) and SHA40_RE.fullmatch(revision) is not None, f"{name} runtime revision malformed")

    moonshine_source = families["moonshine"].get("model_source")
    whisper_source = families["whisper.cpp"].get("model_source")
    sherpa_source = families["sherpa-onnx"].get("model_source")
    require(isinstance(moonshine_source, dict) and pins["moonshine"].get("model_asset_revision") == moonshine_source.get("asset_revision"), "Moonshine model asset revision drift")
    require(isinstance(whisper_source, dict) and pins["whisper.cpp"].get("model_repository") == whisper_source.get("repository"), "whisper.cpp model repository drift")
    require(pins["whisper.cpp"].get("model_revision") == whisper_source.get("revision"), "whisper.cpp model revision drift")
    require(isinstance(sherpa_source, dict) and pins["sherpa-onnx"].get("model_repository") == sherpa_source.get("repository"), "sherpa-onnx model repository drift")
    require(pins["sherpa-onnx"].get("onnx_revision") == sherpa_source.get("onnx_revision"), "sherpa-onnx model revision drift")

    require(readiness.get("state") == "READY" and readiness.get("completed_through") == "B2P04", "B2P05 requires canonical B2P04 readiness")
    public = readiness.get("public_human_baseline")
    preprocessing = readiness.get("preprocessing")
    attempt = readiness.get("attempt_manifest")
    guards = readiness.get("claim_guards")
    require(isinstance(public, dict) and public.get("candidate_decoding_started") is False, "candidate decoding started before B2P05")
    require(isinstance(preprocessing, dict) and preprocessing.get("resolved") is False, "B2P06 preprocessing capture started before B2P05")
    require(isinstance(attempt, dict) and attempt.get("primary_decoding_started") is False and attempt.get("frozen") is False, "attempt state advanced before B2P05")
    require(isinstance(guards, dict), "claim guards missing")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(guards.get("production_stt_selected") is False and guards.get("product_code_authorized") is False, "product-selection guard drift")
    evidence_guards = evidence.get("guards")
    require(isinstance(evidence_guards, dict) and all(evidence_guards.get(key) is False for key in ("candidate_decoding_started", "primary_decoding_started", "b2p06_preprocessing_capture_started", "production_stt_selected", "product_code_authorized")), "B2P05 evidence guard drift")
    require(evidence_guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "B2P05 human-evidence guard drift")

    print("B2P05_STATIC_AUTHORITY=PASS")
    print("B2P05_CANDIDATE_COUNT=6")
    print("B2P05_C0_CONTEXT_FREEZE=PASS")
    print("B2P05_LATER_GATES_CLOSED=PASS")
    return evidence, registry, families


def github_json(url: str) -> dict[str, Any]:
    """Fetch one public GitHub API object with the workflow token when available."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Wispral-B2P05-candidate-revalidation/1",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            value = json.load(response)
    except Exception as exc:
        raise RevalidationError(f"GitHub live identity fetch failed for {url}: {exc}") from exc
    require(isinstance(value, dict), f"GitHub API response must be an object: {url}")
    return value


def resolve_release_tag(repo: str, tag: str) -> str:
    """Resolve a GitHub release tag through annotated tags to its exact commit SHA."""
    release = github_json(f"https://api.github.com/repos/{repo}/releases/tags/{quote(tag, safe='')}")
    require(release.get("tag_name") == tag and release.get("draft") is False, f"{repo} release tag drift")
    ref = github_json(f"https://api.github.com/repos/{repo}/git/ref/tags/{quote(tag, safe='')}")
    obj = ref.get("object")
    require(isinstance(obj, dict), f"{repo} tag object missing")
    for _ in range(4):
        object_type = obj.get("type")
        object_sha = obj.get("sha")
        require(isinstance(object_sha, str) and SHA40_RE.fullmatch(object_sha) is not None, f"{repo} tag SHA malformed")
        if object_type == "commit":
            return object_sha
        require(object_type == "tag", f"{repo} tag resolves to unsupported object type")
        tag_object = github_json(f"https://api.github.com/repos/{repo}/git/tags/{object_sha}")
        obj = tag_object.get("object")
        require(isinstance(obj, dict), f"{repo} annotated tag target missing")
    raise RevalidationError(f"{repo} tag indirection exceeds trusted bound")


def verify_runtime_pins(evidence: dict[str, Any]) -> None:
    """Revalidate every canonical runtime release/tag and exact source revision live."""
    pins = evidence["runtime_pins"]
    for family_name in sorted(pins):
        pin = pins[family_name]
        repo = pin["repository"]
        release = pin["release"]
        revision = pin["revision"]
        tag_commit = resolve_release_tag(repo, release)
        require(tag_commit == revision, f"{family_name} release no longer resolves to canonical revision")
        commit = github_json(f"https://api.github.com/repos/{repo}/commits/{revision}")
        require(commit.get("sha") == revision, f"{family_name} canonical runtime revision no longer resolves")
        print(f"B2P05_RUNTIME_PIN_{family_name.upper().replace('.', '_').replace('-', '_')}=PASS")


def load_trusted_verifier():
    """Load the canonical trusted artifact verifier without creating a second trust policy."""
    spec = importlib.util.spec_from_file_location("wispral_trusted_materialization", TRUSTED_VERIFIER_PATH)
    require(spec is not None and spec.loader is not None, "trusted artifact verifier cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_all_artifact_bytes(registry: dict[str, Any]) -> None:
    """Reproduce pending identities and all already-pinned model artifact digests live."""
    trusted = load_trusted_verifier()
    trusted.verify(ROOT, ROOT)
    print("B2P05_PENDING_ARTIFACT_IDENTITIES=PASS")

    observations: dict[tuple[str, int, str], tuple[str, str]] = {}
    for family in registry["families"]:
        name = family["family"]
        model_source = family.get("model_source")
        require(isinstance(model_source, dict), f"{name} model source missing")
        for config in family["configurations"]:
            for artifact in config["artifacts"]:
                committed_sha = artifact.get("sha256")
                if committed_sha is None:
                    continue
                require(isinstance(committed_sha, str) and SHA256_RE.fullmatch(committed_sha) is not None, f"{config['id']} pinned SHA-256 malformed")
                size = artifact.get("size_bytes")
                require(isinstance(size, int) and size > 0, f"{config['id']} pinned size malformed")
                path = artifact.get("path")
                require(isinstance(path, str) and path, f"{config['id']} pinned artifact path malformed")
                if name == "whisper.cpp":
                    base_url = model_source.get("base_url")
                    require(isinstance(base_url, str) and base_url.startswith("https://huggingface.co/"), "whisper.cpp model base URL drift")
                    url = f"{base_url.rstrip('/')}/{path}"
                elif name == "sherpa-onnx":
                    base_url = model_source.get("base_url")
                    revision = artifact.get("source_revision")
                    require(isinstance(base_url, str) and base_url.startswith("https://huggingface.co/"), "sherpa-onnx model base URL drift")
                    require(isinstance(revision, str) and SHA40_RE.fullmatch(revision) is not None, f"{config['id']} source revision malformed")
                    url = f"{base_url.rstrip('/')}/{revision}/{path}"
                else:
                    raise RevalidationError(f"unexpected pre-pinned artifact family: {name}")
                observations[(url, size, committed_sha)] = (config["id"], path)

    for (url, size, committed_sha), (candidate_id, path) in sorted(observations.items()):
        observed_sha = trusted.download_digest(url, size, "huggingface")
        require(observed_sha == committed_sha, f"live pinned SHA-256 mismatch for {(candidate_id, path)}")
        print(f"B2P05_PINNED_ARTIFACT={candidate_id}:{path}:PASS")
    print(f"B2P05_PINNED_ARTIFACT_UNIQUE_DOWNLOADS={len(observations)}")
    print("B2P05_ALL_ARTIFACT_IDENTITIES=PASS")


def main() -> int:
    """Run static B2P05 gates and optionally the bounded live network revalidation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="revalidate runtime refs and all model artifact bytes from pinned sources")
    args = parser.parse_args()
    try:
        evidence, registry, _ = verify_static_authority()
        if args.live:
            verify_runtime_pins(evidence)
            verify_all_artifact_bytes(registry)
            print("B2P05_LIVE_REVALIDATION=PASS")
        else:
            print("B2P05_LIVE_REVALIDATION=NOT_RUN")
        print("B2P05_CANDIDATE_REVALIDATION_VERIFIER=PASS")
        return 0
    except (RevalidationError, Exception) as exc:
        print(f"B2P05_CANDIDATE_REVALIDATION_VERIFIER=FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
