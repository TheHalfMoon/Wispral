# Klaint: donor qualification, drift, competitors, threats and work packets

**Study date:** 2026-11-08. **Mission:** Wispral master plan, Klaint pillar (customer-facing conversational agents: text MVP, then voice).
**Builds on:** `pr124:research/rea/2026-10-21/KLAINT_DEEP_DIVE.md`, `source-transplants.json` (K01–K12), `opus-repair-source-evidence.json` (K13–K15), and the Opus review `pr125:research/reviews/2026-10-21-opus-pr124/INDEPENDENT_REVIEW.md` (S3: one Python service, Pipecat only, Chatwoot via API; S4: canned responses, retrievers, evaluations).
**Disposition:** research and planning only. Nothing was installed, run, deployed, signed in to or purchased. All GitHub access was read-only (tarballs and `gh api`).

## Evidence legend and limits

| Tag | Meaning in this report |
| --- | --- |
| `SOURCE_VERIFIED` | Read in the extracted donor tree or fetched blob. Cited as `repo@sha7:path:line`. Source presence does not prove the code runs safely. |
| `DOCUMENTED` | An official page or doc file states it. Competitor URLs were fetched 2026-11-08 by a research sub-agent through an automated page summarizer. Spot-check figures before quoting them externally. |
| `RUNTIME_OBSERVED` / `REPRODUCED` | **None in this study.** No donor code, test, model or call was executed. |
| `NOT_RUN` | A planned experiment or test that has not been executed. |
| `BLOCKED_EXTERNAL` | A fetch failed (HTTP error or empty page). |
| `REJECTED` | A candidate or design that was evaluated and not selected. The reason is given. |

**How the sources were obtained.** `git clone` fails in this scratchpad because the path exceeds Windows MAX_PATH. Parlant and Pipecat were therefore extracted from GitHub tarballs into `scratchpad\klaint\parlant` (tag v4.0.2, commit `2a463ccd`) and `scratchpad\klaint\pipecat` (tag v1.15.0, commit `fda1d5e0`), using `\\?\` extended paths. Selected Chatwoot files are in `scratchpad\klaint\chatwoot-files`. Their Git blob hashes match v4.19.1 (`caab07a8`), for example `lib/webhooks/trigger.rb` = `57d96f51` and `app/models/conversation.rb` = `335191af`. Botpress, tau2-bench, standard-webhooks and the other candidates were read with `gh api` only.

**Process note.** Three research sub-agents (Pipecat, Chatwoot/Botpress, other OSS) were interrupted by a usage limit and returned no report. Every Pipecat, Chatwoot, Botpress and OSS-candidate statement below comes from my own direct inspection after that point. The competitor sub-agent completed, and its URLs are listed in section 5.

---

## 1. Drift and re-pin decisions

| Donor | Prior pin | Current release / HEAD (2026-11-08) | Drift | Decision |
| --- | --- | --- | --- | --- |
| **emcie-co/parlant** (Apache-2.0) | `ea737442b8ae65854a842542e544fbe7e6144bad`. A develop commit from 2026-07-10, not a release. It diverged from v3.3.2 (51 commits ahead, 14 behind). | Release **v4.0.2** = `2a463ccd10eaf0d70d42731705f4f00ef066bee8` (2026-11-04). Tag v4.0.3 = `a071a81406e47b4a0ae3bfd448e4deb170ac2f4b`; it changes only dashboard CLI headers and tests. develop HEAD = `ee948e2a431486212faf5e2184bf42182e937757` (11 commits after v4.0.2). | **Breaking major release.** The pin is 95 commits behind v4.0.2, and one squashed commit, `87247c1e` "Parlant 4.0 release", rewrote the vocabulary. The CHANGELOG restarts at 4 and says the older entries describe an API "you can no longer call" (`parlant@2a463cc:CHANGELOG.md:5-9`). | **Re-pin to v4.0.2 `2a463ccd`, conditional on the KT-01 compatibility spike.** Keep **v3.3.2 `61bba3b2b3fffd677d345e393e8c942dbd400297`** as the documented fallback: the last 3.x release (2026-04-28), which still has `CANNED_STRICT`. Retire `ea737442`. v4.0.3 is runtime-equivalent and acceptable. |
| **pipecat-ai/pipecat** (BSD-2-Clause) | `9b0459b47675324843ffea17d90d8d3e422eb92c` (2026-10-21). The first release containing it is v1.14.0, which is 192 commits ahead and 0 behind. | Release **v1.15.0** = `fda1d5e0cde9625c8dcef7b653ed731c2ce63672` (2026-10-29). main HEAD `3dbb0c8445c0ddc2276d566140fe8d12f1d61e5b` is 456 commits after v1.15.0. | 495 commits from the pin to v1.15.0. v1.15 makes several ⚠️ turn-strategy changes: multiple stop strategies now must all agree (`stop_mode` defaults to ALL); `trigger_user_turn_*` is deprecated in favour of `report_*`; `EagerEndOfTurnCancelFrame` becomes `UserTurnResponseCancelFrame`; `deferred()` is deprecated. v1.14 adds Twilio API-key hang-up credentials and `redact_secrets` security fixes. (`DOCUMENTED`: release notes saved in `scratchpad\rel_v1.14.0.md` and `rel_v1.15.0.md`.) | **Re-pin to v1.15.0 `fda1d5e0`** for planning. Voice is phase 2: re-qualify against the latest release when KV-01 starts. Never pin main, given its churn rate. |
| **chatwoot/chatwoot** (MIT outside `enterprise/`) | `8006117055a0d4f9e6d6340a13f7ef5c33dfeec8` (2026-10-21) | Release **v4.19.1** = `caab07a8f00032d5205b5a5d7e2eb0ba2f3d2d82` (2026-10-24). develop `625d5964` has diverged from it (96 commits ahead). | 38 commits. Relevant to Klaint: `AgentBotInbox` now validates `ensure_exclusive_bot_provider`, so an Agent Bot cannot be active on an inbox that already has another bot provider, such as Captain (`chatwoot@caab07a:app/models/agent_bot_inbox.rb:17,27-30`). Also an enterprise `twilio_webhook_verification.rb` concern and enterprise conversation model changes. Webhook trigger and handoff code are unchanged: `trigger.rb` has the same blob on v4.19.1 and develop. | **Re-pin to v4.19.1 `caab07a8`.** Integrate through the API only. |
| **botpress/botpress** (MIT root) | `4dbedde32c5947f2646a03f80421cfd786b8bcd9` | master HEAD **`956bcdef7a8f6499519e28ec5dda6e3ed3c96ad8`**. The only GitHub "release", v12.30.9 (2023), is the legacy v12 and irrelevant. | 21 commits, touching only gmail, gsheets, teams, whatsapp, `packages/{cli,client,cognitive,llmz,sdk,vai,zai}` and `plugins/conversation-insights`. Nothing in zendesk, hubspot or `interfaces/hitl`. | **Reference only, at `956bcdef`.** No runtime adoption (Opus S3). |

### What the Parlant 4 rewrite does to prior packets

| Prior packet | Status at v4.0.2 | Replacement seam |
| --- | --- | --- |
| K01 `engines/alpha/engine.py::AlphaEngine.process` | **REMOVED.** The alpha engine is deleted (compare `ea737442...2a463ccd`). | Compass engine: `parlant@2a463cc:src/parlant/core/engines/compass/engine.py` (1,136 lines) and `loop/base_loop.py`. |
| K02 Guidelines/Journeys | **Journeys REMOVED**: `api/journeys.py` and `core/app_modules/journeys.py` are deleted. Guidelines become **rules** (`core/rules.py`, `core/app_modules/rules.py`). | "Procedures" are now policies written as step-by-step SOP text (`docs/policy-design.md:60-126`). This is LLM-followed text, not a state machine. |
| K03 `Plan.on_tools_inferred` | **REMOVED.** No `class Plan` or `on_tools_inferred` exists in `src`. | `on_reviewing_tool_calls` hook (RESOLVE/BAIL) plus the `ToolService` ABC. See §2.4. |
| K12 `AuthorizationException` leaks headers | **Fixed upstream.** `_safe_headers` redacts authorization, cookie, `*token*`, `*secret*` and `*key*` headers (`api/authorization.py:117-146`). | The remaining work is tenant and CORS configuration. |
| K13 `CANNED_STRICT` | **REMOVED.** Canned responses are now exemplars only. "The model always writes the final text itself" (`docs/canned-responses.md:457-461`). | An `on_message_generated` BAIL hook in BLOCK mode, plus tool-supplied literal responses and `field_dependencies`. See §2.5. |
| K14 Retrievers | Still present. The doc moved to `docs/retrievers.md`. | `sdk.py:1747-1790` (`RetrieverContext` / `RetrieverResult`). |
| K15 `api/evaluations.py` | **REMOVED** (`api/evaluations.py` and `core/app_modules/evaluations.py` deleted). Simulations moved to the hosted Dashboard. | An external harness (τ²-bench pattern). See §4 and KT-08. |

The REST CRUD routes for guidelines, journeys, glossary, context variables, services, tags, capabilities and canned responses were also removed (`api/*.py` deleted in the compare). In v4, configuration is code-first through `parlant.sdk`. The remaining REST surface is agents (read), customers, sessions/events, groups, health, debug and logs (§2.10).

---

## 2. Parlant v4.0.2 deep qualification (`emcie-co/parlant@2a463cc`)

### 2.1 License and package

- `SOURCE_VERIFIED` Apache-2.0 (`LICENSE`; `pyproject.toml:6` `license = "Apache-2.0"`). Python `>=3.10,<3.15` (`pyproject.toml:11`). Version 4.0.2 (`pyproject.toml:3`).
- `SOURCE_VERIFIED` Base dependencies include FastAPI/uvicorn, `openai>=3.26`, `fastmcp>=3.2`, `mcp`, OpenTelemetry API/SDK/OTLP exporter, `boto3`, `nano-vectordb`, `networkx`, `tokenizers`, `tiktoken`, `maxminddb` and `authlib` (`pyproject.toml:12-75`). Extras are `chroma`, `qdrant`, `mongo`, `anthropic`, `gemini` and `litellm` (`pyproject.toml:85-101`).
- **The Ollama extra from v3 is gone.** The sdist excludes `/pro` and `/tests/pro` (`pyproject.toml` `[tool.hatch.build.targets.sdist]`). No `pro/` directory exists in the public tree (`gh api contents/pro` returns 404).
- `DOCUMENTED` The Dashboard is a paid hosted product. The framework is "Apache-2.0 licensed" (https://www.parlant.io/pricing). "Compass Pro" voice is commercial and built on LiveKit (https://parlant.io/docs/compass-pro/overview).

### 2.2 Architecture and module map

| Concern | Path(s) at `2a463cc` | Notes |
| --- | --- | --- |
| Public SDK | `src/parlant/sdk.py` (5,188 lines) | `Server` (`:2966`), `Agent.create_policy` (`:1829`), `create_observation` (`:1904`), `create_canned_response` (`:1967`), `create_term` (`:1995`), `create_variable` (`:2024`), `Customer` (`:1578`), `Session` (`:2577`), `SessionAuthorization` (`:2528`), `SessionBudget` (`:2272`), `Group`, `Relationship`. |
| Agents | `core/agents.py`; `core/app_modules/agents.py` | `MessageOutputMode` = BLOCK, STREAM or VOICE (`core/agents.py:50-62`). `Effort` = MIN, LOW, MEDIUM, HIGH or MAX (`:66-74`). |
| Rules (policies, observations; formerly guidelines) | `core/rules.py`, `core/rule_representation.py`, `core/rule_tool_associations.py`, `core/app_modules/rules.py` | Matching runs in `core/engines/compass/matcher.py` (2,103 lines) and `matching/rule_recaller.py`, `rule_ranker.py`, `rule_pruner.py`, `evaluation_scheduler.py` and `rule_discovery.py`. Indexing proposers live in `core/services/indexing/rule_{signal,title,relativity}_proposer.py`. Matching is LLM- and embedding-mediated, so it is probabilistic. |
| Journeys | **None** | Replaced by procedure-style policies (`docs/policy-design.md:60-126`). |
| Glossary | `core/glossary.py`, `core/app_modules/glossary.py`, `engines/compass/matching/glossary_recaller.py` | `Agent.create_term` (`sdk.py:1995`). |
| Variables (context) | `core/context_variables.py` (`GLOBAL_KEY = "DEFAULT"` at `:83`), `engines/compass/variable_loader.py` | The default store is **transient** (in-memory), `sdk.py:3026`. A variable may carry a tool and refreshes on a cron freshness schedule (`variable_loader.py:156-185`). |
| Canned responses | `core/canned_responses.py`, `core/app_modules/canned_responses.py`, `engines/compass/canned_response_renderer.py` | Exemplars only, no strict mode (§2.5). |
| Tools / ToolService | `core/tools.py` (`ToolService` ABC at `:485-529`, `LocalToolService` at `:542`, `ToolContext` at `:84-106`), `core/services/tools/{plugins.py,mcp_service.py,openapi.py,service_registry.py}`, `engines/compass/tool_runner.py`, `engines/compass/loop/base_loop.py` (`_ToolStepController` at `:958-1305`) | See §2.4. |
| Review and moderation | `engines/compass/reviewer.py` (1,022 lines, LLM), `core/nlp/moderation.py`, `docs/review.md`, `docs/moderation.md` | Tool-call review and message review. Both are model-mediated. |
| Hooks | `engines/compass/hooks.py` (`CompassHooks` at `:161-240`) | 20+ lifecycle hooks. RESOLVE/BAIL semantics at `:128-151`. |
| Retrievers | `core/retrievers.py`, `sdk.py:1747-1790`, `docs/retrievers.md` | User-supplied async functions. There is no built-in document KB or ingestion. |
| Evaluations / simulations | **No OSS harness.** The REST evaluations API was removed. `CustomerKind.PERSONA` (`core/customers.py:49-56`) and a `simulation` metadata flag (`api/sessions.py:197`) remain. | Simulated conversations run in the hosted Dashboard (`DOCUMENTED`, README "Simulated test conversations"). The CLI only lists them (`bin/dashboard/commands/sessions.py:49`). |
| Sessions and events | `core/sessions.py` (`EventSource` at `:81-…`, with `customer`, `customer_ui`, `human_agent`, `human_agent_on_behalf_of_ai_agent`, `ai_agent`, `system`), `core/app_modules/sessions.py` (1,162 lines), `api/sessions.py` (2,385 lines), `core/emission/{event_publisher,event_buffer,session_tap}.py` | Mode is `auto` or `manual` (`core/tools.py:77`). Events are offset-ordered. |
| Storage backends | `adapters/db/{sqlite,json_file,mongo_db,s3,snowflake_db,transient}.py`; vector stores `adapters/vector_db/{chroma,qdrant,mongo,transient}.py`; `nano-vectordb` in base deps | Session and customer stores default to `"local"`, which is SQLite under the Parlant home directory. Other options are `"transient"`, a MongoDB URI, `s3://bucket`, or an instance (`sdk.py:2982-2993, 3024-3026`). S3 requires conditional writes and scans collections for non-ID queries (`CHANGELOG.md` 4.0.2). |
| NLP providers | `adapters/nlp/{openai,anthropic,gemini,gemini_interactions,openrouter,litellm}_service.py`; routing in `core/nlp/model_routing.py` (1,956 lines) | See §2.7. |
| API server | `api/app.py`, `api/{sessions,customers,agents,groups,health,debug,logs}.py`, `bin/server.py` | See §2.10. |
| Auth | `api/authentication.py` (guest, customer and admin principals; JWT HS256/384/512 or JWKS; scopes), `api/authorization.py` (dev and composite policies, permission gate, ownership authorizer, rate limiter) | See §2.8. |
| Observability | `core/tracer.py`, `engines/compass/tracing.py` (832 lines), `adapters/{loggers,tracing,meter}/opentelemetry.py`, `core/health/*`, `core/diagnostic_reports.py`, websocket `/logs` | OTLP exporters are enabled only when `OTEL_EXPORTER_OTLP_{LOGS,TRACES,METRICS}_ENDPOINT` is set (`bin/server.py:506,522,537`). |
| Cost control | `core/cost_control.py`, `core/pricing.py`, `SessionBudget` | Turn and step gates. The step gate **fails open** on a policy error (`loop/base_loop.py:1625-1645`). |
| Hosted dashboard module | `adapters/modules/parlant_dashboard/*`, `bin/dashboard/*` | Auto-loaded only when `PARLANT_DASHBOARD_PROJECT_TOKEN` is set (`adapters/modules/parlant_dashboard/__init__.py:17-25`). Default base URL `https://api.parlant.io` (`config.py:25`). |

### 2.3 Turn lifecycle (Compass)

`SOURCE_VERIFIED` (`core/engines/compass/engine.py`):

```text
process -> _load_context
  -> if session.mode == "manual": stop                      (:206)
  -> on_acknowledging / on_acknowledged hooks (BAIL stops)
  -> matcher.match_early -> rule handlers
  -> manual re-check                                        (:253)
  -> cost-control turn gate
  -> on_preparing hook (BAIL stop | RESOLVE skip matching)
  -> matcher.preload / fill
  -> manual re-check                                        (:310)
  -> responder.respond(...)   # react loop: steps -> tool review -> tools -> message
  -> _update_session_mode     # tool-requested manual applied AFTER the reply (:324-330, :931-936)
```

**The engine does not re-check manual mode inside `responder.respond`.** A human takeover that lands mid-turn does not stop tools or the reply (§6.5).

### 2.4 Tools and the alternate paths past the review gate (re-verified)

The v3 "Plan hook" is gone. The **main path** in v4 is:

```text
StepCompleted(needs_tools)
  -> hooks.on_reviewing_tool_calls          base_loop.py:996-999
       RESOLVE: skip reviewer, approve
       BAIL:    reject (regenerate / give up)
  -> else LLM reviewer only if (tool_review_requested
       or any consequential tool) and effort != MIN    :1074-1106, :1082-1084, :1089-1093
  -> commit step -> hooks.on_calling_tools               :1058
  -> _before_tool_calls gate (no-op in OSS)              :1143, :1371-1378
  -> safe_gather(run_tool_call ...)                      :1146-1148  (concurrent)
  -> ToolRunner.run_tool -> service.call_tool            tool_runner.py:96-105
```

`SOURCE_VERIFIED` deterministic seam: `ReviewingToolCalls` is a two-way payload, and BAIL with `give_up` stops the turn (`hooks.py:116-125, 140-151`). This is the v4 replacement for the restrictive Plan. It runs at every effort level, including MIN: the hook call at `base_loop.py:997` precedes the effort check.

**Alternate tool paths that bypass `on_reviewing_tool_calls` and the reviewer** (all `SOURCE_VERIFIED`):

1. **Context-variable refresh.** `variable_loader.py:169-181` builds a `ToolContext` and calls `tool_service.call_tool(variable.tool_id.tool_name, arguments={})` directly, with no hook and no review. Any tool attached to a variable runs outside the gate.
2. **The SDK's integrated plugin tool server.** `Server` starts a `PluginServer` on `127.0.0.1:<tool_service_port>` (default 8818; `sdk.py:3021, 4916-4924`). Its `POST /tools/{name}/calls` (`core/services/tools/plugins.py:851-862`) has **no authentication**. It accepts caller-supplied `agent_id`, `session_id` and `customer_id` (`CallToolRequest`, `plugins.py:607-612`). Any local process that can reach the port can execute any `@p.tool` directly. `PluginServer`'s own default bind is `0.0.0.0` (`plugins.py:643`) when it is used standalone.
3. **Hook RESOLVE skips the reviewer** (`base_loop.py:1002-1004`). This is by design, but a misbehaving hook approves everything.
4. **Effort MIN skips LLM review entirely**, "whatever was requested" (`base_loop.py:1082-1084`). The `Tool.consequential` docstring says the same (`core/tools.py:381-385`).

Other tool facts:

- `ToolParameterOptions.source` = `"customer"` is a **prompt hint**: "This can help agents understand…" (`core/tools.py:308-310`). It is not enforced.
- `ToolContext` carries only `agent_id`, `session_id`, `customer_id` and `plugin_data`, with **no tenant** (`core/tools.py:84-106`; built at `tool_runner.py:80-84`).
- On a timeout (default 180 s, overridable with `PARLANT_TOOL_TIMEOUT`; `tool_runner.py:43, 203-215`), `asyncio.wait_for` cancels the call. The model receives `ToolResult(data="Tool call timed out")` (`tool_runner.py:102-105, 121-138`). **The commit outcome is unknown, but the model sees an ordinary error and may call again.**
- Tool arguments and results are logged at debug level (`tool_runner.py:92-94, 107-109`).
- Positive: `SessionAuthorization` gives tools per-message OAuth-style scopes. Scopes come only from short-lived customer JWTs (`exp` and `iat` required, lifetime capped; `api/authentication.py:386-407`). `require_scope` raises `ScopeNotGrantedError` (`sdk.py:2492-2575`). Tools can also return an `authorization_required` signal that emits a sign-in custom event (`tool_runner.py:180-201`). **This is a reusable identity input for the broker.**

### 2.5 Canned responses at v4 (strict mode gone)

- `SOURCE_VERIFIED` The doc states this directly: "the message the customer receives always comes from the agent's own generation" (`docs/canned-responses.md:457-461`).
- Canned responses gate delivery only when message review runs. Message review never runs at `Effort.MIN` (`docs/canned-responses.md:296-300`).
- Strongest native levers:
  - `field_dependencies` exclude a response whose data premise is not staged (`:286-305`).
  - Tool and retriever results can supply **literal** response texts with a use-verbatim note (`:306-316`). The model still writes the final text.
- **Deterministic enforcement is still possible through hooks.** `on_message_generated` with BAIL suppresses emission **in blocking output only**, and "the handler may emit a replacement itself" (`hooks.py:149-150`). `on_reviewing_message` BAIL forces regeneration (`hooks.py:104-113`).
- **Decision:** Klaint text MVP uses `MessageOutputMode.BLOCK`. A Klaint `on_message_generated` hook classifies commitments deterministically (refund, price, policy, action-done). It BAILs and emits an approved template that is rendered **only from broker ledger receipts**, or a handoff.
- Streaming and voice cannot use this suppression. They need a different control (KV-02).
- **Fallback:** if the KT-01 spike shows the hook cannot reliably replace text, stay on v3.3.2, where `CompositionMode.CANNED_STRICT` exists (`parlant@61bba3b:src/parlant/core/engines/alpha/canned_response_generator.py:610-616, 698`, fetched via `gh api`).

### 2.6 Retrievers

- `SOURCE_VERIFIED` `RetrieverFunction(RetrieverContext) -> RetrieverResult | None | DeferredRetriever` (`sdk.py:1747-1790`).
- `RetrieverResult` carries `data`, `metadata`, `canned_responses`, `canned_response_fields` and `rules` (transient rules).
- Retrievers can be agent-wide or bound to a rule (`docs/retrievers.md:43-97`).
- **No built-in KB, ingestion or tenant scoping.** Klaint must supply its own tenant-bound index and citations. Retrieved text is injected as data with no sanitization (§6.1).

### 2.7 NLP providers and local models

- `SOURCE_VERIFIED` Built-in providers: OpenAI, Gemini, Anthropic (embeddings via Voyage), OpenRouter and LiteLLM (`docs/providers.md:550-561`).
- **The default route is `{"*": "openrouter"}`** (`sdk.py:3049`). Calls go to `https://openrouter.ai/api/v1` with Parlant app-attribution headers (`adapters/nlp/openrouter_service.py:168, 225-230`).
- **No first-class local or Ollama provider in v4.**
- Local options:
  - LiteLLM, whose adapter names Ollama among its backends (`adapters/nlp/litellm_service.py:16-18`).
  - A custom `ModelProvider` callable that returns a `ReactGenerator`. It can be selected per tenant (`docs/providers.md:1116-1178, 1265-1287`).
  - The OpenAI adapter builds `AsyncClient` without an explicit `base_url` (`openai_service.py:189-195`). An OpenAI-compatible local server via the SDK's environment `base_url` is therefore plausible, but is `NOT_RUN` and not documented by Parlant.
- Schematic operations require structured output (`docs/providers.md:1218-1237`), so local models must support it. Quality is `NOT_MEASURED`.
- Moderation is OpenAI-only among built-ins (an explicit route) or a custom model (`docs/providers.md:557`; `docs/moderation.md:106-140`).

### 2.8 Auth, multi-tenancy and isolation

- `SOURCE_VERIFIED` The default environment is **development**: anything unrecognized counts as development (`core/environment.py:26-38`). Development installs `DevelopmentAuthorizationPolicy`, which allows every operation, applies no rate limit and sets CORS to `*` (`api/authorization.py:287-318`; selected at `bin/server.py:798-801`). The doc warns against exposing it: "Never expose a development-mode server publicly" (`docs/auth.md:222-223`).
- `PARLANT_ENV=production` requires `PARLANT_ADMIN_API_KEY` and accepts either a customer JWT secret or a JWKS URL, not both (`bin/server.py:634-667`).
- Principals are anonymous, guest, customer and admin (`api/authentication.py:114-158`).
- `DefaultPermissionGate` is a per-kind allowlist. Human-agent events, session updates (mode) and log streaming are **admin-only** (`api/authorization.py:341-392`; operations at `:69-116`).
- `OwnershipAuthorizer` checks `customer_id` or the guest instance only (`:405-427`).
- The composite policy's CORS also defaults to `*` with credentials (`:479-488`).
- **The admin credential is one static key with no per-operator identity** (`docs/auth.md:60`).
- **Parlant has no tenant concept.** `grep tenant` in `src/parlant` finds only a docstring suggesting "a tenant-aware authorizer" (`api/authorization.py:438-440`), provider docs, and dashboard CLI code. Per server there is one store set, one customer-token issuer (secret or JWKS), one admin key and one tool-server port.
- **Klaint isolation decision for the MVP: one Parlant `Server` process per tenant.**
  - Each gets its own store (SQLite file, Mongo database or S3 bucket), secrets, model credentials and tool-server port.
  - Run each in its own container or network namespace, so the unauthenticated `127.0.0.1` tool server is not reachable from another tenant.
  - A Klaint gateway maps the authenticated tenant to its server.
  - A shared-process design (many tenants' agents in one server) is `REJECTED` for the MVP. It would need a custom `Authorizer`, tenant-tagged customer IDs, a tenant-aware tool broker and per-tenant model routing, and nothing demonstrates its isolation.
  - Per-process memory and CPU cost is `NOT_MEASURED`. KT-01 measures it.

### 2.9 Human handoff, streaming and voice

- **Handoff.** `PATCH /sessions/{id}` with `mode: "manual"` (admin), then a human posts `source: human_agent` events. A tool can also return `control={"mode": "manual"}` (`docs/sessions.md:24-25, 132-147, 971-975`). The mode switch from a tool lands after the reply (`engine.py:931-936`).
- **Streaming.** Output modes are BLOCK and STREAM. Event listing supports long-poll and SSE: `wait_for_data > 0` returns a `text/event-stream` (`api/sessions.py:2041-2130`).
- **Voice in the OSS is a seam, not a feature.**
  - `MessageOutputMode.VOICE` exists (`core/agents.py:60-62`), but the responder raises `NotImplementedError("Voice output mode requires a responder configured with a voice-capable loop.")` (`engines/compass/responder/responder.py:204-207`).
  - Reusable pieces: `SessionTap` with `SPEECH_DELTA` for push delivery (`core/emission/session_tap.py:14-60`), the `spoken_text` annotation ("barge-in truth"; `core/sessions.py:355-378`), and the `_before_consequential_tools` gate stub (`loop/base_loop.py:1371-1378`).
  - The voice loop itself is commercial "Compass Pro" (`DOCUMENTED`, link above).

### 2.10 API server and SDKs

- `SOURCE_VERIFIED` REST routes:
  - sessions: create, read, list, delete, update, claim, authorize; events create, list (SSE), read, delete, update (`api/sessions.py:1215-2327`)
  - customers: CRUD (`api/customers.py:335-578`)
  - agents: read and list (`api/agents.py:73,101`)
  - groups; health; debug diagnostic reports (`api/debug.py`); websocket `/logs` (`api/logs.py:26-31`, admin-only)
- Default bind is `host="0.0.0.0"`, port 8800 (`sdk.py:3019-3020`).
- `hot_reload=True` by default; it re-execs the process on file change (`sdk.py:3000-3005, 3030`). **Disable it in production.**
- SDKs: Python `parlant.sdk`, the React chat widget `widget/` (ships in the wheel), and the external `parlant-client` (used by `emcie-co/parlant-pipecat`, §3.2). AG-UI is documented in `docs/ag-ui.md`.
- **There is no idempotency key anywhere** on event creation or tool execution. A `grep -i "idempot|dedup"` over `api/`, `core/tools.py`, `tool_runner.py` and `app_modules/sessions.py` finds only the delete-session docstring.

### 2.11 Test inventory (NOT_RUN)

`SOURCE_VERIFIED`: 205 `test_*.py` files and 2,680 `def test_` functions:

| Directory | Files | Functions |
| --- | --- | --- |
| `adapters` | 35 | 684 |
| `api` | 15 | 362 |
| `bin` | 12 | 223 |
| `core/stable` | 94 | 1,282 |
| `core/unstable` | 3 | 2 |
| `sdk` | 37 | 50 (by this regex) |

`pytest_stochastics.json` runs `core/stable` under "strict3" and `core/unstable` under "majority3". Many core tests call real models, so they must not be run against paid providers.

Most relevant tests to port as fixtures:

- `tests/api/test_authorization.py` (52 tests), `test_authentication.py`, `test_auth_flows.py`
- `tests/core/stable/engines/test_hooks.py`, `tests/sdk/test_hook_results.py`
- `tests/core/stable/engines/compass/test_tool_runner.py`, `test_reviewer.py`
- `tests/sdk/test_session_authorization.py`, `test_authorization_required.py`
- `tests/core/stable/test_session_event_scoping.py`, `tests/core/stable/emission/test_session_tap.py`
- `tests/sdk/test_canned_responses.py`, `test_compass_canned_responses.py`, `tests/core/stable/test_retrievers.py`
- `tests/adapters/db/test_{sqlite,mongodb,s3}.py`

### 2.12 Default network egress and telemetry

`SOURCE_VERIFIED`, from a scan of hardcoded external hosts in `core/`, `adapters/`, `sdk.py`, `api/*.py` and `bin/server.py`. The only runtime hosts found are model providers (OpenRouter, Voyage for Anthropic embeddings, and the provider SDKs) and the dashboard (`api.parlant.io`, only if a token is set). **No unconditional product telemetry was found.** Off-by-default egress requires environment settings: the dashboard token, `OTEL_*` endpoints, or `PARLANT_DASHBOARD_*`.

Defaults that need configuration:

- The default model route is OpenRouter (§2.7).
- **Session-client recording is on by default.** It stores the client IP and page origin, and also an approximate location if a local GeoIP database is configured (`bin/server.py:670-685`; disable with `PARLANT_RECORD_SESSION_CLIENTS=false`).
- The widget can register a WebMCP `ask_agent` tool in browsers (`CHANGELOG.md` 4.0.2; disable with `webmcp={false}`).
- No socket-level egress capture was run (`NOT_RUN`).

---

## 3. Pipecat, the Parlant–Pipecat composition, Chatwoot and Botpress

### 3.1 Pipecat v1.15.0 (`pipecat-ai/pipecat@fda1d5e`)

- **License and runtime.** `SOURCE_VERIFIED` BSD-2-Clause, "Copyright (c) 2024–2026, Daily" (`LICENSE:1-3`). `requires-python = ">=3.11"` (`pyproject.toml:12`), which is narrower than Parlant's 3.10+, so the shared service must use Python 3.11–3.14.
- **Transports.** `src/pipecat/transports/` contains `smallwebrtc/` (`connection.py`, `request_handler.py`, `transport.py`), `livekit/`, `daily/`, `websocket/` (`fastapi.py`, `server.py`, `client.py`), `local/`, `vonage/`, `whatsapp/`, `moq/`, `tavus/`, `heygen/` and `lemonslice/`.
- **Telephony serializers.** `src/pipecat/serializers/` holds `twilio.py` (`TwilioFrameSerializer:57`), `telnyx.py` (`:39`), `plivo.py`, `vonage.py`, `exotel.py` and `genesys.py`.
- **Interruption and barge-in:**
  - `InterruptionFrame` (`frames/frames.py:1425`), `UserStartedSpeakingFrame` (`:1437`), `UserTurnResponseCancelFrame` (`:1462`).
  - `LLMService._handle_interruptions` **cancels every in-flight function call whose `cancel_on_interruption` is true** (`services/llm_service.py:1091-1094`). The default is `True` (`adapters/llm/schemas/direct_function.py:293`; `register_function(... cancel_on_interruption: bool | None = None ...)` at `llm_service.py:1228-1236`).
  - **Implication:** a mutating tool run inside Pipecat could be cancelled mid-commit by barge-in. **Klaint must not register mutating functions in Pipecat.** Parlant plus the broker own tools.
- **Turn detection:**
  - `LocalSmartTurnAnalyzerV3` uses ONNX Runtime (`audio/turn/smart_turn/local_smart_turn_v3.py:16, 28, 50`).
  - The model file `smart-turn-v3.2-cpu.onnx` is **bundled** in `audio/turn/smart_turn/data/`, so there is no runtime download. The smart-turn source repo `pipecat-ai/smart-turn` is BSD-2-Clause (`DOCUMENTED` via `gh api`).
  - v1.15 adds classifier, LLM-completion and strategy-mode user-turn strategies (release notes).
- **Local STT, TTS and LLM services (74 service directories):**
  - STT: `whisper/stt.py` (`WhisperSTTService:224`, `WhisperSTTServiceMLX:470`), `moonshine/stt.py:133`.
  - TTS: `piper/tts.py` (`PiperTTSService:47`, `PiperHttpTTSService:210`), `kokoro/tts.py:118`, `xtts/tts.py:93`.
  - LLM: `ollama/llm.py` (`OLLamaLLMService:24`, `base_url="http://localhost:11434/v1"` at `:43`).
  - **Kokoro downloads model files from GitHub on first use** (`kokoro/tts.py:40-63`), so pre-provision them for offline or locked-egress deployments.
  - No `sherpa` service directory exists at this tag. Arabic quality for any engine is `NOT_MEASURED`.
- **Telemetry and egress.** `processors/metrics/sentry.py` exists and is opt-in (it must be added to a pipeline). No unconditional telemetry module was found by grep for posthog, sentry_sdk, mixpanel or segment, apart from that opt-in processor.
- **Twilio serializer.** `auto_hang_up=True` by default and uses Twilio REST credentials (auth token or API key; `serializers/twilio.py:64-66, 77-83, 90-140`). **The serializer does no inbound webhook-signature validation**: a grep for "signature" in `twilio.py` returns no hits. The TwiML or webhook endpoint is app-owned and Klaint must validate it.
- **Tests (NOT_RUN).** 395 `test_*.py` files under `tests/`, including `test_frames_interruptible.py`, `test_direct_functions.py`, `test_base_smart_turn_buffer.py`, `test_eager_user_turn_strategies.py`, `test_classifier_user_turn_stop_strategy.py`, `test_exotel_serializer.py` and `tests/genesys/test_genesys_serializer.py`.

### 3.2 Existing Parlant–Pipecat integration

- `SOURCE_VERIFIED` `emcie-co/parlant-pipecat@eac20d2ea80928874d5081cfbba4cdb0edb1f2b4` (Apache-2.0, last pushed 2025-10-20). File: `parlant/contrib/pipecat/parlant_service.py` (369 lines; copy at `scratchpad\parlant_service.py.txt`).
  - `ParlantService(AIService)` forwards each `TranscriptionFrame` as a `customer` message event (`:213-221, 362-368`).
  - It long-polls `list_events(kinds="message,status", wait_for_data=30)` (`:249-255`) and speaks agent messages as `LLMTextFrame`s (`:231-237, 296-298`).
  - It plays a typing track and filler phrases during `processing` and `typing` status (`:266-294`).
  - The greeting is posted as `human_agent_on_behalf_of_ai_agent` (`:223-229`), **which needs admin credentials** under the v4 permission gate.
- **Gaps:**
  - It pins `pipecat-ai ^0.0` and `parlant-client ^3.0` (its `pyproject.toml`), both stale for v1.15 and v4.
  - Its `tests/` directory holds only `__init__.py`.
  - It never writes the `spoken_text` interruption annotation, has no ownership-epoch check, and has no idempotency.
  - `except Exception: continue` makes a tight retry loop on errors (`:256-257`).
- **Decision: `ADAPT` as a reference.** Write a Klaint `FrameProcessor` with the same seam (`FrameProcessor` `processors/frame_processor.py:203`, `AIService` `services/ai_service.py:33`), targeting Parlant **STREAM** mode and SSE in-process. Add barge-in truth, epoch checks and backoff (KV-01, KV-02). Composition stays "one Python service" (Opus S3): Pipecat and Parlant run in the same tenant process, or the Pipecat worker talks to its tenant's Parlant server over loopback.

### 3.3 Chatwoot v4.19.1: the Agent Bot API boundary (`chatwoot@caab07a`)

**Bot authentication and scope.** A bot authenticates with the `api_access_token` header (legacy) or a bearer token (`app/controllers/concerns/access_token_auth_helper.rb:9-30`). Bots may only call an endpoint allowlist (`:2-7`, `:55-63`):

- conversations: `show`, `toggle_status`, `toggle_typing_status`, `toggle_priority`, `create`, `update`, `custom_attributes`
- messages: `create`
- assignments: `create`
- labels: `index`, `create`

**Bots are account-scoped, not inbox-scoped.** Account access is granted if `bot.account_id == account.id` or the bot has any `agent_bot_inboxes` row in that account (`ensure_current_account_helper.rb:29-33`). `ConversationPolicy` then allows any `AgentBot` to view the conversation (`app/policies/conversation_policy.rb:11, 24-25`). `AgentBot.accessible_to(account)` includes **system bots** with `account_id` nil (`app/models/agent_bot.rb:27-30`).

→ **One Chatwoot account per Klaint tenant, one bot per account. Never attach one bot across accounts.**

**Events to bots.** `AgentBotListener` handles `conversation_resolved`, `conversation_opened`, `conversation_status_changed`, `conversation_updated`, `message_created`, `message_updated` and `webwidget_triggered` (`app/listeners/agent_bot_listener.rb:2-60`). Each delivery gets `secret: agent_bot.secret, delivery_id: SecureRandom.uuid` (`:84-88`).

**Signing.** `Webhooks::Trigger#request_headers` sets `X-Chatwoot-Delivery`, `X-Chatwoot-Timestamp`, and `X-Chatwoot-Signature: sha256=HMAC(secret, "#{ts}.#{body}")` (`lib/webhooks/trigger.rb:54-60`). The POST goes through `SafeFetch` (`:41-52`). The account `WebhookJob` uses the same trigger (`app/jobs/webhook_job.rb:4-5`).

**Retries.** `AgentBots::WebhookJob` retries `RetryableError` 3 times, 3 s apart (`app/jobs/agent_bots/webhook_job.rb:3`). Deliveries are at least once, so **the receiver must dedupe on `X-Chatwoot-Delivery`** and verify the timestamp skew.

**Failure semantics.** After a terminal bot-delivery failure on a `pending` conversation, Chatwoot **opens it** (hands it to humans) and posts an activity message, unless `account.keep_pending_on_bot_failure` is set (`trigger.rb:65-84`).

**Handoff semantics:**

- `pending` = bot-owned.
- `toggle_status` from `pending` to `open` calls `bot_handoff!` (`app/controllers/api/v1/accounts/conversations_controller.rb:83-99`).
- `bot_handoff!` is explicitly "Best-effort eligibility check, not a lock against concurrent takeovers" (`app/models/conversation.rb:184-187`).
- `AssignmentService#assign_agent` uses `with_lock` and opens pending conversations (`app/services/conversations/assignment_service.rb:16-19`). `assign_ai_assignee` locks and sets `pending` (`:37-43`).

**Inbound idempotency.** `Message` has `source_id` (with a non-unique index) and a transient `echo_id` (`app/models/message.rb:23, 38, 84`). `MessageBuilder` passes both through (`app/builders/messages/message_builder.rb:173-174`). **No uniqueness constraint was found**, so Klaint must keep its own outbound dedupe ledger.

**License boundary:**

- Root `LICENSE:1-8`: MIT outside `enterprise/`.
- `enterprise/app/services/` contains `captain`, `llm`, `voice`, `sla`, `saml`, `conversation_monitors`, `twilio`, `whatsapp` and others (`gh api` listing). **Captain (Chatwoot's AI) is enterprise-licensed.**
- The Agent Bot API, listener, trigger and assignment service live in MIT paths. They still carry enterprise extension hooks: `Conversations::AssignmentService.prepend_mod_with` (`assignment_service.rb:62`) and `AgentBot.include_mod_with('Audit::AgentBot')` (`agent_bot.rb:72`).
- Running unmodified Chatwoot through the API keeps Klaint code free of either license's copy obligations. Distributing Chatwoot itself requires the enterprise-composition inventory (prior study).

**Provisioning per tenant.** A platform API exists (`app/controllers/platform_controller.rb`; `platform/api/v1/*`). Its exact account-provisioning endpoints are `NOT_RUN` in this pass.

### 3.4 Botpress public repository (`botpress@956bcdef`)

- `SOURCE_VERIFIED` (`gh api`):
  - `integrations/` holds **83** directories. CRM, helpdesk and messaging ones include zendesk, zendesk-messaging-hitl, hubspot, intercom, salesforce, freshdesk, freshchat, twilio, vonage, whatsapp, messenger, telegram, slack, teams, line, viber, wechat, instagram, sunco and email.
  - `interfaces/` holds creatable, deletable, files-readonly, **hitl**, listable, llm, message-state, proactive-conversation, proactive-user, readable, speech-to-text, text-to-image, typing-indicator and updatable.
  - `packages/` includes **llmz, cognitive, zai, vai**, sdk, client, cli and zui. The LLMz engine source is present, but its package licenses were not checked in this pass (`NOT_RUN`).
- HubSpot signature check at HEAD (`integrations/hubspot/src/hitl/utils/signature.ts:22-24`): `Date.now() - parseInt(timestamp)` against a 5-minute bound. **Future timestamps (a negative difference) and non-numeric ones (NaN) pass the age test.** Line 35 uses `timingSafeEqual`, which throws on a length mismatch.
- Decision unchanged (Opus S3): `REFERENCE_ONLY`. Use the HITL interface and ticket schemas as design input for Python connectors. No Node runtime.

---

## 4. Other open-source candidates

All `DOCUMENTED` via `gh api repos/...` (license SPDX, `pushed_at`, HEAD SHA, latest release) on 2026-11-08. Only candidates with a measurable reuse advantage are kept.

| Candidate | License, HEAD, release | Gap it fills | Measurable advantage / reason | Decision |
| --- | --- | --- | --- | --- |
| **sierra-research/tau2-bench** | MIT; `033bf082f48e`; v2.0.0 (2026-10-20) | Reproducible eval and simulation (§KT-08) | `SOURCE_VERIFIED` `src/tau2/domains/{airline,retail,telecom,banking_knowledge,intake,mock}`; `src/tau2/{user,multilingual,voice,evaluator,gym}`. `EnvironmentEvaluator` scores by **DB-hash equality** of gold vs predicted environment (`src/tau2/evaluator/evaluator_env.py:17, 118-126`). This is a ready deterministic outcome scorer, user simulator and task format. | **ADOPT_TEST_DEPENDENCY** (pattern plus code in the test harness only) |
| **standard-webhooks/standard-webhooks** | Apache-2.0; `ab6844147ce9`; v1.0.2 | Webhook signature, skew and replay checks | Python `Webhook.verify` reads `webhook-id` and `webhook-timestamp`, uses `hmac.compare_digest`, and rejects "too old" or "too new" timestamps (`libraries/python/standardwebhooks/webhooks.py:54-91, 150-160`). It fixes the Botpress HubSpot NaN/future flaw class. A replay store is still Klaint's job. | **ADOPT_RUNTIME** (a small lib; use it for Klaint-issued webhooks, and use its pattern for the Chatwoot receiver) |
| **UKGovernmentBEIS/inspect_ai** | MIT; `b05079960b`; 0.3.288 | Eval orchestration and logging | Mature eval runner. It overlaps with tau2 for Klaint's task shape. | **REFERENCE_ONLY** (reopen if tau2's runner is insufficient) |
| **promptfoo/promptfoo** | MIT; `2a6fdf9b2e`; 0.125.1 | Prompt-injection red-team suites | Red-team plugin catalog. It is Node, which is acceptable as test tooling only. Its plugin count and telemetry default were `NOT_RUN` in this pass. | **ADOPT_TEST_DEPENDENCY, conditional** (only after a telemetry/egress check) |
| **dbos-inc/dbos-transact-py** | MIT; `236142bd7a`; 3.4.0 | Durable steps and idempotency for the broker | A library-only durable-workflow layer on Postgres, so it fits "one Python service". Its advantage over a single ledger table is `NOT_MEASURED`. | **REFERENCE_ONLY**, compared in KT-03 |
| temporalio/sdk-python | MIT; `72406f85e2`; 1.35.0 | Durable execution | Requires a separate Temporal server, which violates S3's single-runtime boundary for the MVP. | **REJECTED** for the MVP |
| langchain-ai/langgraph | MIT; `e5e37b5d70` | Checkpointed graphs, HITL interrupts | Would duplicate Parlant's dialogue state. Two authoritative engines. | **REJECTED** |
| openai/openai-agents-python | MIT; `27c75c5f9c`; v0.24.0 | Guardrails, handoffs, tracing | Duplicates the dialogue engine. Default trace-export behaviour was not inspected (`NOT_RUN`). | **REJECTED** |
| RasaHQ/rasa | Apache-2.0; branch 3.6.x `60a3cff9c0`; 3.6.21 (2025-01-14) | Rule and lock reference | Unchanged since the prior study: maintenance mode, Python <3.11. CALM / Rasa Pro licensing was not re-fetched (`NOT_RUN`). | **REFERENCE_ONLY** (K11 unchanged) |
| letta-ai/letta | Apache-2.0; 0.16.8 | Long-term memory | Not a Klaint MVP gap. Parlant 4 ships `docs/memory.md` and compaction. | **REJECTED** |
| NVIDIA/NeMo-Guardrails | SPDX `NOASSERTION`; v0.24.1 | Guardrails | The license file was not inspected, and it would add a second policy runtime. | **REJECTED for now** (re-check the license if needed) |
| protectai/llm-guard | MIT; **archived = true** | Scanners | Archived upstream. | **REJECTED** |
| confident-ai/deepeval | Apache-2.0; python-v4.2.4 | LLM-judge metrics | The LLM judge is advisory only, and tau2 covers deterministic scoring. Telemetry default `NOT_RUN`. | **REJECTED** |
| livekit/agents | Apache-2.0; `livekit-agents@1.8.11` | Voice framework | Opus S3 keeps Pipecat only. Parlant's commercial voice is LiveKit-based (`DOCUMENTED`), which is not reusable. | **REFERENCE_ONLY** |
| zammad/zammad, freescout | AGPL-3.0 | Helpdesk alternatives | AGPL network-copyleft and no advantage over unmodified Chatwoot through the API. | **REJECTED** |
| OpenFGA / Cerbos / Oso | not fetched | Multi-tenant authz | Per-tenant process isolation plus `tenant_id`-bound broker rows suffices for the MVP. | **REJECTED for the MVP** (`NOT_RUN`) |

---

## 5. Competitors (official documentation only)

The competitor sub-agent fetched 73 pages, 70 successfully, on 2026-11-08, through an automated summarizer. Every cell below is `DOCUMENTED` against the URLs listed after the table. "n/s" means not stated on the fetched pages; it does **not** mean absent. No authenticated workflow, call or trial was run, and no parity is claimed. The Klaint column is the **plan** and is `NOT_RUN`.

### 5.1 Parity matrix (condensed)

| Capability | Decagon | Sierra | Intercom Fin | Ada | Retell | Vapi | Bland | Botpress | Chatwoot (Captain) | Parlant (v4 OSS = source; Dashboard = doc) | Cognigy | **Klaint plan (donor)** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Voice | Yes | Yes | Yes (select customers) | Yes (Twilio/SIP) | Yes | Yes | Yes | Enterprise | Paid self-host tier | OSS: seam only (`responder.py:204-207`); Pro: LiveKit | Yes (add-on) | Phase 2: Pipecat v1.15 |
| Chat | Yes | Yes | Yes | Yes | Yes | Yes | Enterprise | Yes | Yes | Yes (widget) | Yes | Parlant widget / API + Chatwoot |
| Instructions / policy | AOPs | Journeys, SDK | Procedures and Guidance | Playbooks | Prompt or flow | Assistants, Squads | Pathways | Autonomous node | Guidelines and Scenarios | Policies / SOP text (source) | n/s | Parlant policies |
| Approved responses | n/s | n/s | "Say" steps exact | Legacy Processes exact | Flow nodes | n/s | n/s | partial | n/s | Exemplars; gate only with review (source) | n/s | **Hook-enforced templates from ledger receipts** |
| Knowledge retrieval | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | User retrievers (source) | n/s | Tenant-scoped retriever |
| Workflows / procedures | Yes | Yes | Yes (Python conditions) | Yes | Yes | Yes | Yes | Yes | Yes | SOP-text policies | n/s | Parlant + broker |
| Tool execution safety | Scoped JWT tokens, supervisor model | "deterministic" calls | Deterministic code steps | n/s | n/s | n/s | Guardrails (not tools) | Prompt only | **Email OTP before tool**, admin-only tools | LLM review of consequential tools, skipped at MIN (source) | n/s | **Deterministic broker + ledger** |
| CRM / helpdesk | Salesforce, Zendesk, Intercom | 40+ (unnamed) | Salesforce, HubSpot, Freshdesk… | Zendesk, Salesforce, Genesys… | unnamed | n/s | Salesforce, HubSpot | Zendesk HITL | n/a (is the helpdesk) | Any code (no catalog) | Genesys, Salesforce, NICE | Chatwoot + Python connectors |
| Human handoff / takeover | Yes | Yes | Yes | Yes | Yes (listen / take over) | Yes (warm, Twilio) | Yes | Yes | Yes | Manual mode (source) | Yes | Chatwoot + epoch |
| Tenancy | n/s | n/s | Workspaces | partial | partial | Orgs | Dedicated pods | Workspaces | Accounts (source) | **None in OSS** (source) | n/s | Process per tenant |
| Auth / permissions, SSO | SSO, RBAC | n/s | Yes | Roles, SSO | Enterprise SSO, RBAC | RBAC (Pro), SSO (Premier) | SSO, permissions | RBAC (Team) | Enterprise SSO | Guest/customer/admin, JWT/JWKS, scopes (source) | Roles | Gateway + Parlant JWT scopes |
| Session history | partial | partial | partial | Yes | Yes | Yes | Yes | n/s | Yes | Yes (source) | partial | Parlant events + ledger |
| Audit trails | Tamper-protected logs | n/s | Teammate logs, 1 year | Config / sign-in log | n/s | n/s | Audit-log API | Change log | Enterprise | n/s | partial | **Hash-chained tool ledger** |
| QA | Watchtower | partial | Scorecards, monitors | partial | AI QA | Evals | Judges | n/s | partial | Dashboard | partial | KT-08 |
| Simulations | Yes (judge rationale) | Yes + Voice Sims | Inside Procedures only | Yes ("minor variation expected") | Text only, mocks | Voice/chat | Test cases | n/s | Playground | Dashboard (hosted) | n/s | tau2-style, **replayable** |
| Evaluations / benchmarks | Regression CI | τ-bench / τ²/τ³ | LLM-judge Evals | Pass/fail outcomes | Pass rate | Exact / regex / judge / tool-call | Gates | n/s | n/s | n/s | partial | DB-hash scoring |
| Analytics | Yes | Explorer, Insights | CX Score, topics | Yes | Dashboards | partial | Yes | Team plan | Monitors | Session analytics (doc) | Insights | P2 |
| Arabic | not named (70+ languages) | not named (59) | "Arabic (Modern)"; Voice: Arabic in 29 | **6 Arabic voice dialects**, RTL | `ar-SA` only | not named | **absent** from codes | not named | Greeting graphic only | n/s | Listed (NLU) | MSA + Gulf eval set (KT-08) |
| Interruption handling | Yes | Yes | Yes | partial | Yes | Stop-speaking plan | Interruptibility 0–4 | n/s | n/s | spoken_text seam (source) | n/s | Pipecat + spoken_text |
| Observability | Yes | Traces | partial | partial | Yes | Langfuse | partial | Inspect | n/s | OTEL + diagnostics (source) | partial | OTEL, local collector |
| Self-host | n/s | n/s | Regions only | n/s | Dedicated server add-on | EU region | On-prem/VPC (Enterprise) | Residency policy | **Yes** (Community excludes Captain) | **Yes** (Apache-2.0) | **Yes** (Kubernetes) | Yes |
| Pricing published | No | Outcome-based, no figures | $0.99/outcome… | No | $0.07–$0.31/min… | $0.05/min hosting… | $0.14/min… | $150/$750/mo… | $19/$39/$99/agent | $79/$349/mo Dashboard | No | n/a |

**URLs** (all accessed 2026-11-08, `DOCUMENTED`):

- Decagon: https://decagon.ai/product/voice · https://decagon.ai/product/aop · https://decagon.ai/product/testing-qa · https://decagon.ai/security · https://decagon.ai/product/integrations
- Sierra: https://sierra.ai/product/agent-studio · https://sierra.ai/product/channels · https://sierra.ai/product/trust-and-reliability · https://sierra.ai/product · https://sierra.ai/product/agent-sdk · https://sierra.ai/resources/research/tau-bench
- Intercom Fin: https://fin.ai/pricing · https://www.intercom.com/help/en/articles/8322387-set-up-fin-ai-agent-s-multilingual-support · https://www.intercom.com/help/en/articles/16248514-fin-voice-faqs · https://www.intercom.com/help/en/articles/12495167-fin-procedures-explained · https://www.intercom.com/help/en/articles/15899411-fin-evals-explained · https://www.intercom.com/help/en/articles/6124430-regional-data-hosting · https://www.intercom.com/help/en/articles/4667982-review-actions-taken-in-your-workspace-with-teammate-activity-logs
- Ada: https://docs.ada.cx/docs/welcome · https://docs.ada.cx/docs/setup/languages/about-multilingual-support · https://docs.ada.cx/docs/channels/voice/voice-onboarding.md · https://docs.ada.cx/docs/optimization/testing/simulations.md · https://docs.ada.cx/docs/automation/playbooks.md · https://docs.ada.cx/docs/other/audit-log.md · https://www.ada.cx/pricing/
- Retell AI: https://docs.retellai.com/general/introduction · https://www.retellai.com/pricing · https://docs.retellai.com/test/llm-simulation-testing.md · https://docs.retellai.com/build/language-support · https://docs.retellai.com/build/single-multi-prompt/transfer-call
- Vapi: https://docs.vapi.ai/quickstart/introduction · https://vapi.ai/pricing · https://docs.vapi.ai/customization/multilingual.md · https://docs.vapi.ai/observability/simulations-overview.md · https://docs.vapi.ai/customization/speech-configuration.md · https://docs.vapi.ai/squads/handoff · https://docs.vapi.ai/tools/transfer-call/warm-transfer.md
- Bland AI: https://docs.bland.ai/welcome-to-bland · https://www.bland.ai/pricing · https://docs.bland.ai/agents/evaluations.md · https://docs.bland.ai/tutorials/guard-rails.md · https://docs.bland.ai/api-v1/post/calls
- Botpress: https://botpress.com/pricing · https://botpress.com/docs/studio/concepts/agents/hitl-agent/ · https://botpress.com/docs/studio/concepts/nodes/autonomous-node/
- Chatwoot: https://www.chatwoot.com/pricing · https://www.chatwoot.com/pricing/self-hosted-plans · https://www.chatwoot.com/captain · https://www.chatwoot.com/hc/user-guide/articles/1775045339-v2-_-how-to-set-up-custom-tools-for-captain
- Parlant: https://www.parlant.io/pricing · https://parlant.io/docs/playbooks/consequential-tools · https://parlant.io/docs/compass-pro/overview · https://parlant.io/docs/playbooks/human-handoff
- Cognigy: https://docs.cognigy.com/ai/installation/overview/ · https://docs.cognigy.com/ai/empower/nlu/language-support/
- `BLOCKED_EXTERNAL`: https://www.parlant.io/docs/quickstart/introduction (empty page) · https://www.parlant.io/docs/concepts/customization/canned-responses/ (404) · https://www.parlant.io/docs/production/human-handoff/ (404)

### 5.2 Differentiation opportunities (each with a measurable test; all NOT_RUN)

1. **Exactly-once external actions under uncertainty.** No fetched page describes a per-tool outcome ledger or unknown-commit reconciliation.
   - *Test:* a fault-injection suite of 1,000 runs over a fake CRM (timeout after commit, broker crash between dispatch and record, Chatwoot webhook replayed 3 times, customer double-send).
   - *Pass:* exactly 1 external mutation per authorized intent, and every UNKNOWN outcome reconciled before any retry.
2. **Commitments only from receipts.** Competitors describe guardrails and LLM judges. Parlant v4 dropped strict templates.
   - *Test:* 100 preregistered adversarial commitment prompts × 3 seeds × 2 languages.
   - *Pass:* zero emitted messages that assert refund, price or action completion without a matching COMMITTED ledger receipt, checked by a deterministic phrase-and-slot checker.
3. **Self-host, BYOK, zero surprise egress.** Self-host is n/s for 6 of 11 vendors.
   - *Test:* a packet capture or OS firewall log during a full text session with a local model and Chatwoot on the same host.
   - *Pass:* connections only to the allowlisted hosts. Parlant's OpenRouter default, dashboard and OTEL are off.
4. **Arabic (MSA plus Gulf) and code-switching, with published methodology.** Only Ada lists dialects (voice); others list MSA or `ar-SA` only.
   - *Test:* a tau2-style bilingual task set (EN, MSA, Gulf, code-switch) for retail and support.
   - *Pass:* pass^k per language reported with denominators. Targets are set only after a baseline run.
5. **Replayable simulations.** Ada and Retell document run-to-run variation.
   - *Test:* re-run 200 recorded simulation transcripts in replay mode, with model I/O recorded.
   - *Pass:* 100 % identical verdicts and DB hashes on replay.
6. **Race-free human takeover.** Chatwoot calls its own handoff "best-effort"; Parlant does not re-check manual mode mid-turn.
   - *Test:* 1,000 randomized interleavings of takeover against an in-flight AI turn with tools.
   - *Pass:* 0 AI messages or tool calls committed after the epoch change.
7. **Tenant isolation proof.**
   - *Test:* a cross-tenant fuzz of guessed session IDs, swapped JWTs, foreign IDs in tool arguments, cross-account Chatwoot bot tokens, and loopback tool-server probes.
   - *Pass:* 0 cross-tenant reads, writes or tool executions.
8. **Tamper-evident per-tool audit.** Documented audit logs cover admin and config actions, not each customer-facing tool execution.
   - *Test:* modify, delete or reorder one ledger row.
   - *Pass:* the verifier reports the exact break.

---

## 6. Threat-model inputs, with donor code locations that need guards

| # | Threat | Donor location (`SOURCE_VERIFIED`) | Required Klaint guard |
| --- | --- | --- | --- |
| 6.1 | **Prompt injection via customer text or knowledge** | Retriever `data` and `rules` enter the prompt unsanitized (`parlant@2a463cc:src/parlant/sdk.py:1762-1770`). Tool result `data` is appended to history (`loop/base_loop.py:1186-1197`). `source="customer"` is only a hint (`core/tools.py:308-310`). Moderation covers customer messages only and is provider-dependent (`core/nlp/moderation.py:29`; `docs/moderation.md:55-104`). Chatwoot itself warns that tool responses can carry injected instructions (`DOCUMENTED` C3 URL). | Authority comes only from the broker policy and verified identity, never from text. Retrievers return delimited, cited data and never `rules` derived from content. The commitment hook (KT-05) applies regardless of injection. Run an adversarial suite (KT-08). |
| 6.2 | **Tool authority escalation and bypass** | The four bypass paths in §2.4: `variable_loader.py:169-181`; plugin server `plugins.py:607-612, 851-862` (bound at `sdk.py:4916-4924`); RESOLVE skips the reviewer (`base_loop.py:1002-1004`); MIN effort skips review (`:1082-1084`). Development policy allows everything by default (`core/environment.py:26-38`; `bin/server.py:798-801`; `api/authorization.py:287-318`). A single static admin key (`docs/auth.md:60`). Chatwoot's bot allowlist includes `assignments#create` and `toggle_status` (`access_token_auth_helper.rb:2-7`). Pipecat function calls have no hook (`services/llm_service.py:1228-1236`). | The broker is the **only** registered `ToolService`. No tools on variables, or broker read-only tools only. Run each tenant process in its own network namespace. A startup assertion rejects any `PARLANT_ENV` other than production when the listener is non-loopback. No mutating Pipecat functions. The Chatwoot token is held only by the bridge. |
| 6.3 | **Cross-tenant leakage** | No tenant in `ToolContext` (`core/tools.py:84-106`) or `OwnershipAuthorizer` (`api/authorization.py:405-427`). `ContextVariableStore.GLOBAL_KEY="DEFAULT"` (`core/context_variables.py:83`). CORS `*` with credentials (`api/authorization.py:479-488`). Local SQLite under the Parlant home (`sdk.py:2982-2993`). Session-client IP recording on by default (`bin/server.py:670-685`). Debug logs carry tool arguments and results (`tool_runner.py:92-94, 107-109`). Chatwoot bots are account-scoped and view any conversation in the account (`ensure_current_account_helper.rb:29-33`; `conversation_policy.rb:11, 24-25`). System bots are visible to all accounts (`agent_bot.rb:27-30`). | Process, store, secret and port per tenant. A Chatwoot account and bot per tenant, with system bots disallowed. CORS allowlist per tenant. Log redaction, log level ≥ INFO in production. Session-client recording off unless consented. A cross-tenant fuzz (D7). |
| 6.4 | **Duplicate external commits after uncertain outcomes** | `wait_for` timeout returns "Tool call timed out" to the model (`tool_runner.py:102-105, 121-138`). Concurrent tool calls (`base_loop.py:1146-1148`). A superseding customer message replaces the turn (`base_loop.py:1658-1678`; `CHANGELOG.md` 4.0.2). No idempotency in the API or tools (grep negative, §2.10). Pipecat `cancel_on_interruption=True` by default (`adapters/llm/schemas/direct_function.py:293`; `services/llm_service.py:1091-1094`). Chatwoot retries 3 times (`agent_bots/webhook_job.rb:3`), `source_id` is non-unique (`message.rb:23, 38`), and failure reopens the conversation (`trigger.rb:77-84`). The Botpress Zendesk `createTicket` has no idempotency key (prior pin K08; reference). | The broker's idempotency key binds tenant, session, tool, canonical arguments and the authorizing customer event. The ledger states are PROPOSED → AUTHORIZED → DISPATCHED → COMMITTED, FAILED or **UNKNOWN**. UNKNOWN blocks re-dispatch until a connector-specific reconciliation lookup succeeds. The broker returns `ToolResult` with ledger state, not just "error". Webhook dedupe by `X-Chatwoot-Delivery`. |
| 6.5 | **Human-takeover races** | Parlant re-checks manual mode only at `engine.py:206, 253, 310`, not inside `responder.respond` (`:324-327`). A tool-requested manual switch is applied after the reply (`:931-936`). Chatwoot `bot_handoff!` is best-effort (`conversation.rb:184-187`). `toggle_status` pending→open triggers it (`conversations_controller.rb:83-99`). Assignment locks per call only (`assignment_service.rb:16-19, 37-43`). The Parlant–Pipecat bridge speaks every agent message without checks (`parlant-pipecat@eac20d2:parlant/contrib/pipecat/parlant_service.py:296-298`). | Klaint holds an **ownership epoch** per conversation, incremented on takeover. `on_calling_tools` and the broker refuse a stale epoch. The `on_message_generated` hook BAILs on a stale epoch. The bridge drops AI output with a stale epoch before posting to Chatwoot. Race test D6. |
| 6.6 | **Webhook replay** | Chatwoot signs `ts.body` but receiver-side checks are the integrator's job (`lib/webhooks/trigger.rb:54-60`). A new `delivery_id` UUID per enqueued event (`agent_bot_listener.rb:84-88`). The HubSpot reference accepts future and NaN timestamps (`botpress@956bcde:integrations/hubspot/src/hitl/utils/signature.ts:22-24`). The Pipecat Twilio serializer has no signature validation (§3.1). | Verify over **raw bytes**, constant-time compare, symmetric ±300 s skew, reject non-numeric timestamps, and keep a persisted seen-delivery store with TTL longer than the retry window. Validate `X-Twilio-Signature` at the Klaint TwiML endpoint. Use the Standard Webhooks pattern (`standard-webhooks@ab68441:libraries/python/standardwebhooks/webhooks.py:54-91, 150-160`). |

---

## 7. Build-new analysis: a deterministic tool broker for a safe text-agent MVP

**What was inspected:**

- Parlant v4: the `on_reviewing_tool_calls` hook, the LLM reviewer, the `consequential` flag, `SessionAuthorization` scopes, `ToolRunner` timeout handling, the variable-loader bypass and the plugin server (§2.4).
- Pipecat function calling and its interruption cancel (§3.1).
- Chatwoot message builder and webhook retry (§3.3).
- Botpress Zendesk and HubSpot (prior study plus §3.4).
- tau2-bench DB-state scoring (§4).
- Candidate libraries: DBOS (library), Temporal (server), LangGraph and OpenAI Agents SDK (engines), Standard Webhooks.

**Why that is insufficient:**

- Parlant's gates are either model-mediated (reviewer, consequential review) or stateless (the hook sees a call once and has no memory of prior dispatches).
- Its timeout path converts an unknown commit into an ordinary error.
- Parlant has no tenant notion and no idempotency.
- Pipecat cancels functions on barge-in by default.
- Chatwoot delivers at least once.
- Neither DBOS nor Temporal knows Klaint's tenant, principal, scope or ownership-epoch semantics. Temporal also adds a server.
- tau2 scores outcomes but does not enforce them.

**Smallest missing capability: KT-03 broker.** One Python module in the tenant process:

1. Implements `ToolService` (`parlant@2a463cc:src/parlant/core/tools.py:485-529`) and is the only service registered for consequential tools.
2. Derives tenant, agent, session and customer from the server's own context (`tool_runner.py:80-84`, plus the tenant fixed per process). It never trusts arguments for these.
3. Checks a per-tenant tool allowlist, an argument JSON schema, and the required scopes via `SessionAuthorization.require_scope` (`sdk.py:2528-2575`).
4. Checks the ownership epoch.
5. Computes an idempotency key and writes the ledger row **before** dispatch.
6. Dispatches through a connector with a per-tenant credential.
7. Records COMMITTED, FAILED or UNKNOWN, plus a hash-chain link.
8. Returns a `ToolResult` whose `canned_response_fields` carry the receipt, which KT-05 templates render.

The `on_reviewing_tool_calls` hook BAILs early for calls the broker would deny, so the model regenerates instead of hitting a hard error.

**Adapter confinement:**

- The broker is the only code holding connector credentials.
- Parlant tools are thin stubs that call the broker. No `@p.tool` performs I/O itself.
- Variables never reference mutating tools.
- Each tenant's process runs in its own network namespace, so the loopback tool server (§2.4 path 2) is unreachable cross-tenant. A broker-side shared secret on the stub→broker hop is defense in depth.

**Cost:**

- No new runtime or service. One SQLite or Postgres table per tenant store. Optional `standard-webhooks` dependency.
- Engineering size is `NOT_MEASURED`. It is sized after KT-01, and its main cost is the per-connector reconciliation lookup.
- **Verification:** the KT-03 acceptance tests below, plus D1, D6 and D7. All `NOT_RUN`.
- **Decision: BUILD_NEW, confined to `services/klaint-dialogue/broker/`.** Re-evaluate DBOS only if the ledger needs multi-step durable workflows.

---

## 8. Work packets

Text MVP first (KT-*), then voice (KV-*). Paths are proposed Wispral destinations. No packet is implementation-authorized by this research.

| ID | Depends on | Donor (repo@SHA:path) | Decision | Files affected (proposed) | Acceptance | Tests | Risks | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **KT-00** Pins and notices | — | parlant@2a463cc; pipecat@fda1d5e; chatwoot@caab07a; botpress@956bcde (reference); tau2-bench@033bf08; standard-webhooks@ab68441 | RECORD | `research/` source manifest; `services/klaint-dialogue/NOTICE`; lockfile/SBOM | Exact SHAs, licenses and the enterprise boundary recorded. Fallback pin v3.3.2 `61bba3b` recorded. | Lock and SBOM resolution (`NOT_RUN`) | Transitive CVEs (Parlant constrains several in `[tool.uv]`) | Revert manifest |
| **KT-01** Parlant v4 compatibility spike | KT-00 | parlant@2a463cc: `sdk.py:2966-3036`, `engines/compass/hooks.py:128-151`, `loop/base_loop.py:996-1069` | WRAP (OUT_OF_PROCESS per tenant) | `services/klaint-dialogue/host/tenant_server.py` | One tenant, BLOCK mode, `PARLANT_ENV=production`, `hot_reload=False`, explicit model routes, fake tools. Hooks `on_reviewing_tool_calls`, `on_calling_tools` and `on_message_generated` fire in order. A BAIL in `on_message_generated` lets the hook emit a replacement. RSS/CPU per idle tenant process measured. | Port `tests/core/stable/engines/test_hooks.py`, `tests/sdk/test_hook_results.py` | Hook semantics differ from the docs, which would trigger the v3.3.2 fallback | Switch the pin to v3.3.2 (`CANNED_STRICT`) |
| **KT-02** Tenant host and gateway | KT-01 | parlant `api/authentication.py:193-427`, `api/authorization.py:405-488` | ADAPT | `services/klaint-dialogue/host/{supervisor,gateway,tenant_config}.py` | One process, store, secret set and port per tenant. CORS allowlist. Session-client recording off. Dashboard token unset. Startup fails if not production on a non-loopback bind. | Cross-tenant fuzz (D7): 0 leaks. Port `tests/api/test_authorization.py`. | Memory per tenant | Stop the tenant process; the journal is retained |
| **KT-03** Deterministic broker and outcome ledger | KT-01, KT-02 | parlant `core/tools.py:485-529`, `sdk.py:2528-2575`, `tool_runner.py:80-138` | **BUILD_NEW** (§7) | `services/klaint-dialogue/broker/{service,ledger,policy,reconcile}.py` | Denied, expired, substituted or cross-tenant calls make 0 mutations. A timeout-after-commit gives UNKNOWN, then reconciliation, with no re-dispatch. Duplicate customer sends make 1 mutation. Model arguments cannot set tenant, principal or the idempotency key. A stale epoch is refused. Hash chain verifies. | Fault-injection suite D1 (fake CRM). Port `test_tool_runner.py`. | Connector reconciliation is not always possible | Deny all mutations; text answers stay available |
| **KT-04** Review-hook gate and bypass closure | KT-03 | `base_loop.py:996-1008, 1082-1093`; `variable_loader.py:169-181`; `plugins.py:851-862` | ADAPT | `services/klaint-dialogue/hooks/tool_gate.py`; config lint | The hook BAILs on any call the broker pre-denies. A lint rejects variables bound to mutating tools. Tests confirm the plugin port is unreachable from other tenant namespaces. | A unit test per bypass path (4 paths, §2.4) | Upstream adds new paths | Disable consequential tools |
| **KT-05** Commitment guard (receipts to templates) | KT-03 | `hooks.py:149-150`; `docs/canned-responses.md:286-316` | ADAPT (replaces K13) | `services/klaint-dialogue/hooks/commitment_guard.py`; `policy_content/templates/` | In BLOCK mode, a reply asserting a commitment with no matching COMMITTED receipt is suppressed and replaced by an approved template or a handoff. | 100 adversarial prompts × 3 seeds × EN/AR (D2): 0 violations | Classifier misses paraphrases (needs a conservative lexicon and slots) | Force handoff on any commitment intent |
| **KT-06** Tenant-scoped cited retrieval | KT-02 | `sdk.py:1747-1790`; `docs/retrievers.md` | WRAP (replaces K14) | `services/klaint-dialogue/retrieval/` | Results carry document ID, version and citation. The tenant index is fixed per process. Missing or stale knowledge leads to uncertainty or handoff. Retrieved content never produces `rules`. | Injection corpus in KB documents; stale-document tests | Embedding provider egress | Disable the retriever; answers fall back to handoff |
| **KT-07** Chatwoot bridge (Agent Bot API) | KT-02, KT-03 | chatwoot@caab07a: `lib/webhooks/trigger.rb:54-84`, `agent_bot_listener.rb:36-88`, `conversations_controller.rb:83-99`, `access_token_auth_helper.rb:2-7`; standard-webhooks `webhooks.py:54-160` | API_INTEGRATION (replaces K05–K07) | `integrations/chatwoot/{receiver,poster,ownership}.py` | Raw-body HMAC, ±300 s skew, non-numeric timestamp rejected, delivery-ID dedupe. Takeover increments the epoch. A stale AI output is dropped. One Chatwoot account and bot per tenant. Bot failure → open is reflected as a handoff state. | Replay ×3, tamper, future/NaN timestamps, concurrent takeover (D6), cross-account token | Chatwoot `bot_handoff!` race (upstream) | Detach the bot from the inbox; Chatwoot keeps the human queue |
| **KT-08** Evaluation and simulation harness | KT-03 | tau2-bench@033bf08: `src/tau2/evaluator/evaluator_env.py:17-126`, `src/tau2/domains/retail`, `src/tau2/user`; parlant `core/customers.py:49-56` (PERSONA) | ADOPT_TEST_DEPENDENCY (replaces K15) | `tests/klaint/sim/`, `tests/klaint/tasks/{en,ar}/` | Deterministic DB-hash and ledger scoring. Recorded-I/O replay gives identical verdicts. Arabic MSA, Gulf and code-switch task sets. LLM judge advisory only. | D2, D4, D5 | Simulator-model bias; paid-model cost (use local or recorded runs) | Harness only; no product impact |
| **KT-09** Observability and egress | KT-02 | `bin/server.py:506-545`; `tool_runner.py:92-109`; `adapters/modules/parlant_dashboard/config.py:25` | WRAP | `services/klaint-dialogue/ops/` | OTLP only to a local collector. Tool argument logs redacted. Egress allowlist test D3 passes. | Packet capture / firewall-log test | Hidden SDK egress | Disable exporters |
| **KT-10** First connector (Zendesk, Python) | KT-03 | botpress@956bcde `integrations/zendesk/*` (schema reference); prior K08 | REFERENCE → build Python | `adapters/connectors/zendesk/` | Read-only lookup first. `create_ticket` only through the broker, with an external idempotency lookup for reconciliation. Revoked OAuth is handled. | Fake Zendesk API: 429, timeout-after-POST, foreign requester | Vendor API lacks idempotency keys (reconcile by search) | Revoke the connector credential |
| **KV-01** Pipecat pipeline bridged to Parlant | KT-01..KT-07 green | pipecat@fda1d5e: `processors/frame_processor.py:203`, `transports/smallwebrtc/*`, `audio/turn/smart_turn/local_smart_turn_v3.py:28-50`, `services/{whisper,piper,kokoro}/*`; parlant-pipecat@eac20d2 `parlant_service.py:213-368` (reference) | ADAPT | `services/klaint-dialogue/voice/{parlant_processor,pipeline}.py` | Same tenant process (Python ≥3.11). Parlant in STREAM mode through in-process SSE or SessionTap. **No Pipecat-registered mutating functions.** Model weights pre-provisioned (Kokoro auto-download disabled). | Port `test_frames_interruptible.py` ideas; synthetic audio turn tests | v1.15 turn-strategy API churn | Disable the voice channel; text stays |
| **KV-02** Barge-in truth and speculative-tool hold | KV-01 | parlant `core/sessions.py:355-378` (`spoken_text`), `loop/base_loop.py:1371-1378`; pipecat `services/llm_service.py:1091-1094`, `frames/frames.py:1425-1462` | ADAPT | `voice/barge_in.py`; broker hold flag | On interruption, `spoken_text` is written with only the heard words. The broker holds consequential calls until the final transcript and the turn are confirmed. No commitment is spoken without a receipt. A streaming-mode guard replaces the BLOCK-only hook. | Interrupt-during-tool tests; D2 voice variant | Streaming cannot suppress already-spoken text | Voice in read-only (no consequential tools) |
| **KV-03** Telephony and transfer | KV-01, KT-07 | pipecat `serializers/{twilio,telnyx}.py` (`twilio.py:57-140`) | ADAPT | `voice/telephony/` | `X-Twilio-Signature` validated at the Klaint endpoint. Scoped API-key hang-up credentials. The phone transfer state is separate from Chatwoot assignment, and an unanswered transfer leads to a callback or queue. | Signature tamper/replay; unanswered transfer | Carrier cost; consent and recording law | Disable the inbound number |
| **KV-04** Voice evaluation | KV-02, KT-08 | tau2-bench@033bf08 `src/tau2/voice`, `user_simulation_voice_presets.py` (reference) | REFERENCE_ONLY → test | `tests/klaint/voice/` | Interruption, turn-end and Arabic/English audio fixtures. STT finalization and TTS first-audio recorded separately. | Synthetic plus consented audio only | Synthetic-only bias | Harness only |

---

## 9. Residual gaps (NOT_RUN / BLOCKED)

- Nothing was executed: no Parlant, Pipecat, Chatwoot or tau2 code, no tests, models or calls. Every acceptance criterion above is `NOT_RUN`.
- Parlant v4.0.2 is six days old. Its hook-replacement behaviour, per-tenant process cost and local-model structured-output adequacy all depend on KT-01.
- Not re-inspected in this pass:
  - Botpress `packages/{llmz,cognitive,zai,vai}` licenses.
  - Chatwoot platform-API provisioning endpoints.
  - Rasa Pro/CALM license.
  - promptfoo and deepeval telemetry defaults.
  - NeMo-Guardrails license file.
  - OpenAI Agents SDK trace-export default.
- Competitor rows are summarizer-assisted `DOCUMENTED` claims, not product verification. Three Parlant doc URLs were `BLOCKED_EXTERNAL`.
- Effort and line-count estimates are deliberately omitted (`NOT_MEASURED`).
