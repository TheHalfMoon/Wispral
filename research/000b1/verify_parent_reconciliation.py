#!/usr/bin/env python3
"""Fail closed if parent/founding task authority drifts behind canonical 000B1 closeout."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
B1_EVIDENCE = "8df69835349f85d5ae6af9d6a62ef3af24f65f43"
B1_CLOSEOUT = "ed05ad9b0ef80ae4f6838e783188cf306c20391a"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} missing canonical text: {needle}")


def reject(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label} retains stale authority text: {needle}")


def main() -> int:
    try:
        parent_tasks = (ROOT / "specs/000B-stt-entity-bakeoff/tasks.md").read_text(encoding="utf-8")
        founding_tasks = (ROOT / "specs/000-founding-research/tasks.md").read_text(encoding="utf-8")
        frontier = (ROOT / "specs/CURRENT.md").read_text(encoding="utf-8")
        current_state = (ROOT / "docs/canonical/CURRENT_STATE.md").read_text(encoding="utf-8")

        require(parent_tasks, f"- [x] `000B1` benchmark/candidate qualification — `VERIFIED`; evidence merge `{B1_EVIDENCE}`, canonical closeout merge `{B1_CLOSEOUT}`.", "000B tasks")
        require(parent_tasks, "- [ ] `000B2` unbiased local STT bakeoff — `BLOCKED_EXTERNAL`; primary execution is not authorized.", "000B tasks")
        require(parent_tasks, "Entry-preparation work may only remove non-primary readiness blockers", "000B tasks")
        require(parent_tasks, "`specs/CURRENT.md` owns the executable frontier.", "000B tasks")
        reject(parent_tasks, "## Immediate authorized child\n\n`000B1-benchmark-candidate-qualification`", "000B tasks")
        reject(parent_tasks, "State after this refinement becomes canonical: `GRAIN`", "000B tasks")

        require(founding_tasks, "- [x] `000B1` benchmark/candidate qualification — `VERIFIED`.", "founding tasks")
        require(founding_tasks, "- [ ] `000B2` unbiased local STT bakeoff — `BLOCKED_EXTERNAL`; entry-preparation only until all attempt-time gates pass.", "founding tasks")
        require(founding_tasks, f"B1 canonical closeout merge `{B1_CLOSEOUT}`", "founding tasks")
        reject(founding_tasks, "Its only task-level child is:", "founding tasks")
        reject(founding_tasks, "State after the refinement authority becomes canonical: `GRAIN`", "founding tasks")

        require(frontier, "`000B1-benchmark-candidate-qualification`\n\nState: `VERIFIED`", "CURRENT")
        require(frontier, "`000B2-unbiased-stt-bakeoff`\n\nState: `BLOCKED_EXTERNAL`", "CURRENT")
        require(current_state, "**Verified speech child:** `000B1-benchmark-candidate-qualification` — `VERIFIED`", "CURRENT_STATE")
        require(current_state, "**Blocked successor:** `000B2-unbiased-stt-bakeoff` — `BLOCKED_EXTERNAL`", "CURRENT_STATE")
    except (AssertionError, OSError) as exc:
        print(f"VERIFY_000B_PARENT_RECONCILIATION=FAIL: {exc}", file=sys.stderr)
        return 1

    print("VERIFY_000B_PARENT_RECONCILIATION=PASS")
    print("B1_DISPOSITION=VERIFIED")
    print("B2_DISPOSITION=BLOCKED_EXTERNAL")
    print("B2_PRIMARY_EXECUTION=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
