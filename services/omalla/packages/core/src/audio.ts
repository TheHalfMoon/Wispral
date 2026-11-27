/** Minimal PCM WAV helpers. No native dependency, deterministic in tests. */

export interface WavFormat {
  sampleRate: number;
  channels: number;
  bitDepth: 8 | 16 | 32;
}

export const DEFAULT_WAV: WavFormat = { sampleRate: 16000, channels: 1, bitDepth: 16 };

export function encodeWav(pcm: Uint8Array, format: WavFormat = DEFAULT_WAV): Uint8Array {
  const bytesPerSample = format.bitDepth / 8;
  const blockAlign = format.channels * bytesPerSample;
  const byteRate = format.sampleRate * blockAlign;
  const header = new ArrayBuffer(44);
  const view = new DataView(header);

  writeAscii(view, 0, "RIFF");
  view.setUint32(4, 36 + pcm.length, true);
  writeAscii(view, 8, "WAVE");
  writeAscii(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, format.channels, true);
  view.setUint32(24, format.sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, format.bitDepth, true);
  writeAscii(view, 36, "data");
  view.setUint32(40, pcm.length, true);

  const out = new Uint8Array(44 + pcm.length);
  out.set(new Uint8Array(header), 0);
  out.set(pcm, 44);
  return out;
}

export function silenceWav(durationMs: number, format: WavFormat = DEFAULT_WAV): Uint8Array {
  const samples = Math.max(1, Math.round((durationMs / 1000) * format.sampleRate));
  const bytesPerSample = format.bitDepth / 8;
  return encodeWav(new Uint8Array(samples * format.channels * bytesPerSample), format);
}

export function readWavFormat(wav: Uint8Array): WavFormat | undefined {
  if (wav.length < 44) return undefined;
  const view = new DataView(wav.buffer, wav.byteOffset, wav.byteLength);
  const riff = String.fromCharCode(wav[0] ?? 0, wav[1] ?? 0, wav[2] ?? 0, wav[3] ?? 0);
  const wave = String.fromCharCode(wav[8] ?? 0, wav[9] ?? 0, wav[10] ?? 0, wav[11] ?? 0);
  if (riff !== "RIFF" || wave !== "WAVE") return undefined;
  return {
    channels: view.getUint16(22, true),
    sampleRate: view.getUint32(24, true),
    bitDepth: view.getUint16(34, true) as 8 | 16 | 32,
  };
}

export function wavDurationMs(wav: Uint8Array): number {
  const format = readWavFormat(wav);
  if (!format) return 0;
  const view = new DataView(wav.buffer, wav.byteOffset, wav.byteLength);
  const dataBytes = view.getUint32(40, true);
  const bytesPerSecond = format.sampleRate * format.channels * (format.bitDepth / 8);
  return bytesPerSecond > 0 ? Math.round((dataBytes / bytesPerSecond) * 1000) : 0;
}

/** Rough estimate used only for mock providers and UI hints. */
export function estimateSpeechDurationMs(text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length || 1;
  return Math.max(250, Math.round((words / 2.6) * 1000));
}

function writeAscii(view: DataView, offset: number, text: string): void {
  for (let i = 0; i < text.length; i += 1) {
    view.setUint8(offset + i, text.charCodeAt(i));
  }
}
