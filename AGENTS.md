# Wispral Repository Instructions

Wispral is a voice-native control plane for AI coding agents. It is not a dictation application, a proprietary agent, an IDE, or a thin wrapper around one vendor's CLI.

## 1. Canonical reading order

Before changing the repository, read in this order:

1. `AGENTS.md`
2. `CONSTITUTION.md`
3. `docs/canonical/CURRENT_STATE.md`
4. `docs/canonical/ARCHITECTURE_INVARIANTS.md`
5. `docs/canonical/PROGRAM_ROADMAP.md`
6. `specs/CURRENT.md`
7. the complete active specification authority chain (`spec.md`, `plan.md`, `tasks.md`)
8. referenced research, benchmark, security, ADR, contract, and source files

Live repository and GitHub truth override stale handoffs, plans, summaries, and chat history.

## 2. Language

All repository and GitHub technical content MUST be written in English, including code, comments, specifications, plans, tasks, reports, benchmark artifacts, evidence, commit messages, pull-request text, and reviewer responses.

## 3. Proof before done

No compatibility, latency, accuracy, privacy, security, performance, quality, portability, or adoption claim may be represented as established unless the exact claim is supported by reproducible evidence against the exact revision being claimed.

`PASS`, `SUPPORTED`, `VERIFIED`, `FASTER`, `LOWER LATENCY`, `OFFLINE`, and similar words are evidence-bearing terms, not marketing adjectives.

If a required check was not run, record `NOT RUN`. If a system was unavailable, skipped, rate-limited, billing-blocked, or unsupported, do not convert absence of evidence into PASS.

## 4. SpecGrain execution discipline

Wispral uses recursive specifications and evidence-backed execution.

A candidate unit may execute only when it is small enough to be independently understood, bounded, recovered, and verified. The active lifecycle is:

`DRAFT -> SHAPED -> REFINING -> GRAIN -> READY -> RUNNING -> VERIFYING -> VERIFIED -> CONTROLLED`

Exceptional states include `BLOCKED`, `FAILED`, `SUPERSEDED`, `CANCELLED`, and `STALE`.

When a unit is too large, refine it. Do not compensate with a larger prompt, broader context, or speculative implementation.

## 5. Change discipline

- Understand before editing.
- Prefer the smallest coherent change that can prove one outcome.
- No drive-by refactors.
- No speculative abstractions.
- No hidden scope expansion.
- No dependency without a documented capability, security, portability, maintenance, and licensing justification.
- Prefer standard-library and already-approved primitives where they meet the contract.
- Keep optional integrations behind explicit boundaries.
- Preserve reversibility and fail-closed behavior at trust boundaries.

## 6. Product invariants

Unless the constitution is amended, every implementation must preserve these properties:

- agent and model vendor neutrality;
- local-first operation for the core control path;
- explicit user authority for consequential actions;
- interruption and cancellation as first-class control semantics;
- raw speech provenance separate from interpreted intent;
- no silent conversion of tentative speech into destructive authority;
- protocol-first integration, with compatibility fallbacks isolated from the core;
- deterministic policy and state transitions around probabilistic speech/model components;
- open, reproducible benchmark methodology;
- no telemetry dependency for core functionality.

## 7. Rust-first engineering

Rust owns the product runtime unless evidence demonstrates a better boundary.

C/C++ libraries, Python research tooling, TypeScript ecosystem adapters, shell bootstrap code, or other languages may be used when they provide a demonstrated capability that is impractical or materially worse in Rust. Such use must remain bounded and documented.

When Rust product code exists, the minimum local verification set is:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo test --workspace --all-targets --all-features --locked
```

Additional platform, audio, protocol, security, benchmark, or integration gates apply when the touched surface requires them.

## 8. Research and benchmark discipline

External repositories and products are references, not undocumented code sources. Record material provenance and licenses before adapting code.

Benchmarks must disclose, as applicable:

- corpus/task definitions;
- hardware and OS;
- software/model versions and digests;
- configuration;
- warm/cold conditions;
- raw outputs;
- scoring logic;
- statistical method;
- known limitations;
- losing metrics and failed runs.

Do not optimize a benchmark against hidden information and then present the result as general performance.

## 9. Planning discipline

Near-term work may be detailed. Distant work must remain coarse until evidence makes refinement useful. The program roadmap is directional authority; `specs/CURRENT.md` owns the executable frontier.

Do not create an implementation specification merely because a roadmap horizon exists. Fresh evidence and satisfied dependencies must select the next bounded unit.

## 10. Pull requests and completion

Every implementation or evidence PR should identify:

- active spec and task IDs;
- exact outcome and changed surface;
- acceptance evidence;
- checks run and checks not run;
- benchmark provenance where applicable;
- residual risk and recovery notes;
- external material provenance;
- exact head under review.

Reconcile head, base, CI, reviews, threads, comments, mergeability, and canonical `main` before merge. Use expected-head protection for guarded merges when available. Re-read canonical authority after merge before starting dependent work.