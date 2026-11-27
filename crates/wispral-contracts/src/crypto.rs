//! Pure-Rust Ed25519 key generation, signing, and verification for Wispral contracts
//! (`consent_record`, `effect_intent.capability`, and `export_provenance`).

use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine as _;
use ed25519_dalek::{Signature, Signer as _, SigningKey, VerifyingKey};
use rand_core::OsRng;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use thiserror::Error;

use crate::jcs::{canonicalize_jcs_no_floats, sha256_jcs};

pub const DOMAIN_CONSENT_RECORD: &[u8] = b"wispral:consent_record:v1:";
pub const DOMAIN_CAPABILITY_TOKEN: &[u8] = b"wispral:capability_token:v1:";
pub const DOMAIN_EXPORT_PROVENANCE: &[u8] = b"wispral:export_provenance:v1:";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DetachedSignature {
    pub alg: String,
    pub key_id: String,
    pub value: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum CryptoError {
    #[error("unsupported signature algorithm: {0}")]
    UnsupportedAlgorithm(String),
    #[error("invalid base64url key or signature encoding")]
    InvalidEncoding,
    #[error("invalid Ed25519 public key or signature bytes")]
    InvalidKeyOrSignature,
    #[error("Ed25519 signature verification failed")]
    VerificationFailed,
    #[error("canonicalization error: {0}")]
    Canonicalization(String),
}

pub struct Ed25519Keypair {
    pub key_id: String,
    signing_key: SigningKey,
}

impl Ed25519Keypair {
    pub fn generate(key_id: impl Into<String>) -> Self {
        let signing_key = SigningKey::generate(&mut OsRng);
        Self {
            key_id: key_id.into(),
            signing_key,
        }
    }

    pub fn from_secret_bytes(key_id: impl Into<String>, secret: [u8; 32]) -> Self {
        Self {
            key_id: key_id.into(),
            signing_key: SigningKey::from_bytes(&secret),
        }
    }

    pub fn public_key_base64url(&self) -> String {
        URL_SAFE_NO_PAD.encode(self.signing_key.verifying_key().to_bytes())
    }

    pub fn sign_bytes(&self, message: &[u8]) -> DetachedSignature {
        let sig: Signature = self.signing_key.sign(message);
        DetachedSignature {
            alg: "ed25519".to_owned(),
            key_id: self.key_id.clone(),
            value: URL_SAFE_NO_PAD.encode(sig.to_bytes()),
        }
    }
}

pub fn verify_detached_signature(
    public_key_b64url: &str,
    message: &[u8],
    sig: &DetachedSignature,
) -> Result<(), CryptoError> {
    if sig.alg != "ed25519" {
        return Err(CryptoError::UnsupportedAlgorithm(sig.alg.clone()));
    }
    let pk_bytes = URL_SAFE_NO_PAD
        .decode(public_key_b64url)
        .map_err(|_| CryptoError::InvalidEncoding)?;
    let pk_arr: [u8; 32] = pk_bytes
        .try_into()
        .map_err(|_| CryptoError::InvalidKeyOrSignature)?;
    let verifying_key =
        VerifyingKey::from_bytes(&pk_arr).map_err(|_| CryptoError::InvalidKeyOrSignature)?;

    let sig_bytes = URL_SAFE_NO_PAD
        .decode(&sig.value)
        .map_err(|_| CryptoError::InvalidEncoding)?;
    let sig_arr: [u8; 64] = sig_bytes
        .try_into()
        .map_err(|_| CryptoError::InvalidKeyOrSignature)?;
    let signature = Signature::from_bytes(&sig_arr);

    verifying_key
        .verify_strict(message, &signature)
        .map_err(|_| CryptoError::VerificationFailed)
}

/// Domain-separated canonical JCS (`no_floats`) Ed25519 signing helper for contract payloads.
pub fn sign_domain_json(
    keypair: &Ed25519Keypair,
    domain_prefix: &[u8],
    payload: &Value,
) -> Result<DetachedSignature, CryptoError> {
    let jcs = canonicalize_jcs_no_floats(payload)
        .map_err(|e| CryptoError::Canonicalization(e.to_string()))?;
    let mut msg = Vec::with_capacity(domain_prefix.len() + jcs.len());
    msg.extend_from_slice(domain_prefix);
    msg.extend_from_slice(&jcs);
    Ok(keypair.sign_bytes(&msg))
}

/// Domain-separated canonical JCS (`no_floats`) Ed25519 strict verification helper.
pub fn verify_domain_json(
    public_key_b64url: &str,
    domain_prefix: &[u8],
    payload: &Value,
    sig: &DetachedSignature,
) -> Result<(), CryptoError> {
    let jcs = canonicalize_jcs_no_floats(payload)
        .map_err(|e| CryptoError::Canonicalization(e.to_string()))?;
    let mut msg = Vec::with_capacity(domain_prefix.len() + jcs.len());
    msg.extend_from_slice(domain_prefix);
    msg.extend_from_slice(&jcs);
    verify_detached_signature(public_key_b64url, &msg, sig)
}

/// Computes `attestation.bound_fields_digest` over the exact signed subset of a `consent_record`,
/// matching `docs/engineering/contracts/run_conformance.py::bound_digest` byte-for-byte.
pub fn compute_consent_bound_digest(record: &Value) -> Result<String, CryptoError> {
    let obj = record
        .as_object()
        .ok_or_else(|| CryptoError::Canonicalization("consent_record must be an object".into()))?;
    let att = obj
        .get("attestation")
        .and_then(Value::as_object)
        .ok_or_else(|| CryptoError::Canonicalization("missing attestation object".into()))?;

    const COVERED: &[&str] = &[
        "consent_id",
        "subject_ref",
        "voice_id",
        "relationship",
        "principal_scope_ref",
        "purposes",
        "products",
        "allowed_engines",
        "valid_from",
        "valid_until",
        "evidence_digest",
        "consent_epoch",
        "watermark_required",
        "reference_artifact_digest",
        "speaker_match",
    ];

    let mut fields = serde_json::Map::new();
    for &k in COVERED {
        fields.insert(k.to_owned(), obj.get(k).cloned().unwrap_or(Value::Null));
    }
    let mut att_filtered = serde_json::Map::new();
    for (k, v) in att {
        if k != "bound_fields_digest" && k != "signature" {
            att_filtered.insert(k.clone(), v.clone());
        }
    }
    fields.insert("attestation".to_owned(), Value::Object(att_filtered));

    sha256_jcs(&json!(fields), true).map_err(|e| CryptoError::Canonicalization(e.to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ed25519_detached_signature_round_trips_with_86_char_base64url() {
        let kp = Ed25519Keypair::from_secret_bytes("op-key:studio-001", [7u8; 32]);
        let pk = kp.public_key_base64url();
        let sig = kp.sign_bytes(b"sha256:0123456789abcdef");
        assert_eq!(sig.value.len(), 86);
        verify_detached_signature(&pk, b"sha256:0123456789abcdef", &sig).unwrap();
        assert_eq!(
            verify_detached_signature(&pk, b"tampered", &sig).unwrap_err(),
            CryptoError::VerificationFailed
        );
    }
}
