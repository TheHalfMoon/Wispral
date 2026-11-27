//! Wispral Connect (`wispral`): unified local CLI and MCP JSON-RPC 2.0 `stdio` server.
//!
//! Subcommands:
//! - `wispral doctor`: inspects environment, CAS model root, privacy posture, and zero-egress defaults;
//! - `wispral models`: lists or stages SHA-256 verified local model bundles;
//! - `wispral transcribe`: transcribes bounded local WAV files offline;
//! - `wispral speak`: synthesizes local WAV audio with Arabic/multilingual pronunciation support;
//! - `wispral translate`: runs entity- and negation-preserving bilingual translation;
//! - `wispral mcp`: starts the zero-listener Model Context Protocol JSON-RPC 2.0 `stdio` server;
//! - `wispral benchmark`: executes `WispralBench` and writes JSON/Markdown reports.

use std::io::{BufRead, Write};
use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};
use serde_json::{json, Value};
use wispral_adaptive::{ensure_not_reparse_or_symlink, HardwareTier, ModelCasStore};
use wispral_arabic::{detect_dialect_hint, VerbatimTranscript};
use wispral_audio::decode_wav_pcm16_bounded;
use wispral_bench::{render_markdown_report, run_core_benchmarks};
use wispral_memory::{MemoryPrivacyConfig, MemoryStore};
use wispral_policy::{compose_layers, CandidateDecision, LayerSource, PolicyLayer};
use wispral_speech::{
    DeterministicFormantTts, DeterministicLocalStt, OfflineGlossaryTranslator, SpeechToTextEngine,
    SynthesisRequest, TextToSpeechEngine,
};

#[derive(Parser, Debug)]
#[command(
    name = "wispral",
    version,
    about = "Wispral Connect — local-first voice intelligence CLI and MCP server"
)]
struct Cli {
    /// Override `$WISPRAL_HOME` state directory.
    #[arg(long, global = true)]
    wispral_home: Option<PathBuf>,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Inspect local Wispral environment, storage safety, and offline defaults.
    Doctor {
        #[arg(long)]
        json: bool,
    },
    /// Inspect or verify local CAS model artifacts.
    Models {
        #[arg(long)]
        stage_file: Option<PathBuf>,
        #[arg(long)]
        expected_sha256: Option<String>,
    },
    /// Transcribe a local 16-bit PCM WAV file offline.
    Transcribe {
        wav_path: PathBuf,
        #[arg(long, default_value = "en")]
        lang: String,
        #[arg(long)]
        json: bool,
    },
    /// Synthesize speech into a local 16-bit PCM WAV file.
    Speak {
        text: String,
        #[arg(long, short = 'o')]
        output: PathBuf,
        #[arg(long, default_value = "catalog:wispral:default")]
        voice: String,
        #[arg(long, default_value = "en")]
        lang: String,
    },
    /// Translate text while preserving technical entities, CLI flags, and negations.
    Translate {
        text: String,
        #[arg(long, default_value = "en")]
        to: String,
    },
    /// Run Model Context Protocol (MCP) JSON-RPC 2.0 server over stdio (zero network sockets).
    Mcp,
    /// Run reproducible WispralBench suites and output JSON / Markdown reports.
    Benchmark {
        #[arg(long)]
        output_json: Option<PathBuf>,
        #[arg(long)]
        output_md: Option<PathBuf>,
    },
}

fn resolve_wispral_home(override_dir: Option<PathBuf>) -> PathBuf {
    if let Some(p) = override_dir {
        return p;
    }
    if let Ok(env_home) = std::env::var("WISPRAL_HOME") {
        if !env_home.trim().is_empty() {
            return PathBuf::from(env_home);
        }
    }
    let base = std::env::var("LOCALAPPDATA")
        .or_else(|_| std::env::var("HOME"))
        .map(PathBuf::from)
        .unwrap_or_else(|_| std::env::temp_dir());
    base.join("Wispral")
}

fn build_doctor_payload(home: &Path) -> Value {
    let reparse_check = ensure_not_reparse_or_symlink(home).is_ok();
    let cas_ready = ModelCasStore::open(home).is_ok();
    let mem_ready = MemoryStore::open(home, MemoryPrivacyConfig::default()).is_ok();
    json!({
        "product_family": ["Wispral Core", "WisprSide", "WisprStudio", "Klaint", "Omalla"],
        "status": if reparse_check && cas_ready && mem_ready { "healthy" } else { "degraded" },
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "wispral_home": home.display().to_string(),
        "cas_reparse_safe": reparse_check,
        "cas_store_ready": cas_ready,
        "memory_store_ready": mem_ready,
        "default_keep_audio": false,
        "default_telemetry": "off",
        "mandatory_cloud_account": false,
        "default_tier_budget_mb": HardwareTier::T1StandardCpu.ram_budget_mb(),
    })
}

pub fn handle_mcp_request(home: &Path, req: &Value) -> Option<Value> {
    let method = req.get("method").and_then(Value::as_str)?;
    // Notifications (no `id`) receive no response frame per JSON-RPC 2.0
    let id_val = req.get("id")?.clone();

    match method {
        "initialize" => Some(json!({
            "jsonrpc": "2.0",
            "id": id_val,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": { "tools": {} },
                "serverInfo": {
                    "name": "wispral-connect-mcp",
                    "version": env!("CARGO_PKG_VERSION")
                }
            }
        })),
        "ping" => Some(json!({
            "jsonrpc": "2.0",
            "id": id_val,
            "result": {}
        })),
        "tools/list" => Some(json!({
            "jsonrpc": "2.0",
            "id": id_val,
            "result": {
                "tools": [
                    {
                        "name": "wispral_doctor",
                        "description": "Inspect local Wispral voice intelligence health, CAS storage, and privacy defaults.",
                        "inputSchema": { "type": "object", "properties": {} }
                    },
                    {
                        "name": "wispral_analyze_arabic",
                        "description": "Analyze Arabic/multilingual text into verbatim, FSI..PDI bidi-isolated display, match key, and dialect hint.",
                        "inputSchema": {
                            "type": "object",
                            "required": ["text"],
                            "properties": { "text": { "type": "string" } }
                        }
                    },
                    {
                        "name": "wispral_translate",
                        "description": "Translate text offline while preserving protected code entities and negations.",
                        "inputSchema": {
                            "type": "object",
                            "required": ["text", "target_lang"],
                            "properties": {
                                "text": { "type": "string" },
                                "target_lang": { "type": "string" }
                            }
                        }
                    },
                    {
                        "name": "wispral_speak_wav",
                        "description": "Synthesize spoken audio into a local WAV file.",
                        "inputSchema": {
                            "type": "object",
                            "required": ["text", "output_path"],
                            "properties": {
                                "text": { "type": "string" },
                                "output_path": { "type": "string" },
                                "language": { "type": "string" }
                            }
                        }
                    },
                    {
                        "name": "wispral_transcribe_wav",
                        "description": "Transcribe a local 16-bit PCM WAV file offline.",
                        "inputSchema": {
                            "type": "object",
                            "required": ["wav_path"],
                            "properties": {
                                "wav_path": { "type": "string" },
                                "language": { "type": "string" }
                            }
                        }
                    },
                    {
                        "name": "wispral_compose_policy",
                        "description": "Compose ordered Sentrdel/Wispral policy layers with monotone narrowing enforcement.",
                        "inputSchema": {
                            "type": "object",
                            "required": ["decisions"],
                            "properties": {
                                "decisions": {
                                    "type": "array",
                                    "items": { "type": "string" }
                                }
                            }
                        }
                    }
                ]
            }
        })),
        "tools/call" => {
            let params = req.get("params").cloned().unwrap_or_else(|| json!({}));
            let tool_name = params.get("name").and_then(Value::as_str).unwrap_or("");
            let args = params
                .get("arguments")
                .cloned()
                .unwrap_or_else(|| json!({}));

            let tool_res: Result<Value, String> = match tool_name {
                "wispral_doctor" => Ok(build_doctor_payload(home)),
                "wispral_analyze_arabic" => {
                    let text = args.get("text").and_then(Value::as_str).unwrap_or("");
                    let vt = VerbatimTranscript::new(text);
                    Ok(json!({
                        "verbatim": vt.as_str(),
                        "bidi_isolated": vt.to_bidi_isolated().as_str(),
                        "match_key": vt.to_match_key().as_key_str(),
                        "dialect_hint": detect_dialect_hint(text),
                    }))
                }
                "wispral_translate" => {
                    let text = args.get("text").and_then(Value::as_str).unwrap_or("");
                    let to = args
                        .get("target_lang")
                        .and_then(Value::as_str)
                        .unwrap_or("en");
                    OfflineGlossaryTranslator
                        .translate(text, to)
                        .map(|vt| {
                            json!({
                                "translated": vt.as_str(),
                                "bidi_isolated": vt.to_bidi_isolated().as_str()
                            })
                        })
                        .map_err(|e| e.to_string())
                }
                "wispral_speak_wav" => {
                    let text = args.get("text").and_then(Value::as_str).unwrap_or("");
                    let out_path = args
                        .get("output_path")
                        .and_then(Value::as_str)
                        .ok_or_else(|| "missing output_path".to_owned());
                    let lang = args.get("language").and_then(Value::as_str).unwrap_or("en");
                    out_path.and_then(|p| {
                        if let Some(parent) = Path::new(p).parent() {
                            if !parent.as_os_str().is_empty() {
                                std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
                            }
                        }
                        let art = DeterministicFormantTts
                            .synthesize(&SynthesisRequest {
                                text: VerbatimTranscript::new(text),
                                voice_id: "catalog:wispral:mcp".into(),
                                language: lang.to_owned(),
                                sample_rate_hz: 16000,
                                pronunciation_overrides: vec![],
                            })
                            .map_err(|e| e.to_string())?;
                        std::fs::write(p, art.to_wav_bytes()).map_err(|e| e.to_string())?;
                        Ok(json!({
                            "output_path": p,
                            "duration_ms": art.duration_ms,
                            "sample_rate_hz": art.sample_rate_hz
                        }))
                    })
                }
                "wispral_transcribe_wav" => {
                    let wav_p = args
                        .get("wav_path")
                        .and_then(Value::as_str)
                        .ok_or_else(|| "missing wav_path".to_owned());
                    let lang = args.get("language").and_then(Value::as_str);
                    wav_p.and_then(|p| {
                        let raw = std::fs::read(p).map_err(|e| e.to_string())?;
                        let (samples, sr) = decode_wav_pcm16_bounded(&raw, 32 * 1024 * 1024)
                            .map_err(|e| e.to_string())?;
                        let hyp = DeterministicLocalStt::new()
                            .transcribe(&samples, sr, lang)
                            .map_err(|e| e.to_string())?;
                        Ok(json!({
                            "transcript": hyp.transcript.as_str(),
                            "language": hyp.language,
                            "model_id": hyp.model_id
                        }))
                    })
                }
                "wispral_compose_policy" => {
                    let arr = args
                        .get("decisions")
                        .and_then(Value::as_array)
                        .cloned()
                        .unwrap_or_default();
                    let parsed: Result<Vec<PolicyLayer>, String> = arr
                        .into_iter()
                        .map(|v| {
                            let d: CandidateDecision =
                                serde_json::from_value(v).map_err(|e| e.to_string())?;
                            Ok(PolicyLayer {
                                source: LayerSource::Tenant,
                                decision: d,
                            })
                        })
                        .collect();
                    parsed.and_then(|layers| {
                        compose_layers(&layers)
                            .map(|cand| json!({ "candidate_decision": cand }))
                            .map_err(|e| e.to_string())
                    })
                }
                other => Err(format!("unknown MCP tool `{other}`")),
            };

            match tool_res {
                Ok(val) => Some(json!({
                    "jsonrpc": "2.0",
                    "id": id_val,
                    "result": {
                        "content": [{ "type": "text", "text": serde_json::to_string(&val).unwrap_or_default() }],
                        "isError": false
                    }
                })),
                Err(err_msg) => Some(json!({
                    "jsonrpc": "2.0",
                    "id": id_val,
                    "result": {
                        "content": [{ "type": "text", "text": err_msg }],
                        "isError": true
                    }
                })),
            }
        }
        other => Some(json!({
            "jsonrpc": "2.0",
            "id": id_val,
            "error": {
                "code": -32601,
                "message": format!("Method not found: {other}")
            }
        })),
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    let home = resolve_wispral_home(cli.wispral_home);

    match cli.command {
        Commands::Doctor { json: as_json } => {
            let payload = build_doctor_payload(&home);
            if as_json {
                println!("{}", serde_json::to_string_pretty(&payload)?);
            } else {
                println!(
                    "Wispral Connect Doctor: {} (home: {})",
                    payload["status"].as_str().unwrap_or("unknown"),
                    payload["wispral_home"].as_str().unwrap_or("")
                );
            }
        }
        Commands::Models {
            stage_file,
            expected_sha256,
        } => {
            let store = ModelCasStore::open(&home)?;
            if let (Some(src), Some(sha)) = (stage_file, expected_sha256) {
                let staged = store.stage_verified_blob(&src, &sha)?;
                println!(
                    "{}",
                    serde_json::to_string_pretty(&json!({
                        "status": "staged",
                        "blob_path": staged.display().to_string(),
                        "sha256": sha
                    }))?
                );
            } else {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&json!({
                        "status": "ready",
                        "models_root": home.join("models").display().to_string()
                    }))?
                );
            }
        }
        Commands::Transcribe {
            wav_path,
            lang,
            json: as_json,
        } => {
            let raw = std::fs::read(&wav_path)?;
            let (samples, sr) = decode_wav_pcm16_bounded(&raw, 64 * 1024 * 1024)?;
            let hyp = DeterministicLocalStt::new().transcribe(&samples, sr, Some(&lang))?;
            if as_json {
                println!("{}", serde_json::to_string_pretty(&hyp)?);
            } else {
                println!("{}", hyp.transcript.to_bidi_isolated().as_str());
            }
        }
        Commands::Speak {
            text,
            output,
            voice,
            lang,
        } => {
            let art = DeterministicFormantTts.synthesize(&SynthesisRequest {
                text: VerbatimTranscript::new(text),
                voice_id: voice,
                language: lang,
                sample_rate_hz: 16000,
                pronunciation_overrides: vec![],
            })?;
            if let Some(parent) = output.parent() {
                if !parent.as_os_str().is_empty() {
                    std::fs::create_dir_all(parent)?;
                }
            }
            std::fs::write(&output, art.to_wav_bytes())?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "status": "ok",
                    "output": output.display().to_string(),
                    "duration_ms": art.duration_ms,
                    "sample_rate_hz": art.sample_rate_hz
                }))?
            );
        }
        Commands::Translate { text, to } => {
            let out = OfflineGlossaryTranslator.translate(&text, &to)?;
            println!("{}", out.to_bidi_isolated().as_str());
        }
        Commands::Mcp => {
            let stdin = std::io::stdin();
            let mut stdout = std::io::stdout().lock();
            for line in stdin.lock().lines() {
                let line = line?;
                if line.trim().is_empty() {
                    continue;
                }
                let parsed: Value = match serde_json::from_str(&line) {
                    Ok(v) => v,
                    Err(e) => {
                        let err = json!({
                            "jsonrpc": "2.0",
                            "id": Value::Null,
                            "error": { "code": -32700, "message": format!("Parse error: {e}") }
                        });
                        writeln!(stdout, "{}", serde_json::to_string(&err)?)?;
                        stdout.flush()?;
                        continue;
                    }
                };
                if let Some(resp) = handle_mcp_request(&home, &parsed) {
                    writeln!(stdout, "{}", serde_json::to_string(&resp)?)?;
                    stdout.flush()?;
                }
            }
        }
        Commands::Benchmark {
            output_json,
            output_md,
        } => {
            let rep = run_core_benchmarks();
            let json_str = serde_json::to_string_pretty(&rep)?;
            let md_str = render_markdown_report(&rep);
            if let Some(jp) = output_json {
                if let Some(parent) = jp.parent() {
                    if !parent.as_os_str().is_empty() {
                        std::fs::create_dir_all(parent)?;
                    }
                }
                std::fs::write(jp, &json_str)?;
            }
            if let Some(mp) = output_md {
                if let Some(parent) = mp.parent() {
                    if !parent.as_os_str().is_empty() {
                        std::fs::create_dir_all(parent)?;
                    }
                }
                std::fs::write(mp, &md_str)?;
            }
            println!("{json_str}");
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mcp_stdio_handler_serves_initialize_tools_list_and_arabic_and_wav_tools() {
        let dir = std::env::temp_dir().join(format!("wispral-mcp-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);

        let init = handle_mcp_request(
            &dir,
            &json!({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        )
        .unwrap();
        assert_eq!(init["result"]["serverInfo"]["name"], "wispral-connect-mcp");

        // Notifications return None
        assert!(handle_mcp_request(
            &dir,
            &json!({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        )
        .is_none());

        let list = handle_mcp_request(
            &dir,
            &json!({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        )
        .unwrap();
        assert_eq!(list["result"]["tools"].as_array().unwrap().len(), 6);

        let wav_out = dir.join("test_out.wav");
        let speak = handle_mcp_request(
            &dir,
            &json!({
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "wispral_speak_wav",
                    "arguments": {
                        "text": "مرحباً بكم في Wispral",
                        "output_path": wav_out.display().to_string(),
                        "language": "ar"
                    }
                }
            }),
        )
        .unwrap();
        assert_eq!(speak["result"]["isError"], false);
        assert!(wav_out.exists());

        let trans = handle_mcp_request(
            &dir,
            &json!({
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "wispral_transcribe_wav",
                    "arguments": {
                        "wav_path": wav_out.display().to_string(),
                        "language": "ar"
                    }
                }
            }),
        )
        .unwrap();
        assert_eq!(trans["result"]["isError"], false);

        let _ = std::fs::remove_dir_all(&dir);
    }
}
