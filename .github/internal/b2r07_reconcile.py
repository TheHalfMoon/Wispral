#!/usr/bin/env python3
"""Build the B2R07 -> B2R08 four-file reconciliation candidate."""

from __future__ import annotations

import json
from pathlib import Path

TASK_MERGE = "5ea5a513db5ec9c13739510061ca82faa84a0018"
TASK_HEAD = "704a0998e15562e4b22467b7a99d23de85737e1f"
RECOVERY_RUN = 34065234517
RECOVERY_JOB = 101572717810
WORKFLOW_ID = 350986920


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one match, found {count}"
    return text.replace(old, new, 1)


def update_readiness() -> None:
    path = Path("research/000b2-public/recovery-readiness.json")
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["state"] == "RECOVERY_READY"
    assert value["active_recovery_unit"] == "B2R07"
    assert value["completed_recovery_tasks"] == ["B2R01", "B2R02", "B2R03", "B2R04", "B2R05", "B2R06"]
    assert value["transition_proofs"][-1] == {
        "completed_task": "B2R06",
        "canonical_task_merge": "2460eae15260423b3a06d50d9119ae2459ff41c7",
        "post_merge_recovery_run_id": 34043039708,
        "successor_task": "B2R07",
    }
    assert value["qualified_workflow_change_paths"] == []
    assert value["claim_guards"] == {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
    }
    value["transition_proofs"].append({
        "completed_task": "B2R07",
        "canonical_task_merge": TASK_MERGE,
        "post_merge_recovery_run_id": RECOVERY_RUN,
        "successor_task": "B2R08",
    })
    value["completed_recovery_tasks"].append("B2R07")
    value["active_recovery_unit"] = "B2R08"
    value["next_action"] = (
        "Qualify B2R08 only: execute candidate cell 4 (whispercpp-balanced) under "
        "000B2-PUBLIC-ATTEMPT-002 using the unchanged frozen C0 contract and identical frozen public audio. "
        "Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, "
        "and claim guards. Keep B2R09 and every later candidate cell closed until B2R08 is canonically merged, "
        "post-merge verified, and reconciled."
    )
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def update_tasks() -> None:
    path = Path("specs/000B2-public-corpus-bakeoff/tasks.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "- [ ] `B2R07` Execute candidate cell 3 (`whispercpp-compact`) under ATTEMPT-002 and unchanged frozen C0.",
        "- [x] `B2R07` Execute candidate cell 3 (`whispercpp-compact`) under ATTEMPT-002 and unchanged frozen C0.",
        "tasks B2R07",
    )
    assert "- [ ] `B2R08` Execute candidate cell 4 (`whispercpp-balanced`)" in text
    assert "- [ ] `B2R09` Execute candidate cell 5 (`sherpa-onnx-compact`)" in text
    path.write_text(text, encoding="utf-8")


def reconciliation_block() -> str:
    return f"""## Canonical B2R07 recovery reconciliation — latest authority

This section is the sole current recovery-action authority in this document. PR #74 merged the separately qualified B2R07 implementation and sealed evidence as real task merge `{TASK_MERGE}` from exact final head `{TASK_HEAD}` against first parent `16104eacf2d571276452d173ddb54c089faccd0e`. The final eight-file task diff preserved all four reconciliation-authority files and contained no workflow file. Fresh independent exact-range CodeRabbit review on review-only PR #75 reported no actionable substantive correctness, security, evidence-integrity, or governance findings on the exact task head. Exact task-merge push run `{RECOVERY_RUN}` of `000B2 Public Corpus Attempt Recovery` (`workflow_id={WORKFLOW_ID}`, path `.github/workflows/000b2-public-attempt-recovery.yml`, job `{RECOVERY_JOB}`) completed successfully with `head_sha={TASK_MERGE}`.

The canonical B2R07 primary capture remains GitHub Actions run `34058440043`, job `101554521526`, artifact `9998344092`, with artifact ZIP SHA-256 `5991299b3349e8f53c199d1843a8304f63162443bc20faf1ebe871965890bfe3`, exact evidence file SHA-256 `80b9a21377bfd5a52f19b6f54cb1c8b933cb095c8daa3bb94081841f935dd73a`, and canonical payload digest `53a4b3597483e04ec140b7ccbe3bd4352c291fcd470480159a995a6b9ca5b5fd`. It records 240 frozen inputs, 240 decoded outputs, and zero failures. The first primary run `34053187435` timed out only at the 5400-second execution wall-clock guard and exposed no transcript or evidence JSON; the forward-only repair widened only that wall-clock allowance to 10800 seconds before any result inspection, without changing C0 controls, candidate/input order, adapter invocation count, process partitioning, model identity, or scoring semantics. Reference transcripts were not loaded; accuracy scoring and comparative ranking were not performed; timing remains diagnostic only.

**Canonical recovery predecessor:** `B2R07`
**Canonical B2R07 recovery merge:** `{TASK_MERGE}`
**Canonical B2R07 post-merge recovery run:** `{RECOVERY_RUN}`
**Active recovery unit:** `B2R08`

ATTEMPT-001 remains historical and ineligible for comparative scoring. ATTEMPT-002 remains canonically frozen with freeze digest `600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8`. `primary_decode_entry_open=true` only for the active recovery unit B2R08. B2R08 alone is authorized after this reconciliation becomes canonical: execute candidate cell 4 (`whispercpp-balanced`) against the identical frozen P0 public-human audio using the unchanged frozen C0 contract, while preserving raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and all claim guards. B2R09 and every later ATTEMPT-002 candidate cell remain unauthorized until B2R08 is separately qualified, merged, post-merge verified, and reconciled.

"""


def update_current() -> None:
    path = Path("specs/CURRENT.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(text,
        "**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 recovery active; B2R01 through B2R06 canonical and post-merge verified; active recovery unit `B2R07`; ATTEMPT-001 B2E03 and all later primary decoding closed",
        "**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 recovery active; B2R01 through B2R07 canonical and post-merge verified; active recovery unit `B2R08`; ATTEMPT-001 B2E03 and all later primary decoding closed",
        "CURRENT status")
    text = replace_once(text,
        "B2R06 is canonical and post-merge verified at task merge `2460eae15260423b3a06d50d9119ae2459ff41c7` with exact recovery run `34043039708`; this reconciliation makes B2R07 the sole current bounded recovery unit. ATTEMPT-002 is canonically frozen and primary decode entry is open only for B2R07; B2R08 and every later cell remain closed.",
        f"B2R07 is canonical and post-merge verified at task merge `{TASK_MERGE}` with exact recovery run `{RECOVERY_RUN}`; this reconciliation makes B2R08 the sole current bounded recovery unit. ATTEMPT-002 is canonically frozen and primary decode entry is open only for B2R08; B2R09 and every later cell remain closed.",
        "CURRENT summary")
    text = replace_once(text,
        "B2R06 is canonical and post-merge verified at task merge `2460eae15260423b3a06d50d9119ae2459ff41c7` with exact recovery run `34043039708`, and this reconciliation advances current recovery authority to B2R07 only with ATTEMPT-002 frozen.",
        f"B2R07 is canonical and post-merge verified at task merge `{TASK_MERGE}` with exact recovery run `{RECOVERY_RUN}`, and this reconciliation advances current recovery authority to B2R08 only with ATTEMPT-002 frozen.",
        "CURRENT P0")
    text = text.replace("latest B2R06 recovery markers below", "latest B2R07 recovery markers below")
    text = text.replace("latest B2R06 reconciliation block below", "latest B2R07 reconciliation block below")
    text = replace_once(text, "## Canonical B2R06 recovery reconciliation — latest authority", "## Canonical B2R06 recovery reconciliation — predecessor authority", "CURRENT B2R06 header")
    text = replace_once(text, "This section is the sole current recovery-action authority in this document.", "This section records predecessor authority superseded by the canonical B2R07 reconciliation below.", "CURRENT authority")
    marker = "## Next canonical action\n\n"
    assert text.count(marker) == 1
    text = text.replace(marker, reconciliation_block() + marker, 1)
    text = replace_once(text,
        "Qualify `B2R07` only: execute candidate cell 3 (`whispercpp-compact`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R08 and every later candidate cell closed until B2R07 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "Qualify `B2R08` only: execute candidate cell 4 (`whispercpp-balanced`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R09 and every later candidate cell closed until B2R08 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "CURRENT next action")
    path.write_text(text, encoding="utf-8")


def update_state() -> None:
    path = Path("docs/canonical/CURRENT_STATE.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(text,
        "B2R06 is canonical and post-merge verified at task merge `2460eae15260423b3a06d50d9119ae2459ff41c7` with recovery run `34043039708`; ATTEMPT-002 is frozen; active recovery unit is `B2R07`; only B2R07 primary decode is open;",
        f"B2R07 is canonical and post-merge verified at task merge `{TASK_MERGE}` with recovery run `{RECOVERY_RUN}`; ATTEMPT-002 is frozen; active recovery unit is `B2R08`; only B2R08 primary decode is open;",
        "CURRENT_STATE chronology")
    text = replace_once(text,
        "B2R05 and B2R06 are canonical and post-merge verified, with B2R06 task merge `2460eae15260423b3a06d50d9119ae2459ff41c7` and recovery run `34043039708`; B2R07 is the sole current recovery unit and sole open primary-decode entry;",
        f"B2R05 through B2R07 are canonical and post-merge verified, with B2R07 task merge `{TASK_MERGE}` and recovery run `{RECOVERY_RUN}`; B2R08 is the sole current recovery unit and sole open primary-decode entry;",
        "CURRENT_STATE summary")
    text = text.replace("Current authority is the B2R06 reconciliation block below.", "Current authority is the B2R07 reconciliation block below.")
    text = replace_once(text, "## Canonical B2R06 recovery reconciliation — latest authority", "## Canonical B2R06 recovery reconciliation — predecessor authority", "CURRENT_STATE B2R06 header")
    text = replace_once(text, "This section is the sole current recovery-marker authority in this document.", "This section records predecessor authority superseded by the canonical B2R07 reconciliation below.", "CURRENT_STATE authority")
    marker = "## Next canonical action\n\n"
    assert text.count(marker) == 1
    text = text.replace(marker, reconciliation_block().replace("recovery-action", "recovery-marker") + marker, 1)
    text = replace_once(text,
        "Qualify `B2R07` only: execute candidate cell 3 (`whispercpp-compact`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R08 and every later candidate cell closed until B2R07 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "Qualify `B2R08` only: execute candidate cell 4 (`whispercpp-balanced`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R09 and every later candidate cell closed until B2R08 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "CURRENT_STATE next action")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    update_readiness()
    update_tasks()
    update_current()
    update_state()
    readiness = json.loads(Path("research/000b2-public/recovery-readiness.json").read_text())
    tasks = Path("specs/000B2-public-corpus-bakeoff/tasks.md").read_text()
    current = Path("specs/CURRENT.md").read_text()
    state = Path("docs/canonical/CURRENT_STATE.md").read_text()
    assert readiness["active_recovery_unit"] == "B2R08"
    assert readiness["completed_recovery_tasks"][-1] == "B2R07"
    assert readiness["transition_proofs"][-1] == {
        "completed_task": "B2R07", "canonical_task_merge": TASK_MERGE,
        "post_merge_recovery_run_id": RECOVERY_RUN, "successor_task": "B2R08"}
    assert "- [x] `B2R07`" in tasks and "- [ ] `B2R08`" in tasks and "- [ ] `B2R09`" in tasks
    for text in (current, state):
        assert "**Active recovery unit:** `B2R08`" in text
        assert "Qualify `B2R08` only:" in text
        assert "Keep B2R09 and every later candidate cell closed" in text
    print("B2R07_RECONCILIATION_CONSTRUCTION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
