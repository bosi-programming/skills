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
delivers = stage.get("delivers") or {}

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
description = fields.get("description", "")
check("frontmatter-name", fields.get("name") == "proof", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(description) > 40, "description missing or too short")
check("description-yaml-safe", description and "#" not in description and ": " not in description,
      "description is empty or holds # or ': '")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block,
          "work card", "`task`", "service card", "`parent`", "`## Sub-issues`", "`prUrl`", "`## QA`")
check_all("input-stops-blocked", input_block, "`runStatus: blocked`", "no PR", "no verdict")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill),
      "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output,
          "`## Proof`", "`## Decisions`", "`## Open Questions`", "`runStatus`", "`runQuestion`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")
check_all("output-verdicts", output, "`done`", "`blocked`", "`## Proof <parent>`")

check_all("settings-no-key", block(skill, "## Settings", r"^## "), "No key", "`../setup/references/config.md`")

check_all("criteria-step", block(skill, "## 1. Criteria", r"^## "),
          "`proof/<issue>/<n>/verdict.json`", "`./qa-proof/<parent>/`", "`## Quality Gate Results`",
          "`not proved`", "manual")
check_all("pr-step", block(skill, "## 2. Proof on each PR", r"^## "),
          "`## Proof`", "verdict", "evidence", "`gh pr comment <pr> --body-file <file>`",
          "latest `## Proof` comment wins", "no PR gets no PR comment")
check_all("parent-step", block(skill, "## 3. Proof on the parent", r"^## "),
          "`## Proof <parent>`", "uploaded to the tracker", "`### Sub-issues`",
          "how many of its criteria are met", "no PR")
check_all("check-posts-step", block(skill, "## 4. Check the posts", r"^## "),
          "read back", "retried once", "`p1`", "`runStatus: blocked`", "`runQuestion`")
check_all("done-step", block(skill, "## 5. Done", r"^## "), "`## Proof`", "`done`", "`lastTouched`")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "`../feature-recipe/references/headless.md`", "unattended:", "never merges", "### Ending a run")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

check("stage-takes", stage.get("takes") == ["task", "parent", "## Sub-issues", "prUrl", "## QA"],
      "stage.json must take exactly [task, parent, ## Sub-issues, prUrl, ## QA]")
check("stage-delivers",
      delivers.get("sections") == ["## Proof", "## Decisions", "## Open Questions"]
      and delivers.get("fields") == ["runStatus", "runQuestion", "lastTouched"],
      "stage.json must deliver the sections and fields the Solution lists")
check("stage-verdicts", delivers.get("verdicts") == ["done", "blocked"],
      "stage.json must deliver the verdicts done, blocked")
check("stage-return",
      stage.get("return") == {"blocked": {"to": "proof", "limit": 0, "past": "human"}},
      "stage.json must return blocked to proof (limit 0), past human")
check("stage-gate", stage.get("gate") == "auto" and stage.get("signals") == [],
      "stage.json must have gate auto and no signals")

check_all("restaurant-runs-it-on-a-line", skill, "a parent's line", "`open-restaurant`")
check_none("restaurant-section-gone", skill, "its section")

check("readme-section", re.search(r"^### proof$", readme, re.MULTILINE), "README has no ### proof")
check_all("readme-section-content", block(readme, "### proof\n", r"^##"),
          "`## Proof <parent>`", "`done`", "`blocked`", "`open-restaurant`")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "check-proof.py", "check-stage-spec.py skills/proof")
check_all("readme-layout", block(readme, "## Layout", r"^## "), "proof/")
check_all("readme-open-restaurant-names-it", block(readme, "### open-restaurant", r"^### "), "`proof`")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
