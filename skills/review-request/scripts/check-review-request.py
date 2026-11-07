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
delivers = stage.get("delivers") or {}

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
description = fields.get("description", "")
check("frontmatter-name", fields.get("name") == "review-request", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(description) > 40, "description missing or too short")
check("description-yaml-safe", description and "#" not in description and ": " not in description,
      "description is empty or holds # or ': '")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block,
          "work card", "`task`", "service card", "`parent`", "`## Sub-issues`", "`prUrl`")
check_all("input-stops-blocked", input_block, "`runStatus: blocked`", "no PR", "no verdict")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill),
      "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output, "`## Review Request`", "`## Decisions`", "`runStatus`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`", "`gate`")
check_all("output-verdicts", output, "`requested`", "`skipped`")

check_all("settings-key", block(skill, "## Settings", r"^## "),
          "`open-restaurant.reviewChannel`", "`''`", "review ready", "review groups", "`../setup/references/config.md`")

check_all("open-prs-step", block(skill, "## 1. Open PRs", r"^## "), "`## Sub-issues`", "`prUrl`", "tracker", "no PR")
check_all("checks-step", block(skill, "## 2. Checks", r"^## "),
          "review ready", "`gh pr checks <pr> --watch`", "no checks reported counts as green", "red", "timeout",
          "`skipped`")
check_all("request-step", block(skill, "## 3. Request", r"^## "),
          "`open-restaurant.reviewChannel`", "`no channel`", "one message", "every PR", "review groups",
          "never guess", "no tag", "retried once", "a chat failure does not stop the run")
check_all("link-step", block(skill, "## 4. Link", r"^## "), "`## Review Request`", "attach", "tracker")
check_all("done-step", block(skill, "## 5. Done", r"^## "),
          "`## Decisions`", "`lastTouched`", "`requested`", "`skipped`")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "`../feature-recipe/references/headless.md`", "unattended:", "never merges", "### Ending a run")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")
check("reads-key-backticked",
      "`open-restaurant.reviewChannel`" in skill and "`../setup/references/config.md`" in skill,
      "SKILL.md must name the key and link config in backticks")

check("stage-takes", stage.get("takes") == ["task", "parent", "## Sub-issues", "prUrl"],
      "stage.json must take exactly [task, parent, ## Sub-issues, prUrl]")
check("stage-delivers",
      delivers.get("sections") == ["## Review Request", "## Decisions"]
      and delivers.get("fields") == ["runStatus", "lastTouched"],
      "stage.json must deliver the sections and fields the Solution lists")
check("stage-verdicts", delivers.get("verdicts") == ["requested", "skipped"],
      "stage.json must deliver the verdicts requested, skipped")
check("stage-return",
      stage.get("return") == {"skipped": {"to": "review-request", "limit": 0, "past": "human"}},
      "stage.json must return skipped to review-request (limit 0), past human")
check("stage-gate", stage.get("gate") == "auto" and stage.get("signals") == [],
      "stage.json must have gate auto and no signals")

check_all("restaurant-loads-skill", block(read(RESTAURANT), "## 10. Review gate", r"^## "),
          "`../review-request/SKILL.md`", "`requested`", "`skipped`", "section 11")

check("readme-section", re.search(r"^### review-request$", readme, re.MULTILINE), "README has no ### review-request")
check_all("readme-section-content", block(readme, "### review-request\n", r"^##"),
          "`open-restaurant.reviewChannel`", "`requested`", "`skipped`", "`open-restaurant`")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "check-review-request.py", "check-stage-spec.py skills/review-request")
check_all("readme-layout", block(readme, "## Layout", r"^## "), "review-request/")
check_all("readme-open-restaurant-names-it", block(readme, "### open-restaurant", r"^### "), "`review-request`")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
