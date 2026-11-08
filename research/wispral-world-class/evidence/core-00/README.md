# CORE-00 evidence

This is the evidence for Grain `CORE-00` (Specification 000F, packet `CORE-00` in `research/wispral-world-class/packets.json`).

## Files

| File | What it is |
| --- | --- |
| [`anchors.json`](anchors.json) | 57 anchors, each `repo@sha:path`. Some carry a recorded expectation: a SHA-256 or blob prefix from the earlier research reports, or a required substring such as `FSL-1.1-MIT`. |
| [`verify_core00_anchors.py`](verify_core00_anchors.py) | The verifier. It follows the pattern of PR #125's `verify_transplant_pins.py` and only reads. |
| [`runs/verify_core00_anchors.txt`](runs/verify_core00_anchors.txt) | Its output on 2026-11-08: `ANCHORS=57 PASS=57 FAIL=0`, `CORE00_ANCHORS=PASS`, and the declared licence of each repository at its pin. |

## Reproduce

Run with an authenticated `gh`, because `TheHalfMoon/Sentrdel` is private:

```
python -I research/wispral-world-class/evidence/core-00/verify_core00_anchors.py research/wispral-world-class/evidence/core-00/anchors.json
```

## Observation

The verifier takes bytes from the stored git blob, not from the contents endpoint. For `TheHalfMoon/Yamakan@c1786105:NOTICE`, the contents endpoint served 3,201 bytes, while the tree's blob `5ec2ef13…` is 3,186 bytes, and only the stored blob hashes to the tree's id. The first run of the verifier used the contents endpoint and reported that anchor as a blob mismatch. After the switch to the stored blob, all 57 anchors pass. Both runs are described here; the committed output is the second.

## Readiness of CORE-00 (rules of the Platform frontier section in `specs/CURRENT.md`)

| Rule | Status |
| --- | --- |
| Dependencies canonical | F merged as `b6c8507c8a75c11c9260965dda1710c4ba255417` on `main` |
| Pins re-verified | 57 of 57 anchors pass at their pinned commits |
| Evidence outside product paths | Every change is under `research/wispral-world-class/` or `specs/000F-provenance-intake/` |
| Checks named | `verify-b2r16-freeze`, the only workflow that runs on every pull request; no B2 path filter matches these paths. Fresh-context review plus the founder's merge approval (packet CORE-00 CI gates). |
