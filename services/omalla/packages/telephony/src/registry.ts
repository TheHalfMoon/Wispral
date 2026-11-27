import type { TelephonyProvider, TelephonyProviderId } from "./provider.js";
import { TELEPHONY_PROVIDER_IDS } from "./provider.js";
import { SimulatedTelephonyProvider } from "./providers/simulator.js";
import { SipTelephonyProvider } from "./providers/sip-provider.js";
import { TelnyxProvider } from "./providers/telnyx.js";
import { TwilioProvider } from "./providers/twilio.js";
import { VonageProvider } from "./providers/vonage.js";

export interface TelephonyRegistryOptions {
  env?: Record<string, string | undefined>;
  fetchImpl?: typeof fetch;
  /** Overrides the environment, mainly for tests. */
  providers?: TelephonyProvider[];
}

export interface ProviderAvailability {
  id: TelephonyProviderId;
  label: string;
  available: boolean;
  /** Why it is unavailable, or what has been verified. */
  detail: string;
  requiredEnv: string[];
}

/**
 * Provider selection is explicit.
 *
 * A carrier appears only when its credentials exist. The registry never falls
 * back from a misconfigured carrier to "pretend it worked": the default is the
 * simulator, and the API reports which provider actually handled a call.
 */
export class TelephonyRegistry {
  private readonly providers = new Map<TelephonyProviderId, TelephonyProvider>();
  private readonly defaultId: TelephonyProviderId;

  constructor(options: TelephonyRegistryOptions = {}) {
    const env = options.env ?? process.env;
    for (const provider of options.providers ?? []) {
      this.providers.set(provider.id, provider);
    }
    if (!this.providers.has("simulated")) {
      this.providers.set("simulated", new SimulatedTelephonyProvider());
    }

    if (!this.providers.has("twilio")) {
      const accountSid = env.TWILIO_ACCOUNT_SID?.trim();
      const authToken = env.TWILIO_AUTH_TOKEN?.trim();
      if (accountSid && authToken) {
        this.providers.set(
          "twilio",
          new TwilioProvider({
            accountSid,
            authToken,
            ...(env.TWILIO_API_BASE_URL ? { apiBaseUrl: env.TWILIO_API_BASE_URL } : {}),
            ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
          }),
        );
      }
    }

    if (!this.providers.has("signalwire")) {
      const space = env.SIGNALWIRE_SPACE_URL?.trim().replace(/^https?:\/\//, "").replace(/\/+$/, "");
      const projectId = env.SIGNALWIRE_PROJECT_ID?.trim();
      const token = env.SIGNALWIRE_TOKEN?.trim();
      if (space && projectId && token) {
        this.providers.set(
          "signalwire",
          new TwilioProvider({
            accountSid: projectId,
            authToken: token,
            apiBaseUrl: `https://${space}/api/laml`,
            variant: "signalwire",
            ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
          }),
        );
      }
    }

    if (!this.providers.has("telnyx")) {
      const apiKey = env.TELNYX_API_KEY?.trim();
      const connectionId = env.TELNYX_CONNECTION_ID?.trim();
      if (apiKey && connectionId) {
        this.providers.set(
          "telnyx",
          new TelnyxProvider({
            apiKey,
            connectionId,
            ...(env.TELNYX_PUBLIC_KEY ? { publicKey: env.TELNYX_PUBLIC_KEY } : {}),
            ...(env.TELNYX_WEBHOOK_SECRET ? { webhookSecret: env.TELNYX_WEBHOOK_SECRET } : {}),
            ...(env.TELNYX_API_BASE_URL ? { apiBaseUrl: env.TELNYX_API_BASE_URL } : {}),
            ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
          }),
        );
      }
    }

    if (!this.providers.has("vonage")) {
      const apiKey = env.VONAGE_API_KEY?.trim();
      const apiSecret = env.VONAGE_API_SECRET?.trim();
      const applicationId = env.VONAGE_APPLICATION_ID?.trim();
      if (apiKey && apiSecret && applicationId) {
        this.providers.set(
          "vonage",
          new VonageProvider({
            apiKey,
            apiSecret,
            applicationId,
            ...(env.VONAGE_SIGNATURE_SECRET ? { signatureSecret: env.VONAGE_SIGNATURE_SECRET } : {}),
            ...(env.VONAGE_API_BASE_URL ? { apiBaseUrl: env.VONAGE_API_BASE_URL } : {}),
            ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
          }),
        );
      }
    }

    if (!this.providers.has("sip")) {
      const gatewayUrl = env.OMALLA_SIP_GATEWAY_URL?.trim();
      if (gatewayUrl) {
        this.providers.set(
          "sip",
          new SipTelephonyProvider({
            gatewayUrl,
            ...(env.OMALLA_SIP_GATEWAY_TOKEN ? { gatewayToken: env.OMALLA_SIP_GATEWAY_TOKEN } : {}),
            attestedEncryptedTunnel: env.OMALLA_SIP_ATTESTED_TUNNEL === "1" || env.OMALLA_SIP_ATTESTED_TUNNEL === "true",
            ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
          }),
        );
      }
    }

    const requested = env.OMALLA_TELEPHONY_PROVIDER?.trim() as TelephonyProviderId | undefined;
    this.defaultId =
      requested && this.providers.has(requested) ? requested : ("simulated" as TelephonyProviderId);
  }

  get(id: string): TelephonyProvider {
    const provider = this.providers.get(id as TelephonyProviderId);
    if (!provider) {
      throw new Error(`telephony provider ${id} is not configured`);
    }
    return provider;
  }

  get default(): TelephonyProvider {
    return this.get(this.defaultId);
  }

  list(): TelephonyProvider[] {
    return [...this.providers.values()];
  }

  availability(env: Record<string, string | undefined> = process.env): ProviderAvailability[] {
    return TELEPHONY_PROVIDER_IDS.map((id) => {
      const provider = this.providers.get(id);
      if (provider) {
        return {
          id,
          label: provider.label,
          available: true,
          detail: provider.description.notes.join(" "),
          requiredEnv: requiredEnvFor(id),
        };
      }
      return {
        id,
        label: labelFor(id),
        available: false,
        detail: unavailableReason(id, env),
        requiredEnv: requiredEnvFor(id),
      };
    });
  }
}

function requiredEnvFor(id: TelephonyProviderId): string[] {
  switch (id) {
    case "simulated":
      return [];
    case "twilio":
      return ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"];
    case "signalwire":
      return ["SIGNALWIRE_SPACE_URL", "SIGNALWIRE_PROJECT_ID", "SIGNALWIRE_TOKEN"];
    case "telnyx":
      return ["TELNYX_API_KEY", "TELNYX_CONNECTION_ID"];
    case "vonage":
      return ["VONAGE_API_KEY", "VONAGE_API_SECRET", "VONAGE_APPLICATION_ID"];
    case "sip":
      return ["OMALLA_SIP_GATEWAY_URL"];
  }
}

function labelFor(id: TelephonyProviderId): string {
  switch (id) {
    case "twilio":
      return "Twilio Programmable Voice";
    case "signalwire":
      return "SignalWire (Twilio-compatible LaML)";
    case "telnyx":
      return "Telnyx Call Control";
    case "vonage":
      return "Vonage Voice API";
    case "sip":
      return "Self-hosted SIP gateway (Asterisk/FreeSWITCH/LiveKit/Jambonz)";
    case "simulated":
      return "Simulated carrier";
  }
}

function unavailableReason(id: TelephonyProviderId, env: Record<string, string | undefined>): string {
  if (id === "sip") {
    return env.OMALLA_SIP_GATEWAY_URL?.trim()
      ? "SIP gateway not configured"
      : "no gateway configured; set OMALLA_SIP_GATEWAY_URL or start the local SipStack";
  }
  const missing = requiredEnvFor(id).filter((name) => !env[name]?.trim());
  if (missing.length > 0) return `credentials missing: ${missing.join(", ")}`;
  return "not configured";
}
