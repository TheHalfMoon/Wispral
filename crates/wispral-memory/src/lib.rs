//! Wispral Memory: local-first, user-owned vocabulary, corrections, snippets,
//! application profiles, and bounded history.
//!
//! Privacy invariants (Constitution Principle XIV):
//! - `keep_audio` is `false` by default;
//! - Users can set `RetentionPolicy::KeepNothing`, in which case zero transcripts
//!   or history entries are ever written to disk;
//! - Every stored entry can be inspected, edited, deleted individually, purged by TTL,
//!   exported as portable JSON, or wiped completely.

use std::path::{Path, PathBuf};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use thiserror::Error;
use wispral_arabic::{NormalizationLevel, NormalizedMatchKey};
use wispral_journal::{read_lines, rewrite, with_lock};

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum MemoryError {
    #[error("memory journal error: {0}")]
    Journal(String),
    #[error("serialization error: {0}")]
    Serialization(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "mode", rename_all = "snake_case")]
pub enum RetentionPolicy {
    KeepNothing,
    SessionOnly,
    BoundedDays { days: u32 },
    UserControlled,
}

impl Default for RetentionPolicy {
    fn default() -> Self {
        Self::BoundedDays { days: 7 }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MemoryPrivacyConfig {
    pub keep_audio: bool,
    pub retention: RetentionPolicy,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DictionaryEntry {
    pub id: String,
    pub canonical: String,
    pub aliases: Vec<String>,
    pub language: String,
    pub created_at_ms: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CorrectionRule {
    pub id: String,
    pub heard: String,
    pub corrected: String,
    pub created_at_ms: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SnippetTemplate {
    pub id: String,
    pub trigger: String,
    pub expansion: String,
    pub created_at_ms: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HistoryRecord {
    pub id: String,
    pub mode: String,
    pub text: String,
    pub app_name: Option<String>,
    pub audio_ref: Option<String>,
    pub created_at_ms: u64,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MemoryExportBundle {
    pub schema_version: u32,
    pub privacy: MemoryPrivacyConfig,
    pub dictionary: Vec<DictionaryEntry>,
    pub corrections: Vec<CorrectionRule>,
    pub snippets: Vec<SnippetTemplate>,
    pub history: Vec<HistoryRecord>,
}

#[derive(Debug, Clone)]
pub struct MemoryStore {
    root: PathBuf,
    privacy: MemoryPrivacyConfig,
}

impl MemoryStore {
    pub fn open(
        wispral_home: impl AsRef<Path>,
        privacy: MemoryPrivacyConfig,
    ) -> Result<Self, MemoryError> {
        let root = wispral_home.as_ref().join("memory");
        std::fs::create_dir_all(&root).map_err(|e| MemoryError::Journal(e.to_string()))?;
        Ok(Self { root, privacy })
    }

    pub fn privacy(&self) -> &MemoryPrivacyConfig {
        &self.privacy
    }

    pub fn set_privacy(&mut self, privacy: MemoryPrivacyConfig) {
        self.privacy = privacy;
    }

    fn dict_path(&self) -> PathBuf {
        self.root.join("dictionary.jsonl")
    }
    fn corr_path(&self) -> PathBuf {
        self.root.join("corrections.jsonl")
    }
    fn snip_path(&self) -> PathBuf {
        self.root.join("snippets.jsonl")
    }
    fn hist_path(&self) -> PathBuf {
        self.root.join("history.jsonl")
    }

    pub fn upsert_dictionary(&self, entry: DictionaryEntry) -> Result<(), MemoryError> {
        let p = self.dict_path();
        with_lock(&p, Duration::from_secs(2), || {
            let mut items = read_lines::<DictionaryEntry>(&p)?.lines;
            items.retain(|x| x.id != entry.id);
            items.push(entry);
            rewrite(&p, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))
    }

    pub fn upsert_correction(&self, rule: CorrectionRule) -> Result<(), MemoryError> {
        let p = self.corr_path();
        with_lock(&p, Duration::from_secs(2), || {
            let mut items = read_lines::<CorrectionRule>(&p)?.lines;
            items.retain(|x| x.id != rule.id);
            items.push(rule);
            rewrite(&p, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))
    }

    pub fn upsert_snippet(&self, snippet: SnippetTemplate) -> Result<(), MemoryError> {
        let p = self.snip_path();
        with_lock(&p, Duration::from_secs(2), || {
            let mut items = read_lines::<SnippetTemplate>(&p)?.lines;
            items.retain(|x| x.id != snippet.id);
            items.push(snippet);
            rewrite(&p, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))
    }

    pub fn record_history(&self, mut record: HistoryRecord) -> Result<bool, MemoryError> {
        if self.privacy.retention == RetentionPolicy::KeepNothing {
            return Ok(false);
        }
        if !self.privacy.keep_audio {
            record.audio_ref = None;
        }
        let p = self.hist_path();
        with_lock(&p, Duration::from_secs(2), || {
            let mut items = read_lines::<HistoryRecord>(&p)?.lines;
            items.push(record);
            rewrite(&p, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))?;
        Ok(true)
    }

    pub fn delete_entry(&self, id: &str) -> Result<usize, MemoryError> {
        let mut deleted = 0usize;
        let d = self.dict_path();
        with_lock(&d, Duration::from_secs(2), || {
            let mut items = read_lines::<DictionaryEntry>(&d)?.lines;
            let before = items.len();
            items.retain(|x| x.id != id);
            deleted += before - items.len();
            rewrite(&d, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))?;

        let c = self.corr_path();
        with_lock(&c, Duration::from_secs(2), || {
            let mut items = read_lines::<CorrectionRule>(&c)?.lines;
            let before = items.len();
            items.retain(|x| x.id != id);
            deleted += before - items.len();
            rewrite(&c, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))?;

        let s = self.snip_path();
        with_lock(&s, Duration::from_secs(2), || {
            let mut items = read_lines::<SnippetTemplate>(&s)?.lines;
            let before = items.len();
            items.retain(|x| x.id != id);
            deleted += before - items.len();
            rewrite(&s, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))?;

        let h = self.hist_path();
        with_lock(&h, Duration::from_secs(2), || {
            let mut items = read_lines::<HistoryRecord>(&h)?.lines;
            let before = items.len();
            items.retain(|x| x.id != id);
            deleted += before - items.len();
            rewrite(&h, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))?;

        Ok(deleted)
    }

    pub fn purge_expired_history(&self, now_ms: u64) -> Result<usize, MemoryError> {
        let RetentionPolicy::BoundedDays { days } = self.privacy.retention else {
            return Ok(0);
        };
        let ttl_ms = (days as u64) * 86_400_000;
        let cutoff = now_ms.saturating_sub(ttl_ms);
        let h = self.hist_path();
        let mut purged = 0usize;
        with_lock(&h, Duration::from_secs(2), || {
            let mut items = read_lines::<HistoryRecord>(&h)?.lines;
            let before = items.len();
            items.retain(|x| x.created_at_ms >= cutoff);
            purged = before - items.len();
            rewrite(&h, &items)
        })
        .map_err(|e| MemoryError::Journal(e.to_string()))?;
        Ok(purged)
    }

    /// Applies stored user corrections and snippet triggers using Arabic/multilingual match keys.
    pub fn apply_personalizations(&self, input: &str) -> Result<String, MemoryError> {
        let snippets = read_lines::<SnippetTemplate>(&self.snip_path())
            .map_err(|e| MemoryError::Journal(e.to_string()))?
            .lines;
        let input_key = NormalizedMatchKey::from_surface(input, NormalizationLevel::FullMatchFold);
        for snip in &snippets {
            let trig_key =
                NormalizedMatchKey::from_surface(&snip.trigger, NormalizationLevel::FullMatchFold);
            if input_key == trig_key {
                return Ok(snip.expansion.clone());
            }
        }

        let corrections = read_lines::<CorrectionRule>(&self.corr_path())
            .map_err(|e| MemoryError::Journal(e.to_string()))?
            .lines;
        let mut out = input.to_owned();
        for corr in &corrections {
            if out.contains(&corr.heard) {
                out = out.replace(&corr.heard, &corr.corrected);
            }
        }
        Ok(out)
    }

    pub fn export_bundle(&self) -> Result<MemoryExportBundle, MemoryError> {
        Ok(MemoryExportBundle {
            schema_version: 1,
            privacy: self.privacy.clone(),
            dictionary: read_lines(&self.dict_path())
                .map_err(|e| MemoryError::Journal(e.to_string()))?
                .lines,
            corrections: read_lines(&self.corr_path())
                .map_err(|e| MemoryError::Journal(e.to_string()))?
                .lines,
            snippets: read_lines(&self.snip_path())
                .map_err(|e| MemoryError::Journal(e.to_string()))?
                .lines,
            history: read_lines(&self.hist_path())
                .map_err(|e| MemoryError::Journal(e.to_string()))?
                .lines,
        })
    }

    pub fn wipe_all(&self) -> Result<(), MemoryError> {
        for p in [
            self.dict_path(),
            self.corr_path(),
            self.snip_path(),
            self.hist_path(),
        ] {
            with_lock(&p, Duration::from_secs(2), || {
                rewrite::<HistoryRecord>(&p, &[])
            })
            .map_err(|e| MemoryError::Journal(e.to_string()))?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn memory_store_enforces_keep_audio_false_keep_nothing_ttl_and_export() {
        let dir = std::env::temp_dir().join(format!("wispral-mem-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);

        let mut store = MemoryStore::open(&dir, MemoryPrivacyConfig::default()).unwrap();
        assert!(!store.privacy().keep_audio);

        store
            .upsert_snippet(SnippetTemplate {
                id: "sn1".into(),
                trigger: "توقيع البريد".into(),
                expansion: "مع خالص التحية، فريق Wispral".into(),
                created_at_ms: 1_000,
            })
            .unwrap();
        assert_eq!(
            store.apply_personalizations("توقيع البريد").unwrap(),
            "مع خالص التحية، فريق Wispral"
        );

        // Default keep_audio = false strips audio_ref
        store
            .record_history(HistoryRecord {
                id: "h1".into(),
                mode: "dictation".into(),
                text: "hello".into(),
                app_name: Some("VS Code".into()),
                audio_ref: Some("secret.wav".into()),
                created_at_ms: 1_000,
            })
            .unwrap();
        let bundle = store.export_bundle().unwrap();
        assert_eq!(bundle.history.len(), 1);
        assert_eq!(bundle.history[0].audio_ref, None);

        // TTL sweep removes expired record after 8 days
        let purged = store.purge_expired_history(1_000 + 8 * 86_400_000).unwrap();
        assert_eq!(purged, 1);

        // KeepNothing mode writes zero history
        store.set_privacy(MemoryPrivacyConfig {
            keep_audio: false,
            retention: RetentionPolicy::KeepNothing,
        });
        assert!(!store
            .record_history(HistoryRecord {
                id: "h2".into(),
                mode: "dictation".into(),
                text: "ephemeral".into(),
                app_name: None,
                audio_ref: None,
                created_at_ms: 10_000,
            })
            .unwrap());
        assert!(store.export_bundle().unwrap().history.is_empty());

        store.wipe_all().unwrap();
        assert!(store.export_bundle().unwrap().snippets.is_empty());
        let _ = std::fs::remove_dir_all(&dir);
    }
}
