//! Wispral Context: headless privacy-scoped context engine.
//!
//! Provides bounded repository vocabulary scanning, Arabic/multilingual glossary
//! normalization, and deterministic secret/password redaction without pulling any
//! OS GUI or network dependencies into `Wispral Core`.

use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::path::Path;

use serde::{Deserialize, Serialize};
use wispral_arabic::{tokenize_proclitic_aware, NormalizationLevel, NormalizedMatchKey};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkspaceVocabulary {
    pub file_stems: Vec<String>,
    pub symbols: Vec<String>,
}

/// Scans up to `max_files` source files under `root`, skipping hidden/build directories,
/// to extract domain identifiers (`camelCase`, `PascalCase`, `snake_case`, file stems)
/// for STT biasing and entity correction.
pub fn scan_workspace_vocabulary(root: &Path, max_files: usize) -> WorkspaceVocabulary {
    let mut stems = BTreeSet::new();
    let mut symbols = BTreeSet::new();
    let mut visited = 0usize;

    fn walk(
        dir: &Path,
        max_files: usize,
        visited: &mut usize,
        stems: &mut BTreeSet<String>,
        symbols: &mut BTreeSet<String>,
    ) {
        if *visited >= max_files {
            return;
        }
        let Ok(entries) = std::fs::read_dir(dir) else {
            return;
        };
        for entry in entries.flatten() {
            if *visited >= max_files {
                break;
            }
            let Ok(ft) = entry.file_type() else {
                continue;
            };
            if ft.is_symlink() {
                continue;
            }
            let name = entry.file_name();
            let Some(name_str) = name.to_str() else {
                continue;
            };
            if ft.is_dir() {
                if name_str.starts_with('.')
                    || matches!(
                        name_str,
                        "node_modules" | "target" | "dist" | "build" | "__pycache__" | "venv"
                    )
                {
                    continue;
                }
                walk(&entry.path(), max_files, visited, stems, symbols);
            } else if ft.is_file() {
                let path = entry.path();
                let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
                if !matches!(
                    ext,
                    "rs" | "ts" | "tsx" | "js" | "py" | "md" | "toml" | "json"
                ) {
                    continue;
                }
                *visited += 1;
                if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                    if stem.len() >= 3 {
                        stems.insert(stem.to_owned());
                    }
                }
                if let Ok(meta) = entry.metadata() {
                    if meta.len() <= 64 * 1024 {
                        if let Ok(content) = std::fs::read_to_string(&path) {
                            extract_code_symbols(&content, symbols);
                        }
                    }
                }
            }
        }
    }

    walk(root, max_files, &mut visited, &mut stems, &mut symbols);
    WorkspaceVocabulary {
        file_stems: stems.into_iter().collect(),
        symbols: symbols.into_iter().take(512).collect(),
    }
}

fn extract_code_symbols(source: &str, out: &mut BTreeSet<String>) {
    const KEYWORDS: &[&str] = &[
        "fn",
        "struct",
        "enum",
        "trait",
        "class",
        "def",
        "interface",
        "type",
    ];
    for line in source.lines() {
        let tokens: Vec<&str> = line.split_whitespace().collect();
        for pair in tokens.windows(2) {
            let kw = pair[0].trim_start_matches("pub");
            if KEYWORDS.contains(&kw) || (pair[0] == "pub" && tokens.len() >= 3) {
                let raw_ident = pair[1]
                    .split(['(', '<', ':', '{', ';', '='])
                    .next()
                    .unwrap_or("");
                if raw_ident.len() >= 3
                    && raw_ident
                        .chars()
                        .all(|c| c.is_ascii_alphanumeric() || c == '_')
                {
                    out.insert(raw_ident.to_owned());
                }
            }
        }
    }
}

/// Redacts secrets, bearer tokens, API keys, and PEM blocks before context is passed to any model.
pub fn redact_sensitive_text(input: &str) -> String {
    if input.contains("-----BEGIN ") && input.contains("PRIVATE KEY-----") {
        return "[REDACTED_PRIVATE_KEY]".to_owned();
    }
    let mut out = Vec::new();
    let mut prev_is_bearer = false;
    for token in input.split_inclusive(char::is_whitespace) {
        let trimmed = token.trim_end_matches(char::is_whitespace);
        let ws = &token[trimmed.len()..];
        let clean_lower = trimmed
            .trim_matches(&['"', '\'', ',', ';', ':', '(', ')'][..])
            .to_ascii_lowercase();
        if prev_is_bearer && !trimmed.is_empty() {
            out.push(format!("[REDACTED_SECRET]{ws}"));
            prev_is_bearer = false;
            continue;
        }
        prev_is_bearer = clean_lower == "bearer";
        if looks_like_secret_token(trimmed) {
            out.push(format!("[REDACTED_SECRET]{ws}"));
        } else {
            out.push(token.to_owned());
        }
    }
    out.concat()
}

fn looks_like_secret_token(tok: &str) -> bool {
    let clean = tok.trim_matches(&['"', '\'', ',', ';', '(', ')'][..]);
    if let Some((_, rhs)) = clean.split_once('=') {
        let lhs_lower = clean.split('=').next().unwrap_or("").to_ascii_lowercase();
        if (lhs_lower.contains("key")
            || lhs_lower.contains("secret")
            || lhs_lower.contains("token")
            || lhs_lower.contains("password"))
            && rhs.len() >= 8
        {
            return true;
        }
    }
    clean.starts_with("sk-")
        || clean.starts_with("ghp_")
        || clean.starts_with("github_pat_")
        || clean.starts_with("xoxb-")
        || (clean.starts_with("AKIA") && clean.len() >= 16)
        || (clean.starts_with("eyJ") && clean.matches('.').count() >= 2 && clean.len() >= 20)
}

/// Multilingual/Arabic-aware glossary replacer that maps spoken aliases (e.g. `"وسبر سايد"` or `"ecra"`)
/// to canonical product/codebase terms (`"WisprSide"`, `"Ecra"`), preserving Arabic proclitics.
#[derive(Debug, Clone, Default)]
pub struct GlossaryMatcher {
    entries: HashMap<NormalizedMatchKey, String>,
}

impl GlossaryMatcher {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn insert_alias(&mut self, alias: &str, canonical: impl Into<String>) {
        let key = NormalizedMatchKey::from_surface(alias, NormalizationLevel::FullMatchFold);
        self.entries.insert(key, canonical.into());
    }

    pub fn apply(&self, text: &str) -> String {
        if self.entries.is_empty() {
            return text.to_owned();
        }
        let analyzed = tokenize_proclitic_aware(text);
        let mut replacements: BTreeMap<String, String> = BTreeMap::new();
        for tok in analyzed {
            if let Some(canon) = self.entries.get(&tok.match_key) {
                replacements.insert(tok.surface, canon.clone());
            } else if let (Some(proc), Some(canon)) =
                (tok.proclitic.as_deref(), self.entries.get(&tok.stem_key))
            {
                if canon.is_ascii() {
                    replacements.insert(tok.surface, format!("{proc}ـ {canon}"));
                } else {
                    replacements.insert(tok.surface, format!("{proc}{canon}"));
                }
            }
        }
        if replacements.is_empty() {
            return text.to_owned();
        }
        let is_punct = |c: char| {
            c.is_ascii_punctuation() || matches!(c, '،' | '؛' | '؟' | '«' | '»' | '“' | '”' | '’')
        };
        let segments: Vec<&str> = text.split_inclusive(char::is_whitespace).collect();
        let mut out = String::with_capacity(text.len() + 16);
        let mut i = 0usize;
        while i < segments.len() {
            let trimmed = segments[i].trim_end_matches(char::is_whitespace);
            let ws = &segments[i][trimmed.len()..];
            let s = trimmed
                .char_indices()
                .find(|&(_, c)| !is_punct(c))
                .map_or(trimmed.len(), |(idx, _)| idx);
            let e = trimmed[s..]
                .char_indices()
                .rev()
                .find(|&(_, c)| !is_punct(c))
                .map_or(s, |(idx, c)| s + idx + c.len_utf8());
            let (lead, core, trail) = (&trimmed[..s], &trimmed[s..e], &trimmed[e..]);

            if core.ends_with('\u{0640}') && i + 1 < segments.len() {
                let next_trim = segments[i + 1].trim_end_matches(char::is_whitespace);
                let next_ws = &segments[i + 1][next_trim.len()..];
                let ns = next_trim
                    .char_indices()
                    .find(|&(_, c)| !is_punct(c))
                    .map_or(next_trim.len(), |(idx, _)| idx);
                let ne = next_trim[ns..]
                    .char_indices()
                    .rev()
                    .find(|&(_, c)| !is_punct(c))
                    .map_or(ns, |(idx, c)| ns + idx + c.len_utf8());
                let (nlead, ncore, ntrail) =
                    (&next_trim[..ns], &next_trim[ns..ne], &next_trim[ne..]);
                let combined = format!("{core} {ncore}");
                if let Some(rep) = replacements.get(&combined) {
                    out.push_str(lead);
                    out.push_str(nlead);
                    out.push_str(rep);
                    out.push_str(ntrail);
                    out.push_str(next_ws);
                    i += 2;
                    continue;
                }
            }

            if let Some(rep) = replacements.get(core) {
                out.push_str(lead);
                out.push_str(rep);
                out.push_str(trail);
                out.push_str(ws);
            } else {
                out.push_str(segments[i]);
            }
            i += 1;
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn redactor_strips_secrets_and_glossary_matches_arabic_proclitic_code_terms() {
        let raw = "Deploy with OPENAI_API_KEY=sk-proj-1234567890abcdef, Authorization: Bearer opaque_tok_999, and token ghp_secret999999";
        let clean = redact_sensitive_text(raw);
        assert!(!clean.contains("sk-proj"));
        assert!(!clean.contains("opaque_tok_999"));
        assert!(!clean.contains("ghp_secret"));
        assert_eq!(
            clean,
            "Deploy with [REDACTED_SECRET] Authorization: Bearer [REDACTED_SECRET] and token [REDACTED_SECRET]"
        );

        let mut g = GlossaryMatcher::new();
        g.insert_alias("ecra", "Ecra");
        g.insert_alias("وسبرال", "Wispral");
        let fixed = g.apply("افتح مشروع ecra في بوسبرال ولا تغيّر spacecraft");
        assert_eq!(fixed, "افتح مشروع Ecra في بـ Wispral ولا تغيّر spacecraft");
    }
}
