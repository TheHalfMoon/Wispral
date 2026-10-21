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

The independent planning review is recorded in [FINAL_INDEPENDENT_REVIEW.md](FINAL_INDEPENDENT_REVIEW.md). Its scope is research integrity and plan feasibility, not the repository's required independent release/security approval.

## GitHub CI

The exact new PR head must be assessed after push. Existing later-PR B2R16 scope failures are described in [LIVE_FRONTIER_AND_HANDOFF.md](LIVE_FRONTIER_AND_HANDOFF.md); they remain failures. No trusted workflow/verifier is changed in this research PR. A draft delivery is not merge approval, and a missing/skipped/pending check is not a pass. Preserve final observed head/check status in the PR and handoff rather than editing historical evidence to fit this plan.
