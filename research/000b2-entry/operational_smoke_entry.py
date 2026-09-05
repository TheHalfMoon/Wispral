#!/usr/bin/env python3
"""Canonical entrypoint for the bounded 000B2 operational smoke harness."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import operational_smoke as smoke
from verify_materialization import correction_map

HERE = Path(__file__).resolve().parent
B1_REGISTRY = HERE.parent / "000b1" / "qualified-candidates.json"
AMENDMENT = HERE / "artifact-size-amendment.json"
B2R02_HARNESS = HERE.parent / "000b2-public" / "moonshine_streaming_c0.py"
B2R02_VERIFIER = HERE.parent / "000b2-public" / "verify_b2r02_moonshine_streaming.py"
EXPECTED_CORRECTIONS = {
    ("sherpa-onnx-compact", "tokens.txt"),
    ("sherpa-onnx-balanced", "tokens.txt"),
}
ORIGINAL_RUN_WHISPER = smoke.run_whisper
BUILD_IDENTITY_NAME = "wispral-build-identity.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_amendment_sizes() -> dict[tuple[str, str], int]:
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    if not isinstance(amendment, dict):
        raise RuntimeError("artifact amendment must be a JSON object")
    corrections = correction_map(amendment)
    if set(corrections) != EXPECTED_CORRECTIONS:
        raise RuntimeError("artifact amendment correction scope drift")

    registry = json.loads(B1_REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise RuntimeError("B1 candidate registry must be a JSON object")
    pending: dict[tuple[str, str], dict] = {}
    for family in registry.get("families", []):
        for config in family.get("configurations", []):
            candidate_id = config.get("id")
            for artifact in config.get("artifacts", []):
                if isinstance(artifact, dict) and artifact.get("sha256") is None:
                    key = (candidate_id, artifact.get("path"))
                    if key in pending:
                        raise RuntimeError(f"duplicate B1 pending artifact: {key}")
                    pending[key] = artifact

    result: dict[tuple[str, str], int] = {}
    for key, item in corrections.items():
        registry_item = pending.get(key)
        if registry_item is None:
            raise RuntimeError(f"artifact amendment target is not pending in B1: {key}")
        if registry_item.get("size_bytes") != item.get("historical_b1_size_bytes"):
            raise RuntimeError(f"artifact amendment historical size differs from B1: {key}")
        if registry_item.get("source_revision") != item.get("source_revision"):
            raise RuntimeError(f"artifact amendment source revision differs from B1: {key}")
        if item.get("source_revision") != "6037ea07e3abfe599ad00d418968bcf9656e7472":
            raise RuntimeError(f"artifact amendment source revision drift: {key}")
        if item.get("historical_b1_size_bytes") != 5050 or item.get("b2_entry_size_bytes") != 5048:
            raise RuntimeError(f"artifact amendment size drift: {key}")
        result[key] = 5048
    return result


def bound_run_moonshine(candidate_id: str, work_dir: Path, wav_path: Path) -> dict[str, Any]:
    """Exercise the B2R02 adapter on deterministic non-primary smoke material."""

    family, config = smoke.candidate_record(candidate_id)
    if family["family"] != "moonshine":
        raise RuntimeError("moonshine subcommand requires a Moonshine candidate")
    version = importlib.metadata.version("moonshine-voice")
    if version != "0.1.5":
        raise RuntimeError(f"moonshine-voice version drift: {version}")

    from moonshine_voice import ModelArch, Transcriber
    from moonshine_voice.download import download_model_from_info, find_model_info

    harness = load_module("wispral_b2r02_operational_smoke", B2R02_HARNESS)
    verifier = load_module("wispral_b2r02_operational_verifier", B2R02_VERIFIER)
    verifier.verify_canonical_authority(harness)
    verifier.verify_structural_harness(harness)
    verifier.verify_qualification_evidence()

    if harness.EXPECTED_RUNTIME_REVISION != family["runtime"]["revision"]:
        raise RuntimeError("B2R02 harness runtime revision differs from candidate authority")
    if harness.EXPECTED_RUNTIME_DISTRIBUTION != "moonshine-voice" or harness.EXPECTED_RUNTIME_VERSION != version:
        raise RuntimeError("B2R02 harness runtime distribution/version drift")

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
    if Path(model_path).name != harness.EXPECTED_MODEL_ASSET_REVISION:
        raise RuntimeError("Moonshine model asset revision drift")
    artifacts = smoke.verify_artifacts(candidate_id, config, Path(model_path))

    audio = smoke.read_wav_float(wav_path)
    with harness.create_transcriber(
        Transcriber,
        model_path=model_path,
        model_arch=arch,
    ) as transcriber:
        result, trace = harness.transcribe_streaming_c0(transcriber, audio)
        line_count = len(result.lines) if result is not None else 0

    report = smoke.base_report(candidate_id, family, config, smoke.generate_smoke_wav(wav_path))
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
                "b2r02_streaming_c0_harness_executed": True,
                "b2r02_static_verifier_executed": True,
                "speech_samples": trace.speech_samples,
                "speech_chunk_samples": list(trace.speech_chunk_samples),
                "final_zero_pad_samples": trace.zero_pad_samples,
                "sample_rate_hz": trace.sample_rate_hz,
                "transcription_interval_seconds": harness.TRANSCRIPTION_INTERVAL_SECONDS,
                "vad_threshold": harness.MOONSHINE_C0_OPTIONS["vad_threshold"],
                "repository_context_used": False,
                "keyterms_used": False,
                "transcript_text_retained": False,
            },
        }
    )
    return report


def observed_whisper_source_revision(cli_path: Path) -> str:
    cli = cli_path.resolve(strict=True)
    if cli.name != "whisper-cli" or cli.parent.name != "bin" or cli.parent.parent.name != "build":
        raise RuntimeError("whisper CLI path is not the canonical source-tree build/bin/whisper-cli path")
    source_root = cli.parents[2]
    git_dir = source_root / ".git"
    if not git_dir.exists():
        raise RuntimeError("whisper CLI source checkout has no Git identity")
    observed = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    ).stdout.strip()
    if len(observed) != 40 or any(char not in "0123456789abcdef" for char in observed):
        raise RuntimeError("whisper CLI source revision is malformed")
    tree = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD^{tree}"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    ).stdout.strip()
    if len(tree) != 40 or any(char not in "0123456789abcdef" for char in tree):
        raise RuntimeError("whisper source tree identity is malformed")
    clean = subprocess.run(
        ["git", "-C", str(source_root), "diff", "--quiet", "HEAD", "--"],
        check=False,
        timeout=30,
    )
    if clean.returncode != 0:
        raise RuntimeError("whisper tracked source differs from pinned checkout")

    cache = source_root / "build" / "CMakeCache.txt"
    if cache.is_symlink() or not cache.is_file():
        raise RuntimeError("whisper CMake build identity is missing")
    expected_home = f"CMAKE_HOME_DIRECTORY:INTERNAL={source_root}"
    if expected_home not in cache.read_text(encoding="utf-8", errors="strict").splitlines():
        raise RuntimeError("whisper CMake build is not bound to the observed source checkout")

    identity_path = source_root / "build" / BUILD_IDENTITY_NAME
    if identity_path.is_symlink() or not identity_path.is_file():
        raise RuntimeError("whisper verified build manifest is missing")
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    expected_identity = {
        "schema_version": "000b2-whisper-build-identity-v1",
        "source_revision": observed,
        "source_tree": tree,
        "cli_binary_sha256": sha256_file(cli),
        "cmake_cache_sha256": sha256_file(cache),
        "build_type": "Release",
        "ggml_cuda": "OFF",
        "ggml_metal": "OFF",
        "whisper_build_tests": "OFF",
        "whisper_build_examples": "ON",
        "target": "whisper-cli",
    }
    if identity != expected_identity:
        raise RuntimeError("whisper CLI/build manifest does not match observed build inputs and binary")
    return observed


def bound_run_whisper(
    candidate_id: str,
    model_path: Path,
    cli_path: Path,
    wav_path: Path,
    source_revision: str,
) -> dict:
    family, _ = smoke.candidate_record(candidate_id)
    expected = family.get("runtime", {}).get("revision")
    observed = observed_whisper_source_revision(cli_path)
    if observed != expected:
        raise RuntimeError("whisper CLI source checkout differs from frozen B1 runtime revision")
    if source_revision != observed:
        raise RuntimeError("caller-supplied whisper revision differs from independently observed CLI source")
    return ORIGINAL_RUN_WHISPER(candidate_id, model_path, cli_path, wav_path, observed)


smoke.amendment_sizes = canonical_amendment_sizes
smoke.run_moonshine = bound_run_moonshine
smoke.run_whisper = bound_run_whisper

if __name__ == "__main__":
    raise SystemExit(smoke.main())
