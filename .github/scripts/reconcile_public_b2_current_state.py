from __future__ import annotations

from pathlib import Path

PATH = Path("docs/canonical/CURRENT_STATE.md")
text = PATH.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one occurrence, found {count}: {old!r}")
    text = text.replace(old, new, 1)


merge_anchor = (
    "**000B2 participant-material freeze merge:** "
    "`66cca406e69eda33dfd6e0a2adf59ea328eda1c6`  \n"
)
replace_once(
    merge_anchor,
    merge_anchor
    + "**000B2 public-corpus methodology merge:** "
    "`cfb883311c1acb45cb8422ab6b2c02443dc1b62c`  \n",
)

replace_once(
    "**Blocked successor:** `000B2-unbiased-stt-bakeoff` — `BLOCKED_EXTERNAL`  \n",
    "**Historical private successor:** `000B2-unbiased-stt-bakeoff` — "
    "`BLOCKED_EXTERNAL`  \n"
    "**Active public B2 execution lane:** `000B2-public-corpus-bakeoff` — "
    "`CANONICAL`, execution not started  \n"
    "**Public B2 primary decoding:** `NOT_STARTED`  \n",
)

replace_once(
    "## B2 blocked successor\n\n"
    "`000B2-unbiased-stt-bakeoff` remains `BLOCKED_EXTERNAL`, not `READY`.\n",
    "## Canonical public B2 methodology proof\n\n"
    "PR #28 canonically established the separate public-corpus successor as squash merge "
    "`cfb883311c1acb45cb8422ab6b2c02443dc1b62c` from exact base "
    "`c54e09a2d1cca5929bb7cd5571e84ad9698d4f73`. The merge tree is "
    "`241709f190778a359af018b734314820f4ce8ce1`, the commit has exactly one parent, "
    "and GitHub signature verification is `valid`. The reviewed PR head was "
    "`875b0e4be76e8fc0eb753af189255b38ce3dc7ca`, covering exactly 12 changed paths.\n\n"
    "All six applicable exact-head workflows succeeded before merge, and all six applicable "
    "push workflows succeeded on the canonical merge SHA. Independent CodeRabbit review run "
    "`ed2b90b4-c50b-4b26-9283-b58975f448d5` subsequently completed on the exact base/head "
    "and all 12 paths with no actionable comments. The review completed at "
    "`2026-09-02T19:06:58Z` (status success at `2026-09-02T19:07:00Z`), after the merge at "
    "`2026-09-02T19:02:21Z`. It is therefore post-merge independent semantic evidence and "
    "must not be represented as a pre-merge review. No public B2 archive materialization, "
    "subset freeze, candidate decoding, comparative ranking, or product selection began before "
    "that review completed.\n\n"
    "The amendment preserves the historical private lane and its evidence exactly. It does not "
    "establish participant consent, private human corpus acceptance, human developer-speech "
    "accuracy, general STT superiority, accent/cadence coverage, Arabic support, a production "
    "speech winner, or product-code authority.\n\n"
    "## Historical private B2 lane remains blocked\n\n"
    "`000B2-unbiased-stt-bakeoff` remains `BLOCKED_EXTERNAL`, not `READY`. The blockers below "
    "apply to that historical private participant/media lane only and do not authorize or "
    "describe the separate public-corpus execution lane.\n",
)

public_section = """## Active public B2 execution lane

`000B2-public-corpus-bakeoff` is now the canonical active B2 execution methodology, but execution has not started. The lane uses public LibriSpeech SLR12 human read-English audio only for a bounded P0 baseline. It does not convert public audiobook speech into human developer-speech evidence.

Execution must remain ordered and fail closed: B2P01 source/license/checksum freeze; B2P02 real archive materialization and actual byte-derived SHA-256 capture; B2P03 deterministic candidate-independent subset selection; B2P04 subset manifest freeze; B2P05 six-cell candidate revalidation; B2P06 attempt-bound FFmpeg `9.0.1` capture; B2P07 attempt-bound environment/hardware evidence; and B2P08 final pre-decode attempt freeze with `primary_decoding_started=false`. Comparative C0 decode may begin only after all eight preparation tasks are canonical and satisfied.

P0 claims remain bounded to the exact frozen public ordinary read-English subset. D0 remains optional, synthetic, and `DIAGNOSTIC_ONLY`; it may be `NOT_RUN` and can never become human developer-speech evidence. `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT` remains mandatory. No Rust product code, Cargo workspace, permanent STT integration, ACP production client, PTY adapter, TUI, installer, or release is authorized before `000G` selects and independently qualifies the first bounded implementation Grain.

"""
replace_once("## What is established\n", public_section + "## What is established\n")

replace_once(
    "- explicit remaining B2 external/attempt-time readiness blockers.\n",
    "- the historical private B2 lane remains `BLOCKED_EXTERNAL` without participant/media "
    "authority;\n"
    "- the separate public B2 methodology is canonical, with execution still unstarted and "
    "preparation tasks B2P01–B2P08 still outstanding.\n",
)

replace_once(
    "Verified 000A, verified 000B1, canonical B2 entry preparation, canonical B2 authority "
    "structure, and canonical participant policy/materials do not weaken this gate.\n",
    "Verified 000A, verified 000B1, canonical B2 entry preparation, canonical B2 authority "
    "structure, canonical participant policy/materials, and the canonical public B2 methodology "
    "do not weaken this gate.\n",
)

old_next = (
    "Preserve B2 as `BLOCKED_EXTERNAL`. Use the exact frozen participant policy and "
    "participant-facing materials in the real external consent process, establish independently "
    "genuine participant/media authority, and collect the authorized frozen human developer-speech "
    "corpus under that authority. Repository structure, policy, and templates are prepared, but "
    "none is consent. Only then prepare a separately reviewable B2 attempt that captures "
    "preprocessing and execution-environment evidence before primary decoding, freezes the final "
    "manifest, and rechecks readiness from canonical `main`. If those gates cannot be satisfied, "
    "preserve the block rather than substitute synthetic primary evidence or prematurely advance "
    "B3/B4."
)
new_next = (
    "Keep the historical private `000B2-unbiased-stt-bakeoff` lane `BLOCKED_EXTERNAL` unless "
    "genuine participant/media authority is independently established. For the separate canonical "
    "`000B2-public-corpus-bakeoff` lane, execute only in strict task order beginning with B2P01. "
    "Reverify and freeze the authoritative OpenSLR SLR12 source, license, and official checksums "
    "before materialization; then obtain the real archive bytes and derive their actual SHA-256 "
    "values before any subset freeze or candidate decoding. Preserve "
    "`primary_decoding_started=false` through B2P08, keep D0 optional and `DIAGNOSTIC_ONLY`, and "
    "do not advance B3/B4 until canonical B2 evidence supports it."
)
replace_once(old_next, new_next)

PATH.write_text(text, encoding="utf-8")
