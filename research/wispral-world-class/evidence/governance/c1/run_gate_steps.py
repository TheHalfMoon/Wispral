"""Run every `run:` step of one workflow job, as defined at a fixed Git ref, against a candidate checkout.

Successor of run_inline_gate.py for Constitution Principle XVII item 5 evidence. Each step runs
separately under `bash --noprofile --norc -eo pipefail` (the GitHub `shell: bash` contract), so a
failing step does not stop later steps (non-concealment). `uses:` steps are performed by the caller
(the candidate checkout) and are listed, not executed. `--patch STEP::OLD::NEW` replaces one exact
substring in one step for within-step evidence; every patch is printed. Expression-valued env
entries must be supplied with `--env NAME=VALUE`; values are never printed.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import yaml

parser = argparse.ArgumentParser()
parser.add_argument("--repo", required=True)
parser.add_argument("--ref", required=True)
parser.add_argument("--workflow", required=True)
parser.add_argument("--job", required=True)
parser.add_argument("--workdir", required=True)
parser.add_argument("--env", action="append", default=[])
parser.add_argument("--only", action="append", default=[])
parser.add_argument("--patch", action="append", default=[])
parser.add_argument("--tail", type=int, default=12)
args = parser.parse_args()

bash = shutil.which("bash")
source = subprocess.run(["git", "-C", args.repo, "show", f"{args.ref}:{args.workflow}"],
                        capture_output=True, text=True, check=True).stdout
job = yaml.safe_load(source)["jobs"][args.job]
given = dict(item.split("=", 1) for item in args.env)


def resolve(scope, mapping):
    out = {}
    for key, value in (mapping or {}).items():
        if key in given:
            out[key] = given[key]
        elif "${{" in str(value):
            sys.exit(f"{scope}: --env {key}=... is required for expression {value}")
        else:
            out[key] = str(value)
    return out


env = {**os.environ, **resolve("job", job.get("env")), **given}
patches = [item.split("::", 2) for item in args.patch]
used = set()
print(f"## DEFINITION {args.ref}:{args.workflow} job={args.job}")
print(f"## CANDIDATE HEAD {subprocess.run(['git', '-C', args.workdir, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()}")
for index, step in enumerate(job["steps"], 1):
    name = step.get("name", f"step {index}")
    if "run" not in step:
        print(f"## STEP {index} {name}: uses {step.get('uses')} (performed by harness setup)")
        continue
    if args.only and name not in args.only:
        continue
    script = step["run"]
    for target, old, new in patches:
        if target == name:
            count = script.count(old)
            if count != 1:
                sys.exit(f"patch for {name!r} matched {count} times")
            script = script.replace(old, new)
            used.add(target)
            print(f"## PATCH {name}: {old.strip()!r} -> {new.strip()!r}")
    step_env = {**env, **resolve(name, step.get("env"))}
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, newline="\n", encoding="utf-8") as handle:
        handle.write(script)
    try:
        result = subprocess.run([bash, "--noprofile", "--norc", "-eo", "pipefail", handle.name],
                                cwd=args.workdir, env=step_env, capture_output=True, text=True)
    finally:
        os.unlink(handle.name)
    print(f"## STEP {index} {name}: exit {result.returncode}")
    for line in (result.stdout + result.stderr).strip().splitlines()[-args.tail:]:
        print("   " + line)
unused = {target for target, _, _ in patches} - used
if unused:
    sys.exit(f"unused patches: {sorted(unused)}")
