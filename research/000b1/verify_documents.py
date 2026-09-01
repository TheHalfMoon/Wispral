#!/usr/bin/env python3
"""Cross-document verifier for Wispral 000B1 preregistration authority."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(haystack: str, needles: tuple[str, ...], label: str) -> None:
    for needle in needles:
        if needle not in haystack:
            raise AssertionError(f"{label} missing required text: {needle}")


def forbid(haystack: str, needles: tuple[str, ...], label: str) -> None:
    for needle in needles:
        if needle in haystack:
            raise AssertionError(f"{label} contains superseded text: {needle}")


def main() -> int:
    try:
        methodology = text("docs/research/stt/000b1-frozen-methodology.md")
        require(methodology, (
            "The founding human design is fixed at 20 speakers",
            "Planned total: 720 human utterances.",
            "PCM WAV container",
            "ffmpeg -nostdin -hide_banner -loglevel error -i INPUT -map_metadata -1 -vn -sn -dn -ac 1 -ar 16000 -c:a pcm_s16le OUTPUT.wav",
            "Human consent, retention, redistribution, and withdrawal authority remain a B2 external gate.",
            "No primary test decoding, comparative ranking, production speech integration, or product support claim is authorized",
        ), "frozen methodology prose")
        forbid(methodology, (
            "raw headerless PCM",
            "-f s16le OUTPUT.s16le",
        ), "frozen methodology prose")

        contract = text("docs/research/stt/000b1-benchmark-contract.md")
        require(contract, (
            "If suitable authority does not exist, primary execution is `BLOCKED_EXTERNAL`.",
            "Synthetic/TTS audio MUST NOT contribute to the primary human developer-speech ranking",
            "The primary test manifest must be cryptographically frozen before any candidate decodes it.",
            "- PCM WAV;",
            "Repository/test-specific prompt/context/keyterms/hotwords/grammar are OFF for C0.",
            "No opaque weighted winner score is allowed.",
        ), "benchmark contract")

        tasks = text("specs/000B1-benchmark-candidate-qualification/tasks.md")
        require(tasks, (
            "Readiness disposition for the current B1 evidence unit: `PASS` for preregistration/qualification work only.",
            "- [x] **B119 — Adversarial preregistration review.",
            "- [ ] **B120 — Canonical B1 closeout.",
            "B1 completion contains no primary benchmark ranking.",
        ), "B1 task ledger")
        if "- [x] **B120" in tasks:
            raise AssertionError("B120 must remain open before canonical post-merge closeout")

        adversarial = text("docs/research/stt/000b1-adversarial-review.md")
        require(adversarial, (
            "`B1_CONTRACT_REVIEW: PASS`",
            "`PRIMARY_TEST_DECODING: NO`",
            "`COMPARATIVE_RANKING: NO`",
            "`B2_READY: NO`",
        ), "adversarial review")
    except (AssertionError, OSError) as exc:
        print(f"VERIFY_000B1_DOCUMENTS=FAIL: {exc}", file=sys.stderr)
        return 1

    print("VERIFY_000B1_DOCUMENTS=PASS")
    print("B120_OPEN=YES")
    print("B2_READY=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
