import type {
  LlmDelta,
  LlmProvider,
  LlmRequest,
  SttProvider,
  SynthesizedAudio,
  TranscriptResult,
  TtsOptions,
  TtsProvider,
} from "@omalla/core";
import { estimateSpeechDurationMs, silenceWav } from "@omalla/core";

/* ------------------------------------------------------------------ */
/* Scripted LLM — deterministic, used by tests and evals               */
/* ------------------------------------------------------------------ */

export type ScriptStep =
  | { kind: "text"; text: string }
  | { kind: "tool"; name: string; arguments: Record<string, unknown> };

export class ScriptedLlm implements LlmProvider {
  readonly id = "scripted";
  private cursor = 0;

  constructor(
    private readonly script: ScriptStep[],
    private readonly fallback = "Is there anything else I can help you with?",
  ) {}

  async *chat(request: LlmRequest): AsyncIterable<LlmDelta> {
    const step = this.script[this.cursor];
    if (!step) {
      yield { type: "text", text: this.fallback };
      yield { type: "done", finishReason: "stop" };
      return;
    }

    if (step.kind === "tool") {
      this.cursor += 1;
      yield {
        type: "tool_call",
        toolCall: {
          id: `call_${this.cursor}`,
          name: step.name,
          arguments: JSON.stringify(step.arguments),
        },
      };
      yield { type: "done", finishReason: "tool_calls" };
      return;
    }

    this.cursor += 1;
    const chunks = chunkText(step.text, 18);
    for (const chunk of chunks) {
      if (request.signal?.aborted) throw abortError();
      yield { type: "text", text: chunk };
      await tick();
    }
    yield { type: "done", finishReason: "stop" };
  }
}

/* ------------------------------------------------------------------ */
/* Demo LLM — deterministic slot filling without a model download      */
/* ------------------------------------------------------------------ */

const MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];

export interface BookingSlots {
  name?: string;
  when?: string;
}

/**
 * A rule-based assistant used when no model is configured.
 *
 * This is intentionally labelled a demo provider: it exercises the full
 * runtime (streaming, tools, interruption) with zero cost and zero network,
 * but it is not a language model and never claims to be one.
 */
export class DemoLlm implements LlmProvider {
  readonly id = "demo";

  constructor(
    private readonly config: {
      bookingTool?: string;
      transferTool?: string;
      endTool?: string;
      businessName?: string;
    } = {},
  ) {}

  async *chat(request: LlmRequest): AsyncIterable<LlmDelta> {
    const last = [...request.messages].reverse().find((message) => message.role !== "system");
    const text = (last?.content ?? "").toLowerCase();

    if (last?.role === "tool") {
      const summary = summarizeToolResult(last.content);
      yield* this.say(summary);
      return;
    }

    if (looksLikeGoodbye(text) && this.config.endTool) {
      yield* this.toolCall(this.config.endTool, { reason: "caller said goodbye" });
      return;
    }
    if (wantsHuman(text) && this.config.transferTool) {
      yield* this.toolCall(this.config.transferTool, { reason: "caller asked for a person" });
      return;
    }

    if (this.config.bookingTool && (isBookingIntent(text) || isBookingFollowUp(request))) {
      const slots = extractSlots(request.messages);
      if (!slots.name) {
        yield* this.say("Happy to book that. What name should I put on the appointment?");
        return;
      }
      if (!slots.when) {
        yield* this.say(`Thanks, ${slots.name}. What day and time works best for you?`);
        return;
      }
      if (!isConfirmed(request.messages)) {
        yield* this.say(`Let me confirm: ${slots.name}, ${slots.when}. Should I book that now?`);
        return;
      }
      yield* this.toolCall(this.config.bookingTool, { name: slots.name, when: slots.when });
      return;
    }

    if (text.includes("hours") || text.includes("open")) {
      yield* this.say("We are open Monday to Friday, nine in the morning to five in the afternoon.");
      return;
    }
    if (text.includes("price") || text.includes("cost") || text.includes("how much")) {
      yield* this.say("Pricing depends on the service. I can have the team send you a precise quote.");
      return;
    }

    yield* this.say(
      "I can help with that. Could you tell me a little more about what you need?",
    );
  }

  private async *say(text: string): AsyncIterable<LlmDelta> {
    for (const chunk of chunkText(text, 16)) {
      yield { type: "text", text: chunk };
      await tick();
    }
    yield { type: "done", finishReason: "stop" };
  }

  private async *toolCall(name: string, args: Record<string, unknown>): AsyncIterable<LlmDelta> {
    yield {
      type: "tool_call",
      toolCall: { id: `call_${Date.now()}`, name, arguments: JSON.stringify(args) },
    };
    yield { type: "done", finishReason: "tool_calls" };
  }
}

/* ------------------------------------------------------------------ */
/* Mock audio providers                                                */
/* ------------------------------------------------------------------ */

export class MockTts implements TtsProvider {
  readonly id = "mock";
  readonly spoken: string[] = [];
  private latencyMs: number;

  constructor(options: { latencyMs?: number } = {}) {
    this.latencyMs = options.latencyMs ?? 0;
  }

  async synthesize(text: string, options: TtsOptions): Promise<SynthesizedAudio> {
    if (options.signal?.aborted) throw abortError();
    if (this.latencyMs > 0) await sleep(this.latencyMs);
    this.spoken.push(text);
    const durationMs = estimateSpeechDurationMs(text);
    const wav = silenceWav(durationMs);
    return { data: wav, mimeType: "audio/wav", durationMs };
  }
}

export class MockStt implements SttProvider {
  readonly id = "mock";
  private queue: TranscriptResult[];

  constructor(initial: string[] = []) {
    this.queue = initial.map((text) => ({ text, confidence: 1, isFinal: true }));
  }

  push(text: string): void {
    this.queue.push({ text, confidence: 1, isFinal: true });
  }

  async transcribe(): Promise<TranscriptResult> {
    return this.queue.shift() ?? { text: "", confidence: 0, isFinal: true };
  }
}

/* ------------------------------------------------------------------ */
/* helpers                                                             */
/* ------------------------------------------------------------------ */

function chunkText(text: string, size: number): string[] {
  const words = text.split(/(\s+)/);
  const chunks: string[] = [];
  let current = "";
  for (const word of words) {
    if (current.length + word.length > size && current.trim()) {
      chunks.push(current);
      current = word;
    } else {
      current += word;
    }
  }
  if (current.trim()) chunks.push(current);
  return chunks.length > 0 ? chunks : [text];
}

function isBookingIntent(text: string): boolean {
  return /\b(book|booking|appointment|schedule|reserve|meeting)\b/.test(text) ||
    /(حجز|موعد|احجز)/.test(text);
}

function isBookingFollowUp(request: LlmRequest): boolean {
  const recent = request.messages.slice(-4);
  return recent.some(
    (message) =>
      message.role === "assistant" &&
      /name should i put|what day and time|should i book|ما الاسم|أي يوم/.test(message.content.toLowerCase()),
  );
}

function isConfirmed(messages: LlmRequest["messages"]): boolean {
  const lastUser = [...messages].reverse().find((message) => message.role === "user");
  if (!lastUser) return false;
  return /\b(yes|yeah|yep|correct|confirm|that's right|please do|go ahead|sure)\b/i.test(lastUser.content) ||
    /(نعم|أكيد|اكيد|تمام|موافق|ايوه|تأكيد)/.test(lastUser.content);
}

function extractSlots(messages: LlmRequest["messages"]): BookingSlots {
  const userText = messages
    .filter((message) => message.role === "user")
    .map((message) => message.content)
    .join(" ");

  const nameMatch =
    userText.match(/\bmy name is ([A-Za-z][A-Za-z'-]{1,30})/i) ??
    userText.match(/\bthis is ([A-Za-z][A-Za-z'-]{1,30})/i) ??
    userText.match(/\bname(?:'s| is) ([A-Za-z][A-Za-z'-]{1,30})/i);

  const dayMatch = userText.match(
    /\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b[^.!?]{0,30}/i,
  );
  const timeMatch = userText.match(
    /\b(?:at|around)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b/i,
  );
  const monthMatch = new RegExp(`\\b(${MONTHS.join("|")})\\s+\\d{1,2}(?:st|nd|rd|th)?\\b`, "i").exec(userText);

  const when = [monthMatch?.[0] ?? dayMatch?.[0], timeMatch?.[0]].filter(Boolean).join(" ").trim();

  return {
    ...(nameMatch?.[1] ? { name: capitalize(nameMatch[1]) } : {}),
    ...(when ? { when } : {}),
  };
}

function summarizeToolResult(raw: string): string {
  try {
    const parsed = JSON.parse(raw) as { result?: Record<string, unknown>; ok?: boolean };
    if (parsed.ok === false) return "I could not complete that. Let me pass this to a person who can help.";
    const result = parsed.result ?? {};
    if (typeof result.when === "string" && typeof result.name === "string") {
      return `You're booked, ${result.name}, for ${result.when}. You'll get a confirmation shortly. Anything else?`;
    }
    if (typeof result.message === "string") return result.message;
    return "That's done. Is there anything else I can help you with?";
  } catch {
    return "That's done. Is there anything else I can help you with?";
  }
}

function wantsHuman(text: string): boolean {
  return /\b(human|person|agent|representative|someone real|transfer)\b/.test(text) ||
    /(موظف|بشري|إنسان|انسان|تحويل)/.test(text);
}

function looksLikeGoodbye(text: string): boolean {
  return /\b(bye|goodbye|that's all|no thanks|nothing else|hang up)\b/.test(text) ||
    /(مع السلامة|مع السلامه|انهي المكالمة|أنهي المكالمة|باي)/.test(text);
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function tick(): Promise<void> {
  return new Promise((resolve) => setImmediate(resolve));
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function abortError(): Error {
  const error = new Error("aborted");
  error.name = "AbortError";
  return error;
}
