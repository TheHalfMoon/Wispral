import assert from "node:assert/strict";
import { test } from "node:test";
import { encodeWav } from "@omalla/core";
import {
  TELEPHONE_SAMPLE_RATE,
  UtteranceDetector,
  decodeMulaw,
  decodeWav,
  encodeMulaw,
  linearToMulaw,
  mulawToLinear,
  resamplePcm16,
  splitFrames,
  speechEnergy,
  wavToTelephoneFrames,
} from "@omalla/telephony";

/** Builds a PCM16 sine at a chosen frequency and rate. */
function sine(frequency: number, sampleRate: number, durationMs: number, amplitude = 0.5): Int16Array {
  const length = Math.round((durationMs / 1000) * sampleRate);
  const samples = new Int16Array(length);
  for (let i = 0; i < length; i += 1) {
    samples[i] = Math.round(Math.sin((2 * Math.PI * frequency * i) / sampleRate) * 32767 * amplitude);
  }
  return samples;
}

function pcmToBytes(samples: Int16Array): Uint8Array {
  const bytes = new Uint8Array(samples.length * 2);
  for (let i = 0; i < samples.length; i += 1) {
    const value = samples[i] ?? 0;
    bytes[i * 2] = value & 0xff;
    bytes[i * 2 + 1] = (value >> 8) & 0xff;
  }
  return bytes;
}

test("μ-law silence encodes to 0xFF and decodes to zero", () => {
  assert.equal(linearToMulaw(0), 0xff);
  assert.equal(mulawToLinear(0xff), 0);
});

test("μ-law round-trips speech within telephone tolerance", () => {
  const samples = sine(440, TELEPHONE_SAMPLE_RATE, 100);
  const decoded = decodeMulaw(encodeMulaw(samples));
  assert.equal(decoded.length, samples.length);
  let noise = 0;
  let signal = 0;
  for (let i = 0; i < samples.length; i += 1) {
    const expected = samples[i] ?? 0;
    const actual = decoded[i] ?? 0;
    const error = expected - actual;
    noise += error * error;
    signal += expected * expected;
  }
  const snr = 10 * Math.log10(signal / Math.max(1, noise));
  assert.ok(snr > 30, `expected >30 dB SNR, got ${snr.toFixed(1)} dB`);
});

test("resampling 16 kHz to 8 kHz halves the sample count and keeps energy", () => {
  const input = sine(440, 16000, 100);
  const output = resamplePcm16(input, 16000, 8000);
  assert.equal(output.length, input.length / 2);
  assert.ok(speechEnergy(output) > 0.2);
  assert.ok(Math.abs(speechEnergy(output) - speechEnergy(input)) < 0.15);
});

test("WAV decode walks extra chunks instead of assuming a 44-byte header", () => {
  const samples = sine(300, 16000, 60);
  const wav = encodeWav(pcmToBytes(samples), { sampleRate: 16000, channels: 1, bitDepth: 16 });

  // Insert a JUNK chunk after the fmt chunk. The data offset must still be found.
  const extra = new Uint8Array(wav.length + 12);
  extra.set(wav.subarray(0, 36), 0);
  extra.set(new TextEncoder().encode("JUNK"), 36);
  new DataView(extra.buffer).setUint32(40, 4, true);
  extra.set(new TextEncoder().encode("test"), 44);
  extra.set(wav.subarray(36), 48);

  const decoded = decodeWav(extra);
  assert.equal(decoded.sampleRate, 16000);
  assert.equal(decoded.channels, 1);
  assert.equal(decoded.samples.length, samples.length);
});

test("WAV from a 16 kHz voice becomes 8 kHz μ-law frames of 20 ms", () => {
  const wav = encodeWav(pcmToBytes(sine(440, 16000, 1000)), {
    sampleRate: 16000,
    channels: 1,
    bitDepth: 16,
  });
  const converted = wavToTelephoneFrames(wav);
  assert.equal(converted.samples.length, 8000);
  assert.equal(converted.frames.length, 50);
  assert.ok(converted.frames.every((frame) => frame.length === 160));
  assert.ok(Math.abs(converted.durationMs - 1000) <= 2);
});

test("the last frame is padded with μ-law silence", () => {
  const frames = splitFrames(new Uint8Array(321));
  assert.equal(frames.length, 3);
  assert.equal(frames[2]?.length, 160);
  assert.equal(frames[2]?.[7], 0xff);
});

test("utterance detection needs speech followed by enough silence", () => {
  const detector = new UtteranceDetector({ silenceMs: 200, minSpeechMs: 60 });
  const loud = sine(300, TELEPHONE_SAMPLE_RATE, 20, 0.6);
  const quiet = new Int16Array(160);

  for (let i = 0; i < 6; i += 1) assert.notEqual(detector.push(loud), "final");
  let finalized = false;
  for (let i = 0; i < 12; i += 1) {
    if (detector.push(quiet) === "final") {
      finalized = true;
      break;
    }
  }
  assert.equal(finalized, true);
});

test("a silent line never finalizes an utterance", () => {
  const detector = new UtteranceDetector({ silenceMs: 100 });
  const quiet = new Int16Array(160);
  for (let i = 0; i < 100; i += 1) assert.equal(detector.push(quiet), "silence");
});
