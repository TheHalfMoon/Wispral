#!/usr/bin/env python3
"""Build the B2R08 -> B2R09 four-file reconciliation candidate."""

from __future__ import annotations

import json
from pathlib import Path

TASK_MERGE = "2fb2506f460f54bb5f9ff26889bb92cbf017bf87"
TASK_HEAD = "a32ccdd4441c8ca6ef04456b28d60c5b29c5e2b8"
TASK_FIRST_PARENT = "4fc35e9d14f949b90dbee58ddf243a36859e02bd"
RECOVERY_RUN = 34153696352
RECOVERY_JOB = 101841001395
WORKFLOW_ID = 350986920


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one match, found {count}"
    return text.replace(old, new, 1)


def update_readiness() -> None:
    path = Path("research/000b2-public/recovery-readiness.json")
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["state"] == "RECOVERY_READY"
    assert value["active_recovery_unit"] == "B2R08"
    assert value["completed_recovery_tasks"] == [
        "B2R01", "B2R02", "B2R03", "B2R04", "B2R05", "B2R06", "B2R07"
    ]
    assert value["transition_proofs"][-1] == {
        "completed_task": "B2R07",
        "canonical_task_merge": "5ea5a513db5ec9c13739510061ca82faa84a0018",
        "post_merge_recovery_run_id": 34065234517,
        "successor_task": "B2R08",
    }
    assert value["qualified_workflow_change_paths"] == []
    assert value["claim_guards"] == {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
    }
    value["transition_proofs"].append({
        "completed_task": "B2R08",
        "canonical_task_merge": TASK_MERGE,
        "post_merge_recovery_run_id": RECOVERY_RUN,
        "successor_task": "B2R09",
    })
    value["completed_recovery_tasks"].append("B2R08")
    value["active_recovery_unit"] = "B2R09"
    value["next_action"] = (
        "Qualify B2R09 only: execute candidate cell 5 (sherpa-onnx-compact) under "
        "000B2-PUBLIC-ATTEMPT-002 using the unchanged frozen C0 contract and identical frozen public audio. "
        "Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, "
        "and claim guards. Keep B2R10 and every later candidate cell closed until B2R09 is canonically merged, "
        "post-merge verified, and reconciled."
    )
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def update_tasks() -> None:
    path = Path("specs/000B2-public-corpus-bakeoff/tasks.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "- [ ] `B2R08` Execute candidate cell 4 (`whispercpp-balanced`) under ATTEMPT-002 and unchanged frozen C0.",
        "- [x] `B2R08` Execute candidate cell 4 (`whispercpp-balanced`) under ATTEMPT-002 and unchanged frozen C0.",
        "tasks B2R08",
    )
    assert "- [ ] `B2R09` Execute candidate cell 5 (`sherpa-onnx-compact`)" in text
    assert "- [ ] `B2R10` Execute candidate cell 6 (`sherpa-onnx-balanced`)" in text
    path.write_text(text, encoding="utf-8")


def reconciliation_block() -> str:
    return f"""## Canonical B2R08 recovery reconciliation — latest authority

This section is the sole current recovery-action authority in this document. PR #78 merged the separately qualified B2R08 implementation and sealed evidence as real task merge `{TASK_MERGE}` from exact final head `{TASK_HEAD}` against first parent `{TASK_FIRST_PARENT}`. The final eight-file task diff preserved all four reconciliation-authority files and contained no workflow file. Fresh independent exact-range CodeRabbit review on review-only PR #79 reported no actionable substantive correctness, security, evidence-integrity, provenance-integrity, fail-closed, or recovery-governance findings on the exact task head. Exact task-merge push run `{RECOVERY_RUN}` of `000B2 Public Corpus Attempt Recovery` (`workflow_id={WORKFLOW_ID}`, path `.github/workflows/000b2-public-attempt-recovery.yml`, job `{RECOVERY_JOB}`) completed successfully with `head_sha={TASK_MERGE}` and reverified canonical main, all recorded recovery-transition runs, pinned upstream material, and the historical ATTEMPT-001 evidence boundary.

The canonical B2R08 sealed primary evidence remains GitHub Actions seal run `34150046063`, job `101830233512`, artifact `10029053259`, with artifact ZIP SHA-256 `6345de28752f714c1a49ce81cbf4b89e86e8f4520ce2b0f0c573843f90c4090a`, exact evidence file SHA-256 `5b438a0d23c8ec19796df9b384234437a266ef862bd6ddd604772ed965932b41`, and canonical payload digest `b688080a9b54106975fc3d423d210f6b449c47468cdc94135997285d9504314c`. It records 240 frozen inputs, 240 decoded outputs, and zero failures. The original full-list primary run `34067447713` hit only the GitHub-hosted runner execution ceiling and exposed no transcript artifact or B2R08 evidence JSON before the forward-only repair. A pre-primary repair-qualification attempt `34136897131`, job `101789871560`, failed at exact authority/repair-source validation with `KeyError: 'failed_primary'` before runtime-source fetch, adapter build, model download, synthetic qualification, evidence upload, primary-corpus access, or candidate-result access and produced zero artifacts. The successful non-primary equivalence qualification run `34137057908`, job `101790371251`, used only deterministic synthetic fixtures before repaired-primary result availability and recorded eight fixtures with zero semantic mismatches. The four-shard primary run `34139091127` preserved the frozen candidate, model, runtime, audio, C0, scorer, normalization, and final-record-order identities and produced the final 240/240/0 evidence. Reference transcripts were not loaded; accuracy scoring and comparative ranking were not performed; timing remains diagnostic only.

**Canonical recovery predecessor:** `B2R08`
**Canonical B2R08 recovery merge:** `{TASK_MERGE}`
**Canonical B2R08 post-merge recovery run:** `{RECOVERY_RUN}`
**Active recovery unit:** `B2R09`

ATTEMPT-001 remains historical and ineligible for comparative scoring. ATTEMPT-002 remains canonically frozen with freeze digest `600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8`. `primary_decode_entry_open=true` only for the active recovery unit B2R09. B2R09 alone is authorized after this reconciliation becomes canonical: execute candidate cell 5 (`sherpa-onnx-compact`) against the identical frozen P0 public-human audio using the unchanged frozen C0 contract, while preserving raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and all claim guards. B2R10 and every later ATTEMPT-002 candidate cell remain unauthorized until B2R09 is separately qualified, merged, post-merge verified, and reconciled.

"""


def update_current() -> None:
    path = Path("specs/CURRENT.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 recovery active; B2R01 through B2R07 canonical and post-merge verified; active recovery unit `B2R08`; ATTEMPT-001 B2E03 and all later primary decoding closed",
        "**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 recovery active; B2R01 through B2R08 canonical and post-merge verified; active recovery unit `B2R09`; ATTEMPT-001 B2E03 and all later primary decoding closed",
        "CURRENT status",
    )
    text = replace_once(
        text,
        "B2R07 is canonical and post-merge verified at task merge `5ea5a513db5ec9c13739510061ca82faa84a0018` with exact recovery run `34065234517`; this reconciliation makes B2R08 the sole current bounded recovery unit. ATTEMPT-002 is canonically frozen and primary decode entry is open only for B2R08; B2R09 and every later cell remain closed.",
        f"B2R08 is canonical and post-merge verified at task merge `{TASK_MERGE}` with exact recovery run `{RECOVERY_RUN}`; this reconciliation makes B2R09 the sole current bounded recovery unit. ATTEMPT-002 is canonically frozen and primary decode entry is open only for B2R09; B2R10 and every later cell remain closed.",
        "CURRENT summary",
    )
    text = replace_once(
        text,
        "B2R07 is canonical and post-merge verified at task merge `5ea5a513db5ec9c13739510061ca82faa84a0018` with exact recovery run `34065234517`, and this reconciliation advances current recovery authority to B2R08 only with ATTEMPT-002 frozen.",
        f"B2R08 is canonical and post-merge verified at task merge `{TASK_MERGE}` with exact recovery run `{RECOVERY_RUN}`, and this reconciliation advances current recovery authority to B2R09 only with ATTEMPT-002 frozen.",
        "CURRENT P0",
    )
    text = text.replace("latest B2R07 recovery markers below", "latest B2R08 recovery markers below")
    text = text.replace("latest B2R07 reconciliation block below", "latest B2R08 reconciliation block below")
    text = replace_once(
        text,
        "## Canonical B2R07 recovery reconciliation — latest authority",
        "## Canonical B2R07 recovery reconciliation — predecessor authority",
        "CURRENT B2R07 header",
    )
    text = replace_once(
        text,
        "This section is the sole current recovery-action authority in this document.",
        "This section records predecessor authority superseded by the canonical B2R08 reconciliation below.",
        "CURRENT authority",
    )
    marker = "## Next canonical action\n\n"
    assert text.count(marker) == 1
    text = text.replace(marker, reconciliation_block() + marker, 1)
    text = replace_once(
        text,
        "Qualify `B2R08` only: execute candidate cell 4 (`whispercpp-balanced`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R09 and every later candidate cell closed until B2R08 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "Qualify `B2R09` only: execute candidate cell 5 (`sherpa-onnx-compact`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R10 and every later candidate cell closed until B2R09 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "CURRENT next action",
    )
    path.write_text(text, encoding="utf-8")


def update_state() -> None:
    path = Path("docs/canonical/CURRENT_STATE.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "B2R07 is canonical and post-merge verified at task merge `5ea5a513db5ec9c13739510061ca82faa84a0018` with recovery run `34065234517`; ATTEMPT-002 is frozen; active recovery unit is `B2R08`; only B2R08 primary decode is open;",
        f"B2R08 is canonical and post-merge verified at task merge `{TASK_MERGE}` with recovery run `{RECOVERY_RUN}`; ATTEMPT-002 is frozen; active recovery unit is `B2R09`; only B2R09 primary decode is open;",
        "CURRENT_STATE chronology",
    )
    text = replace_once(
        text,
        "B2R05 through B2R07 are canonical and post-merge verified, with B2R07 task merge `5ea5a513db5ec9c13739510061ca82faa84a0018` and recovery run `34065234517`; B2R08 is the sole current recovery unit and sole open primary-decode entry;",
        f"B2R05 through B2R08 are canonical and post-merge verified, with B2R08 task merge `{TASK_MERGE}` and recovery run `{RECOVERY_RUN}`; B2R09 is the sole current recovery unit and sole open primary-decode entry;",
        "CURRENT_STATE summary",
    )
    text = text.replace(
        "Current authority is the B2R07 reconciliation block below.",
        "Current authority is the B2R08 reconciliation block below.",
    )
    text = replace_once(
        text,
        "## Canonical B2R07 recovery reconciliation — latest authority",
        "## Canonical B2R07 recovery reconciliation — predecessor authority",
        "CURRENT_STATE B2R07 header",
    )
    text = replace_once(
        text,
        "This section is the sole current recovery-marker authority in this document.",
        "This section records predecessor authority superseded by the canonical B2R08 reconciliation below.",
        "CURRENT_STATE authority",
    )
    marker = "## Next canonical action\n\n"
    assert text.count(marker) == 1
    text = text.replace(marker, reconciliation_block().replace("recovery-action", "recovery-marker") + marker, 1)
    text = replace_once(
        text,
        "Qualify `B2R08` only: execute candidate cell 4 (`whispercpp-balanced`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R09 and every later candidate cell closed until B2R08 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "Qualify `B2R09` only: execute candidate cell 5 (`sherpa-onnx-compact`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R10 and every later candidate cell closed until B2R09 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "CURRENT_STATE next action",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    update_readiness()
    update_tasks()
    update_current()
    update_state()
    readiness = json.loads(Path("research/000b2-public/recovery-readiness.json").read_text(encoding="utf-8"))
    tasks = Path("specs/000B2-public-corpus-bakeoff/tasks.md").read_text(encoding="utf-8")
    current = Path("specs/CURRENT.md").read_text(encoding="utf-8")
    state = Path("docs/canonical/CURRENT_STATE.md").read_text(encoding="utf-8")
    assert readiness["active_recovery_unit"] == "B2R09"
    assert readiness["completed_recovery_tasks"][-1] == "B2R08"
    assert readiness["transition_proofs"][-1] == {
        "completed_task": "B2R08",
        "canonical_task_merge": TASK_MERGE,
        "post_merge_recovery_run_id": RECOVERY_RUN,
        "successor_task": "B2R09",
    }
    assert "- [x] `B2R08`" in tasks
    assert "- [ ] `B2R09`" in tasks
    assert "- [ ] `B2R10`" in tasks
    for text in (current, state):
        assert "**Active recovery unit:** `B2R09`" in text
        assert "Qualify `B2R09` only" in text
        assert "Keep B2R10 and every later candidate cell closed" in text
        assert f"**Canonical B2R08 recovery merge:** `{TASK_MERGE}`" in text
        assert f"**Canonical B2R08 post-merge recovery run:** `{RECOVERY_RUN}`" in text
    print("B2R08_RECONCILIATION_CONTENT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
