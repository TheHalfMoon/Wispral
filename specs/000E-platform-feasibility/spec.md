# Specification 000E — Platform Feasibility

**State:** `REFINING`
**Parent:** `000-founding-research`
**Type:** research parent specification
**Opened by:** the frontier reconciliation (packet F) under Constitution 1.0.0

## Outcome

Produce reproducible evidence of whether the selected donor baselines for WisprSide, WisprStudio and Klaint build, run and behave as their own test suites claim. The evidence covers each pinned revision, on hosted CI and on the founder's Windows laptop (HW-A). Record what fails, what is missing, and what each product would need to change, so that 000G can choose one bounded first Grain from evidence rather than from catalogue claims.

## Research Grains

This specification opens exactly four research Grains. They are defined by these packets in `research/wispral-world-class/packets.json`, which hold the exact pins, acceptance and evidence paths:

| Grain | Product | Scope | Depends on |
| --- | --- | --- | --- |
| `SD-M0` | WisprSide | Desktop dictation fork baseline: build and run the donor's own suites | F, `CORE-00` |
| `ST-D00` | WisprStudio | Voice-production fork baseline with the fake `_echo` engine | F, `CORE-00` |
| `ST-D00b` | WisprStudio | Static comparison of the two candidate production donors | F, `CORE-00` |
| `KT-01` | Klaint | Dialogue-engine compatibility spike with a deterministic fake LLM backend | `CORE-00` |

Every Grain stays `GRAIN` until its own readiness is recorded on its pull request. A Grain becomes `READY` only when all of the following are recorded:

- its dependencies are canonical on `main`;
- its pins are re-verified;
- its evidence path is outside product paths;
- the checks that apply to it are named.

This specification authorizes no other packet.

## In scope

- Building and testing pinned donor revisions as they are, and recording collected, passed, failed and ignored counts.
- Recording failures. They are not fixed here: a failure is evidence, and fixing it is a later, separately authorized delta.
- Measuring resource behaviour where a packet asks for it: idle memory, per-turn latency against a fake backend, and bundled native libraries.
- Observing egress, including the requirement that the voice-production baseline makes no model-hub connections.
- A static comparison of pinned donor trees.

## Out of scope

This specification does NOT authorize:

- product code, a product workspace, or a permanent integration;
- an installer, a signed build, a release, or an updater channel;
- fixing donor code beyond what a packet's acceptance requires to run its suites;
- downloading models or runtimes that a packet forbids;
- creating or publishing a fork repository without the founder's decision on its location and visibility;
- comparative or superiority claims about any product or donor;
- any change to the B2 benchmark lane.

## Acceptance conditions

000E can close only when each of its four Grains is one of:

- `VERIFIED` with the evidence its packet requires, or
- explicitly `CANCELLED` or `SUPERSEDED` with a rationale,

and a short synthesis states, per product, what is established, what failed, and what is unknown.

## Evidence requirements

Each Grain records:

- the exact donor revision;
- the commands run;
- hosted-runner and HW-A environment details;
- raw test counts and failures;
- egress observations where required;
- known limitations.

Evidence lives under `research/wispral-world-class/evidence/`.

Absence is never success: a suite that was not run, or a runner that was unavailable, is recorded as `NOT RUN`.

## Risk

- Native toolchain supply chain: GPU SDKs, compilers, git-sourced crates.
- Heavy dependency closures and first-run downloads.
- Hook or API semantics that differ from the donor's documentation.
- Mistaking a baseline that builds for a qualified product.

## Recovery

Research artifacts are additive. A failed baseline is retained and marked failed. Rollback for a fork baseline is to delete or discard the fork branch.

## Definition of done

Each product has a recorded, reproducible baseline or comparison, and 000G can cite it. "It built once" is not completion.
