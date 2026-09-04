#!/usr/bin/env python3
"""Freeze the B2P08 public-corpus pre-decode attempt manifest without decoding."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/000b2-public"
ENTRY = ROOT / "research/000b2-entry"
B1 = ROOT / "research/000b1"

ATTEMPT_STATE_PATH = HERE / "predecode-attempt-state.json"
SUBSET_PATH = HERE / "subset-manifest.json"
CANDIDATE_REVALIDATION_PATH = HERE / "candidate-revalidation.json"
PREPROCESSING_PATH = HERE / "preprocessing-capture.json"
ENVIRONMENT_PATH = HERE / "execution-environment.json"
REGISTRY_PATH = B1 / "qualified-candidates.json"
FROZEN_METHODOLOGY_PATH = B1 / "frozen-methodology.json"
SCORER_PATH = ENTRY / "scorer.py"
SCORER_CONFIG_PATH = ENTRY / "scorer-config.json"
PUBLIC_WER_PATH = HERE / "score_public_wer.py"
DEFAULT_OUTPUT = HERE / "attempt-manifest.json"

B2P07_RECONCILIATION_MERGE = "50ce9ac0ac3b3533d3df978a8b3a7e531f415b9c"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-001"
EXPECTED_ATTEMPT_STATE_SHA256 = "2392ab6694ab56facd8eb1f00c095a5727e51cae90d6553e0eca32b7626a85de"
EXPECTED_ATTEMPT_STATE_BLOB = "048b5ed349948a779c2fa388d1e383a065d10f33"
EXPECTED_SUBSET_SHA256 = "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb"
EXPECTED_SUBSET_BLOB = "6acf7e787667512f08b2e7f333cc172310664a7e"
EXPECTED_SUBSET_FREEZE_DIGEST = "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242"
EXPECTED_REGISTRY_SHA256 = "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f"
EXPECTED_REGISTRY_BLOB = "a77c442ae5d4dffa46a0494fbcffd56ecd772be3"
EXPECTED_FROZEN_METHODOLOGY_BLOB = "0eee1c15b5e3fc98edd09f1aae0547afd3c078b5"
EXPECTED_CANDIDATE_REVALIDATION_BLOB = "5db133d2bf9c3085dcfec8f228ed5520e02f772e"
EXPECTED_PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_PREPROCESSING_BLOB = "89cbb28b7961042a1793c694692fe822c9414370"
EXPECTED_ENVIRONMENT_BLOB = "caf814bcb5e42fd769e6df1d9a54c1164535f86c"
EXPECTED_SCORER_BLOB = "21e4c67c00da9a11fb402241444598a104f1f2a7"
EXPECTED_SCORER_CONFIG_BLOB = "0634a3108ab0543fa1f8e9bc19015124feae7079"
EXPECTED_CANDIDATES = [
    "moonshine-compact",
    "moonshine-balanced",
    "whispercpp-compact",
    "whispercpp-balanced",
    "sherpa-onnx-compact",
    "sherpa-onnx-balanced",
]

class FreezeError(ValueError):
    """Raised when B2P08 cannot prove one immutable pre-decode freeze."""

def require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)

def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezeError(f"unable to load {label}: {path}: {exc}") from exc
    require(isinstance(value, dict), f"{label} root must be an object")
    return value

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()

def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

def render_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

def freeze_digest(value: dict[str, Any]) -> str:
    projection = copy.deepcopy(value)
    require("freeze_digest_sha256" in projection, "freeze digest field missing")
    projection["freeze_digest_sha256"] = None
    return hashlib.sha256(canonical_json_bytes(projection)).hexdigest()

def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()

def canonical_blob(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return git("rev-parse", f"{B2P07_RECONCILIATION_MERGE}:{relative}")

def verify_authority_bytes() -> None:
    git("cat-file", "-e", f"{B2P07_RECONCILIATION_MERGE}^{{commit}}")
    git("merge-base", "--is-ancestor", B2P07_RECONCILIATION_MERGE, "HEAD")

    expected_blobs = {
        ATTEMPT_STATE_PATH: EXPECTED_ATTEMPT_STATE_BLOB,
        SUBSET_PATH: EXPECTED_SUBSET_BLOB,
        CANDIDATE_REVALIDATION_PATH: EXPECTED_CANDIDATE_REVALIDATION_BLOB,
        PREPROCESSING_PATH: EXPECTED_PREPROCESSING_BLOB,
        ENVIRONMENT_PATH: EXPECTED_ENVIRONMENT_BLOB,
        REGISTRY_PATH: EXPECTED_REGISTRY_BLOB,
        FROZEN_METHODOLOGY_PATH: EXPECTED_FROZEN_METHODOLOGY_BLOB,
        SCORER_PATH: EXPECTED_SCORER_BLOB,
        SCORER_CONFIG_PATH: EXPECTED_SCORER_CONFIG_BLOB,
    }
    for path, expected_blob in expected_blobs.items():
        actual = canonical_blob(path)
        require(actual == expected_blob, f"canonical blob drift: {path.relative_to(ROOT)}")
        current = git("rev-parse", f"HEAD:{path.relative_to(ROOT).as_posix()}")
        require(current == expected_blob, f"B2P08 must not modify prior authority bytes: {path.relative_to(ROOT)}")

def build_manifest() -> dict[str, Any]:
    verify_authority_bytes()

    attempt_state = load_json(ATTEMPT_STATE_PATH, "predecode attempt state")
    subset = load_json(SUBSET_PATH, "subset manifest")
    revalidation = load_json(CANDIDATE_REVALIDATION_PATH, "candidate revalidation")
    preprocessing = load_json(PREPROCESSING_PATH, "preprocessing capture")
    environment = load_json(ENVIRONMENT_PATH, "execution environment")
    registry = load_json(REGISTRY_PATH, "qualified candidate registry")
    methodology = load_json(FROZEN_METHODOLOGY_PATH, "frozen methodology")
    scorer_config = load_json(SCORER_CONFIG_PATH, "scorer config")

    require(sha256_file(ATTEMPT_STATE_PATH) == EXPECTED_ATTEMPT_STATE_SHA256, "attempt-state bytes drift")
    require(sha256_file(SUBSET_PATH) == EXPECTED_SUBSET_SHA256, "subset-manifest bytes drift")
    require(sha256_file(REGISTRY_PATH) == EXPECTED_REGISTRY_SHA256, "candidate-registry bytes drift")
    require(sha256_file(PREPROCESSING_PATH) == EXPECTED_PREPROCESSING_SHA256, "preprocessing evidence bytes drift")

    require(attempt_state.get("attempt_id") == ATTEMPT_ID, "attempt id drift")
    require(attempt_state.get("phase") == "PRE_PRIMARY_CAPTURE", "attempt phase drift")
    require(attempt_state.get("candidate_decoding_started") is False, "candidate decoding started before B2P08 freeze")
    require(attempt_state.get("primary_test_decoding_started") is False, "primary decoding started before B2P08 freeze")
    require(subset.get("frozen") is True, "B2P04 subset is not frozen")
    require(subset.get("freeze_digest_sha256") == EXPECTED_SUBSET_FREEZE_DIGEST, "B2P04 freeze digest drift")

    candidate_ids = revalidation.get("candidate_ids")
    require(candidate_ids == EXPECTED_CANDIDATES, "B2P05 candidate ordering/membership drift")
    require(registry.get("contract_version") == methodology.get("contract_version"), "B1 registry/methodology contract drift")

    claim_guards = environment.get("claim_guards")
    env = environment.get("environment")
    require(isinstance(claim_guards, dict) and isinstance(env, dict), "B2P07 environment shape drift")
    require(claim_guards.get("candidate_decoding_started") is False, "candidate decoding started before B2P08")
    require(claim_guards.get("primary_decoding_started") is False, "primary decoding started before B2P08")
    require(claim_guards.get("b2p08_attempt_manifest_frozen") is False, "historical B2P07 evidence must predate B2P08 freeze")
    require(claim_guards.get("comparative_performance_authorized") is False, "GitHub timing must not authorize comparison")
    require(claim_guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human evidence guard drift")
    require(claim_guards.get("production_stt_selected") is False, "production STT selected before B2P08")
    require(claim_guards.get("product_code_authorized") is False, "product code authorized before B2P08")
    require(env.get("performance_mode") == "DIAGNOSTIC", "B2P07 environment must remain DIAGNOSTIC")
    require(env.get("comparative_performance_authorized") is False, "B2P07 comparative performance guard drift")

    ordinary = scorer_config.get("ordinary_wer")
    require(isinstance(ordinary, dict), "ordinary WER scorer config missing")
    expected_ordinary = {
        "panels": ["GENERAL_COLLATERAL"],
        "unicode_representation": "NFC",
        "casefold": True,
        "punctuation_and_symbol_categories_to_space": ["P", "S"],
        "whitespace": "COLLAPSE_AND_SPLIT",
        "algorithm": "UNIT_COST_LEVENSHTEIN",
    }
    require(ordinary == expected_ordinary, "ordinary WER normalization drift")

    manifest: dict[str, Any] = {
        "schema_version": "000b2-public-attempt-manifest-v1",
        "task": "B2P08",
        "lane": "PUBLIC_CORPUS",
        "attempt_id": ATTEMPT_ID,
        "phase": "PRE_PRIMARY_FROZEN",
        "frozen": True,
        "freeze_digest_sha256": None,
        "authority": {
            "b2p07_reconciliation_merge": B2P07_RECONCILIATION_MERGE,
            "attempt_state": {
                "path": ATTEMPT_STATE_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(ATTEMPT_STATE_PATH),
                "attempt_origin_revision": attempt_state["canonical_wispral_revision"],
                "phase": attempt_state["phase"],
            },
            "subset": {
                "path": SUBSET_PATH.relative_to(ROOT).as_posix(),
                "git_blob_sha1": EXPECTED_SUBSET_BLOB,
                "sha256": sha256_file(SUBSET_PATH),
                "freeze_digest_sha256": subset["freeze_digest_sha256"],
            },
            "candidate_revalidation": {
                "path": CANDIDATE_REVALIDATION_PATH.relative_to(ROOT).as_posix(),
                "git_blob_sha1": EXPECTED_CANDIDATE_REVALIDATION_BLOB,
                "sha256": sha256_file(CANDIDATE_REVALIDATION_PATH),
                "candidate_registry_sha256": revalidation["candidate_registry_sha256"],
            },
            "preprocessing": {
                "path": PREPROCESSING_PATH.relative_to(ROOT).as_posix(),
                "git_blob_sha1": EXPECTED_PREPROCESSING_BLOB,
                "sha256": sha256_file(PREPROCESSING_PATH),
            },
            "execution_environment": {
                "path": ENVIRONMENT_PATH.relative_to(ROOT).as_posix(),
                "git_blob_sha1": EXPECTED_ENVIRONMENT_BLOB,
                "sha256": sha256_file(ENVIRONMENT_PATH),
                "environment_id": env["environment_id"],
                "hardware_fingerprint_sha256": env["hardware_fingerprint_sha256"],
                "performance_mode": env["performance_mode"],
                "comparative_performance_authorized": False,
            },
        },
        "candidate_set": {
            "registry_path": REGISTRY_PATH.relative_to(ROOT).as_posix(),
            "registry_git_blob_sha1": EXPECTED_REGISTRY_BLOB,
            "registry_sha256": sha256_file(REGISTRY_PATH),
            "frozen_methodology_path": FROZEN_METHODOLOGY_PATH.relative_to(ROOT).as_posix(),
            "frozen_methodology_git_blob_sha1": EXPECTED_FROZEN_METHODOLOGY_BLOB,
            "frozen_methodology_sha256": sha256_file(FROZEN_METHODOLOGY_PATH),
            "b1_contract_version": methodology["contract_version"],
            "count": len(EXPECTED_CANDIDATES),
            "candidate_ids": EXPECTED_CANDIDATES,
            "membership_change_after_freeze_allowed": False,
        },
        "scoring": {
            "core_scorer_path": SCORER_PATH.relative_to(ROOT).as_posix(),
            "core_scorer_git_blob_sha1": EXPECTED_SCORER_BLOB,
            "core_scorer_sha256": sha256_file(SCORER_PATH),
            "core_config_path": SCORER_CONFIG_PATH.relative_to(ROOT).as_posix(),
            "core_config_git_blob_sha1": EXPECTED_SCORER_CONFIG_BLOB,
            "core_config_sha256": sha256_file(SCORER_CONFIG_PATH),
            "ordinary_wer_source_panel_scope": expected_ordinary["panels"],
            "public_wer_adapter_path": PUBLIC_WER_PATH.relative_to(ROOT).as_posix(),
            "public_wer_adapter_sha256": sha256_file(PUBLIC_WER_PATH),
            "public_p0_normalization": {
                key: value for key, value in expected_ordinary.items() if key != "panels"
            },
            "public_p0_relabels_source_panel": False,
            "result_driven_changes_allowed": False,
        },
        "decoding_contract": {
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
            "c0_repository_context": "OFF",
            "c0_test_specific_context": "OFF",
            "candidate_specific_audio_transform": "OFF",
            "identical_frozen_audio_required_across_candidates": True,
            "raw_outputs_and_failures_must_be_preserved": True,
        },
        "claims": {
            "comparative_performance_authorized": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "human_developer_speech_ranking_authorized": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
    }
    manifest["freeze_digest_sha256"] = freeze_digest(manifest)
    return manifest

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--committed", type=Path)
    args = parser.parse_args()

    manifest = build_manifest()
    rendered = render_json(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rendered)

    print("B2P08_ATTEMPT_FREEZE=PASS")
    print(f"B2P08_ATTEMPT_ID={ATTEMPT_ID}")
    print(f"B2P08_FREEZE_DIGEST={manifest['freeze_digest_sha256']}")
    print("B2P08_CANDIDATE_DECODING_STARTED=NO")
    print("B2P08_PRIMARY_DECODING_STARTED=NO")
    print("B2P08_COMPARATIVE_PERFORMANCE_AUTHORIZED=NO")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")

    if args.committed is not None:
        committed = args.committed.read_bytes()
        require(committed == rendered, "committed B2P08 attempt manifest is not byte-identical to deterministic freeze")
        print("B2P08_COMMITTED_MANIFEST=BYTE_IDENTICAL")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
