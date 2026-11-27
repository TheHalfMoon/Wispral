import { timingSafeEqual } from "node:crypto";
import { OmallaError } from "@omalla/core";
import type {
  CallStatusEvent,
  CreateCallRequest,
  DtmfEvent,
  InboundCallEvent,
  InboundResponseOptions,
  MediaStreamEvent,
  ProviderCall,
  ProviderDescription,
  ProviderHttpResponse,
  TelephonyCapabilities,
  TelephonyProvider,
  WebhookRequest,
  WebhookVerification,
} from "../provider.js";
import { normalizeCallStatus } from "../provider.js";
import { isLoopbackIp } from "../sip-stack.js";

export interface SipTelephonyProviderOptions {
  gatewayUrl: string;
  gatewayToken?: string;
  attestedEncryptedTunnel?: boolean;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

const SIP_CAPABILITIES: TelephonyCapabilities = {
  voice: true,
  mediaStream: "bidirectional",
  sms: false,
  dtmf: true,
  transfer: true,
  recording: false,
  numberProvisioning: false,
  signedWebhooks: true,
  sip: true,
};

/**
 * Self-hosted SIP gateway / native SIP stack provider (`id: "sip"`).
 *
 * Enforces `OM-T7`: `x-omalla-gateway-token` is verified in constant time, and
 * non-loopback HTTP cleartext delivery of `x-omalla-gateway-token` is refused
 * unless `attestedEncryptedTunnel` is explicitly configured.
 */
export class SipTelephonyProvider implements TelephonyProvider {
  readonly id = "sip" as const;
  readonly label = "Self-hosted SIP gateway (RFC 3261 / Asterisk / FreeSWITCH / LiveKit / Jambonz)";
  readonly capabilities = SIP_CAPABILITIES;
  readonly description: ProviderDescription;

  private readonly gatewayUrl: string;
  private readonly gatewayToken: string | null;
  private readonly attestedEncryptedTunnel: boolean;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;

  constructor(options: SipTelephonyProviderOptions) {
    if (!options.gatewayUrl.trim()) {
      throw new OmallaError("validation", "OMALLA_SIP_GATEWAY_URL is empty", 400);
    }
    this.gatewayUrl = options.gatewayUrl.trim().replace(/\/+$/, "");
    this.gatewayToken = options.gatewayToken?.trim() || null;
    this.attestedEncryptedTunnel = options.attestedEncryptedTunnel === true;
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.timeoutMs = options.timeoutMs ?? 15_000;

    this.description = {
      id: "sip",
      label: this.label,
      capabilities: SIP_CAPABILITIES,
      pstn: true,
      verification: "unit-tested",
      notes: [
        "Speaks RFC 3261 SIP + SRTP AES_CM_128_HMAC_SHA1_80 + RFC 4733 DTMF via SipStack or an external B2BUA.",
        "Enforces OM-T7: loopback bind by default, SRTP on non-loopback media, and TLS/attested-tunnel requirement for x-omalla-gateway-token.",
      ],
    };
  }

  verifyWebhook(request: WebhookRequest): WebhookVerification {
    if (!this.gatewayToken) {
      return { valid: false, reason: "OMALLA_SIP_GATEWAY_TOKEN is not configured" };
    }
    const presented = request.headers["x-omalla-gateway-token"] ?? "";
    if (!presented) {
      return { valid: false, reason: "missing x-omalla-gateway-token header" };
    }

    // OM-T7 check on HTTP webhook surface: refuse cleartext non-loopback gateway token (never trust X-Forwarded-Proto)
    try {
      const parsed = new URL(request.url);
      const isHttps = parsed.protocol === "https:";
      const hostLoopback = isLoopbackIp(parsed.hostname);
      if (!hostLoopback && !isHttps && !this.attestedEncryptedTunnel) {
        return {
          valid: false,
          reason: "OM-T7: non-loopback x-omalla-gateway-token requires HTTPS/TLS or attested encrypted tunnel",
        };
      }
    } catch {
      return { valid: false, reason: "invalid SIP webhook URL" };
    }

    const exp = Buffer.from(this.gatewayToken, "utf8");
    const got = Buffer.from(presented, "utf8");
    if (exp.length !== got.length || !timingSafeEqual(exp, got)) {
      return { valid: false, reason: "x-omalla-gateway-token mismatch" };
    }
    return { valid: true };
  }

  parseInbound(request: WebhookRequest): InboundCallEvent {
    const src = { ...request.form, ...(request.json ?? {}) };
    const providerCallId = String(src.CallSid ?? src.callId ?? src["call-id"] ?? "");
    if (!providerCallId) {
      throw new OmallaError("validation", "SIP webhook missing CallSid / callId", 400);
    }
    return {
      providerCallId,
      from: String(src.From ?? src.from ?? ""),
      to: String(src.To ?? src.to ?? ""),
      direction: String(src.Direction ?? src.direction ?? "inbound") === "outbound" ? "outbound" : "inbound",
      status: "ringing",
    };
  }

  parseStatus(request: WebhookRequest): CallStatusEvent {
    const src = { ...request.form, ...(request.json ?? {}) };
    const providerCallId = String(src.CallSid ?? src.callId ?? "");
    if (!providerCallId) {
      throw new OmallaError("validation", "SIP status webhook missing CallSid / callId", 400);
    }
    return {
      providerCallId,
      status: normalizeCallStatus(String(src.CallStatus ?? src.status ?? "in-progress")),
      ...(src.CallDuration !== undefined ? { durationSec: Number(src.CallDuration) || 0 } : {}),
    };
  }

  parseDtmf(request: WebhookRequest): DtmfEvent {
    const src = { ...request.form, ...(request.json ?? {}) };
    const providerCallId = String(src.CallSid ?? src.callId ?? "");
    const digits = String(src.Digits ?? src.digits ?? "");
    if (!providerCallId || !digits) {
      throw new OmallaError("validation", "SIP DTMF webhook missing callId or digits", 400);
    }
    return { providerCallId, digits };
  }

  renderInboundResponse(options: InboundResponseOptions): ProviderHttpResponse {
    return {
      status: 200,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify({
        say: options.say,
        mediaStreamUrl: options.mediaStreamUrl,
        parameters: options.parameters ?? {},
        gather: options.gather,
        dial: options.dial,
        hangup: Boolean(options.hangup),
        closingSay: options.closingSay,
      }),
    };
  }

  renderHangupResponse(text?: string): ProviderHttpResponse {
    return {
      status: 200,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify({ ...(text ? { say: text } : {}), hangup: true }),
    };
  }

  parseMediaMessage(raw: string): MediaStreamEvent {
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return { type: "unknown", raw };
    }
    if (!parsed || typeof parsed !== "object") return { type: "unknown", raw };
    const msg = parsed as Record<string, unknown>;
    if (msg.event === "connected") return { type: "connected" };
    if (msg.event === "stop") return { type: "stop" };
    if (msg.event === "dtmf") {
      const dtmf = (msg.dtmf ?? {}) as Record<string, unknown>;
      return { type: "dtmf", digit: String(dtmf.digit ?? msg.digit ?? "") };
    }
    if (msg.event === "start") {
      const start = (msg.start ?? msg) as Record<string, unknown>;
      return {
        type: "start",
        streamId: String(start.streamSid ?? start.streamId ?? "sip_stream"),
        callId: String(start.callSid ?? start.callId ?? ""),
        format: { encoding: "audio/x-mulaw", sampleRate: 8000, channels: 1 },
        parameters: {},
      };
    }
    if (msg.event === "media") {
      const media = (msg.media ?? {}) as Record<string, unknown>;
      return {
        type: "media",
        track: media.track === "outbound" ? "outbound" : "inbound",
        payload: String(media.payload ?? ""),
      };
    }
    return { type: "unknown", raw };
  }

  encodeMediaFrame(streamId: string, payloadBase64: string): string {
    return JSON.stringify({ event: "media", streamSid: streamId, media: { payload: payloadBase64 } });
  }

  encodeClearFrame(streamId: string): string {
    return JSON.stringify({ event: "clear", streamSid: streamId });
  }

  encodeMarkFrame(streamId: string, name: string): string {
    return JSON.stringify({ event: "mark", streamSid: streamId, mark: { name } });
  }

  async createCall(request: CreateCallRequest): Promise<ProviderCall> {
    const res = await this.gatewayRequest("POST", "/calls", {
      to: request.to,
      from: request.from,
      answerUrl: request.answerUrl,
      ...(request.statusCallbackUrl ? { statusCallbackUrl: request.statusCallbackUrl } : {}),
    });
    return {
      providerCallId: String(res.callId ?? res.providerCallId ?? ""),
      status: normalizeCallStatus(String(res.status ?? "initiated")),
    };
  }

  async hangupCall(providerCallId: string): Promise<void> {
    await this.gatewayRequest("POST", `/calls/${encodeURIComponent(providerCallId)}/hangup`, {});
  }

  async redirectCall(providerCallId: string, destination: string): Promise<void> {
    await this.gatewayRequest("POST", `/calls/${encodeURIComponent(providerCallId)}/refer`, {
      referTo: destination,
    });
  }

  private async gatewayRequest(
    method: "POST",
    path: string,
    body: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    const headers: Record<string, string> = {
      "content-type": "application/json",
      accept: "application/json",
    };
    if (this.gatewayToken) {
      let gwParsed: URL;
      try {
        gwParsed = new URL(this.gatewayUrl);
      } catch {
        throw new OmallaError("validation", "invalid OMALLA_SIP_GATEWAY_URL", 400);
      }
      const gwHttps = gwParsed.protocol === "https:";
      const gwLoopback = isLoopbackIp(gwParsed.hostname);
      if (!gwLoopback && !gwHttps && !this.attestedEncryptedTunnel) {
        throw new OmallaError(
          "blocked_by_policy",
          "OM-T7: refusing to send x-omalla-gateway-token over cleartext non-loopback HTTP",
          403,
        );
      }
      headers["x-omalla-gateway-token"] = this.gatewayToken;
    }
    let response: Response;
    try {
      response = await this.fetchImpl(`${this.gatewayUrl}${path}`, {
        method,
        headers,
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(this.timeoutMs),
      });
    } catch (error) {
      throw new OmallaError("provider_error", `SIP gateway request failed: ${(error as Error).message}`, 502);
    }
    if (response.status === 204) return {};
    const text = await response.text();
    const parsed = text ? (JSON.parse(text) as Record<string, unknown>) : {};
    if (!response.ok) {
      throw new OmallaError("provider_error", `HTTP ${response.status} from SIP gateway`, 502);
    }
    return parsed;
  }
}
