# WisprStudio source and competitor research: drift, fork qualification and MVP packets

Date: 2026-11-08. Builds on `pr124:research/rea/2026-10-21/WISPRSTUDIO_DEEP_DIVE.md`, `FORK_BOUNDARY_COMPARISON.md`, `source-transplants.json` (ST-*, VB-*), `RIGHTS_AND_ATTRIBUTION_REGISTER.md`, `FEATURE_PARITY_AND_GAP_MATRIX.md`, and Opus review `pr125:.../INDEPENDENT_REVIEW.md` (S1 fork, M4 fit guard). Earlier findings are not repeated unless they changed.

Scope and limits: read-only GitHub (REST API metadata plus source tarballs). No sign-ins, purchases, model downloads, installs or donor builds. No donor test suites ran (`NOT_RUN`). Two bounded pure-Python probes executed donor files with `python -I` (`REPRODUCED`). An interruption cut this pass short: the engine-card sweep and part of the competitor sweep were not finished. Those cells are marked `NOT_VERIFIED` and are not inferred.

Evidence tags: `SOURCE_VERIFIED` (repo@sha:path:line), `DOCUMENTED` (URL, accessed 2026-11-08), `RUNTIME_OBSERVED`, `REPRODUCED`, `NOT_RUN`, `BLOCKED_EXTERNAL`, `REJECTED`, plus `NOT_VERIFIED` for cells not checked in this pass.

Abbreviations: `VS@pin` = debpalash/VoiceStudio `28bf2c7a83b8a64836297340c52a45d716684aed`; `VS@058` = `200286ccff6f28faaf51bb08b2a5b54c460b39f4` (tag v0.5.8); `VB` = jamiepine/voicebox `8af7efe62fab8d33e2a5dfbedabaa45f68a5184f`.

Local acquisition, as untrusted data: GitHub tarballs extracted to `scratchpad\studio\VoiceStudio-28bf2c7` (3,601 files; tarball sha256 `777a37b3…fdbf9`) and `scratchpad\studio\VoiceStudio-200286c` (4,692 files; tarball sha256 `582b8996…45864`). `git clone` failed on this host with "Filename too long", because the scratchpad path exceeds Windows MAX_PATH for `.git/config`. Tarballs plus the `gh api` compare/commit endpoints were used instead. The tree diff is in `scratchpad\meta\vs_treediff.json`, the commit list in `scratchpad\meta\vs_commits.tsv`, and the probe scripts and outputs in `scratchpad\stools\`.

---

## 1. Drift since the prior pins and the re-pin decision

### 1.1 jamiepine/voicebox: no drift

- `gh api repos/jamiepine/voicebox/compare/8af7efe…...main` returns `status: identical`, ahead 0 and behind 0. HEAD is still `8af7efe` (merge of #1168, "add OmniVoice TTS engine … non-commercial weights"). The last push was 2026-10-07. (`DOCUMENTED`: https://api.github.com/repos/jamiepine/voicebox)
- The license is still MIT (`gh api repos/jamiepine/voicebox/license` → `MIT`). **Keep the VB pin.**

### 1.2 debpalash/VoiceStudio: very high drift

| Metric | Value | Evidence |
|---|---|---|
| HEAD (2026-11-08) | `2e195d72d3794a88b7cb37f87a3e92a20193574e` (2026-11-07T21:02Z, #3866 Vulkan probe race) | `DOCUMENTED` GitHub commits API |
| Commits since pin | **2,124** ahead, 0 behind (compare API) | `DOCUMENTED` |
| Tag v0.5.8 | `200286cc…` (2026-11-07T19:32Z, #3857 "raise security floors for seven Python dependencies") | `DOCUMENTED` tags API |
| v0.5.8 → HEAD | 12 commits, all CI, docs, iOS UI test, sponsors, or `scripts/lib/omnivoice-vulkan.sh` and its test | `DOCUMENTED` compare API |
| Pin → v0.5.8 tree | +1,144 files, −53 files, 1,165 modified; 3,601 → 4,692 files; newline count over all files 1,013,077 → 1,411,315 (includes lockfiles and locales) | `REPRODUCED` (`treediff.py`) |
| Stars and size | 103,840 stars; repository size 197,568 KB | `DOCUMENTED` repos API |
| Latest published desktop release | v0.5.7 `beeaae08…` (2026-10-26, 31 assets) | `DOCUMENTED` releases API |
| v0.5.8 release workflow | "Electron desktop release" **startup_failure** on tag v0.5.8. #3860, after the tag, granted the missing permissions. No v0.5.8 binaries exist. | `DOCUMENTED` actions runs API |
| CI on `200286c` | 45 check runs: 29 success, 16 skipped, 0 failed. Includes Desktop UI on Linux/Windows/macOS, Smoke on Linux/Windows/macOS/macOS Intel, Tests (Python), Tests (backend + frontend), Tests (Electron), Electron installer contracts, CodeQL py/js, bandit, gitleaks and Dependency audit. | `DOCUMENTED` check-runs API |

**Relevant changes, pin → v0.5.8.** Source is `SOURCE_VERIFIED` against the two extracted trees unless noted.

1. **Licensing and provenance. This is the most important change.**
   - `LICENSE` and `LICENSE-NOTICE.md` are byte-identical at both SHAs. The license is still AGPL-3.0-only, and `pyproject.toml:14` and `electron/package.json:7` still say `AGPL-3.0-only`.
   - The notice already offers a paid commercial license and "VoiceStudio Pro features". It already states that contributors license their work to Yupcha Softwares Private Limited under `.github/CLA-1.0.md`.
   - **New since the pin:** a CLA enforcement workflow (`.github/workflows/cla*.yml`, `.github/scripts/cla_check.py`, `scripts/cla_audit.py`).
   - **New since the pin:** a 2026-10-26 to 10-28 **"provenance" wave**: 46 `provenance`-scoped commits plus dozens of `clean-room reimplementation` refactors. They remove code and locale strings written by contributors who had not signed the CLA, then reimplement them. Examples: `5a1813a9e chore(provenance): remove contributor-authored code pending clean-room reimplementation`, `8c535daf6 … remaining contributor code found by the residue scan`, `57d7f476c … contributor wording without a CLA`. (`DOCUMENTED` commit list)
   - Implication: at `28bf2c7` the tree still contains contributor code that the maintainer company itself later treated as not held under its CLA. If any Wispral authorization derives from the copyright holder, a post-wave SHA is cleaner. The founder's confirmed grant is not questioned here. This is a provenance-hygiene reason to re-pin.
   - Related trajectory, from before the pin (DOCUMENTED, v0.5.7 release notes, https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.7):
     - "Remote compute devices, remote workers and GPU sharing moved to VoiceStudio Pro." This is #2748, merged 2026-10-11.
     - Non-commercial models, including the default OmniVoice, need a one-time licence acceptance. This is #2689, merged 2026-10-10.
     - The repo is moving toward open core. Mobile commit `703115010` adds "Donate, Pro and Other Apps pages".
2. **Account and cloud.**
   - New `config/account.json:1-27` with the Zitadel issuer `https://id.voicestudio.sh`, `https://appapi.voicestudio.sh/v1/account|/v1/sync`, and a production `clientId`.
   - New `config/account-config.mjs:4-5` says every build reads the file, so CI and release builds offer sign-in without a build-time flag, though each user must turn it on (off by default).
   - At the pin, packaged builds needed `VOICESTUDIO_CLOUD_ACCOUNTS=1` at build time and defaulted to the `dev` environment (`VS@pin electron/src/main/account/cloud-config.ts`). At v0.5.8 the default environment is `prod` (`VS@058 electron/src/main/account/cloud-config.ts:33-41,71-73`).
   - Switches default OFF (`electron/src/main/account/cloud-switches.ts:4,11`). A backend `services/cloud_sync/` (allowlist, client, voices, vsb1) and router `api/routers/cloud_sync.py` exist.
   - **Net effect: release builds now carry a cloud sign-in and sync path.**
3. **Analytics.**
   - `backend/core/analytics.py` is byte-identical pin → 058 (sha `824f9867…`). Analytics is consent-gated, defaults to `False` (lines 7-10, 101), and has the kill switch `OMNIVOICE_ANALYTICS_DISABLED` (line 44).
   - A **committed publishable PostHog token** `_PUBLIC_PROJECT_TOKEN` exists (line 57), with host `https://us.i.posthog.com` (line 58).
   - Renderer: `electron/src/shared/utils/analytics.ts` and `posthog-js ^1.434.14`.
   - New since the pin: `c2998f6f8 feat(analytics): ask before setup and count setup failures with consent` and `75680b8d5 fix(analytics): honor the kill switch …`. The consent prompt now comes earlier, during setup.
4. **Engines.** All added since the pin:
   - `whisper_cpp` ASR (optional Vulkan): `backend/engines/whisper_cpp/`, #`5ee41e305`.
   - `cosyvoice_gguf` (CosyVoice3 GGUF, Vulkan/CPU): `backend/engines/cosyvoice_gguf/`, #3449.
   - OmniVoice GGUF Vulkan auto and GPU offer: `engines/omnivoice_gguf/vulkan_auto.py`, `gpu_offer.py`.
   - Windows ROCm opt-in: `backend/core/windows_rocm/*`, #3045.
   - `gpu_self_test.py`, `xpu_compat.py`, and `f6fb94e6a feat(gpu): run real work on the GPU in a process that can die`.
   - IndexTTS2 emotion controls, and the VoxCPM2 8-bit MLX entry.
   - **No native Chatterbox, Qwen3-TTS, Kokoro, F5, OpenVoice, XTTS or Voxtral engine on Windows/Linux at either SHA.** They appear only as Apple-Silicon `mlx-audio` families: `backend/services/tts_backend.py:2898-2970` at VS@058, where `"chatterbox": ("en",)` is at 2963.
5. **Dubbing and timeline.**
   - `fit_planner.py` now handles overlapping speakers on one shared timeline (`_shared_timeline`, VS@058 `backend/services/fit_planner.py:138-201,298-305`; #3008).
   - New `dub_language.py` (303 lines), `dub_mix.py`, room-tone fill (#3611), flagged-segment navigation, Uyghur RTL dub target, and pt-BR/pt-PT split.
6. **Projects.** New `services/project_bundle.py` (350 lines) and `api/routers/project_bundles.py` (561 lines), for portable project bundles.
7. **Model manager.** New `services/model_catalogue.py`, `hf_cache_rollback.py` and `reference_transcript.py`. `model_manager.py` grew from 4,592 to 4,737 lines.
8. **Voice conversion and design.** New `services/voice_conversion.py` (190 lines), `voice_design_profiles.py`, and migration `0016_profile_design_recipe.py`.
9. **Packaging.** Mobile apps (iOS/Android, about 388 new files under `mobile/`), AUR, Nix flake, Mac App Store sandbox staging, Snap, F-Droid repository, VirusTotal workflow, and Windows Smart App Control warning. Setup failures are now classified into stable codes.
10. **Security.** `deploy/security-constraints.txt`, `deploy/security_floors.py` and `deploy/uv-overrides.txt` (#3857, raises floors for seven dependencies).

**Previously studied modules, pin → 058** (changed lines per `diff`; `SOURCE_VERIFIED`):

| Module | Status |
|---|---|
| `duration_planner.py`, `longform_resume.py`, `inference_cancellation.py`, `core/analytics.py`, `services/outbound_http.py`, `core/url_safety.py` | **byte-identical** |
| `model_acceptance.py` | 2 lines changed |
| `project-format.ts` | 4 lines changed |
| `dub_pipeline.py` | 19 lines changed |
| `contained_subprocess.py` | 23 lines changed |
| `watermark.py` | 40 lines changed |
| `model_lifecycle.py` | 55 lines changed |
| `dub-draft.ts` | 62 lines changed |
| `fit_planner.py` | 79 lines changed (overlap support) |
| `pronunciation.py` | 82 lines changed |
| `speaker_clone.py` | 144 lines changed |
| `longform_render.py` | 184 lines changed |
| `subprocess_backend.py` | 307 lines changed |
| `profiles.py` | 367 lines changed |
| `model_manager.py` | 371 lines changed |
| `dub_generate.py` | 737 lines changed (2,091 → 2,014 lines) |
| `tts_backend.py` | 836 lines changed (4,494 → 4,978 lines) |

Prior ST-* packets still apply. Their anchors must be rebased.

### 1.3 Re-pin recommendation

**Re-pin the WisprStudio fork base to `200286ccff6f28faaf51bb08b2a5b54c460b39f4` (tag v0.5.8).** Reasons:

- (a) It is after the CLA provenance clean-room wave.
- (b) It includes the #3857 security floors.
- (c) It includes the overlapping-speaker Smart Fit fix.
- (d) Its full CI push run is green (29 success, 0 failed).
- (e) HEAD `2e195d72` differs only by 12 CI/docs/test/build-script commits, so nothing product-relevant is lost.
- (f) The tag gives a human-readable anchor, but pin by SHA because tags can move.

Caveats:

- No v0.5.8 binaries exist, because the release workflow had a startup_failure.
- If REA needs an official-installer baseline, use v0.5.7 `beeaae08204f0de5f49d4a087ef2b0ea8fecfcb9` binaries for observation only. No installer was downloaded in this pass.
- Upstream velocity is about 118 commits/day over 18 days (2,124 / 18). Plan for a pinned fork with scheduled, delta-register-driven rebase windows, not continuous tracking.

---

## 2. VoiceStudio fork qualification at `200286c`

### 2.1 Stack

All entries are `SOURCE_VERIFIED` against `VS@058`.

| Layer | Finding | Anchor |
|---|---|---|
| Desktop shell | Electron `^44.3.0`; electron-builder `^26.15.3`; electron-updater `^6.8.9`; electron-vite `6.0.0-beta.1` | `electron/package.json` |
| Renderer | React `^19.3.0`, Vite `^8.3.0`, TypeScript `^7.0.2`, TanStack Router `^1.170.36` and Query `^5.102.8`, Zustand `^5.0.15`, Tailwind `^4.3.3`, i18next `^26.4.2`, wavesurfer.js `^7.12.12`, vitest `5.1.0` | `electron/package.json` |
| Backend | FastAPI `<0.137` + uvicorn bound to `127.0.0.1`; SQLite via `sqlite3`; Alembic migrations | `electron/src/main/backend.ts:183`; `backend/main.py:2242-2246`; `backend/core/db.py:2,16`; `backend/migrations/versions/` |
| Python | `requires-python >=3.11`; `.python-version` = 3.11; Windows ROCm forces CPython 3.12; Windows arm64 uses x64 CPython 3.11 | `pyproject.toml:15`; `scripts/setup-api.mjs:37-45`; `electron/src/main/runtime-project.ts:140` |
| Package managers | `bun@1.4.2` (root `packageManager`); uv `0.12.13` with `uv.lock`; `torch==2.8.0`, `torchaudio==2.8.0` and `torchvision==0.23.0` constraints; default groups `dev` and `cuda`; cpu and cuda groups conflict | `package.json`; `runtime-project.ts:67`; `pyproject.toml` `[tool.uv]` |
| Heavy base dependencies | `transformers>=5.10.0`, `gradio>=6.15.1`, `whisperx`, `faster-whisper`, `pyannote-audio>=3.3.2,<4`, `demucs`, `yt-dlp>=2026.7.4`, `audioseal`, `posthog`, `litellm`, `openai`, `boto3`, `google-auth`, `argostranslate`, `mcp`, `sherpa-onnx`, and a GitHub wheel URL for KittenTTS and spaCy `en_core_web_sm` | `pyproject.toml:35-110` |

### 2.2 Module map

All entries are `SOURCE_VERIFIED`, `VS@058`, with paths relative to the repo root.

| Capability | Paths | Notes |
|---|---|---|
| Project persistence and format | `backend/api/routers/projects.py` (97 lines), `api/routers/project_bundles.py` (561), `services/project_bundle.py` (350), `electron/src/renderer/src/features/projects/project-format.ts`, `project-handoff-format.ts` | SQLite DB plus files; portable bundles are new |
| Timeline and editor | `features/dub/dub-timeline.tsx`, `dub-draft.ts`, `segment-time-field.ts`, `use-dub-onsets.ts`; Stories/longform editor `features/longform/*`; `api/routers/stories.py:1-30` (client-side Web Audio stitch, then ffmpeg encode) | Segment and speaker timeline for dubbing; story editor |
| Multitrack | **No general multitrack (DAW-style) editor found.** "Multi-track" appears only as multi-language audio mux (`services/ffmpeg_utils.py:1013`, `services/incremental.py:70`). | Gap vs. Voicebox Stories and the ElevenLabs Studio video timeline |
| TTS generation | `api/routers/generation.py`, `services/tts_backend.py` (4,978 lines), `services/chunked_tts.py`, `services/sentence_chunker.py`, `api/routers/tts_stream.py` | — |
| Engine registry | `tts_backend.py:3785-3829` (`_LAZY_REGISTRY`), `:3894-3903` (`_REGISTRY`), `_INSTALL_HINTS` after it | Default `tts_backend="omnivoice"`: `core/prefs.py:9`, `tts_backend.py:4561` |
| Per-engine subprocess and venvs | `backend/engines/{indextts,moss_tts_v15,dots_tts,confucius4,supertonic3,pockettts,omnivoice_subprocess,cosyvoice_gguf,omnivoice_gguf,audiocpp,whisper_cpp,_asr_sidecar,_echo}/`, `engines/_venv_probe.py`, `services/subprocess_backend.py` (1,207 lines), `core/contained_subprocess.py` (739), `services/engine_env.py`, `services/sidecar_install.py`, `services/gpu_sandbox.py` | Own-venv engines are IndexTTS2, MOSS-v1.5 (transformers==5.0), dots.tts (==4.57.0) and Confucius4 (Py 3.10), per `tts_backend.py:3802-3820`. Same-interpreter crash isolation applies to omnivoice-subprocess and pockettts. |
| Model manager, download and acceptance | `services/model_manager.py` (4,737), `model_catalogue.py`, `model_acceptance.py`, `model_licenses.py`, `hf_revisions.py`, `hf_cache_repair.py`, `hf_cache_rollback.py`, `segmented_download.py`, `endpoint_race.py`, `api/routers/setup/download.py`; catalog `backend/config/models.yaml` (452 lines); licence records `backend/config/model_licenses.json` (70 models, 7 dynamic assets, `checked_at 2026-10-03`) | — |
| Voice profiles, cloning and consent | `api/routers/profiles.py` (1,412 lines): consent `:1242`, attestation `:1319/:1334`, revoke `:1346`; `services/speaker_clone.py` (587); `core/voice_leases.py` | **Consent gates only agentic features and gallery sharing. "Plain local synthesis never does"** (`profiles.py:1212-1217`). Consent fields are used in archetypes, community, gallery, personas, persona/project bundles, cloud_sync/voices and telephony, but **not** in `generation.py`, `dub_generate.py` or `speaker_clone.py` (grep). |
| Watermark | `services/watermark.py` (732 lines): AudioSeal invisible watermark, `is_enabled()` default **True** (`:327-329`); audible brand tone default False (`:341-343`); video logo default True (`:346-348`); `api/routers/watermark.py` | AudioSeal weights are recorded as `NOASSERTION`, unreviewed (dynamic asset in `model_licenses.json`) |
| Voice conversion | `services/voice_conversion.py` (new), `services/rvc.py`, `api/routers/voice_convert.py` | RVC uses user-provided models (dynamic asset, unreviewed) |
| Voice design | `api/routers/describe_voice.py`, `core/describe_voice.py`, `services/voice_design_profiles.py`, `features/design/` | Via engines with instruct or design support |
| Dubbing pipeline | Ingest: `services/dub_pipeline.py` (1,853; `ingest_pipeline` `:1457`), `api/routers/dub_core.py`. ASR: `services/asr_backend.py` (4,514). Diarization: `diarization_{local,native,runtime}.py`, `transcript_diarization.py`. Translation: `translator.py`, `translation_engines.py`, `translation_apis.py`, `api/routers/dub_translate.py`, `glossary.py`. Align and fit: `duration_planner.py`, `fit_planner.py`, `onset_align.py`, `speech_rate.py`, `video_retime.py`. TTS: `api/routers/dub_generate.py` (2,014; `plan_fit` call `:1595`). Mix and separation: `dub_mix.py`, `dub_background.py` (demucs), `loudness.py`. QC: `dub_qc.py`, `translation_quality.py`. Export: `api/routers/dub_export.py`. | Full chain present |
| Subtitles | `services/fitted_subtitles.py`, `subtitle_segmenter.py`, `srt_parser.py`, `karaoke_ass.py`; `/dub/import-srt` (`dub_core.py:292`) | — |
| Long-form and audiobook | `services/longform_{import,parser,render,resume,progress}.py`, `audiobook.py`, `api/routers/audiobook.py`, `longform_jobs.py`; `features/longform/render-recovery.tsx`, `render-reattach.test.tsx` | — |
| Batch | `api/routers/batch.py` (download `:1075`), `services/dub_batching.py` | — |
| Resume after failure | `longform_resume.py` (unchanged), `core/job_store.py`, `core/job_queue.py`, `core/run_sentinel.py`, migration `0017_job_events_unique_seq.py`, `features/dub/checkpoint-banner.tsx` | — |
| Export and render formats | Dub audio wav/mp3/flac/m4a/aac plus ass subtitles (`dub_export.py`); stories mp3/m4b/ogg/aac (`stories.py:20-25`); audiobook mp3/m4b | Video mux formats `NOT_VERIFIED` in this pass |
| Pronunciation | `services/pronunciation.py` (519): whole-word respelling lexicon, case-insensitive, longest key first; `api/routers/pronunciation.py` (import `:276`) | **No phoneme or IPA rules.** Arabic clitic gap was `REPRODUCED` (§2.6). |
| Local REST API and MCP | FastAPI routers; `api/routers/openai_compat.py`; `backend/mcp_server.py` (9 `mcp.tool` registrations) and `backend/mcp_shim/`; auth `core/auth.py` (`OMNIVOICE_API_KEY` `:71`, loopback checks `:105,:175`) | Allowed-hosts rule and private-URL import opt-in per v0.5.7 notes |
| Analytics and telemetry | `backend/core/analytics.py`, `electron/src/shared/utils/analytics.ts`, crash/bug report `core/diagnostic_bundle.py`, `electron/src/main/crash-report*` | See §2.4 |
| Remote URL media download | `/dub/ingest-url` via yt-dlp (`dub_core.py:967-986`); `/gallery/search/youtube` (`gallery.py:172`) and `/gallery/download` (`gallery.py:232`); yt-dlp self-update overlay from PyPI (`media_tools.py:50-57`); `/community/submit-url` (`community.py:487`); marketplace and personas import | Ingest feeding voice references is a consent risk |
| Updater | `electron/src/main/updater.ts` (feed `:21` `github.com/debpalash/VoiceStudio/releases/latest/download`, `:22` GitHub releases API, `autoDownload=false` `:267`); scheduled from `electron/src/main/index.ts:322-329` (10 s after start, then every 6 h) | — |
| i18n and RTL | 22 locales including `ar.json` (`electron/src/renderer/src/i18n/locales/`); `document.documentElement.dir = i18next.dir(locale)` (`i18n/index.ts:79`); RTL handling in `features/clone/language-menu.tsx`, `features/dub/segment-highlight.tsx` | Arabic UI locale exists. Its quality is `NOT_VERIFIED`. |

### 2.3 Tests

Counts are by file pattern (`REPRODUCED` counts, not coverage).

| Type | VS@pin | VS@058 |
|---|---|---|
| Python test files (`test_*.py`, excluding `research/` and `omnivoice/`) | 696 (tests/ 648, backend/tests 48) | **869** (tests/ 812, backend/tests 54) |
| Python `def test_` functions in tests/ + backend/tests | 7,163 | **8,722** |
| Electron unit tests (`*.test.{ts,tsx,js,jsx,mjs}`) | 621 | **753** |
| `electron/tests/` files (desktop UI, smokes, live) | 121 | 135 |
| Mobile test files | 30 | 104 |
| GitHub workflows | — | 30 |

Fit fixtures and tests include `tests/test_fit_planner.py`, `tests/test_fit_overlapping_cues.py`, `tests/test_smart_fit_generate.py`, `tests/test_duration_planner.py` and `tests/test_dub_duration_plan_api.py`. **Running the suites: `NOT_RUN`.** Upstream CI pass on `200286c` is `DOCUMENTED` (§1.2). It is not a local baseline.

### 2.4 Packaging

- Windows target is NSIS: `oneClick:false`, `perMachine:false`, `asar:true` (`electron/electron-builder.config.mjs:212,220-231`). The `generic` publish feed is at `:93-96`.
- v0.5.7 `VoiceStudio-0.5.7-win-x64.exe` is **211 MiB**, and the Linux AppImage is 255 MiB (`DOCUMENTED` releases API).
- **Windows installers are unsigned** (v0.5.7 notes). This is `DOCUMENTED`.
- The installer does not contain the ML runtime. On first run it downloads a CPython build through uv (python-build-standalone, with a `gh-proxy.com` mirror at `runtime-project.ts:240` and a `ghproxy.net` latency probe at `:260`). It installs uv itself from `astral.sh` (`:1317`) and then `uv sync --locked` wheels: torch from `download.pytorch.org/whl/cu128` (cuda group, the default on win/linux x64) or `/whl/cpu`.
- CPU fallback offer: `21296c49b`. GPU self-test: `core/gpu_self_test.py`. ROCm on Windows is opt-in. Vulkan is used for the GGUF engines.
- Installed size, GPU behavior and first-run time: `NOT_RUN`.

### 2.5 Default network egress paths

All entries are `SOURCE_VERIFIED`, `VS@058`.

| # | Destination | Trigger | Default state | Anchor |
|---|---|---|---|---|
| E1 | `github.com/debpalash/VoiceStudio/releases/latest/download` and `api.github.com/repos/debpalash/VoiceStudio/releases` | Update check 10 s after launch, then every 6 h | **ON** (check only; `autoDownload=false`) | `electron/src/main/index.ts:322-329`; `updater.ts:21-22,267` |
| E2 | `us.i.posthog.com` (committed `phc_…` token) | Analytics after explicit consent; first-run/setup consent prompt | Off until consent; token baked in; kill switch env | `backend/core/analytics.py:44,57-58,101`; `electron/src/shared/utils/analytics.ts` |
| E3 | `id.voicestudio.sh`, `appapi.voicestudio.sh/v1/account`, `/v1/sync`, `app.voicestudio.sh` | Cloud sign-in and sync | Available in release builds; switches OFF | `config/account.json`; `electron/src/main/account/cloud-config.ts:71-73`; `cloud-switches.ts:11` |
| E4 | `huggingface.co`, auto-raced against **`hf-mirror.com`** (third-party community mirror) | Model downloads (catalog, first-use weights) | **Auto race ON** unless `OMNIVOICE_HF_ENDPOINT_MODE=manual` | `backend/services/endpoint_race.py:18-20,58`; `api/routers/setup/wizard.py:405-440` |
| E5 | `astral.sh` (uv), python-build-standalone via GitHub or **`gh-proxy.com`/`ghproxy.net`**, `pypi.org`/`files.pythonhosted.org`, `download.pytorch.org`, `mirrors.aliyun.com` (China mirror) | First-run runtime install and repair | **ON** (required for a working install) | `electron/src/main/runtime-project.ts:67,240,260,1317`; `electron/src/main/pypi-mirror.ts`; commit `03179288f` |
| E6 | Engine-specific: `git clone` of upstream engines (IndexTTS, MOSS, CosyVoice), GGUF quants from `Serveurperso/OmniVoice-GGUF` on first generate | Opt-in engine install or first use | Opt-in | `tts_backend.py` `_INSTALL_HINTS`; `api/routers/engines.py:507` |
| E7 | yt-dlp to arbitrary sites; YouTube search | `/dub/ingest-url`, `/gallery/search/youtube`, `/gallery/download` | Feature available (yt-dlp is a base dependency) | `api/routers/dub_core.py:967-986`; `gallery.py:172,232` |
| E8 | PyPI (yt-dlp self-update overlay) | User action | Opt-in | `api/routers/media_tools.py:50-57` |
| E9 | `github.com/debpalash/omnivoice-gallery/releases/latest/download` | Gallery or community content | On use | `backend/services/gallery.py:86` |
| E10 | Online translation (Google free web endpoint via `deep_translator`, no key), DeepL, Google Cloud, OpenAI; LLM providers via litellm (OpenRouter, Ollama, LM Studio, SiliconFlow, NVIDIA, xfyun, dashscope, Opper, API Route, …) | Provider selection | Off until chosen. **The default dub translate provider was not established in this pass.** | `services/translation_engines.py:55-123`; `services/llm_providers.py` |
| E11 | Argos language packs; NLLB (CC-BY-NC) | Translation-pack install | Opt-in | `translation_engines.py:55-76,408` |
| E12 | Tailscale (`login.tailscale.com`), LAN network share, Twilio telephony | Opt-in features | Opt-in | `services/tailscale.py`, `network_share.py`, `api/routers/telephony_twilio.py` |
| E13 | Bug or crash report submission | User action ("show what will be sent", `e0941e469`) | Opt-in | `core/diagnostic_bundle.py`; `electron/src/main/crash-report*` |

Upstream docs now list sanctioned network calls (`7091a12ff docs: list optional engine install downloads as sanctioned network calls`). That document was not reviewed in this pass. **Observed runtime egress: `NOT_RUN`.**

### 2.6 Bounded probes

- **P1. Fit guard (M4) re-check: `REPRODUCED`.** The Opus probe (`pr125:.../probe_fit_planner_inputs.py`) ran unchanged with `python -I` on CPython 3.14.7 (Windows 11 10.0.26300).
  - On `VS@pin fit_planner.py` (sha256 `0acd7c33…21442`) the output **matches the Opus-recorded results line for line**.
  - On `VS@058 fit_planner.py` (sha256 `9096f6a3…89d35`), `nan_natural`, `inf_natural` (non-finite output), `negative_natural`, `end_before_start` and `nan_total` are **still ACCEPTED**. `overlap` is accepted by design and now yields total `10.0`, not `12.0`, from the shared timeline.
  - Request-level `FitOptions` bounds exist (`backend/schemas/requests.py:56-62`, `allow_inf_nan=False`). The segment and duration inputs to `plan_fit` (`dub_generate.py:1584-1595`) have no such guard.
  - **M4 stands, revised:** the guard must not reject overlapping segments.
  - Output: `scratchpad\stools\` (script plus console output in this report).
- **P2. Arabic pronunciation lexicon: `REPRODUCED`.** The stdlib-only `pronunciation.py` (sha256 prefix `c2b3123b`), `dub_qc.py` (`03bcf4cf`) and `language_variants.py` (`4a38156f`) were copied to `scratchpad\stools\probe_pron` and run with `python -I -X utf8`. Lexicon `{محمد, الرياض, Dr}`:
  - Bare `محمد` → replaced.
  - `محمد،` (Arabic comma) → replaced.
  - `في الرياض` → replaced.
  - **`ومحمد`** (conjunction clitic) → **not replaced**.
  - **`بالرياض`** (preposition + article) → **not replaced**.
  - The English control was replaced.
  - Results are in `scratchpad\stools\pron_probe_results.jsonl`. Whole-word `\b` matching misses attached Arabic clitics, which are very common in real text.

---

## 3. Engine and model matrix at `VS@058`

Sources:

- "VS record" = VoiceStudio's own `backend/config/model_licenses.json` entry (`SOURCE_VERIFIED`; VS marks every entry `commercial_use:false` unless reviewed, and most `review_status:"unreviewed"`).
- "Card" = official model card. `DOCUMENTED` card revisions come from the prior pinned study (`pr124 studio-source-evidence.json`, URL pattern `https://huggingface.co/<model>/blob/<revision>/README.md`).
- Cards not re-fetched in this pass are `NOT_VERIFIED`.

| Engine id (registry anchor) | Isolation | Weights (VS record license / review) | Card status | Arabic claim (source) | CPU / VRAM notes (VS docs) | Flags |
|---|---|---|---|---|---|---|
| `omnivoice` **DEFAULT** (`tts_backend.py:3895`; `prefs.py:9`; `models.yaml:48-51` `required: true`, 2.4 GB) | in-process | `k2-fsa/OmniVoice` "CC-BY-NC (version unspecified); Higgs Audio 2; Meta Llama 3", `noncommercial` | `DOCUMENTED` rev `c5fdb5cc` (Apache code, CC-BY-NC weights) | `omnivoice_gguf/backend.py:1093` maps `ar` | 6 GB VRAM floor; CPU slow, 600 s budget (`docs/engines/omnivoice.md:13-31`) | **NON-COMMERCIAL default + tokenizer terms** |
| `omnivoice-subprocess` (`:3807`) | subprocess, same interpreter | same | same | same | same | **NC** |
| `omnivoice-gguf` (`:3791`) | native binary | `Serveurperso/OmniVoice-GGUF` CC-BY-NC-4.0 + Higgs + Llama, `noncommercial` | `NOT_VERIFIED` | `ar` mapped | Vulkan/CPU | **NC** |
| `cosyvoice` (`:3896`) | in-process (separate clone) | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` apache-2.0 | `DOCUMENTED` rev `29e01c4e` | `NOT_VERIFIED` (no `ar` found in VS source) | — | Separate requirements |
| `cosyvoice-gguf` (`:3829`) | native server | `Lourdle/Fun-CosyVoice3-0.5B-2512-GGUF` "apache-2.0 (upstream metadata)" | `NOT_VERIFIED` | `NOT_VERIFIED` | Vulkan/CPU | Community conversion |
| `voxcpm2` (`:3899`) | in-process | `openbmb/VoxCPM2` apache-2.0 | `NOT_VERIFIED` | **Yes**: `tts_backend.py:2232` list includes `ar`; `docs/engines/voxcpm2.md:12` "30 supported languages: Arabic…" | CUDA ≥12 recommended; MPS/CPU slower (`voxcpm2.md:21,73`) | **Arabic + Apache per VS record** |
| `moss-tts-nano` (`:3900`) | in-process | `OpenMOSS-Team/MOSS-TTS-Nano(-100M)` apache-2.0 | `NOT_VERIFIED` | **Yes**: `tts_backend.py:2391` list includes `ar` | "realtime on a 4-core CPU" (`moss-tts-nano.md:4`) | **Arabic, CPU, Apache per VS record** |
| `moss-tts-v15` (`:3803`) | own venv (transformers==5.0) | `OpenMOSS-Team/MOSS-TTS-v1.5` apache-2.0 | `NOT_VERIFIED` | **Yes**: `engines/moss_tts_v15/main.py:88` | 8B, about 16 GB weights (`_INSTALL_HINTS`) | Heavy |
| `indextts2` (`:3786`) | own venv | `IndexTeam/IndexTTS-2.5` "other" | `NOT_VERIFIED` (custom license) | **Yes**: `engines/indextts/__init__.py:57,281` (`zh,en,ja,es,ar`) | Needs ≥12 GB free disk (`indextts.md:23`) | **Custom licence: review required** |
| `supertonic3` (`:3797`) | subprocess | `Supertone/supertonic-3` openrail | `NOT_VERIFIED` | `engines/supertonic3/sidecar.py:228` alias `arabic→ar`; 31 languages (`supertonic3.md:4`) | CPU-only ONNX | **OpenRAIL use restrictions** |
| `confucius4-tts` (`:3815`) | own venv, Python 3.10 | `netease-youdao/Confucius4-TTS` apache-2.0 plus `w2v-bert-2.0` mit, `campplus` apache, `bigvgan` mit | `NOT_VERIFIED` | 14 languages (`tts_backend.py:3812`); Arabic `NOT_VERIFIED` | — | Py 3.10 environment |
| `dots-tts` (`:3804`) / `audiocpp-dots` (`:3826`) | own venv (transformers==4.57.0) / native | `rednote-hilab/dots.tts-soar` apache-2.0 | `NOT_VERIFIED` | `NOT_VERIFIED` | — | — |
| `audiocpp` (`:3823`) | native server | `audio-cpp/audio.cpp-gguf` "other" | `NOT_VERIFIED` | en+zh (`:3819-3821`) | — | Unreviewed |
| `pockettts` (`:3812`) | subprocess | `kyutai/pocket-tts` cc-by-4.0; HF-gated per hint | `NOT_VERIFIED` | `NOT_VERIFIED` | CPU-only (`pockettts.md:3-10`) | Gated terms; mobile conversion recorded as NC |
| `kittentts` (`:3897`) | in-process | `KittenML/kitten-tts-mini-0.8` apache-2.0 | `NOT_VERIFIED` | English presets | CPU realtime (`kittentts.md:4,51`) | GitHub wheel URL dependency |
| `gpt-sovits` (`:3902`) | external API server on :9880 | `lj1995/GPT-SoVITS` mit | `NOT_VERIFIED` | `NOT_VERIFIED` | — | External process |
| `sherpa-onnx` (`:3903`) | in-process | User-provided Piper/VITS (dynamic asset NOASSERTION); mobile `vits-piper` GPL-3.0 | `NOT_VERIFIED` | Piper Arabic voice availability `NOT_VERIFIED` | CPU | GPL voices on mobile |
| `mlx-audio` (`:3898`, Apple Silicon only) | in-process | Families include Kokoro (apache), CSM, Dia, Qwen3-TTS VoiceDesign 4-bit (apache), Chatterbox 4-bit (NOASSERTION, English only `:2963`), OuteTTS (**CC-BY-NC-SA + Llama**, `noncommercial`), VoxCPM2 8-bit | Mixed / `NOT_VERIFIED` | outetts and voxcpm2 lists include `ar` (`:2966,2970`) | Apple only | **OuteTTS NC** |
| ASR: whisperx / faster-whisper / pytorch-whisper / whisper-cpp / moonshine / nemo-parakeet / sherpa-onnx-asr / funasr / mlx | mixed (sidecar `_asr_sidecar`) | Mostly mit/apache; Parakeet cc-by-4.0; SenseVoice NOASSERTION | `NOT_VERIFIED` | Whisper multilingual incl. Arabic is upstream knowledge, `NOT_VERIFIED` here | — | — |
| Translation: argos / **nllb** / online | — | `facebook/nllb-200-distilled-600M` **CC-BY-NC-4.0**, `noncommercial`; Argos packs NOASSERTION | — | — | — | **NLLB NC** |
| Diarization: pyannote 3.1 / segmentation-3.0 / wespeaker | in-process | mit / mit / cc-by-4.0 (VS records) | Prior study: separate access terms | — | — | Gated access |
| Watermark: AudioSeal | in-process | Dynamic asset `NOASSERTION`, unreviewed | `NOT_VERIFIED` | — | — | **Unresolved weight licence for a default-on feature** |
| Separation: htdemucs | in-process | NOASSERTION (dynamic) | — | — | — | Archived upstream (prior study) |

**Previously considered engines, at `VS@058` on Windows/Linux:**

| Engine | Status at VS@058 | Card evidence |
|---|---|---|
| Chatterbox Multilingual | **Absent natively.** MLX 4-bit English only (`tts_backend.py:2935,2963`). | Card MIT, `DOCUMENTED` rev `5bb1f6ee`. Arabic in the multilingual source map (prior study `SOURCE_VERIFIED` CB@`5de7a54a` `mtl_tts.py SUPPORTED_LANGUAGES`). Voicebox README lists Chatterbox Multilingual with Arabic (`SOURCE_VERIFIED` VB README@`8af7efe`). |
| Qwen3-TTS Base/VoiceDesign | MLX only | Apache-2.0, `DOCUMENTED` revs `fd4b2543` / `5d839924`. Arabic not in VS's qwen3 list (`:2961`). |
| Kokoro-82M | MLX and mobile only | Apache-2.0, `DOCUMENTED` rev `f3ff3571`. No Arabic (prior study). |
| F5-TTS | Absent | CC-BY-NC-4.0, `DOCUMENTED` rev `84e5a410` |
| Voxtral-4B-TTS-2603 | MLX family mention only (`:2901`) | CC-BY-NC-4.0, `DOCUMENTED` rev `b81be46c` |
| OpenVoice V2 | Absent | MIT, `DOCUMENTED` rev `f36e7edf` |
| XTTS-v2 | Absent. Only a comment in `sonitranslate.py:5` and `plugin_sdk.py:4`. | Licence `NOT_VERIFIED` |
| Piper | Via sherpa-onnx | Per-voice licences, `NOT_VERIFIED` |

**Dependency conflicts** (`SOURCE_VERIFIED`):

- The parent requires `transformers>=5.10.0` and torch 2.8.0.
- MOSS-v1.5 pins `transformers==5.0.0`, dots.tts pins `==4.57.0`, and Confucius4 needs Python 3.10. All are already isolated in their own venvs (`tts_backend.py:3799-3815`).
- Chatterbox (prior: `transformers==5.2.0`, torch 2.6.0, Perth from git `@master`) would also need its own venv.
- whisperx forces `pyannote-audio<4` and `setuptools<80` (`pyproject.toml:46-60`).

**Default-engine finding:**

- VoiceStudio's default and required TTS uses **non-commercial OmniVoice weights**.
- If OmniVoice is excluded, Arabic-capable engines whose VS records say Apache-2.0 remain: **VoxCPM2** (GPU-preferred), **MOSS-TTS-Nano** (CPU) and MOSS-TTS-v1.5 (8B). Their official cards were **not** re-verified in this pass (`NOT_VERIFIED`).
- Qualification packet WS-02 must check the cards before any default change. No audio quality is claimed.

---

## 4. Fork vs. targeted transplant: Opus S1 re-check

**Verdict: S1 is CONFIRMED with qualifications.** Fork VoiceStudio, re-pinned to `200286c`, behind a delta register.

Evidence for forking:

| Factor | Evidence |
|---|---|
| Coupling | The dubbing orchestrator `dub_generate.py` (2,014 lines) imports fit, duration, voice leases, render staging and TTS. `tts_backend.py` (4,978), `model_manager.py` (4,737) and `asr_backend.py` (4,514) are large shared hubs. Extracting dubbing means re-creating job store, events, leases, media tools and UI. `SOURCE_VERIFIED`, line counts. |
| Size | 4,692 files, about 1.41M newline count. The donor is already a complete app. |
| Tests | 869 Python test files with 8,722 test functions, 753 Electron unit test files and 135 `electron/tests` files. Cross-OS CI is green on `200286c`. A transplant forfeits most of this. |
| Process isolation and cancellation | Per-engine venvs and sidecars, `contained_subprocess.py` (Windows kill-on-close jobs, per the prior study), `inference_cancellation.py` (unchanged), and the new "GPU work in a process that can die" (`f6fb94e6a`). Caveat: the **default** OmniVoice engine is in-process. Cancellation conformance must cover in-process paths, or the fork must default to a subprocess engine. |
| Cross-platform packaging | NSIS, DMG, AppImage, deb, Snap and mobile pipelines already exist. Transplanting would rebuild them. |

Qualifications and counter-evidence:

1. **Dependency weight.** Base dependencies pull gradio, yt-dlp, posthog, litellm, boto3, google-auth, openai, demucs, whisperx and pyannote. A fork inherits them until pruned, and each prune is a delta with tests.
2. **Velocity.** About 118 commits/day upstream. Use a pinned fork with time-boxed rebase windows. Keep deltas in isolated files or flags so rebases stay mechanical.
3. **Open-core drift.** Pro features have moved out (#2748). A cloud account and sync path now exists. The CLA lets the company relicense. Future upstream may remove features from the AGPL repo. Treat upstream as a source, not a dependency guarantee.
4. **Engine gap.** The plan's Arabic candidate, Chatterbox Multilingual, is not a native VS engine. It needs a new VS-pattern subprocess engine adapter (WS-06).
5. **NC default.** The default weights are non-commercial, so a default-engine change is mandatory (WS-02).
6. **AGPL.** If WisprStudio's modified backend is ever offered over a network, AGPL §13 source-offer obligations apply, unless the founder's grant covers it. Keep the per-file grant-scope flag (Opus O2).

**Minimum safety deltas on the fork.** Each is a FORK_DELTA with a test:

| Delta | Change | Acceptance test |
|---|---|---|
| D1 Analytics off | Remove the committed PostHog token and `posthog`/`posthog-js` usage, or compile it out. Force the kill switch. Remove the uninstall ping. | Static scan finds no `phc_` or `posthog.com`. Egress capture shows 0 connections through first-run, setup, generate and export. |
| D2 Account and cloud sync off | Blank `clientId` for all envs (`cloudAccountsAvailable()`→false), or strip `electron/src/main/account/` and `api/routers/cloud_sync.py`. Remove sync migrations from the default path. | No account UI. `/api/cloud-sync/*` returns 404. No `voicestudio.sh` DNS. |
| D3 Updater | Repoint to a Wispral-signed feed or manual check. No auto check to `debpalash` endpoints. | No request to `github.com/debpalash` in 6-hour soak. |
| D4 URL ingest off | Disable `/dub/ingest-url`, `/gallery/search/youtube`, `/gallery/download`, the yt-dlp overlay, community submit-url and marketplace import. Drop `yt-dlp` from base dependencies. | Routes return 404 or 403. `import yt_dlp` fails in the bundle. |
| D5 Mirrors and model egress | Set `OMNIVOICE_HF_ENDPOINT_MODE=manual`. Remove the `hf-mirror.com`, `gh-proxy.com`, `ghproxy.net` and aliyun defaults. Stage the runtime and weights from a Wispral-hashed manifest. Offline mode blocks all model hubs. | Offline install from a staged bundle succeeds. With the network blocked, there are 0 connection attempts. Manifest hash mismatch rejects the artifact. |
| D6 Consent before cloning | Require a consent-ledger reference (subject, purpose, reference-artifact hash, revocation epoch) on generation with a cloned profile, `dub_generate` speaker clones, voice conversion and design-to-clone. Enforce in the backend at admission **and** at dispatch. | 100% of clone-class requests without valid consent rejected (fixture matrix). Plain preset-voice synthesis unaffected. |
| D7 Revoked-voice blocking | `DELETE /profiles/{id}/consent` (`profiles.py:1346`) increments the epoch. Queued jobs referencing the profile are cancelled. Late outputs are discarded. | Revoke during a queued batch: no new audio is published for that profile, and stale outputs are rejected. |
| D8 Cancellation semantics | Map `inference_cancellation` and the subprocess kill to request, acknowledgement and stopped-or-unconfirmed states. Prefer a subprocess default engine. | Cancel during load, generate and mux. No orphan processes. Lease is released only after observed stop. |
| D9 Fit guard (M4 revised) | `validate_fit_inputs()` in a separate file, called before `plan_fit` at `dub_generate.py:1595`. Rejects non-finite or negative durations, `end<start` and a non-finite total. **Allows overlaps.** | The 5 invalid probe cases raise typed errors. Overlap gives 10.0. Upstream fit fixtures stay bit-identical. |
| D10 NC weights quarantine | Change the default from OmniVoice. Exclude NC/OpenRAIL/custom weights (OmniVoice*, OuteTTS, NLLB, IndexTTS pending, Supertonic pending) from the default bundle, behind an explicit research flag. | SBOM and model manifest: 0 NC weights in the default bundle. |
| D11 Watermark | Keep invisible AudioSeal on and make it non-disableable for cloned voices. Resolve the AudioSeal weight licence first. | Detection succeeds on exported MP3 and WAV for cloned outputs (local detector). |
| D12 Online translation and LLM off by default | Translation and LLM run only as explicit provider actions. Source and edited text are preserved. | Default dub run uses only local translation, or fails visibly. |

---

## 5. Competitors (brief)

Accessed 2026-11-08. Only confirmed items are listed.

| Vendor | Confirmed facts | Evidence |
|---|---|---|
| ElevenLabs PVC | You may only clone your own voice. A verification recording is required before fine-tuning, with a 24 h retry on failure. 30 min minimum, 2–3 h recommended. PVC slots: Free/Starter 0, Creator/Pro 1, Scale 3, Business 10. Arabic is listed for the Eleven v4 family. | `DOCUMENTED` https://elevenlabs.io/docs/product-guides/voices/voice-cloning/professional-voice-cloning |
| ElevenLabs Dubbing Studio | **In maintenance mode** (critical fixes only). Transcript and translation editing, speaker reassignment, split/merge, clip regeneration with history, SFX and voiceover tracks. Exports AAC, MP3, WAV, zipped tracks, **AAF**, SRT and CSV. Free-plan dubs are watermarked with no removal. | `DOCUMENTED` https://elevenlabs.io/docs/product-guides/products/dubbing/dubbing-studio |
| ElevenLabs Studio | Chapters (up to 500), multi-voice paragraphs, pronunciation alias and phoneme tags (**phoneme only on Eleven Flash v2**), MP3/WAV per chapter or ZIP, video projects with a multi-track timeline, free-plan video watermark. | `DOCUMENTED` https://elevenlabs.io/docs/product-guides/products/studio |
| ElevenLabs pronunciation dictionaries | HTTP 403 | `BLOCKED_EXTERNAL` https://elevenlabs.io/docs/product-guides/tools/pronunciation-dictionaries |
| Cartesia | Instant clone from 10 s (up to 60 s used on Sonic 3.6+). Pro clone needs 30+ min. The page states no consent mechanism. Languages are added via an "Add Voice Accents" API. | `DOCUMENTED` https://docs.cartesia.ai/build-with-cartesia/capability-guides/clone-voices |
| Resemble AI | PerTh is an MIT-licensed open-source neural watermark, on by default in Chatterbox outputs. PerTh Multimodal (enterprise) is not open. The Watermarker also reads SynthID and C2PA. Resemble Detect does deepfake detection. | `DOCUMENTED` https://www.resemble.ai/watermarker/ |
| Voicebox | MIT. "8 TTS engines" including Chatterbox Multilingual (Arabic) and Qwen3 VoiceDesign. Stories multi-track timeline editor. REST API plus MCP server. Windows CUDA MSI. | `SOURCE_VERIFIED` VB@`8af7efe` README.md |
| Descript | The help page fetched did not cover AI voices | `NOT_VERIFIED` (https://help.descript.com/hc/en-us/articles/10164098416909) |
| Rask, HeyGen, Murf, Adobe Podcast | Not fetched | `NOT_VERIFIED` |
| All pricing | Not established in this pass | `NOT_VERIFIED` |

**Parity snapshot.** Y = present; P = partial; — = not found or not verified.

| Capability | WisprStudio (VS fork + deltas) | ElevenLabs | Cartesia | Resemble | Voicebox |
|---|---|---|---|---|---|
| Long-form chapters | Y (longform/audiobook) | Y | — | — | P (stories) |
| Multitrack timeline | **P** (dub timeline; no DAW multitrack) | Y (Studio video, Dubbing) | — | — | Y |
| Professional clone with verification | P (consent recording, not enforced) | Y | P (no consent stated) | — | — |
| Dubbing editor plus AAF export | Y / **no AAF** | Y / Y | — | — | — |
| Pronunciation phoneme rules | **No** (respelling only) | Y (Flash v2) | — | — | — |
| Watermark plus detector | Y (AudioSeal; licence unresolved) | Free-tier watermark | — | Y (PerTh, Detect) | — |
| Arabic TTS, commercial-clean, local | P (VoxCPM2 / MOSS-Nano records; cards `NOT_VERIFIED`) | Y (cloud) | — | — | Y (Chatterbox ML) |
| Offline / local API | Y (after D1–D5) | — | — | — | Y |

**Differentiation opportunities, each with a measurable test:**

1. **Offline Arabic dubbing.** Run with the network blocked at the OS firewall, using staged artifacts. Pass: the run completes ASR→translate→fit→TTS→mix with **0 outbound connection attempts** (packet capture). No vendor in §5 documents an offline dubbing studio.
2. **Consent-ledger enforcement.** Fixture matrix of 4 clone paths × {no consent, valid, revoked, artifact-hash mismatch}. Pass: 100% correct accept or reject. Revocation cancels queued jobs within a fixed deadline, measured, and late output is discarded.
3. **Resume after crash.** Kill the backend during a long-form render. Pass: on restart only incomplete segments regenerate (count), and output equals the uninterrupted run byte-for-byte with the deterministic `_echo` engine.
4. **Commercial-clean default bundle.** SBOM plus model manifest. Pass: 0 NC or unreviewed weights in the default install, and every artifact has a hash and card revision.
5. **Arabic-aware pronunciation.** Pass: P2 clitic cases (`ومحمد`, `بالرياض`) and a 50-item frozen Arabic and Gulf panel apply the lexicon correctly, with no false positives on a negative set.
6. **Watermark on every cloned output.** Pass: the local detector flags 100% of cloned exports across WAV, MP3 128k and AAC re-encode. The false-positive rate on 100 non-generated clips is reported.
7. **No telemetry or account by construction.** Pass: static scan plus 6 h soak egress capture show only user-initiated destinations.
8. **Overlapping-speaker fit correctness.** Pass: the overlap fixture total is 10.0, the guard rejects the 5 invalid inputs, and export subtitles align to the mapped piecewise timeline.

Quality, latency and market claims: none made.

---

## 6. What must genuinely be built new for the MVP

| # | New capability | Inspected | Why insufficient | Smallest missing piece | Confinement | Test and maintenance cost |
|---|---|---|---|---|---|---|
| N1 | Consent-ledger binding and policy gate | `VS@058 profiles.py:1212-1360`; `speaker_clone.py`; `generation.py`; `dub_generate.py`; VB `models.py` (prior) | Flags exist, but synthesis paths never check them (`profiles.py:1215-1216`, plus grep showing absence in generation and dub paths). No artifact hash or revocation epoch. | Ledger record plus `require_clone_consent(profile, artifact_hash)` at admission and dispatch | One new module plus call sites in 4 routers (FORK_DELTA) | About 40 fixture tests. Each rebase re-checks call sites. |
| N2 | Egress policy and allowlist enforcement | `services/outbound_http.py` (trusted endpoint sub-path allowlist `:37-90`), `core/url_safety.py`, `endpoint_race.py` | Guards SSRF on chosen endpoints. No global deny-by-default or offline mode across Electron main and backend. | Central allowlist checked by the Electron `net` session and the Python HTTP clients, plus an offline flag | Electron session hook plus one Python module | Egress capture test in CI. Low upkeep. |
| N3 | Arabic clitic-aware lexicon | `pronunciation.py` (`REPRODUCED` gap) | `\b` whole-word only | Optional proclitic stripping (و ف ب ك ل ال وال بال …) before matching | Additive function next to `apply_lexicon` | Probe and panel tests. Small. |
| N4 | Chatterbox Multilingual engine adapter (WRAP) | CB@`5de7a54a` `mtl_tts.py`; VB chatterbox backend (MIT); VS engine pattern `engines/*/`, `_venv_probe.py` | Not a native VS engine on Windows/Linux | One own-venv subprocess engine using VS `SubprocessBackend`, with pinned weights and Perth | `backend/engines/chatterbox_mtl/` only | Engine contract tests with the `_echo` pattern. A third venv to maintain. |
| N5 | Wispral contract bridge | VS REST/MCP; Wispral core (prior) | Donor has no Wispral job, consent or cancel message contract | Thin adapter mapping Wispral job, consent and cancel to VS routes and events | `adapters/studio/` outside the fork | Contract fixtures |
| N6 | Arabic and Gulf evaluation harness | VS `omnivoice/eval` extras (jiwer, funasr) | No Arabic dialect panels or consent-approved references | Frozen panels plus a WER/CER runner using an independent ASR | Eval-only package | Human study cost is outside code |

**Not to build:** timeline, dubbing orchestrator, fit/duration planners, long-form renderer and resume, model manager, subtitle stack, project bundles, packaging. All exist in VS@058 with tests.

---

## 7. MVP work packets

All packets are non-executable until Wispral governance opens the applicable Grain. The donor is `VS@058` (`200286ccff6f28faaf51bb08b2a5b54c460b39f4`) unless stated.

| ID | Depends on | Donor / path | Decision | Files affected | Acceptance criteria | Tests | Security risks | Rollback |
|---|---|---|---|---|---|---|---|---|
| WS-00 Fork baseline | — | Whole repo @`200286c` | FORK | `forks/wisprstudio/**`; `DELTA_REGISTER.md`; NOTICE and grant flags | Upstream suites run locally with recorded collected, pass, fail and skip counts (`pytest tests`, `pytest backend/tests`, `bun run test`, `check:electron`) | Donor suites unchanged | Supply chain: uv.lock, bun.lock, GitHub wheel URLs | Discard fork branch |
| WS-01 Egress strip | WS-00 | `core/analytics.py:44-58`; `electron/src/shared/utils/analytics.ts`; `config/account.json`; `electron/src/main/account/*`; `api/routers/cloud_sync.py`; `updater.ts:21-22`; `index.ts:322-329`; `endpoint_race.py:58`; `runtime-project.ts:240,260` | FORK_DELTA (D1–D5, D12) | As listed | 0 non-allowlisted connections across install, first-run, generate, dub and export. No account UI. | Static scan, egress capture, route 404 tests | Missed path (E-table drift on rebase) | Feature flags restore upstream behavior |
| WS-02 Default engine and NC quarantine | WS-00 | `core/prefs.py:9`; `tts_backend.py:4561`; `config/models.yaml:48-51`; `model_licenses.json` | FORK_DELTA (D10) plus card verification | Prefs, catalog, bundle manifest | Default engine has a `DOCUMENTED` permissive card at a pinned revision. 0 NC weights bundled. | Manifest and SBOM check; generate with the new default via the `_echo` engine in CI | Licence misread; tokenizer terms | Revert default; NC behind research flag |
| WS-03 Fit guard | WS-00 | `services/fit_planner.py` (unchanged); `dub_generate.py:1584-1595` | COPY plus new guard | `services/fit_inputs.py` (new) and 1 call site | The 5 invalid cases are rejected and overlap is allowed (P1) | Opus probe, upstream fit tests, overlap fixture | None new | Remove call |
| WS-04 Consent gate and revocation | WS-00, N1 design | `profiles.py:1242-1360`; `generation.py`; `dub_generate.py`; `voice_conversion.py`; `speaker_clone.py`; `core/voice_leases.py` | FORK_DELTA (D6, D7) plus BUILD_NEW ledger | New `services/consent_ledger.py`; migration; 4 call sites | 100% fixture-matrix correctness. Revoke cancels queued work and late outputs are dropped. | About 40 tests | Bypass via MCP, OpenAI-compatible or batch routes | Flag off, which logs only |
| WS-05 Cancellation conformance | WS-00 | `inference_cancellation.py`; `subprocess_backend.py`; `contained_subprocess.py`; `gpu_sandbox.py` | FORK_DELTA (D8) | Adapter plus tests | Request, acknowledgement and stopped-or-unconfirmed states. No orphans. Lease released after stop. | Kill and stall fixtures with `_echo` | GPU memory leak, in-process engines | Keep upstream semantics; mark unconfirmed |
| WS-06 Chatterbox Multilingual engine | WS-02, WS-05 | CB@`5de7a54a` `src/chatterbox/mtl_tts.py`; VB backend (reference); VS `engines/*` pattern | WRAP (BUILD_NEW adapter) | `backend/engines/chatterbox_mtl/` plus registry line | Offline load from a staged manifest. Arabic accepted. Reference length precheck. Perth watermark recorded. | Engine contract tests. Quality is `NOT_RUN` until the panel study. | Perth from git `@master` must be pinned | Remove registry entry |
| WS-07 Arabic lexicon | WS-00 | `services/pronunciation.py:113` | ADAPT (N3) | Additive module plus tests | P2 cases pass with no regressions on upstream tests | Probe plus panel | ReDoS (keep `re.escape` alternation) | Flag off |
| WS-08 Offline staging manifest | WS-01 | `model_manager.py`; `hf_revisions.py`; `segmented_download.py`; `runtime-project.ts` | FORK_DELTA (D5) | Manifest reader | Offline install from a hashed bundle. Mismatch rejected. | Network-blocked CI job | Tampered bundle | Online mode, with confirmation |
| WS-09 Watermark hardening | WS-02 | `services/watermark.py:327-348,485-509` | FORK_DELTA (D11) | Prefs plus clone path | Cloned outputs always marked. Detector verifies after re-encode. | Detection fixtures | AudioSeal licence unresolved, which blocks the release | Revert to upstream pref |
| WS-10 Wispral contract bridge | WS-04, WS-05 | VS REST/MCP; Wispral core | BUILD_NEW (N5) | `adapters/studio/` | Contract fixtures pass | Contract tests | Auth between core and backend (loopback plus key) | Disable adapter |
| WS-11 Packaging and signing | WS-01 | `electron/electron-builder.config.mjs:212-231` | FORK_DELTA | Builder config, signing CI | Signed Wispral NSIS. Feed points to Wispral. | Installer contract tests (upstream) | Unsigned upstream installers | Previous build |
| WS-12 Upstream sync policy | WS-00 | — | PROCESS | `DELTA_REGISTER.md` | Each rebase re-runs WS-01, WS-03 and WS-04 tests plus the egress table diff | CI gate | Silent re-introduction of egress or Pro removals | Stay on prior pin |
| WS-13 Arabic eval harness | WS-06 | VS `[eval]` extras | BUILD_NEW (N6) | Eval package | Frozen MSA and Gulf panels; WER/CER with independent ASR; consented references only | — | Consent of panel voices | — |

---

## 8. Open items (honest gaps)

- Suites, installs, runtime egress, audio quality, GPU behavior and first-run sizes: `NOT_RUN`.
- Official model cards for VoxCPM2, MOSS-TTS(-Nano), IndexTTS-2.5, Supertonic-3, Confucius4, AudioSeal and the CosyVoice GGUF conversion were **not re-fetched in this pass** (`NOT_VERIFIED`). WS-02 and WS-09 are blocked on them.
- The default dub translation provider was not established. Competitor pricing and the Descript, Rask, HeyGen, Murf and Adobe facts were not verified.
- VoiceStudio's own sanctioned-network-calls doc (`7091a12ff`) was not reviewed. Diff it against the §2.5 table at WS-01.
