/** Minimal argument parser: no dependency, predictable behaviour. */
export interface ParsedArgs {
  /** Positional words after the command, e.g. `["calls", "list"]`. */
  words: string[];
  flags: Map<string, string | boolean>;
}

export function parseArgs(argv: string[]): ParsedArgs {
  const words: string[] = [];
  const flags = new Map<string, string | boolean>();

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === undefined) continue;
    if (token === "--") {
      words.push(...argv.slice(index + 1));
      break;
    }
    if (token.startsWith("--")) {
      const equals = token.indexOf("=");
      if (equals > 2) {
        flags.set(token.slice(2, equals), token.slice(equals + 1));
        continue;
      }
      const name = token.slice(2);
      const next = argv[index + 1];
      if (next !== undefined && !next.startsWith("-")) {
        flags.set(name, next);
        index += 1;
      } else {
        flags.set(name, true);
      }
      continue;
    }
    if (token.startsWith("-") && token.length > 1) {
      const name = token.slice(1);
      const next = argv[index + 1];
      if (next !== undefined && !next.startsWith("-")) {
        flags.set(name, next);
        index += 1;
      } else {
        flags.set(name, true);
      }
      continue;
    }
    words.push(token);
  }
  return { words, flags };
}

export function flagString(args: ParsedArgs, ...names: string[]): string | undefined {
  for (const name of names) {
    const value = args.flags.get(name);
    if (typeof value === "string") return value;
  }
  return undefined;
}

export function flagBool(args: ParsedArgs, ...names: string[]): boolean {
  return names.some((name) => args.flags.get(name) === true || args.flags.get(name) === "true");
}

export function flagList(args: ParsedArgs, ...names: string[]): string[] {
  const values: string[] = [];
  for (const name of names) {
    const value = args.flags.get(name);
    if (typeof value === "string") values.push(value);
    else if (value === true) values.push("");
  }
  return values.filter(Boolean);
}

export function requireFlag(args: ParsedArgs, name: string): string {
  const value = flagString(args, name);
  if (!value) throw new UsageError(`missing --${name}`);
  return value;
}

export class UsageError extends Error {}
