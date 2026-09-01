# Specification 000B1 — Frozen Methodology Details

**Status:** normative preregistration detail; no primary benchmark decoding performed  
**Canonical Wispral base:** `6b5696a6becc360948282712cc9339df9cb3a67c`  
**Machine-readable authority:** `research/000b1/frozen-methodology.json`

This document explains the exact decisions frozen by the machine-readable record. If prose and JSON disagree, the discrepancy is a preregistration defect that must be corrected before B1 closeout; neither may be silently reinterpreted after primary results exist.

## Human panel design

The founding human design is fixed at 20 speakers with speaker-disjoint splits:

| Split | Speakers | Developer-entity utterances per speaker | General/collateral utterances per speaker |
| --- | ---: | ---: | ---: |
| development | 4 | 24 | 12 |
| qualification | 4 | 24 | 12 |
| test | 12 | 24 | 12 |

Planned total: 720 human utterances. The held-out test panel contains 288 developer-entity utterances plus 144 general/collateral utterances.

Rationale:

- twelve test speakers provide speaker-disjoint replication rather than a single-voice showcase;
- 24 developer-entity utterances per test speaker provides 288 primary technical utterances while keeping recording burden bounded;
- separate development and qualification speakers allow script, annotation, harness, and non-primary operational work without touching test speakers;
- this is descriptive benchmark evidence, not a population-level statistical claim.

Additional frozen constraints:

- primary utterances are at most 12 seconds;
- the test set uses at least four distinct microphone/environment profiles;
- slow, conversational, and fast-but-intelligible cadence assignments are distributed across the test speakers and frozen before recording;
- speaker identifiers are pseudonymous;
- benchmark eligibility does not require collecting or publishing sensitive demographic attributes.

The counts do not authorize recording. Human consent, retention, redistribution, and withdrawal authority remain a B2 external gate.

## Canonical preprocessing

Preprocessing is pinned to FFmpeg `9.0.1`, upstream tag `n9.0.1`, annotated tag object `501bb49457b9dfb25d6a208832e0a6e6cd53108d`, source commit `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa`. The upstream annotated tag is signature-verified.

Attempt-time evidence must additionally record SHA-256 for the actual FFmpeg binary and normalized `ffmpeg -version` output. A source tag alone does not prove which binary executed.

Canonical conversion command:

```text
ffmpeg -nostdin -hide_banner -loglevel error -i INPUT -map_metadata -1 -vn -sn -dn -ac 1 -ar 16000 -c:a pcm_s16le -f s16le OUTPUT.s16le
```

Canonical representation:

- raw headerless PCM;
- mono;
- 16,000 Hz;
- signed 16-bit little-endian samples;
- no denoising;
- no loudness normalization;
- no semantic silence trimming;
- SHA-256 of every canonical output required.

Adapters convert each little-endian signed int16 sample to float32 using `sample / 32768.0` only. No candidate-specific gain, resampling, denoising, or cleanup is permitted.

The feed schedule is also frozen:

- 500 ms / 8,000 canonical samples per regular chunk;
- the final shorter speech chunk is preserved as-is;
- after the `speech_audio_end` marker, every candidate receives the same 660 ms / 10,560-sample zero suffix for deterministic finite-input finalization;
- timing evidence distinguishes `speech_audio_end` from `feed_end_after_zero_pad`.

The zero suffix is identical across candidates, contains no reference speech, and cannot be counted as human utterance duration.

## Common C0 posture

Every C0 cell uses:

- English;
- CPU-only execution;
- repository context OFF;
- test-specific context OFF;
- post-decode entity correction OFF;
- external language model OFF;
- candidate-specific audio transformation OFF;
- the canonical 500 ms feed schedule and 660 ms finalization suffix.

No backend-native prompt, keyterm, hotword, repository vocabulary, grammar, or post-hoc entity correction may enter C0.

## Moonshine C0

Pinned runtime: `moonshine-ai/moonshine@234f60faa0eb388b01cdf7e60aca232af37aefda` (`v0.1.5`).

Pinned source surfaces:

- `docs/api/options.md` at the pinned revision;
- `docs/api/classes.md` at the pinned revision.

Frozen settings:

- `ort_providers`: unset, selecting the documented CPU default;
- runtime model: the tier-selected `small-streaming-en` or `medium-streaming-en` payload;
- `max_tokens_per_second=6.5`;
- `use_speculative_decoding=true`;
- `keyterms=None` / OFF;
- `context=None` / OFF;
- `keyterm_boost=2.0` recorded but inert because keyterms are OFF;
- `context_max_terms=200` recorded but inert because context is OFF;
- `transcription_interval=0.5` seconds;
- `vad_threshold=0.0` to disable VAD decisions for pre-segmented C0;
- `vad_window_duration=0.5` seconds;
- `vad_hop_size=512` samples;
- `vad_look_behind_sample_count=8192`;
- `vad_max_segment_duration=15` seconds;
- primary utterances capped at 12 seconds so the 15-second forced segment boundary is not reached by reference speech;
- `word_timestamps=false`;
- `decode_incomplete_lines=true`;
- `identify_speakers=false`;
- `return_audio_data=true`;
- spelling model OFF;
- model-native punctuation only; no post-processing.

The pinned documented STT options surface does not expose a thread-count setting. The evidence therefore records `RUNTIME_DEFAULT_NO_DOCUMENTED_STT_THREAD_OPTION` rather than inventing one. This explicit asymmetry prevents uncontrolled C0 measurements from supporting a general CPU-efficiency claim.

Streaming semantics remain `DOCUMENTED_NOT_OBSERVED` until Wispral records raw behavior.

## whisper.cpp C0

Pinned runtime: `ggml-org/whisper.cpp@371b5a7561823ab2bb32142d2751e35e7534727b`, the source target of release `b4938`.

Pinned source surfaces:

- `examples/stream/README.md`;
- `examples/stream/stream.cpp`.

The research adapter reproduces the pinned non-VAD fixed-step `stream.cpp` decode semantics over canonical samples rather than depending on a physical microphone.

Frozen settings:

- `n_threads=4`;
- `step_ms=500`;
- `length_ms=5000`;
- `keep_ms=200`;
- `max_tokens=0`;
- `audio_ctx=0`;
- `beam_size=-1`, therefore greedy sampling in the pinned code path;
- temperature fallback OFF (`no_fallback=true`);
- language `en`;
- translation OFF;
- context carryover OFF (`no_context=true`);
- initial prompt OFF;
- VAD OFF because `step_ms > 0`;
- timestamps OFF in the non-VAD stream path;
- single-segment decode true for that path;
- GPU OFF;
- flash attention OFF;
- model-native punctuation only; no post-processing.

The pinned implementation re-decodes a bounded current/previous audio window. That is upstream documentation only; the expected class is recorded as `DOCUMENTED_NOT_OBSERVED_CHUNKED_REDECODE` until the exact Wispral integration is observed.

## sherpa-onnx C0

Pinned runtime: `k2-fsa/sherpa-onnx@917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e` (`v1.13.7`).

Pinned source surface: `python-api-examples/online-decode-files.py`.

The research adapter uses `OnlineRecognizer.from_transducer`, supplies the selected chunk-16/left-128 model, feeds canonical float32 samples in 500 ms chunks, decodes whenever the stream is ready, feeds the universal zero suffix, calls `input_finished`, and drains remaining ready states.

Frozen settings:

- `num_threads=4`;
- `provider="cpu"`;
- `sample_rate=16000`;
- `feature_dim=80`;
- `decoding_method="greedy_search"`;
- `max_active_paths=4` recorded but inactive under greedy search;
- LM OFF;
- LODR FST OFF;
- hotwords file OFF;
- modeling unit OFF;
- BPE vocabulary for hotwords OFF;
- `blank_penalty=0.0`;
- no endpoint-detection policy; the benchmark uses pre-segmented input and explicit `input_finished`;
- model-native punctuation only; no post-processing;
- raw timestamps/results are preserved where exposed but do not alter scoring.

Streaming semantics remain `DOCUMENTED_NOT_OBSERVED` until the exact candidate integration is observed.

## What remains deliberately unresolved

This freeze does not make B2 ready. Remaining gates include:

- attempt-time SHA-256 for every material Moonshine payload and sherpa `tokens.txt`;
- a bounded non-primary operational smoke or separately canonical waiver;
- human developer-speech consent/retention/redistribution authority and frozen manifests;
- exact scorer implementation/revision and config digest;
- exact preprocessing execution binary/config evidence in the future attempt;
- controlled performance environment if comparative performance claims are intended;
- final frozen B2 attempt manifest.

No primary test decoding, comparative ranking, production speech integration, or product support claim is authorized by this document.
