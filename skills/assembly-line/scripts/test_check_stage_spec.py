import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check-stage-spec.py"
SKILLS = Path(__file__).resolve().parents[2]


def spec(**overrides):
    base = {
        "spec": "../assembly-line/references/stage-spec.md",
        "takes": ["task"],
        "delivers": {
            "sections": ["## Problem"],
            "fields": ["phase"],
            "verdicts": ["done", "blocked"],
        },
        "return": {"blocked": {"to": "evaluate-ticket", "limit": 0, "past": "needs-input"}},
        "signals": [],
        "gate": "auto",
    }
    base.update(overrides)
    return base


def run(directory):
    return subprocess.run([sys.executable, str(SCRIPT), str(directory)], check=False, capture_output=True, text=True)


class StageSpecCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, content):
        (self.dir / "stage.json").write_text(content if isinstance(content, str) else json.dumps(content))
        return run(self.dir)

    def test_passes_on_evaluate_ticket(self):
        result = run(SKILLS / "evaluate-ticket")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_passes_on_a_valid_fixture(self):
        result = self.write(spec())
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_fails_naming_return_when_missing(self):
        body = spec()
        del body["return"]
        result = self.write(body)
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+key-return")

    def test_fails_when_return_names_a_missing_stage(self):
        result = self.write(spec(**{"return": {"blocked": {"to": "no-such-stage", "limit": 1, "past": "human"}}}))
        self.assertEqual(result.returncode, 1)
        self.assertIn("no-such-stage", result.stdout)

    def test_fails_on_invalid_json(self):
        result = self.write("{not json")
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+parses")

    def test_fails_when_stage_json_is_missing(self):
        result = run(self.dir)
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+exists")

    def test_fails_on_unknown_gate(self):
        result = self.write(spec(gate="sometimes"))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+gate")

    def test_fails_on_unknown_past(self):
        result = self.write(spec(**{"return": {"blocked": {"to": "evaluate-ticket", "limit": 0, "past": "retry"}}}))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+return-past")

    def test_fails_on_negative_limit(self):
        result = self.write(spec(**{"return": {"blocked": {"to": "evaluate-ticket", "limit": -1, "past": "human"}}}))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+return-limit")

    def test_fails_when_return_verdict_is_not_delivered(self):
        result = self.write(spec(**{"return": {"failed": {"to": "evaluate-ticket", "limit": 0, "past": "human"}}}))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+return-verdict")

    def test_fails_when_takes_is_not_a_list_of_strings(self):
        result = self.write(spec(takes="task"))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+takes")

    def test_fails_when_delivers_lacks_verdicts(self):
        result = self.write(spec(delivers={"sections": [], "fields": []}))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+delivers")


if __name__ == "__main__":
    unittest.main()
