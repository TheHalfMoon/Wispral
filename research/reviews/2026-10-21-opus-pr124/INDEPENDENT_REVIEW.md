# Independent architecture and copy-first plan review of PR #124

- Review date: 2026-10-21
- Reviewer: Claude Opus 5.5, independent of the Codex mission that authored PR #124 (no shared worker, no shared drafts)
- Exact head under review: `f36338138f4b4a872b05393b5cab03856dd7bf8e` (PR #124, 1 commit, 44 files, +57,314)
- Canonical base observed: `main` = `edacdf7504302cc91ff7138bc6ac2d391e4df1f4`
- Scope: research authenticity, source selection, architecture, plan executability, governance/CI. **This is a planning review. It is not a security, benchmark, release or merge approval**, and it does not replace any required exact-range review the repository's governance asks for.
- Recommendation: **REVISE** (details in section 7)

Every claim below is tagged with how it was established:

- `REPRODUCED`: I re-executed it on this review's machine (Windows 11 10.0.26300, Python 3.14.7, Node 24.19.0).
- `SOURCE_READ`: I read the pinned source bytes myself.
- `DOC_READ`: taken from repository documents only.
- `NOT_RUN`: not exercised.

No audio, model, native-app, customer-agent, telephony or GPU behavior was exercised by this review.

---

## 1. What I verified, and what holds up

| Check | Method | Result |
| --- | --- | --- |
| 72 transplant mechanisms → 96 GitHub source anchors | Fetched each file at its pinned commit through the GitHub API. Recomputed SHA-256 and git blob SHA-1 and checked the symbol at the recorded line ([verify_transplant_pins.py](verify_transplant_pins.py)) | `REPRODUCED` **96/96 hash OK, 96/96 blob OK**, all line anchors that carry a line number match ([results](pin-verification-results.txt)) |
| 3 crates.io pins (INK-I1, INK-I2, INK-I11) | Downloaded `.crate` and compared it with the crates.io index checksum. Compared the inner file SHA-256 and the `.cargo_vcs_info.json` revision | `REPRODUCED` 3/3 match the index, the recorded file hash and the recorded revision. All MIT |
| Bundle integrity | `node research/rea/2026-10-21/validate_research.mjs` | `REPRODUCED` 132 catalog rows, 72 transplant rows, `failures: []` |
| OpenWhispr pure tests | `reproduce_ink_pure_units.mjs` into a fresh scratch dir | `REPRODUCED` 17 pass / 0 fail |
| Studio synthetic mechanism probes | `studio_mechanism_probe.py --acquire` | `REPRODUCED` 8 probes, `models_loaded: 0`, `audio_processed: false` |
| Evidence labelling | Tallied status fields in `rea-runtime-observations.json`, `EVIDENCE_INDEX.json` and `official-peer-observations.json`. Scanned the strategy docs for evidence-bearing words | `REPRODUCED` Every competitor observation is `PUBLIC_PAGE_ONLY`, `INCOMPLETE_PREVIEW`, `NO_VERIFIED_AUDIO`, `ABORTED` or `DOCUMENTED_NOT_RUN`. **No overclaim found.** No unrun audio, native or customer-agent test is presented as completed |
| OpenWhispr falls back to the current foreground window | `resources/windows-fast-paste.c` @ `e4280ad` lines 281–291 | `SOURCE_READ` Confirmed: "If it is gone or can't be restored we fall through to whatever is foreground now". The plan's rejection is correct |
| Chatwoot handoff is not race-safe | `app/models/conversation.rb` @ `8006117` line 185 | `SOURCE_READ` Confirmed: the code comment says "Best-effort eligibility check, not a lock against concurrent takeovers" |
| Parlant has an alternate tool path past the Plan hook | `tool_caller.py::_run_tool` calls `service_registry.read_tool_service(...).call_tool` directly. `NullPlan.on_tools_inferred` passes all inferred calls through | `SOURCE_READ` Confirmed. The plan's "restrictive Plan **and** brokered ToolService" is the right control |
| HubSpot webhook timestamp gaps (K09) | `integrations/hubspot/src/hitl/utils/signature.ts` @ `4dbedde` | `SOURCE_READ` Confirmed and sharper than stated: (a) future timestamps pass, because `Date.now() - ts` is negative; (b) a non-numeric timestamp passes the skew check, because `NaN > 300000` is `false`; (c) there is no replay deduplication. K09's acceptance list already covers all three |

**Conclusion on authenticity:** the source inventory is real, precisely pinned and honestly labelled. Codex's work is a sound evidence base. The problems are in **plan structure, sequencing and copy granularity**, not in fabricated evidence.

---

## 2. MUST FIX: blocks an executable or trustworthy plan

### M1. The CI conflict is broader than documented: canonical `main` itself fails the B2R16 verifier

- **Files:** `.github/workflows/000b2-public-b2r16-freeze.yml` (triggers on every `pull_request`, with no paths or task filter); `research/000b2-public/verify_b2r16.py:123-130` (`verify_exact_task_range` diffs the fixed `TASK_AUTHORITY_BASE=4834840…` against `HEAD` and requires exactly the four B2R16 paths); `research/rea/2026-10-21/LIVE_FRONTIER_AND_HANDOFF.md` and `WISPRAL_MASTER_PLAN_REBUILT.md` W0 describe it only as a "later-PR" problem.
- **Evidence:**
  - `REPRODUCED` `verify_b2r16.py --require-git` gives `FAIL: B2R16 actual candidate range scope drift` on the PR head `f363381` **and on canonical `main` `edacdf7`**.
  - It gives `B2R16_ATTEMPT_003_FREEZE=PASS` on the qualified head `ac9f7ce993aec33e6c6436cce4efd85394a97f35`.
  - The four frozen B2R16 paths are byte-identical between merge `885307429ec8…` and the PR head (`git diff --stat` is empty).
  - `verify-b2r16-freeze` also fails on #118 (run `34416457849`), the canonical reconciliation that *was merged*, and on #120 and #123.
  - CI logs for #124 run `39588472485` have expired (HTTP 404 blob), so this local reproduction is the primary evidence.
  - Branch protection and rulesets return 403, so whether the check is *required* is unknown.
- **Why it blocks:**
  - If the check is required, no later PR (including the governance amendment W0 depends on) can ever satisfy Principle XVI.5 or "all exact-head gates".
  - If it is not required, the canonical record must say so, because #118 merged with it red.
  - The defect is **fail-closed over-application, not fail-open**, so Principle XVI's repair lane does not apply as written. Using it would be the "convenient substitute" that XVI forbids.
- **Affected packets:** G-00, G-01, W0, and every later packet.
- **Remedy:**
  1. The founder (repository owner) reads *Settings → Branches / Rules* in the GitHub UI and records whether `verify-b2r16-freeze` is a required check. The API cannot read this on the current plan, but the owner can.
  2. A dedicated, single-purpose governance-control PR that strengthens the check:
     - for `pull_request` events, check out and run the verifier at the canonical qualified head `ac9f7ce…`, so it keeps proving the historical freeze;
     - add a step asserting that the four `EXPECTED_SCOPE` paths at the PR head are byte-identical to their bytes at `885307429ec8…`, so it now also detects tampering, which today's always-failing check cannot.
  3. A canonical reconciliation records the #118 red-check merge factually.
- **Acceptance test:**
  - The workflow passes on #124's head.
  - A throwaway branch that mutates one byte of `research/000b2-public/b2r16-preexecution-state.json` fails.
  - Output at `ac9f7ce` is identical to the pre-change PASS output.
  - The pre-change failure on the fix PR itself is preserved as evidence, not rerun-to-green.

### M2. The critical path skips founding children 000C–000F and the open B2 chain

- **Files:** `specs/CURRENT.md:240-268` (000C–000F precede 000G, and the product-code gate requires 000G); `WISPRAL_MASTER_PLAN_REBUILT.md` W0 ("1–3 engineer-days") and `WISPRAL_COPY_FIRST_WORK_PACKETS.md` G-00/G-01 (neither mentions 000C–000F, and B2R17/#120 appears only as "preserve").
- **Evidence:** `DOC_READ` `grep 000C|000D|000E|000F` across the three strategy docs returns 0 hits. B2R17 is the sole active unit (#120: 209/240 decoded, 31 failures, unscored).
- **Why it blocks:** As written, no Q-packet can reach READY without either completing 000B2 → 000C → 000F → 000G or amending that chain. V3 never states which, so its "1–3 days" W0 is not an executable estimate.
- **Affected packets:** G-01, Q-01…Q-09, all W1+.
- **Remedy:** The amendment must contain an explicit founding-chain re-scope:
  - **000F** ← the REA bundle is exactly dependency, licensing and provenance input, so record it as 000F evidence instead of a parallel track.
  - **000C/000D** are coding-agent-specific (turn-taking, PTY), so make them blocking only for the optional developer-agent capability (A-01).
  - **000E** = the WisprSide native qualification (Q-05/Q-06/Q-08).
  - **B2** stays frozen, and an explicit rule says that grains with no STT dependency (Q-01 policy lattice, Q-02 fit, Q-03 fake worker) do not wait for B2R17 closure, while I-01 (speech adapter) does.
- **Acceptance test:** The amended `specs/CURRENT.md` contains a dependency graph in which every Q/I/S/K packet traces to one named READY authority. A reviewer can mechanically confirm that no packet reaches READY through an unstated dependency.

### M3. The governance amendment proposal leaves direct contradictions in canonical text

- **Files:**
  - `AGENTS.md:3` ("It is **not a dictation application**")
  - `docs/canonical/PROGRAM_ROADMAP.md:341-356` anti-roadmap: "an Electron IDE", "mobile clients before the terminal control plane is proven", "enterprise dashboards before core user value is established"
  - `ARCHITECTURE_INVARIANTS.md:116-118` A12 (no Electron app needed to prove the thesis), while the Studio lead VoiceStudio is Electron
  - `WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md` (its subordinate-documents table)
- **Evidence:** `DOC_READ` The proposal mentions "AGENTS.md mission paragraph" generically. `grep anti-roadmap` returns 0 hits in the proposal and in V3.
- **Why it blocks:** WisprSide is a dictation application and Klaint ships an inbox/enterprise surface. An amendment that leaves these lines intact would fail independent review or create a hidden exception, which the Governance section's clause 2 forbids.
- **Remedy:** Add explicit rows for:
  - the AGENTS.md negation sentence;
  - each anti-roadmap item, marked keep, remove or re-scope. Recommended: keep "foundation model", "custom coding agent" and "hosted vector-memory"; re-scope "Electron IDE" to "Electron IDE (a Studio desktop app is not an IDE)"; re-scope "enterprise dashboards" to apply to Core only, not Klaint operations;
  - A12 as per-product surface rules.
- **Acceptance test:** A post-amendment checklist greps each canonical file for every prohibition and shows, per pillar, "no contradiction" or the ratified exception text.

### M4. Q-02 "copy `plan_fit` unchanged" fails its own acceptance fixtures

- **Files:** `WISPRAL_COPY_FIRST_WORK_PACKETS.md` Q-02; donor `debpalash/VoiceStudio@28bf2c7…/backend/services/fit_planner.py` (sha256 `0acd7c33…21442`, matches the manifest).
- **Evidence:** `REPRODUCED` with [probe_fit_planner_inputs.py](probe_fit_planner_inputs.py) ([results](fit-planner-input-probe-results.txt)). The unchanged donor function **accepts** all of the following:
  - NaN natural duration → plausible output, so a silent garbage-in result;
  - `inf` natural duration → **non-finite output** (`total=20.0` with a non-finite segment field);
  - negative duration;
  - `end < start`;
  - overlapping segments;
  - NaN total duration.

  Only the parallel-length mismatch raises. Q-02's acceptance requires rejecting zero, negative, non-finite and overlapping input.
- **Affected packet:** Q-02, and later S-04 (dubbing fit).
- **Remedy (still copy-first):** COPY `fit_planner.py` byte-for-byte with notices, plus a new ~40-line `validate_fit_inputs()` guard in a separate file. The guard rejects non-finite, negative, inverted, unsorted or overlapping segments and non-finite totals with typed errors, and is called before `plan_fit`. Do not edit the donor function, so upstream diffs stay clean.
- **Acceptance test:** The six probe cases raise typed errors through the guard. The donor's own `tests/test_fit_planner.py` and fixture JSON outputs stay bit-identical through the guard for all valid inputs.

### M5. One responsibility, several owners: duplicated supervisors, cancellation and model inventories

- **Files:** `source-transplants.json` rows:
  - Process ownership: CORE-PROCESS → `crates/wispral-core/src/workers/contained_process.rs`; INK-I10 → `crates/wispral-core/src/model/worker_supervisor.rs`; ST-SIDECAR → `services/model-workers/subprocess_backend.py`; ST-MODEL-LIFECYCLE → `adapters/studio/model_lifecycle`.
  - Cancellation: CORE-CANCEL, ST-CANCEL-SCOPE (COPY), VB-QUEUE.
  - Model inventory: Q-09 shared inventory vs ST-MODEL-TERMS.
  - Realtime: CORE-REALTIME (Pipecat) and CORE-WEBRTC (LiveKit), both OUT_OF_PROCESS.
- **Evidence:** `SOURCE_READ` and `DOC_READ` Four process owners are mapped into new Wispral paths. Meanwhile `WISPRAL_PLATFORM_ARCHITECTURE_REPLAN.md` says "Share **one** artifact inventory and resource lease coordinator" and "one turn controller per session".
- **Why it blocks:** Principle III requires interruption to be core semantics. Four supervisors with different stop/ack semantics produce exactly the "ack-without-stop" and "leaked lease" failures that Q-03 is meant to rule out. The plan contradicts itself.
- **Remedy:** Add a one-owner-per-responsibility table to the architecture:
  - *Process owner:* one per product runtime. WisprSide uses the donor's supervisor (Handy `engine_supervisor` if S1 is adopted, otherwise Sentrdel `ContainedChild`). WisprStudio uses VoiceStudio's `contained_subprocess` + `subprocess_backend`, and is seen by Core as a single worker. Klaint uses its service host.
  - *Cancellation:* one Core contract (CORE-CANCEL states). Each runtime maps to it.
  - *Inventory:* one schema (Q-09). VoiceStudio `model_acceptance` becomes the Studio implementation of that schema, not a second store.
  - *Realtime:* Pipecat only (see S3).
- **Acceptance test:** A cross-runtime conformance fixture issues cancel at load / mid-inference / after-commit against each runtime's single owner. It observes identical Core state transitions, zero orphan processes and lease release only after observed stop.

---

## 3. SHOULD IMPROVE

### S1. Copy at the coarsest compatible boundary: fork-lead WisprSide (Handy) and WisprStudio (VoiceStudio)

- **Evidence:**
  - `REPRODUCED` Only **2 of 72** mechanisms are COPY; 31 are ADAPT, 19 OUT_OF_PROCESS, 10 WRAP. This is adapt-first in practice.
  - Each extracted function loses its surrounding tests and integration, and needs new glue, UI, settings, tray, model download and installer.
  - `SOURCE_READ` Handy @ `93c9ee0` (MIT, Rust/Tauri, 34k stars, active) has 397 files and already contains `transcription_coordinator.rs`, `paste_tx/{mod,windows,macos}.rs`, `engine_supervisor/*`, `secure_input.rs`, `portable.rs`, `cli.rs` and model/history managers.
  - `SOURCE_READ` VoiceStudio @ `28bf2c7` (AGPL-3.0 plus the founder's grant, 80k stars, active) has 3,601 files and **696 test files**. It already isolates engines in per-engine subprocess environments (`backend/engines/*/`, e.g. `cosyvoice_subprocess/requirements.txt`, `_venv_probe.py`, `core/contained_subprocess.py`), ships an `_echo` fake engine, and has consent, watermark, long-form resume and dub flows. The plan's ST-SIDECAR/ST-MODEL-LIFECYCLE and "separate locked environment per engine family" **rebuild capabilities the donor already has**.
- **Remedy:** Replace the per-mechanism extraction packets for these two products with:
  - **F-SIDE-0:** fork Handy at the pin, build, run the donor suite, record the baseline.
  - **F-STUDIO-0:** the same for VoiceStudio, plus `backend/core/analytics.py` defaulted off (Principle XIV) and the URL-download branch disabled.

  Q-05…Q-08 and S-01…S-04 then become **delta patches on the fork**, each tied to a finding: remove the focus fallback, add the target-identity envelope, unify consent/inventory. Keep an upstream-tracking branch and a `DELTA_REGISTER.md`. Core shares contracts and conformance fixtures, not code paths (see S2).
- **Acceptance test:** At fork baseline the donor test suite runs with recorded pass/fail counts before any edit. Every later delta lists its finding, its fixture and its upstream-rebase status. A first installable WisprSide build exists before any new Core crate is required.
- **Expected impact (engineering judgment, not measured):** removes most of I-02/S-03 UI and integration work and the duplicate supervisors, so W2/W3 are bounded by delta qualification rather than reassembly.

### S2. Core should be contracts + a small library + conformance fixtures, not one runtime across desktop and multi-tenant server

- **Files:** `WISPRAL_PLATFORM_ARCHITECTURE_REPLAN.md` (one Rust authority core mediates Klaint ToolService calls); ADR-0001.
- **Evidence:** `DOC_READ` A local single-user desktop core and a multi-tenant server have different identity, scaling, deployment and failure models. Putting a Rust process hop inside every Klaint tool call adds a network/IPC trust boundary without adding authority.
- **Remedy:**
  - Wispral Core = versioned JSON schemas (envelope, cancellation states, inventory, policy verdicts), plus the Rust policy crate (Sentrdel narrowing lattice, `bounded_json`), plus a shared conformance fixture corpus.
  - Klaint consumes the lattice through a PyO3 binding, or a Python port gated by the same fixtures, inside a single Python service.
- **Acceptance test:** The same fixture file yields identical ALLOW/ASK/DENY/UNDECIDABLE verdicts from the Rust crate and the Klaint binding in CI.

### S3. Consolidate Klaint runtimes: one Python service, Pipecat only, Chatwoot by API

- **Evidence:**
  - `SOURCE_READ` Pipecat @ `9b0459b` already ships `transports/livekit`, `transports/daily`, `transports/smallwebrtc` and `serializers/{twilio,telnyx,plivo,vonage,exotel}`, so one framework covers both room and telephony topologies, and CORE-WEBRTC (LiveKit Agents) is redundant.
  - The Botpress connectors (K08/K09) are thin Axios wrappers that add a Node runtime.
  - K05–K07 "ADAPT" Chatwoot's Rails internals although the boundary needed is its Agent Bot API and webhooks.
- **Remedy:**
  - CORE-WEBRTC → REFERENCE_ONLY.
  - Re-implement K08/K09 inside the Python brokered ToolService using vendor Python SDKs. Keep the Botpress schemas and HITL interface as reference, and apply the HubSpot timestamp/NaN/replay fixes from section 1.
  - Run Chatwoot unmodified, with the ownership epoch held on the Klaint side.
- **Acceptance test:** The Klaint deployment manifest lists one language runtime (Python) plus optional unmodified Chatwoot. The K09 fixtures (future, NaN and replayed timestamps) reject.

### S4. Klaint omits Parlant's own safety and quality features

- **Evidence:** `SOURCE_READ` Parlant @ `ea73744` has `core/canned_responses.py`, `engines/alpha/canned_response_generator.py`, `docs/concepts/customization/retrievers.md` and `api/evaluations.py`. `REPRODUCED` "canned" has **0 mentions** in the Klaint deep dive and all strategy docs.
- **Why it matters:** Strict canned-response output is the main control against hallucinated commitments ("your refund is approved") in customer agents. Decagon, Sierra and Fin all compete on grounded answers, simulations and QA.
- **Remedy:** Add K-00: canned-response strict mode as the default for any message that confirms an action, price or policy. Add retrievers with tenant-scoped indexes and cited sources. Use Parlant evaluations as the scenario harness under the deterministic outcome scorer K-01 already plans.
- **Acceptance test:** A synthetic session where the model is prompted to promise an unauthorized refund emits only an approved template or a handoff, never free text, across N preregistered adversarial prompts.

### S5. Defer CORE-NETWORK (Q-04, Ninerr TypeScript → Rust port) from the first release

- **Evidence:** `DOC_READ` Q-04 translates a TypeScript policy into Rust, which is rebuilding, not copying. WisprSide's first release needs "no egress in offline mode", which is better proven by an observed-egress test of the shipped binary plus the absence of network code paths.
- **Remedy:** Move Q-04 behind Klaint connectors, where SSRF protection is actually needed, as Python with Ninerr's fixtures. Replace it in W2 with an egress-observation test.
- **Acceptance test:** In the W2 offline test, a packet capture or OS firewall log shows zero outbound connections during a full PTT session.

### S6. Model-routing boundary is under-specified for LLM rewrite, Klaint dialogue and TTS

- **Evidence:** `DOC_READ` The plan specifies a speech router but no LLM provider boundary (WisprSide rewrite, Klaint NLPService) and no TTS selection rule.
- **Remedy:**
  - One provider interface per modality (STT, TTS, LLM), each with an explicit per-workspace or per-tenant configuration. Local options: whisper.cpp/sherpa/moonshine for STT, llama.cpp-compatible server for LLM, the chosen Studio engine for TTS.
  - No automatic cloud fallback.
  - Model id, digest and provider recorded in every provenance event.
  - Studio engine choice is explicit per project, never auto-switched.
  - No model training (out of scope).
- **Acceptance test:** With the cloud provider disabled, a rewrite or dialogue request returns a visible "provider unavailable" result. The provenance record names the exact model id and digest.

### S7. Competitive gaps to add as coarse P1/P2 rows (not near-term scope)

- **WisprSide** (vs Wispr Flow, Aqua, Superwhisper): learned personal dictionary and corrections; per-app style/tone; voice command-mode edit of selected text; snippets; backtrack/filler cleanup as a reversible edit layer over the immutable raw hypothesis; streaming preview; auto language detect for Arabic/English code-switching.
- **WisprStudio** (vs ElevenLabs, VoiceStudio): voice design from a text prompt (`Qwen3TTSModel.generate_voice_design` exists at the pin); speech-to-speech/voice conversion (OpenVoice already mapped); voice isolation (Demucs mapped, but **upstream archived**: `archived=true`, last push 2024-04-24); pronunciation dictionary; local API.
- **Klaint** (vs Decagon, Sierra, Fin): S4 items plus conversation QA/analytics and multilingual handoff summaries.

**Acceptance test:** `FEATURE_PARITY_AND_GAP_MATRIX.md` carries each item with a donor reference or "no donor", plus a priority. No item becomes READY without evidence.

### S8. "FINAL_INDEPENDENT_REVIEW.md" is not independent under repository governance

- **Evidence:** `DOC_READ` Its own header says it was written by "a separate REA source/evidence worker" of the same mission, which "previously authored the additional-source review and benchmark/replay protocol", while "the parent was editing the bundle during this review".
- **Remedy:** Retitle it "Internal consistency review" (preserving the history and bytes in git) and record `INDEPENDENT_REVIEW=NOT_SATISFIED_BY_THIS_FILE`.
- **Acceptance test:** No document in the bundle claims independent review for a same-mission reviewer.

---

## 4. OPTIONAL

- **O1. Schema uniformity in `source-transplants.json`:** 43/72 rows lack `decision` (WisprStudio rows have both `decision` and `mode`), and 12 rows have null `runtime_status`. Make `validate_research.mjs` require a uniform schema. *Test:* validator fails on a row missing either field.
- **O2. Grant-scope note per copied file for copyleft donors:** VoiceStudio is AGPL-3.0, VoiceInk GPLv3, Piper and Yamakan GPL-3.0. Founder rights are confirmed and are not questioned here. Record privately, per copied file, that it falls within the confirmed grant, and keep the original notices for bundled third-party sub-components and model weights, which stay separate. *Test:* each copied file has a NOTICE entry and a grant-scope flag.
- **O3. Stale or archived donors:** Demucs is archived, Kokoro's last push was 2025-08 and Qwen3-TTS's was 2026-03. Add a maintenance-risk column to the rubric.
- **O4. Effort estimates:** add review/CI latency explicitly, since governance latency dominates (see M2).

---

## 5. Revised lead-donor decision matrix

| Product | Lead (exact pin) | How to reuse | Keep as narrow source | Reference only / reject | Why it changed from V3 |
| --- | --- | --- | --- | --- | --- |
| **WisprSide** | cjpais/Handy `93c9ee05` (MIT) | **Fork** + delta register; donor suite baseline first | OpenWhispr `windows-fast-paste.c` target identity (strip the fallback); VoiceInk outcome vocabulary (`commandPosted/NotPosted/PartiallyPosted`); handy-recorder/handy-keys crates as the fork already uses them | OpenWhispr app (Electron), FreeFlow (screenshot/cloud route), Voicebox | S1: the fork keeps tests, UI, installer and supervisor. Removes INK-I10 duplication (M5) |
| **WisprStudio** | debpalash/VoiceStudio `28bf2c7a` (AGPL-3.0 + founder grant) | **Fork** + delta register; analytics default off; URL ingest off | `fit_planner` + validating guard (M4); engines already isolated per subprocess | Voicebox (reference, zero-volume regression fixture only); F5/OmniVoice weights stay separate rights | S1/M5: the donor already has per-engine environments, a fake engine, consent, watermark and resume |
| **Klaint** | emcie-co/parlant `ea737442` (Apache-2.0) | **Wrap** as one Python service with restrictive Plan + brokered ToolService + **canned responses + retrievers + evaluations** | Chatwoot unmodified via API (optional); Pipecat `9b0459b4` for voice later; Botpress schemas as reference | LiveKit Agents, Rasa, Botpress runtime/Node | S3/S4: one runtime, Parlant's own safety features |
| **Wispral Core** | Sentrdel `f5747319` narrowing + `bounded_json` + `ContainedChild`; ACP rust-sdk `652d1003` | **Contracts + small Rust crate + conformance fixtures**; PyO3 binding for Klaint | Orcel audit record shape; Ascout descriptor → JSON schema | Ninerr port deferred (S5); whole security frameworks rejected (as in V3) | S2: a library and contracts, not a cross-product runtime |

---

## 6. Minimal plan changes (deltas to V3, nothing else rewritten)

1. **W0 / G-00:** the founder reads the required-check setting; open the M1 single-purpose workflow-strengthening PR; reconcile the #118 red-check merge factually.
2. **W0 / G-01 amendment:** add the M2 founding-chain re-scope and the M3 contradiction rows (AGENTS negation, anti-roadmap, A12).
3. **Q-02:** "COPY unchanged + `validate_fit_inputs` guard" (M4).
4. **Architecture:** add the one-owner-per-responsibility table (M5) and redefine Core as contracts + library + fixtures (S2).
5. **Packets:** insert F-SIDE-0 and F-STUDIO-0 fork-baseline packets. Re-express Q-05…Q-08 and S-01…S-04 as fork deltas (S1).
6. **Klaint:** add K-00 (canned responses / retrievers / evaluations); single Python runtime; CORE-WEBRTC → REFERENCE_ONLY; Chatwoot API-only (S3, S4).
7. **Defer Q-04**; add the W2 egress-observation test (S5).
8. **Add the modality routing rules** (S6) and the coarse competitive rows (S7).
9. **Retitle** `FINAL_INDEPENDENT_REVIEW.md` (S8).

Proposed first executable grain after authority opens (unchanged in spirit from V3): **Q-02 with the guard** or **Q-01**. Both are pure, have no STT, model or microphone dependency, and can be proven in under a day. Then **F-SIDE-0**.

---

## 7. Recommendation: **REVISE**

- **Not BLOCKED:** the research is authentic (99/99 pins, reproduced probes, honest labels), and the PR is planning-only with no product code.
- **Not APPROVE FOR PLANNING:** M1–M5 make the plan non-executable as written:
  - an unresolved gate that fails on canonical `main`;
  - an unstated founding-chain dependency;
  - contradictions left in canonical text;
  - a first packet that fails its own acceptance;
  - duplicated owners for cancellation-critical responsibilities.

  Each has a small, concrete remedy above.

**Merge note:** PR #124 (and this review PR) inherit the M1 failure. Neither may be described as gate-green. Do not merge either until M1 is resolved in its own lane.

## Reproduction

From the repository root, using existing interpreters (they install nothing):

```text
python -I research/reviews/2026-10-21-opus-pr124/verify_transplant_pins.py research/rea/2026-10-21/source-transplants.json
python -I research/reviews/2026-10-21-opus-pr124/probe_fit_planner_inputs.py <path to pinned fit_planner.py>
python -I research/000b2-public/verify_b2r16.py --require-git   # at f363381, edacdf7, ac9f7ce
```

The pin verifier needs an authenticated `gh` CLI.
