import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
REVIEW_FIX = REPO / "skills" / "review-fix" / "SKILL.md"

PAUSES = [
    "give them a beat",
    "visible checkpoint",
]
STOPS = [
    "report the open question to the user",
]

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


skill = read(SKILL_MD)
review = block(skill, "## 5. Review and fix", r"^## ")

found = [phrase for phrase in PAUSES if phrase in flatten(skill)]
check("no-pause-between-units", not found, f"found: {found}")

missing = [phrase for phrase in STOPS if flatten(phrase) not in flatten(skill)]
check("keeps-stop-conditions", not missing, f"missing: {missing}")

lowered = flatten(read(REVIEW_FIX))
absent = [phrase for phrase in ("../better-code-review/skill.md", "--headless", "merge base", "failing test first") if phrase not in lowered]
absent += [phrase for phrase in ("../review-fix/skill.md",) if phrase not in flatten(review)]
check("closing-review-pass", not absent, f"missing: {absent}")

close = block(skill, "## 6. Close down", r"^## ")
stops = block(skill, "## 4. Stop conditions", r"^## ")
shots = block(skill, "### UI review", r"^##")
lowered_close = flatten(close)
gaps = [p for p in ('every stop', '`taskstop`', 'background shell', 'still running', 'port or pid', '`relay: closed down') if p not in lowered_close]
gaps += [p for p in ("section 6",) if p not in flatten(stops)]
gaps += [p for p in ("stops what it brought up",) if p not in flatten(shots)]
gaps += [p for p in ("stalled", "30 minutes", "`relay: stalled", "once", "`runstatus: blocked`") if p not in lowered_close]
check("close-down", not gaps, f"missing: {gaps}")

validate = block(read(README), "## Validate a change", r"^## ")
check("readme-validate-command", "check-no-pause.py" in validate, "README must list check-no-pause.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
