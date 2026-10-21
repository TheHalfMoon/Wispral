# Wispral platform architecture replan

Status: **PROPOSED — RESEARCH ONLY**, 2026-10-21. This plan follows the [source studies](../../research/rea/2026-10-21/README.md) and [75-record source matrix](../../research/rea/2026-10-21/SOURCE_TRANSPLANT_MATRIX.md). It does not replace the active constitution, canonical architecture, specification frontier or 000G gate. Final founder names: **Wispral / WisprStudio / WisprSide / Klaint**.

Wispral Core is shared versioned contracts, a small optional embedded policy library and conformance fixtures, not a mandatory cross-product daemon. Each product has one local authority owner appropriate to its deployment. WisprSide provides cross-application dictation and optional developer-agent control. WisprStudio provides generation, timeline/editing, long-form rendering and dubbing. Klaint provides bounded customer dialogue, tools, channels and human handoff. Each surface can ship on its own qualified capability manifest; no user must install every engine or open an account to use the local core.

## Donor-led structure — repaired boundary selection

The [pinned fork comparison](../../research/rea/2026-10-21/FORK_BOUNDARY_COMPARISON.md) supersedes extraction-first application assembly. Retain the coarsest compatible existing boundary; extract pure leaves only when they simplify qualification. Fork adoption is conditional on recorded baseline builds/tests and deltas, currently NOT_RUN.

| Product/boundary | Selected reuse and exact source | Exclusion / qualification |
| --- | --- | --- |
| WisprSide | Pinned Handy fork 93c9ee05efe294cf2a56bd534b77ea1079f21b77, retaining Tauri/UI/settings/history/install/capture/paste/supervisor | No new Core crate required to build a baseline. Fix exact-target/context authority; Handy model loads are not cancellable at this pin, so add/test a bounded cancellation delta or report stopped-unconfirmed |
| WisprStudio | Pinned VoiceStudio fork 28bf2c7a83b8a64836297340c52a45d716684aed, retaining project/timeline/render/resume/consent/engine integration | Keep analytics OFF (manifest already documents default-off; runtime proof missing), disable URL ingest, stage only qualified engines/assets. Existing in-process paths are not magically isolated |
| Klaint | Parlant ea737442b8ae65854a842542e544fbe7e6144bad wrapped in one Python service, with deterministic broker, canned responses, retrievers and evaluations | No mandatory Rust process hop, Node connector host or copied Rails inbox. Optional Chatwoot is unmodified through API/webhooks |
| Core library/contracts | Sentrdel pure policy/bounded-input, ACP schemas, source/consent/cancel envelopes and fixtures | Embed where useful. Python binding or qualified equivalent consumes same verdict fixtures; no duplicate deployment-wide supervisor |
| Voice composition | Pipecat 9b0459b47675324843ffea17d90d8d3e422eb92c inside Klaint's Python service when voice is authorized | LiveKit Agents is REFERENCE_ONLY. Pipecat transports may use LiveKit/WebRTC/SIP bridges without adding a second session controller |

## One owner per responsibility

| Responsibility | Sole owner within its runtime | Mapping and conformance |
| --- | --- | --- |
| Side model process subtree | Handy engine_supervisor; recorder owns only its device handle | INK-I10 is a fork delta, not another Core supervisor; Core-PROCESS is fallback/reference only. Cancel-at-load limitation must remain visible |
| Studio backend/engine subtrees | Existing VoiceStudio containment/backend hierarchy; one parent per distinct child subtree | Keep contained_subprocess + SubprocessBackend/job registry relationships; do not put Sentrdel or Handy around those same children. Selected in-process engines need explicit stop limitations or a qualified existing sidecar path |
| Klaint service/process | Its Python service host; Pipecat owns only session pipeline tasks | No independent model supervisor copied from desktop donors |
| Cancellation semantics | One Core state contract; runtime owner performs stop/escalation and reports observations | request → ack → stopped/completed-before-cancel/stopped-unconfirmed; no lease release merely on ack |
| Model inventory | One shared schema and one implementation/store per product deployment | Side's model manager and Studio model_acceptance implement the same identity/terms/consent contract. Studio model_lifecycle is a facade, not a second inventory. No shared global DB required across desktop and tenants |
| External side effects | Side delivery transaction; Studio export commit; Klaint deterministic broker, respectively | Each request has one commit/unknown-outcome owner. Retrievers/LLMs/Plan hooks cannot authorize connector mutations |

Cross-runtime acceptance: identical cancel-state fixtures at load, mid-inference, after completion/commit and crash; zero orphan children; stale epochs rejected; memory/accelerator leases released only after observed stop. A fake contract passing is not native stop proof. Global cross-product accelerator scheduling is deferred until a measured multi-product contention requirement exists.

F-SIDE-0/F-STUDIO-0 preserve upstream branches, notices and baseline manifests. DELTA_REGISTER.md records finding → file → fixture → upstream-rebase status → rollback/data migration. No competing realtime framework or new general supervisor is selected.

## Authority and data contracts

Core admits immutable facts separately: raw speech, tentative/final hypotheses, user corrections, normalized text, entity bindings, interpreted intent, target/context snapshot, policy decision, dispatch and observed outcome. A user-facing polished sentence must not erase the raw hypothesis or claim every append-only committed_text field is authoritative: transcribe-cpp's backend semantics differ. Keep provider raw text and committed/draft events distinct until each adapter qualifies them.

Every request/event needs a version, request/session/turn ID, monotonically increasing session epoch, sequence, trusted source identity, event type and payload bound. Customer workloads additionally bind tenant/account/channel; desktop delivery binds OS session plus captured target identity, process incarnation and context-consent epoch. A provider/model artifact digest, configuration digest and relevant policy/consent version invalidate stale work. Timestamps support diagnostics, not authority ordering. IDs supplied in customer text cannot select tenant or credentials.

Proposed envelope shape, to be refined into a bounded contract Grain:

```json
{
  "schema_version": 1,
  "request_id": "synthetic-request",
  "session_id": "synthetic-session",
  "epoch": 7,
  "sequence": 12,
  "principal_scope": "trusted-desktop-or-tenant-reference",
  "source_digest": "sha256:artifact-or-content-identity",
  "policy_version": "qualified-policy-identity",
  "consent_epoch": 3,
  "event": "TranscriptFinal",
  "payload": {}
}
```

These are illustrative fields, not an approved wire schema. Cap frame/string/depth/event rate before decoding; do not log raw media or secrets. Use bounded stdio framing for local workers where possible. No unauthenticated listening local HTTP service as an accidental default. A service topology requiring HTTP must qualify authentication, origin binding, resource limits and tenant scope.

## Cancellation, playback and side effects

Model independent lifetimes for capture, ASR, dialogue, TTS, audible playback, tool dispatch, render and text insertion. Request cancellation advances the session epoch and prevents stale output from becoming active. States must distinguish request sent, acknowledged, observed stopped, completed-before-cancel, failed and stopped-unconfirmed. Do not release worker/model memory leases on acknowledgement alone.

Stop local playback immediately using the qualified audio path. Send the provider's correct request/session cancel and, where needed, truncate unheard audio context. Observe worker exit/idle or native completion; escalate within a preregistered deadline to terminate only the owned process tree. Termination must not target a reused PID. Interrupted action completion remains factual: a committed ticket/refund or partially typed string cannot be undone by deleting an event. Represent unknown external outcome and reconcile through a read/idempotency key rather than blindly retry.

One realtime worker owns a session's turn policy, but Core retains action authority and epoch gating. Pipecat CancelFrame, LiveKit interrupt and Parlant cancellation are adapter observations, not universal external rollback. Deepgram eager endpoint signals may trigger speculative reversible work only; they do not authorize customer mutation.

## Text delivery and contextual rewriting

At activation, capture a bounded target token. Revalidate before every delivery attempt: OS session, target liveness/process incarnation, allowed field/window, foreground/focus state and policy epoch. If identity is unreadable or restoration fails, return a visible blocked result and retain editable text. Do not inherit OpenWhispr's fallback to the current foreground. A clipboard reader receipt is evidence of a reader, not proof of intended-field insertion.

Use one transaction with explicit outcomes: refused, posted-unconfirmed, confirmed-by-qualified-mechanism, partially-posted, failed. Never auto-retry partial delivery. Restore clipboard only if the transaction still owns the clipboard marker/version; preserve a user's intervening clipboard change. Browser/editor/terminal/password/elevated windows require separate fixtures and capability restrictions. Sending Enter/submit is a separate action, never implied by paste success.

App context is optional and narrowly scoped: user-selected text/application metadata first; screenshot acquisition requires distinct explicit consent and visibility. Context is untrusted evidence, never system policy. Sensitive fields/apps default to no capture. FreeFlow's enabled screenshot fallback and remote context payload are not inherited. Keep raw text, edited suggestion and final accepted text separate; numbers, negation, names and code identifiers need meaning-distortion checks and reversible correction.

## Workers, resource scheduling and artifact inventory

Reuse donor lifecycle mechanisms rather than rebuild them. Each deployment has one inventory implementation and resource owner behind the common schema. VoiceStudio already has per-engine subprocess infrastructure and also in-process TTS/ASR/diarization paths; qualify the exact selected engine path, not a blanket isolation claim. Preserve its model_acceptance store and lifecycle facade, removing no consent checks.

Engine requirements conflict: VoiceStudio transformers >=5.10.0, Chatterbox ==5.2.0, Qwen ==4.57.3, CosyVoice ==4.51.3, plus torch/pyannote differences. Reuse retained engine-specific environments where present. Only add a sidecar delta if an admitted engine lacks a technically sufficient existing boundary. Pin mutable dependencies such as resemble-perth before execution. No auto-download, telemetry, URL media input or cloud fallback in offline jobs.

One runtime owner holds each job/resource lease. Bound queues/audio duration/tenant budgets; mark crash/OOM/unknown stop accurately. Resume only digest-valid source/config/artifact/consent state. Voice revocation blocks new/queued work and future cache use. Exact modality/provider contracts are in [WISPRAL_MODEL_ROUTING_CONTRACTS.md](WISPRAL_MODEL_ROUTING_CONTRACTS.md).

## Klaint tools, tenancy and human ownership

Parlant prepares guidelines/context, infers tools and calls ToolService. Inject both a restrictive Plan and brokered ToolService: pre-tool filtering alone cannot guard an alternate invocation path. Workers receive no broad CRM credentials. Resolve tenant/customer/tool capability from authenticated server-side context; bind arguments, policy version, target resource and action class before dispatch. External responses are untrusted input.

Adapt Chatwoot account-scoped assignment and ownership transitions. Human takeover advances the AI epoch and stops future AI sends; bot handoff source without locking is not enough for a race-safe bridge. Store an outcome ledger per idempotency key for mutating connectors. Authenticate webhooks over exact bytes, reject nonfinite/stale/future timestamps within a defined skew, and maintain replay protection. Botpress connector schemas reduce API work; they do not replace tenant authorization or vendor entitlement.

Ship synthetic text dialogue and fake tools before voice or live CRM actions. Telephony is a later optional boundary with recording/retention disclosure, regional routing, verified caller/context rules, transfer failure recovery and an authorized test number. Tenant isolation cannot be inferred from a local desktop process model.

## Persistence, packaging and observability

Use a metadata event journal and product-specific stores behind versioned migrations. Reuse the lead donor's project/resume formats through an adapter before inventing a new project engine. Do not run two Studio databases or duplicate Chatwoot conversation ownership. Human-readable exports preserve input/source/translation/output provenance; media remains outside metadata logs and follows explicit retention.

Initial delivery is a qualified Windows local path with text/keyboard fallback. Keep Core CLI usable for diagnostics and automation; add one optional desktop surface using Handy/Tauri seams only after governance and native tests. macOS accessibility/paste adapters and Linux portals/Wayland require separate platform qualification. Mobile keyboards, background capture and cross-device sync remain distant, separately scoped work. A donor platform badge is not Wispral support.

Release packaging must bind the full binary/native/model closure and notices, disable unselected network/telemetry/download defaults, and verify clean install/update/rollback. No runtime implementation, dependency installation, cloud inference or signed package was produced by this mission. See [master plan](WISPRAL_MASTER_PLAN_REBUILT.md), [work packets](WISPRAL_COPY_FIRST_WORK_PACKETS.md) and [governance proposal](WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md).
