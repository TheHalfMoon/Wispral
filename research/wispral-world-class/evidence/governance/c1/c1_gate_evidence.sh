#!/usr/bin/env bash
# C1 Principle XVII item 5 evidence: cause (counterfactual) and non-concealment runs of the two
# base-defined B2 gates (definitions at $BASE, default edacdf7), executed by run_gate_steps.py.
set -uo pipefail
cd "$(dirname "$0")"
H=$PWD
BASE=${BASE:-edacdf7504302cc91ff7138bc6ac2d391e4df1f4}
TP=.github/workflows/000b2-public-attempt-003-trusted-pr.yml
RC=.github/workflows/000b2-public-attempt-003-recovery.yml
GHT=$(gh auth token)
OUT=${OUT:-$H/evidence}
mkdir -p "$OUT"

trusted() { # name workdir extra-args...
  local name=$1 dir=$2; shift 2
  python -I run_gate_steps.py --repo "$H/c1" --ref $BASE --workflow $TP --job verify-successor-pr-from-canonical-base \
    --workdir "$dir" --env EXACT_REVISION="$(git -C "$dir" rev-parse HEAD)" --env AUTHORITY_BASE_REVISION=$BASE \
    --env GITHUB_EVENT_NAME=pull_request_target --env RUNNER_TEMP="$H/rt" "$@" > "$OUT/trusted-pr_$name.txt" 2>&1
}
recovery() {
  local name=$1 dir=$2; shift 2
  python -I run_gate_steps.py --repo "$H/c1" --ref $BASE --workflow $RC --job verify-successor-recovery \
    --workdir "$dir" --env EXACT_REVISION="$(git -C "$dir" rev-parse HEAD)" --env AUTHORITY_BASE_REVISION=$BASE \
    --env GITHUB_EVENT_NAME=pull_request --env GITHUB_REPOSITORY=TheHalfMoon/Wispral --env RUNNER_TEMP="$H/rt" \
    --env "GH_TOKEN=$GHT" "$@" > "$OUT/recovery_$name.txt" 2>&1
}

# Cause: C1, C1 with all declared paths reverted (= base), in-scope #120 head, #120 head plus C1 bytes.
for n in c1 base pr120 pr120c1; do
  trusted "$n" "cand/$n"
  recovery "$n" "cand/$n"
done

# Non-concealment: on the C1 head, neutralize only the over-applied task-candidate classification.
# Inline steps: the scope-violation raise becomes a print. Common verifier: a working-tree-only
# early return after the reconciliation branch of verify_active_task_candidate_content (the
# committed bytes, which the gates compare as Git objects, are unchanged).
V=cand/c1n/research/000b2-public/verify_attempt_002_invalidation.py
python -I - "$V" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
old = "    if delta != 0:\n        return\n    if active == \"B2R14\":\n"
new = "    if delta != 0:\n        return\n    return  # XVII.5(b) neutralization: not a task candidate\n    if active == \"B2R14\":\n"
assert s.count(old) == 1
p.write_bytes(s.replace(old, new).encode("utf-8"))
print("neutralized", p)
PY
git -C cand/c1n diff --stat
trusted c1-neutralized cand/c1n \
  --patch 'Verify trusted-base event and immutable control boundary::raise SystemExit(f"TRUSTED_PR_GATE=FAIL: {active} candidate path scope violation")::print(f"TRUSTED_PR_GATE_NEUTRALIZED={active} candidate path scope violation")'
recovery c1-neutralized cand/c1n \
  --patch 'Trusted pre-candidate execution boundary::raise SystemExit(f"TRUSTED_BOUNDARY=FAIL: {active} task-candidate path scope violation")::print(f"TRUSTED_BOUNDARY_NEUTRALIZED={active} task-candidate path scope violation")'
git -C cand/c1n checkout -- research/000b2-public/verify_attempt_002_invalidation.py
git -C cand/c1n status --short
grep -H -E "^## STEP|=FAIL|NEUTRALIZED|=PASS$|PASS$" "$OUT"/*.txt | grep -v "uses " | sed "s#$OUT/##"
echo DRIVER_DONE
