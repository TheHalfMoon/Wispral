"""A3 boundary evidence (Constitution 0.4.0 Principle XVII item 5): every changed line of each annexed
immutable blob lies inside its annexed scope-classification step or function; every other byte is
identical to the authority base. Usage: python -I c2_a3_boundary.py <repo> <base> <head>"""
import ast
import re
import subprocess
import sys

REPO, BASE, HEAD = sys.argv[1:4]
STEP = {".github/workflows/000b2-public-attempt-003-trusted-pr.yml": "Verify trusted-base event and immutable control boundary",
        ".github/workflows/000b2-public-attempt-003-recovery.yml": "Trusted pre-candidate execution boundary"}
VER = "research/000b2-public/verify_attempt_002_invalidation.py"
ANNEXED_FUNCS = {"verify_active_task_candidate_content", "nonsuccessor_violations"}


def show(rev, path):
    return subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path}"], capture_output=True, check=True).stdout.decode("utf-8")


def hunks(path):
    diff = subprocess.run(["git", "-C", REPO, "diff", "-U0", BASE, HEAD, "--", path], capture_output=True, check=True).stdout.decode("utf-8")
    out = []
    for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", diff, re.M):
        a, ac, b, bc = int(m.group(1)), int(m.group(2) or 1), int(m.group(3)), int(m.group(4) or 1)
        out.append(((a, a + max(ac, 1) - 1), (b, b + max(bc, 1) - 1)))
    return out


def step_span(text, name):
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines, 1) if l.strip() == f"- name: {name}")
    end = next((i - 1 for i, l in enumerate(lines, 1) if i > start and l.startswith("      - name: ")), len(lines))
    return start, end


def func_spans(text):
    tree = ast.parse(text)
    return [(n.lineno, n.end_lineno) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ANNEXED_FUNCS]


ok = True
for path, name in STEP.items():
    b0, b1 = step_span(show(BASE, path), name)
    h0, h1 = step_span(show(HEAD, path), name)
    for (a, b) in hunks(path):
        inside = b0 <= a[0] and a[1] <= b1 + 1 and h0 <= b[0] and b[1] <= h1 + 1
        ok &= inside
        print(f"{path}: base {a} head {b} -> {'INSIDE' if inside else 'OUTSIDE'} step '{name}' (base {b0}-{b1}, head {h0}-{h1})")
spans_head = func_spans(show(HEAD, VER))
spans_base = func_spans(show(BASE, VER))
for (a, b) in hunks(VER):
    inside_head = any(s <= b[0] and b[1] <= e + 1 for s, e in spans_head)
    inside_base = any(s <= a[0] + 1 and a[0] <= e + 1 for s, e in spans_base) or a[1] < a[0] + 1
    inside = inside_head
    ok &= inside
    print(f"{VER}: base {a} head {b} -> {'INSIDE' if inside else 'OUTSIDE'} annexed functions {sorted(ANNEXED_FUNCS)} (head spans {spans_head})")
print("A3_BOUNDARY=" + ("PASS" if ok else "FAIL"))
