# Specification 000A — Evidence Review

**Date:** 2026-09-01  
**Review target before this note:** `f96f0777aa4266cf1d033295d6b21d51bcec1219`  
**Recommendation reviewed:** `PARTIAL` / `MODERATE`

## Result

`PASS WITH EXPLICIT EXTERNAL LIMITS`

This result means the committed `PARTIAL` recommendation is consistent with the evidence available to Specification 000A. It does **not** mean authenticated ACP prompt, cancellation, steering, or permission behavior passed.

## Independent authority re-read

Immediately before this review, the current upstream authority was re-read rather than relying on the earlier research summary.

The pinned revisions remained current:

- ACP specification repository `main`: `01b9d6e9c094d31cdea6d88768a9dd31b089ccef`;
- official ACP Rust SDK `main`: `754d5aa1ce2cfa54ba2c2a6d3edc7e7b6bce28eb`;
- ACP Registry `main`: `c7f1825666fb0008172e5fb93a58071a9618041e`.

The representative package pins and current registry selection therefore remained comparable to Attempt 001 at review time.

## Deterministic evidence verification

Workflow run `33502702519` executed on head `f96f0777aa4266cf1d033295d6b21d51bcec1219` and completed all three jobs successfully:

- `Committed evidence verifier` — `success`;
- `ACP v1 probe (gemini)` — `success`;
- `ACP v1 probe (codex-acp)` — `success`.

The committed evidence verifier independently reads the raw Attempt 001 JSON, manifest, and capability matrix. It fails closed when:

- the allowed evidence vocabulary drifts;
- an untested agent enters the matrix;
- an `OBSERVED`/blocked/unsupported state disagrees with raw outcomes;
- Gemini/Codex version or fixture bindings drift;
- the `PARTIAL` recommendation changes without the expected evidence contract;
- cancellation/permission/steering behavior is promoted from `NOT_TESTED` without evidence;
- common credential-like patterns appear in committed evidence.

The verifier passed.

## Manual raw-evidence reconciliation

The raw traces were independently reread against the matrix and report.

Confirmed:

- Gemini `initialize=SUCCESS`, protocol v1, version `0.57.0`;
- Gemini `session/new=AUTH_REQUIRED`;
- Gemini `session/list=METHOD_NOT_FOUND`;
- Codex ACP `initialize=SUCCESS`, protocol v1, version `1.7.0`;
- Codex ACP `session/new=AUTH_REQUIRED`;
- Codex ACP `session/list=AUTH_REQUIRED`;
- Codex session-list/resume and steering capability are advertisements observed in the initialization result, not behavior claims;
- no session/prompt completed;
- no streaming update was observed;
- cancellation, steering behavior, and permission behavior remain `NOT_TESTED`;
- no untested registry agent is labeled supported.

The `PARTIAL` recommendation remains appropriately conservative.

## Secret/provenance review

The extracted Attempt 001 artifact text received a bounded scan for common OpenAI/GitHub/Google/Bearer/API-key/token patterns with no credential-like values detected.

The committed raw evidence contains only the synthetic fixture path placeholder, public package/protocol metadata, and unauthenticated error/capability messages.

External methodology provenance is recorded: the official ACP Registry protocol matrix was studied as an independent reference, but Wispral uses its own probe and does not copy upstream behavioral results into `OBSERVED` states. The registry repository is Apache-2.0 licensed.

## External review surfaces

External automated review availability was checked but is not represented as evidence that did not exist:

- Qodo: `BILLING_BLOCKED`;
- CodeRabbit automatic review: `SKIPPED` by repository-star policy;
- CodeRabbit manual review: requested on PR #3; no submitted review was present at this review gate;
- Cubic: generated a PR summary consistent with the evidence, but no submitted approval/review was present;
- submitted GitHub PR reviews: `0` at this gate.

None of these unavailable/skipped/summary-only systems is labeled `PASS`.

## Challenge to the recommendation

A stronger `PRIMARY` classification was considered and rejected because the core Wispral thesis depends on behavior that Attempt 001 could not observe without provider authentication:

- session/prompt execution;
- streaming updates;
- active-turn cancellation;
- permission request/response binding;
- steering behavior;
- v2 representative runtime behavior.

A weaker `REJECTED` classification was also considered and rejected because two independent current distributions successfully negotiated ACP v1 and exposed meaningful structured capability/auth surfaces.

Therefore `PARTIAL / MODERATE` remains the narrowest recommendation supported by both positive and missing evidence.

## Review disposition

A011 may be treated as complete for Specification 000A's evidence contract because:

- upstream authority was freshly re-read;
- a separate deterministic verifier passed;
- raw traces were manually reconciled against the matrix;
- credential/provenance checks were performed;
- external review-system unavailability is explicit rather than converted into approval;
- the recommendation was challenged in both stronger and weaker directions.

A012 remains separate. Canonical closeout may occur only after the exact evidence PR is qualified, merged, and canonical `main` is reread.
