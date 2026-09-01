# Specification 000 — Founding Research and Qualification

**State:** `REFINING`  
**Type:** research / architecture-selection parent specification

## Outcome

Produce enough reproducible technical, security, platform, licensing, and benchmark evidence to select Wispral's first bounded product implementation Grain without relying on unverified market assumptions or preferred technologies.

## Canonical progress after 000A

Specification `000A-acp-qualification` is `VERIFIED` at canonical merge `354695c9f4d406147cbdc425d8f59e841a2f96a3`.

Its evidence classifies ACP as `PARTIAL` with `MODERATE` confidence:

- two pinned current representative distributions completed real ACP v1 initialization;
- structured capability/authentication discovery is therefore established for those exact representatives;
- authenticated session/prompt, streaming, cancellation, structured permission, steering, and representative ACP v2 runtime behavior remain unverified;
- ACP is a leading structured-path candidate, not a permanent production selection;
- a version-aware integration boundary is likely required, but production architecture remains unauthorized.

This evidence closes the first child and permits the next coarse child, `000B`, to be refined. It does not authorize 000B execution or product code.

## Problem

Wispral has a strong product thesis but no product implementation evidence yet. Several major choices remain hypotheses:

- structured agent protocol versus PTY boundaries beyond the bounded 000A result;
- authenticated ACP lifecycle, streaming, permission, cancellation, and v1/v2 portability;
- local speech backend selection;
- developer context value;
- turn-taking and interruption architecture;
- platform audio constraints;
- dependency/licensing posture;
- security/privacy boundaries;
- initial supported platform and agent surface.

Beginning implementation before resolving the highest-leverage uncertainties would create expensive lock-in and encourage marketing claims ahead of evidence.

## In scope

This parent specification may authorize bounded research artifacts and non-product experiment harnesses needed to answer:

1. Which structured agent-control semantics are available through ACP today?
2. Which representative agents expose the required lifecycle, stream, permission, and cancellation behavior?
3. What must a PTY compatibility fallback do, and what semantic guarantees can it not provide?
4. Which local streaming STT candidates best fit developer speech under a disclosed benchmark?
5. Does bounded repository context materially improve developer-entity accuracy?
6. What turn-taking and interruption measurements are necessary before hands-free design?
7. What platform audio/privacy constraints materially change architecture?
8. Which dependencies and licenses are acceptable for the first product Grain?
9. What exact first implementation outcome has the highest evidence-to-risk ratio?

## Out of scope

Specification 000 does NOT authorize:

- production CLI/TUI implementation;
- a Cargo product workspace intended for release;
- a permanent STT engine selection without comparative evidence;
- a permanent agent integration;
- public performance/superiority claims;
- release publication;
- Homebrew/Cargo/npm distribution;
- always-listening microphone behavior;
- TTS/full duplex/AEC product work;
- cloud accounts or hosted services;
- plugin architecture;
- multi-agent orchestration;
- custom coding-agent or foundation-model work.

Research code, if necessary, must remain clearly marked experimental and must not silently become production architecture.

## Acceptance conditions

Specification 000 can close only when:

- `000A` through the evidence-selected required children are either `VERIFIED`, explicitly `SUPERSEDED`, or explicitly `CANCELLED` with rationale;
- ACP and PTY recommendations state both supported and unsupported semantics;
- the STT recommendation is backed by a reproducible bakeoff or explicitly records why no selection is yet justified;
- WispralBench has an executable or otherwise independently reproducible founding scoring contract for the metrics used in selection;
- the security/privacy analysis identifies first-product constraints and fail-closed requirements;
- dependency/license/provenance decisions are sufficient to create the first production dependency baseline;
- platform scope for the first implementation is explicit;
- `000G` records a decision matrix and selects exactly one bounded first product Grain, or records that evidence is insufficient to implement product code;
- no claim in README/roadmap exceeds the resulting evidence.

## Evidence requirements

Each research child must preserve enough of the following to reproduce or challenge its conclusion:

- source URLs/repository SHAs/releases;
- exact agent/model/library versions;
- OS/hardware information where behavior depends on them;
- commands/configuration;
- raw protocol traces or sanitized machine-readable observations where permitted;
- raw benchmark outputs;
- scoring logic;
- failures/timeouts/unsupported paths;
- licensing/provenance notes;
- limitations and alternative explanations.

## Risk

Primary risks:

- benchmark leakage or tuning to known fixtures;
- confusing prototype behavior with supported product behavior;
- overfitting architecture to one agent or one protocol version;
- adopting a speech engine based on vendor-provided numbers rather than Wispral workloads;
- treating protocol documentation as proof of a specific agent implementation;
- expanding research until no product decision is ever made.

## Recovery

Research artifacts are additive and non-production. A failed experiment should be retained when useful, marked invalid/failed accurately, and superseded by a new preregistered attempt rather than rewritten as a success.

A research conclusion may be superseded by later evidence without requiring compatibility migration of product code because Specification 000 precedes product implementation.

## Definition of done

Specification 000 is complete only when the repository has enough evidence to choose the first implementation Grain while naming remaining uncertainty. "We researched a lot" is not completion.