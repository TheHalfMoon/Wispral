import assert from "node:assert/strict";
import { test } from "node:test";
import { encodeWav } from "@omalla/core";
import type { Logger, SttProvider, SynthesizedAudio } from "@omalla/core";
import { MediaBridge, TwilioProvider, type VoiceEngine } from "@omalla/telephony";

const logger: Logger = {
  debug: () => {},
  info: () => {},
  warn: () => {},
  error: () => {},
  child: () => logger,
} as unknown as Logger;

class FakeEngine implements VoiceEngine {
  started = 0;
  utterances: string[] = [];
  interrupts = 0;
  ended = 0;
  isEnded = false;
  isSpeaking = false;
  private handlers: Array<(audio: SynthesizedAudio, text: string) => void> = [];

  start(): Promise<void> {
    this.started += 1;
    return Promise.resolve();
  }

  handleCallerUtterance(text: string): Promise<void> {
    this.utterances.push(text);
    return Promise.resolve();
  }

  interrupt(): void {
    this.interrupts += 1;
    this.isSpeaking = false;
  }

  end(): Promise<void> {
    this.ended += 1;
    this.isEnded = true;
    return Promise.resolve();
  }

  onAudio(handler: (audio: SynthesizedAudio, text: string) => void): () => void {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((candidate) => candidate !== handler);
    };
  }

  emitAudio(audio: SynthesizedAudio): void {
    this.isSpeaking = true;
    for (const handler of this.handlers) handler(audio, "hello");
  }
}

class FakeStt implements SttProvider {
  readonly id = "fake";
  calls: Uint8Array[] = [];
  private readonly text: string;
  constructor(text = "I need an appointment") {
    this.text = text;
  }
  transcribe(audio: Uint8Array) {
    this.calls.push(audio);
    return Promise.resolve({ text: this.text, confidence: 0.99, isFinal: true });
  }
}

class FakeSocket {
  messages: string[] = [];
  closed: { code?: number; reason?: string } | null = null;
  send(data: string): void {
    this.messages.push(data);
  }
  close(code?: number, reason?: string): void {
    this.closed = { ...(code !== undefined ? { code } : {}), ...(reason !== undefined ? { reason } : {}) };
  }
}

function mulawSine(frames: number, amplitude = 0.6): string[] {
  const out: string[] = [];
  for (let frame = 0; frame < frames; frame += 1) {
    const bytes = Buffer.alloc(160);
    for (let i = 0; i < 160; i += 1) {
      const sample = Math.round(Math.sin((2 * Math.PI * 300 * (frame * 160 + i)) / 8000) * 32767 * amplitude);
      // G.711 μ-law encode (same algorithm as production, kept local to the fixture).
      let value = Math.max(-32768, Math.min(32767, sample));
      let sign = 0;
      if (value < 0) {
        value = -value;
        sign = 0x80;
      }
      value = Math.min(value, 32635) + 0x84;
      let exponent = 7;
      for (let mask = 0x4000; exponent > 0 && (value & mask) === 0; mask >>= 1) exponent -= 1;
      bytes[i] = ~(sign | (exponent << 4) | ((value >> (exponent + 3)) & 0x0f)) & 0xff;
    }
    out.push(bytes.toString("base64"));
  }
  return out;
}

const silencePayload = Buffer.alloc(160, 0xff).toString("base64");
const loudPayloads = mulawSine(20);

function started(): string {
  return JSON.stringify({
    event: "start",
    start: {
      streamSid: "MZ1",
      callSid: "CA1",
      customParameters: { callId: "call_1" },
      mediaFormat: { encoding: "audio/x-mulaw", sampleRate: 8000, channels: 1 },
    },
  });
}

function media(payload: string): string {
  return JSON.stringify({ event: "media", media: { track: "inbound", payload } });
}

test("a complete utterance is transcribed and handed to the engine", async () => {
  const instance = new TwilioProvider({ accountSid: "AC1", authToken: "token" });
  const engine = new FakeEngine();
  const stt = new FakeStt("I need an appointment on Friday");
  const socket = new FakeSocket();
  const bridge = new MediaBridge({ provider: instance, engine, stt, logger, language: "en-US" });
  bridge.attach(socket);

  bridge.handleMessage(started());
  for (const payload of loudPayloads) bridge.handleMessage(media(payload));
  for (let i = 0; i < 40; i += 1) bridge.handleMessage(media(silencePayload));
  await bridge.idle();

  assert.equal(engine.started, 1);
  assert.equal(stt.calls.length, 1);
  assert.deepEqual(engine.utterances, ["I need an appointment on Friday"]);

  const wav = stt.calls[0];
  assert.ok(wav);
  assert.equal(String.fromCharCode(...(wav?.subarray(0, 4) ?? [])), "RIFF");
  // 20 loud frames plus trailing silence, resampled/encoded as 8 kHz PCM16.
  assert.ok((wav?.length ?? 0) > 44 + 8000);
});

test("synthesized WAV is sent back as 20 ms μ-law frames followed by a mark", () => {
  const instance = new TwilioProvider({ accountSid: "AC1", authToken: "token" });
  const engine = new FakeEngine();
  const socket = new FakeSocket();
  const bridge = new MediaBridge({ provider: instance, engine, stt: new FakeStt(), logger });
  bridge.attach(socket);
  bridge.handleMessage(started());

  const pcm = new Uint8Array(16000 * 2);
  for (let i = 0; i < 16000; i += 1) {
    const value = Math.round(Math.sin((2 * Math.PI * 440 * i) / 16000) * 12000);
    pcm[i * 2] = value & 0xff;
    pcm[i * 2 + 1] = (value >> 8) & 0xff;
  }
  const wav = encodeWav(pcm, { sampleRate: 16000, channels: 1, bitDepth: 16 });
  engine.emitAudio({ data: wav, mimeType: "audio/wav", durationMs: 1000 });

  const frames = socket.messages
    .map((message) => JSON.parse(message) as { event: string; media?: { payload: string }; mark?: { name: string } })
    .filter((message) => message.event === "media");
  assert.equal(frames.length, 50);
  for (const frame of frames) {
    assert.ok(Buffer.from(frame.media?.payload ?? "", "base64").length === 160);
  }
  const mark = socket.messages
    .map((message) => JSON.parse(message) as { event: string; mark?: { name: string } })
    .find((message) => message.event === "mark");
  assert.equal(mark?.mark?.name, "omalla-audio");
});

test("caller speech during playback interrupts and clears the carrier queue", () => {
  const instance = new TwilioProvider({ accountSid: "AC1", authToken: "token" });
  const engine = new FakeEngine();
  const socket = new FakeSocket();
  const bridge = new MediaBridge({ provider: instance, engine, stt: new FakeStt(), logger });
  bridge.attach(socket);
  bridge.handleMessage(started());

  engine.isSpeaking = true;
  for (let i = 0; i < 14; i += 1) bridge.handleMessage(media(loudPayloads[i % loudPayloads.length] ?? silencePayload));

  assert.equal(engine.interrupts, 1);
  const cleared = socket.messages
    .map((message) => JSON.parse(message) as { event: string })
    .some((message) => message.event === "clear");
  assert.equal(cleared, true);
});

test("closing the media socket ends the conversation exactly once", async () => {
  const instance = new TwilioProvider({ accountSid: "AC1", authToken: "token" });
  const engine = new FakeEngine();
  const bridge = new MediaBridge({ provider: instance, engine, stt: new FakeStt(), logger });
  bridge.attach(new FakeSocket());
  bridge.handleMessage(started());

  await bridge.handleClose();
  await bridge.handleClose();
  assert.equal(engine.ended, 1);
  assert.equal(bridge.isClosed, true);
});

test("DTMF digits reach the call controller", () => {
  const instance = new TwilioProvider({ accountSid: "AC1", authToken: "token" });
  const digits: string[] = [];
  const bridge = new MediaBridge({
    provider: instance,
    engine: new FakeEngine(),
    stt: new FakeStt(),
    logger,
    onDtmf: (digit) => digits.push(digit),
  });
  bridge.attach(new FakeSocket());
  bridge.handleMessage(JSON.stringify({ event: "dtmf", dtmf: { digit: "3" } }));
  assert.deepEqual(digits, ["3"]);
});

test("unsupported audio types are refused instead of sent as noise", () => {
  const instance = new TwilioProvider({ accountSid: "AC1", authToken: "token" });
  const engine = new FakeEngine();
  const socket = new FakeSocket();
  const bridge = new MediaBridge({ provider: instance, engine, stt: new FakeStt(), logger });
  bridge.attach(socket);
  bridge.handleMessage(started());
  engine.emitAudio({ data: new Uint8Array([1, 2, 3]), mimeType: "audio/mpeg", durationMs: 100 });
  assert.equal(socket.messages.length, 0);
});
