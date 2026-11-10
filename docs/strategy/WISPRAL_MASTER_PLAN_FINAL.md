# Wispral master implementation plan: final (for founder approval)

**Status: PROPOSED FINAL PLAN, at the founder's planning-approval gate.** This is planning and research only.

- It authorizes no product code, no product build, no release, and no D0G execution.
- `CORE-01` is not selected by this document.
- Approving the plan (FD-01) settles the plan. Every governance change it lists still lands through its own reviewed PR, and every Grain still needs its own 000G selection and readiness record.

**Date:** 2026-11-10. **Canonical base:** `main` at `246283f59dcdfa945ef9d49d0cc2fa5b9deb8b09`.

**Inputs not yet merged:**
- #153: the 000E Grain states, approved at `66bb707`;
- #154: the D0G package, approved at `9433034`.

**Supersedes, for sequencing and for every point it resolves:**
- the 2026-11-08 candidate [`WISPRAL_WORLD_CLASS_MASTER_PLAN.md`](WISPRAL_WORLD_CLASS_MASTER_PLAN.md);
- the phase order in `research/wispral-world-class/packets.json`;
- the critical path in [`WISPRAL_ENGINEERING_ROADMAP.md`](WISPRAL_ENGINEERING_ROADMAP.md).

Those documents stay as the detailed specifications they are. Where they conflict with this plan, this plan wins once approved.

**Machine-checked companion:** [`research/wispral-world-class/final-plan/`](../../research/wispral-world-class/final-plan/README.md).
- [`plan_graph.json`](../../research/wispral-world-class/final-plan/plan_graph.json) is the single source for every finding, decision and stage.
- [`check_plan_graph.py`](../../research/wispral-world-class/final-plan/check_plan_graph.py) validates it.
- [`RESOLUTION_REGISTER.md`](../../research/wispral-world-class/final-plan/RESOLUTION_REGISTER.md) is generated from it, and lists all 90 contradictions and gaps with citations.

---

## 1. The plan in one page

1. **Where things stand.**
   - Governance: Constitution 1.0.0 is in force, the outbound licence is Apache-2.0, and `F`, `CORE-00` and `ST-D00b` are VERIFIED.
   - **SD-M0** (Handy, WisprSide's donor) is green on both platforms, with 332 Rust tests passing on Windows and 338 on Linux. It is VERIFYING.
   - **ST-D00** (VoiceStudio, WisprStudio's donor) is BLOCKED. Its tests reach Hugging Face through the AudioSeal watermark download, which ignores `HF_HUB_OFFLINE`, and the Windows suite is red.
   - **KT-01** (Parlant, Klaint's engine) is BLOCKED. Parlant's tool server cannot be disabled and accepts a forged `customer_id`.
   - D0G, the 000G decision, is NO-GO as written.
2. **The plan resolves 90 contradictions and gaps** (19 blocking, 48 important, 23 minor) across governance, architecture, security, licensing, dependencies, the packet graph and three stale draft PRs. Each is resolved by exactly named vehicles: 21 founder decisions, 11 governance PRs, 16 packet amendments, 5 research Grains and 1 ADR.
3. **One Grain at a time.** Specification 000 says each 000G selection opens exactly one bounded Grain. The plan keeps that rule (FD-02) and rewrites the packets that contradict it.
4. **First Grain: `CORE-01`**, the eight language-neutral contracts. It is reached by amending D0G so that each blocked baseline gates only its own product (FD-03). Then a separate qualifying-reviewed 000G selection picks `CORE-01` alone.
5. **Order after the core** (FD-05, recommended):
   - **WisprSide first.** Its baseline is the only green one, and it has the highest thesis value.
   - **Klaint text second**, after the KT-01b isolation proof.
   - **WisprStudio third.** It carries the most legal and remediation work: AGPL, the founder grant, watermark rights and the Windows suite.

   No product waits on another product's internals any more.
6. **Shape of the system.**
   - Three independently installable products.
   - A shared core of contracts and fixtures only: no daemon, no shared runtime.
   - Rust owns WisprSide's runtime. Python is an evidenced, bounded exception for the WisprStudio backend and the Klaint service (ADR-0003, FD-20).
7. **Trust boundaries are designed in, not inherited.** The plan builds four things the donors lack:
   - fail-closed, target-bound text delivery;
   - consent and fail-closed watermarking on every Studio synthesis path;
   - a deterministic Klaint broker that derives the principal server-side and runs isolated per tenant;
   - zero hidden egress, proven on the shipped binary.
8. **Nothing is published** without the founder's green light at R2, R3 and R4. Installers, signing and update channels each have an owning packet.

## 2. The approval gate: what you are approving

| If you approve | Then |
| --- | --- |
| **FD-01** (the plan) | This document becomes the planning authority for sequencing. The governance wave (stage S1) and research remediation (stage S2) may start as ordinary reviewed PRs. |
| Each other **FD** in §4 that you accept | It is recorded as a founder decision with its date. A rejected or modified FD changes only the vehicles that depend on it. The graph shows which: run `check_plan_graph.py` after editing `plan_graph.json`. |
| **Nothing in this plan** | authorizes product code, a product build, D0G execution, a release, signing, publishing, or any spend. Those happen only through the gates in §11, each with its own approval. |

**Recommended way to approve:** reply with the FD numbers you accept as recommended, and give any you want changed. You can approve FD-01 and defer individual FDs. Deferred FDs simply hold the stages that depend on them.

## 3. How the plan becomes binding

- **Specifications authorize work.** Only `specs/CURRENT.md` and the specifications authorize executable work (`AGENTS.md` §1; `PROGRAM_ROADMAP.md:82`).
- **This plan's role.** It is the reviewed plan those specification changes implement. Its changes land in this order:
  1. **Founder decisions (FD).** Recorded on approval.
  2. **Governance PRs (GP-01 … GP-10).** Each is its own PR.
     - A PR that amends the Constitution, relaxes a 000G gate, or changes Specification 000 needs a **qualifying review** (Governance item 7) and the founder's approval.
     - The others need a fresh-context review and the founder's merge.
  3. **One packet regeneration (PA-SET).** It applies PA-01 … PA-16 through `build_packets.py`, under the procedure GP-01 creates. A qualifying review is needed because it relaxes D0G.
  4. **Research Grains (RG-1 … RG-4).** These are 000E and 000F research. They need no product authority and run under the existing research frontier.
  5. **000G selections, one Grain each.** Each has a qualifying review, a founder merge and a readiness record under GP-03.

## 4. Founder decisions

"Rec." is the recommendation. Each decision lists the findings it resolves (see the register).

| FD | Decision | Rec. | Alternative | Resolves |
| --- | --- | --- | --- | --- |
| **FD-01** | Approve this plan as the planning authority for sequencing | Approve | Request changes | G-19 |
| **S0-MERGE** | Merge #153 (000E states) and #154 (D0G package), both already reviewed | Merge | — | G-14 |
| **FD-02** | Keep Specification 000's exactly-one-Grain rule | Keep | Amend Spec 000 to allow several Grains (qualifying review) | G-01 |
| **FD-03** | D0G Path B: remove `ST-D00` and `KT-01` from D0G's dependencies; the first selection picks `CORE-01` only | Path B | Path A: remediate both first; this delays every Grain by the length of RG-1 plus RG-2 | G-02, A-01 |
| **FD-04** | Accept SD-M0's narrowed item 3. The VC++ runtime and installer contents move to the new `SD-R10`. | Accept | Run the installer build in SD-M0 first | S-08 |
| **FD-05** | Product order: WisprSide, Klaint text, WisprStudio | As listed | Klaint first (needs RG-1 before any product); Studio first (needs RG-2, RG-3, FD-08, FD-10) | G-09 |
| **FD-06** | WisprSide speech: an explicit 000B insufficient-evidence synthesis allows R1 internal alpha with Handy's existing local engines, labelled unranked. Accepted 000B evidence is needed before any accuracy claim and before R3. | As stated | Wait for B2 and B4 before any WisprSide Grain | G-08 |
| **FD-07** | Repositories and licences (details below) | As stated | Per-product alternatives below | G-06, L-01, L-06, A-11 |
| **FD-08** | Founder grant: until the founder records per-file scope, plan as AGPL-3.0 only; no VoiceStudio code moves into the Apache repository | As stated | The founder records grant scope now (no private document requested) | L-02 |
| **FD-09** | Synthetic speech is marked by default. Where a mark is required (cloned, third-party, licensed or commercial voice), a failed mark refuses the export. The legal reading of EU AI Act Art. 50(2) is to be checked. | As stated | Mark cloned output only (the plan's original, narrower scope) | S-02, S-03 |
| **FD-10** | Watermark technology, chosen from RG-3's evidence | Decide after RG-3 | — | S-02, L-03 |
| **FD-11** | Name one pinned local CPU model for KT-01 item 4: permissive weights, CPU-runnable, digest-pinned | Name one | Leave item 4 NOT RUN until Klaint's own readiness | D-09 |
| **FD-12** | Parlant v4.0.2 only, with Klaint-side gates; drop the v3.3.2 fallback | Accept | — (v3.3.2 lacks the required hooks and has the same flaw) | S-01, G-16, D-01 |
| **FD-13** | ST-D00: keep the recorded baseline unchanged. Remediate in RG-2 on a recorded research delta branch. | Accept | Close ST-D00 as FAILED and restart the Studio baseline | A-01, A-07, D-02 |
| **FD-14** | Name the standing qualifying-review route and its fallback | Name it | — | G-15 |
| **FD-15** | Runner plan: hosted CI for Linux; HW-A for Windows manual gates within its recorded limits; a clean-install Windows VM before R2 | Accept | Provide a second Windows machine | D-08 |
| **FD-16** | Opt-in, content-free security-advisory check to one declared host | Offer it | No check; document the risk | S-07 |
| **FD-17** | Defer third-party and commercial voice cloning beyond the Studio MVP, so no Wispral-hosted consent service is needed | Defer | Design the consent-key issuer now (new Grain) | S-12 |
| **FD-18** | Arabic claims before the consented panel (BM-04) are limited to public-subset measurements | Accept | — | P-08 |
| **FD-19** | Close draft PRs #124, #127 and #73 after their salvage items land in GP-07 | Close | Keep #73 open as reference | R-01, R-09 |
| **FD-20** | Ratify ADR-0003: core = contracts and fixtures; per-product language and authority map (§5) | Ratify | Keep ADR-0001's Rust core | A-02 |

**FD-07 details** (repositories and licences):

| Product | Code repository | Licence of Wispral's changes | Notes |
| --- | --- | --- | --- |
| Shared core, policies, harnesses, research, plan | `TheHalfMoon/Wispral` | Apache-2.0 | already decided (#146) |
| WisprSide | `TheHalfMoon/wisprside` (fork of Handy, MIT) | MIT, matching upstream | Keeps upstream merges simple. Apache-2.0 deltas are possible but add a second licence to one binary. |
| WisprStudio | `TheHalfMoon/wisprstudio` (fork of VoiceStudio, AGPL-3.0) | AGPL-3.0 | Ships with source. **Local-only:** no network-reachable service unless AGPL §13 obligations are met by a later packet. The founder grant applies only file by file, as recorded (FD-08). |
| Klaint | `TheHalfMoon/Wispral` under `services/klaint/`, or a new Apache-2.0 repo | Apache-2.0 | Parlant is Apache-2.0. Chatwoot stays an external MIT service outside `enterprise/`. |

## 5. Final architecture

The architecture is recorded in ADR-0003, which refines ADR-0002; ratifying it is FD-20.

**Topology.** Three independently installable products. Each owns its processes, cancellation, inventory, identity and side effects ([owner table](WISPRAL_PRODUCT_ARCHITECTURE.md#2-one-owner-per-responsibility)). There is no central daemon. The Constitution's "resource core" is per-product resource owners, plus the BM-05 co-running measurement.

**Shared core = contracts and fixtures.**

- **Today:** eight versioned JSON Schema contracts:
  - envelope;
  - cancellation;
  - model manifest;
  - consent;
  - policy verdict;
  - provenance;
  - delivery outcome;
  - effect intent.

  They come with shape, runtime, sequence and bundle fixtures, and RFC 8785 / NFC / path canonicalization.
- **Contracts added as minor versions before any packet consumes them** (PA-08):
  - network capability manifest;
  - runtime manifest;
  - export provenance sidecar;
  - update manifest;
  - privacy and telemetry contract;
  - the envelope event families that invariant A1 requires (agent session, permission request, utterance class, consent revoked);
  - an unavailable-capability manifest listing the OS, app, backend and language cells a release does *not* support.
- **The fixtures are the parity authority.** Every implementation, in any language, passes the shared verdict and digest fixtures. A Rust policy crate (CORE-R1) waits for a second Rust consumer (PA-08, GP-10).
- **Forks consume contracts by pinned digest.** Each fork vendors the contract package by digest and runs a CI check against it (GP-04).

**Language and authority map** (Constitution X: Rust-first unless evidence shows a better boundary):

| Product | Owns authority (Rust-first rule applied) | Bounded exception and its evidence | Model output |
| --- | --- | --- | --- |
| WisprSide | **Rust** (Tauri backend): capture, target binding, fail-closed delivery, receipts, policy enforcement | Native STT engines through `transcribe-cpp` (C++), as bounded workers. TypeScript UI is presentation only. | `evidence_only` |
| WisprStudio | Python backend (donor): consent gate, export, watermark, engine supervision | **Exception, evidenced** by ST-D00b (VoiceStudio leads on capability, 10 vs 7). The AGPL fork has no Rust runtime to extend. Boundary: one consent-and-export module with fixture conformance; engines run in isolated subprocesses. | `evidence_only` |
| Klaint | Python service: a deterministic broker that is the **sole executor** of consequential tools, and derives the principal server-side | **Exception, evidenced** by KT-01: Parlant v4.0.2 is Python. Boundary: one Parlant process per tenant in its own network namespace (RG-1); the broker is outside the model's reach. | `evidence_only` |

**Platform order:**
1. Windows 11 x64 for both desktop products.
2. Klaint on a Linux container.
3. macOS.
4. Linux desktop (PF-02).

Windows 10 is not planned. `delivery_outcome` gains a platform discriminator before PF-02 (PA-07).

**Agent control stays optional and later.** AG-00 (agent risk-tier policy and ACP event contract) must precede A-01 (PA-15).

## 6. Security baseline

These are the decisions that make the security architecture consistent with the merged evidence.

| Area | Decision | Vehicles |
| --- | --- | --- |
| Authority | Speech and model output are evidence only. Destructive actions need deterministic gates and explicit user authority. Tentative speech never becomes authority. | (settled: Constitution II, VIII, XIX) |
| Klaint tool server | **Assume it is reachable.** Every tool, including read tools, derives the principal from the server-side session plus the broker capability and ignores `context.customer_id`. Each tenant's Parlant runs in its own network namespace. A loopback probe test is part of acceptance. B6 in `INDEPENDENT_REVIEW.md` is reopened. | RG-1, PA-05 |
| Klaint output mode | A gated agent refuses to start in STREAM mode. A STREAM negative fixture is required. The voice channel stays closed until a pre-stream guard exists. | PA-05, RG-5 |
| Studio watermark | Marked by default. The weights are a pinned, staged, licence-checked asset; nothing is fetched at run time. A required mark that fails refuses the export. | FD-09, FD-10, PA-06, RG-3 |
| Studio consent | The UX collects only what the consent contract allows: an opaque subject reference and live statements. Commercial and third-party cloning is deferred. | PA-06, FD-17 |
| Egress | Zero hidden network on the shipped binary (G-EGRESS). Tests deny egress at socket or OS level, not with environment flags, and use sandboxed profiles. Build-time sources are staged. | PA-08 (CORE-07), PA-06 (ST-D08), RG-2 |
| Supply chain | Toolchain pins per fork. A deny-list gate covers the four git-sourced crates. SBOMs once packaging begins. | PA-12, PA-08, PA-07 |
| Updates and signing | WisprSide: SD-M10, PF-01, SD-R10. WisprStudio: ST-D11. PF-01 covers both. Opt-in advisory check (FD-16). | PA-06, PA-07, PA-14, FD-16 |
| Local surfaces | WisprSide removes exec surfaces and covers `--transcribe-file`. Studio hardens its local API and stays local-only. | PA-07, PA-06, FD-07 |

## 7. Dependencies and rights

- **Licences:** as in FD-07. The licence gate also covers FORK_DELTA, WRAP and BUILD_NEW packets that carry donor code. A root NOTICE file is added. The KT-01 harness's adapted Parlant code gets a rights-register row (PA-13, GP-07).
- **Weights and assets.** RG-3 (000F-W) resolves:
  - AudioSeal and PerTh;
  - the default TTS engines (VoxCPM2, MOSS-TTS-Nano; OmniVoice is non-commercial);
  - the Handy 76-model catalog;
  - ggml and `transcribe-cpp` notices;
  - VC++ runtime redistribution.

  WisprSide gains a model-catalog licence gate, SD-M12 (PA-07).
- **Closures.** RG-4 records per-donor dependency closures (torch, ggml and Vulkan, Playwright, Electron) and finishes the 000F synthesis.
- **Pins.**
  - Parlant: v4.0.2 only, with the source tree verified against `2a463ccd`.
  - Rust, Bun, Node and uv: pinned per fork and used on every platform. This closes the 1.97.1 vs 1.99.1 and Bun 1.4.2 vs 1.4.4 gaps (PA-12).
  - The Vulkan SDK is provisioned in WisprSide's Windows CI. The stale LLVM risk is dropped (PA-07).
  - Studio engine environments stay within the MVP limit (PA-06).

## 8. Governance wave (stage S1)

The governance PRs land in this order. Each lists its review level.

| # | Vehicle | What lands | Review |
| --- | --- | --- | --- |
| 1 | **GP-07** | Records refresh, with no rule changes. Refresh stale state, licence, fork and Actions claims. Add superseded notes on candidate documents. Import the two #124 review files. Add the NOTICE file, the harness register row, risk-register and copy-first updates, release-quality additions and anti-roadmap lines. | fresh review |
| 2 | **GP-01** | The procedure for amending packets | qualifying |
| 3 | **GP-02** | The Specification 000 amendment (per-capability children, scoped 000G, 000C mapping, exactly one) | qualifying |
| 4 | **GP-03** | The definition of a ready product Grain, including estimates and donor-qualification checks | qualifying |
| 5 | **GP-04** | Repository binding and contract consumption | qualifying |
| 6 | **GP-06** | "The latest Platform frontier section governs" (patch amendment) | qualifying |
| 7 | **GP-08** | Owner act, guarded merges, the standing review route, and what independent means | qualifying |
| 8 | **GP-05** | The CI aggregator, plus validate_plan, conformance and contrast jobs | fresh review |
| 9 | **GP-09** | Python and TypeScript verification sets | fresh review |
| 10 | **GP-10** | Decision-ledger rows superseding D-04, D-20, the parity wording and T-7 | fresh review |
| 11 | **ADR-0003** | The architecture record (FD-20 ratifies it) | qualifying |
| 12 | **PA-SET** | One regenerated `packets.json` with PA-01 … PA-16 | qualifying |
| 13 | **FD-19** | Close #124, #127 and #73 | — |

## 9. Packet amendment set (applied once, as PA-SET)

| PA | Change |
| --- | --- |
| PA-01 | D0G depends on `F`, `CORE-00` and `ST-D00b`, plus `SD-M0` if FD-04 is accepted. D0G, D1G and SE-01 acceptance, and the `DECISION_000G` authority, say each selection opens **exactly one** bounded Grain. |
| PA-02 | D1G drops the `SD-M6` condition. Each later product is opened by its own selection. |
| PA-03 | Shared tokens and the component kit live outside the Handy fork. DS-07 and DS-08 depend on DS-01, not on DS-05 or SD-M6. |
| PA-04 | Speech-bearing WisprSide packets depend on a recorded 000B disposition (FD-06). |
| PA-05 | KT-01 item 3 is superseded by RG-1, and KT-03, KT-06 and KT-09 depend on KT-01b instead of KT-01. KT-02, KT-03 and KT-04 require: server-side principal derivation; per-tenant network isolation with a loopback probe; a refusal to start in STREAM mode when gated tools are enabled; a STREAM negative fixture. |
| PA-06 | WisprStudio: ST-D09 depends on ST-D08 and gates ST-D03. The watermark is a staged asset with fail-closed export. ST-D08 covers build-time sources. Engine environments stay within the MVP limit. The consent UX matches the contract. Studio is local-only. Studio packets that depend on `ST-D00` depend on `ST-D00r` (RG-2) instead. New packets: **ST-D11** (identifiers, updater, Authenticode, NSIS), **ST-D12** (Windows suite repair), **ST-D13** (crash-safe long-form resume), **ST-D14** (project migration and downgrade, dubbing provenance). |
| PA-07 | WisprSide: new **SD-M12** (model-catalog licence gate). SD-M2 covers `--transcribe-file`. New **SD-R10** (installer, DLL closure, VC++ runtime, SBOM). SD-M9 provisions the Vulkan SDK. The LLVM risk is dropped. `delivery_outcome` gets a platform discriminator. The #73 input-capture patterns become coarse P4 catalog entries: modifier-only and mouse push-to-talk, microphone hot-plug, tray and launch-at-login repair, permission onboarding. |
| PA-08 | Core: CORE-01 adds cross-language digest vectors (Python, TypeScript and Rust test vectors) and fixes the bundle count. Contracts are added before their consumers (§5). The fixtures are the parity authority. CORE-07 adds test isolation and the git-crate supply-chain gate. |
| PA-09 | Klaint: KT-10 adds SSRF, DNS, redirect and private-IP tests. New **KT-HQA** (handoff summaries and conversation QA, coarse). The shared Chatwoot is stated as an accepted shared component. |
| PA-10 | One BM numbering across all documents. SD-R9 is limited to public subsets until BM-04. |
| PA-11 | Packets get a `repository` field and a merge order for the WisprSide hotspot files (`actions.rs`, `clipboard.rs`, `settings.rs`, `history.rs`). Donor modes are corrected. |
| PA-12 | Toolchain pins per fork. The Parlant source tree is verified. |
| PA-13 | Status is regenerated from canonical tasks. The validator checks states against tasks, source licence against destination repository, exactly-one selections, and reports path collisions. |
| PA-14 | PF-01 covers installers and signing for both desktop products. |
| PA-15 | New **AG-00** (agent risk-tier policy and ACP event contract) before A-01. |
| PA-16 | BM-01 splits into **BM-01a** (Handy egress baseline) and **BM-01b** (VoiceStudio egress baseline). SD-M1 depends on BM-01a and ST-D01 on BM-01b. Without this split, a blocked VoiceStudio baseline would still hold WisprSide's egress lockdown and signing. |

**Proven by the checker.** `check_plan_graph.py` applies the dependency edits of PA-01, PA-02, PA-03, PA-05, PA-06 and PA-16 to `packets.json` in memory, with KT-01b and ST-D00r modelled as research Grains. No WisprSide, Klaint or WisprStudio stage packet is then gated by the blocked `ST-D00` or `KT-01`. Klaint waits only for KT-01b to be VERIFIED, and WisprStudio only for ST-D00r.

## 10. Research remediation (stage S2; runs alongside S1)

| RG | Grain | Acceptance (summary) | Unblocks |
| --- | --- | --- | --- |
| **RG-1** | **KT-01b**: Parlant isolation proof | In the Linux target container: a forged `customer_id` call has no effect and returns no data, because the principal comes from the server-side session. Another tenant's or local process cannot reach a tenant's tool server. The source tree is verified against `2a463ccd`. If FD-11 names a model: calls per turn, p95 latency and idle RSS are measured on HW-A. | Klaint (S6) |
| **RG-2** | **ST-D00r**: Studio remediation baseline | On both platforms, with staged or stubbed watermark weights, socket-level egress denial, sandboxed profiles and Windows harness fixes, all recorded on a research delta branch: **zero model-hub connections, no runtime download**. Suite counts are recorded, and failures are classified against the original baseline. | WisprStudio (S7) |
| **RG-3** | **000F-W**: weights and assets | A licence row, with source, for each item in §7. A watermark recommendation for FD-10. | FD-10, ST-D02, ST-D09, SD-M12, SD-R10 |
| **RG-4** | **000F closure** | Per-donor dependency closures and the 000F synthesis | Spec 000 closure |
| RG-5 | Pre-stream guard (later) | A guard design that holds before tokens stream | Any streamed or voice Klaint channel |

## 11. Roadmap

Each stage has an entry gate and an exit gate. Release stages R0–R4 and their gates are as in [`WISPRAL_RELEASE_QUALITY.md`](WISPRAL_RELEASE_QUALITY.md). R2 and later need the founder's explicit green light. Product packets are **not estimated** until their readiness record (GP-03): the 32 product packets in P3–P6 have no estimate today, and the plan does not invent one.

### S0: Planning closeout (now)
- **Entry:** this plan.
- **Exit:** S0-MERGE done; FD-01 approved; the FDs you accept are recorded.

### S1: Governance wave, and S2: Research remediation (in parallel)
- **Entry:** FD-01.
- **Exit:**
  - the governance PRs in §8 are merged;
  - PA-SET is regenerated;
  - RG-1 and RG-3 are recorded. RG-2 may run longer, since only WisprStudio waits on it.
  - `SD-M0` is VERIFIED (FD-04).

### S3: First 000G selection, `CORE-01` (exactly one)
- **Entry:** PA-SET, GP-03, GP-05 (the CI exists), FD-20, and FD-04.
- **Gate:** the D0G-1 decision PR, with a qualifying review, the founder's merge, and a readiness record for `CORE-01`.
- **Then:** `CORE-01` is READY. This is the **first point where product code may be written**, and only for the contract package.

### S4: Core foundation, one selection at a time
| Order | Selection | Packet | Estimate on record |
| --- | --- | --- | --- |
| 1 | SEL-CORE-07 | CORE-07 egress, delivery and supply-chain harness | 1–2 d |
| 2 | SEL-DS-01 | DS-01 bilingual font harness and type decision | 1 d |
| 3 | SEL-BM-00 | BM-00 WB-AR pilot preregistration | 0.5 d |

### S5: WisprSide
**Selection:** SEL-SIDE opens `SD-M2` first. Each later Grain gets its own readiness record, in dependency order.

**To R1 internal alpha:**

| Step | Packets | Purpose |
| --- | --- | --- |
| Hardening | SD-M2, SD-M11, SD-M12 | Remove exec surfaces, choose retention, gate model licences |
| Egress | BM-01a, SD-M1 | Measure Handy's egress, then lock it down |
| Delivery harness | BM-02, SD-M9 | Windows fixtures and CI |
| Target-bound delivery | SD-M3, SD-M4, SD-M5, SD-M6 | Binding, fail-closed refusal, receipt clipboard, DeliveryOutcome |
| Cancellation | SD-M8 | Contract transition fixtures |
| Design | DS-05 | Tokens and kit in the fork (after DS-01) |
| Identity | SD-M10 | Wispral identifiers, updater key and feed |

- **R1 exit:** the R1 gates in `WISPRAL_RELEASE_QUALITY.md` §2 and §3.1, plus G-REVIEW on the release head.
- **Speech:** engines are labelled unranked (FD-06).

**To R2 and R3:**
- Features: SD-R1 profiles, SD-R2 local cleanup, SD-R3 selected-text rewrite, SD-R4 snippets, SD-R6 history protection, SD-R7 Arabic match keys, SD-R8 streaming preview.
- Release: SD-R10 installer and DLL closure, PF-01 signing.
- Speech evidence: BM-03, then SE-01, then SD-R9, under public-subset Arabic claims only (FD-18).
- **Accepted 000B evidence before R3** (FD-06).

### S6: Klaint text
- **Entry:** RG-1 VERIFIED and a separate selection, SEL-KLAINT, which opens `KT-03` first.
- **To R1:**
  - KT-03 broker and ledger (principal server-side, BLOCK mode enforced);
  - KT-04 review-hook gate;
  - KT-05 commitment guard;
  - KT-06 cited retrieval;
  - KT-07 Chatwoot bridge;
  - KT-08 tau2-bench harness;
  - KT-09 topology and egress;
  - KT-10 first connector with SSRF tests;
  - KT-02 multi-tenant host with namespace isolation;
  - DS-08 console;
  - KT-HQA (coarse).
- **Voice:** stays closed until RG-5.

### S7: WisprStudio
- **Entry:** RG-2 and RG-3 recorded; FD-08 and FD-10 decided; a separate selection, SEL-STUDIO, which opens `ST-D01` first.
- **To R1:**
  - BM-01b VoiceStudio egress baseline;
  - ST-D12 Windows suite repair;
  - ST-D01 strip egress and pin runtime bundles;
  - ST-D08 offline staging, including build-time sources;
  - ST-D02 permissive default engine;
  - ST-D09 fail-closed watermark;
  - ST-D03 consent ledger;
  - ST-D04 fit guard;
  - ST-D05 cancellation;
  - ST-D13 crash-safe long-form resume;
  - ST-D14 migration and dubbing provenance;
  - ST-D07 Arabic lexicon;
  - DS-07 tokens and RTL;
  - ST-D11 identifiers, updater and signing;
  - ST-D06 only if ST-D02 rejects the built-in Arabic engines.
- **Local-only** (FD-07). Own-voice and licensed voices only (FD-17).

### S8: Expansion (coarse, by priority)

1. Authority failures found in R1/R2.
2. The first reliable end-to-end workflow per product.
3. Recovery and install.
4. Held-out Arabic and Gulf evaluation, via the consented panel BM-04.
5. Measured speed.

Later horizons, still coarse:
- AG-00, then A-01 (agent control);
- PF-02 (macOS and Linux);
- CORE-08 (local-API auth);
- CORE-R1 (Rust crates, once a second Rust consumer exists);
- Klaint voice, after RG-5;
- cross-device and mobile input.

## 12. Critical path and parallelism

`S0` → `S1` (GP-07 → GP-01, GP-02, GP-03, GP-04, GP-06, GP-08 → GP-05, GP-09, GP-10, ADR-0003 → PA-SET) → `D0G-1` (CORE-01) → `CORE-07` → `DS-01` → `BM-00` → WisprSide `SD-M2` … `SD-M6` → `DS-05` → **WisprSide R1**.

- **In parallel with S1:** RG-1, RG-2, RG-3 and RG-4. These are research only.
- **Klaint** can start as soon as RG-1 is verified and its selection is made after WisprSide's first selection. Its packets do not depend on WisprSide's.
- **WisprStudio** depends on RG-2, RG-3, FD-08 and FD-10, not on WisprSide.

## 13. Top risks after this plan

| Risk | Mitigation |
| --- | --- |
| The qualifying-review route stalls (rate limits, blocked vendors) | FD-14 names a standing route and a fallback; GP-08 records it |
| HW-A capacity (memory exhausted, 37-minute release builds) slows Windows gates | FD-15; batch the Windows manual gates; a clean-install VM before R2 |
| The RG-1 isolation proof fails in the container | Klaint stays closed. WisprSide and WisprStudio are unaffected. |
| RG-2 cannot reach zero egress without large donor changes | WisprStudio stays closed. FD-13's alternative restarts the Studio baseline. |
| AudioSeal and PerTh both fail the licence check | Studio export of marked content stays refused. FD-09 is revisited with legal input. |
| 000B evidence never arrives | WisprSide stays at R1/R2 with unranked engines and makes no accuracy claims |

## 14. Validation performed

- **`check_plan_graph.py`: PASS.**
  - 90 findings, each resolved by an existing vehicle.
  - 62 vehicles with no dependency cycle and no dependency on a later stage.
  - 7 selections, each opening exactly one Grain.
  - 62 roadmap packets, each existing in `packets.json` or declared new (12 new).
  - Under the simulated amendments, no product stage is gated by a blocked baseline. Klaint and WisprStudio wait only for their research Grains, KT-01b and ST-D00r.
- **`validate_plan.mjs` on the current `packets.json`: PASS** (75 packets, 27 documents, 184 links). It is rerun on the regenerated `packets.json` in PA-SET.
- **Independent reviews** of this plan are recorded on its PR, with reviewer identity, instructions and the exact head.

## 15. Superseded material and PR dispositions

- **Superseded for sequencing:**
  - [`WISPRAL_WORLD_CLASS_MASTER_PLAN.md`](WISPRAL_WORLD_CLASS_MASTER_PLAN.md) §1.7 and §8;
  - [`WISPRAL_ENGINEERING_ROADMAP.md`](WISPRAL_ENGINEERING_ROADMAP.md) §3;
  - `packets.json` phase order.

  GP-07 adds superseded notes to each.
- **Superseded entirely, already marked:** V3 ([`WISPRAL_MASTER_PLAN_REBUILT.md`](WISPRAL_MASTER_PLAN_REBUILT.md)) and the architecture replan. GP-07 also notes their stale fit-overlap and Parlant-mechanism text.
- **#124:** close as carried. Its last two review files are imported first.
- **#127:** close as superseded by Constitution 1.0.0.
- **#73:** close after salvage:
  - donor-qualification gates go into GP-03 and the risk register;
  - input-capture patterns go into PA-07;
  - adoption rules go into the copy-first strategy.

## 16. What this plan does not do

- It writes no product code, starts no product build, and does not execute or decide D0G. `CORE-01` stays unselected until D0G-1.
- It does not amend the Constitution, Specification 000 or `packets.json`. It names those changes, and each lands through its own reviewed PR.
- It does not change the frozen B2 experiment (ATTEMPT-003, B2R17).
- It requests no private legal document. The founder grant is recorded only as the founder chooses (FD-08).
- It publishes, signs, distributes and spends nothing.
