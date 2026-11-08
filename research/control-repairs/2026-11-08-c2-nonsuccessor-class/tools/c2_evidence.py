"""C2 evidence driver: build reproducible synthetic candidates and run both B2 gates step by step.

Usage: python -I c2_evidence.py <repo> <main> <c2> <outdir>
Phase post: gate definitions and authority base = C2 commit (the state after C2 merges).
Phase pre:  gate definitions and authority base = main (C2's own pull request).
"""
import json
import os
import pathlib
import subprocess
import sys

REPO, MAIN, C2, OUT = sys.argv[1], sys.argv[2], sys.argv[3], pathlib.Path(sys.argv[4])
H = pathlib.Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
TP = ".github/workflows/000b2-public-attempt-003-trusted-pr.yml"
RC = ".github/workflows/000b2-public-attempt-003-recovery.yml"
VER = "research/000b2-public/verify_attempt_002_invalidation.py"
CS = "docs/canonical/CURRENT_STATE.md"
CUR = "specs/CURRENT.md"
PR120 = "85fe810267eda7ce1be8b76fd4cd769d3a39003d"
EDACDF = "edacdf7504302cc91ff7138bc6ac2d391e4df1f4"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "Synthetic fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
       "GIT_COMMITTER_NAME": "Synthetic fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
       "GIT_AUTHOR_DATE": "2026-11-08T00:00:00Z", "GIT_COMMITTER_DATE": "2026-11-08T00:00:00Z"}


def git(*a, data=None, env=None):
    return subprocess.run(["git", "-C", REPO, *a], input=data, env=env or ENV, check=True, capture_output=True).stdout


def show(rev, path):
    return git("show", f"{rev}:{path}").decode("utf-8")


def commit(base, files, msg, delete=()):
    """files: {path: text|bytes}; returns a commit on top of base."""
    idx = str(H / "c2_idx")
    env = {**ENV, "GIT_INDEX_FILE": idx}
    git("read-tree", base, env=env)
    for path, content in files.items():
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        blob = git("hash-object", "-w", "--stdin", data=data, env=env).decode().strip()
        git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
    for path in delete:
        git("update-index", "--force-remove", "--", path, env=env)
    tree = git("write-tree", env=env).decode().strip()
    os.remove(idx)
    return git("commit-tree", tree, "-p", base, "-m", msg).decode().strip()


def overlay(base, src, paths, msg):
    return commit(base, {p: git("show", f"{src}:{p}") for p in paths}, msg)


def edit_section(text, heading, extra):
    i = text.index(heading + "\n")
    j = text.find("\n## ", i + len(heading))
    j = len(text) if j < 0 else j + 1
    return text[:j] + extra + text[j:] if text[j - 1:j] == "\n" else text[:j] + "\n" + extra + text[j:]


def append(text, block):
    return text.rstrip("\n") + "\n\n" + block


P120_PATHS = git("diff", "--name-only", EDACDF, PR120).decode().split()


def candidates(base):
    cs, cur = show(base, CS), show(base, CUR)
    ok_cs = append(edit_section(cs, "## Current product thesis", "Platform thesis pending G2 (synthetic non-successor edit).\n\n"),
                   "## Platform frontier\n\nSynthetic appended frontier section.\n")
    ok_cur = edit_section(cur, "## Remaining founding children", "Synthetic non-successor note.\n\n")
    c = {}
    c["ns_ok"] = commit(base, {CS: ok_cs, CUR: ok_cur}, "Synthetic: non-successor frontier edit")
    c["neg_b2_path"] = commit(base, {CS: ok_cs, "research/000b2-public/synthetic-note.md": "x\n"}, "Synthetic: B2 path")
    c["neg_github_path"] = commit(base, {CS: ok_cs, ".github/synthetic.txt": "x\n"}, "Synthetic: .github path")
    rd = "research/000b2-public/recovery-attempt-003-readiness.json"
    c["neg_readiness"] = commit(base, {CS: ok_cs, rd: show(base, rd) + "\n"}, "Synthetic: readiness byte change")
    c["neg_outside_allowlist"] = commit(base, {CS: edit_section(cs, "## What is established", "Synthetic edit.\n\n")}, "Synthetic: edit outside allowlist")
    a, b = cs.index("## Current product thesis\n"), cs.index("## Current architecture posture\n")
    e = cs.index("## Explicit non-claims\n")
    c["neg_reordered"] = commit(base, {CS: cs[:a] + cs[b:e] + cs[a:b] + cs[e:]}, "Synthetic: reordered allowlisted sections")
    c["neg_duplicate_heading"] = commit(base, {CS: append(cs, "## Product-code gate\n\nDuplicate.\n")}, "Synthetic: duplicate heading")
    c["neg_confusable_heading"] = commit(base, {CS: append(cs, "## Platform frontier\n\nok\n\n## product-code  GATE\n\nconfusable\n")}, "Synthetic: confusable heading")
    c["neg_marker_in_allowlisted"] = commit(base, {CS: edit_section(cs, "## Explicit non-claims", "product_code_authorized: true\n\n")}, "Synthetic: marker in allowlisted section")
    c["neg_marker_in_appended"] = commit(base, {CS: append(cs, "## Platform frontier\n\n**ATTEMPT-003 frozen:** `false`\n")}, "Synthetic: marker in appended section")
    c["neg_preamble"] = commit(base, {CS: cs.replace("\n", "\nSynthetic preamble line.\n", 1)}, "Synthetic: preamble change")
    c["neg_c1_checker"] = commit(base, {"research/000b2-public/verify_b2r16_preservation.py": show(base, "research/000b2-public/verify_b2r16_preservation.py") + "# synthetic\n"}, "Synthetic: change C1 checker")
    c["task_pr120"] = overlay(base, PR120, P120_PATHS, "Synthetic: #120 changes overlaid")
    c["neg_task_extra_path"] = commit(c["task_pr120"], {"research/000b2-public/b2r17-extra.json": "{}\n"}, "Synthetic: #120 plus extra path")
    return c


def worktree(name, rev):
    d = H / "c2wt" / name
    subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force", str(d)], capture_output=True)
    subprocess.run(["git", "-C", REPO, "worktree", "add", "-q", "--detach", str(d), rev], check=True, capture_output=True)
    return d


def gate(kind, ref, base, cand_dir, out, extra=()):
    gh = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(cand_dir), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    common = ["--repo", REPO, "--ref", ref, "--workdir", str(cand_dir), "--env", f"EXACT_REVISION={head}", "--env", f"AUTHORITY_BASE_REVISION={base}",
              "--env", f"RUNNER_TEMP={H / 'rt'}"]
    if kind == "trusted":
        args = ["--workflow", TP, "--job", "verify-successor-pr-from-canonical-base", "--env", "GITHUB_EVENT_NAME=pull_request_target"]
    else:
        args = ["--workflow", RC, "--job", "verify-successor-recovery", "--env", "GITHUB_EVENT_NAME=pull_request",
                "--env", "GITHUB_REPOSITORY=TheHalfMoon/Wispral", "--env", f"GH_TOKEN={gh}"]
    r = subprocess.run([sys.executable, "-I", str(H / "run_gate_steps.py"), *common, *args, *extra], capture_output=True, text=True)
    text = (r.stdout + r.stderr).replace(str(H).replace("\\", "/"), "<local>").replace(str(H), "<local>")
    (OUT / out).write_text(text, encoding="utf-8", newline="\n")
    steps = [line for line in text.splitlines() if line.startswith("## STEP") and ": exit" in line]
    return " ".join(s.split(" ")[2] + ":" + s.rsplit(" ", 1)[1] for s in steps)


summary = {"main": MAIN, "c2": C2, "post": {}, "pre": {}}
phase = sys.argv[5] if len(sys.argv) > 5 else "all"
if phase in ("all", "post"):
    cands = candidates(C2)
    summary["post_candidates"] = cands
    for name, rev in cands.items():
        d = worktree(name, rev)
        summary["post"][name] = {"trusted": gate("trusted", C2, C2, d, f"post_trusted_{name}.txt"),
                                 "recovery": gate("recovery", C2, C2, d, f"post_recovery_{name}.txt")}
        print("post", name, summary["post"][name], flush=True)
    d = worktree("canonical_c2", C2)
    summary["post"]["canonical_self_check"] = {"recovery": gate("recovery", C2, C2, d, "post_recovery_canonical_self_check.txt")}
    print("post canonical", summary["post"]["canonical_self_check"], flush=True)
if phase in ("all", "pre"):
    host = overlay(MAIN, PR120, P120_PATHS, "Synthetic: #120 changes overlaid on main")
    host_c2 = overlay(host, C2, [TP, RC, VER], "Synthetic: #120 changes plus exactly the C2 blobs")
    summary["pre_candidates"] = {"c2": C2, "base": MAIN, "pr120": host, "pr120c2": host_c2}
    for name, rev in summary["pre_candidates"].items():
        d = worktree("pre_" + name, rev)
        summary["pre"][name] = {"trusted": gate("trusted", MAIN, MAIN, d, f"pre_trusted_{name}.txt"),
                                "recovery": gate("recovery", MAIN, MAIN, d, f"pre_recovery_{name}.txt")}
        print("pre", name, summary["pre"][name], flush=True)
(OUT / f"summary_{phase}.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
print("C2_EVIDENCE_DONE")
