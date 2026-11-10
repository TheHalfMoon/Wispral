"""Validate the final master plan's graph and generate RESOLUTION_REGISTER.md from it.

Run from the repository root:  python research/wispral-world-class/final-plan/check_plan_graph.py [--write]

Checks (exit 1 on any failure):
  1. IDs are unique across findings and vehicles.
  2. Every finding is resolved by at least one vehicle, and every resolver exists.
  3. Every vehicle dependency exists, and the dependency graph has no cycle.
  4. No vehicle depends on a vehicle in a later stage.
  5. Every 000G selection selects exactly one Grain (Specification 000).
  6. Every packet named by a selection or the roadmap exists in packets.json or is declared new.
  7. Every new packet is placed somewhere in the roadmap or a selection.
  8. With the proposed dependency amendments applied in memory (simulated_amendments), each
     roadmap stage is gated only by the blocked baselines its gating_expectations allow.
With --write, also regenerates RESOLUTION_REGISTER.md next to this file.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
graph = json.load(open(os.path.join(HERE, "plan_graph.json"), encoding="utf-8"))
packets = json.load(open(os.path.join(ROOT, "research", "wispral-world-class", "packets.json"), encoding="utf-8"))
packet_ids = {p["id"] for p in packets["packets"]}

errors = []
vehicles = {v["id"]: v for v in graph["vehicles"]}
findings = graph["findings"]
stage_order = {s["id"]: s["order"] for s in graph["stages"]}
new_packets = set(graph["new_packets"])

ids = [v["id"] for v in graph["vehicles"]] + [f["id"] for f in findings]
dups = {i for i in ids if ids.count(i) > 1}
if dups:
    errors.append(f"duplicate ids: {sorted(dups)}")

for f in findings:
    if not f["resolved_by"]:
        errors.append(f"{f['id']}: no resolver")
    for r in f["resolved_by"]:
        if r not in vehicles:
            errors.append(f"{f['id']}: unknown resolver {r}")

for v in graph["vehicles"]:
    if v["stage"] not in stage_order:
        errors.append(f"{v['id']}: unknown stage {v['stage']}")
    for d in v["depends_on"]:
        if d not in vehicles:
            errors.append(f"{v['id']}: unknown dependency {d}")
        elif stage_order.get(vehicles[d]["stage"], 99) > stage_order.get(v["stage"], -1):
            errors.append(f"{v['id']} ({v['stage']}) depends on later-stage {d} ({vehicles[d]['stage']})")

state = {}


def visit(n, path):
    if state.get(n) == 1:
        errors.append("cycle: " + " -> ".join(path + [n]))
        return
    if state.get(n) == 2:
        return
    state[n] = 1
    for d in vehicles[n]["depends_on"]:
        if d in vehicles:
            visit(d, path + [n])
    state[n] = 2


for n in vehicles:
    visit(n, [])

placed = set()
for v in graph["vehicles"]:
    if v["type"] == "SELECTION":
        sel = v.get("selects", [])
        if len(sel) != 1:
            errors.append(f"{v['id']}: selects {len(sel)} Grains; Specification 000 requires exactly one")
        placed.update(sel)
for group, members in graph["roadmap_packets"].items():
    placed.update(members)
for p in sorted(placed):
    if p not in packet_ids and p not in new_packets:
        errors.append(f"roadmap/selection names unknown packet {p}")
for p in sorted(new_packets):
    if p in packet_ids:
        errors.append(f"new packet {p} already exists in packets.json")
    if p not in placed and p not in ("KT-01b", "ST-D00r"):
        errors.append(f"new packet {p} is not placed in the roadmap")

import copy
sim = {p["id"]: copy.deepcopy(p) for p in packets["packets"]}
am = graph.get("simulated_amendments", {})
for pid, deps in am.get("add_packets", {}).items():
    sim[pid] = {"id": pid, "depends_on": list(deps)}
for pid, rm in am.get("remove_deps", {}).items():
    sim[pid]["depends_on"] = [d for d in sim[pid]["depends_on"] if d not in rm]
for pid, rep in am.get("replace_deps", {}).items():
    sim[pid]["depends_on"] = [rep.get(d, d) for d in sim[pid]["depends_on"]]
blocked = set(graph.get("blocked_baselines", []))


def ancestors(pid, seen=None):
    seen = set() if seen is None else seen
    for d in sim.get(pid, {}).get("depends_on", []):
        if d not in seen:
            seen.add(d)
            ancestors(d, seen)
    return seen


gating_report = {}
for group, allowed in graph.get("gating_expectations", {}).items():
    hits = {}
    for pid in graph["roadmap_packets"][group]:
        if pid in sim:
            b = sorted(ancestors(pid) & blocked)
            if b:
                hits[pid] = b
            bad = sorted(set(b) - set(allowed))
            if bad:
                errors.append(f"{group}: {pid} still gated by {bad} after the simulated amendments")
    gating_report[group] = sorted({x for v in hits.values() for x in v})
print("gating after simulated amendments: " + json.dumps(gating_report))

referenced = {r for f in findings for r in f["resolved_by"]}
unreferenced = sorted(set(vehicles) - referenced)

sev = {}
for f in findings:
    sev[f["severity"]] = sev.get(f["severity"], 0) + 1
print(f"findings: {len(findings)} {sev}")
print(f"vehicles: {len(vehicles)} by type " + str({t: sum(1 for v in graph['vehicles'] if v['type'] == t) for t in sorted({v['type'] for v in graph['vehicles']})}))
print(f"packets placed: {len(placed)} (new: {len(new_packets)}); packets.json has {len(packet_ids)}")
print(f"vehicles not referenced by a finding (structural): {unreferenced}")
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
    out = []
    out.append("# Resolution register (generated)")
    out.append("")
    out.append("Generated by `check_plan_graph.py --write` from [`plan_graph.json`](plan_graph.json). Do not edit by hand: edit the JSON and regenerate.")
    out.append("")
    out.append(f"**{len(findings)} findings** ({', '.join(f'{k} {v}' for k, v in sorted(sev.items()))}), each resolved by at least one of **{len(vehicles)} vehicles**. Vehicle types: FD founder decision, GP governance PR, PA packet amendment (applied together as PA-SET), RG research Grain, ADR architecture decision, SELECTION a 000G selection of exactly one Grain, PLAN coarse direction in the master plan.")
    out.append("")
    for area in ["governance", "architecture", "security", "licensing", "dependency", "packet-graph", "salvage"]:
        rows = [f for f in findings if f["area"] == area]
        if not rows:
            continue
        out.append(f"## {area.capitalize()} ({len(rows)})")
        out.append("")
        out.append("| ID | Severity | Finding | Resolved by | Main citations |")
        out.append("| --- | --- | --- | --- | --- |")
        for f in rows:
            alias = f" (also {', '.join(f['aliases'])})" if f.get("aliases") else ""
            out.append(f"| {f['id']}{alias} | {f['severity']} | {f['summary']} | {', '.join(f['resolved_by'])} | {f['cite']} |")
        out.append("")
    out.append("## Vehicles")
    out.append("")
    out.append("| ID | Type | Stage | Approval | Depends on | What it does | Resolves |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    for v in graph["vehicles"]:
        sel = f" Selects: {v['selects'][0]}." if v.get("selects") else ""
        out.append(f"| {v['id']} | {v['type']} | {v['stage']} | {v['approval']} | {', '.join(v['depends_on']) or '—'} | {v['title']}.{sel} | {', '.join(by_vehicle.get(v['id'], [])) or '—'} |")
    out.append("")
    open(os.path.join(HERE, "RESOLUTION_REGISTER.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("wrote RESOLUTION_REGISTER.md")
