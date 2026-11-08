"""Run the CANDIDATE Wispral contract conformance fixtures.

Usage (from repository root, isolated mode):
    python -I docs/engineering/contracts/run_conformance.py

Requires `jsonschema` (Draft 2020-12). Three layers:
  1. shape   - every schema is valid against the meta-schema and each case matches its expected verdict;
  2. runtime - cross-field invariants JSON Schema cannot express (bounds, date order, uniqueness,
               epoch equality, policy-layer narrowing) applied to shape-valid instances;
  3. sequence - state-machine transitions from transitions/*.json.
Exit code 0 means every case matched. Scope: contract conformance only; not runtime, security or product evidence.
"""

import hashlib
import json
import pathlib
import sys
from datetime import datetime

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = pathlib.Path(__file__).resolve().parent
NAMES = ["envelope", "cancellation", "model_manifest", "consent_record", "policy_verdict", "provenance_event", "delivery_outcome", "effect_intent"]
TERMINAL_INTENT = {"settled", "abandoned", "reconciled"}
ORDER = {"ALLOW": 0, "ASK": 1, "DENY": 2}
BOUND_CONSENT_FIELDS = ("subject_ref", "voice_id", "purposes", "products", "reference_artifact_digest", "valid_from", "valid_until", "consent_epoch")
CAPABILITY_MAX_SECONDS = 60


def ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def bound_digest(record):
    fields = {k: record.get(k) for k in BOUND_CONSENT_FIELDS}
    fields["nonce"] = record["attestation"]["nonce"]
    return "sha256:" + hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def compose(layers):
    """Simplified narrowing composition: DENY absorbs; empty or any UNDECIDABLE (without DENY) is UNDECIDABLE;
    otherwise the most restrictive. Exact Sentrdel semantics are ported with donor test vectors in packet CORE-03."""
    decisions = [layer["decision"] for layer in layers]
    if "DENY" in decisions:
        return "DENY"
    if not decisions or "UNDECIDABLE" in decisions:
        return "UNDECIDABLE"
    return max(decisions, key=ORDER.__getitem__)


def runtime_errors(schema, inst):
    errors = []
    if schema == "delivery_outcome":
        total, done = inst["chars_total"], inst["chars_delivered"]
        if done > total:
            errors.append("chars_delivered exceeds chars_total")
        if inst["outcome"] == "delivered_confirmed" and done != total:
            errors.append("delivered_confirmed requires full delivery")
        if inst["outcome"] == "partial" and not (1 <= done < total):
            errors.append("partial requires 1 <= delivered < total")
        if inst["epoch_at_activation"] != inst["epoch"] and not (inst["outcome"] == "refused" and inst.get("refusal_reason") == "stale_epoch"):
            errors.append("stale activation epoch must be refused as stale_epoch")
    elif schema == "consent_record":
        if "valid_until" in inst and inst["valid_until"] <= inst["valid_from"]:
            errors.append("valid_until must follow valid_from")
        if inst["attestation"]["bound_fields_digest"] != bound_digest(inst):
            errors.append("attested fields changed after attestation (bound_fields_digest mismatch)")
    elif schema == "effect_intent" and "capability" in inst:
        cap, dispatch = inst["capability"], inst.get("dispatch", {})
        if cap["tool"] != dispatch.get("tool") or cap["args_digest"] != dispatch.get("args_digest"):
            errors.append("dispatched tool or arguments differ from the capability")
        lifetime = (ts(cap["expires_at"]) - ts(cap["issued_at"])).total_seconds()
        if not 0 < lifetime <= CAPABILITY_MAX_SECONDS:
            errors.append("capability lifetime must be within (0, 60] seconds")
    elif schema == "model_manifest":
        keys = [(row["code"], row.get("variety")) for row in inst["languages"]]
        if len(keys) != len(set(keys)):
            errors.append("duplicate (code, variety) language rows")
    elif schema == "policy_verdict":
        layers = inst["layers"]
        ranked = [ORDER[layer["decision"]] for layer in layers if layer["decision"] in ORDER]
        if any(later < earlier for earlier, later in zip(ranked, ranked[1:])):
            errors.append("a later policy layer widens an earlier one")
        if compose(layers) != inst["candidate_decision"]:
            errors.append("candidate_decision does not equal the composition of layers")
    return errors


def sequence_ok(table, states):
    if not states or states[0] not in table["initial"]:
        return False
    return all(nxt in table["allowed"][cur] for cur, nxt in zip(states, states[1:]))


def main() -> int:
    schemas = {name: json.loads((HERE / f"{name}.schema.json").read_text(encoding="utf-8")) for name in NAMES}
    registry = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in schemas.values()])
    validators = {}
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        validators[name] = Draft202012Validator(schema, registry=registry)
    tables = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (HERE / "transitions").glob("*.json")}

    fixtures = json.loads((HERE / "fixtures" / "cases.json").read_text(encoding="utf-8"))
    failures, results = [], []
    for case in fixtures["cases"]:
        shape_errors = [e.message for e in validators[case["schema"]].iter_errors(case["instance"])]
        errors = shape_errors or runtime_errors(case["schema"], case["instance"])
        actual = "valid" if not errors else "invalid"
        ok = actual == case["expect"]
        if ok and case["expect"] == "invalid" and case.get("layer") == "runtime" and shape_errors:
            ok = False  # a runtime case must be shape-valid, otherwise it does not test the runtime layer
        if not ok:
            failures.append(case["name"])
        results.append({"schema": case["schema"], "case": case["name"], "layer": case.get("layer", "shape"), "expect": case["expect"], "actual": actual, "ok": ok, "first_error": (errors[0][:160] if errors else None)})

    for seq in fixtures["sequences"]:
        actual = "valid" if sequence_ok(tables[seq["machine"]], seq["states"]) else "invalid"
        ok = actual == seq["expect"]
        if not ok:
            failures.append(seq["name"])
        results.append({"schema": seq["machine"], "case": seq["name"], "layer": "sequence", "expect": seq["expect"], "actual": actual, "ok": ok})

    for b in fixtures.get("bundles", []):
        errors = []
        for i in b["intents"]:
            errors += [e.message for e in validators["effect_intent"].iter_errors(i)]
        for v in b["verdicts"]:
            errors += [e.message for e in validators["policy_verdict"].iter_errors(v)]
        open_keys = {}
        verdicts = {v["verdict_id"]: v for v in b["verdicts"]}
        for i in b["intents"]:
            key = (i["principal_scope_ref"], i["owner"], i["idempotency_key"])
            if i["state"] not in TERMINAL_INTENT:
                open_keys[key] = open_keys.get(key, 0) + 1
            v = verdicts.get(i["verdict_id"])
            if v is None:
                errors.append("intent references an unknown verdict")
            else:
                if v["action_class"] != i["action_class"]:
                    errors.append("verdict action class does not match the intent")
                if v["principal_scope_ref"] != i["principal_scope_ref"]:
                    errors.append("verdict principal does not match the intent")
                if v["enforced_decision"] != "ALLOW":
                    errors.append("intent dispatched without an enforced ALLOW")
        nonces = [i["capability"]["nonce"] for i in b["intents"] if "capability" in i]
        if len(nonces) != len(set(nonces)):
            errors.append("a capability nonce is used more than once")
        for i in b["intents"]:
            errors += runtime_errors("effect_intent", i)
        if any(n > 1 for n in open_keys.values()):
            errors.append("more than one non-terminal intent for the same (principal, owner, key)")
        actual = "valid" if not errors else "invalid"
        ok = actual == b["expect"]
        if not ok:
            failures.append(b["name"])
        results.append({"schema": "bundle", "case": b["name"], "layer": "bundle", "expect": b["expect"], "actual": actual, "ok": ok, "first_error": errors[0][:160] if errors else None})

    per_schema = {n: {"valid": 0, "invalid": 0} for n in NAMES}
    for c in fixtures["cases"]:
        per_schema[c["schema"]][c["expect"]] += 1
    thin = [n for n, v in per_schema.items() if v["valid"] < 1 or v["invalid"] < 2]
    if thin:
        failures.append(f"insufficient fixtures (need >=1 valid and >=2 invalid): {thin}")

    layers = {}
    for r in results:
        layers[r["layer"]] = layers.get(r["layer"], 0) + 1
    print(json.dumps({
        "status": "PASS" if not failures else "FAIL",
        "scope": "Contract conformance only (shape, runtime cross-field, sequence); not runtime, security or product evidence.",
        "schemas": len(NAMES), "cases": len(fixtures["cases"]), "sequences": len(fixtures["sequences"]), "bundles": len(fixtures.get("bundles", [])),
        "per_layer": layers, "per_schema": per_schema, "failures": failures, "results": results,
    }, indent=1, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
