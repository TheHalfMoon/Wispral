# 000B2 Recording Entry Checklist Template

**Template status:** `UNCOMPLETED_TEMPLATE`  
**Benchmark:** `000B2-unbiased-stt-bakeoff`  
**Required participant-policy SHA-256:** `454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811`

This checklist is a fail-closed operator aid for the external human-authority process. A blank or completed copy does not independently prove participant consent, legal/ethics approval, chronology, media provenance, corpus acceptance, or B2 readiness.

Use one externally retained checklist per participant before that participant's first recording session. Do not commit completed checklists containing identity-bearing or private authority evidence to GitHub.

## A. Immutable policy binding

- [ ] The participant-facing material presented to the participant is the exact frozen file `research/000b2-entry/authority/participant-information-consent.template.md` with SHA-256 `dd4143145674473ea56122a7e7e23cfc95c08cb99840b451b190bc92fb3d93b6`.
- [ ] The external consent artifact binds exactly:
  - `authority_policy_sha256 = 454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811`
- [ ] No policy field has materially changed since the participant reviewed it.
- [ ] Public raw-audio redistribution remains prohibited.
- [ ] Model training, speaker identification, voice biometrics, advertising, profiling, unrelated secondary research, and reuse outside the consented scope remain unauthorized without new explicit consent.

If any item above is false or unknown: **STOP — DO NOT RECORD**.

## B. Real participant consent evidence

Complete these checks against the private, identity-bearing evidence outside GitHub:

- [ ] A real participant exists and the operator has verified the externally governed identity/eligibility process required for this study.
- [ ] The participant had a meaningful opportunity to read, hear, or otherwise access the consent information and ask questions.
- [ ] The participant voluntarily gave the required consent/affirmation through the externally governed process.
- [ ] The external consent artifact exists and is retained in the approved off-repository location.
- [ ] The external artifact has a SHA-256 digest.
- [ ] The consent time is recorded as explicit RFC 3339 UTC.
- [ ] The consent time is earlier than the first authorized recording time for this participant.
- [ ] The participant has not withdrawn or invalidated the consent before recording.
- [ ] Any jurisdictional, institutional, age, accessibility, language, or ethics requirements that apply to the real collection have been satisfied outside the repository.

If any item above is false, unknown, or not independently reviewable: **STOP — DO NOT RECORD**.

## C. Pseudonymous repository binding

- [ ] A random participant id matching `spk-<8 lowercase hex>` has been generated independently of the participant's name, email, phone number, account id, or other direct identifier.
- [ ] The private identity-to-pseudonym mapping remains outside the public repository.
- [ ] The participant has exactly one preregistered split assignment: `development`, `qualification`, or `test`.
- [ ] The repository-visible consent record, when later prepared, will contain only schema-permitted pseudonymous metadata.
- [ ] The repository-visible record will bind the exact external consent-artifact SHA-256 and the exact frozen participant-policy SHA-256.
- [ ] No signature, name, email address, phone number, contact information, raw withdrawal evidence, or other direct identifier will be committed.

If any item above is false or unknown: **STOP — DO NOT RECORD**.

## D. Storage and privacy readiness

- [ ] The raw-audio destination is outside the public repository.
- [ ] Access to raw audio and identity-bearing authority evidence is limited to the externally approved process.
- [ ] The operator knows the retention deadline and deletion procedure.
- [ ] Raw audio and identity-bearing consent/authority records will be retained only for the minimum period necessary for 000B2 review and no later than 90 days after canonical 000B2 closeout, subject to earlier effective pre-freeze withdrawal.
- [ ] The participant has been reminded not to disclose credentials, secrets, sensitive personal data, PHI, proprietary/confidential material, or unauthorized source code.
- [ ] The operator has a procedure to stop intake and exclude an item if prohibited content is spoken accidentally.
- [ ] Network routing, telemetry, cloud upload, or third-party processing that would exceed the frozen policy is disabled or separately authorized by new explicit participant consent and canonical governance.

If any item above is false or unknown: **STOP — DO NOT RECORD**.

## E. Session entry record

Record these values in the **private external evidence system**, not in this public template:

- pseudonymous participant id: ______________________________
- preregistered split: _____________________________________
- external consent artifact SHA-256: ________________________
- consent obtained at UTC: __________________________________
- planned first recording start at UTC: ______________________
- operator/reviewer reference: _______________________________
- approved private storage reference: ________________________
- applicable external approval/reference, if required: _______

Do not place a real person's name, signature, contact details, identity mapping, or raw approval document in the public repository.

## F. Final fail-closed decision

All Sections A–E must be complete and independently reviewable before recording.

- [ ] `CONSENT_REAL_AND_REVIEWED=YES`
- [ ] `POLICY_DIGEST_MATCH=YES`
- [ ] `CONSENT_PRECEDES_RECORDING=YES`
- [ ] `PARTICIPANT_ACTIVE_NOT_WITHDRAWN=YES`
- [ ] `PRIVATE_STORAGE_READY=YES`
- [ ] `PROHIBITED_CONTENT_CONTROLS_READY=YES`
- [ ] `EXTERNAL_REQUIREMENTS_SATISFIED=YES`

If every item is checked, this checklist may support the **external** decision that recording for this participant can begin. It still does not make repository metadata self-authenticating and does not authorize B2 primary decoding.

After recording authority becomes real for the full frozen panel, separate corpus, split, preprocessing, environment, final-attempt-freeze, and canonical-readiness gates still apply.

```text
PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_CHECKLIST
PRIMARY_MEDIA_ACCEPTANCE=NO
PRIMARY_TEST_DECODING_AUTHORIZED=NO
B2_READY=NO
```
