#!/usr/bin/env python3
"""Run bounded, synthetic, non-primary operational smoke for B2 candidates.

The smoke is deliberately incapable of producing benchmark claims. It verifies
exact candidate artifacts, loads the pinned runtime path, executes one synthetic
stream/decode, and stores only structural outcome metadata. Transcript text is
never written to evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
B1 = ROOT / "research" / "000b1"
HERE = ROOT / "research" / "000b2-entry"
REGISTRY = B1 / "qualified-candidates.json"
MATERIALIZED = HERE / "materialized-artifacts.json"
AMENDMENT = HERE / "artifact-size-amendment.json"

SMOKE_SCHEMA = "000b2-operational-smoke-cell-v1"
SMOKE_GENERATOR = "wispral-deterministic-multitone-v1"
SAMPLE_RATE = 16000
SPEECH_SAMPLES = 32000
FINAL_ZERO_SAMPLES = 10560


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def candidate_record(candidate_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = load(REGISTRY)
    for family in registry["families"]:
        for config in family["configurations"]:
            if config["id"] == candidate_id:
                return family, config
    raise RuntimeError(f"unknown candidate: {candidate_id}")


def amendment_sizes() -> dict[tuple[str, str], int]:
    amendment = load(AMENDMENT)
    return {
        (item["candidate_id"], item["path"]): item["corrected_b2_size_bytes"]
        for item in amendment["corrections"]
    }


def materialized_rows() -> dict[tuple[str, str], dict[str, Any]]:
    payload = load(MATERIALIZED)
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate_id, artifacts in payload["artifacts"].items():
        for path, row in artifacts.items():
            rows[(candidate_id, path)] = row
    return rows


def expected_artifacts(candidate_id: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    amended = amendment_sizes()
    materialized = materialized_rows()
    result: list[dict[str, Any]] = []
    for artifact in config["artifacts"]:
        path = artifact["path"]
        key = (candidate_id, path)
        size = amended.get(key, artifact["size_bytes"])
        digest = artifact.get("sha256")
        if digest is None:
            row = materialized.get(key)
            if row is None:
                raise RuntimeError(f"missing materialized evidence for {candidate_id}:{path}")
            digest = row["sha256"]
            if row["size_bytes"] != size:
                raise RuntimeError(f"materialized size drift for {candidate_id}:{path}")
        result.append({"path": path, "size_bytes": size, "sha256": digest})
    return result


def find_artifact(root: Path, relative: str) -> Path:
    direct = root / relative
    if direct.is_file():
        return direct
    matches = [p for p in root.rglob(Path(relative).name) if p.is_file()]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one artifact named {relative!r} below {root}, found {len(matches)}"
        )
    return matches[0]


def verify_artifacts(candidate_id: str, config: dict[str, Any], model_root: Path) -> list[dict[str, Any]]:
    rows = []
    for expected in expected_artifacts(candidate_id, config):
        observed_path = find_artifact(model_root, expected["path"])
        observed_size = observed_path.stat().st_size
        observed_sha = sha256_file(observed_path)
        if observed_size != expected["size_bytes"]:
            raise RuntimeError(
                f"artifact size mismatch for {candidate_id}:{expected['path']}: "
                f"expected {expected['size_bytes']}, observed {observed_size}"
            )
        if observed_sha != expected["sha256"]:
            raise RuntimeError(f"artifact SHA-256 mismatch for {candidate_id}:{expected['path']}")
        rows.append(
            {
                "path": expected["path"],
                "size_bytes": observed_size,
                "sha256": observed_sha,
            }
        )
    return rows


def generate_smoke_wav(path: Path) -> dict[str, Any]:
    """Generate deterministic non-speech PCM with multiple tones and silences."""
    samples: list[int] = []
    for i in range(SPEECH_SAMPLES):
        # Deterministic multi-tone signal, intentionally not speech or TTS.
        t = i / SAMPLE_RATE
        gate = 0.0 if (i // 4000) % 4 == 3 else 1.0
        value = gate * (
            0.22 * math.sin(2.0 * math.pi * 233.0 * t)
            + 0.11 * math.sin(2.0 * math.pi * 509.0 * t)
            + 0.05 * math.sin(2.0 * math.pi * 997.0 * t)
        )
        value = max(-0.95, min(0.95, value))
        samples.append(int(round(value * 32767.0)))

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return {
        "generator": SMOKE_GENERATOR,
        "synthetic_non_speech": True,
        "sample_rate_hz": SAMPLE_RATE,
        "channels": 1,
        "sample_format": "PCM_S16LE",
        "samples": len(samples),
        "sha256": sha256_file(path),
    }


def read_wav_float(path: Path) -> list[float]:
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != SAMPLE_RATE:
            raise RuntimeError("smoke WAV drifted from canonical mono/16-bit/16-kHz shape")
        raw = wav.readframes(wav.getnframes())
    values = struct.unpack(f"<{len(raw) // 2}h", raw)
    return [sample / 32768.0 for sample in values]


def base_report(candidate_id: str, family: dict[str, Any], config: dict[str, Any], wav: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SMOKE_SCHEMA,
        "purpose": "B2_ENTRY_OPERATIONAL_QUALIFICATION_NON_PRIMARY",
        "candidate_id": candidate_id,
        "family": family["family"],
        "tier": config["tier"],
        "runtime_revision": family["runtime"]["revision"],
        "synthetic_input": wav,
        "primary_test_decoding_performed": False,
        "human_speech_used": False,
        "comparative_ranking_present": False,
        "accuracy_scoring_performed": False,
        "performance_claim_present": False,
        "transcript_text_retained": False,
        "repository_context_used": False,
        "status": "SMOKE_PASS",
    }


def run_moonshine(candidate_id: str, work_dir: Path, wav_path: Path) -> dict[str, Any]:
    family, config = candidate_record(candidate_id)
    if family["family"] != "moonshine":
        raise RuntimeError("moonshine subcommand requires a Moonshine candidate")
    version = importlib.metadata.version("moonshine-voice")
    if version != "0.1.5":
        raise RuntimeError(f"moonshine-voice version drift: {version}")

    from moonshine_voice import ModelArch, Transcriber
    from moonshine_voice.download import download_model_from_info, find_model_info

    arch_by_id = {
        "moonshine-compact": ModelArch.SMALL_STREAMING,
        "moonshine-balanced": ModelArch.MEDIUM_STREAMING,
    }
    arch = arch_by_id[candidate_id]
    model_info = find_model_info("en", arch)
    model_path, observed_arch = download_model_from_info(
        model_info,
        cache_root=work_dir / "moonshine-cache",
        include_word_timestamps=False,
    )
    if observed_arch != arch:
        raise RuntimeError("Moonshine architecture drift")
    artifacts = verify_artifacts(candidate_id, config, Path(model_path))

    audio = read_wav_float(wav_path)
    with Transcriber(model_path=model_path, model_arch=arch, update_interval=0.5) as transcriber:
        # Explicitly turn the two repository-bias surfaces off before smoke.
        transcriber.set_keyterms([])
        transcriber.set_context(None)
        stream = transcriber.create_stream(update_interval=0.5)
        try:
            stream.start()
            for offset in range(0, len(audio), 8000):
                stream.add_audio(audio[offset : offset + 8000], SAMPLE_RATE)
            stream.add_audio([0.0] * FINAL_ZERO_SAMPLES, SAMPLE_RATE)
            result = stream.stop()
            line_count = len(result.lines) if result is not None else 0
        finally:
            stream.close()

    report = base_report(candidate_id, family, config, generate_smoke_wav(wav_path))
    report.update(
        {
            "runtime": {
                "distribution": "moonshine-voice",
                "version": version,
                "model_arch": int(arch),
                "model_asset_root": Path(model_path).name,
            },
            "artifacts": artifacts,
            "execution": {
                "stream_api_executed": True,
                "decode_completed": True,
                "result_line_count_observed": line_count,
            },
        }
    )
    return report


def run_sherpa(candidate_id: str, model_root: Path, wav_path: Path) -> dict[str, Any]:
    family, config = candidate_record(candidate_id)
    if family["family"] != "sherpa-onnx":
        raise RuntimeError("sherpa subcommand requires a sherpa-onnx candidate")
    version = importlib.metadata.version("sherpa-onnx")
    if version != "1.13.7":
        raise RuntimeError(f"sherpa-onnx version drift: {version}")

    import numpy as np
    import sherpa_onnx

    artifacts = verify_artifacts(candidate_id, config, model_root)
    suffix = ".int8.onnx" if candidate_id.endswith("compact") else ".onnx"
    encoder = find_artifact(model_root, f"encoder-epoch-99-avg-1-chunk-16-left-128{suffix}")
    decoder = find_artifact(model_root, f"decoder-epoch-99-avg-1-chunk-16-left-128{suffix}")
    joiner = find_artifact(model_root, f"joiner-epoch-99-avg-1-chunk-16-left-128{suffix}")
    tokens = find_artifact(model_root, "tokens.txt")

    recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=str(tokens),
        encoder=str(encoder),
        decoder=str(decoder),
        joiner=str(joiner),
        num_threads=4,
        provider="cpu",
        sample_rate=SAMPLE_RATE,
        feature_dim=80,
        decoding_method="greedy_search",
        max_active_paths=4,
        lm="",
        lm_scale=0.1,
        lodr_fst="",
        lodr_scale=-0.1,
        hotwords_file="",
        hotwords_score=1.5,
        modeling_unit="",
        bpe_vocab="",
        blank_penalty=0.0,
    )
    stream = recognizer.create_stream()
    audio = np.asarray(read_wav_float(wav_path), dtype=np.float32)
    stream.accept_waveform(SAMPLE_RATE, audio)
    stream.accept_waveform(SAMPLE_RATE, np.zeros(FINAL_ZERO_SAMPLES, dtype=np.float32))
    stream.input_finished()
    decode_steps = 0
    while recognizer.is_ready(stream):
        recognizer.decode_stream(stream)
        decode_steps += 1
        if decode_steps > 10000:
            raise RuntimeError("sherpa smoke exceeded decode-step safety bound")
    result = recognizer.get_result(stream)
    text_length = len(getattr(result, "text", "") or "")

    report = base_report(candidate_id, family, config, generate_smoke_wav(wav_path))
    report.update(
        {
            "runtime": {"distribution": "sherpa-onnx", "version": version},
            "artifacts": artifacts,
            "execution": {
                "online_transducer_api_executed": True,
                "decode_completed": True,
                "decode_steps": decode_steps,
                "result_text_length_observed": text_length,
            },
        }
    )
    return report


def run_whisper(candidate_id: str, model_path: Path, cli_path: Path, wav_path: Path, source_revision: str) -> dict[str, Any]:
    family, config = candidate_record(candidate_id)
    if family["family"] != "whisper.cpp":
        raise RuntimeError("whisper subcommand requires a whisper.cpp candidate")
    if source_revision != family["runtime"]["revision"]:
        raise RuntimeError("whisper.cpp source revision drift")
    artifacts = verify_artifacts(candidate_id, config, model_path.parent)
    if model_path.name != config["model"]:
        raise RuntimeError("whisper model filename drift")
    version_output = subprocess.run(
        [str(cli_path), "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    ).stdout
    proc = subprocess.run(
        [
            str(cli_path),
            "-m", str(model_path),
            "-f", str(wav_path),
            "-t", "4",
            "-l", "en",
            "-ng",
            "-nfa",
            "-nf",
            "-nt",
            "-np",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"whisper-cli smoke failed with exit code {proc.returncode}")

    report = base_report(candidate_id, family, config, generate_smoke_wav(wav_path))
    report.update(
        {
            "runtime": {
                "source_revision": source_revision,
                "cli_binary_sha256": sha256_file(cli_path),
                "version_output_sha256": sha256_bytes(version_output.encode("utf-8")),
            },
            "artifacts": artifacts,
            "execution": {
                "whisper_cli_executed": True,
                "decode_completed": True,
                "exit_code": proc.returncode,
                "captured_output_retained": False,
            },
        }
    )
    return report


def write_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    canonical = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    report = dict(report)
    report["evidence_payload_sha256"] = sha256_bytes(canonical)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("moonshine", "sherpa", "whisper"):
        p = sub.add_parser(name)
        p.add_argument("--candidate", required=True)
        p.add_argument("--wav", type=Path, required=True)
        p.add_argument("--output", type=Path, required=True)
        if name == "moonshine":
            p.add_argument("--work-dir", type=Path, required=True)
        elif name == "sherpa":
            p.add_argument("--model-root", type=Path, required=True)
        else:
            p.add_argument("--model", type=Path, required=True)
            p.add_argument("--cli", type=Path, required=True)
            p.add_argument("--source-revision", required=True)

    args = parser.parse_args()
    wav_meta = generate_smoke_wav(args.wav)
    # generate_smoke_wav is intentionally called again inside each runner before
    # report creation; equality of its digest makes generator drift observable.
    if args.command == "moonshine":
        report = run_moonshine(args.candidate, args.work_dir, args.wav)
    elif args.command == "sherpa":
        report = run_sherpa(args.candidate, args.model_root, args.wav)
    else:
        report = run_whisper(args.candidate, args.model, args.cli, args.wav, args.source_revision)
    if report["synthetic_input"]["sha256"] != wav_meta["sha256"]:
        raise RuntimeError("deterministic smoke input digest drift")
    write_report(report, args.output)
    print(f"SMOKE_STATUS={report['status']}")
    print(f"CANDIDATE={report['candidate_id']}")
    print("PRIMARY_TEST_DECODING=NO")
    print("HUMAN_SPEECH=NO")
    print("COMPARATIVE_RANKING=NO")
    print("ACCURACY_SCORING=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
