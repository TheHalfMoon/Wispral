import { OmallaError } from "@omalla/core";
import type { LlmDelta, LlmMessage, LlmProvider, LlmRequest, LlmToolCall } from "@omalla/core";

export interface OpenAiCompatibleOptions {
  baseUrl: string;
  apiKey: string;
  model: string;
  headers?: Record<string, string>;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
}

interface OpenAiChunk {
  choices?: Array<{
    delta?: {
      content?: string | null;
      tool_calls?: Array<{
        index?: number;
        id?: string;
        function?: { name?: string; arguments?: string };
      }>;
    };
    finish_reason?: string | null;
  }>;
  usage?: { prompt_tokens?: number; completion_tokens?: number };
}

/**
 * Streaming adapter for any OpenAI-compatible chat endpoint: OpenAI, Ollama,
 * OpenRouter, Together, vLLM, LM Studio, llama.cpp server.
 */
export class OpenAiCompatibleLlm implements LlmProvider {
  readonly id: string;

  constructor(private readonly options: OpenAiCompatibleOptions) {
    this.id = options.baseUrl.includes("ollama") ? "ollama" : "openai-compatible";
  }

  async *chat(request: LlmRequest): AsyncIterable<LlmDelta> {
    const fetchImpl = this.options.fetchImpl ?? fetch;
    const url = `${this.options.baseUrl.replace(/\/$/, "")}/chat/completions`;
    const timeout = AbortSignal.timeout(this.options.timeoutMs ?? 45_000);
    const signal = request.signal ? AbortSignal.any([request.signal, timeout]) : timeout;

    const body: Record<string, unknown> = {
      model: this.options.model,
      messages: request.messages.map(toOpenAiMessage),
      stream: true,
      stream_options: { include_usage: true },
    };
    if (request.temperature !== undefined) body.temperature = request.temperature;
    if (request.maxTokens !== undefined) body.max_tokens = request.maxTokens;
    if (request.tools.length > 0) {
      body.tools = request.tools.map((tool) => ({
        type: "function",
        function: { name: tool.name, description: tool.description, parameters: tool.parameters },
      }));
      body.tool_choice = "auto";
    }

    let response: Response;
    try {
      response = await fetchImpl(url, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(this.options.apiKey ? { authorization: `Bearer ${this.options.apiKey}` } : {}),
          ...this.options.headers,
        },
        body: JSON.stringify(body),
        signal,
      });
    } catch (error) {
      if (signal.aborted) throw abortError();
      throw new OmallaError("provider_error", `LLM request failed: ${(error as Error).message}`, 502);
    }

    if (!response.ok || !response.body) {
      const detail = await safeText(response);
      throw new OmallaError(
        "provider_error",
        `LLM returned ${response.status}: ${detail.slice(0, 300)}`,
        502,
      );
    }

    const toolCalls = new Map<number, { id: string; name: string; arguments: string }>();
    const decoder = new TextDecoder();
    let buffer = "";
    let finishReason = "stop";

    for await (const chunk of response.body as unknown as AsyncIterable<Uint8Array>) {
      buffer += decoder.decode(chunk, { stream: true });
      let separator = buffer.indexOf("\n\n");
      while (separator >= 0) {
        const rawEvent = buffer.slice(0, separator);
        buffer = buffer.slice(separator + 2);
        separator = buffer.indexOf("\n\n");

        for (const line of rawEvent.split("\n")) {
          if (!line.startsWith("data:")) continue;
          const data = line.slice(5).trim();
          if (!data || data === "[DONE]") continue;
          let parsed: OpenAiChunk;
          try {
            parsed = JSON.parse(data) as OpenAiChunk;
          } catch {
            continue;
          }

          if (parsed.usage) {
            yield {
              type: "usage",
              promptTokens: parsed.usage.prompt_tokens ?? 0,
              completionTokens: parsed.usage.completion_tokens ?? 0,
            };
          }

          const choice = parsed.choices?.[0];
          if (!choice) continue;
          if (choice.finish_reason) finishReason = choice.finish_reason;
          const delta = choice.delta;
          if (delta?.content) {
            yield { type: "text", text: delta.content };
          }
          for (const call of delta?.tool_calls ?? []) {
            const index = call.index ?? 0;
            const existing = toolCalls.get(index) ?? { id: "", name: "", arguments: "" };
            if (call.id) existing.id = call.id;
            if (call.function?.name) existing.name += call.function.name;
            if (call.function?.arguments) existing.arguments += call.function.arguments;
            toolCalls.set(index, existing);
          }
        }
      }
    }

    for (const [, call] of [...toolCalls.entries()].sort((a, b) => a[0] - b[0])) {
      if (!call.name) continue;
      const toolCall: LlmToolCall = {
        id: call.id || `call_${Math.random().toString(36).slice(2, 10)}`,
        name: call.name,
        arguments: call.arguments || "{}",
      };
      yield { type: "tool_call", toolCall };
    }

    yield { type: "done", finishReason };
  }
}

function toOpenAiMessage(message: LlmMessage): Record<string, unknown> {
  if (message.role === "tool") {
    return { role: "tool", content: message.content, tool_call_id: message.toolCallId ?? "" };
  }
  if (message.role === "assistant" && message.toolCalls && message.toolCalls.length > 0) {
    return {
      role: "assistant",
      content: message.content || null,
      tool_calls: message.toolCalls.map((call) => ({
        id: call.id,
        type: "function",
        function: { name: call.name, arguments: call.arguments },
      })),
    };
  }
  return { role: message.role, content: message.content };
}

async function safeText(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

export function abortError(): Error {
  const error = new Error("aborted");
  error.name = "AbortError";
  return error;
}
