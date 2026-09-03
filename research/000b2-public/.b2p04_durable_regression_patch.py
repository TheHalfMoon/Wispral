from pathlib import Path

path = Path("research/000b2-public/verify_subset_freeze.py")
text = path.read_text(encoding="utf-8")

anchor = '''    print("B2P04_COMMITTED_MANIFEST=VALID")


def main() -> None:
    """Run all offline B2P04 structural/adversarial gates."""'''
replacement = '''    print("B2P04_COMMITTED_MANIFEST=VALID")


def verify_manifest_presence_phase_regression() -> None:
    """Require absent-manifest handling to differ only by the verified authority phase."""
    global MANIFEST_PATH
    original_manifest_path = MANIFEST_PATH
    with tempfile.TemporaryDirectory() as temporary:
        MANIFEST_PATH = Path(temporary) / "missing-subset-manifest.json"
        try:
            try:
                verify_manifest("B2P04")
            except SystemExit as error:
                require(
                    "canonical B2P04 reconciliation requires the committed subset manifest" in str(error),
                    "canonical missing-manifest rejection emitted the wrong failure",
                )
            else:
                raise SystemExit(
                    "B2P04_FREEZE_VERIFIER=FAIL: reconciled B2P04 accepted a missing committed manifest"
                )

            verify_manifest("B2P03")
        finally:
            MANIFEST_PATH = original_manifest_path

    print("B2P04_RECONCILED_MISSING_MANIFEST_REJECTION=PASS")
    print("B2P03_ABSENT_MANIFEST_PROBE=PASS")


def main() -> None:
    """Run all offline B2P04 structural/adversarial gates."""'''
if text.count(anchor) != 1:
    raise SystemExit(f"B2P04_DURABLE_MANIFEST_REGRESSION=FAIL: insertion anchor count {text.count(anchor)}")
text = text.replace(anchor, replacement)

call_anchor = '''    verify_safe_extraction()
    authority_phase = verify_current_authority()
    verify_manifest(authority_phase)
    print("B2P04_FREEZE_VERIFIER=PASS")'''
call_replacement = '''    verify_safe_extraction()
    verify_manifest_presence_phase_regression()
    authority_phase = verify_current_authority()
    verify_manifest(authority_phase)
    print("B2P04_FREEZE_VERIFIER=PASS")'''
if text.count(call_anchor) != 1:
    raise SystemExit(f"B2P04_DURABLE_MANIFEST_REGRESSION=FAIL: call anchor count {text.count(call_anchor)}")

path.write_text(text.replace(call_anchor, call_replacement), encoding="utf-8")
print("B2P04_DURABLE_MANIFEST_REGRESSION=APPLIED")
