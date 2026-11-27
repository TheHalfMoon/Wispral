import type { RetrievalHit, Retriever } from "./provider-contracts.js";
import { normalizeArabicText } from "./arabic.js";

export interface RetrievalDocument {
  id: string;
  title: string;
  text: string;
}

const STOPWORDS = new Set([
  "a", "an", "the", "and", "or", "but", "if", "then", "than", "that", "this", "these", "those",
  "is", "are", "was", "were", "be", "been", "being", "to", "of", "in", "on", "at", "for", "with",
  "by", "from", "as", "it", "its", "i", "you", "we", "they", "he", "she", "do", "does", "did",
  "can", "could", "would", "should", "will", "shall", "may", "might", "have", "has", "had",
  "not", "no", "yes", "what", "which", "who", "whom", "when", "where", "why", "how", "about",
]);

export function tokenize(input: string): string[] {
  return normalizeArabicText(input, { foldTehMarbuta: true })
    .toLowerCase()
    .split(/[^\p{L}\p{N}]+/u)
    .filter((token) => token.length > 1 && !STOPWORDS.has(token));
}

/**
 * Deterministic, dependency-free lexical retriever.
 *
 * A vector store can replace this behind the same interface, but lexical
 * retrieval keeps the zero-cost local mode honest: no embedding service, no
 * model download, and reproducible results in tests.
 */
export function createRetriever(documents: RetrievalDocument[]): Retriever {
  const prepared = documents.map((doc) => {
    const tokens = tokenize(`${doc.title} ${doc.text}`);
    const termFreq = new Map<string, number>();
    for (const token of tokens) termFreq.set(token, (termFreq.get(token) ?? 0) + 1);
    return { doc, tokens, termFreq, length: tokens.length };
  });

  const docFreq = new Map<string, number>();
  for (const entry of prepared) {
    for (const term of entry.termFreq.keys()) {
      docFreq.set(term, (docFreq.get(term) ?? 0) + 1);
    }
  }
  const total = Math.max(prepared.length, 1);
  const avgLength =
    prepared.reduce((sum, entry) => sum + entry.length, 0) / Math.max(prepared.length, 1) || 1;

  const k1 = 1.4;
  const b = 0.75;

  return {
    search(query: string, limit = 4): RetrievalHit[] {
      const terms = tokenize(query);
      if (terms.length === 0) return [];
      const scored = prepared.map((entry) => {
        let score = 0;
        for (const term of terms) {
          const tf = entry.termFreq.get(term) ?? 0;
          if (tf === 0) continue;
          const df = docFreq.get(term) ?? 0;
          const idf = Math.log(1 + (total - df + 0.5) / (df + 0.5));
          const denominator = tf + k1 * (1 - b + (b * entry.length) / avgLength);
          score += idf * ((tf * (k1 + 1)) / denominator);
        }
        return {
          documentId: entry.doc.id,
          title: entry.doc.title,
          text: entry.doc.text,
          score: Number(score.toFixed(4)),
        };
      });
      return scored
        .filter((hit) => hit.score > 0)
        .sort((a, b2) => b2.score - a.score)
        .slice(0, limit);
    },
  };
}
