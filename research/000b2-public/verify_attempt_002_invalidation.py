#!/usr/bin/env python3
"""Fail closed on ATTEMPT-002 invalidation and the ATTEMPT-003 recovery frontier."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY_MAIN = "dc70fac9eddb6cda2dc4cabc4aec2df5f0beb9ff"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-002"
ATTEMPT_003_ID = "000B2-PUBLIC-ATTEMPT-003"
ATTEMPT_MANIFEST_PATH = "research/000b2-public/attempt-002-manifest.json"
ATTEMPT_MANIFEST_BLOB = "5928f3cc64b783d14d853d57132cbf43b7c98d30"
ATTEMPT_MANIFEST_SHA256 = "a2dc8246e4567e670beb3f26e315be93e001e4d9a9037be57ff11fce5a340134"
ATTEMPT_FREEZE_DIGEST = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
FROZEN_METHODOLOGY_SHA256 = "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df"
B2R09_TASK_MERGE = "fc357350270d5cb34fc1305dba4a9de41a5234c3"
B2R09_POSTMERGE_RUN = 34160146607
B2R09_DECODER_BLOB = "27052cc7f3d57d2743ee06a7db8de730c833935e"
B2R09_EVIDENCE_BLOB = "ee57923e649bee4dc8910f473c8e55ec80eeb790"
B2R09_EVIDENCE_SHA256 = "d59fa9605e8b0cf6892cd5a7ece105c6abe0753ff8949e9206e35f42da9a003f"
B2R09_EVIDENCE_PAYLOAD_SHA256 = "4a81f1be21e18aa462ee9ec9c32a1daeaa6fa86bcca6372b0634a9421c16c1ed"
B2R09_PROVENANCE_BLOB = "11e04cf248a24b5224fd153aece630e0622b7770"
SHERPA_VERSION = "1.13.7"
SHERPA_REVISION = "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e"
SHERPA_PATH = "sherpa-onnx/python/sherpa_onnx/online_recognizer.py"
SHERPA_BLOB = "18b49aaf40dc6e43606c63c9633762e8f573876b"
DEFECTIVE_EXPRESSION = 'str(getattr(recognizer.get_result(stream), "text", "") or "")'
SHERPA_SIGNATURE = "def get_result(self, s: OnlineStream) -> str:"
SHERPA_RETURN = "return self.recognizer.get_result(s).text.strip()"
TASK_ORDER = [f"B2R{number:02d}" for number in range(13, 25)]
CANDIDATES = [
    "moonshine-compact",
    "moonshine-balanced",
    "whispercpp-compact",
    "whispercpp-balanced",
    "sherpa-onnx-compact",
    "sherpa-onnx-balanced",
]
SUCCESSOR_TOKEN_RE = re.compile(r"\bB2R(?:1[3-9]|2[0-4])\b", re.IGNORECASE)
POSITIVE_AUTHORITY_PATTERNS = {
    "comparative_result_available": re.compile(r"comparative_result_available[\"']?\s*[:=]\s*(?:true|True|YES|yes)"),
    "production_stt_selected": re.compile(r"production_stt_selected[\"']?\s*[:=]\s*(?:true|True|YES|yes)"),
    "product_code_authorized": re.compile(r"product_code_authorized[\"']?\s*[:=]\s*(?:true|True|YES|yes)"),
    "primary_decode_entry_open": re.compile(r"primary_decode_entry_open[\"']?\s*[:=]\s*(?:true|True|YES|yes)"),
}
DECODE_CALL_NAMES = {
    "accept_waveform",
    "create_stream",
    "decode",
    "decode_stream",
    "get_result",
    "input_finished",
    "transcribe",
}
SCORING_CALL_NAMES = {
    "compute_wer",
    "score",
    "score_transcript",
    "score_transcripts",
    "wer",
    "word_error_rate",
}

B2R14_NON_PRIMARY_FIXTURE_CONTRACT = {
    "material_class": "DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY",
    "fixture_id": "b2r14-sherpa-result-string-contract-v1",
    "sample_rate_hz": 16000,
    "channel_count": 1,
    "sample_format": "PCM_S16LE",
    "frame_count": 16000,
    "pcm_sha256": "0c92bddb4e96f3ea9ec9f0f64a668255a6c15527ac09f6f119cafde60c7c4a39",
    "primary_corpus_access": False,
    "frozen_p0_access": False,
    "attempt_003_primary_evidence_access": False,
}
B2R14_FORBIDDEN_PRIMARY_MARKERS = (
    "research/000b2-public/preprocessing-capture.json",
    "research/000b2-public/subset-manifest.json",
    "research/000b2-public/raw",
    "research/000b2-public/preprocessed",
    "research/000b2-public/transcripts",
    "attempt-003-manifest.json",
    "b2r17-",
    "b2r18-",
    "b2r19-",
    "b2r20-",
    "b2r21-",
    "b2r22-",
)


# Exact ATTEMPT-002 bytes that were canonical when the defect was discovered.
# These paths are immutable historical evidence/proof material after invalidation.
IMMUTABLE_HISTORICAL_BLOBS = {
    "research/000b2-public/attempt-002-manifest.json": ATTEMPT_MANIFEST_BLOB,
    "research/000b2-public/attempt-002-preexecution-state.json": "0e860485dae45cbc7b5f3c92d4f238983a9db285",
    "research/000b2-public/b2r03-preexecution-rebinding.json": "49ba712b6a71ae69313c06b724833de1a95099b4",
    "research/000b2-public/decode_b2r05.py": "43125c1626d860aa1cb2704d7420a5f72dc7433b",
    "research/000b2-public/b2r05-moonshine-compact.json": "1cd6deb34a6c9aed736cccd7e5e97e57dacb31c3",
    "research/000b2-public/b2r05-provenance.json": "19d8185435b4833d65eb597fa4a95bed1720d396",
    "research/000b2-public/verify_b2r05.py": "ed793584f1f03b85c8b80bad47542bcc681234d6",
    "research/000b2-public/decode_b2r06.py": "72555a02e21f3d2790e86ecdf128cee0b19b659e",
    "research/000b2-public/b2r06-moonshine-balanced.json": "bf5aec3846676124563fa1996c7209f81c66d959",
    "research/000b2-public/b2r06-provenance.json": "2f11bac0ab0ebf4237f1a10c69b82fcfb0f9236b",
    "research/000b2-public/verify_b2r06.py": "7bcf8dd08ed1c9319d84c7bf3614d3fe78508e47",
    "research/000b2-public/decode_b2r07.py": "09f89a77c2339177b45ef09758f2387e44c650af",
    "research/000b2-public/b2r07-whispercpp-compact.json": "37540ea9b5c3fd306349f087ddd503c6e2602eaa",
    "research/000b2-public/b2r07-provenance.json": "54d227ea7b082e2726cce532941a384822cc6501",
    "research/000b2-public/verify_b2r07.py": "1aad81f7a280c4b29f479a2b18ac138940981f88",
    "research/000b2-public/decode_b2r08.py": "ac5a16469309f8ab3ad854b9df616f22f2903c33",
    "research/000b2-public/b2r08-whispercpp-balanced.json": "24dcb8cf79e068402b55a16f47ff3d9f6de9dadb",
    "research/000b2-public/b2r08-provenance.json": "95ede45e4ab8b9acde61c3cbfd7d2ce238a2a694",
    "research/000b2-public/verify_b2r08.py": "54c2cbe0146ab46e038733d5680dadd00ee2d53e",
    "research/000b2-public/decode_b2r09.py": B2R09_DECODER_BLOB,
    "research/000b2-public/b2r09-sherpa-onnx-compact.json": B2R09_EVIDENCE_BLOB,
    "research/000b2-public/b2r09-provenance.json": B2R09_PROVENANCE_BLOB,
    "research/000b2-public/verify_b2r09.py": "c852567f42f5945ad3fe7f3fc9ebd8c2de27073d",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ATTEMPT_002_INVALIDATION=FAIL: {message}")


def run_git(*args: str, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    require(completed.returncode == 0, f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def load_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{label} root must be an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob(ref: str, path: str, cwd: Path = ROOT) -> str:
    return run_git("rev-parse", f"{ref}:{path}", cwd=cwd)


def expected_task_content_policies() -> dict[str, dict[str, Any]]:
    policies: dict[str, dict[str, Any]] = {}
    for task in TASK_ORDER:
        verifier = (
            "research/000b2-public/verify_b2r13_activation.py"
            if task == "B2R13"
            else f"research/000b2-public/verify_{task.lower()}.py"
        )
        policies[task] = {
            "required_verifier": verifier,
            "primary_decode_allowed": task in {"B2R17", "B2R18", "B2R19", "B2R20", "B2R21", "B2R22"},
            "scoring_allowed": task == "B2R24",
            "comparative_publish_allowed": False,
            "production_selection_allowed": False,
            "product_code_allowed": False,
            "foreign_successor_task_references_allowed": False,
        }
    return policies


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id.lower()
    if isinstance(node, ast.Attribute):
        return node.attr.lower()
    return ""


def verify_b2r13_candidate_content(readiness: dict[str, Any]) -> None:
    authority_base = os.environ.get("AUTHORITY_BASE_REVISION", "")
    if not authority_base:
        return
    changed = run_git("diff", "--name-only", "--diff-filter=ACMRTUXB", authority_base, "HEAD", "--")
    changed_paths = [path for path in changed.splitlines() if path]
    scopes = readiness.get("task_candidate_scopes")
    require(isinstance(scopes, dict), "task_candidate_scopes must be an object")
    expected = scopes.get("B2R13")
    require(isinstance(expected, list), "missing exact B2R13 candidate scope")
    require(sorted(changed_paths) == sorted(expected), "B2R13 candidate must match the exact activation path set")
    workflow_patterns = (
        r"\bpython(?:3)?\s+[^\n]*decode_b2r(?:0[5-9]|1[0-9]|2[0-4])\.py\b",
        r"\.create_stream\s*\(",
        r"\.accept_waveform\s*\(",
        r"\.decode_stream\s*\(",
        r"\.input_finished\s*\(",
        r"\.transcribe\s*\(",
    )
    for path in changed_paths:
        payload = run_git("show", f"HEAD:{path}")
        if path.endswith(".py"):
            tree = ast.parse(payload, filename=path)
            calls = {call_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
            forbidden_decode = sorted(calls & DECODE_CALL_NAMES)
            forbidden_scoring = sorted(calls & SCORING_CALL_NAMES)
            require(not forbidden_decode, f"B2R13 forbids decode-runtime calls in {path}: {', '.join(forbidden_decode)}")
            require(not forbidden_scoring, f"B2R13 forbids scoring calls in {path}: {', '.join(forbidden_scoring)}")
        elif path.endswith((".yml", ".yaml")):
            for pattern in workflow_patterns:
                require(re.search(pattern, payload, flags=re.IGNORECASE) is None,
                        f"B2R13 workflow contains primary-decode execution pattern {pattern}: {path}")


def verify_b2r14_non_primary_candidate(readiness: dict[str, Any]) -> None:
    require(readiness.get("b2r14_non_primary_fixture_contract") == B2R14_NON_PRIMARY_FIXTURE_CONTRACT,
            "B2R14 canonical non-primary fixture contract drift")
    authority_base = os.environ.get("AUTHORITY_BASE_REVISION", "")
    if not authority_base:
        return
    changed = run_git("diff", "--name-only", "--diff-filter=ACMRTUXB", authority_base, "HEAD", "--")
    changed_paths = [path for path in changed.splitlines() if path]
    harness_path = "research/000b2-public/b2r14-sherpa-result-harness.py"
    qualification_path = "research/000b2-public/b2r14-harness-qualification.json"
    workflow_path = ".github/workflows/000b2-public-b2r14-sherpa-result-harness.yml"
    require(harness_path in changed_paths and qualification_path in changed_paths and workflow_path in changed_paths,
            "B2R14 candidate must include canonical harness, qualification, and workflow artifacts")
    for path in changed_paths:
        payload = run_git("show", f"HEAD:{path}")
        lowered = payload.lower()
        for forbidden in B2R14_FORBIDDEN_PRIMARY_MARKERS:
            require(forbidden.lower() not in lowered, f"B2R14 candidate may not reference primary material marker {forbidden}: {path}")
        if path == harness_path:
            tree = ast.parse(payload, filename=path)
            strings = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
            for value in (
                B2R14_NON_PRIMARY_FIXTURE_CONTRACT["material_class"],
                B2R14_NON_PRIMARY_FIXTURE_CONTRACT["fixture_id"],
                B2R14_NON_PRIMARY_FIXTURE_CONTRACT["sample_format"],
                B2R14_NON_PRIMARY_FIXTURE_CONTRACT["pcm_sha256"],
            ):
                require(value in strings, f"B2R14 harness must bind exact non-primary fixture value: {value}")
            calls = {call_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
            require("get_result" in calls, "B2R14 harness must exercise the pinned sherpa get_result API")
        elif path == qualification_path:
            document = json.loads(payload)
            require(document.get("non_primary_fixture") == B2R14_NON_PRIMARY_FIXTURE_CONTRACT,
                    "B2R14 qualification must bind exact canonical non-primary fixture contract")
        elif path == workflow_path:
            require("b2r14-sherpa-result-harness.py" in lowered, "B2R14 workflow must invoke canonical harness")
            require(B2R14_NON_PRIMARY_FIXTURE_CONTRACT["pcm_sha256"] in payload,
                    "B2R14 workflow must bind exact canonical fixture digest")


def verify_active_task_candidate_content(readiness: dict[str, Any], active: str | None, completed: list[str]) -> None:
    if active is None:
        return
    if active == "B2R13":
        verify_b2r13_candidate_content(readiness)
        return
    if active == "B2R14":
        verify_b2r14_non_primary_candidate(readiness)
    authority_base = os.environ.get("AUTHORITY_BASE_REVISION", "")
    if not authority_base:
        return
    base_read = subprocess.run(
        ["git", "show", f"{authority_base}:research/000b2-public/recovery-attempt-003-readiness.json"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if base_read.returncode != 0:
        return
    try:
        base_state = json.loads(base_read.stdout)
    except json.JSONDecodeError as error:
        raise SystemExit("ATTEMPT_002_INVALIDATION=FAIL: authority-base successor readiness malformed") from error
    base_completed = base_state.get("completed_recovery_tasks")
    if not isinstance(base_completed, list):
        return
    delta = len(completed) - len(base_completed)
    if delta != 0:
        return

    changed_output = run_git("diff", "--name-only", "--diff-filter=ACMRTUXB", authority_base, "HEAD", "--")
    changed_paths = [path for path in changed_output.splitlines() if path]
    if not changed_paths:
        return

    policies = expected_task_content_policies()
    policy = policies[active]
    scopes = readiness.get("task_candidate_scopes")
    require(isinstance(scopes, dict), "task_candidate_scopes must be an object")
    allowed_paths = scopes.get(active)
    require(isinstance(allowed_paths, list), f"missing exact candidate scope for {active}")
    outside_scope = sorted(set(changed_paths) - set(allowed_paths))
    require(not outside_scope, f"{active} candidate content outside exact path scope: {', '.join(outside_scope)}")

    required_verifier = policy["required_verifier"]
    require(required_verifier in changed_paths, f"{active} candidate must include its required verifier")
    active_token = active.upper()
    active_index = TASK_ORDER.index(active)
    future_tokens = set(TASK_ORDER[active_index + 1 :])

    for path in changed_paths:
        probe = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{path}"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        require(probe.returncode == 0, f"{active} candidate may not delete scoped artifact: {path}")
        text = run_git("show", f"HEAD:{path}")
        task_tokens = {token.upper() for token in SUCCESSOR_TOKEN_RE.findall(text)}
        require(active_token in task_tokens, f"{active} candidate artifact lacks explicit active-task binding: {path}")
        future = sorted(task_tokens & future_tokens)
        require(not future, f"{active} candidate artifact references future successor tasks in {path}: {', '.join(future)}")

        for authority, pattern in POSITIVE_AUTHORITY_PATTERNS.items():
            require(pattern.search(text) is None, f"{active} candidate may not positively publish {authority}: {path}")

        if path.endswith(".json"):
            try:
                document = json.loads(text)
            except json.JSONDecodeError as error:
                raise SystemExit(f"ATTEMPT_002_INVALIDATION=FAIL: malformed {active} JSON artifact: {path}") from error
            require(isinstance(document, dict), f"{active} JSON artifact root must be an object: {path}")
            require(document.get("task") == active, f"{active} JSON artifact must bind task exactly: {path}")

        if path.endswith(".py"):
            try:
                tree = ast.parse(text, filename=path)
            except SyntaxError as error:
                raise SystemExit(f"ATTEMPT_002_INVALIDATION=FAIL: malformed {active} Python artifact: {path}") from error
            calls = {call_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
            if not policy["primary_decode_allowed"] and active != "B2R14":
                forbidden_decode = sorted(calls & DECODE_CALL_NAMES)
                require(not forbidden_decode, f"{active} forbids decode-runtime calls in {path}: {', '.join(forbidden_decode)}")
            if not policy["scoring_allowed"]:
                forbidden_scoring = sorted(calls & SCORING_CALL_NAMES)
                require(not forbidden_scoring, f"{active} forbids scoring calls in {path}: {', '.join(forbidden_scoring)}")

    verifier = ROOT / required_verifier
    require(verifier.is_file(), f"{active} required verifier is missing")
    verification = subprocess.run(
        [sys.executable, str(verifier), "--static-only"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    require(verification.returncode == 0, f"{active} task-specific verifier failed: {verification.stdout.strip()}")


def verify_historical_bytes() -> None:
    run_git("cat-file", "-e", f"{DISCOVERY_MAIN}^{{commit}}")
    for path, expected_blob in IMMUTABLE_HISTORICAL_BLOBS.items():
        discovery_blob = git_blob(DISCOVERY_MAIN, path)
        head_blob = git_blob("HEAD", path)
        require(discovery_blob == expected_blob, f"discovery blob drift for {path}: {discovery_blob}")
        require(head_blob == expected_blob, f"historical ATTEMPT-002 bytes changed at {path}: {head_blob}")

    for forbidden in (
        "research/000b2-public/decode_b2r10.py",
        "research/000b2-public/b2r10-sherpa-onnx-balanced.json",
        "research/000b2-public/b2r10-provenance.json",
        "research/000b2-public/verify_b2r10.py",
    ):
        probe = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{forbidden}"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        require(probe.returncode != 0, f"noncanonical B2R10 material must not appear on canonical candidate: {forbidden}")


def verify_attempt_manifest() -> None:
    path = ROOT / ATTEMPT_MANIFEST_PATH
    require(git_blob("HEAD", ATTEMPT_MANIFEST_PATH) == ATTEMPT_MANIFEST_BLOB, "ATTEMPT-002 manifest blob drift")
    require(sha256_file(path) == ATTEMPT_MANIFEST_SHA256, "ATTEMPT-002 manifest SHA-256 drift")
    manifest = load_object(path, "attempt-002 manifest")
    require(manifest.get("attempt_id") == ATTEMPT_ID, "ATTEMPT-002 id drift")
    require(manifest.get("frozen") is True, "ATTEMPT-002 must remain frozen historical evidence")
    require(manifest.get("freeze_digest_sha256") == ATTEMPT_FREEZE_DIGEST, "ATTEMPT-002 freeze digest drift")
    candidate_set = manifest.get("candidate_set")
    require(isinstance(candidate_set, dict), "candidate_set must be an object")
    require(candidate_set.get("candidate_ids") == CANDIDATES, "ATTEMPT-002 candidate membership/order drift")
    require(candidate_set.get("count") == 6, "ATTEMPT-002 candidate count drift")
    require(candidate_set.get("frozen_methodology_sha256") == FROZEN_METHODOLOGY_SHA256, "frozen methodology digest drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "post-freeze candidate changes must remain prohibited")
    scoring = manifest.get("scoring")
    require(isinstance(scoring, dict), "scoring contract must be an object")
    require(scoring.get("result_driven_changes_allowed") is False, "result-driven scoring changes must remain prohibited")


def verify_b2r09_binding() -> None:
    decoder_path = ROOT / "research/000b2-public/decode_b2r09.py"
    decoder_text = decoder_path.read_text(encoding="utf-8")
    require(git_blob("HEAD", "research/000b2-public/decode_b2r09.py") == B2R09_DECODER_BLOB, "B2R09 decoder blob drift")
    require(DEFECTIVE_EXPRESSION in decoder_text, "canonical B2R09 defective extraction expression is not preserved exactly")

    evidence_path = ROOT / "research/000b2-public/b2r09-sherpa-onnx-compact.json"
    require(git_blob("HEAD", "research/000b2-public/b2r09-sherpa-onnx-compact.json") == B2R09_EVIDENCE_BLOB, "B2R09 evidence blob drift")
    require(sha256_file(evidence_path) == B2R09_EVIDENCE_SHA256, "B2R09 evidence raw SHA-256 drift")

    provenance = load_object(ROOT / "research/000b2-public/b2r09-provenance.json", "B2R09 provenance")
    require(git_blob("HEAD", "research/000b2-public/b2r09-provenance.json") == B2R09_PROVENANCE_BLOB, "B2R09 provenance blob drift")
    source = provenance.get("canonical_evidence_source")
    require(isinstance(source, dict), "B2R09 canonical_evidence_source must be an object")
    require(source.get("evidence_raw_file_sha256") == B2R09_EVIDENCE_SHA256, "B2R09 evidence SHA binding drift")
    require(source.get("evidence_payload_sha256") == B2R09_EVIDENCE_PAYLOAD_SHA256, "B2R09 evidence payload binding drift")
    require(source.get("execution_decoder_blob_sha") == B2R09_DECODER_BLOB, "B2R09 execution decoder binding drift")
    runtime = provenance.get("runtime_identity")
    require(isinstance(runtime, dict), "B2R09 runtime_identity must be an object")
    require(runtime.get("distribution") == "sherpa-onnx", "B2R09 runtime distribution drift")
    require(runtime.get("version") == SHERPA_VERSION, "B2R09 runtime version drift")
    require(runtime.get("source_revision") == SHERPA_REVISION, "B2R09 runtime source revision drift")


def verify_invalidation_record() -> None:
    record = load_object(ROOT / "research/000b2-public/attempt-002-invalidation.json", "ATTEMPT-002 invalidation")
    require(record.get("schema_version") == "000b2-public-attempt-invalidation-v2", "invalidation schema drift")
    require(record.get("task") == "B2R13", "invalidation task must be B2R13")
    require(record.get("attempt_id") == ATTEMPT_ID, "invalidation attempt id drift")
    require(record.get("status") == "INVALIDATED_MATERIAL_EXECUTION_DRIFT", "invalidation status drift")
    require(record.get("discovered_against_canonical_main") == DISCOVERY_MAIN, "discovery main binding drift")

    frozen = record.get("frozen_contract")
    require(isinstance(frozen, dict), "frozen_contract must be an object")
    require(frozen.get("attempt_manifest_git_blob_sha1") == ATTEMPT_MANIFEST_BLOB, "invalidation manifest blob binding drift")
    require(frozen.get("attempt_manifest_sha256") == ATTEMPT_MANIFEST_SHA256, "invalidation manifest SHA binding drift")
    require(frozen.get("attempt_freeze_digest_sha256") == ATTEMPT_FREEZE_DIGEST, "invalidation freeze binding drift")
    require(frozen.get("frozen_methodology_sha256") == FROZEN_METHODOLOGY_SHA256, "invalidation methodology binding drift")

    drifts = record.get("material_drift")
    require(isinstance(drifts, list) and len(drifts) == 1, "exactly one confirmed material-drift class must be recorded")
    drift = drifts[0]
    require(isinstance(drift, dict), "material drift record must be an object")
    require(drift.get("id") == "SHERPA_ONNX_RESULT_EXTRACTION_TYPE_MISMATCH", "material drift id mismatch")
    require(drift.get("severity") == "MATERIAL", "material drift severity must be MATERIAL")
    require(drift.get("canonical_affected_task") == "B2R09", "B2R09 must be the canonical affected task")
    require(drift.get("canonical_decoder_git_blob_sha1") == B2R09_DECODER_BLOB, "material drift decoder blob binding mismatch")
    require(drift.get("canonical_decoder_expression") == DEFECTIVE_EXPRESSION, "material drift expression mismatch")
    require(drift.get("pinned_runtime_distribution_version") == SHERPA_VERSION, "material drift runtime version mismatch")
    require(drift.get("pinned_runtime_revision") == SHERPA_REVISION, "material drift runtime revision mismatch")
    require(drift.get("pinned_upstream_path") == SHERPA_PATH, "material drift upstream path mismatch")
    require(drift.get("pinned_upstream_git_blob_sha1") == SHERPA_BLOB, "material drift upstream blob mismatch")
    require(drift.get("pinned_upstream_contract") == "OnlineRecognizer.get_result(self, s: OnlineStream) -> str", "material drift upstream contract mismatch")
    require(drift.get("pinned_upstream_return") == SHERPA_RETURN, "material drift upstream return mismatch")

    affected = record.get("affected_canonical_execution")
    require(isinstance(affected, list) and len(affected) == 1, "exactly one canonical affected execution must be recorded")
    b2r09 = affected[0]
    require(isinstance(b2r09, dict), "affected B2R09 record must be an object")
    require(b2r09.get("canonical_task_merge") == B2R09_TASK_MERGE, "B2R09 task merge binding mismatch")
    require(b2r09.get("canonical_post_merge_recovery_run_id") == B2R09_POSTMERGE_RUN, "B2R09 post-merge run binding mismatch")
    require(b2r09.get("decoder_git_blob_sha1") == B2R09_DECODER_BLOB, "B2R09 decoder blob mismatch")
    require(b2r09.get("evidence_git_blob_sha1") == B2R09_EVIDENCE_BLOB, "B2R09 evidence blob mismatch")
    require(b2r09.get("evidence_raw_file_sha256") == B2R09_EVIDENCE_SHA256, "B2R09 evidence SHA mismatch")
    require(b2r09.get("evidence_payload_sha256") == B2R09_EVIDENCE_PAYLOAD_SHA256, "B2R09 payload SHA mismatch")
    require(b2r09.get("provenance_git_blob_sha1") == B2R09_PROVENANCE_BLOB, "B2R09 provenance blob mismatch")

    noncanonical = record.get("noncanonical_b2r10_disposition")
    require(isinstance(noncanonical, dict), "noncanonical B2R10 disposition must be an object")
    require(noncanonical.get("merge_candidate_pr") == 89 and noncanonical.get("review_only_pr") == 90, "B2R10 PR disposition drift")
    require(noncanonical.get("exact_head") == "0d9921afc565892b851ba8bf764ede514bf13d16", "B2R10 noncanonical head drift")
    require(noncanonical.get("merged") is False, "B2R10 invalid evidence must remain nonmerged")
    require(noncanonical.get("eligible_as_canonical_attempt_evidence") is False, "B2R10 invalid evidence must remain ineligible")
    require(noncanonical.get("eligible_for_scoring") is False, "B2R10 invalid evidence must remain scoring-ineligible")

    disposition = record.get("disposition")
    require(isinstance(disposition, dict), "invalidation disposition must be an object")
    for key in (
        "attempt_002_eligible_for_comparative_scoring",
        "attempt_002_eligible_for_candidate_superiority_claims",
        "attempt_002_new_primary_decode_authorized",
        "b2r10_b2r11_b2r12_attempt_002_execution_authorized",
        "candidate_membership_change_authorized",
        "subset_membership_change_authorized",
        "scorer_or_normalization_change_authorized",
        "production_stt_selected",
        "product_code_authorized",
    ):
        require(disposition.get(key) is False, f"invalidation disposition {key} must remain false")
    require(disposition.get("historical_attempt_preserved") is True, "historical ATTEMPT-002 must be preserved")
    require(disposition.get("historical_attempt_002_execution_bytes_must_remain_unchanged") is True, "historical ATTEMPT-002 bytes must be immutable")
    require(disposition.get("attempt_003_required") is True, "ATTEMPT-003 must remain required")
    require(disposition.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")


def parse_task_ledger(text: str) -> list[tuple[str, bool]]:
    matches = re.findall(r"^- \[([ xX])\] `?(B2R(?:1[3-9]|2[0-4]))`?\b", text, flags=re.MULTILINE)
    return [(task, mark.lower() == "x") for mark, task in matches]


def verify_successor_frontier() -> None:
    readiness = load_object(ROOT / "research/000b2-public/recovery-attempt-003-readiness.json", "ATTEMPT-003 recovery readiness")
    require(readiness.get("schema_version") == "000b2-public-attempt-003-recovery-readiness-v1", "successor readiness schema drift")
    require(readiness.get("state") == "RECOVERY_READY", "successor recovery must remain RECOVERY_READY")
    require(readiness.get("task_order") == TASK_ORDER, "successor recovery task order drift")
    require(readiness.get("task_content_policies") == expected_task_content_policies(), "successor task content policy drift")
    require(readiness.get("b2r14_non_primary_fixture_contract") == B2R14_NON_PRIMARY_FIXTURE_CONTRACT, "B2R14 canonical non-primary fixture contract drift")

    historical = readiness.get("historical_recovery_snapshot")
    require(isinstance(historical, dict), "historical recovery snapshot must be an object")
    require(historical.get("path") == "research/000b2-public/recovery-readiness.json", "historical recovery snapshot path drift")
    require(historical.get("completed_through") == "B2R09", "historical recovery completion drift")
    require(historical.get("active_unit_at_invalidation") == "B2R10", "historical active unit drift")
    require(historical.get("active_execution_authority") is False, "historical ATTEMPT-002 readiness must not authorize execution")

    invalid = readiness.get("invalidated_attempt")
    require(isinstance(invalid, dict), "invalidated_attempt must be an object")
    require(invalid.get("attempt_id") == ATTEMPT_ID, "successor invalidated attempt id drift")
    require(invalid.get("freeze_digest_sha256") == ATTEMPT_FREEZE_DIGEST, "successor invalidated freeze digest drift")
    require(invalid.get("comparative_scoring_eligible") is False, "ATTEMPT-002 scoring must remain ineligible")
    require(invalid.get("candidate_superiority_claim_eligible") is False, "ATTEMPT-002 superiority claims must remain ineligible")
    require(invalid.get("new_primary_decode_authorized") is False, "ATTEMPT-002 new primary decode must remain closed")

    replacement = readiness.get("replacement_attempt")
    require(isinstance(replacement, dict), "replacement_attempt must be an object")
    require(replacement.get("attempt_id") == ATTEMPT_003_ID, "replacement attempt id drift")
    require(replacement.get("required") is True, "ATTEMPT-003 must remain required")

    completed = readiness.get("completed_recovery_tasks")
    require(isinstance(completed, list), "completed_recovery_tasks must be a list")
    require(completed == TASK_ORDER[: len(completed)], "completed successor tasks must be an exact ordered prefix")
    active = readiness.get("active_recovery_unit")
    expected_active = TASK_ORDER[len(completed)] if len(completed) < len(TASK_ORDER) else None
    require(active == expected_active, f"active successor recovery unit must be {expected_active!r}")

    ledger = parse_task_ledger((ROOT / "specs/000B2-public-corpus-bakeoff/recovery-v2-tasks.md").read_text(encoding="utf-8"))
    require([task for task, _ in ledger] == TASK_ORDER, "successor task ledger membership/order drift")
    checked = [task for task, is_checked in ledger if is_checked]
    require(checked == completed, "successor task ledger and machine completion state disagree")

    proofs = readiness.get("transition_proofs")
    require(isinstance(proofs, list), "successor transition_proofs must be a list")
    require(len(proofs) == len(completed), "successor transition proof cardinality must match completed tasks")

    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "successor claim_guards must be an object")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    comparative_result = guards.get("comparative_result_available")
    if active is not None:
        require(comparative_result is False, f"comparative results must remain unavailable during {active}")
    else:
        require(completed == TASK_ORDER, "terminal comparative-result state requires all successor tasks complete")
        require(len(proofs) == len(TASK_ORDER), "terminal comparative-result state requires one proof per successor task")
        require(type(comparative_result) is bool, "terminal comparative_result_available must be boolean")
    require(guards.get("production_stt_selected") is False, "production STT must remain unselected")
    require(guards.get("product_code_authorized") is False, "product code must remain unauthorized")

    if active in {"B2R13", "B2R14", "B2R15", "B2R16", "B2R23", "B2R24"} or active is None:
        require(replacement.get("primary_decode_entry_open") is False, f"primary decode must be closed during terminal/non-decode phase {active}")
    elif active in {"B2R17", "B2R18", "B2R19", "B2R20", "B2R21", "B2R22"}:
        require(replacement.get("primary_decode_entry_open") is True, f"primary decode must be open during {active}")
    if active in {"B2R17", "B2R18", "B2R19", "B2R20", "B2R21", "B2R22", "B2R23", "B2R24"} or active is None:
        require(replacement.get("frozen") is True, f"ATTEMPT-003 must remain frozen during {active}")
    if replacement.get("primary_decode_entry_open") is True:
        require(replacement.get("frozen") is True, "ATTEMPT-003 primary decode cannot open before attempt freeze")
    if active == "B2R13":
        require(replacement.get("frozen") is False, "ATTEMPT-003 must not be frozen during B2R13 activation")
        require(completed == [], "B2R13 activation candidate must not pre-complete recovery work")
        require(readiness.get("transition_proofs") == [], "B2R13 activation candidate must not fabricate transition proofs")

    verify_active_task_candidate_content(readiness, active, completed)

    current = (ROOT / "specs/CURRENT.md").read_text(encoding="utf-8")
    current_state = (ROOT / "docs/canonical/CURRENT_STATE.md").read_text(encoding="utf-8")
    required_markers = (
        "**ATTEMPT-002 status:** `INVALIDATED_MATERIAL_EXECUTION_DRIFT`",
        "**Successor recovery authority:** `specs/000B2-public-corpus-bakeoff/recovery-v2.md`",
        f"**Active successor recovery unit:** `{active}`",
    )
    for marker in required_markers:
        require(marker in current, f"specs/CURRENT.md missing successor marker: {marker}")
        require(marker in current_state, f"CURRENT_STATE.md missing successor marker: {marker}")
    if active in {"B2R13", "B2R14", "B2R15", "B2R16", "B2R23", "B2R24"} or active is None:
        decode_marker = "**ATTEMPT-003 primary decode entry open:** `false`"
        require(decode_marker in current, f"CURRENT must close ATTEMPT-003 primary decode during {active}")
        require(decode_marker in current_state, f"CURRENT_STATE must close ATTEMPT-003 primary decode during {active}")
    elif active in {"B2R17", "B2R18", "B2R19", "B2R20", "B2R21", "B2R22"}:
        decode_marker = "**ATTEMPT-003 primary decode entry open:** `true`"
        require(decode_marker in current, f"CURRENT must open ATTEMPT-003 primary decode during {active}")
        require(decode_marker in current_state, f"CURRENT_STATE must open ATTEMPT-003 primary decode during {active}")


def verify_sherpa_source(source_root: Path) -> None:
    require(source_root.is_dir(), f"sherpa source root does not exist: {source_root}")
    require(run_git("rev-parse", "HEAD", cwd=source_root) == SHERPA_REVISION, "pinned sherpa source revision mismatch")
    require(git_blob("HEAD", SHERPA_PATH, cwd=source_root) == SHERPA_BLOB, "pinned sherpa source blob mismatch")
    source = (source_root / SHERPA_PATH).read_text(encoding="utf-8")
    require(SHERPA_SIGNATURE in source, "pinned sherpa source is missing the plain-string get_result signature")
    require(SHERPA_RETURN in source, "pinned sherpa source is missing the plain-string get_result return")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sherpa-source", type=Path)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    require(not (args.static_only and args.sherpa_source), "choose either --static-only or --sherpa-source")

    verify_historical_bytes()
    verify_attempt_manifest()
    verify_b2r09_binding()
    verify_invalidation_record()
    verify_successor_frontier()

    if args.sherpa_source is not None:
        verify_sherpa_source(args.sherpa_source.resolve())
        print("SHERPA_PINNED_API=PASS")
    else:
        require(args.static_only, "live pinned-source verification requires --sherpa-source; use --static-only only for offline structural checks")
        print("SHERPA_PINNED_API=NOT_RUN_STATIC_ONLY")

    readiness = load_object(ROOT / "research/000b2-public/recovery-attempt-003-readiness.json", "ATTEMPT-003 recovery readiness")
    replacement = readiness.get("replacement_attempt", {})
    guards = readiness.get("claim_guards", {})
    print("ATTEMPT_002_INVALIDATION=PASS")
    print("ATTEMPT_002_HISTORICAL_BYTES=PASS")
    print(f"ACTIVE_SUCCESSOR_RECOVERY_UNIT={readiness.get('active_recovery_unit')}")
    print("ATTEMPT_003_PRIMARY_DECODE_AUTHORIZED=" + ("YES" if replacement.get("primary_decode_entry_open") is True else "NO"))
    print("COMPARATIVE_RESULT_AVAILABLE=" + ("YES" if guards.get("comparative_result_available") is True else "NO"))
    print("PRODUCTION_STT_SELECTED=NO")
    print("PRODUCT_CODE_AUTHORIZED=NO")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")


if __name__ == "__main__":
    main()
