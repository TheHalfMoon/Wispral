# Specification 000E Tasks

This file tracks Grain progression. Pins, acceptance and evidence paths are in `research/wispral-world-class/packets.json`.

## Grains

- [ ] `SD-M0`: WisprSide fork baseline. State `VERIFYING`. The evidence is merged: the Linux half in #148 (`48fb9c0`) and the Windows half in #150 (`131a2bf`). Each had a fresh-context review and a founder merge, and each PR's head checks were green (1 pass, 4 skipping; no red check).
  - Acceptance item 1, the suites, is recorded on both platforms.
  - Item 2, the debug and release builds, is recorded on Windows.
  - Item 3, the bundled DLL list, is recorded only in the narrowed form that the #150 review required: the DLLs next to `handy.exe`, the 13 DLLs the donor's Windows bundle config would ship from this build, and `handy.exe`'s direct imports. No VC++ runtime was staged, because `HANDY_VC_REDIST_DIRS` was unset. The bundled DLLs' own imports and the installer contents are NOT RUN.
  - Installer packaging stays deferred, as the packet says.

  **`VERIFIED` needs the founder to confirm that this narrowed item 3 satisfies the packet.** History: Its packet dependencies are canonical: F at `b6c8507` and `CORE-00` at `81b2de6`. The founder's decision on the fork's location and visibility, required by the Platform frontier rules, is recorded below. **Linux half recorded** (run 42536089224: 338 passed / 0 failed / 18 ignored; lint, keyboard and Playwright 2/2 pass), in `research/wispral-world-class/evidence/baselines/handy-73cc857/`. **HW-A half recorded** in `research/wispral-world-class/evidence/baselines/handy-73cc857/windows-hwa/` (2026-11-10): `cargo test --locked` 332 passed / 0 failed / 18 ignored (the 6-test gap to Linux is platform-gated tests, listed); lint and keyboard pass; Playwright 2/2 pass on the fifth run, after two environment fixes (a `bunx` shim, and a browser path around a dangling junction); of the four runs that did not pass, runs 1 and 3 are logged as failed, run 2's log was overwritten and run 4's outcome is not recorded, all disclosed; debug and release `cargo build --locked` succeed; the DLLs the donor's Windows bundle config would ship from this build and the `handy.exe` imports are recorded; the installer contents are NOT RUN, and this build staged no VC++ runtime because `HANDY_VC_REDIST_DIRS` was unset. Installer packaging NOT RUN (deferred by the packet); the app was not launched.
- [ ] `ST-D00`: WisprStudio fork baseline with the fake `_echo` engine. State `BLOCKED`. The packet's mandatory condition (no model or runtime download, and zero model-hub connections) fails on both platforms.
  - #151 (`c407288`) attributes the Hugging Face lookups seen in its attribution runs to the AudioSeal watermark download (`torch.hub` through `urllib`, which ignores `HF_HUB_OFFLINE`). For the Linux traffic this is an inference, as #151 says. The baseline's Windows SYN to a Hugging Face address is not shown to be this test.
  - On Windows, `test_setup_preflight` also attempted a runtime download from GitHub.
  - **Unblocking needs both** a founder decision on remediation **and** a rerun on both platforms showing zero model-hub connections and no runtime download.
  - The original baseline stays recorded as it is.

  History: Its packet dependencies are canonical: F at `b6c8507` and `CORE-00` at `81b2de6`. The founder's decision on the fork's location and visibility, required by the Platform frontier rules, is recorded below. **Linux half recorded** (rerun 42538071852: 13,307 + 600 passed, 0 failed; Electron checks pass), in `research/wispral-world-class/evidence/baselines/voicestudio-200286c/`. **Finding:** HTTPS connections to Hugging Face addresses (confirmed by the DNS answers) despite `HF_HUB_OFFLINE=1`, reproduced in both runs; the zero-model-hub criterion fails on Linux. **HW-A half recorded** in `research/wispral-world-class/evidence/baselines/voicestudio-200286c/windows-hwa/` (2026-11-10): `backend/tests` 590 passed / 10 skipped; `tests/` 12,989 passed / 82 failed / 24 errors / 175 skipped / 8 xfailed / 1 xpassed (console totals), plus 21 hanging tests deselected (cause inferred: a bare `bash` starts the WSL launcher) and one module that failed to collect; frontend passes; `bun run test` 4 failed; `check:electron` 19 failed at its test step, so its build and packaging steps are NOT RUN. Windows egress: a test clones from GitHub through the real `git`; `test_setup_preflight` attempted a runtime download from GitHub; a Python process sent a SYN to a Hugging Face address (test not identified). **Not VERIFIED**: the packet's network condition fails on both platforms. No remediation is recorded yet.
- [x] `ST-D00b`: static comparison of the two production donors. `VERIFIED`: merged as `5c2663f146ac7dcb04a0da1e13d0aeb1129afb64` (#142), with a post-merge reread on #142. VoiceStudio stays the lead (capability 10 vs 7; delta size 17 vs 21.5). Evidence: `research/wispral-world-class/evidence/baselines/studio-lead-comparison.md`.
- [ ] `KT-01`: Klaint dialogue-engine spike with a fake LLM backend. State `BLOCKED`. Merged in #152 (`246283f`).
  - Acceptance item 3 fails: the integrated tool server cannot be disabled, and a forged `customer_id` is accepted. It can clear only through either a packet amendment that rescopes the item, or an implemented gate with evidence that a forged call has no effect and returns no data.
  - Item 4 is NOT RUN for the local CPU model. It clears only when the founder names a model **and** the measurement is run and recorded.
  - Item 2 (BAIL) holds only in BLOCK mode, not in the default STREAM mode.

  History: **Spike recorded** in `research/klaint-spike/` with evidence in `research/wispral-world-class/evidence/kt01-hwa/` (2026-11-10, Parlant v4.0.2 `2a463ccd`, fallback v3.3.2 `61bba3b2`, HW-A, deterministic fake backend only). The three required hooks fire in order on v4; Parlant's own hook tests pass 9/9 on the fake; BAIL replaces the message in BLOCK mode only, not in the default STREAM mode; session tokens isolate customers. **FAIL:** the integrated tool server cannot be disabled and accepts a forged `customer_id` (v4 and v3). **NOT RUN:** the pinned local CPU model (none authorized). Fake-backend p95 579 ms per turn (Parlant overhead, not model latency); idle working set 194 MB for the process that runs both the server and the test client. Decision: v4.0.2 with Klaint-side gates. **Not VERIFIED.**

## Fork decision (founder, 2026-11-09)

The founder first chose **private forks**. Later the same day the founder instructed "make the repo public" and confirmed that it applies to **both forks**. Both are now **public**.

Each fork was created as a new repository (not a GitHub fork) holding the donor's history up to the pinned commit, unchanged. Before the visibility change, each was verified to hold only the three refs below at the pin, with no releases, secrets or issues. The pinned commits are themselves public upstream, so the change published nothing that was not already public. The donor's own LICENSE and notices are kept in the tree.

| Grain | Fork | Donor and pin | Pushed refs |
| --- | --- | --- | --- |
| `SD-M0` | `TheHalfMoon/wisprside` (public) | `cjpais/Handy@73cc8579cff74e97e08de9d86035a92e4335ff7f` (931 commits) | `main` and `upstream/pin` at the pin; tag `upstream-73cc857` |
| `ST-D00` | `TheHalfMoon/wisprstudio` (public) | `debpalash/VoiceStudio@200286ccff6f28faaf51bb08b2a5b54c460b39f4` (6,603 commits) | `main` and `upstream/pin` at the pin; tag `upstream-200286c` |

**GitHub Actions was disabled at creation** in both forks. It was disabled before any code was pushed, and at that time both forks showed zero workflow runs. The donors' workflows (9 and 30) were present in the trees but could not run.

**Update (2026-11-10).** For the baselines, Actions was enabled on both forks. Every donor workflow is `disabled_manually` (9 in `wisprside`, 30 in `wisprstudio`). As of 2026-11-10, per the GitHub API, the only workflows that have run are Wispral's own, each on its own branch: `wispral-baseline-sd-m0` (1 run), `wispral-baseline-st-d00` (2 runs) and `wispral-attrib-st-d00` (1 run).

**Before a baseline run:**

- the donor's release, signing and updater workflows are disabled on a baseline branch;
- the runner plan is agreed with the founder. Hosted Actions minutes are free for public repositories; paid runners or services are never used without authorization.

Nothing is published as a release.

## Closeout

- [ ] Write the per-product 000E synthesis (established, failed, unknown).
- [ ] Reconcile the 000E disposition into `specs/CURRENT.md`, in its designated sections only.

## Product-code gate

000E authorizes no product code, installer or release. The product-code gate in `specs/CURRENT.md` applies unchanged until a 000G decision.
