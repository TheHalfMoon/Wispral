# SOURCE_CODE_INVENTORY.md

**Mission:** Klaint (TheHalfMoon/Wispral) vs Lorikeet CX, Decagon, Parloa
**As of:** 2026-11-18
**Scope:** every public or user-authorized source actually inspected in this run, with pins, licenses, what it proves, what it does *not* prove, and reuse conditions.

> Evidence labels used throughout: **[SOURCE-VERIFIED]** read from source at a pinned commit · **[DOCS-VERIFIED]** read from official docs/spec at a URL · **[OBSERVED]** seen in a public artifact (package, page, bundle) without backend access · **[MARKETING-INFERRED]** vendor claim without independent verification · **[UNKNOWN]** not accessible or not measured.

---

## 0. Provenance and legal rules applied

1. **No competitor backend source was obtained.** Nothing below should be read as "we have their engine."
2. Public client SDKs and public packages are *API surface*, not implementation. A Stainless/Fern-generated SDK describes endpoints and types; it does not prove how the server enforces anything.
3. Decagon's only distributable is **proprietary** (`SEE LICENSE IN LICENSE`). It is catalogued for **analysis only** and must not be copied, linked, or redistributed in Klaint.
4. All donor repositories are permissively licensed, but **Chatwoot's `enterprise/` directory is separately licensed** and is excluded from reuse.
5. Wispral itself is **research-only** for this mission. No files under `sources/wispral` were modified.
6. GitHub connected-account searches for installed competitor repositories returned **no matches** (see `ACCESS_GAPS.md`). User-stated permission is not evidence of repository access.
7. **Downloadable ≠ open source.** Where a package declares **no license**, no reuse or redistribution permission is implied; it is catalogued for analysis only. A missing license is not the same as a permissive one.
8. **A published package is not the product.** A tarball may omit its implementation entirely. Every row below records what the archive actually contains, not what its README or `bin` field promises.
9. **Org-repo membership is not production proof.** A library hosted under a vendor's GitHub organisation may be a republished third-party fork; that shows association, not that the vendor's production stack runs it.

---

## 1. Master inventory

| ID | Source | Type | Pin / version | Date | License | Reuse in Klaint | Confidence |
|---|---|---|---|---|---|---|---|
| E-LOR-01 | `github.com/optechai/node-sdk` (Lorikeet TypeScript API Library) | Client SDK (Stainless-generated) | `4bdaf93962d039938c2ef8526e6c55f41c40b1c7` | commit 2026 | **Apache-2.0** | Yes, with NOTICE | SOURCE-VERIFIED |
| E-LOR-02 | `@lorikeetai/node-sdk` | npm package | 3.0.0 | 2026 | Apache-2.0 | Yes | OBSERVED |
| E-LOR-03 | `@lorikeetai/react-native-sdk` | npm package, UI wrapper | 3.0.0 (`lorikeetai-react-native-sdk-3.0.0.tgz`) | 2026 | **MIT** | Yes | OBSERVED |
| E-LOR-04 | `github.com/optechai/mock-api` (Lorikeet/OpTech mock API + example ingest) | Reference server | `d8e7b594544fbb2e315b11f34dad49d0ed5dc2b8` | commit 2026 | See repo (template) | Patterns yes; verify file headers | SOURCE-VERIFIED |
| E-LOR-05 | `lorikeetcx.ai` product/pricing/docs pages + `llms.txt` | Marketing/docs | live | accessed 2026-11-18 | Site terms | Quotation only | DOCS/MARKETING |
| E-LOR-06 | `github.com/optechai/nestjs-temporal` (NestJS ↔ Temporal integration library) | Library, republished third-party code | `da2f975def682e9da7b536aaa4d49c9ccc9aadbd` (shallow clone) | committed 2024-12-06 | **MIT** (`LICENCE`, © 2022 Zegue Kurt) | Yes with notice, but generic library - no evidence Lorikeet production uses it | SOURCE-VERIFIED (1 commit visible) |
| E-LOR-07 | `@lorikeetai/mcp-server` | npm package | 1.0.0 (`lorikeetai-mcp-server-1.0.0.tgz`, 1,760 B) | 2026 | **No license field** | **No reuse.** Archive has README + package.json only | OBSERVED (no code shipped) |
| E-LOR-08 | `@lorikeetai/mcp-client` | npm package | 1.0.0 (`lorikeetai-mcp-client-1.0.0.tgz`, 1,819 B) | 2026 | **ISC** in `package.json`; no `LICENSE` file in tarball | Reference only; demo code, keep notice | SOURCE-VERIFIED (28-line demo) |
| E-LOR-09 | `@lorikeetai/web-sdk` | npm package, widget loaders | 1.13.0 (`lorikeetai-web-sdk-1.13.0.tgz`, 32,185 B) | 2026 | **No license field; no `LICENSE` file** | **No reuse** until a separate grant; analysis only | OBSERVED (bundled `dist/` + `.d.ts`) |
| E-PAR-01 | `github.com/parloa-oss/parloa-sdk-python` | Official Python SDK (Fern-generated) | `873c3f437a373b1be77091aeb75786aa6dc36e02` | 2026-11-05 | **Apache-2.0** | Yes, with NOTICE | SOURCE-VERIFIED |
| E-PAR-02 | `parloa` on PyPI | Python package | 1.0.0 | 2026 | Apache-2.0 | Yes | OBSERVED |
| E-PAR-03 | `docs.parloa.com` (GitBook) | Docs | live | accessed 2026-11-18 | Site terms | Quotation only | DOCS-VERIFIED |
| E-PAR-04 | `parloa.com` platform/pricing/security pages | Marketing | live | accessed 2026-11-18 | Site terms | Quotation only | MARKETING |
| E-PAR-05 | `github.com/parloa` | Org | 2 public repos (fork of Terraform Azure Redis module; etc.) | 2026 | varies | No product code | OBSERVED, no evidence |
| E-DEC-01 | `@decagon-ai/duet-cli` | Public npm CLI, **proprietary** | 0.6.1, tarball `decagon-ai-duet-cli-0.6.1.tgz`, 81,700 B unpacked | 2026 | **Decagon Duet CLI License (restrictive)** | **No reuse.** Analysis only | SOURCE-VERIFIED (dist bundle) |
| E-DEC-02 | `decagon.ai` product/security/blog pages | Marketing + engineering blog | live | accessed 2026-11-18 | Site terms | Quotation only | MARKETING / VENDOR-ENGINEERING |
| E-DEC-03 | `docs.decagon.ai`, `api.decagon.ai` | Developer docs/API | — | 2026-11-18 | — | **Not accessible** | UNKNOWN |
| E-DEC-04 | `decagonai` GitHub org | — | HTTP 404 | 2026-11-18 | — | Does not exist | OBSERVED |
| E-DEC-05 | PyPI `decagon` | — | HTTP 404 | 2026-11-18 | — | Does not exist | OBSERVED |
| E-DON-01 | `github.com/emcie-co/parlant` | Dialogue engine | `4962e62bcd988ff65c1e41c4cc4ade7338efe0dd`, v4.0.6 | 2026-11-17 | **Apache-2.0** | Yes (with broker isolation) | SOURCE-VERIFIED |
| E-DON-02 | `github.com/pipecat-ai/pipecat` | Voice/multimodal framework | `257129f9395d5c5ed41bcc11608b751670e17032` | 2026-11-17 | **BSD-2-Clause** | Yes | SOURCE-VERIFIED |
| E-DON-03 | `github.com/sierra-research/tau2-bench` | Agent benchmark | `c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4`, v2.0 | 2026-11-10 | **MIT** | Yes | SOURCE-VERIFIED |
| E-DON-04 | `github.com/standard-webhooks/standard-webhooks` | Webhook spec + libs | `3d65b1824b6697f05a5a4584e7062bd23512fc8e`, spec 1.0.0 | 2026-11-17 | **Apache-2.0** | Yes | SOURCE-VERIFIED |
| E-DON-05 | `github.com/RasaHQ/rasa` | OSS dialogue framework | `60a3cff9c08183760355b07bd60f5223d8916d6b`, v3.6.21 | 2025-12-18 | Apache-2.0 | **Not recommended** | SOURCE-VERIFIED |
| E-DON-06 | `github.com/chatwoot/chatwoot` | Human inbox / handoff | `8b33b543fc45578d0518553edb8bc51d9603e48c`, v4.20.0 | 2026-11-18 | **MIT** (core) + restricted `enterprise/` | Core only, enterprise excluded | SOURCE-VERIFIED |
| E-WIS-01 | `github.com/TheHalfMoon/Wispral` | Program docs/specs/research | `689a4e421d6f8acebedf15df1d2dfca0c905a835` | 2026-11 | See repo LICENSE/NOTICE | Research only | SOURCE-VERIFIED |

---

## 2. Lorikeet (OpTech AI)

### 2.1 What is actually public

- **One official GitHub organization: `optechai`** (formerly Optech). The node SDK README identifies itself as the Lorikeet TypeScript API Library and is Stainless-generated [E-LOR-01]. The mock-api repo is a template/reference for the ingest protocol, not the product [E-LOR-04].
- The React Native package is a **client UI wrapper**, MIT-licensed [E-LOR-03]. It is not a backend.
- Public docs are served as HTML plus an `llms.txt` index; some docs are also readable as page HTML [E-LOR-05].
- Supplemental archives inspected on 2026-11-18 (E-LOR-06…09): a generic NestJS↔Temporal library in the org, an MCP server package that ships **no implementation**, a 28-line demo MCP client, and the hosted widget loader SDK. None is backend code; two carry no licence. Details in §2.5.
- There is **no** public Lorikeet workflow engine, no server, no agent runtime, no evaluation engine source.

### 2.2 As-built API surface (from SDK source)

| Surface | Evidence | Notes |
|---|---|---|
| `POST /v1/conversation/chat/create` | `src/resources/conversation/chat.ts:51` | Create chat ticket |
| `POST /v1/conversation/chat/message` | `chat.ts:26` | Send message |
| `GET /v1/conversation/chat/message` | `chat.ts:38` | Poll messages |
| `GET /v1/ticket/sse/{conversationId}` | `chat.ts:115` | Server-sent events stream |
| Status union incl. `DraftResponse`, `Escalated`, `EscalatedFailed`, `Error` | `chat.ts:207-211` | Draft-then-send pattern; failure states are explicit |
| Email create/message/poll | `src/resources/conversation/email.ts` | Async channel |
| Voice outbound | `src/resources/conversation/voice.ts` | — |
| `POST /voice/web/create` → `wsUrl` + LiveKit `token` | `src/resources/conversation/voice/web.ts:12-13,35-42` | Web voice is **LiveKit**-based; server-to-server creds required |
| Customer create/update/list/token/consent | `src/resources/customer/customer.ts:26,42,55,65,88` | `POST /v1/customer/token` mints a customer-scoped token |
| Customer profile / remote profile | `src/resources/customer/profile.ts`, `remote.ts` | Profile includes memory-scoped keys with `observedAt` watermarks |
| API keys | `src/resources/api-keys.ts` | Key management |
| Customer events | `src/resources/customer-events.ts` | Event ingestion |
| Tool result ingest | `src/resources/ingest.ts:11` → `/ingest/{toolId}/{ticketId}/{inputHash}/{workflowId}` | Async tool completion |
| Ingest test/validate | `ingest.ts:18,25` | Test harness for tools |

**Signing:** HMAC-SHA256, base64url (`+`→`-`, `/`→`_`) over the raw payload with a client secret (`src/lib/generate-signature.ts:8-18`). The mock-api documents `x-optech-signature`, immediate `200`, or `202` then respond within **10 seconds for chat / 10 minutes for email** [E-LOR-04, README lines 38, 53-54].

**Architectural reading (inference, not vendor statement):** the platform is a ticket/conversation store with an agent that emits drafts, calls customer-configured tools asynchronously through signed webhooks, and escalates. The SDK does not reveal the planner, retrieval, or guardrail implementation.

### 2.3 Claims with citations

- Pricing: Start **$2,100/mo** annual, Scale **$5,100/mo** annual, Signature **$75K platform fee**; resolutions **$0.99** chat/email/SMS and **$1.50** voice (Start), $0.90/$1.20 (Scale); triage and QA $0.30 [E-LOR-05, `pricing.md` lines 32-40 table, 57-62]. Outcome-based: only successful resolutions billed; escalations not billed [same, lines ~86-92].
- Guardrails: two tiers — deterministic boundaries in code (customer isolation, server-side identity validation, workflow-scoped tool access, execution caps) and up to **10 agent guardrails + 10 message checks** per concierge; grounding guardrail always on; retry twice then escalate; explicit refusal to claim prompt-injection immunity [E-LOR-05, `product-guardrails.txt:31-39,56-57,76-77`].
- Simulations: real tickets → scenarios + synthetic customers, mocked tools (same response per tool regardless of inputs), batch diffs, adversarial suites, guardrail test tab; **stated limits: cannot test one skill in isolation; repeated calls to one mocked tool cannot branch** [E-LOR-05, `product-simulations.txt:18-22,78-79`].
- Customer authentication guidance: verify in app/website and pass a reference; do **not** rely on prompt instructions; bind short-lived action tokens to the customer; treat email sender as identifier, not proof [E-LOR-05, `doc-customer-authentication.md:29,43,97-99,125,141`].
- MCP: Lorikeet lists an npm MCP server package (v1.0.0) and an agent-facing catalog; B2A (business-to-agent) endpoint with the same identity/guardrail/action policies [E-LOR-05, `doc-mcp-server.md`, `ai-catalog.json`, `AGENTS.md`]. **Caveat from the artifact (E-LOR-07):** the published tarball contains only `README.md` and `package.json` - no `dist/`, no `index.js` - so this is a documented intent and package listing, **not** a runnable server. A demo client package also exists (E-LOR-08).
- Trust center page exists but is thin (941 bytes saved) [E-LOR-05].

### 2.4 What this source does **not** prove

No evidence of: their model choice, prompt architecture, retrieval stack, guardrail classifier implementation, tenancy isolation mechanism, latency figures, Arabic quality, or on-prem capability. Any such statement in the matrix is labeled inferred/unknown.

### 2.5 Supplemental public code, verified 2026-11-18

Further public archives were downloaded after the first pass. They are catalogued here with what they **actually contain**, because three of the four are thinner than their names suggest. Verification commands are in `REPRODUCE.md` §3.3.

| Archive | Pin / version | Licence | What is actually inside | What it proves | What it does not prove |
|---|---|---|---|---|---|
| `optechai/nestjs-temporal` (E-LOR-06) | `da2f975def682e9da7b536aaa4d49c9ccc9aadbd`, shallow clone (1 commit, 2024-12-06) | **MIT**, `LICENCE`, © 2022 Zegue Kurt | `lib/`: 20 TypeScript files (module, decorators for `@Workflow`/`@Activity`, metadata accessors, providers, utils) + 1 spec; `dist/` committed; `package.json` name `nestjs-temporal` v2.0.1 | A generic NestJS↔Temporal integration library is hosted in Lorikeet's GitHub org, and the org has committed to it | That Lorikeet's production scheduler runs this code. Package name/author and copyright show a republished third-party library; no Lorikeet business logic was observed |
| `@lorikeetai/mcp-server` (E-LOR-07) | 1.0.0; tarball **1,760 B** | **None declared** (no `license` field, no `LICENSE` file) | Exactly two files: `package.json`, `README.md`. Declares `main: index.js`, `bin: ./dist/index.js`, `files: ["dist"]`, deps `@lorikeetai/node-sdk ^0.13.1`, `@modelcontextprotocol/sdk ^1.13.0`, `express ^5.1.0`, `zod ^3.23.8`; **no `dist/` and no `index.js` are shipped** | The intended surface: `POST /mcp`, `GET /health`, resource `lorikeet://workflow/{id}`, tool `getWorkflows`, env `LORIKEET_CLIENT_ID`/`LORIKEET_CLIENT_SECRET` | Any server implementation, workflow schema, auth enforcement or retry behaviour. The package cannot run as published. It also targets node-sdk `^0.13.1` while the current SDK is 3.0.0, so it appears stale |
| `@lorikeetai/mcp-client` (E-LOR-08) | 1.0.0; tarball **1,819 B** | **ISC** in `package.json`; **no `LICENSE` file** in the tarball | `src/index.ts` = 28 lines: an `MCPOrchestrator` holding `Map<name, Client>` and `Map<toolId, {client, tool}>`, `addServer()` (connect + `listTools()`), `callTool()` with a non-null assertion; `example/dev.ts` connects to `http://localhost:3000/mcp` and calls `getWorkflows` | The demo usage pattern for an MCP client against a local Lorikeet MCP server | Any backend, credential handling, tenant identity, retry or error path. `package.json` calls it a "Dummy Lorikeet MCP Client example" |
| `@lorikeetai/web-sdk` (E-LOR-09) | 1.13.0; tarball **32,185 B** | **None declared** (no `license` field, no `LICENSE` file) | `dist/` only: `widget.js` (32,447 B), `widget.umd.cjs` (28,758 B), `voice-widget.js` (7,147 B), `webmcp.js` (6,413 B), `.d.ts` files, plus `README.md` and `CHANGELOG.md`. No `src/`. The `exports` map still points `./globals` at `./src/globals.d.ts`, which is not shipped | A loader/iframe boundary: `getIframeStartUrl()` builds a URL that "carries no credentials"; credentials are handed to the iframe by `postMessage` to the chat's own origin; the only host literal in `dist` is `https://chat.lorikeetcx.ai`; `package.json` deploys to `gs://resources.lorikeetcx.ai`; CHANGELOG 1.13.0 records the credential hand-off, `logout()`, and WebMCP next actions | The iframe application, the backend, authz decisions, retrieval, or model behaviour. Bundled `dist` is minified; no source is included |

**Assessment.** These archives add **API-surface and packaging evidence**, not backend insight. Two are unusable as code: `mcp-server` ships no implementation and no licence, `web-sdk` ships no source and no licence. The MCP-server README describes a workflow-resource server, but a README is a claim about intent, not a record of behaviour. Nothing here changes the finding that no Lorikeet planner, runtime, guardrail model or tenancy mechanism is public.

---

## 3. Parloa

### 3.1 What is actually public

- **`parloa-oss/parloa-sdk-python`** is an official, Apache-2.0 Python SDK, Fern-generated from Parloa's OpenAPI [E-PAR-01]. The `parloa` GitHub org has only unrelated/forks [E-PAR-05].
- The SDK's `raw_client.py` files and `types/` models expose a **very large, semantically rich API**: agent blueprints, drafts, versions, publish, deployments, skills, hooks, simulations, evaluations, knowledge, connectors, secrets, models, environments, tenant URLs.
- The repo explicitly states that Parloa's platform and customer-data handling remain **closed source** (per `parloa-oss` org statement, E-PAR-01/supervisor note).
- Public docs: `docs.parloa.com` welcome is public GitBook with `.md` page variants; `docs.amp.parloa.com` returns the **AMP Studio SPA shell** (build commit `40ea248`, 2026-11-10) and requires login for content [E-PAR-03].

### 3.2 As-built API surface (selected, with file+line)

All paths below are string literals in the generated client:

| Capability | Endpoint (literal) | File:line |
|---|---|---|
| List/create agent blueprints | `v1/agent-blueprints` | `agent_blueprints/raw_client.py:108,275` |
| Blueprint by id | `v1/agent-blueprints/{id}` | `:473,640` |
| Published versions | `.../versions` | `:981` |
| Draft | `.../draft` | `:981` docstring |
| Deployments per blueprint | `.../deployments` | `:620` docstring |
| Simulation definitions | `v1/simulations/definitions` | `simulations/raw_client.py:126,333` |
| Definition versions | `.../definitions/{id}/versions` | `:1376` |
| Simulation runs | `v1/simulations/runs` | `:1596,1812` |
| Batch runs | `v1/simulations/runs:batch` | `:2195` |
| Cancel run | `.../runs/{id}:cancel` | `:2397` |
| Hooks (start/end) | `v1/...hooks` | `hooks/raw_client.py` (see type files) |

**Semantics worth stealing (as design patterns, Apache-2.0 types are reusable with notice):**

- `Pipeline`: *"Keyed, flat capabilities. Execution order is owned by the runtime."* (`types/pipeline.py:25`) - orchestration is platform-owned, not LLM-chosen.
- `BargeIn`: `is_enabled`, `barge_in_after_ms`, `barge_in_min_words` (`types/barge_in.py:21-28`).
- `AuthenticationCustomerIdentity`: the identity key must be an output parameter, must not be a system variable, header, or platform context; collect/sensitive/unstable identifiers are forbidden (`types/authentication_customer_identity.py:22-31`). This is the strongest public statement of caller-identity discipline among the three.
- `DeterministicRuleRequest`: fixed checks over latency or tool calls (`types/deterministic_rule_request.py:22-36`); the `types/validate_*.py` family covers tool-call presence, ordering, parameter matching, message/call alignment, empty/markdown/code leakage, latency thresholds, and runtime errors.
- `McpConnector`: remote MCP `server_url` + `transport` (`types/mcp_connector.py:23-30`).
- `Authentication*` flow types: collect/execute flow steps, conditions, routes, operator, identifier types, terminate/return targets — i.e., deterministic authentication state machines.
- Subtask agents with routing/handoff conditions (`types/subtask_agent.py`, `subtask_agent_routing_condition.py`, `subtask_agent_handoff_condition.py`).
- `SimulationDefinitionResponse`, `EvaluationDefinitionResource`, `ai_judge_rule_request`, `deterministic_rule_request` — simulations and evaluations are first-class resources, versioned, with batch runs and quotas.

### 3.3 Claims with citations

- Consumption pricing: per minute voice, per interaction chat; rates by complexity; volume commitment reusable across use cases; outcome-based supported; **no public rate card** [E-PAR-04, `platform-pricing.txt:10-11,26-33`].
- 140+ languages and variants, adaptive barge-in, smart turn-taking, direct SIP to telephony/CCaaS/PBX/WebRTC, unlimited concurrency, SRTP/IPsec [E-PAR-04, `platform-conversation-infrastructure.txt:17-32`].
- Security: LLM guardrails at infrastructure layer, per-agent controls, topic enforcement, social-engineering defense, PII/PCI redaction with PCI routed to a non-LLM process, data residency ("Parloa Zones"), RBAC/MFA/SSO, ISO 27001 / SOC 2 Type 1+2 / PCI DSS / HIPAA / DORA / GDPR / EU AI Act claims, third-party pen tests [E-PAR-04, `platform-security.txt:14-53`].
- Performance Lab: auto-generated coverage from configuration, per-intent/tool-call/handoff tests, blended historical + synthetic data, human review before use, A/B of two agent versions, Navigator fix recommendations traced to prompt, tested fixes [E-PAR-04, `platform-performance-lab.txt:14-42`].
- Agent Builder: Agent Blueprint single source of truth, per-market settings, subtask agents, deterministic routing, MCP-based Agent Skills, context intelligence with auditable/deletable personalization [E-PAR-04, `platform-agent-builder.txt:14-53`].
- Agent Management API/SDK/CLI/MCP (2026-11-02): same agents through code or assistant; MCP uses SSO, no API key, read-only by default, previews + drafts, publish/deploy separate; API clients scoped to one org and one region with short-lived tokens [E-PAR-04, `blog-agent-management-api.txt:24,34-38`].

### 3.4 What this source does **not** prove

Server-side enforcement, actual language quality, latency, true data residency implementation, or that the 140+ language claim includes Gulf/Levantine/Egyptian dialects. The SDK proves the *contract shape*, not the runtime.

---

## 4. Decagon

### 4.1 What is actually public

- **No GitHub organization** (`decagonai` 404), **no PyPI package** (`decagon` 404).
- **One distributable: `@decagon-ai/duet-cli` 0.6.1** — a public npm package whose LICENSE is a **restrictive commercial license**, not open source: use/copy/publish/distribute only to use or connect to the Decagon Platform under an executed agreement; terminates on breach [E-DEC-01, `package/LICENSE:1-30`]. It requires an **approved Decagon account** [E-DEC-01, README].
- The package is a bundled `dist/bin.mjs` (75,922 B) plus README/LICENSE. It is **not** the agent engine.
- Developer docs are login-gated: `docs.decagon.ai` returns a "Log in" page; `api.decagon.ai` root returns 403 [E-DEC-03].

### 4.2 As-built surface from the CLI bundle (analysis only)

- Regional API hosts: `https://api.decagon.ai`, `https://eu.api.decagon.ai`, `https://au.api.decagon.ai` (`dist/bin.mjs:213-215`).
- Device-code login: `POST /deca_agent/cli/device_codes` (`:1324`), token mint `POST /deca_agent/cli/tokens` (`:605`), teams `POST /deca_agent/cli/teams` (`:1282`).
- Chat completion: `POST /deca_agent/chat/completion` (`:1023`), cancel `POST /deca_agent/chat/cancel` (`:1039`), config `GET /deca_agent/config?team_id=...` (`:1060`).
- Conversation and file handling: `/conversation/new` (`:1001`), `/file/generate_upload_url` (`:488`), `/file/send` (`:511`), `/settings/signature` (`:1116`).
- CLI UX: `duet-cli ask`, `--thinking-effort`, `--conversation-id`, `teams`, `set-team`, `plugins install --harness claude-code|codex|cursor` (SKILL.md inside bundle, lines 28-117).
- The installed skill describes access to "THIS team's AOPs, tools, conversations, analytics, and knowledge" (bundle line 28).

**License consequence:** none of this may be transplanted into Klaint. It is evidence of Decagon's control-plane shape: multi-region, device-code SSO, team-scoped tokens, conversational agent-building, file upload, streaming/cancel.

### 4.3 Claims with citations

- Voice 3 on in-house **Chord** speech model; 70+ languages with automatic detection/switching; interruption handling; hundreds of voices; seamless escalation with summary; outbound; built-in guardrails [E-DEC-02, `product-voice.txt:94-109`].
- AOPs: natural language that "compile[s] into validated workflows"; Git-based versioning; trace reasoning with runtime/latency; guardrails across chat/voice/email; Duet generates AOPs from transcripts [E-DEC-02, `product-aop.txt:82-118`; `blog-sops-to-aop.txt:98-103,113,163`].
- Testing & QA: Duet auto-generates tests, checkpoints per stage, evaluation-model rationale, always-current coverage, CI/CD, scheduled runs, PagerDuty alerts [E-DEC-02, `product-testing-qa.txt:84-107`].
- Security: RBAC, SSO (Okta/Entra), just-in-time short-lived JWT tokens scoped to least privilege, voice authentication, AES-256/TLS 1.2+, zero-data-retention with LLM providers, PII redaction via Google DLP, bad-actor detection, supervisor model revising hallucinations, Watchtower always-on QA, audit logs; certifications SOC 2 II, GDPR, CCPA, HIPAA, EU AI Act, ISO 27001, PCI DSS 4.0.1 [E-DEC-02, `security.txt:84-119`].
- Evaluation engine: models from OpenAI/Anthropic/Gemini plus fine-tuned open/commercial; offline LLM-as-judge on (query, context, response) triplets + human-labeled ground truth; online A/B with gradual rollout; customers can opt out; tracks CSAT/resolution and drift [E-DEC-02, `blog-evaluation-engine.txt:96-122`].
- Agent engine: core agent + routing + agent assist + admin dashboard/QA as one data flywheel [E-DEC-02, `blog-agent-engine.txt:99-103`].
- Missions (2026-11-12): long-horizon, multi-persona, multi-channel, days-to-weeks outcomes; Mission case + Memory; back-office Browser Actions; built as AOPs [E-DEC-02, `blog-missions.txt:97-121`].

### 4.4 What this source does **not** prove

Anything about the runtime, prompts, retrieval, guardrail models, tenancy implementation, actual latency, Arabic coverage, or mission orchestration internals. The engineering blogs are vendor-authored and are labeled as such.

---

## 5. Donors

### 5.1 Parlant — v4.0.6, Apache-2.0

- **Upstream has changed since the Wispral pin (4.0.2), but not in the way an earlier draft of this report assumed.** `pyproject.toml` declares `version = "4.0.6"`, description "vibe-coding platform for chat agents" [E-DON-01].
- **Correction (verified twice): the HTTP plugin tool server that KT-01 exploited is STILL PRESENT in 4.0.6.** The route is declared at `src/parlant/core/services/tools/plugins.py:851` (`@app.post("/tools/{name}/calls")`), and its request model still takes identity from the caller: `CallToolRequest` has `agent_id`, `session_id`, `customer_id`, `arguments` (`plugins.py:607-612`) with no authentication on the server. The SDK still starts an integrated `PluginServer` on `127.0.0.1:<tool_service_port>` (default `8818`, `sdk.py:3065`, started at `sdk.py:4961-4990`, registered as a tool service at `:4983-4988`). The standalone `PluginServer` defaults to `host="0.0.0.0", port=8089` (`plugins.py:642-643`), so a non-SDK user can bind it to all interfaces. Tools are *also* in-process `@tool` callables (`core/tools.py`), MCP (`core/services/tools/mcp_service.py`) and OpenAPI — but "also" is not "instead".
- `ToolContext` still receives `customer_id` from the engine/session (`core/tools.py:84-120`), and tools are invoked with `customer_id=context.customer.id` (`core/engines/compass/tool_runner.py:80-83`). **The identity trust boundary is unchanged:** whoever can reach the plugin server (or create/select a session) determines the tool's `customer_id`. Loopback binding reduces exposure to local processes and same-host SSRF; it does not make the assertion trustworthy.
- Output safety: `_complete_message_step` still documents that in streamed output the `on_message_generated` hook is **observational**, because the chunks are already on the wire (`src/parlant/core/engines/compass/loop/base_loop.py:2229-2244`; the sentence is at 2234-2238). However 4.0.6 adds a pre-emit reviewer path: `_should_buffer_message_for_review` (`:2140-2144`) forces a streaming loop to buffer the whole message when review is requested, and `_maybe_review_message` (`:2160-2227`) rejects/regenerates (`:2246-2254`).
- **Implication:** KT-01's two findings are **still live on 4.0.6** - a forged `customer_id` accepted by the plugin tool server, and a stream-mode hook that cannot suppress delivered text. 4.0.6 adds a better in-engine pre-emit gate, but it does not remove either trust boundary. **Do not plan on disabling the plugin server: KT-01 found no setting that does, and the later master plan assumes it is reachable** (`WISPRAL_MASTER_PLAN_FINAL.md:50,229`). Klaint must register consequential tools only through the broker, require a broker-issued capability on every tool call (read tools included), ignore caller-supplied `customer_id`, and isolate tenants by container and UID; the output gate must sit at the reviewer/buffer point or outside the engine.
- Reuse: Apache-2.0 permits commercial use and modification with NOTICE. But Parlant is a fast-moving "vibe-coding" product; pinning and forking creates maintenance drag. Recommended use: **pattern/reference implementation** for rule matching and tool narration, not as the security boundary.

### 5.2 Pipecat — BSD-2-Clause

- Voice-first Python framework with pluggable transports: `daily, heygen, lemonslice, livekit, local, moq, sip, smallwebrtc, tavus, vonage, websocket, whatsapp` [E-DON-02].
- Turn-taking is a first-class subsystem: VAD, transcription, wake-phrase, min-words, classifier, external, deferred, eager, speech-timeout, and LLM-completion strategies (`src/pipecat/turns/`), plus user-mute strategies.
- BSD-2-Clause is compatible with a commercial self-hosted product; keep copyright notice.
- Recommended: **yes** for the voice media pipeline (with LiveKit or SIP transport), wrapped so that no business policy lives in Pipecat processors.

### 5.3 τ-bench 2.0 — MIT

- Tool-agent-user benchmark with airline, retail, telecom domains; text + full-duplex voice; **six languages (English, Spanish, Portuguese, Hindi, Chinese, Korean)**; user simulator; LLM-judge post-hoc scoring; frozen released task sets [E-DON-03, README:20-45].
- **No Arabic** in the shipped language packs. Klaint can adopt the harness and contribute an Arabic/Arabizi pack — a credible benchmark moat.
- Recommended: **yes** as the evaluation harness skeleton. Do not conflate its reward with production quality; add action-correctness and tenant-isolation suites.

### 5.4 Standard Webhooks 1.0.0 — Apache-2.0

- Spec + reference libraries; `webhook-id`, `webhook-timestamp`, `webhook-signature`; signed content `id.timestamp.payload`; timestamp tolerance; symmetric secret prefix `whsec_` [E-DON-04, `spec/standard-webhooks.md`].
- Recommended: **yes** for outbound webhooks (tool results, escalations, mission events) instead of bespoke HMAC schemes.

### 5.5 Rasa OSS — Apache-2.0, v3.6.21, maintenance mode

- README: "Rasa Open Source is currently in maintenance mode. The future ... is Hello Rasa and CALM" [E-DON-05]. Last commit 2025-12-18; package version 3.6.21.
- **Recommendation: do not build Klaint on Rasa OSS.** It is a legacy NLU/story stack; CALM is the commercial path. Reuse only isolated ideas (domain/story test format, two-stage NLU) if useful.

### 5.6 Chatwoot — MIT core, restricted enterprise

- Core is MIT; everything under `enterprise/` is under a separate commercial license requiring a Chatwoot subscription [E-DON-06, `LICENSE:1-8`, `enterprise/LICENSE`].
- Data model already has `assignee_id`, `team_id`, `status`, `priority`, `assignee_agent_bot_id`, and indexes for account/inbox/status/assignee (`app/models/conversation.rb:16-51`).
- Recommended: **yes** for human inbox/handoff, core only, with an explicit ownership-epoch protocol on top.

---

## 6. Wispral (Klaint benchmark)

- `docs/canonical/CURRENT_STATE.md:33-34`: program status `SPEC_000_RESEARCH_ACTIVE`, **"Active product implementation: none"**; line 105: "product Rust/Cargo implementation added: `NO`" [E-WIS-01].
- `research/klaint-spike/README.md:5-7`: KT-01 **NOT VERIFIED**; forged `customer_id` to the integrated tool server is accepted and data is returned.
- `research/klaint-spike/README.md:46-47`: BAIL in `on_message_generated` only works in BLOCK output mode; in default STREAM mode the original draft is delivered.
- `docs/engineering/WISPRAL_SECURITY_ARCHITECTURE.md` KL-T3 (around line 114) specifies the **capability** fix: an Ed25519-signed, session/tool/argument-bound, 60-second, single-use capability verified by a broker. Its companion instruction to "disable the plugin tool server" is **not achievable** per KT-01 and is superseded by capability-on-every-tool plus per-tenant isolation; see `ARCHITECTURE_RECONCILIATION.md` §3.
- `docs/canonical/ARCHITECTURE_INVARIANTS.md` A1-A15: event-driven control plane; independently cancellable audio/agent execution; provenance; protocol-first agent integration; replaceable speech engines; bounded context; **A9 high-risk authorization fails closed**; **A10 local-first ≠ local-only**; Rust owns concurrency/policy boundaries; per-surface qualification; push-to-talk baseline; accessibility; benchmark instrumentation.

**Consequence:** Klaint has **specified** architecture and **no product code**. Every "Klaint has X" statement must be split into *specified*, *donor-inherited*, or *missing*.

---

## 7. Contradiction / version log

| # | Observation | Resolution |
|---|---|---|
| C1 | Wispral pins Parlant 4.0.2; upstream is 4.0.6 | Both recorded. KT-01 findings are valid for 4.0.2 **and still reproduce structurally on 4.0.6**: `/tools/{name}/calls` exists (`plugins.py:851`), `CallToolRequest.customer_id` is caller-supplied (`:607-612`), and stream-mode `on_message_generated` is still observational (`base_loop.py:2229-2244`). 4.0.6 adds a buffering reviewer path (`:2140-2144`) that a Klaint gate could use. Do not claim KT-01 "fixed upstream". |
| C2 | Parloa PyPI provenance link `github.com/parloa/parloa-sdk-python` may 404 | Live canonical repo is `parloa-oss/parloa-sdk-python` at the pinned commit. Cite that. |
| C3 | Decagon security page says "ISO 27001:2002" | Likely a typo for ISO/IEC 27001:2022; recorded verbatim, not corrected silently. |
| C4 | Decagon footer shows "© 0000" | Site rendering bug; no evidentiary value. |
| C5 | Lorikeet SDK is Apache-2.0 but the platform is closed | SDK license does not grant backend access or patent rights beyond Apache-2.0 terms; do not imply otherwise. |
| C6 | Decagon package is "public" but not open source | "Publicly downloadable" ≠ reusable. License is restrictive; catalogued for analysis only. |
| C7 | Rasa repo commit date 2025-12-18 while other repos are 2026-11 | Consistent with maintenance mode; do not present Rasa as actively developed. |
| C8 | npm `@lorikeetai/mcp-server@1.0.0` is published, but its tarball has no code | "Published" ≠ "runnable". `package.json` declares `bin: ./dist/index.js` and `files: ["dist"]`, yet `dist/` is absent. Treat the README as intent, not behaviour. |
| C9 | `mcp-server` and `web-sdk` declare **no licence** | No permission is implied. Analysis only; no copying, linking or redistribution. A missing licence is not a permissive one. |
| C10 | `optechai/nestjs-temporal` is MIT but © 2022 Zegue Kurt | It is a republished third-party library hosted in Lorikeet's org, not proven production code. The clone is shallow (one visible commit), so full history was not inspected. |
| C11 | `mcp-server@1.0.0` depends on `@lorikeetai/node-sdk ^0.13.1`; current SDK is 3.0.0 | The MCP package predates the current SDK by a major version and looks stale; do not read its README as current product documentation. |
| C12 | `@lorikeetai/react-sdk@1.0.0` returned HTTP 404 on npm (2026-11-18) | No inference about other React libraries or private packages. |

---

## 8. Reuse decision summary

| Source | Decision | Condition |
|---|---|---|
| Lorikeet node SDK | Reference only | Apache-2.0 NOTICE; do not copy API names into public Klaint API to avoid confusion |
| Lorikeet RN SDK | Reference only | MIT |
| Lorikeet `nestjs-temporal` | Not needed | MIT, but a generic third-party library; adopting it buys a Temporal dependency Klaint does not have |
| Lorikeet `mcp-server` package | **No reuse** | No licence field, no implementation shipped |
| Lorikeet `mcp-client` package | Reference only | ISC declared; keep notice; demo code only |
| Lorikeet `web-sdk` package | **No reuse** | No licence field; it is a loader for a hosted vendor iframe, not a reusable SDK |
| Parloa SDK/types | **Patterns + select type definitions** | Apache-2.0 NOTICE; generated code, no patent grant beyond license |
| Decagon Duet CLI | **No reuse** | Restrictive license; analysis only |
| Parlant | Conditional dependency/reference | Apache-2.0; never as trust boundary; pin + fork budget |
| Pipecat | **Adopt** | BSD-2-Clause notice |
| τ-bench | **Adopt harness** | MIT; add Arabic pack |
| Standard Webhooks | **Adopt** | Apache-2.0 |
| Rasa OSS | **Reject** | Maintenance mode |
| Chatwoot | **Adopt core** | MIT; exclude `enterprise/` |
| Wispral docs | **Incorporate** | Research-only; no product code exists |
