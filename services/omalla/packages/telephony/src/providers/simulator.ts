import { newId } from "@omalla/core";
import type {
  CallStatusEvent,
  CreateCallRequest,
  InboundCallEvent,
  InboundResponseOptions,
  NumberOffer,
  NumberSearchQuery,
  ProviderHttpResponse,
  ProviderSms,
  ProvisionNumberRequest,
  ProvisionedNumber,
  SendSmsRequest,
  TelephonyCapabilities,
  TelephonyProvider,
  TelephonyProviderId,
  WebhookRequest,
  WebhookVerification,
} from "../provider.js";
import { normalizeCallStatus } from "../provider.js";

const CAPABILITIES: TelephonyCapabilities = {
  voice: true,
  mediaStream: "none",
  sms: true,
  dtmf: true,
  transfer: true,
  recording: false,
  numberProvisioning: true,
  signedWebhooks: false,
  sip: false,
};

/**
 * In-process carrier.
 *
 * Calls and SMS never leave the machine, cost nothing, and are labelled
 * `simulated` everywhere. The provider exists so the rest of the platform can
 * be developed and qualified without a carrier account.
 */
export class SimulatedTelephonyProvider implements TelephonyProvider {
  readonly id: TelephonyProviderId = "simulated";
  readonly label = "Simulated carrier (no network, no cost)";
  readonly capabilities = CAPABILITIES;
  readonly description = {
    id: this.id,
    label: this.label,
    capabilities: CAPABILITIES,
    pstn: false,
    verification: "simulated" as const,
    notes: [
      "Audio and messages stay in the Omalla process.",
      "There is no PSTN path and no carrier charge.",
    ],
  };

  verifyWebhook(_request: WebhookRequest): WebhookVerification {
    return { valid: true, reason: "simulated provider: no transport signature exists" };
  }

  parseInbound(request: WebhookRequest): InboundCallEvent {
    const form = request.form;
    return {
      providerCallId: form.CallSid ?? newId("simcall"),
      from: form.From ?? "+15550009999",
      to: form.To ?? "+15550001234",
      direction: "inbound",
      status: "ringing",
      raw: { ...form },
    };
  }

  parseStatus(request: WebhookRequest): CallStatusEvent {
    return {
      providerCallId: request.form.CallSid ?? "unknown",
      status: normalizeCallStatus(request.form.CallStatus ?? "completed"),
    };
  }

  renderInboundResponse(options: InboundResponseOptions): ProviderHttpResponse {
    return {
      status: 200,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify({
        simulated: true,
        say: options.say ?? null,
        gather: options.gather ?? null,
        mediaStream: false,
        hangup: options.hangup ?? false,
      }),
    };
  }

  renderHangupResponse(text?: string): ProviderHttpResponse {
    return this.renderInboundResponse({ ...(text ? { say: text } : {}), hangup: true });
  }

  async createCall(request: CreateCallRequest): Promise<{ providerCallId: string; status: "queued" }> {
    return { providerCallId: newId("simcall"), status: "queued" };
  }

  async sendSms(request: SendSmsRequest): Promise<ProviderSms> {
    return { providerMessageId: newId("simsms"), status: "queued" };
  }

  async searchNumbers(query: NumberSearchQuery): Promise<NumberOffer[]> {
    const limit = Math.min(Math.max(query.limit ?? 5, 1), 20);
    const base = 2_000_000 + Math.floor(Math.random() * 6_000_000);
    return Array.from({ length: limit }, (_, index) => ({
      e164: `+1555${String(base + index).padStart(7, "0")}`,
      friendlyName: `Simulated number ${index + 1}`,
      locality: "Simulated",
      region: query.countryCode || "US",
      capabilities: ["voice", "sms"] as Array<"voice" | "sms" | "mms">,
      costNote: "Simulated numbers are free and never connect to the public telephone network.",
    }));
  }

  async provisionNumber(request: ProvisionNumberRequest): Promise<ProvisionedNumber> {
    return {
      providerNumberId: newId("simnum"),
      e164: request.e164,
      friendlyName: request.friendlyName ?? `Simulated ${request.e164}`,
      capabilities: ["voice", "sms"],
    };
  }

  async releaseNumber(_providerNumberId: string): Promise<void> {
    // Nothing external to release.
  }
}
