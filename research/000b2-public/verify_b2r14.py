#!/usr/bin/env python3
"""Reviewable B2R14 static verifier for the sherpa-onnx result harness."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TASK = "B2R14"
HARNESS_PATH = ROOT / "research/000b2-public/b2r14-sherpa-result-harness.py"
QUALIFICATION_PATH = ROOT / "research/000b2-public/b2r14-harness-qualification.json"
SHERPA_REVISION = "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e"
SHERPA_PATH = "sherpa-onnx/python/sherpa_onnx/online_recognizer.py"
SHERPA_BLOB = "18b49aaf40dc6e43606c63c9633762e8f573876b"
FIXTURE_DIGEST = "0c92bddb4e96f3ea9ec9f0f64a668255a6c15527ac09f6f119cafde60c7c4a39"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"B2R14_VERIFICATION=FAIL: {message}")


def git_output(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(completed.returncode == 0, completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def load_qualification() -> dict[str, Any]:
    document = json.loads(QUALIFICATION_PATH.read_text(encoding="utf-8"))
    require(document.get("task") == TASK, "qualification task binding drift")
    fixture = document.get("non_primary_fixture")
    require(isinstance(fixture, dict), "non-primary fixture contract missing")
    require(fixture.get("material_class") == "DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY", "material class drift")
    require(fixture.get("fixture_id") == "b2r14-sherpa-result-string-contract-v1", "fixture id drift")
    require(fixture.get("sample_rate_hz") == 16000, "sample rate drift")
    require(fixture.get("channel_count") == 1, "channel count drift")
    require(fixture.get("sample_format") == "PCM_S16LE", "sample format drift")
    require(fixture.get("frame_count") == 16000, "frame count drift")
    require(fixture.get("pcm_sha256") == FIXTURE_DIGEST, "fixture digest drift")
    require(fixture.get("primary_corpus_access") is False, "non-primary boundary drift")
    require(fixture.get("frozen_p0_access") is False, "frozen subset boundary drift")
    require(fixture.get("attempt_003_primary_evidence_access") is False, "attempt evidence boundary drift")
    return document


def verify_harness() -> None:
    tree = ast.parse(HARNESS_PATH.read_text(encoding="utf-8"), filename=str(HARNESS_PATH))
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    require(len(functions) == 1, "harness must contain exactly one top-level function")
    function = functions[0]
    require(isinstance(function, ast.FunctionDef) and function.name == "extract_result", "entry point drift")
    require([arg.arg for arg in function.args.args] == ["recognizer", "stream"], "entry point arguments drift")
    require(
        function.args.posonlyargs == []
        and function.args.vararg is None
        and function.args.kwarg is None
        and function.args.kwonlyargs == []
        and function.args.defaults == []
        and function.args.kw_defaults == [],
        "entry point must not expose alternate argument forms",
    )
    require(len(function.body) == 1 and isinstance(function.body[0], ast.Return), "entry point body drift")
    returned = function.body[0].value
    require(isinstance(returned, ast.Call), "entry point must directly return a call")
    require(
        isinstance(returned.func, ast.Attribute)
        and isinstance(returned.func.value, ast.Name)
        and returned.func.value.id == "recognizer"
        and returned.func.attr == "get_result"
        and len(returned.args) == 1
        and isinstance(returned.args[0], ast.Name)
        and returned.args[0].id == "stream"
        and not returned.keywords,
        "entry point must exactly return recognizer.get_result(stream)",
    )
    require(not any(isinstance(node, ast.Attribute) and node.attr == "text" for node in ast.walk(tree)), "object-style text extraction is forbidden")
    require(
        not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" for node in ast.walk(tree)),
        "dynamic result coercion is forbidden",
    )


def verify_fixture() -> bytes:
    payload = b"\x00" * (16000 * 2)
    require(len(payload) == 32000, "fixture byte length drift")
    require(hashlib.sha256(payload).hexdigest() == FIXTURE_DIGEST, "fixture digest mismatch")
    return payload


def verify_pinned_source(source_root: Path, fixture: bytes) -> None:
    require(git_output(source_root, "rev-parse", "HEAD") == SHERPA_REVISION, "pinned source revision drift")
    require(git_output(source_root, "rev-parse", f"HEAD:{SHERPA_PATH}") == SHERPA_BLOB, "pinned source blob drift")
    source_path = source_root / SHERPA_PATH
    source_tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    imported_native_names: set[str] = set()
    for node in source_tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "sherpa_onnx.lib._sherpa_onnx":
            imported_native_names.update(alias.name for alias in node.names)
    require(bool(imported_native_names), "pinned recognizer native imports missing")

    native_module = types.ModuleType("sherpa_onnx.lib._sherpa_onnx")
    for name in imported_native_names:
        setattr(native_module, name, type(name, (), {}))
    package = types.ModuleType("sherpa_onnx")
    package.__path__ = []
    lib_package = types.ModuleType("sherpa_onnx.lib")
    lib_package.__path__ = []
    sys.modules["sherpa_onnx"] = package
    sys.modules["sherpa_onnx.lib"] = lib_package
    sys.modules["sherpa_onnx.lib._sherpa_onnx"] = native_module
    module_spec = importlib.util.spec_from_file_location("wispral_b2r14_pinned_online_recognizer", source_path)
    require(module_spec is not None and module_spec.loader is not None, "pinned recognizer loader unavailable")
    pinned = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(pinned)

    class SyntheticStream:
        def __init__(self, payload: bytes) -> None:
            self.fixture_bytes = payload

    class NativeResult:
        text = "b2r14-synthetic-result"

    class NativeRecognizer:
        def get_result(self, stream: SyntheticStream) -> NativeResult:
            require(hashlib.sha256(stream.fixture_bytes).hexdigest() == FIXTURE_DIGEST, "fixture delivery drift")
            return NativeResult()

    recognizer = object.__new__(pinned.OnlineRecognizer)
    recognizer.recognizer = NativeRecognizer()
    result = pinned.OnlineRecognizer.get_result(recognizer, SyntheticStream(fixture))
    require(type(result) is str, "pinned OnlineRecognizer result is not a plain string")
    require(result == "b2r14-synthetic-result", "pinned OnlineRecognizer result content drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sherpa-source", type=Path)
    args = parser.parse_args()
    load_qualification()
    verify_harness()
    fixture = verify_fixture()
    if args.sherpa_source is not None:
        verify_pinned_source(args.sherpa_source.resolve(), fixture)
        print("B2R14_PINNED_SOURCE_CONTRACT=PASS")
    else:
        print("B2R14_PINNED_SOURCE_CONTRACT=NOT_RUN")
    print("B2R14_STATIC_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
