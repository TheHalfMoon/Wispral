#!/usr/bin/env python3
"""Fail-closed verifier for the 000B2 human corpus manifest format.

The verifier checks only repository-visible structure and deterministic digests.
It does not attest participant consent, recording chronology, media provenance, or
primary-decoding authority. Synthetic self-test fixtures are never benchmark data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "corpus-manifest.schema.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SPEAKER_ID = re.compile(r"^spk-[0-9a-f]{8}$")
UTTERANCE_ID = re.compile(r"^utt-[0-9a-f]{12}$")
PROFILE_ID = re.compile(r"^env-[0-9a-f]{8}$")
EXPECTED_SPEAKERS = {"development": 4, "qualification": 4, "test": 12}
EXPECTED_TOTAL_SPEAKERS = 20
EXPECTED_PER_SPEAKER = {"DEVELOPER_ENTITY": 24, "GENERAL_COLLATERAL": 12}
EXPECTED_TOTAL_UTTERANCES = 720
EXPECTED_TEST_UTTERANCES = 432
CADENCES = {"SLOW", "CONVERSATIONAL", "FAST_INTELLIGIBLE"}
ROOT_KEYS = {
    "schema_version",
    "corpus_status",
    "frozen",
    "freeze_digest_sha256",
    "primary_test_manifest_sha256",
    "authority_status",
    "consent_records_sha256",
    "direct_identifiers_present",
    "synthetic_primary_ranking",
    "microphone_environment_profiles",
    "speakers",
    "utterances",
}
PROFILE_KEYS = {"profile_id", "metadata_sha256"}
SPEAKER_KEYS = {"speaker_id", "split", "cadence_assignment"}
UTTERANCE_KEYS = {
    "utterance_id",
    "speaker_id",
    "split",
    "panel",
    "canonical_audio_sha256",
    "annotation_sha256",
    "canonical_duration_ms",
    "microphone_environment_profile_id",
}


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def loads_object(text: str, label: str) -> dict[str, Any]:
    value = json.loads(text, object_pairs_hook=reject_duplicate_pairs)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def load(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} missing or symlinked: {path}")
    return loads_object(path.read_text(encoding="utf-8"), label)


def digest_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def freeze_digest(manifest: dict[str, Any]) -> str:
    projection = json.loads(json.dumps(manifest))
    projection["freeze_digest_sha256"] = None
    return digest_json(projection)


def primary_test_projection(manifest: dict[str, Any]) -> dict[str, Any]:
    test_speakers = [
        {
            "speaker_id": item["speaker_id"],
            "cadence_assignment": item["cadence_assignment"],
        }
        for item in manifest.get("speakers", [])
        if isinstance(item, dict) and item.get("split") == "test"
    ]
    test_utterances = [
        {
            key: item[key]
            for key in (
                "utterance_id",
                "speaker_id",
                "panel",
                "canonical_audio_sha256",
                "annotation_sha256",
                "canonical_duration_ms",
                "microphone_environment_profile_id",
            )
        }
        for item in manifest.get("utterances", [])
        if isinstance(item, dict) and item.get("split") == "test" and UTTERANCE_KEYS <= set(item)
    ]
    used_profiles = {
        item["microphone_environment_profile_id"]
        for item in test_utterances
    }
    profiles = [
        item
        for item in manifest.get("microphone_environment_profiles", [])
        if isinstance(item, dict) and item.get("profile_id") in used_profiles
    ]
    return {
        "schema_version": "000b2-primary-test-manifest-v1",
        "speaker_count": len(test_speakers),
        "utterance_count": len(test_utterances),
        "speakers": test_speakers,
        "microphone_environment_profiles": profiles,
        "utterances": test_utterances,
    }


def primary_test_digest(manifest: dict[str, Any]) -> str:
    return digest_json(primary_test_projection(manifest))


def verify_schema_contract() -> None:
    schema = load(SCHEMA, "corpus manifest schema")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise ValueError("corpus manifest schema root must be a closed object")
    required = schema.get("required")
    properties = schema.get("properties")
    if not isinstance(required, list) or set(required) != ROOT_KEYS:
        raise ValueError("corpus manifest schema required-field set drift")
    if not isinstance(properties, dict) or set(properties) != ROOT_KEYS:
        raise ValueError("corpus manifest schema property set drift")
    if properties.get("schema_version", {}).get("const") != "000b2-human-corpus-manifest-v1":
        raise ValueError("corpus manifest schema version drift")
    if set(properties.get("corpus_status", {}).get("enum", [])) != {"NOT_COLLECTED", "PARTIAL", "COMPLETE"}:
        raise ValueError("corpus status enum drift")
    if properties.get("direct_identifiers_present", {}).get("const") is not False:
        raise ValueError("direct-identifier boundary drift")
    if properties.get("synthetic_primary_ranking", {}).get("const") is not False:
        raise ValueError("synthetic-primary-ranking boundary drift")
    speakers = properties.get("speakers")
    utterances = properties.get("utterances")
    profiles = properties.get("microphone_environment_profiles")
    if not isinstance(speakers, dict) or speakers.get("maxItems") != EXPECTED_TOTAL_SPEAKERS:
        raise ValueError("speaker array bound drift")
    if not isinstance(utterances, dict) or utterances.get("maxItems") != EXPECTED_TOTAL_UTTERANCES:
        raise ValueError("utterance array bound drift")
    for label, container, keys in (
        ("profile", profiles, PROFILE_KEYS),
        ("speaker", speakers, SPEAKER_KEYS),
        ("utterance", utterances, UTTERANCE_KEYS),
    ):
        if not isinstance(container, dict):
            raise ValueError(f"{label} schema missing")
        items = container.get("items")
        if not isinstance(items, dict) or items.get("additionalProperties") is not False:
            raise ValueError(f"{label} item schema must be closed")
        if set(items.get("required", [])) != keys:
            raise ValueError(f"{label} required-field set drift")
        item_properties = items.get("properties")
        if not isinstance(item_properties, dict) or set(item_properties) != keys:
            raise ValueError(f"{label} property set drift")


def verify_manifest(manifest: dict[str, Any], *, require_frozen_structure: bool = False) -> list[str]:
    verify_schema_contract()
    errors: list[str] = []
    if set(manifest) != ROOT_KEYS:
        missing = sorted(ROOT_KEYS - set(manifest))
        extra = sorted(set(manifest) - ROOT_KEYS)
        if missing:
            errors.append(f"missing corpus fields: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected corpus fields: {', '.join(extra)}")
    if manifest.get("schema_version") != "000b2-human-corpus-manifest-v1":
        errors.append("corpus manifest schema version drift")
    status = manifest.get("corpus_status")
    if status not in {"NOT_COLLECTED", "PARTIAL", "COMPLETE"}:
        errors.append("corpus_status must be NOT_COLLECTED, PARTIAL, or COMPLETE")
    frozen = manifest.get("frozen")
    if not isinstance(frozen, bool):
        errors.append("frozen must be boolean")
    authority_status = manifest.get("authority_status")
    if authority_status not in {"NOT_AUTHORIZED", "AUTHORIZED"}:
        errors.append("authority_status must be NOT_AUTHORIZED or AUTHORIZED")
    consent_digest = manifest.get("consent_records_sha256")
    if consent_digest is not None and (not isinstance(consent_digest, str) or not SHA256.fullmatch(consent_digest)):
        errors.append("consent_records_sha256 must be null or lowercase SHA-256")
    if manifest.get("direct_identifiers_present") is not False:
        errors.append("corpus manifest must not contain direct participant identifiers")
    if manifest.get("synthetic_primary_ranking") is not False:
        errors.append("synthetic media cannot enter primary human ranking")

    profiles_value = manifest.get("microphone_environment_profiles")
    speakers_value = manifest.get("speakers")
    utterances_value = manifest.get("utterances")
    profiles = profiles_value if isinstance(profiles_value, list) else []
    speakers = speakers_value if isinstance(speakers_value, list) else []
    utterances = utterances_value if isinstance(utterances_value, list) else []
    if not isinstance(profiles_value, list):
        errors.append("microphone_environment_profiles must be an array")
    if not isinstance(speakers_value, list):
        errors.append("speakers must be an array")
    if not isinstance(utterances_value, list):
        errors.append("utterances must be an array")

    profile_ids: list[str] = []
    profile_digests: list[str] = []
    for index, profile in enumerate(profiles):
        label = f"microphone_environment_profiles[{index}]"
        if not isinstance(profile, dict) or set(profile) != PROFILE_KEYS:
            errors.append(f"{label} field set drift")
            continue
        profile_id = profile.get("profile_id")
        digest = profile.get("metadata_sha256")
        if not isinstance(profile_id, str) or not PROFILE_ID.fullmatch(profile_id):
            errors.append(f"{label}.profile_id malformed")
        else:
            profile_ids.append(profile_id)
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            errors.append(f"{label}.metadata_sha256 malformed")
        else:
            profile_digests.append(digest)
    if profile_ids != sorted(profile_ids):
        errors.append("microphone/environment profiles must be sorted by profile_id")
    if len(profile_ids) != len(set(profile_ids)):
        errors.append("duplicate microphone/environment profile_id")
    if len(profile_digests) != len(set(profile_digests)):
        errors.append("duplicate microphone/environment metadata digest")
    profile_set = set(profile_ids)

    speaker_ids: list[str] = []
    speaker_splits: dict[str, str] = {}
    split_counts: Counter[str] = Counter()
    test_cadences: Counter[str] = Counter()
    for index, speaker in enumerate(speakers):
        label = f"speakers[{index}]"
        if not isinstance(speaker, dict) or set(speaker) != SPEAKER_KEYS:
            errors.append(f"{label} field set drift")
            continue
        speaker_id = speaker.get("speaker_id")
        split = speaker.get("split")
        cadence = speaker.get("cadence_assignment")
        if not isinstance(speaker_id, str) or not SPEAKER_ID.fullmatch(speaker_id):
            errors.append(f"{label}.speaker_id malformed")
        else:
            speaker_ids.append(speaker_id)
            if split in EXPECTED_SPEAKERS:
                speaker_splits[speaker_id] = split
        if split not in EXPECTED_SPEAKERS:
            errors.append(f"{label}.split invalid")
        else:
            split_counts[split] += 1
        if split == "test":
            if cadence not in CADENCES:
                errors.append(f"{label}.cadence_assignment required for test speaker")
            else:
                test_cadences[cadence] += 1
        elif cadence is not None:
            errors.append(f"{label}.cadence_assignment must be null outside test split")
    if speaker_ids != sorted(speaker_ids):
        errors.append("speakers must be sorted by speaker_id")
    if len(speaker_ids) != len(set(speaker_ids)):
        errors.append("duplicate pseudonymous speaker_id")

    utterance_ids: list[str] = []
    audio_digests: list[str] = []
    annotation_digests: list[str] = []
    per_speaker: dict[str, Counter[str]] = defaultdict(Counter)
    test_profiles: set[str] = set()
    test_count = 0
    for index, utterance in enumerate(utterances):
        label = f"utterances[{index}]"
        if not isinstance(utterance, dict) or set(utterance) != UTTERANCE_KEYS:
            errors.append(f"{label} field set drift")
            continue
        utterance_id = utterance.get("utterance_id")
        speaker_id = utterance.get("speaker_id")
        split = utterance.get("split")
        panel = utterance.get("panel")
        audio = utterance.get("canonical_audio_sha256")
        annotation = utterance.get("annotation_sha256")
        duration = utterance.get("canonical_duration_ms")
        profile_id = utterance.get("microphone_environment_profile_id")
        if not isinstance(utterance_id, str) or not UTTERANCE_ID.fullmatch(utterance_id):
            errors.append(f"{label}.utterance_id malformed")
        else:
            utterance_ids.append(utterance_id)
        if not isinstance(speaker_id, str) or not SPEAKER_ID.fullmatch(speaker_id):
            errors.append(f"{label}.speaker_id malformed")
        elif speaker_id not in speaker_splits:
            errors.append(f"{label}.speaker_id not declared")
        elif split != speaker_splits[speaker_id]:
            errors.append(f"{label}.split does not match declared speaker split")
        if split not in EXPECTED_SPEAKERS:
            errors.append(f"{label}.split invalid")
        if panel not in EXPECTED_PER_SPEAKER:
            errors.append(f"{label}.panel invalid")
        elif isinstance(speaker_id, str):
            per_speaker[speaker_id][panel] += 1
        if not isinstance(audio, str) or not SHA256.fullmatch(audio):
            errors.append(f"{label}.canonical_audio_sha256 malformed")
        else:
            audio_digests.append(audio)
        if not isinstance(annotation, str) or not SHA256.fullmatch(annotation):
            errors.append(f"{label}.annotation_sha256 malformed")
        else:
            annotation_digests.append(annotation)
        if not isinstance(duration, int) or isinstance(duration, bool) or not 1 <= duration <= 12000:
            errors.append(f"{label}.canonical_duration_ms must be 1..12000")
        if not isinstance(profile_id, str) or not PROFILE_ID.fullmatch(profile_id):
            errors.append(f"{label}.microphone_environment_profile_id malformed")
        elif profile_id not in profile_set:
            errors.append(f"{label}.microphone_environment_profile_id not declared")
        if split == "test":
            test_count += 1
            if isinstance(profile_id, str):
                test_profiles.add(profile_id)
    if utterance_ids != sorted(utterance_ids):
        errors.append("utterances must be sorted by utterance_id")
    if len(utterance_ids) != len(set(utterance_ids)):
        errors.append("duplicate utterance_id")
    if len(audio_digests) != len(set(audio_digests)):
        errors.append("canonical audio digest reused across utterances")
    if len(annotation_digests) != len(set(annotation_digests)):
        errors.append("annotation digest reused across utterances")

    if status == "NOT_COLLECTED":
        if profiles or speakers or utterances:
            errors.append("NOT_COLLECTED corpus must contain no profiles, speakers, or utterances")
        if frozen is not False:
            errors.append("NOT_COLLECTED corpus cannot be frozen")
        if authority_status != "NOT_AUTHORIZED" or consent_digest is not None:
            errors.append("NOT_COLLECTED corpus cannot claim human authority or consent records")
        if manifest.get("freeze_digest_sha256") is not None or manifest.get("primary_test_manifest_sha256") is not None:
            errors.append("NOT_COLLECTED corpus cannot claim freeze or primary-test digests")
    elif status == "PARTIAL":
        if not speakers and not utterances and not profiles:
            errors.append("PARTIAL corpus requires some corpus metadata")
        if frozen is not False:
            errors.append("PARTIAL corpus cannot be frozen")
        if manifest.get("freeze_digest_sha256") is not None or manifest.get("primary_test_manifest_sha256") is not None:
            errors.append("PARTIAL corpus cannot claim freeze or primary-test digests")
    elif status == "COMPLETE":
        if len(speakers) != EXPECTED_TOTAL_SPEAKERS or split_counts != Counter(EXPECTED_SPEAKERS):
            errors.append(f"COMPLETE corpus must match frozen speaker split counts {EXPECTED_SPEAKERS}")
        if len(utterances) != EXPECTED_TOTAL_UTTERANCES:
            errors.append("COMPLETE corpus must contain exactly 720 utterances")
        for speaker_id in speaker_ids:
            if per_speaker[speaker_id] != Counter(EXPECTED_PER_SPEAKER):
                errors.append(f"speaker {speaker_id} must have 24 developer-entity and 12 collateral utterances")
        if test_count != EXPECTED_TEST_UTTERANCES:
            errors.append("COMPLETE corpus test split must contain exactly 432 utterances")
        if len(test_profiles) < 4:
            errors.append("COMPLETE corpus test split must use at least four microphone/environment profiles")
        if set(test_cadences) != CADENCES:
            errors.append("COMPLETE corpus test speakers must cover all frozen cadence classes")
        if frozen:
            if authority_status != "AUTHORIZED":
                errors.append("frozen corpus structure requires authority_status=AUTHORIZED")
            if not isinstance(consent_digest, str) or not SHA256.fullmatch(consent_digest):
                errors.append("frozen corpus structure requires consent_records_sha256")
            expected_test = primary_test_digest(manifest)
            if manifest.get("primary_test_manifest_sha256") != expected_test:
                errors.append("primary_test_manifest_sha256 does not match deterministic test projection")
            expected_freeze = freeze_digest(manifest)
            if manifest.get("freeze_digest_sha256") != expected_freeze:
                errors.append("freeze_digest_sha256 does not match deterministic corpus freeze projection")
        else:
            if manifest.get("freeze_digest_sha256") is not None or manifest.get("primary_test_manifest_sha256") is not None:
                errors.append("unfrozen COMPLETE corpus cannot claim frozen digests")

    if require_frozen_structure and not (status == "COMPLETE" and frozen is True):
        errors.append("complete frozen corpus structure is required")
    return errors


def synthetic_complete_manifest(*, frozen: bool) -> dict[str, Any]:
    profiles = [
        {
            "profile_id": f"env-{index:08x}",
            "metadata_sha256": hashlib.sha256(f"synthetic-profile-{index}".encode()).hexdigest(),
        }
        for index in range(4)
    ]
    speakers: list[dict[str, Any]] = []
    split_plan = ["development"] * 4 + ["qualification"] * 4 + ["test"] * 12
    cadence_plan = ["SLOW", "CONVERSATIONAL", "FAST_INTELLIGIBLE"] * 4
    test_index = 0
    for index, split in enumerate(split_plan):
        cadence = None
        if split == "test":
            cadence = cadence_plan[test_index]
            test_index += 1
        speakers.append(
            {
                "speaker_id": f"spk-{index:08x}",
                "split": split,
                "cadence_assignment": cadence,
            }
        )
    utterances: list[dict[str, Any]] = []
    utterance_index = 0
    for speaker_index, speaker in enumerate(speakers):
        for panel, count in EXPECTED_PER_SPEAKER.items():
            for local_index in range(count):
                utterances.append(
                    {
                        "utterance_id": f"utt-{utterance_index:012x}",
                        "speaker_id": speaker["speaker_id"],
                        "split": speaker["split"],
                        "panel": panel,
                        "canonical_audio_sha256": hashlib.sha256(f"synthetic-audio-{utterance_index}".encode()).hexdigest(),
                        "annotation_sha256": hashlib.sha256(f"synthetic-annotation-{utterance_index}".encode()).hexdigest(),
                        "canonical_duration_ms": 1000 + (local_index % 100),
                        "microphone_environment_profile_id": profiles[(speaker_index + local_index) % len(profiles)]["profile_id"],
                    }
                )
                utterance_index += 1
    manifest: dict[str, Any] = {
        "schema_version": "000b2-human-corpus-manifest-v1",
        "corpus_status": "COMPLETE",
        "frozen": frozen,
        "freeze_digest_sha256": None,
        "primary_test_manifest_sha256": None,
        "authority_status": "AUTHORIZED" if frozen else "NOT_AUTHORIZED",
        "consent_records_sha256": hashlib.sha256(b"synthetic-consent-bundle").hexdigest() if frozen else None,
        "direct_identifiers_present": False,
        "synthetic_primary_ranking": False,
        "microphone_environment_profiles": profiles,
        "speakers": speakers,
        "utterances": utterances,
    }
    if frozen:
        manifest["primary_test_manifest_sha256"] = primary_test_digest(manifest)
        manifest["freeze_digest_sha256"] = freeze_digest(manifest)
    return manifest


def self_test() -> None:
    verify_schema_contract()
    try:
        loads_object('{"x":1,"x":2}', "duplicate-key fixture")
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate JSON members were accepted")

    complete = synthetic_complete_manifest(frozen=False)
    if verify_manifest(complete):
        raise AssertionError("synthetic complete unfrozen corpus should validate structurally")
    frozen = synthetic_complete_manifest(frozen=True)
    if verify_manifest(frozen, require_frozen_structure=True):
        raise AssertionError("synthetic frozen corpus should validate structurally")

    duplicate = json.loads(json.dumps(complete))
    duplicate["speakers"][1]["speaker_id"] = duplicate["speakers"][0]["speaker_id"]
    if not verify_manifest(duplicate):
        raise AssertionError("duplicate speaker id must fail")
    split_leak = json.loads(json.dumps(complete))
    split_leak["utterances"][0]["split"] = "test"
    if not verify_manifest(split_leak):
        raise AssertionError("speaker/utterance split mismatch must fail")
    synthetic_rank = json.loads(json.dumps(complete))
    synthetic_rank["synthetic_primary_ranking"] = True
    if not verify_manifest(synthetic_rank):
        raise AssertionError("synthetic primary ranking must fail")
    bad_test_digest = json.loads(json.dumps(frozen))
    bad_test_digest["primary_test_manifest_sha256"] = "0" * 64
    bad_test_digest["freeze_digest_sha256"] = freeze_digest(bad_test_digest)
    if not verify_manifest(bad_test_digest, require_frozen_structure=True):
        raise AssertionError("bad primary-test digest must fail")

    print("SYNTHETIC_CORPUS_MANIFEST_FORMAT_SELF_TEST=PASS")
    print("HUMAN_CORPUS_AUTHORITY_ATTESTATION=NOT_PROVIDED_BY_THIS_FORMAT")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    print("PRIMARY_TEST_DECODING_AUTHORIZED=NO")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("--require-frozen-structure", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        if args.manifest is None:
            raise ValueError("corpus manifest path is required unless --self-test is used")
        manifest = load(args.manifest, "corpus manifest")
        errors = verify_manifest(manifest, require_frozen_structure=args.require_frozen_structure)
    except (AssertionError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"CORPUS_MANIFEST=FAIL: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"CORPUS_MANIFEST=FAIL: {error}", file=sys.stderr)
        return 1
    status = manifest["corpus_status"]
    print(f"CORPUS_MANIFEST={status}")
    print(f"FROZEN={'YES' if manifest['frozen'] else 'NO'}")
    print(f"SPEAKERS={len(manifest['speakers'])}")
    print(f"UTTERANCES={len(manifest['utterances'])}")
    if manifest["frozen"]:
        print(f"PRIMARY_TEST_MANIFEST_SHA256={primary_test_digest(manifest)}")
        print(f"CORPUS_FREEZE_DIGEST_SHA256={freeze_digest(manifest)}")
    print("HUMAN_CORPUS_AUTHORITY_ATTESTATION=NOT_PROVIDED_BY_THIS_FORMAT")
    print("PRIMARY_MEDIA_ACCEPTANCE=NO")
    print("PRIMARY_TEST_DECODING_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
