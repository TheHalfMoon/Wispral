# SPDX-License-Identifier: Apache-2.0
"""Klaint Verified Analytics Engine (`klaint.analytics`).

Computes verified First-Contact Resolution (FCR), recontact rate, policy compliance rate,
escalation rate, turn latency (`p50`/`p95`), and per-language (`en`, `ar-MSA`, `ar-Gulf`, `ar-EG`,
`ar-Levantine`, `ar-en-codeswitch`) metrics strictly from ledger and conversation records.
Zero fabricated or estimated CSAT numbers are ever emitted.
"""

from __future__ import annotations

import math
from typing import Any

from klaint.core.models import validate_tenant_id
from klaint.storage.tenant_db import TenantStorageRegistry

SUPPORTED_VARIETIES: tuple[str, ...] = (
    "en",
    "ar-MSA",
    "ar-Gulf",
    "ar-EG",
    "ar-Levantine",
    "ar-en-codeswitch",
)


def _percentile(sorted_values: list[int], pct: float) -> int:
    if not sorted_values:
        return 0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = max(0, min(len(sorted_values) - 1, math.ceil((pct / 100.0) * len(sorted_values)) - 1))
    return int(sorted_values[rank])


class AnalyticsEngine:
    """Computes evidence-backed operational metrics per tenant with zero fabricated CSAT."""

    def __init__(self, storage: TenantStorageRegistry) -> None:
        self.storage = storage

    def compute_overview(self, tenant_id: str) -> dict[str, Any]:
        slug = validate_tenant_id(tenant_id)
        db = self.storage.for_tenant(slug)

        with db.read_connection() as conn:
            convs = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM conversations WHERE tenant_id = ? ORDER BY created_at ASC",
                    (slug,),
                ).fetchall()
            ]
            turns = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM conversation_turns WHERE tenant_id = ? ORDER BY created_at ASC",
                    (slug,),
                ).fetchall()
            ]
            ledger_rows = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM action_ledger WHERE tenant_id = ? ORDER BY created_at ASC",
                    (slug,),
                ).fetchall()
            ]

        total_convs = len(convs)
        recontact_targets = {str(c["recontact_of"]) for c in convs if c.get("recontact_of")}

        fcr_count = 0
        recontact_count = 0
        escalated_count = 0

        conv_primary_lang: dict[str, str] = {}
        turns_by_conv: dict[str, list[dict[str, Any]]] = {}
        for t in turns:
            cid = str(t["conversation_id"])
            turns_by_conv.setdefault(cid, []).append(t)
            if cid not in conv_primary_lang:
                conv_primary_lang[cid] = str(t["language_variety"])

        for conv in convs:
            cid = str(conv["conversation_id"])
            is_recontact = bool(conv.get("recontact_of"))
            had_followup_recontact = cid in recontact_targets
            is_escalated = str(conv["status"]) in ("escalated", "awaiting_approval") or str(conv["owner_kind"]) == "human_owned"

            if is_recontact or had_followup_recontact:
                recontact_count += 1
            if is_escalated:
                escalated_count += 1
            if (
                str(conv["status"]) == "resolved"
                and str(conv["owner_kind"]) == "ai_owned"
                and not is_recontact
                and not had_followup_recontact
            ):
                fcr_count += 1

        latencies = sorted(int(t["latency_ms"]) for t in turns)
        gate_interceptions = sum(1 for t in turns if int(t["gate_blocked"]) != 0)

        # Policy compliance: every settled/reconciled ledger mutation has a non-empty verdict_id AND
        # every delivered turn passed the Commitment Output Gate (unbacked drafts were intercepted).
        compliant_ledger = sum(
            1
            for row in ledger_rows
            if str(row["verdict_id"]).startswith("vrd-") and str(row["capability_json"]).strip() != ""
        )
        total_evaluated_units = len(turns) + len(ledger_rows)
        compliant_units = (len(turns) - gate_interceptions) + compliant_ledger
        policy_compliance_rate = (
            round(compliant_units / total_evaluated_units, 4) if total_evaluated_units > 0 else 1.0
        )

        # Per-language breakdown
        by_language: dict[str, dict[str, Any]] = {}
        observed_langs = list(dict.fromkeys([*SUPPORTED_VARIETIES, *(str(t["language_variety"]) for t in turns)]))
        for lang in observed_langs:
            lang_turns = [t for t in turns if str(t["language_variety"]) == lang]
            lang_convs = [
                c
                for c in convs
                if conv_primary_lang.get(str(c["conversation_id"]), str(c["language"])) == lang
            ]
            lang_lat = sorted(int(t["latency_ms"]) for t in lang_turns)
            lang_fcr = sum(
                1
                for c in lang_convs
                if str(c["status"]) == "resolved"
                and str(c["owner_kind"]) == "ai_owned"
                and not c.get("recontact_of")
                and str(c["conversation_id"]) not in recontact_targets
            )
            lang_esc = sum(
                1
                for c in lang_convs
                if str(c["status"]) in ("escalated", "awaiting_approval") or str(c["owner_kind"]) == "human_owned"
            )
            by_language[lang] = {
                "conversations": len(lang_convs),
                "turns": len(lang_turns),
                "fcr_rate": round(lang_fcr / len(lang_convs), 4) if lang_convs else 0.0,
                "escalation_rate": round(lang_esc / len(lang_convs), 4) if lang_convs else 0.0,
                "latency_ms_p50": _percentile(lang_lat, 50),
                "latency_ms_p95": _percentile(lang_lat, 95),
            }

        settled_count = sum(1 for r in ledger_rows if str(r["state"]) == "settled")
        reconciled_count = sum(1 for r in ledger_rows if str(r["state"]) == "reconciled")

        return {
            "tenant_id": slug,
            "total_conversations": total_convs,
            "total_turns": len(turns),
            "fcr_count": fcr_count,
            "fcr_rate": round(fcr_count / total_convs, 4) if total_convs > 0 else 0.0,
            "recontact_rate": round(recontact_count / total_convs, 4) if total_convs > 0 else 0.0,
            "escalation_rate": round(escalated_count / total_convs, 4) if total_convs > 0 else 0.0,
            "policy_compliance_rate": policy_compliance_rate,
            "commitment_gate_interceptions": gate_interceptions,
            "ledger_actions": {
                "total": len(ledger_rows),
                "settled": settled_count,
                "reconciled": reconciled_count,
            },
            "latency_ms": {
                "p50": _percentile(latencies, 50),
                "p95": _percentile(latencies, 95),
            },
            "by_language": by_language,
            # Strictly null unless real customer survey records exist — never fabricated!
            "csat_score": None,
            "csat_basis": "unmeasured_no_fabricated_csat",
        }
