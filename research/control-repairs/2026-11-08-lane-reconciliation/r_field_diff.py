"""Principle XVII item 10: deterministic field diff for the B2R16/ATTEMPT-003 lane reconciliation.

Proves the reconciliation changes only records. Every authority, freeze, decode, scoring,
readiness, task-scope or completion field is byte-identical between the pre-correction
base, the pre-reconciliation base and the reconciliation head. The changed path set of the
reconciliation itself must be record paths only.

Usage: python -I r_field_diff.py <pre_correction_base> <pre_reconciliation_base> <head>
"""
import json
import subprocess
import sys

PRE, BASE, HEAD = sys.argv[1:4]

# Paths that carry B2 authority, freeze, decode, scoring, readiness, task-scope or completion state.
AUTHORITY_PATHS = (
    "docs/canonical/CURRENT_STATE.md",
    "specs/CURRENT.md",
    "research/000b2-public/recovery-attempt-003-readiness.json",
    "research/000b2-public/b2r16-preexecution-state.json",
    "research/000b2-public/b2r16-attempt-003-manifest.json",
    "research/000b1/frozen-methodology.json",
)
AUTHORITY_TREES = (
    "specs/000B2-public-corpus-bakeoff",
    "research/000b2-entry",
    "research/000b1",
)
READINESS = "research/000b2-public/recovery-attempt-003-readiness.json"
RECORD_PATHS = ("docs/canonical/TRUSTED_CONTROL_REPAIRS.md", "AGENTS.md")
RECORD_PREFIX = "research/control-repairs/2026-11-08-lane-reconciliation/"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def blob(rev, path):
    r = subprocess.run(["git", "rev-parse", f"{rev}:{path}"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "<absent>"


failures = []
print(f"PRE_CORRECTION_BASE={git('rev-parse', PRE)}")
print(f"PRE_RECONCILIATION_BASE={git('rev-parse', BASE)}")
print(f"RECONCILIATION_HEAD={git('rev-parse', HEAD)}")
for path in AUTHORITY_PATHS + AUTHORITY_TREES:
    ids = [blob(rev, path) for rev in (PRE, BASE, HEAD)]
    same = len(set(ids)) == 1 and ids[0] != "<absent>"
    print(f"{'SAME' if same else 'DIFF'} {path} {ids[0]}" + ("" if same else f" -> {ids[1]} -> {ids[2]}"))
    if not same:
        failures.append(path)

readiness = [json.loads(git("show", f"{rev}:{READINESS}")) for rev in (PRE, BASE, HEAD)]
for key in sorted(set().union(*readiness)):
    vals = [json.dumps(r.get(key), sort_keys=True) for r in readiness]
    if len(set(vals)) != 1:
        failures.append(f"readiness field {key}")
print(f"READINESS_FIELDS_COMPARED={len(set().union(*readiness))}")

changed = [p for p in git("diff", "--name-only", "--no-renames", BASE, HEAD).splitlines() if p]
for path in changed:
    ok = path in RECORD_PATHS or path.startswith(RECORD_PREFIX)
    print(f"{'RECORD' if ok else 'NOT_RECORD'} {path}")
    if not ok:
        failures.append(f"non-record path {path}")
if "AGENTS.md" in changed:
    diff = git("diff", "--unified=0", BASE, HEAD, "--", "AGENTS.md").splitlines()
    body = [l for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    if len(body) != 2 or "TRUSTED_CONTROL_REPAIRS.md" not in body[0] or "TRUSTED_CONTROL_REPAIRS.md" not in body[1]:
        failures.append("AGENTS.md change is not the single reading-order line")
ledger_old = git("show", f"{BASE}:docs/canonical/TRUSTED_CONTROL_REPAIRS.md")
ledger_new = git("show", f"{HEAD}:docs/canonical/TRUSTED_CONTROL_REPAIRS.md")
if not ledger_new.startswith(ledger_old):
    failures.append("ledger is not append-only")
print("LEDGER_APPEND_ONLY=" + ("PASS" if ledger_new.startswith(ledger_old) else "FAIL"))

for f in failures:
    print(f"FAILURE {f}")
print("RECORDS_ONLY_FIELD_DIFF=" + ("PASS" if not failures else "FAIL"))
sys.exit(1 if failures else 0)
