#!/usr/bin/env node
import path from "node:path";
import { readFile } from "node:fs/promises";
import { buildApp } from "../app.js";
import { loadConfig, resolveHosts } from "../config.js";
import { OmallaRuntime } from "../runtime.js";

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const flag = (name: string): string | undefined => {
    const index = args.indexOf(`--${name}`);
    return index >= 0 ? args[index + 1] : undefined;
  };

  const config = loadConfig({
    ...(flag("data-dir") ? { dataDir: path.resolve(flag("data-dir") as string) } : {}),
    ...(flag("port") ? { port: Number(flag("port")) } : {}),
    ...(flag("host") ? { host: flag("host") as string } : {}),
    ...(args.includes("--no-seed") ? { seedDemo: false } : {}),
    ...(args.includes("--allow-remote") ? { allowRemote: true } : {}),
  });

  const runtime = await OmallaRuntime.open(config);
  const app = await buildApp(runtime);
  const host = resolveHosts(config)[0] ?? "127.0.0.1";
  await app.listen({ host, port: config.port });

  const token = await readFile(path.join(config.dataDir, "api-key.txt"), "utf8").catch(() => undefined);
  const shown = token?.trim().slice(0, 12) ?? "run `omalla keys create`";

  process.stdout.write(
    [
      "",
      "  Omalla v0.1.0 — local-first voice + automation",
      "",
      `  Dashboard   http://127.0.0.1:${config.port}/`,
      `  API         http://127.0.0.1:${config.port}/v1`,
      `  Data        ${config.dataDir}`,
      `  API key     ${token ? `${shown}… (full key in data/api-key.txt)` : shown}`,
      "",
      "  All calls are simulated. No carrier, cloud model or paid service is contacted.",
      "",
    ].join("\n"),
  );

  const shutdown = async (signal: string) => {
    runtime.logger.info("shutting down", { signal });
    await app.close();
    await runtime.close();
    process.exit(0);
  };
  process.on("SIGINT", () => void shutdown("SIGINT"));
  process.on("SIGTERM", () => void shutdown("SIGTERM"));
}

main().catch((error) => {
  process.stderr.write(`omalla failed to start: ${(error as Error).message}\n`);
  process.exit(1);
});
