/**
 * Shared harness for the smoke scripts: starts the built Omalla server on a
 * random loopback port with a throwaway data directory and mock voice
 * providers, and tears it down again. No carrier, no cost.
 */
import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..", "..");
const entry = path.join(root, "packages", "server", "dist", "bin", "serve.js");

export async function startServer(options = {}) {
  await stat(entry).catch(() => {
    throw new Error(`missing build output: ${entry}\nrun npm run build first`);
  });

  const dataDir = await mkdtemp(path.join(tmpdir(), options.prefix ?? "omalla-smoke-"));
  const port = 8721 + Math.floor(Math.random() * 2000);
  const baseUrl = `http://127.0.0.1:${port}`;
  const child = spawn(process.execPath, [entry], {
    cwd: root,
    env: {
      ...process.env,
      OMALLA_DATA_DIR: dataDir,
      OMALLA_PORT: String(port),
      OMALLA_HOST: "127.0.0.1",
      OMALLA_SEED_DEMO: "1",
      OMALLA_DEMO_VOICE: "mock",
      OMALLA_MASTER_KEY: Buffer.alloc(32, 7).toString("base64"),
      ...(options.env ?? {}),
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  let output = "";
  child.stdout.on("data", (chunk) => {
    output += String(chunk);
  });
  child.stderr.on("data", (chunk) => {
    output += String(chunk);
  });

  async function stop() {
    if (child.exitCode === null && !child.killed) child.kill();
    await new Promise((resolve) => setTimeout(resolve, 400));
    await rm(dataDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 }).catch(() => {});
  }

  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      await stop();
      throw new Error(`server exited early:\n${output}`);
    }
    try {
      const response = await fetch(`${baseUrl}/v1/health`, { signal: AbortSignal.timeout(1500) });
      if (response.ok) {
        const health = await response.json();
        const apiKey = (await readFile(path.join(dataDir, "api-key.txt"), "utf8")).trim();
        return { baseUrl, apiKey, dataDir, health, stop, output: () => output, root };
      }
    } catch {
      // not listening yet
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  await stop();
  throw new Error(`server did not become healthy:\n${output}`);
}
