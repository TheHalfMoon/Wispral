# KT-01: Parlant spike with a deterministic fake LLM backend

**Grain:** `KT-01` (Specification 000E). Packet in `research/wispral-world-class/packets.json`. This is a research path, not Klaint product code.

**Result: NOT VERIFIED.**

- One acceptance item **fails**: a forged `customer_id` sent to the integrated tool server is accepted, the tool runs, and data comes back. The tool server cannot be disabled.
- One item is **NOT RUN**: the measurement on a pinned local CPU model, because no model has been authorized.

The other items are recorded below.

**Recommendation:** Parlant **v4.0.2**, but only if Klaint adds its own gates (see [Decision](#decision-v4-versus-v332)). v3.3.2 lacks the tool-call hooks the packet requires and has the same tool-server flaw.

## What was tested

| Item | Value |
| --- | --- |
| Primary | `emcie-co/parlant@2a463ccd10eaf0d70d42731705f4f00ef066bee8` (release v4.0.2; `pyproject.toml` version 4.0.2), environment `uv sync --frozen --python 3.12 --extra anthropic --extra gemini` |
| Fallback | `emcie-co/parlant@61bba3b2b3fffd677d345e393e8c942dbd400297` (v3.3.2) |
| Source form | both were unpacked source trees, not git checkouts; the commit IDs come from the planning record |
| Machine | HW-A (Intel Core i5-13420H, 16 GB RAM, Windows 11 Home), on CPU, with no other build running during the final set |
| Model access | **none**. Every model capability is the in-process fake below. No API key was used, no model weights were downloaded or run, and no network model was called. |

### The fake backend

[`harness/fake_provider.py`](harness/fake_provider.py) is registered with Parlant v4's provider registry as the provider `fake`. Tests select it with `MODELS = {"*": "fake"}`. It is deterministic and records every call.

| Capability | Fake behaviour |
| --- | --- |
| Schematic generation | Builds a minimal valid instance of the requested schema. Strings are `"fake-text"`; lists of strings get 10 items. |
| Decision | Propositions get a scripted probability. A choice takes its first option; a scale takes its middle level. |
| ReAct (reply and tool use) | Adapted from Parlant's own test fake `_FakeReactGenerator` (`tests/core/nlp/test_react.py`, Apache-2.0; the file keeps the attribution and states that it was adapted). It calls the scripted tool once if that tool is offered, otherwise it replies `FAKE_REPLY`. |
| Embedding, moderation, tokenizer | A 64-dimension SHA-256 embedding, no moderation, a zero-count tokenizer |

[`harness/fake_provider_v3.py`](harness/fake_provider_v3.py) is a `NLPService` with the same idea for v3.3.2.

**Correction during the run.** The fake first returned `""` for every string. Parlant's own `test_hook_results.py` then failed in rule indexing ("Generated title is empty"; [`earlier/ported1.log`](../wispral-world-class/evidence/kt01-hwa/earlier/ported1.log)). The fake was changed to return non-empty strings, and **every v4 result below is from the final rerun on the changed fake** ([`final/`](../wispral-world-class/evidence/kt01-hwa/final/), [`harness/run_final.sh`](harness/run_final.sh)). The earlier logs are kept in [`earlier/`](../wispral-world-class/evidence/kt01-hwa/earlier/).

## Results against the packet

Evidence is in `research/wispral-world-class/evidence/kt01-hwa/`, below shortened to `final/` and `earlier/`.

| Packet acceptance item | Result | Evidence |
| --- | --- | --- |
| Hooks `on_reviewing_tool_calls`, `on_calling_tools` and `on_message_generated` fire in order | **Observed in order on v4** (details below) | `final/hooks.log` |
| A BAIL in `on_message_generated` emits a replacement | **Only in BLOCK output mode.** In the default STREAM mode, the original draft is delivered. | `final/security.log` |
| Plugin tool server disabled; a loopback call with a forged `customer_id` has no effect and returns no data | **FAIL on v4 and on v3.3.2** | `final/security.log`, `earlier/v3run2.log` |
| LLM calls per turn, p95 turn latency (fake backend **and** one pinned local CPU model) and idle RSS on HW-A | **Fake backend: measured. Local CPU model: NOT RUN** (no authorized model) | `final/perf.log` |
| Decision v4 versus v3.3.2 recorded | Recorded below | this file |
| Tests: ported `tests/core/stable/engines/test_hooks.py` and `tests/sdk/test_hook_results.py` | **9 of 9 pass on v4 with the fake.** Eight are unit tests of hook-chain helpers and do not touch the model. One SDK test runs a turn on the fake. None exercises the three required hooks in a live turn; that is covered by the hook-order test above. Run unchanged through [`harness/kt01_port.py`](harness/kt01_port.py), which only installs the fake and switches `SDKTest`'s default model map from Gemini to `fake` | `final/ported.log` |

### Hook order (v4)

One turn in which the fake calls a tool (`lookup_order`, which ran) gave this hook sequence:

`on_preparing`, `on_generating_messages`, `on_step_started`, **`on_reviewing_tool_calls`**, `on_tool_calls_reviewed`, **`on_calling_tools`**, `on_tool_calls_completed`, `on_step_completed`, `on_step_started`, **`on_message_generated`**, `on_step_completed`, `on_messages_emitted`.

The three required hooks fire in the required order. The order of the others (for example `on_generating_messages` before the first step) is recorded as observed, without judgement. `on_reviewing_message` was registered but did not fire; no message reviewer ran in this turn.

`test_kt01_hooks.py` prints the order and asserts nothing, so this result rests on the logged `HOOKS` line, not on the test's pass status.

### BAIL replacement (v4)

The test hook on `on_message_generated` records the draft, emits `SYNTHETIC_REPLACEMENT` and returns BAIL.

| Output mode | Draft seen by the hook | Delivered to the customer |
| --- | --- | --- |
| BLOCK | `FAKE_REPLY` | `SYNTHETIC_REPLACEMENT` |
| STREAM (Parlant's default) | `FAKE_REPLY` | **`FAKE_REPLY`**: the original draft |

The test reads the first agent message only. The v4 source agrees with the reading: the docstring of `_complete_message_step` in `base_loop.py` says a BAIL suppresses the message only in the blocking loop, and that in streaming the hook only observes.

**Security consequence.** In streaming mode this hook cannot stop or replace a message. A Klaint message gate built on it must run the agent in BLOCK mode, or gate at a point that comes before streaming.

### Forged `customer_id` through the integrated tool server

Parlant starts an integrated plugin tool server on `127.0.0.1` with no authentication. In both versions the spike found no setting that turns it off. The test called it directly from the same machine:

| Step | v4.0.2 | v3.3.2 |
| --- | --- | --- |
| `GET /tools` | 200, lists `read_balance` | 200 |
| `POST /tools/read_balance/calls` with `customer_id: "FORGED_CUSTOMER"` and a made-up session | **200**, body contains `{"customer_id":"FORGED_CUSTOMER","balance":"SYNTHETIC-100"}` | **200**, same data |
| What the tool received | `context.customer_id == "FORGED_CUSTOMER"` | the same |

The test observes and does not assert the desired outcome. Its "passed" status means it ran, not that the server is safe. **Any local process can call any registered tool as any customer.**

### Session-token isolation (v4)

This used synthetic test-only secrets and two customers, alpha and beta, with `AuthConfig(admin_api_key=…, customer_jwt_secret=…)`:

| Request | Status |
| --- | --- |
| Admin creates beta's session | 201 |
| Alpha's token reads beta's session, lists its events, posts into it | 403, 403, 403 |
| Beta's token does the same | 200, 200, 201 |
| A token signed with the wrong secret reads beta's session | 401 |

The test records these statuses but asserts none of them, so the results rest on the logged values. The HTTP API enforces principal isolation. The tool server above does not go through it.

### Performance (v4, fake backend)

This is 40 turns each, BLOCK mode, measured inside the test process, from [`final/perf.log`](../wispral-world-class/evidence/kt01-hwa/final/perf.log):

| Turn type | p50 | p95 | max | Model calls per turn (median) |
| --- | ---: | ---: | ---: | --- |
| Plain reply | 536.5 ms | 579.1 ms | 820.0 ms | 1 decision, 2 embedding, 1 ReAct |
| Tool turn | 548.6 ms | 576.7 ms | 583.5 ms | 1 decision, 2 embedding, 2 ReAct |

- **Idle memory:** the working set of the test process, which also holds the server, was 194.3 MB after start-up and 207.6 MB after the 80 turns.
- **Calls per turn follow the fake's script**: the scripted decision probability, and whether a tool is offered. A real model may produce a different pattern.
- **What the latency measures.** The fake answers instantly, so these numbers are Parlant's own overhead plus the SDK test client's send-and-wait loop. They are not model latency. **They do not show how Klaint would perform with a real model.**
- An earlier attempt crashed in the harness's own memory-reading code, before measuring anything ([`earlier/perf1.log`](../wispral-world-class/evidence/kt01-hwa/earlier/perf1.log)). The harness was fixed.

**NOT RUN: the pinned local CPU model.** The packet asks for one, but no specific model has been authorized, and the rules forbid downloading or running unapproved weights. Measuring it needs the founder to name a model and file.

### v3.3.2 checks

- **Hooks.** v3.3.2's `EngineHooks` (`core/engines/alpha/hooks.py`) has no `on_reviewing_tool_calls` and no `on_calling_tools`; checked in the source. v4's `CompassHooks` has both. Only `on_reviewing_tool_calls` also has a `_result` form (`call_on_reviewing_tool_calls_result`); `on_calling_tools` returns a boolean.
- **Tool server.** It has the same forged-`customer_id` flaw (table above).
- **One turn on the fake: not achieved.** The turn timed out (HTTP 504). The engine finished a canned-response draft, then emitted no message within 30 s ([`earlier/v3run2.log`](../wispral-world-class/evidence/kt01-hwa/earlier/v3run2.log)). This is taken to be a gap in the v3 fake, not shown to be a v3 defect. So **the v3 BAIL behaviour was not measured.**

## Decision: v4 versus v3.3.2

**Use Parlant v4.0.2, with these Klaint-side conditions.** v3.3.2 is not a fallback for these requirements: it lacks the tool-review and tool-calling hooks, and it shares the tool-server flaw.

1. **Treat the integrated tool server as untrusted.** Do not rely on `context.customer_id`, because any local process can forge it.
   - Each tool must check the caller against a server-side session binding.
   - Alternatively, Klaint must keep Parlant's process unreachable by any untrusted local process.

   Which of these, and how, is for a later Grain to decide and prove.
2. **Run gated agents in BLOCK output mode.** In STREAM mode, BAIL on `on_message_generated` does not stop delivery.
3. **Keep the HTTP API behind its customer-token auth.** It held in this spike.
4. **Measure a real local model** once one is authorized, before any latency or capacity claim.

KT-01 cannot be marked `VERIFIED` while acceptance item 3 fails and item 4 is NOT RUN.

## Files

| Path | Content |
| --- | --- |
| [`harness/`](harness/) | Fake providers (v4 and v3), the KT-01 tests, the plugin that ports the upstream tests, and the final run script |
| [`../wispral-world-class/evidence/kt01-hwa/final/`](../wispral-world-class/evidence/kt01-hwa/final/) | The final v4 run: ported upstream tests, smoke, hooks, security, performance, and a summary of exit codes |
| [`../wispral-world-class/evidence/kt01-hwa/earlier/`](../wispral-world-class/evidence/kt01-hwa/earlier/) | The earlier runs on the first fake (empty strings), the failed first performance attempt, and the failed first port. Also the v3 runs: `v3run1.log`, where the server did not start because of a container duplicate-definition error in the first v3 fake (fixed by giving each schema its own generator class), and `v3run2.log`, the run the v3 results cite. |

Per the 000E specification, the run evidence lives under `research/wispral-world-class/evidence/kt01-hwa/`; this folder holds the harness and this report.

Local paths in the logs are replaced by `REDACTED_HOME`. Where a path was written in another form, the user name is replaced by `REDACTED_USER`. The JWT secret and admin key in the tests are synthetic, test-only values.
