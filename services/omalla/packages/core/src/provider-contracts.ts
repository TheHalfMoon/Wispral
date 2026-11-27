import type { JsonSchema, JsonValue } from "./types.js";

/* ------------------------------------------------------------------ */
/* LLM                                                                 */
/* ------------------------------------------------------------------ */

export interface LlmToolSpec {
  name: string;
  description: string;
  parameters: JsonSchema;
}

export interface LlmToolCall {
  id: string;
  name: string;
  arguments: string;
}

export interface LlmMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  name?: string;
  toolCallId?: string;
  toolCalls?: LlmToolCall[];
}

export interface LlmRequest {
  messages: LlmMessage[];
  tools: LlmToolSpec[];
  temperature?: number;
  maxTokens?: number;
  signal?: AbortSignal;
}

export type LlmDelta =
  | { type: "text"; text: string }
  | { type: "tool_call"; toolCall: LlmToolCall }
  | { type: "usage"; promptTokens: number; completionTokens: number }
  | { type: "done"; finishReason: string };

export interface LlmProvider {
  readonly id: string;
  chat(request: LlmRequest): AsyncIterable<LlmDelta>;
}

/* ------------------------------------------------------------------ */
/* Text to speech                                                      */
/* ------------------------------------------------------------------ */

export interface SynthesizedAudio {
  data: Uint8Array;
  mimeType: string;
  /** Estimated duration when the provider does not report one. */
  durationMs: number;
}

export interface TtsOptions {
  voiceId: string;
  speed?: number;
  language?: string;
  signal?: AbortSignal;
}

export interface TtsProvider {
  readonly id: string;
  synthesize(text: string, options: TtsOptions): Promise<SynthesizedAudio>;
}

/* ------------------------------------------------------------------ */
/* Speech to text                                                      */
/* ------------------------------------------------------------------ */

export interface SttOptions {
  language?: string;
  mimeType?: string;
  signal?: AbortSignal;
}

export interface TranscriptResult {
  text: string;
  confidence: number;
  isFinal: boolean;
  language?: string;
}

export interface SttProvider {
  readonly id: string;
  transcribe(audio: Uint8Array, options?: SttOptions): Promise<TranscriptResult>;
}

/* ------------------------------------------------------------------ */
/* Tools                                                               */
/* ------------------------------------------------------------------ */

export interface ToolCallContext {
  callId: string;
  tenantId: string;
  agentId: string;
  agentName: string;
  direction: "inbound" | "outbound";
  callerNumber: string;
  variables: Record<string, JsonValue>;
  /** Values the model must never control. */
  trusted: Record<string, JsonValue>;
}

export type ToolControl =
  | { kind: "none" }
  | { kind: "transfer"; destination: string; mode: "blind" | "warm" }
  | { kind: "handoff"; agentId: string }
  | { kind: "end_call"; reason?: string }
  | { kind: "dtmf"; keys: string };

export interface ToolExecutionResult {
  ok: boolean;
  /** Structured result returned to the model. */
  result?: JsonValue;
  error?: string;
  /** Text the assistant should say before or after the action. */
  speech?: string;
  control?: ToolControl;
  /** Set by the executor when a retry is safe. */
  retryable?: boolean;
  latencyMs?: number;
}

export interface ToolInvocation {
  toolId: string;
  name: string;
  args: Record<string, JsonValue>;
  context: ToolCallContext;
  dryRun?: boolean;
  signal?: AbortSignal;
}

export interface ToolExecutor {
  execute(invocation: ToolInvocation): Promise<ToolExecutionResult>;
}

/* ------------------------------------------------------------------ */
/* Retrieval                                                           */
/* ------------------------------------------------------------------ */

export interface RetrievalHit {
  documentId: string;
  title: string;
  text: string;
  score: number;
}

export interface Retriever {
  search(query: string, limit?: number): RetrievalHit[];
}
