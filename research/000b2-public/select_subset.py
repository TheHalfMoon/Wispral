#!/usr/bin/env python3
"""Build an unfrozen deterministic LibriSpeech selection candidate for B2P03."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POLICY_PATH = Path(__file__).with_name("subset-selection-policy.json")
UTTERANCE_ID_RE = re.compile(r"^(?P<speaker>[0-9]+)-(?P<chapter>[0-9]+)-(?P<utterance>[0-9]+)$")
EXPECTED_PARTITIONS = ("test-clean", "test-other")


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
class Utterance:
    """One validated transcript/audio pair from extracted LibriSpeech source data."""

    partition: str
    speaker_id: str
    chapter_id: str
    utterance_id: str
    transcript: str
    audio_path: Path
    source_audio_path: str


def require(condition: bool, message: str) -> None:
    """Fail closed when one deterministic-selection invariant is absent."""
    if not condition:
        raise SelectionError(message)


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash one non-symlink source audio file without loading it all into memory."""
    require(not path.is_symlink(), f"symbolic link is not allowed for source audio: {path}")
    require(path.is_file(), f"source audio is not a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(selection_material: str, *components: str) -> str:
    """Hash UTF-8 components separated by NUL bytes using the frozen ordering contract."""
    encoded = "\0".join((selection_material, *components)).encode("utf-8")
    return sha256_bytes(encoded)


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
    require([item.get("name") for item in partition_rows if isinstance(item, dict)] == list(EXPECTED_PARTITIONS), "partition order drift")
    rules: list[PartitionRule] = []
    for item in partition_rows:
        require(isinstance(item, dict), "selection partition rule must be an object")
        require(set(item) == {"name", "speakers_per_partition", "utterances_per_speaker_max"}, "selection partition rule keys drift")
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


def require_no_symlink_components(path: Path, anchor: Path, label: str) -> None:
    """Reject symlinks at the anchor or any lexical component from anchor through path."""
    try:
        relative = path.relative_to(anchor)
    except ValueError as error:
        raise SelectionError(f"{label} escapes configured corpus root: {path}") from error
    require(not anchor.is_symlink(), f"symbolic link is not allowed for {label}: {anchor}")
    current = anchor
    for component in relative.parts:
        current = current / component
        require(not current.is_symlink(), f"symbolic link is not allowed for {label}: {current}")


def require_symlink_free_tree(root: Path, label: str) -> None:
    """Reject every symlink node under a source tree, including non-traversed directory links."""
    require(not root.is_symlink(), f"symbolic link is not allowed for {label}: {root}")
    for path in root.rglob("*"):
        require(not path.is_symlink(), f"symbolic link is not allowed for {label}: {path}")


def resolve_librispeech_root(corpus_root: Path) -> Path:
    """Resolve a caller-provided extraction root while rejecting symlinked corpus components."""
    require_no_symlink_ancestry(corpus_root, "corpus root")
    require(not corpus_root.is_symlink(), f"symbolic link is not allowed for corpus root: {corpus_root}")
    root = corpus_root.absolute()
    require(not root.is_symlink(), f"symbolic link is not allowed for corpus root: {root}")
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


def validate_relative_source_path(partition: str, speaker: str, chapter: str, path: Path, partition_root: Path) -> None:
    """Require one transcript/audio file to live at the canonical partition/speaker/chapter depth."""
    relative = path.relative_to(partition_root)
    require(len(relative.parts) == 3, f"unexpected LibriSpeech path depth: {partition}/{relative.as_posix()}")
    require(relative.parts[0] == speaker, f"speaker directory mismatch for {path.name}")
    require(relative.parts[1] == chapter, f"chapter directory mismatch for {path.name}")


def discover_partition(librispeech_root: Path, partition: str) -> dict[str, list[Utterance]]:
    """Enumerate and validate every non-symlink transcript/audio pair in one configured partition."""
    partition_root = librispeech_root / partition
    require_no_symlink_components(partition_root, librispeech_root, "partition root")
    require_symlink_free_tree(partition_root, f"partition tree {partition}")
    transcript_files = sorted(partition_root.rglob("*.trans.txt"), key=lambda item: item.relative_to(partition_root).as_posix())
    audio_files = sorted(partition_root.rglob("*.flac"), key=lambda item: item.relative_to(partition_root).as_posix())
    require(transcript_files, f"partition {partition} contains no transcript files")
    require(audio_files, f"partition {partition} contains no FLAC files")

    by_id: dict[str, Utterance] = {}
    expected_audio_paths: dict[str, Path] = {}
    for transcript_file in transcript_files:
        require_no_symlink_components(transcript_file, partition_root, "transcript source")
        relative = transcript_file.relative_to(partition_root)
        require(len(relative.parts) == 3, f"unexpected transcript path depth: {partition}/{relative.as_posix()}")
        speaker_dir, chapter_dir = relative.parts[0], relative.parts[1]
        expected_stem = f"{speaker_dir}-{chapter_dir}"
        require(
            transcript_file.name == f"{expected_stem}.trans.txt",
            f"transcript filename does not match speaker/chapter directories: {relative.as_posix()}",
        )
        require(transcript_file.is_file(), f"transcript source is not a regular file: {relative.as_posix()}")
        lines = transcript_file.read_text(encoding="utf-8").splitlines()
        require(lines, f"empty transcript file: {relative.as_posix()}")
        for line_number, line in enumerate(lines, start=1):
            require(bool(line.strip()), f"blank transcript line at {relative.as_posix()}:{line_number}")
            fields = line.split(maxsplit=1)
            require(len(fields) == 2 and bool(fields[1].strip()), f"malformed transcript line at {relative.as_posix()}:{line_number}")
            utterance_id, transcript = fields[0], fields[1].strip()
            speaker_id, chapter_id, _ = parse_utterance_id(utterance_id)
            require(speaker_id == speaker_dir, f"transcript speaker mismatch for {utterance_id}")
            require(chapter_id == chapter_dir, f"transcript chapter mismatch for {utterance_id}")
            require(utterance_id not in by_id, f"duplicate transcript utterance id: {utterance_id}")
            audio_path = transcript_file.parent / f"{utterance_id}.flac"
            require_no_symlink_components(audio_path, partition_root, "audio source")
            require(audio_path.is_file(), f"missing audio for transcript utterance: {partition}/{speaker_dir}/{chapter_dir}/{utterance_id}.flac")
            source_path = f"LibriSpeech/{partition}/{speaker_id}/{chapter_id}/{utterance_id}.flac"
            by_id[utterance_id] = Utterance(
                partition=partition,
                speaker_id=speaker_id,
                chapter_id=chapter_id,
                utterance_id=utterance_id,
                transcript=transcript,
                audio_path=audio_path,
                source_audio_path=source_path,
            )
            expected_audio_paths[utterance_id] = audio_path

    seen_audio_ids: set[str] = set()
    for audio_file in audio_files:
        require_no_symlink_components(audio_file, partition_root, "audio source")
        utterance_id = audio_file.name.removesuffix(".flac")
        speaker_id, chapter_id, _ = parse_utterance_id(utterance_id)
        validate_relative_source_path(partition, speaker_id, chapter_id, audio_file, partition_root)
        require(audio_file.is_file(), f"audio source is not a regular file: {audio_file.relative_to(partition_root).as_posix()}")
        require(utterance_id not in seen_audio_ids, f"duplicate audio utterance id: {utterance_id}")
        seen_audio_ids.add(utterance_id)
        require(utterance_id in by_id, f"audio has no transcript entry: {partition}/{audio_file.relative_to(partition_root).as_posix()}")
        require(audio_file == expected_audio_paths[utterance_id], f"audio path mismatch for utterance: {utterance_id}")

    require(set(by_id) == seen_audio_ids, f"transcript/audio identity mismatch in partition {partition}")
    speakers: dict[str, list[Utterance]] = {}
    for utterance in by_id.values():
        speakers.setdefault(utterance.speaker_id, []).append(utterance)
    for speaker_id, utterances in speakers.items():
        require(utterances, f"speaker has no utterances: {partition}/{speaker_id}")
    return speakers


def select_partition(rule: PartitionRule, speakers: dict[str, list[Utterance]], selection_material: str) -> dict[str, Any]:
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
                        "source_file_sha256": sha256_file(item.audio_path),
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
    for partition, speakers in inventories.items():
        for utterances in speakers.values():
            for utterance in utterances:
                require(utterance.utterance_id not in all_utterance_ids, f"utterance overlap across partitions: {utterance.utterance_id}")
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
