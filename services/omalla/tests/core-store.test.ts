import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { Database, nowIso } from "@omalla/core";

function contact(id: string) {
  return {
    id,
    tenantId: "ten_store",
    name: "Store Test",
    tags: [],
    attributes: {},
    createdAt: nowIso(),
    updatedAt: nowIso(),
  };
}

test("a failed background save is reported on the next flush, not as an unhandled rejection", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "omalla-store-"));
  // Make the parent of the database file a regular file so mkdir fails.
  const blocker = path.join(dir, "blocker");
  await writeFile(blocker, "not a directory", "utf8");

  const db = await Database.open({ filePath: path.join(blocker, "db.json") });
  try {
    db.col("contacts").insert(contact("con_1"));

    // Wait past the 25 ms debounce so the background write fails and is
    // captured. An unhandled rejection here would fail the whole test file.
    await new Promise((resolve) => setTimeout(resolve, 80));

    await assert.rejects(() => db.flush(), /ENOTDIR|EEXIST|not a directory|ENOENT/i);
  } finally {
    await db.close().catch(() => {});
    await rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
  }
});

test("a durable write survives close and reload", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "omalla-store-"));
  const file = path.join(dir, "db.json");
  try {
    const db = await Database.open({ filePath: file });
    db.col("contacts").insert(contact("con_2"));
    await db.close();

    const reopened = await Database.open({ filePath: file });
    try {
      assert.equal(reopened.col("contacts").get("con_2")?.name, "Store Test");
    } finally {
      await reopened.close();
    }
  } finally {
    await rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
  }
});
