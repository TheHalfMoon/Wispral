# Wispral Program Roadmap

**Status:** Founding candidate  
**Planning model:** progressive refinement; only the active frontier may be decomposed to execution-level tasks

## Mission

Make voice a trustworthy, low-friction control surface for independent AI coding agents.

A successful Wispral experience should eventually let a developer:

- start or attach to an agent session;
- speak developer-specific instructions naturally;
- resolve paths, symbols, flags, packages, branches, and tests against repository context;
- think aloud without accidentally authorizing action;
- interrupt and redirect an active agent immediately;
- inspect what Wispral heard and how it interpreted it;
- approve or deny consequential operations through explicit risk-aware policy;
- use multiple independent agents without relearning the voice interface;
- choose a local speech path without requiring a Wispral account;
- fall back to keyboard/text controls at any time.

## Program north stars

Engineering north stars are measured independently from adoption ambitions.

### Experience north star

`fresh install -> first successful spoken agent instruction`

The long-term product target is less than 60 seconds on a supported clean environment. No threshold becomes a public claim until measured by a reproducible install benchmark.

### Control north star

A deliberate interrupt must feel immediate and must stop further agent/audible progress before a user reasonably perceives the system as ignoring them.

Specific latency thresholds are benchmark targets, not founding claims.

### Trust north star

For every consequential action, the user must be able to determine:

- what Wispral heard;
- what Wispral resolved;
- what Wispral interpreted;
- what the agent requested;
- what object/tool/provider identity was involved where material;
- what security evidence was considered where configured;
- what policy authorized or denied.

Security tools, classifiers, and model-generated reviews are evidence providers. They do not replace deterministic Wispral authorization.

### Interoperability north star

The core interaction model must survive changes in agent vendor, model vendor, speech backend, and optional security-evidence provider.

## Cross-cutting trust-boundary direction

Future context, extension, and security work should converge on one provenance-preserving trust pipeline rather than independent scanner-specific control paths:

`discover -> identify -> decode -> provenance-bind -> statically-inspect -> optionally-evaluate -> policy-classify -> authorize -> execute -> observe -> audit`

This is a directional architecture, not an implementation specification. Individual stages may be omitted when they are irrelevant to a bounded operation, but skipping a stage must not silently fabricate its evidence.

Core rules:

- content identity, scanner output, LLM review, and provider confidence are evidence rather than direct authority;
- deterministic policy owns consequential authorization;
- local-first core use must remain possible without a hosted security service;
- tool/skill/server/provider identity must be capable of invalidating stale approval when material identity or capability changes;
- exact code/dependency adoption requires provenance and license/NOTICE qualification;
- security-provider failure must remain visible as failure/unavailability/inconclusive evidence rather than an implicit pass.

## Horizon model

A horizon describes durable direction and entry conditions. It does not authorize implementation by itself.

### H0 — Founding research and qualification

**Purpose:** replace architecture assumptions with reproducible evidence and establish governance.

Research surfaces include:

- ACP lifecycle, permissions, streaming, cancellation, authentication, and Rust SDK behavior;
- actual ACP behavior of representative coding agents;
- PTY fallback requirements;
- local streaming STT bakeoff;
- developer entity recognition methodology;
- turn detection and pause behavior;
- interruption instrumentation;
- microphone/privacy threat model;
- dependency/license/provenance review;
- AI-agent/MCP/extension security source qualification sufficient to shape later trust-boundary research without prematurely importing a scanner platform;
- file/content identity and safe repository-ingestion hypotheses where evidence shows they are prerequisites to later context work;
- security-evidence interchange and repository-level security-benchmark hypotheses where they can be studied without opening product authority;
- macOS/Linux/Windows feasibility boundaries;
- brand/legal namespace risks sufficient for an open-source engineering decision.

**Exit:** evidence selects the first bounded product Grain. No broad architecture, scanner, security taxonomy, or dependency is considered proven merely by completing H0.

### H1 — Minimal Rust voice runtime

**Purpose:** establish the smallest reliable terminal-native capture/control skeleton selected by H0.

Expected capability class:

- Rust CLI/runtime;
- explicit microphone state;
- push-to-talk baseline;
- one selected STT path behind a replaceable boundary;
- typed event instrumentation;
- no agent mutation beyond the exact first integration contract.

**Entry:** H0 evidence selects concrete dependencies and one narrow runtime slice.

### H2 — First structured agent control

**Purpose:** prove that speech can drive a real independent coding agent through a structured lifecycle without collapsing Wispral into vendor-specific UI scraping.

Expected capability class:

- create/attach a session where supported;
- dispatch one spoken instruction;
- render agent updates;
- cancel an active request;
- preserve raw/interpreted provenance.

**Entry:** exact agent and protocol semantics are experimentally qualified.

### H3 — Independent second-agent portability

**Purpose:** prove the product contract is not accidentally one-agent architecture.

A second materially independent agent must exercise the same core interaction model with adapter-specific differences isolated.

**Entry:** H2 is verified and portability gaps are known.

### H4 — Developer context engine

**Purpose:** improve technical speech interpretation using bounded repository context and, only if later evidence justifies it, explicitly sourced prior session/conversation context.

Expected capability class:

- file/path candidate resolution;
- symbol/package/flag vocabulary support;
- visible confidence and ambiguity;
- context budgets;
- deterministic fallback when no safe binding exists;
- safe repository-ingestion boundaries that can distinguish filesystem metadata, symlink state, content identity, decoded representation, and parser choice;
- content-type mismatch, unknown/low-confidence file identity, malformed encoding, suspicious Unicode/control content, bytecode/generated artifacts, mixed text/binary content, and oversized/archive inputs handled through explicit bounded behavior where those classes are supported;
- raw-byte/content provenance preserved separately from derived text used for interpretation;
- source-scoped prior session/conversation retrieval with timestamps and provenance when separately qualified;
- inspectable correction, deletion, recency, and retention boundaries for any persistent context;
- an explicit rule that retrieved history may inform interpretation but does not silently authorize a current consequential action.

A local content classifier such as a pinned Magika Rust path may be evaluated as an optional `ContentIdentityProvider`; no classifier score may directly authorize parsing, execution, or repository mutation.

**Entry:** WispralBench demonstrates a measurable baseline and a reproducible context-resolution hypothesis. Persistent conversation/session context requires separate evidence for utility, privacy, retention, correction, and authority safety before becoming an implementation requirement. Safe-ingestion implementation requires separate evidence that the additional classifier/parser boundary improves security or correctness without compromising local-first portability.

### H5 — Command / Aside semantics

**Purpose:** let users separate actionable instructions from tentative reasoning/context.

The exact control mechanism is deliberately not preselected.

**Entry:** research and user fixtures define failure cases, authority risks, and measurable acceptance criteria.

### H6 — Interruption and steering

**Purpose:** make barge-in a product primitive rather than a stop button layered on top.

Expected capability class:

- speech-onset observation during agent activity;
- immediate local output suppression where applicable;
- structured cancellation when supported;
- continuation with new instruction and preserved session context;
- explicit failure mode when an underlying agent cannot cancel safely.

**Entry:** instrumentation can measure the complete cancellation path.

### H7 — Permission and trust plane

**Purpose:** apply deterministic risk-aware authorization to structured agent requests and Wispral-originated actions, while admitting repository objects, tools, extensions, and optional security evidence through explicit trust boundaries.

Expected risk classes include read-only, reversible local writes, consequential repository/external writes, destructive/security-sensitive operations, and spending/publication actions.

Expected trust-plane capability class may include, when independently justified:

- exact request identity and normalized action summaries;
- exact tool/skill/server/provider identity where material;
- declared capability and requested privilege manifests;
- filesystem/network/process/credential scope modeling;
- declared-versus-observed capability mismatch evidence;
- name-confusion, tool-shadowing, tool-poisoning, and post-admission behavior-drift handling;
- extension/dependency/model/ruleset provenance sufficient to detect material substitution;
- security observations/findings from bounded evidence providers;
- a scanner/evaluator normalization layer that keeps evidence distinct from `PolicyDecision`;
- fail-closed behavior for stale identity, unknown capability, malformed evidence, or policy-engine failure;
- explicit `NOT_RUN`, `UNAVAILABLE`, `INCONCLUSIVE`, and `STALE` states where applicable;
- re-authorization when a previously approved identity or capability materially changes.

SARIF 2.1.0 is a candidate external static-finding interchange because it can preserve rule identity, locations, severity, fingerprints, and remediation. Its use is not preselected until a bounded study proves it fits Wispral's evidence model.

Optional LLM-driven MCP/Skill/agent scanners may contribute evidence after qualification, but they must not become mandatory core infrastructure or direct sources of authorization.

**Entry:** threat model and agent permission semantics are verified, and any extension/security-evidence boundary selected for implementation has separate provenance, failure, local-first, portability, and policy-isolation evidence.

### H8 — Compatibility expansion

**Purpose:** broaden support without weakening the portable core.

Candidate integrations may include Codex, Claude Code, Gemini CLI, OpenCode, Goose, GitHub Copilot CLI, Cursor, Aider, and future ACP agents. Inclusion depends on current protocol/runtime evidence, licensing, maintainability, and any trust-plane capability/identity contract established by earlier horizons.

**Entry:** two-agent portability contract is verified.

### H9 — Hands-free capture and semantic turn taking

**Purpose:** move beyond push-to-talk while preserving explicit microphone state and interruption safety.

Candidate research includes VAD, semantic endpointing, wake modes, configurable pause tolerance, and accessibility behavior.

**Entry:** push-to-talk is reliable and benchmark instrumentation distinguishes speech start, pause, end-of-turn, and false endpointing.

### H10 — Selective voice output and duplex control

**Purpose:** add spoken system/agent feedback where voice is useful without reading the terminal aloud.

Candidate capability class:

- concise spoken status and questions;
- interruptible TTS;
- half-duplex baseline;
- optional full-duplex/AEC only after separate qualification.

**Entry:** audio output cannot compromise capture, privacy, or cancellation semantics.

### H11 — Wispral SDK and extension model

**Purpose:** make the control plane reusable beyond the first CLI surface.

Potential extension boundaries include agents, speech engines, context providers, policy providers, security-evidence providers, TTS, and UI clients.

If repeated evidence eventually justifies a context-provider boundary, it should preserve one provenance/authority model across local providers and external interfaces. CLI, structured-protocol/MCP, and future API/SDK access should be evaluated as interoperable surfaces over the same semantics rather than as independent sources of authority.

Any future extension admission model must be capable of carrying exact source/version/digest identity, declared capabilities, requested privilege scope, dependency/provenance information, security evidence, and material-change detection. A display name alone is not sufficient identity for consequential authorization.

External conversation-context products and external scanner platforms are references or optional future integration candidates, not mandatory Wispral infrastructure. No hosted memory dependency, remote MCP server, remote scanner, or generic plugin system is authorized by this roadmap note.

**Entry:** real repeated integrations justify extension points. No plugin system is authorized solely for architectural elegance, and no security provider is admitted solely because it emits a score or supports a popular protocol.

### H12 — Cross-platform hardening and distribution

**Purpose:** make installation and updates boring on supported platforms while maintaining independently inspectable supply-chain evidence.

Potential surfaces include Cargo, Homebrew, shell installer, signed binaries, package manager channels, completion scripts, diagnostics, upgrade compatibility, dependency lock verification, SBOM/provenance records where justified, release/signature verification where available, vulnerability/dependency review, and bounded native/FFI security scanning.

Native code does not inherit a security claim from the surrounding Rust runtime. Out-of-process analyzers may be evaluated for native dependencies when they provide useful evidence without contaminating the portable core's licensing or runtime boundary.

**Entry:** platform support claims are backed by native CI and, where hardware is required, explicit qualification evidence. Supply-chain claims require exact artifact/source identities and reproducible or independently verifiable evidence appropriate to the claim.

### H13 — Public WispralBench

**Purpose:** publish a reproducible benchmark suite useful to the wider voice-agent ecosystem.

Benchmark families may include developer entity accuracy, turn detection, end-to-end latency, cancellation, context resolution, CPU/memory, offline behavior, cross-platform variance, and repository-level control-plane security.

A future security family may borrow the repository-level and hybrid static/dynamic evaluation pattern demonstrated by security benchmarks such as AICGSecEval, but must adapt the measured responsibility to Wispral rather than pretending Wispral is the code-generating agent. Candidate security outcomes include:

- preservation of security-relevant user intent and negation;
- correct risk/approval behavior;
- resilience to malicious repository or tool context;
- exact-identity authorization behavior;
- cancellation/recovery truthfulness;
- optional static/dynamic security-evidence handling;
- agent-vendor portability of the same policy contract;
- functional task success reported separately from security-regression evidence.

Known vulnerable fixtures, negative controls, failed runs, provider disagreement, and losing results must remain visible where material.

**Entry:** methodology has survived internal use without benchmark leakage or claim inflation. Security benchmark entry additionally requires an explicit threat mapping, frozen fixtures, exact agent/provider/scanner identities, scoring semantics, and a plan for public-fixture training-data leakage risk.

### H14 — v1 trust and compatibility contract

**Purpose:** establish a stable product surface with documented compatibility, migration, security, privacy, accessibility, and support boundaries.

Before strong v1 trust claims, the stable contract should document, where applicable:

- request and approval binding;
- extension/tool/provider identity and change behavior;
- repository content-ingestion boundaries;
- security-evidence provider scope and failure states;
- remote provider/model identity limitations;
- supply-chain provenance and update behavior;
- residual risks and unsupported threat classes;
- privacy, accessibility, and recovery semantics.

**Entry:** the project has enough real use and evidence to know what deserves stability, and all security claims are tied to reproducible evidence rather than architectural intent or scanner branding.

### H15 — Category expansion

**Purpose:** evaluate whether the proven control plane should extend beyond coding agents to broader agentic software, including whether conversation/session context can support safe cross-application control without turning Wispral into a generic meeting-notes or business-automation product.

**Entry:** coding-agent product-market evidence exists. This horizon must not distract from establishing the core category.

## External product-reference planning note

`docs/research/CIRCLEBACK_REFERENCE.md` records Circleback as a conversation-context / MCP / CLI / API product reference. The useful lesson is the pattern `capture -> structured context -> agent access -> downstream action`, especially the need to keep source provenance, capture visibility, retention/correction, and execution authority separate.

This reference does not authorize a hosted meeting recorder, mandatory cloud memory, generic business automation, screen capture by default, MCP implementation, or any change to the active executable specification frontier.

## External AI-security source planning note

`docs/research/AI_SECURITY_SOURCE_SYNTHESIS.md` and `docs/research/AI_SECURITY_SOURCE_REGISTRY.json` record the current pinned study of:

- `Tencent/AI-Infra-Guard`;
- `google/magika`;
- `Tencent/AICGSecEval`;
- `Tencent/secguide`;
- `Tencent/TscanCode`.

The study selects architectural patterns rather than a wholesale donor platform. Useful directions include MCP/Skill/agent threat taxonomies, confidence-aware file content identity, bounded decoding/smuggling defenses, SARIF-based finding interchange, repository-level hybrid security evaluation, secure-coding rule design, and out-of-process native-code scanning.

Founder-asserted source-use authorization is recorded in the source synthesis/registry. It does not erase exact source-path/blob/license/NOTICE provenance requirements or make every donor dependency appropriate for the Rust/local-first core.

This planning note does not authorize product code, a scanner service, a generic plugin system, an MCP server, any current benchmark execution, or any change to `specs/CURRENT.md`. Future source-code adaptation requires a separately authorized Grain with exact donor provenance and acceptance evidence.

## Adoption ambition

Wispral is intentionally designed for category-scale open-source adoption. Desired external outcomes include:

- GitHub Trending leadership;
- major developer-community launches;
- a contributor ecosystem around agents/speech/context;
- reference-quality benchmark usage;
- 10k, 25k, 50k, 100k, and ultimately 200k+ GitHub stars if product utility earns them;
- credible contention for high-profile repository-of-the-month/year recognition.

These are strategic ambitions, not engineering acceptance gates.

## Anti-roadmap

The following are explicitly not justified by the founding thesis and require separate evidence before entering the roadmap:

- a Wispral foundation model;
- a custom coding agent replacing existing agents;
- an Electron IDE;
- a multi-agent office/fleet visualizer;
- avatars or animated agent personas;
- a proprietary cloud account requirement;
- a hosted vector-memory platform;
- a generic project-management suite;
- a social network;
- mobile clients before the terminal control plane is proven;
- enterprise dashboards before core user value is established;
- a mandatory hosted security scanner;
- an LLM-based security verdict as direct execution authority;
- a generic plugin marketplace before an extension trust/admission contract is justified.

## Refinement rule

Only `specs/CURRENT.md` may authorize the next executable specification. H1 through H15 stay coarse until fresh evidence and completed dependencies make detailed refinement useful.

A roadmap horizon is not a task list. The security research grains listed in `docs/research/AI_SECURITY_SOURCE_SYNTHESIS.md` are candidate future refinements, not authorized execution units.