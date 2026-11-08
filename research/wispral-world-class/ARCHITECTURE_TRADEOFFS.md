# Architecture trade-offs

**Status:** CANDIDATE analysis behind the [decision ledger](DECISION_LEDGER.md). Costs are engineering estimates, never measurements.

## T-1 Fork versus extract (WisprSide, WisprStudio)

| Criterion | Fork the donor app | Extract modules into a new shell |
| --- | --- | --- |
| Reused tests | Handy: 368 Rust test definitions; VoiceStudio: 869 Python + 753 Electron test files (counts) | Lost with the surrounding integration |
| UI, installer, updater, settings, tray | Inherited | Rebuilt |
| Upstream sync | Rebase cost grows with deltas; VoiceStudio moves ~118 commits/day → scheduled windows | Manual porting of every upstream fix |
| Unsafe behaviour inherited | Yes (egress defaults, exec hooks, no consent checks, wrong-target paste) — must be removed as deltas | Only what is copied |
| Verdict | **Fork**, with a delta register and baseline-first rule | Fallback only if a baseline fails |

## T-2 Central runtime versus contracts

A daemon would own lifecycles that donors already own (Handy supervisor, VoiceStudio subprocess backend, Klaint host), add an IPC hop and an authentication surface, and force co-installation. Contracts plus fixtures deliver the shared semantics without a process. **Chosen: contracts.** Revisit only if two products must share a live resource (for example a GPU) on one machine and measured contention exists.

## T-3 Klaint tenancy: process per tenant versus shared service

| | Process per tenant | Shared service |
| --- | --- | --- |
| Isolation proof | Structural (separate process, store, secrets, port) | Must be proven in every query, cache and hook; Parlant v4 has no tenant concept |
| Cost | Memory per tenant (measured in KT-01) | Lower memory |
| Verdict | **First release** | Only after isolation fixtures pass on a shared deployment and memory cost justifies it |

## T-4 Parlant v4 versus v3.3.2

| | v4.0.2 | v3.3.2 |
| --- | --- | --- |
| Strict approved responses | Removed; commitment guard via `on_message_generated` BAIL (non-streamed only) | `CANNED_STRICT` present |
| Journeys / evaluations | Removed (policies as text; external harness) | Present |
| Future maintenance | Active line | Last 3.x release (2026-04-28) |
| Verdict | **Preferred if KT-01 confirms hook semantics** | Fallback |

## T-5 Python port versus PyO3 binding for policy in Klaint

~80 lines of lattice logic do not justify a Rust toolchain and wheel matrix in a Python service. **Port, gated by identical fixture verdicts**; switch to PyO3 abi3 if two consecutive contract majors need non-trivial port changes.

## T-6 Text insertion method on Windows

| Method | Strength | Weakness |
| --- | --- | --- |
| `SendInput` Unicode | No clipboard use | Silent UIPI failure; per-character cost; surrogate handling |
| Clipboard paste with history-exclusion formats | Fast for long text; Handy has a receipt transaction | Clipboard monitors can read delayed-render data |
| UI Automation `ValuePattern` | Confirmable read-back where supported | Many apps lack it; not a general writer |
| **Chosen** | Clipboard transaction for long text, `SendInput` for short text, UIA as sensor/read-back, all behind the fail-closed target verdict | — |

## T-7 Arabic TTS route

Commercially plausible open Arabic TTS is thin (Chatterbox Multilingual V3 retired upstream; `silma-tts` lineage unverified; Piper voices per-voice licenses). **Chosen:** wrap Chatterbox Multilingual as a frozen artifact, evaluate the others, and treat the gap as fine-tune trigger FT-5 rather than adopting non-commercial weights.
