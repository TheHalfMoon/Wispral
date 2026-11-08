# Current-state inventory (live truth, 2026-11-08)

All facts `RUNTIME_OBSERVED` through the GitHub API or `REPRODUCED` locally on 2026-11-08 unless marked. Proposed documents are never treated as adopted governance.

## Canonical repository

| Item | State |
| --- | --- |
| `main` | `edacdf7504302cc91ff7138bc6ac2d391e4df1f4` — "docs(000b2): reconcile B2R16 to B2R17 (#118)", 2026-09-10. Unchanged since. |
| Constitution | v0.2.1 (amended 2026-09-09). Mission: voice-native control plane for AI coding agents; "not a dictation application" (`AGENTS.md:3`) |
| Product-code gate | Closed until Specification 000 synthesis reaches 000G and selects a bounded first Grain |
| Executable frontier | `specs/CURRENT.md`: B2R17 is the sole active successor unit; ATTEMPT-003 frozen; primary decode entry open for B2R17 only; scoring closed; `production_stt_selected=false`; `product_code_authorized=false` |
| Founding children | 000A verified (ACP `PARTIAL`/`MODERATE`); 000B open (B2 at B2R17; B3/B4 coarse); 000C–000G coarse, not started |
| Branch protection | None: classic protection 404 "Branch not protected"; rulesets `[]` |
| License | **None** (`gh api` license = none) |
| Workflows | 27 under `.github/workflows`; inventory in [governance report §2](evidence/research-reports/GOVERNANCE_CI_RESEARCH.md#2-task-1-workflow-inventory-on-main) |

## Open pull requests and issue

| # | State | Head | Content | Checks (relevant) | Disposition proposed |
| --- | --- | --- | --- | --- | --- |
| [#120](https://github.com/TheHalfMoon/Wispral/pull/120) | open | `85fe8102` | B2R17 Moonshine-compact capture (209/240 decoded, 31 harness-bound failures, unscored); owner comment "MUST NOT MERGE" | B2 gates pass; `verify-b2r16-freeze` fails | Requalify after correction C (B2-R17 lane) |
| [#121](https://github.com/TheHalfMoon/Wispral/pull/121) | open | `61cdfc5e` | Graft context tooling (`AGENTS.md`) | freeze fails | Independent of this plan |
| [#123](https://github.com/TheHalfMoon/Wispral/pull/123) | draft | `34263e99` | Founder source-rights and product-identity record | freeze fails | Carried by this PR's ancestry |
| [#124](https://github.com/TheHalfMoon/Wispral/pull/124) | draft | `e7064c78` | Copy-First Master Plan V3 + REA bundle (56 files), Opus-repaired | freeze fails | Carried by ancestry; strategy docs superseded for planning by this package |
| [#125](https://github.com/TheHalfMoon/Wispral/pull/125) | draft | `3de63649` | Independent Opus review of #124 (REVISE; M1–M5, S1–S8) | freeze fails | Carried by ancestry |
| [#126](https://github.com/TheHalfMoon/Wispral/pull/126) | draft | `a97d596b` | B2R16 freeze preservation repair | freeze passes on its own definition; both B2 trusted gates fail (scope) | Absorbed by correction C with four fixes |
| [#122](https://github.com/TheHalfMoon/Wispral/issues/122) | open issue | — | Founder mission: deep source audit, REA, copy-first replanning | — | Addressed by this package |

No PR, issue or comment changed after 2026-10-21 (`RUNTIME_OBSERVED`).

## Prior evidence re-validated on this branch

| Check | Result |
| --- | --- |
| PR #124 bundle validator `validate_research.mjs` | `PASS` — 54 files, 132 catalog rows, 75 transplant rows, 0 failures (`REPRODUCED`) |
| PR #124 schema negative fixtures `test_research_schema.mjs` | Missing-field rejections as expected (`REPRODUCED`) |
| `verify_b2r16.py --require-git` on `main`, #124, #126, #120 heads | `FAIL: B2R16 actual candidate range scope drift` on all four (`REPRODUCED`) |
| #126 preservation suite | 7/7 PASS locally in 366 s (`REPRODUCED`) |
| Gate harness (main's inline gate programs) | #126 fails both gates; #120 passes both — matches CI (`REPRODUCED`) |

## Reference hardware

Founder machine (HW-A): Intel Core i5-13420H (8 cores / 12 threads), 16 GB RAM, Intel UHD integrated graphics only, Windows 11 Home build 26300, WSL2 Ubuntu (`RUNTIME_OBSERVED`).
