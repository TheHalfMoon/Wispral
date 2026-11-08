# Wispral release quality gates

**Status:** CANDIDATE PLAN. Part of the [World-Class Master Plan](WISPRAL_WORLD_CLASS_MASTER_PLAN.md). No Wispral build exists; every gate below is `NOT_RUN`.

**Founder rule (binding):** nothing is published, deployed publicly, distributed as a binary outside the founder's own machines, or announced without the founder's explicit green light, recorded in a GitHub issue comment by the repository owner. Passing every gate below makes a release *eligible*; it does not authorize it.

## 1. Release stages

| Stage | Who can run it | Distribution | Authority to enter |
| --- | --- | --- | --- |
| **R0 Baseline** | Engineering agents | None (CI artifacts only) | Packet READY under the reconciled governance |
| **R1 Internal alpha** | Founder on owned machines | Private CI artifacts | All R1 gates PASS + independent review of the release head |
| **R2 Private beta** | Named invited testers | Private, invitation-only, signed | R2 gates PASS + **founder green light** |
| **R3 Release candidate** | Wider private group | Private, signed | R3 gates PASS + **founder green light** |
| **R4 Public release** | Anyone | Public channels | R4 gates PASS + **explicit founder green light to publish** |

A gate that is absent, skipped, pending, cancelled or failed is **not satisfied** (same rule as Constitution XVI.5). A gate result binds to an exact commit and artifact digest.

## 2. Gate catalogue

Each gate has an ID, the evidence that satisfies it, and the stage where it first becomes mandatory. Product-specific values are in §3.

| Gate | Evidence required | R1 | R2 | R3 | R4 |
| --- | --- | :-: | :-: | :-: | :-: |
| **G-PROV** Source provenance | Donor SHA, LICENSE/NOTICE files, delta register and third-party notices bundled in the app's About screen | ● | ● | ● | ● |
| **G-RIGHTS** Model and asset rights | Every bundled or downloadable artifact has a manifest row with code license, weight license and commercial status; no unresolved row | ● | ● | ● | ● |
| **G-BUILD** Reproducible build | Clean CI build from a lockfile; artifact SHA-256 recorded | ● | ● | ● | ● |
| **G-TEST** Test suites | Donor baseline suite plus Wispral suites at the exact head; failures listed, none newly introduced without a waiver ID | ● | ● | ● | ● |
| **G-SEC** Security fixtures | All SD-T / ST-T / KL-T negative fixtures for shipped capabilities PASS ([security](../engineering/WISPRAL_SECURITY_ARCHITECTURE.md)) | ● | ● | ● | ● |
| **G-EGRESS** Observed network behavior | Packet capture or firewall log of the *shipped binary* in offline mode shows zero unexpected connections; online mode shows only declared hosts | ● | ● | ● | ● |
| **G-INSTALL** Clean install | Fresh Windows 11 VM (and each claimed OS): install, first run, uninstall leaves no residue except declared user data; screenshots captured | — | ● | ● | ● |
| **G-E2E** Real user journeys | Scripted end-to-end journeys from the [UX specs](../design/) on real hardware with a real microphone; recordings or screenshots retained | ● | ● | ● | ● |
| **G-SHOTS** Native screenshots | Light, dark and high-contrast; English and Arabic (RTL); 100% and 150% scaling; reviewed against the [design review rubric](../design/WISPRAL_DESIGN_SYSTEM.md#11-design-review-method) | — | ● | ● | ● |
| **G-A11Y** Accessibility | Keyboard-only completion of core journeys; screen-reader pass (NVDA and Narrator on Windows); WCAG 2.2 AA contrast; Accessibility Insights automated scan with zero critical issues | — | ● | ● | ● |
| **G-PERF** Performance | Product budgets in §3 measured on the reference hardware matrix, reported as p50/p95 with n | — | ● | ● | ● |
| **G-LANG** Language quality | WB-AR and WB-EN results published internally for the shipped model routes, segmented, with confidence intervals; any claimed language has a measured cell | — | ● | ● | ● |
| **G-FAIL** Failure handling | Mic unplug, permission revoked, model missing, disk full, crash mid-job, network loss: each produces a visible, recoverable state; user work is preserved | ● | ● | ● | ● |
| **G-UPDATE** Update and rollback | Signed update applies; rollback to N-1 restores a working app and readable data | — | — | ● | ● |
| **G-SIGN** Code signing | Installer and binaries signed; SmartScreen or Gatekeeper behavior recorded honestly (an unsigned build is never described as warning-free) | — | ● | ● | ● |
| **G-DOCS** Documentation | User guide, privacy statement listing every network host and data store, known limitations, support channel | — | ● | ● | ● |
| **G-REVIEW** Independent review | Reviewer independent of the author covers the release range; blocking findings resolved | ● | ● | ● | ● |
| **G-LEGAL** Name and notices | Trademark/domain clearance review for the product name; AGPL/GPL obligations satisfied or covered by founder-confirmed grants (recorded per file, no confidential documents requested) | — | — | ● | ● |
| **G-GREEN** Founder green light | Repository-owner comment authorizing the exact stage and artifact | — | ● | ● | ● |

## 3. Product-specific acceptance values

Numbers marked *target* are planning targets to be confirmed or revised by the first measurements; they are not claims. A target can be changed only by a recorded decision **before** the run that tests it.

### 3.1 WisprSide

| Area | Gate value |
| --- | --- |
| Safety | WB-DELIVERY: **0** wrong-target insertions across the full fixture suite (hard gate); 100% of refusals keep the text recoverable |
| Egress | Offline mode: **0** outbound connections during a 30-minute scripted session |
| Indicator latency | Capsule visible ≤ 100 ms after activation key-down at p95 (*target*) |
| End-to-end latency | Key-up → text delivered for a 10-second utterance on the CPU reference laptop: p50 ≤ 1.0 s, p95 ≤ 2.0 s with the selected default model (*target*, model-dependent) |
| Resource | Idle RSS and CPU recorded; idle CPU ≈ 0% when not recording (*target*); no model kept in RAM after the configurable idle timeout |
| Language | English and MSA cells measured; Gulf Arabic and code-switch cells measured before any claim of support |
| Accessibility | All settings and history reachable by keyboard; state changes announced to screen readers |

### 3.2 WisprStudio

| Area | Gate value |
| --- | --- |
| Consent | **0** renders with revoked or absent consent across the revocation suite (hard gate) |
| Rights | **0** non-commercial weights reachable in a commercial-profile build (hard gate) |
| Recovery | Kill during long-form render ⇒ resume completes with identical segment identity; no partial file presented as final |
| Egress | Analytics off and URL ingest off verified by packet capture |
| Performance | Time-to-first-audio and real-time factor per engine on the GPU and CPU reference machines, reported (*no fixed target until baselined*) |
| Accessibility | Timeline operable by keyboard for core edits; RTL script editing correct |

### 3.3 Klaint

| Area | Gate value |
| --- | --- |
| Authority | **0** unauthorized tool commits and **0** free-text commitments on the frozen adversarial suite (hard gate) |
| Idempotency | **0** duplicate external commits across the timeout/unknown-outcome suite (hard gate) |
| Tenancy | **0** cross-tenant reads or writes across the two-tenant suite (hard gate) |
| Handoff | **0** AI messages sent after human takeover across the race suite (hard gate) |
| Quality | Test Lab regression suite pass rate recorded per release; regressions block until triaged |
| Operations | Clean install from documented manifests on a fresh Linux host; backup and restore of a tenant verified |

## 4. Rollback contracts

- **Desktop:** the installer keeps N-1; data formats are versioned with forward migrations and a tested downgrade path or a documented one-way migration with an automatic backup.
- **Klaint:** database migrations are reversible or snapshot-guarded; agent definitions are versioned and roll back independently of the service.
- **No rollback can undo an external effect.** Rollback disables the adapter and preserves records; committed connector actions remain in the outcome ledger.
