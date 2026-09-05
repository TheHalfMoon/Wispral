#!/usr/bin/env python3
"""Verify the forward-only invalidation of public-corpus ATTEMPT-001."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "research" / "000b2-public"
INVALIDATION = PUBLIC / "attempt-001-invalidation.json"
RECOVERY_READINESS = PUBLIC / "recovery-readiness.json"
ATTEMPT = PUBLIC / "attempt-manifest.json"
FROZEN = ROOT / "research" / "000b1" / "frozen-methodology.json"
TASKS = ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md"

EXPECTED_MAIN = "b326397cdd29fbb132b9c438ba2178626558efab"
EXPECTED_ATTEMPT = "000B2-PUBLIC-ATTEMPT-001"
EXPECTED_REPLACEMENT_ATTEMPT = "000B2-PUBLIC-ATTEMPT-002"
EXPECTED_FROZEN_SHA256 = "fc177308926941e683f311a340b9e398f2c44ffa32963b3abc20aa359dbb09df"
EXPECTED_MOONSHINE_REV = "234f60faa0eb388b01cdf7e60aca232af37aefda"
EXPECTED_B2E01_EVIDENCE_SHA256 = "af2c604a3f402789d69e424291c5f41a24eca0f575b1b26a3822da73dd0c4a8e"
EXPECTED_B2E02_EVIDENCE_SHA256 = "8bc1b3e2e10bd7c64465b424f8dff5ffc84a153868459457d91e22e5cf3da253"
RECOVERY_TASKS = tuple(f"B2R{index:02d}" for index in range(1, 13))
PRIMARY_DECODE_RECOVERY_TASKS = set(RECOVERY_TASKS[4:10])


class VerifyError(ValueError):
    """Raised when the recovery evidence fails closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def recovery_completed_prefix(tasks: str) -> list[str]:
    """Return the completed recovery prefix and reject skipped recovery units."""
    states: list[tuple[str, bool]] = []
    task_lines = tasks.splitlines()
    for task in RECOVERY_TASKS:
        matches = [line for line in task_lines if f"`{task}`" in line]
        require(len(matches) == 1, f"{task} recovery task must appear exactly once")
        line = matches[0]
        if line.startswith("- [x]"):
            states.append((task, True))
        elif line.startswith("- [ ]"):
            states.append((task, False))
        else:
            raise VerifyError(f"{task} recovery task has malformed checklist state")

    completed: list[str] = []
    pending_seen = False
    for task, complete in states:
        if not complete:
            pending_seen = True
        elif pending_seen:
            raise VerifyError(f"recovery task ordering skipped a predecessor before {task}")
        else:
            completed.append(task)
    return completed


def verify_recovery_readiness(tasks: str) -> None:
    readiness = load(RECOVERY_READINESS)
    completed = recovery_completed_prefix(tasks)
    completed_count = len(completed)
    active = RECOVERY_TASKS[completed_count] if completed_count < len(RECOVERY_TASKS) else None

    require(readiness.get("schema_version") == "000b2-public-recovery-readiness-v1", "recovery readiness schema drift")
    require(readiness.get("lane") == "PUBLIC_CORPUS", "recovery readiness lane drift")
    expected_state = (
        "RECOVERY_PENDING_CANONICALIZATION"
        if completed_count == 0
        else "RECOVERY_READY"
        if active is not None
        else "RECOVERY_COMPLETE"
    )
    require(readiness.get("state") == expected_state, f"recovery readiness state must be {expected_state}")
    require(
        readiness.get("authority_precedence") == "OVERRIDES_ATTEMPT_001_READY_SNAPSHOT_FOR_NEW_EXECUTION",
        "recovery authority precedence drift",
    )

    historical = readiness.get("historical_readiness_snapshot", {})
    require(historical == {
        "path": "research/000b2-public/readiness.json",
        "completed_through": "B2E02",
        "role": "HISTORICAL_ATTEMPT_001_POST_B2E02_SNAPSHOT",
        "active_execution_authority": False,
    }, "historical readiness snapshot boundary drift")

    invalidated = readiness.get("invalidated_attempt", {})
    require(invalidated == {
        "attempt_id": EXPECTED_ATTEMPT,
        "invalidation_path": "research/000b2-public/attempt-001-invalidation.json",
        "comparative_scoring_eligible": False,
        "candidate_superiority_claim_eligible": False,
        "new_primary_decode_authorized": False,
    }, "invalidated attempt readiness boundary drift")

    replacement = readiness.get("replacement_attempt", {})
    expected_frozen = completed_count >= 4
    expected_decode_open = active in PRIMARY_DECODE_RECOVERY_TASKS
    require(replacement.get("attempt_id") == EXPECTED_REPLACEMENT_ATTEMPT, "replacement attempt id drift")
    require(replacement.get("required") is True, "replacement attempt requirement weakened")
    require(replacement.get("frozen") is expected_frozen, "replacement attempt freeze state drift")
    require(replacement.get("primary_decode_entry_open") is expected_decode_open, "replacement attempt decode-entry authority drift")

    require(readiness.get("completed_recovery_tasks") == completed, "recovery readiness completed-task ledger drift")
    require(readiness.get("active_recovery_unit") == active, "active recovery unit drift")
    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action, "recovery next action missing")
    if active is not None:
        require(active in next_action, f"recovery next action does not bind active unit {active}")
    if completed_count < 4:
        require("primary" in next_action.lower() and ("closed" in next_action.lower() or "do not" in next_action.lower()), "pre-freeze recovery next action must keep primary decoding closed")

    guards = readiness.get("claim_guards", {})
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "recovery human developer-speech evidence guard drift")
    require(guards.get("comparative_result_available") is (completed_count >= 12), "recovery comparative-result state drift")
    require(guards.get("production_stt_selected") is False, "recovery production STT selection opened")
    require(guards.get("product_code_authorized") is False, "recovery product code authority opened")


def verify_local() -> None:
    record = load(INVALIDATION)
    attempt = load(ATTEMPT)
    frozen = load(FROZEN)

    require(record.get("schema_version") == "000b2-public-attempt-invalidation-v1", "invalidation schema drift")
    require(record.get("task") == "B2R01", "invalidation task drift")
    require(record.get("lane") == "PUBLIC_CORPUS", "invalidation lane drift")
    require(record.get("attempt_id") == EXPECTED_ATTEMPT, "invalidation attempt id drift")
    require(record.get("status") == "INVALIDATED_MATERIAL_EXECUTION_DRIFT", "invalidation status drift")
    require(record.get("discovered_against_canonical_main") == EXPECTED_MAIN, "discovery base drift")

    require(sha256(FROZEN) == EXPECTED_FROZEN_SHA256, "frozen methodology bytes drift")
    require(attempt.get("attempt_id") == EXPECTED_ATTEMPT, "historical attempt id drift")
    require(attempt.get("frozen") is True and attempt.get("phase") == "PRE_PRIMARY_FROZEN", "historical attempt freeze drift")
    candidate_set = attempt.get("candidate_set", {})
    require(candidate_set.get("frozen_methodology_sha256") == EXPECTED_FROZEN_SHA256, "attempt frozen-methodology binding drift")
    require(candidate_set.get("membership_change_after_freeze_allowed") is False, "attempt candidate membership guard drift")
    scoring = attempt.get("scoring", {})
    require(scoring.get("result_driven_changes_allowed") is False, "historical scoring guard drift")

    preprocessing = frozen.get("preprocessing", {})
    moonshine = frozen.get("c0_by_family", {}).get("moonshine", {})
    require(preprocessing.get("feed_chunk_ms") == 500, "frozen feed chunk ms drift")
    require(preprocessing.get("feed_chunk_samples") == 8000, "frozen feed chunk samples drift")
    require(preprocessing.get("finalization_zero_pad_ms") == 660, "frozen zero pad ms drift")
    require(preprocessing.get("finalization_zero_pad_samples") == 10560, "frozen zero pad samples drift")
    require(moonshine.get("runtime_revision") == EXPECTED_MOONSHINE_REV, "frozen Moonshine revision drift")
    require(str(moonshine.get("integration", "")).startswith("Pinned Moonshine Transcriber streaming API;"), "frozen Moonshine integration is not streaming API")
    require(moonshine.get("transcription_interval_seconds") == 0.5, "frozen Moonshine transcription interval drift")
    require(moonshine.get("vad_threshold") == 0.0, "frozen Moonshine VAD threshold drift")
    require(moonshine.get("decode_incomplete_lines") is True, "frozen Moonshine incomplete-line policy drift")
    require(moonshine.get("word_timestamps") is False, "frozen Moonshine timestamp policy drift")

    frozen_record = record.get("frozen_contract", {})
    require(frozen_record.get("sha256") == EXPECTED_FROZEN_SHA256, "recorded frozen-contract digest drift")
    require(frozen_record.get("moonshine_runtime_revision") == EXPECTED_MOONSHINE_REV, "recorded Moonshine revision drift")
    require(frozen_record.get("feed_chunk_ms") == 500 and frozen_record.get("feed_chunk_samples") == 8000, "recorded feed schedule drift")
    require(frozen_record.get("finalization_zero_pad_ms") == 660 and frozen_record.get("finalization_zero_pad_samples") == 10560, "recorded finalization schedule drift")
    require(frozen_record.get("vad_threshold") == 0.0, "recorded VAD threshold drift")

    affected = record.get("affected_canonical_execution")
    require(isinstance(affected, list) and len(affected) == 2, "affected execution inventory drift")
    expected = {
        "B2E01": {
            "candidate_id": "moonshine-compact",
            "canonical_merge": "bb3acfae1f39669d74118a564e57a131731484d3",
            "qualified_head": "9a2b4dd2d79c445d31a09a6c435af6cbe43e6808",
            "decoder_path": "research/000b2-public/decode_b2e01.py",
            "evidence_path": "research/000b2-public/b2e01-moonshine-compact.json",
            "evidence_raw_file_sha256": EXPECTED_B2E01_EVIDENCE_SHA256,
        },
        "B2E02": {
            "candidate_id": "moonshine-balanced",
            "canonical_merge": "91588babc1f738c4284f53d40b4cd96dc13bfd50",
            "qualified_head": "1c4db3f5f857f7a813f4fbb8bc4593c5c5f066c1",
            "decoder_path": "research/000b2-public/decode_b2e02.py",
            "evidence_path": "research/000b2-public/b2e02-moonshine-balanced.json",
            "evidence_raw_file_sha256": EXPECTED_B2E02_EVIDENCE_SHA256,
        },
    }
    seen: set[str] = set()
    for item in affected:
        require(isinstance(item, dict), "affected execution entry malformed")
        task = item.get("task")
        require(task in expected and task not in seen, f"unexpected or duplicate affected task: {task!r}")
        seen.add(task)
        for key, value in expected[task].items():
            require(item.get(key) == value, f"{task} {key} drift")
        decoder = ROOT / item["decoder_path"]
        decoder_text = decoder.read_text(encoding="utf-8")
        require("transcriber.transcribe_without_streaming(audio)" in decoder_text, f"{task} no longer records the invalidated offline call")
        require("vad_threshold" not in decoder_text, f"{task} unexpectedly overrides vad_threshold; invalidation record needs review")
        evidence = ROOT / item["evidence_path"]
        require(sha256(evidence) == item["evidence_raw_file_sha256"], f"{task} historical evidence bytes drift")
    require(seen == {"B2E01", "B2E02"}, "affected execution task set drift")

    drift = record.get("material_drift")
    require(isinstance(drift, list) and [item.get("id") for item in drift] == [
        "MOONSHINE_OFFLINE_PATH_USED",
        "MOONSHINE_VAD_THRESHOLD_DRIFT",
    ], "material drift inventory drift")
    require(all(item.get("severity") == "MATERIAL" for item in drift), "material drift severity weakened")
    require(all(item.get("upstream_proof_required") is True for item in drift), "upstream proof gate weakened")

    boundary = record.get("discovery_execution_boundary", {})
    require(boundary.get("b2e03_cancelled_run_id") == 33972588550, "B2E03 cancelled run id drift")
    require(boundary.get("b2e03_cancelled_head") == "bcbd27d28453b9e8fe820c03f016e3597d2dd107", "B2E03 cancelled head drift")
    require(boundary.get("b2e03_halt_run_id") == 33973416932, "B2E03 halt run id drift")
    require(boundary.get("b2e03_artifact_eligible_as_primary_evidence") is False, "cancelled B2E03 artifact became eligible")

    disposition = record.get("disposition", {})
    for key in (
        "historical_attempt_preserved",
        "historical_b2e01_b2e02_evidence_bytes_must_remain_unchanged",
        "attempt_002_required",
    ):
        require(disposition.get(key) is True, f"recovery disposition weakened: {key}")
    for key in (
        "attempt_001_eligible_for_comparative_scoring",
        "attempt_001_eligible_for_candidate_superiority_claims",
        "attempt_001_new_primary_decode_authorized",
        "b2e03_or_later_attempt_001_execution_authorized",
        "candidate_membership_change_authorized",
        "subset_membership_change_authorized",
        "scorer_or_normalization_change_authorized",
        "production_stt_selected",
        "product_code_authorized",
    ):
        require(disposition.get(key) is False, f"recovery disposition opened forbidden authority: {key}")
    require(disposition.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")

    tasks = TASKS.read_text(encoding="utf-8")
    require("ATTEMPT-001 evidence is historical and ineligible for comparative scoring" in tasks, "task ledger invalidation boundary missing")
    verify_recovery_readiness(tasks)


def verify_upstream(source: Path) -> None:
    source = source.resolve()
    observed_revision = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    require(observed_revision == EXPECTED_MOONSHINE_REV, "upstream Moonshine revision mismatch")
    subprocess.run(["git", "-C", str(source), "diff", "--quiet", "HEAD", "--"], check=True)

    header = (source / "core" / "transcriber.h").read_text(encoding="utf-8")
    implementation = (source / "core" / "transcriber.cpp").read_text(encoding="utf-8")
    require("float vad_threshold = 0.5f;" in header, "pinned Moonshine default vad_threshold is no longer 0.5")

    start_token = "void Transcriber::transcribe_without_streaming("
    end_token = "int32_t Transcriber::create_stream()"
    start = implementation.find(start_token)
    end = implementation.find(end_token, start)
    require(start >= 0 and end > start, "unable to isolate pinned transcribe_without_streaming implementation")
    body = implementation[start:end]
    require("stream->vad->process_audio(audio_data" in body, "offline path no longer passes the whole supplied audio to VAD in one API call")
    require("stream->stop();" in body, "offline path stop semantics drift")
    require("add_audio_to_stream" not in body, "offline path unexpectedly delegates to the public incremental stream feed API")
    require("transcribe_stream" not in body, "offline path unexpectedly delegates to incremental transcribe_stream")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--moonshine-source", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        verify_local()
        if not args.static_only:
            require(args.moonshine_source is not None, "--moonshine-source is required unless --static-only is used")
            verify_upstream(args.moonshine_source)
        print("B2R01_ATTEMPT_001_INVALIDATION=PASS")
        print("ATTEMPT_001_COMPARATIVE_EVIDENCE=INELIGIBLE")
        print("ATTEMPT_002_REQUIRED=YES")
        print("ATTEMPT_001_NEW_PRIMARY_DECODE_AUTHORIZED=NO")
        return 0
    except (VerifyError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"B2R01_ATTEMPT_001_INVALIDATION=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
