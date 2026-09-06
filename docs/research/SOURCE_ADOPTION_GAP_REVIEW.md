# Source Adoption Gap Review

**Status:** non-executable architecture/security review  
**Prepared:** 2026-09-06  
**Reviewed against:** `docs/canonical/ARCHITECTURE_INVARIANTS.md`, `docs/security/THREAT_MODEL.md`, `docs/research/SOURCE_ADOPTION_STRATEGY.md`

## Review question

Is the external-source adoption plan safe and complete enough that a future authorized Grain can select and import donor code without rediscovering the basic architecture, provenance, security, and lifecycle constraints?

## Result

**READY AS A PLANNING SYSTEM, NOT AS PRODUCT-CODE AUTHORITY.**

The source strategy and registry are structurally aligned with Wispral's founding invariants, but this review adds hard gates that must accompany future donor imports.

## Gap G1 — Donor code must be treated as untrusted before qualification

### Risk

External setup scripts, workflows, build hooks, package scripts, test fixtures, and binaries can execute code before Wispral has decided what it trusts. A donor repository may be legitimate while a transitive dependency, generated binary, installer, or mutable download path is not.

### Required gate

Create a `SOURCE_QUARANTINE` phase before `QUALIFIED_DONOR`:

- inspect source without repository secrets;
- do not run donor CI/workflows with Wispral credentials;
- disable or separately inspect package lifecycle hooks where practical;
- pin mutable downloads before execution;
- record any network access required by build/test;
- never import donor secrets/configuration examples as live credentials;
- execute native or package bootstrap code only inside the task's bounded qualification environment.

## Gap G2 — Native/FFI donors need crash containment

### Risk

ASR, audio, VAD, denoise, hotkey, and system-capture sources may use C/C++/Objective-C/native libraries. Memory safety or ABI faults can terminate the Wispral process and break the invariant that capture, speech, policy, and agent execution remain independently cancellable.

### Required gate

For every native donor, classify the runtime boundary:

- `IN_PROCESS_SAFE_ENOUGH_FOR_JOB`, with evidence;
- `SUBPROCESS_REQUIRED`;
- `SIDECAR_REQUIRED`;
- `UNSUITABLE`.

Prefer subprocess/sidecar isolation when:

- dependency graphs conflict;
- upstream can crash/abort the host process;
- model/runtime unload is unreliable;
- GPU/native state cannot be safely cancelled;
- a platform backend has materially different ABI requirements.

A crash-isolated provider must expose explicit health, startup, shutdown, timeout, and cancellation events.

## Gap G3 — PTY donor code needs adversarial terminal tests

### Risk

PTY/process donor implementations can accidentally trust terminal prose, shell quoting, control sequences, prompt detection, or spoofed permission-like output.

### Required gate

Any PTY-derived donor must pass:

- ANSI/OSC/control-sequence fixtures;
- prompt-spoofing fixtures;
- untrusted-output versus structured-authority separation tests;
- direct argv/process API preference over shell interpolation;
- cancellation and orphan-process tests;
- bounded output/backpressure tests.

PTY text must never become high-risk authorization solely because it visually resembles a permission request.

## Gap G4 — Logging and diagnostics can become a hidden transcript database

### Risk

Copied diagnostics/logging code may retain microphone audio, raw transcripts, repository content, environment variables, command output, or credentials.

### Required gate

Every donor with logging/diagnostics must document:

- default retained fields;
- transcript/audio retention behavior;
- redaction behavior;
- maximum retention/rotation;
- support-bundle contents;
- opt-in debug content;
- deletion behavior.

Founding default remains:

- no persistent raw audio by default;
- no content telemetry;
- no transcript content in normal diagnostic logs;
- support bundles are scrubbed and inspectable before sharing.

## Gap G5 — Cancellation compatibility is a donor acceptance property

### Risk

A fast or accurate donor can still be unsuitable if it cannot stop predictably. UI silence must not be mistaken for stopped execution.

### Required gate

Provider/agent/native donors must distinguish when meaningful:

1. cancellation requested;
2. cancellation accepted/acknowledged;
3. process/operation observed stopped;
4. stale output after cancellation;
5. forced termination/fallback.

If a donor cannot expose enough state, the limitation must remain visible in compatibility metadata.

## Gap G6 — Accessibility must survive donor UX assumptions

### Risk

Voice products often make capture state or control discoverable only through overlays, tray icons, or audio feedback.

### Required gate

Every consequential donor-derived feature must expose a non-voice control path and a terminal-visible state. Graphical helpers may enhance but never replace the CLI/TUI contract during founding horizons.

## Gap G7 — Supply-chain inventory needs machine-verifiable output

### Risk

A provenance note can name the top-level repository while missing transitive packages, native binaries, model assets, download endpoints, or generated code.

### Required gate

For each adopted donor component, produce when technically possible:

- dependency lock or exact resolved dependency list;
- source archive/revision digest;
- model/data/binary digests;
- build toolchain identity;
- SBOM or equivalent dependency inventory;
- required attribution/NOTICE entries;
- network fetch list;
- reproducibility limitations.

No release claim should exceed the reproducibility evidence available for that platform.

## Gap G8 — Upstream drift and patch ownership need policy

### Risk

Copying a mechanism creates a maintenance fork. Without an ownership rule, security fixes and behavior changes can silently diverge.

### Required gate

Every `PRODUCT_ADOPTED` donor component records:

- upstream project and path;
- upstream baseline commit;
- local adaptation commit(s);
- named Wispral owner/steward or owning subsystem;
- upstream update review cadence appropriate to risk;
- known local divergence;
- deprecation/removal condition.

The project should prefer a normal dependency over a copied fork when the dependency boundary is stable, auditable, and does not weaken Wispral's contracts.

## Gap G9 — Update/distribution donors need authenticity and rollback design

### Risk

Autostart/update/packaging code expands authority beyond runtime behavior. A compromised or broken updater can replace the executable or leave stale launch entries.

### Required gate

H12 donor adoption must separately qualify:

- signed release artifacts where supported;
- update channel identity;
- rollback/recovery;
- stale executable/autostart repair;
- user-disabled autostart preservation;
- no silent channel downgrade;
- no unreviewed external installer scripts with elevated privileges.

## Gap G10 — Cloud/network behavior is a first-class donor capability

### Risk

An otherwise local donor may contain optional cloud fallback, telemetry, model download, account, sync, or remote API behavior.

### Required gate

For each donor:

- enumerate network-capable code paths;
- classify each as required, optional, disabled, or removed;
- prohibit silent fallback to a different provider;
- expose current network/provider state;
- keep credentials out of unrelated adapters;
- test offline behavior for features claimed local.

## Gap G11 — Plugin/extension mechanisms cannot arrive accidentally

### Risk

Donor applications may carry generic plugin, MCP, scripting, or provider registries that implicitly grant broad filesystem/network/process access.

### Required gate

Do not import a donor plugin system with a useful component.

Future Wispral extensions must have:

- explicit capability grants;
- least-privilege credentials;
- bounded filesystem/network/process access;
- deterministic policy outside the plugin;
- failure isolation;
- provenance and version identity.

H11 still requires repeated real integrations before a generic extension model is justified.

## Gap G12 — Benchmark instrumentation must survive donor boundaries

### Risk

A donor adapter can hide timestamps and prevent Wispral from measuring end-to-end behavior.

### Required gate

Every performance-relevant adapter must expose or allow Wispral to timestamp:

- capture activation;
- speech onset;
- speech end / turn decision;
- partial/final STT;
- entity resolution;
- dispatch;
- first agent acknowledgement/update;
- cancellation request/acknowledgement;
- TTS/local-output stop where applicable.

No donor may require benchmarking through screen recordings or manual stopwatch timing when a typed boundary can expose the event.

## Gap G13 — Donor context must remain untrusted evidence

### Risk

Graph/RAG/memory/screen/repository donors may carry prompt injection or stale context into interpretation.

### Required gate

Every context item exposed by a donor must carry:

- source class;
- source identifier/path/session;
- retrieval timestamp or revision;
- confidence/relevance metadata where applicable;
- bounded size/budget;
- clear distinction from user authority.

Untrusted repository or retrieved text cannot modify microphone, network, persistence, telemetry, or authorization policy by instruction content.

## Gap G14 — Rights records need a redistribution view, not only an access view

### Risk

Permission to inspect/use code and permission to redistribute an adapted public open-source product are not always the same operational question.

### Required gate

When separate permission is relied upon, the import record should explicitly answer:

- may Wispral modify the code?;
- may Wispral redistribute source?;
- may Wispral redistribute binaries?;
- under which license/notice terms?;
- does permission cover future upstream versions or only a specific snapshot?;
- does it cover model/data/assets or code only?;

This is a provenance requirement, not a demand to expose private legal correspondence publicly when that would be inappropriate. The canonical record may reference a controlled evidence location and state only the operative rights needed by the repository.

## Gap G15 — Source identity must be immutable at adoption time

### Risk

Names such as `Silero VAD`, `TEN VAD`, `Parakeet`, `Omnilingual ASR`, or specialized ASR families are not sufficient provenance identifiers.

### Required gate

An `IDENTITY_PIN_REQUIRED` registry entry cannot advance to `QUALIFIED_DONOR` until exact repository, commit/release, source paths, and relevant asset identities are recorded.

## Final architecture alignment

The amended plan now explicitly preserves all founding invariants relevant to external code:

- event-driven control rather than monolithic donor pipelines;
- independently cancellable audio and agent execution;
- provenance across interpretation;
- deterministic policy outside adapters;
- replaceable speech engines;
- bounded context;
- fail-closed high-risk authorization;
- explicit network boundaries;
- Rust-owned orchestration/policy;
- terminal-native first surface;
- push-to-talk before hands-free;
- non-voice accessibility;
- benchmark instrumentation as architecture.

## Readiness disposition

The external-source planning system is ready for later executable specifications because it now contains:

1. a source-adoption architecture strategy;
2. a human-readable donor registry;
3. a machine-readable source registry;
4. source-specific capture references;
5. this invariant/threat-model gap review;
6. explicit import/provenance/security gates.

What it intentionally does **not** contain is authority to import product code today. That remains owned by `specs/CURRENT.md` and the canonical roadmap.