# Wispral Specification Frontier

**Status:** canonical research frontier after founding authority merge `3cbe212bf7202c37ec322f114c0e5486e5218d9b`

## Active parent specification

`000-founding-research`

State: `REFINING`

Purpose: replace founding technical assumptions with reproducible evidence sufficient to select the first product implementation Grain.

## Near executable frontier

`000A-acp-qualification`

State: `GRAIN`

Readiness: must be rechecked against live canonical repository state and current ACP/registry/distribution truth before transitioning to `READY`.

No product implementation is authorized by this frontier.

## Planned research children

The parent specification currently anticipates these bounded research outcomes, refined only when they approach eligibility:

- `000A` — ACP capability and representative-agent qualification;
- `000B` — local streaming STT and developer-entity benchmark bakeoff;
- `000C` — turn-taking, pause, and interruption measurement design;
- `000D` — PTY compatibility and fallback threat/maintenance boundary;
- `000E` — platform audio feasibility and privacy/permission observations;
- `000F` — dependency, licensing, provenance, and distribution decision inputs;
- `000G` — founding synthesis and first product-Grain selection.

Only `000A` is refined to task-level execution. The other children remain intentionally coarse until prior canonical evidence can change their shape.

## 000A readiness gate

Before `000A` enters `READY`:

- re-read the current ACP specification, official Rust SDK, and registry;
- verify representative distributions can be pinned;
- verify a disposable synthetic fixture can isolate real repositories;
- verify live probes do not require bypassing agent/provider permission protections;
- verify trace capture can avoid committing credentials or sensitive content;
- amend the spec explicitly if the initially selected representative agents are no longer appropriate.

## Global evidence gate

Before any child is marked `VERIFIED`:

- exact artifacts and source revisions must be recorded;
- failures and unsupported behavior must remain visible;
- unavailable systems must be recorded as unavailable, not PASS;
- the evidence must be sufficient to challenge the resulting architecture recommendation.

## Product-code gate

No Rust product implementation, Cargo workspace, speech engine integration, ACP production client, PTY adapter, TUI, installer, or release is authorized until `000G` selects a bounded first implementation Grain and that Grain independently satisfies readiness.

## Live-truth rule

Live canonical GitHub/repository truth overrides this file. After each merged research unit, re-read the current authority before refining or starting the next child.