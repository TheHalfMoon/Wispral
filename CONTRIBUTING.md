# Contributing to Wispral

Thank you for wanting to help build Wispral.

Wispral is currently in a founding research/specification phase. The project is intentionally resisting premature feature growth while protocol, speech, benchmark, security, and architecture assumptions are being qualified.

## Before opening a pull request

Read:

1. `AGENTS.md`
2. `CONSTITUTION.md`
3. `docs/canonical/CURRENT_STATE.md`
4. `specs/CURRENT.md`
5. the active specification authority chain relevant to your change

Live repository state overrides this document if the frontier has moved.

## High-value contributions during the founding phase

Useful contributions include:

- reproducing a documented research observation;
- correcting a primary-source citation;
- challenging benchmark methodology;
- providing accessibility expertise;
- identifying security/privacy failure modes;
- contributing ACP/protocol implementation knowledge;
- reporting platform audio behavior with exact OS/hardware/tool versions;
- improving a spec by narrowing ambiguity or making acceptance evidence stronger;
- reporting a license/provenance concern.

Broad production implementation is not yet authorized unless selected by `specs/CURRENT.md`.

## Pull-request expectations

A PR should state:

- active spec/task ID where applicable;
- exact intended outcome;
- exact changed surface;
- evidence/checks run;
- checks not run and why;
- residual risk/limitations;
- provenance for adapted external material;
- whether the change modifies a public claim.

Keep changes bounded. Unrelated cleanup belongs in another unit only if independently justified.

## Research contributions

For measurements, include enough information to reproduce the observation:

- hardware and OS;
- exact software/model versions;
- commands/configuration;
- inputs/fixtures;
- raw outputs when safe to publish;
- scoring or interpretation method;
- failures and limitations.

Do not remove losing runs merely to make a comparison look stronger.

## External code

Do not copy or adapt implementation material without checking its license and recording provenance. Public availability does not imply permission to reuse code under Wispral's eventual license.

## Security

Do not open public issues containing credentials, sensitive transcripts, private repository content, or exploitable security details. Follow `SECURITY.md`.

## Code style

Product code has not been authorized yet. When Rust code becomes canonical, repository-specific format/lint/test commands in `AGENTS.md` and the active spec govern acceptance.

## AI-assisted contributions

AI tools may assist development, but contributors remain responsible for the resulting content, licensing, evidence, and correctness. An AI summary is not proof that a test ran or a source permits reuse.

## Community standard

Be specific, technical, and respectful. Challenge claims and designs rather than people. Competitor and donor projects should be described accurately and credited appropriately.