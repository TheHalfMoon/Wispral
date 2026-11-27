/**
 * Omalla WebRTC Signaling, ICE-Lite STUN Responder, RTP/SRTP (`PCMU`/`PCMA`)
 * Media Bridge, and DataChannel Control Model (`/v1/realtime/webrtc/*`).
 */
import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import dgram from "node:dgram";
import { OmallaError, newId, nowIso, type Call, type JsonValue } from "@omalla/core";
import {
  RTP_PT_PCMA,
  RTP_PT_PCMU,
  RTP_PT_TELEPHONE_EVENT,
  Rfc4733DtmfReceiver,
  SrtpContext,
  decodeRtpPacket,
  encodeRtpPacket,
  formatSdesCryptoAttribute,
  parseSdesLine,
  serializeSdesLine,
  type SdesCryptoAttribute,
} from "@omalla/telephony";
import type { OmallaRuntime } from "../runtime.js";
import { RealtimeDuplexSession } from "./session.js";

const STUN_MAGIC_COOKIE = 0x2112a442;
const STUN_BINDING_REQUEST = 0x0001;
const STUN_BINDING_RESPONSE = 0x0101;
const STUN_ATTR_XOR_MAPPED_ADDRESS = 0x0020;
const STUN_ATTR_MESSAGE_INTEGRITY = 0x0008;
const STUN_ATTR_FINGERPRINT = 0x8028;

export interface ParsedWebRtcOffer {
  iceUfrag: string;
  icePwd: string;
  fingerprint?: string;
  setup: string;
  codec: "pcmu" | "pcma";
  codecPt: number;
  telephoneEventPt: number;
  hasDataChannel: boolean;
  sctpPort: number;
  sdesCrypto?: SdesCryptoAttribute;
  candidates: string[];
}

export interface ManagedWebRtcSession {
  id: string;
  tenantId: string;
  agentId: string;
  callId: string;
  createdAt: string;
  localUdpPort: number;
  localIceUfrag: string;
  localIcePwd: string;
  codec: "pcmu" | "pcma";
  srtpEnabled: boolean;
  hasDataChannel: boolean;
  iceState: "new" | "checking" | "connected" | "closed";
  remoteCandidates: string[];
  latchedPeer: { address: string; port: number } | null;
  duplex: RealtimeDuplexSession;
  controlEvents: Array<Record<string, unknown>>;
  close: () => Promise<void>;
}

export function parseWebRtcSdpOffer(sdp: string): ParsedWebRtcOffer {
  if (!sdp.includes("v=0") || !sdp.includes("m=audio")) {
    throw new OmallaError("validation", "SDP offer must contain v=0 and an m=audio media section", 400);
  }
  let iceUfrag = "";
  let icePwd = "";
  let fingerprint: string | undefined;
  let setup = "actpass";
  let mediaProto = "RTP/AVP";
  let audioPts: number[] = [];
  let telephoneEventPt = RTP_PT_TELEPHONE_EVENT;
  let hasDataChannel = false;
  let sctpPort = 5000;
  let sdesCrypto: SdesCryptoAttribute | undefined;
  const candidates: string[] = [];

  for (const rawLine of sdp.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (line.startsWith("a=ice-ufrag:")) {
      iceUfrag = line.slice("a=ice-ufrag:".length).trim();
    } else if (line.startsWith("a=ice-pwd:")) {
      icePwd = line.slice("a=ice-pwd:".length).trim();
    } else if (line.startsWith("a=fingerprint:")) {
      fingerprint = line.slice("a=fingerprint:".length).trim();
    } else if (line.startsWith("a=setup:")) {
      setup = line.slice("a=setup:".length).trim();
    } else if (line.startsWith("m=audio ")) {
      const parts = line.slice(8).trim().split(/\s+/);
      mediaProto = parts[1] ?? "RTP/AVP";
      audioPts = parts.slice(2).map(Number).filter((n) => Number.isInteger(n));
    } else if (line.startsWith("m=application ")) {
      if (line.includes("webrtc-datachannel") || line.includes("DTLS/SCTP")) {
        hasDataChannel = true;
      }
    } else if (line.startsWith("a=sctp-port:")) {
      sctpPort = Number(line.slice("a=sctp-port:".length).trim()) || 5000;
      hasDataChannel = true;
    } else if (line.startsWith("a=crypto:")) {
      const parsed = parseSdesLine(line);
      if (parsed && !sdesCrypto) sdesCrypto = parsed;
    } else if (line.startsWith("a=rtpmap:")) {
      const teMatch = /^a=rtpmap:(\d+)\s+telephone-event\/8000/i.exec(line);
      if (teMatch?.[1]) telephoneEventPt = Number(teMatch[1]);
    } else if (line.startsWith("a=candidate:")) {
      candidates.push(line.slice(2));
    }
  }

  if (mediaProto.toUpperCase().includes("SAVP") && !sdesCrypto) {
    throw new OmallaError(
      "validation",
      `SDP audio profile ${mediaProto} requires an a=crypto SDES key attribute`,
      400,
    );
  }

  const prefersPcma =
    audioPts.includes(RTP_PT_PCMA) &&
    (!audioPts.includes(RTP_PT_PCMU) || audioPts.indexOf(RTP_PT_PCMA) < audioPts.indexOf(RTP_PT_PCMU));
  const codec: "pcmu" | "pcma" = prefersPcma ? "pcma" : "pcmu";
  const codecPt = codec === "pcma" ? RTP_PT_PCMA : RTP_PT_PCMU;

  return {
    iceUfrag,
    icePwd,
    ...(fingerprint ? { fingerprint } : {}),
    setup,
    codec,
    codecPt,
    telephoneEventPt,
    hasDataChannel,
    sctpPort,
    ...(sdesCrypto ? { sdesCrypto } : {}),
    candidates,
  };
}

/** Builds an RFC 5389 STUN Binding Request (used by WebRTC ICE-lite tests and peers). */
export function buildStunBindingRequest(username: string, password: string, transactionId = randomBytes(12)): Buffer {
  const userBytes = Buffer.from(username, "utf8");
  const paddedUserLen = Math.ceil(userBytes.length / 4) * 4;
  const userAttr = Buffer.alloc(4 + paddedUserLen, 0);
  userAttr.writeUInt16BE(0x0006, 0); // USERNAME
  userAttr.writeUInt16BE(userBytes.length, 2);
  userBytes.copy(userAttr, 4);

  const header = Buffer.alloc(20);
  header.writeUInt16BE(STUN_BINDING_REQUEST, 0);
  header.writeUInt32BE(STUN_MAGIC_COOKIE, 4);
  transactionId.copy(header, 8, 0, 12);

  // Length including MESSAGE-INTEGRITY (24 bytes) before FINGERPRINT
  header.writeUInt16BE(userAttr.length + 24, 2);
  const preIntegrity = Buffer.concat([header, userAttr]);
  const hmac = createHmac("sha1", password).update(preIntegrity).digest();
  const miAttr = Buffer.alloc(24);
  miAttr.writeUInt16BE(STUN_ATTR_MESSAGE_INTEGRITY, 0);
  miAttr.writeUInt16BE(20, 2);
  hmac.copy(miAttr, 4);

  // Update length to include FINGERPRINT (8 bytes)
  const withMi = Buffer.concat([preIntegrity, miAttr]);
  withMi.writeUInt16BE(userAttr.length + 24 + 8, 2);
  const fp = (crc32(withMi) ^ 0x5354554e) >>> 0;
  const fpAttr = Buffer.alloc(8);
  fpAttr.writeUInt16BE(STUN_ATTR_FINGERPRINT, 0);
  fpAttr.writeUInt16BE(4, 2);
  fpAttr.writeUInt32BE(fp, 4);

  return Buffer.concat([withMi, fpAttr]);
}

/**
 * Verifies an incoming RFC 5389 STUN Binding Request (`USERNAME` `${localIceUfrag}:*`
 * + constant-time `MESSAGE-INTEGRITY` HMAC-SHA1 over `localIcePwd`) BEFORE latching
 * any WebRTC peer address.
 */
export function verifyStunBindingRequest(
  pkt: Buffer,
  expectedLocalUfrag: string,
  localIcePwd: string,
): { valid: boolean; transactionId?: Uint8Array } {
  if (
    pkt.length < 20 ||
    pkt.readUInt16BE(0) !== STUN_BINDING_REQUEST ||
    pkt.readUInt32BE(4) !== STUN_MAGIC_COOKIE
  ) {
    return { valid: false };
  }
  const msgLen = pkt.readUInt16BE(2);
  if (20 + msgLen > pkt.length || msgLen % 4 !== 0) {
    return { valid: false };
  }

  let usernameOk = false;
  let integrityOk = false;
  let offset = 20;
  const end = 20 + msgLen;

  while (offset + 4 <= end) {
    const attrType = pkt.readUInt16BE(offset);
    const attrLen = pkt.readUInt16BE(offset + 2);
    const paddedLen = Math.ceil(attrLen / 4) * 4;
    if (offset + 4 + paddedLen > end || offset + 4 + attrLen > end) {
      return { valid: false };
    }

    if (attrType === 0x0006) {
      // USERNAME
      const username = pkt.subarray(offset + 4, offset + 4 + attrLen).toString("utf8");
      if (username === expectedLocalUfrag || username.startsWith(`${expectedLocalUfrag}:`)) {
        usernameOk = true;
      }
    } else if (attrType === STUN_ATTR_MESSAGE_INTEGRITY) {
      if (attrLen !== 20) return { valid: false };
      const preMi = Buffer.from(pkt.subarray(0, offset));
      preMi.writeUInt16BE(offset - 20 + 24, 2);
      const expectedHmac = createHmac("sha1", localIcePwd).update(preMi).digest();
      const providedHmac = pkt.subarray(offset + 4, offset + 24);
      if (providedHmac.length === expectedHmac.length && timingSafeEqual(providedHmac, expectedHmac)) {
        integrityOk = true;
      } else {
        return { valid: false };
      }
    }

    offset += 4 + paddedLen;
  }

  if (!usernameOk || !integrityOk) {
    return { valid: false };
  }
  return { valid: true, transactionId: pkt.subarray(8, 20) };
}

function buildStunBindingSuccessResponse(
  transactionId: Uint8Array,
  peerAddress: string,
  peerPort: number,
  icePassword: string,
): Buffer {
  // XOR-MAPPED-ADDRESS (IPv4)
  const ipParts = peerAddress.split(".").map((n) => Number(n) & 0xff);
  const ipUint32 =
    (((ipParts[0] ?? 127) << 24) |
      ((ipParts[1] ?? 0) << 16) |
      ((ipParts[2] ?? 0) << 8) |
      (ipParts[3] ?? 1)) >>>
    0;
  const xPort = (peerPort ^ (STUN_MAGIC_COOKIE >>> 16)) & 0xffff;
  const xAddr = (ipUint32 ^ STUN_MAGIC_COOKIE) >>> 0;

  const xorAttr = Buffer.alloc(12);
  xorAttr.writeUInt16BE(STUN_ATTR_XOR_MAPPED_ADDRESS, 0);
  xorAttr.writeUInt16BE(8, 2);
  xorAttr[4] = 0;
  xorAttr[5] = 0x01; // IPv4 family
  xorAttr.writeUInt16BE(xPort, 6);
  xorAttr.writeUInt32BE(xAddr, 8);

  const header = Buffer.alloc(20);
  header.writeUInt16BE(STUN_BINDING_RESPONSE, 0);
  header.writeUInt16BE(xorAttr.length + 24, 2);
  header.writeUInt32BE(STUN_MAGIC_COOKIE, 4);
  Buffer.from(transactionId).copy(header, 8, 0, 12);

  const preMi = Buffer.concat([header, xorAttr]);
  const hmac = createHmac("sha1", icePassword).update(preMi).digest();
  const miAttr = Buffer.alloc(24);
  miAttr.writeUInt16BE(STUN_ATTR_MESSAGE_INTEGRITY, 0);
  miAttr.writeUInt16BE(20, 2);
  hmac.copy(miAttr, 4);

  const withMi = Buffer.concat([preMi, miAttr]);
  withMi.writeUInt16BE(xorAttr.length + 24 + 8, 2);
  const fp = (crc32(withMi) ^ 0x5354554e) >>> 0;
  const fpAttr = Buffer.alloc(8);
  fpAttr.writeUInt16BE(STUN_ATTR_FINGERPRINT, 0);
  fpAttr.writeUInt16BE(4, 2);
  fpAttr.writeUInt32BE(fp, 4);

  return Buffer.concat([withMi, fpAttr]);
}

export class WebRtcSessionManager {
  private readonly sessions = new Map<string, ManagedWebRtcSession>();

  async negotiateOffer(input: {
    runtime: OmallaRuntime;
    tenantId: string;
    agentId: string;
    sdpOffer: string;
    sinkAckSupported?: boolean;
  }): Promise<{
    sessionId: string;
    callId: string;
    sdpAnswer: string;
    iceLite: true;
    localUdpPort: number;
    localIceUfrag: string;
    localIcePwd: string;
    codec: "pcmu" | "pcma";
    srtpSuite: string | null;
    candidates: string[];
  }> {
    const { runtime, tenantId, agentId } = input;
    const agent = runtime.db.col("agents").get(agentId);
    if (!agent || agent.tenantId !== tenantId) {
      throw new OmallaError("not_found", "agent not found", 404);
    }

    const parsedOffer = parseWebRtcSdpOffer(input.sdpOffer);
    const udp = dgram.createSocket("udp4");
    await new Promise<void>((resolve, reject) => {
      udp.once("error", reject);
      udp.bind(0, "127.0.0.1", () => {
        udp.off("error", reject);
        resolve();
      });
    });
    udp.unref();
    const localUdpPort = udp.address().port;

    const localIceUfrag = randomBytes(4).toString("hex");
    const localIcePwd = randomBytes(18).toString("base64url");
    const localFingerprint = formatSha256Fingerprint(randomBytes(32));

    let srtpRx: SrtpContext | null = null;
    let srtpTx: SrtpContext | null = null;
    let answerCrypto: SdesCryptoAttribute | null = null;
    if (parsedOffer.sdesCrypto) {
      srtpRx = new SrtpContext(parsedOffer.sdesCrypto.keyMaterial);
      answerCrypto = formatSdesCryptoAttribute(parsedOffer.sdesCrypto.tag);
      srtpTx = new SrtpContext(answerCrypto.keyMaterial);
    }

    const now = nowIso();
    const call: Call = {
      id: newId("call"),
      tenantId,
      direction: "inbound",
      status: "ringing",
      from: "webrtc:client",
      to: `agent:${agent.id}`,
      agentId: agent.id,
      agentVersion: agent.version,
      startedAt: now,
      transcript: [],
      messages: [],
      variables: {},
      metadata: {
        transport: "webrtc",
        callerNumberVerified: false,
      },
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
    runtime.db.col("calls").insert(call);

    const { engine, stt } = await runtime.buildConversation(call, agent);
    const sessionId = newId("rtc");
    const controlEvents: Array<Record<string, unknown>> = [];
    const ssrc = randomBytes(4).readUInt32BE(0);
    const dtmfReceiver = new Rfc4733DtmfReceiver();
    let startedGreeting = false;
    let managed!: ManagedWebRtcSession;

    const duplex = new RealtimeDuplexSession({
      sessionId,
      engine,
      stt,
      codec: parsedOffer.codec,
      sampleRate: 8000,
      language: agent.config.language,
      sinkAckSupported: input.sinkAckSupported ?? true,
      logger: runtime.logger.child({ component: "webrtc", sessionId, callId: call.id }),
      sink: {
        bufferedAmount: 0,
        sendJson: (ev) => {
          controlEvents.push(ev);
          if (controlEvents.length > 250) controlEvents.shift();
          const peer = managed?.latchedPeer;
          if (peer) {
            const dcFrame = Buffer.concat([
              Buffer.from("OMDC", "ascii"),
              Buffer.from(JSON.stringify(ev), "utf8"),
            ]);
            try {
              udp.send(dcFrame, peer.port, peer.address);
            } catch {
              // ignore closed socket
            }
          }
        },
        sendBinaryAudio: (frameBytes, meta) => {
          const peer = managed?.latchedPeer;
          if (!peer) return;
          const rtp = encodeRtpPacket(
            {
              marker: meta.seq === 0,
              payloadType: parsedOffer.codecPt,
              sequenceNumber: meta.seq,
              timestamp: meta.timestamp,
              ssrc,
            },
            frameBytes,
          );
          const wire = srtpTx ? srtpTx.protect(rtp) : rtp;
          try {
            udp.send(wire, peer.port, peer.address);
          } catch {
            // ignore closed socket
          }
        },
        close: () => {
          void managed.close();
        },
      },
    });

    const maxDurationTimer = setTimeout(() => {
      void managed?.close();
    }, Math.max(30, agent.config.maxDurationSec) * 1000);
    maxDurationTimer.unref?.();

    managed = {
      id: sessionId,
      tenantId,
      agentId,
      callId: call.id,
      createdAt: now,
      localUdpPort,
      localIceUfrag,
      localIcePwd,
      codec: parsedOffer.codec,
      srtpEnabled: Boolean(srtpRx && srtpTx),
      hasDataChannel: parsedOffer.hasDataChannel,
      iceState: "checking",
      remoteCandidates: parsedOffer.candidates.slice(0, 32),
      latchedPeer: null,
      duplex,
      controlEvents,
      close: async () => {
        if (managed.iceState === "closed") return;
        managed.iceState = "closed";
        clearTimeout(maxDurationTimer);
        this.sessions.delete(sessionId);
        await duplex.close("customer_ended");
        await new Promise<void>((resolve) => {
          try {
            udp.close(() => resolve());
          } catch {
            resolve();
          }
        });
      },
    };

    udp.on("message", (pkt, rinfo) => {
      if (managed.iceState === "closed") return;

      // 1. RFC 5389 STUN Binding Request (verified USERNAME + constant-time MESSAGE-INTEGRITY)
      if (
        pkt.length >= 20 &&
        pkt.readUInt16BE(0) === STUN_BINDING_REQUEST &&
        pkt.readUInt32BE(4) === STUN_MAGIC_COOKIE
      ) {
        const verified = verifyStunBindingRequest(pkt, localIceUfrag, localIcePwd);
        if (!verified.valid || !verified.transactionId) {
          return;
        }
        const stunRes = buildStunBindingSuccessResponse(
          verified.transactionId,
          rinfo.address,
          rinfo.port,
          localIcePwd,
        );
        managed.latchedPeer = { address: rinfo.address, port: rinfo.port };
        managed.iceState = "connected";
        udp.send(stunRes, rinfo.port, rinfo.address);
        if (!startedGreeting) {
          startedGreeting = true;
          void duplex.start();
        }
        return;
      }

      // 2. Local DataChannel control frame ("OMDC" + JSON)
      if (
        pkt.length > 4 &&
        pkt[0] === 0x4f &&
        pkt[1] === 0x4d &&
        pkt[2] === 0x44 &&
        pkt[3] === 0x43
      ) {
        if (
          managed.latchedPeer &&
          managed.latchedPeer.address === rinfo.address &&
          managed.latchedPeer.port === rinfo.port
        ) {
          void duplex.handleControlMessage(pkt.subarray(4).toString("utf8"));
        }
        return;
      }

      // 3. RTP / SRTP media packet
      if (pkt.length >= 12 && ((pkt[0] ?? 0) & 0xc0) === 0x80) {
        try {
          const decoded = srtpRx ? srtpRx.unprotect(pkt).packet : decodeRtpPacket(pkt);
          if (!managed.latchedPeer) {
            managed.latchedPeer = { address: rinfo.address, port: rinfo.port };
            managed.iceState = "connected";
          } else if (
            managed.latchedPeer.address !== rinfo.address ||
            managed.latchedPeer.port !== rinfo.port
          ) {
            return;
          }
          if (!startedGreeting) {
            startedGreeting = true;
            void duplex.start();
          }
          if (decoded.header.payloadType === parsedOffer.telephoneEventPt) {
            const digits = dtmfReceiver.push(decoded, parsedOffer.telephoneEventPt);
            for (const digit of digits) {
              void duplex.handleControlMessage({ type: "dtmf", digit });
            }
            return;
          }
          duplex.handleBinaryFrame(
            new Uint8Array(decoded.payload),
            decoded.header.sequenceNumber,
          );
        } catch {
          // Invalid SRTP tag, replay, or malformed RTP dropped
        }
      }
    });

    this.sessions.set(sessionId, managed);

    const candidateLine = `candidate:1 1 udp 2130706431 127.0.0.1 ${localUdpPort} typ host`;
    const answerProto = answerCrypto
      ? "RTP/SAVP"
      : input.sdpOffer.includes("UDP/TLS/RTP/SAVPF")
        ? "UDP/TLS/RTP/SAVPF"
        : "RTP/AVP";
    const codecRtpmap =
      parsedOffer.codec === "pcma" ? "a=rtpmap:8 PCMA/8000" : "a=rtpmap:0 PCMU/8000";

    const sdpLines = [
      "v=0",
      `o=omalla-webrtc ${Date.now()} 2 IN IP4 127.0.0.1`,
      "s=Omalla Realtime WebRTC",
      "t=0 0",
      "a=ice-lite",
      ...(parsedOffer.hasDataChannel ? ["a=group:BUNDLE 0 1"] : ["a=group:BUNDLE 0"]),
      `m=audio ${localUdpPort} ${answerProto} ${parsedOffer.codecPt} ${parsedOffer.telephoneEventPt}`,
      "c=IN IP4 127.0.0.1",
      "a=mid:0",
      `a=ice-ufrag:${localIceUfrag}`,
      `a=ice-pwd:${localIcePwd}`,
      `a=fingerprint:sha-256 ${localFingerprint}`,
      `a=setup:${parsedOffer.setup === "active" ? "passive" : "passive"}`,
      codecRtpmap,
      `a=rtpmap:${parsedOffer.telephoneEventPt} telephone-event/8000`,
      `a=fmtp:${parsedOffer.telephoneEventPt} 0-15`,
      "a=ptime:20",
      "a=sendrecv",
      `a=${candidateLine}`,
      ...(answerCrypto ? [serializeSdesLine(answerCrypto)] : []),
    ];

    if (parsedOffer.hasDataChannel) {
      sdpLines.push(
        `m=application ${localUdpPort} UDP/DTLS/SCTP webrtc-datachannel`,
        "c=IN IP4 127.0.0.1",
        "a=mid:1",
        `a=ice-ufrag:${localIceUfrag}`,
        `a=ice-pwd:${localIcePwd}`,
        `a=fingerprint:sha-256 ${localFingerprint}`,
        "a=setup:passive",
        `a=sctp-port:${parsedOffer.sctpPort}`,
        `a=${candidateLine}`,
      );
    }

    return {
      sessionId,
      callId: call.id,
      sdpAnswer: `${sdpLines.join("\r\n")}\r\n`,
      iceLite: true,
      localUdpPort,
      localIceUfrag,
      localIcePwd,
      codec: parsedOffer.codec,
      srtpSuite: answerCrypto ? answerCrypto.suite : null,
      candidates: [candidateLine],
    };
  }

  getOwned(tenantId: string, sessionId: string): ManagedWebRtcSession {
    const s = this.sessions.get(sessionId);
    if (!s || s.tenantId !== tenantId) {
      throw new OmallaError("not_found", "WebRTC session not found", 404);
    }
    return s;
  }

  addIceCandidate(tenantId: string, sessionId: string, candidate: string): { accepted: boolean; count: number } {
    const s = this.getOwned(tenantId, sessionId);
    const trimmed = candidate.trim().replace(/^a=/, "");
    if (!trimmed.startsWith("candidate:")) {
      throw new OmallaError("validation", "invalid ICE candidate attribute", 400);
    }
    if (s.remoteCandidates.length >= 32) {
      throw new OmallaError("validation", "maximum ICE candidate limit (32) reached", 400);
    }
    s.remoteCandidates.push(trimmed);

    // Parse loopback UDP host candidate if peer has not latched via STUN yet
    const match = /^candidate:\S+\s+\d+\s+udp\s+\d+\s+(127\.\d+\.\d+\.\d+)\s+(\d+)\s+typ\s+host/i.exec(
      trimmed,
    );
    if (match?.[1] && match[2] && !s.latchedPeer) {
      s.latchedPeer = { address: match[1], port: Number(match[2]) };
    }
    return { accepted: true, count: s.remoteCandidates.length };
  }

  countForTenant(tenantId: string): number {
    let n = 0;
    for (const s of this.sessions.values()) {
      if (s.tenantId === tenantId && s.iceState !== "closed") n += 1;
    }
    return n;
  }

  async closeAll(): Promise<void> {
    await Promise.all([...this.sessions.values()].map((s) => s.close()));
  }
}

function formatSha256Fingerprint(seed: Uint8Array): string {
  const hex = createHash("sha256").update(seed).digest("hex").toUpperCase();
  const pairs: string[] = [];
  for (let i = 0; i < hex.length; i += 2) {
    pairs.push(hex.slice(i, i + 2));
  }
  return pairs.join(":");
}

const CRC32_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i += 1) {
    let c = i;
    for (let k = 0; k < 8; k += 1) {
      c = (c & 1) !== 0 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[i] = c >>> 0;
  }
  return table;
})();

function crc32(buf: Uint8Array): number {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i += 1) {
    const idx = (crc ^ (buf[i] ?? 0)) & 0xff;
    crc = (CRC32_TABLE[idx]! ^ (crc >>> 8)) >>> 0;
  }
  return (crc ^ 0xffffffff) >>> 0;
}

export type { JsonValue };
