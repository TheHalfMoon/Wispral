/**
 * OpenAPI 3.1 description of the HTTP API.
 *
 * The document is hand-written but tested against the route table: every
 * documented operation must exist (`app.hasRoute`), and every `/v1` route in
 * the source must be either documented here or listed in `PROVIDER_FACING` /
 * `NOT_JSON`. Carrier webhooks are provider-facing and a WebSocket stream is
 * not representable as a plain request/response, so both are declared outside
 * the document rather than half-described inside it.
 */

type Method = "get" | "post" | "patch" | "put" | "delete";
type Schema = Record<string, unknown>;

const object = (properties: Record<string, Schema> = {}, required: string[] = []): Schema => ({
  type: "object",
  ...(required.length > 0 ? { required } : {}),
  properties,
  additionalProperties: true,
});

const string = (description?: string): Schema => ({ type: "string", ...(description ? { description } : {}) });
const integer = (minimum?: number, maximum?: number): Schema => ({
  type: "integer",
  ...(minimum !== undefined ? { minimum } : {}),
  ...(maximum !== undefined ? { maximum } : {}),
});
const boolean = (): Schema => ({ type: "boolean" });
const arrayOf = (items: Schema): Schema => ({ type: "array", items });
const ref = (name: string): Schema => ({ $ref: `#/components/schemas/${name}` });
const json = (schema: Schema): Schema => ({ "application/json": { schema } });

const ENTITY = object({ id: string() }, ["id"]);
const GENERIC = object();

interface Operation {
  method: Method;
  /** OpenAPI path with `{param}` placeholders. */
  path: string;
  tag: string;
  id: string;
  summary: string;
  request?: Schema;
  response?: Schema;
  status?: number;
  public?: boolean;
}

const list = (item: string): Schema => arrayOf(ref(item));

const OPERATIONS: Operation[] = [
  {
    method: "get",
    path: "/v1/health",
    tag: "system",
    id: "getHealth",
    summary: "Liveness, version and the configured telephony default",
    response: ref("Health"),
    public: true,
  },
  { method: "get", path: "/v1/me", tag: "system", id: "getMe", summary: "Principal and tenant for the API key", response: object({ principal: object(), tenant: object() }) },
  { method: "patch", path: "/v1/tenant/settings", tag: "system", id: "updateTenantSettings", summary: "Update tenant policy, DNC list, calling window and quotas", request: GENERIC, response: object() },
  { method: "get", path: "/v1/metrics", tag: "system", id: "getMetrics", summary: "Counts and latency metrics for the tenant", response: GENERIC },

  { method: "get", path: "/v1/keys", tag: "keys", id: "listKeys", summary: "List API keys (never their hashes)", response: list("ApiKey") },
  {
    method: "post",
    path: "/v1/keys",
    tag: "keys",
    id: "createKey",
    summary: "Issue an API key; the secret is returned once",
    request: object({ name: string(), role: { type: "string", enum: ["viewer", "operator", "admin", "owner"] } }, ["name"]),
    response: object({ id: string(), token: string(), prefix: string() }, ["token"]),
    status: 201,
  },
  { method: "delete", path: "/v1/keys/{id}", tag: "keys", id: "revokeKey", summary: "Revoke an API key", status: 204 },

  { method: "get", path: "/v1/agents", tag: "agents", id: "listAgents", summary: "List agents", response: list("Agent") },
  {
    method: "post",
    path: "/v1/agents",
    tag: "agents",
    id: "createAgent",
    summary: "Create a draft agent; nested tools are persisted with it",
    request: object({ name: string(), description: string(), config: object() }, ["name"]),
    response: ref("Agent"),
    status: 201,
  },
  { method: "get", path: "/v1/agents/{id}", tag: "agents", id: "getAgent", summary: "Get one agent", response: ref("Agent") },
  {
    method: "patch",
    path: "/v1/agents/{id}",
    tag: "agents",
    id: "updateAgent",
    summary: "Update name, description, status or config",
    request: object({
      name: string(),
      description: string(),
      config: object(),
      status: { type: "string", enum: ["draft", "published", "archived"] },
    }),
    response: ref("Agent"),
  },
  { method: "post", path: "/v1/agents/{id}/publish", tag: "agents", id: "publishAgent", summary: "Publish a new immutable agent version", response: ref("Agent") },
  { method: "get", path: "/v1/agents/{id}/versions", tag: "agents", id: "listAgentVersions", summary: "List immutable agent version snapshots", response: arrayOf(object()) },
  {
    method: "post",
    path: "/v1/agents/{id}/test",
    tag: "agents",
    id: "testAgent",
    summary: "Run deterministic dry-run conversation evaluation and optional version diff",
    request: object({ callerTurns: arrayOf(string()), variables: object(), version: integer(1), compareVersion: integer(1), expectations: object() }),
    response: GENERIC,
  },
  {
    method: "post",
    path: "/v1/agents/{id}/rollback",
    tag: "agents",
    id: "rollbackAgent",
    summary: "Roll back an agent to a previous immutable version snapshot",
    request: object({ version: integer(1), note: string() }, ["version"]),
    response: ref("Agent"),
  },
  { method: "delete", path: "/v1/agents/{id}", tag: "agents", id: "deleteAgent", summary: "Delete an agent", status: 204 },

  { method: "get", path: "/v1/tools", tag: "tools", id: "listTools", summary: "List tools", response: list("Tool") },
  { method: "post", path: "/v1/tools", tag: "tools", id: "createTool", summary: "Create a tool definition", request: ref("ToolInput"), response: ref("Tool"), status: 201 },
  { method: "patch", path: "/v1/tools/{id}", tag: "tools", id: "updateTool", summary: "Update a tool definition", request: ref("ToolInput"), response: ref("Tool") },
  { method: "delete", path: "/v1/tools/{id}", tag: "tools", id: "deleteTool", summary: "Delete a tool", status: 204 },
  {
    method: "post",
    path: "/v1/tools/{id}/test",
    tag: "tools",
    id: "testTool",
    summary: "Execute a tool once with a synthetic call context",
    request: object({ args: object(), dryRun: boolean() }),
    response: GENERIC,
  },

  {
    method: "get",
    path: "/v1/calls",
    tag: "calls",
    id: "listCalls",
    summary: "List calls, newest first",
    response: list("Call"),
  },
  {
    method: "post",
    path: "/v1/calls",
    tag: "calls",
    id: "simulateCall",
    summary: "Start a free simulated inbound call; audio never leaves the process",
    request: object({ to: string(), from: string(), variables: object(), say: arrayOf(string()), press: arrayOf(string()) }),
    response: ref("Call"),
    status: 201,
  },
  {
    method: "post",
    path: "/v1/calls/outbound",
    tag: "calls",
    id: "startOutboundCall",
    summary: "Start an outbound call; carrier mode costs money and requires consent",
    request: object(
      {
        to: string(),
        agentId: string(),
        consent: boolean(),
        variables: object(),
        mode: { type: "string", enum: ["simulated", "carrier"] },
        provider: { type: "string", enum: ["simulated", "twilio", "signalwire"] },
        from: string(),
      },
      ["to", "agentId", "consent"],
    ),
    response: ref("Call"),
    status: 201,
  },
  { method: "get", path: "/v1/calls/{id}", tag: "calls", id: "getCall", summary: "Get a call with transcript and metrics", response: ref("Call") },
  { method: "post", path: "/v1/calls/{id}/say", tag: "calls", id: "sayToCall", summary: "Make the agent speak into a live call", request: object({ text: string() }, ["text"]), response: ref("Call") },
  {
    method: "post",
    path: "/v1/calls/{id}/dtmf",
    tag: "calls",
    id: "sendDtmf",
    summary: "Send DTMF digits to a live call",
    request: object({ digits: { type: "string", pattern: "^[0-9*#]{1,32}$" } }, ["digits"]),
    response: ref("Call"),
  },
  { method: "post", path: "/v1/calls/{id}/hangup", tag: "calls", id: "hangupCall", summary: "End a live call", response: ref("Call") },

  { method: "get", path: "/v1/workflows", tag: "workflows", id: "listWorkflows", summary: "List workflows", response: list("Workflow") },
  { method: "post", path: "/v1/workflows", tag: "workflows", id: "createWorkflow", summary: "Create a workflow graph", request: ref("WorkflowInput"), response: ref("Workflow"), status: 201 },
  { method: "get", path: "/v1/workflows/{id}", tag: "workflows", id: "getWorkflow", summary: "Get a workflow", response: ref("Workflow") },
  { method: "patch", path: "/v1/workflows/{id}", tag: "workflows", id: "updateWorkflow", summary: "Update a workflow graph or status", request: ref("WorkflowInput"), response: ref("Workflow") },
  { method: "get", path: "/v1/workflows/{id}/versions", tag: "workflows", id: "listWorkflowVersions", summary: "List immutable workflow version snapshots", response: arrayOf(object()) },
  {
    method: "post",
    path: "/v1/workflows/{id}/test",
    tag: "workflows",
    id: "testWorkflow",
    summary: "Dry-run a workflow graph with optional structural version diff",
    request: object({ payload: {}, version: integer(1), compareVersion: integer(1) }),
    response: GENERIC,
  },
  {
    method: "post",
    path: "/v1/workflows/{id}/rollback",
    tag: "workflows",
    id: "rollbackWorkflow",
    summary: "Roll back a workflow to a previous immutable version snapshot",
    request: object({ version: integer(1), note: string() }, ["version"]),
    response: ref("Workflow"),
  },
  { method: "delete", path: "/v1/workflows/{id}", tag: "workflows", id: "deleteWorkflow", summary: "Delete a workflow", status: 204 },
  {
    method: "post",
    path: "/v1/workflows/{id}/run",
    tag: "workflows",
    id: "runWorkflow",
    summary: "Run a workflow now; duplicate idempotency keys return a skipped run",
    request: object({ payload: {}, dryRun: boolean(), idempotencyKey: string() }),
    response: ref("WorkflowRun"),
  },
  { method: "get", path: "/v1/workflows/{id}/runs", tag: "workflows", id: "listWorkflowRuns", summary: "Runs for one workflow", response: list("WorkflowRun") },
  { method: "get", path: "/v1/runs", tag: "workflows", id: "listRuns", summary: "All runs for the tenant", response: list("WorkflowRun") },
  { method: "post", path: "/v1/workflows/import/n8n", tag: "workflows", id: "importN8n", summary: "Import an n8n workflow; Code nodes are rejected", request: object({ workflow: object() }), response: ref("Workflow"), status: 201 },
  { method: "get", path: "/v1/workflows/{id}/export/n8n", tag: "workflows", id: "exportN8n", summary: "Render a workflow as an n8n-compatible skeleton", response: GENERIC },

  { method: "get", path: "/v1/templates", tag: "templates", id: "listTemplates", summary: "List bundled templates", response: list("Template") },
  {
    method: "post",
    path: "/v1/templates/{id}/install",
    tag: "templates",
    id: "installTemplate",
    summary: "Install a template as a draft, or activate it immediately",
    request: object({ activate: boolean() }),
    response: ref("Workflow"),
    status: 201,
  },

  { method: "get", path: "/v1/tasks", tag: "records", id: "listTasks", summary: "List tasks", response: list("Task") },
  {
    method: "post",
    path: "/v1/tasks",
    tag: "records",
    id: "createTask",
    summary: "Create a task",
    request: object(
      {
        title: string(),
        description: string(),
        priority: { type: "string", enum: ["low", "normal", "high", "urgent"] },
        labels: arrayOf(string()),
        dueAt: { type: "string", format: "date-time" },
        assignee: string(),
      },
      ["title"],
    ),
    response: ref("Task"),
    status: 201,
  },
  { method: "patch", path: "/v1/tasks/{id}", tag: "records", id: "updateTask", summary: "Update a task", request: GENERIC, response: ref("Task") },
  { method: "get", path: "/v1/bookings", tag: "records", id: "listBookings", summary: "List bookings", response: list("Booking") },
  {
    method: "post",
    path: "/v1/bookings",
    tag: "records",
    id: "createBooking",
    summary: "Create a booking from a spoken or ISO time",
    request: object({ name: string(), when: string(), title: string(), durationMin: integer(5, 600), phone: string(), email: string(), notes: string() }, ["name", "when"]),
    response: ref("Booking"),
    status: 201,
  },
  { method: "patch", path: "/v1/bookings/{id}", tag: "records", id: "updateBooking", summary: "Update a booking", request: GENERIC, response: ref("Booking") },
  { method: "get", path: "/v1/contacts", tag: "records", id: "listContacts", summary: "List contacts", response: list("Contact") },
  { method: "get", path: "/v1/escalations", tag: "records", id: "listEscalations", summary: "List escalations", response: list("Escalation") },
  { method: "patch", path: "/v1/escalations/{id}", tag: "records", id: "updateEscalation", summary: "Acknowledge or close an escalation", request: GENERIC, response: ref("Escalation") },

  { method: "get", path: "/v1/knowledge-bases", tag: "knowledge", id: "listKnowledgeBases", summary: "List knowledge bases", response: list("KnowledgeBase") },
  { method: "post", path: "/v1/knowledge-bases", tag: "knowledge", id: "createKnowledgeBase", summary: "Create a knowledge base", request: object({ name: string() }, ["name"]), response: ref("KnowledgeBase"), status: 201 },
  {
    method: "post",
    path: "/v1/knowledge-bases/{id}/documents",
    tag: "knowledge",
    id: "addKnowledgeDocument",
    summary: "Add a document (no embedding leaves the machine)",
    request: object({ title: string(), text: string() }, ["title", "text"]),
    response: ref("KnowledgeBase"),
    status: 201,
  },
  {
    method: "post",
    path: "/v1/knowledge-bases/{id}/search",
    tag: "knowledge",
    id: "searchKnowledge",
    summary: "Search a knowledge base with the local lexical retriever",
    request: object({ query: string(), limit: integer(1, 20) }, ["query"]),
    response: object({ hits: arrayOf(ref("KnowledgeHit")) }, ["hits"]),
  },

  { method: "get", path: "/v1/credentials", tag: "credentials", id: "listCredentials", summary: "List credential names (never values)", response: list("CredentialSummary") },
  {
    method: "put",
    path: "/v1/credentials/{name}",
    tag: "credentials",
    id: "setCredential",
    summary: "Encrypt and store a credential; the value is write-only",
    request: object({ value: string(), provider: string() }, ["value"]),
    response: object({ ok: boolean(), name: string() }),
  },
  { method: "delete", path: "/v1/credentials/{name}", tag: "credentials", id: "deleteCredential", summary: "Delete a credential", status: 204 },

  { method: "get", path: "/v1/telephony/providers", tag: "telephony", id: "listTelephonyProviders", summary: "Carrier availability and the honest reason when unavailable", response: list("ProviderAvailability") },
  { method: "get", path: "/v1/numbers", tag: "telephony", id: "listNumbers", summary: "List configured phone numbers", response: list("PhoneNumber") },
  {
    method: "post",
    path: "/v1/numbers/search",
    tag: "telephony",
    id: "searchNumbers",
    summary: "Search numbers; free on the simulator, carrier searches follow carrier pricing",
    request: object({ provider: string(), countryCode: string(), areaCode: string(), contains: string(), limit: integer(1, 30) }),
    response: object({ provider: string(), carrierCharges: boolean(), offers: arrayOf(ref("NumberOffer")) }),
  },
  {
    method: "post",
    path: "/v1/numbers/provision",
    tag: "telephony",
    id: "provisionNumber",
    summary: "Provision a number; carrier purchases need owner role, config and confirm:true",
    request: object({ e164: string(), provider: string(), label: string(), agentId: string(), ivrMenuId: string(), confirm: { const: true } }, ["e164", "confirm"]),
    response: object({ number: ref("PhoneNumber"), carrierCharges: boolean(), costNote: string() }, ["number"]),
    status: 201,
  },
  { method: "delete", path: "/v1/numbers/{id}", tag: "telephony", id: "releaseNumber", summary: "Release a number; requires ?confirm=true", status: 200, response: object({ released: boolean(), id: string(), e164: string() }) },
  { method: "get", path: "/v1/sms", tag: "telephony", id: "listSms", summary: "List inbound and outbound SMS", response: list("SmsMessage") },
  {
    method: "post",
    path: "/v1/sms",
    tag: "telephony",
    id: "sendSms",
    summary: "Send SMS; consent is mandatory and simulated messages are labelled",
    request: object({ to: string(), body: string(), consent: boolean(), from: string(), provider: string() }, ["to", "body", "consent"]),
    response: ref("SmsMessage"),
    status: 201,
  },

  {
    method: "post",
    path: "/v1/hooks/{path}",
    tag: "automation",
    id: "fireWebhook",
    summary: "Start a workflow from an inbound webhook (tenant API key required)",
    request: GENERIC,
    response: ref("WorkflowRun"),
    status: 202,
  },
];

/** Routes that are not part of the JSON client API. */
export const PROVIDER_FACING = [
  "POST /telephony/{provider}/voice",
  "POST /telephony/{provider}/dtmf",
  "POST /telephony/{provider}/status",
  "POST /telephony/{provider}/recording",
  "POST /telephony/{provider}/sms",
] as const;

export const NOT_JSON = ["GET /v1/calls/{id}/stream"] as const;

function components(): Record<string, Schema> {
  return {
    Error: object({ error: object({ code: string(), message: string() }, ["code", "message"]) }, ["error"]),
    Health: object(
      {
        ok: boolean(),
        version: string(),
        simulation: boolean(),
        telephonyDefault: string(),
        telephony: arrayOf(ref("ProviderAvailability")),
      },
      ["ok", "version", "simulation", "telephonyDefault"],
    ),
    ApiKey: object({ id: string(), name: string(), role: string(), prefix: string(), createdAt: string() }, ["id", "name", "role"]),
    Agent: object(
      {
        id: string(),
        tenantId: string(),
        name: string(),
        description: string(),
        status: { type: "string", enum: ["draft", "published", "archived"] },
        version: integer(),
        config: object(),
      },
      ["id", "name", "status"],
    ),
    Tool: object({ id: string(), name: string(), type: string(), description: string(), parameters: object() }, ["id", "name", "type"]),
    ToolInput: object({ name: string(), type: string(), description: string(), parameters: object() }, ["name", "type", "description"]),
    Call: object(
      {
        id: string(),
        direction: { type: "string", enum: ["inbound", "outbound"] },
        status: string(),
        from: string(),
        to: string(),
        startedAt: string(),
        endedAt: string(),
        endedReason: string(),
        transcript: arrayOf(object({ role: string(), text: string(), at: string(), latencyMs: integer() })),
        metrics: object({ turnCount: integer(), toolCalls: integer(), interruptions: integer() }),
        simulation: boolean(),
      },
      ["id", "status", "from", "to", "simulation"],
    ),
    WorkflowInput: object({ name: string(), description: string(), trigger: object(), nodes: arrayOf(object()), edges: arrayOf(object()), status: string() }),
    Workflow: object({ id: string(), name: string(), status: string(), trigger: object(), nodes: arrayOf(object()), edges: arrayOf(object()) }, ["id", "name", "status"]),
    WorkflowRun: object({ id: string(), workflowId: string(), status: string(), startedAt: string(), finishedAt: string(), steps: arrayOf(object()) }, ["id", "workflowId", "status"]),
    Template: object({ id: string(), name: string(), description: string(), category: string() }, ["id", "name"]),
    Task: object({ id: string(), title: string(), status: string(), priority: string(), labels: arrayOf(string()) }, ["id", "title"]),
    Booking: object({ id: string(), name: string(), title: string(), when: string(), durationMin: integer() }, ["id", "when"]),
    Contact: object({ id: string(), name: string(), phone: string(), email: string() }, ["id"]),
    Escalation: object({ id: string(), reason: string(), status: string() }, ["id"]),
    KnowledgeBase: object({ id: string(), name: string(), documents: arrayOf(object()) }, ["id", "name"]),
    KnowledgeHit: object({ documentId: string(), title: string(), score: { type: "number" }, snippet: string() }),
    CredentialSummary: object({ name: string(), provider: string(), updatedAt: string() }, ["name"]),
    ProviderAvailability: object(
      {
        id: string(),
        label: string(),
        available: boolean(),
        detail: string(),
        requiredEnv: arrayOf(string()),
      },
      ["id", "available"],
    ),
    PhoneNumber: object(
      {
        id: string(),
        e164: string(),
        label: string(),
        provider: string(),
        simulated: boolean(),
        inboundAgentId: string(),
        ivrMenuId: string(),
        status: string(),
      },
      ["id", "e164", "provider", "simulated"],
    ),
    NumberOffer: object({ e164: string(), locality: string(), region: string(), carrierCharges: object() }, ["e164"]),
    SmsMessage: object(
      {
        id: string(),
        direction: { type: "string", enum: ["inbound", "outbound"] },
        from: string(),
        to: string(),
        body: string(),
        provider: string(),
        status: string(),
        simulated: boolean(),
      },
      ["id", "direction", "to", "body", "simulated"],
    ),
  };
}

function pathParameters(path: string): Schema[] {
  const parameters: Schema[] = [];
  for (const match of path.matchAll(/\{([^}]+)\}/g)) {
    parameters.push({
      name: match[1],
      in: "path",
      required: true,
      schema: { type: "string" },
    });
  }
  return parameters;
}

export function openApiDocument(): Record<string, unknown> {
  const paths: Record<string, Record<string, unknown>> = {};

  for (const operation of OPERATIONS) {
    const method = operation.method;
    const status = operation.status ?? 200;
    const responseSchema = operation.response ?? GENERIC;
    const body = operation.request
      ? {
          required: true,
          content: json(operation.request),
        }
      : undefined;
    const responses: Record<string, unknown> = {
      [status]: {
        description: status === 204 ? "No content" : "Success",
        ...(status === 204 ? {} : { content: json(responseSchema) }),
      },
    };
    if (!operation.public) {
      responses["400"] = { description: "Validation error", content: json(ref("Error")) };
      responses["401"] = { description: "Missing or invalid API key", content: json(ref("Error")) };
      responses["403"] = { description: "Role or policy refused the action", content: json(ref("Error")) };
      responses["404"] = { description: "Not found in this tenant", content: json(ref("Error")) };
    }

    const parameters = pathParameters(operation.path);
    paths[operation.path] = {
      ...(paths[operation.path] ?? {}),
      [method]: {
        tags: [operation.tag],
        operationId: operation.id,
        summary: operation.summary,
        ...(operation.public ? { security: [] } : {}),
        ...(parameters.length > 0 ? { parameters } : {}),
        ...(body ? { requestBody: body } : {}),
        responses,
      },
    };
  }

  return {
    openapi: "3.1.0",
    info: {
      title: "Omalla API",
      version: "0.1.0",
      summary: "Local-first voice AI and business automation",
      description:
        "The JSON API behind the dashboard, the TypeScript and Python SDKs, the CLI and the MCP server. " +
        "Simulated telephony is the default; carrier endpoints cost money and are gated by role, config and explicit confirmation. " +
        "Carrier webhooks under /telephony/{provider} are provider-facing and are not part of this document. " +
        "Live call events use a WebSocket at /v1/calls/{id}/stream and are documented in ARCHITECTURE.md.",
      license: { name: "Apache-2.0", identifier: "Apache-2.0" },
    },
    servers: [{ url: "http://127.0.0.1:8787", description: "Local default" }],
    security: [{ bearerAuth: [] }],
    tags: [
      { name: "system" },
      { name: "agents" },
      { name: "tools" },
      { name: "calls" },
      { name: "workflows" },
      { name: "templates" },
      { name: "records" },
      { name: "knowledge" },
      { name: "credentials" },
      { name: "telephony" },
      { name: "automation" },
      { name: "keys" },
    ],
    paths,
    components: {
      securitySchemes: {
        bearerAuth: { type: "http", scheme: "bearer", bearerFormat: "omk_*" },
      },
      schemas: components(),
    },
  };
}

export const OPENAPI_OPERATIONS = OPERATIONS.map((operation) => ({
  method: operation.method,
  path: operation.path,
}));
