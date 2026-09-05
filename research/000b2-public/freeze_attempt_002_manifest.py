#!/usr/bin/env python3
"""Build the deterministic B2R04 ATTEMPT-002 pre-primary freeze manifest."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
ATTEMPT_002 = "000B2-PUBLIC-ATTEMPT-002"
B2R03_RECONCILIATION = "cd527d7e5a8361ff01cb11b85fe552986f44e742"

SOURCE_IDENTITIES = {
    "research/000b2-public/attempt-002-preexecution-state.json": (
        "1390fd4df3ec3c0599db68283b8e967be5f059232756302dcc3dfd8d09ca6734",
        "0e860485dae45cbc7b5f3c92d4f238983a9db285",
    ),
    "research/000b2-public/b2r03-preexecution-rebinding.json": (
        "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1",
        "49ba712b6a71ae69313c06b724833de1a95099b4",
    ),
    "research/000b2-public/subset-manifest.json": (
        "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb",
        "6acf7e787667512f08b2e7f333cc172310664a7e",
    ),
    "research/000b2-public/candidate-revalidation.json": (
        "aeca7b824d14388271b04c2dad953cecf5c47cd53cf3f70b766f4fe4dcac54b8",
        "5db133d2bf9c3085dcfec8f228ed5520e02f772e",
    ),
    "research/000b2-public/preprocessing-capture.json": (
        "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011",
        "89cbb28b7961042a1793c694692fe822c9414370",
    ),
    "research/000b2-public/execution-environment.json": (
        "2b8b521c28c771293648cbf86c7c1b20e820bacfc065074d7cfe2555745387ed",
        "caf814bcb5e42fd769e6df1d9a54c1164535f86c",
    ),
    "research/000b1/qualified-candidates.json": (
        "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f",
        "a77c442ae5d4dffa46a0494fbcffd56ecd772be3",
    ),
    "research/000b1/frozen-methodology.json": (
        "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df",
        "0eee1c15b5e3fc98edd09f1aae0547afd3c078b5",
    ),
    "research/000b2-entry/scorer.py": (
        "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1",
        "21e4c67c00da9a11fb402241444598a104f1f2a7",
    ),
    "research/000b2-entry/scorer-config.json": (
        "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3",
        "0634a3108ab0543fa1f8e9bc19015124feae7079",
    ),
    "research/000b2-public/b2r02-moonshine-streaming-qualification.json": (
        None,
        "90fb99d2c6ef1d7cd9d698e70a9e0a9837155bce",
    ),
}

CANDIDATES = [
    "moonshine-compact",
    "moonshine-balanced",
    "whispercpp-compact",
    "whispercpp-balanced",
    "sherpa-onnx-compact",
    "sherpa-onnx-balanced",
]


class FreezeError(RuntimeError):
    """Fail-closed B2R04 freeze error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise FreezeError(f"git {' '.join(args)} failed: {exc}") from exc


def verify_source_identities() -> None:
    git_output("cat-file", "-e", f"{B2R03_RECONCILIATION}^{{commit}}")
    git_output("merge-base", "--is-ancestor", B2R03_RECONCILIATION, "HEAD")
    for relative, (expected_sha256, expected_blob) in SOURCE_IDENTITIES.items():
        path = ROOT / relative
        require(path.is_file(), f"missing frozen source: {relative}")
        if expected_sha256 is not None:
            require(sha256_file(path) == expected_sha256, f"SHA-256 drift: {relative}")
        require(git_output("rev-parse", f"HEAD:{relative}") == expected_blob, f"Git blob drift: {relative}")


def build_manifest() -> dict[str, Any]:
    verify_source_identities()
    value: dict[str, Any] = {
        "schema_version": "000b2-public-attempt-002-manifest-v1",
        "task": "B2R04",
        "lane": "PUBLIC_CORPUS",
        "attempt_id": ATTEMPT_002,
        "phase": "PRE_PRIMARY_FROZEN",
        "frozen": True,
        "recovery_authority": {
            "b2r03_reconciliation_merge": B2R03_RECONCILIATION,
            "b2r03_task_merge": "6904fa7dd55e35c08e76044a18ebf9a95c65e038",
            "b2r03_post_merge_recovery_run_id": 33995766496,
            "preexecution_state": {
                "path": "research/000b2-public/attempt-002-preexecution-state.json",
                "sha256": "1390fd4df3ec3c0599db68283b8e967be5f059232756302dcc3dfd8d09ca6734",
                "git_blob_sha1": "0e860485dae45cbc7b5f3c92d4f238983a9db285",
            },
            "preexecution_rebinding": {
                "path": "research/000b2-public/b2r03-preexecution-rebinding.json",
                "sha256": "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1",
                "git_blob_sha1": "49ba712b6a71ae69313c06b724833de1a95099b4",
            },
        },
        "authority": {
            "subset": {
                "path": "research/000b2-public/subset-manifest.json",
                "sha256": "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb",
                "git_blob_sha1": "6acf7e787667512f08b2e7f333cc172310664a7e",
                "freeze_digest_sha256": "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242",
            },
            "candidate_revalidation": {
                "path": "research/000b2-public/candidate-revalidation.json",
                "sha256": "aeca7b824d14388271b04c2dad953cecf5c47cd53cf3f70b766f4fe4dcac54b8",
                "git_blob_sha1": "5db133d2bf9c3085dcfec8f228ed5520e02f772e",
                "candidate_registry_sha256": "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f",
            },
            "preprocessing": {
                "path": "research/000b2-public/preprocessing-capture.json",
                "sha256": "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011",
                "git_blob_sha1": "89cbb28b7961042a1793c694692fe822c9414370",
                "reuse_mode": "CRYPTOGRAPHIC_PROVENANCE_REBIND",
                "source_attempt_id": "000B2-PUBLIC-ATTEMPT-001",
                "bound_attempt_id": ATTEMPT_002,
            },
            "execution_environment": {
                "path": "research/000b2-public/execution-environment.json",
                "sha256": "2b8b521c28c771293648cbf86c7c1b20e820bacfc065074d7cfe2555745387ed",
                "git_blob_sha1": "caf814bcb5e42fd769e6df1d9a54c1164535f86c",
                "reuse_mode": "CRYPTOGRAPHIC_PROVENANCE_REBIND",
                "source_attempt_id": "000B2-PUBLIC-ATTEMPT-001",
                "bound_attempt_id": ATTEMPT_002,
                "environment_id": "x86_64:AMD EPYC 9V74 80-Core Processor:3e80c2c63bf88d13",
                "hardware_fingerprint_sha256": "3e80c2c63bf88d13a10c358feaa250672a5250fb9cbc90e59bdb397912cac5cd",
                "performance_mode": "DIAGNOSTIC",
                "comparative_performance_authorized": False,
            },
        },
        "candidate_set": {
            "b1_contract_version": "000b1-contract-v1",
            "candidate_ids": CANDIDATES,
            "count": len(CANDIDATES),
            "registry_path": "research/000b1/qualified-candidates.json",
            "registry_sha256": "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f",
            "registry_git_blob_sha1": "a77c442ae5d4dffa46a0494fbcffd56ecd772be3",
            "frozen_methodology_path": "research/000b1/frozen-methodology.json",
            "frozen_methodology_sha256": "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df",
            "frozen_methodology_git_blob_sha1": "0eee1c15b5e3fc98edd09f1aae0547afd3c078b5",
            "membership_change_after_freeze_allowed": False,
        },
        "corrected_c0": {
            "qualification_path": "research/000b2-public/b2r02-moonshine-streaming-qualification.json",
            "qualification_git_blob_sha1": "90fb99d2c6ef1d7cd9d698e70a9e0a9837155bce",
            "harness_path": "research/000b2-public/moonshine_streaming_c0.py",
            "harness_sha256": "c0f0093cda7ca036c8a97178364b3840ce7093386a8cb711ccef5f183a4453c0",
            "runtime_revision": "234f60faa0eb388b01cdf7e60aca232af37aefda",
            "runtime_distribution": "moonshine-voice",
            "runtime_distribution_version": "0.1.5",
            "model_asset_revision": "quantized_26_08_21",
        },
        "scoring": {
            "core_scorer_path": "research/000b2-entry/scorer.py",
            "core_scorer_sha256": "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1",
            "core_scorer_git_blob_sha1": "21e4c67c00da9a11fb402241444598a104f1f2a7",
            "core_config_path": "research/000b2-entry/scorer-config.json",
            "core_config_sha256": "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3",
            "core_config_git_blob_sha1": "0634a3108ab0543fa1f8e9bc19015124feae7079",
            "public_wer_adapter_path": "research/000b2-public/score_public_wer.py",
            "public_wer_adapter_sha256": "581a0e4b0bb91d55a252b92871dbb1246b5fbc4466a5d94bceb35862744fc023",
            "ordinary_wer_source_panel_scope": ["GENERAL_COLLATERAL"],
            "public_p0_relabels_source_panel": False,
            "public_p0_normalization": {
                "unicode_representation": "NFC",
                "casefold": True,
                "punctuation_and_symbol_categories_to_space": ["P", "S"],
                "whitespace": "COLLAPSE_AND_SPLIT",
                "algorithm": "UNIT_COST_LEVENSHTEIN",
            },
            "result_driven_changes_allowed": False,
        },
        "decoding_contract": {
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
            "identical_frozen_audio_required_across_candidates": True,
            "c0_repository_context": "OFF",
            "c0_test_specific_context": "OFF",
            "candidate_specific_audio_transform": "OFF",
            "raw_outputs_and_failures_must_be_preserved": True,
            "candidate_run_runtime_observations_must_be_preserved_separately": True,
        },
        "claims": {
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "comparative_result_available": False,
            "comparative_performance_authorized": False,
            "human_developer_speech_ranking_authorized": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
            "b2r05_authorized": False,
        },
    }
    value["freeze_digest_sha256"] = freeze_digest(value)
    return value


def freeze_digest(value: dict[str, Any]) -> str:
    canonical = copy.deepcopy(value)
    canonical.pop("freeze_digest_sha256", None)
    payload = (json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def render_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--committed", type=Path)
    args = parser.parse_args()

    rendered = render_json(build_manifest())
    if args.committed is not None:
        require(args.committed.read_bytes() == rendered, "committed ATTEMPT-002 manifest is not deterministic")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rendered)
    print("B2R04_ATTEMPT_002_FREEZER=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
