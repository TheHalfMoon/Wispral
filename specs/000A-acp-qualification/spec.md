# Specification 000A — ACP Capability and Representative-Agent Qualification

**State:** `VERIFIED`  
**Parent:** `000-founding-research`  
**Type:** research / protocol qualification

## Canonical disposition

Specification 000A is canonically `VERIFIED` at Wispral merge `354695c9f4d406147cbdc425d8f59e841a2f96a3`, produced by guarded squash merge of PR #3 from exact qualified head `6882bc8fac6925e068d40b2b68d46a18e8b03f2f`.

The verified recommendation is:

- ACP classification: `PARTIAL`
- confidence: `MODERATE`
- first structured-path posture: **leading candidate, not yet unconditional `PRIMARY`**

The result establishes real ACP v1 initialization and structured capability/authentication discovery for two pinned representative distributions. It does not establish authenticated prompt portability, streaming portability, active-turn cancellation, permission-request behavior, steering behavior, ACP v2 runtime interoperability, or broad named-agent support.

### Exact qualification proof

- initial behavioral workflow: `33501999725` — `completed/success` across Gemini and Codex ACP cells;
- initial evidence head: `4880c9d2d1d5091bdb4f4ee6acc998826a3bdde4`;
- exact final PR head: `6882bc8fac6925e068d40b2b68d46a18e8b03f2f`;
- final exact-head workflow: `33502915021` — `completed/success` across `Committed evidence verifier`, `ACP v1 probe (gemini)`, and `ACP v1 probe (codex-acp)`;
- PR #3 at merge gate: base `25acbcc29bab262223315a55826e77396cc35822`, exact 14-path scope, `mergeable=true`, submitted reviews `0`, inline review threads `0`;
- Qodo was billing-blocked, CodeRabbit automatic review was skipped by repository-star policy, a manual CodeRabbit review was requested but produced no submitted review, and Cubic supplied summary-only metadata; none was treated as approval;
- guarded merge used expected head `6882bc8fac6925e068d40b2b68d46a18e8b03f2f`;
- canonical merge `354695c9f4d406147cbdc425d8f59e841a2f96a3` is GitHub-signature verified.

## Execution activation history

Readiness was rechecked against canonical Wispral `main` at `25acbcc29bab262223315a55826e77396cc35822` and live ACP authority on 2026-09-01.

The execution gate passed because:

- the active Constitution, architecture invariants, parent Specification 000, and this Grain were canonical;
- ACP specification, official Rust SDK, and registry revisions were publicly accessible and pinned in `docs/research/acp/qualification-inputs.md`;
- Gemini CLI `0.57.0` and Codex ACP `1.7.0` remained current pinned representative distributions in the official registry;
- `fixtures/acp-probe` was synthetic and isolated from user repositories;
- the behavioral probe was unauthenticated, received no repository secrets, stripped known API-key/token environment variables, and did not bypass provider permissions;
- trace capture was limited to the synthetic fixture and sanitized ACP messages.

## Outcome

Produce a reproducible ACP capability matrix and representative-agent observations sufficient to decide whether ACP should be Wispral's primary structured agent-control path for the first product implementation.

## Verified findings

### Native representative — Gemini CLI `0.57.0`

Observed:

- ACP v1 `initialize=SUCCESS`;
- structured agent identity/authentication/capability metadata;
- `loadSession` advertisement;
- prompt modality and MCP capability advertisements;
- `session/new=AUTH_REQUIRED`;
- `session/list=METHOD_NOT_FOUND`.

Not observed:

- authenticated session/prompt;
- streaming updates;
- permission behavior;
- active cancellation;
- graceful ACP shutdown semantics.

### Adapter-mediated representative — Codex ACP `1.7.0`

Observed:

- ACP v1 `initialize=SUCCESS`;
- structured agent identity/authentication/capability metadata;
- `loadSession`, session list/resume/close/delete/subagent capability advertisements;
- `_meta.steering.supported=true` advertisement;
- `session/new=AUTH_REQUIRED`;
- `session/list=AUTH_REQUIRED`.

Not observed:

- authenticated session/prompt;
- streaming updates;
- permission behavior;
- active cancellation;
- steering behavior;
- graceful ACP shutdown semantics.

### Protocol-version constraint

Current ACP authority exposes materially different v1 and v2 surfaces while both pinned current representatives negotiated v1. Wispral therefore must treat protocol-version compatibility as a first-order requirement and must not equate registry recency with one wire schema.

## Why the recommendation is `PARTIAL`

A stronger `PRIMARY` classification is unsupported because core Wispral semantics remain authentication-gated or unobserved: prompt/session execution, streaming, cancellation, structured permissions, steering behavior, and a representative v2 runtime.

A weaker `REJECTED` classification is unsupported because two independent current distributions completed real ACP v1 initialization and exposed meaningful structured capability/authentication surfaces.

## Conditions to promote ACP to `PRIMARY`

Before a production ACP runtime Grain is selected, evidence should establish at minimum:

1. one authenticated non-destructive session/prompt flow on a native ACP agent;
2. one authenticated non-destructive session/prompt flow on an adapter-mediated ACP path, or an explicit evidence-backed reason to defer that representative class;
3. observed streaming/update behavior;
4. observed active-turn cancellation and terminal stop semantics;
5. observed structured permission behavior on a safe synthetic action, or a bounded design for agents that do not expose it;
6. an explicit v1/v2 compatibility decision backed by current ecosystem evidence.

Provider credentials or interactive provider authorization are external evidence inputs. Ordinary repository approval does not substitute for them.

## Product-code authority

None.

This verified research result does not authorize a Cargo product workspace, production ACP client, PTY adapter, speech engine, TUI, installer, release, or public named-agent support claim. Product implementation remains blocked until Specification 000 synthesis selects a bounded first implementation Grain.

## Evidence

Canonical artifacts include:

- `docs/research/acp/qualification-inputs.md`
- `docs/research/acp/capability-matrix.json`
- `docs/research/acp/qualification-report.md`
- `docs/research/acp/evidence-review.md`
- `docs/research/acp/evidence/000a-attempt-001/manifest.json`
- `docs/research/acp/evidence/000a-attempt-001/gemini-probe.json`
- `docs/research/acp/evidence/000a-attempt-001/codex-acp-probe.json`
- `research/000a/acp_probe.py`
- `research/000a/verify_evidence.py`

## Recovery / future evidence

A later ACP experiment may supersede or strengthen this recommendation, but it must preserve this attempt rather than rewriting it. If agent versions, registry state, protocol versions, or authentication conditions materially change, use a new pinned attempt and reconcile the delta explicitly.