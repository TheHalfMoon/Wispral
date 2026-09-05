#!/usr/bin/env python3
"""Verify committed B2E01 moonshine-compact C0 execution evidence."""

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
EVIDENCE = PUBLIC / "b2e01-moonshine-compact.json"
DUPLICATE_EVIDENCE = PUBLIC / "b2e01-moonshine-compact-duplicate-run-33928583817.json"
PROVENANCE = PUBLIC / "b2e01-provenance.json"
ATTEMPT = PUBLIC / "attempt-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
READINESS = PUBLIC / "readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"

EXPECTED_BASE = "6607b1b1a13daebe1c267f82e3295be9b3bdea32"
EXPECTED_SOURCE_REVISION = "1a39e9c177fce1f45c46854ffc58640a35dbe2d0"
EXPECTED_FREEZE = "af4d5009e293daef5d8f629ca91af653f5f591448cd94d4555473a51e2d1da86"
EXPECTED_PREPROCESSING = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"

EXPECTED_RAW_EVIDENCE_SHA256 = "af2c604a3f402789d69e424291c5f41a24eca0f575b1b26a3822da73dd0c4a8e"
EXPECTED_PAYLOAD_SHA256 = "a8a15d33e9a2c0b2ab3c2c087f20b645175bf027b8aa0f4b7a954a69af5a3198"
EXPECTED_CAPTURE_RUN_ID = 33928586213
EXPECTED_CAPTURE_RUN_ATTEMPT = 1
EXPECTED_CAPTURE_JOB_ID = 101202392820
EXPECTED_ARTIFACT_ID = 9957837509
EXPECTED_ARTIFACT_NAME = "b2e01-moonshine-compact-1a39e9c177fce1f45c46854ffc58640a35dbe2d0"
EXPECTED_ARTIFACT_ZIP_SHA256 = "cf617a2453048bcb0dbd17b8a2a62389d5f90778bd9a79d4265bfc6f306b1367"

EXPECTED_DUPLICATE_RAW_EVIDENCE_SHA256 = "5b7c9937836607a62f7319c59865b071b784d464aa35c07e53f15c2d65ea4f3e"
EXPECTED_DUPLICATE_PAYLOAD_SHA256 = "ad749bfba117d2c20ba97e818b2662e0f1b88969ce59669ac876e8fc1d5bfb7d"
EXPECTED_DUPLICATE_RUN_ID = 33928583817
EXPECTED_DUPLICATE_RUN_ATTEMPT = 1
EXPECTED_DUPLICATE_JOB_ID = 101202331743
EXPECTED_DUPLICATE_ARTIFACT_ID = 9957866136
EXPECTED_DUPLICATE_ARTIFACT_ZIP_SHA256 = "3ce79885b28491e2d9fcd5c0a4dd617c51a946c755d13f72dc198fb1d50e83ca"
EXPECTED_SEMANTIC_RECORDS_SHA256 = "e0216b7c82ddaa687d221b46eafd676e4e58a4f59856b817c9f1cb250d9cea34"

EXPECTED_CANCELLED_RUN_ID = 33929116272
EXPECTED_CANCELLED_JOB_ID = 101203912236
EXPECTED_CANCELLED_HEAD = "e3b2d865638a0327973958e6008d982395788c5c"

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class VerifyError(ValueError):
    """Raised when committed B2E01 evidence fails closed."""


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


def semantic_records_sha256(evidence: dict[str, Any]) -> str:
    records = evidence.get("execution", {}).get("records")
    require(isinstance(records, list), "semantic record list missing")
    normalized = []
    for row in records:
        require(isinstance(row, dict), "semantic record must be object")
        normalized.append({
            "utterance_id": row.get("utterance_id"),
            "source_partition": row.get("source_partition"),
            "canonical_preprocessed_file_sha256": row.get("canonical_preprocessed_file_sha256"),
            "status": row.get("status"),
            "raw_lines": row.get("raw_lines"),
            "raw_transcript": row.get("raw_transcript"),
            "failure": row.get("failure"),
        })
    return hashlib.sha256(canonical(normalized)).hexdigest()


def static_frontier() -> None:
    readiness = load(READINESS)
    tasks = TASKS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    completed = readiness.get("completed_through")

    if completed == "B2P08":
        require(str(readiness.get("next_action", "")).startswith("Execute B2E01 only:"), "B2E01 is not sole pre-reconciliation next action")
        require("Do not begin B2E02" in readiness["next_action"], "B2E02 closure missing before B2E01 reconciliation")
        require("- [ ] `B2E01`" in tasks and "- [ ] `B2E02`" in tasks, "B2E01 execution PR self-reconciled canonical task state")
        require("B2E01 is the sole current bounded execution unit" in current, "CURRENT pre-reconciliation frontier drift")
    elif completed == "B2E01":
        require(str(readiness.get("next_action", "")).startswith("Execute B2E02 only:"), "B2E02 is not sole post-B2E01 next action")
        require("- [x] `B2E01`" in tasks and "- [ ] `B2E02`" in tasks, "B2E01/B2E02 canonical task frontier drift")
        require("B2E02 (`moonshine-balanced`) is the sole current bounded execution unit" in current, "CURRENT post-B2E01 frontier drift")
    else:
        require("- [x] `B2E01`" in tasks, "later canonical state lost B2E01 completion")

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


def verify_provenance(primary: dict[str, Any], duplicate: dict[str, Any]) -> None:
    require(sha(EVIDENCE) == EXPECTED_RAW_EVIDENCE_SHA256, "raw canonical B2E01 evidence bytes drift")
    require(sha(DUPLICATE_EVIDENCE) == EXPECTED_DUPLICATE_RAW_EVIDENCE_SHA256, "raw duplicate B2E01 evidence bytes drift")

    provenance = load(PROVENANCE)
    require(provenance.get("schema_version") == "000b2-public-b2e01-provenance-v2", "provenance schema drift")
    require(provenance.get("task") == "B2E01", "provenance task drift")
    require(provenance.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-001", "provenance attempt drift")
    require(provenance.get("candidate_id") == "moonshine-compact", "provenance candidate drift")
    require(
        provenance.get("provenance_status")
        == "RECORDED_FROM_EXACT_GITHUB_ACTIONS_RUN_ARTIFACT_AND_DUPLICATE_RECONCILIATION_METADATA",
        "provenance status drift",
    )

    canonical_source = provenance.get("canonical_evidence_source", {})
    require(canonical_source == {
        "role": "CANONICAL_EVIDENCE_SOURCE",
        "selection_basis": "EXISTING_SEALED_PULL_REQUEST_ARTIFACT_IDENTITY; NOT_RESULT_DRIVEN",
        "workflow_name": "Internal B2E01 Public C0 Capture",
        "event": "pull_request",
        "conclusion": "success",
        "run_id": EXPECTED_CAPTURE_RUN_ID,
        "run_attempt": EXPECTED_CAPTURE_RUN_ATTEMPT,
        "job_id": EXPECTED_CAPTURE_JOB_ID,
        "source_revision": EXPECTED_SOURCE_REVISION,
        "artifact_id": EXPECTED_ARTIFACT_ID,
        "artifact_name": EXPECTED_ARTIFACT_NAME,
        "artifact_zip_sha256": EXPECTED_ARTIFACT_ZIP_SHA256,
        "evidence_path": "research/000b2-public/b2e01-moonshine-compact.json",
        "evidence_raw_file_sha256": EXPECTED_RAW_EVIDENCE_SHA256,
        "evidence_payload_sha256": EXPECTED_PAYLOAD_SHA256,
    }, "canonical capture provenance drift")

    related = provenance.get("related_capture_runs")
    require(isinstance(related, list) and len(related) == 2, "related capture run inventory drift")
    duplicate_record, cancelled_record = related
    require(duplicate_record == {
        "role": "SUCCESSFUL_DUPLICATE_NONCANONICAL",
        "reconciliation_status": "PRESERVED_AND_SEMANTICALLY_COMPARED_TO_CANONICAL_EVIDENCE",
        "workflow_name": "Internal B2E01 Public C0 Capture",
        "event": "push",
        "conclusion": "success",
        "run_id": EXPECTED_DUPLICATE_RUN_ID,
        "run_attempt": EXPECTED_DUPLICATE_RUN_ATTEMPT,
        "job_id": EXPECTED_DUPLICATE_JOB_ID,
        "source_revision": EXPECTED_SOURCE_REVISION,
        "artifact_id": EXPECTED_DUPLICATE_ARTIFACT_ID,
        "artifact_name": EXPECTED_ARTIFACT_NAME,
        "artifact_zip_sha256": EXPECTED_DUPLICATE_ARTIFACT_ZIP_SHA256,
        "evidence_path": "research/000b2-public/b2e01-moonshine-compact-duplicate-run-33928583817.json",
        "evidence_raw_file_sha256": EXPECTED_DUPLICATE_RAW_EVIDENCE_SHA256,
        "evidence_payload_sha256": EXPECTED_DUPLICATE_PAYLOAD_SHA256,
        "semantic_records_sha256": EXPECTED_SEMANTIC_RECORDS_SHA256,
        "semantic_equivalence_to_canonical": "PASS",
        "allowed_differences": [
            "github_run_id",
            "decode_wall_seconds",
            "total_decode_wall_seconds",
            "evidence_payload_sha256",
        ],
        "selection_effect": "NONE",
    }, "successful duplicate provenance drift")
    require(cancelled_record == {
        "role": "CANCELLED_LATER_DUPLICATE_NO_DECODE",
        "workflow_name": "Internal B2E01 Public C0 Capture",
        "event": "pull_request",
        "conclusion": "cancelled",
        "run_id": EXPECTED_CANCELLED_RUN_ID,
        "run_attempt": 1,
        "job_id": EXPECTED_CANCELLED_JOB_ID,
        "head_revision": EXPECTED_CANCELLED_HEAD,
        "decode_step_conclusion": "skipped",
        "artifact_count": 0,
    }, "cancelled later duplicate provenance drift")

    reconciliation = provenance.get("duplicate_reconciliation", {})
    require(reconciliation == {
        "cause": "INITIAL_PUSH_AND_PULL_REQUEST_CAPTURE_RUNS_USED_DISTINCT_GITHUB_REF_CONCURRENCY_KEYS",
        "successful_execution_count_for_cell_1": 2,
        "canonical_evidence_source_count": 1,
        "transcript_status_input_identity_equivalence": "PASS",
        "timing_values_are_diagnostic_only": True,
        "result_driven_evidence_selection": False,
        "b2e02_authorized": False,
    }, "duplicate reconciliation record drift")

    claims = provenance.get("claims", {})
    require(claims == {
        "b2e02_authorized": False,
        "comparative_performance_authorized": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "product_code_authorized": False,
        "production_stt_selected": False,
        "timing_semantics": "DIAGNOSTIC_ONLY",
    }, "provenance claim guards drift")

    primary_run = primary.get("run", {})
    duplicate_run = duplicate.get("run", {})
    require(primary_run.get("repository_revision") == EXPECTED_SOURCE_REVISION, "canonical evidence source revision mismatch")
    require(primary_run.get("github_run_id") == EXPECTED_CAPTURE_RUN_ID, "canonical evidence run id mismatch")
    require(primary_run.get("github_run_attempt") == EXPECTED_CAPTURE_RUN_ATTEMPT, "canonical evidence run attempt mismatch")
    require(primary_run.get("github_job") == "capture-b2e01", "canonical evidence job name drift")
    require(duplicate_run.get("repository_revision") == EXPECTED_SOURCE_REVISION, "duplicate evidence source revision mismatch")
    require(duplicate_run.get("github_run_id") == EXPECTED_DUPLICATE_RUN_ID, "duplicate evidence run id mismatch")
    require(duplicate_run.get("github_run_attempt") == EXPECTED_DUPLICATE_RUN_ATTEMPT, "duplicate evidence run attempt mismatch")
    require(duplicate_run.get("github_job") == "capture-b2e01", "duplicate evidence job name drift")


def verify_payload_digest(evidence: dict[str, Any], expected_payload: str, label: str) -> None:
    require(evidence.get("evidence_payload_sha256") == expected_payload, f"{label} recorded payload digest drift")
    unsigned = dict(evidence)
    payload = unsigned.pop("evidence_payload_sha256", None)
    require(isinstance(payload, str) and SHA64.fullmatch(payload) is not None, f"{label} payload digest missing")
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == payload, f"{label} payload digest mismatch")


def verify_duplicate_equivalence(primary: dict[str, Any], duplicate: dict[str, Any]) -> None:
    verify_payload_digest(duplicate, EXPECTED_DUPLICATE_PAYLOAD_SHA256, "duplicate")
    require(duplicate.get("schema_version") == primary.get("schema_version"), "duplicate schema drift")
    require(duplicate.get("task") == primary.get("task"), "duplicate task drift")
    require(duplicate.get("state") == primary.get("state"), "duplicate state drift")
    require(duplicate.get("authority") == primary.get("authority"), "duplicate authority binding drift")
    require(duplicate.get("candidate") == primary.get("candidate"), "duplicate candidate identity drift")
    require(duplicate.get("c0_controls") == primary.get("c0_controls"), "duplicate C0 control drift")
    require(duplicate.get("claim_guards") == primary.get("claim_guards"), "duplicate claim guard drift")

    primary_run = dict(primary.get("run", {}))
    duplicate_run = dict(duplicate.get("run", {}))
    require(primary_run.pop("github_run_id", None) == EXPECTED_CAPTURE_RUN_ID, "canonical run id drift")
    require(duplicate_run.pop("github_run_id", None) == EXPECTED_DUPLICATE_RUN_ID, "duplicate run id drift")
    require(primary_run == duplicate_run, "duplicate runtime identity differs beyond run id")

    primary_execution = primary.get("execution", {})
    duplicate_execution = duplicate.get("execution", {})
    for key in primary_execution:
        if key in {"records", "total_decode_wall_seconds"}:
            continue
        require(duplicate_execution.get(key) == primary_execution.get(key), f"duplicate execution field drift: {key}")
    require(
        isinstance(primary_execution.get("total_decode_wall_seconds"), (int, float))
        and primary_execution["total_decode_wall_seconds"] >= 0,
        "canonical total diagnostic timing malformed",
    )
    require(
        isinstance(duplicate_execution.get("total_decode_wall_seconds"), (int, float))
        and duplicate_execution["total_decode_wall_seconds"] >= 0,
        "duplicate total diagnostic timing malformed",
    )

    primary_records = primary_execution.get("records")
    duplicate_records = duplicate_execution.get("records")
    require(isinstance(primary_records, list) and isinstance(duplicate_records, list), "duplicate record lists missing")
    require(len(primary_records) == len(duplicate_records) == 240, "duplicate record cardinality drift")
    primary_by_id = {row["utterance_id"]: row for row in primary_records}
    duplicate_by_id = {row["utterance_id"]: row for row in duplicate_records}
    require(len(primary_by_id) == len(duplicate_by_id) == 240, "duplicate record identity collision")
    require(set(primary_by_id) == set(duplicate_by_id), "duplicate utterance membership drift")

    for uid in sorted(primary_by_id):
        canonical_row = dict(primary_by_id[uid])
        duplicate_row = dict(duplicate_by_id[uid])
        canonical_timing = canonical_row.pop("decode_wall_seconds", None)
        duplicate_timing = duplicate_row.pop("decode_wall_seconds", None)
        require(isinstance(canonical_timing, (int, float)) and canonical_timing >= 0, f"canonical timing malformed: {uid}")
        require(isinstance(duplicate_timing, (int, float)) and duplicate_timing >= 0, f"duplicate timing malformed: {uid}")
        require(canonical_row == duplicate_row, f"duplicate semantic record drift: {uid}")

    primary_fp = semantic_records_sha256(primary)
    duplicate_fp = semantic_records_sha256(duplicate)
    require(primary_fp == EXPECTED_SEMANTIC_RECORDS_SHA256, "canonical semantic record fingerprint drift")
    require(duplicate_fp == EXPECTED_SEMANTIC_RECORDS_SHA256, "duplicate semantic record fingerprint drift")
    require(primary_fp == duplicate_fp, "duplicate semantic equivalence failure")


def verify(path: Path) -> dict[str, Any]:
    evidence = load(path)
    duplicate = load(DUPLICATE_EVIDENCE)
    verify_payload_digest(evidence, EXPECTED_PAYLOAD_SHA256, "canonical")
    verify_duplicate_equivalence(evidence, duplicate)
    verify_provenance(evidence, duplicate)

    require(evidence.get("schema_version") == "000b2-public-b2e01-decode-v1", "schema drift")
    require(evidence.get("task") == "B2E01" and evidence.get("state") == "C0_PRIMARY_DECODE_CAPTURED", "task/state drift")

    authority = evidence.get("authority", {})
    require(authority.get("canonical_authority_base") == EXPECTED_BASE, "authority base drift")
    require(authority.get("attempt_manifest_sha256") == sha(ATTEMPT), "attempt binding drift")
    require(authority.get("attempt_freeze_digest_sha256") == EXPECTED_FREEZE, "freeze binding drift")
    require(authority.get("preprocessing_capture_sha256") == EXPECTED_PREPROCESSING, "preprocessing binding drift")

    candidate = evidence.get("candidate", {})
    require(candidate.get("cell_index") == 1 and candidate.get("candidate_id") == "moonshine-compact", "candidate cell drift")
    require(candidate.get("family") == "moonshine" and candidate.get("tier") == "COMPACT", "candidate family/tier drift")
    require(
        candidate.get("runtime_distribution") == "moonshine-voice"
        and candidate.get("runtime_version") == "0.1.5",
        "runtime distribution/version drift",
    )
    require(candidate.get("runtime_revision") == "234f60faa0eb388b01cdf7e60aca232af37aefda", "runtime revision drift")
    require(candidate.get("model_arch") == 4 and candidate.get("model_asset_root") == "quantized_26_08_21", "model identity drift")
    artifacts = candidate.get("artifacts")
    require(isinstance(artifacts, list) and artifacts, "artifact evidence missing")
    for row in artifacts:
        require(isinstance(row.get("sha256"), str) and SHA64.fullmatch(row["sha256"]) is not None, "artifact digest malformed")

    require(evidence.get("c0_controls") == {
        "repository_context_used": False,
        "test_specific_context_used": False,
        "candidate_specific_audio_transform_used": False,
        "keyterms": [],
        "context": None,
        "identical_frozen_audio_required_across_candidates": True,
    }, "C0 controls drift")

    run = evidence.get("run", {})
    source = run.get("repository_revision")
    require(isinstance(source, str) and SHA40.fullmatch(source) is not None, "source revision malformed")
    require(source == EXPECTED_SOURCE_REVISION, "source revision drift")
    subprocess.run(["git", "cat-file", "-e", f"{source}^{{commit}}"], check=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", source, "HEAD"], check=True)
    require(run.get("github_repository") == "TheHalfMoon/Wispral", "repository provenance drift")
    require(
        run.get("timing_semantics") == "DIAGNOSTIC_ONLY"
        and run.get("comparative_performance_authorized") is False,
        "timing semantics drift",
    )

    expected = preprocessing_index()
    execution = evidence.get("execution", {})
    records = execution.get("records")
    require(
        isinstance(records, list)
        and len(records) == 240
        and execution.get("input_count") == 240,
        "execution coverage drift",
    )
    for key in (
        "reference_transcripts_loaded_by_decoder",
        "accuracy_scoring_performed",
        "comparative_ranking_present",
        "performance_claim_present",
    ):
        require(execution.get(key) is False, f"forbidden execution claim: {key}")
    require(execution.get("all_frozen_input_hashes_reverified") is True, "input hash revalidation missing")

    seen: set[str] = set()
    decoded = failed = 0
    record_keys = {
        "utterance_id",
        "source_partition",
        "canonical_preprocessed_file_sha256",
        "status",
        "raw_lines",
        "raw_transcript",
        "failure",
        "decode_wall_seconds",
    }
    for row in records:
        require(isinstance(row, dict) and set(row) == record_keys, "record key-set drift")
        uid = row.get("utterance_id")
        require(uid in expected and uid not in seen, f"utterance identity drift: {uid}")
        seen.add(uid)
        require(row.get("source_partition") == expected[uid].get("source_partition"), f"partition drift: {uid}")
        require(
            row.get("canonical_preprocessed_file_sha256")
            == expected[uid].get("canonical_preprocessed_file_sha256"),
            f"input digest drift: {uid}",
        )
        require(
            isinstance(row.get("decode_wall_seconds"), (int, float))
            and row["decode_wall_seconds"] >= 0,
            f"timing malformed: {uid}",
        )
        require(
            isinstance(row.get("raw_lines"), list)
            and all(isinstance(item, str) for item in row["raw_lines"]),
            f"raw lines malformed: {uid}",
        )
        require(isinstance(row.get("raw_transcript"), str), f"raw transcript malformed: {uid}")
        if row.get("status") == "DECODED":
            decoded += 1
            require(row.get("failure") is None, f"decoded row has failure: {uid}")
            require(
                row["raw_transcript"] == " ".join(row["raw_lines"]).strip(),
                f"raw transcript join drift: {uid}",
            )
        elif row.get("status") == "FAILED":
            failed += 1
            require(row["raw_lines"] == [] and row["raw_transcript"] == "", f"failed row fabricated transcript: {uid}")
            require(isinstance(row.get("failure"), dict), f"failure evidence missing: {uid}")
        else:
            raise VerifyError(f"unknown decode status: {uid}")
    require(
        len(seen) == 240
        and execution.get("decoded_count") == decoded
        and execution.get("failure_count") == failed,
        "result accounting drift",
    )
    require(decoded == 240 and failed == 0, "sealed B2E01 result counts drift")

    guards = evidence.get("claim_guards", {})
    require(
        guards.get("candidate_decoding_started") is True
        and guards.get("primary_decoding_started") is True,
        "execution-start guards missing",
    )
    require(
        guards.get("completed_through") == "B2E01_EXECUTION_ONLY"
        and guards.get("b2e02_authorized") is False,
        "execution/reconciliation boundary drift",
    )
    require(
        guards.get("human_developer_speech_accuracy_evidence") == "ABSENT",
        "human developer-speech claim drift",
    )
    require(
        guards.get("production_stt_selected") is False
        and guards.get("product_code_authorized") is False,
        "product authority drift",
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    try:
        static_frontier()
        if args.static_only:
            print("B2E01_STATIC=PASS")
            return 0
        require(
            args.evidence.resolve() == EVIDENCE.resolve(),
            "only committed canonical B2E01 evidence may be verified",
        )
        evidence = verify(args.evidence)
        print("B2E01_EVIDENCE=PASS")
        print(f"B2E01_SOURCE_REVISION={evidence['run']['repository_revision']}")
        print(f"B2E01_CAPTURE_RUN_ID={EXPECTED_CAPTURE_RUN_ID}")
        print(f"B2E01_ARTIFACT_ID={EXPECTED_ARTIFACT_ID}")
        print(f"B2E01_DUPLICATE_RUN_ID={EXPECTED_DUPLICATE_RUN_ID}")
        print(f"B2E01_DUPLICATE_ARTIFACT_ID={EXPECTED_DUPLICATE_ARTIFACT_ID}")
        print("B2E01_DUPLICATE_SEMANTIC_EQUIVALENCE=PASS")
        print(f"B2E01_INPUTS={evidence['execution']['input_count']}")
        print(f"B2E01_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2E01_FAILURES={evidence['execution']['failure_count']}")
        print("B2E02_AUTHORIZED=NO")
        return 0
    except (VerifyError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"B2E01_EVIDENCE=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
