# Catalogue errata (CORE-00)

Corrections to earlier source records. The historical files are not rewritten (they are evidence of what was believed at the time). Each correction is recorded here, and later records use the corrected key.

| ID | Record | Was | Now | Evidence |
| --- | --- | --- | --- | --- |
| E-01 | `research/rea/2026-10-21/SOURCE_CATALOG.md` and `source-catalog.json`, `core-source-evidence.json` | `TheHalfMoon/wepld` | **`TheHalfMoon/Zain`**. The repository was renamed: `gh api repos/TheHalfMoon/wepld` resolves to `TheHalfMoon/Zain`. | Zain HEAD `0a843a2c0913236d9c93b31abb0d54bbdb023f23` equals the old `wepld` pin, and its README still reads "WePLD" (anchor `ERRATA-ZAIN`, PASS). The decision is unchanged: REJECTED for Wispral. |
| E-02 | PR #124 transplant rows `CORE-ACP` and `CORE-CANCEL` | anchored at ACP rust-sdk `652d1003` (3.4.0), including `capabilities.rs` | Re-anchored at rust-sdk **5.0.0** `050cd94c081056ace37a7b89abfed7f6220b47eb`: `src/agent-client-protocol/src/concepts/cancellation.rs` and `session.rs`. `capabilities.rs` no longer exists. | Anchors `CO-SRC-08a`/`08b` PASS |
| E-03 | PR #124 transplant row `CORE-AUDIT` | `orcel-audit` at Orcel `57af189b` | **`CORE-JOURNAL`**: `crates/orcel-journal/src/{lib.rs,resume.rs}` at Orcel `f0b78e6544cf6ea9c2457a6b6f483490c7bd0f6f`, the better donor for the intent journal | Anchors `CO-SRC-03a`/`03b` PASS |
| E-04 | `SOURCE_DECISION_MATRIX.md` short pins | `standard-webhooks@ab68441`, `tau2-bench@033bf08`, `chatterbox@5de7a54a`, `Ninerr@8cba15c4` | Full SHAs: `ab6844147ce9cdb0d2dbf2e60d1ea85001fd2554`, `033bf082f48e4a3c6a1256208e93cf2ce9c3bb6f`, `5de7a54aa4e5e2baadb0182dde554908b48b85c2`, `8cba15c4e4af40b12476433a49e20a1696cfc0f8` | Resolved through the commits API; the anchors at these commits PASS |
| E-05 | Licence column for VoiceInk, VoiceStudio and Chatwoot | The licence API reports `NOASSERTION` | Read from the LICENSE text at the pin: GPL-3.0, AGPL-3.0, and MIT outside `enterprise/` | `RIGHTS_REGISTER.md` §2 |
