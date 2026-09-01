#!/usr/bin/env python3
"""Adversarial regressions for the 000B1 canonical closeout verifier."""

from __future__ import annotations

from copy import deepcopy

import verify_closeout as vc


def expect_failure(label: str, fn) -> None:
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError(f"regression did not fail closed: {label}")


def main() -> int:
    record = vc.verify_record(vc.load(vc.HERE / "canonical-closeout.json"))
    tasks = (vc.ROOT / "specs" / "000B1-benchmark-candidate-qualification" / "tasks.md").read_text(encoding="utf-8")
    spec = (vc.ROOT / "specs" / "000B1-benchmark-candidate-qualification" / "spec.md").read_text(encoding="utf-8")
    frontier = (vc.ROOT / "specs" / "CURRENT.md").read_text(encoding="utf-8")
    current_state = (vc.ROOT / "docs" / "canonical" / "CURRENT_STATE.md").read_text(encoding="utf-8")
    vc.verify_documents(record, tasks, spec, frontier, current_state)

    expect_failure("non-object closeout JSON", lambda: vc.verify_record([]))

    bad_base = deepcopy(record)
    bad_base["canonical_base_before_evidence_merge"] = "0" * 40
    expect_failure("valid-looking but incorrect canonical base", lambda: vc.verify_record(bad_base))

    bad_reviewers = deepcopy(record)
    bad_reviewers["review_reconciliation"]["independent_reviewers"] = {
        "coderabbitai": True,
        "cubic-dev-ai": True,
    }
    expect_failure("reviewer mapping instead of list", lambda: vc.verify_record(bad_reviewers))

    duplicate_blockers = deepcopy(record)
    first_blocker = duplicate_blockers["b2_blockers"][0]
    duplicate_blockers["b2_blockers"] = [first_blocker] * 8
    expect_failure("repeated generic blocker set", lambda: vc.verify_record(duplicate_blockers))

    bad_frontier = frontier.replace(vc.EVIDENCE_MERGE, "1" * 40)
    expect_failure(
        "CURRENT.md evidence merge drift",
        lambda: vc.verify_documents(record, tasks, spec, bad_frontier, current_state),
    )

    bad_current_state = current_state.replace(vc.CANONICAL_BASE, "2" * 40)
    expect_failure(
        "CURRENT_STATE canonical base drift",
        lambda: vc.verify_documents(record, tasks, spec, frontier, bad_current_state),
    )

    print("VERIFY_000B1_CLOSEOUT_REGRESSIONS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
