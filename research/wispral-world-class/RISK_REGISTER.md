# Risk and dependency register

**Status:** CANDIDATE — reviewed at every phase gate. Part of the [World-Class Master Plan](../../docs/strategy/WISPRAL_WORLD_CLASS_MASTER_PLAN.md). Likelihood (L) and impact (I) are engineering judgment on a 1–5 scale, not measurements. Owner "ENG" means the engineering agent team; "FOUNDER" means a decision only the repository owner can make.

| ID | Risk | L | I | Early signal | Mitigation | Owner |
| --- | --- | :-: | :-: | --- | --- | --- |
| R-01 | **Governance deadlock:** every PR fails the historical `verify-b2r16-freeze`; the platform thesis contradicts the active constitution; no legitimate lane to repair a fail-closed over-applied control | 5 | 5 | Planning PRs stay red indefinitely | Executable sequence in [governance reconciliation](../../docs/strategy/WISPRAL_GOVERNANCE_RECONCILIATION.md): founder-ratified amendment adding a narrow applicability-correction lane, then the #126-style repair under it, then the platform amendment | FOUNDER + ENG |
| R-02 | B2 benchmark lane and product lanes block each other | 4 | 4 | Product packets waiting on B2R17 | Keep B2 frozen and resumable; only speech-route packets depend on speech evidence; non-STT packets proceed after their own READY | ENG |
| R-03 | **Name similarity:** "WisprSide" and "Wispral" resemble "Wispr" / "Wispr Flow" (an existing dictation product) | 4 | 4 | Clearance search hits | Trademark/domain clearance review before any public use (gate G-LEGAL); names are founder-final for internal work; clearance is a separate launch check | FOUNDER |
| R-04 | Copyleft obligations: VoiceStudio is AGPL-3.0 and some narrow donors are GPL | 3 | 4 | Distribution or network-service plans | Founder confirms private grants cover the specific reuse; record per-file grant scope without requesting documents; keep notices; isolate any third-party sub-component not covered | FOUNDER (scope) + ENG (records) |
| R-05 | **Model weight rights:** attractive TTS/ASR weights are non-commercial (for example CC BY-NC) or have custom terms | 4 | 4 | Manifest rows with `commercial_use: prohibited/unknown` | Manifest-enforced blocking in commercial profiles; prefer permissive weights for defaults; evaluation-only use clearly labelled | ENG |
| R-06 | **CPU-only reference hardware** (i5-13420H, 16 GB, integrated GPU) makes Studio engines slow and limits local LLM quality | 5 | 3 | RTF ≫ 1 on HW-A | CPU-feasible defaults for Side; Studio measures CPU and free-tier GPU cells separately; optional user-configured providers clearly marked; no hardware purchase assumed | ENG |
| R-07 | **Arabic dialect evaluation data is scarce or restrictively licensed** | 4 | 4 | Datasets unusable for commercial evaluation | Consented Wispral panel with written consent; public datasets used only within their terms; report per-segment n honestly; no claim without a measured cell | ENG + FOUNDER (consent program) |
| R-08 | Donor upstream drift makes fork rebases expensive | 3 | 3 | Large conflict counts on rebase | Upstream-tracking branch, small deltas confined to adapters, delta register, scheduled rebase windows, upstreamable fixes offered back where licenses allow | ENG |
| R-09 | Fork baselines fail to build or tests fail on Windows | 3 | 4 | F-SIDE-0 / F-STUDIO-0 red | Baseline packets record exact failures before any edit; fallback to selective extraction only with evidence | ENG |
| R-10 | **Windows code signing cost and SmartScreen reputation** | 4 | 3 | Unsigned installer warnings | Choose a signing path in phase 3 ([platform compatibility](../../docs/engineering/WISPRAL_PLATFORM_COMPATIBILITY.md)); never claim an unsigned build avoids warnings; private betas can tolerate warnings with instructions | FOUNDER (cost) |
| R-11 | Wrong-target insertion through an unforeseen Windows path (UWP, games, remote desktop, secure desktop) | 3 | 5 | WB-DELIVERY escapes | Expand the fixture matrix; default to refusal for unknown window classes; copy fallback | ENG |
| R-12 | Klaint local LLM tool-use reliability is insufficient on CPU; providers cost money | 4 | 4 | Low Test Lab pass rates | Tenant chooses provider explicitly and pays for it; deterministic broker limits blast radius regardless of model quality; no automatic paid inference | FOUNDER (business) + ENG |
| R-13 | **Parlant API churn (realized):** v4 removed strict canned responses, journeys, the evaluations API, the Plan hook and most REST CRUD routes | 5 | 4 | Already happened (v4.0.2, 2026-11-04) | Spike KT-01 decides v4.0.2 versus the v3.3.2 fallback; broker as sole executor; commitment guard; tau2-bench harness independent of Parlant | ENG |
| R-23 | VoiceStudio upstream velocity (about 118 commits/day) and open-core drift (Pro remote workers, cloud sync) | 4 | 3 | Rebase conflicts; features moving behind paid tiers | Pinned fork, scheduled rebase windows, delta register; egress table re-diffed on every rebase | ENG |
| R-24 | Key Arabic TTS donor unmaintained (Chatterbox Multilingual V3 retired upstream in August 2026) | 4 | 3 | No upstream fixes | Treat as a frozen artifact; evaluate `silma-tts` and Piper Arabic voices; fine-tune trigger FT-5 if no permissive option reaches the gate | ENG |
| R-25 | The Wispral repository has no outbound LICENSE | 5 | 4 | Any COPY packet | Founder chooses the Wispral license before code is copied in (Q-01) | FOUNDER |
| R-26 | Windows fixtures that GitHub-hosted runners cannot host (elevated vs medium integrity, secure desktop, audio input) | 4 | 3 | Fixtures skipped in CI | Execution-context tags per packet; recorded manual runs on HW-A; pure tests for PID/HWND reuse | ENG |
| R-27 | No clean-VM capability on Windows 11 Home (no Hyper-V Manager or Sandbox) | 4 | 3 | G-INSTALL cannot run | Second machine or a free cloud VM the founder already has; otherwise record G-INSTALL as `BLOCKED_EXTERNAL` | FOUNDER |
| R-28 | Klaint inference cost and latency on CPU (several LLM calls per turn; BLOCK mode prevents streaming) | 4 | 4 | KT-01 p95 turn latency | One owned inference server; tenant-configured provider by explicit choice; text MVP tolerates non-streamed replies | ENG + FOUNDER |
| R-14 | Voice-cloning misuse despite the consent ledger | 3 | 5 | Abuse reports | Consent evidence required; watermark where supported; provenance sidecars; no public voice sharing in the first release; documented acceptable use | FOUNDER (policy) + ENG |
| R-15 | Privacy law obligations (for example Saudi PDPL, GDPR) for recorded speech, consent panels and Klaint conversations | 3 | 4 | Legal review questions | Data-minimizing defaults; written consent forms; retention controls; legal review before R2 for Klaint and before recording the panel | FOUNDER |
| R-16 | Same-author review mistaken for independent review | 3 | 4 | Reviews written by the plan's authoring agent | Reviews record the reviewer identity and independence class; required gates demand a reviewer independent of the author | ENG |
| R-17 | Scope creep: every competitor feature pulled into MVP | 4 | 4 | Packets added without tier | Tiers in the [capability catalog](../../docs/strategy/WISPRAL_PRODUCT_VISION.md); a packet enters a phase only with its tier; "smaller excellent product" rule | ENG |
| R-18 | Accessibility regressions in donor UIs (custom widgets without semantics) | 3 | 3 | Accessibility Insights failures | G-A11Y gate from R2; component kit with tested semantics | ENG |
| R-19 | Supply-chain compromise in Python/npm dependency trees of donors | 3 | 5 | Audit findings | Lockfiles, audits, minimal extras, pinned model artifacts, SBOM; no auto-download | ENG |
| R-20 | Reviewer/CI capacity (governance latency) dominates elapsed time | 5 | 3 | PRs waiting on review | Small packets, batched reviews by phase, explicit review SLAs set by the founder | FOUNDER |
| R-21 | Over-reliance on the local `d1-local` classifier for review triage | 2 | 4 | d1 verdicts used as approval | d1 triage only; never approval or security clearance (founder note: it misclassified an auth bypass) | ENG |
| R-22 | Free-tier GPU quotas change or disappear | 3 | 2 | Quota errors | GPU cells are optional evidence; CPU cells remain the primary decision basis for defaults | ENG |

## Dependencies

| Dependency | Needed by | Status |
| --- | --- | --- |
| Founder ratification of the governance amendment(s) | Every product packet | Pending (FOUNDER) |
| Independent reviewer availability (human or agent of a different lineage) | Every gated merge | To be named by the founder |
| Founder decision on code-signing path and budget | R2 (private beta) | Pending |
| Consent program for the Arabic/English speech panel (forms, volunteers, storage) | WB-AR claims, WB-TTS cloning tests | Pending |
| Trademark clearance | R3/R4 | Pending |
| Donor repositories remain accessible at pinned SHAs | All fork packets | Verified on 2026-11-08 for the pins listed in the [source decision matrix](SOURCE_DECISION_MATRIX.md) |
