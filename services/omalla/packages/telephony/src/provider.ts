/**
 * Carrier-neutral telephony contract.
 *
 * A provider translates one carrier's wire protocol into the small set of
 * events Omalla understands. The simulated provider is the default; carrier
 * adapters are control-plane complete and mark any capability they do not
 * implement instead of pretending to support it.
 */

export const TELEPHONY_PROVIDER_IDS = [
  "simulated",
  "twilio",
  "signalwire",
  "telnyx",
  "vonage",
  "sip",
] as const;

export type TelephonyProviderId = (typeof TELEPHONY_PROVIDER_IDS)[number];

export interface TelephonyCapabilities {
  readonly voice: boolean;
  /** none: no audio path, unidirectional: carrier -> Omalla, bidirectional: both ways. */
  readonly mediaStream: "none" | "unidirectional" | "bidirectional";
  readonly sms: boolean;
  readonly dtmf: boolean;
  readonly transfer: boolean;
  readonly recording: boolean;
  readonly numberProvisioning: boolean;
  readonly signedWebhooks: boolean;
  /** Native SIP interop (trunking or a self-hosted gateway). */
  readonly sip: boolean;
}

export interface ProviderHttpResponse {
  status: number;
  contentType: string;
  body: string;
  headers?: Record<string, string>;
}

/** A webhook exactly as the carrier delivered it. */
export interface WebhookRequest {
  /**
   * The absolute public URL the carrier signed. Behind a proxy this must be
   * reconstructed from OMALLA_PUBLIC_URL, never from the raw socket.
   */
  url: string;
  method: string;
  headers: Record<string, string>;
  /** Flattened form fields. Twilio signs the decoded form, not the raw body. */
  form: Record<string, string>;
  /** Exact raw wire bytes for raw-byte HMAC/Ed25519 verifiers (Telnyx, Vonage, Standard Webhooks). */
  rawBody?: Uint8Array;
  /** Parsed JSON object when the carrier posts application/json. */
  json?: Record<string, unknown>;
}

export interface WebhookVerification {
  valid: boolean;
  reason?: string;
}

export type InboundCallStatus = "ringing" | "in-progress" | "completed" | "failed";

export interface InboundCallEvent {
  providerCallId: string;
  from: string;
  to: string;
  direction: "inbound" | "outbound";
  status?: InboundCallStatus;
  /** Carrier-specific fields retained for audit, never trusted for policy. */
  raw?: Record<string, string>;
}

export type CallStatus =
  | "queued"
  | "initiated"
  | "ringing"
  | "in-progress"
  | "completed"
  | "busy"
  | "failed"
  | "no-answer"
  | "canceled";

export interface CallStatusEvent {
  providerCallId: string;
  status: CallStatus;
  from?: string;
  to?: string;
  durationSec?: number;
  error?: string;
}

export interface DtmfEvent {
  providerCallId: string;
  digits: string;
}

export interface RecordingEvent {
  providerCallId: string;
  recordingId: string;
  status: "in-progress" | "completed" | "failed";
  url?: string;
  durationMs?: number;
}

export interface SmsEvent {
  providerMessageId: string;
  from: string;
  to: string;
  body: string;
  status: "received" | "sent" | "delivered" | "failed";
  error?: string;
}

export interface MediaStreamFormat {
  encoding: "audio/x-mulaw" | "audio/pcm" | "audio/l16";
  sampleRate: number;
  channels: number;
}

/** Normalised Media Streams frame. Providers with a different protocol adapt to this. */
export type MediaStreamEvent =
  | { type: "connected" }
  | {
      type: "start";
      streamId: string;
      callId: string;
      format: MediaStreamFormat;
      parameters: Record<string, string>;
    }
  | { type: "media"; track: "inbound" | "outbound"; payload: string; timestamp?: string }
  | { type: "dtmf"; digit: string }
  | { type: "mark"; name: string }
  | { type: "stop" }
  | { type: "unknown"; raw: string };

export interface InboundResponseOptions {
  /** WebSocket URL the carrier should stream audio to. */
  mediaStreamUrl?: string;
  /** Values echoed back in the stream `start` message. */
  parameters?: Record<string, string>;
  /** Spoken before connecting or gathering. */
  say?: string;
  /** Ask the caller for DTMF/speech and POST the result to `actionUrl`. */
  gather?: {
    actionUrl: string;
    numDigits?: number;
    timeoutSec?: number;
    input?: "dtmf" | "speech" | "dtmf speech";
    prompt?: string;
  };
  /** End the call after the response executes. */
  hangup?: boolean;
  /** Play this text when the media stream closes without a goodbye. */
  closingSay?: string;
  /** Start carrier-side recording before connecting audio. */
  startRecording?: {
    statusCallbackUrl: string;
    /** Twilio records both legs by default; mono is cheaper and sufficient here. */
    channels?: "mono" | "dual";
  };
  /** Blind transfer to a PSTN number or SIP URI. */
  dial?: {
    to: string;
    timeoutSec?: number;
    callerId?: string;
  };
  /** Record a voicemail message and POST its metadata to `actionUrl`. */
  voicemail?: {
    greeting: string;
    actionUrl: string;
    maxLengthSec?: number;
  };
}

export interface CreateCallRequest {
  to: string;
  from: string;
  /** Webhook that returns the initial TwiML/XML document. */
  answerUrl: string;
  statusCallbackUrl?: string;
  recordingCallbackUrl?: string;
  /** Ask the carrier to begin recording when answered (consent is the caller's duty). */
  record?: boolean;
  timeoutSec?: number;
  machineDetection?: "enable" | "detect-message-end";
}

export interface ProviderCall {
  providerCallId: string;
  status: CallStatus;
}

export interface SendSmsRequest {
  to: string;
  from: string;
  body: string;
  statusCallbackUrl?: string;
}

export interface ProviderSms {
  providerMessageId: string;
  status: "queued" | "sent";
}

export interface NumberSearchQuery {
  countryCode: string;
  areaCode?: string;
  contains?: string;
  limit?: number;
  smsCapable?: boolean;
  voiceCapable?: boolean;
}

export interface NumberOffer {
  e164: string;
  friendlyName: string;
  locality?: string;
  region?: string;
  postalCode?: string;
  capabilities: Array<"voice" | "sms" | "mms">;
  /** Never invented: carriers price numbers on their own schedule. */
  costNote: string;
}

export interface ProvisionNumberRequest {
  e164: string;
  friendlyName?: string;
  voiceUrl?: string;
  smsUrl?: string;
  statusCallbackUrl?: string;
}

export interface ProvisionedNumber {
  providerNumberId: string;
  e164: string;
  friendlyName: string;
  capabilities: Array<"voice" | "sms" | "mms">;
}

export interface ProviderDescription {
  id: TelephonyProviderId;
  label: string;
  capabilities: TelephonyCapabilities;
  /** True when the provider can place calls to the public telephone network. */
  pstn: boolean;
  /** What has actually been exercised. Live carrier calls are never implied. */
  verification: "simulated" | "unit-tested" | "live-tested";
  notes: string[];
}

/**
 * The carrier contract.
 *
 * Optional methods correspond to optional capabilities: a provider that says
 * `sms: false` also omits `sendSms`. Callers must check capabilities first.
 */
export interface TelephonyProvider {
  readonly id: TelephonyProviderId;
  readonly label: string;
  readonly capabilities: TelephonyCapabilities;
  readonly description: ProviderDescription;

  verifyWebhook(request: WebhookRequest): Promise<WebhookVerification> | WebhookVerification;
  parseInbound(request: WebhookRequest): InboundCallEvent;
  parseStatus(request: WebhookRequest): CallStatusEvent;
  parseDtmf?(request: WebhookRequest): DtmfEvent;
  parseRecordingStatus?(request: WebhookRequest): RecordingEvent;
  parseSms?(request: WebhookRequest): SmsEvent;
  parseMediaMessage?(raw: string): MediaStreamEvent;
  /** Frames Omalla sends into the carrier's media socket. */
  encodeMediaFrame?(streamId: string, payloadBase64: string): string;
  encodeClearFrame?(streamId: string): string;
  encodeMarkFrame?(streamId: string, name: string): string;

  /** XML or JSON the carrier executes in response to an inbound call. */
  renderInboundResponse(options: InboundResponseOptions): ProviderHttpResponse;
  renderHangupResponse?(text?: string): ProviderHttpResponse;

  createCall?(request: CreateCallRequest): Promise<ProviderCall>;
  hangupCall?(providerCallId: string): Promise<void>;
  /** Redirects a live call to new instructions (warm or blind transfer). */
  redirectCall?(providerCallId: string, url: string): Promise<void>;
  startRecording?(providerCallId: string): Promise<void>;
  stopRecording?(providerCallId: string): Promise<void>;

  sendSms?(request: SendSmsRequest): Promise<ProviderSms>;
  searchNumbers?(query: NumberSearchQuery): Promise<NumberOffer[]>;
  provisionNumber?(request: ProvisionNumberRequest): Promise<ProvisionedNumber>;
  releaseNumber?(providerNumberId: string): Promise<void>;
}

/** Error raised when a provider is asked for a capability it does not have. */
export class TelephonyCapabilityError extends Error {
  constructor(
    readonly provider: TelephonyProviderId,
    readonly capability: keyof TelephonyCapabilities,
  ) {
    super(`${provider} does not support ${capability} in this build`);
    this.name = "TelephonyCapabilityError";
  }
}

export function requireCapability(
  provider: TelephonyProvider,
  capability: keyof TelephonyCapabilities,
): void {
  const value = provider.capabilities[capability];
  const supported = typeof value === "boolean" ? value : value !== "none";
  if (!supported) throw new TelephonyCapabilityError(provider.id, capability);
}

/** Maps a carrier status string to the canonical set. Unknown values fail closed. */
export function normalizeCallStatus(raw: string): CallStatus {
  switch (raw.trim().toLowerCase()) {
    case "queued":
      return "queued";
    case "initiated":
      return "initiated";
    case "ringing":
      return "ringing";
    case "in-progress":
    case "in_progress":
    case "answered":
      return "in-progress";
    case "completed":
      return "completed";
    case "busy":
      return "busy";
    case "no-answer":
    case "no_answer":
      return "no-answer";
    case "canceled":
    case "cancelled":
      return "canceled";
    default:
      return "failed";
  }
}
