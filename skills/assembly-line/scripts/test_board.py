import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "board.py"

USAGE = "usage: board.py [--cards <dir>] [--log <path>]"

BASE = datetime(2026, 11, 11, 10, 0, 0, tzinfo=timezone.utc)


def card_text(task=None, status=None, next_stage=None, status_raw=None):
    lines = ["---"]
    if task is not None:
        lines.append(f"task: '{task}'")
    if status_raw is not None:
        lines.append(f"runStatus: {status_raw}")
    elif status is not None:
        lines.append(f"runStatus: '{status}' note")
    if next_stage is not None:
        lines.append(f"runNext: '{next_stage}'")
    lines += ["---", "", "body"]
    return "\n".join(lines) + "\n"


def timed(stage, seconds, ticket="BOS-9"):
    start = BASE.isoformat().replace("+00:00", "Z")
    end = (BASE + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")
    return json.dumps({"ticket": ticket, "stage": stage, "startedAt": start, "endedAt": end})


def blocks(stdout):
    return stdout.rstrip("\n").split("\n\n")


def rows(block):
    return [re.split(r"\s{2,}", line.strip()) for line in block.split("\n")[1:]]


class Board(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name).resolve()
        self.cards = self.home / "recipes"
        self.cards.mkdir()
        self.log = self.home / "log.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def run_board(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.home,
            env={**os.environ, "HOME": str(self.home)},
            capture_output=True,
            text=True,
            timeout=60,
        )

    def board(self, log_lines=None):
        if log_lines is not None:
            self.log.write_text("\n".join(log_lines) + "\n")
        return self.run_board("--cards", str(self.cards), "--log", str(self.log))

    def card(self, name, **kwargs):
        (self.cards / name).write_text(card_text(**kwargs))

    def test_prints_board(self):
        self.card("a.md", task="BOS-1 first", status="running", next_stage="code.md")
        self.card("b.md", task="BOS-2 second", status="needs-input", next_stage="code.md")
        self.card("c.md", task="BOS-3 third", status="running", next_stage="qa.md")
        result = self.board([timed("code", 1000), timed("code", 1160)])
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = (
            "TICKET  STAGE  STATUS\n"
            "BOS-1   code   running\n"
            "BOS-2   code   needs-input\n"
            "BOS-3   qa     running\n"
            "\n"
            "STAGE  WAITING  MEAN MIN\n"
            "code   2        18\n"
            "qa     1        -\n"
            "\n"
            "Bottleneck: code (2 waiting, mean 18 min)\n"
        )
        self.assertEqual(result.stdout, expected)

    def test_only_running_cards(self):
        for status in ["running", "needs-input", "blocked", "gate"]:
            self.card(f"on-{status}.md", task=f"BOS-{len(status)} x", status=status, next_stage="code")
        self.card("terminal.md", task="TERM-1 x", status="terminal", next_stage="code")
        self.card("empty.md", task="EMPTY-1 x", status_raw="''", next_stage="code")
        self.card("none.md", task="NONE-1 x", next_stage="code")
        (self.cards / "plain.md").write_text("just text\nrunStatus: running\n")
        (self.cards / "notes.txt").write_text(card_text(task="TXT-1 x", status="running", next_stage="code"))
        sub = self.cards / "sub"
        sub.mkdir()
        (sub / "deep.md").write_text(card_text(task="SUB-1 x", status="running", next_stage="code"))
        result = self.board([])
        self.assertEqual(result.returncode, 0, result.stderr)
        statuses = sorted(row[2] for row in rows(blocks(result.stdout)[0]))
        self.assertEqual(statuses, ["blocked", "gate", "needs-input", "running"])
        for absent in ["TERM-1", "EMPTY-1", "NONE-1", "TXT-1", "SUB-1"]:
            self.assertNotIn(absent, result.stdout)

    def test_rows_sorted_by_ticket(self):
        self.card("z.md", task="BOS-1 a", status="running", next_stage="code")
        self.card("y.md", task="BOS-3 c", status="running", next_stage="code")
        self.card("x.md", task="BOS-2 b", status="running", next_stage="code")
        result = self.board([])
        tickets = [row[0] for row in rows(blocks(result.stdout)[0])]
        self.assertEqual(tickets, ["BOS-1", "BOS-2", "BOS-3"])

    def test_stage_from_run_next(self):
        self.card("a.md", task="BOS-1 a", status="running", next_stage="phase-3-cooking.md")
        self.card("b.md", task="BOS-2 b", status="running", next_stage="")
        self.card("c.md", task="BOS-3 c", status="running")
        result = self.board([])
        stages = {row[0]: row[1] for row in rows(blocks(result.stdout)[0])}
        self.assertEqual(stages, {"BOS-1": "phase-3-cooking", "BOS-2": "unknown", "BOS-3": "unknown"})

    def test_ticket_from_task_or_file(self):
        self.card("a.md", task="BOS-7 — x", status="running", next_stage="code")
        self.card("named.md", task="no id here", status="running", next_stage="code")
        self.card("bare.md", status="running", next_stage="code")
        result = self.board([])
        tickets = sorted(row[0] for row in rows(blocks(result.stdout)[0]))
        self.assertEqual(tickets, ["BOS-7", "bare", "named"])

    def test_frontmatter_quotes_and_comments(self):
        self.card("a.md", task="BOS-1 a", status_raw="'running' # note", next_stage="code")
        self.card("b.md", task="BOS-2 b", status_raw='"gate"', next_stage="code")
        self.card("c.md", task="BOS-3 c", status_raw="blocked # note", next_stage="code")
        result = self.board([])
        statuses = {row[0]: row[2] for row in rows(blocks(result.stdout)[0])}
        self.assertEqual(statuses, {"BOS-1": "running", "BOS-2": "gate", "BOS-3": "blocked"})

    def test_bottleneck_most_waiting(self):
        self.card("a.md", task="BOS-1 a", status="running", next_stage="qa")
        self.card("b.md", task="BOS-2 b", status="running", next_stage="qa")
        self.card("c.md", task="BOS-3 c", status="running", next_stage="code")
        result = self.board([timed("code", 6000)])
        parts = blocks(result.stdout)
        self.assertEqual(rows(parts[1])[0][0], "qa")
        self.assertEqual(parts[2].split("\n")[0], "Bottleneck: qa (2 waiting)")

    def test_bottleneck_tie_uses_log_mean(self):
        self.card("a.md", task="BOS-1 a", status="running", next_stage="code")
        self.card("b.md", task="BOS-2 b", status="running", next_stage="qa")
        result = self.board([timed("code", 600), timed("qa", 1200)])
        self.assertIn("Bottleneck: qa (1 waiting, mean 20 min)", result.stdout)
        result = self.board([timed("qa", 60)])
        self.assertIn("Bottleneck: qa (1 waiting, mean 1 min)", result.stdout)

    def test_bottleneck_tie_without_log_by_name(self):
        self.card("a.md", task="BOS-1 a", status="running", next_stage="qa")
        self.card("b.md", task="BOS-2 b", status="running", next_stage="code")
        result = self.board([])
        parts = blocks(result.stdout)
        self.assertIn("Bottleneck: code (1 waiting)", parts[2])
        self.assertEqual([row[2] for row in rows(parts[1])], ["-", "-"])

    def test_no_running_cards(self):
        self.card("a.md", task="BOS-1 a", status="terminal", next_stage="code")
        result = self.board([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"No running lines in {self.cards.resolve()}.\n")

    def test_log_lines_skipped_or_untimed(self):
        self.card("a.md", task="BOS-1 a", status="running", next_stage="code")
        stale = json.dumps({"stage": "code", "startedAt": "yesterday", "endedAt": "2026-11-11T10:00:00Z"})
        backwards = json.dumps({"stage": "code", "startedAt": "2026-11-11T10:05:00Z", "endedAt": "2026-11-11T10:00:00Z"})
        result = self.board(["not json", "[1, 2]", json.dumps({"ticket": "BOS-1"}), "", stale, backwards])
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.rstrip("\n").split("\n")
        self.assertEqual(lines[-2], "Bottleneck: code (1 waiting)")
        self.assertEqual(lines[-1], "Skipped 3 bad log lines.")
        self.assertEqual(rows(blocks(result.stdout)[1])[0], ["code", "1", "-"])

    def test_default_paths_and_tilde(self):
        self.card("a.md", task="BOS-1 a", status="running", next_stage="code")
        runs = self.home / ".bosi-skills"
        runs.mkdir()
        (runs / "runs.jsonl").write_text(timed("code", 600) + "\n")
        result = self.run_board()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Bottleneck: code (1 waiting, mean 10 min)", result.stdout)
        other = self.home / "c"
        other.mkdir()
        (other / "b.md").write_text(card_text(task="BOS-5 b", status="running", next_stage="qa"))
        (self.home / "l.jsonl").write_text(timed("qa", 1800) + "\n")
        result = self.run_board("--cards", "~/c", "--log", "~/l.jsonl")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("BOS-5", result.stdout)
        self.assertNotIn("BOS-1", result.stdout)
        self.assertIn("Bottleneck: qa (1 waiting, mean 30 min)", result.stdout)

    def test_errors(self):
        for args in [["--bogus"], ["--cards"], ["--log"], ["stray"], ["--cards", str(self.cards), "stray"]]:
            with self.subTest(args=args):
                result = self.run_board(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, USAGE + "\n")
        plain = self.home / "file.txt"
        plain.write_text("x")
        folder = self.home / "folder"
        folder.mkdir()
        cases = {
            "missing cards": ["--cards", str(self.home / "nope"), "--log", str(self.log)],
            "file cards": ["--cards", str(plain), "--log", str(self.log)],
            "folder log": ["--cards", str(self.cards), "--log", str(folder)],
        }
        for name, args in cases.items():
            with self.subTest(name=name):
                result = self.run_board(*args)
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                self.assertIsInstance(payload["error"], str)

    def test_unreadable_cards_folder(self):
        locked = self.home / "locked"
        locked.mkdir()
        locked.chmod(0)
        try:
            result = self.run_board("--cards", str(locked), "--log", str(self.log))
        finally:
            locked.chmod(0o755)
        self.assertEqual(result.returncode, 1)
        self.assertIsInstance(json.loads(result.stdout)["error"], str)


if __name__ == "__main__":
    unittest.main()
