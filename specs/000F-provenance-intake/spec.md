# Specification 000F — Provenance Intake

**State:** `REFINING`
**Parent:** `000-founding-research`
**Type:** research parent specification
**Opened by:** the frontier reconciliation (packet F) under Constitution 1.0.0

## Outcome

Turn the existing source, rights and reuse records into decision-grade provenance inputs for 000G (Constitution Principle XX). For every donor a candidate first Grain would use, record:

- its exact pins;
- its actual dependency closure;
- its licence and notice obligations, and grant-scope flags;
- its native and model artifacts;
- whether it can be distributed and maintained.

Catalogue presence is not completion.

## Research Grains

This specification opens exactly one research Grain. It is defined by this packet in `research/wispral-world-class/packets.json`, which holds its exact pins, acceptance and evidence paths:

| Grain | Scope | Depends on |
| --- | --- | --- |
| `CORE-00` | Re-pins, rights register and licence-decision gate | F |

`CORE-00` stays `GRAIN` until its readiness is recorded on its own pull request. Its acceptance includes a licence-gate row: no `COPY` or `ADAPT` packet may land code until the founder's Wispral outbound-licence decision is recorded.

This specification authorizes no other packet.

## In scope

- Re-verifying each donor anchor by blob identity and SHA-256.
- A rights register that separates source-code grants from model, tokenizer, dataset, voice and media rights (Principle XVIII).
- Marking sources whose licences forbid adoption as reference-only.
- Recording catalogue errata.
- Recording founder-confirmed grants as `CONFIRMED_BY_FOUNDER`, with the documents private. This specification never requests confidential agreements.

## Out of scope

This specification does NOT authorize:

- landing donor code in a product path;
- a legal opinion, or any claim that private agreements were examined;
- trademark, domain or store clearance;
- product code, a release, or distribution.

## Acceptance conditions

000F can close only when:

- `CORE-00` is `VERIFIED`;
- every donor named by a 000E Grain has a recorded rights row;
- the licence gate's status is explicit: either the founder's decision is recorded, or the gate is recorded as still closed.

## Evidence requirements

Record, per donor:

- the pinned SHA and the verified blob identities;
- the licence and notice files;
- grant-scope flags;
- native and model artifacts;
- dependency-closure notes;
- the method used to verify each item.

## Risk

- A licence incompatibility found late.
- Conflating a source-code grant with rights in models or voices.
- Catalogue drift between pins and the records.

## Recovery

Records are additive. A wrong pin or rights row is corrected forward, and the error is noted in the errata.

## Definition of done

For every donor that 000G may cite, the provenance and rights inputs are recorded and reproducible.
