"""CORE-00 pin verifier (pattern of research/reviews/2026-10-21-opus-pr124/verify_transplant_pins.py).

For every anchor in anchors.json it:

- resolves the pinned commit;
- fetches the stored git blob for the path at that commit;
- computes the git blob id and SHA-256;
- checks that the bytes hash to the tree's blob id for that path;
- checks any recorded expectation (a SHA-256 or blob prefix, or a required substring).

It also reads each repository's declared licence at the pinned commit. Reads only; needs an
authenticated `gh` for private founder repositories.

Usage: python -I verify_core00_anchors.py anchors.json > runs/verify_core00_anchors.txt
Exit status 0 only if every anchor passes.
"""
import base64
import hashlib
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")


def gh(*args, raw=False):
    cmd = ["gh", "api", *args]
    if raw:
        cmd[2:2] = ["-H", "Accept: application/vnd.github.raw"]
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout if r.returncode == 0 else None


anchors = json.load(open(sys.argv[1], encoding="utf-8"))["anchors"]
failures = 0
licences = {}
for a in anchors:
    repo, sha, path = a["repo"], a["sha"], a["path"]
    commit = gh(f"repos/{repo}/commits/{sha}", "--jq", ".sha")
    commit = commit.decode().strip() if commit else None
    # The tree's blob id for the path at the pin, then the stored blob bytes themselves. The
    # contents endpoint can serve bytes that differ from the stored blob (observed for one file),
    # so the git blob is the authority.
    meta = gh(f"repos/{repo}/contents/{path}?ref={sha}", "--jq", ".sha")
    tree_blob = meta.decode().strip() if meta else None
    b64 = gh(f"repos/{repo}/git/blobs/{tree_blob}", "--jq", ".content") if tree_blob else None
    data = base64.b64decode(b64) if b64 else None
    problems = []
    if commit != sha:
        problems.append(f"commit {commit} != pin")
    if data is None:
        problems.append("fetch failed")
        blob = sha256 = "-"
    else:
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()
        if blob != tree_blob:
            problems.append("blob bytes do not hash to the tree's blob id")
        exp = a.get("expect", {})
        if "sha256" in exp and not sha256.startswith(exp["sha256"]):
            problems.append(f"sha256 != recorded {exp['sha256']}")
        if "git_blob" in exp and not blob.startswith(exp["git_blob"]):
            problems.append(f"blob != recorded {exp['git_blob']}")
        if "contains" in exp and exp["contains"].encode() not in data:
            problems.append(f"missing '{exp['contains']}'")
    if (repo, sha) not in licences:
        spdx = gh(f"repos/{repo}/license?ref={sha}", "--jq", ".license.spdx_id")
        licences[(repo, sha)] = spdx.decode().strip() if spdx else "NONE_DETECTED"
    status = "PASS" if not problems else "FAIL: " + "; ".join(problems)
    failures += bool(problems)
    print(f"{a['id']} | {repo}@{sha[:12]} | {path} | blob {blob} | sha256 {sha256} | {status}")
print()
for (repo, sha), spdx in sorted(licences.items()):
    print(f"LICENCE | {repo}@{sha[:12]} | {spdx}")
print()
print(f"ANCHORS={len(anchors)} PASS={len(anchors) - failures} FAIL={failures}")
print("CORE00_ANCHORS=" + ("PASS" if failures == 0 else "FAIL"))
sys.exit(1 if failures else 0)
