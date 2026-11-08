# Plan validation

All results `REPRODUCED` locally on 2026-11-08 (Windows 11, Node 24.19.0, Python 3.14.7, jsonschema 4.26.0) on branch `planning/wispral-world-class-master-plan-20261108`. These checks prove planning-package integrity only. They are not product, security, benchmark or release evidence, and none of them replaces a governance-required check.

| Check | Command | Result |
| --- | --- | --- |
| PR #124 REA bundle integrity | `node research/rea/2026-10-21/validate_research.mjs` | `PASS` — 54 files, 132 catalog rows, 75 transplant rows, 0 failures |
| Design tokens: WCAG 2.2 contrast + accent/state hue separation | `node docs/design/tokens/check_contrast.mjs` | `PASS` — 94 contrast pairs (light and dark; canvas, surface, sunken, selected) and 40 hue checks; 0 failures |
| Core contracts: shape, runtime, sequence, cross-record bundles | `python -I docs/engineering/contracts/run_conformance.py` | `PASS` — 8 schemas, 94 cases (88 shape + 6 runtime), 10 sequences, 4 bundles |
| Fixture generator determinism | `build_cases.py` twice | Identical output (sha256 prefix `8dc9513a356b2f54`) |
| Packet generator determinism | `build_packets.py` twice | Identical `packets.json` and packets document |
| Plan validator | `node research/wispral-world-class/validate_plan.mjs` | See below |

## Plan validator checks

`validate_plan.mjs` enforces, over 73 packets and 27 planning documents:

1. Every packet has all required fields; `ready` is `false` for every packet.
2. Unique IDs; every dependency exists; the dependency graph is acyclic (topological order emitted).
3. Every `FORK`, `FORK_DELTA`, `COPY`, `ADAPT` and `WRAP` packet names a donor with a 40-hex commit SHA and source paths.
4. Every `BUILD_NEW` packet carries the five-part justification **and** cites a row that exists in the build-new register of `WISPRAL_COPY_FIRST_STRATEGY.md`.
5. Every `GRAIN_*` packet reaches the 000G decision (D0G) through dependencies; every `RESEARCH_000E/F` packet reaches F.
6. Tier and phase agree (M: P2/P3/P5/P6; S: P4/P7; L: P7/P8).
7. Every product packet requires all applicable checks green with no preserved red checks (only governance-lane packets may carry authority-preserved reds).
8. The first-ten list has exactly ten packets in dependency order.
9. Every relative link and heading anchor across the 27 documents resolves.
10. No superseded product name appears without a historical marker, and no comparative claim ("better than", "faster than", "outperforms", …) appears without a qualifier.

The validator caught real defects during this work and they were fixed rather than suppressed: 20 product packets without a path to D0G (found when check 5 was added after the testability review), one comparative phrase, and missing anchors.

## Second-round blocker check

A fresh-context reviewer (same model family as the author, so not a qualifying review) re-checked the seven blocker fixes on 2026-11-08. It judged every one **partially resolved** and named the remaining gaps. All were fixed in this branch:

| Blocker | Remaining gap found | Fix |
| --- | --- | --- |
| B1 transitional clause | Condition (ii) contradicted C1's expected scope reds; no checker hash; G1 not limited to `CONSTITUTION.md`; XVI.5 absent/skipped wording missing | (ii) excepts only the XVII-preserved scope reds on C1 and adopts XVI.5 wording; checker and test SHA-256 pinned (`b4ad0f3e…`, `3b144f15…`) and the checker bytes are part of G1's qualifying review; G1 limited to `CONSTITUTION.md`; C1 limited to its declared paths |
| B2 Principle XVII | Counterfactual could pass vacuously (gates absent); masking not addressed; purpose-based scope arguable; lowercase "must"; XVI.9 ancestry missing | Counterfactual runs the base-defined gate programs through the harness so the gate is evaluated in both runs; non-concealment requires every later step to run separately and pass; scope is an explicit annex with security steps (immutable-control boundary) kept unchanged in effect; MUST wording; ancestry verification added |
| B3 section rules | "Markers exactly once" already false on `main`; B2-owned undefined; Platform frontier ambiguous; stale Status line | Everything outside the allowlist is B2-owned and byte-identical; marker count and positions must equal the base and no marker may appear in allowlisted or Platform frontier sections; `main` itself is a positive fixture; the Status line deliberately stays B2's and platform status lives in the appended section |
| B4 qualifying review | "Substantive" and "resolve blocking findings" missing; owner/human reviews not recorded; "lineage" undefined | Governance item 7 requires a substantive review recorded on the PR with the head SHA and all blocking findings resolved; "different vendor" replaces "lineage" |
| B5 authority paths | Validator failed on a missing anchor; the second product Grain and speech packets had no opening packet | This section supplies the anchor; new packets D1G (second product decision) and SE-01 (speech-evaluation decision); the validator now also requires SPEECH_EVIDENCE, LATER_HORIZON and RELEASE packets to reach D0G |
| B6 plugin server | Security doc still allowed a socket variant; read-tool leakage untested; architecture implied port 8818 was live; tier S omitted it | Plugin tool server disabled in every Klaint process (socket variant rejected); forged-customer fixtures require zero effects **and zero data**; architecture and KT-02 updated |
| B7 keyboard recovery | Quick-panel key map not updated; no last-outcome shortcut row; Esc contradiction; error actions had no persistence route | Full key map with "Insert into the original target" as Enter (re-validated, never "current app"); last-outcome shortcut row; Esc captured only during capture; error actions listed under Needs attention |

Tool status at the time of the second-round check: contracts `PASS`, tokens `PASS`, plan validator `FAIL` on the then-missing anchor. After the fixes above, all three pass (table at the top of this file), with 73 packets.
