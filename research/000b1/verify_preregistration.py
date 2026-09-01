#!/usr/bin/env python3
"""Deterministic verifier for Wispral 000B1 preregistration evidence."""

from __future__ import annotations
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "000b1"
SHA = re.compile(r"^[0-9a-f]{64}$")
OFF = {False, None, "OFF", "NONE", "", 0}
WHISPER_MODEL_REVISION = "80da2d8bfee42b0e836fc3a9890373e5defc00a6"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(msg: str):
    raise AssertionError(msg)


def validator_module():
    path = HERE / "validate_attempt_manifest.py"
    spec = importlib.util.spec_from_file_location("b2_validator", path)
    if spec is None or spec.loader is None:
        fail("cannot load attempt validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_candidates():
    m = load(HERE / "qualified-candidates.json")
    if m["schema_version"] != "000b1-qualified-candidates-v1":
        fail("candidate schema drift")
    if m["canonical_wispral_base"] != "6b5696a6becc360948282712cc9339df9cb3a67c":
        fail("canonical base drift")
    if m["contract_version"] != "000b1-contract-v1":
        fail("contract drift")
    if m["primary_test_decoding_performed"] or m["comparative_ranking_present"]:
        fail("B1 cannot contain primary decoding or ranking")
    if m["qualification_smoke"]["status"] != "NOT_RUN_NOT_REQUIRED":
        fail("smoke disposition drift")
    expected_tiers = {
        "COMPACT": {"min_exclusive_bytes": 0, "max_inclusive_bytes": 167772160},
        "BALANCED": {"min_exclusive_bytes": 167772160, "max_inclusive_bytes": 536870912},
    }
    if m["tiers"] != expected_tiers:
        fail("tier definition drift")

    families = {f["family"]: f for f in m["families"]}
    if set(families) != {"moonshine", "whisper.cpp", "sherpa-onnx"}:
        fail("candidate family set drift")

    whisper = families["whisper.cpp"]
    source = whisper.get("model_source", {})
    if source.get("revision") != WHISPER_MODEL_REVISION:
        fail("whisper model source revision drift")
    expected_whisper_url = f"https://huggingface.co/ggerganov/whisper.cpp/resolve/{WHISPER_MODEL_REVISION}"
    if source.get("base_url") != expected_whisper_url:
        fail("whisper model source must be immutable")

    cells = set()
    pending = set()
    for family, data in families.items():
        if len(data["configurations"]) != 2:
            fail(f"{family} must have exactly two tier cells")
        for cfg in data["configurations"]:
            cell = (family, cfg["tier"])
            if cell in cells:
                fail(f"duplicate cell {cell}")
            cells.add(cell)
            arts = cfg["artifacts"]
            if sum(a["size_bytes"] for a in arts) != cfg["payload_total_bytes"]:
                fail(f"artifact byte sum mismatch for {cell}")
            b = expected_tiers[cfg["tier"]]
            if not (b["min_exclusive_bytes"] < cfg["payload_total_bytes"] <= b["max_inclusive_bytes"]):
                fail(f"tier bound violation for {cell}")
            for a in arts:
                value, status = a.get("sha256"), a.get("sha256_status")
                if value is None:
                    if status != "PENDING_B2_MATERIALIZATION":
                        fail(f"unlabeled pending SHA for {cell}:{a['path']}")
                    pending.add((family, a["path"]))
                elif not SHA.fullmatch(value) or status != "PINNED":
                    fail(f"invalid pinned SHA for {cell}:{a['path']}")
            for key, value in cfg["c0"].items():
                if key in {"repository_context", "context", "keyterms", "initial_prompt", "prompt_carryover", "hotwords", "grammar"} and value not in OFF:
                    fail(f"C0 bias enabled for {cell}:{key}")

    if len(cells) != 6:
        fail("expected six family/tier cells")
    if not any(f == "moonshine" for f, _ in pending):
        fail("Moonshine pending materialization gate disappeared")
    if ("sherpa-onnx", "tokens.txt") not in pending:
        fail("sherpa tokens.txt pending materialization gate disappeared")


def verify_schemas():
    for name in ("entity-annotation.schema.json", "qualified-candidates.schema.json", "attempt-manifest.schema.json"):
        s = load(HERE / "schemas" / name)
        if s.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or not s.get("$id"):
            fail(f"invalid schema header: {name}")


def verify_blocked_draft():
    v = validator_module()
    draft = load(HERE / "examples" / "draft-attempt-manifest.json")
    errors, blockers = v.validate(draft, False)
    if errors:
        fail(f"draft structural validation failed: {errors}")
    if not blockers:
        fail("draft must preserve B2 blockers")
    ready_errors, _ = v.validate(draft, True)
    if not ready_errors:
        fail("blocked draft unexpectedly passes --require-ready")


def verify_adversarial_review():
    text = (ROOT / "docs" / "research" / "stt" / "000b1-adversarial-review.md").read_text(encoding="utf-8").lower()
    for term in ("model switching", "test leakage", "normalization inflation", "hidden context bias", "synthetic-audio overclaim", "hosted-runner performance", "dropped failures", "post-hoc weighting"):
        if term not in text:
            fail(f"adversarial review missing {term}")
    if "b2_ready: no" not in text:
        fail("adversarial review must preserve B2_READY: NO")


def main() -> int:
    try:
        verify_schemas()
        verify_candidates()
        verify_blocked_draft()
        verify_adversarial_review()
    except (AssertionError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"VERIFY_000B1=FAIL: {exc}", file=sys.stderr)
        return 1
    print("VERIFY_000B1=PASS")
    print("PRIMARY_TEST_DECODING=NO")
    print("COMPARATIVE_RANKING=NO")
    print("B2_READY=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
