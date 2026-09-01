#!/usr/bin/env python3
"""Fail-closed verifier for the canonical 000B1 closeout record."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "000b1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    try:
        record = load(HERE / "canonical-closeout.json")
        if record.get("schema_version") != "000b1-canonical-closeout-v1":
            fail("closeout schema version drift")
        if record.get("specification") != "000B1-benchmark-candidate-qualification":
            fail("closeout specification drift")
        if record.get("disposition") != "VERIFIED":
            fail("B1 must close as VERIFIED")
        if record.get("evidence_pr") != 7:
            fail("evidence PR drift")
        if record.get("evidence_pr_head") != "262c8cc6dd6fadfcd782ce5beee2f3ca443c77b5":
            fail("evidence PR head drift")
        if record.get("evidence_merge_commit") != "8df69835349f85d5ae6af9d6a62ef3af24f65f43":
            fail("evidence merge commit drift")
        for field in ("canonical_base_before_evidence_merge", "evidence_pr_head", "evidence_merge_commit"):
            if not SHA40.fullmatch(str(record.get(field, ""))):
                fail(f"invalid SHA field {field}")

        workflow = record.get("evidence_workflow", {})
        if workflow != {
            "name": "000B1 Preregistration",
            "run_id": 33514521301,
            "run_number": 58,
            "head_sha": "262c8cc6dd6fadfcd782ce5beee2f3ca443c77b5",
            "conclusion": "success",
        }:
            fail("exact-head workflow evidence drift")

        review = record.get("review_reconciliation", {})
        if set(review.get("independent_reviewers", [])) != {"coderabbitai", "cubic-dev-ai"}:
            fail("independent reviewer record drift")
        if review.get("all_actionable_findings_reconciled") is not True:
            fail("review findings not reconciled")
        if review.get("all_review_threads_resolved_before_merge") is not True:
            fail("review threads not reconciled")

        scope = record.get("scope", {})
        for key in (
            "primary_test_decoding_performed",
            "comparative_ranking_present",
            "product_runtime_or_cargo_added",
            "human_recording_authorized",
            "b2_authorized",
        ):
            if scope.get(key) is not False:
                fail(f"scope non-claim weakened: {key}")

        if record.get("b2_disposition") != "BLOCKED_EXTERNAL" or record.get("b2_ready") is not False:
            fail("B2 must remain BLOCKED_EXTERNAL / not ready")
        blockers = record.get("b2_blockers")
        if not isinstance(blockers, list) or len(blockers) < 8 or any(not isinstance(item, str) or not item for item in blockers):
            fail("B2 blocker set incomplete")
        required_terms = (
            "human developer-speech",
            "Moonshine",
            "tokens.txt",
            "operational smoke",
            "scorer",
            "FFmpeg",
            "execution environment",
            "frozen=true",
        )
        joined = "\n".join(blockers)
        for term in required_terms:
            if term not in joined:
                fail(f"B2 blocker missing required term: {term}")

        tasks = (ROOT / "specs" / "000B1-benchmark-candidate-qualification" / "tasks.md").read_text(encoding="utf-8")
        if "- [x] **B120 — Canonical B1 closeout." not in tasks:
            fail("B120 is not marked complete")
        if "PCM WAV" not in tasks or "raw mono 16 kHz PCM_S16LE representation" in tasks:
            fail("B110 canonical audio wording not reconciled")

        spec = (ROOT / "specs" / "000B1-benchmark-candidate-qualification" / "spec.md").read_text(encoding="utf-8")
        if "**State:** `VERIFIED`" not in spec:
            fail("B1 spec state not VERIFIED")

        frontier = (ROOT / "specs" / "CURRENT.md").read_text(encoding="utf-8")
        if "`000B1-benchmark-candidate-qualification`\n\nState: `VERIFIED`" not in frontier:
            fail("CURRENT.md does not record B1 VERIFIED")
        if "`000B2-unbiased-stt-bakeoff`\n\nState: `BLOCKED_EXTERNAL`" not in frontier:
            fail("CURRENT.md does not record B2 BLOCKED_EXTERNAL")

        current_state = (ROOT / "docs" / "canonical" / "CURRENT_STATE.md").read_text(encoding="utf-8")
        if "**Verified speech child:** `000B1-benchmark-candidate-qualification` — `VERIFIED`" not in current_state:
            fail("canonical CURRENT_STATE missing B1 verified child")
        if "**Blocked successor:** `000B2-unbiased-stt-bakeoff` — `BLOCKED_EXTERNAL`" not in current_state:
            fail("canonical CURRENT_STATE missing B2 blocked successor")
    except (AssertionError, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
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
