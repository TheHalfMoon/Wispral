import { createHash } from "node:crypto";
import type { FastifyInstance, FastifyReply, FastifyRequest } from "fastify";
import { z } from "zod";
import {
  OmallaError,
  evaluateOutboundPolicy,
  isE164,
  newId,
  normalizeNumber,
  nowIso,
} from "@omalla/core";
import type { JsonValue, PhoneNumber, Principal, SmsMessage } from "@omalla/core";
import type { WebhookRequest } from "@omalla/telephony";
import { buildTenantOutboundPolicyInput, isSimulatedNumber } from "@omalla/telephony";
import { executeIdempotent, extractIdempotencyKey } from "./app.js";
import type { OmallaRuntime } from "./runtime.js";

/**
 * Carrier-facing routes and the telephony control API.
 *
 * Public webhook routes authenticate with the carrier's signature, never with
 * an Omalla API key. Control routes live under /v1 and use the normal API key.
 * The simulated provider is not exposed on the public surface: it exists for
 * in-process calls only.
 */
export function registerTelephonyRoutes(app: FastifyInstance, runtime: OmallaRuntime): void {
  registerWebhooks(app, runtime);
  registerControlApi(app, runtime);
  registerMediaSocket(app, runtime);
}

/* ------------------------------------------------------------------ */
/* carrier webhooks                                                    */
/* ------------------------------------------------------------------ */

function registerWebhooks(app: FastifyInstance, runtime: OmallaRuntime): void {
  app.post("/telephony/:provider/voice", async (request, reply) => {
    const provider = carrierProvider(runtime, request);
    await verify(runtime, provider, request);

    const event = provider.parseInbound(webhookRequest(runtime, request));
    const number = runtime.db
      .col("phoneNumbers")
      .list((candidate) => candidate.e164 === normalizeNumber(event.to))[0];

    if (!number || number.status !== "active") {
      return send(reply, provider.renderInboundResponse({
        say: "This number is not configured to receive calls. Goodbye.",
        hangup: true,
      }));
    }

    const base = publicBase(runtime);
    const existingCallId = query(request, "callId");

    // Outbound: the answer URL carries the Omalla call id, signed by Twilio.
    if (existingCallId) {
      const call = runtime.db.col("calls").get(existingCallId);
      if (!call || call.tenantId !== number.tenantId) {
        return send(reply, provider.renderHangupResponse?.("This call could not be matched. Goodbye.") ?? provider.renderInboundResponse({ hangup: true }));
      }
      if (call.metadata.providerCallId === "pending") {
        runtime.bindProviderCall(call.id, event.providerCallId);
      }
      const agent = call.agentId ? runtime.db.col("agents").get(call.agentId) : undefined;
      if (!agent) {
        return send(reply, provider.renderInboundResponse({
          say: "The assistant is unavailable. Goodbye.",
          hangup: true,
        }));
      }
      call.status = "in_progress";
      call.answeredAt = call.answeredAt ?? nowIso();
      runtime.db.col("calls").update(call.id, call);
      return send(reply, voiceResponse(runtime, provider, call.id, agent));
    }

    // Inbound IVR: collect one digit, then branch in the DTMF handler.
    if (number.ivrMenuId) {
      const menu = runtime.db.col("ivrMenus").get(number.ivrMenuId);
      if (menu && menu.tenantId === number.tenantId) {
        const call = runtime.createCarrierCall({
          tenantId: number.tenantId,
          provider,
          direction: "inbound",
          from: event.from,
          to: event.to,
          providerCallId: event.providerCallId,
          phoneNumberId: number.id,
          answered: true,
          variables: { ivrMenuId: menu.id },
        });
        return send(reply, provider.renderInboundResponse({
          gather: {
            actionUrl: `${base}/telephony/${provider.id}/dtmf?callId=${encodeURIComponent(call.id)}&menuId=${encodeURIComponent(menu.id)}&attempt=0`,
            numDigits: 1,
            timeoutSec: menu.timeoutSec,
            prompt: menu.prompt,
          },
        }));
      }
    }

    const agent = resolveAgent(runtime, number.tenantId, query(request, "agentId") ?? number.inboundAgentId);
    const call = runtime.createCarrierCall({
      tenantId: number.tenantId,
      provider,
      direction: "inbound",
      from: event.from,
      to: event.to,
      providerCallId: event.providerCallId,
      phoneNumberId: number.id,
      agentId: agent.id,
      answered: true,
    });
    return send(reply, voiceResponse(runtime, provider, call.id, agent));
  });

  app.post("/telephony/:provider/dtmf", async (request, reply) => {
    const provider = carrierProvider(runtime, request);
    await verify(runtime, provider, request);
    if (!provider.parseDtmf) {
      throw new OmallaError("provider_error", `${provider.id} does not deliver DTMF`, 501);
    }

    const callId = query(request, "callId");
    const menuId = query(request, "menuId");
    const call = callId ? runtime.db.col("calls").get(callId) : undefined;
    if (!call || call.status === "ended") {
      return send(reply, provider.renderInboundResponse({ say: "Goodbye.", hangup: true }));
    }
    const menu = menuId ? runtime.db.col("ivrMenus").get(menuId) : undefined;
    if (!menu || menu.tenantId !== call.tenantId) {
      return send(reply, provider.renderInboundResponse({ say: "Goodbye.", hangup: true }));
    }

    const event = provider.parseDtmf(webhookRequest(runtime, request));
    const option = menu.options.find((candidate) => candidate.key === event.digits.charAt(0));
    const attempt = Number(query(request, "attempt") ?? "0") || 0;
    const base = publicBase(runtime);

    if (!option) {
      if (attempt + 1 >= Math.max(1, menu.maxAttempts)) {
        await runtime.updateCarrierStatus(call.metadata.providerCallId as string ?? "", "completed");
        return send(reply, provider.renderInboundResponse({ say: "Sorry, goodbye.", hangup: true }));
      }
      return send(reply, provider.renderInboundResponse({
        gather: {
          actionUrl: `${base}/telephony/${provider.id}/dtmf?callId=${encodeURIComponent(call.id)}&menuId=${encodeURIComponent(menu.id)}&attempt=${attempt + 1}`,
          numDigits: 1,
          timeoutSec: menu.timeoutSec,
          prompt: menu.invalidPrompt,
        },
      }));
    }

    if (option.action === "repeat") {
      return send(reply, provider.renderInboundResponse({
        gather: {
          actionUrl: `${base}/telephony/${provider.id}/dtmf?callId=${encodeURIComponent(call.id)}&menuId=${encodeURIComponent(menu.id)}&attempt=${attempt}`,
          numDigits: 1,
          timeoutSec: menu.timeoutSec,
          prompt: menu.prompt,
        },
      }));
    }

    if (option.action === "hangup") {
      call.status = "ended";
      call.endedAt = nowIso();
      call.endedReason = "customer_ended";
      runtime.db.col("calls").update(call.id, call);
      return send(reply, provider.renderInboundResponse({ say: "Goodbye.", hangup: true }));
    }

    if (option.action === "voicemail") {
      call.metadata.voicemailRequested = true;
      call.metadata.voicemailGreeting = "Please leave a message after the tone.";
      runtime.db.col("calls").update(call.id, call);
      return send(reply, provider.renderInboundResponse({
        voicemail: {
          greeting: String(call.metadata.voicemailGreeting),
          actionUrl: `${base}/telephony/${provider.id}/recording?callId=${encodeURIComponent(call.id)}&voicemail=1`,
          maxLengthSec: 120,
        },
      }));
    }

    if (option.action === "transfer") {
      call.metadata.transferDestination = option.target ?? null;
      call.metadata.transferMode = "blind";
      runtime.db.col("calls").update(call.id, call);
      return send(reply, provider.renderInboundResponse({
        say: "Please hold while I transfer you.",
        ...(option.target ? { dial: { to: option.target, timeoutSec: 30 } } : {}),
      }));
    }

    if (option.action === "agent") {
      const agent = resolveAgent(runtime, call.tenantId, option.target);
      call.agentId = agent.id;
      call.agentVersion = agent.version;
      call.status = "in_progress";
      call.answeredAt = call.answeredAt ?? nowIso();
      runtime.db.col("calls").update(call.id, call);
      return send(reply, voiceResponse(runtime, provider, call.id, agent));
    }

    return send(reply, provider.renderInboundResponse({ say: "Goodbye.", hangup: true }));
  });

  app.post("/telephony/:provider/status", async (request, reply) => {
    const provider = carrierProvider(runtime, request);
    await verify(runtime, provider, request);
    const event = provider.parseStatus(webhookRequest(runtime, request));
    await runtime.updateCarrierStatus(event.providerCallId, event.status, {
      ...(event.durationSec !== undefined ? { durationSec: event.durationSec } : {}),
      ...(event.error ? { error: event.error } : {}),
    });
    return reply.status(204).send();
  });

  app.post("/telephony/:provider/recording", async (request, reply) => {
    const provider = carrierProvider(runtime, request);
    await verify(runtime, provider, request);
    const form = webhookRequest(runtime, request).form;
    const callId = query(request, "callId");
    const call = callId ? runtime.db.col("calls").get(callId) : runtime.findCallByProviderId(form.CallSid ?? "");
    if (call) {
      const isVoicemail = query(request, "voicemail") === "1";
      call.recording = {
        enabled: true,
        consentAnnounced: Boolean(call.metadata.recordingConsentAnnounced),
        ...(form.RecordingUrl ? { url: form.RecordingUrl } : {}),
        ...(form.RecordingDuration
          ? { durationMs: Math.round(Number(form.RecordingDuration) * 1000) }
          : {}),
      };
      if (isVoicemail) {
        call.metadata.voicemailRecordingUrl = form.RecordingUrl ?? null;
        call.endedReason = "voicemail";
        call.status = "ended";
        call.endedAt = nowIso();
      }
      runtime.db.col("calls").update(call.id, call);
    }
    return reply.status(204).send();
  });

  app.post("/telephony/:provider/sms", async (request, reply) => {
    const provider = carrierProvider(runtime, request);
    await verify(runtime, provider, request);
    if (!provider.parseSms) {
      throw new OmallaError("provider_error", `${provider.id} does not deliver SMS`, 501);
    }
    const event = provider.parseSms(webhookRequest(runtime, request));
    const number = runtime.db
      .col("phoneNumbers")
      .list((candidate) => candidate.e164 === normalizeNumber(event.to))[0];
    if (number) {
      const message: SmsMessage = {
        id: newId("sms"),
        tenantId: number.tenantId,
        direction: "inbound",
        from: normalizeNumber(event.from),
        to: normalizeNumber(event.to),
        body: event.body.slice(0, 4000),
        provider: provider.id,
        providerMessageId: event.providerMessageId,
        status: "received",
        simulated: false,
        createdAt: nowIso(),
      };
      runtime.db.col("smsMessages").insert(message);
    }
    return reply.status(204).send();
  });
}

/* ------------------------------------------------------------------ */
/* media websocket                                                     */
/* ------------------------------------------------------------------ */

function registerMediaSocket(app: FastifyInstance, runtime: OmallaRuntime): void {
  app.get("/telephony/:provider/media", { websocket: true }, (socket, request) => {
    let providerId: string;
    try {
      providerId = carrierProvider(runtime, request).id;
    } catch {
      socket.close(4404, "provider not configured");
      return;
    }
    const callId = query(request, "callId");
    const token = query(request, "token") ?? "";
    if (!callId || !runtime.verifyMediaToken(callId, token)) {
      socket.close(4401, "invalid media token");
      return;
    }

    void runtime
      .openMediaSession(callId)
      .then(({ bridge }) => {
        bridge.attach(socket);
        socket.on("message", (data: unknown) => {
          const text = typeof data === "string" ? data : Buffer.from(data as Uint8Array).toString("utf8");
          bridge.handleMessage(text);
        });
        socket.on("close", () => {
          void bridge.handleClose();
        });
        socket.on("error", () => {
          void bridge.handleClose();
        });
        runtime.emitCallEvent(callId, "media.connected", { provider: providerId });
      })
      .catch((error: unknown) => {
        runtime.logger.warn("media session refused", {
          callId,
          error: (error as Error).message,
        });
        socket.close(4409, "media session unavailable");
      });
  });
}

/* ------------------------------------------------------------------ */
/* control API                                                         */
/* ------------------------------------------------------------------ */

const providerSchema = z.enum(["simulated", "twilio", "signalwire", "telnyx", "vonage", "sip"]);

function registerControlApi(app: FastifyInstance, runtime: OmallaRuntime): void {
  app.get("/v1/telephony/providers", async () => runtime.providerSummary());

  app.get("/v1/numbers", async (request) => {
    const principal = principalOf(request);
    return runtime.db
      .col("phoneNumbers")
      .list((number) => number.tenantId === principal.tenantId)
      .sort((a, b) => a.e164.localeCompare(b.e164));
  });

  app.post("/v1/numbers/search", async (request) => {
    const principal = principalOf(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        provider: providerSchema.default("simulated"),
        countryCode: z.string().length(2).default("US"),
        areaCode: z.string().regex(/^\d{3}$/).optional(),
        contains: z.string().max(16).optional(),
        limit: z.number().int().min(1).max(30).default(8),
      })
      .parse(request.body ?? {});
    const provider = controlProvider(runtime, body.provider);
    if (!provider.capabilities.numberProvisioning || !provider.searchNumbers) {
      throw new OmallaError("provider_error", `${provider.id} cannot search numbers`, 501);
    }
    const offers = await provider.searchNumbers(body);
    return {
      provider: provider.id,
      carrierCharges: provider.id !== "simulated",
      offers,
    };
  });

  app.post("/v1/numbers/provision", async (request, reply) => {
    const principal = principalOf(request);
    runtime.requireRole(principal, "owner");
    const body = z
      .object({
        provider: providerSchema.optional(),
        e164: z.string().min(8).max(20),
        label: z.string().max(120).optional(),
        agentId: z.string().optional(),
        ivrMenuId: z.string().optional(),
        /** Explicit acknowledgement of carrier charges. */
        confirm: z.literal(true),
      })
      .parse(request.body);
    const provider = controlProvider(runtime, body.provider ?? "simulated");
    if (body.agentId) assertAgent(runtime, principal.tenantId, body.agentId);
    if (body.ivrMenuId) {
      const menu = runtime.db.col("ivrMenus").get(body.ivrMenuId);
      if (!menu || menu.tenantId !== principal.tenantId) {
        throw new OmallaError("not_found", "IVR menu not found", 404);
      }
    }

    const e164 = normalizeNumber(body.e164);
    if (!isE164(e164)) throw new OmallaError("validation", "number is not valid E.164", 400);
    if (provider.id === "simulated") {
      if (!isSimulatedNumber(e164)) {
        throw new OmallaError(
          "validation",
          "simulated numbers must be in the +1 555 range; use a carrier provider for a real number",
          400,
        );
      }
      if (runtime.db.col("phoneNumbers").list((number) => number.e164 === e164).length > 0) {
        throw new OmallaError("validation", `number ${e164} is already configured`, 409);
      }
    } else {
      if (!runtime.config.allowCarrierPurchases) {
        throw new OmallaError(
          "forbidden",
          "carrier number purchases are disabled. Set OMALLA_ALLOW_CARRIER_PURCHASES=1 after reviewing carrier pricing and obtaining owner authorization.",
          403,
        );
      }
      if (!provider.capabilities.numberProvisioning || !provider.provisionNumber) {
        throw new OmallaError("provider_error", `${provider.id} cannot provision numbers`, 501);
      }
    }

    const base = publicBase(runtime);
    const provisioned = await provider.provisionNumber?.({
      e164,
      friendlyName: body.label,
      voiceUrl: `${base}/telephony/${provider.id}/voice`,
      smsUrl: `${base}/telephony/${provider.id}/sms`,
      statusCallbackUrl: `${base}/telephony/${provider.id}/status`,
    });

    const number: PhoneNumber = {
      id: newId("num"),
      tenantId: principal.tenantId,
      e164,
      label: body.label ?? `${provider.label} ${e164}`,
      provider: provider.id,
      ...(provisioned?.providerNumberId ? { providerNumberId: provisioned.providerNumberId } : {}),
      simulated: provider.id === "simulated",
      ...(body.agentId ? { inboundAgentId: body.agentId } : {}),
      ...(body.ivrMenuId ? { ivrMenuId: body.ivrMenuId } : {}),
      capabilities: ["voice", "sms", "dtmf"],
      createdAt: nowIso(),
      status: "active",
    };
    runtime.db.col("phoneNumbers").insert(number);
    audit(runtime, principal, "number.provision", number.id, "allowed");
    return reply.status(201).send({
      number,
      billing:
        provider.id === "simulated"
          ? { carrierCharges: false, note: "Simulated number. No carrier is contacted and nothing is billed." }
          : {
              carrierCharges: true,
              note: "The carrier bills this number monthly and per use. Omalla does not bill for telephony.",
            },
    });
  });

  app.delete("/v1/numbers/:id", async (request) => {
    const principal = principalOf(request);
    const number = runtime.db.col("phoneNumbers").get(param(request, "id"));
    if (!number || number.tenantId !== principal.tenantId) {
      throw new OmallaError("not_found", "number not found", 404);
    }
    runtime.requireRole(principal, number.simulated ? "admin" : "owner");
    if (query(request, "confirm") !== "true") {
      throw new OmallaError(
        "validation",
        "releasing a number requires confirm=true; carrier releases may be permanent",
        400,
      );
    }
    if (!number.simulated) {
      if (!runtime.config.allowCarrierPurchases) {
        throw new OmallaError(
          "forbidden",
          "carrier releases are disabled. Set OMALLA_ALLOW_CARRIER_PURCHASES=1 after owner authorization.",
          403,
        );
      }
      const provider = controlProvider(runtime, number.provider);
      if (!provider.releaseNumber || !number.providerNumberId) {
        throw new OmallaError("provider_error", `${number.provider} cannot release this number`, 501);
      }
      await provider.releaseNumber(number.providerNumberId);
    }
    runtime.db.col("phoneNumbers").remove(number.id);
    audit(runtime, principal, "number.release", number.id, "allowed");
    return { released: true, id: number.id, e164: number.e164 };
  });

  app.get("/v1/sms", async (request) => {
    const principal = principalOf(request);
    const queryParams = z
      .object({ direction: z.enum(["inbound", "outbound"]).optional(), limit: z.coerce.number().int().min(1).max(200).default(50) })
      .parse(request.query ?? {});
    return runtime.db
      .col("smsMessages")
      .list(
        (message) =>
          message.tenantId === principal.tenantId &&
          (!queryParams.direction || message.direction === queryParams.direction),
      )
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
      .slice(0, queryParams.limit);
  });

  app.post("/v1/sms", async (request, reply) => {
    const principal = principalOf(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        to: z.string().min(4),
        from: z.string().optional(),
        body: z.string().min(1).max(1600),
        provider: providerSchema.optional(),
        consent: z.boolean(),
      })
      .parse(request.body);

    const idemKey = extractIdempotencyKey(request);
    return executeIdempotent(
      runtime,
      request,
      reply,
      { tenantId: principal.tenantId, scope: "sms.send", idemKey, payload: body },
      async () => {
        const tenant = runtime.db.col("tenants").get(principal.tenantId);
        if (!tenant) throw new OmallaError("not_found", "tenant not found", 404);
        if (!body.consent) {
          throw new OmallaError("blocked_by_policy", "sending SMS requires recorded consent", 403);
        }
        if (!tenant.settings.outboundEnabled) {
          throw new OmallaError("blocked_by_policy", "outbound messaging is disabled for this tenant", 403);
        }
        const to = normalizeNumber(body.to);
        if (!isE164(to)) throw new OmallaError("validation", "destination is not valid E.164", 400);
        const dncList = (tenant.settings.dncList ?? []).map((n) => normalizeNumber(n));
        if (dncList.includes(to)) {
          throw new OmallaError("blocked_by_policy", "destination is on the Do-Not-Call (DNC) list", 403);
        }
        const allowlist = tenant.settings.outboundAllowlist;
        if (allowlist.length > 0 && !allowlist.map((n) => normalizeNumber(n)).includes(to)) {
          throw new OmallaError("blocked_by_policy", "destination is not on the tenant outbound allowlist", 403);
        }

        const from = body.from ? normalizeNumber(body.from) : undefined;
        const number = from
          ? runtime.db
              .col("phoneNumbers")
              .list((candidate) => candidate.tenantId === principal.tenantId && candidate.e164 === from)[0]
          : runtime.db
              .col("phoneNumbers")
              .list((candidate) => candidate.tenantId === principal.tenantId && candidate.status === "active")[0];
        const provider = controlProvider(runtime, body.provider ?? number?.provider ?? "simulated");
        if (!provider.capabilities.sms || !provider.sendSms) {
          throw new OmallaError("provider_error", `${provider.id} cannot send SMS`, 501);
        }
        if (!number && provider.id !== "simulated") {
          throw new OmallaError("validation", `no ${provider.id} number is configured to send from`, 400);
        }

        const effectiveFrom = number?.e164 ?? from ?? "+15550000000";
        const decision = evaluateOutboundPolicy(
          buildTenantOutboundPolicyInput(runtime.db, tenant, {
            to,
            from: effectiveFrom,
            consentGranted: body.consent,
            now: new Date(),
          }),
        );
        if (!decision.allowed) {
          throw new OmallaError("blocked_by_policy", decision.reason ?? "outbound SMS blocked", 403);
        }

        const result = await provider.sendSms({
          to,
          from: effectiveFrom,
          body: body.body,
          ...(provider.id !== "simulated"
            ? { statusCallbackUrl: `${publicBase(runtime)}/telephony/${provider.id}/sms` }
            : {}),
        });
        const message: SmsMessage = {
          id: newId("sms"),
          tenantId: principal.tenantId,
          direction: "outbound",
          from: effectiveFrom,
          to,
          body: body.body,
          provider: provider.id,
          providerMessageId: result.providerMessageId,
          status: result.status,
          simulated: provider.id === "simulated",
          createdAt: nowIso(),
        };
        runtime.db.col("smsMessages").insert(message);
        audit(runtime, principal, "sms.send", message.id, "allowed");
        return { statusCode: 201, body: message };
      },
    );
  });
}

/* ------------------------------------------------------------------ */
/* helpers                                                             */
/* ------------------------------------------------------------------ */

function carrierProvider(runtime: OmallaRuntime, request: FastifyRequest) {
  const id = String((request.params as Record<string, string | undefined>).provider ?? "");
  if (id === "simulated") {
    throw new OmallaError("not_found", "the simulated provider has no public webhook surface", 404);
  }
  try {
    const provider = runtime.telephonyProviders.get(id);
    return provider;
  } catch {
    throw new OmallaError("not_found", `telephony provider ${id} is not configured`, 404);
  }
}

function controlProvider(runtime: OmallaRuntime, id: string) {
  try {
    return runtime.telephonyProviders.get(id);
  } catch {
    throw new OmallaError("not_found", `telephony provider ${id} is not configured`, 404);
  }
}

async function verify(
  runtime: OmallaRuntime,
  provider: ReturnType<typeof carrierProvider>,
  request: FastifyRequest,
): Promise<void> {
  const whReq = webhookRequest(runtime, request);
  const result = await provider.verifyWebhook(whReq);
  if (!result.valid) {
    throw new OmallaError("unauthorized", result.reason ?? "invalid carrier signature", 403);
  }
  const sigHeader =
    whReq.headers["x-twilio-signature"] ??
    whReq.headers["x-signalwire-signature"] ??
    whReq.headers["telnyx-signature-ed25519"] ??
    whReq.headers["x-telnyx-signature-hmac-sha256"] ??
    whReq.headers["x-telnyx-signature"] ??
    whReq.headers["authorization"] ??
    whReq.headers["x-omalla-gateway-token"] ??
    "";
  const bodyBytes =
    whReq.rawBody ??
    Buffer.from(
      whReq.json ? JSON.stringify(whReq.json) : new URLSearchParams(whReq.form).toString(),
      "utf8",
    );
  const bodyDigest = createHash("sha256").update(bodyBytes).digest("hex");
  const eventKey = createHash("sha256")
    .update(`${provider.id}:${sigHeader}:${whReq.url}:${bodyDigest}`, "utf8")
    .digest("hex");
  const fresh = runtime.replayCache.claimEvent("carrier", `carrier:${provider.id}`, eventKey);
  if (!fresh) {
    throw new OmallaError("conflict", "replayed carrier webhook event rejected (OM-T3)", 409);
  }
}

function webhookRequest(runtime: OmallaRuntime, request: FastifyRequest): WebhookRequest {
  const headers: Record<string, string> = {};
  for (const [key, value] of Object.entries(request.headers)) {
    if (typeof value === "string") headers[key.toLowerCase()] = value;
    else if (Array.isArray(value)) headers[key.toLowerCase()] = value.join(", ");
  }
  const form: Record<string, string> = {};
  const body = request.body;
  let jsonBody: Record<string, unknown> | undefined;
  if (body && typeof body === "object" && !Array.isArray(body)) {
    jsonBody = body as Record<string, unknown>;
    for (const [key, value] of Object.entries(jsonBody)) {
      if (value === undefined || value === null) continue;
      if (typeof value === "object") continue;
      form[key] = Array.isArray(value) ? value.map(String).join(",") : String(value);
    }
  }
  const raw = request.raw.url ?? "/";
  return {
    url: `${publicBase(runtime)}${raw.startsWith("/") ? raw : `/${raw}`}`,
    method: request.method,
    headers,
    form,
    ...(request.rawBody ? { rawBody: request.rawBody } : {}),
    ...(jsonBody ? { json: jsonBody } : {}),
  };
}

function voiceResponse(
  runtime: OmallaRuntime,
  provider: ReturnType<typeof carrierProvider>,
  callId: string,
  agent: { id: string; config: { recording: { enabled: boolean; consentAnnouncement: boolean } } },
) {
  const base = publicBase(runtime);
  const ws = base.replace(/^http/i, "ws");
  const consent =
    agent.config.recording.enabled && agent.config.recording.consentAnnouncement
      ? "This call may be recorded for quality and training purposes."
      : undefined;
  if (consent) {
    const call = runtime.db.col("calls").get(callId);
    if (call) {
      call.metadata.recordingConsentAnnounced = true;
      runtime.db.col("calls").update(callId, call);
    }
  }
  return provider.renderInboundResponse({
    ...(consent ? { say: consent } : {}),
    ...(agent.config.recording.enabled
      ? { startRecording: { statusCallbackUrl: `${base}/telephony/${provider.id}/recording`, channels: "mono" as const } }
      : {}),
    mediaStreamUrl: `${ws}/telephony/${provider.id}/media?callId=${encodeURIComponent(callId)}&token=${encodeURIComponent(runtime.issueMediaToken(callId))}`,
    parameters: { callId },
    closingSay: "Goodbye.",
  });
}

function resolveAgent(
  runtime: OmallaRuntime,
  tenantId: string,
  agentId: string | undefined,
) {
  if (!agentId) {
    throw new OmallaError("validation", "no agent is attached to this number", 400);
  }
  const agent = runtime.db.col("agents").get(agentId);
  if (!agent || agent.tenantId !== tenantId) {
    throw new OmallaError("not_found", `agent ${agentId} not found`, 404);
  }
  if (agent.status !== "published") {
    throw new OmallaError("validation", `agent ${agent.name} is not published`, 409);
  }
  return agent;
}

function assertAgent(runtime: OmallaRuntime, tenantId: string, agentId: string): void {
  resolveAgent(runtime, tenantId, agentId);
}

function publicBase(runtime: OmallaRuntime): string {
  return runtime.config.publicBaseUrl.replace(/\/+$/, "");
}

function send(reply: FastifyReply, response: { status: number; contentType: string; body: string }): FastifyReply {
  return reply.status(response.status).type(response.contentType).send(response.body);
}

function query(request: FastifyRequest, name: string): string | undefined {
  const value = (request.query as Record<string, unknown> | undefined)?.[name];
  if (Array.isArray(value)) return value[0] === undefined ? undefined : String(value[0]);
  return value === undefined || value === null ? undefined : String(value);
}

function param(request: FastifyRequest, name: string): string {
  const value = (request.params as Record<string, string | undefined>)[name];
  if (!value) throw new OmallaError("validation", `missing ${name}`, 400);
  return value;
}

function principalOf(request: FastifyRequest): Principal {
  if (!request.principal) throw new OmallaError("unauthorized", "missing API key", 401);
  return request.principal;
}

function audit(
  runtime: OmallaRuntime,
  principal: Principal,
  action: string,
  target: string,
  outcome: "allowed" | "denied",
): void {
  runtime.db.col("auditEvents").insert({
    id: newId("aud"),
    tenantId: principal.tenantId,
    actor: principal.apiKeyId ?? principal.userId ?? "system",
    action,
    target,
    outcome,
    at: nowIso(),
  });
}

export type { JsonValue };
