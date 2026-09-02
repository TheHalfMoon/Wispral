#!/usr/bin/env python3
"""Fail closed on B2P02 workflow exact-head and coupling invariants."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METHODOLOGY = ROOT / ".github/workflows/000b2-public-methodology.yml"
MATERIALIZATION = ROOT / ".github/workflows/000b2-public-materialization.yml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"B2P02_WORKFLOW_CONTRACTS=FAIL: {message}")


def require_text(text: str, phrase: str, label: str) -> None:
    require(phrase in text, f"{label} missing required text: {phrase}")


def main() -> None:
    for path in (METHODOLOGY, MATERIALIZATION):
        require(path.is_file(), f"missing workflow: {path.relative_to(ROOT)}")

    methodology = METHODOLOGY.read_text(encoding="utf-8")
    materialization = MATERIALIZATION.read_text(encoding="utf-8")

    for phrase in (
        "EXACT_REVISION: ${{ github.event.pull_request.head.sha || github.sha }}",
        "ref: ${{ env.EXACT_REVISION }}",
        'test "$(git rev-parse HEAD)" = "$EXACT_REVISION"',
        "python research/000b2-public/verify_workflow_contracts.py",
        "python research/000b2-public/verify_methodology.py",
        "docs/canonical/CURRENT_STATE.md",
        "research/000b2-public/**",
    ):
        require_text(methodology, phrase, "methodology workflow")

    for phrase in (
        "B2P02_REVISION: ${{ github.event.pull_request.head.sha || github.sha }}",
        "ref: ${{ env.B2P02_REVISION }}",
        'test "$(git rev-parse HEAD)" = "$B2P02_REVISION"',
        "python research/000b2-public/verify_workflow_contracts.py",
        "python research/000b2-public/materialize_archives.py",
        "actions/upload-artifact@v4",
        ".github/workflows/000b2-public-methodology.yml",
        ".github/workflows/000b2-public-materialization.yml",
        "research/000b2-public/verify_workflow_contracts.py",
    ):
        require_text(materialization, phrase, "materialization workflow")

    require(
        methodology.count("Verify exact revision identity") == 1,
        "methodology workflow must contain exactly one exact-revision identity step",
    )
    require(
        materialization.count("Verify exact revision identity") == 1,
        "materialization workflow must contain exactly one exact-revision identity step",
    )

    print("B2P02_WORKFLOW_CONTRACTS=PASS")
    print("METHODOLOGY_EXACT_HEAD=ENFORCED")
    print("MATERIALIZATION_EXACT_HEAD=ENFORCED")
    print("WORKFLOW_COUPLING=ENFORCED")


if __name__ == "__main__":
    main()
