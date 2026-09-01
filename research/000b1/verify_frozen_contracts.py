#!/usr/bin/env python3
"""Pin the semantic surface of the 000B1 frozen candidate and schema contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMAS = HERE / "schemas"

SELECTION_RULE = (
    "For each family and tier, select at most one configuration: the largest qualifying "
    "English configuration that does not exceed the tier ceiling using pre-result metadata only."
)
CANDIDATE_IDS = {
    "moonshine-compact",
    "moonshine-balanced",
    "whispercpp-compact",
    "whispercpp-balanced",
    "sherpa-onnx-compact",
    "sherpa-onnx-balanced",
}
RUNTIMES = {
    "moonshine": "234f60faa0eb388b01cdf7e60aca232af37aefda",
    "whisper.cpp": "371b5a7561823ab2bb32142d2751e35e7534727b",
    "sherpa-onnx": "917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e",
}
EXPECTED_CELLS = {
    "moonshine-compact": ("moonshine", "COMPACT", "small-streaming-en", 142300974),
    "moonshine-balanced": ("moonshine", "BALANCED", "medium-streaming-en", 269141623),
    "whispercpp-compact": ("whisper.cpp", "COMPACT", "ggml-base.en.bin", 147964211),
    "whispercpp-balanced": ("whisper.cpp", "BALANCED", "ggml-small.en.bin", 487614201),
    "sherpa-onnx-compact": ("sherpa-onnx", "COMPACT", "INT8 ONNX", 72899649),
    "sherpa-onnx-balanced": ("sherpa-onnx", "BALANCED", "FP32 ONNX", 265495984),
}
EXPECTED_ARTIFACTS = {
    "whispercpp-compact": {
        "ggml-base.en.bin": (147964211, "a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002", "PINNED")
    },
    "whispercpp-balanced": {
        "ggml-small.en.bin": (487614201, "c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d", "PINNED")
    },
    "sherpa-onnx-compact": {
        "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx": (71083163, "563fde436d16cf7607cf408cd6b30909819d03162652ef389c2450ced3f45ac1", "PINNED"),
        "decoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx": (1307236, "98da299f471e38bb4e1a8df579b8cc9122d6039576a77e357b3c60f17dd83b02", "PINNED"),
        "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx": (259335, "d944208d660d67c8d72cd2acaeac971fa5ceb8c80e76c1968148846fedd6e297", "PINNED"),
        "bpe.model": (244865, "c53433de083c4a6ad12d034550ef22de68cec62c4f58932a7b6b8b2f1e743fa5", "PINNED"),
        "tokens.txt": (5050, None, "PENDING_B2_MATERIALIZATION"),
    },
    "sherpa-onnx-balanced": {
        "encoder-epoch-99-avg-1-chunk-16-left-128.onnx": (262127043, "a423883ce5754507fd941755ab0b5bc426a84ac670cbe21cf060e9e2c66dc660", "PINNED"),
        "decoder-epoch-99-avg-1-chunk-16-left-128.onnx": (2092621, "7bf787f90b194b307e5a4ad6a34fadb4e748304c35f78a8d66358a05b13ee6ef", "PINNED"),
        "joiner-epoch-99-avg-1-chunk-16-left-128.onnx": (1026405, "210591f72b3c56b8364f85f345dca240bc2b4c00632848f4aa923630d5639d3b", "PINNED"),
        "bpe.model": (244865, "c53433de083c4a6ad12d034550ef22de68cec62c4f58932a7b6b8b2f1e743fa5", "PINNED"),
        "tokens.txt": (5050, None, "PENDING_B2_MATERIALIZATION"),
    },
}
MOONSHINE_PATHS = {
    "moonshine-compact": {
        "adapter.ort": 2870368, "cross_kv.ort": 5356536, "decoder_kv.ort": 81878600,
        "encoder.ort": 44148576, "frontend.model.ort": 26944, "frontend.weights.ort": 7769464,
        "streaming_config.json": 512, "tokenizer.bin": 249974,
    },
    "moonshine-balanced": {
        "adapter.ort": 3651296, "cross_kv.ort": 11643776, "decoder_kv.ort": 146972408,
        "encoder.ort": 94705376, "frontend.model.ort": 28720, "frontend.weights.ort": 11889560,
        "streaming_config.json": 513, "tokenizer.bin": 249974,
    },
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise AssertionError(message)


def verify_registry() -> None:
    registry = load(HERE / "qualified-candidates.json")
    if registry.get("selection_rule") != SELECTION_RULE:
        fail("candidate selection_rule drift")
    if registry.get("tiers") != {
        "COMPACT": {"min_exclusive_bytes": 0, "max_inclusive_bytes": 167772160},
        "BALANCED": {"min_exclusive_bytes": 167772160, "max_inclusive_bytes": 536870912},
    }:
        fail("candidate tier contract drift")

    families = {family["family"]: family for family in registry["families"]}
    if set(families) != set(RUNTIMES):
        fail("candidate family allowlist drift")
    for family_name, revision in RUNTIMES.items():
        if families[family_name]["runtime"]["revision"] != revision:
            fail(f"{family_name} runtime revision drift")

    if families["moonshine"]["model_source"].get("asset_revision") != "quantized_26_08_21":
        fail("Moonshine model source drift")
    whisper_source = families["whisper.cpp"]["model_source"]
    if whisper_source.get("revision") != "80da2d8bfee42b0e836fc3a9890373e5defc00a6":
        fail("whisper model source revision drift")
    if whisper_source.get("base_url") != "https://huggingface.co/ggerganov/whisper.cpp/resolve/80da2d8bfee42b0e836fc3a9890373e5defc00a6":
        fail("whisper model source URL drift")
    sherpa_source = families["sherpa-onnx"]["model_source"]
    if sherpa_source.get("onnx_revision") != "6037ea07e3abfe599ad00d418968bcf9656e7472":
        fail("sherpa ONNX source revision drift")

    cells = {}
    for family_name, family in families.items():
        for config in family["configurations"]:
            cells[config["id"]] = (family_name, config)
    if set(cells) != CANDIDATE_IDS:
        fail("candidate cell allowlist drift")

    for candidate_id, expected in EXPECTED_CELLS.items():
        family_name, config = cells[candidate_id]
        observed = (family_name, config["tier"], config["model"], config["payload_total_bytes"])
        if observed != expected:
            fail(f"{candidate_id} identity/model/payload drift: {observed!r}")
        if config.get("status") != "QUALIFIED_PREREGISTERED":
            fail(f"{candidate_id} qualification status drift")

        artifacts = {
            artifact["path"]: (artifact["size_bytes"], artifact.get("sha256"), artifact.get("sha256_status"))
            for artifact in config["artifacts"]
        }
        if candidate_id in MOONSHINE_PATHS:
            expected_paths = MOONSHINE_PATHS[candidate_id]
            if {path: value[0] for path, value in artifacts.items()} != expected_paths:
                fail(f"{candidate_id} artifact identity/size drift")
            if any(value[1] is not None or value[2] != "PENDING_B2_MATERIALIZATION" for value in artifacts.values()):
                fail(f"{candidate_id} pending materialization posture drift")
        elif artifacts != EXPECTED_ARTIFACTS[candidate_id]:
            fail(f"{candidate_id} artifact identity/digest drift")


def verify_schema_semantics() -> None:
    attempt = load(SCHEMAS / "attempt-manifest.schema.json")
    required = set(attempt["required"])
    for key in ("qualified_candidates_sha256", "frozen_methodology_sha256", "exclusions"):
        if key not in required:
            fail(f"attempt schema lost required field {key}")
    candidate = attempt["properties"]["candidates"]["items"]
    if set(candidate["properties"]["candidate_id"]["enum"]) != CANDIDATE_IDS:
        fail("attempt schema candidate allowlist drift")
    for key in ("family", "operational_qualification"):
        if key not in candidate["required"]:
            fail(f"attempt candidate schema lost {key}")
    if attempt["properties"]["preprocessing"]["properties"]["tool_version"].get("const") != "9.0.1":
        fail("attempt preprocessing schema FFmpeg version drift")
    if attempt["properties"]["preprocessing"]["properties"]["canonical_format"].get("const") != "PCM_WAV":
        fail("attempt preprocessing schema format drift")

    qualified = load(SCHEMAS / "qualified-candidates.schema.json")
    qtiers = qualified["properties"]["tiers"]["properties"]
    if qtiers["COMPACT"]["properties"]["max_inclusive_bytes"].get("const") != 167772160:
        fail("qualified candidate COMPACT schema drift")
    if qtiers["BALANCED"]["properties"]["max_inclusive_bytes"].get("const") != 536870912:
        fail("qualified candidate BALANCED schema drift")
    qconfig = qualified["properties"]["families"]["items"]["properties"]["configurations"]["items"]
    if set(qconfig["properties"]["id"]["enum"]) != CANDIDATE_IDS:
        fail("qualified candidate schema cell allowlist drift")

    frozen = load(SCHEMAS / "frozen-methodology.schema.json")
    speaker = frozen["properties"]["speaker_design"]["properties"]
    if speaker["total_human_speakers"].get("const") != 20 or speaker["planned_total_utterances"].get("const") != 720:
        fail("frozen methodology schema speaker/corpus drift")
    prep = frozen["properties"]["preprocessing"]["properties"]
    if prep["version"].get("const") != "9.0.1" or prep["canonical_format"].get("const") != "PCM_WAV":
        fail("frozen methodology schema preprocessing drift")
    common = frozen["properties"]["common_c0"].get("const", {})
    if common.get("repository_context") != "OFF" or common.get("external_language_model") != "OFF":
        fail("frozen methodology schema C0 bias boundary drift")

    entity = load(SCHEMAS / "entity-annotation.schema.json")
    entity_props = entity["properties"]["entities"]["items"]["properties"]
    if entity_props["start_char"].get("minimum") != 0 or entity_props["end_char"].get("minimum") != 1:
        fail("entity annotation offset schema drift")
    validator_path = HERE / "validate_entity_annotation.py"
    if not validator_path.is_file():
        fail("entity annotation semantic validator missing")


def main() -> int:
    try:
        verify_registry()
        verify_schema_semantics()
    except (AssertionError, KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"VERIFY_FROZEN_CONTRACTS=FAIL: {exc}", file=sys.stderr)
        return 1
    print("VERIFY_FROZEN_CONTRACTS=PASS")
    print("CANDIDATE_ALLOWLIST=PINNED")
    print("SCHEMA_SEMANTICS=PINNED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
