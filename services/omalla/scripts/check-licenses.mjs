/**
 * Licence gate for runtime dependencies.
 *
 * Reads the installed production tree, collects every package's declared
 * licence, and fails on licences that would constrain an Apache-2.0 release.
 * Unknown licences are reported but do not fail the gate; they need a human
 * decision, not a silent pass.
 */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";

const ALLOWED = new Set([
  "MIT",
  "ISC",
  "BSD-2-Clause",
  "BSD-3-Clause",
  "Apache-2.0",
  "0BSD",
  "Unlicense",
  "CC0-1.0",
  "BlueOak-1.0.0",
]);

const DISALLOWED = new Set([
  "GPL-2.0",
  "GPL-2.0-only",
  "GPL-2.0-or-later",
  "GPL-3.0",
  "GPL-3.0-only",
  "GPL-3.0-or-later",
  "AGPL-3.0",
  "AGPL-3.0-only",
  "AGPL-3.0-or-later",
  "SSPL-1.0",
  "OSL-3.0",
  "CPAL-1.0",
  "EUPL-1.2",
]);

function npmCommand() {
  return process.platform === "win32" ? "cmd.exe" : "npm";
}

function npmArgs(args) {
  return process.platform === "win32" ? ["/d", "/s", "/c", `npm ${args.join(" ")}`] : args;
}

let listing;
try {
  listing = execFileSync(
    npmCommand(),
    npmArgs(["ls", "--all", "--parseable", "--omit=dev"]),
    {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
} catch (error) {
  // npm ls exits non-zero on peer problems but still prints a usable tree.
  listing = String(error.stdout ?? "");
  if (!listing.trim()) {
    console.error("licence gate could not read the dependency tree");
    console.error(String(error.stderr ?? error.message));
    process.exit(1);
  }
}

const roots = listing
  .split(/\r?\n/)
  .map((line) => line.trim())
  .filter((line) => line.includes(`${path.sep}node_modules${path.sep}`));

if (roots.length === 0) {
  console.error("licence gate found no installed packages; run npm install first");
  process.exit(1);
}

const packages = new Map();
for (const dir of roots) {  try {
    const manifest = JSON.parse(readFileSync(path.join(dir, "package.json"), "utf8"));
    if (!manifest.name || !manifest.version) continue;
    const licence =
      typeof manifest.license === "string"
        ? manifest.license
        : manifest.license?.type ?? manifest.licenses?.[0]?.type ?? "UNKNOWN";
    packages.set(`${manifest.name}@${manifest.version}`, {
      licence,
      dir,
    });
  } catch {
    // A broken or partially installed package is not a licence result.
  }
}

const byLicence = new Map();
const disallowed = [];
const unknown = [];
for (const [id, entry] of packages) {
  const key = entry.licence;
  byLicence.set(key, (byLicence.get(key) ?? 0) + 1);
  if (DISALLOWED.has(key)) disallowed.push({ id, licence: key });
  else if (!ALLOWED.has(key) && key !== "UNKNOWN") {
    // Compound expressions such as "(MIT OR Apache-2.0)" are accepted when
    // every alternative is allowed.
    const alternatives = key.replace(/[()]/g, "").split(/\s+OR\s+|\//i).map((part) => part.trim());
    if (!alternatives.every((part) => ALLOWED.has(part))) unknown.push({ id, licence: key });
  } else if (key === "UNKNOWN") {
    unknown.push({ id, licence: key });
  }
}

console.log(`checked ${packages.size} production packages`);
for (const [licence, count] of [...byLicence].sort((a, b) => b[1] - a[1])) {
  console.log(`  ${String(count).padStart(4)}  ${licence}`);
}

if (unknown.length > 0) {
  console.warn(`\n${unknown.length} package(s) need a licence decision:`);
  for (const item of unknown.slice(0, 40)) console.warn(`  ${item.id}  ${item.licence}`);
}

if (disallowed.length > 0) {
  console.error(`\n${disallowed.length} disallowed licence(s) in production dependencies:`);
  for (const item of disallowed) console.error(`  ${item.id}  ${item.licence}`);
  process.exitCode = 1;
} else {
  console.log("\nno disallowed production licences");
}
