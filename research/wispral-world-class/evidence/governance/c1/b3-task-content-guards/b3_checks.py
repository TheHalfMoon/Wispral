"""B3 evidence: run, separately, the task-content checks of verify_active_task_candidate_content that
the item 5(b) neutralization skipped, on each path a candidate changes relative to the authority base.

Executed from the authority-base verifier bytes (blob-identical in the candidate), with ROOT set to
the candidate checkout. Checks that only make sense for a B2R17 task candidate are reported as
CLASSIFICATION; generic guards are reported PASS or FAIL."""
import importlib.util
import subprocess
import sys
from pathlib import Path

workdir, base = Path(sys.argv[1]).resolve(), sys.argv[2]
rel = "research/000b2-public/verify_attempt_002_invalidation.py"
git = lambda *a: subprocess.run(["git", "-C", str(workdir), *a], capture_output=True, text=True, check=True).stdout.strip()
assert git("rev-parse", f"{base}:{rel}") == git("rev-parse", f"HEAD:{rel}"), "verifier bytes differ from base"
spec = importlib.util.spec_from_file_location("v", workdir / rel)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
assert v.ROOT == workdir, (v.ROOT, workdir)
import ast
import json

active = "B2R17"
policy = v.expected_task_content_policies()[active]
future_tokens = set(v.TASK_ORDER[v.TASK_ORDER.index(active) + 1:])
changed = sorted(p for p in git("diff", "--name-only", "--diff-filter=ACDMRTUXB", base, "HEAD", "--").splitlines() if p)
print(f"CANDIDATE={git('rev-parse', 'HEAD')} BASE={base} ACTIVE={active}")
print(f"CLASSIFICATION required verifier {policy['required_verifier']} in changed paths: {policy['required_verifier'] in changed}")
fails = 0
for path in changed:
    present = subprocess.run(["git", "-C", str(workdir), "cat-file", "-e", f"HEAD:{path}"], capture_output=True).returncode == 0
    print(f"--- {path}")
    print(f"  {'PASS' if present else 'FAIL'} not deleted"); fails += not present
    if not present:
        continue
    text = git("show", f"HEAD:{path}")
    tokens = {t.upper() for t in v.SUCCESSOR_TOKEN_RE.findall(text)}
    print(f"  CLASSIFICATION active-task binding token {active} present: {active in tokens}")
    future = sorted(tokens & future_tokens)
    print(f"  {'PASS' if not future else 'FAIL'} no future successor tokens {future}"); fails += bool(future)
    published = [a for a, pattern in v.POSITIVE_AUTHORITY_PATTERNS.items() if pattern.search(text)]
    print(f"  {'PASS' if not published else 'FAIL'} no positive authority publication {published}"); fails += bool(published)
    if path.endswith(".json"):
        doc = json.loads(text)
        print(f"  CLASSIFICATION JSON task binding == {active}: {isinstance(doc, dict) and doc.get('task') == active}")
    if path.endswith(".py"):
        calls = {v.call_name(n.func) for n in ast.walk(ast.parse(text, filename=path)) if isinstance(n, ast.Call)}
        decode = sorted(calls & v.DECODE_CALL_NAMES) if not policy["primary_decode_allowed"] else []
        scoring = sorted(calls & v.SCORING_CALL_NAMES) if not policy["scoring_allowed"] else []
        print(f"  {'PASS' if not decode else 'FAIL'} no forbidden decode-runtime calls {decode} (policy primary_decode_allowed={policy['primary_decode_allowed']})"); fails += bool(decode)
        print(f"  {'PASS' if not scoring else 'FAIL'} no forbidden scoring calls {scoring} (policy scoring_allowed={policy['scoring_allowed']})"); fails += bool(scoring)
print(f"B3_GENERIC_TASK_CONTENT_GUARDS={'PASS' if fails == 0 else 'FAIL'} failures={fails}")
