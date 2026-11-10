# Specification 000F Tasks

This file tracks Grain progression. Pins, acceptance and evidence paths are in `research/wispral-world-class/packets.json`.

## Grains

- [x] `CORE-00`: re-pins, rights register and licence-decision gate. `VERIFIED`: merged as `81b2de6da0b526320c311c9a2a210f80f3b221a6` (#141). The post-merge reread on #141 reran the verifier on `main` (`ANCHORS=57 PASS=57`). The licence gate stayed **CLOSED** at that merge. It opened on 2026-11-09, when the founder chose Apache-2.0 (#146, `53d32b5`; `research/wispral-world-class/RIGHTS_REGISTER.md` §1).

## Closeout

- [ ] Write the 000F synthesis: provenance inputs and open rights questions per candidate first Grain.
- [ ] Reconcile the 000F disposition into `specs/CURRENT.md`, in its designated sections only.

## Product-code gate

000F authorizes no product code. The founder's outbound-licence decision is recorded: Apache-2.0 (#146, 2026-11-09). `COPY` and `ADAPT` packets still land code only under the conditions in `RIGHTS_REGISTER.md` §1, and only through a Grain the product-code gate opens. The product-code gate in `specs/CURRENT.md` applies unchanged until a 000G decision.
