import type { Logger } from "@omalla/core";
import type {
  LlmDelta,
  LlmProvider,
  LlmRequest,
  SttProvider,
  SynthesizedAudio,
  TtsOptions,
  TtsProvider,
} from "@omalla/core";

/**
 * Ordered failover.
 *
 * Failover is only safe before the first delta reaches the caller: switching
 * models mid-sentence would repeat or contradict what was already spoken.
 */
export class FailoverLlm implements LlmProvider {
  readonly id = "failover";

  constructor(
    private readonly providers: LlmProvider[],
    private readonly logger?: Logger,
  ) {}

  async *chat(request: LlmRequest): AsyncIterable<LlmDelta> {
    let lastError: unknown;
    for (const provider of this.providers) {
      let emitted = false;
      try {
        for await (const delta of provider.chat(request)) {
          emitted = true;
          yield delta;
        }
        return;
      } catch (error) {
        lastError = error;
        if (emitted || request.signal?.aborted) throw error;
        this.logger?.warn("llm provider failed, trying next", {
          provider: provider.id,
          error: (error as Error).message,
        });
      }
    }
    throw lastError ?? new Error("no language model providers configured");
  }
}

export class FailoverTts implements TtsProvider {
  readonly id = "failover";

  constructor(
    private readonly providers: TtsProvider[],
    private readonly logger?: Logger,
  ) {}

  async synthesize(text: string, options: TtsOptions): Promise<SynthesizedAudio> {
    let lastError: unknown;
    for (const provider of this.providers) {
      try {
        return await provider.synthesize(text, options);
      } catch (error) {
        if (options.signal?.aborted) throw error;
        lastError = error;
        this.logger?.warn("tts provider failed, trying next", {
          provider: provider.id,
          error: (error as Error).message,
        });
      }
    }
    throw lastError ?? new Error("no text-to-speech providers configured");
  }
}

export class FailoverStt implements SttProvider {
  readonly id = "failover";

  constructor(
    private readonly providers: SttProvider[],
    private readonly logger?: Logger,
  ) {}

  async transcribe(
    audio: Uint8Array,
    options: Parameters<SttProvider["transcribe"]>[1] = {},
  ): ReturnType<SttProvider["transcribe"]> {
    let lastError: unknown;
    for (const provider of this.providers) {
      try {
        const result = await provider.transcribe(audio, options);
        if (result.text) return result;
        lastError = new Error("empty transcript");
      } catch (error) {
        lastError = error;
        this.logger?.warn("stt provider failed, trying next", {
          provider: provider.id,
          error: (error as Error).message,
        });
      }
    }
    throw lastError ?? new Error("no speech-to-text providers configured");
  }
}
