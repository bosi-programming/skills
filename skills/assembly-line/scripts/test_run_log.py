import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "run-log.py"

USAGE = (
    "usage: run-log.py append [--log <path>] --ticket <id> [--kind <kind>] [--line <name>] "
    "--stage <stage> --started-at <iso> --ended-at <iso> --verdict <verdict> --loops <n> "
    "[--tokens <n>] [--changed-by <signal>]"
)

KEYS = ["ticket", "kind", "line", "stage", "startedAt", "endedAt", "verdict", "loops", "tokens", "changedBy"]

REQUIRED = {
    "--ticket": "BOS-1",
    "--stage": "code",
    "--started-at": "2026-11-11T10:00:00Z",
    "--ended-at": "2026-11-11T10:05:00Z",
    "--verdict": "done",
    "--loops": "0",
}

OPTIONAL = {
    "--kind": "feature",
    "--line": "default",
    "--tokens": "1234",
    "--changed-by": "add-stage",
}


def flags(values):
    out = []
    for key, value in values.items():
        out += [key, value]
    return out


class RunLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env={**os.environ, "HOME": str(self.home)},
            capture_output=True,
            text=True,
            timeout=60,
        )

    def append(self, log, **overrides):
        values = {**REQUIRED, **OPTIONAL}
        values.update(overrides)
        return self.run_script("append", "--log", str(log), *flags(values))

    def test_append_writes_one_json_line(self):
        log = self.home / "runs.jsonl"
        result = self.append(log)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = log.read_text()
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(len(text.splitlines()), 1)
        record = json.loads(text)
        self.assertEqual(list(record.keys()), KEYS)
        self.assertEqual(
            record,
            {
                "ticket": "BOS-1",
                "kind": "feature",
                "line": "default",
                "stage": "code",
                "startedAt": "2026-11-11T10:00:00Z",
                "endedAt": "2026-11-11T10:05:00Z",
                "verdict": "done",
                "loops": 0,
                "tokens": 1234,
                "changedBy": "add-stage",
            },
        )
        self.assertIsInstance(record["loops"], int)
        self.assertIsInstance(record["tokens"], int)

    def test_append_creates_missing_folder(self):
        log = self.home / "one" / "two" / "runs.jsonl"
        result = self.append(log)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(log.exists())
        self.assertEqual(len(log.read_text().splitlines()), 1)

    def test_append_keeps_earlier_lines(self):
        log = self.home / "runs.jsonl"
        self.append(log, **{"--ticket": "BOS-1"})
        first = log.read_text().splitlines()[0]
        self.append(log, **{"--ticket": "BOS-2"})
        lines = log.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], first)
        self.assertEqual(json.loads(lines[1])["ticket"], "BOS-2")

    def test_optional_fields_are_null(self):
        log = self.home / "runs.jsonl"
        result = self.run_script("append", "--log", str(log), *flags(REQUIRED))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = json.loads(log.read_text())
        for key in ["kind", "line", "tokens", "changedBy"]:
            self.assertIn(key, record)
            self.assertIsNone(record[key])
        self.assertEqual(list(record.keys()), KEYS)

    def test_default_log_under_home(self):
        result = self.run_script("append", *flags(REQUIRED))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = self.home / ".bosi-skills" / "runs.jsonl"
        self.assertTrue(log.exists())
        self.assertEqual(len(log.read_text().splitlines()), 1)

    def test_log_path_expands_tilde(self):
        result = self.run_script("append", "--log", "~/x/runs.jsonl", *flags(REQUIRED))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = self.home / "x" / "runs.jsonl"
        self.assertTrue(log.exists())
        self.assertEqual(len(log.read_text().splitlines()), 1)

    def test_prints_log_and_record(self):
        log = self.home / "runs.jsonl"
        result = self.append(log)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        printed = json.loads(result.stdout)
        self.assertEqual(set(printed.keys()), {"log", "record"})
        self.assertTrue(os.path.isabs(printed["log"]))
        self.assertEqual(Path(printed["log"]).resolve(), log.resolve())
        self.assertEqual(printed["record"], json.loads(log.read_text()))

    def test_repairs_missing_trailing_newline(self):
        log = self.home / "runs.jsonl"
        log.write_text(json.dumps({"ticket": "OLD"}))
        result = self.append(log)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = log.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            json.loads(line)
        self.assertEqual(json.loads(lines[0]), {"ticket": "OLD"})

    def test_bad_input_writes_nothing(self):
        cases = {
            "no subcommand": [],
            "unknown subcommand": ["remove"],
            "unknown flag": ["append", *flags(REQUIRED), "--bogus", "1"],
            "flag without value": ["append", *flags(REQUIRED), "--kind"],
            "loops negative": ["append", *flags({**REQUIRED, "--loops": "-1"})],
            "loops not a number": ["append", *flags({**REQUIRED, "--loops": "x"})],
            "tokens negative": ["append", *flags({**REQUIRED, "--tokens": "-5"})],
            "started-at bad": ["append", *flags({**REQUIRED, "--started-at": "yesterday"})],
            "ended-at bad": ["append", *flags({**REQUIRED, "--ended-at": "yesterday"})],
        }
        for missing in REQUIRED:
            cases[f"missing {missing}"] = [
                "append",
                *flags({key: value for key, value in REQUIRED.items() if key != missing}),
            ]
        for name, args in cases.items():
            with self.subTest(name):
                log = self.home / "nested" / "runs.jsonl"
                result = self.run_script(*args[:1], "--log", str(log), *args[1:]) if args[:1] == ["append"] else self.run_script(*args)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(USAGE, result.stdout)
                self.assertFalse(log.exists())
                self.assertFalse(log.parent.exists())
                self.assertFalse((self.home / ".bosi-skills").exists())

    def test_unwritable_log_exits_one_with_error(self):
        blocker = self.home / "blocker"
        blocker.write_text("x")
        log = blocker / "runs.jsonl"
        result = self.run_script("append", "--log", str(log), *flags(REQUIRED))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("error", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
