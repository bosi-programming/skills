import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
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
review = read(REVIEW_MD)
readme = read(README)
split = block(skill, "### Cooking in parallel", r"^##")
spawn = block(review, "### 4. Spawn the three sub-agents in parallel", r"^### ")

check("split-section-exists", split, "assembly-line must have a `### Cooking in parallel` section")
check_all("interfaces-first", split, "`## Interfaces`", "before either writer starts")
check_all("pair-per-repo", split, "for each repo", "test writer", "code writer", "at the same time")
check_all("shared-worktree", split, "same branch and worktree", "only the files it wrote")
check("no-writer-worktree", "worktree" not in flatten(split).replace("same branch and worktree", ""),
      "the writers must not get worktrees of their own")
check_all("writers-blind", split, "never sees the code", "never sees the tests")
check_all("red-first", split, "confirms they fail")
check_all("green-on-base-logged", split, "already pass", "`line:`", "carry on")
check_all("writers-then-finish", split, "once both writers", "`../code/SKILL.md`", "again")
check_all("code-writer-runs-code", split, "code writer", "`../code/SKILL.md`", "_Beside test_")
check_all("test-writer-runs-test", split, "test writer", "`../test/SKILL.md`")
check_all("single-repo-splits", split, "even when the task touches one repo")
check_all("coding-model", split, "`assembly-line.codingModel`")
check("no-old-cooking-unit", "are one unit" not in flatten(block(skill, "## 3. Run each stage", r"^### ")),
      "section 3 runs Cooking and Tasting as one sub-agent")

check_all("reviewer-model", spawn, "`better-code-review.reviewerModel`")

check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "),
          "assembly-line/scripts/check-split-cooking.py")

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
