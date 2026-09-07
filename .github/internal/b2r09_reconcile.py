#!/usr/bin/env python3
"""Build the B2R09 -> B2R10 four-file reconciliation candidate."""

from __future__ import annotations

import json
from pathlib import Path

TASK_MERGE = "fc357350270d5cb34fc1305dba4a9de41a5234c3"
TASK_HEAD = "ff990ccc63a120c62758802c305bcc10b33ed0fe"
TASK_FIRST_PARENT = "737e2fa0422e0d1aa0dd4d5bdc0473d51cec624c"
RECOVERY_RUN = 34160146607
RECOVERY_JOB = 101860017509
WORKFLOW_ID = 350986920


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one match, found {count}"
    return text.replace(old, new, 1)


def update_readiness() -> None:
    path = Path("research/000b2-public/recovery-readiness.json")
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["state"] == "RECOVERY_READY"
    assert value["active_recovery_unit"] == "B2R09"
    assert value["completed_recovery_tasks"] == [
        "B2R01", "B2R02", "B2R03", "B2R04", "B2R05", "B2R06", "B2R07", "B2R08"
    ]
    assert value["transition_proofs"][-1] == {
        "completed_task": "B2R08",
        "canonical_task_merge": "2fb2506f460f54bb5f9ff26889bb92cbf017bf87",
        "post_merge_recovery_run_id": 34153696352,
        "successor_task": "B2R09",
    }
    assert value["qualified_workflow_change_paths"] == []
    assert value["claim_guards"] == {
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "comparative_result_available": False,
        "production_stt_selected": False,
        "product_code_authorized": False,
    }
    value["transition_proofs"].append({
        "completed_task": "B2R09",
        "canonical_task_merge": TASK_MERGE,
        "post_merge_recovery_run_id": RECOVERY_RUN,
        "successor_task": "B2R10",
    })
    value["completed_recovery_tasks"].append("B2R09")
    value["active_recovery_unit"] = "B2R10"
    value["next_action"] = (
        "Qualify B2R10 only: execute candidate cell 6 (sherpa-onnx-balanced) under "
        "000B2-PUBLIC-ATTEMPT-002 using the unchanged frozen C0 contract and identical frozen public audio. "
        "Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, "
        "and claim guards. Keep B2R11 and every later recovery, scoring, synthesis, and product unit closed until "
        "B2R10 is canonically merged, post-merge verified, and reconciled."
    )
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def update_tasks() -> None:
    path = Path("specs/000B2-public-corpus-bakeoff/tasks.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "- [ ] `B2R09` Execute candidate cell 5 (`sherpa-onnx-compact`) under ATTEMPT-002 and unchanged frozen C0.",
        "- [x] `B2R09` Execute candidate cell 5 (`sherpa-onnx-compact`) under ATTEMPT-002 and unchanged frozen C0.",
        "tasks B2R09",
    )
    assert "- [ ] `B2R10` Execute candidate cell 6 (`sherpa-onnx-balanced`)" in text
    assert "- [ ] `B2R11` Preserve ATTEMPT-002 raw transcripts" in text
    assert "- [ ] `B2R12` Score P0" in text
    path.write_text(text, encoding="utf-8")


def reconciliation_block(authority_term: str) -> str:
    return f"""## Canonical B2R09 recovery reconciliation — latest authority

This section is the sole current {authority_term} authority in this document. PR #82 merged the separately qualified B2R09 implementation and sealed evidence as real task merge `{TASK_MERGE}` from exact final head `{TASK_HEAD}` against first parent `{TASK_FIRST_PARENT}`. The final five-file task diff contains only B2R09 research evidence/decoder/verifier files and no workflow or canonical-authority file. Fresh independent exact-range CodeRabbit review on review-only PR #85 reported no actionable substantive findings on the exact final task head after prior review-only PRs #83 and #84 identified two fail-closed frontier/ledger verifier gaps that were repaired forward-only. Exact task-merge push run `{RECOVERY_RUN}` of `000B2 Public Corpus Attempt Recovery` (`workflow_id={WORKFLOW_ID}`, path `.github/workflows/000b2-public-attempt-recovery.yml`, job `{RECOVERY_JOB}`) completed successfully with `head_sha={TASK_MERGE}`.

The canonical B2R09 primary capture remains GitHub Actions run `34156167567`, job `101848322734`, artifact `10031177463`, with artifact ZIP SHA-256 `79652728032760ae133845b7f1308623a984ee69c490991cf190d8a7301985ea`, exact evidence file SHA-256 `d59fa9605e8b0cf6892cd5a7ece105c6abe0753ff8949e9206e35f42da9a003f`, and canonical payload digest `4a81f1be21e18aa462ee9ec9c32a1daeaa6fa86bcca6372b0634a9421c16c1ed`. It records 240 frozen inputs, 240 decoded outputs, and zero failures. Failed pre-primary run `34155967652`, job `101847745228`, passed exact authority and then failed during setup-python pip-cache dependency-file discovery before runtime installation, preprocessing, runtime-source fetch, model download, primary decode, result access, or evidence upload, and produced zero artifacts. Forward-only source `47d1c53f6892dda437aa0f1d109f58f1cc5e101e` removed only the setup-python pip cache configuration. Successful primary selection therefore remained non-result-driven. Byte-preserving materialization run `34157501089`, job `101852259514`, independently reproduced the artifact/evidence identities before committing the exact evidence bytes. Reference transcripts were not loaded; accuracy scoring and comparative ranking were not performed; timing remains diagnostic only.

The final B2R09 verifier also fails closed on the complete ordered B2R01-B2R12 recovery ledger and permits only the exact B2R09 pre-reconciliation frontier or the exact immediate B2R10 successor frontier. Internal repair run `34159411258`, job `101857896009`, passed B2R09 verification, composite verification, exact verifier-only scope enforcement, and mutation rejection for early/later/duplicate recovery-task states. No candidate, runtime, model, audio, C0, scorer, normalization, evidence, or claim identity was changed by either review repair.

**Canonical recovery predecessor:** `B2R09`
**Canonical B2R09 recovery merge:** `{TASK_MERGE}`
**Canonical B2R09 post-merge recovery run:** `{RECOVERY_RUN}`
**Active recovery unit:** `B2R10`

ATTEMPT-001 remains historical and ineligible for comparative scoring. ATTEMPT-002 remains canonically frozen with freeze digest `600a286747ef2e1503a48c4138b6e405665ccd6586904ef65b3638b49974bcc8`. `primary_decode_entry_open=true` only for active recovery unit B2R10. B2R10 alone is authorized after this reconciliation becomes canonical: execute candidate cell 6 (`sherpa-onnx-balanced`) against the identical frozen P0 public-human audio using the unchanged frozen C0 contract, while preserving raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and all claim guards. B2R11, B2R12, comparative scoring/ranking, synthesis, production STT selection, and product-code authority remain closed until their separately governed predecessor conditions are satisfied.

"""


def update_current() -> None:
    path = Path("specs/CURRENT.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 recovery active; B2R01 through B2R08 canonical and post-merge verified; active recovery unit `B2R09`; ATTEMPT-001 B2E03 and all later primary decoding closed",
        "**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 recovery active; B2R01 through B2R09 canonical and post-merge verified; active recovery unit `B2R10`; ATTEMPT-001 B2E03 and all later primary decoding closed",
        "CURRENT status",
    )
    text = replace_once(
        text,
        "B2R08 is canonical and post-merge verified at task merge `2fb2506f460f54bb5f9ff26889bb92cbf017bf87` with exact recovery run `34153696352`; this reconciliation makes B2R09 the sole current bounded recovery unit. ATTEMPT-002 is canonically frozen and primary decode entry is open only for B2R09; B2R10 and every later cell remain closed.",
        f"B2R09 is canonical and post-merge verified at task merge `{TASK_MERGE}` with exact recovery run `{RECOVERY_RUN}`; this reconciliation makes B2R10 the sole current bounded recovery unit. ATTEMPT-002 is canonically frozen and primary decode entry is open only for B2R10; B2R11 and every later recovery/scoring/synthesis/product unit remain closed.",
        "CURRENT summary",
    )
    text = replace_once(
        text,
        "B2R08 is canonical and post-merge verified at task merge `2fb2506f460f54bb5f9ff26889bb92cbf017bf87` with exact recovery run `34153696352`, and this reconciliation advances current recovery authority to B2R09 only with ATTEMPT-002 frozen.",
        f"B2R09 is canonical and post-merge verified at task merge `{TASK_MERGE}` with exact recovery run `{RECOVERY_RUN}`, and this reconciliation advances current recovery authority to B2R10 only with ATTEMPT-002 frozen.",
        "CURRENT P0",
    )
    text = text.replace("latest B2R08 recovery markers below", "latest B2R09 recovery markers below")
    text = text.replace("latest B2R08 reconciliation block below", "latest B2R09 reconciliation block below")
    text = replace_once(
        text,
        "## Canonical B2R08 recovery reconciliation — latest authority",
        "## Canonical B2R08 recovery reconciliation — predecessor authority",
        "CURRENT B2R08 header",
    )
    text = replace_once(
        text,
        "This section is the sole current recovery-action authority in this document.",
        "This section records predecessor authority superseded by the canonical B2R09 reconciliation below.",
        "CURRENT authority",
    )
    marker = "## Next canonical action\n\n"
    assert text.count(marker) == 1
    text = text.replace(marker, reconciliation_block("recovery-action") + marker, 1)
    text = replace_once(
        text,
        "Qualify `B2R09` only: execute candidate cell 5 (`sherpa-onnx-compact`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R10 and every later candidate cell closed until B2R09 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "Qualify `B2R10` only: execute candidate cell 6 (`sherpa-onnx-balanced`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R11 and every later recovery, scoring, synthesis, and product unit closed until B2R10 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "CURRENT next action",
    )
    path.write_text(text, encoding="utf-8")


def update_state() -> None:
    path = Path("docs/canonical/CURRENT_STATE.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "B2R08 is canonical and post-merge verified at task merge `2fb2506f460f54bb5f9ff26889bb92cbf017bf87` with recovery run `34153696352`; ATTEMPT-002 is frozen; active recovery unit is `B2R09`; only B2R09 primary decode is open;",
        f"B2R09 is canonical and post-merge verified at task merge `{TASK_MERGE}` with recovery run `{RECOVERY_RUN}`; ATTEMPT-002 is frozen; active recovery unit is `B2R10`; only B2R10 primary decode is open;",
        "CURRENT_STATE chronology",
    )
    text = replace_once(
        text,
        "B2R05 through B2R08 are canonical and post-merge verified, with B2R08 task merge `2fb2506f460f54bb5f9ff26889bb92cbf017bf87` and recovery run `34153696352`; B2R09 is the sole current recovery unit and sole open primary-decode entry;",
        f"B2R05 through B2R09 are canonical and post-merge verified, with B2R09 task merge `{TASK_MERGE}` and recovery run `{RECOVERY_RUN}`; B2R10 is the sole current recovery unit and sole open primary-decode entry;",
        "CURRENT_STATE summary",
    )
    text = text.replace(
        "Current authority is the B2R08 reconciliation block below.",
        "Current authority is the B2R09 reconciliation block below.",
    )
    text = replace_once(
        text,
        "## Canonical B2R08 recovery reconciliation — latest authority",
        "## Canonical B2R08 recovery reconciliation — predecessor authority",
        "CURRENT_STATE B2R08 header",
    )
    text = replace_once(
        text,
        "This section is the sole current recovery-marker authority in this document.",
        "This section records predecessor authority superseded by the canonical B2R09 reconciliation below.",
        "CURRENT_STATE authority",
    )
    marker = "## Next canonical action\n\n"
    assert text.count(marker) == 1
    text = text.replace(marker, reconciliation_block("recovery-marker") + marker, 1)
    text = replace_once(
        text,
        "Qualify `B2R09` only: execute candidate cell 5 (`sherpa-onnx-compact`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R10 and every later candidate cell closed until B2R09 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "Qualify `B2R10` only: execute candidate cell 6 (`sherpa-onnx-balanced`) under `000B2-PUBLIC-ATTEMPT-002` using the unchanged frozen C0 contract and identical frozen public audio. Preserve raw transcripts, failures, runtime observations, exact run identity, frozen input identities, and claim guards. Keep B2R11 and every later recovery, scoring, synthesis, and product unit closed until B2R10 is canonically merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`.",
        "CURRENT_STATE next action",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    update_readiness()
    update_tasks()
    update_current()
    update_state()
    print("B2R09_RECONCILIATION_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
