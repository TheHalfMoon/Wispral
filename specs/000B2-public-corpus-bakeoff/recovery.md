# Specification 000B2 Recovery — ATTEMPT-001 Material Execution Drift

## Authority

This recovery is activated by the existing 000B2 recovery rule: material drift after attempt freeze invalidates that attempt, preserves its history, and requires a new pinned attempt. It does not amend candidate membership, public subset membership, scoring, normalization, or the frozen C0 contract.

The triggering evidence is recorded in `research/000b2-public/attempt-001-invalidation.json` and verified by `research/000b2-public/verify_attempt_001_invalidation.py`.

## Finding

`000B2-PUBLIC-ATTEMPT-001` froze the Moonshine family to the pinned streaming integration with:

- 500 ms / 8,000-sample feed chunks;
- a universal 660 ms / 10,560-sample final zero suffix;
- `vad_threshold=0.0`;
- `transcription_interval_seconds=0.5`;
- repository/test-specific context OFF.

The canonical B2E01 and B2E02 decoders instead called `Transcriber.transcribe_without_streaming(audio)` for each complete utterance. At pinned Moonshine revision `234f60faa0eb388b01cdf7e60aca232af37aefda`, that API processes the supplied full audio through its batch-stream VAD path and stops the stream; it does not implement the frozen public incremental feed schedule. The same pinned runtime defaults `vad_threshold` to `0.5`, and neither canonical decoder overrode that value.

These are material execution differences from the frozen C0 configuration. They are not factual-typo corrections.

## ATTEMPT-001 disposition

Preserve ATTEMPT-001 exactly as historical evidence of what ran.

Do not:

- rewrite `attempt-manifest.json` to pretend the executed configuration matched the freeze;
- rewrite B2E01/B2E02 raw evidence or provenance bytes;
- score ATTEMPT-001 as the canonical six-cell comparison;
- use ATTEMPT-001 to support candidate superiority, shortlist, or production-selection claims;
- continue B2E03 or later cells under ATTEMPT-001;
- repair the Moonshine harness and reuse ATTEMPT-001 after primary outputs were already exposed.

The cancelled B2E03 discovery run `33972588550` is not primary evidence. Halt run `33973416932` records the intentional stop.

## Recovery order

Recovery is dependency ordered and fail closed:

1. `B2R01` — canonically qualify the ATTEMPT-001 invalidation and keep all new primary decoding closed.
2. `B2R02` — implement and qualify a corrected Moonshine streaming C0 harness against non-primary material and pinned upstream source. It must demonstrate the exact 500 ms feed schedule, final 660 ms zero suffix, `vad_threshold=0.0`, unchanged context/keyterm guards, and frozen runtime/model identities without inspecting new primary results.
3. `B2R03` — establish ATTEMPT-002-bound preprocessing and execution-environment evidence. Reuse of unchanged frozen inputs is allowed only by exact digest/provenance rebinding or fresh capture before primary decode; no result-driven input change is allowed.
4. `B2R04` — freeze `000B2-PUBLIC-ATTEMPT-002` before any new primary decode. Candidate membership, subset membership, scorer, normalization, and C0 methodology remain unchanged except for correcting the implementation so it actually matches the already-frozen contract.
5. `B2R05` through `B2R10` — execute all six candidate cells from cell 1 under ATTEMPT-002 in the original frozen order.
6. `B2R11` — preserve all ATTEMPT-002 raw transcripts, failures, runtime observations, and exact run identities.
7. `B2R12` — score ATTEMPT-002 only under the already-frozen scoring/normalization contract.

Only after B2R12 is canonical may the existing D0/synthesis closeout sequence continue, subject to a fresh canonical reread.

## Non-claims

Recovery does not establish human developer-speech accuracy, candidate superiority, production STT selection, product-code authority, controlled performance evidence, or any result for the unfinished six-cell comparison.

`HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT` remains mandatory.
