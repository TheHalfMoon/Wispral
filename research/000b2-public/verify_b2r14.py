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
PRE_REQUALIFICATION_HARNESS_BLOB = "aec083c9a02b501121d510c0ac598df096251362"
PREMATURE_MERGE = "2f4212228f24e40fbd03cfc59ab4774df94c0cc3"
PREMATURE_TASK_BASE = "7004199d33c0c60595086636b95537d8fbee3f84"
PREMATURE_TASK_HEAD = "1687057a56399e5892dee540704b949b868ed94d"
FAILED_REVIEW_RUN = "c647c8b6-cd21-4085-b851-523a474d65ce"


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
    require(document.get("schema_version") == "000b2-public-b2r14-harness-qualification-v2", "qualification schema drift")
    require(document.get("task") == TASK, "qualification task binding drift")
    require(document.get("lane") == "PUBLIC_CORPUS", "qualification lane drift")
    require(document.get("status") == "CORRECTIVE_REQUALIFICATION_PENDING_INDEPENDENT_REVIEW", "requalification status drift")
    require(document.get("predecessor_reconciliation_merge") == PREMATURE_TASK_BASE, "predecessor reconciliation drift")
    require(document.get("harness_path") == "research/000b2-public/b2r14-sherpa-result-harness.py", "harness path drift")
    require(document.get("pre_requalification_harness_git_blob_sha1") == PRE_REQUALIFICATION_HARNESS_BLOB, "pre-requalification harness identity drift")
    require(document.get("harness_semantics_changed") is False, "corrective requalification changed harness semantics")
    require(document.get("entry_point") == "extract_result(recognizer, stream)", "entry-point declaration drift")
    require(document.get("result_contract") == {
        "required_return_type": "str",
        "preservation": "EXACT",
        "object_style_text_extraction_allowed": False,
        "dynamic_result_coercion_allowed": False,
    }, "result contract drift")
    require(document.get("pinned_runtime") == {
        "distribution": "sherpa-onnx",
        "version": "1.13.7",
        "revision": SHERPA_REVISION,
        "source_path": SHERPA_PATH,
        "source_git_blob_sha1": SHERPA_BLOB,
        "contract": "OnlineRecognizer.get_result(self, s: OnlineStream) -> str",
        "return_semantics": "return self.recognizer.get_result(s).text.strip()",
    }, "pinned runtime contract drift")
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
    require(document.get("governance_recovery") == {
        "premature_merge_detected": True,
        "premature_merge_sha": PREMATURE_MERGE,
        "premature_merge_task_base": PREMATURE_TASK_BASE,
        "premature_merge_task_head": PREMATURE_TASK_HEAD,
        "failed_independent_review_provider": "CodeRabbit",
        "failed_independent_review_run_id": FAILED_REVIEW_RUN,
        "failure_reason": "PR_CLOSED_BEFORE_REVIEW_COMPLETION",
        "premature_merge_eligible_as_canonical_task_completion": False,
        "corrective_requalification_required": True,
        "canonical_successor_advance_allowed": False,
        "result_selection_effect": "NONE",
    }, "governance recovery chronology drift")
    require(document.get("qualification_evidence") == {
        "candidate_supplied_verifier": "REVIEW_ONLY_NOT_TRUSTED_AUTHORITY",
        "canonical_base_common_verifier": "REQUIRED",
        "trusted_pull_request_target_gate": "REQUIRED",
        "fresh_independent_exact_range_review": "REQUIRED_ON_CORRECTIVE_HEAD",
        "guarded_normal_merge": "REQUIRED_ON_CORRECTIVE_HEAD",
        "post_merge_recovery_proof": "REQUIRED_ON_CORRECTIVE_MERGE",
    }, "qualification gate declaration drift")
    require(document.get("claim_guards") == {
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
    }, "claim guards drift")
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
    print("B2R14_CORRECTIVE_REQUALIFICATION=PASS")
    print("B2R14_STATIC_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
