#!/usr/bin/env python3
"""Adversarially verify the deterministic B2P03 subset-selection implementation."""

from __future__ import annotations

import inspect
import json
import shutil
import tempfile
from pathlib import Path
from typing import Callable

from select_subset import SelectionError, render_json, select_subset

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "research/000b2-public/subset-selection-policy.json"
SELECTOR_PATH = ROOT / "research/000b2-public/select_subset.py"


def require(condition: bool, message: str) -> None:
    """Abort verification when a B2P03 invariant is not demonstrated."""
    if not condition:
        raise SystemExit(f"B2P03_SUBSET_SELECTION=FAIL: {message}")


def speaker_ids(partition: str) -> list[str]:
    """Return deterministic synthetic speaker IDs with disjoint partition ranges."""
    start = 1000 if partition == "test-clean" else 2000
    return [str(start + offset) for offset in range(13)]


def chapter_id(speaker_id: str) -> str:
    """Derive a deterministic synthetic chapter ID from one speaker ID."""
    return str(int(speaker_id) + 10000)


def utterance_id(speaker_id: str, chapter: str, ordinal: int) -> str:
    """Build a valid synthetic LibriSpeech-style utterance identifier."""
    return f"{speaker_id}-{chapter}-{ordinal:04d}"


def write_speaker_fixture(partition_root: Path, partition: str, speaker_id: str, reverse: bool) -> None:
    """Create one complete synthetic speaker/chapter transcript and FLAC fixture."""
    chapter = chapter_id(speaker_id)
    chapter_root = partition_root / speaker_id / chapter
    chapter_root.mkdir(parents=True, exist_ok=True)
    ordinals = list(range(11))
    if reverse:
        ordinals.reverse()
    transcript_lines: list[str] = []
    for ordinal in ordinals:
        uid = utterance_id(speaker_id, chapter, ordinal)
        transcript = f"TRANSCRIPT {partition} {speaker_id} {ordinal:04d}"
        transcript_lines.append(f"{uid} {transcript}")
        payload = f"synthetic-flac-fixture|{partition}|{speaker_id}|{chapter}|{ordinal:04d}".encode("utf-8")
        (chapter_root / f"{uid}.flac").write_bytes(payload)
    (chapter_root / f"{speaker_id}-{chapter}.trans.txt").write_text("\n".join(transcript_lines) + "\n", encoding="utf-8")


def build_valid_fixture(root: Path, reverse: bool = False) -> Path:
    """Build a synthetic LibriSpeech-like tree large enough to exercise the frozen 12x10 design."""
    librispeech_root = root / "LibriSpeech"
    for partition in ("test-clean", "test-other"):
        partition_root = librispeech_root / partition
        ids = speaker_ids(partition)
        if reverse:
            ids.reverse()
        for speaker_id in ids:
            write_speaker_fixture(partition_root, partition, speaker_id, reverse)
    return librispeech_root


def expect_selection_error(mutator: Callable[[Path], None], expected_fragment: str) -> None:
    """Require one adversarial corpus mutation to fail closed with the expected reason class."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        librispeech_root = build_valid_fixture(root)
        mutator(librispeech_root)
        try:
            select_subset(root)
        except SelectionError as error:
            require(expected_fragment in str(error), f"unexpected fail-closed reason: {error}")
        else:
            raise SystemExit(f"B2P03_SUBSET_SELECTION=FAIL: mutation unexpectedly accepted: {expected_fragment}")


def remove_one_audio(librispeech_root: Path) -> None:
    """Delete one transcript-paired FLAC to test missing-audio rejection."""
    first_audio = sorted((librispeech_root / "test-clean").rglob("*.flac"))[0]
    first_audio.unlink()


def add_orphan_audio(librispeech_root: Path) -> None:
    """Add one structurally valid FLAC without a transcript entry."""
    speaker_id = speaker_ids("test-clean")[0]
    chapter = chapter_id(speaker_id)
    uid = utterance_id(speaker_id, chapter, 9999)
    (librispeech_root / "test-clean" / speaker_id / chapter / f"{uid}.flac").write_bytes(b"orphan")


def duplicate_transcript_id(librispeech_root: Path) -> None:
    """Duplicate one transcript line to test duplicate utterance rejection."""
    transcript_file = sorted((librispeech_root / "test-clean").rglob("*.trans.txt"))[0]
    lines = transcript_file.read_text(encoding="utf-8").splitlines()
    transcript_file.write_text("\n".join(lines + [lines[0]]) + "\n", encoding="utf-8")


def overlap_speaker_between_partitions(librispeech_root: Path) -> None:
    """Copy one clean speaker into the other partition to test speaker-disjointness rejection."""
    speaker_id = speaker_ids("test-clean")[0]
    source = librispeech_root / "test-clean" / speaker_id
    destination = librispeech_root / "test-other" / speaker_id
    shutil.copytree(source, destination)


def replace_audio_with_external_symlink(librispeech_root: Path) -> None:
    """Replace one canonical-looking audio path with a symlink to external bytes."""
    audio_path = sorted((librispeech_root / "test-clean").rglob("*.flac"))[0]
    external = librispeech_root.parent / "candidate-output.flac"
    external.write_bytes(b"external-candidate-like-audio")
    audio_path.unlink()
    audio_path.symlink_to(external)


def replace_transcript_with_external_symlink(librispeech_root: Path) -> None:
    """Replace one canonical-looking transcript path with a symlink to external text."""
    transcript_path = sorted((librispeech_root / "test-clean").rglob("*.trans.txt"))[0]
    external = librispeech_root.parent / "candidate-output.trans.txt"
    external.write_text(transcript_path.read_text(encoding="utf-8"), encoding="utf-8")
    transcript_path.unlink()
    transcript_path.symlink_to(external)


def replace_speaker_directory_with_external_symlink(librispeech_root: Path) -> None:
    """Replace a speaker directory with a symlink that recursive globs would otherwise skip."""
    speaker_id = speaker_ids("test-clean")[0]
    speaker_path = librispeech_root / "test-clean" / speaker_id
    external = librispeech_root.parent / "external-speaker-tree"
    shutil.move(str(speaker_path), str(external))
    speaker_path.symlink_to(external, target_is_directory=True)


def verify_symlinked_corpus_ancestor_rejected() -> None:
    """Reject a corpus path whose final component is regular but an ancestor is a symlink."""
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        real_parent = base / "real-parent"
        real_corpus = real_parent / "corpus"
        build_valid_fixture(real_corpus)
        linked_parent = base / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        indirect_corpus = linked_parent / "corpus"
        require(not indirect_corpus.is_symlink(), "adversarial corpus leaf must itself remain non-symlink")
        try:
            select_subset(indirect_corpus)
        except SelectionError as error:
            require("symbolic link is not allowed for corpus root" in str(error), f"unexpected symlink-ancestry reason: {error}")
        else:
            raise SystemExit("B2P03_SUBSET_SELECTION=FAIL: symlinked corpus ancestry unexpectedly accepted")


def verify_policy_boundaries() -> None:
    """Verify the committed B2P03 policy keeps all later execution and claim gates closed."""
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    require(policy["task"] == "B2P03", "policy task drift")
    require(policy["state"] == "SELECTION_LOGIC_FROZEN_MANIFEST_NOT_FROZEN", "policy state drift")
    require([item["name"] for item in policy["partitions"]] == ["test-clean", "test-other"], "partition order drift")
    require(all(item["speakers_per_partition"] == 12 for item in policy["partitions"]), "speaker count drift")
    require(all(item["utterances_per_speaker_max"] == 10 for item in policy["partitions"]), "utterance cap drift")
    require(policy["ordering"]["hash_algorithm"] == "SHA-256", "hash algorithm drift")
    require(policy["ordering"]["selection_material"] == "wispral-000b2-public-b2p03-v1", "selection material drift")
    require(policy["source_contract"]["candidate_outputs_allowed"] is False, "candidate outputs must remain prohibited")
    require(policy["source_contract"]["candidate_specific_behavior_allowed"] is False, "candidate-specific behavior must remain prohibited")
    require(policy["output_contract"]["kind"] == "UNFROZEN_SELECTION_CANDIDATE", "B2P03 output kind drift")
    require(policy["output_contract"]["manifest_digest_emitted"] is False, "B2P03 must not emit a manifest digest")
    require(policy["claim_guards"]["subset_manifest_frozen"] is False, "B2P04 manifest freeze must remain false")
    require(policy["claim_guards"]["candidate_decoding_started"] is False, "candidate decoding must remain false")
    require(policy["claim_guards"]["primary_decoding_started"] is False, "primary decoding must remain false")
    require(policy["claim_guards"]["human_developer_speech_accuracy_evidence"] == "ABSENT", "human developer-speech evidence must remain absent")
    require(policy["claim_guards"]["production_stt_selected"] is False, "production STT selection must remain false")
    require(policy["claim_guards"]["product_code_authorized"] is False, "product-code authority must remain false")

    signature = inspect.signature(select_subset)
    require(set(signature.parameters) == {"corpus_root", "policy_path"}, "selector input surface must remain corpus + policy only")
    source = SELECTOR_PATH.read_text(encoding="utf-8")
    require("subprocess" not in source, "selector must not invoke external candidate/runtime processes")
    require("requests" not in source and "urllib" not in source, "selector must not access network sources")
    require("is_symlink" in source, "selector must explicitly reject symbolic-link source indirection")
    require("require_no_symlink_ancestry" in source, "selector must reject symlinked corpus ancestry")
    require("require_symlink_free_tree" in source, "selector must reject internal directory symlink nodes")


def verify_determinism_and_shape() -> None:
    """Prove traversal and transcript ordering cannot change the selected source identities."""
    with tempfile.TemporaryDirectory() as first_temp, tempfile.TemporaryDirectory() as second_temp:
        first_root = Path(first_temp)
        second_root = Path(second_temp)
        build_valid_fixture(first_root, reverse=False)
        build_valid_fixture(second_root, reverse=True)
        first = select_subset(first_root)
        second = select_subset(second_root)
        require(render_json(first) == render_json(second), "selection changed when source creation/transcript order changed")

        require(first["state"] == "UNFROZEN_SELECTION_CANDIDATE", "selection candidate state drift")
        require(first["subset_manifest_frozen"] is False, "selection candidate must not freeze B2P04 manifest")
        require(first["candidate_decoding_started"] is False, "selection candidate must not start candidate decoding")
        require(first["primary_decoding_started"] is False, "selection candidate must not start primary decoding")
        require([item["name"] for item in first["partitions"]] == ["test-clean", "test-other"], "selected partition order drift")

        selected_speakers: set[str] = set()
        selected_utterances: set[str] = set()
        for partition in first["partitions"]:
            require(partition["speaker_count"] == 12, f"{partition['name']} selected speaker count drift")
            require(partition["utterance_count"] == 120, f"{partition['name']} selected utterance count drift")
            require(len(partition["speakers"]) == 12, f"{partition['name']} speaker records drift")
            for speaker in partition["speakers"]:
                speaker_id = speaker["speaker_id"]
                require(speaker_id not in selected_speakers, f"selected speaker overlap: {speaker_id}")
                selected_speakers.add(speaker_id)
                require(len(speaker["utterances"]) == 10, f"selected utterance cap drift for speaker {speaker_id}")
                for utterance in speaker["utterances"]:
                    uid = utterance["utterance_id"]
                    require(uid not in selected_utterances, f"selected utterance overlap: {uid}")
                    selected_utterances.add(uid)
                    require(utterance["source_partition"] == partition["name"], f"partition binding drift for {uid}")
                    require(utterance["speaker_id"] == speaker_id, f"speaker binding drift for {uid}")
                    require(utterance["source_audio_path"].startswith(f"LibriSpeech/{partition['name']}/{speaker_id}/"), f"source path drift for {uid}")
                    digest = utterance["source_file_sha256"]
                    require(len(digest) == 64 and all(character in "0123456789abcdef" for character in digest), f"invalid source SHA-256 for {uid}")
        require(len(selected_speakers) == 24, "global selected speaker count drift")
        require(len(selected_utterances) == 240, "global selected utterance count drift")


def main() -> None:
    """Run deterministic and adversarial B2P03 verification without real corpus or candidate execution."""
    verify_policy_boundaries()
    verify_determinism_and_shape()
    expect_selection_error(remove_one_audio, "missing audio for transcript utterance")
    expect_selection_error(add_orphan_audio, "audio has no transcript entry")
    expect_selection_error(duplicate_transcript_id, "duplicate transcript utterance id")
    expect_selection_error(overlap_speaker_between_partitions, "speaker overlap across public partitions")
    expect_selection_error(replace_audio_with_external_symlink, "symbolic link is not allowed for partition tree test-clean")
    expect_selection_error(replace_transcript_with_external_symlink, "symbolic link is not allowed for partition tree test-clean")
    expect_selection_error(replace_speaker_directory_with_external_symlink, "symbolic link is not allowed for partition tree test-clean")
    verify_symlinked_corpus_ancestor_rejected()
    print("B2P03_SUBSET_SELECTION=PASS")
    print("B2P03_HASH_ORDERING=SHA256_FROZEN")
    print("B2P03_TRAVERSAL_ORDER_INDEPENDENT=YES")
    print("B2P03_MISSING_PAIR_REJECTION=PASS")
    print("B2P03_DUPLICATE_REJECTION=PASS")
    print("B2P03_SPEAKER_DISJOINTNESS=PASS")
    print("B2P03_SYMLINK_REJECTION=PASS")
    print("B2P03_INTERNAL_DIRECTORY_SYMLINK_REJECTION=PASS")
    print("B2P03_SYMLINK_ANCESTRY_REJECTION=PASS")
    print("B2P03_CANDIDATE_OUTPUT_DEPENDENCY=ABSENT")
    print("B2P03_SUBSET_MANIFEST_FROZEN=NO")
    print("B2P03_CANDIDATE_DECODING_STARTED=NO")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    print("PRODUCT_CODE_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
