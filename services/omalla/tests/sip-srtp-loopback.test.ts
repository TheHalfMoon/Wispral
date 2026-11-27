import assert from "node:assert/strict";
import { createHmac, createSign, generateKeyPairSync } from "node:crypto";
import dgram from "node:dgram";
import { test } from "node:test";
import {
  RTP_PT_PCMU,
  Rfc4733DtmfReceiver,
  SipLoopbackPeer,
  SipStack,
  SipTelephonyProvider,
  SrtpContext,
  SrtpError,
  TelnyxProvider,
  VonageProvider,
  buildRfc4733DigitBurst,
  buildSdp,
  computeSipDigestResponse,
  decodeMulaw,
  decodeRtpPacket,
  encodeMulaw,
  encodeRtpHeader,
  encodeRtpPacket,
  formatSdesCryptoAttribute,
  generateSrtpKeyMaterial,
  parseSipMessage,
  serializeSipMessage,
} from "@omalla/telephony";

/**
 * Generates an ephemeral in-memory self-signed X.509 v3 RSA-2048 TLS certificate
 * using pure `node:crypto` + ASN.1 DER (zero external CLI or static repo keys!).
 */
function createEphemeralSelfSignedTlsCert(): { keyPem: string; certPem: string } {
  const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const spkiDer = publicKey.export({ type: "spki", format: "der" }) as Buffer;
  const keyPem = privateKey.export({ type: "pkcs8", format: "pem" }) as string;

  const derLen = (len: number): Buffer => {
    if (len < 128) return Buffer.from([len]);
    const hex = len.toString(16).padStart(len > 255 ? 4 : 2, "0");
    const bytes = Buffer.from(hex, "hex");
    return Buffer.concat([Buffer.from([0x80 | bytes.length]), bytes]);
  };
  const tlv = (tag: number, body: Buffer): Buffer => Buffer.concat([Buffer.from([tag]), derLen(body.length), body]);
  const seq = (...items: Buffer[]) => tlv(0x30, Buffer.concat(items));
  const set = (...items: Buffer[]) => tlv(0x31, Buffer.concat(items));
  const oid = (bytes: number[]) => tlv(0x06, Buffer.from(bytes));
  const utf8 = (str: string) => tlv(0x0c, Buffer.from(str, "utf8"));
  const utcTime = (d: Date) => {
    const pad = (n: number) => String(n).padStart(2, "0");
    const s = `${String(d.getUTCFullYear()).slice(-2)}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}${pad(d.getUTCSeconds())}Z`;
    return tlv(0x17, Buffer.from(s, "ascii"));
  };

  // sha256WithRSAEncryption (1.2.840.113549.1.1.11)
  const algId = seq(oid([0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x0b]), Buffer.from([0x05, 0x00]));
  // CN=127.0.0.1 (2.5.4.3)
  const name = seq(set(seq(oid([0x55, 0x04, 0x03]), utf8("127.0.0.1"))));
  const now = new Date();
  const validity = seq(
    utcTime(new Date(now.getTime() - 60_000)),
    utcTime(new Date(now.getTime() + 86_400_000)),
  );
  const serial = tlv(0x02, Buffer.from([0x01, 0x23, 0x45, 0x67, 0x89]));
  const versionV3 = tlv(0xa0, tlv(0x02, Buffer.from([0x02])));
  // SubjectAltName (2.5.29.17) -> iPAddress 127.0.0.1 (0x87 0x04 7f 00 00 01) + dNSName localhost
  const sanValue = seq(
    tlv(0x87, Buffer.from([127, 0, 0, 1])),
    tlv(0x82, Buffer.from("localhost", "ascii")),
  );
  const sanExt = seq(oid([0x55, 0x1d, 0x11]), tlv(0x04, sanValue));
  const extensions = tlv(0xa3, seq(sanExt));

  const tbs = seq(versionV3, serial, algId, name, validity, name, spkiDer, extensions);
  const signer = createSign("RSA-SHA256");
  signer.update(tbs);
  const sig = signer.sign(privateKey);
  const bitStringSig = tlv(0x03, Buffer.concat([Buffer.from([0x00]), sig]));
  const certDer = seq(tbs, algId, bitStringSig);
  const b64 = certDer.toString("base64").replace(/(.{64})/g, "$1\n").trim();
  const certPem = `-----BEGIN CERTIFICATE-----\n${b64}\n-----END CERTIFICATE-----\n`;
  return { keyPem, certPem };
}

test("SRTP AES_CM_128_HMAC_SHA1_80 round-trips PCMU audio and rejects tampered tags & replayed packets", () => {
  const material = generateSrtpKeyMaterial();
  const sender = new SrtpContext(material);
  const receiver = new SrtpContext(material);

  const pcmSamples = new Int16Array(160);
  for (let i = 0; i < 160; i += 1) pcmSamples[i] = (i * 180) - 14000;
  const mulaw = encodeMulaw(pcmSamples);

  const cleartextRtp = encodeRtpPacket(
    {
      marker: true,
      payloadType: RTP_PT_PCMU,
      sequenceNumber: 500,
      timestamp: 8000,
      ssrc: 0x12345678,
    },
    mulaw,
  );

  const srtp = sender.protect(cleartextRtp);
  assert.equal(srtp.length, cleartextRtp.length + 10, "80-bit (10-byte) auth tag appended");
  assert.notDeepEqual(
    srtp.subarray(12, 12 + mulaw.length),
    mulaw,
    "SRTP payload MUST be encrypted, not cleartext",
  );

  // 1. Tampered ciphertext byte MUST fail HMAC-SHA1-80 verification before replay commit!
  const tampered = new Uint8Array(srtp);
  tampered[20] = (tampered[20] ?? 0) ^ 0xff;
  assert.throws(
    () => receiver.unprotect(tampered),
    (err: unknown) => err instanceof SrtpError && err.code === "auth_failed",
  );

  // 2. Authentic packet still succeeds because failed auth did not advance replay window
  const unprotected = receiver.unprotect(srtp);
  assert.deepEqual(unprotected.packet.payload, mulaw);
  assert.equal(decodeMulaw(unprotected.packet.payload).length, 160);

  // 3. Exact replay of sequence 500 MUST be rejected!
  assert.throws(
    () => receiver.unprotect(srtp),
    (err: unknown) => err instanceof SrtpError && err.code === "replay_detected",
  );

  // 4. Advance window by 70 packets, then old packet outside 64-packet window is rejected
  const oldPkt = sender.protect(
    encodeRtpPacket(
      { marker: false, payloadType: RTP_PT_PCMU, sequenceNumber: 501, timestamp: 8160, ssrc: 0x12345678 },
      mulaw,
    ),
  );
  for (let seq = 502; seq <= 570; seq += 1) {
    const p = sender.protect(
      encodeRtpPacket(
        { marker: false, payloadType: RTP_PT_PCMU, sequenceNumber: seq, timestamp: seq * 160, ssrc: 0x12345678 },
        mulaw,
      ),
    );
    receiver.unprotect(p);
  }
  assert.throws(
    () => receiver.unprotect(oldPkt),
    (err: unknown) => err instanceof SrtpError && err.code === "replay_detected",
  );

  // 5. RFC 3711 §3.1: P=1 padded RTP packet encrypts & decrypts padding inside SRTP payload!
  const padBytes = new Uint8Array([0x00, 0x00, 0x00, 0x04]);
  const paddedHdr = encodeRtpHeader({
    version: 2,
    padding: true,
    extension: false,
    csrcCount: 0,
    marker: false,
    payloadType: RTP_PT_PCMU,
    sequenceNumber: 571,
    timestamp: 571 * 160,
    ssrc: 0x12345678,
  });
  const paddedRtp = new Uint8Array(paddedHdr.length + mulaw.length + padBytes.length);
  paddedRtp.set(paddedHdr, 0);
  paddedRtp.set(mulaw, paddedHdr.length);
  paddedRtp.set(padBytes, paddedHdr.length + mulaw.length);

  const paddedSrtp = sender.protect(paddedRtp);
  assert.equal(paddedSrtp.length, paddedRtp.length + 10);
  const paddedUnprotected = receiver.unprotect(paddedSrtp);
  assert.deepEqual(paddedUnprotected.rtpBytes, paddedRtp);
  assert.equal(paddedUnprotected.packet.header.padding, true);
  assert.deepEqual(paddedUnprotected.packet.payload, mulaw);
});

test("RFC 4733 telephone-event receiver deduplicates 3x redundant E=1 end packets so digits are never double-counted", () => {
  const receiver = new Rfc4733DtmfReceiver();
  const emitted: string[] = [];
  let seq = 10;
  let ts = 1600;

  for (const digit of ["1", "8", "*", "0", "#"]) {
    const burst = buildRfc4733DigitBurst({
      digit,
      ssrc: 0x99887766,
      startSeq: seq,
      eventTimestamp: ts,
    });
    assert.equal(burst.packets.length, 5, "burst contains 2 interim + 3 E=1 packets");
    seq = burst.nextSeq;
    ts = burst.nextTimestamp;

    for (const raw of burst.packets) {
      const pkt = decodeRtpPacket(raw);
      emitted.push(...receiver.push(pkt));
      // Network duplicate of every packet!
      emitted.push(...receiver.push(pkt));
    }
  }

  assert.equal(emitted.join(""), "18*0#");
});

test("OM-T7: SipStack enforces loopback default bind, refuses non-loopback cleartext SDES & gateway token, and accepts sips: TLS", async () => {
  // 1. Non-loopback bind without allowRemoteBind throws immediately
  assert.throws(() => new SipStack({ host: "0.0.0.0" }), /OM-T7/);

  const rejections: Array<{ reason: string; peerIp: string }> = [];
  const stack = new SipStack({ gatewayToken: "super-secret-gateway-token-1234" });
  stack.on("security.rejected", (ev) => rejections.push({ reason: ev.reason, peerIp: ev.peerIp }));

  const sdesOffer = buildSdp({
    ip: "203.0.113.55",
    mediaPort: 40000,
    srtp: formatSdesCryptoAttribute(1),
  });

  // 2. Non-loopback INVITE carrying SDES a=crypto: over cleartext UDP -> 488 rejected!
  const udpReplies: string[] = [];
  await stack.handleIncomingMessage(
    serializeSipMessage({
      kind: "request",
      method: "INVITE",
      uri: "sip:ava@198.51.100.1:5060",
      version: "SIP/2.0",
      headers: {
        via: ["SIP/2.0/UDP 203.0.113.55:5060;branch=z9hG4bK1"],
        from: ["<sip:caller@203.0.113.55>;tag=t1"],
        to: ["<sip:ava@198.51.100.1>"],
        "call-id": ["call_omt7_sdes"],
        cseq: ["1 INVITE"],
        "content-type": ["application/sdp"],
      },
      body: sdesOffer,
    }),
    { address: "203.0.113.55", port: 5060, transport: "udp" },
    (wire) => udpReplies.push(wire),
  );
  const sdesRes = parseSipMessage(udpReplies[0]!);
  assert.equal(sdesRes.kind, "response");
  assert.equal(sdesRes.statusCode, 488);
  assert.equal(rejections.length, 1);

  // 3. Non-loopback OPTIONS carrying x-omalla-gateway-token over cleartext TCP -> 403 rejected!
  const tcpReplies: string[] = [];
  await stack.handleIncomingMessage(
    serializeSipMessage({
      kind: "request",
      method: "OPTIONS",
      uri: "sip:ava@198.51.100.1:5060",
      version: "SIP/2.0",
      headers: {
        via: ["SIP/2.0/TCP 203.0.113.55:5060;branch=z9hG4bK2"],
        from: ["<sip:gw@203.0.113.55>;tag=t2"],
        to: ["<sip:ava@198.51.100.1>"],
        "call-id": ["call_omt7_tok"],
        cseq: ["1 OPTIONS"],
        "x-omalla-gateway-token": ["super-secret-gateway-token-1234"],
      },
      body: "",
    }),
    { address: "203.0.113.55", port: 5060, transport: "tcp" },
    (wire) => tcpReplies.push(wire),
  );
  const tokRes = parseSipMessage(tcpReplies[0]!);
  assert.equal(tokRes.kind, "response");
  assert.equal(tokRes.statusCode, 403);

  // 4. Non-loopback INVITE without SRTP (plain RTP/AVP) even over TLS -> 488 rejected!
  const plainRtpSdp = buildSdp({ ip: "203.0.113.55", mediaPort: 40002 });
  const tlsPlainReplies: string[] = [];
  await stack.handleIncomingMessage(
    serializeSipMessage({
      kind: "request",
      method: "INVITE",
      uri: "sips:ava@198.51.100.1:5061",
      version: "SIP/2.0",
      headers: {
        via: ["SIP/2.0/TLS 203.0.113.55:5061;branch=z9hG4bK3"],
        from: ["<sips:caller@203.0.113.55>;tag=t3"],
        to: ["<sips:ava@198.51.100.1>"],
        "call-id": ["call_omt7_plainrtp"],
        cseq: ["1 INVITE"],
        "x-omalla-gateway-token": ["super-secret-gateway-token-1234"],
        "content-type": ["application/sdp"],
      },
      body: plainRtpSdp,
    }),
    { address: "203.0.113.55", port: 5061, transport: "tls" },
    (wire) => tlsPlainReplies.push(wire),
  );
  const plainRes = parseSipMessage(tlsPlainReplies[0]!);
  assert.equal(plainRes.kind, "response");
  assert.equal(plainRes.statusCode, 488);

  // 5. Non-loopback INVITE over sips: TLS WITH SRTP + valid gateway token -> 100/180/200 OK accepted!
  const tlsGoodReplies: string[] = [];
  await stack.handleIncomingMessage(
    serializeSipMessage({
      kind: "request",
      method: "INVITE",
      uri: "sips:ava@198.51.100.1:5061",
      version: "SIP/2.0",
      headers: {
        via: ["SIP/2.0/TLS 203.0.113.55:5061;branch=z9hG4bK4"],
        from: ["<sips:caller@203.0.113.55>;tag=t4"],
        to: ["<sips:ava@198.51.100.1>"],
        "call-id": ["call_omt7_ok"],
        cseq: ["1 INVITE"],
        "x-omalla-gateway-token": ["super-secret-gateway-token-1234"],
        "content-type": ["application/sdp"],
      },
      body: sdesOffer,
    }),
    { address: "203.0.113.55", port: 5061, transport: "tls" },
    (wire) => tlsGoodReplies.push(wire),
  );
  const statuses = tlsGoodReplies.map((w) => {
    const p = parseSipMessage(w);
    return p.kind === "response" ? p.statusCode : 0;
  });
  assert.deepEqual(statuses, [100, 180, 200]);

  await stack.close();
});

test("Full REGISTER (SHA-256 Digest) + INVITE -> 200 OK -> ACK -> SRTP audio + DTMF + symmetric latch + REFER warm transfer + BYE over 127.0.0.1 UDP and sips: TLS", async () => {
  const { keyPem, certPem } = createEphemeralSelfSignedTlsCert();
  const stack = new SipStack({
    host: "127.0.0.1",
    udpPort: 0,
    tlsPort: 0,
    tlsOptions: { key: keyPem, cert: certPem },
    digestAuth: {
      realm: "omalla.local",
      users: { trunk1: "s3cr3t-pass" },
    },
    gatewayToken: "loopback-gw-token-987654321",
  });

  const receivedStackAudio: Uint8Array[] = [];
  const receivedDtmf: string[] = [];
  const receivedRefers: Array<{ referTo: string; mode: string; replaces?: string }> = [];
  let endedReason = "";

  stack.on("call.audio", ({ callId, payload }) => {
    receivedStackAudio.push(payload);
    // Echo back encrypted SRTP audio to SipLoopbackPeer!
    stack.sendAudioFrame(callId, payload);
  });
  stack.on("call.dtmf", ({ digit }) => receivedDtmf.push(digit));
  stack.on("call.refer", (ev) => receivedRefers.push(ev));
  stack.on("call.ended", ({ reason }) => {
    endedReason = reason;
  });

  const ports = await stack.start();
  assert.ok(ports.udpPort && ports.tlsPort);

  const peer = new SipLoopbackPeer();
  await peer.bind();

  try {
    // 1. REGISTER over UDP using SHA-256 Digest challenge-response
    const regRes = await peer.register({
      targetPort: ports.udpPort,
      username: "trunk1",
      password: "s3cr3t-pass",
      transport: "udp",
    });
    assert.equal(regRes.statusCode, 200);
    assert.equal(stack.getRegistrations().size, 1);

    // 2. Place call over UDP with gateway token + SDES SRTP
    const call = await peer.placeCall({
      targetPort: ports.udpPort,
      gatewayToken: "loopback-gw-token-987654321",
      transport: "udp",
    });

    // Verify spoofed unauthenticated UDP packet from rogue socket CANNOT hijack symmetric latch!
    const dialog = stack.getDialog(call.callId)!;
    const rogue = dgram.createSocket("udp4");
    await new Promise<void>((r) => rogue.bind(0, "127.0.0.1", () => r()));
    rogue.send(Buffer.alloc(32, 0x80), dialog.localMediaPort, "127.0.0.1");
    await new Promise((r) => setTimeout(r, 25));
    assert.equal(dialog.latchedPeer, undefined, "unauthenticated packet MUST NOT latch RTP peer");
    await new Promise<void>((r) => rogue.close(() => r()));

    // 3. Exchange real encrypted SRTP μ-law frames & RFC 4733 DTMF bursts
    const toneFrame = new Uint8Array(160).fill(0x5a);
    peer.sendSrtpMulawFrame(toneFrame);
    peer.sendSrtpDtmfDigit("7");
    peer.sendSrtpDtmfDigit("#");

    // Wait briefly for local loopback UDP delivery
    for (let i = 0; i < 40 && (call.receivedAudioFrames.length === 0 || receivedDtmf.length < 2); i += 1) {
      await new Promise((r) => setTimeout(r, 15));
    }

    assert.equal(receivedStackAudio.length, 1);
    assert.deepEqual(receivedStackAudio[0], toneFrame);
    assert.equal(call.receivedAudioFrames.length, 1);
    assert.deepEqual(call.receivedAudioFrames[0], toneFrame);
    assert.deepEqual(receivedDtmf, ["7", "#"], "3x E=1 DTMF bursts deduplicated to single digits");

    // 4. Execute warm REFER transfer (with ?Replaces=...)
    const referRes = await peer.refer(ports.udpPort, "sip:specialist@127.0.0.1:5090", {
      warmReplacesCallId: "consult_leg_42",
      gatewayToken: "loopback-gw-token-987654321",
    });
    assert.equal(referRes.statusCode, 202);
    assert.equal(receivedRefers.length, 1);
    assert.equal(receivedRefers[0]!.mode, "warm");
    assert.equal(receivedRefers[0]!.replaces, "consult_leg_42");

    // 5. Hangup with BYE -> 200 OK
    const byeRes = await peer.hangup(ports.udpPort, {
      gatewayToken: "loopback-gw-token-987654321",
    });
    assert.equal(byeRes.statusCode, 200);
    assert.equal(endedReason, "bye");

    // 6. Verify real `sips:` TLS call signaling over `node:tls`!
    const tlsPeer = new SipLoopbackPeer();
    await tlsPeer.bind();
    await tlsPeer.connectTls(ports.tlsPort, certPem);
    const tlsCall = await tlsPeer.placeCall({
      targetPort: ports.tlsPort,
      gatewayToken: "loopback-gw-token-987654321",
      transport: "tls",
    });
    assert.ok(tlsCall.remoteMediaPort > 0);
    const tlsBye = await tlsPeer.hangup(ports.tlsPort, {
      gatewayToken: "loopback-gw-token-987654321",
      transport: "tls",
    });
    assert.equal(tlsBye.statusCode, 200);
    await tlsPeer.close();
  } finally {
    await peer.close();
    await stack.close();
  }
});

test("Telnyx (Ed25519 + raw-byte), Vonage (Bearer JWT + payload_hash), and SipTelephonyProvider (OM-T7) carrier adapters", async () => {
  // 1. Telnyx Ed25519 webhook verification + transfer API
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  const pubPem = publicKey.export({ type: "spki", format: "pem" }) as string;
  const privPem = privateKey.export({ type: "pkcs8", format: "pem" }) as string;
  const fixedNow = 1_750_000_000;

  const telnyxCalls: Array<{ url: string; body: Record<string, unknown> }> = [];
  const telnyx = new TelnyxProvider({
    apiKey: "KEY_TELNYX_TEST",
    connectionId: "conn_123",
    publicKey: pubPem,
    nowSec: () => fixedNow,
    fetchImpl: async (input, init) => {
      telnyxCalls.push({
        url: String(input),
        body: init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : {},
      });
      return new Response(JSON.stringify({ data: { call_control_id: "v3:cc_1", state: "initiated" } }), {
        status: 200,
      });
    },
  });

  const rawTelnyxJson = JSON.stringify({
    data: {
      event_type: "call.initiated",
      payload: {
        call_control_id: "v3:cc_1",
        from: "+15550001111",
        to: "+15550002222",
        direction: "incoming",
      },
    },
  });
  const sigHeaders = TelnyxProvider.signWebhookPayload(rawTelnyxJson, fixedNow, {
    ed25519PrivateKeyPem: privPem,
  });

  assert.equal(
    telnyx.verifyWebhook({
      url: "https://omalla.example.com/telephony/telnyx/voice",
      method: "POST",
      headers: sigHeaders,
      form: {},
      rawBody: Buffer.from(rawTelnyxJson, "utf8"),
      json: JSON.parse(rawTelnyxJson) as Record<string, unknown>,
    }).valid,
    true,
  );

  // Tampering raw bytes by 1 space invalidates Ed25519 signature!
  assert.equal(
    telnyx.verifyWebhook({
      url: "https://omalla.example.com/telephony/telnyx/voice",
      method: "POST",
      headers: sigHeaders,
      form: {},
      rawBody: Buffer.from(`${rawTelnyxJson} `, "utf8"),
    }).valid,
    false,
  );

  await telnyx.transferCall("v3:cc_1", { to: "sip:agent2@pbx.example.com", mode: "warm" });
  assert.match(telnyxCalls[0]!.url, /\/v2\/calls\/v3%3Acc_1\/actions\/transfer$/);
  assert.equal(telnyxCalls[0]!.body.park_after_unbridge, "self");

  // 2. Vonage HS256 Bearer JWT + SHA-256 payload_hash + NCCO transfer
  const vonageCalls: Array<{ url: string; method: string; body: Record<string, unknown> }> = [];
  const vonage = new VonageProvider({
    apiKey: "vk_1",
    apiSecret: "vs_super_secret_key_1234",
    applicationId: "app_1",
    nowSec: () => fixedNow,
    fetchImpl: async (input, init) => {
      vonageCalls.push({
        url: String(input),
        method: init?.method ?? "GET",
        body: init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : {},
      });
      return new Response(JSON.stringify({ uuid: "von_call_1", status: "started" }), { status: 200 });
    },
  });

  const rawVonageBody = JSON.stringify({
    uuid: "von_call_1",
    from: "15550003333",
    to: "15550004444",
    direction: "inbound",
  });
  const bearer = VonageProvider.signWebhookJwt(rawVonageBody, "vs_super_secret_key_1234", {
    iat: fixedNow,
  });

  assert.equal(
    vonage.verifyWebhook({
      url: "https://omalla.example.com/telephony/vonage/voice",
      method: "POST",
      headers: { authorization: bearer },
      form: {},
      rawBody: Buffer.from(rawVonageBody, "utf8"),
      json: JSON.parse(rawVonageBody) as Record<string, unknown>,
    }).valid,
    true,
  );
  assert.equal(
    vonage.verifyWebhook({
      url: "https://omalla.example.com/telephony/vonage/voice",
      method: "POST",
      headers: { authorization: bearer },
      form: {},
      rawBody: Buffer.from(`${rawVonageBody} `, "utf8"),
    }).valid,
    false,
  );

  const ncco = JSON.parse(
    vonage.renderInboundResponse({
      say: "Welcome",
      mediaStreamUrl: "wss://omalla.example.com/telephony/vonage/media",
    }).body,
  ) as Array<Record<string, unknown>>;
  assert.equal(ncco[0]!.action, "talk");
  assert.equal(ncco[1]!.action, "connect");

  await vonage.redirectCall("von_call_1", "sip:warm@pbx.example.com");
  assert.equal(vonageCalls[0]!.method, "PUT");
  assert.match(vonageCalls[0]!.url, /\/v1\/calls\/von_call_1$/);

  // 3. SipTelephonyProvider OM-T7 cleartext non-loopback token rejection
  const sipProv = new SipTelephonyProvider({
    gatewayUrl: "http://127.0.0.1:5080",
    gatewayToken: "gw-secret-token-123456",
  });
  assert.equal(
    sipProv.verifyWebhook({
      url: "http://sip-public.example.com/telephony/sip/voice",
      method: "POST",
      headers: { "x-omalla-gateway-token": "gw-secret-token-123456" },
      form: {},
    }).valid,
    false,
    "non-loopback HTTP cleartext gateway token MUST be rejected per OM-T7",
  );
  // Forged X-Forwarded-Proto: https on http:// URL MUST NOT bypass OM-T7!
  assert.equal(
    sipProv.verifyWebhook({
      url: "http://sip-public.example.com/telephony/sip/voice",
      method: "POST",
      headers: {
        "x-omalla-gateway-token": "gw-secret-token-123456",
        "x-forwarded-proto": "https",
      },
      form: {},
    }).valid,
    false,
  );
  assert.equal(
    sipProv.verifyWebhook({
      url: "https://sip-public.example.com/telephony/sip/voice",
      method: "POST",
      headers: { "x-omalla-gateway-token": "gw-secret-token-123456" },
      form: {},
    }).valid,
    true,
  );

  // Outbound gatewayRequest refuses cleartext non-loopback HTTP when gatewayToken is set
  const unsafeRemoteSip = new SipTelephonyProvider({
    gatewayUrl: "http://sip-public.example.com:5080",
    gatewayToken: "gw-secret-token-123456",
    fetchImpl: async () => new Response("{}", { status: 200 }),
  });
  await assert.rejects(
    () =>
      unsafeRemoteSip.createCall({
        to: "+15550001111",
        from: "+15550002222",
        answerUrl: "https://omalla.example.com/telephony/sip/voice",
      }),
    /OM-T7/,
  );

  // Vonage JWT without iat or without payload_hash on non-empty body MUST be rejected!
  const makeCustomJwt = (claimsObj: Record<string, unknown>) => {
    const h = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" }), "utf8").toString("base64url");
    const p = Buffer.from(JSON.stringify(claimsObj), "utf8").toString("base64url");
    const s = createHmac("sha256", "vs_super_secret_key_1234").update(`${h}.${p}`, "utf8").digest("base64url");
    return `Bearer ${h}.${p}.${s}`;
  };
  assert.equal(
    vonage.verifyWebhook({
      url: "https://omalla.example.com/telephony/vonage/voice",
      method: "POST",
      headers: { authorization: makeCustomJwt({ jti: "no_iat" }) },
      form: {},
      rawBody: Buffer.from(rawVonageBody, "utf8"),
    }).valid,
    false,
  );
  assert.equal(
    vonage.verifyWebhook({
      url: "https://omalla.example.com/telephony/vonage/voice",
      method: "POST",
      headers: { authorization: makeCustomJwt({ iat: fixedNow, jti: "no_payload_hash" }) },
      form: {},
      rawBody: Buffer.from(rawVonageBody, "utf8"),
    }).valid,
    false,
  );
});

test("OM-T7 SipStack hardening: allowRemoteBind auth gate, empty non-loopback INVITE 488, single-use Digest nonce + URI match, CANCEL answered guard & duplicate Call-ID retransmit", async () => {
  // 1. allowRemoteBind: true without gatewayToken or digestAuth throws
  assert.throws(() => new SipStack({ host: "0.0.0.0", allowRemoteBind: true }), /allowRemoteBind requires/);

  const stack = new SipStack({
    digestAuth: { realm: "omalla.local", users: { u1: "pw123" } },
  });

  // 2. Empty-body non-loopback INVITE -> 488
  const emptyInvReplies: string[] = [];
  await stack.handleIncomingMessage(
    serializeSipMessage({
      kind: "request",
      method: "INVITE",
      uri: "sips:ava@198.51.100.1:5061",
      version: "SIP/2.0",
      headers: {
        via: ["SIP/2.0/TLS 203.0.113.55:5061;branch=z9hG4bKempty"],
        from: ["<sips:caller@203.0.113.55>;tag=te1"],
        to: ["<sips:ava@198.51.100.1>"],
        "call-id": ["call_empty_inv"],
        cseq: ["1 INVITE"],
      },
      body: "",
    }),
    { address: "203.0.113.55", port: 5061, transport: "tls" },
    (w) => emptyInvReplies.push(w),
  );
  const emptyInvRes = parseSipMessage(emptyInvReplies[0]!);
  assert.equal(emptyInvRes.kind, "response");
  assert.equal(emptyInvRes.statusCode, 488);

  // 3. Digest single-use nonce + URI mismatch rejection
  const chReplies: string[] = [];
  await stack.handleIncomingMessage(
    serializeSipMessage({
      kind: "request",
      method: "REGISTER",
      uri: "sip:127.0.0.1:5060",
      version: "SIP/2.0",
      headers: {
        via: ["SIP/2.0/UDP 127.0.0.1:5099;branch=z9hG4bKc1"],
        from: ["<sip:u1@127.0.0.1>;tag=tr1"],
        to: ["<sip:u1@127.0.0.1>"],
        "call-id": ["reg_nonce_1"],
        cseq: ["1 REGISTER"],
      },
      body: "",
    }),
    { address: "127.0.0.1", port: 5099, transport: "udp" },
    (w) => chReplies.push(w),
  );
  const chMsg = parseSipMessage(chReplies[0]!);
  assert.equal(chMsg.kind, "response");
  assert.equal(chMsg.statusCode, 401);
  const nonce = /nonce="([^"]+)"/.exec(chMsg.headers["www-authenticate"]?.[0] ?? "")?.[1] ?? "";
  assert.ok(nonce);

  // URI mismatch in Authorization header -> 403 Forbidden (does NOT consume valid nonce)
  const badUriHash = computeSipDigestResponse({
    username: "u1",
    realm: "omalla.local",
    password: "pw123",
    method: "REGISTER",
    uri: "sip:other.example:5060",
    nonce,
    algorithm: "SHA-256",
  });
  const badUriReplies: string[] = [];
  await stack.handleIncomingMessage(
    serializeSipMessage({
      kind: "request",
      method: "REGISTER",
      uri: "sip:127.0.0.1:5060",
      version: "SIP/2.0",
      headers: {
        via: ["SIP/2.0/UDP 127.0.0.1:5099;branch=z9hG4bKc2"],
        from: ["<sip:u1@127.0.0.1>;tag=tr1"],
        to: ["<sip:u1@127.0.0.1>"],
        "call-id": ["reg_nonce_1"],
        cseq: ["2 REGISTER"],
        authorization: [
          `Digest username="u1", realm="omalla.local", nonce="${nonce}", uri="sip:other.example:5060", response="${badUriHash}", algorithm=SHA-256`,
        ],
      },
      body: "",
    }),
    { address: "127.0.0.1", port: 5099, transport: "udp" },
    (w) => badUriReplies.push(w),
  );
  const badUriRes = parseSipMessage(badUriReplies[0]!);
  assert.equal(badUriRes.kind, "response");
  assert.equal(badUriRes.statusCode, 403);

  // Valid Digest REGISTER succeeds once, then replaying same nonce triggers fresh 401 challenge!
  const goodHash = computeSipDigestResponse({
    username: "u1",
    realm: "omalla.local",
    password: "pw123",
    method: "REGISTER",
    uri: "sip:127.0.0.1:5060",
    nonce,
    algorithm: "SHA-256",
  });
  const regReq = serializeSipMessage({
    kind: "request",
    method: "REGISTER",
    uri: "sip:127.0.0.1:5060",
    version: "SIP/2.0",
    headers: {
      via: ["SIP/2.0/UDP 127.0.0.1:5099;branch=z9hG4bKc3"],
      from: ["<sip:u1@127.0.0.1>;tag=tr1"],
      to: ["<sip:u1@127.0.0.1>"],
      "call-id": ["reg_nonce_1"],
      cseq: ["3 REGISTER"],
      authorization: [
        `Digest username="u1", realm="omalla.local", nonce="${nonce}", uri="sip:127.0.0.1:5060", response="${goodHash}", algorithm=SHA-256`,
      ],
    },
    body: "",
  });
  const okReplies: string[] = [];
  await stack.handleIncomingMessage(regReq, { address: "127.0.0.1", port: 5099, transport: "udp" }, (w) =>
    okReplies.push(w),
  );
  assert.equal((parseSipMessage(okReplies[0]!) as { statusCode: number }).statusCode, 200);

  const replayReplies: string[] = [];
  await stack.handleIncomingMessage(regReq, { address: "127.0.0.1", port: 5099, transport: "udp" }, (w) =>
    replayReplies.push(w),
  );
  assert.equal((parseSipMessage(replayReplies[0]!) as { statusCode: number }).statusCode, 401);

  // 4. Duplicate Call-ID INVITE retransmission reuses existing dialog & CANCEL on answered dialog returns 481
  const tokStack = new SipStack({ gatewayToken: "tok-cancel-guard-12345" });
  const invWire = serializeSipMessage({
    kind: "request",
    method: "INVITE",
    uri: "sip:ava@127.0.0.1:5060",
    version: "SIP/2.0",
    headers: {
      via: ["SIP/2.0/UDP 127.0.0.1:5088;branch=z9hG4bKi1"],
      from: ["<sip:caller@127.0.0.1>;tag=tag_orig"],
      to: ["<sip:ava@127.0.0.1>"],
      "call-id": ["call_dup_cancel"],
      cseq: ["1 INVITE"],
      "x-omalla-gateway-token": ["tok-cancel-guard-12345"],
      "content-type": ["application/sdp"],
    },
    body: buildSdp({ ip: "127.0.0.1", mediaPort: 41000 }),
  });
  const invReplies1: string[] = [];
  await tokStack.handleIncomingMessage(invWire, { address: "127.0.0.1", port: 5088, transport: "udp" }, (w) =>
    invReplies1.push(w),
  );
  const origPort = tokStack.getDialog("call_dup_cancel")!.localMediaPort;

  const invReplies2: string[] = [];
  await tokStack.handleIncomingMessage(invWire, { address: "127.0.0.1", port: 5088, transport: "udp" }, (w) =>
    invReplies2.push(w),
  );
  assert.equal(tokStack.getDialog("call_dup_cancel")!.localMediaPort, origPort);
  assert.equal((parseSipMessage(invReplies2[0]!) as { statusCode: number }).statusCode, 200);

  // CANCEL on already-answered dialog MUST return 481 and NOT tear down active call!
  const cancelReplies: string[] = [];
  await tokStack.handleIncomingMessage(
    serializeSipMessage({
      kind: "request",
      method: "CANCEL",
      uri: "sip:ava@127.0.0.1:5060",
      version: "SIP/2.0",
      headers: {
        via: ["SIP/2.0/UDP 127.0.0.1:5088;branch=z9hG4bKi1"],
        from: ["<sip:caller@127.0.0.1>;tag=tag_orig"],
        to: ["<sip:ava@127.0.0.1>"],
        "call-id": ["call_dup_cancel"],
        cseq: ["1 CANCEL"],
        "x-omalla-gateway-token": ["tok-cancel-guard-12345"],
      },
      body: "",
    }),
    { address: "127.0.0.1", port: 5088, transport: "udp" },
    (w) => cancelReplies.push(w),
  );
  assert.equal((parseSipMessage(cancelReplies[0]!) as { statusCode: number }).statusCode, 481);
  assert.equal(tokStack.getDialog("call_dup_cancel")?.state, "answered");

  await tokStack.close();
  await stack.close();
});
