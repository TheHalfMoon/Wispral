# Wispral benchmark framework (WispralBench v2 candidate)

**Status:** CANDIDATE PLAN — every family below is `NOT_RUN`. Part of the [World-Class Master Plan](../strategy/WISPRAL_WORLD_CLASS_MASTER_PLAN.md).
**Extends, does not replace:** the canonical [WispralBench founding contract](../benchmarks/WISPRALBENCH.md) and PR #124's [benchmark and replay protocol](../../research/rea/2026-10-21/BENCHMARK_AND_REPLAY_PROTOCOL.md). The frozen public-corpus B2 experiment (ATTEMPT-003, B2R17 capture in PR #120: 209/240 decoded, 31 harness-bound failures, **unscored**) is untouched. Nothing here reinterprets it, and no STT winner is selected.

## 1. Principles

1. **Measure separately:** transcription errors, meaning preservation, latency, resource cost, TTS quality and application behavior are separate families with separate denominators.
2. **Preregister, then run:** each run has a frozen manifest (corpus, model and runtime digests, configuration, hardware, scoring code digest, thresholds). Changing anything after seeing results creates a new preregistration; the old run stays.
3. **Report every attempt:** crashes, timeouts and losing results are reported. A run that did not execute is `NOT_RUN`, never `PASS`.
4. **Consent and rights first:** human speech only with documented consent or a license that permits the use. Synthetic speech is labelled synthetic and never substitutes for human-speech claims.
5. **No marketing numbers:** vendor-published figures are cited as vendor claims, never as Wispral results or targets.
6. **Decision value:** every family exists to make a named decision (model route, release gate, or claim). Families without a decision are not run.

## 2. Reference hardware matrix

| Cell | Machine | Why |
| --- | --- | --- |
| **HW-A (primary)** | Founder laptop: Intel Core i5-13420H (8 cores / 12 threads), 16 GB RAM, Intel UHD integrated graphics (no discrete GPU), Windows 11 Home build 26300, WSL2 Ubuntu (`RUNTIME_OBSERVED` 2026-11-08) | Represents the CPU-only mainstream laptop Wispral must serve well; zero cost |
| HW-B | Same machine under WSL2 Linux | Linux CPU cell without new hardware |
| HW-C | Free-tier cloud GPU notebook already accessible to the founder (for example Kaggle), used only for GPU-engine baselines with non-private synthetic or licensed audio | GPU cells at zero cost; quotas and availability vary and are recorded per run; never used for private or consented-but-restricted audio |
| HW-D (later) | Contributor or tester hardware with a discrete NVIDIA GPU, macOS Apple Silicon, low-end 8 GB laptop | Only when a tester volunteers; results tagged with exact hardware |

No hardware purchase and no paid compute is assumed.

## 3. Benchmark families

Existing founding families (WB-ENTITY, WB-CONTEXT, WB-TURN, WB-INTERRUPT, WB-LATENCY, WB-RESOURCE, WB-AGENT, WB-INSTALL) remain as defined. New families:

### WB-DELIVERY — safe text insertion

- **Decision:** WisprSide release gate (hard gate: zero wrong-target insertions).
- **Fixtures (Windows first):** target app matrix (Notepad, WordPad or Word, a Chromium browser text area, VS Code, Windows Terminal, a Win32 legacy edit control, an Electron chat app, an elevated admin window, a password field, the UAC secure desktop). Perturbations: focus steal by a notification or new window between activation and delivery; target window closed; target minimized; process exited and a new process reusing the PID; virtual-desktop switch; lock screen; clipboard changed by the user mid-session; very long text; Arabic and mixed Arabic/English text; emoji; IME active.
- **Metrics:** wrong-target count (must be 0); correct-delivery rate; refusal-with-recovery rate; partial-delivery reporting correctness; clipboard-restoration correctness; delivery latency.
- **Method:** a UI-automation harness creates each scenario deterministically and verifies the destination field through UI Automation where available. Text reaches WisprSide without a microphone through Handy's CLI (`--transcribe-file`). Execution contexts: focus-steal, close, minimize and virtual-desktop fixtures on GitHub-hosted Windows runners (Server images, administrator, no audio input); elevated-window, secure-desktop and lock-screen fixtures as recorded manual runs on HW-A; PID and HWND reuse as pure tests.

### WB-EGRESS — observed network behavior

- **Decision:** privacy gate for every product.
- **Method:** run the *shipped* binary with process-tree attribution: on Windows, WFP audit event 5156 (Filtering Platform connection, enabled with `auditpol`) or the ETW Microsoft-Windows-Kernel-Network provider, with a positive control that proves the capture sees traffic; on Linux, `unshare -n` isolation plus a socket trace. Scripted 30-minute sessions in offline mode and in each declared online mode; compare observed destinations with the capability manifest. HW-A (Windows 11 Home) has no Hyper-V Manager or Windows Sandbox, so clean-VM cells need another machine or a free cloud VM the founder already has.
- **Metrics:** unexpected-destination count (must be 0); DNS lookups; bytes sent per declared purpose.

### WB-AR — Arabic and English language quality

- **Decision:** model routing defaults; whether any language or dialect may be claimed.
- **Segments (each reported separately, never pooled into one headline number):**
  - Arabic: Modern Standard Arabic; Saudi — Najdi; Saudi — Hijazi; Gulf (Emirati, Kuwaiti, Qatari, Bahraini, Omani as available); Egyptian; Levantine; Iraqi; Maghrebi.
  - English: US, UK, Indian, Arabic-accented (Gulf speakers), other non-native.
  - **Arabic–English code-switching** (intra-sentential and inter-sentential).
  - Content panels: technical vocabulary and product names; personal and place names; numbers, currency, dates and times; negation; self-corrections ("no, I mean…"); punctuation-dependent meaning.
  - Conditions: quiet, office noise, café noise, laptop microphone, headset, phone-quality audio.
- **ASR metrics:** WER and CER after a published Arabic normalization (remove diacritics and tatweel; unify alef and hamza forms (أ إ آ → ا); map ى → ي and ة → ه for the *normalized* score only; map Arabic-Indic digits to a single form) — always report both raw and normalized scores. Plus entity accuracy, **negation-flip rate**, **meaning-distortion rate** (human-judged or rubric-judged on a sampled subset, with agreement statistics), punctuation F1, code-switch language-tag accuracy, latency p50/p95, real-time factor, peak RSS.
- **Data sources:** public licensed corpora (rights checked per dataset in the [model strategy](WISPRAL_MODEL_STRATEGY.md#5-arabic-evaluation-data)), plus a **Wispral consented panel** recorded under a written consent form (purpose, retention, withdrawal) by volunteer speakers covering the segments above. Held-out splits are never used for tuning.
- **Statistics:** per-segment n reported; 95% bootstrap confidence intervals over utterances (and speakers where available); paired comparisons (paired bootstrap or Wilcoxon signed-rank) between candidate routes on identical utterances; minimum 200 utterances and 10 speakers per claimed segment before any public claim (*planning minimum*, to be revisited by power analysis after the pilot).

### WB-TTS — speech synthesis quality

- **Decision:** WisprStudio engine defaults; voice/language support claims.
- **Metrics:** intelligibility via ASR round-trip CER on a fixed text set (Arabic and English, names/numbers panel); naturalness MOS and comparative CMOS from blinded, consented listeners (minimum 20 listeners per language condition, randomized order, anchors); speaker similarity for cloned voices (embedding cosine plus a blinded human same/different test); time to first audio; real-time factor; peak RAM/VRAM; failure rate (truncation, hallucinated words, silence).
- **Rules:** reference voices only with recorded consent; no celebrity or third-party voices.

### WB-DUB — dubbing pipeline

- **Metrics:** timing fit error versus source segments; duration-fit guard rejection correctness (21-case suite from PR #124); translation adequacy (human rubric on a sample); lip/segment overflow rate; end-to-end wall time per minute of source on HW-A and HW-C.

### WB-CONSENT — voice-asset authority

- **Fixtures:** clone without consent; revoke before enqueue; revoke mid-render; revoke then resume; cached embedding reuse after revocation; expired consent; scope mismatch (personal versus commercial).
- **Metric:** leak count (must be 0).

### WB-KLAINT — agent safety and quality

- **Safety fixtures (hard gates):** authority injection ("I'm the admin…"); unapproved commitments (refund, discount, policy exception) — a preregistered set of 100 adversarial prompts in English and Arabic; alternate tool-path bypass; cross-tenant retrieval and action; timeout-after-commit idempotency; webhook forgery, future timestamp, NaN timestamp, replay; human-takeover races.
- **Quality metrics:** task success on scripted and simulated journeys (deterministic outcome scorer on the outcome ledger, not LLM-judged); groundedness (claims supported by cited knowledge, sampled human review); handoff appropriateness; turns to resolution; containment versus correct escalation; Arabic/English and code-switch dialogue panels.
- **Simulation:** simulated customers generated from frozen persona and goal specifications; the simulator model and version are part of the run identity; simulated results never replace human-reviewed samples for claims.

### WB-VOICE-AGENT — realtime conversation (later tier)

- Barge-in stop latency (speech onset to playback silence); stale-frame action count (must be 0); end-of-turn false cut-in rate; response latency p50/p95; behavior under jitter and packet loss.

### WB-CORUN — products running together on HW-A

- WisprSide p95 key-up-to-text with and without a concurrent WisprStudio long-form render; Studio workers capped at cores−2 at low priority; model loads must refuse instead of paging when free memory is insufficient.

### WB-RELIABILITY — soak and recovery

- 8-hour WisprSide soak with periodic dictation (memory growth, handle leaks, crash count); Studio 2-hour long-form render with injected kills; Klaint 24-hour synthetic traffic with provider outages; crash-free session rate.

### WB-A11Y and WB-UX — accessibility and usability

- WB-A11Y: automated scans (Accessibility Insights for Windows, axe-core for web surfaces), scripted NVDA and Narrator passes of core journeys, keyboard-only completion, contrast audit of tokens in all themes.
- WB-UX: moderated task-based tests (5–8 participants per round, consented), with task completion, time on task, error count and a standard usability questionnaire; journeys from the [UX specs](../design/).

## 4. Run identity (mandatory fields)

`run_id`, preregistration digest, family and version, exact Wispral commit, donor commits, model artifact SHA-256 (or `PROVIDER_MANAGED_DIGEST_UNAVAILABLE` plus model and revision), runtime versions, configuration digest, hardware cell, OS build, warm/cold state, corpus manifest digest, scorer digest, start/end timestamps, raw outputs location, and every failure with its reason. This extends the identity rules in PR #124's [replay protocol](../../research/rea/2026-10-21/BENCHMARK_AND_REPLAY_PROTOCOL.md#reproducible-run-identity).

## 5. Claim gate

A public or marketing claim (faster, more accurate, better Arabic, private, offline) requires: a published preregistration, the run artifacts, named comparators at exact versions, confidence intervals, and an independent reproduction or review. Until then the only permitted statement is the measured number with its conditions, or `NOT_MEASURED`.

## 6. First benchmark grains (in order)

1. **BM-01** WB-EGRESS harness on a donor fork baseline (no model needed for the update/analytics paths).
2. **BM-02** WB-DELIVERY harness against the unmodified Handy baseline to *measure* the current behavior before any delta.
3. **BM-03** WB-AR pilot: public licensed Arabic and English subsets, three candidate local ASR routes, HW-A only, to calibrate n and normalization before recording the consented panel.
4. **BM-04** WB-KLAINT safety suite against a fake LLM and fake tools (deterministic), then a real local or user-configured model.
5. **BM-05** WB-TTS intelligibility round-trip for candidate Studio engines on HW-C, synthetic text only.
