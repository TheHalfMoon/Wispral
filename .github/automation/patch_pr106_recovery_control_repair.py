#!/usr/bin/env python3
"""Apply the exact forward-only PR #106 Recovery control-repair patch."""

from __future__ import annotations

from pathlib import Path
import subprocess

VERIFIER_PATH = Path("research/000b2-public/verify_attempt_002_invalidation.py")
RECOVERY_WORKFLOW_PATH = Path(".github/workflows/000b2-public-attempt-003-recovery.yml")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one replacement target, found {count}")
    return text.replace(old, new, 1)


def patch_verifier(text: str) -> str:
    text = replace_once(
        text,
        'SHERPA_RETURN = "return self.recognizer.get_result(s).text.strip()"\n',
        'SHERPA_RETURN = "return self.recognizer.get_result(s).text.strip()"\n'
        'CONTROL_REPAIR_AUTHORITY_BASE = "7941ab8b783a22d75e73a05552f8063507048f28"\n'
        'CONTROL_REPAIR_BASE_VERIFIER_BLOB = "8bc3135e961c235194209a40e6665390ed698f6b"\n'
        'CONTROL_REPAIR_BASE_RECOVERY_WORKFLOW_BLOB = "213ebf238aa7eab02d69633d021165d47c006de1"\n'
        'CONTROL_REPAIR_VERIFIER_PATH = "research/000b2-public/verify_attempt_002_invalidation.py"\n'
        'CONTROL_REPAIR_RECOVERY_WORKFLOW_PATH = ".github/workflows/000b2-public-attempt-003-recovery.yml"\n'
        'CONTROL_REPAIR_SCOPE = [CONTROL_REPAIR_RECOVERY_WORKFLOW_PATH, CONTROL_REPAIR_VERIFIER_PATH]\n',
        "verifier constants",
    )

    regression = '''def verify_exact_scope_regression_contract() -> None:
    """Prove exact-scope matching accepts complete sets and rejects missing or extra paths."""
    expected = ["scope/a", "scope/b"]
    require(
        exact_scope_matches(["scope/b", "scope/a"], expected),
        "exact-scope regression rejected the complete path set",
    )
    require(
        not exact_scope_matches(["scope/a"], expected),
        "exact-scope regression accepted an incomplete path set",
    )
    require(
        not exact_scope_matches(["scope/a", "scope/b", "scope/c"], expected),
        "exact-scope regression accepted an extra path",
    )


'''
    control = regression + '''def verify_control_repair_candidate(
    readiness: dict[str, Any], active: str | None, completed: list[str]
) -> None:
    """Validate the exact exceptional trusted-control repair boundary."""
    authority_base = os.environ.get("AUTHORITY_BASE_REVISION", "")
    require(authority_base == CONTROL_REPAIR_AUTHORITY_BASE, "control repair authority base mismatch")
    require(active == "B2R16", "control repair is authorized only while B2R16 remains active")
    changed = run_git("diff", "--name-only", "--diff-filter=ACMRTUXB", authority_base, "HEAD", "--")
    changed_paths = [path for path in changed.splitlines() if path]
    require(
        exact_scope_matches(changed_paths, CONTROL_REPAIR_SCOPE),
        "control repair candidate must match the exact trusted-control repair path set",
    )
    base_text = run_git(
        "show", f"{authority_base}:research/000b2-public/recovery-attempt-003-readiness.json"
    )
    try:
        base_state = json.loads(base_text)
    except json.JSONDecodeError as error:
        raise SystemExit("ATTEMPT_002_INVALIDATION=FAIL: control repair authority readiness malformed") from error
    require(readiness == base_state, "control repair must not change successor readiness state")
    base_completed = base_state.get("completed_recovery_tasks")
    require(isinstance(base_completed, list), "control repair authority completion state malformed")
    require(completed == base_completed, "control repair must not advance recovery completion state")
    trusted = base_state.get("trusted_control_paths")
    transition = base_state.get("transition_policy")
    require(isinstance(trusted, list), "control repair trusted-control path set missing")
    require(isinstance(transition, dict), "control repair transition policy missing")
    immutable = transition.get("immutable_execution_control_paths")
    require(isinstance(immutable, list), "control repair immutable execution-control set missing")
    repair_set = set(CONTROL_REPAIR_SCOPE)
    require(repair_set <= set(trusted), "control repair scope is not fully trusted control")
    require(repair_set <= set(immutable), "control repair scope is not fully immutable execution control")
    require(
        git_blob(authority_base, CONTROL_REPAIR_VERIFIER_PATH) == CONTROL_REPAIR_BASE_VERIFIER_BLOB,
        "control repair base verifier blob mismatch",
    )
    require(
        git_blob(authority_base, CONTROL_REPAIR_RECOVERY_WORKFLOW_PATH)
        == CONTROL_REPAIR_BASE_RECOVERY_WORKFLOW_BLOB,
        "control repair base Recovery workflow blob mismatch",
    )
    constitution = run_git("show", f"{authority_base}:CONSTITUTION.md")
    for marker in (
        "Principle XVI",
        "Trusted-control repair is fail-closed and exceptional",
        "every exact-head gate required by canonical repository authority",
    ):
        require(marker in constitution, f"control repair authority missing Constitution marker: {marker}")


'''
    text = replace_once(text, regression, control, "control repair verifier function")
    text = replace_once(
        text,
        "def verify_successor_frontier() -> None:\n",
        "def verify_successor_frontier(*, control_repair: bool = False) -> None:\n",
        "successor frontier signature",
    )
    text = replace_once(
        text,
        "    verify_active_task_candidate_content(readiness, active, completed)\n",
        "    if control_repair:\n"
        "        verify_control_repair_candidate(readiness, active, completed)\n"
        "    else:\n"
        "        verify_active_task_candidate_content(readiness, active, completed)\n",
        "successor frontier repair dispatch",
    )
    text = replace_once(
        text,
        '    parser.add_argument("--static-only", action="store_true")\n'
        "    args = parser.parse_args()\n"
        '    require(not (args.static_only and args.sherpa_source), "choose either --static-only or --sherpa-source")\n',
        '    parser.add_argument("--static-only", action="store_true")\n'
        '    parser.add_argument("--control-repair", action="store_true")\n'
        "    args = parser.parse_args()\n"
        '    require(not (args.static_only and args.sherpa_source), "choose either --static-only or --sherpa-source")\n'
        "    require(\n"
        '        not args.control_repair or bool(os.environ.get("AUTHORITY_BASE_REVISION")),\n'
        '        "--control-repair requires AUTHORITY_BASE_REVISION",\n'
        "    )\n",
        "control repair CLI",
    )
    text = replace_once(
        text,
        "    verify_successor_frontier()\n",
        "    verify_successor_frontier(control_repair=args.control_repair)\n",
        "control repair frontier invocation",
    )
    text = replace_once(
        text,
        '    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")\n',
        '    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")\n'
        "    if args.control_repair:\n"
        '        print("TRUSTED_CONTROL_REPAIR_COMMON_VERIFIER=PASS")\n',
        "control repair pass marker",
    )
    return text


def patch_recovery_workflow(text: str, verifier_blob: str) -> str:
    old_boundary = '''              is_reconciliation = delta == 1

              four_authority = {
                  "docs/canonical/CURRENT_STATE.md",
                  "research/000b2-public/recovery-attempt-003-readiness.json",
                  "specs/000B2-public-corpus-bakeoff/recovery-v2-tasks.md",
                  "specs/CURRENT.md",
              }
              if is_reconciliation:
                  if not changed or not changed <= four_authority:
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: reconciliation may change only canonical authority files")
              elif active and changed:
                  allowed = set(scopes.get(active, []))
                  if not changed <= allowed:
                      raise SystemExit(f"TRUSTED_BOUNDARY=FAIL: {active} task-candidate path scope violation")
'''
    new_boundary = '''              is_reconciliation = delta == 1
              control_repair_scope = {
                  ".github/workflows/000b2-public-attempt-003-recovery.yml",
                  "research/000b2-public/verify_attempt_002_invalidation.py",
              }
              is_control_repair = changed == control_repair_scope

              four_authority = {
                  "docs/canonical/CURRENT_STATE.md",
                  "research/000b2-public/recovery-attempt-003-readiness.json",
                  "specs/000B2-public-corpus-bakeoff/recovery-v2-tasks.md",
                  "specs/CURRENT.md",
              }
              if is_control_repair:
                  if base != "7941ab8b783a22d75e73a05552f8063507048f28":
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair authority base mismatch")
                  if active != "B2R16" or completed != base_completed:
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair may not advance recovery state")
                  if state != base_state:
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair may not change successor readiness")
                  base_trusted = base_state.get("trusted_control_paths")
                  transition = base_state.get("transition_policy")
                  immutable = transition.get("immutable_execution_control_paths") if isinstance(transition, dict) else None
                  if not isinstance(base_trusted, list) or not isinstance(immutable, list):
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair trusted/immutable authority missing")
                  if not control_repair_scope <= set(base_trusted) or not control_repair_scope <= set(immutable):
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair scope is not canonical trusted immutable control")
                  base_verifier_blob = subprocess.run(
                      ["git", "rev-parse", f"{base}:research/000b2-public/verify_attempt_002_invalidation.py"],
                      check=True, text=True, stdout=subprocess.PIPE,
                  ).stdout.strip()
                  base_workflow_blob = subprocess.run(
                      ["git", "rev-parse", f"{base}:.github/workflows/000b2-public-attempt-003-recovery.yml"],
                      check=True, text=True, stdout=subprocess.PIPE,
                  ).stdout.strip()
                  head_verifier_blob = subprocess.run(
                      ["git", "rev-parse", "HEAD:research/000b2-public/verify_attempt_002_invalidation.py"],
                      check=True, text=True, stdout=subprocess.PIPE,
                  ).stdout.strip()
                  if base_verifier_blob != "8bc3135e961c235194209a40e6665390ed698f6b":
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair base verifier blob mismatch")
                  if base_workflow_blob != "213ebf238aa7eab02d69633d021165d47c006de1":
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair base Recovery workflow blob mismatch")
                  if head_verifier_blob != "__FINAL_VERIFIER_BLOB__":
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair candidate verifier blob mismatch")
                  constitution = subprocess.run(
                      ["git", "show", f"{base}:CONSTITUTION.md"],
                      check=True, text=True, stdout=subprocess.PIPE,
                  ).stdout
                  required_markers = (
                      "Principle XVI",
                      "Trusted-control repair is fail-closed and exceptional",
                      "every exact-head gate required by canonical repository authority",
                  )
                  if any(marker not in constitution for marker in required_markers):
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: control repair Constitution authority missing")
                  github_env = os.environ.get("GITHUB_ENV")
                  if not github_env:
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: GITHUB_ENV unavailable for control repair")
                  with open(github_env, "a", encoding="utf-8") as handle:
                      handle.write("CONTROL_REPAIR=1\\n")
                  print("TRUSTED_CONTROL_REPAIR_BOUNDARY=PASS")
              elif is_reconciliation:
                  if not changed or not changed <= four_authority:
                      raise SystemExit("TRUSTED_BOUNDARY=FAIL: reconciliation may change only canonical authority files")
              elif active and changed:
                  allowed = set(scopes.get(active, []))
                  if not changed <= allowed:
                      raise SystemExit(f"TRUSTED_BOUNDARY=FAIL: {active} task-candidate path scope violation")
'''.replace("__FINAL_VERIFIER_BLOB__", verifier_blob)
    text = replace_once(text, old_boundary, new_boundary, "Recovery control repair boundary")

    old_static = '''          if test "$ACTIVE_UNIT" = "B2R13"; then
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_b2r13_activation.py --static-only
          else
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_attempt_002_invalidation.py --static-only
          fi
'''
    new_static = '''          if test "${CONTROL_REPAIR:-0}" = "1"; then
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_attempt_002_invalidation.py \
              --static-only --control-repair
          elif test "$ACTIVE_UNIT" = "B2R13"; then
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_b2r13_activation.py --static-only
          else
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_attempt_002_invalidation.py --static-only
          fi
'''
    text = replace_once(text, old_static, new_static, "Recovery static verifier dispatch")

    old_live = '''          if test "$ACTIVE_UNIT" = "B2R13"; then
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_b2r13_activation.py \
              --sherpa-source "$RUNNER_TEMP/sherpa-onnx"
          else
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_attempt_002_invalidation.py \
              --sherpa-source "$RUNNER_TEMP/sherpa-onnx"
          fi
'''
    new_live = '''          if test "${CONTROL_REPAIR:-0}" = "1"; then
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_attempt_002_invalidation.py \
              --sherpa-source "$RUNNER_TEMP/sherpa-onnx" --control-repair
          elif test "$ACTIVE_UNIT" = "B2R13"; then
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_b2r13_activation.py \
              --sherpa-source "$RUNNER_TEMP/sherpa-onnx"
          else
            PYTHONDONTWRITEBYTECODE=1 python research/000b2-public/verify_attempt_002_invalidation.py \
              --sherpa-source "$RUNNER_TEMP/sherpa-onnx"
          fi
'''
    return replace_once(text, old_live, new_live, "Recovery pinned-source verifier dispatch")


def main() -> None:
    verifier = patch_verifier(VERIFIER_PATH.read_text(encoding="utf-8"))
    VERIFIER_PATH.write_text(verifier, encoding="utf-8")
    verifier_blob = subprocess.check_output(["git", "hash-object", str(VERIFIER_PATH)], text=True).strip()
    workflow = patch_recovery_workflow(RECOVERY_WORKFLOW_PATH.read_text(encoding="utf-8"), verifier_blob)
    RECOVERY_WORKFLOW_PATH.write_text(workflow, encoding="utf-8")
    print(f"FINAL_VERIFIER_BLOB={verifier_blob}")


if __name__ == "__main__":
    main()
