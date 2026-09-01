# 000B2 Human Corpus Manifest Format

This directory defines the repository-side manifest format for the frozen 000B1 human corpus design. It does not collect recordings, attest consent, or authorize primary decoding.

## Frozen design represented

A structurally complete corpus contains exactly:

- 20 pseudonymous speakers;
- development: 4 speakers;
- qualification: 4 speakers;
- test: 12 speakers;
- 24 `DEVELOPER_ENTITY` utterances per speaker;
- 12 `GENERAL_COLLATERAL` utterances per speaker;
- 720 human utterance records total;
- 432 held-out test utterance records total;
- at least four microphone/environment profiles used by the test split;
- all three frozen test cadence classes represented across test speakers;
- canonical duration at most 12,000 ms per utterance.

Speaker ids are pseudonymous `spk-<8 lowercase hex>` values. The manifest contains no name, email, phone number, signature, address, demographic attribute, raw audio, or reference transcript.

## Per-utterance identity

Each utterance record binds:

- pseudonymous speaker and split;
- panel identity;
- canonical preprocessed audio SHA-256;
- annotation artifact SHA-256;
- canonical duration;
- microphone/environment profile id.

Microphone/environment profile details are represented only by a pseudonymous profile id and metadata SHA-256.

## Primary test manifest digest

The verifier derives a deterministic test projection containing only:

- test speaker ids and cadence assignments;
- test-used microphone/environment profile metadata digests;
- test utterance identities, audio/annotation digests, durations, and profile ids.

`primary_test_manifest_sha256` is SHA-256 of compact sorted-key UTF-8 JSON for that projection.

## Corpus freeze digest

`freeze_digest_sha256` is SHA-256 of compact sorted-key UTF-8 JSON for the full corpus manifest after replacing `freeze_digest_sha256` itself with `null`. This avoids self-hash circularity while binding the primary-test digest and all other manifest fields.

## Fail-closed states

The canonical template is:

- `corpus_status=NOT_COLLECTED`;
- `frozen=false`;
- `authority_status=NOT_AUTHORIZED`;
- `consent_records_sha256=null`;
- zero profiles, speakers, and utterances;
- no freeze or primary-test digest.

`PARTIAL` and `COMPLETE` are structural descriptions only. They do not establish that collection was authorized or that any external consent evidence is genuine.

A structurally frozen manifest additionally requires `COMPLETE`, structural `authority_status=AUTHORIZED`, a consent-record digest, the deterministic primary-test digest, and the deterministic freeze digest. Even that state is not sufficient to authorize benchmark execution because this format cannot attest consent genuineness, consent chronology, recording provenance, or execution chronology.

Every successful verifier invocation preserves:

```text
HUMAN_CORPUS_AUTHORITY_ATTESTATION=NOT_PROVIDED_BY_THIS_FORMAT
PRIMARY_MEDIA_ACCEPTANCE=NO
PRIMARY_TEST_DECODING_AUTHORIZED=NO
```

## Synthetic self-tests

The verifier constructs a deterministic synthetic 20-speaker / 720-record fixture only to exercise structural invariants and digest algorithms. Those synthetic records are not human audio, are not benchmark inputs, and are never eligible for primary ranking.

## Withdrawal and correction

A real participant withdrawal before attempt freeze requires the active consent evidence to change and therefore invalidates any previously bound corpus/attempt authority. If the corresponding speaker/audio is removed or replaced, the corpus and primary-test digests must also change. This format does not itself perform or attest that external process.
