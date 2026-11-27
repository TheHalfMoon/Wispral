import { newId, nowIso, OmallaError } from "@omalla/core";
import type {
  JsonValue,
  Logger,
  Workflow,
  WorkflowRun,
  WorkflowStep,
  WorkflowTrigger,
} from "@omalla/core";
import type { Scope } from "./expressions.js";
import { evaluateCondition, renderDeep } from "./expressions.js";
import { defaultHandlers, type NodeHandler, type WorkflowServices } from "./nodes.js";

export interface IdempotencyStore {
  has(key: string): boolean;
  remember(key: string, ttlSeconds: number): void;
}

export interface EngineOptions {
  handlers?: Record<string, NodeHandler>;
  /** Overrides fetch for dry runs and tests. */
  fetchOverride?: typeof fetch;
  maxSteps?: number;
}

export interface RunOptions {
  trigger?: { type: WorkflowTrigger["type"]; payload: JsonValue };
  idempotencyKey?: string;
  callId?: string;
  variables?: Record<string, JsonValue>;
  dryRun?: boolean;
}

/**
 * Graph executor.
 *
 * Deterministic: the same workflow, trigger and context produce the same node
 * order. Side effects are isolated in node handlers, each with its own retry
 * policy, so a failed Trello call never re-sends an SMS.
 */
export class WorkflowEngine {
  private readonly handlers: Record<string, NodeHandler>;

  constructor(
    private readonly services: WorkflowServices,
    private readonly idempotency: IdempotencyStore,
    private readonly options: EngineOptions = {},
  ) {
    this.handlers = { ...defaultHandlers, ...(options.handlers ?? {}) };
  }

  async run(workflow: Workflow, options: RunOptions = {}): Promise<WorkflowRun> {
    const startedAt = nowIso();
    const trigger = options.trigger ?? { type: workflow.trigger.type, payload: {} };
    const idempotencyKey = options.idempotencyKey;

    const baseRun: WorkflowRun = {
      id: newId("run"),
      tenantId: workflow.tenantId,
      workflowId: workflow.id,
      workflowVersion: workflow.version,
      status: "running",
      trigger,
      ...(idempotencyKey ? { idempotencyKey } : {}),
      context: { ...(options.variables ?? {}) },
      steps: [],
      startedAt,
      ...(options.callId ? { callId: options.callId } : {}),
    };

    if (idempotencyKey && this.idempotency.has(idempotencyKey)) {
      return {
        ...baseRun,
        status: "skipped",
        endedAt: startedAt,
        context: { ...baseRun.context, idempotencyKey },
      };
    }
    if (idempotencyKey) {
      this.idempotency.remember(idempotencyKey, workflow.idempotencyWindowSec);
    }

    const services: WorkflowServices = {
      ...this.services,
      ...(options.dryRun ? { fetch: createDryFetch(workflow, this.services.logger) } : {}),
      ...(this.options.fetchOverride ? { fetch: this.options.fetchOverride } : {}),
    };

    const scope: Scope = {
      trigger,
      context: baseRun.context,
      nodes: {} as Record<string, unknown>,
      env: safeEnv(),
      run: { id: baseRun.id, workflowId: workflow.id },
    };

    let currentNode = workflow.nodes.find((node) => node.type === "trigger") ?? workflow.nodes[0];
    if (!currentNode) {
      return { ...baseRun, status: "failed", endedAt: nowIso(), error: "workflow has no nodes" };
    }

    const maxSteps = this.options.maxSteps ?? 100;
    let steps = 0;
    const controller = new AbortController();
    const deadline = Date.now() + 5 * 60_000;

    while (currentNode && steps < maxSteps) {
      steps += 1;
      if (Date.now() > deadline) {
        baseRun.error = "workflow exceeded its 5 minute budget";
        break;
      }
      const node = currentNode;
      const step = await this.executeNode(workflow, node.id, scope, services, controller.signal, baseRun);
      baseRun.steps.push(step);
      if (step.status === "failed") {
        baseRun.status = "failed";
        baseRun.error = step.error ?? "node failed";
        break;
      }
      if (step.output !== undefined) {
        const previous = (scope.nodes as Record<string, { branch?: string }>)[node.id];
        (scope.nodes as Record<string, unknown>)[node.id] = {
          output: step.output,
          ...(previous?.branch ? { branch: previous.branch } : {}),
        };
      }
      baseRun.context = scope.context as Record<string, JsonValue>;

      const outcome = (scope.nodes as Record<string, { output?: unknown; branch?: string }>)[node.id];
      currentNode = this.nextNode(workflow, node.id, outcome?.branch);
    }

    if (baseRun.status === "running") baseRun.status = "succeeded";
    baseRun.endedAt = nowIso();
    baseRun.context = scope.context as Record<string, JsonValue>;
    return baseRun;
  }

  private nextNode(workflow: Workflow, from: string, branch?: string) {
    const edges = workflow.edges.filter((edge) => edge.from === from);
    if (edges.length === 0) return undefined;
    if (branch) {
      const matched = edges.find((edge) => edge.when === branch);
      if (matched) return workflow.nodes.find((node) => node.id === matched.to);
    }
    const unconditional = edges.filter((edge) => !edge.when);
    if (unconditional.length > 0) {
      return workflow.nodes.find((node) => node.id === unconditional[0]?.to);
    }
    return undefined;
  }

  private async executeNode(
    workflow: Workflow,
    nodeId: string,
    scope: Scope,
    services: WorkflowServices,
    signal: AbortSignal,
    run: WorkflowRun,
  ): Promise<WorkflowStep> {
    const node = workflow.nodes.find((candidate) => candidate.id === nodeId);
    const startedAt = nowIso();
    if (!node) {
      return {
        id: newId("step"),
        nodeId,
        nodeType: "end",
        status: "failed",
        startedAt,
        endedAt: startedAt,
        attempts: 0,
        error: `missing node ${nodeId}`,
      };
    }

    const handler = this.handlers[node.type];
    if (!handler) {
      return {
        id: newId("step"),
        nodeId,
        nodeType: node.type,
        status: "failed",
        startedAt,
        endedAt: startedAt,
        attempts: 0,
        error: `unsupported node type ${node.type}`,
      };
    }

    const attemptsAllowed = Math.max(1, Math.min(node.retry?.attempts ?? 1, 5));
    const backoffMs = Math.max(0, node.retry?.backoffMs ?? 250);
    let lastError = "";

    for (let attempt = 1; attempt <= attemptsAllowed; attempt += 1) {
      try {
        if (signal.aborted) throw new OmallaError("timeout", "run aborted", 499);
        const outcome = await withTimeout(
          handler({
            node,
            run,
            scope,
            services,
            signal,
          }),
          node.timeoutMs ?? 20_000,
        );

        if (outcome.contextPatch) {
          Object.assign(scope.context as Record<string, JsonValue>, outcome.contextPatch);
        }
        if (outcome.branch) {
          (scope.nodes as Record<string, unknown>)[node.id] = {
            output: outcome.output,
            branch: outcome.branch,
          };
        }
        return {
          id: newId("step"),
          nodeId,
          nodeType: node.type,
          status: "succeeded",
          startedAt,
          endedAt: nowIso(),
          attempts: attempt,
          input: renderDeep((node.config ?? {}) as JsonValue, scope),
          output: outcome.output,
        };
      } catch (error) {
        lastError = (error as Error).message;
        if (attempt < attemptsAllowed) {
          await services.sleep(backoffMs * attempt);
        }
      }
    }

    return {
      id: newId("step"),
      nodeId,
      nodeType: node.type,
      status: "failed",
      startedAt,
      endedAt: nowIso(),
      attempts: attemptsAllowed,
      error: lastError,
    };
  }
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new OmallaError("timeout", `node exceeded ${ms}ms`, 504)), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

function safeEnv(): Record<string, string> {
  // Only non-secret configuration is exposed to workflow expressions.
  const allow = ["NODE_ENV", "OMALLA_BASE_URL", "OMALLA_ENV", "OMALLA_BUSINESS_NAME"];
  const out: Record<string, string> = {};
  for (const key of allow) {
    const value = process.env[key];
    if (value) out[key] = value;
  }
  return out;
}

/**
 * Dry-run fetch: every external call is recorded and answered with a synthetic
 * success, so a workflow can be qualified end to end with zero cost and zero
 * outbound network access.
 */
function createDryFetch(workflow: Workflow, logger: Logger): typeof fetch {
  return (async (input: string | URL | Request, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    logger.info("dry-run http", { workflow: workflow.id, url, method: init?.method ?? "GET" });
    const body = {
      simulated: true,
      url,
      method: init?.method ?? "GET",
      id: newId("dry"),
      message: "dry-run response",
    };
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;
}

export function findTriggerNode(workflow: Workflow) {
  return workflow.nodes.find((node) => node.type === "trigger") ?? workflow.nodes[0];
}
