#!/usr/bin/env python3
"""Build the exact B2R05-to-B2R06 reconciliation candidate, then remove this helper."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "f0ec8b70497769332e1ddc6053e4d32f993b5efc"
TASK_HEAD = "b1a3f5866fed1eb4df590d134322eb82904cec78"
FIRST_PARENT = "9c777ae4f4aaf8387cf54bfa4e8afe80e053ff69"
RUN_ID = 34035710870
FREEZE = "600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8"
TARGET_BRANCH = "docs/000b2-b2r05-reconciliation"
WORKFLOW_PATH = Path(".github/workflows/internal-b2r05-reconcile.yml")
HELPER_PATH = Path("research/000b2-public/internal_b2r05_reconcile.py")
FINAL_PATHS = {
    "docs/canonical/CURRENT_STATE.md",
    "research/000b2-public/recovery-readiness.json",
    "specs/000B2-public-corpus-bakeoff/tasks.md",
    "specs/CURRENT.md",
}
TEMP_PATHS = {WORKFLOW_PATH.as_posix(), HELPER_PATH.as_posix()}


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        list(args),
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def changed_from_base(*, cached: bool = False) -> set[str]:
    args = ["git", "diff"]
    if cached:
        args.append("--cached")
    args.extend(["--name-only", BASE])
    return set(run(*args, capture=True).splitlines())


def patch_readiness() -> None:
    path = ROOT / "research/000b2-public/recovery-readiness.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    require(value.get("schema_version") == "000b2-public-recovery-readiness-v2", "readiness schema drift")
    require(value.get("state") == "RECOVERY_READY", "recovery state drift")
    require(
        value.get("completed_recovery_tasks") == ["B2R01", "B2R02", "B2R03", "B2R04"],
        "completed recovery prefix drift",
    )
    require(value.get("active_recovery_unit") == "B2R05", "B2R05 is not the canonical active unit")
    require(value.get("qualified_workflow_change_paths") == [], "unexpected qualified workflow drift")
    require(
        value.get("replacement_attempt")
        == {
            "attempt_id": "000B2-PUBLIC-ATTEMPT-002",
            "required": True,
            "frozen": True,
            "primary_decode_entry_open": True,
        },
        "replacement attempt drift",
    )
    require(
        value.get("transition_proofs", [])[-1]
        == {
            "completed_task": "B2R04",
            "canonical_task_merge": "cdf8e4c13a1e17fe5e0db7bc360e5fbbeef496e0",
            "post_merge_recovery_run_id": 33998872408,
            "successor_task": "B2R05",
        },
        "B2R04 transition proof drift",
    )
    require(
        value.get("claim_guards")
        == {
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "comparative_result_available": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
        "claim guard drift",
    )
    require(
        value.get("transition_policy", {}).get("reconciliation_candidate_scope")
        == [
            "docs/canonical/CURRENT_STATE.md",
            "research/000b2-public/recovery-readiness.json",
            "specs/000B2-public-corpus-bakeoff/tasks.md",
            "specs/CURRENT.md",
        ],
        "reconciliation scope policy drift",
    )
    value["transition_proofs"].append(
        {
            "completed_task": "B2R05",
            "canonical_task_merge": BASE,
            "post_merge_recovery_run_id": RUN_ID,
            "successor_task": "B2R06",
        }
    )
    value["completed_recovery_tasks"].append("B2R05")
    value["active_recovery_unit"] = "B2R06"
    value["next_action"] = (
        "Qualify B2R06 only: execute candidate cell 2 (moonshine-balanced) under "
        "000B2-PUBLIC-ATTEMPT-002 using the canonically frozen corrected streaming C0 contract "
        "and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, "
        "exact run identity, frozen input identities, and claim guards. Keep B2R07 and every later "
        "candidate cell closed until B2R06 is canonically merged, post-merge verified, and reconciled."
    )
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def patch_tasks() -> None:
    path = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
    text = path.read_text(encoding="utf-8")
    old = "- [ ] `B2R05` Execute candidate cell 1 (`moonshine-compact`) under ATTEMPT-002 and unchanged frozen C0."
    new = "- [x] `B2R05` Execute candidate cell 1 (`moonshine-compact`) under ATTEMPT-002 and unchanged frozen C0."
    require(text.count(old) == 1, "B2R05 task marker drift")
    require(new not in text, "B2R05 already checked before reconciliation")
    require(
        "- [ ] `B2R06` Execute candidate cell 2 (`moonshine-balanced`) under ATTEMPT-002 and unchanged frozen C0."
        in text,
        "B2R06 task marker drift",
    )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_current() -> None:
    path = ROOT / "specs/CURRENT.md"
    text = path.read_text(encoding="utf-8")
    old_status = (
        "public-corpus B2 recovery active; B2R01 through B2R04 canonical and post-merge verified; "
        "active recovery unit `B2R05`; ATTEMPT-001 B2E03 and all later primary decoding closed"
    )
    new_status = (
        "public-corpus B2 recovery active; B2R01 through B2R05 canonical and post-merge verified; "
        "active recovery unit `B2R06`; ATTEMPT-001 B2E03 and all later primary decoding closed"
    )
    require(text.count(old_status) == 1, "CURRENT status marker drift")
    text = text.replace(old_status, new_status, 1)

    pattern = re.compile(
        r"## Canonical B2R04 recovery reconciliation — latest authority\n\n.*?\n## Next canonical action\n\n"
        r"Qualify `B2R05` only: execute candidate cell 1 \(`moonshine-compact`\) under `000B2-PUBLIC-ATTEMPT-002` "
        r"using the canonically frozen corrected streaming C0 contract and identical frozen public audio\. Preserve raw transcripts, failures, "
        r"runtime observations, exact run identity, frozen input identities, and claim guards\. Keep B2R06 and every later candidate cell closed "
        r"until B2R05 is separately qualified, merged, post-merge verified, and reconciled\.",
        re.S,
    )
    replacement = f"""## Canonical B2R05 recovery reconciliation — latest authority

This section is the sole current recovery-action authority in this document. B2R05 is canonically implemented at real task merge `{BASE}` from exact qualified head `{TASK_HEAD}` against first parent `{FIRST_PARENT}`. Exact task-merge push run `{RUN_ID}` of workflow `000B2 Public Corpus Attempt Recovery` (`workflow_id=350986920`, path `.github/workflows/000b2-public-attempt-recovery.yml`) completed successfully on that exact merge. The canonical B2R05 evidence remains bound to capture run `34031165041`, job `101480807527`, artifact `9989016229`, 240 frozen inputs, 209 decoded outputs, and 31 preserved frozen-C0 pre-inference >12-second rejections. No reference transcripts were loaded and no accuracy scoring or comparative ranking was performed. Historical ATTEMPT-001 bytes and the immutable recovery proof mechanism remain unchanged.

**Canonical recovery predecessor:** `B2R05`
**Canonical B2R05 recovery merge:** `{BASE}`
**Canonical B2R05 post-merge recovery run:** `{RUN_ID}`
**Active recovery unit:** `B2R06`

ATTEMPT-002 remains canonically frozen with freeze digest `{FREEZE}`, and `primary_decode_entry_open=true` only because B2R06 is the active primary-decode recovery unit. B2R06 alone is authorized after this reconciliation becomes canonical: execute candidate cell 2 (`moonshine-balanced`) against the identical frozen P0 public-human audio using the corrected Moonshine streaming C0 contract. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and all claim guards. B2R07 and every later candidate cell remain unauthorized until B2R06 is separately qualified, merged, post-merge verified, and reconciled.

## Next canonical action

Qualify `B2R06` only: execute candidate cell 2 (`moonshine-balanced`) under `000B2-PUBLIC-ATTEMPT-002` using the canonically frozen corrected streaming C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R07 and every later candidate cell closed until B2R06 is separately qualified, merged, post-merge verified, and reconciled."""
    text, count = pattern.subn(replacement, text, count=1)
    require(count == 1, "CURRENT recovery section drift")
    path.write_text(text, encoding="utf-8")


def patch_current_state() -> None:
    path = ROOT / "docs/canonical/CURRENT_STATE.md"
    text = path.read_text(encoding="utf-8")
    old_tail = (
        "B2R04 is canonical and post-merge verified at task merge `cdf8e4c13a1e17fe5e0db7bc360e5fbbeef496e0` "
        "with recovery run `33998872408`; ATTEMPT-002 is frozen; active recovery unit is `B2R05`; only B2R05 primary decode is open; "
        "ATTEMPT-001 B2E03 and all later primary decoding are closed"
    )
    new_tail = (
        f"B2R05 is canonical and post-merge verified at task merge `{BASE}` with recovery run `{RUN_ID}`; "
        "ATTEMPT-002 is frozen; active recovery unit is `B2R06`; only B2R06 primary decode is open; "
        "ATTEMPT-001 B2E03 and all later primary decoding are closed"
    )
    require(text.count(old_tail) == 1, "CURRENT_STATE status marker drift")
    text = text.replace(old_tail, new_tail, 1)

    old_next = (
        "Qualify `B2R05` only: execute candidate cell 1 (`moonshine-compact`) under `000B2-PUBLIC-ATTEMPT-002` "
        "using the canonically frozen corrected streaming C0 contract and identical frozen public audio. Preserve raw transcripts, failures, "
        "runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R06 and every later candidate cell closed "
        "until B2R05 is separately qualified, merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, "
        "historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`."
    )
    new_next = (
        "Qualify `B2R06` only: execute candidate cell 2 (`moonshine-balanced`) under `000B2-PUBLIC-ATTEMPT-002` "
        "using the canonically frozen corrected streaming C0 contract and identical frozen public audio. Preserve raw transcripts, failures, "
        "runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R07 and every later candidate cell closed "
        "until B2R06 is separately qualified, merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, "
        "historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`."
    )
    require(text.count(old_next) == 1, "CURRENT_STATE next-action marker drift")
    text = text.replace(old_next, new_next, 1)

    pattern = re.compile(r"## Canonical B2R04 recovery reconciliation — latest authority\n\n.*\Z", re.S)
    replacement = f"""## Canonical B2R05 recovery reconciliation — latest authority

This section is the sole current recovery-marker authority in this document. PR #65 merged the separately qualified B2R05 implementation as real task merge `{BASE}` from exact final head `{TASK_HEAD}` against first parent `{FIRST_PARENT}`. The final five-file task diff preserved all four reconciliation-authority files, the immutable recovery proof workflow/verifier mechanism, workflows, and ATTEMPT-001 historical bytes. Fresh independent exact-range review on review-only PR #66 reported no actionable substantive findings on the exact task head. Exact task-merge push run `{RUN_ID}` of `000B2 Public Corpus Attempt Recovery` (`workflow_id=350986920`, path `.github/workflows/000b2-public-attempt-recovery.yml`) completed successfully with `head_sha={BASE}`.

The canonical B2R05 primary capture remains GitHub Actions run `34031165041`, job `101480807527`, artifact `9989016229`, with exact evidence file SHA-256 `c14aaae1ca974e30fee73a7d672bb20910eb9e501601020c5a3f11332d4f00f8` and canonical payload digest `254f0a8f7d0954b3c26ed01aafef8b0c061aae1ceb2fffc2f7b2a0a84aca5cfd`. It records 240 frozen inputs, 209 decoded outputs, and 31 preserved `C0HarnessError` pre-inference rejections enforcing the frozen 12-second primary utterance bound. The failures were preserved without retry or C0 change. Reference transcripts were not loaded; accuracy scoring and comparative ranking were not performed; timing remains diagnostic only.

**Canonical recovery predecessor:** `B2R05`
**Canonical B2R05 recovery merge:** `{BASE}`
**Canonical B2R05 post-merge recovery run:** `{RUN_ID}`
**Active recovery unit:** `B2R06`

ATTEMPT-001 remains historical and ineligible for comparative scoring. ATTEMPT-002 remains canonically frozen with freeze digest `{FREEZE}`. `primary_decode_entry_open=true` only for the active recovery unit B2R06. B2R06 alone is authorized after this reconciliation becomes canonical: execute candidate cell 2 (`moonshine-balanced`) against the identical frozen P0 public-human audio using the corrected Moonshine streaming C0 contract, while preserving raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and all claim guards. B2R07 and every later ATTEMPT-002 candidate cell remain unauthorized until B2R06 is separately qualified, merged, post-merge verified, and reconciled.
"""
    text, count = pattern.subn(replacement, text, count=1)
    require(count == 1, "CURRENT_STATE recovery section drift")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    os.chdir(ROOT)
    run("git", "fetch", "--force", "--no-tags", "origin", "main:refs/remotes/origin/main")
    require(run("git", "rev-parse", "refs/remotes/origin/main", capture=True) == BASE, "canonical main moved")
    bootstrap_changed = set(run("git", "diff", "--name-only", f"{BASE}...HEAD", capture=True).splitlines())
    require(bootstrap_changed == TEMP_PATHS, f"unexpected bootstrap scope: {sorted(bootstrap_changed)!r}")

    patch_readiness()
    patch_tasks()
    patch_current()
    patch_current_state()

    (ROOT / WORKFLOW_PATH).unlink()
    (ROOT / HELPER_PATH).unlink()
    require(changed_from_base() == FINAL_PATHS, f"unexpected final working scope: {sorted(changed_from_base())!r}")

    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", "-A")
    require(changed_from_base(cached=True) == FINAL_PATHS, "unexpected staged reconciliation scope")
    run("git", "commit", "-m", "docs(000b2): reconcile B2R05 and authorize B2R06")
    require(
        set(run("git", "diff", "--name-only", f"{BASE}...HEAD", capture=True).splitlines()) == FINAL_PATHS,
        "committed reconciliation scope drift",
    )

    run(
        "python",
        "-m",
        "py_compile",
        "research/000b2-public/verify_attempt_001_invalidation.py",
        "research/000b2-public/verify_b2r05.py",
        "research/000b2-public/verify_attempt_manifest.py",
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        [
            "python",
            "research/000b2-public/verify_attempt_001_invalidation.py",
            "--static-only",
            "--canonical-main-ref",
            "refs/remotes/origin/main",
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )
    subprocess.run(["python", "research/000b2-public/verify_b2r05.py"], cwd=ROOT, check=True, env=env)
    subprocess.run(["python", "research/000b2-public/verify_attempt_manifest.py"], cwd=ROOT, check=True, env=env)

    run("git", "fetch", "--force", "--no-tags", "origin", "main:refs/remotes/origin/main")
    require(run("git", "rev-parse", "refs/remotes/origin/main", capture=True) == BASE, "canonical main moved before push")
    require(
        run("git", "show", "-s", "--format=%P", BASE, capture=True) == f"{FIRST_PARENT} {TASK_HEAD}",
        "canonical B2R05 task merge parent identity drift",
    )
    candidate = run("git", "rev-parse", "HEAD", capture=True)
    print(f"B2R05_RECONCILIATION_CANDIDATE={candidate}")
    print("B2R05_RECONCILIATION_STATIC_VERIFICATION=PASS")
    run("git", "push", "origin", f"HEAD:refs/heads/{TARGET_BRANCH}")
    print("B2R05_RECONCILIATION_PUSH=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
