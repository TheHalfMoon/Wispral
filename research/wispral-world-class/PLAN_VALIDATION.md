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

`validate_plan.mjs` enforces, over 71 packets and 27 planning documents:

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

**Status:** running — a focused re-check of the seven blocker fixes by a fresh-context reviewer. Its verdicts are recorded here when it completes.
