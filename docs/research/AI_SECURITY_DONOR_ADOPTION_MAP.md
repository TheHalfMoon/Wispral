# AI Security Donor Adoption Map

**Status:** planning-only donor map; no implementation authority  
**Prepared:** 2026-09-08  
**Parent synthesis:** `docs/research/AI_SECURITY_SOURCE_SYNTHESIS.md`  
**Machine registry:** `docs/research/AI_SECURITY_SOURCE_REGISTRY.json`

## Purpose

The Founder has asserted permission for Wispral to copy and adapt code from the studied sources. This map turns that broad permission into a disciplined donor strategy: exact material is considered only where it improves a defined Wispral boundary, and every later adoption must preserve source identity, license/NOTICE obligations, tests, and independent qualification.

This file does not authorize copying now. It records the strongest observed candidate paths so a future authorized Grain does not begin with an unbounded donor sweep.

## Adoption modes

- `DIRECT_ADAPT_CANDIDATE` — implementation material may be worth copying/adapting after an exact license/NOTICE/blob review.
- `DEPENDENCY_CANDIDATE` — prefer the donor's maintained library/crate boundary over copying internals if qualification supports it.
- `BEHAVIORAL_REIMPLEMENTATION_CANDIDATE` — the idea is useful, but Wispral should normally implement its own Rust-first equivalent from a documented behavioral contract.
- `FIXTURE_OR_TAXONOMY_CANDIDATE` — data/rules/fixtures may be useful with provenance; they are not core runtime code.
- `REFERENCE_ONLY_BY_DEFAULT` — useful for architecture or review criteria; direct copying is not the default.
- `OUT_OF_PROCESS_ONLY_BY_DEFAULT` — useful as an external tool boundary; do not link it into the portable core without a separate license/architecture decision.

## Tencent/AI-Infra-Guard

Pinned repository revision: `e4e622af3ad2b8228ce82dd62b01415dd8ce2b9c`.

### Deterministic pre-scan

Source:

- path: `mcp-scan/mcp_scan/utils/pre_scan.py`
- observed blob: `eae2990e004b8f0fac9244dd912615293a91527f`
- mode: `BEHAVIORAL_REIMPLEMENTATION_CANDIDATE` with selective direct adaptation allowed if a future Grain proves it is better than a clean Rust implementation.

Useful behavior:

- bounded traversal;
- skip rules;
- maximum file size;
- high-signal patterns for remote-download-and-execute, metadata access, credential paths, prompt injection, reverse shells, encoded execution/exfiltration, persistence, SSH key writes, executable downloads, tool poisoning, and MCP credential access;
- evidence includes file and line context.

Wispral adaptation rule:

- implement as typed findings rather than concatenated prompt text;
- use byte/content identity and safe decoding before regex inspection;
- rule hits remain evidence, not authorization;
- compile/configure rules independently of LLM prompts;
- benchmark false positives/negatives on frozen fixtures before product use.

### Bounded text decoding

Source:

- path: `skill-scan/skill_scan/utils/text_decoder.py`
- observed blob: `d01135924522f74087c9412e49a21a34574a4781`
- mode: `BEHAVIORAL_REIMPLEMENTATION_CANDIDATE`.

Useful behavior:

- byte-size bound;
- UTF-8-first decoding;
- encoding confidence/fallback handling;
- rejection of binary/control-heavy content;
- explicit mojibake recovery metadata.

Wispral adaptation rule:

- Rust-first implementation;
- preserve raw-byte digest and selected decode path;
- add Unicode bidi/control, archive, bytecode, and parser-differential fixtures not covered by the observed donor file;
- avoid `errors=ignore` behavior in security-sensitive ingestion.

### SARIF formatting

Source:

- path: `mcp-scan/mcp_scan/utils/sarif_formatter.py`
- observed content includes SARIF 2.1.0 rule metadata, severity normalization, locations, fingerprints, and fixes;
- mode: `BEHAVIORAL_REIMPLEMENTATION_CANDIDATE`.

Useful behavior:

- stable finding interchange;
- deterministic fingerprints;
- full rule metadata even when a scan has no findings;
- file/line localization.

Wispral adaptation rule:

- define a native internal `SecurityObservation`/`SecurityFinding` schema first;
- treat SARIF as an import/export adapter, not the canonical policy schema;
- bind imported reports to scanner identity, configuration, and raw report digest;
- preserve unsupported fields rather than silently dropping security-relevant evidence.

### MCP/Skill risk taxonomies

Sources:

- `mcp-scan/README.md` — MCP01-MCP10 plus Name Confusion, Rug Pull, Tool Shadowing;
- `skill-scan/README.md` — SkillTrustBench T01-T09;
- mode: `FIXTURE_OR_TAXONOMY_CANDIDATE`.

Wispral adaptation rule:

- map source taxonomy into Wispral's threat model rather than copying labels as policy truth;
- preserve source attribution for copied/adapted taxonomy text;
- do not make a Tencent scanner score equivalent to a Wispral risk tier.

### Dynamic Agent-Scan patterns

Source family:

- `agent-scan/` at the pinned repository revision;
- mode: `FIXTURE_OR_TAXONOMY_CANDIDATE` and `BEHAVIORAL_REIMPLEMENTATION_CANDIDATE` for provider-agnostic harness concepts.

Useful behavior:

- black-box target-provider abstraction;
- independent security skills;
- vulnerable local target agents;
- authorization bypass, data leakage, indirect injection, tool abuse, web exfiltration, agentic supply chain, unexpected code execution, inter-agent security, cascading failure, and human-agent trust exploitation.

Wispral adaptation rule:

- synthetic/local targets first;
- no live third-party red teaming without explicit authorization;
- no LLM attacker/reviewer required for deterministic acceptance tests;
- preserve dialogue/test traces separately from final verdicts.

### NOTICE obligation

Observed `skill-scan/NOTICE` blob: `10016100a50031f0ddcaa930d20fc1439e01c8d0`.

It requires attribution including the statement `Based on Tencent Zhuque Lab AI-Infra-Guard` and a link to the upstream repository for integrations/derivatives covered by that NOTICE. Any selected donor path must re-check its applicable NOTICE/license at the exact adopted revision.

## google/magika

Pinned repository revision: `26b6a9ba7e92f2b0a3745970a9190ec0dde9bf83`.

Primary mode: `DEPENDENCY_CANDIDATE` before direct copying, because an active Rust library boundary already exists.

Observed Rust library source candidates:

| Path | Blob | Relevance |
|---|---|---|
| `rust/lib/src/lib.rs` | `aa61e6ac4fd9c4ad3ddbd4aa49158583a6b71ecf` | public library boundary |
| `rust/lib/src/input.rs` | `250f24f43fda39829303755376487f6d9364385c` | bounded classifier input preparation |
| `rust/lib/src/file.rs` | `d426dd8862db1d3d33cf781a02577b940794b345` | file-oriented classification boundary |
| `rust/lib/src/content.rs` | `d892f8c6d5f979b1ac1f5ebcf2e11ab86f796117` | content-type definitions/metadata |
| `rust/lib/src/model.rs` | `d6bd5b4187c60c6f0bd68b120f1ba98c7affac6b` | model-level classifier behavior |
| `rust/lib/src/session.rs` | `18c11470496aafd3d7ca07a933f2884c40ef4b1f` | inference/session boundary |

Wispral adoption rule:

- prefer a pinned crate/library integration over forking classifier internals if footprint, maintenance, model licensing, binary size, startup cost, and platform support qualify;
- keep it behind a `ContentIdentityProvider` interface;
- preserve an `UNKNOWN`/generic fallback and confidence;
- never let a content-classifier score authorize execution;
- independently test extension spoofing, symlinks, empty files, source/config/binary/archive ambiguity, and unsupported formats;
- record the exact model artifact identity as well as the Rust source identity if selected.

## Tencent/AICGSecEval

Pinned repository revision: `94428ebf45141bf4ecd365a51d596dcd51caa690`.

Primary mode: `BEHAVIORAL_REIMPLEMENTATION_CANDIDATE` and `FIXTURE_OR_TAXONOMY_CANDIDATE` for WispralBench; not a runtime dependency.

Observed agent-harness sources:

| Path | Blob | Relevance |
|---|---|---|
| `bench/agent/base.py` | `b9ed81a2c9a6224a9557bfb3b52aae1c3bbba236` | common agent benchmark abstraction |
| `bench/agent/manager.py` | `e0fa215d693db48ef7981d3c226f9b82d8d3fdf3` | adapter selection/orchestration |
| `bench/agent/claude_code.py` | `db812e5dc2a143a37be8bb396b46c821185d7a92` | concrete independent-agent adapter example |
| `bench/agent/codex.py` | `cfe13340ab316affd15fd2363d143678a03b66f6` | concrete independent-agent adapter example |
| `bench/agent/gemini.py` | `1e6ba2011f2821bbbfa1d6c4ed5663b5a9cdb901` | concrete independent-agent adapter example |

Wispral adaptation rule:

- copy the **evaluation separation**, not vendor-specific control-plane semantics;
- benchmark adapter start/stop/interaction lifecycle independently from Wispral's product ACP/PTY adapters;
- preserve exact agent/model/configuration identity;
- combine functional task outcome with separate security evidence;
- use known vulnerable and negative-control repository fixtures;
- keep static and dynamic security evidence independently inspectable;
- preserve checkpoint/resume semantics only if they do not allow partial-run selection bias.

## Tencent/secguide

Pinned repository revision: `bfda087142e3bb3f5840cbc6af82c1982d1d14e4`.

Primary mode: `REFERENCE_ONLY_BY_DEFAULT` and `FIXTURE_OR_TAXONOMY_CANDIDATE`.

Relevant source documents include the C/C++, JavaScript/Node, Go, Java, and Python secure-coding guides linked from the repository README.

Wispral adoption rule:

- use rule concepts to improve native/non-Rust adapter review criteria and remediation language;
- do not import large guide sections into Wispral documentation by default;
- any copied/adapted material must retain exact CC-BY-SA-4.0 provenance and satisfy share-alike/attribution obligations applicable to that material;
- the absence of Rust coverage means this source cannot substitute for Rust/unsafe/FFI-specific security guidance.

## Tencent/TscanCode

Pinned repository revision: `3e3b6b66a7e39283d99add581fb9d54ee80c48f5`.

Primary mode: `OUT_OF_PROCESS_ONLY_BY_DEFAULT`.

Observed implementation areas include:

- `trunk/lib/` — analyzer core;
- `trunk/cfg/` — configuration/rule data;
- `trunk/cli/` — CLI boundary;
- `trunk/externals/` — nested third-party material that requires separate license review.

Wispral adoption rule:

- do not link/copy GPL analyzer implementation into the portable core by default;
- if a future native C/C++ speech/FFI Grain needs external static analysis, evaluate TscanCode alongside current alternatives rather than selecting it from history alone;
- ingest machine-readable findings through a generic external-scanner boundary;
- pin analyzer version/config/rules and preserve raw output;
- treat nested `trunk/externals/` as separately provenance-sensitive.

## Cross-source implementation strategy

The preferred implementation sequence if later authorized is:

1. **Own the contracts in Rust first.** Define `ContentIdentity`, `DecodedContent`, `ObjectProvenance`, `SecurityObservation`, `SecurityFinding`, `CapabilityManifest`, and `PolicyDecision` without embedding donor-specific types.
2. **Build deterministic primitives first.** Safe path handling, bounded reads, encoding/control checks, exact identity hashing, deterministic pre-scan, and policy gates must work without remote models.
3. **Use Magika only behind a provider interface.** The classifier should enhance content identity, not become the only way to ingest repository files.
4. **Use SARIF at the edge.** Import/export external findings through an adapter; do not make SARIF the policy engine.
5. **Keep AI-Infra-Guard LLM scanners optional.** They can enrich evidence but never become the only path to a safe result.
6. **Use AICGSecEval patterns in WispralBench.** Security evaluation belongs in benchmark/harness architecture, not the product runtime.
7. **Keep copyleft/native analyzers out-of-process unless deliberately selected.** This avoids accidental coupling of licensing, portability, and core runtime semantics.
8. **Re-run provenance qualification for every copied file.** Repository-level license labels are insufficient when component files or NOTICE requirements differ.

## Required provenance record for future copied/adapted code

Every future direct adaptation should record at minimum:

```text
upstream_repository
upstream_revision
upstream_path
upstream_blob_sha
upstream_license
upstream_notice_sha_or_none
founder_source_use_authorization_reference
adoption_mode
wispral_destination_path
adaptation_summary
behavioral_contract
security_review
license_review
qualification_tests
```

If a field is unknown, the adoption is not ready to merge.

## Explicit non-authorization

This donor map does not authorize any source-code import, dependency installation, scanner execution, MCP/Skill plugin system, product runtime change, benchmark rerun, B2 recovery change, or scoring. It only narrows future donor investigation so later work can be exact, reviewable, and license/provenance safe.
