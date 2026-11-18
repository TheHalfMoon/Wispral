# REA_MASTER_REPORT.md

**Deep Reverse-Engineering & Architecture Analysis**
**Benchmark product:** Klaint (TheHalfMoon/Wispral)
**Competitors:** Lorikeet CX · Decagon · Parloa
**Date:** 2026-11-18
**Author:** autonomous research agent (OpenCode), on a Windows workstation
**Companion files:** `SOURCE_CODE_INVENTORY.md`, `COMPETITOR_EVIDENCE_MATRIX.md`, `KLAINT_TARGET_ARCHITECTURE.md`, `KLAINT_COMPETITIVE_ROADMAP.md`, `ARCHITECTURE_RECONCILIATION.md`, `ACCESS_GAPS.md`, `REPRODUCE.md`, `README.md` (Arabic), `progress.txt`

Evidence labels used throughout:

| Label | Meaning |
|---|---|
| **SOURCE-VERIFIED** | read in code at a pinned commit; file + line cited |
| **DOCS-VERIFIED** | read in official documentation at a URL on a stated date |
| **OBSERVED** | seen in a public artifact (package, page, bundle) without backend access |
| **MARKETING-INFERRED** | vendor claim, not independently verified |
| **UNKNOWN** | not accessible or not measured |

---

## 1. The answer, in one page

**Can Klaint compete with Lorikeet, Decagon, and Parloa?**

**Not today, and not on their terms.** Klaint is a specification with no product code: Wispral's own canonical status file says *"Active product implementation: none"* and *"product Rust/Cargo implementation added: no"* (`sources/wispral/docs/canonical/CURRENT_STATE.md:33-34,105`). The three competitors are shipping multi-channel enterprise products with public customer stories, published pricing or enterprise sales, and certification claims - and, in Parloa's case, a brand-new MCP control plane. A feature-for-feature race is very unlikely to be winnable in year one and would be strategically wrong.

**Can Klaint beat them somewhere specific?**

**Yes, in three defensible wedges, and only if it ships correctness before features:**

1. **Arabic-first support and voice.** Not one of the three publishes any Arabic, Gulf, Levantine, Egyptian, or Arabizi quality evidence. Decagon claims 70+ languages, Parloa claims 140+ variants, Lorikeet states no number — all unverifiable for dialects. Meanwhile the standard tool-agent benchmark, τ-bench 2.0, ships six languages and **no Arabic pack** (`sources/tau2-bench/README.md:23-24`). Klaint can own the benchmark, the evaluation suite, and the UX, and publish raw results including failures. This is the strongest and most durable opening.

2. **Provable action authority.** Klaint's specified design - an Ed25519-signed, single-use, session/argument-bound capability verified by a broker (KL-T3) - has **no publicly documented equivalent** among the three. Their internal authorization mechanisms are unknown, so this is **not** a claim that Klaint's design is cryptographically stronger than their implementations; it is a claim that Klaint can prove its own. Critically, the founding defect that motivates it is **still live in Parlant 4.0.6**: the HTTP plugin tool server accepts `customer_id` from the caller (`core/services/tools/plugins.py:607-612,851`). Klaint can ship a public forgery/replay/tenant-leak test suite. No such public suite was found for any competitor.

3. **True self-host / air-gap with a declared egress manifest.** No public on-prem or self-host option was found for any of the three in the sources reviewed on 2026-11-18; if a private offering exists, it was not visible to us. Regulated buyers who cannot use SaaS - government, healthcare, defence, some EU public sector and banks - are therefore underserved by what is publicly on offer. Adding self-host would strain a SaaS business model, but it is a **narrower** market than the total CX market, and Klaint must price for it honestly.

**Where Klaint cannot win and should not try:** generic English model quality (everyone can rent the same frontier models), feature breadth (Decagon and Parloa have years of integrations), outcome-based pricing at low volume (Lorikeet's $0.99 per chat resolution is hard to undercut with a small team), enterprise brand trust in the first year, and global telephony footprint without carrier partners.

**The single most important engineering sentence in this report:** the broker, the ledger, the output gate, and tenancy are worthless if retrofitted. Build them in P0, gate the release on them, and only then add channels. A "secure agent" shipped in month three without them is a liability with a demo.

---

## 2. Scope, method, and what "depth" meant here

### 2.1 What was actually examined

| Target | What we could obtain | What we could not |
|---|---|---|
| **Klaint / Wispral** | Full public repo at `689a4e421d6f8acebedf15df1d2dfca0c905a835`: canonical status, invariants A1-A15, security architecture KL-T1..KL-T11, KT-01 spike results, governance docs | Product code — there is none |
| **Lorikeet** | Official GitHub org `optechai`: Stainless-generated node SDK (Apache-2.0), mock-api reference, MIT React Native SDK, generic Temporal library (MIT), MCP server package (**no code shipped, no licence**), demo MCP client (ISC), widget loader SDK (**no licence**); public docs, `llms.txt`, `AGENTS.md`, MCP catalog, full pricing page | Backend, planner, guardrail models, tenancy internals, latency |
| **Parloa** | Official Apache-2.0 Python SDK at `873c3f437a373b1be77091aeb75786aa6dc36e02` with generated client + rich type semantics; public product pages, security page, pricing page, integrations, 2026-11-02 Agent Management blog; public GitBook landing page | AMP Studio docs (whitelisted login), runtime traces, actual determinism, rate card |
| **Decagon** | One distributable: `@decagon-ai/duet-cli` 0.6.1 — **proprietary**, analysis only; product pages (Voice, AOP, Testing/QA), security page, four official engineering/marketing blogs including Missions (2026-11-12) | Developer docs (login), API (403), console, pricing |
| **Donors** | Parlant 4.0.6, Pipecat, τ-bench 2.0, Standard Webhooks, Rasa 3.6.21, Chatwoot 4.20.0 — all cloned and pinned | — |

Exact pins, licences and reuse conditions are in `SOURCE_CODE_INVENTORY.md`; every blocked item is in `ACCESS_GAPS.md`.

### 2.2 The rule that shaped the whole report

A generated SDK is an **API contract**, not an implementation. It tells you what endpoints exist and what shapes they exchange. It does not tell you how the server enforces identity, what the planner does, or how fast anything is. So every competitor cell is labelled with what kind of evidence supports it, and any claim that would require backend access is marked `claim` or `UNK`.

Two consequences the reader should hold onto:

- **No competitor score appears anywhere in this work.** No latency number, accuracy percentage, or league table. Inventing one would have been easy and would have destroyed the value of the whole exercise.
- **"Klaint has X" is always split three ways:** *specified* (in Wispral docs), *donor-inherited* (would come from Parlant/Pipecat/etc.), or *missing*. There is no third category of "already working".

### 2.3 A correction made during this mission

An earlier pass of this work concluded that Parlant 4.0.6 had removed the HTTP plugin tool server that KT-01 exploited. **That was wrong, and it is retracted.** Re-checking the pinned 4.0.6 tree:

- `@app.post("/tools/{name}/calls")` still exists — `src/parlant/core/services/tools/plugins.py:851`.
- `CallToolRequest` still carries `agent_id`, `session_id`, `customer_id`, `arguments` from the caller — `plugins.py:607-612`.
- The SDK starts an integrated `PluginServer` on `127.0.0.1`, default port `8818` — `sdk.py:3065,4961-4990`.
- The standalone server defaults to `host="0.0.0.0", port=8089` — `plugins.py:642-643`.

So KT-01's identity finding is **not fixed upstream**; only its exposure narrows (loopback by default in SDK mode). The stream-mode hook limitation is also unchanged (`loop/base_loop.py:2229-2244`). What 4.0.6 *adds* is a buffering reviewer path (`:2140-2144`, `:2160-2227`) that a Klaint gate could use — a genuine improvement, not a removal.

This is recorded in `SOURCE_CODE_INVENTORY.md` §5.1 and C1, and the verification command is in `REPRODUCE.md` §5.4. It matters because it changes the recommendation: upgrading Parlant does **not** discharge the binding acceptance gate.

### 2.4 Status of the architecture described here (read before §8)

The architecture in `KLAINT_TARGET_ARCHITECTURE.md` and summarised in §8 is a **target design**, not a ratified Klaint plan. Wispral's canonical baseline is narrower and explicit: **one hardened Python Parlant process; a Python broker package (BN-02, ~800-1,500 LOC estimate) in a separate process as the sole executor; a ledger implemented as a database table; Rust `wispral-policy`/`wispral-journal` deferred until a second Rust consumer exists** (`sources/wispral/docs/strategy/WISPRAL_COPY_FIRST_STRATEGY.md:50-58,71`; `WISPRAL_MASTER_PLAN_FINAL.md:212,309`; ADR-0003 approved in direction by FD-20 but not yet written).

Where this report's earlier drafts specified a Rust broker at P0, that was an **unratified alternative**. `ARCHITECTURE_RECONCILIATION.md` compares the two, lists the extra trust boundaries the Rust variant creates, and states what evidence would be needed to ratify it. The security *shape* - broker outside the model's reach, capability on every tool call, BLOCK mode where the message gate applies, per-tenant container and UID - is canonical and is shared by both.

Two related corrections carried through the whole report:

- **The legacy "plugin tool server off" requirement is superseded.** KT-01 found no setting that disables it, and the later plan says so (`WISPRAL_MASTER_PLAN_FINAL.md:50`). The plan now assumes the server is reachable and defends every tool call instead (`:224-231`, `:309`). Loopback is **not** treated as a security boundary.
- **No real customer data until the gated tests pass** (KT-01b probes, BLOCK-mode enforcement, per-session STREAM negative fixture).

---

## 3. Klaint today: a specification, audited honestly

### 3.1 Status

| Fact | Evidence |
|---|---|
| Program status `SPEC_000_RESEARCH_ACTIVE` | `CURRENT_STATE.md:33` |
| Active product implementation: **none** | `CURRENT_STATE.md:34` |
| Product Rust/Cargo implementation added: **no** | `CURRENT_STATE.md:105` |
| Published release: **none** | `CURRENT_STATE.md` |
| KT-01 spike: **NOT VERIFIED** | `research/klaint-spike/README.md:5-7` |

### 3.2 What is genuinely strong (specified)

Wispral's architecture documents are better than most funded startups'. Specifically:

- **Fifteen invariants (A1-A15)** that read like hard constraints, not aspirations: event-driven control plane; independently cancellable audio and agent execution; provenance preserved across interpretation; protocol-first agent integration; adapters do not own product policy; replaceable speech engines; bounded, inspectable context; **high-risk authorization fails closed**; local-first ≠ local-only; Rust owns concurrency and policy boundaries; per-surface qualification; push-to-talk as reliability baseline; accessibility independent of voice; benchmark instrumentation as architecture (`docs/canonical/ARCHITECTURE_INVARIANTS.md:8-139`).
- **A threat model (KL-T1..KL-T11)** with named threats and, unusually, a specific remedy: a broker-issued, Ed25519-signed, session/tool/argument-bound, 60-second, single-use **capability** (`docs/engineering/WISPRAL_SECURITY_ARCHITECTURE.md`, KL-T3 around line 114).
- **A spike that failed correctly.** KT-01 found that a forged `customer_id` reached an integrated Parlant tool server and returned data, and that a BAIL in `on_message_generated` cannot suppress streamed output. The repo records this as a failure rather than a footnote. That is the behaviour of an engineering culture worth backing.

### 3.3 What is missing (everything executable)

No orchestrator, no broker binary, no ledger, no gate, no voice pipeline, no channel adapters, no console, no retrieval, no evaluation harness in production form, no tenancy implementation, no deployment packaging. The research harnesses and fixtures exist; the product does not.

**Implication for this report:** competitive claims about Klaint must be phrased as *"Klaint's design specifies X; it is unbuilt"*. Any framing that implies parity today is false.

---

## 4. Competitor profiles, evidence-led

### 4.1 Lorikeet CX (legal trail: OpTech AI → `optechai`)

**What it is.** AI customer support for "complex and regulated businesses" — Concierge (the agent), Coach (forward-deployed configuration), Dreamweaver (per-customer account manager), Quality (automated QA). Chat, email, voice, SMS, SDK, MCP, B2A.

**What is genuinely open (and unusually so).**

- `optechai/node-sdk`, Apache-2.0, Stainless-generated, pinned `4bdaf93962d039938c2ef8526e6c55f41c40b1c7`.
- `optechai/mock-api`, a reference ingest server with the async contract documented in its README.
- `@lorikeetai/react-native-sdk` 3.0.0, MIT, UI wrapper.
- Four supplemental archives verified 2026-11-18 (inventory §2.5): `optechai/nestjs-temporal` (MIT, but a generic third-party library, not proven production code); `@lorikeetai/mcp-server` 1.0.0 (**README + package.json only - no implementation, no licence**); `@lorikeetai/mcp-client` 1.0.0 (ISC, a 28-line demo); `@lorikeetai/web-sdk` 1.13.0 (**no licence**, bundled widget loader for a hosted iframe).
- A public `llms.txt` that indexes every agent-facing surface, plus `AGENTS.md`, an AI catalog, and an OpenAPI description of the demo-booking API.

None of the supplemental archives is backend code, and two carry no licence, so they are analysis-only. They add API-surface and packaging evidence, not runtime insight.

**As-built API surface (selected, SOURCE-VERIFIED):**

| Capability | Evidence |
|---|---|
| Create chat ticket / send / poll | `/v1/conversation/chat/{create,message}` — `chat.ts:26,38,51` |
| SSE stream per conversation | `chat.ts:115` (`/v1/ticket/sse/{conversationId}`) |
| Draft-then-send lifecycle | status union includes `DraftResponse`, `Responded`, `Escalated`, `EscalatedFailed`, `Error` — `chat.ts:207-211` |
| Web voice via **LiveKit** | `/v1/conversation/voice/web/create` returns `wsUrl` + `token` — `voice/web.ts:12-13,24,35-42` |
| Customer identity token | `/v1/customer/token` — `customer.ts:65`; consent `customer.ts:88` |
| Async tool completion | `/ingest/{toolId}/{ticketId}/{inputHash}/{workflowId}` — `ingest.ts:15`; test `:23`; validate `:31` |
| Webhook signing | HMAC-SHA256 over raw payload, base64 → base64url — `src/lib/generate-signature.ts:8-18` |

The mock-api README documents the operational contract: respond `200` immediately, or `202` and answer within **10 seconds for chat / 10 minutes for email**, with `x-optech-signature` on the callback (`sources/lorikeet-mock-api/README.md:38,53-54`).

**Claims worth taking seriously (MARKETING-INFERRED, but specific):**

- Two-tier guardrails: deterministic boundaries in code (customer isolation, server-side identity validation, workflow-scoped tool access, execution caps) plus up to 10 agent guardrails and 10 message checks per concierge; grounding guardrail always on; two retries then escalate (`product-guardrails.txt:31-39,56-57,76-77`).
- Simulations: real tickets → scenarios, synthetic customers, **mocked tools**, batch diffs, adversarial suites — and published limits: cannot test a single skill in isolation, and repeated calls to one mocked tool cannot branch (`product-simulations.txt:18-22,78-79`).
- An explicit refusal to claim prompt-injection immunity: *"Any vendor claiming immunity … is either uninformed or dishonest."*

**Pricing (DOCS-VERIFIED, `pricing.md:12,32-40,57-62,76,163`):** Start $2,100/mo annual, Scale $5,100/mo annual, Signature custom with a **$75K platform fee**; per-resolution $0.99 chat/email/SMS and $1.50 voice (Start), $0.90/$1.20 (Scale), $0.30 triage/QA; voice priced on a 3-minute average; escalations not charged.

**Honest assessment.** Lorikeet is the most *epistemically* trustworthy of the three in public: it publishes limits, prices, and a refusal to overclaim. Its API is the cleanest public contract. Its weakness from Klaint's perspective is that it gives away no backend insight at all, and its own simulations cannot isolate a skill or branch a mock — a real gap Klaint can beat.

### 4.2 Decagon

**What it is.** Enterprise AI concierge for CX: chat, email, voice (Voice 3 on an in-house **Chord** speech model), AOP authoring, Duet (agent-building copilot), Experiments, Testing & QA, Watchtower (always-on QA), Insights, and — as of 2026-11-12 — **Missions** for long-horizon, multi-touchpoint outcomes.

**What is actually available.** Far less than the marketing suggests:

- **No GitHub organisation** (`decagonai` → 404), **no PyPI package** (`decagon` → 404).
- **One distributable:** `@decagon-ai/duet-cli` 0.6.1 — a public npm package under a **restrictive commercial licence**, not open source. Its `LICENSE` is "Decagon - Duet CLI License", © Decagon AI, Inc. 2026, permitting use/copy/distribution solely to use or connect to the Decagon Platform under an executed agreement (`package/LICENSE:1-30`). It requires an approved account.
- **Developer docs are login-gated.** `docs.decagon.ai` returns an auth shell (31,769 B HTML → **0 B** extractable text); `api.decagon.ai` root returns **403**.

**What the bundle reveals (OBSERVED, static analysis only).** Regional API hosts `api.decagon.ai`, `eu.api.decagon.ai`, `au.api.decagon.ai` (`dist/bin.mjs:213-215`); device-code login `POST /deca_agent/cli/device_codes` (`:1324`); token mint `POST /deca_agent/cli/tokens` (`:605`); team selection `POST /deca_agent/cli/teams` (`:1282`); chat completion `POST /deca_agent/chat/completion` (`:1023`); cancel (`:1039`); config (`:1060`); file upload (`:488`); conversation (`:1001`); signature settings (`:1116`). The installed agent skill describes access to "THIS team's AOPs, tools, conversations, analytics, and knowledge" (bundle line 28).

That is a control-plane shape: multi-region, device-code SSO, team-scoped tokens, conversational authoring, streaming with cancel. It is **not** the agent engine.

**Claims (MARKETING / VENDOR-ENGINEERING):**

- AOPs: natural language that *"compile[s] into validated workflows"*, Git-based versioning, reasoning traces with runtime/latency, guardrails across chat/voice/email; Duet generates AOPs from transcripts (`product-aop.txt:82-118`; `blog-sops-to-aop.txt:98-103,113,163`).
- Evaluation: models from OpenAI/Anthropic/Gemini plus fine-tuned open and commercial models; offline LLM-as-judge on (query, context, response) with human-labelled ground truth; live A/B with gradual rollout and opt-out; tracks CSAT, resolution, drift (`blog-evaluation-engine.txt:96-122`).
- Security: RBAC, SSO (Okta/Entra), just-in-time short-lived JWT tokens scoped to least privilege, voice authentication, AES-256 / TLS 1.2+, zero data retention with LLM providers, PII redaction via Google DLP, supervisor model revising hallucinations, audit logs; SOC 2 II, GDPR, CCPA, HIPAA, EU AI Act, ISO 27001 (page typo "2002"), PCI DSS 4.0.1 (`security.txt:84-119`).
- Missions: long-horizon, multi-persona, multi-channel, days-to-weeks; Mission case + Memory; back-office Browser Actions; built as AOPs (`blog-missions.txt:97-121`).

**Honest assessment.** Decagon has the strongest *authoring and evaluation* story and the boldest scope (Missions). It is also the least verifiable of the three: no open SDK, no public docs, no pricing, no repository. Its entire technical narrative rests on vendor blogs. The `© 0000` footer and "ISO 27001:2002" typo are small signals of a marketing site that is not tightly reviewed — not evidence of anything about the product, but a reason to treat the copy as copy.

### 4.3 Parloa

**What it is.** Enterprise AI agent platform for voice and chat: Agent Builder, Performance Lab, Lens, Conversation Infrastructure, enterprise security/governance, Navigator, plus a 2026-11-02 Agent Management API/SDK/CLI/MCP.

**What is actually open.** One official, unusually rich artifact:

- `parloa-oss/parloa-sdk-python`, **Apache-2.0**, Fern-generated from Parloa's OpenAPI, pinned `873c3f437a373b1be77091aeb75786aa6dc36e02`.
- The `parloa` GitHub org has no product code (a fork and unrelated repos). The `parloa-oss` org states that Parloa's platform and customer-data systems remain **closed source**.
- Public docs are thin by design: `docs.parloa.com/sitemap-pages.xml` lists **exactly one URL**; the site's own agent interface, asked how the API scopes tokens, answered that it *"can't verify … from the available documentation"* (`doc-ask-tokens.md`). Technical docs live at `docs.amp.parloa.com`, an AMP Studio SPA behind login (build `40ea248`, 2026-11-10). The landing page states plainly that deeper spaces *"require you to login separately. You must be whitelisted."*

**As-built semantics (SOURCE-VERIFIED).** The SDK is the best public window into a serious voice platform's domain model:

| Concept | What the type says | Where |
|---|---|---|
| Pipeline | *"Keyed, flat capabilities. Execution order is owned by the runtime."* | `types/pipeline.py:25` |
| Barge-in | `is_enabled`, `barge_in_after_ms`, `barge_in_min_words` | `types/barge_in.py:21-28` |
| Caller identity | Identity key must be a skill **output**; not a system variable, header, platform context, reserved name, collect/sensitive/unstable reference | `types/authentication_customer_identity.py:22-31` |
| Deterministic rules | Max/mean/median latency functions; tool-call presence, ordering, parameter matching; empty/markdown/code leakage | `types/validate_*.py`, `types/*_latency_function.py` |
| Simulations | Versioned definitions, runs, batch runs, cancel, quota | `simulations/raw_client.py:126,333,1376,1596,1812,2195,2397` |
| Agent blueprints | Drafts, versions, publish, deployments, 409-protected deletion | `agent_blueprints/raw_client.py:108,275,473,620` |
| MCP | Remote `server_url` + `transport` connectors | `types/mcp_connector.py` |

**Claims (MARKETING / DOCS):** 140+ languages and variants; adaptive barge-in and smart turn-taking; direct SIP to telephony/CCaaS/PBX/WebRTC; unlimited concurrency; SRTP/IPsec; Parloa Zones regional deployment; LLM guardrails at the infrastructure layer with PCI routed to a non-LLM process; RBAC/MFA/SSO; ISO 27001, SOC 2 Type 1+2, PCI DSS, HIPAA, DORA, GDPR, EU AI Act; third-party pen tests (`platform-*.txt`).

**The 2026-11-02 control plane matters most for Klaint.** Parloa's Agent Management API/SDK/CLI/MCP: manage agents from code or from an AI assistant; MCP uses **SSO, no API key, read-only by default**, previews and drafts, with publish/deploy as separate steps; API clients are scoped to **one organisation and one region** with short-lived tokens (`blog-agent-management-api.txt:24,34-38`). That is the shape of the 2027 baseline. Klaint must ship it in the MVP, not "later".

---

## 5. Head-to-head: what the evidence actually supports

Full cell-by-cell table with sources: `COMPETITOR_EVIDENCE_MATRIX.md`. The synthesis:

### 5.1 Where all three are equal (so no differentiation is available)

- Multi-channel: chat, email, voice are table stakes for all three.
- Guardrails as a concept: all three claim incoming and outgoing checks plus some deterministic layer.
- Simulations: all three claim pre-launch scenario testing; all three have published *limits* or require human review.
- Compliance *claims*: all three list SOC 2 / ISO 27001 / HIPAA / PCI / GDPR-adjacent certifications, none verifiable without an NDA.
- SaaS-only deployment: **no public self-host or air-gap option was found in the sources reviewed**; a private offering may exist.
- Arabic/dialect evidence: **no public evidence was found in the sources reviewed**. This is an evidence gap in our sources, not proof that none exists.

### 5.2 Where each is genuinely ahead (steal this)

| Vendor | Genuine strength | What Klaint should copy |
|---|---|---|
| **Lorikeet** | Epistemic honesty; outcome pricing; a clean public API contract; published simulation limits | Publish limits and failures; design the ticket/ingest contract first; price on outcomes where possible |
| **Decagon** | Authoring UX (AOPs from transcripts); evaluation rigour (LLM-judge + human ground truth + live A/B); long-horizon Missions | AOP-like authoring; evaluation as a first-class resource with versions and batch runs |
| **Parloa** | Runtime-owned execution order; authentication as deterministic state machines; versioned draft/publish/deploy; MCP with SSO/read-only/default-deny and org+region scoping | Deterministic graphs over LLM-chosen order; identity as a skill output never an input; a control plane that is read-only until explicitly enabled |

### 5.3 Where each is exposed (Klaint's openings)

| Vendor | Exposure |
|---|---|
| Lorikeet | Cannot isolate a skill in simulation; mocked tools cannot branch on inputs (both published by Lorikeet); **no public self-host or action-authority primitive found in reviewed sources**; no Arabic evidence found |
| Decagon | Docs and API gated ⇒ opaque developer experience; no public language quality data found; AOP "validated workflows" unverified; no self-host documented; dependency on third-party models plus proprietary Chord |
| Parloa | Closed platform, no self-host and no rate card in public sources; 140+ claim unverified for dialects; API breadth large but runtime opaque; MCP control plane is new (2026-11-02) and unproven at scale |
| **All three** | **No public** cryptographic action receipt, tenant-isolation test suite, Arabic dialect benchmark, or offline/air-gapped mode found in reviewed sources. Absence here is an evidence gap, not proof of absence. |

---

## 6. The architecture lessons, stated as rules

These are the transferable conclusions, independent of any vendor's marketing:

1. **Determinism beats autonomy in regulated workflows.** Parloa's "execution order is owned by the runtime" is the strongest public statement of the right model. An LLM that chooses the order of consequential steps is a liability.
2. **Identity must be an output of a verification step, never an input to a tool.** Parloa encodes this in types; Lorikeet documents it in prose; Parlant violates it in its plugin server. Klaint must enforce it in a broker.
3. **A prompt is not a permission.** Every competitor's guardrail story is eventually a model checking text. Klaint's differentiator is that authorization is a signed object, not a sentence.
4. **Unknown is a state.** None of the reviewed public sources documents what happens when a tool call times out after the money moved. Klaint's ledger must model `unknown` and reconcile.
5. **Streaming and safety are in tension; make the trade explicit.** Parlant's own code shows why: in streamed output the hook is observational because the bytes are already gone. Klaint should expose `FAST` / `GUARDED` / `REGULATED` profiles per agent rather than pretend one setting does both.
6. **Handoff needs an ownership epoch.** All three describe escalation; none of the reviewed public sources documents how an in-flight AI turn is prevented from landing after a human replies. Klaint can make this a correctness feature.
7. **The control plane is now the product.** Parloa shipping an API/SDK/CLI/MCP with SSO, read-only default, drafts and previews sets the bar. A GUI-only builder is a 2024 product.
8. **Publish your limits.** Lorikeet's credibility comes from saying what its simulations cannot do. Klaint's Arabic benchmark will only be believed if it includes failures.

---

## 7. Donor assessment (and one firm rejection)

| Donor | Version/pin | Licence | Verdict | Role |
|---|---|---|---|---|
| **Parlant** | `4962e62…` v4.0.6 | Apache-2.0 | **Conditional / reference** | Optional rule/tool-narration engine behind the broker; never the trust boundary |
| **Pipecat** | `257129f…` | BSD-2-Clause | **Adopt** | Voice pipeline, VAD, turn-taking, barge-in, transports |
| **τ-bench 2.0** | `c06b07d…` | MIT | **Adopt harness** | Evaluation skeleton; add Arabic pack |
| **Standard Webhooks** | `3d65b18…` | Apache-2.0 | **Adopt** | Signed outbound events |
| **Chatwoot** | `8b33b54…` v4.20.0 | MIT core; `enterprise/` separate | **Adopt core only** | Human inbox and handoff |
| **Rasa OSS** | `60a3cff…` v3.6.21 | Apache-2.0 | **Reject** | Maintenance mode; vendor path is commercial CALM |

### 7.1 Parlant: why "conditional" and not "adopt"

Apache-2.0 makes reuse legal. The engineering case is weaker:

- It is a fast-moving "vibe-coding platform for chat agents" — a moving target to fork.
- The two defects that matter to Klaint are **not** upstream-fixed: caller-supplied `customer_id` on the plugin tool server (`plugins.py:607-612,851`) and stream-observational output hooks (`loop/base_loop.py:2229-2244`).
- Its own `AGENTS.md` frames the product around chat agents with human handoff and hosting — a different centre of gravity from Klaint's regulated, self-hosted, capability-brokered design.

**Recommendation:** use Parlant as a *reference implementation* for rule matching, tool narration and message review. If adopted, **assume the plugin tool server is reachable and cannot be disabled** - do not plan on turning it off. Register consequential tools only through the broker, require a broker-issued capability on every tool call (read tools included), ignore caller-supplied `customer_id`, isolate tenants by container and UID, pin the version, and budget for divergence. Do not let Parlant become the security boundary.

### 7.2 Rasa: a clear no

The README states Rasa Open Source is in **maintenance mode** and that the future is Hello Rasa and CALM. Last commit 2025-12-18 (`60a3cff…`). Building Klaint on it would inherit a legacy NLU/story model and a dead-end upgrade path. Reuse isolated ideas only (domain/story test format, two-stage NLU) — not the framework.

### 7.3 Pipecat, τ-bench, Standard Webhooks, Chatwoot

- **Pipecat** is the right voice substrate: transports for LiveKit/SIP/WebSocket/WhatsApp, first-class turn-taking strategies, active project, BSD-2 compatible with commercial self-host. Keep business policy out of its processors.
- **τ-bench 2.0** gives a reproducible tool-agent-user loop with a simulated user and programmatic reward, over airline/retail/telecom, text and full-duplex voice, six languages. It has **no Arabic** — which is precisely the contribution Klaint should make.
- **Standard Webhooks** (`webhook-id`, `webhook-timestamp`, `webhook-signature`, signed content `id.timestamp.payload`, timestamp tolerance, `whsec_` prefix) removes the need for a bespoke HMAC scheme.
- **Chatwoot** core already models `assignee_id`, `team_id`, `status`, `priority` with the right indexes (`app/models/conversation.rb:16-51`). Use it; exclude `enterprise/`.

---

## 8. Klaint target architecture, in brief

Full design, contracts C1-C15, diagrams and anti-patterns: `KLAINT_TARGET_ARCHITECTURE.md`. The shape:

```
Channels → Gateway → Orchestrator (Python) → Retrieval / LLM router
                          ↓
                   Capability Broker (canonical: Python · Rust = proposal) → Ledger → Tool Workers → Customer systems
                          ↓
                    Output Gate → TTS / channel release
                          ↓
                 Event bus → traces, audit, Chatwoot handoff, evaluation
```

Five decisions that carry the strategy:

1. **Python orchestrator + Python broker in a separate process; DB-table ledger.** This is the canonical plan (BN-02, ~800-1,500 LOC estimate, `WISPRAL_COPY_FIRST_STRATEGY.md:50-58,71`). A Rust broker/ledger is an **unratified proposal** that would need an ADR and cross-language parity tests; see `ARCHITECTURE_RECONCILIATION.md`.
2. **Capabilities, not credentials.** Every consequential tool call requires a short-lived, single-use, argument-bound Ed25519 capability, verified by the broker, with a nonce ledger and enumerated deny reasons. No tool call may rely on caller-supplied `customer_id`.
3. **Three output profiles** (`FAST` / `GUARDED` / `REGULATED`) with stated latency costs (estimates, to be measured), because the trade is real and hiding it is dishonest.
4. **Event-sourced ledger with first-class `unknown`.** Idempotency keys bind the *business object*, not the turn; reconciliation, not blind retry.
5. **Ownership epochs with Chatwoot.** Every AI turn carries `conversation_id + epoch`; assignment changes increment the epoch; stale turns are dropped.

The testable contracts (C1-C15) are the acceptance criteria for the whole product: forged customer id yields zero data, capability replay denied, argument substitution denied, expiry denied, no text before gate allow in `REGULATED`, no "refunded" without a ledger success, one effect for repeated business action, unknown outcome reconciled, zero cross-tenant leakage, undeclared egress blocked, stale AI turn dropped, citations resolve, handoff packet complete, Arabic suite passes, audit reconstructible.

---

## 9. A neutral head-to-head evaluation methodology

The mission asks how to compare, not to score. This protocol is designed so that any vendor — including Klaint — can be tested the same way, and so that a result is publishable without consent (aggregate) or with consent (named).

### 9.1 Scenario sets

| Set | Domain | Size | What it tests |
|---|---|---|---|
| S1 | SaaS support (billing, cancellation, bug triage) | 60 | Baseline resolution and tool use |
| S2 | E-commerce (order status, refund, address change, returns) | 60 | Object binding, money actions, idempotency |
| S3 | Regulated finance (card block, dispute, KYC handoff) | 40 | Identity proofing, refusal, escalation |
| S4 | Healthcare admin (appointment, prescription refill routing) | 40 | Privacy, scope limits, handoff |
| S5 | **Arabic dialect + English** (MSA, Gulf, Egyptian, Levantine, Arabizi, code-switch) | 120 | The differentiator |
| S6 | Adversarial tool-calling (injection, false authority, goal switch, data exfil, forged identity, replay) | 80 | Authority integrity |
| S7 | Voice-specific (barge-in, hesitation, background noise, DTMF, transfer) | 40 | Real-time behaviour |

Each scenario is a scripted user goal, a tool environment (real sandbox or a deterministic mock that **branches on inputs**), and an expected outcome plus expected action trace.

### 9.2 Measures

| Measure | Definition | Notes |
|---|---|---|
| Task success | Goal achieved, verified by state change or explicit confirmation | Programmatic where possible |
| Resolution accuracy | Correct answer against a human-authored key | Blind human review |
| Action precision / recall | Correct tool calls vs expected, per side-effect class | Money tools weighted separately |
| **False action rate** | Unauthorized, wrong-object, or duplicate effect | Must be 0 on S6 |
| Hallucination rate | Unsupported factual claims per audited sample | Needs citations to check |
| Citation validity | Citations resolve and support the claim | Klaint-specific advantage |
| Handoff correctness | Right escalation, no double reply, complete packet | Scripted race conditions |
| Barge-in latency | Time from detected speech to silenced TTS | Instrumented |
| Latency | p50/p95/p99 end-to-end and per stage | Same network, same telephony |
| Cost per resolution | Telecom + STT + TTS + LLM + infra + platform fee | Public rates where available |
| Tenant leakage | Any cross-tenant data in output or retrieval | Adversarial suite |
| Reviewer UX | Time to diagnose a failure from the trace | Timed task, 5 reviewers |

### 9.3 Fairness rules

- Same telephony path, same STT/TTS providers where the vendor allows it, same network region.
- Disclose every configuration knob changed, including guardrail thresholds.
- Report failures and refusals, not only successes.
- Publish the harness (τ-bench-derived) so results are re-runnable.
- No composite "score". A weighted index invites gaming; publish the vector.

### 9.4 What this protocol cannot do

It cannot fairly compare a self-hosted Klaint on a laptop against a vendor's production SaaS without identical infrastructure — so latency comparisons must state the deployment. It cannot test guardrail precision without adversarial corpora that vendors may treat as confidential. And it cannot produce Arabic results for competitors who will not run the suite; in that case the honest output is *"no public evidence"*, not a zero.

---

## 10. Roadmap and gates, in brief

Full plan with effort ranges: `KLAINT_COMPETITIVE_ROADMAP.md`.

| Phase | Focus | Calendar (est.) | Exit gates |
|---|---|---|---|
| **P0** | Broker, ledger, gate skeleton, tenancy, egress manifest | 3-4 wks | G1-G4: no forged/replayed/substituted capability; zero tenant leakage; no undeclared egress; every action in ledger |
| **P1** | Chat MVP + citations + Chatwoot handoff | 5-7 wks | G5-G8: citations resolve; no double reply; zero unauthorized actions on adversarial suite; p95 < 3 s |
| **P2** | Voice (Pipecat + LiveKit/Twilio) | 6-8 wks | G9-G12: barge-in < 250 ms; p95 < 2.5 s; regulated never ungated; cost in band |
| **P3** | Authoring, simulations, evaluation | 5-7 wks | G13-G15: no publish on failing suite; branchable mocks; per-scenario traces |
| **P4** | Arabic dialect excellence | 6-10 wks | G16-G18: published pack and scores; dialect delta ≤10 pts; no English regression |
| **P5** | Enterprise + self-host | 8-12 wks | G19-G21: air-gap zero egress; no critical/high pen-test findings; restore drill |
| **P6** | MCP control plane | 3-5 wks (parallel) | Read-only default, SSO-bound, drafts/preview |
| **P7** | Compliance evidence | 6-12 months | SOC 2 Type I → II, ISO 27001 as needed |

**Credible chat+voice MVP: ~4-5 months with 4-6 engineers.** Arabic + authoring + evaluation: ~7-8 months. Enterprise/self-host: ~10-12 months. All figures are estimates with ranges, not commitments. The latency and Arabic numbers in the gate column are **acceptance targets to be measured**, not observed results; no competitor latency was measured anywhere in this report.

**The gates are binding, not aspirational.** G1 failing after two remediation rounds is a stop signal, not a schedule slip.

---

## 11. Unit economics

Published rates (accessed 2026-11-18): Twilio US inbound **$0.0085/min**, outbound **$0.0140/min** (`twilio-voice-us.txt:395-398`); Deepgram streaming STT **$0.0065/min** (was $0.0077) (`deepgram-pricing.txt:130`); ElevenLabs Creator **$22/mo for 121k credits**, consumption model-dependent.

**Illustrative 3-minute voice resolution:** PSTN $0.042 + STT $0.0195 + TTS $0.02-0.10 + LLM $0.01-0.06 + compute $0.02-0.05 ≈ **$0.11-0.27** (≈$0.04-0.09/min). Lorikeet lists voice at **$1.50 per resolution** (3-minute average). Infrastructure is roughly **7-18%** of that price — the margin is orchestration quality, not minutes.

**At 10k voice resolutions/month self-hosted:** roughly **$3,200-9,000/month** (≈$0.32-0.90 per resolution) including support/engineering allocation. This is a modelled **estimate**, not a quote or a measurement. Klaint's advantage grows with volume and shrinks with engineering overhead; at low volume, SaaS is simply better and saying otherwise would be dishonest.

**Pricing posture if hosted:** below Lorikeet's $0.99 chat / $1.50 voice but above infra+support — target roughly $0.40-0.70 chat and $0.80-1.20 voice at scale, with a platform fee. Never compete on "free".

Parloa and Decagon have no public rate cards, so no three-way price table is possible. Anyone who shows you one has invented the numbers.

---

## 12. Risks, and the conditions under which to stop

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Broker/orchestrator complexity delays MVP | High | High | P0 scope discipline; no console before gates |
| Parlant upstream churn (and unfixed trust boundaries) | High | Medium | Own orchestrator; Parlant optional; pin |
| Arabic providers insufficient for dialects | Medium | High | Multi-provider bake-off; fine-tune later; publish results |
| Voice latency/cost worse than modelled | Medium | High | LiveKit SIP; sentence gating; caching |
| Competitor ships self-host | Low | High | Move fast in the regulated wedge; partner |
| Security incident | Low | Existential | Gates, pen test, least privilege, kill switch |
| Funding/talent/burnout | Medium | High | 4-6 focused engineers; cut scope, not gates |
| "Open source" attracts unpaid support load | Medium | Medium | Clear licence, paid support, contributor policy |

**Stop or pivot if, after P1:** the red-team suite still produces unauthorized actions after two remediation rounds; design partners will not pay for self-host or Arabic quality; voice p95 cannot get below 3 s on the target network; or the team cannot sustain four engineers for six months.

Stopping at month four is a better outcome than shipping a "secure" agent that isn't.

---

## 13. Contradictions, corrections, and open questions

### 13.1 Contradiction log

| # | Observation | Resolution |
|---|---|---|
| C1 | **KT-01 "fixed upstream" claim was wrong** | Retracted. 4.0.6 still has `/tools/{name}/calls` with caller-supplied `customer_id` (`plugins.py:607-612,851`) and a loopback-bound integrated server (`sdk.py:4961-4990`). See §2.3. |
| C2 | Wispral pins Parlant 4.0.2; upstream is 4.0.6 | Both recorded. 4.0.6 adds a buffering reviewer gate (`base_loop.py:2140-2144`) but does not remove either trust boundary. |
| C3 | Parloa PyPI provenance link may 404 | Canonical repo is `parloa-oss/parloa-sdk-python` at the pinned commit. Cite that. |
| C4 | Decagon security page says "ISO 27001:2002" | Recorded verbatim; almost certainly 2022. Not silently corrected. |
| C5 | Decagon footer shows "© 0000" | Site rendering artefact; no evidentiary value. |
| C6 | Lorikeet SDK is Apache-2.0 but the platform is closed | An SDK licence grants no backend access and no rights beyond Apache-2.0 terms. |
| C7 | Decagon package is "public" but not open source | Publicly downloadable ≠ reusable. Restrictive licence; analysis only. |
| C8 | Rasa commit date is 2025-12-18 while peers are 2026-11 | Consistent with maintenance mode; do not present Rasa as actively developed. |

### 13.2 Open questions that block confident claims

| # | Question | What would answer it |
|---|---|---|
| Q1 | Does any competitor have dialect-grade Arabic? | Blind evaluation on a shared set, or vendor-supplied results |
| Q2 | Is Lorikeet's "customer isolation" enforced server-side? | Authorised forged-caller test in a tenant |
| Q3 | Does Parloa's runtime really own execution order at runtime? | Sandbox trace export |
| Q4 | Do Decagon AOPs "compile into validated workflows"? | Docs/API access |
| Q5 | What do any of them charge at 10k+ resolutions/month? | Written quotes |
| Q6 | Do their certifications cover the exact deployment a regulated buyer needs? | Reports under NDA |
| Q7 | Can Klaint's broker stay under 20 ms p99? | P0 benchmark |
| Q8 | Which Arabic STT/TTS providers pass a dialect suite? | P4 bake-off |

---

## 14. What this report does not claim

- It does not claim any competitor's backend was examined. None was.
- It does not claim any competitor is insecure. It reports that specific public code (Parlant) has a specific weakness, and that **no competitor was found in reviewed sources that publishes** a verifiable action-authority primitive. Their internal mechanisms are unknown.
- It does not claim Klaint's capability design is cryptographically stronger than a competitor's implementation. It claims no competitor **publicly documents** an equivalent, and that Klaint can prove its own with a published test suite.
- It does not assign a winner, a score, or a ranking. The comparison is dimensional and evidence-labelled.
- It does not claim Klaint works. It claims Klaint is well specified and unbuilt, and describes what building it correctly would require.
- It does not treat user-stated permission as repository access. No private competitor repository was found or used.

---

## 15. Bottom line

Klaint has a genuinely good specification, a founder-grade security instinct, and one unresolved but well-understood acceptance gate. It has no product. The competitors are real, competent, and ahead on every dimension that money and time buy: channels, integrations, enterprise plumbing, certifications, customers.

The way to win is not to catch up on their axes. It is to take the three axes they have left open — **Arabic dialects, provable action authority, and true self-host with declared egress** — and be so demonstrably correct on them that a regulated, Arabic-speaking buyer chooses a smaller vendor because it is the only one that can answer the security questionnaire and the language question honestly.

That is a real business. It is not a sure thing. It requires shipping the broker and the gate before the demo, publishing the benchmark including the failures, and resisting the temptation to claim parity before it exists.

**Do that, and Klaint can compete where it matters. Skip it, and it becomes another agent startup with a security page.**
