/**
 * End-to-end smoke test against a real server process.
 *
 * Starts the built server on a loopback port with a throwaway data directory,
 * then exercises health, telephony, calls, SMS, automation and dashboard assets
 * over HTTP. No carrier, no network, no cost: the demo voice provider is mocked.
 */
import { startServer } from "./lib/server-harness.mjs";

const failures = [];
function check(name, condition, detail = "") {
  if (condition) {
    console.log(`  PASS  ${name}${detail ? `  (${detail})` : ""}`);
  } else {
    console.log(`  FAIL  ${name}${detail ? `  (${detail})` : ""}`);
    failures.push(name);
  }
}

let server;
try {
  server = await startServer();
  const { baseUrl, apiKey, health } = server;

  async function api(pathname, init = {}) {
    const response = await fetch(`${baseUrl}${pathname}`, {
      ...init,
      headers: {
        authorization: `Bearer ${apiKey}`,
        "content-type": "application/json",
        ...(init.headers ?? {}),
      },
    });
    const text = await response.text();
    let body;
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
    return { status: response.status, body };
  }

  console.log("\nhealth and auth");
  check("health reports ok", health.ok === true);
  check("default provider is simulated", health.telephonyDefault === "simulated");
  check("API key was issued", apiKey.startsWith("omk_"), `${apiKey.slice(0, 7)}…${apiKey.slice(-4)}`);
  const unauthorized = await fetch(`${baseUrl}/v1/calls`);
  check("unauthenticated request is refused", unauthorized.status === 401);

  console.log("\ntelephony");
  const providers = await api("/v1/telephony/providers");
  check("provider list returns 200", providers.status === 200 && Array.isArray(providers.body));
  const simulated = (providers.body ?? []).find((item) => item.id === "simulated");
  check("simulated provider is available", simulated?.available === true);
  check(
    "carriers are reported unavailable without credentials",
    (providers.body ?? [])
      .filter((item) => item.id !== "simulated")
      .every((item) => item.available === false),
  );
  check("simulator is not claimed to be PSTN", /no pstn/i.test(String(simulated?.detail ?? "")));

  const numbers = await api("/v1/numbers");
  check("number list returns the seeded simulated number", numbers.status === 200 && numbers.body.length >= 1);
  const search = await api("/v1/numbers/search", {
    method: "POST",
    body: JSON.stringify({ areaCode: "555" }),
  });
  check("number search works without spending money", search.status === 200);
  check(
    "search says whether carrier charges apply",
    search.body?.carrierCharges === false && Array.isArray(search.body?.offers),
    `${search.body?.offers?.length ?? 0} offers`,
  );

  console.log("\nsimulated call");
  const created = await api("/v1/calls", {
    method: "POST",
    body: JSON.stringify({
      to: "+15550001234",
      from: "+15550009999",
      say: ["I would like to book a cleaning for Tuesday at 10am."],
    }),
  });
  check("call creation returns 201", created.status === 201, `status ${created.status}`);
  const call = created.body;
  check("call is labelled simulated", call?.simulation === true);
  check("call reached the demo agent", typeof call?.id === "string" && Boolean(call?.agentId));

  const detail = await api(`/v1/calls/${call.id}`);
  const turns = detail.body?.transcript ?? [];
  check("call detail is readable", detail.status === 200);
  check("transcript captured both sides", turns.length >= 2, `${turns.length} turns`);
  check(
    "assistant replied with text",
    turns.some((turn) => turn.role === "assistant" && String(turn.text ?? "").length > 0),
  );
  check(
    "call recorded latency metrics",
    typeof detail.body?.metrics?.turnCount === "number" && detail.body.metrics.turnCount >= 1,
    `turns=${detail.body?.metrics?.turnCount}`,
  );

  console.log("\nsms");
  const sms = await api("/v1/sms", {
    method: "POST",
    body: JSON.stringify({ to: "+15550002222", body: "Omalla smoke test", consent: true }),
  });
  check("SMS accepted with consent", sms.status === 201, `status ${sms.status}`);
  check("SMS is labelled simulated", sms.body?.simulated === true);
  const noConsent = await api("/v1/sms", {
    method: "POST",
    body: JSON.stringify({ to: "+15550002222", body: "no consent", consent: false }),
  });
  check("SMS without consent is refused by policy", noConsent.status === 403, `status ${noConsent.status}`);
  const missingConsent = await api("/v1/sms", {
    method: "POST",
    body: JSON.stringify({ to: "+15550002222", body: "no consent field" }),
  });
  check("SMS without a consent field fails validation", missingConsent.status === 400, `status ${missingConsent.status}`);

  console.log("\nautomation");
  const workflows = await api("/v1/workflows");
  const templates = await api("/v1/templates");
  check("workflow list returns 200", workflows.status === 200 && Array.isArray(workflows.body));
  check(
    "templates are available",
    templates.status === 200 && Array.isArray(templates.body) && templates.body.length >= 10,
    `${templates.body?.length ?? 0} templates`,
  );
  const runs = await api("/v1/runs");
  check("workflow run history is readable", runs.status === 200);

  console.log("\ndashboard");
  const page = await fetch(`${baseUrl}/`);
  const html = await page.text();
  check("dashboard HTML is served", page.status === 200 && page.headers.get("content-type")?.includes("text/html"));
  check("dashboard has the Omalla shell", html.includes("Omalla") && html.includes("Telephony"));
  const script = await fetch(`${baseUrl}/app.js`);
  const js = await script.text();
  check("dashboard script is served", script.status === 200 && js.includes("renderTelephony"));
  check("dashboard script is not a stub", js.length > 10000);

  console.log("\nopenapi");
  const spec = await fetch(`${baseUrl}/openapi.json`);
  const document = await spec.json();
  check("OpenAPI document is served without a key", spec.status === 200 && document.openapi === "3.1.0");
  check("OpenAPI documents the call API", Boolean(document.paths?.["/v1/calls"]?.post));
  check(
    "OpenAPI covers the documented surface",
    Object.keys(document.paths ?? {}).length >= 40,
    `${Object.keys(document.paths ?? {}).length} paths`,
  );
  check("OpenAPI declares bearer auth", document.components?.securitySchemes?.bearerAuth?.scheme === "bearer");

  console.log("\nresult");
  if (failures.length > 0) {
    console.error(`${failures.length} check(s) failed: ${failures.join(", ")}`);
    process.exitCode = 1;
  } else {
    console.log("  all smoke checks passed");
  }
} catch (error) {
  console.error(String(error instanceof Error ? error.message : error));
  process.exitCode = 1;
} finally {
  await server?.stop();
}
