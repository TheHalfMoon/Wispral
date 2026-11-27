import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import {
  NOT_JSON,
  OPENAPI_OPERATIONS,
  PROVIDER_FACING,
  OmallaRuntime,
  buildApp,
  loadConfig,
  openApiDocument,
} from "@omalla/server";

/** `/v1/agents/:id` (Fastify) and `/v1/agents/{id}` (OpenAPI) name the same route. */
const normalise = (url: string): string => url.replace(/:([A-Za-z0-9_]+)/g, "{$1}");

test("the OpenAPI document matches the routes Fastify actually serves", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "omalla-openapi-"));
  const config = loadConfig({
    dataDir: dir,
    seedDemo: true,
    port: 0,
    masterKey: Buffer.alloc(32, 11).toString("base64"),
  });
  const runtime = await OmallaRuntime.open(config);
  const routes: Array<{ method: string; url: string }> = [];
  const app = await buildApp(runtime, {
    onRoute: (route) => {
      for (const method of Array.isArray(route.method) ? route.method : [route.method]) {
        routes.push({ method: method.toLowerCase(), url: normalise(route.url) });
      }
    },
  });

  try {
    const document = openApiDocument() as {
      openapi: string;
      paths: Record<string, Record<string, unknown>>;
      components: { schemas: Record<string, unknown> };
    };
    assert.equal(document.openapi, "3.1.0");

    const documented = new Set<string>();
    for (const [url, item] of Object.entries(document.paths)) {
      for (const method of Object.keys(item)) {
        documented.add(`${method.toUpperCase()} ${url}`);
        const operation = item[method] as { responses?: Record<string, unknown>; tags?: string[] };
        assert.ok(operation.responses && Object.keys(operation.responses).length > 0, `${method} ${url} has no responses`);
        assert.ok(operation.tags && operation.tags.length > 0, `${method} ${url} has no tag`);
      }
    }

    // Forward: everything the document promises is really served.
    for (const operation of OPENAPI_OPERATIONS) {
      assert.equal(
        app.hasRoute({ method: operation.method.toUpperCase() as "GET", url: operation.path.replace(/\{([^}]+)\}/g, ":$1") }),
        true,
        `documented but not served: ${operation.method} ${operation.path}`,
      );
    }

    // Reverse: every /v1 JSON route is documented (or explicitly excluded).
    const exempt = new Set<string>([
      ...PROVIDER_FACING,
      ...NOT_JSON,
    ]);
    const missing: string[] = [];
    for (const route of routes) {
      if (!route.url.startsWith("/v1/") && route.url !== "/v1") continue;
      // Fastify derives HEAD from every GET; OpenAPI does not spell it out.
      if (route.method === "head") continue;
      if (route.url === "/openapi.json") continue;
      const key = `${route.method.toUpperCase()} ${route.url}`;
      if (documented.has(key) || exempt.has(key)) continue;
      missing.push(key);
    }
    assert.deepEqual(missing, [], `served but undocumented: ${missing.join(", ")}`);

    // The excluded sets are real routes, not stale names.
    for (const key of exempt) {
      const [method, url] = key.split(" ") as [string, string];
      assert.equal(
        app.hasRoute({ method: method as "GET", url: url.replace(/\{([^}]+)\}/g, ":$1") }),
        true,
        `excluded route does not exist: ${key}`,
      );
    }

    // Every $ref resolves, so validators do not reject the document.
    const serialised = JSON.stringify(document);
    const names = new Set(Object.keys(document.components.schemas));
    for (const match of serialised.matchAll(/"\$ref":"#\/components\/schemas\/([^"]+)"/g)) {
      assert.ok(names.has(match[1] ?? ""), `dangling $ref: ${match[1]}`);
    }

    // The served document is byte-identical to the module's document.
    const address = await app.listen({ host: "127.0.0.1", port: 0 });
    const response = await fetch(`${address}/openapi.json`);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), document);
  } finally {
    await app.close();
    await runtime.close();
    await rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
  }
});
