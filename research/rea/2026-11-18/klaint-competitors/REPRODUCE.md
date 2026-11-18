# REPRODUCE.md

**How to re-derive every claim in this mission from scratch, on Windows, without special access.**
**As of:** 2026-11-18 · **Reference workspace:** `D:\Klaint-REA-20261118`

Everything below was actually executed in this run unless marked *optional*. Commands are PowerShell, but they translate directly to bash.

---

## 1. Environment

Verified used:

| Tool | Version |
|---|---|
| Windows | 10/11 (win32) |
| PowerShell | 7.x (`pwsh`) |
| git | 2.56.0 |
| Python | 3.14.7 |
| Node.js | 24.19.0 (only needed to repack npm tarballs) |

No credentials, tokens, or cookies are required for anything in §3–§6. Two helpers already exist in the workspace:

- `tools_fetch.py` — reads `url|local/path` lines from stdin, fetches with a research user-agent, writes bytes, prints `status size content-type -> path`.
- `extract_text.py` — strips `script/style/svg/head`, converts block tags to newlines, unescapes entities, de-duplicates lines, writes a sibling `.txt`.

```powershell
# create the workspace
New-Item -ItemType Directory -Force D:\Klaint-REA-20261118\sources\evidence | Out-Null
Set-Location D:\Klaint-REA-20261118
```

---

## 2. Clone the benchmark and the donors (exact pins)

Anonymous clones. To reproduce the **exact** commit rather than today's default branch, fetch the commit directly:

```powershell
function Get-PinnedRepo($url, $sha, $dir) {
  git init $dir
  git -C $dir remote add origin $url
  git -C $dir fetch --depth 1 origin $sha
  git -C $dir checkout FETCH_HEAD
}
```

| Repository | URL | Pin | Licence | Purpose |
|---|---|---|---|---|
| Wispral | `https://github.com/TheHalfMoon/Wispral.git` | `689a4e421d6f8acebedf15df1d2dfca0c905a835` | see repo `LICENSE`/`NOTICE` | Benchmark product (specs only) |
| Lorikeet node SDK | `https://github.com/optechai/node-sdk.git` | `4bdaf93962d039938c2ef8526e6c55f41c40b1c7` | Apache-2.0 | API surface |
| Lorikeet mock API | `https://github.com/optechai/mock-api.git` | `d8e7b594544fbb2e315b11f34dad49d0ed5dc2b8` | see repo | Ingest protocol reference |
| Parloa Python SDK | `https://github.com/parloa-oss/parloa-sdk-python.git` | `873c3f437a373b1be77091aeb75786aa6dc36e02` | Apache-2.0 | API surface + types |
| Parlant | `https://github.com/emcie-co/parlant.git` | `4962e62bcd988ff65c1e41c4cc4ade7338efe0dd` (v4.0.6) | Apache-2.0 | Donor dialogue engine |
| Pipecat | `https://github.com/pipecat-ai/pipecat.git` | `257129f9395d5c5ed41bcc11608b751670e17032` | BSD-2-Clause | Donor voice pipeline |
| τ-bench 2.0 | `https://github.com/sierra-research/tau2-bench.git` | `c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4` | MIT | Evaluation harness |
| Standard Webhooks | `https://github.com/standard-webhooks/standard-webhooks.git` | `3d65b1824b6697f05a5a4584e7062bd23512fc8e` | Apache-2.0 | Webhook signing |
| Rasa OSS | `https://github.com/RasaHQ/rasa.git` | `60a3cff9c08183760355b07bd60f5223d8916d6b` (v3.6.21) | Apache-2.0 | Assessed, rejected |
| Chatwoot | `https://github.com/chatwoot/chatwoot.git` | `8b33b543fc45578d0518553edb8bc51d9603e48c` (v4.20.0) | MIT core; `enterprise/` separate | Handoff inbox |

Faster variant used in this run for speed (`--depth 1` on the default branch, then record the HEAD):

```powershell
git clone --depth 1 https://github.com/emcie-co/parlant.git sources\parlant
git -C sources\parlant rev-parse HEAD
git -C sources\parlant log -1 --format='%H %ad %s' --date=short
```

**Expected Wispral facts on re-clone:**
`git -C sources\wispral log -1 --format='%H %ad %s' --date=iso` → `689a4e4…` "plan: final Wispral master implementation plan — at the founder approval gate (#155)".

Disk: all clones together are small (no model weights, no LFS). Total workspace stayed far below the 5 GiB cap.

---

## 3. Repack the two npm artifacts

### 3.1 Decagon Duet CLI (proprietary — analysis only)

```powershell
npm pack @decagon-ai/duet-cli@0.6.1 --pack-destination sources\decagon-duet-cli
# produced: decagon-ai-duet-cli-0.6.1.tgz  (25,208 B; 81,700 B unpacked)
tar -xzf sources\decagon-duet-cli\decagon-ai-duet-cli-0.6.1.tgz -C sources\decagon-duet-cli
```

Expected contents (`Get-ChildItem -Recurse -File`):

```
LICENSE             3,344 B
package.json        1,273 B
README.md           1,161 B
dist/bin.mjs       75,922 B
```

If `npm` is unavailable, the registry tarball URL is
`https://registry.npmjs.org/@decagon-ai/duet-cli/-/duet-cli-0.6.1.tgz` — fetch with `tools_fetch.py`.

> **Licence gate.** `LICENSE` reads *"Decagon - Duet CLI License"*, © Decagon AI, Inc. 2026, and permits use/copy/distribution **solely** for using or connecting to the Decagon Platform under an executed agreement. It is **not** open source. Do not copy it into a Klaint repository, do not redistribute it, and do not commit it to a public mirror. Delete `sources/decagon-duet-cli` when the analysis is done.

### 3.2 Lorikeet React Native SDK (MIT)

```powershell
npm pack @lorikeetai/react-native-sdk@3.0.0 --pack-destination sources\lorikeet-react-native-sdk
tar -xzf sources\lorikeet-react-native-sdk\lorikeetai-react-native-sdk-3.0.0.tgz -C sources\lorikeet-react-native-sdk
```

`package.json` → `"name": "@lorikeetai/react-native-sdk"`, `"version": "3.0.0"`, `"license": "MIT"`.

### 3.3 Supplemental Lorikeet archives (2026-11-18)

These were fetched after the first pass. Nothing was installed or executed; tarballs were listed and extracted only.

```powershell
# 1. Org-hosted library (shallow clone: one visible commit, 2024-12-06)
git clone --depth 1 https://github.com/optechai/nestjs-temporal.git sources\lorikeet-nestjs-temporal
git -C sources\lorikeet-nestjs-temporal rev-parse HEAD       # expect da2f975def682e9da7b536aaa4d49c9ccc9aadbd
Get-Content sources\lorikeet-nestjs-temporal\LICENCE -TotalCount 3   # "MIT License", "Copyright (c) 2022 Zegue Kurt"

# 2-4. npm packages
npm pack @lorikeetai/mcp-server@1.0.0  --pack-destination sources\lorikeet-mcp-server
npm pack @lorikeetai/mcp-client@1.0.0  --pack-destination sources\lorikeet-mcp-client
npm pack @lorikeetai/web-sdk@1.13.0    --pack-destination sources\lorikeet-web-sdk
tar -xzf sources\lorikeet-mcp-server\lorikeetai-mcp-server-1.0.0.tgz -C sources\lorikeet-mcp-server
tar -xzf sources\lorikeet-mcp-client\lorikeetai-mcp-client-1.0.0.tgz -C sources\lorikeet-mcp-client
tar -xzf sources\lorikeet-web-sdk\lorikeetai-web-sdk-1.13.0.tgz     -C sources\lorikeet-web-sdk
```

| Check | Expected |
|---|---|
| `tar -tzf ...\lorikeetai-mcp-server-1.0.0.tgz` | exactly `package/package.json` and `package/README.md`; tarball 1,760 B; **no `dist/`, no `index.js`** |
| `Select-String ...\mcp-server\extracted\package\package.json -Pattern 'license'` | no match (no licence declared) |
| `tar -tzf ...\lorikeetai-mcp-client-1.0.0.tgz` | `package/src/index.ts` (983 B) and `package/example/dev.ts`; tarball 1,819 B; no `LICENSE` |
| `Select-String ...\mcp-client\extracted\package\package.json -Pattern 'license|description'` | `"license": "ISC"`, description `Dummy Lorikeet MCP Client example` |
| `tar -tzf ...\lorikeetai-web-sdk-1.13.0.tgz` | `dist/` + `README.md` + `CHANGELOG.md` only; tarball 32,185 B; no `src/`, no `LICENSE` |
| `Select-String ...\web-sdk\extracted\package\package.json -Pattern 'license|deploy'` | no licence field; deploy script targets `gs://resources.lorikeetcx.ai` |
| `Select-String ...\web-sdk\extracted\package\dist\*.js -Pattern 'https://[a-z\.]+'` | `https://chat.lorikeetcx.ai` |
| `Get-Content ...\web-sdk\extracted\package\dist\get-start-url.d.ts` | comment: URL "carries no credentials: those are handed to the iframe by `postMessage`" |

> **Licence gates.** `mcp-server` and `web-sdk` declare no licence: analysis only, no reuse. `mcp-client` declares ISC but ships no `LICENSE` file: keep the notice if any pattern is reused. `nestjs-temporal` is MIT but is a generic third-party library, not Lorikeet backend code.

---

## 4. Fetch the public pages

`tools_fetch.py` takes `url|path` lines on stdin. On PowerShell a here-string is the reliable way to pass several at once.

> Paths below are the site sections the saved evidence came from. Vendor sites reorganise; if a path 404s, open the site root and follow its navigation, then update the local filename. The saved copies in `sources/evidence/` are the authoritative record of what was actually read on 2026-11-18.

### 4.1 Lorikeet

```powershell
@"
https://www.lorikeetcx.ai/llms.txt|sources/evidence/lorikeet/llms.txt
https://www.lorikeetcx.ai/index.md|sources/evidence/lorikeet/index.md
https://www.lorikeetcx.ai/pricing.md|sources/evidence/lorikeet/pricing.md
https://www.lorikeetcx.ai/agents.md|sources/evidence/lorikeet/agents.md
https://www.lorikeetcx.ai/auth.md|sources/evidence/lorikeet/auth.md
https://www.lorikeetcx.ai/.well-known/ai-catalog.json|sources/evidence/lorikeet/ai-catalog.json
https://www.lorikeetcx.ai/product/guardrails|sources/evidence/lorikeet/product-guardrails.html
https://www.lorikeetcx.ai/product/simulations|sources/evidence/lorikeet/product-simulations.html
https://docs.lorikeetcx.ai/llms.txt|sources/evidence/lorikeet/docs-llms.txt
"@ | python tools_fetch.py
```

Lorikeet publishes Markdown "twins" of its pages. The doc pages used here (`doc-customer-authentication.md`, `doc-mcp-server.md`, `doc-faq.md`, `doc-trust-center.md`) come from the Lorikeet documentation index at `https://docs.lorikeetcx.ai/llms.txt` — open that index first, then fetch the `.md` URL it lists for each page.

Then convert HTML to text:

```powershell
python extract_text.py sources\evidence\lorikeet\product-guardrails.html sources\evidence\lorikeet\product-simulations.html
```

### 4.2 Parloa

```powershell
@"
https://www.parloa.com/|sources/evidence/parloa/site-home.html
https://www.parloa.com/platform/agent-builder/|sources/evidence/parloa/platform-agent-builder.html
https://www.parloa.com/platform/performance-lab/|sources/evidence/parloa/platform-performance-lab.html
https://www.parloa.com/platform/conversation-infrastructure/|sources/evidence/parloa/platform-conversation-infrastructure.html
https://www.parloa.com/platform/security/|sources/evidence/parloa/platform-security.html
https://www.parloa.com/platform/pricing/|sources/evidence/parloa/platform-pricing.html
https://www.parloa.com/platform/integrations/|sources/evidence/parloa/platform-integrations.html
https://www.parloa.com/blog/build-agents-your-way-introducing-parloa-s-agent-management-api-sdk-cli-and-mcp/|sources/evidence/parloa/blog-agent-management-api.html
https://docs.parloa.com/welcome-to-parloa.md|sources/evidence/parloa/docs-welcome.md
https://docs.parloa.com/llms.txt|sources/evidence/parloa/docs-llms.txt
https://docs.parloa.com/sitemap-pages.xml|sources/evidence/parloa/docs-sitemap-pages.xml
https://docs.amp.parloa.com/|sources/evidence/parloa/amp-docs-root.html
"@ | python tools_fetch.py
```

### 4.3 Decagon

```powershell
@"
https://decagon.ai/|sources/evidence/decagon/site-home.html
https://decagon.ai/product/voice|sources/evidence/decagon/product-voice.html
https://decagon.ai/product/aop|sources/evidence/decagon/product-aop.html
https://decagon.ai/product/testing-qa|sources/evidence/decagon/product-testing-qa.html
https://decagon.ai/security|sources/evidence/decagon/security.html
https://decagon.ai/trust|sources/evidence/decagon/trust.html
https://decagon.ai/blog/the-ai-agent-engine|sources/evidence/decagon/blog-agent-engine.html
https://decagon.ai/blog/evaluation-engine-ai-agents|sources/evidence/decagon/blog-evaluation-engine.html
https://decagon.ai/blog/from-sops-to-agent-operating-procedures|sources/evidence/decagon/blog-sops-to-aop.html
https://decagon.ai/blog/missions|sources/evidence/decagon/blog-missions.html
https://docs.decagon.ai/|sources/evidence/decagon/docs-root.html
"@ | python tools_fetch.py
```

`docs.decagon.ai` is expected to return an authentication shell — see `ACCESS_GAPS.md` §1.

### 4.4 Telephony and speech pricing

```powershell
@"
https://www.twilio.com/en-us/voice/pricing/us|sources/evidence/telephony/twilio-voice-us.html
https://deepgram.com/pricing|sources/evidence/telephony/deepgram-pricing.html
https://elevenlabs.io/pricing|sources/evidence/telephony/elevenlabs-pricing.html
"@ | python tools_fetch.py
```

Then extract all of them:

```powershell
python extract_text.py (Get-ChildItem sources\evidence -Recurse -Filter *.html).FullName
```

(`extract_text.py` writes `<same-name>.txt`.)

---

## 5. Verify the claims — command → expected output

Run from `D:\Klaint-REA-20261118`. These are the checks that back the report's strongest statements.

### 5.1 Klaint has no product code

```powershell
Select-String -Path sources\wispral\docs\canonical\CURRENT_STATE.md -Pattern "Active product implementation|Published release|product Rust/Cargo"
```
**Expected:** `Active product implementation: none`, `Published release: none`, `product Rust/Cargo implementation added: no`.

### 5.2 KT-01 is unresolved

```powershell
Select-String -Path sources\wispral\research\klaint-spike\README.md -Pattern "NOT VERIFIED|forged|STREAM|BLOCK"
```
**Expected:** KT-01 `NOT VERIFIED`; forged `customer_id` accepted; BAIL only effective in BLOCK mode.

### 5.3 Parlant 4.0.6 — the stream-gate limitation still stands

```powershell
Select-String -Path sources\parlant\src\parlant\core\engines\compass\loop\base_loop.py -Pattern "on_message_generated|observational|_maybe_review_message|_should_buffer_message_for_review"
```
**Expected:** a docstring stating that in streamed output the `on_message_generated` hook is observational (chunks already emitted), plus the reviewer/buffer functions.

### 5.4 Parlant 4.0.6 — the plugin tool server is still there

```powershell
Select-String -Path sources\parlant\src\parlant\core\services\tools\plugins.py -Pattern '/tools/\{name\}/calls|class CallToolRequest|customer_id'
Select-String -Path sources\parlant\src\parlant\sdk.py -Pattern 'tool_service_port|PluginServer|127.0.0.1'
```
**Expected:** the `/tools/{name}/calls` route at `plugins.py:851`; `CallToolRequest` fields `agent_id`, `session_id`, `customer_id` (`:607-612`); `PluginServer` started on `127.0.0.1` with `tool_service_port` default `8818` (`sdk.py:4961-4990`, `:3065`).

> **Correction note:** an earlier draft of this mission asserted that 4.0.6 removed this surface. It did not. The check above is the one that settles it; do not repeat the claim without running it.

### 5.5 Lorikeet API surface

```powershell
Select-String -Path sources\lorikeet-node-sdk\src\resources\conversation\chat.ts -Pattern "'/v1/|DraftResponse|Escalated"
Select-String -Path sources\lorikeet-node-sdk\src\resources\conversation\voice\web.ts -Pattern "wsUrl|token|livekit"
Select-String -Path sources\lorikeet-node-sdk\src\lib\generate-signature.ts -Pattern "createHmac|sha256|base64url"
```
**Expected:** chat create/message paths and the `DraftResponse`/`Escalated*` status union; `wsUrl` + LiveKit `token`; HMAC-SHA256 with base64url output.

### 5.6 Lorikeet pricing

```powershell
Select-String -Path sources\evidence\lorikeet\pricing.md -Pattern "2,100|5,100|75K|0.99|1.50|0.90|1.20|3 min average"
```
**Expected:** Start `$2,100/mo`, Scale `$5,100/mo`, Signature `$75K` platform fee; `$0.99` / `$1.50` (Start), `$0.90` / `$1.20` (Scale); voice note "3 min average".

### 5.7 Lorikeet ingest protocol (async window)

```powershell
Select-String -Path sources\lorikeet-mock-api\README.md -Pattern "10 seconds|10 minutes|x-optech-signature|202"
```
**Expected:** `200` immediate, or `202` then respond within 10 s (chat) / 10 min (email); `x-optech-signature` header.

### 5.8 Parloa SDK — deterministic orchestration and identity rules

```powershell
Select-String -Path sources\parloa-sdk-python\src\parloa\types\pipeline.py -Pattern "Execution order"
Select-String -Path sources\parloa-sdk-python\src\parloa\types\barge_in.py -Pattern "barge_in_after_ms|barge_in_min_words|is_enabled"
Select-String -Path sources\parloa-sdk-python\src\parloa\types\authentication_customer_identity.py -Pattern "system variable|header|output|sensitive"
```
**Expected:** "Execution order is owned by the runtime"; the three barge-in fields; identity-key constraints forbidding system variables/headers.

### 5.9 Parloa endpoints

```powershell
Select-String -Path sources\parloa-sdk-python\src\parloa\agent_blueprints\raw_client.py -Pattern "v1/agent-blueprints"
Select-String -Path sources\parloa-sdk-python\src\parloa\simulations\raw_client.py -Pattern "v1/simulations"
```
**Expected:** `v1/agent-blueprints`, `…/deployments`, `v1/simulations/definitions`, `v1/simulations/runs`, `:batch`, `:cancel`.

### 5.10 Decagon CLI hosts and routes (static only)

```powershell
Select-String -Path sources\decagon-duet-cli\package\dist\bin.mjs -Pattern "api.decagon.ai|eu.api.decagon.ai|au.api.decagon.ai|/deca_agent/"
```
**Expected:** the three regional hosts and `/deca_agent/cli/device_codes`, `/deca_agent/chat/completion`, `/deca_agent/config`.

### 5.11 Decagon licence is restrictive

```powershell
Get-Content sources\decagon-duet-cli\package\LICENSE -TotalCount 12
```
**Expected:** "Decagon - Duet CLI License", "Copyright Decagon AI, Inc. 2026", permitted use limited to the Decagon Platform under an executed agreement.

### 5.12 Chatwoot licence split

```powershell
Get-Content sources\chatwoot\LICENSE -TotalCount 8
Get-ChildItem sources\chatwoot\enterprise -Filter LICENSE -Recurse | ForEach-Object { Get-Content $_.FullName -TotalCount 5 }
```
**Expected:** MIT for the core; a separate commercial licence for `enterprise/`.

### 5.13 Rasa is in maintenance mode

```powershell
Select-String -Path sources\rasa\README.md -Pattern "maintenance mode|Hello Rasa|CALM"
git -C sources\rasa log -1 --format='%H %ad' --date=short
```
**Expected:** the maintenance-mode sentence; last commit `60a3cff…`, 2025-12-18.

### 5.14 τ-bench has no Arabic pack

```powershell
Select-String -Path sources\tau2-bench\README.md -Pattern "English|Spanish|Portuguese|Hindi|Chinese|Korean|Arabic"
Get-ChildItem sources\tau2-bench -Recurse -Directory | Where-Object Name -match "arab"
```
**Expected:** six languages listed, no Arabic; no `arab*` directory.

### 5.15 Telephony rates used in the TCO model

```powershell
Select-String -Path sources\evidence\telephony\twilio-voice-us.txt -Pattern "0.0085|0.0140"
Select-String -Path sources\evidence\telephony\deepgram-pricing.txt -Pattern "0.0065|0.0077"
```
**Expected:** Twilio US inbound `$0.0085`/min, outbound `$0.0140`/min; Deepgram streaming `$0.0065`/min.

### 5.16 Parloa public docs are one page

```powershell
Get-Content sources\evidence\parloa\docs-sitemap-pages.xml
Get-Content sources\evidence\parloa\doc-ask-tokens.md
```
**Expected:** a sitemap with exactly one `<loc>`; a docs-agent answer stating it cannot verify the token/authorization model from available documentation.

---

## 6. Access checks (negative results, reproducible)

```powershell
# GitHub org / package existence
curl.exe -s -o NUL -w "%{http_code}`n" https://api.github.com/orgs/decagonai
curl.exe -s -o NUL -w "%{http_code}`n" https://pypi.org/pypi/decagon/json
curl.exe -s -o NUL -w "%{http_code}`n" https://pypi.org/pypi/parloa/json
curl.exe -s -o NUL -w "%{http_code}`n" https://api.decagon.ai/
```

Expected: `404`, `404`, `200`, `403`.
Anonymous GitHub API is limited to 60 requests/hour (search: 10/minute); budget accordingly or the results become `403 rate limit`.

---

## 7. Evidence index

| Folder | Contents | Evidence type |
|---|---|---|
| `sources/wispral` | Program docs, invariants, KL-T3, KT-01 spike | SOURCE-VERIFIED (specs) |
| `sources/lorikeet-node-sdk` | Generated client + resources | SOURCE-VERIFIED |
| `sources/lorikeet-mock-api` | Ingest reference + README protocol | SOURCE-VERIFIED |
| `sources/lorikeet-react-native-sdk` | npm tarball extract | OBSERVED |
| `sources/parloa-sdk-python` | Generated client + `types/` | SOURCE-VERIFIED |
| `sources/parlant` | v4.0.6 engine | SOURCE-VERIFIED |
| `sources/pipecat` | Voice framework | SOURCE-VERIFIED |
| `sources/tau2-bench` | Benchmark harness | SOURCE-VERIFIED |
| `sources/standard-webhooks` | Spec + libs | SOURCE-VERIFIED |
| `sources/rasa` | v3.6.21 | SOURCE-VERIFIED |
| `sources/chatwoot` | v4.20.0 | SOURCE-VERIFIED |
| `sources/decagon-duet-cli` | Proprietary CLI tarball + extract | SOURCE-VERIFIED (static) / **no reuse** |
| `sources/evidence/lorikeet/*` | `llms.txt`, pricing, guardrails, simulations, auth, MCP docs | DOCS/MARKETING |
| `sources/evidence/parloa/*` | Product pages, security, pricing, integrations, AMP shell, docs | DOCS/MARKETING |
| `sources/evidence/decagon/*` | Product pages, security, four blogs, docs shell | MARKETING / VENDOR-ENGINEERING |
| `sources/evidence/telephony/*` | Twilio, Deepgram, ElevenLabs pricing | DOCS-VERIFIED |

---

## 8. Rebuild the deliverables

The reports are static Markdown and were written by hand from the evidence above; there is no generator. To rebuild:

1. Run §2–§4 to repopulate `sources/`.
2. Run §5 to confirm each quoted line still exists at the same location.
3. If a vendor page changed, update the quote **and** the as-of date — do not silently carry a stale claim forward.

Order of authority when sources disagree:

```
pinned source code  >  official docs at URL+date  >  public package artifact  >  vendor marketing  >  inference
```

---

## 9. What cannot be reproduced (and why)

| Item | Reason |
|---|---|
| Decagon API schemas | Login-gated (`ACCESS_GAPS.md` G1) |
| Decagon console behaviour | Requires an approved account |
| Parloa AMP Studio docs | Whitelisted login |
| Any competitor latency or accuracy figure | Not published; no instrumented access |
| Arabic/dialect quality of any competitor | No public evidence exists to reproduce |
| Private repositories | None were provided; connected-account search returned no matches |

If any of these becomes available, re-run §5 with the new source and mark the affected rows in `COMPETITOR_EVIDENCE_MATRIX.md` from `claim/UNK` to the new evidence type.

---

## 10. Housekeeping and legal

- **Do not commit** `sources/decagon-duet-cli/` to any public repository; its licence forbids redistribution outside the Decagon Platform relationship.
- Keep `NOTICE`/licence files when reusing Apache-2.0 or BSD code (Lorikeet SDK patterns, Parloa types, Parlant, Standard Webhooks, Pipecat).
- Do **not** copy `sources/chatwoot/enterprise/` into a Klaint build.
- Wispral is research-only in this mission: no file under `sources/wispral` was modified. Verify with `git -C sources\wispral status --porcelain` (expected: empty).
- Total disk for this mission is small (tens of MB of code + a few MB of HTML); well under the 5 GiB budget. The largest items are the four Decagon marketing HTML files (~400 KB each).
