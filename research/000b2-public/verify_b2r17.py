#!/usr/bin/env python3
"""Verify the bounded B2R17 moonshine-compact primary capture."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
READINESS = PUBLIC / "recovery-attempt-003-readiness.json"
ATTEMPT = PUBLIC / "b2r16-attempt-003-manifest.json"
EVIDENCE = PUBLIC / "b2r17-moonshine-compact.json"
PROVENANCE = PUBLIC / "b2r17-provenance.json"
DECODER = PUBLIC / "decode_b2r17.py"
TASK = "B2R17"
AUTHORITY_BASE = "edacdf7504302cc91ff7138bc6ac2d391e4df1f4"
CAPTURE_REVISION = "3feab78d7e910014e999a76397f46385305c37b9"
CAPTURE_RUN = 34421672201
CAPTURE_JOB = 102698241270
FREEZE_DIGEST = "b92d0a88bb50ebde517f560878a26d0ef796abdaf931278f5bc43e372ff1ac8d"
EVIDENCE_SHA256 = "3750b74a6176bcde2fe4ef9be967d71d71f0b6123766836930c2eb5423d7110c"
EVIDENCE_BLOB = "c549bedc4ccd0ed8eaeac9677dbcedad844d2605"
PAYLOAD_SHA256 = "c12d29254975c94357fcc1ca8b70bcf4bfd3aa6d95414a663fb44b842e19f87e"
DECODER_SHA256 = "ce0ade690694461664465bbeaa230f362f53a8ca354127ae8c5eaf4f9e0cc89d"
DECODER_BLOB = "2d583f4dfd9e9980f6a8054f8ee86f416c3db1a1"
EXPECTED_SCOPE = [
    ".github/workflows/000b2-public-b2r17-moonshine-compact.yml",
    "research/000b2-public/decode_b2r17.py",
    "research/000b2-public/b2r17-moonshine-compact.json",
    "research/000b2-public/b2r17-provenance.json",
    "research/000b2-public/verify_b2r17.py",
]

class VerifyError(RuntimeError): pass

def require(ok: bool, msg: str) -> None:
    if not ok: raise VerifyError(msg)

def load(path: Path) -> dict[str, Any]:
    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out = {}
        for k,v in pairs:
            require(k not in out, f"duplicate JSON key: {k}")
            out[k]=v
        return out
    value=json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=hook)
    require(isinstance(value,dict), f"{path.name} root must be object")
    return value

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args: str) -> str:
    return subprocess.run(["git","-C",str(ROOT),*args],check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30).stdout.strip()

def blob(path: Path) -> str:
    return git("rev-parse",f"HEAD:{path.relative_to(ROOT).as_posix()}")

def verify_authority() -> None:
    r=load(READINESS)
    require(r.get("active_recovery_unit")==TASK,"B2R17 is not active")
    require(r.get("completed_recovery_tasks")==["B2R13","B2R14","B2R15","B2R16"],"predecessor ledger drift")
    a=r.get("replacement_attempt")
    require(isinstance(a,dict) and a.get("attempt_id")=="000B2-PUBLIC-ATTEMPT-003" and a.get("frozen") is True and a.get("primary_decode_entry_open") is True,"ATTEMPT-003 authority drift")
    require(r.get("task_candidate_scopes",{}).get(TASK)==EXPECTED_SCOPE,"B2R17 scope policy drift")
    git("merge-base","--is-ancestor",AUTHORITY_BASE,"HEAD")
    changed=sorted(x for x in git("diff","--name-only",AUTHORITY_BASE,"HEAD","--").splitlines() if x)
    require(changed==sorted(EXPECTED_SCOPE),"B2R17 actual candidate range scope drift")

def verify_evidence(require_git: bool) -> None:
    d=load(EVIDENCE)
    require(sha(EVIDENCE)==EVIDENCE_SHA256,"evidence bytes drift")
    require(d.get("task")==TASK and d.get("attempt_id")=="000B2-PUBLIC-ATTEMPT-003","evidence identity drift")
    c=d.get("candidate",{})
    require(c.get("cell_index")==1 and c.get("candidate_id")=="moonshine-compact" and c.get("tier")=="COMPACT","candidate identity drift")
    auth=d.get("authority",{})
    require(auth.get("canonical_authority_base")==AUTHORITY_BASE and auth.get("attempt_freeze_digest_sha256")==FREEZE_DIGEST,"authority binding drift")
    run=d.get("run",{})
    require(run.get("repository_revision")==CAPTURE_REVISION and run.get("github_run_id")==CAPTURE_RUN and run.get("github_run_attempt")==1,"capture run identity drift")
    ex=d.get("execution",{})
    rows=ex.get("records")
    require(isinstance(rows,list) and len(rows)==240,"record count drift")
    require(len({x.get("utterance_id") for x in rows})==240,"record identity duplication")
    require(ex.get("input_count")==240 and ex.get("decoded_count")==209 and ex.get("failure_count")==31,"capture counts drift")
    require(ex.get("decoded_count")+ex.get("failure_count")==240,"capture accounting drift")
    require(ex.get("all_frozen_input_hashes_reverified") is True and ex.get("reference_transcripts_loaded_by_decoder") is False,"input/reference guard drift")
    require(ex.get("accuracy_scoring_performed") is False and ex.get("comparative_ranking_present") is False and ex.get("performance_claim_present") is False,"claim boundary drift")
    for row in rows:
        require(row.get("status") in {"DECODED","FAILED"},"invalid row status")
        if row.get("status")=="FAILED": require(isinstance(row.get("failure"),dict),"failure details missing")
    guards=d.get("claim_guards",{})
    require(guards.get("human_developer_speech_accuracy_evidence")=="ABSENT" and guards.get("comparative_result_available") is False and guards.get("production_stt_selected") is False and guards.get("product_code_authorized") is False,"claim guards drift")
    payload=dict(d); recorded=payload.pop("evidence_payload_sha256",None)
    encoded=(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
    require(recorded==PAYLOAD_SHA256==hashlib.sha256(encoded).hexdigest(),"evidence payload digest mismatch")
    if require_git: require(blob(EVIDENCE)==EVIDENCE_BLOB,"evidence Git blob drift")

def verify_provenance(require_git: bool) -> None:
    p=load(PROVENANCE)
    require(p.get("task")==TASK,"provenance task drift")
    src=p.get("capture_source",{})
    require(src.get("source_revision")==CAPTURE_REVISION and src.get("source_parent")==AUTHORITY_BASE,"capture source ancestry drift")
    require(src.get("github_run_id")==CAPTURE_RUN and src.get("github_job_id")==CAPTURE_JOB and src.get("run_conclusion")=="success","capture disposition drift")
    require(src.get("decoder_git_blob_sha1")==DECODER_BLOB and src.get("decoder_sha256")==DECODER_SHA256,"source decoder identity drift")
    cap=p.get("captured_evidence",{})
    require(cap.get("sha256")==EVIDENCE_SHA256 and cap.get("payload_sha256")==PAYLOAD_SHA256,"provenance evidence binding drift")
    sem=p.get("preservation_semantics",{})
    require(sem.get("raw_outputs_preserved") is True and sem.get("failures_preserved") is True and sem.get("accuracy_scoring_performed") is False and sem.get("comparative_ranking_present") is False,"preservation semantics drift")
    require(sha(DECODER)==DECODER_SHA256,"decoder bytes drift")
    if require_git: require(blob(DECODER)==DECODER_BLOB,"decoder Git blob drift")

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--require-git",action="store_true"); args=ap.parse_args()
    try:
        verify_authority(); verify_evidence(args.require_git); verify_provenance(args.require_git)
    except (VerifyError,OSError,ValueError,subprocess.SubprocessError,json.JSONDecodeError) as e:
        print(f"B2R17_CAPTURE=FAIL: {e}"); return 1
    print("B2R17_CAPTURE=PASS")
    print(f"B2R17_CAPTURE_RUN={CAPTURE_RUN}")
    print("B2R17_DECODED=209")
    print("B2R17_FAILURES_PRESERVED=31")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    return 0
if __name__=="__main__": raise SystemExit(main())
