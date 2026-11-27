/**
 * Streaming sentence chunker.
 *
 * TTS is requested per sentence so the caller hears the first clause while
 * the model is still generating the rest. The hard character cap bounds
 * latency for models that produce long unpunctuated runs.
 */
export class SentenceChunker {
  private buffer = "";
  private readonly terminators = new Set([".", "!", "?", "؟", "۔", ";", "\n"]);
  private readonly abbreviations = new Set([
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e", "no", "inc", "ltd", "co",
  ]);

  constructor(private readonly maxChars = 220) {}

  push(text: string): string[] {
    this.buffer += text;
    const out: string[] = [];
    let boundary = this.findBoundary();
    while (boundary >= 0) {
      const sentence = this.buffer.slice(0, boundary + 1).trim();
      this.buffer = this.buffer.slice(boundary + 1);
      if (sentence) out.push(sentence);
      boundary = this.findBoundary();
    }
    if (this.buffer.length >= this.maxChars) {
      const cut = this.softCut(this.buffer);
      const piece = this.buffer.slice(0, cut).trim();
      this.buffer = this.buffer.slice(cut);
      if (piece) out.push(piece);
    }
    return out;
  }

  flush(): string[] {
    const rest = this.buffer.trim();
    this.buffer = "";
    return rest ? [rest] : [];
  }

  get pending(): string {
    return this.buffer;
  }

  private findBoundary(): number {
    for (let i = 0; i < this.buffer.length; i += 1) {
      const char = this.buffer[i] ?? "";
      if (!this.terminators.has(char)) continue;
      if (char === "\n") return i;
      const next = this.buffer[i + 1];
      if (next !== undefined && !/\s/.test(next)) continue;
      const word = this.buffer.slice(0, i).split(/\s+/).pop()?.toLowerCase() ?? "";
      if (char === "." && this.abbreviations.has(word.replace(/[^a-z.]/g, ""))) continue;
      if (char === "." && /^[a-z]$/i.test(word) && word.length === 1) continue;
      return i;
    }
    return -1;
  }

  private softCut(text: string): number {
    const window = text.slice(0, this.maxChars);
    const lastSpace = window.lastIndexOf(" ");
    const lastComma = Math.max(window.lastIndexOf(","), window.lastIndexOf("،"));
    const cut = Math.max(lastSpace, lastComma);
    return cut > this.maxChars * 0.4 ? cut + 1 : this.maxChars;
  }
}
