# Wispral source research and copy-first master replan

2026-10-21 · [Authoritative mission #122](https://github.com/TheHalfMoon/Wispral/issues/122) · Research and proposed planning only.

**Wispral** is the proposed umbrella platform, with **WisprStudio** for voice production, **WisprSide** for dictation and optional developer-agent control, and **Klaint** for customer voice/chat agents. These are the final founder names. The active constitution/specification frontier and product-code gate remain unchanged.

FOUNDER_SOURCE_AUTHORIZATION=YES_CONFIRMED_BY_FOUNDER
CONFIDENTIAL_GRANTS=HELD_PRIVATELY_BY_FOUNDER_NOT_SHARED

The founder confirms existing source-copy/adapt/rebrand rights. No confidential documents were requested or independently inspected. Preserve source provenance/notices and separately qualify model weights, tokenizers, personal voices and external assets.

The latest live Issue #122/PR #123 naming revision and the user's direct confirmation select **WisprSide**. This supersedes the older attached brief's dictation name. Historical records remain intact; INK-I source IDs and ink-prefixed evidence/probe filenames are stable technical references, not current product branding.

## Start here

| Decision | Lead source selection | Missing proof |
| --- | --- | --- |
| WisprSide | Handy native packages/coordinator/transaction, selected OpenWhispr helpers | Native permission, target delivery, actual STT/latency and clean OS support |
| WisprStudio | Selected VoiceStudio fit/render/resume/project/dub services; isolated engine workers | Actual generation/quality/GPU, consent-backed voices, install/recovery |
| Klaint | Parlant dialogue, brokered ToolService, optional Chatwoot, selected Botpress connectors | Real tenant/action/handoff behavior, production/phone/voice workflows |
| Core | Rust authority with narrow Sentrdel/Ninerr/Ascout/Orcel/ACP seams | Owned native stop, actual egress enforcement and authenticated agent compatibility |

The catalog covers 132 requested source identities, including 127 resolved pins and five failed/empty accesses, plus the complete 59-repository accessible founder-account inventory (including Wispral itself). Catalog breadth is not whole-source audit coverage: deep findings are bounded to named mechanisms; secondary entries are explicitly preliminary triage. The consolidated transplant matrix has 72 proposed mechanisms; additional Pocket TTS/Aly review is separate. Zero runtime product transplants were made.

Actual experiments: 17 unique OpenWhispr pure unit tests, eight named synthetic non-audio Studio mechanism cases and six pure Ninerr policy fixtures. REA captured public browser observations; an ElevenLabs preview attempt did not verify audio, and Cartesia sign-in/navigation recovery did not exercise authenticated inference. No speech-quality, performance, native application, GPU or phone benchmark result exists here.

## Research and evidence

- [Live frontier, CI conflict and handoff](LIVE_FRONTIER_AND_HANDOFF.md)
- [Source catalog](SOURCE_CATALOG.md) and [machine-readable catalog](source-catalog.json)
- [New candidate decisions](NEW_CANDIDATES_LOG.md)
- [REA methodology and limits](REA_METHODOLOGY.md) and [bounded runtime observations](rea-runtime-observations.json)
- [Evidence index with artifact hashes and trial status](EVIDENCE_INDEX.json)
- [WisprSide deep dive](WISPRSIDE_DEEP_DIVE.md)
- [WisprStudio deep dive](WISPRSTUDIO_DEEP_DIVE.md)
- [Klaint deep dive](KLAINT_DEEP_DIVE.md)
- [Wispral Core deep dive](WISPRAL_CORE_DEEP_DIVE.md)
- [Additional Pocket TTS / Aly source review](ADDITIONAL_SOURCE_REVIEW.md)
- [Transplant matrix](SOURCE_TRANSPLANT_MATRIX.md) and [structured mechanisms](source-transplants.json)
- [Feature parity and gaps](FEATURE_PARITY_AND_GAP_MATRIX.md)
- [Weighted rubric and sensitivity](DONOR_EVALUATION_RUBRIC.md)
- [Rights and attribution register](RIGHTS_AND_ATTRIBUTION_REGISTER.md)
- [Benchmark and success/failure/boundary replay protocol](BENCHMARK_AND_REPLAY_PROTOCOL.md)

## Rebuilt plan

- [Platform architecture](../../../docs/strategy/WISPRAL_PLATFORM_ARCHITECTURE_REPLAN.md)
- [Master Plan V3](../../../docs/strategy/WISPRAL_MASTER_PLAN_REBUILT.md)
- [Copy-first work packets](../../../docs/strategy/WISPRAL_COPY_FIRST_WORK_PACKETS.md)
- [Governance amendment proposal](../../../docs/strategy/WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md)
- [Proposed architecture decision record](../../../docs/adr/0001-proposed-donor-boundaries-for-platform-replan.md)

The first next action is authority/frontier reconciliation and a dedicated governance proposal, followed by one applicable qualified extraction Grain. This research does not merge historical PRs, reopen scoring, choose production STT, claim competitor parity or authorize wholesale implementation. Required CI failures remain failures; source findings and local probes cannot override them.

## Reproduction

Use an existing Node 24 interpreter for [Ink pure tests](reproduce_ink_pure_units.mjs), an existing Python interpreter for [Studio probes](studio_mechanism_probe.py), and authorized exact Ninerr modules for [Core policy probes](reproduce_core_policy.mjs). Helpers require caller-selected disposable paths and verify source SHA-256. They do not install packages or models. Follow tool `--help`/usage and each deep dive; run names/results are not native app verification. [Validation](VALIDATION.md) records checks of this research bundle separately from product evidence.
