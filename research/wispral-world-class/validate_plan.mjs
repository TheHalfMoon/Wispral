#!/usr/bin/env node
// Wispral World-Class plan validator (stdlib only, no network).
// Usage (from repository root): node research/wispral-world-class/validate_plan.mjs
// Checks: packet schema and dependency graph, BUILD_NEW justifications, first-ten ordering,
// relative links and heading anchors across the planning package, superseded product names,
// and unqualified comparative claims. Scope: planning-package integrity only. It is not a
// product, security, benchmark or release approval.
import { readFileSync, existsSync, statSync } from "node:fs";
import { dirname, join, resolve, relative } from "node:path";

const ROOT = process.cwd();
const failures = [];
const warnings = [];
const fail = (msg) => failures.push(msg);
const warn = (msg) => warnings.push(msg);

// ---------- 1. Packets ----------
const packetsPath = "research/wispral-world-class/packets.json";
const data = JSON.parse(readFileSync(packetsPath, "utf8"));
const DECISIONS = new Set(["GOVERNANCE", "RESEARCH", "FORK", "FORK_DELTA", "COPY", "ADAPT", "WRAP", "API_INTEGRATION", "OUT_OF_PROCESS", "BUILD_NEW"]);
const REQUIRED = ["id", "phase", "product", "subsystem", "title", "depends_on", "decision", "affected", "acceptance", "tests", "ci_gates", "security_risks", "rollback", "readiness_authority", "definition_of_done", "status", "ready"];
const phases = new Set(data.phases.map((p) => p.id));
const authorities = new Set(Object.keys(data.authorities));
const ids = new Map();

for (const p of data.packets) {
  for (const f of REQUIRED) {
    const v = p[f];
    if (v === undefined || v === null || (typeof v === "string" && v.trim() === "") || (Array.isArray(v) && v.length === 0 && f !== "depends_on")) fail(`${p.id ?? "?"}: missing or empty field '${f}'`);
  }
  if (ids.has(p.id)) fail(`duplicate packet id ${p.id}`);
  ids.set(p.id, p);
  if (!phases.has(p.phase)) fail(`${p.id}: unknown phase ${p.phase}`);
  if (!DECISIONS.has(p.decision)) fail(`${p.id}: unknown decision ${p.decision}`);
  if (!authorities.has(p.readiness_authority)) fail(`${p.id}: unknown readiness authority ${p.readiness_authority}`);
  if (p.ready !== false) fail(`${p.id}: ready must be false — no packet has readiness authority in this candidate plan`);
  if (p.donor) {
    for (const d of [].concat(p.donor)) {
      if (!/^[0-9a-f]{40}$/.test(d.sha ?? "")) fail(`${p.id}: donor ${d.repo} lacks a 40-hex commit SHA`);
      if (!Array.isArray(d.paths) || d.paths.length === 0) fail(`${p.id}: donor ${d.repo} lists no source paths`);
    }
  } else if (["FORK", "FORK_DELTA", "COPY", "ADAPT", "WRAP"].includes(p.decision)) {
    fail(`${p.id}: decision ${p.decision} requires a pinned donor`);
  }
  if (p.decision === "BUILD_NEW") {
    const j = p.build_new_justification ?? {};
    for (const k of ["inspected", "why_insufficient", "smallest_missing_capability", "adapter_confinement", "test_and_maintenance_cost"]) {
      if (!j[k] || String(j[k]).trim().length < 10) fail(`${p.id}: BUILD_NEW justification missing '${k}'`);
    }
  }
}
for (const p of data.packets) for (const d of p.depends_on) if (!ids.has(d)) fail(`${p.id}: depends on unknown packet ${d}`);

// Cycle detection + topological order (Kahn).
const indeg = new Map([...ids.keys()].map((k) => [k, 0]));
for (const p of data.packets) for (const d of p.depends_on) if (ids.has(d)) indeg.set(p.id, indeg.get(p.id) + 1);
const queue = [...indeg].filter(([, v]) => v === 0).map(([k]) => k);
const order = [];
while (queue.length) {
  const n = queue.shift();
  order.push(n);
  for (const p of data.packets) if (p.depends_on.includes(n)) { indeg.set(p.id, indeg.get(p.id) - 1); if (indeg.get(p.id) === 0) queue.push(p.id); }
}
if (order.length !== ids.size) fail(`dependency cycle among: ${[...ids.keys()].filter((k) => !order.includes(k)).join(", ")}`);

// Authority reachability: every GRAIN_* packet must depend (transitively) on D0G; every RESEARCH_000E/F packet on F.
function reaches(id, target, seen = new Set()) {
  if (id === target) return true;
  if (seen.has(id) || !ids.has(id)) return false;
  seen.add(id);
  return ids.get(id).depends_on.some((d) => reaches(d, target, seen));
}
for (const p of data.packets) {
  if (p.readiness_authority.startsWith("GRAIN_") && !reaches(p.id, "D0G")) fail(`${p.id}: ${p.readiness_authority} packet has no dependency path to D0G`);
  if (p.readiness_authority.startsWith("RESEARCH_000") && !reaches(p.id, "F")) fail(`${p.id}: research Grain packet has no dependency path to F`);
}

// Tier-to-phase consistency.
const TIER_PHASES = { M: ["P2", "P3", "P5", "P6"], S: ["P4", "P7"], L: ["P7", "P8"] };
for (const p of data.packets) {
  if (p.tier && !TIER_PHASES[p.tier]?.includes(p.phase)) fail(`${p.id}: tier ${p.tier} does not belong in phase ${p.phase}`);
}

// BUILD_NEW packets must cite a row of the build-new register; product packets never allow preserved red checks.
const register = readFileSync("docs/strategy/WISPRAL_COPY_FIRST_STRATEGY.md", "utf8");
for (const p of data.packets) {
  if (p.decision === "BUILD_NEW") {
    const rid = p.build_new_register_id;
    if (!rid) fail(`${p.id}: BUILD_NEW packet lacks build_new_register_id`);
    else if (!new RegExp(`^\\| ${rid.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")} \\|`, "m").test(register)) fail(`${p.id}: register row ${rid} missing from WISPRAL_COPY_FIRST_STRATEGY.md`);
  }
  if (p.decision !== "GOVERNANCE" && p.readiness_authority !== "B2_RECOVERY_V2" && !p.ci_gates.some((g) => /no preserved red checks/i.test(g))) fail(`${p.id}: product packet must require all checks green with no preserved red checks`);
}

// First-ten list must exist, be unique, and respect dependencies among themselves and on governance.
const firstTen = data.first_ten ?? [];
if (firstTen.length !== 10) fail(`first_ten must list exactly 10 packets (has ${firstTen.length})`);
firstTen.forEach((id, i) => {
  if (!ids.has(id)) return fail(`first_ten: unknown packet ${id}`);
  for (const d of ids.get(id).depends_on) {
    const j = firstTen.indexOf(d);
    if (j === -1) fail(`first_ten: ${id} depends on ${d}, which is not earlier in the first ten`);
    else if (j > i) fail(`first_ten: ${id} appears before its dependency ${d}`);
  }
});

// ---------- 2. Markdown links and anchors ----------
const docs = data.validated_documents;
const slug = (h) => h.trim().toLowerCase().replace(/[`*_~]/g, "").replace(/<[^>]+>/g, "").replace(/[^\p{L}\p{N}\s-]/gu, "").replace(/\s/g, "-");
const anchorCache = new Map();
function anchorsOf(file) {
  if (anchorCache.has(file)) return anchorCache.get(file);
  const set = new Set();
  const counts = new Map();
  let inFence = false;
  for (const line of readFileSync(file, "utf8").split(/\r?\n/)) {
    if (/^```/.test(line)) inFence = !inFence;
    if (inFence) continue;
    const m = /^#{1,6}\s+(.+?)\s*#*\s*$/.exec(line);
    if (!m) continue;
    const base = slug(m[1]);
    const n = counts.get(base) ?? 0;
    set.add(n === 0 ? base : `${base}-${n}`);
    counts.set(base, n + 1);
  }
  anchorCache.set(file, set);
  return set;
}
let linksChecked = 0;
for (const doc of docs) {
  if (!existsSync(doc)) { fail(`validated document missing: ${doc}`); continue; }
  const text = readFileSync(doc, "utf8").replace(/```[\s\S]*?```/g, "");
  for (const m of text.matchAll(/\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g)) {
    const target = m[1];
    if (/^(https?:|mailto:)/.test(target)) continue;
    linksChecked += 1;
    const [pathPart, anchor] = target.split("#");
    const resolved = pathPart === "" ? doc : join(dirname(doc), decodeURIComponent(pathPart));
    if (!existsSync(resolved)) { fail(`${doc}: broken link → ${target}`); continue; }
    if (anchor && statSync(resolved).isFile() && resolved.endsWith(".md")) {
      if (!anchorsOf(resolved).has(anchor)) fail(`${doc}: missing anchor #${anchor} in ${relative(ROOT, resolve(resolved))}`);
    }
  }
}

// ---------- 3. Names and claims ----------
const superseded = /\b(WisprInk|Wispral Studio|WisperType|WisperOne|Wispral Ink|Wispral Flow|Wispral Agents|Wispivo)\b/;
const claimWords = /\b(better than|faster than|outperform\w*|superior to|best-in-class|industry[- ]leading|world'?s best)\b/i;
const qualifier = /\b(not|no|never|until|unless|hypothes\w*|target|claim gate|must not|do not|without|before any|require\w*|measured|measurable)\b/i;
let claimHits = 0;
for (const doc of docs) {
  if (!existsSync(doc)) continue;
  readFileSync(doc, "utf8").split(/\r?\n/).forEach((line, i) => {
    if (superseded.test(line) && !/historic|supersed|retired|obsolete|old name/i.test(line)) fail(`${doc}:${i + 1}: superseded product name without historical marker`);
    if (claimWords.test(line)) {
      claimHits += 1;
      if (!qualifier.test(line)) fail(`${doc}:${i + 1}: unqualified comparative claim: ${line.trim().slice(0, 120)}`);
    }
  });
}

const status = failures.length === 0 ? "PASS" : "FAIL";
console.log(JSON.stringify({
  status,
  scope: "Planning-package integrity only: packet schema/graph, BUILD_NEW justifications, first-ten ordering, relative links and anchors, superseded names, unqualified comparative claims. Not a product, security, benchmark or release approval.",
  packets: ids.size,
  topological_order: order,
  first_ten: firstTen,
  documents: docs.length,
  links_checked: linksChecked,
  comparative_phrases_reviewed: claimHits,
  failures,
  warnings,
}, null, 1));
process.exit(failures.length === 0 ? 0 : 1);
