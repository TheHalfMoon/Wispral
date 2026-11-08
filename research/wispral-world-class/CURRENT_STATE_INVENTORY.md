# Current-state inventory (live truth, 2026-11-08)

All facts `RUNTIME_OBSERVED` through the GitHub API or `REPRODUCED` locally on 2026-11-08 unless marked. Proposed documents are never treated as adopted governance.

## Canonical repository

| Item | State |
| --- | --- |
| `main` | `5879c43c7a389bd460955f2e181e8bd70f0ecee5`: the C1 merge (#130), 2026-11-08. Before it: `8d52a45` (G1, #129), then `edacdf7` (#118, 2026-09-10) |
| Constitution | **v0.3.0**: Principle XVII (over-application correction lane) and Governance item 7 (qualifying independent review). Mission text unchanged: voice-native control plane for AI coding agents; "not a dictation application" (`AGENTS.md:3`) |
| Freeze control | Base-defined since C1 (`pull_request_target`, `push`, `workflow_dispatch`); `push` run on `5879c43` PASS (run 42446197959) |
| Red check on `main` | `000B2 Public Corpus ATTEMPT-003 Recovery` push run on `5879c43` FAIL (run 42446198003): the preserved B2 scope-classification failure, until C2 |
| Product-code gate | Closed until Specification 000 synthesis reaches 000G and selects a bounded first Grain |
| Executable frontier | `specs/CURRENT.md`: B2R17 is the sole active successor unit; ATTEMPT-003 frozen; primary decode entry open for B2R17 only; scoring closed; `production_stt_selected=false`; `product_code_authorized=false` |
| Founding children | 000A verified (ACP `PARTIAL`/`MODERATE`); 000B open (B2 at B2R17; B3/B4 coarse); 000C–000G coarse, not started |
| Branch protection | None (classic protection "Branch not protected"; no rulesets). Missing protection is not permission |
| License | **None** |
| Workflows | 27 under `.github/workflows` |

## Pull requests and issue (2026-11-08)

| # | State | Content | Disposition |
| --- | --- | --- | --- |
| [#129](https://github.com/TheHalfMoon/Wispral/pull/129) | **merged** `8d52a45` | G1: Constitution 0.3.0 | Done. Waivers recorded on the PR; A040 ratifies them |
| [#130](https://github.com/TheHalfMoon/Wispral/pull/130) | **merged** `5879c43` | C1: base-defined freeze correction | Done. Qualifying review recorded |
| [#133](https://github.com/TheHalfMoon/Wispral/pull/133) | open | A040: Constitution 0.4.0 (another session on the owner's account) | Next governance step; update its #130 clause; qualifying review |
| [#128](https://github.com/TheHalfMoon/Wispral/pull/128) | draft | This planning package (PLAN) | Qualifying review, then owner merge |
| [#127](https://github.com/TheHalfMoon/Wispral/pull/127) | draft | Alternative 0.3.0 draft | Superseded by #129; close |
| [#126](https://github.com/TheHalfMoon/Wispral/pull/126) | closed | B2R16 freeze repair | Absorbed by C1 |
| [#120](https://github.com/TheHalfMoon/Wispral/pull/120) | open | B2R17 Moonshine-compact capture; owner comment "MUST NOT MERGE" | Requalify after C2 (B2-R17 lane) |
| [#121](https://github.com/TheHalfMoon/Wispral/pull/121) | open | Graft context tooling | Independent |
| [#123](https://github.com/TheHalfMoon/Wispral/pull/123) | draft | Founder source-rights and product-identity record | Carried by this PR's ancestry |
| [#124](https://github.com/TheHalfMoon/Wispral/pull/124) | draft | Copy-First Master Plan V3 + REA bundle, plus #131/#132/#134 (V3 sequence alignment, audit, W0 pointer) | Carried up to #125 by ancestry. Its execution sequence is superseded by this plan's §2 sequence; the audit is used as input |
| [#125](https://github.com/TheHalfMoon/Wispral/pull/125) | merged into #124's branch | Opus review of #124 | Carried |
| [#122](https://github.com/TheHalfMoon/Wispral/issues/122) | open issue | Founder mission | Addressed by this package |

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
