import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SKILLS = SKILL.parent
REPO = SKILLS.parent
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
PLATING = SKILLS / "feature-recipe" / "phases" / "phase-5-plating.md"
DSH_TEST = REPO / "dsh" / "index.test.mjs"

PRIVATE = ["~/dev/", "clutch", "withclutch", "aopost", "felipe", "linear-server", "goto-", "cw new", "controller", "ao-adr", "🐞"]

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
    "readiness": "## 2. Readiness gate",
    "contract": "## 3. Contract",
    "plan": "## 4. Seat the cards",
    "cards": "## 5. Cook the cards",
    "unblock": "## 6. Early unblock",
    "pass": "## 7. Close the cards",
    "qa": "## 8. Integrate, QA and fix",
    "proof": "## 9. Proof",
    "review": "## 10. Review gate",
    "merge": "## 11. Merge gate",
    "stops": "## 12. Stops and resume",
    "report": "## 13. Report",
}
text = {key: block(skill, heading, r"^## ") for key, heading in sections.items()}
for key, heading in sections.items():
    check(f"section:{key}", text[key], f"missing `{heading}`")

check_all("drives-relay", skill, "`../recipe-relay/SKILL.md`", "`../feature-recipe/")
check_all("settings-body", text["settings"], "`## open-restaurant`", "`../setup/references/config.md`")
check_all("settings-keys", text["settings"],
          "`open-restaurant.repoByLabel`", "`open-restaurant.implementedState`", "`open-restaurant.doneState`",
          "`open-restaurant.envName`", "`open-restaurant.reviewChannel`", "`open-restaurant.judgeModel`",
          "`open-restaurant.qaModel`", "`open-restaurant.fixModel`")

check_all("service-card", text["order"], ".service.md`", "service card")
check_all("no-worktrees", text["order"], "never creates or removes", "worktree")
check_all("missing-checkout-stops", text["order"], "missing", "stop")

check_all("readiness-lint-judge", text["readiness"], "lint", "judge", "`open-decision`")
check_all("readiness-blocks", text["readiness"], "`## not ready", "readiness gaps", "blocks the parent", "`## ready")

check_all("contract-copied", text["contract"], "`contract.json`", "`## contract", "never invent", "latest `## contract` comment wins")

check_all("one-card-per-sub-issue", text["plan"], "one recipe card", "one pr")
check_all("same-repo-serial", text["plan"], "one at a time", "same repo")
check_all("cross-repo-parallel", text["plan"], "parallel", "unblock note")
check_all("stacked-base", text["plan"], "stack", "blocker's branch")
check_all("bug-reproduce", text["plan"], "reproduce", "`## blocked")

check_all("plating-overrides", text["cards"], "one pr", "ready for review", "never as a draft", "no chunks", "base", "no closing word")
check_all("review-per-pr", text["cards"], "review per pr", "own background sub-agent", "one per pr", "--headless", "never batch")
check_none("no-draft-pr", skill, "one draft pr", "anything but a draft", "mark every sub-issue pr ready", "never mark a pr ready")
check_all("pr-to-sub-issue", text["cards"], "never to the parent", "attachment")
check_all("implemented-state", text["cards"], "`open-restaurant.implementedState`")
check_all("relay-review-per-card", text["cards"], "better-code-review")

check_all("unblock-file", text["unblock"], "`{scratch}/unblock/<a>-to-<b>.md`", "`## upstream interfaces (<a>)`")
check_all("unblock-earliest", text["unblock"], "interfaces unit", "later point")
check_all("unblock-follow-up", text["unblock"], "follow-up", "never guess")
check_all("unblock-change", text["unblock"], "dated entry", "one more fix and taste round")
check_all("unblock-chain", text["unblock"], "chain")

check_all("unfinished-park", text["pass"], "park", "`## blocked")
check_all("interfaces-match", text["pass"], "mismatch", "`runstatus: needs-input`")

check_all("integration-local", text["qa"], "`integration/<parent>`", "never push")
check_all("one-env", text["qa"], "one env", "`open-restaurant.envName`", "never per sub-issue")
check_all("env-torn-down", text["qa"], "tear the env down")
check_all("fix-owner-branch", text["qa"], "owner", "fast-forward", "never `--force`", "never on `integration/<parent>`")
check_all("fix-limits", text["qa"], "at most 2", "at most 4", "human gate")
check_all("verdicts", text["qa"], "pass", "fail", "inconclusive", "blocked", "verdict.json`", "`## qa")

check_all("proof", text["proof"], "`## proof <parent>`", "`### sub-issues`")
check_all("review-human", text["review"], "human", "ready", "`open-restaurant.reviewChannel`", "never guess")
check_all("merge-human", text["merge"], "human", "blocks order", "retarget", "`## open criteria", "`open-restaurant.doneState`")
check_all("merge-resume", text["merge"], "merged", "failed", "pending")

check_all("one-way-doors", skill, "never merges", "without a human")

unresolved = [path for path in re.findall(r"`(\.\.?/[^`\s]+\.md)`", skill) if not (SKILL / path).resolve().exists()]
check("links-resolve", not unresolved, f"unresolved: {unresolved}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", not leaks, f"private content: {leaks}")

check_all("plating-allows-named-base", read(PLATING), "a driver names a base branch")
check_all("readme-section", block(readme, "### open-restaurant", r"^###? "), "recipe-relay", "parent")
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
