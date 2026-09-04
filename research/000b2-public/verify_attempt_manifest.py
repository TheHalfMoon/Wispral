#!/usr/bin/env python3
"""Fail-closed verifier for the frozen B2P08 public-corpus attempt manifest."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/000b2-public"
MANIFEST_PATH = HERE / "attempt-manifest.json"
FREEZER_PATH = HERE / "freeze_attempt_manifest.py"
READINESS_PATH = HERE / "readiness.json"
TASKS_PATH = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
CURRENT_PATH = ROOT / "specs/CURRENT.md"
B2P07_RECONCILIATION_MERGE = "50ce9ac0ac3b3533d3df978a8b3a7e531f415b9c"
SHA256 = re.compile(r"^[0-9a-f]{64}$")

class VerificationError(ValueError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)

def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"unable to load {label}: {path}: {exc}") from exc
    require(isinstance(value, dict), f"{label} root must be an object")
    return value

def load_freezer():
    spec = importlib.util.spec_from_file_location("wispral_b2p08_freezer", FREEZER_PATH)
    require(spec is not None and spec.loader is not None, "unable to load B2P08 freezer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()

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

def main() -> int:
    manifest = load_json(MANIFEST_PATH, "B2P08 attempt manifest")
    freezer = load_freezer()

    require(manifest.get("schema_version") == "000b2-public-attempt-manifest-v1", "manifest schema drift")
    require(manifest.get("task") == "B2P08", "manifest task drift")
    require(manifest.get("lane") == "PUBLIC_CORPUS", "manifest lane drift")
    require(manifest.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-001", "attempt id drift")
    require(manifest.get("phase") == "PRE_PRIMARY_FROZEN", "manifest phase drift")
    require(manifest.get("frozen") is True, "attempt manifest must be frozen")
    digest = manifest.get("freeze_digest_sha256")
    require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None, "freeze digest malformed")
    require(digest == freezer.freeze_digest(manifest), "freeze digest mismatch")

    regenerated = freezer.build_manifest()
    require(
        freezer.render_json(regenerated) == MANIFEST_PATH.read_bytes(),
        "committed attempt manifest is not byte-identical to deterministic regeneration",
    )

    readiness = load_json(READINESS_PATH, "public readiness")
    require(readiness.get("state") == "READY", "public readiness drift")
    require(readiness.get("completed_through") == "B2P07", "B2P08 execution requires canonical completion through B2P07")
    environment = readiness.get("execution_environment")
    attempt = readiness.get("attempt_manifest")
    guards = readiness.get("claim_guards")
    require(isinstance(environment, dict) and environment.get("resolved") is True, "B2P07 environment must be resolved")
    require(isinstance(attempt, dict), "readiness attempt_manifest missing")
    require(attempt.get("frozen") is False, "canonical readiness must remain unreconciled during B2P08 execution PR")
    require(attempt.get("primary_decoding_started") is False, "primary decoding started before B2P08 canonical reconciliation")
    require(isinstance(guards, dict), "claim guards missing")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human evidence guard drift")
    require(guards.get("production_stt_selected") is False, "production STT selected during B2P08")
    require(guards.get("product_code_authorized") is False, "product code authorized during B2P08")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Execute B2P08 only:"), "B2P08 is not the sole canonical next action")

    tasks = TASKS_PATH.read_text(encoding="utf-8")
    current = CURRENT_PATH.read_text(encoding="utf-8")
    require("- [x] `B2P07`" in tasks, "B2P07 must remain complete")
    require("- [ ] `B2P08`" in tasks, "B2P08 task must remain unchecked until separate reconciliation")
    require("- [ ] `B2E01`" in tasks, "B2E01 must remain closed during B2P08")
    require("current bounded execution unit `B2P08`" in current, "CURRENT frontier must remain B2P08")
    require("Execute and canonically qualify `B2P08` only" in current, "CURRENT must authorize B2P08 only")
    require("Candidate and primary decoding remain unauthorized" in current, "CURRENT must keep decoding closed")

    authority = manifest.get("authority")
    scoring = manifest.get("scoring")
    decoding = manifest.get("decoding_contract")
    claims = manifest.get("claims")
    require(isinstance(authority, dict) and authority.get("b2p07_reconciliation_merge") == B2P07_RECONCILIATION_MERGE, "authority revision drift")
    require(isinstance(scoring, dict) and scoring.get("result_driven_changes_allowed") is False, "result-driven scorer changes allowed")
    require(scoring.get("ordinary_wer_source_panel_scope") == ["GENERAL_COLLATERAL"], "canonical scorer source scope drift")
    require(scoring.get("public_p0_relabels_source_panel") is False, "public P0 must not relabel the canonical source panel")
    require(
        scoring.get("public_p0_normalization")
        == {
            "unicode_representation": "NFC",
            "casefold": True,
            "punctuation_and_symbol_categories_to_space": ["P", "S"],
            "whitespace": "COLLAPSE_AND_SPLIT",
            "algorithm": "UNIT_COST_LEVENSHTEIN",
        },
        "public P0 normalization drift",
    )
    require(isinstance(decoding, dict), "decoding contract missing")
    require(decoding.get("candidate_decoding_started") is False, "candidate decoding started before freeze")
    require(decoding.get("primary_decoding_started") is False, "primary decoding started before freeze")
    require(decoding.get("identical_frozen_audio_required_across_candidates") is True, "identical-audio invariant drift")
    require(decoding.get("c0_repository_context") == "OFF", "C0 repository context drift")
    require(decoding.get("c0_test_specific_context") == "OFF", "C0 test-specific context drift")
    require(isinstance(claims, dict), "claim guards missing from manifest")
    require(claims.get("comparative_performance_authorized") is False, "DIAGNOSTIC timing cannot authorize comparative performance")
    require(claims.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human evidence guard drift")
    require(claims.get("human_developer_speech_ranking_authorized") is False, "human developer-speech ranking authorized")
    require(claims.get("production_stt_selected") is False, "production STT selected")
    require(claims.get("product_code_authorized") is False, "product code authorized")

    git("cat-file", "-e", f"{B2P07_RECONCILIATION_MERGE}^{{commit}}")
    git("merge-base", "--is-ancestor", B2P07_RECONCILIATION_MERGE, "HEAD")
    print("B2P08_ATTEMPT_MANIFEST_VERIFIER=PASS")
    print(f"B2P08_FREEZE_DIGEST={digest}")
    print("B2P08_FROZEN=YES")
    print("B2P08_CANDIDATE_DECODING_STARTED=NO")
    print("B2P08_PRIMARY_DECODING_STARTED=NO")
    print("B2E01_AUTHORIZED=NO_UNTIL_CANONICAL_RECONCILIATION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
