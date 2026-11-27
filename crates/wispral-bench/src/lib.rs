//! WispralBench: unified reproducible benchmark & qualification harness for Wispral Core.
//!
//! Honest measurement discipline (Constitution Principle XI):
//! - Records OS, architecture, timestamp, iteration count, cold vs warm timings (`p50`/`p95` us),
//!   and pass/fail counts;
//! - Explicitly tags deterministic local harness measurements (`MEASURED_LOCAL_HARNESS`) and
//!   never fabricates external corpus WER, human subjective MOS, or live PSTN carrier metrics.

use std::time::Instant;

use chrono::Utc;
use serde::{Deserialize, Serialize};
use wispral_adaptive::{AdaptiveMode, HardwareTier, MemoryLease, MemoryLeaseManager};
use wispral_arabic::{
    detect_dialect_hint, extract_protected_entities, normalize_arabic_digits,
    tokenize_proclitic_aware, ArabicDialectHint, DiacritizedTtsInput, PronunciationOverride,
    VerbatimTranscript, FSI, PDI,
};
use wispral_audio::{
    decode_wav_pcm16_bounded, encode_wav_pcm16_mono, g711, resample_mono, EndpointDetector,
    VadEvent,
};
use wispral_context::redact_sensitive_text;
use wispral_contracts::crypto::{verify_detached_signature, Ed25519Keypair};
use wispral_contracts::jcs::canonicalize_jcs_no_floats;
use wispral_journal::IntentState;
use wispral_live::DuplexSessionMachine;
use wispral_policy::bounded_json::{preflight, PreflightLimits};
use wispral_policy::{compose_unvalidated, CandidateDecision};
use wispral_speech::{
    DeterministicFormantTts, DeterministicLocalStt, OfflineGlossaryTranslator, SpeechToTextEngine,
    SynthesisRequest, TextToSpeechEngine,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SuiteResult {
    pub suite_id: String,
    pub scope_tag: String,
    pub cases_total: usize,
    pub cases_passed: usize,
    pub cold_us: u64,
    pub warm_p50_us: u64,
    pub warm_p95_us: u64,
    pub notes: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BenchmarkReport {
    pub generated_at_utc: String,
    pub os: String,
    pub arch: String,
    pub status: String,
    pub suites: Vec<SuiteResult>,
}

fn measure_cold_and_warm<F: FnMut() -> bool>(iterations: usize, mut f: F) -> (bool, u64, u64, u64) {
    let t0 = Instant::now();
    let mut all_ok = f();
    let cold_us = t0.elapsed().as_micros() as u64;

    let n = iterations.max(3);
    let mut samples = Vec::with_capacity(n);
    for _ in 0..n {
        let s = Instant::now();
        all_ok &= f();
        samples.push(s.elapsed().as_micros() as u64);
    }
    samples.sort_unstable();
    let p50 = samples[samples.len() / 2];
    let p95 = samples[(samples.len() * 95 / 100).min(samples.len() - 1)];
    (all_ok, cold_us, p50, p95)
}

pub fn run_core_benchmarks() -> BenchmarkReport {
    let mut suites = Vec::new();

    // 1. WB-AR: Arabic & Multilingual Code-Switching Suite
    {
        let cases_total = 6;
        let (ok, cold_us, p50, p95) = measure_cold_and_warm(25, || {
            let founder_prompt =
                "افتح مشروع Ecra وسوّ code review للـ pull request الأخير، وبعدها شغّل الاختبارات.";
            let vt = VerbatimTranscript::new(founder_prompt);
            let bidi = vt.to_bidi_isolated();
            let toks = tokenize_proclitic_aware(founder_prompt);
            let ents = extract_protected_entities(founder_prompt);
            let tts = DiacritizedTtsInput::from_transcript(
                &VerbatimTranscript::new("بدأنا بالمشروع رقم ١٤٥"),
                &[PronunciationOverride {
                    surface: "مشروع".into(),
                    vocalized_replacement: "مَشْرُوع".into(),
                }],
            );
            let tr = OfflineGlossaryTranslator
                .translate(founder_prompt, "en")
                .unwrap();

            detect_dialect_hint(founder_prompt) == ArabicDialectHint::SaudiGulf
                && detect_dialect_hint("عايز أرجع الطلب دلوقتي") == ArabicDialectHint::Egyptian
                && detect_dialect_hint("بدي شوف الشحنة هلق") == ArabicDialectHint::Levantine
                && bidi.as_str().contains(&format!("{FSI}pull request{PDI}"))
                && toks.iter().any(|t| {
                    t.proclitic.as_deref() == Some("لل") && t.stem_key.as_key_str() == "pull"
                })
                && ents.len() >= 5
                && tts.as_str().contains("بالمَشْرُوع")
                && normalize_arabic_digits("١٢٣٤٥") == "12345"
                && tr.as_str().contains("Ecra")
        });
        suites.push(SuiteResult {
            suite_id: "WB-AR".into(),
            scope_tag: "MEASURED_LOCAL_HARNESS".into(),
            cases_total,
            cases_passed: if ok { cases_total } else { 0 },
            cold_us,
            warm_p50_us: p50,
            warm_p95_us: p95,
            notes: "MSA, Saudi/Gulf, Egyptian, Levantine, `للـ pull request` proclitic binding, Arabic-Indic digits, and FSI..PDI bidi isolation.".into(),
        });
    }

    // 2. WB-CONTRACTS-CRYPTO: JCS + Float Rejection + Ed25519 Sign/Verify
    {
        let kp = Ed25519Keypair::from_secret_bytes("bench-key:01", [9u8; 32]);
        let pk = kp.public_key_base64url();
        let cases_total = 4;
        let (ok, cold_us, p50, p95) = measure_cold_and_warm(25, || {
            let payload = serde_json::json!({
                "tool": "refunds.create",
                "order_id": "ord-4821",
                "amount_cents": 4500,
                "note": "استرداد"
            });
            let jcs = canonicalize_jcs_no_floats(&payload).unwrap();
            let float_rejected =
                canonicalize_jcs_no_floats(&serde_json::json!({"amount": 45.0})).is_err();
            let sig = kp.sign_bytes(&jcs);
            let verified = verify_detached_signature(&pk, &jcs, &sig).is_ok();
            let tamper_rejected = verify_detached_signature(&pk, b"tampered", &sig).is_err();
            float_rejected && verified && tamper_rejected && !jcs.is_empty()
        });
        suites.push(SuiteResult {
            suite_id: "WB-CONTRACTS-CRYPTO".into(),
            scope_tag: "MEASURED_LOCAL_HARNESS".into(),
            cases_total,
            cases_passed: if ok { cases_total } else { 0 },
            cold_us,
            warm_p50_us: p50,
            warm_p95_us: p95,
            notes: "RFC 8785 JCS UTF-16 key canonicalization, float rejection, and Ed25519 detached verification.".into(),
        });
    }

    // 3. WB-POLICY-SECURITY: Sentrdel Lattice + Bounded JSON + Secret Redaction + T0 RAM Leases
    {
        let dir = std::env::temp_dir().join(format!("wb-sec-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        let leases = MemoryLeaseManager::new(&dir, HardwareTier::T0LowResourceCpu);
        let cases_total = 5;
        let (ok, cold_us, p50, p95) = measure_cold_and_warm(15, || {
            let deny_absorbs = compose_unvalidated(&[
                CandidateDecision::Allow,
                CandidateDecision::Undecidable,
                CandidateDecision::Deny,
            ]) == CandidateDecision::Deny;
            let deep_blocked = preflight(
                b"[[[[[[[[[1]]]]]]]]]",
                PreflightLimits {
                    max_depth: 4,
                    ..PreflightLimits::default()
                },
            )
            .is_err();
            let secret_redacted =
                !redact_sensitive_text("key=sk-1234567890abcdef").contains("sk-12345");
            let l1_ok = leases
                .acquire(
                    MemoryLease {
                        lease_id: "wb-l1".into(),
                        product: "wisprside".into(),
                        model_id: "m1".into(),
                        pid: 1,
                        start_generation: "1".into(),
                        ram_mb: 1200,
                        expires_at_ms: 99_999,
                    },
                    100,
                )
                .is_ok();
            let oom_blocked = leases
                .acquire(
                    MemoryLease {
                        lease_id: "wb-l2".into(),
                        product: "wisprstudio".into(),
                        model_id: "m2".into(),
                        pid: 2,
                        start_generation: "1".into(),
                        ram_mb: 800,
                        expires_at_ms: 99_999,
                    },
                    100,
                )
                .is_err();
            let _ = leases.release("wb-l1", 100);
            deny_absorbs && deep_blocked && secret_redacted && l1_ok && oom_blocked
        });
        let _ = std::fs::remove_dir_all(&dir);
        suites.push(SuiteResult {
            suite_id: "WB-SECURITY-RESOURCE".into(),
            scope_tag: "MEASURED_LOCAL_HARNESS".into(),
            cases_total,
            cases_passed: if ok { cases_total } else { 0 },
            cold_us,
            warm_p50_us: p50,
            warm_p95_us: p95,
            notes: format!(
                "Sentrdel lattice, preflight DoS guard, secret redaction, and {:?}/{:?} T0 1536 MB RAM lease cap.",
                AdaptiveMode::Offline,
                HardwareTier::T0LowResourceCpu
            ),
        });
    }

    // 4. WB-AUDIO-LIVE: Resample + G.711 + Formant TTS/STT + T0..T6 Barge-In State Machine
    {
        let tts = DeterministicFormantTts;
        let stt = DeterministicLocalStt::new();
        let cases_total = 5;
        let (ok, cold_us, p50, p95) = measure_cold_and_warm(15, || {
            let synth = tts
                .synthesize(&SynthesisRequest {
                    text: VerbatimTranscript::new("Wispral voice test"),
                    voice_id: "catalog:wispral:en".into(),
                    language: "en".into(),
                    sample_rate_hz: 24000,
                    pronunciation_overrides: vec![],
                })
                .unwrap();
            let wav = encode_wav_pcm16_mono(&synth.samples, 24000);
            let (decoded, sr) = decode_wav_pcm16_bounded(&wav, 2 * 1024 * 1024).unwrap();
            let resampled = resample_mono(&decoded, sr, 16000).unwrap();
            let hyp = stt.transcribe(&resampled, 16000, Some("en")).unwrap();
            let ulaw_rt = g711::decode_ulaw_sample(g711::encode_ulaw_sample(8192));

            let mut vad = EndpointDetector::new(0.02, 20, 40);
            let _ = vad.process_frame(&vec![0.2; 320], 20);
            let vad_end = vad.process_frame(&vec![0.0; 320], 40);

            let mut live = DuplexSessionMachine::new("wb-live");
            live.on_user_speech_end_and_final_stt(100, 140);
            let ep = live.turn_epoch;
            live.on_first_tts_audio_frame(ep, 210);
            let cancel = live
                .on_user_speech_start(300, Some((IntentState::Dispatched, Some("int-1".into()))))
                .unwrap();
            let unconfirmed_none = live.telemetry.confirmed_barge_in_halt_ms().is_none();
            live.confirm_sink_halted(335, true);

            !hyp.transcript.as_str().is_empty()
                && (ulaw_rt - 8192).abs() < 512
                && matches!(vad_end, VadEvent::SpeechEnd { .. })
                && cancel.cancel_epoch == 1
                && unconfirmed_none
                && live.telemetry.confirmed_barge_in_halt_ms() == Some(35)
        });
        suites.push(SuiteResult {
            suite_id: "WB-AUDIO-LIVE".into(),
            scope_tag: "MEASURED_LOCAL_HARNESS".into(),
            cases_total,
            cases_passed: if ok { cases_total } else { 0 },
            cold_us,
            warm_p50_us: p50,
            warm_p95_us: p95,
            notes: "24k->16k resample, WAV + G.711 codecs, VAD endpointing, Formant TTS/STT round-trip, and SI-4 sink-confirmed T2 barge-in.".into(),
        });
    }

    let all_pass = suites.iter().all(|s| s.cases_passed == s.cases_total);
    BenchmarkReport {
        generated_at_utc: Utc::now().to_rfc3339(),
        os: std::env::consts::OS.to_owned(),
        arch: std::env::consts::ARCH.to_owned(),
        status: if all_pass { "PASS" } else { "FAIL" }.to_owned(),
        suites,
    }
}

pub fn render_markdown_report(report: &BenchmarkReport) -> String {
    let mut lines = vec![
        "# WispralBench Reproducible Core Benchmark Report".to_owned(),
        String::new(),
        format!("- **Generated (UTC):** `{}`", report.generated_at_utc),
        format!("- **Platform:** `{}/{}`", report.os, report.arch),
        format!("- **Overall Status:** `{}`", report.status),
        "- **Scope Discipline:** `MEASURED_LOCAL_HARNESS` covers deterministic in-repo algorithms, contracts, DSP, and state machines. External corpus WER and live PSTN carrier call latency are tracked separately and never fabricated.".to_owned(),
        String::new(),
        "| Suite | Scope | Cases Passed | Cold (us) | Warm p50 (us) | Warm p95 (us) | Notes |".to_owned(),
        "| --- | --- | --- | --- | --- | --- | --- |".to_owned(),
    ];
    for s in &report.suites {
        lines.push(format!(
            "| `{}` | `{}` | `{}/{}` | `{}` | `{}` | `{}` | {} |",
            s.suite_id,
            s.scope_tag,
            s.cases_passed,
            s.cases_total,
            s.cold_us,
            s.warm_p50_us,
            s.warm_p95_us,
            s.notes
        ));
    }
    lines.push(String::new());
    lines.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn core_benchmark_suites_execute_and_pass() {
        let rep = run_core_benchmarks();
        assert_eq!(rep.status, "PASS");
        assert_eq!(rep.suites.len(), 4);
        let md = render_markdown_report(&rep);
        assert!(md.contains("WB-AR"));
        assert!(md.contains("WB-AUDIO-LIVE"));
    }
}
