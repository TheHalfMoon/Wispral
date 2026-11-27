# SPDX-License-Identifier: Apache-2.0
"""KL-2 Integration, Studio SPA, Ownership Epoch Race, Chatwoot Standard Webhooks,
tau2 DB-Hash Simulation, Verified Analytics, CLI Doctor, and Omalla Voice Bridge Tests.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterator

import pytest

from klaint.cli import main as cli_main
from klaint.cli import run_doctor
from klaint.connectors.business import BusinessConnectorSuite
from klaint.inbox.chatwoot_bridge import sign_standard_webhook
from klaint.server.app import KlaintApplication, start_background_server
from klaint.simulation.suite import KlaintSimulationRunner
from klaint.voice.omalla_bridge import KlaintVoiceBridge, OmallaTranscriptFrame

WEBHOOK_SECRET = "whsec_QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo="


@pytest.fixture()
def live_klaint_server() -> Iterator[tuple[str, KlaintApplication]]:
    """Spin up a live multi-threaded KlaintHTTPServer on an ephemeral localhost port."""
    data_dir = Path(tempfile.mkdtemp(prefix="klaint_srv_test_"))
    app = KlaintApplication(
        data_dir,
        default_tenant_id="acme-ops",
        default_api_key="klaint-acme-secret-key",
        webhook_secrets={"acme-ops": WEBHOOK_SECRET},
    )
    app.register_tenant_api_key("beta-ops", "klaint-beta-secret-key")
    httpd, thread, base_url = start_background_server(app, host="127.0.0.1", port=0)
    try:
        yield base_url, app
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=3)
        app.close()
        shutil.rmtree(data_dir, ignore_errors=True)


def _http_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    raw_body: bytes | None = None,
) -> tuple[int, bytes, dict[str, Any] | None]:
    req_headers = dict(headers or {})
    data: bytes | None = None
    if raw_body is not None:
        data = raw_body
    elif json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json; charset=utf-8")

    req = urllib.request.Request(f"{base_url}{path}", data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body_bytes = resp.read()
            ct = resp.headers.get("Content-Type", "")
            parsed = json.loads(body_bytes.decode("utf-8")) if "application/json" in ct else None
            return int(resp.status), body_bytes, parsed
    except urllib.error.HTTPError as err:
        body_bytes = err.read()
        try:
            parsed = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            parsed = None
        return int(err.code), body_bytes, parsed


def test_studio_ui_widget_and_rest_workflows_with_why_panel(live_klaint_server) -> None:
    """Verify Klaint Studio (/), Widget (/widget), static assets, auth, SOP 4-eyes, tickets, and Why panel."""
    base_url, app = live_klaint_server
    acme_headers = {"X-Klaint-Api-Key": "klaint-acme-secret-key"}
    beta_headers = {"X-Klaint-Api-Key": "klaint-beta-secret-key"}

    # 1. Studio HTML, CSS (#1F7A65 Quiet Signal emerald), JS, and Customer Widget
    st_code, st_html, _ = _http_request(base_url, "/")
    assert st_code == 200
    assert b"Klaint Studio" in st_html
    assert b"Why Explainability Panel" in st_html
    assert b'data-view="approvals"' in st_html

    css_code, css_bytes, _ = _http_request(base_url, "/static/studio.css")
    assert css_code == 200
    assert b"#1F7A65" in css_bytes

    js_code, js_bytes, _ = _http_request(base_url, "/static/studio.js")
    assert js_code == 200
    assert b"renderWhyPanel" in js_bytes

    wg_code, wg_html, _ = _http_request(base_url, "/widget")
    assert wg_code == 200
    assert b"Talk to a person" in wg_html
    assert b'dir="auto"' in wg_html

    # 2. Unauthenticated and cross-tenant requests rejected
    unauth_code, _, _ = _http_request(base_url, "/api/v1/overview")
    assert unauth_code == 401

    cross_code, _, _ = _http_request(
        base_url,
        "/api/v1/overview",
        headers={"X-Klaint-Api-Key": "klaint-acme-secret-key", "X-Klaint-Tenant": "beta-ops"},
    )
    assert cross_code == 403

    # 3. Operator authentication + 4-eyes SOP approval & rollback over REST
    _, _, login_sara = _http_request(
        base_url,
        "/api/v1/auth/operator-login",
        method="POST",
        headers=acme_headers,
        json_body={"operator_id": "op_sara", "role": "editor"},
    )
    _, _, login_omar = _http_request(
        base_url,
        "/api/v1/auth/operator-login",
        method="POST",
        headers=acme_headers,
        json_body={"operator_id": "op_omar", "role": "approver"},
    )
    sara_hdrs = {**acme_headers, "X-Klaint-Operator-Token": login_sara["operator_token"]}
    omar_hdrs = {**acme_headers, "X-Klaint-Operator-Token": login_omar["operator_token"]}

    # Cross-tenant operator token must fail with 403
    bad_op_code, _, _ = _http_request(
        base_url,
        "/api/v1/procedures/drafts",
        method="POST",
        headers={**beta_headers, "X-Klaint-Operator-Token": login_sara["operator_token"]},
        json_body={"domain": "refund", "title": "Cross", "natural_language_text": "Auto-allow 1000 cents"},
    )
    assert bad_op_code == 403

    d_code, _, draft_resp = _http_request(
        base_url,
        "/api/v1/procedures/drafts",
        method="POST",
        headers=sara_hdrs,
        json_body={
            "sop_id": "sop-refund",
            "domain": "refund",
            "title": "Updated Refund SOP",
            "natural_language_text": "Auto-allow refunds up to 6000 cents within 30 days.",
        },
    )
    assert d_code == 201
    v_num = draft_resp["version_num"]

    # Self-approval by Sara fails with 403
    self_code, _, _ = _http_request(
        base_url,
        "/api/v1/procedures/approve",
        method="POST",
        headers=sara_hdrs,
        json_body={"sop_id": "sop-refund", "version_num": v_num},
    )
    assert self_code == 403

    # Approval by Omar succeeds, then 1-click rollback restores v1
    app_code, _, app_resp = _http_request(
        base_url,
        "/api/v1/procedures/approve",
        method="POST",
        headers=omar_hdrs,
        json_body={"sop_id": "sop-refund", "version_num": v_num},
    )
    assert app_code == 200 and app_resp["status"] == "active"

    rb_code, _, rb_resp = _http_request(
        base_url,
        "/api/v1/procedures/rollback",
        method="POST",
        headers=omar_hdrs,
        json_body={"sop_id": "sop-refund", "target_version_num": 1},
    )
    assert rb_code == 200 and rb_resp["version_num"] == 1

    # 4. Knowledge ingest + cited search + Customer Widget resolution + Why Explainability Panel
    ing_code, _, _ = _http_request(
        base_url,
        "/api/v1/knowledge/ingest",
        method="POST",
        headers=omar_hdrs,
        json_body={
            "doc_id": "doc-warranty",
            "title": "Hardware Warranty",
            "content": "All Wispral microphones carry a 24-month hardware replacement warranty.",
            "acl_tags": ["public", "customer"],
        },
    )
    assert ing_code == 201

    app.connectors("acme-ops").seed_order(
        order_id="ord-web-1",
        customer_id="cust-web-1",
        total_cents=3800,
        days_since_delivery=2,
    )

    _, _, ses_data = _http_request(
        base_url,
        "/api/v1/widget/session",
        method="POST",
        headers=acme_headers,
        json_body={"tenant_id": "acme-ops", "customer_id": "cust-web-1", "language": "en"},
    )
    cust_hdrs = {"X-Klaint-Customer-Token": ses_data["customer_token"]}

    msg_code, _, turn_data = _http_request(
        base_url,
        "/api/v1/widget/messages",
        method="POST",
        headers=cust_hdrs,
        json_body={"message": "Please refund my order ord-web-1."},
    )
    assert msg_code == 200
    assert turn_data["resolution_status"] == "resolved"
    assert len(turn_data["receipt_ids"]) == 1

    # Fetch dedicated 'Why' Explainability Panel for the turn
    why_code, _, why_data = _http_request(
        base_url,
        f"/api/v1/turns/{turn_data['turn_id']}/why",
        headers=acme_headers,
    )
    assert why_code == 200
    assert len(why_data["stages"]) == 8
    assert why_data["verdict_chip"]["en"] == "Allowed"
    assert why_data["verdict_chip"]["ar"] == "مسموح"
    assert why_data["capability_args_digest"].startswith("sha256:")
    assert why_data["receipt_ids"] == turn_data["receipt_ids"]

    # 5. Tickets lifecycle (`open -> pending -> snoozed -> escalated -> resolved`) + internal notes + audit verify
    t_code, _, tkt = _http_request(
        base_url,
        "/api/v1/tickets",
        method="POST",
        headers=omar_hdrs,
        json_body={
            "customer_id": "cust-web-1",
            "subject": "Follow-up receipt copy",
            "priority": "high",
            "conversation_id": ses_data["conversation_id"],
        },
    )
    assert t_code == 201
    ticket_id = tkt["ticket_id"]

    for next_state in ("pending", "snoozed", "escalated", "resolved"):
        p_code, _, p_tkt = _http_request(
            base_url,
            f"/api/v1/tickets/{ticket_id}",
            method="PATCH",
            headers=omar_hdrs,
            json_body={"status": next_state},
        )
        assert p_code == 200 and p_tkt["status"] == next_state

    n_code, _, note = _http_request(
        base_url,
        f"/api/v1/tickets/{ticket_id}/notes",
        method="POST",
        headers=omar_hdrs,
        json_body={"body": "Verified receipt delivered to customer."},
    )
    assert n_code == 201 and note["visibility"] == "internal"

    aud_code, _, aud_verify = _http_request(base_url, "/api/v1/audit/verify", headers=acme_headers)
    assert aud_code == 200 and aud_verify["valid"] is True


def test_ownership_epoch_human_takeover_race_discards_stale_ai_turn(live_klaint_server) -> None:
    """Live concurrency test: operator human takeover mid-turn increments ownership_epoch and discards stale AI turn."""
    base_url, app = live_klaint_server
    acme_headers = {"X-Klaint-Api-Key": "klaint-acme-secret-key"}
    _, _, login = _http_request(
        base_url,
        "/api/v1/auth/operator-login",
        method="POST",
        headers=acme_headers,
        json_body={"operator_id": "op_supervisor_nour", "role": "supervisor"},
    )
    op_headers = {**acme_headers, "X-Klaint-Operator-Token": login["operator_token"]}

    app.connectors("acme-ops").seed_order(
        order_id="ord-race-1",
        customer_id="cust-race-1",
        total_cents=2500,
        days_since_delivery=1,
    )
    _, _, ses_data = _http_request(
        base_url,
        "/api/v1/widget/session",
        method="POST",
        headers=acme_headers,
        json_body={"tenant_id": "acme-ops", "customer_id": "cust-race-1", "language": "en"},
    )
    conv_id = ses_data["conversation_id"]
    cust_headers = {"X-Klaint-Customer-Token": ses_data["customer_token"]}

    ai_result_holder: dict[str, Any] = {}

    def _in_flight_ai_turn() -> None:
        code, _, payload = _http_request(
            base_url,
            "/api/v1/widget/messages",
            method="POST",
            headers={**cust_headers, **acme_headers},
            json_body={
                "message": "Please refund my order ord-race-1",
                "simulate_ai_delay_ms": 450,
            },
        )
        ai_result_holder["status_code"] = code
        ai_result_holder["payload"] = payload

    worker = threading.Thread(target=_in_flight_ai_turn)
    worker.start()

    # Operator takes over 100ms into the AI turn while it is in-flight before EXECUTE/commit!
    time.sleep(0.10)
    tk_code, _, tk_data = _http_request(
        base_url,
        f"/api/v1/conversations/{conv_id}/takeover",
        method="POST",
        headers=op_headers,
        json_body={},
    )
    worker.join(timeout=10)

    assert tk_code == 200
    assert tk_data["owner_kind"] == "human_owned"
    assert tk_data["ownership_epoch"] == 1
    assert tk_data["banner"] == "AI paused — you own this conversation"

    # In-flight AI turn bound to epoch 0 MUST be discarded with 409 Conflict and zero refund executed!
    assert ai_result_holder["status_code"] == 409
    assert ai_result_holder["payload"]["error_type"] == "StaleEpochError"

    db = app.storage.for_tenant("acme-ops")
    with db.read_connection() as conn:
        refunds = conn.execute("SELECT COUNT(*) FROM biz_refunds WHERE order_id = 'ord-race-1'").fetchone()[0]
        turns = conn.execute("SELECT COUNT(*) FROM conversation_turns WHERE conversation_id = ?", (conv_id,)).fetchone()[0]
    assert refunds == 0
    assert turns == 0

    # Explicit return-to-ai advances ownership_epoch monotonically to 2 and re-enables AI turns
    ret_code, _, ret_data = _http_request(
        base_url,
        f"/api/v1/conversations/{conv_id}/return-to-ai",
        method="POST",
        headers=op_headers,
        json_body={},
    )
    assert ret_code == 200
    assert ret_data["owner_kind"] == "ai_owned"
    assert ret_data["ownership_epoch"] == 2

    resumed_code, _, resumed_turn = _http_request(
        base_url,
        "/api/v1/widget/messages",
        method="POST",
        headers=cust_headers,
        json_body={"message": "Please refund my order ord-race-1"},
    )
    assert resumed_code == 200
    assert resumed_turn["ownership_epoch"] == 2
    assert resumed_turn["resolution_status"] == "resolved"


def test_chatwoot_standard_webhooks_valid_tampered_stale_replayed_and_ee_rejected(live_klaint_server) -> None:
    """Verify Standard Webhooks raw-byte HMAC-SHA256, +/-300s timestamp skew, SQLite replay cache, and zero EE."""
    base_url, app = live_klaint_server
    _, _, ses_data = _http_request(
        base_url,
        "/api/v1/widget/session",
        method="POST",
        headers={"X-Klaint-Api-Key": "klaint-acme-secret-key"},
        json_body={"tenant_id": "acme-ops", "customer_id": "cust-cw-1"},
    )
    conv_id = ses_data["conversation_id"]

    now_ts = int(time.time())
    raw_body = json.dumps(
        {
            "event": "conversation_updated",
            "conversation": {
                "custom_attributes": {"klaint_conversation_id": conv_id},
                "meta": {
                    "assignee": {"id": 42, "name": "Sara"},
                    "sender": {"id": 99, "identifier": "cust-cw-1", "name": "Customer CW", "email": "cw@example.com"},
                },
            },
        }
    ).encode("utf-8")

    valid_sig = sign_standard_webhook(
        secret=WEBHOOK_SECRET,
        webhook_id="msg_valid_001",
        webhook_timestamp=now_ts,
        raw_body=raw_body,
    )
    valid_headers = {
        "Content-Type": "application/json",
        "webhook-id": "msg_valid_001",
        "webhook-timestamp": str(now_ts),
        "webhook-signature": valid_sig,
    }

    # 1. Valid Standard Webhook -> 200 OK & triggers human takeover epoch increment
    code_ok, _, body_ok = _http_request(
        base_url,
        "/api/v1/webhooks/chatwoot/acme-ops",
        method="POST",
        headers=valid_headers,
        raw_body=raw_body,
    )
    assert code_ok == 200
    assert body_ok["action"] == "human_takeover"
    assert body_ok["ownership_epoch"] == 1

    # 2. Exact replay of msg_valid_001 -> 401 Rejected by SQLite replay cache
    code_replay, _, body_replay = _http_request(
        base_url,
        "/api/v1/webhooks/chatwoot/acme-ops",
        method="POST",
        headers=valid_headers,
        raw_body=raw_body,
    )
    assert code_replay == 401
    assert "Replay detected" in body_replay["error"]

    # 3. Tampered raw bytes (appending a trailing space alters raw bytes without altering JSON meaning) -> 401
    tampered_raw = raw_body + b" "
    code_tamper, _, _ = _http_request(
        base_url,
        "/api/v1/webhooks/chatwoot/acme-ops",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "webhook-id": "msg_tampered_002",
            "webhook-timestamp": str(now_ts),
            "webhook-signature": sign_standard_webhook(
                secret=WEBHOOK_SECRET,
                webhook_id="msg_tampered_002",
                webhook_timestamp=now_ts,
                raw_body=raw_body,  # Signed over original bytes, sent with trailing space!
            ),
        },
        raw_body=tampered_raw,
    )
    assert code_tamper == 401

    # 4. Stale timestamp (> 300s skew) -> 401
    stale_ts = now_ts - 450
    stale_sig = sign_standard_webhook(
        secret=WEBHOOK_SECRET,
        webhook_id="msg_stale_003",
        webhook_timestamp=stale_ts,
        raw_body=raw_body,
    )
    code_stale, _, _ = _http_request(
        base_url,
        "/api/v1/webhooks/chatwoot/acme-ops",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "webhook-id": "msg_stale_003",
            "webhook-timestamp": str(stale_ts),
            "webhook-signature": stale_sig,
        },
        raw_body=raw_body,
    )
    assert code_stale == 401

    # 5. Chatwoot Enterprise Edition payload rejected (MIT Core API only)
    ee_raw = json.dumps({"event": "sla_policy_breach", "enterprise": True}).encode("utf-8")
    ee_sig = sign_standard_webhook(
        secret=WEBHOOK_SECRET,
        webhook_id="msg_ee_004",
        webhook_timestamp=now_ts,
        raw_body=ee_raw,
    )
    code_ee, _, body_ee = _http_request(
        base_url,
        "/api/v1/webhooks/chatwoot/acme-ops",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "webhook-id": "msg_ee_004",
            "webhook-timestamp": str(now_ts),
            "webhook-signature": ee_sig,
        },
        raw_body=ee_raw,
    )
    assert code_ee == 401
    assert "Enterprise Edition" in body_ee["error"]

    # 6. Non-allowlisted event rejected even when HMAC is valid
    unlisted_raw = json.dumps({"event": "automation_rule_updated"}).encode("utf-8")
    unlisted_sig = sign_standard_webhook(
        secret=WEBHOOK_SECRET,
        webhook_id="msg_unlisted_005",
        webhook_timestamp=now_ts,
        raw_body=unlisted_raw,
    )
    code_unlisted, _, body_unlisted = _http_request(
        base_url,
        "/api/v1/webhooks/chatwoot/acme-ops",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "webhook-id": "msg_unlisted_005",
            "webhook-timestamp": str(now_ts),
            "webhook-signature": unlisted_sig,
        },
        raw_body=unlisted_raw,
    )
    assert code_unlisted == 401
    assert "allowlisted" in body_unlisted["error"]


def test_tau2_db_hash_simulation_en_four_arabic_varieties_codeswitch_and_adversarial(klaint_env) -> None:
    """Run tau2 DB-state SHA-256 simulation across EN + 4 Arabic varieties + code-switching + adversarial suite."""
    base_dir, _, broker, _, _ = klaint_env
    runner = KlaintSimulationRunner(data_dir=base_dir, broker=broker)
    report = runner.run_suite()

    assert report["evaluator"] == "tau2-db-state-sha256"
    assert report["synthetic_disclosure"] is True
    assert report["total_scenarios"] == 11
    failed = [s for s in report["scenarios"] if not s["passed"]]
    assert failed == [], f"Failed simulation scenarios: {failed}"
    assert report["all_passed"] is True

    varieties_covered = {s["observed_variety"] for s in report["scenarios"]}
    assert {"en", "ar-MSA", "ar-Gulf", "ar-EG", "ar-Levantine", "ar-en-codeswitch"}.issubset(varieties_covered)


def test_verified_analytics_fcr_recontact_languages_and_zero_fabricated_csat(klaint_env) -> None:
    """Verify FCR, recontact rate, escalation rate, language breakdown, and strictly null unfabricated CSAT."""
    _, storage, _, session_auth, engine = klaint_env
    from klaint.analytics.metrics import AnalyticsEngine

    db = storage.for_tenant("metrics-tenant")
    connectors = BusinessConnectorSuite(db)
    connectors.seed_order(order_id="ord-m1", customer_id="cust-1", total_cents=2000, days_since_delivery=2)
    connectors.seed_order(order_id="ord-m2", customer_id="cust-2", total_cents=2200, days_since_delivery=2)
    connectors.seed_order(order_id="ord-m3", customer_id="cust-3", total_cents=15000, days_since_delivery=2)

    # Conv 1: Clean single-session FCR in English
    s1, _ = session_auth.create_session(tenant_id="metrics-tenant", customer_id="cust-1", language="en")
    engine.resolve_turn(session=s1, customer_text="Please refund my order ord-m1")

    # Conv 2 + Conv 3 (recontact of Conv 2): Neither counts as FCR!
    s2, _ = session_auth.create_session(tenant_id="metrics-tenant", customer_id="cust-2", language="ar")
    conv2 = engine.ensure_conversation(s2)
    engine.resolve_turn(session=s2, customer_text="أريد استرداد المبلغ للطلب ord-m2")

    s2_followup, _ = session_auth.create_session(tenant_id="metrics-tenant", customer_id="cust-2", language="ar")
    engine.ensure_conversation(s2_followup, recontact_of=conv2["conversation_id"])
    engine.resolve_turn(session=s2_followup, customer_text="عايز اتأكد من حالة الطلب دلوقتي")

    # Conv 4: Escalated / awaiting approval in Saudi/Gulf dialect
    s3, _ = session_auth.create_session(tenant_id="metrics-tenant", customer_id="cust-3", language="ar")
    engine.resolve_turn(session=s3, customer_text="هلا طال عمرك، ابي استرداد الطلبية ord-m3 الحين")

    overview = AnalyticsEngine(storage).compute_overview("metrics-tenant")
    assert overview["total_conversations"] == 4
    assert overview["fcr_count"] == 1
    assert overview["fcr_rate"] == 0.25
    assert overview["recontact_rate"] == 0.5
    assert overview["csat_score"] is None
    assert overview["csat_basis"] == "unmeasured_no_fabricated_csat"
    assert overview["by_language"]["en"]["fcr_rate"] == 1.0
    assert overview["by_language"]["ar-Gulf"]["turns"] == 1
    assert overview["by_language"]["ar-EG"]["turns"] == 1


def test_klaint_doctor_cli_and_omalla_voice_bridge_gated_and_barge_in(klaint_env) -> None:
    """Verify `klaint doctor` CLI and Omalla voice bridge (Commitment Output Gate + barge-in/takeover)."""
    base_dir, storage, _, session_auth, engine = klaint_env

    # 1. `klaint doctor` programmatic & CLI check
    doc = run_doctor(base_dir)
    assert doc["status"] == "PASS"
    assert all(c["ok"] for c in doc["checks"])
    assert cli_main(["doctor", "--data-dir", str(base_dir), "--json"]) == 0

    # 2. Standalone text mode works with zero Omalla dependency
    db = storage.for_tenant("voice-tenant")
    BusinessConnectorSuite(db).seed_order(order_id="ord-v1", customer_id="cust-v1", total_cents=2400)
    ses_txt, _ = session_auth.create_session(tenant_id="voice-tenant", customer_id="cust-v1")
    text_bridge = KlaintVoiceBridge(resolution_engine=engine, mode="standalone_text")
    txt_out = text_bridge.handle_text_turn(session=ses_txt, customer_text="Please refund ord-v1")
    assert txt_out.status == "delivered"
    assert len(txt_out.receipt_ids) == 1

    # 3. Omalla voice mode: tentative frame buffered only; unbacked commitment blocked; barge-in interrupts clauses
    spoken_sink: list[str] = []
    voice_bridge = KlaintVoiceBridge(
        resolution_engine=engine,
        mode="omalla_voice",
        tts_sink=lambda clause, _ses: spoken_sink.append(clause),
    )

    ses_voice, _ = session_auth.create_session(
        tenant_id="voice-tenant",
        customer_id="cust-v2",
        channel="voice",
        language="ar",
    )
    tentative = voice_bridge.handle_omalla_frame(
        session=ses_voice,
        frame=OmallaTranscriptFrame(utterance_id="u-1", text="تم...", is_final=False, language="ar"),
    )
    assert tentative.status == "caption_buffered"
    assert spoken_sink == []

    # Unbacked spoken Arabic refund claim MUST be blocked by CommitmentOutputGate before TTS utters it!
    blocked_voice = voice_bridge.handle_omalla_frame(
        session=ses_voice,
        frame=OmallaTranscriptFrame(utterance_id="u-1", text="ما حالة طلبي؟", is_final=True, language="ar"),
        draft_override="تم استرداد المبلغ فوراً إلى بطاقتك.",
    )
    assert blocked_voice.status == "blocked_by_gate"
    assert "ar_refund_committed" in blocked_voice.gate_blocked_claims
    assert all("تم استرداد المبلغ فوراً" not in s for s in spoken_sink)

    # Multi-clause spoken output interrupted mid-delivery by customer barge-in
    spoken_sink.clear()
    ses_barge, _ = session_auth.create_session(tenant_id="voice-tenant", customer_id="cust-v1", channel="voice")
    interrupted = voice_bridge.handle_omalla_frame(
        session=ses_barge,
        frame=OmallaTranscriptFrame(utterance_id="u-2", text="Hello there", is_final=True, language="en"),
        draft_override="First safe spoken sentence. Second sentence that should be cut off by barge-in.",
        inter_clause_hook=lambda idx: voice_bridge.trigger_barge_in(ses_barge.session_id) if idx == 1 else None,
    )
    assert interrupted.status == "partial_interrupted"
    assert len(interrupted.spoken_clauses) == 1
    assert len(interrupted.discarded_clauses) == 1


def test_pstack_review_hardening_widget_spoofing_sim_isolation_and_studio_ui(live_klaint_server) -> None:
    """Verify all KL-2 PStack review must-fixes:
    - Unauthenticated widget customer_id spoofing rejected (401); unregistered tenant rejected (403); public widget gets anon-...
    - Unauthenticated draft_override & simulate_ai_delay_ms rejected (401)
    - Simulation endpoint runs in isolated temp dir without polluting live app.data_dir
    - Ephemeral default secrets when omitted (never static hardcoded dev keys)
    - Studio UI includes sessionStorage operator sign-in bar, SOP draft form, CSV/JSON audit export, and chip-ask/chip-deny mapping
    - Operator approval over HTTP succeeds while conversation is human_owned
    """
    base_url, app = live_klaint_server
    acme_headers = {"X-Klaint-Api-Key": "klaint-acme-secret-key"}
    _, _, login = _http_request(
        base_url,
        "/api/v1/auth/operator-login",
        method="POST",
        headers=acme_headers,
        json_body={"operator_id": "op_reviewer_hana", "role": "supervisor"},
    )
    op_headers = {**acme_headers, "X-Klaint-Operator-Token": login["operator_token"]}

    # 1. Unauthenticated caller supplying customer_id MUST be rejected (401)
    spoof_code, _, _ = _http_request(
        base_url,
        "/api/v1/widget/session",
        method="POST",
        json_body={"tenant_id": "acme-ops", "customer_id": "cust-victim-vip"},
    )
    assert spoof_code == 401

    # Unregistered tenant on public widget MUST be rejected (403)
    unreg_code, _, _ = _http_request(
        base_url,
        "/api/v1/widget/session",
        method="POST",
        json_body={"tenant_id": "unregistered-ghost"},
    )
    assert unreg_code == 403

    # Public widget without customer_id on registered tenant mints fresh anon-... customer_id
    anon_code, _, anon_ses = _http_request(
        base_url,
        "/api/v1/widget/session",
        method="POST",
        json_body={"tenant_id": "acme-ops", "language": "en"},
    )
    assert anon_code == 201
    assert anon_ses["customer_id"].startswith("anon-")
    anon_hdrs = {"X-Klaint-Customer-Token": anon_ses["customer_token"]}

    # 2. Unauthenticated draft_override or simulate_ai_delay_ms on /widget/messages MUST be rejected (401)
    unauth_override_code, _, _ = _http_request(
        base_url,
        "/api/v1/widget/messages",
        method="POST",
        headers=anon_hdrs,
        json_body={"message": "Hi", "draft_override": "We have refunded your order."},
    )
    assert unauth_override_code == 401

    unauth_delay_code, _, _ = _http_request(
        base_url,
        "/api/v1/widget/messages",
        method="POST",
        headers=anon_hdrs,
        json_body={"message": "Hi", "simulate_ai_delay_ms": 250},
    )
    assert unauth_delay_code == 401

    # 3. Studio HTML/JS features & CSV audit export check
    _, st_html, _ = _http_request(base_url, "/")
    _, st_js, _ = _http_request(base_url, "/static/studio.js")
    assert b'id="studio-auth-form"' in st_html
    assert b'id="create-sop-draft-form"' in st_html
    assert b'id="export-audit-json-btn"' in st_html
    assert b'id="export-audit-csv-btn"' in st_html
    assert b"sessionStorage" in st_js
    assert b"chip-ask" in st_js and b"chip-deny" in st_js

    csv_code, csv_bytes, _ = _http_request(base_url, "/api/v1/audit?format=csv", headers=acme_headers)
    assert csv_code == 200
    assert b"seq,event_kind,actor" in csv_bytes

    # 4. Human takeover + operator approval over HTTP succeeds while conversation is human_owned
    app.connectors("acme-ops").seed_order(
        order_id="ord-ho-http",
        customer_id="cust-ho-http",
        total_cents=14000,
        days_since_delivery=3,
    )
    _, _, ho_ses = _http_request(
        base_url,
        "/api/v1/widget/session",
        method="POST",
        headers=acme_headers,
        json_body={"tenant_id": "acme-ops", "customer_id": "cust-ho-http"},
    )
    _, _, ask_turn = _http_request(
        base_url,
        "/api/v1/widget/messages",
        method="POST",
        headers={"X-Klaint-Customer-Token": ho_ses["customer_token"]},
        json_body={"message": "Please refund my order ord-ho-http"},
    )
    assert ask_turn["resolution_status"] == "awaiting_approval"

    tk_code, _, _ = _http_request(
        base_url,
        f"/api/v1/conversations/{ho_ses['conversation_id']}/takeover",
        method="POST",
        headers=op_headers,
        json_body={},
    )
    assert tk_code == 200

    dec_code, _, dec_body = _http_request(
        base_url,
        f"/api/v1/approvals/{ask_turn['approval_id']}/decide",
        method="POST",
        headers=op_headers,
        json_body={"approve": True, "note": "Approved after human takeover"},
    )
    assert dec_code == 200
    assert dec_body["status"] == "approved"
    assert dec_body["receipt_id"] is not None

    # 5. Simulation endpoint runs in isolated temp directory without creating sim-* tenants in live app.data_dir
    tenants_before = set(app.storage.list_tenants())
    sim_code, _, sim_body = _http_request(
        base_url,
        "/api/v1/simulation/run",
        method="POST",
        headers=op_headers,
        json_body={},
    )
    assert sim_code == 200 and sim_body["all_passed"] is True
    tenants_after = set(app.storage.list_tenants())
    assert tenants_after == tenants_before

    # 6. Default KlaintApplication without explicit default_api_key generates unique random ephemeral secrets
    ephemeral_dir = Path(tempfile.mkdtemp(prefix="klaint_ephem_"))
    try:
        ephem_app = KlaintApplication(ephemeral_dir)
        try:
            assert ephem_app.default_api_key.startswith("klaint-")
            assert ephem_app.default_api_key != "klaint-dev-tenant-key"
        finally:
            ephem_app.close()
    finally:
        shutil.rmtree(ephemeral_dir, ignore_errors=True)
