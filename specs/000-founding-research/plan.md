# Specification 000 Plan

## Strategy

Resolve architecture uncertainty in dependency order. Do not run every research stream in parallel merely because all are interesting.

The first question is whether a structured protocol can provide the control semantics Wispral needs. That answer changes how later interruption, permission, compatibility, and UI experiments should be designed.

## Child sequence

### 000A — ACP capability and representative-agent qualification

Answer what ACP itself exposes and what selected real agents actually implement.

Outputs should include:

- protocol/version notes;
- capability matrix;
- representative raw traces or command logs;
- cancellation and permission observations;
- gaps that require adapter or fallback behavior;
- recommendation for whether ACP can be the primary control path.

### 000B — Local streaming STT and developer-entity bakeoff

Refine only after 000A records the instruction/event boundary that speech must feed.

Compare justified local candidates on Wispral-specific developer speech rather than generic vendor benchmarks. Establish a cloud reference only if useful and permitted.

### 000C — Turn-taking and interruption measurement

Use the event boundaries learned from 000A and timing instrumentation assumptions from 000B.

Define how to measure thinking pauses, endpointing, barge-in, cancellation request, acknowledgement, and stale output.

### 000D — PTY compatibility boundary

Refine after ACP gaps are known. Determine whether PTY fallback can add meaningful agent breadth without pretending to provide structured semantics that are not observable.

### 000E — Platform audio/privacy feasibility

Qualify the first proposed platform set, including microphone permissions, device selection, capture behavior, process permissions, and local model/runtime constraints.

### 000F — Dependency/license/provenance decision inputs

Synthesize actual dependencies selected by evidence. Evaluate maintenance, portability, licenses, patent terms where relevant, native build burden, binary size, supply-chain surface, and update cadence.

### 000G — Founding synthesis and first product Grain selection

Produce a decision matrix using evidence from prior children.

The result must select one first product Grain or explicitly conclude that no implementation is yet justified.

## Decision criteria for the first product Grain

Prefer the candidate that maximizes:

- direct proof of the core voice-control thesis;
- user-visible value;
- interoperability learning;
- reversibility;
- measurable acceptance;
- narrow blast radius;
- low dependency lock-in;
- ability to falsify a bad architecture early.

Do not choose a unit merely because it produces the most impressive demo.

## Progressive-refinement rule

Only 000A is task-refined by the founding authority.

For 000B–000G, this plan provides expected outcomes and ordering only. Their exact specs/tasks must be shaped from canonical evidence after preceding children merge.

## Experiment discipline

For comparative experiments:

1. preregister the question, corpus/input, scoring, environment, and stopping rule;
2. freeze or digest fixtures before the qualifying run when practical;
3. do not inspect hidden/held-out scoring material after the run begins;
4. retain invalidated attempts with the invalidation reason;
5. never use an invalidated attempt to support a superiority claim;
6. record environment changes that make attempts non-comparable.

## External-source discipline

Protocol docs and vendor benchmarks are inputs to experiment design, not substitutes for Wispral qualification.

When a public project is used as a code donor rather than a reference, perform license/provenance review before adaptation.

## Closeout

After 000G:

- update `docs/canonical/CURRENT_STATE.md` with exact evidence and decisions;
- update `specs/CURRENT.md` to the selected first product Grain or `POST_000_OBSERVATION` if none is selected;
- create ADRs only for durable decisions actually supported by the research;
- reconcile README claims;
- do not preserve stale architecture hypotheses as though they remained undecided.