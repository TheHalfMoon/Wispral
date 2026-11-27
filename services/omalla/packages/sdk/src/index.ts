import {
  canonicalizeJcs,
  canonicalizeJcsFromRawJson,
  jcsSha256,
  jcsSha256FromRawJson,
  verifySignedWebhookRaw,
  type WebhookVerifyInput,
  type WebhookVerifyOutcome,
} from "@omalla/core";
import type {
  Agent,
  AgentVersion,
  ApiKey,
  Booking,
  Call,
  Contact,
  Credential,
  Escalation,
  EvaluationCase,
  JsonValue,
  KnowledgeBase,
  PhoneNumber,
  Principal,
  SmsMessage,
  Task,
  Tenant,
  TenantSettings,
  ToolDefinition,
  ToolExecutionResult,
  Workflow,
  WorkflowRun,
  WorkflowVersion,
} from "@omalla/core";

export {
  canonicalizeJcs,
  canonicalizeJcsFromRawJson,
  jcsSha256,
  jcsSha256FromRawJson,
  verifySignedWebhookRaw,
};
export type { WebhookVerifyInput, WebhookVerifyOutcome };

export interface OmallaClientOptions {
  /** e.g. `http://127.0.0.1:8787`. Trailing slashes are ignored. */
  baseUrl?: string;
  /** An `omk_…` API key. The CLI reads the data directory when omitted. */
  apiKey: string;
  fetch?: typeof fetch;
  /** Per-request timeout. Defaults to 30s; call simulation uses 120s. */
  timeoutMs?: number;
  /** Retries for idempotent GETs on network errors and 5xx. Default 2. */
  retries?: number;
  userAgent?: string;
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  timeoutMs?: number;
  signal?: AbortSignal;
  headers?: Record<string, string>;
  /** Sent as `Idempotency-Key` header; payload is JCS-validated before send. */
  idempotencyKey?: string;
}

export class OmallaApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly body?: unknown,
  ) {
    super(message);
    this.name = "OmallaApiError";
  }
}

export interface CallStreamEvent {
  type: string;
  callId: string;
  at: string;
  data: JsonValue;
}

export type StreamFrame = { type: "snapshot"; call: Call } | CallStreamEvent;

export interface CallStreamHandlers {
  onEvent?: (event: CallStreamEvent) => void;
  onSnapshot?: (call: Call) => void;
  onClose?: (reason: string) => void;
  onError?: (error: Error) => void;
}

/**
 * Verifies an Omalla (`x-omalla-signature` + `x-omalla-timestamp` ±300s) or
 * Standard Webhooks raw-byte HMAC signature via the canonical `@omalla/core` verifier.
 */
export function verifyWebhookSignature(input: WebhookVerifyInput): WebhookVerifyOutcome {
  return verifySignedWebhookRaw(input);
}

/**
 * Typed client for the Omalla HTTP & WebSocket API.
 */
export class OmallaClient {
  readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;
  private readonly retries: number;
  private readonly userAgent: string;

  constructor(options: OmallaClientOptions) {
    if (!options.apiKey) throw new Error("an API key is required");
    this.baseUrl = (options.baseUrl ?? "http://127.0.0.1:8787").replace(/\/+$/, "");
    this.apiKey = options.apiKey;
    this.fetchImpl = options.fetch ?? globalThis.fetch.bind(globalThis);
    this.timeoutMs = options.timeoutMs ?? 30_000;
    this.retries = options.retries ?? 2;
    this.userAgent = options.userAgent ?? "omalla-sdk/0.1.0";
  }

  /* ------------------------------------------------------------------ */
  /* transport                                                           */
  /* ------------------------------------------------------------------ */

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const method = options.method ?? "GET";
    const url = new URL(`${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}`);
    for (const [key, value] of Object.entries(options.query ?? {})) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }

    let argsDigest: string | undefined;
    if (options.idempotencyKey && options.body !== undefined) {
      argsDigest = jcsSha256(options.body);
    }

    const idempotent = method === "GET";
    const attempts = idempotent ? this.retries + 1 : 1;
    let lastError: unknown;

    for (let attempt = 0; attempt < attempts; attempt += 1) {
      const timeout = AbortSignal.timeout(options.timeoutMs ?? this.timeoutMs);
      const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout;
      try {
        const response = await this.fetchImpl(url, {
          method,
          signal,
          headers: {
            authorization: `Bearer ${this.apiKey}`,
            accept: "application/json",
            "user-agent": this.userAgent,
            ...(options.body !== undefined ? { "content-type": "application/json" } : {}),
            ...(options.idempotencyKey ? { "idempotency-key": options.idempotencyKey } : {}),
            ...(argsDigest ? { "x-omalla-args-digest": argsDigest } : {}),
            ...options.headers,
          },
          ...(options.body !== undefined ? { body: JSON.stringify(options.body) } : {}),
        });

        if (response.status === 204) return undefined as T;

        const text = await response.text();
        const payload = text ? safeJson(text) : null;

        if (!response.ok) {
          const error = readError(payload, response.status);
          if (idempotent && response.status >= 500 && attempt < attempts - 1) {
            lastError = error;
            await backoff(attempt);
            continue;
          }
          throw error;
        }
        return payload as T;
      } catch (error) {
        if (error instanceof OmallaApiError) throw error;
        lastError = error;
        if (attempt < attempts - 1) {
          await backoff(attempt);
          continue;
        }
        const message = error instanceof Error ? error.message : String(error);
        throw new OmallaApiError(`could not reach ${this.baseUrl}: ${message}`, 0, "network_error");
      }
    }
    throw lastError instanceof Error
      ? lastError
      : new OmallaApiError("request failed", 0, "network_error");
  }

  /* ------------------------------------------------------------------ */
  /* identity & tenant                                                   */
  /* ------------------------------------------------------------------ */

  async me(): Promise<{ principal: Principal; tenant?: Tenant }> {
    return this.request("/v1/me");
  }

  tenant = {
    updateSettings: (settings: Partial<TenantSettings>): Promise<Tenant> =>
      this.request("/v1/tenant/settings", { method: "PATCH", body: settings }),
  };

  async health(): Promise<{ ok: boolean; version: string; simulation: boolean }> {
    return this.request("/v1/health");
  }

  async metrics(): Promise<Record<string, JsonValue>> {
    return this.request("/v1/metrics");
  }

  async openapi(): Promise<Record<string, JsonValue>> {
    return this.request("/openapi.json");
  }

  keys = {
    list: (): Promise<Array<Omit<ApiKey, "hash">>> => this.request("/v1/keys"),
    create: (name: string, role: Principal["role"] = "operator"): Promise<{ id: string; token: string; prefix: string }> =>
      this.request("/v1/keys", { method: "POST", body: { name, role } }),
    revoke: (id: string): Promise<void> => this.request(`/v1/keys/${id}`, { method: "DELETE" }),
  };

  /* ------------------------------------------------------------------ */
  /* agents                                                              */
  /* ------------------------------------------------------------------ */

  agents = {
    list: (): Promise<Agent[]> => this.request("/v1/agents"),
    get: (id: string): Promise<Agent> => this.request(`/v1/agents/${id}`),
    create: (body: { name: string; description?: string; config?: Record<string, unknown> }): Promise<Agent> =>
      this.request("/v1/agents", { method: "POST", body }),
    update: (
      id: string,
      body: Partial<Pick<Agent, "name" | "description" | "status">> & { config?: Record<string, unknown> },
    ): Promise<Agent> => this.request(`/v1/agents/${id}`, { method: "PATCH", body }),
    publish: (id: string): Promise<Agent> =>
      this.request(`/v1/agents/${id}/publish`, { method: "POST" }),
    versions: (id: string): Promise<AgentVersion[]> =>
      this.request(`/v1/agents/${id}/versions`),
    test: (
      id: string,
      body: {
        callerTurns?: string[];
        variables?: Record<string, JsonValue>;
        version?: number;
        compareVersion?: number;
        expectations?: EvaluationCase["expectations"];
      } = {},
    ): Promise<Record<string, JsonValue>> =>
      this.request(`/v1/agents/${id}/test`, { method: "POST", body }),
    rollback: (id: string, version: number, note?: string): Promise<Agent> =>
      this.request(`/v1/agents/${id}/rollback`, {
        method: "POST",
        body: { version, ...(note ? { note } : {}) },
      }),
    remove: (id: string): Promise<void> => this.request(`/v1/agents/${id}`, { method: "DELETE" }),
  };

  /* ------------------------------------------------------------------ */
  /* calls                                                               */
  /* ------------------------------------------------------------------ */

  calls = {
    list: (query: { status?: string; limit?: number } = {}): Promise<Call[]> =>
      this.request("/v1/calls", { query: { ...query } }),
    get: (id: string): Promise<Call> => this.request(`/v1/calls/${id}`),
    simulate: (
      body: {
        to?: string;
        from?: string;
        variables?: Record<string, JsonValue>;
        say?: string[];
        press?: string[];
      },
      options: { idempotencyKey?: string } = {},
    ): Promise<Call> =>
      this.request("/v1/calls", {
        method: "POST",
        body,
        timeoutMs: 120_000,
        ...(options.idempotencyKey ? { idempotencyKey: options.idempotencyKey } : {}),
      }),
    outbound: (
      body: {
        to: string;
        agentId: string;
        consent: boolean;
        variables?: Record<string, JsonValue>;
        mode?: "simulated" | "carrier";
        provider?: PhoneNumber["provider"];
        from?: string;
      },
      options: { idempotencyKey?: string } = {},
    ): Promise<Call> =>
      this.request("/v1/calls/outbound", {
        method: "POST",
        body,
        ...(options.idempotencyKey ? { idempotencyKey: options.idempotencyKey } : {}),
      }),
    say: (id: string, text: string): Promise<Call> =>
      this.request(`/v1/calls/${id}/say`, { method: "POST", body: { text }, timeoutMs: 120_000 }),
    dtmf: (id: string, digits: string): Promise<Call> =>
      this.request(`/v1/calls/${id}/dtmf`, { method: "POST", body: { digits } }),
    hangup: (id: string): Promise<Call> =>
      this.request(`/v1/calls/${id}/hangup`, { method: "POST" }),

    stream: (id: string, handlers: CallStreamHandlers): (() => void) => {
      const wsBase = this.baseUrl.replace(/^http/, "ws");
      const url = `${wsBase}/v1/calls/${id}/stream?token=${encodeURIComponent(this.apiKey)}`;
      const Impl = (globalThis as { WebSocket?: typeof WebSocket }).WebSocket;
      if (!Impl) throw new Error("WebSocket is not available in this runtime");
      const socket = new Impl(url);

      socket.addEventListener("message", (message) => {
        let payload: { type?: string } & Record<string, unknown>;
        try {
          payload = JSON.parse(String(message.data));
        } catch {
          return;
        }
        if (payload.type === "snapshot") {
          handlers.onSnapshot?.(payload.call as Call);
          return;
        }
        handlers.onEvent?.(payload as unknown as CallStreamEvent);
      });
      socket.addEventListener("error", () => {
        handlers.onError?.(new Error("call stream failed"));
      });
      socket.addEventListener("close", (event) => {
        handlers.onClose?.((event as unknown as { reason?: string }).reason ?? "closed");
      });
      return () => socket.close();
    },

    /** Async-iterable event stream helper over `/v1/calls/:id/stream`. */
    streamEvents: async function* (
      this: unknown,
      client: OmallaClient,
      id: string,
      signal?: AbortSignal,
    ): AsyncGenerator<StreamFrame, void, undefined> {
      const queue: StreamFrame[] = [];
      let done = false;
      let err: Error | null = null;
      let wake: (() => void) | null = null;

      const notify = () => {
        const w = wake;
        wake = null;
        w?.();
      };

      const closeStream = client.calls.stream(id, {
        onSnapshot: (call) => {
          queue.push({ type: "snapshot", call });
          notify();
        },
        onEvent: (event) => {
          queue.push(event);
          if (event.type === "call.ended") done = true;
          notify();
        },
        onError: (e) => {
          err = e;
          done = true;
          notify();
        },
        onClose: () => {
          done = true;
          notify();
        },
      });

      const onAbort = () => {
        done = true;
        closeStream();
        notify();
      };
      signal?.addEventListener("abort", onAbort, { once: true });

      try {
        while (!done || queue.length > 0) {
          if (queue.length > 0) {
            yield queue.shift()!;
            continue;
          }
          if (err) throw err;
          if (done) break;
          await new Promise<void>((resolve) => {
            wake = resolve;
          });
        }
        if (err) throw err;
      } finally {
        signal?.removeEventListener("abort", onAbort);
        closeStream();
      }
    },
  };

  /** Convenience wrapper returning an `AsyncIterable<StreamFrame>` for a call. */
  iterateCallEvents(callId: string, signal?: AbortSignal): AsyncGenerator<StreamFrame, void, undefined> {
    return this.calls.streamEvents(this, callId, signal);
  }

  /* ------------------------------------------------------------------ */
  /* telephony                                                           */
  /* ------------------------------------------------------------------ */

  telephony = {
    providers: (): Promise<
      Array<{
        id: string;
        label: string;
        available: boolean;
        detail: string;
        requiredEnv: string[];
      }>
    > => this.request("/v1/telephony/providers"),
  };

  numbers = {
    list: (): Promise<PhoneNumber[]> => this.request("/v1/numbers"),
    search: (body: {
      provider?: PhoneNumber["provider"];
      countryCode?: string;
      areaCode?: string;
      contains?: string;
      limit?: number;
    } = {}): Promise<{
      provider: string;
      carrierCharges: boolean;
      offers: Array<{
        e164: string;
        friendlyName: string;
        locality?: string;
        region?: string;
        capabilities: Array<"voice" | "sms" | "mms">;
        costNote: string;
      }>;
    }> => this.request("/v1/numbers/search", { method: "POST", body }),
    provision: (body: {
      e164: string;
      label?: string;
      agentId?: string;
      ivrMenuId?: string;
      provider?: PhoneNumber["provider"];
      confirm: true;
    }): Promise<{
      number: PhoneNumber;
      billing: { carrierCharges: boolean; note: string };
    }> => this.request("/v1/numbers/provision", { method: "POST", body }),
    release: (id: string): Promise<{ released: boolean; id: string; e164: string }> =>
      this.request(`/v1/numbers/${id}`, { method: "DELETE", query: { confirm: true } }),
  };

  sms = {
    list: (query: { direction?: "inbound" | "outbound"; limit?: number } = {}): Promise<SmsMessage[]> =>
      this.request("/v1/sms", { query: { ...query } }),
    send: (
      body: {
        to: string;
        from?: string;
        body: string;
        provider?: PhoneNumber["provider"];
        consent: boolean;
      },
      options: { idempotencyKey?: string } = {},
    ): Promise<SmsMessage> =>
      this.request("/v1/sms", {
        method: "POST",
        body,
        ...(options.idempotencyKey ? { idempotencyKey: options.idempotencyKey } : {}),
      }),
  };

  /* ------------------------------------------------------------------ */
  /* workflows                                                           */
  /* ------------------------------------------------------------------ */

  workflows = {
    list: (): Promise<Workflow[]> => this.request("/v1/workflows"),
    get: (id: string): Promise<Workflow> => this.request(`/v1/workflows/${id}`),
    create: (body: {
      name: string;
      description?: string;
      status?: Workflow["status"];
      trigger?: Workflow["trigger"];
      nodes?: Workflow["nodes"];
      edges?: Workflow["edges"];
    }): Promise<Workflow> => this.request("/v1/workflows", { method: "POST", body }),
    update: (id: string, body: Partial<Workflow>): Promise<Workflow> =>
      this.request(`/v1/workflows/${id}`, { method: "PATCH", body }),
    versions: (id: string): Promise<WorkflowVersion[]> =>
      this.request(`/v1/workflows/${id}/versions`),
    test: (
      id: string,
      body: { payload?: JsonValue; version?: number; compareVersion?: number } = {},
    ): Promise<Record<string, JsonValue>> =>
      this.request(`/v1/workflows/${id}/test`, { method: "POST", body }),
    rollback: (id: string, version: number, note?: string): Promise<Workflow> =>
      this.request(`/v1/workflows/${id}/rollback`, {
        method: "POST",
        body: { version, ...(note ? { note } : {}) },
      }),
    remove: (id: string): Promise<void> => this.request(`/v1/workflows/${id}`, { method: "DELETE" }),
    run: (
      id: string,
      body: { payload?: JsonValue; dryRun?: boolean; idempotencyKey?: string } = {},
      options: { idempotencyKey?: string } = {},
    ): Promise<WorkflowRun> =>
      this.request(`/v1/workflows/${id}/run`, {
        method: "POST",
        body,
        timeoutMs: 120_000,
        ...(options.idempotencyKey ? { idempotencyKey: options.idempotencyKey } : {}),
      }),
    runs: (id: string): Promise<WorkflowRun[]> => this.request(`/v1/workflows/${id}/runs`),
    importN8n: (workflow: unknown): Promise<{ workflow: Workflow; warnings: string[] }> =>
      this.request("/v1/workflows/import/n8n", { method: "POST", body: { workflow } }),
    exportN8n: (id: string): Promise<unknown> => this.request(`/v1/workflows/${id}/export/n8n`),
  };

  runs = {
    list: (): Promise<WorkflowRun[]> => this.request("/v1/runs"),
  };

  templates = {
    list: (): Promise<Array<{ id: string; name: string; description: string; category: string }>> =>
      this.request("/v1/templates"),
    install: (id: string, activate = false): Promise<Workflow> =>
      this.request(`/v1/templates/${id}/install`, { method: "POST", body: { activate } }),
  };

  /* ------------------------------------------------------------------ */
  /* tools and knowledge                                                 */
  /* ------------------------------------------------------------------ */

  tools = {
    list: (): Promise<ToolDefinition[]> => this.request("/v1/tools"),
    create: (body: Omit<ToolDefinition, "id" | "tenantId" | "createdAt" | "updatedAt">): Promise<ToolDefinition> =>
      this.request("/v1/tools", { method: "POST", body }),
    update: (id: string, body: Partial<ToolDefinition>): Promise<ToolDefinition> =>
      this.request(`/v1/tools/${id}`, { method: "PATCH", body }),
    remove: (id: string): Promise<void> => this.request(`/v1/tools/${id}`, { method: "DELETE" }),
    test: (
      id: string,
      args: Record<string, JsonValue> = {},
    ): Promise<ToolExecutionResult> =>
      this.request(`/v1/tools/${id}/test`, { method: "POST", body: { args } }),
  };

  knowledge = {
    list: (): Promise<KnowledgeBase[]> => this.request("/v1/knowledge-bases"),
    create: (body: { name: string; description?: string }): Promise<KnowledgeBase> =>
      this.request("/v1/knowledge-bases", { method: "POST", body }),
    addDocument: (
      id: string,
      body: { title: string; text: string },
    ): Promise<KnowledgeBase["documents"][number]> =>
      this.request(`/v1/knowledge-bases/${id}/documents`, { method: "POST", body }),
    search: (
      id: string,
      query: string,
      limit = 5,
    ): Promise<{ hits: Array<{ documentId: string; title: string; text: string; score: number }> }> =>
      this.request(`/v1/knowledge-bases/${id}/search`, { method: "POST", body: { query, limit } }),
  };

  /* ------------------------------------------------------------------ */
  /* local automation records                                            */
  /* ------------------------------------------------------------------ */

  tasks = {
    list: (): Promise<Task[]> => this.request("/v1/tasks"),
    create: (body: {
      title: string;
      description?: string;
      priority?: Task["priority"];
      labels?: string[];
      dueAt?: string;
      assignee?: string;
    }): Promise<Task> => this.request("/v1/tasks", { method: "POST", body }),
    update: (id: string, body: Partial<Pick<Task, "title" | "description" | "status" | "priority" | "assignee">>): Promise<Task> =>
      this.request(`/v1/tasks/${id}`, { method: "PATCH", body }),
  };

  bookings = {
    list: (): Promise<Booking[]> => this.request("/v1/bookings"),
    create: (body: {
      name: string;
      title?: string;
      when: string;
      durationMin?: number;
      phone?: string;
      email?: string;
      notes?: string;
    }): Promise<Booking> => this.request("/v1/bookings", { method: "POST", body }),
    update: (id: string, status: Booking["status"]): Promise<Booking> =>
      this.request(`/v1/bookings/${id}`, { method: "PATCH", body: { status } }),
  };

  contacts = {
    list: (): Promise<Contact[]> => this.request("/v1/contacts"),
  };

  escalations = {
    list: (): Promise<Escalation[]> => this.request("/v1/escalations"),
    update: (id: string, status: Escalation["status"]): Promise<Escalation> =>
      this.request(`/v1/escalations/${id}`, { method: "PATCH", body: { status } }),
  };

  /* ------------------------------------------------------------------ */
  /* credentials                                                         */
  /* ------------------------------------------------------------------ */

  credentials = {
    list: (): Promise<Array<Omit<Credential, "ciphertext">>> => this.request("/v1/credentials"),
    set: (name: string, value: string, provider = "custom"): Promise<{ ok: boolean; name: string }> =>
      this.request(`/v1/credentials/${encodeURIComponent(name)}`, {
        method: "PUT",
        body: { value, provider },
      }),
    remove: (name: string): Promise<void> =>
      this.request(`/v1/credentials/${encodeURIComponent(name)}`, { method: "DELETE" }),
  };

  /* ------------------------------------------------------------------ */
  /* webhooks                                                            */
  /* ------------------------------------------------------------------ */

  async webhook(
    path: string,
    payload: JsonValue,
    options: { signature?: string; idempotencyKey?: string; webhookId?: string; webhookTimestamp?: string } = {},
  ): Promise<{ runId: string; status: string }> {
    return this.request(`/v1/hooks/${path}`, {
      method: "POST",
      body: payload,
      ...(options.idempotencyKey ? { idempotencyKey: options.idempotencyKey } : {}),
      headers: {
        ...(options.signature ? { "x-omalla-signature": options.signature } : {}),
        ...(options.webhookId ? { "webhook-id": options.webhookId } : {}),
        ...(options.webhookTimestamp ? { "webhook-timestamp": options.webhookTimestamp } : {}),
      },
    });
  }
}

/** Parses newline-delimited or WebSocket JSON stream frames into typed events. */
export function parseStreamFrames(rawLines: Iterable<string>): StreamFrame[] {
  const out: StreamFrame[] = [];
  for (const line of rawLines) {
    const trimmed = line.replace(/^data:\s*/, "").trim();
    if (!trimmed) continue;
    const parsed = JSON.parse(trimmed) as StreamFrame;
    out.push(parsed);
  }
  return out;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function readError(payload: unknown, status: number): OmallaApiError {
  const candidate = payload as { error?: { code?: string; message?: string } } | null;
  const message = candidate?.error?.message ?? `request failed with status ${status}`;
  const code = candidate?.error?.code ?? "http_error";
  return new OmallaApiError(message, status, code, payload);
}

function backoff(attempt: number): Promise<void> {
  const ms = 150 * 2 ** attempt + Math.random() * 80;
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function createClient(options: OmallaClientOptions): OmallaClient {
  return new OmallaClient(options);
}
