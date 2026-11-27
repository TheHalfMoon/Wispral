import { createCipheriv, createDecipheriv, createHash, randomBytes, timingSafeEqual } from "node:crypto";
import { chmod, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

/**
 * AES-256-GCM envelope for provider credentials.
 *
 * The key never leaves the host. When OMALLA_MASTER_KEY is not set a local key
 * file is generated with owner-only permissions, which keeps the zero-cost
 * local mode usable without weakening the at-rest format.
 */
export class SecretBox {
  private constructor(private readonly key: Buffer) {}

  static async open(options: { dir: string; masterKey?: string }): Promise<SecretBox> {
    const configured = options.masterKey ?? process.env.OMALLA_MASTER_KEY;
    if (configured) {
      const key = Buffer.from(configured, "base64");
      if (key.length !== 32) {
        throw new Error("OMALLA_MASTER_KEY must be 32 bytes, base64 encoded");
      }
      return new SecretBox(key);
    }

    await mkdir(options.dir, { recursive: true });
    const keyPath = path.join(options.dir, "master.key");
    try {
      const existing = await readFile(keyPath);
      if (existing.length === 32) return new SecretBox(existing);
    } catch {
      // fall through and generate
    }
    const key = randomBytes(32);
    await writeFile(keyPath, key, { mode: 0o600 });
    try {
      await chmod(keyPath, 0o600);
    } catch {
      // Windows ACLs are managed by the user profile; best effort here.
    }
    return new SecretBox(key);
  }

  encrypt(plaintext: string): string {
    const iv = randomBytes(12);
    const cipher = createCipheriv("aes-256-gcm", this.key, iv);
    const ciphertext = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
    const tag = cipher.getAuthTag();
    return ["v1", iv.toString("base64"), tag.toString("base64"), ciphertext.toString("base64")].join(":");
  }

  decrypt(payload: string): string {
    const [version, ivB64, tagB64, dataB64] = payload.split(":");
    if (version !== "v1" || !ivB64 || !tagB64 || !dataB64) {
      throw new Error("unsupported secret envelope");
    }
    const decipher = createDecipheriv("aes-256-gcm", this.key, Buffer.from(ivB64, "base64"));
    decipher.setAuthTag(Buffer.from(tagB64, "base64"));
    return Buffer.concat([
      decipher.update(Buffer.from(dataB64, "base64")),
      decipher.final(),
    ]).toString("utf8");
  }
}

export function hashToken(token: string): string {
  return createHash("sha256").update(token, "utf8").digest("hex");
}

export function constantTimeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  if (left.length !== right.length) return false;
  return timingSafeEqual(left, right);
}

export function maskSecret(value: string, visible = 4): string {
  if (value.length <= visible) return "*".repeat(value.length);
  return `${"*".repeat(Math.min(value.length - visible, 12))}${value.slice(-visible)}`;
}
