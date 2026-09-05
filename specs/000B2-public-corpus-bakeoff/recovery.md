# Specification 000B2 Recovery — ATTEMPT-001 Material Execution Drift

## Authority

This recovery is activated by the existing 000B2 recovery rule: material drift after attempt freeze invalidates that attempt, preserves its history, and requires a new pinned attempt. It does not amend candidate membership, public subset membership, scoring, normalization, or the frozen C0 contract.

The triggering evidence is recorded in `research/000b2-public/attempt-001-invalidation.json` and verified by `research/000b2-public/verify_attempt_001_invalidation.py`.

### Transitional authority precedence

`research/000b2-public/readiness.json` is preserved byte-for-byte as the historical ATTEMPT-001 post-B2E02 readiness snapshot because historical evidence verifiers bind it. Once this recovery is canonical, it MUST NOT be treated as authority for new execution.

`research/000b2-public/recovery-readiness.json` is the active machine-readable authority for new 000B2 execution during recovery. Its `authority_precedence=OVERRIDES_ATTEMPT_001_READY_SNAPSHOT_FOR_NEW_EXECUTION` field therefore closes B2E03 and every later ATTEMPT-001 primary decode even while the historical readiness snapshot still names B2E03. Canonical reconciliation after B2R01 must update `specs/CURRENT.md` and `docs/canonical/CURRENT_STATE.md` before B2R02 work begins.

No recovery unit may use this transitional precedence to skip its predecessor. The recovery verifier requires a contiguous completed B2R prefix and binds the active recovery unit to the first pending task.

### Canonical recovery transition proof

Beginning with the B2R01-to-B2R02 transition, a checked recovery task is not sufficient successor authority by itself. Every completed recovery unit must append exactly one ordered entry to `recovery-readiness.json.transition_proofs` containing:

- `completed_task` — the just-completed B2R unit;
- `canonical_task_merge` — the exact merge commit for that unit, which must already be an ancestor of canonical `main`;
- `post_merge_recovery_run_id` — a successful `push` run of `000B2 Public Corpus Attempt Recovery` whose `head_sha` is exactly that canonical task merge;
- `successor_task` — the next B2R unit, or `null` only after B2R12.

The recovery workflow independently queries GitHub Actions and validates the recorded post-merge run identity, event, conclusion, workflow name, and exact head SHA. A run id written into repository evidence is not trusted by itself.

For every transition, both `specs/CURRENT.md` and `docs/canonical/CURRENT_STATE.md` must contain these exact authority markers for the latest completed unit:

```text
**Canonical recovery predecessor:** `B2Rxx`
**Canonical B2Rxx recovery merge:** `<40-hex canonical merge>`
**Canonical B2Rxx post-merge recovery run:** `<run id>`
**Active recovery unit:** `B2Ryy`
```

Use `NONE` for the active unit only after B2R12 is reconciled.

A PR that advances recovery authority beyond what canonical `main` already records is a reconciliation candidate, not an execution PR. It may advance exactly one recovery task and may change only:

- `research/000b2-public/recovery-readiness.json`;
- `specs/000B2-public-corpus-bakeoff/tasks.md`;
- `specs/CURRENT.md`;
- `docs/canonical/CURRENT_STATE.md`.

The verifier compares the candidate against `origin/main`. It rejects skipped recovery tasks, non-main task-merge identities, altered prior transition proofs, and any reconciliation candidate mixed with implementation or evidence-generation paths. Once the reconciliation is merged, successor implementation PRs are accepted only when their inherited recovery state and transition-proof ledger already match canonical `main`.

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

1. `B2R01` — canonically qualify the ATTEMPT-001 invalidation and keep all new ATTEMPT-001 primary decoding closed.
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
