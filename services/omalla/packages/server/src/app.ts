import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Fastify, { type FastifyInstance, type FastifyReply, type FastifyRequest } from "fastify";
import cors from "@fastify/cors";
import websocket from "@fastify/websocket";
import { z } from "zod";
import {
  NODE_TYPES,
  OmallaError,
  RateLimiter,
  TRIGGER_TYPES,
  createRetriever,
  isOmallaError,
  newId,
  normalizeNumber,
  nowIso,
  sanitizeUntrustedCallVariables,
  verifySignedWebhookRaw,
} from "@omalla/core";
import type {
  Agent,
  AgentConfig,
  Call,
  EvaluationCase,
  JsonValue,
  KnowledgeBase,
  Principal,
  TenantSettings,
  ToolDefinition,
  Workflow,
  WorkflowEdge,
  WorkflowNode,
  WorkflowTrigger,
} from "@omalla/core";
import type { TemplateId } from "@omalla/workflow";
import type { OmallaRuntime } from "./runtime.js";
import { parseSpokenDateTime } from "./parse-when.js";
import { registerTelephonyRoutes } from "./telephony-routes.js";
import { openApiDocument } from "./openapi.js";

declare module "fastify" {
  interface FastifyRequest {
    principal: Principal | null;
    rawBody?: Buffer;
  }
}

const DEFAULT_AGENT_CONFIG: AgentConfig = {
  firstMessage: "Hello, how can I help?",
  systemPrompt: "You are a helpful voice assistant. Keep replies short and spoken.",
  model: { provider: "mock", model: "demo", temperature: 0.3, maxTokens: 400 },
  voice: { provider: "mock", voiceId: "demo", speed: 1 },
  transcriber: { provider: "mock", language: "en-US" },
  language: "en-US",
  tools: [],
  knowledgeBaseIds: [],
  maxDurationSec: 600,
  silenceTimeoutSec: 12,
  endCallPhrases: ["goodbye", "that's all", "مع السلامة", "انهي المكالمة"],
  interruption: { enabled: true, minWords: 1 },
  recording: { enabled: false, consentAnnouncement: true },
  variables: {},
};

const CWD_DASHBOARD_DIR = path.resolve(process.cwd(), "apps/dashboard/public");
const MODULE_DASHBOARD_DIR = fileURLToPath(new URL("../../../apps/dashboard/public", import.meta.url));
const DASHBOARD_DIR = existsSync(CWD_DASHBOARD_DIR) ? CWD_DASHBOARD_DIR : MODULE_DASHBOARD_DIR;

export interface BuildAppOptions {
  /** Test seam: observes each route as Fastify registers it. */
  onRoute?: (route: { method: string | string[]; url: string }) => void;
}

export async function buildApp(runtime: OmallaRuntime, options: BuildAppOptions = {}): Promise<FastifyInstance> {
  const app = Fastify({ logger: false, bodyLimit: 2_000_000, trustProxy: false });
  if (options.onRoute) app.addHook("onRoute", options.onRoute);
  const limiter = new RateLimiter(600, 60_000);
  const authLimiter = new RateLimiter(30, 60_000);

  app.decorateRequest("principal", null);
  app.decorateRequest("rawBody", undefined);

  // Preserve exact wire bytes on JSON and form-urlencoded requests (OM-T3 & OM-T5).
  app.removeContentTypeParser("application/json");
  app.addContentTypeParser(
    "application/json",
    { parseAs: "buffer" },
    (request, body, done) => {
      const buf = Buffer.isBuffer(body) ? body : Buffer.from(body);
      request.rawBody = buf;
      if (buf.length === 0) {
        done(null, {});
        return;
      }
      try {
        done(null, JSON.parse(buf.toString("utf8")));
      } catch (error) {
        done(new OmallaError("validation", `malformed JSON: ${(error as Error).message}`, 400));
      }
    },
  );

  app.addContentTypeParser(
    "application/x-www-form-urlencoded",
    { parseAs: "buffer" },
    (request, body, done) => {
      const buf = Buffer.isBuffer(body) ? body : Buffer.from(body);
      request.rawBody = buf;
      try {
        const params = new URLSearchParams(buf.toString("utf8"));
        const out: Record<string, string> = {};
        for (const [key, value] of params) out[key] = value;
        done(null, out);
      } catch (error) {
        done(error as Error);
      }
    },
  );

  await app.register(cors, {
    origin: (origin, callback) => {
      if (!origin) return callback(null, true);
      const allowed = /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/.test(origin);
      callback(null, allowed);
    },
    credentials: false,
  });
  await app.register(websocket, { options: { maxPayload: 256 * 1024 } });

  app.addHook("onRequest", async (request, reply) => {
    const url = request.raw.url ?? "";
    const limit = url.startsWith("/v1/") ? limiter.take(clientKey(request)) : null;
    if (limit && !limit.allowed) {
      await reply
        .status(429)
        .header("retry-after", String(Math.ceil(limit.retryAfterMs / 1000)))
        .send({ error: { code: "rate_limited", message: "too many requests" } });
      return reply;
    }
    if (!url.startsWith("/v1/")) return;
    if (url.startsWith("/v1/health")) return;
    if (url.startsWith("/v1/realtime/ws")) return;
    request.principal = authenticate(runtime, request, authLimiter);
    runtime.requireRole(request.principal, "viewer");
  });

  app.setErrorHandler(async (error, request, reply) => {
    if (isOmallaError(error)) {
      return reply.status(error.status).send({ error: { code: error.code, message: error.message } });
    }
    if (error instanceof z.ZodError) {
      return reply.status(400).send({
        error: {
          code: "validation",
          message: error.issues.map((issue) => `${issue.path.join(".") || "body"}: ${issue.message}`).join("; "),
        },
      });
    }
    const fastifyStatus = (error as { statusCode?: number }).statusCode;
    if (typeof fastifyStatus === "number" && fastifyStatus >= 400 && fastifyStatus < 500) {
      return reply.status(fastifyStatus).send({
        error: { code: "bad_request", message: (error as Error).message },
      });
    }
    runtime.logger.error("unhandled request error", {
      url: request.raw.url,
      error: (error as Error).message,
    });
    return reply.status(500).send({ error: { code: "internal", message: "internal error" } });
  });

  /* ------------------------------------------------------------------ */
  /* telephony                                                           */
  /* ------------------------------------------------------------------ */

  registerTelephonyRoutes(app, runtime);

  /* ------------------------------------------------------------------ */
  /* system & tenant settings                                            */
  /* ------------------------------------------------------------------ */

  app.get("/v1/health", async () => ({
    ok: true,
    version: "0.1.0",
    simulation: runtime.telephonyProviders.default.id === "simulated",
    providerMode: process.env.OMALLA_DEMO_VOICE === "mock" ? "mock" : "local",
    storageMode: runtime.db.journalMode,
    telephonyDefault: runtime.telephonyProviders.default.id,
    telephony: runtime.providerSummary(),
    stats: runtime.db.stats(),
  }));

  app.get("/v1/me", async (request) => {
    const principal = requirePrincipal(request);
    const tenant = runtime.db.col("tenants").get(principal.tenantId);
    return { principal, tenant };
  });

  app.patch("/v1/tenant/settings", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "owner");
    const tenant = runtime.db.col("tenants").get(principal.tenantId);
    if (!tenant) throw new OmallaError("not_found", "tenant not found", 404);
    const patch = tenantSettingsBody.parse(request.body ?? {});
    const nextSettings: TenantSettings = {
      ...tenant.settings,
      ...(patch as Partial<TenantSettings>),
    };
    const updated = runtime.db.col("tenants").update(tenant.id, { settings: nextSettings });
    audit(runtime, principal, "tenant.settings.update", tenant.id, "allowed");
    return updated;
  });

  app.get("/v1/metrics", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.metrics(principal.tenantId);
  });

  app.get("/openapi.json", async (_request, reply) => {
    reply.header("cache-control", "no-store");
    return openApiDocument();
  });

  /* ------------------------------------------------------------------ */
  /* API keys                                                            */
  /* ------------------------------------------------------------------ */

  app.get("/v1/keys", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    return runtime.db
      .col("apiKeys")
      .list((key) => key.tenantId === principal.tenantId)
      .map(({ hash: _hash, ...rest }) => rest);
  });

  app.post("/v1/keys", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "owner");
    const body = z
      .object({
        name: z.string().min(1).max(80),
        role: z.enum(["viewer", "operator", "admin", "owner"]).default("operator"),
      })
      .parse(request.body);
    const key = await runtime.issueApiKey(principal.tenantId, body.name, body.role);
    audit(runtime, principal, "key.create", key.id, "allowed");
    return reply.status(201).send(key);
  });

  app.delete("/v1/keys/:id", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "owner");
    const key = runtime.db.col("apiKeys").get(param(request, "id"));
    if (!key || key.tenantId !== principal.tenantId) {
      throw new OmallaError("not_found", "key not found", 404);
    }
    if (key.id === principal.apiKeyId) {
      throw new OmallaError("validation", "refusing to revoke the key making this request", 400);
    }
    runtime.db.col("apiKeys").update(key.id, { revokedAt: nowIso() });
    audit(runtime, principal, "key.revoke", key.id, "allowed");
    return reply.status(204).send();
  });

  /* ------------------------------------------------------------------ */
  /* agents & immutable versions / test / rollback                       */
  /* ------------------------------------------------------------------ */

  app.get("/v1/agents", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.db
      .col("agents")
      .list((agent) => agent.tenantId === principal.tenantId);
  });

  app.get("/v1/agents/:id", async (request) => {
    const principal = requirePrincipal(request);
    return ownedAgent(runtime, principal, param(request, "id"));
  });

  app.post("/v1/agents", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        name: z.string().min(1).max(120),
        description: z.string().max(500).optional(),
        config: z.record(z.string(), z.unknown()).optional(),
      })
      .parse(request.body);

    const config = sanitizeAndAssertAgentConfig(
      runtime,
      principal.tenantId,
      mergeConfig(DEFAULT_AGENT_CONFIG, body.config ?? {}),
    );
    const now = nowIso();
    const agent: Agent = {
      id: newId("agt"),
      tenantId: principal.tenantId,
      name: body.name,
      description: body.description ?? "",
      status: "draft",
      version: 1,
      createdAt: now,
      updatedAt: now,
      config,
    };
    runtime.db.col("agents").insert(agent);
    for (const tool of config.tools) {
      runtime.db.col("tools").upsert(tool);
    }
    runtime.recordAgentVersion(agent, actorOf(principal), "created");
    audit(runtime, principal, "agent.create", agent.id, "allowed");
    return reply.status(201).send(agent);
  });

  app.patch("/v1/agents/:id", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const agent = ownedAgent(runtime, principal, param(request, "id"));
    const body = z
      .object({
        name: z.string().min(1).max(120).optional(),
        description: z.string().max(500).optional(),
        config: z.record(z.string(), z.unknown()).optional(),
        status: z.enum(["draft", "published", "archived"]).optional(),
      })
      .parse(request.body);

    const nextConfig = body.config
      ? sanitizeAndAssertAgentConfig(runtime, principal.tenantId, mergeConfig(agent.config, body.config))
      : undefined;

    const nextVersion = nextConfig ? agent.version + 1 : agent.version;
    const updated = runtime.db.col("agents").update(agent.id, {
      ...(body.name ? { name: body.name } : {}),
      ...(body.description !== undefined ? { description: body.description } : {}),
      ...(body.status ? { status: body.status } : {}),
      ...(nextConfig ? { config: nextConfig, version: nextVersion } : {}),
      updatedAt: nowIso(),
    });
    for (const tool of updated.config.tools) {
      runtime.db.col("tools").upsert(tool);
    }
    if (nextConfig) {
      runtime.recordAgentVersion(updated, actorOf(principal), "updated");
    }
    return updated;
  });

  app.post("/v1/agents/:id/publish", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    const agent = ownedAgent(runtime, principal, param(request, "id"));
    sanitizeAndAssertAgentConfig(runtime, principal.tenantId, agent.config);
    const now = nowIso();
    const version = agent.version + 1;
    const updated = runtime.db.col("agents").update(agent.id, {
      status: "published",
      version,
      publishedAt: now,
      updatedAt: now,
    });
    runtime.recordAgentVersion(updated, actorOf(principal), "published");
    for (const tool of updated.config.tools) runtime.db.col("tools").upsert(tool);
    audit(runtime, principal, "agent.publish", agent.id, "allowed");
    return updated;
  });

  app.get("/v1/agents/:id/versions", async (request) => {
    const principal = requirePrincipal(request);
    const agent = ownedAgent(runtime, principal, param(request, "id"));
    return runtime.listAgentVersions(principal.tenantId, agent.id);
  });

  app.post("/v1/agents/:id/test", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const agent = ownedAgent(runtime, principal, param(request, "id"));
    const body = z
      .object({
        callerTurns: z.array(z.string().min(1).max(2000)).max(20).default([]),
        variables: z.record(z.string(), z.unknown()).default({}),
        version: z.number().int().min(1).optional(),
        compareVersion: z.number().int().min(1).optional(),
        expectations: z
          .object({
            mustContain: z.array(z.string()).optional(),
            mustNotContain: z.array(z.string()).optional(),
            mustCallTools: z.array(z.string()).optional(),
            maxTurns: z.number().int().min(1).optional(),
          })
          .optional(),
      })
      .parse(request.body ?? {});
    return runtime.testAgent(principal.tenantId, agent.id, {
      callerTurns: body.callerTurns,
      variables: body.variables as Record<string, JsonValue>,
      ...(body.version !== undefined ? { version: body.version } : {}),
      ...(body.compareVersion !== undefined ? { compareVersion: body.compareVersion } : {}),
      ...(body.expectations ? { expectations: body.expectations as EvaluationCase["expectations"] } : {}),
    });
  });

  app.post("/v1/agents/:id/rollback", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    const agent = ownedAgent(runtime, principal, param(request, "id"));
    const body = z
      .object({
        version: z.number().int().min(1),
        note: z.string().max(300).optional(),
      })
      .parse(request.body);
    const rolledBack = runtime.rollbackAgent(
      principal.tenantId,
      agent.id,
      body.version,
      actorOf(principal),
      body.note,
    );
    audit(runtime, principal, "agent.rollback", agent.id, "allowed");
    return rolledBack;
  });

  app.delete("/v1/agents/:id", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    const agent = ownedAgent(runtime, principal, param(request, "id"));
    runtime.db.col("agents").remove(agent.id);
    return reply.status(204).send();
  });

  /* ------------------------------------------------------------------ */
  /* tools                                                               */
  /* ------------------------------------------------------------------ */

  app.get("/v1/tools", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.db.col("tools").list((tool) => tool.tenantId === principal.tenantId);
  });

  app.post("/v1/tools", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const input = toolBody.parse(request.body);
    assertToolReferencesOwned(runtime, principal.tenantId, input);
    const now = nowIso();
    const { staticBody, trustedFields, parameters, ...rest } = input;
    const tool: ToolDefinition = {
      id: newId("tool"),
      tenantId: principal.tenantId,
      createdAt: now,
      updatedAt: now,
      ...rest,
      parameters: parameters as unknown as ToolDefinition["parameters"],
      ...(staticBody ? { staticBody: staticBody as Record<string, JsonValue> } : {}),
      ...(trustedFields ? { trustedFields: trustedFields as Record<string, JsonValue> } : {}),
    };
    runtime.db.col("tools").insert(tool);
    return reply.status(201).send(tool);
  });

  app.patch("/v1/tools/:id", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const tool = ownedTool(runtime, principal, param(request, "id"));
    const patch = toolBody.partial().parse(request.body);
    assertToolReferencesOwned(runtime, principal.tenantId, patch);
    return runtime.db.col("tools").update(tool.id, {
      ...(patch as Partial<ToolDefinition>),
      tenantId: principal.tenantId,
      updatedAt: nowIso(),
    });
  });

  app.delete("/v1/tools/:id", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    const tool = ownedTool(runtime, principal, param(request, "id"));
    runtime.db.col("tools").remove(tool.id);
    return reply.status(204).send();
  });

  /** Executes a tool once with a synthetic context. Used by the debugger. */
  app.post("/v1/tools/:id/test", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const tool = ownedTool(runtime, principal, param(request, "id"));
    const body = z
      .object({
        args: z.record(z.string(), z.unknown()).default({}),
        dryRun: z.boolean().default(true),
        callerNumberVerified: z.boolean().default(false),
      })
      .parse(request.body ?? {});
    if (!body.dryRun || body.callerNumberVerified) {
      runtime.requireRole(principal, "admin");
    }
    const now = nowIso();
    const result = await runtime.tools.execute({
      toolId: tool.id,
      name: tool.name,
      args: body.args as Record<string, JsonValue>,
      dryRun: body.dryRun,
      context: {
        callId: "tool_test",
        tenantId: principal.tenantId,
        agentId: "tool_test",
        agentName: "tool test",
        direction: "inbound",
        callerNumber: "+15550000000",
        variables: {},
        trusted: {
          tenantId: principal.tenantId,
          callId: "tool_test",
          callerNumber: "+15550000000",
          callerNumberVerified: body.callerNumberVerified,
        },
      },
    });
    return { ...result, at: now };
  });

  /* ------------------------------------------------------------------ */
  /* calls                                                               */
  /* ------------------------------------------------------------------ */

  app.get("/v1/calls", async (request) => {
    const principal = requirePrincipal(request);
    const query = z
      .object({ status: z.string().optional(), limit: z.coerce.number().int().min(1).max(200).default(50) })
      .parse(request.query ?? {});
    return runtime.db
      .col("calls")
      .list(
        (call) =>
          call.tenantId === principal.tenantId &&
          (!query.status || call.status === query.status),
      )
      .sort((a, b) => b.startedAt.localeCompare(a.startedAt))
      .slice(0, query.limit);
  });

  app.get("/v1/calls/:id", async (request) => {
    const principal = requirePrincipal(request);
    return ownedCall(runtime, principal, param(request, "id"));
  });

  app.post("/v1/calls", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        to: z.string().default("+15550001234"),
        from: z.string().default("+15550009999"),
        variables: z.record(z.string(), z.unknown()).default({}),
        say: z.array(z.string()).default([]),
        press: z.array(z.string()).default([]),
      })
      .parse(request.body ?? {});

    // OM-T1: normalize destination and verify strict ownership by principal.tenantId
    const to = normalizeNumber(body.to);
    const targetNumber = runtime.db
      .col("phoneNumbers")
      .list((n) => n.e164 === to)[0];
    if (!targetNumber || targetNumber.tenantId !== principal.tenantId) {
      throw new OmallaError("not_found", `no phone number configured for ${body.to}`, 404);
    }

    const sanitizedVars = sanitizeUntrustedCallVariables(
      body.variables as Record<string, JsonValue>,
    );
    const idemKey = extractIdempotencyKey(request);
    return executeIdempotent(
      runtime,
      request,
      reply,
      { tenantId: principal.tenantId, scope: "calls.simulate", idemKey, payload: body },
      async () => {
        const handle = await runtime.startInbound({
          tenantId: principal.tenantId,
          to,
          from: body.from,
          variables: sanitizedVars,
        });
        for (const digits of body.press) await handle.press(digits);
        for (const text of body.say) await handle.say(text);
        audit(runtime, principal, "call.simulate", handle.call.id, "allowed");
        return { statusCode: 201, body: handle.snapshot() };
      },
    );
  });

  app.post("/v1/calls/outbound", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        to: z.string().min(4),
        agentId: z.string().min(1),
        consent: z.boolean(),
        variables: z.record(z.string(), z.unknown()).default({}),
        /** Carrier calls cost real money; simulated remains the default. */
        mode: z.enum(["simulated", "carrier"]).default("simulated"),
        provider: z.enum(["simulated", "twilio", "signalwire", "telnyx", "vonage", "sip"]).optional(),
        from: z.string().optional(),
      })
      .parse(request.body);

    const sanitizedVars = sanitizeUntrustedCallVariables(
      body.variables as Record<string, JsonValue>,
    );
    const idemKey = extractIdempotencyKey(request);
    return executeIdempotent(
      runtime,
      request,
      reply,
      { tenantId: principal.tenantId, scope: "calls.outbound", idemKey, payload: body },
      async () => {
        if (body.mode === "carrier") {
          const call = await runtime.startCarrierOutbound({
            tenantId: principal.tenantId,
            to: body.to,
            agentId: body.agentId,
            consent: body.consent,
            variables: sanitizedVars,
            ...(body.provider ? { providerId: body.provider } : {}),
            ...(body.from ? { from: body.from } : {}),
          });
          audit(runtime, principal, "call.outbound.carrier", call.id, "allowed");
          return { statusCode: 201, body: call };
        }
        const handle = await runtime.startOutbound({
          tenantId: principal.tenantId,
          to: body.to,
          agentId: body.agentId,
          consent: body.consent,
          variables: sanitizedVars,
          ...(body.from ? { from: body.from } : {}),
        });
        audit(runtime, principal, "call.outbound", handle.call.id, "allowed");
        return { statusCode: 201, body: handle.snapshot() };
      },
    );
  });

  app.post("/v1/calls/:id/say", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const call = ownedCall(runtime, principal, param(request, "id"));
    const body = z.object({ text: z.string().min(1).max(2000) }).parse(request.body);
    return runtime.say(call.id, body.text);
  });

  app.post("/v1/calls/:id/dtmf", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const call = ownedCall(runtime, principal, param(request, "id"));
    const body = z.object({ digits: z.string().regex(/^[0-9*#]{1,32}$/) }).parse(request.body);
    return runtime.press(call.id, body.digits);
  });

  app.post("/v1/calls/:id/hangup", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const call = ownedCall(runtime, principal, param(request, "id"));
    return runtime.hangup(call.id);
  });

  app.get("/v1/calls/:id/stream", { websocket: true }, (socket, request) => {
    let principal: Principal;
    try {
      principal = authenticate(runtime, request, authLimiter, true);
    } catch (error) {
      socket.close(4401, (error as Error).message);
      return;
    }
    const callId = param(request, "id");
    const call = runtime.db.col("calls").get(callId);
    if (!call || call.tenantId !== principal.tenantId) {
      socket.close(4404, "call not found");
      return;
    }
    socket.send(JSON.stringify({ type: "snapshot", call }));
    const off = runtime.events.on("call", (event) => {
      if (event.callId !== callId) return;
      if (socket.readyState === 1) socket.send(JSON.stringify(event));
    });
    socket.on("close", off);
  });

  /* ------------------------------------------------------------------ */
  /* workflows & immutable versions / test / rollback                    */
  /* ------------------------------------------------------------------ */

  app.get("/v1/workflows", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.db
      .col("workflows")
      .list((workflow) => workflow.tenantId === principal.tenantId)
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  });

  app.get("/v1/workflows/:id", async (request) => {
    const principal = requirePrincipal(request);
    return ownedWorkflow(runtime, principal, param(request, "id"));
  });

  app.post("/v1/workflows", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = workflowBody.parse(request.body);
    const now = nowIso();
    const workflow: Workflow = {
      id: newId("wf"),
      tenantId: principal.tenantId,
      name: body.name,
      description: body.description ?? "",
      status: body.status ?? "draft",
      version: 1,
      trigger:
        (body.trigger as WorkflowTrigger | undefined) ?? {
          type: "webhook",
          config: { path: body.name.toLowerCase().replace(/[^a-z0-9]+/g, "-") },
        },
      nodes:
        (body.nodes as WorkflowNode[] | undefined) ?? [
          { id: "trigger", type: "trigger", name: "Trigger", config: {} },
          { id: "end", type: "end", name: "Done", config: {} },
        ],
      edges: (body.edges as WorkflowEdge[] | undefined) ?? [{ from: "trigger", to: "end" }],
      idempotencyWindowSec: body.idempotencyWindowSec ?? 600,
      createdAt: now,
      updatedAt: now,
    };
    runtime.db.col("workflows").insert(workflow);
    runtime.recordWorkflowVersion(workflow, actorOf(principal), "created");
    return reply.status(201).send(workflow);
  });

  app.patch("/v1/workflows/:id", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const workflow = ownedWorkflow(runtime, principal, param(request, "id"));
    const body = workflowBody.partial().parse(request.body);
    const patch: Partial<Workflow> = {
      ...(body.name ? { name: body.name } : {}),
      ...(body.description !== undefined ? { description: body.description } : {}),
      ...(body.status ? { status: body.status } : {}),
      ...(body.trigger ? { trigger: body.trigger as WorkflowTrigger } : {}),
      ...(body.nodes ? { nodes: body.nodes as WorkflowNode[] } : {}),
      ...(body.edges ? { edges: body.edges as WorkflowEdge[] } : {}),
      ...(body.idempotencyWindowSec ? { idempotencyWindowSec: body.idempotencyWindowSec } : {}),
      version: workflow.version + 1,
      updatedAt: nowIso(),
    };
    const updated = runtime.db.col("workflows").update(workflow.id, patch);
    runtime.recordWorkflowVersion(updated, actorOf(principal), "updated");
    return updated;
  });

  app.get("/v1/workflows/:id/versions", async (request) => {
    const principal = requirePrincipal(request);
    const workflow = ownedWorkflow(runtime, principal, param(request, "id"));
    return runtime.listWorkflowVersions(principal.tenantId, workflow.id);
  });

  app.post("/v1/workflows/:id/test", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const workflow = ownedWorkflow(runtime, principal, param(request, "id"));
    const body = z
      .object({
        payload: z.unknown().default({}),
        version: z.number().int().min(1).optional(),
        compareVersion: z.number().int().min(1).optional(),
      })
      .parse(request.body ?? {});
    return runtime.testWorkflow(principal.tenantId, workflow.id, {
      payload: body.payload as JsonValue,
      ...(body.version !== undefined ? { version: body.version } : {}),
      ...(body.compareVersion !== undefined ? { compareVersion: body.compareVersion } : {}),
    });
  });

  app.post("/v1/workflows/:id/rollback", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    const workflow = ownedWorkflow(runtime, principal, param(request, "id"));
    const body = z
      .object({
        version: z.number().int().min(1),
        note: z.string().max(300).optional(),
      })
      .parse(request.body);
    const rolledBack = runtime.rollbackWorkflow(
      principal.tenantId,
      workflow.id,
      body.version,
      actorOf(principal),
      body.note,
    );
    audit(runtime, principal, "workflow.rollback", workflow.id, "allowed");
    return rolledBack;
  });

  app.delete("/v1/workflows/:id", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    const workflow = ownedWorkflow(runtime, principal, param(request, "id"));
    runtime.db.col("workflows").remove(workflow.id);
    return reply.status(204).send();
  });

  app.post("/v1/workflows/:id/run", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const workflow = ownedWorkflow(runtime, principal, param(request, "id"));
    const body = z
      .object({
        payload: z.unknown().default({}),
        dryRun: z.boolean().default(false),
        idempotencyKey: z.string().max(200).optional(),
      })
      .parse(request.body ?? {});

    const headerIdemKey = extractIdempotencyKey(request);
    if (headerIdemKey) {
      return executeIdempotent(
        runtime,
        request,
        reply,
        {
          tenantId: principal.tenantId,
          scope: `workflows.run:${workflow.id}`,
          idemKey: headerIdemKey,
          payload: body,
        },
        async () => {
          const run = await runtime.runWorkflow(workflow, {
            ...(workflow.trigger.type !== "manual" ? { type: workflow.trigger.type } : {}),
            payload: body.payload as JsonValue,
            dryRun: body.dryRun,
            ...(body.idempotencyKey ? { idempotencyKey: body.idempotencyKey } : {}),
          });
          return { statusCode: 200, body: run };
        },
      );
    }

    return runtime.runWorkflow(workflow, {
      ...(workflow.trigger.type !== "manual" ? { type: workflow.trigger.type } : {}),
      payload: body.payload as JsonValue,
      dryRun: body.dryRun,
      ...(body.idempotencyKey ? { idempotencyKey: body.idempotencyKey } : {}),
    });
  });

  app.get("/v1/workflows/:id/runs", async (request) => {
    const principal = requirePrincipal(request);
    const workflow = ownedWorkflow(runtime, principal, param(request, "id"));
    return runtime.db
      .col("workflowRuns")
      .list((run) => run.tenantId === principal.tenantId && run.workflowId === workflow.id)
      .sort((a, b) => b.startedAt.localeCompare(a.startedAt))
      .slice(0, 100);
  });

  app.get("/v1/runs", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.db
      .col("workflowRuns")
      .list((run) => run.tenantId === principal.tenantId)
      .sort((a, b) => b.startedAt.localeCompare(a.startedAt))
      .slice(0, 100);
  });

  app.post("/v1/workflows/import/n8n", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z.object({ workflow: z.unknown() }).parse(request.body);
    const result = runtime.importN8n(body.workflow, principal.tenantId, actorOf(principal));
    return reply.status(201).send(result);
  });

  app.get("/v1/workflows/:id/export/n8n", async (request) => {
    const principal = requirePrincipal(request);
    const workflow = ownedWorkflow(runtime, principal, param(request, "id"));
    return runtime.exportN8n(workflow);
  });

  app.get("/v1/templates", async () => runtime.templates());

  app.post("/v1/templates/:id/install", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const id = param(request, "id") as TemplateId;
    const body = z.object({ activate: z.boolean().default(false) }).parse(request.body ?? {});
    const workflow = runtime.installTemplate(id, principal.tenantId, actorOf(principal));
    if (body.activate) {
      const activated = runtime.db
        .col("workflows")
        .update(workflow.id, { status: "active", version: workflow.version + 1 });
      runtime.recordWorkflowVersion(activated, actorOf(principal), "activated");
    }
    return reply.status(201).send(runtime.db.col("workflows").get(workflow.id));
  });

  /* ------------------------------------------------------------------ */
  /* automation records                                                  */
  /* ------------------------------------------------------------------ */

  app.get("/v1/tasks", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.store
      .listTasks(principal.tenantId)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  });

  app.post("/v1/tasks", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        title: z.string().min(1).max(300),
        description: z.string().max(4000).default(""),
        priority: z.enum(["low", "normal", "high", "urgent"]).default("normal"),
        labels: z.array(z.string().max(40)).max(20).default([]),
        dueAt: z.string().datetime().optional(),
        assignee: z.string().max(80).optional(),
      })
      .parse(request.body);
    const task = await runtime.store.createTask({
      tenantId: principal.tenantId,
      title: body.title,
      description: body.description,
      priority: body.priority,
      labels: body.labels,
      ...(body.dueAt ? { dueAt: body.dueAt } : {}),
      ...(body.assignee ? { assignee: body.assignee } : {}),
    });
    return reply.status(201).send(task);
  });

  app.patch("/v1/tasks/:id", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const task = runtime.db.col("tasks").get(param(request, "id"));
    if (!task || task.tenantId !== principal.tenantId) {
      throw new OmallaError("not_found", "task not found", 404);
    }
    const body = z
      .object({
        title: z.string().optional(),
        description: z.string().optional(),
        status: z.enum(["todo", "doing", "done"]).optional(),
        priority: z.enum(["low", "normal", "high", "urgent"]).optional(),
        assignee: z.string().optional(),
      })
      .parse(request.body);
    return runtime.store.updateTask(task.id, body as Record<string, JsonValue>, principal.tenantId);
  });

  app.get("/v1/bookings", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.db
      .col("bookings")
      .list((booking) => booking.tenantId === principal.tenantId)
      .sort((a, b) => a.startAt.localeCompare(b.startAt));
  });

  app.post("/v1/bookings", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        name: z.string().min(1),
        title: z.string().default("Appointment"),
        when: z.string().min(1),
        durationMin: z.number().int().min(5).max(600).default(30),
        phone: z.string().optional(),
        email: z.string().email().optional(),
        notes: z.string().optional(),
      })
      .parse(request.body);
    const parsed = parseSpokenDateTime(body.when);
    if (!parsed) throw new OmallaError("validation", "could not understand the requested time", 400);
    const booking = await runtime.store.createBooking({
      tenantId: principal.tenantId,
      title: body.title,
      name: body.name,
      startAt: parsed.iso,
      durationMin: body.durationMin,
      ...(body.phone ? { phone: body.phone } : {}),
      ...(body.email ? { email: body.email } : {}),
      ...(body.notes ? { notes: body.notes } : {}),
    });
    return reply.status(201).send(booking);
  });

  app.patch("/v1/bookings/:id", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const booking = runtime.db.col("bookings").get(param(request, "id"));
    if (!booking || booking.tenantId !== principal.tenantId) {
      throw new OmallaError("not_found", "booking not found", 404);
    }
    const body = z
      .object({ status: z.enum(["confirmed", "cancelled", "completed", "no_show"]) })
      .parse(request.body);
    return runtime.db.col("bookings").update(booking.id, { status: body.status });
  });

  app.get("/v1/contacts", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.db.col("contacts").list((contact) => contact.tenantId === principal.tenantId);
  });

  app.get("/v1/escalations", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.db
      .col("escalations")
      .list((escalation) => escalation.tenantId === principal.tenantId)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  });

  app.patch("/v1/escalations/:id", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const escalation = runtime.db.col("escalations").get(param(request, "id"));
    if (!escalation || escalation.tenantId !== principal.tenantId) {
      throw new OmallaError("not_found", "escalation not found", 404);
    }
    const body = z
      .object({ status: z.enum(["open", "acknowledged", "closed"]) })
      .parse(request.body);
    return runtime.db.col("escalations").update(escalation.id, { status: body.status });
  });

  /* ------------------------------------------------------------------ */
  /* knowledge                                                           */
  /* ------------------------------------------------------------------ */

  app.get("/v1/knowledge-bases", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.db
      .col("knowledgeBases")
      .list((kb) => kb.tenantId === principal.tenantId)
      .map((kb) => ({ ...kb, documents: kb.documents.map(({ text: _text, ...rest }) => rest) }));
  });

  app.post("/v1/knowledge-bases", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({ name: z.string().min(1), description: z.string().default("") })
      .parse(request.body);
    const now = nowIso();
    const kb: KnowledgeBase = {
      id: newId("kb"),
      tenantId: principal.tenantId,
      name: body.name,
      description: body.description,
      documents: [],
      createdAt: now,
      updatedAt: now,
    };
    runtime.db.col("knowledgeBases").insert(kb);
    return reply.status(201).send(kb);
  });

  app.post("/v1/knowledge-bases/:id/documents", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const kb = ownedKnowledgeBase(runtime, principal, param(request, "id"));
    const body = z
      .object({ title: z.string().min(1), text: z.string().min(1).max(200_000) })
      .parse(request.body);
    const document = {
      id: newId("doc"),
      title: body.title,
      text: body.text,
      createdAt: nowIso(),
      checksum: `${body.text.length}:${body.text.slice(0, 24)}`,
    };
    const updated = runtime.db.col("knowledgeBases").update(kb.id, {
      documents: [...kb.documents, document],
      updatedAt: nowIso(),
    });
    return reply.status(201).send(updated.documents.at(-1));
  });

  app.post("/v1/knowledge-bases/:id/search", async (request) => {
    const principal = requirePrincipal(request);
    const kb = ownedKnowledgeBase(runtime, principal, param(request, "id"));
    const body = z
      .object({ query: z.string().min(1), limit: z.number().int().min(1).max(20).default(5) })
      .parse(request.body);
    const retriever = createRetriever(
      kb.documents.map((document) => ({
        id: document.id,
        title: document.title,
        text: document.text,
      })),
    );
    return { hits: retriever.search(body.query, body.limit) };
  });

  /* ------------------------------------------------------------------ */
  /* credentials                                                         */
  /* ------------------------------------------------------------------ */

  app.get("/v1/credentials", async (request) => {
    const principal = requirePrincipal(request);
    return runtime.credentials.list(principal.tenantId);
  });

  app.put("/v1/credentials/:name", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    const body = z
      .object({ value: z.string().min(1).max(10_000), provider: z.string().max(60).default("custom") })
      .parse(request.body);
    await runtime.credentials.set(
      principal.tenantId,
      param(request, "name").toUpperCase(),
      body.value,
      body.provider,
    );
    audit(runtime, principal, "credential.set", param(request, "name").toUpperCase(), "allowed");
    return { ok: true, name: param(request, "name").toUpperCase() };
  });

  app.delete("/v1/credentials/:name", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "admin");
    const removed = runtime.credentials.remove(principal.tenantId, param(request, "name").toUpperCase());
    if (!removed) throw new OmallaError("not_found", "credential not found", 404);
    return reply.status(204).send();
  });

  /* ------------------------------------------------------------------ */
  /* inbound webhooks (OM-T1 #5 + OM-T3 raw-byte HMAC + replay cache)     */
  /* ------------------------------------------------------------------ */

  app.post("/v1/hooks/:path", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const pathSuffix = param(request, "path");
    const flatHeaders: Record<string, string | undefined> = {};
    for (const [k, v] of Object.entries(request.headers)) {
      if (typeof v === "string") flatHeaders[k.toLowerCase()] = v;
      else if (Array.isArray(v)) flatHeaders[k.toLowerCase()] = v.join(", ");
    }

    const secret = await runtime.credentials.get(principal.tenantId, "WEBHOOK_SECRET");
    let eventKey: string | undefined;

    if (secret) {
      if (!request.rawBody) {
        audit(runtime, principal, "webhook.reject", pathSuffix, "denied");
        throw new OmallaError("unauthorized", "signed webhook requires raw request body", 401);
      }
      const check = verifySignedWebhookRaw({
        rawBody: request.rawBody,
        headers: flatHeaders,
        secret,
      });
      if (!check.valid) {
        audit(runtime, principal, "webhook.reject", pathSuffix, "denied");
        throw new OmallaError("unauthorized", check.reason ?? "invalid webhook signature", 401);
      }
      eventKey = check.eventKey;
    } else {
      eventKey =
        flatHeaders["webhook-id"] ??
        flatHeaders["svix-id"] ??
        flatHeaders["x-omalla-delivery-id"];
    }

    if (eventKey) {
      const fresh = runtime.replayCache.claimEvent(principal.tenantId, `webhook:${pathSuffix}`, eventKey);
      if (!fresh) {
        audit(runtime, principal, "webhook.replay_reject", pathSuffix, "denied");
        throw new OmallaError("conflict", "replayed webhook event rejected (OM-T3)", 409);
      }
    }

    const idempotencyKey = extractIdempotencyKey(request);
    const run = await runtime.runWebhook(
      principal.tenantId,
      pathSuffix,
      (request.body ?? {}) as JsonValue,
      idempotencyKey,
    );
    audit(runtime, principal, "webhook.run", pathSuffix, "allowed");
    return reply.status(202).send({ runId: run.id, status: run.status });
  });

  /* ------------------------------------------------------------------ */
  /* dashboard                                                           */
  /* ------------------------------------------------------------------ */

  app.get("/", async (_request, reply) => sendAsset(reply, "index.html"));
  app.get("/app.js", async (_request, reply) => sendAsset(reply, "app.js"));
  app.get("/styles.css", async (_request, reply) => sendAsset(reply, "styles.css"));

  return app;
}

/* ------------------------------------------------------------------ */
/* helpers & schemas                                                   */
/* ------------------------------------------------------------------ */

const tenantSettingsBody = z.object({
  recordingEnabled: z.boolean().optional(),
  outboundEnabled: z.boolean().optional(),
  outboundAllowlist: z.array(z.string()).optional(),
  dncList: z.array(z.string()).optional(),
  dailyOutboundCap: z.number().int().min(0).max(100_000).optional(),
  maxConcurrentCalls: z.number().int().min(0).max(10_000).optional(),
  dailyMinuteQuota: z.number().min(0).max(1_000_000).optional(),
  monthlyMinuteQuota: z.number().min(0).max(10_000_000).optional(),
  callingWindow: z
    .object({
      start: z.string().regex(/^\d{2}:\d{2}$/),
      end: z.string().regex(/^\d{2}:\d{2}$/),
      days: z.array(z.number().int().min(0).max(6)),
    })
    .optional(),
  callingWindowStart: z.string().regex(/^\d{2}:\d{2}$/).optional(),
  callingWindowEnd: z.string().regex(/^\d{2}:\d{2}$/).optional(),
  callingDays: z.array(z.number().int().min(0).max(6)).optional(),
  retentionDays: z.number().int().min(1).max(3650).optional(),
  timezone: z.string().min(1).max(80).optional(),
});

const toolBody = z.object({
  type: z.enum([
    "function",
    "api_request",
    "transfer",
    "handoff",
    "end_call",
    "dtmf",
    "mcp",
    "query",
    "internal",
    "n8n_workflow",
    "workflow",
  ]),
  name: z.string().min(1).max(64),
  description: z.string().max(2000),
  parameters: z.object({
    type: z.literal("object"),
    properties: z.record(z.string(), z.unknown()),
    required: z.array(z.string()).optional(),
    additionalProperties: z.boolean().optional(),
  }),
  serverUrl: z.string().url().optional(),
  method: z.enum(["GET", "POST", "PUT", "PATCH", "DELETE"]).optional(),
  headers: z.record(z.string(), z.string()).optional(),
  staticBody: z.record(z.string(), z.unknown()).optional(),
  trustedFields: z.record(z.string(), z.unknown()).optional(),
  timeoutMs: z.number().int().min(500).max(60_000).optional(),
  destinations: z.array(z.string()).optional(),
  knowledgeBaseId: z.string().optional(),
  workflowId: z.string().optional(),
  mcpServerUrl: z.string().url().optional(),
  internalAction: z
    .enum(["create_booking", "create_task", "upsert_contact", "escalate", "lookup_order"])
    .optional(),
  riskLevel: z.enum(["low", "standard", "high"]).optional(),
  requiresVerifiedCaller: z.boolean().optional(),
  messages: z
    .object({
      onRequest: z.string().optional(),
      onResult: z.string().optional(),
      onError: z.string().optional(),
    })
    .optional(),
});

const workflowBody = z.object({
  name: z.string().min(1).max(160),
  description: z.string().max(1000).optional(),
  status: z.enum(["draft", "active", "archived"]).optional(),
  trigger: z
    .object({ type: z.enum(TRIGGER_TYPES), config: z.record(z.string(), z.unknown()) })
    .optional(),
  nodes: z
    .array(
      z.object({
        id: z.string().min(1),
        type: z.enum(NODE_TYPES),
        name: z.string().min(1),
        config: z.record(z.string(), z.unknown()).default({}),
        retry: z.object({ attempts: z.number().int().min(1).max(5), backoffMs: z.number().int().min(0) }).optional(),
        timeoutMs: z.number().int().min(500).max(300_000).optional(),
      }),
    )
    .optional(),
  edges: z
    .array(z.object({ from: z.string(), to: z.string(), when: z.string().optional() }))
    .optional(),
  idempotencyWindowSec: z.number().int().min(0).max(86_400).optional(),
});

/**
 * OM-T1: validates that every referenced KB, post-call workflow, and inline tool
 * belongs strictly to `tenantId`, preventing cross-tenant attach or ID overwrite.
 */
function sanitizeAndAssertAgentConfig(
  runtime: OmallaRuntime,
  tenantId: string,
  config: AgentConfig,
): AgentConfig {
  for (const kbId of config.knowledgeBaseIds) {
    const kb = runtime.db.col("knowledgeBases").get(kbId);
    if (!kb || kb.tenantId !== tenantId) {
      throw new OmallaError("not_found", `knowledge base ${kbId} not found`, 404);
    }
  }
  if (config.postCallWorkflowId) {
    const wf = runtime.db.col("workflows").get(config.postCallWorkflowId);
    if (!wf || wf.tenantId !== tenantId) {
      throw new OmallaError("not_found", `workflow ${config.postCallWorkflowId} not found`, 404);
    }
  }

  const now = nowIso();
  const sanitizedTools: ToolDefinition[] = config.tools.map((rawTool) => {
    const toolId = rawTool.id || newId("tool");
    const existing = runtime.db.col("tools").get(toolId);
    if (existing && existing.tenantId !== tenantId) {
      throw new OmallaError("not_found", `tool ${toolId} not found`, 404);
    }
    assertToolReferencesOwned(runtime, tenantId, rawTool);
    return {
      ...rawTool,
      id: toolId,
      tenantId,
      createdAt: existing?.createdAt ?? rawTool.createdAt ?? now,
      updatedAt: now,
    };
  });

  return {
    ...config,
    tools: sanitizedTools,
  };
}

function assertToolReferencesOwned(
  runtime: OmallaRuntime,
  tenantId: string,
  tool: { knowledgeBaseId?: string; workflowId?: string },
): void {
  if (tool.knowledgeBaseId) {
    const kb = runtime.db.col("knowledgeBases").get(tool.knowledgeBaseId);
    if (!kb || kb.tenantId !== tenantId) {
      throw new OmallaError("not_found", `knowledge base ${tool.knowledgeBaseId} not found`, 404);
    }
  }
  if (tool.workflowId) {
    const wf = runtime.db.col("workflows").get(tool.workflowId);
    if (!wf || wf.tenantId !== tenantId) {
      throw new OmallaError("not_found", `workflow ${tool.workflowId} not found`, 404);
    }
  }
}

export function extractIdempotencyKey(request: FastifyRequest): string | undefined {
  const std = request.headers["idempotency-key"];
  const legacy = request.headers["x-idempotency-key"];
  const raw = typeof std === "string" ? std : typeof legacy === "string" ? legacy : undefined;
  const trimmed = raw?.trim();
  return trimmed && trimmed.length > 0 ? trimmed.slice(0, 200) : undefined;
}

export async function executeIdempotent<T>(
  runtime: OmallaRuntime,
  request: FastifyRequest,
  reply: FastifyReply,
  options: {
    tenantId: string;
    scope: string;
    idemKey: string | undefined;
    payload: unknown;
  },
  work: () => Promise<{ statusCode: number; body: T }>,
): Promise<unknown> {
  if (!options.idemKey) {
    const out = await work();
    return reply.status(out.statusCode).send(out.body);
  }

  const clientDigestHeader = request.headers["x-omalla-args-digest"];
  const clientDigest =
    typeof clientDigestHeader === "string" ? clientDigestHeader.trim().toLowerCase() : undefined;

  const claim = runtime.idempotencyManager.claim({
    tenantId: options.tenantId,
    scope: options.scope,
    idemKey: options.idemKey,
    payload: options.payload,
    ...(request.rawBody ? { rawJson: request.rawBody.toString("utf8") } : {}),
  });

  if (clientDigest && clientDigest !== claim.argsDigest.toLowerCase()) {
    if (claim.kind === "claimed") {
      runtime.idempotencyManager.releasePreDispatch(options.tenantId, options.scope, options.idemKey);
    }
    throw new OmallaError(
      "validation",
      "x-omalla-args-digest does not match server JCS SHA-256 digest",
      400,
    );
  }

  if (claim.kind === "replayed") {
    reply.header("x-idempotency-replayed", "true");
    return reply.status(claim.statusCode).send(claim.response);
  }

  try {
    const out = await work();
    runtime.idempotencyManager.complete({
      tenantId: options.tenantId,
      scope: options.scope,
      idemKey: options.idemKey,
      statusCode: out.statusCode,
      response: out.body,
    });
    return reply.status(out.statusCode).send(out.body);
  } catch (error) {
    if (isOmallaError(error) && (error.status === 400 || error.status === 403 || error.status === 404 || error.status === 409)) {
      runtime.idempotencyManager.releasePreDispatch(options.tenantId, options.scope, options.idemKey);
    }
    throw error;
  }
}

function mergeConfig(base: AgentConfig, patch: Record<string, unknown>): AgentConfig {
  const next = { ...base, ...patch } as AgentConfig;
  next.model = { ...base.model, ...(patch.model as object | undefined) };
  next.voice = { ...base.voice, ...(patch.voice as object | undefined) };
  next.transcriber = { ...base.transcriber, ...(patch.transcriber as object | undefined) };
  next.interruption = { ...base.interruption, ...(patch.interruption as object | undefined) };
  next.recording = { ...base.recording, ...(patch.recording as object | undefined) };
  if (!Array.isArray(next.tools)) next.tools = [];
  if (!Array.isArray(next.knowledgeBaseIds)) next.knowledgeBaseIds = [];
  if (!Array.isArray(next.endCallPhrases)) next.endCallPhrases = [...base.endCallPhrases];
  return next;
}

function clientKey(request: FastifyRequest): string {
  return request.ip ?? "unknown";
}

function actorOf(principal: Principal): string {
  return principal.apiKeyId ?? principal.userId ?? "system";
}

function authenticate(
  runtime: OmallaRuntime,
  request: FastifyRequest,
  limiter: RateLimiter,
  allowQuery = false,
): Principal {
  const header = request.headers.authorization;
  const bearer = header?.startsWith("Bearer ") ? header.slice(7).trim() : undefined;
  const alt = request.headers["x-omalla-key"];
  const query = allowQuery ? new URL(request.raw.url ?? "", "http://local").searchParams.get("token") : null;
  const token = bearer ?? (typeof alt === "string" ? alt : undefined) ?? query ?? undefined;
  if (!token) throw new OmallaError("unauthorized", "missing API key", 401);
  const limit = limiter.take(`${clientKey(request)}:${token.slice(0, 8)}`);
  if (!limit.allowed) throw new OmallaError("rate_limited", "too many authentication attempts", 429);
  return runtime.authenticate(token);
}

function requirePrincipal(request: FastifyRequest): Principal {
  if (!request.principal) throw new OmallaError("unauthorized", "missing API key", 401);
  return request.principal;
}

function param(request: FastifyRequest, name: string): string {
  const value = (request.params as Record<string, string | undefined>)[name];
  if (!value) throw new OmallaError("validation", `missing ${name}`, 400);
  return value;
}

function ownedAgent(runtime: OmallaRuntime, principal: Principal, id: string): Agent {
  const agent = runtime.db.col("agents").get(id);
  if (!agent || agent.tenantId !== principal.tenantId) {
    throw new OmallaError("not_found", "agent not found", 404);
  }
  return agent;
}

function ownedTool(runtime: OmallaRuntime, principal: Principal, id: string): ToolDefinition {
  const tool = runtime.db.col("tools").get(id);
  if (!tool || tool.tenantId !== principal.tenantId) {
    throw new OmallaError("not_found", "tool not found", 404);
  }
  return tool;
}

function ownedCall(runtime: OmallaRuntime, principal: Principal, id: string): Call {
  const call = runtime.db.col("calls").get(id);
  if (!call || call.tenantId !== principal.tenantId) {
    throw new OmallaError("not_found", "call not found", 404);
  }
  return call;
}

function ownedWorkflow(runtime: OmallaRuntime, principal: Principal, id: string): Workflow {
  const workflow = runtime.db.col("workflows").get(id);
  if (!workflow || workflow.tenantId !== principal.tenantId) {
    throw new OmallaError("not_found", "workflow not found", 404);
  }
  return workflow;
}

function ownedKnowledgeBase(runtime: OmallaRuntime, principal: Principal, id: string): KnowledgeBase {
  const kb = runtime.db.col("knowledgeBases").get(id);
  if (!kb || kb.tenantId !== principal.tenantId) {
    throw new OmallaError("not_found", "knowledge base not found", 404);
  }
  return kb;
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

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
};

async function sendAsset(reply: FastifyReply, file: string): Promise<unknown> {
  const base = path.resolve(DASHBOARD_DIR);
  const target = path.resolve(base, file);
  if (!target.startsWith(base)) {
    return reply.status(403).send({ error: { code: "forbidden", message: "invalid asset" } });
  }
  try {
    const data = await readFile(target);
    const extension = path.extname(target);
    return reply.type(MIME[extension] ?? "application/octet-stream").send(data);
  } catch {
    return reply
      .status(404)
      .type("text/html; charset=utf-8")
      .send(
        "<!doctype html><meta charset=\"utf-8\"><title>Omalla</title><body style=\"font-family:system-ui;padding:40px;background:#0b0d10;color:#e6e8eb\"><h1>Omalla is running</h1><p>The API is live at <code>/v1</code>. The dashboard assets were not found in <code>apps/dashboard/public</code>.</p></body>",
      );
  }
}
