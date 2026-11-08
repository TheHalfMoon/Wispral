# Wispral Core: shared contracts and founder-repository research

- Date: 2026-11-08. Role: Core / shared-contracts and founder-repository research lead. Read-only on GitHub: no pushes, comments, PRs, issues or settings changes.
- Inputs: prior bundle `pr124:research/rea/2026-10-21/*` (Core deep dive, `source-transplants.json`, `core-source-evidence.json`, catalog), `pr124:docs/strategy/WISPRAL_PLATFORM_ARCHITECTURE_REPLAN.md`, Opus review `pr125:.../INDEPENDENT_REVIEW.md` (S2, M5, S5), and the main session's draft contracts at `wispral/docs/engineering/contracts/*.schema.json` (untracked working-tree files, not committed).
- Acquisition: Git clones failed with "Filename too long" because the scratchpad path is longer than Windows MAX_PATH, and `core.longpaths` did not help the remote helper. Donor code was instead taken from GitHub tarballs at exact SHAs and extracted to `scratchpad\core\<repo>`. Blob identity comes from `git/trees?recursive=1` at the pin and at HEAD (`scratchpad\core\trees\*.tsv`, with deltas in `*-delta.txt`). Pinned versions of changed files are in `scratchpad\core\pinned\`. Content was treated as untrusted. Python ran with `-I`.

Evidence tags: **SOURCE_VERIFIED** (repo@sha:path:line, bytes read here), **DOCUMENTED** (README or document text only), **REPRODUCED** (re-executed here), **RUNTIME_OBSERVED**, **NOT_RUN**, **BLOCKED_EXTERNAL**, **REJECTED**.

What was actually executed: GitHub API reads; tree and blob comparison (REPRODUCED); sha256 of the key donor files (REPRODUCED); the draft contract conformance runner `run_conformance.py`, which gave `PASS`, 7 schemas, 33/33 cases (REPRODUCED); and a 25-instance donor-semantics gap probe against the draft schemas (`scratchpad\core\gap-probe.txt`, script `scratchpad\s\gp.py`), REPRODUCED. **No Rust or Node build or test, no egress test and no runtime worker was executed (NOT_RUN).**

---

## 1. Drift and re-pin

HEADs were read on 2026-11-08. Pinned files are the acquired file records in `core-source-evidence.json`, compared by git blob.

| Repo | Prior pin | HEAD (commit date) | Pinned files unchanged / changed / missing | Material change | Re-pin recommendation |
| --- | --- | --- | --- | --- | --- |
| TheHalfMoon/Sentrdel (private, Apache-2.0) | `f5747319` | `f5747319a50831ef7cee983d253c0ca5503c9a64` (2026-09-16) | 17/0/0; tree identical | None. Recomputed sha256 of `narrowing.rs` `44a2e9a6…`, `bounded_json.rs` `f1aa8820…` and `process_tree.rs` `3ba124be…` equals the prior record (REPRODUCED) | **Keep pin** |
| TheHalfMoon/Orcel (public, Apache-2.0 repo; per-file SPDX varies) | `57af189b` | `f0b78e6544cf6ea9c2457a6b6f483490c7bd0f6f` (2026-11-07) | 13/9/0. Changed: `orcel-audit/src/lib.rs`, `orcel-approval/src/lib.rs`, `orcel-policy/src/{lib,protected_state,sg000040}.rs`, Cargo.toml, README | `orcel-audit::record` is unchanged at line 42. Only the default path changed (it now uses `orcel_platform::stores::AUDIT`; the Windows root moved from `%LOCALAPPDATA%\Orcel` to `%USERPROFILE%\.orcel`). **New crate `orcel-journal`** (fsync'd intent journal) and new `orcel-platform/{process,peer,acl}.rs` are better Core donors than `orcel-audit` (§2). +300 files, 282 modified | **Re-pin to `f0b78e65`** |
| TheHalfMoon/Ascout (public, Apache-2.0) | `48902389` | `32d02a021a48abcb07e576a6c6758e0aad7bd6ed` (2026-11-07) | 10/2/0 (README, package.json only) | `engine-descriptor.ts` blob `141c5576…` is unchanged; `EngineDescriptorV1` is still at line 45. The 255 additions are almost all `qualification/*` evidence | Re-pin optional; **keep `48902389` for the descriptor** (identical bytes) |
| TheHalfMoon/Ninerr (public, Apache-2.0) | `8cba15c4` | `616bafaa26a58476bb2e3ee876b28e13ac1348f3` (2026-11-07) | 17/2/0 (package.json, `studio-host/src/server.ts`) | `network-policy/src/{policy,address,types,validation,errors}.ts` are unchanged (sha256 `eb2e32a5…` matches). `readiness.ts` changed but was not in the pin set | Keep for policy. Pin `616bafaa` for the studio-host auth pattern (§6) |
| TheHalfMoon/Yamakan (public, **GPL-3.0-or-later** combined) | `1bb71e8c` | `c178610544501a497f29860e6ab620167d798947` (2026-11-07) | 5/8/0 (`core/process/owner.ts`, `workers.ts`, `jobs.ts`, `command/policy.ts`, tests, NOTICE) | Now a creative production platform (+890 files: `src/studio`, `core/timeline`, `core/audio`, `vendor/ffmpeg`). `owner.ts` adds a hashed `WorkerProfile` (`engine-worker` v1: AppContainer, no network, kill-on-close Job Object, lines 30–97). NOTICE: combined distribution is GPL-3.0-or-later and includes third-party GPL code | Re-pin to `c1786105` **for reference only**. GPL plus third-party code means no copying into Wispral |
| TheHalfMoon/SafeEvidence (public, Apache-2.0) | `1a10bc59` | `f05bc006185d67f13ca00ecc7b697c6aef0703dc` (2026-11-07) | 3/1/0 (README) | **New material**: a `product/` Rust workspace (contracts, proofstore, release SBOM, vault, keyring), plus CI egress gates `tools/ci/{ta03_isolated.sh, core_no_sockets.py, ta29_dependency_denial.py, network_trace_report.py}` and `product/deny.toml` HTTP-client bans. +182 files | **Re-pin to `f05bc006`** and promote from NOT_SELECTED to a Core donor (§2) |
| TheHalfMoon/Hala (public, no license) | `00f66923` | `00f6692383ca9e9cc147380b062676dd74932e83` (main, 2026-10-13) | 1/0/0 | `main` is unchanged (3 files). The 2026-11-07 push went to feature branches (`ps/h22…`, `ps/h25…`: model-training evidence for "Aladdin Pro") (DOCUMENTED) | Keep. REJECTED for Core |
| agentclientprotocol/rust-sdk (Apache-2.0) | `652d1003` (3.4.0) | `050cd94c081056ace37a7b89abfed7f6220b47eb` (2026-11-02), **5.0.0** | 2/11/1. `src/agent-client-protocol/src/capabilities.rs` is gone; `session.rs`, `concepts/cancellation.rs` and the tests changed | Two major versions. Module paths moved (`schema::v1` became `v1::schema`). New crates: `agent-client-protocol-http`, `-polyfill`, `-trace-viewer`. Cancellation doc (line 144, SOURCE_VERIFIED): "A cancelled request still gets exactly one response", which succeeds only where the method defines a cancelled result; otherwise it returns `-32800`, never partial results. The HTTP server says "CORS does not authenticate requests" (`agent-client-protocol-http/src/server.rs:66`) | **Re-pin to `050cd94c` / 5.0.0** before any A-01 work. The CORE-ACP and CORE-CANCEL anchors are stale |

Not in the drift list, but observed: SpecGrain `5de7d649`, Diffcipline `1e6d14f7`, commandF `3040c4c0` and Morize `62fc04d0` are unchanged. Skilit moved `2b053d35` → `157ace7f` (36 commits); `capture-scope/child/network.ts` did not change. **Zain HEAD `0a843a2c` equals the prior "TheHalfMoon/wepld" pin**, and its README is "WePLD". The repository appears to have been renamed, so the catalog entry should be re-keyed.

---

## 2. Does Wispral need a centralized runtime? Verdict: **No.**

A centralized runtime is not justified by any inspected source or requirement. All four candidate centralizers would duplicate an owner that already exists.

- Sentrdel's `ContainedChild` vs Handy's `engine_supervisor` and VoiceStudio's `contained_subprocess`.
- Orcel's `orceld` daemon, which is a full computer-use authority product.
- Yamakan's `procd`.
- A Core daemon in front of the Klaint `ToolService`.

The desktop products are single-user and local. Klaint is multi-tenant and server-side. They share **vocabulary and invariants, not a process**. Orcel itself shows the cost: `orceld` needs per-user ACL'd state, peer verification, lifecycle install/update/doctor (`crates/orcel-lifecycle/src/*`, about 9k lines) and a daemon API. That is a product, not a library (SOURCE_VERIFIED, Orcel@f0b78e65 `crates/orcel-lifecycle/src/`, `crates/orceld/src/main.rs`).

**Core = (a) versioned JSON Schemas, (b) two small dependency-light Rust crates, (c) a shared fixture corpus with positive, tamper-negative and sequence cases, (d) Python parity, and (e) CI gates.** Each product embeds what it needs. Core never owns a process, store, listener or credential.

### 2.1 Shared artifacts and best donor per artifact

| Artifact | Best donor (exact) | Decision | Why |
| --- | --- | --- | --- |
| Operation/session envelope schema | Orcel `RequestEnvelope` fields used by `AuditEvent` (Orcel@f0b78e65 `crates/orcel-audit/src/lib.rs:16-27`: request_id, client_session_id, workspace_id, capability, operation, target, policy_revision, outcome), SOURCE_VERIFIED | REFERENCE | Field vocabulary only. The Wispral envelope adds epoch, sequence and consent epoch, which no donor has |
| Cancellation state machine | ACP rust-sdk@050cd94c `src/agent-client-protocol/src/concepts/cancellation.rs:7,144` (cooperative; one response per cancelled request); Orcel@f0b78e65 `crates/orcel-journal/src/lib.rs:213-245` (`IntentState::may_become`) | ADAPT (semantics) + COPY (transition-table style) | ACP supplies the peer semantics. orcel-journal supplies the "Unknown, then Reconciled" closure for effects that may have started |
| Model/voice-asset inventory and capability manifest | Ascout@48902389 `src/assurance/contracts/engine-descriptor.ts:45` (`EngineDescriptorV1`: implementation_identity.artifact_sha256, capabilities, effect_classes, requirements{process,network,sandbox}, license_provenance_state.admission_state, qualification_evidence_refs, known_limitations, authority_ceiling) and `intent.ts:30` (E0–E7 effect classes), SOURCE_VERIFIED | ADAPT | Strict exact-key validation and an authority ceiling are exactly what the draft manifest lacks (§3) |
| Consent record | No founder donor carries voice consent. VoiceStudio `profiles.py` consent (ST-CONSENT, prior pin `28bf2c7`) is the product implementation. SafeEvidence@f05bc006 `product/crates/safeevidence-proofstore/src/lib.rs:1-8` (append-only via triggers; update/delete refused) shows the append-only pattern | NEW (thin) + REFERENCE | Domain-specific. Revocation must be an append-only event, not an in-place status edit |
| Policy verdict | Sentrdel@f5747319 `crates/sentrdel-policy/src/lib.rs:130` (`UndecidableResolution`, default Ask, no Allow), `:147` (`compose_verdicts`: DENY absorbing, empty input = UNDECIDABLE), `:203` (`resolve_for_enforcement`: kernel floor, then resolution); `narrowing.rs:58` (`validate_repository_narrowing`), `:85` (`compose_base_and_repository`); `sentrdel-schema/src/policy.rs:13` (`Verdict`) | **ADAPT** into `wispral-policy` | Pure; about 120 lines of logic. Drop the `regorus` and `sentrdel-schema`/`schemars` dependencies and redefine `Verdict` with identical serde names |
| Provenance/audit event and journal | Orcel@f0b78e65 `crates/orcel-journal/src/lib.rs` (deps fs4, serde, serde_json): `append_line` fsyncs (`sync_data`) and seals a torn tail (lines 81-125); `MAX_LINE_BYTES` 64 KiB (line 36); `append_opening_line` (line 89) reserves room to close; one exclusive writer via an OS lock (`Journal`, line 278); `recover` (line 256) fails closed on illegal transitions. "the journal records, it never authorizes" (header) | **COPY** (crate as is, with notice) | Strictly better than `orcel-audit` (flush, not fsync; no bounds). No third-party SPDX header in `orcel-journal`. Repository license is Apache-2.0 |
| Delivery / external-effect outcome | Same `orcel-journal` `IntentState` (Pending, Dispatched, Settled, Abandoned, Unknown, Reconciled); Orcel@f0b78e65 `crates/orcel-platform/src/process.rs:40,54,65` (`ProcessGeneration`, `start_generation`, `is_same_instance`; Windows uses `GetProcessTimes` creation time) for PID-reuse-safe target identity | COPY (states) + ADAPT (process identity into the WisprSide fork) | `process.rs` adapts MIT Cua code with its notice. Preserve `docs/orcel/notices/cua-MIT.txt` |
| Bounded input preflight | Sentrdel@f5747319 `crates/sentrdel-engine/src/bounded_json.rs:55` (`preflight_json`; limits at lines 8-13; the dialect enum is SARIF/native only; the byte cap sits in the caller, `adapter.rs:38`, 8 MiB) | **ADAPT** | Generalize the `Context` dialects to a "generic frame". Add a total-byte cap inside the function. Keep the "walk before serde materializes" property |
| Worker process containment | Sentrdel `process_tree.rs:26` (`ContainedChild`, process-wrap =9.1.0 Job Object / process group); Yamakan@c1786105 `core/process/owner.ts:30-97` (hashed engine-worker profile) | **REFERENCE only** | Owners stay Handy and VoiceStudio (M5). Yamakan is GPL |
| Network egress | Ninerr@8cba15c4 `packages/network-policy/src/policy.ts:25,119,167` (WeakSet-issued decisions, `evaluateUrl`, `evaluateResolved`). **SafeEvidence@f05bc006** `product/deny.toml:31-41` (bans reqwest/ureq/hyper/hf-hub), `tools/ci/core_no_sockets.py` (socket-crate denial per target), `tools/ci/ta03_isolated.sh` (Linux `unshare -n`, macOS `sandbox-exec`; Windows uses a firewall-rule variant that the script itself labels "WEAKER"), `tools/ci/network_trace_report.py` (strace socket report) | Ninerr: REFERENCE now, Python port later for Klaint connectors (S5). **SafeEvidence gates: ADAPT now** | SafeEvidence gives exactly the observed-egress and dependency-denial proof that S5 asked for. Its own docstrings state its limits ("does not detect a socket opened through `std::net`") |
| Release/model-pack binding | SafeEvidence@f05bc006 `product/crates/safeevidence-release/src/lib.rs:1-8` (deterministic CycloneDX 1.5 SBOM binding source_sha, tree_sha, Cargo.lock sha256 and model assets; "never claims RELEASE_READY") | REFERENCE (ADAPT at release-packaging time) | Owned by each product's release, not Core runtime |
| Local IPC auth | Orcel@f0b78e65 `crates/orcel-platform/src/peer.rs:68,113` (same-user kernel peer identity; Linux pidfd, macOS audit token) and `acl.rs` (Windows DACL judging). `crates/orceld/src/app_api.rs:7-40` (named pipe with protected DACL, `FILE_FLAG_FIRST_PIPE_INSTANCE`, `PIPE_REJECT_REMOTE_CLIENTS`, client token-user check) | peer/process/acl: ADAPT. **app_api.rs: REFERENCE ONLY. Its header is `SPDX-License-Identifier: FSL-1.1-MIT` with Cua AI third-party portions (line 1), so the founder's grant cannot cover it** | Rights finding. Three Orcel files carry FSL-1.1-MIT: `orceld/src/app_api.rs`, `orcel-approval/src/{linux,presence_unix}.rs` |
| Local HTTP auth (when HTTP is unavoidable) | Ninerr@616bafaa `packages/studio-host/src/server.ts:86-88,445-468` (127.0.0.1 only; Host must name this host:port; foreign Origin refused; per-launch 32-byte token compared with `timingSafeEqual`; single-use launch ticket redeemed only with a same-origin POST) | ADAPT (pattern, Apache-2.0) | Yamakan `core/launch.ts` (60 s launch secret in a 0600 file) is the same idea under GPL, so REFERENCE |

### 2.2 Rust crate scope

- `wispral-contracts`: serde types with `deny_unknown_fields`, one per schema. JSON Schema files are the normative source. Types are tested against `fixtures/cases.json`. Dependencies: serde and serde_json only. Validating schemas in Rust is a **dev-dependency/CI concern**. Any Rust JSON Schema crate must have its default features checked; if they pull an HTTP client, the cargo-deny ban (below) must fail the build. This was not inspected here (NOT_RUN).
- `wispral-policy` (ADAPT from Sentrdel):
  - `Verdict` and `compose`;
  - `validate_narrowing(base, layer)` and `compose_layers`;
  - `UndecidableResolution` and `resolve(kernel_floor, verdict, resolution)`;
  - a product-supplied, data-only kernel floor (deny-list of invariant IDs);
  - a generic `bounded_json::preflight(raw, Limits)`.

  No regorus, no I/O, no async, no network.
- `wispral-journal` (COPY of `orcel-journal` at `f0b78e65`, renamed, notice preserved): optional, for products that need a local intent journal (WisprSide delivery, Studio export commit). Klaint uses its database ledger with the same state table.
- Explicitly **not** in Core: process supervision, IPC servers, credential stores, model download, telemetry.

### 2.3 Python access

Recommendation: a **pure Python port** of `wispral-policy`'s lattice. It is about 80 lines (`compose`, `validate_narrowing`, `resolve`, `preflight` via a bounded tokenizer or a strict `json` hook with size/depth guards). It must be gated by the identical fixture file in CI, the same rule the Opus review set in S2. PyO3/maturin stays the fallback if the port drifts. A binding adds a Rust toolchain and wheel matrix to Klaint's single-Python-service CI for under 200 lines of logic. Python validates the contracts with `jsonschema` (Draft 2020-12), as the existing runner already does. Decision rule: if two consecutive contract majors need more than trivial port changes, switch to PyO3 abi3 wheels.

---

## 3. Review of the drafted contracts against donors

Baseline: `python -I docs/engineering/contracts/run_conformance.py` gave `PASS`, 7 schemas, 33 cases, 0 failures (jsonschema 4.26.0, Python 3.14.7), REPRODUCED. This proves only that the drafts match their own fixtures.

Gap probe (`scratchpad\core\gap-probe.txt`): 25 instances that donor semantics say should be rejected or behave differently. **23 were ACCEPTED by the drafts** (REPRODUCED). G-CAN-1/1b show the opposite problem: the draft over-restricts. Items marked "runtime" cannot be expressed in JSON Schema without `$data`, so they belong in the Rust/Python conformance code.

### 3.1 `envelope.schema.json`

1. **G-ENV-1/2 (accepted):** `principal_scope` is not discriminated.
   - Require `os_session` when `kind=desktop_user`.
   - Require `account_ref` and `channel` when `kind=tenant`. The architecture says customer workloads bind tenant, account and channel.
2. **G-ENV-3 (accepted):** `payload` is an unbounded object. Add `maxProperties`. Also state normatively that a `bounded_json` preflight (Sentrdel `bounded_json.rs:55` semantics: depth ≤ 32, nodes, string bytes, total frame bytes ≤ 1 MiB for worker frames) runs **before** schema validation. A schema cannot bound bytes.
3. **G-ENV-4 (accepted):** `consent_epoch` is optional. Make it required for `RenderRequested`, `RenderOutcome` and any `voice_render` path via `if/then`.
4. **G-ENV-5 (accepted):** `source.artifact_digest` is optional. Require it when `component` is a worker. Ascout's descriptor ties authorization to `artifact_sha256`, so a changed binary or model must invalidate the event.
5. Add `turn_id` (the architecture names request, session and turn). Change `policy_version` to a digest (`^sha256:`) or `name@semver`, so equal strings mean equal policy. Add events `EffectIntentRecorded` and `EffectIntentSettled` (see §3.8).

### 3.2 `cancellation.schema.json`

1. **G-CAN-1b (rejected, over-restrictive):** a crashed worker (`state=failed`, `observation=process_exit`) can never release its lease, which is a guaranteed lease leak. Allow `lease_released=true` when `state ∈ {observed_stopped, completed_before_cancel}` **or** (`state=failed` and `observation=process_exit`). Exit observed by the owner is an observed stop, per Sentrdel `process_tree.rs` drain-after-exit semantics.
2. **G-CAN-2 (accepted):** `acknowledged` may carry a stop observation. Restrict `observation` to `none` in `requested` and `acknowledged`.
3. **G-CAN-3 (accepted):** the boolean `external_effect_committed` cannot say "unknown". Replace it with `effect_state ∈ {none, committed, unknown}` aligned with orcel-journal `Unknown` (`lib.rs:213`). `unknown` must point to a reconcile intent ID.
4. Add `response ∈ {pending, cancelled_result, error_request_cancelled, completed_result}` for the ACP 5.0 rule that one response always arrives (`cancellation.rs:144`), and `cancel_epoch` (the epoch advanced to).
5. Add `process_instance {pid, start_generation}` from Orcel `process.rs:40`, so an escalation kill can never target a reused PID.
6. The state machine is a sequence property. Ship `transitions.json` (allowed `from → to`) and enforce it in runtime conformance, the same way `IntentState::may_become` is enforced.

### 3.3 `model_manifest.schema.json` (compared with Ascout `EngineDescriptorV1`)

1. **G-MM-1 (accepted):** a provider-managed artifact (no digest) can claim `offline_capable=true` with runtime `ggml`. Add `if artifact has provider_managed_digest_unavailable then offline_capable=false`.
2. **G-MM-2 (accepted):** duplicate or contradictory language rows. A runtime uniqueness check on `(code, variety)` is required, because JSON Schema `uniqueItems` compares whole objects.
3. **G-MM-3 (accepted):** there is no authority ceiling. Add these from Ascout:
   - `effect_classes` and `authority_ceiling` (for example, a TTS model may produce only `audio_artifact`; it never confers delivery or tool authority);
   - `requirements {process_required, network_required, sandbox_required}`;
   - `admission_state ∈ {pending, admitted, rejected, revoked}`, kept separate from the license strings;
   - `qualification_evidence_refs[]` and `known_limitations[]`.
4. `artifact` is a single file. Real models are multi-file (weights, tokenizer, config). Use `files[] {path, sha256, size_bytes}` plus a canonical `bundle_sha256`, and add `config_sha256`. SafeEvidence's release SBOM binds model assets the same way.
5. Add `source_revision` (commit or hub revision) next to `source_url`, and `acquisition ∈ {pre_staged, user_imported}`. Auto-download must not be representable.
6. Use `additionalProperties:false` at every level (already present) **plus** a canonical key order for hashing the manifest itself. Ascout requires canonically ordered effect lists (`engine-descriptor.ts:177`).

### 3.4 `consent_record.schema.json`

1. **G-CON-1 (accepted):** `valid_from: "not-a-date-at-all"` is accepted. Use a strict RFC 3339 UTC `pattern`. `format` is annotation-only unless a format checker is enabled.
2. **G-CON-2 (accepted):** `status=expired` without `valid_until`. Require it.
3. **G-CON-3 (accepted; runtime):** `valid_until < valid_from`.
4. **Privacy:** `subject.display_name` puts personal data into a contract that also appears in provenance. Replace it with an opaque `subject_ref`; keep display data in the product store.
5. Make revocation append-only. The record should be a projection over `consent_granted` / `consent_revoked` provenance events (SafeEvidence proofstore refuses UPDATE/DELETE by trigger). `consent_epoch` must strictly increase on each revocation (runtime).
6. Add the missing scope fields:
   - `principal_scope_ref` (Studio project owner or Klaint tenant);
   - `products[]` (`wisprstudio`, `klaint`);
   - `allowed_engines[]` (model_ids);
   - `watermark_required` (bool; VoiceStudio has watermarking, ST-WATERMARK).

### 3.5 `policy_verdict.schema.json` (compared with Sentrdel)

1. **Semantic conflict:** the draft says "every consumer treats UNDECIDABLE as DENY". Sentrdel's default is `UndecidableResolution::Ask` (`lib.rs:130`), and either is safe because there is no Allow. Split the record:
   - `candidate_decision` (may be `UNDECIDABLE`);
   - `enforced_decision ∈ {ALLOW, ASK, DENY}` (never UNDECIDABLE);
   - `undecidable_resolution ∈ {ASK, DENY}`, with DENY required when no human is present (Klaint unattended, telephony).

   **G-POL-3 (accepted):** UNDECIDABLE is currently accepted as the final record.
2. Add `layers[] {source ∈ base|product|tenant|repository|user, decision}` and `kernel_floor_ids[]`. Runtime conformance must prove monotone narrowing (`validate_repository_narrowing`, `narrowing.rs:58`): a layer may only move up ALLOW < ASK < DENY, and an empty layer list equals UNDECIDABLE (`compose_verdicts`, `lib.rs:147`).
3. **G-POL-1 (accepted):** `ALLOW voice_render` without a rule or consent. Require `rule_ids.minItems:1` **and** an `evidence` item with `kind=consent_record` whenever the voice is not a stock voice.
4. **G-POL-2 (accepted):** `ALLOW text_delivery` backed only by `model_confidence`. Add `text_delivery` to the classes that need a rule. Evidence is never sufficient by itself (runtime rule: if no `rule_ids`, `enforced_decision` ≠ ALLOW for any non-`read` class).
5. Bind against replay with `request_id`, `epoch` and `consent_epoch`.

### 3.6 `provenance_event.schema.json` (compared with orcel-audit, orcel-journal and the SafeEvidence proof manifest)

1. **G-PROV-1 (accepted):** `raw_hypothesis.model.artifact_sha256` is optional. Make it required; the Opus S6 review requires the model ID and digest in every provenance event.
2. **G-PROV-2 (accepted):** `outcome` has no parent and no `policy_version`. Add `outcome` and `policy_verdict` to the parent-required kinds. Add `policy_version`, which orcel-audit already records as `policy_revision`. Add `intent_state` for `dispatch` and `outcome`, using orcel-journal states.
3. **G-PROV-3 (accepted):** `bounded_days` has no `retention_days`. Require it.
4. Add `principal_scope_ref`, which is mandatory for Klaint tenant partitioning, and `journal_seq`. Optionally add `prev_digest` if tamper-evidence is required. Note that orcel-audit's `flush` is not fsync; orcel-journal's `sync_data` is.
5. For `rewrite_suggestion` and `interpretation`, add `components {prompt_digest, policy_version, thresholds}`, following SafeEvidence `ProofComponents` (`proof.rs`), so that "what shaped this text" can be reproduced.

### 3.7 `delivery_outcome.schema.json`

1. **G-DEL-1/2 (accepted; runtime):**
   - `chars_delivered ≤ chars_total`;
   - `delivered_confirmed` requires `chars_delivered = chars_total`;
   - `partial` requires `1 ≤ chars_delivered < chars_total`.
2. **G-DEL-3 (accepted):** `clipboard.used=false` with `restored=true`. Add `if used=false then restored=false, skipped_reason=not_used`.
3. **G-DEL-4 (accepted):** `process_start_time` is free text ("yesterday" passes). Replace it with `process_instance {pid, start_generation:uint64}`, using the Windows FILETIME creation time (Orcel `process.rs`, `GetProcessTimes`).
4. Add an `unknown` outcome (a crash between injection and confirmation is reported at restart as orcel-journal `Unknown`), plus `intent_id`.
5. Add refusal reasons `os_session_changed`, `secure_desktop`, `focus_lost` and `stale_epoch`. Add `epoch_at_activation`, with a runtime check: if it is not equal to `epoch`, the outcome must be `refused/stale_epoch`.

### 3.8 Missing eighth contract: `effect_intent`

One generic external-effect record is needed for the Klaint broker, the Studio export commit and Side delivery:

- `intent_id`;
- `idempotency_key`;
- `owner`;
- `action_class`;
- `state` (orcel-journal six states, plus a `transitions.json` table copied from `may_become`);
- `reconcile_probe`;
- `verdict_id`.

`delivery_outcome` then becomes the WisprSide detail payload for `action_class=text_delivery`. Without this contract, "unknown external outcome, reconcile, never blindly retry" (architecture replan) has no shared shape.

### 3.9 Conformance fixture layout (runnable from Rust and Python)

```text
contracts/
  v1/*.schema.json                      # normative; $id under .invalid
  v1/transitions/{cancellation,effect_intent}.json   # allowed from->to
fixtures/
  shape/cases.json                      # existing: {schema, name, expect, instance}
  shape/tamper/*.json                   # one file per gap ID (G-ENV-1 ...), expect=invalid
  runtime/cases.json                    # checks not expressible in schema
                                        # (chars bounds, date order, uniqueness, epoch equality)
  sequences/cancel/*.jsonl              # ordered events + expected final state + lease rule
  sequences/effect_intent/*.jsonl       # incl. crash-after-dispatch -> unknown -> reconciled
  policy/lattice.json                   # exhaustive 4^n sequences n<=4 (Sentrdel test style,
                                        # narrowing.rs tests) -> expected compose/narrow/resolve
  bounded/{deep,wide,longstring,oversize,trailing,non_utf8}.bin  # expect reject
runners/
  python: run_conformance.py (exists) + run_runtime.py + run_policy.py (port)
  rust:   tests/conformance.rs reading the same files (serde types + wispral-policy)
CI: both runners must emit identical {case -> verdict} JSON; diff must be empty.
```

---

## 4. One owner per responsibility

Rows are responsibilities; columns are owners per product. "Core" never runs anything: it owns only the contract and fixtures.

| Responsibility | WisprSide | WisprStudio | Klaint | Core |
| --- | --- | --- | --- | --- |
| Process lifecycle | Handy `engine_supervisor` (cjpais/Handy@93c9ee0 `src-tauri/src/engine_supervisor/supervisor.rs`, INK-I10; prior SOURCE_VERIFIED) | VoiceStudio `backend/core/contained_subprocess.py` + `backend/services/subprocess_backend.py` (debpalash/VoiceStudio@28bf2c7, ST-SIDECAR) | Klaint Python service host (container/process manager); Pipecat owns only pipeline tasks | `cancellation` contract and `process_instance` format (Orcel `process.rs` ADAPT). ContainedChild and Yamakan procd are REFERENCE |
| Cancellation | Handy `transcription_coordinator.rs` maps to Core states. Model load is not cancellable at the pin, so report `stopped_unconfirmed` | `inference_cancellation.py` (ST-CANCEL-SCOPE) maps to Core states | Parlant/Pipecat cancel is treated as an observation; the broker owns effect state | State set and transitions (ACP 5.0 + orcel-journal) |
| Authoritative model inventory | Handy model manager (fork) emits `model_manifest` rows | VoiceStudio `model_acceptance.py` store (ST-MODEL-TERMS); `model_lifecycle.py` is a facade | Tenant-scoped provider/model config registry in the Klaint DB | Schema and validator (Ascout descriptor ADAPT); no store |
| Voice-asset consent ledger | N/A: no voice cloning; dictation audio is `audio_not_persisted` by default | VoiceStudio `api/routers/profiles.py` consent (ST-CONSENT), the sole desktop ledger | Klaint tenant consent table, only if custom voices are enabled (default: stock voices only) | `consent_record` schema and revocation semantics |
| Tenant identity | Local OS user + OS session (`desktop_user`) | Local OS user (`desktop_user`) | Klaint authenticated server context (`tenant_authorization.py`, K12); IDs inside customer text never select a tenant | `principal_scope` shape only; no identity provider |
| External side effects | Delivery transaction (Handy `paste_tx` fork delta, INK-I4/I5) with a `wispral-journal` intent | Export/render commit (VoiceStudio longform render, ST-RENDER) | Deterministic broker (`brokered_tool_service.py`, K03) with an idempotency ledger | `effect_intent` contract + `wispral-journal` (COPY orcel-journal) |
| Network egress policy | Offline by construction: SafeEvidence-style dependency denial + OS-observed egress test (ADAPT `ta03_isolated.sh`, `core_no_sockets.py`) | URL ingest disabled; analytics off; model fetch only by explicit user import | Connector transport with Ninerr policy fixtures (Python port, deferred per S5) and DNS/redirect pinning | CI gate scripts and fixtures only |
| Update channel | Handy fork's existing updater (not inspected this pass, NOT_RUN); signed and pinned | VoiceStudio Electron update path (not inspected, NOT_RUN); engines and models updated only by manifest digest | Container image tags via the deploy pipeline | Contract semver; release SBOM pattern (SafeEvidence `safeevidence-release` REFERENCE) |
| Telemetry | Off by default (inherit Handy setting; to verify) | Off: `backend/core/analytics.py` default-off (prior DOCUMENTED; runtime proof missing) | Operator metrics self-hosted per tenant; no vendor SaaS | None. Provenance events are not telemetry |

Donor key: Handy (MIT), VoiceStudio (AGPL-3.0 plus founder grant), Parlant/Pipecat (Apache-2.0 / BSD-2), Orcel (Apache-2.0, except FSL files), Sentrdel/Ascout/Ninerr/SafeEvidence (Apache-2.0), Yamakan (GPL, reference only).

---

## 5. Other founder repositories (brief)

| Repo @ HEAD | What it is (DOCUMENTED unless noted) | Verdict |
| --- | --- | --- |
| **SafeEvidence @f05bc006** | Local-first clinical evidence workstation; Rust product workspace + CI egress gates | **CANDIDATE** (material): `product/deny.toml:31-41`, `tools/ci/{core_no_sockets.py, ta29_dependency_denial.py, ta03_isolated.sh, network_trace_report.py}` (ADAPT for WisprSide offline proof); `safeevidence-proofstore/src/lib.rs` (append-only pattern, REFERENCE); `safeevidence-release/src/lib.rs` (SBOM binding, REFERENCE); `safeevidence-contracts/src/proof.rs:129` `commit_defects` (fail-closed commit gating pattern, REFERENCE) |
| **Orcel @f0b78e65** | Local MCP authority daemon | **CANDIDATE**: `crates/orcel-journal/src/{lib,resume}.rs` (COPY); `crates/orcel-platform/src/{process,peer,acl}.rs` (ADAPT, keep the Cua MIT notice); `orceld/src/app_api.rs` REFERENCE only (FSL-1.1-MIT third-party) |
| Ninerr @616bafaa | Local-first design workspace | **CANDIDATE** for the local HTTP auth pattern `packages/studio-host/src/server.ts` (ADAPT); policy stays REFERENCE |
| Other private founder repositories (names and contents withheld from this public repository) | Screened by name, README and tree on 2026-11-08 | **REJECTED**: none contains a Wispral-relevant module; one second agent framework and several unrelated applications or document-only planning repositories. Details are available to the founder on request and are not published here |
| Zain @0a843a2c | Renamed WePLD; README states `IMPLEMENTATION = NOT_STARTED` | REJECTED. Re-key the catalog entry wepld → Zain |
| Hala @00f66923 | Bootstrap for the Aladdin Pro intelligence system; training evidence on branches | REJECTED (model training; out of scope) |
| Skilit @157ace7f | Design intelligence; capture-scope files unchanged | Keep CORE-SCOPE as REFERENCE |
| SpecGrain, Diffcipline, commandF, Morize | Unchanged since prior pins | Keep prior verdicts (governance REFERENCE / NOT_SELECTED) |
| Gomrey @5f299a7a | Evidence-grounded creation platform; no TTS/voice paths in the tree | REJECTED |
| paradigm @4de95147 | Research HQ for Plume (video) and Hala | REJECTED |
| AbdulazizShehri | Only public MedOrigin, MedScale and safeOCR are listed to this token; prior private repos are not listed | **BLOCKED_EXTERNAL** for private ones. Nothing Wispral-relevant in the visible ones |

---

## 6. SDK and API strategy

The principle: **no unauthenticated listener, ever, by default.** ACP's HTTP transport has no built-in auth ("CORS does not authenticate requests", rust-sdk@050cd94c `agent-client-protocol-http/src/server.rs:66`, SOURCE_VERIFIED), so ACP stays on stdio.

| Product | Initial surface | Later surface | Auth |
| --- | --- | --- | --- |
| WisprSide | CLI (Handy `cli.rs` in the fork) for status, diagnostics and transcribe-file; no network listener | (1) Local IPC: Windows named pipe `\\.\pipe\wispral-side-<SID>` with a protected DACL, first-instance, `PIPE_REJECT_REMOTE_CLIENTS` and client token-user/session checks; macOS/Linux UDS 0600 in a 0700 dir with kernel peer-cred check (Orcel `peer.rs`/`acl.rs` ADAPT; `app_api.rs` design REFERENCE only). (2) MCP **stdio** server spawned by the agent client; read-only tools plus "insert text" gated by the delivery policy | OS identity of the peer; never a token in a URL |
| WisprStudio | CLI batch render/export + existing in-app UI | Python/TS SDK over the local API; MCP stdio wrapper | If the retained VoiceStudio backend listens on localhost HTTP (to verify in F-STUDIO-0; NOT_RUN), apply the Ninerr studio-host profile: 127.0.0.1 only, Host allow-list, foreign-Origin refusal, per-launch 32-byte token with constant-time compare, single-use launch ticket, token never in a query string except the SSE stream |
| Klaint | Server HTTPS API + signed webhooks (HMAC over exact bytes; reject non-finite, future or stale timestamps; replay cache) | Python/TS SDK; remote MCP with OAuth scopes (pattern from a private founder repository, REFERENCE) | Tenant-scoped OAuth/API keys bound server-side; customer text never selects tenant or credentials |
| Core | No service. Publishes `contracts/vN`, `wispral-policy`, `wispral-contracts`, `wispral-journal` and fixtures | Generated TS/Python types from the schemas | n/a |

Versioning:

- `schema_version` (major) is in every record.
- Additive optional fields are a minor bump. Tightening, removing or renaming is a major bump with migration notes and both majors' fixtures kept.
- Products pin one major. Readers accept N and N-1 for one release; writers emit only N.
- Local APIs are versioned by path or name (`wispral-side-app/1`, after Orcel's `orcel-app-api/1`).
- Breaking changes to a local API require a new name. Never silently re-interpret.

---

## 7. What must be built new, and why

| New item | Justification against inspected sources |
| --- | --- |
| Wispral contract schemas (8, including `effect_intent`) | No donor models voice consent, dictation target identity or a cross-product epoch envelope. Donors supply field vocabularies (Orcel, Ascout, Sentrdel, SafeEvidence), which is why these are thin NEW |
| Generic bounded-JSON dialect | Sentrdel's preflight is hard-wired to SARIF/native contexts (`bounded_json.rs` `Context` enum) and leaves byte capping to the caller (`adapter.rs:38`). The ADAPT needs about 150 new lines and new limits |
| Runtime (non-schema) conformance checks and sequence fixtures | JSON Schema cannot express ordering, bounds between fields, epoch equality or transition legality (G-DEL-1/2, G-CON-3, cancellation sequences) |
| Python port of the lattice | No Python donor; Sentrdel is Rust. Small and fixture-gated |
| Windows-strength egress observation | SafeEvidence's Windows TA-03 path is self-described as weaker (named-program firewall rules only). WisprSide-on-Windows needs its own observed-egress design: ETW/WFP audit or a per-binary firewall block with a positive control. **No donor solves this fully** |
| Not new: supervisor, journal, policy lattice, network policy, SBOM, local IPC auth | Copied or adapted from Handy/VoiceStudio, orcel-journal, Sentrdel, Ninerr, SafeEvidence and Orcel platform |

---

## 8. Core work packets

Note: draft packet IDs collide. `WISPRAL_PRODUCT_ARCHITECTURE.md` §3 uses PL-03 = Python access and PL-04 = manifests; `WISPRAL_PRODUCT_VISION.md` uses PL-03 = manifest and PL-04 = design tokens. The mapping below uses CORE-* IDs. Reconcile before adoption.

Every packet's CI gates are:

- the shape runner;
- the runtime runner;
- Rust/Python verdict-diff = empty;
- `cargo deny` with SafeEvidence-style bans;
- a socket-crate denial check on Core crates;
- `cargo fmt`/`clippy -D warnings`;
- notices present for every copied file.

| ID | Depends on | Donor + SHA + path | Decision | Files affected (proposed) | Acceptance / tests | Risks | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CORE-00 Re-pin and rights | none | Orcel `f0b78e65`; SafeEvidence `f05bc006`; ACP rust-sdk `050cd94c` (5.0.0); Yamakan `c1786105` (ref); Ninerr `616bafaa` | ADMIN | `research/.../source-transplants.json` rows CORE-AUDIT→CORE-JOURNAL, CORE-ACP/CANCEL re-anchor; catalog wepld→Zain; rights register (FSL files; Yamakan GPL; **Wispral repo has no LICENSE**, `gh api` license = none) | Every new anchor's blob and sha256 re-verified; founder records the Wispral outbound license before any COPY | License incompatibility discovered late | Revert the registry commit |
| CORE-01 Contract corrections v1→v2-candidate | CORE-00 | Sentrdel `lib.rs:130,147,203`; Ascout `engine-descriptor.ts:45`; orcel-journal `lib.rs:213`; Orcel `process.rs:40` | ADAPT (schemas) | `docs/engineering/contracts/*.schema.json`, `fixtures/shape/tamper/*` | All 25 gap probes yield the intended verdict (23 newly rejected; G-CAN-1b accepted); existing 33 cases are still correct or explicitly migrated | Over-constraint breaks product adapters | Keep v1 files; v2 lives in its own directory |
| CORE-02 `effect_intent` contract + `wispral-journal` | CORE-01 | Orcel@f0b78e65 `crates/orcel-journal/src/{lib.rs,resume.rs}`, `Cargo.toml` (fs4, serde, serde_json) | **COPY** crate byte-for-byte + rename layer; notice | `crates/wispral-journal/`, `contracts/v2/effect_intent.schema.json`, `transitions/effect_intent.json` | Upstream tests pass unchanged; crash-after-dispatch sequence becomes `unknown` then `reconciled`; torn-tail and oversize fixtures | Behaviour of fs4 locking on network drives | Drop the crate; products keep a DB ledger |
| CORE-03 `wispral-policy` lattice | CORE-01 | Sentrdel@f5747319 `crates/sentrdel-policy/src/{lib.rs:125-221, narrowing.rs:58-100}`, `sentrdel-schema/src/policy.rs:13` | ADAPT (drop regorus/schemars; data-only kernel floor) | `crates/wispral-policy/src/{verdict,narrowing,resolve}.rs` | Exhaustive 4^n (n≤4) sequences match Sentrdel's own tests (port `for_each_verdict_sequence`); no-widening property; empty input = UNDECIDABLE; resolution never yields ALLOW | Semantics drift from donor | Pin to the donor test vectors; revert the crate |
| CORE-04 Generic bounded preflight | CORE-03 | Sentrdel `crates/sentrdel-engine/src/bounded_json.rs:8-13,55` | ADAPT | `crates/wispral-policy/src/bounded_json.rs`, `fixtures/bounded/*` | Deep, wide, long-string, oversize, trailing and non-UTF-8 fixtures rejected before serde; frame limits documented per product | Limits too tight for Studio payloads | Per-product `Limits` config |
| CORE-05 Python parity | CORE-03, CORE-04 | (no donor) | NEW port, about 80 lines; PyO3 fallback | `python/wispral_policy/`, `runners/run_policy.py` | Byte-identical verdict JSON vs Rust over all fixtures in CI | Port drift | Switch to PyO3 abi3 |
| CORE-06 Manifest alignment | CORE-01 | Ascout@48902389 `engine-descriptor.ts:45-58,147-177`; VoiceStudio `model_acceptance.py` (prior pin) | ADAPT | `contracts/v2/model_manifest.schema.json`, adapters spec for Side/Studio exporters | Studio and Side exporters each emit ≥1 valid manifest for a qualified model; digest change invalidates prior authorization (fixture) | Multi-file bundle hashing disagreements | Keep the v1 single-artifact form for one release |
| CORE-07 Egress gates for WisprSide offline | CORE-00 | SafeEvidence@f05bc006 `product/deny.toml:31-47`, `tools/ci/{core_no_sockets.py, ta29_dependency_denial.py, ta03_isolated.sh, network_trace_report.py}` | ADAPT | `tools/ci/side_no_sockets.py`, `deny.toml` in the Handy fork and Core crates, Windows observed-egress job | Positive control reaches the network first; under isolation, the full PTT session shows zero non-loopback connects; the denial lists catch an injected `reqwest` dependency (tamper-negative) | Windows path weaker than Linux/macOS (donor's own label) | Gate is advisory until the Windows design qualifies |
| CORE-08 Local API auth profiles | CORE-00 | Orcel@f0b78e65 `crates/orcel-platform/src/{peer.rs:68,113; acl.rs; process.rs}`; Ninerr@616bafaa `packages/studio-host/src/server.ts:86-88,445-468` | ADAPT (Orcel `app_api.rs` design REFERENCE only, FSL) | `docs/engineering/LOCAL_API_AUTH.md`, `fixtures/local_api/*` | Negative tests: other-user client, remote pipe client, wrong Host, foreign Origin, missing/replayed launch ticket, PID-reuse peer; all refused before any byte is read | Platform API differences | Ship CLI-only until it passes |
| CORE-09 Cross-runtime cancel conformance | CORE-01, CORE-02 | ACP rust-sdk@050cd94c `concepts/cancellation.rs:7,144`; product owners (Handy, VoiceStudio, Klaint) | NEW harness (fake worker) | `fixtures/sequences/cancel/*`, per-product adapters | Cancel at load, mid-inference, after commit and crash: identical Core transitions, zero orphans, lease released only on observed stop or exit | Fake-pass ≠ native stop proof | Report `stopped_unconfirmed`; no lease release |
| CORE-10 (deferred, Klaint) Connector egress | Klaint broker | Ninerr@8cba15c4 `packages/network-policy/src/policy.ts:25,119,167` + `tests/network-policy.test.mjs` | ADAPT to Python | `services/klaint/connectors/egress.py` | Prior 6/6 synthetic fixtures + DNS-pinning and redirect fixtures pass in Python | DNS rebinding | Disable outbound connectors |

---

## 9. Open items and limits

- **NOT_RUN:**
  - Sentrdel, Orcel and SafeEvidence test suites;
  - any Rust build;
  - egress isolation;
  - Handy/VoiceStudio updater, telemetry and local-API inspection (§4, §6);
  - the ACP 5.0 runtime trial;
  - Code of two private, unrelated founder repositories.
- **BLOCKED_EXTERNAL:** AbdulazizShehri private repositories are not listed to the current token. Branch-protection status was not attempted, because it is read-only out of scope.
- **Rights:**
  - The Wispral repository has no LICENSE file, so outbound terms are undecided.
  - Three Orcel files are FSL-1.1-MIT third-party code.
  - Yamakan is GPL-3.0-or-later combined with third-party GPL.
  - Copy nothing from these without founder and legal decisions; none is required by the packets above.
- The draft contracts are good scaffolding. The probe shows they currently prove shape only and admit 23 donor-inconsistent records. CORE-01 must land before any product consumes them.
- The `wcore` junction in `%TEMP%` pointing to `scratchpad\core` was created during acquisition and is removed at the end of this task (the link only).
