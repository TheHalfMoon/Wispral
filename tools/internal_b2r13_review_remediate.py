#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

VERIFIER = Path("research/000b2-public/verify_attempt_002_invalidation.py")
READINESS = Path("research/000b2-public/recovery-attempt-003-readiness.json")
SPEC = Path("specs/000B2-public-corpus-bakeoff/recovery-v2.md")

FIXTURE = {
    "material_class": "DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY",
    "fixture_id": "b2r14-sherpa-result-string-contract-v1",
    "sample_rate_hz": 16000,
    "channel_count": 1,
    "sample_format": "PCM_S16LE",
    "frame_count": 16000,
    "pcm_sha256": "0c92bddb4e96f3ea9ec9f0f64a668255a6c15527ac09f6f119cafde60c7c4a39",
    "primary_corpus_access": False,
    "frozen_p0_access": False,
    "attempt_003_primary_evidence_access": False,
}

text = VERIFIER.read_text(encoding="utf-8")
marker = "\n\n# Exact ATTEMPT-002 bytes that were canonical when the defect was discovered.\n"
if marker not in text:
    raise SystemExit("contract insertion marker drift")
contract = '''

B2R14_NON_PRIMARY_FIXTURE_CONTRACT = {
    "material_class": "DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY",
    "fixture_id": "b2r14-sherpa-result-string-contract-v1",
    "sample_rate_hz": 16000,
    "channel_count": 1,
    "sample_format": "PCM_S16LE",
    "frame_count": 16000,
    "pcm_sha256": "0c92bddb4e96f3ea9ec9f0f64a668255a6c15527ac09f6f119cafde60c7c4a39",
    "primary_corpus_access": False,
    "frozen_p0_access": False,
    "attempt_003_primary_evidence_access": False,
}
B2R14_FORBIDDEN_PRIMARY_MARKERS = (
    "research/000b2-public/preprocessing-capture.json",
    "research/000b2-public/subset-manifest.json",
    "research/000b2-public/raw",
    "research/000b2-public/preprocessed",
    "research/000b2-public/transcripts",
    "attempt-003-manifest.json",
    "b2r17-",
    "b2r18-",
    "b2r19-",
    "b2r20-",
    "b2r21-",
    "b2r22-",
)
'''
text = text.replace(marker, contract + marker, 1)

function_marker = "def verify_active_task_candidate_content(readiness: dict[str, Any], active: str | None, completed: list[str]) -> None:\n"
if function_marker not in text:
    raise SystemExit("active-task function marker drift")
helpers = r'''def verify_b2r13_candidate_content(readiness: dict[str, Any]) -> None:
    authority_base = os.environ.get("AUTHORITY_BASE_REVISION", "")
    if not authority_base:
        return
    changed = run_git("diff", "--name-only", "--diff-filter=ACMRTUXB", authority_base, "HEAD", "--")
    changed_paths = [path for path in changed.splitlines() if path]
    scopes = readiness.get("task_candidate_scopes")
    require(isinstance(scopes, dict), "task_candidate_scopes must be an object")
    expected = scopes.get("B2R13")
    require(isinstance(expected, list), "missing exact B2R13 candidate scope")
    require(sorted(changed_paths) == sorted(expected), "B2R13 candidate must match the exact activation path set")
    workflow_patterns = (
        r"\bpython(?:3)?\s+[^\n]*decode_b2r(?:0[5-9]|1[0-9]|2[0-4])\.py\b",
        r"\.create_stream\s*\(",
        r"\.accept_waveform\s*\(",
        r"\.decode_stream\s*\(",
        r"\.input_finished\s*\(",
        r"\.transcribe\s*\(",
    )
    for path in changed_paths:
        payload = run_git("show", f"HEAD:{path}")
        if path.endswith(".py"):
            tree = ast.parse(payload, filename=path)
            calls = {call_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
            forbidden_decode = sorted(calls & DECODE_CALL_NAMES)
            forbidden_scoring = sorted(calls & SCORING_CALL_NAMES)
            require(not forbidden_decode, f"B2R13 forbids decode-runtime calls in {path}: {', '.join(forbidden_decode)}")
            require(not forbidden_scoring, f"B2R13 forbids scoring calls in {path}: {', '.join(forbidden_scoring)}")
        elif path.endswith((".yml", ".yaml")):
            for pattern in workflow_patterns:
                require(re.search(pattern, payload, flags=re.IGNORECASE) is None,
                        f"B2R13 workflow contains primary-decode execution pattern {pattern}: {path}")


def verify_b2r14_non_primary_candidate(readiness: dict[str, Any]) -> None:
    require(readiness.get("b2r14_non_primary_fixture_contract") == B2R14_NON_PRIMARY_FIXTURE_CONTRACT,
            "B2R14 canonical non-primary fixture contract drift")
    authority_base = os.environ.get("AUTHORITY_BASE_REVISION", "")
    if not authority_base:
        return
    changed = run_git("diff", "--name-only", "--diff-filter=ACMRTUXB", authority_base, "HEAD", "--")
    changed_paths = [path for path in changed.splitlines() if path]
    harness_path = "research/000b2-public/b2r14-sherpa-result-harness.py"
    qualification_path = "research/000b2-public/b2r14-harness-qualification.json"
    workflow_path = ".github/workflows/000b2-public-b2r14-sherpa-result-harness.yml"
    require(harness_path in changed_paths and qualification_path in changed_paths and workflow_path in changed_paths,
            "B2R14 candidate must include canonical harness, qualification, and workflow artifacts")
    for path in changed_paths:
        payload = run_git("show", f"HEAD:{path}")
        lowered = payload.lower()
        for forbidden in B2R14_FORBIDDEN_PRIMARY_MARKERS:
            require(forbidden.lower() not in lowered, f"B2R14 candidate may not reference primary material marker {forbidden}: {path}")
        if path == harness_path:
            tree = ast.parse(payload, filename=path)
            strings = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
            for value in (
                B2R14_NON_PRIMARY_FIXTURE_CONTRACT["material_class"],
                B2R14_NON_PRIMARY_FIXTURE_CONTRACT["fixture_id"],
                B2R14_NON_PRIMARY_FIXTURE_CONTRACT["sample_format"],
                B2R14_NON_PRIMARY_FIXTURE_CONTRACT["pcm_sha256"],
            ):
                require(value in strings, f"B2R14 harness must bind exact non-primary fixture value: {value}")
            calls = {call_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
            require("get_result" in calls, "B2R14 harness must exercise the pinned sherpa get_result API")
        elif path == qualification_path:
            document = json.loads(payload)
            require(document.get("non_primary_fixture") == B2R14_NON_PRIMARY_FIXTURE_CONTRACT,
                    "B2R14 qualification must bind exact canonical non-primary fixture contract")
        elif path == workflow_path:
            require("b2r14-sherpa-result-harness.py" in lowered, "B2R14 workflow must invoke canonical harness")
            require(B2R14_NON_PRIMARY_FIXTURE_CONTRACT["pcm_sha256"] in payload,
                    "B2R14 workflow must bind exact canonical fixture digest")


'''
text = text.replace(function_marker, helpers + function_marker, 1)
old_gate = '''def verify_active_task_candidate_content(readiness: dict[str, Any], active: str | None, completed: list[str]) -> None:
    if active is None or active == "B2R13":
        return
'''
new_gate = '''def verify_active_task_candidate_content(readiness: dict[str, Any], active: str | None, completed: list[str]) -> None:
    if active is None:
        return
    if active == "B2R13":
        verify_b2r13_candidate_content(readiness)
        return
    if active == "B2R14":
        verify_b2r14_non_primary_candidate(readiness)
'''
if old_gate not in text:
    raise SystemExit("active-task gate drift")
text = text.replace(old_gate, new_gate, 1)
policy_line = '    require(readiness.get("task_content_policies") == expected_task_content_policies(), "successor task content policy drift")\n'
if policy_line not in text:
    raise SystemExit("successor policy marker drift")
text = text.replace(policy_line, policy_line + '    require(readiness.get("b2r14_non_primary_fixture_contract") == B2R14_NON_PRIMARY_FIXTURE_CONTRACT, "B2R14 canonical non-primary fixture contract drift")\n', 1)
VERIFIER.write_text(text, encoding="utf-8")

readiness = json.loads(READINESS.read_text(encoding="utf-8"))
readiness["b2r14_non_primary_fixture_contract"] = FIXTURE
READINESS.write_text(json.dumps(readiness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

spec = SPEC.read_text(encoding="utf-8")
anchor = "B2R14's runtime-call exception is not primary-decode authority. Its task-specific verifier and workflow must prove that qualification material is non-primary, that no frozen P0 primary material is accessed, that the exact pinned sherpa API is exercised, and that object/string API confusion fails closed. A B2R14 task candidate that cannot prove those boundaries is ineligible even though runtime API calls are syntactically present.\n"
addition = anchor + "\nThe canonical B2R14 qualification fixture is frozen before B2R14 begins: `DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY`, fixture id `b2r14-sherpa-result-string-contract-v1`, mono PCM S16LE at 16 kHz, 16000 frames, with exact PCM SHA-256 `0c92bddb4e96f3ea9ec9f0f64a668255a6c15527ac09f6f119cafde60c7c4a39`. The common successor verifier—not the B2R14-supplied verifier—must bind this contract and reject frozen P0, ATTEMPT-003 primary evidence, transcript, or successor decode artifact access from the B2R14 harness/workflow.\n"
if anchor not in spec:
    raise SystemExit("recovery-v2 B2R14 marker drift")
SPEC.write_text(spec.replace(anchor, addition, 1), encoding="utf-8")
