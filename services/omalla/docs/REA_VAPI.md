# REA: Vapi

Reverse Engineering and **Architecture** Analysis, from public artifacts only.

## Scope and refusal

Vapi's backend is closed source. No Vapi source code, customer data or
credentials were obtained, and requests to extract them were declined. This
document records what public documentation, the public website, the public
GitHub organisation and the referenced video actually show, separates that from
inference, and maps the result to Omalla.

The reference video is Ed Hill's `https://youtu.be/HGBMr1RQliY`. It demonstrates
a voice agent built from **Vapi + Twilio + n8n**: Vapi handles the conversation,
Twilio supplies the phone number, and n8n receives a tool call and returns JSON.
Trello is not part of that architecture. Earlier planning that treated Trello as
core was wrong and has been corrected.

## What public artifacts show

| Artifact | Observation | Confidence |
| --- | --- | --- |
| Vapi docs (`docs.vapi.ai`, `llms.txt`) | Assistants are the unit of configuration: model, voice, transcriber, first message, tools, server URL | documented |
| Vapi docs | Phone numbers are provisioned through providers such as Twilio, Vonage and SIP trunks | documented |
| Vapi docs | Tools include function calls, transfers, end-call, DTMF and "server" webhooks | documented |
| Vapi docs | Server URLs receive call lifecycle events (`assistant-request`, `end-of-call-report`, status updates) | documented |
| Vapi docs | Squads/workflows compose multiple assistants into a call | documented |
| Vapi GitHub org | SDKs, examples and starter apps are public; the core server is not | observed |
| The video | A Vapi assistant calls an n8n production webhook as a tool; n8n replies with JSON that becomes speech | observed |
| The video | A Twilio number is attached to the assistant for inbound calls | observed |

## Inferred architecture

```
caller ──PSTN──► Twilio number
                    │ HTTP webhook (TwiML / answer)
                    ▼
                Vapi control plane
                    │  assistant config, tools, server URL
                    ▼
        media session (STT → LLM → TTS, barge-in)
                    │ tool call
                    ▼
             n8n production webhook
                    │ JSON
                    ▼
        Vapi speaks the returned text
                    │
                    ▼
        end-of-call report → customer server
```

Inference, not fact:

- Vapi almost certainly terminates carrier media itself and normalises multiple
  carriers behind one session model. The public API shape (assistant + phone
  number + server URL) implies that indirection.
- Tool results are turned into speech by the assistant, not by n8n. The video
  shows n8n returning structured text and Vapi speaking it.
- Barge-in, endpointing and turn-taking are platform features; the public docs
  describe them but not their implementation.

What cannot be known from public artifacts: internal media server, model routing,
queueing, pricing logic, failover behaviour, exact webhook retry policy, and any
proprietary model. Omalla does not claim to reproduce those internals.

## Behavioural contract Omalla reproduces

| Vapi behaviour | Omalla implementation | State |
| --- | --- | --- |
| Assistant with model, voice, prompt, first message | `Agent` + `AgentVersion` | done |
| Attach a phone number to an assistant | `PhoneNumber.inboundAgentId`, IVR menus | done |
| Inbound call answered with instructions | TwiML / simulator response | unit-tested |
| Bidirectional media | Media Streams WebSocket + `MediaBridge` | unit-tested |
| Tool call mid-call | `ToolDefinition` + `ToolRuntime` | unit-tested |
| Server webhook tool returning JSON | `function` / `api_request` / `n8n_workflow` tools | unit-tested |
| End-of-call report | `call_ended` workflow with transcript and extracted data | verified |
| Transfer to human | `transfer` tool + TwiML dial | unit-tested |
| DTMF / IVR | gather + `/telephony/:provider/dtmf` | unit-tested |
| Squads / multi-agent | not implemented | gap |
| Hosted dashboard and billing | local dashboard only | deliberate difference |

## Where Omalla differs

1. **Simulation is first-class.** A call can be placed with no carrier, no
   number and no cost, through the same conversation path.
2. **Automation is native.** Vapi delegates automation to n8n or a customer
   server. Omalla ships a deterministic workflow engine and exposes it as a
   live-call tool, so n8n is optional.
3. **Local inference is a supported mode.** Mock and SAPI providers work with no
   network. Vapi is cloud-first.
4. **Availability is explicit.** Omalla reports `verification: "live-tested"`
   only after a real carrier call. Vapi's marketing does not need that
   distinction; a local build does.
5. **No hosted multi-tenant service.** Omalla stores one tenant's data on one
   machine by default.

## Lessons taken

- The assistant/server-URL split is the right seam: configuration is data, the
  media session is runtime.
- Tool calls must carry server-resolved context. A model must never choose the
  tenant, the caller id or the destination.
- The n8n bridge works because it is plain HTTP with a JSON response. Omalla
  keeps that contract and adds a signature and an SSRF check.
- The video's Trello step is an example integration, not architecture. Omalla's
  templates default to local stores and treat Trello as optional.

## Open questions

- Exact Vapi webhook retry and signature scheme (public docs describe endpoints,
  not a complete signing specification).
- How Vapi handles carrier failover mid-call.
- Whether squads share one media session or bridge between sessions.

These remain unknowns. No attempt was made to obtain non-public answers.
