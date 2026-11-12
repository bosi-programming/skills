#!/usr/bin/env python3
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
COOKING = REPO / "skills" / "code" / "SKILL.md"

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
cooking = read(COOKING)

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
check("frontmatter-name", fields.get("name") == "test", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

check_all(
    "input-is-work-card", block(skill, "## Input", r"^## "),
    "work card", "`../feature-recipe/phases/phase-0-start.md`",
    "`## Acceptance Criteria`", "`## Testing Strategy`", "`## TDD Test Mapping`", "`## Interfaces`",
)
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

check_all(
    "lists-card-fields", block(skill, "## Output", r"^## "),
    "`## TDD Test Mapping`", "`## Decisions`", "`## Open Questions`",
    "`phase`", "`phasesCompleted`", "`lastTouched`", "`test`",
)
check_all("writes-stage-name", skill, "`phase: 'test'`")

writing = block(skill, "## 2. Write the tests", r"^## ")
check_all("writes-tests-blind", writing, "never opens", "confirm they fail", "regression")
check_all("commits-tests-only", writing, "only the test files", "`git commit -- <paths>`")

headless = block(skill, "## Headless", r"^## ")
check_all("keeps-headless", headless, "`runNext: test`", "unattended:", "### Ending a run")
check_all("hands-off", skill, "`../code/SKILL.md`")
check_all("continue-menu", block(skill, "## 4. Stage done", r"^## "), "Continue here (recommended)")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

check("cooking-drops-mapped-tests", "write the test(s) this step maps to" not in flatten(cooking),
      f"{COOKING.name} still writes the mapped tests")
check_all("cooking-points-here", cooking, "`../test/SKILL.md`")

check("readme-section", re.search(r"^### test$", readme, re.MULTILINE), "README has no ### test")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"), "check-test.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
