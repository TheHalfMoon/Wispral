/**
 * 20 ms Paced Outbound Audio Queue with socket backpressure watermarks,
 * barge-in gain ducking, instant queue flush, atomic `turnEpoch` stale-chunk
 * drop, and exact `T6` first-audio-frame telemetry callback.
 */
import type { SynthesizedAudio } from "@omalla/core";
import {
  decodeAlaw,
  decodeMulaw,
  decodeWav,
  encodeAlaw,
  encodeMulaw,
  pcm16FromBytes,
  pcm16ToBytes,
  resamplePcm16,
} from "@omalla/telephony";

export type RealtimeAudioCodec = "pcm16" | "pcmu" | "pcma";

export interface PacerSink {
  /** Bytes currently buffered on the underlying socket (`ws.bufferedAmount`). */
  readonly bufferedAmount?: number;
  sendAudioFrame(frameBytes: Uint8Array, meta: { seq: number; timestamp: number; turnEpoch: number; codec: RealtimeAudioCodec }): void;
}

export interface OutboundAudioPacerOptions {
  sink: PacerSink;
  codec?: RealtimeAudioCodec;
  sampleRate?: 8000 | 16000;
  frameIntervalMs?: number;
  /** Pause sending when socket bufferedAmount exceeds highWatermarkBytes (default: 32 KiB). */
  highWatermarkBytes?: number;
  /** Shed queued frames when socket bufferedAmount exceeds criticalWatermarkBytes (default: 128 KiB). */
  criticalWatermarkBytes?: number;
  /** Maximum queued 20 ms frames per session (default: 600 = 12 s). */
  maxQueueFrames?: number;
  getTurnEpoch: () => number;
  onFirstFrameForEpoch?: (turnEpoch: number, atMs: number) => void;
  clock?: () => number;
  /** Set false in deterministic manual-tick unit tests if desired (defaults to true). */
  autoTimer?: boolean;
}

interface QueuedFrame {
  pcmSamples: Int16Array;
  turnEpoch: number;
}

export interface PacerStats {
  queuedFrames: number;
  sentFrames: number;
  staleEpochDrops: number;
  flushedFrames: number;
  backpressurePauses: number;
  backpressureDrops: number;
  duckGain: number;
}

export class OutboundAudioPacer {
  private codec: RealtimeAudioCodec;
  private sampleRate: 8000 | 16000;
  private readonly frameIntervalMs: number;
  private readonly highWatermarkBytes: number;
  private readonly criticalWatermarkBytes: number;
  private readonly maxQueueFrames: number;
  private readonly clock: () => number;

  private readonly queue: QueuedFrame[] = [];
  private readonly firstFrameEmittedEpochs = new Set<number>();
  private timer: NodeJS.Timeout | null = null;
  private closed = false;
  private duckGain = 1.0;
  private txSeq = 0;
  private txTimestamp = 0;

  private sentFrames = 0;
  private staleEpochDrops = 0;
  private flushedFrames = 0;
  private backpressurePauses = 0;
  private backpressureDrops = 0;

  constructor(private readonly options: OutboundAudioPacerOptions) {
    this.codec = options.codec ?? "pcm16";
    this.sampleRate = this.codec === "pcm16" ? (options.sampleRate ?? 16000) : 8000;
    this.frameIntervalMs = Math.max(5, options.frameIntervalMs ?? 20);
    this.highWatermarkBytes = options.highWatermarkBytes ?? 32_768;
    this.criticalWatermarkBytes = options.criticalWatermarkBytes ?? 131_072;
    this.maxQueueFrames = options.maxQueueFrames ?? 600;
    this.clock = options.clock ?? (() => performance.now());

    if (options.autoTimer !== false) {
      this.startTimer();
    }
  }

  configure(codec: RealtimeAudioCodec, sampleRate?: 8000 | 16000): void {
    this.codec = codec;
    this.sampleRate = codec === "pcm16" ? (sampleRate ?? 16000) : 8000;
  }

  get activeCodec(): RealtimeAudioCodec {
    return this.codec;
  }

  get activeSampleRate(): 8000 | 16000 {
    return this.sampleRate;
  }

  get pendingFrames(): number {
    return this.queue.length;
  }

  /** Attenuates outbound audio gain (`0.0 .. 1.0`) during speech-onset ducking. */
  setDuckGain(gain: number): void {
    this.duckGain = Math.max(0, Math.min(1, gain));
  }

  /**
   * Enqueues synthesized TTS audio split into exact 20 ms frames.
   * Immediately drops the entire chunk if `turnEpoch` is already stale!
   */
  enqueueAudio(audio: SynthesizedAudio, turnEpoch: number): number {
    if (this.closed) return 0;
    const currentEpoch = this.options.getTurnEpoch();
    if (turnEpoch !== currentEpoch) {
      const skipped = this.estimateFrameCount(audio);
      this.staleEpochDrops += Math.max(1, skipped);
      return 0;
    }

    const pcm = this.decodeToSessionPcm(audio);
    const samplesPerFrame = Math.round((this.sampleRate * this.frameIntervalMs) / 1000);
    let added = 0;

    for (let offset = 0; offset < pcm.length; offset += samplesPerFrame) {
      if (this.options.getTurnEpoch() !== turnEpoch) {
        this.staleEpochDrops += 1;
        continue;
      }
      const frame = new Int16Array(samplesPerFrame);
      frame.set(pcm.subarray(offset, Math.min(pcm.length, offset + samplesPerFrame)));
      if (this.queue.length >= this.maxQueueFrames) {
        this.queue.shift();
        this.backpressureDrops += 1;
      }
      this.queue.push({ pcmSamples: frame, turnEpoch });
      added += 1;
    }

    return added;
  }

  /**
   * Flushes all queued frames on barge-in and resets ducking.
   * Returns exact flushed frame count and monotonic timestamp.
   */
  flushForBargeIn(): { flushedFrames: number; flushedAtMs: number } {
    const count = this.queue.length;
    this.queue.length = 0;
    this.flushedFrames += count;
    this.duckGain = 1.0;
    return {
      flushedFrames: count,
      flushedAtMs: this.clock(),
    };
  }

  /** Executes one 20 ms pacer tick (called automatically by timer or manually in deterministic tests). */
  tick(): boolean {
    if (this.closed || this.queue.length === 0) return false;

    const currentEpoch = this.options.getTurnEpoch();

    // Purge any stale turnEpoch frames at the head of the queue before touching socket!
    while (this.queue.length > 0 && this.queue[0]!.turnEpoch !== currentEpoch) {
      this.queue.shift();
      this.staleEpochDrops += 1;
    }
    if (this.queue.length === 0) return false;

    const buffered = this.options.sink.bufferedAmount ?? 0;
    if (buffered >= this.criticalWatermarkBytes) {
      const shedCount = Math.max(1, Math.floor(this.queue.length / 2));
      this.queue.splice(0, shedCount);
      this.backpressureDrops += shedCount;
      this.backpressurePauses += 1;
      return false;
    }
    if (buffered >= this.highWatermarkBytes) {
      this.backpressurePauses += 1;
      return false;
    }

    const next = this.queue.shift();
    if (!next) return false;
    if (next.turnEpoch !== this.options.getTurnEpoch()) {
      this.staleEpochDrops += 1;
      return false;
    }

    const gained = this.applyGain(next.pcmSamples);
    const wireBytes = this.encodeWireFrame(gained);

    const seq = this.txSeq;
    const ts = this.txTimestamp;
    this.txSeq = (this.txSeq + 1) & 0xffff;
    this.txTimestamp = (this.txTimestamp + gained.length) >>> 0;
    this.sentFrames += 1;

    this.options.sink.sendAudioFrame(wireBytes, {
      seq,
      timestamp: ts,
      turnEpoch: next.turnEpoch,
      codec: this.codec,
    });

    const emittedAt = this.clock();
    if (!this.firstFrameEmittedEpochs.has(next.turnEpoch)) {
      this.firstFrameEmittedEpochs.add(next.turnEpoch);
      this.options.onFirstFrameForEpoch?.(next.turnEpoch, emittedAt);
    }
    return true;
  }

  stats(): PacerStats {
    return {
      queuedFrames: this.queue.length,
      sentFrames: this.sentFrames,
      staleEpochDrops: this.staleEpochDrops,
      flushedFrames: this.flushedFrames,
      backpressurePauses: this.backpressurePauses,
      backpressureDrops: this.backpressureDrops,
      duckGain: this.duckGain,
    };
  }

  close(): void {
    this.closed = true;
    this.queue.length = 0;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  private startTimer(): void {
    this.timer = setInterval(() => {
      this.tick();
    }, this.frameIntervalMs);
    this.timer.unref?.();
  }

  private applyGain(samples: Int16Array): Int16Array {
    if (this.duckGain >= 0.999) return samples;
    const out = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i += 1) {
      out[i] = Math.max(-32768, Math.min(32767, Math.round((samples[i] ?? 0) * this.duckGain)));
    }
    return out;
  }

  private encodeWireFrame(samples: Int16Array): Uint8Array {
    switch (this.codec) {
      case "pcmu":
        return encodeMulaw(samples);
      case "pcma":
        return encodeAlaw(samples);
      case "pcm16":
        return pcm16ToBytes(samples);
    }
  }

  private decodeToSessionPcm(audio: SynthesizedAudio): Int16Array {
    const mime = audio.mimeType.toLowerCase();
    if (mime.includes("wav")) {
      const decoded = decodeWav(audio.data);
      return resamplePcm16(decoded.samples, decoded.sampleRate, this.sampleRate);
    }
    if (mime.includes("mulaw") || mime.includes("pcmu")) {
      const pcm8k = decodeMulaw(audio.data);
      return resamplePcm16(pcm8k, 8000, this.sampleRate);
    }
    if (mime.includes("alaw") || mime.includes("pcma")) {
      const pcm8k = decodeAlaw(audio.data);
      return resamplePcm16(pcm8k, 8000, this.sampleRate);
    }
    const rateMatch = /rate=(\d+)/i.exec(audio.mimeType);
    const rawRate = rateMatch?.[1] ? Number(rateMatch[1]) : 16000;
    const pcm = pcm16FromBytes(audio.data);
    return resamplePcm16(pcm, rawRate, this.sampleRate);
  }

  private estimateFrameCount(audio: SynthesizedAudio): number {
    const frameBytes = this.codec === "pcm16" ? (this.sampleRate / 50) * 2 : 160;
    return Math.max(1, Math.ceil(audio.data.byteLength / frameBytes));
  }
}
