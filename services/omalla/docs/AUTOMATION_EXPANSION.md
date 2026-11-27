# Automation expansion

Automation is a core product surface, not a later integration. This document
describes what exists, how the three modes differ, and what comes next.

## Modes

| Mode | Setup | Runs where | Best for |
| --- | --- | --- | --- |
| Native workflow | Install a template or build a graph | Omalla process | Zero-dependency automation, live-call tools, post-call follow-up |
| External n8n | Paste a production webhook URL into an `n8n_workflow` tool | User's n8n | Existing n8n estate, hundreds of connectors |
| Agent-driven | MCP client or REST | External agent | An LLM operating Omalla as a tool |
| Inbound webhook | `POST /v1/hooks/:path` with an API key | Omalla | Other systems starting a flow |

All four converge on the same run record, so the dashboard and test matrix treat
them the same way.

## Live-call tools

### `workflow`

```json
{
  "type": "workflow",
  "name": "check_order",
  "description": "Look up an order status",
  "workflowId": "wf_...",
  "parameters": { "type": "object", "properties": { "orderId": { "type": "string" } } }
}
```

- The workflow must be `active`.
- The idempotency key is `call:{callId}:tool:{toolId}`; a duplicate returns the
  previous run instead of repeating side effects.
- The spoken result is the last non-`end` node output, stringified if needed.
- A failed run returns a retryable tool error; the agent apologises.

### `n8n_workflow`

```json
{
  "type": "n8n_workflow",
  "name": "check_order",
  "serverUrl": "https://n8n.example/webhook/order-status",
  "trustedFields": { "source": "omalla" }
}
```

- POST with `x-omalla-signature: HMAC-SHA256(body)` using the tool's secret.
- Body carries `callId`, tool name, model arguments, caller number, transcript
  tail and a server-resolved `omalla` block.
- The response must contain a `text`, `speech` or `message` field; otherwise the
  tool fails rather than inventing a sentence.
- SSRF policy applies; a local n8n needs `OMALLA_ALLOW_PRIVATE_HTTP=1`.

## Node catalogue

| Node | Purpose | External dependency |
| --- | --- | --- |
| `trigger` | Entry point | none |
| `condition` | Branch on an expression | none |
| `transform` | Build a JSON object | none |
| `http` | Call an API | network |
| `delay` | Bounded wait | none |
| `end` | Stop and keep output | none |
| `local.create_task` | Task in the local store | none |
| `local.update_task` | Update status/assignee | none |
| `local.create_booking` | Booking in the local store | none |
| `local.upsert_contact` | Contact in the local store | none |
| `sms.send` | SMS via simulated or Twilio | carrier for real SMS |
| `email.send` | Email via HTTP provider | SMTP/API |
| `calendar.create_event` | Calendar event | Google/CalDAV |
| `crm.upsert_contact` | CRM upsert | HTTP CRM |
| `human.escalate` | Escalation record | none |
| `call.start` | Start an outbound call | telephony |
| `n8n.webhook` | Call n8n | n8n |
| `trello.*` | Card operations | Trello (optional) |
| `google.*` | Sheets, Gmail, Calendar | Google OAuth |
| `slack.post_message` | Slack message | Slack |
| `whatsapp.send_message` | WhatsApp message | Meta Cloud API |

`trello.*` exists because the original video showed a Trello step. It is not
used by any bundled template.

## Bundled templates

| Template | Trigger | Local-first path |
| --- | --- | --- |
| `ai_receptionist` | call ended | booking + contact + SMS; task + escalation if no booking |
| `appointment_scheduling` | webhook | booking + confirmation SMS |
| `restaurant_reservation` | call ended | booking + SMS |
| `customer_support` | call ended | task + escalation |
| `lead_qualification` | call ended | contact + task |
| `crm_management` | webhook | contact upsert + optional Google Sheets |
| `order_tracking` | webhook | HTTP lookup + SMS |
| `consent_followup` | call ended | consent check + SMS |
| `task_ticket` | webhook | task + escalation |
| `voicemail_triage` | call ended | task + transcript summary |
| `n8n_bridge` | call ended | signed n8n webhook |

Templates install as `draft` by default. Activation is an explicit action.

## Execution guarantees

| Guarantee | Mechanism |
| --- | --- |
| Bounded | 100 steps and 5 minutes per run |
| Retryable | per-node attempts with backoff; final error names the node |
| Idempotent | trigger key remembered for the workflow window |
| Observable | every step stores status, attempts, output and error |
| Safe by default | dry-run HTTP, SSRF guard, no code nodes |
| Tenant-scoped | store calls always receive the run's tenant |

## Roadmap

### Near term

1. **Workflow editor UI.** The dashboard installs and runs templates but does not
   yet edit graphs visually. A JSON editor is the next step; a canvas after that.
2. **Sub-workflows.** A `workflow.run` node so a flow can call another flow with
   a typed input/output contract.
3. **Approvals.** A `human.approval` node that pauses a run until an operator
   accepts or rejects in the dashboard. Needed before any money-moving action.
4. **Durable timers.** Persist delayed runs so a restart does not lose them.
5. **Campaigns.** The data model exists (`Campaign`, quiet hours, concurrency,
   contacts); execution and pacing are not implemented.

### Medium term

6. **Connector SDK.** A small TypeScript interface so a connector can be added
   without editing the engine.
7. **Run replay.** Re-run a failed run with the same trigger payload and a
   dry-run flag.
8. **Assertions in tests.** A workflow test node that fails the run when an
   expression is false, so automations can be regression-tested.
9. **Outbound webhooks.** Emit `run.succeeded` / `run.failed` to external systems
   with a signature.
10. **Arabic-aware templates.** Confirmation and follow-up copy in both
    languages once Arabic TTS exists.

### Explicit non-goals

- Executing arbitrary JavaScript or Python inside a workflow.
- Embedding n8n, Activepieces, Node-RED or Windmill.
- A general-purpose iPaaS with hundreds of connectors.
- Letting the model author or mutate a workflow at runtime.

## Testing automation

- `tests/workflow-templates.test.ts` builds every template, runs the receptionist
  happy path and the no-booking branch, and proves the n8n bridge is optional.
- `tests/server-automation-tools.test.ts` proves the n8n signature and failure
  path, and that a native workflow runs as a live tool, is idempotent, and
  refuses a draft.
- `npm run verify` runs both.

What is not tested: a real n8n instance, a real Google/Slack/WhatsApp account,
and a workflow with more than a handful of nodes under load.
