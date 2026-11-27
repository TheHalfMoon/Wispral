//! Wispral Core append-only fsync'd intent and tamper-evident provenance journal.
//!
//! Copied and adapted from `TheHalfMoon/Orcel` `crates/orcel-journal/src/lib.rs`
//! (Apache-2.0, commit `f0b78e6544cf6ea9c2457a6b6f483490c7bd0f6f`; see root `NOTICE`),
//! extended with optional SHA-256 hash-chaining (`ChainedRecord<T>`, [`append_chained`],
//! [`read_and_verify_chain`]) for tamper-evident audit/provenance trails.
//!
//! Core guarantees:
//! - [`append_line`] writes one JSON line and `sync_data()`s before returning.
//!   A torn tail (a crash mid-append) is sealed with a newline first.
//! - [`read_lines`] drops power-loss zero-byte runs, counts torn prefixes in
//!   [`Lines::torn`], and fails closed on corrupt complete lines or oversized files.
//! - [`Journal`] holds an exclusive OS lock (`<journal>.lock`) and intra-process
//!   FIFO turn queue so writers never interleave or starve.
//! - Entries record facts, digests, and state transitions; the journal records,
//!   it never authorizes.

pub mod resume;

use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use std::fs::File;
use std::io::{Read as _, Seek as _, SeekFrom, Write as _};
use std::path::{Path, PathBuf};

/// Longest line, newline included.
pub const MAX_LINE_BYTES: usize = 64 * 1024;
/// Largest journal a reader accepts.
pub const MAX_JOURNAL_BYTES: u64 = 16 * 1024 * 1024;
/// Genesis hash anchor for the first record in a hash-chained journal.
pub const GENESIS_DIGEST: &str =
    "sha256:0000000000000000000000000000000000000000000000000000000000000000";

/// Why a journal operation failed. Messages never quote journal content.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JournalError {
    /// The journal could not be written or synced.
    Write,
    /// The journal exists but could not be read.
    Read,
    /// A line that is not a torn prefix could not be parsed.
    Unreadable,
    /// Another writer holds the journal.
    Busy,
    /// A line or the journal exceeds its bound.
    TooLarge,
    /// Hash-chain continuity or entry digest verification failed.
    HashChainBroken { seq: u64 },
}

impl std::fmt::Display for JournalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Write => formatter.write_str("the journal could not be written"),
            Self::Read => formatter.write_str("the journal could not be read"),
            Self::Unreadable => formatter.write_str("the journal is unreadable"),
            Self::Busy => formatter.write_str("another writer holds the journal"),
            Self::TooLarge => {
                formatter.write_str("a journal line or the journal exceeds its bound")
            }
            Self::HashChainBroken { seq } => {
                write!(formatter, "journal hash chain broken at sequence {seq}")
            }
        }
    }
}

impl std::error::Error for JournalError {}

/// The lines of a journal, in order, and how many torn lines were skipped.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Lines<T> {
    pub lines: Vec<T>,
    /// Torn prefixes skipped (a typed warning for the caller to report).
    pub torn: usize,
}

/// Appends one line and syncs it to disk before returning (caller owns writer lock).
pub fn append_line<T: Serialize>(path: &Path, line: &T) -> Result<(), JournalError> {
    append_within(path, line, MAX_JOURNAL_BYTES)
}

/// Appends a line that opens an intent, reserving [`MAX_LINE_BYTES`] so the
/// closing transition (`settled`, `abandoned`, `unknown`, `reconciled`) always fits.
pub fn append_opening_line<T: Serialize>(path: &Path, line: &T) -> Result<(), JournalError> {
    append_within(path, line, MAX_JOURNAL_BYTES - MAX_LINE_BYTES as u64)
}

fn append_within<T: Serialize>(path: &Path, line: &T, limit: u64) -> Result<(), JournalError> {
    let mut bytes = serde_json::to_vec(line).map_err(|_| JournalError::Write)?;
    bytes.push(b'\n');
    if bytes.len() > MAX_LINE_BYTES {
        return Err(JournalError::TooLarge);
    }
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent).map_err(|_| JournalError::Write)?;
        }
    }
    if torn_tail(path)? {
        bytes.insert(0, b'\n');
    }
    let current = match std::fs::metadata(path) {
        Ok(metadata) => metadata.len(),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => 0,
        Err(_) => return Err(JournalError::Write),
    };
    if current.saturating_add(bytes.len() as u64) > limit {
        return Err(JournalError::TooLarge);
    }
    let mut file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|_| JournalError::Write)?;
    file.write_all(&bytes).map_err(|_| JournalError::Write)?;
    file.sync_data().map_err(|_| JournalError::Write)?;
    sync_parent(path)
}

#[cfg(unix)]
fn sync_parent(path: &Path) -> Result<(), JournalError> {
    match path.parent() {
        Some(parent) if !parent.as_os_str().is_empty() => File::open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|_| JournalError::Write),
        _ => Ok(()),
    }
}

#[cfg(not(unix))]
fn sync_parent(_path: &Path) -> Result<(), JournalError> {
    Ok(())
}

fn torn_tail(path: &Path) -> Result<bool, JournalError> {
    let mut file = match File::open(path) {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(false),
        Err(_) => return Err(JournalError::Write),
    };
    let length = file.metadata().map_err(|_| JournalError::Write)?.len();
    if length == 0 {
        return Ok(false);
    }
    let mut last = [0u8; 1];
    file.seek(SeekFrom::Start(length - 1))
        .and_then(|_| file.read_exact(&mut last))
        .map_err(|_| JournalError::Write)?;
    Ok(last[0] != b'\n')
}

/// Every line of the journal, in order. A missing journal has none.
pub fn read_lines<T: DeserializeOwned>(path: &Path) -> Result<Lines<T>, JournalError> {
    let file = match File::open(path) {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return Ok(Lines {
                lines: Vec::new(),
                torn: 0,
            })
        }
        Err(_) => return Err(JournalError::Read),
    };
    let mut text = Vec::new();
    file.take(MAX_JOURNAL_BYTES + 1)
        .read_to_end(&mut text)
        .map_err(|_| JournalError::Read)?;
    if text.len() as u64 > MAX_JOURNAL_BYTES {
        return Err(JournalError::TooLarge);
    }
    let mut lines = Vec::new();
    let mut torn = 0;
    for raw in text.split(|byte| *byte == b'\n') {
        let end = raw
            .iter()
            .rposition(|byte| *byte != 0)
            .map_or(0, |last| last + 1);
        let raw = &raw[..end];
        if raw.iter().all(u8::is_ascii_whitespace) {
            continue;
        }
        match serde_json::from_slice::<T>(raw) {
            Ok(line) => lines.push(line),
            Err(error) if error.is_eof() => torn += 1,
            Err(_) => return Err(JournalError::Unreadable),
        }
    }
    Ok(Lines { lines, torn })
}

/// Six-state lifecycle of an external effect intent (`effect_intent.schema.json`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum IntentState {
    Pending,
    Dispatched,
    Settled,
    Abandoned,
    Unknown,
    Reconciled,
}

impl IntentState {
    /// Allowed state transitions matching `transitions/effect_intent.json`.
    pub fn may_become(self, next: IntentState) -> bool {
        use IntentState::*;
        matches!(
            (self, next),
            (Pending, Dispatched | Settled | Abandoned | Reconciled)
                | (Dispatched, Settled | Unknown | Reconciled)
                | (Unknown, Reconciled)
        )
    }

    /// Whether a provider still has to decide what happened.
    pub fn is_open(self) -> bool {
        matches!(
            self,
            IntentState::Pending | IntentState::Dispatched | IntentState::Unknown
        )
    }
}

/// Folds `(intent_id, IntentState)` events in journal order and returns open intents.
/// Fails closed on illegal transitions or orphan non-pending initial states.
pub fn recover<'a>(
    events: impl IntoIterator<Item = (&'a str, IntentState)>,
) -> Result<Vec<(String, IntentState)>, JournalError> {
    let mut states: Vec<(String, IntentState)> = Vec::new();
    let mut index: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
    for (id, next) in events {
        match index.get(id) {
            None if next == IntentState::Pending => {
                index.insert(id.to_owned(), states.len());
                states.push((id.to_owned(), next));
            }
            None => return Err(JournalError::Unreadable),
            Some(&at) if states[at].1.may_become(next) => states[at].1 = next,
            Some(_) => return Err(JournalError::Unreadable),
        }
    }
    states.retain(|(_, state)| state.is_open());
    Ok(states)
}

/// Tamper-evident hash-chained journal record.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChainedRecord<T> {
    pub journal_seq: u64,
    pub prev_digest: String,
    pub entry_digest: String,
    pub record: T,
}

fn canonical_value_bytes(val: &serde_json::Value) -> Vec<u8> {
    fn write_canon(v: &serde_json::Value, out: &mut Vec<u8>) {
        match v {
            serde_json::Value::Null => out.extend_from_slice(b"null"),
            serde_json::Value::Bool(true) => out.extend_from_slice(b"true"),
            serde_json::Value::Bool(false) => out.extend_from_slice(b"false"),
            serde_json::Value::Number(n) => out.extend_from_slice(n.to_string().as_bytes()),
            serde_json::Value::String(s) => {
                let encoded = serde_json::to_string(s).unwrap_or_default();
                out.extend_from_slice(encoded.as_bytes());
            }
            serde_json::Value::Array(items) => {
                out.push(b'[');
                for (i, item) in items.iter().enumerate() {
                    if i > 0 {
                        out.push(b',');
                    }
                    write_canon(item, out);
                }
                out.push(b']');
            }
            serde_json::Value::Object(map) => {
                out.push(b'{');
                let mut keys: Vec<&String> = map.keys().collect();
                keys.sort_by(|a, b| a.encode_utf16().cmp(b.encode_utf16()));
                for (i, k) in keys.iter().enumerate() {
                    if i > 0 {
                        out.push(b',');
                    }
                    let k_enc = serde_json::to_string(k).unwrap_or_default();
                    out.extend_from_slice(k_enc.as_bytes());
                    out.push(b':');
                    write_canon(&map[*k], out);
                }
                out.push(b'}');
            }
        }
    }
    let mut buf = Vec::new();
    write_canon(val, &mut buf);
    buf
}

fn compute_chained_digest<T: Serialize>(
    journal_seq: u64,
    prev_digest: &str,
    record: &T,
) -> Result<String, JournalError> {
    let record_val = serde_json::to_value(record).map_err(|_| JournalError::Write)?;
    let envelope = serde_json::json!({
        "journal_seq": journal_seq,
        "prev_digest": prev_digest,
        "record": record_val,
    });
    let bytes = canonical_value_bytes(&envelope);
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

/// Appends `record` to a hash-chained journal under the shared OS writer lock,
/// verifying the existing chain before appending.
pub fn append_chained<T: Serialize + DeserializeOwned>(
    path: &Path,
    record: T,
    wait: std::time::Duration,
) -> Result<ChainedRecord<T>, JournalError> {
    with_lock(path, wait, || {
        let existing = read_and_verify_chain::<T>(path)?;
        let (next_seq, prev_digest) = match existing.lines.last() {
            Some(last) => (last.journal_seq + 1, last.entry_digest.clone()),
            None => (0, GENESIS_DIGEST.to_owned()),
        };
        let entry_digest = compute_chained_digest(next_seq, &prev_digest, &record)?;
        let chained = ChainedRecord {
            journal_seq: next_seq,
            prev_digest,
            entry_digest,
            record,
        };
        append_line(path, &chained)?;
        Ok(chained)
    })
}

/// Reads all records from a hash-chained journal and verifies sequence continuity,
/// absence of truncated/torn lines, and every entry's SHA-256 digest. Fails closed
/// with [`JournalError::HashChainBroken`] on any tampering, truncation, deletion,
/// reordering, or forged digest.
pub fn read_and_verify_chain<T: Serialize + DeserializeOwned>(
    path: &Path,
) -> Result<Lines<ChainedRecord<T>>, JournalError> {
    let parsed: Lines<ChainedRecord<T>> = read_lines(path)?;
    if parsed.torn > 0 {
        return Err(JournalError::HashChainBroken {
            seq: parsed.lines.len() as u64,
        });
    }
    let mut expected_prev = GENESIS_DIGEST;
    for (idx, item) in parsed.lines.iter().enumerate() {
        let expected_seq = idx as u64;
        if item.journal_seq != expected_seq || item.prev_digest != expected_prev {
            return Err(JournalError::HashChainBroken { seq: expected_seq });
        }
        let recomputed = compute_chained_digest(item.journal_seq, &item.prev_digest, &item.record)?;
        if item.entry_digest != recomputed {
            return Err(JournalError::HashChainBroken { seq: expected_seq });
        }
        expected_prev = &item.entry_digest;
    }
    Ok(parsed)
}

/// One exclusive writer of a journal.
#[derive(Debug)]
pub struct Journal {
    path: PathBuf,
    _lock: File,
}

fn lock_file(path: &Path) -> Result<File, JournalError> {
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent).map_err(|_| JournalError::Write)?;
        }
    }
    let mut lock_name = path.as_os_str().to_owned();
    lock_name.push(".lock");
    let mut options = std::fs::OpenOptions::new();
    options.create(true).truncate(false).read(true).write(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        const FILE_SHARE_READ: u32 = 0x1;
        const FILE_SHARE_WRITE: u32 = 0x2;
        options.share_mode(FILE_SHARE_READ | FILE_SHARE_WRITE);
    }
    options
        .open(PathBuf::from(lock_name))
        .map_err(|_| JournalError::Write)
}

fn lock_within(path: &Path, wait: std::time::Duration) -> Result<File, JournalError> {
    let deadline = std::time::Instant::now() + wait;
    let turn = Turn::wait(path, deadline)?;
    let lock = lock_file(path)?;
    let taken = loop {
        match fs4::FileExt::try_lock(&lock) {
            Ok(()) => break Ok(lock),
            Err(fs4::TryLockError::WouldBlock) if std::time::Instant::now() < deadline => {
                std::thread::sleep(std::time::Duration::from_millis(2));
            }
            Err(fs4::TryLockError::WouldBlock) => break Err(JournalError::Busy),
            Err(_) => break Err(JournalError::Write),
        }
    };
    drop(turn);
    taken
}

struct Turn {
    key: PathBuf,
    ticket: u64,
}

struct Queue {
    next: u64,
    waiting: std::collections::VecDeque<u64>,
}

static LINES: std::sync::OnceLock<(
    std::sync::Mutex<std::collections::HashMap<PathBuf, Queue>>,
    std::sync::Condvar,
)> = std::sync::OnceLock::new();

fn lines() -> &'static (
    std::sync::Mutex<std::collections::HashMap<PathBuf, Queue>>,
    std::sync::Condvar,
) {
    LINES.get_or_init(|| {
        (
            std::sync::Mutex::new(std::collections::HashMap::new()),
            std::sync::Condvar::new(),
        )
    })
}

impl Turn {
    fn wait(path: &Path, deadline: std::time::Instant) -> Result<Self, JournalError> {
        let (map, ready) = lines();
        let mut guard = map
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        let key = path.to_path_buf();
        let line = guard.entry(key.clone()).or_insert(Queue {
            next: 0,
            waiting: std::collections::VecDeque::new(),
        });
        let ticket = line.next;
        line.next += 1;
        line.waiting.push_back(ticket);
        loop {
            let first = guard
                .get(&key)
                .and_then(|line| line.waiting.front().copied());
            if first == Some(ticket) {
                return Ok(Self { key, ticket });
            }
            let now = std::time::Instant::now();
            if now >= deadline {
                leave(&mut guard, &key, ticket);
                ready.notify_all();
                return Err(JournalError::Busy);
            }
            guard = ready
                .wait_timeout(guard, deadline - now)
                .unwrap_or_else(std::sync::PoisonError::into_inner)
                .0;
        }
    }
}

#[cfg(test)]
fn queued_for(path: &Path) -> usize {
    let (map, _) = lines();
    map.lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner)
        .get(path)
        .map_or(0, |queue| queue.waiting.len())
}

fn leave(map: &mut std::collections::HashMap<PathBuf, Queue>, key: &Path, ticket: u64) {
    if let Some(queue) = map.get_mut(key) {
        queue.waiting.retain(|waiting| *waiting != ticket);
        if queue.waiting.is_empty() {
            map.remove(key);
        }
    }
}

impl Drop for Turn {
    fn drop(&mut self) {
        let (map, ready) = lines();
        let mut guard = map
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        leave(&mut guard, &self.key, self.ticket);
        drop(guard);
        ready.notify_all();
    }
}

/// Appends under the journal's writer lock.
pub fn append_shared<T: Serialize>(
    path: &Path,
    line: &T,
    wait: std::time::Duration,
) -> Result<(), JournalError> {
    let _lock = lock_within(path, wait)?;
    append_line(path, line)
}

/// [`append_opening_line`] under the journal's writer lock.
pub fn append_opening_shared<T: Serialize>(
    path: &Path,
    line: &T,
    wait: std::time::Duration,
) -> Result<(), JournalError> {
    let _lock = lock_within(path, wait)?;
    append_opening_line(path, line)
}

/// Runs `change` with the journal's writer lock held.
pub fn with_lock<R>(
    path: &Path,
    wait: std::time::Duration,
    change: impl FnOnce() -> Result<R, JournalError>,
) -> Result<R, JournalError> {
    let _lock = lock_within(path, wait)?;
    change()
}

/// Atomically replaces the journal with `lines` via temp-file sync + rename.
pub fn rewrite<T: Serialize>(path: &Path, lines: &[T]) -> Result<(), JournalError> {
    let mut bytes = Vec::new();
    for line in lines {
        let mut encoded = serde_json::to_vec(line).map_err(|_| JournalError::Write)?;
        encoded.push(b'\n');
        if encoded.len() > MAX_LINE_BYTES {
            return Err(JournalError::TooLarge);
        }
        bytes.extend_from_slice(&encoded);
    }
    if bytes.len() as u64 > MAX_JOURNAL_BYTES - MAX_LINE_BYTES as u64 {
        return Err(JournalError::TooLarge);
    }
    let mut temporary = path.as_os_str().to_owned();
    temporary.push(".rewrite");
    let temporary = PathBuf::from(temporary);
    {
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(&temporary)
            .map_err(|_| JournalError::Write)?;
        file.write_all(&bytes).map_err(|_| JournalError::Write)?;
        file.sync_all().map_err(|_| JournalError::Write)?;
    }
    std::fs::rename(&temporary, path).map_err(|_| JournalError::Write)?;
    sync_parent(path)
}

impl Journal {
    /// Opens the journal for writing, refusing while another writer holds it.
    pub fn open(path: impl Into<PathBuf>) -> Result<Self, JournalError> {
        let path = path.into();
        let lock = lock_file(&path)?;
        match fs4::FileExt::try_lock(&lock) {
            Ok(()) => Ok(Self { path, _lock: lock }),
            Err(fs4::TryLockError::WouldBlock) => Err(JournalError::Busy),
            Err(_) => Err(JournalError::Write),
        }
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Appends one line and syncs it before returning.
    pub fn append<T: Serialize>(&self, line: &T) -> Result<(), JournalError> {
        append_line(&self.path, line)
    }

    /// Every line written so far, in order.
    pub fn read<T: DeserializeOwned>(&self) -> Result<Lines<T>, JournalError> {
        read_lines(&self.path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
    struct Line {
        event: String,
        id: String,
    }

    fn line(event: &str, id: &str) -> Line {
        Line {
            event: event.into(),
            id: id.into(),
        }
    }

    fn dir(label: &str) -> PathBuf {
        let nanos = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "wispral-journal-{label}-{}-{nanos}",
            std::process::id()
        ));
        std::fs::create_dir_all(&path).unwrap();
        path
    }

    #[test]
    fn lines_round_trip_in_order_and_are_byte_stable() {
        let path = dir("round").join("intents.jsonl");
        append_line(&path, &line("pending", "r1")).unwrap();
        append_line(&path, &line("settled", "r1")).unwrap();
        assert_eq!(
            std::fs::read_to_string(&path).unwrap(),
            "{\"event\":\"pending\",\"id\":\"r1\"}\n{\"event\":\"settled\",\"id\":\"r1\"}\n"
        );
        let read: Lines<Line> = read_lines(&path).unwrap();
        assert_eq!(read.lines, [line("pending", "r1"), line("settled", "r1")]);
        assert_eq!(read.torn, 0);
    }

    #[test]
    fn a_missing_journal_has_no_lines() {
        let read: Lines<Line> = read_lines(&dir("missing").join("none.jsonl")).unwrap();
        assert!(read.lines.is_empty());
        assert_eq!(read.torn, 0);
    }

    #[test]
    fn a_torn_tail_is_counted_and_sealed_by_the_next_append() {
        let path = dir("torn").join("intents.jsonl");
        append_line(&path, &line("pending", "r1")).unwrap();
        std::fs::OpenOptions::new()
            .append(true)
            .open(&path)
            .unwrap()
            .write_all(b"{\"event\":\"pend")
            .unwrap();
        let read: Lines<Line> = read_lines(&path).unwrap();
        assert_eq!(read.lines, [line("pending", "r1")]);
        assert_eq!(read.torn, 1);
        append_line(&path, &line("pending", "r2")).unwrap();
        let read: Lines<Line> = read_lines(&path).unwrap();
        assert_eq!(read.lines, [line("pending", "r1"), line("pending", "r2")]);
        assert_eq!(read.torn, 1);
    }

    #[test]
    fn zero_filled_runs_are_dropped() {
        let path = dir("zeros").join("intents.jsonl");
        append_line(&path, &line("pending", "r1")).unwrap();
        std::fs::OpenOptions::new()
            .append(true)
            .open(&path)
            .unwrap()
            .write_all(b"{\"event\":\"se\0\0\0\0\n\0\0\0")
            .unwrap();
        let read: Lines<Line> = read_lines(&path).unwrap();
        assert_eq!(read.lines, [line("pending", "r1")]);
        assert_eq!(read.torn, 1);
    }

    #[test]
    fn a_corrupt_complete_line_fails_closed() {
        let path = dir("corrupt").join("intents.jsonl");
        std::fs::write(&path, "{\"event\":\"pending\",\"id\":7}\n").unwrap();
        assert_eq!(
            read_lines::<Line>(&path).unwrap_err(),
            JournalError::Unreadable
        );
        std::fs::write(&path, "not json\n").unwrap();
        assert_eq!(
            read_lines::<Line>(&path).unwrap_err(),
            JournalError::Unreadable
        );
    }

    #[test]
    fn lines_and_journals_are_bounded() {
        let path = dir("bounds").join("intents.jsonl");
        let long = line("pending", &"x".repeat(MAX_LINE_BYTES));
        assert_eq!(
            append_line(&path, &long).unwrap_err(),
            JournalError::TooLarge
        );
        assert!(!path.exists());
        let fits = line("pending", &"x".repeat(MAX_LINE_BYTES - 64));
        append_line(&path, &fits).unwrap();
        let file = std::fs::OpenOptions::new().write(true).open(&path).unwrap();
        file.set_len(MAX_JOURNAL_BYTES + 1).unwrap();
        assert_eq!(
            read_lines::<Line>(&path).unwrap_err(),
            JournalError::TooLarge
        );
        drop(file);
        let _ = std::fs::remove_dir_all(path.parent().unwrap());
    }

    #[test]
    fn an_opening_line_always_leaves_room_for_its_closing_line() {
        let path = dir("reserve").join("intents.jsonl");
        append_line(&path, &line("pending", "r1")).unwrap();
        let file = std::fs::OpenOptions::new().write(true).open(&path).unwrap();
        file.set_len(MAX_JOURNAL_BYTES - MAX_LINE_BYTES as u64 - 8)
            .unwrap();
        drop(file);
        let mut ending = std::fs::OpenOptions::new()
            .append(true)
            .open(&path)
            .unwrap();
        ending.write_all(b"\n").unwrap();
        drop(ending);
        assert_eq!(
            append_opening_line(&path, &line("pending", "r2")).unwrap_err(),
            JournalError::TooLarge
        );
        append_line(&path, &line("settled", "r1")).unwrap();
        let _ = std::fs::remove_dir_all(path.parent().unwrap());
    }

    #[test]
    fn shared_appends_wait_for_the_lock_and_never_interleave() {
        let path = dir("shared").join("tasks.jsonl");
        let held = lock_within(&path, std::time::Duration::from_millis(0)).unwrap();
        assert_eq!(
            append_shared(
                &path,
                &line("pending", "r1"),
                std::time::Duration::from_millis(40)
            )
            .unwrap_err(),
            JournalError::Busy
        );
        assert!(!path.exists());
        drop(held);
        let writers: Vec<_> = (0..6)
            .map(|n| {
                let path = path.clone();
                std::thread::spawn(move || {
                    for k in 0..20 {
                        append_shared(
                            &path,
                            &line("pending", &format!("w{n}-{k}")),
                            std::time::Duration::from_secs(10),
                        )
                        .unwrap();
                    }
                })
            })
            .collect();
        for writer in writers {
            writer.join().unwrap();
        }
        let read: Lines<Line> = read_lines(&path).unwrap();
        assert_eq!(read.lines.len(), 120);
        assert_eq!(read.torn, 0);
    }

    #[test]
    fn a_waiting_writer_is_not_starved_by_one_that_keeps_retaking_the_lock() {
        let wait_until = |path: &Path, queued: usize| {
            let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
            while queued_for(path) < queued {
                assert!(std::time::Instant::now() < deadline, "threads never queued");
                std::thread::sleep(std::time::Duration::from_millis(1));
            }
        };
        for attempt in 0..5 {
            let path = dir(&format!("fair-{attempt}")).join("tasks.jsonl");
            let rounds = std::sync::Arc::new(std::sync::atomic::AtomicUsize::new(0));
            let held = lock_within(&path, std::time::Duration::from_secs(1)).unwrap();
            let waiter = {
                let path = path.clone();
                let rounds = std::sync::Arc::clone(&rounds);
                std::thread::spawn(move || {
                    let _held = lock_within(&path, std::time::Duration::from_secs(10)).unwrap();
                    rounds.load(std::sync::atomic::Ordering::SeqCst)
                })
            };
            wait_until(&path, 1);
            let hot = {
                let path = path.clone();
                let rounds = std::sync::Arc::clone(&rounds);
                std::thread::spawn(move || {
                    for _ in 0..5 {
                        let _held = lock_within(&path, std::time::Duration::from_secs(10)).unwrap();
                        rounds.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
                    }
                })
            };
            wait_until(&path, 2);
            drop(held);
            assert_eq!(waiter.join().unwrap(), 0);
            hot.join().unwrap();
        }
    }

    #[test]
    fn a_second_writer_is_refused_until_the_first_closes() {
        let path = dir("writer").join("intents.jsonl");
        let first = Journal::open(&path).unwrap();
        assert_eq!(Journal::open(&path).unwrap_err(), JournalError::Busy);
        first.append(&line("pending", "r1")).unwrap();
        drop(first);
        let second = Journal::open(&path).unwrap();
        let read: Lines<Line> = second.read().unwrap();
        assert_eq!(read.lines, [line("pending", "r1")]);
    }

    #[test]
    fn recover_keeps_dispatched_and_unknown_open_and_fails_closed_on_bad_transitions() {
        use IntentState::*;
        let open = recover([
            ("a", Pending),
            ("a", Dispatched),
            ("b", Pending),
            ("b", Dispatched),
            ("b", Unknown),
            ("c", Pending),
            ("c", Dispatched),
            ("c", Unknown),
            ("c", Reconciled),
        ])
        .unwrap();
        assert_eq!(
            open,
            [("a".to_string(), Dispatched), ("b".to_string(), Unknown)]
        );
        for invalid in [
            vec![("a", Settled)],
            vec![("a", Pending), ("a", Pending)],
            vec![("a", Pending), ("a", Settled), ("a", Dispatched)],
            vec![("a", Pending), ("a", Dispatched), ("a", Abandoned)],
        ] {
            assert_eq!(recover(invalid).unwrap_err(), JournalError::Unreadable);
        }
    }

    #[test]
    fn hash_chained_journal_detects_tampering_and_deletion() {
        let path = dir("chained").join("audit.jsonl");
        let wait = std::time::Duration::from_secs(2);
        let r0 = append_chained(&path, line("consent_granted", "c1"), wait).unwrap();
        let r1 = append_chained(&path, line("consent_revoked", "c1"), wait).unwrap();
        assert_eq!(r0.journal_seq, 0);
        assert_eq!(r0.prev_digest, GENESIS_DIGEST);
        assert_eq!(r1.journal_seq, 1);
        assert_eq!(r1.prev_digest, r0.entry_digest);

        let verified: Lines<ChainedRecord<Line>> = read_and_verify_chain(&path).unwrap();
        assert_eq!(verified.lines.len(), 2);

        // Tamper with record payload while keeping stored entry_digest.
        let raw = std::fs::read_to_string(&path).unwrap();
        let tampered = raw.replace("consent_revoked", "consent_granted");
        std::fs::write(&path, tampered).unwrap();
        assert_eq!(
            read_and_verify_chain::<Line>(&path).unwrap_err(),
            JournalError::HashChainBroken { seq: 1 }
        );

        // Truncating the final bytes of a committed chained record must fail closed
        // on both read_and_verify_chain and append_chained (never silently overwrite seq 1).
        let base_dir = dir("chained-torn");
        let torn_path = base_dir.join("audit.jsonl");
        append_chained(&torn_path, line("consent_granted", "c2"), wait).unwrap();
        append_chained(&torn_path, line("consent_revoked", "c2"), wait).unwrap();
        let mut bytes = std::fs::read(&torn_path).unwrap();
        bytes.truncate(bytes.len() - 6);
        std::fs::write(&torn_path, bytes).unwrap();
        assert_eq!(
            read_and_verify_chain::<Line>(&torn_path).unwrap_err(),
            JournalError::HashChainBroken { seq: 1 }
        );
        assert_eq!(
            append_chained(&torn_path, line("consent_check", "c2"), wait).unwrap_err(),
            JournalError::HashChainBroken { seq: 1 }
        );
        let _ = std::fs::remove_dir_all(&base_dir);
    }
}
