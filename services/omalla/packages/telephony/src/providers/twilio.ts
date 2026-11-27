import { createHmac, timingSafeEqual } from "node:crypto";
import { OmallaError } from "@omalla/core";
import type {
  CallStatus,
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
  TelephonyProviderId,
  WebhookRequest,
  WebhookVerification,
} from "../provider.js";
import { normalizeCallStatus } from "../provider.js";

export interface TwilioProviderOptions {
  accountSid: string;
  authToken: string;
  /** Overrides https://api.twilio.com. SignalWire uses its own LaML base URL. */
  apiBaseUrl?: string;
  /** "twilio" (default) or the Twilio-compatible "signalwire" variant. */
  variant?: "twilio" | "signalwire";
  /** Injected in tests; never read from globals at call time. */
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

const TWILIO_CAPABILITIES: TelephonyCapabilities = {
  voice: true,
  mediaStream: "bidirectional",
  sms: true,
  dtmf: true,
  transfer: true,
  recording: true,
  numberProvisioning: true,
  signedWebhooks: true,
  sip: false,
};

const SIGNATURE_HEADER = "x-twilio-signature";

/**
 * Twilio Programmable Voice + Messaging.
 *
 * Implemented against the public 2010-04-01 REST API and the Media Streams
 * WebSocket protocol. Signature verification follows Twilio's documented
 * algorithm: HMAC-SHA1 over the full URL followed by every POST parameter in
 * lexicographic order. Live carrier calls are NOT RUN in this repository
 * because no credentials are present; every REST path is exercised offline
 * with an injected fetch.
 */
export class TwilioProvider implements TelephonyProvider {
  readonly id: TelephonyProviderId;
  readonly label: string;
  readonly capabilities = TWILIO_CAPABILITIES;
  readonly description: ProviderDescription;

  private readonly accountSid: string;
  private readonly authToken: string;
  private readonly apiBaseUrl: string;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;

  constructor(options: TwilioProviderOptions) {
    if (!options.accountSid.trim()) throw new OmallaError("validation", "Twilio Account SID is empty", 400);
    if (!options.authToken.trim()) throw new OmallaError("validation", "Twilio auth token is empty", 400);
    this.accountSid = options.accountSid.trim();
    this.authToken = options.authToken;
    this.id = options.variant === "signalwire" ? "signalwire" : "twilio";
    this.label = this.id === "signalwire" ? "SignalWire (Twilio-compatible LaML)" : "Twilio Programmable Voice";
    this.apiBaseUrl = (
      options.apiBaseUrl ??
      (this.id === "signalwire" ? "https://YOUR_SPACE.signalwire.com/api/laml" : "https://api.twilio.com")
    ).replace(/\/+$/, "");
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.timeoutMs = options.timeoutMs ?? 15_000;
    this.description = {
      id: this.id,
      label: this.label,
      capabilities: TWILIO_CAPABILITIES,
      pstn: true,
      verification: "unit-tested",
      notes: [
        "Control plane and Media Streams framing are exercised offline with fixtures.",
        "No live PSTN call has been placed from this repository.",
        "Numbers and calls are billed by the carrier, never by Omalla.",
      ],
    };
  }

  /* ------------------------------------------------------------------ */
  /* webhooks                                                            */
  /* ------------------------------------------------------------------ */

  verifyWebhook(request: WebhookRequest): WebhookVerification {
    const header = request.headers[SIGNATURE_HEADER];
    if (!header) return { valid: false, reason: "missing X-Twilio-Signature header" };
    const provided = Buffer.from(header, "utf8");
    // Twilio signs the URL exactly as configured. The official SDK tolerates
    // the standard port being present or absent, so we do the same; each
    // candidate is still an exact HMAC over the signed string.
    for (const candidate of urlCandidates(request.url)) {
      const expected = Buffer.from(this.computeSignature(candidate, request.form), "utf8");
      if (provided.length === expected.length && timingSafeEqual(provided, expected)) {
        return { valid: true };
      }
    }
    return { valid: false, reason: "signature mismatch" };
  }

  /** Exposed for fixtures and the conformance test suite. */
  computeSignature(url: string, params: Record<string, string>): string {
    const joined = Object.keys(params)
      .sort()
      .map((key) => `${key}${params[key] ?? ""}`)
      .join("");
    return createHmac("sha1", this.authToken).update(Buffer.from(url + joined, "utf8")).digest("base64");
  }

  parseInbound(request: WebhookRequest): InboundCallEvent {
    const form = request.form;
    const providerCallId = requiredField(form, "CallSid");
    return {
      providerCallId,
      from: form.From ?? "",
      to: form.To ?? "",
      direction: form.Direction === "outbound-api" || form.Direction === "outbound-dial" ? "outbound" : "inbound",
      status: normalizeInboundStatus(form.CallStatus),
      raw: { ...form },
    };
  }

  parseStatus(request: WebhookRequest): CallStatusEvent {
    const form = request.form;
    return {
      providerCallId: requiredField(form, "CallSid"),
      status: normalizeCallStatus(form.CallStatus ?? ""),
      ...(form.From ? { from: form.From } : {}),
      ...(form.To ? { to: form.To } : {}),
      ...(form.CallDuration ? { durationSec: Number(form.CallDuration) || 0 } : {}),
      ...(form.ErrorMessage ? { error: form.ErrorMessage } : {}),
    };
  }

  parseDtmf(request: WebhookRequest): DtmfEvent {
    const digits = requiredField(request.form, "Digits");
    return { providerCallId: requiredField(request.form, "CallSid"), digits };
  }

  parseRecordingStatus(request: WebhookRequest): RecordingEvent {
    const form = request.form;
    const raw = (form.RecordingStatus ?? "").toLowerCase();
    return {
      providerCallId: requiredField(form, "CallSid"),
      recordingId: form.RecordingSid ?? form.RecordingUrl ?? "unknown",
      status: raw === "completed" ? "completed" : raw === "failed" || raw === "absent" ? "failed" : "in-progress",
      ...(form.RecordingUrl ? { url: form.RecordingUrl } : {}),
      ...(form.RecordingDuration
        ? { durationMs: Math.round(Number(form.RecordingDuration) * 1000) }
        : {}),
    };
  }

  parseSms(request: WebhookRequest): SmsEvent {
    const form = request.form;
    const raw = (form.SmsStatus ?? form.MessageStatus ?? "received").toLowerCase();
    return {
      providerMessageId: form.MessageSid ?? form.SmsSid ?? requiredField(form, "MessageSid"),
      from: form.From ?? "",
      to: form.To ?? "",
      body: form.Body ?? "",
      status:
        raw === "delivered"
          ? "delivered"
          : raw === "failed" || raw === "undelivered"
            ? "failed"
            : raw === "sent"
              ? "sent"
              : "received",
      ...(form.ErrorMessage ? { error: form.ErrorMessage } : {}),
    };
  }

  /* ------------------------------------------------------------------ */
  /* TwiML                                                               */
  /* ------------------------------------------------------------------ */

  renderInboundResponse(options: InboundResponseOptions): ProviderHttpResponse {
    const parts: string[] = [];

    if (options.say) parts.push(`<Say>${escapeXml(options.say)}</Say>`);

    if (options.startRecording) {
      const callback = escapeXmlAttribute(options.startRecording.statusCallbackUrl);
      parts.push(
        `<Start><Recording recordingStatusCallback="${callback}" recordingStatusCallbackMethod="POST"${options.startRecording.channels === "dual" ? ' channels="dual"' : ""}/></Start>`,
      );
    }

    if (options.voicemail) {
      const voicemail = options.voicemail;
      parts.push(
        `<Say>${escapeXml(voicemail.greeting)}</Say>`,
        `<Record action="${escapeXmlAttribute(voicemail.actionUrl)}" method="POST" maxLength="${voicemail.maxLengthSec ?? 120}" playBeep="true"/>`,
      );
    }

    if (options.dial) {
      const dial = options.dial;
      const attrs = [
        `timeout="${dial.timeoutSec ?? 25}"`,
        dial.callerId ? `callerId="${escapeXmlAttribute(dial.callerId)}"` : "",
      ]
        .filter(Boolean)
        .join(" ");
      parts.push(`<Dial ${attrs}>${escapeXml(dial.to)}</Dial>`);
    }

    if (options.gather) {
      const gather = options.gather;
      const attrs = [
        `input="${gather.input ?? "dtmf"}"`,
        `action="${escapeXmlAttribute(gather.actionUrl)}"`,
        'method="POST"',
        gather.numDigits ? `numDigits="${gather.numDigits}"` : "",
        `timeout="${gather.timeoutSec ?? 5}"`,
      ]
        .filter(Boolean)
        .join(" ");
      const prompt = gather.prompt ? `<Say>${escapeXml(gather.prompt)}</Say>` : "";
      parts.push(`<Gather ${attrs}>${prompt}</Gather>`);
    }

    if (options.mediaStreamUrl) {
      const parameters = Object.entries(options.parameters ?? {})
        .map(
          ([name, value]) =>
            `<Parameter name="${escapeXmlAttribute(name)}" value="${escapeXmlAttribute(value)}"/>`,
        )
        .join("");
      parts.push(`<Connect><Stream url="${escapeXmlAttribute(options.mediaStreamUrl)}">${parameters}</Stream></Connect>`);
    }

    if (options.closingSay) parts.push(`<Say>${escapeXml(options.closingSay)}</Say>`);
    if (options.hangup) parts.push("<Hangup/>");

    return xmlResponse(`<Response>${parts.join("")}</Response>`);
  }

  renderHangupResponse(text?: string): ProviderHttpResponse {
    const say = text ? `<Say>${escapeXml(text)}</Say>` : "";
    return xmlResponse(`<Response>${say}<Hangup/></Response>`);
  }

  /* ------------------------------------------------------------------ */
  /* Media Streams                                                       */
  /* ------------------------------------------------------------------ */

  parseMediaMessage(raw: string): MediaStreamEvent {
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return { type: "unknown", raw };
    }
    if (!parsed || typeof parsed !== "object") return { type: "unknown", raw };
    const message = parsed as Record<string, unknown>;
    const event = typeof message.event === "string" ? message.event : "";

    if (event === "connected") return { type: "connected" };
    if (event === "stop") return { type: "stop" };
    if (event === "mark") {
      const mark = asRecord(message.mark);
      return { type: "mark", name: typeof mark?.name === "string" ? mark.name : "" };
    }
    if (event === "dtmf") {
      const dtmf = asRecord(message.dtmf);
      return { type: "dtmf", digit: typeof dtmf?.digit === "string" ? dtmf.digit : "" };
    }
    if (event === "start") {
      const start = asRecord(message.start);
      if (!start) return { type: "unknown", raw };
      const format = asRecord(start.mediaFormat);
      const encoding = format?.encoding === "audio/pcm" ? "audio/pcm" : format?.encoding === "audio/l16" ? "audio/l16" : "audio/x-mulaw";
      return {
        type: "start",
        streamId: String(start.streamSid ?? ""),
        callId: String(start.callSid ?? ""),
        format: {
          encoding,
          sampleRate: Number(format?.sampleRate ?? 8000) || 8000,
          channels: Number(format?.channels ?? 1) || 1,
        },
        parameters: stringRecord(start.customParameters),
      };
    }
    if (event === "media") {
      const media = asRecord(message.media);
      if (!media) return { type: "unknown", raw };
      return {
        type: "media",
        track: media.track === "outbound" ? "outbound" : "inbound",
        payload: typeof media.payload === "string" ? media.payload : "",
        ...(media.timestamp !== undefined ? { timestamp: String(media.timestamp) } : {}),
      };
    }
    return { type: "unknown", raw };
  }

  /** JSON frame Omalla sends back to Twilio for playback. */
  encodeMediaFrame(streamId: string, payloadBase64: string): string {
    return JSON.stringify({ event: "media", streamSid: streamId, media: { payload: payloadBase64 } });
  }

  /** Clears queued outbound audio; used for barge-in. */
  encodeClearFrame(streamId: string): string {
    return JSON.stringify({ event: "clear", streamSid: streamId });
  }

  encodeMarkFrame(streamId: string, name: string): string {
    return JSON.stringify({ event: "mark", streamSid: streamId, mark: { name } });
  }

  /** JSON frame Omalla sends back to Twilio for playback. */
  static mediaFrame(streamId: string, payload: string): string {
    return JSON.stringify({ event: "media", streamSid: streamId, media: { payload } });
  }

  /** Clears queued outbound audio; used for barge-in. */
  static clearFrame(streamId: string): string {
    return JSON.stringify({ event: "clear", streamSid: streamId });
  }

  static markFrame(streamId: string, name: string): string {
    return JSON.stringify({ event: "mark", streamSid: streamId, mark: { name } });
  }

  /* ------------------------------------------------------------------ */
  /* REST control plane                                                  */
  /* ------------------------------------------------------------------ */

  async createCall(request: CreateCallRequest): Promise<ProviderCall> {
    const form = new URLSearchParams();
    form.set("To", request.to);
    form.set("From", request.from);
    form.set("Url", request.answerUrl);
    form.set("Method", "POST");
    if (request.statusCallbackUrl) {
      form.set("StatusCallback", request.statusCallbackUrl);
      form.append("StatusCallbackEvent", "initiated");
      form.append("StatusCallbackEvent", "ringing");
      form.append("StatusCallbackEvent", "answered");
      form.append("StatusCallbackEvent", "completed");
    }
    if (request.recordingCallbackUrl) {
      form.set("RecordingStatusCallback", request.recordingCallbackUrl);
      form.set("RecordingStatusCallbackMethod", "POST");
    }
    if (request.record) form.set("Record", "true");
    if (request.timeoutSec) form.set("Timeout", String(request.timeoutSec));
    if (request.machineDetection) form.set("MachineDetection", request.machineDetection);

    const body = await this.request("POST", this.accountPath("/Calls.json"), form);
    return {
      providerCallId: String(body.sid ?? ""),
      status: normalizeCallStatus(String(body.status ?? "queued")),
    };
  }

  async hangupCall(providerCallId: string): Promise<void> {
    const form = new URLSearchParams();
    form.set("Status", "completed");
    await this.request("POST", this.accountPath(`/Calls/${encodeURIComponent(providerCallId)}.json`), form);
  }

  async redirectCall(providerCallId: string, url: string): Promise<void> {
    const form = new URLSearchParams();
    form.set("Url", url);
    form.set("Method", "POST");
    await this.request("POST", this.accountPath(`/Calls/${encodeURIComponent(providerCallId)}.json`), form);
  }

  async startRecording(providerCallId: string): Promise<void> {
    await this.request(
      "POST",
      this.accountPath(`/Calls/${encodeURIComponent(providerCallId)}/Recordings.json`),
      new URLSearchParams(),
    );
  }

  async sendSms(request: SendSmsRequest): Promise<ProviderSms> {
    const form = new URLSearchParams();
    form.set("To", request.to);
    form.set("From", request.from);
    form.set("Body", request.body);
    if (request.statusCallbackUrl) form.set("StatusCallback", request.statusCallbackUrl);
    const body = await this.request("POST", this.accountPath("/Messages.json"), form);
    const status = String(body.status ?? "queued");
    return {
      providerMessageId: String(body.sid ?? ""),
      status: status === "sent" || status === "delivered" ? "sent" : "queued",
    };
  }

  /* ------------------------------------------------------------------ */
  /* Numbers                                                             */
  /* ------------------------------------------------------------------ */

  async searchNumbers(query: NumberSearchQuery): Promise<NumberOffer[]> {
    const country = (query.countryCode || "US").toUpperCase();
    const params = new URLSearchParams();
    if (query.areaCode) params.set("AreaCode", query.areaCode);
    if (query.contains) params.set("Contains", query.contains);
    if (query.smsCapable) params.set("SmsEnabled", "true");
    if (query.voiceCapable) params.set("VoiceEnabled", "true");
    params.set("PageSize", String(Math.min(Math.max(query.limit ?? 10, 1), 30)));

    const body = await this.request(
      "GET",
      this.accountPath(`/AvailablePhoneNumbers/${encodeURIComponent(country)}/Local.json?${params.toString()}`),
    );
    const available = Array.isArray(body.available_phone_numbers) ? body.available_phone_numbers : [];
    return available
      .map((entry) => {
        const record = asRecord(entry) ?? {};
        const capabilities = asRecord(record.capabilities) ?? {};
        return {
          e164: String(record.phone_number ?? ""),
          friendlyName: String(record.friendly_name ?? record.phone_number ?? ""),
          ...(record.locality ? { locality: String(record.locality) } : {}),
          ...(record.region ? { region: String(record.region) } : {}),
          ...(record.postal_code ? { postalCode: String(record.postal_code) } : {}),
          capabilities: (["voice", "sms", "mms"] as const).filter((name) => capabilities[name] === true),
          costNote:
            "Carrier charges apply. Omalla does not bill for numbers. Confirm the current monthly and usage price with the carrier before provisioning.",
        } satisfies NumberOffer;
      })
      .filter((offer) => offer.e164.startsWith("+"));
  }

  async provisionNumber(request: ProvisionNumberRequest): Promise<ProvisionedNumber> {
    const form = new URLSearchParams();
    form.set("PhoneNumber", request.e164);
    if (request.friendlyName) form.set("FriendlyName", request.friendlyName);
    if (request.voiceUrl) {
      form.set("VoiceUrl", request.voiceUrl);
      form.set("VoiceMethod", "POST");
    }
    if (request.smsUrl) {
      form.set("SmsUrl", request.smsUrl);
      form.set("SmsMethod", "POST");
    }
    if (request.statusCallbackUrl) form.set("StatusCallback", request.statusCallbackUrl);

    const body = await this.request("POST", this.accountPath("/IncomingPhoneNumbers.json"), form);
    const capabilities = asRecord(body.capabilities) ?? {};
    return {
      providerNumberId: String(body.sid ?? ""),
      e164: String(body.phone_number ?? request.e164),
      friendlyName: String(body.friendly_name ?? request.friendlyName ?? request.e164),
      capabilities: (["voice", "sms", "mms"] as const).filter((name) => capabilities[name] === true),
    };
  }

  async releaseNumber(providerNumberId: string): Promise<void> {
    await this.request(
      "DELETE",
      this.accountPath(`/IncomingPhoneNumbers/${encodeURIComponent(providerNumberId)}.json`),
    );
  }

  /* ------------------------------------------------------------------ */

  private accountPath(suffix: string): string {
    return `/2010-04-01/Accounts/${encodeURIComponent(this.accountSid)}${suffix}`;
  }

  private async request(
    method: "GET" | "POST" | "DELETE",
    path: string,
    form?: URLSearchParams,
  ): Promise<Record<string, unknown>> {
    const url = `${this.apiBaseUrl}${path}`;
    const headers: Record<string, string> = {
      authorization: `Basic ${Buffer.from(`${this.accountSid}:${this.authToken}`).toString("base64")}`,
      accept: "application/json",
    };
    let body: string | undefined;
    if (method === "POST" && form) {
      headers["content-type"] = "application/x-www-form-urlencoded";
      body = form.toString();
    }

    let response: Response;
    try {
      response = await this.fetchImpl(url, {
        method,
        headers,
        ...(body !== undefined ? { body } : {}),
        signal: AbortSignal.timeout(this.timeoutMs),
      });
    } catch (error) {
      throw new OmallaError(
        "provider_error",
        `${this.label} request failed before a response: ${(error as Error).message}`,
        502,
      );
    }

    if (response.status === 204) return {};
    const text = await response.text();
    let payload: Record<string, unknown> = {};
    if (text) {
      try {
        payload = JSON.parse(text) as Record<string, unknown>;
      } catch {
        payload = {};
      }
    }
    if (!response.ok) {
      const message =
        typeof payload.message === "string"
          ? payload.message
          : `HTTP ${response.status} from ${this.label}`;
      const code = payload.code !== undefined ? ` (code ${String(payload.code)})` : "";
      throw new OmallaError("provider_error", `${message}${code}`, 502);
    }
    return payload;
  }
}

function normalizeInboundStatus(raw: string | undefined): InboundCallEvent["status"] {
  const status = normalizeCallStatus(raw ?? "ringing");
  if (status === "in-progress") return "in-progress";
  if (status === "completed") return "completed";
  if (status === "failed" || status === "busy" || status === "no-answer" || status === "canceled") return "failed";
  return "ringing";
}

/** Candidate signed URLs: as received, plus with/without the standard port. */
function urlCandidates(url: string): string[] {
  const candidates = new Set<string>([url]);
  const match = /^(https?):\/\/([^/?#]+)([\s\S]*)$/i.exec(url);
  if (!match) return [...candidates];
  const scheme = match[1] ?? "https";
  const authority = match[2] ?? "";
  const rest = match[3] ?? "";
  const standard = scheme.toLowerCase() === "https" ? ":443" : ":80";
  const authorityLower = authority.toLowerCase();
  if (authorityLower.endsWith(standard)) {
    candidates.add(`${scheme}://${authority.slice(0, -standard.length)}${rest}`);
  } else if (!/:\d+$/.test(authority)) {
    candidates.add(`${scheme}://${authority}${standard}${rest}`);
  }
  return [...candidates];
}

function requiredField(form: Record<string, string>, name: string): string {
  const value = form[name];
  if (!value) throw new OmallaError("validation", `webhook is missing ${name}`, 400);
  return value;
}

function xmlResponse(body: string): ProviderHttpResponse {
  return { status: 200, contentType: "text/xml; charset=utf-8", body };
}

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function escapeXmlAttribute(value: string): string {
  return escapeXml(value).replace(/\r?\n/g, "&#10;");
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function stringRecord(value: unknown): Record<string, string> {
  const record = asRecord(value);
  if (!record) return {};
  const out: Record<string, string> = {};
  for (const [key, entry] of Object.entries(record)) {
    if (typeof entry === "string") out[key] = entry;
  }
  return out;
}

export type { CallStatus, CallStatusEvent };
