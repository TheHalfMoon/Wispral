#!/usr/bin/env python3
"""Temporary exact patcher for B2P05 frontier reconciliation; removed before PR."""

from pathlib import Path

path = Path("research/000b2-public/verify_methodology.py")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one occurrence, got {count}: {old[:120]!r}")
    text = text.replace(old, new, 1)


replace_once(
    'B2P04_POSTMERGE_METHODOLOGY_JOB_ID = 100779960182\n',
    'B2P04_POSTMERGE_METHODOLOGY_JOB_ID = 100779960182\n'
    'B2P05_CANONICAL_MERGE = "49538990fb4cf8223e9321261925206ed7ff5cee"\n'
    'B2P05_QUALIFIED_HEAD = "c62a7fa2998cd5292da78a66deb4a6d2044691b3"\n'
    'B2P05_POSTMERGE_REVALIDATION_RUN_ID = 33803832655\n'
    'B2P05_POSTMERGE_STATIC_JOB_ID = 100809416957\n'
    'B2P05_POSTMERGE_LIVE_JOB_ID = 100809480949\n'
    'B2P05_POSTMERGE_METHODOLOGY_RUN_ID = 33803832693\n'
    'B2P05_POSTMERGE_METHODOLOGY_JOB_ID = 100809418067\n'
    'B2P05_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID = 33803832706\n'
    'B2P05_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID = 33803832711\n'
    'B2P05_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID = 33803832717\n'
    'B2P05_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID = 33803832657\n',
)

replace_once(
    '    require(readiness.get("completed_through") == "B2P04", "readiness completed_through must be B2P04")\n',
    '    require(readiness.get("completed_through") == "B2P05", "readiness completed_through must be B2P05")\n',
)

replace_once(
    '    expected_next_action = (\n'
    '        "Execute B2P05 only: revalidate the six canonical candidate cells and artifact/runtime/model identities against live canonical evidence. "\n'
    '        "Do not begin candidate decoding, B2P06 preprocessing capture, or primary decoding until B2P05 is canonical."\n'
    '    )\n'
    '    require(readiness.get("next_action") == expected_next_action, "next action must be exact B2P05-only instruction")\n',
    '    expected_next_action = (\n'
    '        "Execute B2P06 only: capture attempt-bound FFmpeg 9.0.1 preprocessing identity, configuration, and execution evidence while preserving the frozen B2P04 source membership and canonical B2P05 candidate identities. "\n'
    '        "Do not begin B2P07 environment capture, B2P08 attempt freeze, or candidate decoding until B2P06 is canonical."\n'
    '    )\n'
    '    require(readiness.get("next_action") == expected_next_action, "next action must be exact B2P06-only instruction")\n',
)

replace_once(
    '        expected_marker = "- [x]" if task_id in {"B2P01", "B2P02", "B2P03", "B2P04"} else "- [ ]"\n',
    '        expected_marker = "- [x]" if task_id in {"B2P01", "B2P02", "B2P03", "B2P04", "B2P05"} else "- [ ]"\n',
)

replace_once(
    '    require_text(tasks, "- [x] `B2P04` Freeze selected public-human subset manifest and manifest digest before candidate decoding.", "public child tasks")\n',
    '    require_text(tasks, "- [x] `B2P04` Freeze selected public-human subset manifest and manifest digest before candidate decoding.", "public child tasks")\n'
    '    require_text(tasks, "- [x] `B2P05` Revalidate the six canonical candidate cells and artifact/runtime/model identities against live canonical evidence.", "public child tasks")\n'
    '    require_text(tasks, "- [ ] `B2P06` Capture attempt-bound FFmpeg `9.0.1` preprocessing identity/configuration and execution evidence.", "public child tasks")\n',
)

replace_once(
    '''    require_text(current, B2P04_POSTMERGE_ARTIFACT_DIGEST, "current frontier B2P04 post-merge artifact digest proof")
    require_text(current, B2P04_MANIFEST_SHA256, "current frontier B2P04 manifest SHA proof")
    require_text(current, B2P04_FREEZE_DIGEST_SHA256, "current frontier B2P04 freeze digest proof")
    require_text(current, "current bounded execution unit `B2P05`", "current frontier")
    require_text(current, "Execute and canonically qualify `B2P05` only", "current frontier next action")
    require_absent(current, "Execute and canonically qualify `B2P04` only", "current frontier stale next action")
    require_absent(current, "current bounded execution unit `B2P04`", "current frontier")
''',
    '''    require_text(current, B2P04_POSTMERGE_ARTIFACT_DIGEST, "current frontier B2P04 post-merge artifact digest proof")
    require_text(current, B2P04_MANIFEST_SHA256, "current frontier B2P04 manifest SHA proof")
    require_text(current, B2P04_FREEZE_DIGEST_SHA256, "current frontier B2P04 freeze digest proof")
    require_text(current, B2P05_CANONICAL_MERGE, "current frontier B2P05 canonical proof")
    require_text(current, B2P05_QUALIFIED_HEAD, "current frontier B2P05 qualified-head proof")
    require_text(current, f"run `{B2P05_POSTMERGE_REVALIDATION_RUN_ID}`", "current frontier B2P05 revalidation post-merge run proof")
    require_text(current, f"job `{B2P05_POSTMERGE_STATIC_JOB_ID}`", "current frontier B2P05 static post-merge job proof")
    require_text(current, f"job `{B2P05_POSTMERGE_LIVE_JOB_ID}`", "current frontier B2P05 live post-merge job proof")
    require_text(current, f"run `{B2P05_POSTMERGE_METHODOLOGY_RUN_ID}`", "current frontier B2P05 methodology post-merge run proof")
    require_text(current, f"job `{B2P05_POSTMERGE_METHODOLOGY_JOB_ID}`", "current frontier B2P05 methodology post-merge job proof")
    require_text(current, "current bounded execution unit `B2P06`", "current frontier")
    require_text(current, "Execute and canonically qualify `B2P06` only", "current frontier next action")
    require_text(current, "B2P07 remains non-authorized", "current frontier successor boundary")
    require_absent(current, "current bounded execution unit `B2P05`", "current frontier stale unit")
''',
)

replace_once(
    '''    require_text(current_state, B2P04_POSTMERGE_ARTIFACT_DIGEST, "current state B2P04 post-merge artifact digest proof")
    require_text(current_state, B2P04_MANIFEST_SHA256, "current state B2P04 manifest SHA proof")
    require_text(current_state, B2P04_FREEZE_DIGEST_SHA256, "current state B2P04 freeze digest proof")
    require_text(current_state, "current bounded execution unit is `B2P05`", "current state")
    require_absent(current_state, "current bounded execution unit is `B2P04`", "current state")
''',
    '''    require_text(current_state, B2P04_POSTMERGE_ARTIFACT_DIGEST, "current state B2P04 post-merge artifact digest proof")
    require_text(current_state, B2P04_MANIFEST_SHA256, "current state B2P04 manifest SHA proof")
    require_text(current_state, B2P04_FREEZE_DIGEST_SHA256, "current state B2P04 freeze digest proof")
    require_text(current_state, B2P05_CANONICAL_MERGE, "current state B2P05 canonical proof")
    require_text(current_state, B2P05_QUALIFIED_HEAD, "current state B2P05 qualified-head proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_REVALIDATION_RUN_ID}`", "current state B2P05 revalidation post-merge run proof")
    require_text(current_state, f"job `{B2P05_POSTMERGE_STATIC_JOB_ID}`", "current state B2P05 static post-merge job proof")
    require_text(current_state, f"job `{B2P05_POSTMERGE_LIVE_JOB_ID}`", "current state B2P05 live post-merge job proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_METHODOLOGY_RUN_ID}`", "current state B2P05 methodology post-merge run proof")
    require_text(current_state, f"job `{B2P05_POSTMERGE_METHODOLOGY_JOB_ID}`", "current state B2P05 methodology post-merge job proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID}`", "current state B2P05 trusted materialization run proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID}`", "current state B2P05 trusted participant-materials run proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID}`", "current state B2P05 trusted participant-policy run proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID}`", "current state B2P05 trusted human-authority run proof")
    require_text(current_state, "current bounded execution unit is `B2P06`", "current state")
    require_absent(current_state, "current bounded execution unit is `B2P05`", "current state stale unit")
''',
)

replace_once(
    '    print("B2P05_FRONTIER=AUTHORIZED")\n',
    '    print("B2P05_CANDIDATE_REVALIDATION=PASS")\n'
    '    print(f"B2P05_CANONICAL_MERGE={B2P05_CANONICAL_MERGE}")\n'
    '    print(f"B2P05_POSTMERGE_REVALIDATION_RUN_ID={B2P05_POSTMERGE_REVALIDATION_RUN_ID}")\n'
    '    print(f"B2P05_POSTMERGE_METHODOLOGY_RUN_ID={B2P05_POSTMERGE_METHODOLOGY_RUN_ID}")\n'
    '    print("B2P06_FRONTIER=AUTHORIZED")\n',
)

path.write_text(text, encoding="utf-8")
