#!/usr/bin/env python3
"""Verify sealed B2R05 ATTEMPT-002 moonshine-compact execution evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
EVIDENCE = PUBLIC / "b2r05-moonshine-compact.json"
PROVENANCE = PUBLIC / "b2r05-provenance.json"
DECODER = PUBLIC / "decode_b2r05.py"
ATTEMPT = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
REBINDING = PUBLIC / "b2r03-preexecution-rebinding.json"
C0 = PUBLIC / "moonshine_streaming_c0.py"
READINESS = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CANONICAL_CURRENT = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"

AUTHORITY_BASE = "9c777ae4f4aaf8387cf54bfa4e8afe80e053ff69"
SOURCE_REVISION = "6ae90c4403cd7e190c1fa222df90e2f6a8682d71"
DECODER_BLOB = "43125c1626d860aa1cb2704d7420a5f72dc7433b"
ATTEMPT_SHA256 = "a2dc8246e4567e670beb3f26e315be93e001e4d9a9037be57ff11fce5a340134"
FREEZE_DIGEST = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
C0_SHA256 = "c0f0093cda7ca036c8a97178364b3840ce7093386a8cb711ccef5f183a4453c0"
EVIDENCE_SHA256 = "c14aaae1ca974e30fee73a7d672bb20910eb9e501601020c5a3f11332d4f00f8"
EVIDENCE_SIZE = 152226
PAYLOAD_SHA256 = "254f0a8f7d0954b3c26ed01aafef8b0c061aae1ceb2fffc2f7b2a0a84aca5cfd"
PROVENANCE_SHA256 = "5050254cfd600678a462fb6530831a76e59482b6f8040cb64b4bee881ca58f4a"
RUN_ID = 34031165041
JOB_ID = 101480807527
WORKFLOW_ID = 351513766
ARTIFACT_ID = 9989016229
ARTIFACT_NAME = "b2r05-moonshine-compact-6ae90c4403cd7e190c1fa222df90e2f6a8682d71"
ARTIFACT_ZIP_SHA256 = "f48546a778f5a8e9202fb44edebf78e2fd3596bc8cded939350d1039e2463227"
FAILURE = {"type": "C0HarnessError", "message": "Moonshine C0 input exceeds the frozen 12-second primary utterance bound"}
PREFIX = ["B2R01", "B2R02", "B2R03", "B2R04"]


class VerifyError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise VerifyError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def verify_frontier() -> None:
    readiness = load(READINESS)
    tasks = TASKS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    canonical_current = CANONICAL_CURRENT.read_text(encoding="utf-8")
    require(readiness.get("state") == "RECOVERY_READY", "recovery lane not ready")
    require(readiness.get("qualified_workflow_change_paths") == [], "workflow drift unexpectedly authorized")
    require(readiness.get("claim_guards") == {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
    }, "recovery claim guards drift")
    replacement = readiness.get("replacement_attempt", {})
    require(replacement.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-002", "replacement attempt drift")
    require(replacement.get("frozen") is True and replacement.get("primary_decode_entry_open") is True,
            "ATTEMPT-002 entry state drift")
    completed = readiness.get("completed_recovery_tasks")
    active = readiness.get("active_recovery_unit")
    if completed == PREFIX and active == "B2R05":
        require(str(readiness.get("next_action", "")).startswith("Qualify B2R05 only:"), "B2R05 frontier drift")
        require("- [ ] `B2R05`" in tasks and "- [ ] `B2R06`" in tasks, "pre-reconciliation task ledger drift")
        require("active recovery unit `B2R05`" in current and "B2R05" in canonical_current, "B2R05 canonical frontier drift")
    elif completed == PREFIX + ["B2R05"] and active == "B2R06":
        require(str(readiness.get("next_action", "")).startswith("Qualify B2R06 only:"), "B2R06 frontier drift")
        require("- [x] `B2R05`" in tasks and "- [ ] `B2R06`" in tasks, "post-reconciliation task ledger drift")
        require("active recovery unit `B2R06`" in current and "B2R06" in canonical_current, "B2R06 canonical frontier drift")
    else:
        require(isinstance(completed, list) and "B2R05" in completed and "- [x] `B2R05`" in tasks,
                "later state lost B2R05 completion")


def verify_static_identities() -> None:
    attempt = load(ATTEMPT)
    require(sha256(ATTEMPT) == ATTEMPT_SHA256, "ATTEMPT-002 bytes drift")
    require(attempt.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-002", "ATTEMPT-002 id drift")
    require(attempt.get("frozen") is True and attempt.get("freeze_digest_sha256") == FREEZE_DIGEST, "ATTEMPT-002 freeze drift")
    require(sha256(PREPROCESSING) == PREPROCESSING_SHA256, "preprocessing bytes drift")
    require(sha256(REBINDING) == REBINDING_SHA256, "B2R03 rebinding bytes drift")
    require(sha256(C0) == C0_SHA256, "corrected C0 bytes drift")
    require(git("hash-object", str(DECODER.relative_to(ROOT))) == DECODER_BLOB, "mergeable decoder blob drift")
    require(git("rev-parse", f"{SOURCE_REVISION}^{{commit}}") == SOURCE_REVISION, "source execution commit unavailable")
    require(git("rev-parse", f"{SOURCE_REVISION}:research/000b2-public/decode_b2r05.py") == DECODER_BLOB,
            "source execution decoder blob drift")


def verify_provenance() -> None:
    require(sha256(PROVENANCE) == PROVENANCE_SHA256, "provenance bytes drift")
    p = load(PROVENANCE)
    require((p.get("task"), p.get("attempt_id"), p.get("candidate_id")) ==
            ("B2R05", "000B2-PUBLIC-ATTEMPT-002", "moonshine-compact"), "provenance identity drift")
    source = p.get("canonical_evidence_source", {})
    require(source.get("selection_basis") ==
            "FIRST_EXECUTION_THAT_PASSED_CURRENT_B2R05_AUTHORITY_FROZEN_INPUT_DECODE_SEMANTICS_AND_ARTIFACT_GATES; NOT_RESULT_DRIVEN",
            "evidence selection basis drift")
    require(source.get("workflow_id") == WORKFLOW_ID and source.get("run_id") == RUN_ID and source.get("job_id") == JOB_ID,
            "capture run provenance drift")
    require(source.get("source_revision") == SOURCE_REVISION and source.get("execution_decoder_blob_sha") == DECODER_BLOB,
            "capture source provenance drift")
    require(source.get("artifact_id") == ARTIFACT_ID and source.get("artifact_name") == ARTIFACT_NAME,
            "artifact provenance drift")
    require(source.get("artifact_zip_sha256") == ARTIFACT_ZIP_SHA256, "artifact ZIP digest drift")
    require(source.get("evidence_raw_file_sha256") == EVIDENCE_SHA256 and source.get("evidence_raw_file_size_bytes") == EVIDENCE_SIZE,
            "raw evidence provenance drift")
    require(source.get("evidence_payload_sha256") == PAYLOAD_SHA256, "payload provenance drift")
    related = p.get("related_execution_attempts")
    require(
        isinstance(related, list)
        and [r.get("run_id") for r in related] == [34030579352, 34030672630, 34030712272, 34030872729],
        "failed attempt chronology drift",
    )
    for row in related:
        require(row.get("role") == "FAILED_PRE_PRIMARY_NONCANONICAL" and row.get("primary_decode_started") is False,
                "failed attempt primary-boundary drift")
        require(row.get("artifact_count") == 0 and row.get("selection_effect") == "NONE", "failed attempt selection drift")
    accounting = p.get("result_accounting", {})
    require((accounting.get("input_count"), accounting.get("decoded_count"), accounting.get("failure_count")) == (240, 209, 31),
            "provenance result accounting drift")
    require(accounting.get("all_failures_are_frozen_c0_preinference_bound_rejections") is True and
            accounting.get("failures_preserved_without_retry_or_c0_change") is True and
            accounting.get("reference_transcripts_loaded_by_decoder") is False and
            accounting.get("accuracy_scoring_performed") is False and
            accounting.get("result_driven_evidence_selection") is False, "provenance guard drift")
    require(p.get("claims") == {
        "b2r06_authorized": False,
        "comparative_result_available": False,
        "comparative_performance_authorized": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "production_stt_selected": False,
        "product_code_authorized": False,
    }, "provenance claims drift")


def verify_evidence() -> dict[str, Any]:
    require(EVIDENCE.stat().st_size == EVIDENCE_SIZE and sha256(EVIDENCE) == EVIDENCE_SHA256, "raw evidence bytes drift")
    e = load(EVIDENCE)
    payload = e.get("evidence_payload_sha256")
    unsigned = dict(e)
    unsigned.pop("evidence_payload_sha256", None)
    require(payload == PAYLOAD_SHA256 and hashlib.sha256(canonical(unsigned)).hexdigest() == PAYLOAD_SHA256,
            "evidence payload digest mismatch")
    require((e.get("schema_version"), e.get("task"), e.get("state"), e.get("attempt_id")) ==
            ("000b2-public-b2r05-decode-v1", "B2R05", "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED", "000B2-PUBLIC-ATTEMPT-002"),
            "evidence task/state drift")
    authority = e.get("authority", {})
    require(authority.get("canonical_authority_base") == AUTHORITY_BASE and
            authority.get("attempt_freeze_digest_sha256") == FREEZE_DIGEST and
            authority.get("preprocessing_capture_sha256") == PREPROCESSING_SHA256 and
            authority.get("b2r03_rebinding_sha256") == REBINDING_SHA256 and
            authority.get("corrected_c0_harness_sha256") == C0_SHA256, "evidence authority binding drift")
    candidate = e.get("candidate", {})
    require((candidate.get("cell_index"), candidate.get("candidate_id"), candidate.get("family"), candidate.get("tier")) ==
            (1, "moonshine-compact", "moonshine", "COMPACT"), "candidate identity drift")
    require(candidate.get("runtime_distribution") == "moonshine-voice" and candidate.get("runtime_distribution_version") == "0.1.5" and
            candidate.get("runtime_revision") == "234f60faa0eb388b01cdf7e60aca232af37aefda" and
            candidate.get("model_arch") == 4 and candidate.get("model_asset_revision") == "quantized_26_08_21", "runtime/model identity drift")
    controls = e.get("c0_controls", {})
    require(controls == {
        "candidate_specific_audio_transform_used": False, "context": None, "feed_chunk_ms": 500,
        "feed_chunk_samples": 8000, "final_zero_pad_ms": 660, "final_zero_pad_samples": 10560,
        "identical_frozen_audio_required_across_candidates": True, "keyterms": [], "repository_context_used": False,
        "test_specific_context_used": False, "transcription_interval_seconds": 0.5, "vad_threshold": 0.0,
    }, "C0 controls drift")
    run = e.get("run", {})
    require(run.get("repository_revision") == SOURCE_REVISION and run.get("github_run_id") == RUN_ID and
            run.get("github_run_attempt") == 1 and run.get("github_job") == "capture-b2r05" and
            run.get("github_ref") == "refs/heads/research/000b2-b2r05-execution" and run.get("python") == "3.12.14",
            "run identity drift")
    require(run.get("timing_semantics") == "DIAGNOSTIC_ONLY" and run.get("comparative_performance_authorized") is False,
            "timing claim drift")
    preprocessing = load(PREPROCESSING).get("execution", {}).get("records")
    require(isinstance(preprocessing, list) and len(preprocessing) == 240, "preprocessing records missing")
    expected = {r["utterance_id"]: r for r in preprocessing}
    x = e.get("execution", {})
    records = x.get("records")
    require(isinstance(records, list) and len(records) == 240 and x.get("input_count") == 240, "execution coverage drift")
    require(x.get("all_frozen_input_hashes_reverified") is True and x.get("reference_transcripts_loaded_by_decoder") is False and
            x.get("accuracy_scoring_performed") is False and x.get("comparative_ranking_present") is False and
            x.get("performance_claim_present") is False, "execution guard drift")
    seen: set[str] = set(); decoded = 0; failed = 0
    for row in records:
        uid = row.get("utterance_id")
        require(uid in expected and uid not in seen, f"utterance identity drift: {uid}")
        seen.add(uid); src = expected[uid]; frames = src.get("wav_frame_count")
        require(row.get("source_partition") == src.get("source_partition") and
                row.get("canonical_preprocessed_file_sha256") == src.get("canonical_preprocessed_file_sha256"), f"input identity drift: {uid}")
        if row.get("status") == "DECODED":
            decoded += 1
            require(isinstance(frames, int) and frames <= 192000 and row.get("failure") is None, f"decoded bound drift: {uid}")
            require(row.get("raw_transcript") == " ".join(row.get("raw_lines", [])).strip(), f"raw transcript drift: {uid}")
            trace = row.get("feed_trace", {}); chunks = trace.get("speech_chunk_samples")
            require(isinstance(chunks, list) and chunks and all(isinstance(n, int) and 0 < n <= 8000 for n in chunks), f"chunk trace drift: {uid}")
            require(all(n == 8000 for n in chunks[:-1]) and sum(chunks) == trace.get("speech_samples") == frames,
                    f"speech feed trace drift: {uid}")
            require(trace.get("zero_pad_samples") == 10560 and trace.get("sample_rate_hz") == 16000 and
                    trace.get("stream_started") is True and trace.get("stream_stopped") is True, f"stream finalization drift: {uid}")
        elif row.get("status") == "FAILED":
            failed += 1
            require(isinstance(frames, int) and frames > 192000, f"failure bound drift: {uid}")
            require(row.get("failure") == FAILURE and row.get("feed_trace") is None and row.get("raw_lines") == [] and row.get("raw_transcript") == "",
                    f"failure preservation drift: {uid}")
        else:
            raise VerifyError(f"unknown status: {uid}")
    require(len(seen) == 240 and decoded == 209 and failed == 31 and x.get("decoded_count") == 209 and x.get("failure_count") == 31,
            "sealed result accounting drift")
    require(e.get("claim_guards") == {
        "b2r06_authorized": False, "comparative_performance_authorized": False, "comparative_result_available": False,
        "human_developer_speech_accuracy_evidence": "ABSENT", "product_code_authorized": False, "production_stt_selected": False,
    }, "evidence claim guards drift")
    return e


def main() -> int:
    try:
        verify_frontier(); verify_static_identities(); verify_provenance(); evidence = verify_evidence()
        print("B2R05_EVIDENCE=PASS")
        print(f"B2R05_SOURCE_REVISION={SOURCE_REVISION}")
        print(f"B2R05_CAPTURE_RUN_ID={RUN_ID}")
        print(f"B2R05_ARTIFACT_ID={ARTIFACT_ID}")
        print(f"B2R05_INPUTS={evidence['execution']['input_count']}")
        print(f"B2R05_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2R05_FAILURES={evidence['execution']['failure_count']}")
        print("B2R05_FAILURE_CLASS=FROZEN_C0_PREINFERENCE_12_SECOND_BOUND")
        print("B2R06_AUTHORIZED=NO")
        return 0
    except (VerifyError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"B2R05_EVIDENCE=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
