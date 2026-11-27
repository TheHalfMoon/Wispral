import type { JsonValue } from "@omalla/core";

export type Scope = Record<string, unknown>;

/** Dot-path lookup: "trigger.payload.name", "nodes.card.output.id". */
export function getPath(scope: Scope, path: string): unknown {
  const parts = path.split(".").filter(Boolean);
  let current: unknown = scope;
  for (const part of parts) {
    if (current === null || current === undefined) return undefined;
    if (Array.isArray(current)) {
      const index = Number(part);
      current = Number.isInteger(index) ? current[index] : undefined;
      continue;
    }
    if (typeof current !== "object") return undefined;
    current = (current as Record<string, unknown>)[part];
  }
  return current;
}

const EXPRESSION = /\{\{\s*([^}]+?)\s*\}\}/g;

/** True when the whole string is exactly one expression, so types survive. */
function isSingleExpression(template: string): string | undefined {
  const match = template.match(/^\s*\{\{\s*([^}]+?)\s*\}\}\s*$/);
  return match?.[1];
}

export function render(template: string, scope: Scope): JsonValue {
  const single = isSingleExpression(template);
  if (single) {
    const value = resolveReference(single, scope);
    return toJson(value);
  }
  return template.replace(EXPRESSION, (_match, expression: string) => {
    const value = resolveReference(expression, scope);
    if (value === undefined || value === null) return "";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  });
}

export function renderDeep(value: JsonValue, scope: Scope): JsonValue {
  if (typeof value === "string") return render(value, scope);
  if (Array.isArray(value)) return value.map((item) => renderDeep(item, scope));
  if (value && typeof value === "object") {
    const out: Record<string, JsonValue> = {};
    for (const [key, item] of Object.entries(value)) out[key] = renderDeep(item, scope);
    return out;
  }
  return value;
}

/**
 * Reference forms:
 *   trigger.payload.foo
 *   nodes.card.output.id
 *   context.customerName
 *   env.API_BASE (only non-secret configuration)
 *   item(0).name  (index access)
 */
export function resolveReference(reference: string, scope: Scope): unknown {
  const trimmed = reference.trim();
  const fn = trimmed.match(/^([A-Za-z0-9_]+)\((\d+)\)(?:\.(.+))?$/);
  if (fn) {
    const collection = getPath(scope, fn[1] ?? "");
    if (!Array.isArray(collection)) return undefined;
    const item = collection[Number(fn[2])];
    return fn[3] ? getPath({ item }, `item.${fn[3]}`) : item;
  }
  const value = getPath(scope, trimmed);
  if (value !== undefined) return value;
  // Workflow payloads are commonly referenced as `trigger.field` even though
  // the run stores them under `trigger.payload`. Support both spellings.
  if (trimmed.startsWith("trigger.")) {
    return getPath(scope, `trigger.payload.${trimmed.slice("trigger.".length)}`);
  }
  return undefined;
}

export function evaluateCondition(raw: string, scope: Scope): boolean {
  const text = raw.trim();
  if (!text) return true;

  const exists = text.match(/^exists\(\s*([^)]+?)\s*\)$/);
  if (exists?.[1]) {
    const value = resolveReference(exists[1], scope);
    return value !== undefined && value !== null && value !== "";
  }

  const existsCompared = text.match(/^exists\(\s*([^)]+?)\s*\)\s*==\s*(true|false)$/i);
  if (existsCompared?.[1]) {
    const value = resolveReference(existsCompared[1], scope);
    const present = value !== undefined && value !== null && value !== "";
    return present === (existsCompared[2]?.toLowerCase() === "true");
  }

  const operator = findOperator(text);
  if (operator) {
    const left = render(text.slice(0, operator.index), scope);
    const right = render(text.slice(operator.index + operator.token.length), scope);
    return compare(left, right, operator.token);
  }

  const value = render(text, scope);
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") return !["", "false", "0", "null", "undefined", "no"].includes(value.toLowerCase());
  return Boolean(value);
}

function findOperator(text: string): { token: string; index: number } | undefined {
  const quoted = /"[^"]*"|'[^']*'/g;
  const masked = text.replace(quoted, (match) => " ".repeat(match.length));
  for (const token of [" contains ", " startsWith ", " endsWith ", ">=", "<=", "!=", "==", ">", "<"]) {
    const index = masked.indexOf(token);
    if (index >= 0) return { token: token.trim(), index };
  }
  return undefined;
}

function compare(left: JsonValue, right: JsonValue, operator: string): boolean {
  const numeric = Number(left);
  const numericRight = Number(right);
  const bothNumeric =
    left !== "" && right !== "" && Number.isFinite(numeric) && Number.isFinite(numericRight);

  switch (operator) {
    case "==":
      return String(left) === String(right);
    case "!=":
      return String(left) !== String(right);
    case ">":
      return bothNumeric ? numeric > numericRight : String(left) > String(right);
    case "<":
      return bothNumeric ? numeric < numericRight : String(left) < String(right);
    case ">=":
      return bothNumeric ? numeric >= numericRight : String(left) >= String(right);
    case "<=":
      return bothNumeric ? numeric <= numericRight : String(left) <= String(right);
    case "contains":
      return String(left).toLowerCase().includes(String(right).toLowerCase());
    case "startsWith":
      return String(left).toLowerCase().startsWith(String(right).toLowerCase());
    case "endsWith":
      return String(left).toLowerCase().endsWith(String(right).toLowerCase());
    default:
      return false;
  }
}

function toJson(value: unknown): JsonValue {
  if (value === undefined) return null;
  if (value === null) return null;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return value;
  try {
    return JSON.parse(JSON.stringify(value)) as JsonValue;
  } catch {
    return String(value);
  }
}
