"""C2 item 3 evidence: every candidate either B2 scope gate has ever evaluated (all pull-request runs of
both workflows, from the GitHub run history) is classified by C2's nonsuccessor_violations against its
merge base with main. A non-empty result means C2 cannot change that candidate's verdict, because C2
alters the gates' behavior only when the result is empty. Writes a manifest and prints its SHA-256.
Usage: python -I c2_corpus.py <repo> <c2_head> <main> <out_dir>"""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

REPO, C2, MAIN, OUT = sys.argv[1], sys.argv[2], sys.argv[3], pathlib.Path(sys.argv[4])
OUT.mkdir(parents=True, exist_ok=True)
src = subprocess.run(["git", "-C", REPO, "show", f"{C2}:research/000b2-public/verify_attempt_002_invalidation.py"], capture_output=True, check=True).stdout
tmp = OUT / "_c2_verifier.py"
tmp.write_bytes(src)
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("c2v", tmp)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
tmp.unlink()

runs = []
for wf in ("000b2-public-attempt-003-trusted-pr.yml", "000b2-public-attempt-003-recovery.yml"):
    out = subprocess.run(["gh", "run", "list", "-R", "TheHalfMoon/Wispral", "--workflow", wf, "--limit", "300", "--json", "headSha,event,conclusion,databaseId"],
                         capture_output=True, text=True, check=True).stdout
    for r in json.loads(out):
        if r["event"] in ("pull_request", "pull_request_target"):
            runs.append({"workflow": wf, "head": r["headSha"], "conclusion": r["conclusion"], "run": r["databaseId"]})
heads = sorted({r["head"] for r in runs})
rows, changed_verdicts = [], 0
for head in heads:
    if subprocess.run(["git", "-C", REPO, "cat-file", "-e", head + "^{commit}"], capture_output=True).returncode != 0:
        subprocess.run(["git", "-C", REPO, "fetch", "-q", "origin", head], capture_output=True)
    if subprocess.run(["git", "-C", REPO, "cat-file", "-e", head + "^{commit}"], capture_output=True).returncode != 0:
        rows.append({"head": head, "status": "UNAVAILABLE"})
        continue
    base = subprocess.run(["git", "-C", REPO, "merge-base", head, MAIN], capture_output=True, text=True).stdout.strip()
    changed = sorted(p for p in subprocess.run(["git", "-C", REPO, "diff", "--name-only", "--diff-filter=ACDMRTUXB", base, head],
                                               capture_output=True, text=True).stdout.splitlines() if p)
    violations = v.nonsuccessor_violations(base, head, changed, pathlib.Path(REPO))
    conclusions = sorted({f"{r['workflow'].split('-')[-1].split('.')[0]}:{r['conclusion']}" for r in runs if r["head"] == head})
    if not violations:
        changed_verdicts += 1
    rows.append({"head": head, "merge_base": base, "changed_paths": len(changed), "historical": conclusions,
                 "nonsuccessor": not violations, "first_violation": violations[0] if violations else None})
manifest = {"c2_head": C2, "main": MAIN, "candidates": rows,
            "rule": "C2 changes a verdict only when nonsuccessor_violations(...) is empty; every candidate below with nonsuccessor=false keeps its pre-C2 verdict."}
data = (json.dumps(manifest, indent=1) + "\n").encode("utf-8")
(OUT / "c2_in_class_corpus_manifest.json").write_bytes(data)
print(f"candidates={len(heads)} unavailable={sum(1 for r in rows if r.get('status') == 'UNAVAILABLE')} classified_nonsuccessor={changed_verdicts}")
print("manifest sha256", hashlib.sha256(data).hexdigest())
