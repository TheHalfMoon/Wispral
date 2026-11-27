//! Wispral Live: pure full-duplex turn-taking, barge-in, `T0..T6` latency telemetry,
//! and 4-level cancellation state machine.
//!
//! Socket-free by design (`WISPRAL_ECOSYSTEM_ARCHITECTURE_V2.md`): exports deterministic
//! state transitions and golden JSON vectors consumed by Omalla Realtime, Klaint Voice,
//! and WisprSide Live mode.
//!
//! Security & Reliability Invariant `SI-4`:
//! - `T2` (`t2_observed_audio_halt_ms`) is stamped ONLY when the playback sink confirms
//!   queue flush (`confirm_sink_halted`). If a remote PSTN trunk cannot confirm playout
//!   halt, the cancellation record stays `StoppedUnconfirmed` (`lease_released = false`).
//! - Barge-in increments `turn_epoch` atomically; any late TTS or token chunk carrying an
//!   older `turn_epoch` is deterministically rejected (`accept_outbound_chunk == false`).

use serde::{Deserialize, Serialize};
use wispral_contracts::CancellationState;
use wispral_journal::IntentState;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DuplexTurnState {
    Idle,
    UserSpeaking,
    Thinking,
    AgentSpeaking,
    BargeInStopping,
    HumanTakeover,
}

/// Four-layer cancellation status on user barge-in or operator takeover.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FourLevelCancellation {
    pub from_epoch: u64,
    pub cancel_epoch: u64,
    /// Layer 1: Audio output playback sink (`requested -> observed_stopped | stopped_unconfirmed`).
    pub playback_sink_state: CancellationState,
    /// Layer 2: TTS synthesis worker stream aborted.
    pub synthesis_aborted: bool,
    /// Layer 3: LLM / agent reasoning stream aborted.
    pub reasoning_aborted: bool,
    /// Layer 4: External tool effect state (`none`, `settled`, or `unknown` requiring reconcile).
    pub tool_effect_state: Option<IntentState>,
    pub reconcile_intent_id: Option<String>,
}

/// Seven audio-boundary timestamps (`T0..T6`) in monotonic milliseconds.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct TurnLatencyTelemetry {
    /// `T0`: User speech endpoint detected.
    pub t0_speech_end_ms: Option<u64>,
    /// `T1`: Barge-in speech onset detected while agent was speaking/thinking.
    pub t1_barge_in_onset_ms: Option<u64>,
    /// `T2`: Sink-confirmed outbound audio halt (`None` if unconfirmed!).
    pub t2_observed_audio_halt_ms: Option<u64>,
    /// `T3`: First partial STT hypothesis emitted.
    pub t3_partial_stt_ms: Option<u64>,
    /// `T4`: Final endpointed STT transcript emitted.
    pub t4_final_stt_ms: Option<u64>,
    /// `T5`: First LLM/policy/tool response token emitted.
    pub t5_first_token_ms: Option<u64>,
    /// `T6`: First outbound TTS audio frame enqueued to playback sink.
    pub t6_first_tts_frame_ms: Option<u64>,
}

impl TurnLatencyTelemetry {
    /// End-to-end voice-to-voice turn latency (`T6 - T0`), when both boundaries are recorded.
    pub fn voice_to_voice_ms(&self) -> Option<u64> {
        match (self.t0_speech_end_ms, self.t6_first_tts_frame_ms) {
            (Some(t0), Some(t6)) if t6 >= t0 => Some(t6 - t0),
            _ => None,
        }
    }

    /// Sink-confirmed barge-in stop latency (`T2 - T1`), never fabricated from `T1` alone.
    pub fn confirmed_barge_in_halt_ms(&self) -> Option<u64> {
        match (self.t1_barge_in_onset_ms, self.t2_observed_audio_halt_ms) {
            (Some(t1), Some(t2)) if t2 >= t1 => Some(t2 - t1),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DuplexSessionMachine {
    pub session_id: String,
    pub turn_epoch: u64,
    pub state: DuplexTurnState,
    pub telemetry: TurnLatencyTelemetry,
    pub last_cancellation: Option<FourLevelCancellation>,
}

impl DuplexSessionMachine {
    pub fn new(session_id: impl Into<String>) -> Self {
        Self {
            session_id: session_id.into(),
            turn_epoch: 0,
            state: DuplexTurnState::Idle,
            telemetry: TurnLatencyTelemetry::default(),
            last_cancellation: None,
        }
    }

    /// Checks whether an outbound TTS frame or model token tagged with `chunk_epoch`
    /// is still allowed to play/emit.
    pub fn accept_outbound_chunk(&self, chunk_epoch: u64) -> bool {
        chunk_epoch == self.turn_epoch
            && matches!(
                self.state,
                DuplexTurnState::Thinking | DuplexTurnState::AgentSpeaking
            )
    }

    pub fn on_user_speech_start(
        &mut self,
        now_ms: u64,
        in_flight_tool: Option<(IntentState, Option<String>)>,
    ) -> Option<FourLevelCancellation> {
        if self.state == DuplexTurnState::HumanTakeover {
            return None;
        }
        if matches!(
            self.state,
            DuplexTurnState::AgentSpeaking | DuplexTurnState::Thinking
        ) {
            // Barge-in! Advance turn_epoch immediately and trigger 4-level cancellation.
            let prev_epoch = self.turn_epoch;
            self.turn_epoch += 1;
            self.telemetry.t1_barge_in_onset_ms = Some(now_ms);
            self.telemetry.t2_observed_audio_halt_ms = None;

            let (eff_state, rec_id) = match in_flight_tool {
                Some((IntentState::Dispatched, r)) => (Some(IntentState::Unknown), r),
                Some((st, r)) => (Some(st), r),
                None => (None, None),
            };

            let cancel = FourLevelCancellation {
                from_epoch: prev_epoch,
                cancel_epoch: self.turn_epoch,
                playback_sink_state: if self.state == DuplexTurnState::AgentSpeaking {
                    CancellationState::Requested
                } else {
                    CancellationState::ObservedStopped
                },
                synthesis_aborted: true,
                reasoning_aborted: true,
                tool_effect_state: eff_state,
                reconcile_intent_id: rec_id,
            };
            self.state = if cancel.playback_sink_state == CancellationState::Requested {
                DuplexTurnState::BargeInStopping
            } else {
                DuplexTurnState::UserSpeaking
            };
            self.last_cancellation = Some(cancel.clone());
            return Some(cancel);
        }
        self.state = DuplexTurnState::UserSpeaking;
        None
    }

    /// Sink confirms outbound audio buffer flush (`SI-4`). Only this stamps `T2`.
    pub fn confirm_sink_halted(&mut self, now_ms: u64, sink_confirmed: bool) {
        if let Some(cancel) = &mut self.last_cancellation {
            if sink_confirmed {
                cancel.playback_sink_state = CancellationState::ObservedStopped;
                self.telemetry.t2_observed_audio_halt_ms = Some(now_ms);
            } else {
                cancel.playback_sink_state = CancellationState::StoppedUnconfirmed;
                self.telemetry.t2_observed_audio_halt_ms = None;
            }
        }
        if self.state == DuplexTurnState::BargeInStopping {
            self.state = DuplexTurnState::UserSpeaking;
        }
    }

    pub fn on_partial_stt(&mut self, now_ms: u64) {
        if self.telemetry.t3_partial_stt_ms.is_none() {
            self.telemetry.t3_partial_stt_ms = Some(now_ms);
        }
    }

    pub fn on_user_speech_end_and_final_stt(&mut self, speech_end_ms: u64, final_stt_ms: u64) {
        if self.state != DuplexTurnState::HumanTakeover {
            self.telemetry.t0_speech_end_ms = Some(speech_end_ms);
            self.telemetry.t4_final_stt_ms = Some(final_stt_ms);
            self.telemetry.t5_first_token_ms = None;
            self.telemetry.t6_first_tts_frame_ms = None;
            self.state = DuplexTurnState::Thinking;
        }
    }

    pub fn on_first_model_token(&mut self, epoch: u64, now_ms: u64) -> bool {
        if !self.accept_outbound_chunk(epoch) {
            return false;
        }
        if self.telemetry.t5_first_token_ms.is_none() {
            self.telemetry.t5_first_token_ms = Some(now_ms);
        }
        true
    }

    pub fn on_first_tts_audio_frame(&mut self, epoch: u64, now_ms: u64) -> bool {
        if !self.accept_outbound_chunk(epoch) {
            return false;
        }
        self.state = DuplexTurnState::AgentSpeaking;
        if self.telemetry.t6_first_tts_frame_ms.is_none() {
            self.telemetry.t6_first_tts_frame_ms = Some(now_ms);
        }
        true
    }

    pub fn on_human_takeover(&mut self) -> u64 {
        self.turn_epoch += 1;
        self.state = DuplexTurnState::HumanTakeover;
        self.turn_epoch
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn barge_in_advances_epoch_drops_stale_chunks_and_requires_sink_ack_for_t2() {
        let mut sm = DuplexSessionMachine::new("ses-live-01");
        assert_eq!(sm.on_user_speech_start(100, None), None);
        sm.on_partial_stt(180);
        sm.on_user_speech_end_and_final_stt(500, 560);
        assert_eq!(sm.state, DuplexTurnState::Thinking);

        let ep0 = sm.turn_epoch;
        assert!(sm.on_first_model_token(ep0, 640));
        assert!(sm.on_first_tts_audio_frame(ep0, 710));
        assert_eq!(sm.telemetry.voice_to_voice_ms(), Some(210));
        assert_eq!(sm.state, DuplexTurnState::AgentSpeaking);

        // User barges in at 900 ms while a dispatched tool call is in flight!
        let cancel = sm
            .on_user_speech_start(
                900,
                Some((IntentState::Dispatched, Some("int-reconcile-1".into()))),
            )
            .expect("must emit 4-level cancellation");
        assert_eq!(cancel.from_epoch, 0);
        assert_eq!(cancel.cancel_epoch, 1);
        assert_eq!(cancel.playback_sink_state, CancellationState::Requested);
        assert_eq!(cancel.tool_effect_state, Some(IntentState::Unknown));
        assert_eq!(
            cancel.reconcile_intent_id.as_deref(),
            Some("int-reconcile-1")
        );

        // Stale TTS chunk from epoch 0 MUST be rejected!
        assert!(!sm.accept_outbound_chunk(ep0));
        // Before sink ACK, T2 must be None!
        assert_eq!(sm.telemetry.confirmed_barge_in_halt_ms(), None);

        // Sink confirms buffer flush at 945 ms -> T2 = 945 ms (45 ms halt)!
        sm.confirm_sink_halted(945, true);
        assert_eq!(sm.telemetry.confirmed_barge_in_halt_ms(), Some(45));
        assert_eq!(sm.state, DuplexTurnState::UserSpeaking);
    }

    #[test]
    fn unconfirmed_pstn_trunk_halt_never_fabricates_t2() {
        let mut sm = DuplexSessionMachine::new("ses-pstn-01");
        sm.on_user_speech_end_and_final_stt(100, 150);
        let ep = sm.turn_epoch;
        sm.on_first_tts_audio_frame(ep, 220);
        sm.on_user_speech_start(400, None);
        sm.confirm_sink_halted(480, false);
        assert_eq!(
            sm.last_cancellation.as_ref().unwrap().playback_sink_state,
            CancellationState::StoppedUnconfirmed
        );
        assert_eq!(sm.telemetry.t2_observed_audio_halt_ms, None);
    }
}
