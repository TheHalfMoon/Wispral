#!/usr/bin/env node
// Ordered workspace build. Dependency order is explicit so a partial failure
// never leaves a package resolving a stale declaration file.
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const order = [
  "packages/core",
  "packages/providers",
  "packages/workflow",
  "packages/telephony",
  "packages/sdk",
  "sdks/typescript",
  "packages/server",
  "packages/cli",
  "packages/mcp",
];

for (const pkg of order) {
  process.stdout.write(`\n[build] ${pkg}\n`);
  const result = spawnSync(
    process.execPath,
    [path.join(root, "node_modules/typescript/bin/tsc"), "-p", path.join(pkg, "tsconfig.json")],
    { cwd: root, stdio: "inherit", shell: false },
  );
  if (result.status !== 0) {
    process.stderr.write(`\n[build] FAILED: ${pkg} (exit ${result.status ?? "unknown"})\n`);
    process.exit(result.status ?? 1);
  }
}

process.stdout.write("\n[build] ok\n");
