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
CANONICAL_BASE = "6b5696a6becc360948282712cc9339df9cb3a67c"


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
    if m["canonical_wispral_base"] != CANONICAL_BASE:
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


def verify_frozen_methodology():
    m = load(HERE / "frozen-methodology.json")
    if m.get("schema_version") != "000b1-frozen-methodology-v1":
        fail("frozen methodology schema drift")
    if m.get("contract_version") != "000b1-contract-v1" or m.get("canonical_wispral_base") != CANONICAL_BASE:
        fail("frozen methodology authority drift")

    s = m["speaker_design"]
    if s["total_human_speakers"] != 20 or s["speakers_by_split"] != {"development": 4, "qualification": 4, "test": 12}:
        fail("speaker design drift")
    if not s["speaker_disjoint_splits"]:
        fail("speaker splits must be disjoint")
    if s["utterances_per_speaker"] != {"developer_entity": 24, "general_collateral": 12}:
        fail("utterance design drift")
    if s["planned_total_utterances"] != 720 or s["planned_test_utterances"] != {"developer_entity": 288, "general_collateral": 144, "total": 432}:
        fail("planned corpus arithmetic drift")
    if s["max_primary_utterance_seconds"] != 12 or s["minimum_test_microphone_environment_profiles"] < 4:
        fail("recording envelope drift")

    p = m["preprocessing"]
    expected_pre = {
        "tool": "FFmpeg", "version": "9.0.1", "source_tag": "n9.0.1",
        "tag_object": "501bb49457b9dfb25d6a208832e0a6e6cd53108d",
        "source_commit": "bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa",
        "canonical_format": "PCM_WAV", "sample_rate_hz": 16000,
        "channels": 1, "sample_format": "PCM_S16LE", "denoising": "NONE",
        "loudness_normalization": "NONE", "semantic_silence_trim": "NONE",
        "feed_chunk_ms": 500, "feed_chunk_samples": 8000,
        "finalization_zero_pad_ms": 660, "finalization_zero_pad_samples": 10560,
    }
    for key, value in expected_pre.items():
        if p.get(key) != value:
            fail(f"preprocessing.{key} drift")
    if not p.get("attempt_binary_sha256_required") or not p.get("attempt_version_output_sha256_required") or not p.get("canonical_output_sha256_required"):
        fail("preprocessing integrity requirements weakened")
    if p.get("command_template") != "ffmpeg -nostdin -hide_banner -loglevel error -i INPUT -map_metadata -1 -vn -sn -dn -ac 1 -ar 16000 -c:a pcm_s16le OUTPUT.wav":
        fail("preprocessing command drift")

    common = m["common_c0"]
    if common != {
        "language": "en", "device": "CPU_ONLY", "repository_context": "OFF",
        "test_specific_context": "OFF", "post_decode_entity_correction": "OFF",
        "external_language_model": "OFF", "candidate_specific_audio_transform": "OFF",
        "feed_chunk_ms": 500, "finalization_zero_pad_ms": 660,
    }:
        fail("common C0 drift")

    fam = m["c0_by_family"]
    if set(fam) != {"moonshine", "whisper.cpp", "sherpa-onnx"}:
        fail("C0 family set drift")
    moon = fam["moonshine"]
    if moon["runtime_revision"] != "234f60faa0eb388b01cdf7e60aca232af37aefda" or moon["keyterms"] != "OFF" or moon["context"] != "OFF":
        fail("Moonshine C0 authority/bias drift")
    if moon["ort_providers"] != "UNSET_CPU_DEFAULT" or moon["vad_threshold"] != 0.0 or moon["transcription_interval_seconds"] != 0.5 or moon["word_timestamps"] is not False:
        fail("Moonshine C0 execution drift")

    whisper = fam["whisper.cpp"]
    if whisper["runtime_revision"] != "371b5a7561823ab2bb32142d2751e35e7534727b":
        fail("whisper.cpp C0 runtime drift")
    expected_whisper = {
        "threads": 4, "step_ms": 500, "length_ms": 5000, "keep_ms": 200,
        "max_tokens": 0, "audio_ctx": 0, "beam_size": -1, "sampling": "GREEDY",
        "temperature_fallback": "OFF", "no_fallback": True, "language": "en",
        "translate": False, "keep_context": False, "initial_prompt": "OFF",
        "prompt_carryover": "OFF", "vad": "OFF_BY_NONZERO_STEP",
        "timestamps": "OFF_BY_NON_VAD_STREAM_PATH", "single_segment": True,
        "use_gpu": False, "flash_attention": False,
    }
    for key, value in expected_whisper.items():
        if whisper.get(key) != value:
            fail(f"whisper.cpp C0 {key} drift")

    sherpa = fam["sherpa-onnx"]
    if sherpa["runtime_revision"] != "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e":
        fail("sherpa-onnx C0 runtime drift")
    expected_sherpa = {
        "threads": 4, "provider": "cpu", "sample_rate_hz": 16000,
        "feature_dim": 80, "decoding_method": "greedy_search", "max_active_paths": 4,
        "lm": "OFF", "lodr_fst": "OFF", "hotwords_file": "OFF",
        "modeling_unit": "OFF", "bpe_vocab": "OFF", "blank_penalty": 0.0,
        "endpoint_detection": "OFF_PRESEGMENTED_INPUT_FINISHED",
    }
    for key, value in expected_sherpa.items():
        if sherpa.get(key) != value:
            fail(f"sherpa-onnx C0 {key} drift")


def verify_schemas():
    for name in (
        "entity-annotation.schema.json", "qualified-candidates.schema.json",
        "attempt-manifest.schema.json", "frozen-methodology.schema.json",
    ):
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
        verify_frozen_methodology()
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
