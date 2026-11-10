# ST-D00 baseline, Windows half (HW-A)

**Grain:** `ST-D00` (Specification 000E). The Linux half is in [`../README.md`](../README.md).

**Result: recorded, NOT VERIFIED.**

- The packet's network condition fails on both platforms. That condition is: no model or runtime download, `HF_HUB_OFFLINE=1`, and zero model-hub connections. On Windows the test suite also reaches GitHub.
- The Windows suites do not pass. The failures are recorded as found; none was fixed or hidden. The 21 hanging tests were deselected so the run could finish, and they are counted as failures of the baseline.

No remediation was attempted. Everything here is the **original baseline**. Any remediation will be recorded separately, as a delta against this.

## Machine and checkout

| Item | Value |
| --- | --- |
| Machine | HW-A: Intel Core i5-13420H, 16 GB RAM, Windows 11 Home build 26300 (the founder's laptop, approved with "Yes, use my laptop") |
| Checkout | `TheHalfMoon/wisprstudio` branch `wispral/baseline-st-d00` at `b8e67b5fd164368b0535a00890270d4cfca3759e` (donor pin `200286cc…` plus the one Wispral workflow file) |
| Tools | uv 0.13.7, Bun 1.4.4, Node v24.19.0, Python 3.11.15 ([`earlier/environment.txt`](earlier/environment.txt)) |
| Python env | `bash scripts/uv-sync-retry.sh --all-extras --python 3.11 --no-group cuda --group cpu` (the donor's own sync script, CPU group) |
| Machine settings, not changed | `where bash` lists `C:\Windows\System32\bash.exe` (WSL) first; `LongPathsEnabled` is 0 ([`earlier/machine-facts.txt`](earlier/machine-facts.txt)) |

**Redaction.** Local paths, the user name and the host name are replaced by `REDACTED_HOME`, `REDACTED_USER` and `REDACTED_HOST`. pytest's own shortened paths (`C:\Users\S...`) are rewritten to `C:\Users\REDACTED...`. The test names `hf_AAAA…`, `ghp_…` and `github_pat_CCCC…` in `junit-4.xml` are the donor's synthetic test parameters, not secrets.

## Results

| Suite | Result on Windows | Linux (rerun 42538071852) |
| --- | --- | --- |
| `pytest backend/tests/` (`HF_HUB_OFFLINE=1`) | exit 0. **590 passed, 10 skipped** ([log](earlier/pytest-backend.log)) | 600 passed |
| `pytest tests/` (`HF_HUB_OFFLINE=1`), run 4 | Sum of the ten console summaries: **12,989 passed, 82 failed, 24 errors, 175 skipped, 8 xfailed, 1 xpassed**. Plus **21 tests deselected because they hang**, and the module `test_ci_change_detection`, which never ran (see below). | 13,307 passed, 0 failed, 51 skipped, 8 xfailed, 1 xpassed |
| Frontend (`node --test electron/tests/node-version.test.mjs`: 6/6; `bun run test:frontend`: 124 passed, 1 skipped) | exit 0 ([log](earlier/frontend.log)) | exit 0 |
| `bun run test` (Electron unit) | exit 1. **4 failed, 2,896 passed, 12 skipped** (2,912). 3 of the 4 are 5,000 ms timeouts. ([log](earlier/bun-test.log)) | exit 0 |
| `bun run check:electron` | exit 1 at its test step. **19 failed, 2,881 passed, 12 skipped**. 17 of the 19 are 5,000 ms timeouts. **The later steps (build, web build, packaging contract) did not run**, so they are NOT RUN on Windows, not passed. ([log](earlier/check-electron.log)) | exit 0 |

**JUnit counts differ from the console counts.** The JUnit files have 13,276 test cases: 12,990 with no outcome element, 82 with `<failure>`, 21 with `<error>` and 183 with `<skipped>`.

- JUnit files xfailed under skipped and xpassed under passed.
- The console counts the one collection error once per worker.

`run4/analysis.txt` uses the JUnit counts.

The two Electron runs used the same tests and gave different failure sets: 4 failures in one, 19 in the other. Most are timeouts. This suggests timing sensitivity on this laptop; no rerun was done to confirm it.

### How `pytest tests/` was run

A plain run could not complete on this machine. Every attempt is kept:

| Attempt | What happened | Log |
| --- | --- | --- |
| `-n auto` | Aborted at 46 % | [`earlier/pytest-tests-nauto-aborted.log`](earlier/pytest-tests-nauto-aborted.log) |
| `-n 4` | Stalled on hanging tests; stopped by the agent after about 18.6 h (the span of its watcher log, 2026-11-09 06:04 to 2026-11-10 00:39 +03:00) | [`earlier/pytest-tests-n4.log`](earlier/pytest-tests-n4.log) |
| `-n 4` with the probe and hang guard | Killed by the agent tool's 1 h limit; the last progress marker is 87 % (the file name says 88) | [`earlier/pytest-tests-probe-killed-at-88pct.log`](earlier/pytest-tests-probe-killed-at-88pct.log) |
| run 3 | Stopped when the laptop was powered off at 2026-11-10 03:28:20 +03:00 (System event 1074, in [`earlier/machine-facts.txt`](earlier/machine-facts.txt)) | not kept separately; its hang dumps are in `run4/hang-dumps/run3/` |
| **run 4** | **Ran to the end**, 2026-11-10 01:46:25Z to 03:02:40Z, minus the exclusions below | [`run4/`](run4/) |

Run 4 settings:

- **Chunks.** Ten file chunks ([`run4/chunks.json`](run4/chunks.json), 813 test files). Each was run as `pytest <files> -q --tb=short -n 4 -rfE -p wispral_probe -p no:cacheprovider --max-worker-restart=50 --basetemp=<dir> --junitxml=junit-<i>.xml` ([runner](harness/st_d00_run4.ps1)).
- **The 21 hanging tests** were deselected ([`run4/hung-tests.txt`](run4/hung-tests.txt)). Each is listed with the hang-guard stack dump from an earlier attempt, which shows it waiting on a subprocess past the 600 s limit. They are in:
  - `test_android_play_workflow` (4)
  - `test_ci_change_detection` (2)
  - `test_ci_runtime_scope` (1)
  - `test_docker_cudnn8_compat` (4)
  - `test_electron_transition` (4)
  - `test_ios_archive_signing` (3)
  - `test_release_signing_notes` (3)

  **Why they hang is inferred, not shown.** These tests start workflow shell snippets with a bare `bash`. Windows process creation searches `System32` before `PATH`, and `C:\Windows\System32\bash.exe` is the WSL launcher. The dumps show only the wait, not which `bash` ran.
- **`test_ci_change_detection` did not run at all.** Its collection failed with `FileNotFoundError: [WinError 2]` in chunk 1. That is one error, reported once by each of the four workers. So none of its tests have a result, and how many it holds was not counted.
- **The probe.** `wispral_probe` ([source](harness/wispral_probe.py)) only observes.
  - It records **attempts**: every non-loopback name lookup and connection call, before the call is made, with the running test's ID.
  - It also runs the hang guard: a test running longer than 600 s gets a stack dump, and its worker is ended.

### Classification of the 82 failures and 21 errors

These 103 test cases carry 106 failure or error records, because the one collection error in `test_ci_change_detection` carries four `<error>` elements, one per worker. The classification is by test module, using [`harness/st_d00_classify.py`](harness/st_d00_classify.py). The full list is in [`run4/classification.tsv`](run4/classification.tsv).

| Class | Records | Cause | Modules (records) |
| --- | ---: | --- | --- |
| W-PATH | 36 | Windows path and file-name rules | `test_virustotal` (21, a `"` in a file name), `test_ffmpeg_utils` (5), `test_media_tool_missing` (2), `test_omnivoice_gguf` (2, path containment), `test_indextts_sidecar` (2), `test_cla_audit` (1), `test_confucius4_sidecar` (1, `\` vs `/`), `test_profile_delete_regression` (1), `test_db_backup_concurrent_slots` (1) |
| W-POSIX | 26 | A POSIX shell or tool is assumed: a bare `bash`, `PATH` built with `:`, no `openssl`, bash syntax | `test_electron_transition` (9), `test_ios_archive_signing` (6, `openssl` setup), `test_ci_change_detection` (4, one collection error), `test_gguf_portable_x86_runtime` (3), `test_gguf_desktop_bundle` (2), `test_release_signing_notes` (2) |
| W-ENC | 21 | Files opened without `encoding=`, so Windows uses cp1252 | `test_colab_proxy_trust_2705` (12 errors, 2 failures), `test_voicestudio_branding` (2), `test_failure_classify` (1), `test_mobile_contract` (1), `test_mobile_contributors` (1), `test_update_contributors` (1), `test_indextts_sidecar` (1) |
| OTHER | 9 | Not yet root-caused | `test_indextts_speed_3588` (3, `IndexTTS2Backend` has no `_lock`), `test_generation_audio_guard` (2), `test_bundled_code_policy` (2), `test_mobile_mp3_source` (1), `test_xdist_data_dir_isolation` (1) |
| IMPORT | 6 | Circular import of beartype `claw_state` under xdist | `test_windows_rocm_sdk_integrity` (4), `test_text_normalization_routes` (2) |
| TIMING | 4 | Timeouts | `tests/probe/test_probe_dictation` (1), `tests/probe/test_probe_engines` (1), `test_compile_thread_affinity` (1), `test_startup_progress_early_bind` (1) |
| W-NODE | 4 | Node scripts started from Python fail | `test_setup_rocm_variant` (3), `test_setup_windows_rocm` (1) |

None of these fails on Linux. The classes are this analysis's reading of the error messages, not a donor triage. OTHER is unexplained. One lead for `test_generation_audio_guard` ("missing ffmpeg unexpectedly launched") is that this laptop has FFmpeg on `PATH`; it is not checked.

## Network egress on Windows

The packet's condition is: no model or runtime download, `HF_HUB_OFFLINE=1`, and an egress log with zero model-hub connections. **It fails.**

Three observers were used:

- **The probe.** Python socket calls, attributed to the running test.
- **A TCP watcher** ([`harness/egress_watch.ps1`](harness/egress_watch.ps1)). It is non-admin and records each new connection, with its state and owning process, by polling once a second. It is weaker than a packet capture: a connection that opens and closes between polls is missed.
- **The `hf_xet` log files** the suite wrote.

Findings, original baseline:

1. **A test clones from GitHub during the run.** This is certain, and specific to Windows.
   - `test_gguf_desktop_bundle` and `test_gguf_portable_x86_runtime` put a fake `git` first on a `PATH` that they build with `:` separators (`f"{fake}:/usr/bin:/bin"`). They run the build script with Git for Windows' `C:/Program Files/Git/bin/bash.exe`. The drive letter's colon breaks the `PATH` entry, so the real `git` runs.
   - The test output shows `omnivoice.cpp` cloned and `Submodule path 'ggml': checked out '210138933b22…'`, with the submodule cloned from `https://github.com/ServeurpersoCom/ggml.git`. See [`run4/junit-7.xml`](run4/junit-7.xml), [`run4/junit-8.xml`](run4/junit-8.xml), [`run4/pytest-7.log`](run4/pytest-7.log) and [`run4/pytest-8.log`](run4/pytest-8.log).
   - The Python probe cannot see this, because `git` is a separate native process.
2. **Python attempted a runtime download from GitHub** in the probed attempt stopped at 87 %.
   - The probe recorded `test_setup_preflight.py::test_preflight_returns_expected_shape` looking up and connecting to `github.com`. It then looked up and connected to `media.githubusercontent.com`, all from `backend/services/media_tools.py:_download` ([`earlier/probe-run2-egress.jsonl`](earlier/probe-run2-egress.jsonl)).
   - These are attempts. The second host suggests a redirect was answered, but **no record shows that a download completed**.
   - It did not recur in run 4, where the same test passed with no egress record. Why is not established. One hypothesis is a result cached outside the test's temporary directory, as in finding 6; it is not checked.
3. **A Python process attempted a connection to a Hugging Face address.**
   - In the unprobed `-n auto` attempt, the watcher recorded `SynSent 13.36.122.243:443 pid=14936 proc=python` at 2026-11-09 05:00:34 +03:00 ([`watcher/egress-tcp-attempt2-suites.txt`](watcher/egress-tcp-attempt2-suites.txt)). Only `SynSent` was seen, not `Established`, so this shows an attempt, not a completed connection.
   - About 2 h later, and again after run 4, `us.aws.cdn.hf.co` answered with 13.36.122.243 among its addresses. The address reverse-resolves to `ec2-13-36-122-243.eu-west-3.compute.amazonaws.com` ([`watcher/address-lookups.txt`](watcher/address-lookups.txt)).
   - The same PID 14936 had started the native `hf_xet` client at 04:56:50 +03:00 ([`watcher/hf-xet-logs/xet_20261109T045650860+0300_14936.log`](watcher/hf-xet-logs/xet_20261109T045650860+0300_14936.log)).
   - **Which test made the attempt is not identified.** That attempt had no probe, and the watcher does not record tests.
4. **An unattributed connection.** In the unprobed `-n 4` attempt, a Python process (PID 17916) had `Established 57.150.192.193:443` at 2026-11-09 06:54:27 +03:00 ([`watcher/egress-tcp-tests-n4.txt`](watcher/egress-tcp-tests-n4.txt)). The address has no reverse DNS record ([`watcher/address-lookups.txt`](watcher/address-lookups.txt)). **Who owns it, and which test made the connection, are not identified.**
5. **Run 4 (probed, ran to the end): the probe saw no model-hub attempt.**
   - The probe saw only these:
     - lookups of test host names (`youtu.be`, `youtube.com`, `example.com`, `x`, `gpu.example`) through the donor's URL-safety checks;
     - local route detection (`192.0.2.1:9` UDP);
     - the offline probe (`10.255.255.1`).
   - The watcher log for run 4 has no non-loopback TCP entry owned by a named `python` process ([`watcher/egress-tcp-run4.txt`](watcher/egress-tcp-run4.txt)).
   - It does have 384 entries whose process exited before it could be named. 305 of them go to GitHub (`20.233.83.145`/`.146`), and most of the rest go to Microsoft addresses (`2620:1ec:…`, `2603:10xx:…`). They overlap in time with the agent's own `gh` and `git` use, so **they cannot be attributed to tests or excluded**.
   - The `52.85.110.x` addresses are CloudFront. `cas-bridge.xethub.hf.co` answered with addresses in the same `/24` ([`watcher/address-lookups.txt`](watcher/address-lookups.txt)). Ownership:
     - `.91` and `.60` were opened by the laptop vendor's background processes `HwMdcCenter` and `BasicService`.
     - `.78` first appears at 05:41:51 +03:00 as `TimeWait pid=0`, with no owner, during chunk 6. `MBAMessageCenter` opened it again at 05:42:50. **The owner of the first `.78` connection is not established.**

   This **does not show the suite is clean**. A connection shorter than one second can be missed, and finding 1 (native `git`) happened in run 4.
6. **Test isolation.** The suite starts `hf_xet` in the real per-user cache, `%LOCALAPPDATA%\OmniVoice\hf_cache\xet\logs`, not in a temporary directory.
   - That folder held 103 log files written from 2026-11-09 04:18 to 2026-11-10 06:00 +03:00. All are committed in [`watcher/hf-xet-logs/`](watcher/hf-xet-logs/).
   - All 496 lines are start-up and log-cleanup messages ([`watcher/hf-xet-logs-summary.txt`](watcher/hf-xet-logs-summary.txt)). None records a transfer at the logged level (INFO). That says nothing about connections made without logging.
   - The first file, at 04:18, predates the suites. It is probably the agent's environment check; this is not attributed.

Together with the Linux half, the network condition fails, and **the Grain must not be reported as verified**. On Linux, `huggingface.co` and `us.aws.cdn.hf.co` were looked up and contacted in both runs. On Windows, findings 1 and 2 alone already break "no model or runtime download".

## Files

| Path | Content |
| --- | --- |
| `run4/junit-0.xml` … `junit-9.xml`, `pytest-*.log` | Per-chunk JUnit and console output |
| `run4/progress.txt` | Chunk start and end times |
| `run4/analysis.txt` | Output of [`harness/st_d00_analyze.py`](harness/st_d00_analyze.py), run on the local raw layout (`probe/egress-*.jsonl`, `probe/timeline-*.tsv`). Here those are merged into `run4/probe-egress.jsonl` and packed into `run4/probe-timelines.tar.gz`; unpack the tarball into `probe/` to rerun it. |
| `run4/failures.txt`, `run4/classification.tsv` | Every failure and error record, and its class |
| `run4/hung-tests.txt`, `run4/hang-dumps/` | The 21 deselected tests and their stack dumps |
| `run4/probe-egress.jsonl`, `run4/probe-timelines.tar.gz` | Probe records, and per-worker test start and end timelines |
| `earlier/` | Backend, frontend and Electron logs; environment and machine facts; the incomplete `tests/` attempts; run 2 probe records |
| `watcher/` | TCP watcher logs for each phase, address lookups, the `hf_xet` log files and their summary |
| `harness/` | The probe, the watcher, the runner, and the analysis and classification scripts. They are Wispral research tooling and do not modify the donor. |
