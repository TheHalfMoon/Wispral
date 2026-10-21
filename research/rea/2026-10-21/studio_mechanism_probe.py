"""Bounded source-mechanism experiments; no models, audio, network or product code.

Run with a caller-owned source cache acquired at the pins in
studio-source-evidence.json. This probes real donor modules unchanged, not a
reimplementation. It is not an application REA or a speech benchmark.
"""
import argparse
import asyncio
import dataclasses
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.request import urlopen


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


async def queue_probes(queue):
    queue.init_queue()
    observed = []

    async def ignored():
        observed.append("should-not-run")

    queue.enqueue_generation("synthetic-queued", ignored())
    first = queue.cancel_generation("synthetic-queued")
    await asyncio.wait_for(queue._generation_queue.join(), timeout=2)
    assert first == "queued" and observed == []
    started = asyncio.Event()
    stopped = asyncio.Event()

    async def active():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    queue.enqueue_generation("synthetic-running", active())
    await asyncio.wait_for(started.wait(), timeout=2)
    second = queue.cancel_generation("synthetic-running")
    await asyncio.wait_for(stopped.wait(), timeout=2)
    await asyncio.wait_for(queue._generation_queue.join(), timeout=2)
    assert second == "running"
    unknown = queue.cancel_generation("unknown-id")
    assert unknown is None
    queue._generation_worker_task.cancel()
    try:
        await queue._generation_worker_task
    except asyncio.CancelledError:
        pass
    return {"queued_cancel": first, "queued_work_executed": observed,
            "running_cancel": second, "coroutine_finally_observed": stopped.is_set(),
            "unknown_job": unknown,
            "limitation": "No native inference thread/process or GPU was running."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--acquire", action="store_true",
                        help="Fetch only the three exact pinned source files, never model weights")
    args = parser.parse_args()
    root = Path(args.source_root)
    files = {
        "fit": root / "debpalash__VoiceStudio/backend/services/fit_planner.py",
        "cancellation": root / "debpalash__VoiceStudio/backend/services/inference_cancellation.py",
        "queue": root / "jamiepine__voicebox/backend/services/task_queue.py",
    }
    manifest = json.loads(Path(__file__).with_name("studio-source-evidence.json").read_text(encoding="utf8"))
    pins = {"fit": "ST-FIT", "cancellation": "ST-CANCEL-SCOPE", "queue": "VB-QUEUE"}
    for name, file in files.items():
        entry = next(row for row in manifest["mechanisms"] if row["id"] == pins[name])
        if args.acquire:
            url = f"https://raw.githubusercontent.com/{entry['repo']}/{entry['sha']}/{entry['path']}"
            with urlopen(url, timeout=30) as response:
                data = response.read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                raise ValueError("Source file exceeded bounded acquisition size")
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError("Acquired source SHA-256 differs from the pinned evidence")
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
        if hashlib.sha256(file.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"{name}: local source SHA-256 differs from the pinned evidence")
    modules = {name: load("studio_probe_" + name, file) for name, file in files.items()}
    fit = modules["fit"]
    seg = [{"id": "synthetic-1", "start": 0.0, "end": 2.0}]
    ordinary = fit.plan_fit(seg, [2.0], 2.0)
    assert ordinary.segments[0].status == "fits"
    overflow = fit.plan_fit(seg, [12.0], 2.0, fit.FitParams(allow_video_retime=False))
    assert overflow.segments[0].status == "overflow_trimmed"
    assert overflow.segments[0].audio_rate == 1.8
    rejected = None
    try:
        fit.plan_fit(seg, [], 2.0)
    except ValueError as error:
        rejected = str(error)
    assert rejected is not None
    scope = modules["cancellation"].InferenceCancellation()
    assert modules["cancellation"].current_cancellation() is None
    with scope.activate():
        assert modules["cancellation"].current_cancellation() is scope
    assert modules["cancellation"].current_cancellation() is None
    scope.cancel()
    cancellation_rejected = None
    try:
        with scope.activate():
            raise AssertionError("Cancelled inference must not enter scope")
    except RuntimeError as error:
        cancellation_rejected = str(error)
    result = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "method": "UNCHANGED_DONOR_MODULE_EXECUTION_WITH_SYNTHETIC_NON_AUDIO_FIXTURES",
        "status": "REPRODUCED", "application_rea": False,
        "python": sys.version, "os": platform.platform(),
        "source_sha256": {name: hashlib.sha256(file.read_bytes()).hexdigest()
                          for name, file in files.items()},
        "fit_ordinary": dataclasses.asdict(ordinary),
        "fit_overflow": dataclasses.asdict(overflow),
        "parallel_length_mismatch": rejected,
        "cancelled_scope_rejection": cancellation_rejected,
        "cancellation_thread_local_restored": True,
        "queue": asyncio.run(queue_probes(modules["queue"])),
        "not_run": ["TTS inference", "voice cloning", "model downloads",
                    "full donor test suite", "native process cancellation",
                    "GPU cancellation", "subjective voice quality", "latency benchmark"],
    }
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"status": result["status"], "probes": 8,
                      "models_loaded": 0, "audio_processed": False}))


if __name__ == "__main__":
    main()
