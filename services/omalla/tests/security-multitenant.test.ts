import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import http from "node:http";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import {
  Database,
  canonicalizeJcs,
  newId,
  normalizeArabicText,
  nowIso,
} from "@omalla/core";
import {
  LoopbackStt,
  LoopbackSynthTts,
  PiperTts,
  WhisperCppStt,
  WispralCoreStt,
  resolveProviders,
} from "@omalla/providers";
import {
  OmallaRuntime,
  buildApp,
  createSsrfGuardedFetch,
  loadConfig,
  parseSpokenDateTime,
} from "@omalla/server";
import { TelephonyRegistry, TwilioProvider } from "@omalla/telephony";
import { OmallaClient, jcsSha256, parseStreamFrames, verifyWebhookSignature } from "@omalla/typescript-sdk";

async function createTwoTenantFixture(extraConfig: { allowPrivateHttp?: boolean; allowCarrierPurchases?: boolean } = {}) {
  const dir = await mkdtemp(path.join(tmpdir(), "omalla-sec-"));
  let carrierCallCount = 0;
  let carrierSmsCount = 0;

  const twilio = new TwilioProvider({
    accountSid: "AC00000000000000000000000000000001",
    authToken: "twilio-test-secret",
    fetchImpl: async (url) => {
      const target = String(url);
      if (target.includes("/Messages.json")) {
        carrierSmsCount += 1;
        return new Response(JSON.stringify({ sid: `SM_${carrierSmsCount}`, status: "queued" }), {
          status: 201,
          headers: { "content-type": "application/json" },
        });
      }
      carrierCallCount += 1;
      return new Response(JSON.stringify({ sid: `CA_${carrierCallCount}`, status: "queued" }), {
        status: 201,
        headers: { "content-type": "application/json" },
      });
    },
  });

  const config = loadConfig({
    dataDir: dir,
    seedDemo: true,
    allowPrivateHttp: extraConfig.allowPrivateHttp ?? false,
    allowCarrierPurchases: extraConfig.allowCarrierPurchases ?? false,
    publicBaseUrl: "http://127.0.0.1:8787",
    masterKey: Buffer.alloc(32, 5).toString("base64"),
  });

  const registry = new TelephonyRegistry({ env: {}, providers: [twilio] });
  const runtime = await OmallaRuntime.open(config, {
    offlineProviders: true,
    telephonyRegistry: registry,
  });
  const app = await buildApp(runtime);

  const tenantA = runtime.db.col("tenants").list()[0]!;
  const keyA = await runtime.issueApiKey(tenantA.id, "tenant-a-owner", "owner");

  const now = nowIso();
  const tenantBId = newId("ten");
  runtime.db.col("tenants").insert({
    id: tenantBId,
    name: "Rival Corp (Tenant B)",
    region: "US",
    createdAt: now,
    settings: {
      recordingEnabled: false,
      outboundEnabled: true,
      outboundAllowlist: [],
      dncList: [],
      dailyOutboundCap: 25,
      retentionDays: 30,
      timezone: "UTC",
    },
  });
  const keyB = await runtime.issueApiKey(tenantBId, "tenant-b-owner", "owner");

  return {
    dir,
    runtime,
    app,
    tenantAId: tenantA.id,
    tenantBId,
    tokenA: keyA.token,
    tokenB: keyB.token,
    getCarrierCallCount: () => carrierCallCount,
    getCarrierSmsCount: () => carrierSmsCount,
    cleanup: async () => {
      await app.close();
      await runtime.close();
      await rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
    },
  };
}

test("SQLite WAL mode is active by default and migrates legacy omalla.db.json once", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "omalla-wal-mig-"));
  try {
    const legacyJsonPath = path.join(dir, "omalla.db.json");
    const legacyTenantId = "ten_legacy_1";
    await writeFile(
      legacyJsonPath,
      JSON.stringify({
        schemaVersion: 1,
        tenants: [
          {
            id: legacyTenantId,
            name: "Migrated Clinic",
            region: "SA",
            createdAt: nowIso(),
            settings: {
              recordingEnabled: false,
              outboundEnabled: true,
              outboundAllowlist: [],
              dailyOutboundCap: 10,
              retentionDays: 30,
              timezone: "Asia/Riyadh",
            },
          },
        ],
        contacts: [
          {
            id: "con_legacy_1",
            tenantId: legacyTenantId,
            name: "أحمد",
            tags: ["vip"],
            attributes: {},
            createdAt: nowIso(),
            updatedAt: nowIso(),
          },
        ],
      }),
      "utf8",
    );

    const db = await Database.open({
      filePath: path.join(dir, "omalla.db"),
      legacyJsonPath,
    });
    assert.equal(db.journalMode.toLowerCase(), "wal");
    assert.equal(db.col("tenants").get(legacyTenantId)?.name, "Migrated Clinic");
    assert.equal(db.col("contacts").get("con_legacy_1")?.name, "أحمد");
    assert.equal(existsSync(`${legacyJsonPath}.migrated`), true);
    await db.close();

    // Reopen from SQLite WAL directly
    const reopened = await Database.open({ filePath: path.join(dir, "omalla.db") });
    assert.equal(reopened.col("contacts").get("con_legacy_1")?.name, "أحمد");
    await reopened.close();
  } finally {
    await rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
  }
});

test("OM-T1: blocks all 5 cross-tenant isolation attack vectors across KBs, tools, tasks, post-call & webhooks", async () => {
  const ctx = await createTwoTenantFixture();
  try {
    const authA = { authorization: `Bearer ${ctx.tokenA}` };
    const authB = { authorization: `Bearer ${ctx.tokenB}` };

    // Seed secret KB, task, and webhook workflow in Tenant A
    const kbRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/knowledge-bases",
      headers: authA,
      payload: { name: "Tenant A Secret Vault" },
    });
    assert.equal(kbRes.statusCode, 201);
    const kbA = kbRes.json<{ id: string }>();

    await ctx.app.inject({
      method: "POST",
      url: `/v1/knowledge-bases/${kbA.id}/documents`,
      headers: authA,
      payload: { title: "Vault Pin", text: "TOPSECRET_VAULT_CODE_9988" },
    });

    const wfRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/workflows",
      headers: authA,
      payload: {
        name: "Tenant A PostCall Secret",
        status: "active",
        trigger: { type: "webhook", config: { path: "shared-hook-name" } },
        nodes: [
          { id: "trigger", type: "trigger", name: "Trigger", config: {} },
          { id: "task", type: "local.create_task", name: "Task", config: { title: "A-side-effect" } },
          { id: "end", type: "end", name: "End", config: {} },
        ],
        edges: [
          { from: "trigger", to: "task" },
          { from: "task", to: "end" },
        ],
      },
    });
    assert.equal(wfRes.statusCode, 201);
    const wfA = wfRes.json<{ id: string }>();

    const taskRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/tasks",
      headers: authA,
      payload: { title: "Tenant A Confidential Task" },
    });
    assert.equal(taskRes.statusCode, 201);
    const taskA = taskRes.json<{ id: string }>();

    // Vector 1: Tenant B attempts to attach Tenant A's knowledgeBaseIds to a new agent -> 404
    const badAgentKb = await ctx.app.inject({
      method: "POST",
      url: "/v1/agents",
      headers: authB,
      payload: {
        name: "Exfil Agent",
        config: { knowledgeBaseIds: [kbA.id] },
      },
    });
    assert.equal(badAgentKb.statusCode, 404);

    // Vector 2: Tenant B attempts to create a `query` tool pointing to Tenant A's KB -> 404,
    // and even if directly invoked in ToolRuntime, returns error without leaking data.
    const badQueryTool = await ctx.app.inject({
      method: "POST",
      url: "/v1/tools",
      headers: authB,
      payload: {
        type: "query",
        name: "steal_kb",
        description: "Attempt cross-tenant KB query",
        parameters: { type: "object", properties: { query: { type: "string" } } },
        knowledgeBaseId: kbA.id,
      },
    });
    assert.equal(badQueryTool.statusCode, 404);

    // Direct defense-in-depth check on ToolRuntime.execute if DB had a mismatched KB reference
    const directToolId = newId("tool");
    ctx.runtime.db.col("tools").insert({
      id: directToolId,
      tenantId: ctx.tenantBId,
      type: "query",
      name: "forged_query",
      description: "Forged",
      parameters: { type: "object", properties: {} },
      knowledgeBaseId: kbA.id,
      createdAt: nowIso(),
      updatedAt: nowIso(),
    });
    const directRes = await ctx.runtime.tools.execute({
      toolId: directToolId,
      name: "forged_query",
      args: { query: "TOPSECRET_VAULT_CODE_9988" },
      context: {
        callId: "c_b",
        tenantId: ctx.tenantBId,
        agentId: "a_b",
        agentName: "B",
        direction: "inbound",
        callerNumber: "+15550009999",
        variables: {},
        trusted: { tenantId: ctx.tenantBId, callId: "c_b", callerNumberVerified: false },
      },
    });
    assert.equal(directRes.ok, false);
    assert.doesNotMatch(JSON.stringify(directRes), /TOPSECRET_VAULT_CODE_9988/);

    // Vector 3: Tenant B attempts to attach Tenant A's postCallWorkflowId -> 404,
    // and defense-in-depth afterCall refuses cross-tenant workflow execution.
    const badPostCall = await ctx.app.inject({
      method: "POST",
      url: "/v1/agents",
      headers: authB,
      payload: {
        name: "Hijack Workflow Agent",
        config: { postCallWorkflowId: wfA.id },
      },
    });
    assert.equal(badPostCall.statusCode, 404);

    // Vector 4: Tenant B workflow `local.update_task` attempts to overwrite Tenant A's task -> fails!
    const wfOverwriteRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/workflows",
      headers: authB,
      payload: {
        name: "Tamper Task Flow",
        status: "active",
        trigger: { type: "manual", config: {} },
        nodes: [
          { id: "trigger", type: "trigger", name: "Start", config: {} },
          {
            id: "tamper",
            type: "local.update_task",
            name: "Tamper",
            config: { taskId: taskA.id, title: "PWNED BY TENANT B", status: "done" },
          },
          { id: "end", type: "end", name: "End", config: {} },
        ],
        edges: [
          { from: "trigger", to: "tamper" },
          { from: "tamper", to: "end" },
        ],
      },
    });
    assert.equal(wfOverwriteRes.statusCode, 201);
    const wfB = wfOverwriteRes.json<{ id: string }>();

    const tamperRun = await ctx.app.inject({
      method: "POST",
      url: `/v1/workflows/${wfB.id}/run`,
      headers: authB,
      payload: {},
    });
    assert.equal(tamperRun.json<{ status: string }>().status, "failed");
    assert.equal(ctx.runtime.db.col("tasks").get(taskA.id)?.title, "Tenant A Confidential Task");

    // Vector 5: Tenant B posts to `/v1/hooks/shared-hook-name` -> MUST NOT fire Tenant A's workflow!
    const crossHook = await ctx.app.inject({
      method: "POST",
      url: "/v1/hooks/shared-hook-name",
      headers: authB,
      payload: { hello: "world" },
    });
    assert.equal(crossHook.statusCode, 404);
    const aTasks = ctx.runtime.db
      .col("tasks")
      .list((t) => t.tenantId === ctx.tenantAId && t.title === "A-side-effect");
    assert.equal(aTasks.length, 0);
  } finally {
    await ctx.cleanup();
  }
});

test("OM-T2: marks callerNumberVerified false by default and blocks high-risk tools on unverified ANI", async () => {
  const ctx = await createTwoTenantFixture();
  try {
    const authA = { authorization: `Bearer ${ctx.tokenA}` };
    const createTool = await ctx.app.inject({
      method: "POST",
      url: "/v1/tools",
      headers: authA,
      payload: {
        type: "workflow",
        name: "update_account_campaign",
        description: "High-risk account mutation",
        riskLevel: "high",
        requiresVerifiedCaller: true,
        workflowId: ctx.runtime.db.col("workflows").list((w) => w.tenantId === ctx.tenantAId && w.status === "active")[0]!.id,
        parameters: { type: "object", properties: {} },
        // Attempt to spoof callerNumberVerified via static trustedFields config:
        trustedFields: { callerNumberVerified: true },
      },
    });
    assert.equal(createTool.statusCode, 201);
    const highRiskTool = createTool.json<{ id: string }>();

    // Default synthetic / inbound call has callerNumberVerified: false -> MUST BLOCK!
    const denied = await ctx.app.inject({
      method: "POST",
      url: `/v1/tools/${highRiskTool.id}/test`,
      headers: authA,
      payload: { args: {} },
    });
    assert.equal(denied.statusCode, 200);
    assert.equal(denied.json<{ ok: boolean }>().ok, false);
    assert.match(denied.json<{ error: string }>().error, /OM-T2/);

    // With attested trunk verification -> ALLOWED
    const allowed = await ctx.app.inject({
      method: "POST",
      url: `/v1/tools/${highRiskTool.id}/test`,
      headers: authA,
      payload: { args: {}, callerNumberVerified: true },
    });
    assert.equal(allowed.statusCode, 200);
    assert.equal(allowed.json<{ ok: boolean }>().ok, true);
  } finally {
    await ctx.cleanup();
  }
});

test("OM-T4: connect-time pinned-DNS SSRF guard blocks private/loopback/IMDS/CGNAT/IPv4-mapped IPv6 & DNS rebinding", async () => {
  const blockedUrls = [
    "http://127.0.0.1:8080/admin",
    "http://[::1]:8080/admin",
    "http://10.0.0.5/internal",
    "http://172.16.12.4/internal",
    "http://192.168.1.1/router",
    "http://169.254.169.254/latest/meta-data/",
    "http://[fe80::1]/link",
    "http://100.64.10.20/cgnat",
    "http://[::ffff:127.0.0.1]:8080/mapped-loopback",
    "http://[::ffff:169.254.169.254]/mapped-imds",
  ];

  const guarded = createSsrfGuardedFetch({
    allowPrivate: false,
    baseFetch: async () => new Response("should-never-reach", { status: 200 }),
  });

  for (const url of blockedUrls) {
    await assert.rejects(() => guarded(url), /SSRF guard blocked/, `failed to block ${url}`);
  }

  // Simulated DNS rebinding: hostname resolves to loopback or mixed [public, IMDS]
  const rebindGuarded = createSsrfGuardedFetch({
    allowPrivate: false,
    lookup: async (host) => {
      if (host === "rebind.attacker.example") {
        return [
          { address: "93.184.216.34", family: 4 },
          { address: "169.254.169.254", family: 4 },
        ];
      }
      return [{ address: "93.184.216.34", family: 4 }];
    },
    baseFetch: async (url) => {
      if (String(url).includes("/redirect-to-imds")) {
        return new Response(null, {
          status: 302,
          headers: { location: "http://169.254.169.254/latest/meta-data/" },
        });
      }
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    },
  });

  await assert.rejects(() => rebindGuarded("https://rebind.attacker.example/hook"), /restricted IP 169\.254\.169\.254/);
  await assert.rejects(() => rebindGuarded("https://safe.example/redirect-to-imds"), /SSRF guard blocked/);
  const okResp = await rebindGuarded("https://safe.example/ok");
  assert.equal(okResp.status, 200);
});

test("OM-T3 & OM-T5: raw-byte Standard Webhooks + durable SQLite replay cache + JCS Idempotency-Key", async () => {
  const ctx = await createTwoTenantFixture();
  try {
    const authA = { authorization: `Bearer ${ctx.tokenA}` };

    const wfRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/workflows",
      headers: authA,
      payload: {
        name: "Signed Hook Flow",
        status: "active",
        trigger: { type: "webhook", config: { path: "orders" } },
      },
    });
    assert.equal(wfRes.statusCode, 201);

    const secretRaw = Buffer.from("0123456789abcdef0123456789abcdef", "utf8");
    const whSecret = `whsec_${secretRaw.toString("base64")}`;
    await ctx.app.inject({
      method: "PUT",
      url: "/v1/credentials/WEBHOOK_SECRET",
      headers: authA,
      payload: { value: whSecret, provider: "standard-webhooks" },
    });

    // Irregular whitespace raw payload: proves signature is verified over RAW BYTES, not JSON.stringify!
    const rawPayload = '{  "orderId" :   "ORD-77" ,  "count" : 2  }';
    const nowSec = Math.floor(Date.now() / 1000);
    const msgId = "msg_unique_001";
    const signedBytes = Buffer.concat([
      Buffer.from(`${msgId}.${nowSec}.`, "utf8"),
      Buffer.from(rawPayload, "utf8"),
    ]);
    const sigB64 = createHmac("sha256", secretRaw).update(signedBytes).digest("base64");

    const firstHook = await ctx.app.inject({
      method: "POST",
      url: "/v1/hooks/orders",
      headers: {
        ...authA,
        "content-type": "application/json",
        "webhook-id": msgId,
        "webhook-timestamp": String(nowSec),
        "webhook-signature": `v1,${sigB64}`,
      },
      payload: rawPayload,
    });
    assert.equal(firstHook.statusCode, 202);

    // Exact replay of same webhook-id MUST be rejected with 409!
    const replayHook = await ctx.app.inject({
      method: "POST",
      url: "/v1/hooks/orders",
      headers: {
        ...authA,
        "content-type": "application/json",
        "webhook-id": msgId,
        "webhook-timestamp": String(nowSec),
        "webhook-signature": `v1,${sigB64}`,
      },
      payload: rawPayload,
    });
    assert.equal(replayHook.statusCode, 409);

    // Skewed timestamp (>300s old) MUST be rejected with 401!
    const oldSec = nowSec - 600;
    const oldSig = createHmac("sha256", secretRaw)
      .update(Buffer.concat([Buffer.from(`msg_old.${oldSec}.`, "utf8"), Buffer.from(rawPayload, "utf8")]))
      .digest("base64");
    const staleHook = await ctx.app.inject({
      method: "POST",
      url: "/v1/hooks/orders",
      headers: {
        ...authA,
        "content-type": "application/json",
        "webhook-id": "msg_old",
        "webhook-timestamp": String(oldSec),
        "webhook-signature": `v1,${oldSig}`,
      },
      payload: rawPayload,
    });
    assert.equal(staleHook.statusCode, 401);

    // OM-T5: Idempotency-Key deduplicates SMS & rejects float payloads or mismatched args!
    const sms1 = await ctx.app.inject({
      method: "POST",
      url: "/v1/sms",
      headers: { ...authA, "content-type": "application/json", "idempotency-key": "idem_sms_alpha" },
      payload: '{"to":"+15550004444","body":"Hello","consent":true}',
    });
    assert.equal(sms1.statusCode, 201);
    const smsId1 = sms1.json<{ id: string }>().id;

    // Reordered keys, identical JCS digest -> replayed without creating a 2nd SMS!
    const sms2 = await ctx.app.inject({
      method: "POST",
      url: "/v1/sms",
      headers: { ...authA, "content-type": "application/json", "idempotency-key": "idem_sms_alpha" },
      payload: '{"consent":true,"body":"Hello","to":"+15550004444"}',
    });
    assert.equal(sms2.statusCode, 201);
    assert.equal(sms2.headers["x-idempotency-replayed"], "true");
    assert.equal(sms2.json<{ id: string }>().id, smsId1);

    // Same Idempotency-Key with different body -> 409 Conflict!
    const smsConflict = await ctx.app.inject({
      method: "POST",
      url: "/v1/sms",
      headers: { ...authA, "content-type": "application/json", "idempotency-key": "idem_sms_alpha" },
      payload: '{"to":"+15550004444","body":"Different!","consent":true}',
    });
    assert.equal(smsConflict.statusCode, 409);

    // Outbound call with float in variables + Idempotency-Key -> 400 validation!
    const agentId = ctx.runtime.db.col("agents").list((a) => a.tenantId === ctx.tenantAId)[0]!.id;
    const floatCall = await ctx.app.inject({
      method: "POST",
      url: "/v1/calls/outbound",
      headers: { ...authA, "idempotency-key": "idem_float_reject", "content-type": "application/json" },
      payload: JSON.stringify({
        to: "+15550007777",
        agentId,
        consent: true,
        variables: { score: 1.75 },
      }),
    });
    assert.equal(floatCall.statusCode, 400);
  } finally {
    await ctx.cleanup();
  }
});

test("OM-T6: enforces DNC, callingWindow/quiet-hours & quotas on BOTH simulated and carrier outbound calls", async () => {
  const ctx = await createTwoTenantFixture();
  try {
    const authA = { authorization: `Bearer ${ctx.tokenA}` };
    const agent = ctx.runtime.db.col("agents").list((a) => a.tenantId === ctx.tenantAId)[0]!;
    const number = ctx.runtime.db.col("phoneNumbers").list((n) => n.tenantId === ctx.tenantAId)[0]!;
    ctx.runtime.db.col("phoneNumbers").update(number.id, {
      provider: "twilio",
      simulated: false,
      providerNumberId: "PN_TWILIO_1",
    });

    // 1. Add +15550006666 to DNC list and set an impossible calling window (00:00-00:01 on an excluded weekday)
    await ctx.app.inject({
      method: "PATCH",
      url: "/v1/tenant/settings",
      headers: authA,
      payload: {
        dncList: ["+15550006666"],
      },
    });

    const simDnc = await ctx.app.inject({
      method: "POST",
      url: "/v1/calls/outbound",
      headers: authA,
      payload: { to: "+15550006666", agentId: agent.id, consent: true, mode: "simulated" },
    });
    assert.equal(simDnc.statusCode, 403);

    const carrierDnc = await ctx.app.inject({
      method: "POST",
      url: "/v1/calls/outbound",
      headers: authA,
      payload: { to: "+15550006666", agentId: agent.id, consent: true, mode: "carrier", provider: "twilio" },
    });
    assert.equal(carrierDnc.statusCode, 403);
    assert.equal(ctx.getCarrierCallCount(), 0);

    // 2. Quiet hours / callingWindow enforcement on carrier outbound!
    const currentUtcDay = new Date().getUTCDay();
    const otherDay = (currentUtcDay + 3) % 7;
    await ctx.app.inject({
      method: "PATCH",
      url: "/v1/tenant/settings",
      headers: authA,
      payload: {
        timezone: "UTC",
        callingWindow: { start: "09:00", end: "10:00", days: [otherDay] },
      },
    });

    const simQuiet = await ctx.app.inject({
      method: "POST",
      url: "/v1/calls/outbound",
      headers: authA,
      payload: { to: "+15550008888", agentId: agent.id, consent: true, mode: "simulated" },
    });
    assert.equal(simQuiet.statusCode, 403);

    const carrierQuiet = await ctx.app.inject({
      method: "POST",
      url: "/v1/calls/outbound",
      headers: authA,
      payload: { to: "+15550008888", agentId: agent.id, consent: true, mode: "carrier", provider: "twilio" },
    });
    assert.equal(carrierQuiet.statusCode, 403);
    assert.equal(ctx.getCarrierCallCount(), 0);

    // 3. Minute quota exhaustion blocks both simulated and carrier calls
    await ctx.app.inject({
      method: "PATCH",
      url: "/v1/tenant/settings",
      headers: authA,
      payload: {
        callingWindow: { start: "00:00", end: "23:59", days: [0, 1, 2, 3, 4, 5, 6] },
        dailyMinuteQuota: 0,
      },
    });
    const quotaBlocked = await ctx.app.inject({
      method: "POST",
      url: "/v1/calls/outbound",
      headers: authA,
      payload: { to: "+15550008888", agentId: agent.id, consent: true, mode: "carrier", provider: "twilio" },
    });
    assert.equal(quotaBlocked.statusCode, 403);
  } finally {
    await ctx.cleanup();
  }
});

test("Arabic intelligence, speech adapters, silenceTimeoutSec, endCallPhrases, versioning/rollback & TS SDK", async () => {
  // 1. Arabic text + natural time parsing
  assert.equal(normalizeArabicText("مَعَ السَّلَامَةِ ١٢٣"), "مع السلامه 123");
  const refNow = new Date("2026-11-27T10:00:00.000Z");
  const tomorrowAr = parseSpokenDateTime("غداً الساعة 5 مساءً", refNow, "UTC");
  assert.ok(tomorrowAr);
  assert.match(tomorrowAr.iso, /^2026-11-28T17:00:00/);

  const twoHoursAr = parseSpokenDateTime("بعد ساعتين", refNow, "UTC");
  assert.ok(twoHoursAr);
  assert.equal(twoHoursAr.iso, "2026-11-27T12:00:00.000Z");

  const todayFiveAr = parseSpokenDateTime("اليوم الساعة ٥", refNow, "UTC");
  assert.ok(todayFiveAr);
  assert.match(todayFiveAr.iso, /^2026-11-27T17:00:00/);

  // 2. Pluggable zero-cost local loopback & local HTTP adapters + Principle XXI guard
  const synth = new LoopbackSynthTts();
  const stt = new LoopbackStt();
  const audio = await synth.synthesize("مرحباً بكم في أومالا", { voiceId: "ar-demo", language: "ar-SA" });
  assert.ok(audio.data.length > 1000);
  const loopTranscript = await stt.transcribe(audio.data, { language: "ar-SA" });
  assert.equal(loopTranscript.text, "مرحبا بكم في اومالا");

  const whisper = new WhisperCppStt({
    baseUrl: "http://127.0.0.1:18081",
    fetchImpl: async () =>
      new Response(JSON.stringify({ text: "أهلاً وسهلاً", language: "ar" }), { status: 200 }),
  });
  assert.equal((await whisper.transcribe(audio.data, { language: "ar" })).text, "اهلا وسهلا");

  const piper = new PiperTts({
    baseUrl: "http://127.0.0.1:15000",
    fetchImpl: async () => new Response(Buffer.from(audio.data), { status: 200 }),
  });
  assert.equal((await piper.synthesize("Hello", { voiceId: "en_US" })).mimeType, "audio/wav");

  const wcore = new WispralCoreStt({
    baseUrl: "http://127.0.0.1:19797",
    fetchImpl: async () =>
      new Response(JSON.stringify({ text: "Wispral local bridge", confidence: 0.98 }), { status: 200 }),
  });
  assert.equal((await wcore.transcribe(audio.data)).text, "Wispral local bridge");

  // Principle XXI: local primary provider MUST refuse paid cloud fallback!
  const ctx = await createTwoTenantFixture();
  try {
    const baseAgent = ctx.runtime.db.col("agents").list()[0]!;
    await assert.rejects(
      () =>
        resolveProviders(
          {
            ...baseAgent,
            config: {
              ...baseAgent.config,
              transcriber: {
                provider: "whisper.cpp",
                fallbacks: [{ provider: "openai", credentialRef: "OPENAI_KEY" }],
              },
            },
          },
          { logger: ctx.runtime.logger, resolveCredential: async () => "sk-test" },
        ),
      /Principle XXI/,
    );

    // 3. Test TypeScript SDK + Versioning + Diff + Rollback + Arabic endCallPhrases + silenceTimeoutSec
    const address = await ctx.app.listen({ host: "127.0.0.1", port: 0 });
    const sdk = new OmallaClient({ baseUrl: address, apiKey: ctx.tokenA });

    const created = await sdk.agents.create({
      name: "Arabic Concierge",
      config: {
        firstMessage: "مرحباً، كيف أساعدك؟",
        language: "ar-SA",
        voice: { provider: "mock", voiceId: "demo" },
        transcriber: { provider: "mock", language: "ar-SA" },
        silenceTimeoutSec: 1,
        endCallPhrases: ["مع السلامة", "انهي المكالمة"],
      },
    });
    assert.equal(created.version, 1);

    const patched = await sdk.agents.update(created.id, {
      status: "published",
      config: { firstMessage: "أهلاً بك، تفضل!" },
    });
    assert.equal(patched.version, 2);

    const evalRes = await sdk.agents.test(created.id, {
      callerTurns: ["انهي المكالمة"],
      compareVersion: 1,
    });
    assert.equal(evalRes.passed, true);
    assert.equal(evalRes.endedReason, "customer_ended");
    assert.ok(Array.isArray((evalRes.diff as { changedKeys: string[] }).changedKeys));

    const rolledAgent = await sdk.agents.rollback(created.id, 1, "restore original Arabic greeting");
    assert.equal(rolledAgent.version, 3);
    assert.equal(rolledAgent.config.firstMessage, "مرحباً، كيف أساعدك؟");

    // Workflow versioning & rollback via SDK
    const wf = await sdk.workflows.create({ name: "Versioned Flow", status: "draft" });
    assert.equal(wf.version, 1);
    const wf2 = await sdk.workflows.update(wf.id, { status: "active", description: "v2 active" });
    assert.equal(wf2.version, 2);
    const wfTest = await sdk.workflows.test(wf.id, { payload: { ping: 1 }, compareVersion: 1 });
    assert.equal((wfTest.run as { status: string }).status, "succeeded");
    const wfRolled = await sdk.workflows.rollback(wf.id, 1, "revert to draft");
    assert.equal(wfRolled.version, 3);
    assert.equal(wfRolled.status, "draft");

    // Silence timeout ends idle live call automatically
    const pubAgent = await sdk.agents.publish(rolledAgent.id);
    const idleCall = await sdk.calls.outbound(
      { to: "+15550003333", agentId: pubAgent.id, consent: true },
      { idempotencyKey: "idem_sdk_silence_1" },
    );
    await new Promise((resolve) => setTimeout(resolve, 1250));
    const fetchedIdle = await sdk.calls.get(idleCall.id);
    assert.equal(fetchedIdle.status, "ended");
    assert.equal(fetchedIdle.endedReason, "silence_timeout");

    // SDK helpers smoke check
    assert.equal(jcsSha256({ b: 2, a: 1 }), jcsSha256({ a: 1, b: 2 }));
    assert.equal(parseStreamFrames(['data: {"type":"call.ended","callId":"c1","at":"now","data":{}}']).length, 1);
    const tsNow = String(Math.floor(Date.now() / 1000));
    const sigHex = createHmac("sha256", "sec").update(`${tsNow}.{}`).digest("hex");
    // Timeless x-omalla-signature MUST fail (OM-T3)
    assert.equal(
      verifyWebhookSignature({ rawBody: "{}", headers: { "x-omalla-signature": `sha256=${sigHex}` }, secret: "sec" }).valid,
      false,
    );
    const verifiedOmalla = verifyWebhookSignature({
      rawBody: "{}",
      headers: { "x-omalla-signature": `sha256=${sigHex}`, "x-omalla-timestamp": tsNow },
      secret: "sec",
    });
    assert.equal(verifiedOmalla.valid, true);
    assert.ok(verifiedOmalla.eventKey?.startsWith(`omalla:${tsNow}:`));
  } finally {
    await ctx.cleanup();
  }
});

test("OM-T1 & OM-T2 remediations: inbound number normalization, env exfiltration guard, step-up variables strip & dryRun role gates", async () => {
  const ctx = await createTwoTenantFixture();
  const prevMaster = process.env.OMALLA_MASTER_KEY;
  const prevOpenAi = process.env.OPENAI_API_KEY;
  process.env.OMALLA_MASTER_KEY = "SUPER_SECRET_HOST_MASTER_KEY";
  process.env.OPENAI_API_KEY = "sk-host-shared-test";
  try {
    const authA = { authorization: `Bearer ${ctx.tokenA}` };
    const authB = { authorization: `Bearer ${ctx.tokenB}` };

    // 1. OM-T1: Tenant B dialing Tenant A's +15550001234 in non-+ formats gets 404
    for (const rawDial of ["5550001234", "0015550001234", "(555) 000-1234"]) {
      const dialRes = await ctx.app.inject({
        method: "POST",
        url: "/v1/calls",
        headers: authB,
        payload: { to: rawDial, from: "+15550009999" },
      });
      assert.equal(dialRes.statusCode, 404, `expected 404 for ${rawDial}`);
    }
    await assert.rejects(
      () =>
        ctx.runtime.startInbound({
          tenantId: ctx.tenantBId,
          to: "+15550001234",
          from: "+15550009999",
        }),
      /no phone number configured/,
    );

    // 2. OM-T1: CredentialService.get refuses OMALLA_MASTER_KEY and disables env fallback in multi-tenant mode
    assert.equal(await ctx.runtime.credentials.get(ctx.tenantAId, "OMALLA_MASTER_KEY"), undefined);
    assert.equal(await ctx.runtime.credentials.get(ctx.tenantAId, "TWILIO_AUTH_TOKEN"), undefined);
    assert.equal(await ctx.runtime.credentials.get(ctx.tenantAId, "OMALLA_SIP_GATEWAY_TOKEN"), undefined);
    // Multi-tenant (2 tenants in fixture) without allowSharedEnvCredentials -> undefined even for OPENAI_API_KEY
    assert.equal(await ctx.runtime.credentials.get(ctx.tenantAId, "OPENAI_API_KEY"), undefined);

    // 3. OM-T2: camelCase high-risk tool blocked on unverified ANI & untrusted variables.callerVerifiedSecondary stripped
    let externalMutated = 0;
    const wireToolRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/tools",
      headers: authA,
      payload: {
        type: "internal",
        internalAction: "create_task",
        name: "wireTransferPayout",
        description: "CamelCase high-risk wire transfer",
        parameters: { type: "object", properties: { title: { type: "string" } } },
      },
    });
    assert.equal(wireToolRes.statusCode, 201);
    const wireTool = wireToolRes.json<{ id: string }>();

    // Spoofing callerVerifiedSecondary in context.variables MUST be ignored!
    const spoofedExec = await ctx.runtime.tools.execute({
      toolId: wireTool.id,
      name: "wireTransferPayout",
      args: { title: "Spoofed wire" },
      context: {
        callId: "c_spoof",
        tenantId: ctx.tenantAId,
        agentId: "a_spoof",
        agentName: "Spoof",
        direction: "inbound",
        callerNumber: "+15550009999",
        variables: { callerVerifiedSecondary: true, callerNumberVerified: true },
        trusted: { tenantId: ctx.tenantAId, callId: "c_spoof", callerNumberVerified: false },
      },
    });
    assert.equal(spoofedExec.ok, false);
    assert.match(spoofedExec.error ?? "", /OM-T2/);

    // Inbound call strips untrusted verification keys from call.variables
    const inboundHandle = await ctx.runtime.startInbound({
      tenantId: ctx.tenantAId,
      to: "+15550001234",
      from: "+15550009999",
      variables: {
        customerTier: "gold",
        callerVerifiedSecondary: true,
        callerNumberVerified: true,
        stirShakenAttestation: "A",
      },
    });
    assert.equal(inboundHandle.snapshot().variables.customerTier, "gold");
    assert.equal(inboundHandle.snapshot().variables.callerVerifiedSecondary, undefined);
    assert.equal(inboundHandle.snapshot().variables.callerNumberVerified, undefined);
    assert.equal(inboundHandle.snapshot().variables.stirShakenAttestation, undefined);
    await ctx.runtime.hangup(inboundHandle.call.id);

    // /v1/tools/:id/test dryRun: true does NOT mutate tasks, and dryRun: false requires admin role
    const operatorKey = await ctx.runtime.issueApiKey(ctx.tenantAId, "op-only", "operator");
    const authOp = { authorization: `Bearer ${operatorKey.token}` };
    const lowRiskToolRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/tools",
      headers: authA,
      payload: {
        type: "internal",
        internalAction: "create_task",
        name: "log_callback_note",
        description: "Low-risk task creation",
        parameters: { type: "object", properties: { title: { type: "string" } } },
      },
    });
    const lowTool = lowRiskToolRes.json<{ id: string }>();
    const tasksBefore = ctx.runtime.store.listTasks(ctx.tenantAId).length;

    const dryTest = await ctx.app.inject({
      method: "POST",
      url: `/v1/tools/${lowTool.id}/test`,
      headers: authOp,
      payload: { args: { title: "Dry run task" }, dryRun: true },
    });
    assert.equal(dryTest.statusCode, 200);
    assert.equal(dryTest.json<{ ok: boolean; result: { dryRun: boolean } }>().result.dryRun, true);
    assert.equal(ctx.runtime.store.listTasks(ctx.tenantAId).length, tasksBefore);

    // Operator attempting dryRun: false or callerNumberVerified: true -> 403 Forbidden
    const opLiveDenied = await ctx.app.inject({
      method: "POST",
      url: `/v1/tools/${lowTool.id}/test`,
      headers: authOp,
      payload: { args: { title: "Live task" }, dryRun: false },
    });
    assert.equal(opLiveDenied.statusCode, 403);

    const opVerifiedDenied = await ctx.app.inject({
      method: "POST",
      url: `/v1/tools/${wireTool.id}/test`,
      headers: authOp,
      payload: { args: { title: "Verified wire" }, dryRun: true, callerNumberVerified: true },
    });
    assert.equal(opVerifiedDenied.statusCode, 403);
    assert.equal(externalMutated, 0);
  } finally {
    if (prevMaster === undefined) delete process.env.OMALLA_MASTER_KEY;
    else process.env.OMALLA_MASTER_KEY = prevMaster;
    if (prevOpenAi === undefined) delete process.env.OPENAI_API_KEY;
    else process.env.OPENAI_API_KEY = prevOpenAi;
    await ctx.cleanup();
  }
});

test("OM-T4, OM-T6 & JCS live socket remediations: pinnedNodeRequest loopback, >2MiB cap, redirect header strip, SMS quiet-hours & surrogate/arg-digest guards", async () => {
  // 1. Real 127.0.0.1 HTTP servers exercising pinnedNodeRequest WITHOUT baseFetch
  let leakedAuthOnTarget = "";
  const targetServer = http.createServer((req, res) => {
    leakedAuthOnTarget = String(req.headers.authorization ?? "");
    if (req.url === "/oversize") {
      res.writeHead(200, { "content-type": "application/octet-stream" });
      const chunk = Buffer.alloc(64 * 1024, 0x41);
      for (let i = 0; i < 40; i += 1) {
        res.write(chunk); // 2.5 MiB > 2 MiB limit
      }
      res.end();
      return;
    }
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true }));
  });
  await new Promise<void>((resolve) => targetServer.listen(0, "127.0.0.1", resolve));
  const targetPort = (targetServer.address() as { port: number }).port;

  const redirectServer = http.createServer((_req, res) => {
    res.writeHead(302, { location: `http://127.0.0.1:${targetPort}/landed` });
    res.end();
  });
  await new Promise<void>((resolve) => redirectServer.listen(0, "127.0.0.1", resolve));
  const redirectPort = (redirectServer.address() as { port: number }).port;

  const ctx = await createTwoTenantFixture({ allowPrivateHttp: false });
  try {
    // Without allowPrivate, live loopback HTTP is blocked even when host is in allowedHosts!
    const strictLiveFetch = createSsrfGuardedFetch({
      allowPrivate: false,
      allowedHosts: ["127.0.0.1", "localhost"],
    });
    await assert.rejects(
      () => strictLiveFetch(`http://127.0.0.1:${targetPort}/ok`),
      /SSRF guard blocked/,
    );
    await assert.rejects(
      () => strictLiveFetch(`http://localhost.:${targetPort}/ok`),
      /SSRF guard blocked/,
    );
    await assert.rejects(
      () => strictLiveFetch("http://[64:ff9b:1::1]/nat64"),
      /SSRF guard blocked/,
    );

    // With allowPrivate: true, pinnedNodeRequest connects over real TCP, strips cross-origin auth, and aborts >2MiB
    const privateLiveFetch = createSsrfGuardedFetch({ allowPrivate: true });
    const crossRedirectResp = await privateLiveFetch(`http://127.0.0.1:${redirectPort}/bounce`, {
      headers: {
        authorization: "Bearer SECRET_SHOULD_BE_STRIPPED",
        cookie: "sid=secret",
      },
    });
    assert.equal(crossRedirectResp.status, 200);
    assert.equal(leakedAuthOnTarget, "");

    await assert.rejects(
      () => privateLiveFetch(`http://127.0.0.1:${targetPort}/oversize`),
      /exceeded 2 MiB limit/,
    );

    // Provider SSRF guard: tenant agent overriding model.baseUrl to 127.0.0.1 is blocked when allowPrivateHttp=false
    const authA = { authorization: `Bearer ${ctx.tokenA}` };
    const ssrfAgentRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/agents",
      headers: authA,
      payload: {
        name: "SSRF Ollama Agent",
        config: {
          model: {
            provider: "ollama",
            model: "llama3",
            baseUrl: `http://127.0.0.1:${targetPort}`,
          },
        },
      },
    });
    const ssrfAgent = ssrfAgentRes.json<{ id: string }>();
    await ctx.app.inject({
      method: "POST",
      url: `/v1/agents/${ssrfAgent.id}/publish`,
      headers: authA,
    });
    const dummyCall = ctx.runtime.db.col("calls").insert({
      id: newId("call"),
      tenantId: ctx.tenantAId,
      direction: "inbound",
      status: "in_progress",
      from: "+15550009999",
      to: "+15550001234",
      agentId: ssrfAgent.id,
      startedAt: nowIso(),
      transcript: [],
      messages: [],
      variables: {},
      metadata: {},
      metrics: {
        turnCount: 0,
        turnLatenciesMs: [],
        totalTokensIn: 0,
        totalTokensOut: 0,
        toolCalls: 0,
        interruptions: 0,
      },
      simulation: true,
    });
    const publishedSsrfAgent = ctx.runtime.db.col("agents").get(ssrfAgent.id)!;
    const { engine } = await ctx.runtime.buildConversation(dummyCall, publishedSsrfAgent);
    await engine.start();
    await engine.handleCallerUtterance("hello");
    // Ollama Llm failure is caught by ConversationEngine or surfaces SSRF error without reaching targetServer
    assert.equal(dummyCall.metrics.totalTokensOut, 0);

    // Local binary identifier sanitization rejects leading-dash flags
    await assert.rejects(() => new PiperTts().synthesize("hi", { voiceId: "--output-raw" }), /invalid voiceId/);
    await assert.rejects(
      () => new WhisperCppStt().transcribe(new Uint8Array(4), { language: "-f" }),
      /invalid language/,
    );

    // JCS lone surrogate rejection & x-omalla-args-digest mismatch rejection
    assert.throws(() => canonicalizeJcs({ bad: "\uD800" }), /lone UTF-16/);
    const badDigestSms = await ctx.app.inject({
      method: "POST",
      url: "/v1/sms",
      headers: {
        ...authA,
        "idempotency-key": "idem_bad_digest_1",
        "x-omalla-args-digest": "0".repeat(64),
      },
      payload: { to: "+15550008888", body: "Digest test", consent: true },
    });
    assert.equal(badDigestSms.statusCode, 400);
    assert.match(badDigestSms.json<{ error: { message: string } }>().error.message, /x-omalla-args-digest/);

    // OM-T6: quiet hours block BOTH POST /v1/sms and workflow sms.send!
    const currentUtcDay = new Date().getUTCDay();
    const otherDay = (currentUtcDay + 3) % 7;
    await ctx.app.inject({
      method: "PATCH",
      url: "/v1/tenant/settings",
      headers: authA,
      payload: {
        timezone: "UTC",
        callingWindow: { start: "09:00", end: "17:00", days: [otherDay] },
      },
    });
    const quietSms = await ctx.app.inject({
      method: "POST",
      url: "/v1/sms",
      headers: authA,
      payload: { to: "+15550008888", body: "Quiet hour SMS", consent: true },
    });
    assert.equal(quietSms.statusCode, 403);

    const smsWfRes = await ctx.app.inject({
      method: "POST",
      url: "/v1/workflows",
      headers: authA,
      payload: {
        name: "Quiet Hour SMS Workflow",
        status: "active",
        trigger: { type: "manual", config: {} },
        nodes: [
          { id: "trigger", type: "trigger", name: "Start", config: {} },
          {
            id: "sms",
            type: "sms.send",
            name: "Send SMS",
            config: { to: "+15550008888", body: "Workflow SMS", consent: true },
          },
          { id: "end", type: "end", name: "End", config: {} },
        ],
        edges: [
          { from: "trigger", to: "sms" },
          { from: "sms", to: "end" },
        ],
      },
    });
    const smsWf = smsWfRes.json<{ id: string }>();
    const smsWfRun = await ctx.app.inject({
      method: "POST",
      url: `/v1/workflows/${smsWf.id}/run`,
      headers: authA,
      payload: {},
    });
    assert.equal(smsWfRun.json<{ status: string }>().status, "failed");
  } finally {
    await new Promise<void>((resolve) => targetServer.close(() => resolve()));
    await new Promise<void>((resolve) => redirectServer.close(() => resolve()));
    await ctx.cleanup();
  }
});
