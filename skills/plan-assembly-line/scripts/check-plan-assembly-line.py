#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SKILLS = SKILL.parent
REPO = SKILLS.parent
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"
CATALOG = SKILLS / "assembly-line" / "references" / "catalog.json"
VALIDATOR = SKILLS / "assembly-line" / "scripts" / "validate-line.py"
PLAN_WORK = SKILLS / "plan-work" / "SKILL.md"
MANIFESTS = [REPO / ".claude-plugin" / "plugin.json", REPO / ".codex-plugin" / "plugin.json"]

PRIVATE = ["~/dev/", "aopost", "felipe", "linear-server", "goto-", "cw new", "controller", "ao-adr"]

HEADINGS = [
    "## Input",
    "## 1. Read each ticket",
    "## 2. Suggest a line",
    "## 3. Validate each line",
    "## 4. Show and approve",
    "## 5. Save",
    "## 6. Read back",
]

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
check("frontmatter-name", fields.get("name") == "plan-assembly-line", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

check_all("input-ticket-ids", block(skill, "## Input", r"^## "), "ticket id", "`plan-work`")
check_all("links-line-format", skill, "`../assembly-line/references/line-format.md`")
check_all("reads-existing-line", block(skill, "## 1. Read each ticket", r"^## "),
          "`assembly-line/1`", "created last", "new line comment")

section2 = block(skill, "## 2. Suggest a line", r"^## ")
check_all("reads-catalog", section2, "`../assembly-line/references/catalog.json`", "starts at `judge`",
          "ends at `merge`", "only stages in")

try:
    stages = set(json.loads(read(CATALOG) or "{}").get("stages", {}))
    catalog_ok = True
except (ValueError, AttributeError, TypeError):
    stages = set()
    catalog_ok = False
names = {d.name for d in SKILLS.iterdir() if (d / "SKILL.md").is_file()}
offered = {token for token in re.findall(r"`([a-z][a-z0-9-]*)`", section2) if token in names}
check("only-catalog-stages", catalog_ok and offered and offered <= stages,
      f"not in catalog: {sorted(offered - stages)}" if catalog_ok and offered else
      ("catalog.json does not parse" if not catalog_ok else "section 2 names no stage"))

check_all("suggestion-rules", section2, "`[unit]`", "`[int]`", "`[e2e]`", "`[story]`", "`## Design`", "`[ui]`",
          "`[docs]`", "`feat`", '`{"group": "sub-issues"}`', "sub-issues join the list", "why")
check_all("validates-before-showing", block(skill, "## 3. Validate each line", r"^## "),
          "`$SKILL_DIR/../assembly-line/scripts/validate-line.py`", "`{scratch}/<ticket>.line.json`", '`"valid"`',
          "before showing", "`stage`", "`rule`", "stage to add", "`takes-met`", "delivered by")
check_all("line-file-is-full-object", block(skill, "## 3. Validate each line", r"^## "),
          "full line object", "`format`", "`ticket`", "`stages`", "not a bare list")
check("validator-resolves",(SKILL / "../assembly-line/scripts/validate-line.py").resolve().exists(),
      f"{VALIDATOR} missing")
check_all("approval-first", block(skill, "## 4. Show and approve", r"^## "),
          "confirms or edits", "nothing is written", "before the engineer approves", "validated again",
          "not saved", "one table")
check_all("saves-comment", block(skill, "## 5. Save", r"^## "),
          "one comment per ticket", "tracker tool", "`## Assembly line`", "json block",
          "exactly the approved line", "never edit or delete")
check_all("reads-back", block(skill, "## 6. Read back", r"^## "),
          "reads it back", "matches the approved line", "link per ticket", "not saved and why", "not post again")
check("no-skill-dir-var", SKILL_MD.exists() and "${CLAUDE_SKILL_DIR}" not in skill,
      "SKILL.md missing or names ${CLAUDE_SKILL_DIR}")

found = re.findall(r"^## .*$", skill, re.MULTILINE)
check("no-heading-in-sections", found == HEADINGS, f"headings are {found}")

broken = [target for target in sorted(set(re.findall(r"`(\.\.?/[^`\s]+\.(?:md|json))`", skill)))
          if not (SKILL / target).resolve().exists()]
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

check_all("plan-work-hands-off", block(read(PLAN_WORK), "### 7. Hand off", r"^## "),
          "`plan-assembly-line`", "role: engineer")

check("readme-section", re.search(r"^### plan-assembly-line$", readme, re.MULTILINE),
      "README has no ### plan-assembly-line")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "),
          "skills/plan-assembly-line/scripts/check-plan-assembly-line.py")
check_all("readme-count", readme, "thirty-three claude code skills", "the other thirty-one", "the same thirty-three")
missing_manifests = [str(m.relative_to(REPO)) for m in MANIFESTS if "line planner" not in flatten(read(m))]
check("manifests-name-it", not missing_manifests, f"missing 'line planner': {missing_manifests}")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    out = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        out += f"  {detail}"
    print(out)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
