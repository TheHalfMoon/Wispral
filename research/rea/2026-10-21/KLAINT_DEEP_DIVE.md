# Klaint: conversation control, customer actions and human handoff

> V3 repair selection (Opus #125): current reuse modes/owners are in [SOURCE_TRANSPLANT_MATRIX.md](SOURCE_TRANSPLANT_MATRIX.md) and the [repair traceability](OPUS_REPAIR_TRACEABILITY.md). The original pinned source observations below remain valid; extraction-first selection/estimates are superseded where the current fork/API/contract boundary differs. No source identity or runtime result was discarded.

**Mission:** [Issue #122](https://github.com/TheHalfMoon/Wispral/issues/122). **Study date:** 2026-10-21. **Disposition:** research and transplant planning; no product implementation or production selection authorization. **Machine evidence:** [klaint-source-evidence.json](klaint-source-evidence.json).

The strongest qualified design candidate is **Parlant for a bounded conversation service, Chatwoot for an optional human inbox, and selected Botpress connectors for business-system adapters**. Keep one Wispral Core action-authority boundary between conversation inference and external side effects. Rasa is a useful inspectable alternative, but adopting it alongside Parlant would duplicate dialogue state and introduce an older Python/dependency envelope. These are source-based planning decisions, not measured runtime winners.

## Contents

1. [Evidence and rights](#evidence-and-rights)
2. [Source identities](#source-identities)
3. [Parlant execution trace](#parlant-execution-trace)
4. [Chatwoot account and handoff trace](#chatwoot-account-and-handoff-trace)
5. [Botpress connector trace](#botpress-connector-trace)
6. [Rasa alternative](#rasa-alternative)
7. [Lead-donor decisions](#lead-donor-decisions)
8. [Competitor observations](#competitor-observations)
9. [Transplant packets](#transplant-packets)
10. [Acceptance and experiment plan](#acceptance-and-experiment-plan)
11. [Residual gaps](#residual-gaps)

## Evidence and rights

`FOUNDER_SOURCE_AUTHORIZATION=YES_CONFIRMED_BY_FOUNDER`

`CONFIDENTIAL_GRANTS=HELD_PRIVATELY_BY_FOUNDER_NOT_SHARED`

The founder confirms existing permission to copy, use, modify, adapt and rename the supplied/authorized source. Confidential agreements were not requested or independently inspected. This study preserves upstream identity, revision, file hashes and public license boundaries. Rebranding does not erase provenance, attribution or applicable notices. Separate model weights, customer records, voices, media, trademarks and service entitlements are not inferred from source-code permission.

This audit fetched **102 actual source, test, manifest and license files** from four immutable revisions and traced relevant execution paths. The JSON records each attempted path, exact Git blob, SHA-256, source URL, named declarations and direct imports. Missing guessed paths are retained as `NOT_IN_PINNED_TREE`; they are not evidence that a feature is absent. The complete repository trees were available, but this is a selected module audit, not a line-by-line review of every file or a full transitive dependency security audit.

| Evidence class | What this study establishes | Limit |
| --- | --- | --- |
| `SOURCE_VERIFIED` | Captured source content, declarations, call paths, manifests and tests at the recorded SHAs | Source presence does not prove safe execution or feature quality |
| `DOCUMENTED` | Official competitor pages and technical documentation fetched on the study date | Provider claims remain unverified; no latency or resolution-rate number is adopted |
| `BLOCKED_EXTERNAL` | Ada marketing homepage returned HTTP 403; an old Intercom voice URL and a guessed Bland transfer page returned HTTP 404 | Alternative public official documentation was read; no bypass was attempted |
| `NOT_RUN` | Full donor applications, model inference, telephone calls, authenticated competitor workflows and upstream test suites | No test, security, portability, latency or tenant-isolation pass is claimed |

No paid inference, telephony, purchase, installation, customer-data access or donor-repository modification occurred. Fetching a public page is documentation research, not successful application use or REA of the authenticated workflow. The shared [REA methodology](REA_METHODOLOGY.md) and [evidence index](EVIDENCE_INDEX.json) own any separately performed REA/runtime observations; they must not be inferred from this source study.

## Source identities

| Donor | Exact inspected revision | Relevant declared runtime | Public source terms inspected | Planning role |
| --- | --- | --- | --- | --- |
| [emcie-co/parlant](https://github.com/emcie-co/parlant/tree/ea737442b8ae65854a842542e544fbe7e6144bad) | `ea737442b8ae65854a842542e544fbe7e6144bad` (`develop`) | `parlant` 3.3.1; Python `>=3.10,<3.15` | Apache-2.0 [LICENSE][p-license] | Lead conversation/guideline/journey service |
| [botpress/botpress](https://github.com/botpress/botpress/tree/4dbedde32c5947f2646a03f80421cfd786b8bcd9) | `4dbedde32c5947f2646a03f80421cfd786b8bcd9` (`master`) | SDK 7.2.8; Node `>=18`; pnpm 10.29.3 in SDK manifest | MIT [LICENSE][b-license] | Selective connector/HITL schema adaptation |
| [chatwoot/chatwoot](https://github.com/chatwoot/chatwoot/tree/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8) | `8006117055a0d4f9e6d6340a13f7ef5c33dfeec8` (`develop`) | Ruby 3.4.4; Rails 7.2.3.1; PostgreSQL/Redis dependencies | Root [LICENSE][c-license] gives MIT outside specified exceptions; [`enterprise/LICENSE`][c-enterprise-license] is distinct | Optional inbox/human takeover service |
| [RasaHQ/rasa](https://github.com/RasaHQ/rasa/tree/60a3cff9c08183760355b07bd60f5223d8916d6b) | `60a3cff9c08183760355b07bd60f5223d8916d6b` (`3.6.x`) | Rasa 3.6.21; Python `>=3.8,<3.11` | Apache-2.0 [LICENSE.txt][r-license] | Reference/alternative, not a second production dialogue engine |

Default branch identity is recorded, not treated as a stable release. Repository `pushed_at` can reflect work outside the default-branch commit; it is not a release-quality or maintenance score. Before adoption, select a tested release or requalify these exact sources and resolve locks/SBOMs independently.

## Parlant execution trace

### Actual preparation and tool path

The inspected path is:

```text
AlphaEngine.process(context, event_emitter)
  -> _load_context(agent/session/customer/history)
  -> return without automatic processing if session.mode == "manual"
  -> _do_process
  -> initialize response state, context variables, glossary/capabilities
  -> PlannerProvider.get_planner(...).create_plan(context)
  -> preparation iterations
     -> load/match guidelines and journeys
     -> split ordinary vs. tool-enabled guidelines
     -> ToolEventGenerator.infer_tool_calls
     -> Plan.on_tools_inferred(context, inference_result)
     -> ToolEventGenerator.execute_tool_calls
     -> ToolCaller.execute_tool_calls -> _run_tool
     -> registered ToolService.call_tool(...)
  -> message generation, event emission, trace/health observations
```

This trace is anchored in [`AlphaEngine.process`][p-engine], [`Plan`/`NullPlan`][p-planners], [`ToolEventGenerator`][p-tool-events] and [`ToolCaller._run_tool`][p-tool-caller]. The engine catches `asyncio.CancelledError`; the trace does **not** prove that cancellation rolls back an external action already committed by a tool service.

The important reusable boundary is the **tool proposal before execution**. `Plan.on_tools_inferred` can filter/reorder inferred calls. `NullPlan.on_tools_inferred` merely flattens the inferred batches. `ToolCaller._run_tool` resolves a registered service and invokes `service.call_tool` with the generated arguments. Therefore the default engine is not a complete Wispral action-authority gate. A custom plan is useful, but enforcement must also sit in the registered brokered `ToolService`, so another engine path cannot bypass it. [`ToolContext`][p-tools] carries agent/session/customer IDs and plugin data; these are context fields, not authenticated tenant authority.

Guideline matching is explicitly probabilistic: [`GenericActionableGuidelineMatchingBatch.process`][p-actionable] calls `SchematicGenerator.generate` and interprets structured checks. Existing tests cover relevant/irrelevant matching, contradictory guidelines, retry/failure conditions, required/invalid tool arguments and confirmation-sensitive scenarios. Their existence is valuable source material; none was run in this study. In particular, source tests named for consequential tools are not evidence that model-mediated confirmation satisfies a deterministic transaction authorization contract.

### Selective reuse

Reuse `Guideline`/`Journey`/`ContextVariable` entities and the existing engine through a Python adapter, preserving the upstream package boundary. Do not translate the conversation engine into Rust or copy `engine.py` alone. Its immediate dependency surface includes entity queries, session stores, NLP services, planners, glossary, relational resolution, tool services, hooks, tracing and persistence. The JSON contains direct import inventories, not a claim that this entire closure has been audited or reduced to a self-contained file.

The proposed adapter exposes versioned `ConversationInput`, `ConversationEvent` and **unprivileged** `ActionProposal` messages to Wispral Core. A brokered tool service receives only the outcome of deterministic authority evaluation and tenant-bound credentials. The dialogue worker must not hold general CRM credentials or manufacture an authorized principal from customer utterances. Per-tenant worker/storage isolation is the narrow starting topology until shared-process isolation is independently demonstrated.

### Session, privacy and API boundaries

[`Session` and `SessionDocumentStore`][p-sessions] preserve agent/customer identity and event history; [`SessionModule`][p-session-module] manages session work/listeners, and the [session API][p-session-api] exposes explicit event sources, manual/auto mode, status and event streaming. Preserve raw customer messages separately from rewritten assistant text, tool events and human-agent messages. Map upstream event identity to one Wispral journal instead of creating two unrelated product audit stores.

The inspected [`authorization.py`][p-auth] provides extensible operation authorization and rate-limit hooks. Its development policy permits all operations; its production policy is a default operation allowlist and is not evidence of authenticated tenant ownership checks. `AuthorizationException` includes request headers in its formatted message. A Klaint deployment must supply principal/ownership enforcement, origin policy, trusted-proxy configuration and redaction before exposing this service. Do not copy the development policy or treat default production naming as security certification.

`ContextVariableStore.GLOBAL_KEY` is a default-key mechanism, not a multi-tenant identity boundary. Context values, customer mapping, glossary, knowledge, cached retrieval and logs must all be scoped to the authenticated tenant and permitted purpose. A guessed session/customer ID cannot become access authority. Model/provider outages must return visible unavailable outcomes without silently changing retention or sending data to another provider.

### Dependencies, tests and costs

[`pyproject.toml`][p-manifest] declares FastAPI/Starlette, Pydantic-related tooling, HTTP clients, MCP/FastMCP, OpenTelemetry, graph/vector support, OpenAI client support and a separately versioned `parlant-client` Git dependency. It has optional provider extras including Ollama. This supports an inspectable adapter hypothesis; it does not establish adequate local-model quality, absence of network traffic, or zero inference cost in a configured deployment.

Port the useful contract fixtures from `tests/core/stable/engines/alpha/test_tool_caller.py`, `test_guideline_matcher.py`, API sessions tests and journey tests into a bounded integration suite with fake tools first. Some existing semantic tests exercise a model; do not run those with paid providers or count skipped model-dependent tests as passing. Before any install, resolve/pin the complete lock and qualify install scripts, transitive packages, provider SDKs and enabled telemetry/exporters.

## Chatwoot account and handoff trace

### Authenticated account to assignment

The concrete assignment path is:

```text
Accounts::BaseController -> EnsureCurrentAccountHelper
  -> user account membership or bot account/inbox access
Conversations::BaseController#conversation
  -> Current.account.conversations.find_by!(display_id: ...)
  -> authorize @conversation, :show?
AssignmentsController#create -> set_agent / set_team
  -> Conversations::AssignmentService#perform
     -> assign_agent: with_lock, set human, clear AI owner, save
     -> assign_agent_bot: with_lock, clear human, set AI owner, pending, save
```

The account helper, conversation controller and [assignment service][c-assignment] provide actual tenant/handoff mechanisms worth reusing **inside their Rails boundary**. The service looks up human assignees through `conversation.account.users`; bot lookup uses `AgentBot.accessible_to(conversation.account)`. [`ConversationPolicy`][c-policy] checks administrator, agent-bot and inbox/team access. [`AgentBot.accessible_to`][c-bot] also permits system bots with no account; explicitly map/allowlist those when connecting multiple Klaint tenants.

On takeover of a bot-owned pending conversation, `assign_agent` opens it, sets the waiting clock if needed and clears AI ownership. The [assignment tests][c-assignment-tests] check this behavior and ordinary status preservation. Request tests cover unauthenticated/inbox access cases. The code uses database locking for assignment, but this study did not run concurrent requests or verify deployment configuration.

### Distinct handoff mechanisms

[`Conversation#bot_handoff!`][c-conversation] explicitly describes its eligibility check as best-effort, **not a lock against concurrent takeovers**. Do not use it as a synchronization primitive. Conversation/inbox assignment also does not perform a PSTN/SIP warm transfer. The product needs separate states for:

- AI stops replying and a human takes ownership of the inbox conversation;
- a voice leg transfers to a human destination and that destination answers;
- a summary/verified context is delivered to the human with the correct authorization scope;
- a human explicitly returns ownership to AI, if allowed.

Use one handoff ID and ownership epoch across these states. A successful assignment HTTP response cannot be displayed as a successful telephone transfer. A failed/unanswered transfer must retain a recoverable queue/callback state and keep customer-visible failure information accurate.

### Signed webhook and recovery path

[`AgentBotListener`][c-listener] constructs events and schedules `AgentBots::WebhookJob` with the bot secret and a delivery UUID. [`Webhooks::Trigger`][c-trigger] posts through `SafeFetch`; it emits `X-Chatwoot-Delivery`, a timestamp, and an HMAC-SHA256 signature over `timestamp.body` when a secret exists. The job retries selected failures; the trigger can reopen a pending conversation after eligible bot delivery failures, unless account configuration says to keep it pending. These are useful implementation seams and negative-test fixtures.

Adapt the receiver to validate **raw bytes**, timestamp skew, constant-time signature comparison, secret version and delivery replay before accepting an event. A duplicate/retried webhook must not duplicate a refund or ticket. Upstream header construction is not the receiver implementation. Secret-at-rest encryption is conditional on Chatwoot encryption configuration; `WebhookSecretable` is not proof that a particular installation configured it. Failure logging and diagnostic payloads need redaction.

The inspected `spec/lib/webhooks/trigger_spec.rb` covers signing/delivery headers, selected HTTP retry/failure behavior and blocked private webhook targets. Preserve those as donor tests and add receiver-side replay/tamper/tenant tests. No webhook was sent in this study.

### Deployment and license boundary

Run an optional qualified Chatwoot instance out of process and integrate through account-scoped APIs/webhooks. Rails models depend on ActiveRecord, database constraints, callbacks, concerns, jobs, Pundit policies and front-end state. Copying a model into the Rust core would lose those semantics and create a second inbox engine.

The [root license][c-license] expressly separates `enterprise/`, third-party portions and MIT-covered content. [`enterprise/LICENSE`][c-enterprise-license] has subscription/other-agreement terms; the founder's additional grants are confirmed privately, not independently inspected. Keep selected ordinary-source paths and every enterprise dependency/hook provenance explicit. Do not silently describe the whole repository as MIT. `prepend_mod_with`/`include_mod_with` hooks appear in inspected ordinary paths: inventory the actual enabled composition before distribution and do not infer enterprise-free closure solely from an ordinary file's path.

## Botpress connector trace

### What is actually available

The pinned [`readme.md`][b-readme] says the repository contains public integrations, CLI/SDK/API client tooling and example bots; its example bots are not a replacement for Botpress Studio. This source is **not evidence that the complete Botpress Cloud runtime or hosted Studio is available to transplant**. [`packages/client/src/common/config.ts`][b-client-config] defaults to `https://api.botpress.cloud`, reads BP environment configuration and builds authentication/context headers. Copying that client does not create a local Botpress service.

The SDK's [`IntegrationImplementation`][b-integration] connects register/unregister, webhook, actions and channels to its integration handler/server. Actual connectors also import generated `.botpress` definitions and shared workspace packages. Reuse selected business API logic and schemas after replacing these platform-specific bindings; do not fork the entire Cloud-oriented SDK merely to support one CRM connector.

### Zendesk: concrete mutation and human handoff

[`createTicket`][b-zendesk-create] gets a configured Zendesk client and calls `createTicket`. [`ZendeskApi`][b-zendesk-client] uses Axios, OAuth credentials and retry handling. [`startHitl`][b-zendesk-hitl] depends on Botpress users and conversations, creates a Zendesk ticket with a transcript, and links the external ticket and Botpress conversation. `stopHitl` updates ticket status. These functions provide working source structure for a Klaint adapter, but their generated types, client state and identity mapping must be adapted.

Extract ticket schemas/API calls/OAuth handling and transcript conversion into `adapters/connectors/zendesk/`, behind the Wispral action broker. Replace `.botpress` context/client with a tenant-scoped connector installation and explicit idempotency record. Timeout after a successful POST is an **unknown commit outcome**, not permission to retry a mutation blindly. Test safe retry/reconciliation, revoked tokens, foreign requester IDs, malicious tenant payloads and redacted errors.

### HubSpot and reusable HITL interface

[`validateHubSpotSignature`][b-hubspot-signature] computes HMAC-SHA256 and uses `timingSafeEqual`. Its observed age check rejects timestamps when `Date.now() - parseInt(timestamp)` is too large. The selected adaptation must also reject nonnumeric and excessively future timestamps and track replay; do not label this source function a complete replay defense. No exploit or live webhook test was performed.

The [HITL interface definition][b-hitl] and `integrations/zendesk-messaging-hitl/src/events/switchboard-release-control.ts` supply concrete start/stop and release-control schemas. They are useful for the portable handoff contract after removing Botpress type/client assumptions. Context-preserving assistant transfer, human inbox ownership and phone warm transfer remain separate contracts.

### Dependencies and tests

The SDK manifest declares `@botpress/client`, `browser-or-node`, `semver` and a `@bpinternal/zui` peer. HubSpot additionally uses `@hubspot/api-client`, shared common code and generated types; Zendesk uses Axios/retry and OAuth helpers. The integration build uses `bp add`/`bp build`, which is not a pure standalone TypeScript compile. The donor's pnpm workspace and generated artifacts must be fully accounted for in the transplant packet.

Inspected test files include chat ID-store tests and Zendesk OAuth subdomain parsing tests. These are not comprehensive mutation/identity/retry tests. Broader donor test paths and Vitest configurations were inventoried, but no suite ran. Before adopting packages, perform dependency/install-script qualification and resolve an exact lock; this study does not certify npm package safety.

## Rasa alternative

The [README][r-readme] explicitly puts Rasa Open Source in maintenance mode and distinguishes the newer Hello Rasa/CALM offerings. Do not infer that code for the new commercial platform is contained in this revision.

The concrete reusable mechanisms are:

- [`DialogueStateTracker`][r-trackers]: event-derived conversation state, replay, paused/loop state, snapshot/copy and event-difference mechanisms;
- [`RulePolicy`][r-rules]: rule/action prediction, restrictions and contradiction/incomplete-rule checks inside the Rasa domain/featurization model;
- [`LockStore`][r-locks]: conversation-keyed ticket locks with lifetime, acquisition, cleanup and in-memory/Redis implementations;
- [`MessageProcessor`][r-processor]: logs utterances, extracts slots, runs prediction/actions, enforces an action-loop limit and saves the tracker.

These are substantive alternatives. They are not drop-in Rust components and a dialogue rule match is still not identity verification or authorization for an external transaction. Sender/conversation IDs require tenant-bound namespacing. The Python `>=3.8,<3.11` and older dependency constraints in the inspected [`pyproject.toml`][r-manifest] are materially different from Parlant's runtime envelope. Do not merge both into one Python environment or operate two authoritative conversation engines.

**Decision:** retain Rasa as `REFERENCE_ONLY` for rule/replay/lock design and regression fixtures. Reopen it only if a bounded customer dialogue requirement cannot be provided by the selected Parlant service plus the existing deterministic Core boundary. If reopened, compare isolated implementations on the same frozen task set before replacing a lead donor. No evidence currently justifies copying a second entire engine.

## Lead-donor decisions

| Layer | Lead and reuse mode | Alternatives considered | Why this decision is bounded | Measurable next step |
| --- | --- | --- | --- | --- |
| Guided conversation and journeys | Parlant `OUT_OF_PROCESS`/`WRAP` | Rasa, unavailable complete Botpress Cloud runtime | Actual guideline/journey/tool event flow is available; one replaceable dialogue service | Synthetic multi-turn return/refund scenario with fake tools and ordered traces |
| Consequential action authority | Wispral Core broker; adapt Parlant tool service seam | Parlant default plan, Rasa prediction, provider guardrails | None of inspected paths provides Wispral's complete tenant/identity/approval/idempotency/cancellation envelope | All denied/stale/substituted/cross-tenant fixtures execute zero mutations |
| Customer inbox and human ownership | Chatwoot `OUT_OF_PROCESS` | Rebuilding inbox, copying individual Rails models | Existing account/inbox assignment and event mechanisms; keep their dependency boundary | Bot-to-human takeover with duplicate webhook and concurrent ownership tests |
| CRM/helpdesk connector implementation | Selected Botpress Zendesk/HubSpot files `ADAPT` | Full Botpress SDK/runtime, new connectors from scratch | Preserve actual API/schema/OAuth code and replace Cloud bindings | Fake API verifies identity, unknown-commit reconciliation, retry and token revocation |
| Realtime voice transport | Shared Core donor selection; do not create Klaint-specific audio engine | LiveKit Agents, Pipecat, hosted providers | Conversation/action layer remains independent of STT/TTS/WebRTC/SIP | Full turn/barge-in/transfer tests attached to Core evidence, not assumed here |
| Session/audit representation | Parlant event mapping into Wispral journal | Separate proprietary/CRM-specific audit databases | Keep raw speech, inference, verified identity and action receipt distinguishable | Replay one turn and explain each side effect without exposing credentials |
| Evaluations | Adapt Parlant scenario fixtures; own independent frozen scorer | Marketing resolution-rate claims, LLM-only pass judgment | Judge tool outcomes and authorization deterministically; semantic judge is advisory | Compare expected action receipts, human handoff state and supported-language task success |

These decisions maximize reuse of implemented mechanisms while avoiding three full incompatible application stacks in the Core. The integration glue is not a blanket greenfield exception: every new authority/tenant/idempotency field must first be compared with the qualified Core/founder donors. The source-based reasons above justify only missing **cross-donor contracts and enforcement**, not a new conversation engine, inbox, speech stack or connector framework.

The founder's requested 20/20/15/15/10/10/5/5 rubric belongs in the consolidated decision matrix. For this study, measured quality, p50/p95 latency, Arabic quality and deployed security remain `NOT_MEASURED`; do not assign zero or renormalize that missing 15% into a false empirical winner. A higher weight on local footprint may favor a smaller deterministic scenario path over either full service. A higher weight on ready-made inbox functionality increases Chatwoot's value but does not make Rails appropriate inside Core. Runtime experiments may change these provisional leads.

## Competitor observations

All rows below are **`DOCUMENTED`; authenticated workflows, phone calls, latency and quality tests are `NOT_RUN`**. The machine evidence preserves requested/resolved URLs, capture time, response status and content SHA-256. No broad proprietary source permission is inferred.

| Reference | Concrete official evidence read | Capability it sets for Klaint | Gaps this study cannot settle |
| --- | --- | --- | --- |
| [Decagon Voice](https://decagon.ai/product/voice) | Public voice product page | Talk while actions progress, interruption/backtracking, language switching, brand voice, summary with human transfer, outbound calls, AOP guardrails | Actual language accuracy, action authority, latency, transfer failure behavior and tenant isolation |
| [Sierra Agent Studio](https://sierra.ai/product/agent-studio) | Public product page | Composable journeys, tool/data integration, decision/tool/response traces, simulations/regression tests, voice noise/speaker simulation | Runtime control semantics, test reproducibility, local operation and deployment economics |
| [Ada documentation](https://docs.ada.cx/docs/welcome) | Official docs and docs index; marketing homepage returned 403 | Knowledge-grounded agent management; documented tools/processes/playbooks/variables/persona and evaluation surfaces | No authenticated dashboard or customer support workflow; landing/index presence is not feature verification |
| [Intercom Fin](https://fin.ai/) and [Fin Voice](https://fin.ai/voice) | Supplied Intercom URL redirected to official `fin.ai`; voice page read | Procedures, read/write integrations, simulations/evals, cross-channel monitoring, call forwarding/SIP, configurable human transfer/callback | No accepted marketing resolution rate or superiority result; actual action verification/phone recovery untested |
| [Retell introduction](https://docs.retellai.com/general/introduction) and [transfer tool](https://docs.retellai.com/build/single-multi-prompt/transfer-call) | Technical docs | Single-prompt/conversation-flow agents, phone/SIP/web, live monitoring/takeover, CRM sync, warm-transfer configuration | Actual PSTN/SIP behavior, timeout/voicemail failure recovery, Arabic and interrupted tool outcomes |
| [Vapi introduction](https://docs.vapi.ai/quickstart/introduction) and [handoff tool](https://docs.vapi.ai/squads/handoff) | Technical docs | Replaceable STT/LLM/TTS providers, Assistants/Squads, phone/web, version restore, simulation and context-bearing transfers | A squad transfer is not automatically a human handoff; published latency claims remain unmeasured |
| [Bland docs](https://docs.bland.ai/welcome-to-bland) | Official welcome and docs index; docs warn of an ongoing platform/docs transition | Pathways, testbed/scenarios/evals, webhook signing, SIP and warm-transfer surfaces | Precise current/legacy API compatibility, phone performance and safety claims unverified |
| Parlant / Botpress / Chatwoot / Rasa | Immutable code and selected tests above | Open mechanisms for conversation, connectors, inbox ownership and replay | No claim of integrated parity, tested enterprise readiness or production support |

### Grounded priorities and advantage hypotheses

**P0:** identity-bound actions, tenant separation, reliable bot-to-human ownership, a full trace with redacted secrets, and replayable failure recovery. Donor code directly exposes the seams required to test these. **P1:** realtime barge-in, actual warm telephony transfer, Arabic/Gulf dialect and English code switching, constrained CRM operations and per-channel permission policy. **P2:** visual journey authoring, large connector catalogues, production QA analytics, outbound campaigns and broader channel expansion after their business/consent/cost controls are qualified.

Potential advantages are **hypotheses to test**: a useful local/BYOK route, explicit action receipts and unknown-commit recovery, independently reproducible English/Arabic control tests, and transparent human/AI ownership across channels. The present repository does not have those product capabilities and cannot claim it exceeds any competitor.

## Transplant packets

The JSON contains twelve line-anchored units (`K01`–`K12`) with source SHA/file/hash, dependency boundary, destination, reuse mode, donor tests, required integration tests, risks and rights. These are candidate paths for the later implementation Grain, not new product files added by this research PR.

| Packet | Exact implementation seam | Proposed destination/mode | Order and bounded outcome | Rollback |
| --- | --- | --- | --- | --- |
| K01 | `parlant/core/engines/alpha/engine.py::AlphaEngine.process` | `services/klaint-dialogue/parlant_adapter.py`; `OUT_OF_PROCESS` | After governance/Core contracts, replay one synthetic text session through the original engine with fake tools | Disable adapter and retain input/journal; remove no existing speech path |
| K02 | `guidelines.py::Guideline`, `journeys.py::Journey`, `context_variables.py::ContextVariable` | `services/klaint-dialogue/policy_content/`; `WRAP` | Add one versioned policy/journey package and scoped freshness rules | Revert package version without rewriting historical events |
| K03 | `planners.py::Plan.on_tools_inferred`, `tools.py::ToolService`, `tool_caller.py::_run_tool` | `services/klaint-dialogue/brokered_tool_service.py`; `ADAPT` | Tool proposes; deterministic Core broker authorizes exact principal/tool/arguments/expiry before mutation | Deny all actions while text-only conversation remains available |
| K04/K12 | `sessions.py::SessionDocumentStore`, API session modes and `authorization.py` | `session_bridge.py` / `tenant_authorization.py`; `WRAP`/`ADAPT` | Enforce tenant-scoped read/write and manual takeover; redact exception headers | Stop exposed listener, preserve authorized journal and explicit failed session state |
| K05/K07 | Chatwoot `AssignmentsController`, `AssignmentService`, `Conversation#bot_handoff!` | `integrations/chatwoot/`; `OUT_OF_PROCESS` | Human takeover with one owner epoch; phone transfer still separate | Detach inbox bridge, expose manual queue/callback fallback |
| K06 | `AgentBotListener`, `AgentBots::WebhookJob`, `Webhooks::Trigger#request_headers` | `integrations/chatwoot/webhook_bridge/`; `ADAPT` | Signed, replay-resistant delivery with failure recovery and redacted logging | Revoke/rotate connector secret and drain pending deliveries without duplicate mutation |
| K08 | Botpress Zendesk `createTicket`, `startHitl`, `ZendeskApi` | `adapters/connectors/zendesk/`; `ADAPT` | One read-only lookup then separately gated ticket mutation; fake API first | Revoke connector credentials and reconcile uncertain commit IDs |
| K09 | HubSpot `validateHubSpotSignature`, action/HITL module | `adapters/connectors/hubspot/`; `ADAPT` | Qualify HMAC, finite symmetric timestamp skew and replay; no real CRM writes in first test | Disable installation and rotate token/secret |
| K10 | `interfaces/hitl/interface.definition.ts` | `contracts/klaint/handoff/`; `ADAPT` | Contract distinguishes ownership, assistant transfer, phone transfer and failure/return | Version adapter back; reject unknown contract version |
| K11 | Rasa tracker/rule/lock/processor files | `research/reference/rasa/`; `REFERENCE_ONLY` | No runtime import unless an independently scoped unmet requirement reopens comparison | No installed runtime to remove |

Do not estimate a reuse percentage from repository line counts. The available implemented source is substantial, but the final dependency closure and integration code volume are not measured. Estimate developer effort only after the first brokered-session compatibility experiment; the Rust/Python/TypeScript/Rails boundary costs are real even when copying is legally authorized.

## Acceptance and experiment plan

### First useful Klaint slice

After the governance amendment and a bounded first implementation Grain are qualified, start with **one tenant, one text channel, one synthetic support journey, fake order lookup, a separately authorized mock refund and explicit human inbox takeover**. Add voice through the shared Core adapter only after the action/handoff contract works. This proves a customer-agent product seam without waiting for SIP, a visual builder or every CRM.

Prerequisites: pinned source/package closure and notices; versioned Core events; authenticated principal and tenant mapping; brokered tool registration with no direct credential path; deterministic fixture server; redacted journal; explicit session/manual/ownership/cancellation states. The historical B2R17 work and its claim guards remain independent.

### Independent functional and adversarial cases

| Family | Success fixture | Failure/recovery fixture | Boundary/permission fixture |
| --- | --- | --- | --- |
| Parlant conversation | Synthetic customer asks order status; approved fake lookup returns grounded result | Model timeout, contradictory knowledge and malformed tool arguments produce visible recovery | A refund request before identity verification makes zero mutations; guessed foreign session/customer ID denies |
| Chatwoot inbox | Bot conversation assigned to authorized human with transcript/summary | Duplicate webhook, selected 429/500 retries, missing human destination and bridge restart | Cross-account inbox/assignee rejected; stale AI epoch cannot reply after human takeover |
| Botpress-derived connector | Fake Zendesk/HubSpot request round-trips inspected schema | Timeout after POST commit, invalid OAuth refresh and 429 are reconciled without duplicates | Model-supplied account/domain/credential overrides rejected; tampered/stale/future/nonnumeric signed requests deny |
| Rasa comparison if reopened | Frozen rule and tracker fixture returns expected action | Contradictory/incomplete rules and expired lock fail visibly | Sender ID cannot cross tenant; do not introduce shared authoritative state with Parlant |
| Decagon / Sierra / Ada / Fin | Authorized test tenant runs one synthetic return/support case | Tool outage, conflicting facts and failed handoff replay | Identity/tenant boundary plus transcript redaction; outcome `NOT_RUN` until actual captured workflow |
| Retell / Vapi / Bland | Authorized no-cost web/phone test, only if already available | Interrupt during action, transfer unanswered/voicemail and transport drop | Consent/recording notice, no unsolicited call, no unapproved spend or personal voice cloning |

Do not create new paid test tenants or dial real customer phone numbers. Public demo UI discovery is not a call trial. If a no-cost authenticated/hardware route is unavailable, retain `NOT_RUN` with the exact access/hardware prerequisite and continue independent source work.

### Proposed reproducible checks, not executed results

In a separately qualified donor checkout and dependency environment, donor test selections include:

```text
rtk proxy python -m pytest tests/api/test_sessions.py
rtk proxy python -m pytest tests/core/stable/engines/alpha/test_tool_caller.py
rtk proxy python -m pytest tests/core/stable/engines/alpha/test_guideline_matcher.py
rtk proxy bundle exec rspec spec/services/conversations/assignment_service_spec.rb
rtk proxy bundle exec rspec spec/controllers/api/v1/accounts/conversations/assignments_controller_spec.rb
rtk proxy bundle exec rspec spec/lib/webhooks/trigger_spec.rb
```

These commands were **NOT_RUN** and need the respective full repository, exact dependencies, fixture services and safe provider configuration. Do not execute model-dependent donor tests against a paid provider. Botpress tests require its workspace/generated bindings; first port the selected deterministic connector fixtures into a small qualified harness. Running a disconnected pure-function copy would not prove the integrated connector works.

At Wispral integration level, keep the independent scorer outside the dialogue worker. Evaluate exact tool/action receipts, tenant identity, state transitions, number of external mutations, owner epoch, cancellation request/ack/stopped distinctions and whether failure disclosure was accurate. An LLM judge may help assess phrasing/semantic preservation; it cannot approve security outcomes or replace deterministic assertions.

### Benchmarks and language coverage

Predeclare synthetic fixtures separately from consented human speech. Include English, Modern Standard Arabic, Saudi/Gulf dialect, code switching, different speakers, interruptions, long pauses, background noise, noisy telephone audio and customer anger/escalation. No human-language or accent claim is authorized by synthetic tests alone.

Record STT finalization and meaning distortion separately from dialogue latency, tool commit latency and TTS first audio. Capture cold/warm p50/p95, successful/failed denominators, transfer-answer time, cancellation-to-audio-suppression, action authorization failures, tenant leakage attempts, resource RSS/CPU/GPU and provider/telephony costs. **All are `NOT_MEASURED` here.** Do not quote vendor latency/resolution-rate marketing as a comparative result. Use controlled machines and the same frozen scenario/configuration for comparisons, and preserve losing/timeout outcomes.

## Residual gaps

- No four-donor integrated build, deployment, upstream test execution or customer-agent runtime was performed; integration readiness remains to be established.
- Full lockfile/SBOM/native-artifact closure, install scripts, enabled enterprise hooks, external services and production security configuration are not independently qualified.
- Source shows useful cancellation/manual/handoff seams, but real in-flight tool cancellation, duplicate action recovery and phone transfer behavior remain unobserved.
- Multi-tenant isolation, model/policy adherence, local LLM viability, Arabic/Gulf quality and performance cannot be concluded from the source trace.
- Proprietary competitors were studied through official public documentation only in this sub-study. Actual successful, failure/recovery and boundary workflows require authorized no-cost access and proper fixtures; no account or paid entitlement was invented.
- Brand/domain/trademark clearance is not asserted. The final product name is **Klaint**; the shared platform remains **Wispral**, with **WisprStudio** and **WisprSide** as the other final names.

The next bounded research experiment is a pinned **brokered Parlant session with fake tools and one Chatwoot handoff contract**, selected only after repository governance opens that Grain. The decision to reuse these sources is already concrete; their safe integrated runtime behavior still requires evidence.

[p-license]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/LICENSE
[p-manifest]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/pyproject.toml
[p-engine]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/core/engines/alpha/engine.py#L190
[p-planners]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/core/engines/alpha/planners.py
[p-tool-events]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/core/engines/alpha/tool_event_generator.py#L157
[p-tool-caller]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/core/engines/alpha/tool_calling/tool_caller.py#L266
[p-tools]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/core/tools.py#L83
[p-actionable]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/core/engines/alpha/guideline_matching/generic/guideline_actionable_batch.py#L97
[p-sessions]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/core/sessions.py
[p-session-module]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/core/app_modules/sessions.py
[p-session-api]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/api/sessions.py
[p-auth]: https://github.com/emcie-co/parlant/blob/ea737442b8ae65854a842542e544fbe7e6144bad/src/parlant/api/authorization.py
[b-license]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/LICENSE
[b-readme]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/readme.md
[b-client-config]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/packages/client/src/common/config.ts
[b-integration]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/packages/sdk/src/integration/implementation.ts
[b-zendesk-create]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/integrations/zendesk/src/actions/create-ticket.ts
[b-zendesk-client]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/integrations/zendesk/src/client.ts
[b-zendesk-hitl]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/integrations/zendesk/src/actions/hitl.ts
[b-hubspot-signature]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/integrations/hubspot/src/hitl/utils/signature.ts
[b-hitl]: https://github.com/botpress/botpress/blob/4dbedde32c5947f2646a03f80421cfd786b8bcd9/interfaces/hitl/interface.definition.ts
[c-license]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/LICENSE
[c-enterprise-license]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/enterprise/LICENSE
[c-assignment]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/app/services/conversations/assignment_service.rb
[c-assignment-tests]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/spec/services/conversations/assignment_service_spec.rb
[c-policy]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/app/policies/conversation_policy.rb
[c-bot]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/app/models/agent_bot.rb
[c-conversation]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/app/models/conversation.rb
[c-listener]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/app/listeners/agent_bot_listener.rb
[c-trigger]: https://github.com/chatwoot/chatwoot/blob/8006117055a0d4f9e6d6340a13f7ef5c33dfeec8/lib/webhooks/trigger.rb
[r-license]: https://github.com/RasaHQ/rasa/blob/60a3cff9c08183760355b07bd60f5223d8916d6b/LICENSE.txt
[r-readme]: https://github.com/RasaHQ/rasa/blob/60a3cff9c08183760355b07bd60f5223d8916d6b/README.md
[r-manifest]: https://github.com/RasaHQ/rasa/blob/60a3cff9c08183760355b07bd60f5223d8916d6b/pyproject.toml
[r-trackers]: https://github.com/RasaHQ/rasa/blob/60a3cff9c08183760355b07bd60f5223d8916d6b/rasa/shared/core/trackers.py
[r-rules]: https://github.com/RasaHQ/rasa/blob/60a3cff9c08183760355b07bd60f5223d8916d6b/rasa/core/policies/rule_policy.py
[r-locks]: https://github.com/RasaHQ/rasa/blob/60a3cff9c08183760355b07bd60f5223d8916d6b/rasa/core/lock_store.py
[r-processor]: https://github.com/RasaHQ/rasa/blob/60a3cff9c08183760355b07bd60f5223d8916d6b/rasa/core/processor.py

## Opus S3/S4 correction: Parlant safety and quality reuse

Retain one Parlant Python service, tenant-scoped brokered ToolService and restrictive Plan. Reuse CannedResponse/CannedResponseGenerator (including CANNED_STRICT), retrievers and evaluation APIs at the same ea737442 pin; exact source records K13–K15 are in opus-repair-source-evidence.json. Use approved templates for policy/price/action commitments; a success template is permitted only after the broker records the actual committed outcome. A model choosing an allowed template is not action authorization. Preregister 100 adversarial commitment prompts and deterministic outcome expectations; this runtime/model panel remains NOT_RUN. Tenant-bound retrieval returns cited versioned documents and cannot select another tenant index; injection/stale/missing knowledge leads to uncertainty/handoff. Parlant evaluations drive scenarios but do not replace deterministic action scoring.

Chatwoot remains unmodified via Agent Bot API and authenticated webhooks; Klaint owns the AI epoch. K05–K07 are API references, not copied Rails. Botpress schemas inform bounded Python connectors; no Node service is selected. Pipecat is the only later realtime framework inside the same service; LiveKit Agents is REFERENCE_ONLY. Rust/Python policy equivalence needs common fixture verdicts before any binding/port is accepted. No new model training, cloud fallback or paid provider is enabled.
