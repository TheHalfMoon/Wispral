#!/usr/bin/env python3
"""Fail-closed verifier for the ATTEMPT-003 B2R16 pre-primary freeze."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
MANIFEST = PUBLIC / "b2r16-attempt-003-manifest.json"
STATE = PUBLIC / "b2r16-preexecution-state.json"
READINESS = PUBLIC / "recovery-attempt-003-readiness.json"
BASE = "8132b25479643dc955eb4d022400a9e9b36b4261"
TASK_PATHS = {
 ".github/workflows/000b2-public-b2r16-freeze.yml",
 "research/000b2-public/b2r16-attempt-003-manifest.json",
 "research/000b2-public/b2r16-preexecution-state.json",
 "research/000b2-public/verify_b2r16.py",
}

class VerifyError(RuntimeError): pass

def require(v, m):
    if not v: raise VerifyError(m)

def load(path):
    v=json.loads(path.read_text(encoding="utf-8")); require(isinstance(v,dict), f"{path} must be object"); return v

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args): return subprocess.run(["git","-C",str(ROOT),*args],check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30).stdout.strip()
def blob(path): return git("rev-parse",f"HEAD:{path}")

def verify_binding(obj, path_key, sha_key, blob_key):
    p=ROOT/obj[path_key]; require(p.is_file(), f"missing {obj[path_key]}"); require(sha(p)==obj[sha_key], f"SHA drift: {obj[path_key]}"); require(blob(obj[path_key])==obj[blob_key], f"blob drift: {obj[path_key]}")

def main():
    m=load(MANIFEST); s=load(STATE); r=load(READINESS)
    require((m.get("schema_version"),m.get("task"),m.get("attempt_id"),m.get("phase"),m.get("frozen")) == ("000b2-public-attempt-003-manifest-v1","B2R16","000B2-PUBLIC-ATTEMPT-003","PRE_PRIMARY_FROZEN",True), "manifest identity/freeze drift")
    require(m.get("canonical_authority_base")==BASE, "authority base drift")
    c=m["candidate_set"]; require(c["candidate_ids"]==["moonshine-compact","moonshine-balanced","whispercpp-compact","whispercpp-balanced","sherpa-onnx-compact","sherpa-onnx-balanced"] and c["count"]==6, "candidate set drift")
    for x in (c["registry"],c["revalidation"],c["frozen_methodology"]): verify_binding(x,"path","sha256","git_blob_sha1")
    verify_binding(m["subset"],"path","sha256","git_blob_sha1"); require(m["subset"]["frozen_input_count"]==240, "subset count drift")
    for key in ("preprocessing","execution_environment"):
        x=m[key]; require(blob(x["rebind_path"])==x["rebind_git_blob_sha1"], f"{key} rebinding blob drift"); require(sha(ROOT/x["source_path"])==x["source_sha256"] and blob(x["source_path"])==x["source_git_blob_sha1"], f"{key} source drift")
    q=m["qualified_harness"]; require(sha(ROOT/q["path"])==q["sha256"] and blob(q["path"])==q["git_blob_sha1"], "B2R14 harness drift"); require(blob(q["qualification_path"])==q["qualification_git_blob_sha1"] and blob(q["verifier_path"])==q["verifier_git_blob_sha1"], "B2R14 qualification/verifier drift")
    score=m["scoring"]
    for p,sh,b in ((score["core_scorer_path"],score["core_scorer_sha256"],score["core_scorer_git_blob_sha1"]),(score["core_config_path"],score["core_config_sha256"],score["core_config_git_blob_sha1"]),(score["public_wer_adapter_path"],score["public_wer_adapter_sha256"],score["public_wer_adapter_git_blob_sha1"])): require(sha(ROOT/p)==sh and blob(p)==b, f"scoring identity drift: {p}")
    digest=m.pop("freeze_digest_sha256"); require(hashlib.sha256(json.dumps(m,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()==digest, "freeze digest mismatch")
    d=m["decoding_contract"]; require(d["candidate_decoding_started"] is False and d["primary_decoding_started"] is False and d["identical_frozen_audio_required_across_candidates"] is True, "decode freeze drift")
    require(s["attempt_id"]=="000B2-PUBLIC-ATTEMPT-003" and s["freeze_state"]["frozen"] is True and s["freeze_state"]["primary_decoding_started"] is False and s["freeze_state"]["scoring_started"] is False, "preexecution state drift")
    claims=m["claims"]; require(claims=={"human_developer_speech_accuracy_evidence":"ABSENT","comparative_result_available":False,"production_stt_selected":False,"product_code_authorized":False,"b2r17_authorized":False,"scoring_performed":False}, "claim guards drift")
    active=r.get("active_recovery_unit"); repl=r.get("replacement_attempt",{})
    if active=="B2R16":
        require(r.get("completed_recovery_tasks")==["B2R13","B2R14","B2R15"], "B2R16 predecessor ledger drift"); require(repl.get("frozen") is False and repl.get("primary_decode_entry_open") is False, "authority prematurely opened/froze attempt"); require(set(git("diff","--name-only",BASE,"HEAD").splitlines())==TASK_PATHS, "B2R16 scope drift")
    else:
        require(active=="B2R17" and r.get("completed_recovery_tasks")==["B2R13","B2R14","B2R15","B2R16"], "B2R16 not canonical"); require(repl.get("frozen") is True and repl.get("primary_decode_entry_open") is True, "post-reconciliation freeze authority drift")
    print("B2R16_ATTEMPT_003_FREEZE=PASS"); print(f"B2R16_FREEZE_DIGEST={digest}"); print("ATTEMPT_003_PRIMARY_DECODING_STARTED_AT_FREEZE=NO"); print("B2R17_AUTHORIZED=NO" if active=="B2R16" else "B2R17_AUTHORIZED=YES"); print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except (VerifyError,OSError,KeyError,json.JSONDecodeError,subprocess.SubprocessError) as exc: raise SystemExit(f"B2R16_ATTEMPT_003_FREEZE=FAIL: {exc}") from exc
