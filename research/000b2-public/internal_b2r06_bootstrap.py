#!/usr/bin/env python3
"""Generate the exact B2R06 decoder from the reviewed B2R05 streaming decoder."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "04056b795a54e38d9d075e4de7aff15df1be2b3b"
EXECUTION_BRANCH = "research/000b2-b2r06-execution"
TASK_BRANCH = "research/000b2-b2r06-moonshine-balanced"
SOURCE = ROOT / "research/000b2-public/decode_b2r05.py"
TARGET = ROOT / "research/000b2-public/decode_b2r06.py"
BOOTSTRAP = ROOT / "research/000b2-public/internal_b2r06_bootstrap.py"
WORKFLOW = ROOT / ".github/workflows/internal-b2r06-bootstrap.yml"
TEMP_PATHS = {str(BOOTSTRAP.relative_to(ROOT)), str(WORKFLOW.relative_to(ROOT))}


def run(*args: str, cwd: Path = ROOT, capture: bool = False) -> str:
    result = subprocess.run(
        list(args), cwd=cwd, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def replace_exact(text: str, old: str, new: str, *, count: int) -> str:
    observed = text.count(old)
    require(observed == count, f"replacement count drift for {old!r}: {observed} != {count}")
    return text.replace(old, new)


def generate() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    text = replace_exact(text, "B2R05", "B2R06", count=text.count("B2R05"))
    text = replace_exact(text, "b2r05", "b2r06", count=text.count("b2r05"))
    text = replace_exact(text, "moonshine-compact", "moonshine-balanced", count=text.count("moonshine-compact"))
    text = replace_exact(text, "COMPACT", "BALANCED", count=text.count("COMPACT"))
    text = replace_exact(text, "ModelArch.SMALL_STREAMING", "ModelArch.MEDIUM_STREAMING", count=1)
    text = replace_exact(text, '"cell_index": 1', '"cell_index": 2', count=1)
    text = replace_exact(text, "candidate cell 1", "candidate cell 2", count=text.count("candidate cell 1"))
    text = replace_exact(
        text,
        'EXPECTED_AUTHORITY_BASE = "9c777ae4f4aaf8387cf54bfa4e8afe80e053ff69"',
        f'EXPECTED_AUTHORITY_BASE = "{BASE}"',
        count=1,
    )
    text = replace_exact(
        text,
        'readiness.get("completed_recovery_tasks") == ["B2R01", "B2R02", "B2R03", "B2R04"]',
        'readiness.get("completed_recovery_tasks") == ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05"]',
        count=1,
    )
    text = replace_exact(text, '"b2r06_authorized": False', '"b2r07_authorized": False', count=1)

    anchor = '    require(readiness.get("active_recovery_unit") == TASK, "B2R06 is not the active recovery unit")\n'
    require(text.count(anchor) == 1, "active-unit anchor drift")
    insertion = anchor + '''    next_action = readiness.get("next_action")
    require(isinstance(next_action, str) and next_action.startswith("Qualify B2R06 only:"), "B2R06 next-action authority drift")
    require("moonshine-balanced" in next_action, "B2R06 candidate identity missing from next action")
    require("Keep B2R07" in next_action, "B2R07 successor boundary missing from next action")
    tasks = (ROOT / "specs" / "000B2-public-corpus-bakeoff" / "tasks.md").read_text(encoding="utf-8")
    current = (ROOT / "specs" / "CURRENT.md").read_text(encoding="utf-8")
    canonical_current = (ROOT / "docs" / "canonical" / "CURRENT_STATE.md").read_text(encoding="utf-8")
    require("- [x] `B2R05`" in tasks, "B2R05 predecessor task is not complete")
    require("- [ ] `B2R06`" in tasks, "B2R06 task is not open")
    require("- [ ] `B2R07`" in tasks, "B2R07 task boundary drift")
    require("active recovery unit `B2R06`" in current, "CURRENT does not own B2R06 frontier")
    require("**Active recovery unit:** `B2R06`" in canonical_current, "canonical CURRENT_STATE does not own B2R06 frontier")
'''
    text = text.replace(anchor, insertion, 1)

    require("transcribe_without_streaming" not in text, "non-streaming decode leaked into B2R06")
    require("ModelArch.MEDIUM_STREAMING" in text, "medium streaming architecture missing")
    require("moonshine-balanced" in text and "moonshine-compact" not in text, "candidate identity drift")
    require('"b2r07_authorized": False' in text, "B2R07 guard missing")
    require("B2R05" in text, "B2R05 predecessor completion was not preserved")
    return text


def main() -> int:
    os.chdir(ROOT)
    run("git", "fetch", "--force", "--no-tags", "origin", "main:refs/remotes/origin/main")
    require(run("git", "rev-parse", "refs/remotes/origin/main", capture=True) == BASE, "canonical main moved")
    require(run("git", "merge-base", "HEAD", BASE, capture=True) == BASE, "bootstrap does not descend from canonical main")
    bootstrap_scope = set(run("git", "diff", "--name-only", f"{BASE}...HEAD", capture=True).splitlines())
    require(bootstrap_scope == TEMP_PATHS, f"unexpected bootstrap scope: {sorted(bootstrap_scope)!r}")

    generated = generate()
    digest = hashlib.sha256(generated.encode("utf-8")).hexdigest()
    TARGET.write_text(generated, encoding="utf-8")
    run("python", "-m", "py_compile", str(TARGET.relative_to(ROOT)))

    task_root = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "b2r06-task"
    if task_root.exists():
        shutil.rmtree(task_root)
    run("git", "fetch", "--force", "--no-tags", "origin", f"{TASK_BRANCH}:refs/remotes/origin/{TASK_BRANCH}")
    run("git", "worktree", "add", "--detach", str(task_root), f"refs/remotes/origin/{TASK_BRANCH}")
    require(run("git", "rev-parse", "HEAD", cwd=task_root, capture=True) == BASE, "task branch base drift")
    task_target = task_root / TARGET.relative_to(ROOT)
    task_target.parent.mkdir(parents=True, exist_ok=True)
    task_target.write_text(generated, encoding="utf-8")
    run("python", "-m", "py_compile", str(TARGET.relative_to(ROOT)), cwd=task_root)
    run("git", "config", "user.name", "github-actions[bot]", cwd=task_root)
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com", cwd=task_root)
    run("git", "add", str(TARGET.relative_to(ROOT)), cwd=task_root)
    run("git", "commit", "-m", "research(000b2): implement B2R06 streaming decoder", cwd=task_root)
    task_head = run("git", "rev-parse", "HEAD", cwd=task_root, capture=True)
    task_blob = run("git", "rev-parse", f"HEAD:{TARGET.relative_to(ROOT)}", cwd=task_root, capture=True)
    run("git", "push", "origin", f"HEAD:refs/heads/{TASK_BRANCH}", cwd=task_root)

    WORKFLOW.unlink()
    BOOTSTRAP.unlink()
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", "-A")
    changed = set(run("git", "diff", "--cached", "--name-only", BASE, capture=True).splitlines())
    require(changed == {str(TARGET.relative_to(ROOT))}, f"execution bootstrap residue: {sorted(changed)!r}")
    run("git", "commit", "-m", "research(000b2): implement B2R06 streaming decoder")
    execution_head = run("git", "rev-parse", "HEAD", capture=True)
    execution_blob = run("git", "rev-parse", f"HEAD:{TARGET.relative_to(ROOT)}", capture=True)
    require(task_blob == execution_blob, "task/execution decoder blob mismatch")
    run("git", "push", "origin", f"HEAD:refs/heads/{EXECUTION_BRANCH}")

    print(f"B2R06_DECODER_SHA256={digest}")
    print(f"B2R06_DECODER_BLOB={execution_blob}")
    print(f"B2R06_TASK_HEAD={task_head}")
    print(f"B2R06_EXECUTION_HEAD={execution_head}")
    print("B2R06_BOOTSTRAP=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
