# Wispral Category and Adoption Strategy

**Status:** founding strategy candidate  
**Goal:** maximize the probability that exceptional product utility becomes category-scale open-source adoption

## 1. Category claim

Wispral should not position itself as another dictation application or coding agent.

Preferred category language:

> **Voice-native control plane for AI agents.**

Preferred concise description:

> **Talk to your coding agents. Interrupt, steer, approve, and think aloud without leaving the terminal.**

This language must evolve if product evidence proves a better category boundary.

## 2. Strategic differentiation

The founding differentiation stack is:

1. protocol-native agent control rather than text-box insertion;
2. repository-aware developer entity interpretation;
3. explicit command vs tentative-context semantics;
4. first-class interruption and steering;
5. deterministic permission/trust policy around probabilistic speech;
6. multi-agent portability;
7. local-first operation;
8. reproducible public benchmarks.

A competitor matching one layer does not invalidate the thesis. Wispral must make the combination coherent and simpler than assembling separate tools.

## 3. The 15-second demo test

Before public launch, a cold viewer should understand the product from one short terminal recording.

Target demo narrative:

1. developer starts a familiar coding agent through Wispral;
2. developer speaks a repository-specific task containing a path/symbol/constraint;
3. Wispral visibly resolves technical entities;
4. the agent begins work;
5. developer interrupts mid-turn with a changed constraint;
6. Wispral cancels/steers immediately;
7. a permission request is summarized with visible scope;
8. developer approves or denies deliberately;
9. final status is concise, with full details remaining in the terminal.

If this cannot be communicated cleanly, product complexity is leaking into the first-use story.

## 4. Adoption loops built into product quality

### Loop A — Works with the agent users already have

Wispral should reduce switching cost by integrating with existing coding agents rather than requiring migration to a new agent.

### Loop B — One-command first value

Long-term distribution should target simple entry points such as package-manager installation plus `wispral <agent>` or equivalent. Exact commands are not selected until CLI design is specified.

### Loop C — Reproducible benchmark credibility

WispralBench can earn attention beyond direct users if it becomes a useful, fair benchmark for developer speech and agent-control latency.

### Loop D — Extension contributions

Once repeated integrations justify stable interfaces, external contributors should be able to add agent/speech/context support without changing core policy.

### Loop E — Safe shareable proof

A future session recap may expose non-sensitive operational metrics such as duration, interrupts, tests observed, and files changed, but must never default to leaking prompts, transcripts, repository names, diffs, or secrets. This is a future product hypothesis, not current scope.

## 5. Launch readiness gates

Do not launch broadly because a calendar date arrived.

A category launch should wait until evidence shows, at minimum:

- a reliable fresh-install path on the declared launch platforms;
- at least two independent coding agents exercising the portable interaction contract;
- a developer-entity experience that visibly beats raw generic dictation on the published WispralBench methodology or an equally compelling measured result;
- reliable user interruption with measured instrumentation;
- truthful permission/cancellation state;
- a polished terminal demo;
- concise documentation and troubleshooting;
- no known critical microphone/privacy/credential issue;
- license/provenance completeness;
- CI and release reproducibility appropriate to the supported platforms.

## 6. Adoption milestones

The project may track external milestones such as:

- first 100 external users;
- first 10 independent contributors;
- first third-party adapter;
- first external benchmark reproduction;
- 1k / 10k / 25k / 50k / 100k / 200k+ GitHub stars;
- GitHub Trending placement;
- major community launch results;
- ecosystem integrations that mention Wispral independently.

These metrics guide distribution learning. They do not change `VERIFIED` engineering state.

## 7. 200k-star ambition

200k+ GitHub stars is an intentionally extreme aspiration. There is no honest project plan that can guarantee it.

The strategy is therefore to maximize prerequisites that historically make category-scale repositories possible:

- instantly understandable category;
- memorable name and visual identity;
- immediate first-run magic;
- zero or minimal account friction;
- broad compatibility;
- real technical depth beneath the demo;
- open, permissive-enough contribution surface subject to the eventual license decision;
- excellent documentation;
- frequent evidence-backed releases;
- visible maintainer responsiveness;
- a benchmark/research artifact valuable even to non-users;
- ecosystem rather than single-vendor dependence;
- distribution across package managers and communities;
- ruthless avoidance of scope that makes the core product slow or confusing.

Stars are earned by the product and community. They cannot be declared by specification.

## 8. Brand note

The founder selected `Wispral` as the repository/product name on 2026-09-01.

Because `Wispral` is phonetically and visually near `Wispr`, and Wispr publicly operates in voice interfaces, Specification 000 must record namespace/SEO/trademark-risk research sufficient for an engineering/go-to-market decision. This repository does not provide legal advice and must not claim trademark clearance without qualified legal review.

The name remains founder-selected unless a later explicit decision changes it.

## 9. Community posture

Wispral should be welcoming to agent vendors, editor teams, speech researchers, accessibility contributors, systems engineers, and independent developers.

Competitive research must be specific and respectful. The project should compare measurable behavior, not attack competitor motives or communities.

Donor code must be license-reviewed and attributed. A successful open-source project should be easy to trust both technically and socially.

## 10. Scope defense

The fastest way to lose the category is to become a generic AI desktop before the core control plane is exceptional.

Until evidence changes the strategy, say no to unrelated dashboards, avatars, custom agents, memory platforms, collaboration suites, and visual spectacle that do not improve the core spoken-agent control loop.