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
TEMPLATE = REPO / "skills" / "feature-recipe" / "references" / "recipe-card-template.md"

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
check("frontmatter-name", fields.get("name") == "merge", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block,
          "work card", "`task`", "`prUrl`", "`## PR`", "service card", "`parent`", "`## Sub-issues`")
check_all("input-stops-blocked", input_block, "`runStatus: blocked`", "closed")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output, "`## Merge`", "`## Decisions`", "`runStatus`", "`gate`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`", "`status`")

check_all("reads-settings", block(skill, "## Settings", r"^## "),
          "`open-restaurant.doneState`", "`## open-restaurant`", "`## merge`", "`../setup/references/config.md`")
check_all("modes", input_block, "parent mode", "one-ticket mode")
check_all("threads-step", block(skill, "## 1. Threads", r"^## "),
          "unresolved", "`threads-open`", "`review-fix`", "merges nothing")
check_all("threads-open-card-write", block(skill, "## 1. Threads", r"^## "),
          "`runStatus: needs-input`", "`## Decisions`", "`## Merge`")
check_all("output-names-threads-open-status", output, "`needs-input`", "`threads-open`")
check_all("gate-step", block(skill, "## 2. Gate", r"^## "),
          "`runStatus: gate`", "`gate: merge`", "every time", "approv")
check_all("merge-step", block(skill, "## 3. Merge", r"^## "),
          "blocks order", "retarget", "default branch", "merged", "failed", "pending")
check_all("done-step", block(skill, "## 4. Done", r"^## "),
          "`open-restaurant.doneState`", "`## open criteria", "`runstatus: terminal`", "`merged`")
check_all("never-merges-alone", skill, "never merges without")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "never approves", "`runStatus: gate`", "### Ending a run")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

returns = stage.get("return") if isinstance(stage.get("return"), dict) else {}
check("stage-return-review-fix",
      returns.get("threads-open") == {"to": "review-fix", "limit": 2, "past": "human"} and stage.get("gate") == "human",
      "stage.json must return threads-open to review-fix twice, then human, with gate human")

check_all("restaurant-loads-skill", block(read(RESTAURANT), "## 11. Merge gate", r"^## "), "`../merge/SKILL.md`")
check_all("restaurant-handles-threads-open", block(read(RESTAURANT), "## 11. Merge gate", r"^## "),
          "`threads-open`", "`gate: merge`")

status_line = next((line for line in read(TEMPLATE).splitlines() if line.startswith("runStatus:")), "")
check("template-gate-status", "gate" in status_line, "template runStatus line must name gate")

check("readme-section", re.search(r"^### merge$", readme, re.MULTILINE), "README has no ### merge")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"), "check-merge.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
