# Klaint UX specification

**Status:** CANDIDATE SPEC — nothing built or tested. Applies the [design system](WISPRAL_DESIGN_SYSTEM.md) to a Klaint operations console over the Parlant service and optional Chatwoot inbox ([source decision](../../research/wispral-world-class/SOURCE_DECISION_MATRIX.md#klaint)). Capability IDs (KL-xx) refer to the [product capability catalog](../strategy/WISPRAL_PRODUCT_VISION.md#23-klaint--conversational-ai-agents).

**Design priority:** operations teams. Agent behavior, policy, live sessions, testing, handoff, audit and business outcomes must be understandable without AI expertise. The console explains *why* the agent did something, in plain language, with one click to the evidence.

## 1. Information architecture

```text
Klaint console
├─ Overview      outcomes: resolved, handed off, blocked by policy, cost; alerts
├─ Agents        per agent:
│   ├─ Behavior      rules, step-by-step policies, glossary, tone (plain-language editor over Parlant's code-first SDK, versioned)
│   ├─ Responses     approved responses (required for commitments), variables
│   ├─ Tools & permissions   each tool: what it does, risk tier, ALLOW / ASK human / DENY rules
│   ├─ Knowledge     sources, freshness, citations preview
│   └─ Versions      diff, publish, roll back
├─ Test Lab      scenarios, simulated customers, suites, run history, regressions
├─ Live          active conversations, AI/human owner, take over, watch
├─ Approvals     ASK queue: what the agent wants to do, for whom, why it needs a person, wait timer; Approve / Deny
├─ Inbox         (optional) Chatwoot, embedded or linked
├─ Audit         searchable event log: messages, guideline matches, tool proposals, verdicts, outcomes
└─ Settings      channels, model provider per tenant, retention, roles, integrations
```

The console never exposes raw prompts as the main editing surface. Rules are edited as "When… / Then…" statements, policies as numbered steps, tools as permission rules. Because Parlant 4 removed most configuration REST routes, the console writes versioned agent definitions that the tenant's Parlant process loads through the SDK.

**MVP console scope.** The first Klaint release does not build a full console. Operators use Chatwoot for live conversations and takeover, a local trace viewer for Parlant's OpenTelemetry traces, tau2-bench reports for the Test Lab, and a read-only ledger query for audit. The console below is the stable-release (tier S) target, sized after operators have used those tools.

**Health.** Every list distinguishes "nothing happening" from "pipeline unhealthy": a banner names the failing component (dialogue engine, model provider, channel, connector) with the time it failed and what customers currently see.

## 2. The "why" panel (signature interaction)

Every agent message in Live, Test Lab and Audit can expand into a **why panel**:

```text
Customer: "Cancel my order and refund me now"
Agent:    "I can help cancel order #4821. Refunds over 200 SAR need a team member — I've asked one to join."
──────────────────────────────────────────────────────────
Matched rules        • Order cancellation (v12) • Refund > threshold → human (v12)
Tool proposals       cancel_order(#4821)  → ALLOW  (rule: own order, status=processing)  → COMMITTED ✓ (ledger #a91f)
                     issue_refund(350 SAR) → ASK   (rule: amount > 200 SAR)              → handed to human
Response source      Approved response "refund_needs_human" (no free text for commitments)
Knowledge cited      Refund policy v3 §2
Model                provider/model + revision · policy version 12 · tenant: acme
```

Verdict chips use the shared state colors with icons and **localized words** (English: Allowed / Needs approval / Blocked / Undecided-treated-as-blocked; Arabic: مسموح / يحتاج موافقة / مرفوض / غير محسوم — يُعامل كمرفوض), never ALL-CAPS codes. The panel **opens with one plain-language summary** ("Order cancelled. The refund is waiting for a team member."); rule matches, tool proposals, ledger ids and model identity sit behind a **Details** disclosure with glossary tooltips for terms such as ledger, epoch and reconciling. Codes and ids render in left-to-right isolated spans inside Arabic text. Outcome chips: Committed, Not sent, Unknown — checking, Failed.

## 3. Live sessions and takeover (KL-06)

- **Conflicts:** if another operator already owns the conversation, the button shows "Owned by Sara" with a request-handover action; a takeover that fails (network or Chatwoot error) shows "Takeover failed — retry" and the AI stays paused until resolved.
- **Approvals queue:** each ASK item shows the customer context, the proposed action in plain words, why it needs a person, how long the customer has waited and what the customer sees meanwhile ("A team member is checking this"). Approve or Deny writes a verdict with the operator's identity; the broker then executes or refuses.
- **Data tables** default to Western tabular digits in both languages; search matches Western and Arabic-Indic digits.

- Live list shows each conversation's owner (AI / human name), channel, language, sentiment hint (labelled as an estimate), and time waiting.
- **Take over** is a single prominent button. On click: the ownership epoch advances, an "AI paused — you own this conversation" banner appears for the operator, and any AI message already generating is discarded (shown as "discarded: takeover"). Returning to AI is explicit.
- Handoff summaries (later tier) are labelled "AI summary — check before relying on it" and link every claim to the transcript line it came from.

## 4. Test Lab (KL-08)

- **Scenario editor:** persona, goal, language (including Arabic dialect labels), constraints, expected outcome expressed as ledger facts ("order #X cancelled; no refund issued without approval").
- **Suites** run on every agent version before publish; the publish button shows the last suite result and blocks on hard-gate failures (authority, commitment, tenancy).
- **Results** show pass/fail per scenario with the full conversation, why panels, and a diff against the previous version's run.
- Simulated customers are clearly labelled synthetic; the simulator model and version are part of each run record.

## 5. Tools & permissions editor (KL-04, KL-05)

Each tool is a card: description in plain language, connector, risk tier (read / reversible write / irreversible / money), and rules. Rules are deterministic conditions over authenticated context and tool arguments, with a live "test this rule" box. The editor refuses to save a rule that would let model-supplied identifiers select the tenant or customer.

## 6. Audit (KL-07)

Append-only, filterable by conversation, customer identifier (where permitted), tool, verdict, outcome and time. Export to CSV/JSON. Each event shows tenant, policy version and model identity. Deletion requests produce tombstones that keep the audit chain verifiable without retaining personal content.

## 7. Customer-facing chat widget (KL-09)

- Accessible, RTL-correct widget; language follows the customer; clear disclosure that the customer is talking to an AI agent and how to reach a person.
- Visible handoff state ("A team member is joining").
- No dark patterns: the "talk to a person" path is always available.

## 8. Core journeys and acceptance

| Journey | Acceptance (G-E2E) |
| --- | --- |
| K1 Ops lead creates an agent from a template, adds a refund policy guideline and an approved response, runs the starter suite, publishes | Completed without editing any prompt text; suite result shown before publish |
| K2 Customer asks for an unauthorized refund in Arabic | Approved response or handoff only; why panel shows ASK/DENY with the rule |
| K3 Operator takes over mid-generation | No AI message delivered after takeover; banner shown |
| K4 Connector timeout after commit | Outcome shows "UNKNOWN — reconciling", then "COMMITTED" after the read-back; no duplicate action |
| K5 Auditor exports all refund-related tool proposals for a week | CSV with verdicts, outcomes and policy versions |
| K6 Two tenants | Operator of tenant A cannot see or search tenant B data anywhere in the console |
