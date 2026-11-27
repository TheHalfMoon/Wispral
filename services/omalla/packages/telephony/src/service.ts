import {
  newId,
  nowIso,
  OmallaError,
  evaluateOutboundPolicy,
  normalizeNumber,
  sanitizeUntrustedCallVariables,
} from "@omalla/core";
import type {
  Agent,
  Call,
  Database,
  EndedReason,
  IvrMenu,
  JsonValue,
  Logger,
  OutboundPolicyInput,
  PhoneNumber,
  Tenant,
} from "@omalla/core";
import { IvrSession, type IvrStep } from "./ivr.js";

/**
 * A live call leg.
 *
 * The transport is deliberately narrow: the simulated provider, a future SIP
 * bridge, and a browser WebRTC leg all satisfy the same four operations.
 */
export interface ConversationSession {
  start(): Promise<void>;
  handleCallerUtterance(text: string): Promise<void>;
  end(reason?: EndedReason): Promise<void>;
  readonly isEnded: boolean;
}

export interface CallHandle {
  call: Call;
  say(text: string): Promise<void>;
  press(digits: string): Promise<void>;
  hangup(reason?: EndedReason): Promise<void>;
  snapshot(): Call;
}

export interface TelephonyDeps {
  db: Database;
  logger: Logger;
  /** Builds the voice session for an answered call. */
  createSession: (call: Call, agent: Agent) => Promise<ConversationSession>;
  /** Plays IVR prompts through the call's audio path. */
  speak?: (call: Call, text: string) => Promise<void>;
  /** Fired once when a call reaches a terminal state. */
  onCallEnded?: (call: Call) => Promise<void>;
  now?: () => Date;
}

export interface InboundInput {
  to: string;
  from: string;
  /** Optional tenantId scope enforced on authenticated /v1/calls simulation (OM-T1). */
  tenantId?: string;
  /** Optional caller variables, e.g. a CRM lookup performed by the server. */
  variables?: Record<string, JsonValue>;
}

export interface OutboundInput {
  tenantId: string;
  to: string;
  agentId: string;
  from?: string;
  variables?: Record<string, JsonValue>;
  /** Explicit, recorded consent for this destination. */
  consent: boolean;
  callerId?: string;
}

interface ActiveCall {
  call: Call;
  session: ConversationSession | null;
  ivr: IvrSession | null;
  ended: boolean;
}

const SIMULATED_NUMBER = /^\+1(?:555)\d{7}$/;

/**
 * In-process telephony.
 *
 * Every call created here is simulated: audio never leaves the process and no
 * carrier is contacted. That is a hard product boundary, not a placeholder —
 * the UI labels simulated calls and the API reports `simulation: true`.
 */
export class TelephonyService {
  private readonly active = new Map<string, ActiveCall>();
  private readonly now: () => Date;

  constructor(private readonly deps: TelephonyDeps) {
    this.now = deps.now ?? (() => new Date());
  }

  async receiveInbound(input: InboundInput): Promise<CallHandle> {
    const to = normalizeNumber(input.to);
    const from = normalizeNumber(input.from);

    const number = this.findNumber(to);
    if (!number || (input.tenantId !== undefined && number.tenantId !== input.tenantId)) {
      throw new OmallaError("not_found", `no phone number configured for ${to}`, 404);
    }
    if (number.status !== "active") {
      throw new OmallaError("validation", `phone number ${to} is disabled`, 409);
    }
    if (!number.simulated) {
      throw new OmallaError(
        "provider_error",
        `number ${to} is provisioned with ${number.provider}; the carrier adapter is not implemented in v0.1.0`,
        501,
      );
    }

    const call = this.newCall({
      tenantId: number.tenantId,
      direction: "inbound",
      from,
      to,
      phoneNumberId: number.id,
      variables: sanitizeUntrustedCallVariables(input.variables ?? {}),
    });

    const active: ActiveCall = { call, session: null, ivr: null, ended: false };
    this.active.set(call.id, active);
    this.deps.db.col("calls").insert(call);

    const menu = number.ivrMenuId ? this.deps.db.col("ivrMenus").get(number.ivrMenuId) : undefined;
    if (menu) {
      active.ivr = new IvrSession(menu, (text) => this.speak(call, text));
      await active.ivr.start();
      this.recordIvrPrompt(call, menu.prompt);
    } else {
      const agent = this.resolveAgent(number.tenantId, number.inboundAgentId);
      await this.answer(call, agent);
    }

    return this.handle(active);
  }

  async placeOutbound(input: OutboundInput): Promise<CallHandle> {
    const tenant = this.deps.db.col("tenants").get(input.tenantId);
    if (!tenant) throw new OmallaError("not_found", "tenant not found", 404);

    const agent = this.resolveAgent(tenant.id, input.agentId);
    const to = normalizeNumber(input.to);
    const from = normalizeNumber(input.from ?? this.defaultFrom(tenant.id));
    const decision = evaluateOutboundPolicy(
      buildTenantOutboundPolicyInput(this.deps.db, tenant, {
        to,
        from,
        consentGranted: input.consent,
        now: this.now(),
      }),
    );

    if (!decision.allowed) {
      throw new OmallaError("blocked_by_policy", decision.reason ?? "outbound call blocked", 403);
    }

    const call = this.newCall({
      tenantId: tenant.id,
      direction: "outbound",
      from,
      to,
      variables: {
        ...sanitizeUntrustedCallVariables(input.variables ?? {}),
        consentGranted: true,
        consentAt: nowIso(),
      },
    });
    call.agentId = agent.id;
    call.agentVersion = agent.version;

    const active: ActiveCall = { call, session: null, ivr: null, ended: false };
    this.active.set(call.id, active);
    this.deps.db.col("calls").insert(call);
    await this.answer(call, agent);
    return this.handle(active);
  }

  get(callId: string): Call | undefined {
    return this.deps.db.col("calls").get(callId);
  }

  list(): Call[] {
    return this.deps.db.col("calls").list().sort((a, b) => b.startedAt.localeCompare(a.startedAt));
  }

  /* ------------------------------------------------------------------ */

  private handle(active: ActiveCall): CallHandle {
    return {
      call: active.call,
      say: async (text: string) => {
        if (active.ivr) {
          throw new OmallaError("validation", "this call is in an IVR menu; send DTMF digits instead", 409);
        }
        if (!active.session || active.session.isEnded) {
          throw new OmallaError("validation", "call is not connected", 409);
        }
        await active.session.handleCallerUtterance(text);
      },
      press: async (digits: string) => {
        if (!active.ivr) {
          throw new OmallaError("validation", "no IVR menu is attached to this call", 409);
        }
        active.call.metadata.lastDtmf = digits;
        const step: IvrStep = await active.ivr.feed(digits);
        if (step.kind === "prompt") {
          this.recordIvrPrompt(active.call, step.text);
          return;
        }
        await this.finishIvr(active, step.action, step.target);
      },
      hangup: async (reason: EndedReason = "customer_ended") => {
        await this.endCall(active, reason);
      },
      snapshot: () => structuredClone(active.call),
    };
  }

  private async finishIvr(active: ActiveCall, action: string, target?: string): Promise<void> {
    const { call } = active;
    active.ivr = null;
    switch (action) {
      case "hangup":
        await this.endCall(active, "customer_ended");
        return;
      case "voicemail":
        call.metadata.voicemailRequested = true;
        call.metadata.voicemailGreeting =
          "Please leave a message after the tone. Press hash when you are finished.";
        this.recordIvrPrompt(call, String(call.metadata.voicemailGreeting));
        return;
      case "transfer":
        call.metadata.transferDestination = target ?? null;
        call.metadata.transferMode = "blind";
        await this.endCall(active, "transfer");
        return;
      case "agent": {
        const agent = this.resolveAgent(call.tenantId, target);
        await this.answer(call, agent);
        return;
      }
      default:
        await this.endCall(active, "error");
    }
  }

  private async answer(call: Call, agent: Agent): Promise<void> {
    call.agentId = agent.id;
    call.agentVersion = agent.version;
    call.status = "in_progress";
    call.answeredAt = nowIso();

    const active = this.active.get(call.id);
    if (!active) throw new OmallaError("internal", "call is not active", 500);

    const session = await this.deps.createSession(call, agent);
    active.session = session;
    await session.start();
  }

  private async speak(call: Call, text: string): Promise<void> {
    if (this.deps.speak) {
      await this.deps.speak(call, text);
    }
  }

  private recordIvrPrompt(call: Call, text: string): void {
    call.transcript.push({
      id: newId("turn"),
      role: "assistant",
      text,
      at: nowIso(),
      offsetMs: Date.now() - Date.parse(call.startedAt),
    });
  }

  private async endCall(active: ActiveCall, reason: EndedReason): Promise<void> {
    if (active.ended) return;
    active.ended = true;
    const { call } = active;
    if (active.session && !active.session.isEnded) {
      await active.session.end(reason);
    }
    if (call.status !== "ended") {
      call.status = "ended";
      call.endedAt = nowIso();
      call.endedReason = reason;
    }
    this.active.delete(call.id);
    this.persist(call);
    try {
      await this.deps.onCallEnded?.(structuredClone(call));
    } catch (error) {
      this.deps.logger.error("post-call hook failed", {
        callId: call.id,
        error: (error as Error).message,
      });
    }
  }

  private persist(call: Call): void {
    const collection = this.deps.db.col("calls");
    try {
      collection.update(call.id, () => structuredClone(call));
    } catch {
      collection.insert(structuredClone(call));
    }
  }

  private newCall(input: {
    tenantId: string;
    direction: "inbound" | "outbound";
    from: string;
    to: string;
    phoneNumberId?: string;
    variables: Record<string, JsonValue>;
  }): Call {
    const now = nowIso();
    return {
      id: newId("call"),
      tenantId: input.tenantId,
      direction: input.direction,
      status: "ringing",
      from: input.from,
      to: input.to,
      ...(input.phoneNumberId ? { phoneNumberId: input.phoneNumberId } : {}),
      startedAt: now,
      transcript: [],
      messages: [],
      variables: input.variables,
      metadata: {},
      metrics: {
        turnCount: 0,
        turnLatenciesMs: [],
        totalTokensIn: 0,
        totalTokensOut: 0,
        toolCalls: 0,
        interruptions: 0,
      },
      simulation: true,
    };
  }

  private resolveAgent(tenantId: string, agentId: string | undefined): Agent {
    if (!agentId) {
      throw new OmallaError("validation", "no agent is attached to this number or call", 400);
    }
    const agent = this.deps.db.col("agents").get(agentId);
    if (!agent || agent.tenantId !== tenantId) {
      throw new OmallaError("not_found", `agent ${agentId} not found`, 404);
    }
    if (agent.status !== "published") {
      throw new OmallaError("validation", `agent ${agent.name} is not published`, 409);
    }
    return agent;
  }

  private findNumber(e164: string): PhoneNumber | undefined {
    return this.deps.db.col("phoneNumbers").list().find((number) => number.e164 === e164);
  }

  private defaultFrom(tenantId: string): string {
    const number = this.deps.db
      .col("phoneNumbers")
      .list()
      .find((candidate) => candidate.tenantId === tenantId && candidate.status === "active");
    return number?.e164 ?? "+15550000000";
  }
}

export function buildTenantOutboundPolicyInput(
  db: Database,
  tenant: Tenant,
  params: { to: string; from: string; consentGranted: boolean; now?: Date },
): OutboundPolicyInput {
  const now = params.now ?? new Date();
  const dayAgo = now.getTime() - 24 * 60 * 60 * 1000;
  const monthAgo = now.getTime() - 30 * 24 * 60 * 60 * 1000;

  const tenantCalls = db.col("calls").list((call) => call.tenantId === tenant.id);
  const outboundCalls = tenantCalls.filter((call) => call.direction === "outbound");
  const outboundSmsToday = db
    .col("smsMessages")
    .list(
      (msg) =>
        msg.tenantId === tenant.id &&
        msg.direction === "outbound" &&
        Date.parse(msg.createdAt) >= dayAgo,
    ).length;
  const callsToday =
    outboundCalls.filter((call) => Date.parse(call.startedAt) >= dayAgo).length + outboundSmsToday;
  const activeCalls = tenantCalls.filter(
    (call) => call.status === "queued" || call.status === "ringing" || call.status === "in_progress",
  ).length;

  const callDurationMinutes = (call: Call): number => {
    const metaSec = Number(call.metadata.providerDurationSec ?? 0);
    if (Number.isFinite(metaSec) && metaSec > 0) return metaSec / 60;
    if (call.answeredAt && call.endedAt) {
      const diffMs = Date.parse(call.endedAt) - Date.parse(call.answeredAt);
      if (Number.isFinite(diffMs) && diffMs > 0) return diffMs / 60_000;
    }
    return 0;
  };

  const minutesToday = outboundCalls
    .filter((call) => Date.parse(call.startedAt) >= dayAgo)
    .reduce((sum, call) => sum + callDurationMinutes(call), 0);
  const minutesThisMonth = outboundCalls
    .filter((call) => Date.parse(call.startedAt) >= monthAgo)
    .reduce((sum, call) => sum + callDurationMinutes(call), 0);

  const dncContacts = db
    .col("contacts")
    .list(
      (contact) =>
        contact.tenantId === tenant.id &&
        Boolean(contact.phone) &&
        (contact.tags.includes("dnc") || contact.attributes.dnc === true),
    )
    .map((contact) => contact.phone as string);

  const dncList = [...(tenant.settings.dncList ?? []), ...dncContacts];
  const window = parseWindow(tenant);

  return {
    to: params.to,
    from: params.from,
    tenant: {
      outboundEnabled: tenant.settings.outboundEnabled,
      outboundAllowlist: tenant.settings.outboundAllowlist,
      dncList,
      dailyOutboundCap: tenant.settings.dailyOutboundCap,
      ...(tenant.settings.maxConcurrentCalls !== undefined
        ? { maxConcurrentCalls: tenant.settings.maxConcurrentCalls }
        : {}),
      ...(tenant.settings.dailyMinuteQuota !== undefined
        ? { dailyMinuteQuota: tenant.settings.dailyMinuteQuota }
        : {}),
      ...(tenant.settings.monthlyMinuteQuota !== undefined
        ? { monthlyMinuteQuota: tenant.settings.monthlyMinuteQuota }
        : {}),
    },
    callsToday,
    activeCalls,
    minutesToday,
    minutesThisMonth,
    now,
    consentGranted: params.consentGranted,
    ...(window ? { callingWindow: window.window, timeZone: window.timeZone } : {}),
  };
}

function parseWindow(tenant: Tenant): {
  window: { start: string; end: string; days: number[] };
  timeZone: string;
} | null {
  if (tenant.settings.callingWindow) {
    return {
      window: tenant.settings.callingWindow,
      timeZone: tenant.settings.timezone,
    };
  }
  const raw = tenant.settings as unknown as Record<string, unknown>;
  const start = typeof raw.callingWindowStart === "string" ? raw.callingWindowStart : undefined;
  const end = typeof raw.callingWindowEnd === "string" ? raw.callingWindowEnd : undefined;
  if (!start || !end) return null;
  const days = Array.isArray(raw.callingDays) ? (raw.callingDays as number[]) : [1, 2, 3, 4, 5];
  return { window: { start, end, days }, timeZone: tenant.settings.timezone };
}

export function isSimulatedNumber(e164: string): boolean {
  return SIMULATED_NUMBER.test(e164);
}
