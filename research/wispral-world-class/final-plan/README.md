# Final master plan: machine-checked companion

This folder backs [`docs/strategy/WISPRAL_MASTER_PLAN_FINAL.md`](../../../docs/strategy/WISPRAL_MASTER_PLAN_FINAL.md). It is planning material only, and authorizes nothing.

| File | Role |
| --- | --- |
| [`plan_graph.json`](plan_graph.json) | The single source of truth for:<ul><li>every finding (contradiction or gap, with severity and citations);</li><li>every vehicle that resolves it: founder decision, governance PR, packet amendment, research Grain, ADR, 000G selection;</li><li>the stages and the roadmap packet groups;</li><li>the dependency amendments the plan proposes.</li></ul> |
| [`check_plan_graph.py`](check_plan_graph.py) | The validator, described below |
| [`RESOLUTION_REGISTER.md`](RESOLUTION_REGISTER.md) | Generated from the JSON. Do not edit by hand. |

**Run it from the repository root:**

```bash
python research/wispral-world-class/final-plan/check_plan_graph.py --write
```

**The checks:**
1. IDs are unique.
2. Every finding is resolved, and every resolver exists.
3. There are no unknown dependencies and no cycles.
4. No vehicle depends on a later stage.
5. Every 000G selection opens exactly one Grain (Specification 000).
6. Every roadmap packet exists in `packets.json` or is declared new.
7. Every new packet is placed.
8. **Amendment simulation.** The proposed dependency edits (PA-01, PA-02, PA-03, PA-05, PA-06, PA-16) are applied to `packets.json` in memory. No product stage may then depend on the blocked `ST-D00` or `KT-01`.

The script reads `packets.json` and writes only `RESOLUTION_REGISTER.md`, and only when `--write` is given.

**Where the findings came from.** Four read-only research passes over `main` at `246283f`:
- governance and process;
- architecture and security, including the merged SD-M0, ST-D00 and KT-01 evidence;
- dependencies, licensing and the packet graph, computed from `packets.json`;
- the three open planning draft PRs (#124, #127, #73).

Duplicate findings were merged; their other IDs are listed as aliases.

**If you change a decision:** edit `plan_graph.json` and rerun. The checker shows which stages and vehicles the change affects.
