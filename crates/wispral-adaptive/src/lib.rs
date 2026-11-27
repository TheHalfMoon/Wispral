//! Wispral Adaptive: CAS model store, OS-locked RAM leases, and deterministic mode router.
//!
//! Enforces three non-negotiable platform invariants:
//! 1. Symlink / Windows reparse-point rejection on `$WISPRAL_HOME/models` staging and reads;
//! 2. Cross-process RAM lease reservations (`leases.json`) so 8 GB (`T0`) laptops never OOM;
//! 3. Zero silent cloud fallback: when `allow_cloud == false` or `AdaptiveMode::Offline` is
//!    active, network/provider-API models are never selected even if every local model is busy.

use std::path::{Path, PathBuf};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use wispral_arabic::{detect_dialect_hint, ArabicDialectHint};
use wispral_contracts::{validate_runtime, validate_shape, ModelManifest};
use wispral_journal::{read_lines, rewrite, with_lock};

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum AdaptiveError {
    #[error("path `{0}` is a symlink or reparse point, which is forbidden in CAS storage")]
    SymlinkOrReparseRejected(String),
    #[error("model manifest rejected: {0}")]
    InvalidManifest(String),
    #[error("artifact SHA-256 mismatch: expected {expected}, got {actual}")]
    DigestMismatch { expected: String, actual: String },
    #[error("insufficient RAM headroom: requested {requested_mb} MB, available {available_mb} MB")]
    InsufficientMemory {
        requested_mb: u64,
        available_mb: u64,
    },
    #[error("no admitted model satisfies mode={mode:?}, modality={modality}, offline_only={offline_only}")]
    NoSuitableModel {
        mode: AdaptiveMode,
        modality: String,
        offline_only: bool,
    },
    #[error("I/O or lock error: {0}")]
    Io(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HardwareTier {
    /// 8 GB RAM CPU-only laptop (`max_voice_ram_mb = 1536`).
    T0LowResourceCpu,
    /// 16 GB RAM multi-core CPU (`max_voice_ram_mb = 4096`).
    T1StandardCpu,
    /// Unified-memory NPU / Apple Silicon (`max_voice_ram_mb = 6144`).
    T2UnifiedAccelerator,
    /// Desktop discrete GPU >= 8 GB (`max_voice_ram_mb = 8192`).
    T3DesktopGpu,
    /// Server node (`max_voice_ram_mb = 24576`).
    T4ServerGpu,
}

impl HardwareTier {
    pub fn ram_budget_mb(self) -> u64 {
        match self {
            Self::T0LowResourceCpu => 1536,
            Self::T1StandardCpu => 4096,
            Self::T2UnifiedAccelerator => 6144,
            Self::T3DesktopGpu => 8192,
            Self::T4ServerGpu => 24576,
        }
    }

    pub fn has_gpu(self) -> bool {
        matches!(
            self,
            Self::T2UnifiedAccelerator | Self::T3DesktopGpu | Self::T4ServerGpu
        )
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AdaptiveMode {
    Fast,
    Precision,
    Realtime,
    Arabic,
    Multilingual,
    Meeting,
    Technical,
    Offline,
    LowResource,
}

/// Rejects symlinks and Windows NTFS reparse points (`FILE_ATTRIBUTE_REPARSE_POINT = 0x0400`).
pub fn ensure_not_reparse_or_symlink(path: &Path) -> Result<(), AdaptiveError> {
    let meta = match std::fs::symlink_metadata(path) {
        Ok(m) => m,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(e) => return Err(AdaptiveError::Io(e.to_string())),
    };
    if meta.file_type().is_symlink() {
        return Err(AdaptiveError::SymlinkOrReparseRejected(
            path.display().to_string(),
        ));
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt as _;
        const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x0400;
        if (meta.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT) != 0 {
            return Err(AdaptiveError::SymlinkOrReparseRejected(
                path.display().to_string(),
            ));
        }
    }
    Ok(())
}

/// Content-Addressed Model Store (`$WISPRAL_HOME/models/blobs/<sha256>`).
#[derive(Debug, Clone)]
pub struct ModelCasStore {
    root: PathBuf,
}

impl ModelCasStore {
    pub fn open(wispral_home: impl AsRef<Path>) -> Result<Self, AdaptiveError> {
        let root = wispral_home.as_ref().join("models");
        ensure_not_reparse_or_symlink(wispral_home.as_ref())?;
        ensure_not_reparse_or_symlink(&root)?;
        std::fs::create_dir_all(root.join("blobs"))
            .map_err(|e| AdaptiveError::Io(e.to_string()))?;
        std::fs::create_dir_all(root.join("manifests"))
            .map_err(|e| AdaptiveError::Io(e.to_string()))?;
        Ok(Self { root })
    }

    pub fn stage_verified_blob(
        &self,
        source_file: &Path,
        expected_sha256: &str,
    ) -> Result<PathBuf, AdaptiveError> {
        ensure_not_reparse_or_symlink(source_file)?;
        let bytes = std::fs::read(source_file).map_err(|e| AdaptiveError::Io(e.to_string()))?;
        let mut hasher = Sha256::new();
        hasher.update(&bytes);
        let actual = hex::encode(hasher.finalize());
        if actual != expected_sha256 {
            return Err(AdaptiveError::DigestMismatch {
                expected: expected_sha256.to_owned(),
                actual,
            });
        }
        let dest = self.root.join("blobs").join(&actual);
        ensure_not_reparse_or_symlink(&dest)?;
        if !dest.exists() {
            let tmp = self
                .root
                .join("blobs")
                .join(format!("{actual}.tmp-{}", std::process::id()));
            std::fs::write(&tmp, &bytes).map_err(|e| AdaptiveError::Io(e.to_string()))?;
            std::fs::rename(&tmp, &dest).map_err(|e| AdaptiveError::Io(e.to_string()))?;
        }
        Ok(dest)
    }

    pub fn register_manifest(&self, manifest: &ModelManifest) -> Result<PathBuf, AdaptiveError> {
        let val = serde_json::to_value(manifest)
            .map_err(|e| AdaptiveError::InvalidManifest(e.to_string()))?;
        validate_shape("model_manifest", &val).map_err(AdaptiveError::InvalidManifest)?;
        validate_runtime("model_manifest", &val, &std::collections::HashMap::new())
            .map_err(AdaptiveError::InvalidManifest)?;
        if manifest.admission_state != "admitted" {
            return Err(AdaptiveError::InvalidManifest(
                "only admitted manifests can be registered for active routing".into(),
            ));
        }
        let safe_id: String = manifest
            .model_id
            .chars()
            .map(|c| {
                if c.is_ascii_alphanumeric() || c == '-' || c == '_' {
                    c
                } else {
                    '_'
                }
            })
            .collect();
        let path = self
            .root
            .join("manifests")
            .join(format!("{safe_id}--{}.json", manifest.revision));
        ensure_not_reparse_or_symlink(&path)?;
        let encoded = serde_json::to_vec_pretty(&val)
            .map_err(|e| AdaptiveError::InvalidManifest(e.to_string()))?;
        std::fs::write(&path, encoded).map_err(|e| AdaptiveError::Io(e.to_string()))?;
        Ok(path)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MemoryLease {
    pub lease_id: String,
    pub product: String,
    pub model_id: String,
    pub pid: u32,
    pub start_generation: String,
    pub ram_mb: u64,
    pub expires_at_ms: u64,
}

/// Cross-process OS-locked memory reservation ledger (`$WISPRAL_HOME/leases.jsonl`).
#[derive(Debug, Clone)]
pub struct MemoryLeaseManager {
    ledger_path: PathBuf,
    budget_mb: u64,
}

impl MemoryLeaseManager {
    pub fn new(wispral_home: impl AsRef<Path>, tier: HardwareTier) -> Self {
        Self {
            ledger_path: wispral_home.as_ref().join("leases.jsonl"),
            budget_mb: tier.ram_budget_mb(),
        }
    }

    pub fn acquire(&self, lease: MemoryLease, now_ms: u64) -> Result<MemoryLease, AdaptiveError> {
        let mut out_err: Option<AdaptiveError> = None;
        let path = self.ledger_path.clone();
        let budget = self.budget_mb;
        let candidate = lease.clone();

        with_lock(&path, Duration::from_secs(2), || {
            let mut active: Vec<MemoryLease> = read_lines::<MemoryLease>(&path)?
                .lines
                .into_iter()
                .filter(|l| l.expires_at_ms > now_ms && l.lease_id != candidate.lease_id)
                .collect();
            let used_mb: u64 = active.iter().map(|l| l.ram_mb).sum();
            let available_mb = budget.saturating_sub(used_mb);
            if candidate.ram_mb > available_mb {
                out_err = Some(AdaptiveError::InsufficientMemory {
                    requested_mb: candidate.ram_mb,
                    available_mb,
                });
                rewrite(&path, &active)?;
                return Ok(());
            }
            active.push(candidate);
            rewrite(&path, &active)
        })
        .map_err(|e| AdaptiveError::Io(e.to_string()))?;

        if let Some(err) = out_err {
            return Err(err);
        }
        Ok(lease)
    }

    pub fn release(&self, lease_id: &str, now_ms: u64) -> Result<bool, AdaptiveError> {
        let path = self.ledger_path.clone();
        let mut removed = false;
        with_lock(&path, Duration::from_secs(2), || {
            let before = read_lines::<MemoryLease>(&path)?.lines;
            let after: Vec<MemoryLease> = before
                .into_iter()
                .filter(|l| {
                    if l.lease_id == lease_id {
                        removed = true;
                        false
                    } else {
                        l.expires_at_ms > now_ms
                    }
                })
                .collect();
            rewrite(&path, &after)
        })
        .map_err(|e| AdaptiveError::Io(e.to_string()))?;
        Ok(removed)
    }
}

#[derive(Debug, Clone)]
pub struct RouteRequest<'a> {
    pub modality: &'a str,
    pub mode: AdaptiveMode,
    pub tier: HardwareTier,
    pub language_hint: Option<&'a str>,
    pub sample_text: Option<&'a str>,
    pub allow_cloud_byok: bool,
    pub available_ram_mb: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RouteDecision {
    pub model_id: String,
    pub revision: String,
    pub offline: bool,
    pub reason: String,
}

/// Deterministic model selector across registered manifests.
pub fn select_model(
    manifests: &[ModelManifest],
    req: &RouteRequest<'_>,
) -> Result<RouteDecision, AdaptiveError> {
    let offline_only = !req.allow_cloud_byok
        || matches!(req.mode, AdaptiveMode::Offline | AdaptiveMode::LowResource);

    let inferred_arabic = req
        .language_hint
        .is_some_and(|l| l == "ar" || l.starts_with("ar-"))
        || req
            .sample_text
            .is_some_and(|t| detect_dialect_hint(t) != ArabicDialectHint::EnglishOrOther)
        || req.mode == AdaptiveMode::Arabic;

    let mut scored: Vec<(i64, &ModelManifest)> = Vec::new();
    for m in manifests {
        if m.admission_state != "admitted" || m.modality != req.modality {
            continue;
        }
        if offline_only && (!m.offline_capable || m.requirements.network_required) {
            continue;
        }
        if m.requirements.accelerator == "gpu_required" && !req.tier.has_gpu() {
            continue;
        }
        let needed_ram = m.requirements.min_ram_mb.unwrap_or(256);
        if needed_ram > req.available_ram_mb {
            continue;
        }

        let supports_ar = m
            .languages
            .iter()
            .any(|l| (l.code == "ar" || l.code.starts_with("ar-")) && l.support != "unsupported");
        if inferred_arabic && !supports_ar {
            continue;
        }

        let mut score = 0i64;
        if m.offline_capable {
            score += 50; // Local-first preference
        }
        match req.mode {
            AdaptiveMode::Fast | AdaptiveMode::LowResource => {
                score += (4096i64 - needed_ram as i64) / 32;
            }
            AdaptiveMode::Realtime => {
                if matches!(
                    m.streaming_mode.as_deref(),
                    Some("native_streaming" | "full_duplex")
                ) {
                    score += 80;
                }
                score += (4096i64 - needed_ram as i64) / 64;
            }
            AdaptiveMode::Precision | AdaptiveMode::Meeting | AdaptiveMode::Technical => {
                score += (needed_ram as i64) / 32;
            }
            AdaptiveMode::Arabic | AdaptiveMode::Multilingual => {
                if supports_ar {
                    score += 100;
                }
            }
            AdaptiveMode::Offline => {
                score += 100;
            }
        }
        scored.push((score, m));
    }

    scored.sort_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.model_id.cmp(&b.1.model_id)));
    let Some((_, chosen)) = scored.first() else {
        return Err(AdaptiveError::NoSuitableModel {
            mode: req.mode,
            modality: req.modality.to_owned(),
            offline_only,
        });
    };

    Ok(RouteDecision {
        model_id: chosen.model_id.clone(),
        revision: chosen.revision.clone(),
        offline: chosen.offline_capable,
        reason: format!(
            "selected `{}` (mode={:?}, arabic={}, offline={})",
            chosen.model_id, req.mode, inferred_arabic, chosen.offline_capable
        ),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn sample_manifest(
        id: &str,
        offline: bool,
        ram_mb: u64,
        arabic: bool,
        streaming: &str,
    ) -> ModelManifest {
        let mut langs = vec![json!({"code": "en", "support": "documented"})];
        if arabic {
            langs.push(json!({"code": "ar", "variety": "MSA", "support": "documented"}));
        }
        let val = if offline {
            json!({
                "model_id": id,
                "revision": "v1",
                "source_url": "https://example.invalid/m",
                "source_revision": "r1",
                "modality": "stt",
                "artifact": {
                    "files": [{"path": "m.gguf", "sha256": "b".repeat(64), "size_bytes": 1024}],
                    "bundle_sha256": "d".repeat(64)
                },
                "languages": langs,
                "runtime": "ggml",
                "serialization": "gguf",
                "trust_remote_code": false,
                "offline_capable": true,
                "network_hosts": [],
                "acquisition": "pre_staged",
                "code_license": "MIT",
                "weight_license": "Apache-2.0",
                "commercial_use": "allowed",
                "requires_consent": false,
                "effect_classes": ["text_hypothesis"],
                "authority_ceiling": "evidence_only",
                "requirements": {"process_isolation": "subprocess", "network_required": false, "accelerator": "none", "min_ram_mb": ram_mb},
                "admission_state": "admitted",
                "streaming_mode": streaming
            })
        } else {
            json!({
                "model_id": id,
                "revision": "v1",
                "source_url": "https://example.invalid/cloud",
                "source_revision": "r1",
                "modality": "stt",
                "artifact": {"provider_managed_digest_unavailable": true, "provider": "byok"},
                "languages": langs,
                "runtime": "provider_api",
                "serialization": "provider_managed",
                "trust_remote_code": false,
                "offline_capable": false,
                "network_hosts": ["api.example.invalid"],
                "acquisition": "pre_staged",
                "code_license": "MIT",
                "weight_license": "proprietary",
                "commercial_use": "conditional",
                "commercial_conditions": "User BYOK",
                "requires_consent": false,
                "effect_classes": ["text_hypothesis"],
                "authority_ceiling": "evidence_only",
                "requirements": {"process_isolation": "subprocess", "network_required": true, "accelerator": "none", "min_ram_mb": 32},
                "admission_state": "admitted",
                "streaming_mode": streaming
            })
        };
        serde_json::from_value(val).unwrap()
    }

    #[test]
    fn adaptive_router_never_silently_falls_back_to_cloud_and_enforces_t0_leases() {
        let dir = std::env::temp_dir().join(format!("wispral-adaptive-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        let leases = MemoryLeaseManager::new(&dir, HardwareTier::T0LowResourceCpu); // 1536 MB budget

        leases
            .acquire(
                MemoryLease {
                    lease_id: "l1".into(),
                    product: "wisprside".into(),
                    model_id: "whisper-small".into(),
                    pid: 100,
                    start_generation: "1".into(),
                    ram_mb: 1024,
                    expires_at_ms: 50_000,
                },
                1_000,
            )
            .unwrap();

        // Second 1024 MB lease exceeds 1536 MB T0 budget -> refused!
        assert!(matches!(
            leases.acquire(
                MemoryLease {
                    lease_id: "l2".into(),
                    product: "wisprstudio".into(),
                    model_id: "kokoro".into(),
                    pid: 101,
                    start_generation: "1".into(),
                    ram_mb: 1024,
                    expires_at_ms: 50_000,
                },
                1_000,
            ),
            Err(AdaptiveError::InsufficientMemory { .. })
        ));
        assert!(leases.release("l1", 1_500).unwrap());

        // Routing: cloud model available, local model too big for remaining RAM, allow_cloud_byok = false -> MUST FAIL CLOSED, never silently route to cloud!
        let models = vec![
            sample_manifest("local-large-ar", true, 2048, true, "chunked"),
            sample_manifest("cloud-byok-ar", false, 32, true, "full_duplex"),
        ];
        let req = RouteRequest {
            modality: "stt",
            mode: AdaptiveMode::Arabic,
            tier: HardwareTier::T0LowResourceCpu,
            language_hint: Some("ar-SA"),
            sample_text: None,
            allow_cloud_byok: false,
            available_ram_mb: 1024,
        };
        assert!(matches!(
            select_model(&models, &req),
            Err(AdaptiveError::NoSuitableModel {
                offline_only: true,
                ..
            })
        ));

        // Add compact local Arabic model -> selected deterministically!
        let mut with_compact = models;
        with_compact.push(sample_manifest(
            "local-compact-ar",
            true,
            512,
            true,
            "native_streaming",
        ));
        let chosen = select_model(&with_compact, &req).unwrap();
        assert_eq!(chosen.model_id, "local-compact-ar");
        assert!(chosen.offline);
        let _ = std::fs::remove_dir_all(&dir);
    }
}
