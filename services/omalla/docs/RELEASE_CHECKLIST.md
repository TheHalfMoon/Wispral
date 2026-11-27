# Release checklist: v0.1.0

A local development release. Nothing is published, deployed or sold as part of
this checklist. Publishing requires explicit owner authorization and a separate
review.

## Gates

| Gate | Requirement | State |
| --- | --- | --- |
| G1 Build | `npm run build` succeeds from a clean install | PASS |
| G2 Types | `npm run typecheck` has no errors | PASS |
| G3 Tests | `npm test`, `npm run test:python` and the smoke runs are green | PASS (64 TS, 12 Python, 33 + 20 smoke) |
| G4 Docs | All required documents exist and match the code | PASS |
| G5 Honesty | No doc or UI claims a live PSTN call | PASS |
| G6 Security | Known gaps listed in `SECURITY_MODEL.md` | PASS |
| G7 Licence | Donor register with SPDX and revisions | PASS |
| G8 Git | Repository initialised, `.gitignore` excludes data and secrets | PASS |
| G9 Dashboard | Served over HTTP and opened in a browser | HTTP PASS; browser **NOT RUN** |
| G10 Carrier | Live Twilio call, SMS and number lifecycle | **NOT RUN** |

G1-G8 are required for the RC tag. G9 is half met: the dashboard is served and
smoke-tested over HTTP but has not been opened in a browser. Its browser pass and
G10 are required before calling the build "carrier ready", not before the local
RC.

## Verified for this RC

- Simulated inbound and outbound calls with transcript and metrics.
- Workflow engine: retries, idempotency, dry-run, SSRF guard.
- Eleven templates install and run locally.
- n8n live tool signs and validates its payload; failure is retryable.
- Native workflow runs from a live call without n8n.
- Twilio signature, TwiML, Media Streams parsing, REST calls, numbers, SMS.
- Number purchase is gated by config, role and `confirm: true`.
- SMS requires consent and is labelled simulated when it is.
- Credentials are encrypted; logs redact secrets and phone numbers.
- API keys are hashed and compared in constant time.
- Dashboard syntax, API shapes and a 33-check HTTP smoke run (`npm run smoke`).
- Python SDK: 12 unit tests and a 20-check live smoke (`npm run test:python`, `npm run smoke:python`).
- OpenAPI 3.1 document served at `/openapi.json` and drift-tested against the Fastify route table.
- Server boot: one loopback listener, health over real HTTP.

## Explicitly not verified

| Item | Reason |
| --- | --- |
| Real Twilio/SignalWire call | No credentials, no number |
| Real SMS delivery | Same |
| Number purchase/release at a carrier | Same, and spend is not authorised |
| Telnyx/Vonage | Adapters do not exist |
| Asterisk/FreeSWITCH/LiveKit/Jambonz | Docker daemon not running |
| SIP gateway end-to-end | No adapter, no gateway run |
| Arabic speech | No local model |
| Dashboard rendered in a browser | HTTP smoke passed; no browser automation in this session |
| Multi-user concurrency | No load test |
| Hosted deployment | Out of scope |

## Pre-commit checks

```bash
npm run verify
npm run test:python
npm run smoke
npm run smoke:python
npm audit --omit=dev
git status --short
git diff --check
```

Expected: 64 TypeScript tests and 12 Python tests pass, no whitespace errors,
no `.omalla/` data, no `*.key`, no `api-key.txt`, no recordings.

## Repository hygiene

`.gitignore` must exclude:

```
node_modules/
dist/
.omalla/
*.log
.env
.env.*
api-key.txt
recordings/
```

Before committing, confirm no credential, API key, phone number or transcript is
staged. `git diff --cached | Select-String "omk_|sk-|TWILIO_AUTH_TOKEN="` should
return nothing.

## Tagging

```bash
git init
git add .
git commit -m "feat: local-first voice AI and automation platform"
git tag -a v0.1.0-rc.1 -m "v0.1.0-rc.1 local release candidate"
```

Do **not** push, publish to npm, create a GitHub release, or deploy without the
owner's explicit instruction.

## Carrier qualification (separate authorization)

Before any live run:

1. Owner confirms a spend cap and a test number.
2. Set `OMALLA_ALLOW_CARRIER_PURCHASES=1` only for the purchase window.
3. Use a dedicated Twilio project, not production.
4. Place one inbound and one outbound call; record duration and cost.
5. Send one SMS; confirm delivery receipt.
6. Release the number; confirm the carrier's release fee, if any.
7. Record every result in `IMPLEMENTATION_LEDGER.md` and flip the matrix rows
   from `NOT RUN` to `VERIFIED`.
8. Turn `OMALLA_ALLOW_CARRIER_PURCHASES` back off.

Until then, the honest status remains: carrier adapters are unit-tested, not
live-tested.

## Rollback

The store is a JSON directory. Back up `.omalla/` before an upgrade; restoring it
is the rollback. There are no migrations in v0.1.0. A schema change must ship
with a migration or a documented manual step.
