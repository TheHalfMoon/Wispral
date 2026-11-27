# REA: Automation

The reference architecture puts n8n behind the voice agent. Omalla keeps that
path and adds a native engine so automation works without a second product.
This document records the public facts that shaped the design.

## n8n

| Fact | Detail |
| --- | --- |
| Licence | Sustainable Use License (source-available, not OSI). Files containing `.ee.` need a commercial n8n licence. |
| Integration surface | Webhook node (production URL), "Respond to Webhook" node, HTTP Request node, REST API |
| Execution model | Node graph, per-node items, expressions (`{{ $json.field }}`), retries at workflow level |
| Deployment | Single process or queue mode with Redis and workers |

**Consequence:** Omalla never copies n8n source and never bundles it. The
integration is an HTTP POST to a production webhook, with a JSON response that
the agent speaks. Import/export is a data-format convenience, not code reuse.
On import, n8n `Code` nodes are deliberately **not** executed or translated into
executable Omalla code; they are recorded as unsupported so a workflow cannot
smuggle arbitrary code into the engine.

### Live-call bridge

```
agent decides to call tool "check_order"
  → ToolRuntime.callN8n()
  → POST https://n8n.example/webhook/order-status
     headers: x-omalla-signature: HMAC-SHA256(body)
     body: { callId, tool, arguments, caller, transcriptTail, omalla: {...} }
  → n8n Respond to Webhook: { "text": "Order 123 shipped yesterday." }
  → Omalla extracts text → TTS
```

The signature is over the exact JSON body with the tool's shared secret. The
`omalla` metadata block is server-resolved; the model cannot set tenant, call id
or destination. Failures return a retryable tool error and the agent apologises
rather than claiming success.

## Activepieces

- MIT for content outside `packages/ee/` and `packages/server/api/src/app/ee`.
- Enterprise directories carry their own licence.
- Piece-based connectors with a TypeScript SDK.

**Consequence:** reference only. Omalla's node set is its own; no piece code was
copied. Activepieces' shape informed the "one node, one integration" palette.

## Node-RED

- Apache-2.0.
- Flow-based, message-passing runtime; huge node ecosystem with mixed licences.

**Consequence:** compatible in spirit (wires, nodes, function nodes), but no
runtime embedding. Omalla's expression syntax is intentionally simpler and does
not evaluate JavaScript from workflow data.

## Windmill

- AGPLv3 for `backend/` and `frontend/` except enterprise snippets, which are
  proprietary.
- Script-first workflows (Python/TypeScript/Bash) with a queue.

**Consequence:** AGPL makes embedding unattractive for an Apache-2.0 product.
Omalla does not embed Windmill and does not copy its queue design. Script nodes
are out of scope; arbitrary code execution inside a multi-tenant workflow is a
security boundary Omalla does not want.

## Baserow and Twenty

- Baserow: MIT for client-side code, with `premium/` and `enterprise/` under
  separate licences.
- Twenty: mostly AGPLv3, with `/* @license Enterprise */` files under a
  commercial licence and some MIT packages.

**Consequence:** both are optional external systems reached over HTTP. No code
is copied, and no database schema is transplanted.

## The three automation modes

| Mode | Who runs it | How it is invoked | State |
| --- | --- | --- | --- |
| External n8n | User's n8n instance | `n8n_workflow` voice tool, signed webhook | implemented, unit-tested |
| Native engine | Omalla | `workflow` voice tool, `call_ended` trigger, `POST /v1/workflows/:id/run` | implemented, verified |
| Agent-driven | External agent via MCP/API | MCP tools, REST, CLI | implemented, smoke-tested |

A fourth path, `POST /v1/hooks/:path`, lets any system start a workflow with a
tenant API key.

## Native engine semantics

- **Deterministic.** No LLM chooses the next node. Conditions are expressions
  over the run scope.
- **Bounded.** Max steps (default 100) and a five-minute budget per run.
- **Idempotent.** A trigger key is remembered for the workflow's window;
  duplicates return `skipped` with no steps.
- **Retryable.** Per-node attempts with bounded backoff; the final error names
  the node.
- **Dry-runnable.** HTTP is recorded and answered synthetically; nothing leaves
  the machine.
- **SSRF-aware.** Private and link-local targets are rejected unless the operator
  explicitly enables `OMALLA_ALLOW_PRIVATE_HTTP`.
- **Secret-aware.** Integration nodes read credentials from the encrypted store,
  never from workflow JSON.

## n8n interop mapping

| n8n node | Omalla node | Notes |
| --- | --- | --- |
| Webhook | `trigger` (`webhook`) | path suffix in trigger config |
| IF / Switch | `condition` | expression + true/false edges |
| HTTP Request | `http` | method, URL, headers, body; SSRF checked |
| Set | `transform` | explicit field mapping |
| Wait | `delay` | bounded seconds |
| Respond to Webhook | `end` | run output retained |
| Trello | `trello.*` | optional, credential-gated |
| Google Sheets/Calendar/Gmail | `google.*` | optional, credential-gated |
| Slack | `slack.post_message` | optional |
| WhatsApp | `whatsapp.send_message` | optional |
| Code | none | rejected on import, never executed |

## Why not embed a workflow product

1. **Licence.** n8n's Sustainable Use License and Windmill's AGPL are not
   compatible with shipping them inside an Apache-2.0 binary.
2. **Security.** Arbitrary script nodes inside a multi-tenant call path are a
   remote-code-execution surface.
3. **Zero-cost.** A second runtime means a second database, queue and upgrade
   path. The native engine is a few thousand lines and no extra service.
4. **Product fit.** Voice automation needs a small, predictable node set, not
   four hundred connectors. External systems are reached over HTTP.

## Open questions

- A signed n8n *response* (n8n signing its reply) is not standard; Omalla
  authenticates the request and validates the response shape, not its origin.
- Durable timers across restarts: delays are in-process. A crash loses a pending
  delay; the run is marked failed, not silently resumed.
- Multi-tenant queueing: runs execute in-process with a concurrency cap. A real
  queue is a later concern.
