import { redact } from "./redact.js";

export type LogLevel = "debug" | "info" | "warn" | "error";

const LEVELS: Record<LogLevel, number> = { debug: 10, info: 20, warn: 30, error: 40 };

export interface Logger {
  debug(message: string, context?: Record<string, unknown>): void;
  info(message: string, context?: Record<string, unknown>): void;
  warn(message: string, context?: Record<string, unknown>): void;
  error(message: string, context?: Record<string, unknown>): void;
  child(bindings: Record<string, unknown>): Logger;
}

export interface LoggerOptions {
  level?: LogLevel;
  bindings?: Record<string, unknown>;
  sink?: (line: string) => void;
  pretty?: boolean;
}

export function createLogger(options: LoggerOptions = {}): Logger {
  const level = options.level ?? (process.env.OMALLA_LOG_LEVEL as LogLevel) ?? "info";
  const threshold = LEVELS[level] ?? LEVELS.info;
  const bindings = options.bindings ?? {};
  const sink = options.sink ?? ((line: string) => process.stdout.write(`${line}\n`));
  const pretty = options.pretty ?? process.stdout.isTTY === true;

  const write = (entryLevel: LogLevel, message: string, context?: Record<string, unknown>) => {
    if (LEVELS[entryLevel] < threshold) return;
    const record = {
      ts: new Date().toISOString(),
      level: entryLevel,
      msg: message,
      ...(redact({ ...bindings, ...context }) as Record<string, unknown>),
    };
    if (pretty) {
      const { ts: _ts, level: _level, msg, ...rest } = record;
      const tail = Object.keys(rest).length > 0 ? ` ${JSON.stringify(rest)}` : "";
      sink(`${entryLevel.toUpperCase().padEnd(5)} ${message}${tail}`);
    } else {
      sink(JSON.stringify(record));
    }
  };

  return {
    debug: (message, context) => write("debug", message, context),
    info: (message, context) => write("info", message, context),
    warn: (message, context) => write("warn", message, context),
    error: (message, context) => write("error", message, context),
    child: (extra) => createLogger({ level, bindings: { ...bindings, ...extra }, sink, pretty }),
  };
}

export const silentLogger: Logger = {
  debug: () => {},
  info: () => {},
  warn: () => {},
  error: () => {},
  child: () => silentLogger,
};
