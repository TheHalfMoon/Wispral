export type ErrorCode =
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "validation"
  | "rate_limited"
  | "provider_error"
  | "timeout"
  | "blocked_by_policy"
  | "internal";

export class OmallaError extends Error {
  readonly code: ErrorCode;
  readonly status: number;
  readonly detail?: unknown;

  constructor(code: ErrorCode, message: string, status?: number, detail?: unknown) {
    super(message);
    this.name = "OmallaError";
    this.code = code;
    this.status = status ?? defaultStatus(code);
    this.detail = detail;
  }
}

function defaultStatus(code: ErrorCode): number {
  switch (code) {
    case "unauthorized":
      return 401;
    case "forbidden":
      return 403;
    case "not_found":
      return 404;
    case "conflict":
      return 409;
    case "validation":
      return 400;
    case "rate_limited":
      return 429;
    case "blocked_by_policy":
      return 403;
    case "timeout":
      return 504;
    case "provider_error":
      return 502;
    default:
      return 500;
  }
}

export function isOmallaError(error: unknown): error is OmallaError {
  return error instanceof OmallaError;
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return String(error);
}
