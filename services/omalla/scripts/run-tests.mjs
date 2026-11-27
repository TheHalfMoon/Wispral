#!/usr/bin/env node
/**
 * Cross-platform Node 24 test runner.
 *
 * Avoids POSIX-only shell globbing ("tests/*.test.ts") so `npm test` runs
 * identically on Windows PowerShell, macOS, and Linux CI.
 */
import { spawnSync } from "node:child_process";
import { globSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const cliArgs = process.argv.slice(2);

const explicitFiles = cliArgs.filter((arg) => !arg.startsWith("-"));
const flags = cliArgs.filter((arg) => arg.startsWith("-"));

const files =
  explicitFiles.length > 0
    ? explicitFiles
    : globSync("tests/**/*.test.ts", { cwd: root }).sort();

if (files.length === 0) {
  process.stderr.write("[test] no test files matched tests/**/*.test.ts\n");
  process.exit(1);
}

const hasReporter = flags.some((flag) => flag.startsWith("--test-reporter"));
const nodeArgs = [
  "--test",
  ...(hasReporter ? [] : ["--test-reporter=spec"]),
  ...flags,
  ...files,
];

const result = spawnSync(process.execPath, nodeArgs, {
  cwd: root,
  stdio: "inherit",
  shell: false,
});

process.exit(result.status ?? 1);
