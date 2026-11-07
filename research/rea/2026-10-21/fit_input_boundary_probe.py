"""Research-only Q-02 boundary experiment; never imported by product code.

The donor stays byte-for-byte unchanged. No audio/models or dependencies load.
"""
import argparse
from dataclasses import asdict, fields
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest

PIN = "28bf2c7a83b8a64836297340c52a45d716684aed"
SOURCE_SHA256 = "0acd7c33623782cafa975f1f81cbe37362160490e8bdd34ca15f5c2b06321442"


class InvalidFitInput(ValueError):
    """Typed rejection at the WisprStudio input boundary."""


def number(value, label, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidFitInput(f"{label}: numeric value required")
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise InvalidFitInput(f"{label}: finite {'positive' if positive else 'nonnegative'} value required")
    return value


def validate_fit_inputs(segments, natural_durs_s, total_dur_s, params=None, *, allow_silence=False):
    if not isinstance(segments, list) or not isinstance(natural_durs_s, list) or len(segments) != len(natural_durs_s):
        raise InvalidFitInput("parallel segment/duration lists required")
    total = number(total_dur_s, "total", positive=bool(segments))
    previous_end = 0.0
    for index, (segment, natural) in enumerate(zip(segments, natural_durs_s)):
        if not isinstance(segment, dict) or "start" not in segment or "end" not in segment:
            raise InvalidFitInput(f"segment {index}: start/end required")
        start = number(segment["start"], "start")
        end = number(segment["end"], "end", positive=True)
        number(natural, "natural duration", positive=not allow_silence)
        if end <= start or start < previous_end or end > total:
            raise InvalidFitInput("zero/inverted/unsorted/overlapping/out-of-total segment")
        previous_end = end
    if params is not None:
        for field in fields(params):
            value = getattr(params, field.name)
            if not isinstance(value, bool):
                number(value, field.name, positive=field.name != "gap_guard_s")


def guarded_plan(donor, segments, naturals, total, params=None, *, allow_silence=False):
    validate_fit_inputs(segments, naturals, total, params, allow_silence=allow_silence)
    plan = donor.plan_fit(segments, naturals, total, params)
    # Finite input can overflow arithmetic. No corrupt plan crosses the boundary.
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise InvalidFitInput("non-finite computed plan")
        if isinstance(value, dict):
            for child in value.values(): finite(child)
        if isinstance(value, list):
            for child in value: finite(child)
    finite(asdict(plan))
    return plan


def run(source_root, output):
    source = source_root / "backend/services/fit_planner.py"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    if before != SOURCE_SHA256:
        raise ValueError("Pinned donor SHA-256 mismatch")
    spec = importlib.util.spec_from_file_location("unchanged_fit_donor", source)
    donor = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = donor
    spec.loader.exec_module(donor)
    results = []
    class BoundaryTests(unittest.TestCase):
        def test_invalid_inputs(self):
            cases = {
                "nan_natural": ([{"start": 0., "end": 1.}], [math.nan], 2.),
                "infinite_natural": ([{"start": 0., "end": 1.}], [math.inf], 2.),
                "negative_natural": ([{"start": 0., "end": 1.}], [-1.], 2.),
                "zero_natural_without_silence": ([{"start": 0., "end": 1.}], [0.], 2.),
                "zero_segment_span": ([{"start": 1., "end": 1.}], [1.], 2.),
                "inverted": ([{"start": 2., "end": 1.}], [1.], 3.),
                "overlap": ([{"start": 0., "end": 2.}, {"start": 1., "end": 3.}], [1., 1.], 4.),
                "unsorted": ([{"start": 2., "end": 3.}, {"start": 0., "end": 1.}], [1., 1.], 4.),
                "negative_start": ([{"start": -1., "end": 1.}], [1.], 2.),
                "nan_total": ([{"start": 0., "end": 1.}], [1.], math.nan),
                "infinite_total": ([{"start": 0., "end": 1.}], [1.], math.inf),
                "negative_total": ([], [], -1.),
                "zero_total_nonempty": ([{"start": 0., "end": 1.}], [1.], 0.),
                "infinite_end": ([{"start": 0., "end": math.inf}], [1.], 3.),
                "length_mismatch": ([{"start": 0., "end": 1.}], [], 2.),
                "boolean_duration": ([{"start": 0., "end": 1.}], [True], 2.),
            }
            for name, args in cases.items():
                with self.subTest(name=name):
                    with self.assertRaises(InvalidFitInput): guarded_plan(donor, *args)
                    results.append({"case": name, "status": "PASS", "outcome": "typed rejection"})

        def test_zero_semantics(self):
            self.assertEqual(asdict(guarded_plan(donor, [], [], 0.)), asdict(donor.plan_fit([], [], 0.)))
            args = ([{"start": 0., "end": 1.}], [0.], 1.)
            self.assertEqual(asdict(guarded_plan(donor, *args, allow_silence=True)), asdict(donor.plan_fit(*args)))
            results.append({"case": "explicit_silence_and_empty_zero_total", "status": "PASS"})

        def test_valid_golden_outputs_unchanged(self):
            scenarios = {
                "all_fit": ([0., 3.], [2., 5.], [1.5, 2.5], 6., None),
                "audio_only_and_hybrid": ([0., 1.5, 3.], [1., 2.5, 4.], [1.6, 2., .4], 5., None),
                "overflow_caps": ([.5, 2.], [1.5, 3.], [5., 1.], 3.5, None),
                "no_video_retime": ([0., 2.], [1., 3.], [2.5, 1.3], 4., donor.FitParams(allow_video_retime=False)),
            }
            for name, (starts, ends, naturals, total, params) in scenarios.items():
                segments = [{"id": f"g{i}", "start": start, "end": end} for i, (start, end) in enumerate(zip(starts, ends))]
                direct = donor.plan_fit(segments, naturals, total, params)
                guarded = guarded_plan(donor, segments, naturals, total, params)
                self.assertEqual(asdict(direct), asdict(guarded))
                payload = {key: asdict(guarded)[key] for key in ["segments", "video_plan", "total_duration", "orig_duration"]}
                fixture = source_root / "tests/fixtures/fit_planner" / (name + ".json")
                expected = json.loads(fixture.read_text(encoding="utf-8"))
                self.assertEqual(payload, expected)
                results.append({"case": "golden_" + name, "status": "PASS", "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest()})
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryTests))
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    report = {"status": "PASS" if result.wasSuccessful() and before == after else "FAIL", "source_revision": PIN,
              "donor_sha256_before": before, "donor_sha256_after": after, "python": sys.version,
              "cases": results, "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "limits": ["Research-only boundary experiment, not product code", "No audio/model/native behavior tested", "Full upstream pytest suite NOT_RUN; pure golden cases and new boundary tests only", "JSON golden objects match; donor file bytes unchanged"]}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.source_root, args.output))
