/**
 * Deterministic policy for actions with real-world consequences (OM-T6).
 *
 * Policy is separate from the model on purpose: a probabilistic component may
 * request an action, but only deterministic code decides whether it is allowed.
 */
import net from "node:net";

export interface OutboundPolicyInput {
  to: string;
  from: string;
  tenant: {
    outboundEnabled: boolean;
    outboundAllowlist: string[];
    dncList?: string[];
    dailyOutboundCap: number;
    maxConcurrentCalls?: number;
    dailyMinuteQuota?: number;
    monthlyMinuteQuota?: number;
  };
  callsToday: number;
  activeCalls?: number;
  minutesToday?: number;
  minutesThisMonth?: number;
  /** Current timestamp. */
  now: Date;
  callingWindow?: { start: string; end: string; days: number[] };
  timeZone?: string;
  consentGranted: boolean;
}

export interface PolicyDecision {
  allowed: boolean;
  reason?: string;
  code?:
    | "outbound_disabled"
    | "not_allowlisted"
    | "dnc_listed"
    | "daily_cap"
    | "concurrent_cap"
    | "daily_minute_quota"
    | "monthly_minute_quota"
    | "outside_calling_window"
    | "consent_missing"
    | "invalid_number";
}

const E164 = /^\+[1-9]\d{6,14}$/;

export function isE164(value: string): boolean {
  return E164.test(value);
}

/** Normalise common dialing formats into E.164 where it is unambiguous. */
export function normalizeNumber(value: string, defaultCountryCode = "1"): string {
  const trimmed = value.replace(/[\s().-]/g, "");
  if (E164.test(trimmed)) return trimmed;
  if (/^00\d{7,15}$/.test(trimmed)) return `+${trimmed.slice(2)}`;
  if (/^\d{7,15}$/.test(trimmed)) return `+${defaultCountryCode}${trimmed}`;
  return trimmed;
}

export function evaluateOutboundPolicy(input: OutboundPolicyInput): PolicyDecision {
  const to = normalizeNumber(input.to);
  if (!isE164(to)) {
    return { allowed: false, code: "invalid_number", reason: "destination is not a valid E.164 number" };
  }
  if (!input.consentGranted) {
    return { allowed: false, code: "consent_missing", reason: "outbound calling requires recorded consent" };
  }
  if (!input.tenant.outboundEnabled) {
    return { allowed: false, code: "outbound_disabled", reason: "outbound calling is disabled for this tenant" };
  }
  const dncNormalized = (input.tenant.dncList ?? []).map((entry) => normalizeNumber(entry));
  if (dncNormalized.includes(to)) {
    return {
      allowed: false,
      code: "dnc_listed",
      reason: "destination is on the Do-Not-Call (DNC) suppression list",
    };
  }
  if (input.tenant.outboundAllowlist.length > 0 && !input.tenant.outboundAllowlist.map((n) => normalizeNumber(n)).includes(to)) {
    return {
      allowed: false,
      code: "not_allowlisted",
      reason: "destination is not on the tenant outbound allowlist",
    };
  }
  if (input.tenant.dailyOutboundCap <= 0 || input.callsToday >= input.tenant.dailyOutboundCap) {
    return { allowed: false, code: "daily_cap", reason: "daily outbound cap reached" };
  }
  if (
    input.tenant.maxConcurrentCalls !== undefined &&
    (input.tenant.maxConcurrentCalls <= 0 || (input.activeCalls ?? 0) >= input.tenant.maxConcurrentCalls)
  ) {
    return {
      allowed: false,
      code: "concurrent_cap",
      reason: "per-tenant concurrent call limit reached",
    };
  }
  if (
    input.tenant.dailyMinuteQuota !== undefined &&
    (input.tenant.dailyMinuteQuota <= 0 || (input.minutesToday ?? 0) >= input.tenant.dailyMinuteQuota)
  ) {
    return {
      allowed: false,
      code: "daily_minute_quota",
      reason: "daily outbound minute quota exhausted",
    };
  }
  if (
    input.tenant.monthlyMinuteQuota !== undefined &&
    (input.tenant.monthlyMinuteQuota <= 0 || (input.minutesThisMonth ?? 0) >= input.tenant.monthlyMinuteQuota)
  ) {
    return {
      allowed: false,
      code: "monthly_minute_quota",
      reason: "monthly outbound minute quota exhausted",
    };
  }
  if (input.callingWindow && !insideWindow(input.now, input.callingWindow, input.timeZone)) {
    return {
      allowed: false,
      code: "outside_calling_window",
      reason: "outside the permitted local calling window",
    };
  }
  return { allowed: true };
}

export function insideWindow(
  now: Date,
  window: { start: string; end: string; days: number[] },
  timeZone = "UTC",
): boolean {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    weekday: "short",
    hour12: false,
  }).formatToParts(now);

  const lookup = (type: string) => parts.find((part) => part.type === type)?.value ?? "";
  const weekdayName = lookup("weekday");
  const dayIndex = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(weekdayName);
  if (window.days.length > 0 && dayIndex >= 0 && !window.days.includes(dayIndex)) return false;

  const hour = Number(lookup("hour") === "24" ? "0" : lookup("hour"));
  const minute = Number(lookup("minute"));
  const current = hour * 60 + minute;
  const [startH = 0, startM = 0] = window.start.split(":").map(Number);
  const [endH = 23, endM = 59] = window.end.split(":").map(Number);
  const start = startH * 60 + startM;
  const end = endH * 60 + endM;
  return start <= end ? current >= start && current <= end : current >= start || current <= end;
}

/**
 * SSRF URL pre-check for outbound HTTP done on behalf of a model or workflow.
 * Connect-time DNS resolution + socket IP pinning is enforced by ssrf-guard.ts.
 */
export interface UrlPolicyOptions {
  allowedHosts?: string[];
  allowPrivate?: boolean;
}

export function isPrivateOrReservedIp(rawAddress: string): boolean {
  const cleaned = rawAddress.replace(/^\[|\]$/g, "").split("%")[0]?.trim().toLowerCase() ?? "";
  if (!cleaned) return true;

  const version = net.isIP(cleaned);
  if (version === 4) {
    const octets = cleaned.split(".").map(Number);
    if (octets.length !== 4 || octets.some((n) => !Number.isInteger(n) || n < 0 || n > 255)) return true;
    const [a = 0, b = 0, c = 0] = octets;
    if (a === 0) return true; // 0.0.0.0/8
    if (a === 10) return true; // 10.0.0.0/8 RFC1918
    if (a === 127) return true; // 127.0.0.0/8 loopback
    if (a === 169 && b === 254) return true; // 169.254.0.0/16 link-local + IMDS
    if (a === 172 && b >= 16 && b <= 31) return true; // 172.16.0.0/12 RFC1918
    if (a === 192 && b === 168) return true; // 192.168.0.0/16 RFC1918
    if (a === 100 && b >= 64 && b <= 127) return true; // 100.64.0.0/10 CGNAT
    if (a === 192 && b === 0 && (c === 0 || c === 2)) return true;
    if (a === 198 && (b === 18 || b === 19 || (b === 51 && c === 100))) return true;
    if (a === 203 && b === 0 && c === 113) return true;
    if (a >= 224) return true; // multicast + broadcast + reserved
    return false;
  }

  if (version === 6) {
    const groups = expandIpv6(cleaned);
    if (!groups) return true;
    const allZeroExceptLast = groups.slice(0, 7).every((g) => g === 0);
    if (allZeroExceptLast && (groups[7] === 0 || groups[7] === 1)) {
      return true; // :: unspecified or ::1 loopback
    }
    // IPv4-mapped IPv6 ::ffff:0:0/96 or IPv4-compatible ::a.b.c.d
    const prefixZeros = groups.slice(0, 5).every((g) => g === 0);
    if (prefixZeros && (groups[5] === 0xffff || groups[5] === 0)) {
      const hi = groups[6] ?? 0;
      const lo = groups[7] ?? 0;
      const ipv4 = `${(hi >> 8) & 0xff}.${hi & 0xff}.${(lo >> 8) & 0xff}.${lo & 0xff}`;
      return isPrivateOrReservedIp(ipv4);
    }
    // NAT64 64:ff9b::/96 (RFC 6052) and local-use NAT64 64:ff9b:1::/48 (RFC 8215)
    if (groups[0] === 0x0064 && groups[1] === 0xff9b) {
      if (groups[2] === 0x0001) return true;
      const hi = groups[6] ?? 0;
      const lo = groups[7] ?? 0;
      const ipv4 = `${(hi >> 8) & 0xff}.${hi & 0xff}.${(lo >> 8) & 0xff}.${lo & 0xff}`;
      return isPrivateOrReservedIp(ipv4);
    }
    // 6to4 2002::/16
    if (groups[0] === 0x2002) {
      const hi = groups[1] ?? 0;
      const lo = groups[2] ?? 0;
      const ipv4 = `${(hi >> 8) & 0xff}.${hi & 0xff}.${(lo >> 8) & 0xff}.${lo & 0xff}`;
      return isPrivateOrReservedIp(ipv4);
    }
    const g0 = groups[0] ?? 0;
    if ((g0 & 0xffc0) === 0xfe80) return true; // fe80::/10 link-local
    if ((g0 & 0xfe00) === 0xfc00) return true; // fc00::/7 ULA
    if ((g0 & 0xff00) === 0xff00) return true; // ff00::/8 multicast
    if (g0 === 0x2001 && groups[1] === 0x0db8) return true; // documentation
    return false;
  }

  return false;
}

function expandIpv6(addr: string): number[] | null {
  let working = addr;
  // Convert trailing dotted-quad IPv4 (e.g. ::ffff:127.0.0.1) into two hex groups
  const lastColon = working.lastIndexOf(":");
  if (lastColon >= 0 && working.slice(lastColon + 1).includes(".")) {
    const v4Part = working.slice(lastColon + 1);
    if (net.isIP(v4Part) !== 4) return null;
    const octets = v4Part.split(".").map(Number);
    const hi = (((octets[0] ?? 0) << 8) | (octets[1] ?? 0)).toString(16);
    const lo = (((octets[2] ?? 0) << 8) | (octets[3] ?? 0)).toString(16);
    working = `${working.slice(0, lastColon + 1)}${hi}:${lo}`;
  }

  const halves = working.split("::");
  if (halves.length > 2) return null;
  const left = halves[0] ? halves[0].split(":").filter(Boolean) : [];
  const right = halves.length === 2 && halves[1] ? halves[1].split(":").filter(Boolean) : [];
  const missing = halves.length === 2 ? 8 - (left.length + right.length) : 0;
  if (missing < 0) return null;
  const full = halves.length === 2 ? [...left, ...Array<string>(missing).fill("0"), ...right] : left;
  if (full.length !== 8) return null;
  const nums = full.map((part) => Number.parseInt(part, 16));
  if (nums.some((n) => !Number.isInteger(n) || n < 0 || n > 0xffff)) return null;
  return nums;
}

export function evaluateUrl(rawUrl: string, options: UrlPolicyOptions = {}): { allowed: boolean; reason?: string } {
  let url: URL;
  try {
    url = new URL(rawUrl);
  } catch {
    return { allowed: false, reason: "invalid URL" };
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") {
    return { allowed: false, reason: "only http(s) URLs are permitted" };
  }
  if (url.username || url.password) {
    return { allowed: false, reason: "URLs with embedded credentials are not permitted" };
  }
  const bareHost = url.hostname.replace(/^\[|\]$/g, "").replace(/\.+$/, "").toLowerCase();
  if (!bareHost) {
    return { allowed: false, reason: "empty hostname is not permitted" };
  }
  if (options.allowedHosts && options.allowedHosts.length > 0) {
    const allowedNormalized = options.allowedHosts.map((h) =>
      h.replace(/^\[|\]$/g, "").replace(/\.+$/, "").toLowerCase(),
    );
    if (!allowedNormalized.includes(bareHost)) {
      return { allowed: false, reason: `host ${url.hostname} is not allowlisted` };
    }
    return { allowed: true };
  }
  if (options.allowPrivate) return { allowed: true };

  if (
    bareHost === "localhost" ||
    bareHost === "metadata.google.internal" ||
    bareHost === "metadata" ||
    bareHost.endsWith(".localhost") ||
    bareHost.endsWith(".internal") ||
    bareHost.endsWith(".local")
  ) {
    return { allowed: false, reason: "private host is blocked" };
  }
  // Block integer / hex / octal IPv4 hostnames bypassed by naive regexes
  if (/^(0x[0-9a-f]+|\d+)$/i.test(bareHost)) {
    return { allowed: false, reason: "numeric IP literal host is blocked" };
  }
  if (net.isIP(bareHost) !== 0 && isPrivateOrReservedIp(bareHost)) {
    return { allowed: false, reason: "private or loopback IP address is blocked" };
  }
  return { allowed: true };
}

/**
 * Fixed-window rate limiter. Deterministic and dependency-free; suitable for
 * the single-process local core. A distributed deployment swaps the store.
 */
export class RateLimiter {
  private readonly buckets = new Map<string, { count: number; resetAt: number }>();

  constructor(
    private readonly limit: number,
    private readonly windowMs: number,
    private readonly now: () => number = () => Date.now(),
  ) {}

  take(key: string): { allowed: boolean; remaining: number; retryAfterMs: number } {
    const time = this.now();
    const bucket = this.buckets.get(key);
    if (!bucket || bucket.resetAt <= time) {
      this.buckets.set(key, { count: 1, resetAt: time + this.windowMs });
      return { allowed: true, remaining: this.limit - 1, retryAfterMs: 0 };
    }
    bucket.count += 1;
    const allowed = bucket.count <= this.limit;
    return {
      allowed,
      remaining: Math.max(0, this.limit - bucket.count),
      retryAfterMs: allowed ? 0 : Math.max(0, bucket.resetAt - time),
    };
  }

  prune(): void {
    const time = this.now();
    for (const [key, bucket] of this.buckets) {
      if (bucket.resetAt <= time) this.buckets.delete(key);
    }
  }
}

const RESERVED_TRUST_VARIABLE_KEYS = new Set([
  "callerVerifiedSecondary",
  "callerNumberVerified",
  "stirShakenAttestation",
]);

/**
 * OM-T2: strips server-only caller attestation / step-up verification keys from
 * untrusted caller or API `variables` maps so untrusted inputs can never forge them.
 */
export function sanitizeUntrustedCallVariables<T extends Record<string, unknown>>(vars: T | undefined): T {
  const out: Record<string, unknown> = {};
  if (!vars) return out as T;
  for (const [key, val] of Object.entries(vars)) {
    if (RESERVED_TRUST_VARIABLE_KEYS.has(key)) continue;
    out[key] = val;
  }
  return out as T;
}
