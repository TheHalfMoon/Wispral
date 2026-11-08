# Wispral model and speech strategy

**Status:** CANDIDATE PLAN. No model is selected, and no quality, latency or language claim is made. Every candidate below is something to *benchmark*. Full candidate matrices (14 modalities, code license versus weight license, Arabic claims, CPU feasibility, maintenance), the dataset table and the complete evaluation protocol are in the [models and Arabic research report](../../research/wispral-world-class/evidence/research-reports/MODELS_ARABIC_RESEARCH.md). Routing request and result contracts build on PR #124's [routing contracts](../strategy/WISPRAL_MODEL_ROUTING_CONTRACTS.md); the manifest is now an executable schema ([model_manifest.schema.json](contracts/model_manifest.schema.json)).

The frozen public-corpus B2 experiment (ATTEMPT-003, B2R17) is not modified, extended or re-scored here. New evaluation cells belong to new Grains.

## 1. Principles

1. **Replaceable providers behind one interface per modality** (STT, TTS, VAD/turn, diarization, enhancement, translation, alignment, LLM), each described by a capability manifest.
2. **License class is a hard filter.** Weight licenses decide more than code licenses. Non-commercial (NC), revenue-capped or unknown weights never enter a commercial route or default bundle. They may run only in a labelled research workspace with no customer data.
3. **No hidden cloud fallback and no automatic paid inference.** A failed local route returns `ProviderUnavailable` with the raw text or audio kept locally. Provider routes are off by default; enabling one is purpose-scoped and shows cost, with a budget cap; exhaustion stops the route instead of switching provider.
4. **No silent language downgrade.** A Gulf-Arabic request is never routed to an English-only or MSA-only model without telling the user the route is experimental or unavailable for that dialect.
5. **Routes are pinned per workspace, project or tenant.** A route never changes mid-session, mid-render or on resume.
6. **No training in this plan.** Fine-tuning or a Wispral-owned model is proposed only when the measurable triggers in §7 fire.
7. **No model authorizes anything** (`authority_ceiling: evidence_only` in every manifest).

## 2. Device tiers

| Tier | Definition | Planning budget (replaced by measured RSS) |
| --- | --- | --- |
| **R0 (reference cell)** | Founder laptop: i5-13420H, 16 GB, Intel UHD integrated graphics, no discrete GPU, Windows 11 | As T1. GPU-class candidates are `BLOCKED_EXTERNAL` here and are never extrapolated from R0 |
| T0 | CPU-only, 8 GB | All resident models ≤ ~2.5 GB RSS; rewrite LLM off by default |
| T1 | CPU-only, 16 GB | ≤ ~6 GB resident |
| T2 | Apple Silicon ≥ 16 GB | Measured separately |
| T3 | Discrete GPU ≥ 8 GB VRAM | VRAM-resident; CPU fallback only as an explicit route |
| T4 | Server GPU (self-hosted Klaint/Studio) | Per deployment |

## 3. Selection algorithm

```text
eligible = candidates where
    task ∈ manifest.modality
  ∧ license class allowed for (product, distribution mode)      # NC / UNKNOWN never commercial; revenue-capped excluded by default
  ∧ privacy mode permits manifest network requirements          # offline-only ⇒ no network at inference
  ∧ device tier satisfies MEASURED requirements on that tier     # never publisher claims
  ∧ language stratum is QUALIFIED (GA) or SCREENED (user-enabled "experimental")
  ∧ consent prerequisites met (cloning: consent for this exact reference and purpose)
  ∧ (not paid) or (user-approved, cost shown, budget capped)
if eligible = ∅ → ProviderUnavailable(reason codes, user actions)   # never a silent fallback
route = preregistered product decision function(eligible); pin it; log every change
```

| Product / task | Must pass | Then minimize | Tie-breakers |
| --- | --- | --- | --- |
| WisprSide dictation | Latency budget and RSS within tier | Critical semantic error rate in the user's declared dialect | WER → entity accuracy → RSS → disk |
| WisprSide rewrite | Never changes meaning; preserves code-switch script; raw retained | Manual-correction rate | Latency → RSS |
| Studio TTS | Permissive weights; language cell qualified | Critical pronunciation error rate | MOS → dialect authenticity → RTF |
| Studio cloning | Valid consent; license allows cloning; watermark policy satisfied | Speaker-similarity shortfall (with intelligibility gate) | MOS → RTF |
| Klaint streaming ASR | Telephony/8 kHz cell qualified for the tenant's dialects | Critical semantic errors (account numbers, dates, amounts) | WER → self-hosted cost |
| Klaint LLM | Tool-call schema validity ≥ gate; broker blocks every unauthorized attempt | Task failure on frozen synthetic scenarios in the tenant's language | Arabic register appropriateness → latency → cost |

## 4. Initial candidates to benchmark (not selections)

Selection reasons: permissive weights; a documented Arabic or English role; a CPU path or a reason to measure feasibility; maintenance; architectural diversity.

| Product / task | R0 candidates | GPU-cell reference (blocked on R0) | Notes |
| --- | --- | --- | --- |
| WisprSide Arabic streaming STT | Moonshine Arabic Tiny Streaming (MIT, 34M); Qwen3-ASR-0.6B (Apache-2.0); Voxtral-Mini-4B-Realtime-Arabic community ONNX (Apache-2.0; likely too heavy — record infeasible rather than drop) | — | Voxtral Realtime Arabic is the only open streaming model with explicit Saudi/Gulf tags |
| WisprSide Arabic push-to-talk STT | whisper large-v3-turbo via whisper.cpp (MIT); Omnilingual CTC 300M/1B v2 (Apache-2.0); NVIDIA Arabic FastConformer (CC-BY-4.0); Fun-ASR-MLT-Nano (Apache-2.0); Handy catalog's `cohere-transcribe-arabic-07-2026` (gated; license per catalog Apache-2.0) | Jais-ASR (Apache-2.0; leaderboard leader, 22.82 avg WER *per the leaderboard's own normalizer*) | Whisper risks translating dialect into MSA |
| English STT | Frozen B2 cells untouched; a new Grain may add Parakeet-TDT (CC-BY-4.0) and whisper large-v3-turbo | — | |
| VAD / turn | Silero VAD (MIT); smart-turn v3.2 (BSD-2; Arabic listed) | — | TEN VAD excluded (non-compete clause) |
| Rewrite LLM | Qwen3.5-4B, Gemma 4 E4B (terms to read), Jais-3-3.7B, Ministral-3-3B, Phi-4-mini, Granite-4.2-3B at 4-bit | — | Meaning preservation first; **p95 rewrite latency on HW-A is a must-pass gate**, not a tie-breaker. Runs as a llama.cpp-compatible server under WisprSide's engine supervisor with a manifest row, or as a user-owned external server that is labelled and excluded from offline claims |
| Studio Arabic TTS | **First:** VoiceStudio's built-in VoxCPM2 and MOSS-TTS-Nano (Apache-2.0 per VoiceStudio's licence records; official cards to verify; MOSS-TTS-Nano is CPU-oriented). **Then, only if they fail:** Chatterbox Multilingual V3 (MIT; retired upstream Aug 2026; needs a third Python environment and a pinned Perth); `silma-ai/silma-tts` (Apache-2.0 per card; lineage unverified); Piper Arabic voices (per-voice licence unverified; GPL runtime isolated) | Same on GPU | Commercially plausible Arabic TTS is thin; dialect authenticity unknown |
| Studio English TTS | Kokoro-82M (Apache-2.0); Chatterbox Turbo/Nano (MIT); VibeVoice-Realtime-0.5B (MIT); Qwen3-TTS-0.6B (Apache-2.0) | — | Replaces the non-commercial OmniVoice default |
| Studio cloning | Chatterbox Multilingual (Arabic + English); Qwen3-TTS Base, CosyVoice 3 (non-Arabic) | — | Consent per reference artifact |
| Studio voice design | Qwen3-TTS VoiceDesign (non-Arabic) | — | **No permissive Arabic voice-design model exists** (gap FT-5) |
| Studio diarization / enhancement | Sortformer streaming v2 (CC-BY-4.0); pyannote community-1 (gated); RNNoise (BSD-3) | — | DiariZen rejected (NC) |
| Klaint agent LLM | Jais-3-7B, Qwen3.5-9B, Granite-4.2-8B, ALLaM-7B, Fanar-1-9B at Q4 (text-only experiments) | Qwen3.5/3.6-35B-A3B, Gemma 4 26B/31B, Fanar-2-27B, Jais-3-32B, gpt-oss-20b, Mistral Small 4 | Arabic tool-use reliability unmeasured everywhere; tenant may configure a provider explicitly |

**Licenses still to read before any trial:** Gemma 4 terms, LiveKit turn model, TEN Turn Detection, IndexTTS-2, Higgs, Piper and Moonshine Arabic voice assets, `lfm1.0`, Falcon, Llama, Qwen community variants, AudioSeal weights. **Gated models** (pyannote, Cohere transcribe, Pocket TTS) need the founder to accept their terms; agents never accept terms on the founder's behalf.

## 5. Arabic evaluation data

| Source class | Examples | Usable for commercial-product evaluation? |
| --- | --- | --- |
| Permissive, mostly read speech | Common Voice (ar), FLEURS (ar), ClArTTS, DVoice, TunSwitch, Omnilingual ASR corpus | Yes, within each license; weak on spontaneous dialect speech |
| Non-commercial or research-only | Casablanca/NADI, SADA (Saudi), MGB-2/3/5, QASR, ESCWA, Mixat (code-switch), SCC, MenaSpeechBank | **No** for product claims; may inform research only where terms allow |
| Paid | LDC telephony corpora (for-profit membership) | Founder purchase decision; not assumed |
| **Wispral consented panel** | Volunteer speakers across the WB-AR strata, written consent (purpose, retention, withdrawal), held-out splits never used for tuning | **Required** before any Arabic dialect claim |

Normalization differs across benchmarks (ta marbuta, alef maqsura, hamza, attached و), so cross-benchmark WERs are not comparable. Whisper's default normalizer turns Arabic diacritics into spaces and splits words (`SOURCE_VERIFIED` in the report). Wispral preregisters a four-level Arabic normalizer and always reports raw and normalized scores ([WB-AR](WISPRAL_BENCHMARKS.md#wb-ar--arabic-and-english-language-quality)).

## 6. Klaint LLM boundary

The LLM never authorizes spending, refunds, payments, credential use, account-ownership changes, cross-tenant access, data export or deletion, outbound contact to new destinations, or any irreversible action. It emits a structured proposal; the deterministic broker validates tenant binding (from the authenticated session only), tool allowlist, argument schema, idempotency key, rate and spend caps, and authorization freshness, and routes high-risk actions to explicit human or verified-customer confirmation. Model confidence, eager end-of-turn events and "the customer said yes" in a transcript are never authorization. Evaluation adapts BFCL-style tool-call categories, tau2-bench pass^k and When2Call-style abstention, with a Wispral-authored, native-reviewed Arabic scenario set (machine-translated scenarios are not acceptable as Arabic evidence).

## 7. When a Wispral-owned model becomes justified

Preconditions (all required): a frozen, consented held-out set for the affected stratum; every cheap mitigation measured (forced language, VAD tuning, context biasing, user vocabulary, constrained post-correction, the largest model that fits the tier); and rights that permit fine-tuning and commercial distribution, with separate commercial-training consent for the data.

| Trigger | Condition (planning values for founder approval) |
| --- | --- |
| FT-1 Dialect gap | Stratum WER above its release gate *and* ≥ 10 points worse than MSA (CI lower bound ≥ 5) after mitigations |
| FT-2 Meaning-distortion gap | ASR-attributable critical semantic errors > 2% (CI lower bound > 1%) or > 2× the English rate |
| FT-3 Code-switch gap | Code-switch WER ≥ 8 points above the same speakers' monolingual Arabic, or script fidelity < 90% |
| FT-4 Device-tier gap | Every model that passes quality exceeds the T0 budget by ≥ 2× or misses latency |
| FT-5 License gap | Only NC or revenue-capped weights reach the gate for a required capability (today: Arabic voice design and dialect TTS) |
| FT-6 Domain vocabulary gap | Entity accuracy < 90% after biasing, with a consented in-domain corpus available |

A fine-tune is accepted only with an improvement whose confidence interval excludes zero and a preregistered non-inferiority check on other strata. Stop rule: if a dev-split pilot does not close at least half the target gap, do not proceed.
