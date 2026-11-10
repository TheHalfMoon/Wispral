# SD-M0 baseline, Windows half (HW-A)

**Grain:** `SD-M0` (Specification 000E). The Linux half is in [`../README.md`](../README.md).

**Result.** Every acceptance item of the packet is recorded on Windows:

- Rust `cargo test --locked`: 332 passed, 0 failed, 18 ignored.
- Lint and the keyboard test pass.
- Playwright passes 2 of 2, but only on the fifth run, after two environment fixes. Of the four failed runs, two logs survive, one was overwritten and one was deleted; all are disclosed below.
- The debug and release builds succeed.
- The DLLs the donor's Windows bundle config would ship are recorded from this build ([`bundle-dlls.txt`](bundle-dlls.txt)). The installer itself was not built, so what an installer would actually contain is NOT RUN.

No donor file was changed and no failure was fixed. Installer packaging (NSIS/MSI) was **not run**: the packet defers it to the release-candidate packets. Nothing was signed or published.

## Machine and checkout

| Item | Value |
| --- | --- |
| Machine | HW-A: Intel Core i5-13420H, 15.7 GB usable RAM, Windows 11 Home build 26300 (the founder's laptop) |
| Checkout | `TheHalfMoon/wisprside` branch `wispral/baseline-sd-m0` at `f83add0f710ce9675b9c8e1e3716f7977312c000` (donor pin `73cc857…` plus the one Wispral workflow file) |
| Toolchain | rustc and cargo 1.97.1, `stable-x86_64-pc-windows-msvc`; Bun 1.4.4; Node v24.19.0; Visual Studio 2022 Build Tools (MSVC 14.44); CMake 3.31.6-msvc6 (Visual Studio's bundled copy, put first on `PATH` for this run because the machine's default `cmake` is Strawberry Perl's MinGW build); Vulkan SDK 1.4.363.0 ([`toolchain.log`](toolchain.log)) |
| Runner | [`harness/sd_m0_run.ps1`](harness/sd_m0_run.ps1): one step after another, each logged with exit code and duration ([`progress.txt`](progress.txt)), plus a 5 s resource sampler |

The Linux run used rustc 1.99.1. Windows used 1.97.1, which is the version already on this laptop. The donor's `Cargo.lock` was used unchanged (`--locked`).

Local paths in the logs are replaced by `REDACTED_HOME`. The redaction step also replaces the user and host names, but neither occurs in these logs outside those paths.

## Results

| Step | Command | Result | Time | Log |
| --- | --- | --- | ---: | --- |
| Install | `bun install --frozen-lockfile` | exit 0, 348 packages | 75 s | [log](bun-install.log) |
| Lint | `bun run lint` (`eslint src`) | exit 0 | 10 s | [log](lint.log) |
| Keyboard | `bun run test:keyboard` | exit 0, "all assertions passed" (the script reports no count) | <1 s | [log](test-keyboard.log) |
| Playwright, run 1 | `bun run test:playwright` with `CI=true` | **exit 1**: the web server command `bunx vite dev` failed, because the winget Bun install has no `bunx` | 3 s | [log](playwright.log) |
| Playwright, runs 2 and 3 | same, with a `bunx.cmd` shim ([`harness/bunx.cmd`](harness/bunx.cmd), `bun x %*`) on `PATH`. Run 2 was typed directly in the agent's PowerShell tool. Run 3 was the same commands from a detached script, which overwrote run 2's log. | **exit 1, 0 expected / 2 unexpected** (run 3). The browser install failed with `Error: ENOENT: no such file or directory, mkdir '…\AppData\Local\ms-playwright'`. That path is a dangling junction, made 2026-10-12, whose target no longer exists ([`playwright-folder-state.txt`](playwright-folder-state.txt)). It was left untouched. | 14 s | [log](playwright-rerun.log), [json](playwright-rerun-results.json) |
| Playwright, run 4 | the run 3 script, launched again by mistake **before** the browser-path fix was added | **outcome not recorded**: it finished before the agent could stop it, and the agent deleted its log before run 5. Its `PLAYWRIGHT_RERUN2_DONE` marker is the first of the two in [`progress.txt`](progress.txt). The same environment as run 3 means the same failure would be expected, but that is not shown. | — | deleted |
| Playwright, run 5 | same, plus `PLAYWRIGHT_BROWSERS_PATH` set to a folder in the work directory | exit 0. **2 expected, 0 unexpected, 0 flaky, 0 skipped**; the tests took 21.9 s, the rest was the browser download | 55 s | [log](playwright-rerun2.log), [json](playwright-rerun2-results.json), [script](harness/sd_m0_playwright.ps1) |
| Frontend build | `bun run build` (`tsc && vite build`), so the release binary embeds the frontend | exit 0 | 46 s | [log](frontend-build.log) |
| Rust tests | `cargo test --locked` in `src-tauri` | exit 0. **332 passed, 0 failed, 18 ignored**, 0 measured, 0 filtered out | 28 min (compile included) | [log](cargo-test.log) |
| Debug build | `cargo build --locked` | exit 0 | 2 min (after the test build) | [log](cargo-build-debug.log) |
| Release build | `cargo build --locked --release` | exit 0 | 37 min | [log](cargo-build-release.log) |

Playwright ran with `CI=true` to match the Linux run, where GitHub sets it. The donor's config then uses 2 retries and 1 worker. Runs 1 to 4 failed, or would be expected to, because of this machine's setup, not the donor. The two fixes only change the environment.

### Why Windows runs 332 Rust tests and Linux 338

Both platforms list their tests by name, 350 on Windows and 356 on Linux (passed plus ignored). The difference is platform-gated tests:

- **11 run only on Linux** ([`tests-only-on-linux.txt`](tests-only-on-linux.txt)): Linux clipboard tests (ydotool, dotool and an external-script stdio test), an IBus shortcut test, and two model-file deletion tests.
- **5 run only on Windows** ([`tests-only-on-windows.txt`](tests-only-on-windows.txt)): overlay geometry tests and an overlay-default test.

No test fails on either platform. The same 18 tests, by name, are ignored on both.

### Warnings

- **Rust compiler warnings:**
  - `unused import: Emitter` in `src/secure_input.rs:23`, in the library build (debug, release and test);
  - in the test build only, a second `unused import: Emitter` and `unused import: super::*`.
- **Build-script notices** printed as `warning:` lines, which are informational: "Generated tray translations: 26 languages, 20 fields" and "Staged 13 transcribe-cpp runtime library file(s)".
- **Vite** warns that some chunks are larger than 500 kB after minification.

## Binaries and DLLs

From [`artifacts.log`](artifacts.log):

| Build | `handy.exe` size | SHA-256 |
| --- | ---: | --- |
| debug | 66,930,176 B | `ED6B64AFFD973BD7C65D8F35B1BFAC3D189B72BB483BB4F5F445EA8ABA7C95BF` |
| release | 31,245,824 B | `A1C5C0DE4E2E077BCB3EB6F1C6E01858ED547F29278B8D872724C2DA04340BE7` |

These hashes identify local research builds only. They are not reproducible-build claims and nothing was distributed.

**DLLs present next to `handy.exe` in `target/`** (release; debug has the same set): `transcribe.dll`, `ggml.dll`, `ggml-base.dll`, `ggml-vulkan.dll` (45 MB), the CPU variants `ggml-cpu-{x64, sse42, sandybridge, haswell, alderlake, skylakex, cannonlake, cascadelake, icelake}.dll`, and `handy_app_lib.dll`. The last is a build output of the library crate and is not shown to ship.

**DLLs the donor's Windows bundle config would ship** ([`bundle-dlls.txt`](bundle-dlls.txt)):

- `tauri.windows.conf.json` maps `src-tauri/transcribe-libs/` to the install root. After this build that folder holds 13 DLLs: `transcribe.dll` and the 12 `ggml*` DLLs above.
- `build.rs` also stages the VC++ runtime (`msvcp140`, `vcruntime140`, `vcomp140`) into that folder, but only when `HANDY_VC_REDIST_DIRS` is set. The donor's comment says CI sets it. It was not set here, so **this build staged no VC++ runtime DLL**, and a donor CI build would ship more than is listed here.
- The installer was not built, so the final contents of an installer are NOT RUN.

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
- **`handy.exe` imports the Visual C++ runtime.** Only the donor's CI path stages it for the installer (see above). The release-candidate packets must decide how Wispral ships it.

## Resource use

The sampler ([`resources.tsv`](resources.tsv)) logged, every 5 s:

- the time;
- free physical memory (GB);
- the summed working set (GB) of build and test processes (`cargo`, `rustc`, `cl`, `link`, `cmake`, `msbuild`, `node`, `bun`, `chrome` and others), from 06:25 to the end of the runner at 07:34. Playwright runs 2 to 5 came after that and were not sampled;
- the number of those processes.

Peak summed working set: **4.96 GB**, at 06:34:08, during the `cargo test` compile. Lowest free memory: **0.01 GB**, at 06:34:01. Free memory was already 1.08 GB at the start. The laptop was under memory pressure during the native compile. Other user applications were running at the same time and are not separated out.

Disk: the Cargo `target` directory reached **16.99 GB** (debug plus release). After the evidence above was captured, the agent deleted the debug output (`du` reported 8.8 GB) to free space. That step is not in a committed log. The output can be rebuilt with the same commands.

## Supply chain notes (packet security risk)

- The native build compiled `transcribe-cpp-sys` with CMake and the Vulkan SDK's shader tools.
- **Crates.** Dependencies came from crates.io and from the four git sources pinned in `Cargo.lock`, under `--locked`:
  - `cjpais/tao` (`c3bee28c…`);
  - `cjpais/hf-hub`, branch `cancellable-downloads` (`9918f11a…`);
  - `rustdesk-org/rdev` (`a90dbe11…`);
  - `ahkohd/tauri-nspanel`, branch `v2.1` (`da9c9a8d…`). This one is fetched but only used on macOS.
- **Tools already installed.** The Vulkan SDK, Build Tools and Rust toolchain were already on the laptop. No LLVM or libclang is needed: the lock file has no `bindgen`.
- **Playwright downloads.** Beyond Cargo crates and Bun packages, run 5 downloaded four items from `cdn.playwright.dev` into the work directory ([`playwright-rerun2.log`](playwright-rerun2.log)):
  - Chrome for Testing 156.0.8078.4 (chromium v1248);
  - FFmpeg (v1013);
  - Chrome Headless Shell 156.0.8078.4 (v1248), which is what the tests run;
  - Winldd (v1007).

  The Linux run gets its browser the same way, through `playwright install`.

## What this does not cover

- Installer packaging (NSIS/MSI), signing and the updater: deferred by the packet.
- A launch or smoke run of the built app.
- The dependency chain of the bundled DLLs, beyond `handy.exe`'s direct imports.
- What an installer would contain. The VC++ runtime staging depends on `HANDY_VC_REDIST_DIRS`, which was not set.
