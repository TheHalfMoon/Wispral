# WisprStudio lead-donor comparison: VoiceStudio versus Voicebox (ST-D00b)

**Grain:** `ST-D00b` (Specification 000E). Packet in `research/wispral-world-class/packets.json`.
**Date:** 2026-11-09.
**Execution:** pure static analysis. Nothing from either tree was built, installed or run.

| Donor | Pin | Files at pin | Licence at pin |
| --- | --- | --- | --- |
| VoiceStudio (current lead) | `debpalash/VoiceStudio@200286ccff6f28faaf51bb08b2a5b54c460b39f4` | 4,694 | AGPL-3.0-only |
| Voicebox (challenger) | `jamiepine/voicebox@8af7efe62fab8d33e2a5dfbedabaa45f68a5184f` | 633 | MIT |

## Method

- **Acquisition.** Each pin was fetched with `git fetch --depth=1` into a bare repository. Nothing was checked out or executed, and the trees were treated as untrusted data.
- **Analysis.** Each tree was read only through `git ls-tree`, `git grep` and `git show`, by two read-only analysis agents, one per tree, given the same rubric and output format. Each agent was told to cite `path:line` only after checking it, and to mark anything unchecked NOT VERIFIED.
- **Author spot-checks.** The author re-read these citations in the bare repositories, and all matched:
  - VoiceStudio: the default-on watermark (`backend/services/watermark.py`, `is_enabled` defaults `True`); the `resume.json` long-form manifest (`backend/services/longform_resume.py:1-13`); the licence-acceptance gate (`backend/services/model_acceptance.py:1-6`); the yt-dlp URL ingest (`backend/api/routers/dub_core.py:967-972`); the consent migration ("plain local synthesis never does", `backend/migrations/versions/0003_voice_profile_consent.py:9-11`).
  - Voicebox: the update check on launch (`app/src/App.tsx:99`); the retry engine fallback `gen.engine or "qwen"` (`backend/routes/generations.py:179`); the MIT `LICENSE`; a `consent` grep in `backend/` and `app/src/` that matches only Italian UI strings.
- **Limits.**
  - This is static analysis, so behaviour is NOT RUN; ST-D00 measures it.
  - The weight licences are as recorded inside each tree, not checked against model cards.
  - Line numbers are at the pins.

**Scoring rule, applied identically to both:**

- **Capability:** each of ST-01 to ST-09 scores HAS = 2, PARTIAL = 1, MISSING = 0, for a maximum of 18.
- **Delta size:** each required delta is weighted S = 1, M = 2, L = 3, and a range such as M–L is the midpoint. Lower is better.
- **Other criteria:** dependency closure, egress and Arabic-capable permissive engines are compared directly.
- **Decision rule:** VoiceStudio stays the lead unless Voicebox wins on the recorded score (packet acceptance). The recorded score is the capability total, with delta size as the tie-breaker.

## 1. MVP capabilities (ST-01 to ST-09)

| ID | Capability (product vision §2.2) | VoiceStudio | Voicebox |
| --- | --- | --- | --- |
| ST-01 | Durable, versioned project format; autosave; recovery | **PARTIAL**. Project `state_json` has no schema version (`backend/api/routers/projects.py:47`). Alembic database migrations exist, and only the dub draft autosaves (localStorage). Delta M–L. | **PARTIAL**. The `Project` model exists but is unused (`backend/database/models.py:117`); migrations check columns, with no version (`backend/database/migrations.py:34`); a crash marks running jobs failed (`backend/app.py:287`). Delta L. |
| ST-02 | Script → multi-speaker TTS; engine pinned per project | **PARTIAL**. Has `[voice:NAME]` script markup (`backend/services/longform_parser.py:3-4`) and a cast editor. The engine is one global pref (`backend/services/tts_backend.py:4557-4561`). Delta M. | **PARTIAL**. No script editor. The engine is per voice or clip, with silent `"qwen"` fallbacks (`backend/services/profiles.py:131-138`, `backend/routes/generations.py:179`). Delta L. |
| ST-03 | Model manager with code and weight licence, languages, size, offline flag, consent need | **PARTIAL**. Weight licence and `commercial_use` are recorded (`backend/config/model_licenses.json`), and non-commercial or unknown licences are gated until accepted (`backend/services/model_acceptance.py:1-12`). No structured code-licence, language, offline or consent fields. Delta M. | **PARTIAL**. Model record has size and languages only (`backend/backends/__init__.py:54-69`); the licence is read live from Hugging Face (`app/src/components/ServerSettings/ModelManagement.tsx:446-448`); no gate. Delta M. |
| ST-04 | Consent ledger enforced at enqueue, render, resume, cache | **MISSING**. A boolean "verified own voice" lock that local synthesis never checks (`0003_voice_profile_consent.py:9-11`); enforced only for gallery, telephony and agent features. Delta L. | **MISSING**. No consent model at all. Delta L. |
| ST-05 | Synthetic-audio watermark on exports | **HAS**. Invisible watermark on by default (`backend/services/watermark.py`), applied on generation, audiobook, dub and batch outputs (`backend/api/routers/generation.py:1626-1637`). The AudioSeal checkpoint downloads lazily. Delta S. | **MISSING** at app level. `resemble-perth` is bundled only as a Chatterbox dependency (`backend/requirements.txt:36`); no watermark call in app code. Delta M. |
| ST-06 | Segment timeline with edit, undo and export | **PARTIAL**. Dub timeline with undo/redo (`electron/src/renderer/src/features/dub/dub-session.ts:390-475`); long-form is chapter-based, not a timeline. Delta M. | **PARTIAL**. Multitrack clips with trim, split and duplicate (`backend/database/models.py:100-113`, `backend/routes/stories.py:140,168,182`); no undo/redo, no dubbing alignment. Delta M. |
| ST-07 | Long-form with segment-level resume | **HAS**. `resume.json` manifest plus a content-addressed segment cache (`backend/services/longform_resume.py`, `backend/services/longform_render.py:413-454`). On resume the engine is taken from the active one, not the manifest (`backend/api/routers/audiobook.py:632`). Delta S. | **PARTIAL**. Chunks are in memory only (`backend/utils/chunked_tts.py:331-355`); retry re-runs everything. Delta L. |
| ST-08 | Export WAV/MP3/stems/subtitles with a provenance sidecar | **PARTIAL**. SRT, VTT, ASS, MP3 and stems (`backend/api/routers/dub_export.py:1999-2279`); no provenance sidecar. Delta S–M. | **PARTIAL**. WAV, M4B and MP3 (`backend/services/stories.py:1099-1100`); no stems, subtitles or sidecar. Delta M. |
| ST-09 | Local-only operation: analytics off, no URL ingest, no auto-download | **PARTIAL**. Analytics is opt-in, default off (`backend/core/analytics.py:100-105`). URL ingest has no switch. Lazy model downloads. No offline mode. Delta M. | **PARTIAL**. No analytics or URL ingest found. Update check on launch; lazy model downloads. Delta S–M. |

| Score | VoiceStudio | Voicebox |
| --- | --- | --- |
| Capability (max 18) | **10** (2 HAS, 6 PARTIAL, 1 MISSING) | **7** (0 HAS, 7 PARTIAL, 2 MISSING) |
| Delta size (lower is better) | **17** (2.5 + 2 + 2 + 3 + 1 + 2 + 1 + 1.5 + 2) | **21.5** (3 + 3 + 2 + 3 + 2 + 2 + 3 + 2 + 1.5) |
| Required deltas | 9 (2 S, 1 S–M, 4 M, 1 M–L, 1 L) | 9 (1 S–M, 4 M, 4 L) |

## 2. Dependency closure

| | VoiceStudio | Voicebox |
| --- | --- | --- |
| Runtimes | Python ≥ 3.11 (FastAPI), Electron + React, a Rust bridge, and mobile apps (Kotlin, Swift, C/C++) | Python (FastAPI, Torch), React/TS, Tauri 2 (Rust) |
| Python | 54 core dependencies in `pyproject.toml`, plus extras; a CosyVoice sidecar with 24 more | 36 distinct packages in `backend/requirements.txt`, plus small platform files; some installed `--no-deps` |
| JavaScript / Rust | `electron/package.json`: 53 dependencies + 17 devDependencies | app 43 + 7; Tauri 6 + 9; `Cargo.lock` 579 packages |
| Heavy native | torch, torchaudio, whisperx, faster-whisper, pyannote, demucs, pedalboard, sherpa-onnx, CUDA/ROCm indexes | torch, ROCm wheels, MLX, numba, pedalboard, system ffmpeg |
| From URLs or git | 2 pip dependencies from GitHub URLs; audio.cpp runtime from releases | 2 git dependencies and 1 wheel URL; CUDA/ROCm packs (user action) |
| Required default model | OmniVoice, 2.4 GB, **non-commercial weights** | none fixed (Qwen fallback) |

**Smaller closure: Voicebox.**

## 3. Egress paths

| Path | VoiceStudio | Voicebox |
| --- | --- | --- |
| Update check | **On**: GitHub feed 10 s after start and every 6 h; download manual | **On**: on launch |
| Model hub downloads | **On**, lazily on first use | **On**, lazily on first use |
| URL media ingest | **On**: yt-dlp, user-triggered, no switch | none found |
| Analytics | PostHog, opt-in (off by default) | none found |
| Cloud sync and cloud providers | Off unless signed in or keys set: 25+ LLM providers, translation APIs, Twilio | Off unless enabled: cloud login, custom LLM endpoint |

**Fewer default egress paths: Voicebox.** Both need a local-only mode (ST-09).

## 4. Arabic-capable engines with permissive weights (as recorded in each tree)

| | VoiceStudio | Voicebox |
| --- | --- | --- |
| Arabic-listed engines | OmniVoice (non-commercial), OmniVoice-GGUF (non-commercial), MOSS-TTS v1.5 (`apache-2.0` from card metadata, unverified), Supertonic-3 (`openrail`), IndexTTS-2.5 (Arabic not verified) | Chatterbox Multilingual (weights unrecorded in the tree), HumeAI TADA 3B (Llama-based, unrecorded), OmniVoice (non-commercial) |
| Permissive weights recorded in the tree | **1**: MOSS-TTS v1.5, card unverified | **0** |

**Slightly ahead: VoiceStudio.** Every candidate still needs model-card verification (packet ST-D02).

## 5. Licence and maintenance signals

| | VoiceStudio | Voicebox |
| --- | --- | --- |
| Licence | AGPL-3.0-only. Use in Wispral rests on the founder's confirmed grant, recorded per copied file (`RIGHTS_REGISTER.md`). | MIT |
| Upstream direction | A CLA lets Yupcha Softwares relicense contributions; paid Pro tier; open-core drift | No CLA or open-core signals found |

Licence is not one of the packet's scoring criteria. It is recorded here because it bears on the outbound-licence decision (Q-01).

## Result

| Criterion | Better |
| --- | --- |
| MVP capability (ST-01 to ST-09) | **VoiceStudio**, 10 vs 7 |
| Number and size of required deltas | **VoiceStudio**, 17 vs 21.5 |
| Dependency closure | Voicebox |
| Egress paths | Voicebox |
| Arabic-capable permissive engines | **VoiceStudio**, 1 vs 0, unverified |

**Voicebox does not win on the recorded score**, so per the packet **VoiceStudio stays the WisprStudio lead donor.** VoiceStudio's lead rests on two MVP capabilities it already has: the default-on watermark (ST-05) and long-form segment resume (ST-07). Voicebox's multitrack timeline (ST-06) remains the tier-L donor candidate named in the product vision.

**Carried forward to `ST-D00` and later packets:**

- VoiceStudio's required default model has **non-commercial weights**. The default must change to a permissively licensed engine with a verified card (packet ST-D02).
- Make the engine explicit per project and per resume manifest. Both donors can switch engines silently.
- Build a real consent ledger. Neither donor enforces consent for local synthesis.
- Add a local-only mode that disables URL ingest, update checks and lazy downloads (ST-09).
- Bundle the AudioSeal checkpoint, so the watermark does not trigger a download.
- Licence watch: AGPL plus a CLA and open-core upstream. Keep scheduled rebase windows, and keep Voicebox (MIT) as the fallback donor if upstream drift or the outbound licence makes the AGPL path unworkable.
