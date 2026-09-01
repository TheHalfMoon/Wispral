# 000B2 Pseudonymous Active Consent Evidence Format

This format satisfies the repository-side **record format** requirement for future human developer-speech consent evidence. It does not collect consent and does not authorize recording.

## Privacy boundary

Identity-bearing consent documents remain outside the repository. Repository-visible records contain only:

- a pseudonymous participant id matching `spk-<8 lowercase hex>`;
- the preregistered speaker split;
- SHA-256 of the external consent artifact;
- SHA-256 of the exact authority-policy projection acknowledged by that artifact;
- an explicit UTC consent-record timestamp;
- `record_status=ACTIVE`.

Names, email addresses, phone numbers, signatures, addresses, demographic attributes, or other direct participant identifiers are not permitted in the bundle.

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

`CONSENT_RECORDS_SHA256` is SHA-256 of deterministic UTF-8 JSON for the complete bundle using sorted keys and compact separators. A future authority package may bind `consent_records_sha256` to this value.

A structural binding still does not prove that the external artifact is genuine, that the person understood or signed it, or that consent preceded recording. Those are separate externally reviewable authority/chronology facts.

## Fail-closed states

The canonical template is `NOT_COLLECTED` with zero participants and no policy digest.

- `NOT_COLLECTED`: zero active records; no policy digest.
- `PARTIAL`: 1–19 active records; exact policy fingerprint required.
- `COMPLETE`: exactly 20 active records with frozen split counts; exact policy fingerprint required.

`--require-complete` rejects `NOT_COLLECTED` and `PARTIAL`.

`--require-authority-binding` additionally requires a structurally `AUTHORIZED` authority package whose `participant_count` and `consent_records_sha256` match the complete bundle and whose pre-recording-effectiveness field is true. Even then the verifier emits:

```text
PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_FORMAT
PRIMARY_MEDIA_ACCEPTANCE=NO
```

Therefore repository-owner approval, a complete metadata bundle, or matching digests cannot independently authorize human recording or B2 primary decoding.

## Withdrawal rule

Withdrawal or correction before attempt freeze invalidates the previous active bundle. Rebuild the active bundle without the withdrawn record, recompute the bundle digest, and keep B2 blocked until the required active speaker design is again satisfied under separately reviewable real authority evidence.
