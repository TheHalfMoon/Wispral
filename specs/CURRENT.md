# Wispral Specification Frontier

**Status:** founding candidate; effective only after the founding-authority PR becomes canonical

## Active parent specification

`000-founding-research`

Proposed state after canonical founding merge: `REFINING`

Purpose: replace founding technical assumptions with reproducible evidence sufficient to select the first product implementation Grain.

## Near executable frontier

`000A-acp-qualification`

Proposed state after canonical founding merge: `GRAIN` only if its exact readiness conditions remain satisfied on canonical `main`; otherwise `REFINING`.

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

Only `000A` is refined to task-level execution in the founding authority. The other children remain intentionally coarse until prior evidence can change their shape.

## Global gate

Before any child is marked `VERIFIED`:

- exact artifacts and source revisions must be recorded;
- failures and unsupported behavior must remain visible;
- unavailable systems must be recorded as unavailable, not PASS;
- the evidence must be sufficient to challenge the resulting architecture recommendation.

## Product-code gate

No Rust product implementation, Cargo workspace, speech engine integration, ACP production client, PTY adapter, TUI, installer, or release is authorized until `000G` selects a bounded first implementation Grain and that Grain independently satisfies readiness.

## Live-truth rule

Live canonical GitHub/repository truth overrides this file. After each merged research unit, re-read the current authority before refining or starting the next child.