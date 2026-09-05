#!/usr/bin/env python3
"""Verify B2P05 candidate identities against an independent canonical base checkout."""

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

CANDIDATE_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_BASE_SHA = "6135cd67c1b31e0be0b82ba202b6a6770d34b68d"
B2P05_CANONICAL_MERGE = "49538990fb4cf8223e9321261925206ed7ff5cee"
EVIDENCE_REL = Path("research/000b2-public/candidate-revalidation.json")
REGISTRY_REL = Path("research/000b1/qualified-candidates.json")
MATERIALIZED_REL = Path("research/000b2-entry/materialized-artifacts.json")
AMENDMENT_REL = Path("research/000b2-entry/artifact-size-amendment.json")
READINESS_REL = Path("research/000b2-public/readiness.json")
TRUSTED_VERIFIER_REL = Path(".github/trusted/verify_000b2_materialization.py")
EXPECTED_REGISTRY_SHA256 = "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f"
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
IMMUTABLE_BASE_INPUTS = (
    REGISTRY_REL,
    MATERIALIZED_REL,
    AMENDMENT_REL,
    TRUSTED_VERIFIER_REL,
)


class RevalidationError(RuntimeError):
    """Fail-closed B2P05 verification error."""


def require(condition: bool, message: str) -> None:
    """Raise a stable fail-closed error when a B2P05 invariant is false."""
    if not condition:
        raise RevalidationError(message)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys so authority inputs remain unambiguous."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RevalidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def safe_bytes(root: Path, relative: Path) -> bytes:
    """Read one regular non-symlink file without permitting checkout-root escape."""
    resolved_root = root.resolve(strict=True)
    path = resolved_root / relative
    if path.is_symlink():
        raise RevalidationError(f"symlink is forbidden for authority input: {relative}")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(resolved_root):
        raise RevalidationError(f"authority input escapes checkout root: {relative}")
    if not resolved.is_file():
        raise RevalidationError(f"authority input is not a regular file: {relative}")
    return resolved.read_bytes()


def load_object(raw: bytes, label: str) -> dict[str, Any]:
    """Parse one UTF-8 JSON object with duplicate-key rejection."""
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RevalidationError(f"invalid JSON in {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise RevalidationError(f"{label} must be a JSON object")
    return value


def sha256_bytes(raw: bytes) -> str:
    """Return a SHA-256 digest for exact authority bytes."""
    return hashlib.sha256(raw).hexdigest()


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


def verify_readiness_phase(base_readiness: dict[str, Any], readiness: dict[str, Any]) -> str:
    """Accept B2P05 execution and canonical reconciliations through B2E02 with later gates closed."""
    require(base_readiness.get("state") == "READY", "canonical base public readiness must remain READY")
    require(base_readiness.get("completed_through") == "B2P04", "canonical B2P05 base must remain completed through B2P04")
    base_next = base_readiness.get("next_action")
    require(isinstance(base_next, str) and base_next.startswith("Execute B2P05 only:"), "canonical B2P05 base next action drift")

    require(readiness.get("state") == "READY", "public readiness must remain READY")
    completed_through = readiness.get("completed_through")
    require(completed_through in {"B2P04", "B2P05", "B2P06", "B2P07", "B2P08", "B2E01", "B2E02"}, "unsupported B2P05-B2E02 readiness phase")
    public = readiness.get("public_human_baseline")
    preprocessing = readiness.get("preprocessing")
    environment = readiness.get("execution_environment")
    attempt = readiness.get("attempt_manifest")
    guards = readiness.get("claim_guards")
    require(isinstance(public, dict) and public.get("candidate_decoding_started") is False, "historical readiness candidate-decoding flag must remain false through B2E02 reconciliation")
    require(isinstance(preprocessing, dict), "preprocessing readiness missing")
    require(isinstance(environment, dict), "execution environment readiness missing")
    require(isinstance(attempt, dict) and attempt.get("primary_decoding_started") is False, "primary decoding started before B2E01")
    require(isinstance(guards, dict), "claim guards missing")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(guards.get("production_stt_selected") is False and guards.get("product_code_authorized") is False, "product-selection guard drift")
    next_action = readiness.get("next_action")
    if completed_through == "B2P04":
        require(attempt.get("frozen") is False, "B2P08 froze before B2P05 execution")
        require(environment.get("resolved") is False, "B2P07 environment capture started before B2P05 execution")
        require(preprocessing.get("resolved") is False, "B2P06 preprocessing capture started before B2P05 execution")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P05 only:"), "B2P05 execution phase next action drift")
        require("Do not begin candidate decoding, B2P06 preprocessing capture, or primary decoding until B2P05 is canonical." in next_action, "B2P05 execution boundary drift")
        return "EXECUTION"
    if completed_through == "B2P05":
        require(attempt.get("frozen") is False, "B2P08 froze before B2P06 execution")
        require(environment.get("resolved") is False, "B2P07 environment capture started before B2P06 execution")
        require(preprocessing.get("resolved") is False, "B2P06 preprocessing must remain unresolved at the B2P05 frontier")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P06 only:"), "B2P05 reconciliation must authorize B2P06 only")
        require("Do not begin B2P07 environment capture, B2P08 attempt freeze, or candidate decoding until B2P06 is canonical." in next_action, "B2P06 successor boundary drift")
        return "B2P05_RECONCILED"
    if completed_through == "B2P06":
        require(attempt.get("frozen") is False, "B2P08 froze before B2P07 execution")
        require(environment.get("resolved") is False, "B2P07 environment must remain unresolved at the B2P06 frontier")
        require(preprocessing.get("resolved") is True, "B2P06 reconciliation must mark preprocessing resolved")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P07 only:"), "B2P06 reconciliation must authorize B2P07 only")
        require("Do not begin B2P08 attempt freeze or candidate decoding until B2P07 is canonical." in next_action, "B2P07 successor boundary drift")
        return "B2P06_RECONCILED"
    require(preprocessing.get("resolved") is True, "later reconciliation must preserve preprocessing resolution")
    require(environment.get("resolved") is True, "later reconciliation must preserve execution environment resolution")
    if completed_through == "B2P07":
        require(attempt.get("frozen") is False, "B2P08 attempt advanced before canonical reconciliation")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P08 only:"), "B2P07 reconciliation must authorize B2P08 only")
        require("Do not begin candidate or primary decoding until B2P08 is canonical." in next_action, "B2P08 successor boundary drift")
        return "B2P07_RECONCILED"
    require(attempt.get("frozen") is True, "B2P08 reconciliation must mark the attempt manifest frozen")
    if completed_through == "B2P08":
        require(isinstance(next_action, str) and next_action.startswith("Execute B2E01 only:"), "B2P08 reconciliation must authorize B2E01 only")
        require("Do not begin B2E02 or any later candidate cell until B2E01 is canonical." in next_action, "B2E01 successor boundary drift")
        return "B2P08_RECONCILED"
    if completed_through == "B2E01":
        require(isinstance(next_action, str) and next_action.startswith("Execute B2E02 only:"), "B2E01 reconciliation must authorize B2E02 only")
        require("Do not begin B2E03 or any later candidate cell until B2E02 is canonical." in next_action, "B2E02 successor boundary drift")
        return "B2E01_RECONCILED"
    require(isinstance(next_action, str) and next_action.startswith("Execute B2E03 only:"), "B2E02 reconciliation must authorize B2E03 only")
    require("Do not begin B2E04 or any later candidate cell until B2E03 is canonical." in next_action, "B2E03 successor boundary drift")
    return "B2E02_RECONCILED"

def verify_static_authority(trusted_base_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind B2P05 candidate data to immutable canonical-base authority and closed gates."""
    base_root = trusted_base_root.resolve(strict=True)
    candidate_root = CANDIDATE_ROOT.resolve(strict=True)

    for relative in IMMUTABLE_BASE_INPUTS:
        base_raw = safe_bytes(base_root, relative)
        candidate_raw = safe_bytes(candidate_root, relative)
        require(candidate_raw == base_raw, f"candidate changed canonical B2P05 authority input: {relative}")

    registry_raw = safe_bytes(base_root, REGISTRY_REL)
    materialized_raw = safe_bytes(base_root, MATERIALIZED_REL)
    base_readiness_raw = safe_bytes(base_root, READINESS_REL)
    readiness_raw = safe_bytes(candidate_root, READINESS_REL)
    evidence_raw = safe_bytes(candidate_root, EVIDENCE_REL)

    registry_sha = sha256_bytes(registry_raw)
    require(registry_sha == EXPECTED_REGISTRY_SHA256, "canonical candidate registry byte digest drift")

    registry = load_object(registry_raw, "canonical candidate registry")
    materialized = load_object(materialized_raw, "canonical materialized artifact evidence")
    base_readiness = load_object(base_readiness_raw, "canonical B2P05 base readiness")
    readiness = load_object(readiness_raw, "candidate public readiness")
    evidence = load_object(evidence_raw, "B2P05 candidate revalidation evidence")

    require(evidence.get("schema_version") == "000b2-public-candidate-revalidation-v1", "B2P05 evidence schema drift")
    require(evidence.get("task") == "B2P05", "B2P05 task identity drift")
    require(evidence.get("canonical_base_sha") == CANONICAL_BASE_SHA, "B2P05 canonical base drift")
    require(evidence.get("candidate_registry") == str(REGISTRY_REL), "B2P05 registry path drift")
    require(evidence.get("candidate_registry_sha256") == EXPECTED_REGISTRY_SHA256, "B2P05 registry digest binding drift")
    require(evidence.get("materialized_artifact_evidence") == str(MATERIALIZED_REL), "B2P05 materialized-evidence path drift")
    require(evidence.get("artifact_size_amendment") == str(AMENDMENT_REL), "B2P05 amendment path drift")
    require(evidence.get("trusted_artifact_verifier") == str(TRUSTED_VERIFIER_REL), "B2P05 trusted-verifier path drift")
    require(materialized.get("registry_sha256") == EXPECTED_REGISTRY_SHA256, "canonical materialized evidence registry binding drift")

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

    contract = evidence.get("live_revalidation_contract")
    require(isinstance(contract, dict), "B2P05 live revalidation contract missing")
    for field in (
        "exact_runtime_release_and_revision_resolution_required",
        "all_canonical_artifact_bytes_must_match_recorded_size_and_sha256",
        "redirects_must_remain_within_the_existing_trusted_host_policy",
        "candidate_membership_must_not_change",
        "c0_repository_or_test_specific_context_must_remain_off",
    ):
        require(contract.get(field) is True, f"B2P05 live contract drift: {field}")

    phase = verify_readiness_phase(base_readiness, readiness)

    evidence_guards = evidence.get("guards")
    require(isinstance(evidence_guards, dict), "B2P05 evidence guards missing")
    for field in (
        "candidate_decoding_started",
        "primary_decoding_started",
        "b2p06_preprocessing_capture_started",
        "production_stt_selected",
        "product_code_authorized",
    ):
        require(evidence_guards.get(field) is False, f"B2P05 evidence guard drift: {field}")
    require(evidence_guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "B2P05 human-evidence guard drift")

    print(f"B2P05_CANONICAL_BASE={CANONICAL_BASE_SHA}")
    print(f"B2P05_CANONICAL_MERGE={B2P05_CANONICAL_MERGE}")
    print("B2P05_CANONICAL_AUTHORITY_INPUTS=UNCHANGED")
    print(f"B2P05_AUTHORITY_PHASE={phase}")
    print("B2P05_STATIC_AUTHORITY=PASS")
    print("B2P05_CANDIDATE_COUNT=6")
    print("B2P05_C0_CONTEXT_FREEZE=PASS")
    print("B2P05_LATER_GATES_CLOSED=PASS")
    return evidence, registry


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
    """Resolve a GitHub release tag through bounded annotated-tag indirection."""
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
    """Revalidate each canonical runtime release/tag and exact source revision live."""
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


def load_trusted_verifier(trusted_base_root: Path):
    """Load download and redirect policy only from the independent canonical base."""
    verifier_path = trusted_base_root.resolve(strict=True) / TRUSTED_VERIFIER_REL
    require(verifier_path.is_file() and not verifier_path.is_symlink(), "canonical trusted verifier is not a regular file")
    spec = importlib.util.spec_from_file_location("wispral_canonical_trusted_materialization", verifier_path)
    require(spec is not None and spec.loader is not None, "canonical trusted artifact verifier cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_prepinned_artifact_bytes(trusted_base_root: Path, registry: dict[str, Any]) -> None:
    """Re-download all pre-pinned model artifacts using canonical trusted redirect policy."""
    trusted = load_trusted_verifier(trusted_base_root)
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
    print("B2P05_PREPINNED_ARTIFACT_IDENTITIES=PASS")


def main() -> int:
    """Run static authority gates and optionally bounded live runtime/model revalidation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--trusted-base-root", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="revalidate runtime refs and pre-pinned model bytes")
    args = parser.parse_args()
    try:
        evidence, registry = verify_static_authority(args.trusted_base_root)
        if args.live:
            verify_runtime_pins(evidence)
            verify_prepinned_artifact_bytes(args.trusted_base_root, registry)
            print("B2P05_LIVE_REVALIDATION=PASS")
        else:
            print("B2P05_LIVE_REVALIDATION=NOT_RUN")
        print("B2P05_CANDIDATE_REVALIDATION_VERIFIER=PASS")
        return 0
    except RevalidationError as exc:
        print(f"B2P05_CANDIDATE_REVALIDATION_VERIFIER=FAIL: {exc}")
        return 1
    except Exception as exc:
        print(f"B2P05_CANDIDATE_REVALIDATION_VERIFIER=FAIL: unexpected {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
