# SD-M0 baseline, Windows half (HW-A)

**Grain:** `SD-M0` (Specification 000E). The Linux half is in [`../README.md`](../README.md).

**Result.** Every acceptance item of the packet is recorded on Windows:

- Rust `cargo test --locked`: 332 passed, 0 failed, 18 ignored.
- Lint and the keyboard test pass.
- Playwright passes 2 of 2, but only on the third attempt, after two environment fixes (below).
- The debug and release builds succeed.
- The bundled DLL list is recorded.

No donor file was changed and no failure was fixed. Installer packaging (NSIS/MSI) was **not run**: the packet defers it to the release-candidate packets. Nothing was signed or published.

## Machine and checkout

| Item | Value |
| --- | --- |
| Machine | HW-A: Intel Core i5-13420H, 15.7 GB usable RAM, Windows 11 Home build 26300 (the founder's laptop) |
| Checkout | `TheHalfMoon/wisprside` branch `wispral/baseline-sd-m0` at `f83add0f710ce9675b9c8e1e3716f7977312c000` (donor pin `73cc857…` plus the one Wispral workflow file) |
| Toolchain | rustc and cargo 1.97.1, `stable-x86_64-pc-windows-msvc`; Bun 1.4.4; Node v24.19.0; Visual Studio 2022 Build Tools (MSVC 14.44); CMake 3.31.6-msvc6 (Visual Studio's bundled copy, put first on `PATH` for this run because the machine's default `cmake` is Strawberry Perl's MinGW build); Vulkan SDK 1.4.363.0 ([`toolchain.log`](toolchain.log)) |
| Runner | [`harness/sd_m0_run.ps1`](harness/sd_m0_run.ps1): one step after another, each logged with exit code and duration ([`progress.txt`](progress.txt)), plus a 5 s resource sampler |

The Linux run used rustc 1.99.1. Windows used 1.97.1, which is the version already on this laptop. The donor's `Cargo.lock` was used unchanged (`--locked`).

Local paths, the user name and the host name in the logs are replaced by `REDACTED_HOME`, `REDACTED_USER` and `REDACTED_HOST`.

## Results

| Step | Command | Result | Time | Log |
| --- | --- | --- | ---: | --- |
| Install | `bun install --frozen-lockfile` | exit 0, 348 packages | 75 s | [log](bun-install.log) |
| Lint | `bun run lint` (`eslint src`) | exit 0 | 10 s | [log](lint.log) |
| Keyboard | `bun run test:keyboard` | exit 0, "all assertions passed" (the script reports no count) | <1 s | [log](test-keyboard.log) |
| Playwright, attempt 1 | `bun run test:playwright` with `CI=true` | **exit 1**: the web server command `bunx vite dev` failed, because the winget Bun install has no `bunx` | 3 s | [log](playwright.log) |
| Playwright, attempt 2 | same, with a `bunx.cmd` shim (`bun x %*`) on `PATH` | **exit 1, 0 expected / 2 unexpected**. Chromium could not be installed: the existing `%LOCALAPPDATA%\ms-playwright` folder is not readable by this user, and it was left untouched. | 14 s | [log](playwright-rerun.log), [json](playwright-rerun-results.json) |
| Playwright, attempt 3 | same, plus `PLAYWRIGHT_BROWSERS_PATH` set to a folder in the work directory | exit 0. **2 expected, 0 unexpected, 0 flaky, 0 skipped** | 55 s | [log](playwright-rerun2.log), [json](playwright-rerun2-results.json), [script](harness/sd_m0_playwright.ps1) |
| Frontend build | `bun run build` (`tsc && vite build`), so the release binary embeds the frontend | exit 0 | 46 s | [log](frontend-build.log) |
| Rust tests | `cargo test --locked` in `src-tauri` | exit 0. **332 passed, 0 failed, 18 ignored**, 0 measured, 0 filtered out | 28 min (compile included) | [log](cargo-test.log) |
| Debug build | `cargo build --locked` | exit 0 | 2 min (after the test build) | [log](cargo-build-debug.log) |
| Release build | `cargo build --locked --release` | exit 0 | 37 min | [log](cargo-build-release.log) |

Playwright ran with `CI=true` to match the Linux run, where GitHub sets it. The donor's config then uses 2 retries and 1 worker. Attempts 1 and 2 failed because of this machine's setup, not the donor. They are kept as recorded, and the two fixes only change the environment.

### Why Windows runs 332 Rust tests and Linux 338

Both platforms list their tests by name, 350 on Windows and 356 on Linux (passed plus ignored). The difference is platform-gated tests:

- **11 run only on Linux** ([`tests-only-on-linux.txt`](tests-only-on-linux.txt)): ydotool and dotool clipboard tests, an IBus shortcut test, and two model-file deletion tests.
- **5 run only on Windows** ([`tests-only-on-windows.txt`](tests-only-on-windows.txt)): overlay geometry tests and an overlay-default test.

No test fails on either platform. The same 18 tests, by name, are ignored on both.

### Warnings

- **Rust compiler warnings:**
  - `unused import: Emitter` in `src/secure_input.rs:23`, in the library build (debug, release and test);
  - in the test build only, a second `unused import: Emitter` and `unused import: super::*`.
- **Build-script notices** printed as `warning:` lines, which are informational: "Generated tray translations: 26 languages, 20 fields" and "Staged 13 transcribe-cpp runtime library file(s)".
- **Vite** warns that some chunks are larger than 500 kB after minification.

## Binaries and the bundled DLL list

From [`artifacts.log`](artifacts.log):

| Build | `handy.exe` size | SHA-256 |
| --- | ---: | --- |
| debug | 66,930,176 B | `ED6B64AFFD973BD7C65D8F35B1BFAC3D189B72BB483BB4F5F445EA8ABA7C95BF` |
| release | 31,245,824 B | `A1C5C0DE4E2E077BCB3EB6F1C6E01858ED547F29278B8D872724C2DA04340BE7` |

These hashes identify local research builds only. They are not reproducible-build claims and nothing was distributed.

**DLLs the build places next to `handy.exe`** (release; debug has the same set):

- `transcribe.dll`
- `ggml.dll`, `ggml-base.dll`
- `ggml-vulkan.dll` (45 MB)
- the CPU variants `ggml-cpu-{x64, sse42, sandybridge, haswell, alderlake, skylakex, cannonlake, cascadelake, icelake}.dll`
- `handy_app_lib.dll`

**Load-time imports of the release `handy.exe`** (`dumpbin /dependents`):

- Windows system DLLs:
  - `kernel32`, `user32`, `gdi32`, `advapi32`, `ole32`, `oleaut32`, `combase`;
  - `shell32`, `shlwapi`, `comctl32`, `dwmapi`, `imm32`, `mmdevapi`, `wtsapi32`;
  - `crypt32`, `bcrypt`, `bcryptprimitives`, `secur32`, `ws2_32`, `ntdll`;
  - the `api-ms-win-core-*` API sets.
- **`transcribe.dll`**, the only non-system DLL it imports directly.
- **The Visual C++ runtime:** `VCRUNTIME140.dll` and `VCRUNTIME140_1.dll`, plus the Universal CRT `api-ms-win-crt-*` set.

**Limits of this list:**

- Only `handy.exe` was inspected. The imports of `transcribe.dll` and the `ggml-*` DLLs were not dumped, so their dependency chain, which is expected to include the Vulkan loader, is not recorded.
- DLLs loaded at run time (for example WebView2 or a GPU driver) are not visible to `dumpbin /dependents`.
- **The app was not launched.** The packet does not ask for a launch, and none was done.
- **The Visual C++ runtime is a dependency the installer must ship or require.** That is a question for the release-candidate packets.

## Resource use

The sampler ([`resources.tsv`](resources.tsv)) logged, every 5 s:

- the time;
- free physical memory (GB);
- the summed working set (GB) of build and test processes (`cargo`, `rustc`, `cl`, `link`, `cmake`, `msbuild`, `node`, `bun`, `chrome` and others);
- the number of those processes.

Peak summed working set: **4.96 GB**. Lowest free memory: **0.01 GB**. Memory was effectively exhausted at the peak, so the laptop was under memory pressure during the native build. Other user applications were running at the same time and are not separated out.

Disk: the Cargo `target` directory reached **16.99 GB** (debug plus release). After the evidence above was captured, the debug output (8.8 GB) was deleted to free space; it can be rebuilt from the same commands.

## Supply chain notes (packet security risk)

- The native build compiled `transcribe-cpp-sys` with CMake and the Vulkan SDK's shader tools.
- Dependencies came from crates.io and the git sources pinned in `Cargo.lock`, under `--locked`.
- The Vulkan SDK, Build Tools and Rust toolchain were already on the laptop. The only download beyond Cargo crates and Bun packages was Playwright's test browser for attempt 3: Chrome for Testing 156.0.8078.4 (Playwright chromium v1248) from `cdn.playwright.dev`, saved in the work directory (see [`playwright-rerun2.log`](playwright-rerun2.log)). The Linux run downloads the same kind of browser through `playwright install`.

## What this does not cover

- Installer packaging (NSIS/MSI), signing and the updater: deferred by the packet.
- A launch or smoke run of the built app.
- The dependency chain of the bundled DLLs, beyond `handy.exe`'s direct imports.
