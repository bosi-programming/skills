import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
MAESTRI_MD = REPO / "skills" / "maestri-workflow" / "SKILL.md"
REVIEW_MD = REPO / "skills" / "better-code-review" / "SKILL.md"
README = REPO / "README.md"

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


skill = read(SKILL_MD)
maestri = read(MAESTRI_MD)
review = read(REVIEW_MD)
readme = read(README)
split = block(skill, "### Cooking in parallel", r"^##")
spawn = block(review, "### 4. Spawn the three sub-agents in parallel", r"^### ")

check("split-section-exists", split, "recipe-relay must have a `### Cooking in parallel` section")
check_all("interfaces-first", split, "`## Interfaces`", "before either writer starts")
check_all("pair-per-repo", split, "for each repo", "test writer", "code writer", "at the same time")
check_all("shared-worktree", split, "same branch and worktree", "only the files it wrote")
check("no-writer-worktree", "worktree" not in flatten(split).replace("same branch and worktree", ""),
      "the writers must not get worktrees of their own")
check_all("writers-blind", split, "never sees the code", "never sees the tests")
check_all("red-first", split, "confirms they fail")
check_all("green-on-base-logged", split, "already pass", "`relay:`", "carry on")
check_all("writers-then-finish", split, "once both writers", "`phase-3-cooking.md`", "`phase-4-tasting.md`")
check_all("single-repo-splits", split, "even when the task touches one repo")
check_all("coding-model", split, "`recipe-relay.codingModel`")
check("no-old-cooking-unit", "are one unit" not in flatten(block(skill, "## 2.", r"^### ")),
      "section 2 still runs Cooking and Tasting as one sub-agent")

check_all("reviewer-model", spawn, "`better-code-review.reviewerModel`")

check_all("maestri-pair", maestri, "test writer", "code writer", "recruit both")
check("maestri-no-writer-worktree", "its own worktree" not in flatten(maestri),
      "maestri-workflow still gives each writer its own worktree")

check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-split-cooking.py")

unresolved = [path for path in re.findall(r"`(\.\.?/[^`]+\.md)`", skill) if not (SKILL / path).resolve().exists()]
check("links-resolve", not unresolved, f"unresolved: {unresolved}")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
