import { createHash, createHmac, timingSafeEqual } from "node:crypto";

export const DEFAULT_WEBHOOK_SKEW_SEC = 300;

export interface WebhookVerifyInput {
  rawBody: Uint8Array | string;
  headers: Record<string, string | undefined>;
  secret: string;
  nowMs?: number;
  maxSkewSec?: number;
}

export interface WebhookVerifyOutcome {
  valid: boolean;
  eventKey?: string;
  scheme?: "standard-webhooks" | "omalla-hmac";
  reason?: string;
}

/**
 * Constant-time raw-byte HMAC webhook verifier (`OM-T3`) shared across
 * `@omalla/core`, `@omalla/server`, and `@omalla/sdk`:
 *
 *  1. Standard Webhooks (`webhook-id`, `webhook-timestamp`, `webhook-signature` `v1,<base64>`)
 *     with ±300 s timestamp skew enforcement (also accepts `svix-*` aliases).
 *  2. Omalla HMAC (`x-omalla-signature: sha256=<hex>` + mandatory `x-omalla-timestamp`
 *     within ±300 s over `${timestamp}.` + rawBody bytes).
 *
 * Replay `eventKey` is ALWAYS derived strictly from cryptographically signed
 * components (`stdId` or `omalla:${timestamp}:${sha256(rawBody)}`), never from
 * unsigned headers.
 */
export function verifySignedWebhookRaw(input: WebhookVerifyInput): WebhookVerifyOutcome {
  const rawBytes =
    typeof input.rawBody === "string" ? Buffer.from(input.rawBody, "utf8") : Buffer.from(input.rawBody);
  const nowSec = Math.floor((input.nowMs ?? Date.now()) / 1000);
  const maxSkew = input.maxSkewSec ?? DEFAULT_WEBHOOK_SKEW_SEC;
  const headers = lowerCaseHeaders(input.headers);

  const stdId = headers["webhook-id"] ?? headers["svix-id"];
  const stdTs = headers["webhook-timestamp"] ?? headers["svix-timestamp"];
  const stdSig = headers["webhook-signature"] ?? headers["svix-signature"];

  if (stdId || stdTs || stdSig) {
    if (!stdId || !stdTs || !stdSig) {
      return { valid: false, reason: "incomplete Standard Webhooks headers" };
    }
    if (!/^-?\d+$/.test(stdTs.trim())) {
      return { valid: false, reason: "invalid webhook-timestamp" };
    }
    const tsNum = Number(stdTs.trim());
    if (!Number.isSafeInteger(tsNum) || Math.abs(nowSec - tsNum) > maxSkew) {
      return { valid: false, reason: "webhook timestamp outside ±300s window" };
    }
    const keyBytes = decodeStandardWebhookSecret(input.secret);
    const prefix = Buffer.from(`${stdId}.${stdTs.trim()}.`, "utf8");
    const signedBytes = Buffer.concat([prefix, rawBytes]);
    const expectedDigest = createHmac("sha256", keyBytes).update(signedBytes).digest();

    const candidates = stdSig
      .split(/\s+/)
      .map((part) => part.trim())
      .filter(Boolean);

    let matched = false;
    for (const candidate of candidates) {
      const comma = candidate.indexOf(",");
      if (comma <= 0) continue;
      const version = candidate.slice(0, comma);
      const b64 = candidate.slice(comma + 1);
      if (version !== "v1" || !b64) continue;
      const provided = Buffer.from(b64, "base64");
      if (provided.length === expectedDigest.length && timingSafeEqual(provided, expectedDigest)) {
        matched = true;
      }
    }

    if (!matched) {
      return { valid: false, reason: "Standard Webhooks v1 signature mismatch" };
    }
    return { valid: true, eventKey: stdId, scheme: "standard-webhooks" };
  }

  const omallaSig = headers["x-omalla-signature"];
  if (!omallaSig) {
    return { valid: false, reason: "missing webhook signature header" };
  }

  const omallaTs = headers["x-omalla-timestamp"];
  if (!omallaTs || !/^-?\d+$/.test(omallaTs.trim())) {
    return { valid: false, reason: "missing or invalid x-omalla-timestamp header" };
  }
  const tsClean = omallaTs.trim();
  const tsNum = Number(tsClean);
  if (!Number.isSafeInteger(tsNum) || Math.abs(nowSec - tsNum) > maxSkew) {
    return { valid: false, reason: "x-omalla-timestamp outside ±300s window" };
  }

  const signedPayload = Buffer.concat([Buffer.from(`${tsClean}.`, "utf8"), rawBytes]);
  const rawHex = omallaSig.startsWith("sha256=") ? omallaSig.slice(7) : omallaSig;
  if (!/^[0-9a-f]{64}$/i.test(rawHex)) {
    return { valid: false, reason: "malformed sha256 signature" };
  }
  const providedBytes = Buffer.from(rawHex, "hex");
  const expectedBytes = createHmac("sha256", Buffer.from(input.secret, "utf8"))
    .update(signedPayload)
    .digest();

  if (providedBytes.length !== expectedBytes.length || !timingSafeEqual(providedBytes, expectedBytes)) {
    return { valid: false, reason: "webhook HMAC signature mismatch" };
  }

  const bodySha = createHash("sha256").update(rawBytes).digest("hex");
  const eventKey = `omalla:${tsClean}:${bodySha}`;
  return {
    valid: true,
    eventKey,
    scheme: "omalla-hmac",
  };
}

function decodeStandardWebhookSecret(secret: string): Buffer {
  if (secret.startsWith("whsec_")) {
    return Buffer.from(secret.slice(6), "base64");
  }
  return Buffer.from(secret, "utf8");
}

function lowerCaseHeaders(headers: Record<string, string | undefined>): Record<string, string | undefined> {
  const out: Record<string, string | undefined> = {};
  for (const [k, v] of Object.entries(headers)) {
    out[k.toLowerCase()] = v;
  }
  return out;
}
