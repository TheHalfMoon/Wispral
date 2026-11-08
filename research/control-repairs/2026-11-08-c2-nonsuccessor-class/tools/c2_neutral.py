"""C2 item 5 evidence, part 2.
(a) A3 per-blob: #120's changes plus exactly ONE changed immutable blob fail the immutable boundary for
    that blob only; #120 alone passes (see pre_*_pr120), so reverting that blob makes the boundary pass.
(b) Non-concealment: C2 on main's gate definitions with only the preserved checks neutralized
    (immutable boundary, byte-equality test, scope raise, and the task classification of the
    verifier, as a working-tree-only change); every step must then pass.
Usage: python -I c2_neutral.py <repo> <main> <c2> <outdir>"""
import json
import pathlib
import subprocess
import sys

sys.argv_saved = list(sys.argv)
REPO, MAIN, C2, OUT = sys.argv[1], sys.argv[2], sys.argv[3], pathlib.Path(sys.argv[4])
import runpy  # noqa: E402

sys.argv = ["c2_evidence.py", REPO, MAIN, C2, str(OUT), "none"]
g = runpy.run_path(str(pathlib.Path(__file__).with_name("c2_evidence.py")), run_name="lib")
overlay, worktree, gate = g["overlay"], g["worktree"], g["gate"]
TP, RC, VER, PR120, P120 = g["TP"], g["RC"], g["VER"], g["PR120"], g["P120_PATHS"]
summary = {"per_blob": {}, "neutralized": {}}

host = overlay(MAIN, PR120, P120, "Synthetic: #120 changes overlaid on main")
for label, path in (("trusted_pr_workflow", TP), ("recovery_workflow", RC), ("common_verifier", VER)):
    rev = overlay(host, C2, [path], f"Synthetic: #120 changes plus only the C2 blob {path}")
    d = worktree("blob_" + label, rev)
    summary["per_blob"][label] = {"commit": rev, "trusted": gate("trusted", MAIN, MAIN, d, f"perblob_trusted_{label}.txt")}
    print("per-blob", label, summary["per_blob"][label], flush=True)

STEP2 = "Verify trusted-base event and immutable control boundary"
TEST = ('test "$(git rev-parse "${AUTHORITY_BASE_REVISION}:research/000b2-public/verify_attempt_002_invalidation.py")" = \\\n'
        '     "$(git rev-parse "${EXACT_REVISION}:research/000b2-public/verify_attempt_002_invalidation.py")"')
trusted_patches = [
    f'{STEP2}::raise SystemExit(f"TRUSTED_PR_GATE=FAIL: immutable execution control changed: {{path}}")::print(f"TRUSTED_PR_GATE_NEUTRALIZED=immutable execution control changed: {{path}}")',
    f'{STEP2}::raise SystemExit(f"TRUSTED_PR_GATE=FAIL: {{active}} candidate path scope violation")::print(f"TRUSTED_PR_GATE_NEUTRALIZED={{active}} candidate path scope violation")',
    f'{STEP2}::raise SystemExit("TRUSTED_PR_GATE=FAIL: common verifier is not exact authority-base bytes")::print("TRUSTED_PR_GATE_NEUTRALIZED=common verifier is not exact authority-base bytes")',
    f'Verify candidate with exact authority-base common verifier bytes::{TEST}::echo TRUSTED_PR_GATE_NEUTRALIZED=common verifier byte-equality test',
    f'Verify pinned runtime contract with trusted common verifier::{TEST}::echo TRUSTED_PR_GATE_NEUTRALIZED=common verifier byte-equality test',
]
recovery_patches = [
    'Trusted pre-candidate execution boundary::raise SystemExit(f"TRUSTED_BOUNDARY=FAIL: {active} task-candidate path scope violation")::print(f"TRUSTED_BOUNDARY_NEUTRALIZED={active} task-candidate path scope violation")',
]
d = worktree("c2_neutralized", C2)
v = d / VER
s = v.read_text(encoding="utf-8")
old = "    if delta != 0:\n        return\n    if not changed_paths:\n"
assert s.count(old) == 1
v.write_text(s.replace(old, "    if delta != 0:\n        return\n    return  # XVII.5(b) neutralization: not a task candidate\n    if not changed_paths:\n"), encoding="utf-8", newline="\n")
diff = subprocess.run(["git", "-C", str(d), "diff"], capture_output=True, text=True).stdout
(OUT / "neutralization_verifier.diff").write_text(diff, encoding="utf-8", newline="\n")
args_t = [x for p in trusted_patches for x in ("--patch", p)]
args_r = [x for p in recovery_patches for x in ("--patch", p)]
summary["neutralized"] = {"trusted": gate("trusted", MAIN, MAIN, d, "neutralized_trusted_c2.txt", args_t),
                          "recovery": gate("recovery", MAIN, MAIN, d, "neutralized_recovery_c2.txt", args_r)}
print("neutralized", summary["neutralized"], flush=True)
subprocess.run(["git", "-C", str(d), "checkout", "--", VER], check=True)
(OUT / "summary_neutral.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
print("C2_NEUTRAL_DONE")
