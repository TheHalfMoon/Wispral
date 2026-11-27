/**
 * Self-hosted SIP gateway contract.
 *
 * Omalla already speaks one wire protocol for carrier calls: an HTTP webhook
 * that returns call instructions, plus a JSON WebSocket that carries base64
 * mu-law frames. A SIP gateway's only job is to translate SIP/RTP into that
 * protocol. This module describes exactly what a gateway must send, so an
 * Asterisk dialplan, a FreeSWITCH dialplan, LiveKit SIP or Jambonz can be
 * wired without touching Omalla's call logic.
 *
 * Nothing here claims a gateway has been run. `verification` is always
 * "not-run" until a real call is placed through the compose templates.
 */

export const SIP_ENGINES = ["asterisk", "freeswitch", "livekit", "jambonz"] as const;

export type SipEngine = (typeof SIP_ENGINES)[number];

export interface SipGatewayDescriptor {
  id: SipEngine;
  label: string;
  /** The licence of the engine itself, not of this contract. */
  licence: string;
  /** Image the bundled compose file uses. Pinned tags live in deploy/sip. */
  containerImage: string;
  /** SIP signalling ports the container exposes. */
  sipPorts: number[];
  /** Where the engine's routing rules live. */
  dialplan: string;
  verification: "not-run";
  notes: string[];
}

export interface SipGatewayContractOptions {
  engine: SipEngine;
  /** Public origin Omalla is reachable at, e.g. https://omalla.example.com. */
  publicBaseUrl: string;
  /**
   * Shared secret the gateway sends as `x-omalla-gateway-token`. SIP engines
   * cannot produce a Twilio signature, so the token is the whole authentication
   * story. It must be long, random and rotated with the gateway config.
   */
  token: string;
  /** SIP host callers dial. Defaults to the hostname of `publicBaseUrl`. */
  sipHost?: string;
  sipPort?: number;
}

export interface SipGatewayContract {
  engine: SipEngine;
  provider: "sip";
  voiceWebhookUrl: string;
  dtmfWebhookUrl: string;
  statusWebhookUrl: string;
  mediaWebSocketUrl: string;
  auth: {
    header: "x-omalla-gateway-token";
    /** Echoed so an operator can compare it with the gateway config. */
    token: string;
  };
  media: {
    encoding: "audio/x-mulaw";
    sampleRate: 8000;
    channels: 1;
    frameMs: 20;
    direction: "bidirectional";
    /** One JSON object per WebSocket text frame. */
    wireFormat: "json";
  };
  sip: {
    host: string;
    port: number;
    inboundUri: string;
    outboundUriTemplate: string;
  };
  /** Things the gateway must do that Omalla cannot enforce from its side. */
  requirements: string[];
}

const MEDIA = {
  encoding: "audio/x-mulaw",
  sampleRate: 8000,
  channels: 1,
  frameMs: 20,
  direction: "bidirectional",
  wireFormat: "json",
} as const;

/**
 * Builds the URLs and SIP URIs a gateway config needs.
 *
 * The base URL is validated rather than trusted: a relative value would make
 * every webhook fail at call time, and `http`/`ws` silently downgrades carrier
 * audio, so both are called out in `requirements`.
 */
export function buildSipGatewayContract(options: SipGatewayContractOptions): SipGatewayContract {
  let base: URL;
  try {
    base = new URL(options.publicBaseUrl);
  } catch {
    throw new Error("publicBaseUrl must be an absolute http(s) URL");
  }
  if (base.protocol !== "https:" && base.protocol !== "http:") {
    throw new Error("publicBaseUrl must be an absolute http(s) URL");
  }
  const token = options.token.trim();
  if (token.length < 16) {
    throw new Error("gateway token must be at least 16 characters");
  }

  const root = base.origin + base.pathname.replace(/\/+$/, "");
  const wsRoot = root.replace(/^http/, "ws");
  const sipHost = options.sipHost?.trim() || base.hostname;
  const sipPort = options.sipPort ?? 5060;

  const requirements: string[] = [];
  if (base.protocol === "http:") {
    requirements.push(
      "publicBaseUrl is http; production carrier audio must be https/wss, and this is only acceptable on localhost",
    );
  }
  requirements.push(
    "gateway must POST form-encoded call events and send x-omalla-gateway-token on every request",
    "gateway must open the media WebSocket and stream 20 ms base64 mu-law frames at 8 kHz mono",
    "gateway must forward RFC 4733 DTMF as digits, and must not invent digits",
    "recording consent is the operator's duty; the gateway only records when asked",
  );

  return {
    engine: options.engine,
    provider: "sip",
    voiceWebhookUrl: `${root}/telephony/sip/voice`,
    dtmfWebhookUrl: `${root}/telephony/sip/dtmf`,
    statusWebhookUrl: `${root}/telephony/sip/status`,
    mediaWebSocketUrl: `${wsRoot}/telephony/sip/media`,
    auth: { header: "x-omalla-gateway-token", token },
    media: { ...MEDIA },
    sip: {
      host: sipHost,
      port: sipPort,
      inboundUri: `sip:inbound@${sipHost}:${sipPort}`,
      outboundUriTemplate: `sip:{number}@${sipHost}:${sipPort}`,
    },
    requirements,
  };
}

/** Static facts about each engine, used by docs and the dashboard. */
export function sipGatewayDescriptors(): SipGatewayDescriptor[] {
  return [
    {
      id: "asterisk",
      label: "Asterisk",
      licence: "GPL-2.0-or-later",
      containerImage: "andrius/asterisk:20",
      sipPorts: [5060, 5061],
      dialplan: "extensions.conf",
      verification: "not-run",
      notes: [
        "Mature B2BUA with the widest SIP interoperability.",
        "Needs a dialplan context that answers, POSTs to the voice webhook and bridges audio to the media socket.",
        "GPL applies to the engine, not to Omalla's separate process.",
      ],
    },
    {
      id: "freeswitch",
      label: "FreeSWITCH",
      licence: "MPL-1.1",
      containerImage: "safarov/freeswitch:1.10",
      sipPorts: [5060, 5080],
      dialplan: "dialplan/default.xml",
      verification: "not-run",
      notes: [
        "Event Socket and mod_curl make webhook-driven dialplans practical.",
        "The bundled compose file is a starting point, not a hardened switch.",
      ],
    },
    {
      id: "livekit",
      label: "LiveKit SIP",
      licence: "Apache-2.0",
      containerImage: "livekit/sip:latest",
      sipPorts: [5060],
      dialplan: "livekit sip inbound trunk + dispatch rule",
      verification: "not-run",
      notes: [
        "SIP is terminated by the LiveKit SIP service and audio arrives over WebRTC.",
        "Requires a LiveKit server and API key; the Omalla bridge would consume the room, not raw RTP.",
        "The media frame contract in this module does not apply until a LiveKit room adapter exists.",
      ],
    },
    {
      id: "jambonz",
      label: "Jambonz",
      licence: "MIT",
      containerImage: "jambonz/jambonz-api-server:latest",
      sipPorts: [5060],
      dialplan: "jambonz application webhook",
      verification: "not-run",
      notes: [
        "Webhook-first design is the closest match to Omalla's call contract.",
        "A full deployment needs its own MySQL, Redis, drachtio and rtpengine stack.",
      ],
    },
  ];
}
