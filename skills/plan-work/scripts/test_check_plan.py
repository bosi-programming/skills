import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_plan import lint

SCRIPT = Path(__file__).resolve().parent / "check_plan.py"


def criteria(*lines):
    return "\n".join(f"- [ ] #{n} {line}" for n, line in enumerate(lines, 1))


def sub(identifier, repo="api", blocked_by=(), criteria_text=None, extra=""):
    body = "\n\n".join([
        "## What\n\nAdds the export endpoint.",
        "## Technical design\n\n- Approach: a new route." + extra,
        f"## Repos and key paths\n\n- Repo: `{repo}`\n- `src/export.ts`",
        "## Acceptance criteria\n\n" + (criteria_text or criteria("[unit] The export builds one CSV row per order.")),
    ])
    return {"identifier": identifier, "title": f"feat(export): part {identifier}", "description": body, "blockedBy": list(blocked_by)}


def issue(identifier="NEW-1", children=None, criteria_text=None, design_extra="", extra_sections="", blocked_by=()):
    children = [sub("NEW-2"), sub("NEW-3", repo="web", blocked_by=["NEW-2"])] if children is None else children
    contracts = "\n\n### Contracts\n\n- `GET /export` returns `text/csv`." if len(children) >= 2 else ""
    repos = "" if children else "\n\n## Repos and key paths\n\n- Repo: `api`\n- `src/export.ts`"
    default = criteria("[ui] As a store owner on Orders, when I click Export, then a CSV downloads.") if children else criteria("[unit] The export builds one CSV row per order.")
    body = "\n\n".join([
        "## What\n\nStore owners export their orders as CSV.",
        "## How this impacts the final user\n\nOwners stop copying orders by hand.",
        "## Technical design\n\n- Approach: build the CSV on the server." + contracts + design_extra,
        "## Out of scope\n\n- PDF export.",
        "## Acceptance criteria\n\n" + (criteria_text or default),
    ]) + repos + extra_sections
    return {"identifier": identifier, "title": "Store owners export orders as CSV", "description": body, "children": children, "blockedBy": list(blocked_by)}


def rules(result):
    return {gap["rule"] for gap in result["gaps"]}


class ReadyPlan(unittest.TestCase):
    def test_ready_issue_with_sub_issues(self):
        result = lint({"issues": [issue()]})
        self.assertEqual(result["gaps"], [])
        self.assertTrue(result["ready"])

    def test_ready_issue_built_directly(self):
        self.assertEqual(lint(issue(children=[]))["gaps"], [])


class RequiredSections(unittest.TestCase):
    def test_issue_missing_out_of_scope(self):
        story = issue()
        story["description"] = story["description"].replace("## Out of scope", "## Notes")
        self.assertIn("required-sections", rules(lint(story)))

    def test_sub_issue_missing_repos(self):
        child = sub("NEW-2")
        child["description"] = child["description"].replace("## Repos and key paths", "## Files")
        self.assertIn("required-sections", rules(lint(issue(children=[child, sub("NEW-3", repo="web")]))))

    def test_direct_issue_needs_repos(self):
        story = issue(children=[])
        story["description"] = story["description"].replace("## Repos and key paths", "## Files")
        self.assertIn("required-sections", rules(lint(story)))


class CriteriaFormat(unittest.TestCase):
    def test_no_criteria(self):
        self.assertIn("criteria-format", rules(lint(issue(children=[], criteria_text="Works."))))

    def test_missing_tag(self):
        text = "- [ ] #1 The export works."
        self.assertIn("criteria-format", rules(lint(issue(children=[], criteria_text=text))))

    def test_unknown_tag(self):
        text = "- [ ] #1 [vibes] The export works."
        self.assertIn("criteria-format", rules(lint(issue(children=[], criteria_text=text))))

    def test_numbers_out_of_order(self):
        text = "- [ ] #1 [unit] One row per order.\n- [ ] #3 [unit] Header row first."
        self.assertIn("criteria-format", rules(lint(issue(children=[], criteria_text=text))))

    def test_plain_bullet_is_a_bad_criterion(self):
        text = "- [ ] #1 [unit] One row per order.\n- Header row first."
        self.assertIn("criteria-format", rules(lint(issue(children=[], criteria_text=text))))


class IssueLevelTag(unittest.TestCase):
    def test_unit_on_issue_with_sub_issues(self):
        text = criteria("[unit] The export builds one CSV row per order.")
        self.assertIn("issue-level-tag", rules(lint(issue(criteria_text=text))))

    def test_unit_on_direct_issue_is_fine(self):
        self.assertNotIn("issue-level-tag", rules(lint(issue(children=[]))))


class ManualReason(unittest.TestCase):
    def test_manual_without_reason(self):
        text = criteria("[manual] Ana checks the CSV in Excel.")
        self.assertIn("manual-reason", rules(lint(issue(children=[], criteria_text=text))))

    def test_manual_with_reason(self):
        text = criteria("[manual] Ana checks the CSV in Excel, because no test runs Excel.")
        self.assertNotIn("manual-reason", rules(lint(issue(children=[], criteria_text=text))))


class Placeholder(unittest.TestCase):
    def test_missing_marker(self):
        story = issue(design_extra="\n- Data: <missing: table name, see Q1>")
        self.assertIn("placeholder", rules(lint(story)))

    def test_template_placeholder(self):
        story = issue(design_extra="\n- Data: <the table>")
        self.assertIn("placeholder", rules(lint(story)))

    def test_tbd(self):
        self.assertIn("placeholder", rules(lint(issue(design_extra="\n- Data: TBD"))))

    def test_placeholder_in_sub_issue(self):
        children = [sub("NEW-2", extra="\n- Data: TODO"), sub("NEW-3", repo="web")]
        self.assertIn("placeholder", rules(lint(issue(children=children))))


class SingleSubIssue(unittest.TestCase):
    def test_one_sub_issue(self):
        self.assertIn("single-sub-issue", rules(lint(issue(children=[sub("NEW-2")]))))


class OneRepo(unittest.TestCase):
    def test_sub_issue_with_two_repos(self):
        child = sub("NEW-2")
        child["description"] = child["description"].replace("- Repo: `api`", "- Repo: `api`\n- Repo: `web`")
        self.assertIn("one-repo", rules(lint(issue(children=[child, sub("NEW-3", repo="web")]))))

    def test_sub_issue_with_no_repo(self):
        child = sub("NEW-2")
        child["description"] = child["description"].replace("- Repo: `api`\n", "")
        self.assertIn("one-repo", rules(lint(issue(children=[child, sub("NEW-3", repo="web")]))))


class BlocksDag(unittest.TestCase):
    def test_cycle_between_sub_issues(self):
        children = [sub("NEW-2", blocked_by=["NEW-3"]), sub("NEW-3", repo="web", blocked_by=["NEW-2"])]
        self.assertIn("blocks-dag", rules(lint(issue(children=children))))

    def test_sub_issue_blocked_by_other_parent(self):
        children = [sub("NEW-2", blocked_by=["NEW-9"]), sub("NEW-3", repo="web")]
        self.assertIn("blocks-dag", rules(lint(issue(children=children))))

    def test_cycle_between_issues(self):
        plan = {"issues": [issue("NEW-1", children=[], blocked_by=["NEW-5"]), issue("NEW-5", children=[], blocked_by=["NEW-1"])]}
        self.assertIn("blocks-dag", rules(lint(plan)))


class Contracts(unittest.TestCase):
    def test_two_sub_issues_without_contracts(self):
        story = issue()
        story["description"] = story["description"].replace("### Contracts", "### Notes")
        self.assertIn("contracts", rules(lint(story)))


FLAG = "\n\n### Feature flags\n\n- `orders-csv-export`"
FEATURE = "\n\n## Before → after\n\nNo export → an Export button."
OFF = "[ui] As a store owner on Orders, with `orders-csv-export` off, nothing changes."
ON = "[ui] As a store owner on Orders, when I click Export, then a CSV downloads."
REMOVAL = issue(
    "NEW-9",
    children=[],
    extra_sections="\n\n## Removes\n\n- The `orders-csv-export` flag.",
    blocked_by=["NEW-1"],
)


class FeatureFlags(unittest.TestCase):
    def test_feature_without_flag(self):
        plan = {"issues": [issue(extra_sections=FEATURE)]}
        self.assertIn("flag-parity", rules(lint(plan, feature_flags=True)))

    def test_flag_without_off_criterion(self):
        plan = {"issues": [issue(design_extra=FLAG, extra_sections=FEATURE), REMOVAL]}
        self.assertIn("flag-parity", rules(lint(plan, feature_flags=True)))

    def test_flag_without_removal(self):
        story = issue(design_extra=FLAG, extra_sections=FEATURE, criteria_text=criteria(ON, OFF))
        self.assertIn("flag-removal", rules(lint({"issues": [story]}, feature_flags=True)))

    def test_flagged_feature_ready(self):
        story = issue(design_extra=FLAG, extra_sections=FEATURE, criteria_text=criteria(ON, OFF))
        found = rules(lint({"issues": [story, REMOVAL]}, feature_flags=True))
        self.assertNotIn("flag-parity", found)
        self.assertNotIn("flag-removal", found)

    def test_removal_issue_follows_template(self):
        bare = {"identifier": "NEW-9", "description": "## Removes\n\n- The `orders-csv-export` flag.", "children": []}
        self.assertIn("required-sections", rules(lint(bare)))

    def test_rules_off_without_option(self):
        found = rules(lint({"issues": [issue(extra_sections=FEATURE)]}))
        self.assertNotIn("flag-parity", found)


class Cli(unittest.TestCase):
    def run_cli(self, data, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write(data if isinstance(data, str) else json.dumps(data))
        return subprocess.run([sys.executable, str(SCRIPT), *args, handle.name], capture_output=True, text=True, check=False)

    def test_ready_exits_zero(self):
        done = self.run_cli({"issues": [issue()]})
        self.assertEqual(done.returncode, 0)
        self.assertTrue(json.loads(done.stdout)["ready"])

    def test_not_ready_exits_one(self):
        done = self.run_cli(issue(children=[sub("NEW-2")]))
        self.assertEqual(done.returncode, 1)
        self.assertFalse(json.loads(done.stdout)["ready"])

    def test_bad_input_exits_two(self):
        self.assertEqual(self.run_cli("{not json").returncode, 2)

    def test_missing_description_exits_two(self):
        self.assertEqual(self.run_cli({"identifier": "NEW-1", "children": []}).returncode, 2)

    def test_feature_flags_option(self):
        done = self.run_cli({"issues": [issue(extra_sections=FEATURE)]}, "--feature-flags")
        self.assertIn("flag-parity", {gap["rule"] for gap in json.loads(done.stdout)["gaps"]})


if __name__ == "__main__":
    unittest.main()
