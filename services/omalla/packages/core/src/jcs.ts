import { createHash } from "node:crypto";
import { OmallaError } from "./errors.js";

/**
 * RFC 8785 JSON Canonicalization Scheme (JCS) with strict float rejection (OM-T5).
 *
 * Canonicalizes JSON values deterministically across TypeScript, Python, and Rust:
 *  - Object keys are ordered lexicographically by UTF-16 code units (RFC 8785 §3.2.3).
 *  - Only safe exact integers are permitted; floating-point numbers, NaN, and
 *    Infinity are rejected so cross-language argument digests never drift.
 *  - Strings use minimal RFC 8785 escaping with lowercase \u00xx for control chars.
 */
export function canonicalizeJcs(value: unknown): string {
  return serializeValue(value);
}

/**
 * Validates raw JSON text for float tokens (e.g. `1.5`, `1.0`, `1e3`) before
 * parsing and canonicalizing under RFC 8785.
 */
export function canonicalizeJcsFromRawJson(rawJson: string): string {
  assertNoRawFloatTokens(rawJson);
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawJson);
  } catch {
    throw new OmallaError("validation", "payload is not valid JSON", 400);
  }
  return canonicalizeJcs(parsed);
}

export function jcsSha256(value: unknown): string {
  const canonical = canonicalizeJcs(value);
  return createHash("sha256").update(canonical, "utf8").digest("hex");
}

export function jcsSha256FromRawJson(rawJson: string): string {
  const canonical = canonicalizeJcsFromRawJson(rawJson);
  return createHash("sha256").update(canonical, "utf8").digest("hex");
}

function serializeValue(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value) || !Number.isSafeInteger(value)) {
      throw new OmallaError(
        "validation",
        "floating-point or non-safe-integer numbers are rejected in JCS idempotency payloads",
        400,
      );
    }
    return Object.is(value, -0) ? "0" : String(value);
  }
  if (typeof value === "string") {
    return serializeString(value);
  }
  if (Array.isArray(value)) {
    const items = value.map((item) => serializeValue(item === undefined ? null : item));
    return `[${items.join(",")}]`;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const keys = Object.keys(record)
      .filter((key) => record[key] !== undefined)
      .sort(compareUtf16CodeUnits);
    const pairs = keys.map((key) => `${serializeString(key)}:${serializeValue(record[key])}`);
    return `{${pairs.join(",")}}`;
  }
  throw new OmallaError("validation", `unsupported JCS value type: ${typeof value}`, 400);
}

function compareUtf16CodeUnits(a: string, b: string): number {
  const len = Math.min(a.length, b.length);
  for (let i = 0; i < len; i += 1) {
    const ca = a.charCodeAt(i);
    const cb = b.charCodeAt(i);
    if (ca !== cb) return ca - cb;
  }
  return a.length - b.length;
}

function serializeString(input: string): string {
  let out = '"';
  for (let i = 0; i < input.length; i += 1) {
    const code = input.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = i + 1 < input.length ? input.charCodeAt(i + 1) : 0;
      if (next < 0xdc00 || next > 0xdfff) {
        throw new OmallaError("validation", "lone UTF-16 high surrogate is rejected in JCS string", 400);
      }
      out += input[i]! + input[i + 1]!;
      i += 1;
      continue;
    }
    if (code >= 0xdc00 && code <= 0xdfff) {
      throw new OmallaError("validation", "lone UTF-16 low surrogate is rejected in JCS string", 400);
    }
    switch (code) {
      case 0x08:
        out += "\\b";
        break;
      case 0x09:
        out += "\\t";
        break;
      case 0x0a:
        out += "\\n";
        break;
      case 0x0c:
        out += "\\f";
        break;
      case 0x0d:
        out += "\\r";
        break;
      case 0x22:
        out += '\\"';
        break;
      case 0x5c:
        out += "\\\\";
        break;
      default:
        if (code < 0x20) {
          out += `\\u${code.toString(16).padStart(4, "0")}`;
        } else {
          out += input[i];
        }
        break;
    }
  }
  out += '"';
  return out;
}

function assertNoRawFloatTokens(raw: string): void {
  let inString = false;
  let escaped = false;
  for (let i = 0; i < raw.length; i += 1) {
    const ch = raw[i] ?? "";
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }
    if (ch === '"') {
      inString = true;
      continue;
    }
    if (ch === "-" || (ch >= "0" && ch <= "9")) {
      let j = i + 1;
      while (j < raw.length) {
        const c = raw[j] ?? "";
        if ((c >= "0" && c <= "9") || c === "." || c === "e" || c === "E" || c === "+" || c === "-") {
          j += 1;
        } else {
          break;
        }
      }
      const token = raw.slice(i, j);
      if (token.includes(".") || token.includes("e") || token.includes("E")) {
        throw new OmallaError(
          "validation",
          `floating-point number '${token}' is rejected in JCS idempotency payloads`,
          400,
        );
      }
      i = j - 1;
    }
  }
}
