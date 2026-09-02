# 000B2 External Human-Authority Runbook

**Status:** readiness-only operating procedure  
**Scope:** external participant/media authority preparation for `000B2-unbiased-stt-bakeoff`

This runbook makes the existing fail-closed authority and consent contracts operational. It does **not** collect consent, approve a participant, authorize recording, accept media, freeze a corpus, or authorize B2 primary decoding.

Repository-owner approval, a structurally valid JSON file, a digest, a passing workflow, or this document cannot substitute for real participant consent and separately reviewable chronology/media authority.

```text
PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_RUNBOOK
B2_PRIMARY_RECORDING_AUTHORIZED_BY_THIS_RUNBOOK=NO
PRIMARY_MEDIA_ACCEPTANCE=NO
PRIMARY_TEST_DECODING_AUTHORIZED=NO
```

## 1. Keep identity-bearing evidence outside the repository

Identity-bearing consent artifacts, participant contact information, signatures, identity-to-pseudonym mappings, withdrawal evidence, and raw authority-review notes MUST remain outside the public repository.

Participant ids MUST be independently generated pseudonyms matching `spk-<8 lowercase hex>` and MUST NOT be derived from a name, email address, phone number, account identifier, or another direct identifier.

The repository must never be used as the source of truth for the participant's real identity.

## 2. Freeze the policy that participants will actually review

Before requesting consent, prepare a private working copy of the authority package outside the repository. Populate the exact policy fields that form the canonical policy projection:

- `participant_consent_scope`;
- `recording_purpose`;
- `repository_storage_policy`;
- `retention_rule`;
- `deletion_withdrawal_procedure`;
- `public_redistribution_decision`;
- `derivative_benchmark_artifact_permission`;
- `privacy_constraints`;
- `prohibited_content_policy`.

During policy preparation keep:

- `authority_status=NOT_AUTHORIZED`;
- `consent_records_sha256=null`;
- `participant_count=0`;
- `package_contains_direct_identifiers=false`;
- `authority_effective_before_recording=false`.

Do not change the policy projection after a participant has consented to it. A material policy change invalidates consent records tied to the prior policy fingerprint and requires renewed external consent before recording.

Compute the deterministic policy fingerprint from the private policy file:

```bash
python research/000b2-entry/authority/print_authority_policy_sha256.py \
  --authority-package /secure/private/authority-policy.json
```

The helper only computes the existing canonical projection. Its output is not consent or authority.

## 3. Obtain real consent against that exact policy

For each participant, the identity-bearing consent artifact must be created and retained outside the repository under the approved storage and retention policy. The artifact must make the participant's actual choices understandable, including the recording purpose, retention rule, withdrawal procedure, redistribution decision, derivative-artifact permission, privacy constraints, and prohibited-content policy.

Before any recording for that participant:

1. the participant must review the exact frozen policy represented by `authority_policy_sha256`;
2. real consent must be obtained through the externally governed process;
3. the external artifact must receive a SHA-256 digest;
4. the externally recorded consent time must be preserved as explicit RFC 3339 UTC;
5. the pseudonymous participant id and preregistered split assignment must be linked to that external artifact in the private identity mapping, not in GitHub.

No audio may be collected merely because a pseudonymous consent record can be made structurally valid.

## 4. Build the private active consent bundle

Start from a private working copy of `consent-records.template.json` and add only active pseudonymous records. The individual records remain outside GitHub by default. Each record must contain:

- `participant_id`;
- preregistered `split`;
- `consent_artifact_sha256`;
- the exact `authority_policy_sha256`;
- `consent_obtained_at_utc`;
- `record_status=ACTIVE`.

The bundle remains `PARTIAL` until all 20 active participants exist. Validate the private working bundle against the same private policy file:

```bash
python research/000b2-entry/authority/verify_consent_records.py \
  /secure/private/consent-records.json \
  --authority-package /secure/private/authority-policy.json
```

`COMPLETE` requires exactly 20 active records with frozen split counts:

- development: 4;
- qualification: 4;
- test: 12.

When all required active records exist, run:

```bash
python research/000b2-entry/authority/verify_consent_records.py \
  /secure/private/consent-records.json \
  --authority-package /secure/private/authority-policy.json \
  --require-complete
```

Record the emitted `CONSENT_RECORDS_SHA256`. This aggregate digest plus `participant_count=20` is the minimum repository-visible commitment needed by the authority package. Publishing the 20 individual pseudonymous records is not required for B2 entry and must not be done merely to satisfy the authority gate.

A successful structural check still emits no participant-consent attestation and no primary-media acceptance.

## 5. Bind the complete bundle into the authority package only after real review

Only after the real external consent artifacts have been reviewed for genuineness and chronology may the candidate authority package be prepared with:

- `authority_status=AUTHORIZED`;
- `consent_records_sha256=<exact complete private bundle digest>`;
- `participant_count=20`;
- `authority_effective_before_recording=true`.

Setting these fields is an evidence-bearing claim. Do not set them from repository-owner approval alone. Do not set `authority_effective_before_recording=true` unless the separately reviewable external evidence establishes that the required authority was effective before recording.

Structural validation is then:

```bash
python research/000b2-entry/authority/verify_authority.py \
  /secure/private/authority-package.json \
  --require-authorized

python research/000b2-entry/authority/verify_consent_records.py \
  /secure/private/consent-records.json \
  --authority-package /secure/private/authority-package.json \
  --require-authority-binding
```

These commands validate structure and digest binding only. They do not independently verify signatures, identities, understanding, consent chronology, media provenance, or primary-media acceptance.

## 6. Recording entry gate

Recording may begin only after all of the following are true outside the repository:

- the participant's real consent artifact exists and is genuine;
- it binds the exact frozen policy projection;
- consent was effective before that participant's recording;
- the participant remains active and has not withdrawn;
- the collection procedure obeys the approved storage, retention, privacy, prohibited-content, redistribution, and derivative-artifact terms;
- the external reviewer can challenge the identity, artifact, and chronology evidence without relying on repository metadata as proof.

Until those facts are real, preserve `authority-package.json` on canonical `main` as `NOT_AUTHORIZED` and preserve B2 as `BLOCKED_EXTERNAL`.

## 7. Withdrawal and correction

Before final attempt freeze, withdrawal or a material consent correction invalidates the prior active consent bundle for that participant.

Required response:

1. stop new recording/use for the affected participant under the invalidated authority;
2. preserve identity-bearing withdrawal/correction evidence outside the repository;
3. remove the participant from the active pseudonymous bundle;
4. recompute `CONSENT_RECORDS_SHA256`;
5. invalidate any authority-package binding to the old digest;
6. remove or replace affected corpus records as required by the approved withdrawal procedure;
7. recompute corpus/test/freeze digests when affected;
8. keep B2 blocked until the frozen 4/4/12 active design and all downstream bindings are valid again.

Do not rewrite historical evidence to make a withdrawn participant appear never to have existed.

## 8. Corpus collection and freeze remain separate gates

A structurally authorized consent package does not itself accept audio. After real recording authority exists, the human corpus must still satisfy `research/000b2-entry/corpus/` and the frozen 20-speaker / 720-utterance design.

Primary decoding remains prohibited until:

- the real authorized corpus exists;
- consent records and speaker-disjoint split manifests are bound;
- the primary test manifest is frozen;
- attempt-bound FFmpeg `9.0.1` preprocessing identity/execution evidence is captured under separately reviewable chronology;
- attempt-bound execution-environment and hardware evidence is captured under separately reviewable chronology/control evidence;
- the final B2 attempt manifest is `frozen=true` with a matching freeze digest;
- readiness is rechecked from live canonical `main`.

## 9. Repository publication boundary

The default publication surface is privacy-minimal. The repository needs only the non-identifying authority package commitment required by the canonical contract, including the aggregate participant count and complete private-bundle digest.

Before any authority or corpus metadata is proposed to GitHub:

- remove all direct identifiers and private identity mappings;
- do not publish the individual consent records merely to satisfy B2 entry;
- verify external consent artifacts themselves are not added;
- verify no raw human audio is added unless a separately established policy explicitly permits repository publication and canonical governance authorizes that publication surface;
- preserve the external evidence needed to challenge consent genuineness and chronology without publishing participant identities.

A future separately authorized PR may carry additional schema-permitted pseudonymous metadata only when a concrete reproducibility need justifies the additional disclosure. CI success must never be described as participant consent, media acceptance, chronology attestation, or B2 decoding authority.
