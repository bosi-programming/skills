#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
PHASES = REPO / "skills" / "feature-recipe" / "phases"

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
check("frontmatter-name", fields.get("name") == "code", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

check_all(
    "input-is-work-card", block(skill, "## Input", r"^## "),
    "work card", "`../feature-recipe/phases/phase-0-start.md`",
    "`## Solution`", "`## Implementation Plan`", "`## Interfaces`",
)
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

check_all(
    "lists-card-fields", block(skill, "## Output", r"^## "),
    "`## Quality Gate Results`", "`## Decisions`", "`## Open Questions`",
    "`phase`", "`phasesCompleted`", "`lastTouched`", "`code`",
)
check_all("writes-stage-name", skill, "`phase: 'code'`")

check_all("signal-line", block(skill, "## 11. Close the stage", r"^## "),
          "`no-screen-change — code — <evidence>`", "`touches-security — code — <evidence>`",
          "auth", "sessions", "permissions", "secrets", "crypto", "outside input", "dependency")
check_all("output-signal-line", block(skill, "## Output", r"^## "), "`touches-security — code — <evidence>`")

try:
    code_signals = json.loads(read(SKILL / "stage.json") or "{}").get("signals")
except ValueError:
    code_signals = None
check("stage-signals", code_signals == ["no-screen-change", "touches-security"],
      f"code/stage.json signals is {code_signals!r}")

check_all("standards", block(skill, "## 1. Find the standards", r"^## "), "`../code-standards/SKILL.md`")
check_all("tests-come-from-test", block(skill, "## 2. Write the code", r"^## "), "`../test/SKILL.md`", "fix the code, not the test")
check_all("beside-test", block(skill, "## Beside test", r"^## "), "driver", "test file", "again")

review = block(skill, "## 5. Run the review", r"^## ")
check_all("review-gate", review, "`better-code-review`", "**Tests**", "`Reviewed:`", "`Not verified:`")
check_all("hard-gate", skill, "hard gate")

check_all("stage-done-menu", block(skill, "## 12. Stage done", r"^## "),
          "New session (recommended)", "`../prepare-pr/SKILL.md`")

headless = block(skill, "## Headless", r"^## ")
check_all("keeps-headless", headless, "`runNext: code`", "unattended:", "--headless",
          "`../prepare-pr/SKILL.md`", "### Ending a run")
check_all("links-contract", skill, "`../feature-recipe/references/headless.md`",
          "`../feature-recipe/references/recipe-card-template.md`")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

left = [p.name for p in (PHASES / "phase-3-cooking.md", PHASES / "phase-4-tasting.md") if p.exists()]
check("phase-files-moved", not left, f"still in feature-recipe: {left}")

check("readme-section", re.search(r"^### code$", readme, re.MULTILINE), "README has no ### code")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"), "check-code.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
