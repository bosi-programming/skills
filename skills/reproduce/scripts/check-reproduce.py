#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
STAGE = SKILL / "stage.json"
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

try:
    stage = json.loads(read(STAGE) or "{}")
except ValueError:
    stage = {}

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
check("frontmatter-name", fields.get("name") == "reproduce", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block, "work card", "`task`", "bug")
check_all("input-stops-blocked", input_block, "`runStatus: blocked`", "git checkout")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output,
          "`## Reproduction`", "`## Decisions`", "`## Open Questions`", "`runStatus`", "`runQuestion`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")
check_all("output-verdicts", output, "`reproduced`", "`not-reproduced`", "`## Blocked <id>`")

check("no-settings", SKILL_MD.exists() and not re.search(r"^## Settings", skill, re.MULTILINE), "SKILL.md missing or has a ## Settings heading")
check_all("try-step", block(skill, "## 1. Try", r"^## "),
          "sub-agent", "`origin/<default branch>`", "what it tried", "commits nothing")
check_all("not-reproduced-step", block(skill, "## 2. Not reproduced", r"^## "),
          "`## Blocked <id>`", "what it tried", "Comment: <link>", "`runStatus: blocked`", "`r1`", "`runQuestion`", "`not-reproduced`")
check_all("reproduced-step", block(skill, "## 3. Reproduced", r"^## "),
          "`reproduced`", "`## Reproduction`", "`lastTouched`")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: blocked`", "### Ending a run")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

check("stage-return-self",
      stage.get("return") == {"not-reproduced": {"to": "reproduce", "limit": 0, "past": "human"}} and stage.get("gate") == "auto",
      "stage.json must return not-reproduced to reproduce with limit 0, past human, and gate auto")
check("stage-takes-task", stage.get("takes") == ["task"], "stage.json must take exactly [task]")

check_all("restaurant-loads-skill", block(read(RESTAURANT), "## 4. Seat the cards", r"^## "),
          "`../reproduce/SKILL.md`", "`not-reproduced`", "`reproduced`")

check("readme-section", re.search(r"^### reproduce$", readme, re.MULTILINE), "README has no ### reproduce")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "check-reproduce.py", "check-stage-spec.py skills/reproduce")
check_all("readme-open-restaurant-names-it", block(readme, "### open-restaurant", r"^### "), "`reproduce`")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
