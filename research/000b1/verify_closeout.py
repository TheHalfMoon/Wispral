#!/usr/bin/env python3
"""Fail-closed verifier for the canonical 000B1 closeout record."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "000b1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

CANONICAL_BASE = "6b5696a6becc360948282712cc9339df9cb3a67c"
EVIDENCE_HEAD = "262c8cc6dd6fadfcd782ce5beee2f3ca443c77b5"
EVIDENCE_MERGE = "8df69835349f85d5ae6af9d6a62ef3af24f65f43"
EXPECTED_REVIEWERS = {"coderabbitai", "cubic-dev-ai"}
EXPECTED_SCOPE = {
    "primary_test_decoding_performed": False,
    "comparative_ranking_present": False,
    "product_runtime_or_cargo_added": False,
    "human_recording_authorized": False,
    "b2_authorized": False,
}
EXPECTED_B2_BLOCKERS = {
    "human developer-speech consent, retention, redistribution, withdrawal, and frozen corpus authority are absent",
    "Moonshine material payload SHA-256 values remain pending attempt-time materialization",
    "sherpa-onnx tokens.txt SHA-256 remains pending attempt-time materialization",
    "each selected candidate still requires bounded non-primary operational smoke PASS or an explicit canonical waiver",
    "the exact B2 scorer implementation/revision and configuration digest are not frozen",
    "attempt-time FFmpeg binary/version-output identities and preprocessing execution evidence are not frozen",
    "the B2 execution environment and hardware fingerprint are not frozen",
    "a final B2 attempt manifest with frozen=true and a matching freeze digest does not exist",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def require_unique_line(text: str, expected: str, label: str) -> None:
    matches = [line.strip() for line in text.splitlines() if expected in line]
    if matches != [expected]:
        fail(f"{label} must contain exactly one canonical line {expected!r}; got {matches!r}")


def verify_record(raw_record: Any) -> dict[str, Any]:
    record = require_mapping(raw_record, "canonical closeout record")

    if record.get("schema_version") != "000b1-canonical-closeout-v1":
        fail("closeout schema version drift")
    if record.get("specification") != "000B1-benchmark-candidate-qualification":
        fail("closeout specification drift")
    if record.get("disposition") != "VERIFIED":
        fail("B1 must close as VERIFIED")
    if record.get("canonical_base_before_evidence_merge") != CANONICAL_BASE:
        fail("canonical base before evidence merge drift")
    if record.get("evidence_pr") != 7:
        fail("evidence PR drift")
    if record.get("evidence_pr_head") != EVIDENCE_HEAD:
        fail("evidence PR head drift")
    if record.get("evidence_merge_commit") != EVIDENCE_MERGE:
        fail("evidence merge commit drift")

    for field in ("canonical_base_before_evidence_merge", "evidence_pr_head", "evidence_merge_commit"):
        if not SHA40.fullmatch(str(record.get(field, ""))):
            fail(f"invalid SHA field {field}")

    workflow = require_mapping(record.get("evidence_workflow"), "evidence workflow")
    if workflow != {
        "name": "000B1 Preregistration",
        "run_id": 33514521301,
        "run_number": 58,
        "head_sha": EVIDENCE_HEAD,
        "conclusion": "success",
    }:
        fail("exact-head workflow evidence drift")

    review = require_mapping(record.get("review_reconciliation"), "review reconciliation")
    reviewers = review.get("independent_reviewers")
    if (
        not isinstance(reviewers, list)
        or len(reviewers) != 2
        or any(not isinstance(item, str) for item in reviewers)
        or len(set(reviewers)) != 2
        or set(reviewers) != EXPECTED_REVIEWERS
    ):
        fail("independent reviewer record must be a two-item unique reviewer list")
    if review.get("all_actionable_findings_reconciled") is not True:
        fail("review findings not reconciled")
    if review.get("all_review_threads_resolved_before_merge") is not True:
        fail("review threads not reconciled")

    scope = require_mapping(record.get("scope"), "scope")
    if scope != EXPECTED_SCOPE:
        fail("scope non-claims drift")

    if record.get("b2_disposition") != "BLOCKED_EXTERNAL" or record.get("b2_ready") is not False:
        fail("B2 must remain BLOCKED_EXTERNAL / not ready")
    blockers = record.get("b2_blockers")
    if (
        not isinstance(blockers, list)
        or len(blockers) != len(EXPECTED_B2_BLOCKERS)
        or any(not isinstance(item, str) for item in blockers)
        or len(set(blockers)) != len(EXPECTED_B2_BLOCKERS)
        or set(blockers) != EXPECTED_B2_BLOCKERS
    ):
        fail("B2 blocker set must exactly match the eight canonical blockers")

    next_action = record.get("next_action")
    if not isinstance(next_action, str) or "Do not execute 000B2 primary decoding" not in next_action:
        fail("B2 next action no longer fails closed")

    return record


def verify_documents(
    record: dict[str, Any],
    tasks: str,
    spec: str,
    frontier: str,
    current_state: str,
) -> None:
    base = str(record["canonical_base_before_evidence_merge"])
    merge = str(record["evidence_merge_commit"])

    if "- [x] **B120 — Canonical B1 closeout." not in tasks:
        fail("B120 is not marked complete")
    if "PCM WAV" not in tasks or "raw mono 16 kHz PCM_S16LE representation" in tasks:
        fail("B110 canonical audio wording not reconciled")

    if "**State:** `VERIFIED`" not in spec:
        fail("B1 spec state not VERIFIED")

    if "`000B1-benchmark-candidate-qualification`\n\nState: `VERIFIED`" not in frontier:
        fail("CURRENT.md does not record B1 VERIFIED")
    if "`000B2-unbiased-stt-bakeoff`\n\nState: `BLOCKED_EXTERNAL`" not in frontier:
        fail("CURRENT.md does not record B2 BLOCKED_EXTERNAL")
    require_unique_line(
        frontier,
        f"Canonical 000B refinement/base merge: `{base}`",
        "CURRENT.md",
    )
    require_unique_line(
        frontier,
        f"Canonical evidence merge: `{merge}` from PR #7.",
        "CURRENT.md",
    )

    require_unique_line(
        current_state,
        f"**000B refinement merge:** `{base}`",
        "canonical CURRENT_STATE",
    )
    require_unique_line(
        current_state,
        f"**000B1 evidence merge:** `{merge}`",
        "canonical CURRENT_STATE",
    )
    if "**Verified speech child:** `000B1-benchmark-candidate-qualification` — `VERIFIED`" not in current_state:
        fail("canonical CURRENT_STATE missing B1 verified child")
    if "**Blocked successor:** `000B2-unbiased-stt-bakeoff` — `BLOCKED_EXTERNAL`" not in current_state:
        fail("canonical CURRENT_STATE missing B2 blocked successor")


def main() -> int:
    try:
        record = verify_record(load(HERE / "canonical-closeout.json"))
        tasks = (ROOT / "specs" / "000B1-benchmark-candidate-qualification" / "tasks.md").read_text(encoding="utf-8")
        spec = (ROOT / "specs" / "000B1-benchmark-candidate-qualification" / "spec.md").read_text(encoding="utf-8")
        frontier = (ROOT / "specs" / "CURRENT.md").read_text(encoding="utf-8")
        current_state = (ROOT / "docs" / "canonical" / "CURRENT_STATE.md").read_text(encoding="utf-8")
        verify_documents(record, tasks, spec, frontier, current_state)
    except (AssertionError, OSError, ValueError, KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        print(f"VERIFY_000B1_CLOSEOUT=FAIL: {exc}", file=sys.stderr)
        return 1

    print("VERIFY_000B1_CLOSEOUT=PASS")
    print("B1_DISPOSITION=VERIFIED")
    print("B2_DISPOSITION=BLOCKED_EXTERNAL")
    print("PRIMARY_TEST_DECODING=NO")
    print("COMPARATIVE_RANKING=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
