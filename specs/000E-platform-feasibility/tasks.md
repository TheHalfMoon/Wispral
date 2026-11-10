# Specification 000E Tasks

This file tracks Grain progression. Pins, acceptance and evidence paths are in `research/wispral-world-class/packets.json`.

## Grains

- [ ] `SD-M0`: WisprSide fork baseline. State `GRAIN`. Its packet dependencies are canonical: F at `b6c8507` and `CORE-00` at `81b2de6`. The founder's decision on the fork's location and visibility, required by the Platform frontier rules, is recorded below. **Linux half recorded** (run 42536089224: 338 passed / 0 failed / 18 ignored; lint, keyboard and Playwright 2/2 pass), in `research/wispral-world-class/evidence/baselines/handy-73cc857/`. The HW-A half is pending.
- [ ] `ST-D00`: WisprStudio fork baseline with the fake `_echo` engine. State `GRAIN`. Its packet dependencies are canonical: F at `b6c8507` and `CORE-00` at `81b2de6`. The founder's decision on the fork's location and visibility, required by the Platform frontier rules, is recorded below. **Linux half recorded** (rerun 42538071852: 13,307 + 600 passed, 0 failed; Electron checks pass), in `research/wispral-world-class/evidence/baselines/voicestudio-200286c/`. **Finding:** HTTPS connections to Hugging Face addresses (confirmed by the DNS answers) despite `HF_HUB_OFFLINE=1`, reproduced in both runs; the zero-model-hub criterion fails on Linux. **HW-A half recorded** in `windows-hwa/` (2026-11-10): `backend/tests` 590 passed / 10 skipped; `tests/` 12,990 passed / 82 failed / 21 errors / 183 skipped, plus 21 tests deselected because they hang on the WSL `bash`; frontend passes; `bun run test` 4 failed; `check:electron` 19 failed at its test step, so its build and packaging steps are NOT RUN. Windows egress: a test clones from GitHub through the real `git`, `test_setup_preflight` downloaded a runtime from GitHub, and a Python worker opened a connection to a Hugging Face address (test not identified). **Not VERIFIED**: the packet's network condition fails on both platforms. No remediation is recorded yet.
- [x] `ST-D00b`: static comparison of the two production donors. `VERIFIED`: merged as `5c2663f146ac7dcb04a0da1e13d0aeb1129afb64` (#142), with a post-merge reread on #142. VoiceStudio stays the lead (capability 10 vs 7; delta size 17 vs 21.5). Evidence: `research/wispral-world-class/evidence/baselines/studio-lead-comparison.md`.
- [ ] `KT-01`: Klaint dialogue-engine spike with a fake LLM backend. State `GRAIN`. Needs `CORE-00`.

## Fork decision (founder, 2026-11-09)

The founder first chose **private forks**. Later the same day the founder instructed "make the repo public" and confirmed that it applies to **both forks**. Both are now **public**.

Each fork was created as a new repository (not a GitHub fork) holding the donor's history up to the pinned commit, unchanged. Before the visibility change, each was verified to hold only the three refs below at the pin, with no releases, secrets or issues. The pinned commits are themselves public upstream, so the change published nothing that was not already public. The donor's own LICENSE and notices are kept in the tree.

| Grain | Fork | Donor and pin | Pushed refs |
| --- | --- | --- | --- |
| `SD-M0` | `TheHalfMoon/wisprside` (public) | `cjpais/Handy@73cc8579cff74e97e08de9d86035a92e4335ff7f` (931 commits) | `main` and `upstream/pin` at the pin; tag `upstream-73cc857` |
| `ST-D00` | `TheHalfMoon/wisprstudio` (public) | `debpalash/VoiceStudio@200286ccff6f28faaf51bb08b2a5b54c460b39f4` (6,603 commits) | `main` and `upstream/pin` at the pin; tag `upstream-200286c` |

**GitHub Actions is disabled** in both forks. It was disabled before any code was pushed, and both forks show zero workflow runs. The donors' workflows (9 and 30) are present in the trees but cannot run.

**Before a baseline run:**

- the donor's release, signing and updater workflows are disabled on a baseline branch;
- the runner plan is agreed with the founder. Hosted Actions minutes are free for public repositories; paid runners or services are never used without authorization.

Nothing is published as a release.

## Closeout

- [ ] Write the per-product 000E synthesis (established, failed, unknown).
- [ ] Reconcile the 000E disposition into `specs/CURRENT.md`, in its designated sections only.

## Product-code gate

000E authorizes no product code, installer or release. The product-code gate in `specs/CURRENT.md` applies unchanged until a 000G decision.
