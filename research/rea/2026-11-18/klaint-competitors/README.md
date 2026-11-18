# Klaint competitor REA: Lorikeet, Decagon, Parloa (2026-11-18)

**Classification:** historical, evidence-backed competitive research and engineering proposals; **not canonical architecture, executable specification, product implementation, or authorization to start a task**. This study was written for Klaint within Wispral on 2026-11-18 using DeepSeek through OpenCode. It covers publicly available source, SDKs, product documentation, and disclosed limitations, not proprietary backend implementations.

## Start here: agent handoff

Before using this research to build Klaint, follow the repository's actual authority chain in [AGENTS.md](../../../../AGENTS.md) and [specs/CURRENT.md](../../../../specs/CURRENT.md), then read these materials in order:

1. [Implementation handoff](IMPLEMENTATION_HANDOFF.md): work boundaries, prerequisite security gates, and implementation starting point.
2. [Architecture reconciliation](ARCHITECTURE_RECONCILIATION.md): **mandatory** distinction between Wispral's canonical Python broker/DB ledger and this study's **unratified** Rust sidecar proposal.
3. [Master research report](REA_MASTER_REPORT.md) and [competitor evidence matrix](COMPETITOR_EVIDENCE_MATRIX.md): product comparisons with evidence classes; no invented head-to-head scores.
4. [Source code inventory](SOURCE_CODE_INVENTORY.md): precise public-source pins, package licensing, what client code proves, and what it does not prove.
5. [Target architecture](KLAINT_TARGET_ARCHITECTURE.md) and [competitive roadmap](KLAINT_COMPETITIVE_ROADMAP.md): proposals and estimates only, subordinate to canonical decisions.
6. [Access gaps](ACCESS_GAPS.md) and [reproduction guide](REPRODUCE.md): independently verify before accepting claims or transplanting code.

The [supplemental code inventory](SUPPLEMENTAL_PUBLIC_CODE.md), [research supervisor notes](SUPERVISOR_EVIDENCE.md), [original mission](DEEPSEEK_REA_MISSION.md), and [progress log](progress.txt) are retained as research provenance. The [report hashes](REPORT_HASHES.sha256) pin the exact imported research texts.

## Non-negotiable findings and limitations

- At the Wispral source pin used for this REA (`689a4e421d6f8acebedf15df1d2dfca0c905a835`), Klaint was **research/specification-only**. This study neither implements Klaint nor advances the authorized SpecGrain frontier.
- The historical Parlant tool-server-off instructions are superseded. The later verified Wispral plan assumes the tool server is reachable. Every tool route, including reads, must be separately authorized via broker-issued, single-use, proposal-bound capabilities. Caller-supplied customer IDs must not be trusted. The KT-01b negative probes and output BLOCK/STREAM tests remain acceptance gates before real customer data.
- **Python broker + DB ledger** is the canonical planned direction; **Rust broker/ledger** in portions of the REA is an **unratified alternative** requiring a formal decision/ADR. Read [architecture reconciliation](ARCHITECTURE_RECONCILIATION.md) before any implementation.
- Public Lorikeet SDKs, Parloa's public SDK, and Decagon's publicly distributed Duet CLI expose aspects of *client contracts*, not their closed-source production engine implementations. This study obtained **no private competitor backend code**.
- `@decagon-ai/duet-cli@0.6.1` has a restrictive platform-specific license: **do not import its code into Wispral** without an additional grant. The Lorikeet `mcp-server` and `web-sdk` packages do not publish a reusable license in the inspected distributions. Consult [source inventory](SOURCE_CODE_INVENTORY.md) before reuse.
- No direct competitive performance trial was run. Product and marketing statements, hypotheses, architectural proposals, latency targets, and cost estimates must remain labelled accordingly.

## Evidence and portability

The original REA was created in a **separate** local research workspace. References such as `sources/parlant/...` or `sources/evidence/...` in the imported reports refer to *that original research workspace*, **not to files committed under this directory**. No third-party source tree, npm archive, authentication material, raw site mirror, or executable agent instruction was imported into Wispral. To inspect or reproduce those references, follow [REPRODUCE.md](REPRODUCE.md), obtain the listed public revisions independently, and revalidate the rights and exact source lines. Vendor private documentation or proprietary engine code requires appropriately granted access; no such access was verified.

## Maintenance and implementation boundary

This folder is a fixed-date research snapshot. If upstream SDKs, Parlant, vendor APIs, licensing, or Wispral's canonical plan change, record a **new dated evidence revision** rather than silently treating this snapshot as current. Use the current `specs/CURRENT.md`, live `main`, reviewed decisions, and tests to select bounded implementation grains. Publishing this pack alone does **not** authorize production customer data, releases, or comparative superiority claims.
