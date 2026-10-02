import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
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
readme = read(README)
ui = block(skill, "### UI review in parallel", r"^##")

check("ui-section-exists", ui, "recipe-relay must have a `### UI review in parallel` section")
check_all("only-ui-changes", ui, "a person sees", "skip")
check_all("runs-beside-tasting", ui, "at the same time", "fix and taste")
check_all("reviewer-takes-no-screenshots", ui, "never starts the app", "takes no screenshots")
check_all("signal-file", ui, "`screenshots.done`", "`git rev-parse head`")
check_all("stale-signal", ui, "stale", "keep waiting")
check_all("no-screenshots-signal", ui, "`none:`")
check_all("design-source", ui, "the design", "never guess")
check_all("inconclusive", ui, "inconclusive")
check_all("severity", ui, "critical", "major", "minor")
check_all("blocking-routes", ui, "back to the fix agent", "twice")
check_all("cap-stops", ui, "`runstatus: needs-input`")
check_all("minor-logged", ui, "`## quality gate results`")
check_all("card-section", ui, "`## ui review`")
check_all("relay-prefix", ui, "`relay:`")
check("unit-list-names-ui", "ui review in parallel" in flatten(block(skill, "## 2.", r"^### ")),
      "section 2 must name the UI review unit")

check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-ui-review.py")

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
