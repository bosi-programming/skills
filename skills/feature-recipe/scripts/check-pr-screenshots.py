import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
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


plating = read(PLATING)
readme = read(README)
attach = block(plating, "## 4a. Attach the screenshots", r"^## ")
headless = block(plating, "## Headless", r"^### ")

check("section-exists", attach, "no ## 4a. Attach the screenshots in Plating")
check_all("uses-gh-attach", attach, "`gh pr edit", "--attach")
check_all("alt-text", attach, "#<alt text>")
check_all("placed-in-body", attach, "![")
check_all("partial-failure", attach, "non-zero", "only the ones that failed")
check_all("never-invent", attach, "no screenshots")
check_all("headless-no-ask", headless, "section 4a", "unattended:")

check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"), "check-pr-screenshots.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
