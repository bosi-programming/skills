#!/usr/bin/env python3
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
RELAY = REPO / "skills" / "recipe-relay" / "SKILL.md"

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
check("frontmatter-name", fields.get("name") == "review-fix", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

check_all("input-is-work-card", block(skill, "## Input", r"^## "), "work card", "`prUrl`", "`task`")
check_all("input-needs-open-pr", block(skill, "## Input", r"^## "), "`blocked`", "open")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output, "`## Quality Gate Results`", "`## Decisions`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")

check_all("reads-settings", block(skill, "## Settings", r"^## "),
          "`recipe-relay.routineModel`", "`recipe-relay.codingModel`", "`../setup/references/config.md`")
check_all("runs-review", block(skill, "## 1. Review", r"^## "),
          "`../better-code-review/SKILL.md`", "--headless", "merge base", "`{scratch}/review.txt`")
check_all("fix-by-tag", block(skill, "## 2. Fix", r"^## "),
          "`Verified:`", "`ran`", "`read`", "`no`", "failing test first")
check_all("fix-log-prefixes", block(skill, "## 2. Fix", r"^## "),
          "`relay:`", "`unattended:`", "`review-fix:`")
check_all("fix-one-way-door", block(skill, "## 2. Fix", r"^## "),
          "deleting work written on purpose is a one-way door")
check_all("fix-return-cap", block(skill, "## 2. Fix", r"^## "), "at most 150 words")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: needs-input`", "### Ending a run")
check_all("ending-not-under-relay", block(skill, "### Ending a run", r"^#{1,3} "),
          "not under `recipe-relay`", "`## Quality Gate Results`")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

check_all("relay-loads-skill", block(read(RELAY), "## 5. Review and fix", r"^## "), "`../review-fix/SKILL.md`")

check("readme-section", re.search(r"^### review-fix$", readme, re.MULTILINE), "README has no ### review-fix")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"), "check-review-fix.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
