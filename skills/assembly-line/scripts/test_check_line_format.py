import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check-line-format.py"

FULL = ["judge", "evaluate-ticket", "plan-code", {"parallel": ["test", "code"]}, "code",
        "prepare-pr", "review-fix", "code-docs", "merge"]
SHORT = ["judge", "evaluate-ticket", "plan-code", "code", "prepare-pr", "merge"]

SECTIONS = {
    "marker": "## Marker\n\nA line comment holds one ```json block whose object has "
              '`"format": "assembly-line/1"`.\n',
    "order": "## Stages and inputs\n\n`stages` lists the stages in order. An item is a stage name or "
             '`{"stage": "<name>", "with": {...}}`. Card inputs come from `takes` in `stage.json`, '
             "and the `gate` comes from `stage.json` too.\n",
    "parallel": '## Parallel groups\n\n`{"parallel": [...]}` runs its branches at the same time.\n',
    "latest-wins": "## More than one line comment\n\nThe line comment created last wins.\n",
    "sub-issues": '## Sub-issue groups\n\n`{"group": "sub-issues"}` runs each sub-issue\'s own line '
                  "without its `merge`; the parent's `merge` merges them all.\n",
}


def example(title, stages):
    body = json.dumps({"format": "assembly-line/1", "ticket": "BOS-1", "stages": stages}, indent=2)
    return f"## {title}\n\n```json\n{body}\n```\n"


def document(drop=(), full=FULL, short=SHORT):
    parts = ["# Line format\n"]
    parts += [text for name, text in SECTIONS.items() if name not in drop]
    if "full" not in drop:
        parts.append(full if isinstance(full, str) else example("Example: full line", full))
    if "short" not in drop:
        parts.append(short if isinstance(short, str) else example("Example: short line", short))
    return "\n".join(parts)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          check=False, capture_output=True, text=True)


class LineFormatCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "line-format.md"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, text):
        self.path.write_text(text)
        return run(self.path)

    def test_passes_on_the_real_file(self):
        result = run()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_passes_on_a_valid_fixture(self):
        result = self.write(document())
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_fails_when_the_file_is_missing(self):
        result = run(self.path)
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+exists")

    def test_fails_naming_each_missing_answer(self):
        for name in SECTIONS:
            with self.subTest(section=name):
                result = self.write(document(drop=[name]))
                self.assertEqual(result.returncode, 1)
                self.assertRegex(result.stdout, rf"FAIL\s+section-{name}\b")

    def test_fails_when_an_example_is_missing(self):
        for name in ("full", "short"):
            with self.subTest(example=name):
                result = self.write(document(drop=[name]))
                self.assertEqual(result.returncode, 1)
                self.assertRegex(result.stdout, rf"FAIL\s+example-{name}\b")

    def test_fails_when_an_example_does_not_parse(self):
        result = self.write(document(short="## Example: short line\n\n```json\n{not json\n```\n"))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+short-parses")

    def test_fails_when_the_format_marker_is_wrong(self):
        broken = example("Example: short line", SHORT).replace("assembly-line/1", "other/1")
        result = self.write(document(short=broken))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+short-format")

    def test_fails_when_a_line_does_not_start_at_judge(self):
        result = self.write(document(short=SHORT[1:]))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+short-first-judge")

    def test_fails_when_a_line_has_no_merge(self):
        result = self.write(document(short=SHORT[:-1]))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+short-has-merge")

    def test_fails_naming_an_unknown_stage(self):
        result = self.write(document(short=SHORT[:-1] + ["no-such-stage", "merge"]))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+short-known-stages")
        self.assertIn("no-such-stage", result.stdout)

    def test_fails_on_an_unknown_stage_inside_a_parallel_group(self):
        full = FULL[:3] + [{"parallel": ["test", "no-such-stage"]}] + FULL[4:]
        result = self.write(document(full=full))
        self.assertEqual(result.returncode, 1)
        self.assertIn("no-such-stage", result.stdout)

    def test_fails_when_a_human_gate_comes_after_merge(self):
        result = self.write(document(short=SHORT + ["merge"]))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+short-auto-after-merge")

    def test_passes_with_an_auto_stage_after_merge(self):
        result = self.write(document(short=SHORT + ["code-docs"]))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_fails_when_the_full_example_has_no_parallel_group(self):
        result = self.write(document(full=SHORT))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"FAIL\s+full-has-parallel")

    def test_accepts_a_stage_object_with_inputs(self):
        short = SHORT[:-1] + [{"stage": "ui-review", "with": {"url": "http://localhost:3000"}}, "merge"]
        result = self.write(document(short=short))
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
