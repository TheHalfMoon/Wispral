#!/usr/bin/env python3
"""Preserve the historical B2R16 proof and reject changed frozen Git objects.

Ordinary fail-closed applicability correction, not Constitution XVI authority.
The original verifier and evidence stay unchanged. Only the workflow has an
explicit two-identity migration: original or this reviewed replacement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
QUALIFIED_HEAD = "ac9f7ce993aec33e6c6436cce4efd85394a97f35"
FROZEN_MERGE = "885307429ec8b1aa0fe173169a8c2918714c06b0"
WORKFLOW = ".github/workflows/000b2-public-b2r16-freeze.yml"
# Filled from the exact reviewed replacement workflow, not candidate input.
REPLACEMENT_WORKFLOW_TEMPLATE_SHA256 = "39f38a21887ec275b7882285a4e479aa4663f6860a891c66a2329449adce546d"
FROZEN_PATHS = (
    WORKFLOW,
    "research/000b2-public/verify_b2r16.py",
    "research/000b2-public/b2r16-preexecution-state.json",
    "research/000b2-public/b2r16-attempt-003-manifest.json",
    "research/000b2-public/candidate-revalidation.json",
    "research/000b2-public/subset-manifest.json",
    "research/000b1/qualified-candidates.json",
    "research/000b1/frozen-methodology.json",
    "research/000b2-public/b2r15-preprocessing-rebinding.json",
    "research/000b2-public/b2r15-environment-rebinding.json",
    "research/000b2-public/b2r15-provenance.json",
    "research/000b2-public/b2r14-sherpa-result-harness.py",
    "research/000b2-public/b2r14-harness-qualification.json",
    "research/000b2-entry/scorer.py",
    "research/000b2-entry/scorer-config.json",
    "research/000b2-public/score_public_wer.py",
)


class PreservationError(RuntimeError):
    pass


def git(root: Path, *args: str) -> bytes:
    try:
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              capture_output=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreservationError(f"Git object verification failed: {args[0]}") from exc


def identity(root: Path, revision: str, file: str) -> tuple[str, str]:
    record = git(root, "ls-tree", "-z", revision, "--", file)
    if not record or record.count(b"\0") != 1:
        raise PreservationError(f"Missing/ambiguous frozen path: {file}")
    metadata, name = record[:-1].split(b"\t", 1)
    mode, kind, blob = metadata.decode("ascii").split()
    if name.decode("utf-8") != file or kind != "blob" or mode != "100644":
        raise PreservationError(f"Frozen path type/mode drift: {file}")
    return mode, blob


def verify_candidate(root: Path, candidate: str) -> list[dict[str, str]]:
    if re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
        raise PreservationError("Candidate must be an exact full commit SHA")
    git(root, "cat-file", "-e", candidate + "^{commit}")
    git(root, "merge-base", "--is-ancestor", FROZEN_MERGE, candidate)
    records = []
    for file in FROZEN_PATHS:
        _, expected = identity(root, FROZEN_MERGE, file)
        _, actual = identity(root, candidate, file)
        if actual != expected:
            # One exact, declared control migration; never an arbitrary waiver.
            data = git(root, "cat-file", "blob", actual)
            if file != WORKFLOW or not approved_workflow(data):
                raise PreservationError(f"Frozen bytes changed: {file}")
        records.append({"path": file, "historical_blob": expected, "candidate_blob": actual})
    return records


def approved_workflow(data: bytes) -> bool:
    # Break the workflow/checker digest cycle only at its single digest literal.
    # That literal must still equal these exact checker bytes, which the workflow
    # verifies BEFORE executing candidate code. Everything else stays hash-bound.
    matches = list(re.finditer(rb"CHECKER_SHA256: ([0-9a-f]{64})", data))
    if len(matches) != 1:
        return False
    match = matches[0]
    if match.group(1).decode() != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        return False
    normalized = data[:match.start(1)] + b"0" * 64 + data[match.end(1):]
    return hashlib.sha256(normalized).hexdigest() == REPLACEMENT_WORKFLOW_TEMPLATE_SHA256


def historical_proof(root: Path) -> str:
    # Candidate code is never used for the historical proof. The exact qualified
    # commit retains its original authority/readiness context and Git history.
    scratch = Path(tempfile.mkdtemp(prefix=".b2r16-proof-", dir=root.parent)).resolve()
    if scratch.parent != root.parent.resolve():
        raise PreservationError("Unexpected historical proof scratch root")
    try:
        # A partial clone's alternates may omit promised historical blobs.
        # Materialize the pinned tree in the source promisor before local clone.
        subprocess.run(["git", "-C", str(root), "archive", "--format=tar", QUALIFIED_HEAD],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
        subprocess.run(["git", "clone", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "--shared", "--quiet", "--no-checkout", str(root), str(scratch)],
                       check=True, capture_output=True, timeout=60)
        git(scratch, "checkout", "--quiet", "--detach", QUALIFIED_HEAD)
        result = subprocess.run([sys.executable, "-I", str(scratch / "research/000b2-public/verify_b2r16.py"),
                                 "--require-git"], check=True, capture_output=True, text=True, timeout=60)
        return result.stdout
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", errors="replace")
        raise PreservationError("Pinned historical verifier failed: " + detail[-2000:]) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreservationError("Pinned historical verifier failed") from exc
    finally:
        # Delete only the freshly created, identity-checked scratch directory.
        if scratch.parent == root.parent.resolve() and scratch.name.startswith(".b2r16-proof-") and not scratch.is_symlink():
            shutil.rmtree(scratch)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    records = verify_candidate(ROOT, args.candidate)
    historical = historical_proof(ROOT)
    print(historical, end="")
    print("B2R16_FROZEN_OBJECT_PRESERVATION=PASS")
    if args.output:
        args.output.write_text(json.dumps({"candidate": args.candidate, "qualified_head": QUALIFIED_HEAD,
            "historical_stdout": historical, "status": "PASS", "paths": records}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PreservationError, OSError) as exc:
        raise SystemExit(f"B2R16_FROZEN_OBJECT_PRESERVATION=FAIL: {exc}")
