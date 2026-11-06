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
check("frontmatter-name", fields.get("name") == "integrate", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block, "work card", "`task`", "service card", "`parent`", "`## Sub-issues`")
check_all("input-stops-blocked", input_block, "`runStatus: blocked`", "git checkout", "uncommitted")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output,
          "`## Integration`", "`## Decisions`", "`## Open Questions`", "`runStatus`", "`runQuestion`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")
check_all("output-verdicts", output, "`integrated`", "`no-scope`", "`conflict`")

check_all("settings-guidance", block(skill, "## Settings", r"^## "),
          "`## open-restaurant`", "QA scope", "`../setup/references/config.md`")
check_all("scope-step", block(skill, "## 1. Scope", r"^## "),
          "every criterion of the parent", "QA scope", "`### QA scope`", "`no-scope`")
integrate_block = block(skill, "## 2. Integrate", r"^## ")
check_all("integrate-step", integrate_block,
          "`integration/<parent>`", "`origin/<default branch>`", "blocks order", "never pushes", "skipped")
check_all("rebuild-guard", integrate_block, "rebuilt", "`runStatus: blocked`")
check_all("conflict-step", block(skill, "## 3. Conflict", r"^## "),
          "`git merge --abort`", "two branches", "`i1`", "`runStatus: needs-input`", "`runQuestion`", "`conflict`")
conflict_block = block(skill, "## 3. Conflict", r"^## ")
check_all("conflict-names-branch", conflict_block, "`git log -1 --format=%ct <ref> -- <file>`", "newest")
check("conflict-no-ref-names", "--format=%D" not in conflict_block,
      "%D prints ref names only when the commit is a branch tip, so it can print nothing")
check_all("integrated-step", block(skill, "## 4. Integrated", r"^## "),
          "`integrated`", "`## Integration`", "`lastTouched`")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: needs-input`", "### Ending a run")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

check("stage-return-self",
      stage.get("return") == {"conflict": {"to": "integrate", "limit": 0, "past": "needs-input"}} and stage.get("gate") == "auto",
      "stage.json must return conflict to integrate with limit 0, past needs-input, and gate auto")
check("stage-takes", stage.get("takes") == ["task", "parent", "## Sub-issues"],
      "stage.json must take exactly [task, parent, ## Sub-issues]")
check("stage-verdicts", delivers.get("verdicts") == ["integrated", "no-scope", "conflict"],
      "stage.json must deliver the verdicts integrated, no-scope, conflict")

check_all("restaurant-loads-skill", block(read(RESTAURANT), "## 8. Integrate, QA and fix", r"^## "),
          "`../integrate/SKILL.md`", "`no-scope`", "`conflict`", "`integrated`")

check("readme-section", re.search(r"^### integrate$", readme, re.MULTILINE), "README has no ### integrate")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "check-integrate.py", "check-stage-spec.py skills/integrate")
check_all("readme-open-restaurant-names-it", block(readme, "### open-restaurant", r"^### "), "`integrate`")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
