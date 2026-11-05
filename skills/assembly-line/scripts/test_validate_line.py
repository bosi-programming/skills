import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "validate-line.py"
SKILLS = Path(__file__).resolve().parents[2]
REPO = SKILLS.parent
CATALOG = SKILLS / "assembly-line" / "references" / "catalog.json"
LINE_FORMAT = SKILLS / "assembly-line" / "references" / "line-format.md"

USAGE = "usage: validate-line.py"
SHORT = ["judge", "evaluate-ticket", "plan-code", "code", "prepare-pr", "review-fix", "merge"]


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          check=False, capture_output=True, text=True)


def line_of(stages, ticket="BOS-1"):
    return {"format": "assembly-line/1", "ticket": ticket, "stages": stages}


def real_catalog():
    return json.loads(CATALOG.read_text())


def example(heading):
    text = LINE_FORMAT.read_text()
    start = text.index(heading)
    match = re.search(r"```json\n(.*?)```", text[start:], re.S)
    return match.group(1)


class ValidateLine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        path = self.root / name
        path.write_text(content if isinstance(content, str) else json.dumps(content))
        return path

    def validate(self, line, catalog=None):
        args = [self.write("line.json", line)]
        if catalog is not None:
            args += ["--catalog", self.write("catalog.json", catalog)]
        result = run(*args)
        return result.returncode, json.loads(result.stdout)

    def has_error(self, out, stage, rule, message=None):
        for error in out["errors"]:
            if error["stage"] == stage and error["rule"] == rule:
                if message is None or message in error["message"]:
                    return True
        return False

    def assertError(self, out, stage, rule, message=None):
        self.assertTrue(self.has_error(out, stage, rule, message), out)

    def assertNoRule(self, out, rule, stage=False):
        for error in out["errors"]:
            if error["rule"] == rule and (stage is False or error["stage"] == stage):
                self.fail(out)

    def catalog_with(self, add=None, remove=()):
        catalog = real_catalog()
        for name in remove:
            del catalog["stages"][name]
        for name, entry in (add or {}).items():
            catalog["stages"][name] = entry
        return catalog

    def test_rejects_an_unknown_stage(self):
        code, out = self.validate(line_of(["judge", "no-such-stage", "merge"]))
        self.assertEqual(code, 1)
        self.assertFalse(out["valid"])
        self.assertError(out, "no-such-stage", "known-stage", "no-such-stage")

    def test_rejects_an_unknown_stage_in_a_parallel_group(self):
        stages = ["judge", "evaluate-ticket", {"parallel": ["code", "no-such-stage"]}, "merge"]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, "no-such-stage", "known-stage")

    def test_rejects_a_line_not_starting_at_judge(self):
        code, out = self.validate(line_of(["evaluate-ticket", "judge", "merge"]))
        self.assertEqual(code, 1)
        self.assertError(out, "evaluate-ticket", "first-judge", "judge")

    def test_rejects_a_line_without_merge(self):
        code, out = self.validate(line_of(["judge", "evaluate-ticket"]))
        self.assertEqual(code, 1)
        self.assertError(out, "merge", "last-gate-merge", "merge")

    def test_rejects_merge_only_inside_a_parallel_group(self):
        stages = ["judge", "evaluate-ticket", {"parallel": ["code", "merge"]}]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, "merge", "last-gate-merge")

    def test_rejects_a_human_gate_after_merge(self):
        sign_off = copy.deepcopy(real_catalog()["stages"]["judge"])
        sign_off["gate"] = "human"
        catalog = self.catalog_with(add={"sign-off": sign_off})
        stages = SHORT + ["sign-off"]
        code, out = self.validate(line_of(stages), catalog)
        self.assertEqual(code, 1)
        self.assertError(out, "sign-off", "auto-after-merge", "human")

    def test_rejects_a_take_no_stage_delivers(self):
        nowhere = copy.deepcopy(real_catalog()["stages"]["judge"])
        nowhere["takes"] = ["## Nowhere"]
        catalog = self.catalog_with(add={"nowhere": nowhere})
        stages = ["judge", "nowhere", "evaluate-ticket", "merge"]
        code, out = self.validate(line_of(stages), catalog)
        self.assertEqual(code, 1)
        self.assertError(out, "nowhere", "takes-met", "no stage in the catalog delivers it")

    def test_rejects_a_return_role_not_on_the_line(self):
        stages = [s for s in SHORT if s != "review-fix"]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, "merge", "return-target", "review-fix")

    def test_rejects_branches_that_share_a_delivery(self):
        stages = ["judge", "evaluate-ticket", "plan-code", "code", "prepare-pr",
                  {"parallel": ["code", "review-fix"]}, "merge"]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, "review-fix", "parallel-group", "## Quality Gate Results")

    def test_a_branch_does_not_meet_a_sibling_take(self):
        stages = ["judge", "evaluate-ticket", {"parallel": ["plan-code", "code"]},
                  "prepare-pr", "review-fix", "merge"]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, "code", "takes-met")

    def test_rejects_a_missing_line_file(self):
        result = run(self.root / "absent.json")
        out = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertError(out, None, "line-parses", "missing")

    def test_rejects_a_line_file_that_does_not_parse(self):
        code, out = self.validate("{not json")
        self.assertEqual(code, 1)
        self.assertError(out, None, "line-parses", "does not parse")

    def test_rejects_a_line_of_the_wrong_shape(self):
        good = line_of(SHORT)
        cases = {
            "format": {**good, "format": "other/1"},
            "no ticket": {k: v for k, v in good.items() if k != "ticket"},
            "empty stages": {**good, "stages": []},
            "item 42": line_of(["judge", 42, "merge"]),
            "empty parallel": line_of(["judge", {"parallel": []}, "merge"]),
            "other group": line_of(["judge", {"group": "other"}, "merge"]),
        }
        for name, line in cases.items():
            with self.subTest(case=name):
                code, out = self.validate(line)
                self.assertEqual(code, 1)
                self.assertError(out, None, "line-shape")
                for error in out["errors"]:
                    self.assertEqual(error["rule"], "line-shape")

    def test_rejects_a_catalog_that_does_not_parse(self):
        code, out = self.validate(line_of(SHORT), "{not json")
        self.assertEqual(code, 1)
        self.assertError(out, None, "catalog-parses")

    def test_full_example_passes(self):
        code, out = self.validate(example("## Example: full line"))
        self.assertEqual(code, 0, out)
        self.assertEqual(out, {"valid": True, "errors": []})

    def test_short_example_passes(self):
        code, out = self.validate(example("## Example: short line"))
        self.assertEqual(code, 0, out)
        self.assertEqual(out, {"valid": True, "errors": []})

    def test_parent_example_passes(self):
        code, out = self.validate(example("## Example: parent line"))
        self.assertEqual(code, 0, out)
        self.assertEqual(out, {"valid": True, "errors": []})

    def test_code_without_plan_code_names_plan_code(self):
        stages = ["judge", "evaluate-ticket", "code", "prepare-pr", "review-fix", "merge"]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, "code", "takes-met", "plan-code")

    def test_test_and_code_may_share_bookkeeping_sections(self):
        code, out = self.validate(example("## Example: full line"))
        self.assertNoRule(out, "parallel-group")

    def test_a_stage_meets_a_take_it_delivers_itself(self):
        code, out = self.validate(line_of(SHORT))
        self.assertNoRule(out, "takes-met", "prepare-pr")

    def test_accepts_an_auto_stage_after_merge(self):
        line = json.loads(example("## Example: full line"))
        stages = [s for s in line["stages"] if s != "code-docs"]
        stages.append("code-docs")
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 0, out)

    def test_a_sub_issue_group_meets_later_takes_and_returns(self):
        stages = ["judge", "evaluate-ticket", {"group": "sub-issues"}, "merge"]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 0, out)

    def test_usage_without_a_line_file(self):
        result = run()
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stdout.startswith(USAGE))

    def test_usage_on_an_unknown_argument(self):
        result = run("--nope")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stdout.startswith(USAGE))

    def test_usage_when_catalog_has_no_value(self):
        path = self.write("line.json", line_of(SHORT))
        result = run(path, "--catalog")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stdout.startswith(USAGE))

    def test_catalog_flag_replaces_the_default(self):
        catalog = self.catalog_with(remove=["review-fix"])
        code, out = self.validate(line_of(SHORT), catalog)
        self.assertEqual(code, 1)
        self.assertError(out, "review-fix", "known-stage")

    def test_valid_output_is_exact(self):
        path = self.write("line.json", example("## Example: short line"))
        result = run(path)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"valid": True, "errors": []})

    def test_readme_runs_the_validator_tests(self):
        text = (REPO / "README.md").read_text()
        match = re.search(r"## Validate a change\n(.*?)## Falsify a change", text, re.S)
        self.assertIsNotNone(match)
        self.assertIn("python3 skills/assembly-line/scripts/test_validate_line.py", match.group(1))


if __name__ == "__main__":
    unittest.main()
