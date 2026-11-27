import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { newId, nowIso } from "@omalla/core";
import type { ToolCallContext, ToolDefinition } from "@omalla/core";
import { OmallaRuntime, loadConfig } from "@omalla/server";

let dir = "";
let runtime: OmallaRuntime;
let tenantId = "";
let agentId = "";
let callId = "";
let captured: { url: string; init: RequestInit } | undefined;

function context(): ToolCallContext {
  return {
    callId,
    tenantId,
    agentId,
    agentName: "Test agent",
    direction: "inbound",
    callerNumber: "+15550001111",
    variables: {},
    trusted: { callId, tenantId, callerNumber: "+15550001111" },
  };
}

function tool(overrides: Partial<ToolDefinition>): ToolDefinition {
  const now = nowIso();
  return {
    id: newId("tool"),
    tenantId,
    type: "n8n_workflow",
    name: "test_tool",
    description: "Test tool",
    parameters: { type: "object", properties: {} },
    createdAt: now,
    updatedAt: now,
    ...overrides,
  };
}

before(async () => {
  dir = await mkdtemp(path.join(tmpdir(), "omalla-tools-"));
  const config = loadConfig({
    dataDir: dir,
    seedDemo: true,
    allowPrivateHttp: true,
    publicBaseUrl: "http://127.0.0.1:8787",
    masterKey: Buffer.alloc(32, 9).toString("base64"),
  });
  runtime = await OmallaRuntime.open(config, {
    offlineProviders: true,
    fetchImpl: async (input, init) => {
      captured = { url: String(input), init: init ?? {} };
      if (String(input).includes("/fail")) {
        return new Response(JSON.stringify({ message: "workflow error" }), {
          status: 500,
          headers: { "content-type": "application/json" },
        });
      }
      return new Response(
        JSON.stringify({ id: "n8n-run-1", speech: "Your appointment is at 3pm.", ok: true }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    },
  });
  const tenant = runtime.db.col("tenants").list()[0];
  assert.ok(tenant);
  tenantId = tenant.id;
  agentId = runtime.db.col("agents").list((candidate) => candidate.tenantId === tenantId)[0]?.id ?? "";
  callId = newId("call");
  await runtime.credentials.set(tenantId, "N8N_WEBHOOK_SECRET", "n8n-secret");
});

after(async () => {
  await runtime?.close();
  if (dir) await rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
});

test("the n8n_workflow tool signs the live payload and returns spoken text", async () => {
  const definition = tool({
    name: "check_calendar",
    type: "n8n_workflow",
    serverUrl: "https://n8n.example.com/webhook/check-calendar",
    staticBody: { source: "voice" },
  });
  runtime.db.col("tools").insert(definition);

  const result = await runtime.tools.execute({
    toolId: definition.id,
    name: definition.name,
    args: { when: "Friday at 3pm" },
    context: context(),
  });

  assert.equal(result.ok, true, result.error);
  assert.equal(result.speech, "Your appointment is at 3pm.");
  assert.ok(captured);
  assert.equal(captured?.url, "https://n8n.example.com/webhook/check-calendar");
  const body = String(captured?.init.body);
  const payload = JSON.parse(body) as Record<string, unknown>;
  assert.deepEqual(payload.source, "voice");
  assert.deepEqual(payload.when, "Friday at 3pm");
  assert.equal((payload.omalla as Record<string, unknown>).callId, callId);
  assert.equal((payload.omalla as Record<string, unknown>).callerNumber, "+15550001111");
  assert.equal((payload.omalla as Record<string, unknown>).event, "voice_tool");

  const headers = captured?.init.headers as Record<string, string>;
  const expected = createHmac("sha256", "n8n-secret").update(body).digest("hex");
  assert.equal(headers["x-omalla-signature"], `sha256=${expected}`);
  assert.doesNotMatch(body, /n8n-secret/);
});

test("the n8n_workflow tool surfaces HTTP failures as retryable errors", async () => {
  const definition = tool({
    name: "failing_flow",
    serverUrl: "https://n8n.example.com/webhook/fail",
  });
  runtime.db.col("tools").insert(definition);

  const result = await runtime.tools.execute({
    toolId: definition.id,
    name: definition.name,
    args: {},
    context: context(),
  });
  assert.equal(result.ok, false);
  assert.match(result.error ?? "", /500/);
  assert.equal(result.retryable, true);
});

test("a native workflow runs as a live tool without n8n and is idempotent", async () => {
  const workflow = runtime.installTemplate("task_ticket", tenantId);
  runtime.db.col("workflows").update(workflow.id, { ...workflow, status: "active" });

  const definition = tool({
    name: "open_ticket",
    type: "workflow",
    workflowId: workflow.id,
  });
  runtime.db.col("tools").insert(definition);

  const args = { title: "Broken meter", description: "Caller reports a faulty meter", priority: "high" };
  const first = await runtime.tools.execute({
    toolId: definition.id,
    name: definition.name,
    args,
    context: context(),
  });
  assert.equal(first.ok, true, first.error);
  const firstResult = first.result as { runId: string; output: { id?: string; title?: string } };
  assert.equal(firstResult.output.title, "Broken meter");

  const tasks = runtime.db
    .col("tasks")
    .list((candidate) => candidate.tenantId === tenantId && candidate.title === "Broken meter");
  assert.equal(tasks.length, 1);

  const retry = await runtime.tools.execute({
    toolId: definition.id,
    name: definition.name,
    args,
    context: context(),
  });
  assert.equal(retry.ok, true, retry.error);
  assert.equal((retry.result as { deduplicated?: boolean }).deduplicated, true);
  const afterRetry = runtime.db
    .col("tasks")
    .list((candidate) => candidate.tenantId === tenantId && candidate.title === "Broken meter");
  assert.equal(afterRetry.length, 1);
});

test("a draft workflow cannot be run from a live call", async () => {
  const workflow = runtime.installTemplate("customer_support", tenantId);
  const definition = tool({
    name: "draft_flow",
    type: "workflow",
    workflowId: workflow.id,
  });
  runtime.db.col("tools").insert(definition);

  const result = await runtime.tools.execute({
    toolId: definition.id,
    name: definition.name,
    args: {},
    context: context(),
  });
  assert.equal(result.ok, false);
  assert.match(result.error ?? "", /not active/);
});
