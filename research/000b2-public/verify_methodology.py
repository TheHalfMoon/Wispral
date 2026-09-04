#!/usr/bin/env python3
"""Fail closed on the bounded 000B2 public-corpus methodology contract."""

from __future__ import annotations

import hashlib
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
B2P03_CANONICAL_MERGE = "83eca872148f329033c299f6671d275edf2d7b58"
B2P03_POSTMERGE_SUBSET_RUN_ID = 33775647508
B2P03_POSTMERGE_SUBSET_JOB_ID = 100716549752
B2P03_POSTMERGE_METHODOLOGY_RUN_ID = 33775647539
B2P03_POSTMERGE_METHODOLOGY_JOB_ID = 100716550502
B2P04_CANONICAL_MERGE = "4c4e758f22b54fa62256e57bfbd344adc817df8e"
B2P04_QUALIFIED_HEAD = "0d83d277cc2544f63613e674d60bae07ad24dc26"
B2P04_MANIFEST_SHA256 = "5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb"
B2P04_FREEZE_DIGEST_SHA256 = "f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242"
B2P04_POSTMERGE_SUBSET_RUN_ID = 33794854765
B2P04_POSTMERGE_SUBSET_JOB_ID = 100779961908
B2P04_POSTMERGE_ARTIFACT_ID = 9908811632
B2P04_POSTMERGE_ARTIFACT_DIGEST = "sha256:bad9a31cea1a3a51b6ecbf9053f4941b1ae8a5d88cb97b747703166fe9444578"
B2P04_POSTMERGE_METHODOLOGY_RUN_ID = 33794854595
B2P04_POSTMERGE_METHODOLOGY_JOB_ID = 100779960182
B2P05_CANONICAL_MERGE = "49538990fb4cf8223e9321261925206ed7ff5cee"
B2P05_QUALIFIED_HEAD = "c62a7fa2998cd5292da78a66deb4a6d2044691b3"
B2P05_POSTMERGE_REVALIDATION_RUN_ID = 33803832655
B2P05_POSTMERGE_STATIC_JOB_ID = 100809416957
B2P05_POSTMERGE_LIVE_JOB_ID = 100809480949
B2P05_POSTMERGE_METHODOLOGY_RUN_ID = 33803832693
B2P05_POSTMERGE_METHODOLOGY_JOB_ID = 100809418067
B2P05_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID = 33803832706
B2P05_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID = 33803832711
B2P05_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID = 33803832717
B2P05_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID = 33803832657
B2P06_CANONICAL_MERGE = "3dceadd984ff307ce55745bf5f289890a2fac261"
B2P06_QUALIFIED_HEAD = "c5501daf14038ced0ba3ad2de1cad92cfb38302a"
B2P06_EVIDENCE_SHA256 = "d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011"
B2P06_POSTMERGE_PREPROCESSING_RUN_ID = 33814736588
B2P06_POSTMERGE_PREPROCESSING_JOB_ID = 100844238206
B2P06_POSTMERGE_PREPROCESSING_ARTIFACT_ID = 9916141620
B2P06_POSTMERGE_PREPROCESSING_ARTIFACT_DIGEST = "sha256:d0a6918fc7bf48e93053fab4fb3286c250a6c980456d893bb9c286f9697130b9"
B2P06_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID = 33814736795
B2P06_POSTMERGE_METHODOLOGY_RUN_ID = 33814736759
B2P06_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID = 33814736691
B2P06_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID = 33814736716
B2P06_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID = 33814736734
B2P06_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID = 33814736663
B2P07_CANONICAL_MERGE = "4bd5306fa1d274d7b822b73e26172dd9c7058319"
B2P07_QUALIFIED_HEAD = "422ea2d7f0945437ea271412b2f2e33c85256f2e"
B2P07_RAW_CAPTURE_COMMIT = "aa4711c083b652dfdb7a5d29a39a222125000131"
B2P07_RAW_CAPTURE_EVIDENCE_BLOB = "d84e3e55d45a937a09e5898727b60c635144ac5c"
B2P07_PROVENANCE_SEAL_COMMIT = "b8268cb4316a0d05c898bbf5b8bb3f7fe82d4937"
B2P07_SEALED_EVIDENCE_BLOB = "caf814bcb5e42fd769e6df1d9a54c1164535f86c"
B2P07_POSTMERGE_ENVIRONMENT_RUN_ID = 33864082394
B2P07_POSTMERGE_ENVIRONMENT_JOB_ID = 100994833527
B2P07_POSTMERGE_METHODOLOGY_RUN_ID = 33864082358
B2P07_POSTMERGE_METHODOLOGY_JOB_ID = 100994833254
B2P07_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID = 33864082439
B2P07_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID = 33864082418
B2P07_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID = 33864082356
B2P07_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID = 33864082410
B2P07_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID = 33864082452
B2P08_CANONICAL_MERGE = "dd65e23d29e7f83b9a94aba9c018928c7f9cc41d"
B2P08_QUALIFIED_HEAD = "a5ee2ccb48a301b623f775970c23434d3a50ccba"
B2P08_FREEZE_DIGEST = "af4d5009e293daef5d8f629ca91af653f5f591448cd94d4555473a51e2d1da86"
B2P08_POSTMERGE_ATTEMPT_RUN_ID = 33873343952
B2P08_POSTMERGE_METHODOLOGY_RUN_ID = 33873344061
B2P08_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID = 33873344096
B2P08_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID = 33873344252
B2P08_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID = 33873344071
B2P08_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID = 33873344118
B2P08_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID = 33873344044
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    subset_policy_path = ROOT / "research/000b2-public/subset-selection-policy.json"
    subset_selector_path = ROOT / "research/000b2-public/select_subset.py"
    subset_verifier_path = ROOT / "research/000b2-public/verify_subset_selection.py"
    subset_workflow_path = ROOT / ".github/workflows/000b2-public-subset-selection.yml"
    subset_manifest_path = ROOT / "research/000b2-public/subset-manifest.json"
    subset_freeze_workflow_path = ROOT / ".github/workflows/000b2-public-subset-freeze.yml"
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
        materialization_workflow_path, subset_policy_path, subset_selector_path, subset_verifier_path,
        subset_workflow_path, subset_manifest_path, subset_freeze_workflow_path, spec_path, plan_path, tasks_path, parent_spec_path,
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
    require(readiness.get("completed_through") == "B2P08", "readiness completed_through must be B2P08")

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
    require_bool(public, "subset_manifest_frozen", True, "public_human_baseline")
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
    require_bool(preprocessing, "resolved", True, "preprocessing")

    environment = readiness.get("execution_environment")
    require(isinstance(environment, dict), "execution environment contract must be an object")
    require_exact_keys(environment, {"attempt_bound_capture_required", "resolved", "hosted_runner_performance_mode"}, "execution_environment")
    require_bool(environment, "attempt_bound_capture_required", True, "execution_environment")
    require_bool(environment, "resolved", True, "execution_environment")
    require(environment.get("hosted_runner_performance_mode") == "DIAGNOSTIC_ONLY", "hosted-runner performance boundary drift")

    attempt = readiness.get("attempt_manifest")
    require(isinstance(attempt, dict), "attempt manifest state must be an object")
    require_exact_keys(attempt, {"frozen", "primary_decoding_started"}, "attempt_manifest")
    require_bool(attempt, "frozen", True, "attempt_manifest")
    require_bool(attempt, "primary_decoding_started", False, "attempt_manifest")

    guards = readiness.get("claim_guards")
    require(isinstance(guards, dict), "claim guards must be an object")
    require_exact_keys(guards, {"human_developer_speech_accuracy_evidence", "synthetic_developer_media_is_human_evidence", "production_stt_selected", "product_code_authorized"}, "claim_guards")
    require(guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "human developer-speech evidence must remain absent")
    require_bool(guards, "synthetic_developer_media_is_human_evidence", False, "claim_guards")
    require_bool(guards, "production_stt_selected", False, "claim_guards")
    require_bool(guards, "product_code_authorized", False, "claim_guards")

    expected_next_action = (
        'Execute B2E01 only: decode the exact frozen P0 public-human subset with candidate cell 1 (`moonshine-compact`) under frozen C0, preserve raw transcript/failure/run evidence, keep repository/test-specific context and candidate-specific audio transforms OFF, and preserve DIAGNOSTIC timing semantics. Do not begin B2E02 or any later candidate cell until B2E01 is canonical.'
    )
    require(readiness.get("next_action") == expected_next_action, "next action must be exact B2P08-only instruction")

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
    require(corpus_source.get("next_task_after_canonicalization") == "B2P03", "B2P02 successor must remain historical B2P03")

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

    subset_policy = load_object(subset_policy_path, "subset selection policy")
    require_exact_keys(
        subset_policy,
        {"schema_version", "task", "state", "corpus", "partitions", "ordering", "source_contract", "output_contract", "claim_guards"},
        "subset_policy",
    )
    require(subset_policy.get("schema_version") == "000b2-public-subset-selection-policy-v1", "subset policy schema drift")
    require(subset_policy.get("task") == "B2P03", "subset policy task drift")
    require(subset_policy.get("state") == "SELECTION_LOGIC_FROZEN_MANIFEST_NOT_FROZEN", "subset policy state drift")
    require(subset_policy.get("corpus") == "LibriSpeech ASR corpus SLR12", "subset policy corpus drift")
    require(
        subset_policy.get("partitions") == [
            {"name": "test-clean", "speakers_per_partition": 12, "utterances_per_speaker_max": 10},
            {"name": "test-other", "speakers_per_partition": 12, "utterances_per_speaker_max": 10},
        ],
        "subset policy partition contract drift",
    )
    ordering = subset_policy.get("ordering")
    require(isinstance(ordering, dict), "subset ordering must be an object")
    require_exact_keys(
        ordering,
        {
            "hash_algorithm", "selection_material", "encoding", "component_separator",
            "speaker_components", "utterance_components", "tie_breaker",
        },
        "subset_ordering",
    )
    require(ordering.get("hash_algorithm") == "SHA-256", "subset ordering hash drift")
    require(ordering.get("selection_material") == "wispral-000b2-public-b2p03-v1", "subset selection material drift")
    require(ordering.get("encoding") == "UTF-8", "subset ordering encoding drift")
    require(ordering.get("component_separator") == "NUL", "subset ordering separator drift")
    require(ordering.get("tie_breaker") == "lexicographic stable identifier", "subset ordering tie-breaker drift")

    source_contract = subset_policy.get("source_contract")
    require(isinstance(source_contract, dict), "subset source contract must be an object")
    require_exact_keys(
        source_contract,
        {
            "membership_inputs", "candidate_outputs_allowed", "candidate_specific_behavior_allowed",
            "require_complete_transcript_audio_pairs", "require_partition_speaker_disjointness",
            "reject_duplicate_utterance_ids", "audio_extension", "transcript_extension",
        },
        "subset_source_contract",
    )
    require(source_contract.get("membership_inputs") == "EXTRACTED_LIBRISPEECH_METADATA_AND_SOURCE_CONTENT_IDENTITIES_ONLY", "subset source input boundary drift")
    require_bool(source_contract, "candidate_outputs_allowed", False, "subset_source_contract")
    require_bool(source_contract, "candidate_specific_behavior_allowed", False, "subset_source_contract")
    require_bool(source_contract, "require_complete_transcript_audio_pairs", True, "subset_source_contract")
    require_bool(source_contract, "require_partition_speaker_disjointness", True, "subset_source_contract")
    require_bool(source_contract, "reject_duplicate_utterance_ids", True, "subset_source_contract")

    output_contract = subset_policy.get("output_contract")
    require(isinstance(output_contract, dict), "subset output contract must be an object")
    require_exact_keys(
        output_contract,
        {
            "kind", "includes_source_partition", "includes_speaker_id", "includes_chapter_id",
            "includes_utterance_id", "includes_reference_transcript", "includes_source_audio_path",
            "includes_source_file_sha256", "manifest_digest_emitted",
            "canonical_preprocessed_file_sha256_emitted",
        },
        "subset_output_contract",
    )
    require(output_contract.get("kind") == "UNFROZEN_SELECTION_CANDIDATE", "subset output kind drift")
    require_bool(output_contract, "manifest_digest_emitted", False, "subset_output_contract")
    require_bool(output_contract, "canonical_preprocessed_file_sha256_emitted", False, "subset_output_contract")

    subset_guards = subset_policy.get("claim_guards")
    require(isinstance(subset_guards, dict), "subset claim guards must be an object")
    require_exact_keys(
        subset_guards,
        {
            "subset_manifest_frozen", "candidate_decoding_started", "primary_decoding_started",
            "human_developer_speech_accuracy_evidence", "production_stt_selected", "product_code_authorized",
        },
        "subset_claim_guards",
    )
    require_bool(subset_guards, "subset_manifest_frozen", False, "subset_claim_guards")
    require_bool(subset_guards, "candidate_decoding_started", False, "subset_claim_guards")
    require_bool(subset_guards, "primary_decoding_started", False, "subset_claim_guards")
    require(subset_guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "subset human-developer evidence guard drift")
    require_bool(subset_guards, "production_stt_selected", False, "subset_claim_guards")
    require_bool(subset_guards, "product_code_authorized", False, "subset_claim_guards")

    subset_manifest = load_object(subset_manifest_path, "subset manifest")
    require_exact_keys(
        subset_manifest,
        {"schema_version", "task", "state", "frozen", "freeze_digest_sha256", "authority", "source_corpus", "selection_engine", "membership", "preprocessing_boundary", "claim_guards"},
        "subset_manifest",
    )
    require(subset_manifest.get("schema_version") == "000b2-public-subset-manifest-v1", "subset manifest schema drift")
    require(subset_manifest.get("task") == "B2P04", "subset manifest task drift")
    require(subset_manifest.get("state") == "FROZEN_SOURCE_MEMBERSHIP", "subset manifest state drift")
    require_bool(subset_manifest, "frozen", True, "subset_manifest")
    require(subset_manifest.get("freeze_digest_sha256") == B2P04_FREEZE_DIGEST_SHA256, "B2P04 freeze digest drift")
    require(sha256_file(subset_manifest_path) == B2P04_MANIFEST_SHA256, "B2P04 manifest byte SHA-256 drift")
    manifest_authority = subset_manifest.get("authority")
    require(isinstance(manifest_authority, dict), "subset manifest authority must be an object")
    require(manifest_authority.get("b2p03_canonical_merge") == B2P03_CANONICAL_MERGE, "subset manifest B2P03 canonical binding drift")
    membership = subset_manifest.get("membership")
    require(isinstance(membership, dict), "subset manifest membership must be an object")
    require(membership.get("kind") == "SOURCE_FLAC_IDENTITIES_AND_REFERENCE_TRANSCRIPTS", "subset manifest membership kind drift")
    require(membership.get("total_speakers") == 24, "subset manifest speaker count drift")
    require(membership.get("total_utterances") == 240, "subset manifest utterance count drift")
    manifest_preprocessing = subset_manifest.get("preprocessing_boundary")
    require(isinstance(manifest_preprocessing, dict), "subset manifest preprocessing boundary must be an object")
    require(manifest_preprocessing.get("status") == "NOT_CAPTURED_B2P06", "B2P06 preprocessing boundary drift")
    require_bool(manifest_preprocessing, "canonical_preprocessed_file_sha256_present", False, "subset_manifest.preprocessing_boundary")
    manifest_guards = subset_manifest.get("claim_guards")
    require(isinstance(manifest_guards, dict), "subset manifest claim guards must be an object")
    require_bool(manifest_guards, "candidate_revalidation_started", False, "subset_manifest.claim_guards")
    require_bool(manifest_guards, "candidate_decoding_started", False, "subset_manifest.claim_guards")
    require_bool(manifest_guards, "primary_decoding_started", False, "subset_manifest.claim_guards")
    require(manifest_guards.get("human_developer_speech_accuracy_evidence") == "ABSENT", "subset manifest human evidence guard drift")
    require_bool(manifest_guards, "production_stt_selected", False, "subset_manifest.claim_guards")
    require_bool(manifest_guards, "product_code_authorized", False, "subset_manifest.claim_guards")

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
    subset_selector = subset_selector_path.read_text(encoding="utf-8")
    subset_verifier = subset_verifier_path.read_text(encoding="utf-8")
    subset_workflow = subset_workflow_path.read_text(encoding="utf-8")
    subset_freeze_workflow = subset_freeze_workflow_path.read_text(encoding="utf-8")

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
        expected_marker = "- [x]" if task_id in {"B2P01", "B2P02", "B2P03", "B2P04", "B2P05", "B2P06", "B2P07", "B2P08"} else "- [ ]"
        require(matching_lines[0].startswith(f"{expected_marker} `{task_id}`"), f"{task_id} checklist state must be {expected_marker}")
    require_text(tasks, "- [x] `B2P01` Record exact OpenSLR SLR12 source/license facts and official checksums in machine-readable provenance.", "public child tasks")
    require_text(tasks, "- [x] `B2P02` Materialize `test-clean.tar.gz` and `test-other.tar.gz` from an approved source or official mirror; verify official MD5 and record exact archive SHA-256.", "public child tasks")
    require_text(tasks, "- [x] `B2P03` Implement deterministic speaker/utterance subset selection independent of candidate outputs.", "public child tasks")
    require_text(tasks, "- [x] `B2P04` Freeze selected public-human subset manifest and manifest digest before candidate decoding.", "public child tasks")
    require_text(tasks, "- [x] `B2P05` Revalidate the six canonical candidate cells and artifact/runtime/model identities against live canonical evidence.", "public child tasks")
    require_text(tasks, "- [x] `B2P06` Capture attempt-bound FFmpeg `9.0.1` preprocessing identity/configuration and execution evidence.", "public child tasks")
    require_text(tasks, "- [x] `B2P07` Capture attempt-bound execution environment/hardware facts and preserve `CONTROLLED` versus `DIAGNOSTIC` semantics.", "public child tasks")
    require_text(tasks, "- [x] `B2P08` Freeze final pre-decode attempt manifest and verify `primary_decoding_started=false` at freeze.", "public child tasks")

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
    require_text(current, B2P03_CANONICAL_MERGE, "current frontier B2P03 canonical proof")
    require_text(current, f"run `{B2P03_POSTMERGE_SUBSET_RUN_ID}`", "current frontier B2P03 subset post-merge run proof")
    require_text(current, f"job `{B2P03_POSTMERGE_SUBSET_JOB_ID}`", "current frontier B2P03 subset post-merge job proof")
    require_text(current, f"run `{B2P03_POSTMERGE_METHODOLOGY_RUN_ID}`", "current frontier B2P03 methodology post-merge run proof")
    require_text(current, f"job `{B2P03_POSTMERGE_METHODOLOGY_JOB_ID}`", "current frontier B2P03 methodology post-merge job proof")
    require_text(current, B2P04_CANONICAL_MERGE, "current frontier B2P04 canonical proof")
    require_text(current, B2P04_QUALIFIED_HEAD, "current frontier B2P04 qualified-head proof")
    require_text(current, f"run `{B2P04_POSTMERGE_SUBSET_RUN_ID}`", "current frontier B2P04 subset post-merge run proof")
    require_text(current, f"job `{B2P04_POSTMERGE_SUBSET_JOB_ID}`", "current frontier B2P04 subset post-merge job proof")
    require_text(current, f"run `{B2P04_POSTMERGE_METHODOLOGY_RUN_ID}`", "current frontier B2P04 methodology post-merge run proof")
    require_text(current, f"job `{B2P04_POSTMERGE_METHODOLOGY_JOB_ID}`", "current frontier B2P04 methodology post-merge job proof")
    require_text(current, f"artifact `{B2P04_POSTMERGE_ARTIFACT_ID}`", "current frontier B2P04 post-merge artifact proof")
    require_text(current, B2P04_POSTMERGE_ARTIFACT_DIGEST, "current frontier B2P04 post-merge artifact digest proof")
    require_text(current, B2P04_MANIFEST_SHA256, "current frontier B2P04 manifest SHA proof")
    require_text(current, B2P04_FREEZE_DIGEST_SHA256, "current frontier B2P04 freeze digest proof")
    require_text(current, B2P05_CANONICAL_MERGE, "current frontier B2P05 canonical proof")
    require_text(current, B2P05_QUALIFIED_HEAD, "current frontier B2P05 qualified-head proof")
    require_text(current, f"run `{B2P05_POSTMERGE_REVALIDATION_RUN_ID}`", "current frontier B2P05 revalidation post-merge run proof")
    require_text(current, f"job `{B2P05_POSTMERGE_STATIC_JOB_ID}`", "current frontier B2P05 static post-merge job proof")
    require_text(current, f"job `{B2P05_POSTMERGE_LIVE_JOB_ID}`", "current frontier B2P05 live post-merge job proof")
    require_text(current, f"run `{B2P05_POSTMERGE_METHODOLOGY_RUN_ID}`", "current frontier B2P05 methodology post-merge run proof")
    require_text(current, f"job `{B2P05_POSTMERGE_METHODOLOGY_JOB_ID}`", "current frontier B2P05 methodology post-merge job proof")
    require_text(current, B2P06_CANONICAL_MERGE, "current frontier B2P06 canonical proof")
    require_text(current, B2P06_QUALIFIED_HEAD, "current frontier B2P06 qualified-head proof")
    require_text(current, f"run `{B2P06_POSTMERGE_PREPROCESSING_RUN_ID}`", "current frontier B2P06 preprocessing post-merge run proof")
    require_text(current, f"job `{B2P06_POSTMERGE_PREPROCESSING_JOB_ID}`", "current frontier B2P06 preprocessing post-merge job proof")
    require_text(current, f"artifact `{B2P06_POSTMERGE_PREPROCESSING_ARTIFACT_ID}`", "current frontier B2P06 preprocessing artifact proof")
    require_text(current, B2P06_POSTMERGE_PREPROCESSING_ARTIFACT_DIGEST, "current frontier B2P06 artifact digest proof")
    require_text(current, B2P06_EVIDENCE_SHA256, "current frontier B2P06 evidence digest proof")
    require_text(current, B2P07_CANONICAL_MERGE, "current frontier B2P07 canonical proof")
    require_text(current, B2P07_QUALIFIED_HEAD, "current frontier B2P07 qualified-head proof")
    require_text(current, f"run `{B2P07_POSTMERGE_ENVIRONMENT_RUN_ID}`", "current frontier B2P07 environment post-merge run proof")
    require_text(current, f"job `{B2P07_POSTMERGE_ENVIRONMENT_JOB_ID}`", "current frontier B2P07 environment post-merge job proof")
    require_text(current, f"run `{B2P07_POSTMERGE_METHODOLOGY_RUN_ID}`", "current frontier B2P07 methodology post-merge run proof")
    require_text(current, f"job `{B2P07_POSTMERGE_METHODOLOGY_JOB_ID}`", "current frontier B2P07 methodology post-merge job proof")
    require_text(current, B2P07_RAW_CAPTURE_COMMIT, "current frontier B2P07 raw-capture proof")
    require_text(current, B2P07_PROVENANCE_SEAL_COMMIT, "current frontier B2P07 provenance-seal proof")
    require_text(current, B2P08_CANONICAL_MERGE, "current frontier B2P08 canonical proof")
    require_text(current, B2P08_QUALIFIED_HEAD, "current frontier B2P08 qualified-head proof")
    require_text(current, B2P08_FREEZE_DIGEST, "current frontier B2P08 freeze proof")
    for run_id in (
        B2P08_POSTMERGE_ATTEMPT_RUN_ID,
        B2P08_POSTMERGE_METHODOLOGY_RUN_ID,
        B2P08_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID,
        B2P08_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID,
        B2P08_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID,
        B2P08_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID,
        B2P08_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID,
    ):
        require_text(current, f"run `{run_id}`", "current frontier B2P08 post-merge proof")
    require_text(current, "current bounded execution unit `B2E01`", "current frontier")
    require_text(current, "Execute and canonically qualify `B2E01` only", "current frontier next action")
    require_text(current, "B2E02 and all later candidate cells remain unauthorized", "current frontier successor boundary")
    require_absent(current, "current bounded execution unit `B2P07`", "current frontier stale unit")
    require_absent(current, "B2P07 is now authorized", "current frontier stale B2P07 authority wording")
    require_absent(current, "B2P08 attempt freeze, and primary decoding remain unauthorized during B2P07", "current frontier stale B2P07 successor wording")
    require_text(current, "B2E01 is now the only authorized bounded unit", "current frontier B2E01 baseline summary")
    require_text(current, "B2P08 pre-decode attempt freeze became canonical at merge `dd65e23d29e7f83b9a94aba9c018928c7f9cc41d`", "current frontier B2P08 active-route chronology")
    require_text(current, "B2P01 through B2P08 are complete and the final attempt manifest is frozen with `primary_decoding_started=false`.", "current frontier post-B2P08 completion")
    require_text(current, "B2E01 is the sole current bounded execution unit.", "current frontier B2E01 active-route authority")
    require_absent(current, "B2P01 through B2P07 are complete. B2P08 is the current bounded execution unit.", "current frontier stale B2P08 authority")
    require_absent(current, "Comparative decoding remains prohibited until the ordered pre-decode tasks `B2P01` through `B2P08` are genuinely complete", "current frontier stale pre-decode prohibition")

    require_text(current_state, B2P01_CANONICAL_MERGE, "current state B2P01 canonical proof")
    require_text(current_state, B2P02_CANONICAL_MERGE, "current state B2P02 canonical proof")
    require_text(current_state, f"run `{B2P02_POSTMERGE_RUN_ID}`", "current state B2P02 post-merge run proof")
    require_text(current_state, f"job `{B2P02_POSTMERGE_JOB_ID}`", "current state B2P02 post-merge job proof")
    require_text(current_state, f"artifact `{B2P02_POSTMERGE_ARTIFACT_ID}`", "current state B2P02 post-merge artifact proof")
    require_text(current_state, B2P02_POSTMERGE_ARTIFACT_DIGEST, "current state B2P02 post-merge artifact digest proof")
    require_text(current_state, B2P03_CANONICAL_MERGE, "current state B2P03 canonical proof")
    require_text(current_state, f"run `{B2P03_POSTMERGE_SUBSET_RUN_ID}`", "current state B2P03 subset post-merge run proof")
    require_text(current_state, f"job `{B2P03_POSTMERGE_SUBSET_JOB_ID}`", "current state B2P03 subset post-merge job proof")
    require_text(current_state, f"run `{B2P03_POSTMERGE_METHODOLOGY_RUN_ID}`", "current state B2P03 methodology post-merge run proof")
    require_text(current_state, f"job `{B2P03_POSTMERGE_METHODOLOGY_JOB_ID}`", "current state B2P03 methodology post-merge job proof")
    require_text(current_state, B2P04_CANONICAL_MERGE, "current state B2P04 canonical proof")
    require_text(current_state, B2P04_QUALIFIED_HEAD, "current state B2P04 qualified-head proof")
    require_text(current_state, f"run `{B2P04_POSTMERGE_SUBSET_RUN_ID}`", "current state B2P04 subset post-merge run proof")
    require_text(current_state, f"job `{B2P04_POSTMERGE_SUBSET_JOB_ID}`", "current state B2P04 subset post-merge job proof")
    require_text(current_state, f"run `{B2P04_POSTMERGE_METHODOLOGY_RUN_ID}`", "current state B2P04 methodology post-merge run proof")
    require_text(current_state, f"job `{B2P04_POSTMERGE_METHODOLOGY_JOB_ID}`", "current state B2P04 methodology post-merge job proof")
    require_text(current_state, f"artifact `{B2P04_POSTMERGE_ARTIFACT_ID}`", "current state B2P04 post-merge artifact proof")
    require_text(current_state, B2P04_POSTMERGE_ARTIFACT_DIGEST, "current state B2P04 post-merge artifact digest proof")
    require_text(current_state, B2P04_MANIFEST_SHA256, "current state B2P04 manifest SHA proof")
    require_text(current_state, B2P04_FREEZE_DIGEST_SHA256, "current state B2P04 freeze digest proof")
    require_text(current_state, B2P05_CANONICAL_MERGE, "current state B2P05 canonical proof")
    require_text(current_state, B2P05_QUALIFIED_HEAD, "current state B2P05 qualified-head proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_REVALIDATION_RUN_ID}`", "current state B2P05 revalidation post-merge run proof")
    require_text(current_state, f"job `{B2P05_POSTMERGE_STATIC_JOB_ID}`", "current state B2P05 static post-merge job proof")
    require_text(current_state, f"job `{B2P05_POSTMERGE_LIVE_JOB_ID}`", "current state B2P05 live post-merge job proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_METHODOLOGY_RUN_ID}`", "current state B2P05 methodology post-merge run proof")
    require_text(current_state, f"job `{B2P05_POSTMERGE_METHODOLOGY_JOB_ID}`", "current state B2P05 methodology post-merge job proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID}`", "current state B2P05 trusted materialization run proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID}`", "current state B2P05 trusted participant-materials run proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID}`", "current state B2P05 trusted participant-policy run proof")
    require_text(current_state, f"run `{B2P05_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID}`", "current state B2P05 trusted human-authority run proof")
    require_text(current_state, B2P06_CANONICAL_MERGE, "current state B2P06 canonical proof")
    require_text(current_state, B2P06_QUALIFIED_HEAD, "current state B2P06 qualified-head proof")
    require_text(current_state, f"run `{B2P06_POSTMERGE_PREPROCESSING_RUN_ID}`", "current state B2P06 preprocessing post-merge run proof")
    require_text(current_state, f"job `{B2P06_POSTMERGE_PREPROCESSING_JOB_ID}`", "current state B2P06 preprocessing post-merge job proof")
    require_text(current_state, f"artifact `{B2P06_POSTMERGE_PREPROCESSING_ARTIFACT_ID}`", "current state B2P06 preprocessing artifact proof")
    require_text(current_state, B2P06_POSTMERGE_PREPROCESSING_ARTIFACT_DIGEST, "current state B2P06 artifact digest proof")
    require_text(current_state, B2P06_EVIDENCE_SHA256, "current state B2P06 evidence digest proof")
    require_text(current_state, f"run `{B2P06_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID}`", "current state B2P06 candidate-revalidation run proof")
    require_text(current_state, f"run `{B2P06_POSTMERGE_METHODOLOGY_RUN_ID}`", "current state B2P06 methodology run proof")
    require_text(current_state, f"run `{B2P06_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID}`", "current state B2P06 trusted-materialization run proof")
    require_text(current_state, f"run `{B2P06_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID}`", "current state B2P06 participant-materials run proof")
    require_text(current_state, f"run `{B2P06_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID}`", "current state B2P06 participant-policy run proof")
    require_text(current_state, f"run `{B2P06_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID}`", "current state B2P06 human-authority run proof")
    require_text(current_state, B2P07_CANONICAL_MERGE, "current state B2P07 canonical proof")
    require_text(current_state, B2P07_QUALIFIED_HEAD, "current state B2P07 qualified-head proof")
    require_text(current_state, f"run `{B2P07_POSTMERGE_ENVIRONMENT_RUN_ID}`", "current state B2P07 environment run proof")
    require_text(current_state, f"job `{B2P07_POSTMERGE_ENVIRONMENT_JOB_ID}`", "current state B2P07 environment job proof")
    require_text(current_state, f"run `{B2P07_POSTMERGE_METHODOLOGY_RUN_ID}`", "current state B2P07 methodology run proof")
    require_text(current_state, f"job `{B2P07_POSTMERGE_METHODOLOGY_JOB_ID}`", "current state B2P07 methodology job proof")
    require_text(current_state, f"run `{B2P07_POSTMERGE_CANDIDATE_REVALIDATION_RUN_ID}`", "current state B2P07 candidate-revalidation run proof")
    require_text(current_state, f"run `{B2P07_POSTMERGE_TRUSTED_MATERIALIZATION_RUN_ID}`", "current state B2P07 trusted-materialization run proof")
    require_text(current_state, f"run `{B2P07_POSTMERGE_TRUSTED_PARTICIPANT_MATERIALS_RUN_ID}`", "current state B2P07 participant-materials run proof")
    require_text(current_state, f"run `{B2P07_POSTMERGE_TRUSTED_PARTICIPANT_POLICY_RUN_ID}`", "current state B2P07 participant-policy run proof")
    require_text(current_state, f"run `{B2P07_POSTMERGE_TRUSTED_HUMAN_AUTHORITY_RUN_ID}`", "current state B2P07 human-authority run proof")
    require_text(current_state, B2P07_RAW_CAPTURE_COMMIT, "current state B2P07 raw capture proof")
    require_text(current_state, B2P07_RAW_CAPTURE_EVIDENCE_BLOB, "current state B2P07 raw blob proof")
    require_text(current_state, B2P07_PROVENANCE_SEAL_COMMIT, "current state B2P07 seal proof")
    require_text(current_state, B2P07_SEALED_EVIDENCE_BLOB, "current state B2P07 sealed blob proof")
    require_text(current_state, B2P08_CANONICAL_MERGE, "current state B2P08 canonical proof")
    require_text(current_state, B2P08_QUALIFIED_HEAD, "current state B2P08 qualified-head proof")
    require_text(current_state, B2P08_FREEZE_DIGEST, "current state B2P08 freeze proof")
    require_text(current_state, "current bounded execution unit is `B2E01`", "current state")
    require_absent(current_state, "current bounded execution unit is `B2P07`", "current state stale unit")
    require_absent(current_state, "B2P08 authorized as the sole current bounded execution unit", "current state stale B2P08 authority")
    require_absent(current_state, "B2P08 remains unfrozen until its own execution unit", "current state stale B2P08 freeze wording")
    require_absent(current_state, "Execute and canonically qualify `B2P08` only", "current state stale B2P08 next action")

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

    for phrase in (
        "UNFROZEN_SELECTION_CANDIDATE", "require_discovery_unchanged", "O_NOFOLLOW",
    ):
        require_text(subset_selector, phrase, "B2P03 selector")
    for phrase in (
        "B2P03_CROSS_PARTITION_LATE_MUTATION_REJECTION=PASS", "B2P03_SUBSET_MANIFEST_FROZEN=NO",
        "B2P03_CANDIDATE_DECODING_STARTED=NO",
    ):
        require_text(subset_verifier, phrase, "B2P03 verifier")
    for phrase in (
        "000B2 Public Corpus Subset Selection", "persist-credentials: false",
        "python research/000b2-public/verify_subset_selection.py", "B2P03_POST_SNAPSHOT_ADDITION=PASS",
        "B2P03_SNAPSHOT_ENUMERATION_DELETION=PASS",
    ):
        require_text(subset_workflow, phrase, "B2P03 subset workflow")
    for phrase in (
        "000B2 Public Corpus Subset Freeze", "python-version: '3.12'", "cancel-in-progress: true",
        "python research/000b2-public/verify_subset_freeze.py",
        "python research/000b2-public/verify_subset_freeze_root_metadata.py",
        "--committed research/000b2-public/subset-manifest.json",
    ):
        require_text(subset_freeze_workflow, phrase, "B2P04 subset-freeze workflow")

    print("PUBLIC_CORPUS_METHODOLOGY=PASS")
    print("B2P01_CORPUS_PROVENANCE=PASS")
    print("B2P02_ARCHIVE_MATERIALIZATION=PASS")
    print(f"B2P02_PROBE_RUN_ID={B2P02_PROBE_RUN_ID}")
    print(f"B2P02_CANONICAL_MERGE={B2P02_CANONICAL_MERGE}")
    print(f"B2P02_POSTMERGE_RUN_ID={B2P02_POSTMERGE_RUN_ID}")
    print(f"B2P02_TEST_CLEAN_SHA256={EXPECTED_ARCHIVES['test-clean.tar.gz']['archive_sha256']}")
    print(f"B2P02_TEST_OTHER_SHA256={EXPECTED_ARCHIVES['test-other.tar.gz']['archive_sha256']}")
    print("B2P03_SUBSET_SELECTION=PASS")
    print(f"B2P03_CANONICAL_MERGE={B2P03_CANONICAL_MERGE}")
    print(f"B2P03_POSTMERGE_SUBSET_RUN_ID={B2P03_POSTMERGE_SUBSET_RUN_ID}")
    print(f"B2P03_POSTMERGE_METHODOLOGY_RUN_ID={B2P03_POSTMERGE_METHODOLOGY_RUN_ID}")
    print("B2P04_SUBSET_MANIFEST=PASS")
    print(f"B2P04_CANONICAL_MERGE={B2P04_CANONICAL_MERGE}")
    print(f"B2P04_POSTMERGE_SUBSET_RUN_ID={B2P04_POSTMERGE_SUBSET_RUN_ID}")
    print(f"B2P04_POSTMERGE_METHODOLOGY_RUN_ID={B2P04_POSTMERGE_METHODOLOGY_RUN_ID}")
    print(f"B2P04_MANIFEST_SHA256={B2P04_MANIFEST_SHA256}")
    print(f"B2P04_FREEZE_DIGEST_SHA256={B2P04_FREEZE_DIGEST_SHA256}")
    print("B2P05_CANDIDATE_REVALIDATION=PASS")
    print(f"B2P05_CANONICAL_MERGE={B2P05_CANONICAL_MERGE}")
    print(f"B2P05_POSTMERGE_REVALIDATION_RUN_ID={B2P05_POSTMERGE_REVALIDATION_RUN_ID}")
    print(f"B2P05_POSTMERGE_METHODOLOGY_RUN_ID={B2P05_POSTMERGE_METHODOLOGY_RUN_ID}")
    print("B2P06_PREPROCESSING_CAPTURE=PASS")
    print(f"B2P06_CANONICAL_MERGE={B2P06_CANONICAL_MERGE}")
    print(f"B2P06_POSTMERGE_PREPROCESSING_RUN_ID={B2P06_POSTMERGE_PREPROCESSING_RUN_ID}")
    print(f"B2P06_EVIDENCE_SHA256={B2P06_EVIDENCE_SHA256}")
    print("B2P07_ENVIRONMENT_CAPTURE=PASS")
    print(f"B2P07_CANONICAL_MERGE={B2P07_CANONICAL_MERGE}")
    print(f"B2P07_POSTMERGE_ENVIRONMENT_RUN_ID={B2P07_POSTMERGE_ENVIRONMENT_RUN_ID}")
    print("B2E01_FRONTIER=AUTHORIZED")
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
    print("SUBSET_SELECTION_STARTED=YES")
    print("SUBSET_SELECTION_CANONICAL=YES")
    print("SUBSET_MANIFEST_FROZEN=YES")
    print("CANDIDATE_DECODING_STARTED=NO")
    print("PRIMARY_DECODING_STARTED=NO")
    print("PRODUCT_CODE_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
