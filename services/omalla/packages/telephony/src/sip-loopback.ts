/**
 * Zero-cost local SIP + RTP/SRTP + RFC 4733 DTMF loopback peer (`127.0.0.1:0`).
 *
 * Places real UDP or `sips:` TLS SIP calls against `SipStack`, negotiates SDES
 * `AES_CM_128_HMAC_SHA1_80`, exchanges encrypted SRTP G.711 μ-law frames,
 * transmits RFC 4733 `telephone-event` DTMF bursts (including 3x `E=1` end
 * packets), executes `REFER` warm/cold transfers, and hangs up with `BYE`.
 */
import { randomBytes } from "node:crypto";
import dgram from "node:dgram";
import tls from "node:tls";
import {
  RTP_PT_PCMU,
  RTP_PT_TELEPHONE_EVENT,
  buildRfc4733DigitBurst,
  decodeRtpPacket,
  encodeRtpPacket,
} from "./rtp.js";
import {
  buildSdp,
  computeSipDigestResponse,
  parseSdp,
  parseSipMessage,
  serializeSipMessage,
  type SipMessage,
  type SipRequestMessage,
  type SipResponseMessage,
} from "./sip-stack.js";
import { SrtpContext, formatSdesCryptoAttribute } from "./srtp.js";

export interface SipLoopbackCall {
  callId: string;
  localTag: string;
  remoteTag: string;
  remoteMediaPort: number;
  srtpTx: SrtpContext;
  srtpRx: SrtpContext;
  seq: number;
  timestamp: number;
  ssrc: number;
  receivedAudioFrames: Uint8Array[];
  receivedSipMessages: SipMessage[];
}

export class SipLoopbackPeer {
  private sipUdp: dgram.Socket | null = null;
  private sipTls: tls.TLSSocket | null = null;
  private mediaUdp: dgram.Socket | null = null;
  private cseq = 1;
  private activeCall: SipLoopbackCall | null = null;
  private readonly pendingResponses = new Array<(res: SipResponseMessage) => void>();

  async bind(): Promise<{ sipPort: number; mediaPort: number }> {
    const sip = dgram.createSocket("udp4");
    const media = dgram.createSocket("udp4");
    sip.unref();
    media.unref();
    this.sipUdp = sip;
    this.mediaUdp = media;

    sip.on("message", (buf) => {
      const msg = parseSipMessage(buf.toString("utf8"));
      if (this.activeCall) this.activeCall.receivedSipMessages.push(msg);
      if (msg.kind === "response") {
        // Only resolve waiter on final (>=200) responses; 100/180 provisional are recorded
        if (msg.statusCode >= 200) {
          const waiter = this.pendingResponses.shift();
          waiter?.(msg);
        }
      } else if (msg.method === "NOTIFY" && this.sipUdp) {
        // Acknowledge RFC 3515 NOTIFY with 200 OK
        const viaHostPort = msg.headers.via?.[0]?.split(/\s+/)[1]?.split(";")[0] ?? "127.0.0.1:5060";
        const [host = "127.0.0.1", portStr = "5060"] = viaHostPort.split(":");
        const ok: SipResponseMessage = {
          kind: "response",
          version: "SIP/2.0",
          statusCode: 200,
          reasonPhrase: "OK",
          headers: {
            ...(msg.headers.via ? { via: msg.headers.via } : {}),
            ...(msg.headers.from ? { from: msg.headers.from } : {}),
            ...(msg.headers.to ? { to: msg.headers.to } : {}),
            ...(msg.headers["call-id"] ? { "call-id": msg.headers["call-id"] } : {}),
            ...(msg.headers.cseq ? { cseq: msg.headers.cseq } : {}),
          },
          body: "",
        };
        this.sipUdp.send(Buffer.from(serializeSipMessage(ok), "utf8"), Number(portStr), host);
      }
    });

    media.on("message", (pkt) => {
      const call = this.activeCall;
      if (!call) return;
      try {
        const unprotected = call.srtpRx.unprotect(pkt);
        call.receivedAudioFrames.push(new Uint8Array(unprotected.packet.payload));
      } catch {
        // Fallback if unencrypted loopback test
        try {
          const rtp = decodeRtpPacket(pkt);
          call.receivedAudioFrames.push(new Uint8Array(rtp.payload));
        } catch {
          // ignore invalid frame
        }
      }
    });

    await Promise.all([
      new Promise<void>((resolve, reject) => {
        sip.once("error", reject);
        sip.bind(0, "127.0.0.1", () => {
          sip.off("error", reject);
          resolve();
        });
      }),
      new Promise<void>((resolve, reject) => {
        media.once("error", reject);
        media.bind(0, "127.0.0.1", () => {
          media.off("error", reject);
          resolve();
        });
      }),
    ]);

    return {
      sipPort: sip.address().port,
      mediaPort: media.address().port,
    };
  }

  async connectTls(port: number, caCert?: string | Buffer): Promise<void> {
    await new Promise<void>((resolve, reject) => {
      const sock = tls.connect(
        {
          host: "127.0.0.1",
          port,
          ...(caCert ? { ca: caCert } : { rejectUnauthorized: false }),
        },
        () => resolve(),
      );
      this.sipTls = sock;
      sock.once("error", reject);
      let buf = "";
      sock.on("data", (chunk: Buffer) => {
        buf += chunk.toString("utf8");
        while (true) {
          const sep = buf.indexOf("\r\n\r\n");
          if (sep < 0) break;
          const head = buf.slice(0, sep);
          const clMatch = /(?:^|\r?\n)content-length\s*:\s*(\d+)/i.exec(head);
          const cl = clMatch?.[1] ? Number(clMatch[1]) : 0;
          const tailBuf = Buffer.from(buf.slice(sep + 4), "utf8");
          if (tailBuf.length < cl) break;
          const body = tailBuf.subarray(0, cl).toString("utf8");
          buf = tailBuf.subarray(cl).toString("utf8");
          const msg = parseSipMessage(`${head}\r\n\r\n${body}`);
          if (this.activeCall) this.activeCall.receivedSipMessages.push(msg);
          if (msg.kind === "response" && msg.statusCode >= 200) {
            const waiter = this.pendingResponses.shift();
            waiter?.(msg);
          }
        }
      });
    });
  }

  async register(input: {
    targetPort: number;
    username: string;
    password: string;
    transport?: "udp" | "tls";
  }): Promise<SipResponseMessage> {
    const uri = `${input.transport === "tls" ? "sips" : "sip"}:127.0.0.1:${input.targetPort}`;
    const callId = `reg_${randomBytes(6).toString("hex")}`;
    const tag = randomBytes(4).toString("hex");
    const first = await this.sendRequest(
      {
        kind: "request",
        method: "REGISTER",
        uri,
        version: "SIP/2.0",
        headers: {
          via: [this.viaHeader(input.transport ?? "udp")],
          from: [`<sip:${input.username}@127.0.0.1>;tag=${tag}`],
          to: [`<sip:${input.username}@127.0.0.1>`],
          "call-id": [callId],
          cseq: [`${this.cseq++} REGISTER`],
          contact: [`<sip:${input.username}@127.0.0.1:${this.sipUdp?.address().port ?? 5060}>`],
          expires: ["600"],
        },
        body: "",
      },
      input.targetPort,
      input.transport ?? "udp",
    );

    if (first.statusCode !== 401) return first;

    const challenge = first.headers["www-authenticate"]?.[0] ?? "";
    const realm = /realm="([^"]+)"/.exec(challenge)?.[1] ?? "omalla.local";
    const nonce = /nonce="([^"]+)"/.exec(challenge)?.[1] ?? "";
    const alg = /algorithm=SHA-256/i.test(challenge) ? "SHA-256" : "MD5";
    const cnonce = randomBytes(6).toString("hex");
    const nc = "00000001";
    const respHash = computeSipDigestResponse({
      username: input.username,
      realm,
      password: input.password,
      method: "REGISTER",
      uri,
      nonce,
      algorithm: alg,
      qop: "auth",
      nc,
      cnonce,
    });

    return this.sendRequest(
      {
        kind: "request",
        method: "REGISTER",
        uri,
        version: "SIP/2.0",
        headers: {
          via: [this.viaHeader(input.transport ?? "udp")],
          from: [`<sip:${input.username}@127.0.0.1>;tag=${tag}`],
          to: [`<sip:${input.username}@127.0.0.1>`],
          "call-id": [callId],
          cseq: [`${this.cseq++} REGISTER`],
          contact: [`<sip:${input.username}@127.0.0.1:${this.sipUdp?.address().port ?? 5060}>`],
          expires: ["600"],
          authorization: [
            `Digest username="${input.username}", realm="${realm}", nonce="${nonce}", uri="${uri}", response="${respHash}", algorithm=${alg}, qop=auth, nc=${nc}, cnonce="${cnonce}"`,
          ],
        },
        body: "",
      },
      input.targetPort,
      input.transport ?? "udp",
    );
  }

  async placeCall(input: {
    targetPort: number;
    fromUser?: string;
    toUser?: string;
    gatewayToken?: string;
    transport?: "udp" | "tls";
  }): Promise<SipLoopbackCall> {
    if (!this.mediaUdp) throw new Error("SipLoopbackPeer.bind() must be called first");
    const transport = input.transport ?? "udp";
    const scheme = transport === "tls" ? "sips" : "sip";
    const callId = `call_${randomBytes(8).toString("hex")}`;
    const localTag = randomBytes(4).toString("hex");
    const offerCrypto = formatSdesCryptoAttribute(1);
    const sdpOffer = buildSdp({
      ip: "127.0.0.1",
      mediaPort: this.mediaUdp.address().port,
      srtp: offerCrypto,
      payloadTypes: [RTP_PT_PCMU, RTP_PT_TELEPHONE_EVENT],
    });

    const inviteReq: SipRequestMessage = {
      kind: "request",
      method: "INVITE",
      uri: `${scheme}:${input.toUser ?? "ava"}@127.0.0.1:${input.targetPort}`,
      version: "SIP/2.0",
      headers: {
        via: [this.viaHeader(transport)],
        from: [`<${scheme}:${input.fromUser ?? "caller"}@127.0.0.1>;tag=${localTag}`],
        to: [`<${scheme}:${input.toUser ?? "ava"}@127.0.0.1>`],
        "call-id": [callId],
        cseq: [`${this.cseq++} INVITE`],
        contact: [`<${scheme}:caller@127.0.0.1:${this.sipUdp?.address().port ?? 5060}>`],
        "content-type": ["application/sdp"],
        ...(input.gatewayToken ? { "x-omalla-gateway-token": [input.gatewayToken] } : {}),
      },
      body: sdpOffer,
    };

    const res = await this.sendRequest(inviteReq, input.targetPort, transport);
    if (res.statusCode !== 200) {
      throw new Error(`SIP INVITE failed with ${res.statusCode} ${res.reasonPhrase}`);
    }

    const answerSdp = parseSdp(res.body);
    if (!answerSdp.sdesCrypto) {
      throw new Error("SIP answer missing SRTP SDES crypto attribute");
    }
    const remoteTag = /;tag=([^;\s>]+)/i.exec(res.headers.to?.[0] ?? "")?.[1] ?? "";

    const call: SipLoopbackCall = {
      callId,
      localTag,
      remoteTag,
      remoteMediaPort: answerSdp.mediaPort,
      srtpTx: new SrtpContext(offerCrypto.keyMaterial),
      srtpRx: new SrtpContext(answerSdp.sdesCrypto.keyMaterial),
      seq: 100,
      timestamp: 160,
      ssrc: 0x11223344,
      receivedAudioFrames: [],
      receivedSipMessages: [],
    };
    this.activeCall = call;

    // Send ACK
    const ackReq: SipRequestMessage = {
      kind: "request",
      method: "ACK",
      uri: `${scheme}:${input.toUser ?? "ava"}@127.0.0.1:${input.targetPort}`,
      version: "SIP/2.0",
      headers: {
        via: [this.viaHeader(transport)],
        from: inviteReq.headers.from!,
        to: res.headers.to ?? inviteReq.headers.to!,
        "call-id": [callId],
        cseq: ["1 ACK"],
      },
      body: "",
    };
    this.sendRaw(serializeSipMessage(ackReq), input.targetPort, transport);

    return call;
  }

  sendSrtpMulawFrame(mulawPayload: Uint8Array): void {
    const call = this.activeCall;
    if (!call || !this.mediaUdp) throw new Error("no active call");
    const rtp = encodeRtpPacket(
      {
        marker: call.seq === 100,
        payloadType: RTP_PT_PCMU,
        sequenceNumber: call.seq,
        timestamp: call.timestamp,
        ssrc: call.ssrc,
      },
      mulawPayload,
    );
    call.seq = (call.seq + 1) & 0xffff;
    call.timestamp = (call.timestamp + mulawPayload.length) >>> 0;
    const srtp = call.srtpTx.protect(rtp);
    this.mediaUdp.send(srtp, call.remoteMediaPort, "127.0.0.1");
  }

  /** Sends an RFC 4733 DTMF digit burst (including 3 redundant `E=1` packets!) encrypted over SRTP. */
  sendSrtpDtmfDigit(digit: string): void {
    const call = this.activeCall;
    if (!call || !this.mediaUdp) throw new Error("no active call");
    const burst = buildRfc4733DigitBurst({
      digit,
      ssrc: call.ssrc,
      startSeq: call.seq,
      eventTimestamp: call.timestamp,
    });
    call.seq = burst.nextSeq;
    call.timestamp = burst.nextTimestamp;
    for (const rtp of burst.packets) {
      const srtp = call.srtpTx.protect(rtp);
      this.mediaUdp.send(srtp, call.remoteMediaPort, "127.0.0.1");
    }
  }

  async refer(
    targetPort: number,
    referToUri: string,
    options: { warmReplacesCallId?: string; gatewayToken?: string; transport?: "udp" | "tls" } = {},
  ): Promise<SipResponseMessage> {
    const call = this.activeCall;
    if (!call) throw new Error("no active call");
    const transport = options.transport ?? "udp";
    const referHeader = options.warmReplacesCallId
      ? `<${referToUri}?Replaces=${encodeURIComponent(options.warmReplacesCallId)}>`
      : `<${referToUri}>`;

    return this.sendRequest(
      {
        kind: "request",
        method: "REFER",
        uri: `sip:ava@127.0.0.1:${targetPort}`,
        version: "SIP/2.0",
        headers: {
          via: [this.viaHeader(transport)],
          from: [`<sip:caller@127.0.0.1>;tag=${call.localTag}`],
          to: [`<sip:ava@127.0.0.1>;tag=${call.remoteTag}`],
          "call-id": [call.callId],
          cseq: [`${this.cseq++} REFER`],
          "refer-to": [referHeader],
          ...(options.gatewayToken ? { "x-omalla-gateway-token": [options.gatewayToken] } : {}),
        },
        body: "",
      },
      targetPort,
      transport,
    );
  }

  async hangup(
    targetPort: number,
    options: { gatewayToken?: string; transport?: "udp" | "tls" } = {},
  ): Promise<SipResponseMessage> {
    const call = this.activeCall;
    if (!call) throw new Error("no active call");
    const transport = options.transport ?? "udp";
    return this.sendRequest(
      {
        kind: "request",
        method: "BYE",
        uri: `sip:ava@127.0.0.1:${targetPort}`,
        version: "SIP/2.0",
        headers: {
          via: [this.viaHeader(transport)],
          from: [`<sip:caller@127.0.0.1>;tag=${call.localTag}`],
          to: [`<sip:ava@127.0.0.1>;tag=${call.remoteTag}`],
          "call-id": [call.callId],
          cseq: [`${this.cseq++} BYE`],
          ...(options.gatewayToken ? { "x-omalla-gateway-token": [options.gatewayToken] } : {}),
        },
        body: "",
      },
      targetPort,
      transport,
    );
  }

  async close(): Promise<void> {
    this.sipTls?.destroy();
    this.sipTls = null;
    await Promise.all([
      this.sipUdp ? new Promise<void>((r) => this.sipUdp!.close(() => r())) : Promise.resolve(),
      this.mediaUdp ? new Promise<void>((r) => this.mediaUdp!.close(() => r())) : Promise.resolve(),
    ]);
  }

  private viaHeader(transport: "udp" | "tls"): string {
    const proto = transport === "tls" ? "TLS" : "UDP";
    const port = this.sipUdp?.address().port ?? 5060;
    return `SIP/2.0/${proto} 127.0.0.1:${port};branch=z9hG4bK${randomBytes(6).toString("hex")}`;
  }

  private sendRaw(wire: string, targetPort: number, transport: "udp" | "tls"): void {
    if (transport === "tls") {
      if (!this.sipTls) throw new Error("TLS socket not connected");
      this.sipTls.write(wire, "utf8");
      return;
    }
    if (!this.sipUdp) throw new Error("UDP socket not bound");
    this.sipUdp.send(Buffer.from(wire, "utf8"), targetPort, "127.0.0.1");
  }

  private sendRequest(
    req: SipRequestMessage,
    targetPort: number,
    transport: "udp" | "tls",
  ): Promise<SipResponseMessage> {
    return new Promise<SipResponseMessage>((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`SIP ${req.method} timed out waiting for final response`));
      }, 4000);
      timer.unref?.();
      this.pendingResponses.push((res) => {
        clearTimeout(timer);
        resolve(res);
      });
      this.sendRaw(serializeSipMessage(req), targetPort, transport);
    });
  }
}
