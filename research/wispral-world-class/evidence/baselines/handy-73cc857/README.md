# SD-M0 baseline: WisprSide donor Handy@73cc857

**Grain:** `SD-M0` (Specification 000E). Packet in `research/wispral-world-class/packets.json`.

**Status:** both halves are recorded. The HW-A (Windows) half, with suites, debug and release binaries, and the DLLs the Windows bundle config would ship (installer not built), is in [`windows-hwa/`](windows-hwa/README.md). The Grain becomes `VERIFIED` only when this evidence is merged after review.

| Item | Value |
| --- | --- |
| Donor and pin | `cjpais/Handy@73cc8579cff74e97e08de9d86035a92e4335ff7f` (MIT) |
| Research fork | `TheHalfMoon/wisprside` (public) |
| Baseline branch | `wispral/baseline-sd-m0` at `f83add0f710ce9675b9c8e1e3716f7977312c000` = the pin plus one file, `.github/workflows/wispral-baseline-sd-m0.yml` ([copy](wispral-baseline-sd-m0.yml)). No donor file is changed. |
| Donor workflows | All 9 disabled through the GitHub API before the baseline branch was pushed (`disabled_manually`), including release, signing and updater |
| Run | [`wisprside` run 42536089224](https://github.com/TheHalfMoon/wisprside/actions/runs/42536089224), 2026-11-08 |

**The workflow's steps** are copied from the donor's `test.yml`, `code-quality.yml` and `playwright.yml`. It differs in two ways only:

- it uses `cargo test --locked`, as the packet requires;
- it captures failures and counts instead of stopping on them.

## Linux results (hosted `ubuntu-24.04` / `ubuntu-latest`)

| Suite | Command | Result | Log |
| --- | --- | --- | --- |
| Rust | `cargo test --locked` in `src-tauri` | exit 0. **338 passed, 0 failed, 18 ignored**, 0 measured, 0 filtered out | [`cargo-test.log`](linux-run-42536089224/cargo-test.log), [`rust-summary.txt`](linux-run-42536089224/rust-summary.txt) |
| Lint | `bun run lint` (`eslint src`) | exit 0 | [`lint.log`](linux-run-42536089224/lint.log) |
| Keyboard | `bun run test:keyboard` | exit 0, "all assertions passed" (the script reports no count) | [`keyboard.log`](linux-run-42536089224/keyboard.log) |
| Playwright | `bun run test:playwright` (Chromium) | exit 0. **2 expected, 0 unexpected, 0 flaky, 0 skipped** | [`playwright.log`](linux-run-42536089224/playwright.log), [`playwright-results.json`](linux-run-42536089224/playwright-results.json) |

**Toolchain:** rustc 1.99.1, cargo 1.99.1, Ubuntu 24.04.5 LTS ([`toolchain.txt`](linux-run-42536089224/toolchain.txt)); Bun 1.4.4.

**Not covered by this half:** the Windows suites, binaries and DLLs, which are now in [`windows-hwa/`](windows-hwa/README.md); and installer packaging, which the packet defers to the release-candidate packets.

No failures were fixed.
