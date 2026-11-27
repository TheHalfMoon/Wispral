import { encodeWav } from "@omalla/core";
import type { ConversationEngine, EndedReason, Logger, SttProvider, SynthesizedAudio } from "@omalla/core";
import {
  TELEPHONE_SAMPLE_RATE,
  UtteranceDetector,
  base64ToBytes,
  bytesToBase64,
  decodeMulaw,
  pcm16ToBytes,
  splitFrames,
  wavToTelephoneFrames,
} from "./audio.js";
import type { MediaStreamEvent, TelephonyProvider } from "./provider.js";

/** The slice of the conversation engine the bridge needs. */
export interface VoiceEngine {
  readonly isEnded: boolean;
  readonly isSpeaking: boolean;
  start(): Promise<void>;
  handleCallerUtterance(text: string): Promise<void>;
  interrupt(): void;
  end(reason?: EndedReason): Promise<void>;
  onAudio(handler: (audio: SynthesizedAudio, text: string) => void): () => void;
}

export interface MediaSocket {
  send(data: string): void;
  close(code?: number, reason?: string): void;
}

export interface MediaBridgeOptions {
  provider: TelephonyProvider;
  engine: VoiceEngine;
  stt: SttProvider;
  logger: Logger;
  language?: string;
  /** DTMF digits pressed by the caller during the media session. */
  onDtmf?: (digit: string) => void;
  onStop?: () => void;
  /** Hard cap on one utterance, protects memory on a stuck line. */
  maxUtteranceMs?: number;
  silenceMs?: number;
  speechThreshold?: number;
}

interface StreamState {
  streamId: string;
  callId: string;
}

/**
 * Bridges a carrier media stream to a conversation.
 *
 * Twilio sends 20 ms μ-law frames; the bridge detects utterance boundaries,
 * transcribes complete utterances, and converts synthesized WAV back into
 * μ-law frames. Barge-in clears the carrier's playback queue and aborts the
 * in-flight turn.
 */
export class MediaBridge {
  private socket: MediaSocket | null = null;
  private stream: StreamState | null = null;
  private readonly detector: UtteranceDetector;
  private preRoll: Int16Array[] = [];
  private capture: Int16Array[] = [];
  private capturedSamples = 0;
  private capturing = false;
  private closed = false;
  private playbackGeneration = 0;
  private queue: Promise<void> = Promise.resolve();
  private readonly unsubscribe: () => void;
  private readonly maxSamples: number;

  constructor(private readonly options: MediaBridgeOptions) {
    this.detector = new UtteranceDetector({
      ...(options.silenceMs !== undefined ? { silenceMs: options.silenceMs } : {}),
      ...(options.speechThreshold !== undefined ? { threshold: options.speechThreshold } : {}),
    });
    this.maxSamples = Math.round(((options.maxUtteranceMs ?? 45_000) / 1000) * TELEPHONE_SAMPLE_RATE);
    this.unsubscribe = options.engine.onAudio((audio) => {
      void this.play(audio);
    });
  }

  attach(socket: MediaSocket): void {
    this.socket = socket;
  }

  get isClosed(): boolean {
    return this.closed;
  }

  /** Resolves when all queued utterances have been processed. */
  async idle(): Promise<void> {
    await this.queue;
  }

  /** Entry point for every WebSocket text frame. */
  handleMessage(raw: string): void {
    if (this.closed) return;
    const parse = this.options.provider.parseMediaMessage;
    if (!parse) {
      this.options.logger.warn("provider has no media parser", { provider: this.options.provider.id });
      return;
    }
    const event = parse.call(this.options.provider, raw);
    switch (event.type) {
      case "connected":
        return;
      case "start":
        this.onStart(event);
        return;
      case "media":
        if (event.track === "inbound") this.onInboundAudio(event.payload);
        return;
      case "dtmf":
        if (event.digit) this.options.onDtmf?.(event.digit);
        return;
      case "stop":
        this.onStop();
        return;
      case "mark":
      case "unknown":
        return;
    }
  }

  /** Call when the carrier closes the socket. */
  async handleClose(): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    this.unsubscribe();
    this.options.onStop?.();
    if (!this.options.engine.isEnded) {
      await this.options.engine.end("customer_ended").catch((error: unknown) => {
        this.options.logger.warn("engine end failed after media close", {
          error: (error as Error).message,
        });
      });
    }
  }

  /** Server-initiated hangup. */
  async close(reason: EndedReason = "assistant_ended"): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    this.unsubscribe();
    try {
      this.socket?.close(1000, reason);
    } catch {
      // Socket may already be gone.
    }
    if (!this.options.engine.isEnded) await this.options.engine.end(reason);
  }

  private onStart(event: Extract<MediaStreamEvent, { type: "start" }>): void {
    this.stream = { streamId: event.streamId, callId: event.callId };
    this.options.logger.debug("media stream started", {
      streamId: event.streamId,
      callId: event.callId,
      encoding: event.format.encoding,
    });
    void this.options.engine.start().catch((error: unknown) => {
      this.options.logger.error("engine start failed", { error: (error as Error).message });
    });
  }

  private onInboundAudio(payload: string): void {
    if (!this.stream || !payload) return;
    const bytes = base64ToBytes(payload);
    const samples = decodeMulaw(bytes);
    const result = this.detector.push(samples);

    if (result === "speech" && this.options.engine.isSpeaking) {
      this.options.engine.interrupt();
      this.interruptPlayback();
    }

    if (result === "speech" || this.detector.isVoiced) {
      if (!this.capturing) {
        this.capturing = true;
        for (const frame of this.preRoll) {
          this.capture.push(frame);
          this.capturedSamples += frame.length;
        }
        this.preRoll = [];
      }
      this.capture.push(samples);
      this.capturedSamples += samples.length;
    } else if (!this.capturing) {
      this.preRoll.push(samples);
      if (this.preRoll.length > 15) this.preRoll.shift();
    }

    if (result === "final" || this.capturedSamples >= this.maxSamples) {
      const utterance = this.takeUtterance();
      if (utterance) {
        this.queue = this.queue
          .then(() => this.transcribeAndRespond(utterance))
          .catch((error: unknown) => {
            this.options.logger.error("utterance handling failed", {
              error: (error as Error).message,
            });
          });
      }
    }
  }

  private takeUtterance(): Int16Array | null {
    const chunks = this.capture;
    const total = this.capturedSamples;
    this.capture = [];
    this.capturedSamples = 0;
    this.capturing = false;
    this.detector.reset();
    if (total < TELEPHONE_SAMPLE_RATE * 0.2) return null;
    const combined = new Int16Array(total);
    let offset = 0;
    for (const chunk of chunks) {
      combined.set(chunk, offset);
      offset += chunk.length;
    }
    return combined;
  }

  private async transcribeAndRespond(samples: Int16Array): Promise<void> {
    if (this.closed || this.options.engine.isEnded) return;
    const wav = encodeWav(pcm16ToBytes(samples), {
      sampleRate: TELEPHONE_SAMPLE_RATE,
      channels: 1,
      bitDepth: 16,
    });
    const transcript = await this.options.stt.transcribe(wav, {
      mimeType: "audio/wav",
      ...(this.options.language ? { language: this.options.language } : {}),
    });
    const text = transcript.text.trim();
    if (!text || !transcript.isFinal) return;
    await this.options.engine.handleCallerUtterance(text);
  }

  private async play(audio: SynthesizedAudio): Promise<void> {
    const stream = this.stream;
    if (!stream || this.closed || this.options.engine.isEnded) return;
    const generation = this.playbackGeneration;
    let frames: Uint8Array[];
    try {
      frames = toFrames(audio);
    } catch (error) {
      this.options.logger.warn("could not convert synthesized audio for telephony", {
        mimeType: audio.mimeType,
        error: (error as Error).message,
      });
      return;
    }
    for (const frame of frames) {
      if (this.closed || generation !== this.playbackGeneration) return;
      const encoded = this.options.provider.encodeMediaFrame?.(stream.streamId, bytesToBase64(frame));
      if (!encoded) {
        this.options.logger.warn("provider cannot encode media frames", { provider: this.options.provider.id });
        return;
      }
      this.send(encoded);
    }
    const mark = this.options.provider.encodeMarkFrame?.(stream.streamId, "omalla-audio");
    if (mark) this.send(mark);
  }

  private interruptPlayback(): void {
    this.playbackGeneration += 1;
    const stream = this.stream;
    if (!stream) return;
    const clear = this.options.provider.encodeClearFrame?.(stream.streamId);
    if (clear) this.send(clear);
  }

  private onStop(): void {
    this.options.onStop?.();
  }

  private send(payload: string): void {
    try {
      this.socket?.send(payload);
    } catch (error) {
      this.options.logger.warn("media socket send failed", { error: (error as Error).message });
    }
  }
}

/** Adapts a ConversationEngine to the bridge's narrow contract. */
export class ConversationVoiceEngine implements VoiceEngine {
  constructor(private readonly engine: ConversationEngine) {}

  get isEnded(): boolean {
    return this.engine.isEnded;
  }

  get isSpeaking(): boolean {
    return this.engine.isSpeaking;
  }

  start(): Promise<void> {
    return this.engine.start();
  }

  handleCallerUtterance(text: string): Promise<void> {
    return this.engine.handleCallerUtterance(text);
  }

  interrupt(): void {
    this.engine.interrupt();
  }

  end(reason?: EndedReason): Promise<void> {
    return this.engine.end(reason);
  }

  onAudio(handler: (audio: SynthesizedAudio, text: string) => void): () => void {
    return this.engine.on("assistant.audio", ({ audio, text }) => handler(audio, text));
  }
}

/** Converts provider audio to 8 kHz μ-law frames. */
export function toFrames(audio: SynthesizedAudio): Uint8Array[] {
  if (audio.mimeType.includes("wav")) {
    return wavToTelephoneFrames(audio.data).frames;
  }
  if (
    audio.mimeType.includes("mulaw") ||
    audio.mimeType.includes("pcmu") ||
    audio.mimeType.includes("g711")
  ) {
    return splitFrames(audio.data);
  }
  throw new Error(`unsupported telephony audio type: ${audio.mimeType}`);
}
