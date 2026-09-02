#!/usr/bin/env python3
"""Fail closed on the bounded 000B2 public-corpus methodology contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"PUBLIC_CORPUS_METHODOLOGY=FAIL: {message}")


def require_text(text: str, phrase: str, label: str) -> None:
    require(phrase in text, f"{label} missing required text: {phrase}")


def require_bool(mapping: dict[str, Any], key: str, expected: bool, label: str) -> None:
    require(mapping.get(key) is expected, f"{label}.{key} must be {expected}")


def require_exact_keys(mapping: dict[str, Any], expected: set[str], label: str) -> None:
    require(set(mapping) == expected, f"{label} keys drift: expected {sorted(expected)}, got {sorted(mapping)}")


def main() -> None:
    readiness_path = ROOT / "research/000b2-public/readiness.json"
    corpus_source_path = ROOT / "research/000b2-public/corpus-source.json"
    spec_path = ROOT / "specs/000B2-public-corpus-bakeoff/spec.md"
    plan_path = ROOT / "specs/000B2-public-corpus-bakeoff/plan.md"
    tasks_path = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
    parent_spec_path = ROOT / "specs/000B-stt-entity-bakeoff/spec.md"
    parent_plan_path = ROOT / "specs/000B-stt-entity-bakeoff/plan.md"
    parent_tasks_path = ROOT / "specs/000B-stt-entity-bakeoff/tasks.md"
    current_path = ROOT / "specs/CURRENT.md"
    founding_tasks_path = ROOT / "specs/000-founding-research/tasks.md"

    required_paths = (
        readiness_path,
        corpus_source_path,
        spec_path,
        plan_path,
        tasks_path,
        parent_spec_path,
        parent_plan_path,
        parent_tasks_path,
        current_path,
        founding_tasks_path,
    )
    for path in required_paths:
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")

    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    require(isinstance(readiness, dict), "readiness root must be an object")
    require(readiness.get("schema_version") == "000b2-public-readiness-v1", "schema version drift")
    require(readiness.get("lane") == "PUBLIC_CORPUS", "lane drift")
    require(
        readiness.get("state") == "READY",
        "canonical public execution readiness must be explicit",
    )

    historical = readiness.get("historical_private_collection_lane")
    require(isinstance(historical, dict), "historical private lane must be an object")
    require_bool(historical, "preserved", True, "historical_private_collection_lane")
    require_bool(historical, "executed", False, "historical_private_collection_lane")
    require_bool(historical, "primary_decoding_performed", False, "historical_private_collection_lane")
    require_bool(historical, "active_entry_gate", False, "historical_private_collection_lane")

    public = readiness.get("public_human_baseline")
    require(isinstance(public, dict), "public human baseline must be an object")
    require(public.get("corpus") == "LibriSpeech ASR corpus SLR12", "unexpected public corpus")
    require(public.get("upstream") == "https://www.openslr.org/12/", "OpenSLR source drift")
    require(public.get("license") == "CC BY 4.0", "license drift")
    require(
        public.get("claim_scope") == "BOUNDED_ORDINARY_READ_ENGLISH_ONLY",
        "public-human claim scope drift",
    )
    require_bool(public, "subset_manifest_frozen", False, "public_human_baseline")
    require_bool(public, "candidate_decoding_started", False, "public_human_baseline")

    expected_md5 = {
        "test-clean.tar.gz": "32fa31d27d2e1cad72775fee3f4849a9",
        "test-other.tar.gz": "fb5a50374b501bb3bac4815ee91d3135",
    }
    partitions = public.get("partitions")
    require(isinstance(partitions, list) and len(partitions) == 2, "exactly two public partitions are required")
    observed_names: set[str] = set()
    for item in partitions:
        require(isinstance(item, dict), "partition record must be an object")
        name = item.get("name")
        require(isinstance(name, str) and name in expected_md5, f"unexpected public partition: {name!r}")
        require(name not in observed_names, f"duplicate public partition: {name}")
        observed_names.add(name)
        require(item.get("official_md5") == expected_md5[name], f"official MD5 drift for {name}")
        require(item.get("archive_sha256") is None, f"{name} must not pre-claim fetched-byte SHA-256")
        require_bool(item, "materialized", False, f"partition[{name}]")
    require(observed_names == set(expected_md5), "public partition set drift")

    diagnostic = readiness.get("developer_term_diagnostic")
    require(isinstance(diagnostic, dict), "developer diagnostic must be an object")
    require(diagnostic.get("status") == "OPTIONAL_NOT_FROZEN", "developer diagnostic status drift")
    require_bool(diagnostic, "synthetic_only", True, "developer_term_diagnostic")
    require_bool(diagnostic, "human_accuracy_claim_eligible", False, "developer_term_diagnostic")
    require_bool(diagnostic, "may_be_not_run", True, "developer_term_diagnostic")

    registry = readiness.get("candidate_registry")
    require(isinstance(registry, dict), "candidate registry must be an object")
    require_bool(registry, "reuse_canonical_b1_b2_entry_cells", True, "candidate_registry")
    require_bool(registry, "revalidation_required_before_decode", True, "candidate_registry")

    preprocessing = readiness.get("preprocessing")
    require(isinstance(preprocessing, dict), "preprocessing contract must be an object")
    require(preprocessing.get("required_tool") == "FFmpeg 9.0.1", "preprocessing tool drift")
    require_bool(preprocessing, "attempt_bound_capture_required", True, "preprocessing")
    require_bool(preprocessing, "resolved", False, "preprocessing")

    environment = readiness.get("execution_environment")
    require(isinstance(environment, dict), "execution environment contract must be an object")
    require_bool(environment, "attempt_bound_capture_required", True, "execution_environment")
    require_bool(environment, "resolved", False, "execution_environment")
    require(
        environment.get("hosted_runner_performance_mode") == "DIAGNOSTIC_ONLY",
        "hosted-runner performance claim boundary drift",
    )

    attempt = readiness.get("attempt_manifest")
    require(isinstance(attempt, dict), "attempt manifest state must be an object")
    require_bool(attempt, "frozen", False, "attempt_manifest")
    require_bool(attempt, "primary_decoding_started", False, "attempt_manifest")

    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "claim guards must be an object")
    require(
        guards.get("human_developer_speech_accuracy_evidence") == "ABSENT",
        "human developer-speech evidence must remain explicitly absent",
    )
    require_bool(guards, "synthetic_developer_media_is_human_evidence", False, "claim_guards")
    require_bool(guards, "production_stt_selected", False, "claim_guards")
    require_bool(guards, "product_code_authorized", False, "claim_guards")

    next_action = readiness.get("next_action")
    expected_next_action = (
        "Execute B2P01 only: reverify and record the exact OpenSLR SLR12 source/license facts and "
        "official archive checksums in machine-readable provenance. Do not materialize corpus archives "
        "or begin B2P02 until B2P01 is canonical."
    )
    require(next_action == expected_next_action, "next action must be the exact B2P01-only instruction")

    corpus_source = json.loads(corpus_source_path.read_text(encoding="utf-8"))
    require(isinstance(corpus_source, dict), "corpus-source root must be an object")
    require_exact_keys(
        corpus_source,
        {
            "schema_version",
            "task",
            "state",
            "verified_on",
            "resource",
            "partitions",
            "verification",
            "claim_guards",
            "next_task_after_canonicalization",
        },
        "corpus_source",
    )
    require(corpus_source.get("schema_version") == "000b2-public-corpus-source-v1", "corpus-source schema drift")
    require(corpus_source.get("task") == "B2P01", "corpus-source task must be B2P01")
    require(corpus_source.get("state") == "FROZEN_SOURCE_PROVENANCE", "corpus-source state drift")
    require(corpus_source.get("verified_on") == "2026-09-02", "corpus-source verification date drift")

    source_resource = corpus_source.get("resource")
    require(isinstance(source_resource, dict), "corpus-source resource must be an object")
    expected_resource = {
        "provider": "OpenSLR",
        "identifier": "SLR12",
        "name": "LibriSpeech ASR corpus",
        "resource_page": "https://www.openslr.org/12/",
        "summary": "Large-scale (1000 hours) corpus of read English speech",
        "category": "Speech",
        "license": "CC BY 4.0",
        "checksum_manifest": "https://www.openslr.org/resources/12/md5sum.txt",
        "checksum_algorithm": "MD5",
    }
    require(source_resource == expected_resource, "corpus-source authoritative resource facts drift")

    source_partitions = corpus_source.get("partitions")
    require(isinstance(source_partitions, list) and len(source_partitions) == 2, "corpus-source must freeze two partitions")
    source_by_name: dict[str, dict[str, Any]] = {}
    partition_keys = {"name", "role", "official_md5", "materialized", "archive_sha256"}
    for item in source_partitions:
        require(isinstance(item, dict), "corpus-source partition must be an object")
        require_exact_keys(item, partition_keys, "corpus_source.partition")
        name = item.get("name")
        require(isinstance(name, str) and name in expected_md5, f"unexpected corpus-source partition: {name!r}")
        require(name not in source_by_name, f"duplicate corpus-source partition: {name}")
        source_by_name[name] = item
        require(item.get("official_md5") == expected_md5[name], f"corpus-source MD5 drift for {name}")
        require_bool(item, "materialized", False, f"corpus_source.partition[{name}]")
        require(item.get("archive_sha256") is None, f"corpus-source {name} must not pre-claim SHA-256")
    require(set(source_by_name) == set(expected_md5), "corpus-source partition set drift")
    require(source_by_name["test-clean.tar.gz"].get("role") == "test set, clean speech", "test-clean role drift")
    require(
        source_by_name["test-other.tar.gz"].get("role") == "test set, other more challenging speech",
        "test-other role drift",
    )

    source_verification = corpus_source.get("verification")
    require(isinstance(source_verification, dict), "corpus-source verification must be an object")
    expected_verification = {
        "resource_page_checked": True,
        "checksum_manifest_checked": True,
        "archive_bytes_fetched": False,
        "archive_checksums_verified_against_bytes": False,
        "scope": "SOURCE_LICENSE_AND_OFFICIAL_CHECKSUM_PROVENANCE_ONLY",
    }
    require(source_verification == expected_verification, "corpus-source verification boundary drift")

    source_guards = corpus_source.get("claim_guards")
    require(isinstance(source_guards, dict), "corpus-source claim guards must be an object")
    expected_source_guards = {
        "public_human_claim_scope": "BOUNDED_ORDINARY_READ_ENGLISH_ONLY",
        "human_developer_speech_accuracy_evidence": "ABSENT",
        "production_stt_selected": False,
        "product_code_authorized": False,
    }
    require(source_guards == expected_source_guards, "corpus-source claim guards drift")
    require(corpus_source.get("next_task_after_canonicalization") == "B2P02", "B2P01 successor must be B2P02")

    spec = spec_path.read_text(encoding="utf-8")
    plan = plan_path.read_text(encoding="utf-8")
    tasks = tasks_path.read_text(encoding="utf-8")
    current = current_path.read_text(encoding="utf-8")
    founding_tasks = founding_tasks_path.read_text(encoding="utf-8")
    parent_spec = parent_spec_path.read_text(encoding="utf-8")
    parent_plan = parent_plan_path.read_text(encoding="utf-8")
    parent_tasks = parent_tasks_path.read_text(encoding="utf-8")

    for phrase in (
        "HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT",
        "DIAGNOSTIC_ONLY",
        "CC BY 4.0",
        "32fa31d27d2e1cad72775fee3f4849a9",
        "fb5a50374b501bb3bac4815ee91d3135",
    ):
        require_text(spec, phrase, "public child spec")
        require_text(current, phrase, "current frontier")

    for phrase in (
        "Materialize and verify exact archive bytes",
        "Freeze deterministic public-human subset selection logic and manifest",
        "Revalidate all candidate artifact/runtime identities from canonical evidence",
        "identical P0 audio bytes",
        "The subset builder must operate before candidate decoding",
        "D0 is optional and diagnostic",
        "D0 must never be merged numerically into P0 as one human accuracy score",
        "Do not infer control merely because metadata was captured",
        "Large upstream audio/model binaries must not be committed merely for reproducibility",
    ):
        require_text(plan, phrase, "public child plan")

    all_task_ids = (
        "B2P01", "B2P02", "B2P03", "B2P04", "B2P05", "B2P06", "B2P07", "B2P08",
        "B2E01", "B2E02", "B2E03", "B2E04", "B2E05", "B2E06", "B2E07", "B2E08",
        "B2D01", "B2D02", "B2D03", "B2D04",
        "B2S01", "B2S02", "B2S03", "B2S04", "B2S05", "B2S06", "B2S07", "B2S08", "B2S09",
    )
    for task_id in all_task_ids:
        require_text(tasks, f"`{task_id}`", "public child tasks")
    require_text(
        tasks,
        "- [x] `B2P01` Record exact OpenSLR SLR12 source/license facts and official checksums in machine-readable provenance.",
        "public child tasks",
    )
    require_text(
        tasks,
        "- [ ] `B2P02` Materialize `test-clean.tar.gz` and `test-other.tar.gz` from an approved source or official mirror; verify official MD5 and record exact archive SHA-256.",
        "public child tasks",
    )
    for task_id in all_task_ids[1:]:
        require(f"- [x] `{task_id}`" not in tasks, f"{task_id} must remain unchecked during B2P01")
    for phrase in (
        "These execution tasks become authorized only after the public-corpus amendment and frontier reconciliation are canonical on `main`.",
        "primary_decoding_started=false",
        "P0 and D0 strictly separated",
        "representing public audiobook speech as developer speech",
        "representing synthetic developer speech as human speech",
        "changing subset membership after candidate results are visible",
        "production STT integration",
        "permanent Rust/Cargo speech dependency",
    ):
        require_text(tasks, phrase, "public child tasks")

    require_text(current, "`000B2-unbiased-stt-bakeoff`", "current frontier")
    historical_section = current[current.index("`000B2-unbiased-stt-bakeoff`") :]
    require_text(historical_section[:512], "State: `BLOCKED_EXTERNAL`", "historical B2 frontier")
    require_text(current, "`000B2-public-corpus-bakeoff`", "current frontier")

    for label, text in (
        ("parent spec", parent_spec),
        ("parent plan", parent_plan),
        ("parent tasks", parent_tasks),
    ):
        require_text(text, "`000B2-unbiased-stt-bakeoff`", label)
        require_text(text, "`000B2-public-corpus-bakeoff`", label)
        require_text(text, "BLOCKED_EXTERNAL", label)
        require_text(text, "HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT", label)

    require_text(founding_tasks, "production Rust/Cargo speech code", "founding tasks")
    require_text(founding_tasks, "private 20-speaker", "founding tasks")
    require_text(founding_tasks, "`000B2-public-corpus-bakeoff`", "founding tasks")
    require_text(founding_tasks, "HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT", "founding tasks")

    print("PUBLIC_CORPUS_METHODOLOGY=PASS")
    print("B2P01_CORPUS_PROVENANCE=PASS")
    print("STRUCTURED_READINESS_GUARDS=PASS")
    print("P0_D0_SEPARATION=PASS")
    print("PRE_DECODE_FREEZE_ORDERING=PASS")
    print("PARENT_AUTHORITY_CHAIN=ALIGNED")
    print("HISTORICAL_PRIVATE_B2=BLOCKED_EXTERNAL")
    print("PRIVATE_COLLECTION_HISTORY=PRESERVED_UNEXECUTED")
    print("PUBLIC_HUMAN_BASELINE=LIBRISPEECH_SLR12")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    print("ARCHIVE_BYTES_FETCHED=NO")
    print("PRODUCT_CODE_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
