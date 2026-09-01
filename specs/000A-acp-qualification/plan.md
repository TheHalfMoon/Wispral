# Specification 000A Plan

## Execution model

Use three layers of evidence:

1. **Protocol evidence** — current ACP specification and official Rust SDK documentation/code.
2. **Registry/distribution evidence** — current ACP registry records and exact agent launch packages/commands.
3. **Behavioral evidence** — disposable live probes against representative agents where authorized access exists.

Documentation alone may establish what a protocol claims to support. It may not establish what a named agent implementation actually does.

## Phase A — Pin protocol authority

Record:

- ACP repository commit or release;
- official Rust SDK release and commit when needed;
- registry release/index digest or commit;
- relevant schema/protocol document hashes where practical.

Extract only the lifecycle and capability surfaces material to Wispral.

## Phase B — Build capability matrix skeleton

Create a versioned data artifact, preferably JSON plus a human-readable report, with explicit states such as:

- `OBSERVED`
- `DOCUMENTED_NOT_OBSERVED`
- `UNSUPPORTED`
- `NOT_TESTED`
- `BLOCKED_EXTERNAL`
- `UNKNOWN`

Never collapse `DOCUMENTED_NOT_OBSERVED` into `OBSERVED`.

## Phase C — Prepare disposable probe repository

The fixture should contain only synthetic, license-clear files and safe commands. It should be sufficient to ask the agent to:

- inspect one file;
- explain a small deterministic property;
- optionally propose or perform a reversible fixture edit if permission qualification requires it;
- accept a cancellation during a deliberately long but safe request where feasible.

Record the fixture tree digest before qualifying runs.

## Phase D — Native ACP representative probe

Initial candidate: Gemini CLI using its current ACP invocation.

Capture:

- exact version;
- launch/auth path;
- initialization exchange;
- session creation;
- prompt/update sequence;
- capability declarations;
- cancellation behavior;
- permission behavior when safely triggerable;
- exit/shutdown behavior.

If live access is unavailable, complete all non-authenticated protocol/distribution evidence and mark live fields `BLOCKED_EXTERNAL` rather than substituting another claim.

## Phase E — Adapter-mediated representative probe

Initial candidate: Codex through the current ACP registry adapter.

Repeat the same matrix, additionally identifying which behavior comes from:

- ACP core;
- the adapter;
- the underlying Codex CLI/runtime;
- Wispral's test client.

This distinction is important for future maintenance and failure diagnosis.

## Phase F — Cancellation focus

Where safe and observable:

1. start a request that produces continuing work/output;
2. capture timestamp of client cancellation request;
3. observe whether protocol/agent acknowledges cancellation;
4. observe whether further session updates arrive;
5. distinguish local client stop from underlying agent stop;
6. record unsupported or ambiguous semantics explicitly.

No performance claim is authorized from 000A unless timing methodology is separately specified. The goal is semantic qualification first.

## Phase G — Permission focus

Use the safest available fixture that can produce a structured permission request.

Record:

- request identity;
- action description/metadata;
- available response choices;
- whether response is tied to the request;
- effect of deny;
- effect of stale/mismatched response if safely testable;
- behavior when permission capability is unavailable.

Do not enable dangerous/yolo/bypass modes to manufacture a result.

## Phase H — Synthesis

Classify ACP for Wispral:

### `PRIMARY`

Structured semantics are sufficient for the first control path; gaps are bounded and adapters remain maintainable.

### `PARTIAL`

ACP is useful but a material required semantic is absent or inconsistent enough that the first product must expose limitations or pair it with another boundary.

### `REJECTED`

ACP cannot provide a trustworthy primary path for the first product thesis under current evidence.

The recommendation must name evidence and limitations.

## Artifacts expected

The qualifying branch should eventually add, names may be refined before execution:

```text
docs/research/acp/qualification-report.md
docs/research/acp/capability-matrix.json
docs/research/acp/attempts/<attempt-id>/environment.json
docs/research/acp/attempts/<attempt-id>/commands.txt
docs/research/acp/attempts/<attempt-id>/sanitized-trace.jsonl
fixtures/acp-probe/...
```

Do not commit credentials, auth tokens, personal filesystem paths when avoidable, or sensitive provider responses.

## Verification

Before claiming 000A complete:

- validate JSON artifacts deterministically;
- verify all referenced fixture/revision digests;
- ensure secrets scan of committed traces is clean using the strongest available repository/tooling mechanism;
- manually reconcile matrix entries against raw evidence;
- record any live checks that could not be repeated in CI;
- independently re-read current ACP authority before final recommendation because the ecosystem is fast-moving.