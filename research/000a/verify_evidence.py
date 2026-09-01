#!/usr/bin/env python3
"""Deterministically verify committed Specification 000A evidence against its matrix.

This verifier is deliberately separate from the ACP probe. It does not contact an
agent or provider. It fails closed when the committed narrative/matrix drifts from
the raw sanitized traces or when common credential-like patterns appear.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/research/acp/evidence/000a-attempt-001"
MATRIX_PATH = ROOT / "docs/research/acp/capability-matrix.json"
MANIFEST_PATH = EVIDENCE / "manifest.json"

ALLOWED_STATES = {
    "OBSERVED",
    "DOCUMENTED_NOT_OBSERVED",
    "UNSUPPORTED",
    "NOT_TESTED",
    "BLOCKED_EXTERNAL",
    "UNKNOWN",
}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{10,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{10,}", re.IGNORECASE),
    re.compile(
        r"(?:api[_-]?key|token)\s*[=:]\s*[\"']?[A-Za-z0-9._-]{12,}",
        re.IGNORECASE,
    ),
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def state(matrix: dict[str, Any], agent: str, field: str) -> str:
    value = matrix["agents"][agent][field]["state"]
    require(value in ALLOWED_STATES, f"invalid evidence state {agent}.{field}: {value}")
    return value


def scan_secrets(paths: list[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            require(match is None, f"credential-like pattern in {path}: {pattern.pattern}")


def verify_gemini(raw: dict[str, Any], matrix: dict[str, Any]) -> None:
    require(raw["agent_id"] == "gemini", "Gemini evidence agent id mismatch")
    require(raw["protocol_version_requested"] == 1, "Gemini requested protocol mismatch")
    require(raw["outcomes"]["initialize"] == "SUCCESS", "Gemini initialize evidence drift")
    require(state(matrix, "gemini", "initialize") == "OBSERVED", "Gemini initialize matrix drift")
    require(raw["initialize_result"]["protocolVersion"] == 1, "Gemini negotiated protocol mismatch")
    require(raw["initialize_result"]["agentInfo"]["version"] == "0.57.0", "Gemini version drift")
    require(raw["outcomes"]["session_new"] == "AUTH_REQUIRED", "Gemini session/new evidence drift")
    require(state(matrix, "gemini", "session_new") == "BLOCKED_EXTERNAL", "Gemini session/new matrix drift")
    require(raw["outcomes"]["session_list"] == "METHOD_NOT_FOUND", "Gemini session/list evidence drift")
    require(state(matrix, "gemini", "session_list") == "UNSUPPORTED", "Gemini session/list matrix drift")
    require(raw["initialize_result"]["agentCapabilities"]["loadSession"] is True, "Gemini loadSession advertisement drift")
    require(state(matrix, "gemini", "load_session_advertised") == "OBSERVED", "Gemini loadSession matrix drift")
    require(state(matrix, "gemini", "cancellation_behavior") == "NOT_TESTED", "Gemini cancellation overclaim")
    require(state(matrix, "gemini", "permission_request_behavior") == "NOT_TESTED", "Gemini permission overclaim")


def verify_codex(raw: dict[str, Any], matrix: dict[str, Any]) -> None:
    require(raw["agent_id"] == "codex-acp", "Codex evidence agent id mismatch")
    require(raw["protocol_version_requested"] == 1, "Codex requested protocol mismatch")
    require(raw["outcomes"]["initialize"] == "SUCCESS", "Codex initialize evidence drift")
    require(state(matrix, "codex-acp", "initialize") == "OBSERVED", "Codex initialize matrix drift")
    require(raw["initialize_result"]["protocolVersion"] == 1, "Codex negotiated protocol mismatch")
    require(raw["initialize_result"]["agentInfo"]["version"] == "1.7.0", "Codex version drift")
    require(raw["outcomes"]["session_new"] == "AUTH_REQUIRED", "Codex session/new evidence drift")
    require(state(matrix, "codex-acp", "session_new") == "BLOCKED_EXTERNAL", "Codex session/new matrix drift")
    require(raw["outcomes"]["session_list"] == "AUTH_REQUIRED", "Codex session/list evidence drift")
    require(state(matrix, "codex-acp", "session_list") == "BLOCKED_EXTERNAL", "Codex session/list matrix drift")
    capabilities = raw["initialize_result"]["agentCapabilities"]["sessionCapabilities"]
    require("list" in capabilities, "Codex session/list advertisement missing")
    require("resume" in capabilities, "Codex session/resume advertisement missing")
    require(raw["initialize_result"]["_meta"]["steering"]["supported"] is True, "Codex steering advertisement drift")
    require(state(matrix, "codex-acp", "steering_advertised") == "OBSERVED", "Codex steering matrix drift")
    require(state(matrix, "codex-acp", "steering_behavior") == "NOT_TESTED", "Codex steering behavior overclaim")
    require(state(matrix, "codex-acp", "cancellation_behavior") == "NOT_TESTED", "Codex cancellation overclaim")
    require(state(matrix, "codex-acp", "permission_request_behavior") == "NOT_TESTED", "Codex permission overclaim")


def main() -> int:
    matrix = load(MATRIX_PATH)
    manifest = load(MANIFEST_PATH)
    gemini_path = EVIDENCE / "gemini-probe.json"
    codex_path = EVIDENCE / "codex-acp-probe.json"
    gemini = load(gemini_path)
    codex = load(codex_path)

    require(set(matrix["allowed_evidence_states"]) == ALLOWED_STATES, "matrix evidence vocabulary drift")
    require(set(matrix["agents"]) == {"gemini", "codex-acp"}, "untested agent entered capability matrix")
    require(matrix["recommendation"]["classification"] == "PARTIAL", "recommendation drift")
    require(matrix["recommendation"]["confidence"] == "MODERATE", "recommendation confidence drift")

    verify_gemini(gemini, matrix)
    verify_codex(codex, matrix)

    fixture_digest = manifest["fixture"]["tree_sha256"]
    require(gemini["fixture"]["tree_sha256"] == fixture_digest, "Gemini fixture digest mismatch")
    require(codex["fixture"]["tree_sha256"] == fixture_digest, "Codex fixture digest mismatch")

    require(manifest["wispral"]["workflow_conclusion"] == "success", "manifest workflow conclusion drift")
    require(manifest["artifacts"]["gemini"]["package"] == "@google/gemini-cli@0.57.0", "Gemini package pin drift")
    require(manifest["artifacts"]["codex-acp"]["package"] == "@agentclientprotocol/codex-acp@1.7.0", "Codex package pin drift")

    scan_secrets([gemini_path, codex_path, MANIFEST_PATH, MATRIX_PATH])

    print("000A evidence verification: PASS")
    print("agents: gemini, codex-acp")
    print("recommendation: PARTIAL / MODERATE")
    print(f"fixture_sha256: {fixture_digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"000A evidence verification: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
