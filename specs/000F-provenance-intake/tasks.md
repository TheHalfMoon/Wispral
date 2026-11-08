# Specification 000F Tasks

This file tracks Grain progression. Pins, acceptance and evidence paths are in `research/wispral-world-class/packets.json`.

## Grains

- [x] `CORE-00`: re-pins, rights register and licence-decision gate. `VERIFIED`: merged as `81b2de6da0b526320c311c9a2a210f80f3b221a6` (#141). The post-merge reread on #141 reran the verifier on `main` (`ANCHORS=57 PASS=57`). The licence gate stays **CLOSED**.

## Closeout

- [ ] Write the 000F synthesis: provenance inputs and open rights questions per candidate first Grain.
- [ ] Reconcile the 000F disposition into `specs/CURRENT.md`, in its designated sections only.

## Product-code gate

000F authorizes no product code. Until the founder's outbound-licence decision is recorded, no `COPY` or `ADAPT` packet may land code. The product-code gate in `specs/CURRENT.md` applies unchanged until a 000G decision.
