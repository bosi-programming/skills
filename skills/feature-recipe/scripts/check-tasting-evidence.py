import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
TASTING = SKILL / "phases" / "phase-4-tasting.md"
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
tasting = read(TASTING)
readme = read(README)
review = block(tasting, "## 1. Run the review", r"^## ")
detect = block(tasting, "## 2. Detect", r"^## ")
fix = block(tasting, "## 6. Fix and retry", r"^## ")

check_all("review-result-kept", review, "`Reviewed:`", "`ran`", "`Not verified:`")
check_all("no-second-run", detect, "`Reviewed:`", "`HEAD`", "only")
check_all("rerun-after-fix", detect, "not verified", "fix")
check_all("fix-reruns-set", fix, "section 4")

rules = block(skill, "## Rules for all phases", r"^## ")
check("comment-rule-rewritten", "never, ever, comment a code" not in flatten(rules), "comment rule still has the broken wording")
check_all("comment-rule-kept", rules, "never comment code", "tsdoc")

check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-tasting-evidence.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
