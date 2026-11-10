"""Wispral 000E ST-D00 test-harness plugin (not part of the donor; loaded with `-p wispral_probe`).

Two observation-only functions:

1. Egress attribution. Wraps socket.getaddrinfo and socket.socket.connect / connect_ex, and records
   every attempt to reach a non-loopback host as one JSON line, with the running test's node ID and
   the non-stdlib call stack. It never blocks or alters a call.
2. Hang guard. If a single test runs longer than WISPRAL_TEST_LIMIT_S (default 600 s), it writes
   all thread stacks and ends the worker process (os._exit(70)). pytest-xdist reports the test as
   failed with a crashed worker and starts a replacement, so one hang cannot stall the whole suite.

Output directory: WISPRAL_PROBE_DIR (one egress-<pid>.jsonl and hang-<pid>.txt per process).
"""
import faulthandler
import ipaddress
import json
import os
import socket
import sys
import threading
import time
import traceback

OUT = os.environ.get("WISPRAL_PROBE_DIR", ".")
LIMIT = float(os.environ.get("WISPRAL_TEST_LIMIT_S", "600"))
_current = {"nodeid": None}
_lock = threading.Lock()
_orig_getaddrinfo = socket.getaddrinfo
_orig_connect = socket.socket.connect
_orig_connect_ex = socket.socket.connect_ex


def _local(host):
    if host is None:
        return True
    h = str(host).strip("[]").lower()
    if h in ("localhost", "", "0.0.0.0"):
        return True
    try:
        ip = ipaddress.ip_address(h.split("%")[0])
        return ip.is_loopback or ip.is_unspecified
    except ValueError:
        return h.endswith(".localhost")


def _stack():
    frames = []
    for f in traceback.extract_stack()[:-3]:
        p = f.filename.replace("\\", "/")
        if "/Lib/" in p and "site-packages" not in p:
            continue  # standard library
        if p.endswith("wispral_probe.py"):
            continue
        short = p.split("site-packages/")[-1] if "site-packages/" in p else p.split("/vs/")[-1]
        frames.append(f"{short}:{f.lineno}:{f.name}")
    return frames[-12:]


def _log(kind, host, port):
    if _local(host):
        return
    rec = {"t": time.time(), "pid": os.getpid(), "test": _current["nodeid"], "kind": kind,
           "host": str(host), "port": port, "stack": _stack()}
    with _lock:
        with open(os.path.join(OUT, f"egress-{os.getpid()}.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")


def _getaddrinfo(host, port, *a, **k):
    try:
        _log("getaddrinfo", host, port)
    except Exception:
        pass
    return _orig_getaddrinfo(host, port, *a, **k)


def _addr(address):
    if isinstance(address, tuple) and len(address) >= 2:
        return address[0], address[1]
    return None, None


def _connect(self, address):
    try:
        _log("connect", *_addr(address))
    except Exception:
        pass
    return _orig_connect(self, address)


def _connect_ex(self, address):
    try:
        _log("connect_ex", *_addr(address))
    except Exception:
        pass
    return _orig_connect_ex(self, address)


socket.getaddrinfo = _getaddrinfo
socket.socket.connect = _connect
socket.socket.connect_ex = _connect_ex


def _expire(nodeid):
    path = os.path.join(OUT, f"hang-{os.getpid()}.txt")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"HANG_LIMIT_EXCEEDED {LIMIT}s test={nodeid} t={time.time()}\n")
        fh.flush()
        faulthandler.dump_traceback(file=fh, all_threads=True)
    os._exit(70)


def _timeline(event, nodeid):
    with _lock:
        with open(os.path.join(OUT, f"timeline-{os.getpid()}.tsv"), "a", encoding="utf-8") as fh:
            fh.write(f"{time.time():.3f}\t{event}\t{nodeid}\n")


def pytest_runtest_protocol(item, nextitem):
    _current["nodeid"] = item.nodeid
    _timeline("start", item.nodeid)
    timer = threading.Timer(LIMIT, _expire, args=(item.nodeid,))
    timer.daemon = True
    timer.start()
    item._wispral_timer = timer


def pytest_runtest_logfinish(nodeid, location):
    _timeline("end", nodeid)
    _current["nodeid"] = None


def pytest_runtest_teardown(item, nextitem):
    pass


def pytest_runtest_makereport(item, call):
    if call.when == "teardown":
        t = getattr(item, "_wispral_timer", None)
        if t is not None:
            t.cancel()


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        _timeline("outcome:" + report.outcome + ":" + report.when, report.nodeid)
