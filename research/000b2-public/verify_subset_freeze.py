#!/usr/bin/env python3
"""Fail closed on B2P04 safe extraction, manifest semantics, and pre-decode boundaries."""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import freeze_subset_manifest as freeze

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "research/000b2-public/subset-manifest.json"
READINESS_PATH = ROOT / "research/000b2-public/readiness.json"
TASKS_PATH = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
CURRENT_PATH = ROOT / "specs/CURRENT.md"
HEX = set("0123456789abcdef")


def require(condition: bool, message: str) -> None:
    """Abort verification when one B2P04 invariant is absent."""
    if not condition:
        raise SystemExit(f"B2P04_FREEZE_VERIFIER=FAIL: {message}")


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    """Reject added, removed, or renamed manifest fields."""
    require(set(value) == expected, f"{label} keys drift: expected {sorted(expected)}, got {sorted(value)}")


def require_sha256(value: Any, label: str) -> str:
    """Require one lowercase 64-character SHA-256 value."""
    require(isinstance(value, str) and len(value) == 64 and set(value) <= HEX, f"{label} must be lowercase SHA-256")
    return value


def load_object(path: Path, label: str) -> dict[str, Any]:
    """Load one required JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{label} root must be an object")
    return value


def write_tar(path: Path, members: list[tuple[tarfile.TarInfo, bytes | None]]) -> None:
    """Write one synthetic gzip tar used only by extraction adversarial tests."""
    with tarfile.open(path, "w:gz") as archive:
        for info, payload in members:
            if payload is None:
                archive.addfile(info)
            else:
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))


def directory(name: str) -> tuple[tarfile.TarInfo, None]:
    """Create one synthetic directory member."""
    info = tarfile.TarInfo(name)
    info.type = tarfile.DIRTYPE
    info.mode = 0o755
    return info, None


def regular(name: str, payload: bytes = b"fixture") -> tuple[tarfile.TarInfo, bytes]:
    """Create one synthetic regular-file member."""
    info = tarfile.TarInfo(name)
    info.type = tarfile.REGTYPE
    info.mode = 0o644
    return info, payload


def require_rejected(members: list[tuple[tarfile.TarInfo, bytes | None]], partition: str, label: str) -> None:
    """Require one malicious archive shape to fail before extraction can be trusted."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        archive_path = root / "fixture.tar.gz"
        write_tar(archive_path, members)
        try:
            freeze.safe_extract_archive(archive_path, root / "out", partition)
        except freeze.FreezeError:
            return
    raise SystemExit(f"B2P04_FREEZE_VERIFIER=FAIL: malicious archive accepted: {label}")


def verify_safe_extraction() -> None:
    """Exercise regular extraction and reject traversal/link/special/cross-partition inputs."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        archive_path = root / "good.tar.gz"
        write_tar(
            archive_path,
            [
                directory("LibriSpeech/"),
                directory("LibriSpeech/test-clean/"),
                directory("LibriSpeech/test-clean/1/"),
                directory("LibriSpeech/test-clean/1/2/"),
                regular("LibriSpeech/test-clean/1/2/1-2-3.flac", b"audio"),
                regular("LibriSpeech/test-clean/1/2/1-2.trans.txt", b"1-2-3 TEXT\n"),
            ],
        )
        observation = freeze.safe_extract_archive(archive_path, root / "out", "test-clean")
        require(observation["regular_file_count"] == 2, "good archive regular-file count drift")
        require((root / "out/LibriSpeech/test-clean/1/2/1-2-3.flac").read_bytes() == b"audio", "good archive bytes drift")

    require_rejected([regular("../escape")], "test-clean", "parent traversal")
    require_rejected([regular("/absolute")], "test-clean", "absolute path")
    require_rejected([regular("LibriSpeech/test-other/1/2/x")], "test-clean", "cross-partition member")

    symlink = tarfile.TarInfo("LibriSpeech/test-clean/link")
    symlink.type = tarfile.SYMTYPE
    symlink.linkname = "target"
    require_rejected([(symlink, None)], "test-clean", "symbolic link")

    hardlink = tarfile.TarInfo("LibriSpeech/test-clean/hard")
    hardlink.type = tarfile.LNKTYPE
    hardlink.linkname = "LibriSpeech/test-clean/target"
    require_rejected([(hardlink, None)], "test-clean", "hard link")

    fifo = tarfile.TarInfo("LibriSpeech/test-clean/fifo")
    fifo.type = tarfile.FIFOTYPE
    require_rejected([(fifo, None)], "test-clean", "FIFO")

    negative_size = tarfile.TarInfo("LibriSpeech/test-clean/negative.flac")
    negative_size.type = tarfile.REGTYPE
    negative_size.size = -1
    try:
        freeze.validate_member_scope(negative_size, "test-clean")
    except freeze.FreezeError:
        pass
    else:
        raise SystemExit("B2P04_FREEZE_VERIFIER=FAIL: negative regular-file size was accepted")


def verify_static_boundaries() -> None:
    """Require the implementation to stay on the bounded no-extractall/no-subprocess surface."""
    source = (ROOT / "research/000b2-public/freeze_subset_manifest.py").read_text(encoding="utf-8")
    for prohibited in ("extractall(", ".extract(", "subprocess", "candidate transcript", "candidate_output"):
        require(prohibited not in source, f"freeze engine contains prohibited surface: {prohibited}")
    for required in (
        "safe_extract_archive",
        "select_subset.select_subset",
        "freeze_digest",
        "B2P04_MANIFEST_BASE64_BEGIN",
        "B2P06_PREPROCESSING_IDENTITIES=NOT_CAPTURED",
        "B2P04_CANDIDATE_REVALIDATION_STARTED=NO",
    ):
        require(required in source, f"freeze engine missing required boundary marker: {required}")


def verify_current_authority() -> str:
    """Require and return the exact current authority phase while preserving the B2P04 freeze."""
    readiness = load_object(READINESS_PATH, "public readiness")
    require(readiness.get("state") == "READY", "public readiness must remain READY")
    public = readiness.get("public_human_baseline")
    require(isinstance(public, dict), "public_human_baseline must be an object")
    require(public.get("candidate_decoding_started") is False, "candidate decoding must remain closed")
    preprocessing = readiness.get("preprocessing")
    require(isinstance(preprocessing, dict), "preprocessing readiness must be an object")
    environment = readiness.get("execution_environment")
    require(isinstance(environment, dict), "execution environment readiness must be an object")
    attempt = readiness.get("attempt_manifest")
    require(isinstance(attempt, dict) and attempt.get("primary_decoding_started") is False and attempt.get("frozen") is False, "primary decoding and B2P08 freeze must remain closed")
    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "claim_guards must be an object")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence guard drift")
    require(guards.get("production_stt_selected") is False, "production STT must remain unselected")
    require(guards.get("product_code_authorized") is False, "product code must remain unauthorized")

    completed_through = readiness.get("completed_through")
    next_action = readiness.get("next_action")
    tasks = TASKS_PATH.read_text(encoding="utf-8")
    current = CURRENT_PATH.read_text(encoding="utf-8")
    require("- [x] `B2P03`" in tasks, "B2P03 must remain complete")
    if completed_through == "B2P07":
        require(environment.get("resolved") is True, "B2P07 reconciliation must mark environment resolved")
    else:
        require(environment.get("resolved") is False, "B2P07 environment must remain unresolved before B2P07 reconciliation")

    if completed_through == "B2P03":
        require(preprocessing.get("resolved") is False, "B2P06 preprocessing must remain unresolved before B2P06 canonical reconciliation")
        require(public.get("subset_manifest_frozen") is False, "pre-reconciliation readiness must remain unfrozen")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P04 only:"), "pre-reconciliation readiness must authorize B2P04 only")
        require("Do not begin candidate revalidation or decoding until B2P04 is canonical." in next_action, "pre-reconciliation B2P05/decode boundary drift")
        require("- [ ] `B2P04`" in tasks, "B2P04 must remain unchecked during implementation qualification")
        require("- [ ] `B2P05`" in tasks, "B2P05 must remain uncompleted before B2P04 canonicalization")
        require("Execute and canonically qualify `B2P04` only" in current, "pre-reconciliation frontier is not B2P04-only")
        require("B2P05 remains non-authorized" in current, "pre-reconciliation frontier must keep B2P05 closed")
        return "B2P03"

    if completed_through == "B2P04":
        require(preprocessing.get("resolved") is False, "B2P06 preprocessing must remain unresolved before B2P06 canonical reconciliation")
        require(public.get("subset_manifest_frozen") is True, "canonical B2P04 readiness must bind the frozen manifest")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P05 only:"), "canonical B2P04 reconciliation must authorize B2P05 only")
        require("Do not begin candidate decoding, B2P06 preprocessing capture, or primary decoding until B2P05 is canonical." in next_action, "canonical B2P05/decode boundary drift")
        require("- [x] `B2P04`" in tasks, "canonical reconciliation must mark B2P04 complete")
        require("- [ ] `B2P05`" in tasks, "B2P05 must remain open during B2P05 execution qualification")
        require("- [ ] `B2P06`" in tasks, "B2P06 must remain unauthorized")
        require("current bounded execution unit `B2P05`" in current, "canonical frontier is not B2P05-only")
        require("B2P05 is now authorized only to revalidate" in current, "canonical frontier must bound B2P05 to identity revalidation")
        require("Candidate decoding, B2P06 preprocessing capture, and primary decoding remain unauthorized during B2P05." in current, "canonical B2P05 boundaries drift")
        return "B2P04"

    if completed_through == "B2P05":
        require(preprocessing.get("resolved") is False, "B2P06 preprocessing must remain unresolved before B2P06 canonical reconciliation")
        require(public.get("subset_manifest_frozen") is True, "B2P05 reconciliation must preserve the B2P04 frozen manifest")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P06 only:"), "B2P05 reconciliation must authorize B2P06 only")
        require("Do not begin B2P07 environment capture, B2P08 attempt freeze, or candidate decoding until B2P06 is canonical." in next_action, "B2P06 successor boundary drift")
        require("- [x] `B2P04`" in tasks, "B2P04 must remain complete")
        require("- [x] `B2P05`" in tasks, "B2P05 reconciliation must mark B2P05 complete")
        require("- [ ] `B2P06`" in tasks, "B2P06 must remain open and not pre-completed")
        require("- [ ] `B2P07`" in tasks, "B2P07 must remain unauthorized")
        require("current bounded execution unit `B2P06`" in current, "reconciled frontier is not B2P06-only")
        require("Execute and canonically qualify `B2P06` only" in current, "reconciled current view must authorize B2P06 only")
        require("B2P07 remains non-authorized" in current, "reconciled frontier must keep B2P07 closed")
        return "B2P05"

    if completed_through == "B2P06":
        require(preprocessing.get("resolved") is True, "B2P06 reconciliation must mark preprocessing resolved")
        require(public.get("subset_manifest_frozen") is True, "B2P06 reconciliation must preserve the B2P04 frozen manifest")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P07 only:"), "B2P06 reconciliation must authorize B2P07 only")
        require("Do not begin B2P08 attempt freeze or candidate decoding until B2P07 is canonical." in next_action, "B2P07 successor boundary drift")
        require("- [x] `B2P06`" in tasks, "B2P06 reconciliation must mark B2P06 complete")
        require("- [ ] `B2P07`" in tasks, "B2P07 must remain open during B2P07 execution qualification")
        require("- [ ] `B2P08`" in tasks, "B2P08 must remain unauthorized")
        require("current bounded execution unit `B2P07`" in current, "reconciled frontier is not B2P07-only")
        require("Execute and canonically qualify `B2P07` only" in current, "reconciled current view must authorize B2P07 only")
        require("B2P08 remains non-authorized" in current, "reconciled frontier must keep B2P08 closed")
        return "B2P06"

    if completed_through == "B2P07":
        require(preprocessing.get("resolved") is True, "B2P07 reconciliation must preserve preprocessing resolution")
        require(public.get("subset_manifest_frozen") is True, "B2P07 reconciliation must preserve the B2P04 frozen manifest")
        require(isinstance(next_action, str) and next_action.startswith("Execute B2P08 only:"), "B2P07 reconciliation must authorize B2P08 only")
        require("Do not begin candidate or primary decoding until B2P08 is canonical." in next_action, "B2P08 successor boundary drift")
        require("- [x] `B2P06`" in tasks, "B2P06 must remain complete")
        require("- [x] `B2P07`" in tasks, "B2P07 reconciliation must mark B2P07 complete")
        require("- [ ] `B2P08`" in tasks, "B2P08 must remain open during B2P08 execution qualification")
        require("current bounded execution unit `B2P08`" in current, "reconciled frontier is not B2P08-only")
        require("Execute and canonically qualify `B2P08` only" in current, "reconciled current view must authorize B2P08 only")
        require("Candidate and primary decoding remain unauthorized" in current, "reconciled frontier must keep decoding closed")
        return "B2P07"

    raise SystemExit(f"B2P04_FREEZE_VERIFIER=FAIL: unsupported completed_through state: {completed_through!r}")


def verify_manifest(authority_phase: str) -> None:
    """Verify the committed freeze; absence is permitted only for the B2P03 probe phase."""
    if not MANIFEST_PATH.exists():
        require(authority_phase == "B2P03", "canonical B2P04 reconciliation requires the committed subset manifest")
        print("B2P04_COMMITTED_MANIFEST=ABSENT_PROBE_REQUIRED")
        return
    require(MANIFEST_PATH.is_file() and not MANIFEST_PATH.is_symlink(), "subset manifest must be a regular non-symlink file")
    manifest = load_object(MANIFEST_PATH, "subset manifest")
    require_exact_keys(
        manifest,
        {
            "schema_version", "task", "state", "frozen", "freeze_digest_sha256", "authority",
            "source_corpus", "selection_engine", "membership", "preprocessing_boundary", "claim_guards",
        },
        "subset_manifest",
    )
    require(manifest.get("schema_version") == "000b2-public-subset-manifest-v1", "manifest schema drift")
    require(manifest.get("task") == "B2P04", "manifest task drift")
    require(manifest.get("state") == "FROZEN_SOURCE_MEMBERSHIP", "manifest state drift")
    require(manifest.get("frozen") is True, "manifest frozen flag must be true")
    digest = require_sha256(manifest.get("freeze_digest_sha256"), "freeze_digest_sha256")
    require(digest == freeze.freeze_digest(manifest), "manifest freeze digest does not reproduce")
    require(MANIFEST_PATH.read_bytes() == freeze.render_manifest(manifest), "manifest bytes are not canonical pretty JSON")

    authority = manifest.get("authority")
    require(isinstance(authority, dict), "authority must be an object")
    require_exact_keys(authority, {"b2p03_canonical_merge", "b2p03_frontier_reconciliation_merge"}, "authority")
    require(authority.get("b2p03_canonical_merge") == freeze.B2P03_CANONICAL_MERGE, "B2P03 canonical merge binding drift")
    require(authority.get("b2p03_frontier_reconciliation_merge") == freeze.B2P03_FRONTIER_RECONCILIATION_MERGE, "B2P03 frontier reconciliation binding drift")

    source_corpus = manifest.get("source_corpus")
    require(isinstance(source_corpus, dict), "source_corpus must be an object")
    require_exact_keys(
        source_corpus,
        {"name", "resource_page", "license", "corpus_source_path", "corpus_source_sha256", "archives"},
        "source_corpus",
    )
    require(source_corpus.get("name") == "LibriSpeech ASR corpus SLR12", "source corpus name drift")
    require(source_corpus.get("resource_page") == "https://www.openslr.org/12/", "source corpus URL drift")
    require(source_corpus.get("license") == "CC BY 4.0", "source corpus license drift")
    require(source_corpus.get("corpus_source_path") == "research/000b2-public/corpus-source.json", "corpus-source path drift")
    require(source_corpus.get("corpus_source_sha256") == freeze.sha256_file(freeze.CORPUS_SOURCE_PATH), "corpus-source byte identity drift")
    archives = source_corpus.get("archives")
    require(isinstance(archives, list) and len(archives) == 2, "manifest must bind exactly two archives")
    provenance = load_object(freeze.CORPUS_SOURCE_PATH, "corpus source")
    expected_by_name = {row["name"]: row for row in provenance["partitions"]}
    for row in archives:
        require(isinstance(row, dict), "archive binding must be an object")
        require_exact_keys(row, {"name", "source_url", "bytes", "official_md5", "archive_sha256"}, "archive_binding")
        name = row.get("name")
        require(name in expected_by_name, f"unexpected archive binding: {name!r}")
        expected = expected_by_name[name]
        require(row.get("source_url") == expected["source_url"], f"archive source URL drift for {name}")
        require(row.get("bytes") == expected["archive_bytes"], f"archive byte count drift for {name}")
        require(row.get("official_md5") == expected["official_md5"], f"archive MD5 drift for {name}")
        require(row.get("archive_sha256") == expected["archive_sha256"], f"archive SHA-256 drift for {name}")

    engine = manifest.get("selection_engine")
    require(isinstance(engine, dict), "selection_engine must be an object")
    require_exact_keys(engine, {"selector_path", "selector_sha256", "policy_path", "policy_sha256", "selection_material", "hash_algorithm"}, "selection_engine")
    require(engine.get("selector_path") == "research/000b2-public/select_subset.py", "selector path drift")
    require(engine.get("selector_sha256") == freeze.sha256_file(freeze.SELECTOR_PATH), "selector byte identity drift")
    require(engine.get("policy_path") == "research/000b2-public/subset-selection-policy.json", "policy path drift")
    require(engine.get("policy_sha256") == freeze.sha256_file(freeze.POLICY_PATH), "policy byte identity drift")
    require(engine.get("selection_material") == "wispral-000b2-public-b2p03-v1", "selection material drift")
    require(engine.get("hash_algorithm") == "SHA-256", "selection hash algorithm drift")

    membership = manifest.get("membership")
    require(isinstance(membership, dict), "membership must be an object")
    require_exact_keys(membership, {"kind", "total_speakers", "total_utterances", "partitions"}, "membership")
    require(membership.get("kind") == "SOURCE_FLAC_IDENTITIES_AND_REFERENCE_TRANSCRIPTS", "membership kind drift")
    partitions = membership.get("partitions")
    require(isinstance(partitions, list) and [p.get("name") for p in partitions if isinstance(p, dict)] == ["test-clean", "test-other"], "membership partition order drift")

    global_speakers: set[str] = set()
    global_utterances: set[str] = set()
    counted_speakers = 0
    counted_utterances = 0
    for partition in partitions:
        require(isinstance(partition, dict), "membership partition must be an object")
        require_exact_keys(partition, {"name", "speaker_count", "utterance_count", "speakers"}, "membership_partition")
        partition_name = partition["name"]
        speakers = partition.get("speakers")
        require(isinstance(speakers, list) and len(speakers) == 12, f"{partition_name} must contain 12 selected speakers")
        require(partition.get("speaker_count") == len(speakers), f"{partition_name} speaker_count mismatch")
        partition_utterances = 0
        for speaker in speakers:
            require(isinstance(speaker, dict), "speaker record must be an object")
            require_exact_keys(speaker, {"speaker_id", "utterances"}, "speaker_record")
            speaker_id = speaker.get("speaker_id")
            require(isinstance(speaker_id, str) and speaker_id.isdigit(), "speaker_id must be numeric text")
            require(speaker_id not in global_speakers, f"speaker overlap detected: {speaker_id}")
            global_speakers.add(speaker_id)
            utterances = speaker.get("utterances")
            require(isinstance(utterances, list) and 1 <= len(utterances) <= 10, f"speaker {speaker_id} utterance count outside 1..10")
            for utterance in utterances:
                require(isinstance(utterance, dict), "utterance record must be an object")
                require_exact_keys(
                    utterance,
                    {"source_partition", "speaker_id", "chapter_id", "utterance_id", "reference_transcript", "source_audio_path", "source_file_sha256"},
                    "utterance_record",
                )
                uid = utterance.get("utterance_id")
                chapter_id = utterance.get("chapter_id")
                require(utterance.get("source_partition") == partition_name, f"partition binding drift for {uid}")
                require(utterance.get("speaker_id") == speaker_id, f"speaker binding drift for {uid}")
                require(isinstance(chapter_id, str) and chapter_id.isdigit(), f"chapter_id invalid for {uid}")
                require(isinstance(uid, str) and uid.startswith(f"{speaker_id}-{chapter_id}-"), f"utterance id structure drift: {uid!r}")
                require(uid not in global_utterances, f"duplicate utterance id: {uid}")
                global_utterances.add(uid)
                transcript = utterance.get("reference_transcript")
                require(isinstance(transcript, str) and bool(transcript.strip()), f"empty reference transcript for {uid}")
                expected_path = f"LibriSpeech/{partition_name}/{speaker_id}/{chapter_id}/{uid}.flac"
                require(utterance.get("source_audio_path") == expected_path, f"source path drift for {uid}")
                require_sha256(utterance.get("source_file_sha256"), f"source_file_sha256[{uid}]")
                require("preprocessed" not in utterance, f"B2P04 utterance must not contain B2P06 preprocessing identity: {uid}")
                partition_utterances += 1
        require(partition.get("utterance_count") == partition_utterances, f"{partition_name} utterance_count mismatch")
        counted_speakers += len(speakers)
        counted_utterances += partition_utterances

    require(counted_speakers == 24 and membership.get("total_speakers") == 24, "global selected speaker count must be 24")
    require(24 <= counted_utterances <= 240, "global utterance count outside bounded design")
    require(membership.get("total_utterances") == counted_utterances, "global utterance count mismatch")

    preprocessing = manifest.get("preprocessing_boundary")
    require(isinstance(preprocessing, dict), "preprocessing_boundary must be an object")
    require_exact_keys(preprocessing, {"status", "canonical_preprocessed_file_sha256_present", "later_binding_must_reference_freeze_digest"}, "preprocessing_boundary")
    require(preprocessing == {
        "status": "NOT_CAPTURED_B2P06",
        "canonical_preprocessed_file_sha256_present": False,
        "later_binding_must_reference_freeze_digest": True,
    }, "B2P06 preprocessing boundary drift")

    guards = manifest.get("claim_guards")
    require(isinstance(guards, dict), "claim_guards must be an object")
    require(guards == {
        "candidate_revalidation_started": False,
        "candidate_decoding_started": False,
        "primary_decoding_started": False,
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "production_stt_selected": False,
        "product_code_authorized": False,
    }, "manifest claim guard drift")

    print(f"B2P04_FREEZE_DIGEST_SHA256={digest}")
    print(f"B2P04_TOTAL_SPEAKERS={counted_speakers}")
    print(f"B2P04_TOTAL_UTTERANCES={counted_utterances}")
    print("B2P04_COMMITTED_MANIFEST=VALID")


def verify_manifest_presence_phase_regression() -> None:
    """Require absent-manifest handling to differ only by the verified authority phase."""
    global MANIFEST_PATH
    original_manifest_path = MANIFEST_PATH
    with tempfile.TemporaryDirectory() as temporary:
        MANIFEST_PATH = Path(temporary) / "missing-subset-manifest.json"
        try:
            try:
                verify_manifest("B2P04")
            except SystemExit as error:
                require(
                    "canonical B2P04 reconciliation requires the committed subset manifest" in str(error),
                    "canonical missing-manifest rejection emitted the wrong failure",
                )
            else:
                raise SystemExit(
                    "B2P04_FREEZE_VERIFIER=FAIL: reconciled B2P04 accepted a missing committed manifest"
                )

            verify_manifest("B2P03")
        finally:
            MANIFEST_PATH = original_manifest_path

    print("B2P04_RECONCILED_MISSING_MANIFEST_REJECTION=PASS")
    print("B2P03_ABSENT_MANIFEST_PROBE=PASS")


def main() -> None:
    """Run all offline B2P04 structural/adversarial gates."""
    verify_static_boundaries()
    verify_safe_extraction()
    verify_manifest_presence_phase_regression()
    authority_phase = verify_current_authority()
    verify_manifest(authority_phase)
    print("B2P04_FREEZE_VERIFIER=PASS")
    print(f"B2P04_AUTHORITY_PHASE={authority_phase}")
    print("B2P04_TAR_TRAVERSAL_REJECTION=PASS")
    print("B2P04_SYMLINK_REJECTION=PASS")
    print("B2P04_HARDLINK_REJECTION=PASS")
    print("B2P04_SPECIAL_NODE_REJECTION=PASS")
    print("B2P04_NEGATIVE_SIZE_REJECTION=PASS")
    print("B2P04_MANIFEST_CANDIDATE_REVALIDATION_STARTED_AT_FREEZE=NO")
    print("B2P04_CANDIDATE_DECODING_STARTED=NO")
    print("B2P04_PRIMARY_DECODING_STARTED=NO")
    print("B2P06_PREPROCESSING_IDENTITIES=NOT_CAPTURED")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    print("PRODUCT_CODE_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
