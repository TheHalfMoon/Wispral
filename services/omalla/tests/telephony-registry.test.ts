import assert from "node:assert/strict";
import { test } from "node:test";
import { SimulatedTelephonyProvider, TelephonyRegistry } from "@omalla/telephony";

test("the simulator is always available and is the default", () => {
  const registry = new TelephonyRegistry({ env: {} });
  assert.equal(registry.default.id, "simulated");
  assert.ok(registry.default instanceof SimulatedTelephonyProvider);
  const twilio = registry.availability({}).find((entry) => entry.id === "twilio");
  assert.equal(twilio?.available, false);
  assert.match(twilio?.detail ?? "", /TWILIO_ACCOUNT_SID/);
});

test("carriers appear only when their credentials exist", () => {
  const registry = new TelephonyRegistry({
    env: {
      TWILIO_ACCOUNT_SID: "AC1",
      TWILIO_AUTH_TOKEN: "secret",
      OMALLA_TELEPHONY_PROVIDER: "twilio",
    },
  });
  assert.equal(registry.default.id, "twilio");
  const twilio = registry.availability({ TWILIO_ACCOUNT_SID: "AC1", TWILIO_AUTH_TOKEN: "secret" }).find(
    (entry) => entry.id === "twilio",
  );
  assert.equal(twilio?.available, true);
  assert.equal(registry.get("twilio").capabilities.mediaStream, "bidirectional");
});

test("an unknown requested provider falls back to the simulator", () => {
  const registry = new TelephonyRegistry({ env: { OMALLA_TELEPHONY_PROVIDER: "not-real" } });
  assert.equal(registry.default.id, "simulated");
});

test("SignalWire is selected through its Twilio-compatible credentials", () => {
  const registry = new TelephonyRegistry({
    env: {
      SIGNALWIRE_SPACE_URL: "https://example.signalwire.com",
      SIGNALWIRE_PROJECT_ID: "project-1",
      SIGNALWIRE_TOKEN: "token-1",
    },
  });
  const provider = registry.get("signalwire");
  assert.equal(provider.id, "signalwire");
  assert.match(provider.label, /SignalWire/);
  assert.equal(provider.capabilities.sms, true);
});

test("Telnyx, Vonage, and SIP adapters activate when their credentials exist", () => {
  const env = {
    TELNYX_API_KEY: "key",
    TELNYX_CONNECTION_ID: "1",
    VONAGE_API_KEY: "key",
    VONAGE_API_SECRET: "secret",
    VONAGE_APPLICATION_ID: "app",
    OMALLA_SIP_GATEWAY_URL: "http://127.0.0.1:5080",
  };
  const registry = new TelephonyRegistry({ env });
  const telnyx = registry.availability(env).find((entry) => entry.id === "telnyx");
  const vonage = registry.availability(env).find((entry) => entry.id === "vonage");
  const sip = registry.availability(env).find((entry) => entry.id === "sip");
  assert.equal(telnyx?.available, true);
  assert.equal(vonage?.available, true);
  assert.equal(sip?.available, true);
  assert.equal(registry.get("telnyx").capabilities.transfer, true);
  assert.equal(registry.get("vonage").capabilities.transfer, true);
  assert.equal(registry.get("sip").capabilities.sip, true);
});

test("a missing SIP gateway never pretends to be a carrier", () => {
  const registry = new TelephonyRegistry({ env: {} });
  const sip = registry.availability({}).find((entry) => entry.id === "sip");
  assert.equal(sip?.available, false);
  assert.match(sip?.detail ?? "", /no gateway configured/);
});
