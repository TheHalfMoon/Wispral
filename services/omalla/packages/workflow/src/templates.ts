import { newId, nowIso } from "@omalla/core";
import type { JsonValue, Workflow, WorkflowEdge, WorkflowNode, WorkflowTrigger } from "@omalla/core";

export type TemplateId =
  | "ai_receptionist"
  | "appointment_scheduling"
  | "restaurant_reservation"
  | "customer_support"
  | "lead_qualification"
  | "crm_management"
  | "order_tracking"
  | "consent_followup"
  | "task_ticket"
  | "voicemail_triage"
  | "n8n_bridge";

export interface TemplateDefinition {
  id: TemplateId;
  name: string;
  description: string;
  category: "voice" | "sales" | "support" | "operations";
  build: (tenantId: string) => Workflow;
}

function n(
  id: string,
  type: WorkflowNode["type"],
  name: string,
  config: Record<string, JsonValue>,
  retry?: { attempts: number; backoffMs: number },
): WorkflowNode {
  return { id, type, name, config, ...(retry ? { retry } : {}) };
}

function e(from: string, to: string, when?: string): WorkflowEdge {
  return { from, to, ...(when ? { when } : {}) };
}

function wf(
  tenantId: string,
  name: string,
  description: string,
  triggerType: WorkflowTrigger["type"],
  nodes: WorkflowNode[],
  edges: WorkflowEdge[],
): Workflow {
  return {
    id: newId("wf"),
    tenantId,
    name,
    description,
    status: "draft",
    version: 1,
    trigger: { type: triggerType, config: {} },
    nodes,
    edges,
    idempotencyWindowSec: 600,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  };
}

const SIDE_EFFECT_RETRY = { attempts: 3, backoffMs: 750 };

export const TEMPLATES: Record<TemplateId, TemplateDefinition> = {
  ai_receptionist: {
    id: "ai_receptionist",
    name: "AI receptionist",
    description:
      "After every call: book the appointment locally, save the caller, send a confirmation, and escalate anything that needs a human. Add a Trello mirror only if your team uses boards.",
    category: "voice",
    build: (tenantId) =>
      wf(
        tenantId,
        "AI receptionist",
        "Post-call receptionist workflow with local booking, local contact, SMS confirmation and escalation.",
        "call_ended",
        [
          n("t", "trigger", "Call ended", { source: "call.ended" }),
          n("has_booking", "branch", "Was an appointment booked?", {
            condition: "exists(trigger.appointment)",
          }),
          n("book", "local.create_booking", "Create local booking", {
            title: "Appointment booked by phone",
            name: "{{trigger.appointment.name}}",
            phone: "{{trigger.callerNumber}}",
            startAt: "{{trigger.appointment.startAt}}",
            durationMin: 30,
            notes: "Booked by the voice agent.",
          }, SIDE_EFFECT_RETRY),
          n("contact", "local.upsert_contact", "Save caller", {
            name: "{{trigger.appointment.name}}",
            phone: "{{trigger.callerNumber}}",
            tags: "reception,booked",
          }),
          n("sms", "sms.send", "Send confirmation SMS", {
            provider: "mock",
            consent: true,
            to: "{{trigger.callerNumber}}",
            body: "You're booked for {{trigger.appointment.startAt}}. Reply STOP to opt out.",
          }, SIDE_EFFECT_RETRY),
          n("task", "local.create_task", "Create follow-up task", {
            title: "Call back {{trigger.callerNumber}}",
            description: "No booking was captured. Review the transcript and follow up.",
            priority: "normal",
            labels: "reception,follow-up",
          }),
          n("escalate", "human.escalate", "Escalate to a human", {
            reason: "Caller did not book and may need assistance",
          }),
          n("done_booking", "end", "Done", {}),
          n("done_task", "end", "Done", {}),
        ],
        [
          e("t", "has_booking"),
          e("has_booking", "book", "true"),
          e("book", "contact"),
          e("contact", "sms"),
          e("sms", "done_booking"),
          e("has_booking", "task", "false"),
          e("task", "escalate"),
          e("escalate", "done_task"),
        ],
      ),
  },

  appointment_scheduling: {
    id: "appointment_scheduling",
    name: "Appointment scheduling",
    description:
      "Create a booking, store the guest as a contact, email the guest, and keep an execution record - all locally by default.",
    category: "operations",
    build: (tenantId) =>
      wf(
        tenantId,
        "Appointment scheduling",
        "Booking with local calendar, local contact and email confirmation.",
        "webhook",
        [
          n("t", "trigger", "Booking request", { path: "appointment", method: "POST" }),
          n("book", "local.create_booking", "Create booking", {
            title: "{{trigger.title}}",
            name: "{{trigger.name}}",
            email: "{{trigger.email}}",
            phone: "{{trigger.phone}}",
            startAt: "{{trigger.startAt}}",
            durationMin: "{{trigger.durationMin}}",
            notes: "{{trigger.notes}}",
          }, SIDE_EFFECT_RETRY),
          n("contact", "local.upsert_contact", "Save guest", {
            name: "{{trigger.name}}",
            email: "{{trigger.email}}",
            phone: "{{trigger.phone}}",
            tags: "appointment",
          }),
          n("email", "email.send", "Email confirmation", {
            to: "{{trigger.email}}",
            subject: "Your appointment is confirmed",
            text: "Hi {{trigger.name}}, your appointment is confirmed for {{trigger.startAt}}.",
          }),
          n("end", "end", "Done", {}),
        ],
        [e("t", "book"), e("book", "contact"), e("contact", "email"), e("email", "end")],
      ),
  },

  restaurant_reservation: {
    id: "restaurant_reservation",
    name: "Restaurant reservation",
    description:
      "Reservations for small parties are confirmed automatically; large parties go to a human.",
    category: "operations",
    build: (tenantId) =>
      wf(
        tenantId,
        "Restaurant reservation",
        "Party-size routing with local booking and SMS confirmation.",
        "webhook",
        [
          n("t", "trigger", "Reservation request", { path: "reservation", method: "POST" }),
          n("large", "branch", "Large party?", { condition: "{{trigger.partySize}} >= 7" }),
          n("book", "local.create_booking", "Book table", {
            title: "Table for {{trigger.partySize}}",
            name: "{{trigger.name}}",
            phone: "{{trigger.phone}}",
            startAt: "{{trigger.startAt}}",
            durationMin: 90,
            notes: "Party of {{trigger.partySize}}",
          }, SIDE_EFFECT_RETRY),
          n("sms", "sms.send", "Confirm by SMS", {
            provider: "mock",
            consent: true,
            to: "{{trigger.phone}}",
            body: "Table confirmed for {{trigger.partySize}} at {{trigger.startAt}}.",
          }),
          n("escalate", "human.escalate", "Route to host", {
            reason: "Party of {{trigger.partySize}} needs host approval",
          }),
          n("end", "end", "Done", {}),
        ],
        [
          e("t", "large"),
          e("large", "book", "false"),
          e("book", "sms"),
          e("sms", "end"),
          e("large", "escalate", "true"),
          e("escalate", "end"),
        ],
      ),
  },

  customer_support: {
    id: "customer_support",
    name: "Customer support",
    description:
      "Turn every support call into a tracked task, escalate urgent issues, and send a written follow-up.",
    category: "support",
    build: (tenantId) =>
      wf(
        tenantId,
        "Customer support",
        "Task creation, urgency routing and follow-up email.",
        "call_ended",
        [
          n("t", "trigger", "Call ended", { source: "call.ended" }),
          n("task", "local.create_task", "Create support task", {
            title: "Support: {{trigger.summary}}",
            description: "{{trigger.transcript}}",
            priority: "{{trigger.priority}}",
            labels: "support,voice",
          }),
          n("urgent", "branch", "Urgent?", { condition: "{{trigger.priority}} == urgent" }),
          n("escalate", "human.escalate", "Page on-call", { reason: "{{trigger.summary}}" }),
          n("email", "email.send", "Send follow-up", {
            to: "{{trigger.email}}",
            subject: "We have your request",
            text: "Thanks for calling. Your reference is {{trigger.callId}}.",
          }),
          n("end", "end", "Done", {}),
        ],
        [
          e("t", "task"),
          e("task", "urgent"),
          e("urgent", "escalate", "true"),
          e("escalate", "end"),
          e("urgent", "email", "false"),
          e("email", "end"),
        ],
      ),
  },

  lead_qualification: {
    id: "lead_qualification",
    name: "Lead qualification",
    description:
      "Score the lead, store the contact, open a follow-up task, and notify sales only when the score qualifies.",
    category: "sales",
    build: (tenantId) =>
      wf(
        tenantId,
        "Lead qualification",
        "Contact upsert, local follow-up task, and score-based routing.",
        "call_ended",
        [
          n("t", "trigger", "Call ended", { source: "call.ended" }),
          n("contact", "local.upsert_contact", "Upsert contact", {
            name: "{{trigger.name}}",
            email: "{{trigger.email}}",
            phone: "{{trigger.callerNumber}}",
            tags: "lead,voice",
          }),
          n("card", "local.create_task", "Create lead follow-up", {
            title: "Lead: {{trigger.name}} ({{trigger.score}})",
            description: "{{trigger.summary}}",
            priority: "normal",
            labels: "lead,voice",
          }, SIDE_EFFECT_RETRY),
          n("qualified", "branch", "Qualified?", { condition: "{{trigger.score}} >= 70" }),
          n("slack", "slack.post_message", "Notify sales", {
            channel: "{{env.SLACK_CHANNEL}}",
            text: "Qualified lead: {{trigger.name}} - score {{trigger.score}}",
          }),
          n("email", "email.send", "Nurture email", {
            to: "{{trigger.email}}",
            subject: "Thanks for your interest",
            text: "We'll be in touch shortly.",
          }),
          n("end", "end", "Done", {}),
        ],
        [
          e("t", "contact"),
          e("contact", "card"),
          e("card", "qualified"),
          e("qualified", "slack", "true"),
          e("slack", "end"),
          e("qualified", "email", "false"),
          e("email", "end"),
        ],
      ),
  },

  crm_management: {
    id: "crm_management",
    name: "CRM management",
    description: "Keep contacts and a spreadsheet in sync after every conversation.",
    category: "operations",
    build: (tenantId) =>
      wf(
        tenantId,
        "CRM management",
        "Local contact store plus optional Google Sheets mirror.",
        "call_ended",
        [
          n("t", "trigger", "Call ended", { source: "call.ended" }),
          n("contact", "local.upsert_contact", "Upsert contact", {
            name: "{{trigger.name}}",
            email: "{{trigger.email}}",
            phone: "{{trigger.callerNumber}}",
            tags: "voice,crm",
          }),
          n("sheet", "google.sheets_append", "Append to sheet", {
            spreadsheetId: "{{env.SHEET_ID}}",
            range: "Calls!A:D",
            values: ["{{trigger.callerNumber}}", "{{trigger.name}}", "{{trigger.summary}}", "{{trigger.callId}}"],
          }),
          n("end", "end", "Done", {}),
        ],
        [e("t", "contact"), e("contact", "sheet"), e("sheet", "end")],
      ),
  },

  order_tracking: {
    id: "order_tracking",
    name: "Order tracking",
    description: "Look up an order over HTTP and text the caller only when the carrier reports movement.",
    category: "support",
    build: (tenantId) =>
      wf(
        tenantId,
        "Order tracking",
        "HTTP lookup with a shipped branch and SMS notification.",
        "webhook",
        [
          n("t", "trigger", "Tracking request", { path: "order", method: "POST" }),
          n("lookup", "http", "Look up order", {
            url: "{{env.ORDER_LOOKUP_URL}}/{{trigger.orderId}}",
            method: "GET",
          }, { attempts: 3, backoffMs: 400 }),
          n("shipped", "branch", "Shipped?", {
            condition: "{{nodes.lookup.output.body.status}} == shipped",
          }),
          n("sms", "sms.send", "Notify caller", {
            provider: "mock",
            consent: true,
            to: "{{trigger.phone}}",
            body: "Order {{trigger.orderId}} has shipped: {{nodes.lookup.output.body.trackingUrl}}",
          }),
          n("end", "end", "Done", {}),
        ],
        [
          e("t", "lookup"),
          e("lookup", "shipped"),
          e("shipped", "sms", "true"),
          e("sms", "end"),
          e("shipped", "end", "false"),
        ],
      ),
  },

  consent_followup: {
    id: "consent_followup",
    name: "Consent-based follow-up calls",
    description:
      "Only call when consent was explicitly recorded. Outbound policy still applies at the telephony layer.",
    category: "sales",
    build: (tenantId) =>
      wf(
        tenantId,
        "Consent-based follow-up",
        "Consent gate before any outbound call.",
        "webhook",
        [
          n("t", "trigger", "Follow-up request", { path: "follow-up", method: "POST" }),
          n("consent", "branch", "Consent recorded?", { condition: "{{trigger.consent}} == true" }),
          n("call", "call.start", "Start follow-up call", {
            agentId: "{{trigger.agentId}}",
            to: "{{trigger.phone}}",
            variables: { name: "{{trigger.name}}", reason: "{{trigger.reason}}" },
          }),
          n("denied", "end", "No consent — stop", {}),
          n("end", "end", "Done", {}),
        ],
        [
          e("t", "consent"),
          e("consent", "call", "true"),
          e("call", "end"),
          e("consent", "denied", "false"),
        ],
      ),
  },

  task_ticket: {
    id: "task_ticket",
    name: "Task and ticket management",
    description: "Create a local task with priority and labels; add a Trello mirror only if your team already uses boards.",
    category: "operations",
    build: (tenantId) =>
      wf(
        tenantId,
        "Task and ticket management",
        "Local task by default; Trello remains an optional node on the palette.",
        "webhook",
        [
          n("t", "trigger", "New ticket", { path: "ticket", method: "POST" }),
          n("task", "local.create_task", "Create local task", {
            title: "{{trigger.title}}",
            description: "{{trigger.description}}",
            priority: "{{trigger.priority}}",
            labels: "ticket",
          }),
          n("end", "end", "Done", {}),
        ],
        [e("t", "task"), e("task", "end")],
      ),
  },

  voicemail_triage: {    id: "voicemail_triage",
    name: "Voicemail triage",
    description: "Convert a voicemail into a task with a transcript and route urgent messages to a human.",
    category: "support",
    build: (tenantId) =>
      wf(
        tenantId,
        "Voicemail triage",
        "Transcript to task, urgency routing.",
        "call_ended",
        [
          n("t", "trigger", "Call ended", { source: "call.ended" }),
          n("voicemail", "branch", "Voicemail?", { condition: "{{trigger.endedReason}} == voicemail" }),
          n("task", "local.create_task", "Create voicemail task", {
            title: "Voicemail from {{trigger.callerNumber}}",
            description: "{{trigger.transcript}}",
            priority: "normal",
            labels: "voicemail",
          }),
          n("urgent", "branch", "Urgent?", { condition: "{{trigger.priority}} == urgent" }),
          n("escalate", "human.escalate", "Escalate", { reason: "Urgent voicemail" }),
          n("end", "end", "Done", {}),
        ],
        [
          e("t", "voicemail"),
          e("voicemail", "task", "true"),
          e("task", "urgent"),
          e("urgent", "escalate", "true"),
          e("escalate", "end"),
          e("urgent", "end", "false"),
          e("voicemail", "end", "false"),
        ],
      ),
  },

  n8n_bridge: {
    id: "n8n_bridge",
    name: "n8n post-call handoff",
    description:
      "Send the finished call to a published n8n production webhook. Optional: native Omalla workflows do the same work with no n8n install.",
    category: "operations",
    build: (tenantId) =>
      wf(
        tenantId,
        "n8n post-call handoff",
        "Replace the placeholder URL with your n8n production webhook, then activate.",
        "call_ended",
        [
          n("t", "trigger", "Call ended", { source: "call.ended" }),
          n("n8n", "n8n.webhook", "POST to n8n", {
            url: "https://your-n8n.example.com/webhook/omalla-call-ended",
            secretName: "N8N_WEBHOOK_SECRET",
            payload: {
              event: "call.ended",
              callId: "{{trigger.callId}}",
              callerNumber: "{{trigger.callerNumber}}",
              summary: "{{trigger.summary}}",
              transcript: "{{trigger.transcript}}",
              endedReason: "{{trigger.endedReason}}",
            },
          }, SIDE_EFFECT_RETRY),
          n("end", "end", "Done", {}),
        ],
        [e("t", "n8n"), e("n8n", "end")],
      ),
  },
};

export function buildTemplate(id: TemplateId, tenantId: string): Workflow {
  const definition = TEMPLATES[id];
  if (!definition) throw new Error(`unknown template: ${id}`);
  return definition.build(tenantId);
}

export function listTemplates(): Array<Omit<TemplateDefinition, "build">> {
  return Object.values(TEMPLATES).map(({ build: _build, ...rest }) => rest);
}
