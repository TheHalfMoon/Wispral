"""Single source for the Wispral implementation packets.

Usage (from repository root):  python -I research/wispral-world-class/build_packets.py
Writes research/wispral-world-class/packets.json and docs/engineering/WISPRAL_IMPLEMENTATION_PACKETS.md.
Every open packet is a CANDIDATE: status DRAFT, ready=false. Readiness comes only from the named authority.
Packets already merged on canonical main carry status MERGED and a merged record; ready stays false.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

SHA = {
    "wispral": "edacdf7504302cc91ff7138bc6ac2d391e4df1f4",
    "pr126": "a97d596bfc9a027bc6c71747b11d94de14f3e838",
    "handy": "73cc8579cff74e97e08de9d86035a92e4335ff7f",
    "freeflow": "37786464bb2422c58313d7456fe7191d115d0d18",
    "openwhispr": "cb08c411dd008c57e4f0a8193756d6b5812479fd",
    "safeevidence": "f05bc006185d67f13ca00ecc7b697c6aef0703dc",
    "orcel": "f0b78e6544cf6ea9c2457a6b6f483490c7bd0f6f",
    "sentrdel": "f5747319a50831ef7cee983d253c0ca5503c9a64",
    "ascout": "48902389ec37019845fd67c8b8c53c5f499ffc85",
    "ninerr": "616bafaa26a58476bb2e3ee876b28e13ac1348f3",
    "acp": "050cd94c081056ace37a7b89abfed7f6220b47eb",
    "voicestudio": "200286ccff6f28faaf51bb08b2a5b54c460b39f4",
    "chatterbox": "5de7a54aa4e5e2baadb0182dde554908b48b85c2",
    "parlant": "2a463ccd10eaf0d70d42731705f4f00ef066bee8",
    "parlant_v3": "61bba3b2b3fffd677d345e393e8c942dbd400297",
    "pipecat": "fda1d5e0cde9625c8dcef7b653ed731c2ce63672",
    "chatwoot": "caab07a8f00032d5205b5a5d7e2eb0ba2f3d2d82",
    "botpress": "956bcdef7a8f6499519e28ec5dda6e3ed3c96ad8",
    "tau2": "033bf082f48e4a3c6a1256208e93cf2ce9c3bb6f",
    "stdwebhooks": "ab6844147ce9cdb0d2dbf2e60d1ea85001fd2554",
    "voicebox": "8af7efe62fab8d33e2a5dfbedabaa45f68a5184f",
}
REPO = {
    "wispral": "TheHalfMoon/Wispral", "pr126": "TheHalfMoon/Wispral", "handy": "cjpais/Handy", "freeflow": "zachlatta/freeflow",
    "openwhispr": "OpenWhispr/openwhispr", "safeevidence": "TheHalfMoon/SafeEvidence", "orcel": "TheHalfMoon/Orcel",
    "sentrdel": "TheHalfMoon/Sentrdel", "ascout": "TheHalfMoon/Ascout", "ninerr": "TheHalfMoon/Ninerr",
    "acp": "agentclientprotocol/rust-sdk", "voicestudio": "debpalash/VoiceStudio", "chatterbox": "resemble-ai/chatterbox",
    "parlant": "emcie-co/parlant", "parlant_v3": "emcie-co/parlant", "pipecat": "pipecat-ai/pipecat", "chatwoot": "chatwoot/chatwoot",
    "botpress": "botpress/botpress", "tau2": "sierra-research/tau2-bench", "stdwebhooks": "standard-webhooks/standard-webhooks", "voicebox": "jamiepine/voicebox",
}


def D(key, *paths):
    return {"repo": REPO[key], "sha": SHA[key], "paths": list(paths)}


AUTHORITIES = {
    "FOUNDER_RATIFICATION": "Repository owner ratifies a constitutional amendment after independent review of the exact range (Constitution Governance 1-4).",
    "XVII_CORRECTION": "Principle XVII control-correction lane created by G1 (preserved red results, tamper-negative proof, independent review, guarded merge, canonical exercise, ledger).",
    "GOVERNANCE_REVIEW": "Ordinary governance or reconciliation PR with review; only after C so no unlawful red check remains.",
    "B2_RECOVERY_V2": "Existing specs/000B2-public-corpus-bakeoff/recovery-v2.md authority for B2 successor tasks; unchanged by this plan.",
    "RESEARCH_000E": "Research Grain opened by F under 000E (platform and native feasibility). Disposable baselines only; no product, installer or release authority.",
    "RESEARCH_000F": "Research Grain opened by F under 000F (dependency, license and provenance intake). Records only.",
    "DECISION_000G": "The 000G decision PR that selects capability-specific Grains from canonical evidence: GRAIN_CORE, GRAIN_DESIGN, GRAIN_BENCH and at most two product Grains at once (GRAIN_SIDE plus GRAIN_STUDIO or GRAIN_KLAINT_TEXT).",
    "GRAIN_CORE": "Product Grain for shared contracts and the policy library, selected by the 000G decision.",
    "GRAIN_SIDE": "Product Grain for WisprSide Windows MVP, selected by the 000G decision.",
    "GRAIN_STUDIO": "Product Grain for WisprStudio MVP, selected by the 000G decision.",
    "GRAIN_KLAINT_TEXT": "Product Grain for the Klaint text-agent MVP, selected by the 000G decision.",
    "GRAIN_DESIGN": "Design-system Grain selected by the 000G decision alongside the first product Grain.",
    "GRAIN_BENCH": "Benchmark Grain with its own preregistration; never modifies the frozen B2 experiment.",
    "SPEECH_EVIDENCE": "Speech-bearing packet: additionally needs a qualified speech-evaluation Grain (new cells) or the canonical B2/B4 disposition.",
    "RELEASE_GREEN_LIGHT": "Any distribution beyond the founder's machines: release gates plus the founder's explicit green light.",
    "LATER_HORIZON": "Coarse future work; must be refined into a Grain when its dependencies are verified.",
}

PHASES = [
    {"id": "P0", "title": "Authority and CI reconciliation", "exit": "G1, C, R, P, G2 and F merged with recorded evidence; B2R17 requalified independently; 000G decision PR opens the first product Grains."},
    {"id": "P1", "title": "Source-fork baseline qualification", "exit": "Donor baselines built and their own test suites run at the pins with recorded counts; re-pins and rights recorded; Parlant v4-versus-v3 decided by spike."},
    {"id": "P2", "title": "Shared contracts, design foundations and harnesses", "exit": "Contracts adopted with Rust/Python parity; policy library; journal; egress and delivery harnesses; tokens and component kit."},
    {"id": "P3", "title": "WisprSide Windows MVP", "exit": "Internal alpha (R1): safe target-bound delivery, offline egress proven on the shipped binary, truthful cancel, Arabic text layer."},
    {"id": "P4", "title": "WisprSide release candidate", "exit": "R3 gates: profiles, guarded rewrite, selected-text edits, accessibility, signing, measured Arabic/English cells."},
    {"id": "P5", "title": "WisprStudio MVP", "exit": "R1: local-only fork, permissive default engine, consent ledger with revocation, crash-safe long-form, Arabic TTS route measured."},
    {"id": "P6", "title": "Klaint safe text-agent MVP", "exit": "R1: per-tenant Parlant, broker as sole executor, commitment guard, Chatwoot takeover, tau2-bench suites passing hard gates."},
    {"id": "P7", "title": "Speech, multilingual and integration expansion", "exit": "Voice for Klaint, consented Arabic panel results, developer-agent module, more connectors."},
    {"id": "P8", "title": "SDKs, cross-platform and optimization", "exit": "macOS/Linux cells, SDKs over authenticated local APIs, performance work driven by measured bottlenecks."},
]

PACKETS = []


def P(id, phase, product, subsystem, title, depends_on, decision, authority, affected, acceptance, tests, risks, rollback, dod,
      donor=None, ci=None, estimate="Not estimated (baseline-dependent)", bnj=None, tier=None, register=None, execution=None,
      status="DRAFT", merged=None):
    pk = {
        "id": id, "phase": phase, "product": product, "subsystem": subsystem, "title": title, "depends_on": depends_on,
        "decision": decision, "readiness_authority": authority, "affected": affected, "acceptance": acceptance, "tests": tests,
        "ci_gates": ci or PRODUCT_CI,
        "security_risks": risks, "rollback": rollback, "definition_of_done": dod, "estimate": estimate,
        "status": status, "ready": False,
    }
    if merged:
        pk["merged"] = merged
    if donor:
        pk["donor"] = donor
    if bnj:
        pk["build_new_justification"] = bnj
    if tier:
        pk["tier"] = tier
    if register:
        pk["build_new_register_id"] = register
    if execution:
        pk["execution"] = execution
    PACKETS.append(pk)


GOV_CI = ["Exact-head workflows; the only permitted red checks are those its governing authority preserves, each recorded as an owner act", "Qualifying independent review (proposed Governance item 7)", "Founder approval of the merge"]
PRODUCT_CI = ["All applicable checks green at the exact head; no preserved red checks", "Fresh-context review plus founder merge approval (qualifying review where Governance item 7 requires it)"]
HW_A = "manual:HW-A (founder laptop, Windows 11 Home, medium-integrity user session), evidence recorded under research/wispral-world-class/evidence/"

# ---------------- P0 governance
P("G1", "P0", "governance", "constitution", "Constitution 0.3.0: Principle XVII (narrow over-application correction), transitional clause, Governance item 7 (qualifying review)", [], "GOVERNANCE", "FOUNDER_RATIFICATION",
  ["CONSTITUTION.md"], ["Text as in WISPRAL_GOVERNANCE_RECONCILIATION.md section 3, or a reviewed revision", "Only CONSTITUTION.md changes", "The only red check is verify-b2r16-freeze; every other applicable check succeeds", "Transitional-clause condition (iii): base-pinned preservation checker PASS on the G1 head, run recorded"],
  ["Trigger matrix for this path class (REPRODUCED in evidence/governance)", "Preservation checker from a97d596 with SHA-256 verified, python -I"], ["A broadly worded lane could become a bypass (mitigated by scope exclusions and counterfactual proof)"], "Governed revert PR", "Merged with founder ratification and the owner act recorded", ci=GOV_CI, estimate="0.5 d drafting + review latency", execution=["hosted-ci", HW_A],
  status="MERGED", merged={"pr": 129, "head": "447d7da42edc3f719e94deae7de9d5c20d7f719c", "merge": "8d52a4579a0b1c6555cbe8443027c1950493b326", "date": "2026-11-08",
                           "note": "Owner act on 'skip review and go ahead'; qualifying review and transitional condition (iii) reviewer reproduction waived and recorded on #129; to be ratified by A040"})
P("C1", "P0", "governance", "trusted controls", "XVII correction 1: B2R16 freeze preservation run from a base-defined pull_request_target job", ["G1"], "GOVERNANCE", "XVII_CORRECTION",
  [".github/workflows/000b2-public-b2r16-freeze.yml", "research/000b2-public/verify_b2r16_preservation.py", "research/000b2-public/test_b2r16_preservation.py", "research/control-repairs/2026-11-*/**"],
  ["#126 checker with fixes (test pin reachable from main, dispatch exercise, XVII framing)", "G1 condition (iii) on C1: every other frozen path keeps its blob and mode from 885307429ec8; C1 checker and tests pass on its head; workflow_dispatch run on C1's exact head succeeds", "Historical B2R16 PASS output at ac9f7ce byte-identical", "Each preserved red has a counterfactual run (control bytes reverted) in which it disappears and nothing else changes"],
  ["#126 seven-group suite from base-pinned code", "Counterfactual runs", "Gate harness from evidence/governance"], ["Candidate-controlled checker (removed: base-defined job)"],
  "Governed revert restores the original workflow; preserved evidence remains", "Merged; post-merge workflow_dispatch exercise on the merge SHA recorded",
  donor=D("pr126", ".github/workflows/000b2-public-b2r16-freeze.yml", "research/000b2-public/verify_b2r16_preservation.py", "research/000b2-public/test_b2r16_preservation.py"), ci=GOV_CI, estimate="1 d + review latency", execution=["hosted-ci", HW_A],
  status="MERGED", merged={"pr": 130, "head": "cabf4e5d96ab03d38a74ee4e5986be17a26f5e74", "merge": "5879c43c7a389bd460955f2e181e8bd70f0ecee5", "date": "2026-11-08",
                           "note": "Qualifying different-vendor review (DeepSeek V4.1 Flash via OpenCode) APPROVE with 0 blocking after one REQUEST_CHANGES round; freeze push run 42446197959 PASS; recovery push run 42446198003 FAIL as the declared preserved scope failure"})
P("A040", "P0", "governance", "constitution", "Constitution 0.4.0 (#133): harden Principle XVII after the post-merge audit (A1-A4) and ratify the waived #129 review", ["C1"], "GOVERNANCE", "FOUNDER_RATIFICATION",
  ["CONSTITUTION.md"],
  ["Item 3a: every non-classification invariant stays enforced on every later candidate, including the correction's own verifier and test files", "Item 10: the reconciliation changes records only, proven by a deterministic field diff, with a qualifying review; Frontier sections designated only by constitutional amendment", "A3: an immutable-boundary failure whose only cause is the declared annexed byte change may be preserved, with the immutable list unchanged", "A4: corrections in one closed, owner-confirmed lane share one combined reconciliation", "Text updated for #130 having merged under 0.3.0 (its 'must meet before merge' clause becomes a C2 obligation)", "Only CONSTITUTION.md changes; every applicable check green (the freeze is base-defined since C1)"],
  ["Trigger matrix for CONSTITUTION.md-only changes", "Exact-head checks all green"], ["Lane loosening beyond A3/A4 (mitigated by deterministic proof conditions)"], "Governed revert PR", "Merged with a recorded qualifying review and owner merge act", ci=GOV_CI, estimate="Review latency only (drafted in #133)", execution=["hosted-ci"])
P("C2", "P0", "governance", "trusted controls", "XVII correction 2: non-successor class with exact section allowlist, marker uniqueness and trusted-coverage extension", ["A040"], "GOVERNANCE", "XVII_CORRECTION",
  [".github/workflows/000b2-public-attempt-003-recovery.yml", ".github/workflows/000b2-public-attempt-003-trusted-pr.yml", "research/000b2-public/verify_attempt_002_invalidation.py", "research/control-repairs/2026-11-*/**"],
  ["Rules exactly as in reconciliation section 4.2 (allowlisted headings; appended Platform frontier sections; NFC; confusables; B2 markers exactly once in B2-owned sections)", "PR #120 still passes both gates; F's literal planned diff passes", "Trusted base-defined gate also covers research/000b2-entry/**, research/000b1/** and 000b2-entry-*.yml", "Immutable-control boundary failure preserved only as A040 allows (declared annexed byte change only; immutable list unchanged)", "C1 lessons: in-class corpus with recorded historical verdicts; a negative fixture for every rejecting branch; non-concealment diff pinned by commit SHA; every check skipped by a neutralization run separately; the correction's own verifier and tests equal the trusted revision's bytes"],
  ["Positive: #120, F diff, terminal-state non-successor", "Negative: B2 path, readiness change, .github change, non-allowlisted section edit, reordered or confusable or duplicated heading, injected marker, extra/missing/deleted task paths", "Counterfactual runs for preserved reds"],
  ["Weakening B2 scope enforcement by mistake (mitigated by the negative corpus run from base-pinned code)"], "Governed revert restores the original controls", "Merged; post-merge exercise recorded",
  ci=GOV_CI, estimate="1-2 d + review latency", execution=["hosted-ci", HW_A])
P("R", "P0", "governance", "ledger", "Combined lane reconciliation (XVII item 10, A040 A4): record the G1 waivers, C1, C2 and #118 as an exception with fresh evidence", ["C2"], "GOVERNANCE", "GOVERNANCE_REVIEW",
  ["docs/canonical/TRUSTED_CONTROL_REPAIRS.md (outside every B2 path filter, so no scope gate triggers)", "AGENTS.md (reading-order line only)"],
  ["Records only: no authority, freeze, decode, scoring, readiness, task-scope or completion field changes, proven by a deterministic field diff against the pre-correction base", "G1 waivers (no qualifying review; condition (iii) reviewer reproduction) and their A040 ratification recorded", "C1 and C2 identities, preserved reds (including the recovery push failures on main after C1 and their end after C2), counterfactuals, reviews and ancestry recorded", "#118 recorded as merged with a red required verifier and no approving review, with the trusted checker run on its merge and a qualifying retrospective review; founder decision on the B2R17 frontier recorded"],
  ["No B2 workflow triggers for these paths (precedent #116)", "Field-diff script output attached"], ["Mis-recording history"], "Revert", "Merged with a qualifying review; canonical reread confirms state", ci=GOV_CI, estimate="0.5 d")
P("NOOP", "P0", "governance", "confirmation", "No-op confirmation: an empty-diff pull request against main passes every applicable check, and a push to main is green", ["R"], "GOVERNANCE", "GOVERNANCE_REVIEW",
  ["none (empty commit on a throwaway branch)"], ["Every applicable check green on the empty PR, including the base-defined freeze", "Latest push runs on main all green (recovery gate green after C2)"],
  ["Exact-head check inventory"], ["None"], "Close the throwaway PR", "Recorded in the R follow-up note; the throwaway PR is closed unmerged", ci=GOV_CI, estimate="0.1 d")
P("PLAN", "P0", "governance", "planning", "Merge this candidate planning package (research and docs only) after its qualifying review", ["C1"], "GOVERNANCE", "GOVERNANCE_REVIEW",
  ["docs/strategy/**", "docs/design/**", "docs/engineering/**", "docs/adr/**", "research/rea/**", "research/reviews/**", "research/wispral-world-class/**"],
  ["validate_plan.mjs, check_contrast.mjs and run_conformance.py PASS at the exact head", "Every applicable check green (the freeze is base-defined since C1)", "Qualifying different-vendor review APPROVE with 0 blocking findings, recorded with the exact head"], ["validate_plan.mjs", "check_contrast.mjs", "run_conformance.py", "build_packets.py regeneration diff empty"],
  ["Plan content mistaken for ratified governance"], "Revert (no runtime effect)", "Merged; content remains CANDIDATE until G2 and F", ci=GOV_CI, estimate="Review latency only")
P("G2", "P0", "governance", "constitution", "Constitution 1.0.0: platform thesis (WisprSide, WisprStudio, Klaint), anti-roadmap and A12 dispositions, 000C-000G re-scope", ["R", "PLAN"], "GOVERNANCE", "FOUNDER_RATIFICATION",
  ["CONSTITUTION.md", "AGENTS.md", "docs/canonical/ARCHITECTURE_INVARIANTS.md", "docs/canonical/PROGRAM_ROADMAP.md", "specs/000-founding-research/spec.md", "specs/000-founding-research/plan.md"],
  ["Every contradiction row from PR #124's amendment proposal has a KEEP/REPLACE/RE-SCOPE disposition", "New principles: voice-asset consent, tenant and action authority, copy-first", "States that readiness claim_guards.product_code_authorized=false scopes the B2 lane only"],
  ["Contradiction checklist reviewed semantically (grep is discovery only)"], ["Silent scope expansion"], "Governed major revert", "Merged with founder ratification", ci=GOV_CI, estimate="1-3 d drafting + review latency")
P("F", "P0", "governance", "frontier", "Frontier reconciliation: open the 000E and 000F research Grains; product code stays closed", ["G2", "C2"], "GOVERNANCE", "GOVERNANCE_REVIEW",
  ["specs/CURRENT.md (allowlisted sections and an appended Platform frontier section)", "docs/canonical/CURRENT_STATE.md (allowlisted sections)", "specs/000-founding-research/tasks.md", "specs/000E-platform-feasibility/{spec,plan,tasks}.md (new)", "specs/000F-provenance-intake/{spec,plan,tasks}.md (new)"],
  ["Edits only inside C2's allowlist", "The two new research Grain specs name every research packet they open (CORE-00, SD-M0, ST-D00, ST-D00b, KT-01)", "Product-code gate unchanged except a reference to the 000G decision"],
  ["Both B2 gates pass via the non-successor class", "Content verifiers unchanged versus main"], ["Opening more than named"], "Revert", "Merged; research Grains visible in specs/CURRENT.md", ci=GOV_CI, estimate="0.5-1 d")
P("B2-R17", "P0", "benchmark", "B2 lane", "Requalify PR #120 (B2R17) after C2 and the founder's B2R17 decision", ["C2", "R"], "RESEARCH", "B2_RECOVERY_V2",
  ["PR #120 branch only"], ["Fresh exact-head CI, qualifying review, guarded merge, post-merge recovery run, B2R17-to-B2R18 reconciliation"],
  ["Existing B2 verifiers"], ["Stale evidence reused"], "Per recovery-v2", "B2R17 canonical; no scoring authority added", ci=GOV_CI, estimate="Per recovery-v2")

# ---------------- P1 research baselines
P("CORE-00", "P1", "core", "rights", "Re-pins, rights register and licence-decision gate", ["F"], "RESEARCH", "RESEARCH_000F",
  ["research/wispral-world-class/RIGHTS_REGISTER.md (new)", "research/wispral-world-class/SOURCE_DECISION_MATRIX.md", "research/wispral-world-class/CATALOG_ERRATA.md (new: re-key wepld to Zain)"],
  ["Every new anchor's blob and sha256 re-verified", "FSL-1.1 Orcel files and GPL Yamakan marked reference-only", "Klaint pins incl. tau2-bench and standard-webhooks recorded", "A licence gate row states that no COPY/ADAPT packet may land code until the founder's Wispral outbound-licence decision is recorded (Q-01)"],
  ["Pin verifier (PR #125 verify_transplant_pins.py pattern) on new pins"], ["Licence incompatibility found late"], "Revert registry commit", "Register merged; verifier output committed",
  donor=[D("orcel", "crates/orcel-journal/src/lib.rs"), D("safeevidence", "product/deny.toml"), D("acp", "src/agent-client-protocol/src/concepts/cancellation.rs")], estimate="0.5-1 d", execution=["hosted-ci"])
P("SD-M0", "P1", "wisprside", "fork baseline", "Handy fork baseline at 73cc857: build and run the donor's own suites", ["F"], "FORK", "RESEARCH_000E",
  ["fork repository TheHalfMoon/wisprside (visibility is a founder decision: private Windows Actions minutes count double)", "upstream release, signing and updater workflows disabled in the fork", "research/wispral-world-class/evidence/baselines/handy-73cc857/"],
  ["Unmodified cargo test --locked on hosted Linux and on HW-A (Windows), bun lint, test:keyboard, Playwright: collected/pass/fail/ignored counts recorded", "Unsigned NSIS and MSI built on HW-A", "Bundled DLL list recorded"],
  ["Donor suites as is; failures recorded, not fixed"], ["Native toolchain supply chain (Vulkan SDK, LLVM, ggml); 4 git-sourced crates"], "Delete fork branch", "Baseline manifest committed",
  donor=D("handy", "src-tauri/", "src/", ".github/workflows/"), estimate="1-2 d (estimate)", execution=["hosted-ci:ubuntu", HW_A])
P("ST-D00", "P1", "wisprstudio", "fork baseline", "VoiceStudio fork baseline at 200286c with the fake _echo engine", ["F"], "FORK", "RESEARCH_000E",
  ["fork repository TheHalfMoon/wisprstudio", "research/wispral-world-class/evidence/baselines/voicestudio-200286c/", "NOTICE and per-file grant flags"],
  ["pytest tests, pytest backend/tests, bun run test, check:electron with recorded counts on hosted Linux and on HW-A", "No model or runtime download: HF_HUB_OFFLINE=1 and an egress log with zero model-hub connections"],
  ["Donor suites as is"], ["Heavy dependency closure; first-run runtime downloads (see ST-D01)"], "Discard fork branch", "Baseline manifest committed",
  donor=D("voicestudio", "backend/", "electron/", "tests/"), estimate="1-3 d (estimate)", execution=["hosted-ci:ubuntu", HW_A])
P("ST-D00b", "P1", "wisprstudio", "donor comparison", "Voicebox versus VoiceStudio on MVP-tier capabilities, required fork deltas and dependency size", ["F"], "RESEARCH", "RESEARCH_000E",
  ["research/wispral-world-class/evidence/baselines/studio-lead-comparison.md"],
  ["Scored on ST-01..ST-09 (MVP tier), number and size of required deltas, dependency closure, egress paths and Arabic-capable permissive engines", "VoiceStudio stays the lead unless Voicebox wins on the recorded score"],
  ["Static analysis of both pinned trees"], ["None material"], "Not applicable", "Comparison committed", donor=D("voicebox", "backend/", "README.md"), estimate="1 d", execution=["pure"])
P("KT-01", "P1", "klaint", "dialogue", "Parlant v4.0.2 compatibility spike (fallback v3.3.2) with a deterministic fake LLM backend", ["CORE-00"], "WRAP", "RESEARCH_000E",
  ["research/klaint-spike/ (research path, not a product path)"],
  ["Hooks on_reviewing_tool_calls, on_calling_tools and on_message_generated fire in order", "A BAIL in on_message_generated emits a replacement", "Plugin tool server disabled; a loopback call with a forged customer_id has no effect and returns no data", "LLM calls per turn, p95 turn latency (fake backend and one pinned local CPU model) and idle RSS measured on HW-A", "Decision v4 versus v3.3.2 recorded"],
  ["Ported tests/core/stable/engines/test_hooks.py and tests/sdk/test_hook_results.py"], ["Hook semantics differ from docs"], "Switch pin to v3.3.2", "Spike report and decision committed",
  donor=D("parlant", "src/parlant/sdk.py", "src/parlant/core/engines/compass/hooks.py", "src/parlant/core/engines/compass/loop/base_loop.py"), estimate="2-3 d (estimate)", execution=[HW_A])
P("D0G", "P1", "governance", "000G", "000G decision: select capability-specific Grains from P1 evidence", ["F", "CORE-00", "SD-M0", "ST-D00", "ST-D00b", "KT-01"], "GOVERNANCE", "DECISION_000G",
  ["specs/000-founding-research/tasks.md", "specs/CURRENT.md (allowlisted sections)", "new Grain specs"],
  ["Decision matrix cites 000E/000F evidence and capability-specific 000B/000C/000D dispositions", "Opens GRAIN_CORE, GRAIN_DESIGN and GRAIN_BENCH (with BM-00 preregistration) plus at most two product Grains at once: GRAIN_SIDE and one of GRAIN_STUDIO or GRAIN_KLAINT_TEXT"],
  ["Reviewer confirms every selected packet traces to evidence"], ["Mass-opening packets"], "Revert", "Merged; selected Grains READY", ci=GOV_CI, estimate="1 d + review")

# ---------------- P2 foundations
P("CORE-01", "P2", "core", "contracts", "Adopt the eight candidate contracts as a language-neutral package with the gap-probe corpus", ["D0G"], "ADAPT", "GRAIN_CORE",
  ["contracts/v1/*.schema.json", "contracts/v1/transitions/*.json", "contracts/v1/fixtures/**", "contracts/VERSION (semver)", "contracts/README.md (canonicalization: RFC 8785 JCS, NFC, path normalization)"],
  ["run_conformance.py PASS (94 cases, 10 sequences, 4 bundles today)", "The Core audit gap probes are committed as fixtures with their IDs and each yields its intended verdict"],
  ["run_conformance.py", "build_cases.py regeneration diff empty"], ["Over-constraint breaks adapters"], "Keep v1; new majors in their own directory", "Package merged; tests green",
  donor=[D("ascout", "src/assurance/contracts/engine-descriptor.ts"), D("sentrdel", "crates/sentrdel-policy/src/lib.rs"), D("orcel", "crates/orcel-journal/src/lib.rs")], estimate="1 d", execution=["hosted-ci", "pure"])
P("CORE-07", "P2", "core", "egress", "Egress gates: dependency denial, no-socket checks and a Windows-strength observed-egress harness", ["D0G"], "ADAPT", "GRAIN_CORE",
  ["tools/ci/no_sockets.py", "deny.toml templates", "benchmarks/egress/harness/"],
  ["Positive control reaches the network first", "Process-tree attribution via WFP audit event 5156 or the ETW Kernel-Network provider on Windows; unshare -n on Linux", "Injected reqwest dependency is caught (tamper-negative)", "Session script fixed: 30 minutes as in the release gates"],
  ["Linux variant in hosted CI; Windows variant on HW-A"], ["Windows path weaker than Linux (donor's own label)"], "Gate advisory until the Windows design qualifies", "Harness and gates merged; both variants demonstrated",
  donor=D("safeevidence", "product/deny.toml", "tools/ci/core_no_sockets.py", "tools/ci/ta29_dependency_denial.py", "tools/ci/ta03_isolated.sh", "tools/ci/network_trace_report.py"), estimate="1-2 d", execution=["hosted-ci:ubuntu", HW_A])
P("DS-01", "P2", "design", "typography", "Bilingual font harness and type decision", ["D0G"], "RESEARCH", "GRAIN_DESIGN",
  ["docs/design/fonts/harness.html", "decision record"],
  ["Arabic with tashkeel, mixed code tokens and both digit systems rendered at 12-16 px, 100% and 150% on Windows", "At least 3 native Arabic readers (at least 1 Gulf) score legibility at 13 px, diacritic collision and digit clarity 0-3; decision recorded"],
  ["Screenshot set and scores"], ["OFL reserved-name misuse"], "Fallback stack only", "Decision and screenshots committed", estimate="1 d", execution=[HW_A])
P("BM-00", "P2", "benchmark", "preregistration", "WB-AR pilot preregistration: routes, datasets with licences, sample size, normalizer", ["D0G"], "RESEARCH", "GRAIN_BENCH",
  ["benchmarks/wb-ar/PREREGISTRATION.md"], ["Three candidate local ASR routes named with manifests; permissive datasets named with licence rows; n per segment and normalizer frozen"], ["Reviewer check"], ["Dataset licence misuse"], "Not applicable", "Preregistration merged before any run", estimate="0.5 d", execution=["pure"])
P("BM-01", "P2", "benchmark", "egress", "WB-EGRESS baseline on the unmodified Handy and VoiceStudio forks", ["SD-M0", "ST-D00", "CORE-07"], "RESEARCH", "GRAIN_BENCH",
  ["benchmarks/egress/results/"], ["Observed destinations per scripted 30-minute session recorded for both baselines (expected: Handy update check; VoiceStudio update check, mirrors and runtime installs)"], ["CORE-07 harness"],
  ["OS noise attributed to the app"], "Harness only", "Baseline egress table committed", estimate="1 d", execution=[HW_A])
P("BM-02", "P2", "benchmark", "delivery", "WB-DELIVERY harness and Windows fixture apps against the unmodified Handy baseline", ["SD-M0", "D0G"], "RESEARCH", "GRAIN_BENCH",
  ["benchmarks/delivery/", "tests/windows-fixtures/ (single owner)"],
  ["Text reaches Handy without a microphone via its CLI --transcribe-file", "Focus-steal, close, minimize and virtual-desktop fixtures automated; elevated-window and secure-desktop fixtures run manually on HW-A; PID and HWND reuse covered by pure tests", "Current wrong-target behaviour measured before any delta"],
  ["UIA-verified destination checks"], ["Harness itself steals focus"], "Harness only", "Baseline delivery table committed", estimate="1-2 d", execution=["hosted-ci:windows-latest (Server image, admin)", HW_A, "pure"])
P("BM-03", "P2", "benchmark", "language", "WB-AR pilot on permissive public subsets with three local ASR routes on HW-A", ["BM-00", "SD-M0"], "RESEARCH", "GRAIN_BENCH",
  ["benchmarks/wb-ar/results/"], ["Per-segment results with confidence intervals exactly as preregistered"], ["Preregistered run"], ["Dataset licence misuse"], "Not applicable", "Pilot report committed", estimate="2-3 d", execution=[HW_A])

# ---------------- P3 WisprSide MVP
SIDE = "GRAIN_SIDE"
P("SD-M1", "P3", "wisprside", "egress", "Egress lockdown: update check off by default, cloud LLM providers behind a switch, host shown before download", ["SD-M0", "CORE-07", "BM-01"], "FORK_DELTA", SIDE,
  ["src-tauri/src/settings.rs", "src-tauri/src/lib.rs", "src/components/update-checker/UpdateChecker.tsx", "src-tauri/tauri.conf.json"],
  ["Zero outbound connections from the process tree during install, onboarding and a 30-minute push-to-talk session with a preinstalled model"], ["BM-01 harness", "Default-settings unit test"],
  ["Users miss security updates"], "Flip defaults back", "WB-EGRESS PASS on the exact build", donor=D("handy", "src-tauri/src/settings.rs", "src-tauri/tauri.conf.json"), tier="M", execution=[HW_A, "hosted-ci"])
P("SD-M2", "P3", "wisprside", "hardening", "Remove exec surfaces; non-null CSP; gate media decode; local command surface cannot start capture invisibly", ["SD-M0", "D0G"], "FORK_DELTA", SIDE,
  ["src-tauri/src/transcription_hook.rs", "src-tauri/src/actions.rs", "src-tauri/src/clipboard.rs", "src-tauri/tauri.conf.json", "src-tauri/src/audio/decode.rs", "src-tauri/src/cli.rs"],
  ["Hook file present is never executed", "ExternalScript unreachable", "CSP non-null with UI working; asset scope narrowed", "CLI and single-instance --toggle-transcription always show the capsule and respect pause"],
  ["Unit and Playwright tests; malformed-media corpus if decode kept"], ["CSP breakage"], "Revert commit", "Tests green", donor=D("handy", "src-tauri/src/transcription_hook.rs", "src-tauri/src/clipboard.rs", "src-tauri/src/cli.rs"), tier="M", execution=["hosted-ci"])
P("SD-M9", "P3", "wisprside", "ci", "Windows CI test job wired to the BM-02 fixtures", ["SD-M0", "BM-02"], "FORK_DELTA", SIDE,
  [".github/workflows/test.yml"], ["cargo test runs on windows-latest for every PR touching src-tauri"], ["Workflow run"], ["Runner image drift"], "Remove job", "Green Windows job", donor=D("handy", ".github/workflows/test.yml"), tier="M", execution=["hosted-ci:windows-latest"])
P("SD-M3", "P3", "wisprside", "delivery", "Target binding at activation (HWND, PID + creation time, image path, hosted process, UIA focus element, integrity)", ["SD-M0", "SD-M9"], "BUILD_NEW", SIDE,
  ["src-tauri/src/paste_tx/target.rs (new, pure)", "src-tauri/src/paste_tx/target_windows.rs (new)", "src-tauri/src/actions.rs"],
  ["Binding captured every session; no field text stored; unreadable fields recorded as unknown", "UIA runs on a dedicated thread with timeouts of 100 ms or less; a timeout yields identity_unreadable", "UWP targets bind the hosted process behind ApplicationFrameHost", "p95 activation latency with capture measured on HW-A"],
  ["Pure snapshot tests on Linux CI", "Windows fixtures from BM-02"], ["UIA calls can block on hung targets"], "Feature flag off = copy-only delivery", "Binding fixtures green",
  donor=[D("freeflow", "Sources/AppTextInsertionTarget.swift"), D("openwhispr", "resources/windows-fast-paste.c", "resources/windows-text-monitor.c"), D("orcel", "crates/orcel-platform/src/process.rs")], tier="M", register="BN-01",
  bnj={"inspected": "Handy actions.rs, clipboard.rs and paste_tx (no target identity); OpenWhispr windows-fast-paste.c (HWND only; falls through to the foreground window); FreeFlow AppTextInsertionCore (macOS AX); VoiceInk (macOS)", "why_insufficient": "No donor binds HWND + PID + process start + focused UIA element on Windows and refuses on mismatch", "smallest_missing_capability": "One pure verdict module and one Windows capture module", "adapter_confinement": "New files in paste_tx plus about 20 lines at two call sites", "test_and_maintenance_cost": "Pure tests anywhere; Windows fixtures; small upstream conflict surface"}, execution=["pure", "hosted-ci:windows-latest", HW_A])
P("SD-M4", "P3", "wisprside", "delivery", "Fail-closed verification and refusal (changed, gone, expired, password, read-only, elevated, secure desktop)", ["SD-M3", "BM-02"], "BUILD_NEW", SIDE,
  ["src-tauri/src/clipboard.rs", "src-tauri/src/paste_tx/windows.rs", "src-tauri/src/notices.rs"],
  ["Zero injections in every refusal fixture", "No SetForegroundWindow calls (static test)", "Transcript recoverable in 100% of refusals", "binding_expired limit set from measured p95 plus margin (default 10 s until measured)"], ["Verdict table tests", "BM-02 rerun"],
  ["False refusals in apps without UIA (per-app override with audit entry)"], "Warn-only policy (still never redirect)", "WB-DELIVERY: zero wrong-target",
  donor=D("freeflow", "Sources/AppTextInsertionCore.swift"), tier="M", register="BN-01b",
  bnj={"inspected": "Handy secure_input.rs (macOS hotkey only); OpenWhispr UIA probe (no integrity check)", "why_insufficient": "UIPI blocking is silent and no donor compares integrity levels or refuses on Windows", "smallest_missing_capability": "Integrity comparison, UIA predicate port, ES_PASSWORD check, double re-verification", "adapter_confinement": "Inside the SD-M3 module", "test_and_maintenance_cost": "Elevated and password fixtures, run manually on HW-A"}, execution=["pure", "hosted-ci:windows-latest", HW_A])
P("SD-M5", "P3", "wisprside", "clipboard", "Receipt-based clipboard transaction as the Windows default; no legacy fallback", ["SD-M4"], "FORK_DELTA", SIDE,
  ["src-tauri/src/settings.rs", "src-tauri/src/clipboard.rs"], ["User copy during pending restore preserved", "Text+HTML+image snapshot restored byte-equal", "History-exclusion formats on every write"],
  ["Independent clipboard-reader process test", "Sequence-number race test"], ["Delayed-render data readable by clipboard monitors (documented)"], "Legacy path behind a flag", "Clipboard fixtures green", donor=D("handy", "src-tauri/src/paste_tx/windows.rs"), tier="M", execution=["hosted-ci:windows-latest"])
P("SD-M6", "P3", "wisprside", "delivery", "DeliveryOutcome with partial reporting, written to history after delivery; auto-submit only on PostedAndRead", ["SD-M4", "SD-M5", "CORE-01"], "BUILD_NEW", SIDE,
  ["src-tauri/src/clipboard.rs", "src-tauri/src/input.rs", "src-tauri/src/actions.rs", "src-tauri/src/managers/history.rs"],
  ["Outcome mapping correct on every fixture; partial never retried", "Outcomes validate against delivery_outcome.schema.json"], ["Mapping unit tests", "Receipt fixtures", "History migration up/down"],
  ["Migration rollback on downgrade"], "Down-migration and flag", "Contract fixtures green", tier="M", register="BN-01c",
  bnj={"inspected": "Handy Result<(),String> and TranscriptionOutcome; VoiceInk and FreeFlow vocabularies (Swift)", "why_insufficient": "Handy reports Typed at chord time and has no partial state", "smallest_missing_capability": "One enum, a receipt channel and a chunked surrogate-safe typer", "adapter_confinement": "clipboard.rs, input.rs, actions.rs and one history migration", "test_and_maintenance_cost": "Unit and fixture tests; one migration"}, execution=["hosted-ci:windows-latest"])
P("SD-M8", "P3", "wisprside", "cancellation", "Cancellation completeness with per-product fixtures against the contract transition table", ["SD-M0", "CORE-01"], "FORK_DELTA", SIDE,
  ["src-tauri/src/actions.rs", "src-tauri/src/shortcut/mod.rs", "src-tauri/src/engine_supervisor/supervisor.rs"],
  ["Keyboard cancel works through transcription, post-processing and paste wait", "Late results never injected", "Model-load cancel either escalates (deadline, kill exact instance, observe exit) or is shown as non-cancellable"], ["Coordinator tests", "Sequence fixtures"],
  ["Shortcut re-registration races"], "Revert", "Cancel fixtures green", donor=D("handy", "src-tauri/src/actions.rs"), tier="M", execution=["hosted-ci"])
P("SD-M10", "P3", "wisprside", "packaging", "Wispral-owned identifiers, signing command, updater key and feed; deliberate WebView2 install mode", ["SD-M1"], "FORK_DELTA", SIDE,
  ["src-tauri/tauri.conf.json", "src-tauri/nsis/installer.nsi", "icons"], ["No upstream author identifiers in signing, updater or bundle identifier", "Updater key custody documented outside the repo"], ["Package audit script"],
  ["Key custody"], "Revert config", "Audit green", donor=D("handy", "src-tauri/tauri.conf.json"), tier="M", execution=["hosted-ci"])
P("SD-M11", "P3", "wisprside", "privacy", "History retention choice in onboarding, including keeping no text", ["SD-M0", "D0G"], "FORK_DELTA", SIDE,
  ["src-tauri/src/managers/history.rs", "src-tauri/src/settings.rs", "onboarding"], ["Retention options off / 24 h / 7 d / 30 d honoured for text and audio; deletion verified"], ["Retention tests"], ["Data kept longer than chosen"], "Revert", "Retention tests green", donor=D("handy", "src-tauri/src/managers/history.rs"), tier="M", execution=["hosted-ci"])
P("DS-05", "P3", "design", "wisprside", "Tokens (Tailwind 4 theme variables) and the component kit built in the Handy fork: capsule, receipt, refusal, quick panel, onboarding", ["DS-01", "SD-M6"], "FORK_DELTA", SIDE,
  ["src/overlay/**", "src/components/**", "src/styles/tokens.css"],
  ["check_contrast.mjs PASS for the shipped tokens", "Screenshot and state-sequence matrix; rubric 3 on state clarity and keyboard path, at least 2 elsewhere, scored by a non-builder", "Narrator and NVDA announce every capsule state; journeys J7 and J9 pass", "Listening-colour A/B with at least 5 participants (metric: correct state identification and time)"],
  ["Screenshot capture", "Accessibility Insights", "Manual NVDA/Narrator scripts on HW-A"], ["None material"], "Revert UI commits", "G-SHOTS and G-A11Y evidence for R1", donor=D("handy", "src/overlay/RecordingOverlay.tsx"), tier="M", execution=[HW_A])

P("SE-01", "P4", "governance", "speech evidence", "Speech-evaluation Grain decision: opens new speech cells (WB-AR, panel) without touching the frozen B2 experiment", ["D0G", "BM-03"], "GOVERNANCE", "DECISION_000G",
  ["specs/CURRENT.md (allowlisted sections)", "new speech-evaluation Grain spec"], ["States which speech-bearing packets it opens (SD-R9, BM-04) and that B2 ATTEMPT-003 is unchanged", "Cites the BM-03 pilot and its preregistration"],
  ["Reviewer confirms no B2 artifact changes"], ["Reinterpreting frozen B2 results"], "Revert", "Merged; speech cells READY", ci=GOV_CI, estimate="0.5 d + review")
P("D1G", "P4", "governance", "000G successor", "Second product decision: opens whichever of GRAIN_STUDIO or GRAIN_KLAINT_TEXT the 000G decision did not", ["D0G", "SD-M6"], "GOVERNANCE", "DECISION_000G",
  ["specs/CURRENT.md (allowlisted sections)", "Grain spec"], ["Opens the second product Grain only when WisprSide's MVP delivery core (SD-M6) is verified and capacity exists; respects the two-product concurrency rule"],
  ["Reviewer confirms evidence"], ["Opening both at once without capacity"], "Revert", "Merged; second product Grain READY", ci=GOV_CI, estimate="0.5 d + review")

# ---------------- P4 WisprSide RC
P("SD-R1", "P4", "wisprside", "profiles", "App-aware profiles from exe and class only (no screenshots)", ["SD-M3"], "COPY", SIDE,
  ["src-tauri/src/settings.rs", "src-tauri/src/clipboard.rs"], ["Profile chosen from exe_path + class only; terminals get Ctrl+Shift+V"], ["Mapping tests"], ["Spoofable exe names (profiles never grant authority)"], "Disable profiles", "Profile fixtures green",
  donor=D("openwhispr", "resources/windows-fast-paste.c"), tier="S", execution=["pure"])
P("SD-R2", "P4", "wisprside", "rewrite", "Local LLM cleanup and backtrack with output guard; supervised local server or user-owned endpoint", ["SD-M6", "SD-M1"], "ADAPT", SIDE,
  ["src-tauri/src/actions.rs", "src-tauri/src/llm_client.rs", "src-tauri/src/engine_supervisor/**"],
  ["Raw kept; diff shown; one-key revert", "Zero silent distortions on the meaning-preservation set", "p95 rewrite latency on HW-A within the preregistered budget (must-pass)", "A bundled llama.cpp-compatible server runs under the engine supervisor with a manifest row; an external user-owned server is labelled and excluded from offline claims"],
  ["Golden fixtures; ported validator tests"], ["Prompt injection from dictated text"], "Toggle off", "Meaning-preservation panel green", donor=D("openwhispr", "src/utils/cleanupOutput.ts"), tier="S", execution=[HW_A, "pure"])
P("SD-R3", "P4", "wisprside", "selection", "Selected-text rewrite via UIA TextPattern with preview and confirm in the quick panel", ["SD-M4", "SD-R2"], "BUILD_NEW", SIDE,
  ["src-tauri/src/paste_tx/selection_windows.rs (new)"], ["Selection read without clipboard mutation; replacement only after confirm and re-verify", "Refuse when TextPattern is absent"], ["Win32 Edit, RichEdit and WebView2 fixtures"],
  ["Reading sensitive selections (per-app consent)"], "Disable feature", "Selection fixtures green", tier="S", register="BN-09",
  bnj={"inspected": "OpenWhispr synthetic Ctrl+C selection (mutates the clipboard); VoiceInk and FreeFlow (macOS AX)", "why_insufficient": "No donor reads a Windows selection without touching the clipboard", "smallest_missing_capability": "UIA TextPattern.GetSelection read bound into the target binding", "adapter_confinement": "One new module", "test_and_maintenance_cost": "Fixture editors; many apps lack TextPattern so refusal is common"}, execution=["hosted-ci:windows-latest", HW_A])
P("SD-R4", "P4", "wisprside", "snippets", "Voice-triggered snippets (exact whole-utterance trigger)", ["SD-M6"], "ADAPT", SIDE,
  ["src-tauri/src/snippets.rs (new)"], ["Expansion logged; undo restores raw"], ["Unit tests incl. Arabic triggers"], ["Accidental expansion of secrets"], "Disable", "Snippet tests green", donor=D("openwhispr", "src/components/SnippetsView.tsx"), tier="S", execution=["pure"])
P("SD-R6", "P4", "wisprside", "privacy", "Per-app history exclusion and DPAPI-encrypted history store", ["SD-M11"], "FORK_DELTA", SIDE,
  ["src-tauri/src/managers/history.rs", "settings UI"], ["Per-app exclusion honoured; encryption decision recorded and implemented"], ["Migration tests"], ["Key loss means history loss"], "Down-migration", "Privacy tests green", donor=D("handy", "src-tauri/src/managers/history.rs"), tier="S", execution=["hosted-ci:windows-latest"])
P("SD-R7", "P4", "wisprside", "arabic", "Arabic match-key normalizer for custom words (never rewrites output)", ["SD-M0", "D0G"], "BUILD_NEW", SIDE,
  ["src-tauri/src/audio_toolkit/text.rs"], ["Custom words match across alef/hamza/tatweel/harakat variants", "Raw transcript byte-identical in history"], ["Unit fixtures; native-speaker review"], ["Over-normalization changing meaning"], "Disable normalizer", "Fixtures green", donor=D("handy", "src-tauri/src/audio_toolkit/text.rs"), tier="S", register="BN-08",
  bnj={"inspected": "Handy text.rs (ASCII-only fuzzy keys); VoiceInk, OpenWhispr and FreeFlow (no Arabic normalization found)", "why_insufficient": "No donor normalizes Arabic script for matching", "smallest_missing_capability": "A key normalizer used only for matching", "adapter_confinement": "audio_toolkit/text.rs", "test_and_maintenance_cost": "Unit fixtures and native-speaker review"}, execution=["pure"])
P("SD-R8", "P4", "wisprside", "preview", "Streaming preview hardening: tentative text distinct, only final text inserted", ["SD-M6"], "FORK_DELTA", SIDE,
  ["src-tauri/src/managers/transcription/policy.rs", "src/overlay/**"], ["Preview never written to the target"], ["Unit and overlay snapshot tests"], ["None material"], "OverlayStyle::Minimal", "Tests green", donor=D("handy", "src-tauri/src/managers/transcription/policy.rs"), tier="S", execution=["hosted-ci"])
P("SD-R9", "P4", "wisprside", "language", "Measure Arabic/Gulf/code-switch and English cells for shipped routes (WB-AR)", ["SD-R7", "BM-03", "SE-01"], "RESEARCH", "SPEECH_EVIDENCE",
  ["benchmarks/wb-ar/"], ["Per-segment WER/CER with confidence intervals, negation-flip and meaning-distortion rates, latency p50/p95 on HW-A"], ["Preregistered run"], ["Consent and retention of voice data"], "Not applicable", "Results committed; claims only for measured cells", tier="S", execution=[HW_A])
P("PF-01", "P4", "platform", "signing", "Code-signing route decision and pipeline (Artifact Signing, OV certificate or Store)", ["SD-M10"], "RESEARCH", "RELEASE_GREEN_LIGHT",
  ["signing pipeline config"], ["Founder decision recorded with cost", "Signed test build; SmartScreen behaviour recorded honestly"], ["Signature verification"], ["Key custody; cost"], "Unsigned private builds only", "Signed build evidence for R3", tier="S", execution=[HW_A])

# ---------------- P5 WisprStudio MVP
STU = "GRAIN_STUDIO"
P("ST-D01", "P5", "wisprstudio", "egress", "Strip default egress, ship pinned runtime bundles, harden the local API", ["ST-D00", "CORE-07", "BM-01"], "FORK_DELTA", STU,
  ["backend/core/analytics.py", "electron/src/main/account/**", "electron/src/main/updater.ts", "electron/src/main/index.ts", "backend/services/endpoint_race.py", "electron/src/main/runtime-project.ts", "backend/api/auth.py"],
  ["Zero non-allowlisted connections across install, first run, generate, dub and export", "Runtimes come from pinned, digest-checked bundles with a CPU variant (or one explicit user-started download with declared hosts); a runtime manifest exists; at most two engine environments in the MVP", "Local API: loopback only, Host and Origin checks, per-launch token; DNS-rebinding and foreign-Origin fixtures rejected"],
  ["Static scan", "BM-01 capture", "Route 404 tests", "Local API negative fixtures"], ["Missed path after rebase"], "Feature flags restore upstream", "WB-EGRESS green on the exact build",
  donor=D("voicestudio", "backend/core/analytics.py", "electron/src/main/updater.ts", "backend/services/endpoint_race.py", "electron/src/main/runtime-project.ts"), tier="M", execution=[HW_A, "hosted-ci"])
P("ST-D02", "P5", "wisprstudio", "models", "Replace the non-commercial default: benchmark built-in VoxCPM2 and MOSS-TTS-Nano first; manifest rows for every engine", ["ST-D00", "CORE-01"], "FORK_DELTA", STU,
  ["backend/core/prefs.py", "backend/services/tts_backend.py", "config/models.yaml", "model_licenses.json"],
  ["Default engine has a verified permissive card at a pinned revision", "Zero non-commercial weights bundled", "Manifests validate (no pickle, no remote code for admitted models)"], ["Manifest and SBOM check; generate via _echo in CI"],
  ["Licence misread; tokenizer terms"], "Revert default; non-commercial behind research flag", "Rights gate green", donor=D("voicestudio", "backend/core/prefs.py", "config/models.yaml"), tier="M", execution=["hosted-ci", HW_A])
P("ST-D03", "P5", "wisprstudio", "consent", "Consent ledger and gate on every synthesis, dubbing, conversion and cloning path", ["ST-D00", "CORE-01"], "BUILD_NEW", STU,
  ["backend/services/consent_ledger.py (new)", "backend/api/routers/profiles.py", "generation, dub_generate, voice_conversion, speaker_clone, MCP and OpenAI-compatible routes"],
  ["100% correct on the matrix 4 clone paths x {none, valid, revoked, reference-hash mismatch}", "Consent binds the reference-audio digest and a speaker match", "Stock voices only from manifest catalog entries", "Revocation cancels queued work; late outputs dropped"], ["About 40 fixture tests", "WB-CONSENT"],
  ["Bypass via an uncovered route"], "Disable cloning entirely (fail closed)", "WB-CONSENT: zero leaks",
  donor=D("voicestudio", "backend/api/routers/profiles.py"), tier="M", register="BN-03",
  bnj={"inspected": "VoiceStudio profiles.py consent flags, speaker_clone.py, generation.py, dub_generate.py; Voicebox models", "why_insufficient": "Flags exist but no synthesis path checks them (profiles.py:1215-1216); no reference digest or revocation epoch", "smallest_missing_capability": "Ledger record plus require_clone_consent(profile, reference_digest) at admission and dispatch", "adapter_confinement": "One module plus call sites in the synthesis routers", "test_and_maintenance_cost": "About 40 tests; call sites re-checked every rebase"}, execution=["hosted-ci"])
P("ST-D04", "P5", "wisprstudio", "dubbing", "fit_inputs guard before the unchanged plan_fit (allows overlap)", ["ST-D00", "D0G"], "COPY", STU,
  ["backend/services/fit_inputs.py (new)", "backend/api/routers/dub_generate.py"], ["NaN, Inf, negative, end-before-start and NaN-total rejected with typed errors; overlap allowed", "plan_fit sha256 unchanged"], ["Opus probe", "Upstream fit tests", "Overlap fixture"],
  ["None new"], "Remove call", "Guard fixtures green", donor=D("voicestudio", "backend/services/fit_planner.py"), tier="M", execution=["pure"])
P("ST-D05", "P5", "wisprstudio", "cancellation", "Cancellation conformance with mandatory escalation; subprocess isolation for engines without a measured abort bound", ["ST-D00", "CORE-01"], "FORK_DELTA", STU,
  ["backend/services/inference_cancellation.py", "backend/services/subprocess_backend.py", "backend/core/contained_subprocess.py"],
  ["Kill and stall fixtures with _echo produce truthful states", "Deadline, kill of the exact (pid, start_generation), observed exit", "Studio workers default to cores-2 threads at low priority"], ["Sequence fixtures"],
  ["GPU memory leaks in in-process engines"], "Keep upstream semantics; mark unconfirmed", "Cancel fixtures green", donor=D("voicestudio", "backend/services/inference_cancellation.py"), tier="M", execution=["hosted-ci", HW_A])
P("ST-D08", "P5", "wisprstudio", "offline", "Offline staging manifest for engines and runtimes", ["ST-D01"], "FORK_DELTA", STU,
  ["backend/services/model_manager.py", "electron/src/main/runtime-project.ts"], ["Offline install from a hashed bundle; mismatch rejected"], ["Network-blocked CI job"], ["Tampered bundle"], "Online mode with confirmation", "Offline install green", donor=D("voicestudio", "backend/services/model_manager.py"), tier="M", execution=["hosted-ci"])
P("ST-D09", "P5", "wisprstudio", "watermark", "Force watermark on cloned output; resolve the AudioSeal weight licence", ["ST-D02"], "FORK_DELTA", STU,
  ["backend/services/watermark.py"], ["Cloned outputs always marked; detector verifies after re-encode", "AudioSeal licence recorded"], ["Detection fixtures"], ["Licence unresolved blocks release"], "Upstream preference", "Watermark tests green", donor=D("voicestudio", "backend/services/watermark.py"), tier="M", execution=["hosted-ci"])
P("DS-07", "P5", "design", "wisprstudio", "Tokens and first-run flow in the VoiceStudio fork; RTL script editing; LTR timeline", ["DS-05", "ST-D00"], "FORK_DELTA", STU,
  ["electron/src/renderer/**"], ["Screenshot and state-sequence matrix; rubric gate as DS-05", "Keyboard-only clip edit (S7)", "New-project wizard with profile and engine recommendation"], ["Screenshot capture", "Accessibility Insights"], ["None material"], "Revert UI commits", "G-SHOTS evidence", donor=D("voicestudio", "electron/src/renderer/"), tier="M", execution=[HW_A])
P("BM-05", "P5", "benchmark", "co-running", "Dictation p95 while a Studio render runs on HW-A", ["SD-M6", "ST-D05"], "RESEARCH", "GRAIN_BENCH",
  ["benchmarks/co-running/"], ["WisprSide p95 key-up-to-text recorded with and without a concurrent Studio render; free-memory check refuses model loads instead of paging"], ["Scripted run"], ["None material"], "Not applicable", "Results committed", estimate="1 d", execution=[HW_A])

# ---------------- P6 Klaint text MVP (single hardened process)
KL = "GRAIN_KLAINT_TEXT"
P("KT-03", "P6", "klaint", "broker", "Deterministic broker and outcome ledger: sole executor of consequential tools in one hardened Parlant process", ["KT-01", "D0G"], "BUILD_NEW", KL,
  ["services/klaint-dialogue/broker/{service,ledger,policy,reconcile}.py"],
  ["Consequential tools registered only through the in-process ToolService; plugin server disabled", "Principal from Parlant's session store plus a per-call token bound to the authenticated session; a forged customer_id yields zero effects and zero data from read tools", "Idempotency key = H(tenant, conversation, tool, canonical arguments); dispatch refused while a non-terminal intent with that key exists", "Timeout-after-commit: unknown, then reconciled, never re-dispatched", "Verdict class and principal must match the intent", "ASK needs operator or step-up confirmation; conversation text never confirms"],
  ["Fault-injection suite with a fake CRM (1,000 runs)", "Ported test_tool_runner.py", "Contract bundle fixtures"], ["Connector reconciliation not always possible"], "Deny all mutations; text answers stay available", "WB-KLAINT idempotency and authority hard gates green",
  donor=D("parlant", "src/parlant/core/tools.py", "src/parlant/sdk.py"), tier="M", register="BN-02",
  bnj={"inspected": "Parlant v4 ToolService and review hooks; Botpress connectors; Chatwoot handoff; Rasa action server; Sentrdel lattice (concepts adapted in Python)", "why_insufficient": "No donor resolves principal server-side, records intents before dispatch, enforces idempotency keys and reconciles unknown outcomes; Parlant's plugin server trusts caller-supplied ids", "smallest_missing_capability": "Broker service, Python policy module (allowlist, argument schema, scope checks, resolution), ledger table and reconciliation loop", "adapter_confinement": "One Python package in the Klaint process", "test_and_maintenance_cost": "Adversarial fixture suites; grows with connectors"}, execution=["hosted-ci", HW_A])
P("KT-04", "P6", "klaint", "tool gate", "Review-hook gate and bypass closure (variable refresh, plugin port, lowest effort level)", ["KT-03"], "ADAPT", KL,
  ["services/klaint-dialogue/hooks/tool_gate.py", "config lint"], ["Hook BAILs any broker-pre-denied call", "Lint rejects variables bound to mutating tools", "One test per bypass path"], ["Unit tests per path"],
  ["Upstream adds new paths"], "Disable consequential tools", "Bypass fixtures green", donor=D("parlant", "src/parlant/core/engines/compass/loop/base_loop.py"), tier="M", execution=["hosted-ci"])
P("KT-05", "P6", "klaint", "responses", "Commitment guard: commitments only from committed receipts; otherwise approved template or handoff", ["KT-03"], "ADAPT", KL,
  ["services/klaint-dialogue/hooks/commitment_guard.py", "policy_content/templates/"], ["100 adversarial prompts x 3 seeds x EN/AR: zero unbacked commitments"], ["WB-KLAINT commitment suite"],
  ["Classifier misses paraphrases"], "Force handoff on any commitment intent", "Hard gate green", donor=D("parlant", "src/parlant/core/engines/compass/hooks.py"), tier="M", execution=["hosted-ci"])
P("KT-06", "P6", "klaint", "retrieval", "Cited retrieval; stale or missing knowledge leads to handoff", ["KT-01", "D0G"], "WRAP", KL,
  ["services/klaint-dialogue/retrieval/"], ["Citations with document id and version; retrieved text never becomes rules"], ["Injection corpus; stale-document tests"], ["Embedding provider egress"], "Disable retriever", "Retrieval fixtures green", donor=D("parlant", "src/parlant/sdk.py"), tier="M", execution=["hosted-ci"])
P("KT-07", "P6", "klaint", "inbox", "Chatwoot bridge via Agent Bot API: immediate ack and queue, signature-keyed replay cache, ownership epoch", ["KT-03"], "API_INTEGRATION", KL,
  ["integrations/chatwoot/{receiver,poster,ownership}.py"],
  ["Webhooks acknowledged immediately and processed from a queue", "Replay cache keyed on H(ts || body) or the signature plus the signed message id; replay with a mutated delivery header rejected", "Future, NaN and stale timestamps rejected", "No AI message after takeover"],
  ["Concurrent takeover fixtures", "Mutated-header replay fixture"], ["Chatwoot bot_handoff race upstream"], "Detach the bot; Chatwoot keeps the human queue", "Takeover and webhook suites green",
  donor=[D("chatwoot", "lib/webhooks/trigger.rb", "app/listeners/agent_bot_listener.rb"), D("stdwebhooks", "libraries/python/standardwebhooks/webhooks.py")], tier="M", execution=["hosted-ci"])
P("KT-08", "P6", "klaint", "test lab", "tau2-bench harness with deterministic ledger scoring (EN, MSA, Gulf, code-switch)", ["KT-03"], "WRAP", KL,
  ["tests/klaint/sim/", "tests/klaint/tasks/{en,ar}/"], ["Recorded-I/O replay gives identical verdicts; LLM judges advisory only"], ["WB-KLAINT suites"], ["Simulator bias; model cost (use local or recorded runs)"], "Harness only", "Harness runs in CI",
  donor=D("tau2", "src/tau2/evaluator/evaluator_env.py"), tier="M", execution=["hosted-ci"])
P("KT-09", "P6", "klaint", "operations", "Inference topology, observability and egress: one local inference server or a tenant-configured provider; local OTLP; egress allowlist", ["KT-01", "D0G"], "WRAP", KL,
  ["services/klaint-dialogue/ops/"], ["Inference server (llama.cpp-compatible or explicit provider) has one owner, keys per tenant and no cross-tenant prefix cache", "Egress allowlist test green; no vendor telemetry", "Read-only ledger query CLI for audit"], ["Packet capture or firewall log"], ["Hidden SDK egress"], "Disable exporters", "WB-EGRESS for Klaint green", donor=D("parlant", "src/parlant/bin/server.py"), tier="M", execution=[HW_A])

# ---------------- P7 expansion
P("BM-04", "P7", "benchmark", "consented panel", "Consented Arabic/English speech panel (forms, volunteers, storage, withdrawal)", ["BM-03", "SE-01"], "RESEARCH", "SPEECH_EVIDENCE",
  ["benchmarks/panel/ (metadata only)"], ["Written consent per speaker; held-out splits frozen"], ["Consent audit"], ["Privacy law obligations"], "Withdraw and delete per consent", "Panel available", tier="S", execution=["manual:founder-run consent program"])
P("ST-D06", "P7", "wisprstudio", "engines", "Chatterbox Multilingual subprocess engine adapter, only if ST-D02 rejects the built-in Arabic engines", ["ST-D02", "ST-D05"], "WRAP", STU,
  ["backend/engines/chatterbox_mtl/ (new)"], ["Offline load from a staged manifest; Arabic accepted; Perth watermark pinned (not @master)"], ["Engine contract tests (_echo pattern)"], ["Unmaintained upstream"], "Remove registry entry", "Engine tests green",
  donor=D("chatterbox", "src/chatterbox/mtl_tts.py"), tier="S", execution=["hosted-ci"])
P("ST-D07", "P7", "wisprstudio", "pronunciation", "Arabic proclitic-aware lexicon matching", ["ST-D00", "D0G"], "ADAPT", STU,
  ["backend/services/pronunciation.py"], ["Clitic cases and a 50-item panel matched; no false positives on a negative set; upstream tests unchanged"], ["Probe and panel tests"], ["ReDoS (keep escaped alternation)"], "Flag off", "Lexicon tests green", donor=D("voicestudio", "backend/services/pronunciation.py"), tier="S", execution=["pure"])
P("KT-02", "P7", "klaint", "tenancy", "Multi-tenant host and gateway: one Parlant process per tenant, shared Chatwoot with one account and bot per tenant", ["KT-03", "KT-07"], "ADAPT", KL,
  ["services/klaint-dialogue/host/{supervisor,gateway,tenant_config}.py"], ["Gateway and shared Chatwoot are owned components with routing tests", "Plugin tool server off in every tenant process", "Cross-tenant and same-tenant forged-customer fuzz: zero leaks"], ["Isolation fixtures"], ["Memory per tenant"], "Single-tenant mode", "Isolation suite green", donor=D("parlant", "src/parlant/api/authentication.py"), tier="S", execution=["hosted-ci"])
P("KT-10", "P7", "klaint", "connectors", "First real connector (Zendesk-class) through the broker; read-only first", ["KT-03"], "BUILD_NEW", KL,
  ["adapters/connectors/zendesk/"], ["create_ticket only through the broker with a reconciliation lookup; revoked OAuth handled"], ["Fake API: 429, timeout-after-POST, foreign requester"], ["Vendor API lacks idempotency keys"], "Revoke the connector credential", "Connector fixtures green", donor=D("botpress", "integrations/zendesk/"), tier="S", register="BN-10",
  bnj={"inspected": "Botpress zendesk integration (TypeScript, cloud runtime) and HubSpot HITL signature code", "why_insufficient": "Node runtime and missing replay and timestamp checks; Klaint is a Python service", "smallest_missing_capability": "Thin Python client using the Botpress schema as reference", "adapter_confinement": "One connector package behind the broker", "test_and_maintenance_cost": "Fake-API fixtures per connector"}, execution=["hosted-ci"])
P("DS-08", "P7", "design", "klaint", "Klaint console: why panel, approvals queue, live takeover, Test Lab, audit", ["KT-03", "KT-08", "DS-05"], "BUILD_NEW", KL,
  ["services/klaint-console/"], ["Journeys K1-K6 pass", "Screenshot matrix + rubric gate", "Approvals queue with timers and plain-language summaries"], ["E2E journeys", "Accessibility Insights"], ["Cross-tenant data exposure in UI"], "Read-only console", "G-E2E and G-SHOTS evidence", tier="S", register="BN-06",
  bnj={"inspected": "Parlant v4 APIs (most CRUD routes removed), Chatwoot UI, Botpress Studio (cloud components absent), OpenTelemetry trace viewers", "why_insufficient": "No open console shows verdicts, ledger outcomes and evaluations together for non-experts", "smallest_missing_capability": "Web views over existing APIs, traces and agent-definition files, sized after MVP operators used Chatwoot, traces and tau2 reports", "adapter_confinement": "Separate console app", "test_and_maintenance_cost": "Largest new UI surface; mitigated by the component kit"}, execution=["hosted-ci", HW_A])
P("KV-01", "P7", "klaint", "voice", "Pipecat pipeline inside the Klaint process; no mutating tools in Pipecat", ["KT-07", "KT-08"], "ADAPT", "LATER_HORIZON",
  ["services/klaint-dialogue/voice/"], ["Pre-provisioned weights (Kokoro auto-download off); synthetic audio turn tests"], ["Frame interruption tests"], ["v1.15 turn API churn"], "Disable voice channel", "Voice smoke green", donor=D("pipecat", "src/pipecat/processors/frame_processor.py"), tier="L", execution=["hosted-ci"])
P("KV-02", "P7", "klaint", "voice", "Barge-in truth: spoken_text records only heard words; broker holds consequential calls until the turn is final", ["KV-01"], "ADAPT", "LATER_HORIZON",
  ["services/klaint-dialogue/voice/barge_in.py"], ["No commitment spoken without a receipt; streaming guard replaces the BLOCK-only hook"], ["Interrupt-during-tool tests"], ["Streaming cannot unsay spoken text"], "Voice read-only", "Barge-in suite green", donor=D("pipecat", "src/pipecat/frames/frames.py"), tier="L", execution=["hosted-ci"])
P("CORE-R1", "P7", "core", "rust crates", "wispral-policy and wispral-journal Rust crates, once a second Rust consumer exists (A-01)", ["CORE-01"], "ADAPT", "LATER_HORIZON",
  ["crates/wispral-policy/", "crates/wispral-journal/", "Cargo.toml workspace, rust-toolchain.toml, Cargo.lock"],
  ["Sentrdel exhaustive verdict vectors reproduced", "orcel-journal upstream tests pass unchanged", "AGENTS.md section 7 commands pass verbatim"], ["cargo fmt, clippy and test as in AGENTS.md section 7"], ["Semantics drift"], "Drop crates", "Crates green",
  donor=[D("sentrdel", "crates/sentrdel-policy/src/lib.rs", "crates/sentrdel-policy/src/narrowing.rs", "crates/sentrdel-engine/src/bounded_json.rs"), D("orcel", "crates/orcel-journal/src/lib.rs")], tier="L", execution=["hosted-ci"])
P("A-01", "P7", "wisprside", "developer agents", "Developer-agent voice module over ACP 5.0 (stdio only) with risk-tiered approvals", ["SD-M6", "CORE-R1"], "WRAP", "LATER_HORIZON",
  ["adapters/acp/"], ["Init, prompt, permissions, cancel race and reconnect fixtures against a fake peer, then one real agent"], ["Fake ACP peer"], ["ACP HTTP transport has no auth (stdio only)"], "Disconnect agent; keep text", "Needs 000A/000C/000D disposition",
  donor=D("acp", "src/agent-client-protocol/src/concepts/cancellation.rs"), tier="L", execution=["hosted-ci"])

# ---------------- P8
P("CORE-08", "P8", "core", "local api", "Shared local-API auth profiles: (a) same-user pipe/UDS, (b) localhost HTTP", ["CORE-01"], "ADAPT", "LATER_HORIZON",
  ["docs/engineering/LOCAL_API_AUTH.md", "fixtures/local_api/*"], ["Other-user client, remote pipe client, wrong Host, foreign Origin, missing or replayed ticket refused; refusal observed before any request body is parsed (log assertion)"], ["Negative fixture suite"], ["Platform API differences"], "CLI only", "Profiles documented and tested",
  donor=[D("orcel", "crates/orcel-platform/src/peer.rs", "crates/orcel-platform/src/acl.rs"), D("ninerr", "packages/studio-host/src/server.ts")], tier="L", execution=["hosted-ci", HW_A])
P("ST-D10", "P8", "wisprstudio", "bridge", "Wispral contract bridge (job, consent, cancel) outside the fork", ["ST-D03", "ST-D05", "CORE-08"], "BUILD_NEW", "LATER_HORIZON",
  ["adapters/studio/ (new)"], ["Contract fixtures pass; local API uses the CORE-08 profile"], ["Contract tests"], ["Auth between adapter and backend"], "Disable adapter", "Bridge tests green", tier="L", register="BN-11",
  bnj={"inspected": "VoiceStudio REST and MCP routes", "why_insufficient": "No Wispral job, consent or cancel message contract in the donor", "smallest_missing_capability": "Thin mapping adapter", "adapter_confinement": "adapters/studio outside the fork", "test_and_maintenance_cost": "Contract fixtures; low"}, execution=["hosted-ci"])
P("PL-SDK", "P8", "platform", "sdk", "TypeScript and Python SDKs over authenticated local APIs; MCP stdio wrappers", ["CORE-08", "ST-D10"], "BUILD_NEW", "LATER_HORIZON",
  ["sdk/"], ["Generated types from contracts; semver policy"], ["Contract fixtures"], ["Unauthenticated listeners"], "Withdraw SDK", "SDK published only after founder green light", tier="L", register="BN-12",
  bnj={"inspected": "VoiceStudio REST/MCP, Handy CLI, Orcel app API (FSL, reference only)", "why_insufficient": "No donor SDK spans products or uses the Wispral contracts", "smallest_missing_capability": "Thin generated clients", "adapter_confinement": "sdk package", "test_and_maintenance_cost": "Generated; low"}, execution=["hosted-ci"])
P("PF-02", "P8", "platform", "cross-platform", "macOS (notarized) and Linux (X11, GNOME/KDE portals) cells for WisprSide", ["SD-R6", "PF-01"], "FORK_DELTA", "LATER_HORIZON",
  ["platform adapters"], ["Per-cell clean-install journeys pass"], ["Platform fixtures"], ["TCC and portal differences"], "Do not claim the cell", "Cell evidence", donor=D("handy", "src-tauri/src/clipboard.rs"), tier="L", execution=["manual:platform hardware"])

FIRST_TEN = ["G1", "C1", "PLAN", "A040", "C2", "R", "NOOP", "G2", "F", "CORE-00"]

VALIDATED_DOCS = [
    "docs/strategy/WISPRAL_WORLD_CLASS_MASTER_PLAN.md", "docs/strategy/WISPRAL_PRODUCT_VISION.md", "docs/strategy/WISPRAL_PRODUCT_ARCHITECTURE.md",
    "docs/strategy/WISPRAL_COPY_FIRST_STRATEGY.md", "docs/strategy/WISPRAL_ENGINEERING_ROADMAP.md", "docs/strategy/WISPRAL_RELEASE_QUALITY.md",
    "docs/strategy/WISPRAL_GOVERNANCE_RECONCILIATION.md", "docs/design/WISPRAL_DESIGN_SYSTEM.md", "docs/design/WISPRSIDE_UX_SPEC.md",
    "docs/design/WISPRSTUDIO_UX_SPEC.md", "docs/design/KLAINT_UX_SPEC.md", "docs/engineering/WISPRAL_MODEL_STRATEGY.md",
    "docs/engineering/WISPRAL_SECURITY_ARCHITECTURE.md", "docs/engineering/WISPRAL_BENCHMARKS.md", "docs/engineering/WISPRAL_PLATFORM_COMPATIBILITY.md",
    "docs/engineering/WISPRAL_IMPLEMENTATION_PACKETS.md", "docs/engineering/contracts/README.md",
    "research/wispral-world-class/SOURCE_DECISION_MATRIX.md", "research/wispral-world-class/COMPETITOR_GAP_MATRIX.md",
    "research/wispral-world-class/ARCHITECTURE_TRADEOFFS.md", "research/wispral-world-class/REA_EVIDENCE_INDEX.md",
    "research/wispral-world-class/INDEPENDENT_REVIEW.md", "research/wispral-world-class/RISK_REGISTER.md",
    "research/wispral-world-class/DECISION_LEDGER.md", "research/wispral-world-class/CURRENT_STATE_INVENTORY.md",
    "research/wispral-world-class/PLAN_VALIDATION.md", "research/wispral-world-class/FINAL_HANDOFF.md",
]

data = {
    "schema_version": 1, "generated_by": "research/wispral-world-class/build_packets.py", "date": "2026-11-08",
    "status": "CANDIDATE. No packet is READY. Readiness comes only from the named authority after the governance sequence.",
    "authorities": AUTHORITIES, "phases": PHASES, "first_ten": FIRST_TEN, "validated_documents": VALIDATED_DOCS, "packets": PACKETS,
}
(ROOT / "research/wispral-world-class/packets.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def cell(v):
    if isinstance(v, list):
        return "<br>".join(str(x) for x in v)
    return str(v)


def donor_cell(pk):
    ds = pk.get("donor")
    if not ds:
        return "none (governance, research or build-new)"
    ds = ds if isinstance(ds, list) else [ds]
    return "<br>".join(f"`{d['repo']}@{d['sha'][:12]}`: " + ", ".join(f"`{p}`" for p in d["paths"]) for d in ds)


lines = [
    "# Wispral implementation packets",
    "",
    "**Status:** CANDIDATE. Generated by [`build_packets.py`](../../research/wispral-world-class/build_packets.py) from the same source as the machine-readable [`packets.json`](../../research/wispral-world-class/packets.json); edit the generator, never this file. **No packet is READY.** Each packet becomes executable only through its named readiness authority after the [governance sequence](../strategy/WISPRAL_GOVERNANCE_RECONCILIATION.md). Estimates are engineering judgement for a familiar contributor, exclude review latency, and are not measured.",
    "",
    "Packet contract (applies to every row): name the exact capability and changed paths; pin the donor and its full dependency closure; keep notices; run the donor's own tests before adapting; make the smallest change; test at the final head; record failed, skipped and not-run checks, the exact base and head, rollback and the last readable data format. Rust code runs exactly the AGENTS.md section 7 set: `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets --all-features --locked -- -D warnings` and `cargo test --workspace --all-targets --all-features --locked` (the first packet that creates a Rust workspace in this repository owns `Cargo.toml`, `Cargo.lock` and `rust-toolchain.toml`; forks use their donor workspace). Execution context tags: `hosted-ci` (GitHub-hosted runners; Windows runners are Server images running as administrator), `manual:HW-A` (founder laptop with recorded evidence), `pure` (platform-independent tests). `d1-local` may triage findings but never approves or clears a gate.",
    "",
    "## Readiness authorities",
    "",
    "| Authority | Meaning |",
    "| --- | --- |",
]
lines += [f"| `{k}` | {v} |" for k, v in AUTHORITIES.items()]
lines += ["", "## First ten packets in dependency order", "", "| # | Packet | Depends on | Authority |", "| --- | --- | --- | --- |"]
by_id = {p["id"]: p for p in PACKETS}
for i, pid in enumerate(FIRST_TEN, 1):
    pk = by_id[pid]
    lines.append(f"| {i} | **{pid}** {pk['title']} | {', '.join(pk['depends_on']) or '—'} | `{pk['readiness_authority']}` |")
for ph in PHASES:
    group = [p for p in PACKETS if p["phase"] == ph["id"]]
    lines += ["", f"## {ph['id']} — {ph['title']}", "", f"**Exit:** {ph['exit']}", ""]
    for pk in group:
        lines += [
            f"### {pk['id']} — {pk['title']}", "",
            "| Field | Value |", "| --- | --- |",
            f"| Product / subsystem | {pk['product']} / {pk['subsystem']} |",
            f"| Depends on | {', '.join(pk['depends_on']) or '—'} |",
            f"| Decision | `{pk['decision']}` |",
            f"| Donor (pinned) | {donor_cell(pk)} |",
            f"| Files / interfaces | {cell(pk['affected'])} |",
            f"| Acceptance | {cell(pk['acceptance'])} |",
            f"| Tests | {cell(pk['tests'])} |",
            f"| CI gates | {cell(pk['ci_gates'])} |",
            f"| Security risks | {cell(pk['security_risks'])} |",
            f"| Rollback | {pk['rollback']} |",
            f"| Readiness authority | `{pk['readiness_authority']}` |",
            f"| Definition of done | {pk['definition_of_done']} |",
            f"| Estimate | {pk['estimate']} |",
            f"| Tier | {pk.get('tier', 'foundation / governance')} |",
            f"| Execution context | {cell(pk.get('execution', ['not applicable']))} |",
        ]
        if "build_new_justification" in pk:
            j = pk["build_new_justification"]
            lines.append(f"| Build-new register | {pk.get('build_new_register_id', 'MISSING')} |")
            lines.append(f"| Build-new justification | Inspected: {j['inspected']}. Why insufficient: {j['why_insufficient']}. Smallest missing capability: {j['smallest_missing_capability']}. Confined to: {j['adapter_confinement']}. Cost: {j['test_and_maintenance_cost']}. |")
        lines.append("")
(ROOT / "docs/engineering/WISPRAL_IMPLEMENTATION_PACKETS.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(f"wrote {len(PACKETS)} packets")
