# Specification 000A Tasks

## Readiness

000A is eligible for execution only after the founding-authority PR is canonical and these conditions are rechecked:

- `CONSTITUTION.md`, architecture invariants, and Specification 000 are canonical;
- current ACP authority remains publicly accessible;
- selected representative distributions can be pinned;
- a disposable fixture repository can be used;
- no task requires bypassing provider permissions or exposing credentials.

**Readiness result:** `PASSED` on 2026-09-01 against canonical Wispral `25acbcc29bab262223315a55826e77396cc35822`; execution inputs are recorded in `docs/research/acp/qualification-inputs.md`.

## Grain tasks

- [x] **A001 — Pin ACP authority.** Exact ACP specification, official Rust SDK, registry, representative tags, and package versions are recorded.
- [x] **A002 — Define capability schema.** `docs/research/acp/capability-matrix.json` uses the explicit evidence states `OBSERVED`, `DOCUMENTED_NOT_OBSERVED`, `UNSUPPORTED`, `NOT_TESTED`, `BLOCKED_EXTERNAL`, and `UNKNOWN`.
- [x] **A003 — Create disposable ACP probe fixture.** `fixtures/acp-probe` is synthetic; Attempt 001 records exact file and tree SHA-256 digests.
- [x] **A004 — Build minimal research client/probe path.** `research/000a/acp_probe.py` is Python-standard-library research instrumentation only and is not a Wispral product runtime.
- [x] **A005 — Qualify native ACP representative.** Gemini CLI `0.57.0` completed v1 initialization; session creation was authentication-blocked; prompt/stream/cancellation/permission behavior remains explicitly unobserved.
- [x] **A006 — Qualify adapter-mediated representative.** Codex ACP `1.7.0` completed v1 initialization; session creation/list behavior was authentication-blocked; prompt/stream/cancellation/permission behavior remains explicitly unobserved.
- [x] **A007 — Run cancellation fixture.** Active cancellation was `NOT_TESTED` because no unauthenticated session/prompt could exist. The external authentication blocker is preserved rather than bypassed or inferred through documentation.
- [x] **A008 — Run safe permission fixture.** Structured permission behavior was `NOT_TESTED` because the no-secret attempt could not create a safe authenticated action. No provider permission protection was disabled.
- [x] **A009 — Reconcile capability matrix.** Every behavioral `OBSERVED`/blocked/unsupported state points to committed raw Attempt 001 evidence; untested registry agents remain untested.
- [x] **A010 — Produce ACP recommendation.** `docs/research/acp/qualification-report.md` classifies ACP `PARTIAL` with `MODERATE` confidence and explicit promotion conditions.
- [x] **A011 — Independent evidence review.** Current ACP authority was freshly reread; `research/000a/verify_evidence.py` passed against committed raw evidence/matrix; manual reconciliation and bounded secret/provenance review passed. External automated reviewers were unavailable/skipped/summary-only and are not represented as approval. See `docs/research/acp/evidence-review.md`.
- [ ] **A012 — Canonical closeout.** Update `specs/CURRENT.md` and parent Specification 000 only after exact-head evidence is merged and canonical truth is re-read.

## Attempt 001 evidence

- Workflow: `000A ACP Qualification` run `33501999725` — `completed/success` across both representative matrix cells.
- Initial evidence head: `4880c9d2d1d5091bdb4f4ee6acc998826a3bdde4`.
- GitHub pull-request test merge executed by the workflow: `378e1192837ec02733419fb077e8101d37cd292c` with parents canonical base `25acbcc29bab262223315a55826e77396cc35822` and evidence head `4880c9d2d1d5091bdb4f4ee6acc998826a3bdde4`.
- Gemini workflow artifact `9798068210`: `sha256:d8781662cf11d78e59d90d7a1b8f010854a462942f928ecf007f5902e93469cd`.
- Codex ACP workflow artifact `9798065060`: `sha256:23cc0841cf961f03205c5bc39e32b3a95386c8c2ad277fc9cc0a54bdde0756c1`.
- Extracted artifact text received a bounded credential-pattern scan; no common credential-like value was detected. This does not claim perfect secret detection.
- Exact-head verification workflow `33502702519` on head `f96f0777aa4266cf1d033295d6b21d51bcec1219` completed `success` across the committed-evidence verifier plus both representative probe cells.

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
