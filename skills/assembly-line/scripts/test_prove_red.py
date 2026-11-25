import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "prove-red.py"
TEST_PATH = "tests/check.py"
PYTHON = shlex.quote(sys.executable)


def load_parse_tap():
    spec = importlib.util.spec_from_file_location("prove_red", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse_tap


class ProveRed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.repo = root / "repo"
        self.repo.mkdir()
        self.marker = root / "marker.json"
        self.spec_path = root / "spec.json"
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "commit.gpgsign", "false")
        self.commit({"lib/code.txt": "base\n", "README.md": "readme\n"}, msg="base")
        self.base = self.rev()

    def tearDown(self):
        for path in self.repo.rglob("*"):
            if path.is_dir():
                os.chmod(path, 0o755)
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def rev(self, ref="HEAD"):
        return self.git("rev-parse", ref).strip()

    def commit(self, files=None, remove=(), msg="change"):
        for rel, content in (files or {}).items():
            target = self.repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            self.git("add", "--", rel)
        for rel in remove:
            self.git("rm", "-q", "--", rel)
        self.git("commit", "-q", "-m", msg)

    def script(self, tap="", code=0, probe=(), extra=""):
        return (
            "import json, os, sys\n"
            f"probe = {list(probe)!r}\n"
            "seen = {p: (open(p).read() if os.path.exists(p) else None) for p in probe}\n"
            f"open({str(self.marker)!r}, 'w').write(json.dumps(seen))\n"
            f"{extra}\n"
            f"sys.stdout.write({tap!r})\n"
            f"sys.exit({code})\n"
        )

    def seen(self):
        return json.loads(self.marker.read_text())

    def snapshot(self):
        files = {
            str(path.relative_to(self.repo)): path.read_text()
            for path in sorted(self.repo.rglob("*"))
            if path.is_file() and ".git" not in path.relative_to(self.repo).parts
        }
        return self.rev(), self.git("status", "--porcelain"), files

    def prove(self, tests=None, spec=None):
        if spec is None:
            spec = {
                "repo": str(self.repo),
                "base": self.base,
                "tests": tests if tests is not None else [
                    {"path": TEST_PATH, "command": f"{PYTHON} {TEST_PATH}"}
                ],
            }
        self.spec_path.write_text(json.dumps(spec))
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.spec_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        report = json.loads(proc.stdout) if proc.stdout.strip() else None
        return proc, report

    def standard_repo(self, test_content):
        self.commit({"lib/code.txt": "changed\n"}, msg="code")
        self.commit({TEST_PATH: test_content}, msg="tests")

    def test_reverts_code_to_base_during_run(self):
        self.standard_repo(self.script(tap="ok 1 - a\n", probe=["lib/code.txt"]))
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(self.seen()["lib/code.txt"], "base\n")

    def test_reports_red_per_tap_test(self):
        self.standard_repo(self.script(tap="not ok 1 - needs code\nnot ok 2 - also needs code\n", code=1))
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        result = report["results"][0]
        self.assertEqual(result["path"], TEST_PATH)
        self.assertEqual(result["exit"], 1)
        self.assertFalse(result["timedOut"])
        self.assertEqual(result["verdict"], "red")
        self.assertEqual(
            result["tests"],
            [
                {"name": "needs code", "verdict": "red"},
                {"name": "also needs code", "verdict": "red"},
            ],
        )
        self.assertEqual(report["weak"], [])

    def test_reports_weak_per_tap_test(self):
        self.standard_repo(self.script(tap="not ok 1 - needs code\nok 2 - holds at base\n", code=1))
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        result = report["results"][0]
        self.assertEqual(
            result["tests"],
            [
                {"name": "needs code", "verdict": "red"},
                {"name": "holds at base", "verdict": "weak"},
            ],
        )
        self.assertEqual(report["weak"], [f"{TEST_PATH} :: holds at base"])

    def test_all_ok_file_is_weak(self):
        self.standard_repo(self.script(tap="ok 1 - holds\n", code=0))
        proc, report = self.prove()
        result = report["results"][0]
        self.assertEqual(result["verdict"], "weak")
        self.assertEqual(result["tests"], [{"name": "holds", "verdict": "weak"}])
        self.assertEqual(report["weak"], [f"{TEST_PATH} :: holds"])

    def test_restores_code_to_head(self):
        self.standard_repo(self.script(tap="not ok 1 - a\n", code=1))
        before = self.snapshot()
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue(report["restored"])
        self.assertIsNone(report["error"])
        self.assertEqual(report["head"], self.rev())
        self.assertEqual(report["base"], self.base)
        self.assertEqual((self.repo / "lib/code.txt").read_text(), "changed\n")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.snapshot(), before)

    def test_code_excludes_tests_and_exclude(self):
        self.commit({"lib/code.txt": "changed\n", "recipes/card.md": "card\n"}, msg="code")
        self.commit({TEST_PATH: self.script(tap="not ok 1 - a\n", code=1)}, msg="tests")
        spec = {
            "repo": str(self.repo),
            "base": self.base,
            "tests": [{"path": TEST_PATH, "command": f"{PYTHON} {TEST_PATH}"}],
            "exclude": ["recipes/card.md"],
        }
        proc, report = self.prove(spec=spec)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(report["code"], ["lib/code.txt"])

    def test_code_is_sorted_diff_paths(self):
        self.commit({"lib/z.txt": "z\n", "lib/code.txt": "changed\n", "lib/a.txt": "a\n"}, msg="code")
        self.commit({TEST_PATH: self.script(tap="not ok 1 - a\n", code=1)}, msg="tests")
        proc, report = self.prove()
        self.assertEqual(report["code"], ["lib/a.txt", "lib/code.txt", "lib/z.txt"])

    def test_added_file_absent_during_run(self):
        self.commit({"lib/new.txt": "new\n"}, msg="code")
        self.commit({TEST_PATH: self.script(tap="not ok 1 - a\n", code=1, probe=["lib/new.txt"])}, msg="tests")
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIsNone(self.seen()["lib/new.txt"])
        self.assertEqual((self.repo / "lib/new.txt").read_text(), "new\n")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_deleted_file_present_during_run(self):
        self.commit({"lib/old.txt": "old\n"}, msg="more base")
        self.base = self.rev()
        self.commit(remove=["lib/old.txt"], msg="code")
        self.commit({TEST_PATH: self.script(tap="not ok 1 - a\n", code=1, probe=["lib/old.txt"])}, msg="tests")
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(self.seen()["lib/old.txt"], "old\n")
        self.assertFalse((self.repo / "lib/old.txt").exists())
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_no_code_files(self):
        self.commit({TEST_PATH: self.script(tap="ok 1 - holds\n", code=0, probe=["lib/code.txt"])}, msg="tests")
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(report["code"], [])
        self.assertEqual(self.seen()["lib/code.txt"], "base\n")
        self.assertEqual(report["weak"], [f"{TEST_PATH} :: holds"])
        self.assertTrue(report["restored"])

    def test_timeout_is_red(self):
        self.standard_repo(self.script(tap="", code=0, extra="import time; time.sleep(30)"))
        spec = {
            "repo": str(self.repo),
            "base": self.base,
            "tests": [{"path": TEST_PATH, "command": f"{PYTHON} {TEST_PATH}"}],
            "timeout": 1,
        }
        proc, report = self.prove(spec=spec)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        result = report["results"][0]
        self.assertEqual(result["verdict"], "red")
        self.assertTrue(result["timedOut"])
        self.assertIsNone(result["exit"])
        self.assertTrue(report["restored"])
        self.assertEqual((self.repo / "lib/code.txt").read_text(), "changed\n")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_no_tap_uses_exit_code(self):
        self.commit({"lib/code.txt": "changed\n"}, msg="code")
        self.commit(
            {
                "tests/green.py": "import sys\nsys.exit(0)\n",
                "tests/broken.py": "import sys\nsys.exit(3)\n",
            },
            msg="tests",
        )
        tests = [
            {"path": "tests/green.py", "command": f"{PYTHON} tests/green.py"},
            {"path": "tests/broken.py", "command": f"{PYTHON} tests/broken.py"},
        ]
        proc, report = self.prove(tests=tests)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        green, broken = report["results"]
        self.assertEqual(green["verdict"], "weak")
        self.assertEqual(green["tests"], [])
        self.assertEqual(broken["verdict"], "red")
        self.assertEqual(broken["exit"], 3)
        self.assertEqual(broken["tests"], [])
        self.assertEqual(report["weak"], ["tests/green.py"])

    def test_parse_tap_skips_suites_and_directives(self):
        parse_tap = load_parse_tap()
        output = (
            "TAP version 13\n"
            "# Subtest: outer\n"
            "    ok 1 - inner\n"
            "      ---\n"
            "      duration_ms: 1\n"
            "      type: 'test'\n"
            "      ...\n"
            "ok 1 - outer\n"
            "  ---\n"
            "  duration_ms: 2\n"
            "  type: 'suite'\n"
            "  ...\n"
            "ok 2 - skipped one # SKIP not now\n"
            "not ok 3 - todo one # todo later\n"
            "not ok 4 - real failure\n"
            "  ---\n"
            "  type: 'test'\n"
            "  ...\n"
            "ok 5\n"
            "1..5\n"
        )
        self.assertEqual(
            parse_tap(output),
            [
                {"name": "inner", "ok": True},
                {"name": "real failure", "ok": False},
                {"name": "", "ok": True},
            ],
        )

    def test_parse_tap_empty_output(self):
        parse_tap = load_parse_tap()
        self.assertEqual(parse_tap("plain output\nno tap here\n"), [])

    def test_dirty_code_path_refused(self):
        self.standard_repo(self.script(tap="not ok 1 - a\n", code=1))
        (self.repo / "lib/code.txt").write_text("uncommitted\n")
        before = self.snapshot()
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 2)
        self.assertIn("error", report)
        self.assertEqual((self.repo / "lib/code.txt").read_text(), "uncommitted\n")
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.marker.exists())

    def test_base_not_ancestor_refused(self):
        self.git("checkout", "-q", "-b", "side")
        self.commit({"side.txt": "side\n"}, msg="side")
        side = self.rev()
        self.git("checkout", "-q", "main")
        self.standard_repo(self.script(tap="not ok 1 - a\n", code=1))
        before = self.snapshot()
        self.base = side
        proc, report = self.prove()
        self.assertEqual(proc.returncode, 2)
        self.assertIn("error", report)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.marker.exists())

    def test_bad_spec_refused(self):
        self.standard_repo(self.script(tap="not ok 1 - a\n", code=1))
        before = self.snapshot()
        good = {
            "repo": str(self.repo),
            "base": self.base,
            "tests": [{"path": TEST_PATH, "command": f"{PYTHON} {TEST_PATH}"}],
        }

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.spec_path.with_name("nope.json"))],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("error", json.loads(proc.stdout))

        self.spec_path.write_text("{not json")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.spec_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("error", json.loads(proc.stdout))

        for key in ("repo", "base", "tests"):
            spec = {k: v for k, v in good.items() if k != key}
            proc, report = self.prove(spec=spec)
            self.assertEqual(proc.returncode, 2, key)
            self.assertIn("error", report, key)

        missing = dict(good, tests=[{"path": "tests/absent.py", "command": "true"}])
        proc, report = self.prove(spec=missing)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("error", report)

        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.marker.exists())

    def test_restore_failure_exits_1(self):
        if os.geteuid() == 0:
            self.skipTest("root ignores directory permissions")
        self.commit({"gen/keep.txt": "keep\n"}, msg="more base")
        self.base = self.rev()
        self.commit({"gen/new.txt": "new\n"}, msg="code")
        self.commit(
            {
                TEST_PATH: self.script(
                    tap="not ok 1 - a\n", code=1, extra="os.chmod('gen', 0o555)"
                )
            },
            msg="tests",
        )
        proc, report = self.prove()
        os.chmod(self.repo / "gen", 0o755)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertFalse(report["restored"])
        self.assertIn("gen/new.txt", report["error"])


if __name__ == "__main__":
    unittest.main()
