#!/usr/bin/env python3
"""Fail closed on the bounded 000B2 public-corpus methodology contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
B2P01_CANONICAL_MERGE = "2d2937b0da1dc9b4d7278fe6bfb778eb6a75d129"
B2P02_CANONICAL_MERGE = "1ba4e42561cc53f574d5d35689e2ae499a398b5c"
B2P02_POSTMERGE_RUN_ID = 33751302416
B2P02_POSTMERGE_JOB_ID = 100635230794
B2P02_POSTMERGE_ARTIFACT_ID = 9891735545
B2P02_POSTMERGE_ARTIFACT_DIGEST = "sha256:b0187d8b664a212a100d6d1515773891315d5af9e137178507c3b079d9edca6b"
B2P02_PROBE_REVISION = "b95da4aef86766ee9a976bb951cc2f6779dd1ef2"
B2P02_PROBE_RUN_ID = 33683639224
B2P02_PROBE_JOB_ID = 100425793105
B2P02_PROBE_ARTIFACT_ID = 9867230579
B2P02_PROBE_ARTIFACT_DIGEST = "sha256:82d64230f1aa0c52ac5eef8f314415095916e79b97945e302f4a03d7361c8c74"

EXPECTED_ARCHIVES: dict[str, dict[str, Any]] = {
    "test-clean.tar.gz": {
        "role": "test set, clean speech",
        "source_url": "https://www.openslr.org/resources/12/test-clean.tar.gz",
        "official_md5": "32fa31d27d2e1cad72775fee3f4849a9",
        "archive_bytes": 346663984,
        "archive_sha256": "39fde525e59672dc6d1551919b1478f724438a95aa55f874b576be21967e6c23",
    },
    "test-other.tar.gz": {
        "role": "test set, other more challenging speech",
        "source_url": "https://www.openslr.org/resources/12/test-other.tar.gz",
        "official_md5": "fb5a50374b501bb3bac4815ee91d3135",
        "archive_bytes": 328757843,
        "archive_sha256": "d09c181bba5cf717b3dee7d4d592af11a3ee3a09e08ae025c5506f6ebe961c29",
    },
}

ALL_TASK_IDS = (
    "B2P01", "B2P02", "B2P03", "B2P04", "B2P05", "B2P06", "B2P07", "B2P08",
    "B2E01", "B2E02", "B2E03", "B2E04", "B2E05", "B2E06", "B2E07", "B2E08",
    "B2D01", "B2D02", "B2D03", "B2D04",
    "B2S01", "B2S02", "B2S03", "B2S04", "B2S05", "B2S06", "B2S07", "B2S08", "B2S09",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"PUBLIC_CORPUS_METHODOLOGY=FAIL: {message}")


def require_text(text: str, phrase: str, label: str) -> None:
    require(phrase in text, f"{label} missing required text: {phrase}")


def require_absent(text: str, phrase: str, label: str) -> None:
    require(phrase not in text, f"{label} contains stale/prohibited text: {phrase}")


def require_bool(mapping: dict[str, Any], key: str, expected: bool, label: str) -> None:
    require(mapping.get(key) is expected, f"{label}.{key} must be {expected}")


def require_exact_keys(mapping: dict[str, Any], expected: set[str], label: str) -> None:
    require(set(mapping) == expected, f"{label} keys drift: expected {sorted(expected)}, got {sorted(mapping)}")


def load_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{label} root must be an object")
    return value


def index_records(records: Any, expected_names: set[str], label: str) -> dict[str, dict[str, Any]]:
    require(isinstance(records, list) and len(records) == len(expected_names), f"{label} record count drift")
    indexed: dict[str, dict[str, Any]] = {}
    for item in records:
        require(isinstance(item, dict), f"{label} record must be an object")
        name = item.get("name")
        require(isinstance(name, str) and name in expected_names, f"unexpected {label} name: {name!r}")
        require(name not in indexed, f"duplicate {label} name: {name}")
        indexed[name] = item
    require(set(indexed) == expected_names, f"{label} name set drift")
    return indexed


def main() -> None:
    readiness_path = ROOT / "research/000b2-public/readiness.json"
    corpus_source_path = ROOT / "research/000b2-public/corpus-source.json"
    materialization_path = ROOT / "research/000b2-public/archive-materialization.json"
    materializer_path = ROOT / "research/000b2-public/materialize_archives.py"
    materialization_workflow_path = ROOT / ".github/workflows/000b2-public-materialization.yml"
    spec_path = ROOT / "specs/000B2-public-corpus-bakeoff/spec.md"
    plan_path = ROOT / "specs/000B2-public-corpus-bakeoff/plan.md"
    tasks_path = ROOT / "specs/000B2-public-corpus-bakeoff/tasks.md"
    parent_spec_path = ROOT / "specs/000B-stt-entity-bakeoff/spec.md"
    parent_plan_path = ROOT / "specs/000B-stt-entity-bakeoff/plan.md"
    parent_tasks_path = ROOT / "specs/000B-stt-entity-bakeoff/tasks.md"
    current_path = ROOT / "specs/CURRENT.md"
    current_state_path = ROOT / "docs/canonical/CURRENT_STATE.md"
    founding_tasks_path = ROOT / "specs/000-founding-research/tasks.md"

    required_paths = (
        readiness_path, corpus_source_path, materialization_path, materializer_path,
        materialization_workflow_path, spec_path, plan_path, tasks_path, parent_spec_path,
        parent_plan_path, parent_tasks_path, current_path, current_state_path, founding_tasks_path,
    )
    for path in required_paths:
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")

    expected_names = set(EXPECTED_ARCHIVES)

    readiness = load_object(readiness_path, "readiness")
    require_exact_keys(
        readiness,
        {
            "schema_version", "lane", "state", "completed_through", "historical_private_collection_lane",
            "public_human_baseline", "developer_term_diagnostic", "candidate_registry", "preprocessing",
            "execution_environment", "attempt_manifest", "claim_guards", "next_action",
        },
        "readiness",
    )
    require(readiness.get("schema_version") == "000b2-public-readiness-v2", "readiness schema version drift")
    require(readiness.get("lane") == "PUBLIC_CORPUS", "readiness lane drift")
    require(readiness.get("state") == "READY", "public execution readiness must remain explicit")
    require(readiness.get("completed_through") == "B2P02", "readiness completed_through must be B2P02")

    historical = readiness.get("historical_private_collection_lane")
    require(isinstance(historical, dict), "historical private lane must be an object")
    require_exact_keys(historical, {"preserved", "executed", "primary_decoding_performed", "active_entry_gate"}, "historical_private_collection_lane")
    require_bool(historical, "preserved", True, "historical_private_collection_lane")
    require_bool(historical, "executed", False, "historical_private_collection_lane")
    require_bool(historical, "primary_decoding_performed", False, "historical_private_collection_lane")
    require_bool(historical, "active_entry_gate", False, "historical_private_collection_lane")

    public = readiness.get("public_human_baseline")
    require(isinstance(public, dict), "public human baseline must be an object")
    require_exact_keys(
        public,
        {"corpus", "upstream", "license", "partitions", "archive_byte_evidence", "subset_manifest_frozen", "candidate_decoding_started", "claim_scope"},
        "public_human_baseline",
    )
    require(public.get("corpus") == "LibriSpeech ASR corpus SLR12", "unexpected public corpus")
    require(public.get("upstream") == "https://www.openslr.org/12/", "OpenSLR source drift")
    require(public.get("license") == "CC BY 4.0", "license drift")
    require(public.get("archive_byte_evidence") == "research/000b2-public/archive-materialization.json", "archive evidence binding drift")
    require(public.get("claim_scope") == "BOUNDED_ORDINARY_READ_ENGLISH_ONLY", "public-human claim scope drift")
    require_bool(public, "subset_manifest_frozen", False, "public_human_baseline")
    require_bool(public, "candidate_decoding_started", False, "public_human_baseline")

    readiness_partitions = index_records(public.get("partitions"), expected_names, "readiness partition")
    for name, expected in EXPECTED_ARCHIVES.items():
        item = readiness_partitions[name]
        require_exact_keys(item, {"name", "official_md5", "archive_bytes", "archive_sha256", "materialized"}, f"readiness partition[{name}]")
        require(item.get("official_md5") == expected["official_md5"], f"readiness MD5 drift for {name}")
        require(item.get("archive_bytes") == expected["archive_bytes"], f"readiness byte-count drift for {name}")
        require(item.get("archive_sha256") == expected["archive_sha256"], f"readiness SHA-256 drift for {name}")
        require_bool(item, "materialized", True, f"readiness partition[{name}]")

    diagnostic = readiness.get("developer_term_diagnostic")
    require(isinstance(diagnostic, dict), "developer diagnostic must be an object")
    require_exact_keys(diagnostic, {"status", "synthetic_only", "human_accuracy_claim_eligible", "may_be_not_run"}, "developer_term_diagnostic")
    require(diagnostic.get("status") == "OPTIONAL_NOT_FROZEN", "developer diagnostic status drift")
    require_bool(diagnostic, "synthetic_only", True, "developer_term_diagnostic")
    require_bool(diagnostic, "human_accuracy_claim_eligible", False, "developer_term_diagnostic")
    require_bool(diagnostic, "may_be_not_run", True, "developer_term_diagnostic")

    registry = readiness.get("candidate_registry")
    require(isinstance(registry, dict), "candidate registry must be an object")
    require_exact_keys(registry, {"reuse_canonical_b1_b2_entry_cells", "revalidation_required_before_decode"}, "candidate_registry")
    require_bool(registry, "reuse_canonical_b1_b2_entry_cells", True, "candidate_registry")
    require_bool(registry, "revalidation_required_before_decode", True, "candidate_registry")

    preprocessing = readiness.get("preprocessing")
    require(isinstance(preprocessing, dict), "preprocessing contract must be an object")
    require_exact_keys(preprocessing, {"required_tool", "attempt_bound_capture_required", "resolved"}, "preprocessing")
    require(preprocessing.get("required_tool") == "FFmpeg 9.0.1", "preprocessing tool drift")
    require_bool(preprocessing, "attempt_bound_capture_required", True, "preprocessing")
    require_bool(preprocessing, "resolved", False, "preprocessing")

    environment = readiness.get("execution_environment")
    require(isinstance(environment, dict), "execution environment contract must be an object")
    require_exact_keys(environment, {"attempt_bound_capture_required", "resolved", "hosted_runner_performance_mode"}, "execution_environment")
    require_bool(environment, "attempt_bound_capture_required", True, "execution_environment")
    require_bool(environment, "resolved", False, "execution_environment")
    require(environment.get("hosted_runner_performance_mode") == "DIAGNOSTIC_ONLY", "hosted-runner performance boundary drift")

    attempt = readiness.get("attempt_manifest")
    require(isinstance(attempt, dict), "attempt manifest state must be an object")
    require_exact_keys(attempt, {"frozen", "primary_decoding_started"}, "attempt_manifest")
    require_bool(attempt, "frozen", False, "attempt_manifest")
    require_bool(attempt, "primary_decoding_started", False, "attempt_manifest")

    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "claim guards must be an object")
    require_exact_keys(guards, {"human_developer_speech_accuracy_evidence", "synthetic_developer_media_is_human_evidence", "production_stt_selected", "product_code_authorized"}, "claim_guards")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence must remain absent")
    require_bool(guards, "synthetic_developer_media_is_human_evidence", False, "claim_guards")
    require_bool(guards, "production_stt_selected", False, "claim_guards")
    require_bool(guards, "product_code_authorized", False, "claim_guards")

    expected_next_action = (
        "Execute B2P03 only: implement deterministic speaker/utterance subset selection independent of candidate outputs. "
        "Do not freeze the B2P04 subset manifest or begin candidate work until B2P03 is canonical."
    )
    require(readiness.get("next_action") == expected_next_action, "next action must be exact B2P03-only instruction")

    corpus_source = load_object(corpus_source_path, "corpus-source")
    require_exact_keys(
        corpus_source,
        {"schema_version", "task", "state", "source_provenance_verified_on", "resource", "partitions", "verification", "claim_guards", "next_task_after_canonicalization"},
        "corpus_source",
    )
    require(corpus_source.get("schema_version") == "000b2-public-corpus-source-v2", "corpus-source schema drift")
    require(corpus_source.get("task") == "B2P02", "corpus-source task must be B2P02")
    require(corpus_source.get("state") == "ARCHIVES_MATERIALIZED_AND_VERIFIED", "corpus-source state drift")
    require(corpus_source.get("source_provenance_verified_on") == "2026-09-02", "source provenance date drift")

    expected_resource = {
        "provider": "OpenSLR", "identifier": "SLR12", "name": "LibriSpeech ASR corpus",
        "resource_page": "https://www.openslr.org/12/", "summary": "Large-scale (1000 hours) corpus of read English speech",
        "category": "Speech", "license": "CC BY 4.0", "checksum_manifest": "https://www.openslr.org/resources/12/md5sum.txt",
        "checksum_algorithm": "MD5",
    }
    source_resource = corpus_source.get("resource")
    require(isinstance(source_resource, dict), "corpus-source resource must be an object")
    require(source_resource == expected_resource, "corpus-source authoritative resource facts drift")

    source_partitions = index_records(corpus_source.get("partitions"), expected_names, "corpus-source partition")
    source_partition_keys = {"name", "role", "source_url", "official_md5", "archive_bytes", "materialized", "archive_sha256", "archive_retained_in_repository"}
    for name, expected in EXPECTED_ARCHIVES.items():
        item = source_partitions[name]
        require_exact_keys(item, source_partition_keys, f"corpus_source.partition[{name}]")
        require(item.get("role") == expected["role"], f"corpus-source role drift for {name}")
        require(item.get("source_url") == expected["source_url"], f"corpus-source source URL drift for {name}")
        require(item.get("official_md5") == expected["official_md5"], f"corpus-source MD5 drift for {name}")
        require(item.get("archive_bytes") == expected["archive_bytes"], f"corpus-source byte-count drift for {name}")
        require(item.get("archive_sha256") == expected["archive_sha256"], f"corpus-source SHA-256 drift for {name}")
        require_bool(item, "materialized", True, f"corpus_source.partition[{name}]")
        require_bool(item, "archive_retained_in_repository", False, f"corpus_source.partition[{name}]")

    expected_verification = {
        "resource_page_checked": True, "checksum_manifest_checked": True, "archive_bytes_fetched": True,
        "archive_checksums_verified_against_bytes": True, "archive_sha256_computed_from_fetched_bytes": True,
        "materialization_evidence": "research/000b2-public/archive-materialization.json",
        "scope": "SOURCE_LICENSE_AND_EXACT_ARCHIVE_BYTE_VERIFICATION",
    }
    source_verification = corpus_source.get("verification")
    require(isinstance(source_verification, dict), "corpus-source verification must be an object")
    require(source_verification == expected_verification, "corpus-source verification boundary drift")

    expected_source_guards = {
        "public_human_claim_scope": "BOUNDED_ORDINARY_READ_ENGLISH_ONLY",
        "human_developer_speech_accuracy_evidence": "ABSENT", "subset_manifest_frozen": False,
        "candidate_decoding_started": False, "production_stt_selected": False, "product_code_authorized": False,
    }
    source_guards = corpus_source.get("claim_guards")
    require(isinstance(source_guards, dict), "corpus-source claim guards must be an object")
    require(source_guards == expected_source_guards, "corpus-source claim guards drift")
    require(corpus_source.get("next_task_after_canonicalization") == "B2P03", "B2P02 successor must be B2P03")

    evidence = load_object(materialization_path, "archive materialization evidence")
    require_exact_keys(
        evidence,
        {"schema_version", "task", "status", "repository", "probe_revision", "github_run_id", "github_run_attempt", "github_job_id", "artifact", "runner", "checksum_manifest", "checksum_manifest_resolved_url", "archive_bytes_retained_in_repository", "archives", "evidence_boundary"},
        "archive_materialization",
    )
    require(evidence.get("schema_version") == "000b2-public-archive-materialization-evidence-v1", "materialization schema drift")
    require(evidence.get("task") == "B2P02", "materialization task drift")
    require(evidence.get("status") == "VERIFIED_ARCHIVE_BYTES", "materialization status drift")
    require(evidence.get("repository") == "TheHalfMoon/Wispral", "materialization repository drift")
    require(evidence.get("probe_revision") == B2P02_PROBE_REVISION, "materialization probe revision drift")
    require(evidence.get("github_run_id") == B2P02_PROBE_RUN_ID, "materialization run identity drift")
    require(evidence.get("github_run_attempt") == 1, "materialization run attempt drift")
    require(evidence.get("github_job_id") == B2P02_PROBE_JOB_ID, "materialization job identity drift")
    require(evidence.get("checksum_manifest") == expected_resource["checksum_manifest"], "materialization checksum manifest drift")
    require(evidence.get("checksum_manifest_resolved_url") == expected_resource["checksum_manifest"], "materialization resolved manifest drift")
    require_bool(evidence, "archive_bytes_retained_in_repository", False, "archive_materialization")

    artifact = evidence.get("artifact")
    require(isinstance(artifact, dict), "materialization artifact must be an object")
    require_exact_keys(artifact, {"id", "name", "digest", "created_at", "retention_days"}, "archive_materialization.artifact")
    require(artifact.get("id") == B2P02_PROBE_ARTIFACT_ID, "materialization artifact id drift")
    require(artifact.get("name") == f"b2p02-archive-materialization-{B2P02_PROBE_REVISION}", "materialization artifact name drift")
    require(artifact.get("digest") == B2P02_PROBE_ARTIFACT_DIGEST, "materialization artifact digest drift")
    require(artifact.get("created_at") == "2026-09-02T21:11:08Z", "materialization artifact timestamp drift")
    require(artifact.get("retention_days") == 7, "materialization artifact retention drift")

    runner = evidence.get("runner")
    require(isinstance(runner, dict), "materialization runner must be an object")
    require(runner == {"os": "Linux", "arch": "X64", "image": "ubuntu-24.04"}, "materialization runner identity drift")

    evidence_archives = index_records(evidence.get("archives"), expected_names, "materialization archive")
    evidence_archive_keys = {"name", "source_url", "resolved_url", "bytes", "official_md5", "observed_md5", "observed_sha256"}
    for name, expected in EXPECTED_ARCHIVES.items():
        item = evidence_archives[name]
        require_exact_keys(item, evidence_archive_keys, f"archive_materialization.archive[{name}]")
        require(item.get("source_url") == expected["source_url"], f"materialization source URL drift for {name}")
        require(item.get("resolved_url") == expected["source_url"], f"materialization resolved URL drift for {name}")
        require(item.get("bytes") == expected["archive_bytes"], f"materialization byte-count drift for {name}")
        require(item.get("official_md5") == expected["official_md5"], f"materialization official MD5 drift for {name}")
        require(item.get("observed_md5") == expected["official_md5"], f"materialization observed MD5 drift for {name}")
        require(item.get("observed_sha256") == expected["archive_sha256"], f"materialization SHA-256 drift for {name}")

    evidence_boundary = evidence.get("evidence_boundary")
    require(isinstance(evidence_boundary, dict), "materialization evidence boundary must be an object")
    require(
        evidence_boundary == {
            "official_md5_verified_against_fetched_bytes": True,
            "sha256_computed_from_same_fetched_bytes": True,
            "archives_extracted": False,
            "subset_selection_started": False,
            "candidate_decoding_started": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
        },
        "materialization evidence boundary drift",
    )

    spec = spec_path.read_text(encoding="utf-8")
    plan = plan_path.read_text(encoding="utf-8")
    tasks = tasks_path.read_text(encoding="utf-8")
    current = current_path.read_text(encoding="utf-8")
    current_state = current_state_path.read_text(encoding="utf-8")
    founding_tasks = founding_tasks_path.read_text(encoding="utf-8")
    parent_spec = parent_spec_path.read_text(encoding="utf-8")
    parent_plan = parent_plan_path.read_text(encoding="utf-8")
    parent_tasks = parent_tasks_path.read_text(encoding="utf-8")
    materializer = materializer_path.read_text(encoding="utf-8")
    materialization_workflow = materialization_workflow_path.read_text(encoding="utf-8")

    for phrase in (
        "HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT", "DIAGNOSTIC_ONLY", "CC BY 4.0",
        EXPECTED_ARCHIVES["test-clean.tar.gz"]["official_md5"], EXPECTED_ARCHIVES["test-other.tar.gz"]["official_md5"],
    ):
        require_text(spec, phrase, "public child spec")
        require_text(current, phrase, "current frontier")

    for phrase in (
        "Materialize and verify exact archive bytes", "Freeze deterministic public-human subset selection logic and manifest",
        "Revalidate all candidate artifact/runtime identities from canonical evidence", "identical P0 audio bytes",
        "The subset builder must operate before candidate decoding", "D0 is optional and diagnostic",
        "D0 must never be merged numerically into P0 as one human accuracy score", "Do not infer control merely because metadata was captured",
        "Large upstream audio/model binaries must not be committed merely for reproducibility",
    ):
        require_text(plan, phrase, "public child plan")

    task_lines = tasks.splitlines()
    for task_id in ALL_TASK_IDS:
        matching_lines = [line for line in task_lines if f"`{task_id}`" in line]
        require(len(matching_lines) == 1, f"{task_id} must appear in exactly one checklist line")
        expected_marker = "- [x]" if task_id in {"B2P01", "B2P02"} else "- [ ]"
        require(matching_lines[0].startswith(f"{expected_marker} `{task_id}`"), f"{task_id} checklist state must be {expected_marker}")
    require_text(tasks, "- [x] `B2P01` Record exact OpenSLR SLR12 source/license facts and official checksums in machine-readable provenance.", "public child tasks")
    require_text(tasks, "- [x] `B2P02` Materialize `test-clean.tar.gz` and `test-other.tar.gz` from an approved source or official mirror; verify official MD5 and record exact archive SHA-256.", "public child tasks")

    for phrase in (
        "These execution tasks become authorized only after the public-corpus amendment and frontier reconciliation are canonical on `main`.",
        "primary_decoding_started=false", "P0 and D0 strictly separated", "representing public audiobook speech as developer speech",
        "representing synthetic developer speech as human speech", "changing subset membership after candidate results are visible",
        "production STT integration", "permanent Rust/Cargo speech dependency",
    ):
        require_text(tasks, phrase, "public child tasks")

    require_text(current, "`000B2-unbiased-stt-bakeoff`", "current frontier")
    historical_section = current[current.index("`000B2-unbiased-stt-bakeoff`") :]
    require_text(historical_section[:512], "State: `BLOCKED_EXTERNAL`", "historical B2 frontier")
    require_text(current, "`000B2-public-corpus-bakeoff`", "current frontier")
    require_text(current, B2P01_CANONICAL_MERGE, "current frontier B2P01 canonical proof")
    require_text(current, B2P02_CANONICAL_MERGE, "current frontier B2P02 canonical proof")
    require_text(current, f"run `{B2P02_POSTMERGE_RUN_ID}`", "current frontier B2P02 post-merge run proof")
    require_text(current, f"job `{B2P02_POSTMERGE_JOB_ID}`", "current frontier B2P02 post-merge job proof")
    require_text(current, f"artifact `{B2P02_POSTMERGE_ARTIFACT_ID}`", "current frontier B2P02 post-merge artifact proof")
    require_text(current, B2P02_POSTMERGE_ARTIFACT_DIGEST, "current frontier B2P02 post-merge artifact digest proof")
    require_text(current, "current bounded execution unit `B2P03`", "current frontier")
    require_absent(current, "current bounded execution unit `B2P02`", "current frontier")

    require_text(current_state, B2P01_CANONICAL_MERGE, "current state B2P01 canonical proof")
    require_text(current_state, B2P02_CANONICAL_MERGE, "current state B2P02 canonical proof")
    require_text(current_state, f"run `{B2P02_POSTMERGE_RUN_ID}`", "current state B2P02 post-merge run proof")
    require_text(current_state, f"job `{B2P02_POSTMERGE_JOB_ID}`", "current state B2P02 post-merge job proof")
    require_text(current_state, f"artifact `{B2P02_POSTMERGE_ARTIFACT_ID}`", "current state B2P02 post-merge artifact proof")
    require_text(current_state, B2P02_POSTMERGE_ARTIFACT_DIGEST, "current state B2P02 post-merge artifact digest proof")
    require_text(current_state, "current bounded execution unit is `B2P03`", "current state")
    require_absent(current_state, "current bounded execution unit is `B2P02`", "current state")

    for label, text in (("parent spec", parent_spec), ("parent plan", parent_plan), ("parent tasks", parent_tasks)):
        require_text(text, "`000B2-unbiased-stt-bakeoff`", label)
        require_text(text, "`000B2-public-corpus-bakeoff`", label)
        require_text(text, "BLOCKED_EXTERNAL", label)
        require_text(text, "HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT", label)

    require_text(founding_tasks, "production Rust/Cargo speech code", "founding tasks")
    require_text(founding_tasks, "private 20-speaker", "founding tasks")
    require_text(founding_tasks, "`000B2-public-corpus-bakeoff`", "founding tasks")
    require_text(founding_tasks, "HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT", "founding tasks")

    for phrase in (
        "https://www.openslr.org/resources/12/test-clean.tar.gz", "https://www.openslr.org/resources/12/test-other.tar.gz",
        "B2P02_MATERIALIZATION=PASS", "B2P02_REVISION",
    ):
        require_text(materializer, phrase, "B2P02 materializer")
    for phrase in (
        "000B2 Public Corpus Archive Materialization", "B2P02_REVISION: ${{ github.event.pull_request.head.sha || github.sha }}",
        "ref: ${{ env.B2P02_REVISION }}", "materialize_archives.py", "actions/upload-artifact@v4",
    ):
        require_text(materialization_workflow, phrase, "B2P02 materialization workflow")

    print("PUBLIC_CORPUS_METHODOLOGY=PASS")
    print("B2P01_CORPUS_PROVENANCE=PASS")
    print("B2P02_ARCHIVE_MATERIALIZATION=PASS")
    print(f"B2P02_PROBE_RUN_ID={B2P02_PROBE_RUN_ID}")
    print(f"B2P02_CANONICAL_MERGE={B2P02_CANONICAL_MERGE}")
    print(f"B2P02_POSTMERGE_RUN_ID={B2P02_POSTMERGE_RUN_ID}")
    print(f"B2P02_TEST_CLEAN_SHA256={EXPECTED_ARCHIVES['test-clean.tar.gz']['archive_sha256']}")
    print(f"B2P02_TEST_OTHER_SHA256={EXPECTED_ARCHIVES['test-other.tar.gz']['archive_sha256']}")
    print("B2P03_FRONTIER=AUTHORIZED")
    print("STRUCTURED_READINESS_GUARDS=PASS")
    print("P0_D0_SEPARATION=PASS")
    print("PRE_DECODE_FREEZE_ORDERING=PASS")
    print("PARENT_AUTHORITY_CHAIN=ALIGNED")
    print("HISTORICAL_PRIVATE_B2=BLOCKED_EXTERNAL")
    print("PRIVATE_COLLECTION_HISTORY=PRESERVED_UNEXECUTED")
    print("PUBLIC_HUMAN_BASELINE=LIBRISPEECH_SLR12")
    print("HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT")
    print("ARCHIVE_BYTES_FETCHED=YES")
    print("ARCHIVE_MD5_VERIFIED=YES")
    print("ARCHIVE_SHA256_RECORDED=YES")
    print("SUBSET_SELECTION_STARTED=NO")
    print("CANDIDATE_DECODING_STARTED=NO")
    print("PRODUCT_CODE_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
