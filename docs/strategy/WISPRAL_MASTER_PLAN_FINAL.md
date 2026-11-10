# Wispral master implementation plan: final (frozen for founder approval)

**Status: FROZEN FINAL PLAN, at the founder's approval gate.** This is planning and research only. The founder approved decisions FD-01 to FD-20 as recommended on 2026-11-10 (recorded on PR #155). This frozen text now asks for approval of the plan itself and, separately, of merging PR #155.

- It authorizes no product code, no product build, no release and no D0G execution.
- `CORE-01` is not selected here.

**Rank.** This plan ranks **below** the Constitution, Specification 000 and `specs/CURRENT.md`. It changes nothing canonical by itself. Every governance change it lists lands through its own reviewed PR, and every Grain still needs its own selection or readiness record. Only `specs/CURRENT.md` and the specifications authorize executable work (`AGENTS.md` §9, line 109; `PROGRAM_ROADMAP.md:82`).

**Date:** 2026-11-10. **Canonical base:** `main` at `f4abac79f2295c3845b3ff4518ca5af585d352bf`. That commit includes #153 (000E Grain states, `0d997d5`), #154 (D0G package, `f40cce2`) and GP-07 (#156, `f4abac7`).

## 0. Execution status: what is done and what is only planned

**Done** (each with its evidence):

| Vehicle | Result |
| --- | --- |
| S0-MERGE | #153 merged as `0d997d5`; #154 merged as `f40cce2` |
| FD-01 to FD-20 | Approved as recommended on 2026-11-10 and recorded on PR #155. Exceptions: FD-11 and FD-14 still need the founder's named input, and FD-10 waits for the RG-3 evidence. |
| GP-07 | Records refresh merged as #156 (`f4abac7`). It deliberately left GOV-20 alone, because that is B2-lane text; GOV-20 now goes to the B2-lane vehicle B2L-1. |
| FD-19 | #124, #127 and #73 closed on 2026-11-10, with their branches kept |

**Planned, not started.** Everything else in this plan is a planned implementation step: AM-1, AM-2, GP-01 to GP-14S, ADR-0003, the four packet regenerations, the research Grains and every 000G selection. **None has been started.** Each starts only when its dependencies are met, and each needs its own PR, its own review and the founder's merge.

**Open founder inputs:**
- FD-11: the local CPU model to measure.
- FD-14: the standing qualifying-review route. Until it is named, a reviewer is named per PR.
- FD-10: the watermark technology, after RG-3.
- The copyright holder named in the root `NOTICE` (merged with GP-07 as "the Wispral authors (repository owner: TheHalfMoon)").

**Supersedes, for sequencing only, these non-canonical candidate documents:**
- the 2026-11-08 [`WISPRAL_WORLD_CLASS_MASTER_PLAN.md`](WISPRAL_WORLD_CLASS_MASTER_PLAN.md) §1.7 and §8;
- [`WISPRAL_ENGINEERING_ROADMAP.md`](WISPRAL_ENGINEERING_ROADMAP.md) §3.

The phase order in `packets.json` changes only through the four packet regenerations in §9, never by approving this plan.

**Machine-checked companion:** [`research/wispral-world-class/final-plan/`](../../research/wispral-world-class/final-plan/README.md).
- [`plan_graph.json`](../../research/wispral-world-class/final-plan/plan_graph.json) is the single source for every finding, decision, stage and packet placement.
- [`check_plan_graph.py`](../../research/wispral-world-class/final-plan/check_plan_graph.py) validates it.
- [`RESOLUTION_REGISTER.md`](../../research/wispral-world-class/final-plan/RESOLUTION_REGISTER.md) is generated from it. It lists all 121 findings with citations, every vehicle, the disposition of every packet that is not placed, and the roadmap groups.

---

## 1. The plan in one page

1. **Where things stand.**
   - Governance: Constitution 1.0.0 is in force, the outbound licence is Apache-2.0, and `F`, `CORE-00` and `ST-D00b` are VERIFIED.
   - **SD-M0** (Handy, WisprSide's donor) is green on both platforms. It is VERIFYING.
   - **ST-D00** (VoiceStudio, WisprStudio's donor) is BLOCKED. Its tests reach Hugging Face through the AudioSeal watermark download, and the Windows suite is red.
   - **KT-01** (Parlant, Klaint's engine) is BLOCKED. Parlant's tool server cannot be disabled and accepts a forged `customer_id`.
   - D0G is NO-GO as written.
2. **121 findings resolved:** 33 blocking, 64 important, 24 minor. They span governance, architecture, security, licensing, dependencies, the packet graph and three stale draft PRs. 30 of them came from two review rounds of this plan, and 1 from the author's own dependency audit. Each is resolved by named vehicles:
   - 21 founder decisions;
   - 2 constitutional amendments;
   - 19 governance and plan PRs, including the four packet regenerations;
   - 1 B2-lane vehicle outside this plan's authority (B2L-1);
   - 16 packet amendments;
   - 5 research Grains;
   - 1 ADR;
   - 6 one-Grain 000G selections;
   - 1 coarse direction.
3. **One Grain per selection, one selection per capability** (GP-02).
   - A 000G selection opens exactly one Grain: the first Grain of one capability (core, design, benchmarks, WisprSide, Klaint text or WisprStudio).
   - It also creates that capability's implementation spec.
   - Later Grains of an opened capability become READY by readiness record under that spec.
   - That makes **six** qualifying-reviewed selections in total, not one per packet.
4. **First Grain: `CORE-01`**, the eight language-neutral contracts.
   - D0G is amended so each blocked baseline gates only its own product (FD-03).
   - Then the first selection, D0G-1, opens `CORE-01` alone.
5. **Preferred order after the foundation** (FD-05, recommended):
   - **WisprSide first.** It has the only green baseline and the highest thesis value.
   - **Klaint text second**, after the KT-01b isolation proof.
   - **WisprStudio third.** It carries the most legal and remediation work.

   This order is a **preference, not a dependency**. Each product's selection depends only on the foundation and its own prerequisites, so a product that is blocked never holds another. The checker proves this on the amended graph.
6. **Shape of the system.**
   - Three independently installable products.
   - A shared core of contracts and fixtures only: no daemon, no shared runtime.
   - Rust owns WisprSide's runtime. Python is an evidenced, bounded exception for the WisprStudio backend and the Klaint service (ADR-0003).
7. **Trust boundaries are designed in, not inherited:**
   - fail-closed, target-bound text delivery;
   - consent and marking on every Studio synthesis path, refusing export when a required mark fails;
   - a Klaint broker capability required on every tool call, issued only to Parlant over a dedicated channel, with per-tenant container isolation;
   - zero hidden egress, proven on the shipped binary.
8. **Nothing is published** without the founder's green light at R2, R3 and R4. Installers, signing and update channels each have an owning packet.

## 2. The approval gate

**Already decided.** FD-01 to FD-20 were approved as recommended on 2026-11-10 (§0).

**What this frozen version asks for:**

| Approval | Effect |
| --- | --- |
| **Approve the frozen plan** | This text, at its reviewed head, becomes the plan of record for sequencing. The next planned step, AM-1, still starts only on the founder's separate instruction. |
| **Approve merging PR #155** (separate) | The plan lands on `main` as a non-canonical strategy document. It still ranks below the Constitution, Specification 000 and `specs/CURRENT.md`. |
| **Nothing in this plan** | authorizes product code, a product build, D0G execution, a release, signing, publishing, or any spend |

**What happens if you defer a decision.** Deferring an FD holds every vehicle that depends on it. `plan_graph.json` lists those dependencies.

The work is split so that **deferring one product's decisions never holds the core or another product**:
- **Packet amendments.** There are four regenerations. PA-SET-CORE covers everything `CORE-01` and the foundation need; PA-SET-SIDE, PA-SET-KLAINT and PA-SET-STUDIO cover each product.
- **Specification 000.** The speech change is its own PR (GP-02S), so it holds only WisprSide.
- **Security and architecture text.** Klaint's security text (GP-12), the core parity text (GP-14C) and the Studio local-only text (GP-14S) are three separate PRs.
- **Review route.** The standing route is its own amendment (AM-2), so FD-14 holds nothing else.
- **SD-M0.** Its verification record (GP-13) is separate from the research frontier (GP-11), so FD-04 does not hold the research Grains.

**Decisions each selection needs** (computed from `plan_graph.json`):

| Selection | Needs |
| --- | --- |
| `CORE-01` (D0G-1); also SEL-DESIGN and SEL-BENCH | S0-MERGE, FD-01, FD-02, FD-03, FD-04, FD-07, FD-20 |
| WisprSide (SEL-SIDE) | adds FD-06, FD-15, FD-16, FD-18 |
| Klaint (SEL-KLAINT) | adds FD-12 |
| WisprStudio (SEL-STUDIO) | adds FD-08, FD-09, FD-10, FD-13, FD-15, FD-16, FD-17 |
| Research: KT-01b / ST-D00r / 000F-W | S0-MERGE and FD-01, plus FD-12 (KT-01b) or FD-13 (ST-D00r) |


## 3. How the plan becomes binding

Changes land in this order:

1. **Founder decisions (FD).** Recorded on approval.
2. **Amendments AM-1 and AM-2.** Constitutional, minor versions 1.1.0 and 1.2.0. Governance item 7 **requires** a qualifying review for each.
3. **Governance and plan PRs** (§8).
   - The plan chooses a qualifying review, which is stricter than item 7 requires, for: GP-01, GP-02, GP-02S, GP-03, GP-05, GP-11, GP-12, GP-14C, GP-14S, ADR-0003 and the four packet regenerations. They change Specification 000, relax a 000G gate, open research Grains, or change gates and security text.
   - The others take a fresh-context review.
   - All of them need the founder's merge.
4. **Research Grains.** KT-01b, ST-D00r and 000F-W are opened by GP-11, an amendment of the 000E and 000F specs plus a new frontier section. Each becomes READY by its own readiness record.
5. **The six 000G selections.** Governance item 7 **requires** a qualifying review for each. Each also needs the founder's merge and a readiness record (GP-03).
6. **Later Grains.** Readiness records under each capability's implementation spec, with a fresh review and the founder's merge.

## 4. Founder decisions (approved 2026-11-10)

"Rec." is the final recommendation. **All of them were approved as recommended on 2026-11-10.** FD-11 and FD-14 still need a named input, FD-10 waits for RG-3, and FD-19 is done. Each row lists the findings it resolves, using the IDs in the register.

| FD | Decision | Rec. | Alternative | Resolves |
| --- | --- | --- | --- | --- |
| **FD-01** | Approve this plan as the reviewed plan for sequencing, below the Constitution, Specification 000 and `specs/CURRENT.md` | Approve | Request changes | GOV-19 |
| **S0-MERGE** | Merge #153 (000E states) and #154 (D0G package), both already reviewed | Merge | — | GOV-14 |
| **FD-02** | Keep Specification 000's exactly-one rule, applied per capability (GP-02) | Keep | Amend Spec 000 to open several Grains per selection | GOV-01 |
| **FD-03** | D0G Path B: remove `ST-D00` and `KT-01` from D0G's dependencies; the first selection opens `CORE-01` only | Path B | Path A: remediate both first; this delays every Grain | GOV-02, ARC-01 |
| **FD-04** | Accept SD-M0's narrowed item 3. The VC++ runtime and installer contents move to `SD-R10`. SD-M0 becomes VERIFIED through GP-13's reviewed tasks change. | Accept | Run the installer build in SD-M0 first | SEC-08 |
| **FD-05** | Preferred product order: WisprSide, Klaint text, WisprStudio. It is a preference, not a dependency; each product is opened by its own selection once its own prerequisites are met. | As listed | Another preference order | GOV-09, PKT-22 |
| **FD-06** | WisprSide speech: R1 internal alpha with Handy's existing engines labelled unranked and no accuracy claim, **only once GP-02S amends Specification 000** to allow it. Accepted 000B evidence before any accuracy claim and before R3. | As stated | Wait for B2 and B4 before any WisprSide Grain | GOV-08, GOV-25 |
| **FD-07** | Repositories and licences (details below) | As stated | Per-product alternatives below | GOV-06, LIC-01, LIC-06, LIC-10, LIC-11, ARC-11 |
| **FD-08** | Founder grant: until the founder records per-file scope, plan as AGPL-3.0 only; no VoiceStudio code moves into the Apache repository | As stated | The founder records grant scope now (no private document requested) | LIC-02 |
| **FD-09** | Mark every synthetic output by default. **Until the legal reading of EU AI Act Art. 50(2) is recorded, every mark is required**, so any failed mark refuses export. After that reading, the founder may scope required marks (cloned, third-party, licensed, commercial). Other failures are then shown visibly and recorded as "unmarked" in the provenance sidecar. | As stated | Mark cloned output only | SEC-02, SEC-03, SEC-18 |
| **FD-10** | Watermark technology, chosen from RG-3's evidence | Decide after RG-3 | — | SEC-02, LIC-03 |
| **FD-11** | Name one pinned local CPU model (permissive weights, CPU-runnable, digest-pinned) for the KT-01 item-4 measurement in KT-01b | Name one | Leave item 4 NOT RUN, so KT-01 stays BLOCKED and Klaint relies on KT-01b alone | DEP-09 |
| **FD-12** | Parlant v4.0.2 only, with Klaint-side gates; drop the v3.3.2 fallback | Accept | — (v3.3.2 lacks the hooks and has the same flaw) | SEC-01, GOV-16, DEP-01 |
| **FD-13** | ST-D00: keep the recorded baseline unchanged. Remediate in ST-D00r on a recorded research delta branch. | Accept | Close ST-D00 as FAILED and restart the Studio baseline | ARC-01, ARC-07, DEP-02 |
| **FD-14** | Name the qualifying-review route and its fallback. A standing route lands through AM-2; until then, a reviewer is named per PR as item 7(b) allows. | Name it | Keep naming a reviewer per PR | GOV-15 |
| **FD-15** | Runner plan: hosted CI for Linux; HW-A for Windows manual gates within its recorded limits; a clean-install Windows VM before R2 | Accept | Provide a second Windows machine | DEP-08 |
| **FD-16** | Opt-in, content-free security-advisory check to one declared host | Offer it | No check; document the risk | SEC-07 |
| **FD-17** | Defer third-party, licensed-actor and commercial cloning beyond the Studio MVP. The MVP offers self and non-commercial voices plus manifest-catalog stock voices. No Wispral-hosted consent service is needed. | Defer | Design the consent-key issuer now (new Grain) | SEC-12, LIC-12 |
| **FD-18** | Arabic claims before the consented panel (BM-04) are limited to public-subset measurements | Accept | — | PKT-08 |
| **FD-19** | Close draft PRs #124, #127 and #73 after their salvage items land in GP-07 | Close | Keep #73 open as reference | SAL-01, SAL-09 |
| **FD-20** | Ratify ADR-0003 (§5) | Ratify | Keep ADR-0001's Rust core | ARC-02 |

**FD-07 details** (repositories and licences; this is not legal advice):

| Product | Code repository | Licence of Wispral's changes | Conditions |
| --- | --- | --- | --- |
| Shared core, policies, harnesses, research, plan | `TheHalfMoon/Wispral` | Apache-2.0 | Decided (#146) |
| Klaint | `TheHalfMoon/Wispral`, at `services/klaint-dialogue/` (the path the packets use) | Apache-2.0 | Parlant is Apache-2.0. Chatwoot stays an external MIT service outside `enterprise/`. |
| WisprSide | `TheHalfMoon/wisprside` (fork of Handy, MIT) | MIT, matching upstream | The binary also carries Apache-2.0 material (the vendored contracts and adapted Orcel/Sentrdel code), so a NOTICE and an About screen are required. |
| WisprStudio | `TheHalfMoon/wisprstudio` (fork of VoiceStudio, AGPL-3.0) | AGPL-3.0 | **Local-only**, enforced by the ST-D01 test: loopback binding, Host/Origin checks, per-launch token. No LAN render workers. A source offer in the UI and API. The founder grant applies only file by file (FD-08). |

**For every product: no AGPL material may flow into MIT or Apache code.** The Arabic lexicon pair (ST-D07 adapts AGPL code; SD-R7 is in the MIT fork) is checked by name (PA-13).

## 5. Final architecture

The architecture is recorded in ADR-0003, refining ADR-0002. FD-20 ratifies it; AM-1(d) clarifies the Preamble's "resource core".

**Topology.** Three independently installable products. Each owns its processes, cancellation, inventory, identity and side effects ([owner table](WISPRAL_PRODUCT_ARCHITECTURE.md#2-one-owner-per-responsibility)).

- There is no central daemon.
- The "resource core" means per-product resource owners, plus the BM-05 co-running measurement.
- Until BM-05 runs, ADR-0003 states how the products handle microphone and CPU contention when installed together.

**Shared core = contracts and fixtures.**

- **`CORE-01`.** The eight existing contracts:
  - envelope;
  - cancellation;
  - model manifest;
  - consent;
  - policy verdict;
  - provenance;
  - delivery outcome;
  - effect intent.

  They come with shape, runtime, sequence and bundle fixtures, RFC 8785 / NFC / path canonicalization, and cross-language digest vectors in Python, TypeScript and Rust.
- **`CORE-02`, a new packet.** It owns the contracts added before their consumers:
  - network capability manifest;
  - runtime manifest;
  - export provenance sidecar, with an `unmarked` flag;
  - update manifest;
  - privacy and telemetry contract;
  - the envelope event families that invariant A1 requires;
  - the unavailable-capability manifest.
- **Parity.** Every implementation passes the shared fixtures. That replaces "identical Rust and Python verdicts" (GP-14C updates SI-2 and the contracts README). A Rust policy crate (CORE-R1) waits for a second Rust consumer.
- **Contract consumption.** Forks vendor the contract package by digest, with a CI check (GP-04).

**Language and authority map** (Constitution X: Rust-first unless evidence shows a better boundary):

| Product | Owns authority | Bounded exception and its evidence | Model output |
| --- | --- | --- | --- |
| WisprSide | **Rust** (Tauri backend): capture, target binding, fail-closed delivery, receipts, policy enforcement | Native STT engines through `transcribe-cpp` (C++), as bounded workers. TypeScript UI is presentation only. | `evidence_only` |
| WisprStudio | Python backend (donor): consent gate, export, marking, engine supervision | **Evidenced** by ST-D00b (VoiceStudio leads on capability, 10 vs 7). The AGPL fork has no Rust runtime to extend. Boundary: one consent-and-export module with fixture conformance; engines in isolated subprocesses. | `evidence_only` |
| Klaint | Python service. The **broker** is the sole executor of consequential tools and issues the per-call capability. | **Evidenced** by KT-01: Parlant v4.0.2 is Python. The broker is BUILD_NEW and is placed in a **separate process from Parlant**, outside the model's reach. It issues capabilities only to Parlant, over a dedicated channel no other resident can reach, and binds each one to the proposal it reviewed. One stack per tenant, in its own container with a distinct UID (RG-1). | `evidence_only` |

**Platform order:**
1. Windows 11 x64 for both desktop products.
2. Klaint on a Linux container.
3. macOS.
4. Linux desktop (PF-02).

`delivery_outcome` gains a platform discriminator before PF-02.

**Agent control stays optional and later.** AG-00 (agent risk-tier policy and ACP event contract, after CORE-02) precedes A-01.

## 6. Security baseline

| Area | Decision | Vehicles |
| --- | --- | --- |
| Authority | Speech and model output are evidence only. Destructive actions need deterministic gates and explicit user authority. | (settled: Constitution II, VIII, XIX) |
| Klaint tool server | **Assume it is reachable.** Every tool, read tools included, requires the broker-issued capability (bound to session, tool and arguments; short-lived; single use) and ignores `context.customer_id`. Each tenant runs its own container stack with a distinct UID, and the residents of each namespace are listed. | RG-1, PA-05, GP-12 |
| Capability issuance | The broker's issuance channel is a trust boundary. It accepts requests only from Parlant, over a dedicated channel no other resident (console, connector, bridge) can reach. The mechanism is a distinct UID per component inside the tenant stack, or a socket on a mount only Parlant can see; ADR-0003 fixes the choice. It binds each capability to the tool proposal it reviewed in `on_reviewing_tool_calls`, never to a caller-supplied session ID. | RG-1, PA-05, GP-12, ADR-0003 |
| Klaint probes | Each of these yields zero effects and zero data, under production `AuthConfig`, not dev allow-all: a made-up session; **a valid live session of another customer of the same tenant**; another tenant; every tool-server route, including `GET /tools`; loopback from a KT-10 connector; **a capability request to the broker from any resident other than Parlant**, which must yield no capability. | RG-1, PA-05, PA-09 |
| Canonical text | KL-T3, KT-02 and KT-03 stop saying the tool server is disabled. B6 is reopened. KL-T5 records the shared-Chatwoot residual risk, or moves to per-tenant Chatwoot. | GP-12, PA-05 |
| Klaint output mode | **Every customer-facing agent whose message gate is required runs in BLOCK mode**, with or without tools. This is enforced at start-up and at run time, with a per-session STREAM negative fixture. Voice stays closed until a pre-stream guard exists (RG-5). | PA-05, RG-5 |
| Studio marking | Marked by default. The weights are a pinned, staged, licence-checked asset, never fetched at run time. Until the legal reading is recorded, every failed mark refuses the export. | FD-09, FD-10, PA-06, RG-3 |
| Studio consent | The UX collects only what the consent contract allows. Licensed-actor and commercial cloning are deferred. | PA-06, FD-17 |
| Egress | Zero hidden network on the shipped binary. Tests deny egress at OS or namespace level over the whole process tree, including native `git`, and use sandboxed profiles. Build-time sources are staged. | PA-08 (CORE-07), PA-06 (ST-D08), RG-2 |
| Supply chain | Toolchain pins per fork. A deny-list gate covers the four git-sourced crates. SBOMs once packaging begins. | PA-12, PA-08, PA-07 |
| Updates and signing | WisprSide: SD-M10, SD-R10, PF-01. WisprStudio: ST-D11. PF-01 covers both. Opt-in advisory check (FD-16). | PA-06, PA-07, PA-14, FD-16 |
| Local surfaces | WisprSide removes exec surfaces and covers `--transcribe-file`. Studio is local-only by test. | PA-07, PA-06, FD-07 |

## 7. Dependencies and rights

- **Licences:** as in FD-07. The licence gate also covers FORK_DELTA, WRAP and BUILD_NEW packets that carry donor code. A root NOTICE file is added. The KT-01 harness's adapted Parlant code gets a rights row (PA-13, GP-07).
- **Weights, data, voices, fonts and media** each get their own row in RG-3 (000F-W):
  - AudioSeal and PerTh;
  - the default TTS engines;
  - the Handy model catalog;
  - the FD-11 model;
  - Klaint inference and embedding weights;
  - Studio stock voices;
  - DS-01 fonts;
  - Arabic lexicon and benchmark datasets;
  - tau2-bench task data;
  - Chatterbox and Perth, if chosen;
  - the Studio FFmpeg build;
  - ggml and `transcribe-cpp` notices;
  - VC++ runtime redistribution.

  WisprSide also gains a model-catalog licence gate, SD-M12.
- **Closures.** RG-4 records per-donor dependency closures (torch, ggml and Vulkan, Playwright, Electron) and finishes the 000F synthesis.
- **Pins.**
  - Parlant: v4.0.2 only, with the source tree verified against `2a463ccd`.
  - Rust, Bun, Node and uv: pinned per fork and used on every platform.
  - The Vulkan SDK is provisioned in WisprSide's Windows CI. The stale LLVM risk is dropped.
  - Studio engine environments stay within the MVP limit.

## 8. Governance wave (stage S1)

**Only GP-07 is done. Every other row is a planned step, not yet started.** Each needs its own PR, its review and the founder's merge.

| # | Vehicle | What lands | Review |
| --- | --- | --- | --- |
| 1 | **GP-07** (**DONE**, #156 `f4abac7`) | Records refresh in **editable sections and non-canonical documents only**, never a frozen frontier section. Refreshed stale licence, fork and Actions claims and added superseded notes. Imported the two #124 review files. Added the NOTICE file and the harness rights row, plus risk-register, copy-first, release-quality and anti-roadmap updates. GOV-20 was not changed: it is B2-lane text, handled by B2L-1. | fresh (done) |
| 2 | **AM-1** | Constitutional amendment 1.1.0: <ul><li>(a) the product-code gate, review and evidence rules **extend** to the product repositories. Extend-only; research branches the frontier authorizes are not product code.</li><li>(c) the latest appended Platform frontier section governs. It names what it supersedes, covers `specs/CURRENT.md` and `CURRENT_STATE.md`, and grants nothing beyond the specifications.</li><li>(d) the resource core means per-product owners</li></ul> | qualifying (required) |
| 2b | **AM-2** | Constitutional amendment 1.2.0: (b) a standing qualifying-review route under item 7(b). Every other item 7 condition is unchanged. Until it lands, reviewers are named per PR. | qualifying (required) |
| 3 | **GP-01** | Procedure for amending packets | qualifying |
| 4 | **GP-02** | Specification 000 amendment: <ul><li>one selection opens the first Grain of one capability and creates its implementation spec;</li><li>per-capability required children;</li><li>000C mapping</li></ul> | qualifying |
| 4b | **GP-02S** | Specification 000 speech amendment: R1-only use of unranked speech engines before accepted 000B evidence. It holds only WisprSide. | qualifying |
| 5 | **GP-03** | Definition of a ready Grain, including an estimate made at readiness and the donor-qualification checks | qualifying |
| 6 | **GP-11** | A new appended Platform frontier section with current states. Amendments to the 000E and 000F specs opening **exactly three** more research Grains (KT-01b, ST-D00r and 000F-W), and amending 000E's scope clauses so that ST-D00r's remediation is in scope as research. | qualifying |
| 6b | **GP-13** | SD-M0 verification record: the 000E tasks change recording the founder's confirmation of the narrowed item 3 (FD-04) and SD-M0 VERIFIED | fresh |
| 7 | **GP-04** | How contract versions are consumed in forks, and the packet repository field | fresh |
| 8 | **GP-08** | Owner-act comment format and guarded expected-head merges | fresh |
| 9 | **GP-12** | Klaint security-architecture amendment: KL-T3 (reachable tool server, capability per tool, authenticated issuance), B6 reopened, KL-T5 and Chatwoot | qualifying |
| 9b | **GP-14C** | Core parity text: SI-2 and contracts-README parity wording. CORE-01 depends on it, and it needs no product decision. | qualifying |
| 9c | **GP-14S** | Studio architecture text: no LAN render workers; Studio local-only. It holds only WisprStudio. | qualifying |
| 10 | **ADR-0003** | The architecture record (FD-20 ratifies it) | qualifying |
| 11 | **GP-05** | CI in the Wispral repo **and both forks**: an aggregator check, validate_plan, conformance, contrast and the fork suites. The B2 lane workflows are untouched. | qualifying |
| 12 | **GP-09** | Python and TypeScript verification sets | fresh |
| 13 | **GP-10** | Decision-ledger rows superseding D-04, D-20 and T-7 | fresh |
| 14 | **PA-SET-CORE** | Regeneration 1: PA-01, PA-02, PA-03, PA-08, PA-11, PA-12, PA-13, PA-15, PA-16 | qualifying |
| 15 | **PA-SET-SIDE**, **PA-SET-KLAINT**, **PA-SET-STUDIO** | Regenerations 2–4: PA-04, PA-07, PA-10, PA-14 (WisprSide); PA-05, PA-09 (Klaint, after GP-12 and GP-10); PA-06 (WisprStudio, after GP-14S) | qualifying |
| 16 | **FD-19** (**DONE** 2026-11-10) | Closed #124, #127 and #73 after GP-07 | — |
| — | **B2L-1** (B2 lane, not scheduled here) | The B2 lane, under its own authority, updates the stale 000B text in `specs/000-founding-research/tasks.md` and records the private lane's closure, so that Specification 000 can close | B2 lane |

## 9. Packet amendments

| PA | Set | Change |
| --- | --- | --- |
| PA-01 | CORE | D0G depends on `F`, `CORE-00`, `ST-D00b` and `SD-M0`. D0G, SE-01 and the `DECISION_000G` authority say each selection opens exactly one Grain of one capability. |
| PA-02 | CORE | **Retire D1G.** GP-02 opens each capability by its own selection. |
| PA-03 | CORE | New **DS-KIT**: product-neutral tokens and component kit in the Wispral repo, after DS-01's type decision. DS-05, DS-07 and DS-08 apply DS-KIT in their products and no longer depend on SD-M6. |
| PA-08 | CORE | CORE-01 adds cross-language digest vectors and fixes the bundle count. New **CORE-02** owns the added contracts and precedes their consumers. Fixtures are the parity authority. CORE-07 adds OS-level egress denial over the process tree, sandboxed profiles and the git-crate gate. |
| PA-11 | CORE | A `repository` field, and a merge order for WisprSide hotspot files. Donor modes are corrected. |
| PA-12 | CORE | Toolchain pins per fork. The Parlant source tree is verified. |
| PA-13 | CORE | Status is regenerated from canonical tasks. The validator checks states, licence direction (naming the SD-R7/ST-D07 pair), exactly-one selections and path collisions. |
| PA-16 | CORE | BM-01 splits into **BM-01a** (Handy) and **BM-01b** (VoiceStudio, after ST-D00r). SD-M1 depends on BM-01a and ST-D01 on BM-01b. BM-01 is retired. |
| PA-04 | SIDE | Speech-bearing WisprSide packets carry the GP-02S R1-only condition and need accepted 000B evidence for R3. |
| PA-05 | KLAINT | KT-01 stays BLOCKED for item 3 and is **superseded** for it by KT-01b, never rewritten into a pass. KT-03, KT-06 and KT-09 depend on KT-01b. **KT-03's title and acceptance are rewritten for a broker in a separate process from Parlant.** KT-02 and KT-03 "plugin server disabled/off" items are **replaced** by: <ul><li>the capability on every tool;</li><li>an authenticated issuance channel reachable only by Parlant, with capabilities bound to the reviewed proposal;</li><li>per-tenant container isolation with a distinct UID;</li><li>the KT-01b probes;</li><li>BLOCK mode for every customer-facing agent whose message gate is required, at start-up and at run time, with a per-session STREAM negative fixture.</li></ul> KT-10 tests name the loopback tool-server port and the issuance channel. |
| PA-06 | STUDIO | Studio: <ul><li>ST-D09 depends on ST-D08 and gates ST-D03;</li><li>marking per FD-09;</li><li>ST-D08 covers build-time sources;</li><li>engine environments within the MVP limit;</li><li>consent UX matches the contract;</li><li>local-only by the ST-D01 test, with a source offer;</li><li>Studio packets depend on ST-D00r instead of ST-D00.</li></ul> New **ST-D11** (identifiers, updater, Authenticode, NSIS), **ST-D12** (Windows suite repair: the fork's Windows suites green in fork CI at the exact head, with failures fixed, not deselected; distinct from ST-D00r, which only measures the donor on a research branch), **ST-D13** (crash-safe long-form resume), **ST-D14** (project migration and downgrade, dubbing provenance). |
| PA-07 | SIDE | WisprSide: <ul><li>new **SD-M12** (model-catalog licence gate);</li><li>SD-M2 covers `--transcribe-file`;</li><li>new **SD-R10** (installer, DLL closure, VC++ runtime, SBOM);</li><li>SD-M9 provisions the Vulkan SDK;</li><li>the LLVM risk is dropped;</li><li>`delivery_outcome` gets a platform discriminator;</li><li>the #73 input-capture patterns become coarse P4 entries.</li></ul> |
| PA-09 | KLAINT | KT-10 adds SSRF, DNS, redirect, private-IP and loopback tests. New **KT-HQA** (handoff summaries and conversation QA, coarse). |
| PA-10 | SIDE | One BM numbering across all documents. SD-R9 is limited to public subsets until BM-04. |
| PA-14 | SIDE | PF-01 covers installers and signing for both desktop products |
| PA-15 | CORE | New **AG-00** (agent risk-tier policy and ACP event contract, after CORE-02) before A-01 |

**What the checker simulates.** It applies the **dependency** edits of these amendments to `packets.json` in memory. Edits to acceptance text, such as SE-01's two-packet wording and KT-03's "plugin server disabled", are not simulated. They are verified in review of the four regenerations.

## 10. Research Grains (stage S2, opened by GP-11)

| RG | Grain | Acceptance (summary) | Unblocks |
| --- | --- | --- | --- |
| **RG-1** | **KT-01b**: Parlant isolation proof. A bounded experimental harness, not KT-03 code. | <ul><li>In the Linux target container stack with production `AuthConfig`: every tool requires the broker capability and ignores `context.customer_id`.</li><li>The broker issues capabilities only to Parlant, over a dedicated channel, bound to the reviewed proposal.</li><li>The probes in §6 all yield zero effects and zero data, and no non-Parlant resident obtains a capability.</li><li>One container per tenant, with a distinct UID; namespace residents listed.</li><li>Source tree verified against `2a463ccd`.</li><li>If FD-11 names a model: calls per turn, p95 latency and idle RSS on HW-A.</li></ul> | Klaint (S6) |
| **RG-2** | **ST-D00r**: Studio remediation baseline | <ul><li>On both platforms, on a recorded research delta branch: staged or stubbed watermark weights; OS or namespace-level egress denial over the whole process tree; sandboxed profiles; Windows harness fixes.</li><li>**Zero model-hub connections, no runtime download.**</li><li>Suite counts recorded against the original baseline.</li></ul> | WisprStudio (S7) |
| **RG-3** | **000F-W**: weights, data, voices, fonts, media | A rights row, with its source, for each item in §7. A watermark recommendation for FD-10. | FD-10, ST-D02, ST-D09, SD-M12, SD-R10 |
| **RG-4** | **000F closure** | Per-donor dependency closures and the 000F synthesis | Spec 000 closure |
| RG-5 | Pre-stream guard (later) | A guard design that holds before tokens stream | Klaint voice |

## 11. Roadmap

Release stages R0–R4 and their gates are as in [`WISPRAL_RELEASE_QUALITY.md`](WISPRAL_RELEASE_QUALITY.md). R2 and later need the founder's explicit green light.

**Estimates.** 35 product packets in P3–P6 have no estimate today (49 across all phases). The plan does not invent numbers: GP-03 requires an estimate in each readiness record.

### S0: Planning closeout (**done**)
- S0-MERGE is done. FD-01 to FD-20 are approved and recorded.

### S1: Governance wave, and S2: Research Grains (**planned**; GP-07 and FD-19 done)
- **Entry:** FD-01 (met). AM-1 starts only on the founder's instruction.
- **Exit:** the PRs in §8 are merged. KT-01b, ST-D00r and 000F-W run once GP-11 opens them.
- **Important:** `CORE-01` does **not** wait for the research Grains, and FD-04 does not hold them. Only Klaint waits for KT-01b, and only WisprStudio waits for ST-D00r and 000F-W.

### S3: First 000G selection, D0G-1, opening `CORE-01`
- **Entry:** PA-SET-CORE, GP-03, GP-05, GP-08, GP-09, GP-11, GP-13 (SD-M0 VERIFIED), GP-14C, AM-1 and FD-20.
- **Gate:** a qualifying review, the founder's merge, and a readiness record for `CORE-01`.
- **This is the first point where product code may be written**, and only for the contract package.

### S4: Foundation
| Group | Grains, in order | How they open |
| --- | --- | --- |
| Core | CORE-02 (added contracts), CORE-07 (egress, delivery and supply-chain harness) | Readiness records under the core spec |
| Design | DS-01 (font harness, type decision), DS-KIT (tokens and component kit) | SEL-DESIGN opens DS-01; DS-KIT by readiness record |
| Benchmarks | BM-00 (WB-AR preregistration), BM-01a (Handy egress baseline), BM-02 (delivery harness) | SEL-BENCH (after D0G-1; it does not wait for design) opens BM-00; the rest by readiness record under the benchmark spec. That spec also issues the records for BM-01b and BM-03, which the plan schedules inside product stages. |

### S5: WisprSide
**SEL-SIDE opens `SD-M2`.** Later Grains open by readiness record under the WisprSide spec.

**To R1 internal alpha:**
- SD-M2 exec surfaces;
- SD-M11 retention;
- SD-M12 catalog licence gate;
- SD-M1 egress lockdown (after BM-01a);
- SD-M9 Windows CI;
- SD-M3, SD-M4, SD-M5, SD-M6 target-bound delivery;
- SD-M8 cancellation;
- DS-05 kit in the fork;
- SD-M10 identifiers and updater.

Speech engines are labelled unranked under the GP-02S R1-only condition. The R1 gates are in `WISPRAL_RELEASE_QUALITY.md` §2 and §3.1.

**To R2 and R3:**
- Features: SD-R1, SD-R2, SD-R3, SD-R4, SD-R6, SD-R7, SD-R8.
- Speech evidence: BM-03, then SE-01, then SD-R9, under public-subset Arabic claims only.
- Release: SD-R10 installer and DLL closure, PF-01 signing.
- **Accepted 000B evidence before R3.**

### S6: Klaint text
- **Entry:** the foundation (SEL-BENCH), KT-01b VERIFIED and PA-SET-KLAINT. Then **SEL-KLAINT opens `KT-03`**. It does not wait for WisprSide.
- **To R1:**
  - KT-03 broker and ledger: capability per call, separate process, BLOCK mode enforced;
  - KT-04 review-hook gate;
  - KT-05 commitment guard;
  - KT-06 cited retrieval;
  - KT-07 Chatwoot bridge;
  - KT-08 tau2-bench harness;
  - KT-09 topology and egress;
  - KT-10 first connector with SSRF and loopback tests;
  - KT-02 multi-tenant host with per-tenant containers;
  - DS-08 console;
  - KT-HQA.

### S7: WisprStudio
- **Entry:** the foundation (SEL-BENCH), ST-D00r VERIFIED, 000F-W recorded, FD-08, FD-10, FD-15 and FD-17 decided, and PA-SET-STUDIO. Then **SEL-STUDIO opens `ST-D12`** (Windows suite repair). It does not wait for WisprSide or Klaint.
- **To R1:**
  - BM-01b VoiceStudio egress baseline;
  - ST-D01 strip egress, pin runtime bundles, local-only test;
  - ST-D08 offline staging;
  - ST-D02 permissive default engine;
  - ST-D09 marking;
  - ST-D03 consent ledger;
  - ST-D04 fit guard;
  - ST-D05 cancellation;
  - ST-D06 only if ST-D02 rejects the built-in Arabic engines;
  - ST-D07 Arabic lexicon;
  - ST-D13 crash-safe resume;
  - ST-D14 migration and dubbing provenance;
  - ST-D11 identifiers, updater and signing;
  - DS-07 tokens and RTL.

### S8: Expansion (coarse, by priority)

1. Authority failures found in R1/R2.
2. The first reliable end-to-end workflow per product.
3. Recovery and install.
4. Held-out Arabic and Gulf evaluation, through BM-04.
5. Measured speed.

Packets kept coarse:
- AG-00, CORE-R1, then A-01 (agent control);
- BM-05 (co-running);
- PF-02 (macOS and Linux);
- CORE-08 (local-API auth);
- KV-01 and KV-02 (Klaint voice, after RG-5);
- ST-D10 and PL-SDK (SDKs);
- cross-device and mobile input.

### Packets not placed in a roadmap group

These have a stated disposition instead:
- **Merged or done (P0):** G1, C1, PLAN, A040, C2, R, NOOP, G2, F.
- **VERIFIED:** CORE-00, ST-D00b.
- **SD-M0:** VERIFYING, then VERIFIED through GP-13.
- **ST-D00:** BLOCKED, remediated by ST-D00r.
- **KT-01:** BLOCKED, item 3 superseded by KT-01b.
- **D0G:** amended, executed as D0G-1.
- **Retired:** D1G and BM-01.
- **Out of scope:** B2-R17, which the B2 lane governs.

The full table is in the register.

## 12. Critical path and parallelism

**Recommended sequence** (the graph allows more parallelism than this):

`S0` → GP-07 → AM-1 → GP-01, GP-02, GP-03, GP-11, GP-13, GP-14C → GP-04, GP-08, ADR-0003 → GP-05, GP-09 → PA-SET-CORE → **D0G-1 (`CORE-01`)** → CORE-02 → CORE-07 → SEL-DESIGN (DS-01 → DS-KIT) → SEL-BENCH (BM-00 → BM-01a → BM-02) → SEL-SIDE (after GP-02S and PA-SET-SIDE) (SD-M2 … SD-M6, DS-05, SD-M10) → **WisprSide R1**.

**In parallel:**
- KT-01b, ST-D00r, 000F-W and 000F closure, once GP-11 opens them;
- AM-2, GP-10 and GP-12.

**Klaint** can be selected as soon as the foundation is done and KT-01b is VERIFIED. **WisprStudio** can be selected once ST-D00r and 000F-W are done. Neither waits for another product.

## 13. Top risks after this plan

| Risk | Mitigation |
| --- | --- |
| The qualifying-review route stalls | FD-14 and AM-2 name a standing route and a fallback; until then, reviewers are named per PR |
| HW-A capacity slows Windows gates | FD-15; batch Windows manual gates; a clean-install VM before R2 |
| KT-01b fails in the container | Klaint stays closed. WisprSide and WisprStudio are unaffected. |
| ST-D00r cannot reach zero egress without large donor changes | WisprStudio stays closed; FD-13's alternative restarts the Studio baseline |
| No watermark passes the licence check | Required-mark exports stay refused. FD-09 is revisited with legal input. |
| 000B evidence never arrives | WisprSide stays at R1/R2 with unranked engines and no accuracy claims |

## 14. Validation

- **`check_plan_graph.py`: PASS** on this head.
  - 121 findings, each resolved by an existing vehicle.
  - 72 vehicles with no cycle and no dependency on a later stage. Each has an execution status: 3 DONE (with evidence), 19 APPROVED, 49 PLANNED and 1 coarse direction.
  - No product's selection depends on another product's selection.
  - 6 selections, each opening exactly one Grain.
  - Every one of the 75 packets is placed (57) or has a disposition (18); 12 new and 2 research packets are declared.
  - Under the simulated amendments:
    - every roadmap packet's dependencies come earlier, including order inside each group;
    - every selected Grain's dependencies are ready before its group;
    - no stage is gated by `ST-D00` or `KT-01`;
    - nothing blocked, retired or out of scope is assumed available.
- **Mutation tests**, run on a scratch copy: the checker caught all 17 deliberate breakages:
  - a two-Grain selection;
  - an unknown replacement target;
  - a no-op replacement;
  - a packet placed before its dependency;
  - a dropped packet;
  - a blocked dependency in S8;
  - a new packet without dependencies;
  - a selected Grain whose dependency is not ready;
  - a vehicle cycle;
  - an unresolved finding;
  - wrong order inside a group;
  - a blocked or retired packet assumed available;
  - product selections chained together;
  - a DONE status without evidence;
  - a missing status;
  - a review note with an unknown target.

  A round-3 reviewer separately ran 33 mutations.
- **`validate_plan.mjs` on the current `packets.json`: PASS.** It is rerun on each regeneration.
- **Independent reviews** are recorded on PR #155 with reviewer, instructions, head and verdict.
  - Rounds 1 to 3 ran on heads `5640016`, `ba44fcb` and `24bd345`. Three fresh-context reviewers approved `24bd345`.
  - The frozen version reconciles the plan with current `main`, records the approved decisions and execution status, and applies the round-3 non-blocking notes (listed in the register as RN-01 to RN-13). The same three reviewers' confirmations of the frozen head are recorded on the PR, as review comments posted after the head they cover.
  - **The different-vendor (Nemotron) review was waived by the founder for this planning PR; it was not completed on the final heads.** That waiver does not extend to any later vehicle that requires a qualifying review.

## 15. Superseded material and PR dispositions

- **Superseded for sequencing:**
  - [`WISPRAL_WORLD_CLASS_MASTER_PLAN.md`](WISPRAL_WORLD_CLASS_MASTER_PLAN.md) §1.7 and §8;
  - [`WISPRAL_ENGINEERING_ROADMAP.md`](WISPRAL_ENGINEERING_ROADMAP.md) §3.

  GP-07 (#156) added superseded notes to each.
- **Marked superseded by GP-07:** V3 ([`WISPRAL_MASTER_PLAN_REBUILT.md`](WISPRAL_MASTER_PLAN_REBUILT.md), the copy-first work packets) and the architecture replan, including their stale fit-overlap and Parlant text.
- **#124:** closed as carried (FD-19, done), after GP-07 imported its two review files.
- **#127:** closed as superseded by Constitution 1.0.0 (FD-19, done).
- **#73:** closed after salvage (FD-19, done):
  - donor-qualification gates went into the risk register (R-30 to R-32), and go into GP-03 when it lands;
  - input-capture patterns go into PA-07 (planned);
  - adoption rules went into the copy-first strategy (rules 6 to 14).

## 16. What this plan does not do

- It writes no product code, starts no product build, and does not execute or decide D0G.
- It does not amend the Constitution, Specification 000, the 000E/000F specs, the security architecture, any ADR or `packets.json`. It names those changes, and each lands through its own reviewed PR.
- It does not change the frozen B2 experiment (ATTEMPT-003, B2R17).
- It requests no private legal document and gives no legal advice.
- It publishes, signs, distributes and spends nothing.
