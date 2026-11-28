import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check-design-gate.py"
SKILL_MD = Path(__file__).resolve().parents[1] / "SKILL.md"
README = Path(__file__).resolve().parents[3] / "README.md"

LINK_SENTENCE = "The question ends with the plan comment link:"
TRACKER_SENTENCE = "With no tracker tool, it ends with `not posted — no tracker tool` instead. "
PLACEHOLDER_TAIL = "question is never a placeholder"


def run(path):
    command = [sys.executable, str(SCRIPT)]
    if path is not None:
        command.append(str(path))
    return subprocess.run(command, capture_output=True, text=True, check=False)


class GateLinkCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_text(self, text):
        path = self.dir / "SKILL.md"
        path.write_text(text, encoding="utf-8")
        return run(path)

    def write(self, old, new):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn(old, text)
        return self.write_text(text.replace(old, new, 1))

    def test_fails_when_the_link_sentence_is_negated(self):
        result = self.write(LINK_SENTENCE, "The question never ends with the plan comment link:")
        self.assertRegex(result.stdout, r"FAIL\s+gate-link")
        self.assertEqual(result.returncode, 1)

    def test_passes_on_the_real_skill(self):
        by_default = run(None)
        by_path = run(SKILL_MD)
        self.assertEqual(by_default.returncode, 0, by_default.stdout)
        self.assertEqual(by_path.returncode, 0, by_path.stdout)
        self.assertRegex(by_path.stdout, r"PASS\s+gate-link")
        self.assertNotRegex(by_path.stdout, r"FAIL")

    def test_fails_when_a_word_is_inserted_in_a_phrase(self):
        result = self.write(PLACEHOLDER_TAIL, "question is not only never a placeholder")
        self.assertRegex(result.stdout, r"FAIL\s+gate-link")
        self.assertEqual(result.returncode, 1)

    def test_fails_when_words_come_before_the_phrase(self):
        result = self.write(LINK_SENTENCE, "It is false that the question ends with the plan comment link:")
        self.assertRegex(result.stdout, r"FAIL\s+gate-link")
        self.assertEqual(result.returncode, 1)

    def test_fails_naming_a_missing_sentence(self):
        result = self.write(TRACKER_SENTENCE, "")
        self.assertRegex(result.stdout, r"FAIL\s+gate-link")
        gate_line = next(line for line in result.stdout.splitlines() if re.search(r"gate-link", line))
        self.assertIn("missing:", gate_line)
        self.assertIn("with no tracker tool", gate_line)

    def test_passes_when_rewrapped_and_upper_cased(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        match = re.search(r"^## 3\. Gate\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertIsNotNone(match)
        body = match.group(1)
        rewrapped = textwrap.fill(" ".join(body.split()), width=37).upper() + "\n\n"
        result = self.write_text(text.replace(body, rewrapped, 1))
        self.assertRegex(result.stdout, r"PASS\s+gate-link")

    def test_readme_lists_the_test_file(self):
        text = README.read_text(encoding="utf-8")
        match = re.search(r"^## Validate a change\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        self.assertIsNotNone(match)
        self.assertIn("python3 skills/design-gate/scripts/test_check_design_gate.py", match.group(1))


if __name__ == "__main__":
    unittest.main()
