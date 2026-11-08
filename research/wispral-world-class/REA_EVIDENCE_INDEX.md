# Evidence index

Every important claim in the planning package traces to one of these artifacts. Evidence classes: `SOURCE_VERIFIED` (read at an exact revision), `RUNTIME_OBSERVED` (GitHub API or live page), `REPRODUCED` (run locally), `DOCUMENTED` (vendor or upstream document), `NOT_RUN`, `BLOCKED_EXTERNAL`, `REJECTED`.

## Executed in this mission (2026-11-08)

| Evidence | Class | Artifact | Result |
| --- | --- | --- | --- |
| PR #124 REA bundle integrity on the consolidated branch | REPRODUCED | `research/rea/2026-10-21/validate_research.mjs` | PASS (54 files, 132 + 75 rows) |
| Design-token contrast (WCAG 2.2 AA, light + dark, canvas/surface/sunken) | REPRODUCED | [check_contrast.mjs](../../docs/design/tokens/check_contrast.mjs) | PASS: 94 contrast pairs + 40 hue-separation checks (after three forward fixes, all recorded) |
| Core contract conformance (shape, runtime, sequence) | REPRODUCED | [run_conformance.py](../../docs/engineering/contracts/run_conformance.py) | PASS: 8 schemas, 94 cases, 10 sequences, 4 cross-record bundles |
| Plan validator (packet graph, build-new justifications, links/anchors, names, claims) | REPRODUCED | [validate_plan.mjs](validate_plan.mjs) | See [PLAN_VALIDATION.md](PLAN_VALIDATION.md) |
| B2R16 verifier on four heads | REPRODUCED | [verify_b2r16_repro.txt](evidence/governance/verify_b2r16_repro.txt) | FAIL (range drift) everywhere |
| Workflow trigger and gate simulation | REPRODUCED | [trigger_matrix.txt](evidence/governance/trigger_matrix.txt), [scope_gate_sim.txt](evidence/governance/scope_gate_sim.txt), [run_inline_gate.py](evidence/governance/run_inline_gate.py) | Matches CI on #126 and #120 |
| #126 failing CI logs | RUNTIME_OBSERVED | [pr126_failed_logs.txt](evidence/governance/pr126_failed_logs.txt) | Exact failing assertions |
| #126 preservation tests | REPRODUCED | [pr126_tests.txt](evidence/governance/pr126_tests.txt) | 7/7 PASS |
| Donor drift and re-pins (Handy, OpenWhispr, VoiceInk, FreeFlow) | SOURCE_VERIFIED / REPRODUCED | [WisprSide report](evidence/research-reports/WISPRSIDE_SOURCE_RESEARCH.md) | Re-pin Handy `73cc8579`; CI green 9/9 via API |
| Handy default egress inventory | SOURCE_VERIFIED | WisprSide report §2.6 | One silent default request (update check) |
| VoiceStudio drift, egress, fit-guard and Arabic-lexicon probes | SOURCE_VERIFIED / REPRODUCED | [WisprStudio report](evidence/research-reports/WISPRSTUDIO_SOURCE_RESEARCH.md) | Re-pin `200286cc`; consent unchecked; 5 invalid fit inputs accepted; clitics missed |
| Parlant v4 qualification, Pipecat, Chatwoot, Botpress, tau2-bench | SOURCE_VERIFIED | [Klaint report](evidence/research-reports/KLAINT_SOURCE_RESEARCH.md) | Parlant 4 breaking; bypass paths; no tenancy |
| Klaint competitors (11 vendors, 70 pages) | DOCUMENTED | Klaint report §5 | Gaps: self-host, Arabic dialects, replayable sims, per-action audit |
| Founder repositories and Core contract gap probe | SOURCE_VERIFIED / REPRODUCED | [Core report](evidence/research-reports/CORE_FOUNDER_REPOS_RESEARCH.md) | 23/25 gap records accepted by first draft → contracts revised |
| Models and Arabic datasets (14 modalities) | DOCUMENTED / SOURCE_VERIFIED | [Models report](evidence/research-reports/MODELS_ARABIC_RESEARCH.md) | License traps; 2026 Arabic ASR models; datasets mostly NC |
| Design references, Windows/macOS/Linux platform facts | DOCUMENTED | [Design/platform report](evidence/research-reports/DESIGN_PLATFORM_RESEARCH.md) | 362 DOCUMENTED + 125 NOT_VERIFIED tags |
| Reference hardware | RUNTIME_OBSERVED | [CURRENT_STATE_INVENTORY.md](CURRENT_STATE_INVENTORY.md) | CPU-only HW-A |

## Inherited (PR #124 and PR #125, 2026-10-21)

| Evidence | Class | Artifact |
| --- | --- | --- |
| 96/96 transplant source anchors re-verified at old pins | REPRODUCED (Opus) | `research/reviews/2026-10-21-opus-pr124/pin-verification-results.txt` |
| OpenWhispr 17 pure tests | REPRODUCED | `research/rea/2026-10-21/reproduce_ink_pure_units.mjs` |
| Fit-planner input probe | REPRODUCED | `research/reviews/2026-10-21-opus-pr124/fit-planner-input-probe-results.txt` |
| Competitor public-page observations | RUNTIME_OBSERVED / DOCUMENTED | `research/rea/2026-10-21/official-peer-observations.json`, `rea-runtime-observations.json` |

## Not run (honest gaps)

Donor builds and test suites (all three forks); any audio, microphone, model inference, GPU or TTS quality run; native text insertion; packet-capture egress tests; competitor product trials; Parlant, Pipecat or Chatwoot runtime; Arabic panel recording; code signing; clean-machine installs; REA tooling (`morluto/rea`) runs in this pass (PR #124 recorded its earlier REA observations); external human review. All are mapped to packets in [WISPRAL_IMPLEMENTATION_PACKETS.md](../../docs/engineering/WISPRAL_IMPLEMENTATION_PACKETS.md).
