# ST-D00 baseline, Windows half (HW-A)

**Grain:** `ST-D00` (Specification 000E). The Linux half is in [`../README.md`](../README.md).

**Result: recorded, NOT VERIFIED.**

- The packet's network condition fails on both platforms: zero model-hub connections under `HF_HUB_OFFLINE=1`. On Windows the test suite also reaches GitHub.
- The Windows suites do not pass. The failures are recorded as found; none was fixed, skipped or hidden.

No remediation was attempted. Everything here is the **original baseline**. Any remediation will be recorded separately, as a delta against this.

## Machine and checkout

| Item | Value |
| --- | --- |
| Machine | HW-A: Intel Core i5-13420H, 16 GB RAM, Windows 11 Home build 26300 (founder's laptop, "Yes, use my laptop") |
| Checkout | `TheHalfMoon/wisprstudio` branch `wispral/baseline-st-d00` at `b8e67b5fd164368b0535a00890270d4cfca3759e` (donor pin `200286cc…` plus the one Wispral workflow file) |
| Tools | uv 0.13.7, Bun 1.4.4, Node v24.19.0, Python 3.11.15 ([`earlier/environment.txt`](earlier/environment.txt)) |
| Python env | `bash scripts/uv-sync-retry.sh --all-extras --python 3.11 --no-group cuda --group cpu` (the donor's own sync script; CPU group) |
| Machine quirks, not changed | `bash` on `PATH` resolves to `C:\Windows\system32\bash.exe` (WSL). `LongPathsEnabled` is 0. |

Local paths in the logs are redacted to `<HOME>` and `<USER>`. The test names `hf_AAAA…` and `github_pat_CCCC…` in `junit-4.xml` are the donor's own synthetic test parameters, not secrets.

## Results

| Suite | Result on Windows | Linux (rerun 42538071852) |
| --- | --- | --- |
| `pytest backend/tests/` (`HF_HUB_OFFLINE=1`) | exit 0. **590 passed, 10 skipped** ([log](earlier/pytest-backend.log)) | 600 passed |
| `pytest tests/` (`HF_HUB_OFFLINE=1`), run 4 | **12,990 passed, 82 failed, 21 errors, 183 skipped** (13,276 test cases in JUnit), plus **21 tests deselected because they hang** | 13,307 passed, 0 failed, 51 skipped, 8 xfailed, 1 xpassed |
| Frontend (`node --test` 6/6; `bun run test:frontend` 124 passed, 1 skipped) | exit 0 ([log](earlier/frontend.log)) | exit 0 |
| `bun run test` (Electron unit) | exit 1. **4 failed, 2,896 passed, 12 skipped** (2,912). 3 of the 4 are 5,000 ms timeouts. ([log](earlier/bun-test.log)) | exit 0 |
| `bun run check:electron` | exit 1 at its test step. **19 failed, 2,881 passed, 12 skipped**. 17 of the 19 are 5,000 ms timeouts. **The later steps (build, web build, packaging contract) did not run**, so they are NOT RUN on Windows, not passed. ([log](earlier/check-electron.log)) | exit 0 |

The two Electron runs used the same tests and gave different failure sets: 4 failures in one, 19 in the other. Most are timeouts. This points to timing sensitivity on this laptop, but no rerun was done to confirm it.

### How `pytest tests/` was run

A plain run could not complete on this machine. Every attempt is kept:

| Attempt | What happened | Log |
| --- | --- | --- |
| `-n auto` (12 workers) | Aborted at 46 % | [`earlier/pytest-tests-nauto-aborted.log`](earlier/pytest-tests-nauto-aborted.log) |
| `-n 4` | Hung for about 21 h on tests that call `bash`; stopped | [`earlier/pytest-tests-n4.log`](earlier/pytest-tests-n4.log) |
| `-n 4` with the probe and hang guard | Killed by the agent tool's 1 h limit at 88 % | [`earlier/pytest-tests-probe-killed-at-88pct.log`](earlier/pytest-tests-probe-killed-at-88pct.log) |
| run 3 | Stopped by a laptop restart (Windows event 1074) | not kept separately; its hang dumps are in `run4/hang-dumps/run3/` |
| **run 4** | **Complete**: 2026-11-10 01:46:25Z to 03:02:40Z | [`run4/`](run4/) |

The run 4 settings were:

- Ten file chunks ([`run4/chunks.json`](run4/chunks.json), 813 test files), each run as `pytest <files> -q --tb=short -n 4 -rfE -p wispral_probe -p no:cacheprovider --max-worker-restart=50 --basetemp=<dir> --junitxml=junit-<i>.xml` ([runner](harness/st_d00_run4.ps1)).
- The **21 hanging tests** were deselected ([`run4/hung-tests.txt`](run4/hung-tests.txt)). Each one is listed with the hang-guard stack dump that shows it stuck. All 21 run workflow shell snippets through `bash`, which on this machine is WSL. They are in:
  - `test_android_play_workflow` (4)
  - `test_ci_change_detection` (2)
  - `test_ci_runtime_scope` (1)
  - `test_docker_cudnn8_compat` (4)
  - `test_electron_transition` (4)
  - `test_ios_archive_signing` (3)
  - `test_release_signing_notes` (3)

  These are failures of the baseline. Deselecting them is not a pass.
- `wispral_probe` ([source](harness/wispral_probe.py)) only observes. It records non-loopback socket lookups and connections with the running test's ID. It also runs the hang guard: a test running longer than 600 s gets a stack dump and its worker is ended.

### Classification of the 82 failures and 21 errors

These 103 test cases produce 106 records: the one collection error in `test_ci_change_detection` appears in four chunks. The classification is by test module, using [`harness/st_d00_classify.py`](harness/st_d00_classify.py). The full list is in [`run4/classification.tsv`](run4/classification.tsv).

| Class | Records | Cause | Modules |
| --- | ---: | --- | --- |
| W-PATH | 36 | Windows path and filename rules | `test_virustotal` (21: a `"` in a file name); `test_ffmpeg_utils` (5); `test_cla_audit`; `test_confucius4_sidecar` (`\` vs `/`); `test_media_tool_missing`; `test_profile_delete_regression`; `test_omnivoice_gguf` (path containment); `test_db_backup_concurrent_slots`; `test_indextts_sidecar` (2) |
| W-POSIX | 26 | A POSIX shell or tool is assumed: `bash` is WSL here; `PATH` is built with `:`; no `openssl`; bash syntax | `test_electron_transition` (9), `test_ios_archive_signing` (6, `openssl` setup), `test_ci_change_detection` (4 records of one collection error), `test_gguf_portable_x86_runtime` (3), `test_gguf_desktop_bundle` (2), `test_release_signing_notes` (2) |
| W-ENC | 21 | Files opened without `encoding=`, so Windows uses cp1252 | `test_colab_proxy_trust_2705` (12 errors, 2 failures), `test_voicestudio_branding` (2), `test_failure_classify`, `test_mobile_contract`, `test_mobile_contributors`, `test_update_contributors`, `test_indextts_sidecar` (1) |
| OTHER | 9 | Not yet root-caused | `test_indextts_speed_3588` (3, `IndexTTS2Backend` has no `_lock`), `test_generation_audio_guard` (2), `test_bundled_code_policy` (2), `test_mobile_mp3_source`, `test_xdist_data_dir_isolation` |
| IMPORT | 6 | Circular import of beartype `claw_state` under xdist | `test_windows_rocm_sdk_integrity` (4), `test_text_normalization_routes` (2) |
| TIMING | 4 | Timeouts | `tests/probe/test_probe_dictation`, `tests/probe/test_probe_engines`, `test_compile_thread_affinity`, `test_startup_progress_early_bind` |
| W-NODE | 4 | Node scripts started from Python fail | `test_setup_rocm_variant` (3), `test_setup_windows_rocm` |

None of these fails on Linux. The classes are this analysis's reading of the error messages. They are not a donor triage, and OTHER is unexplained.

## Network egress on Windows

The packet's condition is: no model or runtime download, `HF_HUB_OFFLINE=1`, and an egress log with zero model-hub connections. **It fails.**

Three observers were used:

- **The probe.** Python socket calls, attributed to the running test.
- **A TCP watcher** ([`harness/egress_watch.ps1`](harness/egress_watch.ps1)). It is non-admin and polls every connection once a second with its owning process. It is weaker than a packet capture: a connection that opens and closes between polls is missed.
- **The hf-xet log directory** that the suite created.

Findings, original baseline:

1. **A test clones from GitHub during the run.** This is certain and specific to Windows.
   - `test_gguf_desktop_bundle` and `test_gguf_portable_x86_runtime` put a fake `git` first on a `PATH` they build with `:` separators (`f"{fake}:/usr/bin:/bin"`). On Windows the drive letter's colon breaks that entry, so the real `git` runs.
   - The failure output shows `omnivoice.cpp` cloned and `Submodule path 'ggml': checked out '210138933b22…'`, with the submodule fetched from `https://github.com/…` ([`run4/failures.txt`](run4/failures.txt), lines for these two modules).
   - The Python probe cannot see this, because `git` is a separate native process.
2. **Python reached GitHub to download a runtime** in the probed attempt killed at 88 %.
   - `test_setup_preflight.py::test_preflight_returns_expected_shape` reached `github.com` and `media.githubusercontent.com` through `backend/services/media_tools.py:_download`, the FFmpeg bundle download ([`earlier/probe-run2-egress.jsonl`](earlier/probe-run2-egress.jsonl)).
   - It did not recur in run 4. Why it differed is not established.
3. **A Python worker opened a connection to a Hugging Face address.**
   - In the unprobed `-n auto` attempt, the watcher recorded `SynSent 13.36.122.243:443 pid=14936 proc=python` at 2026-11-09 05:00:34 +03:00 ([`watcher/egress-tcp-attempt2-suites.txt`](watcher/egress-tcp-attempt2-suites.txt)).
   - That address reverse-resolves to `ec2-13-36-122-243.eu-west-3.compute.amazonaws.com`. On 2026-11-09 it was in the DNS answer for `us.aws.cdn.hf.co`.
   - The same PID 14936 had started the native `hf_xet` client at 04:56:50: its log file `xet_20261109T045650860+0300_14936.log` is in the inventory below.
   - **Which test made the connection is not identified.** That attempt had no probe, and the 1 s watcher does not record tests.
4. **An unattributed connection to an Azure address.** In the unprobed `-n 4` attempt, a Python worker (PID 17916) had `Established 57.150.192.193:443` at 06:54:27 (no PTR record). The destination's owner and the test are not identified.
5. **Run 4 (probed, complete) showed no Python connection.**
   - The probe saw only name lookups of test hosts (`youtu.be`, `youtube.com`, `example.com`, `x`, `gpu.example`) through the donor's URL-safety checks. It also saw local route detection (`192.0.2.1:9` UDP) and the offline probe (`10.255.255.1`).
   - The watcher saw no non-loopback TCP connection owned by a named `python` process ([`watcher/egress-tcp-run4.txt`](watcher/egress-tcp-run4.txt)). It has 384 entries whose process had exited before it could be named:
     - most go to GitHub (`20.233.83.145`/`.146`) and Microsoft (`2620:1ec:…`, `2603:10xx:…`) addresses;
     - they overlap in time with the agent's own `gh` and `git` use, so **they cannot be attributed to tests**;
     - separately, the three `52.85.110.x` (CloudFront) addresses, which share a range with `cas-bridge.xethub.hf.co`, were opened by the laptop vendor's background processes (`HwMdcCenter`, `MBAMessageCenter`, `BasicService`), not by the suite.

   This **does not show the suite is clean**. A connection shorter than one second can be missed, and finding 1 (native `git`) did occur in run 4.
6. **Test isolation.** The suite starts `hf_xet` in the real per-user cache, `%LOCALAPPDATA%\OmniVoice\hf_cache\xet\logs`, not in a temporary directory. That folder holds 103 log files from 2026-11-09 04:18 to 2026-11-10 06:00 ([`watcher/hf-xet-log-inventory.txt`](watcher/hf-xet-log-inventory.txt)). Every one contains only start-up and log-cleanup lines and no transfers. The first, at 04:18, is from before the suites and is probably the agent's environment check; it is not attributed.

Together with the Linux half, where `huggingface.co` and `us.aws.cdn.hf.co` were looked up and contacted in both runs, **the Grain's network condition fails**. It must not be reported as verified.

## Files

| Path | Content |
| --- | --- |
| `run4/junit-0.xml` … `junit-9.xml`, `pytest-*.log` | Per-chunk JUnit and console output |
| `run4/progress.txt` | Chunk start and end times |
| `run4/analysis.txt` | Output of [`harness/st_d00_analyze.py`](harness/st_d00_analyze.py) |
| `run4/failures.txt`, `run4/classification.tsv` | Every failure and error record, and its class |
| `run4/hung-tests.txt`, `run4/hang-dumps/` | The 21 deselected tests and their stack dumps |
| `run4/probe-egress.jsonl`, `run4/probe-timelines.tar.gz` | Probe records, and per-worker test start/end timelines |
| `earlier/` | Backend, frontend and Electron logs, environment, the incomplete `tests/` attempts, run 2 probe records |
| `watcher/` | TCP watcher logs for each phase, and the hf-xet log inventory |
| `harness/` | The probe, the watcher, the runner, the analysis and classification scripts. They are Wispral research tooling and do not modify the donor. |
