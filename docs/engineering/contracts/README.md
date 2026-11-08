# Wispral core contracts (CANDIDATE v1)

Executable interface specifications for the shared Wispral platform layer described in [WISPRAL_PRODUCT_ARCHITECTURE.md](../../strategy/WISPRAL_PRODUCT_ARCHITECTURE.md#3-wispral-core-contracts-library-fixtures). They are **candidates**: no product consumes them yet. Adopting them is packet `CORE-01` in the [implementation packets](../WISPRAL_IMPLEMENTATION_PACKETS.md).

**History.** The first draft (7 schemas, 33 cases) passed its own fixtures, but the independent Core audit showed that 23 of 25 donor-informed invalid records also passed ([Core research report §3](../../../research/wispral-world-class/evidence/research-reports/CORE_FOUNDER_REPOS_RESEARCH.md#3-review-of-the-drafted-contracts-against-donors)). This revision applies those findings, adds the eighth contract (`effect_intent`), and adds runtime and sequence checks. Each fixture that closes an audit gap carries the audit's gap ID (`G-ENV-*`, `G-CAN-*`, `G-MM-*`, `G-CON-*`, `G-POL-*`, `G-PROV-*`, `G-DEL-*`).

**Second revision (independent architecture and security review, 2026-11-08):** 64-bit identifiers (`start_generation`) are decimal strings so JavaScript hops never round them; `delivery_outcome` gains the UIA `focus_element` and the `hosted_process_instance` behind ApplicationFrameHost; text delivery is no longer an `effect_intent` (most targets have no read-back probe); `effect_intent` keys are unique per (principal, owner, key) and bound to an ALLOW verdict of the same class and principal; an ASK becomes ALLOW only with an operator or step-up-verified confirmation; stock voices come from manifest catalog entries; consent binds the reference-audio digest and a speaker match; admitted models never use pickle or remote code; contract-bearing envelope events carry their typed payloads.

**Canonicalization (required for identical digests across Rust, Python and TypeScript):** JSON is canonicalized with RFC 8785 (JCS) before hashing; strings are NFC-normalized; Windows paths for `image_path_digest` are made absolute, use backslashes, are case-folded with the invariant culture and have no trailing separator before hashing. Cross-language digest tests are part of CORE-01.

| Contract | File | Key invariants | Donor lineage |
| --- | --- | --- | --- |
| Operation envelope | [envelope.schema.json](envelope.schema.json) | Closed, discriminated principal kinds (desktop binds the OS session; tenant binds account and channel); bounded payload; worker events carry the artifact digest; render events carry the consent epoch; policy version is a digest or `name@semver` | Orcel `orcel-audit` field vocabulary (reference) |
| Cancellation state | [cancellation.schema.json](cancellation.schema.json) + [transitions](transitions/cancellation.json) | Lease release only after an observed stop, a pre-cancel completion, or an owner-observed exit after a crash; `effect_state` can be `unknown` and then names a reconcile intent; every cancelled request gets exactly one response; kills target `(pid, start_generation)` | ACP rust-sdk 5.0 cancellation rules; Orcel `process.rs` identity |
| Model capability manifest | [model_manifest.schema.json](model_manifest.schema.json) | Multi-file bundles with digests; weight license separate from code license; measured language cells cite evidence; offline artifacts declare no hosts and no network; provider-managed or API routes are never offline; models have an `evidence_only` authority ceiling; automatic download is not representable; admitted models have a resolved commercial status | Ascout `EngineDescriptorV1` (adapted) |
| Voice consent record | [consent_record.schema.json](consent_record.schema.json) | Opaque subject reference (no personal display data); RFC 3339 UTC dates; revocation timestamped and append-only; expiry needs an end date; third-party voices are watermarked | VoiceStudio consent (product); SafeEvidence append-only pattern (reference) |
| Policy verdict | [policy_verdict.schema.json](policy_verdict.schema.json) | Candidate vs enforced decision; UNDECIDABLE resolves to ASK with a human present and DENY unattended; enforcement never widens; non-read ALLOW cites a rule; personal-voice render cites consent; text delivery cites a target binding | Sentrdel narrowing lattice (adapted) |
| Provenance event | [provenance_event.schema.json](provenance_event.schema.json) | Derived text and outcomes point at their parent; model identity with digest on raw and derived text; prompt/threshold digests on rewrites; intent state on dispatch and outcome; bounded retention states its days; media never embedded | orcel-journal, orcel-audit, SafeEvidence proof components |
| Delivery outcome | [delivery_outcome.schema.json](delivery_outcome.schema.json) | Target captured at activation with PID-reuse-safe process identity; revalidated before any delivery; refusals deliver nothing; clipboard restored only if used and always history-excluded; `unknown` outcome; stale epochs refused | Handy `paste_tx`, FreeFlow `AppTextInsertionCore`, VoiceInk vocabulary (concepts) |
| Effect intent | [effect_intent.schema.json](effect_intent.schema.json) + [transitions](transitions/effect_intent.json) | Six states and the exact `may_become` table copied from orcel-journal; unknown outcomes are closed only by a reconcile probe; text delivery is owned by the WisprSide transaction | `TheHalfMoon/Orcel@f0b78e65` `crates/orcel-journal/src/lib.rs` |

## Run

```text
python -I docs/engineering/contracts/fixtures/build_cases.py   # regenerate fixtures/cases.json
python -I docs/engineering/contracts/run_conformance.py
```

Result on 2026-11-08 after the independent architecture and security reviews (Python 3.14.7, jsonschema 4.26.0): `PASS` — 8 schemas, 131 cases (88 shape, 6 runtime), 10 state-machine sequences and 4 cross-record bundles (intent uniqueness and verdict binding); every case matched its expected verdict (`REPRODUCED`). This proves contract conformance only. Whether products *behave* this way (revalidation actually happening, leases actually released only on observed stop) needs product conformance fixtures (packets `CORE-09`, `SD-M3..M6`, `ST-D03`, `KT-03`).

**Known simplification:** `compose()` in the runner is a simplified narrowing composition. Exact Sentrdel semantics, including `UndecidableResolution` and the kernel floor, are ported with the donor's exhaustive test vectors in packet `CORE-03`, and the Rust and Python implementations must then produce identical verdict JSON for every fixture.

## Evolution rules

- Additive optional fields → minor version; removing or tightening a field → new major version with migration notes and both majors' fixtures kept.
- The Rust crate and the Python port must pass the same fixture file in CI before either is used by a product.
- `$id` URLs use the reserved `.invalid` domain on purpose; no network resolution is implied.
