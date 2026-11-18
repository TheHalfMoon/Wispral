# ARCHITECTURE_RECONCILIATION.md

**Purpose:** reconcile the REA's proposed Klaint architecture with Wispral's canonical, ratified planning baseline; label the REA's deviations as unratified proposals; resolve the "plugin tool server off" contradiction; and fix evidence language that overreached.

**Date:** 2026-11-18
**Benchmark pin inspected:** `TheHalfMoon/Wispral@689a4e421d6f8acebedf15df1d2dfca0c905a835`
**Parlant pins:** canonical `emcie-co/parlant@2a463ccd10eaf0d70d42731705f4f00ef066bee8` (v4.0.2, Wispral's pin); independently inspected `4962e62bcd988ff65c1e41c4cc4ade7338efe0dd` (v4.0.6)
**Status of this document:** research reconciliation only. No product repository was modified.

---

## 0. Bottom line

| Question | Answer |
|---|---|
| Is the Rust broker/ledger in the REA reports an adopted Klaint design? | **No.** It is an unratified alternative. |
| What does the canonical plan specify? | **One hardened Python Parlant process**, a **Python broker package** (BN-02, ~800-1,500 LOC estimate) that is the sole executor, and a **ledger implemented as a database table**. Rust `wispral-policy`/`wispral-journal` crates are **deferred until a second Rust consumer exists**. |
| Do the two agree on anything important? | **Yes, on the security shape:** broker in a **separate process from Parlant**, capability on every tool call, bound to the reviewed proposal, BLOCK mode where the message gate is required, per-tenant container with a distinct UID. This part is canonical and the REA should have said so. |
| What must happen before anyone builds the Rust variant? | A ratified ADR/decision-ledger amendment with evidence, per Constitution X and the master plan's GP-10/FD-20 lane. Until then it is a proposal, not a plan. |
| Can the Parlant tool server simply be switched off? | **No evidence supports that, and both the spike and the master plan say the opposite.** The legacy strategy's "off" wording is superseded. Assume the server is reachable. |
| May Klaint process real customer data yet? | **No.** Not until the gated capability/isolation tests pass (KT-01b probes and the BLOCK-mode requirements). |

---

## 1. Canonical sources, with anchors

All paths are relative to `sources/wispral/` at the pin above.

| ID | Source | Anchor | What it says | Status |
|---|---|---|---|---|
| C-1 | `docs/strategy/WISPRAL_COPY_FIRST_STRATEGY.md` | `:50-54` | Klaint wraps Parlant v4.0.2 `2a463ccd`; "Build new: the deterministic tool broker **with its Python policy module** … and outcome ledger"; "The MVP is **one hardened Parlant process** (production mode, loopback only, dashboard and plugin tool server off)". | Ratified strategy text, **partly superseded** (see §3) |
| C-2 | same | `:56-58` | "**Contracts first, crates later.**" Rust `wispral-policy` and `wispral-journal` "are deferred until a second Rust consumer exists (A-01); Klaint's policy lives in its **Python broker** and its ledger is a **database table** with the same state table." | Canonical language boundary |
| C-3 | same | `:71` (BN-02) | Broker deliverable is "One Python package inside the Klaint service", "~800-1,500 LOC plus adversarial fixture suites (estimate)". | Canonical scope estimate |
| C-4 | `docs/strategy/WISPRAL_PRODUCT_ARCHITECTURE.md` | `:120,150` | MVP: one hardened Parlant process, "plugin tool server off", broker as sole executor with a per-call token bound to the session; review note: "the plugin server trusts caller-supplied customer ids". | Ratified architecture, **"off" wording superseded** |
| C-5 | `docs/strategy/WISPRAL_WORLD_CLASS_MASTER_PLAN.md` | `:77` | Same MVP statement; multi-tenancy is tier S. | Ratified, **"off" wording superseded** |
| C-6 | `research/klaint-spike/README.md` | `:5-7,59-73,84-92` | KT-01 **NOT VERIFIED**: forged `customer_id` accepted; "The tool server cannot be disabled"; "In both versions the spike found no setting that turns it off"; BAIL in STREAM delivers the original draft. | Primary experimental evidence |
| C-7 | `docs/strategy/WISPRAL_MASTER_PLAN_FINAL.md` | `:50` | "KT-01 … is BLOCKED. Parlant's tool server **cannot be disabled** and accepts a forged `customer_id`." | Later verified position |
| C-8 | same | `:79,203,212` | Language map: Rust owns WisprSide; Python is an **evidenced, bounded exception** for the Klaint service; "A Rust policy crate (CORE-R1) waits for a second Rust consumer"; Klaint broker is BUILD_NEW, **in a separate process from Parlant**, outside the model's reach, capabilities bound to the reviewed proposal, one stack per tenant with distinct UID. | Canonical |
| C-9 | same | `:224-231` | Security baseline: "Klaint tool server — **Assume it is reachable.** Every tool, read tools included, requires the broker-issued capability … and ignores `context.customer_id`"; issuance channel is itself a trust boundary; enumerated probes. | Canonical |
| C-10 | same | `:309` (PA-05) | KT-03 rewritten for a broker in a **separate process**; KT-02/KT-03 "plugin server disabled/off" items are **replaced** by capability-on-every-tool, authenticated issuance channel, per-tenant container/UID, KT-01b probes, BLOCK mode + per-session STREAM negative fixture. | **Explicit supersession** |
| C-11 | `research/wispral-world-class/final-plan/RESOLUTION_REGISTER.md` | `:72` (SEC-01), `:91` (SEC-20), `:66` (ARC-16), `:53` (ARC-03) | SEC-01: "tool server cannot be disabled … plans assume it is off". SEC-20: a separate-process broker's issuing channel is a **new trust boundary**. ARC-16: inside/outside placement decides what "outside the model's reach" means. ARC-03: Rust/Python policy parity is unmet while the Rust crate is deferred. | Reviewed findings |
| C-12 | `CONSTITUTION.md` | `:83-85` | "The product runtime SHOULD be Rust-first…"; "Other languages … MAY be used when evidence demonstrates a better engineering boundary."; "Language purity MUST NOT outrank product correctness, accessibility, portability, or maintainability." | Binding governance |
| C-13 | `docs/strategy/WISPRAL_MASTER_PLAN_FINAL.md` | `:3,23,159,287` | Plan is FROZEN at the approval gate; FD-01…FD-20 approved 2026-11-10; ADR-0003 is **planned, not started**; FD-20 ratifies ADR-0003; ADR-0003 requires qualifying review. | Status of the Rust/Python decision record |
| C-14 | `docs/canonical/ARCHITECTURE_INVARIANTS.md` | `:8-139` (A1-A15) | Event-driven control plane; cancellable execution; provenance; protocol-first integration; replaceable speech; bounded context; A9 fail-closed; A10 local-first ≠ local-only; **A11 Rust owns concurrency and policy boundaries**; per-surface qualification. | Binding invariants |
| C-15 | `docs/engineering/WISPRAL_SECURITY_ARCHITECTURE.md` | `:114` (KL-T3) | Broker-issued, Ed25519-signed, session/tool/argument-bound, 60-second, single-use capability; plugin tool server **"disabled in every Klaint process" as design intent**; peer credentials identify a process, not a customer. | Binding security design; **"disabled" clause superseded** (see §3) |

**Note on C-13:** ADR-0003 is the record that would fix the architecture, and it is approved *in direction* (FD-20) but **its text is not in `docs/adr/`** — only ADR-0001 and ADR-0002 exist. Until ADR-0003 is written and ratified, §5 of the master plan is the best canonical statement of the intended shape. Any REA variant must cite that, not invent a new baseline.

---

## 2. What the canonical architecture actually is

Three distinct boundaries, not one:

```
Parlant process (Python)
  engine + tools + message generation
        │  reviewed tool proposal (on_reviewing_tool_calls)
        ▼
Broker process (Python; BN-02, ~800-1500 LOC estimate)
  allowlist, argument schema, scope checks, ASK/UNDECIDABLE,
  capability issue (Ed25519, single-use, short-lived), ledger writes
        │  capability + execution
        ▼
Tool workers / connectors (Python; tier S for real connectors)
        │
        ▼
Customer systems
```

- **Broker placement:** separate process from Parlant (C-8, C-10). "Outside the model's reach" means the model cannot call a tool; it can only produce a proposal the broker reviews.
- **Ledger:** a database table with the canonical state table, inside the Klaint service (C-2), not a separate service.
- **Policy:** a Python module in the broker (C-2), not a Rust crate. Contracts are language-neutral JSON Schemas with fixtures (C-2), so a later Rust implementation is possible without redesign.
- **Rust:** deferred until a second Rust consumer exists; the only ratified Rust runtime owner is WisprSide (C-8).
- **Isolation:** one container stack per tenant, distinct UID, residents enumerated (C-8, C-9); probes must show zero data and zero effects.
- **Output safety:** BLOCK mode required wherever the message gate is required, at start-up and at run time, with a per-session STREAM negative fixture (C-10).

That design is coherent and matches the evidence. The REA's job was to describe it, not replace it.

---

## 3. The "plugin tool server off" contradiction, resolved

### 3.1 What the documents say

| Document | Text | Date/status |
|---|---|---|
| `WISPRAL_COPY_FIRST_STRATEGY.md:54` | MVP has "plugin tool server off" | earlier strategy |
| `WISPRAL_PRODUCT_ARCHITECTURE.md:120,150` | "plugin tool server off in every process" | earlier architecture |
| `WISPRAL_WORLD_CLASS_MASTER_PLAN.md:77` | "plugin tool server off" | earlier plan |
| `docs/engineering/WISPRAL_SECURITY_ARCHITECTURE.md:114` (KL-T3) | "the plugin tool server is **disabled in every Klaint process**" | binding security design, written before KT-01 |
| KT-01 spike `README.md:5-7,84-92` | "The tool server cannot be disabled"; no setting found in v4.0.2 or v3.3.2; forged `customer_id` returned data | experiment |
| `WISPRAL_MASTER_PLAN_FINAL.md:50` | "Parlant's tool server cannot be disabled" | later verified plan |
| `WISPRAL_MASTER_PLAN_FINAL.md:309` (PA-05) | KT-02/KT-03 "plugin server disabled/off" items are **replaced** by capability-on-every-tool + issuance channel + isolation + probes + BLOCK mode | later plan, explicit |

### 3.2 Resolution

**The legacy "off" statements are superseded.** They described an intended configuration that the spike could not achieve. This includes the binding security architecture's KL-T3 wording ("the plugin tool server is disabled in every Klaint process", `WISPRAL_SECURITY_ARCHITECTURE.md:114`): the *capability* requirements in KL-T3 still stand, but the *disabling* mechanism does not. The later, verified plan does not rely on disabling anything:

- It **assumes the server is reachable** (C-9).
- It requires a capability on **every** tool call, read tools included.
- It ignores `context.customer_id` entirely.
- It isolates each tenant in its own container with a distinct UID.
- It proves the result with the KT-01b probe set (C-9, C-10).

That is a stronger position than "turn it off", because it remains true if a future version re-enables the route or a configuration drifts.

### 3.3 Loopback is not a security boundary

Three reasons, all evidenced:

1. KT-01 called the server **from the same machine** and got data for a forged customer (C-6).
2. Parlant's own integrated server is started by the SDK on `127.0.0.1` (`sdk.py:4961-4990` in v4.0.6), so loopback is the *default*, not a mitigation.
3. Any local process — a connector, a console, a bridge, a compromised dependency, an SSRF from another local service — shares that loopback. SEC-20 makes the same point about peer credentials: they identify a **process**, not a customer.

**Rule for Klaint:** loopback binding is a deployment detail, never an authorization argument. The authorization argument is the capability and the tenant/UID isolation.

### 3.4 No real customer data yet

**Binding rule:** Klaint must not process real customer data until the gated capability and isolation tests pass:

- KT-01b probes (C-9): made-up session; **a valid live session of another customer of the same tenant**; another tenant; every tool-server route including `GET /tools`; loopback from a connector; **a capability request from any resident other than Parlant**.
- BLOCK mode enforced at start-up and run time, with a per-session STREAM negative fixture (C-10).
- Zero data and zero effects on every probe.

Until then: synthetic fixtures only. This applies equally to the Python canonical broker and to any Rust proposal.

---

## 4. The REA's Rust broker: an unratified proposal

### 4.1 What the REA wrote, and why it is not canonical

The REA reports state a **Rust capability broker/ledger** as a design decision (`KLAINT_TARGET_ARCHITECTURE.md` §19, `KLAINT_COMPETITIVE_ROADMAP.md` P0, `README.md` §6). That is **not** what the ratified plan says. It was derived from:

- Wispral invariant **A11** ("Rust owns concurrency and policy boundaries", C-14), and
- Constitution X's Rust-first *should* (C-12).

Both are real, but both are already addressed by the canonical exception: Klaint is Python **because Parlant is Python**, and the master plan records that as evidenced (C-8). A second Rust runtime for the same boundary has to justify itself under the same rule that produced the exception.

**Correct label in every REA document: proposal, unratified, pending ADR.**

### 4.2 Comparison

| Dimension | Canonical (ratified direction) | REA proposal (unratified) |
|---|---|---|
| Broker language | **Python package** inside the Klaint service | Rust sidecar/service |
| Process placement | **Separate process from Parlant** | Separate process from both Parlant and the orchestrator |
| Ledger | **Database table** in the service, canonical state table | Rust-owned ledger service/table |
| Policy | Python module; contracts are language-neutral JSON Schemas + fixtures | Rust policy engine implementing the same contracts |
| Capability signing | Ed25519, per KL-T3 | Same, implemented in Rust |
| Effort | **~800-1,500 LOC** + adversarial fixtures (estimate, C-3) | Not estimable without a design; adds a second implementation of the contracts, IPC, packaging, and parity CI |
| Ratification state | FD-20 approved direction; ADR-0003 text pending | **None** |
| Language-rule status | Evidenced exception (Parlant is Python) | Needs new evidence; Constitution X forbids purity over correctness |
| Parity obligation | None (single implementation; Rust deferred by A-01) | **Two implementations** must pass shared fixtures (RFC 8785/JCS, NFC, path canonicalization, digest vectors) |

### 4.3 Honest case *for* the proposal

- A separate Rust broker is a hard memory-safety and single-binary boundary; it cannot be monkey-patched by Python code loaded into the same interpreter.
- Concurrency and cancellation are stronger, matching A11's intent.
- If Klaint later ships self-hosted binaries, a static broker simplifies packaging.
- It keeps the policy boundary identical in shape to WisprSide's, which may reduce long-term cognitive load across products.

### 4.4 Honest case *against* the proposal

- It **contradicts the ratified language map** and the explicit "contracts first, crates later" decision (C-2, C-8). Adopting it requires a decision-ledger row superseding that choice, plus ADR-0003 or a successor.
- It **doubles the contract surface**: every canonicalization and digest rule must be implemented twice and proven byte-identical. ARC-03 already flags that Rust/Python policy parity is unmet while the crate is deferred; the proposal makes parity mandatory on day one.
- It adds a **new IPC boundary** and a second packaging/deployment unit before the first customer.
- It gives up the main canonical advantage: one language, one team, one stack, fastest path to the first proof.
- Constitution X line 85: language purity must not outrank correctness, portability or maintainability. A Rust broker that delays KT-01b is purity outranking correctness.

### 4.5 Additional trust boundaries the Rust proposal creates

The canonical design already has one dangerous channel: **Parlant → broker issuance** (SEC-20). The Rust proposal adds more:

| # | Boundary | Why it is dangerous | Minimum proof |
|---|---|---|---|
| B1 | Parlant → broker (issuance) | Any resident with the channel could mint a capability for a valid session | Accept only Parlant identity (distinct UID or mount-scoped socket); bind capability to the reviewed proposal; reject caller-supplied session ids; probe from console/connector/bridge must yield no capability |
| B2 | Orchestrator → broker (if separate) | Orchestrator compromise becomes authority compromise | mTLS/UID authentication, replay-resistant request ids, per-request audit, no shared static secret |
| B3 | Broker → tool workers | A worker that can call the broker directly could escalate | Workers hold no mint authority; capabilities are audience-bound to one tool; worker re-validates args |
| B4 | Cross-language canonicalization | A byte difference between Rust and Python changes a digest and silently invalidates or, worse, accepts a capability | Shared fixtures (JCS/NFC/path rules), cross-language digest vectors in CI, property-based tests |
| B5 | Broker restart/crash | Nonce ledger state can be lost or duplicated | Durable nonce table with unique constraint; idempotent recovery; test kill/restart mid-issue |
| B6 | Deployment drift | A second binary can be misconfigured or omitted, silently disabling the gate | Startup self-check refuses to serve without broker; health/attestation in the console; egress manifest |

Each of B1-B6 is a test requirement, not a design paragraph. If the proposal is ever ratified, these tests must exist **before** the first integration, not after.

### 4.6 What would make the proposal ratifiable

1. A written ADR (successor to ADR-0003 or an amendment) that names the evidence: measured broker p99, concurrency target, packaging need, or a specific Python failure mode that Rust removes.
2. A decision-ledger row (GP-10 lane) superseding the "second Rust consumer" rule for this component, explicitly.
3. A fixture-parity plan with the exact canonicalization vectors and CI gates.
4. A migration story: the Python broker ships first, the Rust broker replaces it behind the same contract without changing Parlant integration.
5. A cost estimate for the second implementation, reviewed against BN-02's ~800-1,500 LOC baseline.

Absent 1-5, the correct engineering choice is the canonical Python broker.

---

## 5. Recommendation

**Ship the canonical Python broker for P0.** It satisfies the security shape, keeps one language, and gets to the proof fastest. Treat the Rust broker as a **post-proof performance/portability decision**, revisited only with evidence.

Concretely:

- P0 broker: Python package, separate process, DB ledger, Ed25519 capability, canonical state table.
- P0 tests: KT-01b probes, BLOCK-mode enforcement, STREAM negative fixture, no-capability-for-other-residents.
- P0 non-negotiable: no real customer data until those pass.
- Rust: deferred; if pursued, via ADR + decision-ledger row + parity plan, not by editing the roadmap silently.

The REA's architecture document remains useful as a *target* description of boundaries, contracts and failure semantics. It is not a ratified plan, and its language choice must not be read as one.

---

## 6. Evidence-language corrections

### 6.1 Absence of evidence is not evidence of absence

The REA used categorical phrasing about competitors. Corrected scope:

| Original style | Corrected claim |
|---|---|
| "All three are SaaS-only" | "No public, verified self-host or on-prem option was found in the sources reviewed on 2026-11-18. A private or unlisted offering may exist." |
| "None publishes Arabic/dialect evidence" | "No public Arabic/dialect quality evidence was found in the sources reviewed. This is an evidence gap in our sources, not proof that none exists." |
| "Cannot match / cannot follow" | "No public evidence shows them doing this; whether they could is unknown." |
| "No competitor has X" | "X was not found in reviewed public sources." |

Applies to `README.md`, `REA_MASTER_REPORT.md`, `COMPETITOR_EVIDENCE_MATRIX.md`, and the roadmap's "where each is exposed" table.

### 6.2 Cryptographic comparison

The REA said the capability design is "stronger than anything any competitor documents publicly". Keep only the documented part:

> "No competitor **publicly documents** an equivalent signed, single-use, argument-bound capability. Their internal authorization mechanisms are **unknown**; this is not a claim that Klaint's design is cryptographically stronger than their implementations."

### 6.3 Claims ledger: observed vs estimate vs target

| Claim type | Examples in the REA | Correct label |
|---|---|---|
| Vendor list prices | Lorikeet $2,100/$5,100, $0.99/$1.50, $75K; Twilio $0.0085/$0.0140; Deepgram $0.0065 | **Observed** at URL + date; subject to change |
| Klaint TCO | $3,200-9,000/mo; $0.32-0.90 per resolution | **Estimate** with stated assumptions |
| Latency budgets | p95 < 2.5 s voice, < 3 s chat, barge-in < 250 ms | **Acceptance targets**, not measured results |
| Arabic thresholds | dialect delta ≤10 points | **Target**, not a result |
| Effort | P0 3-4 weeks, 12-18 EW | **Estimate range** |
| Safety | "zero unauthorized actions", "zero cross-tenant leakage" | **Test pass criteria** for Klaint; competitor values unknown |
| Competitor performance | none | **Not measured; no score assigned** |

No observed competitor result exists in this work, and none is implied.

---

## 7. Validation and test steps

All commands run from `D:\Klaint-REA-20261118`. These verify the canonical anchors and the Parlant behaviour without touching any product repository.

### 7.1 Canonical anchors

```powershell
Select-String -Path sources\wispral\docs\strategy\WISPRAL_COPY_FIRST_STRATEGY.md -Pattern "Python policy module|one hardened Parlant process|plugin tool server off|Contracts first, crates later|second Rust consumer|800-1,500"
Select-String -Path sources\wispral\docs\strategy\WISPRAL_MASTER_PLAN_FINAL.md -Pattern "cannot be disabled|separate process from Parlant|Assume it is reachable|plugin server disabled/off|ADR-0003|FD-20"
Select-String -Path sources\wispral\research\klaint-spike\README.md -Pattern "cannot be disabled|no setting that turns it off|FORGED_CUSTOMER|STREAM"
Select-String -Path sources\wispral\CONSTITUTION.md -Pattern "Rust-first|Other languages|Language purity"
```

Expected: the strings quoted in §1 and §3 appear at the cited locations. If a line moved, update the anchor rather than the claim.

### 7.2 Parlant pins

```powershell
git -C sources\parlant rev-parse HEAD          # expected 4962e62bcd988ff65c1e41c4cc4ade7338efe0dd (v4.0.6)
Select-String -Path sources\parlant\src\parlant\core\services\tools\plugins.py -Pattern '/tools/\{name\}/calls|class CallToolRequest|customer_id'
Select-String -Path sources\parlant\src\parlant\sdk.py -Pattern 'tool_service_port|PluginServer|127.0.0.1'
Select-String -Path sources\parlant\src\parlant\core\engines\compass\loop\base_loop.py -Pattern 'observational|_should_buffer_message_for_review|_maybe_review_message'
```

Expected: route at `plugins.py:851`; caller-supplied identity at `:607-612`; loopback server at `sdk.py:4961-4990`; observational hook at `base_loop.py:2229-2244`; buffering reviewer at `:2140-2144`.

### 7.3 Behavioural gates (Klaint, once implemented)

| Gate | Test | Pass criterion |
|---|---|---|
| G-B1 | Made-up session → tool route | Zero data, zero effects |
| G-B2 | Valid live session of **another customer, same tenant** | Zero data, zero effects |
| G-B3 | Another tenant's identifiers | Zero data, zero effects |
| G-B4 | Every tool-server route including `GET /tools` | No capability, no data |
| G-B5 | Loopback call from a connector | Denied |
| G-B6 | Capability request from console/connector/bridge | No capability issued |
| G-B7 | BLOCK mode at start-up and after a run-time change | Gate applies; STREAM negative fixture shows original draft suppressed |
| G-B8 | Capability replay / arg substitution / expiry | Denied and logged |
| G-B9 | (Rust proposal only) cross-language digest parity | Byte-identical on shared vectors |

**Real customer data is prohibited until G-B1…G-B7 pass on the target Linux container stack in production `AuthConfig`.**

### 7.4 Supplemental Lorikeet artifacts (2026-11-18)

```powershell
tar -tzf sources\lorikeet-mcp-server\lorikeetai-mcp-server-1.0.0.tgz   # 2 files only, no dist/
Select-String -Path sources\lorikeet-mcp-server\extracted\package\package.json -Pattern 'license|bin'
tar -tzf sources\lorikeet-web-sdk\lorikeetai-web-sdk-1.13.0.tgz        # dist/ only, no LICENSE
Select-String -Path sources\lorikeet-web-sdk\extracted\package\README.md -Pattern 'hosted iframe'
git -C sources\lorikeet-nestjs-temporal rev-parse HEAD                 # da2f975...
```

Expected: no licence in the MCP server or web SDK; `bin` points at a `dist/index.js` that is not shipped; one host literal, `https://chat.lorikeetcx.ai`. These are **API-surface** facts, not backend insight. Full inventory: `SOURCE_CODE_INVENTORY.md` §2.5.

---

## 8. Changes made to the REA documents

| File | Change |
|---|---|
| `README.md` | Added a canonical-vs-proposal note; softened competitor absolutes; marked prices as observed and TCO/latency/Arabic numbers as estimates/targets; cross-reference to this file |
| `REA_MASTER_REPORT.md` | Added reconciliation pointer and §2.4 status note; softened self-host/dialect claims; corrected the cryptographic comparison; labelled estimates vs observed |
| `KLAINT_TARGET_ARCHITECTURE.md` | Status banner: canonical baseline is Python broker (BN-02) + DB ledger, Rust is a proposal; §19 decision table updated; §7.3 and §9.4 labelled as targets; link to this file |
| `KLAINT_COMPETITIVE_ROADMAP.md` | P0 language corrected to canonical Python broker with Rust deferred; effort and latency marked estimates/targets; competitor exposure softened |
| `COMPETITOR_EVIDENCE_MATRIX.md` | Self-host, dialect and "cannot match" cells rewritten as "not found in reviewed public sources"; Lorikeet MCP row qualified (package ships no code); supplemental-archive note added |
| `SOURCE_CODE_INVENTORY.md` | §2.5 added for four supplemental Lorikeet archives with pins, licences, actual contents and limits; master inventory rows E-LOR-06…09; MCP claim corrected; contradiction log C8–C12; reuse rules for unlicensed packages |
| `REPRODUCE.md` | §3.3 added: fetch/list commands and expected file sets for the supplemental archives |
| `ARCHITECTURE_RECONCILIATION.md` | This document |
| `progress.txt` | Stage 5 and Stage 6 entries recording the conflict, resolution and edits |

---

## 9. Open items

| # | Item | Owner | Needed before |
|---|---|---|---|
| R1 | Write ADR-0003 text (already FD-20 approved in direction) | Architecture | Any Klaint implementation PR |
| R2 | Decide Python broker vs Rust proposal with evidence | Founder/architecture | P0 start |
| R3 | Freeze the KT-01b probe list as an executable suite | Security | Any real data |
| R4 | Confirm BLOCK-mode policy per agent and the STREAM negative fixture | Security | Customer-facing GA |
| R5 | Update legacy "plugin server off" wording in strategy docs to the superseded form | Docs | Next docs PR (not done here — research-only) |
