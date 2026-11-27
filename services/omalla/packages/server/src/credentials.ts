import { OmallaError, SecretBox, newId, nowIso } from "@omalla/core";
import type { Credential, Database } from "@omalla/core";

/**
 * Explicit allowlist of provider API key env var names permitted as single-tenant
 * operator convenience fallbacks (OM-T1). Host infrastructure secrets such as
 * `OMALLA_MASTER_KEY`, `TWILIO_AUTH_TOKEN`, `OMALLA_SIP_GATEWAY_TOKEN`, or arbitrary
 * process environment variables are NEVER readable via `CredentialService.get`.
 */
export const ALLOWED_ENV_CREDENTIAL_NAMES = new Set<string>([
  "OPENAI_API_KEY",
  "DEEPGRAM_API_KEY",
  "ELEVENLABS_API_KEY",
  "N8N_WEBHOOK_SECRET",
  "MCP_TOKEN",
  "TRELLO_KEY",
  "TRELLO_TOKEN",
  "GOOGLE_ACCESS_TOKEN",
  "SLACK_BOT_TOKEN",
  "WHATSAPP_ACCESS_TOKEN",
]);

/**
 * Credential storage.
 *
 * Values are encrypted with the host's master key before they reach the
 * database. Allowlisted provider environment variables are read as a fallback
 * in single-tenant mode (or when `allowSharedEnvCredentials` is explicitly set),
 * and a stored tenant credential always wins.
 */
export class CredentialService {
  constructor(
    private readonly db: Database,
    private readonly box: SecretBox,
    private readonly options: { allowSharedEnvCredentials?: boolean } = {},
  ) {}

  list(tenantId: string): Array<Omit<Credential, "ciphertext">> {
    return this.db
      .col("credentials")
      .list((credential) => credential.tenantId === tenantId)
      .map(({ ciphertext: _ciphertext, ...rest }) => rest);
  }

  async set(tenantId: string, name: string, value: string, provider = "custom"): Promise<void> {
    if (!/^[A-Z][A-Z0-9_]{1,63}$/.test(name)) {
      throw new OmallaError("validation", "credential names must be UPPER_SNAKE_CASE", 400);
    }
    if (!value.trim()) throw new OmallaError("validation", "credential value is empty", 400);
    const ciphertext = this.box.encrypt(value);
    const existing = this.db
      .col("credentials")
      .list((credential) => credential.tenantId === tenantId && credential.name === name)[0];
    if (existing) {
      this.db.col("credentials").update(existing.id, {
        ciphertext,
        lastRotatedAt: nowIso(),
        provider,
      });
      return;
    }
    this.db.col("credentials").insert({
      id: newId("cred"),
      tenantId,
      name,
      provider,
      ciphertext,
      createdAt: nowIso(),
    });
  }

  /** Reads a credential by name; never logs or returns ciphertext. */
  async get(tenantId: string, name: string): Promise<string | undefined> {
    const record = this.db
      .col("credentials")
      .list((credential) => credential.tenantId === tenantId && credential.name === name)[0];
    if (record) {
      try {
        return this.box.decrypt(record.ciphertext);
      } catch {
        throw new OmallaError(
          "internal",
          `credential ${name} could not be decrypted with the current master key`,
          500,
        );
      }
    }
    if (!ALLOWED_ENV_CREDENTIAL_NAMES.has(name)) {
      return undefined;
    }
    if (this.db.col("tenants").count() > 1 && this.options.allowSharedEnvCredentials !== true) {
      return undefined;
    }
    return process.env[name];
  }

  remove(tenantId: string, name: string): boolean {
    const record = this.db
      .col("credentials")
      .list((credential) => credential.tenantId === tenantId && credential.name === name)[0];
    if (!record) return false;
    return this.db.col("credentials").remove(record.id);
  }
}
