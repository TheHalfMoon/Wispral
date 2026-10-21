> Historical internal review of original f363381 only. Its original architecture assessment is superseded by the Opus-repaired current plan and owner table; it does not review or approve the later repair range.

INDEPENDENT_REVIEW=NOT_SATISFIED_BY_THIS_FILE

# Internal consistency review of the original research bundle

Review date: 2026-10-21. Reviewer: a separate REA source/evidence worker. Scope: research integrity, traceability and feasibility of the proposed plan against Issue #122 and the founder's English-only steering. **This is not independent security, benchmark, merge or release approval.** This worker previously authored the additional-source review and benchmark/replay protocol; those files are referenced for consistency, not represented as independently reviewed work by a fresh author.

The parent was editing the bundle during this review. Findings below distinguish the initially reviewed text, corrections observed during reread and checks that must be rerun after the final artifact set is frozen. Git commit identity and the final validation output, rather than this intermediate review's timestamp, bind the delivered bundle.

## Review performed

Read the research README, Core deep dive, REA methodology, live frontier/handoff, source catalog and transplant synthesis, feature/parity matrix, rights register, new-candidate log, rubric and all four proposed strategy documents plus the proposed ADR. Inspected structured catalog/transplant/rubric/runtime/index records and relevant pinned source files. The pillar studies' stated test counts and runtime limits were also checked in the earlier bounded review recorded in [ADDITIONAL_SOURCE_REVIEW.md](ADDITIONAL_SOURCE_REVIEW.md).

Mechanical cross-checks during this review found:

- 132 catalog identities, 127 resolved pins, four empty-repository responses and one incorrect scorer identity returning 404. These counts agree with the synthesis; the corrected jitsi/jiwer identity is separate.
- 72 unique proposed mechanism IDs. For the GitHub source references with captured files, URL pin/path and recorded source SHA-256 checks found no mismatch; this was a source-reference integrity check, not semantic audit of every captured byte or dependency.
- All six runtime observation records' `original_envelope_sha256` values matched their local original REA envelope files. Derived observations retain the public-page/incomplete-event/unknown-platform limits and do not claim generated audio, dictation or customer-agent success.
- Rubric scenario weights/arithmetic matched the JSON ratings. Measured-quality values remain null; no missing quality was silently converted to zero or renormalized into an empirical winner.
- Local Markdown target checks found only the then-unwritten link to this review, which creation of this file resolves. Remote links' future availability and Markdown fragment correctness were not exhaustively validated.
- At one intermediate snapshot, three indexed artifact hashes were stale after concurrent edits. Final index regeneration and validation are required after the corrections and this review file are in place. This check is not a final-hash attestation.

No donor full suite, new product runtime, audio inference, native installation or authenticated vendor workflow was executed as part of this review.

## Actionable findings

### R1 — Correct source-rights summaries from captured license text

**Status: corrected register text observed on reread.** [RIGHTS_AND_ATTRIBUTION_REGISTER.md](RIGHTS_AND_ATTRIBUTION_REGISTER.md) initially carried `NOASSERTION` for Moonshine, codex-acp and FFmpeg even though their actual license files were captured. The parent replaced those metadata-only summaries with inspected terms, including the Arabic checkpoint exception and build-dependent FFmpeg boundary. The ACP Rust SDK's Apache terms are also explicit.

Correction evidence:

- At Moonshine revision `234f60faa0eb388b01cdf7e60aca232af37aefda`, [LICENSE](https://github.com/moonshine-ai/moonshine/blob/234f60faa0eb388b01cdf7e60aca232af37aefda/LICENSE#L1) says code except `core/third-party` is MIT and defaults models to MIT, but explicitly lists **legacy non-streaming Arabic Base/Tiny** among the non-MIT models governed by its Community License. The register now preserves that exact code/model distinction, separate TTS/G2P terms and the Community body's limited-commercial provisions. It does not infer every Arabic or every streaming model has that exception or categorically prohibit all commercial Community use.
- At codex-acp revision `ced4c34368d271d61bbc81f4047813b4db387623`, [LICENSE](https://github.com/agentclientprotocol/codex-acp/blob/ced4c34368d271d61bbc81f4047813b4db387623/LICENSE#L1) expressly declares the Apache License 2.0 and JetBrains copyright. `NOASSERTION` is metadata, not the observed file terms.
- At FFmpeg revision `3b3dc211fed40e7e4f627dffd6a4e221eb481880`, [LICENSE.md](https://github.com/FFmpeg/FFmpeg/blob/3b3dc211fed40e7e4f627dffd6a4e221eb481880/LICENSE.md#L1) describes LGPL v2.1+ for the default combination and optional GPL activation/build-dependent obligations. The register now states that boundary and preserves the actual-build qualification requirement; the controlling summary is linked here alongside its existing COPYING references.

These are provenance corrections, **not** requests for confidential founder agreements or reasons to block authorized source-code research. The founder's confirmed grants remain recorded and distinct from model/voice/dependency assets.

### R2 — Repair work-packet mechanism joins

**Status: corrections observed during review.** The initial K-02 cited `K04/K05` for action/idempotency, but those IDs map to Parlant session history and Chatwoot account/inbox scope. The parent corrected K-02 to `K03/K12` plus connector/ledger glue and expanded K-03 to the actual account/session/handoff IDs. This now follows the source manifest rather than sending a contributor to the wrong mechanism.

The initial I-02 attributed optional rewriting to `INK-I8/I13`, which supply a macOS selection snapshot and streaming provenance rather than a rewrite implementation. The parent changed that packet to identify these as context/provenance only and require separate qualification/deferment of any rewrite provider. Preserve this correction in the final index and PR.

### R3 — Add per-attempt provenance for failed REA collection

**Status: bounded failure-provenance records added and observed on reread.** The initially reviewed `rea-runtime-observations.json` retained four aggregate failure summaries, grouping Flow/Aqua/Superwhisper launch failures and both CLI attempts without per-attempt original-envelope digests/scenario identities. The parent added a `failed_attempt_provenance` section with available request/response artifacts and digests. It explicitly discloses overwritten CLI output and absent valid envelopes rather than inventing independent per-attempt evidence. The six successful bounded observation records retain their verified original-envelope hashes.

The correction follows the requested bounded record design: target/tool/mode/version, invocation identity, result/failure class and available artifact digest, with explicit identity limits. Those digests establish the retained artifact's identity, not a successful workflow or independent visibility into an overwritten attempt. No repetition of failed experiments or full proprietary page dump was needed.

### R4 — Regenerate final index after all edits

**Priority: required final integrity housekeeping.** The independently sampled intermediate `EVIDENCE_INDEX.json` mismatched `official-peer-observations.json`, `official-web-source-manifest.json` and `WISPRAL_COPY_FIRST_WORK_PACKETS.md` because the parent was actively correcting them. Regenerate the artifact index after all edits, include this review, and run the committed bundle validator against the final checkout. Keep its integrity-only scope and exclude the index's own digest to avoid a hash cycle. Do not report the intermediate mismatch as a product or source failure.

## Feasibility and authority assessment

The main source-fit decisions follow the inspected boundaries: Handy packages/native seams, selective VoiceStudio production mechanisms, Parlant with brokered ToolService, optional Chatwoot and selected Botpress connectors, and one Rust authority/provenance/resource Core. Incompatible speech-engine environments are isolated, not merged. Pipecat/LiveKit are topology choices with one turn controller per session. No production STT or measured quality winner is claimed.

The architecture and work packets correctly treat cancellation request/acknowledgement as weaker than observed stop, reject stale results, avoid wrong-foreground insertion, distinguish model guidelines from authorization, preserve partial/unknown external effects and retain human takeover authority. These are proposed contracts; none is represented as implemented or independently security-qualified.

The proposal preserves Constitution 0.2.1, canonical B2R17/frozen ATTEMPT-003 and the closed product-code/000G authority. Governance changes and the ADR remain proposed; no strategy prose is used as readiness authority. CI applicability failures remain failures, and the plan does not alter trusted verifiers to make this draft green. Existing PRs remain references, not silently merged dependencies.

Some packets span multiple operating-system/security/engine responsibilities despite short estimates. The document explicitly requires refinement and separate native qualification, so these are shaping estimates rather than executable one-step tasks. In particular, split Q-04 into pure route decisions, actual DNS-to-socket transport binding and OS worker-egress enforcement before READY; a passing route fixture cannot supply the final enforcement proof. Similarly, native target integrity and real stop guarantees need actual platform fixtures. The unrun/blocked-cell table makes those missing resources actionable.

The catalog is substantive but not a whole-source audit of all 132 repositories. Deep conclusions are limited to named mechanisms, and secondary founder/historical candidates are honestly labeled preliminary. Runtime competitive coverage remains limited to public pages/access boundaries and failed previews. The bundle appropriately records those gaps, defines future success/failure/boundary trials and does not claim product parity, acoustic superiority or legal review of private grants.

After the findings above are addressed and final integrity checks rerun, this review found no additional planning-level contradiction that requires product implementation or expanded authority to resolve. This statement neither approves merge nor satisfies any mandatory independent security/release gate.

## Naming addendum

The founder subsequently confirmed the dictation name **WisprSide**, expressly referring to the updated record in PR #123. The parent communicated that direct human answer to this reviewer. Accordingly, replacing the earlier dictation branding in newly authored deliverables and renaming the pillar report to `WISPRSIDE_DEEP_DIVE.md` is a human-authorized naming correction. The final hierarchy is **Wispral / WisprStudio / WisprSide / Klaint**. This correction changes no donor selection, interface, technical work packet, test result, governance readiness or implementation authority. Existing `INK-I*` source mechanism IDs and `ink-*` evidence/helper filenames remain stable provenance identifiers rather than public product branding. The parent will refresh local links and indexed hashes after the rename; this addendum does not attest to those later integrity checks.
