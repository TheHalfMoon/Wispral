import { createInterface } from "node:readline";
import type { JsonValue } from "@omalla/core";
import type { OmallaClient } from "@omalla/sdk";

export const PROTOCOL_VERSION = "2025-06-18";
export const SERVER_INFO = { name: "omalla", version: "0.1.0" } as const;

type JsonObject = Record<string, JsonValue>;

interface McpTool {
  name: string;
  description: string;
  inputSchema: JsonObject;
  handler: (args: JsonObject) => Promise<unknown>;
}

interface JsonRpcRequest {
  jsonrpc: "2.0";
  id?: string | number | null;
  method: string;
  params?: JsonObject;
}

export interface McpServerOptions {
  client: OmallaClient;
  input?: NodeJS.ReadableStream;
  output?: NodeJS.WritableStream;
  /** Diagnostics only; must never be stdout, which carries the protocol. */
  log?: (message: string) => void;
}

/**
 * Agent-driven automation surface.
 *
 * These tools let an external agent (Claude, Codex, an n8n AI node) discover
 * what the workspace can do and act on it: inspect calls, run workflows, book
 * appointments and escalate to a human. Everything routes through the same
 * authenticated REST API the dashboard uses, so tenant isolation, role checks
 * and SSRF policy apply unchanged.
 */
export function buildTools(api: OmallaClient): McpTool[] {
  return [
    {
      name: "omalla_list_calls",
      description: "List recent voice calls with status, direction and duration.",
      inputSchema: {
        type: "object",
        properties: {
          limit: { type: "integer", description: "How many calls to return (1-100).", default: 20 },
          status: { type: "string", description: "Filter by status, e.g. ended or in_progress." },
        },
      },
      handler: async (args) => {
        const calls = await api.calls.list({
          limit: typeof args.limit === "number" ? args.limit : 20,
          ...(typeof args.status === "string" ? { status: args.status } : {}),
        });
        return calls.map((call) => ({
          id: call.id,
          from: call.from,
          to: call.to,
          status: call.status,
          direction: call.direction,
          startedAt: call.startedAt,
          durationSec: call.endedAt
            ? Math.round((Date.parse(call.endedAt) - Date.parse(call.startedAt)) / 1000)
            : null,
          turns: call.metrics.turnCount,
          toolCalls: call.metrics.toolCalls,
          endedReason: call.endedReason ?? null,
        }));
      },
    },
    {
      name: "omalla_get_call",
      description: "Read one call with its full transcript and tool activity.",
      inputSchema: {
        type: "object",
        properties: { call_id: { type: "string", description: "The call id." } },
        required: ["call_id"],
      },
      handler: async (args) => {
        const call = await api.calls.get(String(args.call_id ?? ""));
        return {
          id: call.id,
          status: call.status,
          from: call.from,
          to: call.to,
          transcript: call.transcript.map((turn) => ({ role: turn.role, text: turn.text })),
          metrics: call.metrics,
          endedReason: call.endedReason ?? null,
        };
      },
    },
    {
      name: "omalla_start_simulated_call",
      description:
        "Start an inbound call against the local carrier simulator. No real phone rings. Provide caller lines in order; the agent answers each one.",
      inputSchema: {
        type: "object",
        properties: {
          from: { type: "string", description: "Caller number, E.164. Defaults to +15550112233." },
          to: { type: "string", description: "Business number. Defaults to the seeded demo line." },
          say: {
            type: "array",
            items: { type: "string" },
            description: "Caller utterances, spoken in order.",
          },
        },
      },
      handler: async (args) => {
        const call = await api.calls.simulate({
          ...(typeof args.from === "string" ? { from: args.from } : {}),
          ...(typeof args.to === "string" ? { to: args.to } : {}),
          ...(Array.isArray(args.say) ? { say: args.say.map(String) } : {}),
        });
        return {
          id: call.id,
          status: call.status,
          transcript: call.transcript.map((turn) => ({ role: turn.role, text: turn.text })),
        };
      },
    },
    {
      name: "omalla_list_workflows",
      description: "List installed automation workflows, their trigger and status.",
      inputSchema: { type: "object", properties: {} },
      handler: async () =>
        (await api.workflows.list()).map((workflow) => ({
          id: workflow.id,
          name: workflow.name,
          status: workflow.status,
          trigger: workflow.trigger,
          version: workflow.version,
        })),
    },
    {
      name: "omalla_run_workflow",
      description:
        "Run a workflow now with a JSON payload. Use dry_run to record external HTTP calls without sending them.",
      inputSchema: {
        type: "object",
        properties: {
          workflow_id: { type: "string" },
          payload: { type: "object", description: "Trigger payload available as {{trigger.*}}." },
          dry_run: { type: "boolean", default: false },
        },
        required: ["workflow_id"],
      },
      handler: async (args) => {
        const run = await api.workflows.run(String(args.workflow_id ?? ""), {
          payload: (args.payload ?? {}) as JsonValue,
          dryRun: args.dry_run === true,
        });
        return {
          id: run.id,
          status: run.status,
          error: run.error ?? null,
          steps: run.steps.map((step) => ({
            nodeId: step.nodeId,
            nodeType: step.nodeType,
            status: step.status,
            error: step.error ?? null,
          })),
        };
      },
    },
    {
      name: "omalla_list_templates",
      description: "List the nine shipped automation templates.",
      inputSchema: { type: "object", properties: {} },
      handler: async () => api.templates.list() as unknown as JsonValue,
    },
    {
      name: "omalla_install_template",
      description: "Install a template as a new workflow in this workspace.",
      inputSchema: {
        type: "object",
        properties: {
          template_id: { type: "string" },
          activate: { type: "boolean", default: false },
        },
        required: ["template_id"],
      },
      handler: async (args) => {
        const workflow = await api.templates.install(
          String(args.template_id ?? ""),
          args.activate === true,
        );
        return { id: workflow.id, name: workflow.name, status: workflow.status };
      },
    },
    {
      name: "omalla_create_task",
      description:
        "Create a follow-up task in the local board. Use this when a caller needs work done after the call.",
      inputSchema: {
        type: "object",
        properties: {
          title: { type: "string" },
          description: { type: "string" },
          priority: { type: "string", enum: ["low", "normal", "high", "urgent"] },
          labels: { type: "array", items: { type: "string" } },
        },
        required: ["title"],
      },
      handler: async (args) => {
        const task = await api.tasks.create({
          title: String(args.title ?? ""),
          ...(typeof args.description === "string" ? { description: args.description } : {}),
          ...(typeof args.priority === "string"
            ? { priority: args.priority as "low" | "normal" | "high" | "urgent" }
            : {}),
          ...(Array.isArray(args.labels) ? { labels: args.labels.map(String) } : {}),
        });
        return task as unknown as JsonValue;
      },
    },
    {
      name: "omalla_list_tasks",
      description: "List tasks with status and priority.",
      inputSchema: { type: "object", properties: {} },
      handler: async () => api.tasks.list() as unknown as JsonValue,
    },
    {
      name: "omalla_create_booking",
      description:
        "Book an appointment. `when` is natural language such as 'tomorrow at 3pm' or an ISO timestamp.",
      inputSchema: {
        type: "object",
        properties: {
          name: { type: "string" },
          when: { type: "string" },
          duration_min: { type: "integer", default: 30 },
          phone: { type: "string" },
          email: { type: "string" },
          notes: { type: "string" },
        },
        required: ["name", "when"],
      },
      handler: async (args) => {
        const booking = await api.bookings.create({
          name: String(args.name ?? ""),
          when: String(args.when ?? ""),
          ...(typeof args.duration_min === "number" ? { durationMin: args.duration_min } : {}),
          ...(typeof args.phone === "string" ? { phone: args.phone } : {}),
          ...(typeof args.email === "string" ? { email: args.email } : {}),
          ...(typeof args.notes === "string" ? { notes: args.notes } : {}),
        });
        return booking as unknown as JsonValue;
      },
    },
    {
      name: "omalla_list_bookings",
      description: "List appointments, earliest first.",
      inputSchema: { type: "object", properties: {} },
      handler: async () => api.bookings.list() as unknown as JsonValue,
    },
    {
      name: "omalla_list_escalations",
      description: "List calls escalated to a human and their status.",
      inputSchema: { type: "object", properties: {} },
      handler: async () => api.escalations.list() as unknown as JsonValue,
    },
    {
      name: "omalla_update_escalation",
      description: "Acknowledge or close an escalation.",
      inputSchema: {
        type: "object",
        properties: {
          escalation_id: { type: "string" },
          status: { type: "string", enum: ["open", "acknowledged", "closed"] },
        },
        required: ["escalation_id", "status"],
      },
      handler: async (args) => {
        const escalation = await api.escalations.update(
          String(args.escalation_id ?? ""),
          (args.status as "open" | "acknowledged" | "closed") ?? "acknowledged",
        );
        return escalation as unknown as JsonValue;
      },
    },
    {
      name: "omalla_search_knowledge",
      description: "Search a knowledge base and return the best matching passages.",
      inputSchema: {
        type: "object",
        properties: {
          knowledge_base_id: { type: "string" },
          query: { type: "string" },
          limit: { type: "integer", default: 5 },
        },
        required: ["knowledge_base_id", "query"],
      },
      handler: async (args) => {
        const result = await api.knowledge.search(
          String(args.knowledge_base_id ?? ""),
          String(args.query ?? ""),
          typeof args.limit === "number" ? args.limit : 5,
        );
        return result.hits as unknown as JsonValue;
      },
    },
    {
      name: "omalla_fire_webhook",
      description:
        "Trigger a workflow that listens on a webhook path, for example one published from n8n.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string" },
          payload: { type: "object" },
        },
        required: ["path"],
      },
      handler: async (args) => {
        const result = await api.webhook(String(args.path ?? ""), (args.payload ?? {}) as JsonValue);
        return result as unknown as JsonValue;
      },
    },
  ];
}

export function createMcpServer(options: McpServerOptions): {
  handle: (line: string) => Promise<void>;
  tools: McpTool[];
} {
  const tools = buildTools(options.client);
  const byName = new Map(tools.map((tool) => [tool.name, tool]));
  const write = (payload: unknown) => {
    options.output?.write(`${JSON.stringify(payload)}\n`);
  };
  const log = options.log ?? ((message: string) => process.stderr.write(`[omalla-mcp] ${message}\n`));

  const respond = (id: JsonRpcRequest["id"], result: unknown) =>
    write({ jsonrpc: "2.0", id: id ?? null, result });
  const fail = (id: JsonRpcRequest["id"], code: number, message: string, data?: unknown) =>
    write({ jsonrpc: "2.0", id: id ?? null, error: { code, message, ...(data ? { data } : {}) } });

  async function handle(line: string): Promise<void> {
    const trimmed = line.trim();
    if (!trimmed) return;

    let request: JsonRpcRequest;
    try {
      request = JSON.parse(trimmed) as JsonRpcRequest;
    } catch {
      fail(null, -32700, "parse error");
      return;
    }
    if (request.jsonrpc !== "2.0" || typeof request.method !== "string") {
      fail(request.id, -32600, "invalid request");
      return;
    }

    switch (request.method) {
      case "initialize":
        respond(request.id, {
          protocolVersion: PROTOCOL_VERSION,
          capabilities: { tools: { listChanged: false } },
          serverInfo: SERVER_INFO,
          instructions:
            "Omalla is a local voice-agent workspace. Telephony is simulated: calls never reach a real phone. Use omalla_start_simulated_call to exercise the receptionist, then omalla_get_call to read the transcript.",
        });
        return;

      case "notifications/initialized":
      case "notifications/cancelled":
        return;

      case "ping":
        respond(request.id, {});
        return;

      case "tools/list":
        respond(request.id, {
          tools: tools.map((tool) => ({
            name: tool.name,
            description: tool.description,
            inputSchema: tool.inputSchema,
          })),
        });
        return;

      case "tools/call": {
        const name = typeof request.params?.name === "string" ? request.params.name : undefined;
        if (!name) {
          fail(request.id, -32602, "tools/call requires a name");
          return;
        }
        const tool = byName.get(name);
        if (!tool) {
          fail(request.id, -32602, `unknown tool: ${name}`);
          return;
        }
        const args = (request.params?.arguments ?? {}) as JsonObject;
        try {
          const result = await tool.handler(args);
          respond(request.id, {
            content: [
              {
                type: "text",
                text: typeof result === "string" ? result : JSON.stringify(result, null, 2),
              },
            ],
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          log(`${name} failed: ${message}`);
          respond(request.id, {
            isError: true,
            content: [{ type: "text", text: JSON.stringify({ error: message }) }],
          });
        }
        return;
      }

      default:
        fail(request.id, -32601, `method not found: ${request.method}`);
    }
  }

  return { handle, tools };
}

/** Newline-delimited JSON-RPC over stdio, the MCP stdio transport. */
export async function runMcpServer(
  options: McpServerOptions & { ready?: () => void },
): Promise<void> {
  const server = createMcpServer(options);
  const input = options.input ?? process.stdin;
  const rl = createInterface({ input: input as NodeJS.ReadableStream, crlfDelay: Infinity });

  process.stderr.write(
    `[omalla-mcp] ready · ${server.tools.length} tools · telephony simulated\n`,
  );
  options.ready?.();

  for await (const line of rl) {
    await server.handle(line);
  }
}
