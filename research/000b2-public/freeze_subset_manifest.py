#!/usr/bin/env python3
"""Materialize exact public archives and freeze the B2P04 source-membership manifest."""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import shutil
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

import materialize_archives
import select_subset

ROOT = Path(__file__).resolve().parents[2]
CORPUS_SOURCE_PATH = ROOT / "research/000b2-public/corpus-source.json"
POLICY_PATH = ROOT / "research/000b2-public/subset-selection-policy.json"
SELECTOR_PATH = ROOT / "research/000b2-public/select_subset.py"
DEFAULT_COMMITTED_MANIFEST = ROOT / "research/000b2-public/subset-manifest.json"
B2P03_CANONICAL_MERGE = "83eca872148f329033c299f6671d275edf2d7b58"
B2P03_FRONTIER_RECONCILIATION_MERGE = "c1a576db2adf67cb4b830c280e6cba80b0ae3b43"
EXPECTED_ARCHIVES = {
    "test-clean.tar.gz": "test-clean",
    "test-other.tar.gz": "test-other",
}
MAX_ARCHIVE_MEMBERS = 100_000
MAX_EXTRACTED_BYTES_PER_ARCHIVE = 2 * 1024 * 1024 * 1024
COPY_CHUNK_SIZE = 1024 * 1024
BASE64_LINE_WIDTH = 120


class FreezeError(ValueError):
    """Raised when B2P04 cannot prove one immutable source-membership freeze."""


def require(condition: bool, message: str) -> None:
    """Fail closed on one B2P04 invariant."""
    if not condition:
        raise FreezeError(message)


def sha256_bytes(data: bytes) -> str:
    """Return lowercase SHA-256 for exact bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash one repository file exactly as stored."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(COPY_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    """Serialize the digest projection as compact sorted-key UTF-8 JSON plus one newline."""
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def render_manifest(value: dict[str, Any]) -> bytes:
    """Render the committed human-reviewable manifest deterministically."""
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def freeze_digest(value: dict[str, Any]) -> str:
    """Hash the full manifest with its self-referential digest field replaced by null."""
    projection = copy.deepcopy(value)
    require("freeze_digest_sha256" in projection, "manifest is missing freeze_digest_sha256")
    projection["freeze_digest_sha256"] = None
    return sha256_bytes(canonical_json_bytes(projection))


def load_json(path: Path, label: str) -> dict[str, Any]:
    """Load one required repository JSON object."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FreezeError(f"unable to load {label}: {path}: {error}") from error
    require(isinstance(value, dict), f"{label} root must be an object")
    return value


def normalized_member_parts(name: str) -> tuple[str, ...]:
    """Return safe POSIX archive components without normalizing unsafe syntax away."""
    require(bool(name), "archive member name must not be empty")
    require("\\" not in name, f"archive member must not contain backslashes: {name!r}")
    pure = PurePosixPath(name)
    require(not pure.is_absolute(), f"absolute archive member is prohibited: {name!r}")
    raw = name[:-1] if name.endswith("/") else name
    parts = tuple(raw.split("/"))
    require(parts and all(part not in {"", ".", ".."} for part in parts), f"unsafe archive member path: {name!r}")
    return parts


def validate_member_scope(member: tarfile.TarInfo, partition: str) -> tuple[str, ...]:
    """Require one tar member to be a regular file/directory inside exactly one expected partition."""
    parts = normalized_member_parts(member.name)
    if parts == ("LibriSpeech",):
        require(member.isdir(), "LibriSpeech archive root must be a directory")
        return parts
    require(len(parts) >= 2, f"archive member is outside expected LibriSpeech/{partition} root: {member.name!r}")
    require(parts[:2] == ("LibriSpeech", partition), f"archive member escaped expected partition {partition}: {member.name!r}")
    require(not member.issym(), f"symbolic link archive member is prohibited: {member.name!r}")
    require(not member.islnk(), f"hard-link archive member is prohibited: {member.name!r}")
    require(member.isdir() or member.isreg(), f"special archive member is prohibited: {member.name!r}")
    return parts


def copy_exact(source: BinaryIO, destination: Path, expected_size: int) -> None:
    """Copy exactly one regular member and reject a size mismatch."""
    written = 0
    with destination.open("xb") as output:
        while chunk := source.read(COPY_CHUNK_SIZE):
            output.write(chunk)
            written += len(chunk)
    require(written == expected_size, f"archive member size mismatch for {destination}: expected {expected_size}, got {written}")


def safe_extract_archive(archive_path: Path, destination: Path, partition: str) -> dict[str, int]:
    """Extract one exact archive without tarfile.extract* and reject links/traversal/special nodes."""
    require(partition in {"test-clean", "test-other"}, f"unexpected partition: {partition}")
    destination.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    regular_files = 0
    total_regular_bytes = 0
    member_count = 0

    try:
        archive = tarfile.open(archive_path, mode="r:gz")
    except (OSError, tarfile.TarError) as error:
        raise FreezeError(f"unable to open archive {archive_path.name}: {error}") from error

    with archive:
        for member in archive:
            member_count += 1
            require(member_count <= MAX_ARCHIVE_MEMBERS, f"archive member-count bound exceeded for {archive_path.name}")
            parts = validate_member_scope(member, partition)
            key = "/".join(parts)
            require(key not in seen, f"duplicate archive member path: {key}")
            seen.add(key)
            target = destination.joinpath(*parts)

            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                require(target.is_dir() and not target.is_symlink(), f"unsafe extracted directory state: {target}")
                continue

            total_regular_bytes += member.size
            require(
                total_regular_bytes <= MAX_EXTRACTED_BYTES_PER_ARCHIVE,
                f"archive extracted-byte bound exceeded for {archive_path.name}",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            require(not target.exists(), f"archive regular-file collision: {target}")
            source = archive.extractfile(member)
            require(source is not None, f"regular archive member could not be opened: {member.name!r}")
            with source:
                copy_exact(source, target, member.size)
            regular_files += 1

    require(member_count > 0, f"archive contains no members: {archive_path.name}")
    require(regular_files > 0, f"archive contains no regular files: {archive_path.name}")
    partition_root = destination / "LibriSpeech" / partition
    require(partition_root.is_dir() and not partition_root.is_symlink(), f"extracted partition root missing: {partition}")
    return {
        "member_count": member_count,
        "regular_file_count": regular_files,
        "regular_file_bytes": total_regular_bytes,
    }


def validate_provenance() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Require the exact canonical B2P02 archive identities needed by B2P04."""
    provenance = load_json(CORPUS_SOURCE_PATH, "corpus source")
    require(provenance.get("schema_version") == "000b2-public-corpus-source-v2", "corpus-source schema drift")
    require(provenance.get("task") == "B2P02", "corpus-source task drift")
    require(provenance.get("state") == "ARCHIVES_MATERIALIZED_AND_VERIFIED", "B2P02 archive state is not verified")
    resource = provenance.get("resource")
    require(isinstance(resource, dict), "corpus-source resource must be an object")
    require(resource.get("resource_page") == "https://www.openslr.org/12/", "OpenSLR resource page drift")
    require(resource.get("license") == "CC BY 4.0", "LibriSpeech license drift")
    require(resource.get("checksum_manifest") == materialize_archives.CHECKSUM_MANIFEST_URL, "checksum manifest drift")

    partitions = provenance.get("partitions")
    require(isinstance(partitions, list), "corpus-source partitions must be a list")
    by_name: dict[str, dict[str, Any]] = {}
    for raw in partitions:
        require(isinstance(raw, dict), "corpus-source partition must be an object")
        name = raw.get("name")
        require(isinstance(name, str) and name in EXPECTED_ARCHIVES, f"unexpected corpus-source archive: {name!r}")
        require(name not in by_name, f"duplicate corpus-source archive: {name}")
        require(raw.get("source_url") == materialize_archives.ARCHIVE_SOURCE_URLS[name], f"source URL drift for {name}")
        require(raw.get("materialized") is True, f"B2P02 materialized flag drift for {name}")
        require(raw.get("archive_retained_in_repository") is False, f"archive retention boundary drift for {name}")
        require(isinstance(raw.get("archive_bytes"), int) and raw["archive_bytes"] > 0, f"archive byte count missing for {name}")
        require(isinstance(raw.get("official_md5"), str) and len(raw["official_md5"]) == 32, f"official MD5 missing for {name}")
        require(isinstance(raw.get("archive_sha256"), str) and len(raw["archive_sha256"]) == 64, f"archive SHA-256 missing for {name}")
        by_name[name] = raw
    require(set(by_name) == set(EXPECTED_ARCHIVES), "corpus-source archive set drift")
    return provenance, [by_name[name] for name in sorted(by_name)]


def fetch_verify_and_extract(work_dir: Path, archive_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Re-fetch exact B2P02 bytes, verify upstream MD5, and safely extract only expected partitions."""
    manifest_text, resolved_manifest = materialize_archives.fetch_text(materialize_archives.CHECKSUM_MANIFEST_URL)
    require(resolved_manifest == materialize_archives.CHECKSUM_MANIFEST_URL, "checksum manifest final URL drift")
    official = materialize_archives.parse_official_md5(manifest_text, set(EXPECTED_ARCHIVES))

    extraction_root = work_dir / "extracted"
    observations: list[dict[str, Any]] = []
    for row in archive_rows:
        name = str(row["name"])
        require(official[name] == row["official_md5"], f"live official MD5 drift for {name}")
        archive_path = work_dir / name
        observed = materialize_archives.stream_archive(str(row["source_url"]), archive_path)
        require(observed["resolved_url"] == row["source_url"], f"final archive URL drift for {name}")
        require(observed["bytes"] == row["archive_bytes"], f"archive byte-count mismatch for {name}")
        require(observed["md5"] == row["official_md5"], f"archive MD5 mismatch for {name}")
        require(observed["sha256"] == row["archive_sha256"], f"archive SHA-256 mismatch for {name}")
        extraction = safe_extract_archive(archive_path, extraction_root, EXPECTED_ARCHIVES[name])
        archive_path.unlink(missing_ok=True)
        observations.append(
            {
                "name": name,
                "source_url": row["source_url"],
                "bytes": row["archive_bytes"],
                "official_md5": row["official_md5"],
                "archive_sha256": row["archive_sha256"],
                "safe_extraction": extraction,
            }
        )
    return observations


def build_manifest(selection: dict[str, Any], provenance: dict[str, Any], archives: list[dict[str, Any]]) -> dict[str, Any]:
    """Project the canonical B2P03 selection into one immutable B2P04 source-membership freeze."""
    require(selection.get("schema_version") == "000b2-public-subset-selection-candidate-v1", "selection candidate schema drift")
    require(selection.get("task") == "B2P03", "selection candidate task drift")
    require(selection.get("state") == "UNFROZEN_SELECTION_CANDIDATE", "selection candidate state drift")
    require(selection.get("subset_manifest_frozen") is False, "B2P03 candidate must remain unfrozen")
    require(selection.get("candidate_decoding_started") is False, "candidate decoding already started")
    require(selection.get("primary_decoding_started") is False, "primary decoding already started")
    partitions = selection.get("partitions")
    require(isinstance(partitions, list) and len(partitions) == 2, "selection candidate partition count drift")

    total_speakers = sum(int(partition["speaker_count"]) for partition in partitions)
    total_utterances = sum(int(partition["utterance_count"]) for partition in partitions)
    manifest: dict[str, Any] = {
        "schema_version": "000b2-public-subset-manifest-v1",
        "task": "B2P04",
        "state": "FROZEN_SOURCE_MEMBERSHIP",
        "frozen": True,
        "freeze_digest_sha256": None,
        "authority": {
            "b2p03_canonical_merge": B2P03_CANONICAL_MERGE,
            "b2p03_frontier_reconciliation_merge": B2P03_FRONTIER_RECONCILIATION_MERGE,
        },
        "source_corpus": {
            "name": "LibriSpeech ASR corpus SLR12",
            "resource_page": provenance["resource"]["resource_page"],
            "license": provenance["resource"]["license"],
            "corpus_source_path": "research/000b2-public/corpus-source.json",
            "corpus_source_sha256": sha256_file(CORPUS_SOURCE_PATH),
            "archives": [
                {
                    "name": row["name"],
                    "source_url": row["source_url"],
                    "bytes": row["bytes"],
                    "official_md5": row["official_md5"],
                    "archive_sha256": row["archive_sha256"],
                }
                for row in archives
            ],
        },
        "selection_engine": {
            "selector_path": "research/000b2-public/select_subset.py",
            "selector_sha256": sha256_file(SELECTOR_PATH),
            "policy_path": "research/000b2-public/subset-selection-policy.json",
            "policy_sha256": selection["policy_sha256"],
            "selection_material": selection["selection_material"],
            "hash_algorithm": selection["hash_algorithm"],
        },
        "membership": {
            "kind": "SOURCE_FLAC_IDENTITIES_AND_REFERENCE_TRANSCRIPTS",
            "total_speakers": total_speakers,
            "total_utterances": total_utterances,
            "partitions": partitions,
        },
        "preprocessing_boundary": {
            "status": "NOT_CAPTURED_B2P06",
            "canonical_preprocessed_file_sha256_present": False,
            "later_binding_must_reference_freeze_digest": True,
        },
        "claim_guards": {
            "candidate_revalidation_started": False,
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
    }
    manifest["freeze_digest_sha256"] = freeze_digest(manifest)
    return manifest


def emit_manifest_base64(rendered: bytes) -> None:
    """Emit a bounded machine-recoverable candidate to Actions logs for the pre-commit probe."""
    encoded = base64.b64encode(rendered).decode("ascii")
    print("B2P04_MANIFEST_BASE64_BEGIN")
    for offset in range(0, len(encoded), BASE64_LINE_WIDTH):
        print(encoded[offset : offset + BASE64_LINE_WIDTH])
    print("B2P04_MANIFEST_BASE64_END")


def parse_args() -> argparse.Namespace:
    """Parse the bounded B2P04 freeze command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--committed", type=Path, default=DEFAULT_COMMITTED_MANIFEST)
    return parser.parse_args()


def main() -> None:
    """Reproduce the exact source membership and require a byte-identical committed freeze."""
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        provenance, archive_rows = validate_provenance()
        archive_observations = fetch_verify_and_extract(args.work_dir, archive_rows)
        selection = select_subset.select_subset(args.work_dir / "extracted")
        manifest = build_manifest(selection, provenance, archive_observations)
        rendered = render_manifest(manifest)
        args.output.write_bytes(rendered)
        print(f"B2P04_FREEZE_DIGEST_SHA256={manifest['freeze_digest_sha256']}")
        print(f"B2P04_TOTAL_SPEAKERS={manifest['membership']['total_speakers']}")
        print(f"B2P04_TOTAL_UTTERANCES={manifest['membership']['total_utterances']}")

        if not args.committed.is_file():
            emit_manifest_base64(rendered)
            raise FreezeError("committed subset manifest is missing; deterministic candidate emitted to the log")

        committed = args.committed.read_bytes()
        if committed != rendered:
            emit_manifest_base64(rendered)
            raise FreezeError("committed subset manifest is not byte-identical to the exact regenerated freeze")

        print("B2P04_SUBSET_MANIFEST=PASS")
        print("B2P04_SAFE_EXTRACTION=PASS")
        print("B2P04_SOURCE_ARCHIVE_BINDING=PASS")
        print("B2P04_SELECTION_ENGINE_BINDING=PASS")
        print("B2P04_SUBSET_MANIFEST_FROZEN=YES")
        print("B2P04_CANDIDATE_REVALIDATION_STARTED=NO")
        print("B2P04_CANDIDATE_DECODING_STARTED=NO")
        print("B2P04_PRIMARY_DECODING_STARTED=NO")
        print("B2P06_PREPROCESSING_IDENTITIES=NOT_CAPTURED")
        print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
        print("PRODUCT_CODE_AUTHORIZED=NO")
    except FreezeError as error:
        raise SystemExit(f"B2P04_SUBSET_MANIFEST=FAIL: {error}") from error
    finally:
        shutil.rmtree(args.work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
