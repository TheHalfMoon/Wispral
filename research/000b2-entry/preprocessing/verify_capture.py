#!/usr/bin/env python3
"""Regression checks for fail-closed B2 preprocessing capture."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module():
    spec = importlib.util.spec_from_file_location(
        "wispral_b2_preprocessing_capture", HERE / "capture.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import preprocessing capture")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def state_bytes(
    *,
    attempt_id: str = "B2-ATTEMPT-TEST",
    revision: str = "0" * 40,
    phase: str = "PRE_PRIMARY_CAPTURE",
    primary_started: bool = False,
) -> bytes:
    return (
        json.dumps(
            {
                "attempt_id": attempt_id,
                "canonical_wispral_revision": revision,
                "phase": phase,
                "primary_test_decoding_started": primary_started,
            },
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def fake_ffmpeg(path: Path, version_token: str = "n9.0.1") -> None:
    path.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' 'ffmpeg version {version_token} Copyright (c) FFmpeg'\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def main() -> int:
    capture = load_module()
    revision = "0" * 40
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        binary = root / "ffmpeg"
        fake_ffmpeg(binary)

        qualification = capture.capture(
            binary, attempt_state_path=None, qualification_only=True
        )
        require(
            qualification["ordering"]["mode"] == "QUALIFICATION_ONLY",
            "qualification mode drift",
        )
        require(
            qualification["ordering"]["attempt_time_authority"] is False,
            "qualification became attempt authority",
        )
        require(qualification["source_tag"] == "n9.0.1", "source tag drift")
        require(
            qualification["source_commit"]
            == "bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa",
            "source commit drift",
        )

        state = root / "attempt-state.json"
        raw = state_bytes(revision=revision)
        state.write_bytes(raw)
        bound = capture.capture(
            binary, attempt_state_path=state, qualification_only=False
        )
        ordering = bound["ordering"]
        require(ordering["mode"] == "ATTEMPT_STATE_BOUND", "attempt mode drift")
        require(ordering["attempt_time_authority"] is True, "attempt authority missing")
        require(ordering["attempt_id"] == "B2-ATTEMPT-TEST", "attempt id drift")
        require(ordering["canonical_wispral_revision"] == revision, "revision drift")
        require(
            ordering["attempt_state_sha256"] == hashlib.sha256(raw).hexdigest(),
            "attempt-state digest drift",
        )
        require(
            ordering["primary_test_decoding_started"] is False,
            "attempt ordering drift",
        )

        duplicate = root / "duplicate.json"
        duplicate.write_bytes(
            b'{"attempt_id":"A","attempt_id":"B","canonical_wispral_revision":"'
            + (b"0" * 40)
            + b'","phase":"PRE_PRIMARY_CAPTURE","primary_test_decoding_started":false}'
        )
        try:
            capture.capture(
                binary, attempt_state_path=duplicate, qualification_only=False
            )
        except ValueError:
            pass
        else:
            raise AssertionError("duplicate JSON attempt-state keys were accepted")

        for raw_bad in (
            state_bytes(phase="POST_PRIMARY"),
            state_bytes(primary_started=True),
            state_bytes(revision="A" * 40),
        ):
            bad = root / "bad-state.json"
            bad.write_bytes(raw_bad)
            try:
                capture.capture(
                    binary, attempt_state_path=bad, qualification_only=False
                )
            except ValueError:
                pass
            else:
                raise AssertionError("invalid attempt-state ordering was accepted")

        symlink = root / "state-link.json"
        try:
            symlink.symlink_to(state)
        except (OSError, NotImplementedError):
            pass
        else:
            try:
                capture.capture(
                    binary, attempt_state_path=symlink, qualification_only=False
                )
            except ValueError:
                pass
            else:
                raise AssertionError("symlink attempt state was accepted")

        wrong = root / "ffmpeg-wrong"
        fake_ffmpeg(wrong, "9.0.1")
        try:
            capture.capture(wrong, attempt_state_path=None, qualification_only=True)
        except ValueError:
            pass
        else:
            raise AssertionError("non-tag FFmpeg version identity was accepted")

        require(
            bound["binary_sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest(),
            "binary digest drift",
        )

    print("VERIFY_000B2_PREPROCESSING_CAPTURE=PASS")
    print("RELEASE_TAG_IDENTITY=PINNED")
    print("ATTEMPT_STATE_BOUND=YES")
    print("DUPLICATE_JSON_KEYS=REJECTED")
    print("SYMLINK_ATTEMPT_STATE=REJECTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
