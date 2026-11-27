import path from "node:path";
import { readFile } from "node:fs/promises";
import { buildApp, loadConfig, resolveHosts } from "@omalla/server";
import { OmallaRuntime } from "@omalla/server";

export interface StartOptions {
  dataDir?: string;
  port?: number;
  host?: string;
  seed?: boolean;
  allowRemote?: boolean;
}

/**
 * Runs the server in the foreground.
 *
 * `omalla start` deliberately runs in-process rather than spawning a daemon:
 * a single foreground process is easier to reason about, logs to the same
 * terminal, and Ctrl-C always stops it.
 */
export async function startServer(options: StartOptions = {}): Promise<void> {
  const config = loadConfig({
    ...(options.dataDir ? { dataDir: path.resolve(options.dataDir) } : {}),
    ...(options.port ? { port: options.port } : {}),
    ...(options.host ? { host: options.host } : {}),
    ...(options.seed === false ? { seedDemo: false } : {}),
    ...(options.allowRemote ? { allowRemote: true } : {}),
  });

  const runtime = await OmallaRuntime.open(config);
  const app = await buildApp(runtime);
  const host = resolveHosts(config)[0] ?? "127.0.0.1";
  await app.listen({ host, port: config.port });

  const keyFile = path.join(config.dataDir, "api-key.txt");
  const token = (await readFile(keyFile, "utf8").catch(() => undefined))?.trim();

  process.stdout.write(
    [
      "",
      "  Omalla 0.1.0 — local-first voice + automation",
      "",
      `  Console   http://127.0.0.1:${config.port}/`,
      `  API       http://127.0.0.1:${config.port}/v1`,
      `  Data      ${config.dataDir}`,
      token
        ? `  API key   ${token.slice(0, 12)}…   (full key: ${keyFile})`
        : "  API key   none yet — run `omalla keys create --name cli`",
      "",
      "  Telephony is simulated. No carrier, cloud model or paid service is contacted.",
      "  Press Ctrl-C to stop.",
      "",
    ].join("\n"),
  );

  const shutdown = async (signal: string) => {
    process.stdout.write(`\n  stopping (${signal})…\n`);
    await app.close().catch(() => undefined);
    await runtime.close().catch(() => undefined);
    process.exit(0);
  };
  process.on("SIGINT", () => void shutdown("SIGINT"));
  process.on("SIGTERM", () => void shutdown("SIGTERM"));
}
