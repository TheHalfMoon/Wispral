from __future__ import annotations

import json
from pathlib import Path

readiness = json.loads(Path("research/000b2-public/readiness.json").read_text(encoding="utf-8"))
completed = readiness.get("completed_through")
if completed == "B2P08":
    print("B2P08_RECONCILIATION_ALREADY_APPLIED=YES")
    raise SystemExit(0)
if completed != "B2P07":
    raise SystemExit(f"unexpected entry frontier: {completed!r}")

workflow = Path(".github/workflows/internal-b2p08-reconciliation-v2.yml").read_text(encoding="utf-8")
marker = "          python - <<'PY'\n"
start = workflow.index(marker) + len(marker)
end = workflow.index("\n          PY", start)
source = workflow[start:end]
source = "\n".join(line[10:] if line.startswith("          ") else line for line in source.splitlines())
exec(compile(source, "<b2p08-reconciliation-v2-apply>", "exec"), {"__name__": "__main__"})

prep_path = Path("research/000b2-public/verify_preprocessing_capture.py")
prep = prep_path.read_text(encoding="utf-8")
prep_old = "\n".join([
    "    else:",
    '        require(preprocessing.get("resolved") is True, "B2P07 reconciliation must preserve preprocessing resolution")',
    '        require("- [x] `B2P06`" in tasks, "B2P06 must remain complete")',
    '        require("- [x] `B2P07`" in tasks, "B2P07 reconciliation must mark B2P07 complete")',
    '        require("- [ ] `B2P08`" in tasks, "B2P08 must remain open")',
    '        require("Execute B2P08 only" in str(readiness.get("next_action")), "B2P07 reconciliation must advance to B2P08")',
    '        require("Execute and canonically qualify `B2P08` only" in current, "CURRENT must authorize B2P08 only")',
]) + "\n"
prep_new = "\n".join([
    "    else:",
    '        require(preprocessing.get("resolved") is True, "B2P07+ reconciliation must preserve preprocessing resolution")',
    '        require("- [x] `B2P06`" in tasks, "B2P06 must remain complete")',
    '        require("- [x] `B2P07`" in tasks, "B2P07 must remain complete")',
    '        if completed == "B2P07":',
    '            require("- [ ] `B2P08`" in tasks, "B2P08 must remain open at the B2P07 frontier")',
    '            require("Execute B2P08 only" in str(readiness.get("next_action")), "B2P07 reconciliation must advance to B2P08")',
    '            require("Execute and canonically qualify `B2P08` only" in current, "CURRENT must authorize B2P08 only")',
    "        else:",
    '            require("- [x] `B2P08`" in tasks, "B2P08 reconciliation must mark B2P08 complete")',
    '            require("- [ ] `B2E01`" in tasks, "B2E01 must remain pending before execution")',
    '            require("- [ ] `B2E02`" in tasks, "B2E02 must remain unauthorized")',
    '            require("Execute B2E01 only" in str(readiness.get("next_action")), "B2P08 reconciliation must advance to B2E01")',
    '            require("Execute and canonically qualify `B2E01` only" in current, "CURRENT must authorize B2E01 only")',
]) + "\n"
if prep.count(prep_old) != 1:
    raise SystemExit(f"preprocessing historical frontier anchor count={prep.count(prep_old)}")
prep_path.write_text(prep.replace(prep_old, prep_new, 1), encoding="utf-8")

subset_path = Path("research/000b2-public/verify_subset_freeze.py")
subset = subset_path.read_text(encoding="utf-8")
subset_old = "\n".join([
    '    if completed_through == "B2P07":',
    '        require(preprocessing.get("resolved") is True, "B2P07 reconciliation must preserve preprocessing resolution")',
    '        require(public.get("subset_manifest_frozen") is True, "B2P07 reconciliation must preserve the B2P04 frozen manifest")',
    '        require(isinstance(next_action, str) and next_action.startswith("Execute B2P08 only:"), "B2P07 reconciliation must authorize B2P08 only")',
    '        require("Do not begin candidate or primary decoding until B2P08 is canonical." in next_action, "B2P08 successor boundary drift")',
    '        require("- [x] `B2P06`" in tasks, "B2P06 must remain complete")',
    '        require("- [x] `B2P07`" in tasks, "B2P07 reconciliation must mark B2P07 complete")',
    '        require("- [ ] `B2P08`" in tasks, "B2P08 must remain open during B2P08 execution qualification")',
    '        require("current bounded execution unit `B2P08`" in current, "reconciled frontier is not B2P08-only")',
    '        require("Execute and canonically qualify `B2P08` only" in current, "reconciled current view must authorize B2P08 only")',
    '        require("Candidate and primary decoding remain unauthorized" in current, "reconciled frontier must keep decoding closed")',
    '        return "B2P07"',
    "",
    '    raise SystemExit(f"B2P04_FREEZE_VERIFIER=FAIL: unsupported completed_through state: {completed_through!r}")',
]) + "\n"
subset_new = "\n".join([
    '    if completed_through == "B2P07":',
    '        require(preprocessing.get("resolved") is True, "B2P07 reconciliation must preserve preprocessing resolution")',
    '        require(public.get("subset_manifest_frozen") is True, "B2P07 reconciliation must preserve the B2P04 frozen manifest")',
    '        require(isinstance(next_action, str) and next_action.startswith("Execute B2P08 only:"), "B2P07 reconciliation must authorize B2P08 only")',
    '        require("Do not begin candidate or primary decoding until B2P08 is canonical." in next_action, "B2P08 successor boundary drift")',
    '        require("- [x] `B2P06`" in tasks, "B2P06 must remain complete")',
    '        require("- [x] `B2P07`" in tasks, "B2P07 reconciliation must mark B2P07 complete")',
    '        require("- [ ] `B2P08`" in tasks, "B2P08 must remain open during B2P08 execution qualification")',
    '        require("current bounded execution unit `B2P08`" in current, "reconciled frontier is not B2P08-only")',
    '        require("Execute and canonically qualify `B2P08` only" in current, "reconciled current view must authorize B2P08 only")',
    '        require("Candidate and primary decoding remain unauthorized" in current, "reconciled frontier must keep decoding closed")',
    '        return "B2P07"',
    "",
    '    if completed_through == "B2P08":',
    '        require(preprocessing.get("resolved") is True, "B2P08 reconciliation must preserve preprocessing resolution")',
    '        require(environment.get("resolved") is True, "B2P08 reconciliation must preserve environment resolution")',
    '        require(public.get("subset_manifest_frozen") is True, "B2P08 reconciliation must preserve the B2P04 frozen manifest")',
    '        require(isinstance(next_action, str) and next_action.startswith("Execute B2E01 only:"), "B2P08 reconciliation must authorize B2E01 only")',
    '        require("Do not begin B2E02 or any later candidate cell until B2E01 is canonical." in next_action, "B2E01 successor boundary drift")',
    '        require("- [x] `B2P06`" in tasks, "B2P06 must remain complete")',
    '        require("- [x] `B2P07`" in tasks, "B2P07 must remain complete")',
    '        require("- [x] `B2P08`" in tasks, "B2P08 reconciliation must mark B2P08 complete")',
    '        require("- [ ] `B2E01`" in tasks, "B2E01 must remain pending before execution")',
    '        require("- [ ] `B2E02`" in tasks, "B2E02 must remain unauthorized")',
    '        require("current bounded execution unit `B2E01`" in current, "reconciled frontier is not B2E01-only")',
    '        require("Execute and canonically qualify `B2E01` only" in current, "reconciled current view must authorize B2E01 only")',
    '        require("B2E02 and all later candidate cells remain unauthorized" in current, "reconciled frontier must keep later candidate cells closed")',
    '        return "B2P08"',
    "",
    '    raise SystemExit(f"B2P04_FREEZE_VERIFIER=FAIL: unsupported completed_through state: {completed_through!r}")',
]) + "\n"
if subset.count(subset_old) != 1:
    raise SystemExit(f"subset historical frontier anchor count={subset.count(subset_old)}")
subset_path.write_text(subset.replace(subset_old, subset_new, 1), encoding="utf-8")

current_path = Path("specs/CURRENT.md")
current = current_path.read_text(encoding="utf-8")
old = (
    "Execute and canonically qualify `B2P08` only: freeze the final pre-decode attempt manifest for "
    "`000B2-PUBLIC-ATTEMPT-001`, binding the canonical B2P04 subset, B2P05 candidate revalidation, "
    "B2P06 preprocessing evidence, and B2P07 execution-environment evidence while verifying "
    "`primary_decoding_started=false`. B2P08 must not execute candidate or primary decoding. Preserve "
    "`HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, `production_stt_selected=false`, and "
    "`product_code_authorized=false`. Candidate and primary decoding remain unauthorized until B2P08 "
    "is canonically qualified, post-merge verified, and reconciled."
)
new = (
    "Execute and canonically qualify `B2E01` only: decode the exact frozen P0 public-human subset with "
    "candidate cell 1 (`moonshine-compact`) under frozen C0, preserving raw transcript/failure/run "
    "evidence and keeping repository/test-specific context, candidate-specific audio transforms, and "
    "comparative timing claims disabled. B2E02 and all later candidate cells remain unauthorized until "
    "B2E01 is canonically qualified, post-merge verified, and reconciled."
)
if current.count(old) != 1:
    raise SystemExit(f"CURRENT exact next-action anchor count={current.count(old)}")
current_path.write_text(current.replace(old, new, 1), encoding="utf-8")
print("B2P08_RECONCILIATION_V3=APPLIED")
