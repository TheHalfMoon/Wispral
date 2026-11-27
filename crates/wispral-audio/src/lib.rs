//! Wispral Core deterministic audio capture abstractions, DSP, codecs, VAD, and WAV I/O.
//!
//! Pure-Rust, zero-unsafe, zero-network implementation shared by Wispral CLI/MCP,
//! WisprSide pre-processing, WispralBench acoustic harnesses, and Omalla parity tests.

use std::collections::VecDeque;
use std::f32::consts::PI;

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum AudioError {
    #[error("unsupported sample rate: {0} Hz")]
    UnsupportedSampleRate(u32),
    #[error("WAV payload size {actual} exceeds bound {limit}")]
    WavTooLarge { actual: usize, limit: usize },
    #[error("invalid or unsupported WAV header: {0}")]
    InvalidWav(&'static str),
}

/// Bounded sample ring buffer that never grows past `capacity_samples`.
#[derive(Debug, Clone)]
pub struct AudioRingBuffer {
    buf: VecDeque<f32>,
    capacity: usize,
    dropped_samples: u64,
}

impl AudioRingBuffer {
    pub fn new(capacity_samples: usize) -> Self {
        let cap = capacity_samples.max(1);
        Self {
            buf: VecDeque::with_capacity(cap),
            capacity: cap,
            dropped_samples: 0,
        }
    }

    pub fn push_slice(&mut self, samples: &[f32]) {
        for &s in samples {
            if self.buf.len() == self.capacity {
                self.buf.pop_front();
                self.dropped_samples += 1;
            }
            self.buf.push_back(s.clamp(-1.0, 1.0));
        }
    }

    pub fn pop_frame(&mut self, frame_len: usize) -> Option<Vec<f32>> {
        if self.buf.len() < frame_len {
            return None;
        }
        let mut out = Vec::with_capacity(frame_len);
        for _ in 0..frame_len {
            if let Some(s) = self.buf.pop_front() {
                out.push(s);
            }
        }
        Some(out)
    }

    pub fn len(&self) -> usize {
        self.buf.len()
    }

    pub fn is_empty(&self) -> bool {
        self.buf.is_empty()
    }

    pub fn dropped_samples(&self) -> u64 {
        self.dropped_samples
    }

    pub fn clear(&mut self) {
        self.buf.clear();
    }
}

/// Resamples mono `f32` audio between supported rates (`8000..=48000` Hz) using
/// anti-aliased low-pass prefiltering (when downsampling) + linear/cubic interpolation.
pub fn resample_mono(samples: &[f32], src_hz: u32, dst_hz: u32) -> Result<Vec<f32>, AudioError> {
    if !(8000..=96000).contains(&src_hz) {
        return Err(AudioError::UnsupportedSampleRate(src_hz));
    }
    if !(8000..=96000).contains(&dst_hz) {
        return Err(AudioError::UnsupportedSampleRate(dst_hz));
    }
    if samples.is_empty() || src_hz == dst_hz {
        return Ok(samples.to_vec());
    }

    // Apply single-pole low-pass anti-aliasing filter before downsampling
    let source: Vec<f32> = if dst_hz < src_hz {
        let cutoff = 0.45 * (dst_hz as f32);
        let rc = 1.0 / (2.0 * PI * cutoff);
        let dt = 1.0 / (src_hz as f32);
        let alpha = dt / (rc + dt);
        let mut filtered = Vec::with_capacity(samples.len());
        let mut y = samples[0];
        for &x in samples {
            y += alpha * (x - y);
            filtered.push(y);
        }
        filtered
    } else {
        samples.to_vec()
    };

    let out_len = ((source.len() as u64 * dst_hz as u64) / src_hz as u64).max(1) as usize;
    let ratio = src_hz as f64 / dst_hz as f64;
    let mut out = Vec::with_capacity(out_len);
    for i in 0..out_len {
        let pos = i as f64 * ratio;
        let idx = pos.floor() as usize;
        let frac = (pos - idx as f64) as f32;
        let s0 = source[idx.min(source.len() - 1)];
        let s1 = source[(idx + 1).min(source.len() - 1)];
        out.push(s0 + frac * (s1 - s0));
    }
    Ok(out)
}

/// ITU-T G.711 μ-law (`PCMU`) and A-law (`PCMA`) 8-bit telephony codecs.
pub mod g711 {
    const BIAS: i16 = 0x84;
    const CLIP: i16 = 32635;

    pub fn encode_ulaw_sample(mut pcm: i16) -> u8 {
        let sign = if pcm < 0 {
            pcm = pcm.saturating_neg();
            0x80u8
        } else {
            0x00u8
        };
        if pcm > CLIP {
            pcm = CLIP;
        }
        pcm = pcm.saturating_add(BIAS);
        let mut exponent = 7u8;
        let mut exp_mask = 0x4000i16;
        while exponent > 0 && (pcm & exp_mask) == 0 {
            exponent -= 1;
            exp_mask >>= 1;
        }
        let mantissa = ((pcm >> (exponent + 3)) & 0x0F) as u8;
        !(sign | (exponent << 4) | mantissa)
    }

    pub fn decode_ulaw_sample(ulaw: u8) -> i16 {
        let u = !ulaw;
        let t = (((u & 0x0F) as i16) << 3) + BIAS;
        let mag = (t << ((u & 0x70) >> 4)) - BIAS;
        if (u & 0x80) != 0 {
            -mag
        } else {
            mag
        }
    }

    pub fn encode_alaw_sample(pcm: i16) -> u8 {
        let mut val = pcm;
        let sign = if val >= 0 {
            0xD5u8
        } else {
            val = val.saturating_neg().saturating_sub(1);
            0x55u8
        };
        let (seg, aval) = if val < 256 {
            (0u8, (val >> 4) as u8)
        } else {
            let mut s = 1u8;
            let mut mask = 0x100i16;
            while s < 7 && val >= (mask << 1) {
                s += 1;
                mask <<= 1;
            }
            (s, ((val >> (s + 3)) & 0x0F) as u8)
        };
        ((seg << 4) | aval) ^ sign
    }

    pub fn decode_alaw_sample(alaw: u8) -> i16 {
        let a = alaw ^ 0x55;
        let mut t = ((a & 0x0F) as i16) << 4;
        let seg = (a & 0x70) >> 4;
        match seg {
            0 => t += 8,
            1 => t += 0x108,
            _ => {
                t += 0x108;
                t <<= seg - 1;
            }
        }
        if (a & 0x80) != 0 {
            t
        } else {
            -t
        }
    }
}

/// 2nd-order Butterworth high-pass filter for DC offset and low-frequency rumble removal.
#[derive(Debug, Clone)]
pub struct BiquadHighPass {
    b0: f32,
    b1: f32,
    b2: f32,
    a1: f32,
    a2: f32,
    x1: f32,
    x2: f32,
    y1: f32,
    y2: f32,
}

impl BiquadHighPass {
    pub fn new(sample_rate_hz: u32, cutoff_hz: f32) -> Self {
        let fs = sample_rate_hz.max(8000) as f32;
        let fc = cutoff_hz.clamp(20.0, fs * 0.45);
        let w0 = 2.0 * PI * fc / fs;
        let cos_w0 = w0.cos();
        let alpha = w0.sin() / std::f32::consts::SQRT_2;
        let a0 = 1.0 + alpha;
        let b0 = ((1.0 + cos_w0) * 0.5) / a0;
        let b1 = -(1.0 + cos_w0) / a0;
        let b2 = ((1.0 + cos_w0) * 0.5) / a0;
        let a1 = (-2.0 * cos_w0) / a0;
        let a2 = (1.0 - alpha) / a0;
        Self {
            b0,
            b1,
            b2,
            a1,
            a2,
            x1: 0.0,
            x2: 0.0,
            y1: 0.0,
            y2: 0.0,
        }
    }

    pub fn process_in_place(&mut self, samples: &mut [f32]) {
        for x in samples {
            let y = self.b0 * *x + self.b1 * self.x1 + self.b2 * self.x2
                - self.a1 * self.y1
                - self.a2 * self.y2;
            self.x2 = self.x1;
            self.x1 = *x;
            self.y2 = self.y1;
            self.y1 = y;
            *x = y.clamp(-1.0, 1.0);
        }
    }
}

/// Normalizes audio RMS toward `target_rms` (e.g. `0.12` ~ `-18 dBFS`) while hard-limiting peak to `0.95`.
pub fn normalize_loudness(samples: &mut [f32], target_rms: f32) {
    if samples.is_empty() {
        return;
    }
    let sum_sq: f64 = samples.iter().map(|&s| (s as f64) * (s as f64)).sum();
    let rms = (sum_sq / samples.len() as f64).sqrt() as f32;
    if rms < 1e-5 {
        return;
    }
    let peak = samples.iter().fold(0.0f32, |acc, &s| acc.max(s.abs()));
    let desired_gain = (target_rms / rms).clamp(0.1, 8.0);
    let safe_gain = if peak * desired_gain > 0.95 {
        0.95 / peak
    } else {
        desired_gain
    };
    for s in samples {
        *s = (*s * safe_gain).clamp(-1.0, 1.0);
    }
}

/// Smooth gain ducking envelope used during duplex barge-in before hard playback halt.
#[derive(Debug, Clone)]
pub struct DuckingEnvelope {
    current_gain: f32,
    ducked_gain: f32,
    attack_coeff: f32,
    release_coeff: f32,
}

impl DuckingEnvelope {
    pub fn new(ducked_gain: f32) -> Self {
        Self {
            current_gain: 1.0,
            ducked_gain: ducked_gain.clamp(0.0, 1.0),
            attack_coeff: 0.35,
            release_coeff: 0.08,
        }
    }

    pub fn apply_frame(&mut self, outbound_samples: &mut [f32], user_speaking: bool) {
        let target = if user_speaking { self.ducked_gain } else { 1.0 };
        let coeff = if user_speaking {
            self.attack_coeff
        } else {
            self.release_coeff
        };
        for s in outbound_samples {
            self.current_gain += coeff * (target - self.current_gain);
            *s *= self.current_gain;
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum VadEvent {
    Silence,
    SpeechStart,
    SpeechContinue,
    SpeechEnd { speech_ms: u64, silence_ms: u64 },
}

/// Deterministic frame-based Voice Activity & Endpointing Detector.
#[derive(Debug, Clone)]
pub struct EndpointDetector {
    rms_threshold: f32,
    min_speech_ms: u64,
    endpoint_silence_ms: u64,
    in_speech: bool,
    accum_speech_ms: u64,
    accum_silence_ms: u64,
}

impl EndpointDetector {
    pub fn new(rms_threshold: f32, min_speech_ms: u64, endpoint_silence_ms: u64) -> Self {
        Self {
            rms_threshold: rms_threshold.max(0.001),
            min_speech_ms,
            endpoint_silence_ms,
            in_speech: false,
            accum_speech_ms: 0,
            accum_silence_ms: 0,
        }
    }

    pub fn process_frame(&mut self, samples: &[f32], frame_ms: u64) -> VadEvent {
        let rms = if samples.is_empty() {
            0.0
        } else {
            let sum: f64 = samples.iter().map(|&s| (s as f64) * (s as f64)).sum();
            (sum / samples.len() as f64).sqrt() as f32
        };
        let active = rms >= self.rms_threshold;

        if active {
            self.accum_silence_ms = 0;
            self.accum_speech_ms += frame_ms;
            if !self.in_speech && self.accum_speech_ms >= self.min_speech_ms {
                self.in_speech = true;
                return VadEvent::SpeechStart;
            }
            if self.in_speech {
                return VadEvent::SpeechContinue;
            }
            VadEvent::Silence
        } else if self.in_speech {
            self.accum_silence_ms += frame_ms;
            if self.accum_silence_ms >= self.endpoint_silence_ms {
                let ev = VadEvent::SpeechEnd {
                    speech_ms: self.accum_speech_ms,
                    silence_ms: self.accum_silence_ms,
                };
                self.in_speech = false;
                self.accum_speech_ms = 0;
                self.accum_silence_ms = 0;
                ev
            } else {
                VadEvent::SpeechContinue
            }
        } else {
            self.accum_speech_ms = 0;
            VadEvent::Silence
        }
    }
}

/// Encodes mono `f32` samples (`-1.0..=1.0`) as standard 16-bit PCM RIFF/WAVE bytes.
pub fn encode_wav_pcm16_mono(samples: &[f32], sample_rate_hz: u32) -> Vec<u8> {
    let data_bytes = (samples.len() * 2) as u32;
    let riff_size = 36u32.saturating_add(data_bytes);
    let byte_rate = sample_rate_hz.saturating_mul(2);
    let mut out = Vec::with_capacity(44 + data_bytes as usize);
    out.extend_from_slice(b"RIFF");
    out.extend_from_slice(&riff_size.to_le_bytes());
    out.extend_from_slice(b"WAVEfmt ");
    out.extend_from_slice(&16u32.to_le_bytes());
    out.extend_from_slice(&1u16.to_le_bytes()); // PCM = 1
    out.extend_from_slice(&1u16.to_le_bytes()); // mono = 1
    out.extend_from_slice(&sample_rate_hz.to_le_bytes());
    out.extend_from_slice(&byte_rate.to_le_bytes());
    out.extend_from_slice(&2u16.to_le_bytes()); // block align
    out.extend_from_slice(&16u16.to_le_bytes()); // bits per sample
    out.extend_from_slice(b"data");
    out.extend_from_slice(&data_bytes.to_le_bytes());
    for &s in samples {
        let q = (s.clamp(-1.0, 1.0) * 32767.0).round() as i16;
        out.extend_from_slice(&q.to_le_bytes());
    }
    out
}

/// Parses bounded 16-bit PCM RIFF/WAVE bytes into `(mono_f32_samples, sample_rate_hz)`.
/// Stereo/multi-channel inputs are downmixed deterministically to mono.
pub fn decode_wav_pcm16_bounded(
    bytes: &[u8],
    max_bytes: usize,
) -> Result<(Vec<f32>, u32), AudioError> {
    if bytes.len() > max_bytes {
        return Err(AudioError::WavTooLarge {
            actual: bytes.len(),
            limit: max_bytes,
        });
    }
    if bytes.len() < 44 || &bytes[0..4] != b"RIFF" || &bytes[8..12] != b"WAVE" {
        return Err(AudioError::InvalidWav("missing RIFF/WAVE header"));
    }
    let mut offset = 12usize;
    let mut channels = 0u16;
    let mut sample_rate = 0u32;
    let mut bits_per_sample = 0u16;
    let mut data_slice: Option<&[u8]> = None;

    while offset + 8 <= bytes.len() {
        let chunk_id = &bytes[offset..offset + 4];
        let chunk_len = u32::from_le_bytes([
            bytes[offset + 4],
            bytes[offset + 5],
            bytes[offset + 6],
            bytes[offset + 7],
        ]) as usize;
        offset += 8;
        if offset + chunk_len > bytes.len() {
            return Err(AudioError::InvalidWav("truncated WAV chunk"));
        }
        if chunk_id == b"fmt " {
            if chunk_len < 16 {
                return Err(AudioError::InvalidWav("short fmt chunk"));
            }
            let fmt_tag = u16::from_le_bytes([bytes[offset], bytes[offset + 1]]);
            if fmt_tag != 1 {
                return Err(AudioError::InvalidWav("only PCM format tag 1 supported"));
            }
            channels = u16::from_le_bytes([bytes[offset + 2], bytes[offset + 3]]);
            sample_rate = u32::from_le_bytes([
                bytes[offset + 4],
                bytes[offset + 5],
                bytes[offset + 6],
                bytes[offset + 7],
            ]);
            bits_per_sample = u16::from_le_bytes([bytes[offset + 14], bytes[offset + 15]]);
        } else if chunk_id == b"data" {
            data_slice = Some(&bytes[offset..offset + chunk_len]);
            break;
        }
        offset += chunk_len + (chunk_len % 2);
    }

    if channels == 0 || bits_per_sample != 16 || !(8000..=96000).contains(&sample_rate) {
        return Err(AudioError::InvalidWav(
            "unsupported channels, bit depth, or rate",
        ));
    }
    let raw = data_slice.ok_or(AudioError::InvalidWav("missing data chunk"))?;
    let frame_bytes = (channels as usize) * 2;
    let frames = raw.len() / frame_bytes;
    let mut mono = Vec::with_capacity(frames);
    for f in 0..frames {
        let base = f * frame_bytes;
        let mut sum = 0.0f32;
        for ch in 0..(channels as usize) {
            let idx = base + ch * 2;
            let v = i16::from_le_bytes([raw[idx], raw[idx + 1]]) as f32 / 32768.0;
            sum += v;
        }
        mono.push((sum / channels as f32).clamp(-1.0, 1.0));
    }
    Ok((mono, sample_rate))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ring_buffer_g711_resampler_vad_and_wav_round_trip() {
        // 1. Ring buffer bounds
        let mut rb = AudioRingBuffer::new(4);
        rb.push_slice(&[0.1, 0.2, 0.3, 0.4, 0.5]);
        assert_eq!(rb.dropped_samples(), 1);
        assert_eq!(rb.pop_frame(4).unwrap(), vec![0.2, 0.3, 0.4, 0.5]);

        // 2. G.711 u-law & A-law monotonic round-trip accuracy
        for sample in [-24000i16, -4000, -200, 0, 200, 4000, 24000] {
            let u = g711::decode_ulaw_sample(g711::encode_ulaw_sample(sample));
            let a = g711::decode_alaw_sample(g711::encode_alaw_sample(sample));
            assert!((u - sample).abs() <= (sample.abs() / 12 + 32));
            assert!((a - sample).abs() <= (sample.abs() / 12 + 32));
        }

        // 3. Resample 48 kHz -> 16 kHz -> WAV -> decode
        let sine_48k: Vec<f32> = (0..4800)
            .map(|n| (2.0 * PI * 440.0 * (n as f32) / 48000.0).sin() * 0.5)
            .collect();
        let down_16k = resample_mono(&sine_48k, 48000, 16000).unwrap();
        assert_eq!(down_16k.len(), 1600);
        let wav = encode_wav_pcm16_mono(&down_16k, 16000);
        let (decoded, sr) = decode_wav_pcm16_bounded(&wav, 64 * 1024).unwrap();
        assert_eq!(sr, 16000);
        assert_eq!(decoded.len(), 1600);

        // 4. Endpoint detector transitions SpeechStart -> SpeechEnd
        let mut vad = EndpointDetector::new(0.05, 40, 60);
        let loud = vec![0.25f32; 320];
        let quiet = vec![0.0f32; 320];
        assert_eq!(vad.process_frame(&loud, 20), VadEvent::Silence);
        assert_eq!(vad.process_frame(&loud, 20), VadEvent::SpeechStart);
        assert_eq!(vad.process_frame(&loud, 20), VadEvent::SpeechContinue);
        assert_eq!(vad.process_frame(&quiet, 20), VadEvent::SpeechContinue);
        assert_eq!(vad.process_frame(&quiet, 20), VadEvent::SpeechContinue);
        assert_eq!(
            vad.process_frame(&quiet, 20),
            VadEvent::SpeechEnd {
                speech_ms: 60,
                silence_ms: 60
            }
        );
    }
}
