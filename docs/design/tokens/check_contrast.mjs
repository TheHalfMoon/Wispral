#!/usr/bin/env node
// Checks WCAG 2.2 contrast for the semantic token pairs declared in wispral.tokens.json.
// Usage: node docs/design/tokens/check_contrast.mjs [path-to-tokens.json]
// Exit code 0 = every pair passes in light and dark; 1 = at least one failure.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const tokens = JSON.parse(readFileSync(process.argv[2] ?? join(here, "wispral.tokens.json"), "utf8"));

function resolve(ref) {
  const m = /^\{(.+)\}$/.exec(ref);
  if (!m) throw new Error(`not a reference: ${ref}`);
  let node = tokens;
  for (const part of m[1].split(".")) {
    node = node?.[part];
    if (node === undefined) throw new Error(`unresolved reference: ${ref}`);
  }
  if (typeof node.$value !== "string" || !/^#[0-9A-Fa-f]{6}$/.test(node.$value)) throw new Error(`not a hex color: ${ref}`);
  return node.$value;
}

function luminance(hex) {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const lin = c.map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

function ratio(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const required = { text: 4.5, ui: 3.0 };
const results = [];
let failures = 0;
for (const theme of ["light", "dark"]) {
  const sem = tokens.semantic[theme];
  for (const [fg, bg, kind] of tokens.contrastRequirements.pairs) {
    if (!(fg in sem) || !(bg in sem)) throw new Error(`missing semantic token in ${theme}: ${fg} or ${bg}`);
    const r = ratio(resolve(sem[fg]), resolve(sem[bg]));
    const pass = r >= required[kind];
    if (!pass) failures += 1;
    results.push({ theme, fg, bg, kind, ratio: Number(r.toFixed(2)), required: required[kind], pass });
  }
}

function hue(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
  if (d === 0) return null;
  let h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return (h * 60 + 360) % 360;
}
const hueResults = [];
if (tokens.hueSeparation) {
  const { minDegrees, accents, states } = tokens.hueSeparation;
  for (const theme of ["light", "dark"]) {
    const sem = tokens.semantic[theme];
    for (const a of accents) for (const st of states) {
      const ha = hue(resolve(sem[a])), hs = hue(resolve(sem[st]));
      if (ha === null || hs === null) continue;
      const dist = Math.min(Math.abs(ha - hs), 360 - Math.abs(ha - hs));
      const pass = dist >= minDegrees;
      if (!pass) failures += 1;
      hueResults.push({ theme, accent: a, state: st, degrees: Math.round(dist), pass });
    }
  }
}

console.log(JSON.stringify({ status: failures === 0 ? "PASS" : "FAIL", checked: results.length, hue_checks: hueResults.length, failures, results, hueResults }, null, 1));
process.exit(failures === 0 ? 0 : 1);
