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

1. Review this research PR as planning-only, including source choices and missing evidence. Preserve its actual failed/pending/unavailable CI results.
2. Recheck canonical main, open PRs and required exact-head controls. Diagnose the B2R16 later-PR scope conflict independently. Determine the applicable governance/control lane from live authority; Principle XVI must not be used as a convenient substitute for an ordinary gate or for an unproven fail-open defect.
3. Open a dedicated amendment PR with exact canonical base, changed paths, proposed major version, compatibility impacts, security/privacy and affected specs. Resolve independent substantive review and required gates at the final head; use the prescribed guarded merge and verify actual canonical ancestry.
4. Reconcile subordinate documents in a separately qualified bounded sequence. Record what is still closed. Do not auto-merge #120/#121/#123 or treat them as canonical dependencies.
5. Refine applicable 000G successor and one extraction/contract Grain; only explicit READY authority opens that packet. No source selection, founder code grant, strategy merge or proposed ADR substitutes for readiness.

## Security/privacy and migration impact

The broader mission adds application context capture, personal voice assets, multi-tenant data, external CRM actions and phone recordings. It therefore increases the surface even when the first release is local. New authority contracts must deny stale target/context, revoked voice consent, cross-tenant IDs, unbrokered worker network access and unknown irreversible action retries. Existing prompt/permission/cancel invariants stay intact. Local media/project data needs versioned migration/export and retention controls. An amendment must not promise that old third-party outputs can be recalled after voice-consent revocation.

Names are final founder selections; trademark/domain/store clearance is not asserted. Existing confidential source grants are confirmed, not pending. Models, voices and independently licensed third-party portions still need their specific records. Implementation/release approval is a technical governance matter and does not reopen a request to view confidential legal agreements.
