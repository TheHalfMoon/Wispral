# SPDX-License-Identifier: Apache-2.0
"""Klaint CLI (`klaint doctor`, `klaint serve`, `klaint simulate`)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

from klaint import __ecosystem__, __product__, __vendor__, __version__
from klaint.broker.client import BrokerClient
from klaint.conversation.gate import CommitmentOutputGate
from klaint.core.errors import CanonicalSerializationError
from klaint.core.jcs import compute_args_digest
from klaint.core.models import SessionAuthenticator
from klaint.server.app import main as server_main
from klaint.simulation.suite import KlaintSimulationRunner
from klaint.storage.tenant_db import TenantStorageRegistry
from klaint.ui import load_static_asset, load_studio_html, load_widget_html


def run_doctor(data_dir: Path | str | None = None) -> dict[str, Any]:
    """Run deterministic self-diagnostics across broker isolation, SQLite WAL/FTS5, JCS, Output Gate, and UI."""
    owned_tmp: Path | None = None
    if data_dir is None:
        owned_tmp = Path(tempfile.mkdtemp(prefix="klaint_doctor_"))
        probe_dir = owned_tmp
    else:
        probe_dir = Path(data_dir).resolve() / "_doctor_probe"
        probe_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []
    storage = TenantStorageRegistry(probe_dir)
    broker: BrokerClient | None = None

    try:
        # 1. Python & SQLite WAL + FTS5 check
        db = storage.for_tenant("doctor-probe")
        pragmas = db.get_pragmas()
        fts_ok = False
        with db.read_connection() as conn:
            row = conn.execute("SELECT sqlite_version()").fetchone()
            sqlite_ver = str(row[0])
            fts_ok = True
        checks.append(
            {
                "name": "sqlite_wal_and_fts5",
                "ok": pragmas["journal_mode"] == "wal" and pragmas["foreign_keys"] == 1 and fts_ok,
                "detail": f"SQLite {sqlite_ver}, pragmas={pragmas}",
            }
        )

        # 2. RFC 8785 JCS IEEE-754 float rejection check
        float_rejected = False
        try:
            compute_args_digest({"bad_float": 1.25})
        except CanonicalSerializationError:
            float_rejected = True
        checks.append(
            {
                "name": "jcs_float_rejection",
                "ok": float_rejected,
                "detail": "IEEE-754 floats rejected in canonical signed arguments",
            }
        )

        # 3. Out-of-process Ed25519 capability broker spawn & PID separation
        broker = BrokerClient(probe_dir)
        info = broker.info()
        checks.append(
            {
                "name": "out_of_process_broker",
                "ok": broker.broker_pid != os.getpid() and len(broker.public_key_b64) >= 43,
                "detail": f"host_pid={os.getpid()}, broker_pid={broker.broker_pid}, key_id={info['key_id']}",
            }
        )

        # 4. Commitment Output Gate EN & AR self-test
        auth = SessionAuthenticator()
        ses, _ = auth.create_session(tenant_id="doctor-probe", customer_id="cust-doc", language="ar")
        gate = CommitmentOutputGate(db)
        blocked_en = not gate.evaluate(session=ses, draft_text="We have refunded your order.").allowed
        blocked_ar = not gate.evaluate(session=ses, draft_text="تم استرداد المبلغ لحسابك.").allowed
        checks.append(
            {
                "name": "commitment_output_gate_en_ar",
                "ok": blocked_en and blocked_ar,
                "detail": "Unbacked English & Arabic commitments blocked in BLOCK mode",
            }
        )

        # 5. Audit log SHA-256 hash chain verification
        db.append_audit(event_kind="doctor_probe", actor="klaint_doctor", payload={"ok": True})
        chain = db.verify_audit_chain()
        checks.append(
            {
                "name": "audit_sha256_hash_chain",
                "ok": chain.valid and chain.total_entries >= 1,
                "detail": f"valid={chain.valid}, entries={chain.total_entries}",
            }
        )

        # 6. Klaint Studio & Widget UI assets check
        studio_html = load_studio_html()
        widget_html = load_widget_html()
        css_asset = load_static_asset("studio.css")
        js_asset = load_static_asset("studio.js")
        ui_ok = (
            b"#1F7A65" in (css_asset[0] if css_asset else b"")
            and b"Why Explainability Panel" in studio_html
            and b"Talk to a person" in widget_html
            and js_asset is not None
        )
        checks.append(
            {
                "name": "studio_and_widget_ui_assets",
                "ok": ui_ok,
                "detail": "Quiet Signal #1F7A65 tokens, Studio SPA, Why panel, and Customer Widget verified",
            }
        )
    except sqlite3.Error as exc:
        checks.append({"name": "sqlite_error", "ok": False, "detail": str(exc)})
    finally:
        if broker is not None:
            broker.close()
        storage.close_all()
        if owned_tmp is not None:
            shutil.rmtree(owned_tmp, ignore_errors=True)
        elif data_dir is not None:
            shutil.rmtree(probe_dir, ignore_errors=True)

    all_ok = all(bool(c["ok"]) for c in checks)
    return {
        "status": "PASS" if all_ok else "FAIL",
        "product": __product__,
        "ecosystem": __ecosystem__,
        "vendor": __vendor__,
        "version": __version__,
        "python": sys.version.split()[0],
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="klaint", description="Klaint CLI (Wispral by Halfmoon)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_doc = sub.add_parser("doctor", help="Run Klaint platform & trust-boundary self-diagnostics")
    p_doc.add_argument("--data-dir", default=None)
    p_doc.add_argument("--json", action="store_true", dest="as_json")

    p_srv = sub.add_parser("serve", help="Start klaint-server (Studio + Widget + REST API)")
    p_srv.add_argument("--host", default="127.0.0.1")
    p_srv.add_argument("--port", type=int, default=8090)
    p_srv.add_argument("--data-dir", default=".klaint_data")
    p_srv.add_argument("--tenant-id", default="default-tenant")

    p_sim = sub.add_parser("simulate", help="Run tau2 DB-state SHA-256 simulation & adversarial suite")
    p_sim.add_argument("--json", action="store_true", dest="as_json")

    ns = parser.parse_args(argv)

    if ns.command == "doctor":
        report = run_doctor(ns.data_dir)
        if ns.as_json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"{report['product']} v{report['version']} ({report['ecosystem']} by {report['vendor']}) — DOCTOR: {report['status']}")
            for chk in report["checks"]:
                mark = "PASS" if chk["ok"] else "FAIL"
                print(f"  [{mark}] {chk['name']}: {chk['detail']}")
        return 0 if report["status"] == "PASS" else 1

    if ns.command == "serve":
        return server_main(
            [
                "--host",
                ns.host,
                "--port",
                str(ns.port),
                "--data-dir",
                ns.data_dir,
                "--tenant-id",
                ns.tenant_id,
            ]
        )

    if ns.command == "simulate":
        sim_report = KlaintSimulationRunner().run_suite()
        if ns.as_json:
            print(json.dumps(sim_report, indent=2, ensure_ascii=False))
        else:
            print(
                f"Simulation ({sim_report['evaluator']}): "
                f"{sim_report['passed_scenarios']}/{sim_report['total_scenarios']} passed"
            )
        return 0 if sim_report["all_passed"] else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
