import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "stats.py"

USAGE = "usage: stats.py --kind <kind> [--log <path>] [--catalog <path>]"

CATALOG = {"stages": {"qa": {"return": {"fail": {"to": "code", "limit": 2, "past": "human"}}}}}


def line(ticket="T-1", stage="qa", verdict="pass", loops=0, kind="feature", **extra):
    out = {"ticket": ticket, "kind": kind, "stage": stage, "verdict": verdict, "loops": loops}
    out.update(extra)
    return json.dumps(out)


class Stats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name).resolve()
        self.catalog = self.home / "catalog.json"
        self.catalog.write_text(json.dumps(CATALOG))

    def tearDown(self):
        self.tmp.cleanup()

    def run_stats(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env={**os.environ, "HOME": str(self.home)},
            capture_output=True,
            text=True,
            timeout=60,
        )

    def write_log(self, lines, name="runs.jsonl"):
        path = self.home / name
        path.write_text("\n".join(lines) + "\n")
        return path

    def stats(self, lines, kind="feature"):
        path = self.write_log(lines)
        result = self.run_stats("--kind", kind, "--log", str(path), "--catalog", str(self.catalog))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def stage(self, data, name):
        return next(s for s in data["stages"] if s["stage"] == name)

    def test_counts_per_stage(self):
        data = self.stats([
            line("T-1", "qa", "fail", 1, changedBy="add-stage"),
            line("T-2", "qa", "pass", 0),
            line("T-2", "qa", "pass", 2),
            line("T-3", "qa", "pass", 1, changedBy=None),
            line("T-1", "code", "done", 3, changedBy="drop-stage"),
            line("T-4", "code", "done", 0),
        ])
        self.assertEqual(list(data), ["log", "kind", "tickets", "skipped", "stages"])
        self.assertEqual(data["kind"], "feature")
        self.assertEqual(data["tickets"], 4)
        self.assertEqual(data["skipped"], 0)
        self.assertEqual([s["stage"] for s in data["stages"]], ["code", "qa"])
        qa = self.stage(data, "qa")
        self.assertEqual(qa["runs"], 4)
        self.assertEqual(qa["tickets"], 3)
        self.assertEqual(qa["fails"], 1)
        self.assertEqual(qa["failRate"], 0.25)
        self.assertEqual(qa["meanLoops"], 1.0)
        self.assertEqual(qa["added"], 1)
        self.assertEqual(qa["addedRate"], 0.25)
        code = self.stage(data, "code")
        self.assertEqual(code["runs"], 2)
        self.assertEqual(code["tickets"], 2)
        self.assertEqual(code["fails"], 0)
        self.assertEqual(code["failRate"], 0.0)
        self.assertEqual(code["meanLoops"], 1.5)
        self.assertEqual(code["added"], 1)
        self.assertEqual(code["addedRate"], 0.5)

    def test_fail_uses_catalog_return(self):
        data = self.stats([
            line("T-1", "qa", "fail"),
            line("T-2", "qa", "pass"),
            line("T-3", "qa", "blocked"),
            line("T-1", "lint", "blocked"),
            line("T-2", "lint", "needs-input"),
            line("T-3", "lint", "gate"),
            line("T-4", "lint", "done"),
            line("T-5", "lint", "fail"),
        ])
        self.assertEqual(self.stage(data, "qa")["fails"], 2)
        self.assertEqual(self.stage(data, "lint")["fails"], 3)

    def test_other_kinds_ignored(self):
        data = self.stats([
            line("T-1", "qa", "pass", kind="feature"),
            line("T-2", "qa", "fail", kind="bug"),
            line("T-3", "qa", "fail", kind=None),
            line("T-4", "code", "done", kind="bug"),
        ])
        self.assertEqual(data["tickets"], 1)
        self.assertEqual(data["skipped"], 0)
        self.assertEqual([s["stage"] for s in data["stages"]], ["qa"])
        self.assertEqual(self.stage(data, "qa")["runs"], 1)
        self.assertEqual(self.stage(data, "qa")["fails"], 0)

    def test_bad_lines_skipped(self):
        data = self.stats([
            "not json",
            "[1, 2]",
            json.dumps({"ticket": "T-9", "kind": "feature", "verdict": "pass", "loops": 0}),
            line("T-9", "qa", "pass", "x"),
            "",
            "   ",
            line("T-1", "qa", "pass"),
            line("T-2", "qa", "pass"),
        ])
        self.assertEqual(data["skipped"], 4)
        self.assertEqual(data["tickets"], 2)
        self.assertEqual(self.stage(data, "qa")["runs"], 2)

    def test_missing_log_is_empty(self):
        path = self.home / "absent" / "runs.jsonl"
        result = self.run_stats("--kind", "feature", "--log", str(path), "--catalog", str(self.catalog))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["stages"], [])
        self.assertEqual(data["tickets"], 0)
        self.assertEqual(data["skipped"], 0)
        self.assertFalse(path.exists())
        self.assertFalse(path.parent.exists())

    def test_default_log_and_tilde(self):
        default = self.home / ".bosi-skills" / "runs.jsonl"
        default.parent.mkdir()
        default.write_text(line("T-1", "qa", "pass") + "\n")
        (self.home / "x.jsonl").write_text(line("T-1", "qa") + "\n" + line("T-2", "qa") + "\n")
        result = self.run_stats("--kind", "feature", "--catalog", str(self.catalog))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["log"], str(default.resolve()))
        self.assertEqual(data["tickets"], 1)
        result = self.run_stats("--kind", "feature", "--log", "~/x.jsonl", "--catalog", str(self.catalog))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["log"], str((self.home / "x.jsonl").resolve()))
        self.assertTrue(os.path.isabs(data["log"]))
        self.assertEqual(data["tickets"], 2)

    def test_bad_input_exits_two(self):
        cases = {
            "no arguments": [],
            "unknown flag": ["--kind", "feature", "--nope", "x"],
            "flag with no value": ["--kind", "feature", "--log"],
            "no kind": ["--log", str(self.home / "x.jsonl")],
            "empty kind": ["--kind", ""],
        }
        for name, args in cases.items():
            with self.subTest(name):
                result = self.run_stats(*args)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(result.stdout.strip(), USAGE)

    def runs(self, stage, count, **per_run):
        out = []
        for i in range(count):
            fields = {key: value(i) if callable(value) else value for key, value in per_run.items()}
            out.append(line(f"T-{i}", stage, **fields))
        return out

    def test_no_suggestion_under_five_runs(self):
        data = self.stats(self.runs("qa", 4, verdict="fail") + self.runs("code", 4, verdict="done"))
        for name in ("qa", "code"):
            entry = self.stage(data, name)
            self.assertEqual(entry["runs"], 4)
            self.assertIsNone(entry["suggestion"])
            self.assertIsNone(entry["because"])

    def test_cut_when_never_fails(self):
        data = self.stats(self.runs("qa", 5, verdict="pass"))
        qa = self.stage(data, "qa")
        self.assertEqual(qa["suggestion"], "cut")
        self.assertEqual(qa["because"], "`qa` never failed in 5 runs on 5 feature tickets")

    def test_look_when_fails_a_quarter(self):
        data = self.stats(self.runs("qa", 8, verdict=lambda i: "fail" if i < 2 else "pass"))
        qa = self.stage(data, "qa")
        self.assertEqual(qa["suggestion"], "look")
        self.assertEqual(qa["because"], "`qa` failed 2 of 8 runs on feature tickets")
        data = self.stats(self.runs("qa", 9, verdict=lambda i: "fail" if i < 2 else "pass"))
        qa = self.stage(data, "qa")
        self.assertIsNone(qa["suggestion"])
        self.assertIsNone(qa["because"])

    def test_add_wins_over_cut(self):
        data = self.stats(self.runs("qa", 6, changedBy=lambda i: "add-stage" if i < 4 else None))
        qa = self.stage(data, "qa")
        self.assertEqual(qa["suggestion"], "add")
        self.assertEqual(qa["because"], "a signal added `qa` in 4 of 6 runs on feature tickets")
        data = self.stats(self.runs("qa", 6, changedBy=lambda i: "add-stage" if i < 3 else None))
        qa = self.stage(data, "qa")
        self.assertEqual(qa["suggestion"], "cut")
        self.assertEqual(qa["because"], "`qa` never failed in 6 runs on 6 feature tickets")

    def test_judge_and_merge_never_cut(self):
        data = self.stats(self.runs("judge", 5, verdict="done") + self.runs("merge", 5, verdict="done"))
        for name in ("judge", "merge"):
            entry = self.stage(data, name)
            self.assertEqual(entry["runs"], 5)
            self.assertIsNone(entry["suggestion"])
            self.assertIsNone(entry["because"])


if __name__ == "__main__":
    unittest.main()
