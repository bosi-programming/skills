#!/usr/bin/env python3
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

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
check("frontmatter-name", fields.get("name") == "evaluate-ticket", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

check_all("input-is-work-card", block(skill, "## Input", r"^## "), "work card", "`../feature-recipe/phases/phase-0-start.md`")
check("no-recipe-card-wording", "recipe card" not in flatten(skill), "SKILL.md still says recipe card")

check_all(
    "lists-card-fields", block(skill, "## Output", r"^## "),
    "`## Problem`", "`## Goal & measure`", "`## Decisions`",
    "`phase`", "`phasesCompleted`", "`lastTouched`", "`evaluate-ticket`",
)
check_all("writes-stage-name", skill, "`phase: 'evaluate-ticket'`")

headless = block(skill, "## Headless", r"^## ")
check_all("keeps-headless", headless, "`runNext: evaluate-ticket`", "unattended: grill-me skipped", "### Ending a run")
check_all("hands-off", skill, "`../feature-recipe/phases/phase-2-mise-en-place.md`")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

check("readme-section", re.search(r"^### evaluate-ticket$", readme, re.MULTILINE), "README has no ### evaluate-ticket")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"), "check-evaluate-ticket.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
