import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SKILLS = SKILL.parent
REPO = SKILLS.parent
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
PLATING = SKILLS / "prepare-pr" / "SKILL.md"
DSH_TEST = REPO / "dsh" / "index.test.mjs"

PRIVATE = ["~/dev/", "aopost", "felipe", "linear-server", "goto-", "cw new", "controller", "ao-adr", "🐞"]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def read(path):
    return path.read_text() if path.exists() else ""


def flatten(text):
    return " ".join(text.split()).lower()


def block(text, start, stop_pattern):
    begin = text.find(start)
    if begin < 0:
        return ""
    rest = text[begin + len(start):]
    stop = re.search(stop_pattern, rest, re.MULTILINE)
    return rest[:stop.start()] if stop else rest


def check_all(name, text, *phrases):
    lowered = flatten(text)
    missing = [phrase for phrase in phrases if phrase.lower() not in lowered]
    check(name, not missing, f"missing: {missing}" if missing else "")


def check_none(name, text, *phrases):
    lowered = flatten(text)
    present = [phrase for phrase in phrases if phrase.lower() in lowered]
    check(name, not present, f"must not say: {present}" if present else "")


skill = read(SKILL_MD)
readme = read(README)

check("skill-exists", re.search(r"^name: open-restaurant$", skill, re.MULTILINE), "skills/open-restaurant/SKILL.md must declare name: open-restaurant")

sections = {
    "settings": "## Settings",
    "order": "## 1. Take the order",
    "line": "## 2. Run the parent's line",
    "plan": "## 3. Seat the cards",
    "cards": "## 4. Cook the cards",
    "unblock": "## 5. Early unblock",
    "close": "## 6. Close the cards",
    "stops": "## 7. Stops and resume",
    "report": "## 8. Report",
}
text = {key: block(skill, heading, r"^## ") for key, heading in sections.items()}
for key, heading in sections.items():
    check(f"section:{key}", text[key], f"missing `{heading}`")

check_none("removed-sections", skill,
           "## 2. readiness gate", "## 3. contract", "## 8. integrate, qa and fix",
           "## 9. proof", "## 10. review gate", "## 11. merge gate")
check_none("no-review-gate", skill, "`gate: review`")
check_all("drives-assembly-line", skill, "`../assembly-line/SKILL.md`", "`plan-assembly-line`")
check_none("no-relay", skill, "recipe-relay", "`../feature-recipe/")
check_none("no-fixed-stages", skill,
           "`../judge/SKILL.md`", "`../contract/SKILL.md`", "`../reproduce/SKILL.md`", "`../integrate/SKILL.md`",
           "`../qa/SKILL.md`", "`../proof/SKILL.md`", "`../review-request/SKILL.md`", "`../merge/SKILL.md`")
check_all("settings-body", text["settings"], "`## open-restaurant`", "`../setup/references/config.md`")
check_all("settings-keys", text["settings"],
          "`open-restaurant.repoByLabel`", "`open-restaurant.implementedState`", "`open-restaurant.doneState`",
          "`open-restaurant.envName`", "`open-restaurant.reviewChannel`", "`open-restaurant.judgeModel`",
          "`open-restaurant.qaModel`", "`open-restaurant.fixModel`")

check_all("service-card", text["order"], ".service.md`", "service card")
check_all("service-card-row", text["order"], "| id | repo | branch | base | blocked by | line | card | status | PR |")
check_all("no-worktrees", text["order"], "never creates or removes", "worktree")
check_all("missing-checkout-stops", text["order"], "missing", "stop")
check_all("line-missing-stops", text["order"], "no line comment", "`plan-assembly-line`", "`runStatus: needs-input`")
check_all("lines-validated", text["order"], "`validate-line.py`", "before any card")
check_all("lines-expanded", text["order"], "`from`", '`"line"`', "expanded")
check_all("group-required", text["order"], 'holds no `{"group": "sub-issues"}`')
check_all("no-sub-issues-one-ticket", text["order"], "no sub-issues", "`../assembly-line/SKILL.md`")

check_all("parent-line-assembly", text["line"],
          "`../assembly-line/SKILL.md`", "service card", '`{"group": "sub-issues"}`', "sections 3 to 6", "its section 2 does not apply")
check_all("only-named-stages", text["line"], "only the stages the parent's line names")
check_all("restaurant-prefix", text["line"], "`restaurant:` in place of `line:`")
check_all("return-off-line", text["line"], "not on the parent's line", "`past`")
check_all("merge-gate", text["line"],
          "`gate: human`", "`open-restaurant.doneState`", "`threads-open`", "`integration/<parent>`", "`stage: closed`")
check_all("step-log", text["line"], "`restaurant: step <n>/<total> <stage> <verdict>`")

check_all("one-card-per-sub-issue", text["plan"], "one card", "one pr")
check_all("same-repo-serial", text["plan"], "one at a time", "same repo")
check_all("cross-repo-parallel", text["plan"], "parallel", "unblock note")
check_all("stacked-base", text["plan"], "stack", "blocker's branch")
check_all("two-blockers-stop", text["plan"], "do not form a chain")
check_all("parent-contract", text["plan"], "`## parent contract`")
check_none("no-reproduce-item", text["plan"], "`../reproduce/skill.md`", "bug marker")

check_all("cards-through-assembly-line", text["cards"], "`../assembly-line/SKILL.md`", "own line")
check_all("sub-issue-no-merge", text["cards"], "without its `merge`", "`restaurant: skipped merge`", "not run")
check_all("shared-files-once", text["cards"], "once per session", "frontmatter", "a card is finished when its pr's `review-fix`")
check_all("prepare-pr-overrides", text["cards"],
          "`prepare-pr`", "one pr", "ready for review", "never as a draft", "no chunks", "base", "no closing word")
check_all("review-per-pr", text["cards"], "`review-fix`", "one per pr", "never batch")
check_none("no-draft-pr", skill, "one draft pr", "anything but a draft", "mark every sub-issue pr ready", "never mark a pr ready")
check_all("pr-to-sub-issue", text["cards"], "never to the parent", "attachment")
check_all("implemented-state", text["cards"], "`open-restaurant.implementedState`", "in place of `assembly-line.reviewState`")
check_all("card-stops", text["cards"], "`## blocked <id>`", "does not depend on it")

check_all("unblock-file", text["unblock"], "`{scratch}/unblock/<a>-to-<b>.md`", "`## upstream interfaces (<a>)`")
check_all("unblock-earliest", text["unblock"], "`plan-code`", "later point")
check_all("unblock-follow-up", text["unblock"], "follow-up", "never guess")
check_all("unblock-change", text["unblock"], "dated entry", "back to its `code` stage")
check_all("no-contract-no-early-unblock", skill, "no `## contract`", "no `## parent contract`", "no early unblock")
check_all("unblock-chain", text["unblock"], "chain")
check_none("no-interfaces-unit", skill, "interfaces unit")
check_none("no-nesting-claim", skill, "cannot start sub-agents")
check_none("no-design-unit", skill, "design unit", "phase 1")

check_all("unfinished-park", text["close"], "park", "`## blocked", "`gate: unfinished`", "`runStatus: gate`")
check_all("interfaces-match", text["close"], "mismatch", "`runstatus: needs-input`", "compare each producer's final `## interfaces`")
check_all("close-returns", text["close"], "next step of the parent's line")

check_all("resume", text["stops"], "service card", "`restaurant: step`")
check_all("gate-stop", text["stops"], "`runStatus: gate`")
check_all("report", text["report"], "unblock notes", "`restaurant:`")

check_all("one-way-doors", skill, "never merges", "without a human")

unresolved = [path for path in re.findall(r"`(\.\.?/[^`\s]+\.md)`", skill) if not (SKILL / path).resolve().exists()]
check("links-resolve", not unresolved, f"unresolved: {unresolved}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", not leaks, f"private content: {leaks}")

check_all("plating-allows-named-base", read(PLATING), "a driver names a base branch")
readme_section = block(readme, "### open-restaurant", r"^###? ")
check_all("readme-section", readme_section, "assembly-line", "parent", "line")
check_none("readme-no-relay", readme_section, "recipe-relay")
check_all("readme-layout", block(readme, "## Layout", r"^## "), "open-restaurant/")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-open-restaurant.py")
check("dsh-lists-skill", "'open-restaurant'" in read(DSH_TEST), "dsh/index.test.mjs must list open-restaurant")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
