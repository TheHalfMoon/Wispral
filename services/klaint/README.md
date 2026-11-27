# Klaint

**Klaint** (part of **Wispral** by **Halfmoon**) is a self-hostable enterprise customer-experience and verified customer-resolution platform built on deterministic trust boundaries.

## Architecture Highlights

- **Out-of-Process Capability Broker (`klaint.broker`):** Separate OS subprocess receiving its 256-bit `broker_issuance_secret` exclusively over `stdin`. Holds Ed25519 signing keys and connector secrets strictly in broker memory, issuing single-use (`<= 60 s` TTL), RFC 8785 JCS argument-bound capability tokens (`effect_intent.schema.json`) while rejecting IEEE-754 floats and forged caller `customer_id`s.
- **Per-Tenant SQLite WAL Ledger & Reconcile Probes (`klaint.storage`):** Physical per-tenant isolation (`<data_dir>/tenants/<tenant_id>/klaint.db`), atomic `BEGIN IMMEDIATE` nonce consumption, pre-dispatch `action_ledger` (`pending -> dispatched -> settled | abandoned | unknown -> reconciled` via read-only `reconcile_probe`, never blind retry), and tamper-evident SHA-256 hash-chained `audit_log`.
- **Commitment Output Gate (`klaint.conversation`):** Clause-buffered / `BLOCK`-mode gate verifying English and Arabic commitment claims against committed `action_ledger` receipts before any customer text or voice delivery.
- **Procedures SOP Engine (`klaint.procedures`):** Compiles natural-language and structured SOPs into deterministic policy graphs with monetary thresholds, step-up verification, immutable version history, 4-eyes approval (`author_id != approver_id`), and 1-click rollback.
- **8-Stage Deterministic Resolution (`klaint.resolution`):** `IDENTIFY -> INVESTIGATE -> UNDERSTAND -> DECIDE -> AUTHORIZE -> EXECUTE -> VERIFY -> RESOLVE` with structured step traces.
- **Cited Tenant-ACL Hybrid RAG (`klaint.knowledge`):** SQLite FTS5 + n-gram dense-vector cosine similarity fused with Reciprocal Rank Fusion ($k=60$), 4-level Arabic match-key normalization, document ACLs, and explicit `UNAVAILABLE` vs `CONFIRMED_NEGATIVE` epistemic status.
- **Inbox, Epoch Takeover & Chatwoot Core Bridge (`klaint.inbox`):** Customer profiles, tickets, SLAs, monotonic `ownership_epoch` human takeover discarding stale AI work, and Standard Webhooks HMAC-SHA256 verification.
- **Klaint Studio, Widget, Simulation, Analytics & Voice (`klaint.server`, `klaint.ui`, `klaint.simulation`, `klaint.analytics`, `klaint.voice`):** Bilingual RTL/LTR Quiet Signal `#1F7A65` Studio SPA with the "Why" Explainability Panel, `/widget` customer chat, `tau2-bench`-style DB-hash simulation across English and 4 Arabic varieties + adversarial suite, verified FCR analytics, and Omalla voice bridge.

## Quick Start

```bash
python -m klaint.cli doctor
python -m klaint.server.app --host 127.0.0.1 --port 8090
pytest services/klaint/tests -v
```
