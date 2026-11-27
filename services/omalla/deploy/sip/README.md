# Self-hosted SIP gateways

These compose files are **skeletons and have not been run**. Docker was not
running when this build was produced, so nothing in this directory is verified.
They exist so the SIP path is concrete rather than a promise.

Omalla's side of the contract is implemented and unit-tested:

- `POST /telephony/sip/voice` - form-encoded call event, returns call instructions
- `POST /telephony/sip/dtmf` - DTMF digits
- `POST /telephony/sip/status` - call status
- `WS /telephony/sip/media` - bidirectional base64 mu-law audio

Every request must carry `x-omalla-gateway-token`. Generate a contract with:

```
omalla sip contract --engine asterisk --public-url https://your-host.example
```

## What is missing

The `sip` telephony provider is not registered in v0.1.0. The contract module
(`packages/telephony/src/sip.ts`) describes the wire format, but no adapter
translates SIP engine events into `TelephonyProvider` calls yet. Running a
container below therefore does not produce a working call.

## Engines

| Engine | Licence | Compose profile | State |
| --- | --- | --- | --- |
| Asterisk | GPL-2.0-or-later | `asterisk` | not run |
| FreeSWITCH | MPL-1.1 | `freeswitch` | not run |
| LiveKit SIP | Apache-2.0 | `livekit` | not run |
| Jambonz | MIT | `jambonz` | not run |

## Usage

```bash
export OMALLA_PUBLIC_URL=https://your-host.example
export OMALLA_GATEWAY_TOKEN="$(openssl rand -hex 32)"
docker compose --profile asterisk up
```

Then add a dialplan that answers the call, POSTs the caller and callee to the
voice webhook, and bridges RTP to the media WebSocket. Asterisk cannot open a
WebSocket from a dialplan by itself; that needs ARI, an AGI script or an
external media server. FreeSWITCH needs `mod_audio_stream` or equivalent.
Jambonz is the closest fit because its applications are webhooks already.

Do not expose these containers to the public internet without a firewall,
TLS termination and a real SIP password. Default configs in public images are
not safe defaults.
