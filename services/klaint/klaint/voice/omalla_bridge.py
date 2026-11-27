# SPDX-License-Identifier: Apache-2.0
"""Klaint Voice Adapter (`klaint.voice.omalla_bridge`).

- Standalone text mode (`mode="standalone_text"`) operates with zero Omalla runtime dependency.
- Voice mode (`mode="omalla_voice"`) connects to Omalla / Wispral Core transcript streams & TTS sinks,
  holding tentative (`is_final=False`) frames as non-authoritative captions (Principle II), routing
  every spoken TTS clause through `CommitmentOutputGate`, and enforcing real-time `ownership_epoch`
  human takeover and barge-in cancellation (Principle III).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from klaint.conversation.gate import CommitmentOutputGate, split_into_clauses
from klaint.core.errors import StaleEpochError
from klaint.core.models import AuthenticatedSession
from klaint.resolution.engine import ResolutionEngine, ResolutionTurnResult


@dataclass(frozen=True)
class OmallaTranscriptFrame:
    utterance_id: str
    text: str
    is_final: bool
    language: str = "en"
    confidence: float = 0.95


@dataclass
class VoiceTurnDelivery:
    mode: Literal["standalone_text", "omalla_voice"]
    status: Literal["caption_buffered", "delivered", "partial_interrupted", "blocked_by_gate", "refused_stale_epoch"]
    spoken_clauses: list[str] = field(default_factory=list)
    discarded_clauses: list[str] = field(default_factory=list)
    receipt_ids: list[str] = field(default_factory=list)
    resolution: ResolutionTurnResult | None = None
    gate_blocked_claims: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "status": self.status,
            "spoken_clauses": list(self.spoken_clauses),
            "discarded_clauses": list(self.discarded_clauses),
            "receipt_ids": list(self.receipt_ids),
            "gate_blocked_claims": list(self.gate_blocked_claims),
            "turn_id": self.resolution.turn_id if self.resolution else None,
        }


class KlaintVoiceBridge:
    """Bridges Klaint resolution and CommitmentOutputGate to standalone text or Omalla real-time voice."""

    def __init__(
        self,
        *,
        resolution_engine: ResolutionEngine,
        mode: Literal["standalone_text", "omalla_voice"] = "standalone_text",
        tts_sink: Callable[[str, AuthenticatedSession], None] | None = None,
    ) -> None:
        self.engine = resolution_engine
        self.mode = mode
        self._tts_sink = tts_sink
        self._tentative_captions: dict[str, str] = {}
        self._barge_in_sessions: set[str] = set()

    def trigger_barge_in(self, session_id: str) -> None:
        """Signal immediate customer barge-in interrupting spoken TTS clause delivery."""
        self._barge_in_sessions.add(session_id)

    def clear_barge_in(self, session_id: str) -> None:
        self._barge_in_sessions.discard(session_id)

    def handle_text_turn(
        self,
        *,
        session: AuthenticatedSession,
        customer_text: str,
        draft_override: str | None = None,
    ) -> VoiceTurnDelivery:
        """Standalone zero-Omalla text turn gated by CommitmentOutputGate and ownership_epoch."""
        try:
            turn_res = self.engine.resolve_turn(
                session=session,
                customer_text=customer_text,
                draft_override=draft_override,
            )
        except StaleEpochError:
            return VoiceTurnDelivery(mode="standalone_text", status="refused_stale_epoch")

        verify_stage = turn_res.stages[6]
        blocked = list(verify_stage.details.get("blocked_claims", []))
        return VoiceTurnDelivery(
            mode="standalone_text",
            status="blocked_by_gate" if blocked else "delivered",
            spoken_clauses=[turn_res.assistant_text],
            receipt_ids=list(turn_res.receipt_ids),
            resolution=turn_res,
            gate_blocked_claims=blocked,
        )

    def handle_omalla_frame(
        self,
        *,
        session: AuthenticatedSession,
        frame: OmallaTranscriptFrame,
        draft_override: str | None = None,
        inter_clause_hook: Callable[[int], None] | None = None,
    ) -> VoiceTurnDelivery:
        """Process an Omalla STT frame; only `is_final=True` frames carry action authority (Principle II)."""
        if not frame.is_final:
            self._tentative_captions[session.session_id] = frame.text
            return VoiceTurnDelivery(mode="omalla_voice", status="caption_buffered")

        self._tentative_captions.pop(session.session_id, None)
        self._barge_in_sessions.discard(session.session_id)

        try:
            turn_res = self.engine.resolve_turn(
                session=session,
                customer_text=frame.text,
                draft_override=draft_override,
            )
        except StaleEpochError:
            return VoiceTurnDelivery(mode="omalla_voice", status="refused_stale_epoch")

        verify_details = turn_res.stages[6].details
        initial_blocked = list(verify_details.get("blocked_claims", []))
        if initial_blocked:
            # Render only the safe replacement through TTS sink after epoch check
            if self._is_epoch_or_barge_interrupted(session):
                return VoiceTurnDelivery(
                    mode="omalla_voice",
                    status="refused_stale_epoch",
                    discarded_clauses=[turn_res.assistant_text],
                    resolution=turn_res,
                    gate_blocked_claims=initial_blocked,
                )
            if self._tts_sink is not None:
                self._tts_sink(turn_res.assistant_text, session)
            return VoiceTurnDelivery(
                mode="omalla_voice",
                status="blocked_by_gate",
                spoken_clauses=[turn_res.assistant_text],
                resolution=turn_res,
                gate_blocked_claims=initial_blocked,
            )

        # Clause-by-clause gated TTS streaming with real-time barge-in and ownership_epoch takeover check!
        db = self.engine.storage.for_tenant(session.tenant_id)
        gate = CommitmentOutputGate(db)
        raw_clauses = split_into_clauses(turn_res.assistant_text)
        spoken: list[str] = []
        discarded: list[str] = []

        for idx, clause in enumerate(raw_clauses):
            if inter_clause_hook is not None:
                inter_clause_hook(idx)

            if self._is_epoch_or_barge_interrupted(session):
                discarded.extend(raw_clauses[idx:])
                return VoiceTurnDelivery(
                    mode="omalla_voice",
                    status="partial_interrupted" if spoken else "refused_stale_epoch",
                    spoken_clauses=spoken,
                    discarded_clauses=discarded,
                    receipt_ids=list(turn_res.receipt_ids),
                    resolution=turn_res,
                )

            clause_gate = gate.evaluate(session=session, draft_text=clause, mode="BLOCK")
            if not clause_gate.allowed:
                discarded.extend(raw_clauses[idx:])
                if self._tts_sink is not None:
                    self._tts_sink(clause_gate.output_text, session)
                spoken.append(clause_gate.output_text)
                return VoiceTurnDelivery(
                    mode="omalla_voice",
                    status="blocked_by_gate",
                    spoken_clauses=spoken,
                    discarded_clauses=discarded,
                    resolution=turn_res,
                    gate_blocked_claims=clause_gate.blocked_claims,
                )

            if self._tts_sink is not None:
                self._tts_sink(clause, session)
            spoken.append(clause)

        return VoiceTurnDelivery(
            mode="omalla_voice",
            status="delivered",
            spoken_clauses=spoken,
            receipt_ids=list(turn_res.receipt_ids),
            resolution=turn_res,
        )

    def _is_epoch_or_barge_interrupted(self, session: AuthenticatedSession) -> bool:
        if session.session_id in self._barge_in_sessions:
            return True
        db = self.engine.storage.for_tenant(session.tenant_id)
        with db.read_connection() as conn:
            row = conn.execute(
                "SELECT ownership_epoch, owner_kind FROM conversations WHERE tenant_id = ? AND session_id = ?",
                (session.tenant_id, session.session_id),
            ).fetchone()
        if row is None:
            return False
        return int(row["ownership_epoch"]) != session.ownership_epoch or str(row["owner_kind"]) == "human_owned"
