# Wispral Specification Frontier

**Status:** canonical founding-research frontier after ACP qualification merge `354695c9f4d406147cbdc425d8f59e841a2f96a3`

## Active parent specification

`000-founding-research`

State: `REFINING`

Purpose: replace founding technical assumptions with reproducible evidence sufficient to select the first product implementation Grain.

## Verified child

`000A-acp-qualification`

State: `VERIFIED`

Canonical evidence merge: `354695c9f4d406147cbdc425d8f59e841a2f96a3`

Disposition:

- ACP recommendation: `PARTIAL`
- confidence: `MODERATE`
- ACP remains the leading structured-path candidate, not an unconditional production selection;
- authenticated prompt/stream/cancellation/permission behavior and representative ACP v2 runtime behavior remain unverified;
- no broad named-agent support claim is authorized.

See `docs/research/acp/qualification-report.md` and `docs/research/acp/capability-matrix.json` for the bounded evidence.

## Next refinement candidate

`000B` — local streaming STT and developer-entity benchmark bakeoff

Status: intentionally coarse; eligible for bounded refinement after 000A canonical closeout.

This does **not** make 000B `READY`, authorize an experiment, select an STT engine, or authorize product speech code. Its specification must be shaped from current canonical evidence and must satisfy its own readiness gate before execution.

## Remaining planned research children

The parent specification currently anticipates these bounded research outcomes, refined only when they approach eligibility:

- `000B` — local streaming STT and developer-entity benchmark bakeoff;
- `000C` — turn-taking, pause, and interruption measurement design;
- `000D` — PTY compatibility and fallback threat/maintenance boundary;
- `000E` — platform audio feasibility and privacy/permission observations;
- `000F` — dependency, licensing, provenance, and distribution decision inputs;
- `000G` — founding synthesis and first product-Grain selection.

000A evidence now permits 000B to be refined from its coarse parent description. 000C–000G remain intentionally coarse until preceding canonical evidence can materially shape them.

## Global evidence gate

Before any child is marked `VERIFIED`:

- exact artifacts and source revisions must be recorded;
- failures and unsupported behavior must remain visible;
- unavailable systems must be recorded as unavailable, not PASS;
- evidence claims must remain narrower than the raw observations;
- the evidence must be sufficient to challenge the resulting architecture recommendation.

## Product-code gate

No Rust product implementation, Cargo workspace, permanent speech engine integration, ACP production client, PTY adapter, TUI, installer, or release is authorized until `000G` selects a bounded first implementation Grain and that Grain independently satisfies readiness.

The verified 000A result does not weaken this gate.

## Live-truth rule

Live canonical GitHub/repository truth overrides this file. After each merged research unit, re-read current authority before refining or starting the next child.