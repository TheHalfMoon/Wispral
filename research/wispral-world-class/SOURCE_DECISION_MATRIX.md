# Source decision matrix (re-pinned 2026-11-08)

**Status:** CANDIDATE. Supersedes the *pins* (not the mechanism evidence) in PR #124's [transplant matrix](../rea/2026-10-21/SOURCE_TRANSPLANT_MATRIX.md), whose 96 source anchors PR #125 re-verified at the 2026-10-21 pins. Every row below was re-read at the listed revision on 2026-11-08 by the research passes whose full reports are in [evidence/research-reports/](evidence/research-reports/WISPRSIDE_SOURCE_RESEARCH.md). No donor was built, installed or run unless the row says `REPRODUCED`.

**Rights columns are separate:** "Public license" is what the repository declares (`SOURCE_VERIFIED`). "Founder grant" records `FOUNDER_SOURCE_AUTHORIZATION=YES_CONFIRMED_BY_FOUNDER` for founder-supplied or founder-owned sources; the private documents were not requested or inspected. Weight, dataset, font and voice rights are never inferred from either.

**Open rights item:** the Wispral repository itself has **no LICENSE file** (`gh api` license = none, `SOURCE_VERIFIED`). The founder must choose Wispral's outbound license before any code is copied into it (decision Q-01 in the [handoff](FINAL_HANDOFF.md)).

## Summary of lead decisions

| Product | Lead donor and pin | Mode | Previous pin | Why re-pinned |
| --- | --- | --- | --- | --- |
| WisprSide | `cjpais/Handy@73cc8579cff74e97e08de9d86035a92e4335ff7f` (v0.10.0 + TLS fixes, 2026-11-06) | FORK | `93c9ee05` | Three security fixes after the old pin; CI green on 9 check runs (`REPRODUCED` via API); plan-relevant modules unchanged |
| WisprStudio | `debpalash/VoiceStudio@200286ccff6f28faaf51bb08b2a5b54c460b39f4` (v0.5.8) | FORK | `28bf2c7a` | 2,124 upstream commits in 18 days; v0.5.8 has security floors, the overlapping-speaker fit fix, a post-CLA clean-room provenance wave, CI green (29/0). No v0.5.8 installers exist (release startup failure); v0.5.7 `beeaae08` binaries are the observation baseline |
| Klaint | `emcie-co/parlant@2a463ccd10eaf0d70d42731705f4f00ef066bee8` (v4.0.2), **conditional on spike KT-01**; fallback `61bba3b2b3fffd677d345e393e8c942dbd400297` (v3.3.2) | WRAP (one process per tenant) | `ea737442` | Parlant 4 is a breaking rewrite (strict canned responses, journeys, evaluations API and the Plan hook were removed). v3.3.2 is the last release with `CANNED_STRICT` |
| Core | Sentrdel `f5747319`, Orcel `f0b78e65`, Ascout `48902389`, SafeEvidence `f05bc006`, ACP rust-sdk `050cd94c` (5.0.0) | ADAPT / COPY | Orcel `57af189b`, ACP `652d1003` | New `orcel-journal` and `orcel-platform` modules; SafeEvidence egress gates; ACP rust-sdk moved two majors |

## WisprSide

| ID | Capability | Source (repo@sha:path) | Public license / founder grant | Decision | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| SD-SRC-01 | Whole application (recorder, hotkeys, coordinator, engine supervisor, model manager with 76-model offline catalog, paste incl. receipt transaction, overlay, settings, history, tray, i18n incl. `ar` RTL, updater, CLI, portable mode, NSIS/MSI) | `cjpais/Handy@73cc857` | MIT / not required | **FORK** | `SOURCE_VERIFIED` module map; 368 Rust test definitions in 43 files (`REPRODUCED` count, not run); 0 Windows insertion tests | Baseline suites `NOT_RUN` (packet SD-M0) |
| SD-SRC-02 | Receipt-based clipboard transaction (snapshot, delayed render, sequence-guarded restore, history-exclusion formats) | `Handy@73cc857:src-tauri/src/paste_tx/windows.rs` | MIT | FORK_DELTA (make default on Windows) | `SOURCE_VERIFIED`; default `reliable_paste=false` (`settings.rs:1055`) | Reports "Typed" before any receipt today |
| SD-SRC-03 | Fail-closed insertion algorithm (double re-verification; `inserted / notInserted / unverified / unavailable`) | `zachlatta/freeflow@37786464bb2422c58313d7456fe7191d115d0d18:Sources/AppTextInsertionCore.swift:3-137` | MIT | ADAPT (algorithm; Windows calls are new) | `SOURCE_VERIFIED` | macOS AX implementation; tests not run |
| SD-SRC-04 | Windows UIA editable/password probe; `GetExeName` | `OpenWhispr/openwhispr@cb08c411dd008c57e4f0a8193756d6b5812479fd:resources/windows-text-monitor.c:226-293`, `windows-fast-paste.c:64-85` | MIT | ADAPT (idea) | `SOURCE_VERIFIED` | **REJECTED parts:** foreground fall-through (`windows-fast-paste.c:281-291`, byte-identical to old pin), nircmd/PowerShell fallback, "unknown exe is foreign" predicate, focus stealing |
| SD-SRC-05 | Terminal class/exe lists for app profiles | `OpenWhispr@cb08c41:resources/windows-fast-paste.c:31-53` | MIT | COPY (lists) | `SOURCE_VERIFIED` | RC tier |
| SD-SRC-06 | Delivery outcome vocabulary; surrogate-safe chunked typing concept | `Beingpax/VoiceInk@4bc74caddfad6fdfab71e5957451b83b33c1a2c5:.../Paste/CursorPaster.swift:11-14` | GPLv3 | REFERENCE (concept only, no code) | `SOURCE_VERIFIED` | Founder grant may be invoked per file if code is ever needed |
| SD-SRC-07 | LLM cleanup output guard ("…no wait Friday" → "Friday") | `OpenWhispr@cb08c41:src/utils/cleanupOutput.ts` + tests | MIT | ADAPT (TS → Rust validator) | `SOURCE_VERIFIED`; 17 OpenWhispr pure tests `REPRODUCED` in PR #124 (older pin) | RC tier |
| SD-SRC-08 | Snippets | `OpenWhispr@cb08c41:src/components/SnippetsView.tsx` | MIT | ADAPT | `SOURCE_VERIFIED` | RC tier |
| SD-SRC-09 | Offline-egress CI gates (dependency denial, no-socket checks, isolated run) | `TheHalfMoon/SafeEvidence@f05bc006185d67f13ca00ecc7b697c6aef0703dc:product/deny.toml:31-47`, `tools/ci/{core_no_sockets.py,ta29_dependency_denial.py,ta03_isolated.sh,network_trace_report.py}` | Apache-2.0 / founder-owned | ADAPT | `SOURCE_VERIFIED` | Its Windows path is self-labelled "weaker"; the Windows-strength design is new (BN-01d) |
| SD-SRC-10 | PID-reuse-safe process identity (`ProcessGeneration`, `GetProcessTimes`) | `TheHalfMoon/Orcel@f0b78e6544cf6ea9c2457a6b6f483490c7bd0f6f:crates/orcel-platform/src/process.rs:40-65` | Apache-2.0 (file adapts MIT Cua code; keep its notice) / founder-owned | ADAPT | `SOURCE_VERIFIED` | |
| SD-SRC-11 | Local ASR engines | Handy's `transcribe-cpp 0.4.0` (ggml) inside the fork; catalog entries | MIT (engine); per-model weights vary | WRAP (inherited) | Catalog lists 17 models with `ar` (`REPRODUCED` count) | Model rights per manifest; quality `NOT_MEASURED` |

## WisprStudio

| ID | Capability | Source | Public license / founder grant | Decision | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| ST-SRC-01 | Whole application (Electron + FastAPI backend; projects, timeline, script editor, per-engine subprocess envs, model acceptance, consent capture, watermark, long-form resume, dubbing, export, MCP/REST) | `debpalash/VoiceStudio@200286c` | AGPL-3.0-only (LICENSE byte-identical to old pin) / **founder grant confirmed**, recorded per copied file | **FORK** | `SOURCE_VERIFIED`; 869 Python test files, 753 Electron unit tests (counts, not run) | Upstream adds a CLA workflow and is drifting toward open-core (Pro remote workers, cloud sync); scheduled rebase windows, not continuous tracking |
| ST-SRC-02 | Duration fit planner | `VoiceStudio@200286c:backend/services/fit_planner.py` (sha256 `9096f6a3…`) | AGPL-3.0 / grant | COPY unchanged + new `fit_inputs.py` guard | `REPRODUCED`: NaN, Inf, negative, end-before-start and NaN-total still accepted; **overlap is now intentional and must stay allowed** | Revises Opus M4 |
| ST-SRC-03 | Pronunciation lexicon | `VoiceStudio@200286c:backend/services/pronunciation.py:113` | AGPL-3.0 / grant | ADAPT (+ Arabic proclitic-aware matching) | `REPRODUCED`: misses `ومحمد`, `بالرياض` | |
| ST-SRC-04 | Consent flags and profiles | `VoiceStudio@200286c:backend/api/routers/profiles.py:1212-1360` | AGPL-3.0 / grant | FORK_DELTA + new ledger | `SOURCE_VERIFIED`: synthesis, dubbing and clone paths **never check consent** (`profiles.py:1215-1216` comment + grep) | BN-03 |
| ST-SRC-05 | Cancellation and containment | `backend/services/{inference_cancellation,subprocess_backend}.py`, `backend/core/contained_subprocess.py` | AGPL-3.0 / grant | FORK_DELTA (map to contract states) | `SOURCE_VERIFIED` | |
| ST-SRC-06 | Chatterbox Multilingual (Arabic-listed TTS) | `resemble-ai/chatterbox@5de7a54a:src/chatterbox/mtl_tts.py` | MIT code; weights per model card | WRAP as a new subprocess engine | `SOURCE_VERIFIED` | Not a native VoiceStudio engine on Windows/Linux; upstream README says Multilingual V3 was retired in August 2026 (models report) — maintenance risk R-05 |
| ST-SRC-07 | Default TTS engine | OmniVoice (VoiceStudio default, `core/prefs.py:9`) | **Non-commercial weights** | **REJECTED as default** | `SOURCE_VERIFIED` (`model_licenses.json`) | Default must change to a permissively licensed engine with a verified card (packet ST-D02) |
| ST-SRC-08 | Generation fallback / zero-volume export regression | `jamiepine/voicebox@8af7efe62fab8d33e2a5dfbedabaa45f68a5184f` | MIT | REFERENCE | No drift since old pin | |
| ST-SRC-09 | Watermark | VoiceStudio `services/watermark.py:327-348,485-509`; Resemble PerTh | PerTh MIT; AudioSeal weight license unrecorded | FORK_DELTA (force on cloned output) | `SOURCE_VERIFIED` | AudioSeal license must be resolved before release |

## Klaint

| ID | Capability | Source | Public license | Decision | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| KL-SRC-01 | Dialogue engine (rules, policies, tools, retrievers, sessions, customers, SDK) | `emcie-co/parlant@2a463cc` (v4.0.2); fallback `61bba3b` (v3.3.2) | Apache-2.0 | WRAP, one process per tenant | `SOURCE_VERIFIED` | v4 has **no tenant concept**, defaults to allow-all dev mode and OpenRouter; built-in tool server on `127.0.0.1:8818` has no auth and trusts caller IDs |
| KL-SRC-02 | Tool review gate | `parlant@2a463cc:src/parlant/core/engines/compass/hooks.py:128-151`, `loop/base_loop.py:996-1093` (`on_reviewing_tool_calls` RESOLVE/BAIL) | Apache-2.0 | ADAPT (gate + bypass closure) | `SOURCE_VERIFIED`: tools also run via context-variable refresh (`variable_loader.py:169-181`), the plugin port (`plugins.py:851-862`), and the lowest effort level skips model review | The broker remains the sole executor of consequential tools |
| KL-SRC-03 | Approved-response control | `parlant@2a463cc` `on_message_generated` BAIL in BLOCK mode (`hooks.py:149-150`); `docs/canned-responses.md:286-316,457-461` | Apache-2.0 | ADAPT (commitment guard) | `SOURCE_VERIFIED`: "The model always writes the final text itself" in v4 | Works only for non-streamed replies; streaming voice needs a separate guard (KV-02) |
| KL-SRC-04 | Retrieval | `parlant@2a463cc:sdk.py:1747-1790` | Apache-2.0 | WRAP | `SOURCE_VERIFIED` | Tenant index fixed per process |
| KL-SRC-05 | Human inbox and takeover | `chatwoot/chatwoot@caab07a8f00032d5205b5a5d7e2eb0ba2f3d2d82` (v4.19.1) via Agent Bot API | MIT outside `enterprise/` | API_INTEGRATION (unmodified) | `SOURCE_VERIFIED`: bot tokens are account-wide; webhooks at-least-once; `bot_handoff!` not race-safe; one bot provider per inbox | One Chatwoot account and bot per tenant; Klaint-side ownership epoch and delivery dedupe |
| KL-SRC-06 | Webhook signatures | `standard-webhooks/standard-webhooks@ab68441` (`webhooks.py:54-160`) | Apache-2.0 | ADAPT | `SOURCE_VERIFIED` | Rejects future/NaN/stale timestamps; replay cache |
| KL-SRC-07 | Simulation and deterministic scoring | `sierra-research/tau2-bench@033bf08` (`src/tau2/evaluator/evaluator_env.py:17-126`) | MIT | ADOPT as test dependency | `SOURCE_VERIFIED` | Replaces the removed Parlant evaluations API; LLM judges advisory only |
| KL-SRC-08 | Voice pipeline (later) | `pipecat-ai/pipecat@fda1d5e0cde9625c8dcef7b653ed731c2ce63672` (v1.15.0) | BSD-2-Clause | ADAPT inside the same tenant process | `SOURCE_VERIFIED`: barge-in cancels in-flight function calls by default | **No mutating tools inside Pipecat**; Kokoro auto-download disabled |
| KL-SRC-09 | Connector schemas | `botpress/botpress@956bcdef7a8f6499519e28ec5dda6e3ed3c96ad8` | MIT | REFERENCE | `SOURCE_VERIFIED` | Thin Python connectors are new |
| — | Rejected | Rasa (maintenance mode), LangGraph, OpenAI Agents SDK, Letta, Temporal, llm-guard (archived), Zammad/FreeScout (AGPL), DeepEval, NeMo-Guardrails, LiveKit Agents (reference only) | — | REJECTED / REFERENCE | Klaint and Core reports | Avoids a second dialogue engine or runtime |

## Wispral Core

| ID | Artifact | Source | License | Decision | Evidence |
| --- | --- | --- | --- | --- | --- |
| CO-SRC-01 | Policy lattice + undecidable resolution + narrowing | `TheHalfMoon/Sentrdel@f5747319a50831ef7cee983d253c0ca5503c9a64:crates/sentrdel-policy/src/{lib.rs:125-221,narrowing.rs:58-100}` | Apache-2.0 / founder-owned | ADAPT → `wispral-policy` (drop regorus/schemars) | sha256 of `narrowing.rs` reproduced; HEAD = pin |
| CO-SRC-02 | Bounded JSON preflight | `Sentrdel@f5747319:crates/sentrdel-engine/src/bounded_json.rs:8-13,55` | Apache-2.0 | ADAPT (generic dialect + byte cap) | `SOURCE_VERIFIED` |
| CO-SRC-03 | Intent journal (fsync, torn-tail sealing, exclusive writer, recover fails closed) | `Orcel@f0b78e65:crates/orcel-journal/src/{lib.rs,resume.rs}` | Apache-2.0 | **COPY** (renamed `wispral-journal`, notice kept) | `SOURCE_VERIFIED`; state table copied into [effect_intent transitions](../../docs/engineering/contracts/transitions/effect_intent.json) |
| CO-SRC-04 | Same-user local IPC identity | `Orcel@f0b78e65:crates/orcel-platform/src/{peer.rs:68,113;acl.rs}` | Apache-2.0 | ADAPT | `SOURCE_VERIFIED`. **`orceld/src/app_api.rs` and two `orcel-approval` files are FSL-1.1-MIT third-party: REFERENCE ONLY** |
| CO-SRC-05 | Model descriptor | `TheHalfMoon/Ascout@48902389ec37019845fd67c8b8c53c5f499ffc85:src/assurance/contracts/engine-descriptor.ts:45` | Apache-2.0 | ADAPT → `model_manifest` | Bytes identical at HEAD `32d02a02` |
| CO-SRC-06 | Local HTTP auth profile | `TheHalfMoon/Ninerr@616bafaa26a58476bb2e3ee876b28e13ac1348f3:packages/studio-host/src/server.ts:86-88,445-468` | Apache-2.0 | ADAPT (pattern) | `SOURCE_VERIFIED` |
| CO-SRC-07 | Network policy for connectors | `Ninerr@8cba15c4:packages/network-policy/src/policy.ts` | Apache-2.0 | REFERENCE now; Python port later (deferred) | Unchanged since pin |
| CO-SRC-08 | Agent Client Protocol | `agentclientprotocol/rust-sdk@050cd94c081056ace37a7b89abfed7f6220b47eb` (5.0.0) | Apache-2.0 | WRAP (later developer-agent module) | Old anchors stale (`capabilities.rs` removed); ACP HTTP transport has no auth, so stdio only |
| — | Rejected | Yamakan (now GPL-3.0 combined, reference only), Hala (model training), Gomrey, paradigm, Zain (renamed WePLD), and other private founder repositories screened without a Wispral-relevant module (names withheld from this public repository) | — | REJECTED / REFERENCE | Core report §5 |

## Models (rights screen, not quality)

Full matrix with code vs weight licenses, Arabic claims and CPU feasibility: [models and Arabic research report](evidence/research-reports/MODELS_ARABIC_RESEARCH.md) and [model strategy](../../docs/engineering/WISPRAL_MODEL_STRATEGY.md). Non-commercial or restricted weights flagged so far: OmniVoice, F5-TTS, XTTS-v2, Fish-Speech 1.5, Voxtral-4B-TTS, MMS/Seamless, NLLB, OuteTTS, DiariZen, tiny-aya; Moonshine legacy Arabic Base/Tiny (revenue cap); TEN VAD (non-compete clause).
