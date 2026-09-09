# Wispral Founder Source-Use Attestation

**Status:** research planning evidence; non-executable  
**Recorded:** 2026-09-07  
**Scope:** all source-code projects already present in Wispral research artifacts and all source-code projects previously discussed for Wispral  
**Authority effect:** none; this record does not change the active specification frontier or authorize product implementation

## Founder statement

The Founder attests that Wispral has permission to use the source code of every source-code project already recorded in the repository and every source-code project previously discussed for Wispral, including permission to copy, modify, adapt, combine, reimplement, and otherwise reuse that code for Wispral as needed.

For repository governance, this is recorded as a **Founder-attested broad source-use permission basis** covering the Wispral source universe.

## What this attestation enables

When an implementation unit is canonically authorized, a source may be evaluated as a direct donor without requiring the planning process to assume that public upstream licensing is the only possible rights basis.

A future import may therefore choose among:

- direct dependency use;
- minimal code transplant;
- adapted transplant;
- clean Wispral reimplementation informed by the source;
- compatibility-oracle use;
- architecture/reference-only use.

The implementation decision must still be job-driven and architecture-driven rather than permission-driven.

## What this attestation does not remove

Broad permission does not remove the repository's evidence and supply-chain requirements. Every direct or adapted import must still record:

1. exact upstream repository identity;
2. exact upstream revision or release;
3. exact upstream paths used;
4. source hashes for copied/adapted material where practical;
5. the public upstream license observed at the pinned revision;
6. this Founder-attested permission basis, plus any more specific permission evidence if later available;
7. required notices or attribution that Wispral chooses or is required to preserve;
8. transitive dependencies and native binaries;
9. model, tokenizer, dataset, voice, generated asset, and other non-application-code rights separately;
10. adaptation summary and Wispral-owned destination paths;
11. security and platform notes;
12. acceptance tests and independent review evidence.

No model weight, dataset, tokenizer, voice, binary blob, hosted service, trademark, or third-party asset is inferred to be covered merely because application source code is covered.

## Evidence classification

This document records a statement supplied by the Founder. It is not represented as independently verified legal documentation.

Repository status label:

`FOUNDER_ATTESTED_BROAD_SOURCE_USE_PERMISSION`

Verification label:

`FOUNDER_ATTESTED_NOT_EXTERNALLY_VERIFIED`

That distinction must remain visible in future provenance packages.

## Canonical implementation rule

Permission is not implementation authority.

A donor may enter product paths only when all of the following are true:

- the active canonical specification authorizes the named implementation unit;
- the donor solves a named Wispral job;
- exact source identity and revision are pinned;
- the transplant surface is bounded behind a Wispral-owned contract;
- dependency and asset rights are classified;
- security, privacy, and platform risks are reviewed;
- deterministic acceptance tests exist;
- exact-head CI and required independent review pass;
- the import is merged through normal guarded repository governance.

Until then, all source-adoption artifacts remain planning-only.
