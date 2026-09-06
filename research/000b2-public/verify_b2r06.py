#!/usr/bin/env python3
"""Verify sealed B2R06 ATTEMPT-002 moonshine-balanced execution evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
EVIDENCE = PUBLIC / "b2r06-moonshine-balanced.json"
PROVENANCE = PUBLIC / "b2r06-provenance.json"
DECODER = PUBLIC / "decode_b2r06.py"
ATTEMPT = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
REBINDING = PUBLIC / "b2r03-preexecution-rebinding.json"
C0 = PUBLIC / "moonshine_streaming_c0.py"
READINESS = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CANONICAL_CURRENT = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"

AUTHORITY_BASE = "04056b795a54e38d9d075e4de7aff15df1be2b3b"
SOURCE_REVISION = "fd933886fcaa7a00338de8a96b7b2913124816f1"
DECODER_BLOB = "72555a02e21f3d2790e86ecdf128cee0b19b659e"
ATTEMPT_SHA256 = "a2dc8246e4567e670beb3f26e315be93e001e4d9a9037be57ff11fce5a340134"
FREEZE_DIGEST = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
C0_SHA256 = "c0f0093cda7ca036c8a97178364b3840ce7093386a8cb711ccef5f183a4453c0"
EVIDENCE_SHA256 = "055a93c9a9f15193ffcf8edd7618648f9849f077c8b4c1b49edb9f91d023b722"
EVIDENCE_SIZE = 152146
PAYLOAD_SHA256 = "2b069cf7dbc4eb8ec50c641c2d05e78054cace513d794ebd2f84eefe784f3b38"
PROVENANCE_SHA256 = "3e4257a781fa273a0125dd45e7fce188a2227c5006b3b1304cde3b49a249e8de"
RUN_ID = 34041046129
JOB_ID = 101507742625
WORKFLOW_ID = 351624005
ARTIFACT_ID = 9992059464
ARTIFACT_NAME = "b2r06-moonshine-balanced-fd933886fcaa7a00338de8a96b7b2913124816f1"
ARTIFACT_ZIP_SHA256 = "8d4961084e5c33339cb0317e0387e8856d7d138abad18e204c2adea3715174cb"
FAILURE = {"type": "C0HarnessError", "message": "Moonshine C0 input exceeds the frozen 12-second primary utterance bound"}
PREFIX = ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05"]
MODEL_ARTIFACTS = {
    "adapter.ort": ("3f2a287def57cc094367a0eec3c4f5fc36a32ec420e86764b696920991b20281", 3651296),
    "cross_kv.ort": ("642f6e21cd305be79342207c6f9e6b681d469d55bc48c72b27b84846fb71fd1e", 11643776),
    "decoder_kv.ort": ("193bb366492b74fc4ad338c6778e8d8eb916aaa11b5aa264f9057f4db7759486", 146972408),
    "encoder.ort": ("12915e76ebac7dd287c5ea63965d06103a53ba1ce242a4a34f318f3958c60c37", 94705376),
    "frontend.model.ort": ("95768855c70c8251eeecc05fedf69999da1b8ab16f605c9f457fd3354b0ad6b5", 28720),
    "frontend.weights.ort": ("5ac941f490cbe035b335b99a414cc393d62d4c6f9f2423495b286870d271d709", 11889560),
    "streaming_config.json": ("28e83b7a28e91472692a035e0dae3116422ae43aeb2bef5ed822c44ce89b88af", 513),
    "tokenizer.bin": ("6884b35fd6377d4c4d32336a0bc152f36b64d1e45b6503683cdc238250a8472d", 249974),
}


class VerifyError(ValueError):
    """Raised when sealed B2R06 evidence or authority drifts."""


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
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


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
    if completed == PREFIX and active == "B2R06":
        require(str(readiness.get("next_action", "")).startswith("Qualify B2R06 only:"), "B2R06 frontier drift")
        require("- [x] `B2R05`" in tasks and "- [ ] `B2R06`" in tasks and "- [ ] `B2R07`" in tasks,
                "pre-reconciliation task ledger drift")
        require("active recovery unit `B2R06`" in current and "B2R06" in canonical_current,
                "B2R06 canonical frontier drift")
    elif completed == PREFIX + ["B2R06"] and active == "B2R07":
        require(str(readiness.get("next_action", "")).startswith("Qualify B2R07 only:"), "B2R07 frontier drift")
        require("- [x] `B2R06`" in tasks and "- [ ] `B2R07`" in tasks, "post-reconciliation task ledger drift")
        require("active recovery unit `B2R07`" in current and "B2R07" in canonical_current,
                "B2R07 canonical frontier drift")
    else:
        require(isinstance(completed, list) and "B2R06" in completed and "- [x] `B2R06`" in tasks,
                "later state lost B2R06 completion")


def verify_static_identities() -> None:
    attempt = load(ATTEMPT)
    require(sha256(ATTEMPT) == ATTEMPT_SHA256, "ATTEMPT-002 bytes drift")
    require(attempt.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-002", "ATTEMPT-002 id drift")
    require(attempt.get("frozen") is True and attempt.get("freeze_digest_sha256") == FREEZE_DIGEST,
            "ATTEMPT-002 freeze drift")
    ids = attempt.get("candidate_set", {}).get("candidate_ids")
    require(ids == [
        "moonshine-compact",
        "moonshine-balanced",
        "whispercpp-compact",
        "whispercpp-balanced",
        "sherpa-onnx-compact",
        "sherpa-onnx-balanced",
    ], "frozen candidate order drift")
    require(sha256(PREPROCESSING) == PREPROCESSING_SHA256, "preprocessing bytes drift")
    require(sha256(REBINDING) == REBINDING_SHA256, "B2R03 rebinding bytes drift")
    require(sha256(C0) == C0_SHA256, "corrected C0 bytes drift")
    require(git("hash-object", str(DECODER.relative_to(ROOT))) == DECODER_BLOB, "mergeable decoder blob drift")
    require(git("rev-parse", f"{SOURCE_REVISION}^{{commit}}") == SOURCE_REVISION, "source execution commit unavailable")
    require(git("rev-parse", f"{SOURCE_REVISION}:research/000b2-public/decode_b2r06.py") == DECODER_BLOB,
            "source execution decoder blob drift")


def verify_provenance() -> None:
    require(sha256(PROVENANCE) == PROVENANCE_SHA256, "provenance bytes drift")
    p = load(PROVENANCE)
    require((p.get("task"), p.get("attempt_id"), p.get("candidate_id")) ==
            ("B2R06", "000B2-PUBLIC-ATTEMPT-002", "moonshine-balanced"), "provenance identity drift")
    source = p.get("canonical_evidence_source", {})
    require(source.get("selection_basis") ==
            "FIRST_B2R06_PRIMARY_EXECUTION_AFTER_FAIL_CLOSED_DECODER_BOOTSTRAP_AND_CANDIDATE_ORDER_REPAIR_THAT_PASSED_CURRENT_AUTHORITY_FROZEN_INPUT_STREAMING_C0_SEMANTICS_AND_ARTIFACT_GATES; NOT_RESULT_DRIVEN",
            "evidence selection basis drift")
    require(source.get("workflow_id") == WORKFLOW_ID and source.get("run_id") == RUN_ID and source.get("job_id") == JOB_ID,
            "capture run provenance drift")
    require(source.get("source_revision") == SOURCE_REVISION and
            source.get("execution_decoder_blob_sha") == DECODER_BLOB and
            source.get("mergeable_decoder_blob_sha") == DECODER_BLOB,
            "capture source provenance drift")
    require(source.get("artifact_id") == ARTIFACT_ID and source.get("artifact_name") == ARTIFACT_NAME,
            "artifact provenance drift")
    require(source.get("artifact_zip_sha256") == ARTIFACT_ZIP_SHA256, "artifact ZIP digest drift")
    require(source.get("evidence_raw_file_sha256") == EVIDENCE_SHA256 and
            source.get("evidence_raw_file_size_bytes") == EVIDENCE_SIZE, "raw evidence provenance drift")
    require(source.get("evidence_payload_sha256") == PAYLOAD_SHA256, "payload provenance drift")
    related = p.get("related_pre_primary_runs")
    require(isinstance(related, list) and [r.get("run_id") for r in related] ==
            [34037600568, 34037676040, 34040971762], "pre-primary run chronology drift")
    for row in related:
        require(row.get("primary_decode_started") is False and row.get("artifact_count") == 0 and
                row.get("selection_effect") == "NONE", "pre-primary selection boundary drift")
    accounting = p.get("result_accounting", {})
    require((accounting.get("input_count"), accounting.get("decoded_count"), accounting.get("failure_count")) ==
            (240, 209, 31), "provenance result accounting drift")
    require(accounting.get("all_failures_are_frozen_c0_preinference_bound_rejections") is True and
            accounting.get("failures_preserved_without_retry_or_c0_change") is True and
            accounting.get("reference_transcripts_loaded_by_decoder") is False and
            accounting.get("accuracy_scoring_performed") is False and
            accounting.get("result_driven_evidence_selection") is False, "provenance guard drift")
    require(p.get("claims") == {
        "b2r07_authorized": False,
        "comparative_result_available": False,
        "comparative_performance_authorized": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "production_stt_selected": False,
        "product_code_authorized": False,
    }, "provenance claims drift")


def verify_evidence() -> dict[str, Any]:
    require(EVIDENCE.stat().st_size == EVIDENCE_SIZE and sha256(EVIDENCE) == EVIDENCE_SHA256,
            "raw evidence bytes drift")
    e = load(EVIDENCE)
    payload = e.get("evidence_payload_sha256")
    unsigned = dict(e)
    unsigned.pop("evidence_payload_sha256", None)
    require(payload == PAYLOAD_SHA256 and hashlib.sha256(canonical(unsigned)).hexdigest() == PAYLOAD_SHA256,
            "evidence payload digest mismatch")
    require((e.get("schema_version"), e.get("task"), e.get("state"), e.get("attempt_id")) ==
            ("000b2-public-b2r06-decode-v1", "B2R06", "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED",
             "000B2-PUBLIC-ATTEMPT-002"), "evidence task/state drift")
    authority = e.get("authority", {})
    require(authority.get("canonical_authority_base") == AUTHORITY_BASE and
            authority.get("attempt_freeze_digest_sha256") == FREEZE_DIGEST and
            authority.get("attempt_manifest_sha256") == ATTEMPT_SHA256 and
            authority.get("preprocessing_capture_sha256") == PREPROCESSING_SHA256 and
            authority.get("b2r03_rebinding_sha256") == REBINDING_SHA256 and
            authority.get("corrected_c0_harness_sha256") == C0_SHA256, "evidence authority binding drift")
    candidate = e.get("candidate", {})
    require((candidate.get("cell_index"), candidate.get("candidate_id"), candidate.get("family"), candidate.get("tier")) ==
            (2, "moonshine-balanced", "moonshine", "BALANCED"), "candidate identity drift")
    require(candidate.get("runtime_distribution") == "moonshine-voice" and
            candidate.get("runtime_distribution_version") == "0.1.5" and
            candidate.get("runtime_revision") == "234f60faa0eb388b01cdf7e60aca232af37aefda" and
            candidate.get("model_arch") == 5 and candidate.get("model_asset_revision") == "quantized_26_08_21",
            "runtime/model identity drift")
    observed_artifacts = {row["path"]: (row["sha256"], row["size_bytes"]) for row in candidate.get("artifacts", [])}
    require(observed_artifacts == MODEL_ARTIFACTS, "model artifact manifest drift")
    require(e.get("c0_controls") == {
        "candidate_specific_audio_transform_used": False,
        "context": None,
        "feed_chunk_ms": 500,
        "feed_chunk_samples": 8000,
        "final_zero_pad_ms": 660,
        "final_zero_pad_samples": 10560,
        "identical_frozen_audio_required_across_candidates": True,
        "keyterms": [],
        "repository_context_used": False,
        "test_specific_context_used": False,
        "transcription_interval_seconds": 0.5,
        "vad_threshold": 0.0,
    }, "C0 controls drift")
    run = e.get("run", {})
    require(run.get("repository_revision") == SOURCE_REVISION and run.get("github_run_id") == RUN_ID and
            run.get("github_run_attempt") == 1 and run.get("github_job") == "capture-b2r06" and
            run.get("github_ref") == "refs/heads/research/000b2-b2r06-execution" and
            run.get("github_repository") == "TheHalfMoon/Wispral" and run.get("python") == "3.12.14",
            "run identity drift")
    require(run.get("timing_semantics") == "DIAGNOSTIC_ONLY" and
            run.get("comparative_performance_authorized") is False, "timing claim drift")
    build = run.get("runtime_build_identity", {})
    require(build.get("source_revision") == "234f60faa0eb388b01cdf7e60aca232af37aefda" and
            build.get("source_tree") == "8959001455244ff4cc1a88d9ed1d6bc5e8121b02" and
            build.get("release") == "v0.1.5" and build.get("runtime_origin") == "PINNED_SOURCE_CHECKOUT_BUILD",
            "runtime build identity drift")
    preprocessing = load(PREPROCESSING).get("execution", {}).get("records")
    require(isinstance(preprocessing, list) and len(preprocessing) == 240, "preprocessing records missing")
    expected = {r["utterance_id"]: r for r in preprocessing}
    execution = e.get("execution", {})
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240 and execution.get("input_count") == 240,
            "execution coverage drift")
    require(execution.get("decoded_count") == 209 and execution.get("failure_count") == 31,
            "execution result accounting drift")
    require(execution.get("all_frozen_input_hashes_reverified") is True and
            execution.get("reference_transcripts_loaded_by_decoder") is False and
            execution.get("accuracy_scoring_performed") is False and
            execution.get("comparative_ranking_present") is False and
            execution.get("performance_claim_present") is False, "execution guard drift")
    seen: set[str] = set()
    decoded = failed = 0
    for row in records:
        uid = row.get("utterance_id")
        require(uid in expected and uid not in seen, f"utterance identity drift: {uid}")
        seen.add(uid)
        source = expected[uid]
        require(row.get("source_partition") == source.get("source_partition") and
                row.get("canonical_preprocessed_file_sha256") == source.get("canonical_preprocessed_file_sha256"),
                f"input identity drift: {uid}")
        if row.get("status") == "DECODED":
            decoded += 1
            require(row.get("failure") is None and isinstance(row.get("raw_lines"), list) and
                    isinstance(row.get("raw_transcript"), str), f"decoded output drift: {uid}")
            trace = row.get("feed_trace")
            require(isinstance(trace, dict), f"feed trace missing: {uid}")
            chunks = trace.get("speech_chunk_samples")
            require(isinstance(chunks, list) and chunks and all(isinstance(v, int) and 0 < v <= 8000 for v in chunks),
                    f"chunk bound drift: {uid}")
            require(all(v == 8000 for v in chunks[:-1]), f"non-final chunk drift: {uid}")
            require(sum(chunks) == trace.get("speech_samples") and trace.get("zero_pad_samples") == 10560 and
                    trace.get("sample_rate_hz") == 16000 and trace.get("stream_started") is True and
                    trace.get("stream_stopped") is True, f"feed trace semantics drift: {uid}")
        elif row.get("status") == "FAILED":
            failed += 1
            require(row.get("failure") == FAILURE and row.get("raw_lines") == [] and
                    row.get("raw_transcript") == "" and row.get("feed_trace") is None,
                    f"failure preservation drift: {uid}")
        else:
            raise VerifyError(f"unknown execution status: {uid}")
    require(decoded == 209 and failed == 31 and len(seen) == 240, "record accounting drift")
    require(e.get("claim_guards") == {
        "b2r07_authorized": False,
        "comparative_performance_authorized": False,
        "comparative_result_available": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "product_code_authorized": False,
        "production_stt_selected": False,
    }, "evidence claim guards drift")
    return e


def main() -> int:
    verify_frontier()
    verify_static_identities()
    verify_provenance()
    verify_evidence()
    print("B2R06_EVIDENCE=PASS")
    print(f"B2R06_SOURCE_REVISION={SOURCE_REVISION}")
    print(f"B2R06_CAPTURE_RUN_ID={RUN_ID}")
    print("B2R06_INPUTS=240")
    print("B2R06_DECODED=209")
    print("B2R06_FAILURES=31")
    print("B2R07_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
