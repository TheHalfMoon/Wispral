#!/usr/bin/env python3
"""Regression tests for the frozen B2 public-corpus WER adapter."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/000b2-public"
ADAPTER_PATH = HERE / "score_public_wer.py"


def fail(message: str) -> None:
    raise SystemExit(f"B2P08_PUBLIC_WER_VERIFIER=FAIL: {message}")


def load_adapter():
    spec = importlib.util.spec_from_file_location("wispral_b2_public_wer", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        fail("unable to load adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_subset() -> dict:
    utterances = []
    for index in range(240):
        utterances.append(
            {
                "utterance_id": f"u-{index:03d}",
                "reference_transcript": "HELLO, WORLD!" if index == 0 else "ONE TWO",
            }
        )
    return {
        "membership": {
            "partitions": [
                {
                    "name": "fixture",
                    "speakers": [
                        {"speaker_id": "fixture", "utterances": utterances}
                    ],
                }
            ]
        }
    }


def expect_failure(callable_obj, label: str) -> None:
    try:
        callable_obj()
    except Exception:
        return
    fail(f"{label} was accepted")


def main() -> int:
    adapter = load_adapter()
    contract = adapter.verify_normalization_contract()
    if contract.get("algorithm") != "UNIT_COST_LEVENSHTEIN":
        fail("algorithm drift")

    canonical_subset = adapter.load_json(adapter.DEFAULT_SUBSET, "canonical subset")
    if not isinstance(canonical_subset, dict):
        fail("canonical subset root drift")
    adapter.verify_canonical_subset(canonical_subset)

    tampered_subset = copy.deepcopy(canonical_subset)
    first_partition = tampered_subset["membership"]["partitions"][0]
    first_speaker = first_partition["speakers"][0]
    first_utterance = first_speaker["utterances"][0]
    first_utterance["reference_transcript"] += " TAMPERED"
    expect_failure(
        lambda: adapter.verify_canonical_subset(tampered_subset),
        "tampered canonical subset with copied freeze digest",
    )

    original_scorer_path = adapter.SCORER_PATH
    original_config_path = adapter.SCORER_CONFIG_PATH
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        tampered_scorer = temp / "scorer.py"
        tampered_scorer.write_bytes(original_scorer_path.read_bytes() + b"\n# tampered\n")
        adapter.SCORER_PATH = tampered_scorer
        expect_failure(adapter.load_core_scorer, "tampered core scorer implementation")
        adapter.SCORER_PATH = original_scorer_path

        tampered_config = temp / "scorer-config.json"
        config = json.loads(original_config_path.read_text(encoding="utf-8"))
        config["ordinary_wer"]["casefold"] = False
        tampered_config.write_text(
            json.dumps(config, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        adapter.SCORER_CONFIG_PATH = tampered_config
        expect_failure(adapter.verify_normalization_contract, "tampered core scorer config")
        adapter.SCORER_CONFIG_PATH = original_config_path

    subset = synthetic_subset()
    predictions = []
    for index in range(240):
        predictions.append(
            {
                "utterance_id": f"u-{index:03d}",
                "outcome": "SUCCESS",
                "hypothesis": "hello world" if index == 0 else "ONE TWO",
            }
        )

    result = adapter.score_predictions(subset, predictions, require_canonical_subset=False)
    if result["utterance_count"] != 240 or result["failure_count"] != 0:
        fail("perfect fixture count drift")
    if result["errors"] != 0 or result["wer"] != 0:
        fail("NFC/casefold/punctuation normalization regression")

    changed = [dict(row) for row in predictions]
    changed[1] = {"utterance_id": "u-001", "outcome": "SUCCESS", "hypothesis": "ONE THREE"}
    changed[2] = {"utterance_id": "u-002", "outcome": "SUCCESS", "hypothesis": "ONE"}
    changed[3] = {"utterance_id": "u-003", "outcome": "SUCCESS", "hypothesis": "ONE TWO THREE"}
    scored = adapter.score_predictions(subset, changed, require_canonical_subset=False)
    if (scored["substitutions"], scored["deletions"], scored["insertions"]) != (1, 1, 1):
        fail("Levenshtein operation accounting drift")
    if scored["errors"] != 3:
        fail("aggregate error accounting drift")

    failure_case = [dict(row) for row in predictions]
    failure_case[4] = {"utterance_id": "u-004", "outcome": "TIMEOUT", "hypothesis": ""}
    failure_result = adapter.score_predictions(subset, failure_case, require_canonical_subset=False)
    if failure_result["failure_count"] != 1:
        fail("failure count drift")
    if failure_result["deletions"] != 2:
        fail("non-success must score as empty hypothesis")

    invalid = [dict(row) for row in predictions]
    invalid[4] = {"utterance_id": "u-004", "outcome": "TIMEOUT", "hypothesis": "leak"}
    expect_failure(
        lambda: adapter.score_predictions(subset, invalid, require_canonical_subset=False),
        "non-success transcript leakage",
    )

    missing = predictions[:-1]
    expect_failure(
        lambda: adapter.score_predictions(subset, missing, require_canonical_subset=False),
        "missing prediction",
    )

    print("B2P08_PUBLIC_WER_VERIFIER=PASS")
    print("B2P08_PUBLIC_WER_NORMALIZATION=NFC_CASEFOLD_PUNCT_SYMBOL_TO_SPACE")
    print("B2P08_PUBLIC_WER_ALGORITHM=UNIT_COST_LEVENSHTEIN")
    print("B2P08_PUBLIC_WER_CANONICAL_SUBSET_IDENTITY=BOUND")
    print("B2P08_PUBLIC_WER_CORE_SCORER_IDENTITY=BOUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
