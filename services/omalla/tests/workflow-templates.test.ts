import assert from "node:assert/strict";
import { test } from "node:test";
import { createLogger } from "@omalla/core";
import type { JsonValue, Logger } from "@omalla/core";
import {
  TEMPLATES,
  WorkflowEngine,
  buildTemplate,
  evaluateCondition,
  render,
} from "@omalla/workflow";
import type { AutomationStore, WorkflowServices } from "@omalla/workflow";

const logger: Logger = createLogger({ level: "error", sink: () => {} });

const idempotency = {
  has: () => false,
  remember: () => {},
};

function fakeStore(): AutomationStore & { calls: string[] } {
  const calls: string[] = [];
  return {
    calls,
    async createTask(input) {
      calls.push(`task:${input.title}`);
      return { id: "task_1", type: "task", title: input.title, priority: input.priority } as unknown as JsonValue;
    },
    async updateTask(id) {
      return { id, updated: true } as unknown as JsonValue;
    },
    async createBooking(input) {
      calls.push(`booking:${input.name}`);
      return { id: "booking_1", name: input.name, startAt: input.startAt } as unknown as JsonValue;
    },
    async upsertContact(input) {
      calls.push(`contact:${input.name}`);
      return { id: "contact_1", name: input.name } as unknown as JsonValue;
    },
  };
}

function services(store: AutomationStore): WorkflowServices {
  return {
    logger,
    fetch: (async () => {
      throw new Error("no network is allowed in this test");
    }) as unknown as typeof fetch,
    urlPolicy: { allowPrivate: false },
    now: () => new Date("2026-11-20T12:00:00.000Z"),
    sleep: async () => {},
    secrets: { get: async () => undefined },
    store,
  };
}

test("every bundled template builds a well-formed graph", () => {
  const ids = new Set<string>();
  for (const definition of Object.values(TEMPLATES)) {
    const workflow = definition.build("ten_test");
    assert.equal(workflow.tenantId, "ten_test");
    assert.ok(workflow.nodes.length > 0);
    assert.ok(workflow.nodes.some((node) => node.type === "trigger"));
    ids.add(workflow.id);
    const nodeIds = new Set(workflow.nodes.map((node) => node.id));
    assert.equal(nodeIds.size, workflow.nodes.length, `${definition.id} has duplicate node ids`);
    for (const edge of workflow.edges) {
      assert.ok(nodeIds.has(edge.from), `${definition.id} edge from ${edge.from} is missing`);
      assert.ok(nodeIds.has(edge.to), `${definition.id} edge to ${edge.to} is missing`);
    }
  }
  assert.equal(ids.size, Object.keys(TEMPLATES).length);
});

test("core templates no longer require Trello", () => {
  for (const key of ["ai_receptionist", "appointment_scheduling", "lead_qualification", "task_ticket"] as const) {
    const workflow = buildTemplate(key, "ten_test");
    assert.equal(
      workflow.nodes.some((node) => node.type.startsWith("trello.")),
      false,
      `${key} still depends on Trello`,
    );
  }
});

test("the AI receptionist books, saves the caller and texts without leaving the machine", async () => {
  const store = fakeStore();
  const workflow = buildTemplate("ai_receptionist", "ten_test");
  const engine = new WorkflowEngine(services(store), idempotency);
  const run = await engine.run(workflow, {
    trigger: {
      type: "call_ended",
      payload: {
        callId: "call_1",
        callerNumber: "+15550001111",
        appointment: { name: "Sam Rivera", startAt: "2026-11-24T15:00:00.000Z" },
      },
    },
    callId: "call_1",
  });

  assert.equal(run.status, "succeeded", run.error);
  assert.deepEqual(store.calls, ["booking:Sam Rivera", "contact:Sam Rivera"]);
  const sms = run.steps.find((step) => step.nodeType === "sms.send");
  assert.match(JSON.stringify(sms?.output ?? {}), /2026-11-24T15:00:00.000Z/);
  assert.equal(run.steps.some((step) => step.nodeType.startsWith("trello.")), false);
});

test("the no-booking branch creates a task and escalates", async () => {
  const store = fakeStore();
  const escalations: string[] = [];
  const workflow = buildTemplate("ai_receptionist", "ten_test");
  const engine = new WorkflowEngine(
    {
      ...services(store),
      escalate: async (input) => {
        escalations.push(input.reason);
      },
    },
    idempotency,
  );
  const run = await engine.run(workflow, {
    trigger: { type: "call_ended", payload: { callId: "call_2", callerNumber: "+15550002222" } },
  });
  assert.equal(run.status, "succeeded", run.error);
  assert.deepEqual(store.calls, ["task:Call back +15550002222"]);
  assert.equal(escalations.length, 1);
});

test("the n8n bridge is optional and its dry run never touches the network", async () => {
  const store = fakeStore();
  const workflow = buildTemplate("n8n_bridge", "ten_test");
  const engine = new WorkflowEngine(services(store), idempotency);
  const run = await engine.run(workflow, {
    trigger: { type: "call_ended", payload: { callId: "call_3", callerNumber: "+15550003333" } },
    dryRun: true,
  });
  assert.equal(run.status, "succeeded", run.error);
  const n8nStep = run.steps.find((step) => step.nodeType === "n8n.webhook");
  assert.ok(n8nStep);
  assert.match(JSON.stringify(n8nStep?.output ?? {}), /dryRun|dry-run/i);
});

test("template expressions read both trigger.payload.x and the shorthand trigger.x", () => {
  const scope = {
    trigger: { type: "webhook", payload: { title: "Leak", count: 2 } },
    context: {},
    nodes: {},
    env: {},
    run: { id: "run_1", workflowId: "wf_1" },
  };
  assert.equal(render("{{trigger.title}}", scope), "Leak");
  assert.equal(render("{{trigger.payload.title}}", scope), "Leak");
  assert.equal(render("Ticket: {{trigger.title}} ({{trigger.count}})", scope), "Ticket: Leak (2)");
  assert.equal(evaluateCondition("exists(trigger.title)", scope), true);
  assert.equal(evaluateCondition("exists(trigger.missing)", scope), false);
});
