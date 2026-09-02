#!/usr/bin/env python3
"""Fail closed on active B2P02 workflow structure and exact-head invariants."""

from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
METHODOLOGY = ROOT / ".github/workflows/000b2-public-methodology.yml"
MATERIALIZATION = ROOT / ".github/workflows/000b2-public-materialization.yml"

METHODOLOGY_PATHS = [
    "specs/000B-stt-entity-bakeoff/**",
    "specs/000B2-public-corpus-bakeoff/**",
    "specs/000-founding-research/tasks.md",
    "specs/CURRENT.md",
    "docs/canonical/CURRENT_STATE.md",
    "research/000b2-public/**",
    ".github/workflows/000b2-public-methodology.yml",
    ".github/workflows/000b2-public-materialization.yml",
]
MATERIALIZATION_PATHS = [
    "research/000b2-public/corpus-source.json",
    "research/000b2-public/readiness.json",
    "research/000b2-public/archive-materialization.json",
    "research/000b2-public/materialize_archives.py",
    "research/000b2-public/verify_methodology.py",
    "research/000b2-public/verify_workflow_contracts.py",
    "specs/000B2-public-corpus-bakeoff/tasks.md",
    "specs/CURRENT.md",
    "docs/canonical/CURRENT_STATE.md",
    ".github/workflows/000b2-public-methodology.yml",
    ".github/workflows/000b2-public-materialization.yml",
]


def require(condition: bool, message: str) -> None:
    """Abort verification when a required invariant is absent."""
    if not condition:
        raise SystemExit(f"B2P02_WORKFLOW_CONTRACTS=FAIL: {message}")


def indentation(line: str) -> int:
    """Return leading-space indentation and reject tabs."""
    require("\t" not in line[: len(line) - len(line.lstrip())], "workflow indentation must not use tabs")
    return len(line) - len(line.lstrip(" "))


def scalar(value: str) -> Any:
    """Parse the scalar forms used by the two bounded workflow files."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    if value.isdigit():
        return int(value)
    return value


def next_content(lines: list[str], index: int) -> int:
    """Advance to the next non-empty, non-comment YAML line."""
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped and not stripped.startswith("#"):
            return index
        index += 1
    return index


def split_mapping(text: str) -> tuple[str, str]:
    """Split one simple YAML mapping entry at its first colon."""
    require(":" in text, f"expected mapping entry, got {text!r}")
    key, value = text.split(":", 1)
    key = key.strip()
    require(bool(key), f"empty YAML mapping key in {text!r}")
    return key, value.strip()


def parse_block_scalar(lines: list[str], index: int, parent_indent: int) -> tuple[str, int]:
    """Parse one literal block scalar while preserving its command text."""
    start = next_content(lines, index)
    require(start < len(lines), "literal block scalar must not be empty")
    block_indent = indentation(lines[start])
    require(block_indent > parent_indent, "literal block scalar must be indented")
    collected: list[str] = []
    cursor = index
    while cursor < len(lines):
        raw = lines[cursor]
        if raw.strip():
            current = indentation(raw)
            if current <= parent_indent:
                break
            require(current >= block_indent, "inconsistent literal block indentation")
            collected.append(raw[block_indent:])
        else:
            collected.append("")
        cursor += 1
    while collected and collected[-1] == "":
        collected.pop()
    return "\n".join(collected), cursor


def parse_mapping(lines: list[str], index: int, indent: int) -> tuple[dict[str, Any], int]:
    """Parse the mapping subset required by the bounded GitHub Actions files."""
    result: dict[str, Any] = {}
    cursor = index
    while True:
        cursor = next_content(lines, cursor)
        if cursor >= len(lines):
            break
        raw = lines[cursor]
        current = indentation(raw)
        if current < indent:
            break
        require(current == indent, f"unexpected mapping indentation at line {cursor + 1}")
        text = raw.strip()
        if text.startswith("- "):
            break
        key, value = split_mapping(text)
        require(key not in result, f"duplicate YAML key {key!r} at indentation {indent}")
        if value == "|":
            parsed, cursor = parse_block_scalar(lines, cursor + 1, indent)
            result[key] = parsed
            continue
        if value:
            result[key] = scalar(value)
            cursor += 1
            continue
        child_index = next_content(lines, cursor + 1)
        require(child_index < len(lines), f"mapping key {key!r} has no value")
        child_indent = indentation(lines[child_index])
        require(child_indent > indent, f"mapping key {key!r} must contain an indented value")
        if lines[child_index].strip().startswith("- "):
            parsed, cursor = parse_list(lines, child_index, child_indent)
        else:
            parsed, cursor = parse_mapping(lines, child_index, child_indent)
        result[key] = parsed
    return result, cursor


def parse_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    """Parse scalar lists and step mappings used by these workflows."""
    result: list[Any] = []
    cursor = index
    while True:
        cursor = next_content(lines, cursor)
        if cursor >= len(lines):
            break
        raw = lines[cursor]
        current = indentation(raw)
        if current < indent:
            break
        require(current == indent, f"unexpected list indentation at line {cursor + 1}")
        text = raw.strip()
        if not text.startswith("- "):
            break
        item_text = text[2:].strip()
        require(bool(item_text), f"empty list item at line {cursor + 1}")
        if ":" not in item_text:
            result.append(scalar(item_text))
            cursor += 1
            continue

        key, value = split_mapping(item_text)
        item: dict[str, Any] = {key: scalar(value) if value else None}
        cursor += 1
        continuation = next_content(lines, cursor)
        if continuation < len(lines) and indentation(lines[continuation]) > indent:
            continuation_indent = indentation(lines[continuation])
            extra, cursor = parse_mapping(lines, continuation, continuation_indent)
            for extra_key, extra_value in extra.items():
                require(extra_key not in item, f"duplicate list-item key {extra_key!r}")
                item[extra_key] = extra_value
        result.append(item)
    return result, cursor


def parse_workflow(path: Path) -> dict[str, Any]:
    """Parse one workflow into a bounded structural representation."""
    lines = path.read_text(encoding="utf-8").splitlines()
    first = next_content(lines, 0)
    require(first < len(lines), f"workflow is empty: {path.relative_to(ROOT)}")
    require(indentation(lines[first]) == 0, f"workflow must begin at top level: {path.relative_to(ROOT)}")
    parsed, cursor = parse_mapping(lines, first, 0)
    require(next_content(lines, cursor) == len(lines), f"unparsed workflow content: {path.relative_to(ROOT)}")
    return parsed


def mapping(value: Any, label: str) -> dict[str, Any]:
    """Require and return a mapping value."""
    require(isinstance(value, dict), f"{label} must be a mapping")
    return value


def sequence(value: Any, label: str) -> list[Any]:
    """Require and return a list value."""
    require(isinstance(value, list), f"{label} must be a list")
    return value


def require_exact_mapping(actual: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    """Require an exact mapping so inactive or extra fields cannot satisfy the gate."""
    require(actual == expected, f"{label} drift: expected {expected!r}, got {actual!r}")


def named_steps(job: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    """Index the active job's steps by unique name."""
    steps = sequence(job.get("steps"), f"{label}.steps")
    indexed: dict[str, dict[str, Any]] = {}
    for raw_step in steps:
        step = mapping(raw_step, f"{label}.step")
        name = step.get("name")
        require(isinstance(name, str) and name, f"every {label} step must have a name")
        require(name not in indexed, f"duplicate {label} step name: {name}")
        indexed[name] = step
    return indexed


def verify_triggers(workflow: dict[str, Any], expected_paths: list[str], label: str) -> None:
    """Verify exact pull-request/push path coupling for one workflow."""
    trigger = mapping(workflow.get("on"), f"{label}.on")
    require(set(trigger) == {"pull_request", "push"}, f"{label} trigger keys drift")
    pull_request = mapping(trigger.get("pull_request"), f"{label}.on.pull_request")
    push = mapping(trigger.get("push"), f"{label}.on.push")
    require_exact_mapping(pull_request, {"paths": expected_paths}, f"{label}.on.pull_request")
    require_exact_mapping(push, {"branches": ["main"], "paths": expected_paths}, f"{label}.on.push")


def verify_methodology(workflow: dict[str, Any]) -> None:
    """Verify the active methodology job and every exact-head control field."""
    require(workflow.get("name") == "000B2 Public Corpus Methodology", "methodology workflow name drift")
    verify_triggers(workflow, METHODOLOGY_PATHS, "methodology")
    require_exact_mapping(mapping(workflow.get("permissions"), "methodology.permissions"), {"contents": "read"}, "methodology.permissions")
    jobs = mapping(workflow.get("jobs"), "methodology.jobs")
    require(set(jobs) == {"verify-public-corpus-methodology"}, "methodology active job set drift")
    job = mapping(jobs.get("verify-public-corpus-methodology"), "methodology.job")
    require(job.get("runs-on") == "ubuntu-latest", "methodology runner drift")
    require_exact_mapping(
        mapping(job.get("env"), "methodology.job.env"),
        {"EXACT_REVISION": "${{ github.event.pull_request.head.sha || github.sha }}"},
        "methodology.job.env",
    )
    steps = named_steps(job, "methodology.job")
    require(
        list(steps) == [
            "Checkout exact revision",
            "Verify exact revision identity",
            "Verify workflow contracts",
            "Verify methodology contract",
        ],
        "methodology step order drift",
    )
    require_exact_mapping(
        steps["Checkout exact revision"],
        {"name": "Checkout exact revision", "uses": "actions/checkout@v4", "with": {"ref": "${{ env.EXACT_REVISION }}"}},
        "methodology checkout step",
    )
    require_exact_mapping(
        steps["Verify exact revision identity"],
        {
            "name": "Verify exact revision identity",
            "run": 'test "$(git rev-parse HEAD)" = "$EXACT_REVISION"\necho "EXACT_REVISION=$EXACT_REVISION"',
        },
        "methodology identity step",
    )
    require_exact_mapping(
        steps["Verify workflow contracts"],
        {"name": "Verify workflow contracts", "run": "python research/000b2-public/verify_workflow_contracts.py"},
        "methodology workflow-contract step",
    )
    require_exact_mapping(
        steps["Verify methodology contract"],
        {"name": "Verify methodology contract", "run": "python research/000b2-public/verify_methodology.py"},
        "methodology verifier step",
    )


def verify_materialization(workflow: dict[str, Any]) -> None:
    """Verify the active materialization job and every exact-head/evidence field."""
    require(workflow.get("name") == "000B2 Public Corpus Archive Materialization", "materialization workflow name drift")
    verify_triggers(workflow, MATERIALIZATION_PATHS, "materialization")
    require_exact_mapping(mapping(workflow.get("permissions"), "materialization.permissions"), {"contents": "read"}, "materialization.permissions")
    jobs = mapping(workflow.get("jobs"), "materialization.jobs")
    require(set(jobs) == {"materialize-official-archives"}, "materialization active job set drift")
    job = mapping(jobs.get("materialize-official-archives"), "materialization.job")
    require(job.get("runs-on") == "ubuntu-latest", "materialization runner drift")
    require(job.get("timeout-minutes") == 30, "materialization timeout drift")
    require_exact_mapping(
        mapping(job.get("env"), "materialization.job.env"),
        {"B2P02_REVISION": "${{ github.event.pull_request.head.sha || github.sha }}"},
        "materialization.job.env",
    )
    steps = named_steps(job, "materialization.job")
    require(
        list(steps) == [
            "Checkout exact revision",
            "Verify exact revision identity",
            "Verify workflow contracts",
            "Reverify official OpenSLR archive bytes",
            "Upload bounded materialization observation",
        ],
        "materialization step order drift",
    )
    require_exact_mapping(
        steps["Checkout exact revision"],
        {"name": "Checkout exact revision", "uses": "actions/checkout@v4", "with": {"ref": "${{ env.B2P02_REVISION }}"}},
        "materialization checkout step",
    )
    require_exact_mapping(
        steps["Verify exact revision identity"],
        {
            "name": "Verify exact revision identity",
            "run": 'test "$(git rev-parse HEAD)" = "$B2P02_REVISION"\necho "B2P02_REVISION=$B2P02_REVISION"',
        },
        "materialization identity step",
    )
    require_exact_mapping(
        steps["Verify workflow contracts"],
        {"name": "Verify workflow contracts", "run": "python research/000b2-public/verify_workflow_contracts.py"},
        "materialization workflow-contract step",
    )
    require_exact_mapping(
        steps["Reverify official OpenSLR archive bytes"],
        {
            "name": "Reverify official OpenSLR archive bytes",
            "run": 'mkdir -p "$RUNNER_TEMP/b2p02/work"\npython research/000b2-public/materialize_archives.py \\\n  --work-dir "$RUNNER_TEMP/b2p02/work" \\\n  --output "$RUNNER_TEMP/b2p02/archive-materialization.json"',
        },
        "materialization archive step",
    )
    require_exact_mapping(
        steps["Upload bounded materialization observation"],
        {
            "name": "Upload bounded materialization observation",
            "uses": "actions/upload-artifact@v4",
            "with": {
                "name": "b2p02-archive-materialization-${{ env.B2P02_REVISION }}",
                "path": "${{ runner.temp }}/b2p02/archive-materialization.json",
                "if-no-files-found": "error",
                "retention-days": 7,
            },
        },
        "materialization upload step",
    )


def main() -> None:
    """Parse and structurally verify both active B2P02 workflows."""
    for path in (METHODOLOGY, MATERIALIZATION):
        require(path.is_file(), f"missing workflow: {path.relative_to(ROOT)}")
    verify_methodology(parse_workflow(METHODOLOGY))
    verify_materialization(parse_workflow(MATERIALIZATION))
    print("B2P02_WORKFLOW_CONTRACTS=PASS")
    print("METHODOLOGY_EXACT_HEAD=ENFORCED")
    print("MATERIALIZATION_EXACT_HEAD=ENFORCED")
    print("WORKFLOW_COUPLING=ENFORCED")
    print("ACTIVE_WORKFLOW_STRUCTURE=VERIFIED")


if __name__ == "__main__":
    main()
