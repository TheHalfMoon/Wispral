#!/usr/bin/env python3
"""Trusted-base verifier for 000B2 artifact identity.

This verifier executes from canonical base authority and treats the pull-request
checkout strictly as untrusted data. It proves only cryptographic artifact identity:
that the candidate preserves the canonical B1 registry, applies the narrowly bounded
sherpa ``tokens.txt`` size correction facts, and records SHA-256 values that reproduce
from approved pinned sources under strict byte and redirect bounds.

It intentionally does NOT attest chronology, primary-decoding state, comparative-
ranking state, consent, corpus authority, or any other process claim authored by the
candidate checkout. Those remain separate canonical/review gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REGISTRY_REL = Path("research/000b1/qualified-candidates.json")
AMENDMENT_REL = Path("research/000b2-entry/artifact-size-amendment.json")
EVIDENCE_REL = Path("research/000b2-entry/materialized-artifacts.json")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_CORRECTIONS = {
    ("sherpa-onnx-compact", "tokens.txt"),
    ("sherpa-onnx-balanced", "tokens.txt"),
}
EXPECTED_PENDING_COUNT = 18
MAX_ARTIFACT_BYTES = 536_870_912
SHERPA_SOURCE_REVISION = "6037ea07e3abfe599ad00d418968bcf9656e7472"
TRUSTED_REDIRECT_HOSTS = {
    "moonshine": {
        "download.moonshine.ai",
        "storage.googleapis.com",
    },
    "huggingface": {
        "huggingface.co",
        ".huggingface.co",
        "hf.co",
        ".hf.co",
    },
}


class VerificationError(RuntimeError):
    """Fail-closed trusted artifact-identity verification error."""


def safe_bytes(root: Path, relative: Path) -> bytes:
    root = root.resolve(strict=True)
    path = root / relative
    if path.is_symlink():
        raise VerificationError(f"symlink is forbidden for authority input: {relative}")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise VerificationError(f"authority input escapes checkout root: {relative}")
    if not resolved.is_file():
        raise VerificationError(f"authority input is not a regular file: {relative}")
    return resolved.read_bytes()


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"{label} must be a JSON object")
    return value


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def correction_map(
    amendment: dict[str, Any], registry: dict[str, Any]
) -> dict[tuple[str, str], dict[str, Any]]:
    """Validate correction facts only; do not infer chronology from candidate labels."""
    if amendment.get("schema_version") != "000b2-entry-artifact-amendment-v1":
        raise VerificationError("amendment schema drift")

    rows = amendment.get("corrections")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_CORRECTIONS):
        raise VerificationError("amendment correction cardinality drift")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise VerificationError("amendment correction must be an object")
        key = (row.get("candidate_id"), row.get("path"))
        if key in result:
            raise VerificationError(f"duplicate amendment correction: {key}")
        result[key] = row
    if set(result) != EXPECTED_CORRECTIONS:
        raise VerificationError("amendment correction scope drift")

    registry_artifacts: dict[tuple[str, str], dict[str, Any]] = {}
    for family in registry.get("families", []):
        if not isinstance(family, dict):
            raise VerificationError("registry family must be an object")
        for config in family.get("configurations", []):
            if not isinstance(config, dict):
                raise VerificationError("registry configuration must be an object")
            candidate_id = config.get("id")
            for artifact in config.get("artifacts", []):
                if isinstance(artifact, dict):
                    registry_artifacts[(candidate_id, artifact.get("path"))] = artifact

    for key, row in result.items():
        artifact = registry_artifacts.get(key)
        if artifact is None or artifact.get("sha256") is not None:
            raise VerificationError(f"amendment target is not a B1-pending artifact: {key}")
        if (
            row.get("historical_b1_size_bytes") != artifact.get("size_bytes")
            or artifact.get("size_bytes") != 5050
        ):
            raise VerificationError(f"historical B1 size mismatch for {key}")
        if row.get("b2_entry_size_bytes") != 5048:
            raise VerificationError(f"B2 corrected size drift for {key}")
        if (
            row.get("source_revision") != artifact.get("source_revision")
            or row.get("source_revision") != SHERPA_SOURCE_REVISION
        ):
            raise VerificationError(f"source revision drift for {key}")
    return result


def expected_pending(
    registry: dict[str, Any], corrections: dict[tuple[str, str], dict[str, Any]]
) -> dict[tuple[str, str], dict[str, Any]]:
    expected: dict[tuple[str, str], dict[str, Any]] = {}
    for family in registry.get("families", []):
        family_name = family.get("family")
        configurations = family.get("configurations")
        if not isinstance(configurations, list):
            raise VerificationError(f"registry configurations missing for {family_name}")
        for config in configurations:
            if not isinstance(config, dict):
                raise VerificationError("registry configuration must be an object")
            candidate_id = config.get("id")
            artifacts = config.get("artifacts")
            if not isinstance(candidate_id, str) or not isinstance(artifacts, list):
                raise VerificationError("registry candidate identity/artifacts malformed")
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    raise VerificationError(f"registry artifact malformed for {candidate_id}")
                if artifact.get("sha256") is not None:
                    continue
                path = artifact.get("path")
                if not isinstance(path, str) or not path:
                    raise VerificationError(f"pending artifact path malformed for {candidate_id}")
                key = (candidate_id, path)
                if key in expected:
                    raise VerificationError(f"duplicate pending artifact: {key}")
                original_size = artifact.get("size_bytes")
                if not isinstance(original_size, int) or original_size <= 0:
                    raise VerificationError(f"pending artifact size malformed for {key}")
                correction = corrections.get(key)
                size = correction["b2_entry_size_bytes"] if correction else original_size
                source_revision = artifact.get("source_revision")
                if family_name == "moonshine":
                    base_url = config.get("artifact_base_url")
                    if not isinstance(base_url, str) or not base_url.startswith(
                        "https://download.moonshine.ai/"
                    ):
                        raise VerificationError(f"Moonshine base URL drift for {candidate_id}")
                    source_url = f"{base_url.rstrip('/')}/{path}"
                    source_group = "moonshine"
                elif family_name == "sherpa-onnx":
                    model_source = family.get("model_source")
                    if not isinstance(model_source, dict):
                        raise VerificationError("sherpa model source missing")
                    base_url = model_source.get("base_url")
                    if not isinstance(base_url, str) or not base_url.startswith(
                        "https://huggingface.co/"
                    ):
                        raise VerificationError("sherpa base URL drift")
                    if not isinstance(source_revision, str) or not source_revision:
                        raise VerificationError(f"sherpa source revision missing for {key}")
                    source_url = f"{base_url.rstrip('/')}/{source_revision}/{path}"
                    source_group = "huggingface"
                else:
                    raise VerificationError(
                        f"unexpected family with pending SHA-256: {family_name}"
                    )
                expected[key] = {
                    "size_bytes": size,
                    "source_revision": source_revision,
                    "source_url": source_url,
                    "source_group": source_group,
                }

    if len(expected) != EXPECTED_PENDING_COUNT:
        raise VerificationError(
            f"expected {EXPECTED_PENDING_COUNT} B1-pending artifacts, got {len(expected)}"
        )
    if set(corrections) - set(expected):
        raise VerificationError("amendment contains a non-pending artifact")
    return expected


def flatten_evidence(evidence: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, dict):
        raise VerificationError("materialized evidence artifact mapping missing")
    flattened: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate_id, paths in artifacts.items():
        if not isinstance(candidate_id, str) or not isinstance(paths, dict):
            raise VerificationError("materialized candidate mapping malformed")
        for path, row in paths.items():
            if not isinstance(path, str) or not isinstance(row, dict):
                raise VerificationError("materialized artifact row malformed")
            key = (candidate_id, path)
            if key in flattened:
                raise VerificationError(f"duplicate materialized artifact: {key}")
            flattened[key] = row
    return flattened


def host_allowed(host: str, source_group: str) -> bool:
    rules = TRUSTED_REDIRECT_HOSTS[source_group]
    host = host.lower().rstrip(".")
    for rule in rules:
        if rule.startswith("."):
            if host.endswith(rule) and host != rule[1:]:
                return True
        elif host == rule:
            return True
    return False


def validate_remote_url(url: str, source_group: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname
    if parsed.scheme != "https" or not host or not host_allowed(host, source_group):
        raise VerificationError(
            f"unapproved {source_group} source/redirect destination: {url}"
        )
    if parsed.username is not None or parsed.password is not None:
        raise VerificationError(f"userinfo is forbidden in source URL: {url}")


class TrustedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, source_group: str):
        super().__init__()
        self.source_group = source_group

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        validate_remote_url(newurl, self.source_group)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_digest(url: str, expected_size: int, source_group: str) -> str:
    if expected_size <= 0 or expected_size > MAX_ARTIFACT_BYTES:
        raise VerificationError(f"download size outside trusted bound: {expected_size}")
    validate_remote_url(url, source_group)
    request = urllib.request.Request(
        url, headers={"User-Agent": "Wispral-trusted-artifact-identity/1"}
    )
    opener = urllib.request.build_opener(TrustedRedirectHandler(source_group))
    digest = hashlib.sha256()
    observed = 0
    try:
        with opener.open(request, timeout=60) as response:
            validate_remote_url(response.geturl(), source_group)
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    declared = int(content_length)
                except ValueError as exc:
                    raise VerificationError(f"invalid Content-Length for {url}") from exc
                if declared > expected_size:
                    raise VerificationError(
                        f"declared payload exceeds expected size for {url}: "
                        f"{declared} > {expected_size}"
                    )
            while True:
                chunk = response.read(min(1024 * 1024, expected_size - observed + 1))
                if not chunk:
                    break
                observed += len(chunk)
                if observed > expected_size:
                    raise VerificationError(f"payload exceeds expected size for {url}")
                digest.update(chunk)
    except VerificationError:
        raise
    except Exception as exc:
        raise VerificationError(f"download failed for {url}: {exc}") from exc
    if observed != expected_size:
        raise VerificationError(
            f"payload size mismatch for {url}: expected {expected_size}, observed {observed}"
        )
    return digest.hexdigest()


def digest_local_bounded(path: Path, expected_size: int) -> str:
    if path.stat().st_size != expected_size:
        raise VerificationError("local self-test size mismatch")
    digest = hashlib.sha256()
    observed = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            observed += len(chunk)
            if observed > expected_size:
                raise VerificationError("local self-test payload exceeded expected size")
            digest.update(chunk)
    if observed != expected_size:
        raise VerificationError("local self-test payload size mismatch")
    return digest.hexdigest()


def verify(base_root: Path, candidate_root: Path) -> None:
    base_registry_raw = safe_bytes(base_root, REGISTRY_REL)
    candidate_registry_raw = safe_bytes(candidate_root, REGISTRY_REL)
    if candidate_registry_raw != base_registry_raw:
        raise VerificationError("candidate changed the frozen canonical B1 registry")
    registry = load_object(base_registry_raw, "canonical B1 registry")

    amendment_raw = safe_bytes(candidate_root, AMENDMENT_REL)
    evidence_raw = safe_bytes(candidate_root, EVIDENCE_REL)
    amendment = load_object(amendment_raw, "B2 artifact-size correction record")
    evidence = load_object(evidence_raw, "B2 materialized artifact record")
    corrections = correction_map(amendment, registry)
    expected = expected_pending(registry, corrections)

    if evidence.get("schema_version") != "000b2-materialized-artifacts-v1":
        raise VerificationError("materialized evidence schema drift")
    if evidence.get("registry_sha256") != sha256_bytes(base_registry_raw):
        raise VerificationError("materialized evidence registry digest drift")
    if evidence.get("amendment_sha256") != sha256_bytes(amendment_raw):
        raise VerificationError("materialized evidence amendment digest drift")

    actual = flatten_evidence(evidence)
    if set(actual) != set(expected):
        raise VerificationError(
            "materialized evidence does not contain the exact canonical pending set"
        )

    for key in sorted(expected):
        wanted = expected[key]
        row = actual[key]
        for field in ("size_bytes", "source_revision", "source_url"):
            if row.get(field) != wanted[field]:
                raise VerificationError(f"materialized evidence {field} drift for {key}")
        committed_sha = row.get("sha256")
        if not isinstance(committed_sha, str) or not SHA256.fullmatch(committed_sha):
            raise VerificationError(f"materialized evidence SHA-256 malformed for {key}")
        live_sha = download_digest(
            wanted["source_url"], wanted["size_bytes"], wanted["source_group"]
        )
        if live_sha != committed_sha:
            raise VerificationError(f"trusted live SHA-256 mismatch for {key}")

    compact_tokens = actual[("sherpa-onnx-compact", "tokens.txt")]["sha256"]
    balanced_tokens = actual[("sherpa-onnx-balanced", "tokens.txt")]["sha256"]
    if (
        compact_tokens
        != "49e3c2646595fd907228b3c6787069658f67b17377c60aeb8619c4551b2316fb"
    ):
        raise VerificationError("trusted sherpa tokens.txt SHA-256 drift")
    if balanced_tokens != compact_tokens:
        raise VerificationError("shared sherpa tokens.txt differs by tier")
    if (
        actual[("moonshine-compact", "tokenizer.bin")]["sha256"]
        != actual[("moonshine-balanced", "tokenizer.bin")]["sha256"]
    ):
        raise VerificationError("shared Moonshine tokenizer differs by tier")


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inside = root / "inside.bin"
        inside.write_bytes(b"abcd")
        expected = hashlib.sha256(b"abcd").hexdigest()
        observed = digest_local_bounded(inside, 4)
        if observed != expected:
            raise VerificationError("self-test digest mismatch")
        try:
            digest_local_bounded(inside, 3)
        except VerificationError:
            pass
        else:
            raise VerificationError("self-test failed to reject size mismatch")

        try:
            load_object(b'{"key": 1, "key": 2}', "duplicate-key self-test")
        except VerificationError:
            pass
        else:
            raise VerificationError("self-test failed to reject duplicate JSON keys")
        nested = load_object(b'{"outer": {"key": 1}}', "nested JSON self-test")
        if nested != {"outer": {"key": 1}}:
            raise VerificationError("self-test strict JSON parse mismatch")

        validate_remote_url(
            "https://huggingface.co/example/model", "huggingface"
        )
        validate_remote_url(
            "https://cas-bridge.xethub.hf.co/example", "huggingface"
        )
        validate_remote_url(
            "https://storage.googleapis.com/example/object", "moonshine"
        )
        for url, source_group in (
            ("https://evil.example/object", "huggingface"),
            ("http://huggingface.co/example", "huggingface"),
            ("https://huggingface.co/example", "moonshine"),
        ):
            try:
                validate_remote_url(url, source_group)
            except VerificationError:
                pass
            else:
                raise VerificationError(
                    f"self-test failed to reject redirect/source URL: {url}"
                )

        safe_root = root / "safe"
        safe_root.mkdir()
        (safe_root / "value.json").write_text("{}\n", encoding="utf-8")
        if safe_bytes(safe_root, Path("value.json")) != b"{}\n":
            raise VerificationError("self-test safe read mismatch")
        outside = root / "outside.json"
        outside.write_text("{}\n", encoding="utf-8")
        symlink = safe_root / "escape.json"
        try:
            symlink.symlink_to(outside)
        except (OSError, NotImplementedError):
            return
        try:
            safe_bytes(safe_root, Path("escape.json"))
        except VerificationError:
            pass
        else:
            raise VerificationError(
                "self-test failed to reject symlink authority input"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-root", type=Path)
    parser.add_argument("--candidate-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            print("TRUSTED_000B2_ARTIFACT_IDENTITY_SELF_TEST=PASS")
            return 0
        if args.base_root is None or args.candidate_root is None:
            parser.error(
                "--base-root and --candidate-root are required unless --self-test is used"
            )
        verify(args.base_root, args.candidate_root)
    except VerificationError as exc:
        print(f"TRUSTED_000B2_ARTIFACT_IDENTITY=FAIL: {exc}")
        return 1
    print("TRUSTED_000B2_ARTIFACT_IDENTITY=PASS")
    print(f"MATERIALIZED_ARTIFACT_RECORDS={EXPECTED_PENDING_COUNT}")
    print("PROCESS_ATTESTATION=NOT_PROVIDED_BY_THIS_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())