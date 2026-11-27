# Omalla Python SDK

A dependency-free client for the Omalla HTTP API. Standard library only, so it
runs on Python 3.9+ with no virtualenv and no `pip install`:

```python
import sys
sys.path.insert(0, "sdks/python")

from omalla import OmallaClient, OmallaApiError

client = OmallaClient(
    api_key="omk_...",                 # .omalla/api-key.txt after the first run
    base_url="http://127.0.0.1:8787",
)

client.health()
me = client.me()
providers = client.telephony.providers()

# A free in-process call. No carrier, no PSTN, no charge.
call = client.calls.simulate(say=["I would like to book a cleaning on Tuesday."])
print(client.calls.get(call["id"])["transcript"])

# Native automation, installed as a draft and run explicitly.
template = client.templates.install("ai_receptionist")
client.workflows.update(template["id"], status="active")
run = client.workflows.run(template["id"], payload={"phone": "+15550009999"})

# SMS requires consent and is labelled simulated when no carrier is configured.
client.sms.send(to="+15550002222", body="Your appointment is confirmed.", consent=True)
```

## Errors

```python
try:
    client.sms.send(to="+15550002222", body="hi", consent=False)
except OmallaApiError as error:
    print(error.status, error.code, error.body)   # 403 blocked_by_policy ...
```

GET requests retry on network errors and 5xx (default two retries). Mutations are
never retried automatically.

## Install (optional)

The SDK is a plain package; installing is optional and useful only for editor
completion:

```bash
pip install ./sdks/python
```

## Tests

```bash
# Unit tests against a local fake server, no Omalla instance needed
python -m unittest discover -s sdks/python/tests -t sdks/python -v

# Live test: unit tests plus 18 checks against a real server (simulated provider)
npm run smoke:python
```

`npm run smoke:python` builds and boots Omalla itself, so it also proves the
client and server agree on the wire format. It does not touch a carrier.

## What is not covered

- No websocket call-event stream yet (the TypeScript SDK has it). Poll
  `calls.get` for now.
- No automatic pagination; list endpoints return what the server returns.
- No async client. `urllib` is blocking; run it in a thread or worker if needed.
