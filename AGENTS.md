# Wispral Repository Instructions

Wispral (by Halfmoon) is a modular, independent voice intelligence ecosystem with shared infrastructure and four independently installable products:

- **Wispral Core** (`crates/wispral-*`): shared voice intelligence, contracts, policy, journal, Arabic/multilingual normalization, audio/DSP, adaptive routing, context, memory, duplex live turn/cancellation primitives, `Wispral Connect` (`wispral` CLI/MCP), and `WispralBench`;
- **WisprSide** (`TheHalfMoon/wisprside`): local-first voice typing, intelligent writing, editing, and optional developer-agent control;
- **WisprStudio** (`TheHalfMoon/wisprstudio`): local-first professional AI voice and audio production;
- **Klaint** (`services/klaint/`): self-hostable enterprise customer-service and verified customer-resolution platform;
- **Omalla** (`services/omalla/`): self-hostable programmable real-time voice-agent, WebRTC/WebSocket, workflow, and telephony infrastructure.

No compulsory proprietary agent, IDE, paid model, Wispral cloud account, or mandatory telemetry is required for the useful local or self-hosted core.

## 1. Canonical reading order

Before changing the repository, read in this order:

1. `AGENTS.md`
2. `CONSTITUTION.md` (Version 2.0.0)
3. `docs/canonical/EXECUTION_REGISTRY.md` (live multi-wave execution state, evidence, and PR ledger)
4. `docs/architecture/WISPRAL_ECOSYSTEM_ARCHITECTURE_V2.md` (EGM-hardened target architecture & deterministic lock-in table)
5. `docs/canonical/CURRENT_STATE.md`
6. `docs/canonical/TRUSTED_CONTROL_REPAIRS.md`
7. `docs/canonical/ARCHITECTURE_INVARIANTS.md`
8. `docs/canonical/PROGRAM_ROADMAP.md`
9. `specs/CURRENT.md`
10. referenced research, benchmark, security (`docs/engineering/WISPRAL_SECURITY_ARCHITECTURE.md`), ADR, contract, and source provenance files

Live repository and GitHub truth override stale handoffs, plans, summaries, and chat history.

## 2. Language

All repository and GitHub technical content MUST be written in English, including code, comments, specifications, plans, tasks, reports, benchmark artifacts, evidence, commit messages, pull-request text, and reviewer responses (except Arabic language evaluation fixtures, UI localization catalogs, and preserved Arabic executive readouts explicitly labeled as such).

## 3. Proof before done

No compatibility, latency, accuracy, privacy, security, performance, quality, portability, or adoption claim may be represented as established unless the exact claim is supported by reproducible evidence against the exact revision being claimed.

`PASS`, `SUPPORTED`, `VERIFIED`, `QUALIFIED`, `FASTER`, `LOWER LATENCY`, `OFFLINE`, and similar words are evidence-bearing terms, not marketing adjectives. Unmeasured engineering targets must be labeled `RELEASE_GATE_TARGET (NOT_MEASURED)`. If a required check was not run, record `NOT RUN`.

## 4. Copy-first and bounded execution discipline

**COPY FIRST. ADAPT SECOND. BUILD FROM SCRATCH ONLY WHEN NECESSARY.**

- Reuse qualified Halfmoon and authorized open-source donor implementations before writing new subsystems.
- Record upstream repository, exact commit SHA, adapted paths, license, and required attribution (`NOTICE`).
- Enforce strict license separation: `AGPL-3.0` material in `TheHalfMoon/wisprstudio` MUST NOT enter `TheHalfMoon/Wispral` (Apache-2.0) or `TheHalfMoon/wisprside` (MIT); `FSL-1.1-MIT` donor files remain reference-only.
- Keep `000B2` frozen benchmark paths (`research/000b*`, `specs/000B*`, `.github/workflows/000b*`, `.github/trusted/*`) untouched. Track active ecosystem implementation waves in `docs/canonical/EXECUTION_REGISTRY.md` rather than re-editing `CURRENT_STATE.md` or `specs/CURRENT.md`.

## 5. Product invariants

Unless the constitution is amended, every implementation must preserve:

- agent, model, and carrier vendor neutrality;
- zero-mandatory-cost local-first (`WisprSide`, `WisprStudio`) and self-hostable (`Klaint`, `Omalla`) operation, with zero silent cloud fallback;
- explicit user or deterministic server-derived policy authority for consequential actions;
- bound, visible, revocable voice and asset consent;
- sink-verified interruption and cancellation (`requested`, `acknowledged`, `observed_stopped`, `completed_before_cancel`, `stopped_unconfirmed`, `failed`);
- raw speech provenance separate from normalized keys, rewritten text, and interpreted intent;
- `Command` vs. `Aside` separation;
- open, reproducible `WispralBench` methodology and zero mandatory telemetry.

## 6. Verification and independent review gates

- **Rust (`crates/*`, `wisprside`):**
  ```bash
  cargo fmt --all -- --check
  cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
  cargo test --workspace --all-targets --all-features --locked
  ```
- **Python (`services/klaint/`, `wisprstudio`, contracts):** `pytest` + contract conformance (`python -I docs/engineering/contracts/run_conformance.py`).
- **TypeScript / Node (`services/omalla/`, frontend surfaces, design tokens):** `tsc --noEmit`, unit/smoke suites, and `node docs/design/tokens/check_contrast.mjs`.
- **Independent review (`Constitution §7`):** Run deterministic local diff/rule review (`ocr delegate preview` / `ocr delegate rule`) and fresh-context multi-bar PStack review (`correctness`, `parsimony`, `product`, `security`) bound to the exact commit SHA before guarded expected-head merge.
