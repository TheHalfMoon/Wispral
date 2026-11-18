# Supplemental code inventory verification — 2026-11-18

Further public packages were downloaded to `sources/` after the initial report.

1. `optechai/nestjs-temporal` — official-linked organisation repository, cloned to `sources/lorikeet-nestjs-temporal`, Git HEAD `da2f975def682e9da7b536aaa4d49c9ccc9aadbd`, MIT license present in cloned repository. It is a NestJS/Temporal integration library, **NOT** proof that Lorikeet's production scheduler runs this code. Inspect relevant modules before borrowing. Do not overclaim that it is their backend.
2. npm `@lorikeetai/mcp-server@1.0.0` downloaded and extracted at `sources/lorikeet-mcp-server/extracted/package`. Observed files are only `README.md` and `package.json`; package metadata has no declared license field. README describes Lorikeet workflow MCP with API credentials, but this archive does **not** contain working server implementation. Evidence only. **No license = no redistribution/reuse permission implied.**
3. npm `@lorikeetai/mcp-client@1.0.0` downloaded to `sources/lorikeet-mcp-client/extracted/package`. npm `package.json` says ISC license; source `src/` and `example/` included. Investigate what these expose. Keep license/notice.
4. npm `@lorikeetai/web-sdk@1.13.0` downloaded and extracted at `sources/lorikeet-web-sdk/extracted/package`. README says Chat and Voice Widget SDK loaders and hosted iframe under `apps/chat`; archive contains `dist/` and changelog; metadata has NO license field. Do not assume reusable until separate grant. Widget integration is not proprietary workflow backend.
5. npm `@lorikeetai/react-sdk` returned HTTP 404 on registry 2026-11-18. No inference about other React libraries.
6. npm `@decagon-ai/duet-cli@0.6.1` remains proprietary restrictive; source in `sources/decagon-duet-cli/package` is analyzed only, not suitable for transplant.

All additional archives were retrieved from normal public npm/GitHub package distribution without running scripts or connecting to vendor private systems. The main REA research findings should remain grounded by exact pins and licenses.
