//! Bounded JSON preflight scanner (adapted from `TheHalfMoon/Sentrdel` `bounded_json.rs`).
//!
//! Validates raw byte size, UTF-8 integrity, maximum nesting depth, maximum AST node/property
//! count, and maximum string byte length in a single streaming pass BEFORE `serde_json`
//! materializes any heap tree.

use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PreflightLimits {
    pub max_total_bytes: usize,
    pub max_depth: usize,
    pub max_nodes: usize,
    pub max_string_bytes: usize,
    pub max_object_keys: usize,
}

impl Default for PreflightLimits {
    fn default() -> Self {
        Self {
            max_total_bytes: 1024 * 1024, // 1 MiB worker frame cap
            max_depth: 32,
            max_nodes: 8192,
            max_string_bytes: 256 * 1024,
            max_object_keys: 256,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum PreflightError {
    #[error("input is empty")]
    Empty,
    #[error("frame size {actual} exceeds limit {limit}")]
    TooLarge { actual: usize, limit: usize },
    #[error("invalid UTF-8 payload")]
    InvalidUtf8,
    #[error("nesting depth exceeds limit {limit}")]
    DepthExceeded { limit: usize },
    #[error("node count exceeds limit {limit}")]
    NodeCountExceeded { limit: usize },
    #[error("string byte length {actual} exceeds limit {limit}")]
    StringTooLong { actual: usize, limit: usize },
    #[error("object key count exceeds limit {limit}")]
    ObjectTooWide { limit: usize },
    #[error("malformed or trailing JSON syntax")]
    MalformedJson,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Container {
    Object { keys: usize },
    Array,
}

/// Scans `raw` against `limits` without allocating a DOM tree.
pub fn preflight(raw: &[u8], limits: PreflightLimits) -> Result<(), PreflightError> {
    if raw.is_empty() {
        return Err(PreflightError::Empty);
    }
    if raw.len() > limits.max_total_bytes {
        return Err(PreflightError::TooLarge {
            actual: raw.len(),
            limit: limits.max_total_bytes,
        });
    }
    let text = std::str::from_utf8(raw).map_err(|_| PreflightError::InvalidUtf8)?;
    let bytes = text.as_bytes();
    let mut i = 0usize;
    let mut stack: Vec<Container> = Vec::new();
    let mut nodes = 0usize;

    fn skip_ws(b: &[u8], idx: &mut usize) {
        while *idx < b.len() && matches!(b[*idx], b' ' | b'\t' | b'\r' | b'\n') {
            *idx += 1;
        }
    }

    fn scan_string(
        b: &[u8],
        idx: &mut usize,
        max_string_bytes: usize,
    ) -> Result<(), PreflightError> {
        if *idx >= b.len() || b[*idx] != b'"' {
            return Err(PreflightError::MalformedJson);
        }
        *idx += 1;
        let start = *idx;
        while *idx < b.len() {
            let c = b[*idx];
            if c == b'"' {
                let span = *idx - start;
                if span > max_string_bytes {
                    return Err(PreflightError::StringTooLong {
                        actual: span,
                        limit: max_string_bytes,
                    });
                }
                *idx += 1;
                return Ok(());
            }
            if c < 0x20 {
                return Err(PreflightError::MalformedJson);
            }
            if c == b'\\' {
                *idx += 1;
                if *idx >= b.len() {
                    return Err(PreflightError::MalformedJson);
                }
                if b[*idx] == b'u' {
                    if *idx + 4 >= b.len() {
                        return Err(PreflightError::MalformedJson);
                    }
                    for k in 1..=4 {
                        if !b[*idx + k].is_ascii_hexdigit() {
                            return Err(PreflightError::MalformedJson);
                        }
                    }
                    *idx += 4;
                }
            }
            *idx += 1;
            if *idx - start > max_string_bytes {
                return Err(PreflightError::StringTooLong {
                    actual: *idx - start,
                    limit: max_string_bytes,
                });
            }
        }
        Err(PreflightError::MalformedJson)
    }

    fn scan_primitive(b: &[u8], idx: &mut usize) -> Result<(), PreflightError> {
        if b[*idx..].starts_with(b"true") {
            *idx += 4;
            return Ok(());
        }
        if b[*idx..].starts_with(b"false") {
            *idx += 5;
            return Ok(());
        }
        if b[*idx..].starts_with(b"null") {
            *idx += 4;
            return Ok(());
        }
        // JSON number
        let start = *idx;
        if *idx < b.len() && b[*idx] == b'-' {
            *idx += 1;
        }
        if *idx >= b.len() || !b[*idx].is_ascii_digit() {
            return Err(PreflightError::MalformedJson);
        }
        if b[*idx] == b'0' {
            *idx += 1;
        } else {
            while *idx < b.len() && b[*idx].is_ascii_digit() {
                *idx += 1;
            }
        }
        if *idx < b.len() && b[*idx] == b'.' {
            *idx += 1;
            if *idx >= b.len() || !b[*idx].is_ascii_digit() {
                return Err(PreflightError::MalformedJson);
            }
            while *idx < b.len() && b[*idx].is_ascii_digit() {
                *idx += 1;
            }
        }
        if *idx < b.len() && matches!(b[*idx], b'e' | b'E') {
            *idx += 1;
            if *idx < b.len() && matches!(b[*idx], b'+' | b'-') {
                *idx += 1;
            }
            if *idx >= b.len() || !b[*idx].is_ascii_digit() {
                return Err(PreflightError::MalformedJson);
            }
            while *idx < b.len() && b[*idx].is_ascii_digit() {
                *idx += 1;
            }
        }
        if *idx == start {
            return Err(PreflightError::MalformedJson);
        }
        Ok(())
    }

    skip_ws(bytes, &mut i);
    if i >= bytes.len() {
        return Err(PreflightError::Empty);
    }

    loop {
        // Parse one value
        nodes += 1;
        if nodes > limits.max_nodes {
            return Err(PreflightError::NodeCountExceeded {
                limit: limits.max_nodes,
            });
        }
        skip_ws(bytes, &mut i);
        if i >= bytes.len() {
            return Err(PreflightError::MalformedJson);
        }
        match bytes[i] {
            b'{' => {
                if stack.len() + 1 > limits.max_depth {
                    return Err(PreflightError::DepthExceeded {
                        limit: limits.max_depth,
                    });
                }
                i += 1;
                skip_ws(bytes, &mut i);
                if i < bytes.len() && bytes[i] == b'}' {
                    i += 1;
                } else {
                    scan_string(bytes, &mut i, limits.max_string_bytes)?;
                    skip_ws(bytes, &mut i);
                    if i >= bytes.len() || bytes[i] != b':' {
                        return Err(PreflightError::MalformedJson);
                    }
                    i += 1;
                    if 1 > limits.max_object_keys {
                        return Err(PreflightError::ObjectTooWide {
                            limit: limits.max_object_keys,
                        });
                    }
                    stack.push(Container::Object { keys: 1 });
                    continue;
                }
            }
            b'[' => {
                if stack.len() + 1 > limits.max_depth {
                    return Err(PreflightError::DepthExceeded {
                        limit: limits.max_depth,
                    });
                }
                i += 1;
                skip_ws(bytes, &mut i);
                if i < bytes.len() && bytes[i] == b']' {
                    i += 1;
                } else {
                    stack.push(Container::Array);
                    continue;
                }
            }
            b'"' => {
                scan_string(bytes, &mut i, limits.max_string_bytes)?;
            }
            _ => {
                scan_primitive(bytes, &mut i)?;
            }
        }

        // Unwind completed containers or advance to next sibling value
        loop {
            skip_ws(bytes, &mut i);
            let Some(top) = stack.last_mut() else {
                if i != bytes.len() {
                    return Err(PreflightError::MalformedJson);
                }
                return Ok(());
            };
            match top {
                Container::Object { keys } => {
                    if i >= bytes.len() {
                        return Err(PreflightError::MalformedJson);
                    }
                    if bytes[i] == b'}' {
                        i += 1;
                        stack.pop();
                    } else if bytes[i] == b',' {
                        i += 1;
                        skip_ws(bytes, &mut i);
                        *keys += 1;
                        if *keys > limits.max_object_keys {
                            return Err(PreflightError::ObjectTooWide {
                                limit: limits.max_object_keys,
                            });
                        }
                        scan_string(bytes, &mut i, limits.max_string_bytes)?;
                        skip_ws(bytes, &mut i);
                        if i >= bytes.len() || bytes[i] != b':' {
                            return Err(PreflightError::MalformedJson);
                        }
                        i += 1;
                        break;
                    } else {
                        return Err(PreflightError::MalformedJson);
                    }
                }
                Container::Array => {
                    if i >= bytes.len() {
                        return Err(PreflightError::MalformedJson);
                    }
                    if bytes[i] == b']' {
                        i += 1;
                        stack.pop();
                    } else if bytes[i] == b',' {
                        i += 1;
                        break;
                    } else {
                        return Err(PreflightError::MalformedJson);
                    }
                }
            }
        }
    }
}
