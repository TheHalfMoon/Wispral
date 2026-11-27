/**
 * Pure-TypeScript RFC 3261 SIP Stack over UDP, TCP, and TLS (`sips:` via `node:tls`).
 *
 * Supported methods:
 *  - `REGISTER`, `INVITE` (`100 Trying`, `180 Ringing`, `200 OK`), `ACK`,
 *    `BYE`, `CANCEL`, `OPTIONS`, `REFER` (warm/cold transfer + `NOTIFY`), `NOTIFY`
 *  - RFC 2617 / RFC 7616 HTTP Digest Auth (`MD5` & `SHA-256`, `qop="auth"`)
 *  - `x-omalla-gateway-token` constant-time authentication
 *
 * Security invariants (`OM-T7`):
 *  - Default bind host is `127.0.0.1`.
 *  - Refuses non-loopback SDES (`a=crypto:`) or `x-omalla-gateway-token` unless
 *    transported over `sips:` TLS (`node:tls`) or `attestedEncryptedTunnel === true`.
 *  - Requires `SRTP` (`RTP/SAVP` or `UDP/TLS/RTP/SAVPF`) on non-loopback media.
 *  - Enforces symmetric RTP latching ONLY after authenticated SDP + valid SRTP tag!
 */
import { createHash, randomBytes, timingSafeEqual } from "node:crypto";
import dgram from "node:dgram";
import net from "node:net";
import tls from "node:tls";
import { Emitter } from "@omalla/core";
import {
  RTP_PT_PCMA,
  RTP_PT_PCMU,
  RTP_PT_TELEPHONE_EVENT,
  Rfc4733DtmfReceiver,
  decodeRtpPacket,
  encodeRtpPacket,
} from "./rtp.js";
import {
  SrtpContext,
  formatSdesCryptoAttribute,
  parseSdesLine,
  serializeSdesLine,
  type SdesCryptoAttribute,
} from "./srtp.js";

export type SipTransportKind = "udp" | "tcp" | "tls";

export interface SipRequestMessage {
  kind: "request";
  method: string;
  uri: string;
  version: string;
  headers: Record<string, string[]>;
  body: string;
}

export interface SipResponseMessage {
  kind: "response";
  version: string;
  statusCode: number;
  reasonPhrase: string;
  headers: Record<string, string[]>;
  body: string;
}

export type SipMessage = SipRequestMessage | SipResponseMessage;

export interface ParsedSdp {
  connectionIp: string;
  mediaPort: number;
  mediaProto: string;
  payloadTypes: number[];
  sdesCrypto?: SdesCryptoAttribute;
  telephoneEventPt: number;
}

export interface SipPeerAddress {
  address: string;
  port: number;
  transport: SipTransportKind;
}

export interface SipDigestCredentials {
  realm: string;
  users: Record<string, string>; // username -> plaintext password (or pre-hashed in prod)
}

export interface SipDialog {
  callId: string;
  fromUri: string;
  toUri: string;
  localTag: string;
  remoteTag: string;
  peer: SipPeerAddress;
  state: "ringing" | "answered" | "confirmed" | "terminated";
  localMediaPort: number;
  remoteMediaIp: string;
  remoteMediaPort: number;
  latchedPeer?: { address: string; port: number };
  srtpTx?: SrtpContext;
  srtpRx?: SrtpContext;
  answerCrypto?: SdesCryptoAttribute;
  telephoneEventPt?: number;
  mediaSocket: dgram.Socket;
  dtmfReceiver: Rfc4733DtmfReceiver;
  txSeq: number;
  txTimestamp: number;
  txSsrc: number;
  codecPt: number;
  transferTarget?: string;
  transferMode?: "warm" | "blind";
}

export interface SipStackEvents {
  "register": { aor: string; contact: string; expiresSec: number };
  "call.ringing": { callId: string; from: string; to: string; transport: SipTransportKind };
  "call.answered": { callId: string; localMediaPort: number; srtp: boolean };
  "call.confirmed": { callId: string };
  "call.audio": { callId: string; payloadType: number; payload: Uint8Array; seq: number; timestamp: number };
  "call.dtmf": { callId: string; digit: string };
  "call.refer": { callId: string; referTo: string; mode: "warm" | "blind"; replaces?: string };
  "call.ended": { callId: string; reason: "bye" | "cancel" | "refer" };
  "security.rejected": { reason: string; peerIp: string; transport: SipTransportKind };
}

export interface SipStackOptions {
  /** Defaults strictly to 127.0.0.1 per OM-T7. */
  host?: string;
  allowRemoteBind?: boolean;
  udpPort?: number;
  tcpPort?: number;
  tlsPort?: number;
  tlsOptions?: tls.TlsOptions;
  /** Explicit operator attestation that a local loopback/WireGuard/IPsec SBC terminates TLS. */
  attestedEncryptedTunnel?: boolean;
  gatewayToken?: string;
  digestAuth?: SipDigestCredentials;
  autoAnswer?: boolean;
}

const COMPACT_HEADERS: Record<string, string> = {
  v: "via",
  f: "from",
  t: "to",
  i: "call-id",
  m: "contact",
  c: "content-type",
  l: "content-length",
};

export function isLoopbackIp(ip: string): boolean {
  const clean = ip.replace(/^\[|\]$/g, "").toLowerCase();
  if (clean === "127.0.0.1" || clean === "::1" || clean === "localhost") return true;
  if (clean.startsWith("127.")) return true;
  if (clean.startsWith("::ffff:127.")) return true;
  return false;
}

export function parseSipMessage(raw: string): SipMessage {
  const sepIdx = raw.indexOf("\r\n\r\n");
  const fallbackIdx = sepIdx < 0 ? raw.indexOf("\n\n") : -1;
  const headerPart =
    sepIdx >= 0 ? raw.slice(0, sepIdx) : fallbackIdx >= 0 ? raw.slice(0, fallbackIdx) : raw;
  const body =
    sepIdx >= 0 ? raw.slice(sepIdx + 4) : fallbackIdx >= 0 ? raw.slice(fallbackIdx + 2) : "";

  const lines = headerPart.split(/\r?\n/);
  const startLine = (lines.shift() ?? "").trim();
  if (!startLine) throw new Error("empty SIP message");

  const headers: Record<string, string[]> = {};
  for (const line of lines) {
    if (!line.trim()) continue;
    const colon = line.indexOf(":");
    if (colon <= 0) continue;
    const rawName = line.slice(0, colon).trim().toLowerCase();
    const canonical = COMPACT_HEADERS[rawName] ?? rawName;
    const val = line.slice(colon + 1).trim();
    headers[canonical] = [...(headers[canonical] ?? []), val];
  }

  if (startLine.startsWith("SIP/")) {
    const match = /^(SIP\/\d+\.\d+)\s+(\d{3})\s*(.*)$/.exec(startLine);
    if (!match) throw new Error(`malformed SIP status line: ${startLine}`);
    return {
      kind: "response",
      version: match[1] ?? "SIP/2.0",
      statusCode: Number(match[2]),
      reasonPhrase: match[3] ?? "",
      headers,
      body,
    };
  }

  const parts = startLine.split(/\s+/);
  if (parts.length < 3) throw new Error(`malformed SIP request line: ${startLine}`);
  return {
    kind: "request",
    method: (parts[0] ?? "").toUpperCase(),
    uri: parts[1] ?? "",
    version: parts[2] ?? "SIP/2.0",
    headers,
    body,
  };
}

export function serializeSipMessage(message: SipMessage): string {
  const bodyBytes = Buffer.byteLength(message.body, "utf8");
  const start =
    message.kind === "request"
      ? `${message.method} ${message.uri} ${message.version}`
      : `${message.version} ${message.statusCode} ${message.reasonPhrase}`;

  const headerLines: string[] = [];
  const entries = { ...message.headers };
  entries["content-length"] = [String(bodyBytes)];

  for (const [name, values] of Object.entries(entries)) {
    const proper = formatHeaderName(name);
    for (const val of values) {
      headerLines.push(`${proper}: ${val}`);
    }
  }

  return `${start}\r\n${headerLines.join("\r\n")}\r\n\r\n${message.body}`;
}

function formatHeaderName(lower: string): string {
  const special: Record<string, string> = {
    "call-id": "Call-ID",
    cseq: "CSeq",
    "www-authenticate": "WWW-Authenticate",
    "content-type": "Content-Type",
    "content-length": "Content-Length",
    "max-forwards": "Max-Forwards",
    "refer-to": "Refer-To",
    "referred-by": "Referred-By",
    "subscription-state": "Subscription-State",
  };
  if (special[lower]) return special[lower]!;
  return lower
    .split("-")
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join("-");
}

export function parseSdp(sdp: string): ParsedSdp {
  let connectionIp = "127.0.0.1";
  let mediaPort = 0;
  let mediaProto = "RTP/AVP";
  let payloadTypes: number[] = [];
  let sdesCrypto: SdesCryptoAttribute | undefined;
  let telephoneEventPt = RTP_PT_TELEPHONE_EVENT;

  for (const rawLine of sdp.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (line.startsWith("c=IN IP")) {
      const parts = line.split(/\s+/);
      if (parts[2]) connectionIp = parts[2].split("/")[0] ?? connectionIp;
    } else if (line.startsWith("m=audio ")) {
      const parts = line.slice(8).trim().split(/\s+/);
      mediaPort = Number(parts[0] ?? 0);
      mediaProto = parts[1] ?? "RTP/AVP";
      payloadTypes = parts.slice(2).map(Number).filter((n) => Number.isInteger(n));
    } else if (line.startsWith("a=crypto:")) {
      const parsed = parseSdesLine(line);
      if (parsed && !sdesCrypto) sdesCrypto = parsed;
    } else if (line.startsWith("a=rtpmap:")) {
      const match = /^a=rtpmap:(\d+)\s+telephone-event\/8000/i.exec(line);
      if (match?.[1]) telephoneEventPt = Number(match[1]);
    }
  }

  return {
    connectionIp,
    mediaPort,
    mediaProto,
    payloadTypes,
    ...(sdesCrypto ? { sdesCrypto } : {}),
    telephoneEventPt,
  };
}

export function buildSdp(input: {
  ip: string;
  mediaPort: number;
  srtp?: SdesCryptoAttribute;
  payloadTypes?: number[];
  sessionId?: string;
}): string {
  const sid = input.sessionId ?? String(Date.now());
  const proto = input.srtp ? "RTP/SAVP" : "RTP/AVP";
  const pts = input.payloadTypes ?? [RTP_PT_PCMU, RTP_PT_PCMA, RTP_PT_TELEPHONE_EVENT];
  const addrType = net.isIP(input.ip) === 6 ? "IP6" : "IP4";
  const lines = [
    "v=0",
    `o=omalla ${sid} ${sid} IN ${addrType} ${input.ip}`,
    "s=Omalla SIP Media",
    `c=IN ${addrType} ${input.ip}`,
    "t=0 0",
    `m=audio ${input.mediaPort} ${proto} ${pts.join(" ")}`,
    "a=rtpmap:0 PCMU/8000",
    "a=rtpmap:8 PCMA/8000",
    "a=rtpmap:101 telephone-event/8000",
    "a=fmtp:101 0-15",
    "a=ptime:20",
    "a=sendrecv",
  ];
  if (input.srtp) {
    lines.push(serializeSdesLine(input.srtp));
  }
  return `${lines.join("\r\n")}\r\n`;
}

/** Computes RFC 2617 / RFC 7616 Digest response (`MD5` or `SHA-256`). */
export function computeSipDigestResponse(input: {
  username: string;
  realm: string;
  password: string;
  method: string;
  uri: string;
  nonce: string;
  algorithm?: "MD5" | "SHA-256";
  qop?: string;
  nc?: string;
  cnonce?: string;
}): string {
  const alg = input.algorithm === "SHA-256" ? "sha256" : "md5";
  const hash = (text: string) => createHash(alg).update(text, "utf8").digest("hex");
  const ha1 = hash(`${input.username}:${input.realm}:${input.password}`);
  const ha2 = hash(`${input.method}:${input.uri}`);
  if (input.qop === "auth" && input.nc && input.cnonce) {
    return hash(`${ha1}:${input.nonce}:${input.nc}:${input.cnonce}:${input.qop}:${ha2}`);
  }
  return hash(`${ha1}:${input.nonce}:${ha2}`);
}

export class SipStack {
  private readonly events = new Emitter<SipStackEvents>();
  private readonly bindHost: string;
  private udpSocket: dgram.Socket | null = null;
  private tcpServer: net.Server | null = null;
  private tlsServer: tls.Server | null = null;
  private readonly streamConnections = new Set<net.Socket>();
  private readonly dialogs = new Map<string, SipDialog>();
  private readonly registrations = new Map<string, { contact: string; expiresAtMs: number }>();
  private readonly nonces = new Map<string, number>();
  private closed = false;

  constructor(private readonly options: SipStackOptions = {}) {
    const requestedHost = options.host ?? "127.0.0.1";
    if (!isLoopbackIp(requestedHost) && options.allowRemoteBind !== true) {
      throw new Error("OM-T7: SipStack refuses non-loopback bind unless allowRemoteBind is explicitly set");
    }
    if (options.allowRemoteBind === true && !options.gatewayToken && !options.digestAuth) {
      throw new Error("OM-T7: allowRemoteBind requires gatewayToken or digestAuth");
    }
    this.bindHost = requestedHost;
  }

  on<K extends keyof SipStackEvents>(event: K, handler: (payload: SipStackEvents[K]) => void): () => void {
    return this.events.on(event, handler);
  }

  async start(): Promise<{ udpPort?: number; tcpPort?: number; tlsPort?: number; host: string }> {
    const ports: { udpPort?: number; tcpPort?: number; tlsPort?: number; host: string } = {
      host: this.bindHost,
    };

    if (this.options.udpPort !== undefined || (this.options.tcpPort === undefined && this.options.tlsPort === undefined)) {
      const sock = dgram.createSocket("udp4");
      this.udpSocket = sock;
      sock.on("message", (msg, rinfo) => {
        void this.onRawDatagram(msg, {
          address: rinfo.address,
          port: rinfo.port,
          transport: "udp",
        });
      });
      await new Promise<void>((resolve, reject) => {
        sock.once("error", reject);
        sock.bind(this.options.udpPort ?? 0, this.bindHost, () => {
          sock.off("error", reject);
          resolve();
        });
      });
      sock.unref();
      ports.udpPort = sock.address().port;
    }

    if (this.options.tcpPort !== undefined) {
      const server = net.createServer((socket) => this.attachStreamSocket(socket, "tcp"));
      this.tcpServer = server;
      await new Promise<void>((resolve, reject) => {
        server.once("error", reject);
        server.listen(this.options.tcpPort, this.bindHost, () => {
          server.off("error", reject);
          resolve();
        });
      });
      const addr = server.address();
      if (addr && typeof addr === "object") ports.tcpPort = addr.port;
    }

    if (this.options.tlsPort !== undefined && this.options.tlsOptions) {
      const server = tls.createServer(this.options.tlsOptions, (socket) =>
        this.attachStreamSocket(socket, "tls"),
      );
      this.tlsServer = server;
      await new Promise<void>((resolve, reject) => {
        server.once("error", reject);
        server.listen(this.options.tlsPort, this.bindHost, () => {
          server.off("error", reject);
          resolve();
        });
      });
      const addr = server.address();
      if (addr && typeof addr === "object") ports.tlsPort = addr.port;
    }

    return ports;
  }

  getDialog(callId: string): SipDialog | undefined {
    return this.dialogs.get(callId);
  }

  getRegistrations(): ReadonlyMap<string, { contact: string; expiresAtMs: number }> {
    return this.registrations;
  }

  /** Sends one 20 ms G.711 frame (`PCMU` or `PCMA`) encrypted with SRTP (if negotiated) to the active dialog. */
  sendAudioFrame(callId: string, audioBytes: Uint8Array, marker = false): boolean {
    const dialog = this.dialogs.get(callId);
    if (!dialog || (dialog.state !== "answered" && dialog.state !== "confirmed")) return false;
    const dest = dialog.latchedPeer ?? { address: dialog.remoteMediaIp, port: dialog.remoteMediaPort };
    if (!dest.port) return false;

    const rtp = encodeRtpPacket(
      {
        marker,
        payloadType: dialog.codecPt,
        sequenceNumber: dialog.txSeq,
        timestamp: dialog.txTimestamp,
        ssrc: dialog.txSsrc,
      },
      audioBytes,
    );
    dialog.txSeq = (dialog.txSeq + 1) & 0xffff;
    dialog.txTimestamp = (dialog.txTimestamp + audioBytes.length) >>> 0;

    const wire = dialog.srtpTx ? dialog.srtpTx.protect(rtp) : rtp;
    dialog.mediaSocket.send(wire, dest.port, dest.address);
    return true;
  }

  /** Evaluates OM-T7 transport/media security posture for an incoming SIP request. */
  evaluateOmT7(
    req: SipRequestMessage,
    peer: SipPeerAddress,
  ): { allowed: boolean; statusCode?: number; reason?: string } {
    const peerIsLoopback = isLoopbackIp(peer.address);
    const isEncryptedSignaling = peer.transport === "tls" || this.options.attestedEncryptedTunnel === true;

    const hasGatewayToken = Boolean(req.headers["x-omalla-gateway-token"]?.[0]);
    const hasSdesKeyInSdp = /(?:^|\r?\n)a=crypto:/i.test(req.body);

    // OM-T7 rule 1: refuse non-loopback SDES key material or x-omalla-gateway-token over cleartext UDP/TCP!
    if (!peerIsLoopback && !isEncryptedSignaling && (hasGatewayToken || hasSdesKeyInSdp)) {
      return {
        allowed: false,
        statusCode: hasGatewayToken ? 403 : 488,
        reason:
          "OM-T7: non-loopback SDES key material and x-omalla-gateway-token require sips: TLS or an attested encrypted tunnel",
      };
    }

    // OM-T7 rule 2: non-loopback INVITE MUST carry an SDP offer and negotiate SRTP!
    if (req.method === "INVITE") {
      if (!peerIsLoopback && req.body.trim().length === 0) {
        return {
          allowed: false,
          statusCode: 488,
          reason: "OM-T7: non-loopback SIP INVITE requires an SRTP SDP offer",
        };
      }
      if (req.body.trim().length > 0) {
        const sdp = parseSdp(req.body);
        const mediaLoopback = isLoopbackIp(sdp.connectionIp) && peerIsLoopback;
        const isSrtpProto = sdp.mediaProto.includes("SAVP");
        if (!mediaLoopback && (!isSrtpProto || !sdp.sdesCrypto)) {
          return {
            allowed: false,
            statusCode: 488,
            reason: "OM-T7: non-loopback SIP media requires SRTP",
          };
        }
      }
    }

    return { allowed: true };
  }

  /** Entry point exposed for both live sockets and adversarial OM-T7 unit tests. */
  async handleIncomingMessage(
    rawText: string,
    peer: SipPeerAddress,
    replyFn: (wire: string) => void,
  ): Promise<void> {
    let msg: SipMessage;
    try {
      msg = parseSipMessage(rawText);
    } catch {
      return;
    }
    if (msg.kind === "response") return;

    const omT7 = this.evaluateOmT7(msg, peer);
    if (!omT7.allowed) {
      this.events.emit("security.rejected", {
        reason: omT7.reason ?? "OM-T7 violation",
        peerIp: peer.address,
        transport: peer.transport,
      });
      replyFn(
        serializeSipMessage(
          this.makeResponse(
            msg,
            omT7.statusCode ?? 488,
            omT7.statusCode === 403 ? "Forbidden" : "Not Acceptable Here",
            {},
            "",
            { "x-omalla-security": [omT7.reason ?? "OM-T7"] },
          ),
        ),
      );
      return;
    }

    if (!this.authenticateRequest(msg, replyFn)) {
      return;
    }

    switch (msg.method) {
      case "OPTIONS":
        replyFn(
          serializeSipMessage(
            this.makeResponse(msg, 200, "OK", {}, "", {
              allow: ["INVITE, ACK, BYE, CANCEL, OPTIONS, REGISTER, REFER, NOTIFY"],
            }),
          ),
        );
        return;

      case "REGISTER":
        this.handleRegister(msg, replyFn);
        return;

      case "INVITE":
        await this.handleInvite(msg, peer, replyFn);
        return;

      case "ACK":
        this.handleAck(msg);
        return;

      case "CANCEL":
        this.handleCancel(msg, peer, replyFn);
        return;

      case "REFER":
        this.handleRefer(msg, peer, replyFn);
        return;

      case "NOTIFY":
        replyFn(serializeSipMessage(this.makeResponse(msg, 200, "OK")));
        return;

      case "BYE":
        this.handleBye(msg, replyFn);
        return;

      default:
        replyFn(serializeSipMessage(this.makeResponse(msg, 501, "Not Implemented")));
    }
  }

  async close(): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    for (const dialog of this.dialogs.values()) {
      try {
        dialog.mediaSocket.close();
      } catch {
        // ignore
      }
    }
    this.dialogs.clear();
    for (const conn of this.streamConnections) {
      conn.destroy();
    }
    this.streamConnections.clear();

    await Promise.all([
      this.udpSocket
        ? new Promise<void>((resolve) => {
            this.udpSocket?.close(() => resolve());
          })
        : Promise.resolve(),
      this.tcpServer
        ? new Promise<void>((resolve) => {
            this.tcpServer?.close(() => resolve());
          })
        : Promise.resolve(),
      this.tlsServer
        ? new Promise<void>((resolve) => {
            this.tlsServer?.close(() => resolve());
          })
        : Promise.resolve(),
    ]);
  }

  /* ------------------------------------------------------------------ */

  private async onRawDatagram(buf: Buffer, peer: SipPeerAddress): Promise<void> {
    await this.handleIncomingMessage(buf.toString("utf8"), peer, (wire) => {
      this.udpSocket?.send(Buffer.from(wire, "utf8"), peer.port, peer.address);
    });
  }

  private attachStreamSocket(socket: net.Socket, transport: "tcp" | "tls"): void {
    this.streamConnections.add(socket);
    const maxStreamBytes = 64 * 1024;
    let rawBuf = Buffer.alloc(0);
    const peer: SipPeerAddress = {
      address: socket.remoteAddress ?? "127.0.0.1",
      port: socket.remotePort ?? 0,
      transport,
    };

    socket.on("data", (chunk: Buffer) => {
      if (rawBuf.length + chunk.length > maxStreamBytes) {
        socket.destroy();
        return;
      }
      rawBuf = Buffer.concat([rawBuf, chunk]);
      while (true) {
        const headerEnd = rawBuf.indexOf("\r\n\r\n");
        if (headerEnd < 0) break;
        const headerBlock = rawBuf.subarray(0, headerEnd).toString("utf8");
        const clMatch = /(?:^|\r?\n)(?:content-length|l)\s*:\s*(\d+)/i.exec(headerBlock);
        const contentLen = clMatch?.[1] ? Number(clMatch[1]) : 0;
        if (contentLen > maxStreamBytes) {
          socket.destroy();
          return;
        }
        const totalBytesNeeded = headerEnd + 4 + contentLen;
        if (rawBuf.length < totalBytesNeeded) break;

        const exactBody = rawBuf.subarray(headerEnd + 4, totalBytesNeeded).toString("utf8");
        rawBuf = rawBuf.subarray(totalBytesNeeded);
        const fullMessage = `${headerBlock}\r\n\r\n${exactBody}`;

        void this.handleIncomingMessage(fullMessage, peer, (wire) => {
          if (!socket.destroyed) socket.write(wire, "utf8");
        });
      }
    });

    socket.on("close", () => {
      this.streamConnections.delete(socket);
    });
    socket.on("error", () => {
      this.streamConnections.delete(socket);
    });
  }

  private authenticateRequest(req: SipRequestMessage, replyFn: (wire: string) => void): boolean {
    if (req.method === "ACK" || req.method === "OPTIONS") {
      return true;
    }

    if (this.options.gatewayToken) {
      const presented = req.headers["x-omalla-gateway-token"]?.[0] ?? "";
      const expectedBuf = Buffer.from(this.options.gatewayToken, "utf8");
      const presentedBuf = Buffer.from(presented, "utf8");
      if (presentedBuf.length === expectedBuf.length && timingSafeEqual(presentedBuf, expectedBuf)) {
        return true;
      }
      if (!this.options.digestAuth) {
        replyFn(serializeSipMessage(this.makeResponse(req, 403, "Forbidden")));
        return false;
      }
    }

    if (!this.options.digestAuth) {
      return true;
    }

    const authHeader = req.headers.authorization?.[0];
    const { realm, users } = this.options.digestAuth;
    if (!authHeader || !authHeader.toLowerCase().startsWith("digest ")) {
      return this.sendDigestChallenge(req, realm, replyFn);
    }

    const params = parseAuthParams(authHeader.slice(7));
    const username = params.username ?? "";
    const nonce = params.nonce ?? "";
    const responseHash = params.response ?? "";
    const uri = params.uri ?? "";
    if (!uri || uri !== req.uri) {
      replyFn(serializeSipMessage(this.makeResponse(req, 403, "Forbidden")));
      return false;
    }
    const alg = params.algorithm === "SHA-256" ? "SHA-256" : "MD5";
    const password = users[username];

    const nowMs = Date.now();
    for (const [k, exp] of this.nonces) {
      if (exp <= nowMs) this.nonces.delete(k);
    }
    const nonceExp = this.nonces.get(nonce);
    if (!password || nonceExp === undefined || nonceExp <= nowMs) {
      return this.sendDigestChallenge(req, realm, replyFn);
    }

    const expected = computeSipDigestResponse({
      username,
      realm,
      password,
      method: req.method,
      uri,
      nonce,
      algorithm: alg,
      ...(params.qop ? { qop: params.qop } : {}),
      ...(params.nc ? { nc: params.nc } : {}),
      ...(params.cnonce ? { cnonce: params.cnonce } : {}),
    });

    const expBuf = Buffer.from(expected, "utf8");
    const gotBuf = Buffer.from(responseHash, "utf8");
    if (expBuf.length !== gotBuf.length || !timingSafeEqual(expBuf, gotBuf)) {
      replyFn(serializeSipMessage(this.makeResponse(req, 403, "Forbidden")));
      return false;
    }

    // Single-use nonce consumed on valid Digest authentication
    this.nonces.delete(nonce);
    return true;
  }

  private sendDigestChallenge(
    req: SipRequestMessage,
    realm: string,
    replyFn: (wire: string) => void,
  ): false {
    const nowMs = Date.now();
    for (const [k, exp] of this.nonces) {
      if (exp <= nowMs) this.nonces.delete(k);
    }
    while (this.nonces.size >= 1024) {
      const oldest = this.nonces.keys().next().value;
      if (oldest === undefined) break;
      this.nonces.delete(oldest);
    }
    const nonce = randomBytes(12).toString("hex");
    this.nonces.set(nonce, nowMs + 120_000);
    replyFn(
      serializeSipMessage(
        this.makeResponse(req, 401, "Unauthorized", {}, "", {
          "www-authenticate": [`Digest realm="${realm}", nonce="${nonce}", algorithm=SHA-256, qop="auth"`],
        }),
      ),
    );
    return false;
  }

  private handleRegister(req: SipRequestMessage, replyFn: (wire: string) => void): void {
    const toHdr = req.headers.to?.[0] ?? req.uri;
    const contact = req.headers.contact?.[0] ?? toHdr;
    const expiresSec = Number(req.headers.expires?.[0] ?? "3600") || 3600;
    this.registrations.set(toHdr, {
      contact,
      expiresAtMs: Date.now() + expiresSec * 1000,
    });
    this.events.emit("register", { aor: toHdr, contact, expiresSec });
    replyFn(
      serializeSipMessage(
        this.makeResponse(req, 200, "OK", {}, "", {
          contact: [contact],
          expires: [String(expiresSec)],
        }),
      ),
    );
  }

  private async handleInvite(
    req: SipRequestMessage,
    peer: SipPeerAddress,
    replyFn: (wire: string) => void,
  ): Promise<void> {
    const callId = req.headers["call-id"]?.[0] ?? randomBytes(8).toString("hex");
    const existingDialog = this.dialogs.get(callId);
    if (existingDialog) {
      if (existingDialog.state === "answered" || existingDialog.state === "confirmed") {
        const retransSdp = buildSdp({
          ip: this.bindHost,
          mediaPort: existingDialog.localMediaPort,
          ...(existingDialog.answerCrypto ? { srtp: existingDialog.answerCrypto } : {}),
          payloadTypes: [existingDialog.codecPt, existingDialog.telephoneEventPt ?? RTP_PT_TELEPHONE_EVENT],
        });
        replyFn(
          serializeSipMessage(
            this.makeResponse(
              req,
              200,
              "OK",
              { localTag: existingDialog.localTag },
              retransSdp,
              { "content-type": ["application/sdp"] },
            ),
          ),
        );
      } else {
        replyFn(
          serializeSipMessage(
            this.makeResponse(req, 180, "Ringing", { localTag: existingDialog.localTag }),
          ),
        );
      }
      return;
    }

    const fromHdr = req.headers.from?.[0] ?? "";
    const toHdr = req.headers.to?.[0] ?? "";
    const remoteTag = extractTag(fromHdr) ?? randomBytes(4).toString("hex");
    const localTag = randomBytes(6).toString("hex");

    replyFn(serializeSipMessage(this.makeResponse(req, 100, "Trying")));
    replyFn(serializeSipMessage(this.makeResponse(req, 180, "Ringing", { localTag })));

    const offer = parseSdp(req.body);
    const mediaSocket = dgram.createSocket("udp4");
    await new Promise<void>((resolve, reject) => {
      mediaSocket.once("error", reject);
      mediaSocket.bind(0, this.bindHost, () => {
        mediaSocket.off("error", reject);
        resolve();
      });
    });
    mediaSocket.unref();
    const localMediaPort = mediaSocket.address().port;

    let srtpTx: SrtpContext | undefined;
    let srtpRx: SrtpContext | undefined;
    let answerCrypto: SdesCryptoAttribute | undefined;

    if (offer.sdesCrypto) {
      srtpRx = new SrtpContext(offer.sdesCrypto.keyMaterial);
      answerCrypto = formatSdesCryptoAttribute(offer.sdesCrypto.tag);
      srtpTx = new SrtpContext(answerCrypto.keyMaterial);
    }

    const codecPt = offer.payloadTypes.includes(RTP_PT_PCMU)
      ? RTP_PT_PCMU
      : offer.payloadTypes.includes(RTP_PT_PCMA)
        ? RTP_PT_PCMA
        : RTP_PT_PCMU;

    const dialog: SipDialog = {
      callId,
      fromUri: fromHdr,
      toUri: toHdr,
      localTag,
      remoteTag,
      peer,
      state: "ringing",
      localMediaPort,
      remoteMediaIp: offer.connectionIp,
      remoteMediaPort: offer.mediaPort,
      ...(srtpTx ? { srtpTx } : {}),
      ...(srtpRx ? { srtpRx } : {}),
      ...(answerCrypto ? { answerCrypto } : {}),
      telephoneEventPt: offer.telephoneEventPt,
      mediaSocket,
      dtmfReceiver: new Rfc4733DtmfReceiver(),
      txSeq: randomBytes(2).readUInt16BE(0),
      txTimestamp: randomBytes(4).readUInt32BE(0),
      txSsrc: randomBytes(4).readUInt32BE(0),
      codecPt,
    };

    mediaSocket.on("message", (pkt, rinfo) => {
      this.onDialogMediaPacket(dialog, pkt, rinfo, offer.telephoneEventPt);
    });

    this.dialogs.set(callId, dialog);
    this.events.emit("call.ringing", {
      callId,
      from: fromHdr,
      to: toHdr,
      transport: peer.transport,
    });

    if (this.options.autoAnswer !== false) {
      dialog.state = "answered";
      const answerSdp = buildSdp({
        ip: this.bindHost,
        mediaPort: localMediaPort,
        ...(answerCrypto ? { srtp: answerCrypto } : {}),
        payloadTypes: [codecPt, offer.telephoneEventPt],
      });
      const contactScheme = peer.transport === "tls" ? "sips" : "sip";
      const contactPort =
        peer.transport === "tls"
          ? this.tlsServer && typeof this.tlsServer.address() === "object"
            ? (this.tlsServer.address() as net.AddressInfo).port
            : 5061
          : this.udpSocket
            ? this.udpSocket.address().port
            : 5060;

      replyFn(
        serializeSipMessage(
          this.makeResponse(
            req,
            200,
            "OK",
            { localTag },
            answerSdp,
            {
              "content-type": ["application/sdp"],
              contact: [`<${contactScheme}:omalla@${this.bindHost}:${contactPort}>`],
            },
          ),
        ),
      );
      this.events.emit("call.answered", {
        callId,
        localMediaPort,
        srtp: Boolean(srtpRx && srtpTx),
      });
    }
  }

  private onDialogMediaPacket(
    dialog: SipDialog,
    rawPacket: Buffer,
    rinfo: dgram.RemoteInfo,
    telephoneEventPt: number,
  ): void {
    if (dialog.state !== "answered" && dialog.state !== "confirmed") return;

    // Symmetric RTP latching: before latching, or when SRTP is active, verify
    // cryptographic authenticity FIRST so spoofed packets can NEVER hijack latch!
    if (dialog.latchedPeer) {
      if (dialog.latchedPeer.address !== rinfo.address || dialog.latchedPeer.port !== rinfo.port) {
        return;
      }
    } else if (!dialog.srtpRx) {
      // Unencrypted loopback RTP only latches from the SDP-negotiated IP
      if (rinfo.address !== dialog.remoteMediaIp) return;
      dialog.latchedPeer = { address: rinfo.address, port: rinfo.port };
    }

    try {
      const decoded = dialog.srtpRx
        ? dialog.srtpRx.unprotect(rawPacket).packet
        : decodeRtpPacket(rawPacket);

      if (!dialog.latchedPeer) {
        dialog.latchedPeer = { address: rinfo.address, port: rinfo.port };
      }

      if (decoded.header.payloadType === telephoneEventPt) {
        const digits = dialog.dtmfReceiver.push(decoded, telephoneEventPt);
        for (const digit of digits) {
          this.events.emit("call.dtmf", { callId: dialog.callId, digit });
        }
        return;
      }

      this.events.emit("call.audio", {
        callId: dialog.callId,
        payloadType: decoded.header.payloadType,
        payload: new Uint8Array(decoded.payload),
        seq: decoded.header.sequenceNumber,
        timestamp: decoded.header.timestamp,
      });
    } catch {
      // Invalid SRTP tag / replay / malformed RTP packet is dropped silently.
    }
  }

  private handleAck(req: SipRequestMessage): void {
    const callId = req.headers["call-id"]?.[0] ?? "";
    const dialog = this.dialogs.get(callId);
    if (!dialog) return;
    dialog.state = "confirmed";
    this.events.emit("call.confirmed", { callId });
  }

  private handleCancel(
    req: SipRequestMessage,
    peer: SipPeerAddress,
    replyFn: (wire: string) => void,
  ): void {
    const callId = req.headers["call-id"]?.[0] ?? "";
    const dialog = this.dialogs.get(callId);
    if (!dialog || dialog.state !== "ringing") {
      replyFn(serializeSipMessage(this.makeResponse(req, 481, "Call/Transaction Does Not Exist")));
      return;
    }
    const presentedTag = extractTag(req.headers.from?.[0] ?? "");
    if (peer.address !== dialog.peer.address || !presentedTag || presentedTag !== dialog.remoteTag) {
      replyFn(serializeSipMessage(this.makeResponse(req, 403, "Forbidden")));
      return;
    }
    replyFn(serializeSipMessage(this.makeResponse(req, 200, "OK")));
    dialog.state = "terminated";
    try {
      dialog.mediaSocket.close();
    } catch {
      // ignore
    }
    this.dialogs.delete(callId);
    const inviteCseq = (req.headers.cseq?.[0] ?? "1 CANCEL").replace(/CANCEL/i, "INVITE");
    replyFn(
      serializeSipMessage(
        this.makeResponse(req, 487, "Request Terminated", { localTag: dialog.localTag }, "", {
          cseq: [inviteCseq],
        }),
      ),
    );
    this.events.emit("call.ended", { callId, reason: "cancel" });
  }

  private handleRefer(
    req: SipRequestMessage,
    peer: SipPeerAddress,
    replyFn: (wire: string) => void,
  ): void {
    const callId = req.headers["call-id"]?.[0] ?? "";
    const dialog = this.dialogs.get(callId);
    const referToRaw = req.headers["refer-to"]?.[0] ?? "";
    if (!dialog || !referToRaw) {
      replyFn(serializeSipMessage(this.makeResponse(req, 400, "Bad Request")));
      return;
    }

    const replacesMatch = /[?&]Replaces=([^&>;]+)/i.exec(referToRaw);
    const mode: "warm" | "blind" = replacesMatch ? "warm" : "blind";
    const cleanTarget = referToRaw.replace(/^<|>$/g, "").split("?")[0] ?? referToRaw;

    dialog.transferTarget = cleanTarget;
    dialog.transferMode = mode;

    replyFn(
      serializeSipMessage(
        this.makeResponse(req, 202, "Accepted", { localTag: dialog.localTag }),
      ),
    );

    // Send RFC 3515 NOTIFY `SIP/2.0 200 OK` sipfrag over UDP or TCP/TLS stream
    const viaProto = peer.transport.toUpperCase();
    const localPort =
      peer.transport === "udp" && this.udpSocket
        ? this.udpSocket.address().port
        : peer.transport === "tls" && this.tlsServer && typeof this.tlsServer.address() === "object"
          ? (this.tlsServer.address() as net.AddressInfo).port
          : 5060;
    const notifyReq: SipRequestMessage = {
      kind: "request",
      method: "NOTIFY",
      uri: cleanSipUri(dialog.fromUri),
      version: "SIP/2.0",
      headers: {
        via: [`SIP/2.0/${viaProto} ${this.bindHost}:${localPort};branch=z9hG4bK${randomBytes(6).toString("hex")}`],
        from: [`${dialog.toUri};tag=${dialog.localTag}`],
        to: [dialog.fromUri],
        "call-id": [callId],
        cseq: ["2 NOTIFY"],
        event: ["refer"],
        "subscription-state": ["terminated;reason=noresource"],
        "content-type": ["message/sipfrag;version=2.0"],
      },
      body: "SIP/2.0 200 OK\r\n",
    };
    if (peer.transport === "udp" && this.udpSocket) {
      this.udpSocket.send(Buffer.from(serializeSipMessage(notifyReq), "utf8"), peer.port, peer.address);
    } else {
      replyFn(serializeSipMessage(notifyReq));
    }

    this.events.emit("call.refer", {
      callId,
      referTo: cleanTarget,
      mode,
      ...(replacesMatch?.[1] ? { replaces: decodeURIComponent(replacesMatch[1]) } : {}),
    });
  }

  private handleBye(req: SipRequestMessage, replyFn: (wire: string) => void): void {
    const callId = req.headers["call-id"]?.[0] ?? "";
    const dialog = this.dialogs.get(callId);
    replyFn(
      serializeSipMessage(
        this.makeResponse(req, 200, "OK", dialog ? { localTag: dialog.localTag } : {}),
      ),
    );
    if (dialog) {
      dialog.state = "terminated";
      try {
        dialog.mediaSocket.close();
      } catch {
        // ignore
      }
      this.dialogs.delete(callId);
      this.events.emit("call.ended", { callId, reason: "bye" });
    }
  }

  private makeResponse(
    req: SipRequestMessage,
    statusCode: number,
    reasonPhrase: string,
    opts: { localTag?: string } = {},
    body = "",
    extraHeaders: Record<string, string[]> = {},
  ): SipResponseMessage {
    const toRaw = req.headers.to?.[0] ?? "";
    const toWithTag =
      opts.localTag && !/;tag=/i.test(toRaw) ? `${toRaw};tag=${opts.localTag}` : toRaw;

    return {
      kind: "response",
      version: "SIP/2.0",
      statusCode,
      reasonPhrase,
      headers: {
        ...(req.headers.via ? { via: req.headers.via } : {}),
        ...(req.headers.from ? { from: req.headers.from } : {}),
        ...(toWithTag ? { to: [toWithTag] } : {}),
        ...(req.headers["call-id"] ? { "call-id": req.headers["call-id"] } : {}),
        ...(req.headers.cseq ? { cseq: req.headers.cseq } : {}),
        server: ["Omalla-SIP/0.1.0"],
        ...extraHeaders,
      },
      body,
    };
  }
}

function extractTag(headerVal: string): string | undefined {
  const m = /;tag=([^;\s>]+)/i.exec(headerVal);
  return m?.[1];
}

function cleanSipUri(headerVal: string): string {
  const m = /<([^>]+)>/.exec(headerVal);
  if (m?.[1]) return m[1];
  return headerVal.split(";")[0]?.trim() ?? headerVal;
}

function parseAuthParams(raw: string): Record<string, string> {
  const out: Record<string, string> = {};
  const re = /([a-zA-Z0-9_-]+)\s*=\s*(?:"([^"]*)"|([^,\s]+))/g;
  for (const m of raw.matchAll(re)) {
    const key = (m[1] ?? "").toLowerCase();
    const val = m[2] ?? m[3] ?? "";
    if (key) out[key] = val;
  }
  return out;
}
