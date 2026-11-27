#![forbid(unsafe_code)]
//! Official pure-Rust SDK for **Omalla** (part of **Wispral** by **Halfmoon**).
//!
//! Zero external crate dependencies: provides strongly-typed request/response
//! models, RFC 8785 JSON Canonicalization Scheme (`args_digest`) with strict
//! floating-point rejection (`OM-T5`), constant-time raw-byte Standard Webhooks
//! and Omalla HMAC verification (`OM-T3`), streaming frame parsing, and a
//! synchronous HTTP/1.1 client with pluggable transport.

use std::collections::BTreeMap;
use std::error::Error;
use std::fmt;
use std::io::{Read, Write};
use std::net::TcpStream;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

pub const SDK_VERSION: &str = "0.1.0";
pub const MAX_SAFE_INTEGER: i64 = 9_007_199_254_740_991;
pub const DEFAULT_WEBHOOK_SKEW_SEC: i64 = 300;

/* ------------------------------------------------------------------ */
/* Errors                                                              */
/* ------------------------------------------------------------------ */

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SdkError {
    Configuration(String),
    JsonParse(String),
    FloatRejected(String),
    IntegerOutOfRange(i64),
    WebhookRejected(String),
    Http {
        status: u16,
        code: String,
        message: String,
    },
    Transport(String),
}

impl fmt::Display for SdkError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Configuration(msg) => write!(f, "configuration error: {msg}"),
            Self::JsonParse(msg) => write!(f, "JSON parse error: {msg}"),
            Self::FloatRejected(tok) => {
                write!(
                    f,
                    "floating-point number '{tok}' is rejected in JCS payloads"
                )
            }
            Self::IntegerOutOfRange(val) => {
                write!(f, "integer {val} exceeds IEEE-754 safe integer range")
            }
            Self::WebhookRejected(reason) => write!(f, "webhook rejected: {reason}"),
            Self::Http {
                status,
                code,
                message,
            } => write!(f, "{status} {code}: {message}"),
            Self::Transport(msg) => write!(f, "transport error: {msg}"),
        }
    }
}

impl Error for SdkError {}

/* ------------------------------------------------------------------ */
/* JSON value & RFC 8785 JCS Canonicalizer (OM-T5)                     */
/* ------------------------------------------------------------------ */

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JsonValue {
    Null,
    Bool(bool),
    Integer(i64),
    String(String),
    Array(Vec<JsonValue>),
    Object(Vec<(String, JsonValue)>),
}

impl JsonValue {
    pub fn object(entries: Vec<(&str, JsonValue)>) -> Self {
        Self::Object(
            entries
                .into_iter()
                .map(|(k, v)| (k.to_string(), v))
                .collect(),
        )
    }

    pub fn get(&self, key: &str) -> Option<&JsonValue> {
        match self {
            Self::Object(entries) => entries.iter().rev().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self {
            Self::String(s) => Some(s.as_str()),
            _ => None,
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match self {
            Self::Bool(b) => Some(*b),
            _ => None,
        }
    }

    pub fn as_i64(&self) -> Option<i64> {
        match self {
            Self::Integer(n) => Some(*n),
            _ => None,
        }
    }
}

/// Canonicalizes a [`JsonValue`] according to RFC 8785 (JCS), ordering object
/// keys lexicographically by UTF-16 code units and rejecting non-safe integers.
pub fn canonicalize_jcs(value: &JsonValue) -> Result<String, SdkError> {
    let mut out = String::new();
    write_jcs(value, &mut out)?;
    Ok(out)
}

/// Parses raw JSON strictly (rejecting any float literal such as `1.5`, `1.0`,
/// or `1e3`) and returns the lowercase hex SHA-256 of its RFC 8785 canonical form.
pub fn args_digest_json(raw_json: &str) -> Result<String, SdkError> {
    let parsed = parse_json_strict(raw_json)?;
    args_digest(&parsed)
}

/// Computes the lowercase hex SHA-256 digest of the RFC 8785 JCS form of `value`.
pub fn args_digest(value: &JsonValue) -> Result<String, SdkError> {
    let canonical = canonicalize_jcs(value)?;
    Ok(hex_encode(&sha256_bytes(canonical.as_bytes())))
}

fn write_jcs(value: &JsonValue, out: &mut String) -> Result<(), SdkError> {
    match value {
        JsonValue::Null => out.push_str("null"),
        JsonValue::Bool(true) => out.push_str("true"),
        JsonValue::Bool(false) => out.push_str("false"),
        JsonValue::Integer(n) => {
            if n.unsigned_abs() > MAX_SAFE_INTEGER as u64 {
                return Err(SdkError::IntegerOutOfRange(*n));
            }
            out.push_str(&n.to_string());
        }
        JsonValue::String(s) => write_jcs_string(s, out),
        JsonValue::Array(items) => {
            out.push('[');
            for (idx, item) in items.iter().enumerate() {
                if idx > 0 {
                    out.push(',');
                }
                write_jcs(item, out)?;
            }
            out.push(']');
        }
        JsonValue::Object(entries) => {
            let mut dedup: Vec<(&str, &JsonValue)> = Vec::with_capacity(entries.len());
            for (k, v) in entries {
                if let Some(pos) = dedup.iter().position(|(ek, _)| *ek == k.as_str()) {
                    dedup[pos] = (k.as_str(), v);
                } else {
                    dedup.push((k.as_str(), v));
                }
            }
            dedup.sort_by(|(a, _), (b, _)| a.encode_utf16().cmp(b.encode_utf16()));
            out.push('{');
            for (idx, (k, v)) in dedup.iter().enumerate() {
                if idx > 0 {
                    out.push(',');
                }
                write_jcs_string(k, out);
                out.push(':');
                write_jcs(v, out)?;
            }
            out.push('}');
        }
    }
    Ok(())
}

fn write_jcs_string(s: &str, out: &mut String) {
    out.push('"');
    for ch in s.chars() {
        let code = ch as u32;
        match code {
            0x08 => out.push_str("\\b"),
            0x09 => out.push_str("\\t"),
            0x0A => out.push_str("\\n"),
            0x0C => out.push_str("\\f"),
            0x0D => out.push_str("\\r"),
            0x22 => out.push_str("\\\""),
            0x5C => out.push_str("\\\\"),
            0x00..=0x1F => {
                let _ = fmt::Write::write_fmt(out, format_args!("\\u{code:04x}"));
            }
            _ => out.push(ch),
        }
    }
    out.push('"');
}

/// Strict JSON parser that rejects floating-point numbers (`OM-T5`).
pub fn parse_json_strict(input: &str) -> Result<JsonValue, SdkError> {
    let mut parser = JsonParser {
        bytes: input.as_bytes(),
        src: input,
        pos: 0,
    };
    let value = parser.parse_value()?;
    parser.skip_ws();
    if parser.pos != parser.bytes.len() {
        return Err(SdkError::JsonParse(format!(
            "unexpected trailing byte at offset {}",
            parser.pos
        )));
    }
    Ok(value)
}

/// Permissive JSON parser for API responses where numeric metrics may contain floats
/// (converts whole floats to integers or preserves stringified representation if needed).
pub fn parse_json_response(input: &str) -> Result<JsonValue, SdkError> {
    let mut parser = JsonParser {
        bytes: input.as_bytes(),
        src: input,
        pos: 0,
    };
    let value = parser.parse_value_permissive()?;
    parser.skip_ws();
    if parser.pos != parser.bytes.len() {
        return Err(SdkError::JsonParse(format!(
            "unexpected trailing byte at offset {}",
            parser.pos
        )));
    }
    Ok(value)
}

struct JsonParser<'a> {
    bytes: &'a [u8],
    src: &'a str,
    pos: usize,
}

impl<'a> JsonParser<'a> {
    fn skip_ws(&mut self) {
        while self.pos < self.bytes.len() {
            match self.bytes[self.pos] {
                b' ' | b'\t' | b'\r' | b'\n' => self.pos += 1,
                _ => break,
            }
        }
    }

    fn peek(&self) -> Option<u8> {
        self.bytes.get(self.pos).copied()
    }

    fn parse_value(&mut self) -> Result<JsonValue, SdkError> {
        self.parse_inner(false)
    }

    fn parse_value_permissive(&mut self) -> Result<JsonValue, SdkError> {
        self.parse_inner(true)
    }

    fn parse_inner(&mut self, allow_response_floats: bool) -> Result<JsonValue, SdkError> {
        self.skip_ws();
        let b = self
            .peek()
            .ok_or_else(|| SdkError::JsonParse("unexpected end of JSON".to_string()))?;
        match b {
            b'n' => {
                self.expect_literal(b"null")?;
                Ok(JsonValue::Null)
            }
            b't' => {
                self.expect_literal(b"true")?;
                Ok(JsonValue::Bool(true))
            }
            b'f' => {
                self.expect_literal(b"false")?;
                Ok(JsonValue::Bool(false))
            }
            b'"' => Ok(JsonValue::String(self.parse_string()?)),
            b'[' => {
                self.pos += 1;
                self.skip_ws();
                let mut items = Vec::new();
                if self.peek() == Some(b']') {
                    self.pos += 1;
                    return Ok(JsonValue::Array(items));
                }
                loop {
                    items.push(self.parse_inner(allow_response_floats)?);
                    self.skip_ws();
                    match self.peek() {
                        Some(b',') => self.pos += 1,
                        Some(b']') => {
                            self.pos += 1;
                            break;
                        }
                        _ => {
                            return Err(SdkError::JsonParse(format!(
                                "expected ',' or ']' at offset {}",
                                self.pos
                            )))
                        }
                    }
                }
                Ok(JsonValue::Array(items))
            }
            b'{' => {
                self.pos += 1;
                self.skip_ws();
                let mut entries = Vec::new();
                if self.peek() == Some(b'}') {
                    self.pos += 1;
                    return Ok(JsonValue::Object(entries));
                }
                loop {
                    self.skip_ws();
                    if self.peek() != Some(b'"') {
                        return Err(SdkError::JsonParse(format!(
                            "expected object key string at offset {}",
                            self.pos
                        )));
                    }
                    let key = self.parse_string()?;
                    self.skip_ws();
                    if self.peek() != Some(b':') {
                        return Err(SdkError::JsonParse(format!(
                            "expected ':' after key at offset {}",
                            self.pos
                        )));
                    }
                    self.pos += 1;
                    let val = self.parse_inner(allow_response_floats)?;
                    entries.push((key, val));
                    self.skip_ws();
                    match self.peek() {
                        Some(b',') => self.pos += 1,
                        Some(b'}') => {
                            self.pos += 1;
                            break;
                        }
                        _ => {
                            return Err(SdkError::JsonParse(format!(
                                "expected ',' or '}}' at offset {}",
                                self.pos
                            )))
                        }
                    }
                }
                Ok(JsonValue::Object(entries))
            }
            b'-' | b'0'..=b'9' => self.parse_number(allow_response_floats),
            _ => Err(SdkError::JsonParse(format!(
                "unexpected character at offset {}",
                self.pos
            ))),
        }
    }

    fn expect_literal(&mut self, lit: &[u8]) -> Result<(), SdkError> {
        if self.bytes.get(self.pos..self.pos + lit.len()) == Some(lit) {
            self.pos += lit.len();
            Ok(())
        } else {
            Err(SdkError::JsonParse(format!(
                "invalid literal at offset {}",
                self.pos
            )))
        }
    }

    fn parse_number(&mut self, allow_response_floats: bool) -> Result<JsonValue, SdkError> {
        let start = self.pos;
        if self.peek() == Some(b'-') {
            self.pos += 1;
        }
        let digit_start = self.pos;
        while let Some(b'0'..=b'9') = self.peek() {
            self.pos += 1;
        }
        if self.pos == digit_start {
            return Err(SdkError::JsonParse(format!(
                "invalid number at offset {start}"
            )));
        }
        if self.bytes[digit_start] == b'0' && (self.pos - digit_start) > 1 {
            return Err(SdkError::JsonParse(format!(
                "leading zero in number at offset {start}"
            )));
        }
        let mut is_float = false;
        if self.peek() == Some(b'.') {
            is_float = true;
            self.pos += 1;
            let frac_start = self.pos;
            while let Some(b'0'..=b'9') = self.peek() {
                self.pos += 1;
            }
            if self.pos == frac_start {
                return Err(SdkError::JsonParse(format!(
                    "malformed fraction at offset {start}"
                )));
            }
        }
        if matches!(self.peek(), Some(b'e' | b'E')) {
            is_float = true;
            self.pos += 1;
            if matches!(self.peek(), Some(b'+' | b'-')) {
                self.pos += 1;
            }
            let exp_start = self.pos;
            while let Some(b'0'..=b'9') = self.peek() {
                self.pos += 1;
            }
            if self.pos == exp_start {
                return Err(SdkError::JsonParse(format!(
                    "malformed exponent at offset {start}"
                )));
            }
        }
        let token = &self.src[start..self.pos];
        if is_float {
            if allow_response_floats {
                let parsed: f64 = token
                    .parse()
                    .map_err(|_| SdkError::JsonParse(format!("invalid float '{token}'")))?;
                return Ok(JsonValue::Integer(parsed.round() as i64));
            }
            return Err(SdkError::FloatRejected(token.to_string()));
        }
        if token == "-0" {
            return Ok(JsonValue::Integer(0));
        }
        let int_val: i64 = token
            .parse()
            .map_err(|_| SdkError::JsonParse(format!("integer overflow in '{token}'")))?;
        if int_val.unsigned_abs() > MAX_SAFE_INTEGER as u64 {
            return Err(SdkError::IntegerOutOfRange(int_val));
        }
        Ok(JsonValue::Integer(int_val))
    }

    fn parse_string(&mut self) -> Result<String, SdkError> {
        if self.peek() != Some(b'"') {
            return Err(SdkError::JsonParse("expected '\"'".to_string()));
        }
        self.pos += 1;
        let mut out = String::new();
        while self.pos < self.bytes.len() {
            let b = self.bytes[self.pos];
            if b == b'"' {
                self.pos += 1;
                return Ok(out);
            }
            if b == b'\\' {
                self.pos += 1;
                let esc = self
                    .peek()
                    .ok_or_else(|| SdkError::JsonParse("unterminated escape".to_string()))?;
                self.pos += 1;
                match esc {
                    b'"' => out.push('"'),
                    b'\\' => out.push('\\'),
                    b'/' => out.push('/'),
                    b'b' => out.push('\u{0008}'),
                    b'f' => out.push('\u{000C}'),
                    b'n' => out.push('\n'),
                    b'r' => out.push('\r'),
                    b't' => out.push('\t'),
                    b'u' => {
                        let hi = self.read_hex4()?;
                        if (0xD800..=0xDBFF).contains(&hi) {
                            if self.bytes.get(self.pos..self.pos + 2) != Some(b"\\u") {
                                return Err(SdkError::JsonParse(
                                    "unpaired high UTF-16 surrogate".to_string(),
                                ));
                            }
                            self.pos += 2;
                            let lo = self.read_hex4()?;
                            if !(0xDC00..=0xDFFF).contains(&lo) {
                                return Err(SdkError::JsonParse(
                                    "invalid low UTF-16 surrogate".to_string(),
                                ));
                            }
                            let scalar =
                                0x10000 + (((hi as u32 - 0xD800) << 10) | (lo as u32 - 0xDC00));
                            let ch = char::from_u32(scalar).ok_or_else(|| {
                                SdkError::JsonParse("invalid Unicode scalar".to_string())
                            })?;
                            out.push(ch);
                        } else {
                            let ch = char::from_u32(hi as u32).ok_or_else(|| {
                                SdkError::JsonParse("invalid Unicode escape".to_string())
                            })?;
                            out.push(ch);
                        }
                    }
                    _ => {
                        return Err(SdkError::JsonParse(format!(
                            "unknown escape '\\{}'",
                            esc as char
                        )))
                    }
                }
            } else {
                let tail = &self.src[self.pos..];
                let ch = tail
                    .chars()
                    .next()
                    .ok_or_else(|| SdkError::JsonParse("invalid UTF-8".to_string()))?;
                if (ch as u32) < 0x20 {
                    return Err(SdkError::JsonParse(
                        "unescaped control character in JSON string".to_string(),
                    ));
                }
                out.push(ch);
                self.pos += ch.len_utf8();
            }
        }
        Err(SdkError::JsonParse("unterminated JSON string".to_string()))
    }

    fn read_hex4(&mut self) -> Result<u16, SdkError> {
        let slice = self
            .src
            .get(self.pos..self.pos + 4)
            .ok_or_else(|| SdkError::JsonParse("truncated \\u escape".to_string()))?;
        let val = u16::from_str_radix(slice, 16)
            .map_err(|_| SdkError::JsonParse(format!("invalid hex escape '{slice}'")))?;
        self.pos += 4;
        Ok(val)
    }
}

/* ------------------------------------------------------------------ */
/* Pure-Rust SHA-256, HMAC-SHA256 & Constant-Time Webhook Verifier     */
/* ------------------------------------------------------------------ */

const SHA256_K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

pub fn sha256_bytes(data: &[u8]) -> [u8; 32] {
    let mut state: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];

    let bit_len = (data.len() as u64).wrapping_mul(8);
    let mut padded = Vec::with_capacity((data.len() + 9).div_ceil(64) * 64);
    padded.extend_from_slice(data);
    padded.push(0x80);
    while (padded.len() % 64) != 56 {
        padded.push(0x00);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());

    for chunk in padded.chunks_exact(64) {
        let mut w = [0u32; 64];
        for (i, slot) in w.iter_mut().enumerate().take(16) {
            let j = i * 4;
            *slot = u32::from_be_bytes([chunk[j], chunk[j + 1], chunk[j + 2], chunk[j + 3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }

        let mut a = state[0];
        let mut b = state[1];
        let mut c = state[2];
        let mut d = state[3];
        let mut e = state[4];
        let mut f = state[5];
        let mut g = state[6];
        let mut h = state[7];

        for i in 0..64 {
            let sum1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = h
                .wrapping_add(sum1)
                .wrapping_add(ch)
                .wrapping_add(SHA256_K[i])
                .wrapping_add(w[i]);
            let sum0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = sum0.wrapping_add(maj);

            h = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        state[0] = state[0].wrapping_add(a);
        state[1] = state[1].wrapping_add(b);
        state[2] = state[2].wrapping_add(c);
        state[3] = state[3].wrapping_add(d);
        state[4] = state[4].wrapping_add(e);
        state[5] = state[5].wrapping_add(f);
        state[6] = state[6].wrapping_add(g);
        state[7] = state[7].wrapping_add(h);
    }

    let mut out = [0u8; 32];
    for (i, word) in state.iter().enumerate() {
        out[i * 4..(i + 1) * 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

pub fn hmac_sha256(key: &[u8], message: &[u8]) -> [u8; 32] {
    let mut key_block = [0u8; 64];
    if key.len() > 64 {
        let hashed = sha256_bytes(key);
        key_block[..32].copy_from_slice(&hashed);
    } else {
        key_block[..key.len()].copy_from_slice(key);
    }

    let mut ipad = [0x36u8; 64];
    let mut opad = [0x5cu8; 64];
    for i in 0..64 {
        ipad[i] ^= key_block[i];
        opad[i] ^= key_block[i];
    }

    let mut inner_input = Vec::with_capacity(64 + message.len());
    inner_input.extend_from_slice(&ipad);
    inner_input.extend_from_slice(message);
    let inner_hash = sha256_bytes(&inner_input);

    let mut outer_input = [0u8; 96];
    outer_input[..64].copy_from_slice(&opad);
    outer_input[64..].copy_from_slice(&inner_hash);
    sha256_bytes(&outer_input)
}

pub fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut diff = 0u8;
    for (x, y) in a.iter().zip(b.iter()) {
        diff |= x ^ y;
    }
    diff == 0
}

pub fn hex_encode(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        out.push(HEX[(b >> 4) as usize] as char);
        out.push(HEX[(b & 0x0f) as usize] as char);
    }
    out
}

pub fn hex_decode(hex: &str) -> Result<Vec<u8>, SdkError> {
    if hex.len() % 2 != 0 {
        return Err(SdkError::WebhookRejected(
            "odd-length hex string".to_string(),
        ));
    }
    let mut out = Vec::with_capacity(hex.len() / 2);
    let bytes = hex.as_bytes();
    for i in (0..bytes.len()).step_by(2) {
        let hi = hex_nibble(bytes[i])?;
        let lo = hex_nibble(bytes[i + 1])?;
        out.push((hi << 4) | lo);
    }
    Ok(out)
}

fn hex_nibble(b: u8) -> Result<u8, SdkError> {
    match b {
        b'0'..=b'9' => Ok(b - b'0'),
        b'a'..=b'f' => Ok(b - b'a' + 10),
        b'A'..=b'F' => Ok(b - b'A' + 10),
        _ => Err(SdkError::WebhookRejected(
            "invalid hex character".to_string(),
        )),
    }
}

pub fn base64_encode(bytes: &[u8]) -> String {
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let b0 = chunk[0] as u32;
        let b1 = chunk.get(1).copied().unwrap_or(0) as u32;
        let b2 = chunk.get(2).copied().unwrap_or(0) as u32;
        let n = (b0 << 16) | (b1 << 8) | b2;
        out.push(TABLE[((n >> 18) & 0x3f) as usize] as char);
        out.push(TABLE[((n >> 12) & 0x3f) as usize] as char);
        if chunk.len() > 1 {
            out.push(TABLE[((n >> 6) & 0x3f) as usize] as char);
        } else {
            out.push('=');
        }
        if chunk.len() > 2 {
            out.push(TABLE[(n & 0x3f) as usize] as char);
        } else {
            out.push('=');
        }
    }
    out
}

pub fn base64_decode(input: &str) -> Result<Vec<u8>, SdkError> {
    let clean: Vec<u8> = input
        .bytes()
        .filter(|b| !matches!(b, b' ' | b'\r' | b'\n' | b'\t'))
        .collect();
    if clean.is_empty() {
        return Ok(Vec::new());
    }
    if clean.len() % 4 != 0 {
        return Err(SdkError::WebhookRejected(
            "invalid base64 length".to_string(),
        ));
    }
    let mut out = Vec::with_capacity((clean.len() / 4) * 3);
    for chunk in clean.chunks_exact(4) {
        let c0 = b64_val(chunk[0])?;
        let c1 = b64_val(chunk[1])?;
        let pad2 = chunk[2] == b'=';
        let pad3 = chunk[3] == b'=';
        let c2 = if pad2 { 0 } else { b64_val(chunk[2])? };
        let c3 = if pad3 { 0 } else { b64_val(chunk[3])? };
        let n = ((c0 as u32) << 18) | ((c1 as u32) << 12) | ((c2 as u32) << 6) | (c3 as u32);
        out.push(((n >> 16) & 0xff) as u8);
        if !pad2 {
            out.push(((n >> 8) & 0xff) as u8);
        }
        if !pad3 {
            out.push((n & 0xff) as u8);
        }
    }
    Ok(out)
}

fn b64_val(b: u8) -> Result<u8, SdkError> {
    match b {
        b'A'..=b'Z' => Ok(b - b'A'),
        b'a'..=b'z' => Ok(b - b'a' + 26),
        b'0'..=b'9' => Ok(b - b'0' + 52),
        b'+' | b'-' => Ok(62),
        b'/' | b'_' => Ok(63),
        _ => Err(SdkError::WebhookRejected(
            "invalid base64 character".to_string(),
        )),
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WebhookVerification {
    pub event_key: Option<String>,
    pub scheme: &'static str,
}

/// Verifies Standard Webhooks (`webhook-id`, `webhook-timestamp` ±300 s,
/// `webhook-signature` `v1,<base64>`) or Omalla raw-byte HMAC (`x-omalla-signature`).
pub fn verify_webhook_signature(
    raw_body: &[u8],
    headers: &BTreeMap<String, String>,
    secret: &str,
    now_unix_sec: Option<i64>,
) -> Result<WebhookVerification, SdkError> {
    let now_sec = match now_unix_sec {
        Some(ts) => ts,
        None => SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs() as i64)
            .unwrap_or(0),
    };

    let lower: BTreeMap<String, &str> = headers
        .iter()
        .map(|(k, v)| (k.to_ascii_lowercase(), v.as_str()))
        .collect();

    let std_id = lower
        .get("webhook-id")
        .or_else(|| lower.get("svix-id"))
        .copied();
    let std_ts = lower
        .get("webhook-timestamp")
        .or_else(|| lower.get("svix-timestamp"))
        .copied();
    let std_sig = lower
        .get("webhook-signature")
        .or_else(|| lower.get("svix-signature"))
        .copied();

    if std_id.is_some() || std_ts.is_some() || std_sig.is_some() {
        let (Some(id), Some(ts_raw), Some(sig_raw)) = (std_id, std_ts, std_sig) else {
            return Err(SdkError::WebhookRejected(
                "incomplete Standard Webhooks headers".to_string(),
            ));
        };
        let ts: i64 = ts_raw
            .parse()
            .map_err(|_| SdkError::WebhookRejected("invalid webhook-timestamp".to_string()))?;
        if (now_sec - ts).abs() > DEFAULT_WEBHOOK_SKEW_SEC {
            return Err(SdkError::WebhookRejected(
                "webhook-timestamp outside ±300s skew window".to_string(),
            ));
        }

        let key_bytes = if let Some(b64_key) = secret.strip_prefix("whsec_") {
            base64_decode(b64_key)?
        } else {
            secret.as_bytes().to_vec()
        };

        let mut signed = Vec::with_capacity(id.len() + ts_raw.len() + 2 + raw_body.len());
        signed.extend_from_slice(id.as_bytes());
        signed.push(b'.');
        signed.extend_from_slice(ts_raw.as_bytes());
        signed.push(b'.');
        signed.extend_from_slice(raw_body);

        let expected = hmac_sha256(&key_bytes, &signed);
        let mut matched = false;
        for token in sig_raw.split_whitespace() {
            if let Some((ver, b64)) = token.split_once(',') {
                if ver == "v1" && !b64.is_empty() {
                    if let Ok(provided) = base64_decode(b64) {
                        if constant_time_eq(&provided, &expected) {
                            matched = true;
                        }
                    }
                }
            }
        }
        if !matched {
            return Err(SdkError::WebhookRejected(
                "Standard Webhooks v1 signature mismatch".to_string(),
            ));
        }
        return Ok(WebhookVerification {
            event_key: Some(id.to_string()),
            scheme: "standard-webhooks",
        });
    }

    let Some(omalla_sig) = lower.get("x-omalla-signature").copied() else {
        return Err(SdkError::WebhookRejected(
            "missing webhook signature header".to_string(),
        ));
    };

    let Some(ts_raw) = lower.get("x-omalla-timestamp").copied() else {
        return Err(SdkError::WebhookRejected(
            "missing x-omalla-timestamp header".to_string(),
        ));
    };
    let ts_clean = ts_raw.trim();
    let ts: i64 = ts_clean
        .parse()
        .map_err(|_| SdkError::WebhookRejected("invalid x-omalla-timestamp".to_string()))?;
    if (now_sec - ts).abs() > DEFAULT_WEBHOOK_SKEW_SEC {
        return Err(SdkError::WebhookRejected(
            "x-omalla-timestamp outside ±300s skew window".to_string(),
        ));
    }
    let mut signed_payload = Vec::with_capacity(ts_clean.len() + 1 + raw_body.len());
    signed_payload.extend_from_slice(ts_clean.as_bytes());
    signed_payload.push(b'.');
    signed_payload.extend_from_slice(raw_body);

    let hex_part = omalla_sig.strip_prefix("sha256=").unwrap_or(omalla_sig);
    let provided = hex_decode(hex_part)?;
    let expected = hmac_sha256(secret.as_bytes(), &signed_payload);
    if !constant_time_eq(&provided, &expected) {
        return Err(SdkError::WebhookRejected(
            "webhook HMAC signature mismatch".to_string(),
        ));
    }

    let body_sha = hex_encode(&sha256_bytes(raw_body));
    let event_key = Some(format!("omalla:{ts_clean}:{body_sha}"));

    Ok(WebhookVerification {
        event_key,
        scheme: "omalla-hmac",
    })
}

/* ------------------------------------------------------------------ */
/* Strongly-Typed Domain Models                                        */
/* ------------------------------------------------------------------ */

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HealthStatus {
    pub ok: bool,
    pub version: String,
    pub simulation: bool,
    pub telephony_default: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AgentSummary {
    pub id: String,
    pub name: String,
    pub status: String,
    pub version: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorkflowSummary {
    pub id: String,
    pub name: String,
    pub status: String,
    pub version: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OutboundCallRequest {
    pub to: String,
    pub agent_id: String,
    pub consent: bool,
    pub mode: String,
    pub provider: Option<String>,
    pub from: Option<String>,
    pub variables: Vec<(String, JsonValue)>,
}

impl OutboundCallRequest {
    pub fn simulated(to: impl Into<String>, agent_id: impl Into<String>, consent: bool) -> Self {
        Self {
            to: to.into(),
            agent_id: agent_id.into(),
            consent,
            mode: "simulated".to_string(),
            provider: None,
            from: None,
            variables: Vec::new(),
        }
    }

    pub fn to_json_value(&self) -> JsonValue {
        let mut fields = vec![
            ("to".to_string(), JsonValue::String(self.to.clone())),
            (
                "agentId".to_string(),
                JsonValue::String(self.agent_id.clone()),
            ),
            ("consent".to_string(), JsonValue::Bool(self.consent)),
            ("mode".to_string(), JsonValue::String(self.mode.clone())),
            (
                "variables".to_string(),
                JsonValue::Object(self.variables.clone()),
            ),
        ];
        if let Some(ref p) = self.provider {
            fields.push(("provider".to_string(), JsonValue::String(p.clone())));
        }
        if let Some(ref f) = self.from {
            fields.push(("from".to_string(), JsonValue::String(f.clone())));
        }
        JsonValue::Object(fields)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CallSummary {
    pub id: String,
    pub status: String,
    pub simulation: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SmsRequest {
    pub to: String,
    pub body: String,
    pub consent: bool,
    pub from: Option<String>,
}

impl SmsRequest {
    pub fn to_json_value(&self) -> JsonValue {
        let mut fields = vec![
            ("to".to_string(), JsonValue::String(self.to.clone())),
            ("body".to_string(), JsonValue::String(self.body.clone())),
            ("consent".to_string(), JsonValue::Bool(self.consent)),
        ];
        if let Some(ref f) = self.from {
            fields.push(("from".to_string(), JsonValue::String(f.clone())));
        }
        JsonValue::Object(fields)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SmsSummary {
    pub id: String,
    pub status: String,
    pub simulated: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RollbackRequest {
    pub version: i64,
    pub note: Option<String>,
}

impl RollbackRequest {
    pub fn new(version: i64) -> Self {
        Self {
            version,
            note: None,
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.note = Some(note.into());
        self
    }

    pub fn to_json_value(&self) -> JsonValue {
        let mut fields = vec![("version".to_string(), JsonValue::Integer(self.version))];
        if let Some(ref n) = self.note {
            fields.push(("note".to_string(), JsonValue::String(n.clone())));
        }
        JsonValue::Object(fields)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StreamEvent {
    pub event_type: String,
    pub call_id: Option<String>,
    pub payload: JsonValue,
}

pub fn parse_stream_event(raw_frame: &str) -> Result<StreamEvent, SdkError> {
    let trimmed = raw_frame
        .trim()
        .strip_prefix("data:")
        .map(str::trim)
        .unwrap_or_else(|| raw_frame.trim());
    let parsed = parse_json_response(trimmed)?;
    let event_type = parsed
        .get("type")
        .and_then(JsonValue::as_str)
        .ok_or_else(|| SdkError::JsonParse("stream frame missing 'type'".to_string()))?
        .to_string();
    let call_id = parsed
        .get("callId")
        .and_then(JsonValue::as_str)
        .map(str::to_string);
    Ok(StreamEvent {
        event_type,
        call_id,
        payload: parsed,
    })
}

/* ------------------------------------------------------------------ */
/* HTTP Transport & Client Builder                                     */
/* ------------------------------------------------------------------ */

#[derive(Debug, Clone)]
pub struct RawHttpRequest {
    pub method: String,
    pub url: String,
    pub headers: Vec<(String, String)>,
    pub body: Option<Vec<u8>>,
    pub timeout: Duration,
}

#[derive(Debug, Clone)]
pub struct RawHttpResponse {
    pub status: u16,
    pub body: Vec<u8>,
}

pub trait HttpTransport: Send + Sync {
    fn execute(&self, request: RawHttpRequest) -> Result<RawHttpResponse, SdkError>;
}

/// Minimal synchronous HTTP/1.1 client over `std::net::TcpStream` for local
/// self-hosted `http://` endpoints.
#[derive(Debug, Clone, Default)]
pub struct StdHttpTransport;

impl HttpTransport for StdHttpTransport {
    fn execute(&self, request: RawHttpRequest) -> Result<RawHttpResponse, SdkError> {
        let without_scheme = request.url.strip_prefix("http://").ok_or_else(|| {
            SdkError::Transport(
                "StdHttpTransport supports http:// URLs; inject a TLS HttpTransport for https://"
                    .to_string(),
            )
        })?;
        let (authority, path) = match without_scheme.find('/') {
            Some(idx) => (&without_scheme[..idx], &without_scheme[idx..]),
            None => (without_scheme, "/"),
        };
        if has_crlf_or_nul(&request.method) || has_crlf_or_nul(path) || has_crlf_or_nul(authority) {
            return Err(SdkError::Transport(
                "CR/LF or NUL byte in HTTP request target".to_string(),
            ));
        }
        for (k, v) in &request.headers {
            if k.is_empty() || k.contains(':') || has_crlf_or_nul(k) || has_crlf_or_nul(v) {
                return Err(SdkError::Transport(
                    "CR/LF or invalid character in HTTP header".to_string(),
                ));
            }
        }
        let host_port = if authority.contains(':') {
            authority.to_string()
        } else {
            format!("{authority}:80")
        };

        let mut stream = TcpStream::connect(&host_port)
            .map_err(|e| SdkError::Transport(format!("connect {host_port} failed: {e}")))?;
        let _ = stream.set_read_timeout(Some(request.timeout));
        let _ = stream.set_write_timeout(Some(request.timeout));

        let body_bytes = request.body.as_deref().unwrap_or(&[]);
        let mut wire = format!(
            "{} {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\nContent-Length: {}\r\n",
            request.method,
            path,
            authority,
            body_bytes.len()
        );
        for (k, v) in &request.headers {
            wire.push_str(k);
            wire.push_str(": ");
            wire.push_str(v);
            wire.push_str("\r\n");
        }
        wire.push_str("\r\n");

        stream
            .write_all(wire.as_bytes())
            .and_then(|_| stream.write_all(body_bytes))
            .and_then(|_| stream.flush())
            .map_err(|e| SdkError::Transport(format!("write failed: {e}")))?;
        let _ = stream.shutdown(std::net::Shutdown::Write);

        let mut resp_bytes = Vec::new();
        stream
            .read_to_end(&mut resp_bytes)
            .map_err(|e| SdkError::Transport(format!("read failed: {e}")))?;

        let header_end = resp_bytes
            .windows(4)
            .position(|w| w == b"\r\n\r\n")
            .ok_or_else(|| SdkError::Transport("malformed HTTP response".to_string()))?;

        let head = String::from_utf8_lossy(&resp_bytes[..header_end]);
        let status_line = head
            .lines()
            .next()
            .ok_or_else(|| SdkError::Transport("empty HTTP status line".to_string()))?;
        let status: u16 = status_line
            .split_whitespace()
            .nth(1)
            .ok_or_else(|| SdkError::Transport("missing HTTP status code".to_string()))?
            .parse()
            .map_err(|_| SdkError::Transport("invalid HTTP status code".to_string()))?;

        let body = resp_bytes[header_end + 4..].to_vec();
        Ok(RawHttpResponse { status, body })
    }
}

#[derive(Debug, Clone)]
pub struct OmallaClientBuilder {
    base_url: String,
    api_key: Option<String>,
    timeout: Duration,
    user_agent: String,
}

impl Default for OmallaClientBuilder {
    fn default() -> Self {
        Self {
            base_url: "http://127.0.0.1:8787".to_string(),
            api_key: None,
            timeout: Duration::from_secs(30),
            user_agent: format!("omalla-rust/{SDK_VERSION}"),
        }
    }
}

impl OmallaClientBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn base_url(mut self, base_url: impl Into<String>) -> Self {
        self.base_url = base_url.into();
        self
    }

    pub fn api_key(mut self, api_key: impl Into<String>) -> Self {
        self.api_key = Some(api_key.into());
        self
    }

    pub fn timeout(mut self, timeout: Duration) -> Self {
        self.timeout = timeout;
        self
    }

    pub fn user_agent(mut self, user_agent: impl Into<String>) -> Self {
        self.user_agent = user_agent.into();
        self
    }

    pub fn build(self) -> Result<OmallaClient<StdHttpTransport>, SdkError> {
        self.build_with_transport(StdHttpTransport)
    }

    pub fn build_with_transport<T: HttpTransport>(
        self,
        transport: T,
    ) -> Result<OmallaClient<T>, SdkError> {
        let key = self
            .api_key
            .map(|k| k.trim().to_string())
            .filter(|k| !k.is_empty())
            .ok_or_else(|| SdkError::Configuration("an API key is required".to_string()))?;
        let normalized_url = self.base_url.trim_end_matches('/').to_string();
        if normalized_url.is_empty() {
            return Err(SdkError::Configuration(
                "base_url must not be empty".to_string(),
            ));
        }
        Ok(OmallaClient {
            base_url: normalized_url,
            api_key: key,
            timeout: self.timeout,
            user_agent: self.user_agent,
            transport,
        })
    }
}

pub struct OmallaClient<T: HttpTransport = StdHttpTransport> {
    base_url: String,
    api_key: String,
    timeout: Duration,
    user_agent: String,
    transport: T,
}

impl OmallaClient<StdHttpTransport> {
    pub fn builder() -> OmallaClientBuilder {
        OmallaClientBuilder::new()
    }
}

impl<T: HttpTransport> OmallaClient<T> {
    pub fn base_url(&self) -> &str {
        &self.base_url
    }

    pub fn request_json(
        &self,
        method: &str,
        path: &str,
        body: Option<&JsonValue>,
        idempotency_key: Option<&str>,
    ) -> Result<JsonValue, SdkError> {
        let rel = if path.starts_with('/') {
            path.to_string()
        } else {
            format!("/{path}")
        };
        let url = format!("{}{}", self.base_url, rel);

        let mut headers = vec![
            (
                "Authorization".to_string(),
                format!("Bearer {}", self.api_key),
            ),
            ("Accept".to_string(), "application/json".to_string()),
            ("User-Agent".to_string(), self.user_agent.clone()),
        ];

        let encoded_body = if let Some(val) = body {
            let canonical = canonicalize_jcs(val)?;
            headers.push(("Content-Type".to_string(), "application/json".to_string()));
            if let Some(idem) = idempotency_key {
                let digest = hex_encode(&sha256_bytes(canonical.as_bytes()));
                headers.push(("Idempotency-Key".to_string(), idem.to_string()));
                headers.push(("X-Omalla-Args-Digest".to_string(), digest));
            }
            Some(canonical.into_bytes())
        } else {
            if let Some(idem) = idempotency_key {
                headers.push(("Idempotency-Key".to_string(), idem.to_string()));
            }
            None
        };

        let response = self.transport.execute(RawHttpRequest {
            method: method.to_string(),
            url,
            headers,
            body: encoded_body,
            timeout: self.timeout,
        })?;

        if response.status == 204 || response.body.is_empty() {
            return Ok(JsonValue::Null);
        }

        let text = String::from_utf8(response.body)
            .map_err(|_| SdkError::Transport("non-UTF8 response body".to_string()))?;

        let parsed = parse_json_response(&text)?;
        if !(200..300).contains(&response.status) {
            let err_obj = parsed.get("error");
            let code = err_obj
                .and_then(|e| e.get("code"))
                .and_then(JsonValue::as_str)
                .unwrap_or("http_error")
                .to_string();
            let message = err_obj
                .and_then(|e| e.get("message"))
                .and_then(JsonValue::as_str)
                .unwrap_or("request failed")
                .to_string();
            return Err(SdkError::Http {
                status: response.status,
                code,
                message,
            });
        }

        Ok(parsed)
    }

    pub fn health(&self) -> Result<HealthStatus, SdkError> {
        let json = self.request_json("GET", "/v1/health", None, None)?;
        Ok(HealthStatus {
            ok: json.get("ok").and_then(JsonValue::as_bool).unwrap_or(false),
            version: json
                .get("version")
                .and_then(JsonValue::as_str)
                .unwrap_or("0.1.0")
                .to_string(),
            simulation: json
                .get("simulation")
                .and_then(JsonValue::as_bool)
                .unwrap_or(true),
            telephony_default: json
                .get("telephonyDefault")
                .and_then(JsonValue::as_str)
                .unwrap_or("simulated")
                .to_string(),
        })
    }

    pub fn rollback_agent(
        &self,
        agent_id: &str,
        request: &RollbackRequest,
    ) -> Result<AgentSummary, SdkError> {
        let payload = request.to_json_value();
        let json = self.request_json(
            "POST",
            &format!("/v1/agents/{}/rollback", percent_encode_segment(agent_id)),
            Some(&payload),
            None,
        )?;
        parse_agent_summary(&json)
    }

    pub fn rollback_workflow(
        &self,
        workflow_id: &str,
        request: &RollbackRequest,
    ) -> Result<WorkflowSummary, SdkError> {
        let payload = request.to_json_value();
        let json = self.request_json(
            "POST",
            &format!(
                "/v1/workflows/{}/rollback",
                percent_encode_segment(workflow_id)
            ),
            Some(&payload),
            None,
        )?;
        parse_workflow_summary(&json)
    }

    pub fn start_outbound_call(
        &self,
        request: &OutboundCallRequest,
        idempotency_key: Option<&str>,
    ) -> Result<CallSummary, SdkError> {
        let payload = request.to_json_value();
        let json = self.request_json(
            "POST",
            "/v1/calls/outbound",
            Some(&payload),
            idempotency_key,
        )?;
        Ok(CallSummary {
            id: json
                .get("id")
                .and_then(JsonValue::as_str)
                .unwrap_or_default()
                .to_string(),
            status: json
                .get("status")
                .and_then(JsonValue::as_str)
                .unwrap_or("queued")
                .to_string(),
            simulation: json
                .get("simulation")
                .and_then(JsonValue::as_bool)
                .unwrap_or(true),
        })
    }

    pub fn send_sms(
        &self,
        request: &SmsRequest,
        idempotency_key: Option<&str>,
    ) -> Result<SmsSummary, SdkError> {
        let payload = request.to_json_value();
        let json = self.request_json("POST", "/v1/sms", Some(&payload), idempotency_key)?;
        Ok(SmsSummary {
            id: json
                .get("id")
                .and_then(JsonValue::as_str)
                .unwrap_or_default()
                .to_string(),
            status: json
                .get("status")
                .and_then(JsonValue::as_str)
                .unwrap_or("queued")
                .to_string(),
            simulated: json
                .get("simulated")
                .and_then(JsonValue::as_bool)
                .unwrap_or(true),
        })
    }
}

fn parse_agent_summary(json: &JsonValue) -> Result<AgentSummary, SdkError> {
    let id = json
        .get("id")
        .and_then(JsonValue::as_str)
        .ok_or_else(|| SdkError::JsonParse("missing agent id".to_string()))?
        .to_string();
    Ok(AgentSummary {
        id,
        name: json
            .get("name")
            .and_then(JsonValue::as_str)
            .unwrap_or_default()
            .to_string(),
        status: json
            .get("status")
            .and_then(JsonValue::as_str)
            .unwrap_or("draft")
            .to_string(),
        version: json.get("version").and_then(JsonValue::as_i64).unwrap_or(1),
    })
}

fn parse_workflow_summary(json: &JsonValue) -> Result<WorkflowSummary, SdkError> {
    let id = json
        .get("id")
        .and_then(JsonValue::as_str)
        .ok_or_else(|| SdkError::JsonParse("missing workflow id".to_string()))?
        .to_string();
    Ok(WorkflowSummary {
        id,
        name: json
            .get("name")
            .and_then(JsonValue::as_str)
            .unwrap_or_default()
            .to_string(),
        status: json
            .get("status")
            .and_then(JsonValue::as_str)
            .unwrap_or("draft")
            .to_string(),
        version: json.get("version").and_then(JsonValue::as_i64).unwrap_or(1),
    })
}

fn has_crlf_or_nul(s: &str) -> bool {
    s.bytes().any(|b| matches!(b, b'\r' | b'\n' | b'\0'))
}

fn percent_encode_segment(segment: &str) -> String {
    let mut out = String::with_capacity(segment.len());
    for &b in segment.as_bytes() {
        if b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_' | b'.' | b'~') {
            out.push(b as char);
        } else {
            let _ = fmt::Write::write_fmt(&mut out, format_args!("%{b:02X}"));
        }
    }
    out
}

/* ------------------------------------------------------------------ */
/* Unit Tests                                                          */
/* ------------------------------------------------------------------ */

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::TcpListener;
    use std::sync::Mutex;
    use std::thread;

    #[test]
    fn sha256_and_hmac_match_nist_and_rfc4231_vectors() {
        assert_eq!(
            hex_encode(&sha256_bytes(b"")),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
        assert_eq!(
            hex_encode(&sha256_bytes(b"abc")),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
        assert_eq!(
            hex_encode(&sha256_bytes(
                b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"
            )),
            "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"
        );
        // RFC 4231 Test Case 2
        let mac = hmac_sha256(b"Jefe", b"what do ya want for nothing?");
        assert_eq!(
            hex_encode(&mac),
            "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        );
    }

    #[test]
    fn jcs_orders_keys_by_utf16_and_rejects_floats() {
        // RFC 8785 §3.2.3: U+1D11E (surrogate pair 0xD834 0xDD1E) sorts BEFORE U+E000 in UTF-16!
        let val = JsonValue::object(vec![
            ("\u{E000}", JsonValue::Integer(2)),
            ("\u{1D11E}", JsonValue::Integer(1)),
            ("arabic", JsonValue::String("مع السلامة".to_string())),
            ("negZero", JsonValue::Integer(0)),
        ]);
        let canonical = canonicalize_jcs(&val).expect("valid JCS");
        assert_eq!(
            canonical,
            "{\"arabic\":\"مع السلامة\",\"negZero\":0,\"\u{1D11E}\":1,\"\u{E000}\":2}"
        );

        let d1 = args_digest_json(r#"{"b": 2, "a": [true, false, null, -0]}"#).unwrap();
        let d2 = args_digest_json(r#"{"a":[true,false,null,0],"b":2}"#).unwrap();
        assert_eq!(d1, d2);

        assert!(matches!(
            args_digest_json(r#"{"amount": 19.99}"#),
            Err(SdkError::FloatRejected(_))
        ));
        assert!(matches!(
            args_digest_json(r#"{"amount": 10.0}"#),
            Err(SdkError::FloatRejected(_))
        ));
        assert!(matches!(
            args_digest_json(r#"{"amount": 1e3}"#),
            Err(SdkError::FloatRejected(_))
        ));
        // RFC 8259 leading zero rejection
        assert!(matches!(
            args_digest_json(r#"{"code": 01}"#),
            Err(SdkError::JsonParse(_))
        ));
        assert!(matches!(
            args_digest_json(r#"{"code": -01}"#),
            Err(SdkError::JsonParse(_))
        ));
    }

    #[test]
    fn webhook_hmac_verifies_standard_webhooks_and_rejects_skew() {
        let raw_body = br#"{"event":"call.ended","callId":"call_42"}"#;
        let key_raw = b"0123456789abcdef0123456789abcdef";
        let secret = format!("whsec_{}", base64_encode(key_raw));
        let msg_id = "msg_991";
        let ts = "1700000000";

        let mut signed = Vec::new();
        signed.extend_from_slice(format!("{msg_id}.{ts}.").as_bytes());
        signed.extend_from_slice(raw_body);
        let sig = base64_encode(&hmac_sha256(key_raw, &signed));

        let mut headers = BTreeMap::new();
        headers.insert("webhook-id".to_string(), msg_id.to_string());
        headers.insert("webhook-timestamp".to_string(), ts.to_string());
        headers.insert("webhook-signature".to_string(), format!("v1,{sig}"));

        let verified =
            verify_webhook_signature(raw_body, &headers, &secret, Some(1_700_000_120)).unwrap();
        assert_eq!(verified.event_key.as_deref(), Some(msg_id));
        assert_eq!(verified.scheme, "standard-webhooks");

        // Skew > 300s rejected
        let stale = verify_webhook_signature(raw_body, &headers, &secret, Some(1_700_000_305));
        assert!(matches!(stale, Err(SdkError::WebhookRejected(_))));

        // Tampered byte rejected
        let tampered = verify_webhook_signature(
            br#"{"event":"call.ended","callId":"call_43"}"#,
            &headers,
            &secret,
            Some(1_700_000_120),
        );
        assert!(matches!(tampered, Err(SdkError::WebhookRejected(_))));

        // x-omalla-signature requires x-omalla-timestamp and derives event_key from signed bytes
        let mut om_headers = BTreeMap::new();
        let om_secret = "om_sec_123";
        let om_signed = format!("{ts}.{}", std::str::from_utf8(raw_body).unwrap());
        let om_sig = format!(
            "sha256={}",
            hex_encode(&hmac_sha256(om_secret.as_bytes(), om_signed.as_bytes()))
        );
        om_headers.insert("x-omalla-signature".to_string(), om_sig);
        assert!(matches!(
            verify_webhook_signature(raw_body, &om_headers, om_secret, Some(1_700_000_120)),
            Err(SdkError::WebhookRejected(_))
        ));
        om_headers.insert("x-omalla-timestamp".to_string(), ts.to_string());
        om_headers.insert(
            "x-omalla-delivery-id".to_string(),
            "forged_unsigned_header".to_string(),
        );
        let om_ok = verify_webhook_signature(raw_body, &om_headers, om_secret, Some(1_700_000_120))
            .unwrap();
        assert_eq!(om_ok.scheme, "omalla-hmac");
        assert!(om_ok
            .event_key
            .as_deref()
            .unwrap()
            .starts_with("omalla:1700000000:"));
    }

    struct RecordingTransport {
        requests: Mutex<Vec<RawHttpRequest>>,
        response_status: u16,
        response_json: String,
    }

    impl HttpTransport for RecordingTransport {
        fn execute(&self, request: RawHttpRequest) -> Result<RawHttpResponse, SdkError> {
            self.requests.lock().unwrap().push(request);
            Ok(RawHttpResponse {
                status: self.response_status,
                body: self.response_json.as_bytes().to_vec(),
            })
        }
    }

    #[test]
    fn client_builder_sends_idempotency_digest_and_executes_rollback() {
        assert!(matches!(
            OmallaClient::builder().build(),
            Err(SdkError::Configuration(_))
        ));

        let transport = RecordingTransport {
            requests: Mutex::new(Vec::new()),
            response_status: 201,
            response_json: r#"{"id":"call_1","status":"in_progress","simulation":true}"#
                .to_string(),
        };
        let client = OmallaClient::builder()
            .base_url("http://127.0.0.1:8787/")
            .api_key("omk_rust_test")
            .build_with_transport(transport)
            .unwrap();

        let req = OutboundCallRequest::simulated("+15550009999", "agt_1", true);
        let call = client
            .start_outbound_call(&req, Some("idem_rust_1"))
            .unwrap();
        assert_eq!(call.id, "call_1");
        assert!(call.simulation);

        let recorded = client.transport.requests.lock().unwrap();
        assert_eq!(recorded.len(), 1);
        assert_eq!(recorded[0].url, "http://127.0.0.1:8787/v1/calls/outbound");
        assert!(recorded[0]
            .headers
            .iter()
            .any(|(k, v)| k == "Idempotency-Key" && v == "idem_rust_1"));
        assert!(recorded[0]
            .headers
            .iter()
            .any(|(k, v)| k == "X-Omalla-Args-Digest" && v.len() == 64));
    }

    #[test]
    fn std_http_transport_round_trips_over_loopback() {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let addr = listener.local_addr().unwrap();

        let handle = thread::spawn(move || {
            let (mut sock, _) = listener.accept().unwrap();
            let mut req_buf = Vec::new();
            let _ = sock.read_to_end(&mut req_buf);
            let body = r#"{"id":"agt_42","name":"Ava","status":"published","version":3}"#;
            let resp = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                body.len(),
                body
            );
            sock.write_all(resp.as_bytes()).unwrap();
            let _ = sock.shutdown(std::net::Shutdown::Write);
        });

        let client = OmallaClient::builder()
            .base_url(format!("http://{addr}"))
            .api_key("omk_live_loopback")
            .build()
            .unwrap();

        let rolled = client
            .rollback_agent("agt_42", &RollbackRequest::new(1).with_note("restore v1"))
            .unwrap();
        assert_eq!(rolled.id, "agt_42");
        assert_eq!(rolled.version, 3);
        handle.join().unwrap();

        let evt =
            parse_stream_event(r#"data: {"type":"assistant.delta","callId":"call_9"}"#).unwrap();
        assert_eq!(evt.event_type, "assistant.delta");
        assert_eq!(evt.call_id.as_deref(), Some("call_9"));

        // CR/LF header injection rejected before TCP connect
        let bad_transport = StdHttpTransport.execute(RawHttpRequest {
            method: "GET".to_string(),
            url: "http://127.0.0.1:9/v1/health".to_string(),
            headers: vec![("X-Injected".to_string(), "ok\r\nX-Evil: 1".to_string())],
            body: None,
            timeout: Duration::from_secs(1),
        });
        assert!(matches!(bad_transport, Err(SdkError::Transport(_))));
    }
}
