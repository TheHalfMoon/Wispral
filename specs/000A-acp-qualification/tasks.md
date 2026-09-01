# Specification 000A Tasks

## Readiness

000A is eligible for execution only after the founding-authority PR is canonical and these conditions are rechecked:

- `CONSTITUTION.md`, architecture invariants, and Specification 000 are canonical;
- current ACP authority remains publicly accessible;
- selected representative distributions can be pinned;
- a disposable fixture repository can be used;
- no task requires bypassing provider permissions or exposing credentials.

## Grain tasks

- [ ] **A001 — Pin ACP authority.** Record exact ACP specification, official Rust SDK, and registry revisions/releases used by the qualification.
- [ ] **A002 — Define capability schema.** Add deterministic schema/data format with explicit evidence states (`OBSERVED`, `DOCUMENTED_NOT_OBSERVED`, `UNSUPPORTED`, `NOT_TESTED`, `BLOCKED_EXTERNAL`, `UNKNOWN`).
- [ ] **A003 — Create disposable ACP probe fixture.** Synthetic repository only; record exact tree/content digest and safe probe prompts.
- [ ] **A004 — Build minimal research client/probe path.** Use the smallest non-production mechanism capable of recording sanitized ACP exchanges. Do not create a product architecture around the probe.
- [ ] **A005 — Qualify native ACP representative.** Initial candidate Gemini CLI, subject to live registry revalidation. Record exact environment, handshake, session, prompt, stream, cancellation, permission, error, and shutdown observations.
- [ ] **A006 — Qualify adapter-mediated representative.** Initial candidate Codex ACP adapter, subject to live registry revalidation. Separate adapter behavior from underlying-agent behavior where observable.
- [ ] **A007 — Run cancellation fixture.** Observe request, acknowledgement/stop semantics, and stale updates without making latency superiority claims.
- [ ] **A008 — Run safe permission fixture.** Exercise a reversible/non-sensitive action if the agent exposes structured permission; otherwise record the exact unsupported/blocked state.
- [ ] **A009 — Reconcile capability matrix.** Every non-documentation claim must point to raw behavioral evidence; untested registry agents remain untested.
- [ ] **A010 — Produce ACP recommendation.** Classify `PRIMARY`, `PARTIAL`, or `REJECTED` for the first Wispral control path with limitations and confidence.
- [ ] **A011 — Independent evidence review.** Re-read protocol/registry authority, inspect raw artifacts for claim drift and secrets, and challenge the recommendation before closeout.
- [ ] **A012 — Canonical closeout.** Update `specs/CURRENT.md` and parent Specification 000 only after exact-head evidence is merged and canonical truth is re-read.

## Stop conditions

Stop dependent tasks and record `BLOCKED`/`FAILED` rather than improvising if:

- protocol or registry versions cannot be pinned;
- selected agent authentication is unavailable and the task requires live behavior;
- a probe would require disabling safety/permission protections;
- trace capture would expose credentials that cannot be reliably sanitized;
- the disposable fixture cannot isolate real user repositories;
- the representative agent changes materially mid-attempt.

## Completion evidence

000A completion requires:

- exact changed paths;
- capability matrix;
- environment/version records;
- sanitized raw trace or equivalent behavioral evidence;
- fixture digest;
- commands/configuration;
- validation output for structured artifacts;
- limitation register;
- final ACP recommendation;
- PR/exact-head verification and canonical post-merge reconciliation.