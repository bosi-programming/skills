#!/usr/bin/env python3
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
RESTAURANT = REPO / "skills" / "open-restaurant" / "SKILL.md"

PRIVATE = ["~/dev/", "aopost", "felipe", "linear-server", "goto-", "cw new", "controller", "ao-adr", "🐞"]

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
check("frontmatter-name", fields.get("name") == "judge", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block, "work card", "`task`", "service card", "`parent`")
check_all("input-stops-blocked", input_block, "`not-ready`", "`runStatus: blocked`")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output, "`## Decisions`", "`## Open Questions`", "`runStatus`", "`runQuestion`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")

check_all("reads-settings", block(skill, "## Settings", r"^## "),
          "`open-restaurant.judgeModel`", "`## open-restaurant`", "`## judge`", "`../setup/references/config.md`")

judge_block = block(skill, "## 2. Judge", r"^## ")
check_all("modes", input_block + "\n" + judge_block, "parent mode", "one-ticket mode")
check_all("lint-step", block(skill, "## 1. Lint", r"^## "),
          "readiness lint", "acceptance criteria", "one repo", "no cycle")
check_all("judge-rules", judge_block,
          "`open-decision`", "`parity-shorthand`", "`missing-contract`", "`manual-reason`",
          "no tools", "`open-restaurant.judgeModel`", "{ ready, gaps")
check_all("one-ticket-rules", judge_block, "on one ticket it checks only `open-decision` and `manual-reason`")
check_all("not-ready-step", block(skill, "## 3. Not ready", r"^## "),
          "readiness gaps", "blocks the", "`## not ready", "`runstatus: blocked`", "`## open questions`")
check_all("ready-step", block(skill, "## 4. Ready", r"^## "), "`## ready", "`ready`")
check_all("never-answers-gaps", skill, "never answered on")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: blocked`", "### Ending a run")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

check_all("restaurant-loads-skill", block(read(RESTAURANT), "## 2. Readiness gate", r"^## "), "`../judge/SKILL.md`")

check("readme-section", re.search(r"^### judge$", readme, re.MULTILINE), "README has no ### judge")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"), "check-judge.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
