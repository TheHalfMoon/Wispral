/**
 * Omalla domain model.
 *
 * The model is deliberately transport- and provider-neutral: a call is a
 * state machine, a turn is data, and every provider sits behind a contract.
 */

export type Id = string;
export type ISODate = string;

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export interface JsonSchema {
  type: "object";
  properties: Record<string, JsonSchemaProperty>;
  required?: string[];
  additionalProperties?: boolean;
}

export interface JsonSchemaProperty {
  type: "string" | "number" | "integer" | "boolean" | "object" | "array";
  description?: string;
  enum?: string[];
  items?: JsonSchemaProperty;
  properties?: Record<string, JsonSchemaProperty>;
  default?: JsonValue;
}

/* ------------------------------------------------------------------ */
/* Tenancy and identity                                                */
/* ------------------------------------------------------------------ */

export type Role = "owner" | "admin" | "operator" | "viewer";

export interface Tenant {
  id: Id;
  name: string;
  createdAt: ISODate;
  /** ISO 3166-1 alpha-2, used for consent and calling-window defaults. */
  region: string;
  settings: TenantSettings;
}

export interface TenantSettings {
  /** Default recording posture. Recording is opt-in per agent. */
  recordingEnabled: boolean;
  /** Outbound calling requires an explicit allow-list unless disabled here. */
  outboundEnabled: boolean;
  outboundAllowlist: string[];
  /** Do-Not-Call E.164 list enforced before any simulated or carrier dial. */
  dncList?: string[];
  /** Hard cap per rolling 24h. Zero means no outbound calls at all. */
  dailyOutboundCap: number;
  /** Optional per-tenant concurrent active call ceiling. */
  maxConcurrentCalls?: number;
  /** Optional per-tenant rolling 24h outbound minute quota. */
  dailyMinuteQuota?: number;
  /** Optional per-tenant rolling 30d outbound minute quota. */
  monthlyMinuteQuota?: number;
  /** Optional default tenant calling window (quiet hours outside it). */
  callingWindow?: { start: string; end: string; days: number[] };
  callingWindowStart?: string;
  callingWindowEnd?: string;
  callingDays?: number[];
  retentionDays: number;
  timezone: string;
}

export interface User {
  id: Id;
  tenantId: Id;
  email: string;
  name: string;
  role: Role;
  passwordHash?: string;
  createdAt: ISODate;
  lastSeenAt?: ISODate;
}

export interface ApiKey {
  id: Id;
  tenantId: Id;
  name: string;
  prefix: string;
  hash: string;
  role: Role;
  createdAt: ISODate;
  lastUsedAt?: ISODate;
  revokedAt?: ISODate;
}

export interface Principal {
  tenantId: Id;
  role: Role;
  kind: "api_key" | "user" | "system";
  apiKeyId?: Id;
  userId?: Id;
}

/* ------------------------------------------------------------------ */
/* Providers                                                           */
/* ------------------------------------------------------------------ */

export interface ModelRef {
  provider:
    | "mock"
    | "loopback"
    | "wispral-core"
    | "ollama"
    | "openai"
    | "openai-compatible"
    | "anthropic"
    | "local";
  model: string;
  temperature?: number;
  baseUrl?: string;
  /** Name of a stored credential. Never an inline key. */
  credentialRef?: string;
  maxTokens?: number;
  /** Ordered, only used before the first token reaches the caller. */
  fallbacks?: ModelRef[];
}

export interface VoiceRef {
  provider:
    | "mock"
    | "loopback"
    | "synth"
    | "wispral-core"
    | "sapi"
    | "piper"
    | "kokoro"
    | "elevenlabs"
    | "openai"
    | "custom";
  voiceId: string;
  speed?: number;
  baseUrl?: string;
  credentialRef?: string;
  fallbacks?: VoiceRef[];
}

export interface TranscriberRef {
  provider:
    | "mock"
    | "loopback"
    | "wispral-core"
    | "sapi"
    | "whisper"
    | "whisper.cpp"
    | "deepgram"
    | "assemblyai"
    | "openai"
    | "custom";
  model?: string;
  language?: string;
  baseUrl?: string;
  credentialRef?: string;
  fallbacks?: TranscriberRef[];
}

export interface Credential {
  id: Id;
  tenantId: Id;
  name: string;
  provider: string;
  /** AES-256-GCM ciphertext, never plaintext at rest. */
  ciphertext: string;
  createdAt: ISODate;
  lastRotatedAt?: ISODate;
}

/* ------------------------------------------------------------------ */
/* Agents                                                              */
/* ------------------------------------------------------------------ */

export type AgentStatus = "draft" | "published" | "archived";

export type ToolType =
  | "function"
  | "api_request"
  | "transfer"
  | "handoff"
  | "end_call"
  | "dtmf"
  | "mcp"
  | "query"
  | "internal"
  | "n8n_workflow"
  | "workflow";

/** Built-in actions that need no external service. */
export type InternalToolAction =
  | "create_booking"
  | "create_task"
  | "upsert_contact"
  | "escalate"
  | "lookup_order";

export interface ToolDefinition {
  id: Id;
  tenantId: Id;
  type: ToolType;
  name: string;
  description: string;
  parameters: JsonSchema;
  /** function + api_request */
  serverUrl?: string;
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  headers?: Record<string, string>;
  staticBody?: Record<string, JsonValue>;
  /** Fields the model may never set, resolved server-side. Prompt-injection boundary. */
  trustedFields?: Record<string, JsonValue>;
  timeoutMs?: number;
  /** transfer + handoff */
  destinations?: string[];
  /** query */
  knowledgeBaseId?: Id;
  /** mcp */
  mcpServerUrl?: string;
  /** workflow: the local workflow to run; n8n_workflow keeps its URL in serverUrl */
  workflowId?: Id;
  /** internal */
  internalAction?: InternalToolAction;
  /** Security classification; high-risk tools refuse unverified caller ANI (OM-T2). */
  riskLevel?: "low" | "standard" | "high";
  requiresVerifiedCaller?: boolean;
  /** spoken filler */
  messages?: { onRequest?: string; onResult?: string; onError?: string };
  createdAt: ISODate;
  updatedAt: ISODate;
}

export interface AgentConfig {
  firstMessage: string;
  systemPrompt: string;
  model: ModelRef;
  voice: VoiceRef;
  transcriber: TranscriberRef;
  /** BCP-47 primary language, or "auto". */
  language: string;
  tools: ToolDefinition[];
  knowledgeBaseIds: Id[];
  maxDurationSec: number;
  silenceTimeoutSec: number;
  endCallPhrases: string[];
  interruption: { enabled: boolean; minWords: number };
  recording: { enabled: boolean; consentAnnouncement: boolean };
  variables: Record<string, JsonValue>;
  /** Optional workflow started when the call ends. */
  postCallWorkflowId?: Id;
}

export interface Agent {
  id: Id;
  tenantId: Id;
  name: string;
  description: string;
  status: AgentStatus;
  version: number;
  config: AgentConfig;
  createdAt: ISODate;
  updatedAt: ISODate;
  publishedAt?: ISODate;
}

export interface AgentVersion {
  id: Id;
  tenantId: Id;
  agentId: Id;
  version: number;
  config: AgentConfig;
  createdAt: ISODate;
  createdBy: string;
  note?: string;
}

/* ------------------------------------------------------------------ */
/* Telephony                                                           */
/* ------------------------------------------------------------------ */

export type PhoneProvider =
  | "simulated"
  | "sip"
  | "twilio"
  | "telnyx"
  | "vonage"
  | "signalwire"
  | "didww";

export interface IvrOption {
  /** DTMF key: 0-9, *, #. */
  key: string;
  label: string;
  action: "agent" | "voicemail" | "transfer" | "hangup" | "repeat";
  /** Agent id, phone number, or extension, depending on action. */
  target?: string;
}

export interface IvrMenu {
  id: Id;
  tenantId: Id;
  name: string;
  prompt: string;
  invalidPrompt: string;
  options: IvrOption[];
  timeoutSec: number;
  maxAttempts: number;
  createdAt: ISODate;
}

export interface PhoneNumber {
  id: Id;
  tenantId: Id;
  e164: string;
  label: string;
  provider: PhoneProvider;
  /** Carrier-side identifier (Twilio PN…); absent for simulated numbers. */
  providerNumberId?: string;
  /** Simulated numbers are always free and never leave the process. */
  simulated: boolean;
  inboundAgentId?: Id;
  inboundWorkflowId?: Id;
  ivrMenuId?: Id;
  outboundAgentId?: Id;
  capabilities: Array<"voice" | "sms" | "dtmf">;
  createdAt: ISODate;
  status: "active" | "disabled";
}

/* ------------------------------------------------------------------ */
/* SMS                                                                 */
/* ------------------------------------------------------------------ */

export interface SmsMessage {
  id: Id;
  tenantId: Id;
  direction: "inbound" | "outbound";
  from: string;
  to: string;
  body: string;
  provider: PhoneProvider;
  providerMessageId?: string;
  status: "queued" | "sent" | "delivered" | "failed" | "received";
  /** Simulated messages are stored locally and never sent to a carrier. */
  simulated: boolean;
  error?: string;
  createdAt: ISODate;
}

/* ------------------------------------------------------------------ */
/* Calls                                                               */
/* ------------------------------------------------------------------ */

export type CallDirection = "inbound" | "outbound";
export type CallStatus = "queued" | "ringing" | "in_progress" | "ended" | "failed";

export type EndedReason =
  | "customer_ended"
  | "assistant_ended"
  | "max_duration"
  | "silence_timeout"
  | "transfer"
  | "handoff"
  | "voicemail"
  | "no_answer"
  | "busy"
  | "error"
  | "canceled";

export interface CallTurn {
  id: Id;
  role: "caller" | "assistant" | "system";
  text: string;
  at: ISODate;
  offsetMs: number;
  interrupted?: boolean;
  latencyMs?: number;
}

export type ChatRole = "system" | "user" | "assistant" | "tool";

export interface ChatMessage {
  role: ChatRole;
  content: string;
  at: ISODate;
  toolCallId?: string;
  toolName?: string;
  toolCalls?: Array<{ id: string; name: string; arguments: string }>;
  interrupted?: boolean;
}

export interface CallMetrics {
  turnCount: number;
  /** caller speech end -> first assistant audio, milliseconds */
  turnLatenciesMs: number[];
  totalTokensIn: number;
  totalTokensOut: number;
  toolCalls: number;
  interruptions: number;
}

export interface Call {
  id: Id;
  tenantId: Id;
  direction: CallDirection;
  status: CallStatus;
  from: string;
  to: string;
  phoneNumberId?: Id;
  agentId?: Id;
  agentVersion?: number;
  workflowId?: Id;
  startedAt: ISODate;
  answeredAt?: ISODate;
  endedAt?: ISODate;
  endedReason?: EndedReason;
  /** Human-readable transcript for the UI. */
  transcript: CallTurn[];
  /** Model-visible history. */
  messages: ChatMessage[];
  variables: Record<string, JsonValue>;
  metadata: Record<string, JsonValue>;
  recording?: {
    enabled: boolean;
    consentAnnounced: boolean;
    url?: string;
    durationMs?: number;
  };
  metrics: CallMetrics;
  simulation: boolean;
  error?: string;
}

/* ------------------------------------------------------------------ */
/* Knowledge                                                           */
/* ------------------------------------------------------------------ */

export interface KnowledgeDocument {
  id: Id;
  title: string;
  text: string;
  source?: string;
  createdAt: ISODate;
  checksum: string;
}

export interface KnowledgeBase {
  id: Id;
  tenantId: Id;
  name: string;
  description: string;
  documents: KnowledgeDocument[];
  createdAt: ISODate;
  updatedAt: ISODate;
}

/* ------------------------------------------------------------------ */
/* Workflows                                                           */
/* ------------------------------------------------------------------ */

export type WorkflowStatus = "draft" | "active" | "archived";

export const TRIGGER_TYPES = ["manual", "webhook", "call_ended", "schedule", "event"] as const;

export type TriggerType = (typeof TRIGGER_TYPES)[number];

export interface WorkflowTrigger {
  type: TriggerType;
  /** webhook path suffix, event name, or cron expression */
  config: Record<string, JsonValue>;
}

export const NODE_TYPES = [
  "trigger",
  "http",
  "branch",
  "set",
  "delay",
  "loop",
  "trello.create_card",
  "trello.update_card",
  "trello.move_card",
  "trello.add_comment",
  "trello.add_label",
  "trello.assign_member",
  "trello.set_due",
  "trello.create_list",
  "trello.list_cards",
  "calendar.create_event",
  "crm.upsert_contact",
  "sms.send",
  "email.send",
  "n8n.webhook",
  "human.escalate",
  "call.start",
  "local.create_task",
  "local.update_task",
  "local.create_booking",
  "local.upsert_contact",
  "google.calendar_create_event",
  "google.gmail_send",
  "google.sheets_append",
  "slack.post_message",
  "whatsapp.send_message",
  "end",
] as const;

export type NodeType = (typeof NODE_TYPES)[number];

export interface WorkflowNode {
  id: string;
  type: NodeType;
  name: string;
  config: Record<string, JsonValue>;
  /** Retry policy for side-effecting nodes. */
  retry?: { attempts: number; backoffMs: number };
  timeoutMs?: number;
}

export interface WorkflowEdge {
  from: string;
  to: string;
  /** Optional condition evaluated against the run context. Branch nodes use "true"/"false". */
  when?: string;
}

export interface Workflow {
  id: Id;
  tenantId: Id;
  name: string;
  description: string;
  status: WorkflowStatus;
  version: number;
  trigger: WorkflowTrigger;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  /** Idempotency window in seconds for trigger keys. */
  idempotencyWindowSec: number;
  createdAt: ISODate;
  updatedAt: ISODate;
}

export interface WorkflowVersion {
  id: Id;
  tenantId: Id;
  workflowId: Id;
  version: number;
  snapshot: {
    name: string;
    description: string;
    status: WorkflowStatus;
    trigger: WorkflowTrigger;
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    idempotencyWindowSec: number;
  };
  createdAt: ISODate;
  createdBy: string;
  note?: string;
}

export type WorkflowRunStatus = "running" | "succeeded" | "failed" | "skipped";

export interface WorkflowStep {
  id: Id;
  nodeId: string;
  nodeType: NodeType;
  status: "succeeded" | "failed" | "skipped";
  startedAt: ISODate;
  endedAt: ISODate;
  attempts: number;
  input?: JsonValue;
  output?: JsonValue;
  error?: string;
}

export interface WorkflowRun {
  id: Id;
  tenantId: Id;
  workflowId: Id;
  workflowVersion: number;
  status: WorkflowRunStatus;
  trigger: { type: TriggerType; payload: JsonValue };
  idempotencyKey?: string;
  context: Record<string, JsonValue>;
  steps: WorkflowStep[];
  startedAt: ISODate;
  endedAt?: ISODate;
  error?: string;
  callId?: Id;
}

/* ------------------------------------------------------------------ */
/* Campaigns                                                           */
/* ------------------------------------------------------------------ */

export interface CampaignContact {
  id: Id;
  phone: string;
  name?: string;
  variables: Record<string, JsonValue>;
  status: "pending" | "calling" | "completed" | "failed" | "skipped";
  callId?: Id;
  attempts: number;
  lastAttemptAt?: ISODate;
}

export interface Campaign {
  id: Id;
  tenantId: Id;
  name: string;
  agentId: Id;
  phoneNumberId: Id;
  status: "draft" | "running" | "paused" | "completed" | "archived";
  contacts: CampaignContact[];
  concurrency: number;
  /** Local-time window, e.g. 09:00-17:00. Enforced; never call outside it. */
  callingWindow: { start: string; end: string; timezone: string; days: number[] };
  createdAt: ISODate;
  updatedAt: ISODate;
}

/* ------------------------------------------------------------------ */
/* Local automation records                                            */
/* ------------------------------------------------------------------ */

export interface Contact {
  id: Id;
  tenantId: Id;
  name: string;
  email?: string;
  phone?: string;
  tags: string[];
  attributes: Record<string, JsonValue>;
  createdAt: ISODate;
  updatedAt: ISODate;
}

export interface Booking {
  id: Id;
  tenantId: Id;
  title: string;
  name: string;
  phone?: string;
  email?: string;
  startAt: ISODate;
  durationMin: number;
  status: "confirmed" | "cancelled" | "completed" | "no_show";
  notes?: string;
  source: string;
  callId?: Id;
  createdAt: ISODate;
}

export interface Task {
  id: Id;
  tenantId: Id;
  title: string;
  description: string;
  status: "todo" | "doing" | "done";
  priority: "low" | "normal" | "high" | "urgent";
  labels: string[];
  assignee?: string;
  dueAt?: ISODate;
  source: "workflow" | "call" | "manual";
  callId?: Id;
  createdAt: ISODate;
  updatedAt: ISODate;
}

export interface Escalation {
  id: Id;
  tenantId: Id;
  reason: string;
  status: "open" | "acknowledged" | "closed";
  context: Record<string, JsonValue>;
  createdAt: ISODate;
}

/* ------------------------------------------------------------------ */
/* Observability and security                                          */
/* ------------------------------------------------------------------ */

export interface AuditEvent {
  id: Id;
  tenantId: Id;
  actor: string;
  action: string;
  target?: string;
  outcome: "allowed" | "denied";
  at: ISODate;
  detail?: Record<string, JsonValue>;
}

export interface WebhookEndpoint {
  id: Id;
  tenantId: Id;
  name: string;
  url: string;
  events: string[];
  secret: string;
  createdAt: ISODate;
  active: boolean;
}

export interface EvaluationCase {
  id: Id;
  name: string;
  callerTurns: string[];
  expectations: {
    mustContain?: string[];
    mustNotContain?: string[];
    mustCallTools?: string[];
    maxTurns?: number;
  };
}

export interface Evaluation {
  id: Id;
  tenantId: Id;
  agentId: Id;
  agentVersion: number;
  name: string;
  cases: EvaluationCase[];
  runs: EvaluationRun[];
  createdAt: ISODate;
}

export interface EvaluationRun {
  id: Id;
  startedAt: ISODate;
  endedAt?: ISODate;
  status: "passed" | "failed" | "error";
  results: Array<{
    caseId: Id;
    passed: boolean;
    failures: string[];
    callId?: Id;
    transcript: string[];
  }>;
}
