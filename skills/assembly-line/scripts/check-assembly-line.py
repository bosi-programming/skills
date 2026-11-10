#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
CATALOG = SKILL / "references" / "catalog.json"
CONFIG_MD = REPO / "skills" / "setup" / "references" / "config.md"

PRIVATE = ["~/dev/", "aopost", "felipe", "linear-server", "goto-", "cw new", "controller", "ao-adr"]

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
check("frontmatter-name", fields.get("name") == "assembly-line", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

check_all("input-is-ticket", block(skill, "## Input", r"^## "), "ticket id", "`open-restaurant`")
check_all("reads-settings", block(skill, "## Settings", r"^## "),
          "`assembly-line.codingModel`", "`assembly-line.routineModel`", "`assembly-line.uiReviewerModel`",
          "`assembly-line.reviewState`", "`assembly-line.doneState`", "`../setup/references/config.md`",
          "grep -n -A8 '^assembly-line:'", "`## assembly-line`", "`## recipe-relay`", "Project rules:")
check("no-whole-config-read", SKILL_MD.exists() and "read `../setup/references/config.md`" not in flatten(skill),
      "SKILL.md missing or reads the whole config.md")

line = block(skill, "## 1. Read the line", r"^## ")
check_all("reads-line-comment", line, "`assembly-line/1`", "created last", "`./references/line-format.md`", "`ticket`")
check_all("validates-first", line, "`$SKILL_DIR/scripts/validate-line.py`", "`{scratch}/line.json`", '`"valid"`',
          "before any stage runs", "names the missing stage")
check_all("no-line-stops", line, "no line comment", "`plan-assembly-line`", "writes nothing")
check_all("expands-saved-line", line, "`from`", '`"line"`', "expanded line")
check_all("sub-issue-group-stops", line, '`{"group": "sub-issues"}`', "`open-restaurant`")

card = block(skill, "## 2. Find or make the card", r"^## ")
check_all("card-through-phase-0", card, "`../feature-recipe/phases/phase-0-start.md`", "interactive invocation",
          "`runMode`", "the line routes")
check_all("links-to-comment", card, "link to the line comment")

run = block(skill, "## 3. Run each stage", r"^## ")
check_all("own-sub-agent", run, "own sub-agent", "`general-purpose`", "in this session")
check_all("stage-prompt", block(skill, "### Stage prompt", r"^##"),
          "`## Headless`", "`line:`", "`Verdict:`", "never merge", "`## Open Questions`", "`runStatus`", "`with`",
          "100 words")
check_all("routine-model", run, "`assembly-line.routineModel`", "`prepare-pr`", "`code-docs`")
check_all("review-state", run, "`assembly-line.reviewState`", "ready for review", "never as a draft")
check_all("ui-review-stage", block(skill, "### UI review", r"^##"),
          "`../ui-review/SKILL.md`", "`{scratch}/ui-review/`", "`assembly-line.uiReviewerModel`", "`inconclusive`")
check_all("review-fix-stage", block(skill, "### Review and fix", r"^##"),
          "`../review-fix/SKILL.md`", "`assembly-line.codingModel`", "`assembly-line.routineModel`")
gates = block(skill, "### Gates", r"^##")
check_all("gates", gates, "`gate: human`", "`runStatus: gate`", "`## Open Questions`", "in chat", "approv")
check_all("done-state", gates, "`assembly-line.doneState`", "`open-restaurant.doneState`")
check_all("go-back", block(skill, "## 4. Go back on a failing verdict", r"^## "),
          "`./references/catalog.json`", "`return`", "`limit`", "`past`", "latest", "line: return", "`needs-input`",
          "`human`")
check_all("next-stage", block(skill, "## 5. Move to the next stage", r"^## "),
          "line: step", "without waiting", "one line per stage")
check_all("stop-conditions", block(skill, "## 6. Stop conditions", r"^## "),
          "`blocked`", "`needs-input`", "`runStatus: gate`", "report the open question to the user",
          "never merely because")
check("no-headless-mode", SKILL_MD.exists() and "runmode: headless" not in flatten(skill),
      "SKILL.md missing or sets runMode: headless")
check("no-skill-dir-var", SKILL_MD.exists() and "${CLAUDE_SKILL_DIR}" not in skill,
      "SKILL.md missing or names ${CLAUDE_SKILL_DIR}")

broken = [target for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill)))
          if not (SKILL / target).resolve().exists()]
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

try:
    ui_fail = json.loads(read(CATALOG) or "{}")["stages"]["ui-review"]["return"]["fail"]
except (ValueError, KeyError, TypeError):
    ui_fail = None
check("catalog-ui-limit", ui_fail == {"to": "code", "limit": 2, "past": "needs-input"},
      "catalog.json ui-review return.fail must be to code, limit 2, past needs-input")

check("readme-section", re.search(r"^### assembly-line$", readme, re.MULTILINE), "README has no ### assembly-line")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "),
          "skills/assembly-line/scripts/check-assembly-line.py")
check_all("readme-saved-line", block(readme, "### assembly-line", r"^### "), "saved line", "`from`")
check_all("config-names-section", read(CONFIG_MD), "`## assembly-line`")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    out = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        out += f"  {detail}"
    print(out)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
