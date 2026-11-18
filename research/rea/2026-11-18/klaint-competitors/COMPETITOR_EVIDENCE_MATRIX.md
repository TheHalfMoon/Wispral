# COMPETITOR_EVIDENCE_MATRIX.md

**As of:** 2026-11-18 · **Benchmark product:** Klaint (TheHalfMoon/Wispral)
**Rule:** no invented scores. Every cell carries an evidence type and a source. Where a vendor claims something we could not verify, the cell says **claim** and explains what would verify it.

**Scope rule (2026-11-18):** "not found" and "no public option" mean **not found in the public sources reviewed on that date**. They are statements about our evidence, not proof of absence; a private or unlisted capability may exist. See `ARCHITECTURE_RECONCILIATION.md` §6 for the wording rule.

**Supplemental Lorikeet archives (2026-11-18):** a generic NestJS/Temporal library (MIT), an MCP server package that ships **no implementation and no licence**, a 28-line demo MCP client (ISC), and a widget loader SDK with **no licence**. They add API-surface evidence only; none is backend code. Details: `SOURCE_CODE_INVENTORY.md` §2.5.

Evidence labels: **SV** source-verified (pinned code) · **DV** docs-verified · **OB** observed public artifact · **MI** marketing-inferred (vendor claim) · **UNK** unknown.

---

## 1. At a glance

| Dimension | Lorikeet CX | Decagon | Parloa | Klaint (today) |
|---|---|---|---|---|
| Entity / product | AI customer support for complex/regulated businesses; "concierge", Coach, Dreamweaver, Quality | AI concierge for enterprise CX; chat, email, voice, AOPs, Duet, Missions | Enterprise AI agent platform for voice + chat; Agent Builder, Performance Lab, Lens | Specified in Wispral; **no product implementation** (`CURRENT_STATE.md:33-34`) |
| Public code | Node SDK (Apache-2.0), mock-api, RN SDK (MIT) **SV** | Duet CLI (proprietary), no OSS **SV/OB** | Python SDK (Apache-2.0), generated API types **SV** | Docs/specs only **SV** |
| Backend source | Not public **UNK** | Not public **UNK** | Explicitly closed **DV** | None |
| Primary evidence depth | High on API + product discipline; low on runtime | Medium on product + engineering blogs; low on API (login-gated) | High on API/type semantics; medium on product; low on runtime | High on specs; zero on runtime |
| Strongest real moat | Outcome pricing + simulation-first + guardrail discipline | AOP authoring + evaluation engine + Missions + Chord voice | Deterministic orchestration + enterprise compliance + API/MCP control plane | Arabic + self-host + verifiable action authority (all unbuilt) |
| Weakest proven area | Voice/telephony depth unclear from public evidence | Public API/docs access; Arabic evidence | Self-host / open source; public pricing | Everything runtime |

---

## 2. Channels and modalities

| Capability | Lorikeet | Decagon | Parloa | Evidence |
|---|---|---|---|---|
| Chat | Yes (`/v1/conversation/chat/*`) | Yes (Chat product) | Yes (Universal Chat) | L: SV `chat.ts:26-51`; D: MI `product-voice.txt:9`; P: MI `platform-conversation-infrastructure.txt:34-42` |
| Email | Yes (`conversation/email.ts`) | Yes (Email product) | Yes (per pricing "per interaction for chat"; email implied) | L: SV; D: MI footer; P: MI pricing |
| Voice / PSTN | Yes; web voice via LiveKit; telephony integrations listed | Yes; Voice 3, outbound, escalation | Yes; direct SIP, CCaaS/PBX/WebRTC, unlimited concurrency claim | L: SV `voice/web.ts:12-42`, MI pricing telephony list; D: MI `product-voice.txt:94-109`; P: MI `platform-conversation-infrastructure.txt:17-24` |
| SMS | Yes (pricing SKU) | Not explicit on pages reviewed | Not explicit | L: MI `pricing.md:57-62` |
| In-app / SDK | Yes (RN SDK, web) | Yes (personal agent channel, "Duet") | Yes (chat widget) | L: OB RN package; D: MI `product-voice.txt:33-35`; P: MI `...conversation-infrastructure.txt:37-38` |
| Business-to-agent (B2A) | **Yes**, launched **17 September 2026**; WebMCP + public endpoint | **Yes**, "personal agents ... dedicated channel ... permissions you control" | Not found | L: DV `agents.md:167,177`; D: MI `product-voice.txt:33-35` |

**Read:** all three are multi-channel. Klaint is unlikely to differentiate on "we have chat + voice"; it must differentiate on *where the data goes* and *what the agent is allowed to do*.

---

## 3. Voice stack and conversational quality

| Dimension | Lorikeet | Decagon | Parloa | Notes |
|---|---|---|---|---|
| Voice transport | LiveKit for web calls; PSTN via listed providers (Amazon Connect, Twilio, Vonage, Five9, AirCall, Dialpad) | Not public; "Voice 3" | Direct SIP; SRTP/IPsec | L SV + MI; D UNK; P MI |
| Speech models | Not public | **Chord**, in-house speech model (claim) | STT/TTS provider types in SDK (Azure, Deepgram, ElevenLabs, Riva, Soniox, Cartesia) | P: **SV** `types/stt.py`, `types/tts.py`, provider parameter files |
| Barge-in | Not stated on reviewed pages | "Interruption handling"; agent yields and picks up (claim) | **Configurable**: `barge_in_after_ms`, `barge_in_min_words`; "adaptive barge-in" | P: **SV** `types/barge_in.py:21-28`; D: MI |
| Turn-taking | Not public | Not public | "smart turn-taking" claim; runtime owns order | P: MI + SV `pipeline.py:25` |
| Languages | Not stated on reviewed pages | **70+**, auto-detect + switching (claim) | **140+ languages & variants** (claim) | Both MI; no dialect evidence |
| Latency | Not published | Not published | "low latency"; deterministic eval rules include max/mean/median latency functions | No independent numbers. P: SV `types/agent_max_latency_function.py` etc. |
| Voice testing | Conversation testing lab for outbound | Simulations across channels | Simulations + evaluations at production scale | All MI; none publish methodology |
| Arabic / dialects | Not found | Not found | Not found (140+ claim only) | **Genuine evidence gap across all three** |

**Conclusion:** no public evidence of Gulf/Levantine/Egyptian dialect quality was found for any of the three in the sources reviewed on 2026-11-18. Absence of evidence is not proof of absence; a private capability may exist. This is an opportunity, not a proven Klaint advantage - Klaint must publish its own reproducible Arabic benchmark.

---

## 4. Agent building and orchestration model

| Dimension | Lorikeet | Decagon | Parloa |
|---|---|---|---|
| Authoring surface | "Coach" setup agent + concierge config; plain-language guardrails | **AOPs**: natural language that compiles into validated workflows; Git-based versioning; Duet generates AOPs from transcripts | **Agent Blueprint**: single source of truth, drafts, versions, publish; subtask agents; Navigator converts SOPs → agents |
| Who owns execution order | Not public | Hybrid: LLM interprets, code enforces critical actions (claim) | **Runtime owns order** ("Execution order is owned by the runtime", SV) |
| Determinism | Tier-1 deterministic boundaries in code (customer isolation, server-side identity, workflow-scoped tools, execution caps) | "deterministic execution" for critical actions; validated workflows | Skills + flows + hooks + deterministic rules; authentication state machines |
| Multi-agent | Not public | Missions coordinate personas/systems over days (claim) | Subtask agents with deterministic routing/handoff conditions (SV types) |
| Versioning / release | Not public | Git-based tracking; version every change; rollback (claim) | Draft → version → publish → deployment → `:validate` / `:deactivate` / `:sync` (SV) |
| Environment model | Not public | Not public | Environments + variables, per-market settings (SV + MI) |

**Design lesson for Klaint:** Parloa's "runtime owns order" is the most defensible model for regulated workflows. Decagon's AOP authoring is the best UX story. Lorikeet's deterministic tier-1 is the best *security* story. Klaint should combine: AOP-like authoring, runtime-owned deterministic graph, and code-enforced capabilities.

---

## 5. Identity, authentication, and action authority

| Dimension | Lorikeet | Decagon | Parloa |
|---|---|---|---|
| Customer identity API | `POST /v1/customer/token`, `/consent`; server-side identity validation claimed | Voice authentication; JIT API tokens scoped per session; RBAC/SSO for staff | Authentication skills with collect/execute steps, flow conditions, routes, identity key rules |
| Guidance on identity | **Strong public doc**: verify in app/site, pass a reference; don't rely on prompt instructions; bind short-lived action tokens to the customer; email sender is identifier not proof; 7-30 day cooldown on changed details | "Just-in-time API tokens ... scoped for minimal privilege and discarded after each session" (claim) | Identity key must be a skill output; system variables/headers/reserved names forbidden (SV) |
| Action-level authority | Workflow-scoped tool access + execution caps (claim) | "Critical operations ... under strict validation protocols" (claim) | Deterministic skills; connector auth types; secrets; MCP connectors; per-environment vars |
| Where identity can be forged | Not public | Not public | Not public |
| Evidence quality | **DV** (`doc-customer-authentication.md`) | MI | **SV** types (`authentication_customer_identity.py`) + MI |

**Klaint's opening:** no verifiable action-authority primitive was found in the public documentation of any of the three. Klaint's specified Ed25519 capability broker (KL-T3) is a different class of control from a prompt-level guardrail and can be demonstrated with a forgery/replay test suite. This is a *claim Klaint can prove about itself*; it is not a claim of cryptographic superiority over mechanisms we cannot inspect.

---

## 6. Guardrails and output safety

| Dimension | Lorikeet | Decagon | Parloa |
|---|---|---|---|
| Incoming message checks | Up to 10 message checks; detection prompt or exact phrase; prompt-injection flag | Bad-actor detection; deflect or escalate | Per-agent safety controls; topic enforcement; social-engineering defense |
| Outgoing reply checks | Up to 10 agent guardrails; grounding guardrail always on; alert / guide (2 retries) / escalate / workflow | Supervisor model detects hallucinations and revises before send | LLM guardrails at infrastructure layer; zero perceived latency claim |
| Deterministic boundaries | Yes — isolation, identity, scoped tools, execution caps | Some critical actions deterministic | Yes — runtime + rules + authentication flows |
| Honesty about limits | **Explicit**: "Any vendor claiming immunity ... is either uninformed or dishonest"; blast radius = one conversation | Does not claim immunity; supervisor reduces | Does not claim immunity |
| Testability | Guardrail Test tab + adversarial scenarios | Simulations; checkpoints | Performance Lab; regulatory rule library |
| Evidence | MI + DV | MI | MI + SV (guardrail types: jailbreak, classifier, custom filters, thresholds) |

**Important negative finding:** Lorikeet's public writing is the most epistemically honest of the three ("reduction is the honest promise"). Klaint should match that tone and go further with a public attack harness.

---

## 7. Memory, knowledge, and retrieval

| Dimension | Lorikeet | Decagon | Parloa |
|---|---|---|---|
| Cross-channel memory | Customer profile with memory-scoped keys and `observedAt` watermarks (SV) | "Cross-channel memory" (customer quote, MI); Missions use user Memory (MI) | "Context Intelligence" remembers prior conversations; governed, auditable, deletable (MI) |
| Knowledge / RAG | Knowledge articles grounded; grounding guardrail (MI) | Suggestions / AI-powered knowledge; retrieval evaluated (MI) | Knowledge collections, attributes, files, imports, search/ranking methods (SV types) |
| Freshness controls | Not public | "Always-current test coverage" refers to tests, not KB | Imports + versioned collections (SV) |
| Deletion / governance | Consent endpoint (SV) | "auditable and deletable" not stated for Decagon; PII redaction via DLP (MI) | Governed personalization, auditable + deletable (MI) |

**Klaint target:** content-addressed KB versions + citation spans per answer + per-tenant freshness SLO. No citation-level provenance was found in the reviewed public material for any of the three; that is a defensible differentiator.

---

## 8. Tools, integrations, API, and MCP

| Dimension | Lorikeet | Decagon | Parloa |
|---|---|---|---|
| Tool protocol | Signed webhook ingest (`/ingest/...`), 200 or 202 async (10 s chat / 10 min email); `x-optech-signature` HMAC-SHA256 base64url | Not public (CLI hits `/deca_agent/*`) | Connectors: API connector, custom tool, MCP connector (`server_url`, transport); hooks (start/end) with HTTP/code/connector-tool steps |
| Integrations | Zendesk, Slack, Intercom, HubSpot, Front, HelpScout, Salesforce, Genesys; telephony list | Zendesk/Salesforce etc. (claim), pre-built connectors | SAP, CCaaS, CRM, MCP skills; SAP SOLEX story |
| Public API | Yes, comprehensive SDK (SV) | Duet CLI only (proprietary); docs login-gated | **Agent Management API + Python SDK + CLI + MCP** (2026-11-02) |
| MCP | npm package `@lorikeetai/mcp-server@1.0.0` **ships README + package.json only - no server code**; MCP/agent catalog published | Not public | MCP server for builders; remote MCP connectors for agents |
| Control-plane security | API keys (SV) | Team-scoped device-code tokens (OB) | MCP via SSO, no API key, read-only default, previews/drafts; API client scoped org+region with short-lived tokens (MI/DV) |
| Webhooks | Signed ingest; customer events | Not public | Hooks + events (SV types) |

**Table stakes by 2027:** every serious vendor will have an MCP control plane with SSO, read-only default, preview, and draft/publish separation. Parloa has already shipped it. Klaint must implement it in the MVP, not "later."

---

## 9. Testing, evaluation, and quality operations

| Dimension | Lorikeet | Decagon | Parloa |
|---|---|---|---|
| Pre-launch simulation | Real tickets → scenarios; synthetic customers; mocked tools; batch diffs; suites; adversarial (prompt injection, false authority, goal switching) | Duet auto-generates tests; checkpoints per stage; stale-test detection; CI/CD; scheduled runs; PagerDuty alerts | Auto-generated coverage from config; per-intent/tool-call/handoff tests; historical + synthetic data; human review before use |
| A/B testing | Batch comparison, not live traffic split (per reviewed pages) | **Live A/B** with gradual rollout; customers can opt out | Agent A/B: two configs, same tests, side-by-side |
| Evaluation rules | Pass-rate threshold agreed before publish | LLM-as-judge rationale + ground truth + human labels | Deterministic + AI-judge rule libraries; `validate_*` families |
| Production QA | Auto QA scores every conversation | Watchtower always-on QA + Insights | Parloa Lens + Navigator fix recommendations |
| Published limits | Cannot test one skill in isolation; mocked tool returns same answer | Not stated | Human review required; quotas |
| Benchmark evidence | Own Goal public prompt-injection challenge; third-party red team | Engineering blog on evaluation; no public benchmark leaderboard | Customer metrics only |

**Klaint target:** combine τ-bench-style reproducible tasks + action-correctness assertions + a public Arabic/Arabizi pack + tenant-isolation suite. Publish failures, not just pass rates.

---

## 10. Human handoff and ownership

| Dimension | Lorikeet | Decagon | Parloa |
|---|---|---|---|
| Escalation | Guardrail or agent escalation; full context; status `Escalated` / `EscalatedFailed` (SV) | Seamless transfer with concise summary; Decagon Assist for humans | Routing skills with destinations, invite/refer/bye configs; human escalation |
| Human workspace | Ticket platforms (Zendesk etc.) + own console | Admin dashboard + Assist | Agent/ops console + integrations |
| Ownership semantics | Not public | Not public | Not public |
| Evidence | SV statuses; MI behavior | MI | SV routing types + MI |

**Klaint target:** explicit **ownership epoch** with Chatwoot: every AI turn carries `conversation_id + epoch`; assignment change increments epoch; stale AI turns are dropped, not delivered. No public documentation of this was found for any of the three; it is a concrete correctness feature Klaint can own.

---

## 11. Deployment, tenancy, and data control

| Dimension | Lorikeet | Decagon | Parloa |
|---|---|---|---|
| SaaS | Yes | Yes | Yes |
| Self-host / on-prem | **No public option found in reviewed sources** | **No public option found in reviewed sources** | **No public option found in reviewed sources**; platform closed source |
| Region / residency | Not stated | US/EU/AU API hosts (OB from CLI); data residency not stated | **Parloa Zones** — regional deployment claim |
| Tenant isolation | Claimed in code (customer isolation) | RBAC/SSO; tenant implied by team | Org + region scoping on API clients |
| Hidden egress | Not disclosed | Not disclosed; zero-retention with LLM providers claimed | Not disclosed |
| Evidence | MI | MI/OB | MI/SV |

**Klaint's structural differentiator:** true self-host with a declared egress manifest and offline mode. Adding that would strain the SaaS model of all three, and no public self-host option was found for any of them; whether they could offer one privately is unknown. But it only matters to buyers who cannot use SaaS - a real but narrower segment (regulated, government, healthcare, defence, some EU public sector).

---

## 12. Pricing

| Vendor | Public pricing | Model | Evidence |
|---|---|---|---|
| Lorikeet | **Yes**: Start $2,100/mo annual; Scale $5,100/mo annual; Signature $75K platform fee; $0.99 chat/email/SMS, $1.50 voice (Start); $0.90/$1.20 (Scale); triage/QA $0.30 | Outcome-based per successful resolution; escalations not charged | **DV** `pricing.md:32-62,86-92` |
| Parloa | **No rate card**: per minute voice, per interaction chat; complexity-based; volume commitment; outcome-based supported | Consumption + custom enterprise | **DV** `platform-pricing.txt:10-11,26-33` |
| Decagon | **No public pricing** (pricing URL 404) | Enterprise quote | **OB** |

**TCO implication:** Klaint cannot win on list price against Lorikeet's outcome model for low-complexity chat. It can win on (a) self-host licence + infra, (b) Arabic voice where competitors charge enterprise rates, (c) avoided per-resolution fees at high volume. Model both.

---

## 13. Compliance and trust claims

| Vendor | Claims | Verification status |
|---|---|---|
| Lorikeet | Trust center; third-party penetration testing; Own Goal public challenge; honest prompt-injection stance | MI; trust page thin |
| Decagon | SOC 2 II, GDPR, CCPA, HIPAA, EU AI Act, ISO 27001 (page typo "2002"), PCI DSS 4.0.1; AES-256, TLS 1.2+; zero retention with LLM providers; Google DLP redaction; audit logs | MI; no certificates reviewed |
| Parloa | ISO 27001, SOC 2 Type 1+2, PCI DSS, HIPAA, DORA, GDPR, EU AI Act; RBAC/MFA/SSO; third-party pen tests; audit-ready logs | MI |
| Klaint | **None today** | Must build compliance evidence from zero |

**Do not** put "SOC 2" on a Klaint slide until an audit exists. Use "SOC 2-ready controls mapped" and name the auditor when true.

---

## 14. Where each competitor is genuinely strong (steal these)

1. **Lorikeet — honesty + simulation-first + outcome pricing.** Their guardrail page is a model of trustworthy positioning. Their simulation limits are published. Their pricing aligns incentive with resolution.
2. **Decagon — authoring UX + evaluation rigor + long-horizon missions.** AOPs from transcripts, LLM-judge + human ground truth + live A/B, Missions as a first-class object with a case file.
3. **Parloa — deterministic runtime + enterprise control plane.** Runtime-owned execution order, authentication state machines, versioned drafts/deployments, MCP with SSO/read-only/default-deny, regional zones.

## 15. Where each is exposed (Klaint attack surface)

1. **Lorikeet:** no public self-host, no published Arabic/dialect evidence, and no public action-authority primitive found in reviewed sources; simulation cannot isolate a skill or branch on repeated tool calls (both published by Lorikeet).
2. **Decagon:** docs/API are login-gated, so developer experience is opaque; no public language quality data found; no self-host found in reviewed sources; AOP "compiles into validated workflows" is unverified; dependency on third-party models plus proprietary Chord.
3. **Parloa:** closed platform; no self-host and no public pricing found in reviewed sources; 140+ language claim unverified for dialects; API breadth is large but the runtime is opaque; MCP control plane is new (2026-11-02) and unproven at scale.
4. **All three:** no published cryptographic action receipt, no public tenant-isolation test suite, no Arabic dialect benchmark, and no offline/air-gapped deployment were found in reviewed sources. These are evidence gaps in our sources, not proof of absence.

## 16. What we could not verify (and what would verify it)

| Unknown | Would require |
|---|---|
| Any competitor's true latency p50/p95/p99 | Instrumented trial with identical scenarios and telephony |
| Arabic/dialect quality | Blind human evaluation on a shared scenario set; recorded audio |
| Guardrail precision/recall | Adversarial test corpus run against each vendor under NDA |
| Tenant isolation | Authorized security review / pen-test report |
| Pricing at volume | Written quotes for identical volumes |
| Decagon API and AOP semantics | Approved developer account + docs access |
| Parloa runtime determinism | Authorized sandbox + trace export |
| Lorikeet tool-call enforcement | Authorized tenant + forged-caller test with permission |

**No competitor score is assigned in this report.** Any league table would be fabricated.
