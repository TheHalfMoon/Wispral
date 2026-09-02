#!/usr/bin/env python3
"""Fail closed on the bounded 000B2 public-corpus methodology contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"PUBLIC_CORPUS_METHODOLOGY=FAIL: {message}")


def main() -> None:
    readiness_path = ROOT / "research/000b2-public/readiness.json"
    spec_path = ROOT / "specs/000B2-public-corpus-bakeoff/spec.md"
    plan_path = ROOT / "specs/000B2-public-corpus-bakeoff/plan.md"
    tasks_path = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
    current_path = ROOT / "specs/CURRENT.md"
    founding_tasks_path = ROOT / "specs/000-founding-research/tasks.md"

    for path in (
        readiness_path,
        spec_path,
        plan_path,
        tasks_path,
        current_path,
        founding_tasks_path,
    ):
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")

    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    require(readiness["schema_version"] == "000b2-public-readiness-v1", "schema version drift")
    require(readiness["lane"] == "PUBLIC_CORPUS", "lane drift")
    require(
        readiness["state"] == "READY_CANDIDATE_PENDING_CANONICALIZATION",
        "candidate must not self-claim canonical readiness",
    )

    historical = readiness["historical_private_collection_lane"]
    require(historical["preserved"] is True, "historical lane must remain preserved")
    require(historical["executed"] is False, "historical private lane must remain unexecuted")
    require(
        historical["primary_decoding_performed"] is False,
        "historical private lane must not claim primary decoding",
    )
    require(historical["active_entry_gate"] is False, "historical private lane must not remain active gate")

    public = readiness["public_human_baseline"]
    require(public["corpus"] == "LibriSpeech ASR corpus SLR12", "unexpected public corpus")
    require(public["license"] == "CC BY 4.0", "license drift")
    expected_md5 = {
        "test-clean.tar.gz": "32fa31d27d2e1cad72775fee3f4849a9",
        "test-other.tar.gz": "fb5a50374b501bb3bac4815ee91d3135",
    }
    observed = {item["name"]: item["official_md5"] for item in public["partitions"]}
    require(observed == expected_md5, "OpenSLR official checksum contract drift")
    require(public["subset_manifest_frozen"] is False, "subset must not be pre-claimed frozen")
    require(public["candidate_decoding_started"] is False, "candidate decoding must not start on amendment")

    diagnostic = readiness["developer_term_diagnostic"]
    require(diagnostic["synthetic_only"] is True, "developer diagnostic must remain synthetic-only")
    require(
        diagnostic["human_accuracy_claim_eligible"] is False,
        "synthetic diagnostic must never become human accuracy evidence",
    )

    guards = readiness["claim_guards"]
    require(
        guards["human_developer_speech_accuracy_evidence"] == "ABSENT",
        "human developer-speech evidence must remain explicitly absent",
    )
    require(guards["production_stt_selected"] is False, "methodology amendment cannot select production STT")
    require(guards["product_code_authorized"] is False, "methodology amendment cannot authorize product code")

    spec = spec_path.read_text(encoding="utf-8")
    current = current_path.read_text(encoding="utf-8")
    founding_tasks = founding_tasks_path.read_text(encoding="utf-8")

    required_phrases = (
        "HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT",
        "DIAGNOSTIC_ONLY",
        "CC BY 4.0",
        "32fa31d27d2e1cad72775fee3f4849a9",
        "fb5a50374b501bb3bac4815ee91d3135",
    )
    for phrase in required_phrases:
        require(phrase in spec, f"spec missing required phrase: {phrase}")
        require(phrase in current, f"current frontier missing required phrase: {phrase}")

    require("`000B2-unbiased-stt-bakeoff`" in current, "historical B2 marker missing")
    historical_section = current[current.index("`000B2-unbiased-stt-bakeoff`") :]
    require("State: `BLOCKED_EXTERNAL`" in historical_section[:512], "historical B2 lane must remain blocked")
    require("`000B2-public-corpus-bakeoff`" in current, "public successor marker missing")
    require("production Rust/Cargo speech code" in founding_tasks, "product-code prohibition missing")
    require("private 20-speaker" in founding_tasks, "historical private-path preservation missing")

    print("PUBLIC_CORPUS_METHODOLOGY=PASS")
    print("HISTORICAL_PRIVATE_B2=BLOCKED_EXTERNAL")
    print("PRIVATE_COLLECTION_HISTORY=PRESERVED_UNEXECUTED")
    print("PUBLIC_HUMAN_BASELINE=LIBRISPEECH_SLR12")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    print("PRODUCT_CODE_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
