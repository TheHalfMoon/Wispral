/**
 * Live smoke test for the Python SDK against a real Omalla server.
 *
 * Boots the built server exactly like `npm run smoke`, then runs
 * sdks/python/tests/live_smoke.py with the base URL and API key. Simulated
 * provider only: no carrier and no cost. Requires Python 3.9+ on PATH.
 */
import { spawn } from "node:child_process";
import path from "node:path";
import { startServer } from "./lib/server-harness.mjs";

let server;
try {
  server = await startServer({ prefix: "omalla-python-" });
  const python = process.platform === "win32" ? "python" : "python3";
  const script = path.join(server.root, "sdks", "python", "tests", "live_smoke.py");

  console.log(`python sdk smoke against ${server.baseUrl}\n`);
  const child = spawn(python, [script], {
    cwd: server.root,
    env: {
      ...process.env,
      PYTHONPATH: [path.join(server.root, "sdks", "python"), process.env.PYTHONPATH]
        .filter(Boolean)
        .join(path.delimiter),
      PYTHONIOENCODING: "utf-8",
      OMALLA_BASE_URL: server.baseUrl,
      OMALLA_API_KEY: server.apiKey,
    },
    stdio: "inherit",
  });

  const code = await new Promise((resolve) => child.on("exit", (value) => resolve(value ?? 1)));
  if (code !== 0) {
    console.error(`\npython sdk smoke failed with exit code ${code}`);
    process.exitCode = 1;
  }
} catch (error) {
  console.error(String(error instanceof Error ? error.message : error));
  process.exitCode = 1;
} finally {
  await server?.stop();
}
