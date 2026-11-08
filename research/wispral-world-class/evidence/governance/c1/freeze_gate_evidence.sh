#!/usr/bin/env bash
# C1 finding-4 evidence: the pre-correction freeze gate (definition at $BASE) on the C1 head and on
# the authority base, plainly and with its B2R16 task-time classifications neutralized.
set -uo pipefail
cd "$(dirname "$0")"
H=$PWD
BASE=${BASE:?}
C1=${C1:?}
OUT=${OUT:?}
WF=.github/workflows/000b2-public-b2r16-freeze.yml
V=research/000b2-public/verify_b2r16.py
mkdir -p "$OUT"
for n in fz-c1 fz-base fz-c1n fz-basen; do git -C c1 worktree remove --force "cand/$n" 2>/dev/null; rm -rf "cand/$n"; done
git -C c1 worktree add -q --detach "$H/cand/fz-c1" "$C1"
git -C c1 worktree add -q --detach "$H/cand/fz-base" "$BASE"
git -C c1 worktree add -q --detach "$H/cand/fz-c1n" "$C1"
git -C c1 worktree add -q --detach "$H/cand/fz-basen" "$BASE"

gate() { # name workdir
  python -I run_gate_steps.py --repo "$H/c1" --ref "$BASE" --workflow $WF --job verify-b2r16-freeze \
    --workdir "$2" --env EXACT_REVISION="$(git -C "$2" rev-parse HEAD)" > "$OUT/freeze_$1.txt" 2>&1
}
neutralize() { # workdir level: 1 = range only, 2 = range and task-time authority
  python -I - "$1/$V" "$2" <<'PY'
import sys
from pathlib import Path
p, level = Path(sys.argv[1]), int(sys.argv[2])
s = p.read_text(encoding="utf-8")
patches = [('    require(changed_paths == sorted(EXPECTED_SCOPE), "B2R16 actual candidate range scope drift")\n',
            '    print("B2R16_RANGE_CLASSIFICATION_NEUTRALIZED")\n')]
if level >= 2:
    patches.append(("def verify_authority() -> None:\n",
                    'def verify_authority() -> None:\n    print("B2R16_TASK_AUTHORITY_CLASSIFICATION_NEUTRALIZED")\n    return\n'))
for old, new in patches:
    assert s.count(old) == 1, old
    s = s.replace(old, new)
p.write_bytes(s.encode("utf-8"))
PY
}
gate c1 cand/fz-c1
gate base cand/fz-base
for level in 1 2; do
  for n in c1 base; do
    git -C "cand/fz-${n}n" checkout -q -- "$V"
    neutralize "cand/fz-${n}n" $level
    gate "${n}-neutralized-${level}" "cand/fz-${n}n"
    git -C "cand/fz-${n}n" diff --stat -- "$V" | tail -1 >> "$OUT/freeze_${n}-neutralized-${level}.txt"
  done
done
for n in c1n basen; do git -C "cand/fz-$n" checkout -q -- "$V"; git -C "cand/fz-$n" status --short; done
grep -H -E "^## STEP|=FAIL|NEUTRALIZED|=PASS|file changed" "$OUT"/freeze_*.txt | grep -v "uses " | sed "s#$OUT/##"
echo FREEZE_DONE
