# Source inventory

Donors examined for Omalla. Licence metadata and revisions were read from the
GitHub API and each repository's licence file on **2026-11-20**. Revisions are
the default-branch head at that time, recorded so a later reader can tell what
was actually looked at.

**No donor source code has been copied into this repository.** Omalla's code is
original TypeScript. The donors below are references, protocol specifications or
optional external systems. Where a licence would make copying unsafe, the row
says so explicitly.

## Voice and telephony

| Donor | Repository | Licence | Revision examined | Use in Omalla |
| --- | --- | --- | --- | --- |
| Dograh | `dograh-hq/dograh` | BSD-2-Clause | `b5e30bd65d75ce6487ca40f5af60a284fe585146` | Reference for self-hosted voice-agent shape and telephony abstraction |
| Pipecat | `pipecat-ai/pipecat` | BSD-2-Clause | `77bb17660805a7fb1db5f02307044255d49340a6` | Reference for frame pipeline, interruption and turn handling |
| LiveKit | `livekit/livekit` | Apache-2.0 | `c10a54095ceaf9b963f65512373031b259e62cb3` | Reference for room/SIP separation; SIP compose skeleton |
| Vocode | `vocodedev/vocode-core` | MIT | `e054c33a72787b6a4920f91eb8598ad0bafb4240` | Reference for provider-agnostic conversation contract |
| TEN Framework | `TEN-framework/ten-framework` | Apache-2.0 **with additional conditions** | `238da29e3bbf6b2ad233034bcee84838e78789d4` | Reference only; additional conditions restrict competing hosted deployment |
| Jambonz | `jambonz/jambonz-api-server` | MIT | `92aef10b92a3640c0bf84d13013047203a528203` | Reference for webhook-first call control; SIP compose skeleton |
| Asterisk | `asterisk/asterisk` | GPL-2.0 | `8481b8e7aec24862f93db60bd5eb0cebc3c7f254` | External gateway option; compose skeleton only |
| FreeSWITCH | `signalwire/freeswitch` | MPL-1.1 | `eb8645be7d416a8350b0175c6d91d6dac55626ec` | External gateway option; compose skeleton only |
| Twilio Node SDK | `twilio/twilio-node` | MIT | `676777e0f190980b307c507ee378004923980d63` | Signature algorithm cross-check only; not vendored |
| Twilio APIs | proprietary service | Commercial terms | docs, 2026-11-20 | Protocol reference: TwiML, Media Streams, REST, signatures |

## Speech and models

| Donor | Repository | Licence | Revision examined | Use in Omalla |
| --- | --- | --- | --- | --- |
| Whisper | `openai/whisper` | MIT | `86098128c0b4f24f0e2aa2994de830614b474227` | Candidate local STT; not bundled, no weights downloaded |
| Silero VAD | `snakers4/silero-vad` | MIT | `066409f3d9db45a30d21dfcbf9147826ffdd7052` | Algorithm reference; Omalla ships an energy VAD, no model |
| Piper | `OHF-Voice/piper1-gpl` | GPL-3.0 | `39ac0a04ff01120b1cb7867d21723fa320305b03` | Not linked; GPL would constrain distribution. Optional external TTS at most |
| Kokoro | `hexgrad/kokoro` | Apache-2.0 | `dfb907a02bba8152ca444717ca5d78747ccb4bec` | Candidate external TTS; not bundled |
| Moshi | `kyutai-labs/moshi` | Apache-2.0 | `e6a55d2722a65870ef52a6c9f6ecfc0e90f38362` | Candidate full-duplex speech model; not bundled |

Model **weights** carry their own terms, separate from repository code. Omalla
downloads nothing by default and therefore inherits no weight licence.

## Automation and data

| Donor | Repository | Licence | Revision examined | Use in Omalla |
| --- | --- | --- | --- | --- |
| n8n | `n8n-io/n8n` | Sustainable Use License (source-available) | `94c61b2c36cfaa12a1adfa1f3e6ef2b16dc36136` | HTTP integration only; no code copied or bundled |
| Activepieces | `activepieces/activepieces` | MIT outside `packages/ee/`; enterprise dirs separate | `ca93da9cd7a3b93250a8c9858b74d0d96832d90f` | Reference for connector palette |
| Node-RED | `node-red/node-red` | Apache-2.0 | `f613ba109eff360a1c8f8cb9add7b39531c75f12` | Reference for flow UX |
| Windmill | `windmill-labs/windmill` | AGPL-3.0 plus proprietary enterprise snippets | `66262f364a5e299a2fa917098e7589278bc4cf8f` | Reference only; not embedded |
| Baserow | `baserow/baserow` | MIT client code; `premium/` and `enterprise/` separate | `6508fbbc32e108f71ea1e550a18cdb736a6f2ce9` | Optional external database; no schema copied |
| Twenty | `twentyhq/twenty` | Mostly AGPL-3.0; `/* @license Enterprise */` files commercial; some MIT packages | `63733f37e71a15b56aba8b91f415999e5201911c` | Optional external CRM; no code copied |

## Licence conclusions

| Decision | Reason |
| --- | --- |
| Do not embed n8n | Sustainable Use License is not compatible with an Apache-2.0 binary; HTTP keeps the boundary clean |
| Do not link Piper GPL code | GPL-3.0 would impose distribution obligations on the whole binary; external process only, and not shipped |
| Do not embed Windmill or Twenty | AGPL-3.0 plus commercial carve-outs; external systems only |
| Do not copy TEN | Apache-2.0 with additional conditions that restrict competing deployments |
| Use Twilio docs, not Twilio code | The service is proprietary; the signature algorithm is documented and independently reproducible |
| Keep Asterisk/FreeSWITCH external | GPL-2.0 / MPL-1.1 engines run as separate containers, never linked |

## Reproducing this inventory

```bash
curl -s https://api.github.com/repos/<owner>/<repo> | jq '{license: .license.spdx_id, pushed_at}'
curl -s https://api.github.com/repos/<owner>/<repo>/commits?per_page=1 | jq '.[0].sha'
curl -s https://raw.githubusercontent.com/<owner>/<repo>/<sha>/LICENSE
```

The revisions above are snapshots. A donor's current head may have moved; the
row records what was examined, not a dependency to track.

## Sources that are not code

- Vapi documentation and `llms.txt` (public docs, no source).
- Twilio Programmable Voice, Media Streams, SIP and security documentation.
- n8n webhook and Respond to Webhook documentation.
- The reference video `https://youtu.be/HGBMr1RQliY` (public demonstration).

No private repository, leaked dump, credential or customer record was accessed.
Requests to obtain Vapi's source or secrets were declined.
