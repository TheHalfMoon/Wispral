import path from "node:path";

export interface OmallaConfig {
  dataDir: string;
  host: string;
  port: number;
  /** Bind to every interface only when explicitly requested. */
  allowRemote: boolean;
  seedDemo: boolean;
  allowPrivateHttp: boolean;
  /** Carrier number purchases and releases stay off until an owner opts in. */
  allowCarrierPurchases: boolean;
  /** Allow multi-tenant process.env fallback for allowlisted provider API keys. */
  allowSharedEnvCredentials?: boolean;
  masterKey?: string;
  publicBaseUrl: string;
}

export function loadConfig(overrides: Partial<OmallaConfig> = {}): OmallaConfig {
  const dataDir = overrides.dataDir ?? process.env.OMALLA_DATA_DIR ?? path.resolve(process.cwd(), ".omalla");
  const host = overrides.host ?? process.env.OMALLA_HOST ?? "127.0.0.1";
  return {
    dataDir,
    host,
    port: overrides.port ?? Number(process.env.OMALLA_PORT ?? 8787),
    allowRemote: overrides.allowRemote ?? process.env.OMALLA_ALLOW_REMOTE === "1",
    seedDemo: overrides.seedDemo ?? process.env.OMALLA_SEED_DEMO !== "0",
    allowPrivateHttp: overrides.allowPrivateHttp ?? process.env.OMALLA_ALLOW_PRIVATE_HTTP === "1",
    allowCarrierPurchases: overrides.allowCarrierPurchases ?? process.env.OMALLA_ALLOW_CARRIER_PURCHASES === "1",
    allowSharedEnvCredentials:
      overrides.allowSharedEnvCredentials ?? process.env.OMALLA_ALLOW_SHARED_ENV_CREDENTIALS === "1",
    ...(overrides.masterKey ?? process.env.OMALLA_MASTER_KEY
      ? { masterKey: overrides.masterKey ?? process.env.OMALLA_MASTER_KEY }
      : {}),
    publicBaseUrl: overrides.publicBaseUrl ?? process.env.OMALLA_BASE_URL ?? "http://127.0.0.1:8787",
  };
}

export function resolveHosts(config: OmallaConfig): string[] {
  // Fastify binds one address per instance, so this deliberately returns one
  // host. Dual-stack loopback needs a proxy or a second listener, not a loop
  // that calls listen twice.
  if (config.allowRemote) return [config.host === "0.0.0.0" ? "0.0.0.0" : config.host];
  return ["127.0.0.1"];
}
