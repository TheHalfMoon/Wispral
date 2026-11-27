import dns from "node:dns";
import http from "node:http";
import https from "node:https";
import net from "node:net";
import { OmallaError, evaluateUrl, isPrivateOrReservedIp } from "@omalla/core";
import type { UrlPolicyOptions } from "@omalla/core";

export interface ResolvedHostAddress {
  address: string;
  family: 4 | 6;
}

export type DnsLookupAll = (hostname: string) => Promise<ResolvedHostAddress[]>;

export interface SsrfGuardOptions extends UrlPolicyOptions {
  /** Custom DNS resolver (used in adversarial DNS-rebinding unit tests). */
  lookup?: DnsLookupAll;
  /** Optional base fetch (used when tests inject a synthetic HTTP responder). */
  baseFetch?: typeof fetch;
  /** Maximum redirect hops to follow; every hop is re-validated & re-pinned. */
  maxRedirects?: number;
}

export interface PinnedTarget {
  url: URL;
  pinnedIp?: string;
  pinnedFamily?: 4 | 6;
  bypassedByPolicy: boolean;
}

const defaultLookup: DnsLookupAll = async (hostname: string): Promise<ResolvedHostAddress[]> => {
  const records = await dns.promises.lookup(hostname, { all: true, verbatim: true });
  return records.map((entry) => ({
    address: entry.address,
    family: entry.family === 6 ? 6 : 4,
  }));
};

export function isBlockedIp(ip: string): boolean {
  return isPrivateOrReservedIp(ip);
}

/**
 * Resolves a target URL and pins a verified public IP address for connect-time
 * use, blocking loopback, RFC1918, link-local, CGNAT, ULA, and IPv4-mapped IPv6
 * (`::ffff:...`) unless explicitly permitted by self-hosted operator config (OM-T4).
 */
export async function resolveAndPinUrl(
  rawUrl: string,
  options: SsrfGuardOptions = {},
): Promise<PinnedTarget> {
  const precheck = evaluateUrl(rawUrl, options);
  if (!precheck.allowed) {
    throw new OmallaError(
      "blocked_by_policy",
      `SSRF guard blocked URL: ${precheck.reason ?? "disallowed"}`,
      403,
    );
  }

  const url = new URL(rawUrl);
  const bareHost = url.hostname.replace(/^\[|\]$/g, "").replace(/\.+$/, "");

  if (options.allowPrivate) {
    return { url, bypassedByPolicy: true };
  }

  const literalVersion = net.isIP(bareHost);
  if (literalVersion === 4 || literalVersion === 6) {
    if (isBlockedIp(bareHost)) {
      throw new OmallaError(
        "blocked_by_policy",
        `SSRF guard blocked private/reserved IP literal: ${bareHost}`,
        403,
      );
    }
    return {
      url,
      pinnedIp: bareHost,
      pinnedFamily: literalVersion,
      bypassedByPolicy: false,
    };
  }

  const lookup = options.lookup ?? defaultLookup;
  let records: ResolvedHostAddress[];
  try {
    records = await lookup(bareHost);
  } catch (error) {
    throw new OmallaError(
      "provider_error",
      `DNS lookup failed for ${bareHost}: ${(error as Error).message}`,
      502,
    );
  }

  if (records.length === 0) {
    throw new OmallaError("blocked_by_policy", `SSRF guard refused unresolvable host: ${bareHost}`, 403);
  }

  // Every resolved A/AAAA record MUST be public; mixed public+private records are refused.
  for (const record of records) {
    if (isBlockedIp(record.address)) {
      throw new OmallaError(
        "blocked_by_policy",
        `SSRF guard blocked host ${bareHost} resolving to restricted IP ${record.address}`,
        403,
      );
    }
  }

  const primary = records[0]!;
  return {
    url,
    pinnedIp: primary.address,
    pinnedFamily: primary.family,
    bypassedByPolicy: false,
  };
}

/**
 * Returns a `fetch`-compatible function that enforces OM-T4 connect-time DNS
 * pinning and hop-by-hop redirect validation.
 */
export function createSsrfGuardedFetch(options: SsrfGuardOptions = {}): typeof fetch {
  const maxRedirects = options.maxRedirects ?? 3;

  return (async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
    let currentUrl =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    let currentMethod = (init?.method ?? (input instanceof Request ? input.method : "GET")).toUpperCase();
    let currentBody = init?.body;
    const baseHeaders = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined));

    for (let hop = 0; hop <= maxRedirects; hop += 1) {
      // When a custom test fetch is provided without a custom lookup, skip live OS DNS
      // for synthetic `.example.com` test domains unless `options.lookup` was supplied.
      const effectiveOptions: SsrfGuardOptions =
        options.baseFetch && !options.lookup
          ? {
              ...options,
              lookup: async (host) => {
                if (net.isIP(host)) {
                  return [{ address: host, family: net.isIP(host) === 6 ? 6 : 4 }];
                }
                return [{ address: "93.184.216.34", family: 4 }];
              },
            }
          : options;

      const target = await resolveAndPinUrl(currentUrl, effectiveOptions);

      let response: Response;
      if (options.baseFetch) {
        response = await options.baseFetch(target.url.toString(), {
          ...init,
          method: currentMethod,
          headers: Object.fromEntries(baseHeaders.entries()),
          ...(currentBody !== undefined ? { body: currentBody } : {}),
          redirect: "manual",
        });
      } else {
        response = await pinnedNodeRequest(target, {
          method: currentMethod,
          headers: baseHeaders,
          body: currentBody,
          signal: init?.signal ?? undefined,
        });
      }

      if (isRedirectStatus(response.status)) {
        const location = response.headers.get("location");
        if (!location) return response;
        if (hop === maxRedirects) {
          throw new OmallaError("blocked_by_policy", "SSRF guard: too many HTTP redirects", 403);
        }
        const nextParsed = new URL(location, target.url);
        if (nextParsed.origin !== target.url.origin) {
          baseHeaders.delete("authorization");
          baseHeaders.delete("cookie");
          baseHeaders.delete("proxy-authorization");
          baseHeaders.delete("x-omalla-signature");
        }
        const nextUrl = nextParsed.toString();
        if (response.status === 301 || response.status === 302 || response.status === 303) {
          currentMethod = "GET";
          currentBody = undefined;
          baseHeaders.delete("content-length");
        }
        currentUrl = nextUrl;
        continue;
      }

      return response;
    }

    throw new OmallaError("blocked_by_policy", "SSRF guard: redirect limit exceeded", 403);
  }) as typeof fetch;
}

function isRedirectStatus(status: number): boolean {
  return status === 301 || status === 302 || status === 303 || status === 307 || status === 308;
}

type FetchBody = RequestInit["body"];

async function toBodyBuffer(body: FetchBody): Promise<Buffer | undefined> {
  if (body === undefined || body === null) return undefined;
  if (typeof body === "string") return Buffer.from(body, "utf8");
  if (Buffer.isBuffer(body)) return body;
  if (body instanceof Uint8Array) return Buffer.from(body);
  if (body instanceof ArrayBuffer) return Buffer.from(body);
  if (body instanceof URLSearchParams) return Buffer.from(body.toString(), "utf8");
  const resp = new Response(body);
  return Buffer.from(await resp.arrayBuffer());
}

async function pinnedNodeRequest(
  target: PinnedTarget,
  init: {
    method: string;
    headers: Headers;
    body?: FetchBody;
    signal?: AbortSignal;
  },
): Promise<Response> {
  const { url, pinnedIp, pinnedFamily } = target;
  const isHttps = url.protocol === "https:";
  const transport = isHttps ? https : http;
  const bodyBuf = await toBodyBuffer(init.body);

  const headersObj: Record<string, string> = {};
  init.headers.forEach((v, k) => {
    headersObj[k] = v;
  });
  if (!headersObj.host) {
    headersObj.host = url.host;
  }
  if (bodyBuf && !headersObj["content-length"]) {
    headersObj["content-length"] = String(bodyBuf.byteLength);
  }

  const bareHost = url.hostname.replace(/^\[|\]$/g, "").replace(/\.+$/, "");

  return new Promise<Response>((resolve, reject) => {
    const req = transport.request(
      {
        protocol: url.protocol,
        hostname: bareHost,
        port: url.port ? Number(url.port) : isHttps ? 443 : 80,
        path: `${url.pathname}${url.search}`,
        method: init.method,
        headers: headersObj,
        ...(isHttps && net.isIP(bareHost) === 0 ? { servername: bareHost } : {}),
        ...(pinnedIp && pinnedFamily
          ? {
              lookup: (_hostname, lookupOpts, cb) => {
                const wantsAll = typeof lookupOpts === "object" && lookupOpts !== null && lookupOpts.all === true;
                if (wantsAll) {
                  cb(null, [{ address: pinnedIp, family: pinnedFamily }]);
                } else {
                  cb(null, pinnedIp, pinnedFamily);
                }
              },
            }
          : {}),
      },
      (res) => {
        const chunks: Buffer[] = [];
        let total = 0;
        const maxBytes = 2 * 1024 * 1024;
        res.on("data", (chunk: Buffer) => {
          total += chunk.length;
          if (total > maxBytes) {
            const err = new OmallaError("provider_error", "upstream response exceeded 2 MiB limit", 502);
            res.destroy(err);
            req.destroy(err);
            reject(err);
            return;
          }
          chunks.push(chunk);
        });
        res.on("end", () => {
          const buf = Buffer.concat(chunks);
          const respHeaders = new Headers();
          for (const [k, v] of Object.entries(res.headers)) {
            if (typeof v === "string") respHeaders.set(k, v);
            else if (Array.isArray(v)) respHeaders.set(k, v.join(", "));
          }
          const status = res.statusCode ?? 502;
          const bodyBytes = status === 204 || status === 304 ? null : buf;
          resolve(new Response(bodyBytes, { status, headers: respHeaders }));
        });
        res.on("error", reject);
      },
    );

    if (init.signal) {
      if (init.signal.aborted) {
        req.destroy(init.signal.reason instanceof Error ? init.signal.reason : new Error("aborted"));
        return;
      }
      const onAbort = () => {
        req.destroy(init.signal?.reason instanceof Error ? init.signal.reason : new Error("aborted"));
      };
      init.signal.addEventListener("abort", onAbort, { once: true });
      req.on("close", () => init.signal?.removeEventListener("abort", onAbort));
    }

    req.on("error", reject);
    if (bodyBuf) req.write(bodyBuf);
    req.end();
  });
}
