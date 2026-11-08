# Wispral model strategy and Arabic/English language quality

Date: 2026-11-08. **Research only.** No model, dataset or weight was downloaded. No gated terms were accepted, no account was signed into, nothing was bought, and no benchmark or decode was run. Every quality number below is a publisher, paper or leaderboard claim, cited and dated. None of them is a Wispral measurement.

Products: **WisprSide** (dictation), **WisprStudio** (TTS, dubbing, consented cloning), **Klaint** (customer voice and chat agents).

## Evidence tags

| Tag | Meaning |
| --- | --- |
| `DOCUMENTED` | Read from a primary page on 2026-11-08: a model card, repo README or LICENSE, dataset card, paper or leaderboard source. Hugging Face card metadata was read from `https://huggingface.co/api/models/<id>` and is shown with the first 8 hex digits of the card revision. Full SHAs are in `workers/hf_model_meta.tsv` and `workers/hf_newcomers_meta.tsv`. |
| `SOURCE_VERIFIED` | Read from a pinned GitHub tree as `owner/repo@sha:path`. |
| `NOT_RUN` | Nothing was executed. Applies to every CPU feasibility, latency and quality statement about Wispral. |
| `BLOCKED_EXTERNAL` | Needs hardware, an account, gated-term acceptance or data that this mission does not have. |
| `REJECTED` | Excluded from commercial routes, with the reason given. |
| `NOT_VERIFIED` | Not confirmed from a primary source in this session, either because the research workers were stopped by a usage limit or because no primary statement was found. Treat it as unknown. It is not a negative finding. |

"CPU feasibility" is **inferred** from parameter count, file size and runtime unless it says otherwise. It is always `NOT_RUN` for Wispral.

## 0. Executive summary

1. **Weight licenses matter more than code licenses.** Many permissive repos ship non-commercial weights:
   - F5-TTS: CC-BY-NC-4.0.
   - XTTS-v2: CPML.
   - Fish-Speech 1.5: CC-BY-NC-SA-4.0.
   - Voxtral-4B-TTS: CC-BY-NC-4.0.
   - MMS and Seamless: CC-BY-NC-4.0.
   - DiariZen: CC-BY-NC-4.0.
   - granite-speech-5.0-470m-turboctc-nc: CC-BY-NC-SA-4.0.

   Some code repos also carry non-standard conditions:
   - TEN VAD is Apache-2.0 plus an Agora non-compete clause.
   - Moonshine's legacy non-English models are under a community license that terminates above US$1M annual revenue.
   - LFM models use `lfm1.0`.

   The routing policy (Section 6) treats license class as a hard filter.
2. **Arabic ASR changed a lot in 2026.** New Arabic-specific open-weight models, all Apache-2.0 per their cards:
   - `IFM/Jais-ASR` (2026-10): based on Jais-3-4B, 19 dialects, code-switching, built-in dialect ID.
   - `mistralai/Voxtral-Mini-4B-Realtime-Arabic` (2026-10): streaming, about 4.4B parameters, dialect-tagged.
   - `CohereLabs/cohere-transcribe-arabic-07-2026`: gated.
   - Qwen3-ASR 0.6B/1.7B (2026-01): Arabic listed.
   - Meta Omnilingual ASR (2025-11): per-dialect CERs published.
   - Moonshine **Arabic Tiny Streaming** (34M parameters, MIT).

   On the Open Universal Arabic ASR Leaderboard (`app.py`, last update entry 2026-10-19), Jais-ASR has the lowest average WER at 22.82. whisper-large-v3 averages 36.86. These are leaderboard claims, scored with the leaderboard's own normalizer.
3. **Dialect gaps are large and consistent across independent sources.** Every source ranks the varieties the same way:
   - MSA does best.
   - Levantine, Egyptian and Gulf are worse, with Najdi and Hijazi notably bad in some sets.
   - Iraqi is worse again.
   - Maghrebi is worst.

   Code-switching is a major failure mode for off-the-shelf models: Whisper-medium was reported at above 100% WER on Mixat code-switched segments. All of these are paper or publisher claims. Most dialect benchmarks are NC or research-only, so **a consented, commercially licensed Wispral held-out set is required** (Sections 4 and 5).
4. **Commercially usable open Arabic TTS is thin.**
   - Chatterbox Multilingual V3 is MIT and lists Arabic, but its README says it has been retired and unmaintained since August 2026.
   - `silma-ai/silma-tts` is Apache-2.0 per card metadata; its lineage is NOT_VERIFIED.
   - Piper Arabic voices: license per voice is NOT_VERIFIED.
   - Qwen3-TTS, CosyVoice 2/3 and Kokoro do **not** list Arabic.
   - The strongest Arabic-capable open TTS weights are NC: Fish-Speech, Voxtral TTS, XTTS-v2, MMS-TTS, and OmniVoice per the earlier register.

   Arabic voice design has no verified commercially licensed open option. This is the clearest candidate for a future fine-tuning trigger (FT-5).
5. **Reference machine R0** (i5-13420H, 16 GB, no dGPU) can host only the small streaming and CTC ASR cells, Silero and smart-turn, small TTS, and 2–4B rewrite LLMs at 4-bit. Jais-ASR (11.4 GB bf16), Voxtral Realtime Arabic (4.4B), Qwen3-Omni and agent-class LLMs are `BLOCKED_EXTERNAL` on R0 until a GPU cell exists. The Voxtral model also has a community ONNX/WebGPU export whose CPU real-time factor is unknown.
6. **Klaint's LLM never authorizes actions.** Candidate open agent models with Apache-2.0 weights and documented tool calling include:
   - Qwen3.5 / 3.6
   - Gemma 4
   - Jais 3
   - Fanar-2-27B
   - Ministral 3 / Mistral Small 4
   - Granite 4.2
   - gpt-oss-20b

   A deterministic broker owns authority (Section 8).

## 1. Inputs read and authority boundaries

Wispral clone at `main@edacdf7504302cc91ff7138bc6ac2d391e4df1f4` and `pr124@e7064c785ac4cf8a667526fa20feb0734f8afe45`. Files read:

- `docs/benchmarks/WISPRALBENCH.md`
- `docs/research/stt/000b1-qualification-report.md`
- `research/000b1/qualified-candidates.json`
- `docs/research/stt/000b-refinement-inputs.md`
- `pr124:research/rea/2026-10-21/BENCHMARK_AND_REPLAY_PROTOCOL.md`
- `pr124:docs/strategy/WISPRAL_MODEL_ROUTING_CONTRACTS.md`
- `pr124:research/rea/2026-10-21/RIGHTS_AND_ATTRIBUTION_REGISTER.md`
- The model-card table in `pr124:research/rea/2026-10-21/WISPRSTUDIO_DEEP_DIVE.md`

Boundaries kept:

- **Frozen B2 is untouched.** Its six preregistered English cells stay as they are:
  - Moonshine `small-streaming-en` and `medium-streaming-en` at `quantized_26_08_21`, runtime v0.1.5 `234f60fa`.
  - whisper.cpp `ggml-base.en` and `ggml-small.en`, release b4938.
  - sherpa-onnx Zipformer chunk-16/left-128 INT8 and FP32, v1.13.7.

  The B2R17 state (209/240 decoded, unscored) is not reinterpreted, re-scored or compared with anything here. Newer Moonshine assets at `moonshine-ai/moonshine@d8d8fa29` (current head), including Arabic Tiny Streaming, are **outside** the B2 identities. Consistent with `000b-refinement-inputs.md`, they do not establish Wispral Arabic support.
- Routing follows the pr124 routing contract: one modality interface, one selected provider per request, no unapproved network or paid fallback, and model confidence never becomes action authority.
- Model-card licenses are card terms. This document does not inspect training-data legality and grants no personal voice rights (see the rights register).

## 2. Candidate matrices per modality

Column key: **Code lic.** is the license of the inference repo; **Weights** is the license of the checkpoint and whether commercial use is allowed; **Arabic** is the documented claim. "R0" is CPU feasibility on the reference laptop, inferred and NOT_RUN. "Maint." is the last push to the GitHub repo, from `gh api` on 2026-11-08.

### 2.1 ASR: streaming-capable (dictation, live agent)

| Candidate (id, card rev) | Code lic. | Weights / commercial | Arabic (source) | Size | R0 CPU (inferred) | Streaming (documented) | Runtime | Maint. | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Moonshine **Arabic Tiny Streaming** | MIT | MIT, yes | Arabic listed. Publisher claim: 15.5% WER, 400-clip macro over Common Voice + FLEURS, quantized | 34M | Very likely: tiny ORT model | Native streaming per docs | ONNX Runtime (.ort), C/C++/Python/WASM | Pushed 2026-11-07 | SOURCE_VERIFIED `moonshine-ai/moonshine@d8d8fa29:LICENSE`, `:docs/models/available-models.md`, `:docs/models/accuracy.md` |
| Moonshine English Tiny/Small/Medium Streaming (B2 family) | MIT | MIT, yes | English only | 34M / 123M / 245M | Small and medium are in frozen B2; not reinterpreted | Native streaming per docs | ORT | as above | `000b1-qualification-report.md`; same LICENSE |
| Moonshine legacy Arabic Base/Tiny (non-streaming) | MIT | **Moonshine Community License**: NC plus commercial use only below US$1M annual revenue, with registration. **REJECTED** for default routes | Arabic; publisher's FLEURS claim not comparable | 58M (Base) | Yes | No | ORT | as above | SOURCE_VERIFIED `moonshine@d8d8fa29:LICENSE` Section 2 |
| `mistralai/Voxtral-Mini-4B-Realtime-Arabic` (`7c60cf2a`, 2026-10-08) | vLLM / Transformers ≥5.2 | Apache-2.0 (card "License" section), yes | **Dialect claims**: card tags include ar, ary, ayl, aeb, arq, mey, afb, ars, acx, ayn, arz, apd, acm, ajp, apc, shu. Publisher claim: average CER 8.82% across seven Arabic benchmarks at 480 ms delay, using its own MTNRA-co-developed normalizer | About 4.4B, BF16 | Doubtful for real time. There is a community ONNX/WebGPU export. NOT_RUN | Native realtime, configurable delay | vLLM `/v1/realtime`, Transformers, community ONNX | HF updated 2026-10-12 | DOCUMENTED https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-Arabic |
| `mistralai/Voxtral-Mini-4B-Realtime-2602` (`2769294d`) | vLLM / Transformers | Apache-2.0 (card metadata), yes | Arabic in card tags | About 4B | As above | Native realtime | vLLM, Transformers | 2026-03 | DOCUMENTED HF API |
| `Qwen/Qwen3-ASR-0.6B` / `-1.7B` (`5eb14417` / `7278e1e7`, 2026-01-28) | Apache-2.0 | Apache-2.0, yes | Arabic (ar) listed. Dialect list covers Chinese dialects only | 0.6B / 1.7B | 0.6B plausible, 1.7B slow. The CPU path (Transformers) is NOT_VERIFIED; streaming is documented via vLLM | "Offline / Streaming" unified | Transformers, vLLM | Repo pushed 2026-06-26 | SOURCE_VERIFIED `QwenLM/Qwen3-ASR@7c6daf77:README.md` |
| `nvidia/nemotron-speech-streaming-en-0.6b` | NeMo (Apache-2.0) | NOT_VERIFIED | English | 0.6B | sherpa-onnx int8 exports exist (community) | Streaming | NeMo, sherpa-onnx | — | HF search listing only: NOT_VERIFIED |
| sherpa-onnx streaming Zipformer (B2 family) | Apache-2.0 | Apache-2.0 for the B2 English model | English; Arabic streaming model NOT_VERIFIED | 73–265 MB | In frozen B2 | Native streaming | ONNX, C++ | Pushed 2026-11-07 | `qualified-candidates.json` |
| `microsoft/VibeVoice-ASR-Streaming-1.5B` / `-7B` (`4262d23d`, 2026-09) | MIT | MIT, yes | **Not listed** (en, zh, es, pt, de, ja, ko, fr, ru, it) | 1.5B / 7B | 1.5B unknown | Streaming | Transformers | 2026-09 | DOCUMENTED HF API |
| Kyutai STT `stt-1b-en_fr` / `stt-2.6b-en` | Apache-2.0 | CC-BY-4.0, yes with attribution | **Not listed** (en/fr) | 1B / 2.6B | — | Native streaming | PyTorch, Rust, MLX | DSM repo pushed 2026-01-26 | DOCUMENTED HF API |

### 2.2 ASR: batch / push-to-talk / server

| Candidate | Code lic. | Weights / commercial | Arabic (source) | Size | R0 CPU (inferred) | Runtime | Maint. | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `IFM/Jais-ASR` (`1323995f`, 2026-10-06) | Transformers + vLLM plugin (license of plugin NOT_VERIFIED) | Apache-2.0, yes | **19 dialects** (DZ, BH, EG, AE, IQ, JO, KW, LB, LY, MR, MA, OM, PS, QA, SA, SD, SY…), MSA, code-switching to en/fr/es/it, optional diacritics, dialect ID, a refusal token when there is no speech. Leaderboard claim 22.82 avg WER (app.py); card claim 22.85 WER / 8.37 CER | Based on Jais-3-4B; bf16 weights 11.4 GB; card says "roughly 12 GB of GPU memory" | **BLOCKED_EXTERNAL on R0** (GPU class) | Transformers 5.x, vLLM 0.23 | HF 2026-10-13 | DOCUMENTED https://huggingface.co/IFM/Jais-ASR |
| `CohereLabs/cohere-transcribe-arabic-07-2026` (`c3e911b4`) | — | Apache-2.0 (metadata), **gated=auto** (accepting the gate is a user action) | ar, en. Leaderboard claim 24.19 avg WER. Card claim 25.87 "as of 07.07.2026". Card notes inconsistent code-switching performance and no automatic LID (per dataset worker) | NOT_VERIFIED | NOT_VERIFIED | — | 2026-07 | DOCUMENTED HF API; BLOCKED_EXTERNAL for download |
| `CohereLabs/cohere-transcribe-03-2026` (`d552dadc`) | — | Apache-2.0 (metadata), gated=auto | ar among about 14 languages | NOT_VERIFIED | NOT_VERIFIED | — | 2026-10 | DOCUMENTED HF API |
| `abedbanna/Sygma-ASR-Arabic` (`d9c4166b`) | — | Apache-2.0 (metadata); base is Cohere Arabic | ar. Leaderboard claim 23.01 | NOT_VERIFIED | NOT_VERIFIED | — | 2026-10 | DOCUMENTED HF API. Individual uploader; provenance review needed |
| `audarai/Audar-ASR-V1-Turbo` (`371428be`) | — | **audarai-community-license-v1.0**: terms NOT_VERIFIED, treat as UNKNOWN | ar, en. Leaderboard claim 23.17 | NOT_VERIFIED | NOT_VERIFIED | — | 2026-08 | DOCUMENTED HF API |
| Meta **Omnilingual ASR** (CTC and LLM-ASR 300M–7B, v2) | Apache-2.0 | "code and models are released under the Apache 2.0", yes | 1,600+ languages. Per-variety publisher CER claims (7B LLM-ASR CSV): arb 2.4, acw 4.6, ary 4.2, aec 8.9, arz 9.9, ayl 10.6, apc 11.5, acm 14.7, aeb 20.1, arq 28.3, ars 38.9, afb 41.8. Training hours per variety are only 2–18 h, except arb at 1,146 h | CTC 300M = 1.3 GiB fp32; LLM 300M = 6.1 GiB | CTC 300M/1B plausible as batch. LLM variants heavy | fairseq2/PyTorch. **Inputs under 40 s only** (CTC/LLM) | Pushed 2025-12-30 | SOURCE_VERIFIED `facebookresearch/omnilingual-asr@81f51e22:README.md`, `:LICENSE`, `:per_language_results_table_7B_llm_asr.csv` |
| OpenAI Whisper large-v3 (`06f233fe`) / large-v3-turbo (`41f01f3f`) | MIT (`openai/whisper`) | Card metadata: large-v3 **apache-2.0**, turbo **MIT**; yes | Arabic listed (multilingual). Leaderboard claim large-v3 36.86 avg WER, Casablanca 71.81. NADI 2025 zero-shot baseline 93.89 WER. Known to translate dialect into MSA and to produce runaway output in some papers | 1.55B / 809M | Turbo via whisper.cpp quantized is plausible for PTT | PyTorch; GGML (whisper.cpp); CTranslate2 (faster-whisper) | whisper pushed 2026-08-31 | DOCUMENTED HF API |
| whisper.cpp (`ggml-org/whisper.cpp`) + `ggerganov/whisper.cpp` models (`5359861c`) | MIT | MIT, yes | Same as the Whisper checkpoint | — | Yes (B2 runtime) | GGML; chunked "stream" example | Pushed 2026-11-07 | DOCUMENTED; B2 pins unchanged |
| faster-whisper (`SYSTRAN/faster-whisper`) / `Systran/faster-whisper-large-v3` (`edaa852e`) | MIT | MIT (converted weights), yes | As Whisper | — | int8 CPU plausible | CTranslate2 | Pushed 2026-11-06 | DOCUMENTED |
| `nvidia/stt_ar_fastconformer_hybrid_large_pcd_v1.0` (`7f32349d`) | NeMo, Apache-2.0 | CC-BY-4.0, yes with attribution | Arabic (card language includes ar). The 2024 leaderboard paper's top system was an NVIDIA conformer-ctc-large-ar (LM) at 25.71 avg WER; the identity mapping to this checkpoint is NOT_VERIFIED | NOT_VERIFIED (FastConformer "large") | Plausible via ONNX export (NOT_VERIFIED) | NeMo; ONNX export path NOT_VERIFIED | NeMo repo active (2026-11-07) | DOCUMENTED HF API |
| NVIDIA Parakeet TDT 0.6B v2/v3, Canary-1B-v2, Canary-Qwen-2.5B | Apache-2.0 (NeMo) | CC-BY-4.0, yes | **Not listed** (card tags) | 0.6–2.5B | Parakeet via sherpa-onnx plausible (English cells) | NeMo, ONNX (sherpa) | 2026 card updates | DOCUMENTED HF API |
| `FunAudioLLM/Fun-ASR-MLT-Nano-2512` (`2c088f53`) | FunASR MIT | Apache-2.0, yes | Arabic in card tags | "Nano" (size NOT_VERIFIED) | NOT_VERIFIED | FunASR, vLLM | 2026-08 | DOCUMENTED HF API |
| `FunAudioLLM/SenseVoiceSmall` | MIT (repo) | Custom `model-license` (FunASR MODEL_LICENSE): terms NOT_VERIFIED | Not listed | Small | Yes (sherpa-onnx) | ONNX | Repo 2026-09 | DOCUMENTED HF API |
| `Qwen/Qwen3-Omni-30B-A3B-Instruct` | Apache-2.0 | Card `other`/apache-2.0, yes | Arabic not in tags. Leaderboard claim 30.71 avg | 30B MoE | BLOCKED_EXTERNAL (GPU) | Transformers, vLLM | 2026-04 | DOCUMENTED HF API |
| Voxtral Mini 3B / Small 24B (2507) | — | Apache-2.0, yes | Arabic not in card tags. Leaderboard claim Small-24B 34.47 | 3B / 24B | Mini maybe; Small no | vLLM, Transformers | 2025 | DOCUMENTED HF API |
| IBM `granite-speech-5.0-2b` (`ec49ca6b`) | — | Apache-2.0, yes | Not listed | 2B | NOT_VERIFIED; ONNX variant exists | Transformers, ONNX | 2026-11 | DOCUMENTED HF API |
| IBM `granite-speech-5.0-470m-turboctc-nc` | — | **CC-BY-NC-SA-4.0: REJECTED** | English | 470M | — | — | 2026-10 | DOCUMENTED HF API |
| `microsoft/Phi-4-multimodal-instruct` (`93f923e1`) | — | MIT, yes | Arabic listed for **text**. Speech-input languages NOT_VERIFIED | 5.6B (NOT_VERIFIED) | Heavy | Transformers | 2025-12 | DOCUMENTED HF API |
| `facebook/seamless-m4t-v2-large`, `facebook/mms-1b-all` | — | **CC-BY-NC-4.0: REJECTED** | Arabic listed. Leaderboard claim mms-1b-all 54.54 | — | — | — | — | DOCUMENTED HF API |

### 2.3 VAD

| Candidate | Code lic. | Weights / commercial | Language note | Size / CPU | Evidence |
| --- | --- | --- | --- | --- | --- |
| Silero VAD (`snakers4/silero-vad`) | MIT | MIT (bundled in repo; per-file confirmation NOT_VERIFIED this session) | Language-agnostic claim NOT_VERIFIED this session | Small ONNX, CPU | DOCUMENTED gh API (MIT, pushed 2026-10-22); rights register pin `1e261b03` |
| TEN VAD (`TEN-framework/ten-vad`) | **Apache-2.0 plus Agora conditions**: you may not deploy it "in a way that competes with Agora's offerings" or that enables third parties to build applications. Deployment is allowed only for your own applications and their direct end users | Same file | — | Small, CPU | SOURCE_VERIFIED `TEN-framework/ten-vad@8843b975:LICENSE`. **REJECTED for Klaint** (a platform letting tenants deploy agents plausibly falls under clause 1). Side use needs legal review |
| Moonshine micro `tinyvad_cnn` | MIT (repo) | MIT by repo default (NOT_VERIFIED per file) | — | Very small | SOURCE_VERIFIED path `moonshine@d8d8fa29:micro/models/tinyvad_cnn_speech_mel.onnx` (exists) |
| WebRTC VAD, NVIDIA MarbleNet, pyannote segmentation-3.0 (MIT, gated auto) | — | segmentation-3.0 MIT (`e66f3d3b`, gated) | — | — | Others NOT_VERIFIED |

### 2.4 Turn detection / endpointing

| Candidate | Code lic. | Weights / commercial | Arabic | Size / CPU | Evidence |
| --- | --- | --- | --- | --- | --- |
| **pipecat smart-turn v3.2** (`pipecat-ai/smart-turn-v3`, `f766f81d`) | BSD-2-Clause | BSD-2-Clause (card metadata). README: datasets, training script and weights are open | **Arabic listed** among 23 languages; dialect coverage not stated | About 8M parameters (Whisper-Tiny base plus classifier). CPU int8 8 MB. Publisher claims "10ms on some CPUs" and about 65 ms on a Pipecat Cloud instance | SOURCE_VERIFIED `pipecat-ai/smart-turn@4786657e:README.md`; DOCUMENTED HF API |
| LiveKit `livekit/turn-detector` (`fba34c38`) | Apache-2.0 (agents) | **`livekit-model-license`**: terms NOT_VERIFIED this session; earlier knowledge says use is restricted to LiveKit Agents. Treat as UNKNOWN | Card language tags do not include ar | Small text model | DOCUMENTED HF API |
| TEN Turn Detection (`TEN-framework/TEN_Turn_Detection`, `41845390`) | Repo NOASSERTION | Card says apache-2.0, but the repo license may carry the same Agora conditions as TEN VAD: NOT_VERIFIED. Treat as UNKNOWN | NOT_VERIFIED | 7B-class text model (NOT_VERIFIED) | DOCUMENTED HF API, gh API |
| NVIDIA `parakeet_realtime_eou_120m-v1` (2025-10) | NeMo | NOT_VERIFIED | English | 120M | HF listing only |
| Jais-ASR refusal token / Voxtral realtime delay | — | — | — | — | These are not turn detectors. Do not substitute them |

### 2.5 Diarization and speaker embedding

| Candidate | Code lic. | Weights / commercial | Gated | Evidence |
| --- | --- | --- | --- | --- |
| pyannote `speaker-diarization-community-1` (`3533c8cf`) | MIT (pyannote-audio, pushed 2026-11-07) | CC-BY-4.0, yes with attribution | **auto-gated**: accepting is a user action, so BLOCKED_EXTERNAL for this mission | DOCUMENTED HF API |
| pyannote `speaker-diarization-3.1` (`84fd2591`) | MIT | MIT | auto-gated | DOCUMENTED HF API |
| NVIDIA `diar_streaming_sortformer_4spk-v2` (`84edd514`) | NeMo Apache-2.0 | CC-BY-4.0, yes | No | DOCUMENTED HF API. Up to 4 speakers per the name; streaming |
| `BUT-FIT/diarizen-wavlm-large-s80-md` (`6285693d`) | MIT (DiariZen code) | **CC-BY-NC-4.0: REJECTED** | No | DOCUMENTED HF API |
| WeSpeaker / 3D-Speaker | Apache-2.0 | Weights NOT_VERIFIED | — | gh API |
| Moonshine diarization models | MIT repo | NOT_VERIFIED (`docs/diarization-models.md` exists) | — | SOURCE_VERIFIED path exists at `moonshine@d8d8fa29` |

No Arabic-specific diarization evidence was verified. Arabic broadcast and telephony diarization quality is NOT_VERIFIED.

### 2.6 Speech enhancement, denoise and separation

| Candidate | Code lic. | Weights / commercial | Evidence |
| --- | --- | --- | --- |
| RNNoise (`xiph/rnnoise`) | BSD-3-Clause | Bundled model under the same license (NOT_VERIFIED per file) | gh API (pushed 2025-02-22) |
| DeepFilterNet (`Rikorose/DeepFilterNet`) | Repo NOASSERTION; earlier knowledge says MIT/Apache dual: NOT_VERIFIED | NOT_VERIFIED | gh API |
| Demucs (`facebookresearch/demucs`) | MIT (rights register) | Pretrained weights license NOT_VERIFIED | register pin `e976d93e` |
| ClearerVoice-Studio (MossFormer2 etc.) | Apache-2.0 | Weights NOT_VERIFIED | gh API (pushed 2025-08-14) |
| `ResembleAI/resemble-enhance` | — | NOT_VERIFIED | HF listing |
| Echo cancellation for barge-in (WebRTC AEC3, SpeexDSP) | NOT_VERIFIED | — | — |

### 2.7 TTS (preset voices)

| Candidate (card rev) | Code lic. | Weights / commercial | Arabic (source) | Size / R0 CPU (inferred) | Streaming | Maint. | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Chatterbox Multilingual V3** (`ResembleAI/chatterbox`, `5bb1f6ee`) | MIT | MIT, yes. **PerTh watermark** built into every output | **Arabic (ar) listed** among 23 languages. There is no Arabic single-language pack (packs exist for zh, es-MX, es-ES, pt-BR, pt-PT and hi only) | 500M; CPU feasible but probably slower than real time: NOT_RUN | Not documented | **"As of August 2026, Chatterbox is retired research and is no longer maintained"**. The repo is an MIT archive | SOURCE_VERIFIED `resemble-ai/chatterbox@ab55923c:README.md` |
| Chatterbox Turbo (350M) / Nano (110M) / Flash | MIT | MIT, yes | **English only** | Nano: publisher claim "3x faster than realtime on 8 CPU cores" | — | Retired as above | SOURCE_VERIFIED same README; DOCUMENTED HF API |
| `silma-ai/silma-tts` (`226dd7a6`, 2026-03-13) | NOT_VERIFIED | Apache-2.0 (metadata); base-model lineage and inherited terms NOT_VERIFIED | en, ar in tags; dialects NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | HF 2026-08 | DOCUMENTED HF API |
| Piper (`OHF-Voice/piper1-gpl`; old `rhasspy/piper` archived) | **GPL-3.0** (piper1-gpl) | `rhasspy/piper-voices` (`e7229f7d`) metadata says MIT, but **per-voice MODEL_CARD licenses vary: NOT_VERIFIED for Arabic voices** | Arabic voice(s) present (ar in tags) | Very small, CPU real time (publisher-class claim, NOT_RUN) | Chunked | piper1-gpl pushed 2026-11-07 | DOCUMENTED HF API, gh API |
| Moonshine Voice TTS, Arabic MSA path | MIT code | TTS/G2P assets "licensed under the terms listed in their own readmes". The Arabic path uses Piper-derived voices plus an AraBERT-based tashkeel ONNX: per-asset licenses NOT_VERIFIED | MSA only | CPU | Frame-range streaming of Piper stages | Active | SOURCE_VERIFIED `moonshine@d8d8fa29:LICENSE`, `:core/moonshine-tts/data/README.md`, `:core/moonshine-tts/data/ar_msa/README.md` |
| Qwen3-TTS 0.6B/1.7B (Base, CustomVoice, VoiceDesign) | Apache-2.0 | Apache-2.0, yes | **Not listed**: 10 languages (zh, en, ja, ko, de, fr, ru, pt, es, it) | 0.6B/1.7B | Documented in repo (not re-read) | Repo 2026-03 | SOURCE_VERIFIED `QwenLM/Qwen3-TTS@022e286b:README.md` |
| CosyVoice 2 / Fun-CosyVoice3-0.5B-2512 | Apache-2.0 | Apache-2.0, yes | **Not listed**: 9 languages plus Chinese dialects | 0.5B | Streaming (per register) | Repo 2026-05 | SOURCE_VERIFIED `QwenAudio/CosyVoice@074ca6dc:README.md` |
| Kokoro-82M (`f3ff3571`) | Apache-2.0 | Apache-2.0, yes | Not listed | 82M, CPU-friendly (inferred) | — | Repo 2025-08 | DOCUMENTED HF API |
| Kyutai Pocket TTS (`kyutai/pocket-tts`, `db04f0e6`) | MIT (repo) | CC-BY-4.0, **gated auto** | Not listed | CPU-targeted (per its positioning; NOT_RUN) | Streaming | 2026-11-07 | DOCUMENTED HF API, gh API |
| Kyutai TTS 1.6B en/fr | Apache-2.0 | CC-BY-4.0 | Not listed | 1.6B | Streaming | 2025 | DOCUMENTED HF API |
| Microsoft VibeVoice 1.5B / Realtime-0.5B | MIT | MIT | Not listed | 1.5B / 0.5B | Realtime variant | Repo 2026-10 | DOCUMENTED HF API |
| Orpheus 3B (`canopylabs/orpheus-3b-0.1-ft`) | Apache-2.0 | apache-2.0 (metadata, gated auto); Llama-3.2 base-license inheritance NOT_VERIFIED | Not listed | 3B | Streaming | Repo 2025-12 | DOCUMENTED HF API |
| IndexTTS2 (`IndexTeam/IndexTTS-2`) | Repo NOASSERTION | **Card license empty: NOT_VERIFIED (treat as UNKNOWN)** | Not listed | — | — | Repo 2026-09 | DOCUMENTED HF API |
| Higgs Audio v2 (`boson-ai/higgs-audio`) | Apache-2.0 | Weights NOT_VERIFIED (HF lookup failed) | NOT_VERIFIED | 3B+ | — | 2026-06 | gh API |
| Dia, Sesame CSM-1B, Spark-TTS, Zonos, NeuTTS | Apache-2.0 (Dia, CSM, Spark, Zonos code); NeuTTS repo NOASSERTION | Weights NOT_VERIFIED | English or not verified | — | — | Several stale (Zonos and Spark last pushed early 2025) | gh API |
| **F5-TTS** (`SWivid/F5-TTS`, `84e5a410`) | MIT | **CC-BY-NC-4.0: REJECTED** | — | — | — | — | DOCUMENTED HF API |
| **XTTS-v2** (`coqui/XTTS-v2`, `6c2b0d75`) | MPL-2.0 (coqui-ai/TTS, last push 2024-08; idiap fork active) | **Coqui Public Model License (CPML): REJECTED** | Arabic supported per earlier knowledge (NOT_VERIFIED); used as the NADI 2026 TTS baseline | — | — | — | DOCUMENTED HF API |
| **Fish-Speech 1.5** (`275a984d`) / OpenAudio S1-mini | Repo NOASSERTION | 1.5: **CC-BY-NC-SA-4.0: REJECTED**. S1-mini: NOT_VERIFIED | ar in tags (1.5) | — | — | — | DOCUMENTED HF API |
| **Voxtral-4B-TTS-2603** (`b81be46c`) | — | **CC-BY-NC-4.0: REJECTED** (reference voices also NC per register) | ar in tags | 4B | — | — | DOCUMENTED HF API |
| **OmniVoice** (`k2-fsa/OmniVoice`, `c5fdb5cc`) | Apache-2.0 | Card metadata license now empty. The pr124 register captured CC-BY-NC pretrained weights: **REJECTED until re-verified** | ar in tags | — | — | — | DOCUMENTED HF API; pr124 register |
| **MMS-TTS-ara** (`afba26a4`) | — | **CC-BY-NC-4.0: REJECTED** | Arabic | — | — | — | DOCUMENTED HF API |
| LiquidAI `LFM3-Audio-2B` (`2d6c1f99`) | — | **`lfm1.0`** (LFM Open License; revenue threshold terms NOT_VERIFIED this session). Excluded by default as REVENUE_CAPPED | ar in tags; TTS capability NOT_VERIFIED | 2B | — | — | DOCUMENTED HF API |

### 2.8 Voice cloning and voice conversion

| Candidate | Weights / commercial | Arabic | Note |
| --- | --- | --- | --- |
| Chatterbox Multilingual V3 (zero-shot clone) | MIT; watermark | Listed | The only verified MIT model that clones in Arabic. Unmaintained. Reference-voice consent is still required |
| Qwen3-TTS Base (clone) | Apache-2.0 | Not listed | English and the other 9 languages only |
| CosyVoice 3 (clone, cross-lingual) | Apache-2.0 | Not listed | — |
| OpenVoice V2 tone-color converter (`f36e7edf`) | MIT | Not listed. Language-agnostic conversion for Arabic NOT_VERIFIED | Candidate voice-conversion stage after a licensed Arabic TTS. NOT_RUN |
| Seed-VC, RVC, kNN-VC | NOT_VERIFIED | — | Not researched this session |
| F5, XTTS-v2, Fish, Voxtral TTS, OmniVoice | NC: **REJECTED** | Some list Arabic | Do not use as commercial clone engines |

### 2.9 Voice design (text-described voices)

| Candidate | Weights | Arabic | Evidence |
| --- | --- | --- | --- |
| `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` (`5ecdb673`) | Apache-2.0 | **Not listed** | DOCUMENTED HF API |
| Others (Parler-TTS, Higgs, VibeVoice prompts) | NOT_VERIFIED | NOT_VERIFIED | — |

There is **no verified commercially licensed open Arabic voice-design model**. This is a gap (FT-5).

### 2.10 Speech translation

| Candidate | License | Arabic | Note |
| --- | --- | --- | --- |
| Whisper `translate` task | MIT / Apache-2.0 card | X→English only | Studio dubbing out of Arabic only |
| Canary-1B-v2 (AST) | CC-BY-4.0 | Not listed | — |
| SeamlessM4T v2 / Seamless Streaming | **CC-BY-NC-4.0: REJECTED** | Listed | — |
| Voxtral Mini/Small; Qwen3-Omni | Apache-2.0 | Arabic translation quality NOT_VERIFIED | GPU class |
| **Cascade**: ASR → reviewed transcript → Apache-licensed LLM MT (Qwen3.5/3.6, Gemma 4, Jais 3, Fanar-2) → human review → TTS | Per component | Arabic-capable LLMs listed in 2.12 | Recommended for Studio dubbing: each stage auditable, raw transcript retained. Quality NOT_RUN |

### 2.11 Forced alignment

| Candidate | License | Arabic | Note |
| --- | --- | --- | --- |
| `Qwen/Qwen3-ForcedAligner-0.6B` (`c7cbfc20`) | Apache-2.0 | **Not supported**: its 11 languages exclude Arabic | SOURCE_VERIFIED `Qwen3-ASR@7c6daf77:README.md` |
| Omnilingual ASR CTC models used for CTC segmentation | Apache-2.0 | Arabic varieties covered | Inferred technique. NOT_VERIFIED as a shipped aligner |
| `MahmoudAshraf97/ctc-forced-aligner` | BSD-2-Clause code | The default alignment weights may be MMS-derived (NC): NOT_VERIFIED | Check the weight identity before use |
| WhisperX (`m-bain/whisperX`) | BSD-2-Clause | Per-language wav2vec2 aligner; Arabic model license NOT_VERIFIED | — |
| Montreal Forced Aligner | MIT code | Arabic acoustic model and dictionary license NOT_VERIFIED | — |
| NeMo Forced Aligner with the Arabic FastConformer (CC-BY-4.0) | Apache-2.0 / CC-BY-4.0 | Arabic | Plausible. NOT_VERIFIED |

### 2.12 Language identification (routing aid)

| Candidate | License | Note |
| --- | --- | --- |
| `mistralai/LIDstral-Arabic` (`077451f0`, 2026-10) | Apache-2.0 | Card tags include many Arabic varieties plus Berber (tzm, zgh). The HF pipeline tag is `text-classification`, so **audio vs text input is NOT_VERIFIED** |
| Jais-ASR built-in dialect labels | Apache-2.0 | Output field `language` (e.g. `msa`, `EG`) per card. GPU class |
| Whisper LID | MIT | Language level only, no dialect |
| MMS-LID | CC-BY-NC: **REJECTED** | — |

### 2.13 Text-rewriting LLM (small, local, R0)

All rows are DOCUMENTED from HF card metadata and README text captured on 2026-11-08 in `workers/models/readme/` and the HF API TSVs. Arabic claims quote the card. Fit on R0 assumes 4-bit GGUF or ONNX and is NOT_RUN.

| Model | License / commercial | Params | Arabic claim | Tool calling | R0 fit (inferred) |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-2B / 4B (2026) | Apache-2.0 | 2B / 4B | Multilingual; Arabic-specific statement NOT_VERIFIED in captured text | Yes (tool-call parser documented) | Yes |
| Qwen3-4B-Instruct-2507 | Apache-2.0 | 4B | Multilingual (not re-quoted) | "excels in tool calling" | Yes |
| Gemma 4 E2B / E4B (2026-03) | Card metadata `apache-2.0` with link to `ai.google.dev/gemma/docs/gemma_4_license`. Whether any Gemma prohibited-use policy still attaches is NOT_VERIFIED | E2B/E4B (effective) | Multilingual claim; Arabic NOT_VERIFIED | "native function-calling support" | Yes |
| Jais 3 3.7B / 0.9B (`inception42`, 2026) | Apache-2.0 | 3.7B / 0.9B | Arabic-centric. Card reports Arabic MMLU and Arabic GSM8K (publisher claims, not quoted) | Tool-call parser `k2_horizon` documented | Yes |
| Ministral 3 3B / 8B Instruct (2512) | Apache-2.0 | 3B / 8B | Arabic listed | Native function calling and JSON | 3B yes; 8B tight |
| Phi-4-mini-instruct | MIT | 3.8B | Arabic listed | Function-calling training data mentioned | Yes |
| Granite 4.2 3B / 4.0-h-micro | Apache-2.0 | 3B | Arabic listed | Tool-calling tag | Yes |
| SmolLM3-3B | Apache-2.0 | 3B | Card: trained on Arabic (standard) with fewer tokens | Yes | Yes |
| SILMA-Kashif-2B, Atlas-Chat (Darija), Nile-Chat (Egyptian, Arabic script + Arabizi) | **Gemma license** (gemma terms; conditions NOT_VERIFIED this session) | 2B–9B | Arabic or dialect-specialised | NOT_VERIFIED | Yes (small sizes) |
| LFM2.5 / LFM3-1.7B / d1-2B (LiquidAI) | **`lfm1.0`**: REVENUE_CAPPED class, threshold NOT_VERIFIED this session. Excluded by default | 1.2–2.6B | Arabic listed | Yes | Yes |
| `CohereLabs/tiny-aya-global` | **CC-BY-NC-4.0: REJECTED** | — | Arabic in tags | — | — |
| Llama 3.2 3B | Llama 3.2 Community License (text not re-read this session: NOT_VERIFIED; MAU and acceptable-use conditions known from prior knowledge) | 3B | NOT_VERIFIED | Yes | Yes |
| Falcon-H1 3B/7B, H1R-7B, H1-Tiny-Tool-Calling-90M | **Falcon LLM license** (terms URL documented; conditions NOT_VERIFIED) | 0.09–7B | NOT_VERIFIED | Tiny tool-calling variant exists | Yes |

### 2.14 Agent-reasoning LLM with tool use (Klaint)

| Model | License | Params | Arabic | Tool calling | Hardware |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-9B / 35B-A3B; Qwen3.6-27B / 35B-A3B | Apache-2.0 | 9B; 35B MoE (3B active); 27B | Multilingual (Arabic NOT_VERIFIED in captured text) | `qwen3_coder` tool-call parser documented | 9B: R0 at Q4 tight. Others need a GPU (BLOCKED_EXTERNAL) |
| `Qwen/Qwen3.8-27B` (2026-08) | Apache-2.0 | 27B | NOT_VERIFIED | Built-in tools | GPU |
| `Qwen/Qwen3.8-Flash-Next` | **`qwen-community-1.0`**: terms NOT_VERIFIED, treat as UNKNOWN | — | — | — | — |
| `Qwen/Qwen-AgentWorld-35B-A3B` (2026-06) | Apache-2.0 | 35B MoE | NOT_VERIFIED | Agent-oriented | GPU |
| Gemma 4 12B / 26B-A4B / 31B | apache-2.0 metadata + Gemma 4 license link (see 2.13) | 12–31B | NOT_VERIFIED | Native function calling | GPU |
| Jais 3 7B / 32B / MoVA-36B-A4B / 375B-A23B | Apache-2.0 | 7B–375B | Arabic-centric ("Arabic-centric Agentic AI") | `k2_horizon` parser | 7B: R0 at Q4. Others GPU |
| `QCRI/Fanar-2-27B-Instruct` (`07400504`, 2026-03) | Apache-2.0 | 27B | Arabic–English | "tool calling" documented | GPU |
| `QCRI/Fanar-1-9B-Instruct` | Apache-2.0 | 9B (Gemma-2-9B continual pretraining) | Arabic–English | NOT_VERIFIED | Q4 fits R0. **Only 4,096-token context** |
| `humain-ai/ALLaM-7B-Instruct-preview` | Apache-2.0 | 7B | Arabic–English (NCAI/SDAIA) | NOT_VERIFIED | Q4 fits R0 |
| Ministral 3 14B; Mistral Small 3.2 24B / Small 4 119B | Apache-2.0 | 14–119B | Arabic listed (3/4) | Native function calling | GPU |
| Mistral Medium 3.5 128B | `other`: NOT_VERIFIED | — | — | — | — |
| `openai/gpt-oss-20b` | Apache-2.0 (usage-policy attachment NOT_VERIFIED) | 21B MoE | NOT_VERIFIED | Native function calling | Borderline on 16 GB. NOT_RUN |
| Granite 4.2 8B / 30B | Apache-2.0 | 8B / 30B | Arabic listed | Tool-calling | 8B Q4 on R0 |
| Karnak 6B / 40B (Applied-Innovation-Center) | Apache-2.0 | 6B / 40B | Arabic–English | NOT_VERIFIED | 6B Q4 on R0 |
| AceGPT-v2-8B-Chat | Apache-2.0 (metadata). Llama-3 base inheritance NOT_VERIFIED | 8B | Arabic | NOT_VERIFIED | Q4 on R0 |
| Command R7B Arabic | Gated; **CC-BY-NC per prior knowledge: REJECTED pending verification** | 7B | Arabic | — | — |
| Llama 3.1/3.3/4 | Llama Community Licenses: NOT_VERIFIED this session | — | — | — | — |
| Optional provider (user-approved only) | Provider terms | — | — | — | Disabled by default. Never automatic or paid without approval |

Jais 2 (`inception42/Jais-2-8B-Chat`, `-70B-Chat`): the captured cards had no license line. NOT_VERIFIED.

### 2.15 Consolidated license-trap register

| Trap | Items | Handling |
| --- | --- | --- |
| Permissive code, NC weights | F5-TTS, DiariZen, OmniVoice (per register), Fish-Speech, Voxtral TTS, MMS / MMS-TTS / Seamless, tiny-aya, granite-speech-470m-nc | REJECTED from commercial routes and from model-selection evaluation |
| Non-commercial model license | XTTS-v2 (CPML) | REJECTED |
| Revenue-capped community license | Moonshine legacy non-English Base/Tiny (US$1M cap, registration); LiquidAI `lfm1.0`; Audar community license (unknown) | Excluded by default (REVENUE_CAPPED / UNKNOWN) |
| Non-compete add-on to Apache | TEN VAD (SOURCE_VERIFIED); possibly TEN Turn Detection | REJECTED for Klaint; legal review for Side |
| Vendor-tied model license | LiveKit turn-detector (`livekit-model-license`) | UNKNOWN until read |
| Copyleft runtime | piper1-gpl (GPL-3.0); VoiceStudio AGPL (founder grant per register) | Separate process with source-offer obligations, or the founder-grant route as recorded |
| Gated acceptance | pyannote 3.1 / community-1, Cohere transcribe, Pocket TTS, Orpheus | Acceptance is a user action. BLOCKED_EXTERNAL for this mission |
| Watermark obligation | Chatterbox PerTh (built in) | Record in the manifest; do not strip |
| Unmaintained | Chatterbox (retired Aug 2026), coqui-ai/TTS (last push 2024-08), rhasspy/piper (archived), Zonos and Spark-TTS (no push since early 2025) | Maintenance risk is a routing input |
| Model-card number vs leaderboard mismatch | Cohere card 25.87 vs leaderboard 24.19; Jais-ASR card 22.85 vs app.py 22.82 | Cite as claims with dates; never as Wispral results |

## 3. Provider references (optional; disabled by default)

Provider routes are reference points only. They need explicit, purpose-scoped approval, a cost display and a budget cap (Section 6). There is no automatic paid inference and no hidden fallback.

- Example: Azure Speech lists 18 `ar-*` speech-to-text locales and 16 `ar-*` neural TTS locales (DOCUMENTED https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=stt, accessed 2026-11-08). A country locale is **not** evidence of dialect accuracy.
- The Jais-ASR card compares itself against Speechmatics Melia 1 and ElevenLabs Scribe v2. Those comparisons are publisher claims.

## 4. Arabic quality: public evidence

Source: dataset/leaderboard worker report, 2026-11-08, plus my own SOURCE_VERIFIED reads. "Commercial-eval usable" is an engineering reading of stated terms, not legal advice. CC BY-NC 4.0 defines NonCommercial as "not primarily intended for or directed towards commercial advantage or monetary compensation" (https://creativecommons.org/licenses/by-nc/4.0/legalcode.en). Internal benchmarking to select models for a sold product is therefore treated as **not** permitted under NC or research-only terms.

### 4.1 Leaderboards and benchmarks (all dated claims)

**Open Universal Arabic ASR Leaderboard (ELM Research Center)**
- Paper arXiv:2412.13788; HF space `elmresearchcenter/open_universal_arabic_asr_leaderboard`; code `github.com/Natural-Language-Processing-Elm/open_universal_arabic_asr_leaderboard`.
- Zero-shot WER/CER on SADA (10.7 h), Common Voice 18.0 (12.6 h), MASC clean (10.5 h), MASC noisy (8.9 h in the paper; 14.9 h in app.py), MGB-2 (9.6 h) and Casablanca (7.7 h, added 2025-01-11). QASR was excluded.
- The submission README asks entrants not to train on the test sets. Contamination is not checked.
- Average WER from `app.py`, last update-log entry 2026-10-19 (leaderboard claims):

| Model | Avg WER |
| --- | --- |
| IFM/Jais-ASR | 22.82 (CER 8.31; Casablanca 46.61; SADA 30.52; CV 8.59; MGB-2 9.60) |
| abedbanna/Sygma-ASR-Arabic | 23.01 |
| audarai/Audar-ASR-V1-Turbo | 23.17 |
| CohereLabs/cohere-transcribe-arabic-07-2026 | 24.19 (Casablanca 45.68) |
| omniASR_LLM_7B | 28.32 |
| Qwen3-Omni-30B | 30.71 |
| Qwen3-ASR-1.7B | 33.36 |
| Voxtral-Small-24B | 34.47 |
| whisper-large-v3 | 36.86 (Casablanca 71.81) |
| mms-1b-all | 54.54 |

Casablanca is the worst column for every model, and SADA is second worst.

**NADI 2025 Subtask 2** (arXiv:2509.02038v2; Casablanca subset)
- Winner: Munsit at 35.68 WER / 12.20 CER. Zero-shot Whisper-large-v3 baseline: 93.89 WER.
- Munsit's per-dialect WER: Jordan 20.68, Egypt 20.88, Palestine 22.27, UAE 22.66, Morocco 41.71, Yemen 44.62, Algeria 53.62, Mauritania 59.03.

**NADI 2026** (arXiv:2609.27086v1)
- Robust 4 kHz ASR, best: 43.24 WER.
- Mixed-dialect ASR, best: 44.22 WER.
- Code-switched Tunisian ASR, best: 14.41 WER, after in-domain training.
- TTS track: one submission. The XTTS-v2 baseline beat it. The organisers say automatic metrics barely distinguish dialects. Intelligibility was scored with omniASR-LLM-7B forced to `arb_Arab`, which the paper calls MSA-biased.

**Arab Voices** (arXiv:2601.13319v2)
- A framework over 31 datasets and 14 dialects. It ships scripts, not data.
- Best test WER per dialect, worker's reading of Table 2:

| Dialect | Best WER |
| --- | --- |
| MSA | 10.19 |
| Levantine | 23.53 |
| Egyptian | 34.80 |
| Najdi | 46.90 |
| Hijazi | 53.49 |
| Khaleeji | 53.71 |
| Mesopotamian | 71.16 |
| Tunisian | 74.31 |
| Algerian | 78.01 |
| Moroccan | 79.71 |
| Hassaniyya | 83.17 |

**Publisher self-reports**
- Omnilingual per-variety CER, 7B LLM-ASR (SOURCE_VERIFIED CSV): Najdi (ars) 38.9 and Gulf (afb) 41.8 vs MSA (arb) 2.4. Training hours per dialect are only 14–15 h.
- Moonshine Arabic Tiny Streaming: 15.5% WER.
- Voxtral Realtime Arabic: 8.82% average CER at 480 ms delay, with its own normalizer.
- Jais-ASR: 22.85 / 8.37 on the leaderboard script.
- NVIDIA blog (2026-09-30, seen only via a search summary, NOT_VERIFIED): fine-tuning on 133.7 h of SADA Najdi/Hijazi took WER from 55.05 to 29.96.

**TTS evidence**
- There is no Arabic TTS leaderboard.
- SawtArabi (Interspeech 2025): 25 listeners × 25 sentences. MSA naturalness 3.15 vs 4.37 for ground truth.
- ArVoice (Interspeech 2025): A/B tests with at least 10 native raters. VITS ASR-WER 20.67 diacritised vs 35.69 undiacritised. Fish-Speech was over 100% WER and was dropped.
- Habibi (arXiv:2601.13802): automatic metrics only, compared against ElevenLabs v3 alpha.
- QASR-TTS (2023): MOS 4.4 intelligibility, 4.2 naturalness.
- "More Data, Fewer Diacritics" (arXiv:2603.01622): diacritised training generally helps.

### 4.2 Dataset table

| Dataset | License / terms | Dialects | Size | Type | Commercial-eval usable? | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Casablanca (UBC-NLP) | HF: CC-BY-NC-ND-4.0; paper: "research use only" | Algeria, Egypt, UAE, Jordan, Mauritania, Morocco, Palestine, Yemen | ~48 h (HF: validation and test only) | TV series; code-switching annotated | **No** | DOCUMENTED huggingface.co/datasets/UBC-NLP/Casablanca; arXiv:2410.04527 |
| NADI 2025 ASR data | Inherits Casablanca; HF returned 401 | Same | 1,600 utterances per split per dialect | TV | **No** | PARTIAL arXiv:2509.02038 |
| SADA (SDAIA/NCAI + SBA) | Kaggle: CC BY-NC-SA 4.0. IEEE DataPort shows CC BY 4.0 but its instructions say NC-SA (**conflict**) | Saudi (Najdi > Hijazi > Khaliji), some MSA and Egyptian | ~667 h | Broadcast TV | **No** (treat as NC until resolved in writing) | DOCUMENTED kaggle sdaiancai/sada2022; ieee-dataport node 14747 |
| MGB-2 (QCRI) | "NON-EXCLUSIVE RESEARCH USE LICENSE"; commercial use needs a Qatar Foundation license; auto-gated | MSA-heavy plus dialects | ~1,200 h | Al Jazeera | **No** | DOCUMENTED huggingface.co/datasets/QCRI/mgb2 |
| MGB-3 (Egyptian) | No license posted; series described as research-only | Egyptian | 16 h | YouTube | **No / unverified** | PARTIAL |
| MGB-5 (Moroccan) | Org reply: "still for research purposes only" | Moroccan | ~13–14 h (conflicting 54 h) | YouTube | **No** | PARTIAL |
| QASR (QCRI) | CC-BY-NC-2.0 | Multi-dialect, mostly MSA, code-switching | ~2,000 h | Broadcast | **No** | DOCUMENTED HF QCRI/QASR |
| Common Voice Arabic (v27.0, 2026-09-11) | CC0, plus an agreement not to re-identify speakers; per-dataset sign-off via Mozilla Data Collective | Self-reported accent (mostly blank) | 158.27 h total, 93.34 h validated, 1,679 users | Read prompts | **Yes** (honour the no-reidentification term) | DOCUMENTED cv-dataset JSON; license page PARTIAL |
| FLEURS ar_eg (Google) | CC-BY-4.0 | MSA text, Egyptian speakers | ~8 h | Read | **Yes** (attribution) | DOCUMENTED HF google/fleurs |
| ArzEn / ArzEn-ST | Google Form; **no license on the page** | Egyptian + English code-switching | 12 h, 38 speakers | Interviews | **Unknown**: obtain terms | PARTIAL |
| ESCWA-CS (QCRI) | QCRI-ALT cc-by-nc-4.0, gated | Dialectal + English/French code-switching | ~2.8 h | UN meetings | **No** | DOCUMENTED |
| Mixat (Emirati–English) | CC BY-NC-SA 4.0; audio "for research purposes" | Emirati + English (36% code-switched sentences) | 14.9 h | Podcasts | **No** | DOCUMENTED h-aldarmaki.github.io/mixat |
| SCC (Saudilang Code-Switch, SDAIA) | CC BY-NC-SA 4.0 | Saudi + English | ~5 h | Podcast | **No** | DOCUMENTED kaggle |
| MASC | CC BY 4.0 (IEEE DataPort, login required) | MSA + 20+ dialects | ~1,000 h | YouTube | **Conditional yes**: YouTube rights rest on the publisher's assertion | DOCUMENTED |
| Arabic Speech Corpus (Halabi) | CC BY 4.0, but the footer says "All rights reserved" | MSA, one speaker | 1,813 utterances | Studio read | **Conditional** (clarify) | DOCUMENTED |
| ClArTTS | CC-BY-4.0 (HF) | Classical Arabic, one speaker | ~12 h | Audiobook | **Yes** (official site unreachable) | PARTIAL |
| ArVoice | HF CC-BY-4.0 for some subsets, a DUA for the professional subset; project badge says CC BY-NC-SA (**conflict**) | MSA, diacritised | 83.5 h (about 10 h human) | TTS read | **Conditional** | PARTIAL |
| SawtArabi | Not stated | MSA, Egyptian, Egyptian–English code-switching | ~4 h | TTS studio | **Unknown** | PARTIAL |
| QASR-TTS | Not verified | MSA | Small | Broadcast | **Unknown** | UNVERIFIED |
| KSUEmotions (LDC2017S12) | LDC agreement | MSA | ~5 h | Emotional read | **Only with LDC for-profit membership** | DOCUMENTED |
| LDC Gulf / Iraqi / Levantine CTS | LDC; non-members "cannot use LDC data to develop or test products for commercialization" | Gulf; Iraqi; Levantine | ~47 / 50 / 45 h | 8 kHz telephone | **Only with LDC for-profit membership**. Valuable for Klaint telephony | DOCUMENTED |
| TunSwitch | CC BY 4.0 (Zenodo) | Tunisian + French/English code-switching | Several zips (18 GB) | Radio and podcasts | **Yes** | DOCUMENTED zenodo 8370566 |
| LinTO Tunisian | CC-BY-4.0 (relicenses YouTube aggregates) | Tunisian | ~93 h | Mixed | **Conditional** (provenance) | DOCUMENTED |
| TARIC-SLU | LICENCE.md unreadable | Tunisian | ~6 h | Dialogues | **Unknown** | UNVERIFIED |
| DVoice (Darija) | CC BY 4.0 (Zenodo) | Moroccan | Not stated | Community read | **Yes** | DOCUMENTED zenodo 5824476 |
| Omnilingual ASR Corpus (Meta) | CC-BY-4.0 | acm, acw, aeb, afb, apc, apd, arq, ars, ary, arz, ayl, ayp | ~2.5–62 h per variety | Mixed | **Yes**. Note it is also Omnilingual's training source, so it is contaminated for evaluating that model | DOCUMENTED HF facebook/omnilingual-asr-corpus |
| YODAS2 (ar) | CC-BY-3.0 | Mixed | Long-form | YouTube, noisy subtitles | **Conditional**: not evaluation-grade | DOCUMENTED |
| Granary v2 (NVIDIA) | Manifest openmdw-1.1 / CC-BY-SA-4.0; audio under source licenses | Includes `ar` | — | Training-oriented | **Conditional** | DOCUMENTED |
| MenaSpeechBank (QCRI, 2026) | CC BY-NC-SA 4.0 | Egyptian, Gulf, Levantine, MSA, North African | 26.45 h, 123 speakers | Reference voices | **No** | DOCUMENTED |
| Ramsa (Emirati, 2026) | Not stated | Emirati varieties | 41 h | Interviews and TV | **Unknown** | PARTIAL arXiv:2603.08125 |
| Saudi ASWAT (LREC 2026) | Availability not stated | 5 Saudi regions | Target 2,500 h | Spontaneous | **Unknown** | PARTIAL |

**What this means**
- License-clean public Arabic evaluation data is mostly **read speech**: Common Voice, FLEURS, ClArTTS, DVoice, TunSwitch and the Omnilingual corpus.
- There is **no license-clean Saudi/Gulf conversational test set** and no clean Gulf–English code-switch set.
- So E0 screening (Section 5) can only cover read speech. Product claims need the consented E1 set.

### 4.3 Normalization practices found

| Source | Rules (summary) |
| --- | --- |
| Open Universal leaderboard `eval.py` | Strips `[ً-ْ]` and punctuation incl. ، ؛ ؟; آ/أ/إ→ا; ؤ→و; ئ→ي; deletes standalone ء; پ→ب, ڤ→ف; Eastern digits→ASCII; re-attaches a detached و; keeps Latin. **Ta marbuta, alef maqsura, tatweel and dagger alef are left alone.** NeMo `word_error_rate` |
| Casablanca / NADI 2025 | Remove diacritics; normalise hamza and madda to bare alif; Eastern→Western numerals; keep Latin. Casablanca keeps % and @ |
| NADI 2026 | Official ranking does **not** normalise hamza; a normalised score is reported alongside |
| Arab Voices | NFKD; remove tashkeel and punctuation; alef folding; **ta marbuta→ha; alef maqsura→ya** |
| Whisper `BasicTextNormalizer` | SOURCE_VERIFIED `openai/whisper@86098128:whisper/normalizers/basic.py`. The default (`remove_diacritics=False`) applies NFKC and then replaces every Unicode category M/S/P character **with a space**, so Arabic harakat split diacritised words into fragments and inflate WER. With `remove_diacritics=True` it applies NFKD and drops Mn characters. That silently folds أ/إ/آ/ؤ/ئ to bare letters (verified locally: U+0623 → U+0627 + U+0654). Tatweel (Lm) and Arabic-Indic digits (Nd) are kept unchanged |
| Code-switching references | Casablanca writes foreign words in both scripts. Mixat writes English in Latin script. Hamed et al. (SLT 2022) found transliteration plus normalisation correlates best with human judgment. PolyWER accepts transliterations |

**Consequence:** published Arabic WERs from different benchmarks are not comparable. Wispral must freeze its own normalizer (Section 5.3) and add a leaderboard-compatible level only for side-by-side context.

### 4.4 Qualitative findings

- **Dialect ordering is consistent** across the leaderboard, NADI, Arab Voices, Casablanca and Omnilingual: MSA, then Levantine, Egyptian and Gulf, then Iraqi, then Maghrebi/Hassaniyya.
  - Najdi, Hijazi and Khaleeji perform notably badly in Arab Voices and Omnilingual (claims). Saudi/Gulf is Wispral's priority stratum, so this is the highest-risk gap.
- **Demographic skew:** higher WER is reported for elderly and female speakers (SADA analyses). Casablanca is heavily male-skewed.
- **Whisper-family failure modes:** translating dialect into MSA, hallucination, and non-terminating output (WER above 100%). The Wispral metrics include hallucination and insertion-burst checks for this reason.
- **Code-switching:** severe for zero-shot models.
  - Mixat code-switched segments: Whisper-medium 121.78 WER (paper claim).
  - Casablanca code-switched segments: Whisper-v3 about 90 WER.
  - In-domain adaptation can help a lot (NADI 2026 Tunisian: 14.41), but only with matching data.
- **TTS:** human MOS studies are small. Automatic proxies (UTMOS, NISQA, MSA-biased ASR-WER) disagree with each other. Diacritisation quality drives MSA pronunciation.


## 5. Proposed Arabic/English evaluation protocol (PROPOSED; NOT_RUN)

This section extends, and does not replace, the PROPOSED human-language design in `pr124:research/rea/2026-10-21/BENCHMARK_AND_REPLAY_PROTOCOL.md` (40 speakers / 400 utterances across English, read MSA, natural Saudi and natural non-Saudi Gulf). It is a planning contract. No corpus has been collected, no model has been run, and no number below is a measurement. Every numeric target is either (a) copied from the existing PROPOSED release thresholds and labelled as such, or (b) a planning assumption to be replaced by pilot variance estimates before any held-out confirmation run.

### 5.1 Evaluation tracks (kept separate in every report)

| Track | Purpose | May support a product claim? |
| --- | --- | --- |
| E0 Public-benchmark replay | Re-score open models on commercially usable public sets (Section 4.2 "usable = yes") with Wispral's frozen normalizer, for screening only | No. Screening and sanity checks only; public sets are read/broadcast-biased and some are in model training data (contamination unknown) |
| E1 Consented Wispral held-out set | Speaker-independent, dialect-stratified, product-task recordings with documented consent, retention and withdrawal | Yes, per stratum, after freeze and independent review |
| E2 Synthetic contract replay | Deterministic fixtures (TTS-generated or scripted text) for routing, normalization, cancellation and entity-pipeline invariants | No recognition-accuracy claim (consistent with B1/B2 rule that synthetic/TTS media cannot substitute for human developer speech) |
| E3 Listening study | Blinded, consented native/bilingual listeners rating TTS | Yes, per language/dialect cell rated |
| Frozen B2 | Existing 000B2 English developer-speech experiment | Governed only by its own authority. Not reinterpreted, re-scored, or merged into E0–E3 |

### 5.2 Strata (segmentation)

Speakers self-report dialect, region of upbringing and languages used daily. Never infer dialect from nationality or name. Every utterance carries one primary stratum tag and optional secondary tags.

Arabic primary strata (BCP-47 / ISO 639-3 tags shown for the manifest):

| Stratum | Tag | Notes |
| --- | --- | --- |
| MSA read | `arb` (macro `ar`) | Read scripts; also spontaneous-MSA cell if collected |
| Saudi Najdi | `ars` | Central Saudi |
| Saudi Hijazi | `acw` | Western Saudi |
| Gulf (non-Saudi and eastern Saudi) | `afb` | Kuwait, Bahrain, Qatar, UAE, Oman (Omani `acx` optionally separate), Eastern Province |
| Egyptian | `arz` | Cairene default; Sa'idi (`aec`) separate if collected |
| Levantine | `apc` | ISO 639-3 merged `ajp` into `apc` effective 2023-01-20 (DOCUMENTED, https://www.iana.org/assignments/lang-subtags-templates/apc.txt, accessed 2026-11-08); record country sub-tag (JO/PS/SY/LB) |
| Maghrebi | `ary` / `aeb` / `arq` / `ayl` | Moroccan, Tunisian, Algerian, Libyan reported separately; never pooled into one "Maghrebi" number for a claim |
| Iraqi | `acm` | Mesopotamian; Gulf-influenced southern Iraqi noted |

English strata: US, UK, South Asian, Arab-accented English (Gulf/Levantine/Egyptian L1), other L2. Arab-accented English is a first-class stratum for this product family.

Cross-cutting task tags (each utterance may carry several): `cs` Arabic–English code-switching (intra-sentential vs inter-sentential), `tech` technical vocabulary (developer entities as in WB-ENTITY, product/catalog terms for Klaint), `name` person/place/organisation names (Arabic names in Arabic script and Latin script), `num` numbers (cardinals, ordinals, money, phone numbers, IDs), `date` dates/times (Hijri and Gregorian), `neg` negation (dialect particles such as ما / مش / مو / مب / لا / ماني), `selfcorr` self-correction ("send it Sunday, no, Monday"), `filler` disfluency, `noise` acoustic condition (clean / 20 dB / 10 dB per existing proposal), `farfield`, `telephony` (8 kHz narrowband for Klaint).

### 5.3 Arabic normalization specification (preregister before any scoring)

Score every hypothesis at the preregistered levels below and report all of them. Public benchmarks disagree on ta marbuta, alef maqsura, standalone hamza, و-attachment and Latin handling (Section 4.3), so WERs from different benchmarks are not comparable. The STANDARD level is the primary metric. Do not tune the normalizer on held-out data.

| Level | Operations (applied in order to both reference and hypothesis) |
| --- | --- |
| RAW | Unicode NFC; collapse whitespace; nothing else. Shows script/orthography fidelity |
| STANDARD (primary) | RAW + NFKC for Arabic presentation forms (U+FB50–U+FDFF, U+FE70–U+FEFF) and lam-alef ligatures; remove tatweel U+0640; remove harakat/tanween/shadda/sukun U+064B–U+0652, U+0653–U+065F, dagger alef U+0670 and Quranic marks U+06D6–U+06ED; unify alef variants أ إ آ ٱ (U+0623, U+0625, U+0622, U+0671) → ا (U+0627); map Persian/Urdu look-alikes ک U+06A9 → ك U+0643 and ی U+06CC → ي U+064A; map Arabic-Indic digits U+0660–U+0669 and Extended Arabic-Indic U+06F0–U+06F9 → ASCII 0–9; remove bidi/format controls (U+200B–U+200F, U+061C, U+202A–U+202E, U+2066–U+2069); strip punctuation incl. Arabic comma U+060C, semicolon U+061B, question mark U+061F, full stop U+06D4, and Latin punctuation, except inside protected entity spans; casefold Latin script |
| LENIENT | STANDARD + alef maqsura ى U+0649 → ي U+064A; ta marbuta ة U+0629 → ه U+0647; hamza seats ؤ U+0624 → و and ئ U+0626 → ي; standalone hamza ء U+0621 removed. These are common orthographic disagreements in dialect writing, but they can also change meaning, so LENIENT is a sensitivity analysis, never the headline |
| OUAL-COMPAT (comparability only) | Exact replica of `normalize_arabic_text` in the Open Universal Arabic ASR Leaderboard `eval.py` at a pinned commit (as read by the dataset worker: strips `[ً-ْ]`, ASCII and Arabic punctuation; maps آ/أ/إ→ا, ؤ→و, ئ→ي; deletes standalone ء; پ→ب, ڤ→ف; Eastern digits→ASCII; re-attaches a detached و to the next word; keeps Latin; does NOT touch ta marbuta, alef maqsura, tatweel or dagger alef). Used only to place Wispral numbers next to public leaderboard numbers; never the headline. Commit pin NOT_VERIFIED in this session |

Protected content (never normalized away at any level): negation particles; numbers (compare by canonical value in the entity scorer, see 5.4); named entities; developer/code tokens (case and punctuation preserved inside protected spans, scored by WB-ENTITY rules).

Numbers: references are written in a single preregistered canonical form per stratum (recommend: digits for quantities, dates, phone numbers; words only when spoken as words in an idiom). A deterministic, versioned number-canonicalizer maps spoken-form Arabic/English number words in hypotheses to digits before STANDARD scoring; its version and test fixtures are frozen with the scorer. Report WER with and without canonicalization.

Code-switching and loanwords: English words may legitimately appear in Latin script or as Arabic-script transliteration (for example "meeting" / "ميتنج"). Use multi-reference alternatives for a preregistered loanword list and report a separate script-fidelity rate (share of English-origin reference tokens emitted in the preregistered script). Do not silently transliterate.

Reference transcription guidelines: dialect is transcribed as spoken (CODA-style conventional orthography recommended; record the guideline version), not "corrected" to MSA. Two independent transcribers for the held-out set with adjudication; report inter-annotator CER on a double-transcribed subset.

### 5.4 STT metrics

| Metric | Definition | Notes |
| --- | --- | --- |
| WER / CER | (S+D+I)/N over words / declared character units at RAW, STANDARD, LENIENT | Per speaker, stratum, task tag, noise cell, device, model; completed-attempt and all-attempt denominators (failures count as full deletion in all-attempt) |
| Per-language WER within `cs` utterances | WER computed separately over Arabic-tagged and English-tagged reference tokens | Plus code-switch-point error rate (errors within ±1 token of a switch) |
| Script-fidelity rate | See 5.3 | `cs` only |
| Entity accuracy | Exact-match accuracy over annotated entity spans (names, numbers by canonical value, dates by canonical date, tech tokens by WB-ENTITY rules); substitution/deletion/insertion breakdown | Reported per entity class; Arabic names scored in the script of the reference with a preregistered alternative-spelling list |
| Negation flip rate | Over reference utterances tagged `neg`: share whose hypothesis polarity differs (dropped, inserted or inverted negation), judged by bilingual annotators | Also false-negation-insertion rate over non-`neg` utterances |
| Critical semantic error (meaning distortion) rate | Blinded bilingual annotation per utterance: changed intent, polarity, quantity, named entity, target/path or omitted instruction | Report counts / eligible utterances, inter-annotator kappa, adjudication. LLM-as-judge may be used only as a secondary signal calibrated against human labels (report agreement); never as the sole metric |
| Self-correction resolution | `selfcorr` utterances: raw ASR captures both spans; rewrite stage outputs the corrected intent only | Raw, formatted and intent stages scored separately so the distorting stage is located |
| Hallucination / insertion bursts | Hypothesis text with no aligned reference speech (silence, noise-only and music clips included in the set) | Whisper-family models are known to need this check |
| LID accuracy | Language/dialect label vs. reference when auto-detect is used | Wrong-language decoding counted as an outcome, not excluded |

Latency and resources (per hardware cell id, warm and cold separately, per existing protocol: proposed 100 warm repetitions and 20 cold starts, randomized/interleaved by engine):

- streaming: speech-onset → first partial; last speech sample → final transcript; endpoint-decision latency; partial-revision (flicker) rate = tokens later revised / tokens emitted;
- batch/PTT: release → final, release → accepted text;
- RTF = processing wall time / audio duration; peak RSS, VRAM, disk footprint, threads, CPU utilization; model load time;
- report p50, p90, p95 with sample count, and a bootstrap CI for p95; a p95 from fewer than ~100 samples is labelled exploratory.

### 5.5 TTS, cloning and voice-design metrics

| Metric | Method |
| --- | --- |
| Intelligibility (objective) | ASR round trip: synthesize preregistered scripts, transcribe with at least two fixed, version-pinned ASR systems from different families, report CER/WER at STANDARD normalization against the input text. Because Arabic ASR error confounds this, also have human transcribers transcribe a random subset (proposed ≥10% of clips per cell) and report human-transcription CER |
| Diacritization / pronunciation accuracy | Arabic TTS depends on (often implicit) vocalization. Score a preregistered list of heterophonic words (same undiacritized spelling, different pronunciation by context), names, numbers and dates by native-listener judgment |
| Naturalness | MOS (ITU-T P.800 ACR 5-point) and CMOS (paired, −3..+3) with blinded, consented native listeners of the target dialect; hidden natural-speech references and low anchors; attention checks; loudness-normalized playback |
| Dialect authenticity | Separate 5-point rating "sounds like a native speaker of <dialect>" by listeners from that dialect; prevents MSA-accented output being scored as "natural Gulf" |
| Speaker similarity (cloning) | Objective: cosine similarity between speaker embeddings of reference and output with a pinned, commercially licensed embedding model (record its license); subjective: SMOS / same-different ABX by listeners. Only on consented reference voices with cloning-specific consent |
| Voice-design adherence | Listener rating of match to the text description (age, gender, register, emotion) on a preregistered description set |
| Latency/resources | First generated PCM, first audible output, full RTF, peak RSS/VRAM, warm/cold (as existing protocol) |
| Safety | Watermark presence/detection rate where the engine claims one; refusal/consent-gate behavior is a contract test, not a quality metric |

### 5.6 Consent and licensing rules for evaluation data

1. A dataset is usable for E0 commercial-product screening only if its license or terms permit commercial use (CC0, CC-BY, CC-BY-SA with attribution, Apache/MIT data, or a signed commercial license). CC-BY-NC / research-only / LDC non-member / "academic use" terms are treated as NOT usable for evaluating or selecting models for a commercial product, even internally, unless written permission is obtained (Section 4.2 lists per-dataset status).
2. Results on non-commercial datasets must not appear in marketing or product claims.
3. E1 recordings require: identified purpose (ASR evaluation, optionally training — separate checkbox), retention period, withdrawal path that removes the speaker from future runs, no publication of raw audio by default, and separate opt-in for (a) redistribution in a public benchmark and (b) use as a TTS/cloning reference. Transcription consent does not cover voice cloning or speaker-similarity tests (consistent with the existing register).
4. Speaker metadata stored as pseudonymous IDs; dialect labels self-reported; no names, no national IDs.
5. TTS listening tests: listeners consent to participation; clips from cloned voices only from consented reference speakers; no real public figures.
6. Model licenses are checked for evaluation as well as deployment (some community licenses restrict even internal commercial evaluation once revenue thresholds are met — see the Moonshine Community License row in Sections 2.1 and 2.15).

### 5.7 Minimum sample sizes and statistics

Planning minima (to be revised from pilot variance, never lowered after held-out data is seen):

| Item | Planning minimum | Rationale |
| --- | --- | --- |
| Speakers per Arabic dialect stratum (held-out) | 20 (balanced gender, ≥2 age bands) | Speaker-cluster bootstrap needs enough clusters; existing proposal of 10 per stratum treated as pilot-scale only |
| Reference words per stratum | ≥ 3,000 STANDARD-normalized words (≈ 20–30 min of speech) | Stabilizes stratum WER; per-speaker 25–40 utterances |
| Utterances per cross-cutting tag per stratum (`neg`, `num`, `name`, `selfcorr`, `cs`) | ≥ 100 eligible items | Rate estimates with ±~6–10 point 95% CI at moderate rates; zero-failure upper bound ≈ 3/n = 3% |
| Critical-error gate items | ≥ 300 eligible utterances per claimed stratum | Zero observed critical errors then gives a one-sided 95% upper bound ≈ 1% (rule of three), matching "zero unreviewed critical distortion reaches an action" intent |
| Speakers for a paired model comparison | n ≈ ((z₁₋α/₂ + z₁₋β)·σ_d / δ)²; e.g. σ_d = 5 WER points (assumption), δ = 3 points, α = 0.05, power 0.8 → ≈ 22 speakers | Replace σ_d with pilot estimate of between-speaker SD of paired WER differences |
| Listening study per language/dialect cell | ≥ 24 qualified native listeners, ≥ 30 sentences per system, each listener ≥ 40 trials; existing threshold of ≥ 20 listeners across a panel is kept as the floor | Listener and sentence variance both matter |
| Performance cells | 100 warm + 20 cold runs per engine × hardware cell (existing proposal) | p95 with bootstrap CI |

Statistics:

- Confidence intervals: speaker-level cluster bootstrap (resample speakers with replacement; ≥ 10,000 replicates; record seed) for WER/CER and rate metrics; Wilson or Clopper–Pearson intervals for pooled proportions only when items are independent.
- Paired model comparisons on identical clips: speaker-level paired bootstrap of the WER difference, plus a speaker-level sign-flip permutation test or Wilcoxon signed-rank on per-speaker differences; NIST MAPSSWE as an utterance-level secondary.
- Listening tests: linear mixed-effects (or cumulative-link mixed) model with random intercepts for listener and sentence; report fixed-effect contrasts with 95% CI; CMOS analysed as paired.
- Multiple comparisons: Holm–Bonferroni across the preregistered family of (model × stratum) comparisons; exploratory comparisons labelled exploratory.
- Report per-stratum results and worst-stratum results; never only a pooled mean. A pooled "Arabic WER" is not reported without its per-stratum breakdown.
- Split discipline: development speakers (normalizer, prompts, biasing lists, decision-function tuning) are disjoint from held-out speakers; held-out set is decoded only after the attempt manifest is frozen (mirrors the 000B1/B2 gate discipline).

---

## 6. Routing policy (PROPOSED)

Consistent with `pr124:docs/strategy/WISPRAL_MODEL_ROUTING_CONTRACTS.md`: one modality interface per runtime, one selected provider per request, explicit per-workspace/per-tenant configuration, no unapproved network or paid fallback, and no route promotes confidence to action authority.

### 6.1 Selection inputs

| Input | Values |
| --- | --- |
| Product / task | `side.dictation.stream`, `side.dictation.ptt`, `side.rewrite`, `studio.tts.preset`, `studio.tts.clone`, `studio.voice_design`, `studio.dub.asr`, `studio.dub.align`, `studio.dub.translate`, `studio.diarize`, `studio.enhance`, `klaint.asr.stream`, `klaint.turn`, `klaint.tts.stream`, `klaint.llm.agent`, `klaint.llm.rewrite` |
| Language policy | Declared language/dialect (BCP-47, e.g. `ar-SA` + dialect tag `ars`), declared set for auto-detect, or `en` |
| Device capability profile | Measured at install: OS, arch, CPU model/ISA (AVX2/AVX-512/NEON), physical cores, RAM total/available, GPU vendor/VRAM/driver, NPU; mapped to a tier below |
| Privacy mode (per workspace/tenant, explicit) | `OFFLINE_ONLY` (no network after admitted artifact staging); `LOCAL_PREFERRED` (local only unless the user approves a specific provider route for a specific purpose); `PROVIDER_APPROVED` (a named provider route is approved for named data classes and purpose) |
| License class of candidate | `PERMISSIVE` (MIT/Apache/BSD/CC0/CC-BY), `ATTRIBUTION_OR_TERMS` (e.g. Gemma Terms, Llama Community License, NVIDIA Open Model License — commercial allowed with conditions), `COPYLEFT` (GPL/AGPL/MPL — distribution obligations), `REVENUE_CAPPED` (e.g. Moonshine Community, LFM Open License), `NON_COMMERCIAL` (CC-BY-NC*, CPML, research-only), `UNKNOWN` |
| Measured status | Per (model artifact digest × task × stratum × hardware cell): `QUALIFIED` (frozen E1/E3 evidence id), `SCREENED` (E0 only), `UNQUALIFIED`, `REJECTED` (with reason) |

### 6.2 Device tiers

| Tier | Definition | Planning budget (to be replaced by measured RSS) |
| --- | --- | --- |
| R0 (reference cell) | Intel Core i5-13420H laptop, 16 GB RAM, no discrete GPU, Windows 11 (machine as specified by the coordinator; core count/ISA not re-verified in this session: NOT_VERIFIED) | First frozen performance cell; planning budget as T1. GPU-class candidates are BLOCKED_EXTERNAL on R0 and must not be extrapolated from it |
| T0 | CPU-only, 8 GB RAM, x86-64 AVX2 or ARM64 (no qualified hardware cell yet: BLOCKED_EXTERNAL) | All concurrently resident models ≤ ~2.5 GB RSS (STT + VAD + optional rewrite LLM), leaving OS/browser/editor headroom. Rewrite LLM optional and off by default on T0 |
| T1 | CPU-only, 16 GB RAM | ≤ ~6 GB resident |
| T2 | Apple Silicon unified memory ≥ 16 GB | Metal/MLX/Core ML paths measured separately from CPU |
| T3 | Discrete GPU ≥ 8 GB VRAM (desktop) | VRAM-resident models; CPU fallback is an explicit route, not silent |
| T4 | Server GPU (Klaint/Studio self-hosted; 24–80 GB VRAM) | Concurrency-dependent; measured per deployment |

### 6.3 Selection algorithm

```
eligible = candidates where
    task in manifest.tasks
  and license_class allowed for (product, distribution_mode)        # NON_COMMERCIAL, UNKNOWN never in commercial routes;
                                                                    # REVENUE_CAPPED excluded by default; COPYLEFT only via
                                                                    # an approved distribution route (separate process/worker, source offer)
  and privacy_mode permits manifest.network_requirement             # OFFLINE_ONLY => network_at_inference == none
  and device_tier satisfies manifest.measured_requirements[tier]    # measured RSS/VRAM/RTF on that tier, not publisher claims
  and language stratum status in {QUALIFIED} for GA,
      or {QUALIFIED, SCREENED} for an explicitly labelled "experimental language" toggle the user turned on
  and consent prerequisites met (voice cloning: consent record for this exact reference artifact and purpose)
  and paid == false, or (paid == true and user approved this route, cost display shown, budget cap set)

if eligible is empty:
    return PROVIDER_UNAVAILABLE(reason codes, user actions: e.g. "download local model X (size)", "approve provider Y for purpose Z")
    # never silently fall back to another provider, to cloud, or to a lower-quality language

route = argmax over eligible of product decision function (preregistered, below)
pin route to workspace/tenant; any change is explicit, logged, and never mid-session or mid-render
```

Product decision functions (lexicographic, preregistered before E1 runs):

| Product/task | Constraint (must pass) | Then minimize | Tie-breakers |
| --- | --- | --- | --- |
| WisprSide dictation | Latency budget (existing PROPOSED: warm p95 release-to-final ≤ 1.5 s, release-to-accepted ≤ 2 s on reference device) and RSS within tier | Critical semantic error rate (stratum of the user's declared dialect) | STANDARD WER → entity accuracy → RSS → disk |
| WisprSide rewrite | Never changes meaning (critical-error rate on rewrite stage ≤ gate), preserves code-switch script, raw text always retained | Manual-correction rate | Latency → RSS |
| Studio TTS | License `PERMISSIVE`/`ATTRIBUTION_OR_TERMS` for the shipped artifact; language cell QUALIFIED | Critical pronunciation error rate | MOS → dialect authenticity → RTF |
| Studio cloning | Consent record valid; license allows cloning use; watermark policy satisfied | Speaker-similarity shortfall subject to intelligibility gate | MOS → RTF |
| Klaint streaming ASR | Telephony/8 kHz cell qualified for the tenant's dialects; endpoint latency budget | Critical semantic error rate (entities: account numbers, dates, amounts) | WER → cost per audio hour (self-hosted compute) |
| Klaint turn detection | False-cutoff rate ≤ gate on the tenant's language cell | End-of-turn latency | CPU cost |
| Klaint LLM | Tool-call schema validity ≥ gate; zero broker-blocked unauthorized-action attempts that reach execution (always enforced outside model) | Task-failure rate on frozen synthetic scenarios in the tenant's language | Arabic dialect appropriateness rating → latency → cost |

Hard rules:

1. No hidden cloud fallback. A failed local route returns `PROVIDER_UNAVAILABLE` with the raw text/audio retained locally.
2. No automatic paid inference. Any provider route is disabled by default; enabling it requires an explicit, purpose-scoped approval, a visible cost model, and a budget cap; exhaustion stops the route rather than switching provider.
3. No language downgrade without consent: an Arabic-dialect request is never silently routed to an English-only or MSA-only model; the user is told the route is "experimental" or "unavailable for this dialect".
4. NON_COMMERCIAL / UNKNOWN-license weights never appear in a commercial route or default bundle; they may run only in an explicitly labelled research workspace with no customer data.
5. Every request/result binds route id, model id, artifact digest (or `PROVIDER_MANAGED_DIGEST_UNAVAILABLE`), config digest, consent/policy version (existing contract).

### 6.4 Capability manifest schema (fields)

Proposed `wispral-model-capability-v1` (JSON). Required unless marked optional. Unknown values are explicit enums, never defaults.

```json
{
  "schema_version": "wispral-model-capability-v1",
  "model_id": "org/name",
  "family": "e.g. moonshine | whisper | parakeet | chatterbox | qwen3",
  "variant": "e.g. tiny-streaming-ar",
  "modality": "asr | vad | turn | diarization | enhancement | lid | tts | vc | voice_design | st | alignment | llm",
  "tasks": ["side.dictation.stream"],
  "source": {
    "upstream_url": "https://...",
    "code_repo": "owner/repo", "code_revision": "full-sha", "code_license_spdx": "MIT", "code_license_url": "https://...",
    "weights_host": "huggingface | vendor-cdn | provider", "weights_revision": "full-sha-or-PROVIDER_MANAGED",
    "release_date": "YYYY-MM-DD", "last_upstream_activity": "YYYY-MM-DD", "archived": false
  },
  "artifacts": [{"path": "file", "size_bytes": 0, "sha256": "hex-or-PENDING", "role": "encoder|decoder|tokenizer|config|voice"}],
  "weight_license": {
    "id": "SPDX-or-custom-id", "url": "https://...", "text_sha256": "hex",
    "class": "PERMISSIVE | ATTRIBUTION_OR_TERMS | COPYLEFT | REVENUE_CAPPED | NON_COMMERCIAL | UNKNOWN",
    "commercial_use": "yes | conditional | no | unknown",
    "conditions": ["attribution", "revenue_cap_usd", "mau_cap", "acceptable_use_policy", "naming_requirement", "watermark_required", "registration_required", "no_eu_multimodal"],
    "gated": false, "evidence": "DOCUMENTED url+date | SOURCE_VERIFIED repo@sha:path"
  },
  "languages": [{
    "tag": "ar | arb | ars | acw | afb | arz | apc | ary | aeb | arq | acm | en-US ...",
    "claim_source": "publisher | wispral_measured",
    "publisher_claim_quote": "<=15 words", "publisher_claim_url": "https://...",
    "status": "QUALIFIED | SCREENED | UNQUALIFIED | REJECTED", "evidence_ids": []
  }],
  "capabilities": {
    "streaming_class": "NATIVE_INCREMENTAL | CHUNKED_REDECODE | BATCH_ONLY | UNKNOWN",
    "streaming_evidence": "DOCUMENTED_NOT_OBSERVED | OBSERVED",
    "sample_rates_hz": [16000], "telephony_8khz": "unknown",
    "max_input_seconds": null,
    "timestamps": "none | segment | word", "punctuation": true, "lid": false,
    "context_biasing": "none | prompt | hotwords | keyterms",
    "tts": {"preset_voices": 0, "zero_shot_clone": false, "voice_design": false, "style_control": false, "watermark": "none | perth | other"},
    "llm": {"tool_calling": "native | template | none", "max_context_tokens": 0, "structured_output": false}
  },
  "runtime": {"engine": "onnxruntime | ggml | ctranslate2 | pytorch | mlx | coreml | nemo | provider_api",
              "engine_version": "exact", "execution_providers": ["cpu"], "quantization": "fp32 | fp16 | int8 | q4_k_m ..."},
  "measured_requirements": [{"hardware_cell_id": "id", "tier": "T0", "peak_rss_bytes": null, "vram_bytes": null,
                             "rtf_p50": null, "rtf_p95": null, "load_ms_cold": null, "evidence_id": "NOT_RUN"}],
  "privacy": {"network_at_inference": "none | provider", "network_at_install": "artifact_download | none",
              "provider_data_retention": "n/a | documented-url", "paid": false, "cost_model_url": null},
  "consent_requirements": ["voice_reference_consent", "speaker_similarity_consent"],
  "product_status": {"side": "CANDIDATE | QUALIFIED | REJECTED | DEPRECATED", "studio": "...", "klaint": "..."},
  "known_limitations": ["text"],
  "reviewed": {"by": "identity-or-NOT_RUN", "date": "YYYY-MM-DD"}
}
```

Nulls above are type placeholders, not measurements.



### 6.5 Initial candidates to BENCHMARK (not winners)

These are candidates to benchmark, not selections. Everything here is NOT_RUN.

- Each benchmark needs its own READY Grain, frozen manifest and pinned artifact digests.
- Each needs a license re-check at attempt time.
- **Primary hardware cell:** R0 (i5-13420H, 16 GB, no dGPU, Windows 11).
- Rows marked "GPU cell" are BLOCKED_EXTERNAL until a GPU host exists. Do not extrapolate to them from R0.
- **None of this modifies, extends or re-scores the frozen B2 experiment.** New cells belong to a new Grain.

**Why these candidates:**
- (a) Weight license class is PERMISSIVE.
- (b) A documented Arabic or dialect claim, or a documented role in the English baseline.
- (c) A documented CPU path, or a reason to measure feasibility.
- (d) Upstream maintenance.
- (e) A mix of architectures (streaming transducer, encoder–decoder, CTC, audio-LLM) so the decision function has real alternatives.

#### WisprSide (dictation) on R0

| Task | Candidates | Rationale / risk |
| --- | --- | --- |
| Arabic streaming STT | 1. Moonshine Arabic Tiny Streaming (MIT, 34M)<br>2. Voxtral-Mini-4B-Realtime-Arabic via its community ONNX export (Apache-2.0)<br>3. Qwen3-ASR-0.6B streaming path (Apache-2.0) | (1) Smallest native streaming model with an Arabic claim; same runtime family as B2.<br>(2) Only open streaming model with explicit Saudi/Gulf dialect tags. Measure RTF on R0 first; likely too heavy, so record as infeasible rather than drop silently.<br>(3) Arabic listed; the CPU streaming path is NOT_VERIFIED |
| Arabic PTT / batch STT | 4. whisper large-v3-turbo via whisper.cpp quantized (MIT)<br>5. Omnilingual CTC 300M/1B v2 (Apache-2.0)<br>6. NVIDIA `stt_ar_fastconformer_hybrid_large_pcd_v1.0` (CC-BY-4.0)<br>7. Fun-ASR-MLT-Nano (Apache-2.0) | (4) Widely used baseline; known dialect→MSA translation risk.<br>(5) Per-dialect claims exist; 40 s input limit.<br>(6) Arabic-specific CTC/transducer; ONNX export path NOT_VERIFIED.<br>(7) Arabic listed; size and CPU path NOT_VERIFIED |
| Arabic reference ceiling (GPU cell) | Jais-ASR (Apache-2.0); Cohere transcribe Arabic (Apache-2.0, gated) | Leaderboard leaders. Bound what is achievable before any fine-tune decision (Section 7). Cohere needs user gate acceptance |
| English STT | Frozen B2 cells stay as is; a separate Grain may add Parakeet-TDT-0.6B-v2/v3 (CC-BY-4.0) via sherpa-onnx and whisper large-v3-turbo | English quality reference outside B2 |
| VAD | Silero VAD (MIT) | Small, MIT; TEN VAD excluded on license |
| Rewrite LLM (Arabic + English, code-switch preservation) | Qwen3.5-4B, Qwen3-4B-Instruct-2507, Gemma 4 E4B, Jais-3-3.7B, Ministral-3-3B, Phi-4-mini, Granite-4.2-3B (4-bit GGUF/ONNX) | All Apache/MIT per card. Jais 3 is Arabic-centric. Measure meaning preservation first: a rewrite that changes meaning fails regardless of fluency. Gemma 4 terms need a final read |

#### WisprStudio on R0 (+ GPU cell)

| Task | Candidates | Rationale / risk |
| --- | --- | --- |
| Arabic TTS (preset) | Chatterbox Multilingual V3 (MIT; watermark; unmaintained); `silma-ai/silma-tts` (Apache-2.0 metadata, lineage NOT_VERIFIED); Piper Arabic voice via piper1-gpl or the Moonshine TTS path (per-voice license NOT_VERIFIED; GPL runtime isolated) | The only commercially plausible Arabic options found. All are MSA-leaning; dialect authenticity is unknown |
| English TTS (preset) | Kokoro-82M (Apache-2.0); Chatterbox Nano/Turbo (MIT); VibeVoice-Realtime-0.5B (MIT); Qwen3-TTS-0.6B (Apache-2.0); Pocket TTS (CC-BY-4.0, gated) | Range of CPU-friendly to quality-oriented options |
| Cloning (consented) | Chatterbox Multilingual V3 (Arabic + English); Qwen3-TTS Base and CosyVoice 3 (non-Arabic) | Consent record per reference artifact; watermark recorded |
| Voice design | Qwen3-TTS VoiceDesign (non-Arabic only) | Arabic voice design has no permissive candidate. Record as a gap (FT-5) |
| Dubbing pipeline | ASR (as Side) → human-reviewed transcript → LLM MT (Apache LLM) → human review → TTS; alignment via Omnilingual CTC segmentation or NeMo aligner with Arabic FastConformer (NOT_VERIFIED); separation via Demucs (weights license NOT_VERIFIED) | Each stage auditable. Qwen3-ForcedAligner excluded for Arabic (not supported) |
| Diarization | Sortformer streaming v2 (CC-BY-4.0); pyannote community-1 (CC-BY-4.0, gated: user must accept) | DiariZen REJECTED (NC) |
| Enhancement | RNNoise (BSD-3); DeepFilterNet (license NOT_VERIFIED) | — |

#### Klaint

| Task | Candidates | Rationale / risk |
| --- | --- | --- |
| Streaming Arabic ASR (telephony 8 kHz cell required) | GPU cell: Voxtral-Mini-4B-Realtime-Arabic, Qwen3-ASR-1.7B streaming. R0: Moonshine Arabic Tiny | Telephony quality is NOT_VERIFIED for all of them. LDC CTS sets need membership |
| Turn detection | smart-turn v3.2 (BSD-2, Arabic listed) + Silero VAD | LiveKit and TEN turn models excluded until licenses are read |
| Streaming TTS | Chatterbox Multilingual V3 (GPU); Piper Arabic (CPU) | Both weak on dialect evidence |
| Agent LLM | R0 text-only cells: Jais-3-7B, Qwen3.5-9B, Granite-4.2-8B, ALLaM-7B, Fanar-1-9B (4K context limit) at Q4. GPU cell: Qwen3.5/3.6-35B-A3B, Gemma 4 26B-A4B/31B, Fanar-2-27B, Jais-3-32B or MoVA-36B-A4B, gpt-oss-20b, Mistral Small 4 | All Apache-2.0 per card except where noted. Arabic tool-use reliability is unmeasured everywhere |
| Optional provider | Only with explicit tenant approval, cost display and cap | Disabled by default |

---

## 7. When fine-tuning or a Wispral-owned model is justified (triggers only; no training in this mission)

Preconditions (all required before a fine-tune Grain may be proposed):

- P1. A frozen, consented E1 held-out set exists for the affected stratum (Section 5.7 minima), with frozen normalizer/scorer and independent review.
- P2. The best eligible open, commercially licensed candidate has been measured with every cheap mitigation the routing contract allows: forced language/dialect, VAD/segmentation tuning, backend-native context biasing (prompt / hotwords / keyterms), user/tenant vocabulary, constrained LLM post-correction that cannot change meaning (measured separately), the largest model that fits the device tier, and (only if the user approved a no-cost provider route) a provider reference to bound what is achievable.
- P3. Rights: base-model license permits fine-tuning and commercial distribution of derivatives (Apache/MIT/CC-BY; Gemma/Llama terms carry obligations forward; NC/CPML/revenue-capped excluded); training audio/text has commercial-training consent separate from evaluation consent; tenant data never used for a shared model without contract and opt-in; per-tenant adapters isolated.

Triggers (any one, on held-out data, with speaker-cluster bootstrap 95% CI):

| ID | Trigger | Proposed condition (planning values for approval) |
| --- | --- | --- |
| FT-1 Dialect accuracy gap | Stratum WER fails the release gate and is far from MSA | STANDARD WER for stratum S > its PROPOSED release gate (existing proposal: ≤ 20% per Saudi/Gulf stratum; ≤ 12% MSA) with the CI lower bound above the gate, AND WER_S − WER_MSA ≥ 10 absolute points with CI lower bound ≥ 5 points, after all P2 mitigations |
| FT-2 Meaning-distortion gap | ASR-attributable critical errors (negation, numbers, names) | Critical semantic error rate for S > 2% of eligible utterances with CI lower bound > 1%, or > 2× the English-stratum rate, after P2 mitigations, with errors attributed to the ASR stage (not rewrite) |
| FT-3 Code-switching gap | Arabic–English mixing degrades badly | `cs` WER exceeds same speakers' monolingual Arabic WER by ≥ 8 points (CI lower bound ≥ 4), or script-fidelity < 90% |
| FT-4 Device-tier gap | Only models that miss T0/T1 budgets pass quality | Every candidate meeting FT-1/FT-2 gates exceeds the T0 memory budget by ≥ 2× or has warm p95 latency > budget, AND a distillation/fine-tune of a smaller permissive model is technically plausible (dev-split pilot) |
| FT-5 License gap | Capability exists only under NC/revenue-capped weights | No PERMISSIVE/ATTRIBUTION_OR_TERMS model reaches the gate for a required language/modality (e.g., Gulf-dialect TTS) while NC models demonstrate feasibility → justifies a fine-tune of a permissive base or an owned model on owned/licensed data |
| FT-6 Domain-vocabulary gap | Product entities fail despite biasing | Entity exact-match accuracy for preregistered domain classes < 90% (planning value) after biasing and tenant vocabulary, with a legitimate consented in-domain corpus available |

Acceptance of a fine-tune (future Grain): improvement on the target stratum with CI excluding zero, and no regression beyond a preregistered non-inferiority margin (proposal: ≤ 0.5 WER points English, ≤ 1 point other Arabic strata) — forgetting check is mandatory. A Wispral-owned model (from scratch or continued pre-training) is justified only if FT-5 holds, or FT-1/FT-2 persist across ≥ 2 strata after a fine-tune attempt, and a costed data plan with commercial-training rights exists. Stop rule: if a dev-split pilot does not reach at least half of the targeted gap closure, do not proceed to held-out confirmation.

---

## 8. Klaint LLM requirements (PROPOSED)

Authority boundary (non-negotiable, enforced outside any model):

- The LLM never authorizes spending, refunds, payments, credential use/reset, account-ownership changes, cross-tenant access, data export/deletion, outbound calls/messages to new destinations, or any irreversible action. It may only emit a structured proposal; a deterministic broker validates tenant binding (from the authenticated session, never from model text), tool allowlist per tenant, argument schema, idempotency key, rate/spend caps and authorization freshness, and routes irreversible/financial/credential actions to explicit human or verified-customer confirmation through an out-of-band channel.
- Model confidence, eager end-of-turn events and "the customer said yes" in transcript text are never authorization.
- Retrieved knowledge and tool output are untrusted data (prompt-injection fixtures in KL-F1 apply).

Capability requirements to evaluate (NOT_RUN):

| Requirement | Metric |
| --- | --- |
| Tool-call correctness | Exact match of tool name + arguments; JSON-schema validity rate; parallel/multiple-call accuracy (BFCL-style categories) |
| Abstention | Irrelevance detection / asking for missing required fields instead of fabricating (When2Call-style) |
| Multi-turn task success and consistency | tau-bench / tau2-bench-style pass^k on synthetic customer domains, re-authored in MSA and target dialects with native review |
| Arabic dialect competence | Understanding of Gulf/Saudi, Egyptian, Levantine customer turns; response register appropriateness (MSA vs dialect per tenant policy) rated by native annotators |
| Grounding | Unsupported-claim rate against the tenant KB |
| Safety | Attempted unauthorized actions (must be 100% blocked by broker; attempt rate itself is a model-quality signal), injection-following rate, cross-tenant leakage (must be zero) |
| Latency/cost | Time-to-first-token and full-turn latency at target concurrency on T4; tokens per turn |

### 8.1 Klaint model candidates and evidence sources

- **Open candidates:** Section 2.14, with GPU/R0 split in Section 6.5. Apache-2.0 per card with documented tool calling: Qwen3.5/3.6/3.8-27B, Gemma 4 (pending the terms read), Jais 3, Fanar-2-27B, Ministral 3 / Mistral Small 4, Granite 4.2, gpt-oss-20b.
- **Arabic-centric options:**
  - Jais 3 (Apache-2.0, tool-call parser documented, sizes 0.9B to 375B-A23B).
  - Fanar-2-27B (Apache-2.0, tool calling documented).
  - ALLaM-7B (Apache-2.0, preview).
  - Dialect specialists Nile-Chat (Egyptian, also Arabizi) and Atlas-Chat (Darija), both under the Gemma license.
- **Local vs provider:**
  - Local on R0 is realistic only for text-only experiments with 3–9B models at 4-bit.
  - Production voice-agent latency and concurrency need a GPU host (BLOCKED_EXTERNAL here) or an explicitly approved provider.
  - Provider routes are opt-in per tenant and purpose. They are never a fallback, never automatic, and never paid without approval and a cap.
- **Benchmark methodology to adapt** (licenses and terms of these benchmarks are NOT_VERIFIED this session because the LLM worker stopped; verify before reuse):
  - Berkeley Function Calling Leaderboard categories: simple, multiple, parallel, irrelevance.
  - tau-bench / tau2-bench: pass^k on simulated customer-service domains.
  - When2Call: abstention.
  - Open Arabic LLM Leaderboard / BALSAM / AraTrust: Arabic knowledge and safety.

  None of these measures Arabic-dialect tool use. Wispral must author its own consented, native-reviewed Arabic scenario set. Translated English scenarios must be adapted by native speakers, not machine-translated and then scored.
- **Decision rule:** a model that scores well on tool-call accuracy is still never granted authority. The broker contract (Section 8) is evaluated independently, with 100% enforcement required regardless of model.

## 9. Gaps, blocked items and next smallest steps

| Item | State | Smallest next step |
| --- | --- | --- |
| All quality, latency and RSS numbers for Wispral | NOT_RUN | Open a Grain for R0 E0 screening on license-clean read sets (CV ar, FLEURS ar_eg, DVoice, TunSwitch) with the frozen normalizer. Screening only |
| Consented Arabic dialect / code-switch held-out set (E1) | BLOCKED_EXTERNAL (no corpus, consent or manifest) | Approve consent text and corpus manifest per Section 5.6/5.7; recruit by self-reported dialect |
| GPU cell (Jais-ASR, Voxtral Realtime Arabic, Qwen3-ASR-1.7B, agent LLMs, Chatterbox speed) | BLOCKED_EXTERNAL (no GPU) | Freeze one GPU cell definition; no extrapolation from R0 |
| 8 GB T0 cell | BLOCKED_EXTERNAL | Reserve hardware or keep T0 support claims absent |
| Gated models (pyannote, Cohere transcribe, Pocket TTS, Orpheus) | BLOCKED_EXTERNAL (user must accept terms) | The founder decides whether to accept; record terms text and hash |
| Licenses NOT_VERIFIED | Gemma 4 terms text; LiveKit model license; TEN Turn Detection; IndexTTS-2; Higgs Audio v2 weights; Fish OpenAudio S1-mini; Piper Arabic per-voice cards; Moonshine TTS Arabic assets (AraBERT tashkeel, Piper voice); silma-tts lineage; Audar community license; Qwen community license; LFM `lfm1.0` threshold; Falcon LLM license; Llama licenses; DeepFilterNet; Demucs weights; WeSpeaker/3D-Speaker weights; ctc-forced-aligner default weights; Jais 2; Command R7B Arabic; Voxtral TTS reference voices | Read each license file at a pinned revision, record text SHA-256 in the capability manifest; UNKNOWN stays excluded meanwhile |
| Dataset license conflicts | SADA (CC BY vs CC BY-NC-SA), ArVoice (CC-BY vs NC-SA badge), Arabic Speech Corpus footer, ArzEn terms | Written clarification from the publishers; treat as NC until resolved |
| LDC CTS (Gulf/Iraqi/Levantine telephony) | Requires LDC for-profit membership (a purchase decision, outside this mission) | Founder decision only; no purchase implied |
| Open Universal leaderboard normalizer commit pin | NOT_VERIFIED | Pin the `eval.py` commit before using OUAL-COMPAT |
| Benchmark licenses for BFCL / tau2-bench / When2Call | NOT_VERIFIED | Verify before copying any fixtures |

## 10. Explicit non-claims

This report does not establish:

- any model's accuracy, latency or resource use on Wispral hardware;
- Arabic or dialect support for any Wispral product;
- a winner in any modality;
- that any listed license has been legally reviewed;
- any voice right;
- any change to the frozen B2 experiment or its B2R17 state.

Publisher and leaderboard numbers are quoted only as dated claims under the publisher's own normalization and test sets.

## Appendix A. Machine-readable evidence captured this session (scratchpad `research/workers/`)

- `hf_model_meta.tsv`, `hf_newcomers_meta.tsv`: Hugging Face API card metadata (full revision SHA, license fields, gated flag, created and modified dates, Arabic tag presence) for about 95 models, accessed 2026-11-08.
- `hf_recent_by_org.txt`: newest models per relevant org (discovery list for 2025–2026 releases).
- `gh_repo_meta.tsv`: GitHub SPDX license, stars, last push, archived flag for 52 repos. `repo_heads.txt`: default-branch head SHAs used for SOURCE_VERIFIED reads.
- `moonshine_LICENSE.txt`, `moonshine_README.md`: `moonshine-ai/moonshine@d8d8fa29d05ca67441a7719e70099f9f48917a93`.
- `models/readme/*.md`: model-card README captures for about 60 LLMs (the LLM worker's output; revision SHAs not recorded, so cite as DOCUMENTED with access date only).
- `draft_design_sections.md`: source of Sections 5–8.

## Appendix B. Key SOURCE_VERIFIED anchors

- `moonshine-ai/moonshine@d8d8fa29d05ca67441a7719e70099f9f48917a93`: `LICENSE` (MIT default; Community License list incl. Arabic Base/Tiny; US$1M revenue clause); `docs/models/available-models.md` and `docs/models/accuracy.md` (Arabic Tiny Streaming 34M MIT, 15.5% WER claim); `core/moonshine-tts/data/README.md` and `ar_msa/README.md` (TTS assets licensed per their own readmes; AraBERT tashkeel ONNX)
- `resemble-ai/chatterbox@ab55923c27757c90cfcc407baa57dc25a7d25217:README.md`: retired Aug 2026; Multilingual V3 languages incl. Arabic; PerTh watermark
- `QwenLM/Qwen3-ASR@7c6daf77a2421100f5fb066495372c00129d39ff:README.md`: 30 languages incl. Arabic; ForcedAligner 11 languages without Arabic
- `QwenLM/Qwen3-TTS@022e286b98fbec7e1e916cb940cdf532cd9f488e:README.md`: 10 languages, no Arabic
- `QwenAudio/CosyVoice@074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc:README.md`: 9 languages, no Arabic
- `facebookresearch/omnilingual-asr@81f51e224ce9e74b02cc2a3eaf21b2d91d743455`: `README.md` (Apache-2.0 code and models; 40 s limit), `LICENSE`, `per_language_results_table_7B_llm_asr.csv`
- `pipecat-ai/smart-turn@4786657e242dfe77dd138699ac564ee074a2a543:README.md`: v3.2, BSD-2, 23 languages incl. Arabic, 8M params
- `TEN-framework/ten-vad@8843b97555afa4359d319831b6c3a52e6377b0fc:LICENSE`: Apache-2.0 plus Agora non-compete conditions
- `openai/whisper@86098128c0b4f24f0e2aa2994de830614b474227:whisper/normalizers/basic.py`: diacritic-to-space behavior and NFKD hamza folding
- IANA Language Subtag Registry (File-Date 2026-09-17): ars, acw, afb, arz, apc (Levantine; ajp deprecated 2023-03-17 → apc), ary, aeb, arq, acm, ayl, arb, acx all present
