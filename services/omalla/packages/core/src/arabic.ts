/**
 * Arabic & dialectal speech normalization utilities (MSA, Gulf/ar-SA,
 * Egyptian/ar-EG, Levantine/ar-LB, and Arabic-English code-switching).
 */

export const SUPPORTED_ARABIC_LOCALES = [
  "ar",
  "ar-SA",
  "ar-EG",
  "ar-LB",
  "ar-AE",
  "ar-JO",
  "ar-MA",
  "ar-QA",
  "ar-KW",
] as const;

export const DEFAULT_ARABIC_END_CALL_PHRASES = [
  "مع السلامة",
  "انهي المكالمة",
  "أنهي المكالمة",
  "إغلاق المكالمة",
  "شكرا مع السلامة",
  "باي",
] as const;

const ARABIC_DIACRITICS = /[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g;
const TATWEEL = /\u0640/g;
const ARABIC_SCRIPT = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]/;

/** Converts Eastern Arabic-Indic (٠-٩) and Extended Arabic-Indic (۰-۹) digits to ASCII 0-9. */
export function normalizeArabicDigits(input: string): string {
  let out = "";
  for (let i = 0; i < input.length; i += 1) {
    const code = input.charCodeAt(i);
    if (code >= 0x0660 && code <= 0x0669) {
      out += String(code - 0x0660);
    } else if (code >= 0x06f0 && code <= 0x06f9) {
      out += String(code - 0x06f0);
    } else {
      out += input[i];
    }
  }
  return out;
}

/**
 * Normalizes Arabic text for transcript comparison, phrase detection, and
 * lexical retrieval while preserving English tokens in code-switched speech.
 */
export function normalizeArabicText(
  input: string,
  options: { foldTehMarbuta?: boolean } = {},
): string {
  const foldTeh = options.foldTehMarbuta ?? true;
  let normalized = normalizeArabicDigits(input.normalize("NFKC"))
    .replace(ARABIC_DIACRITICS, "")
    .replace(TATWEEL, "")
    // Alef variants: أ إ آ ٱ -> ا
    .replace(/[\u0622\u0623\u0625\u0671]/g, "\u0627")
    // Alef Maqsura: ى -> ي
    .replace(/\u0649/g, "\u064A")
    // Hamza on Waw / Yeh: ؤ -> و, ئ -> ي
    .replace(/\u0624/g, "\u0648")
    .replace(/\u0626/g, "\u064A");

  if (foldTeh) {
    // Teh Marbuta: ة -> ه for spoken/written equivalence ("المكالمة" == "المكالمه")
    normalized = normalized.replace(/\u0629/g, "\u0647");
  }
  return normalized.replace(/\s+/g, " ").trim();
}

export function containsArabic(input: string): boolean {
  return ARABIC_SCRIPT.test(input);
}

export function isArabicLocale(language: string | undefined): boolean {
  if (!language) return false;
  const lower = language.trim().toLowerCase();
  return lower === "ar" || lower.startsWith("ar-") || lower.startsWith("ar_");
}

/**
 * Normalizes an utterance (English, Arabic, or code-switched) for deterministic
 * end-call phrase and intent matching.
 */
export function normalizeForPhraseMatch(input: string): string {
  return normalizeArabicText(input, { foldTehMarbuta: true })
    .toLowerCase()
    .replace(/[.,!?؟،؛:"'()[\]{}\-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function matchesEndCallPhrase(utterance: string, configuredPhrases: readonly string[]): boolean {
  const cleanUtterance = normalizeForPhraseMatch(utterance);
  if (!cleanUtterance) return false;

  for (const rawPhrase of configuredPhrases) {
    const phrase = normalizeForPhraseMatch(rawPhrase);
    if (!phrase) continue;
    if (cleanUtterance === phrase) return true;
    // Match whole phrase boundaries within short closing utterances
    const padded = ` ${cleanUtterance} `;
    if (cleanUtterance.split(" ").length <= 8 && padded.includes(` ${phrase} `)) {
      return true;
    }
  }
  return false;
}
