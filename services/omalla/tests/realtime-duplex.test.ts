import assert from "node:assert/strict";
import dgram from "node:dgram";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { ConversationEngine, encodeWav, newId, nowIso, silentLogger } from "@omalla/core";
import type { Agent, Call, SynthesizedAudio } from "@omalla/core";
import { DemoLlm, MockStt } from "@omalla/providers";
import {
  BoundedJitterBuffer,
  OmallaRuntime,
  OutboundAudioPacer,
  RealtimeDuplexSession,
  buildApp,
  buildStunBindingRequest,
  loadConfig,
} from "@omalla/server";
import {
  RTP_PT_PCMU,
  SrtpContext,
  encodeAlaw,
  encodeMulaw,
  encodeRtpPacket,
  formatSdesCryptoAttribute,
  parseSdp,
  pcm16ToBytes,
  serializeSdesLine,
} from "@omalla/telephony";

function makeSineSpeechPcm16(sampleRate: number, durationMs: number, amplitude = 12000): Int16Array {
  const count = Math.round((sampleRate * durationMs) / 1000);
  const out = new Int16Array(count);
  for (let i = 0; i < count; i += 1) {
    out[i] = Math.round(Math.sin((2 * Math.PI * 440 * i) / sampleRate) * amplitude);
  }
  return out;
}

function makeLongWav(durationMs: number, sampleRate = 16000): SynthesizedAudio {
  const pcm = makeSineSpeechPcm16(sampleRate, durationMs, 9000);
  return {
    mimeType: "audio/wav",
    data: encodeWav(pcm16ToBytes(pcm), { sampleRate, channels: 1, bitDepth: 16 }),
    durationMs,
  };
}

test("BoundedJitterBuffer reorders out-of-order packets, conceals losses (PLC), and enforces max-depth bounds", () => {
  const jb = new BoundedJitterBuffer({
    maxDepthFrames: 4,
    reorderWindowFrames: 2,
    frameSamples: 160,
  });

  const frameOf = (val: number) => new Int16Array(160).fill(val);

  // Push out-of-order: 100, 102, 101
  assert.equal(jb.push(100, frameOf(1000)).accepted, true);
  assert.equal(jb.push(102, frameOf(3000)).accepted, true);
  assert.equal(jb.push(101, frameOf(2000)).accepted, true);
  // Duplicate 101 rejected
  const dup = jb.push(101, frameOf(2000));
  assert.equal(dup.accepted, false);
  assert.equal(dup.reason, "duplicate");

  const p0 = jb.pop();
  const p1 = jb.pop();
  const p2 = jb.pop();
  assert.equal(p0.sequenceNumber, 100);
  assert.equal(p0.samples[0], 1000);
  assert.equal(p1.sequenceNumber, 101);
  assert.equal(p1.samples[0], 2000);
  assert.equal(p2.sequenceNumber, 102);
  assert.equal(p2.samples[0], 3000);

  // Late packet (< nextExpectedSeq 103) dropped
  const late = jb.push(99, frameOf(999));
  assert.equal(late.accepted, false);
  assert.equal(late.reason, "too_late");

  // Missing seq 103: push 104 and 105 -> pop conceals 103 with attenuated PLC!
  jb.push(104, frameOf(4000));
  jb.push(105, frameOf(5000));
  const plc = jb.pop();
  assert.equal(plc.kind, "plc");
  assert.equal(plc.sequenceNumber, 103);
  assert.ok(plc.samples[0]! > 0 && plc.samples[0]! < 3000, "PLC frame should attenuate last good frame");

  // Overflow beyond maxDepthFrames=4 sheds oldest frames without unbounded growth
  for (let seq = 106; seq <= 114; seq += 1) {
    jb.push(seq, frameOf(seq));
  }
  const stats = jb.stats();
  assert.ok(stats.queuedFrames <= 4);
  assert.ok(stats.overflowDropCount >= 4);
  assert.equal(stats.plcCount, 1);
  assert.equal(stats.duplicateCount, 1);
  assert.equal(stats.lateDropCount, 1);
});

test("OutboundAudioPacer paces 20ms frames, enforces socket backpressure watermarks, and drops stale turn_epoch chunks", () => {
  let activeEpoch = 1;
  let fakeClockMs = 1000;
  let fakeBufferedAmount = 0;
  const sent: Array<{ bytes: Uint8Array; epoch: number; seq: number }> = [];
  const firstFrames: Array<{ epoch: number; atMs: number }> = [];

  const pacer = new OutboundAudioPacer({
    codec: "pcm16",
    sampleRate: 16000,
    highWatermarkBytes: 4096,
    criticalWatermarkBytes: 16384,
    autoTimer: false,
    clock: () => fakeClockMs,
    getTurnEpoch: () => activeEpoch,
    onFirstFrameForEpoch: (epoch, atMs) => firstFrames.push({ epoch, atMs }),
    sink: {
      get bufferedAmount() {
        return fakeBufferedAmount;
      },
      sendAudioFrame: (bytes, meta) => {
        sent.push({ bytes, epoch: meta.turnEpoch, seq: meta.seq });
      },
    },
  });

  // 200 ms WAV -> 10 frames of 20 ms (640 bytes each @ 16kHz PCM16)
  const queued = pacer.enqueueAudio(makeLongWav(200, 16000), 1);
  assert.equal(queued, 10);

  // Tick 1 emits T6 first frame
  fakeClockMs = 1020;
  assert.equal(pacer.tick(), true);
  assert.equal(sent.length, 1);
  assert.equal(sent[0]!.bytes.byteLength, 640);
  assert.deepEqual(firstFrames, [{ epoch: 1, atMs: 1020 }]);

  // High watermark pauses send without dropping
  fakeBufferedAmount = 8000;
  assert.equal(pacer.tick(), false);
  assert.equal(pacer.stats().backpressurePauses, 1);

  // Critical watermark sheds queued frames to bound latency
  fakeBufferedAmount = 20000;
  assert.equal(pacer.tick(), false);
  assert.ok(pacer.stats().backpressureDrops > 0);
  fakeBufferedAmount = 0;

  // Increment turnEpoch (barge-in): remaining epoch-1 frames + any late epoch-1 TTS chunk MUST be dropped!
  activeEpoch = 2;
  assert.equal(pacer.tick(), false);
  const staleQueued = pacer.enqueueAudio(makeLongWav(100, 16000), 1);
  assert.equal(staleQueued, 0);
  assert.ok(pacer.stats().staleEpochDrops >= 2);

  // Epoch 2 audio flows cleanly and triggers T6 for epoch 2
  fakeClockMs = 1200;
  assert.equal(pacer.enqueueAudio(makeLongWav(40, 16000), 2), 2);
  assert.equal(pacer.tick(), true);
  assert.equal(sent[sent.length - 1]!.epoch, 2);
  assert.equal(firstFrames.length, 2);
  assert.equal(firstFrames[1]!.epoch, 2);

  pacer.close();
});

test("RealtimeDuplexSession enforces OM-T8 sink-confirmed T2 observed_audio_halt vs stopped_unconfirmed and drops stale epochs", async () => {
  let fakeNowMs = 500;
  const makeEngineAndCall = (agentId = "agt_rt") => {
    const now = nowIso();
    const agent: Agent = {
      id: agentId,
      tenantId: "ten_1",
      name: "Ava",
      description: "Test",
      status: "published",
      version: 1,
      createdAt: now,
      updatedAt: now,
      config: {
        firstMessage: "",
        systemPrompt: "Helpful receptionist.",
        model: { provider: "mock", model: "demo" },
        voice: { provider: "mock", voiceId: "demo" },
        transcriber: { provider: "mock", language: "en-US" },
        language: "en-US",
        tools: [],
        knowledgeBaseIds: [],
        maxDurationSec: 300,
        silenceTimeoutSec: 0,
        endCallPhrases: ["goodbye"],
        interruption: { enabled: true, minWords: 1 },
        recording: { enabled: false, consentAnnouncement: false },
        variables: {},
      },
    };
    const call: Call = {
      id: newId("call"),
      tenantId: "ten_1",
      direction: "inbound",
      status: "in_progress",
      from: "ws:caller",
      to: "agent:agt_rt",
      agentId: agent.id,
      startedAt: now,
      transcript: [],
      messages: [],
      variables: {},
      metadata: { callerNumberVerified: false },
      metrics: {
        turnCount: 0,
        turnLatenciesMs: [],
        totalTokensIn: 0,
        totalTokensOut: 0,
        toolCalls: 0,
        interruptions: 0,
      },
      simulation: true,
    };
    const engine = new ConversationEngine({
      call,
      agent,
      llm: new DemoLlm(),
      tts: {
        id: "long-mock-tts",
        synthesize: async () => makeLongWav(600, 16000), // 30 frames of 20 ms
      },
      tools: { execute: async () => ({ ok: true }) },
      logger: silentLogger,
      clock: () => fakeNowMs,
    });
    return { engine, call };
  };

  // Case A: Acknowledged WebSocket client -> T2 becomes observed_audio_halt ONLY after clear.ack!
  {
    const { engine } = makeEngineAndCall();
    const jsonEvents: Array<Record<string, unknown>> = [];
    const audioFrames: Array<{ epoch: number; bytes: Uint8Array }> = [];

    const session = new RealtimeDuplexSession({
      engine,
      stt: new MockStt(["What are your opening hours?"]),
      codec: "pcm16",
      sampleRate: 16000,
      sinkAckSupported: true,
      autoPace: false,
      clock: () => fakeNowMs,
      logger: silentLogger,
      sink: {
        bufferedAmount: 0,
        sendJson: (ev) => jsonEvents.push(ev),
        sendBinaryAudio: (bytes, meta) => audioFrames.push({ epoch: meta.turnEpoch, bytes }),
        close: () => {},
      },
    });

    await session.start();
    fakeNowMs = 600;
    await session.handleControlMessage({ type: "utterance.text", text: "What are your opening hours?" });

    // Emit 2 paced frames at epoch 1 -> records T6
    fakeNowMs = 625;
    assert.equal(session.pacer.tick(), true);
    fakeNowMs = 645;
    assert.equal(session.pacer.tick(), true);
    assert.ok(session.pacer.pendingFrames > 10, "TTS queue still has many frames in flight");

    // Caller barges in at T1 = 700ms! (turnEpoch increments atomically from 1 -> 2)
    fakeNowMs = 700;
    await session.handleControlMessage({ type: "barge_in" });
    assert.equal(session.turnEpoch, 2);
    assert.equal(session.pacer.pendingFrames, 0, "outbound pacer queue flushed immediately");

    const clearEvent = jsonEvents.find((e) => e.type === "audio.clear");
    assert.ok(clearEvent, "server sent audio.clear to sink");
    assert.equal(clearEvent.turnEpoch, 2);

    // BEFORE client sends clear.ack, T2 MUST NOT claim observed_audio_halt!
    const snapBeforeAck = session.telemetrySnapshot();
    assert.equal(snapBeforeAck.turns[0]?.t2HaltStatus, "pending_sink_ack");

    // clear.ack without numeric turnEpoch or with stale turnEpoch=1 MUST NOT confirm halt!
    await session.handleControlMessage({ type: "clear.ack" });
    await session.handleControlMessage({ type: "clear.ack", turnEpoch: 1 });
    assert.equal(session.telemetrySnapshot().turns[0]?.t2HaltStatus, "pending_sink_ack");

    // Oversized audio.append (>16 KiB) is rejected deterministically
    await session.handleControlMessage({
      type: "audio.append",
      payload: Buffer.alloc(17 * 1024, 0).toString("base64"),
    });
    assert.ok(jsonEvents.some((e) => e.type === "error" && e.code === "frame_too_large"));

    // Client confirms playback buffer cleared at 718ms with exact newEpoch=2
    fakeNowMs = 718;
    await session.handleControlMessage({ type: "clear.ack", turnEpoch: 2 });

    const snapAfterAck = session.telemetrySnapshot();
    const tlm = snapAfterAck.turns[0]!;
    assert.equal(tlm.t1BargeInOnsetMs, 700);
    assert.equal(tlm.t2AudioHaltMs, 718);
    assert.equal(tlm.t2HaltStatus, "observed_audio_halt");
    assert.equal(tlm.deltasMs.bargeInHaltMs, 18);
    assert.ok(tlm.t0SpeechEndMs !== null);
    assert.ok(tlm.t3PartialSttMs !== null);
    assert.ok(tlm.t4FinalSttMs !== null);
    assert.ok(tlm.t5FirstTokenMs !== null);
    assert.ok(tlm.t6FirstAudioFrameMs !== null);

    await session.close();
  }

  // Case B: Unacknowledged PSTN trunk (sinkAckSupported = false) -> T2 MUST report stopped_unconfirmed (OM-T8)!
  {
    const { engine } = makeEngineAndCall("agt_pstn");
    const jsonEvents: Array<Record<string, unknown>> = [];
    const session = new RealtimeDuplexSession({
      engine,
      stt: new MockStt(["Hello"]),
      codec: "pcmu",
      sampleRate: 8000,
      sinkAckSupported: false,
      autoPace: false,
      clock: () => fakeNowMs,
      logger: silentLogger,
      sink: {
        bufferedAmount: 0,
        sendJson: (ev) => jsonEvents.push(ev),
        sendBinaryAudio: () => {},
        close: () => {},
      },
    });

    await session.start();
    fakeNowMs = 1000;
    await session.handleControlMessage({ type: "utterance.text", text: "What are your hours?" });
    fakeNowMs = 1020;
    session.pacer.tick();

    fakeNowMs = 1050;
    await session.handleControlMessage({ type: "barge_in" });

    const haltMsg = jsonEvents.find((e) => e.type === "barge_in.halt");
    assert.ok(haltMsg);
    assert.equal(haltMsg.t2HaltStatus, "stopped_unconfirmed");
    assert.equal(session.telemetrySnapshot().turns[0]?.t2HaltStatus, "stopped_unconfirmed");

    await session.close();
  }
});

test("Live /v1/realtime/ws enforces single-use media token, binary PCM16/PCMU/PCMA codecs, and /v1/realtime/webrtc/offer negotiates ICE-lite STUN + SRTP", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "omalla-realtime-e2e-"));
  const prevVoice = process.env.OMALLA_DEMO_VOICE;
  const prevStt = process.env.OMALLA_DEMO_STT;
  process.env.OMALLA_DEMO_VOICE = "mock";
  process.env.OMALLA_DEMO_STT = "mock";

  const runtime = await OmallaRuntime.open(
    loadConfig({
      dataDir: dir,
      seedDemo: true,
      masterKey: Buffer.alloc(32, 9).toString("base64"),
    }),
    { offlineProviders: true },
  );
  const tenant = runtime.db.col("tenants").list()[0]!;
  const agent = runtime.db.col("agents").list((a: Agent) => a.tenantId === tenant.id)[0]!;
  const apiKey = (await runtime.issueApiKey(tenant.id, "rt-test", "owner")).token;

  const app = await buildApp(runtime);
  const address = await app.listen({ host: "127.0.0.1", port: 0 });
  const wsBase = address.replace(/^http/, "ws");

  interface NativeWs {
    binaryType: string;
    send(data: string | Uint8Array | Buffer): void;
    close(): void;
    addEventListener(type: "message", listener: (ev: { data: string | ArrayBuffer }) => void): void;
    addEventListener(type: "close", listener: (ev: { code: number }) => void): void;
    addEventListener(type: "error", listener: (ev: unknown) => void): void;
  }
  const NativeWebSocket = (globalThis as unknown as { WebSocket: new (url: string) => NativeWs }).WebSocket;

  try {
    // 1. Issue single-use media token
    const tokenRes = await app.inject({
      method: "POST",
      url: "/v1/realtime/token",
      headers: { authorization: `Bearer ${apiKey}` },
      payload: { agentId: agent.id, ttlSec: 60 },
    });
    assert.equal(tokenRes.statusCode, 201);
    const { token } = tokenRes.json() as { token: string; singleUse: boolean };
    assert.ok(token.startsWith("omrt_"));

    // 2. Connect WS #1 with PCMA (A-law) codec, exchange binary audio + barge-in clear.ack
    const ws1Events: Array<Record<string, unknown>> = [];
    const ws1BinaryFrames: Buffer[] = [];
    await new Promise<void>((resolve, reject) => {
      const ws = new NativeWebSocket(`${wsBase}/v1/realtime/ws?token=${encodeURIComponent(token)}&codec=pcma`);
      ws.binaryType = "arraybuffer";
      ws.addEventListener("error", (err) => reject(new Error(String(err))));
      ws.addEventListener("message", (msg) => {
        if (typeof msg.data !== "string") {
          ws1BinaryFrames.push(Buffer.from(msg.data));
          return;
        }
        const ev = JSON.parse(msg.data) as Record<string, unknown>;
        ws1Events.push(ev);
        if (ev.type === "session.ready") {
          const alaw = encodeAlaw(new Int16Array(160));
          const framed = Buffer.alloc(4 + alaw.length);
          framed[0] = 0x4f;
          framed[1] = 0x4d;
          framed.writeUInt16BE(0, 2);
          Buffer.from(alaw).copy(framed, 4);
          ws.send(framed);
          ws.send(JSON.stringify({ type: "utterance.text", text: "What are your hours?" }));
        }
        if (ev.type === "telemetry.latency") {
          ws.close();
        }
      });
      ws.addEventListener("close", () => resolve());
    });

    assert.ok(ws1Events.some((e) => e.type === "session.ready"));
    assert.ok(ws1Events.some((e) => e.type === "telemetry.latency"));
    assert.ok(ws1BinaryFrames.length >= 1, "received binary 20ms PCMA TTS frames");
    assert.equal(ws1BinaryFrames[0]!.length, 160, "20 ms @ 8 kHz PCMA is exactly 160 bytes");

    // 3. Replaying the SAME single-use media token MUST be rejected with close code 4401!
    const replayCloseCode = await new Promise<number>((resolve) => {
      const wsReplay = new NativeWebSocket(`${wsBase}/v1/realtime/ws?token=${encodeURIComponent(token)}`);
      wsReplay.addEventListener("close", (ev) => resolve(ev.code));
    });
    assert.equal(replayCloseCode, 4401);

    // 4. WebRTC Offer: SAVPF without a=crypto: MUST be rejected with 400!
    const missingCryptoRes = await app.inject({
      method: "POST",
      url: "/v1/realtime/webrtc/offer",
      headers: { authorization: `Bearer ${apiKey}` },
      payload: {
        agentId: agent.id,
        sdp: [
          "v=0",
          "o=client 9910 2 IN IP4 127.0.0.1",
          "s=Missing Crypto",
          "t=0 0",
          "m=audio 49170 UDP/TLS/RTP/SAVPF 0 101",
          "c=IN IP4 127.0.0.1",
          "a=ice-ufrag:u1",
          "a=ice-pwd:password0123456789abcdef",
        ].join("\r\n") + "\r\n",
      },
    });
    assert.equal(missingCryptoRes.statusCode, 400);

    // 5. WebRTC Offer -> ICE-lite STUN Binding Check (MESSAGE-INTEGRITY enforced!) -> Encrypted SRTP Audio Round-Trip!
    const offerCrypto = formatSdesCryptoAttribute(1);
    const sdpOffer = [
      "v=0",
      "o=client 9911 2 IN IP4 127.0.0.1",
      "s=WebRTC Test",
      "t=0 0",
      "m=audio 49170 RTP/SAVP 0 101",
      "c=IN IP4 127.0.0.1",
      "a=ice-ufrag:clientufrag",
      "a=ice-pwd:clientpassword0123456789",
      "a=rtpmap:0 PCMU/8000",
      "a=rtpmap:101 telephone-event/8000",
      serializeSdesLine(offerCrypto),
      "m=application 5000 UDP/DTLS/SCTP webrtc-datachannel",
      "a=sctp-port:5000",
    ].join("\r\n") + "\r\n";

    const offerRes = await app.inject({
      method: "POST",
      url: "/v1/realtime/webrtc/offer",
      headers: { authorization: `Bearer ${apiKey}` },
      payload: { agentId: agent.id, sdp: sdpOffer },
    });
    assert.equal(offerRes.statusCode, 201);
    const negotiated = offerRes.json() as {
      sessionId: string;
      sdpAnswer: string;
      iceLite: boolean;
      localUdpPort: number;
      localIceUfrag: string;
      localIcePwd: string;
      srtpSuite: string;
    };
    assert.equal(negotiated.iceLite, true);
    assert.equal(negotiated.srtpSuite, "AES_CM_128_HMAC_SHA1_80");
    assert.match(negotiated.sdpAnswer, /a=ice-lite/);
    assert.match(negotiated.sdpAnswer, /webrtc-datachannel/);

    const parsedAnswer = parseSdp(negotiated.sdpAnswer);
    assert.ok(parsedAnswer.sdesCrypto);
    const clientSrtpTx = new SrtpContext(offerCrypto.keyMaterial);
    const clientSrtpRx = new SrtpContext(parsedAnswer.sdesCrypto.keyMaterial);

    const peerUdp = dgram.createSocket("udp4");
    peerUdp.unref();
    await new Promise<void>((r) => peerUdp.bind(0, "127.0.0.1", () => r()));

    try {
      let stunResponseReceived = false;
      const decryptedWebRtcFrames: Uint8Array[] = [];

      const mediaReady = new Promise<void>((resolve) => {
        peerUdp.on("message", (pkt) => {
          if (pkt.length >= 20 && pkt.readUInt16BE(0) === 0x0101) {
            stunResponseReceived = true;
            return;
          }
          if (pkt.length >= 12 && ((pkt[0] ?? 0) & 0xc0) === 0x80) {
            const dec = clientSrtpRx.unprotect(pkt);
            decryptedWebRtcFrames.push(dec.packet.payload);
            if (decryptedWebRtcFrames.length >= 1) resolve();
          }
        });
      });

      // 1a. Unauthenticated STUN Binding Request (wrong ice-pwd) MUST NOT latch peer!
      const badStunReq = buildStunBindingRequest(
        `${negotiated.localIceUfrag}:clientufrag`,
        "wrong-ice-password-should-be-dropped",
      );
      peerUdp.send(badStunReq, negotiated.localUdpPort, "127.0.0.1");
      await new Promise((r) => setTimeout(r, 25));
      const preCheckStatus = await app.inject({
        method: "GET",
        url: `/v1/realtime/webrtc/${negotiated.sessionId}`,
        headers: { authorization: `Bearer ${apiKey}` },
      });
      assert.equal((preCheckStatus.json() as { iceState: string }).iceState, "checking");
      assert.equal(stunResponseReceived, false);

      // 1b. Authentic RFC 5389 STUN Binding Request -> latches ICE-lite peer and streams SRTP greeting frames
      const stunReq = buildStunBindingRequest(
        `${negotiated.localIceUfrag}:clientufrag`,
        negotiated.localIcePwd,
      );
      peerUdp.send(stunReq, negotiated.localUdpPort, "127.0.0.1");

      await mediaReady;
      assert.equal(stunResponseReceived, true);
      assert.ok(decryptedWebRtcFrames.length >= 1);

      // 2. Send inbound SRTP PCMU audio packet (triggers barge-in on greeting!)
      const mulawSpeech = encodeMulaw(makeSineSpeechPcm16(8000, 20, 10000));
      const rtp = encodeRtpPacket(
        {
          marker: true,
          payloadType: RTP_PT_PCMU,
          sequenceNumber: 1,
          timestamp: 160,
          ssrc: 0xabcdef01,
        },
        mulawSpeech,
      );
      peerUdp.send(clientSrtpTx.protect(rtp), negotiated.localUdpPort, "127.0.0.1");

      // Submit Trickle ICE candidate + inspect session state
      const iceRes = await app.inject({
        method: "POST",
        url: `/v1/realtime/webrtc/${negotiated.sessionId}/ice`,
        headers: { authorization: `Bearer ${apiKey}` },
        payload: {
          candidate: `candidate:2 1 udp 2130706431 127.0.0.1 ${peerUdp.address().port} typ host`,
        },
      });
      assert.equal(iceRes.statusCode, 200);

      const statusRes = await app.inject({
        method: "GET",
        url: `/v1/realtime/webrtc/${negotiated.sessionId}`,
        headers: { authorization: `Bearer ${apiKey}` },
      });
      assert.equal(statusRes.statusCode, 200);
      assert.equal((statusRes.json() as { iceState: string }).iceState, "connected");
    } finally {
      await app.inject({
        method: "DELETE",
        url: `/v1/realtime/webrtc/${negotiated.sessionId}`,
        headers: { authorization: `Bearer ${apiKey}` },
      });
      await new Promise<void>((r) => {
        try {
          peerUdp.close(() => r());
        } catch {
          r();
        }
      });
    }
  } finally {
    if (prevVoice === undefined) delete process.env.OMALLA_DEMO_VOICE;
    else process.env.OMALLA_DEMO_VOICE = prevVoice;
    if (prevStt === undefined) delete process.env.OMALLA_DEMO_STT;
    else process.env.OMALLA_DEMO_STT = prevStt;
    await app.close();
    await runtime.close();
    await rm(dir, { recursive: true, force: true });
  }
});
