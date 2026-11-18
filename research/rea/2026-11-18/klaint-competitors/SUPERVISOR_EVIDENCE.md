# Supervisor evidence — 2026-11-18

This file contains independently checked leads for DeepSeek's final audit. Do not treat any code as licensed for Klaint reuse without verifying conditions.

## Decagon actual distributable
- Registry: https://www.npmjs.com/package/@decagon-ai/duet-cli
- Version downloaded: 0.6.1, tarball at sources/decagon-duet-cli/decagon-ai-duet-cli-0.6.1.tgz, extracted at sources/decagon-duet-cli/package/
- metadata: published public package, 81,700 bytes unpacked; includes dist/bin.mjs, README.md, LICENSE.
- LICENSE says "Decagon - Duet CLI License", copyright Decagon AI Inc. 2026; permits use/copy/distribution solely for using/connecting to the Decagon Platform pursuant to an executed platform Agreement. This is restrictive, NOT an open-source license. Do not transplant or redistribute into Klaint without documented separate license grant.
- node >=22; eventsource-parser 3.1.0, tsdown build; requires approved Decagon account (package description). Do not use authenticated platform features without user-provided authorized account access.
- Official recent capability: https://decagon.ai/blog/missions posted 2026-11-12: long-running coordinated work across days/weeks. Treat as vendor claim, not source-verified backend.
- Official engineering sources: https://decagon.ai/blog/the-ai-agent-engine ; https://decagon.ai/blog/evaluation-engine-ai-agents ; https://decagon.ai/blog/introducing-decagon-labs ; https://decagon.ai/blog/from-sops-to-agent-operating-procedures

## Lorikeet code
- Official-linked GitHub repo https://github.com/optechai/node-sdk.git clone in sources/lorikeet-node-sdk at 4bdaf93962d039938c2ef8526e6c55f41c40b1c7; README calls it Lorikeet TypeScript API Library (Stainless-generated), Apache-2.0. Not backend engine.
- Published npm @lorikeetai/react-native-sdk@3.0.0 (MIT) extracted in sources/lorikeet-react-native-sdk; UI wrapper not backend.
- https://www.lorikeetcx.ai/integrations/lorikeet-sdk says REST APIs and client libraries support chat and voice workflows.

## Parloa code
- https://github.com/parloa-oss/parloa-sdk-python.git cloned at 873c3f437a373b1be77091aeb75786aa6dc36e02, Apache-2.0.
- The historical PyPI provenance link github.com/parloa/parloa-sdk-python may now 404; live public repo is parloa-oss/parloa-sdk-python. Verify current URL and avoid claiming deleted repo accessible.
- https://www.parloa.com/blog/build-agents-your-way-introducing-parloa-s-agent-management-api-sdk-cli-and-mcp/ dated 2026-11-02.
- https://github.com/parloa-oss/ explicitly says Parloa's platform and customer-data-handling systems remain closed source.

## Private access
- GitHub connected-account installed-repo searches for Lorikeet, Decagon, and Parloa (both connected accounts) returned no matching installed competitor repositories. User-stated permission is not a substitute for actual repository access. Record ACCESS_GAPS for official private access provision.
