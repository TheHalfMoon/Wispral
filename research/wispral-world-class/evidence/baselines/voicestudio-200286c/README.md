# ST-D00 baseline: WisprStudio donor VoiceStudio@200286c

**Grain:** `ST-D00` (Specification 000E). Packet in `research/wispral-world-class/packets.json`.

**Status:** both halves are recorded. The Linux half is below; the HW-A (Windows) half is in [`windows-hwa/`](windows-hwa/README.md). **The Grain is NOT VERIFIED**: the packet's network condition (zero model-hub connections under `HF_HUB_OFFLINE=1`) fails on Linux and on Windows, and the Windows suites do not pass.

| Item | Value |
| --- | --- |
| Donor and pin | `debpalash/VoiceStudio@200286ccff6f28faaf51bb08b2a5b54c460b39f4` (AGPL-3.0) |
| Research fork | `TheHalfMoon/wisprstudio` (public) |
| Baseline branch | `wispral/baseline-st-d00`, first at `c8b933c50f971ebe3add6e353ce6954e9442b704`, then at `b8e67b5fd164368b0535a00890270d4cfca3759e`. Each is the pin plus one file, `.github/workflows/wispral-baseline-st-d00.yml` ([final copy](wispral-baseline-st-d00.yml)). No donor file is changed. |
| Donor workflows | All 30 disabled through the GitHub API before the baseline branch was pushed |

**The workflow's steps** are copied from the donor's `ci.yml` jobs "Tests (Python)" and "Tests (Electron)", with the donor's pinned action SHAs and tool versions (Python 3.11, uv, Node 22, Bun 1.4.2). It adds two things only:

- failure capture;
- an egress capture during the two pytest steps: DNS queries and outbound TCP SYNs, using `tcpdump`.

## Runs

| Run | Branch head | Purpose |
| --- | --- | --- |
| [42536251537](https://github.com/TheHalfMoon/wisprstudio/actions/runs/42536251537) | `c8b933c` | First run |
| [42538071852](https://github.com/TheHalfMoon/wisprstudio/actions/runs/42538071852) | `b8e67b5` | Rerun after pinning the workflow's own `upload-artifact` to a commit SHA (`ea165f8d…`, v4.6.2) |

**The two failures in the first run were caused by the Wispral workflow, not by the donor.** The donor's `tests/test_actions_pinned.py` requires every action in every workflow to be pinned to a full commit SHA. The first workflow used `actions/upload-artifact@v4`, which is not. In the rerun these two tests pass. Both runs are kept here.

## Linux results (hosted `ubuntu-22.04`)

| Suite | First run (42536251537) | Rerun (42538071852) |
| --- | --- | --- |
| `pytest tests/ -n auto` (`HF_HUB_OFFLINE=1`) | exit 1. **2 failed** (`test_actions_pinned`: workflow-caused), 13,305 passed, 51 skipped, 8 xfailed, 1 xpassed | exit 0. **13,307 passed, 0 failed**, 51 skipped, 8 xfailed, 1 xpassed |
| `pytest backend/tests/` (`HF_HUB_OFFLINE=1`) | exit 0. **600 passed** | exit 0. **600 passed** |
| Frontend (`node --test …node-version`, `bun run test:frontend`) | exit 0 | exit 0 |
| `bun run test` (Electron unit) | exit 0 | exit 0 |
| `bun run check:electron` (typecheck, tests, build, web build, packaging contract) | exit 0 | exit 0 |

Logs are in [`linux-run-42536251537/`](linux-run-42536251537/) and [`linux-run-42538071852/`](linux-run-42538071852/).

## Finding: model-hub egress despite `HF_HUB_OFFLINE=1`

The packet requires "no model or runtime download: `HF_HUB_OFFLINE=1` and an egress log with zero model-hub connections". **This criterion fails on Linux, and the failure reproduced in both runs:**

| Run | Model-hub DNS names looked up during pytest | Outbound HTTPS that followed |
| --- | --- | --- |
| 42536251537 | `huggingface.co`, `us.aws.cdn.hf.co` (23:44:02 UTC) | TCP SYNs to `108.138.246.85:443` and `54.68.202.150:443`. Each is an address in the DNS answer for those names: `huggingface.co` (query id 34494) answered `108.138.246.85, …`. |
| 42538071852 | `huggingface.co`, `us.aws.cdn.hf.co` (00:12:33 UTC) | TCP SYNs to `52.84.217.103:443` and `100.29.213.216:443`. Each is an address in the DNS answer for those names: `huggingface.co` (query id 54716) answered `52.84.217.103, …`. |

- **Attribution.** The capture includes the DNS answers, and each connection's destination is an address returned for a model-hub name. So these are connections to Hugging Face, not just timing coincidences. What is not identified is **which test** made them, because `pytest -n auto` runs in parallel. (An earlier draft of this file said the answers were not captured. That was wrong; the fresh-context review corrected it.)
- **What it means for Wispral.** At least one VoiceStudio test path reaches Hugging Face even when the offline flag is set. This matches the comparison finding (ST-D00b) that WisprStudio needs a local-only mode that blocks all egress.
- **Other non-loopback names** looked up during the tests:
  - `example.com`, `x`, `youtube.com` and `youtu.be`, consistent with tests of URL-ingest validation;
  - `api.snapcraft.io` (rerun only);
  - GitHub and Azure runner infrastructure.

  These are listed in the `egress-python-summary.txt` files.

No donor failure was fixed. The finding is recorded, not patched.

**The Windows half** ([`windows-hwa/`](windows-hwa/README.md)) found more egress: a test that clones from GitHub through the real `git` because its fake-`git` `PATH` breaks on Windows; a runtime download from GitHub by `test_setup_preflight`; and one Python connection to a Hugging Face address that could not be tied to a test.
