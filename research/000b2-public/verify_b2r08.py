#!/usr/bin/env python3
"""Verify sealed B2R08 ATTEMPT-002 whispercpp-balanced sharded execution evidence."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
EVIDENCE = PUBLIC / "b2r08-whispercpp-balanced.json"
QUALIFICATION = PUBLIC / "b2r08-shard-equivalence.json"
PROVENANCE = PUBLIC / "b2r08-provenance.json"
ATTEMPT = PUBLIC / "attempt-002-manifest.json"
PREPROCESSING = PUBLIC / "preprocessing-capture.json"
REBINDING = PUBLIC / "b2r03-preexecution-rebinding.json"
READINESS = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CANONICAL_CURRENT = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
EVIDENCE_SHA256 = "5b438a0d23c8ec19796df9b384234437a266ef862bd6ddd604772ed965932b41"
EVIDENCE_SIZE = 397706
PAYLOAD_SHA256 = "b688080a9b54106975fc3d423d210f6b449c47468cdc94135997285d9504314c"
QUALIFICATION_SHA256 = "122e217b7efcfadea44540fcd20a181ad881351a89b6303e0a283fdc569d96a1"
QUALIFICATION_SIZE = 5146
QUALIFICATION_PAYLOAD_SHA256 = "6d419e5a975c245132b2edca9f40c35bb0abd22c708896ba51b481e815409afd"
PROVENANCE_SHA256 = "9cac7769794dafcade8c5413d6971625cba3f90edd8939e68bf19bae544326b6"
ATTEMPT_SHA256 = "a2dc8246e4567e670beb3f26e315be93e001e4d9a9037be57ff11fce5a340134"
PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
PRIMARY_SOURCE = "4a6c776b2a666113420263b70a4fad06f752b99a"
PRIMARY_RUN_ID = 34139091127
QUALIFICATION_SOURCE = "900482d4cce3c69c8ad0a36261e2a8d53f106142"
QUALIFICATION_RUN_ID = 34137057908
SEAL_SOURCE = "70d9e71961510f2124c02ee4a05fb13b82399d03"
SEAL_RUN_ID = 34150046063
CLAIMS = {
    "b2r09_authorized": False,
    "comparative_performance_authorized": False,
    "comparative_result_available": False,
    "human_developer_speech_accuracy_evidence": "ABSENT",
    "product_code_authorized": False,
    "production_stt_selected": False,
}
BLOBS = {
    "research/000b2-public/decode_b2r08.py": "ac5a16469309f8ab3ad854b9df616f22f2903c33",
    "research/000b2-public/b2r08-repair-plan.json": "ff79ed2e15ac95e58c0f2b66b84f9a879b17ebdd",
    "research/000b2-public/run_b2r08_sharded_repair.py": "7f656bc352be4195b968d0e57f2d1725f033d0f1",
    "research/000b2-public/decode_b2r07.py": "09f89a77c2339177b45ef09758f2387e44c650af",
    "research/000b2-public/whispercpp-adapter/CMakeLists.txt": "e975e7d4afd0f580881b17a7e9c2856634ec61e7",
    "research/000b2-public/whispercpp-adapter/adapter.cpp": "e7405cd343532b7d9dff8b667bfc7591f50631d9",
}

class VerifyError(ValueError): pass
def require(ok: bool, message: str) -> None:
    if not ok: raise VerifyError(message)
def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8")); require(isinstance(value, dict), f"object expected: {path}"); return value
def sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value: Any) -> bytes: return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

def verify_frontier() -> None:
    readiness = load(READINESS); tasks = TASKS.read_text(); current = CURRENT.read_text(); canonical_current = CANONICAL_CURRENT.read_text()
    require(readiness.get("state") == "RECOVERY_READY", "recovery lane not ready")
    require(readiness.get("qualified_workflow_change_paths") == [], "workflow drift authorized")
    require(readiness.get("claim_guards", {}).get("comparative_result_available") is False, "comparative result open")
    completed = readiness.get("completed_recovery_tasks"); active = readiness.get("active_recovery_unit")
    prefix = ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05", "B2R06", "B2R07"]
    if completed == prefix and active == "B2R08":
        require("- [ ] `B2R08`" in tasks and "- [ ] `B2R09`" in tasks, "pre-reconciliation ledger drift")
        require("active recovery unit `B2R08`" in current and "**Active recovery unit:** `B2R08`" in canonical_current, "B2R08 frontier drift")
    else:
        require(isinstance(completed, list) and "B2R08" in completed, "B2R08 completion lost")
        require("- [x] `B2R08`" in tasks, "B2R08 ledger completion lost")
        require(active != "B2R08", "B2R08 remained active after completion")

def verify_static() -> None:
    require(sha256(ATTEMPT) == ATTEMPT_SHA256, "ATTEMPT-002 bytes drift")
    require(sha256(PREPROCESSING) == PREPROCESSING_SHA256, "preprocessing bytes drift")
    require(sha256(REBINDING) == REBINDING_SHA256, "rebinding bytes drift")
    for revision in (PRIMARY_SOURCE, QUALIFICATION_SOURCE, SEAL_SOURCE): require(git("rev-parse", f"{revision}^{{commit}}") == revision, f"source missing: {revision}")
    for path, blob in BLOBS.items(): require(git("hash-object", path) == blob, f"mergeable blob drift: {path}")

def verify_qualification() -> None:
    require(QUALIFICATION.stat().st_size == QUALIFICATION_SIZE and sha256(QUALIFICATION) == QUALIFICATION_SHA256, "qualification bytes drift")
    q = load(QUALIFICATION); u = dict(q); payload = u.pop("evidence_payload_sha256", None)
    require(payload == QUALIFICATION_PAYLOAD_SHA256 and hashlib.sha256(canonical(u)).hexdigest() == payload, "qualification payload drift")
    require((q.get("task"), q.get("attempt_id"), q.get("state")) == ("B2R08", "000B2-PUBLIC-ATTEMPT-002", "NON_PRIMARY_SHARD_EQUIVALENCE_QUALIFIED"), "qualification identity drift")
    require(q.get("material_class") == "DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY", "qualification material drift")
    require(q.get("primary_corpus_accessed") is False and q.get("candidate_result_accessed") is False, "qualification isolation drift")
    k = q.get("qualification", {})
    require(k.get("fixture_count") == 8 and k.get("shard_count") == 4 and k.get("mismatch_count") == 0 and k.get("semantic_rows_byte_identical") is True, "qualification result drift")
    require(k.get("ignored_fields") == ["decode_wall_seconds"] and k.get("full_semantic_sha256") == k.get("sharded_semantic_sha256"), "qualification semantic hash drift")
    run = q.get("run", {})
    require(run.get("github_run_id") == QUALIFICATION_RUN_ID and run.get("repository_revision") == QUALIFICATION_SOURCE and run.get("github_job") == "qualify-b2r08-sharding", "qualification run drift")
    require(q.get("claim_guards") == CLAIMS, "qualification claims drift")

def verify_provenance() -> None:
    require(sha256(PROVENANCE) == PROVENANCE_SHA256, "provenance bytes drift")
    p = load(PROVENANCE); u = dict(p); payload = u.pop("provenance_payload_sha256", None)
    require(isinstance(payload, str) and hashlib.sha256(canonical(u)).hexdigest() == payload, "provenance payload drift")
    require((p.get("task"), p.get("attempt_id"), p.get("candidate_id")) == ("B2R08", "000B2-PUBLIC-ATTEMPT-002", "whispercpp-balanced"), "provenance identity drift")
    src = p.get("canonical_evidence_source", {})
    require((src.get("workflow_id"), src.get("run_id"), src.get("job_id"), src.get("artifact_id")) == (352504105, SEAL_RUN_ID, 101830233512, 10029053259), "seal source identity drift")
    require(src.get("source_revision") == SEAL_SOURCE and src.get("artifact_zip_sha256") == "6345de28752f714c1a49ce81cbf4b89e86e8f4520ce2b0f0c573843f90c4090a", "seal provenance drift")
    require(src.get("evidence_raw_file_sha256") == EVIDENCE_SHA256 and src.get("evidence_payload_sha256") == PAYLOAD_SHA256 and src.get("selection_basis", "").endswith("NOT_RESULT_DRIVEN"), "evidence provenance drift")
    failed = p.get("original_failed_primary", {})
    require((failed.get("run_id"), failed.get("job_id"), failed.get("artifact_id")) == (34067447713, 101578604948, 10005732797), "failed primary identity drift")
    require(failed.get("artifact_contents") == ["whisper-build/wispral-build-identity.json"] and failed.get("transcript_artifact_present") is False and failed.get("evidence_json_present") is False and failed.get("candidate_result_inspection_before_repair") is False and failed.get("selection_effect") == "NONE", "failed primary exposure drift")
    repair = p.get("forward_only_repair", {})
    require(repair.get("policy") == "FORWARD_ONLY_DETERMINISTIC_CONTIGUOUS_SHARDING_AFTER_HOSTED_RUNNER_CEILING" and repair.get("shard_sizes") == [60,60,60,60] and repair.get("per_shard_adapter_timeout_seconds") == 18000, "repair policy drift")
    for key in ("candidate_changed","model_changed","runtime_revision_changed","frozen_audio_membership_changed","frozen_audio_bytes_changed","frozen_input_order_changed_in_final_evidence","c0_controls_changed","scorer_changed","normalization_changed","reference_transcript_access_during_decode","accuracy_scoring_during_decode"):
        require(repair.get(key) is False, f"repair semantic drift: {key}")
    q = p.get("equivalence_qualification", {})
    require((q.get("run_id"), q.get("job_id"), q.get("artifact_id")) == (QUALIFICATION_RUN_ID, 101790371251, 10024691621), "qualification provenance identity drift")
    require(q.get("primary_corpus_accessed") is False and q.get("candidate_result_accessed") is False and q.get("mismatch_count") == 0 and q.get("semantic_rows_byte_identical") is True, "qualification provenance drift")
    primary = p.get("sharded_primary", {})
    require(primary.get("run_id") == PRIMARY_RUN_ID and primary.get("source_revision") == PRIMARY_SOURCE and primary.get("preflight_job_id") == 101796754393, "primary provenance drift")
    shards = primary.get("shards"); require(isinstance(shards, list) and [s.get("shard_index") for s in shards] == [0,1,2,3], "shard provenance order drift")
    require([s.get("job_id") for s in shards] == [101796800482,101796800522,101796800502,101796800450], "shard job identity drift")
    require([s.get("id") for s in shards] == [10028072115,10028151064,10027694151,10028582691], "shard artifact identity drift")
    seal = p.get("seal", {})
    require(seal.get("prepared_staging_commit") == "5d549bb46c7e232f06d975a91aae2a22b2ec7ee1" and seal.get("execution_source") == SEAL_SOURCE and seal.get("workflow_content_blob_sha") == "c89986f9f9bb1d1b5b5386985469a67819931a4c" and seal.get("workflow_content_unchanged_by_trigger_commit") is True, "seal chronology drift")
    accounting = p.get("result_accounting", {})
    require((accounting.get("input_count"), accounting.get("decoded_count"), accounting.get("failure_count")) == (240,240,0) and accounting.get("result_driven_evidence_selection") is False, "provenance accounting drift")
    require(p.get("claims") == CLAIMS, "provenance claims drift")

def verify_evidence() -> None:
    require(EVIDENCE.stat().st_size == EVIDENCE_SIZE and sha256(EVIDENCE) == EVIDENCE_SHA256, "evidence bytes drift")
    e = load(EVIDENCE); u = dict(e); payload = u.pop("evidence_payload_sha256", None)
    require(payload == PAYLOAD_SHA256 and hashlib.sha256(canonical(u)).hexdigest() == payload, "evidence payload drift")
    require((e.get("task"), e.get("attempt_id"), e.get("state")) == ("B2R08", "000B2-PUBLIC-ATTEMPT-002", "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED"), "evidence identity drift")
    c = e.get("candidate", {})
    require((c.get("cell_index"), c.get("candidate_id"), c.get("tier"), c.get("family")) == (4,"whispercpp-balanced","BALANCED","whisper.cpp"), "candidate drift")
    require(c.get("runtime_revision") == "371b5a7561823ab2bb32142d2751e35e7534727b" and c.get("runtime_source_tree") == "3d7ce4f956997cfa325c7556533aba5604278463" and c.get("model_source_revision") == "80da2d8bfee42b0e836fc3a9890373e5defc00a6" and c.get("model") == "ggml-small.en.bin", "runtime/model drift")
    builds = c.get("adapter_build_identities"); require(isinstance(builds, list) and [b.get("shard_index") for b in builds] == [0,1,2,3], "build identity coverage drift")
    for b in builds:
        ident = b.get("identity", {}); require(ident.get("source_revision") == "371b5a7561823ab2bb32142d2751e35e7534727b" and ident.get("source_tree") == "3d7ce4f956997cfa325c7556533aba5604278463" and ident.get("ggml_cuda") == "OFF" and ident.get("ggml_metal") == "OFF" and ident.get("adapter_source_sha256") == "ac481f71af8657f15213651304284c199f8598a901fa34997c79d603e5ad0470" and ident.get("adapter_cmake_sha256") == "61e4292ac51c06dbb5805ee13c7d09e673276ec5435d0bda8224472e6eab570b", "build identity drift")
    c0 = e.get("c0_controls", {})
    require(c0.get("language") == "en" and c0.get("threads") == 4 and c0.get("step_ms") == 500 and c0.get("length_ms") == 5000 and c0.get("keep_ms") == 200 and c0.get("sampling") == "GREEDY" and c0.get("temperature_fallback") == "OFF" and c0.get("use_gpu") is False and c0.get("vad") is False and c0.get("repository_context_used") is False and c0.get("test_specific_context_used") is False and c0.get("candidate_specific_audio_transform_used") is False and c0.get("identical_frozen_audio_required_across_candidates") is True, "C0 drift")
    o = e.get("execution_orchestration", {})
    require(o.get("policy") == "FORWARD_ONLY_DETERMINISTIC_CONTIGUOUS_SHARDING_AFTER_HOSTED_RUNNER_CEILING" and o.get("shard_count") == 4 and o.get("shard_sizes") == [60,60,60,60] and o.get("per_shard_adapter_processes") == 1 and o.get("per_shard_adapter_timeout_seconds") == 18000 and o.get("failed_primary_run_id") == 34067447713 and o.get("failed_primary_artifact_id") == 10005732797 and o.get("candidate_result_inspection_before_repair") is False and o.get("equivalence_qualification_run_id") == QUALIFICATION_RUN_ID, "orchestration identity drift")
    for key in ("candidate_changed","model_changed","runtime_revision_changed","frozen_audio_membership_changed","frozen_audio_bytes_changed","frozen_input_order_changed_in_final_evidence","c0_controls_changed","scorer_changed","normalization_changed"): require(o.get(key) is False, f"orchestration semantic drift: {key}")
    run = e.get("run", {}); require(run.get("repository_revision") == SEAL_SOURCE and run.get("github_run_id") == SEAL_RUN_ID and run.get("github_job") == "seal-b2r08" and run.get("timing_semantics") == "DIAGNOSTIC_ONLY", "seal run identity drift")
    shards = e.get("shard_runs"); require(isinstance(shards, list) and [s.get("shard_index") for s in shards] == [0,1,2,3], "shard run coverage drift")
    require(all(s.get("run",{}).get("github_run_id") == PRIMARY_RUN_ID and s.get("run",{}).get("repository_revision") == PRIMARY_SOURCE for s in shards), "shard run identity drift")
    x = e.get("execution", {}); records = x.get("records")
    require((x.get("input_count"), x.get("decoded_count"), x.get("failure_count")) == (240,240,0), "execution accounting drift")
    require(x.get("all_frozen_input_hashes_reverified") is True and x.get("all_speech_samples_delivered_for_decoded_records") is True and x.get("all_zero_suffix_samples_delivered_for_decoded_records") is True and x.get("reference_transcripts_loaded_by_decoder") is False and x.get("accuracy_scoring_performed") is False and x.get("comparative_ranking_present") is False and x.get("performance_claim_present") is False, "execution guard drift")
    require(isinstance(records, list) and len(records) == 240, "record coverage drift")
    ids = [r.get("utterance_id") for r in records]; require(ids == sorted(ids) and len(set(ids)) == 240, "record order/uniqueness drift")
    require(all(r.get("status") == "DECODED" and r.get("failure") is None and r.get("speech_samples_delivered") == r.get("speech_sample_count") and r.get("zero_suffix_samples_delivered") == 10560 and r.get("zero_suffix_chunks_delivered") == 2 for r in records), "record feed/status drift")
    require(e.get("claim_guards") == CLAIMS, "evidence claims drift")

def main() -> int:
    verify_frontier(); verify_static(); verify_qualification(); verify_provenance(); verify_evidence()
    print("B2R08_EVIDENCE=PASS")
    print(f"B2R08_SEAL_SOURCE={SEAL_SOURCE}")
    print(f"B2R08_SEAL_RUN_ID={SEAL_RUN_ID}")
    print("B2R08_INPUTS=240"); print("B2R08_DECODED=240"); print("B2R08_FAILURES=0"); print("B2R09_AUTHORIZED=NO")
    return 0
if __name__ == "__main__": raise SystemExit(main())
