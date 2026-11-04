import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "build-catalog.py"
SKILLS = Path(__file__).resolve().parents[2]
REPO = SKILLS.parent

VALID = {
    "spec": "../assembly-line/references/stage-spec.md",
    "takes": ["task"],
    "delivers": {
        "sections": ["## Problem", "## Goal & measure", "## Decisions", "## Open Questions"],
        "fields": ["phase", "phasesCompleted", "lastTouched"],
        "verdicts": ["done", "blocked"],
    },
    "return": {"blocked": {"to": "evaluate-ticket", "limit": 0, "past": "needs-input"}},
    "signals": [],
    "gate": "auto",
}

UNKNOWN = "FAIL signals-known-stage no-such-stage"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          check=False, capture_output=True, text=True)


class BuildCatalog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.catalog = self.root / "assembly-line" / "references" / "catalog.json"
        self.signals({"signals": []})

    def tearDown(self):
        self.tmp.cleanup()

    def stage(self, name, body=None, skill_md=True):
        folder = self.root / name
        folder.mkdir(parents=True, exist_ok=True)
        if skill_md:
            (folder / "SKILL.md").write_text(f"# {name}\n")
        if body is False:
            return
        if body is None:
            body = VALID
        text = body if isinstance(body, str) else json.dumps(body)
        (folder / "stage.json").write_text(text)

    def signals(self, content):
        path = self.root / "assembly-line" / "references" / "signals.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content))

    def build(self):
        return run("--skills", self.root)

    def check(self):
        return run("--check", "--skills", self.root)

    def written(self):
        return json.loads(self.catalog.read_text())

    def two_stages(self):
        self.stage("alpha")
        self.stage("beta")

    def test_lists_every_stage_skill(self):
        self.stage("beta")
        self.stage("alpha")
        self.build()
        self.assertEqual(list(self.written()["stages"]), ["alpha", "beta"])

    def test_skips_a_skill_without_stage_json(self):
        self.stage("alpha")
        self.stage("plain", body=False)
        self.build()
        self.assertEqual(list(self.written()["stages"]), ["alpha"])

    def test_skips_a_stage_json_without_skill_md(self):
        self.stage("alpha")
        self.stage("orphan", skill_md=False)
        self.build()
        self.assertEqual(list(self.written()["stages"]), ["alpha"])

    def test_copies_each_stage_json_as_it_stands(self):
        body = {"zeta": 1, "alpha": {"b": 2, "a": 1}, "gate": "auto"}
        self.stage("alpha", body)
        self.build()
        entry = self.written()["stages"]["alpha"]
        self.assertEqual(entry, body)
        self.assertEqual(list(entry), ["zeta", "alpha", "gate"])
        self.assertEqual(list(entry["alpha"]), ["b", "a"])

    def test_build_reports_the_stage_count(self):
        self.two_stages()
        result = self.build()
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout, r"wrote .*assembly-line/references/catalog\.json: 2 stages")
        catalog = self.written()
        self.assertEqual(catalog["format"], "assembly-line-catalog/1")
        self.assertEqual(catalog["generatedBy"], "skills/assembly-line/scripts/build-catalog.py")

    def test_check_passes_after_a_build(self):
        self.two_stages()
        self.build()
        result = self.check()
        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS catalog-current", result.stdout)

    def test_check_fails_after_a_stage_json_changes(self):
        self.two_stages()
        self.build()
        before = self.catalog.read_bytes()
        self.stage("beta", {**VALID, "gate": "human"})
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL catalog-current beta: changed since catalog was written", result.stdout)
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_check_passes_once_rebuilt(self):
        self.two_stages()
        self.build()
        self.stage("beta", {**VALID, "gate": "human"})
        self.assertEqual(self.build().returncode, 0)
        self.assertEqual(self.check().returncode, 0)

    def test_check_names_an_added_and_a_removed_stage(self):
        self.two_stages()
        self.build()
        self.stage("gamma")
        (self.root / "alpha" / "stage.json").unlink()
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL catalog-current gamma: in tree but missing from catalog", result.stdout)
        self.assertIn("FAIL catalog-current alpha: in catalog but not in tree", result.stdout)

    def test_check_fails_when_the_catalog_is_missing(self):
        self.two_stages()
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL catalog-exists", result.stdout)

    def test_check_fails_when_signals_change(self):
        self.two_stages()
        self.build()
        self.signals({"signals": [{"signal": "s", "raisedBy": "alpha", "add": "beta",
                                   "where": "after alpha"}]})
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL catalog-current signals: changed since catalog was written", result.stdout)

    def test_merges_signal_rows(self):
        self.two_stages()
        row = {"signal": "s", "raisedBy": "alpha", "add": "beta", "where": "after alpha"}
        self.signals({"signals": [row]})
        result = self.build()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.written()["signals"], [row])

    def signal_fails(self, **fields):
        self.two_stages()
        self.signals({"signals": [{"signal": "s", **fields}]})
        return self.build()

    def test_fails_naming_an_unknown_raised_by(self):
        result = self.signal_fails(raisedBy="no-such-stage")
        self.assertEqual(result.returncode, 1)
        self.assertIn(UNKNOWN, result.stdout)

    def test_fails_naming_an_unknown_added_stage(self):
        result = self.signal_fails(add="no-such-stage")
        self.assertEqual(result.returncode, 1)
        self.assertIn(UNKNOWN, result.stdout)

    def test_fails_naming_an_unknown_removed_stage(self):
        result = self.signal_fails(remove="no-such-stage")
        self.assertEqual(result.returncode, 1)
        self.assertIn(UNKNOWN, result.stdout)

    def test_fails_naming_an_unknown_where_stage(self):
        result = self.signal_fails(where="after no-such-stage")
        self.assertEqual(result.returncode, 1)
        self.assertIn(UNKNOWN, result.stdout)

    def test_fails_on_a_where_without_after_or_before(self):
        result = self.signal_fails(where="next to code")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL signals-where", result.stdout)

    def test_check_also_fails_on_an_unknown_stage(self):
        self.two_stages()
        self.build()
        before = self.catalog.read_bytes()
        self.signals({"signals": [{"signal": "s", "raisedBy": "no-such-stage"}]})
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL signals-known-stage", result.stdout)
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_check_passes_on_the_real_tree(self):
        result = run("--check")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_real_signals_table_is_empty(self):
        path = SKILLS / "assembly-line" / "references" / "signals.json"
        self.assertEqual(json.loads(path.read_text()), {"signals": []})

    def test_readme_validates_the_catalog(self):
        text = (REPO / "README.md").read_text()
        match = re.search(r"## Validate a change\n(.*?)## Falsify a change", text, re.S)
        self.assertIsNotNone(match)
        block = match.group(1)
        self.assertIn("python3 skills/assembly-line/scripts/build-catalog.py --check", block)
        self.assertIn("python3 skills/assembly-line/scripts/test_build_catalog.py", block)

    def test_fails_naming_a_stage_json_that_does_not_parse(self):
        self.stage("alpha", "{not json")
        result = self.build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL stage-parses alpha", result.stdout)
        self.assertFalse(self.catalog.exists())

    def test_fails_when_a_stage_json_is_not_an_object(self):
        self.stage("alpha", "[]")
        result = self.build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL stage-parses alpha", result.stdout)

    def test_fails_when_signals_json_is_missing(self):
        self.stage("alpha")
        (self.root / "assembly-line" / "references" / "signals.json").unlink()
        result = self.build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL signals-parses signals.json", result.stdout)

    def test_fails_when_signals_json_has_the_wrong_shape(self):
        self.stage("alpha")
        for content in ("[]", '{"signals": {}}', '{"signals": ["x"]}'):
            with self.subTest(content=content):
                self.signals(content)
                result = self.build()
                self.assertEqual(result.returncode, 1)
                self.assertIn("FAIL signals-parses", result.stdout)

    def test_failed_build_leaves_the_catalog_alone(self):
        self.two_stages()
        self.build()
        before = self.catalog.read_bytes()
        self.stage("beta", "{not json")
        result = self.build()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_usage_on_an_unknown_argument(self):
        result = run("--nope")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stdout.startswith("usage: build-catalog.py"))

    def test_usage_when_skills_has_no_value(self):
        result = run("--skills")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stdout.startswith("usage: build-catalog.py"))

    def test_fails_when_a_row_key_is_not_a_string(self):
        self.stage("alpha")
        for key in ("raisedBy", "add", "remove", "where"):
            with self.subTest(key=key):
                self.signals({"signals": [{key: 1}]})
                result = self.build()
                self.assertEqual(result.returncode, 1)
                self.assertIn(f"FAIL signals-parses signals.json: row 1 {key} must be a string", result.stdout)

    def test_check_fails_when_the_catalog_does_not_parse(self):
        self.two_stages()
        self.build()
        self.catalog.write_text("{not json")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL catalog-current catalog.json: does not parse", result.stdout)

    def test_check_fails_when_the_catalog_differs_only_in_bytes(self):
        self.two_stages()
        self.build()
        self.catalog.write_text(json.dumps(self.written()))
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL catalog-current catalog.json: differs from the build", result.stdout)


if __name__ == "__main__":
    unittest.main()
