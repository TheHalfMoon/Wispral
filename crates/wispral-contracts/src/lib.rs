//! Wispral Core portable contracts, shape & runtime invariant validators, and state machines.
//!
//! Covers all 10 normative v1/v1.1 schemas under `docs/engineering/contracts/`:
//! - `envelope`
//! - `cancellation`
//! - `model_manifest`
//! - `consent_record`
//! - `policy_verdict`
//! - `provenance_event`
//! - `delivery_outcome`
//! - `effect_intent`
//! - `network_manifest`
//! - `export_provenance`

pub mod canonical_path;
pub mod crypto;
pub mod jcs;

use std::collections::{HashMap, HashSet};

use chrono::{DateTime, FixedOffset};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use wispral_journal::IntentState;
use wispral_policy::{compose_layers, CandidateDecision, PolicyLayer};

use crate::crypto::{compute_consent_bound_digest, DetachedSignature};

pub const CAPABILITY_MAX_SECONDS: f64 = 60.0;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProductId {
    Wisprside,
    Wisprstudio,
    Klaint,
    Omalla,
    Core,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CancellationState {
    Requested,
    Acknowledged,
    ObservedStopped,
    CompletedBeforeCancel,
    StoppedUnconfirmed,
    Failed,
}

impl CancellationState {
    pub fn may_become(self, next: Self) -> bool {
        use CancellationState::*;
        matches!(
            (self, next),
            (
                Requested,
                Acknowledged
                    | ObservedStopped
                    | CompletedBeforeCancel
                    | StoppedUnconfirmed
                    | Failed
            ) | (
                Acknowledged,
                ObservedStopped | CompletedBeforeCancel | StoppedUnconfirmed | Failed
            ) | (StoppedUnconfirmed, ObservedStopped | Failed)
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProcessInstance {
    pub pid: u64,
    pub start_generation: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Envelope {
    pub schema_version: u32,
    pub request_id: String,
    pub session_id: String,
    pub turn_id: Option<String>,
    pub epoch: u64,
    pub sequence: u64,
    pub principal_scope: PrincipalScope,
    pub source: EventSource,
    pub policy_version: String,
    pub consent_epoch: Option<u64>,
    pub event: String,
    pub payload: Map<String, Value>,
    pub observed_at: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PrincipalScope {
    pub kind: String,
    #[serde(rename = "ref")]
    pub scope_ref: String,
    pub os_session: Option<String>,
    pub account_ref: Option<String>,
    pub channel: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EventSource {
    pub product: ProductId,
    pub component: String,
    pub artifact_digest: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CancellationRecord {
    pub operation_id: String,
    pub epoch: u64,
    pub cancel_epoch: u64,
    pub state: CancellationState,
    pub owner: String,
    pub process_instance: Option<ProcessInstance>,
    pub observation: String,
    pub effect_state: String,
    pub reconcile_intent_id: Option<String>,
    pub response: String,
    pub lease_released: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ModelManifest {
    pub model_id: String,
    pub revision: String,
    pub source_url: String,
    pub source_revision: String,
    pub modality: String,
    pub artifact: Value,
    pub languages: Vec<LanguageRow>,
    pub runtime: String,
    pub offline_capable: bool,
    pub network_hosts: Vec<String>,
    pub acquisition: String,
    pub code_license: String,
    pub weight_license: String,
    pub commercial_use: String,
    pub commercial_conditions: Option<String>,
    pub requires_consent: bool,
    pub effect_classes: Vec<String>,
    pub authority_ceiling: String,
    pub requirements: ModelRequirements,
    pub admission_state: String,
    pub qualification_evidence_refs: Option<Vec<String>>,
    pub known_limitations: Option<Vec<String>>,
    pub serialization: String,
    pub trust_remote_code: bool,
    pub provenance_ref: Option<String>,
    pub streaming_mode: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LanguageRow {
    pub code: String,
    pub variety: Option<String>,
    pub support: String,
    pub evidence: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ModelRequirements {
    pub process_isolation: String,
    pub network_required: bool,
    pub accelerator: String,
    pub min_ram_mb: Option<u64>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConsentRecord {
    pub consent_id: String,
    pub voice_id: String,
    pub subject_ref: String,
    pub relationship: String,
    pub principal_scope_ref: String,
    pub purposes: Vec<String>,
    pub products: Vec<String>,
    pub allowed_engines: Option<Vec<String>>,
    pub scope_note: Option<String>,
    pub valid_from: String,
    pub valid_until: Option<String>,
    pub evidence_digest: String,
    pub status: String,
    pub revoked_at: Option<String>,
    pub consent_epoch: u64,
    pub watermark_required: bool,
    pub reference_artifact_digest: String,
    pub speaker_match: SpeakerMatch,
    pub attestation: ConsentAttestation,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SpeakerMatch {
    pub method: String,
    pub result: String,
    pub evidence_digest: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConsentAttestation {
    pub issuer: IssuerIdentity,
    pub identity_check: String,
    pub statement: ConsentStatement,
    pub bound_fields_digest: String,
    pub nonce: String,
    pub issued_at: String,
    pub signature: DetachedSignature,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct IssuerIdentity {
    pub kind: String,
    pub key_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConsentStatement {
    pub script_id: String,
    pub transcript_match: String,
    pub operator_confirmed: bool,
    pub live_capture: bool,
    pub challenge_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PolicyVerdict {
    pub verdict_id: String,
    pub request_id: String,
    pub epoch: u64,
    pub consent_epoch: Option<u64>,
    pub candidate_decision: CandidateDecision,
    pub enforced_decision: String,
    pub undecidable_resolution: Option<String>,
    pub human_present: bool,
    pub action_class: String,
    pub rule_ids: Vec<String>,
    pub kernel_floor_ids: Option<Vec<String>>,
    pub layers: Vec<PolicyLayer>,
    pub policy_version: String,
    pub inputs_digest: String,
    pub principal_scope_ref: String,
    pub evidence: Option<Vec<EvidenceItem>>,
    pub reason: Option<String>,
    pub stock_voice_catalog_id: Option<String>,
    pub consent_id: Option<String>,
    pub voice_id: Option<String>,
    pub confirmation: Option<ConfirmationRecord>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EvidenceItem {
    pub kind: String,
    #[serde(rename = "ref")]
    pub item_ref: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConfirmationRecord {
    pub confirmer_kind: String,
    pub verification_ref: String,
    pub confirmed_at: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProvenanceEvent {
    pub event_id: String,
    pub request_id: String,
    pub session_id: String,
    pub epoch: u64,
    pub sequence: u64,
    pub journal_seq: u64,
    pub kind: String,
    pub content_digest: String,
    pub prev_digest: Option<String>,
    pub parent_event_id: Option<String>,
    pub model: Option<ProvenanceModel>,
    pub components: Option<ProvenanceComponents>,
    pub intent_state: Option<IntentState>,
    pub actor: String,
    pub retention: String,
    pub retention_days: Option<u64>,
    pub principal_scope_ref: String,
    pub policy_version: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProvenanceModel {
    pub model_id: String,
    pub revision: String,
    pub artifact_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProvenanceComponents {
    pub prompt_digest: Option<String>,
    pub thresholds_digest: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DeliveryOutcome {
    pub delivery_id: String,
    pub intent_id: Option<String>,
    pub request_id: String,
    pub epoch: u64,
    pub epoch_at_activation: u64,
    pub target: DeliveryTarget,
    pub revalidated_before_delivery: Option<bool>,
    pub focus_revalidated_before_delivery: Option<bool>,
    pub outcome: String,
    pub refusal_reason: Option<String>,
    pub platform: Option<String>,
    pub method: Option<String>,
    pub chars_total: u64,
    pub chars_delivered: u64,
    pub clipboard: ClipboardOutcome,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DeliveryTarget {
    pub captured_at_activation: bool,
    pub window_handle: String,
    pub focus_handle: Option<String>,
    pub process_instance: ProcessInstance,
    pub image_path_digest: String,
    pub app_display_name: Option<String>,
    pub integrity_level: Option<String>,
    pub hosted_process_instance: Option<HostedProcessInstance>,
    pub focus_element: Option<FocusElement>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostedProcessInstance {
    pub pid: u64,
    pub start_generation: String,
    pub image_path_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FocusElement {
    pub runtime_id_digest: String,
    pub control_type: String,
    pub is_password: bool,
    pub is_read_only: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ClipboardOutcome {
    pub used: bool,
    pub restored: bool,
    pub history_excluded: Option<bool>,
    pub skipped_reason: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EffectIntent {
    pub intent_id: String,
    pub idempotency_key: String,
    pub owner: String,
    pub action_class: String,
    pub state: IntentState,
    pub verdict_id: String,
    pub principal_scope_ref: String,
    pub epoch: u64,
    pub reconcile_probe: Option<String>,
    pub reconciled_result: Option<String>,
    pub detail_ref: Option<String>,
    pub dispatch: Option<DispatchRecord>,
    pub capability: Option<CapabilityToken>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DispatchRecord {
    pub tool: String,
    pub args_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CapabilityToken {
    pub token_id: String,
    pub issuer: String,
    pub session_ref: String,
    pub tool: String,
    pub args_digest: String,
    pub nonce: String,
    pub issued_at: String,
    pub expires_at: String,
    pub single_use: bool,
    pub signature: DetachedSignature,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NetworkManifest {
    pub schema_version: u32,
    pub product: ProductId,
    pub surface: String,
    pub mode: String,
    pub allowed_hosts: Vec<String>,
    pub forbid_auto_download: bool,
    pub forbid_default_telemetry: bool,
    pub ssrf_block_private_ips: bool,
    pub loopback_ports: Option<Vec<u16>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExportProvenance {
    pub schema_version: u32,
    pub export_id: String,
    pub project_id: Option<String>,
    pub product: String,
    pub artifact_sha256: String,
    pub duration_ms: u64,
    pub sample_rate_hz: u32,
    pub voice_mode: String,
    pub stock_voice_catalog_id: Option<String>,
    pub consent_id: Option<String>,
    pub consent_epoch: Option<u64>,
    pub voice_id: Option<String>,
    pub model: ProvenanceModel,
    pub watermark: WatermarkProof,
    pub created_at: String,
    pub signature: DetachedSignature,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WatermarkProof {
    pub embedded: bool,
    pub scheme: String,
    pub payload_digest: String,
    pub roundtrip_verified: bool,
}

// ---- Pattern & format helpers ----

fn is_sha256_prefixed(s: &str) -> bool {
    s.strip_prefix("sha256:").is_some_and(is_lower_hex_64)
}

fn is_lower_hex_64(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

fn is_policy_version(s: &str) -> bool {
    if is_sha256_prefixed(s) {
        return true;
    }
    let Some((name, ver)) = s.split_once('@') else {
        return false;
    };
    if name.is_empty()
        || name.len() > 64
        || !name.as_bytes()[0].is_ascii_lowercase()
        || !name
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
    {
        return false;
    }
    let parts: Vec<&str> = ver.split('.').collect();
    parts.len() == 3
        && parts
            .iter()
            .all(|p| !p.is_empty() && p.bytes().all(|b| b.is_ascii_digit()))
}

fn is_rfc3339_utc_z(s: &str) -> bool {
    if !s.ends_with('Z') || s.len() < 20 {
        return false;
    }
    let b = s.as_bytes();
    let basic_ok = b[4] == b'-' && b[7] == b'-' && b[10] == b'T' && b[13] == b':' && b[16] == b':';
    if !basic_ok {
        return false;
    }
    parse_ts(s).is_some()
}

fn parse_ts(s: &str) -> Option<DateTime<FixedOffset>> {
    DateTime::parse_from_rfc3339(s).ok()
}

fn is_id_chars(s: &str, min_len: usize, max_len: usize) -> bool {
    s.len() >= min_len
        && s.len() <= max_len
        && s.bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'.' | b'_' | b':' | b'-'))
}

fn is_len(s: &str, min_len: usize, max_len: usize) -> bool {
    let n = s.chars().count();
    n >= min_len && n <= max_len
}

fn is_snake_ident(s: &str, max_len: usize) -> bool {
    !s.is_empty()
        && s.len() <= max_len
        && s.as_bytes()[0].is_ascii_lowercase()
        && s.bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'_')
}

fn is_process_instance_valid(p: &ProcessInstance) -> bool {
    p.pid >= 1
        && !p.start_generation.is_empty()
        && p.start_generation.len() <= 20
        && p.start_generation.bytes().all(|b| b.is_ascii_digit())
}

fn is_sig_shape_valid(sig: &DetachedSignature) -> bool {
    sig.alg == "ed25519"
        && sig.key_id.len() >= 3
        && sig.key_id.len() <= 64
        && sig
            .key_id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b':' | b'.' | b'_' | b'-'))
        && sig.value.len() == 86
        && sig
            .value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
}

fn has_unique_items<T: Eq + std::hash::Hash>(items: &[T]) -> bool {
    let mut set = HashSet::with_capacity(items.len());
    items.iter().all(|i| set.insert(i))
}

/// Validates schema/shape invariants (`Draft 2020-12` equivalent) for any of the 10 contracts.
pub fn validate_shape(schema: &str, value: &Value) -> Result<(), String> {
    match schema {
        "envelope" => {
            let env: Envelope = serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if env.schema_version != 1 {
                return Err("schema_version must be 1".into());
            }
            if !is_id_chars(&env.request_id, 8, 128) || !is_id_chars(&env.session_id, 8, 128) {
                return Err("invalid request_id or session_id".into());
            }
            if let Some(t) = &env.turn_id {
                if !is_id_chars(t, 1, 128) {
                    return Err("invalid turn_id".into());
                }
            }
            if !is_len(&env.principal_scope.scope_ref, 1, 128) {
                return Err("invalid principal_scope.ref".into());
            }
            match env.principal_scope.kind.as_str() {
                "desktop_user" => {
                    let Some(os) = &env.principal_scope.os_session else {
                        return Err("desktop_user requires os_session".into());
                    };
                    if !is_len(os, 1, 64)
                        || env.principal_scope.account_ref.is_some()
                        || env.principal_scope.channel.is_some()
                    {
                        return Err("desktop_user scope invalid".into());
                    }
                }
                "tenant" => {
                    let (Some(acct), Some(ch)) = (
                        &env.principal_scope.account_ref,
                        &env.principal_scope.channel,
                    ) else {
                        return Err("tenant requires account_ref and channel".into());
                    };
                    if !is_len(acct, 1, 128)
                        || env.principal_scope.os_session.is_some()
                        || !matches!(
                            ch.as_str(),
                            "web_chat"
                                | "inbox"
                                | "voice_webrtc"
                                | "telephony"
                                | "sip"
                                | "websocket_audio"
                                | "api"
                        )
                    {
                        return Err("tenant scope invalid".into());
                    }
                }
                _ => return Err("unknown principal_scope.kind".into()),
            }
            if !is_snake_ident(&env.source.component, 64) {
                return Err("invalid source.component".into());
            }
            if let Some(d) = &env.source.artifact_digest {
                if !is_sha256_prefixed(d) {
                    return Err("invalid source.artifact_digest".into());
                }
            } else if env.source.component.ends_with("_worker") {
                return Err("worker component requires artifact_digest".into());
            }
            if !is_policy_version(&env.policy_version) {
                return Err("invalid policy_version".into());
            }
            const EVENTS: &[&str] = &[
                "CaptureStarted",
                "CaptureStopped",
                "TranscriptPartial",
                "TranscriptFinal",
                "TextEdited",
                "DeliveryRequested",
                "DeliveryOutcome",
                "RenderRequested",
                "RenderOutcome",
                "ToolProposed",
                "PolicyVerdict",
                "ToolOutcome",
                "EffectIntentRecorded",
                "EffectIntentSettled",
                "CancelRequested",
                "CancelState",
                "OwnershipChanged",
                "ProviderUnavailable",
            ];
            if !EVENTS.contains(&env.event.as_str()) {
                return Err("unknown envelope event".into());
            }
            if matches!(env.event.as_str(), "RenderRequested" | "RenderOutcome")
                && env.consent_epoch.is_none()
            {
                return Err("render event requires consent_epoch".into());
            }
            if env.payload.len() > 64 {
                return Err("payload exceeds maxProperties 64".into());
            }
            if let Some(obs) = &env.observed_at {
                if !is_rfc3339_utc_z(obs) {
                    return Err("invalid observed_at".into());
                }
            }
            let payload_val = Value::Object(env.payload);
            match env.event.as_str() {
                "DeliveryOutcome" => validate_shape("delivery_outcome", &payload_val)?,
                "PolicyVerdict" => validate_shape("policy_verdict", &payload_val)?,
                "CancelState" => validate_shape("cancellation", &payload_val)?,
                "EffectIntentRecorded" | "EffectIntentSettled" => {
                    validate_shape("effect_intent", &payload_val)?
                }
                _ => {}
            }
            Ok(())
        }
        "cancellation" => {
            let c: CancellationRecord =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if !is_len(&c.operation_id, 8, 128) || !is_snake_ident(&c.owner, 64) {
                return Err("invalid operation_id or owner".into());
            }
            if let Some(pi) = &c.process_instance {
                if !is_process_instance_valid(pi) {
                    return Err("invalid process_instance".into());
                }
            }
            if !matches!(
                c.observation.as_str(),
                "none"
                    | "process_exit"
                    | "worker_idle_report"
                    | "native_completion"
                    | "deadline_expired"
            ) {
                return Err("invalid observation".into());
            }
            if !matches!(c.effect_state.as_str(), "none" | "committed" | "unknown") {
                return Err("invalid effect_state".into());
            }
            if let Some(rid) = &c.reconcile_intent_id {
                if !is_len(rid, 8, 128) {
                    return Err("invalid reconcile_intent_id".into());
                }
            }
            if !matches!(
                c.response.as_str(),
                "pending" | "cancelled_result" | "error_request_cancelled" | "completed_result"
            ) {
                return Err("invalid response".into());
            }
            if c.lease_released {
                let ok = matches!(
                    c.state,
                    CancellationState::ObservedStopped | CancellationState::CompletedBeforeCancel
                ) || (c.state == CancellationState::Failed
                    && c.observation == "process_exit");
                if !ok {
                    return Err(
                        "lease_released requires observed stop or crash process_exit".into(),
                    );
                }
            }
            if c.state == CancellationState::ObservedStopped
                && !matches!(
                    c.observation.as_str(),
                    "process_exit" | "worker_idle_report" | "native_completion"
                )
            {
                return Err("observed_stopped requires real stop observation".into());
            }
            if matches!(
                c.state,
                CancellationState::Requested | CancellationState::Acknowledged
            ) && (c.observation != "none" || c.response != "pending" || c.lease_released)
            {
                return Err("non-terminal cancel cannot carry observation/response/release".into());
            }
            if matches!(
                c.state,
                CancellationState::ObservedStopped
                    | CancellationState::CompletedBeforeCancel
                    | CancellationState::StoppedUnconfirmed
                    | CancellationState::Failed
            ) && c.response == "pending"
            {
                return Err("settled/failed cancel requires non-pending response".into());
            }
            if c.effect_state == "unknown" && c.reconcile_intent_id.is_none() {
                return Err("unknown effect_state requires reconcile_intent_id".into());
            }
            Ok(())
        }
        "model_manifest" => {
            let m: ModelManifest =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if !is_len(&m.model_id, 1, 128)
                || !is_len(&m.revision, 1, 128)
                || !m.source_url.starts_with("https://")
                || !is_len(&m.source_revision, 1, 128)
                || !is_len(&m.code_license, 1, 64)
                || !is_len(&m.weight_license, 1, 64)
            {
                return Err("invalid manifest string bounds".into());
            }
            if !matches!(
                m.modality.as_str(),
                "stt"
                    | "tts"
                    | "voice_conversion"
                    | "vad"
                    | "turn_detection"
                    | "diarization"
                    | "enhancement"
                    | "translation"
                    | "alignment"
                    | "llm"
                    | "language_id"
            ) {
                return Err("invalid modality".into());
            }
            // artifact oneOf
            let mut is_provider_managed = false;
            let Some(art_obj) = m.artifact.as_object() else {
                return Err("artifact must be object".into());
            };
            if art_obj.contains_key("provider_managed_digest_unavailable") {
                is_provider_managed = true;
                if art_obj
                    .keys()
                    .any(|k| k != "provider_managed_digest_unavailable" && k != "provider")
                {
                    return Err("extra fields in provider artifact".into());
                }
                if art_obj.get("provider_managed_digest_unavailable") != Some(&Value::Bool(true)) {
                    return Err("provider_managed_digest_unavailable must be true".into());
                }
                let Some(prov) = art_obj.get("provider").and_then(Value::as_str) else {
                    return Err("missing provider".into());
                };
                if !is_len(prov, 1, 128) {
                    return Err("invalid provider".into());
                }
            } else {
                if art_obj
                    .keys()
                    .any(|k| !matches!(k.as_str(), "files" | "bundle_sha256" | "config_sha256"))
                {
                    return Err("extra fields in bundle artifact".into());
                }
                let Some(bundle_sha) = art_obj.get("bundle_sha256").and_then(Value::as_str) else {
                    return Err("missing bundle_sha256".into());
                };
                if !is_lower_hex_64(bundle_sha) {
                    return Err("invalid bundle_sha256".into());
                }
                if let Some(cfg_sha) = art_obj.get("config_sha256") {
                    if !cfg_sha.as_str().is_some_and(is_lower_hex_64) {
                        return Err("invalid config_sha256".into());
                    }
                }
                let Some(files) = art_obj.get("files").and_then(Value::as_array) else {
                    return Err("missing files".into());
                };
                if files.is_empty() || files.len() > 64 {
                    return Err("invalid files count".into());
                }
                for f in files {
                    let Some(fo) = f.as_object() else {
                        return Err("file item must be object".into());
                    };
                    if fo.len() != 3 {
                        return Err("file item requires exact 3 fields".into());
                    }
                    let Some(p) = fo.get("path").and_then(Value::as_str) else {
                        return Err("missing file path".into());
                    };
                    if p.is_empty()
                        || p.len() > 255
                        || p.starts_with('/')
                        || p.contains("..")
                        || !p.bytes().all(|b| {
                            b.is_ascii_alphanumeric() || matches!(b, b'.' | b'_' | b'/' | b'-')
                        })
                    {
                        return Err("invalid bundle file path".into());
                    }
                    if !fo
                        .get("sha256")
                        .and_then(Value::as_str)
                        .is_some_and(is_lower_hex_64)
                    {
                        return Err("invalid file sha256".into());
                    }
                    if !fo
                        .get("size_bytes")
                        .and_then(Value::as_u64)
                        .is_some_and(|n| n >= 1)
                    {
                        return Err("invalid file size_bytes".into());
                    }
                }
            }
            if m.languages.is_empty() || m.languages.len() > 256 {
                return Err("invalid languages count".into());
            }
            for lang in &m.languages {
                if !matches!(
                    lang.support.as_str(),
                    "documented" | "measured" | "unsupported"
                ) {
                    return Err("invalid language support".into());
                }
                if lang.support == "measured" && lang.evidence.is_none() {
                    return Err("measured language requires evidence".into());
                }
            }
            if !matches!(
                m.runtime.as_str(),
                "ggml" | "onnx" | "pytorch" | "ctranslate2" | "mlx" | "provider_api" | "other"
            ) {
                return Err("invalid runtime".into());
            }
            if m.network_hosts.len() > 16 {
                return Err("too many network_hosts".into());
            }
            if !matches!(
                m.acquisition.as_str(),
                "bundled" | "pre_staged" | "user_imported" | "user_initiated_download"
            ) {
                return Err("invalid acquisition".into());
            }
            if !matches!(
                m.commercial_use.as_str(),
                "allowed" | "prohibited" | "unknown" | "conditional"
            ) {
                return Err("invalid commercial_use".into());
            }
            if m.effect_classes.is_empty() || !has_unique_items(&m.effect_classes) {
                return Err("invalid effect_classes".into());
            }
            for ec in &m.effect_classes {
                if !matches!(
                    ec.as_str(),
                    "text_hypothesis"
                        | "audio_artifact"
                        | "voice_embedding"
                        | "segment_labels"
                        | "text_suggestion"
                        | "structured_proposal"
                        | "language_label"
                ) {
                    return Err("unknown effect_class".into());
                }
            }
            if m.authority_ceiling != "evidence_only" {
                return Err("authority_ceiling must be evidence_only".into());
            }
            if !matches!(
                m.requirements.process_isolation.as_str(),
                "in_process" | "subprocess" | "container"
            ) || !matches!(
                m.requirements.accelerator.as_str(),
                "none" | "optional_gpu" | "gpu_required" | "apple_silicon_only"
            ) {
                return Err("invalid requirements".into());
            }
            if !matches!(
                m.admission_state.as_str(),
                "pending" | "admitted" | "rejected" | "revoked"
            ) {
                return Err("invalid admission_state".into());
            }
            if !matches!(
                m.serialization.as_str(),
                "gguf"
                    | "onnx"
                    | "safetensors"
                    | "ctranslate2"
                    | "pickle"
                    | "provider_managed"
                    | "other"
            ) {
                return Err("invalid serialization".into());
            }
            if let Some(sm) = &m.streaming_mode {
                if !matches!(
                    sm.as_str(),
                    "none" | "chunked" | "native_streaming" | "full_duplex"
                ) {
                    return Err("invalid streaming_mode".into());
                }
            }
            // Conditional rules
            if m.offline_capable && (!m.network_hosts.is_empty() || m.requirements.network_required)
            {
                return Err("offline_capable model cannot declare network hosts".into());
            }
            if (m.runtime == "provider_api" || is_provider_managed) && m.offline_capable {
                return Err("provider model cannot be offline_capable".into());
            }
            if m.commercial_use == "conditional" && m.commercial_conditions.is_none() {
                return Err("conditional commercial_use requires commercial_conditions".into());
            }
            if m.admission_state == "admitted" {
                if m.commercial_use == "unknown" {
                    return Err("admitted model cannot have unknown commercial_use".into());
                }
                if matches!(m.serialization.as_str(), "pickle" | "other") || m.trust_remote_code {
                    return Err("admitted model forbids pickle/other/trust_remote_code".into());
                }
            }
            if m.acquisition == "user_imported"
                && !m
                    .provenance_ref
                    .as_deref()
                    .is_some_and(|s| is_len(s, 1, 512))
            {
                return Err("user_imported model requires provenance_ref".into());
            }
            Ok(())
        }
        "consent_record" => {
            let c: ConsentRecord =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if !is_len(&c.consent_id, 8, 128)
                || !is_len(&c.voice_id, 8, 128)
                || !is_len(&c.principal_scope_ref, 1, 128)
            {
                return Err("invalid consent ids".into());
            }
            let Some(sref) = c.subject_ref.strip_prefix("subj-") else {
                return Err("invalid subject_ref prefix".into());
            };
            if sref.len() < 6
                || sref.len() > 64
                || !sref
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
            {
                return Err("invalid subject_ref".into());
            }
            if !matches!(
                c.relationship.as_str(),
                "self" | "consenting_third_party" | "licensed_voice_actor"
            ) {
                return Err("invalid relationship".into());
            }
            if c.purposes.is_empty()
                || !has_unique_items(&c.purposes)
                || !c.purposes.iter().all(|p| {
                    matches!(
                        p.as_str(),
                        "personal" | "commercial" | "internal_evaluation"
                    )
                })
            {
                return Err("invalid purposes".into());
            }
            if c.products.is_empty()
                || !has_unique_items(&c.products)
                || !c
                    .products
                    .iter()
                    .all(|p| matches!(p.as_str(), "wisprstudio" | "klaint" | "omalla"))
            {
                return Err("invalid products".into());
            }
            if !is_rfc3339_utc_z(&c.valid_from) {
                return Err("invalid valid_from".into());
            }
            if let Some(vu) = &c.valid_until {
                if !is_rfc3339_utc_z(vu) {
                    return Err("invalid valid_until".into());
                }
            }
            if let Some(ra) = &c.revoked_at {
                if !is_rfc3339_utc_z(ra) {
                    return Err("invalid revoked_at".into());
                }
            }
            if !is_sha256_prefixed(&c.evidence_digest)
                || !is_sha256_prefixed(&c.reference_artifact_digest)
            {
                return Err("invalid consent digests".into());
            }
            if !matches!(c.status.as_str(), "active" | "revoked" | "expired") {
                return Err("invalid status".into());
            }
            if !matches!(
                c.speaker_match.method.as_str(),
                "speaker_verification_model" | "human_review"
            ) || !matches!(
                c.speaker_match.result.as_str(),
                "match" | "no_match" | "not_checked"
            ) {
                return Err("invalid speaker_match".into());
            }
            if let Some(ed) = &c.speaker_match.evidence_digest {
                if !is_sha256_prefixed(ed) {
                    return Err("invalid speaker_match.evidence_digest".into());
                }
            }
            // attestation
            let att = &c.attestation;
            if !matches!(
                att.issuer.kind.as_str(),
                "studio_operator" | "consent_service"
            ) {
                return Err("invalid issuer.kind".into());
            }
            if !matches!(
                att.identity_check.as_str(),
                "in_person_id_check" | "live_video_id_check"
            ) {
                return Err("invalid identity_check".into());
            }
            if !matches!(
                att.statement.transcript_match.as_str(),
                "match" | "mismatch"
            ) || !att.statement.live_capture
                || !is_sha256_prefixed(&att.statement.challenge_digest)
            {
                return Err("invalid attestation.statement".into());
            }
            let Some((scr_name, scr_ver)) = att.statement.script_id.split_once('@') else {
                return Err("invalid script_id".into());
            };
            if scr_name.len() < 3
                || scr_name.len() > 48
                || !scr_name
                    .bytes()
                    .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
                || scr_ver.is_empty()
                || !scr_ver.bytes().all(|b| b.is_ascii_digit())
            {
                return Err("invalid script_id pattern".into());
            }
            if !is_sha256_prefixed(&att.bound_fields_digest)
                || att.nonce.len() < 22
                || att.nonce.len() > 64
                || !is_rfc3339_utc_z(&att.issued_at)
                || !is_sig_shape_valid(&att.signature)
            {
                return Err("invalid attestation fields".into());
            }
            if att.issuer.kind == "consent_service"
                && !att.issuer.key_id.starts_with("consent-svc:")
            {
                return Err("consent_service requires consent-svc: key_id".into());
            }
            if att.issuer.kind == "studio_operator" && !att.issuer.key_id.starts_with("op-key:") {
                return Err("studio_operator requires op-key: key_id".into());
            }
            // allOf rules
            if (c.status == "revoked") != c.revoked_at.is_some() {
                return Err("revoked status and revoked_at must co-occur".into());
            }
            if c.status == "expired" && c.valid_until.is_none() {
                return Err("expired requires valid_until".into());
            }
            if c.relationship == "consenting_third_party" && !c.watermark_required {
                return Err("third_party requires watermark".into());
            }
            if c.status == "active"
                && matches!(c.relationship.as_str(), "self" | "consenting_third_party")
                && c.speaker_match.result != "match"
            {
                return Err("active personal consent requires speaker match".into());
            }
            if c.status == "active"
                && (att.statement.transcript_match != "match" || !att.statement.operator_confirmed)
            {
                return Err(
                    "active consent requires transcript match and operator confirmation".into(),
                );
            }
            if (c.purposes.iter().any(|p| p == "commercial")
                || matches!(
                    c.relationship.as_str(),
                    "consenting_third_party" | "licensed_voice_actor"
                ))
                && (!c.watermark_required || att.issuer.kind != "consent_service")
            {
                return Err(
                    "commercial/third-party/actor requires watermark and consent_service".into(),
                );
            }
            Ok(())
        }
        "policy_verdict" => {
            let v: PolicyVerdict =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if !is_len(&v.verdict_id, 8, 128)
                || !is_len(&v.request_id, 8, 128)
                || !is_len(&v.principal_scope_ref, 1, 128)
                || !is_policy_version(&v.policy_version)
                || !is_sha256_prefixed(&v.inputs_digest)
            {
                return Err("invalid policy_verdict header fields".into());
            }
            if !matches!(v.enforced_decision.as_str(), "ALLOW" | "ASK" | "DENY") {
                return Err("invalid enforced_decision".into());
            }
            if let Some(ur) = &v.undecidable_resolution {
                if !matches!(ur.as_str(), "ASK" | "DENY") {
                    return Err("invalid undecidable_resolution".into());
                }
            }
            if !matches!(
                v.action_class.as_str(),
                "read"
                    | "reversible_write"
                    | "irreversible_write"
                    | "money"
                    | "credential_use"
                    | "publication"
                    | "text_delivery"
                    | "voice_render"
                    | "file_export"
            ) {
                return Err("invalid action_class".into());
            }
            if !has_unique_items(&v.rule_ids) || v.layers.len() > 16 {
                return Err("invalid rule_ids or layers".into());
            }
            if let Some(ev) = &v.evidence {
                if ev.len() > 32
                    || !ev.iter().all(|e| {
                        matches!(
                            e.kind.as_str(),
                            "model_confidence"
                                | "scanner_finding"
                                | "retrieved_document"
                                | "user_confirmation"
                                | "consent_record"
                                | "target_binding"
                        ) && is_len(&e.item_ref, 1, 256)
                    })
                {
                    return Err("invalid evidence".into());
                }
            }
            if let Some(cat) = &v.stock_voice_catalog_id {
                if !cat.starts_with("catalog:") || cat.len() <= 8 || cat.len() > 128 {
                    return Err("invalid stock_voice_catalog_id".into());
                }
            }
            if let Some(conf) = &v.confirmation {
                if !matches!(
                    conf.confirmer_kind.as_str(),
                    "operator" | "step_up_verified_holder"
                ) || !is_len(&conf.verification_ref, 8, 256)
                    || !is_rfc3339_utc_z(&conf.confirmed_at)
                {
                    return Err("invalid confirmation".into());
                }
            }
            if v.candidate_decision == CandidateDecision::Undecidable {
                if v.undecidable_resolution.is_none()
                    || !matches!(v.enforced_decision.as_str(), "ASK" | "DENY")
                {
                    return Err("UNDECIDABLE requires ASK/DENY resolution".into());
                }
                if !v.human_present
                    && (v.undecidable_resolution.as_deref() != Some("DENY")
                        || v.enforced_decision != "DENY")
                {
                    return Err("unattended UNDECIDABLE must resolve to DENY".into());
                }
            }
            if v.enforced_decision == "ALLOW" {
                let ok = v.candidate_decision == CandidateDecision::Allow
                    || (v.candidate_decision == CandidateDecision::Ask && v.confirmation.is_some());
                if !ok {
                    return Err("enforced ALLOW widens candidate without confirmation".into());
                }
                if v.action_class != "read" && v.rule_ids.is_empty() {
                    return Err("non-read ALLOW requires rule_ids".into());
                }
                if v.action_class == "voice_render" {
                    let stock_ok = v.stock_voice_catalog_id.is_some();
                    let consent_ok = v.consent_epoch.is_some()
                        && v.consent_id.is_some()
                        && v.voice_id.is_some()
                        && v.evidence
                            .as_ref()
                            .is_some_and(|ev| ev.iter().any(|e| e.kind == "consent_record"));
                    if !stock_ok && !consent_ok {
                        return Err("voice_render ALLOW requires stock catalog or consent".into());
                    }
                }
                if v.action_class == "text_delivery"
                    && !v
                        .evidence
                        .as_ref()
                        .is_some_and(|ev| ev.iter().any(|e| e.kind == "target_binding"))
                {
                    return Err("text_delivery ALLOW requires target_binding".into());
                }
            }
            if v.confirmation.is_some()
                && matches!(
                    v.action_class.as_str(),
                    "money" | "credential_use" | "irreversible_write" | "publication"
                )
                && !v.human_present
            {
                return Err("high-risk confirmation requires human_present".into());
            }
            Ok(())
        }
        "provenance_event" => {
            let p: ProvenanceEvent =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if !is_len(&p.event_id, 8, 128)
                || !is_len(&p.request_id, 8, 128)
                || !is_len(&p.session_id, 8, 128)
                || !is_sha256_prefixed(&p.content_digest)
                || !is_len(&p.principal_scope_ref, 1, 128)
                || !is_policy_version(&p.policy_version)
            {
                return Err("invalid provenance_event fields".into());
            }
            if let Some(pd) = &p.prev_digest {
                if !is_sha256_prefixed(pd) {
                    return Err("invalid prev_digest".into());
                }
            }
            if !matches!(
                p.kind.as_str(),
                "audio_metadata"
                    | "audio_not_persisted"
                    | "raw_hypothesis"
                    | "normalized_text"
                    | "user_edit"
                    | "rewrite_suggestion"
                    | "interpretation"
                    | "policy_verdict"
                    | "dispatch"
                    | "outcome"
                    | "ownership_change"
                    | "consent_granted"
                    | "consent_revoked"
                    | "consent_check"
            ) {
                return Err("invalid provenance kind".into());
            }
            if !matches!(
                p.actor.as_str(),
                "user"
                    | "speech_worker"
                    | "rewrite_worker"
                    | "policy"
                    | "delivery_owner"
                    | "render_owner"
                    | "broker"
                    | "human_operator"
                    | "dialogue_engine"
            ) {
                return Err("invalid actor".into());
            }
            if !matches!(
                p.retention.as_str(),
                "session_only" | "bounded_days" | "user_controlled" | "audit_tombstone"
            ) {
                return Err("invalid retention".into());
            }
            if let Some(m) = &p.model {
                if !is_len(&m.model_id, 1, 128)
                    || !is_len(&m.revision, 1, 128)
                    || !(is_lower_hex_64(&m.artifact_sha256)
                        || m.artifact_sha256 == "PROVIDER_MANAGED_DIGEST_UNAVAILABLE")
                {
                    return Err("invalid provenance model".into());
                }
            }
            if matches!(
                p.kind.as_str(),
                "normalized_text"
                    | "user_edit"
                    | "rewrite_suggestion"
                    | "interpretation"
                    | "dispatch"
                    | "outcome"
                    | "policy_verdict"
            ) && p.parent_event_id.is_none()
            {
                return Err("derived provenance kind requires parent_event_id".into());
            }
            if matches!(
                p.kind.as_str(),
                "raw_hypothesis" | "rewrite_suggestion" | "interpretation"
            ) && p.model.is_none()
            {
                return Err("hypothesis/rewrite/interpretation requires model".into());
            }
            if matches!(p.kind.as_str(), "rewrite_suggestion" | "interpretation")
                && p.components.is_none()
            {
                return Err("rewrite/interpretation requires components".into());
            }
            if matches!(p.kind.as_str(), "dispatch" | "outcome") && p.intent_state.is_none() {
                return Err("dispatch/outcome requires intent_state".into());
            }
            if p.retention == "bounded_days"
                && !p.retention_days.is_some_and(|d| (1..=3650).contains(&d))
            {
                return Err("bounded_days requires retention_days 1..=3650".into());
            }
            Ok(())
        }
        "delivery_outcome" => {
            let d: DeliveryOutcome =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if !is_len(&d.delivery_id, 8, 128) || !is_len(&d.request_id, 8, 128) {
                return Err("invalid delivery ids".into());
            }
            if !d.target.captured_at_activation
                || !d.target.window_handle.strip_prefix("0x").is_some_and(|h| {
                    !h.is_empty() && h.len() <= 16 && h.bytes().all(|b| b.is_ascii_hexdigit())
                })
                || !is_process_instance_valid(&d.target.process_instance)
                || !is_sha256_prefixed(&d.target.image_path_digest)
            {
                return Err("invalid delivery target".into());
            }
            if let Some(fe) = &d.target.focus_element {
                if !is_sha256_prefixed(&fe.runtime_id_digest)
                    || fe.control_type.is_empty()
                    || fe.control_type.len() > 32
                    || !fe.control_type.bytes().all(|b| b.is_ascii_alphabetic())
                {
                    return Err("invalid focus_element".into());
                }
            }
            if let Some(plat) = &d.platform {
                if !matches!(
                    plat.as_str(),
                    "windows" | "macos" | "linux_x11" | "linux_wayland"
                ) {
                    return Err("invalid platform".into());
                }
            }
            if !matches!(
                d.outcome.as_str(),
                "delivered_confirmed"
                    | "posted_unconfirmed"
                    | "refused"
                    | "partial"
                    | "failed"
                    | "unknown"
            ) {
                return Err("invalid delivery outcome".into());
            }
            if let Some(rr) = &d.refusal_reason {
                if !matches!(
                    rr.as_str(),
                    "target_changed"
                        | "target_gone"
                        | "pid_reused"
                        | "focus_lost"
                        | "focus_moved"
                        | "os_session_changed"
                        | "secure_desktop"
                        | "elevated_target"
                        | "password_field"
                        | "not_editable"
                        | "identity_unreadable"
                        | "stale_epoch"
                        | "binding_expired"
                        | "policy_denied"
                        | "user_cancelled"
                        | "wayland_copy_fallback"
                ) {
                    return Err("invalid refusal_reason".into());
                }
            }
            if let Some(m) = &d.method {
                if !matches!(
                    m.as_str(),
                    "clipboard_paste" | "send_input_unicode" | "uia_value_pattern" | "none"
                ) {
                    return Err("invalid delivery method".into());
                }
            }
            // clipboard rules
            if !d.clipboard.used {
                if d.clipboard.restored || d.clipboard.skipped_reason.as_deref() != Some("not_used")
                {
                    return Err(
                        "unused clipboard must not be restored and must cite not_used".into(),
                    );
                }
            } else if d.clipboard.history_excluded != Some(true) {
                return Err("used clipboard must set history_excluded = true".into());
            }
            // outcome conditional rules
            if (d.outcome == "refused") != d.refusal_reason.is_some() {
                return Err("refused outcome and refusal_reason must co-occur".into());
            }
            if d.outcome == "refused"
                && (d.chars_delivered != 0 || d.method.as_deref() != Some("none"))
            {
                return Err("refused delivery must deliver 0 chars with method none".into());
            }
            if matches!(
                d.outcome.as_str(),
                "delivered_confirmed" | "posted_unconfirmed" | "partial"
            ) {
                if d.revalidated_before_delivery != Some(true)
                    || d.focus_revalidated_before_delivery != Some(true)
                    || !matches!(
                        d.method.as_deref(),
                        Some("clipboard_paste" | "send_input_unicode" | "uia_value_pattern")
                    )
                {
                    return Err("delivering outcome requires revalidation and active method".into());
                }
                let Some(fe) = &d.target.focus_element else {
                    return Err("delivering outcome requires focus_element".into());
                };
                if fe.is_password || fe.is_read_only {
                    return Err("cannot deliver into password or read-only field".into());
                }
            }
            if d.outcome == "partial" && d.chars_delivered < 1 {
                return Err("partial delivery requires chars_delivered >= 1".into());
            }
            Ok(())
        }
        "effect_intent" => {
            let e: EffectIntent =
                serde_json::from_value(value.clone()).map_err(|err| err.to_string())?;
            if !is_len(&e.intent_id, 8, 128)
                || !is_id_chars(&e.idempotency_key, 16, 128)
                || !is_len(&e.verdict_id, 8, 128)
                || !is_len(&e.principal_scope_ref, 1, 128)
            {
                return Err("invalid effect_intent identifiers".into());
            }
            if !matches!(
                e.owner.as_str(),
                "studio_export_commit" | "klaint_broker" | "omalla_gateway"
            ) {
                return Err("invalid owner".into());
            }
            if !matches!(
                e.action_class.as_str(),
                "file_export"
                    | "reversible_write"
                    | "irreversible_write"
                    | "money"
                    | "credential_use"
                    | "publication"
            ) {
                return Err("invalid action_class for effect_intent".into());
            }
            if let Some(rr) = &e.reconciled_result {
                if !matches!(rr.as_str(), "effect_present" | "effect_absent") {
                    return Err("invalid reconciled_result".into());
                }
            }
            if let Some(disp) = &e.dispatch {
                if !is_sha256_prefixed(&disp.args_digest) {
                    return Err("invalid dispatch.args_digest".into());
                }
            }
            if let Some(cap) = &e.capability {
                if !cap.token_id.starts_with("cap-")
                    || cap.issuer != "klaint_broker"
                    || !cap.session_ref.starts_with("ses-")
                    || !is_sha256_prefixed(&cap.args_digest)
                    || cap.nonce.len() < 22
                    || !is_rfc3339_utc_z(&cap.issued_at)
                    || !is_rfc3339_utc_z(&cap.expires_at)
                    || !cap.single_use
                    || !is_sig_shape_valid(&cap.signature)
                {
                    return Err("invalid capability token".into());
                }
            }
            if matches!(e.state, IntentState::Unknown | IntentState::Reconciled)
                && e.reconcile_probe.is_none()
            {
                return Err("unknown/reconciled requires reconcile_probe".into());
            }
            if (e.state == IntentState::Reconciled) != e.reconciled_result.is_some() {
                return Err("reconciled state and reconciled_result must co-occur".into());
            }
            if e.owner == "studio_export_commit" && e.action_class != "file_export" {
                return Err("studio_export_commit only commits file_export".into());
            }
            if e.owner == "klaint_broker"
                && (e.action_class == "file_export"
                    || e.capability.is_none()
                    || e.dispatch.is_none())
            {
                return Err(
                    "klaint_broker requires capability, dispatch, and non-file_export".into(),
                );
            }
            if e.owner == "omalla_gateway"
                && (e.action_class == "file_export" || e.dispatch.is_none())
            {
                return Err("omalla_gateway requires dispatch and non-file_export".into());
            }
            Ok(())
        }
        "network_manifest" => {
            let n: NetworkManifest =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if n.schema_version != 1
                || !n.forbid_auto_download
                || !n.forbid_default_telemetry
                || !has_unique_items(&n.allowed_hosts)
            {
                return Err("invalid network_manifest invariants".into());
            }
            match n.mode.as_str() {
                "offline_strict" => {
                    if !n.allowed_hosts.is_empty() || n.loopback_ports.is_some() {
                        return Err("offline_strict forbids hosts and loopback_ports".into());
                    }
                }
                "loopback_only" => {
                    if !n.allowed_hosts.is_empty() {
                        return Err("loopback_only forbids external hosts".into());
                    }
                }
                "allowlisted_hosts" => {
                    if n.allowed_hosts.is_empty() {
                        return Err("allowlisted_hosts requires at least one host".into());
                    }
                }
                _ => return Err("unknown network_manifest mode".into()),
            }
            Ok(())
        }
        "export_provenance" => {
            let ep: ExportProvenance =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if ep.schema_version != 1
                || !is_len(&ep.export_id, 8, 128)
                || !matches!(ep.product.as_str(), "wisprstudio" | "klaint" | "omalla")
                || !is_sha256_prefixed(&ep.artifact_sha256)
                || ep.duration_ms < 1
                || !matches!(
                    ep.sample_rate_hz,
                    8000 | 16000 | 22050 | 24000 | 32000 | 44100 | 48000
                )
                || !ep.watermark.embedded
                || ep.watermark.scheme != "wispral-qim-v1"
                || !is_sha256_prefixed(&ep.watermark.payload_digest)
                || !ep.watermark.roundtrip_verified
                || !is_rfc3339_utc_z(&ep.created_at)
                || !is_sig_shape_valid(&ep.signature)
            {
                return Err("invalid export_provenance fields".into());
            }
            match ep.voice_mode.as_str() {
                "stock_catalog" => {
                    if !ep
                        .stock_voice_catalog_id
                        .as_deref()
                        .is_some_and(|s| s.starts_with("catalog:"))
                        || ep.consent_id.is_some()
                        || ep.consent_epoch.is_some()
                    {
                        return Err("stock_catalog requires catalog id and forbids consent".into());
                    }
                }
                "authorized_clone" => {
                    if ep.consent_id.is_none()
                        || ep.consent_epoch.is_none()
                        || ep.voice_id.is_none()
                        || ep.stock_voice_catalog_id.is_some()
                    {
                        return Err(
                            "authorized_clone requires consent fields and forbids catalog".into(),
                        );
                    }
                }
                _ => return Err("unknown voice_mode".into()),
            }
            Ok(())
        }
        other => Err(format!("unknown schema {other}")),
    }
}

/// Validates cross-field runtime invariants (`run_conformance.py::runtime_errors`) on shape-valid instances.
pub fn validate_runtime(
    schema: &str,
    value: &Value,
    trusted_keys: &HashMap<String, String>,
) -> Result<(), String> {
    match schema {
        "delivery_outcome" => {
            let d: DeliveryOutcome =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if d.chars_delivered > d.chars_total {
                return Err("chars_delivered exceeds chars_total".into());
            }
            if d.outcome == "delivered_confirmed" && d.chars_delivered != d.chars_total {
                return Err("delivered_confirmed requires full delivery".into());
            }
            if d.outcome == "partial"
                && !(1 <= d.chars_delivered && d.chars_delivered < d.chars_total)
            {
                return Err("partial requires 1 <= delivered < total".into());
            }
            if d.epoch_at_activation != d.epoch
                && !(d.outcome == "refused" && d.refusal_reason.as_deref() == Some("stale_epoch"))
            {
                return Err("stale activation epoch must be refused as stale_epoch".into());
            }
            Ok(())
        }
        "consent_record" => {
            let c: ConsentRecord =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            if let Some(vu) = &c.valid_until {
                if vu <= &c.valid_from {
                    return Err("valid_until must follow valid_from".into());
                }
            }
            let expected_digest = compute_consent_bound_digest(value).map_err(|e| e.to_string())?;
            if c.attestation.bound_fields_digest != expected_digest {
                return Err("bound_fields_digest mismatch".into());
            }
            if c.attestation.signature.key_id != c.attestation.issuer.key_id {
                return Err("signature key_id differs from issuer key_id".into());
            }
            if trusted_keys.get(&c.attestation.issuer.key_id) != Some(&c.attestation.issuer.kind) {
                return Err("issuer key is not registered in trusted_keys".into());
            }
            Ok(())
        }
        "effect_intent" => {
            let e: EffectIntent =
                serde_json::from_value(value.clone()).map_err(|err| err.to_string())?;
            if let Some(cap) = &e.capability {
                let Some(disp) = &e.dispatch else {
                    return Err("capability requires dispatch".into());
                };
                if cap.tool != disp.tool || cap.args_digest != disp.args_digest {
                    return Err("dispatched tool or arguments differ from capability".into());
                }
                let issued = parse_ts(&cap.issued_at).ok_or("invalid issued_at")?;
                let expires = parse_ts(&cap.expires_at).ok_or("invalid expires_at")?;
                let lifetime = (expires - issued).num_milliseconds() as f64 / 1000.0;
                if !(lifetime > 0.0 && lifetime <= CAPABILITY_MAX_SECONDS) {
                    return Err("capability lifetime must be within (0, 60] seconds".into());
                }
            }
            Ok(())
        }
        "model_manifest" => {
            let m: ModelManifest =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            let mut seen = HashSet::new();
            for row in &m.languages {
                if !seen.insert((row.code.clone(), row.variety.clone())) {
                    return Err("duplicate (code, variety) language rows".into());
                }
            }
            Ok(())
        }
        "policy_verdict" => {
            let v: PolicyVerdict =
                serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
            let composed = compose_layers(&v.layers).map_err(|e| e.to_string())?;
            if composed != v.candidate_decision {
                return Err("candidate_decision does not equal composition of layers".into());
            }
            Ok(())
        }
        _ => Ok(()),
    }
}

pub fn validate_sequence(machine: &str, states: &[String]) -> bool {
    if states.is_empty() {
        return false;
    }
    match machine {
        "effect_intent" => {
            let parsed: Option<Vec<IntentState>> = states
                .iter()
                .map(|s| serde_json::from_value(Value::String(s.clone())).ok())
                .collect();
            let Some(seq) = parsed else {
                return false;
            };
            if seq[0] != IntentState::Pending {
                return false;
            }
            seq.windows(2).all(|w| w[0].may_become(w[1]))
        }
        "cancellation" => {
            let parsed: Option<Vec<CancellationState>> = states
                .iter()
                .map(|s| serde_json::from_value(Value::String(s.clone())).ok())
                .collect();
            let Some(seq) = parsed else {
                return false;
            };
            if seq[0] != CancellationState::Requested {
                return false;
            }
            seq.windows(2).all(|w| w[0].may_become(w[1]))
        }
        _ => false,
    }
}

pub fn validate_bundle(
    intents: &[Value],
    verdicts: &[Value],
    trusted_keys: &HashMap<String, String>,
) -> Result<(), String> {
    let mut parsed_verdicts = HashMap::new();
    for v_val in verdicts {
        validate_shape("policy_verdict", v_val)?;
        validate_runtime("policy_verdict", v_val, trusted_keys)?;
        let v: PolicyVerdict = serde_json::from_value(v_val.clone()).map_err(|e| e.to_string())?;
        parsed_verdicts.insert(v.verdict_id.clone(), v);
    }

    let mut open_keys: HashMap<(String, String, String), usize> = HashMap::new();
    let mut nonces = HashSet::new();

    for i_val in intents {
        validate_shape("effect_intent", i_val)?;
        validate_runtime("effect_intent", i_val, trusted_keys)?;
        let i: EffectIntent = serde_json::from_value(i_val.clone()).map_err(|e| e.to_string())?;
        if i.state.is_open() {
            let key = (
                i.principal_scope_ref.clone(),
                i.owner.clone(),
                i.idempotency_key.clone(),
            );
            *open_keys.entry(key).or_insert(0) += 1;
        }
        let Some(v) = parsed_verdicts.get(&i.verdict_id) else {
            return Err("intent references unknown verdict".into());
        };
        if v.action_class != i.action_class {
            return Err("verdict action_class mismatch".into());
        }
        if v.principal_scope_ref != i.principal_scope_ref {
            return Err("verdict principal mismatch".into());
        }
        if v.enforced_decision != "ALLOW" {
            return Err("intent dispatched without enforced ALLOW".into());
        }
        if let Some(cap) = &i.capability {
            if !nonces.insert(cap.nonce.clone()) {
                return Err("capability nonce replayed".into());
            }
        }
    }

    if open_keys.values().any(|&count| count > 1) {
        return Err("duplicate non-terminal intent for (principal, owner, idempotency_key)".into());
    }
    Ok(())
}
