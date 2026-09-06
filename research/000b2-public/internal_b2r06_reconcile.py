#!/usr/bin/env python3
"""Build the exact four-file B2R06-to-B2R07 recovery reconciliation candidate."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "2460eae15260423b3a06d50d9119ae2459ff41c7"
TASK_HEAD = "d8cfb5d5d4c5ef13483991ae2a1a6d2c5ae04a7d"
POST_RUN = 34043039708
BRANCH = "docs/000b2-b2r06-reconciliation"
HELPER = Path("research/000b2-public/internal_b2r06_reconcile.py")
WORKFLOW = Path(".github/workflows/internal-b2r06-reconcile.yml")
ALLOWED = {
    "docs/canonical/CURRENT_STATE.md",
    "research/000b2-public/recovery-readiness.json",
    "specs/000B2-public-corpus-bakeoff/tasks.md",
    "specs/CURRENT.md",
}
NEXT_MARKDOWN = (
    "Qualify `B2R07` only: execute candidate cell 3 (`whispercpp-compact`) under "
    "`000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. "
    "Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, "
    "and claim guards. Keep B2R08 and every later candidate cell closed until B2R07 is canonically merged, "
    "post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, "
    "historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and "
    "`product_code_authorized=false`."
)
NEXT_MACHINE = (
    "Qualify B2R07 only: execute candidate cell 3 (whispercpp-compact) under 000B2-PUBLIC-ATTEMPT-002 "
    "using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, "
    "runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R08 and every later "
    "candidate cell closed until B2R07 is canonically merged, post-merge verified, and reconciled."
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
    require(text.count(old) == 1, f"{label}: expected one occurrence, found {text.count(old)}")
    return text.replace(old, new, 1)


def replace_next_action(text: str, label: str) -> str:
    marker = "## Next canonical action\n\n"
    require(text.count(marker) == 1, f"{label}: next-action marker drift")
    start = text.index(marker) + len(marker)
    end = text.find("\n\n", start)
    if end == -1:
        end = len(text)
    current = text[start:end]
    require(current.startswith("Qualify `B2R06` only:"), f"{label}: B2R06 next action drift")
    return text[:start] + NEXT_MARKDOWN + text[end:]


def validate_post_run() -> None:
    repository = os.environ.get("GITHUB_REPOSITORY")
    require(repository == "TheHalfMoon/Wispral", "repository identity drift")
    payload = run("gh", "api", f"repos/{repository}/actions/runs/{POST_RUN}", capture=True)
    value = json.loads(payload)
    require(value.get("workflow_id") == 350986920, "post-merge Recovery workflow id drift")
    require(value.get("path") == ".github/workflows/000b2-public-attempt-recovery.yml", "Recovery workflow path drift")
    require(value.get("name") == "000B2 Public Corpus Attempt Recovery", "Recovery workflow name drift")
    require(value.get("event") == "push", "Recovery proof is not a push run")
    require(value.get("status") == "completed" and value.get("conclusion") == "success", "Recovery proof is not successful")
    require(value.get("head_sha") == BASE, "Recovery proof head SHA drift")


def update_readiness() -> None:
    path = ROOT / "research/000b2-public/recovery-readiness.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    require(value.get("completed_recovery_tasks") == ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05"], "completed recovery prefix drift")
    require(value.get("active_recovery_unit") == "B2R06", "active recovery unit is not B2R06")
    require(value.get("qualified_workflow_change_paths") == [], "workflow drift unexpectedly authorized")
    require(str(value.get("next_action", "")).startswith("Qualify B2R06 only:"), "machine next-action drift")
    proofs = value.get("transition_proofs")
    require(isinstance(proofs, list) and len(proofs) == 5 and proofs[-1].get("completed_task") == "B2R05", "transition proof prefix drift")
    proofs.append({
        "completed_task": "B2R06",
        "canonical_task_merge": BASE,
        "post_merge_recovery_run_id": POST_RUN,
        "successor_task": "B2R07",
    })
    value["completed_recovery_tasks"].append("B2R06")
    value["active_recovery_unit"] = "B2R07"
    value["next_action"] = NEXT_MACHINE
    expected_guards = {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
    }
    require(value.get("claim_guards") == expected_guards, "claim guards drift")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_tasks() -> None:
    path = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
    text = path.read_text(encoding="utf-8")
    old = "- [ ] `B2R06` Execute candidate cell 2 (`moonshine-balanced`) under ATTEMPT-002 and unchanged frozen C0."
    new = "- [x] `B2R06` Execute candidate cell 2 (`moonshine-balanced`) under ATTEMPT-002 and unchanged frozen C0."
    text = replace_once(text, old, new, "tasks B2R06")
    require("- [ ] `B2R07` Execute candidate cell 3 (`whispercpp-compact`) under ATTEMPT-002 and unchanged frozen C0." in text, "B2R07 task boundary drift")
    require("- [ ] `B2R08`" in text, "B2R08 successor boundary drift")
    path.write_text(text, encoding="utf-8")


def reconciliation_section(authority_word: str) -> str:
    return f'''\n\n## Canonical B2R06 recovery reconciliation — latest authority\n\nThis section is the sole current recovery-{authority_word} authority in this document. PR #69 merged the separately qualified B2R06 implementation and sealed evidence as real task merge `{BASE}` from exact final head `{TASK_HEAD}` against first parent `04056b795a54e38d9d075e4de7aff15df1be2b3b`. The final five-file task diff preserved all four reconciliation-authority files, the immutable recovery proof workflow/verifier mechanism, all permanent workflows, the frozen scoring/normalization contract, and ATTEMPT-001 historical bytes. Fresh independent exact-range review on review-only PR #70 reported no actionable substantive findings on the exact task head. Exact task-merge push run `{POST_RUN}` of `000B2 Public Corpus Attempt Recovery` (`workflow_id=350986920`, path `.github/workflows/000b2-public-attempt-recovery.yml`) completed successfully with `head_sha={BASE}`.\n\nThe canonical B2R06 primary capture remains GitHub Actions run `34041046129`, job `101507742625`, artifact `9992059464`, with artifact ZIP SHA-256 `8d4961084e5c33339cb0317e0387e8856d7d138abad18e204c2adea3715174cb`, exact evidence file SHA-256 `055a93c9a9f15193ffcf8edd7618648f9849f077c8b4c1b49edb9f91d023b722`, and canonical payload digest `2b069cf7dbc4eb8ec50c641c2d05e78054cace513d794ebd2f84eefe784f3b38`. It records 240 frozen inputs, 209 decoded outputs, and 31 preserved `C0HarnessError` pre-inference rejections enforcing the frozen 12-second primary utterance bound. The failures were preserved without retry or C0 change. Reference transcripts were not loaded; accuracy scoring and comparative ranking were not performed; timing remains diagnostic only.\n\n**Canonical recovery predecessor:** `B2R06`\n**Canonical B2R06 recovery merge:** `{BASE}`\n**Canonical B2R06 post-merge recovery run:** `{POST_RUN}`\n**Active recovery unit:** `B2R07`\n\nATTEMPT-001 remains historical and ineligible for comparative scoring. ATTEMPT-002 remains canonically frozen with freeze digest `600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8`. `primary_decode_entry_open=true` only for the active recovery unit B2R07. B2R07 alone is authorized after this reconciliation becomes canonical: execute candidate cell 3 (`whispercpp-compact`) against the identical frozen P0 public-human audio using the unchanged frozen C0 contract, while preserving raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and all claim guards. B2R08 and every later ATTEMPT-002 candidate cell remain unauthorized until B2R07 is separately qualified, merged, post-merge verified, and reconciled.\n'''


def update_specs_current() -> None:
    path = ROOT / "specs/CURRENT.md"
    text = path.read_text(encoding="utf-8")
    text = replace_next_action(text, str(path.relative_to(ROOT)))
    text = replace_once(
        text,
        "B2R01 through B2R05 canonical and post-merge verified; active recovery unit `B2R06`",
        "B2R01 through B2R06 canonical and post-merge verified; active recovery unit `B2R07`",
        "CURRENT status",
    )
    text = text.replace("The latest B2R04 reconciliation block below", "The latest B2R06 reconciliation block below")
    old_title = "## Canonical B2R05 recovery reconciliation — latest authority"
    text = replace_once(text, old_title, "## Canonical B2R05 recovery reconciliation — predecessor authority", "CURRENT predecessor title")
    text = replace_once(
        text,
        "This section is the sole current recovery-action authority in this document.",
        "This section records predecessor authority superseded by the canonical B2R06 reconciliation below.",
        "CURRENT predecessor sentence",
    )
    require("## Canonical B2R06 recovery reconciliation — latest authority" not in text, "CURRENT B2R06 section already present")
    marker = "\n## Next canonical action\n"
    require(text.count(marker) == 1, "CURRENT next-action section count drift")
    index = text.index(marker)
    text = text[:index].rstrip() + reconciliation_section("action") + text[index:]
    path.write_text(text, encoding="utf-8")


def update_canonical_current() -> None:
    path = ROOT / "docs/canonical/CURRENT_STATE.md"
    text = path.read_text(encoding="utf-8")
    text = replace_next_action(text, str(path.relative_to(ROOT)))
    text = replace_once(
        text,
        "B2R05 is canonical and post-merge verified at task merge `f0ec8b70497769332e1ddc6053e4d32f993b5efc` with recovery run `34035710870`; ATTEMPT-002 is frozen; active recovery unit is `B2R06`; only B2R06 primary decode is open;",
        f"B2R06 is canonical and post-merge verified at task merge `{BASE}` with recovery run `{POST_RUN}`; ATTEMPT-002 is frozen; active recovery unit is `B2R07`; only B2R07 primary decode is open;",
        "canonical summary frontier",
    )
    text = replace_once(
        text,
        "ATTEMPT-002 is frozen with freeze digest `600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8`; B2R05 is the sole current recovery unit and sole open primary-decode entry; no comparative scoring or ranking is available; and no production STT is selected.",
        f"ATTEMPT-002 is frozen with freeze digest `600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8`; B2R05 and B2R06 are canonical and post-merge verified, with B2R06 task merge `{BASE}` and recovery run `{POST_RUN}`; B2R07 is the sole current recovery unit and sole open primary-decode entry; no comparative scoring or ranking is available; and no production STT is selected.",
        "canonical established frontier",
    )
    text = text.replace("Current authority is the B2R04 reconciliation block below.", "Current authority is the B2R06 reconciliation block below.")
    old_title = "## Canonical B2R05 recovery reconciliation — latest authority"
    text = replace_once(text, old_title, "## Canonical B2R05 recovery reconciliation — predecessor authority", "canonical predecessor title")
    text = replace_once(
        text,
        "This section is the sole current recovery-marker authority in this document.",
        "This section records predecessor authority superseded by the canonical B2R06 reconciliation below.",
        "canonical predecessor sentence",
    )
    require("## Canonical B2R06 recovery reconciliation — latest authority" not in text, "canonical B2R06 section already present")
    text = text.rstrip() + reconciliation_section("marker")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    os.chdir(ROOT)
    run("git", "fetch", "--force", "--no-tags", "origin", "main:refs/remotes/origin/main")
    require(run("git", "rev-parse", "refs/remotes/origin/main", capture=True) == BASE, "canonical main moved before reconciliation")
    require(run("git", "merge-base", "HEAD", BASE, capture=True) == BASE, "reconciliation helper branch base drift")
    pre = set(run("git", "diff", "--name-only", f"{BASE}...HEAD", capture=True).splitlines())
    require(pre == {str(HELPER), str(WORKFLOW)}, f"unexpected pre-reconciliation helper scope: {sorted(pre)!r}")
    validate_post_run()
    update_readiness()
    update_tasks()
    update_specs_current()
    update_canonical_current()

    (ROOT / HELPER).unlink()
    (ROOT / WORKFLOW).unlink()

    run("python", "research/000b2-public/verify_b2r06.py")
    run("python", "research/000b2-public/verify_attempt_manifest.py")
    run("git", "diff", "--check", BASE)
    changed = set(run("git", "diff", "--name-only", BASE, capture=True).splitlines())
    require(changed == ALLOWED, f"reconciliation scope drift: {sorted(changed)!r}")

    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", *sorted(ALLOWED), str(HELPER), str(WORKFLOW))
    staged = set(run("git", "diff", "--cached", "--name-only", BASE, capture=True).splitlines())
    require(staged == ALLOWED, f"staged reconciliation scope drift: {sorted(staged)!r}")
    run("git", "commit", "-m", "docs(000b2): reconcile B2R06 and authorize B2R07")
    head = run("git", "rev-parse", "HEAD", capture=True)
    run("git", "push", "origin", f"HEAD:refs/heads/{BRANCH}")
    print(f"B2R06_RECONCILIATION_HEAD={head}")
    print("B2R06_RECONCILIATION_SCOPE=PASS")
    print("B2R07_AUTHORIZED_BY_CANDIDATE=YES_PENDING_CANONICAL_MERGE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
