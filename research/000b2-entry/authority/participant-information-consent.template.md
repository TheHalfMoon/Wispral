# 000B2 Participant Information and Consent Template

**Template status:** `UNCOMPLETED_TEMPLATE`  
**Benchmark:** `000B2-unbiased-stt-bakeoff`  
**Frozen participant-policy SHA-256:** `454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811`

> This repository document is a participant-facing template only. It is not a completed consent record, does not prove informed consent, does not authorize recording, and must not be treated as legal, ethics-board, institutional, or jurisdiction-specific approval. Before real use, the externally governed study owner must determine whether additional legal, ethics, institutional, age, accessibility, or local-language requirements apply.

## 1. Why you are being invited

Wispral is evaluating local speech-to-text systems for developer speech. The 000B2 benchmark is designed to compare preregistered local speech-to-text candidates before Wispral selects any production speech dependency.

If you participate, you will be asked to record preregistered developer-speech utterances. The benchmark may include file paths, symbols, package names, command-line flags, Git references, test names, database identifiers, corrections, abandoned phrases, and ordinary non-entity language.

Participation is voluntary. Repository-owner approval is not your consent.

## 2. What participation covers

If you consent under this exact frozen policy, your participation covers only one Wispral 000B2 developer-speech benchmark participation:

- recording the preregistered benchmark utterances assigned to you;
- local preprocessing of those recordings under the frozen benchmark method;
- local C0 speech-to-text decoding with repository/test-specific decoder context disabled;
- deterministic benchmark scoring;
- creation of pseudonymous, non-identifying transcript, timing, and error artifacts permitted by the benchmark;
- aggregate benchmark reporting.

This consent does **not** authorize:

- model training or fine-tuning;
- speaker identification or voice biometrics;
- advertising or profiling;
- unrelated secondary research;
- public release of raw audio;
- reuse outside the scope above without new explicit consent.

## 3. Recording purpose

The recordings are collected only to evaluate preregistered local speech-to-text candidates for Wispral 000B2 under the frozen benchmark design, measure recognition quality and bounded operational behavior, and support an evidence-based decision before any product dependency is selected.

The benchmark is research evidence for an open-source software project. It is not a clinical, employment, biometric-identification, or surveillance study.

## 4. What must not be spoken

Use only the preregistered benchmark prompts. Do not intentionally say or add:

- passwords, API keys, authentication tokens, private keys, recovery codes, or other secrets;
- protected health information, medical records, financial account data, government identifiers, home addresses, or other sensitive personal data;
- proprietary source code, confidential employer/client information, unreleased product information, or material you are not authorized to disclose;
- personal disclosures not required by the benchmark.

If prohibited content is spoken accidentally, recording intake for that item must stop and the affected media must be excluded from the active corpus under the external handling procedure.

## 5. Privacy and pseudonyms

The public repository must not contain your name, email address, phone number, signature, contact details, identity-to-pseudonym mapping, identity-bearing consent artifact, withdrawal evidence, or raw human audio.

A randomly generated pseudonymous participant id of the form `spk-<8 lowercase hex>` is used in repository-visible metadata. It must not be derived from your identity.

GitHub may contain only schema-permitted pseudonymous metadata, cryptographic digests, consented non-identifying derived text/metrics, and aggregate reports.

Your identity-bearing consent material, identity mapping, contact information, withdrawal evidence, and raw audio remain outside the public repository under the externally governed storage process.

## 6. Public redistribution and derived artifacts

**Raw human audio will not be publicly redistributed under this policy.**

Within the scope you approve here, non-identifying derived benchmark artifacts may be retained and published, including pseudonymous transcripts, timing/error metadata, cryptographic digests, benchmark scores, and aggregate reports.

If a later project wants to use your recordings or derived material outside this scope, or for model training, speaker identification, voice biometrics, advertising, profiling, or unrelated secondary research, new explicit consent is required.

## 7. Retention

Raw human audio and identity-bearing consent/authority records must be retained only for the minimum period needed to complete and independently review 000B2, and no later than 90 days after canonical 000B2 closeout.

They may be deleted earlier when an effective withdrawal before final attempt freeze requires it.

Pseudonymous benchmark evidence may remain after closeout only within the derivative-artifact scope you approve here.

## 8. Withdrawal before final attempt freeze

Before the final 000B2 attempt is frozen, you may withdraw through the external consent channel provided to you by the study owner.

For an effective pre-freeze withdrawal, the project must:

1. stop new collection and use for your participant record;
2. remove you from the active consent bundle and active corpus;
3. delete your raw audio from active benchmark storage;
4. remove attributable derivatives from the active benchmark corpus;
5. recompute affected digests and manifests;
6. keep B2 blocked until the frozen design is restored;
7. retain only the minimum off-repository evidence necessary to prove that the withdrawal request was honored.

The external consent process must tell you how to submit a withdrawal request and must explain any limits that apply after a final benchmark attempt has been frozen or results have already been irreversibly published. This repository template does not invent those jurisdiction- or institution-specific rights.

## 9. What the repository can and cannot prove

A repository-visible pseudonymous consent record may later contain:

- your pseudonymous participant id;
- your preregistered split;
- SHA-256 of the external consent artifact;
- this exact participant-policy SHA-256;
- the UTC time recorded for consent;
- `record_status=ACTIVE`.

That metadata is a reproducibility binding. It does not by itself prove your identity, understanding, signature, voluntariness, or that consent preceded recording. Those facts must remain supported by separately reviewable external evidence.

## 10. Questions and external contact

Before you consent, the externally governed process must provide a real contact channel for questions, withdrawal requests, privacy requests, or complaints.

Do not put participant contact details or identity-bearing correspondence into the public repository.

**External study contact:** ______________________________________________

**External withdrawal/privacy channel:** __________________________________

**Any required institutional/ethics contact:** ______________________________

If a required contact or approval is missing, do not record.

## 11. Participant acknowledgements

The completed external consent artifact must make each choice explicit. The participant should be able to affirm all of the following before recording:

- [ ] I have read or had explained to me the exact frozen 000B2 participant policy identified above.
- [ ] I understand why developer-speech recordings are being collected and what I will be asked to do.
- [ ] I understand that raw audio will not be publicly redistributed under this policy.
- [ ] I understand that non-identifying derived benchmark artifacts may be retained or published within the approved benchmark scope.
- [ ] I understand that model training, speaker identification, voice biometrics, advertising, profiling, unrelated secondary research, and reuse outside this scope are not authorized without new explicit consent.
- [ ] I understand the retention rule and the pre-freeze withdrawal procedure described above.
- [ ] I know how to ask questions and how to submit a withdrawal or privacy request through the external channel.
- [ ] I understand that I should speak only preregistered prompts and must not disclose secrets, sensitive personal data, or confidential/proprietary material.
- [ ] I voluntarily agree to participate in the 000B2 developer-speech benchmark under this exact scope.

## 12. Completion boundary

The actual identity-bearing consent artifact, signature/affirmation mechanism, date/time evidence, and any legally or institutionally required language must be completed and stored **outside the public repository**.

A completed artifact must be cryptographically bound to:

`authority_policy_sha256 = 454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811`

No recording may begin merely because this template exists or because a repository verifier passes.

```text
PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_TEMPLATE
B2_PRIMARY_RECORDING_AUTHORIZED_BY_THIS_TEMPLATE=NO
PRIMARY_MEDIA_ACCEPTANCE=NO
PRIMARY_TEST_DECODING_AUTHORIZED=NO
```
