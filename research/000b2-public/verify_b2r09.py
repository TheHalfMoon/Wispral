#!/usr/bin/env python3
"""Verify sealed B2R09 ATTEMPT-002 sherpa-onnx-compact execution evidence."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
EVIDENCE = PUBLIC / "b2r09-sherpa-onnx-compact.json"
PROVENANCE = PUBLIC / "b2r09-provenance.json"
ATTEMPT = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
REBINDING = PUBLIC / "b2r03-preexecution-rebinding.json"
READINESS = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CANONICAL_CURRENT = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
DECODER = PUBLIC / "decode_b2r09.py"

TASK_SOURCE = "b7a4bb8828a4b861a399b1424bc07a4e549cf51f"
EXECUTION_SOURCE = "47d1c53f6892dda437aa0f1d109f58f1cc5e101e"
DECODER_BLOB = "27052cc7f3d57d2743ee06a7db8de730c833935e"
RUN_ID = 34156167567
JOB_ID = 101848322734
WORKFLOW_ID = 352553362
ARTIFACT_ID = 10031177463
ARTIFACT_ZIP_SHA256 = "79652728032760ae133845b7f1308623a984ee69c490991cf190d8a7301985ea"
EVIDENCE_SIZE = 248426
EVIDENCE_SHA256 = "d59fa9605e8b0cf6892cd5a7ece105c6abe0753ff8949e9206e35f42da9a003f"
PAYLOAD_SHA256 = "4a81f1be21e18aa462ee9ec9c32a1daeaa6fa86bcca6372b0634a9421c16c1ed"
PROVENANCE_SHA256 = "91a6a527718efd835e387e48aa5314adf20441dd48696b505f62d911758c50fd"
ATTEMPT_SHA256 = "a2dc8246e4567e670beb3f26e315be93e001e4d9a9037be57ff11fce5a340134"
PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
RUNTIME_REVISION = "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e"
RUNTIME_TREE = "fd2c4e97c9f7499b6ed91c7c2854b4211f61bdc0"
MODEL_ONNX_REVISION = "6037ea07e3abfe599ad00d418968bcf9656e7472"
MODEL_AUX_REVISION = "672fbf1b30579d6585301139bb363f42a0ad4a24"
RUNTIME_MODULE_SHA256 = "9f1d820f337a09099a77e321d6ccddd0ea76b24ebaf815fb9a315cbb0a08b1f3"
EXPECTED_ARTIFACTS = [
    {
        "path": "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
        "sha256": "563fde436d16cf7607cf408cd6b30909819d03162652ef389c2450ced3f45ac1",
        "size_bytes": 71083163,
    },
    {
        "path": "decoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
        "sha256": "98da299f471e38bb4e1a8df579b8cc9122d6039576a77e357b3c60f17dd83b02",
        "size_bytes": 1307236,
    },
    {
        "path": "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
        "sha256": "d944208d660d67c8d72cd2acaeac971fa5ceb8c80e76c1968148846fedd6e297",
        "size_bytes": 259335,
    },
    {
        "path": "bpe.model",
        "sha256": "c53433de083c4a6ad12d034550ef22de68cec62c4f58932a7b6b8b2f1e743fa5",
        "size_bytes": 244865,
    },
    {
        "path": "tokens.txt",
        "sha256": "49e3c2646595fd907228b3c6787069658f67b17377c60aeb8619c4551b2316fb",
        "size_bytes": 5048,
    },
]
CLAIMS = {
    "b2r10_authorized": False,
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
    """Raised when committed B2R09 evidence violates its frozen contract."""


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
        timeout=30,
    ).stdout.strip()


def verify_recovery_ledger(tasks: str, completed_through: int) -> None:
    entries = re.findall(r"^- \[([ x])\] `(B2R\d{2})`", tasks, re.MULTILINE)
    expected = [
        ("x" if index <= completed_through else " ", f"B2R{index:02d}")
        for index in range(1, 13)
    ]
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
    pre_prefix = [f"B2R{i:02d}" for i in range(1, 9)]
    post_prefix = [f"B2R{i:02d}" for i in range(1, 10)]
    if completed == pre_prefix and active == "B2R09":
        require(replacement.get("primary_decode_entry_open") is True, "B2R09 primary entry closed before reconciliation")
        verify_recovery_ledger(tasks, 8)
        require("**Active recovery unit:** `B2R09`" in current, "CURRENT does not own B2R09 frontier")
        require("**Active recovery unit:** `B2R09`" in canonical_current, "CURRENT_STATE does not own B2R09 frontier")
        next_action = str(readiness.get("next_action", ""))
        require(next_action.startswith("Qualify B2R09 only:"), "B2R09 next action drift")
        require("sherpa-onnx-compact" in next_action and "Keep B2R10" in next_action, "B2R09/B2R10 authority boundary drift")
    else:
        require(completed == post_prefix and active == "B2R10", "unexpected post-B2R09 recovery frontier")
        require(replacement.get("primary_decode_entry_open") is True, "B2R10 primary entry closed after reconciliation")
        verify_recovery_ledger(tasks, 9)
        require("**Active recovery unit:** `B2R10`" in current, "CURRENT does not own B2R10 frontier")
        require("**Active recovery unit:** `B2R10`" in canonical_current, "CURRENT_STATE does not own B2R10 frontier")
        next_action = str(readiness.get("next_action", ""))
        require(next_action.startswith("Qualify B2R10 only:"), "B2R10 next action drift")
        require("sherpa-onnx-balanced" in next_action and "Keep B2R11" in next_action, "B2R10/B2R11 authority boundary drift")


def verify_static() -> None:
    require(sha256(ATTEMPT) == ATTEMPT_SHA256, "ATTEMPT-002 bytes drift")
    require(sha256(PREPROCESSING) == PREPROCESSING_SHA256, "preprocessing bytes drift")
    require(sha256(REBINDING) == REBINDING_SHA256, "B2R03 rebinding bytes drift")
    require(git("rev-parse", f"{TASK_SOURCE}^{{commit}}") == TASK_SOURCE, "task source missing")
    require(git("rev-parse", f"{EXECUTION_SOURCE}^{{commit}}") == EXECUTION_SOURCE, "execution source missing")
    require(git("hash-object", str(DECODER.relative_to(ROOT))) == DECODER_BLOB, "mergeable decoder blob drift")
    require(git("rev-parse", f"{TASK_SOURCE}:research/000b2-public/decode_b2r09.py") == DECODER_BLOB, "task-source decoder blob drift")
    require(git("rev-parse", f"{EXECUTION_SOURCE}:research/000b2-public/decode_b2r09.py") == DECODER_BLOB, "execution-source decoder blob drift")


def verify_evidence() -> None:
    require(EVIDENCE.stat().st_size == EVIDENCE_SIZE and sha256(EVIDENCE) == EVIDENCE_SHA256, "evidence bytes drift")
    evidence = load(EVIDENCE)
    unsigned = dict(evidence)
    payload = unsigned.pop("evidence_payload_sha256", None)
    require(payload == PAYLOAD_SHA256, "evidence payload identity drift")
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == PAYLOAD_SHA256, "evidence payload digest drift")
    require(
        (evidence.get("schema_version"), evidence.get("task"), evidence.get("attempt_id"), evidence.get("state"))
        == ("000b2-public-b2r09-decode-v1", "B2R09", "000B2-PUBLIC-ATTEMPT-002", "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED"),
        "evidence identity drift",
    )

    candidate = evidence.get("candidate", {})
    require(
        (candidate.get("cell_index"), candidate.get("candidate_id"), candidate.get("family"), candidate.get("tier"), candidate.get("model"))
        == (5, "sherpa-onnx-compact", "sherpa-onnx", "COMPACT", "INT8 ONNX"),
        "candidate identity drift",
    )
    require(candidate.get("runtime_distribution") == "sherpa-onnx", "runtime distribution drift")
    require(candidate.get("runtime_distribution_version") == "1.13.7", "runtime distribution version drift")
    require(candidate.get("runtime_revision") == RUNTIME_REVISION, "runtime revision drift")
    require(candidate.get("model_onnx_revision") == MODEL_ONNX_REVISION, "model ONNX revision drift")
    require(candidate.get("model_aux_revision") == MODEL_AUX_REVISION, "model auxiliary revision drift")
    require(candidate.get("artifacts") == EXPECTED_ARTIFACTS, "candidate artifact identity drift")

    run = evidence.get("run", {})
    require(run.get("repository_revision") == EXECUTION_SOURCE, "execution repository revision drift")
    require(run.get("github_repository") == "TheHalfMoon/Wispral", "execution repository drift")
    require(run.get("github_ref") == "refs/heads/research/000b2-b2r09-execution", "execution ref drift")
    require(run.get("github_run_id") == RUN_ID and run.get("github_run_attempt") == 1 and run.get("github_job") == "capture-b2r09", "run identity drift")
    require(run.get("runner_os") == "Linux" and run.get("runner_arch") == "X64", "runner identity drift")
    require(run.get("timing_semantics") == "DIAGNOSTIC_ONLY" and run.get("comparative_performance_authorized") is False, "timing semantics drift")
    runtime = run.get("runtime_identity", {})
    require(runtime.get("distribution") == "sherpa-onnx" and runtime.get("version") == "1.13.7", "runtime package identity drift")
    require(runtime.get("source_revision") == RUNTIME_REVISION and runtime.get("source_tree") == RUNTIME_TREE, "runtime source identity drift")
    require(runtime.get("module_file") == "__init__.py" and runtime.get("module_file_sha256") == RUNTIME_MODULE_SHA256, "runtime module identity drift")

    controls = evidence.get("c0_controls", {})
    require(
        controls
        == {
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
        },
        "C0 controls drift",
    )

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
    require(PROVENANCE.stat().st_size == 5074 and sha256(PROVENANCE) == PROVENANCE_SHA256, "provenance bytes drift")
    provenance = load(PROVENANCE)
    unsigned = dict(provenance)
    payload = unsigned.pop("provenance_payload_sha256", None)
    require(payload == "22c7e7ba9dc290ca8ae3f07da5331ef27cbe1bf9f80facd58c541e4ef774a16d", "provenance payload identity drift")
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == payload, "provenance payload digest drift")
    require((provenance.get("task"), provenance.get("attempt_id"), provenance.get("candidate_id")) == ("B2R09", "000B2-PUBLIC-ATTEMPT-002", "sherpa-onnx-compact"), "provenance identity drift")

    source = provenance.get("canonical_evidence_source", {})
    require((source.get("workflow_id"), source.get("run_id"), source.get("job_id"), source.get("artifact_id")) == (WORKFLOW_ID, RUN_ID, JOB_ID, ARTIFACT_ID), "canonical source identity drift")
    require(source.get("workflow_name") == "Internal B2R09 ATTEMPT-002 Capture" and source.get("event") == "push", "canonical source name/event drift")
    require(source.get("source_branch") == "research/000b2-b2r09-execution" and source.get("source_revision") == EXECUTION_SOURCE, "canonical source revision drift")
    require(source.get("execution_decoder_blob_sha") == DECODER_BLOB and source.get("mergeable_decoder_blob_sha") == DECODER_BLOB, "decoder provenance drift")
    require(source.get("artifact_name") == "b2r09-sherpa-onnx-compact-47d1c53f6892dda437aa0f1d109f58f1cc5e101e", "artifact name drift")
    require(source.get("artifact_zip_sha256") == ARTIFACT_ZIP_SHA256 and source.get("artifact_zip_size_bytes") == 19519, "artifact ZIP provenance drift")
    require(source.get("evidence_raw_file_sha256") == EVIDENCE_SHA256 and source.get("evidence_raw_file_size_bytes") == EVIDENCE_SIZE, "evidence file provenance drift")
    require(source.get("evidence_payload_sha256") == PAYLOAD_SHA256 and source.get("conclusion") == "success", "evidence payload provenance drift")
    require(str(source.get("selection_basis", "")).endswith("NOT_RESULT_DRIVEN"), "canonical evidence selection basis drift")

    attempts = provenance.get("related_pre_primary_runs")
    require(isinstance(attempts, list) and len(attempts) == 1, "pre-primary chronology drift")
    failed = attempts[0]
    require((failed.get("workflow_id"), failed.get("run_id"), failed.get("job_id"), failed.get("source_revision")) == (WORKFLOW_ID, 34155967652, 101847745228, "f45e9884e3fbcdc84dd27393b8ffde7d12df65e5"), "failed pre-primary identity drift")
    require(failed.get("conclusion") == "failure" and failed.get("failure_stage") == "SETUP_PYTHON_CACHE_DEPENDENCY_FILE_DISCOVERY", "failed pre-primary stage drift")
    require(failed.get("authority_validation_succeeded") is True, "failed pre-primary authority gate drift")
    for key in ("runtime_install_started", "preprocessing_container_pull_started", "preprocessing_started", "runtime_source_fetch_started", "model_download_started", "primary_decode_started", "candidate_result_accessed"):
        require(failed.get(key) is False, f"failed pre-primary exposure drift: {key}")
    require(failed.get("artifact_count") == 0 and failed.get("selection_effect") == "NONE", "failed pre-primary artifact/selection drift")
    repair = failed.get("repair", {})
    require(repair.get("policy") == "FORWARD_ONLY_REMOVE_SETUP_PYTHON_PIP_CACHE_CONFIGURATION", "repair policy drift")
    for key in ("c0_controls_changed", "candidate_changed", "frozen_audio_changed", "model_changed", "normalization_changed", "runtime_revision_changed", "scorer_changed"):
        require(repair.get(key) is False, f"repair semantic drift: {key}")

    require(
        provenance.get("result_accounting")
        == {
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
        },
        "provenance accounting drift",
    )
    require(provenance.get("claims") == CLAIMS, "provenance claim guards drift")
    require(
        provenance.get("runtime_identity")
        == {
            "distribution": "sherpa-onnx",
            "module_file": "__init__.py",
            "module_file_sha256": RUNTIME_MODULE_SHA256,
            "source_revision": RUNTIME_REVISION,
            "source_tree": RUNTIME_TREE,
            "version": "1.13.7",
        },
        "provenance runtime identity drift",
    )
    materialization = provenance.get("task_materialization", {})
    require((materialization.get("workflow_id"), materialization.get("run_id"), materialization.get("job_id")) == (352563253, 34157501089, 101852259514), "materialization run identity drift")
    require(materialization.get("source_branch") == "ci/000b2-b2r09-task-materialize" and materialization.get("source_revision") == "8a1827018438b9ed50b9760bf38bf65c71da8976", "materialization source drift")
    require(materialization.get("input_task_revision") == TASK_SOURCE and materialization.get("output_task_revision") == "52f5ca98c85402af47007983590c5dea4ec19b8f", "materialization ancestry drift")
    require(materialization.get("evidence_blob_sha") == "ee57923e649bee4dc8910f473c8e55ec80eeb790", "materialized evidence blob drift")
    require(materialization.get("scope") == ["research/000b2-public/decode_b2r09.py", "research/000b2-public/b2r09-sherpa-onnx-compact.json"], "materialization scope drift")
    require(materialization.get("candidate_result_accessed_for_integrity_validation") is True and materialization.get("result_access_effect") == "NONE" and materialization.get("selection_effect") == "NONE", "materialization result-access boundary drift")


def main() -> int:
    verify_frontier()
    verify_static()
    verify_evidence()
    verify_provenance()
    print("B2R09_EVIDENCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
