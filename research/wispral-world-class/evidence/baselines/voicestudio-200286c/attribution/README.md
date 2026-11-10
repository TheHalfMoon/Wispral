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
| Why `HF_HUB_OFFLINE=1` does not stop it | the download goes through PyTorch's hub helper and the standard library, not through `huggingface_hub`, so the offline flag is never consulted |
| Effect on the test | none: it passes either way (see the Windows rerun below) |

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

- **Suites:** `pytest tests/` gave 13,307 passed, 51 skipped, 8 xfailed, 1 xpassed. `pytest backend/tests/` gave 600 passed. These are the same totals as the baseline rerun ([`python-summary.txt`](linux-run-42749631072/python-summary.txt)).
- **Probe:** 31 non-loopback records. Two are model-hub lookups, `huggingface.co` then `us.aws.cdn.hf.co`. Both are attributed to the test above, inside a pytest worker ([`attribution-summary.txt`](linux-run-42749631072/attribution-summary.txt), [`probe-out/`](linux-run-42749631072/probe-out/)).
  - The probe keeps the last 12 stack frames. Here those were all standard-library `urllib` and `http.client` frames, so the calling library was found with the Windows rerun below.
- **Packet capture** ([`egress-python.txt`](linux-run-42749631072/egress-python.txt), lines 161–181), at 2026-11-10 03:43:09 UTC:
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

Result: `1 passed`. There was exactly one blocked lookup, `huggingface.co:443`, and its full stack is in [`block.txt`](windows-blocked-rerun/block.txt). That stack gives the call path in the table above.

## Open questions

- **Why run 4 on Windows saw no lookup.** In the probed Windows run 4, this test passed and the probe recorded no model-hub lookup. A clean-cache rerun does make the lookup, and no AudioSeal checkpoint was found in the laptop's usual cache locations. Why run 4 differed is not established.
- **The earlier Windows connection attempt.** The Windows SYN to 13.36.122.243 recorded in the baseline came from an unprobed run. It is consistent with this path, but it is not shown to be this test.
- **Other weight downloads.** Only this path was observed. Other tests that reach the same watermark code with a real cache miss could do the same.

## What a remediation would need (not done here)

- The test suite needs the watermark generator stubbed or a local checkpoint, and it must fail closed on egress.
- The product needs AudioSeal weights treated as a pinned, licence-checked model asset under the offline policy, not fetched at run time by `torch.hub`.

These belong to a later Grain. Nothing here changes the donor.
