"""Summarize ST-D00 HW-A run 4: JUnit totals, failures by file, probe-attributed egress, and the
TCP watcher's non-loopback Python connections matched to tests running at that moment.
Usage: python -I st_d00_analyze.py <run_dir> <hung_tests.txt>"""
import collections
import datetime as dt
import glob
import ipaddress
import json
import os
import socket
import sys
import xml.etree.ElementTree as ET

RUN, HUNG = sys.argv[1], sys.argv[2]
tot = collections.Counter()
fails = []
for f in sorted(glob.glob(os.path.join(RUN, "junit-*.xml"))):
    root = ET.parse(f).getroot()
    for tc in root.iter("testcase"):
        tot["tests"] += 1
        node = f"{tc.get('classname')}::{tc.get('name')}"
        kinds = [c.tag for c in tc]
        if "failure" in kinds:
            tot["failed"] += 1; fails.append(("FAILED", tc.get("file") or tc.get("classname"), node, (tc.find("failure").get("message") or "")[:160]))
        elif "error" in kinds:
            tot["error"] += 1; fails.append(("ERROR", tc.get("file") or tc.get("classname"), node, (tc.find("error").get("message") or "")[:160]))
        elif "skipped" in kinds:
            tot["skipped"] += 1
        else:
            tot["passed"] += 1
hung = [l.split("\t")[0] for l in open(HUNG, encoding="utf-8") if l.strip()]
print("TOTALS", dict(tot), "hung_deselected", len(hung))
byfile = collections.Counter(k + " " + c.rsplit(".", 1)[0] for k, c, n, m in fails)
print("FAILURES_BY_FILE")
for k, v in byfile.most_common():
    print(f"  {v:3d} {k}")

print("PROBE_EGRESS (Python sockets, attributed)")
seen = collections.Counter()
for f in glob.glob(os.path.join(RUN, "probe", "egress-*.jsonl")):
    for line in open(f, encoding="utf-8"):
        r = json.loads(line)
        seen[(r["kind"], r["host"], r["port"], r["test"], " <- ".join(r["stack"][-3:]))] += 1
for (kind, host, port, test, stack), n in sorted(seen.items(), key=lambda x: (x[0][3] or "", x[0][1])):
    print(f"  {n:3d} {kind} {host}:{port} test={test}\n        {stack[:260]}")

# Timeline: test intervals
spans = []
for f in glob.glob(os.path.join(RUN, "probe", "timeline-*.tsv")):
    start = {}
    for line in open(f, encoding="utf-8"):
        t, ev, node = line.rstrip("\n").split("\t", 2)
        if ev == "start":
            start[node] = float(t)
        elif ev == "end" and node in start:
            spans.append((start.pop(node), float(t), node))
print("TIMELINE_SPANS", len(spans))

hf = set()
for name in ("huggingface.co", "us.aws.cdn.hf.co", "cas-bridge.xethub.hf.co", "cdn-lfs.huggingface.co", "hf.co"):
    try:
        hf |= {ai[4][0] for ai in socket.getaddrinfo(name, 443)}
    except OSError:
        pass
print("HF_ADDRESSES_NOW", sorted(hf))
print("TCP_WATCHER python connections (non-loopback)")
for f in sorted(glob.glob(os.path.join(RUN, "egress-tcp-*.txt"))):
    for line in open(f, encoding="utf-8-sig", errors="replace"):
        if line.startswith("#") or "proc=python" not in line:
            continue
        ts, state, ep = line.split()[:3]
        ip = ep.rsplit(":", 1)[0]
        try:
            if ipaddress.ip_address(ip.strip("[]")).is_private:
                continue
        except ValueError:
            pass
        t = dt.datetime.fromisoformat(ts[:26] + ts[27:] if len(ts) > 32 else ts).timestamp()
        running = sorted({n for s, e, n in spans if s - 1.5 <= t <= e + 1.5})
        tag = "HF" if ip in hf else ""
        print(f"  {ts} {state} {ep} {tag} candidates={running[:8]}")
