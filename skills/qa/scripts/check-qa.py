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
check("frontmatter-name", fields.get("name") == "qa", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

input_block = block(skill, "## Input", r"^## ")
check_all("input-is-work-card", input_block,
          "work card", "`task`", "service card", "`parent`", "`## Integration`", "`### QA scope`")
check_all("input-stops-blocked", input_block, "`runStatus: blocked`", "`integration/<parent>`", "missing checkout")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output,
          "`## QA`", "`## Decisions`", "`## Open Questions`", "`runStatus`", "`runQuestion`",
          "`gate`", "`qaRounds`", "`fixChecks`", "`lastTouched`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")
check_all("output-verdicts", output, "`pass`", "`fail`", "`inconclusive`", "`blocked`", "verdict.json")

settings = block(skill, "## Settings", r"^## ")
check_all("settings-keys", settings,
          "`open-restaurant.envName`", "`open-restaurant.qaModel`", "`open-restaurant.fixModel`",
          "`../setup/references/config.md`")
check_all("settings-guidance", settings, "`## open-restaurant`", "QA skill", "QA env", "QA checks", "fix check")
check_all("under-a-line", block(skill, "## Under a line", r"^## "),
          "`line:`", "`./stage.json`", "`code`", "`integrate`", "at most twice")

qa_block = block(skill, "## 1. QA", r"^## ")
check_all("qa-step", qa_block,
          "one env", "`open-restaurant.envName`", "never per sub-issue", "`open-restaurant.qaModel`",
          "`./qa-proof/<parent>/`", "`proof/<issue>/<n>/verdict.json`", "never edits the checkouts", "`## QA <parent>`")
check_all("qa-no-env", qa_block, "no QA env entry")
check_all("on-pass-step", block(skill, "## 2. On pass", r"^## "), "tear the env down", "`pass`")
check_all("on-fail-step", block(skill, "## 3. On fail", r"^## "),
          "proof bundle", "tear the env down", "off `integration/<parent>`")
check_all("fix-step", block(skill, "## 4. Fix", r"^## "),
          "`open-restaurant.fixModel`", "owning sub-issue", "`origin/<owner branch>`", "fast-forward only",
          "never `--force`", "never on `integration/<parent>`",
          "`{ fixes: [{ criterion, owner, branch, repo, sha, summary }] }`")
check_all("fix-check-step", block(skill, "## 5. Fix check", r"^## "),
          "fix check", "refused fix", "`../integrate/SKILL.md`", "`integrated`", "`conflict`", "every criterion in scope")
check_all("limits-step", block(skill, "## 6. Limits", r"^## "),
          "at most 2", "at most 4", "human gate", "`runStatus: gate`", "`gate: qa`", "`qa1`",
          "`inconclusive`", "`blocked`")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: gate`", "### Ending a run")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

check("stage-return",
      stage.get("return") == {
          "fail": {"to": "code", "limit": 2, "past": "human"},
          "inconclusive": {"to": "qa", "limit": 0, "past": "human"},
          "blocked": {"to": "qa", "limit": 0, "past": "human"},
      } and stage.get("gate") == "auto",
      "stage.json must return fail to code (limit 2), inconclusive and blocked to qa (limit 0), all past human, and gate auto")
check("stage-takes", stage.get("takes") == ["task", "parent", "## Sub-issues", "## Integration"],
      "stage.json must take exactly [task, parent, ## Sub-issues, ## Integration]")
check("stage-delivers",
      delivers.get("sections") == ["## QA", "## Decisions", "## Open Questions"]
      and delivers.get("fields") == ["runStatus", "runQuestion", "gate", "qaRounds", "fixChecks", "lastTouched"],
      "stage.json must deliver the sections and fields the Solution lists")
check("stage-verdicts", delivers.get("verdicts") == ["pass", "fail", "inconclusive", "blocked"],
      "stage.json must deliver the verdicts pass, fail, inconclusive, blocked")

WORD_NUMBERS = {"once": 1, "twice": 2}
limits_text = flatten(block(skill, "## 6. Limits", r"^## "))
line_text = flatten(block(skill, "## Under a line", r"^## "))
stated_qa = re.search(r"qa to fix runs at most (\d+) times", limits_text)
stated_line = re.search(r"at most (\w+)", line_text)
fail_limit = (stage.get("return") or {}).get("fail", {}).get("limit")
check("limits-match-stage",
      stated_qa is not None and stated_line is not None
      and int(stated_qa.group(1)) == fail_limit
      and WORD_NUMBERS.get(stated_line.group(1), None) == fail_limit,
      f"SKILL.md states {stated_qa and stated_qa.group(1)} and {stated_line and stated_line.group(1)}; stage.json return.fail.limit is {fail_limit}")

check_all("restaurant-loads-skill", block(read(RESTAURANT), "## 8. Integrate, QA and fix", r"^## "),
          "`../qa/SKILL.md`", "`pass`", "`gate: qa`", "section 9")

check("readme-section", re.search(r"^### qa$", readme, re.MULTILINE), "README has no ### qa")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "check-qa.py", "check-stage-spec.py skills/qa")
check_all("readme-open-restaurant-names-it", block(readme, "### open-restaurant", r"^### "), "`qa`")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
