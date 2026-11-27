import assert from "node:assert/strict";
import { test } from "node:test";
import { redact, redactString } from "@omalla/core";

test("E.164 numbers and credentials are redacted from logs", () => {
  const line = "call from +15550001234 failed with Bearer abcdefghijklmnop and sk-abcdefghijklmnopqrst";
  const redacted = redactString(line);
  assert.match(redacted, /\[REDACTED_NUMBER\]/);
  assert.match(redacted, /\[REDACTED\]/);
  assert.doesNotMatch(redacted, /15550001234/);
  assert.doesNotMatch(redacted, /abcdefghijklmnopqrst/);
});

test("short business identifiers are not mistaken for phone numbers", () => {
  assert.equal(redactString("order 12345678 shipped"), "order 12345678 shipped");
  assert.equal(redactString("port 8787 listening"), "port 8787 listening");
});

test("secret-looking object keys are dropped even when the value is nested", () => {
  const output = redact({
    tenant: "ten_1",
    credentials: { apiKey: "plain", token: "plain" },
    note: "caller +15550009999",
  }) as Record<string, unknown>;
  assert.equal(output.tenant, "ten_1");
  assert.equal(output.credentials, "[REDACTED]");
  assert.match(String(output.note), /\[REDACTED_NUMBER\]/);
});
