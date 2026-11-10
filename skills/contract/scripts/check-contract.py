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


def check_none(name, text, *phrases):
    lowered = flatten(text)
    present = [phrase for phrase in phrases if phrase.lower() in lowered]
    check(name, not present, f"must not say: {present}" if present else "")


skill = read(SKILL_MD)
readme = read(README)

try:
    stage = json.loads(read(STAGE) or "{}")
except ValueError:
    stage = {}

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
check("frontmatter-name", fields.get("name") == "contract", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block, "work card", "`task`", "service card", "`parent`")
check_all("input-stops-blocked", input_block, "`runStatus: blocked`")
check_all("input-no-sub-issues", input_block, "no sub-issues", "`done`")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output,
          "`## Contract`", "`## Decisions`", "`## Open Questions`", "`runStatus`", "`runQuestion`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")
check_all("output-verdicts", output, "`done`", "`gaps`", "`contract.json`")

check_all("reads-settings", block(skill, "## Settings", r"^## "),
          "`open-restaurant.judgeModel`", "`../setup/references/config.md`")
check_all("shapes-step", block(skill, "## 1. Shapes", r"^## "),
          "sub-agent", "word for word", "never invent", "`gaps`", "producer", "consumers", "`contract.json`")
check_all("post-step", block(skill, "## 2. Post", r"^## "), "`## Contract <id>`", "link", "`## Contract`")
check_all("gaps-step", block(skill, "## 3. Gaps", r"^## "),
          "`runStatus: needs-input`", "`runQuestion`", "`## Open Questions`", "`c1`", "`gaps`")
check_all("done-step", block(skill, "## 4. Done", r"^## "), "`done`", "`lastTouched`")
check_all("latest-comment-wins", skill, "latest `## Contract` comment wins")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: needs-input`", "### Ending a run")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

returns = stage.get("return")
check("stage-return-self",
      returns == {"gaps": {"to": "contract", "limit": 0, "past": "needs-input"}} and stage.get("gate") == "auto",
      "stage.json must return gaps to contract with limit 0, past needs-input, and gate auto")

check_all("restaurant-runs-it-on-a-line", skill, "a parent's line", "`open-restaurant`")
check_none("restaurant-section-gone", skill, "its section")

check("readme-section", re.search(r"^### contract$", readme, re.MULTILINE), "README has no ### contract")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "check-contract.py", "check-stage-spec.py skills/contract")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
