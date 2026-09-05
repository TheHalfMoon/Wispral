# Circleback Product and Architecture Reference

**Status:** product / competitive / architectural reference only  
**Source class:** external product reference; not a source-code donor  
**Accessed:** 2026-09-06

## Why this reference matters

Circleback is useful to Wispral because it demonstrates a mature product pattern in which captured conversations become structured, searchable context that can be exposed to humans and AI agents through multiple interfaces.

This does **not** make Circleback a direct product template for Wispral. Wispral's founding boundary remains real-time, authority-aware voice control for coding agents. Conversation history can become context; it must never become silent execution authority.

## Publicly observed product patterns

### Conversation context is exposed as infrastructure

Circleback exposes captured meeting and related context through a public API, an authenticated remote MCP server, and a CLI.

Relevant public sources:

- `https://circleback.ai/releases/circleback-cli`
- `https://circleback.ai/releases`
- `https://support.circleback.ai/en/articles/13249081-circleback-mcp`

The MCP surface uses Streamable HTTP and OAuth and is documented for AI clients including ChatGPT, Claude, Cursor, and Codex. The CLI exposes meetings, emails, calendar events, and related context to terminal workflows and coding agents.

**Wispral lesson:** future context-provider boundaries should be agent-addressable and interface-neutral where evidence justifies them. CLI, structured protocol, and API surfaces should converge on one underlying provenance model rather than becoming separate semantic products.

### Capture can be bot-free and multimodal

Circleback's desktop application can record meetings without a meeting bot, capture system audio, and optionally capture a screen or window. Its 2026 product updates also make information shown on shared screens searchable and available to connected assistants/agents.

Relevant public sources:

- `https://circleback.ai/releases/desktop-app`
- `https://circleback.ai/releases/notes-capture-whats-shared-on-screen`
- `https://circleback.ai/releases/change-microphone-and-screen-while-recording`

**Wispral lesson:** voice interpretation may eventually benefit from explicit current-editor, terminal, window, or visual context, but multimodal capture expands privacy and authority risk. Any such context must be separately permissioned, visible, bounded, and source-attributed.

### Context can drive downstream actions

Circleback documents integrations that can search connected systems and make changes using conversation context, including work-management and CRM systems, and also allows custom MCP connectors.

Relevant public source:

- `https://circleback.ai/releases/ask-circleback-to-do-things-in-your-apps`

**Wispral lesson:** the valuable product boundary is not merely transcription or memory. The hard trust problem is the transition from remembered context to an authorized action. Wispral must keep current command intent, retrieved historical context, agent request, and policy decision as distinct provenance layers.

### Capture state is visible

Circleback's desktop product includes persistent recording-state affordances while capture is active.

Relevant public source:

- `https://circleback.ai/releases/always-visible-record-panel`

**Wispral lesson:** microphone/capture state should remain continuously inspectable. Background or ambient context collection must not become invisible product behavior.

### History portability reduces cold-start cost

Circleback supports importing prior meetings from other products so notes, transcripts, attendees, and available recordings can become searchable history.

Relevant public source:

- `https://circleback.ai/releases`

**Wispral lesson:** if persistent developer-session context is ever qualified, migration and explicit import may be preferable to proprietary lock-in. Imported history must retain source identity and must not be treated as trusted command authority merely because it exists in the context store.

## Competitive reference classification

Circleback should be classified as:

- `PRODUCT_REFERENCE`;
- `COMPETITIVE_ADJACENCY`;
- `CONVERSATION_CONTEXT_ARCHITECTURE_REFERENCE`;
- `MCP_CLI_API_SURFACE_REFERENCE`;
- `NOT_CORE_CODE_DONOR`.

No Circleback implementation material may enter Wispral without a separate exact license/provenance review.

## Patterns worth carrying into later Wispral research

1. **Conversation/session as a first-class object** — preserve source, timestamps, participant/session identity, provenance, and derived actions instead of storing an unstructured transcript blob.
2. **One context model across interfaces** — a CLI, protocol adapter, and future SDK should expose consistent semantics.
3. **Multimodal context remains source-scoped** — spoken text, repository state, terminal state, visible screen context, and imported history are different evidence classes.
4. **Visible capture state** — users must be able to determine when microphone, system-audio, or other capture is active.
5. **History is context, not authority** — retrieved prior speech can inform interpretation but cannot silently authorize a current consequential action.
6. **Retention and correction are product semantics** — persistent context must be inspectable, correctable, deletable, and bounded by explicit retention policy.
7. **Portability matters** — context should not require a mandatory proprietary Wispral cloud account or a single agent vendor.

## Explicit non-goals created by this reference

This research reference does not authorize:

- a hosted meeting recorder;
- a generic meeting-notes product;
- mandatory cloud conversation storage;
- a hosted vector-memory platform;
- CRM/project-management automation as Wispral's founding product;
- screen recording or ambient capture by default;
- using remembered speech as execution authorization;
- broad MCP server implementation before the extension boundary is justified;
- any product implementation before `specs/CURRENT.md` and the active Specification 000 frontier authorize it.

## Roadmap placement

The useful Circleback-derived patterns belong primarily in later research/refinement of:

- **H4 — Developer context engine:** evaluate bounded prior session/conversation context alongside repository context, with source provenance, recency, visibility, retention, and correction controls;
- **H11 — Wispral SDK and extension model:** evaluate context-provider interfaces and consistent CLI/protocol/API semantics only after real integrations justify an extension boundary;
- **H15 — Category expansion:** revisit broader conversation-to-agent control only after coding-agent product-market evidence exists.

These roadmap implications are intentionally coarse. They do not alter the current executable recovery frontier, do not authorize B2R03 implementation beyond its canonical specification, and do not weaken the product-code gate.
