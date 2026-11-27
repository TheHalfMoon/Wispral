import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import type { FastifyInstance } from "fastify";
import { OmallaRuntime, buildApp, loadConfig } from "@omalla/server";
import { TelephonyRegistry, TwilioProvider } from "@omalla/telephony";

let dir = "";
let runtime: OmallaRuntime;
let app: FastifyInstance;
let key = "";
let twilio: TwilioProvider;
let tenantId = "";
let agentId = "";
let numberId = "";
let ivrMenuId = "";
let outboundSid = 0;

async function signedRequest(
  pathWithQuery: string,
  form: Record<string, string>,
): Promise<{ statusCode: number; body: string; headers: Record<string, unknown> }> {
  const url = `http://127.0.0.1:8787${pathWithQuery}`;
  const signature = twilio.computeSignature(url, form);
  const response = await app.inject({
    method: "POST",
    url: pathWithQuery,
    headers: {
      "content-type": "application/x-www-form-urlencoded",
      "x-twilio-signature": signature,
    },
    payload: new URLSearchParams(form).toString(),
  });
  return { statusCode: response.statusCode, body: response.body, headers: response.headers };
}

function auth(): Record<string, string> {
  return { authorization: `Bearer ${key}` };
}

before(async () => {
  dir = await mkdtemp(path.join(tmpdir(), "omalla-telephony-"));
  const config = loadConfig({
    dataDir: dir,
    seedDemo: true,
    allowCarrierPurchases: false,
    publicBaseUrl: "http://127.0.0.1:8787",
    masterKey: Buffer.alloc(32, 7).toString("base64"),
  });
  twilio = new TwilioProvider({
    accountSid: "AC00000000000000000000000000000000",
    authToken: "test-token",
    fetchImpl: async () => {
      outboundSid += 1;
      return new Response(JSON.stringify({ sid: `CAOUT${outboundSid}`, status: "queued" }), {
        status: 201,
        headers: { "content-type": "application/json" },
      });
    },
  });
  const registry = new TelephonyRegistry({ env: {}, providers: [twilio] });
  runtime = await OmallaRuntime.open(config, {
    offlineProviders: true,
    telephonyRegistry: registry,
  });
  app = await buildApp(runtime);
  key = (await readFile(path.join(dir, "api-key.txt"), "utf8")).trim();
  const tenant = runtime.db.col("tenants").list()[0];
  assert.ok(tenant);
  tenantId = tenant.id;
  const agent = runtime.db.col("agents").list((candidate) => candidate.tenantId === tenantId)[0];
  assert.ok(agent);
  agentId = agent.id;
  const number = runtime.db
    .col("phoneNumbers")
    .list((candidate) => candidate.tenantId === tenantId)[0];
  assert.ok(number);
  numberId = number.id;

  // This fixture behaves like a Twilio-provisioned number.
  runtime.db.col("phoneNumbers").update(numberId, {
    provider: "twilio",
    simulated: false,
    providerNumberId: "PNTEST",
  });
  const menu = runtime.db.col("ivrMenus").list((candidate) => candidate.tenantId === tenantId)[0];
  assert.ok(menu);
  ivrMenuId = menu.id;
});

after(async () => {
  await app?.close();
  await runtime?.close();
  if (dir) await rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
});

test("health reports the configured carrier and keeps the simulated default honest", async () => {
  const response = await app.inject({ method: "GET", url: "/v1/health" });
  assert.equal(response.statusCode, 200);
  const body = response.json() as {
    simulation: boolean;
    telephonyDefault: string;
    telephony: Array<{ id: string; available: boolean }>;
  };
  assert.equal(body.simulation, true);
  assert.equal(body.telephonyDefault, "simulated");
  assert.equal(body.telephony.find((entry) => entry.id === "twilio")?.available, true);
});

test("an unsigned or wrongly signed webhook is rejected", async () => {
  const unsigned = await app.inject({
    method: "POST",
    url: "/telephony/twilio/voice",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    payload: "CallSid=CA1&To=%2B15550001234&From=%2B15550009999",
  });
  assert.equal(unsigned.statusCode, 403);

  const wrong = await app.inject({
    method: "POST",
    url: "/telephony/twilio/voice",
    headers: {
      "content-type": "application/x-www-form-urlencoded",
      "x-twilio-signature": "not-a-signature",
    },
    payload: "CallSid=CA1&To=%2B15550001234&From=%2B15550009999",
  });
  assert.equal(wrong.statusCode, 403);
});

test("a signed inbound call produces media-stream TwiML and a durable call record", async () => {
  const form = {
    CallSid: "CAINBOUND1",
    From: "+15550009999",
    To: "+15550001234",
    Direction: "inbound",
    CallStatus: "ringing",
  };
  const response = await signedRequest("/telephony/twilio/voice", form);
  assert.equal(response.statusCode, 200);
  assert.match(response.body, /<Connect><Stream url="ws:\/\/127\.0\.0\.1:8787\/telephony\/twilio\/media\?callId=/);
  assert.match(response.body, /&amp;token=/);

  const call = runtime.findCallByProviderId("CAINBOUND1");
  assert.ok(call);
  assert.equal(call.simulation, false);
  assert.equal(call.agentId, agentId);
  assert.equal(call.status, "in_progress");

  const mediaUrl = /<Stream url="([^"]+)"/.exec(response.body)?.[1] ?? "";
  const parsed = new URL(mediaUrl.replace(/&amp;/g, "&"));
  const callId = parsed.searchParams.get("callId") ?? "";
  const token = parsed.searchParams.get("token") ?? "";
  assert.equal(runtime.verifyMediaToken(callId, token), true);
  // Single-use media token is consumed on first verification (OM-T3)
  assert.equal(runtime.verifyMediaToken(callId, token), false);
  assert.equal(runtime.verifyMediaToken(callId, `${token}x`), false);
});

test("an unconfigured destination is refused without leaking internal names", async () => {
  const response = await signedRequest("/telephony/twilio/voice", {
    CallSid: "CAINBOUND2",
    From: "+15550009999",
    To: "+15559998888",
    Direction: "inbound",
  });
  assert.equal(response.statusCode, 200);
  assert.match(response.body, /not configured/);
  assert.match(response.body, /<Hangup\/>/);
});

test("the IVR gathers a digit and routes to the configured agent", async () => {
  const number = runtime.db.col("phoneNumbers").get(numberId);
  assert.ok(number);
  runtime.db.col("phoneNumbers").update(numberId, {
    ...number,
    inboundAgentId: undefined,
    ivrMenuId,
  });

  const voice = await signedRequest("/telephony/twilio/voice", {
    CallSid: "CAIVR1",
    From: "+15550009999",
    To: "+15550001234",
    Direction: "inbound",
  });
  assert.equal(voice.statusCode, 200);
  assert.match(voice.body, /<Gather input="dtmf"/);
  assert.match(voice.body, /appointments/i);

  const call = runtime.findCallByProviderId("CAIVR1");
  assert.ok(call);
  const dtmf = await signedRequest(
    `/telephony/twilio/dtmf?callId=${encodeURIComponent(call.id)}&menuId=${encodeURIComponent(ivrMenuId)}&attempt=0`,
    { CallSid: "CAIVR1", Digits: "1", To: "+15550001234", From: "+15550009999" },
  );
  assert.equal(dtmf.statusCode, 200);
  assert.match(dtmf.body, /<Connect><Stream/);
  assert.equal(runtime.db.col("calls").get(call.id)?.agentId, agentId);

  runtime.db.col("phoneNumbers").update(numberId, {
    ...number,
    inboundAgentId: agentId,
    ivrMenuId: undefined,
  });
});

test("a completed status callback ends the call exactly once", async () => {
  const call = runtime.findCallByProviderId("CAINBOUND1");
  assert.ok(call);
  const form = {
    CallSid: "CAINBOUND1",
    CallStatus: "completed",
    CallDuration: "14",
    From: "+15550009999",
    To: "+15550001234",
  };
  const first = await signedRequest("/telephony/twilio/status", form);
  assert.equal(first.statusCode, 204);
  // Exact byte-for-byte carrier webhook replay is rejected by replayCache (OM-T3)
  const replay = await signedRequest("/telephony/twilio/status", form);
  assert.equal(replay.statusCode, 409);
  // A distinct terminal status callback remains idempotent on the call record
  const second = await signedRequest("/telephony/twilio/status", {
    ...form,
    CallDuration: "15",
  });
  assert.equal(second.statusCode, 204);

  const ended = runtime.db.col("calls").get(call.id);
  assert.equal(ended?.status, "ended");
  assert.equal(ended?.metadata.providerDurationSec, 14);
  assert.equal(ended?.metadata.carrierPostCallRan, true);
});

test("a recording callback stores metadata and never fetches the recording", async () => {
  const call = runtime.findCallByProviderId("CAIVR1");
  assert.ok(call);
  const response = await signedRequest("/telephony/twilio/recording", {
    CallSid: "CAIVR1",
    RecordingSid: "RE1",
    RecordingStatus: "completed",
    RecordingUrl: "https://api.twilio.com/2010-04-01/recordings/RE1",
    RecordingDuration: "9",
  });
  assert.equal(response.statusCode, 204);
  const stored = runtime.db.col("calls").get(call.id);
  assert.equal(stored?.recording?.enabled, true);
  assert.equal(stored?.recording?.durationMs, 9000);
  assert.match(stored?.recording?.url ?? "", /RE1/);
});

test("number search is free by default, provisioning requires explicit confirmation", async () => {
  const search = await app.inject({
    method: "POST",
    url: "/v1/numbers/search",
    headers: auth(),
    payload: { countryCode: "US", limit: 3 },
  });
  assert.equal(search.statusCode, 200);
  const offers = search.json() as { carrierCharges: boolean; offers: Array<{ e164: string; costNote: string }> };
  assert.equal(offers.carrierCharges, false);
  assert.equal(offers.offers.length, 3);
  assert.match(offers.offers[0]?.costNote ?? "", /free/i);

  const noConfirm = await app.inject({
    method: "POST",
    url: "/v1/numbers/provision",
    headers: auth(),
    payload: { e164: "+15551234567" },
  });
  assert.equal(noConfirm.statusCode, 400);

  const provisioned = await app.inject({
    method: "POST",
    url: "/v1/numbers/provision",
    headers: auth(),
    payload: { e164: "+15551234567", label: "Test line", confirm: true, agentId },
  });
  assert.equal(provisioned.statusCode, 201);
  const created = provisioned.json() as { number: { id: string; simulated: boolean; provider: string }; billing: { carrierCharges: boolean } };
  assert.equal(created.number.simulated, true);
  assert.equal(created.billing.carrierCharges, false);

  const realWithoutGate = await app.inject({
    method: "POST",
    url: "/v1/numbers/provision",
    headers: auth(),
    payload: { provider: "twilio", e164: "+14155550123", confirm: true },
  });
  assert.equal(realWithoutGate.statusCode, 403);
  assert.match(realWithoutGate.json<{ error: { message: string } }>().error.message, /OMALLA_ALLOW_CARRIER_PURCHASES/);

  const releaseNoConfirm = await app.inject({
    method: "DELETE",
    url: `/v1/numbers/${created.number.id}`,
    headers: auth(),
  });
  assert.equal(releaseNoConfirm.statusCode, 400);
  const released = await app.inject({
    method: "DELETE",
    url: `/v1/numbers/${created.number.id}?confirm=true`,
    headers: auth(),
  });
  assert.equal(released.statusCode, 200);
});

test("simulated SMS requires consent, is labelled simulated, and is listed", async () => {
  const denied = await app.inject({
    method: "POST",
    url: "/v1/sms",
    headers: auth(),
    payload: { to: "+15550009999", body: "hello", consent: false },
  });
  assert.equal(denied.statusCode, 403);

  // A dedicated simulated line keeps this assertion about the simulator even
  // though the shared fixture number is Twilio-provisioned.
  const line = await app.inject({
    method: "POST",
    url: "/v1/numbers/provision",
    headers: auth(),
    payload: { e164: "+15559876543", label: "Simulated SMS line", confirm: true },
  });
  assert.equal(line.statusCode, 201);

  const sent = await app.inject({
    method: "POST",
    url: "/v1/sms",
    headers: auth(),
    payload: {
      to: "+15550009999",
      from: "+15559876543",
      body: "Your appointment is confirmed.",
      consent: true,
    },
  });
  assert.equal(sent.statusCode, 201);
  const message = sent.json() as { id: string; simulated: boolean; status: string };
  assert.equal(message.simulated, true);
  assert.equal(message.status, "queued");

  const listed = await app.inject({ method: "GET", url: "/v1/sms", headers: auth() });
  assert.equal(listed.statusCode, 200);
  const messages = listed.json() as Array<{ id: string }>;
  assert.ok(messages.some((candidate) => candidate.id === message.id));
});

test("an inbound SMS webhook stores the message for its tenant", async () => {
  const response = await signedRequest("/telephony/twilio/sms", {
    MessageSid: "SMIN1",
    SmsStatus: "received",
    From: "+15550009999",
    To: "+15550001234",
    Body: "Can I move my appointment?",
  });
  assert.equal(response.statusCode, 204);
  const stored = runtime.db
    .col("smsMessages")
    .list((message) => message.providerMessageId === "SMIN1")[0];
  assert.ok(stored);
  assert.equal(stored.tenantId, tenantId);
  assert.equal(stored.direction, "inbound");
});

test("carrier outbound calls pass policy, go through the provider and are marked non-simulated", async () => {
  const response = await app.inject({
    method: "POST",
    url: "/v1/calls/outbound",
    headers: auth(),
    payload: {
      to: "+15550009999",
      agentId,
      consent: true,
      mode: "carrier",
      provider: "twilio",
    },
  });
  assert.equal(response.statusCode, 201);
  const call = response.json() as {
    id: string;
    simulation: boolean;
    status: string;
    metadata: { providerCallId: string; provider: string };
  };
  assert.equal(call.simulation, false);
  assert.equal(call.metadata.provider, "twilio");
  assert.match(call.metadata.providerCallId, /^CAOUT/);
  assert.equal(runtime.db.col("calls").get(call.id)?.status, "queued");

  const denied = await app.inject({
    method: "POST",
    url: "/v1/calls/outbound",
    headers: auth(),
    payload: { to: "+15550009999", agentId, consent: false, mode: "carrier", provider: "twilio" },
  });
  assert.equal(denied.statusCode, 403);
});

test("the simulated provider has no public webhook surface", async () => {
  const response = await app.inject({
    method: "POST",
    url: "/telephony/simulated/voice",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    payload: "CallSid=CA1&To=%2B15550001234&From=%2B15550009999",
  });
  assert.equal(response.statusCode, 404);
});
