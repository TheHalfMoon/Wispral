import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { OmallaRuntime, buildApp, loadConfig } from "@omalla/server";

test("Omalla Studio serves Quiet Signal (#7E22CE / #D8B4FE) tokens, RTL/LTR dir=auto, AudioWorklet, SIP monitor, and 1-click rollback APIs", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "omalla-studio-"));
  const runtime = await OmallaRuntime.open(
    loadConfig({
      dataDir: dir,
      seedDemo: true,
      masterKey: Buffer.alloc(32, 11).toString("base64"),
    }),
    { offlineProviders: true },
  );
  const tenant = runtime.db.col("tenants").list()[0]!;
  const apiKey = (await runtime.issueApiKey(tenant.id, "studio-test", "owner")).token;
  const app = await buildApp(runtime);

  try {
    // 1. HTML shell: dir="auto", RTL/LTR toggle, Theme toggle, Voice Studio & Telephony nav
    const htmlRes = await app.inject({ method: "GET", url: "/" });
    assert.equal(htmlRes.statusCode, 200);
    assert.match(htmlRes.body, /Omalla/);
    assert.match(htmlRes.body, /dir="auto"/);
    assert.match(htmlRes.body, /id="lang-toggle"/);
    assert.match(htmlRes.body, /id="theme-toggle"/);
    assert.match(htmlRes.body, /data-view="studio"/);
    assert.match(htmlRes.body, /Telephony/);

    // 2. Quiet Signal design tokens (#7E22CE light, #D8B4FE dark) + logical RTL properties
    const cssRes = await app.inject({ method: "GET", url: "/styles.css" });
    assert.equal(cssRes.statusCode, 200);
    assert.match(cssRes.body, /#7E22CE/i);
    assert.match(cssRes.body, /#D8B4FE/i);
    assert.match(cssRes.body, /\[data-theme="light"\]/);
    assert.match(cssRes.body, /border-inline-end/);

    // 3. Browser Microphone AudioWorklet processor
    const workletRes = await app.inject({ method: "GET", url: "/audio-worklet.js" });
    assert.equal(workletRes.statusCode, 200);
    assert.match(workletRes.body, /class OmallaPcm16Worklet extends AudioWorkletProcessor/);
    assert.match(workletRes.body, /registerProcessor\("omalla-pcm16-worklet"/);

    // 4. Studio ES module app.js: Arabic/English i18n, WebSocket + WebRTC duplex console, T0..T6 latency, rollback
    const jsRes = await app.inject({ method: "GET", url: "/app.js" });
    assert.equal(jsRes.statusCode, 200);
    assert.ok(jsRes.body.length > 10_000);
    assert.match(jsRes.body, /renderTelephony/);
    assert.match(jsRes.body, /renderStudio/);
    assert.match(jsRes.body, /observed_audio_halt/);
    assert.match(jsRes.body, /stopped_unconfirmed/);
    assert.match(jsRes.body, /\/v1\/realtime\/ws/);
    assert.match(jsRes.body, /\/v1\/realtime\/webrtc\/offer/);
    assert.match(jsRes.body, /استوديو أومالا الصوتي المباشر/);

    // 5. SIP/Telephony Status Monitor endpoint
    const sipRes = await app.inject({
      method: "GET",
      url: "/v1/telephony/sip/status",
      headers: { authorization: `Bearer ${apiKey}` },
    });
    assert.equal(sipRes.statusCode, 200);
    const sipBody = sipRes.json() as {
      defaultBindHost: string;
      srtpSuites: string[];
      omT7Policy: { nonLoopbackRequiresSrtp: boolean; nonLoopbackSdesRequiresSipsTlsOrAttestedTunnel: boolean };
    };
    assert.equal(sipBody.defaultBindHost, "127.0.0.1");
    assert.ok(sipBody.srtpSuites.includes("AES_CM_128_HMAC_SHA1_80"));
    assert.equal(sipBody.omT7Policy.nonLoopbackRequiresSrtp, true);
    assert.equal(sipBody.omT7Policy.nonLoopbackSdesRequiresSipsTlsOrAttestedTunnel, true);

    // 6. Studio Agent version history + 1-click rollback flow
    const agentsRes = await app.inject({
      method: "GET",
      url: "/v1/agents",
      headers: { authorization: `Bearer ${apiKey}` },
    });
    const agent = (agentsRes.json() as Array<{ id: string; version: number; config: { firstMessage: string } }>)[0]!;
    const v1Greeting = agent.config.firstMessage;

    await app.inject({
      method: "PATCH",
      url: `/v1/agents/${agent.id}`,
      headers: { authorization: `Bearer ${apiKey}` },
      payload: { config: { firstMessage: "Temporary experimental v2 greeting" } },
    });
    const pubRes = await app.inject({
      method: "POST",
      url: `/v1/agents/${agent.id}/publish`,
      headers: { authorization: `Bearer ${apiKey}` },
    });
    assert.equal(pubRes.statusCode, 200);
    assert.equal((pubRes.json() as { version: number }).version, 3);

    const rbRes = await app.inject({
      method: "POST",
      url: `/v1/agents/${agent.id}/rollback`,
      headers: { authorization: `Bearer ${apiKey}` },
      payload: { version: 1, note: "Studio 1-click rollback test" },
    });
    assert.equal(rbRes.statusCode, 200);
    const rolled = rbRes.json() as { version: number; config: { firstMessage: string } };
    assert.equal(rolled.version, 4);
    assert.equal(rolled.config.firstMessage, v1Greeting);
  } finally {
    await app.close();
    await runtime.close();
    await rm(dir, { recursive: true, force: true });
  }
});
