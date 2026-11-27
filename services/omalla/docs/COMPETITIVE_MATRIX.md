# Competitive matrix

Public positioning as of **2026-11-20**. This is a product comparison, not a
benchmark. No competitor was tested; pricing changes constantly and is
deliberately not reproduced here. Cells marked "public" come from vendor
documentation or the repository licence, not from an independent trial.

## Shape of the market

| Product | Core offer | Telephony | Automation | Self-host / local |
| --- | --- | --- | --- | --- |
| **Vapi** | Voice agent API and dashboard | Twilio, Vonage, SIP trunks (public) | Tools + server webhooks; n8n via webhook | No; cloud-first |
| **Retell AI** | Voice agents, numbers, campaigns | Own + BYO carrier (public) | Tools, webhooks, post-call analysis | No |
| **Bland AI** | Phone agents at scale | Own telephony | Tools, pathways, webhooks | No |
| **Synthflow** | No-code voice agents | Own + BYO | Visual flows, integrations | No |
| **Dograh** | Open-source voice agent platform | Pluggable telephony | Workflows | Yes, BSD-2-Clause |
| **Twilio Studio** | IVR/flow builder | Twilio | Visual flow, Functions | No; Twilio-hosted |
| **n8n** | General automation | None native | Visual workflows, 400+ integrations | Yes, Sustainable Use License |
| **Omalla** | Local-first voice + automation | Simulated default; Twilio/SignalWire; SIP contract | Native engine + n8n + MCP | Yes, Apache-2.0 |

## Capability comparison

| Capability | Vapi | Retell | Bland | Synthflow | Dograh | Omalla |
| --- | --- | --- | --- | --- | --- | --- |
| Inbound calls | yes | yes | yes | yes | yes | simulated verified; carrier unit-tested |
| Outbound calls | yes | yes | yes | yes | yes | simulated verified; carrier unit-tested |
| Bidirectional media | yes | yes | yes | yes | yes | implemented, unit-tested |
| Barge-in | yes | yes | yes | yes | likely | implemented, unit-tested |
| DTMF / IVR | yes | yes | yes | yes | yes | implemented, unit-tested |
| Transfers | yes | yes | yes | yes | yes | implemented, unit-tested |
| SMS | via Twilio | yes | limited | yes | via provider | simulated + Twilio unit-tested |
| Native workflow engine | no (webhooks) | partial | partial | yes | yes | yes |
| n8n integration | webhook | webhook | webhook | integration | possible | signed webhook tool + import/export |
| MCP / agent-driven | API | API | API | API | API | MCP server + REST |
| Local models | no | no | no | no | yes | mock, SAPI, Ollama/OpenAI-compatible |
| Runs with zero paid services | no | no | no | no | possible | yes |
| Open source | no | no | no | no | BSD-2 | Apache-2.0 |
| Self-host | no | no | no | no | yes | yes |
| Arabic | public | public | public | public | unclear | data model yes; local voice **no** |
| Hosted dashboard | yes | yes | yes | yes | yes | local only |

"Public" means the vendor advertises it; it was not verified. "Unclear" means no
public claim was found, not that the capability is absent.

## Where Omalla is weaker

- **No live PSTN qualification.** Every carrier claim is unit-tested against
  injected HTTP, not a real call. Competitors run production traffic.
- **No Arabic speech.** The largest functional gap for the target market.
- **No visual workflow editor.** Templates and JSON, no canvas yet.
- **No campaigns execution.** The data model exists; pacing does not.
- **No hosted offering.** No signup, billing, team management or SLA.
- **Small connector set.** Ten-ish nodes versus hundreds in n8n.
- **Single-process store.** Not a multi-tenant SaaS database.

## Where Omalla is stronger

- **Zero-cost development.** A full call, transcript, tool call and post-call
  workflow with no account and no card.
- **Native automation.** No second product to install, and the same run record
  whether the trigger was a call, a webhook or a human.
- **Licence clarity.** Apache-2.0 with a documented donor register, unlike
  source-available automation tools.
- **Honest availability.** Providers report `available: false` with a reason
  instead of failing at call time.
- **Local inference path.** SAPI works offline on Windows today; Ollama and
  OpenAI-compatible endpoints are adapters, not rewrites.
- **Cost transparency.** Carrier charges are explicit and purchases are off by
  default.

## Positioning

Omalla is not trying to beat Vapi on carrier scale. It is the option for a team
that wants to:

1. build and test a voice agent on one machine with no spend;
2. own the automation layer instead of renting n8n;
3. keep the option to attach Twilio or a SIP trunk later, without a rewrite;
4. read the source and the licence.

The honest one-line claim: **a local voice-agent and automation stack that can
grow into a carrier-backed deployment, with every unverified claim labelled.**

## What would change this matrix

- A live Twilio qualification run (moves carrier rows from unit-tested to
  verified).
- An Arabic STT/TTS model (closes the biggest product gap).
- A visual editor and campaign runner (matches Synthflow's no-code surface).
- A hosted multi-tenant mode (enters Vapi's market, with a much larger security
  burden).
