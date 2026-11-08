"""Independent Git-object mutation fixtures; no frozen working file is edited."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("preservation", Path(__file__).with_name("verify_b2r16_preservation.py"))
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)

MANIFEST = "research/000b2-public/b2r16-attempt-003-manifest.json"
# Every B2R16 candidate the original freeze gate evaluated before the freeze merge
# (`000B2 Public Corpus B2R16 Freeze` runs of 2026-09-08 and 2026-09-09), with the
# verdict the canonical frozen original verifier gives. The four candidates the gate
# rejected stay rejected, and the qualified head passes. Five superseded heads
# passed only under their own, superseded verifier bytes bound to the superseded
# authority base 483484023087; the frozen verifier rejects them.
IN_CLASS_CORPUS = {
    "7db0ffbbc9245bbf7271f6827f55380d03d8946a": False,
    "adbc6f996179acadac31ba64986950d004855427": False,
    "9c5d475e9c86c1df2b1650e4fb4370cdecf73a77": False,
    "049e2e9b7fa32e296968df24436eb601a0749ad5": False,
    "d9528e3a6abfbe589593a332b4ec48d2686e4144": False,
    "e1525036e619fb49863a1c2f707d5ed29ff3289b": False,
    "17b526448bd3534968c459cc27f80f2fab6775d8": False,
    "ee3b419bc2b5c32bc72ced1c777a07ebfc6f85f4": False,
    "0b8c70a922cafd759da3d5b8d26e996e2daec929": False,
    "ac9f7ce993aec33e6c6436cce4efd85394a97f35": True,
}
PREVIOUSLY_REJECTED = ("adbc6f996179acadac31ba64986950d004855427", "9c5d475e9c86c1df2b1650e4fb4370cdecf73a77",
                       "049e2e9b7fa32e296968df24436eb601a0749ad5", "0b8c70a922cafd759da3d5b8d26e996e2daec929")


def candidate_with(file, mode="modify", base=None, payload=None):
    root = CHECK.ROOT
    base = base or CHECK.git(root, "rev-parse", "HEAD").decode().strip()
    # Build trees through an isolated index; avoid editing any checkout file.
    import tempfile
    with tempfile.TemporaryDirectory(prefix=".b2r16-index-", dir=root.parent) as temp:
        assert Path(temp).resolve().parent == root.parent.resolve()
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(temp) / "index"),
               "GIT_AUTHOR_NAME": "Synthetic fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
               "GIT_COMMITTER_NAME": "Synthetic fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
        def run(*args, data=None):
            return subprocess.run(["git", "-C", str(root), *args], input=data, env=env,
                                  check=True, capture_output=True, timeout=30).stdout.decode().strip()
        run("read-tree", base)
        if mode == "delete":
            run("update-index", "--force-remove", "--", file)
        elif mode == "gitlink":
            run("update-index", "--add", "--cacheinfo", "160000", base, file)
        elif mode == "tree":
            run("update-index", "--force-remove", "--", file)
            blob = run("hash-object", "-w", "--stdin", data=b"fixture\n")
            run("update-index", "--add", "--cacheinfo", "100644", blob, file + "/inner")
        else:
            if payload is None:
                original = CHECK.git(root, "show", f"{base}:{file}")
                payload = (CHECK.ROOT / file).read_bytes() if mode == "replacement" else original if mode in ("symlink", "mode") else original + b"\n"
            blob = run("hash-object", "-w", "--stdin", data=payload)
            run("update-index", "--add", "--cacheinfo", "120000" if mode == "symlink" else "100755" if mode == "mode" else "100644", blob, file)
        tree = run("write-tree")
        return run("commit-tree", tree, "-p", base, data=b"Synthetic mutation fixture\n")


class PreservationTests(unittest.TestCase):
    def test_mutable_checker_and_tests_cannot_bypass_unchanged_workflow(self):
        import hashlib
        import re
        import tempfile
        workflow = (CHECK.ROOT / CHECK.WORKFLOW).read_text(encoding="utf-8")
        invocation = next(line.strip().split(" <<")[0].split()[1:] for line in workflow.splitlines() if "<<'PY'" in line)
        block = workflow.split("<<'PY'\n", 1)[1].split("\n          PY", 1)[0]
        code = "\n".join(line[10:] for line in block.splitlines())
        env = {**os.environ}
        for variable in ("CHECKER_SHA256", "TEST_SHA256"):
            env[variable] = re.search(variable + r": ([0-9a-f]{64})", workflow).group(1)
        names = ["verify_b2r16_preservation.py", "test_b2r16_preservation.py"]
        with tempfile.TemporaryDirectory(prefix=".b2r16-preflight-", dir=CHECK.ROOT.parent) as temp:
            root = Path(temp)
            assert root.resolve().parent == CHECK.ROOT.parent.resolve()
            (root / "hashlib.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
            target = root / "research/000b2-public"
            target.mkdir(parents=True)
            for name in names:
                (target / name).write_bytes((CHECK.ROOT / "research/000b2-public" / name).read_bytes())
            good = subprocess.run([sys.executable, *invocation], input=code.encode(), cwd=root, env=env, capture_output=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            for name in names:
                original = (target / name).read_bytes()
                (target / name).write_text("raise SystemExit(0)\n", encoding="utf-8")
                bad = subprocess.run([sys.executable, *invocation], input=code.encode(), cwd=root, env=env, capture_output=True)
                self.assertNotEqual(bad.returncode, 0)
                (target / name).write_bytes(original)

    def test_exact_replacement_workflow_and_its_tampering(self):
        candidate = candidate_with(CHECK.WORKFLOW, "replacement")
        CHECK.verify_candidate(CHECK.ROOT, candidate)
        with self.assertRaises(CHECK.PreservationError):
            CHECK.verify_candidate(CHECK.ROOT, candidate_with(CHECK.WORKFLOW, base=candidate))

    def test_workflow_trust_root_is_base_defined(self):
        workflow = (CHECK.ROOT / CHECK.WORKFLOW).read_text(encoding="utf-8")
        self.assertIn("\n  pull_request_target:\n", workflow)
        self.assertNotIn("\n  pull_request:\n", workflow)
        self.assertEqual(workflow.count("ref: "), 1)
        self.assertIn("ref: ${{ env.TRUSTED_REVISION }}\n", workflow)
        self.assertIn("persist-credentials: false\n", workflow)

    def test_candidate_defined_trigger_rejected(self):
        workflow = (CHECK.ROOT / CHECK.WORKFLOW).read_bytes()
        downgraded = workflow.replace(b"\n  pull_request_target:\n", b"\n  pull_request:\n", 1)
        self.assertNotEqual(downgraded, workflow)
        with self.assertRaises(CHECK.PreservationError):
            CHECK.verify_candidate(CHECK.ROOT, candidate_with(CHECK.WORKFLOW, payload=downgraded))

    def test_exact_original_workflow_restore_rejected(self):
        original = CHECK.git(CHECK.ROOT, "show", f"{CHECK.FROZEN_MERGE}:{CHECK.WORKFLOW}")
        with self.assertRaisesRegex(CHECK.PreservationError, "downgraded to the original identity"):
            CHECK.verify_candidate(CHECK.ROOT, candidate_with(CHECK.WORKFLOW, payload=original))

    def test_branch_predating_replacement_keeps_original_workflow(self):
        # A branch forked before the replacement does not touch the workflow, so a
        # merge keeps the base's replacement; its tree still has the original.
        stale = candidate_with("README.md", base="edacdf7504302cc91ff7138bc6ac2d391e4df1f4")
        CHECK.verify_candidate(CHECK.ROOT, stale)

    def test_workflow_digest_literal_count_and_value(self):
        workflow = (CHECK.ROOT / CHECK.WORKFLOW).read_bytes()
        self.assertTrue(CHECK.approved_workflow(workflow))
        none = workflow.replace(b"CHECKER_SHA256: ", b"CHECKER_DIGEST: ", 1)
        two = workflow + b"# CHECKER_SHA256: " + b"0" * 64 + b"\n"
        literal = workflow.split(b"CHECKER_SHA256: ", 1)[1][:64]
        wrong = workflow.replace(literal, b"f" * 64, 1)
        for label, payload in (("none", none), ("two", two), ("wrong", wrong)):
            with self.subTest(literal=label):
                self.assertFalse(CHECK.approved_workflow(payload))
                with self.assertRaisesRegex(CHECK.PreservationError, "Frozen bytes changed"):
                    CHECK.verify_candidate(CHECK.ROOT, candidate_with(CHECK.WORKFLOW, payload=payload))

    def test_oversized_workflow_rejected(self):
        payload = (CHECK.ROOT / CHECK.WORKFLOW).read_bytes() + b"#" * (CHECK.MAX_WORKFLOW_BYTES + 1)
        with self.assertRaisesRegex(CHECK.PreservationError, "size limit"):
            CHECK.verify_candidate(CHECK.ROOT, candidate_with(CHECK.WORKFLOW, payload=payload))

    def test_unchanged_main_history(self):
        # Commits reachable from canonical main after the B2R16 freeze merge.
        for candidate in ["885307429ec8b1aa0fe173169a8c2918714c06b0", "0fd4e2252e485b887af33d404ac589354fdb05ee",
                          "edacdf7504302cc91ff7138bc6ac2d391e4df1f4"]:
            with self.subTest(candidate=candidate):
                CHECK.verify_candidate(CHECK.ROOT, candidate)

    def test_historical_stdout_unchanged(self):
        text = CHECK.historical_proof(CHECK.ROOT)
        self.assertEqual(text, "B2R16_ATTEMPT_003_FREEZE=PASS\nB2R16_FREEZE_DIGEST=b92d0a88bb50ebde517f560878a26d0ef796abdaf931278f5bc43e372ff1ac8d\nATTEMPT_003_FROZEN_EVIDENCE=YES\nATTEMPT_003_CANDIDATE_DECODING_STARTED_AT_FREEZE=NO\nATTEMPT_003_PRIMARY_DECODING_STARTED_AT_FREEZE=NO\nATTEMPT_003_SCORING_PERFORMED_AT_FREEZE=NO\nHUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT\n")

    def test_historical_proof_failure_rejected(self):
        with mock.patch.object(CHECK, "QUALIFIED_HEAD", "edacdf7504302cc91ff7138bc6ac2d391e4df1f4"):
            with self.assertRaisesRegex(CHECK.PreservationError, "Pinned historical verifier failed"):
                CHECK.historical_proof(CHECK.ROOT)

    def test_unexpected_scratch_root_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as elsewhere:
            with mock.patch.object(CHECK.tempfile, "mkdtemp", return_value=elsewhere):
                with self.assertRaisesRegex(CHECK.PreservationError, "scratch root"):
                    CHECK.run_original(CHECK.ROOT, CHECK.QUALIFIED_HEAD)

    def test_every_frozen_path_rejects_byte_change(self):
        for file in CHECK.FROZEN_PATHS:
            with self.subTest(file=file):
                with self.assertRaises(CHECK.PreservationError):
                    CHECK.verify_candidate(CHECK.ROOT, candidate_with(file))

    def test_delete_mode_and_symlink_rejected(self):
        for file in CHECK.FROZEN_PATHS:
            for mode in ["delete", "mode", "symlink"]:
                with self.subTest(file=file, mode=mode):
                    with self.assertRaises(CHECK.PreservationError):
                        CHECK.verify_candidate(CHECK.ROOT, candidate_with(file, mode))

    def test_non_blob_frozen_path_rejected(self):
        for file in (CHECK.WORKFLOW, MANIFEST):
            for mode in ["gitlink", "tree"]:
                with self.subTest(file=file, mode=mode):
                    with self.assertRaisesRegex(CHECK.PreservationError, "type/mode drift"):
                        CHECK.verify_candidate(CHECK.ROOT, candidate_with(file, mode))

    def test_malformed_or_ambiguous_tree_record_rejected(self):
        name = CHECK.WORKFLOW.encode()
        for record in (b"", b"100644 blob " + b"a" * 40 + b"\t" + name + b"\0" + b"100644 blob " + b"b" * 40 + b"\t" + name + b"\0",
                       b"100644 blob\t" + name + b"\0", b"100644 blob " + b"a" * 40 + b"\t\xff\0"):
            with self.subTest(record=record[:24]):
                with mock.patch.object(CHECK, "git", return_value=record):
                    with self.assertRaises(CHECK.PreservationError):
                        CHECK.identity(CHECK.ROOT, CHECK.FROZEN_MERGE, CHECK.WORKFLOW)

    def test_candidate_predating_freeze_is_not_a_preservation_candidate(self):
        with self.assertRaisesRegex(CHECK.PreservationError, "predates the B2R16 freeze merge"):
            CHECK.verify_candidate(CHECK.ROOT, CHECK.QUALIFIED_HEAD)

    def test_candidate_identity_rejects_refs_and_options(self):
        for value in ["HEAD", "--help", "0" * 40, "edacdf7", "edacdf7504302cc91ff7138bc6ac2d391e4df1f4\n"]:
            with self.subTest(value=value):
                with self.assertRaises(CHECK.PreservationError):
                    CHECK.verify_candidate(CHECK.ROOT, value)

    def test_in_class_corpus_verdicts(self):
        for candidate, passes in IN_CLASS_CORPUS.items():
            with self.subTest(candidate=candidate):
                self.assertFalse(CHECK.descends_from_freeze(CHECK.ROOT, candidate))
                result = CHECK.run_original(CHECK.ROOT, candidate)
                self.assertEqual(result.returncode == 0, passes, result.stdout + result.stderr)
        for candidate in PREVIOUSLY_REJECTED:
            self.assertFalse(IN_CLASS_CORPUS[candidate])

    def test_in_class_malformed_candidates_rejected(self):
        extra = candidate_with("research/000b2-public/b2r16-extra.json", "modify", base=CHECK.QUALIFIED_HEAD, payload=b"{}\n")
        manifest = candidate_with(MANIFEST, base=CHECK.QUALIFIED_HEAD)
        for candidate in (extra, manifest):
            with self.subTest(candidate=candidate):
                self.assertNotEqual(CHECK.run_original(CHECK.ROOT, candidate).returncode, 0)
        verifier_link = candidate_with(CHECK.VERIFIER, "symlink", base=CHECK.QUALIFIED_HEAD)
        with self.assertRaisesRegex(CHECK.PreservationError, "type/mode drift"):
            CHECK.run_original(CHECK.ROOT, verifier_link)


if __name__ == "__main__":
    unittest.main(verbosity=2)
