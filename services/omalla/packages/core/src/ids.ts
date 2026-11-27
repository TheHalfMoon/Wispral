import { randomUUID, randomBytes } from "node:crypto";

const ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz";

export function newId(prefix: string): string {
  return `${prefix}_${randomUUID().replace(/-/g, "").slice(0, 24)}`;
}

/** URL-safe random token, used for API keys and webhook secrets. */
export function newToken(bytes = 32): string {
  const buffer = randomBytes(bytes);
  let out = "";
  for (let i = 0; i < buffer.length; i += 1) {
    const byte = buffer[i] ?? 0;
    out += ALPHABET[byte % ALPHABET.length];
  }
  return out;
}

export function nowIso(): string {
  return new Date().toISOString();
}

export function shortId(prefix: string, length = 8): string {
  return `${prefix}_${randomUUID().replace(/-/g, "").slice(0, length)}`;
}
