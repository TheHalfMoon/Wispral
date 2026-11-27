import { createHmac } from "node:crypto";
import { OmallaError, evaluateUrl, sanitizeUntrustedCallVariables } from "@omalla/core";
import type { JsonValue, Logger, UrlPolicyOptions, WorkflowNode, WorkflowRun } from "@omalla/core";
import { evaluateCondition, render, renderDeep, type Scope } from "./expressions.js";

export interface AutomationStore {
  createTask(input: {
    tenantId: string;
    title: string;
    description: string;
    priority: "low" | "normal" | "high" | "urgent";
    labels: string[];
    dueAt?: string;
    callId?: string;
  }): Promise<JsonValue>;
  updateTask(id: string, patch: Record<string, JsonValue>, tenantId: string): Promise<JsonValue>;
  createBooking(input: {
    tenantId: string;
    title: string;
    name: string;
    phone?: string;
    email?: string;
    startAt: string;
    durationMin: number;
    notes?: string;
    callId?: string;
  }): Promise<JsonValue>;
  upsertContact(input: {
    tenantId: string;
    name: string;
    email?: string;
    phone?: string;
    tags: string[];
    attributes: Record<string, JsonValue>;
  }): Promise<JsonValue>;
}

export interface WorkflowServices {
  logger: Logger;
  fetch: typeof fetch;
  urlPolicy: UrlPolicyOptions;
  now: () => Date;
  sleep: (ms: number) => Promise<void>;
  secrets: { get(name: string): Promise<string | undefined> };
  store?: AutomationStore;
  escalate?: (input: {
    runId: string;
    tenantId: string;
    reason: string;
    context: Record<string, JsonValue>;
  }) => Promise<void>;
  startCall?: (input: {
    tenantId: string;
    to: string;
    agentId: string;
    variables: Record<string, JsonValue>;
  }) => Promise<{ callId: string }>;
  /** Policy-enforcing outbound SMS callback (`OM-T6`). */
  sendSms?: (input: {
    tenantId: string;
    to: string;
    body: string;
    provider?: string;
    consent: boolean;
    from?: string;
  }) => Promise<JsonValue>;
}

export interface NodeContext {
  node: WorkflowNode;
  run: WorkflowRun;
  scope: Scope;
  services: WorkflowServices;
  signal: AbortSignal;
}

export interface NodeOutcome {
  output: JsonValue;
  contextPatch?: Record<string, JsonValue>;
  /** "true" or "false" for branch nodes. */
  branch?: string;
  stop?: boolean;
}

export type NodeHandler = (context: NodeContext) => Promise<NodeOutcome>;

const DEFAULT_TIMEOUT_MS = 15_000;

export const defaultHandlers: Record<string, NodeHandler> = {
  trigger: async ({ run }) => ({ output: run.trigger.payload }),

  set: async ({ node, scope }) => {
    const values = (node.config.values ?? {}) as JsonValue;
    const patch = renderDeep(values, scope);
    return {
      output: patch,
      contextPatch:
        patch && typeof patch === "object" && !Array.isArray(patch)
          ? (patch as Record<string, JsonValue>)
          : {},
    };
  },

  branch: async ({ node, scope }) => {
    const condition = String(node.config.condition ?? "");
    const result = evaluateCondition(condition, scope);
    return { output: { condition, result }, branch: result ? "true" : "false" };
  },

  delay: async ({ node, scope, services, signal }) => {
    const raw = node.config.ms ?? 0;
    const resolved = Number(render(String(raw), scope));
    const ms = Math.max(0, Math.min(Number.isFinite(resolved) ? resolved : 0, 60_000));
    if (signal.aborted) throw new Error("aborted");
    await services.sleep(ms);
    return { output: { waitedMs: ms } };
  },

  http: async ({ node, scope, services, signal }) => {
    const url = String(render(String(node.config.url ?? ""), scope));
    const policy = evaluateUrl(url, services.urlPolicy);
    if (!policy.allowed) {
      throw new OmallaError("blocked_by_policy", `HTTP node blocked: ${policy.reason}`, 403);
    }
    const method = String(node.config.method ?? "POST").toUpperCase();
    const headers = (renderDeep((node.config.headers ?? {}) as JsonValue, scope) as Record<string, JsonValue>) ?? {};
    const bodyTemplate = node.config.body;
    const timeout = AbortSignal.timeout(Number(node.config.timeoutMs ?? DEFAULT_TIMEOUT_MS));
    const combined = AbortSignal.any([signal, timeout]);

    const response = await services.fetch(url, {
      method,
      headers: Object.fromEntries(Object.entries(headers).map(([k, v]) => [k, String(v)])),
      ...(bodyTemplate !== undefined && method !== "GET"
        ? { body: JSON.stringify(renderDeep(bodyTemplate as JsonValue, scope)) }
        : {}),
      signal: combined,
    });

    const contentType = response.headers.get("content-type") ?? "";
    let body: JsonValue;
    if (contentType.includes("application/json")) {
      body = (await response.json().catch(() => null)) as JsonValue;
    } else {
      const text = await response.text();
      body = text.slice(0, 20_000);
    }
    return { output: { status: response.status, ok: response.ok, body } };
  },

  "calendar.create_event": async ({ node, scope, services, signal }) => {
    const mode = String(node.config.mode ?? "ics");
    const summary = String(render(String(node.config.summary ?? "Appointment"), scope));
    const start = String(render(String(node.config.start ?? ""), scope));
    const durationMin = Number(render(String(node.config.durationMin ?? 30), scope));
    const description = String(render(String(node.config.description ?? ""), scope));

    let output: JsonValue;
    if (mode === "webhook") {
      const url = String(render(String(node.config.webhookUrl ?? ""), scope));
      const policy = evaluateUrl(url, services.urlPolicy);
      if (!policy.allowed) throw new OmallaError("blocked_by_policy", policy.reason ?? "blocked", 403);
      const response = await services.fetch(url, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ summary, start, durationMin, description }),
        signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
      });
      output = { mode, status: response.status, ok: response.ok };
    } else {
      const uid = `${node.id}@omalla.local`;
      const dtStart = toIcsDate(start || new Date().toISOString());
      const dtEnd = toIcsDate(
        new Date(new Date(start || Date.now()).getTime() + Math.max(5, durationMin) * 60_000).toISOString(),
      );
      const ics = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Omalla//Omalla Local//EN",
        "BEGIN:VEVENT",
        `UID:${uid}`,
        `DTSTAMP:${toIcsDate(new Date().toISOString())}`,
        `DTSTART:${dtStart}`,
        `DTEND:${dtEnd}`,
        `SUMMARY:${escapeIcs(summary)}`,
        `DESCRIPTION:${escapeIcs(description)}`,
        "END:VEVENT",
        "END:VCALENDAR",
      ].join("\r\n");
      output = { mode: "ics", uid, summary, start, durationMin, ics };
    }
    return { output };
  },

  "crm.upsert_contact": async ({ node, scope, services, signal }) => {
    const email = String(render(String(node.config.email ?? ""), scope));
    const phone = String(render(String(node.config.phone ?? ""), scope));
    const name = String(render(String(node.config.name ?? ""), scope));
    const webhookUrl = node.config.webhookUrl ? String(render(String(node.config.webhookUrl), scope)) : "";

    let output: JsonValue;
    if (!webhookUrl) {
      output = { stored: "local", email, phone, name, note: "no CRM webhook configured" };
    } else {
      const policy = evaluateUrl(webhookUrl, services.urlPolicy);
      if (!policy.allowed) throw new OmallaError("blocked_by_policy", policy.reason ?? "blocked", 403);
      const response = await services.fetch(webhookUrl, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, phone, name, source: "omalla" }),
        signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
      });
      output = { stored: "webhook", status: response.status, ok: response.ok };
    }
    return { output };
  },

  "sms.send": async ({ node, run, scope, services }) => {
    const to = String(render(String(node.config.to ?? ""), scope));
    const body = String(render(String(node.config.body ?? ""), scope));
    const provider = String(node.config.provider ?? "mock");
    const consentRendered =
      node.config.consent !== undefined ? String(render(String(node.config.consent), scope)).toLowerCase() : undefined;
    const triggerPayload =
      scope.trigger && typeof scope.trigger === "object" && !Array.isArray(scope.trigger)
        ? (scope.trigger as Record<string, unknown>)
        : {};
    const consent =
      node.config.consent === true ||
      consentRendered === "true" ||
      triggerPayload.consent === true ||
      (node.config.consent === undefined && Boolean(triggerPayload.appointment));

    if (services.sendSms) {
      const output = await services.sendSms({
        tenantId: run.tenantId,
        to,
        body,
        provider,
        consent,
      });
      return { output };
    }

    if (!consent) {
      throw new OmallaError("blocked_by_policy", "sending SMS requires recorded consent (OM-T6)", 403);
    }
    if (provider === "mock" || provider === "simulated") {
      return { output: json({ simulated: true, to, body, provider: "mock" }) };
    }
    throw new OmallaError(
      "provider_error",
      "carrier SMS requires WorkflowServices.sendSms policy enforcement",
      500,
    );
  },

  "email.send": async ({ node, scope, services, signal }) => {
    const to = String(render(String(node.config.to ?? ""), scope));
    const subject = String(render(String(node.config.subject ?? ""), scope));
    const text = String(render(String(node.config.text ?? ""), scope));
    const webhookUrl = node.config.webhookUrl ? String(render(String(node.config.webhookUrl), scope)) : "";

    if (!webhookUrl) {
      return { output: json({ simulated: true, to, subject, text }) };
    }
    const policy = evaluateUrl(webhookUrl, services.urlPolicy);
    if (!policy.allowed) throw new OmallaError("blocked_by_policy", policy.reason ?? "blocked", 403);
    const response = await services.fetch(webhookUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ to, subject, text }),
      signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
    });
    return { output: json({ simulated: false, status: response.status, ok: response.ok }) };
  },

  "n8n.webhook": async ({ node, scope, services, signal }) => {
    const url = String(render(String(node.config.url ?? ""), scope));
    const policy = evaluateUrl(url, services.urlPolicy);
    if (!policy.allowed) throw new OmallaError("blocked_by_policy", policy.reason ?? "blocked", 403);

    const payload = JSON.stringify(renderDeep((node.config.payload ?? {}) as JsonValue, scope));
    const secret = await services.secrets.get(String(node.config.secretName ?? "N8N_WEBHOOK_SECRET"));
    const signature = secret ? createHmac("sha256", secret).update(payload).digest("hex") : undefined;

    const response = await services.fetch(url, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(signature ? { "x-omalla-signature": `sha256=${signature}` } : {}),
      },
      body: payload,
      signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
    });
    const text = await response.text();
    return {
      output: { status: response.status, ok: response.ok, body: text.slice(0, 20_000) },
    };
  },

  "human.escalate": async ({ node, run, services, scope }) => {
    const reason = String(render(String(node.config.reason ?? "Caller requested a human"), scope));
    if (services.escalate) {
      await services.escalate({
        runId: run.id,
        tenantId: run.tenantId,
        reason,
        context: run.context,
      });
    }
    return { output: { escalated: true, reason } };
  },

  "call.start": async ({ node, run, services, scope }) => {
    const to = String(render(String(node.config.to ?? ""), scope));
    const agentId = String(render(String(node.config.agentId ?? ""), scope));
    if (!services.startCall) {
      throw new OmallaError("provider_error", "call.start requires a telephony service", 500);
    }
    const rawVariables = renderDeep((node.config.variables ?? {}) as JsonValue, scope);
    const safeVariables =
      rawVariables && typeof rawVariables === "object" && !Array.isArray(rawVariables)
        ? sanitizeUntrustedCallVariables(rawVariables as Record<string, JsonValue>)
        : {};
    const result = await services.startCall({
      tenantId: run.tenantId,
      to,
      agentId,
      variables: safeVariables,
    });
    return { output: result };
  },

  end: async ({ node }) => ({ output: { ended: true }, stop: true, stopReason: node.id } as NodeOutcome),
};

/* ------------------------------------------------------------------ */
/* Trello — full board/list/card operations (BYOK, optional)           */
/* ------------------------------------------------------------------ */

interface TrelloCredentials {
  key: string;
  token: string;
}

async function trelloCredentials(services: WorkflowServices): Promise<TrelloCredentials> {
  const key = await services.secrets.get("TRELLO_KEY");
  const token = await services.secrets.get("TRELLO_TOKEN");
  if (!key || !token) {
    throw new OmallaError(
      "provider_error",
      "Trello is not connected: add TRELLO_KEY and TRELLO_TOKEN in Settings -> Providers",
      400,
    );
  }
  return { key, token };
}

async function trelloCall(
  services: WorkflowServices,
  method: "GET" | "POST" | "PUT" | "DELETE",
  path: string,
  params: Record<string, string | undefined>,
  signal: AbortSignal,
  body?: Record<string, unknown>,
): Promise<JsonValue> {
  const { key, token } = await trelloCredentials(services);
  const url = new URL(`https://api.trello.com/1${path}`);
  url.searchParams.set("key", key);
  url.searchParams.set("token", token);
  for (const [name, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") url.searchParams.set(name, value);
  }
  const response = await services.fetch(url, {
    method,
    ...(body ? { headers: { "content-type": "application/json" }, body: JSON.stringify(body) } : {}),
    signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new OmallaError("provider_error", `Trello returned ${response.status}: ${text.slice(0, 200)}`, 502);
  }
  try {
    return JSON.parse(text) as JsonValue;
  } catch {
    return text.slice(0, 5000);
  }
}

const str = (node: WorkflowNode, key: string, scope: Scope, fallback = ""): string => {
  const raw = node.config[key];
  return raw === undefined ? fallback : String(render(String(raw), scope));
};

const trelloHandlers: Record<string, NodeHandler> = {
  "trello.create_card": async ({ node, scope, services, signal }) => {
    const listId = str(node, "listId", scope);
    if (!listId) throw new OmallaError("validation", "trello.create_card requires listId", 400);
    const card = await trelloCall(
      services,
      "POST",
      "/cards",
      {},
      signal,
      {
        idList: listId,
        name: str(node, "name", scope, "New card").slice(0, 512),
        desc: str(node, "desc", scope).slice(0, 16000),
        ...(node.config.due ? { due: str(node, "due", scope) } : {}),
        ...(node.config.labelIds ? { idLabels: str(node, "labelIds", scope) } : {}),
        ...(node.config.memberIds ? { idMembers: str(node, "memberIds", scope) } : {}),
      },
    );
    const record = (card ?? {}) as Record<string, JsonValue>;
    return { output: { id: record.id ?? null, url: record.shortUrl ?? null, name: record.name ?? null } };
  },

  "trello.update_card": async ({ node, scope, services, signal }) => {
    const cardId = str(node, "cardId", scope);
    if (!cardId) throw new OmallaError("validation", "trello.update_card requires cardId", 400);
    const body: Record<string, unknown> = {};
    for (const field of ["name", "desc", "due", "closed", "pos"]) {
      if (node.config[field] !== undefined) body[field] = str(node, field, scope);
    }
    const card = await trelloCall(services, "PUT", `/cards/${encodeURIComponent(cardId)}`, {}, signal, body);
    return { output: card };
  },

  "trello.move_card": async ({ node, scope, services, signal }) => {
    const cardId = str(node, "cardId", scope);
    const listId = str(node, "listId", scope);
    if (!cardId || !listId) throw new OmallaError("validation", "trello.move_card requires cardId and listId", 400);
    const card = await trelloCall(services, "PUT", `/cards/${encodeURIComponent(cardId)}`, {}, signal, {
      idList: listId,
    });
    return { output: card };
  },

  "trello.add_comment": async ({ node, scope, services, signal }) => {
    const cardId = str(node, "cardId", scope);
    if (!cardId) throw new OmallaError("validation", "trello.add_comment requires cardId", 400);
    const action = await trelloCall(
      services,
      "POST",
      `/cards/${encodeURIComponent(cardId)}/actions/comments`,
      {},
      signal,
      { text: str(node, "text", scope).slice(0, 16000) },
    );
    return { output: action };
  },

  "trello.add_label": async ({ node, scope, services, signal }) => {
    const cardId = str(node, "cardId", scope);
    const labelId = str(node, "labelId", scope);
    if (!cardId || !labelId) throw new OmallaError("validation", "trello.add_label requires cardId and labelId", 400);
    const result = await trelloCall(
      services,
      "POST",
      `/cards/${encodeURIComponent(cardId)}/idLabels`,
      {},
      signal,
      { value: labelId },
    );
    return { output: result };
  },

  "trello.assign_member": async ({ node, scope, services, signal }) => {
    const cardId = str(node, "cardId", scope);
    const memberId = str(node, "memberId", scope);
    if (!cardId || !memberId) {
      throw new OmallaError("validation", "trello.assign_member requires cardId and memberId", 400);
    }
    const result = await trelloCall(
      services,
      "POST",
      `/cards/${encodeURIComponent(cardId)}/idMembers`,
      {},
      signal,
      { value: memberId },
    );
    return { output: result };
  },

  "trello.set_due": async ({ node, scope, services, signal }) => {
    const cardId = str(node, "cardId", scope);
    const due = str(node, "due", scope);
    if (!cardId || !due) throw new OmallaError("validation", "trello.set_due requires cardId and due", 400);
    const card = await trelloCall(services, "PUT", `/cards/${encodeURIComponent(cardId)}`, {}, signal, { due });
    return { output: card };
  },

  "trello.create_list": async ({ node, scope, services, signal }) => {
    const boardId = str(node, "boardId", scope);
    if (!boardId) throw new OmallaError("validation", "trello.create_list requires boardId", 400);
    const list = await trelloCall(services, "POST", "/lists", {}, signal, {
      name: str(node, "name", scope, "New list"),
      idBoard: boardId,
      ...(node.config.pos ? { pos: str(node, "pos", scope) } : {}),
    });
    return { output: list };
  },

  "trello.list_cards": async ({ node, scope, services, signal }) => {
    const listId = str(node, "listId", scope);
    if (!listId) throw new OmallaError("validation", "trello.list_cards requires listId", 400);
    const cards = await trelloCall(services, "GET", `/lists/${encodeURIComponent(listId)}/cards`, {}, signal);
    return { output: cards };
  },
};

/* ------------------------------------------------------------------ */
/* Google / Slack / WhatsApp — BYOK adapters                           */
/* ------------------------------------------------------------------ */

async function bearer(
  services: WorkflowServices,
  secretName: string,
  label: string,
): Promise<string> {
  const token = await services.secrets.get(secretName);
  if (!token) {
    throw new OmallaError("provider_error", `${label} is not connected: add ${secretName}`, 400);
  }
  return token;
}

const workspaceHandlers: Record<string, NodeHandler> = {
  "google.calendar_create_event": async ({ node, scope, services, signal }) => {
    const token = await bearer(services, "GOOGLE_ACCESS_TOKEN", "Google Calendar");
    const calendarId = str(node, "calendarId", scope, "primary");
    const startAt = str(node, "startAt", scope);
    const durationMin = Number(str(node, "durationMin", scope, "30")) || 30;
    if (!startAt) throw new OmallaError("validation", "startAt is required", 400);
    const endAt = new Date(new Date(startAt).getTime() + durationMin * 60_000).toISOString();
    const response = await services.fetch(
      `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events`,
      {
        method: "POST",
        headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
        body: JSON.stringify({
          summary: str(node, "summary", scope, "Appointment"),
          description: str(node, "description", scope),
          start: { dateTime: startAt },
          end: { dateTime: endAt },
        }),
        signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
      },
    );
    if (!response.ok) {
      throw new OmallaError("provider_error", `Google Calendar returned ${response.status}`, 502);
    }
    const event = (await response.json()) as { id?: string; htmlLink?: string };
    return { output: { id: event.id ?? null, url: event.htmlLink ?? null } };
  },

  "google.gmail_send": async ({ node, scope, services, signal }) => {
    const token = await bearer(services, "GOOGLE_ACCESS_TOKEN", "Gmail");
    const to = str(node, "to", scope);
    const subject = str(node, "subject", scope);
    const text = str(node, "text", scope);
    if (!to) throw new OmallaError("validation", "gmail_send requires to", 400);
    const raw = Buffer.from(
      [`To: ${to}`, `Subject: ${subject}`, "Content-Type: text/plain; charset=UTF-8", "", text].join("\r\n"),
    )
      .toString("base64")
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
    const response = await services.fetch("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", {
      method: "POST",
      headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
      body: JSON.stringify({ raw }),
      signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
    });
    if (!response.ok) throw new OmallaError("provider_error", `Gmail returned ${response.status}`, 502);
    const message = (await response.json()) as { id?: string };
    return { output: { id: message.id ?? null } };
  },

  "google.sheets_append": async ({ node, scope, services, signal }) => {
    const token = await bearer(services, "GOOGLE_ACCESS_TOKEN", "Google Sheets");
    const spreadsheetId = str(node, "spreadsheetId", scope);
    const range = str(node, "range", scope, "A1");
    if (!spreadsheetId) throw new OmallaError("validation", "sheets_append requires spreadsheetId", 400);
    const values = node.config.values;
    const rendered = values === undefined ? [] : renderDeep(values, scope);
    const rows = Array.isArray(rendered) ? rendered : [rendered];
    const response = await services.fetch(
      `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(spreadsheetId)}/values/${encodeURIComponent(range)}:append?valueInputOption=RAW`,
      {
        method: "POST",
        headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
        body: JSON.stringify({ values: rows }),
        signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
      },
    );
    if (!response.ok) throw new OmallaError("provider_error", `Sheets returned ${response.status}`, 502);
    return { output: (await response.json()) as JsonValue };
  },

  "slack.post_message": async ({ node, scope, services, signal }) => {
    const token = await bearer(services, "SLACK_BOT_TOKEN", "Slack");
    const channel = str(node, "channel", scope);
    if (!channel) throw new OmallaError("validation", "slack.post_message requires channel", 400);
    const response = await services.fetch("https://slack.com/api/chat.postMessage", {
      method: "POST",
      headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
      body: JSON.stringify({ channel, text: str(node, "text", scope) }),
      signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
    });
    const payload = (await response.json().catch(() => ({}))) as { ok?: boolean; error?: string; ts?: string };
    if (!response.ok || payload.ok === false) {
      throw new OmallaError("provider_error", `Slack error: ${payload.error ?? response.status}`, 502);
    }
    return { output: { ok: true, ts: payload.ts ?? null } };
  },

  "whatsapp.send_message": async ({ node, scope, services, signal }) => {
    const token = await bearer(services, "WHATSAPP_ACCESS_TOKEN", "WhatsApp");
    const phoneNumberId = str(node, "phoneNumberId", scope);
    const to = str(node, "to", scope);
    if (!phoneNumberId || !to) {
      throw new OmallaError("validation", "whatsapp.send_message requires phoneNumberId and to", 400);
    }
    const response = await services.fetch(
      `https://graph.facebook.com/v20.0/${encodeURIComponent(phoneNumberId)}/messages`,
      {
        method: "POST",
        headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
        body: JSON.stringify({
          messaging_product: "whatsapp",
          to,
          type: "text",
          text: { body: str(node, "text", scope) },
        }),
        signal: AbortSignal.any([signal, AbortSignal.timeout(DEFAULT_TIMEOUT_MS)]),
      },
    );
    if (!response.ok) throw new OmallaError("provider_error", `WhatsApp returned ${response.status}`, 502);
    return { output: (await response.json()) as JsonValue };
  },
};

/* ------------------------------------------------------------------ */
/* Local automation records — no external service required             */
/* ------------------------------------------------------------------ */

const localHandlers: Record<string, NodeHandler> = {
  "local.create_task": async ({ node, run, scope, services }) => {
    if (!services.store) throw new OmallaError("provider_error", "local task store is not configured", 500);
    const due = node.config.dueAt ? str(node, "dueAt", scope) : undefined;
    const task = await services.store.createTask({
      tenantId: run.tenantId,
      title: str(node, "title", scope, "Untitled task"),
      description: str(node, "description", scope),
      priority: (str(node, "priority", scope, "normal") as "low" | "normal" | "high" | "urgent") ?? "normal",
      labels: str(node, "labels", scope)
        .split(",")
        .map((label) => label.trim())
        .filter(Boolean),
      ...(due ? { dueAt: due } : {}),
      ...(run.callId ? { callId: run.callId } : {}),
    });
    return { output: task };
  },

  "local.update_task": async ({ node, run, scope, services }) => {
    if (!services.store) throw new OmallaError("provider_error", "local task store is not configured", 500);
    const id = str(node, "taskId", scope);
    if (!id) throw new OmallaError("validation", "local.update_task requires taskId", 400);
    const patch: Record<string, JsonValue> = {};
    for (const field of ["title", "description", "status", "priority", "assignee", "dueAt"]) {
      if (node.config[field] !== undefined) patch[field] = str(node, field, scope);
    }
    return { output: await services.store.updateTask(id, patch, run.tenantId) };
  },

  "local.create_booking": async ({ node, run, scope, services }) => {
    if (!services.store) throw new OmallaError("provider_error", "local booking store is not configured", 500);
    const startAt = str(node, "startAt", scope);
    if (!startAt) throw new OmallaError("validation", "local.create_booking requires startAt", 400);
    const booking = await services.store.createBooking({
      tenantId: run.tenantId,
      title: str(node, "title", scope, "Appointment"),
      name: str(node, "name", scope, "Guest"),
      ...(node.config.phone ? { phone: str(node, "phone", scope) } : {}),
      ...(node.config.email ? { email: str(node, "email", scope) } : {}),
      startAt,
      durationMin: Number(str(node, "durationMin", scope, "30")) || 30,
      ...(node.config.notes ? { notes: str(node, "notes", scope) } : {}),
      ...(run.callId ? { callId: run.callId } : {}),
    });
    return { output: booking };
  },

  "local.upsert_contact": async ({ node, run, scope, services }) => {
    if (!services.store) throw new OmallaError("provider_error", "local contact store is not configured", 500);
    const contact = await services.store.upsertContact({
      tenantId: run.tenantId,
      name: str(node, "name", scope, "Unknown caller"),
      ...(node.config.email ? { email: str(node, "email", scope) } : {}),
      ...(node.config.phone ? { phone: str(node, "phone", scope) } : {}),
      tags: str(node, "tags", scope)
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      attributes: {},
    });
    return { output: contact };
  },
};

/* ------------------------------------------------------------------ */
/* Bounded graph loop                                                  */
/* ------------------------------------------------------------------ */

const loopHandler: NodeHandler = async ({ node, scope }) => {
  const counterKey = `__loop_${node.id}`;
  const limit = Math.max(1, Math.min(Number(render(String(node.config.maxIterations ?? 3), scope)) || 3, 50));
  const current = Number((scope.context as Record<string, unknown>)[counterKey] ?? 0);
  const next = current + 1;
  (scope.context as Record<string, unknown>)[counterKey] = next;
  return {
    output: { iteration: next, maxIterations: limit },
    branch: next < limit ? "again" : "done",
  };
};

Object.assign(defaultHandlers, trelloHandlers, workspaceHandlers, localHandlers, { loop: loopHandler });

/** Narrow a plain object literal to JsonValue without losing the runtime shape. */
function json(value: Record<string, unknown>): JsonValue {
  return value as unknown as JsonValue;
}

function toIcsDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${date.toISOString().replace(/[-:]/g, "").split(".")[0]}Z`;
}

function escapeIcs(value: string): string {
  return value.replace(/([,;\\])/g, "\\$1").replace(/\n/g, "\\n");
}
