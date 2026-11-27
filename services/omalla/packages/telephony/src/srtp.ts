/**
 * Pure-TypeScript RFC 3711 Secure Real-time Transport Protocol (SRTP) +
 * RFC 4568 SDES (`AES_CM_128_HMAC_SHA1_80`) using Node's built-in `node:crypto`.
 *
 * Implements:
 *  - RFC 3711 §4.3.1 AES-CM Pseudo-Random Function key derivation (`k_e`, `k_a`, `k_s`)
 *  - RFC 3711 §4.1.1 Segmented Integer Counter Mode (`AES-128-CTR`) payload encryption
 *  - RFC 3711 §4.2.1 `HMAC-SHA1-80` (10-byte authentication tag over `RTP || ROC`)
 *  - RFC 3711 §3.3.1 48-bit packet index (`ROC || SEQ`) estimation
 *  - RFC 3711 §3.3.2 64-packet sliding-window anti-replay protection
 *  - RFC 4568 `a=crypto:<tag> AES_CM_128_HMAC_SHA1_80 inline:<base64>` negotiation
 */
import { createCipheriv, createDecipheriv, createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import { decodeRtpHeaderOnly, decodeRtpPacket, type RtpPacket } from "./rtp.js";

export const SRTP_SUITE_AES_CM_128_HMAC_SHA1_80 = "AES_CM_128_HMAC_SHA1_80";
export const SRTP_MASTER_KEY_BYTES = 16;
export const SRTP_MASTER_SALT_BYTES = 14;
export const SRTP_INLINE_KEY_SALT_BYTES = 30;
export const SRTP_AUTH_TAG_BYTES = 10; // 80 bits

export interface SrtpKeyMaterial {
  masterKey: Uint8Array; // 16 bytes
  masterSalt: Uint8Array; // 14 bytes
}

export interface SdesCryptoAttribute {
  tag: number;
  suite: typeof SRTP_SUITE_AES_CM_128_HMAC_SHA1_80;
  inlineBase64: string;
  keyMaterial: SrtpKeyMaterial;
}

export function generateSrtpKeyMaterial(): SrtpKeyMaterial {
  return {
    masterKey: new Uint8Array(randomBytes(SRTP_MASTER_KEY_BYTES)),
    masterSalt: new Uint8Array(randomBytes(SRTP_MASTER_SALT_BYTES)),
  };
}

export function formatSdesCryptoAttribute(tag = 1, material = generateSrtpKeyMaterial()): SdesCryptoAttribute {
  validateKeyMaterial(material);
  const combined = Buffer.concat([Buffer.from(material.masterKey), Buffer.from(material.masterSalt)]);
  const inlineBase64 = combined.toString("base64");
  return {
    tag,
    suite: SRTP_SUITE_AES_CM_128_HMAC_SHA1_80,
    inlineBase64,
    keyMaterial: material,
  };
}

export function serializeSdesLine(attr: SdesCryptoAttribute): string {
  return `a=crypto:${attr.tag} ${attr.suite} inline:${attr.inlineBase64}`;
}

export function parseSdesLine(line: string): SdesCryptoAttribute | null {
  const trimmed = line.trim().replace(/^a=/, "");
  const match = /^crypto:(\d+)\s+(AES_CM_128_HMAC_SHA1_80)\s+inline:([A-Za-z0-9+/=]+)(?:\s|$)/.exec(
    trimmed,
  );
  if (!match) return null;
  const tag = Number(match[1]);
  const b64 = match[3] ?? "";
  const raw = Buffer.from(b64, "base64");
  if (raw.length < SRTP_INLINE_KEY_SALT_BYTES) return null;
  return {
    tag,
    suite: SRTP_SUITE_AES_CM_128_HMAC_SHA1_80,
    inlineBase64: b64,
    keyMaterial: {
      masterKey: new Uint8Array(raw.subarray(0, SRTP_MASTER_KEY_BYTES)),
      masterSalt: new Uint8Array(raw.subarray(SRTP_MASTER_KEY_BYTES, SRTP_INLINE_KEY_SALT_BYTES)),
    },
  };
}

interface SessionKeys {
  encKey: Buffer; // 16 bytes
  authKey: Buffer; // 20 bytes
  saltKey: Buffer; // 14 bytes
}

/**
 * RFC 3711 §4.3.1 Key Derivation Function (`key_derivation_rate = 0`).
 */
export function deriveSrtpSessionKeys(material: SrtpKeyMaterial): SessionKeys {
  validateKeyMaterial(material);
  return {
    encKey: deriveLabel(material, 0x00, 16),
    authKey: deriveLabel(material, 0x01, 20),
    saltKey: deriveLabel(material, 0x02, 14),
  };
}

function deriveLabel(material: SrtpKeyMaterial, label: number, outBytes: number): Buffer {
  // x = master_salt XOR (label || r) where r = 48-bit zero, so label sits at byte index 7 (14 - 7 = 7).
  const iv = Buffer.alloc(16, 0);
  for (let i = 0; i < 14; i += 1) {
    iv[i] = material.masterSalt[i] ?? 0;
  }
  iv[7] = (iv[7] ?? 0) ^ (label & 0xff);

  const cipher = createCipheriv("aes-128-ctr", Buffer.from(material.masterKey), iv);
  const zeros = Buffer.alloc(outBytes, 0);
  return Buffer.concat([cipher.update(zeros), cipher.final()]).subarray(0, outBytes);
}

/**
 * RFC 3711 §4.1.1 AES-CM 16-byte IV for `(saltKey, ssrc, roc, seq)`:
 * `IV = (k_s * 2^16) XOR (SSRC * 2^64) XOR (i * 2^16)` where `i = (ROC << 16) | SEQ`.
 */
function buildPacketIv(saltKey: Buffer, ssrc: number, roc: number, seq: number): Buffer {
  const iv = Buffer.alloc(16, 0);
  saltKey.copy(iv, 0, 0, 14);

  const ssrcBuf = Buffer.alloc(4);
  ssrcBuf.writeUInt32BE(ssrc >>> 0, 0);
  for (let j = 0; j < 4; j += 1) {
    iv[4 + j] = (iv[4 + j] ?? 0) ^ (ssrcBuf[j] ?? 0);
  }

  const indexBuf = Buffer.alloc(6);
  indexBuf.writeUInt32BE(roc >>> 0, 0);
  indexBuf.writeUInt16BE(seq & 0xffff, 4);
  for (let j = 0; j < 6; j += 1) {
    iv[8 + j] = (iv[8 + j] ?? 0) ^ (indexBuf[j] ?? 0);
  }

  return iv;
}

function computeAuthTag(authKey: Buffer, authenticatedPortion: Uint8Array, roc: number): Buffer {
  const rocBuf = Buffer.alloc(4);
  rocBuf.writeUInt32BE(roc >>> 0, 0);
  return createHmac("sha1", authKey)
    .update(authenticatedPortion)
    .update(rocBuf)
    .digest()
    .subarray(0, SRTP_AUTH_TAG_BYTES);
}

export class SrtpError extends Error {
  constructor(
    readonly code: "invalid_packet" | "replay_detected" | "auth_failed",
    message: string,
  ) {
    super(message);
    this.name = "SrtpError";
  }
}

/**
 * Stateful SRTP endpoint context (one instance for outbound TX, one for inbound RX,
 * or paired via `SrtpSessionPair`).
 */
export class SrtpContext {
  private readonly keys: SessionKeys;
  private txRoc = 0;
  private lastTxSeq: number | null = null;

  private rxInitialized = false;
  private rxRoc = 0;
  private rxHighestSeq = 0;
  private highestIndex = -1n;
  private replayBitmap = 0n; // 64-bit sliding anti-replay window

  constructor(material: SrtpKeyMaterial) {
    this.keys = deriveSrtpSessionKeys(material);
  }

  /**
   * Encrypts a cleartext RTP packet (including any RFC 3550 `P=1` padding bytes
   * per RFC 3711 §3.1) and appends the 10-byte HMAC-SHA1-80 authentication tag.
   */
  protect(rtpPacket: Uint8Array): Uint8Array {
    const parsed = decodeRtpPacket(rtpPacket);
    const seq = parsed.header.sequenceNumber;
    if (this.lastTxSeq !== null && seq < this.lastTxSeq && this.lastTxSeq - seq > 0x8000) {
      this.txRoc = (this.txRoc + 1) >>> 0;
    }
    this.lastTxSeq = seq;

    // RFC 3711 §3.1: the encrypted portion starts immediately after the RTP header
    // (fixed + CSRC + extension) and includes both RTP payload and any RTP padding.
    const plaintextPortion = rtpPacket.subarray(parsed.headerBytes.length);
    const iv = buildPacketIv(this.keys.saltKey, parsed.header.ssrc, this.txRoc, seq);
    const cipher = createCipheriv("aes-128-ctr", this.keys.encKey, iv);
    const encryptedPayload = Buffer.concat([cipher.update(plaintextPortion), cipher.final()]);

    const bodyLen = parsed.headerBytes.length + encryptedPayload.length;
    const out = new Uint8Array(bodyLen + SRTP_AUTH_TAG_BYTES);
    out.set(parsed.headerBytes, 0);
    out.set(encryptedPayload, parsed.headerBytes.length);

    const tag = computeAuthTag(this.keys.authKey, out.subarray(0, bodyLen), this.txRoc);
    out.set(tag, bodyLen);
    return out;
  }

  /**
   * Verifies anti-replay window + HMAC-SHA1-80 tag in constant time, then
   * decrypts the SRTP payload (including any `P=1` padding) and returns both
   * raw RTP bytes and parsed unpadded RTP packet.
   */
  unprotect(srtpPacket: Uint8Array): { rtpBytes: Uint8Array; packet: RtpPacket } {
    if (srtpPacket.length < 12 + SRTP_AUTH_TAG_BYTES) {
      throw new SrtpError("invalid_packet", "SRTP packet shorter than minimum header + auth tag");
    }
    const authOffset = srtpPacket.length - SRTP_AUTH_TAG_BYTES;
    const signedPortion = srtpPacket.subarray(0, authOffset);
    const receivedTag = srtpPacket.subarray(authOffset);

    let headerOnly: ReturnType<typeof decodeRtpHeaderOnly>;
    try {
      headerOnly = decodeRtpHeaderOnly(signedPortion);
    } catch (error) {
      throw new SrtpError("invalid_packet", (error as Error).message);
    }

    const seq = headerOnly.header.sequenceNumber;
    const estimatedRoc = this.estimateRoc(seq);
    const packetIndex = (BigInt(estimatedRoc) << 16n) | BigInt(seq);

    // Anti-replay check BEFORE cryptographic state mutation (RFC 3711 §3.3.2)
    if (this.highestIndex >= 0n) {
      const delta = this.highestIndex - packetIndex;
      if (delta >= 64n) {
        throw new SrtpError("replay_detected", `SRTP packet index ${packetIndex} outside 64-packet replay window`);
      }
      if (delta >= 0n) {
        const mask = 1n << delta;
        if ((this.replayBitmap & mask) !== 0n) {
          throw new SrtpError("replay_detected", `duplicate SRTP packet sequence ${seq} rejected`);
        }
      }
    }

    const expectedTag = computeAuthTag(this.keys.authKey, signedPortion, estimatedRoc);
    if (receivedTag.length !== expectedTag.length || !timingSafeEqual(receivedTag, expectedTag)) {
      throw new SrtpError("auth_failed", "SRTP HMAC-SHA1-80 authentication tag verification failed");
    }

    // Commit anti-replay & ROC state only after tag succeeds
    this.commitReplayWindow(packetIndex, estimatedRoc, seq);

    const iv = buildPacketIv(this.keys.saltKey, headerOnly.header.ssrc, estimatedRoc, seq);
    const decipher = createDecipheriv("aes-128-ctr", this.keys.encKey, iv);
    const decryptedPortion = Buffer.concat([decipher.update(headerOnly.encryptedPortion), decipher.final()]);

    const rtpBytes = new Uint8Array(headerOnly.headerBytes.length + decryptedPortion.length);
    rtpBytes.set(headerOnly.headerBytes, 0);
    rtpBytes.set(decryptedPortion, headerOnly.headerBytes.length);

    let packet: RtpPacket;
    try {
      packet = decodeRtpPacket(rtpBytes);
    } catch (error) {
      throw new SrtpError("invalid_packet", (error as Error).message);
    }

    return {
      rtpBytes,
      packet,
    };
  }

  private estimateRoc(seq: number): number {
    if (!this.rxInitialized) return 0;
    if (this.rxHighestSeq < 0x8000) {
      if (seq - this.rxHighestSeq > 0x8000) {
        return this.rxRoc > 0 ? (this.rxRoc - 1) >>> 0 : 0;
      }
      return this.rxRoc;
    }
    if (this.rxHighestSeq - 0x8000 > seq) {
      return (this.rxRoc + 1) >>> 0;
    }
    return this.rxRoc;
  }

  private commitReplayWindow(packetIndex: bigint, estimatedRoc: number, seq: number): void {
    const mask64 = (1n << 64n) - 1n;
    if (!this.rxInitialized) {
      this.rxInitialized = true;
      this.rxRoc = estimatedRoc;
      this.rxHighestSeq = seq;
      this.highestIndex = packetIndex;
      this.replayBitmap = 1n;
      return;
    }

    if (packetIndex > this.highestIndex) {
      const shift = packetIndex - this.highestIndex;
      this.replayBitmap = shift >= 64n ? 1n : ((this.replayBitmap << shift) | 1n) & mask64;
      this.highestIndex = packetIndex;
      if (estimatedRoc > this.rxRoc) {
        this.rxRoc = estimatedRoc;
        this.rxHighestSeq = seq;
      } else if (estimatedRoc === this.rxRoc && seq > this.rxHighestSeq) {
        this.rxHighestSeq = seq;
      }
    } else {
      const delta = this.highestIndex - packetIndex;
      this.replayBitmap = (this.replayBitmap | (1n << delta)) & mask64;
    }
  }
}

function validateKeyMaterial(material: SrtpKeyMaterial): void {
  if (material.masterKey.length !== SRTP_MASTER_KEY_BYTES) {
    throw new Error(`SRTP masterKey must be ${SRTP_MASTER_KEY_BYTES} bytes`);
  }
  if (material.masterSalt.length !== SRTP_MASTER_SALT_BYTES) {
    throw new Error(`SRTP masterSalt must be ${SRTP_MASTER_SALT_BYTES} bytes`);
  }
}
