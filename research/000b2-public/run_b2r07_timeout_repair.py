#!/usr/bin/env python3
"""Run B2R07 with a forward-only wall-clock budget repair and no C0 change."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DECODER_PATH = ROOT / "research" / "000b2-public" / "decode_b2r07.py"
ORIGINAL_ADAPTER_TIMEOUT_SECONDS = 5400
REPAIRED_ADAPTER_TIMEOUT_SECONDS = 10800
FAILED_PRIMARY_RUN_ID = 34053187435
FAILED_PRIMARY_JOB_ID = 101540334687
FAILED_PRIMARY_ARTIFACT_ID = 9996564565
FAILED_PRIMARY_ARTIFACT_ZIP_SHA256 = "a31432029720f93567d5da616e92b068ca0661ddff6ab0db3dd8b97edbf183b2"
FAILED_PRIMARY_BUILD_IDENTITY_SHA256 = "4888182a73a921fa574a2a4f1cf6862779687c0918d0b724622a01a69e30ff82"


class TimeoutRepairError(RuntimeError):
    """Raised when the bounded timeout repair cannot be applied exactly."""


def load_decoder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("wispral_b2r07_decoder", DECODER_PATH)
    if spec is None or spec.loader is None:
        raise TimeoutRepairError(f"unable to load decoder: {DECODER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SubprocessProxy:
    """Delegate subprocess calls while widening only the frozen adapter wall-clock allowance."""

    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    CalledProcessError = subprocess.CalledProcessError
    TimeoutExpired = subprocess.TimeoutExpired

    def run(self, args: Any, *pargs: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        is_adapter = (
            isinstance(args, (list, tuple))
            and bool(args)
            and Path(str(args[0])).name == "wispral-whispercpp-c0"
        )
        if is_adapter:
            observed_timeout = kwargs.get("timeout")
            if observed_timeout != ORIGINAL_ADAPTER_TIMEOUT_SECONDS:
                raise TimeoutRepairError(
                    "adapter timeout repair expected the original 5400-second wall-clock guard"
                )
            kwargs["timeout"] = REPAIRED_ADAPTER_TIMEOUT_SECONDS
            print("B2R07_TIMEOUT_REPAIR=APPLIED")
            print(f"B2R07_ORIGINAL_ADAPTER_TIMEOUT_SECONDS={ORIGINAL_ADAPTER_TIMEOUT_SECONDS}")
            print(f"B2R07_REPAIRED_ADAPTER_TIMEOUT_SECONDS={REPAIRED_ADAPTER_TIMEOUT_SECONDS}")
            print("B2R07_C0_SEMANTICS_CHANGED=NO")
        return subprocess.run(args, *pargs, **kwargs)


def main() -> int:
    decoder = load_decoder()
    decoder.subprocess = SubprocessProxy()
    args = decoder.parse_args()

    try:
        decoder.validate_authority()
        evidence = decoder.execute(
            args.work_dir,
            args.preprocessed_root,
            args.model,
            args.adapter,
            args.build_identity,
        )
        evidence.pop("evidence_payload_sha256", None)
        evidence["execution_orchestration"] = {
            "policy": "FORWARD_ONLY_WALL_CLOCK_BUDGET_REPAIR",
            "repair_basis": "FIRST_B2R07_PRIMARY_EXECUTION_TIMED_OUT_WITHOUT_TRANSCRIPT_OR_EVIDENCE_ARTIFACT",
            "failed_primary_run_id": FAILED_PRIMARY_RUN_ID,
            "failed_primary_job_id": FAILED_PRIMARY_JOB_ID,
            "failed_primary_artifact_id": FAILED_PRIMARY_ARTIFACT_ID,
            "failed_primary_artifact_zip_sha256": FAILED_PRIMARY_ARTIFACT_ZIP_SHA256,
            "failed_primary_artifact_contents": ["whisper-build/wispral-build-identity.json"],
            "failed_primary_build_identity_sha256": FAILED_PRIMARY_BUILD_IDENTITY_SHA256,
            "failed_primary_transcript_artifact_present": False,
            "failed_primary_evidence_json_present": False,
            "result_inspection_before_repair": False,
            "adapter_process_partitioning_changed": False,
            "adapter_invocation_count_changed": False,
            "candidate_order_changed": False,
            "frozen_input_order_changed": False,
            "c0_controls_changed": False,
            "original_adapter_timeout_seconds": ORIGINAL_ADAPTER_TIMEOUT_SECONDS,
            "repaired_adapter_timeout_seconds": REPAIRED_ADAPTER_TIMEOUT_SECONDS,
            "timeout_semantics": "EXECUTION_WALL_CLOCK_GUARD_ONLY_NOT_A_C0_OR_SCORING_PARAMETER",
        }
        evidence["evidence_payload_sha256"] = decoder.sha256_bytes(
            decoder.canonical_json_bytes(evidence)
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("B2R07_EXECUTION=CAPTURED")
        print(f"B2R07_SOURCE_REVISION={evidence['run']['repository_revision']}")
        print(f"B2R07_INPUTS={evidence['execution']['input_count']}")
        print(f"B2R07_DECODED={evidence['execution']['decoded_count']}")
        print(f"B2R07_FAILURES={evidence['execution']['failure_count']}")
        print("B2R08_AUTHORIZED=NO")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        return 0
    except (
        decoder.DecodeError,
        TimeoutRepairError,
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"B2R07_EXECUTION=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
