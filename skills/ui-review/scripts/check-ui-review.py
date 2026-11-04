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
RELAY = REPO / "skills" / "recipe-relay" / "SKILL.md"

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
check("frontmatter-name", fields.get("name") == "ui-review", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block, "work card", "`task`", "`## Solution`", "`{scratch}/ui-review/`")
check_all("input-no-screenshots", input_block, "`inconclusive`", "no reviewer starts")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output, "`## UI Review`", "`## Quality Gate Results`", "`## Decisions`", "`lastTouched`")
check_all("lists-verdicts", output, "`pass`", "`fail`", "`inconclusive`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")

check_all("reads-settings", block(skill, "## Settings", r"^## "),
          "`recipe-relay.uiReviewerModel`", "`../setup/references/config.md`")
check_all("design-step", block(skill, "## 1. Design", r"^## "),
          "image attached to the task", "never stands in", "never guesses")
check_all("compare-step", block(skill, "## 2. Compare", r"^## "),
          "never starts the app", "takes no screenshots", "critical", "major", "minor", "`## UI Review`")
check_all("verdict-step", block(skill, "## 3. Verdict", r"^## "),
          "critical or major", "only minor", "`fail`", "`pass`", "`inconclusive`", "`## Quality Gate Results`", "`code`", "twice", "`needs-input`")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: needs-input`", "### Ending a run")
check_all("log-prefixes", skill, "`relay:`", "`unattended:`", "`ui-review:`")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

returns = stage.get("return") if isinstance(stage.get("return"), dict) else {}
check("stage-return-code",
      returns.get("fail") == {"to": "code", "limit": 2, "past": "needs-input"} and stage.get("gate") == "auto",
      "stage.json must return fail to code twice, then needs-input, with gate auto")
delivers = stage.get("delivers") if isinstance(stage.get("delivers"), dict) else {}
check("stage-verdicts", delivers.get("verdicts") == ["pass", "fail", "inconclusive"],
      "stage.json verdicts must be pass, fail, inconclusive")

check_all("relay-loads-skill", block(read(RELAY), "### UI review\n", r"^##"), "`../ui-review/SKILL.md`")

check("readme-section", re.search(r"^### ui-review$", readme, re.MULTILINE), "README has no ### ui-review")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "skills/ui-review/scripts/check-ui-review.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
