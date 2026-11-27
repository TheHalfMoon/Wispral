# SPDX-License-Identifier: Apache-2.0
"""Arabic 4-level match-key normalization (`wispral-arabic`-compatible) and variety detection."""

from __future__ import annotations

import re
import unicodedata

# Zero-width & directional formatting marks
_FORMAT_MARKS_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]")
# Tatweel (kashida) + Arabic harakat / Quranic annotation marks
_TATWEEL_HARAKAT_RE = re.compile(r"[\u0640\u064b-\u065f\u0670\u06d6-\u06ed]")
# Alef variants -> bare Alef (\u0627)
_ALEF_VARIANTS_TABLE = str.maketrans(
    {
        "\u0622": "\u0627",  # آ -> ا
        "\u0623": "\u0627",  # أ -> ا
        "\u0625": "\u0627",  # إ -> ا
        "\u0671": "\u0627",  # ٱ -> ا
    }
)
# Level-3 orthographic folding (Teh Marbuta -> Heh, Alef Maqsura -> Yeh, Farsi Yeh/Kaf)
_LEVEL3_FOLD_TABLE = str.maketrans(
    {
        "\u0629": "\u0647",  # ة -> ه
        "\u0649": "\u064a",  # ى -> ي
        "\u06cc": "\u064a",  # ی -> ي
        "\u06a9": "\u0643",  # ک -> ك
    }
)
# Eastern Arabic-Indic (٠-٩) and Extended Arabic-Indic (۰-۹) digits -> ASCII 0-9
_ARABIC_DIGITS_TABLE = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)
_PUNCT_RE = re.compile(r"[^\w\s\u0600-\u06ff]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+")
_ARABIC_LETTER_RE = re.compile(r"[\u0621-\u064a\u0671-\u06d3]")
_TECH_ID_RE = re.compile(r"\b(?:ord|bkg|shp|acc|ses|tkt|rcp|cap|doc|cust|apr)-[A-Za-z0-9_-]+\b", re.IGNORECASE)
_LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")

_GULF_MARKERS = {
    "وش",
    "ابي",
    "ابغى",
    "يبغى",
    "الطلبيه",
    "ريال",
    "الحين",
    "تبي",
    "شالسالفه",
    "طال عمرك",
    "حيل",
    "ماقصر",
    "فلوسي",
}
_EGYPTIAN_MARKERS = {
    "عايز",
    "عاوز",
    "ازاي",
    "بتاعي",
    "بتاعتي",
    "دلوقتي",
    "ليه",
    "كده",
    "فين",
    "معلش",
    "حضرتك",
    "اوردر",
}
_LEVANTINE_MARKERS = {
    "بدي",
    "هلق",
    "ليش",
    "شو",
    "كيفك",
    "مصاري",
    "لسا",
    "هاد",
    "هاي",
    "منيح",
    "كتير",
}


def normalize_digits(text: str) -> str:
    """Convert Arabic-Indic and Extended Arabic-Indic digits to Western ASCII digits."""
    return text.translate(_ARABIC_DIGITS_TABLE)


def normalize_arabic(text: str, level: int = 3) -> str:
    """Apply `wispral-arabic` 4-level normalization (`level` in `0..3`).

    - Level 0: NFC normalization, strip invisible directional marks, normalize whitespace.
    - Level 1: Strip tatweel (`ـ`) and harakat/diacritics, normalize Eastern digits to `0-9`.
    - Level 2: Fold Alef variants (`أ`, `إ`, `آ`, `ٱ` -> `ا`).
    - Level 3: Fold Teh Marbuta (`ة` -> `ه`), Alef Maqsura (`ى` -> `ي`), Farsi variants, lowercase Latin, strip punctuation.
    """
    if level not in (0, 1, 2, 3):
        raise ValueError(f"Unsupported Arabic normalization level {level}; expected 0..3")

    out = unicodedata.normalize("NFC", text)
    out = _FORMAT_MARKS_RE.sub("", out)

    if level >= 1:
        out = _TATWEEL_HARAKAT_RE.sub("", out)
        out = out.translate(_ARABIC_DIGITS_TABLE)

    if level >= 2:
        out = out.translate(_ALEF_VARIANTS_TABLE)

    if level >= 3:
        out = out.translate(_LEVEL3_FOLD_TABLE)
        out = out.lower()
        out = _PUNCT_RE.sub(" ", out)

    return _WHITESPACE_RE.sub(" ", out).strip()


def contains_arabic(text: str) -> bool:
    """Return True if `text` contains Arabic script letters."""
    return bool(_ARABIC_LETTER_RE.search(text))


def detect_language_variety(text: str) -> str:
    """Classify utterance language/variety: `en`, `ar-MSA`, `ar-Gulf`, `ar-EG`, `ar-Levantine`, or `ar-en-codeswitch`."""
    has_ar = contains_arabic(text)
    if not has_ar:
        return "en"

    prose_without_ids = _TECH_ID_RE.sub(" ", text)
    latin_words = _LATIN_WORD_RE.findall(prose_without_ids)
    norm = normalize_arabic(prose_without_ids, level=3)
    tokens = set(norm.split())

    if len(latin_words) >= 2:
        return "ar-en-codeswitch"

    eg_hits = sum(1 for m in _EGYPTIAN_MARKERS if m in tokens or (" " in m and m in norm))
    lv_hits = sum(1 for m in _LEVANTINE_MARKERS if m in tokens or (" " in m and m in norm))
    gulf_hits = sum(1 for m in _GULF_MARKERS if m in tokens or (" " in m and m in norm))

    best = max((eg_hits, "ar-EG"), (lv_hits, "ar-Levantine"), (gulf_hits, "ar-Gulf"), key=lambda pair: pair[0])
    if best[0] > 0:
        return best[1]
    return "ar-MSA"
