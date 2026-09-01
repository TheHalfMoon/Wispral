#!/usr/bin/env python3
"""Fail-closed validator for a Wispral 000B2 attempt manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "qualified-candidates.json"
METHODOLOGY_PATH = HERE / "frozen-methodology.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
OFF = {False, None, "OFF", "NONE", "", 0}
ALLOWED_EXCLUSION_REASONS = {
    "LICENSE_OR_PROVENANCE_UNRESOLVED",
    "ARTIFACT_IDENTITY_UNRESOLVED",
    "ARTIFACT_UNAVAILABLE",
    "NO_LOCAL_ENGLISH_PATH",
    "BUILD_OR_INSTALL_UNREPRODUCIBLE",
    "OUTSIDE_PRODUCT_ENVELOPE",
    "HOSTED_INFERENCE_REQUIRED",
    "C0_FAIRNESS_UNRESOLVABLE",
    "OPERATIONAL_QUALIFICATION_FAILED",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(manifest: dict) -> str:
    obj = dict(manifest)
    obj["freeze_digest_sha256"] = None
    raw = (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def sha256(value) -> bool:
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def git_sha(value) -> bool:
    return isinstance(value, str) and bool(GIT_SHA.fullmatch(value))


def frozen_authority():
    registry = load(REGISTRY_PATH)
    methodology = load(METHODOLOGY_PATH)
    expected = {}
    for family in registry["families"]:
        family_name = family["family"]
        runtime_revision = family["runtime"]["revision"]
        family_c0 = methodology["c0_by_family"][family_name]
        for cfg in family["configurations"]:
            expected[cfg["id"]] = {
                "family": family_name,
                "tier": cfg["tier"],
                "runtime_revision": runtime_revision,
                "artifacts": {
                    artifact["path"]: {
                        "size_bytes": artifact["size_bytes"],
                        "sha256": artifact.get("sha256"),
                        "sha256_status": artifact.get("sha256_status"),
                    }
                    for artifact in cfg["artifacts"]
                },
                "c0": {
                    "common": methodology["common_c0"],
                    "family": family_c0,
                },
            }
    return registry, methodology, expected


def add_blocker(blockers: list[str], message: str) -> None:
    if message not in blockers:
        blockers.append(message)


def validate(m: dict, require_ready: bool = False):
    errors: list[str] = []
    blockers: list[str] = []
    registry, methodology, expected_cells = frozen_authority()

    required = {
        "schema_version",
        "attempt_id",
        "canonical_wispral_revision",
        "b1_contract_version",
        "qualified_candidates_sha256",
        "frozen_methodology_sha256",
        "frozen",
        "freeze_digest_sha256",
        "primary_test_decoding_started",
        "candidates",
        "exclusions",
        "corpus",
        "preprocessing",
        "scorer",
        "execution_environment",
        "claims",
    }
    missing = sorted(required - set(m))
    if missing:
        return [f"missing fields: {', '.join(missing)}"], blockers

    if m["schema_version"] != "000b2-attempt-manifest-v1":
        errors.append("schema_version drift")
    if m["b1_contract_version"] != registry["contract_version"]:
        errors.append("b1_contract_version drift")
    if not git_sha(m["canonical_wispral_revision"]):
        errors.append("invalid canonical_wispral_revision")

    expected_registry_sha = file_sha256(REGISTRY_PATH)
    registry_sha = m.get("qualified_candidates_sha256")
    if registry_sha is None:
        add_blocker(blockers, "qualified candidate registry digest not pinned")
    elif not sha256(registry_sha):
        errors.append("qualified_candidates_sha256 malformed")
    elif registry_sha != expected_registry_sha:
        errors.append("qualified_candidates_sha256 does not match frozen registry")

    expected_methodology_sha = file_sha256(METHODOLOGY_PATH)
    methodology_sha = m.get("frozen_methodology_sha256")
    if methodology_sha is None:
        add_blocker(blockers, "frozen methodology digest not pinned")
    elif not sha256(methodology_sha):
        errors.append("frozen_methodology_sha256 malformed")
    elif methodology_sha != expected_methodology_sha:
        errors.append("frozen_methodology_sha256 does not match frozen methodology")

    candidates = m["candidates"]
    if not isinstance(candidates, list):
        errors.append("candidates must be an array")
        candidates = []

    selected_ids: set[str] = set()
    for i, candidate in enumerate(candidates):
        p = f"candidate[{i}]"
        if not isinstance(candidate, dict):
            errors.append(f"{p} must be an object")
            continue
        cid = candidate.get("candidate_id")
        if not cid or cid in selected_ids:
            errors.append(f"{p} candidate_id missing/duplicate")
            continue
        selected_ids.add(cid)
        registered = expected_cells.get(cid)
        if registered is None:
            errors.append(f"{p} candidate_id is not in qualified-candidates.json")
            continue

        if candidate.get("family") != registered["family"]:
            errors.append(f"{p} family drift from frozen registry")
        if candidate.get("tier") != registered["tier"]:
            errors.append(f"{p} tier drift from frozen registry")
        if candidate.get("runtime_revision") != registered["runtime_revision"]:
            errors.append(f"{p} runtime_revision drift from frozen registry")
        if candidate.get("c0") != registered["c0"]:
            errors.append(f"{p}.c0 does not exactly match frozen methodology")

        artifacts = candidate.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"{p} artifacts missing")
        else:
            actual_paths: set[str] = set()
            for j, artifact in enumerate(artifacts):
                ap = f"{p}.artifacts[{j}]"
                if not isinstance(artifact, dict):
                    errors.append(f"{ap} must be an object")
                    continue
                path = artifact.get("path")
                if not path or path in actual_paths:
                    errors.append(f"{ap} path missing/duplicate")
                    continue
                actual_paths.add(path)
                registered_artifact = registered["artifacts"].get(path)
                if registered_artifact is None:
                    errors.append(f"{ap} is not in the frozen artifact registry")
                    continue
                if artifact.get("size_bytes") != registered_artifact["size_bytes"]:
                    errors.append(f"{ap} size_bytes drift from frozen registry")
                value = artifact.get("sha256")
                pinned = registered_artifact.get("sha256")
                if pinned is not None:
                    if value != pinned:
                        errors.append(f"{ap} SHA-256 differs from frozen pinned artifact")
                elif value is not None and not sha256(value):
                    errors.append(f"{ap} malformed SHA-256")
                if m["frozen"] and not sha256(value):
                    add_blocker(blockers, f"{ap} SHA-256 not materialized")
            expected_paths = set(registered["artifacts"])
            missing_paths = sorted(expected_paths - actual_paths)
            extra_paths = sorted(actual_paths - expected_paths)
            if missing_paths:
                errors.append(f"{p} missing frozen artifacts: {', '.join(missing_paths)}")
            if extra_paths:
                errors.append(f"{p} contains unregistered artifacts: {', '.join(extra_paths)}")

        operational = candidate.get("operational_qualification")
        if not isinstance(operational, dict):
            add_blocker(blockers, f"{p} operational qualification missing")
        else:
            status = operational.get("status")
            evidence_sha = operational.get("evidence_sha256")
            waiver_revision = operational.get("canonical_waiver_revision")
            if status == "SMOKE_PASS":
                if not sha256(evidence_sha):
                    add_blocker(blockers, f"{p} smoke PASS evidence not pinned")
                if waiver_revision is not None:
                    errors.append(f"{p} smoke PASS must not carry a waiver revision")
            elif status == "CANONICAL_WAIVER":
                if not sha256(evidence_sha):
                    add_blocker(blockers, f"{p} waiver evidence not pinned")
                if not git_sha(waiver_revision):
                    add_blocker(blockers, f"{p} canonical waiver revision not pinned")
            elif status in {"NOT_RUN", "FAILED"}:
                add_blocker(blockers, f"{p} operational qualification is {status}")
            else:
                errors.append(f"{p} invalid operational qualification status")

    exclusions = m["exclusions"]
    if not isinstance(exclusions, list):
        errors.append("exclusions must be an array")
        exclusions = []
    excluded_ids: set[str] = set()
    for i, exclusion in enumerate(exclusions):
        p = f"exclusion[{i}]"
        if not isinstance(exclusion, dict):
            errors.append(f"{p} must be an object")
            continue
        cid = exclusion.get("candidate_id")
        if cid not in expected_cells:
            errors.append(f"{p} candidate_id is not in qualified-candidates.json")
            continue
        if cid in excluded_ids:
            errors.append(f"{p} duplicate exclusion")
        excluded_ids.add(cid)
        if cid in selected_ids:
            errors.append(f"{p} candidate is both selected and excluded")
        if exclusion.get("reason_code") not in ALLOWED_EXCLUSION_REASONS:
            errors.append(f"{p} exclusion reason is not allowed")
        rationale = exclusion.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"{p} exclusion rationale missing")
        if not sha256(exclusion.get("evidence_sha256")):
            add_blocker(blockers, f"{p} exclusion evidence not pinned")
        if not git_sha(exclusion.get("canonical_revision")):
            add_blocker(blockers, f"{p} exclusion canonical revision not pinned")

    expected_ids = set(expected_cells)
    covered_ids = selected_ids | excluded_ids
    missing_ids = sorted(expected_ids - covered_ids)
    if missing_ids:
        errors.append(
            "frozen candidate cells omitted without allowed pre-freeze exclusion: "
            + ", ".join(missing_ids)
        )
    if covered_ids - expected_ids:
        errors.append("manifest contains unregistered candidate cells")

    corpus = m["corpus"]
    if corpus.get("synthetic_primary_ranking") is not False:
        errors.append("synthetic_primary_ranking must be false")
    if corpus.get("authority_status") != "AUTHORIZED":
        add_blocker(blockers, "human developer-speech authority not AUTHORIZED")
    if not sha256(corpus.get("consent_records_sha256")):
        add_blocker(blockers, "consent_records_sha256 not pinned")
    if not sha256(corpus.get("primary_test_manifest_sha256")):
        add_blocker(blockers, "primary_test_manifest_sha256 not pinned")

    prep = m["preprocessing"]
    frozen_prep = methodology["preprocessing"]
    prep_expected = {
        "tool": frozen_prep["tool"],
        "tool_version": frozen_prep["version"],
        "tool_source_commit": frozen_prep["source_commit"],
        "canonical_format": frozen_prep["canonical_format"],
        "sample_rate_hz": frozen_prep["sample_rate_hz"],
        "channels": frozen_prep["channels"],
        "sample_format": frozen_prep["sample_format"],
        "denoising": frozen_prep["denoising"],
        "loudness_normalization": frozen_prep["loudness_normalization"],
        "semantic_silence_trim": frozen_prep["semantic_silence_trim"],
        "feed_chunk_ms": frozen_prep["feed_chunk_ms"],
        "finalization_zero_pad_ms": frozen_prep["finalization_zero_pad_ms"],
    }
    for key, expected in prep_expected.items():
        if prep.get(key) != expected:
            errors.append(f"preprocessing.{key} drift from frozen methodology")
    if not prep.get("revision") or not sha256(prep.get("config_sha256")):
        add_blocker(blockers, "preprocessing revision/config not frozen")
    if not sha256(prep.get("binary_sha256")):
        add_blocker(blockers, "preprocessing binary SHA-256 not pinned")
    if not sha256(prep.get("version_output_sha256")):
        add_blocker(blockers, "preprocessing version-output SHA-256 not pinned")

    scorer = m["scorer"]
    if not scorer.get("revision") or not sha256(scorer.get("config_sha256")):
        add_blocker(blockers, "scorer revision/config not frozen")

    environment = m["execution_environment"]
    claims = m["claims"]
    if not environment.get("environment_id") or not sha256(
        environment.get("hardware_fingerprint_sha256")
    ):
        add_blocker(blockers, "execution environment not frozen")
    if (
        claims.get("comparative_performance_authorized")
        and environment.get("performance_mode") != "CONTROLLED"
    ):
        errors.append("comparative performance requires CONTROLLED environment")
    if (
        claims.get("human_developer_speech_ranking_authorized")
        and corpus.get("authority_status") != "AUTHORIZED"
    ):
        errors.append("human ranking authorized without corpus authority")

    if not m["frozen"]:
        add_blocker(blockers, "manifest not frozen")
        if m.get("freeze_digest_sha256") is not None:
            errors.append("unfrozen manifest must use null freeze_digest_sha256")
    else:
        if not sha256(m.get("freeze_digest_sha256")):
            add_blocker(blockers, "freeze_digest_sha256 not pinned")
        elif m["freeze_digest_sha256"] != digest(m):
            errors.append("freeze_digest_sha256 mismatch")

    if not claims.get("human_developer_speech_ranking_authorized"):
        add_blocker(blockers, "human ranking not authorized")
    if m.get("primary_test_decoding_started"):
        add_blocker(blockers, "primary test decoding already started; readiness is an entry-state gate")

    if require_ready and blockers:
        errors.extend(f"BLOCKER: {blocker}" for blocker in blockers)
    return errors, blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--print-freeze-digest", action="store_true")
    args = parser.parse_args()
    manifest = load(args.manifest)
    if args.print_freeze_digest:
        print(digest(manifest))
        return 0
    errors, blockers = validate(manifest, args.require_ready)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("STRUCTURE=PASS")
    print(f"B2_READY={'NO' if blockers else 'YES'}")
    for blocker in blockers:
        print(f"BLOCKER={blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
