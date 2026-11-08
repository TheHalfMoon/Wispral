# Independent review record

**What these reviews are.** Six review passes ran on 2026-11-08 against the planning package, each as a separate agent with its own context, a non-overlapping scope and no access to the author's drafts beyond the files. They are **fresh-context reviews by the same model family (Claude) as the author**. Under the plan's own proposed Governance item 7 they do **not** count as qualifying independent reviews: constitution-required reviews of G1, C1, C2, G2, D0G and B2-R17 still need the founder, a founder-named human, or a different-vendor reviewer. The local `d1-local` classifier was not used to approve or clear anything. Earlier external review evidence (Opus review of PR #124, PR #125) is preserved unchanged in `research/reviews/2026-10-21-opus-pr124/`.

## Reviewers

| Pass | Scope | Verdict before repair | Findings |
| --- | --- | --- | --- |
| Core audit (research pass) | Contracts versus founder-repo donors | 23/25 invalid donor-informed records accepted by the first contract draft | Contract corrections + `effect_intent` |
| Architecture and performance (`egm-design`) | Duplicated owners, coupling, unrealistic assumptions, performance | Sound with fixes; Klaint unsound until fixed | 1 BLOCKER, 8 MUST FIX, 3 SHOULD |
| Copy-first and scope (`egm-zoom-out`) | Rebuilding despite donors, over-scoped MVPs, ordering | Not the smallest defensible plan | 0 BLOCKER, 6 MUST FIX, 5 SHOULD, 1 OPTIONAL |
| Testability and readiness (`egm-implementation-readiness`) | Executable packets, dependencies, CI realism | Not ready | 3 BLOCKER, 7 MUST FIX, 2 SHOULD |
| Security and governance integrity (general-purpose) | Trust boundaries, consent, tenancy, Principle XVII loopholes | Not ready to ratify | 2 BLOCKER, 8 MUST FIX, 2 SHOULD |
| UX and design (general-purpose) | Workflows, states, accessibility, RTL, identity | Direction solid, not ready to build | 1 BLOCKER, 8 MUST FIX, 2 SHOULD |

## Dispositions

`FIXED` means the change is in this branch; the location is given. `RETAINED` means intentionally not changed, with the reason.

### Blockers

| # | Source | Finding | Disposition |
| --- | --- | --- | --- |
| B1 | Security 1 | Transitional clause too broad; freeze verifier masks later checks; entry paths only guarded by candidate-controlled workflows | FIXED: clause limited to G1 and C1 with path, all-other-checks-green and base-pinned preservation-checker conditions ([reconciliation §3](../../docs/strategy/WISPRAL_GOVERNANCE_RECONCILIATION.md#3-proposed-text-for-g1-constitution-021--030)); trusted coverage extended in C2 (§4.2 item 4) |
| B2 | Security 2 | Principle XVII arguable, no scope exclusions, weak "solely", missing XVI.3/XVI.5 language | FIXED: scope limited to benchmark/governance controls; security, consent, tenancy, egress, credential, release and signing controls excluded; reproduction required; counterfactual proof of "solely"; XVI.3 description, XVI.5 absent/skipped/pending/cancelled language and the closing "remains blocked" paragraph imported |
| B3 | Testability 1 | C's "B2-owned sections" undefined; F would trip C | FIXED: exact heading allowlist, appended `## Platform frontier` sections, NFC and confusable checks, marker uniqueness, F's literal diff as positive fixture (reconciliation §4.2) |
| B4 | Testability 2 | No reviewer definition or route | FIXED: proposed Governance item 7 defines qualifying review; founder decision 2 lists zero-cost routes (§7) |
| B5 | Testability 3 | GRAIN packets without a path to D0G; GRAIN_BENCH never opened | FIXED: D0G opens GRAIN_BENCH with BM-00 preregistration; explicit D0G edges; validator now enforces reachability for GRAIN_* (to D0G) and RESEARCH_000E/F (to F) |
| B6 | Architecture 1 | Same-tenant customer impersonation via the unauthenticated plugin tool server | FIXED: plugin server off; consequential tools only via in-process ToolService; principal from session store plus mandatory per-call token; forged-customer fixture (KT-01, KT-03; security KL-T3) |
| B7 | UX 1 | Capsule recovery actions unreachable by keyboard and screen readers | FIXED: last-outcome shortcut opening the quick panel, tray "Needs attention", persistence rules, expanded layout with 24 px targets, journey J9 ([WisprSide spec §2.1](../../docs/design/WISPRSIDE_UX_SPEC.md#21-expanded-capsule-and-keyboard-recovery)) |

### Must fix

| Source | Finding | Disposition |
| --- | --- | --- |
| Arch 2 | No Klaint inference topology; webhook retries | FIXED: owned inference server row, KT-01 measures calls per turn and p95, KT-07 immediate ack + queue |
| Arch 3 | Hidden gateway and shared Chatwoot; two cancel owners | FIXED: owner-table rows; single cancellation owner per product |
| Arch 4 | Studio first-run runtime downloads | FIXED: ST-D01 pinned runtime bundles or one explicit download; runtime manifest; ≤ 2 environments |
| Arch 5 | Effect intent per dictation unusable | FIXED: text delivery recorded as `delivery_outcome`; `effect_intent` limited to Studio export and Klaint |
| Arch 6 | Windows identity for UWP/Chromium; UIA stalls | FIXED: `focus_element`, `hosted_process_instance`, ≤ 100 ms UIA timeouts, activation p95 measurement (SD-M3) |
| Arch 7 | 64-bit encoding and digest canonicalization | FIXED: decimal-string `start_generation`; RFC 8785, NFC and path rules in the contracts README |
| Arch 8 | Untyped envelope payload; stale "7 schemas" | FIXED: per-event `$ref` payload typing with fixtures; counts updated |
| Arch 9 | Rewrite LLM owner and latency | FIXED: supervised server or labelled user-owned endpoint; p95 rewrite latency is a must-pass gate (SD-R2) |
| Copy 1 | Rust Core crates without an MVP consumer | FIXED: deferred to CORE-R1 (P7); Klaint policy in Python |
| Copy 2 | Build-new register incomplete | FIXED: register rows BN-08..BN-12; validator requires a register row for every BUILD_NEW packet |
| Copy 3 | Timeline wrongly credited | FIXED: ST-06 is the segment timeline; multitrack is tier L with Voicebox as donor candidate |
| Copy 4 | Klaint MVP builds tier-S features | FIXED: KT-02 and KT-10 moved to P7; MVP is one hardened process |
| Copy 5 | Console duplicates donors in the MVP | FIXED: DS-08 moved to P7; MVP uses Chatwoot, local traces, tau2 reports and a ledger query CLI |
| Copy 6 | Phase order contradictions | FIXED: roadmap regenerated from the packet graph; one concurrency rule shared by D0G and the roadmap |
| Test 4 | Missing edges and double ownership of fixtures | FIXED: B2-R17 → R; SD-M1 → BM-01; SD-M4 → BM-02; `tests/windows-fixtures/` owned by BM-02 only |
| Test 5 | Definitions of done depending on later packets | FIXED: DoD is the packet's own artifact and green tests |
| Test 6 | Windows fixtures not runnable on hosted runners or Windows 11 Home | FIXED: execution-context tags; WFP 5156 / ETW attribution; CLI input path; manual HW-A runs; risks R-26/R-27 |
| Test 7 | Baseline execution context | FIXED: fork repositories, disabled upstream release jobs, evidence paths, OS per baseline, offline verification |
| Test 8 | KT-01 authority and LLM backend | FIXED: RESEARCH_000E, research path, deterministic fake backend plus one pinned local CPU model |
| Test 9 | CORE-01 inputs and package path | FIXED: `contracts/v1/` package with VERSION; gap probes committed as fixtures in CORE-01 acceptance |
| Test 10 | Oversized packets | FIXED: C split into C1/C2; CORE-08 moved to P8 with two profiles; CORE-09 dropped; BM-00 preregistration before BM-03 |
| Sec 3 | Freeze checker run from candidate code | FIXED: base-defined `pull_request_target` job mandatory in C1 |
| Sec 4 | Marker injection outside B2 sections | FIXED: markers exactly once inside B2-owned sections, with negative fixtures |
| Sec 5 | #118 relabeled; preserved reds normalized | FIXED: #118 recorded as an exception decided on fresh evidence; product packets require all checks green; owner-act recording; aggregator ruleset recommended |
| Sec 6 | Same-tenant impersonation via port 8818 | FIXED (see B6) |
| Sec 7 | Counterparty can approve an ASK | FIXED: `confirmation.confirmer_kind` operator or step-up-verified holder; conversation text never confirms (schema + fixtures) |
| Sec 8 | Idempotency key scope, uniqueness, verdict binding | FIXED: key = H(tenant, conversation, tool, canonical args); uniqueness and verdict binding enforced by bundle fixtures |
| Sec 9 | Replay keyed on an unsigned header | FIXED: replay cache keyed on H(ts‖body) or signature plus signed message id; mutated-header fixture |
| Sec 10 | Self-asserted stock voices; no reference digest; fail-open rollback | FIXED: catalog-bound stock voices; `reference_artifact_digest` and `speaker_match`; ST-D03 rollback disables cloning |
| UX 2 | Missing WisprSide states; lost first words while arming | FIXED: six new states; audio buffered from key-down |
| UX 3 | Receipt too brief; no undo | FIXED: ≥ 3 s plus title length, persistent tray tooltip, Undo insert where verifiable |
| UX 4 | Onboarding conflicts | FIXED: background download, privacy before practice, simulated refusal demo, real-app step, skip and resume |
| UX 5 | Shortcut conflicts | FIXED: Ctrl+R, list-scoped Delete with Undo, focus-scoped single-key Studio shortcuts, physical key codes, Ctrl+K label |
| UX 6 | Focus, selection and accent collisions | FIXED: dedicated focus ring token with gap, selection/disabled/input tokens, Studio accent changed to plum, wisp to orchid, full forced-colors mapping, hue-separation lint (`PASS` 94 contrast + 40 hue checks) |
| UX 7 | Klaint approvals queue, health and takeover conflicts | FIXED: approvals queue, health banners, conflict and failure states |
| UX 8 | Why-panel jargon and untranslatable verdict codes | FIXED: plain-language summary first, Details disclosure with glossary, localized verdict words, LTR-isolated ids |
| UX 9 | Studio first-run and take history | FIXED: first-run wizard with profile, take history with A/B, stale regeneration, dubbing stage staleness |
| UX 10 | Review method would let bad UI through | FIXED: state-freeze capture, state sequences, all contrast themes, scales and text size, rubric anchors, non-builder scorer, release gate, diverse participants |

### Should improve and optional

| Source | Finding | Disposition |
| --- | --- | --- |
| Arch 10 | Co-running products on HW-A | FIXED: WB-CORUN / BM-05; cores−2 and free-memory refusal |
| Arch 11 | In-process cancellation | FIXED: mandatory escalation in the cancellation contract and ST-D05 |
| Arch 12 / Copy 7 | Chatterbox adapter versus built-in engines | FIXED: built-in VoxCPM2 and MOSS-TTS-Nano benchmarked first; ST-D06 conditional in P7 |
| Copy 8 | Studio bridge and local-API profiles without MVP users | FIXED: moved to P8; MVP local-API hardening folded into ST-D01 and SD-M2 |
| Copy 9 | Shared cancel harness | FIXED: dropped; per-product fixtures against the transition table |
| Copy 10 | Voicebox versus VoiceStudio | FIXED: ST-D00b comparison before committing the fork |
| Copy 11 | Custom token pipeline and gallery | FIXED: tokens and components built in the Handy fork (DS-05); DS-02/DS-04 removed |
| Copy 12 | Tier mismatches; contract count | FIXED: SD-08, SD-19, SD-11 retiered; tier-phase check added to the validator; counts corrected |
| Test 11 | Rust commands misquoted; workspace ownership | FIXED: AGENTS §7 quoted verbatim; first Rust packet owns the workspace |
| Test 12 | Subjective acceptance | FIXED: DS-01 reader count and criteria; DS-05 A/B with ≥ 5 participants; manual HW-A contexts; CORE-00 file paths; licence decision moved to a gate row |
| Sec 11 | Pickle, remote code, unsigned electron-updater manifests, key custody | FIXED: manifest `serialization` and `trust_remote_code`; Authenticode `publisherName` pinning; HSM or managed signing |
| Sec 12 | No local-API boundary | FIXED: boundary B11 with fixtures |
| UX 11 | Arabic sizes, meter direction, truncation, digits | FIXED: 13 px Arabic minimum with size-adjust, centre-out meter, isolate-then-truncate, Western tabular digits in Klaint tables |
| UX 12 | Generic look risk | FIXED: signal-line component tokens, banned-pattern list, why panel as Klaint's signature, unbranded recognition test |

**Retained:** none of the BLOCKER or MUST FIX findings were retained unaddressed. The plan's own limitation remains: these reviews are same-family fresh-context reviews, and governance-required qualifying reviews have not happened.

## Second-round check

A focused re-check judged all seven blocker fixes partially resolved and named the remaining gaps; every gap was then fixed. Details: [PLAN_VALIDATION.md](PLAN_VALIDATION.md#second-round-blocker-check). A third round was not run; the governance text still requires a qualifying review before ratification.
