/* Plain-text rendering. Everything also has a --json form, which is the
 * stable interface for scripts; the tables are for people. */

export function table(headers: string[], rows: string[][]): string {
  const widths = headers.map((header, column) =>
    Math.max(header.length, ...rows.map((row) => (row[column] ?? "").length)),
  );
  const line = (cells: string[]) =>
    cells.map((cell, column) => cell.padEnd(widths[column] ?? cell.length)).join("  ").trimEnd();
  return [line(headers), widths.map((width) => "─".repeat(width)).join("  "), ...rows.map(line)].join("\n");
}

export function kv(pairs: Array<[string, unknown]>): string {
  const width = Math.max(...pairs.map(([key]) => key.length));
  return pairs
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => `  ${key.padEnd(width)}  ${String(value)}`)
    .join("\n");
}

export function shortId(id: string | undefined): string {
  if (!id) return "—";
  const [, suffix] = id.split("_");
  return suffix ? suffix.slice(0, 8) : id.slice(0, 8);
}

export function clock(iso: string | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString(undefined, {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
}

export function seconds(from: string, to?: string): string {
  const end = to ? Date.parse(to) : Date.now();
  const start = Date.parse(from);
  if (Number.isNaN(start) || Number.isNaN(end)) return "—";
  const total = Math.max(0, Math.round((end - start) / 1000));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

export function truncate(text: string, length: number): string {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > length ? `${clean.slice(0, length - 1)}…` : clean;
}

export function printJson(value: unknown): void {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}
