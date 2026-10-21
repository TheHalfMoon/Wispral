# Donor rubric and sensitivity

The founder weights are functional fit 20%, qualified reusable code 20%, technical integration 15%, **measured quality 15%**, security/privacy 10%, offline/portability 10%, maintenance/tests 5%, compliance/economics 5%. No model/product quality was measured; that field is **NOT_MEASURED (null)** for every candidate. We do not impute vendor claims, score it zero or renormalize the other 85 points into an empirical total.

The following 0–5 ordinal ratings are analyst source-engineering judgments (5 = stronger fit/fewer observed obstacles), not experimentally measured integration/security/offline performance. Known subtotal is sum(weight × rating / 5) over seven source-assessable dimensions, out of 85. The possible range adds the unknown 0–15 quality contribution; its endpoints are uncertainty bounds, not predicted quality scores. Rights/economics rates distribution/asset/dependency burden, never whether founder permission exists. No cost or development velocity was benchmarked.

| Pillar / candidate | Fit / reuse / integration | Privacy / offline / maintenance / rights | Source subtotal /85 | Total remains unknown | Rationale |
| --- | --- | --- | --- | --- | --- |
| Studio / VoiceStudio | 5 / 4 / 2 | 3 / 4 / 3 / 2 | 61 | 61…76 | Broad fit/render/resume/dub seams; coupled backend and incompatible engine environments; default asset restrictions separated from founder code authorization. |
| Studio / Voicebox | 4 / 4 / 3 | 3 / 4 / 3 / 3 | 61 | 61…76 | Smaller generation service/desktop boundary; less long-form/dubbing breadth; asyncio cancel does not prove native stop. |
| Ink / Handy | 5 / 5 / 4 | 3 / 4 / 4 / 4 | 74 | 74…89 | Rust capture/hotkey packages and transaction source match boundary; native permission/insertion behavior unqualified. |
| Ink / OpenWhispr | 5 / 4 / 2 | 2 / 3 / 4 / 4 | 60 | 60…75 | Broad dictation helpers and real pure tests; large Electron glue and unsafe focus fallback require extraction. |
| Klaint / Parlant | 5 / 4 / 3 | 2 / 3 / 4 / 4 | 63 | 63…78 | Real dialogue/guideline/tool lifecycle; deterministic tenant/action authority must be added around probabilistic service. |
| Klaint / Rasa | 3 / 3 / 1 | 3 / 3 / 3 / 4 | 46 | 46…61 | Useful tracker/rule/lock mechanisms but maintenance mode and old Python closure; second dialogue engine duplicates lead. |
| Klaint / Botpress public SDK | 4 / 3 / 2 | 2 / 1 / 4 / 4 | 48 | 48…63 | Strong selected connectors/HITL schemas; API defaults/cloud-dependent SDK is not a complete self-hosted runtime. |
| Realtime / Pipecat | 4 / 4 / 4 | 3 / 4 / 4 / 4 | 66 | 66…81 | Composable local frame/worker boundary; optional provider/native closure still needs qualification. |
| Realtime / LiveKit Agents | 5 / 4 / 3 | 3 / 3 / 4 / 4 | 65 | 65…80 | Strong WebRTC/room/SIP session fit; topology and media/server dependencies cost more for first local PTT path. |

## Weight sensitivity

Each scenario retains null quality. Alternative weights sum to 100; no results change their evidence class. Read [donor-rubric.json](donor-rubric.json) to reproduce arithmetic.

| Candidate | Founder known + unknown | Integration emphasized | Privacy/offline emphasized | Quality emphasized |
| --- | --- | --- | --- | --- |
| VoiceStudio | 61 + UNKNOWN[15] | 54 + UNKNOWN[15] | 60 + UNKNOWN[15] | 50 + UNKNOWN[30] |
| Voicebox | 61 + UNKNOWN[15] | 58 + UNKNOWN[15] | 60 + UNKNOWN[15] | 50 + UNKNOWN[30] |
| Handy | 74 + UNKNOWN[15] | 72 + UNKNOWN[15] | 70 + UNKNOWN[15] | 60 + UNKNOWN[30] |
| OpenWhispr | 60 + UNKNOWN[15] | 54 + UNKNOWN[15] | 56 + UNKNOWN[15] | 49 + UNKNOWN[30] |
| Parlant | 63 + UNKNOWN[15] | 60 + UNKNOWN[15] | 58 + UNKNOWN[15] | 51 + UNKNOWN[30] |
| Rasa | 46 + UNKNOWN[15] | 40 + UNKNOWN[15] | 48 + UNKNOWN[15] | 39 + UNKNOWN[30] |
| Botpress public SDK | 48 + UNKNOWN[15] | 46 + UNKNOWN[15] | 44 + UNKNOWN[15] | 39 + UNKNOWN[30] |
| Pipecat | 66 + UNKNOWN[15] | 66 + UNKNOWN[15] | 64 + UNKNOWN[15] | 54 + UNKNOWN[30] |
| LiveKit Agents | 65 + UNKNOWN[15] | 62 + UNKNOWN[15] | 62 + UNKNOWN[15] | 53 + UNKNOWN[30] |

VoiceStudio/Voicebox are tied on the base source subtotal: choose VoiceStudio provisionally because the requested scope includes dubbing/long-form, and retain Voicebox if a narrower release makes its extraction materially smaller. Integration weighting favors the narrower application boundary. Handy has the best source alignment for Rust capture/delivery, but its base total interval still overlaps OpenWhispr; do not label it a measured reliability/quality winner. Parlant is the provisional conversation lead while Chatwoot and Botpress are complementary service/connector roles rather than rivals on one undifferentiated leaderboard. Pipecat/LiveKit swap value with local versus room/SIP topology; the scoring is not a reason to run both.

Increasing quality weight widens uncertainty and makes blanket ranking less defensible. Strict CPU budgets reopen Pocket TTS/Kokoro/Piper artifact and acoustic trials; Arabic requirements can exclude candidates regardless of a good generic score. Non-negotiable authority/tenant/consent or artifact-rights failures are qualification vetoes, not tradeoffs that a weighted average can cancel. STT has no production selection: complete its applicable governed evidence sequence instead of using this rubric to bypass frozen B2.

No numerical ranking establishes superiority over proprietary competitors. Rerate integration after an actual extraction spike and replace null quality only with preregistered held-out results. Preserve this initial judgment and record revisions forward.
