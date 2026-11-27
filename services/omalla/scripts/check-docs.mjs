/**
 * Documentation gate: every required document exists, is non-trivial, and
 * every relative markdown link in the README resolves.
 */
import { readFileSync, statSync } from "node:fs";
import path from "node:path";

const REQUIRED = [
  "README.md",
  "docs/MASTER_PLAN.md",
  "docs/ARCHITECTURE.md",
  "docs/REA_VAPI.md",
  "docs/REA_TELEPHONY.md",
  "docs/REA_AUTOMATION.md",
  "docs/COMPETITIVE_MATRIX.md",
  "docs/SOURCE_INVENTORY.md",
  "docs/DONOR_TRANSPLANT_MAP.md",
  "docs/SECURITY_MODEL.md",
  "docs/AUTOMATION_EXPANSION.md",
  "docs/IMPLEMENTATION_LEDGER.md",
  "docs/TEST_MATRIX.md",
  "docs/RELEASE_CHECKLIST.md",
];

let failed = false;
for (const relative of REQUIRED) {
  try {
    const stats = statSync(relative);
    if (stats.size < 400) {
      console.error(`${relative} is suspiciously short (${stats.size} bytes)`);
      failed = true;
    }
  } catch {
    console.error(`missing required document: ${relative}`);
    failed = true;
  }
}

const files = ["README.md", ...REQUIRED.filter((file) => file !== "README.md")];
for (const file of files) {
  const text = readFileSync(file, "utf8");
  const links = [...text.matchAll(/\]\(([^)#]+\.md)(?:#[^)]*)?\)/g)].map((match) => match[1]);
  for (const link of links) {
    if (/^https?:/.test(link)) continue;
    const target = path.resolve(path.dirname(file), link);
    try {
      statSync(target);
    } catch {
      console.error(`${file} links to missing ${link}`);
      failed = true;
    }
  }
}

if (failed) process.exit(1);
console.log(`documentation gate: ${REQUIRED.length} required files present, links resolve`);
