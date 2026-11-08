# Specification 000E Tasks

This file tracks Grain progression. Pins, acceptance and evidence paths are in `research/wispral-world-class/packets.json`.

## Grains

- [ ] `SD-M0`: WisprSide fork baseline. State `GRAIN`. Needs `CORE-00`, and the founder's decision on the fork's location and visibility.
- [ ] `ST-D00`: WisprStudio fork baseline with the fake `_echo` engine. State `GRAIN`. Needs `CORE-00`, and the founder's decision on the fork's location and visibility.
- [ ] `ST-D00b`: static comparison of the two production donors. Its dependencies are canonical (F `b6c8507`, `CORE-00` `81b2de6`), and it was executed in its own pull request: `research/wispral-world-class/evidence/baselines/studio-lead-comparison.md`. VoiceStudio stays the lead (capability 10 vs 7; delta size 17 vs 21.5). It becomes `VERIFIED` after merge and a canonical reread.
- [ ] `KT-01`: Klaint dialogue-engine spike with a fake LLM backend. State `GRAIN`. Needs `CORE-00`.

## Closeout

- [ ] Write the per-product 000E synthesis (established, failed, unknown).
- [ ] Reconcile the 000E disposition into `specs/CURRENT.md`, in its designated sections only.

## Product-code gate

000E authorizes no product code, installer or release. The product-code gate in `specs/CURRENT.md` applies unchanged until a 000G decision.
