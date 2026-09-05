#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CURRENT = ROOT / "specs/CURRENT.md"
STATE = ROOT / "docs/canonical/CURRENT_STATE.md"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_FAIL {path}: expected one anchor, found {count}: {old[:140]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


current_status_old = "**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 execution frontier `READY`; B2P01 through B2P08 canonical; current bounded execution unit `B2E03`"
current_status_new = "**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 recovery active; B2R01 canonical and post-merge verified; active recovery unit `B2R02`; ATTEMPT-001 B2E03 and all later primary decoding closed"
replace_once(CURRENT, current_status_old, current_status_new)

current_active_old = "B2E03 (`whispercpp-compact`) is the sole current bounded execution unit. B2E04 and all later candidate cells remain unauthorized until B2E03 is separately qualified, merged, post-merge verified, and reconciled."
current_active_new = "ATTEMPT-001 is now historical and ineligible for comparative scoring because B2R01 is canonical at merge `715efc4855fb52187ed250b11f0c28bb2c2c0660`; B2E03 and every later ATTEMPT-001 primary decode are closed. `research/000b2-public/recovery-readiness.json` is the active machine-readable execution authority. B2R02 is the sole current bounded recovery unit, and all ATTEMPT-002 primary decoding remains closed until B2R04 is canonically reconciled."
replace_once(CURRENT, current_active_old, current_active_new)

current_recovery_section = r'''## Canonical B2R01 recovery reconciliation

B2R01 invalidation is canonical at merge `715efc4855fb52187ed250b11f0c28bb2c2c0660` and exact-merge-head recovery workflow run `33979925715` succeeded. The historical ATTEMPT-001 `readiness.json` remains byte-preserved evidence only; `recovery-readiness.json` overrides it for every new execution decision.

**Canonical recovery predecessor:** `B2R01`
**Canonical B2R01 recovery merge:** `715efc4855fb52187ed250b11f0c28bb2c2c0660`
**Canonical B2R01 post-merge recovery run:** `33979925715`
**Active recovery unit:** `B2R02`

ATTEMPT-001 is ineligible for comparative scoring and candidate-superiority claims. No new ATTEMPT-001 primary decode is authorized. ATTEMPT-002 is required but not frozen, and its primary decode entry remains closed. B2R02 may use only non-primary material and exact pinned upstream source to qualify the corrected Moonshine streaming C0 harness. No B2R03 or later recovery work is authorized before B2R02 is separately qualified, merged, post-merge verified, and reconciled.

### Historical ATTEMPT-001 post-B2E02 snapshot wording — non-authoritative

The following strings are retained only as a literal description of the superseded ATTEMPT-001 post-B2E02 snapshot so historical evidence verifiers can continue proving what the old snapshot said. They MUST NOT be interpreted as current execution authority; `recovery-readiness.json` and the recovery markers above supersede them for new execution:

```text
current bounded execution unit `B2E03`
B2E01 and B2E02 are canonical. B2E03 (`whispercpp-compact`) is now the only authorized bounded unit
B2P01 through B2P08, B2E01, and B2E02 are complete.
B2P08 pre-decode attempt freeze became canonical at merge `dd65e23d29e7f83b9a94aba9c018928c7f9cc41d`
B2E03 (`whispercpp-compact`) is the sole current bounded execution unit.
Execute and canonically qualify `B2E03` only: decode the identical frozen P0 public-human subset with candidate cell 3 (`whispercpp-compact`) under unchanged frozen C0
B2E04 and all later candidate cells remain unauthorized
```

'''
replace_once(CURRENT, "## Live-truth rule\n", current_recovery_section + "## Live-truth rule\n")

current_next_old = "Execute and canonically qualify `B2E03` only: decode the identical frozen P0 public-human subset with candidate cell 3 (`whispercpp-compact`) under unchanged frozen C0, preserving raw transcript/failure/run evidence while keeping repository/test-specific context and candidate-specific audio transforms OFF and preserving `DIAGNOSTIC_ONLY` timing semantics. B2E04 and all later candidate cells remain unauthorized until B2E03 is separately qualified, merged, post-merge verified, and reconciled."
current_next_new = "Qualify `B2R02` only: implement and verify the corrected Moonshine streaming C0 harness against non-primary material and exact pinned upstream source. Demonstrate the frozen 500 ms / 8,000-sample feed schedule, final 660 ms / 10,560-sample zero suffix, `vad_threshold=0.0`, `transcription_interval_seconds=0.5`, unchanged repository/test-specific context and keyterm guards, and frozen runtime/model identities without inspecting new primary results. Keep all ATTEMPT-002 primary decoding closed until B2R04 is canonically reconciled. Do not begin B2R03 before B2R02 is separately qualified, merged, post-merge verified, and reconciled."
replace_once(CURRENT, current_next_old, current_next_new)

state_top_old = "current bounded execution unit is `B2E03`"
state_top_new = "active recovery unit is `B2R02`; ATTEMPT-001 B2E03 and all later primary decoding are closed"
replace_once(STATE, state_top_old, state_top_new)

state_bullets_old = "- B2E01 and B2E02 are canonical; B2E03 (`whispercpp-compact`) is now the only authorized bounded unit;\n- candidate revalidation, preprocessing capture, execution-environment capture, final pre-decode attempt freeze, B2E01 decoding, and B2E02 decoding are complete; B2E03 is the sole authorized decoding unit, B2E04 and all later candidate cells remain unauthorized, no comparative scoring or ranking has begun, and no production STT is selected."
state_bullets_new = "- B2E01 and B2E02 remain canonical historical ATTEMPT-001 executions, but B2R01 invalidated ATTEMPT-001 for material execution drift; its outputs are ineligible for the canonical six-cell comparison and B2E03 plus every later ATTEMPT-001 primary decode are closed;\n- B2R01 is canonical at merge `715efc4855fb52187ed250b11f0c28bb2c2c0660`, exact-merge-head recovery run `33979925715` succeeded, ATTEMPT-002 is required but not frozen, B2R02 is the sole current recovery unit, no comparative scoring or ranking is available, and no production STT is selected."
replace_once(STATE, state_bullets_old, state_bullets_new)

state_recovery_section = r'''## Canonical B2R01 recovery reconciliation

B2R01 records the material ATTEMPT-001 Moonshine C0 execution drift without rewriting any historical attempt, decoder, transcript, evidence, or provenance bytes. The task merge `715efc4855fb52187ed250b11f0c28bb2c2c0660` is canonical on `main`, and exact-head push run `33979925715` of `000B2 Public Corpus Attempt Recovery` succeeded on that merge. The old `research/000b2-public/readiness.json` remains a historical post-B2E02 snapshot only; `research/000b2-public/recovery-readiness.json` is the active execution authority.

**Canonical recovery predecessor:** `B2R01`
**Canonical B2R01 recovery merge:** `715efc4855fb52187ed250b11f0c28bb2c2c0660`
**Canonical B2R01 post-merge recovery run:** `33979925715`
**Active recovery unit:** `B2R02`

ATTEMPT-001 comparative evidence is ineligible, candidate-superiority claims are unavailable, and no new ATTEMPT-001 primary decoding is authorized. ATTEMPT-002 is required but remains unfrozen with primary decode entry closed. B2R02 alone may qualify the corrected Moonshine streaming C0 harness against non-primary material and exact pinned upstream source. B2R03 and all later recovery units remain unauthorized until their predecessors are separately qualified, merged, post-merge verified, and reconciled.

### Historical ATTEMPT-001 post-B2E02 snapshot wording — non-authoritative

These literal strings describe only the superseded historical snapshot and are retained so immutable historical verifiers can prove what that snapshot said. They are not current authority:

```text
current bounded execution unit is `B2E03`
Execute and canonically qualify `B2E03` only: decode the identical frozen P0 public-human subset with candidate cell 3 (`whispercpp-compact`) under unchanged frozen C0
B2E04 and all later candidate cells remain unauthorized
```

'''
replace_once(STATE, "## Current product thesis\n", state_recovery_section + "## Current product thesis\n")

state_next_old = "Execute and canonically qualify `B2E03` only: decode the identical frozen P0 public-human subset with candidate cell 3 (`whispercpp-compact`) under unchanged frozen C0. Preserve raw transcript, failure, and run evidence; keep repository/test-specific context and candidate-specific audio transforms OFF; and preserve GitHub-hosted timing as `DIAGNOSTIC_ONLY`. Do not begin B2E04 or any later candidate cell until B2E03 is separately qualified, merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`. B2E04 and all later candidate cells remain unauthorized."
state_next_new = "Qualify `B2R02` only: implement and verify the corrected Moonshine streaming C0 harness against non-primary material and exact pinned upstream source. Demonstrate the frozen 500 ms / 8,000-sample feed schedule, final 660 ms / 10,560-sample zero suffix, `vad_threshold=0.0`, `transcription_interval_seconds=0.5`, unchanged repository/test-specific context and keyterm guards, and frozen runtime/model identities without inspecting new primary results. Keep all ATTEMPT-002 primary decoding closed until B2R04 is canonically reconciled. Do not begin B2R03 before B2R02 is separately qualified, merged, post-merge verified, and reconciled. Preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, historical `000B2-unbiased-stt-bakeoff=BLOCKED_EXTERNAL`, `production_stt_selected=false`, and `product_code_authorized=false`."
replace_once(STATE, state_next_old, state_next_new)

print("B2R01_RECONCILIATION_PATCH=PASS")
