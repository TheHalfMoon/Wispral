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
3. The vehicle graph has no unknown dependency and no cycle, and no vehicle depends on a later stage.
4. Every 000G selection opens exactly one Grain (Specification 000).
5. **Coverage.** Every one of the 75 packets in `packets.json` has exactly one place: a roadmap group, or a stated disposition. Every roadmap packet exists or is declared new, every new packet is placed, and research packets are declared separately.
6. **Amendment simulation.** The proposed dependency edits are applied to `packets.json` in memory. Every edit must name an existing packet and change something: no unknown target, no no-op. Every new packet must have planned dependencies. The simulated graph must have no cycle.
7. **Order.** After the edits, every dependency of a roadmap packet must be either available before the roadmap, a research packet, or placed in the same or an earlier group. A selected Grain's dependencies must be ready before its own group.
8. **Gating.** After the edits, no roadmap packet in any group may depend on the blocked `ST-D00` or `KT-01`.

The checker was mutation-tested on a scratch copy. It caught all ten deliberate breakages:
- a two-Grain selection;
- an unknown replacement target;
- a no-op replacement;
- a packet placed before its dependency;
- a dropped packet;
- a blocked dependency in S8;
- a new packet without dependencies;
- a selected Grain whose dependency is not ready;
- a vehicle cycle;
- an unresolved finding.

The simulation covers **dependency** edits only. Edits to acceptance text are checked in review of each packet regeneration.

The script reads `packets.json` and writes only `RESOLUTION_REGISTER.md`, and only when `--write` is given.

**Where the findings came from.** Four read-only research passes over `main` at `246283f`:
- governance and process;
- architecture and security, including the merged SD-M0, ST-D00 and KT-01 evidence;
- dependencies, licensing and the packet graph, computed from `packets.json`;
- the three open planning draft PRs (#124, #127, #73).

Duplicate findings were merged; their other IDs are listed as aliases. Review round 1 of PR #155 added 23 findings (marked with their source). The author's own dependency audit added one more (PKT-21). Finding IDs use area prefixes (GOV, ARC, SEC, LIC, DEP, PKT, SAL); `former_id` gives the ID before the rename.

**If you change a decision:** edit `plan_graph.json` and rerun. The checker shows which stages and vehicles the change affects.
