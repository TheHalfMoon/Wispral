#!/usr/bin/env python3
"""Correct Moonshine streaming C0 adapter for 000B2 recovery.

This module contains no corpus discovery, reference loading, scoring, or result
persistence. It only implements the already-frozen Moonshine streaming feed
contract so later ATTEMPT-002 decode code can call one audited adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

SAMPLE_RATE_HZ = 16_000
FEED_CHUNK_MS = 500
FEED_CHUNK_SAMPLES = 8_000
FINAL_ZERO_PAD_MS = 660
FINAL_ZERO_PAD_SAMPLES = 10_560
TRANSCRIPTION_INTERVAL_SECONDS = 0.5
MAX_PRIMARY_UTTERANCE_SECONDS = 12
EXPECTED_RUNTIME_REVISION = "234f60faa0eb388b01cdf7e60aca232af37aefda"
EXPECTED_RUNTIME_DISTRIBUTION = "moonshine-voice"
EXPECTED_RUNTIME_VERSION = "0.1.5"
EXPECTED_MODEL_ASSET_REVISION = "quantized_26_08_21"

# These values are copied from the canonical frozen C0 contract. CPU provider
# selection remains intentionally unset because the contract requires the
# pinned runtime's CPU default rather than an adapter-specific provider list.
MOONSHINE_C0_OPTIONS: dict[str, Any] = {
    "transcription_interval": 0.5,
    "vad_threshold": 0.0,
    "vad_window_duration": 0.5,
    "vad_hop_size": 512,
    "vad_look_behind_sample_count": 8192,
    "vad_max_segment_duration": 15,
    "max_tokens_per_second": 6.5,
    "use_speculative_decoding": True,
    "decode_incomplete_lines": True,
    "identify_speakers": False,
    "return_audio_data": True,
    "word_timestamps": False,
    "keyterm_boost": 2.0,
    "context_max_terms": 200,
}


class C0HarnessError(ValueError):
    """Raised when the frozen Moonshine C0 adapter contract is violated."""


@dataclass(frozen=True)
class FeedTrace:
    """Non-transcript structural trace for one bounded streaming invocation."""

    speech_samples: int
    speech_chunk_samples: tuple[int, ...]
    zero_pad_samples: int
    sample_rate_hz: int
    stream_started: bool
    stream_stopped: bool


def require(condition: bool, message: str) -> None:
    if not condition:
        raise C0HarnessError(message)


def create_transcriber(
    transcriber_type: Callable[..., Any],
    *,
    model_path: Any,
    model_arch: Any,
) -> Any:
    """Construct a Moonshine transcriber with every material frozen C0 option."""

    return transcriber_type(
        model_path=model_path,
        model_arch=model_arch,
        update_interval=TRANSCRIPTION_INTERVAL_SECONDS,
        options=dict(MOONSHINE_C0_OPTIONS),
    )


def speech_chunks(audio: Sequence[float]) -> tuple[Sequence[float], ...]:
    """Partition speech audio in deterministic 500 ms chunks, preserving a final remainder."""

    require(len(audio) > 0, "Moonshine C0 input must contain at least one speech sample")
    require(
        len(audio) <= SAMPLE_RATE_HZ * MAX_PRIMARY_UTTERANCE_SECONDS,
        "Moonshine C0 input exceeds the frozen 12-second primary utterance bound",
    )
    return tuple(
        audio[offset : offset + FEED_CHUNK_SAMPLES]
        for offset in range(0, len(audio), FEED_CHUNK_SAMPLES)
    )


def transcribe_streaming_c0(transcriber: Any, audio: Sequence[float]) -> tuple[Any, FeedTrace]:
    """Run the exact frozen streaming feed contract without reading reference text.

    Repository/test-specific context and keyterms are explicitly disabled before
    the stream begins. Speech is fed in 8,000-sample chunks, followed by one
    universal 10,560-sample zero suffix. The returned trace contains only feed
    structure; it contains no transcript text or comparative measurement.
    """

    chunks = speech_chunks(audio)
    transcriber.set_keyterms([])
    transcriber.set_context(None)
    stream = transcriber.create_stream(update_interval=TRANSCRIPTION_INTERVAL_SECONDS)
    started = False
    stopped = False
    try:
        stream.start()
        started = True
        for chunk in chunks:
            stream.add_audio(chunk, SAMPLE_RATE_HZ)
        stream.add_audio([0.0] * FINAL_ZERO_PAD_SAMPLES, SAMPLE_RATE_HZ)
        result = stream.stop()
        stopped = True
    finally:
        stream.close()

    return result, FeedTrace(
        speech_samples=len(audio),
        speech_chunk_samples=tuple(len(chunk) for chunk in chunks),
        zero_pad_samples=FINAL_ZERO_PAD_SAMPLES,
        sample_rate_hz=SAMPLE_RATE_HZ,
        stream_started=started,
        stream_stopped=stopped,
    )
