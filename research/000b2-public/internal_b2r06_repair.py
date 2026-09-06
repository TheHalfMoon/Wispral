#!/usr/bin/env python3
"""Repair the bounded B2R06 decoder and converge task/execution branches to identical bytes."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "04056b795a54e38d9d075e4de7aff15df1be2b3b"
TASK_BRANCH = "research/000b2-b2r06-moonshine-balanced"
EXECUTION_BRANCH = "research/000b2-b2r06-execution"
EXPECTED_TASK_HEAD = "1c831ccc8fbe8428f3ae313fbeff9763169125fb"
TARGET = Path("research/000b2-public/decode_b2r06.py")
HELPERS = {
    ".github/workflows/internal-b2r06-bootstrap.yml",
    "research/000b2-public/internal_b2r06_bootstrap.py",
    ".github/workflows/internal-b2r06-repair.yml",
    "research/000b2-public/internal_b2r06_repair.py",
}
WRONG = '''        == [
            "moonshine-balanced",
            "moonshine-balanced",
            "whispercpp-compact",
            "whispercpp-balanced",
            "sherpa-onnx-compact",
            "sherpa-onnx-balanced",
        ],'''
RIGHT = '''        == [
            "moonshine-compact",
            "moonshine-balanced",
            "whispercpp-compact",
            "whispercpp-balanced",
            "sherpa-onnx-compact",
            "sherpa-onnx-balanced",
        ],'''


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


def main() -> int:
    run("git", "fetch", "--force", "--no-tags", "origin",
        "main:refs/remotes/origin/main",
        f"{TASK_BRANCH}:refs/remotes/origin/{TASK_BRANCH}")
    require(run("git", "rev-parse", "refs/remotes/origin/main", capture=True) == BASE, "canonical main moved")
    require(run("git", "merge-base", "HEAD", BASE, capture=True) == BASE, "execution branch is not based on canonical base")
    current_scope = set(run("git", "diff", "--name-only", BASE, "HEAD", capture=True).splitlines())
    require(current_scope == HELPERS, f"unexpected pre-repair execution scope: {sorted(current_scope)!r}")
    require(run("git", "rev-parse", f"refs/remotes/origin/{TASK_BRANCH}", capture=True) == EXPECTED_TASK_HEAD,
            "task branch moved before repair")

    task_root = Path("/tmp/b2r06-task-repair")
    if task_root.exists():
        shutil.rmtree(task_root)
    run("git", "worktree", "add", "--detach", str(task_root), f"refs/remotes/origin/{TASK_BRANCH}")
    require(run("git", "diff", "--name-only", BASE, "HEAD", cwd=task_root, capture=True) == str(TARGET),
            "task branch is not decoder-only")
    task_target = task_root / TARGET
    text = task_target.read_text(encoding="utf-8")
    require(text.count(WRONG) == 1, "expected candidate-order defect not found exactly once")
    text = text.replace(WRONG, RIGHT, 1)
    require(text.count(WRONG) == 0 and text.count(RIGHT) == 1, "candidate-order repair failed")
    require('CANDIDATE_ID = "moonshine-balanced"' in text, "B2R06 candidate id drift")
    require("ModelArch.MEDIUM_STREAMING" in text, "B2R06 medium streaming architecture missing")
    require('config.get("tier") == "BALANCED"' in text, "B2R06 balanced tier guard missing")
    require('"b2r07_authorized": False' in text, "B2R07 closure guard missing")
    compile(text, str(TARGET), "exec")
    task_target.write_text(text, encoding="utf-8")
    run("git", "config", "user.name", "github-actions[bot]", cwd=task_root)
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com", cwd=task_root)
    run("git", "add", str(TARGET), cwd=task_root)
    require(run("git", "diff", "--cached", "--name-only", BASE, capture=True, cwd=task_root) == str(TARGET),
            "task repair escaped decoder-only scope")
    run("git", "commit", "-m", "fix(000b2): preserve frozen B2R06 candidate order", cwd=task_root)
    task_head = run("git", "rev-parse", "HEAD", cwd=task_root, capture=True)
    task_blob = run("git", "rev-parse", f"HEAD:{TARGET}", cwd=task_root, capture=True)
    run("git", "push", "origin", f"HEAD:refs/heads/{TASK_BRANCH}", cwd=task_root)

    shutil.copyfile(task_target, ROOT / TARGET)
    for helper in HELPERS:
        path = ROOT / helper
        if path.exists():
            path.unlink()
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", "-A")
    final_scope = set(run("git", "diff", "--cached", "--name-only", BASE, capture=True).splitlines())
    require(final_scope == {str(TARGET)}, f"execution repair residue: {sorted(final_scope)!r}")
    run("git", "commit", "-m", "research(000b2): implement repaired B2R06 streaming decoder")
    execution_head = run("git", "rev-parse", "HEAD", capture=True)
    execution_blob = run("git", "rev-parse", f"HEAD:{TARGET}", capture=True)
    require(execution_blob == task_blob, "task/execution decoder blob mismatch")
    run("git", "push", "origin", f"HEAD:refs/heads/{EXECUTION_BRANCH}")

    print(f"B2R06_TASK_HEAD={task_head}")
    print(f"B2R06_EXECUTION_HEAD={execution_head}")
    print(f"B2R06_DECODER_BLOB={task_blob}")
    print("B2R06_REPAIR=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
