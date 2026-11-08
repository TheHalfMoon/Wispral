# Specification 000E Tasks

This file tracks Grain progression. Pins, acceptance and evidence paths are in `research/wispral-world-class/packets.json`.

## Grains

- [ ] `SD-M0`: WisprSide fork baseline. State `GRAIN`. Its dependencies are met: `CORE-00` is `VERIFIED`, and the fork exists (see Fork decision below).
- [ ] `ST-D00`: WisprStudio fork baseline with the fake `_echo` engine. State `GRAIN`. Its dependencies are met: `CORE-00` is `VERIFIED`, and the fork exists (see Fork decision below).
- [ ] `ST-D00b`: static comparison of the two production donors. Its dependencies are canonical (F `b6c8507`, `CORE-00` `81b2de6`), and it was executed in its own pull request: `research/wispral-world-class/evidence/baselines/studio-lead-comparison.md`. VoiceStudio stays the lead (capability 10 vs 7; delta size 17 vs 21.5). It becomes `VERIFIED` after merge and a canonical reread.
- [ ] `KT-01`: Klaint dialogue-engine spike with a fake LLM backend. State `GRAIN`. Needs `CORE-00`.

## Fork decision (founder, 2026-11-09)

The founder chose **private forks**.

GitHub does not allow a private fork of a public repository. Each fork is therefore a new private repository holding the donor's history up to the pinned commit, unchanged. The donor's own LICENSE and notices are kept in the tree.

| Grain | Fork | Donor and pin | Pushed refs |
| --- | --- | --- | --- |
| `SD-M0` | `TheHalfMoon/wisprside` (private) | `cjpais/Handy@73cc8579cff74e97e08de9d86035a92e4335ff7f` (931 commits) | `main` and `upstream/pin` at the pin; tag `upstream-73cc857` |
| `ST-D00` | `TheHalfMoon/wisprstudio` (private) | `debpalash/VoiceStudio@200286ccff6f28faaf51bb08b2a5b54c460b39f4` (6,603 commits) | `main` and `upstream/pin` at the pin; tag `upstream-200286c` |

**GitHub Actions is disabled** in both forks. It was disabled before any code was pushed, and both forks show zero workflow runs. The donors' workflows (9 and 30) are present in the trees but cannot run.

**Before a baseline run:**

- the donor's release, signing and updater workflows are disabled on a baseline branch;
- the Actions-minutes budget for private runners is agreed with the founder. Windows minutes count double, and paid minutes are never used without authorization.

Nothing is published as a release.

## Closeout

- [ ] Write the per-product 000E synthesis (established, failed, unknown).
- [ ] Reconcile the 000E disposition into `specs/CURRENT.md`, in its designated sections only.

## Product-code gate

000E authorizes no product code, installer or release. The product-code gate in `specs/CURRENT.md` applies unchanged until a 000G decision.
