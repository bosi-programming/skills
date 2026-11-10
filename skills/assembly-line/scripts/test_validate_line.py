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
LINES = SKILLS / "assembly-line" / "references" / "lines"

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

    def validate(self, line, catalog=None, lines=None):
        args = [self.write("line.json", line)]
        if catalog is not None:
            args += ["--catalog", self.write("catalog.json", catalog)]
        if lines is not None:
            args += ["--lines", lines]
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

    def test_rejects_a_catalog_with_a_malformed_stage(self):
        base = real_catalog()["stages"]["judge"]
        broken = {
            "stage not an object": 5,
            "takes not a list": {**base, "takes": "x"},
            "takes holds a non-string": {**base, "takes": [1]},
            "delivers not an object": {**base, "delivers": []},
            "sections not a list": {**base, "delivers": {"sections": "x"}},
            "fields not a list": {**base, "delivers": {"fields": 3}},
            "return not an object": {**base, "return": []},
            "verdict not an object": {**base, "return": {"blocked": 1}},
        }
        for name, entry in broken.items():
            with self.subTest(case=name):
                catalog = self.catalog_with(add={"judge": entry})
                result = run(self.write("line.json", line_of(SHORT)),
                             "--catalog", self.write("catalog.json", catalog))
                self.assertEqual(result.returncode, 1, result.stderr)
                out = json.loads(result.stdout)
                self.assertError(out, None, "catalog-parses")

    def test_rejects_a_sub_issue_group_after_merge(self):
        stages = ["judge", "evaluate-ticket", "merge", {"group": "sub-issues"}]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, None, "auto-after-merge", "sub-issue group")

    def test_rejects_a_parallel_group_as_the_first_item(self):
        stages = [{"parallel": ["judge", "evaluate-ticket"]}, "merge"]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, None, "first-judge", "judge")

    def test_rejects_a_sub_issue_group_as_the_first_item(self):
        stages = [{"group": "sub-issues"}, "merge"]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 1)
        self.assertError(out, None, "first-judge", "judge")

    def test_accepts_the_stage_object_form(self):
        stages = SHORT[:-1] + [{"stage": "merge", "with": {}}]
        code, out = self.validate(line_of(stages))
        self.assertEqual(code, 0, out)

    def test_rejects_a_stage_object_of_the_wrong_shape(self):
        cases = {
            "with not an object": {"stage": "merge", "with": 1},
            "extra key": {"stage": "merge", "foo": 1},
        }
        for name, item in cases.items():
            with self.subTest(case=name):
                code, out = self.validate(line_of(["judge", "evaluate-ticket", item]))
                self.assertEqual(code, 1)
                self.assertError(out, None, "line-shape", "item 3")

    def test_an_unknown_first_stage_reports_only_known_stage(self):
        code, out = self.validate(line_of(["no-such-stage", "merge"]))
        self.assertEqual(code, 1)
        self.assertError(out, "no-such-stage", "known-stage")
        self.assertNoRule(out, "first-judge")

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

    def from_line(self, saved, **extra):
        return {"format": "assembly-line/1", "ticket": "BOS-1", "from": saved, **extra}

    def saved(self, name):
        return json.loads((LINES / f"{name}.json").read_text())

    def test_every_saved_line_passes(self):
        paths = sorted(LINES.glob("*.json"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(line=path.name):
                result = run(path)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertEqual(json.loads(result.stdout), {"valid": True, "errors": []})

    def test_saved_lines_are_the_four(self):
        expected = {
            "feature": ["judge", "evaluate-ticket", "plan-code", {"parallel": ["test", "code"]}, "code",
                        "ui-review", "prepare-pr", "review-fix", "code-docs", "merge"],
            "bug": ["judge", "reproduce", "evaluate-ticket", "plan-code", {"parallel": ["test", "code"]},
                    "code", "ui-review", "prepare-pr", "review-fix", "code-docs", "merge"],
            "small-fix": ["judge", "evaluate-ticket", "plan-code", "code", "prepare-pr", "review-fix", "merge"],
            "parent": ["judge", "contract", {"group": "sub-issues"}, "integrate", "qa", "proof",
                       "review-request", "merge"],
        }
        self.assertEqual(sorted(path.stem for path in LINES.glob("*.json")), sorted(expected))
        for name, stages in expected.items():
            with self.subTest(line=name):
                self.assertEqual(self.saved(name),
                                 {"format": "assembly-line/1", "name": name, "stages": stages})

    def test_a_saved_line_has_no_line_key(self):
        result = run(LINES / "feature.json")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout), {"valid": True, "errors": []})

    def test_from_feature_drop_ui_review_expands(self):
        code, out = self.validate(self.from_line("feature", drop=["ui-review"]))
        self.assertEqual(code, 0, out)
        stages = [s for s in self.saved("feature")["stages"] if s != "ui-review"]
        self.assertEqual(out.get("line"), {"format": "assembly-line/1", "ticket": "BOS-1", "stages": stages})
        self.assertEqual(list(out), ["valid", "errors", "line"])

    def test_drop_merge_is_rejected(self):
        code, out = self.validate(self.from_line("feature", drop=["merge"]))
        self.assertEqual(code, 1)
        self.assertError(out, "merge", "line-edit")
        self.assertNotIn("line", out)

    def test_drop_judge_is_rejected(self):
        code, out = self.validate(self.from_line("feature", drop=["judge"]))
        self.assertEqual(code, 1)
        self.assertError(out, "judge", "line-edit")

    def test_drop_a_stage_not_on_the_saved_line(self):
        code, out = self.validate(self.from_line("small-fix", drop=["ui-review"]))
        self.assertEqual(code, 1)
        self.assertError(out, "ui-review", "line-edit")

    def test_drop_a_parallel_branch(self):
        code, out = self.validate(self.from_line("feature", drop=["test"]))
        self.assertEqual(code, 0, out)
        stages = out["line"]["stages"]
        self.assertIn({"parallel": ["code"]}, stages)
        self.assertNotIn({"parallel": ["test", "code"]}, stages)

    def test_drop_every_branch_removes_the_group(self):
        saved = {"format": "assembly-line/1", "name": "grouped",
                 "stages": ["judge", "evaluate-ticket", "plan-code", {"parallel": ["test", "code"]},
                            "prepare-pr", "review-fix", "merge"]}
        folder = self.root / "lines"
        folder.mkdir()
        (folder / "grouped.json").write_text(json.dumps(saved))
        code, out = self.validate(self.from_line("grouped", drop=["test", "code"]), lines=folder)
        self.assertEqual(out["line"]["stages"],
                         ["judge", "evaluate-ticket", "plan-code", "prepare-pr", "review-fix", "merge"])

    def test_add_after_the_last_top_level_stage(self):
        code, out = self.validate(self.from_line("small-fix", add=[{"after": "code", "item": "ui-review"}]))
        self.assertEqual(code, 0, out)
        stages = out["line"]["stages"]
        self.assertEqual(stages[stages.index("code") + 1], "ui-review")
        self.assertEqual(stages.count("ui-review"), 1)

    def test_adds_apply_in_order(self):
        adds = [{"after": "code", "item": "ui-review"}, {"after": "ui-review", "item": "code-docs"}]
        code, out = self.validate(self.from_line("small-fix", add=adds))
        stages = out["line"]["stages"]
        at = stages.index("code")
        self.assertEqual(stages[at:at + 3], ["code", "ui-review", "code-docs"])

    def test_add_after_a_stage_not_on_the_line(self):
        code, out = self.validate(self.from_line("small-fix", add=[{"after": "qa", "item": "ui-review"}]))
        self.assertEqual(code, 1)
        self.assertError(out, "qa", "line-edit")

    def test_unknown_saved_line(self):
        code, out = self.validate(self.from_line("nope"))
        self.assertEqual(code, 1)
        self.assertError(out, None, "saved-line", "from")
        self.assertNotIn("line", out)

    def test_from_with_a_bad_name(self):
        code, out = self.validate(self.from_line("../catalog"))
        self.assertEqual(code, 1)
        self.assertError(out, None, "saved-line")

    def test_from_line_shapes(self):
        stages = ["judge", "merge"]
        item = {"after": "code", "item": "ui-review"}
        cases = {
            "from with stages": self.from_line("feature", stages=stages),
            "drop without from": {**line_of(stages), "drop": ["code"]},
            "add without from": {**line_of(stages), "add": [item]},
            "ticket and name": {"format": "assembly-line/1", "ticket": "BOS-1", "name": "x", "stages": stages},
            "name with from": {"format": "assembly-line/1", "name": "x", "from": "feature"},
            "drop not strings": self.from_line("feature", drop=[1]),
            "drop not a list": self.from_line("feature", drop="code"),
            "add missing after": self.from_line("feature", add=[{"item": "ui-review"}]),
            "add missing item": self.from_line("feature", add=[{"after": "code"}]),
            "add another key": self.from_line("feature", add=[{**item, "extra": 1}]),
            "from empty": self.from_line(""),
        }
        for label, line in cases.items():
            with self.subTest(case=label):
                code, out = self.validate(line)
                self.assertEqual(code, 1, out)
                self.assertTrue(out["errors"], out)
                self.assertEqual({e["rule"] for e in out["errors"]}, {"line-shape"}, out)

    def test_expanded_line_runs_every_rule(self):
        code, out = self.validate(self.from_line("feature", drop=["plan-code"]))
        self.assertEqual(code, 1)
        self.assertRegex(json.dumps(out["errors"]), "takes-met")
        self.assertIn("line", out)

    def test_lines_flag_replaces_the_default(self):
        folder = self.root / "lines"
        folder.mkdir()
        custom = {"format": "assembly-line/1", "name": "feature", "stages": SHORT}
        (folder / "feature.json").write_text(json.dumps(custom))
        code, out = self.validate(self.from_line("feature"), lines=folder)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["line"]["stages"], SHORT)
        result = run(self.write("line.json", self.from_line("feature")), "--lines")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stdout.startswith(USAGE))

    def test_from_example_passes(self):
        code, out = self.validate(example("## Example: line from a saved line"))
        self.assertEqual(code, 0, out)

    def test_readme_runs_the_validator_tests(self):
        text = (REPO / "README.md").read_text()
        match = re.search(r"## Validate a change\n(.*?)## Falsify a change", text, re.S)
        self.assertIsNotNone(match)
        self.assertIn("python3 skills/assembly-line/scripts/test_validate_line.py", match.group(1))


if __name__ == "__main__":
    unittest.main()
