#!/usr/bin/env python3
"""Build an unfrozen deterministic LibriSpeech selection candidate for B2P03."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POLICY_PATH = Path(__file__).with_name("subset-selection-policy.json")
UTTERANCE_ID_RE = re.compile(r"^(?P<speaker>[0-9]+)-(?P<chapter>[0-9]+)-(?P<utterance>[0-9]+)$")
EXPECTED_PARTITIONS = ("test-clean", "test-other")
READ_CHUNK_SIZE = 1024 * 1024


class SelectionError(ValueError):
    """Raised when corpus structure or selection policy violates B2P03."""


@dataclass(frozen=True)
class PartitionRule:
    """Frozen deterministic selection limits for one public partition."""

    name: str
    speakers_per_partition: int
    utterances_per_speaker_max: int


@dataclass(frozen=True)
class SelectionPolicy:
    """Validated B2P03 selection policy consumed by the selector."""

    selection_material: str
    hash_algorithm: str
    partitions: tuple[PartitionRule, ...]
    policy_sha256: str


@dataclass(frozen=True)
class SourceIdentity:
    """Race-detection identity captured for one validated filesystem node."""

    device: int
    inode: int
    mode: int
    link_count: int
    size: int
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True)
class SourceTreeSnapshot:
    """Validated partition tree identities used for no-follow descriptor access."""

    root_identity: SourceIdentity
    entries: dict[str, SourceIdentity]


@dataclass(frozen=True)
class Utterance:
    """One validated transcript/audio pair from extracted LibriSpeech source data."""

    partition: str
    speaker_id: str
    chapter_id: str
    utterance_id: str
    transcript: str
    source_audio_path: str
    source_file_sha256: str


def require(condition: bool, message: str) -> None:
    """Fail closed when one deterministic-selection invariant is absent."""
    if not condition:
        raise SelectionError(message)


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def stable_hash(selection_material: str, *components: str) -> str:
    """Hash UTF-8 components separated by NUL bytes using the frozen ordering contract."""
    encoded = "\0".join((selection_material, *components)).encode("utf-8")
    return sha256_bytes(encoded)


def source_identity(value: os.stat_result) -> SourceIdentity:
    """Project stat metadata needed to detect source-node replacement or mutation."""
    return SourceIdentity(
        device=value.st_dev,
        inode=value.st_ino,
        mode=value.st_mode,
        link_count=value.st_nlink,
        size=value.st_size,
        mtime_ns=value.st_mtime_ns,
        ctime_ns=value.st_ctime_ns,
    )


def require_identity(actual: SourceIdentity, expected: SourceIdentity, label: str) -> None:
    """Reject any node whose identity changed after the validated tree snapshot."""
    require(actual == expected, f"{label} identity changed since validation")


def no_follow_flags(*, directory: bool) -> int:
    """Return fail-closed POSIX open flags for descriptor-relative source access."""
    no_follow = getattr(os, "O_NOFOLLOW", None)
    require(isinstance(no_follow, int), "race-safe source validation requires O_NOFOLLOW support")
    flags = os.O_RDONLY | no_follow
    if directory:
        directory_flag = getattr(os, "O_DIRECTORY", None)
        require(isinstance(directory_flag, int), "race-safe source validation requires O_DIRECTORY support")
        flags |= directory_flag
    else:
        non_block = getattr(os, "O_NONBLOCK", 0)
        if isinstance(non_block, int):
            flags |= non_block
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if isinstance(close_on_exec, int):
        flags |= close_on_exec
    return flags


def open_absolute_directory_for_snapshot(path: Path, label: str) -> tuple[int, SourceIdentity]:
    """Open an absolute directory chain without following links and return its live identity."""
    absolute = path.absolute()
    require(absolute.is_absolute() and bool(absolute.anchor), f"{label} must resolve to an absolute path")
    directory_flags = no_follow_flags(directory=True)
    current_fd: int | None = None
    try:
        current_fd = os.open(absolute.anchor, directory_flags)
        for component in absolute.parts[1:]:
            next_fd = os.open(component, directory_flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        observed = source_identity(os.fstat(current_fd))
        require(stat.S_ISDIR(observed.mode), f"{label} is not a directory")
        result = current_fd
        current_fd = None
        return result, observed
    except OSError as error:
        raise SelectionError(f"unable to open {label} without following links: {path}: {error}") from error
    finally:
        if current_fd is not None:
            os.close(current_fd)


def open_absolute_directory_no_follow(path: Path, expected: SourceIdentity, label: str) -> int:
    """Open an absolute directory one component at a time and require the captured identity."""
    directory_fd, observed = open_absolute_directory_for_snapshot(path, label)
    try:
        require_identity(observed, expected, label)
        result = directory_fd
        directory_fd = -1
        return result
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)


def snapshot_entry(snapshot: SourceTreeSnapshot, relative: Path, label: str) -> SourceIdentity:
    """Return the prevalidated identity for one partition-relative source node."""
    key = relative.as_posix()
    expected = snapshot.entries.get(key)
    require(expected is not None, f"{label} was not present in the validated source tree: {key}")
    assert expected is not None
    return expected


def open_regular_file_beneath(
    root_fd: int,
    relative: Path,
    snapshot: SourceTreeSnapshot,
    label: str,
) -> tuple[int, SourceIdentity]:
    """Open one validated regular file through no-follow directory descriptors."""
    require(not relative.is_absolute(), f"{label} must be relative to the partition root")
    require(relative.parts and all(part not in {"", ".", ".."} for part in relative.parts), f"invalid {label} path")
    directory_flags = no_follow_flags(directory=True)
    file_flags = no_follow_flags(directory=False)
    current_fd = os.dup(root_fd)
    cumulative: list[str] = []
    file_fd: int | None = None
    try:
        for component in relative.parts[:-1]:
            cumulative.append(component)
            expected_directory = snapshot_entry(snapshot, Path(*cumulative), label)
            require(stat.S_ISDIR(expected_directory.mode), f"{label} parent is not a validated directory")
            next_fd = os.open(component, directory_flags, dir_fd=current_fd)
            observed_directory = source_identity(os.fstat(next_fd))
            require_identity(observed_directory, expected_directory, f"{label} parent {'/'.join(cumulative)}")
            os.close(current_fd)
            current_fd = next_fd

        expected_file = snapshot_entry(snapshot, relative, label)
        require(stat.S_ISREG(expected_file.mode), f"{label} is not a validated regular file: {relative.as_posix()}")
        file_fd = os.open(relative.parts[-1], file_flags, dir_fd=current_fd)
        observed_file = source_identity(os.fstat(file_fd))
        require(stat.S_ISREG(observed_file.mode), f"{label} is not a regular file: {relative.as_posix()}")
        require_identity(observed_file, expected_file, label)
        result = file_fd
        file_fd = None
        return result, expected_file
    except OSError as error:
        raise SelectionError(
            f"unable to open {label} without following links: {relative.as_posix()}: {error}"
        ) from error
    finally:
        os.close(current_fd)
        if file_fd is not None:
            os.close(file_fd)


def read_stable_bytes(file_fd: int, expected: SourceIdentity, label: str) -> bytes:
    """Read bytes from the already-open validated descriptor and reject concurrent mutation."""
    before = source_identity(os.fstat(file_fd))
    require_identity(before, expected, label)
    chunks: list[bytes] = []
    while chunk := os.read(file_fd, READ_CHUNK_SIZE):
        chunks.append(chunk)
    after = source_identity(os.fstat(file_fd))
    require_identity(after, before, f"{label} during read")
    return b"".join(chunks)


def sha256_stable_fd(file_fd: int, expected: SourceIdentity, label: str) -> str:
    """Hash bytes from the already-open validated descriptor and reject concurrent mutation."""
    before = source_identity(os.fstat(file_fd))
    require_identity(before, expected, label)
    digest = hashlib.sha256()
    while chunk := os.read(file_fd, READ_CHUNK_SIZE):
        digest.update(chunk)
    after = source_identity(os.fstat(file_fd))
    require_identity(after, before, f"{label} during hash")
    return digest.hexdigest()


def require_no_symlink_ancestry(path: Path, label: str) -> None:
    """Reject a symlink at the path or in any existing ancestor component."""
    absolute = path.absolute()
    resolved = path.resolve(strict=False)
    require(absolute == resolved, f"symbolic link is not allowed for {label}: {path}")


def load_policy(path: Path = POLICY_PATH) -> SelectionPolicy:
    """Load and strictly validate the frozen B2P03 selection policy."""
    require_no_symlink_ancestry(path, "selection policy")
    require(not path.is_symlink(), f"symbolic link is not allowed for selection policy: {path}")
    require(path.is_file(), f"selection policy is not a regular file: {path}")
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"))
    require(isinstance(raw, dict), "selection policy root must be an object")
    require(raw.get("schema_version") == "000b2-public-subset-selection-policy-v1", "selection policy schema drift")
    require(raw.get("task") == "B2P03", "selection policy task must be B2P03")
    require(raw.get("state") == "SELECTION_LOGIC_FROZEN_MANIFEST_NOT_FROZEN", "selection policy state drift")
    require(raw.get("corpus") == "LibriSpeech ASR corpus SLR12", "selection policy corpus drift")

    ordering = raw.get("ordering")
    require(isinstance(ordering, dict), "selection policy ordering must be an object")
    require(ordering.get("hash_algorithm") == "SHA-256", "selection ordering must use SHA-256")
    require(ordering.get("selection_material") == "wispral-000b2-public-b2p03-v1", "selection material drift")
    require(ordering.get("encoding") == "UTF-8", "selection encoding drift")
    require(ordering.get("component_separator") == "NUL", "selection component separator drift")
    require(
        ordering.get("speaker_components") == ["selection_material", "speaker", "partition", "speaker_id"],
        "speaker ordering components drift",
    )
    require(
        ordering.get("utterance_components")
        == ["selection_material", "utterance", "partition", "speaker_id", "chapter_id", "utterance_id"],
        "utterance ordering components drift",
    )
    require(ordering.get("tie_breaker") == "lexicographic stable identifier", "selection tie-breaker drift")

    source_contract = raw.get("source_contract")
    require(isinstance(source_contract, dict), "selection policy source_contract must be an object")
    require(
        source_contract
        == {
            "membership_inputs": "EXTRACTED_LIBRISPEECH_METADATA_AND_SOURCE_CONTENT_IDENTITIES_ONLY",
            "candidate_outputs_allowed": False,
            "candidate_specific_behavior_allowed": False,
            "require_complete_transcript_audio_pairs": True,
            "require_partition_speaker_disjointness": True,
            "reject_duplicate_utterance_ids": True,
            "audio_extension": ".flac",
            "transcript_extension": ".trans.txt",
        },
        "selection source contract drift",
    )

    output_contract = raw.get("output_contract")
    require(isinstance(output_contract, dict), "selection policy output_contract must be an object")
    require(output_contract.get("kind") == "UNFROZEN_SELECTION_CANDIDATE", "selection output kind drift")
    for key in (
        "includes_source_partition",
        "includes_speaker_id",
        "includes_chapter_id",
        "includes_utterance_id",
        "includes_reference_transcript",
        "includes_source_audio_path",
        "includes_source_file_sha256",
    ):
        require(output_contract.get(key) is True, f"selection output contract {key} must remain true")
    require(output_contract.get("manifest_digest_emitted") is False, "B2P03 must not emit a manifest digest")
    require(
        output_contract.get("canonical_preprocessed_file_sha256_emitted") is False,
        "B2P03 must not claim preprocessing identities",
    )

    guards = raw.get("claim_guards")
    require(isinstance(guards, dict), "selection policy claim_guards must be an object")
    require(
        guards
        == {
            "subset_manifest_frozen": False,
            "candidate_decoding_started": False,
            "primary_decoding_started": False,
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
        "selection claim guards drift",
    )

    partition_rows = raw.get("partitions")
    require(isinstance(partition_rows, list), "selection policy partitions must be a list")
    require(
        [item.get("name") for item in partition_rows if isinstance(item, dict)] == list(EXPECTED_PARTITIONS),
        "partition order drift",
    )
    rules: list[PartitionRule] = []
    for item in partition_rows:
        require(isinstance(item, dict), "selection partition rule must be an object")
        require(
            set(item) == {"name", "speakers_per_partition", "utterances_per_speaker_max"},
            "selection partition rule keys drift",
        )
        speakers = item.get("speakers_per_partition")
        utterances = item.get("utterances_per_speaker_max")
        require(type(speakers) is int and speakers == 12, f"{item.get('name')} speaker count must remain 12")
        require(type(utterances) is int and utterances == 10, f"{item.get('name')} utterance cap must remain 10")
        rules.append(PartitionRule(str(item["name"]), speakers, utterances))

    return SelectionPolicy(
        selection_material=str(ordering["selection_material"]),
        hash_algorithm="SHA-256",
        partitions=tuple(rules),
        policy_sha256=sha256_bytes(raw_bytes),
    )


def list_directory_names(directory_fd: int, relative: Path, label: str) -> list[str]:
    """Return one deterministic directory listing from an already-open source descriptor."""
    try:
        names = os.listdir(directory_fd)
    except OSError as error:
        location = relative.as_posix() if relative.parts else "."
        raise SelectionError(f"unable to enumerate {label} directory {location}: {error}") from error
    require(all(name not in {"", ".", ".."} and "/" not in name for name in names), f"invalid source-tree entry in {label}")
    return sorted(names)


def snapshot_directory(
    directory_fd: int,
    relative: Path,
    entries: dict[str, SourceIdentity],
    label: str,
    expected_identity: SourceIdentity,
) -> None:
    """Recursively snapshot one directory while rejecting mutation during enumeration."""
    before = source_identity(os.fstat(directory_fd))
    require(stat.S_ISDIR(before.mode), f"{label} snapshot node is not a directory")
    require_identity(before, expected_identity, f"{label} directory {relative.as_posix() or '.'}")
    names = list_directory_names(directory_fd, relative, label)
    directory_flags = no_follow_flags(directory=True)
    file_flags = no_follow_flags(directory=False)

    for name in names:
        child_relative = relative / name if relative.parts else Path(name)
        child_key = child_relative.as_posix()
        try:
            child_stat = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as error:
            raise SelectionError(f"unable to inspect {label} entry {child_key}: {error}") from error
        captured = source_identity(child_stat)
        require(not stat.S_ISLNK(captured.mode), f"symbolic link is not allowed for {label}: {child_key}")
        require(
            stat.S_ISDIR(captured.mode) or stat.S_ISREG(captured.mode),
            f"special filesystem node is not allowed for {label}: {child_key}",
        )
        if stat.S_ISREG(captured.mode):
            require(captured.link_count == 1, f"hard-linked regular file is not allowed for {label}: {child_key}")
        require(child_key not in entries, f"duplicate source-tree path: {child_key}")

        flags = directory_flags if stat.S_ISDIR(captured.mode) else file_flags
        child_fd: int | None = None
        try:
            child_fd = os.open(name, flags, dir_fd=directory_fd)
            opened = source_identity(os.fstat(child_fd))
            require_identity(opened, captured, f"{label} entry {child_key}")
            entries[child_key] = opened
            if stat.S_ISDIR(opened.mode):
                snapshot_directory(child_fd, child_relative, entries, label, opened)
        except OSError as error:
            raise SelectionError(f"unable to open {label} entry {child_key} without following links: {error}") from error
        finally:
            if child_fd is not None:
                os.close(child_fd)

    after = source_identity(os.fstat(directory_fd))
    require_identity(after, before, f"{label} directory {relative.as_posix() or '.'} during snapshot")


def require_symlink_free_tree(root: Path, label: str) -> SourceTreeSnapshot:
    """Build a descriptor-relative source snapshot and reject links, special nodes, or concurrent mutation."""
    root_fd, root_identity = open_absolute_directory_for_snapshot(root, label)
    entries: dict[str, SourceIdentity] = {}
    try:
        snapshot_directory(root_fd, Path(), entries, label, root_identity)
        final_root = source_identity(os.fstat(root_fd))
        require_identity(final_root, root_identity, f"{label} root during snapshot")
    finally:
        os.close(root_fd)
    return SourceTreeSnapshot(root_identity=root_identity, entries=entries)


def require_snapshot_unchanged(root_fd: int, snapshot: SourceTreeSnapshot, label: str) -> None:
    """Re-snapshot an open partition and reject any added, removed, or changed source node."""
    entries: dict[str, SourceIdentity] = {}
    snapshot_directory(root_fd, Path(), entries, label, snapshot.root_identity)
    final_root = source_identity(os.fstat(root_fd))
    require_identity(final_root, snapshot.root_identity, f"{label} root after inventory consumption")
    final_snapshot = SourceTreeSnapshot(root_identity=final_root, entries=entries)
    require(final_snapshot == snapshot, f"{label} changed after initial snapshot")


def resolve_librispeech_root(corpus_root: Path) -> Path:
    """Resolve a caller-provided extraction root while rejecting symlinked corpus components."""
    require_no_symlink_ancestry(corpus_root, "corpus root")
    require(not corpus_root.is_symlink(), f"symbolic link is not allowed for corpus root: {corpus_root}")
    root = corpus_root.absolute()
    require(root.is_dir(), f"corpus root is not a directory: {corpus_root}")
    nested = root / "LibriSpeech"
    if root.name == "LibriSpeech":
        resolved = root
    elif nested.exists():
        require(not nested.is_symlink(), f"symbolic link is not allowed for LibriSpeech root: {nested}")
        require(nested.is_dir(), f"LibriSpeech extraction is not a directory: {nested}")
        resolved = nested
    elif all((root / partition).is_dir() for partition in EXPECTED_PARTITIONS):
        resolved = root
    else:
        raise SelectionError("corpus root must be LibriSpeech or contain the configured test-clean/test-other extraction")
    require(not resolved.is_symlink(), f"symbolic link is not allowed for LibriSpeech root: {resolved}")
    for partition in EXPECTED_PARTITIONS:
        partition_root = resolved / partition
        require(not partition_root.is_symlink(), f"symbolic link is not allowed for partition root: {partition_root}")
        require(partition_root.is_dir(), f"missing required partition: {partition}")
    return resolved


def parse_utterance_id(value: str) -> tuple[str, str, str]:
    """Parse and validate a canonical numeric LibriSpeech utterance identifier."""
    match = UTTERANCE_ID_RE.fullmatch(value)
    require(match is not None, f"malformed LibriSpeech utterance id: {value!r}")
    assert match is not None
    return match.group("speaker"), match.group("chapter"), match.group("utterance")


def validate_relative_source_path(
    partition: str,
    speaker: str,
    chapter: str,
    path: Path,
    partition_root: Path,
) -> None:
    """Require one transcript/audio file to live at the canonical partition/speaker/chapter depth."""
    relative = path.relative_to(partition_root)
    require(len(relative.parts) == 3, f"unexpected LibriSpeech path depth: {partition}/{relative.as_posix()}")
    require(relative.parts[0] == speaker, f"speaker directory mismatch for {path.name}")
    require(relative.parts[1] == chapter, f"chapter directory mismatch for {path.name}")


def snapshot_inventory(partition_root: Path, snapshot: SourceTreeSnapshot, suffix: str) -> list[Path]:
    """Build a deterministic regular-file inventory only from the validated source snapshot."""
    return [
        partition_root / relative
        for relative, identity in sorted(snapshot.entries.items())
        if stat.S_ISREG(identity.mode) and relative.endswith(suffix)
    ]


def discover_partition(librispeech_root: Path, partition: str) -> dict[str, list[Utterance]]:
    """Enumerate and race-safely validate every transcript/audio pair in one partition."""
    partition_root = librispeech_root / partition
    snapshot = require_symlink_free_tree(partition_root, f"partition tree {partition}")
    partition_fd = open_absolute_directory_no_follow(
        partition_root,
        snapshot.root_identity,
        f"partition root {partition}",
    )
    try:
        transcript_files = snapshot_inventory(partition_root, snapshot, ".trans.txt")
        audio_files = snapshot_inventory(partition_root, snapshot, ".flac")
        require(transcript_files, f"partition {partition} contains no transcript files")
        require(audio_files, f"partition {partition} contains no FLAC files")

        by_id: dict[str, Utterance] = {}
        expected_audio_paths: dict[str, Path] = {}
        for transcript_file in transcript_files:
            relative = transcript_file.relative_to(partition_root)
            require(len(relative.parts) == 3, f"unexpected transcript path depth: {partition}/{relative.as_posix()}")
            speaker_dir, chapter_dir = relative.parts[0], relative.parts[1]
            expected_stem = f"{speaker_dir}-{chapter_dir}"
            require(
                transcript_file.name == f"{expected_stem}.trans.txt",
                f"transcript filename does not match speaker/chapter directories: {relative.as_posix()}",
            )
            transcript_fd, transcript_identity = open_regular_file_beneath(
                partition_fd,
                relative,
                snapshot,
                "transcript source",
            )
            try:
                transcript_bytes = read_stable_bytes(transcript_fd, transcript_identity, "transcript source")
            finally:
                os.close(transcript_fd)
            try:
                lines = transcript_bytes.decode("utf-8").splitlines()
            except UnicodeDecodeError as error:
                raise SelectionError(f"transcript source is not valid UTF-8: {relative.as_posix()}") from error
            require(lines, f"empty transcript file: {relative.as_posix()}")

            for line_number, line in enumerate(lines, start=1):
                require(bool(line.strip()), f"blank transcript line at {relative.as_posix()}:{line_number}")
                fields = line.split(maxsplit=1)
                require(
                    len(fields) == 2 and bool(fields[1].strip()),
                    f"malformed transcript line at {relative.as_posix()}:{line_number}",
                )
                utterance_id, transcript = fields[0], fields[1].strip()
                speaker_id, chapter_id, _ = parse_utterance_id(utterance_id)
                require(speaker_id == speaker_dir, f"transcript speaker mismatch for {utterance_id}")
                require(chapter_id == chapter_dir, f"transcript chapter mismatch for {utterance_id}")
                require(utterance_id not in by_id, f"duplicate transcript utterance id: {utterance_id}")

                audio_path = transcript_file.parent / f"{utterance_id}.flac"
                audio_relative = audio_path.relative_to(partition_root)
                require(
                    audio_relative.as_posix() in snapshot.entries,
                    f"missing audio for transcript utterance: {partition}/{speaker_dir}/{chapter_dir}/{utterance_id}.flac",
                )
                audio_fd, audio_identity = open_regular_file_beneath(
                    partition_fd,
                    audio_relative,
                    snapshot,
                    "audio source",
                )
                try:
                    audio_sha256 = sha256_stable_fd(audio_fd, audio_identity, "audio source")
                finally:
                    os.close(audio_fd)

                source_path = f"LibriSpeech/{partition}/{speaker_id}/{chapter_id}/{utterance_id}.flac"
                by_id[utterance_id] = Utterance(
                    partition=partition,
                    speaker_id=speaker_id,
                    chapter_id=chapter_id,
                    utterance_id=utterance_id,
                    transcript=transcript,
                    source_audio_path=source_path,
                    source_file_sha256=audio_sha256,
                )
                expected_audio_paths[utterance_id] = audio_path

        seen_audio_ids: set[str] = set()
        for audio_file in audio_files:
            relative = audio_file.relative_to(partition_root)
            utterance_id = audio_file.name.removesuffix(".flac")
            speaker_id, chapter_id, _ = parse_utterance_id(utterance_id)
            validate_relative_source_path(partition, speaker_id, chapter_id, audio_file, partition_root)
            audio_fd, _ = open_regular_file_beneath(partition_fd, relative, snapshot, "audio source")
            os.close(audio_fd)
            require(utterance_id not in seen_audio_ids, f"duplicate audio utterance id: {utterance_id}")
            seen_audio_ids.add(utterance_id)
            require(
                utterance_id in by_id,
                f"audio has no transcript entry: {partition}/{relative.as_posix()}",
            )
            require(audio_file == expected_audio_paths[utterance_id], f"audio path mismatch for utterance: {utterance_id}")

        require(set(by_id) == seen_audio_ids, f"transcript/audio identity mismatch in partition {partition}")
        speakers: dict[str, list[Utterance]] = {}
        for utterance in by_id.values():
            speakers.setdefault(utterance.speaker_id, []).append(utterance)
        for speaker_id, utterances in speakers.items():
            require(utterances, f"speaker has no utterances: {partition}/{speaker_id}")
        require_snapshot_unchanged(partition_fd, snapshot, f"partition tree {partition}")
        return speakers
    finally:
        os.close(partition_fd)


def select_partition(
    rule: PartitionRule,
    speakers: dict[str, list[Utterance]],
    selection_material: str,
) -> dict[str, Any]:
    """Select speakers and utterances by frozen hash ordering for one partition."""
    require(
        len(speakers) >= rule.speakers_per_partition,
        f"partition {rule.name} has {len(speakers)} speakers; need {rule.speakers_per_partition}",
    )
    ordered_speakers = sorted(
        speakers,
        key=lambda speaker_id: (stable_hash(selection_material, "speaker", rule.name, speaker_id), speaker_id),
    )
    selected_speakers = ordered_speakers[: rule.speakers_per_partition]
    output_speakers: list[dict[str, Any]] = []
    for speaker_id in selected_speakers:
        ordered_utterances = sorted(
            speakers[speaker_id],
            key=lambda item: (
                stable_hash(
                    selection_material,
                    "utterance",
                    rule.name,
                    item.speaker_id,
                    item.chapter_id,
                    item.utterance_id,
                ),
                item.utterance_id,
            ),
        )
        selected = ordered_utterances[: rule.utterances_per_speaker_max]
        require(selected, f"selected speaker has no utterances: {rule.name}/{speaker_id}")
        output_speakers.append(
            {
                "speaker_id": speaker_id,
                "utterances": [
                    {
                        "source_partition": item.partition,
                        "speaker_id": item.speaker_id,
                        "chapter_id": item.chapter_id,
                        "utterance_id": item.utterance_id,
                        "reference_transcript": item.transcript,
                        "source_audio_path": item.source_audio_path,
                        "source_file_sha256": item.source_file_sha256,
                    }
                    for item in selected
                ],
            }
        )
    return {
        "name": rule.name,
        "speaker_count": len(output_speakers),
        "utterance_count": sum(len(item["utterances"]) for item in output_speakers),
        "speakers": output_speakers,
    }


def select_subset(corpus_root: Path, policy_path: Path = POLICY_PATH) -> dict[str, Any]:
    """Build the deterministic B2P03 selection candidate without freezing a B2P04 manifest."""
    policy = load_policy(policy_path)
    librispeech_root = resolve_librispeech_root(corpus_root)
    inventories = {rule.name: discover_partition(librispeech_root, rule.name) for rule in policy.partitions}

    partition_speaker_sets = {name: set(speakers) for name, speakers in inventories.items()}
    overlap = partition_speaker_sets[EXPECTED_PARTITIONS[0]] & partition_speaker_sets[EXPECTED_PARTITIONS[1]]
    require(not overlap, f"speaker overlap across public partitions: {sorted(overlap)}")

    all_utterance_ids: set[str] = set()
    for speakers in inventories.values():
        for utterances in speakers.values():
            for utterance in utterances:
                require(
                    utterance.utterance_id not in all_utterance_ids,
                    f"utterance overlap across partitions: {utterance.utterance_id}",
                )
                all_utterance_ids.add(utterance.utterance_id)

    selected_partitions = [
        select_partition(rule, inventories[rule.name], policy.selection_material) for rule in policy.partitions
    ]
    return {
        "schema_version": "000b2-public-subset-selection-candidate-v1",
        "task": "B2P03",
        "state": "UNFROZEN_SELECTION_CANDIDATE",
        "policy_sha256": policy.policy_sha256,
        "selection_material": policy.selection_material,
        "hash_algorithm": policy.hash_algorithm,
        "subset_manifest_frozen": False,
        "candidate_decoding_started": False,
        "primary_decoding_started": False,
        "partitions": selected_partitions,
    }


def render_json(value: dict[str, Any]) -> str:
    """Serialize a selection candidate deterministically for inspection or later B2P04 input."""
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def parse_args() -> argparse.Namespace:
    """Parse the bounded B2P03 command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", required=True, type=Path, help="Extracted LibriSpeech root or its parent directory")
    parser.add_argument("--policy", type=Path, default=POLICY_PATH, help="Frozen B2P03 selection policy")
    parser.add_argument("--output", type=Path, help="Write the unfrozen selection candidate JSON to this path")
    return parser.parse_args()


def main() -> None:
    """Run deterministic subset selection against an already extracted public corpus."""
    args = parse_args()
    rendered = render_json(select_subset(args.corpus_root, args.policy))
    if args.output is None:
        print(rendered, end="")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"B2P03_SELECTION_CANDIDATE={args.output}")
    print("B2P03_SUBSET_MANIFEST_FROZEN=NO")
    print("B2P03_CANDIDATE_DECODING_STARTED=NO")


if __name__ == "__main__":
    main()