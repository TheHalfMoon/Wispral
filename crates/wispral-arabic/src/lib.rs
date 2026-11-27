//! Wispral Core Arabic-first and multilingual text intelligence.
//!
//! Enforces strict Rust type separation between four representations so lossy
//! search/lexicon folding (`ة -> ه`, `أ/إ/آ -> ا`, `ى -> ي`, harakat stripping)
//! can NEVER leak into user-visible transcripts, UI display strings, or TTS inputs:
//!
//! - [`VerbatimTranscript`]: NFC-normalized exact spoken/written surface text;
//! - [`BidiIsolatedDisplay`]: RTL/LTR safe display text wrapping embedded Latin/code
//!   runs with Unicode `U+2068` (`FSI`) .. `U+2069` (`PDI`) directional isolates;
//! - [`NormalizedMatchKey`]: 4-level folded search/glossary/RAG match key (never displayable as transcript);
//! - [`DiacritizedTtsInput`]: TTS-ready text preserving harakat/shadda and applying
//!   proclitic-aware pronunciation overrides.

use serde::{Deserialize, Serialize};
use unicode_normalization::UnicodeNormalization;

pub const FSI: char = '\u{2068}';
pub const PDI: char = '\u{2069}';
pub const TATWEEL: char = '\u{0640}';

/// Exact spoken or authored surface text (NFC-normalized, no lossy folding).
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct VerbatimTranscript(String);

impl VerbatimTranscript {
    pub fn new(raw: impl AsRef<str>) -> Self {
        Self(raw.as_ref().nfc().collect())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn into_string(self) -> String {
        self.0
    }

    /// Produces a [`BidiIsolatedDisplay`] wrapping LTR code/identifier/URL spans
    /// inside RTL text with `U+2068 FSI` .. `U+2069 PDI`.
    pub fn to_bidi_isolated(&self) -> BidiIsolatedDisplay {
        BidiIsolatedDisplay(isolate_ltr_in_rtl(&self.0))
    }

    /// Derives a lossy [`NormalizedMatchKey`] for dictionary, glossary, or FTS lookup.
    pub fn to_match_key(&self) -> NormalizedMatchKey {
        NormalizedMatchKey::from_surface(&self.0, NormalizationLevel::FullMatchFold)
    }
}

/// Display-safe text with Unicode directional isolates around embedded LTR spans.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct BidiIsolatedDisplay(String);

impl BidiIsolatedDisplay {
    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn into_string(self) -> String {
        self.0
    }
}

/// Configurable Arabic normalization depth.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NormalizationLevel {
    /// Level 1: Unicode NFC + strip tatweel (`ـ`).
    OrthographicClean,
    /// Level 2: Level 1 + strip tashkeel/harakat (`U+064B..U+065F`, `U+0670`).
    StripDiacritics,
    /// Level 3: Level 2 + fold alef variants (`أ/إ/آ/ٱ -> ا`) + Arabic-Indic digits (`٠-٩/۰-۹ -> 0-9`).
    CanonicalStem,
    /// Level 4: Level 3 + fold teh marbuta (`ة -> ه`), alef maqsura (`ى -> ي`), hamza-on-waw/ya (`ؤ -> و`, `ئ -> ي`), and ASCII lowercase.
    FullMatchFold,
}

/// Search/lexicon match key. Intentionally opaque to transcript/TTS consumers so
/// lossy `ة -> ه` and alef folding never escapes into user-visible text.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct NormalizedMatchKey(String);

impl NormalizedMatchKey {
    pub fn from_surface(input: &str, level: NormalizationLevel) -> Self {
        let mut out = String::with_capacity(input.len());
        let mut prev_space = true;
        for ch in input.nfc() {
            if ch == TATWEEL || ch == FSI || ch == PDI {
                continue;
            }
            if level != NormalizationLevel::OrthographicClean && is_arabic_diacritic(ch) {
                continue;
            }
            let mapped = match level {
                NormalizationLevel::OrthographicClean | NormalizationLevel::StripDiacritics => ch,
                NormalizationLevel::CanonicalStem => fold_alef_and_digits(ch),
                NormalizationLevel::FullMatchFold => {
                    let c = fold_alef_and_digits(ch);
                    match c {
                        '\u{0629}' => '\u{0647}', // ة -> ه
                        '\u{0649}' => '\u{064A}', // ى -> ي
                        '\u{0624}' => '\u{0648}', // ؤ -> و
                        '\u{0626}' => '\u{064A}', // ئ -> ي
                        other => other.to_ascii_lowercase(),
                    }
                }
            };
            if mapped.is_whitespace() {
                if !prev_space {
                    out.push(' ');
                    prev_space = true;
                }
            } else {
                out.push(mapped);
                prev_space = false;
            }
        }
        if out.ends_with(' ') {
            out.pop();
        }
        Self(out)
    }

    pub fn as_key_str(&self) -> &str {
        &self.0
    }
}

/// TTS input text preserving diacritics (harakat/shadda) for accurate synthesis.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct DiacritizedTtsInput(String);

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PronunciationOverride {
    /// Unvocalized or vocalized surface form to match (e.g. `"مشروع"` or `"Wispral"`).
    pub surface: String,
    /// Vocalized or phonetic replacement for TTS (e.g. `"مَشْرُوع"` or `"وِسْبْرَال"`).
    pub vocalized_replacement: String,
}

impl DiacritizedTtsInput {
    /// Builds TTS-ready text from a [`VerbatimTranscript`], applying proclitic-aware
    /// pronunciation overrides while preserving attached Arabic proclitics (`بـ`, `الـ`, `والـ`, `للـ`).
    pub fn from_transcript(
        transcript: &VerbatimTranscript,
        overrides: &[PronunciationOverride],
    ) -> Self {
        if overrides.is_empty() {
            return Self(transcript.as_str().replace(TATWEEL, ""));
        }
        let mut table: Vec<(NormalizedMatchKey, &str)> = overrides
            .iter()
            .map(|o| {
                (
                    NormalizedMatchKey::from_surface(&o.surface, NormalizationLevel::FullMatchFold),
                    o.vocalized_replacement.as_str(),
                )
            })
            .collect();
        table.sort_by_key(|a| std::cmp::Reverse(a.0.as_key_str().len()));

        let mut out = String::with_capacity(transcript.as_str().len() + 16);
        for segment in transcript.as_str().split_inclusive(char::is_whitespace) {
            let trimmed = segment.trim_end_matches(char::is_whitespace);
            let trailing_ws = &segment[trimmed.len()..];
            let (lead_punct, core, trail_punct) = split_outer_punctuation(trimmed);

            let mut replaced: Option<String> = None;
            let whole_key =
                NormalizedMatchKey::from_surface(core, NormalizationLevel::FullMatchFold);
            for (k, rep) in &table {
                if whole_key == *k {
                    replaced = Some((*rep).to_owned());
                    break;
                }
            }
            if replaced.is_none() {
                if let Some((proclitic_display, stem)) = split_arabic_proclitic_for_tts(core) {
                    let stem_key =
                        NormalizedMatchKey::from_surface(stem, NormalizationLevel::FullMatchFold);
                    for (k, rep) in &table {
                        if stem_key == *k {
                            replaced = Some(format!("{proclitic_display}{rep}"));
                            break;
                        }
                    }
                }
            }

            out.push_str(lead_punct);
            match replaced {
                Some(r) => out.push_str(&r),
                None => out.push_str(&core.replace(TATWEEL, "")),
            }
            out.push_str(trail_punct);
            out.push_str(trailing_ws);
        }
        Self(out)
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

pub fn is_arabic_diacritic(ch: char) -> bool {
    matches!(
        ch,
        '\u{064B}'..='\u{065F}' | '\u{0670}' | '\u{06D6}'..='\u{06ED}'
    )
}

pub fn is_arabic_script(ch: char) -> bool {
    matches!(
        ch,
        '\u{0600}'..='\u{06FF}'
            | '\u{0750}'..='\u{077F}'
            | '\u{08A0}'..='\u{08FF}'
            | '\u{FB50}'..='\u{FDFF}'
            | '\u{FE70}'..='\u{FEFF}'
    )
}

pub fn fold_alef_and_digits(ch: char) -> char {
    match ch {
        '\u{0622}' | '\u{0623}' | '\u{0625}' | '\u{0671}' => '\u{0627}', // آ أ إ ٱ -> ا
        '\u{0660}'..='\u{0669}' => char::from_u32((ch as u32 - 0x0660) + b'0' as u32).unwrap_or(ch),
        '\u{06F0}'..='\u{06F9}' => char::from_u32((ch as u32 - 0x06F0) + b'0' as u32).unwrap_or(ch),
        other => other,
    }
}

/// Converts Eastern Arabic-Indic (`٠-٩`) and Extended Arabic-Indic (`۰-۹`) digits to ASCII `0-9`
/// without altering any letters or diacritics.
pub fn normalize_arabic_digits(input: &str) -> String {
    input
        .chars()
        .map(|c| match c {
            '\u{0660}'..='\u{0669}' => {
                char::from_u32((c as u32 - 0x0660) + b'0' as u32).unwrap_or(c)
            }
            '\u{06F0}'..='\u{06F9}' => {
                char::from_u32((c as u32 - 0x06F0) + b'0' as u32).unwrap_or(c)
            }
            _ => c,
        })
        .collect()
}

fn split_outer_punctuation(word: &str) -> (&str, &str, &str) {
    let is_punct = |c: char| {
        c.is_ascii_punctuation() || matches!(c, '،' | '؛' | '؟' | '«' | '»' | '“' | '”' | '’')
    };
    let start = word
        .char_indices()
        .find(|&(_, c)| !is_punct(c))
        .map_or(word.len(), |(idx, _)| idx);
    let end = word[start..]
        .char_indices()
        .rev()
        .find(|&(_, c)| !is_punct(c))
        .map_or(start, |(idx, c)| start + idx + c.len_utf8());
    (&word[..start], &word[start..end], &word[end..])
}

/// Proclitic prefixes ordered longest-first (`وال`, `بال`, `كال`, `فال`, `لل`, `ال`, `و`, `ف`, `ب`, `ك`, `ل`).
pub const ARABIC_PROCLITICS: &[&str] = &[
    "وال", "بال", "كال", "فال", "لل", "ال", "و", "ف", "ب", "ك", "ل",
];

fn split_arabic_proclitic_for_tts(word: &str) -> Option<(&str, &str)> {
    // Strip tatweel only at seam check if needed; check clean prefix on surface word
    for &prefix in ARABIC_PROCLITICS {
        if let Some(rest) = word.strip_prefix(prefix) {
            let rest_clean = rest.trim_start_matches(TATWEEL);
            let arabic_letters = rest_clean
                .chars()
                .filter(|&c| is_arabic_script(c) && !is_arabic_diacritic(c))
                .count();
            let latin_letters = rest_clean
                .chars()
                .filter(|c| c.is_ascii_alphabetic())
                .count();
            if arabic_letters >= 3 || latin_letters >= 2 {
                let consumed = word.len() - rest_clean.len();
                return Some((&word[..consumed], rest_clean));
            }
        }
    }
    None
}

/// Tokenizes mixed Arabic-English text while linking standalone code-switch proclitics
/// such as `"للـ pull"` or `"بالـ API"` and generating stem candidates for dictionary lookup.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AnalyzedToken {
    pub surface: String,
    pub match_key: NormalizedMatchKey,
    pub proclitic: Option<String>,
    pub stem_key: NormalizedMatchKey,
    pub is_code_switched_latin: bool,
}

pub fn tokenize_proclitic_aware(input: &str) -> Vec<AnalyzedToken> {
    let raw_tokens: Vec<&str> = input.split_whitespace().collect();
    let mut out = Vec::with_capacity(raw_tokens.len());
    let mut i = 0usize;

    while i < raw_tokens.len() {
        let (_, core, _) = split_outer_punctuation(raw_tokens[i]);
        if core.is_empty() {
            i += 1;
            continue;
        }
        // Check standalone Arabic proclitic ending in tatweel before a Latin token, e.g. `للـ pull`
        if core.ends_with(TATWEEL) && i + 1 < raw_tokens.len() {
            let prefix_clean = core.trim_end_matches(TATWEEL);
            let (_, next_core, _) = split_outer_punctuation(raw_tokens[i + 1]);
            if ARABIC_PROCLITICS.contains(&prefix_clean)
                && next_core.chars().any(|c| c.is_ascii_alphanumeric())
            {
                let combined_surface = format!("{core} {next_core}");
                let stem_key =
                    NormalizedMatchKey::from_surface(next_core, NormalizationLevel::FullMatchFold);
                let match_key = NormalizedMatchKey::from_surface(
                    &combined_surface,
                    NormalizationLevel::FullMatchFold,
                );
                out.push(AnalyzedToken {
                    surface: combined_surface,
                    match_key,
                    proclitic: Some(prefix_clean.to_owned()),
                    stem_key,
                    is_code_switched_latin: true,
                });
                i += 2;
                continue;
            }
        }

        let match_key = NormalizedMatchKey::from_surface(core, NormalizationLevel::FullMatchFold);
        let is_latin = core.chars().any(|c| c.is_ascii_alphabetic());
        let mut proclitic = None;
        let mut stem_key = match_key.clone();

        let key_str = match_key.as_key_str();
        for &p in ARABIC_PROCLITICS {
            if let Some(rest) = key_str.strip_prefix(p) {
                if rest.chars().count() >= 3 {
                    proclitic = Some(p.to_owned());
                    stem_key = NormalizedMatchKey(rest.to_owned());
                    break;
                }
            }
        }

        out.push(AnalyzedToken {
            surface: core.to_owned(),
            match_key,
            proclitic,
            stem_key,
            is_code_switched_latin: is_latin,
        });
        i += 1;
    }
    out
}

/// Wraps contiguous LTR technical/English runs inside RTL strings with `FSI` .. `PDI`.
pub fn isolate_ltr_in_rtl(input: &str) -> String {
    let has_rtl = input.chars().any(is_arabic_script);
    let has_ltr = input.chars().any(|c| c.is_ascii_alphabetic());
    if !has_rtl || !has_ltr {
        return input.to_owned();
    }

    let chars: Vec<char> = input.chars().collect();
    let mut out = String::with_capacity(input.len() + 16);
    let mut i = 0usize;
    while i < chars.len() {
        let c = chars[i];
        if c == FSI {
            // Preserve existing isolate span
            out.push(c);
            i += 1;
            while i < chars.len() {
                out.push(chars[i]);
                if chars[i] == PDI {
                    i += 1;
                    break;
                }
                i += 1;
            }
            continue;
        }
        let starts_ltr = c.is_ascii_alphabetic()
            || (matches!(c, '-' | '/' | '@' | '#')
                && i + 1 < chars.len()
                && chars[i + 1].is_ascii_alphanumeric());
        if starts_ltr {
            let start = i;
            let mut last_ltr_end = i + 1;
            let mut j = i + 1;
            while j < chars.len() {
                let cj = chars[j];
                if is_arabic_script(cj) || matches!(cj, '،' | '؛' | '؟' | '\n' | '\r') {
                    break;
                }
                if cj.is_ascii_alphanumeric() || matches!(cj, '_' | '-' | '/' | '.' | ':' | '#') {
                    last_ltr_end = j + 1;
                    j += 1;
                } else if cj == ' ' && j + 1 < chars.len() && chars[j + 1].is_ascii_alphanumeric() {
                    j += 1;
                } else {
                    break;
                }
            }
            out.push(FSI);
            for &ch in &chars[start..last_ltr_end] {
                out.push(ch);
            }
            out.push(PDI);
            i = last_ltr_end;
        } else {
            out.push(c);
            i += 1;
        }
    }
    out
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ArabicDialectHint {
    MsaOrGeneral,
    SaudiGulf,
    Egyptian,
    Levantine,
    EnglishOrOther,
}

/// Lightweight deterministic dialect cue detector for adaptive routing and evaluation tags.
pub fn detect_dialect_hint(input: &str) -> ArabicDialectHint {
    if !input.chars().any(is_arabic_script) {
        return ArabicDialectHint::EnglishOrOther;
    }
    let tokens = tokenize_proclitic_aware(input);
    let keys: Vec<&str> = tokens
        .iter()
        .flat_map(|t| [t.match_key.as_key_str(), t.stem_key.as_key_str()])
        .collect();

    const GULF: &[&str] = &[
        "سو",
        "وسو",
        "سوي",
        "وسوي",
        "وش",
        "الحين",
        "ابغى",
        "ابي",
        "يبغى",
        "شلون",
        "وايد",
        "مره",
        "طال عمرك",
    ];
    const EGYPTIAN: &[&str] = &[
        "عايز",
        "عاوز",
        "ازيك",
        "دلوقتي",
        "كده",
        "ليه",
        "فين",
        "امبارح",
        "بتاع",
        "مفيش",
    ];
    const LEVANTINE: &[&str] = &[
        "بدي",
        "هلق",
        "شو",
        "هيك",
        "كيفك",
        "منيح",
        "كتير",
        "ليش",
        "وين",
        "مبارح",
    ];

    if keys.iter().any(|k| GULF.contains(k)) {
        return ArabicDialectHint::SaudiGulf;
    }
    if keys.iter().any(|k| EGYPTIAN.contains(k)) {
        return ArabicDialectHint::Egyptian;
    }
    if keys.iter().any(|k| LEVANTINE.contains(k)) {
        return ArabicDialectHint::Levantine;
    }
    ArabicDialectHint::MsaOrGeneral
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EntityKind {
    TechnicalIdentifier,
    CliFlag,
    ReferenceId,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProtectedEntity {
    pub text: String,
    pub kind: EntityKind,
}

/// Extracts technical/code-switched entities, CLI flags, and reference numbers that
/// intelligent rewrite/translation modes MUST preserve verbatim.
pub fn extract_protected_entities(input: &str) -> Vec<ProtectedEntity> {
    let mut entities = Vec::new();
    for raw in input.split_whitespace() {
        let (_, core, _) = split_outer_punctuation(raw.trim_matches(|c| c == FSI || c == PDI));
        if core.is_empty() {
            continue;
        }
        if raw.starts_with("--") || (raw.starts_with('-') && raw.len() > 1 && raw.is_ascii()) {
            entities.push(ProtectedEntity {
                text: raw.trim_end_matches(&[',', '.', '،', '؛'][..]).to_owned(),
                kind: EntityKind::CliFlag,
            });
            continue;
        }
        if (raw.starts_with('#') && raw[1..].chars().all(|c| c.is_ascii_digit()))
            || (core.contains('-') && core.chars().any(|c| c.is_ascii_digit()))
        {
            entities.push(ProtectedEntity {
                text: raw.trim_end_matches(&[',', '.', '،', '؛'][..]).to_owned(),
                kind: EntityKind::ReferenceId,
            });
            continue;
        }
        if core.chars().any(|c| c.is_ascii_alphabetic()) {
            entities.push(ProtectedEntity {
                text: core.to_owned(),
                kind: EntityKind::TechnicalIdentifier,
            });
        }
    }
    entities
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn founder_code_switch_prompt_preserves_verbatim_isolates_bidi_and_links_proclitics() {
        let prompt =
            "افتح مشروع Ecra وسوّ code review للـ pull request الأخير، وبعدها شغّل الاختبارات.";
        let vt = VerbatimTranscript::new(prompt);
        assert_eq!(vt.as_str(), prompt);

        // Dialect hint recognizes Saudi/Gulf `وسوّ` (`سو`)
        assert_eq!(detect_dialect_hint(prompt), ArabicDialectHint::SaudiGulf);

        // Bidi display wraps LTR runs with FSI..PDI without losing Arabic punctuation
        let bidi = vt.to_bidi_isolated();
        assert!(bidi.as_str().contains(&format!("{FSI}Ecra{PDI}")));
        assert!(bidi.as_str().contains(&format!("{FSI}code review{PDI}")));
        assert!(bidi.as_str().contains(&format!("{FSI}pull request{PDI}")));
        assert!(bidi.as_str().ends_with("الاختبارات."));

        // Proclitic-aware tokenizer binds `للـ` to `pull`
        let tokens = tokenize_proclitic_aware(prompt);
        let ll_pull = tokens
            .iter()
            .find(|t| t.proclitic.as_deref() == Some("لل") && t.is_code_switched_latin)
            .expect("standalone للـ before pull must bind proclitic");
        assert_eq!(ll_pull.stem_key.as_key_str(), "pull");

        // Protected entities capture Ecra, code, review, pull, request
        let entities = extract_protected_entities(prompt);
        let names: Vec<&str> = entities.iter().map(|e| e.text.as_str()).collect();
        assert!(names.contains(&"Ecra"));
        assert!(names.contains(&"code"));
        assert!(names.contains(&"review"));
        assert!(names.contains(&"pull"));
        assert!(names.contains(&"request"));
    }

    #[test]
    fn match_key_folds_four_levels_without_polluting_verbatim_or_tts() {
        let a = VerbatimTranscript::new("مَدرَسَةُ الإِبداعِ");
        let b = VerbatimTranscript::new("مدرسه الابداع");
        assert_ne!(a.as_str(), b.as_str());
        assert_eq!(a.to_match_key(), b.to_match_key());
        assert_eq!(a.to_match_key().as_key_str(), "مدرسه الابداع");

        // Proclitic-aware TTS pronunciation override applies to `بالمشروع`
        let spoken = VerbatimTranscript::new("بدأنا بالمشروع رقم ١٤٥");
        let tts = DiacritizedTtsInput::from_transcript(
            &spoken,
            &[PronunciationOverride {
                surface: "مشروع".into(),
                vocalized_replacement: "مَشْرُوع".into(),
            }],
        );
        assert_eq!(tts.as_str(), "بدأنا بالمَشْرُوع رقم ١٤٥");
        assert_eq!(
            normalize_arabic_digits(spoken.as_str()),
            "بدأنا بالمشروع رقم 145"
        );
    }

    #[test]
    fn dialect_hints_distinguish_egyptian_levantine_gulf_and_msa() {
        assert_eq!(
            detect_dialect_hint("عايز أرجع الطلب ده دلوقتي"),
            ArabicDialectHint::Egyptian
        );
        assert_eq!(
            detect_dialect_hint("بدي شوف وين صارت الشحنة هلق"),
            ArabicDialectHint::Levantine
        );
        assert_eq!(
            detect_dialect_hint("وش صار على طلبي الحين"),
            ArabicDialectHint::SaudiGulf
        );
        assert_eq!(
            detect_dialect_hint("أريد الاستفسار عن حالة الطلب"),
            ArabicDialectHint::MsaOrGeneral
        );
    }
}
