# Wispral attribution, fail-closed variant: any non-loopback name lookup raises and dumps the full
# Python stack, so nothing is downloaded and the caller is visible. Observation tool, not donor code.
import os, socket, traceback, ipaddress
_orig = socket.getaddrinfo
OUT = os.environ.get("WISPRAL_BLOCK_OUT", "block.txt")
def _local(h):
    h = str(h).strip("[]").lower()
    if h in ("localhost", "", "0.0.0.0", "none"):
        return True
    try:
        ip = ipaddress.ip_address(h.split("%")[0]); return ip.is_loopback or ip.is_unspecified
    except ValueError:
        return h.endswith(".localhost")
def _gai(host, port, *a, **k):
    if not _local(host):
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(f"BLOCKED {host}:{port} pid={os.getpid()} test={os.environ.get('PYTEST_CURRENT_TEST')}\n")
            f.write("".join(traceback.format_stack()) + "\n")
        raise socket.gaierror(socket.EAI_NONAME, "blocked by wispral attribution probe")
    return _orig(host, port, *a, **k)
socket.getaddrinfo = _gai
