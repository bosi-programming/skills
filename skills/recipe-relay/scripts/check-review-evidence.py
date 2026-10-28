import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
MAESTRI_MD = REPO / "skills" / "maestri-workflow" / "SKILL.md"
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
readme = read(README)
review = block(skill, "## 5. Review and fix", r"^## ")
maestri_report = block(maestri, "## 5. Report", r"^## ")

check_all("evidence-tags-triaged", review, "`Verified:`", "`ran`", "`read`", "`no`")
check_all("ran-goes-to-fix", review, "a `ran` finding is proved")
check_all("no-verified-first", review, "a `no` finding", "verify it first")
check("no-blanket-read", "read each one at its `file:line` first" not in flatten(review), "step 2 still reads every finding the same way")
check_all("not-verified-logged", review, "`Not verified:`", "`## Decisions`")
check_all("reviewed-sha-kept", review, "`Reviewed:`")
check_all("report-gaps", review, "not verified")
check_all("maestri-report-gaps", maestri_report, "not verified")

stops = block(skill, "## 4. Stop conditions", r"^## ")
moving = block(skill, "## 3. Move to the next unit", r"^## ")
units = block(skill, "## 2. Run one unit per sub-agent", r"^## ")
check_all("review-after-plating", review, "`phase-5-plating.md` returns", "whatever the card's `status`")
check_all("review-before-documentation", moving, "after `phase-5-plating.md` returns", "section 5", "before `phase-6-documentation.md`")
check("review-not-gated-on-terminal", "reaches `terminal`" not in flatten(review + stops), "section 4 or 5 still waits for runStatus: terminal")
check_all("stop-waits-for-review", stops, "section 5 is done")
check_all("pr-never-draft", units, "never as a draft", "ready for review", "overrides")
check("no-draft-promote-wait", "draft" not in flatten(review), "section 5 still talks about drafts")

readme_check = block(readme, "## Validate a change", r"^## ")
check_all("readme-validate-command", readme_check, "check-review-evidence.py")

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
