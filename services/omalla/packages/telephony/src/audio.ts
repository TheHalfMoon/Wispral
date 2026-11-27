/**
 * Telephone audio primitives.
 *
 * Twilio Media Streams carry 8 kHz mono G.711 μ-law in base64 frames, while
 * local voices (SAPI, OpenAI, Piper) return 16/24 kHz PCM WAV. Everything in
 * this file is pure, synchronous and deterministic so the conversion path is
 * unit-tested without a carrier, a socket or a sound card.
 */

export const TELEPHONE_SAMPLE_RATE = 8000;
/** 20 ms of 8 kHz μ-law: the frame size Twilio sends and expects. */
export const TELEPHONE_FRAME_BYTES = 160;

/* ------------------------------------------------------------------ */
/* G.711 μ-law                                                         */
/* ------------------------------------------------------------------ */

const MULAW_BIAS = 0x84;
const MULAW_CLIP = 32635;

/** Encodes one signed 16-bit PCM sample to an 8-bit μ-law byte. */
export function linearToMulaw(sample: number): number {
  let value = Math.max(-32768, Math.min(32767, Math.round(sample)));
  let sign = 0;
  if (value < 0) {
    value = -value;
    sign = 0x80;
  }
  if (value > MULAW_CLIP) value = MULAW_CLIP;
  value += MULAW_BIAS;

  let exponent = 7;
  for (let mask = 0x4000; exponent > 0 && (value & mask) === 0; mask >>= 1) {
    exponent -= 1;
  }
  const mantissa = (value >> (exponent + 3)) & 0x0f;
  return ~(sign | (exponent << 4) | mantissa) & 0xff;
}

/** Decodes one 8-bit μ-law byte to a signed 16-bit PCM sample. */
export function mulawToLinear(byte: number): number {
  const value = ~byte & 0xff;
  const sign = value & 0x80;
  const exponent = (value >> 4) & 0x07;
  const mantissa = value & 0x0f;
  let sample = ((mantissa << 3) + MULAW_BIAS) << exponent;
  sample -= MULAW_BIAS;
  return sign !== 0 ? -sample : sample;
}

export function encodeMulaw(samples: Int16Array): Uint8Array {
  const out = new Uint8Array(samples.length);
  for (let i = 0; i < samples.length; i += 1) {
    out[i] = linearToMulaw(samples[i] ?? 0);
  }
  return out;
}

export function decodeMulaw(bytes: Uint8Array): Int16Array {
  const out = new Int16Array(bytes.length);
  for (let i = 0; i < bytes.length; i += 1) {
    out[i] = mulawToLinear(bytes[i] ?? 0);
  }
  return out;
}

/* ------------------------------------------------------------------ */
/* PCM helpers                                                         */
/* ------------------------------------------------------------------ */

/** Reads little-endian PCM16 bytes into samples. Never assumes alignment. */
export function pcm16FromBytes(bytes: Uint8Array): Int16Array {
  const samples = new Int16Array(Math.floor(bytes.length / 2));
  for (let i = 0; i < samples.length; i += 1) {
    const lo = bytes[i * 2] ?? 0;
    const hi = bytes[i * 2 + 1] ?? 0;
    const value = (hi << 8) | lo;
    samples[i] = value >= 0x8000 ? value - 0x10000 : value;
  }
  return samples;
}

export function pcm16ToBytes(samples: Int16Array): Uint8Array {
  const out = new Uint8Array(samples.length * 2);
  for (let i = 0; i < samples.length; i += 1) {
    const value = samples[i] ?? 0;
    out[i * 2] = value & 0xff;
    out[i * 2 + 1] = (value >> 8) & 0xff;
  }
  return out;
}

/**
 * Linear-interpolation resampler.
 *
 * Deliberately simple: telephone speech is band-limited upstream and the
 * alternative (a polyphase filter) buys nothing at 8 kHz. For downsampling we
 * average each source window first so high frequencies do not fold back.
 */
export function resamplePcm16(samples: Int16Array, fromRate: number, toRate: number): Int16Array {
  if (fromRate <= 0 || toRate <= 0) throw new RangeError("sample rates must be positive");
  if (fromRate === toRate) return Int16Array.from(samples);
  const outLength = Math.max(0, Math.round((samples.length * toRate) / fromRate));
  const out = new Int16Array(outLength);
  if (samples.length === 0 || outLength === 0) return out;
  const ratio = fromRate / toRate;

  if (ratio > 1) {
    // Downsample: box filter over the source window, then interpolate between
    // adjacent window averages.
    const windows = Math.ceil(samples.length / ratio);
    const averaged = new Float64Array(windows);
    for (let w = 0; w < windows; w += 1) {
      const start = Math.floor(w * ratio);
      const end = Math.min(samples.length, Math.max(start + 1, Math.floor((w + 1) * ratio)));
      let sum = 0;
      for (let i = start; i < end; i += 1) sum += samples[i] ?? 0;
      averaged[w] = sum / (end - start);
    }
    for (let i = 0; i < outLength; i += 1) {
      const position = i * ratio;
      const index = Math.floor(position);
      const fraction = position - index;
      const a = averaged[index] ?? averaged[windows - 1] ?? 0;
      const b = averaged[index + 1] ?? a;
      out[i] = clampSample(a + (b - a) * fraction);
    }
    return out;
  }

  // Upsample: linear interpolation between neighbouring samples.
  for (let i = 0; i < outLength; i += 1) {
    const position = i * ratio;
    const index = Math.floor(position);
    const fraction = position - index;
    const a = samples[index] ?? samples[samples.length - 1] ?? 0;
    const b = samples[index + 1] ?? a;
    out[i] = clampSample(a + (b - a) * fraction);
  }
  return out;
}

/** Converts any PCM16 rate to the 8 kHz telephone rate. */
export function toTelephonePcm(samples: Int16Array, sampleRate: number): Int16Array {
  return resamplePcm16(samples, sampleRate, TELEPHONE_SAMPLE_RATE);
}

/* ------------------------------------------------------------------ */
/* WAV                                                                 */
/* ------------------------------------------------------------------ */

export interface DecodedWav {
  samples: Int16Array;
  sampleRate: number;
  channels: number;
  bitDepth: number;
}

/**
 * Minimal RIFF/WAVE reader for PCM. Chunks are walked rather than assuming a
 * 44-byte header: SAPI and ffmpeg both emit extra chunks in practice.
 */
export function decodeWav(wav: Uint8Array): DecodedWav {
  if (wav.length < 12) throw new Error("not a WAV file: too short");
  const view = new DataView(wav.buffer, wav.byteOffset, wav.byteLength);
  if (ascii(wav, 0, 4) !== "RIFF" || ascii(wav, 8, 4) !== "WAVE") {
    throw new Error("not a WAV file: missing RIFF/WAVE header");
  }

  let format: { audioFormat: number; channels: number; sampleRate: number; bitDepth: number } | null = null;
  let dataOffset = -1;
  let dataLength = 0;
  let offset = 12;

  while (offset + 8 <= wav.length) {
    const id = ascii(wav, offset, 4);
    const size = view.getUint32(offset + 4, true);
    const body = offset + 8;
    if (id === "fmt ") {
      if (size < 16 || body + 16 > wav.length) throw new Error("invalid WAV fmt chunk");
      format = {
        audioFormat: view.getUint16(body, true),
        channels: view.getUint16(body + 2, true),
        sampleRate: view.getUint32(body + 4, true),
        bitDepth: view.getUint16(body + 14, true),
      };
    } else if (id === "data") {
      dataOffset = body;
      dataLength = Math.min(size, wav.length - body);
      if (format) break;
    }
    offset = body + size + (size % 2);
  }

  if (!format) throw new Error("WAV file has no fmt chunk");
  if (dataOffset < 0) throw new Error("WAV file has no data chunk");
  if (format.audioFormat !== 1 && format.audioFormat !== 3) {
    throw new Error(`unsupported WAV encoding: ${format.audioFormat}`);
  }
  if (format.channels < 1) throw new Error("WAV file has no channels");

  const bytesPerSample = format.bitDepth / 8;
  const frameCount = Math.floor(dataLength / (bytesPerSample * format.channels));
  const mono = new Int16Array(frameCount);

  for (let frame = 0; frame < frameCount; frame += 1) {
    let sum = 0;
    for (let channel = 0; channel < format.channels; channel += 1) {
      const at = dataOffset + (frame * format.channels + channel) * bytesPerSample;
      sum += readSample(wav, at, format.bitDepth, format.audioFormat === 3);
    }
    mono[frame] = clampSample(sum / format.channels);
  }

  return {
    samples: mono,
    sampleRate: format.sampleRate,
    channels: format.channels,
    bitDepth: format.bitDepth,
  };
}

export interface TelephoneFrames {
  /** 8 kHz mono PCM after conversion. */
  samples: Int16Array;
  /** μ-law bytes, already framed to 20 ms. */
  mulaw: Uint8Array;
  frames: Uint8Array[];
  durationMs: number;
}

/** Decodes a WAV produced by any voice provider into Twilio-ready frames. */
export function wavToTelephoneFrames(wav: Uint8Array, frameBytes = TELEPHONE_FRAME_BYTES): TelephoneFrames {
  const decoded = decodeWav(wav);
  const samples = toTelephonePcm(decoded.samples, decoded.sampleRate);
  const mulaw = encodeMulaw(samples);
  return {
    samples,
    mulaw,
    frames: splitFrames(mulaw, frameBytes),
    durationMs: Math.round((samples.length / TELEPHONE_SAMPLE_RATE) * 1000),
  };
}

/** Splits encoded audio into fixed-size frames, padding the last one with μ-law silence. */
export function splitFrames(bytes: Uint8Array, frameBytes = TELEPHONE_FRAME_BYTES): Uint8Array[] {
  if (frameBytes <= 0) throw new RangeError("frame size must be positive");
  const frames: Uint8Array[] = [];
  const silence = linearToMulaw(0);
  for (let offset = 0; offset < bytes.length; offset += frameBytes) {
    const chunk = new Uint8Array(frameBytes);
    chunk.fill(silence);
    chunk.set(bytes.subarray(offset, Math.min(bytes.length, offset + frameBytes)));
    frames.push(chunk);
  }
  return frames;
}

/* ------------------------------------------------------------------ */
/* Detection and gain                                                  */
/* ------------------------------------------------------------------ */

/**
 * Energy-based speech detection on 8 kHz PCM.
 *
 * Returns a 0..1 score. A caller is considered speaking above ~0.02; the
 * threshold is exposed so a noisy line can be tuned without code changes.
 */
export function speechEnergy(samples: Int16Array): number {
  if (samples.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < samples.length; i += 1) {
    const value = (samples[i] ?? 0) / 32768;
    sum += value * value;
  }
  return Math.sqrt(sum / samples.length);
}

/** Streaming end-of-utterance detector used by the media bridge. */
export class UtteranceDetector {
  private speechMs = 0;
  private silenceMs = 0;
  private voiced = false;

  constructor(
    private readonly options: {
      /** RMS above which a frame counts as speech. */
      threshold?: number;
      /** Consecutive silence before an utterance is final. */
      silenceMs?: number;
      /** Speech required before silence can end an utterance. */
      minSpeechMs?: number;
      /** Hard cap so a noisy line cannot grow without bound. */
      maxUtteranceMs?: number;
      frameMs?: number;
    } = {},
  ) {}

  /** Feeds one frame; returns "final" when a complete utterance has ended. */
  push(samples: Int16Array): "silence" | "speech" | "final" {
    const frameMs = this.options.frameMs ?? 20;
    const energy = speechEnergy(samples);
    const threshold = this.options.threshold ?? 0.02;
    if (energy >= threshold) {
      this.speechMs += frameMs;
      this.silenceMs = 0;
      this.voiced = true;
    } else if (this.voiced) {
      this.silenceMs += frameMs;
    }

    const minSpeech = this.options.minSpeechMs ?? 240;
    const silenceLimit = this.options.silenceMs ?? 700;
    const maxUtterance = this.options.maxUtteranceMs ?? 30_000;

    if (this.voiced && this.silenceMs >= silenceLimit && this.speechMs >= minSpeech) {
      this.reset();
      return "final";
    }
    if (this.speechMs >= maxUtterance) {
      this.reset();
      return "final";
    }
    return energy >= threshold ? "speech" : "silence";
  }

  get isVoiced(): boolean {
    return this.voiced;
  }

  reset(): void {
    this.speechMs = 0;
    this.silenceMs = 0;
    this.voiced = false;
  }
}

/* ------------------------------------------------------------------ */
/* Base64                                                              */
/* ------------------------------------------------------------------ */

export function bytesToBase64(bytes: Uint8Array): string {
  return Buffer.from(bytes).toString("base64");
}

export function base64ToBytes(value: string): Uint8Array {
  return Uint8Array.from(Buffer.from(value, "base64"));
}

/* ------------------------------------------------------------------ */

function readSample(bytes: Uint8Array, offset: number, bitDepth: number, float: boolean): number {
  if (offset < 0 || offset >= bytes.length) return 0;
  if (float && bitDepth === 32) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    return clampSample(view.getFloat32(offset, true) * 32767);
  }
  if (bitDepth === 8) return ((bytes[offset] ?? 0) - 128) * 256;
  if (bitDepth === 16) {
    const lo = bytes[offset] ?? 0;
    const hi = bytes[offset + 1] ?? 0;
    const value = (hi << 8) | lo;
    return value >= 0x8000 ? value - 0x10000 : value;
  }
  if (bitDepth === 24) {
    const b0 = bytes[offset] ?? 0;
    const b1 = bytes[offset + 1] ?? 0;
    const b2 = bytes[offset + 2] ?? 0;
    let value = (b2 << 16) | (b1 << 8) | b0;
    if (value >= 0x800000) value -= 0x1000000;
    return clampSample(value / 256);
  }
  if (bitDepth === 32) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    return clampSample(view.getInt32(offset, true) / 65536);
  }
  throw new Error(`unsupported WAV bit depth: ${bitDepth}`);
}

function clampSample(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(-32768, Math.min(32767, Math.round(value)));
}

function ascii(bytes: Uint8Array, offset: number, length: number): string {
  let out = "";
  for (let i = 0; i < length; i += 1) {
    out += String.fromCharCode(bytes[offset + i] ?? 0);
  }
  return out;
}
