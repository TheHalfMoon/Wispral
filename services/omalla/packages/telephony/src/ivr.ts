import type { IvrMenu, IvrOption } from "@omalla/core";

export type IvrAction = IvrOption["action"];

export type IvrStep =
  | { kind: "prompt"; text: string; attemptsLeft: number }
  | { kind: "action"; action: IvrAction; target?: string };

/**
 * Deterministic IVR state machine.
 *
 * Kept pure and transport-independent so the same menu runs over a simulated
 * call, a SIP leg, or a WebRTC data channel without change.
 */
export class IvrSession {
  private attempts = 0;
  private finished = false;

  constructor(
    private readonly menu: IvrMenu,
    private readonly speak: (text: string) => Promise<void> = async () => {},
  ) {}

  get done(): boolean {
    return this.finished;
  }

  /** Plays the greeting and returns the prompt that was spoken. */
  async start(): Promise<string> {
    await this.speak(this.menu.prompt);
    return this.menu.prompt;
  }

  /** Feeds a DTMF key or digit string; the first recognised key wins. */
  async feed(input: string): Promise<IvrStep> {
    if (this.finished) {
      return { kind: "action", action: "hangup" };
    }
    const key = input.trim().charAt(0);
    const option = this.menu.options.find((candidate) => candidate.key === key);

    if (!option) {
      this.attempts += 1;
      if (this.attempts >= Math.max(1, this.menu.maxAttempts)) {
        this.finished = true;
        return { kind: "action", action: "hangup" };
      }
      const text = this.menu.invalidPrompt;
      await this.speak(text);
      return { kind: "prompt", text, attemptsLeft: Math.max(0, this.menu.maxAttempts - this.attempts) };
    }

    if (option.action === "repeat") {
      await this.speak(this.menu.prompt);
      return { kind: "prompt", text: this.menu.prompt, attemptsLeft: this.menu.maxAttempts };
    }

    this.finished = true;
    return {
      kind: "action",
      action: option.action,
      ...(option.target ? { target: option.target } : {}),
    };
  }

  /** Silence/timeout path; counts as one failed attempt. */
  async timeout(): Promise<IvrStep> {
    return this.feed("?");
  }
}

export function validateMenu(menu: Pick<IvrMenu, "prompt" | "options" | "maxAttempts">): string[] {
  const problems: string[] = [];
  if (!menu.prompt.trim()) problems.push("menu prompt is empty");
  if (menu.options.length === 0) problems.push("menu has no options");
  if (menu.maxAttempts < 1) problems.push("maxAttempts must be at least 1");
  const seen = new Set<string>();
  for (const option of menu.options) {
    if (!/^[0-9*#]$/.test(option.key)) problems.push(`invalid DTMF key: ${option.key}`);
    if (seen.has(option.key)) problems.push(`duplicate DTMF key: ${option.key}`);
    seen.add(option.key);
    if (option.action === "agent" && !option.target) problems.push(`option ${option.key} targets an agent but has no target`);
    if (option.action === "transfer" && !option.target) problems.push(`option ${option.key} transfers but has no destination`);
  }
  return problems;
}
