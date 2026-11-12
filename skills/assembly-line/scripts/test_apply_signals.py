import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "apply-signals.py"
SKILLS = Path(__file__).resolve().parents[2]
CATALOG = SKILLS / "assembly-line" / "references" / "catalog.json"
LINES = SKILLS / "assembly-line" / "references" / "lines"

FEATURE = json.loads((LINES / "feature.json").read_text())["stages"]
SMALL_FIX = json.loads((LINES / "small-fix.json").read_text())["stages"]

CODE_LINE = "- no-screen-change — code — only scripts changed"
SECURITY_LINE = "- touches-security — code — adds a session token check"


def line_of(stages):
    return {"format": "assembly-line/1", "ticket": "BOS-1", "stages": copy.deepcopy(stages)}


def without(stages, name):
    return [item for item in stages if item != name]


class ApplySignals(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def card(self, signals_body, extra=""):
        text = "# Card\n\n## Decisions\n\n- x\n\n"
        if signals_body is not None:
            text += f"## Signals\n\n{signals_body}\n\n"
        text += extra
        path = self.root / "card.md"
        path.write_text(text)
        return path

    def line_file(self, line):
        path = self.root / "line.json"
        path.write_text(line if isinstance(line, str) else json.dumps(line))
        return path

    def catalog_with(self, rows):
        catalog = json.loads(CATALOG.read_text())
        catalog["signals"] = rows
        path = self.root / "catalog.json"
        path.write_text(json.dumps(catalog))
        return path

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              check=False, capture_output=True, text=True, timeout=60)

    def apply(self, signals_body, line, done, catalog=None):
        args = [self.card(signals_body), self.line_file(line), "--done", done]
        if catalog is not None:
            args += ["--catalog", catalog]
        result = self.run_script(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_no_screen_change_removes_ui_review(self):
        report = self.apply(CODE_LINE, line_of(FEATURE), 5)
        self.assertEqual(list(report), ["changed", "line", "applied", "rejected", "skipped"])
        self.assertTrue(report["changed"])
        self.assertEqual(report["line"]["stages"], without(without(FEATURE, "ui-review"), "a11y-check"))
        self.assertEqual(report["applied"][0], {
            "text": CODE_LINE,
            "signal": "no-screen-change",
            "raisedBy": "code",
            "evidence": "only scripts changed",
            "change": "remove",
            "stage": "ui-review",
            "where": None,
        })
        self.assertEqual(report["rejected"], [])
        self.assertEqual(report["skipped"], [])

    def test_no_screen_change_removes_a11y_check(self):
        report = self.apply(CODE_LINE, line_of(FEATURE), 5)
        self.assertTrue(report["changed"], report)
        self.assertNotIn("a11y-check", report["line"]["stages"])
        self.assertNotIn("ui-review", report["line"]["stages"])
        self.assertEqual([(entry["change"], entry["stage"]) for entry in report["applied"]],
                         [("remove", "ui-review"), ("remove", "a11y-check")])
        self.assertEqual(report["rejected"], [])
        self.assertEqual(report["skipped"], [])

    def test_signal_from_another_stage_is_skipped(self):
        report = self.apply("no-screen-change — test — x", line_of(FEATURE), 5)
        self.assertFalse(report["changed"])
        self.assertEqual([entry["reason"] for entry in report["skipped"]], ["no-row"])

    def test_unknown_signal_is_skipped(self):
        report = self.apply("nothing-known — code — x", line_of(FEATURE), 5)
        self.assertFalse(report["changed"])
        self.assertEqual([entry["reason"] for entry in report["skipped"]], ["no-row"])

    def test_stage_already_run_is_not_removed(self):
        report = self.apply(CODE_LINE, line_of(FEATURE), 7)
        self.assertFalse(report["changed"])
        self.assertEqual(report["line"]["stages"], FEATURE)
        self.assertEqual([entry["reason"] for entry in report["skipped"]], ["not-on-line", "not-on-line"])

    def test_applying_twice_changes_nothing(self):
        first = self.apply(CODE_LINE, line_of(FEATURE), 5)
        second = self.apply(CODE_LINE, first["line"], 5)
        self.assertFalse(second["changed"])
        self.assertEqual(second["line"], first["line"])
        self.assertEqual([entry["reason"] for entry in second["skipped"]], ["not-on-line", "not-on-line"])

    def test_card_without_signals_section(self):
        line = line_of(FEATURE)
        report = self.apply(None, line, 5)
        self.assertFalse(report["changed"])
        self.assertEqual(report["applied"], [])
        self.assertEqual(report["rejected"], [])
        self.assertEqual(report["skipped"], [])
        self.assertEqual(report["line"], line)

    def test_comments_and_blanks_are_ignored_and_bad_lines_skipped(self):
        body = "<!-- one -->\n\n<!--\nmulti\nline\n-->\n\njust text"
        report = self.apply(body, line_of(FEATURE), 5)
        self.assertFalse(report["changed"])
        self.assertEqual(len(report["skipped"]), 1)
        self.assertEqual(report["skipped"][0]["reason"], "malformed")
        self.assertIsNone(report["skipped"][0]["signal"])
        self.assertIsNone(report["skipped"][0]["raisedBy"])

    def test_section_ends_at_next_heading(self):
        card = self.root / "card.md"
        card.write_text(f"## Signals\n\nnothing here\n\n## Notes\n\n{CODE_LINE}\n")
        result = self.run_script(card, self.line_file(line_of(FEATURE)), "--done", 5)
        self.assertEqual(result.returncode, 0, result.stdout)
        report = json.loads(result.stdout)
        self.assertFalse(report["changed"])
        self.assertEqual(report["applied"], [])
        self.assertEqual([entry["reason"] for entry in report["skipped"]], ["malformed"])

    def test_remove_a_parallel_branch(self):
        catalog = self.catalog_with([{"signal": "s", "raisedBy": "plan-code", "remove": "test"}])
        report = self.apply("s — plan-code — x", line_of(FEATURE), 3, catalog)
        self.assertTrue(report["changed"], report)
        self.assertEqual(len(report["applied"]), 1)
        self.assertEqual(report["line"]["stages"][3], {"parallel": ["code"]})

    def test_add_after_and_before(self):
        for where in ("after review-fix", "before merge"):
            with self.subTest(where=where):
                rows = [{"signal": "s", "raisedBy": "plan-code", "add": "code-docs", "where": where}]
                catalog = self.catalog_with(rows)
                report = self.apply("s — plan-code — x", line_of(SMALL_FIX), 3, catalog)
                self.assertTrue(report["changed"], report)
                self.assertEqual(report["line"]["stages"], SMALL_FIX[:6] + ["code-docs", "merge"])
                self.assertEqual(report["applied"][0]["change"], "add")
                self.assertEqual(report["applied"][0]["stage"], "code-docs")
                self.assertEqual(report["applied"][0]["where"], where)

    def test_touches_security_adds_security_review_after_code(self):
        report = self.apply(SECURITY_LINE, line_of(FEATURE), 5)
        self.assertTrue(report["changed"], report)
        index = FEATURE.index("ui-review")
        self.assertEqual(report["line"]["stages"], FEATURE[:index] + ["security-review"] + FEATURE[index:])
        self.assertEqual(report["applied"][0]["change"], "add")
        self.assertEqual(report["applied"][0]["stage"], "security-review")
        self.assertEqual(report["applied"][0]["where"], "after code")
        self.assertEqual(report["rejected"], [])
        self.assertEqual(report["skipped"], [])

    def test_touches_security_on_small_fix(self):
        report = self.apply(SECURITY_LINE, line_of(SMALL_FIX), 4)
        self.assertTrue(report["changed"], report)
        self.assertEqual(report["line"]["stages"], SMALL_FIX[:4] + ["security-review"] + SMALL_FIX[4:])
        self.assertEqual(report["rejected"], [])

    def test_touches_security_twice_is_skipped(self):
        first = self.apply(SECURITY_LINE, line_of(FEATURE), 5)
        second = self.apply(SECURITY_LINE, first["line"], 5)
        self.assertFalse(second["changed"])
        self.assertEqual(second["line"], first["line"])
        self.assertEqual([entry["reason"] for entry in second["skipped"]], ["already-on-line"])

    def test_before_anchor_already_run_is_missing(self):
        rows = [{"signal": "s", "raisedBy": "code", "add": "code-docs", "where": "before code"}]
        line = line_of(SMALL_FIX)
        report = self.apply("s — code — x", line, 4, self.catalog_with(rows))
        self.assertFalse(report["changed"])
        self.assertEqual(report["line"], line)
        self.assertEqual([entry["reason"] for entry in report["skipped"]], ["anchor-missing"])

    def test_after_anchor_already_run_goes_first_in_the_rest(self):
        rows = [{"signal": "s", "raisedBy": "code", "add": "ui-review", "where": "after code"}]
        report = self.apply("s — code — x", line_of(SMALL_FIX), 4, self.catalog_with(rows))
        self.assertTrue(report["changed"], report)
        self.assertEqual(report["line"]["stages"], SMALL_FIX[:4] + ["ui-review"] + SMALL_FIX[4:])

    def test_add_already_on_line_is_skipped(self):
        rows = [{"signal": "s", "raisedBy": "plan-code", "add": "code", "where": "after plan-code"}]
        report = self.apply("s — plan-code — x", line_of(FEATURE), 2, self.catalog_with(rows))
        self.assertFalse(report["changed"])
        self.assertEqual([entry["reason"] for entry in report["skipped"]], ["already-on-line"])

    def test_add_anchor_missing_is_skipped(self):
        rows = [{"signal": "s", "raisedBy": "plan-code", "add": "code-docs", "where": "after ui-review"}]
        report = self.apply("s — plan-code — x", line_of(SMALL_FIX), 3, self.catalog_with(rows))
        self.assertFalse(report["changed"])
        self.assertEqual([entry["reason"] for entry in report["skipped"]], ["anchor-missing"])

    def test_removing_a_kept_stage_is_rejected(self):
        rows = [
            {"signal": "drop-merge", "raisedBy": "plan-code", "remove": "merge"},
            {"signal": "drop-judge", "raisedBy": "plan-code", "remove": "judge"},
        ]
        line = line_of(SMALL_FIX)
        report = self.apply("drop-merge — plan-code — x\ndrop-judge — plan-code — y",
                            line, 0, self.catalog_with(rows))
        self.assertFalse(report["changed"])
        self.assertEqual(report["line"], line)
        self.assertEqual(report["applied"], [])
        self.assertEqual(len(report["rejected"]), 2)
        for entry in report["rejected"]:
            self.assertEqual([error["rule"] for error in entry["errors"]], ["kept-stage"])

    def test_a_change_the_validator_rejects_leaves_the_line(self):
        rows = [{"signal": "skip-pr", "raisedBy": "plan-code", "remove": "prepare-pr"}]
        line = line_of(FEATURE)
        report = self.apply("skip-pr — plan-code — x", line, 3, self.catalog_with(rows))
        self.assertFalse(report["changed"])
        self.assertEqual(report["line"], line)
        self.assertEqual(report["applied"], [])
        self.assertEqual(len(report["rejected"]), 1)
        rules = [error["rule"] for error in report["rejected"][0]["errors"]]
        self.assertIn("takes-met", rules)

    def test_a_rejected_change_keeps_later_ones(self):
        rows = json.loads(CATALOG.read_text())["signals"]
        rows = rows + [{"signal": "skip-pr", "raisedBy": "plan-code", "remove": "prepare-pr"}]
        body = "skip-pr — plan-code — x\nno-screen-change — code — y"
        report = self.apply(body, line_of(FEATURE), 3, self.catalog_with(rows))
        stages = report["line"]["stages"]
        self.assertNotIn("ui-review", stages)
        self.assertNotIn("a11y-check", stages)
        self.assertIn("prepare-pr", stages)
        self.assertEqual(len(report["applied"]), 2)
        self.assertEqual(len(report["rejected"]), 1)

    def test_usage_and_fatal_errors(self):
        card = self.card(CODE_LINE)
        line = self.line_file(line_of(FEATURE))
        with self.subTest("no --done"):
            result = self.run_script(card, line)
            self.assertEqual(result.returncode, 2)
            self.assertTrue(result.stdout.startswith("usage: apply-signals.py"))
        with self.subTest("negative --done"):
            result = self.run_script(card, line, "--done", "-1")
            self.assertEqual(result.returncode, 2)
        with self.subTest("line with from"):
            bad = self.line_file({**line_of(FEATURE), "from": "feature"})
            result = self.run_script(card, bad, "--done", 5)
            self.assertEqual(result.returncode, 1)
            self.assertIn("error", json.loads(result.stdout))
        with self.subTest("missing card"):
            result = self.run_script(self.root / "none.md", line, "--done", 5)
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
