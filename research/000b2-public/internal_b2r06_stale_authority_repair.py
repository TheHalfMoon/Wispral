#!/usr/bin/env python3
"""Repair stale B2R04/B2R05 current-authority wording in B2R06 reconciliation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "2460eae15260423b3a06d50d9119ae2459ff41c7"
BRANCH = "docs/000b2-b2r06-reconciliation"
HELPER = Path("research/000b2-public/internal_b2r06_stale_authority_repair.py")
WORKFLOW = Path(".github/workflows/internal-b2r06-stale-authority-repair.yml")
CURRENT = Path("specs/CURRENT.md")
ALLOWED = {
    "docs/canonical/CURRENT_STATE.md",
    "research/000b2-public/recovery-readiness.json",
    "specs/000B2-public-corpus-bakeoff/tasks.md",
    "specs/CURRENT.md",
}

OLD_ACTIVE = (
    "B2R04 is canonical and post-merge verified at task merge `cdf8e4c13a1e17fe5e0db7bc360e5fbbeef496e0` "
    "with exact recovery run `33998872408`; this reconciliation makes B2R05 the sole current bounded recovery unit. "
    "ATTEMPT-002 is canonically frozen and primary decode entry is open only for B2R05; B2R06 and every later cell remain closed."
)
NEW_ACTIVE = (
    "B2R06 is canonical and post-merge verified at task merge `2460eae15260423b3a06d50d9119ae2459ff41c7` "
    "with exact recovery run `34043039708`; this reconciliation makes B2R07 the sole current bounded recovery unit. "
    "ATTEMPT-002 is canonically frozen and primary decode entry is open only for B2R07; B2R08 and every later cell remain closed."
)
OLD_SUMMARY = (
    "B2R04 is canonical and post-merge verified at task merge `cdf8e4c13a1e17fe5e0db7bc360e5fbbeef496e0`, "
    "and this reconciliation advances current recovery authority to B2R05 only with ATTEMPT-002 frozen."
)
NEW_SUMMARY = (
    "B2R06 is canonical and post-merge verified at task merge `2460eae15260423b3a06d50d9119ae2459ff41c7` "
    "with exact recovery run `34043039708`, and this reconciliation advances current recovery authority to B2R07 only with ATTEMPT-002 frozen."
)


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        list(args), cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected exactly one stale occurrence, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    run("git", "fetch", "--force", "--no-tags", "origin", "main:refs/remotes/origin/main")
    require(run("git", "rev-parse", "refs/remotes/origin/main", capture=True) == BASE, "canonical main moved before repair")
    pre = set(run("git", "diff", "--name-only", f"{BASE}...HEAD", capture=True).splitlines())
    require(pre == ALLOWED | {str(HELPER), str(WORKFLOW)}, f"unexpected pre-repair scope: {sorted(pre)!r}")

    path = ROOT / CURRENT
    text = path.read_text(encoding="utf-8")
    require("latest B2R06 recovery markers below supersede them for new execution" in text, "historical snapshot supersession repair missing")
    require("latest B2R04 recovery markers below supersede them for new execution" not in text, "stale B2R04 snapshot authority remains")
    text = replace_once(text, OLD_ACTIVE, NEW_ACTIVE, "active execution successor")
    text = replace_once(text, OLD_SUMMARY, NEW_SUMMARY, "B2 status summary")
    path.write_text(text, encoding="utf-8")

    (ROOT / HELPER).unlink()
    (ROOT / WORKFLOW).unlink()

    run("python", "research/000b2-public/verify_b2r06.py")
    run("python", "research/000b2-public/verify_attempt_manifest.py")
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    run("git", "diff", "--check", BASE)
    changed = set(run("git", "diff", "--name-only", BASE, capture=True).splitlines())
    require(changed == ALLOWED, f"final reconciliation scope drift: {sorted(changed)!r}")

    final_text = path.read_text(encoding="utf-8")
    for stale in (
        "this reconciliation makes B2R05 the sole current bounded recovery unit",
        "this reconciliation advances current recovery authority to B2R05 only",
        "latest B2R04 recovery markers below supersede them for new execution",
    ):
        require(stale not in final_text, f"stale authority remains: {stale}")
    require("this reconciliation makes B2R07 the sole current bounded recovery unit" in final_text, "B2R07 active authority missing")
    require("this reconciliation advances current recovery authority to B2R07 only" in final_text, "B2R07 summary authority missing")

    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", "-A")
    staged = set(run("git", "diff", "--cached", "--name-only", BASE, capture=True).splitlines())
    require(staged == ALLOWED, f"staged repair scope drift: {sorted(staged)!r}")
    run("git", "commit", "-m", "docs(000b2): remove stale B2R05 recovery authority")
    head = run("git", "rev-parse", "HEAD", capture=True)
    run("git", "push", "origin", f"HEAD:refs/heads/{BRANCH}")
    print(f"B2R06_RECONCILIATION_REPAIRED_HEAD={head}")
    print("B2R06_STALE_AUTHORITY_REPAIR=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
