import { OmallaError } from "@omalla/core";
import type {
  Agent,
  Logger,
  LlmProvider,
  ModelRef,
  SttProvider,
  TranscriberRef,
  TtsProvider,
  VoiceRef,
} from "@omalla/core";
import { FailoverLlm, FailoverStt, FailoverTts } from "./failover.js";
import { OpenAiStt, OpenAiTts } from "./http-providers.js";
import {
  DeepgramStt,
  ElevenLabsTts,
  LoopbackStt,
  LoopbackSynthTts,
  PiperTts,
  WhisperCppStt,
  WispralCoreLlm,
  WispralCoreStt,
  WispralCoreTts,
} from "./local-and-byok.js";
import { DemoLlm, MockStt, MockTts } from "./mock.js";
import { OpenAiCompatibleLlm } from "./openai-compatible.js";
import { SapiStt, SapiTts } from "./sapi.js";

export interface ProviderContext {
  logger: Logger;
  resolveCredential: (ref: string | undefined) => Promise<string | undefined>;
  fetchImpl?: typeof fetch;
  /** Overrides used by tests and the simulated environment. */
  mockStt?: SttProvider;
  mockTts?: TtsProvider;
  mockLlm?: LlmProvider;
}

export interface ResolvedProviders {
  llm: LlmProvider;
  tts: TtsProvider;
  stt: SttProvider;
}

export async function resolveProviders(agent: Agent, context: ProviderContext): Promise<ResolvedProviders> {
  const llm = await buildLlm(agent, context);
  const tts = await buildTts(agent, context);
  const stt = await buildStt(agent, context);
  return { llm, tts, stt };
}

async function buildLlm(agent: Agent, context: ProviderContext): Promise<LlmProvider> {
  const refs = [agent.config.model, ...(agent.config.model.fallbacks ?? [])];
  assertNoImplicitPaidFallback(refs.map((r) => r.provider));
  const providers: LlmProvider[] = [];
  for (const ref of refs) {
    providers.push(await buildOneLlm(ref, agent, context));
  }
  return providers.length === 1 ? (providers[0] as LlmProvider) : new FailoverLlm(providers, context.logger);
}

async function buildOneLlm(ref: ModelRef, agent: Agent, context: ProviderContext): Promise<LlmProvider> {
  switch (ref.provider) {
    case "mock":
    case "loopback":
      if (context.mockLlm) return context.mockLlm;
      return new DemoLlm({
        businessName: agent.name,
        bookingTool: findToolByName(agent, ["book_appointment", "schedule_appointment", "create_booking"]),
        transferTool: findToolByName(agent, ["transfer_call", "transfer_to_human", "handoff"]),
        endTool: findToolByName(agent, ["end_call", "hang_up"]),
      });
    case "wispral-core":
      return new WispralCoreLlm({
        ...(ref.baseUrl ? { baseUrl: ref.baseUrl } : {}),
        model: ref.model || "wispral-local",
        ...(context.fetchImpl ? { fetchImpl: context.fetchImpl } : {}),
      });
    case "ollama":
      return new OpenAiCompatibleLlm({
        baseUrl: ref.baseUrl ?? "http://127.0.0.1:11434/v1",
        apiKey: "ollama",
        model: ref.model || "qwen2.5:1.5b",
        fetchImpl: context.fetchImpl,
      });
    case "openai": {
      const apiKey = await requireCredential(ref.credentialRef, context, "OpenAI");
      return new OpenAiCompatibleLlm({
        baseUrl: ref.baseUrl ?? "https://api.openai.com/v1",
        apiKey,
        model: ref.model || "gpt-4o-mini",
        fetchImpl: context.fetchImpl,
      });
    }
    case "openai-compatible": {
      if (!ref.baseUrl) {
        throw new OmallaError("validation", "openai-compatible models require a baseUrl", 400);
      }
      const apiKey = (await context.resolveCredential(ref.credentialRef)) ?? "";
      return new OpenAiCompatibleLlm({
        baseUrl: ref.baseUrl,
        apiKey,
        model: ref.model,
        fetchImpl: context.fetchImpl,
      });
    }
    case "local":
      return new OpenAiCompatibleLlm({
        baseUrl: ref.baseUrl ?? "http://127.0.0.1:8080/v1",
        apiKey: "",
        model: ref.model,
        fetchImpl: context.fetchImpl,
      });
    case "anthropic":
      throw new OmallaError(
        "provider_error",
        "the Anthropic adapter requires an OpenAI-compatible gateway",
        501,
      );
    default:
      throw new OmallaError("provider_error", `unknown model provider: ${String(ref.provider)}`, 400);
  }
}

async function buildTts(agent: Agent, context: ProviderContext): Promise<TtsProvider> {
  const refs = [agent.config.voice, ...(agent.config.voice.fallbacks ?? [])];
  assertNoImplicitPaidFallback(refs.map((r) => r.provider));
  const providers: TtsProvider[] = [];
  for (const ref of refs) {
    providers.push(await buildOneTts(ref, context));
  }
  return providers.length === 1 ? (providers[0] as TtsProvider) : new FailoverTts(providers, context.logger);
}

async function buildOneTts(ref: VoiceRef, context: ProviderContext): Promise<TtsProvider> {
  switch (ref.provider) {
    case "mock":
      return context.mockTts ?? new MockTts();
    case "loopback":
    case "synth":
      return context.mockTts ?? new LoopbackSynthTts();
    case "piper":
      return new PiperTts({
        ...(ref.baseUrl ? { baseUrl: ref.baseUrl } : {}),
        ...(context.fetchImpl ? { fetchImpl: context.fetchImpl } : {}),
      });
    case "wispral-core":
      return new WispralCoreTts({
        ...(ref.baseUrl ? { baseUrl: ref.baseUrl } : {}),
        ...(context.fetchImpl ? { fetchImpl: context.fetchImpl } : {}),
      });
    case "sapi":
      if (process.platform !== "win32") {
        throw new OmallaError("provider_error", "the SAPI voice provider requires Windows", 501);
      }
      return new SapiTts();
    case "openai": {
      const apiKey = await requireCredential(ref.credentialRef, context, "OpenAI");
      return new OpenAiTts({ apiKey, baseUrl: ref.baseUrl, fetchImpl: context.fetchImpl });
    }
    case "elevenlabs": {
      const apiKey = await requireCredential(ref.credentialRef, context, "ElevenLabs");
      return new ElevenLabsTts({
        apiKey,
        ...(ref.baseUrl ? { baseUrl: ref.baseUrl } : {}),
        ...(context.fetchImpl ? { fetchImpl: context.fetchImpl } : {}),
      });
    }
    case "kokoro":
    case "custom": {
      if (!ref.baseUrl) {
        throw new OmallaError("validation", `${ref.provider} voice requires an explicit local baseUrl`, 400);
      }
      const apiKey = (await context.resolveCredential(ref.credentialRef)) ?? "";
      return new OpenAiTts({ apiKey, baseUrl: ref.baseUrl, fetchImpl: context.fetchImpl });
    }
    default:
      throw new OmallaError("provider_error", `unknown voice provider: ${String(ref.provider)}`, 400);
  }
}

async function buildStt(agent: Agent, context: ProviderContext): Promise<SttProvider> {
  const refs = [agent.config.transcriber, ...(agent.config.transcriber.fallbacks ?? [])];
  assertNoImplicitPaidFallback(refs.map((r) => r.provider));
  const providers: SttProvider[] = [];
  for (const ref of refs) {
    providers.push(await buildOneStt(ref, context));
  }
  return providers.length === 1 ? (providers[0] as SttProvider) : new FailoverStt(providers, context.logger);
}

async function buildOneStt(ref: TranscriberRef, context: ProviderContext): Promise<SttProvider> {
  switch (ref.provider) {
    case "mock":
      return context.mockStt ?? new MockStt();
    case "loopback":
      return context.mockStt ?? new LoopbackStt();
    case "whisper":
    case "whisper.cpp":
      return new WhisperCppStt({
        ...(ref.baseUrl ? { baseUrl: ref.baseUrl } : {}),
        ...(ref.model ? { model: ref.model } : {}),
        ...(context.fetchImpl ? { fetchImpl: context.fetchImpl } : {}),
      });
    case "wispral-core":
      return new WispralCoreStt({
        ...(ref.baseUrl ? { baseUrl: ref.baseUrl } : {}),
        ...(ref.model ? { model: ref.model } : {}),
        ...(context.fetchImpl ? { fetchImpl: context.fetchImpl } : {}),
      });
    case "sapi":
      if (process.platform !== "win32") {
        throw new OmallaError("provider_error", "the SAPI transcriber requires Windows", 501);
      }
      return new SapiStt();
    case "openai": {
      const apiKey = await requireCredential(ref.credentialRef, context, "OpenAI");
      return new OpenAiStt({ apiKey, baseUrl: ref.baseUrl, model: ref.model, fetchImpl: context.fetchImpl });
    }
    case "deepgram": {
      const apiKey = await requireCredential(ref.credentialRef, context, "Deepgram");
      return new DeepgramStt({
        apiKey,
        ...(ref.baseUrl ? { baseUrl: ref.baseUrl } : {}),
        ...(ref.model ? { model: ref.model } : {}),
        ...(context.fetchImpl ? { fetchImpl: context.fetchImpl } : {}),
      });
    }
    case "assemblyai":
    case "custom": {
      if (!ref.baseUrl) {
        throw new OmallaError("validation", `${ref.provider} transcription requires an explicit baseUrl`, 400);
      }
      const apiKey = (await context.resolveCredential(ref.credentialRef)) ?? "";
      return new OpenAiStt({ apiKey, baseUrl: ref.baseUrl, model: ref.model, fetchImpl: context.fetchImpl });
    }
    default:
      throw new OmallaError("provider_error", `unknown transcriber provider: ${String(ref.provider)}`, 400);
  }
}

const LOCAL_PROVIDERS = new Set([
  "mock",
  "loopback",
  "synth",
  "sapi",
  "piper",
  "whisper",
  "whisper.cpp",
  "wispral-core",
  "ollama",
  "local",
]);
const PAID_CLOUD_PROVIDERS = new Set(["openai", "elevenlabs", "deepgram", "anthropic", "assemblyai"]);

/**
 * Principle XXI: local routes MUST NEVER fall back to paid commercial providers.
 */
function assertNoImplicitPaidFallback(providers: readonly string[]): void {
  if (providers.length <= 1) return;
  const primary = providers[0] ?? "";
  if (!LOCAL_PROVIDERS.has(primary)) return;
  for (const fallback of providers.slice(1)) {
    if (PAID_CLOUD_PROVIDERS.has(fallback)) {
      throw new OmallaError(
        "blocked_by_policy",
        `local provider '${primary}' cannot configure paid fallback '${fallback}' (Principle XXI)`,
        400,
      );
    }
  }
}

async function requireCredential(
  ref: string | undefined,
  context: ProviderContext,
  label: string,
): Promise<string> {
  const value = await context.resolveCredential(ref);
  if (!value) {
    throw new OmallaError(
      "provider_error",
      `${label} requires a stored credential; add one in Settings -> Providers`,
      400,
    );
  }
  return value;
}

function findToolByName(agent: Agent, names: string[]): string | undefined {
  return agent.config.tools.find((tool) => names.includes(tool.name))?.name;
}
