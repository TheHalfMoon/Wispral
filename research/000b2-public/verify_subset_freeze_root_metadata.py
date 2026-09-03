#!/usr/bin/env python3
"""Regression-gate exact LibriSpeech root metadata handling for B2P04 extraction."""

from __future__ import annotations

import io
import tarfile
import tempfile
from pathlib import Path

import freeze_subset_manifest as freeze


def require(condition: bool, message: str) -> None:
    """Fail closed on one root-metadata regression."""
    if not condition:
        raise SystemExit(f"B2P04_ROOT_METADATA_VERIFIER=FAIL: {message}")


def write_tar(path: Path, root_name: str, payload: bytes = b"metadata") -> None:
    """Write one minimal archive with exact partition content and one root metadata file."""
    with tarfile.open(path, "w:gz") as archive:
        for name in ("LibriSpeech/", "LibriSpeech/test-clean/", "LibriSpeech/test-clean/1/", "LibriSpeech/test-clean/1/2/"):
            directory = tarfile.TarInfo(name)
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)

        metadata = tarfile.TarInfo(f"LibriSpeech/{root_name}")
        metadata.type = tarfile.REGTYPE
        metadata.size = len(payload)
        archive.addfile(metadata, io.BytesIO(payload))

        audio = tarfile.TarInfo("LibriSpeech/test-clean/1/2/1-2-3.flac")
        audio.type = tarfile.REGTYPE
        audio.size = 5
        archive.addfile(audio, io.BytesIO(b"audio"))


def verify_allowed_root_metadata_is_not_extracted() -> None:
    """Allow only the exact metadata allowlist and keep those bytes outside extracted selection input."""
    for name in sorted(freeze.ALLOWED_LIBRISPEECH_ROOT_METADATA):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "fixture.tar.gz"
            output = root / "out"
            write_tar(archive, name)
            observation = freeze.safe_extract_archive(archive, output, "test-clean")
            require(observation["ignored_root_metadata_file_count"] == 1, f"ignored metadata count drift for {name}")
            require(not (output / "LibriSpeech" / name).exists(), f"root metadata was extracted into selection input: {name}")
            require((output / "LibriSpeech/test-clean/1/2/1-2-3.flac").read_bytes() == b"audio", "partition file missing")


def verify_unknown_root_metadata_is_rejected() -> None:
    """Reject unreviewed LibriSpeech root files rather than widening the extraction surface."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        archive = root / "fixture.tar.gz"
        write_tar(archive, "UNREVIEWED.TXT")
        try:
            freeze.safe_extract_archive(archive, root / "out", "test-clean")
        except freeze.FreezeError:
            return
    raise SystemExit("B2P04_ROOT_METADATA_VERIFIER=FAIL: unreviewed root metadata was accepted")


def main() -> None:
    """Run the exact root-metadata regression surface."""
    verify_allowed_root_metadata_is_not_extracted()
    verify_unknown_root_metadata_is_rejected()
    print("B2P04_ROOT_METADATA_VERIFIER=PASS")
    print("B2P04_ROOT_METADATA_ALLOWLIST=EXACT")
    print("B2P04_ROOT_METADATA_EXTRACTED=NO")


if __name__ == "__main__":
    main()
