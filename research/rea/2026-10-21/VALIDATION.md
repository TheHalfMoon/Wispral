# Validation of the research bundle

Scope: documentation/evidence integrity and bounded reproduction helpers. This is not product, independent security, benchmark or release qualification. Final Git commit identity binds the documents and EVIDENCE_INDEX.json; the index intentionally excludes its own digest.

## Checks performed

- JSON parse of the new evidence files, 132 catalog entries, exact source-pin shape and nontruncated acquired-tree records.
- Local Markdown target existence, unique IDs for 72 proposed transplant mechanisms and required path/URL/hash identity on each source row.
- SHA-256 and byte-length match for each indexed artifact, plus a bounded secret-pattern scan of new files. Such a scan does not prove all possible secret formats absent.
- Node syntax check and actual replay of `reproduce_core_policy.mjs` against the exact five pinned Ninerr modules: the same six pure fixtures passed again. This replay is not six additional unique tests. The Node module-type warning was retained and does not establish a native integration failure.
- Existing study results retained: 17 unique unchanged OpenWhispr helper tests and eight named synthetic non-audio Studio mechanism cases. No broad upstream suites were added or claimed.
- Changed-path review and `git diff --check` before committing. Only new research, proposed strategy and proposed ADR paths are in scope; canonical/governance controls and historical benchmark evidence remain unchanged.

Run the bundle checker from the repository root with an existing Node interpreter:

```text
node research/rea/2026-10-21/validate_research.mjs
```

Its PASS applies only to the printed integrity scope. It does not check every remote URL's future availability, establish model rights, prove native behavior or satisfy a required independent security/release gate. Per-source Git blob/source anchors were checked during acquisition; byte capture alone is not semantic review of all source lines.

## Checks not run

No product workspace exists in the canonical state; Cargo fmt/clippy/test for a new Wispral runtime is not applicable to this documentation-only mission. Donor full applications, native microphone/paste/OS installation, authenticated agent/customer actions, audio/model/GPU inference, telephony, human speech quality and performance benchmarks remain NOT_RUN/NOT_MEASURED as indexed. No compatibility or production-quality claim follows from bundle validation.

The internal consistency review is recorded in [INTERNAL_CONSISTENCY_REVIEW.md](INTERNAL_CONSISTENCY_REVIEW.md). INDEPENDENT_REVIEW=NOT_SATISFIED_BY_THIS_FILE. Its scope is research integrity and plan feasibility, not the repository's required independent release/security approval.

## GitHub CI

The exact new PR head must be assessed after push. Existing later-PR B2R16 scope failures are described in [LIVE_FRONTIER_AND_HANDOFF.md](LIVE_FRONTIER_AND_HANDOFF.md); they remain failures. No trusted workflow/verifier is changed in this research PR. A draft delivery is not merge approval, and a missing/skipped/pending check is not a pass. Preserve final observed head/check status in the PR and handoff rather than editing historical evidence to fit this plan.

## Opus repair acceptance

Current map: 75 source mechanisms (original 72 plus three Parlant records at the original pin), uniform decision/runtime_status, explicit retained-fork paths and owners. Authority graph: 26 packets, each with a proposed authority, no READY state, valid references and no cycles. The validator checks the graph structurally; semantic founding dependencies are documented and reviewed separately. Missing decision/runtime_status negative fixtures must reject.

Q-02 research boundary: three unittest methods / 21 named cases PASS (16 rejects, four unchanged donor golden payloads, explicit silence/empty-zero behavior). NaN/infinity, negative/zero durations, inverted/overlapping ranges and non-finite totals reject before donor plan_fit. Donor SHA before/after is identical. Full upstream pytest/native/model paths remain NOT_RUN. Reproduction and actual output: [fit_input_boundary_probe.py](fit_input_boundary_probe.py), [fit-input-boundary-results.json](fit-input-boundary-results.json).

[Plan repair review](PLAN_REPAIR_INTERNAL_REVIEW.md) is same-mission fresh-context review; it is not required external approval. Final exact-head local and GitHub observations belong in the PR description and final-head evidence. Original CI failures stay FAIL; skipped mandatory jobs stay SKIPPED, not PASS. Freeze repair [#126](https://github.com/TheHalfMoon/Wispral/pull/126) remains separate.
