# Final handoff and unresolved questions

**For the next session or engineering agent.** Start from live truth, not from this file: re-read `AGENTS.md`, `CONSTITUTION.md`, `docs/canonical/*`, `specs/CURRENT.md`, then fetch `main`, open PR heads and their checks. Compare against [CURRENT_STATE_INVENTORY.md](CURRENT_STATE_INVENTORY.md). If anything changed, update the inventory before acting.

## 1. What this package is

A single candidate planning package on branch `planning/wispral-world-class-master-plan-20261108`. It carries PRs #123, #124 and #125 by merge ancestry, plus new plan documents, executable contracts, design tokens, research reports and governance evidence. Entry point: [WISPRAL_WORLD_CLASS_MASTER_PLAN.md](../../docs/strategy/WISPRAL_WORLD_CLASS_MASTER_PLAN.md).

## 2. How to verify the package

```text
node research/rea/2026-10-21/validate_research.mjs          # PR #124 bundle integrity
node docs/design/tokens/check_contrast.mjs                  # 94 contrast pairs + 40 hue-separation checks
python -I docs/engineering/contracts/run_conformance.py     # 8 contracts, 131 cases, 10 sequences, 6 bundles
python -I research/wispral-world-class/build_packets.py     # regenerate packets (diff must be empty)
node research/wispral-world-class/validate_plan.mjs         # packet graph, links, anchors, names, claims
```

## 3. Questions that genuinely need the founder

**Status on 2026-11-10:**
- **Resolved:**
  - Q-01: Apache-2.0 (#146).
  - Q-02: A040 merged with a qualifying review (#133, `76fe651`).
  - Q-03: correction C2 (#135), then the Constitution 1.0.0 designation.
  - Q-05: the frontier stands, with #118 recorded as an exception (#136).
  - Q-06: Constitution 1.0.0 ratified (#139).
  - Q-12: #123 merged; #124, #127 and #73 close after the records refresh (founder decision FD-19).
  - Q-13: the governance sequence completed.
- **Partly resolved:** Q-04. The founder is to name a standing qualifying-review route (FD-14); until then, a reviewer is named per PR.
- **Open:** Q-07, Q-08, Q-09, Q-10 and Q-11. For Q-10, plan as AGPL-only until the founder records per-file grant scope (FD-08).

The founder decisions are recorded on [PR #155](https://github.com/TheHalfMoon/Wispral/pull/155).

| ID | Question | Why it is the founder's call | Recommended answer |
| --- | --- | --- | --- |
| Q-01 | Which outbound license for the Wispral repository? | Ownership and distribution terms; AGPL-derived Studio code and founder grants interact with it | Decide before CORE-00 closes; keep per-product licensing possible |
| Q-02 | ~~Ratify G1~~: merged as `8d52a45` (owner act, review waived). Ratify the waiver through A040 (#133)? | Constitutional authority act | Yes: obtain A040's qualifying review and merge it before C2 |
| Q-03 | May non-B2 governance PRs edit the allowlisted sections of `specs/CURRENT.md` and `CURRENT_STATE.md`? | Changes who controls the frontier | Yes, exactly the allowlist in correction C2; everything else byte-identical |
| Q-04 | Who are the qualifying reviewers for PLAN, A040, C2, R, G2, D0G and #120? | Governance item 7 (in force): same-vendor agents and `d1-local` cannot qualify | Default: the different-vendor route proven on C1 (DeepSeek via OpenCode), with identity, prompts and outputs recorded; the founder or a named human also qualifies |
| Q-05 | Does the B2R17 frontier stand despite #118 merging with a red required verifier and no approving review? | Governance debt disposition | Decide on fresh evidence (trusted checker run on the #118 merge plus a qualifying retrospective review); R records it as an exception either way |
| Q-06 | Ratify G2 (platform thesis, version 1.0.0)? | Mission change | Yes, after reviewing this plan |
| Q-07 | Which code-signing route and budget (Artifact Signing eligibility depends on the legal entity's region)? | Cost and legal entity | Decide before R2 |
| Q-08 | Approve the Arabic/English speech-panel consent program (forms, storage, retention, withdrawal)? | Personal data and legal obligations | Yes, with legal review |
| Q-09 | Accept gated model terms (pyannote, Cohere Arabic transcribe, Pocket TTS) for evaluation? | Terms acceptance binds the founder | Only when the benchmark Grain needs them |
| Q-10 | For VoiceStudio (AGPL) code and narrow GPL concepts, confirm the private grant covers the specific files the fork keeps? | Only the founder knows the grant's scope; documents stay private | Record a per-file grant-scope flag; never request documents |
| Q-11 | Trademark clearance for Wispral / WisprSide (similarity to Wispr / Wispr Flow) before any public use? | Legal and brand | Run clearance before R3 |
| Q-12 | Dispositions for open PRs after this package merges | Repository owner | Close #123 and #124 as carried, and #127 as superseded by #129 (#126 is already closed); #121 independent; #120 requalifies after C2 |
| Q-13 | Which session owns each open governance PR (#133 and C2)? | Parallel sessions acted on the same sequence on 2026-11-08 | Name one owner per PR; this plan's §2 sequence is canonical |

## 4. Questions engineering can settle with tests (no founder needed)

| Question | Settled by |
| --- | --- |
| Parlant v4.0.2 or v3.3.2? | KT-01 spike |
| Does the Handy baseline build and pass on Windows? | SD-M0 |
| Which local ASR routes meet latency and RSS budgets on HW-A? | BM-03 and the WB-AR pilot |
| Do IBM Plex Sans Arabic diacritics and digits render well at UI sizes? | DS-01 |
| Coral or product-accent "listening" colour? | DS-04 A/B |
| Is the Windows egress harness strong enough? | CORE-07 positive and negative controls |
| Exact Sentrdel composition semantics in the Python port | CORE-03 / CORE-05 donor test vectors |
| Memory per tenant process for Klaint | KT-01 measurement |

## 5. Known limitations of this package

- No donor was built or run when this package was written; no audio, model, GPU, native insertion or competitor trial was executed. *(2026-11-10: the donor baselines `SD-M0` and `ST-D00` and the Klaint spike `KT-01` have since run; see `specs/000E-platform-feasibility/tasks.md`.)*
- The WisprSide competitor refresh for 2026-11-08 was incomplete; WisprSide competitor cells rely on PR #124's 2026-10-21 observations.
- Several model weight licenses and gated terms remain to be read (listed in the [model strategy](../../docs/engineering/WISPRAL_MODEL_STRATEGY.md#4-initial-candidates-to-benchmark-not-selections)).
- The validators run manually today. No workflow runs `validate_plan.mjs`, `check_contrast.mjs` or `run_conformance.py`. A follow-up PR adds that CI job; this planning-only PR edits no workflow.
- `validate_plan.mjs` rejects `ready: true` by design. When an authority marks a packet READY, the record goes in that authority's PR, not in `packets.json`. The validator gains a `readiness_record` rule in the same follow-up.
- The six review passes were fresh-context agents of the same model family as the author, so they are **not** qualifying independent reviews under the proposed Governance item 7. Every BLOCKER and MUST FIX they raised was addressed ([INDEPENDENT_REVIEW.md](INDEPENDENT_REVIEW.md)); governance-required qualifying reviews remain to be done.

## 6. Do not

Merge anything without the governance sequence; weaken, skip or relabel any check; push to `main`; publish, release or announce any product; enable paid inference; accept model terms on the founder's behalf; request the founder's private legal documents; modify frozen B2 evidence.
