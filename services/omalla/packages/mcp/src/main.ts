#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import path from "node:path";
import { OmallaClient } from "@omalla/sdk";
import { runMcpServer } from "./server.js";

async function resolveKey(): Promise<string | undefined> {
  if (process.env.OMALLA_API_KEY) return process.env.OMALLA_API_KEY.trim();
  const dataDir = path.resolve(process.env.OMALLA_DATA_DIR ?? path.join(process.cwd(), ".omalla"));
  try {
    const token = (await readFile(path.join(dataDir, "api-key.txt"), "utf8")).trim();
    return token || undefined;
  } catch {
    return undefined;
  }
}

async function main(): Promise<void> {
  const apiKey = await resolveKey();
  if (!apiKey) {
    process.stderr.write(
      [
        "omalla-mcp: no API key.",
        "",
        "Set OMALLA_API_KEY, or run `omalla start` once so .omalla/api-key.txt exists.",
        "Point OMALLA_DATA_DIR at the data directory if it is not ./.omalla.",
        "",
      ].join("\n"),
    );
    process.exit(1);
  }

  const baseUrl = process.env.OMALLA_URL ?? `http://127.0.0.1:${process.env.OMALLA_PORT ?? 8787}`;
  const client = new OmallaClient({ apiKey, baseUrl });
  await runMcpServer({ client });
}

main().catch((error) => {
  process.stderr.write(`omalla-mcp: ${(error as Error).message}\n`);
  process.exit(1);
});
