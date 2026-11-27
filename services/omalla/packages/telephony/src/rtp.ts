/**
 * Pure-TypeScript RFC 3550 Real-time Transport Protocol (RTP) framing and
 * RFC 4733 `telephone-event` DTMF codec with End-of-Event (`E=1`) deduplication.
 */

export const RTP_VERSION = 2;
export const RTP_HEADER_MIN_BYTES = 12;

export const RTP_PT_PCMU = 0;
export const RTP_PT_PCMA = 8;
export const RTP_PT_TELEPHONE_EVENT = 101;

export interface RtpHeader {
  version: number;
  padding: boolean;
  extension: boolean;
  csrcCount: number;
  marker: boolean;
  payloadType: number;
  sequenceNumber: number;
  timestamp: number;
  ssrc: number;
  csrcs?: number[];
  extensionProfile?: number;
  extensionData?: Uint8Array;
}

export interface RtpPacket {
  header: RtpHeader;
  headerBytes: Uint8Array;
  payload: Uint8Array;
}

export function encodeRtpHeader(header: RtpHeader): Uint8Array {
  const csrcs = header.csrcs ?? [];
  const cc = Math.min(15, csrcs.length);
  const hasExt = Boolean(header.extension && header.extensionData);
  const extWords = hasExt ? Math.ceil((header.extensionData?.length ?? 0) / 4) : 0;
  const extLenBytes = hasExt ? 4 + extWords * 4 : 0;
  const totalHeader = RTP_HEADER_MIN_BYTES + cc * 4 + extLenBytes;

  const out = new Uint8Array(totalHeader);
  const view = new DataView(out.buffer, out.byteOffset, out.byteLength);

  const b0 =
    ((RTP_VERSION & 0x03) << 6) |
    ((header.padding ? 1 : 0) << 5) |
    ((hasExt ? 1 : 0) << 4) |
    (cc & 0x0f);
  const b1 = ((header.marker ? 1 : 0) << 7) | (header.payloadType & 0x7f);

  out[0] = b0;
  out[1] = b1;
  view.setUint16(2, header.sequenceNumber & 0xffff, false);
  view.setUint32(4, header.timestamp >>> 0, false);
  view.setUint32(8, header.ssrc >>> 0, false);

  for (let i = 0; i < cc; i += 1) {
    view.setUint32(12 + i * 4, (csrcs[i] ?? 0) >>> 0, false);
  }

  if (hasExt && header.extensionData) {
    const extOffset = 12 + cc * 4;
    view.setUint16(extOffset, (header.extensionProfile ?? 0xbede) & 0xffff, false);
    view.setUint16(extOffset + 2, extWords & 0xffff, false);
    out.set(header.extensionData, extOffset + 4);
  }

  return out;
}

export function encodeRtpPacket(
  header: Omit<RtpHeader, "version" | "padding" | "extension" | "csrcCount"> &
    Partial<Pick<RtpHeader, "padding" | "extension" | "csrcs" | "extensionProfile" | "extensionData">>,
  payload: Uint8Array,
): Uint8Array {
  const headerBytes = encodeRtpHeader({
    version: RTP_VERSION,
    padding: header.padding ?? false,
    extension: header.extension ?? false,
    csrcCount: header.csrcs?.length ?? 0,
    marker: header.marker,
    payloadType: header.payloadType,
    sequenceNumber: header.sequenceNumber,
    timestamp: header.timestamp,
    ssrc: header.ssrc,
    ...(header.csrcs ? { csrcs: header.csrcs } : {}),
    ...(header.extensionProfile !== undefined ? { extensionProfile: header.extensionProfile } : {}),
    ...(header.extensionData ? { extensionData: header.extensionData } : {}),
  });
  const out = new Uint8Array(headerBytes.length + payload.length);
  out.set(headerBytes, 0);
  out.set(payload, headerBytes.length);
  return out;
}

export function decodeRtpHeaderOnly(packet: Uint8Array): {
  header: RtpHeader;
  headerBytes: Uint8Array;
  encryptedPortion: Uint8Array;
} {
  if (packet.length < RTP_HEADER_MIN_BYTES) {
    throw new Error(`RTP packet too short: ${packet.length} bytes`);
  }
  const view = new DataView(packet.buffer, packet.byteOffset, packet.byteLength);
  const b0 = packet[0] ?? 0;
  const b1 = packet[1] ?? 0;
  const version = (b0 >> 6) & 0x03;
  if (version !== RTP_VERSION) {
    throw new Error(`unsupported RTP version: ${version}`);
  }
  const padding = ((b0 >> 5) & 0x01) === 1;
  const extension = ((b0 >> 4) & 0x01) === 1;
  const csrcCount = b0 & 0x0f;
  const marker = ((b1 >> 7) & 0x01) === 1;
  const payloadType = b1 & 0x7f;
  const sequenceNumber = view.getUint16(2, false);
  const timestamp = view.getUint32(4, false);
  const ssrc = view.getUint32(8, false);

  let offset = RTP_HEADER_MIN_BYTES;
  if (offset + csrcCount * 4 > packet.length) {
    throw new Error("RTP CSRC list exceeds packet length");
  }
  const csrcs: number[] = [];
  for (let i = 0; i < csrcCount; i += 1) {
    csrcs.push(view.getUint32(offset, false));
    offset += 4;
  }

  let extensionProfile: number | undefined;
  let extensionData: Uint8Array | undefined;
  if (extension) {
    if (offset + 4 > packet.length) {
      throw new Error("RTP extension header truncated");
    }
    extensionProfile = view.getUint16(offset, false);
    const extWords = view.getUint16(offset + 2, false);
    const extBytes = extWords * 4;
    offset += 4;
    if (offset + extBytes > packet.length) {
      throw new Error("RTP extension payload truncated");
    }
    extensionData = packet.subarray(offset, offset + extBytes);
    offset += extBytes;
  }

  return {
    header: {
      version,
      padding,
      extension,
      csrcCount,
      marker,
      payloadType,
      sequenceNumber,
      timestamp,
      ssrc,
      ...(csrcs.length > 0 ? { csrcs } : {}),
      ...(extensionProfile !== undefined ? { extensionProfile } : {}),
      ...(extensionData ? { extensionData } : {}),
    },
    headerBytes: packet.subarray(0, offset),
    encryptedPortion: packet.subarray(offset),
  };
}

export function decodeRtpPacket(packet: Uint8Array): RtpPacket {
  const { header, headerBytes, encryptedPortion } = decodeRtpHeaderOnly(packet);
  let payloadLen = encryptedPortion.length;
  if (header.padding) {
    const padLen = encryptedPortion[encryptedPortion.length - 1] ?? 0;
    if (padLen === 0 || padLen > encryptedPortion.length) {
      throw new Error("invalid RTP padding length");
    }
    payloadLen -= padLen;
  }

  return {
    header,
    headerBytes,
    payload: encryptedPortion.subarray(0, payloadLen),
  };
}

/* ------------------------------------------------------------------ */
/* RFC 4733 DTMF (`telephone-event`)                                   */
/* ------------------------------------------------------------------ */

const DTMF_CHAR_TO_CODE: Record<string, number> = {
  "0": 0,
  "1": 1,
  "2": 2,
  "3": 3,
  "4": 4,
  "5": 5,
  "6": 6,
  "7": 7,
  "8": 8,
  "9": 9,
  "*": 10,
  "#": 11,
  A: 12,
  B: 13,
  C: 14,
  D: 15,
};

const DTMF_CODE_TO_CHAR: Record<number, string> = Object.fromEntries(
  Object.entries(DTMF_CHAR_TO_CODE).map(([ch, code]) => [code, ch]),
);

export interface Rfc4733Event {
  digit: string;
  eventCode: number;
  end: boolean;
  volume: number;
  duration: number;
}

export function dtmfDigitToCode(digit: string): number {
  const code = DTMF_CHAR_TO_CODE[digit.toUpperCase()];
  if (code === undefined) {
    throw new Error(`unsupported RFC 4733 DTMF digit: ${digit}`);
  }
  return code;
}

export function encodeRfc4733Payload(input: {
  digit: string;
  end: boolean;
  volume?: number;
  duration: number;
}): Uint8Array {
  const code = dtmfDigitToCode(input.digit);
  const out = new Uint8Array(4);
  const view = new DataView(out.buffer);
  out[0] = code & 0xff;
  out[1] = ((input.end ? 1 : 0) << 7) | ((input.volume ?? 10) & 0x3f);
  view.setUint16(2, Math.max(0, Math.min(65535, input.duration)), false);
  return out;
}

export function decodeRfc4733Payload(payload: Uint8Array): Rfc4733Event | null {
  if (payload.length < 4) return null;
  const code = payload[0] ?? 255;
  const digit = DTMF_CODE_TO_CHAR[code];
  if (!digit) return null;
  const b1 = payload[1] ?? 0;
  const end = ((b1 >> 7) & 0x01) === 1;
  const volume = b1 & 0x3f;
  const view = new DataView(payload.buffer, payload.byteOffset, payload.byteLength);
  const duration = view.getUint16(2, false);
  return { digit, eventCode: code, end, volume, duration };
}

/**
 * Generates a realistic RFC 4733 RTP packet burst for one DTMF key press:
 *  - 1 start packet (`M=1, E=0, duration=160`)
 *  - 1 continuation packet (`M=0, E=0, duration=320`)
 *  - 3 redundant end-of-event packets (`M=0, E=1, duration=480`) sharing the
 *    exact event onset `timestamp` per RFC 4733 §2.5.1.4.
 */
export function buildRfc4733DigitBurst(input: {
  digit: string;
  ssrc: number;
  startSeq: number;
  eventTimestamp: number;
  payloadType?: number;
}): { packets: Uint8Array[]; nextSeq: number; nextTimestamp: number } {
  const pt = input.payloadType ?? RTP_PT_TELEPHONE_EVENT;
  let seq = input.startSeq & 0xffff;
  const ts = input.eventTimestamp >>> 0;
  const packets: Uint8Array[] = [];

  const steps: Array<{ marker: boolean; end: boolean; duration: number }> = [
    { marker: true, end: false, duration: 160 },
    { marker: false, end: false, duration: 320 },
    { marker: false, end: true, duration: 480 },
    { marker: false, end: true, duration: 480 },
    { marker: false, end: true, duration: 480 },
  ];

  for (const step of steps) {
    const payload = encodeRfc4733Payload({
      digit: input.digit,
      end: step.end,
      volume: 10,
      duration: step.duration,
    });
    packets.push(
      encodeRtpPacket(
        {
          marker: step.marker,
          payloadType: pt,
          sequenceNumber: seq,
          timestamp: ts,
          ssrc: input.ssrc,
        },
        payload,
      ),
    );
    seq = (seq + 1) & 0xffff;
  }

  return {
    packets,
    nextSeq: seq,
    nextTimestamp: (ts + 640) >>> 0,
  };
}

/**
 * Stateful RFC 4733 DTMF receiver that deduplicates repeated `E=1` end-of-event
 * packets (and interim `E=0` packets) keyed by `(ssrc, rtpTimestamp)`.
 *
 * Emits each pressed digit at most once when `E=1` arrives (or if a subsequent
 * event timestamp supersedes an unclosed event whose `E=1` packets were all lost).
 */
export class Rfc4733DtmfReceiver {
  private readonly completedEvents = new Set<string>();
  private readonly completedOrder: string[] = [];
  private activeBySsrc = new Map<number, { timestamp: number; digit: string }>();

  constructor(private readonly maxHistory = 256) {}

  /**
   * Feeds one decoded RTP packet. Returns the newly completed digit(s) (`0`, `1`,
   * or `2` if an unclosed prior event was finalized by a new event timestamp).
   */
  push(packet: RtpPacket, telephoneEventPt = RTP_PT_TELEPHONE_EVENT): string[] {
    if (packet.header.payloadType !== telephoneEventPt) return [];
    const ev = decodeRfc4733Payload(packet.payload);
    if (!ev) return [];

    const ssrc = packet.header.ssrc >>> 0;
    const ts = packet.header.timestamp >>> 0;
    const eventKey = `${ssrc}:${ts}`;

    if (this.completedEvents.has(eventKey)) {
      return [];
    }

    const emitted: string[] = [];
    const currentActive = this.activeBySsrc.get(ssrc);
    if (currentActive && currentActive.timestamp !== ts) {
      const prevKey = `${ssrc}:${currentActive.timestamp}`;
      if (!this.completedEvents.has(prevKey)) {
        this.markCompleted(prevKey);
        emitted.push(currentActive.digit);
      }
      this.activeBySsrc.delete(ssrc);
    }

    if (ev.end) {
      this.activeBySsrc.delete(ssrc);
      this.markCompleted(eventKey);
      emitted.push(ev.digit);
      return emitted;
    }

    this.activeBySsrc.set(ssrc, { timestamp: ts, digit: ev.digit });
    return emitted;
  }

  private markCompleted(key: string): void {
    this.completedEvents.add(key);
    this.completedOrder.push(key);
    while (this.completedOrder.length > this.maxHistory) {
      const oldest = this.completedOrder.shift();
      if (oldest) this.completedEvents.delete(oldest);
    }
  }
}
