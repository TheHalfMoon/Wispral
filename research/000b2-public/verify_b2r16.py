#!/usr/bin/env python3
"""Verify the bounded B2R16 ATTEMPT-003 pre-primary freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
READINESS = PUBLIC / "recovery-attempt-003-readiness.json"
CURRENT = ROOT / "specs" / "CURRENT.md"
CURRENT_STATE = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
PRESTATE = PUBLIC / "b2r16-preexecution-state.json"
MANIFEST = PUBLIC / "b2r16-attempt-003-manifest.json"
PREPROCESSING_REBIND = PUBLIC / "b2r15-preprocessing-rebinding.json"
ENVIRONMENT_REBIND = PUBLIC / "b2r15-environment-rebinding.json"
B2R15_PROVENANCE = PUBLIC / "b2r15-provenance.json"
B2R14_HARNESS = PUBLIC / "b2r14-sherpa-result-harness.py"
B2R14_QUALIFICATION = PUBLIC / "b2r14-harness-qualification.json"
CANDIDATE_REVALIDATION = PUBLIC / "candidate-revalidation.json"
SUBSET = PUBLIC / "subset-manifest.json"
CANDIDATE_REGISTRY = ROOT / "research" / "000b1" / "qualified-candidates.json"
FROZEN_METHODOLOGY = ROOT / "research" / "000b1" / "frozen-methodology.json"
CORE_SCORER = ROOT / "research" / "000b2-entry" / "scorer.py"
CORE_CONFIG = ROOT / "research" / "000b2-entry" / "scorer-config.json"
PUBLIC_WER = PUBLIC / "score_public_wer.py"

TASK = "B2R16"
ATTEMPT = "000B2-PUBLIC-ATTEMPT-003"
AUTHORITY_BASE = "8132b25479643dc955eb4d022400a9e9b36b4261"
PREDECESSOR_TASK = "B2R15"
PREDECESSOR_TASK_MERGE = "3d31b18823b8275c99e1478b132a64f36fad05c0"
PREDECESSOR_POSTMERGE_RUN = 34274935240
PREDECESSOR_RECONCILIATION = AUTHORITY_BASE
PRESTATE_SHA256 = "cf62c57d6948242e973bd526cfc6955530d0c334fa9f9633c3779c83687b341c"
PRESTATE_BLOB = "78546da56a36b00f77ecab9adb311bf4f32a827f"
MANIFEST_SHA256 = "4dc8074417679554d37ef67f38a8571faf561ead3efa4af5f2f285ab5f4b6048"
MANIFEST_BLOB = "a0e22d11a5dc02c4bb06c1c0eaa3a5d8defbfb72"
FREEZE_DIGEST = "9bb596d496831f919a9eab0f263ec88e6ff8134ae126c9664e23ae5317d0cabc"

EXPECTED_SCOPE = [
    ".github/workflows/000b2-public-b2r16-freeze.yml",
    "research/000b2-public/b2r16-attempt-003-manifest.json",
    "research/000b2-public/b2r16-preexecution-state.json",
    "research/000b2-public/verify_b2r16.py",
]
CANDIDATE_IDS = [
    "moonshine-compact", "moonshine-balanced", "whispercpp-compact",
    "whispercpp-balanced", "sherpa-onnx-compact", "sherpa-onnx-balanced",
]
IDENTITIES = {
    "candidate_revalidation": {"path": CANDIDATE_REVALIDATION, "sha256": "aeca7b824d14388271b04c2dad953cecf5c47cd53cf3f70b766f4fe4dcac54b8", "blob": "5db133d2bf9c3085dcfec8f228ed5520e02f772e"},
    "subset": {"path": SUBSET, "sha256": "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb", "blob": "6acf7e787667512f08b2e7f333cc172310664a7e"},
    "candidate_registry": {"path": CANDIDATE_REGISTRY, "sha256": "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f", "blob": "a77c442ae5d4dffa46a0494fbcffd56ecd772be3"},
    "frozen_methodology": {"path": FROZEN_METHODOLOGY, "sha256": "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df", "blob": "0eee1c15b5e3fc98edd09f1aae0547afd3c078b5"},
    "preprocessing_rebind": {"path": PREPROCESSING_REBIND, "sha256": "c44bbbf6d20aaec671d48c083eb76cfb6889a3c50486bd9da94c25b2b8f8039f", "blob": "697d3a19d8b48805e445157c07a333866e03c4cc"},
    "environment_rebind": {"path": ENVIRONMENT_REBIND, "sha256": "0a6b32abae50da0d3d16f850a8e59edde0cb24f9489ce726054d6cf06e03532c", "blob": "628965b646c763ccd031370187730c359c6aaf83"},
    "b2r15_provenance": {"path": B2R15_PROVENANCE, "blob": "a15a81618ab132812f064525045a6d6bcfed69db"},
    "b2r14_harness": {"path": B2R14_HARNESS, "sha256": "388b1480de6caed4adaad5d88cf3d275a5a4b1d35bd99e00f466581958886e39", "blob": "7f0d76bf2490a254d515409d39585f6c9296cfa9"},
    "b2r14_qualification": {"path": B2R14_QUALIFICATION, "blob": "b9c5b807c0a98e990991213f517b7e43854c17c5"},
    "core_scorer": {"path": CORE_SCORER, "sha256": "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1", "blob": "21e4c67c00da9a11fb402241444598a104f1f2a7"},
    "core_config": {"path": CORE_CONFIG, "sha256": "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3", "blob": "0634a3108ab0543fa1f8e9bc19015124feae7079"},
    "public_wer": {"path": PUBLIC_WER, "sha256": "581a0e4b0bb91d55a252b92871dbb1246b5fbc4466a5d94bceb35862744fc023", "blob": "f5719cee1f3dfee1c84d7a5e4c7c25620ded1e2d"},
}
EXPECTED_POLICY = {
    "required_verifier": "research/000b2-public/verify_b2r16.py",
    "primary_decode_allowed": False,
    "scoring_allowed": False,
    "comparative_publish_allowed": False,
    "production_selection_allowed": False,
    "product_code_allowed": False,
    "foreign_successor_task_references_allowed": False,
}
EXPECTED_NORMALIZATION = {
    "algorithm": "UNIT_COST_LEVENSHTEIN", "casefold": True,
    "punctuation_and_symbol_categories_to_space": ["P", "S"],
    "unicode_representation": "NFC", "whitespace": "COLLAPSE_AND_SPLIT",
}

class VerifyError(RuntimeError):
    """Fail-closed B2R16 verification error."""

def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)

def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value

def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerifyError(f"unable to read {path.relative_to(ROOT)}: {exc}") from exc
    require(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain one JSON object")
    return value

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def git_output(*args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise VerifyError(f"git {' '.join(args)} failed: {exc}") from exc

def git_blob(path: Path) -> str:
    return git_output("rev-parse", f"HEAD:{path.relative_to(ROOT).as_posix()}")

def canonical_freeze_digest(document: dict[str, Any]) -> str:
    payload = dict(document)
    recorded = payload.pop("freeze_digest_sha256", None)
    require(recorded is not None, "freeze digest field missing")
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

def verify_authority() -> None:
    readiness = load_json(READINESS)
    require(readiness.get("completed_recovery_tasks") == ["B2R13", "B2R14", "B2R15"], "canonical recovery prefix drift")
    require(readiness.get("active_recovery_unit") == TASK, "B2R16 is not the sole active recovery unit")
    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict), "replacement attempt authority missing")
    require(replacement.get("attempt_id") == ATTEMPT and replacement.get("required") is True, "replacement attempt authority drift")
    require(replacement.get("frozen") is False, "canonical authority froze ATTEMPT-003 before B2R16 reconciliation")
    require(replacement.get("primary_decode_entry_open") is False, "primary decode entry opened during B2R16")
    proofs = readiness.get("transition_proofs")
    require(isinstance(proofs, list) and proofs, "transition proofs missing")
    predecessor = proofs[-1]
    require(isinstance(predecessor, dict) and predecessor.get("completed_task") == PREDECESSOR_TASK, "B2R16 predecessor task drift")
    require(predecessor.get("canonical_task_merge") == PREDECESSOR_TASK_MERGE, "B2R15 task merge drift")
    require(predecessor.get("post_merge_recovery_run_id") == PREDECESSOR_POSTMERGE_RUN, "B2R15 post-merge proof drift")
    require(predecessor.get("successor_task") == TASK, "B2R15 transition does not authorize B2R16")
    scopes = readiness.get("task_candidate_scopes")
    require(isinstance(scopes, dict) and scopes.get(TASK) == EXPECTED_SCOPE, "B2R16 exact candidate scope drift")
    policies = readiness.get("task_content_policies")
    require(isinstance(policies, dict) and policies.get(TASK) == EXPECTED_POLICY, "B2R16 content policy drift")
    for path, label in ((CURRENT, "CURRENT"), (CURRENT_STATE, "CURRENT_STATE")):
        text = path.read_text(encoding="utf-8")
        require("**Active successor recovery unit:** `B2R16`" in text, f"{label} does not authorize B2R16")
        require(f"`{PREDECESSOR_TASK_MERGE}`" in text and f"`{PREDECESSOR_POSTMERGE_RUN}`" in text, f"{label} lost B2R15 proof")
        require("**ATTEMPT-003 frozen:** `false`" in text, f"{label} lost pre-reconciliation state")
        require("**ATTEMPT-003 primary decode entry open:** `false`" in text, f"{label} opens primary decoding")

def verify_source_identities(require_git: bool) -> None:
    for label, identity in IDENTITIES.items():
        path = identity["path"]
        require(path.exists(), f"missing frozen dependency: {path.relative_to(ROOT)}")
        expected_sha = identity.get("sha256")
        if expected_sha is not None:
            require(sha256_file(path) == expected_sha, f"{label} SHA-256 drift")
        if require_git:
            require(git_blob(path) == identity["blob"], f"{label} Git blob drift")
    prep = load_json(PREPROCESSING_REBIND)
    env = load_json(ENVIRONMENT_REBIND)
    provenance = load_json(B2R15_PROVENANCE)
    qualification = load_json(B2R14_QUALIFICATION)
    prep_attempt = prep.get("attempt")
    env_attempt = env.get("attempt")
    require(isinstance(prep_attempt, dict) and prep_attempt.get("bound_attempt_id") == ATTEMPT and prep_attempt.get("primary_decoding_started") is False, "preprocessing binding drift")
    require(isinstance(env_attempt, dict) and env_attempt.get("bound_attempt_id") == ATTEMPT and env_attempt.get("primary_decoding_started") is False, "environment binding drift")
    harness_identity = provenance.get("preserved_b2r14_harness_identity")
    require(isinstance(harness_identity, dict), "B2R15 provenance lost B2R14 harness identity")
    require(harness_identity.get("harness_git_blob_sha1") == IDENTITIES["b2r14_harness"]["blob"], "B2R14 harness provenance blob drift")
    require(harness_identity.get("harness_sha256") == IDENTITIES["b2r14_harness"]["sha256"], "B2R14 harness provenance SHA-256 drift")
    require(harness_identity.get("runtime_version") == "1.13.7" and harness_identity.get("runtime_revision") == "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e", "pinned runtime identity drift")
    require(qualification.get("task") == "B2R14", "B2R14 qualification task drift")
    contract = qualification.get("result_contract")
    require(isinstance(contract, dict) and contract.get("required_return_type") == "str" and contract.get("preservation") == "EXACT", "B2R14 result contract drift")
    require(contract.get("object_style_text_extraction_allowed") is False and contract.get("dynamic_result_coercion_allowed") is False, "B2R14 result safety drift")

def verify_preexecution_state(require_git: bool) -> None:
    document = load_json(PRESTATE)
    require(document.get("schema_version") == "000b2-public-b2r16-preexecution-state-v1", "preexecution schema drift")
    require(document.get("task") == TASK and document.get("lane") == "PUBLIC_CORPUS" and document.get("attempt_id") == ATTEMPT, "preexecution identity drift")
    require(document.get("phase") == "PRE_PRIMARY_CAPTURE" and document.get("frozen") is False, "preexecution phase/freeze drift")
    require(document.get("candidate_decoding_started") is False and document.get("primary_decoding_started") is False, "preexecution records decoding")
    require(document.get("canonical_authority_base") == AUTHORITY_BASE, "preexecution authority base drift")
    require(document.get("recovery_predecessor") == {"task": PREDECESSOR_TASK, "canonical_task_merge": PREDECESSOR_TASK_MERGE, "post_merge_recovery_run_id": PREDECESSOR_POSTMERGE_RUN, "reconciliation_merge": PREDECESSOR_RECONCILIATION}, "preexecution predecessor proof drift")
    expected = {
        "subset_manifest_sha256": "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb",
        "subset_freeze_digest_sha256": "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242",
        "candidate_registry_sha256": "2448daab15aea13d1e03c326e43b163337a4e3a09ec077bb0f25e3dd51499f1f",
        "candidate_revalidation_sha256": "aeca7b824d14388271b04c2dad953cecf5c47cd53cf3f70b766f4fe4dcac54b8",
        "frozen_methodology_sha256": "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df",
        "core_scorer_sha256": "7328cb34610218a703544a0de6dbfd5e0980b0a62131966119bca648855260e1",
        "core_config_sha256": "4d97d6b9e563bbbaf6cf455597f4c56e44c459a41c25d85f2f069c5fcbeec8e3",
        "public_wer_adapter_sha256": "581a0e4b0bb91d55a252b92871dbb1246b5fbc4466a5d94bceb35862744fc023",
        "b2r15_preprocessing_rebinding_sha256": "c44bbbf6d20aaec671d48c083eb76cfb6889a3c50486bd9da94c25b2b8f8039f",
        "b2r15_environment_rebinding_sha256": "0a6b32abae50da0d3d16f850a8e59edde0cb24f9489ce726054d6cf06e03532c",
        "b2r14_harness_sha256": "388b1480de6caed4adaad5d88cf3d275a5a4b1d35bd99e00f466581958886e39",
    }
    require(document.get("preserved_identities") == expected, "preexecution identity set drift")
    guards = document.get("claim_guards")
    require(isinstance(guards, dict) and guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "preexecution claim guards missing")
    for key in ("comparative_result_available", "comparative_performance_authorized", "production_stt_selected", "product_code_authorized", "attempt_003_primary_decode_authorized", "primary_decode_performed", "scoring_performed"):
        require(guards.get(key) is False, f"preexecution guard opened: {key}")
    require(sha256_file(PRESTATE) == PRESTATE_SHA256, "preexecution file SHA-256 drift")
    if require_git:
        require(git_blob(PRESTATE) == PRESTATE_BLOB, "preexecution Git blob drift")

def verify_manifest(require_git: bool) -> None:
    document = load_json(MANIFEST)
    require(document.get("schema_version") == "000b2-public-b2r16-attempt-003-manifest-v1", "manifest schema drift")
    require(document.get("task") == TASK and document.get("lane") == "PUBLIC_CORPUS" and document.get("attempt_id") == ATTEMPT, "manifest identity drift")
    require(document.get("phase") == "PRE_PRIMARY_FROZEN" and document.get("frozen") is True, "ATTEMPT-003 manifest is not frozen")
    require(document.get("freeze_digest_sha256") == FREEZE_DIGEST and canonical_freeze_digest(document) == FREEZE_DIGEST, "freeze digest mismatch")
    authority = document.get("authority")
    require(isinstance(authority, dict), "manifest authority bindings missing")
    require(authority.get("preexecution_state") == {"path": "research/000b2-public/b2r16-preexecution-state.json", "git_blob_sha1": PRESTATE_BLOB, "sha256": PRESTATE_SHA256}, "preexecution state binding drift")
    preprocessing = authority.get("preprocessing")
    environment = authority.get("execution_environment")
    harness = authority.get("b2r14_harness")
    require(isinstance(preprocessing, dict) and preprocessing.get("git_blob_sha1") == IDENTITIES["preprocessing_rebind"]["blob"] and preprocessing.get("sha256") == IDENTITIES["preprocessing_rebind"]["sha256"] and preprocessing.get("bound_attempt_id") == ATTEMPT, "preprocessing authority drift")
    require(isinstance(environment, dict) and environment.get("git_blob_sha1") == IDENTITIES["environment_rebind"]["blob"] and environment.get("sha256") == IDENTITIES["environment_rebind"]["sha256"] and environment.get("bound_attempt_id") == ATTEMPT, "environment authority drift")
    require(environment.get("performance_mode") == "DIAGNOSTIC" and environment.get("comparative_performance_authorized") is False, "environment claim boundary drift")
    require(isinstance(harness, dict) and harness.get("git_blob_sha1") == IDENTITIES["b2r14_harness"]["blob"] and harness.get("sha256") == IDENTITIES["b2r14_harness"]["sha256"], "B2R14 harness authority drift")
    require(harness.get("qualification_git_blob_sha1") == IDENTITIES["b2r14_qualification"]["blob"] and harness.get("runtime_version") == "1.13.7" and harness.get("runtime_revision") == "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e", "B2R14 runtime/qualification drift")
    candidate_set = document.get("candidate_set")
    require(isinstance(candidate_set, dict) and candidate_set.get("candidate_ids") == CANDIDATE_IDS and candidate_set.get("count") == 6, "candidate order or membership drift")
    require(candidate_set.get("registry_git_blob_sha1") == IDENTITIES["candidate_registry"]["blob"] and candidate_set.get("registry_sha256") == IDENTITIES["candidate_registry"]["sha256"], "candidate registry drift")
    require(candidate_set.get("frozen_methodology_git_blob_sha1") == IDENTITIES["frozen_methodology"]["blob"] and candidate_set.get("frozen_methodology_sha256") == IDENTITIES["frozen_methodology"]["sha256"], "methodology drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "candidate membership mutation reopened")
    decoding_contract = document.get("decoding_contract")
    require(isinstance(decoding_contract, dict), "decoding contract missing")
    require(decoding_contract.get("c0_repository_context") == "OFF" and decoding_contract.get("c0_test_specific_context") == "OFF" and decoding_contract.get("candidate_specific_audio_transform") == "OFF", "C0 contract drift")
    require(decoding_contract.get("identical_frozen_audio_required_across_candidates") is True and decoding_contract.get("candidate_decoding_started") is False and decoding_contract.get("primary_decoding_started") is False, "freeze decoding contract drift")
    require(decoding_contract.get("raw_outputs_and_failures_must_be_preserved") is True and decoding_contract.get("candidate_run_runtime_observations_must_be_preserved_separately") is True, "evidence preservation weakened")
    scoring = document.get("scoring")
    require(isinstance(scoring, dict), "scoring identity block missing")
    require(scoring.get("core_scorer_git_blob_sha1") == IDENTITIES["core_scorer"]["blob"] and scoring.get("core_scorer_sha256") == IDENTITIES["core_scorer"]["sha256"], "core scorer drift")
    require(scoring.get("core_config_git_blob_sha1") == IDENTITIES["core_config"]["blob"] and scoring.get("core_config_sha256") == IDENTITIES["core_config"]["sha256"], "core config drift")
    require(scoring.get("public_wer_adapter_git_blob_sha1") == IDENTITIES["public_wer"]["blob"] and scoring.get("public_wer_adapter_sha256") == IDENTITIES["public_wer"]["sha256"], "public WER adapter drift")
    require(scoring.get("public_p0_normalization") == EXPECTED_NORMALIZATION and scoring.get("result_driven_changes_allowed") is False, "normalization/scoring contract drift")
    recovery = document.get("recovery_authority")
    require(isinstance(recovery, dict) and recovery.get("canonical_authority_base") == AUTHORITY_BASE and recovery.get("predecessor_task") == PREDECESSOR_TASK, "recovery authority drift")
    require(recovery.get("predecessor_task_merge") == PREDECESSOR_TASK_MERGE and recovery.get("predecessor_post_merge_recovery_run_id") == PREDECESSOR_POSTMERGE_RUN and recovery.get("predecessor_reconciliation_merge") == PREDECESSOR_RECONCILIATION, "predecessor proof drift")
    require(recovery.get("predecessor_provenance_git_blob_sha1") == IDENTITIES["b2r15_provenance"]["blob"], "B2R15 provenance binding drift")
    claims = document.get("claims")
    require(isinstance(claims, dict) and claims.get("human_developer_speech_accuracy_evidence") == "ABSENT", "manifest claim guards missing")
    for key in ("comparative_result_available", "comparative_performance_authorized", "human_developer_speech_ranking_authorized", "production_stt_selected", "product_code_authorized", "primary_decode_authorized_at_freeze", "primary_decode_performed", "scoring_performed", "successor_execution_authorized_at_freeze"):
        require(claims.get(key) is False, f"manifest guard opened: {key}")
    require(sha256_file(MANIFEST) == MANIFEST_SHA256, "manifest file SHA-256 drift")
    if require_git:
        require(git_blob(MANIFEST) == MANIFEST_BLOB, "manifest Git blob drift")

def verify_no_primary_output_surface() -> None:
    forbidden = (PUBLIC / "b2r16-transcripts.json", PUBLIC / "b2r16-results.json", PUBLIC / "b2r16-scores.json")
    require(all(not path.exists() for path in forbidden), "B2R16 primary/scored output surface exists during freeze")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-git", action="store_true")
    args = parser.parse_args()
    verify_authority()
    verify_source_identities(args.require_git)
    verify_preexecution_state(args.require_git)
    verify_manifest(args.require_git)
    verify_no_primary_output_surface()
    print("B2R16_ATTEMPT_003_FREEZE=PASS")
    print(f"B2R16_FREEZE_DIGEST={FREEZE_DIGEST}")
    print("ATTEMPT_003_FROZEN_EVIDENCE=YES")
    print("ATTEMPT_003_CANDIDATE_DECODING_STARTED_AT_FREEZE=NO")
    print("ATTEMPT_003_PRIMARY_DECODING_STARTED_AT_FREEZE=NO")
    print("ATTEMPT_003_SCORING_PERFORMED_AT_FREEZE=NO")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerifyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"B2R16_ATTEMPT_003_FREEZE=FAIL: {exc}") from exc
