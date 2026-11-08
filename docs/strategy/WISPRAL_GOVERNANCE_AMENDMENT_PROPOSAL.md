# Governance amendment proposal for the broader Wispral platform

Status: **PROPOSAL ONLY — NOT RATIFIED**, 2026-10-21. This research PR does not edit CONSTITUTION.md, AGENTS.md, canonical architecture/roadmap, active specs, trusted controls or benchmark evidence. Founder authorization covers the research/replanning mission and existing source grants; it does not silently declare canonical product readiness.

## Motivation and compatibility impact

The active constitution 0.2.1 describes a voice-native control plane for independent AI coding agents. The founder now selects Wispral as an umbrella platform with WisprSide dictation, WisprStudio production and Klaint customer agents. A platform plan cannot become executable by placing conflicting prose under docs/strategy. Governance requires a dedicated amendment PR describing motivation, compatibility, security/privacy and affected specifications. A major constitutional version is proposed because the primary scope and first surface change incompatibly; final version selection belongs to that amendment review.

## Proposed constitutional wording

| Location | Proposed replacement or addition | Preserved obligation |
| --- | --- | --- |
| Preamble | “Wispral makes voice a trustworthy interface for writing, audio production and independent agent interaction. WisprSide, WisprStudio and Klaint share one authority, provenance and resource core.” | Trust, interoperability, accessibility and open evidence remain primary |
| Principle I | Rename to “Platform and control plane, not compulsory proprietary intelligence.” Replace coding-agent-only primacy with a modular platform around replaceable speech/model/dialogue implementations. A useful local core must not require a Wispral-owned foundation model, coding agent, IDE or hosted reasoning service. | Vendor neutrality; optional coding-agent control remains a supported direction, not removed |
| Principle V | Rename to “Bounded domain context improves meaning.” Repository context remains one domain; application selection, script/project metadata and tenant-authorized knowledge are other explicitly scoped domains. Raw text, selected context and interpretation stay distinct. | Inspectability, confidence-aware binding, budgets, reversibility and no hidden exfiltration |
| Principle VII clarification | Local dictation/core and local project workflows must have useful account-free paths; enterprise channels/cloud services are optional separately declared deployments. Do not imply every phone/CRM service can operate offline. | Cloud failure never weakens privacy or authorization; no hidden fallback |
| New voice/asset consent principle | Bind personal voice/reference assets to purpose, subject, artifact and revocation; qualify model/tokenizer/data rights separately from code grants. Expose recording/retention and block stale consent on queued work. | Founder-held confidential code grants stay confirmed and private; no mandatory document upload |
| New tenant/action principle | Customer authority derives from authenticated server context and deterministic policy, not model-supplied identifiers. External side effects require scoped credentials, idempotency and unknown-outcome reconciliation. | Guidelines/confidence/scanners are evidence, not authority |
| New copy-first principle | Qualified source reuse precedes new implementation; record immutable provenance, actual dependency closure, notices, mismatch and tests. Smaller modules/services are preferred to duplicate complete applications. | No weakening of correctness/security/rights gates to increase reuse |

Principles II, III, IV, VI and VIII–XVI are preserved, with vocabulary changes only where independently reviewed as necessary. Rust-first remains a justified boundary, not a mandate to rewrite Python speech engines. Accessibility, observable privacy, no unproven superiority, progressive refinement and trusted-control repair remain binding.

## Subordinate documents affected after ratification

| Authority | Required controlled follow-up |
| --- | --- |
| AGENTS.md mission paragraph | Align scope and exact four names; retain reading order, English-only technical content, proof-before-done and grain discipline |
| ARCHITECTURE_INVARIANTS A1/A3/A6/A8 | Extend event/context/adapter vocabulary to generation, targets, tenants, consent and channels; one authority model |
| A11 | Retain Rust concurrency/policy; permit isolated donor-native/Python workers with exact closure and resource evidence |
| A12 | Proposed text: “Core retains CLI/TUI diagnostics and text fallback. The first user product may be a qualified desktop dictation surface; no custom IDE or compulsory heavyweight shell is required. Graphical surfaces consume the same Core contracts.” This is an explicit change, not a reinterpretation of terminal-first |
| A13/A14/A15 | Preserve push-to-talk baseline, keyboard fallback and typed measurements; extend cancellation events to playback/worker/action outcomes |
| PROGRAM_ROADMAP H0–H15 | Preserve as historical scope; replace future ordering through an explicit canonical roadmap revision based on V3, with distant horizons coarse |
| specs/CURRENT and 000G | Define exactly which new research/implementation grain can open, based on independently qualified prerequisites; do not retroactively mark closed product gates open |
| Benchmark/source/rights contracts | Keep frozen attempts unchanged; introduce new protocols/artifact/voice/tenant capability manifests separately |

## Approval and transition sequence

### Opus M2/M3 correction: explicit founding-chain re-scope

This section supplies the exact proposed dependency changes missing from the original proposal. None is ratified by this PR. Under current main, **B2R17 remains the sole executable successor** and 000C–000G remain unfinished. Until a dedicated amendment and canonical reconciliation legitimately adopt this graph, no Q/I/S/K/F product packet becomes READY.

| Founding child | Proposed disposition and dependency | Evidence still required |
| --- | --- | --- |
| 000A | Preserve PARTIAL/MODERATE ACP evidence; do not inflate compatibility | Authenticated lifecycle/permissions/cancel fixtures before developer-agent support |
| 000B / B2R17 → later B2 → B3/B4 disposition | Keep frozen ATTEMPT-003, #120's 209/240 outputs and 31 failures unscored. Complete its applicable qualified sequence or explicitly record insufficient STT evidence through a separately authorized synthesis; no silent winner | I-01 and speech-bearing release cells require canonically accepted backend evidence. Q-01 policy, Q-02 pure fit and Q-03 fake-worker contracts have **no STT dependency**, but still require a scoped 000G decision before production adoption |
| 000C | Split proposed scope: 000C-AGENT for optional developer steering; 000C-VOICE for later hands-free/Klaint duplex. Explicit PTT does not wait for semantic endpointing | A-01 requires agent interruption observations; V-01 requires voice/playback stop and late-frame tests; neither is automatically VERIFIED |
| 000D | PTY threat/maintenance disposition blocks only optional developer compatibility. A structured-only A-01 must explicitly exclude PTY instead of implying fallback support | Canonical decision to exclude PTY or qualified PTY fixtures; no dependency on this for Studio/text Klaint |
| 000E | Reuse F-SIDE-0 baseline plus Q-05/Q-06/Q-08 native research as the proposed platform-feasibility stream | Mic permission/device/hotkey/target/session/egress observations. Bounded disposable source-baseline builds need a named 000E research READY Grain; no release, permanent integration or installer authority follows |
| 000F | Intake the existing REA/source/rights bundle **as evidence inputs to 000F**, not a parallel completed program | Resolve actual retained fork/engine closure, notices/grant-scope flags, native/model artifacts and distribution/maintenance. Catalog presence is not 000F completion |
| 000G | Select exactly one bounded next Grain per canonical synthesis/reconciliation. Proposed capability-specific decisions: pure non-STT, Side, Studio, Klaint-text; do not mass-open all packets | Each decision cites its required 000F evidence and capability-specific 000B/000C/000D/000E disposition. Missing child evidence means no dependent product Grain READY |

The [machine-readable proposed authority graph](../../research/rea/2026-10-21/packet-authorities.json) maps every packet to one named readiness authority and explicit dependencies. It has no active READY product nodes. It distinguishes a research baseline from an installable product release, avoiding a circular requirement to implement the product before 000E can investigate feasibility. After ratification, `specs/CURRENT.md`, parent `spec.md`/`plan.md`/`tasks.md` and affected children must be reconciled together; until then this graph remains proposal data.

### Exact contradiction dispositions for the dedicated amendment

| Canonical prohibition / location | Proposed action and replacement | Verification after adoption |
| --- | --- | --- |
| AGENTS.md: “Wispral is a voice-native control plane for AI coding agents. It is not a dictation application, a proprietary agent, an IDE, or a thin wrapper around one vendor's CLI.” | REPLACE the full mission paragraph: “Wispral is a modular voice platform. WisprSide provides dictation and optional developer-agent control; WisprStudio provides voice production; Klaint provides customer dialogue. Shared contracts preserve authority and provenance. No compulsory proprietary agent, IDE, model or hosted account is required for the useful local core.” | Exact old negation absent from active mission; all four identities present; historical evidence not rewritten |
| Anti-roadmap: Wispral foundation model | KEEP excluded; no model training in this repair or first release | No training packet |
| Custom coding agent replacing existing agents | KEEP excluded | ACP remains optional integration |
| Electron IDE | RE-SCOPE: “A custom Electron IDE remains excluded. A pinned VoiceStudio desktop application for audio production is a separately qualified product surface, not an IDE.” | Studio fork does not imply coding IDE authority |
| Multi-agent office/fleet visualizer; avatars/animated personas | KEEP excluded | No such packet |
| Proprietary cloud account requirement | KEEP excluded for useful local workflows | Offline test and provider-unavailable path |
| Hosted vector-memory platform | KEEP excluded; tenant-scoped retrieval reuses existing Parlant extension/storage interfaces | No new hosted memory platform |
| Generic project-management suite; social network | KEEP excluded | No such packet |
| Mobile before terminal control proven | RE-SCOPE: “Mobile remains deferred until its product's desktop/core contract and separate platform research qualify it; no universal terminal milestone substitutes for mobile permission evidence.” | No near-term mobile READY node |
| Enterprise dashboards before core user value | RE-SCOPE: “Core has no generic enterprise dashboard. Klaint may expose the minimum operational inbox/QA/tenant controls required by a separately qualified customer workflow, using existing APIs.” | Dashboard scope tied to Klaint action/handoff fixtures |
| Mandatory hosted security scanner; LLM verdict as direct authority | KEEP excluded | Deterministic authorization and local availability preserved |
| Generic plugin marketplace before admission contract | KEEP excluded | No marketplace packet |
| A12 terminal-native first surface | REPLACE with per-product rule: “Core contracts and diagnostics retain CLI/text accessibility. WisprSide may retain Handy's Tauri surface; WisprStudio may retain VoiceStudio's desktop surface; Klaint uses its Python service and optional unmodified inbox API. Each surface requires its own authority and accessibility evidence. No new Core daemon or IDE is mandatory.” | Per-pillar contradiction checklist against A12, AGENTS mission and every anti-roadmap item |

G-01 acceptance requires a reviewer to compare each of the above old phrases against the final proposed canonical diff and record KEEP/REPLACE/RE-SCOPE, exact replacement text, affected pillar and required evidence. A grep alone is a discovery aid, not semantic approval. No constitutional exception is inferred from donor functionality.

M1 is an ordinary **fail-closed over-application** repair, not a Principle XVI fail-open repair. Its dedicated PR must preserve the original red results, exact historical PASS and frozen-object mutation rejection. Earlier API 403 observations remain historical. The repair-session API recheck returns `protected=false` on main, 404 “Branch not protected” from classic protection, and an empty ruleset list including parents. No classic required-check list is exposed; governance-required gates still apply. Recheck settings at merge and record UNKNOWN if access fails. Do not infer an exemption from #118 having merged while a check was red. Neither repair nor plan is merge-approved.

1. Review this research PR as planning-only, including source choices and missing evidence. Preserve its actual failed/pending/unavailable CI results.
2. Recheck canonical main, open PRs and required exact-head controls. Diagnose the B2R16 later-PR scope conflict independently. Determine the applicable governance/control lane from live authority; Principle XVI must not be used as a convenient substitute for an ordinary gate or for an unproven fail-open defect.
3. Open a dedicated amendment PR with exact canonical base, changed paths, proposed major version, compatibility impacts, security/privacy and affected specs. Resolve independent substantive review and required gates at the final head; use the prescribed guarded merge and verify actual canonical ancestry.
4. Reconcile subordinate documents in a separately qualified bounded sequence. Record what is still closed. Do not auto-merge #120/#121/#123 or treat them as canonical dependencies.
5. Refine applicable 000G successor and one extraction/contract Grain; only explicit READY authority opens that packet. No source selection, founder code grant, strategy merge or proposed ADR substitutes for readiness.

## Security/privacy and migration impact

The broader mission adds application context capture, personal voice assets, multi-tenant data, external CRM actions and phone recordings. It therefore increases the surface even when the first release is local. New authority contracts must deny stale target/context, revoked voice consent, cross-tenant IDs, unbrokered worker network access and unknown irreversible action retries. Existing prompt/permission/cancel invariants stay intact. Local media/project data needs versioned migration/export and retention controls. An amendment must not promise that old third-party outputs can be recalled after voice-consent revocation.

Names are final founder selections; trademark/domain/store clearance is not asserted. Existing confidential source grants are confirmed, not pending. Models, voices and independently licensed third-party portions still need their specific records. Implementation/release approval is a technical governance matter and does not reopen a request to view confidential legal agreements.
