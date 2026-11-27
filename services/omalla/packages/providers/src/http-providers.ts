import { OmallaError } from "@omalla/core";
import type { SttProvider, SynthesizedAudio, TtsOptions, TtsProvider, TranscriptResult } from "@omalla/core";

/** OpenAI-compatible text-to-speech (BYOK, optional). */
export class OpenAiTts implements TtsProvider {
  readonly id = "openai";

  constructor(
    private readonly options: { apiKey: string; baseUrl?: string; model?: string; fetchImpl?: typeof fetch },
  ) {}

  async synthesize(text: string, options: TtsOptions): Promise<SynthesizedAudio> {
    const fetchImpl = this.options.fetchImpl ?? fetch;
    const baseUrl = (this.options.baseUrl ?? "https://api.openai.com/v1").replace(/\/$/, "");
    const response = await fetchImpl(`${baseUrl}/audio/speech`, {
      method: "POST",
      headers: {
        authorization: `Bearer ${this.options.apiKey}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: this.options.model ?? "gpt-4o-mini-tts",
        voice: options.voiceId,
        input: text,
        response_format: "wav",
        speed: options.speed ?? 1,
      }),
      signal: options.signal,
    });
    if (!response.ok) {
      throw new OmallaError("provider_error", `OpenAI TTS returned ${response.status}`, 502);
    }
    const data = new Uint8Array(await response.arrayBuffer());
    return { data, mimeType: "audio/wav", durationMs: estimateDuration(text) };
  }
}

/** OpenAI-compatible transcription (BYOK, optional). */
export class OpenAiStt implements SttProvider {
  readonly id = "openai";

  constructor(
    private readonly options: { apiKey: string; baseUrl?: string; model?: string; fetchImpl?: typeof fetch },
  ) {}

  async transcribe(audio: Uint8Array, options: Parameters<SttProvider["transcribe"]>[1] = {}): Promise<TranscriptResult> {
    const fetchImpl = this.options.fetchImpl ?? fetch;
    const baseUrl = (this.options.baseUrl ?? "https://api.openai.com/v1").replace(/\/$/, "");
    const form = new FormData();
    form.append("file", new Blob([audio], { type: options.mimeType ?? "audio/wav" }), "audio.wav");
    form.append("model", this.options.model ?? "whisper-1");
    if (options.language) form.append("language", options.language);

    const response = await fetchImpl(`${baseUrl}/audio/transcriptions`, {
      method: "POST",
      headers: { authorization: `Bearer ${this.options.apiKey}` },
      body: form,
      signal: options.signal,
    });
    if (!response.ok) {
      throw new OmallaError("provider_error", `OpenAI STT returned ${response.status}`, 502);
    }
    const payload = (await response.json()) as { text?: string };
    return { text: payload.text ?? "", confidence: 0.9, isFinal: true, language: options.language };
  }
}

function estimateDuration(text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length || 1;
  return Math.max(250, Math.round((words / 2.6) * 1000));
}
