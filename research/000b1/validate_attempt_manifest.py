#!/usr/bin/env python3
"""Fail-closed validator for a Wispral 000B2 attempt manifest."""

from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{64}$")
OFF = {False, None, "OFF", "NONE", "", 0}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(manifest: dict) -> str:
    obj = dict(manifest)
    obj["freeze_digest_sha256"] = None
    raw = (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def sha(value) -> bool:
    return isinstance(value, str) and bool(SHA.fullmatch(value))


def validate(m: dict, require_ready: bool = False):
    errors, blockers = [], []
    required = {
        "schema_version", "attempt_id", "canonical_wispral_revision",
        "b1_contract_version", "frozen", "freeze_digest_sha256",
        "primary_test_decoding_started", "candidates", "corpus",
        "preprocessing", "scorer", "execution_environment", "claims",
    }
    missing = sorted(required - set(m))
    if missing:
        return [f"missing fields: {', '.join(missing)}"], blockers
    if m["schema_version"] != "000b2-attempt-manifest-v1":
        errors.append("schema_version drift")
    if m["b1_contract_version"] != "000b1-contract-v1":
        errors.append("b1_contract_version drift")
    if not re.fullmatch(r"[0-9a-f]{40}", str(m["canonical_wispral_revision"])):
        errors.append("invalid canonical_wispral_revision")
    if not isinstance(m["candidates"], list) or not m["candidates"]:
        errors.append("candidates must be non-empty")
        return errors, blockers

    ids = set()
    for i, c in enumerate(m["candidates"]):
        p = f"candidate[{i}]"
        cid, tier = c.get("candidate_id"), c.get("tier")
        if not cid or cid in ids:
            errors.append(f"{p} candidate_id missing/duplicate")
        ids.add(cid)
        if tier not in {"COMPACT", "BALANCED"}:
            errors.append(f"{p} invalid tier")
        arts = c.get("artifacts")
        if not isinstance(arts, list) or not arts:
            errors.append(f"{p} artifacts missing")
        else:
            for j, a in enumerate(arts):
                ap = f"{p}.artifacts[{j}]"
                if not a.get("path") or not isinstance(a.get("size_bytes"), int) or a["size_bytes"] <= 0:
                    errors.append(f"{ap} invalid identity/size")
                if a.get("sha256") is not None and not sha(a["sha256"]):
                    errors.append(f"{ap} malformed SHA-256")
                if m["frozen"] and not sha(a.get("sha256")):
                    blockers.append(f"{ap} SHA-256 not pinned")
        for key, value in c.get("c0", {}).items():
            if key in {"repository_context", "context", "keyterms", "initial_prompt",
                       "prompt_carryover", "hotwords", "grammar"} and value not in OFF:
                blockers.append(f"{p}.c0.{key} must be OFF")

    corpus = m["corpus"]
    if corpus.get("synthetic_primary_ranking") is not False:
        errors.append("synthetic_primary_ranking must be false")
    if corpus.get("authority_status") != "AUTHORIZED":
        blockers.append("human developer-speech authority not AUTHORIZED")
    if not sha(corpus.get("consent_records_sha256")):
        blockers.append("consent_records_sha256 not pinned")
    if not sha(corpus.get("primary_test_manifest_sha256")):
        blockers.append("primary_test_manifest_sha256 not pinned")

    prep = m["preprocessing"]
    fixed = {"sample_rate_hz": 16000, "channels": 1, "sample_format": "PCM_S16LE",
             "denoising": "NONE", "semantic_silence_trim": "NONE"}
    for key, expected in fixed.items():
        if prep.get(key) != expected:
            errors.append(f"preprocessing.{key} must equal {expected}")
    if not prep.get("revision") or not sha(prep.get("config_sha256")):
        blockers.append("preprocessing revision/config not frozen")

    scorer = m["scorer"]
    if not scorer.get("revision") or not sha(scorer.get("config_sha256")):
        blockers.append("scorer revision/config not frozen")

    env, claims = m["execution_environment"], m["claims"]
    if not env.get("environment_id") or not sha(env.get("hardware_fingerprint_sha256")):
        blockers.append("execution environment not frozen")
    if claims.get("comparative_performance_authorized") and env.get("performance_mode") != "CONTROLLED":
        errors.append("comparative performance requires CONTROLLED environment")
    if claims.get("human_developer_speech_ranking_authorized") and corpus.get("authority_status") != "AUTHORIZED":
        errors.append("human ranking authorized without corpus authority")

    if m["frozen"]:
        if not sha(m.get("freeze_digest_sha256")):
            blockers.append("freeze_digest_sha256 not pinned")
        elif m["freeze_digest_sha256"] != digest(m):
            errors.append("freeze_digest_sha256 mismatch")
    elif m.get("freeze_digest_sha256") is not None:
        errors.append("unfrozen manifest must use null freeze_digest_sha256")

    if require_ready:
        if m.get("primary_test_decoding_started"):
            errors.append("primary test decoding already started")
        if not m["frozen"]:
            blockers.append("manifest not frozen")
        if not claims.get("human_developer_speech_ranking_authorized"):
            blockers.append("human ranking not authorized")
        errors += [f"BLOCKER: {b}" for b in blockers]
    return errors, blockers


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--require-ready", action="store_true")
    ap.add_argument("--print-freeze-digest", action="store_true")
    a = ap.parse_args()
    m = load(a.manifest)
    if a.print_freeze_digest:
        print(digest(m)); return 0
    errors, blockers = validate(m, a.require_ready)
    if errors:
        for e in errors: print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print("STRUCTURE=PASS")
    print(f"B2_READY={'NO' if blockers else 'YES'}")
    for b in blockers: print(f"BLOCKER={b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
