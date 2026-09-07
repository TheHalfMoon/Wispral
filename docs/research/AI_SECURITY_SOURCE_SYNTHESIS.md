# AI Security Source Synthesis and Wispral Trust-Plane Plan

**Status:** planning / source qualification; non-executable  
**Prepared:** 2026-09-08  
**Canonical planning base:** `d1447a3a3aa9cef1490747b0a8b288e16465e95b`  
**Executable-frontier effect:** none; `specs/CURRENT.md` remains the sole execution authority

## 1. Purpose

This document studies five external security sources against Wispral's constitution, architecture invariants, threat model, and program roadmap. Its purpose is not to import another security platform into Wispral. Its purpose is to identify reusable security ideas, data models, taxonomies, interfaces, tests, and implementation material that can strengthen Wispral's later trust plane while preserving the project's core invariants:

- voice-native control plane rather than a coding agent;
- deterministic authorization around probabilistic components;
- local-first core operation;
- agent/model/vendor neutrality;
- bounded and inspectable repository context;
- explicit user authority for consequential actions;
- Rust-first product runtime;
- evidence before claims;
- progressive refinement rather than speculative implementation.

The resulting architectural direction is a **Trust Boundary Pipeline** around repository context, agent extensions, tools, providers, and actions:

`discover -> identify -> decode -> provenance-bind -> statically inspect -> optionally evaluate -> policy-classify -> authorize -> execute -> observe -> audit`

No single scanner owns this pipeline. No LLM-based security verdict may become direct execution authority.

## 2. Founder source-use authorization and repository policy

The Founder stated on 2026-09-08 that Wispral has permission to copy and adapt source code from the sources studied here.

Wispral records that statement as `FOUNDER_ASSERTED_SOURCE_USE_AUTHORIZATION` for planning purposes. It does not remove repository obligations to:

- record exact donor repository, revision, path, and material identity before adaptation;
- preserve required copyright, license, attribution, and NOTICE material;
- distinguish upstream license rights from any separate permission asserted by the Founder;
- identify third-party material nested inside a donor repository;
- prevent license obligations from silently expanding the portable core;
- document whether material is copied, adapted, translated, reimplemented from behavior, or used only as a conceptual reference;
- re-qualify donor code if the selected upstream revision changes.

External code remains ineligible for undocumented copy/paste.

## 3. Pinned source registry

| Source | Pinned revision observed | Primary license observation | Strongest Wispral use | Default disposition |
|---|---|---|---|---|
| `Tencent/AI-Infra-Guard` | `e4e622af3ad2b8228ce82dd62b01415dd8ce2b9c` | repository root Apache-2.0; component metadata/NOTICE must be checked per selected path | MCP/skill/agent threat taxonomies, deterministic pre-scan ideas, SARIF output, intent-alignment audit, adversarial fixtures | `SELECTIVE_ADAPTATION_CANDIDATE` |
| `google/magika` | `26b6a9ba7e92f2b0a3745970a9190ec0dde9bf83` | Apache-2.0 | local content-type identification, confidence-aware unknown fallback, file-extension/content mismatch handling | `OPTIONAL_RUST_BOUNDARY_CANDIDATE` |
| `Tencent/AICGSecEval` | `94428ebf45141bf4ecd365a51d596dcd51caa690` | Apache-2.0 at project level with bundled third-party notices | repository-level security evaluation methodology, static + dynamic hybrid evidence, agent adapter benchmark design, checkpointed evaluation | `METHODOLOGY_AND_FIXTURE_REFERENCE` |
| `Tencent/secguide` | `bfda087142e3bb3f5840cbc6af82c1982d1d14e4` | CC-BY-SA-4.0 | secure-coding rule/reference taxonomy for non-Rust adapters and scanner-rule design | `REFERENCE_FIRST` |
| `Tencent/TscanCode` | `3e3b6b66a7e39283d99add581fb9d54ee80c48f5` | GPL-3.0; repository also records additional component licenses | external/native-code static-analysis reference for C/C++ bridges and bundled native dependencies | `OUT_OF_PROCESS_REFERENCE_BY_DEFAULT` |

The source registry is intentionally revision-pinned. Future code adoption must pin the exact file/blob actually used rather than relying on the repository-level revision alone.

## 4. Source-derived findings

### 4.1 Tencent AI-Infra-Guard

AI-Infra-Guard is the highest-value source in this group for Wispral's future trust plane because it treats AI infrastructure, MCP servers, Agent Skills, and running agents as security targets rather than ordinary application code.

Useful source patterns include:

- MCP-specific risk classes covering token/secret exposure, scope creep, tool poisoning, supply-chain compromise, command execution, prompt injection, authorization gaps, audit gaps, shadow servers, and context over-sharing;
- supplemental identity attacks such as name confusion, rug pull, and tool shadowing;
- SkillTrustBench categories for instruction hijacking, memory poisoning, remote payload execution, embedded malicious code, privilege escalation, persistence, tool hijacking, insecure dependencies, and insecure coding;
- `agent-scan` black-box scenarios covering authorization bypass, data leakage, indirect prompt injection, tool abuse, web exfiltration, agentic supply chain, unexpected code execution, inter-agent communication, cascading failure, and human-agent trust exploitation;
- SARIF 2.1.0 as a machine-consumable security-finding interchange format;
- a fast deterministic/regex pre-scan before higher-cost probabilistic analysis;
- Skill intent-alignment checks that compare declared capability with implementation behavior;
- encoding-smuggling and bytecode-awareness work in the skill scanner;
- provider adapters for black-box security evaluation;
- explicit separation of discovery, audit, review, and report phases.

Wispral should **not** copy AI-Infra-Guard's overall architecture into the core. Its scanner agents are LLM-driven and frequently assume configured remote model endpoints. That is acceptable for an optional security-evidence provider, but it cannot own deterministic Wispral authorization or become a mandatory core dependency.

The best adaptation is therefore architectural decomposition:

1. reimplement or selectively adapt deterministic pre-scan primitives in Rust where justified;
2. normalize external scanner findings to a Wispral security-evidence contract, preferably SARIF-compatible;
3. import selected adversarial fixtures/taxonomy data with provenance when useful;
4. keep optional LLM-driven scans out-of-process and explicitly non-authoritative;
5. use declared-vs-observed capability comparison as an extension admission gate.

### 4.2 Google Magika

Magika demonstrates a local, confidence-aware content identification primitive that is directly relevant to bounded repository context. Its useful properties include:

- Rust CLI availability;
- local inference;
- content identification from bytes rather than filename extension alone;
- explicit prediction scores;
- confidence modes;
- generic/unknown fallback instead of forcing a specific type;
- bounded-content sampling rather than full-file processing;
- recursive file handling and explicit symlink dereference control.

Wispral currently treats repository context as bounded and inspectable, but the founding architecture does not yet define a strong **content identity** boundary. That leaves future context providers vulnerable to extension spoofing, parser mismatch, unexpected binaries, and text/binary confusion.

Magika therefore fits best as a future optional implementation candidate behind a generic `ContentIdentityProvider` boundary. Wispral must still define deterministic fallback rules for unknown/low-confidence classifications. A model score must never independently authorize parsing or execution.

### 4.3 Tencent AICGSecEval

AICGSecEval is most valuable as benchmark architecture rather than runtime code. The framework contributes four important patterns:

- repository-level rather than isolated-snippet evaluation;
- tasks derived from real code and vulnerability history;
- project-context extraction that simulates realistic agentic programming;
- hybrid static + dynamic assessment, including tests and vulnerability PoCs.

Its agent adapter model also reinforces a Wispral principle: the evaluation harness should abstract over independent agents rather than couple the benchmark to one vendor.

For Wispral, the correct translation is not "measure whether Wispral generates secure code" because Wispral is not the code generator. The useful benchmark question is:

> Does the Wispral control plane preserve or improve security-relevant user intent and policy boundaries when an independent agent modifies a repository?

Future WispralBench security families should therefore include repository-level tasks where the important result is not only task completion, but also:

- whether risky target/action semantics were preserved;
- whether required approval was requested;
- whether malicious repository context changed authorization behavior;
- whether unsafe generated changes were surfaced by configured evidence providers;
- whether cancellation and rollback evidence are truthful;
- whether the same policy contract survives different agent adapters.

### 4.4 Tencent secguide

`secguide` is a useful rule-design and secure-coding reference, especially for Python, JavaScript/Node, Go, Java, and C/C++ support surfaces. It is not a strong direct product-code donor for the Rust core because it does not target Rust and its documentation license is ShareAlike.

Useful patterns are:

- developer-readable security rules at API level;
- rules that can be converted into scanner policies;
- remediation-oriented guidance rather than finding-only output;
- early lifecycle / DevSecOps framing.

Wispral should use it primarily to improve rule wording, fixture design, and non-Rust adapter review criteria. Any copied/adapted documentation or rule text requires exact CC-BY-SA attribution/compatibility handling.

### 4.5 Tencent TscanCode

TscanCode is an older C/C++-centered static analyzer with extensible checks and machine-readable output. It is relevant to Wispral only at bounded native-code surfaces, for example:

- C/C++ speech libraries;
- FFI wrappers;
- vendored native utilities;
- future platform audio bridges.

It is not appropriate as a linked core dependency by default. Its GPL-3.0 licensing and older maintenance profile make an out-of-process scanner/reference boundary the safer default unless a future exact architectural and license decision selects something else.

Its strongest conceptual contribution is that native adapter risk should be independently scanned rather than receiving a security pass merely because the Rust orchestration layer is memory-safe.

## 5. Gap analysis against the current Wispral plan

The founding threat model is strong on microphone authority, STT substitution, repository false binding, command/asides, permissions, cancellation, prompt injection, cloud leakage, persistence, plugins, PTY injection, and benchmark privacy. The source study identifies additional gaps that deserve explicit future planning.

### G1. File identity and parser-selection gap

Current architecture bounds repository context but does not yet define how a context provider decides what a file actually is.

Needed future contract:

- extension, MIME/content prediction, executable bit, symlink state, size, and parser choice remain separate observations;
- content-type mismatch becomes a security signal;
- low-confidence/unknown type fails to a safer generic path;
- no executable/parser invocation solely because a filename extension suggests it.

### G2. Encoding and content-smuggling gap

Future context ingestion needs explicit defenses for:

- invalid or ambiguous text encodings;
- mojibake that changes visible instructions;
- hidden Unicode controls;
- bytecode or generated artifacts presented as source;
- polyglot/mixed-format files;
- oversized files, compressed archives, and decompression bombs;
- parser discrepancies between what the user sees and what an agent/scanner consumes.

### G3. Tool/skill identity continuity gap

The current threat model covers plugin compromise, but not the complete lifecycle of identity attacks:

- name confusion;
- same-name tool shadowing;
- post-install behavior change / rug pull;
- declared capability differing from implementation;
- extension identity changing between approval and invocation.

Future policy should bind approvals to a content/capability identity, not just a display name.

### G4. Extension admission gap

A future MCP/server/skill/plugin ecosystem needs an admission protocol before execution:

- source identity;
- version/revision/digest;
- declared capabilities;
- requested filesystem/network/process/credential scope;
- dependency provenance;
- security evidence;
- explicit user/admin policy decision;
- re-evaluation on material change.

### G5. Security finding interchange gap

Wispral currently has evidence concepts but no durable cross-scanner finding format. SARIF 2.1.0 is a strong candidate for static-analysis interchange because it preserves rules, locations, severity, fingerprints, and fixes.

Future design should distinguish:

- `SecurityObservation` — raw scanner/test evidence;
- `SecurityFinding` — normalized classified evidence;
- `PolicyDecision` — deterministic authorization result.

A scanner finding is evidence, not authority.

### G6. Dynamic agent security evaluation gap

Static repository review alone cannot prove safe agent behavior. Future qualification needs black-box dynamic fixtures for:

- indirect prompt injection;
- tool abuse;
- authorization bypass;
- data exfiltration;
- unexpected code execution;
- cross-agent/cascading failures;
- malicious tool descriptions;
- cancellation lies;
- stale approvals;
- human-agent trust exploitation.

### G7. Repository-level security benchmark gap

WispralBench currently anticipates performance, entity accuracy, turn detection, cancellation, and context metrics, but the roadmap does not yet define a repository-level security benchmark family.

A future benchmark should combine:

- deterministic policy assertions;
- static findings;
- dynamic behavior tests;
- known vulnerable fixtures;
- negative controls;
- losing results;
- agent-vendor portability;
- exact source/fixture provenance.

### G8. Supply-chain evidence gap

The plan mentions dependency provenance but does not yet specify a complete admission evidence set for native libraries, extensions, models, rulesets, and scanners.

Future evidence should be capable of carrying:

- exact source revision/blob;
- package/model artifact digest;
- lockfile identity;
- license/NOTICE identity;
- build provenance where available;
- SBOM reference where applicable;
- known-vulnerability scan evidence;
- signer/release identity where available;
- stale/revoked status.

### G9. Provider/model identity drift gap

Optional cloud STT/LLM/security providers may change implementation behind a stable API name. AI-Infra-Guard's model/API poisoning work highlights a broader issue: provider identity and behavior drift can invalidate evidence.

Wispral should eventually bind remote-provider claims to the strongest observable identity available and expose when only a mutable service alias is known.

### G10. Security-tool trust gap

A scanner can be compromised, stale, non-deterministic, or wrong. A future security pipeline therefore needs:

- multiple evidence classes;
- scanner identity/version binding;
- explicit `NOT_RUN`, `UNAVAILABLE`, `INCONCLUSIVE`, and `STALE` states;
- no `PASS` generated from absence of findings alone unless the applicable test contract defines that meaning;
- deterministic policy independent of one scanner's prose verdict.

## 6. Target architecture: Trust Boundary Pipeline

The following is a future architectural direction, not an implementation specification.

### Stage 1 — Discovery

Enumerate candidate files, tools, skills, servers, providers, and agent capabilities without granting trust.

Security properties:

- bounded traversal;
- symlink-aware behavior;
- path normalization;
- explicit exclusions and budgets;
- no execution during discovery.

### Stage 2 — Content identity

Establish content observations before parser/tool selection.

Possible evidence providers:

- extension and filesystem metadata;
- magic signatures;
- Magika-like local classifier;
- textual/binary heuristics.

Output should include confidence and `UNKNOWN`, not just a forced type.

### Stage 3 — Safe decode

Decode text or metadata under bounded rules.

Security properties:

- byte limits;
- encoding provenance;
- control-character checks;
- suspicious Unicode/charset-smuggling signals;
- raw-byte digest retained separately from decoded representation.

### Stage 4 — Provenance binding

Create a stable identity for the object being considered:

- origin;
- revision/version;
- digest;
- declared capability metadata;
- dependency/notice metadata;
- acquisition time;
- mutable-alias warning where applicable.

### Stage 5 — Deterministic pre-scan

Use bounded deterministic checks for high-signal patterns before any optional probabilistic security analysis.

Potential initial families adapted from AI-Infra-Guard concepts:

- remote-download-and-execute;
- cloud metadata access;
- credential-file access;
- encoded execution;
- sensitive-data exfiltration;
- persistence mechanisms;
- SSH/key modification;
- prompt-injection markers;
- tool definition mutation;
- extension configuration/credential harvesting.

Regex alone is not proof of vulnerability; findings are evidence requiring classification.

### Stage 6 — Optional security evidence providers

Support external or local scanners behind a provider boundary. Examples may include:

- SARIF-producing static scanners;
- MCP/skill scanners;
- native-code analyzers;
- dependency scanners;
- optional LLM-assisted reviewers;
- dynamic black-box harnesses.

These providers may influence risk classification but cannot directly authorize an action.

### Stage 7 — Capability and risk classification

Deterministically normalize:

- declared capabilities;
- observed behaviors;
- security findings;
- requested action;
- target sensitivity;
- user policy.

Capability mismatch itself is a security event.

### Stage 8 — Authorization

Authorization remains a Wispral-owned deterministic decision bound to exact request and object identities.

Changing tool/skill/server/provider identity invalidates prior approval where material.

### Stage 9 — Execution containment

Future execution contracts should consider least privilege for:

- filesystem;
- network;
- process spawning;
- environment/credentials;
- repository writes;
- external/public effects.

The exact sandbox technology is deliberately not selected here.

### Stage 10 — Observation and audit

Record sufficient typed evidence to reconstruct:

- what object/capability was admitted;
- what was scanned and by which exact tool;
- what policy evaluated;
- what approval was granted;
- what actually executed;
- whether cancellation was acknowledged and observed;
- what identity changed afterward.

## 7. Proposed Wispral security taxonomy additions

The following future taxonomy supplements rather than replaces the founding threat model.

| ID | Threat family | Source influence |
|---|---|---|
| `T13` | Content-type confusion / parser mismatch | Magika |
| `T14` | Encoding, bytecode, Unicode, or content smuggling | AI-Infra-Guard skill-scan + Magika |
| `T15` | Tool/skill name confusion, shadowing, poisoning, or rug pull | AI-Infra-Guard MCP/Skill taxonomies |
| `T16` | Extension/dependency/supply-chain substitution | AI-Infra-Guard + TscanCode/secure-code review principles |
| `T17` | Context over-sharing and cross-session leakage | AI-Infra-Guard MCP taxonomy |
| `T18` | Provider/model endpoint substitution or material behavior drift | AI-Infra-Guard API/model integrity work |
| `T19` | Security scanner false assurance or compromised evidence provider | synthesis gap |
| `T20` | Agent-generated security regression hidden by task success | AICGSecEval hybrid methodology |

These IDs are planning candidates until the threat model change is canonical.

## 8. Roadmap integration

### H0 — Founding research and qualification

Add source qualification and security-architecture research sufficient to define later trust boundaries, without implementing a general scanner platform during H0.

### H4 — Developer context engine

Add a future `safe repository ingestion` research requirement:

- content identity;
- symlink/path rules;
- size/encoding budgets;
- provenance-preserving decoding;
- parser selection independent of filename trust;
- prompt-injection/content-smuggling fixtures.

### H7 — Permission and trust plane

This becomes the primary future home of the Trust Boundary Pipeline:

- extension/tool capability manifests;
- exact-identity-bound approvals;
- declared-vs-observed behavior checks;
- scanner-evidence ingestion;
- policy handling for shadowing/rug-pull/supply-chain events;
- fail-closed semantics for stale or changed identities.

### H11 — SDK and extension model

Any future extension system must include a security admission contract. A generic plugin API is still not authorized merely because scanners exist.

### H12 — Cross-platform hardening and distribution

Add future release-supply-chain evidence such as lockfile verification, SBOM/provenance/signature support where applicable, dependency review, and native bridge scanning.

### H13 — Public WispralBench

Add a security benchmark family inspired by AICGSecEval's repository-level and hybrid static/dynamic approach, but adapted to Wispral's control-plane responsibility.

### H14 — v1 trust and compatibility contract

Require documented security-evidence boundaries, extension identity behavior, provider drift handling, and residual risks before stable trust claims.

## 9. Candidate future research grains

These are **not authorized tasks**. They are candidate units that may be selected later only when `specs/CURRENT.md` advances to the relevant horizon.

### SEC-R01 — Repository content identity study

Compare deterministic magic/metadata approaches with a pinned Magika Rust path on a bounded fixture set including source, config, binary, archive, symlink, extension-spoofed, empty, and ambiguous files.

Expected evidence:

- exact classifier/source identity;
- correctness on frozen fixtures;
- unknown/low-confidence behavior;
- CPU/memory/latency measurements;
- failure behavior;
- license/provenance record.

### SEC-R02 — Safe text decoding and smuggling fixtures

Build frozen fixtures for UTF variants, malformed encodings, suspicious controls, mojibake, bytecode, mixed binary/text, and oversized input. Compare a minimal Rust implementation with selectively adapted ideas from AI-Infra-Guard's bounded text decoding.

### SEC-R03 — Deterministic repository pre-scan

Evaluate a small Rust rule engine on high-signal patterns with explicit false-positive/false-negative accounting. Output normalized findings, not policy decisions.

### SEC-R04 — Extension capability manifest

Define a data contract for tool/skill/server identity, declared capabilities, requested privileges, provenance, and change detection. Include name-confusion, shadowing, and rug-pull fixtures.

### SEC-R05 — SARIF evidence adapter

Test whether SARIF 2.1.0 is sufficient for importing external static findings without collapsing them into authorization. Preserve tool identity and raw report digest.

### SEC-R06 — Dynamic agent red-team harness

Adapt provider-agnostic black-box patterns from AI-Infra-Guard Agent-Scan and AICGSecEval agent adapters. Use synthetic local target agents first. No production service testing is implied.

### SEC-R07 — Repository-level control-plane security benchmark

Create task fixtures where independent coding agents face vulnerable or malicious repository context. Measure policy, approval, cancellation, provenance, and security-evidence behavior separately from agent coding success.

### SEC-R08 — Supply-chain admission evidence

Define exact evidence fields for source revision, artifact digest, license/NOTICE, dependency lock, SBOM/signature/provenance when available, vulnerability status, and staleness.

### SEC-R09 — Native dependency scan boundary

Evaluate out-of-process C/C++ scanning for selected native speech/FFI surfaces. TscanCode may be one historical reference; current alternatives must be compared before selection.

### SEC-R10 — Security provider disagreement protocol

Define behavior when scanners disagree, fail, are unavailable, or produce probabilistic findings. The required result is a deterministic policy input model with explicit uncertainty—not a majority-vote authorization mechanism.

## 10. Adoption decisions by source

### AI-Infra-Guard

**Adopt now at planning level:**

- MCP and Skill threat taxonomy concepts;
- agent red-team categories;
- SARIF interchange pattern;
- deterministic pre-scan pattern;
- declared-vs-implemented intent alignment;
- charset/bytecode smuggling awareness.

**Do not adopt now:**

- mandatory remote LLM security scanning;
- AIG web platform/backend;
- model-specific configuration as a Wispral core requirement;
- scanner security score as authorization authority.

**Potential future code adaptation:** selected utility/rule/formatter logic after exact path/blob/license/NOTICE review.

### Magika

**Adopt now at planning level:** confidence-aware content identity and unknown fallback.

**Potential future code/dependency adoption:** Rust classifier path behind an optional content-identity provider only after SEC-R01 evidence.

**Do not treat:** classification confidence as execution authority.

### AICGSecEval

**Adopt now at planning level:** repository-level, agent-aware, hybrid static/dynamic security evaluation methodology.

**Potential future adaptation:** harness abstractions, checkpointing ideas, fixture schemas, and evaluation workflow patterns after exact provenance review.

**Do not import wholesale:** large benchmark dataset or heavyweight Docker/Python stack into the Wispral runtime.

### secguide

**Adopt now at planning level:** secure-rule organization and remediation framing.

**Default code/content posture:** reference-first because the material is CC-BY-SA-4.0 and does not target Rust core code.

### TscanCode

**Adopt now at planning level:** native-code analyzer boundary and extensible-check concept.

**Default runtime posture:** external/out-of-process only. Do not link or copy GPL implementation into the portable core without a dedicated compatibility decision, even though Founder source-use authorization is recorded.

## 11. Additional gaps not solved by these sources

The five sources materially improve the plan but do not solve several Wispral-specific risks:

- acoustic/voice-origin authentication;
- speaker/ambient authority distinction;
- STT negation preservation;
- interruption semantics;
- exact ACP permission identity;
- PTY escape-sequence hardening;
- secrets in spoken transcripts;
- operating-system microphone permission behavior;
- Rust-specific secure coding and unsafe/FFI review;
- sandbox selection and containment guarantees;
- cryptographic release signing strategy;
- enterprise policy distribution;
- privacy-preserving telemetry design;
- accessibility tradeoffs in security confirmation;
- benchmark leakage caused by security fixtures becoming public training data.

These remain separate research requirements. The new sources should not create a false impression that security is "covered."

## 12. Planning acceptance criteria

This source synthesis is successful when the repository preserves all of the following:

1. the current executable specification frontier is unchanged;
2. the five sources are revision-pinned and dispositioned;
3. copying permission is recorded without erasing license/provenance duties;
4. deterministic policy remains separate from probabilistic security scanners;
5. local-first core operation remains possible;
6. no generic plugin/MCP platform is prematurely authorized;
7. the threat model includes the newly identified trust classes;
8. the roadmap places future security work in the correct horizons;
9. future code adoption requires exact path/blob/license/NOTICE provenance;
10. security claims remain evidence-bearing and fail closed on unavailable or inconclusive checks.

## 13. Current-frontier non-interference

This document does not authorize product code, a scanner dependency, an MCP server, a plugin system, B2R11, B2R12, scoring, or any benchmark rerun.

The B2R10 PR #88 was closed without merge after substantive review exposed a sherpa-onnx transcript extraction defect that also affects canonical B2R09 evidence. That recovery matter must follow the existing attempt-invalidation rule independently. This security-source planning work must not be used to bypass, rewrite, or broaden that recovery authority.
