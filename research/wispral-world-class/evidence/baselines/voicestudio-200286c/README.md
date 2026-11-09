# ST-D00 baseline: WisprStudio donor VoiceStudio@200286c

**Grain:** `ST-D00` (Specification 000E). Packet in `research/wispral-world-class/packets.json`.

**Status:** the **Linux half is recorded here**. The HW-A (Windows) half is not yet run. The Grain is not `VERIFIED` until both halves are recorded.

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
| 42536251537 | `huggingface.co`, `us.aws.cdn.hf.co` (23:44:02 UTC) | TCP SYNs to `108.138.246.85:443` and `54.68.202.150:443` within 100 ms of the lookups |
| 42538071852 | `huggingface.co`, `us.aws.cdn.hf.co` (00:12:33 UTC) | TCP SYNs to `52.84.217.103:443` (38 ms after the lookup) and `100.29.213.216:443` |

- **Attribution is by timing.** The capture kept DNS queries and SYNs, not the DNS answers, and `pytest -n auto` runs in parallel, so the exact test is not yet identified.
- **What it means for Wispral.** At least one VoiceStudio test path reaches Hugging Face even when the offline flag is set. This matches the comparison finding (ST-D00b) that WisprStudio needs a local-only mode that blocks all egress.
- **Other non-loopback names** looked up during the tests:
  - `example.com`, `x`, `youtube.com` and `youtu.be`, consistent with tests of URL-ingest validation;
  - `api.snapcraft.io` (rerun only);
  - GitHub and Azure runner infrastructure.

  These are listed in the `egress-python-summary.txt` files.

No donor failure was fixed. The finding is recorded, not patched.

**Not yet covered by this half:** the Windows suites and the Windows egress log.
