import { existsSync } from "node:fs";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";
import { nowIso } from "./ids.js";
import type {
  Agent,
  AgentVersion,
  ApiKey,
  AuditEvent,
  Booking,
  Call,
  Campaign,
  Contact,
  Credential,
  Escalation,
  Evaluation,
  IvrMenu,
  KnowledgeBase,
  PhoneNumber,
  SmsMessage,
  Task,
  Tenant,
  ToolDefinition,
  User,
  WebhookEndpoint,
  Workflow,
  WorkflowRun,
  WorkflowVersion,
} from "./types.js";

export interface DbShape {
  schemaVersion: number;
  tenants: Tenant[];
  users: User[];
  apiKeys: ApiKey[];
  credentials: Credential[];
  agents: Agent[];
  agentVersions: AgentVersion[];
  tools: ToolDefinition[];
  phoneNumbers: PhoneNumber[];
  smsMessages: SmsMessage[];
  ivrMenus: IvrMenu[];
  calls: Call[];
  knowledgeBases: KnowledgeBase[];
  workflows: Workflow[];
  workflowVersions: WorkflowVersion[];
  workflowRuns: WorkflowRun[];
  campaigns: Campaign[];
  webhookEndpoints: WebhookEndpoint[];
  auditEvents: AuditEvent[];
  evaluations: Evaluation[];
  contacts: Contact[];
  bookings: Booking[];
  tasks: Task[];
  escalations: Escalation[];
}

const EMPTY: DbShape = {
  schemaVersion: 2,
  tenants: [],
  users: [],
  apiKeys: [],
  credentials: [],
  agents: [],
  agentVersions: [],
  tools: [],
  phoneNumbers: [],
  smsMessages: [],
  ivrMenus: [],
  calls: [],
  knowledgeBases: [],
  workflows: [],
  workflowVersions: [],
  workflowRuns: [],
  campaigns: [],
  webhookEndpoints: [],
  auditEvents: [],
  evaluations: [],
  contacts: [],
  bookings: [],
  tasks: [],
  escalations: [],
};

export type CollectionName = Exclude<keyof DbShape, "schemaVersion">;

type Entity = { id: string; tenantId?: string };

interface CollectionPersistenceHooks<T extends Entity> {
  onUpsert?: (item: T) => void;
  onRemove?: (id: string) => void;
  onClear?: () => void;
  onChange?: () => void;
}

/**
 * In-memory indexed collection backed either by synchronous Node 24 SQLite WAL
 * persistence (default for server runtime `.db`/`.sqlite` files) or atomic JSON
 * snapshots (`.json` files).
 */
export class Collection<T extends Entity> {
  private items: T[] = [];
  private index = new Map<string, T>();

  constructor(private readonly hooks: CollectionPersistenceHooks<T>) {}

  load(items: T[]): void {
    this.items = [...items];
    this.index = new Map(items.map((item) => [item.id, item]));
  }

  toArray(): T[] {
    return this.items.map((item) => structuredClone(item));
  }

  /** Internal, non-cloned iteration for hot paths. Do not mutate. */
  raw(): readonly T[] {
    return this.items;
  }

  get(id: string): T | undefined {
    const found = this.index.get(id);
    return found ? structuredClone(found) : undefined;
  }

  get rawGet(): (id: string) => T | undefined {
    return (id: string) => this.index.get(id);
  }

  list(predicate?: (item: T) => boolean): T[] {
    const source = predicate ? this.items.filter(predicate) : this.items;
    return source.map((item) => structuredClone(item));
  }

  insert(item: T): T {
    if (this.index.has(item.id)) {
      throw new Error(`duplicate id ${item.id}`);
    }
    const stored = structuredClone(item);
    this.items.push(stored);
    this.index.set(item.id, stored);
    this.hooks.onUpsert?.(stored);
    this.hooks.onChange?.();
    return structuredClone(stored);
  }

  update(id: string, patch: Partial<T> | ((current: T) => T)): T {
    const current = this.index.get(id);
    if (!current) throw new Error(`missing ${id}`);
    const next =
      typeof patch === "function"
        ? (patch(structuredClone(current)) as T)
        : ({ ...current, ...patch } as T);
    if (next.id !== id) throw new Error("id is immutable");
    const position = this.items.findIndex((item) => item.id === id);
    this.items[position] = next;
    this.index.set(id, next);
    this.hooks.onUpsert?.(next);
    this.hooks.onChange?.();
    return structuredClone(next);
  }

  upsert(item: T): T {
    return this.index.has(item.id) ? this.update(item.id, item) : this.insert(item);
  }

  remove(id: string): boolean {
    const position = this.items.findIndex((item) => item.id === id);
    if (position < 0) return false;
    this.items.splice(position, 1);
    this.index.delete(id);
    this.hooks.onRemove?.(id);
    this.hooks.onChange?.();
    return true;
  }

  count(predicate?: (item: T) => boolean): number {
    return predicate ? this.items.filter(predicate).length : this.items.length;
  }

  clear(): void {
    this.items = [];
    this.index.clear();
    this.hooks.onClear?.();
    this.hooks.onChange?.();
  }
}

export interface DatabaseOptions {
  filePath: string;
  /** Set false for ephemeral test databases. */
  persist?: boolean;
  /** Optional explicit path to a legacy `omalla.db.json` file for one-time migration into SQLite. */
  legacyJsonPath?: string;
}

const SQLITE_SCHEMA = `
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS omalla_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS omalla_entities (
  collection TEXT NOT NULL,
  id TEXT NOT NULL,
  tenant_id TEXT,
  updated_at TEXT NOT NULL,
  payload TEXT NOT NULL,
  PRIMARY KEY (collection, id)
);

CREATE INDEX IF NOT EXISTS idx_omalla_entities_tenant
  ON omalla_entities (collection, tenant_id);

CREATE TABLE IF NOT EXISTS omalla_webhook_replay (
  tenant_id TEXT NOT NULL,
  scope TEXT NOT NULL,
  event_key TEXT NOT NULL,
  created_at_ms INTEGER NOT NULL,
  expires_at_ms INTEGER NOT NULL,
  PRIMARY KEY (tenant_id, scope, event_key)
);

CREATE INDEX IF NOT EXISTS idx_omalla_webhook_replay_exp
  ON omalla_webhook_replay (expires_at_ms);

CREATE TABLE IF NOT EXISTS omalla_idempotency (
  tenant_id TEXT NOT NULL,
  scope TEXT NOT NULL,
  idem_key TEXT NOT NULL,
  args_digest TEXT NOT NULL,
  status TEXT NOT NULL,
  status_code INTEGER,
  response_json TEXT,
  created_at_ms INTEGER NOT NULL,
  expires_at_ms INTEGER NOT NULL,
  PRIMARY KEY (tenant_id, scope, idem_key)
);

CREATE INDEX IF NOT EXISTS idx_omalla_idempotency_exp
  ON omalla_idempotency (expires_at_ms);
`;

function isSqlitePath(filePath: string): boolean {
  const lower = filePath.toLowerCase();
  return lower.endsWith(".db") || lower.endsWith(".sqlite") || lower.endsWith(".sqlite3") || filePath === ":memory:";
}

export class Database {
  private readonly collections = new Map<CollectionName, Collection<Entity>>();
  private readonly sqlite: DatabaseSync | undefined;
  private closed = false;
  private saveTimer: NodeJS.Timeout | undefined;
  private saving: Promise<void> | undefined;
  private dirty = false;
  private backgroundError: Error | undefined;

  private constructor(
    private readonly options: DatabaseOptions,
    data: DbShape,
    sqlite?: DatabaseSync,
  ) {
    this.sqlite = sqlite;
    const names = Object.keys(EMPTY).filter((key) => key !== "schemaVersion") as CollectionName[];

    const upsertStmt = sqlite
      ? sqlite.prepare(
          `INSERT INTO omalla_entities (collection, id, tenant_id, updated_at, payload)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(collection, id) DO UPDATE SET
             tenant_id = excluded.tenant_id,
             updated_at = excluded.updated_at,
             payload = excluded.payload`,
        )
      : undefined;
    const deleteStmt = sqlite
      ? sqlite.prepare(`DELETE FROM omalla_entities WHERE collection = ? AND id = ?`)
      : undefined;
    const clearStmt = sqlite
      ? sqlite.prepare(`DELETE FROM omalla_entities WHERE collection = ?`)
      : undefined;

    for (const name of names) {
      const collection = new Collection<Entity>(
        sqlite
          ? {
              onUpsert: (item) => {
                if (this.closed) return;
                upsertStmt?.run(
                  name,
                  item.id,
                  typeof item.tenantId === "string" ? item.tenantId : null,
                  nowIso(),
                  JSON.stringify(item),
                );
              },
              onRemove: (id) => {
                if (this.closed) return;
                deleteStmt?.run(name, id);
              },
              onClear: () => {
                if (this.closed) return;
                clearStmt?.run(name);
              },
            }
          : {
              onChange: () => this.markDirty(),
            },
      );
      collection.load((data[name] ?? []) as Entity[]);
      this.collections.set(name, collection);
    }
  }

  static async open(options: DatabaseOptions): Promise<Database> {
    if (isSqlitePath(options.filePath)) {
      return Database.openSqlite(options);
    }

    let data: DbShape = { ...EMPTY };
    if (options.persist !== false) {
      try {
        const raw = await readFile(options.filePath, "utf8");
        const parsed = JSON.parse(raw) as Partial<DbShape>;
        data = { ...EMPTY, ...parsed, schemaVersion: parsed.schemaVersion ?? EMPTY.schemaVersion };
      } catch (error) {
        const code = (error as NodeJS.ErrnoException).code;
        if (code !== "ENOENT" && code !== "ENOTDIR") throw error;
      }
    }
    return new Database(options, data);
  }

  private static async openSqlite(options: DatabaseOptions): Promise<Database> {
    const dbPath = options.persist === false ? ":memory:" : options.filePath;
    if (dbPath !== ":memory:") {
      await mkdir(path.dirname(dbPath), { recursive: true });
    }
    const sqlite = new DatabaseSync(dbPath);
    sqlite.exec(SQLITE_SCHEMA);

    const names = Object.keys(EMPTY).filter((key) => key !== "schemaVersion") as CollectionName[];
    const data: DbShape = structuredClone(EMPTY);

    const countRow = sqlite.prepare(`SELECT COUNT(*) AS cnt FROM omalla_entities`).get() as
      | { cnt?: number }
      | undefined;
    const entityCount = Number(countRow?.cnt ?? 0);

    const migratedRow = sqlite
      .prepare(`SELECT value FROM omalla_meta WHERE key = 'migrated_legacy_json'`)
      .get() as { value?: string } | undefined;

    const legacyPath =
      options.legacyJsonPath ??
      (dbPath !== ":memory:" ? `${dbPath}.json` : undefined);

    if (!migratedRow && entityCount === 0 && legacyPath && existsSync(legacyPath)) {
      const raw = await readFile(legacyPath, "utf8");
      const parsed = JSON.parse(raw) as Partial<DbShape>;
      const insertStmt = sqlite.prepare(
        `INSERT OR REPLACE INTO omalla_entities (collection, id, tenant_id, updated_at, payload)
         VALUES (?, ?, ?, ?, ?)`,
      );
      const now = nowIso();
      sqlite.exec("BEGIN IMMEDIATE");
      try {
        for (const name of names) {
          const items = (parsed[name] ?? []) as Entity[];
          (data[name] as unknown as Entity[]) = items;
          for (const item of items) {
            insertStmt.run(
              name,
              item.id,
              typeof item.tenantId === "string" ? item.tenantId : null,
              now,
              JSON.stringify(item),
            );
          }
        }
        sqlite
          .prepare(`INSERT OR REPLACE INTO omalla_meta (key, value) VALUES ('migrated_legacy_json', ?)`)
          .run(now);
        sqlite.exec("COMMIT");
      } catch (error) {
        sqlite.exec("ROLLBACK");
        sqlite.close();
        throw error;
      }
      await rename(legacyPath, `${legacyPath}.migrated`).catch(() => {});
    } else if (entityCount > 0) {
      const rows = sqlite
        .prepare(`SELECT collection, payload FROM omalla_entities ORDER BY rowid ASC`)
        .all() as Array<{ collection: string; payload: string }>;
      for (const row of rows) {
        const colName = row.collection as CollectionName;
        if (colName in data) {
          (data[colName] as unknown as Entity[]).push(JSON.parse(row.payload) as Entity);
        }
      }
    }

    return new Database(options, data, sqlite);
  }

  /** Underlying Node 24 SQLite connection when running in WAL mode. */
  get sqliteDb(): DatabaseSync | undefined {
    return this.closed ? undefined : this.sqlite;
  }

  get journalMode(): string {
    if (!this.sqlite || this.closed) return "json";
    const row = this.sqlite.prepare("PRAGMA journal_mode").get() as { journal_mode?: string } | undefined;
    return String(row?.journal_mode ?? "unknown");
  }

  col<K extends CollectionName>(name: K): Collection<DbShape[K][number] & Entity> {
    const collection = this.collections.get(name);
    if (!collection) throw new Error(`unknown collection ${name}`);
    return collection as unknown as Collection<DbShape[K][number] & Entity>;
  }

  private markDirty(): void {
    this.dirty = true;
    if (this.options.persist === false || this.saveTimer) return;
    this.saveTimer = setTimeout(() => {
      this.saveTimer = undefined;
      void this.flush().catch((error: unknown) => {
        this.backgroundError =
          error instanceof Error ? error : new Error(String(error));
      });
    }, 25);
  }

  /** Force a durable write. Safe to call concurrently. */
  async flush(): Promise<void> {
    if (this.sqlite) {
      if (!this.closed && this.options.persist !== false) {
        this.sqlite.exec("PRAGMA wal_checkpoint(PASSIVE)");
      }
      return;
    }
    if (this.backgroundError) {
      if (!this.dirty) {
        const error = this.backgroundError;
        this.backgroundError = undefined;
        throw error;
      }
      this.backgroundError = undefined;
    }
    if (this.options.persist === false) {
      this.dirty = false;
      return;
    }
    if (this.saving) {
      await this.saving;
      if (!this.dirty) return;
    }
    if (!this.dirty) return;
    this.dirty = false;

    this.saving = this.writeSnapshot();
    try {
      await this.saving;
    } finally {
      this.saving = undefined;
    }
  }

  private async writeSnapshot(): Promise<void> {
    const snapshot: Record<string, unknown> = { schemaVersion: EMPTY.schemaVersion };
    for (const [name, collection] of this.collections) {
      snapshot[name] = collection.raw();
    }
    await mkdir(path.dirname(this.options.filePath), { recursive: true });
    const tmp = `${this.options.filePath}.${process.pid}.tmp`;
    await writeFile(tmp, JSON.stringify(snapshot), "utf8");
    await rename(tmp, this.options.filePath);
  }

  async close(): Promise<void> {
    if (this.closed) return;
    if (this.saveTimer) {
      clearTimeout(this.saveTimer);
      this.saveTimer = undefined;
    }
    if (this.sqlite) {
      this.closed = true;
      try {
        if (this.options.persist !== false && this.options.filePath !== ":memory:") {
          try {
            this.sqlite.exec("PRAGMA wal_checkpoint(TRUNCATE)");
          } catch (error) {
            const msg = String((error as Error)?.message ?? error);
            if (!msg.includes("SQLITE_BUSY") && !msg.toLowerCase().includes("locked")) {
              throw error;
            }
          }
        }
      } finally {
        this.sqlite.close();
      }
      return;
    }
    await this.flush();
    this.closed = true;
  }

  stats(): Record<string, number> {
    const out: Record<string, number> = {};
    for (const [name, collection] of this.collections) {
      out[name] = collection.count();
    }
    return out;
  }
}
