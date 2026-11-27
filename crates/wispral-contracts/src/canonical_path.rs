//! Deterministic executable image path canonicalization (`image_path_digest`).
//!
//! Matches `docs/engineering/contracts/README.md`:
//! - NFC-normalized;
//! - Forward slashes converted to Windows backslashes when canonicalizing Windows paths;
//! - Extended-length `\\?\` prefix stripped;
//! - Invariant/ASCII lowercase fold (and Unicode simple lowercase for non-ASCII segments);
//! - Trailing separator stripped (except drive root `c:\`).

use sha2::{Digest as _, Sha256};
use unicode_normalization::UnicodeNormalization;

pub fn canonicalize_windows_image_path(raw: &str) -> String {
    let nfc: String = raw.trim().nfc().collect();
    let replaced = nfc.replace('/', "\\");
    let stripped_prefix = replaced
        .strip_prefix(r"\\?\UNC\")
        .map(|rest| format!(r"\\{rest}"))
        .or_else(|| replaced.strip_prefix(r"\\?\").map(str::to_owned))
        .unwrap_or(replaced);

    // Collapse duplicate backslashes after any leading UNC `\\`
    let (unc, body) = if let Some(rest) = stripped_prefix.strip_prefix(r"\\") {
        (true, rest)
    } else {
        (false, stripped_prefix.as_str())
    };

    let mut collapsed = String::with_capacity(stripped_prefix.len());
    if unc {
        collapsed.push_str(r"\\");
    }
    let mut prev_slash = false;
    for ch in body.chars() {
        if ch == '\\' {
            if !prev_slash {
                collapsed.push('\\');
                prev_slash = true;
            }
        } else {
            for lc in ch.to_lowercase() {
                collapsed.push(lc);
            }
            prev_slash = false;
        }
    }

    // Strip trailing backslash unless drive root like `c:\`
    let is_drive_root = collapsed.len() == 3
        && collapsed.as_bytes()[0].is_ascii_alphabetic()
        && &collapsed[1..3] == r":\";
    if !is_drive_root && collapsed.ends_with('\\') {
        collapsed.pop();
    }
    collapsed
}

pub fn windows_image_path_digest(raw: &str) -> String {
    let canon = canonicalize_windows_image_path(raw);
    let mut hasher = Sha256::new();
    hasher.update(canon.as_bytes());
    format!("sha256:{}", hex::encode(hasher.finalize()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn windows_paths_with_different_casing_slashes_or_verbatim_prefix_hash_identically() {
        let a = windows_image_path_digest(r"C:\Program Files\Microsoft VS Code\Code.exe");
        let b = windows_image_path_digest(r"\\?\c:/program files/microsoft vs code/CODE.EXE\");
        assert_eq!(a, b);
    }
}
