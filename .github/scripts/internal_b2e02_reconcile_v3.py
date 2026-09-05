from pathlib import Path

SOURCE = Path('.github/workflows/internal-b2e02-reconciliation-apply.yml')
OUT = Path('/tmp/reconcile-v3.sh')

source = SOURCE.read_text(encoding='utf-8')
marker = '        run: |\n'
if source.count(marker) != 1:
    raise SystemExit(f'apply run block drift: {source.count(marker)}')

block = source.split(marker, 1)[1]
lines = block.splitlines()
extracted: list[str] = []
for line in lines:
    if line.startswith('          '):
        extracted.append(line[10:])
    elif not line.strip():
        extracted.append('')
    else:
        raise SystemExit(f'unexpected YAML indentation in apply block: {line!r}')
script = '\n'.join(extracted) + '\n'

insertion_anchor = '# Canonical CURRENT: update frontier and record the exact B2E02 merge/post-merge proof.\n'
if script.count(insertion_anchor) != 1:
    raise SystemExit(f'methodology insertion anchor drift: {script.count(insertion_anchor)}')

extension = """# Exact methodology frontier/proof extension for post-B2E02 reconciliation.
p = Path("research/000b2-public/verify_methodology.py")
text = read(p)

constants_anchor = 'B2E01_POSTMERGE_EVIDENCE_JOB_ID = 101290913708\\n'
constants_new = constants_anchor + '''B2E02_CANONICAL_MERGE = "91588babc1f738c4284f53d40b4cd96dc13bfd50"\nB2E02_QUALIFIED_HEAD = "1c4db3f5f857f7a813f4fbb8bc4593c5c5f066c1"\nB2E02_POSTMERGE_EVIDENCE_RUN_ID = 33964134856\nB2E02_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID = 33964134877\nB2E02_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID = 33964134889\nB2E02_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID = 33964134896\nB2E02_POSTMERGE_METHODOLOGY_RUN_ID = 33964134899\nB2E02_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID = 33964134921\nB2E02_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID = 33964134937\n'''
text = once(text, constants_anchor, constants_new, "methodology B2E02 proof constants")
text = once(
    text,
    '    require(readiness.get("completed_through") in {"B2E01", "B2E02"}, "readiness completed_through must be B2E01")\\n',
    '    require(readiness.get("completed_through") == "B2E02", "readiness completed_through must be B2E02")\\n',
    "methodology exact completed_through",
)
old_next = '''    expected_next_action = (\\n        'Execute B2E02 only: decode the identical frozen P0 public-human subset with candidate cell 2 (`moonshine-balanced`) under unchanged frozen C0, preserve raw transcript/failure/run evidence, keep repository/test-specific context and candidate-specific audio transforms OFF, and preserve DIAGNOSTIC timing semantics. Do not begin B2E03 or any later candidate cell until B2E02 is canonical.'\\n    )\\n    require(readiness.get("next_action") == expected_next_action, "next action must be exact post-B2E01 B2E02-only instruction")\\n'''
new_next = '''    expected_next_action = (\\n        'Execute B2E03 only: decode the identical frozen P0 public-human subset with candidate cell 3 (`whispercpp-compact`) under unchanged frozen C0, preserve raw transcript/failure/run evidence, keep repository/test-specific context and candidate-specific audio transforms OFF, and preserve DIAGNOSTIC timing semantics. Do not begin B2E04 or any later candidate cell until B2E03 is canonical.'\\n    )\\n    require(readiness.get("next_action") == expected_next_action, "next action must be exact post-B2E02 B2E03-only instruction")\\n'''
text = once(text, old_next, new_next, "methodology exact next action")
old_task = '    require_text(tasks, "- [ ] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0.", "public child tasks")\\n'
new_task = '    require_text(tasks, "- [x] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0.", "public child tasks")\\n    require_text(tasks, "- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0.", "public child tasks")\\n'
text = once(text, old_task, new_task, "methodology exact task frontier")
replacements = [
    ('    require_text(current, "current bounded execution unit `B2E02`", "current frontier")\\n', '    require_text(current, "current bounded execution unit `B2E03`", "current frontier")\\n'),
    ('    require_text(current, "Execute and canonically qualify `B2E02` only", "current frontier next action")\\n', '    require_text(current, "Execute and canonically qualify `B2E03` only", "current frontier next action")\\n'),
    ('    require_text(current, "Execute and canonically qualify `B2E02` only: decode the identical frozen P0 public-human subset with candidate cell 2 (`moonshine-balanced`) under unchanged frozen C0", "current frontier exact B2E02 candidate/action identity")\\n', '    require_text(current, "Execute and canonically qualify `B2E03` only: decode the identical frozen P0 public-human subset with candidate cell 3 (`whispercpp-compact`) under unchanged frozen C0", "current frontier exact B2E03 candidate/action identity")\\n'),
    ('    require_text(current, "B2E03 and all later candidate cells remain unauthorized", "current frontier successor boundary")\\n', '    require_text(current, "B2E04 and all later candidate cells remain unauthorized", "current frontier successor boundary")\\n'),
    ('    require_text(current, "B2E01 is canonical and B2E02 is now the only authorized bounded unit", "current frontier B2E02 baseline summary")\\n', '    require_text(current, "B2E01 and B2E02 are canonical. B2E03 (`whispercpp-compact`) is now the only authorized bounded unit", "current frontier B2E03 baseline summary")\\n'),
    ('    require_text(current, "B2P01 through B2P08 and B2E01 are complete.", "current frontier post-B2E01 completion")\\n', '    require_text(current, "B2P01 through B2P08, B2E01, and B2E02 are complete.", "current frontier post-B2E02 completion")\\n'),
    ('    require_text(current, "B2E02 (`moonshine-balanced`) is the sole current bounded execution unit.", "current frontier B2E02 active-route authority")\\n', '    require_text(current, "B2E03 (`whispercpp-compact`) is the sole current bounded execution unit.", "current frontier B2E03 active-route authority")\\n'),
    ('    require_text(current_state, "current bounded execution unit is `B2E02`", "current state")\\n', '    require_text(current_state, "current bounded execution unit is `B2E03`", "current state")\\n'),
]
for index, (old, new) in enumerate(replacements, start=1):
    text = once(text, old, new, f"methodology current frontier assertion {index}")
current_proof_anchor = '    require_text(current, f"job `{B2E01_POSTMERGE_EVIDENCE_JOB_ID}`", "current frontier B2E01 evidence job proof")\\n'
current_proof_new = current_proof_anchor + '''    require_text(current, B2E02_CANONICAL_MERGE, "current frontier B2E02 canonical proof")\n    require_text(current, B2E02_QUALIFIED_HEAD, "current frontier B2E02 qualified-head proof")\n    for run_id in (B2E02_POSTMERGE_EVIDENCE_RUN_ID, B2E02_POSTMERGE_METHODOLOGY_RUN_ID, B2E02_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID, B2E02_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID, B2E02_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID, B2E02_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID, B2E02_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID):\n        require_text(current, f"run `{run_id}`", "current frontier B2E02 post-merge proof")\n'''
text = once(text, current_proof_anchor, current_proof_new, "methodology current B2E02 proof checks")
state_proof_anchor = '    require_text(current_state, B2E01_QUALIFIED_HEAD, "current state B2E01 qualified-head proof")\\n'
state_proof_new = state_proof_anchor + '''    require_text(current_state, B2E02_CANONICAL_MERGE, "current state B2E02 canonical proof")\n    require_text(current_state, B2E02_QUALIFIED_HEAD, "current state B2E02 qualified-head proof")\n    for run_id in (B2E02_POSTMERGE_EVIDENCE_RUN_ID, B2E02_POSTMERGE_METHODOLOGY_RUN_ID, B2E02_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID, B2E02_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID, B2E02_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID, B2E02_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID, B2E02_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID):\n        require_text(current_state, f"`{run_id}`", "current state B2E02 post-merge proof")\n'''
text = once(text, state_proof_anchor, state_proof_new, "methodology current-state B2E02 proof checks")
write(p, text)

# Extend the historical B2P04 verifier through the exact B2E02 reconciled phase.
p = Path("research/000b2-public/verify_subset_freeze.py")
text = read(p)
text = once(
    text,
    '    require(attempt.get("frozen") is (readiness.get("completed_through") in {"B2P08", "B2E01"}), "B2P08 freeze state must match reconciliation phase")\\n',
    '    require(attempt.get("frozen") is (readiness.get("completed_through") in {"B2P08", "B2E01", "B2E02"}), "B2P08 freeze state must remain frozen through B2E02 reconciliation")\\n',
    "subset frozen phase",
)
text = once(
    text,
    '    if completed_through in {"B2P07", "B2P08", "B2E01"}:\\n',
    '    if completed_through in {"B2P07", "B2P08", "B2E01", "B2E02"}:\\n',
    "subset environment phase",
)
b2e01_block = '''    if completed_through == "B2E01":\n        require(preprocessing.get("resolved") is True, "B2E01 reconciliation must preserve preprocessing resolution")\n        require(environment.get("resolved") is True, "B2E01 reconciliation must preserve environment resolution")\n        require(public.get("subset_manifest_frozen") is True, "B2E01 reconciliation must preserve the B2P04 frozen manifest")\n        require(isinstance(next_action, str) and next_action.startswith("Execute B2E02 only:"), "B2E01 reconciliation must authorize B2E02 only")\n        require("Do not begin B2E03 or any later candidate cell until B2E02 is canonical." in next_action, "B2E02 successor boundary drift")\n        require("- [x] `B2P08`" in tasks, "B2P08 must remain complete")\n        require("- [x] `B2E01`" in tasks, "B2E01 reconciliation must mark B2E01 complete")\n        require("- [ ] `B2E02`" in tasks, "B2E02 must remain pending before execution")\n        require("current bounded execution unit `B2E02`" in current, "reconciled frontier is not B2E02-only")\n        require("Execute and canonically qualify `B2E02` only" in current, "reconciled current view must authorize B2E02 only")\n        require("B2E03 and all later candidate cells remain unauthorized" in current, "reconciled frontier must keep later candidate cells closed")\n        return "B2E01"\n\n'''
b2e02_block = b2e01_block + '''    if completed_through == "B2E02":\n        require(preprocessing.get("resolved") is True, "B2E02 reconciliation must preserve preprocessing resolution")\n        require(environment.get("resolved") is True, "B2E02 reconciliation must preserve environment resolution")\n        require(public.get("subset_manifest_frozen") is True, "B2E02 reconciliation must preserve the B2P04 frozen manifest")\n        require(attempt.get("frozen") is True, "B2E02 reconciliation must preserve the frozen attempt")\n        require(isinstance(next_action, str) and next_action.startswith("Execute B2E03 only:"), "B2E02 reconciliation must authorize B2E03 only")\n        require("Do not begin B2E04 or any later candidate cell until B2E03 is canonical." in next_action, "B2E03 successor boundary drift")\n        require("- [x] `B2E02`" in tasks, "B2E02 reconciliation must mark B2E02 complete")\n        require("- [ ] `B2E03`" in tasks, "B2E03 must remain pending before execution")\n        require("current bounded execution unit `B2E03`" in current, "reconciled frontier is not B2E03-only")\n        require("Execute and canonically qualify `B2E03` only" in current, "reconciled current view must authorize B2E03 only")\n        require("B2E04 and all later candidate cells remain unauthorized" in current, "reconciled frontier must keep later candidate cells closed")\n        return "B2E02"\n\n'''
text = once(text, b2e01_block, b2e02_block, "subset exact B2E02 branch")
write(p, text)

"""
script = script.replace(insertion_anchor, extension + insertion_anchor)

state_write_anchor = 'text = text.replace("B2E03 and all later candidate cells remain unauthorized until B2E02", "B2E04 and all later candidate cells remain unauthorized until B2E03")\nwrite(p, text)\n'
state_write_new = 'text = text.replace("B2E03 and all later candidate cells remain unauthorized until B2E02", "B2E04 and all later candidate cells remain unauthorized until B2E03")\ntext = text.replace("current bounded execution unit is `B2E02`", "current bounded execution unit is `B2E03`", 1)\nwrite(p, text)\n'
if script.count(state_write_anchor) != 1:
    raise SystemExit(f'CURRENT_STATE live-frontier anchor drift: {script.count(state_write_anchor)}')
script = script.replace(state_write_anchor, state_write_new, 1)

preprocess_call = 'PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_preprocessing_capture.py\n'
if script.count(preprocess_call) != 1:
    raise SystemExit(f'preprocessing verification invocation drift: {script.count(preprocess_call)}')
script = script.replace(preprocess_call, 'PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_preprocessing_capture.py --static-only\n', 1)

OUT.write_text(script, encoding='utf-8')
print(f'WROTE={OUT}')
