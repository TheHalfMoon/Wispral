#!/usr/bin/env python3
"""Qualify and execute the B2R08 deterministic sharding repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path
from typing import Any

import decode_b2r08 as b2r08

base = b2r08.base

ROOT = base.ROOT
PUBLIC = base.PUBLIC
REPAIR_PLAN_PATH = PUBLIC / "b2r08-repair-plan.json"

TASK = "B2R08"
ATTEMPT_ID = "000B2-PUBLIC-ATTEMPT-002"
CANDIDATE_ID = "whispercpp-balanced"
SHARD_COUNT = 4
EXPECTED_TOTAL_INPUTS = 240
EXPECTED_SHARD_SIZE = 60
SHARD_ADAPTER_TIMEOUT_SECONDS = 18000
QUALIFICATION_FIXTURE_COUNT = 8


class RepairError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RepairError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def semantic_row(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    result.pop("decode_wall_seconds", None)
    return result


def contiguous_partitions(uids: list[str], shard_count: int = SHARD_COUNT) -> list[list[str]]:
    require(shard_count > 0, "shard count must be positive")
    require(len(uids) >= shard_count, "not enough inputs for requested shards")
    quotient, remainder = divmod(len(uids), shard_count)
    parts: list[list[str]] = []
    start = 0
    for index in range(shard_count):
        size = quotient + (1 if index < remainder else 0)
        parts.append(uids[start:start + size])
        start += size
    require(start == len(uids), "partition accounting drift")
    require([uid for part in parts for uid in part] == uids, "partition order drift")
    require(len({uid for part in parts for uid in part}) == len(uids), "partition duplicate drift")
    return parts


def verify_repair_plan() -> dict[str, Any]:
    plan = load_json(REPAIR_PLAN_PATH)
    require(plan.get("schema_version") == "000b2-public-b2r08-repair-plan-v1", "repair plan schema drift")
    require(plan.get("task") == TASK and plan.get("attempt_id") == ATTEMPT_ID, "repair plan identity drift")
    require(plan.get("state") == "PREDECLARED_FORWARD_ONLY_ORCHESTRATION_REPAIR", "repair plan state drift")
    require(plan.get("prepared_after_candidate_result_exposure") is False, "repair was declared after result exposure")
    failed = plan.get("failed_primary_execution")
    require(isinstance(failed, dict), "failed-primary repair basis missing")
    require((failed.get("run_id"), failed.get("job_id"), failed.get("artifact_id")) ==
            (34067447713, 101578604948, 10005732797), "failed-primary identity drift")
    require(failed.get("artifact_zip_sha256") == "1a72b3553e7e7fd20c4c058a3d4d3d45fb88bff3d96a8563916c65a1da708a37",
            "failed-primary artifact digest drift")
    require(failed.get("artifact_contents") == ["whisper-build/wispral-build-identity.json"],
            "failed-primary artifact exposure drift")
    require(failed.get("transcript_artifact_present") is False and
            failed.get("evidence_json_present") is False and
            failed.get("candidate_result_available_before_repair") is False and
            failed.get("candidate_result_inspection_before_repair") is False,
            "repair is not result-independent")
    repair = plan.get("repair")
    require(isinstance(repair, dict), "repair block missing")
    require(repair.get("policy") == "FORWARD_ONLY_DETERMINISTIC_CONTIGUOUS_SHARDING_AFTER_HOSTED_RUNNER_CEILING",
            "repair policy drift")
    require(repair.get("shard_count") == SHARD_COUNT and
            repair.get("expected_total_input_count") == EXPECTED_TOTAL_INPUTS and
            repair.get("expected_shard_sizes") == [EXPECTED_SHARD_SIZE] * SHARD_COUNT,
            "repair shard plan drift")
    require(repair.get("partitioning") == "CONTIGUOUS_PARTITIONS_OF_SORTED_FROZEN_UTTERANCE_IDS",
            "repair partition policy drift")
    require(repair.get("per_shard_adapter_timeout_seconds") == SHARD_ADAPTER_TIMEOUT_SECONDS,
            "repair shard timeout drift")
    for key in (
        "candidate_changed",
        "model_changed",
        "runtime_revision_changed",
        "frozen_audio_membership_changed",
        "frozen_audio_bytes_changed",
        "frozen_input_order_changed_in_final_evidence",
        "c0_controls_changed",
        "scorer_changed",
        "normalization_changed",
        "reference_transcripts_loaded_during_decode",
        "accuracy_scoring_during_decode",
    ):
        require(repair.get(key) is False, f"repair semantic guard drift: {key}")
    qualification = plan.get("required_pre_primary_qualification")
    require(isinstance(qualification, dict) and
            qualification.get("status") == "REQUIRED_BEFORE_REPAIRED_PRIMARY_EXECUTION" and
            qualification.get("material_class") == "DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY" and
            qualification.get("primary_corpus_access") is False and
            qualification.get("candidate_result_access") is False and
            qualification.get("fail_closed") is True,
            "repair qualification guard drift")
    return plan


def verify_candidate_assets(model_path: Path, adapter: Path, build_identity_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    b2r08.validate_authority()
    family, config = base.operational_smoke.candidate_record(CANDIDATE_ID)
    require(family.get("family") == "whisper.cpp", "candidate family drift")
    require(family.get("runtime", {}).get("revision") == b2r08.EXPECTED_RUNTIME_REVISION, "runtime revision drift")
    require(family.get("model_source", {}).get("revision") == b2r08.EXPECTED_MODEL_SOURCE_REVISION,
            "model source revision drift")
    require(config.get("id") == CANDIDATE_ID and config.get("tier") == "BALANCED", "candidate cell drift")
    require(config.get("model") == b2r08.EXPECTED_MODEL_NAME, "candidate model name drift")
    require(model_path.is_file() and not model_path.is_symlink(), "model missing or unsafe")
    require(model_path.name == b2r08.EXPECTED_MODEL_NAME, "model filename drift")
    require(model_path.stat().st_size == b2r08.EXPECTED_MODEL_BYTES, "model size drift")
    require(base.sha256_file(model_path) == b2r08.EXPECTED_MODEL_SHA256, "model SHA-256 drift")
    artifacts = base.operational_smoke.verify_artifacts(CANDIDATE_ID, config, model_path.parent)
    require(len(artifacts) == 1 and artifacts[0].get("sha256") == b2r08.EXPECTED_MODEL_SHA256,
            "candidate artifact verification drift")
    require(adapter.is_file() and not adapter.is_symlink(), "adapter missing or unsafe")
    identity = base.validate_build_identity(build_identity_path, adapter)
    return artifacts, identity


def parse_adapter_output(path: Path, expected_frames: dict[str, int]) -> dict[str, dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    require(len(lines) == len(expected_frames), "adapter output cardinality drift")
    rows: dict[str, dict[str, Any]] = {}
    for line in lines:
        row = json.loads(line)
        require(isinstance(row, dict), "adapter row must be object")
        uid = row.get("utterance_id")
        require(isinstance(uid, str) and uid in expected_frames and uid not in rows, f"adapter identity drift: {uid}")
        require(row.get("status") in {"DECODED", "FAILED"}, f"adapter status drift: {uid}")
        require(isinstance(row.get("raw_lines"), list) and all(isinstance(v, str) for v in row["raw_lines"]),
                f"adapter raw lines malformed: {uid}")
        require(isinstance(row.get("raw_transcript"), str), f"adapter transcript malformed: {uid}")
        require(row["raw_transcript"] == base.reconstruct_stream_text(row["raw_lines"]),
                f"adapter stream reconstruction drift: {uid}")
        require(row.get("stream_iteration_count") == len(row["raw_lines"]), f"iteration accounting drift: {uid}")
        require(isinstance(row.get("decode_wall_seconds"), (int, float)) and row["decode_wall_seconds"] >= 0,
                f"timing malformed: {uid}")
        speech_count = expected_frames[uid]
        require(row.get("speech_sample_count") == speech_count, f"sample count drift: {uid}")
        regular = speech_count // base.REGULAR_CHUNK_SAMPLES
        final = speech_count % base.REGULAR_CHUNK_SAMPLES
        planned = regular + (1 if final else 0) + len(base.FINAL_ZERO_CHUNKS)
        require(row.get("regular_speech_chunk_count") == regular, f"regular chunk drift: {uid}")
        require(row.get("final_speech_chunk_samples") == final, f"final chunk drift: {uid}")
        require(isinstance(row.get("speech_samples_delivered"), int) and
                0 <= row["speech_samples_delivered"] <= speech_count, f"speech delivery drift: {uid}")
        require(isinstance(row.get("zero_suffix_samples_delivered"), int) and
                0 <= row["zero_suffix_samples_delivered"] <= base.FINAL_ZERO_SAMPLES,
                f"zero suffix delivery drift: {uid}")
        require(isinstance(row.get("zero_suffix_chunks_delivered"), int) and
                0 <= row["zero_suffix_chunks_delivered"] <= len(base.FINAL_ZERO_CHUNKS),
                f"zero suffix chunk drift: {uid}")
        require(row["stream_iteration_count"] <= planned, f"iteration count exceeds feed schedule: {uid}")
        if row["status"] == "DECODED":
            require(row.get("failure") is None, f"decoded row has failure: {uid}")
            require(row["stream_iteration_count"] == planned, f"decoded row incomplete: {uid}")
            require(row["speech_samples_delivered"] == speech_count, f"speech feed incomplete: {uid}")
            require(row["zero_suffix_samples_delivered"] == base.FINAL_ZERO_SAMPLES, f"zero suffix incomplete: {uid}")
            require(row["zero_suffix_chunks_delivered"] == len(base.FINAL_ZERO_CHUNKS), f"zero chunks incomplete: {uid}")
        else:
            require(isinstance(row.get("failure"), dict), f"failed row lacks failure evidence: {uid}")
        rows[uid] = row
    require(set(rows) == set(expected_frames), "adapter membership drift")
    return rows


def run_adapter(adapter: Path, model: Path, input_rows: list[tuple[str, Path, int]], work_dir: Path,
                label: str, timeout_seconds: int) -> tuple[dict[str, dict[str, Any]], str]:
    work_dir.mkdir(parents=True, exist_ok=True)
    input_list = work_dir / f"{label}-inputs.tsv"
    output = work_dir / f"{label}-adapter-output.jsonl"
    input_list.write_text("".join(f"{uid}\t{path}\n" for uid, path, _ in input_rows), encoding="utf-8")
    proc = subprocess.run(
        [str(adapter), "--model", str(model), "--input-list", str(input_list), "--output", str(output)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_seconds,
    )
    require(proc.returncode == 0, f"adapter failed for {label}: {proc.stdout[-4000:]}")
    expected = {uid: frames for uid, _, frames in input_rows}
    return parse_adapter_output(output, expected), proc.stdout


def generate_fixture_wav(path: Path, fixture_index: int, frame_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    amplitude = 1200 + fixture_index * 137
    period = 71 + fixture_index * 4
    phase = fixture_index * 11
    samples = bytearray()
    for n in range(frame_count):
        sign = 1 if (((n + phase) // max(1, period // 2)) % 2 == 0) else -1
        modulation = ((n * (fixture_index + 3)) % 97) - 48
        value = max(-32768, min(32767, sign * amplitude + modulation))
        samples.extend(struct.pack("<h", value))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(bytes(samples))


def qualify(args: argparse.Namespace) -> dict[str, Any]:
    plan = verify_repair_plan()
    artifacts, build_identity = verify_candidate_assets(args.model, args.adapter, args.build_identity)
    fixture_root = args.work_dir / "fixtures"
    frame_counts = [9000, 11000, 13000, 15000, 17000, 19000, 21000, 23000]
    require(len(frame_counts) == QUALIFICATION_FIXTURE_COUNT, "qualification fixture count drift")
    fixture_rows: list[tuple[str, Path, int]] = []
    fixture_manifest: list[dict[str, Any]] = []
    for index, frames in enumerate(frame_counts):
        uid = f"fixture-{index:02d}"
        path = fixture_root / f"{uid}.wav"
        generate_fixture_wav(path, index, frames)
        fixture_rows.append((uid, path, frames))
        fixture_manifest.append({
            "utterance_id": uid,
            "frame_count": frames,
            "wav_sha256": base.sha256_file(path),
            "wav_size_bytes": path.stat().st_size,
        })

    full_rows, _ = run_adapter(args.adapter, args.model, fixture_rows, args.work_dir / "full",
                               "qualification-full", 3600)
    uids = [uid for uid, _, _ in fixture_rows]
    parts = contiguous_partitions(uids, SHARD_COUNT)
    row_lookup = {uid: (uid, path, frames) for uid, path, frames in fixture_rows}
    sharded_rows: dict[str, dict[str, Any]] = {}
    for shard_index, part in enumerate(parts):
        rows, _ = run_adapter(
            args.adapter,
            args.model,
            [row_lookup[uid] for uid in part],
            args.work_dir / f"shard-{shard_index}",
            f"qualification-shard-{shard_index}",
            3600,
        )
        require(not (set(sharded_rows) & set(rows)), "qualification shard duplicate")
        sharded_rows.update(rows)

    require(set(full_rows) == set(sharded_rows) == set(uids), "qualification membership drift")
    mismatches: list[str] = []
    for uid in uids:
        if canonical(semantic_row(full_rows[uid])) != canonical(semantic_row(sharded_rows[uid])):
            mismatches.append(uid)
    require(not mismatches, f"single-process/sharded semantic mismatch: {mismatches}")

    evidence = {
        "schema_version": "000b2-public-b2r08-shard-equivalence-v1",
        "task": TASK,
        "attempt_id": ATTEMPT_ID,
        "state": "NON_PRIMARY_SHARD_EQUIVALENCE_QUALIFIED",
        "material_class": "DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY",
        "primary_corpus_accessed": False,
        "candidate_result_accessed": False,
        "repair_plan_sha256": base.sha256_file(REPAIR_PLAN_PATH),
        "candidate": {
            "candidate_id": CANDIDATE_ID,
            "runtime_revision": b2r08.EXPECTED_RUNTIME_REVISION,
            "runtime_source_tree": b2r08.EXPECTED_RUNTIME_TREE,
            "model_source_revision": b2r08.EXPECTED_MODEL_SOURCE_REVISION,
            "model": b2r08.EXPECTED_MODEL_NAME,
            "artifacts": artifacts,
            "adapter_build_identity": build_identity,
        },
        "qualification": {
            "fixture_count": len(fixture_rows),
            "shard_count": SHARD_COUNT,
            "partitioning": "CONTIGUOUS_PARTITIONS_OF_SORTED_FIXTURE_IDS",
            "ignored_fields": ["decode_wall_seconds"],
            "semantic_rows_byte_identical": True,
            "mismatch_count": 0,
            "fixture_manifest": fixture_manifest,
            "full_semantic_sha256": sha256_bytes(canonical([semantic_row(full_rows[uid]) for uid in uids])),
            "sharded_semantic_sha256": sha256_bytes(canonical([semantic_row(sharded_rows[uid]) for uid in uids])),
        },
        "run": runtime_provenance(),
        "claim_guards": plan["claim_guards"],
    }
    evidence["evidence_payload_sha256"] = sha256_bytes(canonical(evidence))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def runtime_provenance() -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    require(run_id.isdigit() and int(run_id) > 0, "GITHUB_RUN_ID missing")
    require(run_attempt.isdigit() and int(run_attempt) > 0, "GITHUB_RUN_ATTEMPT missing")
    return {
        "repository_revision": base.git_head(),
        "github_repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "github_run_id": int(run_id),
        "github_run_attempt": int(run_attempt),
        "github_job": os.environ.get("GITHUB_JOB", ""),
        "runner_os": os.environ.get("RUNNER_OS", ""),
        "runner_arch": os.environ.get("RUNNER_ARCH", ""),
        "runner_environment": os.environ.get("RUNNER_ENVIRONMENT", ""),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.system(),
        "timing_semantics": "DIAGNOSTIC_ONLY",
        "comparative_performance_authorized": False,
    }


def primary_shard(args: argparse.Namespace) -> dict[str, Any]:
    plan = verify_repair_plan()
    _, build_identity = verify_candidate_assets(args.model, args.adapter, args.build_identity)
    _, _, preprocessing = b2r08.validate_authority()
    indexed = base.build_preprocessing_index(preprocessing)
    uids = sorted(indexed)
    require(len(uids) == EXPECTED_TOTAL_INPUTS, "primary input count drift")
    parts = contiguous_partitions(uids, SHARD_COUNT)
    require([len(part) for part in parts] == [EXPECTED_SHARD_SIZE] * SHARD_COUNT, "primary shard size drift")
    require(0 <= args.shard_index < SHARD_COUNT, "invalid shard index")
    selected = parts[args.shard_index]

    rows_input: list[tuple[str, Path, int]] = []
    for uid in selected:
        source = indexed[uid]
        partition = source.get("source_partition")
        require(isinstance(partition, str) and partition in {"test-clean", "test-other"}, f"partition drift: {uid}")
        wav = args.preprocessed_root / partition / f"{uid}.wav"
        require(wav.is_file() and not wav.is_symlink(), f"preprocessed WAV missing or unsafe: {uid}")
        require(base.sha256_file(wav) == source.get("canonical_preprocessed_file_sha256"), f"WAV digest drift: {uid}")
        require(wav.stat().st_size == source.get("canonical_preprocessed_bytes"), f"WAV size drift: {uid}")
        rows_input.append((uid, wav, int(source["wav_frame_count"])))

    started = time.perf_counter()
    observed, adapter_stdout = run_adapter(
        args.adapter, args.model, rows_input, args.work_dir,
        f"b2r08-primary-shard-{args.shard_index}", SHARD_ADAPTER_TIMEOUT_SECONDS
    )
    records: list[dict[str, Any]] = []
    for uid in selected:
        source = indexed[uid]
        row = observed[uid]
        records.append({
            "utterance_id": uid,
            "source_partition": source["source_partition"],
            "canonical_preprocessed_file_sha256": source["canonical_preprocessed_file_sha256"],
            "status": row["status"],
            "raw_lines": row["raw_lines"],
            "raw_transcript": row["raw_transcript"],
            "failure": row["failure"],
            "stream_iteration_count": row["stream_iteration_count"],
            "speech_sample_count": row["speech_sample_count"],
            "speech_samples_delivered": row["speech_samples_delivered"],
            "regular_speech_chunk_count": row["regular_speech_chunk_count"],
            "final_speech_chunk_samples": row["final_speech_chunk_samples"],
            "zero_suffix_samples_delivered": row["zero_suffix_samples_delivered"],
            "zero_suffix_chunks_delivered": row["zero_suffix_chunks_delivered"],
            "decode_wall_seconds": row["decode_wall_seconds"],
        })
    shard = {
        "schema_version": "000b2-public-b2r08-primary-shard-v1",
        "task": TASK,
        "attempt_id": ATTEMPT_ID,
        "candidate_id": CANDIDATE_ID,
        "shard_index": args.shard_index,
        "shard_count": SHARD_COUNT,
        "partitioning": "CONTIGUOUS_PARTITIONS_OF_SORTED_FROZEN_UTTERANCE_IDS",
        "expected_total_input_count": EXPECTED_TOTAL_INPUTS,
        "expected_shard_size": EXPECTED_SHARD_SIZE,
        "utterance_ids": selected,
        "repair_plan_sha256": base.sha256_file(REPAIR_PLAN_PATH),
        "build_identity": build_identity,
        "run": runtime_provenance(),
        "execution": {
            "input_count": len(records),
            "decoded_count": sum(row["status"] == "DECODED" for row in records),
            "failure_count": sum(row["status"] != "DECODED" for row in records),
            "records": records,
            "shard_decode_wall_seconds": round(time.perf_counter() - started, 9),
            "adapter_stdout_tail": adapter_stdout[-2000:],
            "reference_transcripts_loaded_by_decoder": False,
            "accuracy_scoring_performed": False,
        },
        "claim_guards": plan["claim_guards"],
    }
    shard["evidence_payload_sha256"] = sha256_bytes(canonical(shard))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(shard, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return shard


def merge_primary(args: argparse.Namespace) -> dict[str, Any]:
    plan = verify_repair_plan()
    b2r08.validate_authority()
    require(len(args.shard_evidence) == SHARD_COUNT, "exactly four shard evidence files required")
    _, attempt, preprocessing = b2r08.validate_authority()
    indexed = base.build_preprocessing_index(preprocessing)
    uids = sorted(indexed)
    require(len(uids) == EXPECTED_TOTAL_INPUTS, "primary input count drift")
    expected_parts = contiguous_partitions(uids, SHARD_COUNT)

    shards: list[dict[str, Any]] = []
    records_by_uid: dict[str, dict[str, Any]] = {}
    build_identities: list[dict[str, Any]] = []
    shard_runs: list[dict[str, Any]] = []
    for path in args.shard_evidence:
        shard = load_json(path)
        require(shard.get("schema_version") == "000b2-public-b2r08-primary-shard-v1", f"shard schema drift: {path}")
        index = shard.get("shard_index")
        require(isinstance(index, int) and 0 <= index < SHARD_COUNT, f"shard index drift: {path}")
        shards.append(shard)
    shards.sort(key=lambda item: item["shard_index"])
    require([item["shard_index"] for item in shards] == list(range(SHARD_COUNT)), "shard index coverage drift")

    for index, shard in enumerate(shards):
        require(shard.get("attempt_id") == ATTEMPT_ID and shard.get("candidate_id") == CANDIDATE_ID,
                f"shard identity drift: {index}")
        require(shard.get("repair_plan_sha256") == base.sha256_file(REPAIR_PLAN_PATH), f"repair plan binding drift: {index}")
        require(shard.get("utterance_ids") == expected_parts[index], f"shard membership/order drift: {index}")
        execution = shard.get("execution")
        require(isinstance(execution, dict), f"shard execution missing: {index}")
        records = execution.get("records")
        require(isinstance(records, list) and len(records) == EXPECTED_SHARD_SIZE, f"shard record count drift: {index}")
        require(execution.get("reference_transcripts_loaded_by_decoder") is False and
                execution.get("accuracy_scoring_performed") is False, f"shard scoring/reference guard drift: {index}")
        for row, uid in zip(records, expected_parts[index], strict=True):
            require(row.get("utterance_id") == uid, f"shard record order drift: {index}:{uid}")
            require(uid not in records_by_uid, f"duplicate primary record: {uid}")
            records_by_uid[uid] = row
        build = shard.get("build_identity")
        require(isinstance(build, dict), f"shard build identity missing: {index}")
        build_identities.append({"shard_index": index, "identity": build})
        run = shard.get("run")
        require(isinstance(run, dict), f"shard run identity missing: {index}")
        shard_runs.append({"shard_index": index, "run": run})

    require(set(records_by_uid) == set(uids), "merged primary membership drift")
    records = [records_by_uid[uid] for uid in uids]
    decoded = sum(row["status"] == "DECODED" for row in records)
    failed = len(records) - decoded

    artifacts = [{
        "path": b2r08.EXPECTED_MODEL_NAME,
        "size_bytes": b2r08.EXPECTED_MODEL_BYTES,
        "sha256": b2r08.EXPECTED_MODEL_SHA256,
    }]
    evidence: dict[str, Any] = {
        "schema_version": "000b2-public-b2r08-decode-v2",
        "task": TASK,
        "state": "ATTEMPT_002_C0_PRIMARY_DECODE_CAPTURED",
        "attempt_id": ATTEMPT_ID,
        "candidate": {
            "cell_index": 4,
            "candidate_id": CANDIDATE_ID,
            "family": "whisper.cpp",
            "tier": "BALANCED",
            "runtime_revision": b2r08.EXPECTED_RUNTIME_REVISION,
            "runtime_source_tree": b2r08.EXPECTED_RUNTIME_TREE,
            "model_source_revision": b2r08.EXPECTED_MODEL_SOURCE_REVISION,
            "model": b2r08.EXPECTED_MODEL_NAME,
            "artifacts": artifacts,
            "adapter_build_identities": build_identities,
            "streaming_semantics_observed": True,
        },
        "authority": {
            "canonical_authority_base": b2r08.EXPECTED_AUTHORITY_BASE,
            "attempt_manifest_path": "research/000b2-public/attempt-002-manifest.json",
            "attempt_manifest_sha256": base.sha256_file(b2r08.ATTEMPT_MANIFEST_PATH),
            "attempt_freeze_digest_sha256": attempt["freeze_digest_sha256"],
            "preprocessing_capture_path": "research/000b2-public/preprocessing-capture.json",
            "preprocessing_capture_sha256": base.sha256_file(b2r08.PREPROCESSING_CAPTURE_PATH),
            "repair_plan_path": "research/000b2-public/b2r08-repair-plan.json",
            "repair_plan_sha256": base.sha256_file(REPAIR_PLAN_PATH),
        },
        "c0_controls": {
            "language": "en",
            "threads": 4,
            "step_ms": 500,
            "regular_chunk_samples": b2r08.REGULAR_CHUNK_SAMPLES,
            "final_speech_chunk_preserved": True,
            "length_ms": 5000,
            "keep_ms": 200,
            "max_tokens": 0,
            "audio_ctx": 0,
            "beam_size": -1,
            "sampling": "GREEDY",
            "temperature_fallback": "OFF",
            "translate": False,
            "keep_context": False,
            "initial_prompt": None,
            "prompt_carryover": False,
            "vad": False,
            "timestamps": False,
            "single_segment": True,
            "use_gpu": False,
            "flash_attention": False,
            "repository_context_used": False,
            "test_specific_context_used": False,
            "candidate_specific_audio_transform_used": False,
            "identical_frozen_audio_required_across_candidates": True,
            "finalization_zero_pad_samples": b2r08.FINAL_ZERO_SAMPLES,
            "zero_suffix_chunk_samples": b2r08.FINAL_ZERO_CHUNKS,
            "raw_transcript_materialization": b2r08.RAW_TRANSCRIPT_MATERIALIZATION,
        },
        "execution_orchestration": {
            "policy": "FORWARD_ONLY_DETERMINISTIC_CONTIGUOUS_SHARDING_AFTER_HOSTED_RUNNER_CEILING",
            "shard_count": SHARD_COUNT,
            "shard_sizes": [len(part) for part in expected_parts],
            "partitioning": "CONTIGUOUS_PARTITIONS_OF_SORTED_FROZEN_UTTERANCE_IDS",
            "final_record_order": "ORIGINAL_SORTED_FROZEN_UTTERANCE_ID_ORDER",
            "per_shard_adapter_processes": 1,
            "per_shard_adapter_timeout_seconds": SHARD_ADAPTER_TIMEOUT_SECONDS,
            "failed_primary_run_id": 34067447713,
            "failed_primary_job_id": 101578604948,
            "failed_primary_artifact_id": 10005732797,
            "failed_primary_artifact_zip_sha256": "1a72b3553e7e7fd20c4c058a3d4d3d45fb88bff3d96a8563916c65a1da708a37",
            "failed_primary_transcript_artifact_present": False,
            "failed_primary_evidence_json_present": False,
            "candidate_result_inspection_before_repair": False,
            "equivalence_qualification_run_id": int(os.environ["B2R08_EQUIVALENCE_RUN_ID"]),
            "equivalence_qualification_evidence_sha256": os.environ["B2R08_EQUIVALENCE_EVIDENCE_SHA256"],
            "candidate_changed": False,
            "model_changed": False,
            "runtime_revision_changed": False,
            "frozen_audio_membership_changed": False,
            "frozen_audio_bytes_changed": False,
            "frozen_input_order_changed_in_final_evidence": False,
            "c0_controls_changed": False,
            "scorer_changed": False,
            "normalization_changed": False,
        },
        "run": runtime_provenance(),
        "shard_runs": shard_runs,
        "execution": {
            "input_count": len(records),
            "decoded_count": decoded,
            "failure_count": failed,
            "all_frozen_input_hashes_reverified": True,
            "all_speech_samples_delivered_for_decoded_records": all(
                row["status"] != "DECODED" or row["speech_samples_delivered"] == row["speech_sample_count"]
                for row in records
            ),
            "all_zero_suffix_samples_delivered_for_decoded_records": all(
                row["status"] != "DECODED" or row["zero_suffix_samples_delivered"] == b2r08.FINAL_ZERO_SAMPLES
                for row in records
            ),
            "reference_transcripts_loaded_by_decoder": False,
            "accuracy_scoring_performed": False,
            "comparative_ranking_present": False,
            "performance_claim_present": False,
            "records": records,
        },
        "claim_guards": {
            "human_developer_speech_accuracy_evidence": "ABSENT",
            "comparative_result_available": False,
            "comparative_performance_authorized": False,
            "production_stt_selected": False,
            "product_code_authorized": False,
            "b2r09_authorized": False,
        },
    }
    evidence["evidence_payload_sha256"] = sha256_bytes(canonical(evidence))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    q = sub.add_parser("qualify")
    q.add_argument("--work-dir", type=Path, required=True)
    q.add_argument("--model", type=Path, required=True)
    q.add_argument("--adapter", type=Path, required=True)
    q.add_argument("--build-identity", type=Path, required=True)
    q.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("shard")
    s.add_argument("--shard-index", type=int, required=True)
    s.add_argument("--work-dir", type=Path, required=True)
    s.add_argument("--preprocessed-root", type=Path, required=True)
    s.add_argument("--model", type=Path, required=True)
    s.add_argument("--adapter", type=Path, required=True)
    s.add_argument("--build-identity", type=Path, required=True)
    s.add_argument("--output", type=Path, required=True)

    m = sub.add_parser("merge")
    m.add_argument("--shard-evidence", type=Path, action="append", required=True)
    m.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "qualify":
            evidence = qualify(args)
            print("B2R08_SHARD_EQUIVALENCE=PASS")
            print(f"B2R08_QUALIFICATION_FIXTURES={evidence['qualification']['fixture_count']}")
            print(f"B2R08_QUALIFICATION_PAYLOAD_SHA256={evidence['evidence_payload_sha256']}")
            print("B2R08_PRIMARY_CORPUS_ACCESSED=NO")
            print("B2R09_AUTHORIZED=NO")
        elif args.mode == "shard":
            evidence = primary_shard(args)
            print("B2R08_PRIMARY_SHARD=CAPTURED")
            print(f"B2R08_SHARD_INDEX={evidence['shard_index']}")
            print(f"B2R08_SHARD_INPUTS={evidence['execution']['input_count']}")
            print(f"B2R08_SHARD_DECODED={evidence['execution']['decoded_count']}")
            print(f"B2R08_SHARD_FAILURES={evidence['execution']['failure_count']}")
            print("B2R09_AUTHORIZED=NO")
        else:
            evidence = merge_primary(args)
            print("B2R08_EXECUTION=CAPTURED")
            print(f"B2R08_INPUTS={evidence['execution']['input_count']}")
            print(f"B2R08_DECODED={evidence['execution']['decoded_count']}")
            print(f"B2R08_FAILURES={evidence['execution']['failure_count']}")
            print(f"B2R08_PAYLOAD_SHA256={evidence['evidence_payload_sha256']}")
            print("B2R09_AUTHORIZED=NO")
        return 0
    except (RepairError, base.DecodeError, OSError, KeyError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"B2R08_REPAIR=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
