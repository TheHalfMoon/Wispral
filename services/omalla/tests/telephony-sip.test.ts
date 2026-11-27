import assert from "node:assert/strict";
import { test } from "node:test";
import {
  SIP_ENGINES,
  buildSipGatewayContract,
  sipGatewayDescriptors,
} from "@omalla/telephony";

test("a gateway contract points at the sip webhooks and media socket", () => {
  const contract = buildSipGatewayContract({
    engine: "asterisk",
    publicBaseUrl: "https://calls.example.com/omalla/",
    token: "0123456789abcdef0123456789abcdef",
    sipHost: "sip.example.com",
    sipPort: 5070,
  });

  assert.equal(contract.provider, "sip");
  assert.equal(contract.voiceWebhookUrl, "https://calls.example.com/omalla/telephony/sip/voice");
  assert.equal(contract.dtmfWebhookUrl, "https://calls.example.com/omalla/telephony/sip/dtmf");
  assert.equal(contract.statusWebhookUrl, "https://calls.example.com/omalla/telephony/sip/status");
  assert.equal(contract.mediaWebSocketUrl, "wss://calls.example.com/omalla/telephony/sip/media");
  assert.equal(contract.sip.inboundUri, "sip:inbound@sip.example.com:5070");
  assert.equal(contract.auth.header, "x-omalla-gateway-token");
  assert.deepEqual(contract.media, {
    encoding: "audio/x-mulaw",
    sampleRate: 8000,
    channels: 1,
    frameMs: 20,
    direction: "bidirectional",
    wireFormat: "json",
  });
  assert.equal(contract.requirements.some((line) => line.includes("http; production")), false);
});

test("an http base URL is called out and the websocket downgrades with it", () => {
  const contract = buildSipGatewayContract({
    engine: "jambonz",
    publicBaseUrl: "http://127.0.0.1:8787",
    token: "0123456789abcdef",
  });
  assert.equal(contract.mediaWebSocketUrl, "ws://127.0.0.1:8787/telephony/sip/media");
  assert.equal(contract.sip.host, "127.0.0.1");
  assert.equal(contract.sip.port, 5060);
  assert.ok(contract.requirements.some((line) => line.includes("http; production")));
});

test("a weak token and a relative base URL are rejected", () => {
  assert.throws(
    () => buildSipGatewayContract({ engine: "asterisk", publicBaseUrl: "https://x.test", token: "short" }),
    /at least 16/,
  );
  assert.throws(
    () => buildSipGatewayContract({ engine: "asterisk", publicBaseUrl: "/relative", token: "0123456789abcdef" }),
    /absolute/,
  );
});

test("every SIP engine is described and none claims to have been run", () => {
  const engines = sipGatewayDescriptors();
  assert.deepEqual(engines.map((engine) => engine.id), [...SIP_ENGINES]);
  for (const engine of engines) {
    assert.equal(engine.verification, "not-run");
    assert.ok(engine.licence.length > 0);
    assert.ok(engine.containerImage.length > 0);
    assert.ok(engine.notes.length > 0);
  }
});
