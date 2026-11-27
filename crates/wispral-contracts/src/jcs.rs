//! RFC 8785 JSON Canonicalization Scheme (JCS) + Unicode NFC + SHA-256 digesting.
//!
//! Guarantees byte-for-byte identical digests across Rust, Python (`json.dumps` sorted),
//! and TypeScript/Node. Signed capabilities and idempotency keys reject IEEE-754 floats
//! (`canonicalize_jcs_no_floats`) so cross-runtime float formatting differences can never
//! cause signature mismatches or replay splits.

use serde::Serialize;
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum JcsError {
    #[error("JSON serialization failed: {0}")]
    Serialization(String),
    #[error("floating-point numbers are forbidden in signed or idempotent contract payloads")]
    FloatingPointForbidden,
    #[error("duplicate object key after Unicode NFC normalization: `{0}`")]
    DuplicateKey(String),
}

/// Canonicalizes a `serde_json::Value` into RFC 8785 JCS UTF-8 bytes with NFC-normalized strings.
pub fn canonicalize_jcs(value: &Value) -> Result<Vec<u8>, JcsError> {
    canonicalize_inner(value, false)
}

/// Canonicalizes a `serde_json::Value` into RFC 8785 JCS UTF-8 bytes while rejecting any
/// non-integer number (`f64`), enforcing cross-language deterministic capability hashing.
pub fn canonicalize_jcs_no_floats(value: &Value) -> Result<Vec<u8>, JcsError> {
    canonicalize_inner(value, true)
}

pub fn sha256_jcs<T: Serialize>(value: &T, forbid_floats: bool) -> Result<String, JcsError> {
    let v = serde_json::to_value(value).map_err(|e| JcsError::Serialization(e.to_string()))?;
    let bytes = canonicalize_inner(&v, forbid_floats)?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

fn canonicalize_inner(value: &Value, forbid_floats: bool) -> Result<Vec<u8>, JcsError> {
    let mut out = Vec::with_capacity(256);
    write_value(value, forbid_floats, &mut out)?;
    Ok(out)
}

fn write_jcs_string(raw: &str, out: &mut Vec<u8>) {
    let nfc: String = raw.nfc().collect();
    out.push(b'"');
    for ch in nfc.chars() {
        match ch {
            '"' => out.extend_from_slice(b"\\\""),
            '\\' => out.extend_from_slice(b"\\\\"),
            '\u{0008}' => out.extend_from_slice(b"\\b"),
            '\u{0009}' => out.extend_from_slice(b"\\t"),
            '\u{000A}' => out.extend_from_slice(b"\\n"),
            '\u{000C}' => out.extend_from_slice(b"\\f"),
            '\u{000D}' => out.extend_from_slice(b"\\r"),
            c if (c as u32) < 0x20 => {
                out.extend_from_slice(format!("\\u{:04x}", c as u32).as_bytes());
            }
            c => {
                let mut buf = [0u8; 4];
                out.extend_from_slice(c.encode_utf8(&mut buf).as_bytes());
            }
        }
    }
    out.push(b'"');
}

fn write_value(value: &Value, forbid_floats: bool, out: &mut Vec<u8>) -> Result<(), JcsError> {
    match value {
        Value::Null => out.extend_from_slice(b"null"),
        Value::Bool(true) => out.extend_from_slice(b"true"),
        Value::Bool(false) => out.extend_from_slice(b"false"),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                out.extend_from_slice(i.to_string().as_bytes());
            } else if let Some(u) = n.as_u64() {
                out.extend_from_slice(u.to_string().as_bytes());
            } else {
                if forbid_floats {
                    return Err(JcsError::FloatingPointForbidden);
                }
                let f = n
                    .as_f64()
                    .ok_or_else(|| JcsError::Serialization("non-finite number".into()))?;
                if !f.is_finite() {
                    return Err(JcsError::Serialization("non-finite float".into()));
                }
                if f == 0.0 {
                    out.push(b'0');
                } else {
                    out.extend_from_slice(n.to_string().as_bytes());
                }
            }
        }
        Value::String(s) => write_jcs_string(s, out),
        Value::Array(items) => {
            out.push(b'[');
            for (idx, item) in items.iter().enumerate() {
                if idx > 0 {
                    out.push(b',');
                }
                write_value(item, forbid_floats, out)?;
            }
            out.push(b']');
        }
        Value::Object(map) => {
            out.push(b'{');
            let mut entries: Vec<(String, &Value)> =
                map.iter().map(|(k, v)| (k.nfc().collect(), v)).collect();
            // RFC 8785 §3.2.3: sort object member names by UTF-16 code units
            entries.sort_by(|(a, _), (b, _)| a.encode_utf16().cmp(b.encode_utf16()));
            for idx in 1..entries.len() {
                if entries[idx - 1].0 == entries[idx].0 {
                    return Err(JcsError::DuplicateKey(entries[idx].0.clone()));
                }
            }
            for (idx, (k, v)) in entries.iter().enumerate() {
                if idx > 0 {
                    out.push(b',');
                }
                write_jcs_string(k, out);
                out.push(b':');
                write_value(v, forbid_floats, out)?;
            }
            out.push(b'}');
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn jcs_sorts_utf16_keys_normalizes_nfc_and_rejects_floats_when_configured() {
        let val = json!({
            "z": 1,
            "a": "مشروع",
            "nested": { "b": [true, false, null], "a": -42 }
        });
        let canon = String::from_utf8(canonicalize_jcs_no_floats(&val).unwrap()).unwrap();
        assert_eq!(
            canon,
            r#"{"a":"مشروع","nested":{"a":-42,"b":[true,false,null]},"z":1}"#
        );

        let with_float = json!({"amount": 12.5});
        assert_eq!(
            canonicalize_jcs_no_floats(&with_float).unwrap_err(),
            JcsError::FloatingPointForbidden
        );
    }
}
