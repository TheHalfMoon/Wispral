/**
 * Full-Duplex Realtime Voice Session (`RealtimeDuplexSession`).
 *
 * Bridges binary RFC 6455 WebSocket / WebRTC RTP frames (`PCM16`, `PCMU`, `PCMA`)
 * and JSON control events to `ConversationEngine`, `BoundedJitterBuffer`,
 * `OutboundAudioPacer`, energy VAD + barge-in ducking, and Sink-Confirmed
 * `T0..T6` Audio-Boundary Latency Telemetry (`OM-T8`).
 */
import { encodeWav, newId, type ConversationEngine, type Logger, type SttProvider } from "@omalla/core";
import {
  UtteranceDetector,
  decodeAlaw,
  decodeMulaw,
  pcm16FromBytes,
  pcm16ToBytes,
  resamplePcm16,
  speechEnergy,
} from "@omalla/telephony";
import { BoundedJitterBuffer, type JitterBufferStats } from "./jitter-buffer.js";
import { OutboundAudioPacer, type PacerStats, type RealtimeAudioCodec } from "./pacer.js";

export type HaltConfirmationStatus =
  | "observed_audio_halt"
  | "stopped_unconfirmed"
  | "pending_sink_ack"
  | "not_applicable";

/**
 * Sink-Confirmed `T0..T6` Audio-Boundary Latency Telemetry (`OM-T8`):
 *  - `T0`: user speech end (`t0SpeechEndMs`)
 *  - `T1`: barge-in onset (`t1BargeInOnsetMs`)
 *  - `T2`: sink-confirmed `observed_audio_halt` after outbound pacer flush + client
 *          `clear.ack` — OR `stopped_unconfirmed` on unacknowledged PSTN trunks (`OM-T8`)
 *  - `T3`: partial STT (`t3PartialSttMs`)
 *  - `T4`: final STT (`t4FinalSttMs`)
 *  - `T5`: first model/tool token (`t5FirstTokenMs`)
 *  - `T6`: first outbound TTS audio frame (`t6FirstAudioFrameMs`)
 */
export interface TurnLatencyTelemetry {
  turnId: string;
  turnEpoch: number;
  t0SpeechEndMs: number | null;
  t1BargeInOnsetMs: number | null;
  t2AudioHaltMs: number | null;
  t2HaltStatus: HaltConfirmationStatus;
  t3PartialSttMs: number | null;
  t4FinalSttMs: number | null;
  t5FirstTokenMs: number | null;
  t6FirstAudioFrameMs: number | null;
  deltasMs: {
    bargeInHaltMs: number | null;
    sttFinalMs: number | null;
    llmFirstTokenMs: number | null;
    ttsFirstFrameFromSpeechEndMs: number | null;
  };
}

export interface RealtimeTransportSink {
  readonly bufferedAmount?: number;
  sendJson(event: Record<string, unknown>): void;
  sendBinaryAudio(
    frameBytes: Uint8Array,
    meta: { seq: number; timestamp: number; turnEpoch: number; codec: RealtimeAudioCodec },
  ): void;
  close(code?: number, reason?: string): void;
}

export interface RealtimeDuplexSessionOptions {
  sessionId?: string;
  engine: ConversationEngine;
  stt: SttProvider;
  sink: RealtimeTransportSink;
  logger: Logger;
  codec?: RealtimeAudioCodec;
  sampleRate?: 8000 | 16000;
  language?: string;
  /** True for WS/WebRTC clients that reply `clear.ack`; false for unacknowledged PSTN trunks (`OM-T8`). */
  sinkAckSupported?: boolean;
  /** Timeout before an un-acked barge-in degrades to `stopped_unconfirmed` (default: 350 ms). */
  clearAckTimeoutMs?: number;
  autoPace?: boolean;
  clock?: () => number;
  silenceMs?: number;
  speechThreshold?: number;
}

interface PendingHalt {
  interruptedEpoch: number;
  newEpoch: number;
  t1BargeInOnsetMs: number;
  pacerFlushedAtMs: number;
  flushedFrames: number;
  timer: NodeJS.Timeout | null;
  resolved: boolean;
}

const MAGIC_O = 0x4f; // 'O'
const MAGIC_M = 0x4d; // 'M'
const MAX_AUDIO_APPEND_BYTES = 16 * 1024;
const MAX_CAPTURE_DURATION_SEC = 45;

export class RealtimeDuplexSession {
  readonly sessionId: string;
  private codec: RealtimeAudioCodec;
  private sampleRate: 8000 | 16000;
  private sinkAckSupported: boolean;
  private readonly clearAckTimeoutMs: number;
  private readonly clock: () => number;

  readonly jitterBuffer: BoundedJitterBuffer;
  readonly pacer: OutboundAudioPacer;
  private readonly detector: UtteranceDetector;

  private inboundSeqAuto = 0;
  private captureChunks: Int16Array[] = [];
  private capturedSamples = 0;
  private capturing = false;
  private closed = false;

  private activeTelemetry: TurnLatencyTelemetry | null = null;
  private readonly completedTelemetry: TurnLatencyTelemetry[] = [];
  private pendingHalt: PendingHalt | null = null;
  private lastBargeInResult: {
    t1Ms: number;
    t2Ms: number | null;
    status: HaltConfirmationStatus;
  } | null = null;
  private readonly unsubscribers: Array<() => void> = [];

  constructor(private readonly options: RealtimeDuplexSessionOptions) {
    this.sessionId = options.sessionId ?? newId("rts");
    this.codec = options.codec ?? "pcm16";
    this.sampleRate = this.codec === "pcm16" ? (options.sampleRate ?? 16000) : 8000;
    this.sinkAckSupported = options.sinkAckSupported ?? true;
    this.clearAckTimeoutMs = options.clearAckTimeoutMs ?? 350;
    this.clock = options.clock ?? (() => performance.now());

    this.jitterBuffer = new BoundedJitterBuffer({
      maxDepthFrames: 24,
      reorderWindowFrames: 2,
      frameSamples: Math.round((this.sampleRate * 20) / 1000),
    });

    this.detector = new UtteranceDetector({
      threshold: options.speechThreshold ?? 0.02,
      silenceMs: options.silenceMs ?? 500,
      minSpeechMs: 160,
      frameMs: 20,
    });

    this.pacer = new OutboundAudioPacer({
      sink: {
        get bufferedAmount() {
          return options.sink.bufferedAmount ?? 0;
        },
        sendAudioFrame: (bytes, meta) => {
          options.sink.sendBinaryAudio(bytes, meta);
        },
      },
      codec: this.codec,
      sampleRate: this.sampleRate,
      getTurnEpoch: () => this.options.engine.turnEpoch,
      onFirstFrameForEpoch: (epoch, atMs) => this.recordT6FirstAudioFrame(epoch, atMs),
      clock: this.clock,
      ...(options.autoPace !== undefined ? { autoTimer: options.autoPace } : {}),
    });

    this.wireEngineEvents();
  }

  get turnEpoch(): number {
    return this.options.engine.turnEpoch;
  }

  get isOutputActive(): boolean {
    return this.options.engine.isSpeaking || this.pacer.pendingFrames > 0;
  }

  async start(): Promise<void> {
    this.options.sink.sendJson({
      type: "session.ready",
      sessionId: this.sessionId,
      callId: this.options.engine.call.id,
      agentId: this.options.engine.call.agentId ?? null,
      codec: this.codec,
      sampleRate: this.sampleRate,
      sinkAckSupported: this.sinkAckSupported,
      turnEpoch: this.options.engine.turnEpoch,
    });
    await this.options.engine.start();
  }

  /**
   * Handles an inbound binary RFC 6455 frame or RTP payload:
   *  - Optional 4-byte `"OM" + uint16BE seq` header for sequenced WS frames, OR
   *  - Raw `PCM16` / `PCMU` / `PCMA` bytes using auto-incrementing sequence.
   */
  handleBinaryFrame(raw: Uint8Array, explicitSeq?: number): void {
    if (this.closed) return;
    let seq: number;
    let payload: Uint8Array;

    if (
      explicitSeq === undefined &&
      raw.byteLength > 4 &&
      raw[0] === MAGIC_O &&
      raw[1] === MAGIC_M
    ) {
      seq = ((raw[2] ?? 0) << 8) | (raw[3] ?? 0);
      payload = raw.subarray(4);
    } else {
      seq = explicitSeq !== undefined ? explicitSeq & 0xffff : this.inboundSeqAuto;
      this.inboundSeqAuto = (this.inboundSeqAuto + 1) & 0xffff;
      payload = raw;
    }

    const pcm = this.decodeInboundFrame(payload);
    this.jitterBuffer.push(seq, pcm);

    const ready = this.jitterBuffer.drainReady(false);
    for (const item of ready) {
      if (item.kind !== "silence") {
        this.processOrderedPcmFrame(item.samples);
      }
    }
  }

  /** Handles an inbound JSON control message over WebSocket or WebRTC DataChannel. */
  async handleControlMessage(rawText: string | Record<string, unknown>): Promise<void> {
    if (this.closed) return;
    let msg: Record<string, unknown>;
    if (typeof rawText === "string") {
      try {
        msg = JSON.parse(rawText) as Record<string, unknown>;
      } catch {
        this.options.sink.sendJson({ type: "error", code: "invalid_json", message: "Malformed JSON control frame" });
        return;
      }
    } else {
      msg = rawText;
    }

    const type = String(msg.type ?? "");
    switch (type) {
      case "session.configure": {
        const nextCodec = msg.codec === "pcmu" || msg.codec === "pcma" || msg.codec === "pcm16"
          ? msg.codec
          : this.codec;
        const nextRate: 8000 | 16000 =
          nextCodec === "pcm16" && msg.sampleRate === 8000 ? 8000 : nextCodec === "pcm16" ? 16000 : 8000;
        if (typeof msg.sinkAckSupported === "boolean") {
          this.sinkAckSupported = msg.sinkAckSupported;
        }
        if (msg.unacknowledgedTrunk === true) {
          this.sinkAckSupported = false;
        }
        this.codec = nextCodec;
        this.sampleRate = nextRate;
        this.pacer.configure(nextCodec, nextRate);
        this.jitterBuffer.setFrameSamples(Math.round((nextRate * 20) / 1000));
        this.options.sink.sendJson({
          type: "session.configured",
          codec: this.codec,
          sampleRate: this.sampleRate,
          sinkAckSupported: this.sinkAckSupported,
          turnEpoch: this.turnEpoch,
        });
        return;
      }

      case "audio.append": {
        if (typeof msg.payload === "string") {
          if (msg.payload.length > Math.ceil((MAX_AUDIO_APPEND_BYTES * 4) / 3) + 16) {
            this.options.sink.sendJson({
              type: "error",
              code: "frame_too_large",
              message: "audio.append payload exceeds 16 KiB limit",
            });
            return;
          }
          const bytes = Uint8Array.from(Buffer.from(msg.payload, "base64"));
          if (bytes.byteLength > MAX_AUDIO_APPEND_BYTES) {
            this.options.sink.sendJson({
              type: "error",
              code: "frame_too_large",
              message: "audio.append payload exceeds 16 KiB limit",
            });
            return;
          }
          const seq = typeof msg.seq === "number" ? msg.seq : undefined;
          this.handleBinaryFrame(bytes, seq);
        }
        return;
      }

      case "audio.commit": {
        for (const item of this.jitterBuffer.drainReady(true)) {
          if (item.kind !== "silence") this.processOrderedPcmFrame(item.samples);
        }
        await this.commitCapturedAudio();
        return;
      }

      case "barge_in": {
        this.triggerBargeIn("explicit_client");
        return;
      }

      case "clear.ack": {
        if (typeof msg.turnEpoch !== "number" || !Number.isFinite(msg.turnEpoch)) {
          this.options.sink.sendJson({
            type: "error",
            code: "invalid_epoch",
            message: "clear.ack requires explicit numeric turnEpoch",
          });
          return;
        }
        this.handleSinkClearAck(msg.turnEpoch);
        return;
      }

      case "utterance.text": {
        const text = typeof msg.text === "string" ? msg.text.trim() : "";
        if (!text) return;
        if (this.isOutputActive) {
          this.triggerBargeIn("utterance_text");
        }
        const t0 = this.clock();
        this.beginTurnTelemetry(t0);
        this.recordT3PartialStt(text.slice(0, Math.max(1, Math.floor(text.length / 2))), this.clock());
        this.recordT4FinalStt(text, this.clock());
        await this.options.engine.handleCallerUtterance(text);
        return;
      }

      case "dtmf": {
        const digit = typeof msg.digit === "string" ? msg.digit : "";
        if (digit) {
          this.options.engine.call.metadata.lastDtmf = digit;
          this.options.sink.sendJson({ type: "dtmf.received", digit });
        }
        return;
      }

      case "ping": {
        this.options.sink.sendJson({ type: "pong", ts: msg.ts ?? Date.now() });
        return;
      }

      default:
        this.options.sink.sendJson({
          type: "error",
          code: "unknown_event",
          message: `Unsupported realtime control event: ${type}`,
        });
    }
  }

  /**
   * Executes atomic barge-in:
   *  1. Records `T1` (`t1BargeInOnsetMs`).
   *  2. Atomically increments `engine.turnEpoch` (`engine.interrupt()`), causing
   *     all in-flight LLM/TTS operations and stale `OutboundAudioPacer` chunks to drop.
   *  3. Flushes `OutboundAudioPacer` queue immediately.
   *  4. Sends `{ type: "audio.clear", turnEpoch }` to the sink.
   *  5. Enforces `OM-T8`: waits for sink `clear.ack` before recording `observed_audio_halt`,
   *     or records `stopped_unconfirmed` immediately when `sinkAckSupported === false`
   *     (unacknowledged PSTN/SIP trunk) or upon ACK timeout!
   */
  triggerBargeIn(source: string): number {
    const t1 = this.clock();
    const interruptedEpoch = this.options.engine.turnEpoch;
    const newEpoch = this.options.engine.interrupt();
    const { flushedFrames, flushedAtMs } = this.pacer.flushForBargeIn();

    if (this.pendingHalt?.timer) {
      clearTimeout(this.pendingHalt.timer);
    }

    this.options.sink.sendJson({
      type: "audio.clear",
      turnEpoch: newEpoch,
      interruptedEpoch,
      flushedFrames,
      source,
    });

    if (!this.sinkAckSupported) {
      // OM-T8: PSTN / unacknowledged trunks cannot confirm speaker halt!
      this.lastBargeInResult = {
        t1Ms: t1,
        t2Ms: flushedAtMs,
        status: "stopped_unconfirmed",
      };
      this.applyBargeInToActiveTelemetry();
      this.options.sink.sendJson({
        type: "barge_in.halt",
        turnEpoch: newEpoch,
        t1BargeInOnsetMs: roundMs(t1),
        t2AudioHaltMs: roundMs(flushedAtMs),
        t2HaltStatus: "stopped_unconfirmed",
        bargeInHaltMs: roundMs(flushedAtMs - t1),
      });
      return newEpoch;
    }

    const pending: PendingHalt = {
      interruptedEpoch,
      newEpoch,
      t1BargeInOnsetMs: t1,
      pacerFlushedAtMs: flushedAtMs,
      flushedFrames,
      timer: null,
      resolved: false,
    };

    pending.timer = setTimeout(() => {
      if (pending.resolved || this.closed) return;
      pending.resolved = true;
      const fallbackAt = this.clock();
      this.lastBargeInResult = {
        t1Ms: pending.t1BargeInOnsetMs,
        t2Ms: fallbackAt,
        status: "stopped_unconfirmed",
      };
      this.applyBargeInToActiveTelemetry();
      this.options.sink.sendJson({
        type: "barge_in.halt",
        turnEpoch: pending.newEpoch,
        t1BargeInOnsetMs: roundMs(pending.t1BargeInOnsetMs),
        t2AudioHaltMs: roundMs(fallbackAt),
        t2HaltStatus: "stopped_unconfirmed",
        bargeInHaltMs: roundMs(fallbackAt - pending.t1BargeInOnsetMs),
      });
    }, this.clearAckTimeoutMs);
    pending.timer.unref?.();

    this.pendingHalt = pending;
    this.lastBargeInResult = {
      t1Ms: t1,
      t2Ms: null,
      status: "pending_sink_ack",
    };
    this.applyBargeInToActiveTelemetry();
    return newEpoch;
  }

  handleSinkClearAck(ackEpoch: number): void {
    const pending = this.pendingHalt;
    if (!pending || pending.resolved) return;
    if (!Number.isFinite(ackEpoch) || ackEpoch !== pending.newEpoch) {
      return;
    }
    pending.resolved = true;
    if (pending.timer) {
      clearTimeout(pending.timer);
      pending.timer = null;
    }
    const t2 = Math.max(pending.pacerFlushedAtMs, this.clock());
    this.lastBargeInResult = {
      t1Ms: pending.t1BargeInOnsetMs,
      t2Ms: t2,
      status: "observed_audio_halt",
    };
    this.applyBargeInToActiveTelemetry();
    this.persistTelemetryOnCall();

    this.options.sink.sendJson({
      type: "barge_in.halt",
      turnEpoch: pending.newEpoch,
      t1BargeInOnsetMs: roundMs(pending.t1BargeInOnsetMs),
      t2AudioHaltMs: roundMs(t2),
      t2HaltStatus: "observed_audio_halt",
      bargeInHaltMs: roundMs(t2 - pending.t1BargeInOnsetMs),
    });
  }

  telemetrySnapshot(): {
    sessionId: string;
    callId: string;
    turnEpoch: number;
    codec: RealtimeAudioCodec;
    sampleRate: number;
    jitter: JitterBufferStats;
    pacer: PacerStats;
    activeTurn: TurnLatencyTelemetry | null;
    turns: TurnLatencyTelemetry[];
  } {
    return {
      sessionId: this.sessionId,
      callId: this.options.engine.call.id,
      turnEpoch: this.turnEpoch,
      codec: this.codec,
      sampleRate: this.sampleRate,
      jitter: this.jitterBuffer.stats(),
      pacer: this.pacer.stats(),
      activeTurn: this.activeTelemetry ? structuredClone(this.activeTelemetry) : null,
      turns: structuredClone(this.completedTelemetry),
    };
  }

  async close(reason: "customer_ended" | "assistant_ended" = "customer_ended"): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    if (this.pendingHalt?.timer) {
      clearTimeout(this.pendingHalt.timer);
      this.pendingHalt.timer = null;
    }
    this.pacer.close();
    for (const unsub of this.unsubscribers) unsub();
    this.unsubscribers.length = 0;
    if (!this.options.engine.isEnded) {
      await this.options.engine.end(reason);
    }
  }

  /* ------------------------------------------------------------------ */

  private wireEngineEvents(): void {
    this.unsubscribers.push(
      this.options.engine.on("caller.transcript", () => {
        if (this.activeTelemetry) {
          this.activeTelemetry.turnEpoch = this.turnEpoch;
        }
      }),
      this.options.engine.on("assistant.first_token", () => {
        this.recordT5FirstToken(this.clock());
      }),
      this.options.engine.on("assistant.delta", ({ text }) => {
        this.options.sink.sendJson({
          type: "assistant.delta",
          text,
          turnEpoch: this.turnEpoch,
        });
      }),
      this.options.engine.on("assistant.audio", ({ audio, text, turnEpoch }) => {
        const queued = this.pacer.enqueueAudio(audio, turnEpoch);
        if (queued > 0) {
          this.options.sink.sendJson({
            type: "assistant.audio.queued",
            text,
            queuedFrames: queued,
            turnEpoch,
          });
        }
      }),
      this.options.engine.on("assistant.speech", ({ text, interrupted }) => {
        this.options.sink.sendJson({
          type: "assistant.speech",
          text,
          interrupted,
          turnEpoch: this.turnEpoch,
        });
      }),
      this.options.engine.on("call.ended", ({ reason }) => {
        this.pacer.close();
        this.options.sink.sendJson({ type: "session.ended", reason });
      }),
    );
  }

  private processOrderedPcmFrame(samples: Int16Array): void {
    const energy = speechEnergy(samples);
    if (energy >= 0.012 && this.isOutputActive) {
      // Early barge-in ducking on voice onset before full speech confirmation
      this.pacer.setDuckGain(0.22);
    } else if (energy < 0.008 && !this.detector.isVoiced) {
      this.pacer.setDuckGain(1.0);
    }

    const vad = this.detector.push(samples);
    if (vad === "speech") {
      this.options.engine.notifyCallerActivity();
      if (this.isOutputActive && this.options.engine.call.agentId !== undefined) {
        this.triggerBargeIn("vad_speech");
      }
      if (!this.capturing) {
        this.capturing = true;
      }
      this.captureChunks.push(samples);
      this.capturedSamples += samples.length;
    } else if (this.capturing && this.detector.isVoiced) {
      this.captureChunks.push(samples);
      this.capturedSamples += samples.length;
    }

    const maxCaptureSamples = this.sampleRate * MAX_CAPTURE_DURATION_SEC;
    if (vad === "final" || this.capturedSamples >= maxCaptureSamples) {
      void this.commitCapturedAudio();
    }
  }

  private async commitCapturedAudio(): Promise<void> {
    if (this.capturedSamples === 0) return;
    const total = this.capturedSamples;
    const chunks = this.captureChunks;
    this.captureChunks = [];
    this.capturedSamples = 0;
    this.capturing = false;
    this.detector.reset();
    this.pacer.setDuckGain(1.0);

    const combined = new Int16Array(total);
    let offset = 0;
    for (const c of chunks) {
      combined.set(c, offset);
      offset += c.length;
    }

    const t0 = this.clock();
    this.beginTurnTelemetry(t0);

    const wav = encodeWav(pcm16ToBytes(combined), {
      sampleRate: this.sampleRate,
      channels: 1,
      bitDepth: 16,
    });

    const partialAt = this.clock();
    const result = await this.options.stt.transcribe(wav, {
      mimeType: "audio/wav",
      ...(this.options.language ? { language: this.options.language } : {}),
    });
    const text = result.text.trim();
    if (!text) return;

    this.recordT3PartialStt(text.split(/\s+/)[0] ?? text, partialAt);
    this.recordT4FinalStt(text, this.clock());
    await this.options.engine.handleCallerUtterance(text);
  }

  private beginTurnTelemetry(t0SpeechEndMs: number): void {
    const barge = this.lastBargeInResult;
    this.activeTelemetry = {
      turnId: newId("tlm"),
      turnEpoch: this.turnEpoch,
      t0SpeechEndMs: roundMs(t0SpeechEndMs),
      t1BargeInOnsetMs: barge ? roundMs(barge.t1Ms) : null,
      t2AudioHaltMs: barge?.t2Ms !== null && barge?.t2Ms !== undefined ? roundMs(barge.t2Ms) : null,
      t2HaltStatus: barge ? barge.status : "not_applicable",
      t3PartialSttMs: null,
      t4FinalSttMs: null,
      t5FirstTokenMs: null,
      t6FirstAudioFrameMs: null,
      deltasMs: {
        bargeInHaltMs:
          barge && barge.t2Ms !== null ? roundMs(barge.t2Ms - barge.t1Ms) : null,
        sttFinalMs: null,
        llmFirstTokenMs: null,
        ttsFirstFrameFromSpeechEndMs: null,
      },
    };
    this.lastBargeInResult = null;
  }

  private applyBargeInToActiveTelemetry(): void {
    const barge = this.lastBargeInResult;
    if (!barge) return;
    if (this.activeTelemetry) {
      this.activeTelemetry.t1BargeInOnsetMs = roundMs(barge.t1Ms);
      this.activeTelemetry.t2AudioHaltMs = barge.t2Ms !== null ? roundMs(barge.t2Ms) : null;
      this.activeTelemetry.t2HaltStatus = barge.status;
      this.activeTelemetry.deltasMs.bargeInHaltMs =
        barge.t2Ms !== null ? roundMs(barge.t2Ms - barge.t1Ms) : null;
    }
    const lastCompleted = this.completedTelemetry[this.completedTelemetry.length - 1];
    if (lastCompleted && (!this.activeTelemetry || lastCompleted.turnId === this.activeTelemetry.turnId || lastCompleted.t2HaltStatus === "pending_sink_ack")) {
      lastCompleted.t1BargeInOnsetMs = roundMs(barge.t1Ms);
      lastCompleted.t2AudioHaltMs = barge.t2Ms !== null ? roundMs(barge.t2Ms) : null;
      lastCompleted.t2HaltStatus = barge.status;
      lastCompleted.deltasMs.bargeInHaltMs =
        barge.t2Ms !== null ? roundMs(barge.t2Ms - barge.t1Ms) : null;
    }
  }

  private recordT3PartialStt(partialText: string, atMs: number): void {
    if (this.activeTelemetry && this.activeTelemetry.t3PartialSttMs === null) {
      this.activeTelemetry.t3PartialSttMs = roundMs(atMs);
    }
    this.options.sink.sendJson({
      type: "stt.partial",
      text: partialText,
      atMs: roundMs(atMs),
      turnEpoch: this.turnEpoch,
    });
  }

  private recordT4FinalStt(finalText: string, atMs: number): void {
    if (this.activeTelemetry) {
      this.activeTelemetry.t4FinalSttMs = roundMs(atMs);
      if (this.activeTelemetry.t0SpeechEndMs !== null) {
        this.activeTelemetry.deltasMs.sttFinalMs = roundMs(atMs - this.activeTelemetry.t0SpeechEndMs);
      }
    }
    this.options.sink.sendJson({
      type: "stt.final",
      text: finalText,
      atMs: roundMs(atMs),
      turnEpoch: this.turnEpoch,
    });
  }

  private recordT5FirstToken(atMs: number): void {
    if (this.activeTelemetry && this.activeTelemetry.t5FirstTokenMs === null) {
      this.activeTelemetry.t5FirstTokenMs = roundMs(atMs);
      if (this.activeTelemetry.t4FinalSttMs !== null) {
        this.activeTelemetry.deltasMs.llmFirstTokenMs = roundMs(atMs - this.activeTelemetry.t4FinalSttMs);
      }
    }
    this.options.sink.sendJson({
      type: "llm.first_token",
      atMs: roundMs(atMs),
      turnEpoch: this.turnEpoch,
    });
  }

  private recordT6FirstAudioFrame(epoch: number, atMs: number): void {
    if (this.activeTelemetry && this.activeTelemetry.turnEpoch === epoch) {
      this.activeTelemetry.t6FirstAudioFrameMs = roundMs(atMs);
      if (this.activeTelemetry.t0SpeechEndMs !== null) {
        this.activeTelemetry.deltasMs.ttsFirstFrameFromSpeechEndMs = roundMs(
          atMs - this.activeTelemetry.t0SpeechEndMs,
        );
      }
      const finalized = structuredClone(this.activeTelemetry);
      this.completedTelemetry.push(finalized);
      this.persistTelemetryOnCall();
      this.options.sink.sendJson({
        type: "telemetry.latency",
        telemetry: finalized,
      });
    } else {
      this.options.sink.sendJson({
        type: "tts.first_frame",
        turnEpoch: epoch,
        atMs: roundMs(atMs),
      });
    }
  }

  private persistTelemetryOnCall(): void {
    this.options.engine.call.metadata.realtimeLatency = structuredClone(
      this.completedTelemetry,
    ) as unknown as import("@omalla/core").JsonValue;
  }

  private decodeInboundFrame(bytes: Uint8Array): Int16Array {
    switch (this.codec) {
      case "pcmu": {
        const pcm8k = decodeMulaw(bytes);
        return resamplePcm16(pcm8k, 8000, this.sampleRate);
      }
      case "pcma": {
        const pcm8k = decodeAlaw(bytes);
        return resamplePcm16(pcm8k, 8000, this.sampleRate);
      }
      case "pcm16":
        return pcm16FromBytes(bytes);
    }
  }
}

function roundMs(val: number): number {
  return Math.round(val * 100) / 100;
}
