# 000B2 Pseudonymous Active Consent Evidence Format

This format defines the deterministic **private active-consent bundle** used to bind real external participant authority to B2 without publishing identity-bearing consent evidence. It does not collect consent and does not authorize recording.

The individual consent records do **not** need to be committed to GitHub. The minimum repository-visible commitment for an authorized authority package is the aggregate `participant_count` plus the deterministic `consent_records_sha256` of the complete private bundle. The private bundle remains available outside the repository for separately governed challenge and review.

## Privacy boundary

Identity-bearing consent documents remain outside the repository. Individual pseudonymous consent records also remain private by default and MUST NOT be committed merely to satisfy B2 authority binding.

The private bundle contains only:

- a pseudonymous participant id matching `spk-<8 lowercase hex>`;
- the preregistered speaker split;
- SHA-256 of the external consent artifact;
- SHA-256 of the exact authority-policy projection acknowledged by that artifact;
- an explicit UTC consent-record timestamp;
- `record_status=ACTIVE`.

Names, email addresses, phone numbers, signatures, addresses, demographic attributes, or other direct participant identifiers are not permitted in the bundle.

A future separately authorized publication may expose schema-permitted pseudonymous metadata when there is a concrete reproducibility need, but publication of individual records is not an entry requirement and is not implied by `authority_status=AUTHORIZED`.

## Active-only semantics

The bundle represents currently active consent evidence only. A withdrawn participant is removed from the active bundle and the bundle digest changes. Withdrawal history and identity-bearing withdrawal evidence remain outside the repository.

`COMPLETE` requires exactly the frozen 20-speaker design:

- development: 4;
- qualification: 4;
- test: 12.

Records are sorted by pseudonymous participant id. Participant ids and consent-artifact digests are unique.

## Policy fingerprint

`authority_policy_sha256` is SHA-256 of deterministic UTF-8 JSON with sorted keys and compact separators over exactly these authority-package fields:

- `participant_consent_scope`;
- `recording_purpose`;
- `repository_storage_policy`;
- `retention_rule`;
- `deletion_withdrawal_procedure`;
- `public_redistribution_decision`;
- `derivative_benchmark_artifact_permission`;
- `privacy_constraints`;
- `prohibited_content_policy`.

The authority status, participant count, consent-record bundle digest, and pre-recording-effectiveness claim are deliberately excluded from the policy fingerprint to avoid a circular digest dependency.

## Bundle digest

`CONSENT_RECORDS_SHA256` is SHA-256 of deterministic UTF-8 JSON for the complete private bundle using sorted keys and compact separators. The canonical authority package binds `consent_records_sha256` to this value while the underlying individual records remain outside GitHub.

The digest is a commitment, not consent proof. It prevents the benchmark from silently switching to a different consent bundle after results are observed and gives an external reviewer a stable identity for the exact private bundle used by the attempt.

A structural binding still does not prove that the external artifact is genuine, that the person understood or signed it, or that consent preceded recording. Those are separate externally reviewable authority/chronology facts.

## Fail-closed states

The canonical template is `NOT_COLLECTED` with zero participants and no policy digest.

- `NOT_COLLECTED`: zero active records; no policy digest.
- `PARTIAL`: 1–19 active records; exact policy fingerprint required.
- `COMPLETE`: exactly 20 active records with frozen split counts; exact policy fingerprint required.

`--require-complete` rejects `NOT_COLLECTED` and `PARTIAL`.

`--require-authority-binding` additionally requires a structurally `AUTHORIZED` authority package whose `participant_count` and `consent_records_sha256` match the complete private bundle and whose pre-recording-effectiveness field is true. Even then the verifier emits:

```text
PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_FORMAT
PRIMARY_MEDIA_ACCEPTANCE=NO
```

Therefore repository-owner approval, a complete private metadata bundle, or matching digests cannot independently authorize human recording, accept primary media, or authorize B2 primary decoding.

## Withdrawal rule

Withdrawal or correction before attempt freeze invalidates the previous active bundle. Rebuild the active bundle without the withdrawn record, recompute the bundle digest, and keep B2 blocked until the required active speaker design is again satisfied under separately reviewable real authority evidence.
