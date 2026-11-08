# Wispral World-Class Master Plan

**Status:** CANDIDATE MASTER PLAN — the one authoritative *candidate* plan for Wispral, WisprStudio, WisprSide and Klaint. It is **not ratified governance** and authorizes no implementation, release or publication. It becomes binding only through the governance sequence in [WISPRAL_GOVERNANCE_RECONCILIATION.md](WISPRAL_GOVERNANCE_RECONCILIATION.md).
**Date:** 2026-11-08 · **Canonical base:** `main` = `edacdf7504302cc91ff7138bc6ac2d391e4df1f4` · **Supersedes for planning:** PR #124's [Master Plan V3](WISPRAL_MASTER_PLAN_REBUILT.md) and [architecture replan](WISPRAL_PLATFORM_ARCHITECTURE_REPLAN.md) (kept unchanged as history and evidence).

> **Copy first. Design exceptionally. Build deliberately. Verify everything. Do not publish.**

---

## 1. The plan in one page

1. **Unblock legitimately first (P0).** Today every PR fails a historical B2 check, and two B2 trusted gates permanently lock the frontier files. Fixing only the freeze check is not enough. The smallest legitimate path is a narrow constitutional lane for correcting over-applied benchmark controls (G1, Principle XVII, which explicitly excludes security, consent, tenancy, egress and release controls), two control corrections (C1 freeze preservation from a base-defined job; C2 an exact section allowlist for non-B2 edits), a ledger record (R), then the platform amendment (G2) and the frontier update (F). The B2 benchmark stays frozen and resumable in its own lane.
2. **Fork, don't rebuild.** WisprSide forks **Handy** (`73cc8579`), and WisprStudio forks **VoiceStudio** (`200286cc`; packet ST-D00b first compares it with Voicebox). Klaint's MVP is **one hardened Parlant process** (v4.0.2 if spike KT-01 passes, else v3.3.2) with the broker as the sole tool executor. Wispral Core is **eight language-neutral contracts with fixtures**; Rust crates wait for a second Rust consumer. There is no daemon.
3. **Build only the trust boundaries the donors lack.** Fail-closed, target-bound text delivery on Windows. Consent enforcement on every Studio synthesis path. A deterministic Klaint broker that is the sole executor of consequential tools, with an outcome ledger and commitments only from receipts. Each item is justified in the [build-new register](WISPRAL_COPY_FIRST_STRATEGY.md#4-build-new-register).
4. **Strip what the donors do silently.** Handy checks for updates by default. VoiceStudio checks for updates, races a third-party model mirror, offers cloud sync, ships an analytics key and defaults to a **non-commercial** TTS model. Parlant v4 defaults to allow-all and runs an unauthenticated local tool server.
5. **Design is a first-class requirement.** "Quiet Signal" tokens are verified for contrast (76/76 pairs). The three UX specs center the moments that carry risk: live capture, where text went, voice consent and agent authority.
6. **Arabic is measured, not claimed.** 2026 brought new permissively licensed Arabic ASR models, but most dialect datasets are non-commercial. A consented Wispral panel is the only path to a Gulf/code-switch claim.
7. **Order:** P0 → P1 baselines (Parlant spike moved here) → 000G decision → P2 foundations the MVPs consume → P3 WisprSide MVP → P4 WisprSide RC; P5 Studio and P6 Klaint are alternatives alongside WisprSide (Klaint text recommended first). Phases are labels: packets start when their own dependencies are met. Nothing is published without the founder's green light.

## 2. Deliverable map (sections A–N)

| Section | Content | Document |
| --- | --- | --- |
| A | Executive product strategy: vision, users, positioning, boundaries | [WISPRAL_PRODUCT_VISION.md §1](WISPRAL_PRODUCT_VISION.md#1-vision) |
| B | Complete capability specification (MVP / stable / later / research) | [WISPRAL_PRODUCT_VISION.md §2](WISPRAL_PRODUCT_VISION.md#2-capability-catalog) |
| C | Verified source strategy and donor matrix (re-pinned 2026-11-08) | [WISPRAL_COPY_FIRST_STRATEGY.md](WISPRAL_COPY_FIRST_STRATEGY.md), [SOURCE_DECISION_MATRIX.md](../../research/wispral-world-class/SOURCE_DECISION_MATRIX.md) |
| D | Architecture: boundaries, owners, data flows, topology, failure behaviour | [WISPRAL_PRODUCT_ARCHITECTURE.md](WISPRAL_PRODUCT_ARCHITECTURE.md), [executable contracts](../engineering/contracts/README.md), [trade-offs](../../research/wispral-world-class/ARCHITECTURE_TRADEOFFS.md) |
| E | Design system and UX specifications | [Design system](../design/WISPRAL_DESIGN_SYSTEM.md), [WisprSide](../design/WISPRSIDE_UX_SPEC.md), [WisprStudio](../design/WISPRSTUDIO_UX_SPEC.md), [Klaint](../design/KLAINT_UX_SPEC.md) |
| F | Model integration architecture and routing | [WISPRAL_MODEL_STRATEGY.md](../engineering/WISPRAL_MODEL_STRATEGY.md) |
| G | Security and privacy, threat models per product | [WISPRAL_SECURITY_ARCHITECTURE.md](../engineering/WISPRAL_SECURITY_ARCHITECTURE.md) |
| H | Benchmark framework (WispralBench v2 candidate) | [WISPRAL_BENCHMARKS.md](../engineering/WISPRAL_BENCHMARKS.md) |
| I | Engineering work packets (73, machine-checked for graph, authority reachability, tiers and build-new register) | [WISPRAL_IMPLEMENTATION_PACKETS.md](../engineering/WISPRAL_IMPLEMENTATION_PACKETS.md), [packets.json](../../research/wispral-world-class/packets.json) |
| J | Milestone plan | [WISPRAL_ENGINEERING_ROADMAP.md](WISPRAL_ENGINEERING_ROADMAP.md) |
| K | Release quality gates | [WISPRAL_RELEASE_QUALITY.md](WISPRAL_RELEASE_QUALITY.md) |
| L | Risk and dependency register | [RISK_REGISTER.md](../../research/wispral-world-class/RISK_REGISTER.md) |
| M | Decision ledger | [DECISION_LEDGER.md](../../research/wispral-world-class/DECISION_LEDGER.md) |
| N | Unresolved questions (founder versus engineering) | [FINAL_HANDOFF.md](../../research/wispral-world-class/FINAL_HANDOFF.md) |
| — | Governance and CI reconciliation (Phase 0) | [WISPRAL_GOVERNANCE_RECONCILIATION.md](WISPRAL_GOVERNANCE_RECONCILIATION.md) |
| — | Platform, packaging and distribution | [WISPRAL_PLATFORM_COMPATIBILITY.md](../engineering/WISPRAL_PLATFORM_COMPATIBILITY.md) |
| — | Competitors and measurable differentiators | [COMPETITOR_GAP_MATRIX.md](../../research/wispral-world-class/COMPETITOR_GAP_MATRIX.md) |
| — | Live state, evidence, review and validation | [CURRENT_STATE_INVENTORY.md](../../research/wispral-world-class/CURRENT_STATE_INVENTORY.md), [REA_EVIDENCE_INDEX.md](../../research/wispral-world-class/REA_EVIDENCE_INDEX.md), [INDEPENDENT_REVIEW.md](../../research/wispral-world-class/INDEPENDENT_REVIEW.md), [PLAN_VALIDATION.md](../../research/wispral-world-class/PLAN_VALIDATION.md) |

## 3. Final architectural recommendation

- **Three independently installable products and a thin shared layer.** No central runtime; each product owns its processes, cancellation, inventory, identity and side effects ([owner table](WISPRAL_PRODUCT_ARCHITECTURE.md#2-one-owner-per-responsibility)).
- **Eight versioned contracts** (envelope with typed payloads, cancellation, model manifest, consent, policy verdict, provenance, delivery outcome, effect intent) with shape, runtime, sequence and cross-record bundle fixtures that already pass (94 cases, 10 sequences, 4 bundles). Digests are canonicalized (RFC 8785, NFC, path rules) so any future Rust, Python or TypeScript implementation produces identical results.
- **Deterministic authority everywhere it matters.** Policy verdicts from the adapted Sentrdel lattice; effect intents and reconciliation adopted from orcel-journal; probabilistic outputs are evidence only (`authority_ceiling: evidence_only`).
- **Local-first by default.** No hidden network, no hidden cloud fallback, no automatic paid inference, no telemetry. Each product proves this on its shipped binary with a packet-capture test.

## 4. Primary donors

| Product | Lead donor (exact pin) | Mode | Key narrow donors |
| --- | --- | --- | --- |
| WisprSide | `cjpais/Handy@73cc8579cff74e97e08de9d86035a92e4335ff7f` (MIT) | Fork | FreeFlow `AppTextInsertionCore` (fail-closed algorithm, MIT); OpenWhispr UIA probe and terminal lists (MIT); SafeEvidence egress gates; Orcel process identity |
| WisprStudio | `debpalash/VoiceStudio@200286ccff6f28faaf51bb08b2a5b54c460b39f4` (AGPL-3.0 + founder grant) | Fork | Chatterbox Multilingual (MIT) as an engine adapter; Resemble PerTh watermark |
| Klaint | `emcie-co/parlant@2a463ccd10eaf0d70d42731705f4f00ef066bee8` v4.0.2 (fallback v3.3.2 `61bba3b2`) (Apache-2.0) | Wrap, process per tenant | Chatwoot v4.19.1 via API; standard-webhooks; tau2-bench; Pipecat v1.15.0 later |
| Core | Sentrdel `f5747319`, Orcel `f0b78e65`, Ascout `48902389`, SafeEvidence `f05bc006`, Ninerr `616bafaa`, ACP rust-sdk `050cd94c` | Adapt / copy | — |

## 5. Most important corrections to previous plans

| # | Correction | Earlier position | Evidence |
| --- | --- | --- | --- |
| 1 | **The freeze check is not the only CI blocker.** Two B2 trusted gates permanently lock `specs/CURRENT.md` and `CURRENT_STATE.md` for every non-B2 PR, even after B2 completes | PR #124/#125/#126 treated M1 (freeze) as the blocker | Governance report §1 (`REPRODUCED` gate harness) |
| 2 | **#126 cannot merge under current authority**; a new constitutional lane (Principle XVII) is needed first | #126 described itself as an "ordinary" correction | Governance report §3(c) |
| 3 | **Parlant 4 removed strict canned responses, journeys, evaluations and the Plan hook** | PR #124/#125 planned around `CANNED_STRICT`, journeys, `api/evaluations.py` and the restrictive Plan | Klaint report §1 |
| 4 | **VoiceStudio's default TTS (OmniVoice) has non-commercial weights**, and **no synthesis path checks consent** | Fork assumed to carry usable consent and defaults | Studio report §2–§3 |
| 5 | **Fit guard must allow overlapping segments** | Opus M4 rejected overlap | Studio report P1 (`REPRODUCED`) |
| 6 | **Re-pins:** Handy, VoiceStudio, Parlant, Pipecat, Chatwoot, Orcel, ACP rust-sdk (two majors) | 2026-10-21 pins | Source decision matrix |
| 7 | **Contracts were too permissive** (23/25 invalid donor-informed records accepted); revised, plus `effect_intent` | First draft in this mission | Core report §3 |
| 8 | **Klaint MVP = one hardened Parlant process**; plugin tool server off; broker is the sole executor with a per-call session token; multi-tenancy (a process per tenant behind a gateway) is tier S | Tenant binding inside one shared service | Klaint report §2.8; architecture and security reviews |
| 9 | **Wispral has no LICENSE**; founder decision before any copy | Not noted | Core report §1 |
| 10 | **Parlant spike moved to P1; P5 and P6 may run in parallel** | Strictly sequential phases | Roadmap §2 |
| 11 | **Independent review changed the plan materially:** 7 blockers and 37 must-fix findings across architecture, copy-first, testability, security and UX, all addressed ([INDEPENDENT_REVIEW.md](../../research/wispral-world-class/INDEPENDENT_REVIEW.md)) | Plan as first drafted | Review record |

## 6. What can be copied immediately once authorized

These still need F, the relevant research or product Grain, and a recorded Wispral license. "Immediately" means no new design work is required:

- **Whole forks:** Handy at `73cc8579` (SD-M0) and VoiceStudio at `200286cc` (ST-D00), with upstream and delta branches.
- **Unchanged files:** VoiceStudio `fit_planner.py` (behind a new guard that allows overlap); OpenWhispr terminal class/exe lists; orcel-journal later (`crates/orcel-journal/**` → `wispral-journal`, packet CORE-R1).
- **Adapt with small changes:** Sentrdel policy lattice and bounded JSON; Ascout engine descriptor (→ manifest); Orcel process/peer/ACL identity; Ninerr local-HTTP auth profile; SafeEvidence egress CI gates; FreeFlow insertion algorithm; OpenWhispr cleanup-output guard and snippets; standard-webhooks verification.
- **Wrap or integrate:** Parlant (per tenant), Chatwoot (API), tau2-bench (tests), Pipecat (later), whisper.cpp/transcribe-cpp and Moonshine routes inherited through Handy.

## 7. What must be built new, and why

| Item | Why no donor suffices | Size (estimate) |
| --- | --- | --- |
| Windows target binding + fail-closed verdict + refusal (BN-01, BN-01b) | No donor binds HWND + PID + process start + focused control + UIA element on Windows and refuses on mismatch; UIPI fails silently | ~1 pure module + 1 Windows module |
| `DeliveryOutcome` with partial and receipt states (BN-01c) | Handy reports "Typed" before any receipt and has no partial state | One enum + typer + migration |
| Egress observation harness, Windows-strength (BN-01d) | SafeEvidence's Windows path is self-labelled weaker | CI job + harness |
| Studio consent ledger and gate (BN-03) | Consent recorded but never checked on synthesis paths | One module + four call sites |
| Rights-manifest enforcement (BN-04) | Donors lack a weight-license field with commercial blocking | Small |
| Klaint broker + outcome ledger + commitment guard (BN-02) | No donor resolves tenant credentials server-side, records intents before dispatch and reconciles unknown outcomes; Parlant v4 lets the model write final text | One Python package |
| Chatwoot ownership-epoch bridge (BN-05) | Chatwoot's handoff is documented as best-effort | Small |
| Klaint operations console views (BN-06) | No open console shows verdicts, ledger outcomes and evaluations together | Largest new UI |
| Contracts, Python lattice port, runtime fixtures (BN-07) | Each donor has its own types | Drafted already |
| Arabic text and evaluation tooling (BN-08) | No donor normalizes Arabic for matching or implements the WB-AR rules | Small + consented panel |

## 8. First ten packets in dependency order

| # | Packet | Why first |
| --- | --- | --- |
| 1 | **G1** Constitution 0.3.0 — Principle XVII lane | Without it no legitimate first merge exists |
| 2 | **C1** Freeze preservation from a base-defined job | Removes the over-applied freeze failure without weakening the freeze |
| 3 | **C2** Non-successor class with an exact section allowlist | Lets F edit only named frontier sections; B2 untouched |
| 4 | **R** Ledger record (C1, C2 and #118 as an exception) | Canonical truth before dependent work |
| 5 | **PLAN** Merge this planning package (after C1) | Makes the plan durable research authority |
| 6 | **G2** Constitution 1.0.0 — platform thesis | Ends the mission contradiction |
| 7 | **F** Frontier reconciliation | Opens the 000E/000F research Grains |
| 8 | **CORE-00** Re-pins, rights register, licence gate | Nothing is copied before the Wispral licence is recorded |
| 9 | **SD-M0** Handy fork baseline | Proves the WisprSide base builds and tests |
| 10 | **KT-01** Parlant v4 compatibility spike | Decides v4 versus v3.3.2; proves the plugin port is closed |

Then ST-D00 and ST-D00b (Studio baselines) and **D0G** (000G decision) open the first product Grains. The first product-code packets follow in dependency order: CORE-01 → BM-02 → SD-M9 → SD-M3 → SD-M4 → SD-M5 → SD-M6 → SD-M1 (after BM-01) → SD-M2 → DS-05.

## 9. Remaining genuine blockers

| Blocker | Who resolves it |
| --- | --- |
| Ratify G1 and accept its transitional preserved red; later ratify G2 | Founder |
| Name qualifying reviewers (Governance item 7: the founder, a founder-named human, or a different-vendor reviewer with recorded identity); same-family agents and `d1-local` cannot approve | Founder |
| Choose Wispral's outbound license | Founder |
| Decide whether the B2R17 frontier stands given #118's unrecorded red check | Founder |
| Code-signing route and budget; Apple Developer membership later | Founder |
| Consent program for the Arabic/English speech panel; legal review of privacy obligations | Founder |
| GPU cells for Studio and Klaint quality benchmarks | Founder (free tiers only; no purchase assumed) |
| Accept gated model terms (pyannote, Cohere Arabic, Pocket TTS) if wanted | Founder |
| Everything else (baselines, deltas, harnesses, fixtures) | Engineering, once authorized |

## 10. Verdict

**PLAN READY** — for founder review and the Phase 0 decisions. Evidence:

- **Ready:** canonical state verified live (2026-11-08); PRs #123–#125 reconciled and preserved by ancestry, #126 absorbed into correction C1; every donor re-pinned with source evidence; architecture, design, model, security, benchmark, platform and release plans complete; 73 packets with dependencies, tests, gates, rollback and execution contexts; contracts (94 cases, 10 sequences, 4 bundles), tokens (94 contrast + 40 hue checks) and the plan validator all `PASS`; six fresh-context reviews (7 blockers, 37 must-fix) addressed, and a second-round check of the blockers whose remaining gaps were also fixed ([INDEPENDENT_REVIEW.md](../../research/wispral-world-class/INDEPENDENT_REVIEW.md), [PLAN_VALIDATION.md](../../research/wispral-world-class/PLAN_VALIDATION.md)).
- **Conditions:** the proposed constitutional text (G1, Principle XVII, Governance item 7) and corrections C1/C2 still need a **qualifying** independent review before ratification; all reviews so far were same-model-family reviews. No third review round was run after the second-round fixes.
- **Not ready (by design):** implementation. Every packet is `ready: false` until the founder completes the Phase 0 steps. Before C1 merges, this draft PR fails `verify-b2r16-freeze` exactly as `main` does; that failure is reported as **FAIL**, never as passing.
