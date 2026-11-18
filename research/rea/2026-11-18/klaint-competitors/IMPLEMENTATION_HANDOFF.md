# Klaint REA — Implementation-team handoff

**Date:** 2026-11-18
**Research workspace:** `D:\Klaint-REA-20261118`
**Product:** Klaint, within Wispral
**Status:** Competitive architecture research completed. **This is not production implementation or evidence of production readiness.**

## Read in this order
1. `README.md` — Arabic executive readout
2. `ARCHITECTURE_RECONCILIATION.md` — **mandatory** canonical Python broker vs unratified Rust alternative and superseded Parlant tool-server-off wording
3. `REA_MASTER_REPORT.md` — detailed competitor research and constraints
4. `COMPETITOR_EVIDENCE_MATRIX.md` — as-observed vs vendor claims vs unknown
5. `SOURCE_CODE_INVENTORY.md` — actual code, pins, licenses, source-vs-SDK distinction
6. `KLAINT_TARGET_ARCHITECTURE.md` — **proposal**, not accepted design, capability and security contracts
7. `KLAINT_COMPETITIVE_ROADMAP.md` — estimates and gated phases
8. `ACCESS_GAPS.md` — actual inaccessible source and official access needed
9. `REPRODUCE.md` — evidence reproduction and exact-file references
10. `SUPPLEMENTAL_PUBLIC_CODE.md`, `progress.txt` — later research addenda and work log

## Canonical decisions / open gate
- Wispral's current approved direction: one Python Parlant service plus **separately isolated Python deterministic action broker**, DB ledger, reusable language-neutral contracts. Rust broker at P0 is **an unratified REA alternative**; do not implement or claim it is adopted without ADR/decision evidence.
- **Never trust caller-supplied customer identity**, including Parlant plugin-tool-server payloads.
- Assume Parlant's tool server is **reachable**. The old docs' instruction to turn it off is superseded; do not use loopback as an authorization boundary. Bind one-time capabilities to authenticated tenant/session/tool/canonical arguments and reviewed proposal; isolate tenants; test all routes.
- BLOCK mode and pre-emission gating for safety-dependent responses; streaming negative cases must demonstrate no unreviewed output leaves.
- KT-01/KT-01b authority, customer-crossing, and output-gate tests must pass before live customer data.
- Two source types must never be conflated: public SDK/client artifacts versus proprietary backend services. No private competitor engine source was obtained.
- `@decagon-ai/duet-cli@0.6.1` license is restrictive to connecting to Decagon. Do NOT transplant or redistribute its bundle into Klaint. Lorikeet web-sdk and mcp-server packages have no published license field; do not assume reuse rights.
- Vendor comparisons contain **no independently measured head-to-head scores**. Distinguish performance targets from measured facts.

## Recommended next engineering action (not yet authorized by this REA)
1. Produce an ADR comparing Python vs Rust broker, referencing ratified Wispral architecture decisions and attack surface.
2. Specify and run KT-01b in a synthetic, representative per-tenant production-mode container with separate issuance channels, signed one-use capabilities and deterministic read/write tool broker. Require zero data and effects on forgery/replay/cross-principal probes.
3. Write a minimal public-reference chat scenario with authenticated customer context, cited policy, action ledger, human handoff, controlled model backend.
4. Only then estimate voice, Arabic-dialect benchmark, authoring console and self-host enterprise packaging.

## Reproduce before implementing
- Review live `TheHalfMoon/Wispral` canonical docs and check for changes since pinned `689a4e4`.
- Re-run file/line evidence in `REPRODUCE.md` and record resulting commit and changes.
- Run source-level license review and preserve LICENSE/NOTICE for each donor.
- Do not turn historical source-verified endpoints into claims about server-side policies.
- Maintain every research assertion with a link, pin, and evidence class.

## Workspace rules
`sources/` contains research clones, published packages, and captured public evidence. Do not commit it wholesale into Wispral. Work through small, reviewed and tested implementation units after the owner authorizes that next phase. This research did not modify the original Wispral repository.
