import type { DatabaseSync } from "node:sqlite";
import { OmallaError, jcsSha256, jcsSha256FromRawJson } from "@omalla/core";
import type { IdempotencyStore } from "@omalla/workflow";

export type IdempotencyClaimResult =
  | { kind: "claimed"; argsDigest: string }
  | { kind: "replayed"; statusCode: number; response: unknown; argsDigest: string };

interface MemoryIdempotencyEntry {
  argsDigest: string;
  status: "in_progress" | "completed";
  statusCode?: number;
  responseJson?: string;
  expiresAtMs: number;
}

/**
 * Durable SQLite `omalla_idempotency` coordinator (OM-T5).
 *
 * Persists `(tenant_id, scope, idem_key)` + RFC 8785 JCS SHA-256 `args_digest`
 * (strictly rejecting floats) BEFORE dispatching outbound calls, SMS, or workflows.
 */
export class SqliteIdempotencyManager {
  private readonly memoryFallback = new Map<string, MemoryIdempotencyEntry>();

  constructor(private readonly getSqlite: () => DatabaseSync | undefined) {}

  claim(input: {
    tenantId: string;
    scope: string;
    idemKey: string;
    payload: unknown;
    rawJson?: string;
    ttlSec?: number;
    nowMs?: number;
  }): IdempotencyClaimResult {
    const nowMs = input.nowMs ?? Date.now();
    const ttlSec = input.ttlSec ?? 24 * 60 * 60;
    const expiresAtMs = nowMs + Math.max(1, ttlSec) * 1000;

    const argsDigest =
      input.rawJson !== undefined && input.rawJson.trim().length > 0
        ? jcsSha256FromRawJson(input.rawJson)
        : jcsSha256(input.payload ?? {});

    const sqlite = this.getSqlite();
    if (sqlite) {
      sqlite.prepare(`DELETE FROM omalla_idempotency WHERE expires_at_ms <= ?`).run(nowMs);
      const inserted = sqlite
        .prepare(
          `INSERT INTO omalla_idempotency (
             tenant_id, scope, idem_key, args_digest, status, status_code, response_json, created_at_ms, expires_at_ms
           ) VALUES (?, ?, ?, ?, 'in_progress', NULL, NULL, ?, ?)
           ON CONFLICT(tenant_id, scope, idem_key) DO NOTHING`,
        )
        .run(input.tenantId, input.scope, input.idemKey, argsDigest, nowMs, expiresAtMs);

      if (Number(inserted.changes) > 0) {
        return { kind: "claimed", argsDigest };
      }

      const existing = sqlite
        .prepare(
          `SELECT args_digest, status, status_code, response_json
           FROM omalla_idempotency
           WHERE tenant_id = ? AND scope = ? AND idem_key = ?`,
        )
        .get(input.tenantId, input.scope, input.idemKey) as
        | {
            args_digest: string;
            status: string;
            status_code: number | null;
            response_json: string | null;
          }
        | undefined;

      if (!existing) {
        return { kind: "claimed", argsDigest };
      }
      if (existing.args_digest !== argsDigest) {
        throw new OmallaError(
          "conflict",
          "Idempotency-Key cannot be reused with a different canonical request payload",
          409,
        );
      }
      if (existing.status === "completed" && existing.response_json !== null) {
        return {
          kind: "replayed",
          statusCode: existing.status_code ?? 200,
          response: JSON.parse(existing.response_json),
          argsDigest,
        };
      }
      throw new OmallaError(
        "conflict",
        "A request with this Idempotency-Key is already in progress; reconcile outcome before retrying",
        409,
      );
    }

    const key = `${input.tenantId}\u0000${input.scope}\u0000${input.idemKey}`;
    const current = this.memoryFallback.get(key);
    if (current && current.expiresAtMs > nowMs) {
      if (current.argsDigest !== argsDigest) {
        throw new OmallaError(
          "conflict",
          "Idempotency-Key cannot be reused with a different canonical request payload",
          409,
        );
      }
      if (current.status === "completed" && current.responseJson !== undefined) {
        return {
          kind: "replayed",
          statusCode: current.statusCode ?? 200,
          response: JSON.parse(current.responseJson),
          argsDigest,
        };
      }
      throw new OmallaError(
        "conflict",
        "A request with this Idempotency-Key is already in progress; reconcile outcome before retrying",
        409,
      );
    }

    this.memoryFallback.set(key, {
      argsDigest,
      status: "in_progress",
      expiresAtMs,
    });
    return { kind: "claimed", argsDigest };
  }

  complete(input: {
    tenantId: string;
    scope: string;
    idemKey: string;
    statusCode: number;
    response: unknown;
  }): void {
    const responseJson = JSON.stringify(input.response);
    const sqlite = this.getSqlite();
    if (sqlite) {
      sqlite
        .prepare(
          `UPDATE omalla_idempotency
           SET status = 'completed', status_code = ?, response_json = ?
           WHERE tenant_id = ? AND scope = ? AND idem_key = ?`,
        )
        .run(input.statusCode, responseJson, input.tenantId, input.scope, input.idemKey);
      return;
    }
    const key = `${input.tenantId}\u0000${input.scope}\u0000${input.idemKey}`;
    const entry = this.memoryFallback.get(key);
    if (entry) {
      entry.status = "completed";
      entry.statusCode = input.statusCode;
      entry.responseJson = responseJson;
    }
  }

  /** Releases a claim ONLY when policy/validation failed before any external side effect started. */
  releasePreDispatch(tenantId: string, scope: string, idemKey: string): void {
    const sqlite = this.getSqlite();
    if (sqlite) {
      sqlite
        .prepare(
          `DELETE FROM omalla_idempotency
           WHERE tenant_id = ? AND scope = ? AND idem_key = ? AND status = 'in_progress'`,
        )
        .run(tenantId, scope, idemKey);
      return;
    }
    const key = `${tenantId}\u0000${scope}\u0000${idemKey}`;
    const entry = this.memoryFallback.get(key);
    if (entry?.status === "in_progress") {
      this.memoryFallback.delete(key);
    }
  }

  /** Tenant-scoped `IdempotencyStore` adapter for `WorkflowEngine`. */
  forWorkflowTenant(tenantId: string): IdempotencyStore {
    return {
      has: (key: string): boolean => {
        const nowMs = Date.now();
        const sqlite = this.getSqlite();
        if (sqlite) {
          sqlite.prepare(`DELETE FROM omalla_idempotency WHERE expires_at_ms <= ?`).run(nowMs);
          const row = sqlite
            .prepare(
              `SELECT 1 AS ok FROM omalla_idempotency
               WHERE tenant_id = ? AND scope = 'workflow_run' AND idem_key = ? AND expires_at_ms > ?`,
            )
            .get(tenantId, key, nowMs);
          return Boolean(row);
        }
        const composite = `${tenantId}\u0000workflow_run\u0000${key}`;
        const entry = this.memoryFallback.get(composite);
        return Boolean(entry && entry.expiresAtMs > nowMs);
      },
      remember: (key: string, ttlSeconds: number): void => {
        const nowMs = Date.now();
        const expiresAtMs = nowMs + Math.max(1, ttlSeconds) * 1000;
        const sqlite = this.getSqlite();
        if (sqlite) {
          sqlite
            .prepare(
              `INSERT OR REPLACE INTO omalla_idempotency (
                 tenant_id, scope, idem_key, args_digest, status, status_code, response_json, created_at_ms, expires_at_ms
               ) VALUES (?, 'workflow_run', ?, 'workflow', 'completed', 200, '{}', ?, ?)`,
            )
            .run(tenantId, key, nowMs, expiresAtMs);
          return;
        }
        const composite = `${tenantId}\u0000workflow_run\u0000${key}`;
        this.memoryFallback.set(composite, {
          argsDigest: "workflow",
          status: "completed",
          statusCode: 200,
          responseJson: "{}",
          expiresAtMs,
        });
      },
    };
  }
}
