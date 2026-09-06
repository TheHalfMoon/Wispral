#!/usr/bin/env python3
"""Verify sealed B2R07 ATTEMPT-002 whispercpp-compact execution evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
EVIDENCE = PUBLIC / "b2r07-whispercpp-compact.json"
PROVENANCE = PUBLIC / "b2r07-provenance.json"
ATTEMPT = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
REBINDING = PUBLIC / "b2r03-preexecution-rebinding.json"
READINESS = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CANONICAL_CURRENT = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"

SOURCE_REVISION = "42434a018a1feeb599db0c64ecb836d0e4e6b909"
RUN_ID = 34058440043
JOB_ID = 101554521526
WORKFLOW_ID = 351743293
ARTIFACT_ID = 9998344092
EVIDENCE_SHA256 = "80b9a21377bfd5a52f19b6f54cb1c8b933cb095c8daa3bb94081841f935dd73a"
EVIDENCE_SIZE = 393777
PAYLOAD_SHA256 = "53a4b3597483e04ec140b7ccbe3bd4352c291fcd470480159a995a6b9ca5b5fd"
PROVENANCE_SHA256 = "d331eb014316f1a3ecaa5d5a82278b39226d29381de37081b49833c80765fb22"
ATTEMPT_SHA256 = "a2dc8246e4567e670beb3f26e315be93e001e4d9a9037be57ff11fce5a340134"
PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
BUILD_IDENTITY_SHA256 = "4888182a73a921fa574a2a4f1cf6862779687c0918d0b724622a01a69e30ff82"
FAILED_PRIMARY_ZIP_SHA256 = "a31432029720f93567d5da616e92b068ca0661ddff6ab0db3dd8b97edbf183b2"
BLOBS = {
    "research/000b2-public/decode_b2r07.py": "09f89a77c2339177b45ef09758f2387e44c650af",
    "research/000b2-public/run_b2r07_timeout_repair.py": "4af80f636b1587dea8ebf3b165a08cf15a9ad7ee",
    "research/000b2-public/whispercpp-adapter/CMakeLists.txt": "e975e7d4afd0f580881b17a7e9c2856634ec61e7",
    "research/000b2-public/whispercpp-adapter/adapter.cpp": "e7405cd343532b7d9dff8b667bfc7591f50631d9",
}
CLAIMS = {
    "b2r08_authorized": False,
    "comparative_performance_authorized": False,
    "comparative_result_available": False,
    "human_developer_speech_accuracy_evidence": "ABSENT",
    "product_code_authorized": False,
    "production_stt_selected": False,
}
C0 = {
    "audio_ctx": 0,
    "beam_size": -1,
    "candidate_specific_audio_transform_used": False,
    "final_speech_chunk_preserved": True,
    "finalization_zero_pad_samples": 10560,
    "flash_attention": False,
    "identical_frozen_audio_required_across_candidates": True,
    "initial_prompt": None,
    "keep_context": False,
    "keep_ms": 200,
    "language": "en",
    "length_ms": 5000,
    "max_tokens": 0,
    "prompt_carryover": False,
    "raw_transcript_materialization": "STREAM_CPP_COMMIT_EVERY_9_PLUS_FINAL_PENDING",
    "regular_chunk_samples": 8000,
    "repository_context_used": False,
    "sampling": "GREEDY",
    "single_segment": True,
    "step_ms": 500,
    "temperature_fallback": "OFF",
    "test_specific_context_used": False,
    "threads": 4,
    "timestamps": False,
    "translate": False,
    "use_gpu": False,
    "vad": False,
    "zero_suffix_chunk_samples": [8000, 2560],
}
ORCHESTRATION = {
    "adapter_invocation_count_changed": False,
    "adapter_process_partitioning_changed": False,
    "c0_controls_changed": False,
    "candidate_order_changed": False,
    "failed_primary_artifact_contents": ["whisper-build/wispral-build-identity.json"],
    "failed_primary_artifact_id": 9996564565,
    "failed_primary_artifact_zip_sha256": FAILED_PRIMARY_ZIP_SHA256,
    "failed_primary_build_identity_sha256": BUILD_IDENTITY_SHA256,
    "failed_primary_evidence_json_present": False,
    "failed_primary_job_id": 101540334687,
    "failed_primary_run_id": 34053187435,
    "failed_primary_transcript_artifact_present": False,
    "frozen_input_order_changed": False,
    "original_adapter_timeout_seconds": 5400,
    "policy": "FORWARD_ONLY_WALL_CLOCK_BUDGET_REPAIR",
    "repair_basis": "FIRST_B2R07_PRIMARY_EXECUTION_TIMED_OUT_WITHOUT_TRANSCRIPT_OR_EVIDENCE_ARTIFACT",
    "repaired_adapter_timeout_seconds": 10800,
    "result_inspection_before_repair": False,
    "timeout_semantics": "EXECUTION_WALL_CLOCK_GUARD_ONLY_NOT_A_C0_OR_SCORING_PARAMETER",
}

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

def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()

def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

def verify_frontier() -> None:
    readiness = load(READINESS)
    tasks = TASKS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    canonical_current = CANONICAL_CURRENT.read_text(encoding="utf-8")
    require(readiness.get("state") == "RECOVERY_READY", "recovery lane not ready")
    require(readiness.get("qualified_workflow_change_paths") == [], "workflow drift authorized")
    require(readiness.get("claim_guards", {}).get("comparative_result_available") is False, "comparative result open")
    completed = readiness.get("completed_recovery_tasks")
    active = readiness.get("active_recovery_unit")
    prefix = ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05", "B2R06"]
    if completed == prefix and active == "B2R07":
        require("- [ ] `B2R07`" in tasks and "- [ ] `B2R08`" in tasks, "pre-reconciliation ledger drift")
        require("active recovery unit `B2R07`" in current and "**Active recovery unit:** `B2R07`" in canonical_current,
                "B2R07 frontier drift")
    else:
        require(isinstance(completed, list) and "B2R07" in completed, "B2R07 completion lost")
        require("- [x] `B2R07`" in tasks, "B2R07 ledger completion lost")
        require(active != "B2R07", "B2R07 remained active after completion")

def verify_static() -> None:
    require(sha256(ATTEMPT) == ATTEMPT_SHA256, "ATTEMPT-002 bytes drift")
    require(sha256(PREPROCESSING) == PREPROCESSING_SHA256, "preprocessing bytes drift")
    require(sha256(REBINDING) == REBINDING_SHA256, "rebinding bytes drift")
    require(git("rev-parse", f"{SOURCE_REVISION}^{{commit}}") == SOURCE_REVISION, "capture source missing")
    for path, blob in BLOBS.items():
        require(git("hash-object", path) == blob, f"mergeable blob drift: {path}")
        require(git("rev-parse", f"{SOURCE_REVISION}:{path}") == blob, f"capture blob drift: {path}")

def verify_provenance() -> None:
    require(sha256(PROVENANCE) == PROVENANCE_SHA256, "provenance bytes drift")
    p = load(PROVENANCE)
    require((p.get("task"), p.get("attempt_id"), p.get("candidate_id")) ==
            ("B2R07", "000B2-PUBLIC-ATTEMPT-002", "whispercpp-compact"), "provenance identity drift")
    src = p.get("canonical_evidence_source", {})
    require((src.get("workflow_id"), src.get("run_id"), src.get("job_id"), src.get("artifact_id")) ==
            (WORKFLOW_ID, RUN_ID, JOB_ID, ARTIFACT_ID), "canonical source identity drift")
    require(src.get("source_revision") == SOURCE_REVISION and src.get("conclusion") == "success", "source revision drift")
    require(src.get("evidence_raw_file_sha256") == EVIDENCE_SHA256 and
            src.get("evidence_raw_file_size_bytes") == EVIDENCE_SIZE and
            src.get("evidence_payload_sha256") == PAYLOAD_SHA256, "evidence provenance drift")
    require(src.get("selection_basis", "").endswith("NOT_RESULT_DRIVEN"), "selection basis drift")
    pre = p.get("related_pre_primary_runs")
    require(isinstance(pre, list) and [r.get("run_id") for r in pre] ==
            [34052577612, 34052689209, 34052909122, 34052985819], "pre-primary chronology drift")
    require(all(r.get("primary_decode_started") is False and r.get("artifact_count") == 0 and
                r.get("selection_effect") == "NONE" for r in pre), "pre-primary selection drift")
    failed = p.get("related_failed_primary_runs")
    require(isinstance(failed, list) and len(failed) == 1, "failed-primary chronology drift")
    f = failed[0]
    require((f.get("run_id"), f.get("job_id"), f.get("artifact_id")) ==
            (34053187435, 101540334687, 9996564565), "failed-primary identity drift")
    require(f.get("artifact_zip_sha256") == FAILED_PRIMARY_ZIP_SHA256 and
            f.get("artifact_contents") == ["whisper-build/wispral-build-identity.json"] and
            f.get("transcript_artifact_present") is False and f.get("evidence_json_present") is False and
            f.get("result_inspection_before_repair") is False and f.get("selection_effect") == "NONE",
            "failed-primary exposure drift")
    require(f.get("repair") == {
        "adapter_invocation_count_changed": False,
        "adapter_process_partitioning_changed": False,
        "c0_controls_changed": False,
        "candidate_order_changed": False,
        "frozen_input_order_changed": False,
        "original_adapter_timeout_seconds": 5400,
        "policy": "FORWARD_ONLY_WALL_CLOCK_BUDGET_REPAIR",
        "repaired_adapter_timeout_seconds": 10800,
    }, "timeout repair provenance drift")
    require(p.get("result_accounting", {}).get("decoded_count") == 240 and
            p.get("result_accounting", {}).get("failure_count") == 0 and
            p.get("result_accounting", {}).get("result_driven_evidence_selection") is False,
            "provenance accounting drift")
    require(p.get("claims") == CLAIMS, "provenance claims drift")

def verify_evidence() -> None:
    require(EVIDENCE.stat().st_size == EVIDENCE_SIZE and sha256(EVIDENCE) == EVIDENCE_SHA256,
            "evidence bytes drift")
    e = load(EVIDENCE)
    unsigned = dict(e)
    payload = unsigned.pop("evidence_payload_sha256", None)
    require(payload == PAYLOAD_SHA256 and hashlib.sha256(canonical(unsigned)).hexdigest() == PAYLOAD_SHA256,
            "payload digest drift")
    require((e.get("task"), e.get("attempt_id"), e.get("state")) ==
            ("B2R07", "000B2-PUBLIC-ATTEMPT-002", "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED"),
            "evidence identity drift")
    candidate = e.get("candidate", {})
    require((candidate.get("cell_index"), candidate.get("candidate_id"), candidate.get("tier")) ==
            (3, "whispercpp-compact", "COMPACT"), "candidate drift")
    require(candidate.get("runtime_revision") == "371b5a7561823ab2bb32142d2751e35e7534727b" and
            candidate.get("runtime_source_tree") == "3d7ce4f956997cfa325c7556533aba5604278463" and
            candidate.get("model_source_revision") == "80da2d8bfee42b0e836fc3a9890373e5defc00a6" and
            candidate.get("model") == "ggml-base.en.bin", "runtime/model drift")
    build = candidate.get("adapter_build_identity")
    require(isinstance(build, dict) and len(pretty(build)) == 1091 and
            hashlib.sha256(pretty(build)).hexdigest() == BUILD_IDENTITY_SHA256, "build identity drift")
    require(e.get("c0_controls") == C0, "C0 controls drift")
    require(e.get("execution_orchestration") == ORCHESTRATION, "orchestration drift")
    run = e.get("run", {})
    require(run.get("repository_revision") == SOURCE_REVISION and run.get("github_run_id") == RUN_ID and
            run.get("github_run_attempt") == 1 and run.get("github_job") == "capture-b2r07" and
            run.get("github_repository") == "TheHalfMoon/Wispral" and
            run.get("timing_semantics") == "DIAGNOSTIC_ONLY" and
            run.get("comparative_performance_authorized") is False, "run identity drift")
    x = e.get("execution", {})
    records = x.get("records")
    require((x.get("input_count"), x.get("decoded_count"), x.get("failure_count")) == (240, 240, 0),
            "execution accounting drift")
    require(x.get("all_frozen_input_hashes_reverified") is True and
            x.get("all_speech_samples_delivered_for_decoded_records") is True and
            x.get("all_zero_suffix_samples_delivered_for_decoded_records") is True and
            x.get("reference_transcripts_loaded_by_decoder") is False and
            x.get("accuracy_scoring_performed") is False and
            x.get("comparative_ranking_present") is False and x.get("performance_claim_present") is False,
            "execution guard drift")
    require(isinstance(records, list) and len(records) == 240, "record coverage drift")
    ids = [r.get("utterance_id") for r in records]
    require(ids == sorted(ids) and len(set(ids)) == 240, "record order/uniqueness drift")
    require(all(r.get("status") == "DECODED" and r.get("failure") is None and
                r.get("speech_samples_delivered") == r.get("speech_sample_count") and
                r.get("zero_suffix_samples_delivered") == 10560 and
                r.get("zero_suffix_chunks_delivered") == 2 for r in records), "record feed/status drift")
    require(e.get("claim_guards") == CLAIMS, "evidence claims drift")

def main() -> int:
    verify_frontier()
    verify_static()
    verify_provenance()
    verify_evidence()
    print("B2R07_EVIDENCE=PASS")
    print(f"B2R07_SOURCE_REVISION={SOURCE_REVISION}")
    print(f"B2R07_CAPTURE_RUN_ID={RUN_ID}")
    print("B2R07_INPUTS=240")
    print("B2R07_DECODED=240")
    print("B2R07_FAILURES=0")
    print("B2R08_AUTHORIZED=NO")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
