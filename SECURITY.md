# Security Policy

Wispral is currently in a pre-product founding research phase. There is no production release and no supported deployment surface yet.

## Reporting a vulnerability

Do not publish credentials, private transcripts, sensitive repository content, or detailed exploit instructions in a public issue.

If GitHub private vulnerability reporting is available for this repository, prefer that channel. If it is not available, open a minimal public issue stating that you have a security concern and need a private maintainer contact path; do not include exploit details in the issue.

## Scope during the founding phase

Security review is especially welcome for:

- microphone and recording-state ambiguity;
- unintended/ambient voice authorization;
- transcript or raw-audio persistence;
- credential leakage in traces/logs;
- permission binding and stale approvals;
- cancellation state misrepresentation;
- agent protocol trust boundaries;
- PTY/terminal escape or command-injection risks;
- repository-context data exfiltration;
- cloud speech-provider routing/privacy;
- dependency and supply-chain provenance;
- future plugin/adapter capability isolation.

See `docs/security/THREAT_MODEL.md` for the current founding threat model.

## Supported versions

No version is currently production-supported.

| Version | Supported |
| --- | --- |
| unreleased founding research | research feedback only |

This table will change when Wispral publishes a version with an explicit support contract.

## Security claim discipline

Documentation of a threat does not prove mitigation. A mitigation does not become `VERIFIED` until the active specification's exact evidence requirements are satisfied.

Do not interpret the presence of `SECURITY.md` or a threat model as a statement that Wispral is safe for production or consequential autonomous operation.