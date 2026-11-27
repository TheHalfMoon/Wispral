const SECRET_PATTERNS: Array<{ name: string; re: RegExp; replacement: string }> = [
  { name: "bearer", re: /\bBearer\s+[A-Za-z0-9._~+/=-]{12,}/gi, replacement: "Bearer [REDACTED]" },
  { name: "openai", re: /\bsk-[A-Za-z0-9_-]{16,}/g, replacement: "[REDACTED_API_KEY]" },
  { name: "anthropic", re: /\bsk-ant-[A-Za-z0-9_-]{16,}/g, replacement: "[REDACTED_API_KEY]" },
  { name: "omalla", re: /\bom_[a-z]+_[a-z0-9]{20,}/gi, replacement: "[REDACTED_API_KEY]" },
  { name: "twilio", re: /\bSK[0-9a-fA-F]{32}\b/g, replacement: "[REDACTED_TWILIO_KEY]" },
  { name: "aws", re: /\bAKIA[0-9A-Z]{16}\b/g, replacement: "[REDACTED_AWS_KEY]" },
  { name: "jwt", re: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, replacement: "[REDACTED_JWT]" },
  { name: "phone", re: /\+\d{8,15}\b/g, replacement: "[REDACTED_NUMBER]" },
];

/** Redact credentials and caller identifiers before anything is logged. */
export function redact(value: unknown, depth = 0): unknown {
  if (depth > 6) return "[depth-limit]";
  if (typeof value === "string") return redactString(value);
  if (Array.isArray(value)) return value.map((item) => redact(item, depth + 1));
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      if (/key|secret|token|password|authorization|credential/i.test(key)) {
        out[key] = "[REDACTED]";
      } else {
        out[key] = redact(item, depth + 1);
      }
    }
    return out;
  }
  return value;
}

export function redactString(input: string): string {
  let out = input;
  for (const pattern of SECRET_PATTERNS) {
    out = out.replace(pattern.re, pattern.replacement);
  }
  return out;
}
