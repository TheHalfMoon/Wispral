# Specification 000E Plan

## Strategy

Measure the donors as they are before changing anything. Rights come first: every 000E Grain except the static comparison depends on `CORE-00` (000F), because a baseline of a donor whose licence status is unknown cannot inform a decision.

## Order

1. `CORE-00` (000F) re-pins the donors and records the rights register and the licence gate.
2. In parallel, once `CORE-00` is canonical:
   - `SD-M0`: the WisprSide fork baseline;
   - `ST-D00`: the WisprStudio fork baseline;
   - `ST-D00b`: the static comparison of the two production donors;
   - `KT-01`: the Klaint dialogue spike.
3. A 000E synthesis note per product, cited by 000G.

## Execution environments

- **Hosted CI** (Linux runners) for reproducible suites.
- **HW-A**, the founder's laptop (Windows 11 Home, medium-integrity user session). Its evidence is recorded with the machine details under `research/wispral-world-class/evidence/`, and runs there only with the founder's go-ahead.

Paid runner minutes or paid services are not used without the founder's authorization.

## Experiment discipline

- Pin every donor by full commit SHA, and re-verify the pins before the run.
- Run donor suites unmodified, and record counts and failures as they are.
- Do not tune a baseline to pass. Do not download forbidden models.
- Retain failed attempts, with the reason they failed.

## Closeout

After the four Grains settle:

- update `specs/CURRENT.md`, in its designated sections, with the 000E disposition;
- hand the per-product synthesis to 000G.
