import {
  createHmac,
  createPublicKey,
  sign as cryptoSign,
  timingSafeEqual,
  verify as cryptoVerify,
  type KeyObject,
} from "node:crypto";
import { OmallaError } from "@omalla/core";
import type {
  CallStatusEvent,
  CreateCallRequest,
  DtmfEvent,
  InboundCallEvent,
  InboundResponseOptions,
  MediaStreamEvent,
  NumberOffer,
  NumberSearchQuery,
  ProviderCall,
  ProviderDescription,
  ProviderHttpResponse,
  ProviderSms,
  ProvisionNumberRequest,
  ProvisionedNumber,
  RecordingEvent,
  SendSmsRequest,
  SmsEvent,
  TelephonyCapabilities,
  TelephonyProvider,
  WebhookRequest,
  WebhookVerification,
} from "../provider.js";
import { normalizeCallStatus } from "../provider.js";

export interface TelnyxProviderOptions {
  apiKey: string;
  connectionId: string;
  /** Ed25519 public key (PEM, base64 SPKI DER, or base64 raw 32-byte key). */
  publicKey?: string;
  /** Shared HMAC-SHA256 secret for Telnyx TeXML / HMAC webhook mode. */
  webhookSecret?: string;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
  toleranceSec?: number;
  nowSec?: () => number;
}

const TELNYX_CAPABILITIES: TelephonyCapabilities = {
  voice: true,
  mediaStream: "bidirectional",
  sms: true,
  dtmf: true,
  transfer: true,
  recording: true,
  numberProvisioning: true,
  signedWebhooks: true,
  sip: true,
};

// RFC 8410 ASN.1 SubjectPublicKeyInfo prefix for raw 32-byte Ed25519 public keys
const ED25519_SPKI_PREFIX = Buffer.from("302a300506032b6570032100", "hex");

/**
 * Telnyx Call Control v2 + TeXML + Bidirectional Media Streams adapter.
 *
 * Supports Ed25519 (`telnyx-signature-ed25519` + `telnyx-timestamp`) and
 * raw-byte HMAC-SHA256 (`telnyx-signature-hmac-sha256`) webhook verification
 * with ±300 s replay skew protection, plus warm/cold call transfer via
 * `/v2/calls/{call_control_id}/actions/transfer` and SIP URI targets.
 */
export class TelnyxProvider implements TelephonyProvider {
  readonly id = "telnyx" as const;
  readonly label = "Telnyx Call Control";
  readonly capabilities = TELNYX_CAPABILITIES;
  readonly description: ProviderDescription;

  private readonly apiKey: string;
  private readonly connectionId: string;
  private readonly publicKeyObj: KeyObject | null;
  private readonly webhookSecret: string | null;
  private readonly apiBaseUrl: string;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;
  private readonly toleranceSec: number;
  private readonly nowSec: () => number;

  constructor(options: TelnyxProviderOptions) {
    if (!options.apiKey.trim()) {
      throw new OmallaError("validation", "Telnyx API key is empty", 400);
    }
    if (!options.connectionId.trim()) {
      throw new OmallaError("validation", "Telnyx connection ID is empty", 400);
    }
    this.apiKey = options.apiKey.trim();
    this.connectionId = options.connectionId.trim();
    this.publicKeyObj = options.publicKey ? parseEd25519PublicKey(options.publicKey) : null;
    this.webhookSecret = options.webhookSecret?.trim() || null;
    this.apiBaseUrl = (options.apiBaseUrl ?? "https://api.telnyx.com").replace(/\/+$/, "");
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.timeoutMs = options.timeoutMs ?? 15_000;
    this.toleranceSec = options.toleranceSec ?? 300;
    this.nowSec = options.nowSec ?? (() => Math.floor(Date.now() / 1000));

    this.description = {
      id: "telnyx",
      label: this.label,
      capabilities: TELNYX_CAPABILITIES,
      pstn: true,
      verification: "unit-tested",
      notes: [
        "Supports Telnyx Call Control v2 JSON events, TeXML responses, and bidirectional RTP/WS media.",
        "Verifies Ed25519 or HMAC-SHA256 webhook signatures over exact raw wire bytes with ±300 s skew enforcement.",
        "Supports blind and warm attended transfers to E.164 numbers or SIP URIs.",
      ],
    };
  }

  verifyWebhook(request: WebhookRequest): WebhookVerification {
    const tsHeader = request.headers["telnyx-timestamp"];
    if (!tsHeader || !/^\d+$/.test(tsHeader.trim())) {
      return { valid: false, reason: "missing or non-numeric telnyx-timestamp header" };
    }
    const ts = Number(tsHeader.trim());
    const now = this.nowSec();
    if (Math.abs(now - ts) > this.toleranceSec) {
      return { valid: false, reason: "Telnyx webhook timestamp outside ±300s window" };
    }

    const rawBytes =
      request.rawBody ??
      Buffer.from(request.json ? JSON.stringify(request.json) : new URLSearchParams(request.form).toString(), "utf8");
    const signedBytes = Buffer.concat([Buffer.from(`${ts}|`, "utf8"), Buffer.from(rawBytes)]);

    const edSigB64 = request.headers["telnyx-signature-ed25519"];
    if (edSigB64 && this.publicKeyObj) {
      try {
        const sigBuf = Buffer.from(edSigB64.trim(), "base64");
        if (sigBuf.length === 64 && cryptoVerify(null, signedBytes, this.publicKeyObj, sigBuf)) {
          return { valid: true };
        }
      } catch {
        return { valid: false, reason: "invalid Ed25519 Telnyx signature encoding" };
      }
      return { valid: false, reason: "Telnyx Ed25519 signature mismatch" };
    }

    const hmacHeader =
      request.headers["telnyx-signature-hmac-sha256"] ?? request.headers["x-telnyx-signature"];
    if (hmacHeader && this.webhookSecret) {
      const cleanHexOrB64 = hmacHeader.trim().replace(/^sha256=/i, "");
      const expectedBuf = createHmac("sha256", this.webhookSecret).update(signedBytes).digest();
      const gotHexBuf = /^[0-9a-fA-F]{64}$/.test(cleanHexOrB64)
        ? Buffer.from(cleanHexOrB64, "hex")
        : Buffer.from(cleanHexOrB64, "base64");
      if (gotHexBuf.length === expectedBuf.length && timingSafeEqual(gotHexBuf, expectedBuf)) {
        return { valid: true };
      }
      return { valid: false, reason: "Telnyx HMAC-SHA256 signature mismatch" };
    }

    if (!this.publicKeyObj && !this.webhookSecret) {
      return {
        valid: false,
        reason: "Telnyx webhook verification requires TELNYX_PUBLIC_KEY or TELNYX_WEBHOOK_SECRET",
      };
    }
    return { valid: false, reason: "missing Telnyx signature header" };
  }

  /** Helper for deterministic offline test fixtures (Ed25519 private key or HMAC secret). */
  static signWebhookPayload(
    rawBody: Uint8Array | string,
    timestampSec: number,
    signer: { ed25519PrivateKeyPem?: string; hmacSecret?: string },
  ): Record<string, string> {
    const bodyBuf = typeof rawBody === "string" ? Buffer.from(rawBody, "utf8") : Buffer.from(rawBody);
    const signedBytes = Buffer.concat([Buffer.from(`${timestampSec}|`, "utf8"), bodyBuf]);
    const headers: Record<string, string> = {
      "telnyx-timestamp": String(timestampSec),
    };
    if (signer.ed25519PrivateKeyPem) {
      headers["telnyx-signature-ed25519"] = cryptoSign(null, signedBytes, signer.ed25519PrivateKeyPem).toString("base64");
    }
    if (signer.hmacSecret) {
      headers["telnyx-signature-hmac-sha256"] = createHmac("sha256", signer.hmacSecret)
        .update(signedBytes)
        .digest("hex");
    }
    return headers;
  }

  parseInbound(request: WebhookRequest): InboundCallEvent {
    const payload = extractTelnyxPayload(request);
    const providerCallId = String(
      payload.call_control_id ?? payload.call_leg_id ?? request.form.CallSid ?? "",
    );
    if (!providerCallId) {
      throw new OmallaError("validation", "Telnyx webhook missing call_control_id / CallSid", 400);
    }
    const dirRaw = String(payload.direction ?? request.form.Direction ?? "incoming").toLowerCase();
    return {
      providerCallId,
      from: String(payload.from ?? request.form.From ?? ""),
      to: String(payload.to ?? request.form.To ?? ""),
      direction: dirRaw.includes("out") ? "outbound" : "inbound",
      status: "ringing",
      raw: flattenStrings(payload, request.form),
    };
  }

  parseStatus(request: WebhookRequest): CallStatusEvent {
    const data = asRecord(request.json?.data);
    const eventType = String(data?.event_type ?? "");
    const payload = extractTelnyxPayload(request);
    const providerCallId = String(
      payload.call_control_id ?? payload.call_leg_id ?? request.form.CallSid ?? "",
    );
    if (!providerCallId) {
      throw new OmallaError("validation", "Telnyx status webhook missing call_control_id", 400);
    }

    let statusRaw = String(payload.state ?? request.form.CallStatus ?? "");
    if (!statusRaw && eventType) {
      if (eventType === "call.initiated") statusRaw = "initiated";
      else if (eventType === "call.answered") statusRaw = "in-progress";
      else if (eventType === "call.hangup") {
        const cause = String(payload.hangup_cause ?? "normal_clearing").toLowerCase();
        statusRaw =
          cause === "user_busy"
            ? "busy"
            : cause === "no_answer" || cause === "timeout"
              ? "no-answer"
              : cause === "originator_cancel"
                ? "canceled"
                : cause === "normal_clearing" || cause === "hangup"
                  ? "completed"
                  : "failed";
      }
    }

    const startIso = typeof payload.start_time === "string" ? Date.parse(payload.start_time) : NaN;
    const endIso = typeof payload.end_time === "string" ? Date.parse(payload.end_time) : NaN;
    const computedDuration =
      Number.isFinite(startIso) && Number.isFinite(endIso) && endIso >= startIso
        ? Math.round((endIso - startIso) / 1000)
        : request.form.CallDuration
          ? Number(request.form.CallDuration) || 0
          : undefined;

    return {
      providerCallId,
      status: normalizeCallStatus(statusRaw || "in-progress"),
      ...(payload.from ? { from: String(payload.from) } : {}),
      ...(payload.to ? { to: String(payload.to) } : {}),
      ...(computedDuration !== undefined ? { durationSec: computedDuration } : {}),
    };
  }

  parseDtmf(request: WebhookRequest): DtmfEvent {
    const payload = extractTelnyxPayload(request);
    const providerCallId = String(payload.call_control_id ?? request.form.CallSid ?? "");
    const digits = String(payload.digit ?? payload.digits ?? request.form.Digits ?? "");
    if (!providerCallId || !digits) {
      throw new OmallaError("validation", "Telnyx DTMF webhook missing call_control_id or digit", 400);
    }
    return { providerCallId, digits };
  }

  parseRecordingStatus(request: WebhookRequest): RecordingEvent {
    const payload = extractTelnyxPayload(request);
    const urls = asRecord(payload.recording_urls);
    const url = String(urls?.wav ?? urls?.mp3 ?? request.form.RecordingUrl ?? "");
    const statusRaw = String(payload.status ?? request.form.RecordingStatus ?? "completed").toLowerCase();
    return {
      providerCallId: String(payload.call_control_id ?? request.form.CallSid ?? "unknown"),
      recordingId: String(payload.recording_id ?? request.form.RecordingSid ?? "unknown"),
      status: statusRaw === "completed" ? "completed" : statusRaw === "failed" ? "failed" : "in-progress",
      ...(url ? { url } : {}),
      ...(payload.duration_millis ? { durationMs: Number(payload.duration_millis) || 0 } : {}),
    };
  }

  parseSms(request: WebhookRequest): SmsEvent {
    const payload = extractTelnyxPayload(request);
    const fromObj = asRecord(payload.from);
    const toArr = Array.isArray(payload.to) ? asRecord(payload.to[0]) : asRecord(payload.to);
    const providerMessageId = String(payload.id ?? request.form.MessageSid ?? "");
    if (!providerMessageId) {
      throw new OmallaError("validation", "Telnyx SMS webhook missing message id", 400);
    }
    return {
      providerMessageId,
      from: String(fromObj?.phone_number ?? payload.from ?? request.form.From ?? ""),
      to: String(toArr?.phone_number ?? payload.to ?? request.form.To ?? ""),
      body: String(payload.text ?? request.form.Body ?? ""),
      status: "received",
    };
  }

  renderInboundResponse(options: InboundResponseOptions): ProviderHttpResponse {
    const parts: string[] = [];
    if (options.say) parts.push(`<Say>${escapeXml(options.say)}</Say>`);
    if (options.startRecording) {
      const cb = escapeXmlAttr(options.startRecording.statusCallbackUrl);
      parts.push(`<Start><Recording recordingStatusCallback="${cb}" channels="${options.startRecording.channels ?? "mono"}"/></Start>`);
    }
    if (options.voicemail) {
      parts.push(
        `<Say>${escapeXml(options.voicemail.greeting)}</Say>`,
        `<Record action="${escapeXmlAttr(options.voicemail.actionUrl)}" maxLength="${options.voicemail.maxLengthSec ?? 120}" playBeep="true"/>`,
      );
    }
    if (options.dial) {
      const to = options.dial.to;
      const callerAttr = options.dial.callerId ? ` callerId="${escapeXmlAttr(options.dial.callerId)}"` : "";
      const targetXml = to.startsWith("sip:") || to.startsWith("sips:")
        ? `<Sip>${escapeXml(to)}</Sip>`
        : escapeXml(to);
      parts.push(`<Dial timeout="${options.dial.timeoutSec ?? 25}"${callerAttr}>${targetXml}</Dial>`);
    }
    if (options.gather) {
      const prompt = options.gather.prompt ? `<Say>${escapeXml(options.gather.prompt)}</Say>` : "";
      const numDigitsAttr = options.gather.numDigits ? ` numDigits="${options.gather.numDigits}"` : "";
      parts.push(
        `<Gather input="${options.gather.input ?? "dtmf"}" action="${escapeXmlAttr(options.gather.actionUrl)}" method="POST" timeout="${options.gather.timeoutSec ?? 5}"${numDigitsAttr}>${prompt}</Gather>`,
      );
    }
    if (options.mediaStreamUrl) {
      const params = Object.entries(options.parameters ?? {})
        .map(([k, v]) => `<Parameter name="${escapeXmlAttr(k)}" value="${escapeXmlAttr(v)}"/>`)
        .join("");
      parts.push(
        `<Connect><Stream url="${escapeXmlAttr(options.mediaStreamUrl)}" bidirectionalMode="rtp">${params}</Stream></Connect>`,
      );
    }
    if (options.closingSay) parts.push(`<Say>${escapeXml(options.closingSay)}</Say>`);
    if (options.hangup) parts.push("<Hangup/>");
    return {
      status: 200,
      contentType: "text/xml; charset=utf-8",
      body: `<Response>${parts.join("")}</Response>`,
    };
  }

  renderHangupResponse(text?: string): ProviderHttpResponse {
    const say = text ? `<Say>${escapeXml(text)}</Say>` : "";
    return {
      status: 200,
      contentType: "text/xml; charset=utf-8",
      body: `<Response>${say}<Hangup/></Response>`,
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
    const event = String(msg.event ?? "");
    if (event === "connected") return { type: "connected" };
    if (event === "stop") return { type: "stop" };
    if (event === "mark") {
      const mark = asRecord(msg.mark);
      return { type: "mark", name: String(mark?.name ?? "") };
    }
    if (event === "dtmf") {
      const dtmf = asRecord(msg.dtmf);
      return { type: "dtmf", digit: String(dtmf?.digit ?? msg.digit ?? "") };
    }
    if (event === "start") {
      const start = asRecord(msg.start) ?? msg;
      const fmt = asRecord(start.media_format ?? start.mediaFormat);
      const encRaw = String(fmt?.encoding ?? "PCMU").toUpperCase();
      const encoding = encRaw.includes("L16") ? "audio/l16" : encRaw.includes("PCM") && !encRaw.includes("PCMU") ? "audio/pcm" : "audio/x-mulaw";
      return {
        type: "start",
        streamId: String(msg.stream_id ?? start.streamSid ?? start.call_control_id ?? "stream_telnyx"),
        callId: String(start.call_control_id ?? start.callSid ?? ""),
        format: {
          encoding,
          sampleRate: Number(fmt?.sample_rate ?? fmt?.sampleRate ?? 8000) || 8000,
          channels: Number(fmt?.channels ?? 1) || 1,
        },
        parameters: flattenStrings(asRecord(start.custom_parameters ?? start.customParameters) ?? {}, {}),
      };
    }
    if (event === "media") {
      const media = asRecord(msg.media);
      if (!media) return { type: "unknown", raw };
      return {
        type: "media",
        track: media.track === "outbound" ? "outbound" : "inbound",
        payload: String(media.payload ?? ""),
        ...(media.timestamp !== undefined ? { timestamp: String(media.timestamp) } : {}),
      };
    }
    return { type: "unknown", raw };
  }

  encodeMediaFrame(streamId: string, payloadBase64: string): string {
    return JSON.stringify({ event: "media", stream_id: streamId, media: { payload: payloadBase64 } });
  }

  encodeClearFrame(streamId: string): string {
    return JSON.stringify({ event: "clear", stream_id: streamId });
  }

  encodeMarkFrame(streamId: string, name: string): string {
    return JSON.stringify({ event: "mark", stream_id: streamId, mark: { name } });
  }

  async createCall(request: CreateCallRequest): Promise<ProviderCall> {
    const res = await this.apiRequest("POST", "/v2/calls", {
      connection_id: this.connectionId,
      to: request.to,
      from: request.from,
      webhook_url: request.answerUrl,
      webhook_url_method: "POST",
      ...(request.timeoutSec ? { timeout_secs: request.timeoutSec } : {}),
      ...(request.machineDetection ? { answering_machine_detection: "detect" } : {}),
    });
    const data = asRecord(res.data) ?? res;
    return {
      providerCallId: String(data.call_control_id ?? data.call_leg_id ?? ""),
      status: normalizeCallStatus(String(data.state ?? "initiated")),
    };
  }

  async hangupCall(providerCallId: string): Promise<void> {
    await this.apiRequest("POST", `/v2/calls/${encodeURIComponent(providerCallId)}/actions/hangup`, {});
  }

  /**
   * Redirects or transfers a live Telnyx call:
   *  - If `destination` is a PSTN E.164 (`+...`) or `sip:`/`sips:` URI, executes
   *    `/v2/calls/{id}/actions/transfer` directly.
   *  - If `destination` is an HTTP(S) webhook URL, updates the call webhook / TeXML URL.
   */
  async redirectCall(providerCallId: string, destination: string): Promise<void> {
    if (destination.startsWith("+") || destination.startsWith("sip:") || destination.startsWith("sips:")) {
      await this.transferCall(providerCallId, { to: destination, mode: "blind" });
      return;
    }
    await this.apiRequest(
      "POST",
      `/v2/texml/calls/${encodeURIComponent(providerCallId)}/update`,
      { Url: destination, Method: "POST" },
    );
  }

  async transferCall(
    providerCallId: string,
    input: { to: string; from?: string; mode?: "warm" | "blind"; webhookUrl?: string; sipAuthUsername?: string },
  ): Promise<void> {
    await this.apiRequest(
      "POST",
      `/v2/calls/${encodeURIComponent(providerCallId)}/actions/transfer`,
      {
        to: input.to,
        ...(input.from ? { from: input.from } : {}),
        ...(input.webhookUrl ? { webhook_url: input.webhookUrl } : {}),
        ...(input.mode === "warm" ? { park_after_unbridge: "self" } : {}),
      },
    );
  }

  async startRecording(providerCallId: string): Promise<void> {
    await this.apiRequest("POST", `/v2/calls/${encodeURIComponent(providerCallId)}/actions/record_start`, {
      format: "wav",
      channels: "single",
    });
  }

  async stopRecording(providerCallId: string): Promise<void> {
    await this.apiRequest("POST", `/v2/calls/${encodeURIComponent(providerCallId)}/actions/record_stop`, {});
  }

  async sendSms(request: SendSmsRequest): Promise<ProviderSms> {
    const res = await this.apiRequest("POST", "/v2/messages", {
      from: request.from,
      to: request.to,
      text: request.body,
      ...(request.statusCallbackUrl ? { webhook_url: request.statusCallbackUrl } : {}),
    });
    const data = asRecord(res.data) ?? res;
    return {
      providerMessageId: String(data.id ?? ""),
      status: "queued",
    };
  }

  async searchNumbers(query: NumberSearchQuery): Promise<NumberOffer[]> {
    const params = new URLSearchParams();
    params.set("filter[country_code]", (query.countryCode || "US").toUpperCase());
    if (query.areaCode) params.set("filter[national_destination_code]", query.areaCode);
    if (query.contains) params.set("filter[phone_number][contains]", query.contains);
    params.set("page[size]", String(Math.min(Math.max(query.limit ?? 10, 1), 30)));
    const res = await this.apiRequest("GET", `/v2/available_phone_numbers?${params.toString()}`);
    const list = Array.isArray(res.data) ? res.data : [];
    return list
      .map((item) => {
        const rec = asRecord(item) ?? {};
        const e164 = String(rec.phone_number ?? "");
        return {
          e164,
          friendlyName: e164,
          capabilities: ["voice", "sms"] as Array<"voice" | "sms" | "mms">,
          costNote: "Carrier charges apply via Telnyx. Omalla does not bill for numbers.",
        };
      })
      .filter((o) => o.e164.startsWith("+"));
  }

  async provisionNumber(request: ProvisionNumberRequest): Promise<ProvisionedNumber> {
    const res = await this.apiRequest("POST", "/v2/number_orders", {
      phone_numbers: [{ phone_number: request.e164 }],
      connection_id: this.connectionId,
    });
    const data = asRecord(res.data) ?? res;
    return {
      providerNumberId: String(data.id ?? request.e164),
      e164: request.e164,
      friendlyName: request.friendlyName ?? request.e164,
      capabilities: ["voice", "sms"],
    };
  }

  async releaseNumber(providerNumberId: string): Promise<void> {
    await this.apiRequest("DELETE", `/v2/phone_numbers/${encodeURIComponent(providerNumberId)}`);
  }

  private async apiRequest(
    method: "GET" | "POST" | "DELETE",
    path: string,
    body?: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    const url = `${this.apiBaseUrl}${path}`;
    const headers: Record<string, string> = {
      authorization: `Bearer ${this.apiKey}`,
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
      throw new OmallaError(
        "provider_error",
        `Telnyx request failed: ${(error as Error).message}`,
        502,
      );
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
      throw new OmallaError("provider_error", `HTTP ${response.status} from Telnyx`, 502);
    }
    return parsed;
  }
}

function parseEd25519PublicKey(raw: string): KeyObject {
  const trimmed = raw.trim();
  if (trimmed.includes("BEGIN PUBLIC KEY")) {
    return createPublicKey(trimmed);
  }
  const bytes = Buffer.from(trimmed, "base64");
  if (bytes.length === 32) {
    return createPublicKey({
      key: Buffer.concat([ED25519_SPKI_PREFIX, bytes]),
      format: "der",
      type: "spki",
    });
  }
  return createPublicKey({ key: bytes, format: "der", type: "spki" });
}

function extractTelnyxPayload(request: WebhookRequest): Record<string, unknown> {
  const data = asRecord(request.json?.data);
  const payload = asRecord(data?.payload);
  return payload ?? request.json ?? {};
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function flattenStrings(a: Record<string, unknown>, b: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = { ...b };
  for (const [k, v] of Object.entries(a)) {
    if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
      out[k] = String(v);
    }
  }
  return out;
}

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function escapeXmlAttr(value: string): string {
  return escapeXml(value).replace(/\r?\n/g, "&#10;");
}
