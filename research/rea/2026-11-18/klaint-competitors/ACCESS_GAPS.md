# ACCESS_GAPS.md

**Mission:** Klaint (TheHalfMoon/Wispral) vs Lorikeet CX, Decagon, Parloa
**As of:** 2026-11-18
**Purpose:** record exactly what non-public material was *not* available, why, what official access would close each gap, and how each gap limits the conclusions in this report.

> **Rules followed.** No login control was bypassed. No credential, token, cookie, or session value was captured, printed, or retained. No private endpoint was probed. No target was scanned or exploited. Where a page returned a login shell, it was saved as-is and labelled `UNKNOWN`. `api.decagon.ai` root returning 403 was recorded as an observation and not retried with altered headers.
>
> **What "permission" does and does not mean.** The mission states the user has permission to use competitor code. Permission from the user is not evidence that a private repository exists, that an account exists, or that a licence grants reuse. GitHub connected-account searches for installed competitor repositories returned **no matches** for all three vendors (see §7). Therefore every absence below is an *access* fact, not a judgment about the vendor.

---

## 0. Summary table

| # | Material | Why unavailable | Official access needed | Impact if unclosed |
|---|---|---|---|---|
| G1 | Decagon developer docs (`docs.decagon.ai`) | Login wall; page renders an auth shell (31,769 B HTML, **0 B extractable text**) | Approved Decagon org + developer seat | Decagon API/AOP semantics stay `UNKNOWN`; matrix rows marked claim-only |
| G2 | Decagon API host (`api.decagon.ai`) | Root returns **HTTP 403** | Approved account + API credentials issued by Decagon | No independent endpoint/schema verification |
| G3 | Decagon console (AOP editor, Duet, Missions, Watchtower, Insights) | Authenticated product | Demo/trial tenant | Authoring UX, versioning, eval UI judged from marketing only |
| G4 | Decagon pricing | No public pricing page (404) | Written enterprise quote | TCO comparison is structural, not numeric |
| G5 | Parloa technical docs (`docs.amp.parloa.com`) | AMP Studio SPA behind login; build `40ea248` (2026-11-10) | Parloa tenant/partner account | Runtime behaviour, auth internals, quotas `UNKNOWN` |
| G6 | Parloa rate card | Not published (consumption, complexity-based) | Written quote for a defined volume | Unit-economics comparison limited to structure |
| G7 | Parloa sandbox traces / determinism proof | Authenticated environment | Sandbox tenant + trace export | "Runtime owns execution order" remains a contract reading, not observed behaviour |
| G8 | Lorikeet tenant, workflow engine, guardrail internals | Authenticated product | Trial tenant + permission to run a controlled forged-caller test | Guardrail precision, tool enforcement, latency `UNKNOWN` |
| G9 | All three: private source repositories | No repository made available; connected-account search empty | Signed repo invitation + written licence grant | Backend implementation claims stay out of scope |
| G10 | Arabic/dialect quality evidence (all three) | None found in the public sources reviewed | Vendor-supplied eval or joint blind test | No competitor dialect score can be assigned - and none is |
| G11 | Compliance reports (SOC 2, ISO, pen tests) | Under NDA/trust-center request | NDA + trust center access | Certification rows remain vendor claims |
| G12 | Decagon Duet CLI authenticated behaviour | CLI requires approved account; licence restricts use to the Decagon Platform | Written authorisation to run inside a test workspace | CLI examined statically only (`dist/bin.mjs`), never executed against the API |
| G13 | Competitor production latency/telemetry | Internal | Instrumented pilot | No p50/p95/p99 numbers for any competitor; none invented |

---

## 1. Decagon

### 1.1 Developer documentation — blocked

**Attempted:** `https://docs.decagon.ai/` and a documentation path, 2026-11-18.
**Result:** an authentication shell. Saved as `sources/evidence/decagon/docs-root.html` (31,769 bytes). Text extraction produced **0 bytes** (`docs-root.txt`), i.e. there is no readable content without signing in. The page advertises a login, not a 404 — so the docs exist behind authentication, they are not absent.

**What this means:** every statement about Decagon's API surface in this report is derived from the **bundled Duet CLI** (`@decagon-ai/duet-cli` 0.6.1, `dist/bin.mjs`) plus vendor marketing. That is enough to name hosts and a handful of `/deca_agent/*` routes, and not enough to describe request/response schemas, pagination, error models, webhooks, or auth scopes.

**Access needed:** an approved Decagon customer organisation plus a developer/API seat, or a documentation export under NDA.

### 1.2 API host — 403

**Attempted:** `https://api.decagon.ai/` (root), 2026-11-18 → **HTTP 403**.
This is expected for an authenticated API and was not retried with modified headers. Recorded as `UNKNOWN`, not as evidence of a vulnerability or of absence.

### 1.3 Product console and Duet authenticated paths

The Duet CLI (public npm, **proprietary licence**) documents device-code login, team selection, `ask`, file upload, and chat completion. It was **not executed**. Running it requires an approved Decagon account, and the licence permits use only to connect to the Decagon Platform under an executed agreement (`package/LICENSE:1-30`). Static inspection only.

**Access needed:** written authorisation plus a test workspace, if Klaint ever wants observed Duet behaviour. Absent that, the CLI remains an architectural signal (multi-region control plane, team-scoped tokens, conversational authoring), not a tested product.

### 1.4 Pricing

No public pricing page. No quote requested on the user's behalf. All Decagon cost statements in this report are structural (enterprise quote, unknown floor), never numeric.

---

## 2. Parloa

### 2.1 Public docs are a single page — confirmed by two independent signals

1. `https://docs.parloa.com/sitemap-pages.xml` lists **exactly one URL** (`https://docs.parloa.com`, lastmod 2026-10-29). Saved as `sources/evidence/parloa/docs-sitemap-pages.xml`.
2. The site's own agent interface (`GET https://docs.parloa.com/index.md?ask=...&goal=...`) answered a direct question about token scoping with: *"I can't verify the Agent Management API's token scopes or how it enforces read-only access from the available documentation. The AMP Documentation is the relevant reference, but the available content doesn't describe its token or authorization model."* — saved as `sources/evidence/parloa/doc-ask-tokens.md`.

That second result is important: **the vendor's own documentation agent cannot answer questions beyond the landing page.** Technical content lives in AMP Studio.

The landing page itself says so, for the adjacent documentation spaces: *"The documentation spaces below require you to login separately. You must be whitelisted. Please contact your Parloa representative."* (`sources/evidence/parloa/docs-welcome.md`, "Additional Documentation" card). Parloa operates a whitelist model for its deeper documentation; that is a legitimate access control, not a defect, and it was respected.

### 2.2 AMP Studio — login wall

`https://docs.amp.parloa.com/` returns the AMP Studio single-page-app shell (2,908 bytes), with build metadata `build-commit: 40ea248`, `build-date: Tue Nov 10 15:39:51 2026 +0000`, and a CSP that forbids `object-src`. No documentation content is served to an unauthenticated client. Saved as `sources/evidence/parloa/amp-docs-root.html` and `amp-developer.html` (identical bytes).

**Access needed:** a Parloa tenant or partner account (SSO), or a documentation export.

### 2.3 What the public SDK does and does not cover

The Apache-2.0 Python SDK (`parloa-oss/parloa-sdk-python`, pinned `873c3f437a373b1be77091aeb75786aa6dc36e02`) is unusually rich: agent blueprints, drafts, versions, deployments, simulations, evaluations, hooks, connectors, STT/TTS types, authentication flows. It proves the **contract shape**.

It does **not** prove: server-side enforcement of those contracts, actual latency, true regional isolation ("Parloa Zones"), quota behaviour, or whether the 140+ language claim includes Gulf/Levantine/Egyptian dialects. Those stay `UNKNOWN`.

### 2.4 Pricing

Published model: per minute (voice), per interaction (chat), complexity tiers, volume commitment, outcome-based option. **No rate card.** Saved as `sources/evidence/parloa/platform-pricing.txt`. Any Klaint price comparison against Parloa must be marked "structure only".

---

## 3. Lorikeet CX

### 3.1 What is open (and it is genuinely open)

- `optechai/node-sdk` — Apache-2.0, Stainless-generated, pinned `4bdaf93962d039938c2ef8526e6c55f41c40b1c7`.
- `optechai/mock-api` — reference ingest server, pinned `d8e7b594544fbb2e315b11f34dad49d0ed5dc2b8`.
- `@lorikeetai/react-native-sdk` 3.0.0 — MIT, UI wrapper only.
- Public docs pages, `llms.txt`, `AGENTS.md`, MCP catalog.

This is the **most transparent API surface of the three**, which is why the Lorikeet column has the highest number of source-verified cells.

### 3.2 What is not open

| Missing | Why it matters |
|---|---|
| Workflow/planner engine | Cannot verify how a "concierge" decides actions |
| Guardrail classifier implementation | Cannot verify precision/recall of the 10+10 guardrail claim |
| Retrieval stack | Cannot verify grounding behaviour |
| Tenancy isolation mechanism | Claim only; no test possible without a tenant |
| Telephony routing internals | Provider list is public; behaviour is not |
| Latency figures | None published |

### 3.3 The test that would matter most

A controlled experiment inside an authorised Lorikeet tenant: create two customers, attempt a tool call carrying customer B's identifier while authenticated as customer A, and record whether data or an effect occurs. That single test would either validate or falsify the "server-side identity validation / customer isolation" claim.

**Status: not performed.** It requires (a) a tenant, (b) written permission to test, (c) a scope agreement that this is a functional test, not a penetration test. The mission forbids exploit attempts, and this would sit on the boundary — so it is listed as a *future authorised* test, not something done here.

---

## 4. Cross-vendor gaps

### 4.1 Arabic and dialect evidence — absent everywhere

Searches of all three public sites, docs, and SDKs found **no** published Arabic, Gulf, Levantine, Egyptian, or Arabizi quality data. Decagon claims 70+ languages with auto-detection; Parloa claims 140+ languages and variants; Lorikeet does not state a number on the pages reviewed.

This is not a vendor failure - no evidence was found that any of them targets Arabic-first support publicly. It is an **evidence vacuum**, and it is the single largest strategic opening for Klaint. It also means: **no competitor dialect score exists in this work, and none is asserted in this report.**

### 4.2 Benchmarks

No vendor publishes a reproducible third-party benchmark result with task sets and harness. Decagon published an evaluation *methodology* blog; Parloa publishes Performance Lab *features*; Lorikeet publishes an adversarial challenge and simulation *limits*. None publishes a leaderboard Klaint could enter today without consent.

`τ-bench 2.0` ships six languages — English, Spanish, Portuguese, Hindi, Chinese, Korean — and **no Arabic pack**. Klaint contributing one is both a gap closure and a credibility asset.

### 4.3 Compliance evidence

All three claim certifications (SOC 2, ISO 27001, HIPAA, PCI, GDPR, EU AI Act). None of the underlying reports or certificates was accessible without an NDA. The matrix therefore labels these as **vendor claims**, including Decagon's page typo "ISO 27001:2002" (recorded verbatim, not silently corrected).

### 4.4 Pricing at volume

Only Lorikeet publishes a rate card (verified at `pricing.md:12,32-40,57-62,76,163`). Decagon has none public; Parloa has a model but no numbers. Any three-way TCO table with hard numbers would be fabricated. This report gives Klaint's cost model and Lorikeet's list price, and stops there.

---

## 5. Tooling and provider gaps encountered (not vendor access)

| # | Issue | Effect | Mitigation used |
|---|---|---|---|
| T1 | `websearch` provider returned **HTTP 402** | No general web search | Direct fetches of official URLs; `llms.txt`; sitemaps; GitHub API |
| T2 | GitHub anonymous API **60 req/hr**, search **10 req/min** | Throttled discovery | Targeted org/repo lookups only; clones via git |
| T3 | Some marketing pages are heavy SPA/JS (400 KB+ HTML, little text) | Extraction noise | `extract_text.py` + manual line-level reading of the text output |
| T4 | `docs.decagon.ai` shell extracts to 0 bytes | No docs | Recorded as access gap G1 |
| T5 | Windows/PowerShell quoting broke some `Select-String` patterns | A few retries | Switched to `grep` tool / simpler patterns |

None of these changed a conclusion; they changed how much could be verified.

---

## 6. What was accessible and *was* used

For completeness, so the gaps are not over-read:

- Wispral public repo at `689a4e421d6f8acebedf15df1d2dfca0c905a835` (docs, invariants, KL-T3, KT-01 findings).
- Lorikeet node SDK, mock-api, RN SDK, public docs, `llms.txt`, MCP catalog, pricing page.
- Parloa Python SDK (full generated client + types), public landing docs, product pages, security page, pricing page, integrations page, 2026-11-02 Agent Management blog.
- Decagon Duet CLI distribution (static), product pages (voice, AOP, testing/QA), security page, four engineering/marketing blogs including Missions (2026-11-12).
- Donors: Parlant 4.0.6, Pipecat, τ-bench 2.0, Standard Webhooks, Rasa 3.6.21, Chatwoot 4.20.0 — all cloned and pinned.
- Telephony/model pricing: Twilio US voice, Deepgram streaming, ElevenLabs.

---

## 7. Private repositories — explicit negative result

Connected-account searches (both connected GitHub accounts) for installed repositories matching Lorikeet, Decagon, and Parloa returned **no matching competitor repositories**.

Additional public checks, 2026-11-18:

| Check | Result |
|---|---|
| `github.com/decagonai` | **404** (no such organisation) |
| PyPI `decagon` | **404** |
| PyPI `parloa` | exists, Apache-2.0, 1.0.0 (matches the public SDK) |
| `github.com/parloa` | exists; no Parloa product code (unrelated/forks) |
| `github.com/optechai` | 8 public repos (SDK, mock-api, skills, misc) — no backend |
| npm `@decagon-ai/duet-cli` | public, **proprietary** licence, not open source |

**Conclusion:** there is no evidence that any of the three vendors' backend source is available to this mission. Any future claim of "we reviewed their engine" would be false unless a repository is actually provided.

---

## 8. Minimum access request list (if the mission is extended)

Ordered by how much each item would improve the analysis:

1. **Decagon developer account + docs access** — closes G1/G2; the largest single evidence gap.
2. **Parloa tenant/partner seat** — closes G5/G7; enables observed determinism and trace export.
3. **Lorikeet trial tenant with written test permission** — closes G8; enables the identity-isolation test in §3.3.
4. **Written quotes** at a defined volume from all three — closes G4/G6; makes TCO real.
5. **NDA + trust-center access** for SOC 2/ISO reports — closes G11.
6. **Any private repository**, with a written licence grant naming Klaint — closes G9; without the grant, even access would not permit reuse.
7. **Joint blind Arabic evaluation protocol** — closes G10 in a way that is fair to competitors and publishable.

---

## 9. Honest statement of limitation

This report can tell you, with precise citations, **what each vendor publishes, what their client contracts look like, and what their public code does**. It cannot tell you **how their backends behave**, because none of that was accessible and none of it was obtained.

Every place where that distinction matters is labelled in `COMPETITOR_EVIDENCE_MATRIX.md` as `UNK` or `claim`. No competitor performance score, latency figure, accuracy percentage, or benchmark ranking appears anywhere in this work.
