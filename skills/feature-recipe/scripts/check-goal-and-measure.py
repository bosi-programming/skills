import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
CARD = SKILL / "references" / "recipe-card-template.md"
READING = SKILL / "phases" / "phase-1-reading-the-recipe.md"
PLATING = SKILL / "phases" / "phase-5-plating.md"
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


card = read(CARD)
reading = read(READING)
plating = read(PLATING)
readme = read(README)

headings = re.findall(r"^## (.+)$", card, re.MULTILINE)
check("card-has-section", "Goal & measure" in headings, "no ## Goal & measure in the card skeleton")
check(
    "card-section-after-problem",
    "Problem" in headings and "Goal & measure" in headings
    and headings.index("Goal & measure") == headings.index("Problem") + 1,
    "## Goal & measure must follow ## Problem",
)
check_all("card-section-owner", block(card, "## Goal & measure", r"^## "), "Phase 1")

check_all("grill-dimension", block(reading, "## 2.", r"^## "), "how we will know it worked")
section = block(reading, "## 3.", r"^## ")
check_all(
    "reading-writes-section", section,
    "`## Goal & measure`", "what changes for whom", "where we see it", "after release",
    "no product metric", "never invent",
)
check_all("headless-gap", block(reading, "## Headless", r"^### "), "goal & measure", "unattended:")

check_all("pr-carries-goal", block(plating, "## 3. Draft the description", r"^## "), "goal & measure")

check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"), "check-goal-and-measure.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
