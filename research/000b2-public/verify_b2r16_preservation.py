#!/usr/bin/env python3
"""Preserve the historical B2R16 proof and reject changed frozen Git objects.

Constitution Principle XVII correction C1 (absorbs #126), not Principle XVI
authority. The original verifier and evidence stay unchanged.

- A candidate that does not contain the freeze merge belongs to the original
  B2R16 candidate class. It is judged by the frozen original verifier bytes, as
  the original control judged it; the candidate's own verifier never runs.
- A later candidate must keep every frozen object. Only the workflow has an
  explicit two-identity migration: the original (on a branch whose fork point
  predates the replacement) or this reviewed, base-defined replacement.

Candidate files are read only as data; candidate code is never executed.
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
VERIFIER = "research/000b2-public/verify_b2r16.py"
MAX_WORKFLOW_BYTES = 65536
# Filled from the exact reviewed replacement workflow, not candidate input.
REPLACEMENT_WORKFLOW_TEMPLATE_SHA256 = "0befa88c6558d6b4835c3cefcdc5353a337075dcdb54fdcbd75fe9412579b9f2"
FROZEN_PATHS = (
    WORKFLOW,
    VERIFIER,
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
    try:
        metadata, name = record[:-1].split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split()
        decoded = name.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise PreservationError(f"Malformed tree record: {file}") from exc
    if decoded != file or kind != "blob" or mode != "100644":
        raise PreservationError(f"Frozen path type/mode drift: {file}")
    return mode, blob


def require_commit(root: Path, candidate: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
        raise PreservationError("Candidate must be an exact full commit SHA")
    git(root, "cat-file", "-e", candidate + "^{commit}")


def descends_from_freeze(root: Path, candidate: str) -> bool:
    try:
        result = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", FROZEN_MERGE, candidate],
                                capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreservationError("Git object verification failed: merge-base") from exc
    if result.returncode not in (0, 1):
        raise PreservationError("Git object verification failed: merge-base")
    return result.returncode == 0


def verify_candidate(root: Path, candidate: str) -> list[dict[str, str]]:
    require_commit(root, candidate)
    if not descends_from_freeze(root, candidate):
        raise PreservationError("Candidate predates the B2R16 freeze merge")
    records = []
    for file in FROZEN_PATHS:
        _, expected = identity(root, FROZEN_MERGE, file)
        _, actual = identity(root, candidate, file)
        if actual != expected:
            # One exact, declared control migration; never an arbitrary waiver.
            if file != WORKFLOW or not approved_workflow(workflow_bytes(root, actual)):
                raise PreservationError(f"Frozen bytes changed: {file}")
        elif file == WORKFLOW and restores_original(root, candidate, expected):
            raise PreservationError(f"Frozen workflow downgraded to the original identity: {file}")
        records.append({"path": file, "historical_blob": expected, "candidate_blob": actual})
    return records


def workflow_bytes(root: Path, blob: str) -> bytes:
    try:
        size = int(git(root, "cat-file", "-s", blob))
    except ValueError as exc:
        raise PreservationError("Workflow blob size unreadable") from exc
    if size > MAX_WORKFLOW_BYTES:
        raise PreservationError("Workflow blob exceeds the size limit")
    return git(root, "cat-file", "blob", blob)


def restores_original(root: Path, candidate: str, original: str) -> bool:
    # The original workflow is accepted only on a branch whose fork point with the
    # trusted revision still has it. Restoring it after the replacement is in the
    # candidate's history is a downgrade of the base-defined trust root.
    bases = git(root, "merge-base", "--all", "HEAD", candidate).decode("ascii").split()
    if not bases:
        raise PreservationError("No merge base with the trusted revision")
    return any(identity(root, base, WORKFLOW)[1] != original for base in bases)


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


def run_original(root: Path, revision: str) -> subprocess.CompletedProcess:
    # Judge an exact revision with the frozen original verifier bytes, in a fresh
    # scratch clone. The revision's own verifier must be a regular file in real
    # directories and is replaced by the frozen bytes; its other files are data.
    require_commit(root, revision)
    _, frozen_blob = identity(root, FROZEN_MERGE, VERIFIER)
    identity(root, revision, VERIFIER)
    frozen = git(root, "cat-file", "blob", frozen_blob)
    scratch = Path(tempfile.mkdtemp(prefix=".b2r16-proof-", dir=root.parent)).resolve()
    if scratch.parent != root.parent.resolve():
        raise PreservationError("Unexpected historical proof scratch root")
    try:
        # A partial clone's alternates may omit promised historical blobs.
        # Materialize the pinned tree in the source promisor before local clone.
        subprocess.run(["git", "-C", str(root), "archive", "--format=tar", revision],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
        subprocess.run(["git", "clone", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "--shared", "--quiet", "--no-checkout", str(root), str(scratch)],
                       check=True, capture_output=True, timeout=60)
        git(scratch, "checkout", "--quiet", "--detach", revision)
        target = scratch / VERIFIER
        target.write_bytes(frozen)
        return subprocess.run([sys.executable, "-I", str(target), "--require-git"],
                              capture_output=True, text=True, timeout=120)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr or exc.stdout or ""
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", errors="replace")
        raise PreservationError("Original verifier setup failed: " + detail[-2000:]) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreservationError("Original verifier setup failed") from exc
    finally:
        # Delete only the freshly created, identity-checked scratch directory.
        if scratch.parent == root.parent.resolve() and scratch.name.startswith(".b2r16-proof-") and not scratch.is_symlink():
            shutil.rmtree(scratch)


def historical_proof(root: Path) -> str:
    # Candidate code is never used for the historical proof. The exact qualified
    # commit retains its original authority/readiness context and Git history.
    result = run_original(root, QUALIFIED_HEAD)
    if result.returncode != 0:
        raise PreservationError("Pinned historical verifier failed: " + (result.stderr or result.stdout)[-2000:])
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    require_commit(ROOT, args.candidate)
    if not descends_from_freeze(ROOT, args.candidate):
        result = run_original(ROOT, args.candidate)
        print(result.stdout, end="")
        print("B2R16_VERDICT_SOURCE=FROZEN_ORIGINAL_VERIFIER")
        if result.returncode != 0:
            raise PreservationError("original B2R16 verifier rejected the candidate: " + (result.stderr or result.stdout).strip()[-500:])
        if args.output:
            args.output.write_text(json.dumps({"candidate": args.candidate, "source": "FROZEN_ORIGINAL_VERIFIER",
                "stdout": result.stdout, "status": "PASS"}, indent=2) + "\n", encoding="utf-8")
        return 0
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
