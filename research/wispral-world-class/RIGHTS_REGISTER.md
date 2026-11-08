# Rights register (CORE-00)

**Status:** research record for Grain `CORE-00` (Specification 000F). Re-verified on 2026-11-08.

**Not:**

- a legal opinion;
- a licence for anyone;
- a claim that any private agreement was examined.

**Method.** [`evidence/core-00/verify_core00_anchors.py`](evidence/core-00/verify_core00_anchors.py) re-verified every anchor in [`evidence/core-00/anchors.json`](evidence/core-00/anchors.json) at its pinned commit. For each anchor it resolved the commit, fetched the stored git blob, recomputed the blob id and SHA-256, checked any recorded prefix, and read the declared licence. Result: `ANCHORS=57 PASS=57 FAIL=0`, in [`evidence/core-00/runs/verify_core00_anchors.txt`](evidence/core-00/runs/verify_core00_anchors.txt).

**Rights are recorded separately.** Each column below is its own question. None implies another:

- the **public licence**, which is what the repository declares at the pin;
- the **founder grant**: `CONFIRMED_BY_FOUNDER`, with the documents private and neither requested nor inspected (Constitution Principle XVIII);
- **weights, data, voices, fonts and media**, which are never inferred from either of the above.

## 1. Licence gate (Q-01)

| Gate | State | Rule |
| --- | --- | --- |
| Wispral outbound licence | **CLOSED**. `TheHalfMoon/Wispral` has no LICENSE file: `gh api repos/TheHalfMoon/Wispral/license` returned HTTP 404 on 2026-11-08. | No `COPY` or `ADAPT` packet may land code in a Wispral repository until the founder's outbound-licence decision is recorded in this register. Research, reference reading and baselines of unmodified donors in their own forks are not blocked. |

**Inputs the founder's decision has to fit.** These are facts, not advice:

- The WisprStudio lead donor is AGPL-3.0. Its use in Wispral rests on the founder's confirmed grant, recorded per copied file.
- Every other lead donor is permissive: MIT, Apache-2.0 or BSD-2-Clause.
- Some files are reference-only (§3). They do not constrain the outbound licence, because no code from them is copied.

## 2. Donor register

| Donor | Pin | Public licence at pin | Founder grant | Decision (matrix) | Separate rights still open |
| --- | --- | --- | --- | --- | --- |
| `cjpais/Handy` | `73cc8579cff74e97e08de9d86035a92e4335ff7f` | MIT | not required | FORK (WisprSide) | Per-model weight licences in its catalogue; ggml/`transcribe-cpp` notices |
| `zachlatta/freeflow` | `37786464bb2422c58313d7456fe7191d115d0d18` | MIT | not required | ADAPT (algorithm) | none |
| `OpenWhispr/openwhispr` | `cb08c411dd008c57e4f0a8193756d6b5812479fd` | MIT | not required | ADAPT / COPY (lists) | none |
| `Beingpax/VoiceInk` | `4bc74caddfad6fdfab71e5957451b83b33c1a2c5` | GPL-3.0 (LICENSE text; the licence API reports `NOASSERTION`) | not required | **REFERENCE only** (concept, no code) | none |
| `TheHalfMoon/SafeEvidence` | `f05bc006185d67f13ca00ecc7b697c6aef0703dc` | Apache-2.0 | founder-owned, `CONFIRMED_BY_FOUNDER` | ADAPT | none |
| `TheHalfMoon/Orcel` | `f0b78e6544cf6ea9c2457a6b6f483490c7bd0f6f` | Apache-2.0 (repository); per-file SPDX varies | founder-owned, `CONFIRMED_BY_FOUNDER` | COPY (`orcel-journal`) / ADAPT (`orcel-platform`) | Three FSL-1.1-MIT files are reference-only (§3); `process.rs` adapts MIT code whose notice must be kept |
| `debpalash/VoiceStudio` | `200286ccff6f28faaf51bb08b2a5b54c460b39f4` | AGPL-3.0 (LICENSE text; the licence API reports `NOASSERTION` at the pin and `AGPL-3.0` on the default branch) | `CONFIRMED_BY_FOUNDER`, recorded per copied file | FORK (WisprStudio) | The default engine's weights are non-commercial (rejected as default); the AudioSeal weight licence is unrecorded; per-engine weights |
| `resemble-ai/chatterbox` | `5de7a54aa4e5e2baadb0182dde554908b48b85c2` | MIT (code) | not required | WRAP | Weights per model card |
| `jamiepine/voicebox` | `8af7efe62fab8d33e2a5dfbedabaa45f68a5184f` | MIT | not required | REFERENCE | none |
| `emcie-co/parlant` v4.0.2 | `2a463ccd10eaf0d70d42731705f4f00ef066bee8` | Apache-2.0 | not required | WRAP (conditional on `KT-01`) | Model provider terms at run time |
| `emcie-co/parlant` v3.3.2 (fallback) | `61bba3b2b3fffd677d345e393e8c942dbd400297` | Apache-2.0 | not required | fallback | as above |
| `chatwoot/chatwoot` | `caab07a8f00032d5205b5a5d7e2eb0ba2f3d2d82` | MIT outside `enterprise/`; `enterprise/` separately licensed (LICENSE text; the API reports `NOASSERTION`) | not required | API integration, unmodified | Never use `enterprise/` code |
| `standard-webhooks/standard-webhooks` | `ab6844147ce9cdb0d2dbf2e60d1ea85001fd2554` | Apache-2.0 | not required | ADAPT | none |
| `sierra-research/tau2-bench` | `033bf082f48e4a3c6a1256208e93cf2ce9c3bb6f` | MIT | not required | test dependency | Task-set data terms, if any are bundled |
| `pipecat-ai/pipecat` | `fda1d5e0cde9625c8dcef7b653ed731c2ce63672` | BSD-2-Clause | not required | ADAPT (later) | Voice model weights (auto-download disabled) |
| `botpress/botpress` | `956bcdef7a8f6499519e28ec5dda6e3ed3c96ad8` | MIT | not required | REFERENCE | none |
| `TheHalfMoon/Sentrdel` | `f5747319a50831ef7cee983d253c0ca5503c9a64` | Apache-2.0 | founder-owned, `CONFIRMED_BY_FOUNDER` | ADAPT | none |
| `TheHalfMoon/Ascout` | `48902389ec37019845fd67c8b8c53c5f499ffc85` | Apache-2.0 | founder-owned, `CONFIRMED_BY_FOUNDER` | ADAPT | none |
| `TheHalfMoon/Ninerr` | `616bafaa26a58476bb2e3ee876b28e13ac1348f3` (studio-host); `8cba15c4e4af40b12476433a49e20a1696cfc0f8` (network-policy) | Apache-2.0 | founder-owned, `CONFIRMED_BY_FOUNDER` | ADAPT (pattern) / REFERENCE | none |
| `agentclientprotocol/rust-sdk` 5.0.0 | `050cd94c081056ace37a7b89abfed7f6220b47eb` | Apache-2.0 | not required | WRAP (later) | none |
| `TheHalfMoon/Yamakan` | `c178610544501a497f29860e6ab620167d798947` | GPL-3.0 (combined distribution, with third-party GPL code per its NOTICE) | founder-owned | **REFERENCE only** | No code is copied |

## 3. Reference-only files and repositories

No code may be copied from these into Wispral. Reading them for design is allowed.

| Source | Files | Reason |
| --- | --- | --- |
| `TheHalfMoon/Orcel@f0b78e65` | `crates/orceld/src/app_api.rs`, `crates/orcel-approval/src/linux.rs`, `crates/orcel-approval/src/presence_unix.rs` | Each declares `SPDX-License-Identifier: FSL-1.1-MIT` (third-party), verified by the anchor check `contains FSL-1.1-MIT` |
| `TheHalfMoon/Yamakan@c1786105` | the whole repository | GPL-3.0 combined distribution, including third-party GPL code (NOTICE verified to contain `GPL`) |
| `Beingpax/VoiceInk@4bc74cad` | the whole repository | GPL-3.0. The concept only; a founder grant may be invoked per file if code is ever needed |
| `chatwoot/chatwoot@caab07a8` | `enterprise/` | Separately licensed |

## 4. Klaint pins (packet acceptance)

All are recorded in §2 and verified in the anchor run:

| Pin | Value |
| --- | --- |
| Parlant v4.0.2 | `2a463ccd…` |
| Parlant v3.3.2 fallback | `61bba3b2…` |
| Chatwoot | `caab07a8…` |
| standard-webhooks | `ab684414…`, `libraries/python/standardwebhooks/webhooks.py` |
| tau2-bench | `033bf082…`, `src/tau2/evaluator/evaluator_env.py` |
| Pipecat | `fda1d5e0…` |
| Botpress | `956bcdef…` |

## 5. Not covered here

- Model, tokenizer, dataset and voice rights: see the model rights screen in [`SOURCE_DECISION_MATRIX.md`](SOURCE_DECISION_MATRIX.md) §Models. Each must be recorded per artifact before use (Principle XVIII).
- Trademark, domain and store clearance for the product names.
