import assert from "node:assert/strict";
import { test } from "node:test";
import { TwilioProvider } from "@omalla/telephony";

const TOKEN = "12345";

function provider(fetchImpl?: typeof fetch): TwilioProvider {
  return new TwilioProvider({
    accountSid: "AC00000000000000000000000000000000",
    authToken: TOKEN,
    ...(fetchImpl ? { fetchImpl } : {}),
  });
}

function request(url: string, form: Record<string, string>, signature?: string) {
  const headers: Record<string, string> = {};
  if (signature) headers["x-twilio-signature"] = signature;
  return {
    url,
    method: "POST",
    headers,
    form,
  };
}

test("Twilio signature matches the documented HMAC-SHA1 construction", () => {
  // Cross-checked with an independent Python hmac implementation.
  const params = {
    CallSid: "CA1234567890ABCDE",
    Caller: "+12349013030",
    Digits: "1234",
    From: "+12349013030",
    To: "+18005551212",
  };
  const url = "https://example.com/myapp";
  const instance = provider();
  assert.equal(instance.computeSignature(url, params), "NGAgWNhdnsLF8j385frvrQoi9sg=");
  assert.equal(instance.verifyWebhook(request(url, params, "NGAgWNhdnsLF8j385frvrQoi9sg=")).valid, true);
});

test("Twilio signature rejects a tampered parameter, missing header and wrong URL", () => {
  const params = { CallSid: "CA1", From: "+15550001111", To: "+15550002222" };
  const instance = provider();
  const signature = instance.computeSignature("https://example.com/voice", params);

  const tampered = instance.verifyWebhook(
    request("https://example.com/voice", { ...params, From: "+15550009999" }, signature),
  );
  assert.equal(tampered.valid, false);

  const missing = instance.verifyWebhook(request("https://example.com/voice", params));
  assert.equal(missing.valid, false);
  assert.match(missing.reason ?? "", /signature/i);

  const wrongUrl = instance.verifyWebhook(
    request("https://evil.example/voice", params, signature),
  );
  assert.equal(wrongUrl.valid, false);
});

test("signature tolerates the standard HTTPS port being present or absent", () => {
  const params = { CallSid: "CA1" };
  const instance = provider();
  const withPort = "https://example.com:443/voice";
  const signature = instance.computeSignature(withPort, params);
  assert.equal(instance.verifyWebhook(request("https://example.com/voice", params, signature)).valid, true);
});

test("inbound and status webhooks are parsed into canonical events", () => {
  const instance = provider();
  const inbound = instance.parseInbound(
    request("https://example.com/voice", {
      CallSid: "CA123",
      From: "+15550001111",
      To: "+15550002222",
      Direction: "inbound",
      CallStatus: "ringing",
      AccountSid: "AC1",
    }),
  );
  assert.deepEqual(
    { id: inbound.providerCallId, from: inbound.from, to: inbound.to, direction: inbound.direction },
    { id: "CA123", from: "+15550001111", to: "+15550002222", direction: "inbound" },
  );

  const status = instance.parseStatus(
    request("https://example.com/status", {
      CallSid: "CA123",
      CallStatus: "in-progress",
      CallDuration: "12",
    }),
  );
  assert.equal(status.status, "in-progress");
  assert.equal(status.durationSec, 12);

  assert.equal(instance.parseDtmf(request("https://example.com/dtmf", { CallSid: "CA123", Digits: "7" })).digits, "7");

  const recording = instance.parseRecordingStatus(
    request("https://example.com/recording", {
      CallSid: "CA123",
      RecordingSid: "RE1",
      RecordingStatus: "completed",
      RecordingUrl: "https://api.twilio.com/recordings/RE1",
      RecordingDuration: "3",
    }),
  );
  assert.equal(recording.status, "completed");
  assert.equal(recording.durationMs, 3000);

  const sms = instance.parseSms(
    request("https://example.com/sms", {
      MessageSid: "SM1",
      SmsStatus: "received",
      From: "+15550001111",
      To: "+15550002222",
      Body: "hello",
    }),
  );
  assert.equal(sms.body, "hello");
  assert.equal(sms.status, "received");
});

test("TwiML connects a bidirectional media stream with escaped parameters", () => {
  const instance = provider();
  const response = instance.renderInboundResponse({
    say: "One moment & welcome.",
    mediaStreamUrl: "wss://example.com/telephony/twilio/media?callId=call_1",
    parameters: { callId: "call_1", note: "a\"b<c" },
    closingSay: "Goodbye & thanks.",
  });

  assert.equal(response.contentType, "text/xml; charset=utf-8");
  assert.match(response.body, /<Say>One moment &amp; welcome\.<\/Say>/);
  assert.match(response.body, /<Connect><Stream url="wss:\/\/example\.com\/telephony\/twilio\/media\?callId=call_1">/);
  assert.match(response.body, /<Parameter name="callId" value="call_1"\/>/);
  assert.match(response.body, /<Parameter name="note" value="a&quot;b&lt;c"\/>/);
  assert.match(response.body, /<Say>Goodbye &amp; thanks\.<\/Say>/);
  assert.doesNotMatch(response.body, /<Hangup\/>/);
});

test("TwiML gathers DTMF digits into an action URL", () => {
  const instance = provider();
  const response = instance.renderInboundResponse({
    gather: {
      actionUrl: "https://example.com/telephony/twilio/dtmf?callId=call_1",
      numDigits: 1,
      prompt: "Press 1 for sales",
      timeoutSec: 4,
    },
  });
  assert.match(response.body, /<Gather input="dtmf" action="https:\/\/example\.com\/telephony\/twilio\/dtmf\?callId=call_1" method="POST" numDigits="1" timeout="4">/);
  assert.match(response.body, /Press 1 for sales/);
});

test("media stream messages round-trip through the parser and encoder", () => {
  const instance = provider();

  const started = instance.parseMediaMessage(
    JSON.stringify({
      event: "start",
      sequenceNumber: "1",
      start: {
        streamSid: "MZ123",
        callSid: "CA123",
        tracks: ["inbound"],
        customParameters: { callId: "call_1" },
        mediaFormat: { encoding: "audio/x-mulaw", sampleRate: 8000, channels: 1 },
      },
    }),
  );
  assert.equal(started.type, "start");
  if (started.type !== "start") return;
  assert.equal(started.streamId, "MZ123");
  assert.equal(started.callId, "CA123");
  assert.deepEqual(started.parameters, { callId: "call_1" });
  assert.equal(started.format.encoding, "audio/x-mulaw");

  const media = instance.parseMediaMessage(
    JSON.stringify({ event: "media", media: { track: "inbound", payload: "AAAA", timestamp: "20" } }),
  );
  assert.equal(media.type, "media");
  if (media.type === "media") assert.equal(media.payload, "AAAA");

  const dtmf = instance.parseMediaMessage(JSON.stringify({ event: "dtmf", dtmf: { digit: "5" } }));
  assert.deepEqual(dtmf, { type: "dtmf", digit: "5" });

  assert.deepEqual(instance.parseMediaMessage(JSON.stringify({ event: "stop" })), { type: "stop" });
  assert.equal(instance.parseMediaMessage("not json").type, "unknown");

  const frame = JSON.parse(instance.encodeMediaFrame("MZ123", "AAAA")) as Record<string, unknown>;
  assert.deepEqual(frame, { event: "media", streamSid: "MZ123", media: { payload: "AAAA" } });
  assert.deepEqual(JSON.parse(instance.encodeClearFrame("MZ123")), { event: "clear", streamSid: "MZ123" });
});

test("outbound calls use the signed REST contract and never put credentials in the URL", async () => {
  let captured: { url: string; init: RequestInit } | undefined;
  const fakeFetch: typeof fetch = async (input, init) => {
    captured = { url: String(input), init: init ?? {} };
    return new Response(JSON.stringify({ sid: "CA999", status: "queued" }), {
      status: 201,
      headers: { "content-type": "application/json" },
    });
  };

  const call = await provider(fakeFetch).createCall({
    to: "+15550001111",
    from: "+15550002222",
    answerUrl: "https://example.com/telephony/twilio/voice",
    statusCallbackUrl: "https://example.com/telephony/twilio/status",
    record: true,
    timeoutSec: 20,
  });

  assert.deepEqual(call, { providerCallId: "CA999", status: "queued" });
  assert.ok(captured);
  const url = captured?.url ?? "";
  assert.match(url, /\/2010-04-01\/Accounts\/AC00000000000000000000000000000000\/Calls\.json$/);
  assert.doesNotMatch(url, new RegExp(TOKEN));

  const headers = captured?.init.headers as Record<string, string>;
  assert.equal(headers.authorization, `Basic ${Buffer.from(`AC00000000000000000000000000000000:${TOKEN}`).toString("base64")}`);
  const form = new URLSearchParams(String(captured?.init.body));
  assert.equal(form.get("To"), "+15550001111");
  assert.equal(form.get("Record"), "true");
  assert.equal(form.get("Timeout"), "20");
  assert.deepEqual(form.getAll("StatusCallbackEvent"), ["initiated", "ringing", "answered", "completed"]);
});

test("hanging up redirects a live call and SMS uses the Messages endpoint", async () => {
  const calls: Array<{ url: string; body: string | undefined }> = [];
  const fakeFetch: typeof fetch = async (input, init) => {
    calls.push({ url: String(input), body: init?.body ? String(init.body) : undefined });
    return new Response(JSON.stringify({ sid: "SM1", status: "sent" }), { status: 201 });
  };
  const instance = provider(fakeFetch);

  await instance.hangupCall("CA999");
  await instance.redirectCall("CA999", "https://example.com/telephony/twilio/transfer");
  const sms = await instance.sendSms({ to: "+15550001111", from: "+15550002222", body: "See you then" });

  assert.equal(sms.providerMessageId, "SM1");
  assert.match(calls[0]?.url ?? "", /Calls\/CA999\.json$/);
  assert.equal(new URLSearchParams(calls[0]?.body).get("Status"), "completed");
  assert.equal(new URLSearchParams(calls[1]?.body).get("Url"), "https://example.com/telephony/twilio/transfer");
  assert.match(calls[2]?.url ?? "", /Messages\.json$/);
  assert.equal(new URLSearchParams(calls[2]?.body).get("Body"), "See you then");
});

test("number search, provisioning and release map the Twilio resource", async () => {
  const requests: string[] = [];
  const fakeFetch: typeof fetch = async (input, init) => {
    const url = String(input);
    requests.push(`${init?.method ?? "GET"} ${url}`);
    if (url.includes("AvailablePhoneNumbers")) {
      return new Response(
        JSON.stringify({
          available_phone_numbers: [
            {
              phone_number: "+15551234567",
              friendly_name: "(555) 123-4567",
              locality: "Seattle",
              region: "WA",
              postal_code: "98101",
              capabilities: { voice: true, sms: true, mms: false },
            },
          ],
        }),
        { status: 200 },
      );
    }
    if (init?.method === "DELETE") return new Response(null, { status: 204 });
    return new Response(
      JSON.stringify({
        sid: "PN123",
        phone_number: "+15551234567",
        friendly_name: "Front desk",
        capabilities: { voice: true, sms: true },
      }),
      { status: 201 },
    );
  };

  const instance = provider(fakeFetch);
  const offers = await instance.searchNumbers({ countryCode: "US", areaCode: "555", smsCapable: true });
  assert.equal(offers.length, 1);
  assert.equal(offers[0]?.e164, "+15551234567");
  assert.deepEqual(offers[0]?.capabilities, ["voice", "sms"]);
  assert.match(offers[0]?.costNote ?? "", /carrier charges/i);
  assert.match(requests[0] ?? "", /SmsEnabled=true/);

  const provisioned = await instance.provisionNumber({
    e164: "+15551234567",
    friendlyName: "Front desk",
    voiceUrl: "https://example.com/telephony/twilio/voice",
  });
  assert.equal(provisioned.providerNumberId, "PN123");
  assert.equal(provisioned.friendlyName, "Front desk");

  await instance.releaseNumber("PN123");
  assert.match(requests[2] ?? "", /^DELETE .*IncomingPhoneNumbers\/PN123\.json$/);
});

test("carrier errors surface without leaking the auth token", async () => {
  const fakeFetch: typeof fetch = async () =>
    new Response(JSON.stringify({ code: 20003, message: "Authentication Error", status: 401 }), {
      status: 401,
      headers: { "content-type": "application/json" },
    });

  await assert.rejects(
    provider(fakeFetch).createCall({
      to: "+15550001111",
      from: "+15550002222",
      answerUrl: "https://example.com/voice",
    }),
    (error: unknown) => {
      const message = (error as Error).message;
      assert.match(message, /Authentication Error/);
      assert.doesNotMatch(message, /12345/);
      return true;
    },
  );
});
