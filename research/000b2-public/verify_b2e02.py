#!/usr/bin/env python3
"""Verify sealed B2E02 moonshine-balanced C0 execution evidence and provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
EVIDENCE = PUBLIC / "b2e02-moonshine-balanced.json"
DUPLICATE_EVIDENCE = PUBLIC / "b2e02-moonshine-balanced-duplicate-run-33963021322.json"
PROVENANCE = PUBLIC / "b2e02-provenance.json"
ATTEMPT = PUBLIC / "attempt-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
READINESS = PUBLIC / "readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"

EXPECTED_BASE = "116dbd1734e01ec1280d6b530f0cb1dec867feb1"
EXPECTED_SOURCE_REVISION = "43cab310662b6e8eb1ea25b6d8e39a6dbf14a17e"
EXPECTED_FREEZE = "af4d5009e293daef5d8f629ca91af653f5f591448cd94d4555473a51e2d1da86"
EXPECTED_PREPROCESSING = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
EXPECTED_RAW_EVIDENCE_SHA256 = "8bc1b3e2e10bd7c64465b424f8dff5ffc84a153868459457d91e22e5cf3da253"
EXPECTED_PAYLOAD_SHA256 = "ad2baccb196313323b0284d5672f94d9ffae551f0b2af38cc29b4be082e6a6aa"
EXPECTED_SEMANTIC_RECORDS_SHA256 = "5d3a4f43768e7a862267f76df36a5e3dc9c8ec523b7156494c3b739096bc0bb1"
EXPECTED_CAPTURE_RUN_ID = 33962004933
EXPECTED_CAPTURE_RUN_ATTEMPT = 1
EXPECTED_CAPTURE_JOB_ID = 101295384896
EXPECTED_ARTIFACT_ID = 9968333519
EXPECTED_ARTIFACT_NAME = "b2e02-moonshine-balanced-43cab310662b6e8eb1ea25b6d8e39a6dbf14a17e"
EXPECTED_ARTIFACT_ZIP_SHA256 = "0cb9ae81262a6af0a5eb2382ac1fccdae6488c8a04d8551a912bdf8ff9d818ad"

EXPECTED_DUPLICATE_SOURCE_REVISION = "76611d5436f1ca6313d5c0832a02e3e7583b0337"
EXPECTED_DUPLICATE_RAW_EVIDENCE_SHA256 = "f21cf41533787b3045cf9209b150949ad646d50f702c89640d57c95c47085bc1"
EXPECTED_DUPLICATE_PAYLOAD_SHA256 = "601bccfe660db1e3f2b7b1348841c0cfb6152f085c86b9aa2f853e1dce3d0d51"
EXPECTED_DUPLICATE_SEMANTIC_RECORDS_SHA256 = "76665968a9b315a69534342570080d693cd44ac82cd888a78aaa743ccb947386"
EXPECTED_DUPLICATE_RUN_ID = 33963021322
EXPECTED_DUPLICATE_JOB_ID = 101298112856
EXPECTED_DUPLICATE_ARTIFACT_ID = 9968588759
EXPECTED_DUPLICATE_ARTIFACT_NAME = "b2e02-moonshine-balanced-76611d5436f1ca6313d5c0832a02e3e7583b0337"
EXPECTED_DUPLICATE_ARTIFACT_ZIP_SHA256 = "daa2236bd1bee96a4c241671eefe622d9353c3f5481691aa453640f3f6888c9a"
EXPECTED_DUPLICATE_TRANSCRIPT_DIFFERENCES = 10

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class VerifyError(ValueError):
    """Raised when committed B2E02 evidence fails closed."""


def require(value: bool, message: str) -> None:
    if not value:
        raise VerifyError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def static_frontier() -> None:
    readiness = load(READINESS)
    tasks = TASKS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    completed = readiness.get("completed_through")

    if completed == "B2E01":
        require(str(readiness.get("next_action", "")).startswith("Execute B2E02 only:"), "B2E02 is not sole pre-reconciliation next action")
        require("Do not begin B2E03" in readiness["next_action"], "B2E03 closure missing before B2E02 reconciliation")
        require("- [x] `B2E01`" in tasks and "- [ ] `B2E02`" in tasks and "- [ ] `B2E03`" in tasks, "B2E02 execution PR self-reconciled canonical task state")
        require("B2E02 (`moonshine-balanced`) is the sole current bounded execution unit" in current, "CURRENT pre-reconciliation B2E02 frontier drift")
    elif completed == "B2E02":
        require(str(readiness.get("next_action", "")).startswith("Execute B2E03 only:"), "B2E03 is not sole post-B2E02 next action")
        require("- [x] `B2E02`" in tasks and "- [ ] `B2E03`" in tasks, "B2E02/B2E03 canonical task frontier drift")
        require("B2E03" in current and "whispercpp-compact" in current and "sole current bounded execution unit" in current, "CURRENT post-B2E02 frontier drift")
    else:
        require("- [x] `B2E02`" in tasks, "later canonical state lost B2E02 completion")

    attempt = load(ATTEMPT)
    require(attempt.get("frozen") is True, "attempt is not frozen")
    require(attempt.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-001", "attempt id drift")
    require(attempt.get("freeze_digest_sha256") == EXPECTED_FREEZE, "attempt freeze digest drift")
    contract = attempt.get("decoding_contract", {})
    require(
        contract.get("candidate_decoding_started") is False
        and contract.get("primary_decoding_started") is False,
        "historical predecode manifest mutated",
    )


def preprocessing_index() -> dict[str, dict[str, Any]]:
    require(sha(PREPROCESSING) == EXPECTED_PREPROCESSING, "preprocessing bytes drift")
    records = load(PREPROCESSING).get("execution", {}).get("records")
    require(isinstance(records, list) and len(records) == 240, "preprocessing cardinality drift")
    result = {row["utterance_id"]: row for row in records}
    require(len(result) == 240, "duplicate preprocessing utterance id")
    return result


def validate_payload(evidence: dict[str, Any], expected_payload: str, label: str) -> None:
    recorded = evidence.get("evidence_payload_sha256")
    require(recorded == expected_payload, f"{label} recorded payload digest drift")
    unsigned = dict(evidence)
    unsigned.pop("evidence_payload_sha256", None)
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == expected_payload, f"{label} payload digest mismatch")


def semantic_records_digest(evidence: dict[str, Any]) -> str:
    records = evidence.get("execution", {}).get("records")
    require(isinstance(records, list) and len(records) == 240, "semantic record cardinality drift")
    semantic_keys = (
        "utterance_id",
        "source_partition",
        "canonical_preprocessed_file_sha256",
        "status",
        "raw_lines",
        "raw_transcript",
        "failure",
    )
    semantic: list[dict[str, Any]] = []
    for row in sorted(records, key=lambda item: item["utterance_id"]):
        require(isinstance(row, dict), "semantic record malformed")
        require(all(key in row for key in semantic_keys), "semantic record key missing")
        semantic.append({key: row[key] for key in semantic_keys})
    return hashlib.sha256(canonical(semantic)).hexdigest()


def verify_duplicate_semantics(primary: dict[str, Any], duplicate: dict[str, Any]) -> None:
    require(sha(DUPLICATE_EVIDENCE) == EXPECTED_DUPLICATE_RAW_EVIDENCE_SHA256, "raw duplicate B2E02 evidence bytes drift")
    validate_payload(duplicate, EXPECTED_DUPLICATE_PAYLOAD_SHA256, "duplicate")
    require(duplicate.get("schema_version") == "000b2-public-b2e02-decode-v1", "duplicate schema drift")
    require(duplicate.get("task") == "B2E02" and duplicate.get("state") == "C0_PRIMARY_DECODE_CAPTURED", "duplicate task/state drift")
    require(duplicate.get("authority") == primary.get("authority"), "duplicate authority binding drift")
    require(duplicate.get("candidate") == primary.get("candidate"), "duplicate candidate binding drift")
    require(duplicate.get("c0_controls") == primary.get("c0_controls"), "duplicate C0 controls drift")
    require(duplicate.get("claim_guards") == primary.get("claim_guards"), "duplicate claim guards drift")

    duplicate_run = duplicate.get("run", {})
    require(duplicate_run.get("repository_revision") == EXPECTED_DUPLICATE_SOURCE_REVISION, "duplicate source revision drift")
    require(duplicate_run.get("github_run_id") == EXPECTED_DUPLICATE_RUN_ID, "duplicate run id drift")
    require(duplicate_run.get("github_run_attempt") == 1, "duplicate run attempt drift")
    require(duplicate_run.get("github_job") == "capture-b2e02", "duplicate job name drift")
    require(duplicate_run.get("github_repository") == "TheHalfMoon/Wispral", "duplicate repository provenance drift")
    require(duplicate_run.get("timing_semantics") == "DIAGNOSTIC_ONLY", "duplicate timing semantics drift")
    require(duplicate_run.get("comparative_performance_authorized") is False, "duplicate comparative-performance authority drift")

    primary_execution = primary.get("execution", {})
    duplicate_execution = duplicate.get("execution", {})
    for execution, label in ((primary_execution, "canonical"), (duplicate_execution, "duplicate")):
        require(execution.get("input_count") == 240, f"{label} input count drift")
        require(execution.get("decoded_count") == 240, f"{label} decoded count drift")
        require(execution.get("failure_count") == 0, f"{label} failure count drift")
        require(execution.get("reference_transcripts_loaded_by_decoder") is False, f"{label} reference transcript boundary drift")
        require(execution.get("accuracy_scoring_performed") is False, f"{label} scoring boundary drift")
        require(execution.get("comparative_ranking_present") is False, f"{label} ranking boundary drift")
        require(execution.get("performance_claim_present") is False, f"{label} performance claim drift")

    primary_rows = {row["utterance_id"]: row for row in primary_execution["records"]}
    duplicate_rows = {row["utterance_id"]: row for row in duplicate_execution["records"]}
    require(len(primary_rows) == len(duplicate_rows) == 240, "duplicate record identity cardinality drift")
    require(set(primary_rows) == set(duplicate_rows), "duplicate utterance membership drift")

    transcript_differences = 0
    for uid in sorted(primary_rows):
        first = primary_rows[uid]
        second = duplicate_rows[uid]
        require(first.get("source_partition") == second.get("source_partition"), f"duplicate partition drift: {uid}")
        require(
            first.get("canonical_preprocessed_file_sha256") == second.get("canonical_preprocessed_file_sha256"),
            f"duplicate input digest drift: {uid}",
        )
        require(first.get("status") == second.get("status"), f"duplicate status drift: {uid}")
        if (
            first.get("raw_lines"),
            first.get("raw_transcript"),
            first.get("failure"),
        ) != (
            second.get("raw_lines"),
            second.get("raw_transcript"),
            second.get("failure"),
        ):
            transcript_differences += 1

    require(transcript_differences == EXPECTED_DUPLICATE_TRANSCRIPT_DIFFERENCES, "duplicate raw transcript difference count drift")
    require(semantic_records_digest(primary) == EXPECTED_SEMANTIC_RECORDS_SHA256, "canonical semantic record digest drift")
    require(semantic_records_digest(duplicate) == EXPECTED_DUPLICATE_SEMANTIC_RECORDS_SHA256, "duplicate semantic record digest drift")


def verify_provenance(evidence: dict[str, Any]) -> None:
    require(sha(EVIDENCE) == EXPECTED_RAW_EVIDENCE_SHA256, "raw canonical B2E02 evidence bytes drift")
    duplicate = load(DUPLICATE_EVIDENCE)
    verify_duplicate_semantics(evidence, duplicate)

    provenance = load(PROVENANCE)
    require(provenance.get("schema_version") == "000b2-public-b2e02-provenance-v2", "provenance schema drift")
    require(provenance.get("task") == "B2E02", "provenance task drift")
    require(provenance.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-001", "provenance attempt drift")
    require(provenance.get("candidate_id") == "moonshine-balanced", "provenance candidate drift")
    require(
        provenance.get("provenance_status")
        == "RECORDED_FROM_EXACT_GITHUB_ACTIONS_RUN_ARTIFACT_AND_DUPLICATE_RECONCILIATION_METADATA",
        "provenance status drift",
    )

    canonical_source = provenance.get("canonical_evidence_source", {})
    require(canonical_source == {
        "artifact_id": EXPECTED_ARTIFACT_ID,
        "artifact_name": EXPECTED_ARTIFACT_NAME,
        "artifact_zip_sha256": EXPECTED_ARTIFACT_ZIP_SHA256,
        "conclusion": "success",
        "event": "push",
        "evidence_path": "research/000b2-public/b2e02-moonshine-balanced.json",
        "evidence_payload_sha256": EXPECTED_PAYLOAD_SHA256,
        "evidence_raw_file_sha256": EXPECTED_RAW_EVIDENCE_SHA256,
        "job_id": EXPECTED_CAPTURE_JOB_ID,
        "role": "CANONICAL_EVIDENCE_SOURCE",
        "run_attempt": EXPECTED_CAPTURE_RUN_ATTEMPT,
        "run_id": EXPECTED_CAPTURE_RUN_ID,
        "selection_basis": "CANONICAL_EVIDENCE_WAS_SEALED_BEFORE_DUPLICATE_RUN_STARTED; NOT_RESULT_DRIVEN",
        "semantic_records_sha256": EXPECTED_SEMANTIC_RECORDS_SHA256,
        "source_revision": EXPECTED_SOURCE_REVISION,
        "workflow_name": "Internal B2E02 Public C0 Capture",
    }, "canonical B2E02 capture provenance drift")

    related = provenance.get("related_capture_runs")
    require(isinstance(related, list) and len(related) == 1, "related B2E02 capture inventory drift")
    require(related[0] == {
        "artifact_id": EXPECTED_DUPLICATE_ARTIFACT_ID,
        "artifact_name": EXPECTED_DUPLICATE_ARTIFACT_NAME,
        "artifact_zip_sha256": EXPECTED_DUPLICATE_ARTIFACT_ZIP_SHA256,
        "conclusion": "failure",
        "decoder_capture_status": "CAPTURED_240_DECODED_0_FAILED",
        "event": "push",
        "evidence_path": "research/000b2-public/b2e02-moonshine-balanced-duplicate-run-33963021322.json",
        "evidence_payload_sha256": EXPECTED_DUPLICATE_PAYLOAD_SHA256,
        "evidence_raw_file_sha256": EXPECTED_DUPLICATE_RAW_EVIDENCE_SHA256,
        "input_identity_equivalence": "PASS",
        "job_id": EXPECTED_DUPLICATE_JOB_ID,
        "post_decode_verifier_failure": "recorded payload digest drift",
        "raw_transcript_difference_count": EXPECTED_DUPLICATE_TRANSCRIPT_DIFFERENCES,
        "raw_transcript_identity_equivalence": "DIFF",
        "reconciliation_status": "PRESERVED_AND_COMPARED_TO_CANONICAL_EVIDENCE",
        "role": "FAILED_WORKFLOW_AFTER_SUCCESSFUL_DECODE_NONCANONICAL",
        "run_attempt": 1,
        "run_id": EXPECTED_DUPLICATE_RUN_ID,
        "selection_effect": "NONE",
        "semantic_records_sha256": EXPECTED_DUPLICATE_SEMANTIC_RECORDS_SHA256,
        "source_revision": EXPECTED_DUPLICATE_SOURCE_REVISION,
        "status_identity_equivalence": "PASS",
        "workflow_name": "Internal B2E02 Public C0 Capture",
    }, "duplicate B2E02 capture provenance drift")

    reconciliation = provenance.get("duplicate_reconciliation", {})
    require(reconciliation == {
        "b2e03_authorized": False,
        "canonical_evidence_source_count": 1,
        "cause": "POST_SEAL_VERIFY_B2E02_CHANGE_MATCHED_CAPTURE_WORKFLOW_PATH_FILTER_BEFORE_CAPTURE_BOOTSTRAP_REMOVAL",
        "decode_capture_count_for_cell_2": 2,
        "input_identity_equivalence": "PASS",
        "raw_transcript_difference_count": EXPECTED_DUPLICATE_TRANSCRIPT_DIFFERENCES,
        "raw_transcript_identity_equivalence": "DIFF",
        "result_driven_evidence_selection": False,
        "status_identity_equivalence": "PASS",
        "timing_values_are_diagnostic_only": True,
    }, "duplicate B2E02 reconciliation drift")

    require(provenance.get("claims") == {
        "b2e03_authorized": False,
        "comparative_performance_authorized": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "product_code_authorized": False,
        "production_stt_selected": False,
        "timing_semantics": "DIAGNOSTIC_ONLY",
    }, "B2E02 provenance claim guards drift")

    run = evidence.get("run", {})
    require(run.get("repository_revision") == EXPECTED_SOURCE_REVISION, "evidence source revision mismatch")
    require(run.get("github_run_id") == EXPECTED_CAPTURE_RUN_ID, "evidence run id mismatch")
    require(run.get("github_run_attempt") == EXPECTED_CAPTURE_RUN_ATTEMPT, "evidence run attempt mismatch")
    require(run.get("github_job") == "capture-b2e02", "evidence job name drift")


def verify(path: Path) -> dict[str, Any]:
    evidence = load(path)
    validate_payload(evidence, EXPECTED_PAYLOAD_SHA256, "canonical")
    require(evidence.get("schema_version") == "000b2-public-b2e02-decode-v1", "schema drift")
    require(evidence.get("task") == "B2E02" and evidence.get("state") == "C0_PRIMARY_DECODE_CAPTURED", "task/state drift")

    authority = evidence.get("authority", {})
    require(authority.get("canonical_authority_base") == EXPECTED_BASE, "authority base drift")
    require(authority.get("attempt_manifest_sha256") == sha(ATTEMPT), "attempt binding drift")
    require(authority.get("attempt_freeze_digest_sha256") == EXPECTED_FREEZE, "freeze binding drift")
    require(authority.get("preprocessing_capture_sha256") == EXPECTED_PREPROCESSING, "preprocessing binding drift")

    candidate = evidence.get("candidate", {})
    require(candidate.get("cell_index") == 2 and candidate.get("candidate_id") == "moonshine-balanced", "candidate cell 2 drift")
    require(candidate.get("family") == "moonshine" and candidate.get("tier") == "BALANCED", "candidate family/tier drift")
    require(candidate.get("runtime_distribution") == "moonshine-voice" and candidate.get("runtime_version") == "0.1.5", "runtime distribution/version drift")
    require(candidate.get("runtime_revision") == "234f60faa0eb388b01cdf7e60aca232af37aefda", "runtime revision drift")
    require(candidate.get("model_arch") == 5 and candidate.get("model_asset_root") == "quantized_26_08_21", "model identity drift")
    artifacts = candidate.get("artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 8, "artifact evidence cardinality drift")
    for row in artifacts:
        require(isinstance(row, dict), "artifact row malformed")
        require(isinstance(row.get("sha256"), str) and SHA64.fullmatch(row["sha256"]) is not None, "artifact digest malformed")
        require(isinstance(row.get("size_bytes"), int) and row["size_bytes"] > 0, "artifact size malformed")

    require(evidence.get("c0_controls") == {
        "candidate_specific_audio_transform_used": False,
        "context": None,
        "identical_frozen_audio_required_across_candidates": True,
        "keyterms": [],
        "repository_context_used": False,
        "test_specific_context_used": False,
    }, "C0 controls drift")

    run = evidence.get("run", {})
    source = run.get("repository_revision")
    require(isinstance(source, str) and SHA40.fullmatch(source) is not None, "source revision malformed")
    require(source == EXPECTED_SOURCE_REVISION, "source revision drift")
    subprocess.run(["git", "cat-file", "-e", f"{source}^{{commit}}"], check=True)
    require(run.get("github_repository") == "TheHalfMoon/Wispral", "repository provenance drift")
    require(run.get("timing_semantics") == "DIAGNOSTIC_ONLY" and run.get("comparative_performance_authorized") is False, "timing semantics drift")

    expected = preprocessing_index()
    execution = evidence.get("execution", {})
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240 and execution.get("input_count") == 240, "execution coverage drift")
    for key in ("reference_transcripts_loaded_by_decoder", "accuracy_scoring_performed", "comparative_ranking_present", "performance_claim_present"):
        require(execution.get(key) is False, f"forbidden execution claim: {key}")
    require(execution.get("all_frozen_input_hashes_reverified") is True, "input hash revalidation missing")

    seen: set[str] = set()
    decoded = failed = 0
    record_keys = {"utterance_id", "source_partition", "canonical_preprocessed_file_sha256", "status", "raw_lines", "raw_transcript", "failure", "decode_wall_seconds"}
    for row in records:
        require(isinstance(row, dict) and set(row) == record_keys, "record key-set drift")
        uid = row.get("utterance_id")
        require(uid in expected and uid not in seen, f"utterance identity drift: {uid}")
        seen.add(uid)
        require(row.get("source_partition") == expected[uid].get("source_partition"), f"partition drift: {uid}")
        require(row.get("canonical_preprocessed_file_sha256") == expected[uid].get("canonical_preprocessed_file_sha256"), f"input digest drift: {uid}")
        require(isinstance(row.get("decode_wall_seconds"), (int, float)) and row["decode_wall_seconds"] >= 0, f"timing malformed: {uid}")
        require(isinstance(row.get("raw_lines"), list) and all(isinstance(x, str) for x in row["raw_lines"]), f"raw lines malformed: {uid}")
        require(isinstance(row.get("raw_transcript"), str), f"raw transcript malformed: {uid}")
        if row.get("status") == "DECODED":
            decoded += 1
            require(row.get("failure") is None, f"decoded row has failure: {uid}")
            require(row["raw_transcript"] == " ".join(row["raw_lines"]).strip(), f"raw transcript join drift: {uid}")
        elif row.get("status") == "FAILED":
            failed += 1
            require(row["raw_lines"] == [] and row["raw_transcript"] == "", f"failed row fabricated transcript: {uid}")
            require(isinstance(row.get("failure"), dict), f"failure evidence missing: {uid}")
        else:
            raise VerifyError(f"unknown decode status: {uid}")
    require(len(seen) == 240 and execution.get("decoded_count") == decoded and execution.get("failure_count") == failed, "result accounting drift")

    guards = evidence.get("claim_guards", {})
    require(guards.get("candidate_decoding_started") is True and guards.get("primary_decoding_started") is True, "execution-start guards missing")
    require(guards.get("completed_through") == "B2E02_EXECUTION_ONLY" and guards.get("b2e03_authorized") is False, "execution/reconciliation boundary drift")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech claim drift")
    require(guards.get("production_stt_selected") is False and guards.get("product_code_authorized") is False, "product authority drift")
    verify_provenance(evidence)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    try:
        static_frontier()
        if args.static_only:
            print("B2E02_STATIC=PASS")
            return 0
        evidence = verify(args.evidence)
        print("B2E02_EVIDENCE=PASS")
        print(f"B2E02_SOURCE_REVISION={evidence['run']['repository_revision']}")
        print(f"B2E02_INPUTS={evidence['execution']['input_count']}")
        print(f"B2E02_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2E02_FAILURES={evidence['execution']['failure_count']}")
        print("B2E02_DUPLICATE_INPUT_IDENTITY=PASS")
        print("B2E02_DUPLICATE_STATUS_IDENTITY=PASS")
        print("B2E02_DUPLICATE_RAW_TRANSCRIPT_IDENTITY=DIFF")
        print(f"B2E02_DUPLICATE_RAW_TRANSCRIPT_DIFFERENCE_COUNT={EXPECTED_DUPLICATE_TRANSCRIPT_DIFFERENCES}")
        print("B2E03_AUTHORIZED=NO")
        return 0
    except (VerifyError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"B2E02_EVIDENCE=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
