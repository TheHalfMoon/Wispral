import { createHmac } from "node:crypto";
import { OmallaError, createRetriever, evaluateUrl, nowIso } from "@omalla/core";
import type {
  Database,
  JsonValue,
  Logger,
  ToolCallContext,
  ToolDefinition,
  ToolExecutionResult,
  ToolExecutor,
  ToolInvocation,
  UrlPolicyOptions,
} from "@omalla/core";
import type { CredentialService } from "./credentials.js";
import type { LocalAutomationStore } from "./automation-store.js";
import { parseSpokenDateTime } from "./parse-when.js";
import { createSsrfGuardedFetch, type DnsLookupAll } from "./ssrf-guard.js";

export interface ToolRuntimeDeps {
  db: Database;
  credentials: CredentialService;
  store: LocalAutomationStore;
  logger: Logger;
  urlPolicy: UrlPolicyOptions;
  fetch?: typeof fetch;
  dnsLookup?: DnsLookupAll;
  now?: () => Date;
  /** Runs a native Omalla workflow synchronously for the `workflow` tool. */
  runWorkflow?: (input: {
    tenantId: string;
    workflowId: string;
    payload: Record<string, JsonValue>;
    callId?: string;
    idempotencyKey: string;
  }) => Promise<{ runId: string; status: string; output: JsonValue }>;
}

const MAX_RESPONSE_BYTES = 64_000;
const DEFAULT_TIMEOUT_MS = 10_000;
const HIGH_RISK_NAME_PATTERN = /(account|campaign|billing|refund|wire.?transfer|payout)/i;

/**
 * Executes the tools an agent declares.
 *
 * Security invariants enforced deterministically:
 *  - OM-T1: tool & knowledge-base lookups are strictly scoped to `context.tenantId`.
 *  - OM-T2: `callerNumberVerified` is always server-derived (`false` unless trunk
 *    attestation verified ANI); high-risk account/campaign tools cannot authorize
 *    on unverified `callerNumber` alone.
 *  - OM-T4: every outbound HTTP/MCP/n8n request passes connect-time pinned-DNS SSRF guard.
 */
export class ToolRuntime implements ToolExecutor {
  private readonly safeFetch: typeof fetch;

  constructor(private readonly deps: ToolRuntimeDeps) {
    this.safeFetch = createSsrfGuardedFetch({
      ...deps.urlPolicy,
      ...(deps.fetch ? { baseFetch: deps.fetch } : {}),
      ...(deps.dnsLookup ? { lookup: deps.dnsLookup } : {}),
    });
  }

  async execute(invocation: ToolInvocation): Promise<ToolExecutionResult> {
    const started = Date.now();
    const tool = this.resolveTool(invocation);
    if (!tool) {
      return { ok: false, error: `unknown tool: ${invocation.name}`, latencyMs: 0 };
    }

    const callerNumberVerified = invocation.context.trusted.callerNumberVerified === true;
    const secondaryVerified = invocation.context.trusted.callerVerifiedSecondary === true;

    const isHighRisk =
      tool.riskLevel === "high" ||
      tool.requiresVerifiedCaller === true ||
      (tool.riskLevel !== "low" && HIGH_RISK_NAME_PATTERN.test(tool.name));

    if (isHighRisk && !callerNumberVerified && !secondaryVerified) {
      this.deps.logger.warn("blocked high-risk tool on unverified caller ANI (OM-T2)", {
        tool: tool.name,
        callId: invocation.context.callId,
        tenantId: invocation.context.tenantId,
      });
      return {
        ok: false,
        error: `tool '${tool.name}' blocked: high-risk action cannot authorize on unverified caller ANI (OM-T2)`,
        retryable: false,
        latencyMs: Date.now() - started,
      };
    }

    const merged = {
      ...invocation.args,
      ...(tool.trustedFields ?? {}),
      ...invocation.context.trusted,
      tenantId: invocation.context.tenantId,
      callId: invocation.context.callId,
      callerNumber: invocation.context.callerNumber,
      callerNumberVerified,
    } as Record<string, JsonValue>;

    if (invocation.dryRun === true) {
      const candidateUrl = tool.serverUrl
        ? applyTemplate(tool.serverUrl, merged)
        : tool.mcpServerUrl;
      if (candidateUrl) {
        const check = evaluateUrl(candidateUrl, this.deps.urlPolicy);
        if (!check.allowed) {
          return {
            ok: false,
            error: `SSRF guard blocked URL: ${check.reason ?? "disallowed"}`,
            retryable: false,
            latencyMs: Date.now() - started,
          };
        }
      }
      if (tool.type === "query") {
        const qResult = this.query(tool, merged, invocation.context);
        return { ...qResult, latencyMs: Date.now() - started };
      }
      return {
        ok: true,
        result: {
          simulated: true,
          dryRun: true,
          tool: tool.name,
          type: tool.type,
          args: merged,
        },
        latencyMs: Date.now() - started,
      };
    }

    try {
      const result = await this.dispatch(tool, merged, invocation.context, invocation.signal);
      return { ...result, latencyMs: Date.now() - started };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.deps.logger.warn("tool execution failed", {
        tool: tool.name,
        callId: invocation.context.callId,
        error: message,
      });
      return {
        ok: false,
        error: message,
        retryable: error instanceof OmallaError ? error.code === "timeout" : false,
        latencyMs: Date.now() - started,
      };
    }
  }

  private resolveTool(invocation: ToolInvocation): ToolDefinition | undefined {
    const tenantId = invocation.context.tenantId;
    const stored = this.deps.db.col("tools").get(invocation.toolId);
    if (stored) {
      return stored.tenantId === tenantId ? stored : undefined;
    }
    const agent = this.deps.db.col("agents").get(invocation.context.agentId);
    if (!agent || agent.tenantId !== tenantId) return undefined;
    const inline = agent.config.tools.find(
      (tool) => tool.id === invocation.toolId || tool.name === invocation.name,
    );
    if (inline && inline.tenantId && inline.tenantId !== tenantId) return undefined;
    return inline;
  }

  private async dispatch(
    tool: ToolDefinition,
    args: Record<string, JsonValue>,
    context: ToolCallContext,
    signal?: AbortSignal,
  ): Promise<ToolExecutionResult> {
    switch (tool.type) {
      case "function":
      case "api_request":
        return this.callApi(tool, args, signal);

      case "transfer": {
        const requested = String(args.destination ?? args.to ?? tool.destinations?.[0] ?? "");
        const allowed = tool.destinations ?? [];
        if (!requested) return { ok: false, error: "no transfer destination was provided" };
        if (allowed.length > 0 && !allowed.includes(requested)) {
          return { ok: false, error: `destination ${requested} is not permitted by this tool` };
        }
        return {
          ok: true,
          result: { transferringTo: requested },
          speech: tool.messages?.onResult ?? "One moment, I'm transferring you now.",
          control: { kind: "transfer", destination: requested, mode: "blind" },
        };
      }

      case "handoff": {
        const requested = String(args.agentId ?? tool.destinations?.[0] ?? "");
        const allowed = tool.destinations ?? [];
        if (!requested) return { ok: false, error: "no handoff agent was provided" };
        if (allowed.length > 0 && !allowed.includes(requested)) {
          return { ok: false, error: `agent ${requested} is not permitted by this tool` };
        }
        const targetAgent = this.deps.db.col("agents").get(requested);
        if (targetAgent && targetAgent.tenantId !== context.tenantId) {
          return { ok: false, error: "handoff agent not found" };
        }
        return {
          ok: true,
          result: { handoffAgentId: requested },
          speech: tool.messages?.onResult ?? "I'll hand you to a specialist now.",
          control: { kind: "handoff", agentId: requested },
        };
      }

      case "end_call":
        return {
          ok: true,
          result: { ended: true },
          speech: tool.messages?.onResult ?? "Thanks for calling. Goodbye.",
          control: { kind: "end_call" },
        };

      case "dtmf": {
        const keys = String(args.keys ?? "").replace(/[^0-9*#wW,]/g, "");
        if (!keys) return { ok: false, error: "no DTMF keys were provided" };
        return { ok: true, result: { keys }, control: { kind: "dtmf", keys } };
      }

      case "query":
        return this.query(tool, args, context);

      case "mcp":
        return this.callMcp(tool, args, context, signal);

      case "n8n_workflow":
        return this.callN8n(tool, args, context, signal);

      case "workflow":
        return this.callWorkflow(tool, args, context);

      case "internal":
        return this.internal(tool, args, context);

      default:
        return { ok: false, error: `unsupported tool type: ${String(tool.type)}` };
    }
  }

  private async callApi(
    tool: ToolDefinition,
    args: Record<string, JsonValue>,
    signal?: AbortSignal,
  ): Promise<ToolExecutionResult> {
    if (!tool.serverUrl) return { ok: false, error: "tool has no server URL" };
    const url = applyTemplate(tool.serverUrl, args);

    const timeout = AbortSignal.timeout(tool.timeoutMs ?? DEFAULT_TIMEOUT_MS);
    const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;
    const method = tool.method ?? "POST";
    const headers: Record<string, string> = {
      "content-type": "application/json",
      ...Object.fromEntries(
        Object.entries(tool.headers ?? {}).map(([key, value]) => [key, applyTemplate(value, args)]),
      ),
    };

    const body =
      method === "GET"
        ? undefined
        : JSON.stringify({ ...(tool.staticBody ?? {}), ...args });

    const response = await this.safeFetch(url, {
      method,
      headers,
      ...(body ? { body } : {}),
      signal: combined,
    });
    const text = (await response.text()).slice(0, MAX_RESPONSE_BYTES);
    let parsed: JsonValue = text;
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      try {
        parsed = JSON.parse(text) as JsonValue;
      } catch {
        parsed = text;
      }
    }

    if (!response.ok) {
      return {
        ok: false,
        error: `upstream returned ${response.status}`,
        result: { status: response.status, body: parsed },
        retryable: response.status >= 500 || response.status === 429,
      };
    }
    return { ok: true, result: parsed };
  }

  private query(
    tool: ToolDefinition,
    args: Record<string, JsonValue>,
    context: ToolCallContext,
  ): ToolExecutionResult {
    if (tool.tenantId && tool.tenantId !== context.tenantId) {
      return { ok: false, error: "knowledge base is not configured" };
    }
    const knowledgeBase = tool.knowledgeBaseId
      ? this.deps.db.col("knowledgeBases").get(tool.knowledgeBaseId)
      : undefined;
    // OM-T1: enforce strict tenant match on KB read
    if (!knowledgeBase || knowledgeBase.tenantId !== context.tenantId) {
      return { ok: false, error: "knowledge base is not configured" };
    }
    const query = String(args.query ?? args.q ?? "");
    if (!query) return { ok: false, error: "query is empty" };
    const retriever = createRetriever(
      knowledgeBase.documents.map((document) => ({
        id: document.id,
        title: document.title,
        text: document.text,
      })),
    );
    const hits = retriever.search(query, 5);
    return {
      ok: true,
      result: {
        hits: hits.map((hit) => ({
          documentId: hit.documentId,
          title: hit.title,
          text: hit.text.slice(0, 1200),
          score: hit.score,
        })),
      },
    };
  }

  private async callN8n(
    tool: ToolDefinition,
    args: Record<string, JsonValue>,
    context: ToolCallContext,
    signal?: AbortSignal,
  ): Promise<ToolExecutionResult> {
    if (!tool.serverUrl) {
      return { ok: false, error: "n8n_workflow needs a published production webhook URL" };
    }
    const url = applyTemplate(tool.serverUrl, args);
    const callerNumberVerified = context.trusted.callerNumberVerified === true;

    const payload = {
      ...(tool.staticBody ?? {}),
      ...args,
      omalla: {
        callId: context.callId,
        tenantId: context.tenantId,
        agentId: context.agentId,
        callerNumber: context.callerNumber,
        callerNumberVerified,
        tool: tool.name,
        event: "voice_tool",
        timestamp: nowIso(),
      },
    };
    const body = JSON.stringify(payload);
    const secret = await this.deps.credentials.get(context.tenantId, "N8N_WEBHOOK_SECRET");
    const signature = secret
      ? createHmac("sha256", secret).update(body).digest("hex")
      : undefined;

    const method = tool.method ?? "POST";
    const timeout = AbortSignal.timeout(tool.timeoutMs ?? DEFAULT_TIMEOUT_MS);
    const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;
    const response = await this.safeFetch(url, {
      method,
      headers: {
        "content-type": "application/json",
        accept: "application/json",
        ...(signature ? { "x-omalla-signature": `sha256=${signature}` } : {}),
        ...Object.fromEntries(
          Object.entries(tool.headers ?? {}).map(([key, value]) => [key, applyTemplate(value, args)]),
        ),
      },
      ...(method === "GET" ? {} : { body }),
      signal: combined,
    });

    const text = (await response.text()).slice(0, MAX_RESPONSE_BYTES);
    let parsed: JsonValue = text;
    if ((response.headers.get("content-type") ?? "").includes("application/json")) {
      try {
        parsed = JSON.parse(text) as JsonValue;
      } catch {
        parsed = text;
      }
    }
    if (!response.ok) {
      return {
        ok: false,
        error: `n8n returned ${response.status}`,
        result: { status: response.status, body: parsed },
        retryable: response.status >= 500 || response.status === 429,
      };
    }

    const speechField = extractSpeech(parsed);
    return {
      ok: true,
      result: parsed,
      ...(speechField ? { speech: speechField } : {}),
    };
  }

  /** Runs a native Omalla workflow during a live call, with no n8n needed. */
  private async callWorkflow(
    tool: ToolDefinition,
    args: Record<string, JsonValue>,
    context: ToolCallContext,
  ): Promise<ToolExecutionResult> {
    if (!tool.workflowId) return { ok: false, error: "workflow tool has no workflowId" };
    if (!this.deps.runWorkflow) {
      return { ok: false, error: "the workflow engine is not available in this runtime" };
    }
    const result = await this.deps.runWorkflow({
      tenantId: context.tenantId,
      workflowId: tool.workflowId,
      payload: {
        ...args,
        callerNumber: context.callerNumber,
        callerNumberVerified: context.trusted.callerNumberVerified === true,
      },
      callId: context.callId,
      idempotencyKey: `tool:${context.callId}:${tool.id}`,
    });
    if (result.status === "skipped") {
      return {
        ok: true,
        result: { runId: result.runId, output: result.output, deduplicated: true },
      };
    }
    if (result.status !== "succeeded") {
      return { ok: false, error: `workflow ${result.runId} finished as ${result.status}`, result: result.output };
    }
    const speechField = extractSpeech(result.output);
    return {
      ok: true,
      result: { runId: result.runId, output: result.output },
      ...(speechField ? { speech: speechField } : {}),
    };
  }

  private async callMcp(
    tool: ToolDefinition,
    args: Record<string, JsonValue>,
    context: ToolCallContext,
    signal?: AbortSignal,
  ): Promise<ToolExecutionResult> {
    if (!tool.mcpServerUrl) return { ok: false, error: "MCP server URL is missing" };
    const headers: Record<string, string> = {
      "content-type": "application/json",
      accept: "application/json, text/event-stream",
    };
    const token = await this.deps.credentials.get(context.tenantId, "MCP_TOKEN");
    if (token) headers.authorization = `Bearer ${token}`;

    const endpoint = tool.mcpServerUrl;
    const invoke = async (payload: Record<string, unknown>) => {
      const response = await this.safeFetch(endpoint, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
        signal: signal ?? AbortSignal.timeout(tool.timeoutMs ?? DEFAULT_TIMEOUT_MS),
      });
      if (!response.ok) throw new Error(`MCP returned ${response.status}`);
      const session = response.headers.get("mcp-session-id");
      if (session) headers["mcp-session-id"] = session;
      const raw = await response.text();
      const dataLine = raw
        .split("\n")
        .find((line) => line.startsWith("data:"));
      const json = JSON.parse(dataLine ? dataLine.slice(5).trim() : raw) as {
        result?: { content?: Array<{ type?: string; text?: string }> };
        error?: { message?: string };
      };
      return json;
    };

    await invoke({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2025-06-18",
        capabilities: {},
        clientInfo: { name: "omalla", version: "0.1.0" },
      },
    }).catch(() => undefined);

    const result = await invoke({
      jsonrpc: "2.0",
      id: 2,
      method: "tools/call",
      params: { name: tool.name, arguments: args },
    });
    if (result.error) return { ok: false, error: result.error.message ?? "MCP tool failed" };
    const text = (result.result?.content ?? [])
      .filter((item) => item.type === "text")
      .map((item) => item.text ?? "")
      .join("\n");
    return { ok: true, result: { text } };
  }

  private async internal(
    tool: ToolDefinition,
    args: Record<string, JsonValue>,
    context: ToolCallContext,
  ): Promise<ToolExecutionResult> {
    const tenantId = context.tenantId;
    switch (tool.internalAction) {
      case "create_booking": {
        const name = String(args.name ?? "").trim();
        const rawWhen = String(args.when ?? args.startAt ?? "").trim();
        if (!name) return { ok: false, error: "the caller's name is required to book" };
        const parsed = rawWhen ? parseSpokenDateTime(rawWhen, this.deps.now?.() ?? new Date()) : null;
        if (!parsed) return { ok: false, error: "a specific day and time is required to book" };
        const booking = await this.deps.store.createBooking({
          tenantId,
          title: String(args.title ?? "Appointment"),
          name,
          startAt: parsed.iso,
          durationMin: Number(args.durationMin ?? 30),
          ...(args.phone ? { phone: String(args.phone) } : { phone: context.callerNumber }),
          ...(args.email ? { email: String(args.email) } : {}),
          ...(args.notes ? { notes: String(args.notes) } : {}),
          callId: context.callId,
        });
        return { ok: true, result: booking };
      }

      case "create_task": {
        const title = String(args.title ?? "Follow up").slice(0, 300);
        const task = await this.deps.store.createTask({
          tenantId,
          title,
          description: String(args.description ?? ""),
          priority: normalizePriority(args.priority),
          labels: splitList(args.labels),
          ...(args.dueAt ? { dueAt: String(args.dueAt) } : {}),
          callId: context.callId,
        });
        return { ok: true, result: task };
      }

      case "upsert_contact": {
        const name = String(args.name ?? "").trim();
        if (!name) return { ok: false, error: "contact name is required" };
        const contact = await this.deps.store.upsertContact({
          tenantId,
          name,
          tags: splitList(args.tags),
          attributes: {},
          ...(args.email ? { email: String(args.email) } : {}),
          ...(args.phone ? { phone: String(args.phone) } : { phone: context.callerNumber }),
        });
        return { ok: true, result: contact };
      }

      case "escalate": {
        const reason = String(args.reason ?? "Caller requested a human");
        await this.deps.store.escalate({
          runId: context.callId,
          tenantId,
          reason,
          context: { ...context.variables, callerNumber: context.callerNumber },
        });
        return { ok: true, result: { escalated: true, reason } };
      }

      case "lookup_order": {
        const orderId = String(args.orderId ?? args.id ?? "");
        if (!orderId) return { ok: false, error: "order id is required" };
        const base = process.env.OMALLA_ORDER_LOOKUP_URL;
        if (!base) {
          return {
            ok: true,
            result: {
              orderId,
              status: "simulated",
              message: "Order lookup is running in simulation because no lookup service is configured.",
            },
          };
        }
        const url = `${base.replace(/\/$/, "")}/${encodeURIComponent(orderId)}`;
        const response = await this.safeFetch(url, {
          signal: AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
        });
        if (!response.ok) return { ok: false, error: `lookup returned ${response.status}` };
        return { ok: true, result: (await response.json()) as JsonValue };
      }

      default:
        return { ok: false, error: "unknown internal action" };
    }
  }
}

function extractSpeech(value: JsonValue | undefined): string | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  for (const key of ["speech", "message", "reply", "answer", "text"]) {
    const candidate = (value as Record<string, JsonValue>)[key];
    if (typeof candidate === "string" && candidate.trim()) return candidate.slice(0, 1200);
  }
  return undefined;
}

function applyTemplate(template: string, args: Record<string, JsonValue>): string {
  return template.replace(/\{\{\s*([A-Za-z0-9_]+)\s*\}\}/g, (_match, key: string) => {
    const value = args[key];
    if (value === undefined || value === null) return "";
    return typeof value === "object" ? JSON.stringify(value) : String(value);
  });
}

function splitList(value: JsonValue | undefined): string[] {
  if (Array.isArray(value)) return value.map(String).filter(Boolean);
  if (typeof value === "string") return value.split(",").map((item) => item.trim()).filter(Boolean);
  return [];
}

function normalizePriority(value: JsonValue | undefined): "low" | "normal" | "high" | "urgent" {
  const text = String(value ?? "normal").toLowerCase();
  return text === "low" || text === "high" || text === "urgent" ? text : "normal";
}

export function nowIsoSafe(): string {
  return nowIso();
}
