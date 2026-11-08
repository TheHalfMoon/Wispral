"""Generate fixtures/cases.json for the CANDIDATE Wispral contracts.

Usage (from repository root):  python -I docs/engineering/contracts/fixtures/build_cases.py
Each tamper case names the invariant it attacks; G-* IDs refer to the Core audit gap probe
(research/wispral-world-class/evidence/research-reports/CORE_FOUNDER_REPOS_RESEARCH.md section 3).
"runtime" cases are shape-valid but must be rejected by run_conformance.py's runtime checks.
"""

import copy
import hashlib
import json
import pathlib

H = "sha256:" + "a" * 64
HX = "b" * 64


def mutate(base, path, value):
    inst = copy.deepcopy(base)
    node = inst
    for key in path[:-1]:
        node = node[key]
    if value is DELETE:
        del node[path[-1]]
    else:
        node[path[-1]] = value
    return inst


DELETE = object()

UNSIGNED_CONSENT_FIELDS = ("status", "revoked_at", "scope_note")


def bound_digest(record):
    """SHA-256 of the canonical JSON of every signed consent field: the record minus its lifecycle fields,
    plus the attestation minus bound_fields_digest and signature (absent optional fields as null)."""
    fields = {k: record.get(k) for k in ("subject_ref", "voice_id", "relationship", "principal_scope_ref", "purposes", "products", "allowed_engines",
                                         "valid_from", "valid_until", "evidence_digest", "consent_epoch", "watermark_required",
                                         "reference_artifact_digest", "speaker_match")}
    fields["attestation"] = {k: v for k, v in record["attestation"].items() if k not in ("bound_fields_digest", "signature")}
    return "sha256:" + hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def attest(record):
    """Re-sign (in fixture terms: re-bind) a consent record after its bound fields change."""
    if "attestation" in record:
        record = copy.deepcopy(record)
        record["attestation"]["bound_fields_digest"] = bound_digest(record)
    return record


SIGNATURE = {"alg": "ed25519", "key_id": "op-key:studio-001", "value": "A" * 86}

ENVELOPE = {
    "schema_version": 1, "request_id": "req-00000001", "session_id": "ses-00000001", "turn_id": "t1",
    "epoch": 3, "sequence": 12,
    "principal_scope": {"kind": "desktop_user", "ref": "local-user", "os_session": "1"},
    "source": {"product": "wisprside", "component": "speech_worker", "artifact_digest": H},
    "policy_version": "side-policy@1.0.0", "event": "TranscriptFinal", "payload": {},
}
TENANT_ENVELOPE = mutate(mutate(ENVELOPE, ["principal_scope"], {"kind": "tenant", "ref": "acme", "account_ref": "acct-1", "channel": "web_chat"}), ["source"], {"product": "klaint", "component": "broker"})
CANCEL = {
    "operation_id": "op-0000001", "epoch": 4, "cancel_epoch": 5, "state": "observed_stopped",
    "owner": "handy_engine_supervisor", "process_instance": {"pid": 4242, "start_generation": "133700000000000000"},
    "observation": "process_exit", "effect_state": "none", "response": "cancelled_result", "lease_released": True,
}
MANIFEST = {
    "model_id": "example-local-asr", "revision": "r1", "source_url": "https://example.invalid/model", "source_revision": "abc123",
    "modality": "stt",
    "artifact": {"files": [{"path": "model.gguf", "sha256": HX, "size_bytes": 148000000}, {"path": "tokenizer.json", "sha256": "c" * 64, "size_bytes": 2000}], "bundle_sha256": "d" * 64},
    "languages": [{"code": "en", "support": "documented"}, {"code": "ar", "variety": "MSA", "support": "documented"}, {"code": "ar-SA", "variety": "Najdi", "support": "unsupported"}],
    "runtime": "ggml", "serialization": "gguf", "trust_remote_code": False, "offline_capable": True, "network_hosts": [], "acquisition": "user_initiated_download",
    "code_license": "MIT", "weight_license": "Apache-2.0", "commercial_use": "allowed", "requires_consent": False,
    "effect_classes": ["text_hypothesis"], "authority_ceiling": "evidence_only",
    "requirements": {"process_isolation": "subprocess", "network_required": False, "accelerator": "none"},
    "admission_state": "admitted",
}
CONSENT = {
    "consent_id": "consent-0001", "voice_id": "voice-00001", "subject_ref": "subj-ab12cd", "relationship": "self",
    "principal_scope_ref": "local-user", "purposes": ["personal"], "products": ["wisprstudio"],
    "valid_from": "2026-11-08T00:00:00Z", "evidence_digest": H, "status": "active", "consent_epoch": 1, "watermark_required": True,
    "reference_artifact_digest": "sha256:" + "e" * 64, "speaker_match": {"method": "speaker_verification_model", "result": "match", "evidence_digest": H},
    "attestation": {"issuer": {"kind": "studio_operator", "key_id": "op-key:studio-001"}, "identity_check": "in_person_id_check",
                    "statement": {"script_id": "voice-consent@1", "transcript_match": "match", "operator_confirmed": True, "live_capture": True, "challenge_digest": H},
                    "bound_fields_digest": H, "nonce": "c0nsentN0nce_0123456789", "issued_at": "2026-11-08T00:00:00Z", "signature": SIGNATURE},
}
CONSENT = attest(CONSENT)
VERDICT = {
    "verdict_id": "verdict-0001", "request_id": "req-00000001", "epoch": 3, "candidate_decision": "ASK", "enforced_decision": "ASK",
    "action_class": "money", "rule_ids": ["refund_over_threshold"], "layers": [{"source": "base", "decision": "ALLOW"}, {"source": "tenant", "decision": "ASK"}],
    "policy_version": "klaint-acme@12.0.0", "inputs_digest": H, "principal_scope_ref": "tenant:acme", "human_present": True,
}
PROV = {
    "event_id": "evt-0000001", "request_id": "req-00000001", "session_id": "ses-00000001", "epoch": 3, "sequence": 12, "journal_seq": 40,
    "kind": "raw_hypothesis", "content_digest": H, "model": {"model_id": "example-local-asr", "revision": "r1", "artifact_sha256": HX},
    "actor": "speech_worker", "retention": "bounded_days", "retention_days": 7, "principal_scope_ref": "local-user", "policy_version": "side-policy@1.0.0",
}
TARGET = {"captured_at_activation": True, "window_handle": "0x00A1B2", "process_instance": {"pid": 4242, "start_generation": "133700000000000000"}, "focus_element": {"runtime_id_digest": H, "control_type": "Edit", "is_password": False, "is_read_only": False}, "image_path_digest": H, "app_display_name": "Notepad", "integrity_level": "medium"}
DELIVERY = {
    "delivery_id": "del-0000001", "intent_id": "int-0000001", "request_id": "req-00000001", "epoch": 3, "epoch_at_activation": 3,
    "target": TARGET, "revalidated_before_delivery": True, "focus_revalidated_before_delivery": True, "outcome": "delivered_confirmed", "method": "uia_value_pattern",
    "chars_total": 120, "chars_delivered": 120, "clipboard": {"used": False, "restored": False, "skipped_reason": "not_used"},
}
INTENT = {
    "intent_id": "int-0000002", "idempotency_key": "acme:refund:order-4821:v1", "owner": "klaint_broker", "action_class": "money",
    "state": "dispatched", "verdict_id": "verdict-0002", "principal_scope_ref": "tenant:acme", "epoch": 3,
    "dispatch": {"tool": "refunds.create", "args_digest": H},
    "capability": {"token_id": "cap-00000001", "issuer": "klaint_broker", "session_ref": "ses-00000001", "tool": "refunds.create", "args_digest": H,
                   "nonce": "capN0nce_0123456789abcd", "issued_at": "2026-11-08T10:00:00Z", "expires_at": "2026-11-08T10:00:30Z", "single_use": True,
                   "signature": {"alg": "ed25519", "key_id": "broker-key:acme-1", "value": "B" * 86}},
}
STUDIO_INTENT = {k: v for k, v in INTENT.items() if k not in ("dispatch", "capability")}

cases = []


def add(schema, name, expect, inst, invariant=None, layer="shape", keep_attestation=False):
    if schema == "consent_record" and not keep_attestation:
        inst = attest(inst)
    case = {"schema": schema, "name": name, "expect": expect, "layer": layer, "instance": inst}
    if invariant:
        case["invariant"] = invariant
    cases.append(case)


# ---- envelope
add("envelope", "valid_desktop_transcript_final", "valid", ENVELOPE)
add("envelope", "valid_tenant_tool_proposed", "valid", mutate(TENANT_ENVELOPE, ["event"], "ToolProposed"))
add("envelope", "invalid_unknown_principal_kind", "invalid", mutate(ENVELOPE, ["principal_scope", "kind"], "admin_from_chat"), "closed principal kinds")
add("envelope", "invalid_extra_field_credentials", "invalid", mutate(ENVELOPE, ["credential"], "secret"), "no extra top-level fields")
add("envelope", "invalid_negative_epoch", "invalid", mutate(ENVELOPE, ["epoch"], -1), "epoch is non-negative")
add("envelope", "G-ENV-1_desktop_without_os_session", "invalid", mutate(ENVELOPE, ["principal_scope"], {"kind": "desktop_user", "ref": "u"}), "desktop principal binds the OS session")
add("envelope", "G-ENV-2_tenant_without_channel", "invalid", mutate(TENANT_ENVELOPE, ["principal_scope"], {"kind": "tenant", "ref": "acme"}), "tenant principal binds account and channel")
add("envelope", "G-ENV-3_unbounded_payload", "invalid", mutate(ENVELOPE, ["payload"], {f"k{i}": i for i in range(65)}), "payload property count is bounded")
add("envelope", "G-ENV-4_render_without_consent_epoch", "invalid", mutate(mutate(ENVELOPE, ["event"], "RenderRequested"), ["source"], {"product": "wisprstudio", "component": "render_owner"}), "render events carry the consent epoch")
add("envelope", "G-ENV-5_worker_without_digest", "invalid", mutate(ENVELOPE, ["source"], {"product": "wisprside", "component": "speech_worker"}), "worker events carry the artifact digest")
add("envelope", "invalid_free_text_policy_version", "invalid", mutate(ENVELOPE, ["policy_version"], "latest"), "policy version is a digest or name@semver")

# ---- cancellation
add("cancellation", "valid_observed_stop_release", "valid", CANCEL)
add("cancellation", "valid_unconfirmed_keeps_lease", "valid", mutate(mutate(mutate(CANCEL, ["state"], "stopped_unconfirmed"), ["observation"], "deadline_expired"), ["lease_released"], False))
add("cancellation", "G-CAN-1b_crash_exit_releases_lease", "valid", mutate(mutate(CANCEL, ["state"], "failed"), ["response"], "error_request_cancelled"), "owner-observed exit after a crash releases the lease")
add("cancellation", "valid_acknowledged_pending", "valid", {**CANCEL, "state": "acknowledged", "observation": "none", "response": "pending", "lease_released": False})
add("cancellation", "invalid_release_on_ack", "invalid", {**CANCEL, "state": "acknowledged", "observation": "none", "response": "pending", "lease_released": True}, "no lease release on acknowledgement")
add("cancellation", "invalid_observed_stop_by_deadline", "invalid", {**CANCEL, "observation": "deadline_expired", "lease_released": False}, "a deadline expiry is not an observed stop")
add("cancellation", "G-CAN-2_ack_with_observation", "invalid", {**CANCEL, "state": "acknowledged", "observation": "process_exit", "response": "pending", "lease_released": False}, "acknowledged carries no stop observation")
add("cancellation", "G-CAN-3_unknown_effect_without_intent", "invalid", {**CANCEL, "effect_state": "unknown"}, "an unknown effect names its reconcile intent")
add("cancellation", "invalid_terminal_without_response", "invalid", {**CANCEL, "response": "pending"}, "every cancelled request gets exactly one response")

# ---- model manifest
add("model_manifest", "valid_local_stt_bundle", "valid", MANIFEST)
add("model_manifest", "valid_provider_llm", "valid", {**MANIFEST, "model_id": "provider-llm", "modality": "llm", "artifact": {"provider_managed_digest_unavailable": True, "provider": "user-configured"}, "runtime": "provider_api", "serialization": "provider_managed", "offline_capable": False, "network_hosts": ["api.example.invalid"], "acquisition": "pre_staged", "code_license": "n/a", "weight_license": "proprietary", "commercial_use": "conditional", "commercial_conditions": "Tenant's own provider contract", "effect_classes": ["structured_proposal"], "requirements": {"process_isolation": "subprocess", "network_required": True, "accelerator": "none"}})
add("model_manifest", "invalid_offline_with_hosts", "invalid", mutate(MANIFEST, ["network_hosts"], ["telemetry.example.invalid"]), "offline artifacts declare no hosts")
add("model_manifest", "invalid_measured_without_evidence", "invalid", mutate(MANIFEST, ["languages"], [{"code": "ar", "variety": "Gulf", "support": "measured"}]), "measured language cells cite evidence")
add("model_manifest", "invalid_missing_weight_license", "invalid", mutate(MANIFEST, ["weight_license"], DELETE), "weight license is mandatory")
add("model_manifest", "invalid_provider_api_offline", "invalid", {**MANIFEST, "runtime": "provider_api"}, "provider APIs are never offline")
add("model_manifest", "G-MM-1_provider_managed_digest_offline", "invalid", mutate(MANIFEST, ["artifact"], {"provider_managed_digest_unavailable": True, "provider": "p"}), "no digest means not offline")
add("model_manifest", "G-MM-3_authority_above_evidence", "invalid", mutate(MANIFEST, ["authority_ceiling"], "may_deliver_text"), "models are evidence only")
add("model_manifest", "invalid_auto_download", "invalid", mutate(MANIFEST, ["acquisition"], "automatic_download"), "automatic download is not representable")
add("model_manifest", "invalid_admitted_unknown_commercial", "invalid", mutate(MANIFEST, ["commercial_use"], "unknown"), "an admitted model has a resolved commercial status")
add("model_manifest", "invalid_path_traversal", "invalid", mutate(MANIFEST, ["artifact", "files", 0, "path"], "../evil.bin"), "bundle paths cannot escape")
add("model_manifest", "G-MM-2_duplicate_language_rows", "invalid", mutate(MANIFEST, ["languages"], [{"code": "ar", "variety": "MSA", "support": "documented"}, {"code": "ar", "variety": "MSA", "support": "unsupported"}]), "(code, variety) is unique", layer="runtime")

# ---- consent record
add("consent_record", "valid_active_self", "valid", CONSENT)
add("consent_record", "valid_revoked", "valid", mutate({**CONSENT, "relationship": "consenting_third_party", "status": "revoked", "revoked_at": "2026-11-08T10:00:00Z", "consent_epoch": 2}, ["attestation", "issuer"], {"kind": "consent_service", "key_id": "consent-svc:key-1"}) | {"attestation": {**CONSENT["attestation"], "issuer": {"kind": "consent_service", "key_id": "consent-svc:key-1"}, "signature": {**SIGNATURE, "key_id": "consent-svc:key-1"}}})
add("consent_record", "invalid_revoked_without_time", "invalid", {**CONSENT, "status": "revoked"}, "revocation is timestamped")
add("consent_record", "invalid_active_with_revoked_at", "invalid", {**CONSENT, "revoked_at": "2026-11-08T10:00:00Z"}, "revoked consent is never active")
add("consent_record", "invalid_no_evidence", "invalid", mutate(CONSENT, ["evidence_digest"], DELETE), "evidence digest required")
add("consent_record", "G-CON-1_non_date", "invalid", mutate(CONSENT, ["valid_from"], "not-a-date-at-all"), "dates are RFC 3339 UTC")
add("consent_record", "G-CON-2_expired_without_valid_until", "invalid", {**CONSENT, "status": "expired"}, "expiry needs valid_until")
add("consent_record", "invalid_personal_display_name", "invalid", mutate(CONSENT, ["display_name"], "Jane Doe"), "no personal display data in the contract")
add("consent_record", "invalid_third_party_without_watermark", "invalid", {**CONSENT, "relationship": "consenting_third_party", "watermark_required": False}, "third-party voices are watermarked")
add("consent_record", "G-CON-3_valid_until_before_from", "invalid", {**CONSENT, "valid_until": "2026-01-01T00:00:00Z"}, "valid_until follows valid_from", layer="runtime")

# ---- policy verdict
add("policy_verdict", "valid_ask_money", "valid", VERDICT)
add("policy_verdict", "valid_allow_read_without_rule", "valid", {**VERDICT, "candidate_decision": "ALLOW", "enforced_decision": "ALLOW", "action_class": "read", "rule_ids": [], "layers": [{"source": "base", "decision": "ALLOW"}]})
add("policy_verdict", "valid_undecidable_unattended_deny", "valid", {**VERDICT, "candidate_decision": "UNDECIDABLE", "undecidable_resolution": "DENY", "enforced_decision": "DENY", "human_present": False, "layers": []})
add("policy_verdict", "invalid_allow_money_without_rule", "invalid", {**VERDICT, "candidate_decision": "ALLOW", "enforced_decision": "ALLOW", "rule_ids": [], "layers": [{"source": "base", "decision": "ALLOW"}], "evidence": [{"kind": "model_confidence", "ref": "0.99"}]}, "high-risk ALLOW cites a rule")
add("policy_verdict", "invalid_llm_decision_value", "invalid", mutate(VERDICT, ["enforced_decision"], "APPROVED_BY_MODEL"), "closed decision vocabulary")
add("policy_verdict", "G-POL-3_undecidable_enforced", "invalid", {**VERDICT, "candidate_decision": "UNDECIDABLE", "enforced_decision": "UNDECIDABLE", "layers": []}, "UNDECIDABLE is never the enforced decision")
add("policy_verdict", "invalid_undecidable_unattended_ask", "invalid", {**VERDICT, "candidate_decision": "UNDECIDABLE", "undecidable_resolution": "ASK", "enforced_decision": "ASK", "human_present": False, "layers": []}, "unattended UNDECIDABLE resolves to DENY")
add("policy_verdict", "invalid_enforced_allow_widens_candidate", "invalid", {**VERDICT, "enforced_decision": "ALLOW"}, "enforcement never widens the candidate")
add("policy_verdict", "G-POL-1_voice_render_without_consent", "invalid", {**VERDICT, "candidate_decision": "ALLOW", "enforced_decision": "ALLOW", "action_class": "voice_render", "rule_ids": ["project_voice"], "layers": [{"source": "base", "decision": "ALLOW"}]}, "personal voice render cites consent")
add("policy_verdict", "G-POL-2_text_delivery_confidence_only", "invalid", {**VERDICT, "candidate_decision": "ALLOW", "enforced_decision": "ALLOW", "action_class": "text_delivery", "rule_ids": [], "layers": [{"source": "base", "decision": "ALLOW"}], "evidence": [{"kind": "model_confidence", "ref": "0.97"}]}, "text delivery needs a rule and a target binding")
add("policy_verdict", "invalid_layer_widening", "invalid", {**VERDICT, "layers": [{"source": "base", "decision": "DENY"}, {"source": "tenant", "decision": "ASK"}]}, "layers only narrow and compose to the candidate", layer="runtime")

# ---- provenance
add("provenance_event", "valid_raw_hypothesis", "valid", PROV)
add("provenance_event", "invalid_rewrite_without_parent", "invalid", {**PROV, "kind": "rewrite_suggestion", "components": {"prompt_digest": H}}, "derived text points at its parent")
add("provenance_event", "invalid_raw_without_model", "invalid", mutate(PROV, ["model"], DELETE), "raw hypotheses name their model")
add("provenance_event", "invalid_embedded_media", "invalid", mutate(PROV, ["audio_base64"], "UklGRg=="), "media is never embedded")
add("provenance_event", "G-PROV-1_model_without_digest", "invalid", mutate(PROV, ["model"], {"model_id": "m", "revision": "r1"}), "model digest required")
add("provenance_event", "G-PROV-2_outcome_without_parent", "invalid", {**PROV, "kind": "outcome", "intent_state": "settled"}, "outcomes point at their dispatch")
add("provenance_event", "G-PROV-3_bounded_days_without_days", "invalid", mutate(PROV, ["retention_days"], DELETE), "bounded retention states its days")

# ---- delivery outcome
add("delivery_outcome", "valid_delivered", "valid", DELIVERY)
add("delivery_outcome", "valid_refused_target_changed", "valid", {**DELIVERY, "outcome": "refused", "refusal_reason": "target_changed", "method": "none", "chars_delivered": 0})
add("delivery_outcome", "valid_partial_clipboard", "valid", {**DELIVERY, "outcome": "partial", "method": "send_input_unicode", "chars_delivered": 40, "clipboard": {"used": True, "restored": True, "history_excluded": True}})
add("delivery_outcome", "invalid_delivered_without_revalidation", "invalid", {**DELIVERY, "revalidated_before_delivery": False}, "revalidate before delivery")
add("delivery_outcome", "invalid_foreground_fallback_target", "invalid", mutate(DELIVERY, ["target", "captured_at_activation"], False), "no current-foreground fallback")
add("delivery_outcome", "invalid_refused_with_chars", "invalid", {**DELIVERY, "outcome": "refused", "refusal_reason": "elevated_target", "method": "none", "chars_delivered": 4}, "a refusal delivers nothing")
add("delivery_outcome", "invalid_partial_zero", "invalid", {**DELIVERY, "outcome": "partial", "method": "send_input_unicode", "chars_delivered": 0}, "partial delivers at least one character")
add("delivery_outcome", "G-DEL-3_restored_unused_clipboard", "invalid", mutate(DELIVERY, ["clipboard"], {"used": False, "restored": True}), "an unused clipboard is not restored")
add("delivery_outcome", "G-DEL-4_free_text_start_time", "invalid", mutate(DELIVERY, ["target", "process_instance", "start_generation"], "yesterday"), "process identity is numeric")
add("delivery_outcome", "invalid_clipboard_without_history_exclusion", "invalid", mutate(DELIVERY, ["clipboard"], {"used": True, "restored": True, "history_excluded": False}), "clipboard writes exclude history")
add("delivery_outcome", "G-DEL-1_delivered_exceeds_total", "invalid", {**DELIVERY, "chars_delivered": 130}, "chars_delivered <= chars_total", layer="runtime")
add("delivery_outcome", "G-DEL-2_confirmed_but_short", "invalid", {**DELIVERY, "chars_delivered": 100}, "confirmed means complete", layer="runtime")
add("delivery_outcome", "invalid_stale_epoch_delivered", "invalid", {**DELIVERY, "epoch_at_activation": 2}, "a stale activation epoch must be refused", layer="runtime")
add("delivery_outcome", "valid_stale_epoch_refused", "valid", {**DELIVERY, "epoch_at_activation": 2, "outcome": "refused", "refusal_reason": "stale_epoch", "method": "none", "chars_delivered": 0})

# ---- effect intent
add("effect_intent", "valid_dispatched", "valid", INTENT)
add("effect_intent", "valid_reconciled", "valid", {**INTENT, "state": "reconciled", "reconcile_probe": "GET /refunds?idempotency_key=...", "reconciled_result": "effect_present"})
add("effect_intent", "invalid_unknown_without_probe", "invalid", {**INTENT, "state": "unknown"}, "unknown outcomes need a reconcile probe")
add("effect_intent", "invalid_result_without_reconciled", "invalid", {**INTENT, "reconciled_result": "effect_absent", "reconcile_probe": "x"}, "a reconcile result implies the reconciled state")
add("effect_intent", "invalid_text_delivery_not_an_intent", "invalid", {**INTENT, "action_class": "text_delivery"}, "text delivery is a delivery_outcome, not an effect intent")
add("effect_intent", "valid_studio_export", "valid", {**STUDIO_INTENT, "owner": "studio_export_commit", "action_class": "file_export", "idempotency_key": "project-42:export:chapter-3:v7"})
add("effect_intent", "invalid_studio_money", "invalid", {**STUDIO_INTENT, "owner": "studio_export_commit", "action_class": "money"}, "the export owner only commits files")
add("effect_intent", "invalid_short_idempotency_key", "invalid", mutate(INTENT, ["idempotency_key"], "k1"), "idempotency keys have enough entropy")


# ---- review-driven cases (2026-11-08 independent review)
add("consent_record", "invalid_active_speaker_not_checked", "invalid", mutate(CONSENT, ["speaker_match"], {"method": "human_review", "result": "not_checked"}), "active personal consent requires a speaker match")
add("consent_record", "invalid_missing_reference_digest", "invalid", mutate(CONSENT, ["reference_artifact_digest"], DELETE), "consent binds the exact reference audio")
add("policy_verdict", "valid_voice_render_stock_catalog", "valid", {**VERDICT, "candidate_decision": "ALLOW", "enforced_decision": "ALLOW", "action_class": "voice_render", "rule_ids": ["stock_voice_licensed"], "layers": [{"source": "base", "decision": "ALLOW"}], "stock_voice_catalog_id": "catalog:kokoro:af_heart"})
add("policy_verdict", "valid_ask_confirmed_by_operator", "valid", {**VERDICT, "enforced_decision": "ALLOW", "confirmation": {"confirmer_kind": "operator", "verification_ref": "operator:sara-001", "confirmed_at": "2026-11-08T10:00:00Z"}})
add("policy_verdict", "invalid_ask_confirmed_by_conversation_text", "invalid", {**VERDICT, "enforced_decision": "ALLOW", "confirmation": {"confirmer_kind": "customer_text", "verification_ref": "turn-0000009", "confirmed_at": "2026-11-08T10:00:00Z"}}, "conversation text never confirms an ASK")
add("policy_verdict", "invalid_self_asserted_stock_voice", "invalid", {**VERDICT, "candidate_decision": "ALLOW", "enforced_decision": "ALLOW", "action_class": "voice_render", "rule_ids": ["x"], "layers": [{"source": "base", "decision": "ALLOW"}], "stock_voice": True}, "stock voices come from a catalog, not a flag")
add("model_manifest", "invalid_admitted_pickle", "invalid", mutate(MANIFEST, ["serialization"], "pickle"), "admitted models never use pickle")
add("model_manifest", "invalid_admitted_remote_code", "invalid", mutate(MANIFEST, ["trust_remote_code"], True), "admitted models never run remote code")
add("model_manifest", "invalid_imported_without_provenance", "invalid", mutate(MANIFEST, ["acquisition"], "user_imported"), "user-imported models record provenance")
add("cancellation", "invalid_numeric_start_generation", "invalid", mutate(CANCEL, ["process_instance", "start_generation"], 133700000000000000), "64-bit ids are decimal strings")
add("envelope", "valid_typed_delivery_payload", "valid", {**ENVELOPE, "event": "DeliveryOutcome", "source": {"product": "wisprside", "component": "delivery_owner"}, "payload": DELIVERY})
add("envelope", "invalid_untyped_delivery_payload", "invalid", {**ENVELOPE, "event": "DeliveryOutcome", "source": {"product": "wisprside", "component": "delivery_owner"}, "payload": {"outcome": "delivered"}}, "contract-bearing events carry their contract payload")

# ---- plan review round 1 (#128): focus binding, consent attestation, broker capability
add("delivery_outcome", "invalid_delivered_without_focus_element", "invalid", mutate(DELIVERY, ["target", "focus_element"], DELETE), "delivery binds the focused element")
add("delivery_outcome", "invalid_delivered_into_password_field", "invalid", mutate(DELIVERY, ["target", "focus_element", "is_password"], True), "never deliver into a password field")
add("delivery_outcome", "invalid_delivered_into_read_only_field", "invalid", mutate(DELIVERY, ["target", "focus_element", "is_read_only"], True), "never deliver into a read-only field")
add("delivery_outcome", "invalid_delivered_focus_not_revalidated", "invalid", {**DELIVERY, "focus_revalidated_before_delivery": False}, "same-window focus moves are caught before delivery")
add("delivery_outcome", "valid_refused_focus_moved", "valid", {**DELIVERY, "outcome": "refused", "refusal_reason": "focus_moved", "method": "none", "chars_delivered": 0, "focus_revalidated_before_delivery": False})
add("delivery_outcome", "valid_refused_identity_unreadable_without_focus", "valid", {**mutate(DELIVERY, ["target", "focus_element"], DELETE), "outcome": "refused", "refusal_reason": "identity_unreadable", "method": "none", "chars_delivered": 0})
add("consent_record", "invalid_missing_attestation", "invalid", mutate(CONSENT, ["attestation"], DELETE), "consent is authenticated, not self-asserted")
add("consent_record", "invalid_active_statement_mismatch", "invalid", mutate(CONSENT, ["attestation", "statement", "transcript_match"], "mismatch"), "the statement must say the consent script")
add("consent_record", "invalid_active_operator_not_confirmed", "invalid", mutate(CONSENT, ["attestation", "statement", "operator_confirmed"], False), "a human operator confirms the statement")
add("consent_record", "invalid_statement_imported_not_live", "invalid", mutate(CONSENT, ["attestation", "statement", "live_capture"], False), "consent statements are captured live")
add("consent_record", "invalid_statement_without_challenge", "invalid", mutate(CONSENT, ["attestation", "statement", "challenge_digest"], DELETE), "a capture-time challenge defeats replayed or spliced statements")
COMMERCIAL = {**CONSENT, "purposes": ["commercial"], "attestation": {**CONSENT["attestation"], "issuer": {"kind": "consent_service", "key_id": "consent-svc:key-1"}, "signature": {**SIGNATURE, "key_id": "consent-svc:key-1"}}}
add("consent_record", "valid_commercial_consent_service", "valid", COMMERCIAL)
add("consent_record", "invalid_commercial_operator_key", "invalid", mutate(COMMERCIAL, ["attestation", "issuer", "kind"], "studio_operator"), "commercial consent needs the consent-service key")
add("consent_record", "invalid_commercial_without_watermark", "invalid", {**COMMERCIAL, "watermark_required": False}, "commercial voices are watermarked")
add("consent_record", "invalid_written_consent_method", "invalid", mutate(CONSENT, ["attestation", "identity_check"], "signed_written_consent"), "only live identity checks with a live statement")
for label, path, value in (("evidence_swapped", ["evidence_digest"], "sha256:" + "7" * 64),
                           ("speaker_evidence_swapped", ["speaker_match", "evidence_digest"], "sha256:" + "8" * 64),
                           ("identity_check_relabelled", ["attestation", "identity_check"], "live_video_id_check"),
                           ("script_swapped", ["attestation", "statement", "script_id"], "voice-consent@2"),
                           ("challenge_swapped", ["attestation", "statement", "challenge_digest"], "sha256:" + "6" * 64),
                           ("issued_at_moved", ["attestation", "issued_at"], "2026-11-07T00:00:00Z")):
    add("consent_record", f"invalid_{label}_after_attestation", "invalid", mutate(CONSENT, path, value), "every attested field is signed", layer="runtime", keep_attestation=True)
add("consent_record", "invalid_signature_key_differs_from_issuer", "invalid", mutate(CONSENT, ["attestation", "signature", "key_id"], "op-key:other-007"), "the signing key is the issuer key", layer="runtime")
add("consent_record", "invalid_attestation_wrong_alg", "invalid", mutate(CONSENT, ["attestation", "signature", "alg"], "none"), "attestations are Ed25519-signed")
add("consent_record", "invalid_purposes_widened_after_attestation", "invalid", {**CONSENT, "purposes": ["personal", "internal_evaluation"]}, "attested fields cannot change after signing", layer="runtime", keep_attestation=True)
add("consent_record", "invalid_reference_swapped_after_attestation", "invalid", {**CONSENT, "reference_artifact_digest": "sha256:" + "f" * 64}, "the attested reference audio cannot be swapped", layer="runtime", keep_attestation=True)
add("effect_intent", "invalid_broker_intent_without_capability", "invalid", mutate(INTENT, ["capability"], DELETE), "consequential broker calls need a capability")
add("effect_intent", "invalid_capability_reusable", "invalid", mutate(INTENT, ["capability", "single_use"], False), "capabilities are single-use")
add("effect_intent", "invalid_capability_tool_substituted", "invalid", mutate(INTENT, ["dispatch", "tool"], "refunds.void"), "the capability binds the exact tool", layer="runtime")
add("effect_intent", "invalid_capability_args_substituted", "invalid", mutate(INTENT, ["dispatch", "args_digest"], "sha256:" + "9" * 64), "the capability binds the exact arguments", layer="runtime")
add("effect_intent", "invalid_capability_ttl_over_60s", "invalid", mutate(INTENT, ["capability", "expires_at"], "2026-11-08T10:05:00Z"), "capabilities live at most 60 seconds", layer="runtime")
add("effect_intent", "invalid_capability_expires_before_issue", "invalid", mutate(INTENT, ["capability", "expires_at"], "2026-11-08T09:59:00Z"), "expiry follows issue", layer="runtime")

ALLOW_MONEY = {**VERDICT, "verdict_id": "verdict-0002", "candidate_decision": "ALLOW", "enforced_decision": "ALLOW", "layers": [{"source": "base", "decision": "ALLOW"}]}
BUNDLES = [
    {"name": "valid_intent_bound_to_allow_verdict", "expect": "valid", "intents": [INTENT], "verdicts": [ALLOW_MONEY]},
    {"name": "invalid_duplicate_open_intent_same_key", "expect": "invalid", "intents": [INTENT, {**INTENT, "intent_id": "int-0000003"}], "verdicts": [ALLOW_MONEY], "invariant": "one non-terminal intent per (principal, owner, key)"},
    {"name": "invalid_intent_verdict_class_mismatch", "expect": "invalid", "intents": [INTENT], "verdicts": [{**ALLOW_MONEY, "action_class": "read", "rule_ids": []}], "invariant": "verdict class must match the intent"},
    {"name": "invalid_intent_on_ask_verdict", "expect": "invalid", "intents": [INTENT], "verdicts": [{**VERDICT, "verdict_id": "verdict-0002"}], "invariant": "dispatch needs an enforced ALLOW"},
    {"name": "valid_two_intents_distinct_capabilities", "expect": "valid", "verdicts": [ALLOW_MONEY],
     "intents": [INTENT, mutate(mutate({**INTENT, "intent_id": "int-0000004", "idempotency_key": "acme:refund:order-4822:v1"}, ["capability", "nonce"], "capN0nce_zyxwvutsrq9876"), ["capability", "token_id"], "cap-00000002")]},
    {"name": "invalid_capability_nonce_replayed", "expect": "invalid", "verdicts": [ALLOW_MONEY], "invariant": "a capability nonce is consumed on first use",
     "intents": [INTENT, {**INTENT, "intent_id": "int-0000004", "idempotency_key": "acme:refund:order-4822:v1"}]},
]

SEQUENCES = [
    {"machine": "effect_intent", "name": "pending_dispatched_settled", "states": ["pending", "dispatched", "settled"], "expect": "valid"},
    {"machine": "effect_intent", "name": "crash_after_dispatch_reconciled", "states": ["pending", "dispatched", "unknown", "reconciled"], "expect": "valid"},
    {"machine": "effect_intent", "name": "download_settles_from_pending", "states": ["pending", "settled"], "expect": "valid"},
    {"machine": "effect_intent", "name": "abandoned_after_dispatch", "states": ["pending", "dispatched", "abandoned"], "expect": "invalid"},
    {"machine": "effect_intent", "name": "retry_after_unknown", "states": ["pending", "dispatched", "unknown", "dispatched"], "expect": "invalid"},
    {"machine": "effect_intent", "name": "settled_reopened", "states": ["pending", "settled", "pending"], "expect": "invalid"},
    {"machine": "cancellation", "name": "ack_then_observed", "states": ["requested", "acknowledged", "observed_stopped"], "expect": "valid"},
    {"machine": "cancellation", "name": "unconfirmed_then_failed", "states": ["requested", "acknowledged", "stopped_unconfirmed", "failed"], "expect": "valid"},
    {"machine": "cancellation", "name": "stopped_then_reack", "states": ["requested", "observed_stopped", "acknowledged"], "expect": "invalid"},
    {"machine": "cancellation", "name": "does_not_start_acknowledged", "states": ["acknowledged", "observed_stopped"], "expect": "invalid"},
]

out = pathlib.Path(__file__).resolve().parent / "cases.json"
out.write_text(json.dumps({"description": __doc__.strip().splitlines()[0], "cases": cases, "sequences": SEQUENCES, "bundles": BUNDLES}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(f"wrote {len(cases)} cases and {len(SEQUENCES)} sequences to {out.name}")
