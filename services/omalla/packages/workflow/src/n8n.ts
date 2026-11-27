import { newId, nowIso } from "@omalla/core";
import type { JsonValue, Workflow, WorkflowEdge, WorkflowNode, WorkflowTrigger } from "@omalla/core";

/**
 * n8n interoperability.
 *
 * Import is best-effort by design: n8n executes arbitrary JavaScript in Code
 * nodes, which Omalla will not run inside its own process. Unsupported nodes
 * are imported as explicit, disabled markers rather than silently dropped.
 */

export interface N8nNode {
  name?: string;
  type?: string;
  parameters?: Record<string, unknown>;
  position?: [number, number];
  disabled?: boolean;
}

export interface N8nConnection {
  main?: Array<Array<{ node?: string; type?: string; index?: number }>>;
}

export interface N8nWorkflow {
  name?: string;
  nodes?: N8nNode[];
  connections?: Record<string, N8nConnection>;
  meta?: Record<string, unknown>;
}

export interface ImportResult {
  workflow: Workflow;
  warnings: string[];
}

export function importN8nWorkflow(json: unknown, tenantId: string): ImportResult {
  const source = (json ?? {}) as N8nWorkflow;
  const warnings: string[] = [];
  const nodes: WorkflowNode[] = [];
  const byName = new Map<string, string>();

  for (const [index, n8nNode] of (source.nodes ?? []).entries()) {
    const name = n8nNode.name ?? `Node ${index + 1}`;
    const id = `n${index + 1}`;
    byName.set(name, id);
    const params = n8nNode.parameters ?? {};
    const type = n8nNode.type ?? "";

    if (type.includes("webhook")) {
      nodes.push({
        id,
        type: "trigger",
        name,
        config: {
          source: "n8n",
          path: String(params.path ?? "webhook"),
          method: String(params.httpMethod ?? "POST"),
          note: "Imported n8n webhook trigger; configure the Omalla path in the trigger settings.",
        },
      });
      continue;
    }
    if (type.includes("scheduleTrigger") || type.includes("cron")) {
      nodes.push({
        id,
        type: "trigger",
        name,
        config: {
          source: "n8n",
          cron: String((params.rule as Record<string, unknown> | undefined)?.cronExpression ?? "0 9 * * *"),
        },
      });
      continue;
    }
    if (type.includes("httpRequest")) {
      nodes.push({
        id,
        type: "http",
        name,
        config: {
          url: String(params.url ?? ""),
          method: String(params.method ?? "POST"),
          headers: (params.headerParameters as JsonValue) ?? {},
          body: (params.bodyParameters as JsonValue) ?? (params.jsonBody as JsonValue) ?? {},
        },
        retry: { attempts: 2, backoffMs: 500 },
      });
      continue;
    }
    if (type.includes("trello")) {
      const operation = String(params.operation ?? "create");
      const listId = String(params.listId ?? "");
      nodes.push({
        id,
        type: operation === "create" ? "trello.create_card" : "trello.update_card",
        name,
        config: { listId, name: "{{trigger.name}}", desc: "{{trigger.description}}" },
        retry: { attempts: 2, backoffMs: 500 },
      });
      continue;
    }
    if (type.includes(".if")) {
      nodes.push({
        id,
        type: "branch",
        name,
        config: { condition: "exists(trigger.payload)" },
      });
      warnings.push(`Node "${name}": n8n IF conditions were imported as a presence check; review the condition.`);
      continue;
    }
    if (type.includes(".set")) {
      const values = (params.values as Record<string, JsonValue> | undefined) ?? {};
      nodes.push({ id, type: "set", name, config: { values } });
      continue;
    }
    if (type.includes("respondToWebhook")) {
      nodes.push({ id, type: "end", name, config: { respond: true } });
      continue;
    }
    if (type.includes(".code")) {
      nodes.push({
        id,
        type: "set",
        name: `${name} (code not imported)`,
        config: { values: {}, note: "n8n Code nodes are not executed by Omalla." },
      });
      warnings.push(`Node "${name}": Code execution is not imported for security reasons.`);
      continue;
    }
    if (type.includes("noOp")) {
      nodes.push({ id, type: "set", name, config: { values: {} } });
      continue;
    }

    nodes.push({
      id,
      type: "set",
      name: `${name} (unsupported: ${type})`,
      config: {
        values: {},
        note: `Node type ${type} is not mapped; replace it with an Omalla node.`,
      },
    });
    warnings.push(`Node "${name}": type ${type || "unknown"} is not mapped.`);
  }

  const edges: WorkflowEdge[] = [];
  for (const [nodeName, connection] of Object.entries(source.connections ?? {})) {
    const from = byName.get(nodeName);
    if (!from) continue;
    connection.main?.forEach((outputs, outputIndex) => {
      for (const target of outputs ?? []) {
        const to = target.node ? byName.get(target.node) : undefined;
        if (!to) continue;
        const branchLabel = outputIndex === 0 ? "true" : outputIndex === 1 ? "false" : undefined;
        const fromNode = nodes.find((node) => node.id === from);
        edges.push({
          from,
          to,
          ...(fromNode?.type === "branch" && branchLabel ? { when: branchLabel } : {}),
        });
      }
    });
  }

  if (!nodes.some((node) => node.type === "trigger")) {
    nodes.unshift({
      id: "n0",
      type: "trigger",
      name: "Manual trigger",
      config: { source: "import", note: "No trigger found in the n8n workflow." },
    });
    if (edges.length === 0 && nodes.length > 1) {
      edges.push({ from: "n0", to: nodes[1]?.id ?? "n1" });
    }
  }

  const trigger: WorkflowTrigger = { type: "webhook", config: { importedFrom: "n8n" } };
  const workflow: Workflow = {
    id: newId("wf"),
    tenantId,
    name: source.name ?? "Imported n8n workflow",
    description: `Imported from n8n${source.meta ? ` (${JSON.stringify(source.meta).slice(0, 200)})` : ""}`,
    status: "draft",
    version: 1,
    trigger,
    nodes,
    edges,
    idempotencyWindowSec: 600,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  };

  return { workflow, warnings };
}

export function exportN8nWorkflow(workflow: Workflow): N8nWorkflow {
  const nodes: N8nNode[] = [];
  const connections: Record<string, N8nConnection> = {};
  const nameById = new Map(workflow.nodes.map((node) => [node.id, node.name]));

  for (const node of workflow.nodes) {
    if (node.type === "trigger") {
      nodes.push({
        name: node.name,
        type: "n8n-nodes-base.webhook",
        parameters: {
          path: String(node.config.path ?? workflow.id),
          httpMethod: String(node.config.method ?? "POST"),
        },
        position: [0, 0],
      });
      continue;
    }
    if (node.type === "http") {
      nodes.push({
        name: node.name,
        type: "n8n-nodes-base.httpRequest",
        parameters: {
          url: String(node.config.url ?? ""),
          method: String(node.config.method ?? "POST"),
          jsonBody: node.config.body ?? {},
        },
      });
      continue;
    }
    if (node.type.startsWith("trello.")) {
      nodes.push({
        name: node.name,
        type: "n8n-nodes-base.trello",
        parameters: {
          operation: node.type === "trello.create_card" ? "create" : "update",
          listId: String(node.config.listId ?? ""),
        },
      });
      continue;
    }
    if (node.type === "branch") {
      nodes.push({
        name: node.name,
        type: "n8n-nodes-base.if",
        parameters: { condition: String(node.config.condition ?? "") },
      });
      continue;
    }
    if (node.type === "end") {
      nodes.push({
        name: node.name,
        type: "n8n-nodes-base.respondToWebhook",
        parameters: { respondWith: "json" },
      });
      continue;
    }
    nodes.push({
      name: node.name,
      type: "n8n-nodes-base.noOp",
      parameters: { omallaNodeType: node.type },
    });
  }

  for (const edge of workflow.edges) {
    const fromName = nameById.get(edge.from);
    const toName = nameById.get(edge.to);
    if (!fromName || !toName) continue;
    const outputIndex = edge.when === "false" ? 1 : 0;
    const existing = connections[fromName] ?? { main: [] as NonNullable<N8nConnection["main"]> };
    const main = existing.main ?? [];
    while (main.length <= outputIndex) main.push([]);
    main[outputIndex]?.push({ node: toName, type: "main", index: outputIndex });
    existing.main = main;
    connections[fromName] = existing;
  }

  return {
    name: workflow.name,
    nodes,
    connections,
    meta: { omallaWorkflowId: workflow.id, omallaVersion: workflow.version },
  };
}
