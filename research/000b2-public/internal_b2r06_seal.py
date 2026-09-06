#!/usr/bin/env python3
"""Seal exact B2R06 primary evidence into the clean task branch after successful capture."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
BASE = "04056b795a54e38d9d075e4de7aff15df1be2b3b"
TASK_BRANCH = "research/000b2-b2r06-moonshine-balanced"
EXPECTED_TASK_HEAD = "ec25eadab9818a54707b604deb936f10d16206f7"
SOURCE_REVISION = "fd933886fcaa7a00338de8a96b7b2913124816f1"
DECODER_BLOB = "72555a02e21f3d2790e86ecdf128cee0b19b659e"
RUN_ID = 34041046129
JOB_ID = 101507742625
WORKFLOW_ID = 351624005
WORKFLOW_NAME = "Internal B2R06 ATTEMPT-002 Capture"
WORKFLOW_PATH = ".github/workflows/internal-b2r06-capture.yml"
ARTIFACT_NAME = f"b2r06-moonshine-balanced-{SOURCE_REVISION}"
ATTEMPT_SHA256 = "a2dc8246e4567e670beb3f26e315be93e001e4d9a9037be57ff11fce5a340134"
FREEZE_DIGEST = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
PREPROCESSING_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
REBINDING_SHA256 = "f9cda5168e6cafb6a1e9e6898f394ec3987b37af50c53c15cf63bc136c1f2df1"
C0_SHA256 = "c0f0093cda7ca036c8a97178364b3840ce7093386a8cb711ccef5f183a4453c0"
FAILURE = {"type": "C0HarnessError", "message": "Moonshine C0 input exceeds the frozen 12-second primary utterance bound"}
EXPECTED_SCOPE = {
    "research/000b2-public/b2r06-moonshine-balanced.json",
    "research/000b2-public/b2r06-provenance.json",
    "research/000b2-public/decode_b2r06.py",
    "research/000b2-public/verify_attempt_manifest.py",
    "research/000b2-public/verify_b2r06.py",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def run(*args: str, cwd: Path = ROOT, capture: bool = False, binary: bool = False) -> Any:
    result = subprocess.run(
        list(args), cwd=cwd, check=True,
        text=not binary,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture and not binary else result.stdout if capture else ""


def api(path: str) -> Any:
    return json.loads(run("gh", "api", path, capture=True))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def verify_capture_truth() -> tuple[dict[str, Any], dict[str, Any]]:
    repository = os.environ["GITHUB_REPOSITORY"]
    run_data = api(f"repos/{repository}/actions/runs/{RUN_ID}")
    require(run_data.get("id") == RUN_ID, "capture run id drift")
    require(run_data.get("workflow_id") == WORKFLOW_ID, "capture workflow id drift")
    require(run_data.get("name") == WORKFLOW_NAME and run_data.get("path") == WORKFLOW_PATH, "capture workflow identity drift")
    require(run_data.get("event") == "push", "capture event drift")
    require(run_data.get("head_sha") == SOURCE_REVISION, "capture source revision drift")
    require(run_data.get("head_branch") == "research/000b2-b2r06-execution", "capture source branch drift")
    require(run_data.get("status") == "completed" and run_data.get("conclusion") == "success", "capture run is not successful")

    jobs = api(f"repos/{repository}/actions/runs/{RUN_ID}/jobs?per_page=100").get("jobs", [])
    matches = [row for row in jobs if row.get("id") == JOB_ID]
    require(len(matches) == 1, "capture job identity missing")
    job = matches[0]
    require(job.get("name") == "capture-b2r06" and job.get("status") == "completed" and job.get("conclusion") == "success",
            "capture job is not successful")

    artifacts = api(f"repos/{repository}/actions/runs/{RUN_ID}/artifacts?per_page=100").get("artifacts", [])
    matches = [row for row in artifacts if row.get("name") == ARTIFACT_NAME]
    require(len(matches) == 1, f"expected exactly one capture artifact, got {len(matches)}")
    artifact = matches[0]
    require(artifact.get("expired") is False, "capture artifact expired")
    require(isinstance(artifact.get("id"), int) and artifact["id"] > 0, "artifact id missing")
    return run_data, artifact


def download_artifact(artifact: dict[str, Any], temp: Path) -> tuple[bytes, bytes, dict[str, Any]]:
    repository = os.environ["GITHUB_REPOSITORY"]
    token = os.environ.get("GH_TOKEN", "")
    require(bool(token), "GH_TOKEN missing")
    zip_path = temp / "b2r06.zip"
    url = f"https://api.github.com/repos/{repository}/actions/artifacts/{artifact['id']}/zip"
    run("curl", "-fsSL", "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/vnd.github+json",
        "-H", "X-GitHub-Api-Version: 2022-11-28", url, "-o", str(zip_path))
    zip_bytes = zip_path.read_bytes()
    require(len(zip_bytes) == artifact.get("size_in_bytes"), "artifact ZIP size drift")
    digest = artifact.get("digest")
    if isinstance(digest, str) and digest.startswith("sha256:"):
        require(digest == f"sha256:{sha256_bytes(zip_bytes)}", "artifact API digest drift")
    with zipfile.ZipFile(zip_path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        require(names == ["b2r06-moonshine-balanced.json"], f"unexpected artifact files: {names!r}")
        raw = archive.read(names[0])
    evidence = json.loads(raw.decode("utf-8"))
    require(isinstance(evidence, dict), "evidence root is not an object")
    return zip_bytes, raw, evidence


def expected_artifacts(task_root: Path) -> list[dict[str, Any]]:
    materialized = json.loads((task_root / "research/000b2-entry/materialized-artifacts.json").read_text(encoding="utf-8"))
    rows = materialized["artifacts"]["moonshine-balanced"]
    return [
        {"path": name, "sha256": row["sha256"], "size_bytes": row["size_bytes"]}
        for name, row in sorted(rows.items())
    ]


def verify_evidence_semantics(e: dict[str, Any], task_root: Path) -> str:
    require((e.get("schema_version"), e.get("task"), e.get("state"), e.get("attempt_id")) ==
            ("000b2-public-b2r06-decode-v1", "B2R06", "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED", "000B2-PUBLIC-ATTEMPT-002"),
            "evidence task/state drift")
    payload = e.get("evidence_payload_sha256")
    unsigned = dict(e); unsigned.pop("evidence_payload_sha256", None)
    require(isinstance(payload, str) and payload == sha256_bytes(canonical(unsigned)), "evidence payload digest mismatch")
    authority = e.get("authority", {})
    require(authority.get("canonical_authority_base") == BASE and authority.get("attempt_freeze_digest_sha256") == FREEZE_DIGEST and
            authority.get("preprocessing_capture_sha256") == PREPROCESSING_SHA256 and authority.get("b2r03_rebinding_sha256") == REBINDING_SHA256 and
            authority.get("corrected_c0_harness_sha256") == C0_SHA256, "evidence authority drift")
    candidate = e.get("candidate", {})
    require((candidate.get("cell_index"), candidate.get("candidate_id"), candidate.get("family"), candidate.get("tier")) ==
            (2, "moonshine-balanced", "moonshine", "BALANCED"), "candidate identity drift")
    require(candidate.get("runtime_distribution") == "moonshine-voice" and candidate.get("runtime_distribution_version") == "0.1.5" and
            candidate.get("runtime_revision") == "234f60faa0eb388b01cdf7e60aca232af37aefda" and
            candidate.get("model_arch") == 5 and candidate.get("model_asset_revision") == "quantized_26_08_21", "runtime/model identity drift")
    observed_artifacts = sorted(candidate.get("artifacts", []), key=lambda row: row.get("path", ""))
    require(observed_artifacts == expected_artifacts(task_root), "model artifact identity drift")
    require(e.get("c0_controls") == {
        "candidate_specific_audio_transform_used": False, "context": None, "feed_chunk_ms": 500,
        "feed_chunk_samples": 8000, "final_zero_pad_ms": 660, "final_zero_pad_samples": 10560,
        "identical_frozen_audio_required_across_candidates": True, "keyterms": [], "repository_context_used": False,
        "test_specific_context_used": False, "transcription_interval_seconds": 0.5, "vad_threshold": 0.0,
    }, "C0 controls drift")
    run_data = e.get("run", {})
    require(run_data.get("repository_revision") == SOURCE_REVISION and run_data.get("github_run_id") == RUN_ID and
            run_data.get("github_run_attempt") == 1 and run_data.get("github_job") == "capture-b2r06" and
            run_data.get("github_ref") == "refs/heads/research/000b2-b2r06-execution" and run_data.get("python") == "3.12.14",
            "run identity drift")
    require(run_data.get("timing_semantics") == "DIAGNOSTIC_ONLY" and run_data.get("comparative_performance_authorized") is False,
            "timing claim drift")
    preprocessing = json.loads((task_root / "research/000b2-public/preprocessing-capture.json").read_text(encoding="utf-8"))["execution"]["records"]
    expected = {row["utterance_id"]: row for row in preprocessing}
    execution = e.get("execution", {}); records = execution.get("records")
    require(isinstance(records, list) and len(records) == 240 and execution.get("input_count") == 240, "execution coverage drift")
    require(execution.get("all_frozen_input_hashes_reverified") is True and execution.get("reference_transcripts_loaded_by_decoder") is False and
            execution.get("accuracy_scoring_performed") is False and execution.get("comparative_ranking_present") is False and
            execution.get("performance_claim_present") is False, "execution guard drift")
    seen: set[str] = set(); decoded = 0; failed = 0
    for row in records:
        uid = row.get("utterance_id")
        require(uid in expected and uid not in seen, f"utterance identity drift: {uid}")
        seen.add(uid); source = expected[uid]; frames = source.get("wav_frame_count")
        require(row.get("source_partition") == source.get("source_partition") and
                row.get("canonical_preprocessed_file_sha256") == source.get("canonical_preprocessed_file_sha256"), f"input identity drift: {uid}")
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
            require(isinstance(frames, int) and frames > 192000 and row.get("failure") == FAILURE,
                    f"failure bound/preservation drift: {uid}")
            require(row.get("feed_trace") is None and row.get("raw_lines") == [] and row.get("raw_transcript") == "", f"failure bytes drift: {uid}")
        else:
            raise SystemExit(f"unknown status: {uid}")
    require((decoded, failed, execution.get("decoded_count"), execution.get("failure_count")) == (209, 31, 209, 31),
            "result accounting drift")
    require(e.get("claim_guards") == {
        "b2r07_authorized": False, "comparative_performance_authorized": False, "comparative_result_available": False,
        "human_developer_speech_accuracy_evidence": "ABSENT", "product_code_authorized": False, "production_stt_selected": False,
    }, "claim guard drift")
    return payload


def build_provenance(artifact: dict[str, Any], zip_bytes: bytes, raw: bytes, payload: str) -> dict[str, Any]:
    return {
        "schema_version": "000b2-public-b2r06-provenance-v1",
        "task": "B2R06",
        "attempt_id": "000B2-PUBLIC-ATTEMPT-002",
        "candidate_id": "moonshine-balanced",
        "canonical_evidence_source": {
            "role": "CANONICAL_EVIDENCE_SOURCE",
            "selection_basis": "FIRST_EXECUTION_THAT_PASSED_CURRENT_B2R06_AUTHORITY_FROZEN_INPUT_DECODE_SEMANTICS_AND_ARTIFACT_GATES; NOT_RESULT_DRIVEN",
            "workflow_name": WORKFLOW_NAME,
            "workflow_id": WORKFLOW_ID,
            "event": "push",
            "conclusion": "success",
            "run_id": RUN_ID,
            "run_attempt": 1,
            "job_id": JOB_ID,
            "job_name": "capture-b2r06",
            "source_branch": "research/000b2-b2r06-execution",
            "source_revision": SOURCE_REVISION,
            "execution_decoder_blob_sha": DECODER_BLOB,
            "mergeable_decoder_blob_sha": DECODER_BLOB,
            "artifact_id": artifact["id"],
            "artifact_name": ARTIFACT_NAME,
            "artifact_zip_size_bytes": len(zip_bytes),
            "artifact_zip_sha256": sha256_bytes(zip_bytes),
            "evidence_path": "research/000b2-public/b2r06-moonshine-balanced.json",
            "evidence_raw_file_size_bytes": len(raw),
            "evidence_raw_file_sha256": sha256_bytes(raw),
            "evidence_payload_sha256": payload,
        },
        "related_execution_attempts": [],
        "construction_history": [
            {"role": "NON_PRIMARY_CONSTRUCTION", "run_id": 34037600568, "conclusion": "failure", "primary_decode_started": False, "selection_effect": "NONE"},
            {"role": "NON_PRIMARY_CONSTRUCTION", "run_id": 34037676040, "conclusion": "failure", "primary_decode_started": False, "selection_effect": "NONE"},
            {"role": "NON_PRIMARY_CONSTRUCTION", "run_id": 34040971762, "conclusion": "success", "primary_decode_started": False, "selection_effect": "NONE"},
        ],
        "result_accounting": {
            "input_count": 240,
            "decoded_count": 209,
            "failure_count": 31,
            "failure_type": FAILURE["type"],
            "failure_reason": FAILURE["message"],
            "all_failures_are_frozen_c0_preinference_bound_rejections": True,
            "failures_preserved_without_retry_or_c0_change": True,
            "reference_transcripts_loaded_by_decoder": False,
            "accuracy_scoring_performed": False,
            "result_driven_evidence_selection": False,
            "timing_semantics": "DIAGNOSTIC_ONLY",
        },
        "claims": {
            "b2r07_authorized": False,
            "comparative_result_available": False,
            "comparative_performance_authorized": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
        "provenance_status": "RECORDED_FROM_EXACT_GITHUB_ACTIONS_RUN_ARTIFACT_WITH_NON_PRIMARY_CONSTRUCTION_HISTORY_PRESERVED",
    }


def build_verifier(*, evidence_sha: str, evidence_size: int, payload_sha: str, provenance_sha: str,
                   artifact_id: int, artifact_zip_sha: str, materialized_sha: str) -> str:
    return f'''#!/usr/bin/env python3
"""Verify sealed B2R06 ATTEMPT-002 moonshine-balanced execution evidence."""
from __future__ import annotations
import hashlib, json, subprocess, sys
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
MATERIALIZED = ROOT / "research" / "000b2-entry" / "materialized-artifacts.json"
READINESS = PUBLIC / "recovery-readiness.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"
CURRENT = ROOT / "specs" / "CURRENT.md"
CANONICAL_CURRENT = ROOT / "docs" / "canonical" / "CURRENT_STATE.md"
AUTHORITY_BASE = "{BASE}"
SOURCE_REVISION = "{SOURCE_REVISION}"
DECODER_BLOB = "{DECODER_BLOB}"
ATTEMPT_SHA256 = "{ATTEMPT_SHA256}"
FREEZE_DIGEST = "{FREEZE_DIGEST}"
PREPROCESSING_SHA256 = "{PREPROCESSING_SHA256}"
REBINDING_SHA256 = "{REBINDING_SHA256}"
C0_SHA256 = "{C0_SHA256}"
MATERIALIZED_SHA256 = "{materialized_sha}"
EVIDENCE_SHA256 = "{evidence_sha}"
EVIDENCE_SIZE = {evidence_size}
PAYLOAD_SHA256 = "{payload_sha}"
PROVENANCE_SHA256 = "{provenance_sha}"
RUN_ID = {RUN_ID}
JOB_ID = {JOB_ID}
WORKFLOW_ID = {WORKFLOW_ID}
ARTIFACT_ID = {artifact_id}
ARTIFACT_NAME = "{ARTIFACT_NAME}"
ARTIFACT_ZIP_SHA256 = "{artifact_zip_sha}"
FAILURE = {FAILURE!r}
PREFIX = ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05"]
class VerifyError(ValueError): pass
def require(ok: bool, message: str) -> None:
    if not ok: raise VerifyError(message)
def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8")); require(isinstance(value, dict), f"object expected: {{path}}"); return value
def sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value: Any) -> bytes: return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\\n").encode()
def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
def verify_frontier() -> None:
    readiness = load(READINESS); tasks = TASKS.read_text(encoding="utf-8"); current = CURRENT.read_text(encoding="utf-8"); canonical_current = CANONICAL_CURRENT.read_text(encoding="utf-8")
    require(readiness.get("state") == "RECOVERY_READY" and readiness.get("qualified_workflow_change_paths") == [], "recovery authority drift")
    require(readiness.get("claim_guards") == {{"human_developer_speech_accuracy_evidence":"ABSENT","comparative_result_available":False,"production_stt_selected":False,"product_code_authorized":False}}, "recovery claim guards drift")
    replacement = readiness.get("replacement_attempt", {{}}); require(replacement.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-002" and replacement.get("frozen") is True and replacement.get("primary_decode_entry_open") is True, "ATTEMPT-002 entry drift")
    completed = readiness.get("completed_recovery_tasks"); active = readiness.get("active_recovery_unit")
    if completed == PREFIX and active == "B2R06":
        require(str(readiness.get("next_action", "")).startswith("Qualify B2R06 only:"), "B2R06 frontier drift")
        require("- [x] `B2R05`" in tasks and "- [ ] `B2R06`" in tasks and "- [ ] `B2R07`" in tasks, "B2R06 task frontier drift")
        require("active recovery unit `B2R06`" in current and "**Active recovery unit:** `B2R06`" in canonical_current, "B2R06 canonical frontier drift")
    elif completed == PREFIX + ["B2R06"] and active == "B2R07":
        require(str(readiness.get("next_action", "")).startswith("Qualify B2R07 only:"), "B2R07 frontier drift")
        require("- [x] `B2R06`" in tasks and "- [ ] `B2R07`" in tasks, "post-B2R06 task frontier drift")
        require("active recovery unit `B2R07`" in current and "**Active recovery unit:** `B2R07`" in canonical_current, "B2R07 canonical frontier drift")
    else:
        require(isinstance(completed, list) and "B2R06" in completed and "- [x] `B2R06`" in tasks, "later state lost B2R06 completion")
def expected_artifacts() -> list[dict[str, Any]]:
    rows = load(MATERIALIZED)["artifacts"]["moonshine-balanced"]
    return [{{"path":name,"sha256":row["sha256"],"size_bytes":row["size_bytes"]}} for name,row in sorted(rows.items())]
def verify_static_identities() -> None:
    attempt = load(ATTEMPT); require(sha256(ATTEMPT) == ATTEMPT_SHA256 and attempt.get("freeze_digest_sha256") == FREEZE_DIGEST, "ATTEMPT-002 drift")
    require(sha256(PREPROCESSING) == PREPROCESSING_SHA256 and sha256(REBINDING) == REBINDING_SHA256 and sha256(C0) == C0_SHA256 and sha256(MATERIALIZED) == MATERIALIZED_SHA256, "frozen identity drift")
    require(git("hash-object", str(DECODER.relative_to(ROOT))) == DECODER_BLOB, "mergeable decoder blob drift")
    require(git("rev-parse", f"{{SOURCE_REVISION}}^{{commit}}") == SOURCE_REVISION and git("rev-parse", f"{{SOURCE_REVISION}}:research/000b2-public/decode_b2r06.py") == DECODER_BLOB, "execution decoder binding drift")
def verify_provenance() -> None:
    require(sha256(PROVENANCE) == PROVENANCE_SHA256, "provenance bytes drift"); p = load(PROVENANCE)
    require((p.get("task"),p.get("attempt_id"),p.get("candidate_id")) == ("B2R06","000B2-PUBLIC-ATTEMPT-002","moonshine-balanced"), "provenance identity drift")
    s=p.get("canonical_evidence_source",{{}}); require(s.get("selection_basis") == "FIRST_EXECUTION_THAT_PASSED_CURRENT_B2R06_AUTHORITY_FROZEN_INPUT_DECODE_SEMANTICS_AND_ARTIFACT_GATES; NOT_RESULT_DRIVEN", "selection basis drift")
    require(s.get("workflow_id")==WORKFLOW_ID and s.get("run_id")==RUN_ID and s.get("job_id")==JOB_ID and s.get("source_revision")==SOURCE_REVISION and s.get("execution_decoder_blob_sha")==DECODER_BLOB and s.get("mergeable_decoder_blob_sha")==DECODER_BLOB, "capture provenance drift")
    require(s.get("artifact_id")==ARTIFACT_ID and s.get("artifact_name")==ARTIFACT_NAME and s.get("artifact_zip_sha256")==ARTIFACT_ZIP_SHA256 and s.get("evidence_raw_file_sha256")==EVIDENCE_SHA256 and s.get("evidence_raw_file_size_bytes")==EVIDENCE_SIZE and s.get("evidence_payload_sha256")==PAYLOAD_SHA256, "artifact provenance drift")
    require(p.get("related_execution_attempts") == [], "unexpected primary execution history")
    for row in p.get("construction_history",[]): require(row.get("primary_decode_started") is False and row.get("selection_effect")=="NONE", "construction history drift")
    a=p.get("result_accounting",{{}}); require((a.get("input_count"),a.get("decoded_count"),a.get("failure_count"))==(240,209,31) and a.get("result_driven_evidence_selection") is False, "result accounting drift")
    require(p.get("claims") == {{"b2r07_authorized":False,"comparative_result_available":False,"comparative_performance_authorized":False,"human_developer_speech_accuracy_evidence":"ABSENT","production_stt_selected":False,"product_code_authorized":False}}, "provenance claims drift")
def verify_evidence() -> dict[str, Any]:
    require(EVIDENCE.stat().st_size==EVIDENCE_SIZE and sha256(EVIDENCE)==EVIDENCE_SHA256, "raw evidence bytes drift"); e=load(EVIDENCE); payload=e.get("evidence_payload_sha256"); unsigned=dict(e); unsigned.pop("evidence_payload_sha256",None); require(payload==PAYLOAD_SHA256 and hashlib.sha256(canonical(unsigned)).hexdigest()==PAYLOAD_SHA256,"payload drift")
    require((e.get("schema_version"),e.get("task"),e.get("state"),e.get("attempt_id")) == ("000b2-public-b2r06-decode-v1","B2R06","ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED","000B2-PUBLIC-ATTEMPT-002"), "evidence identity drift")
    authority=e.get("authority",{{}}); require(authority.get("canonical_authority_base")==AUTHORITY_BASE and authority.get("attempt_freeze_digest_sha256")==FREEZE_DIGEST and authority.get("preprocessing_capture_sha256")==PREPROCESSING_SHA256 and authority.get("b2r03_rebinding_sha256")==REBINDING_SHA256 and authority.get("corrected_c0_harness_sha256")==C0_SHA256,"authority binding drift")
    c=e.get("candidate",{{}}); require((c.get("cell_index"),c.get("candidate_id"),c.get("family"),c.get("tier"),c.get("model_arch"))==(2,"moonshine-balanced","moonshine","BALANCED",5),"candidate drift"); require(c.get("runtime_distribution")=="moonshine-voice" and c.get("runtime_distribution_version")=="0.1.5" and c.get("runtime_revision")=="234f60faa0eb388b01cdf7e60aca232af37aefda" and c.get("model_asset_revision")=="quantized_26_08_21","runtime/model drift"); require(sorted(c.get("artifacts",[]),key=lambda row:row.get("path",""))==expected_artifacts(),"model artifact drift")
    require(e.get("c0_controls") == {{"candidate_specific_audio_transform_used":False,"context":None,"feed_chunk_ms":500,"feed_chunk_samples":8000,"final_zero_pad_ms":660,"final_zero_pad_samples":10560,"identical_frozen_audio_required_across_candidates":True,"keyterms":[],"repository_context_used":False,"test_specific_context_used":False,"transcription_interval_seconds":0.5,"vad_threshold":0.0}}, "C0 controls drift")
    r=e.get("run",{{}}); require(r.get("repository_revision")==SOURCE_REVISION and r.get("github_run_id")==RUN_ID and r.get("github_run_attempt")==1 and r.get("github_job")=="capture-b2r06" and r.get("github_ref")=="refs/heads/research/000b2-b2r06-execution" and r.get("python")=="3.12.14","run identity drift"); require(r.get("timing_semantics")=="DIAGNOSTIC_ONLY" and r.get("comparative_performance_authorized") is False,"timing claim drift")
    preprocessing=load(PREPROCESSING)["execution"]["records"]; expected={{row["utterance_id"]:row for row in preprocessing}}; x=e.get("execution",{{}}); records=x.get("records"); require(isinstance(records,list) and len(records)==240 and x.get("input_count")==240,"coverage drift"); require(x.get("all_frozen_input_hashes_reverified") is True and x.get("reference_transcripts_loaded_by_decoder") is False and x.get("accuracy_scoring_performed") is False and x.get("comparative_ranking_present") is False and x.get("performance_claim_present") is False,"execution guard drift")
    seen=set(); decoded=failed=0
    for row in records:
        uid=row.get("utterance_id"); require(uid in expected and uid not in seen,f"utterance drift: {{uid}}"); seen.add(uid); src=expected[uid]; frames=src.get("wav_frame_count"); require(row.get("source_partition")==src.get("source_partition") and row.get("canonical_preprocessed_file_sha256")==src.get("canonical_preprocessed_file_sha256"),f"input drift: {{uid}}")
        if row.get("status")=="DECODED":
            decoded+=1; require(isinstance(frames,int) and frames<=192000 and row.get("failure") is None,f"decoded bound drift: {{uid}}"); require(row.get("raw_transcript")==" ".join(row.get("raw_lines",[])).strip(),f"transcript drift: {{uid}}"); trace=row.get("feed_trace",{{}}); chunks=trace.get("speech_chunk_samples"); require(isinstance(chunks,list) and chunks and all(isinstance(n,int) and 0<n<=8000 for n in chunks),f"chunk drift: {{uid}}"); require(all(n==8000 for n in chunks[:-1]) and sum(chunks)==trace.get("speech_samples")==frames,f"feed drift: {{uid}}"); require(trace.get("zero_pad_samples")==10560 and trace.get("sample_rate_hz")==16000 and trace.get("stream_started") is True and trace.get("stream_stopped") is True,f"stream drift: {{uid}}")
        elif row.get("status")=="FAILED":
            failed+=1; require(isinstance(frames,int) and frames>192000 and row.get("failure")==FAILURE and row.get("feed_trace") is None and row.get("raw_lines")==[] and row.get("raw_transcript")=="",f"failure drift: {{uid}}")
        else: raise VerifyError(f"unknown status: {{uid}}")
    require(len(seen)==240 and decoded==209 and failed==31 and x.get("decoded_count")==209 and x.get("failure_count")==31,"sealed result accounting drift")
    require(e.get("claim_guards") == {{"b2r07_authorized":False,"comparative_performance_authorized":False,"comparative_result_available":False,"human_developer_speech_accuracy_evidence":"ABSENT","product_code_authorized":False,"production_stt_selected":False}}, "evidence claims drift"); return e
def main() -> int:
    try:
        verify_frontier(); verify_static_identities(); verify_provenance(); evidence=verify_evidence(); print("B2R06_EVIDENCE=PASS"); print(f"B2R06_SOURCE_REVISION={{SOURCE_REVISION}}"); print(f"B2R06_CAPTURE_RUN_ID={{RUN_ID}}"); print(f"B2R06_ARTIFACT_ID={{ARTIFACT_ID}}"); print(f"B2R06_INPUTS={{evidence['execution']['input_count']}}"); print(f"B2R06_DECODED={{evidence['execution']['decoded_count']}}"); print(f"B2R06_FAILURES={{evidence['execution']['failure_count']}}"); print("B2R06_FAILURE_CLASS=FROZEN_C0_PREINFERENCE_12_SECOND_BOUND"); print("B2R07_AUTHORIZED=NO"); return 0
    except (VerifyError,OSError,json.JSONDecodeError,subprocess.CalledProcessError) as error:
        print(f"B2R06_EVIDENCE=FAIL: {{error}}",file=sys.stderr); return 1
if __name__ == "__main__": raise SystemExit(main())
'''


def update_composite(task_root: Path) -> None:
    path = task_root / "research/000b2-public/verify_attempt_manifest.py"
    text = path.read_text(encoding="utf-8")
    require("B2R06_VERIFIER" not in text, "composite already contains B2R06")
    text = text.replace("historical B2P08 and recovery B2R04/B2R05.", "historical B2P08 and recovery B2R04/B2R05/B2R06.", 1)
    anchor = 'B2R05_VERIFIER = PUBLIC / "verify_b2r05.py"\n'
    require(text.count(anchor) == 1, "B2R05 verifier constant anchor drift")
    text = text.replace(anchor, anchor + 'B2R06_VERIFIER = PUBLIC / "verify_b2r06.py"\n', 1)
    anchor = '    run_verifier(B2R05_VERIFIER, "wispral_b2r05_execution_evidence")\n'
    require(text.count(anchor) == 1, "B2R05 verifier call anchor drift")
    text = text.replace(anchor, anchor + '    run_verifier(B2R06_VERIFIER, "wispral_b2r06_execution_evidence")\n', 1)
    old = '    print("B2P08_B2R04_AND_B2R05_ATTEMPT_VERIFIER=PASS")\n'
    require(text.count(old) == 1, "composite marker anchor drift")
    text = text.replace(old, '    print("B2P08_B2R04_B2R05_AND_B2R06_ATTEMPT_VERIFIER=PASS")\n', 1)
    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    run_data, artifact = verify_capture_truth()
    run("git", "fetch", "--force", "--no-tags", "origin", "main:refs/remotes/origin/main", f"{TASK_BRANCH}:refs/remotes/origin/{TASK_BRANCH}")
    require(run("git", "rev-parse", "refs/remotes/origin/main", capture=True) == BASE, "canonical main moved before sealing")
    require(run("git", "rev-parse", f"refs/remotes/origin/{TASK_BRANCH}", capture=True) == EXPECTED_TASK_HEAD, "task branch moved before sealing")

    task_root = Path(tempfile.mkdtemp(prefix="b2r06-task-"))
    run("git", "worktree", "add", "--detach", str(task_root), f"refs/remotes/origin/{TASK_BRANCH}")
    require(set(run("git", "diff", "--name-only", BASE, "HEAD", cwd=task_root, capture=True).splitlines()) == {"research/000b2-public/decode_b2r06.py"},
            "pre-seal task branch is not decoder-only")
    require(run("git", "rev-parse", "HEAD:research/000b2-public/decode_b2r06.py", cwd=task_root, capture=True) == DECODER_BLOB,
            "task decoder blob drift")

    with tempfile.TemporaryDirectory(prefix="b2r06-artifact-") as td:
        zip_bytes, raw, evidence = download_artifact(artifact, Path(td))
    payload = verify_evidence_semantics(evidence, task_root)
    provenance = build_provenance(artifact, zip_bytes, raw, payload)
    provenance_bytes = json.dumps(provenance, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    evidence_path = task_root / "research/000b2-public/b2r06-moonshine-balanced.json"
    provenance_path = task_root / "research/000b2-public/b2r06-provenance.json"
    verifier_path = task_root / "research/000b2-public/verify_b2r06.py"
    evidence_path.write_bytes(raw)
    provenance_path.write_bytes(provenance_bytes)
    materialized_sha = sha256_file(task_root / "research/000b2-entry/materialized-artifacts.json")
    verifier = build_verifier(
        evidence_sha=sha256_bytes(raw), evidence_size=len(raw), payload_sha=payload,
        provenance_sha=sha256_bytes(provenance_bytes), artifact_id=artifact["id"],
        artifact_zip_sha=sha256_bytes(zip_bytes), materialized_sha=materialized_sha,
    )
    compile(verifier, str(verifier_path), "exec")
    verifier_path.write_text(verifier, encoding="utf-8")
    update_composite(task_root)

    run("git", "config", "user.name", "github-actions[bot]", cwd=task_root)
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com", cwd=task_root)
    run("git", "add", "research/000b2-public", cwd=task_root)
    scope = set(run("git", "diff", "--cached", "--name-only", BASE, capture=True, cwd=task_root).splitlines())
    require(scope == EXPECTED_SCOPE, f"sealed task scope drift: {sorted(scope)!r}")
    run("python", "research/000b2-public/verify_b2r06.py", cwd=task_root)
    run("python", "research/000b2-public/verify_attempt_manifest.py", cwd=task_root)
    run("git", "commit", "-m", "research(000b2): preserve B2R06 primary evidence", cwd=task_root)
    sealed_head = run("git", "rev-parse", "HEAD", capture=True, cwd=task_root)
    run("git", "push", "origin", f"HEAD:refs/heads/{TASK_BRANCH}", cwd=task_root)

    print(f"B2R06_SEALED_TASK_HEAD={sealed_head}")
    print(f"B2R06_ARTIFACT_ID={artifact['id']}")
    print(f"B2R06_ARTIFACT_ZIP_SHA256={sha256_bytes(zip_bytes)}")
    print(f"B2R06_EVIDENCE_SHA256={sha256_bytes(raw)}")
    print(f"B2R06_EVIDENCE_SIZE={len(raw)}")
    print(f"B2R06_PAYLOAD_SHA256={payload}")
    print(f"B2R06_PROVENANCE_SHA256={sha256_bytes(provenance_bytes)}")
    print("B2R06_SEAL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
