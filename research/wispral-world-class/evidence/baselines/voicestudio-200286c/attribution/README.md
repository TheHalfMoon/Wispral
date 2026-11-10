# ST-D00 egress attribution: which test reaches Hugging Face

**Grain:** `ST-D00` (Specification 000E). This adds to the baseline in [`../README.md`](../README.md) and [`../windows-hwa/README.md`](../windows-hwa/README.md). It is not a remediation: no donor file was changed, and **ST-D00 stays NOT VERIFIED**.

## Finding

On Linux, `pytest tests/` with `HF_HUB_OFFLINE=1` looks up and connects to Hugging Face. The baseline could not say which test does it. This run identifies it:

| Item | Value |
| --- | --- |
| Test | `tests/test_chunked_tts.py::test_long_text_is_chunked_through_engine` |
| What the test does | posts a long text to `/generate` with a fake TTS engine |
| Call path | `backend/services/model_manager.py` `_run` → `backend/services/watermark.py` `mark_synthetic` → `embed_watermark` → `_get_generator` → `audioseal/loader.py` `load_model_checkpoint` → `torch.hub.load_state_dict_from_url` → `urllib` |
| URL the call path implies | `https://huggingface.co/facebook/audioseal/resolve/main/generator_base.pth`. `_get_generator` calls `AudioSeal.load_generator("audioseal_wm_16bits")`, and that is the checkpoint URL in AudioSeal's packaged card `audioseal_wm_16bits.yaml`. The capture records host names only, not URLs. |
| Why `HF_HUB_OFFLINE=1` does not stop it | inferred from the stack: the download goes through PyTorch's hub helper and the standard library, and no `huggingface_hub` frame appears, so the offline flag is not consulted on this path |
| Effect on the test | none observed: with the lookup blocked it still passes ([`rerun.log`](windows-blocked-rerun/rerun.log)). When watermarking is on (the user setting, or `force=True`), the donor's `mark_synthetic` passes the audio through unchanged if watermarking fails (`backend/services/watermark.py` at `b8e67b5`, docstring lines 366–381). `embed_watermark` logs a warning, "Watermark embedding failed (passing through original)". So with the download blocked, the request still succeeds and the audio leaves **unwatermarked**, with only a log warning. |

So the only model-hub traffic the probe saw is a **model-weight download for the synthetic-speech watermark**, made by a test that uses a fake engine. This matters for Wispral twice over:

- it is a mandatory-network-condition failure of the baseline;
- the product path tries to fetch weights at run time.

## Evidence

### 1. Linux run on the fork, probe in every Python process

[`linux-run-42749631072/`](linux-run-42749631072/): [`TheHalfMoon/wisprstudio` run 42749631072](https://github.com/TheHalfMoon/wisprstudio/actions/runs/42749631072) on branch `wispral/attrib-st-d00-egress` at `2f55fab`. That branch is the baseline commit `b8e67b5` plus three files:

- [the workflow](linux-run-42749631072/wispral-attrib-st-d00.yml);
- [the probe](linux-run-42749631072/wispral_probe.py);
- a [`sitecustomize.py`](linux-run-42749631072/probe-sitecustomize.py) that loads the probe into every Python process.

The baseline branch is unchanged.

- **Suites:** `pytest tests/` gave 13,307 passed, 51 skipped, 8 xfailed, 1 xpassed. `pytest backend/tests/` gave 600 passed. ([`python-summary.txt`](linux-run-42749631072/python-summary.txt)). These are the same totals as the baseline rerun in [`../README.md`](../README.md).
- **Probe:** 31 records the probe classed as non-loopback. Four of them are loopback aliases its classifier cannot parse (`127.1`, `0x7f000001`, `2130706433`). Four are model-hub records: lookups of `huggingface.co` and `us.aws.cdn.hf.co`, and a connect call to each. All four are attributed to the test above, inside a pytest worker (pid 3515) ([`attribution-summary.txt`](linux-run-42749631072/attribution-summary.txt), [`probe-out/`](linux-run-42749631072/probe-out/)).
  - The probe drops standard-library frames by matching the Windows path `/Lib/`, which does not match on Linux, and keeps the last 12 frames. So on Linux the kept frames were all standard-library `urllib` and `http.client` frames. The calling library was found with the Windows rerun below.
  - **Linking the Linux traffic to AudioSeal is an inference.** It rests on the same test, the same `urllib` frame shape, and the full call path from the Windows stack, which comes from a different Python build with different line numbers.
- **Packet capture** ([`egress-python.txt`](linux-run-42749631072/egress-python.txt), lines 159–186), at 2026-11-10 03:43:09 UTC:
  1. A lookup of `huggingface.co`, answered with `143.204.1.6, …`.
  2. A TCP SYN to `143.204.1.6:443`.
  3. About 100 ms later, a lookup of `us.aws.cdn.hf.co`, answered with `44.233.64.198, …`.
  4. A TCP SYN to `44.233.64.198:443`.

  The second lookup is consistent with an HTTP redirect from the Hub to its CDN. **The capture holds only SYNs and DNS, so it does not show whether the file finished downloading.**

### 2. Windows rerun of that one test, network blocked

[`windows-blocked-rerun/`](windows-blocked-rerun/): on HW-A, the same test was run alone from the ST-D00 checkout.

- [`sitecustomize.py`](windows-blocked-rerun/sitecustomize.py) makes every non-loopback name lookup **raise an error** and write the full Python stack. Nothing could be downloaded.
- `HF_HUB_OFFLINE=1` was set.
- `LOCALAPPDATA`, `APPDATA`, `USERPROFILE`, `XDG_CACHE_HOME` and `HF_HOME` pointed to new empty folders, so no cached file could hide the request.

It was run twice:

- **First run.** Only its stack dump was kept: [`block.txt`](windows-blocked-rerun/block.txt). The setup and result above come from the agent's session for that run and were not logged to a file.
- **Second run**, repeated after review with everything logged ([`rerun.log`](windows-blocked-rerun/rerun.log), [`block-rerun2.txt`](windows-blocked-rerun/block-rerun2.txt)). The log records the environment, the command, a check that the folders were empty (0 entries), `1 passed` with `PYTEST_EXIT=0`, and exactly one blocked lookup, `huggingface.co:443`, during the test's call phase.

The stacks give the call path in the table above.

## Open questions

- **Why run 4 on Windows saw no lookup.** In the probed Windows run 4, this test passed and the probe recorded no model-hub lookup. A clean-cache rerun does make the lookup. A search of the user cache folders and the work directory found no AudioSeal checkpoint ([`checkpoint-search.txt`](windows-blocked-rerun/checkpoint-search.txt)). Why run 4 differed is not established.
- **The earlier Windows connection attempt.** The Windows SYN to 13.36.122.243 recorded in the baseline came from an unprobed run. It is consistent with this path, but it is not shown to be this test.
- **Whether the Linux download completed.** `pytest-tests.log` shows a `weight_norm` `FutureWarning` listed under this test, together with another test. That could mean the generator model was built, which would need the download to have finished. It is inconclusive.
- **Other weight downloads.** Only this path was observed. Other tests that reach the same watermark code with a real cache miss could do the same.

## What a remediation would need (not done here)

- The test suite needs the watermark generator stubbed or a local checkpoint, and it must fail closed on egress.
- The product needs AudioSeal weights treated as a pinned, licence-checked model asset under the offline policy, not fetched at run time by `torch.hub`.
- A failed watermark load must not let unwatermarked synthetic speech leave with only a log warning. The donor's own `mark_synthetic` docstring (`watermark.py` lines 366–368 at `b8e67b5`) presents this mark as its answer to EU AI Act Art. 50(2), which, per that docstring, requires machine-readable marking of synthetic audio. This legal reading is the donor's and has not been checked independently. If it holds, the pass-through on an offline machine without cached weights is a compliance risk, not just a test problem.

These belong to a later Grain. Nothing here changes the donor.
