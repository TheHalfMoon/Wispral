#!/usr/bin/env python3
"""Verify the B2R02 corrected Moonshine streaming C0 harness fail-closed."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
HARNESS_PATH = PUBLIC / "moonshine_streaming_c0.py"
FROZEN_PATH = ROOT / "research" / "000b1" / "frozen-methodology.json"
CANDIDATES_PATH = ROOT / "research" / "000b1" / "qualified-candidates.json"
REVALIDATION_PATH = PUBLIC / "candidate-revalidation.json"
RECOVERY_READINESS_PATH = PUBLIC / "recovery-readiness.json"
QUALIFICATION_PATH = PUBLIC / "b2r02-moonshine-streaming-qualification.json"

TASK = "B2R02"
EXPECTED_AUTHORITY_MAIN = "b6425789ebc02f3e270a7ba53f463aad0f8c451a"
EXPECTED_UPSTREAM_REPOSITORY = "moonshine-ai/moonshine"
EXPECTED_UPSTREAM_REVISION = "234f60faa0eb388b01cdf7e60aca232af37aefda"
EXPECTED_RUNTIME_VERSION = "0.1.5"
EXPECTED_MODEL_ASSET_REVISION = "quantized_26_08_21"
EXPECTED_MAIN_REVALIDATION_RUN_ID = 33984268736
EXPECTED_SOURCE_BLOBS = {
    "language-bindings/python/src/moonshine_voice/transcriber.py": "7193028a24c47b2914c552e2edfd143212899f4f",
    "core/transcriber.h": "58e1c30c2d3003c3a785583bad49e6bf646bd3bd",
    "core/moonshine-c-api.cpp": "b5effa3a8bb5aa6e735961d777ea6e3109eb784c",
    "docs/api/options.md": "1691d525ee198c2d86b8e895a9dae1ad915234c2",
}
EXPECTED_OPTIONS = {
    "transcription_interval": 0.5,
    "vad_threshold": 0.0,
    "vad_window_duration": 0.5,
    "vad_hop_size": 512,
    "vad_look_behind_sample_count": 8192,
    "vad_max_segment_duration": 15,
    "max_tokens_per_second": 6.5,
    "use_speculative_decoding": True,
    "decode_incomplete_lines": True,
    "identify_speakers": False,
    "return_audio_data": True,
    "word_timestamps": False,
    "keyterm_boost": 2.0,
    "context_max_terms": 200,
}


class VerifyError(ValueError):
    """Raised when B2R02 qualification evidence or code drifts."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_harness() -> Any:
    spec = importlib.util.spec_from_file_location("wispral_b2r02_moonshine_streaming_c0", HARNESS_PATH)
    require(spec is not None and spec.loader is not None, "unable to load B2R02 harness")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeStream:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def start(self) -> None:
        self.calls.append(("start", None))

    def add_audio(self, audio: Any, sample_rate: int) -> None:
        self.calls.append(("add_audio", (tuple(audio), sample_rate)))

    def stop(self) -> dict[str, Any]:
        self.calls.append(("stop", None))
        return {"transcript_text_retained": False}

    def close(self) -> None:
        self.calls.append(("close", None))


class FakeTranscriber:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.keyterms: Any = "UNSET"
        self.context: Any = "UNSET"
        self.stream_update_interval: Any = None
        self.stream = FakeStream()

    def set_keyterms(self, value: Any) -> None:
        self.keyterms = value

    def set_context(self, value: Any) -> None:
        self.context = value

    def create_stream(self, *, update_interval: float) -> FakeStream:
        self.stream_update_interval = update_interval
        return self.stream


def verify_canonical_authority(harness: Any) -> None:
    recovery = load_json(RECOVERY_READINESS_PATH)
    require(recovery.get("completed_recovery_tasks") == ["B2R01"], "B2R02 predecessor ledger drift")
    require(recovery.get("active_recovery_unit") == TASK, "B2R02 is not the sole active recovery unit")
    replacement = recovery.get("replacement_attempt")
    require(isinstance(replacement, dict), "replacement attempt authority missing")
    require(replacement.get("attempt_id") == "000B2-PUBLIC-ATTEMPT-002", "replacement attempt identity drift")
    require(replacement.get("frozen") is False, "ATTEMPT-002 must remain unfrozen during B2R02")
    require(replacement.get("primary_decode_entry_open") is False, "ATTEMPT-002 primary decode opened before B2R04")

    frozen = load_json(FROZEN_PATH)
    preprocessing = frozen.get("preprocessing")
    common = frozen.get("common_c0")
    moonshine = frozen.get("c0_by_family", {}).get("moonshine")
    require(isinstance(preprocessing, dict) and isinstance(common, dict) and isinstance(moonshine, dict), "frozen C0 blocks missing")
    require(preprocessing.get("sample_rate_hz") == harness.SAMPLE_RATE_HZ == 16000, "sample-rate freeze drift")
    require(preprocessing.get("feed_chunk_ms") == harness.FEED_CHUNK_MS == 500, "feed-duration freeze drift")
    require(preprocessing.get("feed_chunk_samples") == harness.FEED_CHUNK_SAMPLES == 8000, "feed-sample freeze drift")
    require(preprocessing.get("finalization_zero_pad_ms") == harness.FINAL_ZERO_PAD_MS == 660, "zero-pad duration freeze drift")
    require(preprocessing.get("finalization_zero_pad_samples") == harness.FINAL_ZERO_PAD_SAMPLES == 10560, "zero-pad sample freeze drift")
    require(common.get("repository_context") == "OFF" and common.get("test_specific_context") == "OFF", "context guard drift")
    require(moonshine.get("runtime_revision") == EXPECTED_UPSTREAM_REVISION, "Moonshine runtime revision drift")
    require(moonshine.get("transcription_interval_seconds") == 0.5, "transcription interval drift")
    require(moonshine.get("vad_threshold") == 0.0, "VAD threshold drift")
    require(moonshine.get("keyterms") == "OFF" and moonshine.get("context") == "OFF", "Moonshine bias guard drift")
    require(moonshine.get("max_primary_utterance_seconds") == 12, "primary utterance bound drift")
    require(harness.MOONSHINE_C0_OPTIONS == EXPECTED_OPTIONS, "harness C0 options drift")

    registry = load_json(CANDIDATES_PATH)
    moonshine_family = next((row for row in registry.get("families", []) if row.get("family") == "moonshine"), None)
    require(isinstance(moonshine_family, dict), "Moonshine candidate family missing")
    runtime = moonshine_family.get("runtime")
    model_source = moonshine_family.get("model_source")
    require(isinstance(runtime, dict) and isinstance(model_source, dict), "Moonshine runtime/model registry missing")
    require(runtime.get("repository") == EXPECTED_UPSTREAM_REPOSITORY, "Moonshine repository pin drift")
    require(runtime.get("revision") == EXPECTED_UPSTREAM_REVISION, "Moonshine runtime pin drift")
    require(runtime.get("release") == "v0.1.5", "Moonshine release pin drift")
    require(model_source.get("asset_revision") == EXPECTED_MODEL_ASSET_REVISION, "Moonshine model asset revision drift")
    ids = [row.get("id") for row in moonshine_family.get("configurations", [])]
    require(ids == ["moonshine-compact", "moonshine-balanced"], "Moonshine candidate ordering/membership drift")

    revalidation = load_json(REVALIDATION_PATH)
    live_contract = revalidation.get("live_revalidation_contract")
    guards = revalidation.get("guards")
    runtime_pin = revalidation.get("runtime_pins", {}).get("moonshine")
    require(isinstance(live_contract, dict) and isinstance(guards, dict) and isinstance(runtime_pin, dict), "candidate revalidation contract missing")
    require(live_contract.get("exact_runtime_release_and_revision_resolution_required") is True, "runtime live-revalidation gate weakened")
    require(live_contract.get("all_canonical_artifact_bytes_must_match_recorded_size_and_sha256") is True, "artifact live-revalidation gate weakened")
    require(runtime_pin.get("revision") == EXPECTED_UPSTREAM_REVISION, "revalidated runtime revision drift")
    require(runtime_pin.get("model_asset_revision") == EXPECTED_MODEL_ASSET_REVISION, "revalidated model asset revision drift")
    require(guards.get("primary_decoding_started") is False, "candidate revalidation evidence indicates primary decode")


def verify_structural_harness(harness: Any) -> None:
    transcriber = harness.create_transcriber(FakeTranscriber, model_path="synthetic-model-root", model_arch="STREAMING")
    require(transcriber.kwargs.get("update_interval") == 0.5, "Python streaming convenience interval drift")
    require(transcriber.kwargs.get("options") == EXPECTED_OPTIONS, "Transcriber options not frozen exactly")

    # Deterministic non-primary material: four exact 500 ms chunks. Values are
    # deliberately synthetic and no transcript text is inspected or retained.
    audio = tuple(((index % 17) - 8) / 64.0 for index in range(32_000))
    result, trace = harness.transcribe_streaming_c0(transcriber, audio)
    require(result == {"transcript_text_retained": False}, "structural fake result drift")
    require(transcriber.keyterms == [], "keyterms were not explicitly disabled")
    require(transcriber.context is None, "repository/test context was not explicitly disabled")
    require(transcriber.stream_update_interval == 0.5, "stream update interval drift")
    require(trace.speech_samples == 32_000, "synthetic speech-sample count drift")
    require(trace.speech_chunk_samples == (8000, 8000, 8000, 8000), "500 ms feed schedule drift")
    require(trace.zero_pad_samples == 10_560, "660 ms zero suffix drift")
    require(trace.sample_rate_hz == 16_000 and trace.stream_started and trace.stream_stopped, "stream lifecycle trace drift")

    calls = transcriber.stream.calls
    require([name for name, _ in calls] == ["start", "add_audio", "add_audio", "add_audio", "add_audio", "add_audio", "stop", "close"], "stream call order drift")
    add_calls = [payload for name, payload in calls if name == "add_audio"]
    require([len(samples) for samples, _ in add_calls] == [8000, 8000, 8000, 8000, 10560], "stream feed sample-count trace drift")
    require(all(rate == 16_000 for _, rate in add_calls), "stream feed sample-rate drift")
    require(all(value == 0.0 for value in add_calls[-1][0]), "final suffix is not universal zero padding")

    # Prove a non-multiple final speech chunk is preserved rather than padded or dropped.
    short = tuple(0.125 for _ in range(8_123))
    transcriber2 = harness.create_transcriber(FakeTranscriber, model_path="synthetic-model-root", model_arch="STREAMING")
    _, trace2 = harness.transcribe_streaming_c0(transcriber2, short)
    require(trace2.speech_chunk_samples == (8000, 123), "final speech remainder handling drift")
    add2 = [payload for name, payload in transcriber2.stream.calls if name == "add_audio"]
    require([len(samples) for samples, _ in add2] == [8000, 123, 10560], "final remainder/zero suffix call schedule drift")


def git_output(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(source), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def verify_pinned_upstream(source: Path) -> None:
    require(source.is_dir(), f"Moonshine source directory missing: {source}")
    require(git_output(source, "rev-parse", "HEAD") == EXPECTED_UPSTREAM_REVISION, "Moonshine source checkout revision drift")
    require(subprocess.run(["git", "-C", str(source), "diff", "--quiet", "HEAD", "--"], check=False).returncode == 0, "Moonshine source checkout is dirty")
    for path, expected_blob in EXPECTED_SOURCE_BLOBS.items():
        require(git_output(source, "rev-parse", f"HEAD:{path}") == expected_blob, f"pinned Moonshine source blob drift: {path}")

    py = (source / "language-bindings/python/src/moonshine_voice/transcriber.py").read_text(encoding="utf-8")
    header = (source / "core/transcriber.h").read_text(encoding="utf-8")
    capi = (source / "core/moonshine-c-api.cpp").read_text(encoding="utf-8")
    options = (source / "docs/api/options.md").read_text(encoding="utf-8")

    for token in ("def create_stream(", "def start(self):", "def add_audio(self, audio_data", "def stop(self):"):
        require(token in py, f"pinned Python streaming API proof missing: {token}")
    require("self.get_default_stream().add_audio(audio_data, sample_rate)" in py, "Python default-stream add_audio route drift")
    require("float transcription_interval = 0.5f;" in header, "pinned transcription_interval default proof missing")
    require("float vad_threshold = 0.5f;" in header, "pinned vad_threshold default proof missing")
    require('option_name == "transcription_interval"' in capi, "transcription_interval C option parser proof missing")
    require('option.first == "vad_threshold"' in capi, "vad_threshold C option parser proof missing")
    require("| `transcription_interval` | `0.5` |" in options, "pinned options documentation transcription interval drift")
    require("| `vad_threshold` | `0.5` |" in options, "pinned options documentation VAD default drift")
    require("`0` disables VAD" in options, "pinned options documentation VAD-zero semantics missing")


def verify_qualification_evidence() -> None:
    evidence = load_json(QUALIFICATION_PATH)
    require(evidence.get("schema_version") == "000b2-public-b2r02-moonshine-streaming-qualification-v1", "B2R02 qualification schema drift")
    require(evidence.get("task") == TASK, "B2R02 qualification task drift")
    require(evidence.get("authority_main") == EXPECTED_AUTHORITY_MAIN, "B2R02 authority main drift")
    upstream = evidence.get("pinned_upstream_source")
    require(isinstance(upstream, dict), "B2R02 upstream source evidence missing")
    require(upstream.get("repository") == EXPECTED_UPSTREAM_REPOSITORY, "B2R02 upstream repository drift")
    require(upstream.get("revision") == EXPECTED_UPSTREAM_REVISION, "B2R02 upstream revision drift")
    require(upstream.get("git_blobs") == EXPECTED_SOURCE_BLOBS, "B2R02 upstream source blob ledger drift")
    non_primary = evidence.get("non_primary_qualification")
    require(isinstance(non_primary, dict), "B2R02 non-primary qualification missing")
    require(non_primary.get("synthetic_non_speech") is True, "B2R02 qualification must remain non-primary synthetic")
    require(non_primary.get("speech_samples") == 32000, "B2R02 synthetic sample count drift")
    require(non_primary.get("speech_chunk_samples") == [8000, 8000, 8000, 8000], "B2R02 qualification feed trace drift")
    require(non_primary.get("final_zero_pad_samples") == 10560, "B2R02 qualification zero suffix drift")
    require(non_primary.get("transcript_text_retained") is False, "B2R02 qualification retained transcript text")
    require(non_primary.get("accuracy_scoring_performed") is False, "B2R02 qualification performed accuracy scoring")
    identities = evidence.get("runtime_model_identity_basis")
    require(isinstance(identities, dict), "B2R02 runtime/model identity basis missing")
    require(identities.get("runtime_revision") == EXPECTED_UPSTREAM_REVISION, "B2R02 runtime identity drift")
    require(identities.get("runtime_distribution_version") == EXPECTED_RUNTIME_VERSION, "B2R02 runtime version drift")
    require(identities.get("model_asset_revision") == EXPECTED_MODEL_ASSET_REVISION, "B2R02 model identity drift")
    require(identities.get("latest_canonical_main_live_revalidation_run_id") == EXPECTED_MAIN_REVALIDATION_RUN_ID, "B2R02 live-revalidation run drift")
    guards = evidence.get("claim_guards")
    require(isinstance(guards, dict), "B2R02 claim guards missing")
    require(guards == {
        "primary_decode_performed": False,
        "reference_transcripts_loaded": False,
        "accuracy_scoring_performed": False,
        "comparative_ranking_present": False,
        "candidate_superiority_claim_present": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "production_stt_selected": False,
        "product_code_authorized": False,
        "b2r03_authorized_by_this_artifact": False,
        "attempt_002_primary_decode_authorized": False,
    }, "B2R02 claim-guard drift")
    require(evidence.get("harness_sha256") == sha256_file(HARNESS_PATH), "B2R02 harness digest drift")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--moonshine-source", type=Path, help="Exact pinned moonshine-ai/moonshine checkout for upstream-source qualification")
    parser.add_argument("--require-upstream", action="store_true", help="Fail unless --moonshine-source is supplied")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    harness = load_harness()
    verify_canonical_authority(harness)
    verify_structural_harness(harness)
    verify_qualification_evidence()
    if args.moonshine_source is not None:
        verify_pinned_upstream(args.moonshine_source)
    else:
        require(not args.require_upstream, "exact pinned upstream source checkout required")
    print("B2R02_MOONSHINE_STREAMING_C0=PASS")
    print("B2R02_NON_PRIMARY_STRUCTURAL_QUALIFICATION=PASS")
    print(f"B2R02_PINNED_UPSTREAM_SOURCE={'PASS' if args.moonshine_source is not None else 'NOT_RUN'}")
    print("ATTEMPT_002_PRIMARY_DECODE_AUTHORIZED=NO")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")


if __name__ == "__main__":
    main()
