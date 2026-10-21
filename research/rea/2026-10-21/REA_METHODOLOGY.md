# REA methodology, coverage and limits

This study separates direct source inspection from runtime reverse engineering. Source findings are bounded to pinned modules and traces. Browser observations describe the page and actions actually observed. Neither a README nor a successful homepage navigation establishes product accuracy, privacy, cancellation or supported platforms.

## Evidence vocabulary

| Label | Meaning |
| --- | --- |
| DOCUMENTED | An official source states a capability; no independent runtime verification |
| SOURCE_VERIFIED | A concrete source mechanism was inspected at an immutable revision with path/hash/anchor |
| RUNTIME_OBSERVED | A tool captured actual behavior within its stated observation window |
| REPRODUCED | A recorded mechanism experiment was replayed with stated inputs and environment |
| NOT_RUN | No valid experiment result exists for the claim |
| BLOCKED_EXTERNAL | A named access/tool/hardware constraint prevents the specified trial |

These labels apply to individual claims. A repository can have SOURCE_VERIFIED policy code and NOT_RUN application workflows simultaneously. Test names and source byte acquisition are not executed coverage. No model accuracy, speech quality, latency, GPU footprint or installed product support was measured in this mission.

## Official REA tool use

The official repository `morluto/rea` was read at `7c6c25dda75e2d1d595a6cacc5cf9a82607f8502`. Executed tooling was the already available **rea-agents 6.3.0** package; repository main declared 6.7.0, which was not silently substituted as the executed version. Node was 24.19.0. Registration diagnostics were read-only. Native disassembly engines were unavailable; none was installed. MCP availability fluctuated during the session. A registered server in configuration was never treated as proof of a connected active tool.

Source-repository analysis used GitHub pinned trees/blobs and direct reads. REA was reserved for browser runtime behavior. Task-owned headless Edge/Chromium 155.0.4283.62 used a separate profile, loopback CDP endpoint, no personal cookies, no credentials and synthetic public-preview text. The REA browser result itself reports platform/architecture unknown; the orchestrating host was Windows, and that distinction is retained. No cross-platform browser or native support is inferred.

Initial launch-mode scenarios for Flow/Aqua/Superwhisper and ElevenLabs produced **cleanup_incomplete** at a 1000 ms cleanup-confirmation bound, with partial page evidence. Two CLI passive attempts produced no usable JSON. An in-app-browser entry aborted. These failures are retained, not rerun-to-green or counted as completed user workflows. The task then used a separately owned browser and REA's connect mode; results reported `disconnected-external`. This changes attachment/cleanup mode, not the provider code or claim scope.

## Actual runtime observations

The [bounded runtime evidence](rea-runtime-observations.json) preserves provider/evidence IDs, scenario identities, actions, step URLs, short relevant accessibility observations, artifact hashes, completeness and limitations. It omits URL query values, cookies, storage contents, request/response bodies, credentials, analytics identifiers and complete proprietary page dumps. Original-envelope hashes bind local captures; those hashes are not a claim that omitted full captures are distributed in this repository. Replay the declared scenario to obtain new evidence; mutable sites cannot reproduce an old page byte-for-byte.

| Target / actual action | Outcome | What remains NOT_RUN |
| --- | --- | --- |
| Decagon passive public homepage | DOM/accessibility observed in 500 ms window; attach-limited / policy-filtered | Customer conversation, tool use, transfer and tenant isolation |
| ElevenLabs first public fill + Play | Hydration replaced entered text; no verified audio | Successful generated preview |
| ElevenLabs second fill after 1.5 s hydration wait + Play + 2 s observation | Synthetic text persisted; Play disabled; hCaptcha resources and page errors observed; event capture incomplete | Audio generation/playback/quality/latency; causal attribution of failure |
| Cartesia homepage | Public page and entry points observed | Studio and voice-agent runtime |
| Cartesia Sign in, observe form, explicit return navigation | Email/Continue boundary and recovery to public page observed; nothing submitted | Authenticated inference and actual inference failure recovery |
| Flow public homepage | Download/onboarding entry points observed | Native microphone/dictation/insertion/privacy or OS installation |

No 2-second observation timeout is an inference latency result. An analytics event named as generated audio is not proof of audio. Marketing platform lists are DOCUMENTED, not installation tests. Public form navigation is a boundary workflow, not a successful voice workflow.

## Source and experiment acquisition

All mandatory D0/D1 donors, historical supplied sources and accessible founder repositories are in [SOURCE_CATALOG.md](SOURCE_CATALOG.md). Exact source revision, Git blob and SHA-256 records distinguish semantic inspection from entry-file triage. Account inventory used actual returned identities, pagination and owner-authenticated retries; no secrets or private legal documents are stored. The failed `jiwer/jiwer` identity is retained beside corrected `jitsi/jiwer`. Fanatir organization visibility was not established; the similarly named founder repository is separate.

Actual execution was deliberately bounded: 17 unique unchanged OpenWhispr pure unit tests; eight named synthetic non-audio Studio mechanism cases; six unchanged Ninerr pure policy fixtures. They do not jointly form 31 integrated product tests or an independent release gate. Reproduction helpers verify pinned source hashes before running and do not install packages or models. See the pillar reports and result JSONs for case-level detail. No donor full application suite, native audio capture or GPU inference ran.

Official technical pages were read through existing connected tools and no-auth public fetches. [Web manifest](official-web-source-manifest.json), [additional peer observations](official-peer-observations.json), Klaint web records and Studio model-card revisions supply provenance. Connector search/scrape credits were used without purchasing resources. No paid inference, subscriptions or compute were purchased. No vendor sign-in, personal microphone capture, phone call, private customer data or unconsented voice cloning occurred.

## Runnable gap plan and completion boundary

For each top R0 family, the target remains one successful workflow, one genuine failure/recovery workflow and one boundary/platform/permission workflow where access permits. The missing workflows are enumerated in [BENCHMARK_AND_REPLAY_PROTOCOL.md](BENCHMARK_AND_REPLAY_PROTOCOL.md); source donors have fake dependency recipes first, then legitimate native or account runtime qualification. Native apps lack installed/qualified artifacts in this study; proprietary production workflows require legitimate accessible accounts; phone tests require a qualified sandbox/number; dialect and cloning studies require consent-backed data and suitable hardware. These constraints do not block the source plan, and no product success is fabricated to fill them.

The plan is based on source-fit evidence and limited actual REA. It is not a completed competitive product benchmark. Research ends with one draft PR; implementation, constitutional amendment, frozen benchmark progression and release remain separately governed.
