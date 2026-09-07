#!/usr/bin/env python3
"""Verify sealed B2R10 ATTEMPT-002 sherpa-onnx-balanced execution evidence."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
EVIDENCE = PUBLIC / "b2r10-sherpa-onnx-balanced.json"
PROVENANCE = PUBLIC / "b2r10-provenance.json"
ATTEMPT = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
REBINDING = PUBLIC / "b2r03-preexecution-rebinding.json"
READINESS = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CANONICAL_CURRENT = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
DECODER = PUBLIC / "decode_b2r10.py"

TASK_SOURCE = "59408cd54edc3ae0ae7d92342e9aa92a8bcecc26"
MATERIALIZED_SOURCE = "77946f348e033a4e244c357b5599ffb76c0da836"
EXECUTION_SOURCE = "1952ce8ef29fc3b7d2ea3c019d058623f15a8920"
DECODER_BLOB = "ee8b2b7e1bb1a6eeeb76bcfeda31098f25855a1c"
EVIDENCE_BLOB = "cfa16eec7ce35e322adb3d000c210d1a564e6128"
RUN_ID = 34161621255
JOB_ID = 101864461547
WORKFLOW_ID = 352600251
ARTIFACT_ID = 10033013012
ARTIFACT_ZIP_SHA256 = "718c32dab605eebbc9973a361d6bb0caf8626ad3a38a1e606cf31ca944b37c82"
ARTIFACT_ZIP_SIZE = 19585
EVIDENCE_SIZE = 248415
EVIDENCE_SHA256 = "5f372636498121d10d22d79f0125730d156504bd3e17972bd3f92f34b96ccecf"
PAYLOAD_SHA256 = "7339e041e92527e5ddf1ec529653b292ccc44e391db54ee349ee2ab34d00cdfb"
PROVENANCE_SIZE = 3665
PROVENANCE_SHA256 = "0a2a4778db5da300b1bedce96400a415b33a4c2f76cd4dea75c6de9e2f3d8d99"
PROVENANCE_PAYLOAD_SHA256 = "285a0477d2a9dd4001132f82ff2e5136820adfe18abf71f7586e3fe98261bfc7"
ATTEMPT_SHA256 = "a2dc8246e4567e670beb3f26e315be93e001e4d9a9037be57ff11fce5a340134"
PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
RUNTIME_REVISION = "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e"
RUNTIME_TREE = "fd2c4e97c9f7499b6ed91c7c2854b4211f61bdc0"
MODEL_ONNX_REVISION = "6037ea07e3abfe599ad00d418968bcf9656e7472"
MODEL_AUX_REVISION = "672fbf1b30579d6585301139bb363f42a0ad4a24"
RUNTIME_MODULE_SHA256 = "9f1d820f337a09099a77e321d6ccddd0ea76b24ebaf815fb9a315cbb0a08b1f3"
MATERIALIZATION_WORKFLOW_ID = 352610808
MATERIALIZATION_RUN_ID = 34162912980
MATERIALIZATION_JOB_ID = 101868220299
MATERIALIZATION_SOURCE = "913279bc419af19a3a547ef487b040c3939c1c8e"

EXPECTED_ARTIFACTS = [
    {"path": "encoder-epoch-99-avg-1-chunk-16-left-128.onnx", "sha256": "a423883ce5754507fd941755ab0b5bc426a84ac670cbe21cf060e9e2c66dc660", "size_bytes": 262127043},
    {"path": "decoder-epoch-99-avg-1-chunk-16-left-128.onnx", "sha256": "7bf787f90b194b307e5a4ad6a34fadb4e748304c35f78a8d66358a05b13ee6ef", "size_bytes": 2092621},
    {"path": "joiner-epoch-99-avg-1-chunk-16-left-128.onnx", "sha256": "210591f72b3c56b8364f85f345dca240bc2b4c00632848f4aa923630d5639d3b", "size_bytes": 1026405},
    {"path": "bpe.model", "sha256": "c53433de083c4a6ad12d034550ef22de68cec62c4f58932a7b6b8b2f1e743fa5", "size_bytes": 244865},
    {"path": "tokens.txt", "sha256": "49e3c2646595fd907228b3c6787069658f67b17377c60aeb8619c4551b2316fb", "size_bytes": 5048},
]
CLAIMS = {
    "b2r11_authorized": False,
    "b2r12_authorized": False,
    "comparative_performance_authorized": False,
    "comparative_result_available": False,
    "human_developer_speech_accuracy_evidence": "ABSENT",
    "product_code_authorized": False,
    "production_stt_selected": False,
}
READINESS_CLAIMS = {
    "human_developer_speech_accuracy_evidence": "ABSENT",
    "comparative_result_available": False,
    "production_stt_selected": False,
    "product_code_authorized": False,
}


class VerifyError(ValueError):
    """Raised when committed B2R10 evidence violates its frozen contract."""


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
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30).stdout.strip()


def verify_recovery_ledger(tasks: str, completed_through: int) -> None:
    entries = re.findall(r"^- \[([ x])\] `(B2R\d{2})`", tasks, re.MULTILINE)
    expected = [("x" if i <= completed_through else " ", f"B2R{i:02d}") for i in range(1, 13)]
    require(entries == expected, "recovery task ledger drift")


def verify_frontier() -> None:
    readiness = load(READINESS)
    tasks = TASKS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    canonical_current = CANONICAL_CURRENT.read_text(encoding="utf-8")
    require(readiness.get("state") == "RECOVERY_READY", "recovery lane not ready")
    require(readiness.get("qualified_workflow_change_paths") == [], "workflow drift authorized")
    require(readiness.get("claim_guards") == READINESS_CLAIMS, "readiness claim guards drift")
    replacement = readiness.get("replacement_attempt", {})
    require(replacement.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-002", "replacement attempt drift")
    require(replacement.get("frozen") is True, "replacement attempt is not frozen")
    completed = readiness.get("completed_recovery_tasks")
    active = readiness.get("active_recovery_unit")
    pre_prefix = [f"B2R{i:02d}" for i in range(1, 10)]
    post_prefix = [f"B2R{i:02d}" for i in range(1, 11)]
    proofs = readiness.get("transition_proofs")
    require(isinstance(proofs, list), "transition proof ledger missing")
    if completed == pre_prefix and active == "B2R10":
        require(replacement.get("primary_decode_entry_open") is True, "B2R10 primary entry closed before reconciliation")
        require(len(proofs) == 9 and proofs[-1].get("completed_task") == "B2R09" and proofs[-1].get("successor_task") == "B2R10", "B2R10 predecessor transition proof drift")
        verify_recovery_ledger(tasks, 9)
        require("**Active recovery unit:** `B2R10`" in current, "CURRENT does not own B2R10 frontier")
        require("**Active recovery unit:** `B2R10`" in canonical_current, "CURRENT_STATE does not own B2R10 frontier")
        next_action = str(readiness.get("next_action", ""))
        require(next_action.startswith("Qualify B2R10 only:"), "B2R10 next action drift")
        require("sherpa-onnx-balanced" in next_action and "Keep B2R11" in next_action, "B2R10/B2R11 authority boundary drift")
    else:
        require(completed == post_prefix and active == "B2R11", "unexpected post-B2R10 recovery frontier")
        require(replacement.get("primary_decode_entry_open") is False, "primary decode entry remains open after all six cells")
        require(len(proofs) == 10 and proofs[-1].get("completed_task") == "B2R10" and proofs[-1].get("successor_task") == "B2R11", "B2R10 transition proof drift")
        verify_recovery_ledger(tasks, 10)
        require("**Active recovery unit:** `B2R11`" in current, "CURRENT does not own B2R11 frontier")
        require("**Active recovery unit:** `B2R11`" in canonical_current, "CURRENT_STATE does not own B2R11 frontier")
        next_action = str(readiness.get("next_action", ""))
        require(next_action.startswith("Qualify B2R11 only:"), "B2R11 next action drift")
        require("preserv" in next_action.lower() and "B2R12" in next_action, "B2R11/B2R12 authority boundary drift")


def verify_static() -> None:
    require(sha256(ATTEMPT) == ATTEMPT_SHA256, "ATTEMPT-002 bytes drift")
    require(sha256(PREPROCESSING) == PREPROCESSING_SHA256, "preprocessing bytes drift")
    require(sha256(REBINDING) == REBINDING_SHA256, "B2R03 rebinding bytes drift")
    for source, label in ((TASK_SOURCE, "task"), (MATERIALIZED_SOURCE, "materialized"), (EXECUTION_SOURCE, "execution")):
        require(git("rev-parse", f"{source}^{{commit}}") == source, f"{label} source missing")
    rel = "research/000b2-public/decode_b2r10.py"
    require(git("hash-object", rel) == DECODER_BLOB, "mergeable decoder blob drift")
    require(git("rev-parse", f"{TASK_SOURCE}:{rel}") == DECODER_BLOB, "task-source decoder blob drift")
    require(git("rev-parse", f"{MATERIALIZED_SOURCE}:{rel}") == DECODER_BLOB, "materialized-source decoder blob drift")
    require(git("rev-parse", f"{EXECUTION_SOURCE}:{rel}") == DECODER_BLOB, "execution-source decoder blob drift")
    evidence_rel = "research/000b2-public/b2r10-sherpa-onnx-balanced.json"
    require(git("rev-parse", f"{MATERIALIZED_SOURCE}:{evidence_rel}") == EVIDENCE_BLOB, "materialized evidence blob drift")


def verify_evidence() -> None:
    require(EVIDENCE.stat().st_size == EVIDENCE_SIZE and sha256(EVIDENCE) == EVIDENCE_SHA256, "evidence bytes drift")
    evidence = load(EVIDENCE)
    unsigned = dict(evidence)
    payload = unsigned.pop("evidence_payload_sha256", None)
    require(payload == PAYLOAD_SHA256, "evidence payload identity drift")
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == PAYLOAD_SHA256, "evidence payload digest drift")
    require((evidence.get("schema_version"), evidence.get("task"), evidence.get("attempt_id"), evidence.get("state")) == ("000b2-public-b2r10-decode-v1", "B2R10", "000B2-PUBLIC-ATTEMPT-002", "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED"), "evidence identity drift")
    candidate = evidence.get("candidate", {})
    require((candidate.get("cell_index"), candidate.get("candidate_id"), candidate.get("family"), candidate.get("tier"), candidate.get("model")) == (6, "sherpa-onnx-balanced", "sherpa-onnx", "BALANCED", "FP32 ONNX"), "candidate identity drift")
    require(candidate.get("runtime_distribution") == "sherpa-onnx", "runtime distribution drift")
    require(candidate.get("runtime_distribution_version") == "1.13.7", "runtime distribution version drift")
    require(candidate.get("runtime_revision") == RUNTIME_REVISION, "runtime revision drift")
    require(candidate.get("model_onnx_revision") == MODEL_ONNX_REVISION, "model ONNX revision drift")
    require(candidate.get("model_aux_revision") == MODEL_AUX_REVISION, "model auxiliary revision drift")
    require(candidate.get("artifacts") == EXPECTED_ARTIFACTS, "candidate artifact identity drift")
    run = evidence.get("run", {})
    require(run.get("repository_revision") == EXECUTION_SOURCE, "execution repository revision drift")
    require(run.get("github_repository") == "TheHalfMoon/Wispral", "execution repository drift")
    require(run.get("github_ref") == "refs/heads/research/000b2-b2r10-execution", "execution ref drift")
    require(run.get("github_run_id") == RUN_ID and run.get("github_run_attempt") == 1 and run.get("github_job") == "capture-b2r10", "run identity drift")
    require(run.get("runner_os") == "Linux" and run.get("runner_arch") == "X64", "runner identity drift")
    require(run.get("timing_semantics") == "DIAGNOSTIC_ONLY" and run.get("comparative_performance_authorized") is False, "timing semantics drift")
    runtime = run.get("runtime_identity", {})
    require(runtime.get("distribution") == "sherpa-onnx" and runtime.get("version") == "1.13.7", "runtime package identity drift")
    require(runtime.get("source_revision") == RUNTIME_REVISION and runtime.get("source_tree") == RUNTIME_TREE, "runtime source identity drift")
    require(runtime.get("module_file") == "__init__.py" and runtime.get("module_file_sha256") == RUNTIME_MODULE_SHA256, "runtime module identity drift")
    require(evidence.get("c0_controls") == {
        "candidate_specific_audio_transform_used": False,
        "decoding_method": "greedy_search",
        "feature_dim": 80,
        "feed_chunk_ms": 500,
        "feed_chunk_samples": 8000,
        "final_zero_chunk_samples": [8000, 2560],
        "final_zero_pad_samples": 10560,
        "hotwords": [],
        "identical_frozen_audio_required_across_candidates": True,
        "language": "en",
        "language_model": None,
        "max_active_paths": 4,
        "provider": "cpu",
        "repository_context_used": False,
        "sample_rate_hz": 16000,
        "test_specific_context_used": False,
        "threads": 4,
    }, "C0 controls drift")
    execution = evidence.get("execution", {})
    require((execution.get("input_count"), execution.get("decoded_count"), execution.get("failure_count")) == (240, 240, 0), "execution accounting drift")
    require(execution.get("all_frozen_input_hashes_reverified") is True, "frozen input hashes were not reverified")
    require(execution.get("reference_transcripts_loaded_by_decoder") is False, "reference transcript boundary drift")
    require(execution.get("accuracy_scoring_performed") is False, "accuracy scoring opened during decode")
    require(execution.get("comparative_ranking_present") is False, "comparative ranking opened during decode")
    require(execution.get("performance_claim_present") is False, "performance claim opened during decode")
    records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240, "record count drift")
    ids = [row.get("utterance_id") for row in records]
    require(len(set(ids)) == 240 and all(isinstance(uid, str) and uid for uid in ids), "record identity coverage drift")
    preprocessing = load(PREPROCESSING).get("execution", {}).get("records", [])
    require(isinstance(preprocessing, list) and len(preprocessing) == 240, "preprocessing record count drift")
    preprocessing_index = {row["utterance_id"]: row for row in preprocessing}
    require(ids == [row["utterance_id"] for row in preprocessing], "frozen input order drift")
    for row in records:
        uid = row["utterance_id"]
        source = preprocessing_index[uid]
        require(row.get("source_partition") == source.get("source_partition"), f"source partition drift: {uid}")
        require(row.get("canonical_preprocessed_file_sha256") == source.get("canonical_preprocessed_file_sha256"), f"preprocessed digest drift: {uid}")
        require(row.get("status") == "DECODED" and row.get("failure") is None, f"decode status drift: {uid}")
        require(isinstance(row.get("raw_transcript"), str), f"raw transcript missing: {uid}")
        snapshots = row.get("raw_stream_snapshots")
        require(isinstance(snapshots, list) and all(isinstance(value, str) for value in snapshots), f"raw snapshot drift: {uid}")
        trace = row.get("feed_trace")
        require(isinstance(trace, dict), f"feed trace missing: {uid}")
        require(trace.get("sample_rate_hz") == 16000, f"sample rate drift: {uid}")
        require(trace.get("zero_suffix_chunk_samples") == [8000, 2560] and trace.get("zero_suffix_samples") == 10560, f"zero suffix drift: {uid}")
        require(trace.get("input_finished") is True, f"input-finished marker drift: {uid}")
        chunks = trace.get("speech_chunk_samples")
        require(isinstance(chunks, list) and chunks and all(isinstance(value, int) and 0 < value <= 8000 for value in chunks), f"speech chunk trace drift: {uid}")
        require(sum(chunks) == trace.get("speech_samples"), f"speech sample accounting drift: {uid}")
        require(isinstance(trace.get("decode_steps"), int) and trace.get("decode_steps") >= 0, f"decode-step trace drift: {uid}")
    require(evidence.get("claim_guards") == CLAIMS, "evidence claim guards drift")
    require(not (PUBLIC / "raw").exists(), "unexpected raw directory materialized")


def verify_provenance() -> None:
    require(PROVENANCE.stat().st_size == PROVENANCE_SIZE and sha256(PROVENANCE) == PROVENANCE_SHA256, "provenance bytes drift")
    provenance = load(PROVENANCE)
    unsigned = dict(provenance)
    payload = unsigned.pop("provenance_payload_sha256", None)
    require(payload == PROVENANCE_PAYLOAD_SHA256, "provenance payload identity drift")
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == payload, "provenance payload digest drift")
    require((provenance.get("schema_version"), provenance.get("task"), provenance.get("attempt_id"), provenance.get("candidate_id")) == ("000b2-public-b2r10-provenance-v1", "B2R10", "000B2-PUBLIC-ATTEMPT-002", "sherpa-onnx-balanced"), "provenance identity drift")
    source = provenance.get("canonical_evidence_source", {})
    require((source.get("workflow_id"), source.get("run_id"), source.get("job_id"), source.get("artifact_id")) == (WORKFLOW_ID, RUN_ID, JOB_ID, ARTIFACT_ID), "canonical source identity drift")
    require(source.get("workflow_name") == "Internal B2R10 ATTEMPT-002 Capture" and source.get("event") == "push", "canonical source name/event drift")
    require(source.get("source_branch") == "research/000b2-b2r10-execution" and source.get("source_revision") == EXECUTION_SOURCE, "canonical source revision drift")
    require(source.get("execution_decoder_blob_sha") == DECODER_BLOB and source.get("mergeable_decoder_blob_sha") == DECODER_BLOB, "decoder provenance drift")
    require(source.get("artifact_name") == f"b2r10-sherpa-onnx-balanced-{EXECUTION_SOURCE}", "artifact name drift")
    require(source.get("artifact_zip_sha256") == ARTIFACT_ZIP_SHA256 and source.get("artifact_zip_size_bytes") == ARTIFACT_ZIP_SIZE, "artifact ZIP provenance drift")
    require(source.get("evidence_raw_file_sha256") == EVIDENCE_SHA256 and source.get("evidence_raw_file_size_bytes") == EVIDENCE_SIZE, "evidence file provenance drift")
    require(source.get("evidence_payload_sha256") == PAYLOAD_SHA256 and source.get("conclusion") == "success", "evidence payload provenance drift")
    require(source.get("selection_basis") == "FIRST_B2R10_PRIMARY_EXECUTION_THAT_PASSED_CURRENT_B2R10_AUTHORITY_FROZEN_INPUT_DECODE_SEMANTICS_AND_ARTIFACT_GATES; NOT_RESULT_DRIVEN", "canonical evidence selection basis drift")
    require(source.get("run_attempt") == 1, "canonical run attempt drift")
    require(provenance.get("related_pre_primary_runs") == [], "unexpected pre-primary chronology")
    require(provenance.get("result_accounting") == {
        "input_count": 240,
        "decoded_count": 240,
        "failure_count": 0,
        "all_frozen_input_hashes_reverified": True,
        "reference_transcripts_loaded_by_decoder": False,
        "accuracy_scoring_performed": False,
        "comparative_ranking_present": False,
        "performance_claim_present": False,
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "result_driven_evidence_selection": False,
    }, "provenance accounting drift")
    require(provenance.get("claims") == CLAIMS, "provenance claim guards drift")
    require(provenance.get("runtime_identity") == {
        "distribution": "sherpa-onnx",
        "module_file": "__init__.py",
        "module_file_sha256": RUNTIME_MODULE_SHA256,
        "source_revision": RUNTIME_REVISION,
        "source_tree": RUNTIME_TREE,
        "version": "1.13.7",
    }, "provenance runtime identity drift")
    materialization = provenance.get("task_materialization", {})
    require((materialization.get("workflow_id"), materialization.get("run_id"), materialization.get("job_id")) == (MATERIALIZATION_WORKFLOW_ID, MATERIALIZATION_RUN_ID, MATERIALIZATION_JOB_ID), "materialization run identity drift")
    require(materialization.get("source_branch") == "ci/000b2-b2r10-task-materialize" and materialization.get("source_revision") == MATERIALIZATION_SOURCE, "materialization source drift")
    require(materialization.get("input_task_revision") == TASK_SOURCE and materialization.get("output_task_revision") == MATERIALIZED_SOURCE, "materialization ancestry drift")
    require(materialization.get("evidence_blob_sha") == EVIDENCE_BLOB, "materialized evidence blob drift")
    require(materialization.get("scope") == ["research/000b2-public/decode_b2r10.py", "research/000b2-public/b2r10-sherpa-onnx-balanced.json"], "materialization scope drift")
    require(materialization.get("candidate_result_accessed_for_integrity_validation") is True, "materialization integrity validation missing")
    require(materialization.get("result_access_effect") == "NONE" and materialization.get("selection_effect") == "NONE", "materialization result-access boundary drift")


def main() -> int:
    verify_frontier()
    verify_static()
    verify_evidence()
    verify_provenance()
    print("B2R10_EVIDENCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
