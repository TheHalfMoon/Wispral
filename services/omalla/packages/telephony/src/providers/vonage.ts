import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";
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
  ProviderSms,
  RecordingEvent,
  SendSmsRequest,
  SmsEvent,
  TelephonyCapabilities,
  TelephonyProvider,
  WebhookRequest,
  WebhookVerification,
} from "../provider.js";
import { normalizeCallStatus } from "../provider.js";

export interface VonageProviderOptions {
  apiKey: string;
  apiSecret: string;
  applicationId: string;
  /** Vonage webhook signing secret (defaults to `apiSecret` for HS256 Bearer JWT verification). */
  signatureSecret?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
  toleranceSec?: number;
  nowSec?: () => number;
}

const VONAGE_CAPABILITIES: TelephonyCapabilities = {
  voice: true,
  mediaStream: "bidirectional",
  sms: true,
  dtmf: true,
  transfer: true,
  recording: true,
  numberProvisioning: false,
  signedWebhooks: true,
  sip: true,
};

/**
 * Vonage Voice API (NCCO + WebSocket Media) + Messages v1 adapter.
 *
 * Verifies Vonage signed Bearer JWT webhooks (`HS256` signature + `iat`/`exp`
 * ±300 s window + raw-byte `payload_hash` SHA-256 verification), renders NCCO
 * JSON call control arrays, and executes live call transfers (`PUT /v1/calls/{uuid}`).
 */
export class VonageProvider implements TelephonyProvider {
  readonly id = "vonage" as const;
  readonly label = "Vonage Voice API";
  readonly capabilities = VONAGE_CAPABILITIES;
  readonly description: ProviderDescription;

  private readonly apiKey: string;
  private readonly apiSecret: string;
  private readonly applicationId: string;
  private readonly signatureSecret: string;
  private readonly apiBaseUrl: string;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;
  private readonly toleranceSec: number;
  private readonly nowSec: () => number;

  constructor(options: VonageProviderOptions) {
    if (!options.apiKey.trim()) throw new OmallaError("validation", "Vonage API key is empty", 400);
    if (!options.apiSecret.trim()) throw new OmallaError("validation", "Vonage API secret is empty", 400);
    if (!options.applicationId.trim()) {
      throw new OmallaError("validation", "Vonage application ID is empty", 400);
    }
    this.apiKey = options.apiKey.trim();
    this.apiSecret = options.apiSecret.trim();
    this.applicationId = options.applicationId.trim();
    this.signatureSecret = options.signatureSecret?.trim() || this.apiSecret;
    this.apiBaseUrl = (options.apiBaseUrl ?? "https://api.nexmo.com").replace(/\/+$/, "");
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.timeoutMs = options.timeoutMs ?? 15_000;
    this.toleranceSec = options.toleranceSec ?? 300;
    this.nowSec = options.nowSec ?? (() => Math.floor(Date.now() / 1000));

    this.description = {
      id: "vonage",
      label: this.label,
      capabilities: VONAGE_CAPABILITIES,
      pstn: true,
      verification: "unit-tested",
      notes: [
        "Renders Vonage NCCO JSON (`talk`, `input`, `record`, `connect` WebSocket/phone/sip).",
        "Verifies Vonage HS256 Bearer JWT + SHA-256 `payload_hash` over raw wire bytes.",
        "Supports live NCCO and SIP/PSTN transfers via `PUT /v1/calls/{uuid}`.",
      ],
    };
  }

  verifyWebhook(request: WebhookRequest): WebhookVerification {
    const auth = request.headers.authorization ?? "";
    if (!auth.toLowerCase().startsWith("bearer ")) {
      return { valid: false, reason: "missing Vonage Bearer JWT header" };
    }
    const token = auth.slice(7).trim();
    const parts = token.split(".");
    if (parts.length !== 3) {
      return { valid: false, reason: "malformed Vonage JWT" };
    }
    const [headerB64 = "", payloadB64 = "", sigB64 = ""] = parts;

    let header: Record<string, unknown>;
    let claims: Record<string, unknown>;
    try {
      header = JSON.parse(Buffer.from(headerB64, "base64url").toString("utf8")) as Record<string, unknown>;
      claims = JSON.parse(Buffer.from(payloadB64, "base64url").toString("utf8")) as Record<string, unknown>;
    } catch {
      return { valid: false, reason: "invalid Vonage JWT JSON encoding" };
    }

    if (header.alg !== "HS256") {
      return { valid: false, reason: `unsupported Vonage JWT alg: ${String(header.alg)}` };
    }

    const expectedSig = createHmac("sha256", this.signatureSecret)
      .update(`${headerB64}.${payloadB64}`, "utf8")
      .digest();
    const providedSig = Buffer.from(sigB64, "base64url");
    if (providedSig.length !== expectedSig.length || !timingSafeEqual(providedSig, expectedSig)) {
      return { valid: false, reason: "Vonage JWT signature mismatch" };
    }

    const now = this.nowSec();
    if (
      typeof claims.iat !== "number" ||
      !Number.isFinite(claims.iat) ||
      Math.abs(now - claims.iat) > this.toleranceSec
    ) {
      return { valid: false, reason: "Vonage JWT missing or out-of-window iat claim" };
    }
    if (
      typeof claims.exp === "number" &&
      (!Number.isFinite(claims.exp) || now > claims.exp + this.toleranceSec)
    ) {
      return { valid: false, reason: "Vonage JWT expired" };
    }

    const rawBytes =
      request.rawBody ??
      Buffer.from(
        request.json ? JSON.stringify(request.json) : new URLSearchParams(request.form).toString(),
        "utf8",
      );
    if (rawBytes.length > 0 && (typeof claims.payload_hash !== "string" || !claims.payload_hash.trim())) {
      return { valid: false, reason: "Vonage JWT missing required payload_hash claim" };
    }
    if (typeof claims.payload_hash === "string") {
      const actualHash = createHash("sha256").update(rawBytes).digest("hex");
      const expHashBuf = Buffer.from(claims.payload_hash.toLowerCase(), "utf8");
      const actHashBuf = Buffer.from(actualHash.toLowerCase(), "utf8");
      if (expHashBuf.length !== actHashBuf.length || !timingSafeEqual(expHashBuf, actHashBuf)) {
        return { valid: false, reason: "Vonage payload_hash mismatch" };
      }
    }

    return { valid: true };
  }

  /** Helper for deterministic offline Vonage webhook tests. */
  static signWebhookJwt(
    rawBody: Uint8Array | string,
    secret: string,
    options: { iat?: number; jti?: string } = {},
  ): string {
    const iat = options.iat ?? Math.floor(Date.now() / 1000);
    const bodyBuf = typeof rawBody === "string" ? Buffer.from(rawBody, "utf8") : Buffer.from(rawBody);
    const payloadHash = createHash("sha256").update(bodyBuf).digest("hex");
    const headerB64 = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" }), "utf8").toString("base64url");
    const payloadB64 = Buffer.from(
      JSON.stringify({
        iat,
        jti: options.jti ?? randomBytes(8).toString("hex"),
        payload_hash: payloadHash,
      }),
      "utf8",
    ).toString("base64url");
    const sigB64 = createHmac("sha256", secret)
      .update(`${headerB64}.${payloadB64}`, "utf8")
      .digest("base64url");
    return `Bearer ${headerB64}.${payloadB64}.${sigB64}`;
  }

  parseInbound(request: WebhookRequest): InboundCallEvent {
    const json = request.json ?? {};
    const providerCallId = String(json.uuid ?? json.conversation_uuid ?? request.form.uuid ?? "");
    if (!providerCallId) {
      throw new OmallaError("validation", "Vonage inbound webhook missing uuid", 400);
    }
    const from = normalizeVonageParty(json.from ?? request.form.from);
    const to = normalizeVonageParty(json.to ?? request.form.to);
    const dir = String(json.direction ?? request.form.direction ?? "inbound").toLowerCase();
    return {
      providerCallId,
      from,
      to,
      direction: dir === "outbound" ? "outbound" : "inbound",
      status: "ringing",
      raw: { ...request.form, uuid: providerCallId },
    };
  }

  parseStatus(request: WebhookRequest): CallStatusEvent {
    const json = request.json ?? {};
    const providerCallId = String(json.uuid ?? json.conversation_uuid ?? request.form.uuid ?? "");
    if (!providerCallId) {
      throw new OmallaError("validation", "Vonage status webhook missing uuid", 400);
    }
    const rawStatus = String(json.status ?? request.form.status ?? "").toLowerCase();
    const mapped =
      rawStatus === "started"
        ? "initiated"
        : rawStatus === "answered"
          ? "in-progress"
          : rawStatus === "timeout" || rawStatus === "unanswered"
            ? "no-answer"
            : rawStatus === "rejected"
              ? "busy"
              : rawStatus;

    return {
      providerCallId,
      status: normalizeCallStatus(mapped),
      ...(json.from ? { from: normalizeVonageParty(json.from) } : {}),
      ...(json.to ? { to: normalizeVonageParty(json.to) } : {}),
      ...(json.duration !== undefined ? { durationSec: Number(json.duration) || 0 } : {}),
    };
  }

  parseDtmf(request: WebhookRequest): DtmfEvent {
    const json = request.json ?? {};
    const dtmfObj = asRecord(json.dtmf);
    const providerCallId = String(json.uuid ?? json.conversation_uuid ?? request.form.uuid ?? "");
    const digits = String(dtmfObj?.digits ?? json.digits ?? request.form.digits ?? "");
    if (!providerCallId || !digits) {
      throw new OmallaError("validation", "Vonage DTMF webhook missing uuid or digits", 400);
    }
    return { providerCallId, digits };
  }

  parseRecordingStatus(request: WebhookRequest): RecordingEvent {
    const json = request.json ?? {};
    return {
      providerCallId: String(json.conversation_uuid ?? json.uuid ?? "unknown"),
      recordingId: String(json.recording_uuid ?? "unknown"),
      status: json.recording_url ? "completed" : "in-progress",
      ...(typeof json.recording_url === "string" ? { url: json.recording_url } : {}),
      ...(json.duration !== undefined ? { durationMs: Math.round(Number(json.duration) * 1000) } : {}),
    };
  }

  parseSms(request: WebhookRequest): SmsEvent {
    const json = request.json ?? {};
    const providerMessageId = String(json.message_uuid ?? json.messageId ?? request.form.messageId ?? "");
    if (!providerMessageId) {
      throw new OmallaError("validation", "Vonage SMS webhook missing message_uuid", 400);
    }
    return {
      providerMessageId,
      from: normalizeVonageParty(json.from ?? json.msisdn ?? request.form.msisdn),
      to: normalizeVonageParty(json.to ?? request.form.to),
      body: String(json.text ?? request.form.text ?? ""),
      status: "received",
    };
  }

  renderInboundResponse(options: InboundResponseOptions): ProviderHttpResponse {
    const ncco: Array<Record<string, unknown>> = [];
    if (options.say) {
      ncco.push({ action: "talk", text: options.say });
    }
    if (options.startRecording) {
      ncco.push({
        action: "record",
        eventUrl: [options.startRecording.statusCallbackUrl],
        channels: options.startRecording.channels === "dual" ? 2 : 1,
      });
    }
    if (options.voicemail) {
      ncco.push(
        { action: "talk", text: options.voicemail.greeting },
        {
          action: "record",
          eventUrl: [options.voicemail.actionUrl],
          endOnSilence: 4,
          endOnKey: "#",
          timeOut: options.voicemail.maxLengthSec ?? 120,
          beepStart: true,
        },
      );
    }
    if (options.dial) {
      const to = options.dial.to;
      const endpoint =
        to.startsWith("sip:") || to.startsWith("sips:")
          ? { type: "sip", uri: to }
          : { type: "phone", number: to.replace(/^\+/, "") };
      ncco.push({
        action: "connect",
        timeout: options.dial.timeoutSec ?? 25,
        ...(options.dial.callerId ? { from: options.dial.callerId.replace(/^\+/, "") } : {}),
        endpoint: [endpoint],
      });
    }
    if (options.gather) {
      if (options.gather.prompt) {
        ncco.push({ action: "talk", text: options.gather.prompt, bargeIn: true });
      }
      ncco.push({
        action: "input",
        eventUrl: [options.gather.actionUrl],
        type: options.gather.input === "speech" ? ["speech"] : ["dtmf"],
        dtmf: {
          maxDigits: options.gather.numDigits ?? 1,
          timeOut: options.gather.timeoutSec ?? 5,
        },
      });
    }
    if (options.mediaStreamUrl) {
      ncco.push({
        action: "connect",
        endpoint: [
          {
            type: "websocket",
            uri: options.mediaStreamUrl,
            "content-type": "audio/l16;rate=16000",
            headers: options.parameters ?? {},
          },
        ],
      });
    }
    if (options.closingSay) {
      ncco.push({ action: "talk", text: options.closingSay });
    }
    return {
      status: 200,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify(ncco),
    };
  }

  renderHangupResponse(text?: string): ProviderHttpResponse {
    const ncco = text ? [{ action: "talk", text }] : [];
    return {
      status: 200,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify(ncco),
    };
  }

  parseMediaMessage(raw: string): MediaStreamEvent {
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return { type: "unknown", raw };
    }
    const msg = asRecord(parsed);
    if (!msg) return { type: "unknown", raw };
    if (msg.event === "websocket:connected") {
      return {
        type: "start",
        streamId: String(msg.uuid ?? "stream_vonage"),
        callId: String(msg.callId ?? msg.uuid ?? ""),
        format: { encoding: "audio/l16", sampleRate: 16000, channels: 1 },
        parameters: {},
      };
    }
    if (msg.event === "websocket:dtmf") {
      return { type: "dtmf", digit: String(msg.digit ?? "") };
    }
    if (msg.event === "media" && typeof msg.payload === "string") {
      return { type: "media", track: "inbound", payload: msg.payload };
    }
    return { type: "unknown", raw };
  }

  encodeMediaFrame(_streamId: string, payloadBase64: string): string {
    return JSON.stringify({ event: "media", payload: payloadBase64 });
  }

  encodeClearFrame(): string {
    return JSON.stringify({ event: "websocket:cleared" });
  }

  async createCall(request: CreateCallRequest): Promise<ProviderCall> {
    const res = await this.apiRequest("POST", "/v1/calls", {
      to: [{ type: "phone", number: request.to.replace(/^\+/, "") }],
      from: { type: "phone", number: request.from.replace(/^\+/, "") },
      answer_url: [request.answerUrl],
      answer_method: "POST",
      ...(request.statusCallbackUrl ? { event_url: [request.statusCallbackUrl], event_method: "POST" } : {}),
      ...(request.timeoutSec ? { ringing_timer: request.timeoutSec } : {}),
    });
    return {
      providerCallId: String(res.uuid ?? ""),
      status: normalizeCallStatus(String(res.status ?? "started")),
    };
  }

  async hangupCall(providerCallId: string): Promise<void> {
    await this.apiRequest("PUT", `/v1/calls/${encodeURIComponent(providerCallId)}`, {
      action: "hangup",
    });
  }

  async redirectCall(providerCallId: string, destination: string): Promise<void> {
    if (destination.startsWith("+") || destination.startsWith("sip:") || destination.startsWith("sips:")) {
      const endpoint =
        destination.startsWith("sip:") || destination.startsWith("sips:")
          ? { type: "sip", uri: destination }
          : { type: "phone", number: destination.replace(/^\+/, "") };
      await this.apiRequest("PUT", `/v1/calls/${encodeURIComponent(providerCallId)}`, {
        action: "transfer",
        destination: {
          type: "ncco",
          ncco: [{ action: "connect", endpoint: [endpoint] }],
        },
      });
      return;
    }
    await this.apiRequest("PUT", `/v1/calls/${encodeURIComponent(providerCallId)}`, {
      action: "transfer",
      destination: {
        type: "ncco",
        url: [destination],
      },
    });
  }

  async sendSms(request: SendSmsRequest): Promise<ProviderSms> {
    const res = await this.apiRequest("POST", "/v1/messages", {
      message_type: "text",
      channel: "sms",
      to: request.to.replace(/^\+/, ""),
      from: request.from.replace(/^\+/, ""),
      text: request.body,
    });
    return {
      providerMessageId: String(res.message_uuid ?? ""),
      status: "queued",
    };
  }

  private async apiRequest(
    method: "GET" | "POST" | "PUT",
    path: string,
    body?: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    const url = `${this.apiBaseUrl}${path}`;
    const basic = Buffer.from(`${this.apiKey}:${this.apiSecret}`).toString("base64");
    const headers: Record<string, string> = {
      authorization: `Basic ${basic}`,
      "x-vonage-application-id": this.applicationId,
      accept: "application/json",
    };
    if (body !== undefined) {
      headers["content-type"] = "application/json";
    }
    let response: Response;
    try {
      response = await this.fetchImpl(url, {
        method,
        headers,
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
        signal: AbortSignal.timeout(this.timeoutMs),
      });
    } catch (error) {
      throw new OmallaError("provider_error", `Vonage request failed: ${(error as Error).message}`, 502);
    }
    if (response.status === 204) return {};
    const text = await response.text();
    let parsed: Record<string, unknown> = {};
    if (text) {
      try {
        parsed = JSON.parse(text) as Record<string, unknown>;
      } catch {
        parsed = {};
      }
    }
    if (!response.ok) {
      throw new OmallaError("provider_error", `HTTP ${response.status} from Vonage`, 502);
    }
    return parsed;
  }
}

function normalizeVonageParty(raw: unknown): string {
  if (typeof raw === "string") {
    const trimmed = raw.trim();
    if (/^\d{7,15}$/.test(trimmed)) return `+${trimmed}`;
    return trimmed;
  }
  const obj = asRecord(raw);
  if (obj) {
    if (typeof obj.number === "string") return normalizeVonageParty(obj.number);
    if (typeof obj.uri === "string") return obj.uri;
  }
  return "";
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}
