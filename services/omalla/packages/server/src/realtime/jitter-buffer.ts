/**
 * Bounded Inbound Jitter Buffer with sequence reordering, duplicate/late drop,
 * max-depth overflow protection, and attenuated Packet Loss Concealment (PLC).
 */

export interface JitterBufferOptions {
  /** Maximum queued frames before oldest frames are shed (default: 24 = 480 ms at 20 ms/frame). */
  maxDepthFrames?: number;
  /** Minimum queued frames before advancing past a missing sequence via PLC (default: 2). */
  reorderWindowFrames?: number;
  /** Samples per 20 ms frame (default: 160 for 8 kHz, 320 for 16 kHz). */
  frameSamples?: number;
  /** Maximum consecutive concealed frames before decaying to pure silence (default: 4 = 80 ms). */
  maxPlcFrames?: number;
  /** Per-frame attenuation multiplier during PLC (default: 0.7). */
  plcDecay?: number;
}

export interface JitterPushResult {
  accepted: boolean;
  reordered: boolean;
  reason?: "duplicate" | "too_late" | "overflow_dropped_oldest";
}

export interface JitterPopResult {
  samples: Int16Array;
  kind: "normal" | "plc" | "silence";
  sequenceNumber: number | null;
}

export interface JitterBufferStats {
  queuedFrames: number;
  receivedCount: number;
  reorderedCount: number;
  duplicateCount: number;
  lateDropCount: number;
  overflowDropCount: number;
  plcCount: number;
  nextExpectedSeq: number | null;
}

/** Signed 16-bit RTP sequence delta (`a - b` in `[-32768, 32767]`). */
export function signedSeqDelta(a: number, b: number): number {
  const diff = ((a & 0xffff) - (b & 0xffff) + 0x10000) & 0xffff;
  return diff >= 0x8000 ? diff - 0x10000 : diff;
}

export class BoundedJitterBuffer {
  private readonly maxDepthFrames: number;
  private readonly reorderWindowFrames: number;
  private frameSamples: number;
  private readonly maxPlcFrames: number;
  private readonly plcDecay: number;

  private readonly queue = new Map<number, Int16Array>();
  private nextExpectedSeq: number | null = null;
  private lastGoodFrame: Int16Array | null = null;
  private consecutivePlc = 0;

  private receivedCount = 0;
  private reorderedCount = 0;
  private duplicateCount = 0;
  private lateDropCount = 0;
  private overflowDropCount = 0;
  private plcCount = 0;

  constructor(options: JitterBufferOptions = {}) {
    this.maxDepthFrames = Math.max(2, options.maxDepthFrames ?? 24);
    this.reorderWindowFrames = Math.max(1, options.reorderWindowFrames ?? 2);
    this.frameSamples = Math.max(1, options.frameSamples ?? 160);
    this.maxPlcFrames = Math.max(1, options.maxPlcFrames ?? 4);
    this.plcDecay = options.plcDecay ?? 0.7;
  }

  setFrameSamples(samples: number): void {
    if (samples > 0) this.frameSamples = samples;
  }

  push(sequenceNumber: number, samples: Int16Array): JitterPushResult {
    const seq = sequenceNumber & 0xffff;
    this.receivedCount += 1;
    if (samples.length > 0 && samples.length !== this.frameSamples) {
      this.frameSamples = samples.length;
    }

    if (this.nextExpectedSeq === null) {
      this.nextExpectedSeq = seq;
    }

    const deltaFromExpected = signedSeqDelta(seq, this.nextExpectedSeq);
    if (deltaFromExpected < 0) {
      this.lateDropCount += 1;
      return { accepted: false, reordered: false, reason: "too_late" };
    }

    if (this.queue.has(seq)) {
      this.duplicateCount += 1;
      return { accepted: false, reordered: false, reason: "duplicate" };
    }

    const reordered = deltaFromExpected > 0 && this.queue.size > 0;
    if (reordered) {
      this.reorderedCount += 1;
    } else if (deltaFromExpected > 0 && this.queue.size === 0) {
      // Arrived ahead of expected sequence (gap detected)
      this.reorderedCount += 1;
    }

    this.queue.set(seq, Int16Array.from(samples));

    if (this.queue.size > this.maxDepthFrames) {
      this.dropOldest();
      return { accepted: true, reordered, reason: "overflow_dropped_oldest" };
    }

    return { accepted: true, reordered };
  }

  /**
   * Pops the next playout frame:
   *  - Exact match for `nextExpectedSeq` -> `"normal"`
   *  - Missing `nextExpectedSeq` when `forceConceal` is true OR queued frames
   *    exceed `reorderWindowFrames` -> `"plc"` (attenuated continuation)
   *  - Empty/waiting within reorder window -> `"silence"` without advancing `nextExpectedSeq`
   */
  pop(forceConceal = false): JitterPopResult {
    if (this.nextExpectedSeq === null) {
      return {
        samples: new Int16Array(this.frameSamples),
        kind: "silence",
        sequenceNumber: null,
      };
    }

    const exact = this.queue.get(this.nextExpectedSeq);
    if (exact) {
      const seq = this.nextExpectedSeq;
      this.queue.delete(seq);
      this.nextExpectedSeq = (seq + 1) & 0xffff;
      this.lastGoodFrame = exact;
      this.consecutivePlc = 0;
      return {
        samples: exact,
        kind: "normal",
        sequenceNumber: seq,
      };
    }

    if (this.queue.size > 0 && (forceConceal || this.queue.size >= this.reorderWindowFrames)) {
      const missingSeq = this.nextExpectedSeq;
      this.nextExpectedSeq = (missingSeq + 1) & 0xffff;
      this.consecutivePlc += 1;
      this.plcCount += 1;
      return {
        samples: this.synthesizePlcFrame(),
        kind: "plc",
        sequenceNumber: missingSeq,
      };
    }

    if (forceConceal && this.lastGoodFrame && this.consecutivePlc < this.maxPlcFrames) {
      const missingSeq = this.nextExpectedSeq;
      this.nextExpectedSeq = (missingSeq + 1) & 0xffff;
      this.consecutivePlc += 1;
      this.plcCount += 1;
      return {
        samples: this.synthesizePlcFrame(),
        kind: "plc",
        sequenceNumber: missingSeq,
      };
    }

    return {
      samples: new Int16Array(this.frameSamples),
      kind: "silence",
      sequenceNumber: null,
    };
  }

  /** Drains all currently playable frames in monotonic sequence order, concealing gaps. */
  drainReady(concealGaps = false): JitterPopResult[] {
    const out: JitterPopResult[] = [];
    while (this.queue.size > 0) {
      if (this.nextExpectedSeq !== null && this.queue.has(this.nextExpectedSeq)) {
        out.push(this.pop(false));
        continue;
      }
      if (concealGaps || this.queue.size >= this.reorderWindowFrames) {
        out.push(this.pop(true));
        continue;
      }
      break;
    }
    return out;
  }

  reset(): void {
    this.queue.clear();
    this.nextExpectedSeq = null;
    this.lastGoodFrame = null;
    this.consecutivePlc = 0;
  }

  stats(): JitterBufferStats {
    return {
      queuedFrames: this.queue.size,
      receivedCount: this.receivedCount,
      reorderedCount: this.reorderedCount,
      duplicateCount: this.duplicateCount,
      lateDropCount: this.lateDropCount,
      overflowDropCount: this.overflowDropCount,
      plcCount: this.plcCount,
      nextExpectedSeq: this.nextExpectedSeq,
    };
  }

  private dropOldest(): void {
    if (this.queue.size === 0 || this.nextExpectedSeq === null) return;
    let oldestSeq: number | null = null;
    let minDelta = Infinity;
    for (const seq of this.queue.keys()) {
      const d = signedSeqDelta(seq, this.nextExpectedSeq);
      if (d < minDelta) {
        minDelta = d;
        oldestSeq = seq;
      }
    }
    if (oldestSeq !== null) {
      this.queue.delete(oldestSeq);
      this.overflowDropCount += 1;
      // Advance expected pointer past dropped frame so playout never stalls on it
      if (signedSeqDelta(oldestSeq, this.nextExpectedSeq) >= 0) {
        this.nextExpectedSeq = (oldestSeq + 1) & 0xffff;
      }
    }
  }

  private synthesizePlcFrame(): Int16Array {
    const out = new Int16Array(this.frameSamples);
    if (!this.lastGoodFrame || this.consecutivePlc > this.maxPlcFrames) {
      return out;
    }
    const factor = Math.pow(this.plcDecay, this.consecutivePlc);
    const len = Math.min(out.length, this.lastGoodFrame.length);
    for (let i = 0; i < len; i += 1) {
      // Smoothly cross-fade tail to avoid clicks
      const fade = 1 - (i / len) * 0.25;
      out[i] = Math.round((this.lastGoodFrame[i] ?? 0) * factor * fade);
    }
    return out;
  }
}
