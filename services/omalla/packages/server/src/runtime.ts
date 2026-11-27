import { mkdir, writeFile } from "node:fs/promises";
import { timingSafeEqual } from "node:crypto";
import path from "node:path";
import {
  ConversationEngine,
  Database,
  Emitter,
  OmallaError,
  SecretBox,
  createLogger,
  createRetriever,
  evaluateOutboundPolicy,
  hashToken,
  isE164,
  newId,
  newToken,
  normalizeNumber,
  nowIso,
  sanitizeUntrustedCallVariables,
} from "@omalla/core";
import type {
  Agent,
  AgentConfig,
  AgentVersion,
  ApiKey,
  Call,
  EndedReason,
  EvaluationCase,
  JsonValue,
  Logger,
  Principal,
  SmsMessage,
  SttProvider,
  Tenant,
  ToolDefinition,
  Workflow,
  WorkflowRun,
  WorkflowVersion,
} from "@omalla/core";
import { resolveProviders } from "@omalla/providers";
import {
  TEMPLATES,
  WorkflowEngine,
  buildTemplate,
  exportN8nWorkflow,
  importN8nWorkflow,
  type TemplateId,
  type WorkflowServices,
} from "@omalla/workflow";
import {
  ConversationVoiceEngine,
  MediaBridge,
  TelephonyRegistry,
  TelephonyService,
  buildTenantOutboundPolicyInput,
  requireCapability,
  type CallHandle,
  type ConversationSession,
  type TelephonyProvider,
} from "@omalla/telephony";
import type { OmallaConfig } from "./config.js";
import { CredentialService } from "./credentials.js";
import { LocalAutomationStore } from "./automation-store.js";
import { SqliteIdempotencyManager } from "./idempotency.js";
import { createSsrfGuardedFetch, type DnsLookupAll } from "./ssrf-guard.js";
import { ToolRuntime } from "./tools.js";
import { WebhookReplayCache } from "./webhooks.js";

export interface CallEvent {
  callId: string;
  type: string;
  at: string;
  data: JsonValue;
}

interface RuntimeEvents {
  call: CallEvent;
}

export interface RuntimeOptions {
  logger?: Logger;
  /** Force mock providers; used by tests and CI. */
  offlineProviders?: boolean;
  fetchImpl?: typeof fetch;
  dnsLookup?: DnsLookupAll;
  /** Tests inject a registry so carrier adapters run without environment variables. */
  telephonyRegistry?: TelephonyRegistry;
}

export interface AgentTestInput {
  callerTurns: string[];
  variables?: Record<string, JsonValue>;
  version?: number;
  compareVersion?: number;
  expectations?: EvaluationCase["expectations"];
}

export interface AgentTestResult {
  passed: boolean;
  failures: string[];
  versionTested: number;
  transcript: Array<{ role: string; text: string }>;
  toolCalls: string[];
  metrics: Call["metrics"];
  endedReason?: EndedReason;
  diff?: {
    fromVersion: number;
    toVersion: number;
    changedKeys: string[];
  };
}

export interface WorkflowTestInput {
  payload?: JsonValue;
  version?: number;
  compareVersion?: number;
}

export interface WorkflowTestResult {
  versionTested: number;
  run: WorkflowRun;
  diff?: {
    fromVersion: number;
    toVersion: number;
    addedNodes: string[];
    removedNodes: string[];
    changedNodes: string[];
    edgesChanged: boolean;
  };
}

/**
 * Composition root.
 *
 * Persists state in Node 24 built-in `node:sqlite` (`DatabaseSync` WAL mode)
 * with automatic one-time migration from legacy `omalla.db.json`.
 */
export class OmallaRuntime {
  readonly db: Database;
  readonly logger: Logger;
  readonly credentials: CredentialService;
  readonly store: LocalAutomationStore;
  readonly telephony: TelephonyService;
  readonly telephonyProviders: TelephonyRegistry;
  readonly tools: ToolRuntime;
  readonly replayCache: WebhookReplayCache;
  readonly idempotencyManager: SqliteIdempotencyManager;
  readonly events = new Emitter<RuntimeEvents>();
  private readonly secrets: SecretBox;
  private readonly singleUseCarrierMediaTokens = new Map<
    string,
    { callId: string; expiresAtMs: number }
  >();
  private readonly singleUseMediaTokens = new Map<
    string,
    { tenantId: string; agentId: string; callId?: string; expiresAtMs: number }
  >();
  private readonly handles = new Map<string, CallHandle>();
  private readonly options: RuntimeOptions;

  private constructor(
    readonly config: OmallaConfig,
    db: Database,
    box: SecretBox,
    logger: Logger,
    options: RuntimeOptions,
  ) {
    this.db = db;
    this.secrets = box;
    this.logger = logger;
    this.options = options;
    this.credentials = new CredentialService(db, box, {
      allowSharedEnvCredentials: config.allowSharedEnvCredentials === true,
    });
    this.store = new LocalAutomationStore(db);
    this.replayCache = new WebhookReplayCache(() => this.db.sqliteDb);
    this.idempotencyManager = new SqliteIdempotencyManager(() => this.db.sqliteDb);
    this.telephonyProviders =
      options.telephonyRegistry ??
      new TelephonyRegistry(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {});
    this.tools = new ToolRuntime({
      db,
      credentials: this.credentials,
      store: this.store,
      logger,
      urlPolicy: { allowPrivate: config.allowPrivateHttp },
      ...(options.fetchImpl ? { fetch: options.fetchImpl } : {}),
      ...(options.dnsLookup ? { dnsLookup: options.dnsLookup } : {}),
      runWorkflow: (input) => this.runWorkflowTool(input),
    });
    this.telephony = new TelephonyService({
      db,
      logger,
      createSession: (call, agent) => this.createSession(call, agent),
      speak: async (call, text) => {
        this.emit(call.id, "ivr.prompt", { text });
      },
      onCallEnded: (call) => this.afterCall(call),
    });
  }

  static async open(config: OmallaConfig, options: RuntimeOptions = {}): Promise<OmallaRuntime> {
    await mkdir(config.dataDir, { recursive: true });
    const db = await Database.open({
      filePath: path.join(config.dataDir, "omalla.db"),
      legacyJsonPath: path.join(config.dataDir, "omalla.db.json"),
    });
    const box = await SecretBox.open({
      dir: config.dataDir,
      ...(config.masterKey ? { masterKey: config.masterKey } : {}),
    });
    const logger = options.logger ?? createLogger({ bindings: { service: "omalla" } });
    const runtime = new OmallaRuntime(config, db, box, logger, options);
    if (config.seedDemo) await runtime.seedIfEmpty();
    return runtime;
  }

  /* ------------------------------------------------------------------ */
  /* identity                                                            */
  /* ------------------------------------------------------------------ */

  async issueApiKey(
    tenantId: string,
    name: string,
    role: Principal["role"] = "owner",
  ): Promise<{ id: string; token: string; prefix: string }> {
    const token = `omk_${newToken(24)}`;
    const prefix = token.slice(0, 12);
    const record: ApiKey = {
      id: newId("key"),
      tenantId,
      name,
      prefix,
      hash: hashToken(token),
      role,
      createdAt: nowIso(),
    };
    this.db.col("apiKeys").insert(record);
    return { id: record.id, token, prefix };
  }

  authenticate(token: string, now = new Date()): Principal {
    const trimmed = token.trim();
    if (!trimmed.startsWith("omk_")) {
      throw new OmallaError("unauthorized", "invalid API key", 401);
    }
    const prefix = trimmed.slice(0, 12);
    const presented = Buffer.from(hashToken(trimmed), "hex");
    const candidate = this.db
      .col("apiKeys")
      .list((key) => key.prefix === prefix && !key.revokedAt)
      .find((key) => {
        const stored = Buffer.from(key.hash, "hex");
        return stored.length === presented.length && timingSafeEqual(stored, presented);
      });
    if (!candidate) throw new OmallaError("unauthorized", "invalid API key", 401);
    this.db.col("apiKeys").update(candidate.id, { lastUsedAt: now.toISOString() });
    return { tenantId: candidate.tenantId, role: candidate.role, kind: "api_key", apiKeyId: candidate.id };
  }

  requireRole(principal: Principal, minimum: Principal["role"]): void {
    const order: Principal["role"][] = ["viewer", "operator", "admin", "owner"];
    if (order.indexOf(principal.role) < order.indexOf(minimum)) {
      throw new OmallaError("forbidden", `this action requires the ${minimum} role`, 403);
    }
  }

  /* ------------------------------------------------------------------ */
  /* carrier calls                                                       */
  /* ------------------------------------------------------------------ */

  createCarrierCall(input: {
    tenantId: string;
    provider: TelephonyProvider;
    direction: "inbound" | "outbound";
    from: string;
    to: string;
    providerCallId: string;
    phoneNumberId?: string;
    agentId?: string;
    variables?: Record<string, JsonValue>;
    answered?: boolean;
    callerNumberVerified?: boolean;
  }): Call {
    const now = nowIso();
    const call: Call = {
      id: newId("call"),
      tenantId: input.tenantId,
      direction: input.direction,
      status: input.answered ? "in_progress" : "queued",
      from: input.from,
      to: input.to,
      ...(input.phoneNumberId ? { phoneNumberId: input.phoneNumberId } : {}),
      ...(input.agentId ? { agentId: input.agentId } : {}),
      startedAt: now,
      ...(input.answered ? { answeredAt: now } : {}),
      transcript: [],
      messages: [],
      variables: input.variables ?? {},
      metadata: {
        provider: input.provider.id,
        providerCallId: input.providerCallId,
        carrierCharges: true,
        callerNumberVerified: input.callerNumberVerified === true,
      },
      metrics: {
        turnCount: 0,
        turnLatenciesMs: [],
        totalTokensIn: 0,
        totalTokensOut: 0,
        toolCalls: 0,
        interruptions: 0,
      },
      simulation: false,
    };
    this.db.col("calls").insert(call);
    return call;
  }

  findCallByProviderId(providerCallId: string, tenantId?: string): Call | undefined {
    return this.db
      .col("calls")
      .list(
        (call) =>
          call.metadata.providerCallId === providerCallId &&
          (tenantId === undefined || call.tenantId === tenantId),
      )[0];
  }

  bindProviderCall(callId: string, providerCallId: string): Call {
    const call = this.db.col("calls").get(callId);
    if (!call) throw new OmallaError("not_found", "call not found", 404);
    const next = { ...call, metadata: { ...call.metadata, providerCallId } };
    this.db.col("calls").update(callId, next);
    return next;
  }

  /** Applies a carrier status callback exactly once per terminal state. */
  async updateCarrierStatus(
    providerCallId: string,
    status: "queued" | "initiated" | "ringing" | "in-progress" | "completed" | "busy" | "failed" | "no-answer" | "canceled",
    options: { durationSec?: number; error?: string } = {},
  ): Promise<Call | undefined> {
    const call = this.findCallByProviderId(providerCallId);
    if (!call) return undefined;

    if (status === "in-progress") {
      call.status = "in_progress";
      call.answeredAt = call.answeredAt ?? nowIso();
      this.persistCall(call);
      return call;
    }
    if (status === "ringing" || status === "queued" || status === "initiated") {
      if (call.status !== "ended") call.status = status === "ringing" ? "ringing" : "queued";
      this.persistCall(call);
      return call;
    }
    if (call.status === "ended") return call;

    const reason: EndedReason =
      status === "completed"
        ? call.metadata.transferDestination
          ? "transfer"
          : call.metrics.turnCount > 0
            ? "customer_ended"
            : "no_answer"
        : status === "busy"
          ? "busy"
          : status === "no-answer"
            ? "no_answer"
            : status === "canceled"
              ? "canceled"
              : "error";

    call.status = "ended";
    call.endedAt = nowIso();
    call.endedReason = reason;
    if (options.durationSec !== undefined) call.metadata.providerDurationSec = options.durationSec;
    if (options.error) call.error = options.error;
    this.persistCall(call);
    this.emit(call.id, "call.ended", { reason, at: call.endedAt });

    if (call.metadata.carrierPostCallRan !== true) {
      call.metadata.carrierPostCallRan = true;
      await this.afterCall(call);
    }
    return call;
  }

  /* ------------------------------------------------------------------ */
  /* media stream signing & single-use realtime tokens                   */
  /* ------------------------------------------------------------------ */

  issueMediaToken(callId: string, ttlSec = 120): string {
    const nowMs = Date.now();
    for (const [k, v] of this.singleUseCarrierMediaTokens) {
      if (v.expiresAtMs <= nowMs) this.singleUseCarrierMediaTokens.delete(k);
    }
    const clampedTtl = Math.max(5, Math.min(ttlSec, 600));
    const token = `ommt_${newToken(24)}`;
    this.singleUseCarrierMediaTokens.set(token, {
      callId,
      expiresAtMs: nowMs + clampedTtl * 1000,
    });
    return token;
  }

  signMediaToken(callId: string): string {
    return this.issueMediaToken(callId);
  }

  verifyMediaToken(callId: string, token: string): boolean {
    const entry = this.singleUseCarrierMediaTokens.get(token);
    if (!entry) return false;
    this.singleUseCarrierMediaTokens.delete(token);
    if (entry.expiresAtMs <= Date.now()) return false;
    return entry.callId === callId;
  }

  issueRealtimeToken(input: {
    tenantId: string;
    agentId: string;
    callId?: string;
    ttlSec?: number;
  }): { token: string; expiresAt: string } {
    const nowMs = Date.now();
    for (const [k, v] of this.singleUseMediaTokens) {
      if (v.expiresAtMs <= nowMs) this.singleUseMediaTokens.delete(k);
    }
    const ttlSec = Math.max(5, Math.min(input.ttlSec ?? 60, 300));
    const expiresAtMs = nowMs + ttlSec * 1000;
    const nonce = newToken(24);
    const token = `omrt_${nonce}`;
    this.singleUseMediaTokens.set(token, {
      tenantId: input.tenantId,
      agentId: input.agentId,
      ...(input.callId ? { callId: input.callId } : {}),
      expiresAtMs,
    });
    return { token, expiresAt: new Date(expiresAtMs).toISOString() };
  }

  consumeRealtimeToken(token: string): { tenantId: string; agentId: string; callId?: string } | null {
    const entry = this.singleUseMediaTokens.get(token);
    if (!entry) return null;
    this.singleUseMediaTokens.delete(token);
    if (entry.expiresAtMs <= Date.now()) return null;
    return {
      tenantId: entry.tenantId,
      agentId: entry.agentId,
      ...(entry.callId ? { callId: entry.callId } : {}),
    };
  }

  /** Builds the media bridge for a carrier call; the server owns the socket. */
  async openMediaSession(callId: string): Promise<{
    bridge: MediaBridge;
    call: Call;
    agent: Agent;
  }> {
    const call = this.db.col("calls").get(callId);
    if (!call) throw new OmallaError("not_found", "call not found", 404);
    if (call.simulation) {
      throw new OmallaError("validation", "simulated calls do not use the carrier media bridge", 409);
    }
    if (call.status === "ended") {
      throw new OmallaError("validation", "call has already ended", 409);
    }
    const providerId = String(call.metadata.provider ?? "");
    const provider = this.telephonyProviders.get(providerId);
    const agent = call.agentId ? this.db.col("agents").get(call.agentId) : undefined;
    if (!agent || agent.tenantId !== call.tenantId) {
      throw new OmallaError("validation", "call has no valid tenant agent", 409);
    }

    const { engine, stt } = await this.buildConversation(call, agent);
    const voiceEngine = new ConversationVoiceEngine(engine);
    const bridge = new MediaBridge({
      provider,
      engine: voiceEngine,
      stt,
      logger: this.logger.child({ callId: call.id, component: "media" }),
      language: agent.config.language,
    });

    const maxTimer = setTimeout(() => {
      void bridge.close("max_duration");
    }, Math.max(30, agent.config.maxDurationSec) * 1000);
    maxTimer.unref?.();
    engine.on("call.ended", () => {
      clearTimeout(maxTimer);
      void bridge.close(engine.call.endedReason ?? "customer_ended").catch(() => {});
    });

    return { bridge, call, agent };
  }

  providerSummary(): Array<Record<string, JsonValue>> {
    return this.telephonyProviders.availability().map((entry) => ({
      id: entry.id,
      label: entry.label,
      available: entry.available,
      detail: entry.detail,
      requiredEnv: entry.requiredEnv,
    }));
  }

  emitCallEvent(callId: string, type: string, data: Record<string, unknown>): void {
    this.emit(callId, type, data);
  }

  /* ------------------------------------------------------------------ */
  /* voice                                                               */
  /* ------------------------------------------------------------------ */

  async startInbound(input: {
    tenantId?: string;
    to: string;
    from: string;
    variables?: Record<string, JsonValue>;
  }): Promise<CallHandle> {
    const handle = await this.telephony.receiveInbound(input);
    this.handles.set(handle.call.id, handle);
    return handle;
  }

  async startOutbound(input: {
    tenantId: string;
    to: string;
    agentId: string;
    consent: boolean;
    variables?: Record<string, JsonValue>;
    from?: string;
  }): Promise<CallHandle> {
    const handle = await this.telephony.placeOutbound(input);
    this.handles.set(handle.call.id, handle);
    return handle;
  }

  /**
   * Places a real carrier call. Enforces the exact same deterministic OM-T6
   * outbound policy (consent, DNC, allowlist, callingWindow + timeZone, daily
   * cap, concurrent calls, and daily/monthly minute quotas) as simulated calls.
   */
  async startCarrierOutbound(input: {
    tenantId: string;
    to: string;
    agentId: string;
    providerId?: string;
    consent: boolean;
    variables?: Record<string, JsonValue>;
    from?: string;
  }): Promise<Call> {
    const tenant = this.db.col("tenants").get(input.tenantId);
    if (!tenant) throw new OmallaError("not_found", "tenant not found", 404);
    const agent = this.resolvePublishedAgent(tenant.id, input.agentId);
    const explicitFrom = input.from ? normalizeNumber(input.from) : undefined;
    const numberByFrom = explicitFrom
      ? this.db
          .col("phoneNumbers")
          .list(
            (candidate) =>
              candidate.tenantId === tenant.id &&
              candidate.e164 === explicitFrom &&
              candidate.status === "active",
          )[0]
      : undefined;
    const provider = this.telephonyProviders.get(
      input.providerId ?? numberByFrom?.provider ?? this.telephonyProviders.default.id,
    );
    requireCapability(provider, "voice");

    const to = normalizeNumber(input.to);
    const number =
      numberByFrom ??
      this.db
        .col("phoneNumbers")
        .list(
          (candidate) =>
            candidate.tenantId === tenant.id &&
            candidate.status === "active" &&
            candidate.provider === provider.id,
        )[0];
    const from = number?.e164 ?? explicitFrom ?? "";
    if (!from) {
      throw new OmallaError(
        "validation",
        `no active ${provider.id} number is configured; provision a number first`,
        400,
      );
    }

    const decision = evaluateOutboundPolicy(
      buildTenantOutboundPolicyInput(this.db, tenant, {
        to,
        from,
        consentGranted: input.consent,
        now: new Date(),
      }),
    );
    if (!decision.allowed) {
      throw new OmallaError("blocked_by_policy", decision.reason ?? "outbound call blocked", 403);
    }

    const base = this.config.publicBaseUrl.replace(/\/+$/, "");
    const safeVars = sanitizeUntrustedCallVariables(input.variables);
    const call = this.createCarrierCall({
      tenantId: tenant.id,
      provider,
      direction: "outbound",
      from,
      to,
      providerCallId: "pending",
      ...(number ? { phoneNumberId: number.id } : {}),
      agentId: agent.id,
      answered: false,
      variables: { ...safeVars, consentGranted: true, consentAt: nowIso() },
    });

    try {
      requireCapability(provider, "voice");
      const created = await provider.createCall?.({
        to,
        from,
        answerUrl: `${base}/telephony/${provider.id}/voice?callId=${encodeURIComponent(call.id)}`,
        statusCallbackUrl: `${base}/telephony/${provider.id}/status`,
        ...(agent.config.recording.enabled
          ? { recordingCallbackUrl: `${base}/telephony/${provider.id}/recording` }
          : {}),
        record: agent.config.recording.enabled,
        timeoutSec: 30,
      });
      if (!created) {
        throw new OmallaError("provider_error", `${provider.id} cannot place calls`, 501);
      }
      this.bindProviderCall(call.id, created.providerCallId);
      call.metadata.providerCallId = created.providerCallId;
    } catch (error) {
      call.status = "failed";
      call.endedAt = nowIso();
      call.endedReason = "error";
      call.error = (error as Error).message;
      this.persistCall(call);
      this.emit(call.id, "call.ended", { reason: "error", at: call.endedAt });
      throw error;
    }

    this.emit(call.id, "call.queued", { provider: provider.id });
    return this.db.col("calls").get(call.id) ?? call;
  }

  private resolvePublishedAgent(tenantId: string, agentId: string): Agent {
    const agent = this.db.col("agents").get(agentId);
    if (!agent || agent.tenantId !== tenantId) {
      throw new OmallaError("not_found", `agent ${agentId} not found`, 404);
    }
    if (agent.status !== "published") {
      throw new OmallaError("validation", `agent ${agent.name} is not published`, 409);
    }
    return agent;
  }

  handleFor(callId: string): CallHandle {
    const handle = this.handles.get(callId);
    if (!handle) {
      throw new OmallaError("not_found", "call is not active", 404);
    }
    return handle;
  }

  async say(callId: string, text: string): Promise<Call> {
    const handle = this.handleFor(callId);
    await handle.say(text);
    return handle.snapshot();
  }

  async press(callId: string, digits: string): Promise<Call> {
    const handle = this.handleFor(callId);
    await handle.press(digits);
    return handle.snapshot();
  }

  async hangup(
    callId: string,
    reason: "customer_ended" | "assistant_ended" | "canceled" = "customer_ended",
  ): Promise<Call> {
    const handle = this.handleFor(callId);
    await handle.hangup(reason);
    this.handles.delete(callId);
    return handle.snapshot();
  }

  private async createSession(call: Call, agent: Agent): Promise<ConversationSession> {
    const { engine } = await this.buildConversation(call, agent);
    return engine;
  }

  async buildConversation(
    call: Call,
    agent: Agent,
  ): Promise<{ engine: ConversationEngine; stt: SttProvider }> {
    const tenantId = call.tenantId;
    const offline = this.options.offlineProviders === true;
    const hasTenantBaseUrl = Boolean(
      agent.config.model.baseUrl ||
        agent.config.model.fallbacks?.some((f) => Boolean(f.baseUrl)) ||
        agent.config.voice.baseUrl ||
        agent.config.voice.fallbacks?.some((f) => Boolean(f.baseUrl)) ||
        agent.config.transcriber.baseUrl ||
        agent.config.transcriber.fallbacks?.some((f) => Boolean(f.baseUrl)),
    );
    const providerFetch = createSsrfGuardedFetch({
      allowPrivate: this.config.allowPrivateHttp || !hasTenantBaseUrl,
      ...(this.options.fetchImpl ? { baseFetch: this.options.fetchImpl } : {}),
      ...(this.options.dnsLookup ? { lookup: this.options.dnsLookup } : {}),
    });
    const providers = await resolveProviders(agent, {
      logger: this.logger,
      resolveCredential: async (ref) => (ref ? this.credentials.get(tenantId, ref) : undefined),
      fetchImpl: providerFetch,
    });

    // OM-T1 #1: filter knowledge bases strictly by authenticated call.tenantId
    const documents = agent.config.knowledgeBaseIds.flatMap((id) => {
      const kb = this.db.col("knowledgeBases").get(id);
      if (!kb || kb.tenantId !== tenantId) return [];
      return kb.documents.map((document) => ({
        id: document.id,
        title: document.title,
        text: document.text,
      }));
    });

    const engine = new ConversationEngine({
      call,
      agent,
      llm: providers.llm,
      tts: providers.tts,
      tools: this.tools,
      logger: this.logger.child({ callId: call.id }),
      ...(documents.length > 0 ? { retriever: createRetriever(documents) } : {}),
      persist: (current) => this.persistCall(current),
    });

    engine.on("call.started", ({ at }) => this.emit(call.id, "call.started", { at }));
    engine.on("assistant.delta", ({ text }) => this.emit(call.id, "assistant.delta", { text }));
    engine.on("assistant.speech", (payload) =>
      this.emit(call.id, "assistant.speech", {
        text: payload.text,
        interrupted: payload.interrupted,
        at: payload.at,
      }),
    );
    engine.on("assistant.interrupted", ({ offsetMs }) =>
      this.emit(call.id, "assistant.interrupted", { offsetMs }),
    );
    engine.on("caller.transcript", ({ text, at }) => this.emit(call.id, "caller.transcript", { text, at }));
    engine.on("tool.started", ({ name, args }) => this.emit(call.id, "tool.started", { name, args }));
    engine.on("tool.finished", ({ name, ok, result, error }) =>
      this.emit(call.id, "tool.finished", {
        name,
        ok,
        ...(result !== undefined ? { result } : {}),
        ...(error ? { error } : {}),
      }),
    );
    engine.on("call.ended", ({ reason, at }) => this.emit(call.id, "call.ended", { reason, at }));

    if (offline) {
      this.logger.debug("offline provider mode", { callId: call.id });
    }
    return { engine, stt: providers.stt };
  }

  private persistCall(call: Call): void {
    try {
      this.db.col("calls").update(call.id, () => structuredClone(call));
    } catch {
      // The call may already have been written by the telephony layer.
    }
  }

  private emit(callId: string, type: string, data: Record<string, unknown>): void {
    if (type === "call.ended") this.handles.delete(callId);
    const event: CallEvent = {
      callId,
      type,
      at: nowIso(),
      data: data as JsonValue,
    };
    this.events.emit("call", event);
  }

  /** Runs after every terminal call: stores the outcome and starts automation. */
  private async afterCall(call: Call): Promise<void> {
    this.persistCall(call);
    const agent = call.agentId ? this.db.col("agents").get(call.agentId) : undefined;
    // OM-T1 #3: verify agent AND postCallWorkflowId strictly belong to call.tenantId
    if (!agent || agent.tenantId !== call.tenantId) return;
    const workflowId = agent.config.postCallWorkflowId;
    if (!workflowId) return;

    const workflow = this.db.col("workflows").get(workflowId);
    if (!workflow || workflow.tenantId !== call.tenantId || workflow.status !== "active") return;

    const bookings = this.db
      .col("bookings")
      .list((booking) => booking.tenantId === call.tenantId && booking.callId === call.id);
    const appointment = bookings[0];

    const summary = call.transcript
      .filter((turn) => turn.role === "caller")
      .map((turn) => turn.text)
      .join(" ")
      .slice(0, 800);

    await this.runWorkflow(workflow, {
      type: "call_ended",
      payload: {
        callId: call.id,
        callerNumber: call.from,
        businessNumber: call.to,
        endedReason: call.endedReason ?? "customer_ended",
        summary: summary || "No caller speech was captured.",
        transcript: call.transcript.map((turn) => `${turn.role}: ${turn.text}`).join("\n"),
        priority: call.metadata.priority ?? "normal",
        ...(appointment
          ? {
              appointment: {
                name: appointment.name,
                startAt: appointment.startAt,
                durationMin: appointment.durationMin,
              },
            }
          : {}),
      },
      idempotencyKey: `call:${call.id}:${workflow.id}`,
      callId: call.id,
    }).catch((error) => {
      this.logger.error("post-call workflow failed", {
        callId: call.id,
        error: (error as Error).message,
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* agent & workflow immutable versioning, test runner, and rollback    */
  /* ------------------------------------------------------------------ */

  recordAgentVersion(agent: Agent, createdBy: string, note?: string): AgentVersion {
    const snapshot: AgentVersion = {
      id: newId("agv"),
      tenantId: agent.tenantId,
      agentId: agent.id,
      version: agent.version,
      config: structuredClone(agent.config),
      createdAt: nowIso(),
      createdBy,
      ...(note ? { note } : {}),
    };
    const existing = this.db
      .col("agentVersions")
      .list((v) => v.tenantId === agent.tenantId && v.agentId === agent.id && v.version === agent.version)[0];
    if (existing) return existing;
    return this.db.col("agentVersions").insert(snapshot);
  }

  listAgentVersions(tenantId: string, agentId: string): AgentVersion[] {
    return this.db
      .col("agentVersions")
      .list((v) => v.tenantId === tenantId && v.agentId === agentId)
      .sort((a, b) => b.version - a.version);
  }

  rollbackAgent(
    tenantId: string,
    agentId: string,
    targetVersion: number,
    actor: string,
    note?: string,
  ): Agent {
    const agent = this.db.col("agents").get(agentId);
    if (!agent || agent.tenantId !== tenantId) {
      throw new OmallaError("not_found", "agent not found", 404);
    }
    const target = this.db
      .col("agentVersions")
      .list(
        (v) => v.tenantId === tenantId && v.agentId === agentId && v.version === targetVersion,
      )[0];
    if (!target) {
      throw new OmallaError("not_found", `agent version ${targetVersion} not found`, 404);
    }

    const versions = this.listAgentVersions(tenantId, agentId);
    const maxVer = Math.max(agent.version, ...versions.map((v) => v.version));
    const nextVersion = maxVer + 1;
    const restoredConfig = structuredClone(target.config);
    const now = nowIso();

    const updated = this.db.col("agents").update(agent.id, {
      config: restoredConfig,
      version: nextVersion,
      updatedAt: now,
    });

    for (const tool of restoredConfig.tools) {
      if (tool.tenantId === tenantId) {
        this.db.col("tools").upsert(tool);
      }
    }

    this.recordAgentVersion(
      updated,
      actor,
      note ?? `rollback from v${agent.version} to v${targetVersion}`,
    );
    return updated;
  }

  async testAgent(
    tenantId: string,
    agentId: string,
    input: AgentTestInput,
  ): Promise<AgentTestResult> {
    const baseAgent = this.db.col("agents").get(agentId);
    if (!baseAgent || baseAgent.tenantId !== tenantId) {
      throw new OmallaError("not_found", "agent not found", 404);
    }

    let configToTest: AgentConfig = structuredClone(baseAgent.config);
    let versionTested = baseAgent.version;

    if (input.version !== undefined) {
      const snap = this.db
        .col("agentVersions")
        .list(
          (v) => v.tenantId === tenantId && v.agentId === agentId && v.version === input.version,
        )[0];
      if (!snap) {
        throw new OmallaError("not_found", `agent version ${input.version} not found`, 404);
      }
      configToTest = structuredClone(snap.config);
      versionTested = snap.version;
    }

    // Force zero-cost local mock voice/STT during synthetic test evaluation if cloud lacks creds
    const syntheticAgent: Agent = {
      ...structuredClone(baseAgent),
      version: versionTested,
      config: {
        ...configToTest,
        voice: { provider: "mock", voiceId: "test" },
        transcriber: { provider: "mock", language: configToTest.language },
        silenceTimeoutSec: 0,
      },
    };

    const ephemeralDb = await Database.open({ filePath: ":memory:", persist: false });
    for (const kb of this.db.col("knowledgeBases").list((k) => k.tenantId === tenantId)) {
      ephemeralDb.col("knowledgeBases").insert(kb);
    }
    ephemeralDb.col("agents").insert(syntheticAgent);
    for (const tool of syntheticAgent.config.tools) {
      if (tool.tenantId === tenantId) ephemeralDb.col("tools").upsert(tool);
    }

    const dryTools = new ToolRuntime({
      db: ephemeralDb,
      credentials: this.credentials,
      store: new LocalAutomationStore(ephemeralDb),
      logger: this.logger,
      urlPolicy: { allowPrivate: this.config.allowPrivateHttp },
      fetch: async (urlInput) =>
        new Response(JSON.stringify({ simulated: true, url: String(urlInput) }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
    });

    const dryProviderFetch = createSsrfGuardedFetch({
      allowPrivate: this.config.allowPrivateHttp,
      baseFetch: async () =>
        new Response(
          JSON.stringify({
            choices: [{ message: { role: "assistant", content: "Dry-run test response." } }],
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
    });
    const providers = await resolveProviders(syntheticAgent, {
      logger: this.logger,
      resolveCredential: async (ref) => (ref ? this.credentials.get(tenantId, ref) : undefined),
      fetchImpl: dryProviderFetch,
    });

    const documents = syntheticAgent.config.knowledgeBaseIds.flatMap((id) => {
      const kb = ephemeralDb.col("knowledgeBases").get(id);
      if (!kb || kb.tenantId !== tenantId) return [];
      return kb.documents.map((doc) => ({ id: doc.id, title: doc.title, text: doc.text }));
    });

    const call: Call = {
      id: newId("call"),
      tenantId,
      direction: "inbound",
      status: "in_progress",
      from: "+15550009999",
      to: "+15550001234",
      agentId: syntheticAgent.id,
      agentVersion: versionTested,
      startedAt: nowIso(),
      transcript: [],
      messages: [],
      variables: sanitizeUntrustedCallVariables(input.variables),
      metadata: { dryRun: true, callerNumberVerified: false },
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

    const calledTools: string[] = [];
    const engine = new ConversationEngine({
      call,
      agent: syntheticAgent,
      llm: providers.llm,
      tts: providers.tts,
      tools: dryTools,
      logger: this.logger,
      ...(documents.length > 0 ? { retriever: createRetriever(documents) } : {}),
    });
    engine.on("tool.started", ({ name }) => calledTools.push(name));

    try {
      await engine.start();
      for (const turn of input.callerTurns) {
        if (engine.isEnded) break;
        await engine.handleCallerUtterance(turn);
      }
      if (!engine.isEnded) {
        await engine.end("customer_ended");
      }
    } finally {
      await ephemeralDb.close();
    }

    const failures: string[] = [];
    const assistantText = call.transcript
      .filter((t) => t.role === "assistant")
      .map((t) => t.text)
      .join(" ")
      .toLowerCase();

    if (input.expectations?.mustContain) {
      for (const phrase of input.expectations.mustContain) {
        if (!assistantText.includes(phrase.toLowerCase())) {
          failures.push(`missing expected phrase: ${phrase}`);
        }
      }
    }
    if (input.expectations?.mustNotContain) {
      for (const phrase of input.expectations.mustNotContain) {
        if (assistantText.includes(phrase.toLowerCase())) {
          failures.push(`contained forbidden phrase: ${phrase}`);
        }
      }
    }
    if (input.expectations?.mustCallTools) {
      for (const toolName of input.expectations.mustCallTools) {
        if (!calledTools.includes(toolName)) {
          failures.push(`expected tool was not called: ${toolName}`);
        }
      }
    }
    if (
      input.expectations?.maxTurns !== undefined &&
      call.metrics.turnCount > input.expectations.maxTurns
    ) {
      failures.push(`turnCount ${call.metrics.turnCount} exceeded maxTurns ${input.expectations.maxTurns}`);
    }

    let diff: AgentTestResult["diff"] | undefined;
    if (input.compareVersion !== undefined) {
      const other = this.db
        .col("agentVersions")
        .list(
          (v) =>
            v.tenantId === tenantId &&
            v.agentId === agentId &&
            v.version === input.compareVersion,
        )[0];
      if (!other) {
        throw new OmallaError("not_found", `agent version ${input.compareVersion} not found`, 404);
      }
      const keys = Object.keys(configToTest) as Array<keyof AgentConfig>;
      const changedKeys = keys.filter(
        (key) => JSON.stringify(other.config[key]) !== JSON.stringify(configToTest[key]),
      );
      diff = {
        fromVersion: other.version,
        toVersion: versionTested,
        changedKeys,
      };
    }

    return {
      passed: failures.length === 0,
      failures,
      versionTested,
      transcript: call.transcript.map((t) => ({ role: t.role, text: t.text })),
      toolCalls: calledTools,
      metrics: call.metrics,
      ...(call.endedReason ? { endedReason: call.endedReason } : {}),
      ...(diff ? { diff } : {}),
    };
  }

  recordWorkflowVersion(workflow: Workflow, createdBy: string, note?: string): WorkflowVersion {
    const existing = this.db
      .col("workflowVersions")
      .list(
        (v) =>
          v.tenantId === workflow.tenantId &&
          v.workflowId === workflow.id &&
          v.version === workflow.version,
      )[0];
    if (existing) return existing;

    const record: WorkflowVersion = {
      id: newId("wfv"),
      tenantId: workflow.tenantId,
      workflowId: workflow.id,
      version: workflow.version,
      snapshot: structuredClone({
        name: workflow.name,
        description: workflow.description,
        status: workflow.status,
        trigger: workflow.trigger,
        nodes: workflow.nodes,
        edges: workflow.edges,
        idempotencyWindowSec: workflow.idempotencyWindowSec,
      }),
      createdAt: nowIso(),
      createdBy,
      ...(note ? { note } : {}),
    };
    return this.db.col("workflowVersions").insert(record);
  }

  listWorkflowVersions(tenantId: string, workflowId: string): WorkflowVersion[] {
    return this.db
      .col("workflowVersions")
      .list((v) => v.tenantId === tenantId && v.workflowId === workflowId)
      .sort((a, b) => b.version - a.version);
  }

  rollbackWorkflow(
    tenantId: string,
    workflowId: string,
    targetVersion: number,
    actor: string,
    note?: string,
  ): Workflow {
    const workflow = this.db.col("workflows").get(workflowId);
    if (!workflow || workflow.tenantId !== tenantId) {
      throw new OmallaError("not_found", "workflow not found", 404);
    }
    const target = this.db
      .col("workflowVersions")
      .list(
        (v) => v.tenantId === tenantId && v.workflowId === workflowId && v.version === targetVersion,
      )[0];
    if (!target) {
      throw new OmallaError("not_found", `workflow version ${targetVersion} not found`, 404);
    }

    const versions = this.listWorkflowVersions(tenantId, workflowId);
    const maxVer = Math.max(workflow.version, ...versions.map((v) => v.version));
    const nextVersion = maxVer + 1;
    const snap = structuredClone(target.snapshot);

    const updated = this.db.col("workflows").update(workflow.id, {
      name: snap.name,
      description: snap.description,
      status: snap.status,
      trigger: snap.trigger,
      nodes: snap.nodes,
      edges: snap.edges,
      idempotencyWindowSec: snap.idempotencyWindowSec,
      version: nextVersion,
      updatedAt: nowIso(),
    });
    this.recordWorkflowVersion(
      updated,
      actor,
      note ?? `rollback from v${workflow.version} to v${targetVersion}`,
    );
    return updated;
  }

  async testWorkflow(
    tenantId: string,
    workflowId: string,
    input: WorkflowTestInput,
  ): Promise<WorkflowTestResult> {
    const baseWorkflow = this.db.col("workflows").get(workflowId);
    if (!baseWorkflow || baseWorkflow.tenantId !== tenantId) {
      throw new OmallaError("not_found", "workflow not found", 404);
    }

    let candidate: Workflow = structuredClone(baseWorkflow);
    if (input.version !== undefined) {
      const snap = this.db
        .col("workflowVersions")
        .list(
          (v) => v.tenantId === tenantId && v.workflowId === workflowId && v.version === input.version,
        )[0];
      if (!snap) {
        throw new OmallaError("not_found", `workflow version ${input.version} not found`, 404);
      }
      candidate = {
        ...candidate,
        ...structuredClone(snap.snapshot),
        version: snap.version,
      };
    }

    const ephemeralDb = await Database.open({ filePath: ":memory:", persist: false });
    const dryStore = new LocalAutomationStore(ephemeralDb);
    const engine = new WorkflowEngine(
      {
        ...this.workflowServices(tenantId),
        store: dryStore,
        escalate: (esc) => dryStore.escalate(esc),
        startCall: async () => ({ callId: newId("dry_call") }),
        sendSms: async (s) => ({
          simulated: true,
          dryRun: true,
          to: s.to,
          body: s.body,
          provider: s.provider ?? "mock",
        }),
      },
      { has: () => false, remember: () => {} },
    );

    let run: WorkflowRun;
    try {
      run = await engine.run(candidate, {
        trigger: { type: candidate.trigger.type, payload: input.payload ?? {} },
        dryRun: true,
      });
    } finally {
      await ephemeralDb.close();
    }

    let diff: WorkflowTestResult["diff"] | undefined;
    if (input.compareVersion !== undefined) {
      const other = this.db
        .col("workflowVersions")
        .list(
          (v) =>
            v.tenantId === tenantId &&
            v.workflowId === workflowId &&
            v.version === input.compareVersion,
        )[0];
      if (!other) {
        throw new OmallaError("not_found", `workflow version ${input.compareVersion} not found`, 404);
      }
      const prevMap = new Map(other.snapshot.nodes.map((n) => [n.id, JSON.stringify(n)]));
      const currMap = new Map(candidate.nodes.map((n) => [n.id, JSON.stringify(n)]));
      const addedNodes = [...currMap.keys()].filter((id) => !prevMap.has(id));
      const removedNodes = [...prevMap.keys()].filter((id) => !currMap.has(id));
      const changedNodes = [...currMap.entries()]
        .filter(([id, json]) => prevMap.has(id) && prevMap.get(id) !== json)
        .map(([id]) => id);
      const edgesChanged = JSON.stringify(other.snapshot.edges) !== JSON.stringify(candidate.edges);
      diff = {
        fromVersion: other.version,
        toVersion: candidate.version,
        addedNodes,
        removedNodes,
        changedNodes,
        edgesChanged,
      };
    }

    return {
      versionTested: candidate.version,
      run,
      ...(diff ? { diff } : {}),
    };
  }

  /* ------------------------------------------------------------------ */
  /* workflows                                                           */
  /* ------------------------------------------------------------------ */

  async runWorkflow(
    workflow: Workflow,
    options: {
      type?: Workflow["trigger"]["type"];
      payload?: JsonValue;
      idempotencyKey?: string;
      callId?: string;
      dryRun?: boolean;
    } = {},
  ): Promise<WorkflowRun> {
    const engine = new WorkflowEngine(
      this.workflowServices(workflow.tenantId),
      this.idempotencyManager.forWorkflowTenant(workflow.tenantId),
    );
    const run = await engine.run(workflow, {
      ...(options.type ? { trigger: { type: options.type, payload: options.payload ?? {} } } : {}),
      ...(options.idempotencyKey ? { idempotencyKey: options.idempotencyKey } : {}),
      ...(options.callId ? { callId: options.callId } : {}),
      ...(options.dryRun ? { dryRun: true } : {}),
    });
    this.db.col("workflowRuns").insert(run);
    return run;
  }

  private async runWorkflowTool(input: {
    tenantId: string;
    workflowId: string;
    payload: Record<string, JsonValue>;
    callId?: string;
    idempotencyKey: string;
  }): Promise<{ runId: string; status: string; output: JsonValue }> {
    const workflow = this.db.col("workflows").get(input.workflowId);
    if (!workflow || workflow.tenantId !== input.tenantId) {
      throw new OmallaError("not_found", "workflow not found", 404);
    }
    if (workflow.status !== "active") {
      throw new OmallaError("validation", `workflow ${workflow.name} is not active`, 409);
    }
    const run = await this.runWorkflow(workflow, {
      type: workflow.trigger.type,
      payload: input.payload,
      idempotencyKey: input.idempotencyKey,
      ...(input.callId ? { callId: input.callId } : {}),
    });
    const succeeded = run.steps.filter(
      (step) => step.status === "succeeded" && step.output !== undefined,
    );
    const last = [...succeeded].reverse().find((step) => step.nodeType !== "end")
      ?? succeeded[succeeded.length - 1];
    return { runId: run.id, status: run.status, output: last?.output ?? null };
  }

  /** OM-T1 #5: webhook path lookup is strictly scoped to the authenticated `tenantId`. */
  async runWebhook(
    tenantId: string,
    pathSuffix: string,
    payload: JsonValue,
    idempotencyKey?: string,
  ): Promise<WorkflowRun> {
    const workflow = this.db
      .col("workflows")
      .list(
        (candidate) =>
          candidate.tenantId === tenantId &&
          candidate.status === "active" &&
          candidate.trigger.type === "webhook" &&
          String(candidate.trigger.config.path ?? "") === pathSuffix,
      )[0];
    if (!workflow) {
      throw new OmallaError("not_found", `no active workflow listens on /hooks/${pathSuffix}`, 404);
    }
    return this.runWorkflow(workflow, {
      type: "webhook",
      payload,
      ...(idempotencyKey ? { idempotencyKey } : {}),
    });
  }

  private workflowServices(tenantId: string): WorkflowServices {
    const guardedFetch = createSsrfGuardedFetch({
      allowPrivate: this.config.allowPrivateHttp,
      ...(this.options.fetchImpl ? { baseFetch: this.options.fetchImpl } : {}),
      ...(this.options.dnsLookup ? { lookup: this.options.dnsLookup } : {}),
    });
    return {
      logger: this.logger.child({ component: "workflow" }),
      fetch: guardedFetch,
      urlPolicy: { allowPrivate: this.config.allowPrivateHttp },
      now: () => new Date(),
      sleep: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
      secrets: {
        get: (name: string) => this.credentials.get(tenantId, name),
      },
      store: this.store,
      escalate: (input) => this.store.escalate(input),
      startCall: async (input) => {
        const handle = await this.telephony.placeOutbound({
          tenantId: input.tenantId,
          to: input.to,
          agentId: input.agentId,
          variables: input.variables,
          consent: input.variables.consent === true,
        });
        return { callId: handle.call.id };
      },
      sendSms: async (s) => {
        const tenant = this.db.col("tenants").get(tenantId);
        if (!tenant) throw new OmallaError("not_found", "tenant not found", 404);
        const to = normalizeNumber(s.to);
        if (!isE164(to)) throw new OmallaError("validation", "SMS destination is not valid E.164", 400);
        const requestedProviderId = !s.provider || s.provider === "mock" ? "simulated" : s.provider;
        const explicitFrom = s.from ? normalizeNumber(s.from) : undefined;
        const number = explicitFrom
          ? this.db
              .col("phoneNumbers")
              .list((candidate) => candidate.tenantId === tenantId && candidate.e164 === explicitFrom)[0]
          : this.db
              .col("phoneNumbers")
              .list((candidate) => candidate.tenantId === tenantId && candidate.status === "active")[0];
        const fromNum = explicitFrom ?? number?.e164 ?? "+15550000000";
        const decision = evaluateOutboundPolicy(
          buildTenantOutboundPolicyInput(this.db, tenant, {
            to,
            from: fromNum,
            consentGranted: s.consent,
            now: new Date(),
          }),
        );
        if (!decision.allowed) {
          throw new OmallaError("blocked_by_policy", decision.reason ?? "outbound SMS blocked", 403);
        }
        const provider = this.telephonyProviders.get(requestedProviderId);
        if (!provider.capabilities.sms || !provider.sendSms) {
          throw new OmallaError("provider_error", `${provider.id} cannot send SMS`, 501);
        }
        const sent = await provider.sendSms({
          to,
          from: fromNum,
          body: s.body,
        });
        const message: SmsMessage = {
          id: newId("sms"),
          tenantId,
          direction: "outbound",
          from: fromNum,
          to,
          body: s.body,
          provider: provider.id,
          providerMessageId: sent.providerMessageId,
          status: sent.status,
          simulated: provider.id === "simulated",
          createdAt: nowIso(),
        };
        this.db.col("smsMessages").insert(message);
        return {
          id: message.id,
          providerMessageId: message.providerMessageId ?? null,
          simulated: message.simulated,
          to: message.to,
          status: message.status,
        };
      },
    };
  }

  installTemplate(id: TemplateId, tenantId: string, createdBy = "system"): Workflow {
    const workflow = buildTemplate(id, tenantId);
    this.db.col("workflows").insert(workflow);
    this.recordWorkflowVersion(workflow, createdBy, `template:${id}`);
    return workflow;
  }

  importN8n(
    json: unknown,
    tenantId: string,
    createdBy = "system",
  ): { workflow: Workflow; warnings: string[] } {
    const result = importN8nWorkflow(json, tenantId);
    this.db.col("workflows").insert(result.workflow);
    this.recordWorkflowVersion(result.workflow, createdBy, "imported:n8n");
    return result;
  }

  exportN8n(workflow: Workflow): unknown {
    return exportN8nWorkflow(workflow);
  }

  /* ------------------------------------------------------------------ */
  /* demo seed                                                           */
  /* ------------------------------------------------------------------ */

  async seedIfEmpty(): Promise<void> {
    if (this.db.col("tenants").count() > 0) return;

    const now = nowIso();
    const tenantId = newId("ten");
    const tenant: Tenant = {
      id: tenantId,
      name: "Northwind Dental (demo)",
      region: "US",
      createdAt: now,
      settings: {
        recordingEnabled: false,
        outboundEnabled: true,
        outboundAllowlist: [],
        dncList: [],
        dailyOutboundCap: 25,
        retentionDays: 30,
        timezone: "America/New_York",
      },
    };
    this.db.col("tenants").insert(tenant);

    const knowledgeBaseId = newId("kb");
    this.db.col("knowledgeBases").insert({
      id: knowledgeBaseId,
      tenantId,
      name: "Front desk handbook",
      description: "Hours, services and pricing used by the receptionist.",
      createdAt: now,
      updatedAt: now,
      documents: [
        {
          id: newId("doc"),
          title: "Opening hours",
          text:
            "The clinic is open Monday to Friday from 9:00 to 17:00. It is closed on Saturdays, Sundays and public holidays. Emergency calls are routed to the on-call dentist.",
          createdAt: now,
          checksum: "seed-hours",
        },
        {
          id: newId("doc"),
          title: "Services and pricing",
          text:
            "A standard check-up costs 90 dollars and takes 30 minutes. A hygiene appointment costs 120 dollars and takes 45 minutes. New patients need a 60 minute first visit. Insurance is accepted; the team confirms coverage before treatment.",
          createdAt: now,
          checksum: "seed-pricing",
        },
        {
          id: newId("doc"),
          title: "Cancellation policy",
          text:
            "Appointments can be moved or cancelled free of charge up to 24 hours in advance. Later cancellations incur a 40 dollar fee.",
          createdAt: now,
          checksum: "seed-policy",
        },
      ],
    });

    const bookingTool = this.makeTool(tenantId, {
      type: "internal",
      internalAction: "create_booking",
      name: "book_appointment",
      description:
        "Book an appointment for the caller. Only call this after the caller confirmed their name, the day and the time.",
      parameters: {
        type: "object",
        properties: {
          name: { type: "string", description: "Caller's full name" },
          when: {
            type: "string",
            description: "Requested day and time in natural language, e.g. 'tomorrow at 3pm'",
          },
          durationMin: { type: "integer", description: "Appointment length in minutes", default: 30 },
          notes: { type: "string", description: "Anything the clinic should know" },
        },
        required: ["name", "when"],
        additionalProperties: false,
      },
      messages: { onRequest: "Let me check that slot for you." },
    });

    const transferTool = this.makeTool(tenantId, {
      type: "transfer",
      name: "transfer_to_human",
      description: "Transfer the caller to a human when they ask for one or need urgent help.",
      parameters: {
        type: "object",
        properties: { reason: { type: "string", description: "Why the caller needs a person" } },
        required: ["reason"],
        additionalProperties: false,
      },
      destinations: ["front-desk"],
    });

    const endTool = this.makeTool(tenantId, {
      type: "end_call",
      name: "end_call",
      description: "End the call politely once the caller has nothing else.",
      parameters: { type: "object", properties: {}, additionalProperties: false },
    });

    const voiceProvider = this.demoVoiceProvider();
    const transcriberProvider = this.demoTranscriberProvider();
    const agent: Agent = {
      id: newId("agt"),
      tenantId,
      name: "Ava — reception",
      description: "Front-desk receptionist for the demo clinic.",
      status: "published",
      version: 1,
      createdAt: now,
      updatedAt: now,
      publishedAt: now,
      config: {
        firstMessage: "Thanks for calling Northwind Dental. This is Ava. How can I help?",
        systemPrompt:
          "You are the front-desk receptionist for Northwind Dental. Help callers book, move or cancel appointments, answer questions about hours and pricing from the knowledge base, and transfer urgent clinical questions to a human. Never give clinical advice.",
        model: { provider: "mock", model: "demo", temperature: 0.3, maxTokens: 400 },
        voice: {
          provider: voiceProvider,
          voiceId: voiceProvider === "sapi" ? "zira" : "demo",
          speed: 1,
        },
        transcriber: { provider: transcriberProvider, language: "en-US" },
        language: "en-US",
        tools: [bookingTool, transferTool, endTool],
        knowledgeBaseIds: [knowledgeBaseId],
        maxDurationSec: 600,
        silenceTimeoutSec: 12,
        endCallPhrases: ["goodbye", "that's all", "no thanks", "مع السلامة", "انهي المكالمة"],
        interruption: { enabled: true, minWords: 1 },
        recording: { enabled: false, consentAnnouncement: true },
        variables: { businessName: "Northwind Dental" },
      },
    };
    this.db.col("agents").insert(agent);
    for (const tool of agent.config.tools) this.db.col("tools").insert(tool);

    const phoneId = newId("num");
    this.db.col("phoneNumbers").insert({
      id: phoneId,
      tenantId,
      e164: "+15550001234",
      label: "Demo reception line (simulated)",
      provider: "simulated",
      simulated: true,
      inboundAgentId: agent.id,
      capabilities: ["voice", "dtmf"],
      createdAt: now,
      status: "active",
    });

    const ivrId = newId("ivr");
    this.db.col("ivrMenus").insert({
      id: ivrId,
      tenantId,
      name: "After-hours menu",
      prompt:
        "Thanks for calling Northwind Dental. For appointments, press 1. For opening hours, press 2. To leave a message, press 3.",
      invalidPrompt: "Sorry, I didn't catch that. For appointments press 1, for hours press 2, to leave a message press 3.",
      options: [
        { key: "1", label: "Appointments", action: "agent", target: agent.id },
        { key: "2", label: "Opening hours", action: "repeat" },
        { key: "3", label: "Voicemail", action: "voicemail" },
      ],
      timeoutSec: 8,
      maxAttempts: 3,
      createdAt: now,
    });

    const receptionist = this.installTemplate("ai_receptionist", tenantId);
    const activeReceptionist = this.db
      .col("workflows")
      .update(receptionist.id, { status: "active", name: "AI receptionist (demo)", version: 2 });
    this.recordWorkflowVersion(activeReceptionist, "system", "activated");

    const updatedSeedAgent = this.db.col("agents").update(agent.id, {
      config: { ...agent.config, postCallWorkflowId: receptionist.id },
    });
    this.recordAgentVersion(updatedSeedAgent, "system", "seed");

    this.installTemplate("task_ticket", tenantId);
    this.installTemplate("consent_followup", tenantId);

    if (this.db.col("apiKeys").count() === 0) {
      const key = await this.issueApiKey(tenantId, "local bootstrap");
      await mkdir(this.config.dataDir, { recursive: true });
      await writeFile(path.join(this.config.dataDir, "api-key.txt"), `${key.token}\n`, {
        encoding: "utf8",
        mode: 0o600,
      });
      this.logger.info("demo workspace created", {
        tenantId,
        agentId: agent.id,
        phone: "+15550001234",
        apiKeyFile: path.join(this.config.dataDir, "api-key.txt"),
      });
    }

    await this.db.flush();
  }

  private makeTool(
    tenantId: string,
    input: Omit<
      ToolDefinition,
      "id" | "tenantId" | "createdAt" | "updatedAt" | "description" | "parameters"
    > & { description: string; parameters: ToolDefinition["parameters"] },
  ): ToolDefinition {
    const now = nowIso();
    return { id: newId("tool"), tenantId, createdAt: now, updatedAt: now, ...input };
  }

  private demoVoiceProvider(): "sapi" | "mock" {
    const configured = process.env.OMALLA_DEMO_VOICE;
    if (configured === "mock" || configured === "sapi") return configured;
    return process.platform === "win32" ? "sapi" : "mock";
  }

  private demoTranscriberProvider(): "sapi" | "mock" {
    const configured = process.env.OMALLA_DEMO_STT;
    if (configured === "mock" || configured === "sapi") return configured;
    return "mock";
  }

  /* ------------------------------------------------------------------ */
  /* read models                                                         */
  /* ------------------------------------------------------------------ */

  metrics(tenantId: string): Record<string, JsonValue> {
    const calls = this.db.col("calls").list((call) => call.tenantId === tenantId);
    const ended = calls.filter((call) => call.status === "ended");
    const latencies = ended.flatMap((call) => call.metrics.turnLatenciesMs);
    const runs = this.db
      .col("workflowRuns")
      .list((run) => run.tenantId === tenantId);
    return {
      calls: calls.length,
      callsToday: calls.filter(
        (call) => Date.parse(call.startedAt) >= Date.now() - 24 * 60 * 60 * 1000,
      ).length,
      activeCalls: calls.filter((call) => call.status === "in_progress").length,
      avgTurnLatencyMs:
        latencies.length > 0
          ? Math.round(latencies.reduce((sum, value) => sum + value, 0) / latencies.length)
          : 0,
      interruptions: ended.reduce((sum, call) => sum + call.metrics.interruptions, 0),
      workflowRuns: runs.length,
      workflowFailures: runs.filter((run) => run.status === "failed").length,
      bookings: this.db.col("bookings").count((booking) => booking.tenantId === tenantId),
      openTasks: this.db
        .col("tasks")
        .count((task) => task.tenantId === tenantId && task.status !== "done"),
      escalations: this.db
        .col("escalations")
        .count((escalation) => escalation.tenantId === tenantId && escalation.status === "open"),
    };
  }

  templates(): Array<{ id: TemplateId; name: string; description: string; category: string }> {
    return Object.values(TEMPLATES).map(({ id, name, description, category }) => ({
      id,
      name,
      description,
      category,
    }));
  }

  async close(): Promise<void> {
    await this.db.close();
  }
}
