# Wispral 000E ST-D00 egress attribution: load the observation-only socket probe in every Python
# process that has this directory on PYTHONPATH (pytest workers and the subprocesses tests start).
try:
    import wispral_probe  # noqa: F401
except Exception:
    pass
