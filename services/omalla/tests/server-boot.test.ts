import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { OmallaRuntime, buildApp, loadConfig, resolveHosts } from "@omalla/server";

test("the server binds one loopback host and answers health over HTTP", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "omalla-boot-"));
  const config = loadConfig({
    dataDir: dir,
    seedDemo: true,
    port: 0,
    masterKey: Buffer.alloc(32, 9).toString("base64"),
  });

  // Regression: a previous version returned both 127.0.0.1 and ::1 and called
  // Fastify listen twice, which always failed with "already listening".
  assert.deepEqual(resolveHosts(config), ["127.0.0.1"]);

  const runtime = await OmallaRuntime.open(config);
  const app = await buildApp(runtime);
  try {
    const address = await app.listen({ host: resolveHosts(config)[0] ?? "127.0.0.1", port: 0 });
    assert.match(address, /^http:\/\/127\.0\.0\.1:\d+$/);
    const response = await fetch(`${address}/v1/health`);
    assert.equal(response.status, 200);
    const health = (await response.json()) as { ok?: boolean; telephonyDefault?: string };
    assert.equal(health.ok, true);
    assert.equal(health.telephonyDefault, "simulated");
  } finally {
    await app.close();
    await runtime.close();
    await rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
  }
});
