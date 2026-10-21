"""Independent Git-object mutation fixtures; no frozen working file is edited."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

SPEC = importlib.util.spec_from_file_location("preservation", Path(__file__).with_name("verify_b2r16_preservation.py"))
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def candidate_with(file, mode="modify", base=None):
    root = CHECK.ROOT
    base = base or CHECK.git(root, "rev-parse", "HEAD").decode().strip()
    original = CHECK.git(root, "show", f"{base}:{file}")
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
        else:
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

    def test_unchanged_main_and_original_plan(self):
        for candidate in ["edacdf7504302cc91ff7138bc6ac2d391e4df1f4", "f36338138f4b4a872b05393b5cab03856dd7bf8e"]:
            with self.subTest(candidate=candidate):
                CHECK.verify_candidate(CHECK.ROOT, candidate)

    def test_historical_stdout_unchanged(self):
        text = CHECK.historical_proof(CHECK.ROOT)
        self.assertEqual(text, "B2R16_ATTEMPT_003_FREEZE=PASS\nB2R16_FREEZE_DIGEST=b92d0a88bb50ebde517f560878a26d0ef796abdaf931278f5bc43e372ff1ac8d\nATTEMPT_003_FROZEN_EVIDENCE=YES\nATTEMPT_003_CANDIDATE_DECODING_STARTED_AT_FREEZE=NO\nATTEMPT_003_PRIMARY_DECODING_STARTED_AT_FREEZE=NO\nATTEMPT_003_SCORING_PERFORMED_AT_FREEZE=NO\nHUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT\n")

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

    def test_candidate_identity_rejects_refs_and_options(self):
        for value in ["HEAD", "--help", "0" * 40, "f363381", "f36338138f4b4a872b05393b5cab03856dd7bf8e\n"]:
            with self.subTest(value=value):
                with self.assertRaises(CHECK.PreservationError):
                    CHECK.verify_candidate(CHECK.ROOT, value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
