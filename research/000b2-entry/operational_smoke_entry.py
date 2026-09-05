#!/usr/bin/env python3
"""Canonical entrypoint for the bounded 000B2 operational smoke harness."""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
import shutil
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
MOONSHINE_UPSTREAM_URL = "https://github.com/moonshine-ai/moonshine.git"
MOONSHINE_RUNTIME_IDENTITY_NAME = "wispral-moonshine-source-build-identity.json"
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


def git_output(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(source), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    ).stdout.strip()


def python_manifest(root: Path) -> dict[str, str]:
    """Return a deterministic digest ledger for every Python source in a package tree."""

    result: dict[str, str] = {}
    for path in sorted(root.rglob("*.py")):
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"unexpected Python source path in Moonshine runtime: {path}")
        result[path.relative_to(root).as_posix()] = sha256_file(path)
    if not result:
        raise RuntimeError("Moonshine Python source manifest is empty")
    return result


def manifest_digest(manifest: dict[str, str]) -> str:
    raw = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verified_pinned_moonshine_source(work_dir: Path, verifier: Any) -> Path:
    """Materialize and fail-closed verify the exact pinned Moonshine source checkout."""

    source_root = work_dir.parent / "moonshine-source"
    git_dir = source_root / ".git"
    if source_root.is_symlink() or git_dir.is_symlink():
        raise RuntimeError("Moonshine source checkout path must not be a symlink")

    if not git_dir.is_dir():
        if source_root.exists() and (not source_root.is_dir() or any(source_root.iterdir())):
            raise RuntimeError("Moonshine source checkout path exists with unexpected contents")
        source_root.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init", str(source_root)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
        subprocess.run(
            ["git", "-C", str(source_root), "remote", "add", "origin", MOONSHINE_UPSTREAM_URL],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(source_root),
                "fetch",
                "--depth=1",
                "--no-tags",
                "origin",
                verifier.EXPECTED_UPSTREAM_REVISION,
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        subprocess.run(
            ["git", "-C", str(source_root), "checkout", "--detach", "FETCH_HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )

    remote = git_output(source_root, "remote", "get-url", "origin")
    if remote != MOONSHINE_UPSTREAM_URL:
        raise RuntimeError("Moonshine source checkout origin drift")
    status = git_output(source_root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise RuntimeError("Moonshine source checkout contains tracked or untracked drift")

    verifier.verify_pinned_upstream(source_root)
    return source_root


def source_bound_moonshine_runtime(work_dir: Path, source_root: Path, verifier: Any) -> tuple[Path, dict[str, Any]]:
    """Build and materialize a Moonshine Python/native runtime from the verified checkout itself."""

    shared_root = work_dir.parent
    build_root = shared_root / "moonshine-source-build"
    runtime_root = shared_root / "moonshine-source-runtime"
    runtime_package = runtime_root / "moonshine_voice"
    identity_path = shared_root / MOONSHINE_RUNTIME_IDENTITY_NAME
    source_package = source_root / "language-bindings" / "python" / "src" / "moonshine_voice"
    core_root = source_root / "core"
    source_ort = core_root / "third-party" / "onnxruntime" / "lib" / "linux" / "x86_64" / "libonnxruntime.so.1"
    source_revision = git_output(source_root, "rev-parse", "HEAD")
    source_tree = git_output(source_root, "rev-parse", "HEAD^{tree}")
    source_python_manifest = python_manifest(source_package)
    source_python_digest = manifest_digest(source_python_manifest)

    if source_revision != verifier.EXPECTED_UPSTREAM_REVISION:
        raise RuntimeError("Moonshine source revision changed before runtime build")
    setup_py = source_root / "language-bindings" / "python" / "setup.py"
    if 'version="0.1.5"' not in setup_py.read_text(encoding="utf-8"):
        raise RuntimeError("pinned Moonshine Python package version drift")
    if source_ort.is_symlink() or not source_ort.is_file():
        raise RuntimeError("pinned Moonshine ONNX Runtime library missing")

    def validate_existing_identity(identity: dict[str, Any]) -> bool:
        if not runtime_package.is_dir() or runtime_package.is_symlink():
            return False
        native = runtime_package / "libmoonshine.so"
        ort = runtime_package / "libonnxruntime.so.1"
        cache = build_root / "CMakeCache.txt"
        if any(path.is_symlink() or not path.is_file() for path in (native, ort, cache)):
            return False
        observed_python_manifest = python_manifest(runtime_package)
        expected = {
            "schema_version": "000b2-moonshine-source-build-identity-v1",
            "source_repository": verifier.EXPECTED_UPSTREAM_REPOSITORY,
            "source_revision": source_revision,
            "source_tree": source_tree,
            "release": "v0.1.5",
            "python_source_manifest_sha256": source_python_digest,
            "native_library_sha256": sha256_file(native),
            "onnxruntime_sha256": sha256_file(ort),
            "cmake_cache_sha256": sha256_file(cache),
            "build_type": "Release",
            "runtime_origin": "PINNED_SOURCE_CHECKOUT_BUILD",
        }
        if observed_python_manifest != source_python_manifest:
            return False
        return identity == expected

    if identity_path.is_file() and not identity_path.is_symlink():
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        if isinstance(identity, dict) and validate_existing_identity(identity):
            if git_output(source_root, "status", "--porcelain=v1", "--untracked-files=all"):
                raise RuntimeError("Moonshine source checkout drifted after source build")
            return runtime_root, identity
        raise RuntimeError("existing Moonshine source-build identity is invalid")

    if build_root.exists():
        shutil.rmtree(build_root)
    if runtime_root.exists():
        shutil.rmtree(runtime_root)
    build_root.mkdir(parents=True)

    subprocess.run(
        [
            "cmake",
            "-S",
            str(core_root),
            "-B",
            str(build_root),
            "-DCMAKE_BUILD_TYPE=Release",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )
    subprocess.run(
        ["cmake", "--build", str(build_root), "--config", "Release", "-j2"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=900,
    )

    built_native = build_root / "libmoonshine.so"
    cache = build_root / "CMakeCache.txt"
    if built_native.is_symlink() or not built_native.is_file():
        raise RuntimeError("Moonshine source build did not produce libmoonshine.so")
    if cache.is_symlink() or not cache.is_file():
        raise RuntimeError("Moonshine source build CMake cache missing")
    expected_home = f"CMAKE_HOME_DIRECTORY:INTERNAL={core_root}"
    if expected_home not in cache.read_text(encoding="utf-8", errors="strict").splitlines():
        raise RuntimeError("Moonshine CMake build is not bound to pinned core source")
    if git_output(source_root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeError("Moonshine source build mutated the verified checkout")

    shutil.copytree(source_package, runtime_package)
    shutil.copy2(built_native, runtime_package / "libmoonshine.so")
    shutil.copy2(source_ort, runtime_package / "libonnxruntime.so.1")
    if python_manifest(runtime_package) != source_python_manifest:
        raise RuntimeError("materialized Moonshine Python runtime differs from pinned source")

    identity = {
        "schema_version": "000b2-moonshine-source-build-identity-v1",
        "source_repository": verifier.EXPECTED_UPSTREAM_REPOSITORY,
        "source_revision": source_revision,
        "source_tree": source_tree,
        "release": "v0.1.5",
        "python_source_manifest_sha256": source_python_digest,
        "native_library_sha256": sha256_file(runtime_package / "libmoonshine.so"),
        "onnxruntime_sha256": sha256_file(runtime_package / "libonnxruntime.so.1"),
        "cmake_cache_sha256": sha256_file(cache),
        "build_type": "Release",
        "runtime_origin": "PINNED_SOURCE_CHECKOUT_BUILD",
    }
    identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not validate_existing_identity(identity):
        raise RuntimeError("Moonshine source-build identity failed self-verification")
    return runtime_root, identity


def import_source_bound_moonshine(runtime_root: Path, identity: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    """Import Moonshine only from the source-built runtime root and prove the loaded native library path."""

    if any(name == "moonshine_voice" or name.startswith("moonshine_voice.") for name in sys.modules):
        raise RuntimeError("moonshine_voice was imported before source/runtime identity verification")
    sys.path.insert(0, str(runtime_root))
    importlib.invalidate_caches()

    from moonshine_voice import ModelArch, Transcriber
    from moonshine_voice.download import download_model_from_info, find_model_info
    from moonshine_voice.moonshine_api import _MoonshineLib

    package = importlib.import_module("moonshine_voice")
    package_file = Path(package.__file__).resolve(strict=True)
    expected_package = (runtime_root / "moonshine_voice").resolve(strict=True)
    if package_file.parent != expected_package:
        raise RuntimeError("Moonshine Python runtime was not imported from the verified source copy")

    lib_wrapper = _MoonshineLib()
    native_path = Path(lib_wrapper._lib._name).resolve(strict=True)
    expected_native = expected_package / "libmoonshine.so"
    if native_path != expected_native:
        raise RuntimeError("Moonshine native runtime was not loaded from the pinned source build")
    if sha256_file(native_path) != identity.get("native_library_sha256"):
        raise RuntimeError("loaded Moonshine native library digest differs from source-build identity")

    return ModelArch, Transcriber, download_model_from_info, find_model_info


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

    harness = load_module("wispral_b2r02_operational_smoke", B2R02_HARNESS)
    verifier = load_module("wispral_b2r02_operational_verifier", B2R02_VERIFIER)
    verifier.verify_canonical_authority(harness)
    verifier.verify_structural_harness(harness)
    verifier.verify_qualification_evidence()
    source_root = verified_pinned_moonshine_source(work_dir, verifier)
    runtime_root, build_identity = source_bound_moonshine_runtime(work_dir, source_root, verifier)

    if harness.EXPECTED_RUNTIME_REVISION != family["runtime"]["revision"]:
        raise RuntimeError("B2R02 harness runtime revision differs from candidate authority")
    if harness.EXPECTED_RUNTIME_REVISION != build_identity.get("source_revision"):
        raise RuntimeError("B2R02 harness runtime revision differs from source-built runtime")
    if harness.EXPECTED_RUNTIME_DISTRIBUTION != "moonshine-voice" or harness.EXPECTED_RUNTIME_VERSION != "0.1.5":
        raise RuntimeError("B2R02 harness runtime distribution/version drift")

    ModelArch, Transcriber, download_model_from_info, find_model_info = import_source_bound_moonshine(
        runtime_root, build_identity
    )
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
                "version": "0.1.5",
                "model_arch": int(arch),
                "model_asset_root": Path(model_path).name,
                "source_repository": build_identity["source_repository"],
                "source_revision": build_identity["source_revision"],
                "source_tree": build_identity["source_tree"],
                "runtime_origin": build_identity["runtime_origin"],
                "python_source_manifest_sha256": build_identity["python_source_manifest_sha256"],
                "native_library_sha256": build_identity["native_library_sha256"],
                "onnxruntime_sha256": build_identity["onnxruntime_sha256"],
                "cmake_cache_sha256": build_identity["cmake_cache_sha256"],
                "build_type": build_identity["build_type"],
            },
            "artifacts": artifacts,
            "execution": {
                "stream_api_executed": True,
                "decode_completed": True,
                "result_line_count_observed": line_count,
                "b2r02_streaming_c0_harness_executed": True,
                "b2r02_static_verifier_executed": True,
                "b2r02_pinned_upstream_source_verified": True,
                "b2r02_runtime_built_from_verified_source": True,
                "b2r02_runtime_imported_from_verified_source_copy": True,
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
