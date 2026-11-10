"""Validate the final master plan's graph and generate RESOLUTION_REGISTER.md from it.

Run from the repository root:  python research/wispral-world-class/final-plan/check_plan_graph.py [--write]

Checks (exit 1 on any failure):
  1. IDs are unique across findings and vehicles.
  2. Every finding is resolved by at least one vehicle, and every resolver exists.
  3. Every vehicle dependency exists, the vehicle graph has no cycle, and no vehicle depends on a
     vehicle in a later stage.
  4. Every 000G selection opens exactly one Grain (Specification 000).
  5. Every packet in packets.json has exactly one place in the plan: a roadmap group, or a
     disposition. Every roadmap packet exists in packets.json or is declared new; every new packet is
     placed; research packets are declared separately.
  6. Simulated amendments: the proposed dependency edits are applied in memory. Every edit must name
     an existing packet and change something (no unknown target, no no-op). The simulated packet graph
     must have no cycle.
  7. Order: after the edits, every dependency of a roadmap packet is available before the roadmap,
     a research packet, or placed in the same or an earlier roadmap group. A selected Grain's
     dependencies must be available before its own group.
  8. Gating: after the edits, no roadmap packet in any group depends, directly or transitively, on a
     blocked baseline (ST-D00, KT-01).
With --write, also regenerates RESOLUTION_REGISTER.md next to this file.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
graph = json.load(open(os.path.join(HERE, "plan_graph.json"), encoding="utf-8"))
packets = json.load(open(os.path.join(ROOT, "research", "wispral-world-class", "packets.json"), encoding="utf-8"))
packet_ids = [p["id"] for p in packets["packets"]]

errors = []
vehicles = {v["id"]: v for v in graph["vehicles"]}
findings = graph["findings"]
stage_order = {s["id"]: s["order"] for s in graph["stages"]}
new_packets = set(graph["new_packets"])
research = graph["research_packets"]
groups = graph["roadmap_groups"]
available = set(graph["available_before_roadmap"])
dispositions = graph["dispositions"]

# 1. unique ids
ids = list(vehicles) + [f["id"] for f in findings]
dups = sorted({i for i in ids if ids.count(i) > 1}) + sorted({p for p in packet_ids if packet_ids.count(p) > 1})
if len(ids) != len(set(ids)):
    errors.append(f"duplicate ids: {dups}")

# 2. resolution coverage
for f in findings:
    if not f["resolved_by"]:
        errors.append(f"{f['id']}: no resolver")
    for r in f["resolved_by"]:
        if r not in vehicles:
            errors.append(f"{f['id']}: unknown resolver {r}")

# 3. vehicle graph
for v in graph["vehicles"]:
    if v["stage"] not in stage_order:
        errors.append(f"{v['id']}: unknown stage {v['stage']}")
    for d in v["depends_on"]:
        if d not in vehicles:
            errors.append(f"{v['id']}: unknown dependency {d}")
        elif stage_order.get(vehicles[d]["stage"], 99) > stage_order.get(v["stage"], -1):
            errors.append(f"{v['id']} ({v['stage']}) depends on later-stage {d} ({vehicles[d]['stage']})")


def find_cycles(nodes, deps_of, label):
    state = {}

    def visit(n, path):
        if state.get(n) == 1:
            errors.append(f"{label} cycle: " + " -> ".join(path + [n]))
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for d in deps_of(n):
            if d in nodes:
                visit(d, path + [n])
        state[n] = 2

    for n in nodes:
        visit(n, [])


find_cycles(set(vehicles), lambda n: vehicles[n]["depends_on"], "vehicle")

# 4. exactly one Grain per selection
selections = [v for v in graph["vehicles"] if v["type"] == "SELECTION"]
for v in selections:
    if len(v.get("selects", [])) != 1:
        errors.append(f"{v['id']}: selects {len(v.get('selects', []))} Grains; Specification 000 requires exactly one")

# 5. placement and coverage
placed = {}
for gi, grp in enumerate(groups):
    for pid in grp["packets"]:
        if pid in placed:
            errors.append(f"{pid} placed twice ({placed[pid][1]} and {grp['id']})")
        placed[pid] = (gi, grp["id"])
for pid in placed:
    if pid not in packet_ids and pid not in new_packets:
        errors.append(f"roadmap names unknown packet {pid}")
for pid in new_packets:
    if pid in packet_ids:
        errors.append(f"new packet {pid} already exists in packets.json")
    if pid not in placed:
        errors.append(f"new packet {pid} is not placed")
for pid in research:
    if pid in packet_ids or pid in placed:
        errors.append(f"research packet {pid} collides with a packet or a placement")
for pid in packet_ids:
    in_plan = (pid in placed) + (pid in dispositions)
    if in_plan == 0:
        errors.append(f"packet {pid} has no place in the plan (roadmap group or disposition)")
    elif in_plan == 2:
        errors.append(f"packet {pid} is both placed and given a disposition")
for v in selections:
    for s in v.get("selects", []):
        if s not in placed:
            errors.append(f"{v['id']} selects {s}, which is not placed in the roadmap")

# 6. simulated amendments
sim = {p["id"]: copy.deepcopy(p) for p in packets["packets"]}
am = graph["simulated_amendments"]
for pid, deps in list(am.get("add_packets", {}).items()) + list(research.items()):
    sim[pid] = {"id": pid, "depends_on": list(deps)}
missing_add = sorted(new_packets - set(am.get("add_packets", {})))
if missing_add:
    errors.append(f"new packets without planned dependencies in add_packets: {missing_add}")
for op in ("remove_deps", "remove_deps_extra"):
    for pid, rm in am.get(op, {}).items():
        if pid not in sim:
            errors.append(f"{op}: unknown packet {pid}")
            continue
        for d in rm:
            if d not in sim[pid]["depends_on"]:
                errors.append(f"{op}: {pid} has no dependency {d} (no-op)")
        sim[pid]["depends_on"] = [d for d in sim[pid]["depends_on"] if d not in rm]
for pid, rep in am.get("replace_deps", {}).items():
    if pid not in sim:
        errors.append(f"replace_deps: unknown packet {pid}")
        continue
    for old, new in rep.items():
        if old not in sim[pid]["depends_on"]:
            errors.append(f"replace_deps: {pid} has no dependency {old} (no-op)")
        if new not in sim:
            errors.append(f"replace_deps: {pid} -> unknown target {new}")
    sim[pid]["depends_on"] = [rep.get(d, d) for d in sim[pid]["depends_on"]]
for pid, add in am.get("add_deps", {}).items():
    if pid not in sim:
        errors.append(f"add_deps: unknown packet {pid}")
        continue
    for d in add:
        if d not in sim:
            errors.append(f"add_deps: {pid} -> unknown target {d}")
        if d in sim[pid]["depends_on"]:
            errors.append(f"add_deps: {pid} already depends on {d} (no-op)")
    sim[pid]["depends_on"] = sim[pid]["depends_on"] + [d for d in add if d not in sim[pid]["depends_on"]]
for pid, p in sim.items():
    for d in p["depends_on"]:
        if d not in sim:
            errors.append(f"simulated graph: {pid} depends on unknown {d}")
find_cycles(set(sim), lambda n: sim[n]["depends_on"], "simulated packet")

# 7. order
for pid, (gi, gid) in placed.items():
    for d in sim.get(pid, {}).get("depends_on", []):
        if d in available or d in research:
            continue
        if d in placed and placed[d][0] <= gi:
            continue
        where = f"later group {placed[d][1]}" if d in placed else (f"disposition '{dispositions.get(d)}'" if d in dispositions else "nowhere")
        errors.append(f"{gid}: {pid} depends on {d}, which is in {where}")
for v in selections:
    for s in v.get("selects", []):
        if s in placed:
            gi = placed[s][0]
            for d in sim.get(s, {}).get("depends_on", []):
                if not (d in available or d in research or (d in placed and placed[d][0] < gi)):
                    errors.append(f"{v['id']}: selected {s} depends on {d}, not available before {placed[s][1]}")

# 8. gating
blocked = set(graph["blocked_baselines"])


def ancestors(pid, seen=None):
    seen = set() if seen is None else seen
    for d in sim.get(pid, {}).get("depends_on", []):
        if d not in seen:
            seen.add(d)
            ancestors(d, seen)
    return seen


gating = {}
for grp in groups:
    hit = {}
    for pid in grp["packets"]:
        b = sorted(ancestors(pid) & blocked)
        if b:
            hit[pid] = b
            errors.append(f"{grp['id']}: {pid} still gated by {b} after the simulated amendments")
    gating[grp["id"]] = hit

sev = {}
for f in findings:
    sev[f["severity"]] = sev.get(f["severity"], 0) + 1
types = {}
for v in graph["vehicles"]:
    types[v["type"]] = types.get(v["type"], 0) + 1
print(f"findings: {len(findings)} {dict(sorted(sev.items()))}")
print(f"vehicles: {len(vehicles)} {dict(sorted(types.items()))}")
print(f"packets: {len(packet_ids)} in packets.json; {sum(1 for p in placed if p in packet_ids)} placed, {len(dispositions)} with a disposition; {len(new_packets)} new; {len(research)} research")
print(f"selections: {len(selections)}, each exactly one Grain: " + ", ".join(f"{v['id']}={v['selects'][0]}" for v in selections))
print("gating after simulated amendments: " + json.dumps({k: v for k, v in gating.items()}))
if errors:
    print("FAIL")
    for e in errors:
        print("  " + e)
    sys.exit(1)
print("PASS")

if "--write" in sys.argv:
    by_vehicle = {}
    for f in findings:
        for r in f["resolved_by"]:
            by_vehicle.setdefault(r, []).append(f["id"])
    out = ["# Resolution register (generated)", "",
           "Generated by `check_plan_graph.py --write` from [`plan_graph.json`](plan_graph.json). Do not edit by hand: edit the JSON and regenerate.", "",
           f"**{len(findings)} findings** ({', '.join(f'{k} {v}' for k, v in sorted(sev.items()))}), each resolved by at least one of **{len(vehicles)} vehicles** ({', '.join(f'{k} {v}' for k, v in sorted(types.items()))}).", "",
           "Vehicle types: FD founder decision; AMENDMENT constitutional amendment; GP governance or plan PR (including the two packet regenerations); PA packet amendment; RG research Grain; ADR architecture decision; SELECTION a 000G selection of exactly one Grain; PLAN coarse direction in the master plan.", "",
           "Finding IDs use area prefixes (GOV, ARC, SEC, LIC, DEP, PKT, SAL) so they never collide with packet IDs or decision-ledger rows. `former_id` gives the ID used before review round 1.", ""]
    for area in ["governance", "architecture", "security", "licensing", "dependency", "packet-graph", "salvage"]:
        rows = [f for f in findings if f["area"] == area]
        if not rows:
            continue
        out += [f"## {area.capitalize()} ({len(rows)})", "", "| ID | Severity | Finding | Resolved by | Main citations |", "| --- | --- | --- | --- | --- |"]
        for f in rows:
            extra = []
            if f.get("former_id"):
                extra.append(f"was {f['former_id']}")
            if f.get("aliases"):
                extra.append("also " + ", ".join(f["aliases"]))
            if f.get("source"):
                extra.append(f["source"])
            tag = f" ({'; '.join(extra)})" if extra else ""
            out.append(f"| {f['id']}{tag} | {f['severity']} | {f['summary']} | {', '.join(f['resolved_by'])} | {f['cite']} |")
        out.append("")
    out += ["## Vehicles", "", "| ID | Type | Stage | Approval | Depends on | What it does | Resolves |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for v in graph["vehicles"]:
        sel = f" Selects: {v['selects'][0]}." if v.get("selects") else ""
        out.append(f"| {v['id']} | {v['type']} | {v['stage']} | {v['approval']} | {', '.join(v['depends_on']) or '—'} | {v['title']}.{sel} | {', '.join(by_vehicle.get(v['id'], [])) or '—'} |")
    out += ["", "## Packet dispositions (packets not placed in a roadmap group)", "", "| Packet | Disposition |", "| --- | --- |"]
    for pid in packet_ids:
        if pid in dispositions:
            out.append(f"| {pid} | {dispositions[pid]} |")
    out += ["", "## Roadmap groups", "", "| Group | Stage | Packets (in order) |", "| --- | --- | --- |"]
    for grp in groups:
        out.append(f"| {grp['id']} | {grp['stage']} | {', '.join(grp['packets'])} |")
    out.append("")
    open(os.path.join(HERE, "RESOLUTION_REGISTER.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("wrote RESOLUTION_REGISTER.md")
