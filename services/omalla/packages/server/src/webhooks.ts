import type { DatabaseSync } from "node:sqlite";
import {
  DEFAULT_WEBHOOK_SKEW_SEC,
  verifySignedWebhookRaw,
  type WebhookVerifyInput,
  type WebhookVerifyOutcome,
} from "@omalla/core";

export { DEFAULT_WEBHOOK_SKEW_SEC, verifySignedWebhookRaw };
export type { WebhookVerifyInput, WebhookVerifyOutcome };

export const DEFAULT_REPLAY_TTL_SEC = 24 * 60 * 60;

/**
 * Durable SQLite `(tenant_id, scope, event_key)` anti-replay cache (OM-T3).
 */
export class WebhookReplayCache {
  private readonly memoryFallback = new Map<string, number>();

  constructor(private readonly getSqlite: () => DatabaseSync | undefined) {}

  /**
   * Atomically records `(tenantId, scope, eventKey)` if unseen within TTL.
   * Returns `true` if fresh (accepted), `false` if duplicate/replayed!
   */
  claimEvent(
    tenantId: string,
    scope: string,
    eventKey: string,
    ttlSec = DEFAULT_REPLAY_TTL_SEC,
    nowMs = Date.now(),
  ): boolean {
    const expiresAtMs = nowMs + Math.max(1, ttlSec) * 1000;
    const sqlite = this.getSqlite();
    if (sqlite) {
      sqlite
        .prepare(`DELETE FROM omalla_webhook_replay WHERE expires_at_ms <= ?`)
        .run(nowMs);
      const result = sqlite
        .prepare(
          `INSERT INTO omalla_webhook_replay (tenant_id, scope, event_key, created_at_ms, expires_at_ms)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(tenant_id, scope, event_key) DO NOTHING`,
        )
        .run(tenantId, scope, eventKey, nowMs, expiresAtMs);
      return Number(result.changes) > 0;
    }

    const composite = `${tenantId}\u0000${scope}\u0000${eventKey}`;
    const existingExp = this.memoryFallback.get(composite);
    if (existingExp !== undefined && existingExp > nowMs) {
      return false;
    }
    this.memoryFallback.set(composite, expiresAtMs);
    return true;
  }
}
