# Competitor gap matrix and measurable differentiators

**Status:** CANDIDATE. Every competitor fact is `DOCUMENTED` from the vendor's public pages (URLs in the linked reports, accessed 2026-10-21 or 2026-11-08) or `SOURCE_VERIFIED` for open source. "Not stated" never means absent. No competitor product was installed, signed into or used, and **no parity or superiority is claimed**. The Wispral column is the plan, `NOT_RUN`.

Sources: PR #124 [feature parity matrix](../rea/2026-10-21/FEATURE_PARITY_AND_GAP_MATRIX.md) (WisprSide and realtime references); 2026-11-08 [Klaint report §5](evidence/research-reports/KLAINT_SOURCE_RESEARCH.md#5-competitors-official-documentation-only) (11 vendors, 70 pages); [WisprStudio report §5](evidence/research-reports/WISPRSTUDIO_SOURCE_RESEARCH.md#5-competitors-brief); [WisprSide report](evidence/research-reports/WISPRSIDE_SOURCE_RESEARCH.md) (Wispr Flow admin-window guidance, Windows UIPI). **Known gap:** the 2026-11-08 WisprSide competitor refresh (report §5) was not completed before the usage limit; WisprSide competitor cells rely on PR #124's 2026-10-21 observations and are flagged for refresh in packet BM-02's preparation.

## 1. Tiering rule

1. **Parity** — needed to be credible at all.
2. **Polished first release** — what makes the first release feel finished.
3. **Differentiators** — where Wispral aims to lead, each with a test.
4. **Long-term research** — only after evidence.

## 2. WisprSide (vs Wispr Flow, Aqua Voice, Superwhisper, VoiceInk, OpenWhispr, Handy, FreeFlow, Windows Voice Access)

| Capability | Reference behaviour (documented) | Wispral tier | Source for Wispral |
| --- | --- | --- | --- |
| Push-to-talk / toggle, floating indicator | Common to all references | Parity (SD-01, SD-02) | Handy |
| Local offline transcription | Superwhisper, VoiceInk, Handy, OpenWhispr document local models; Wispr Flow and Aqua are cloud-first | Parity (SD-03) | Handy + transcribe-cpp |
| App and screen context | Aqua and others use screen context; FreeFlow's screenshot fallback defaults on | **Rejected as default**; opt-in app identity and selected text only (SD-18, SD-20) | Privacy stance |
| Custom vocabulary, filler removal, self-correction | Common in paid products | Polished release (SD-11, SD-12) | Handy custom words + OpenWhispr guard |
| Elevated windows | Wispr Flow's documented answer for paste failures in admin windows is to run Flow as administrator | Refuse and explain (SD-06) | New (BN-01b) |
| Arabic dialects / code-switching | Language-count claims (for example Aqua 49, Superwhisper 100+) with no published dialect evidence found | **Differentiator only after measurement** (SD-16) | WB-AR |

| # | WisprSide differentiator | Measurable test (pass condition) |
| --- | --- | --- |
| SX-1 | **Never types into the wrong window** | WB-DELIVERY: 0 wrong-target insertions across focus-steal, close, PID-reuse, virtual-desktop, lock-screen, elevated and password fixtures on the shipped binary |
| SX-2 | **Provably offline** | WB-EGRESS: 0 outbound connections during a 30-minute offline session (packet capture or firewall log) |
| SX-3 | **Delivery receipt** naming the destination app, with truthful partial/refused states | Outcome correctness 100% on the fixture matrix; usability test: participants identify where text went in ≥ 95% of trials |
| SX-4 | **Raw transcript always one click away**; rewrite is reversible | Provenance check: raw hypothesis byte-identical in history for 100% of rewritten entries |
| SX-5 | **Gulf Arabic / code-switch quality, published openly** | WB-AR per-segment WER/CER and negation-flip rates with CIs on the consented panel, compared on identical utterances against named alternatives |
| SX-6 | **Low resource footprint** on 8–16 GB CPU laptops | Idle CPU ≈ 0% and recorded RSS on HW-A; model unloaded after timeout |

## 3. WisprStudio (vs ElevenLabs, Cartesia, Resemble AI, Voicebox, VoiceStudio)

| Capability | Reference behaviour (documented) | Wispral tier |
| --- | --- | --- |
| Long-form chapters, multi-voice | ElevenLabs Studio (up to 500 chapters); VoiceStudio long-form | Parity (ST-07) |
| Professional cloning with verification | ElevenLabs PVC requires a verification recording and allows only your own voice; Cartesia's cloning page states no consent mechanism | Parity+ (ST-04 consent ledger enforced on every path) |
| Dubbing editor | ElevenLabs Dubbing Studio (now in maintenance mode; exports AAF/SRT/CSV) | Polished release (ST-11); AAF export is a later gap |
| Pronunciation rules | ElevenLabs phoneme tags (Flash v2 only) | Polished release (ST-10; respelling first, phonemes per engine) |
| Watermark and detection | Resemble PerTh (MIT) and Detect | Parity (ST-05) |
| Local / offline | Voicebox and VoiceStudio local; cloud vendors are not | Differentiator after ST-D01/ST-D08 |

| # | WisprStudio differentiator | Measurable test (pass condition) |
| --- | --- | --- |
| STX-1 | **Offline Arabic dubbing** | OS firewall blocks network; full ASR → translate → fit → TTS → mix completes with 0 outbound attempts (packet capture) |
| STX-2 | **Consent enforced everywhere, revocation that bites** | 4 clone paths × {none, valid, revoked, hash mismatch}: 100% correct; queued jobs cancelled within a measured deadline; late output discarded |
| STX-3 | **Crash-safe long-form** | Kill during render; restart regenerates only incomplete segments; output byte-identical to an uninterrupted run with the deterministic `_echo` engine |
| STX-4 | **Commercial-clean default bundle** | SBOM + manifest: 0 non-commercial or unreviewed weights in the default install |
| STX-5 | **Arabic-aware pronunciation** | Clitic cases and a 50-item Arabic/Gulf panel apply the lexicon correctly with no false positives on a negative set |
| STX-6 | **Watermark on every cloned output** | Detector flags 100% of cloned exports across WAV, MP3 128k and AAC re-encodes; false-positive rate reported on 100 natural clips |

## 4. Klaint (vs Decagon, Sierra, Intercom Fin, Ada, Retell, Vapi, Bland, Botpress, Chatwoot Captain, Parlant, Cognigy)

Condensed from the 11-vendor matrix: every vendor documents voice and chat, knowledge retrieval, workflows and handoff; **self-hosting is not stated by 6 of 11**; **only Ada lists Arabic voice dialects**; Ada and Retell document run-to-run variation in simulations; no fetched page describes a per-action ledger of customer-facing tool executions with unknown-outcome reconciliation.

| # | Klaint differentiator | Measurable test (pass condition) |
| --- | --- | --- |
| KX-1 | **Exactly-once external actions under uncertainty** | 1,000 fault-injection runs (timeout after commit, broker crash between dispatch and record, webhook replayed ×3, customer double-send): exactly 1 mutation per authorized intent; every unknown reconciled before any retry |
| KX-2 | **Commitments only from receipts** | 100 adversarial prompts × 3 seeds × EN/AR: 0 messages asserting refund, price or completion without a matching committed receipt (deterministic phrase-and-slot checker) |
| KX-3 | **Self-host with zero surprise egress** | Packet capture during a full text session with a local model and Chatwoot: only allowlisted hosts |
| KX-4 | **Arabic (MSA + Gulf) and code-switch with published method** | tau2-style bilingual task sets: pass^k per language with denominators; targets set only after a baseline |
| KX-5 | **Replayable simulations** | 200 recorded transcripts replayed: 100% identical verdicts and database hashes |
| KX-6 | **Race-free human takeover** | 1,000 randomized takeover interleavings: 0 AI messages or tool calls committed after the epoch change |
| KX-7 | **Tenant isolation proof** | Cross-tenant fuzz (guessed sessions, swapped JWTs, foreign IDs in tool arguments, cross-account bot tokens, loopback tool-server probes): 0 cross-tenant reads, writes or executions |
| KX-8 | **Tamper-evident per-action audit** | Modify, delete or reorder one ledger row: the verifier reports the exact break |

## 5. Long-term research (not planned work)

Hands-free capture with semantic endpointing; mobile keyboards; Arabic voice design (no permissive open model today; fine-tune trigger FT-5); outbound calling; collaborative studio review; cross-device sync.
