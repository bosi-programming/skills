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
MANIFESTS = [REPO / ".claude-plugin" / "plugin.json", REPO / ".codex-plugin" / "plugin.json"]

PRIVATE = ["~/dev/", "aopost", "felipe", "linear-server", "goto-", "cw new", "controller", "ao-adr"]

SECTIONS = [
    "## Input",
    "## Output",
    "## Settings",
    "## 1. Reach the app",
    "## 2. Scan",
    "## 3. Keyboard walk",
    "## 4. Verdict",
    "## Headless",
]

RULES = ["keyboard-reach", "keyboard-trap", "aria-hidden-focusable", "focus-indicator", "modal-focus", "route-focus"]

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
check("frontmatter-name", fields.get("name") == "a11y-check", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

check_all("input-is-work-card", block(skill, "## Input", r"^## "),
          "work card", "`task`", "`## Solution`", "`../feature-recipe/references/recipe-card-template.md`")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output, "`## Accessibility`", "`## Quality Gate Results`", "`## Decisions`",
          "`## Open Questions`", "`lastTouched`", "Verdict:", "Reason:", "### Round <n>")
check_all("lists-verdicts", output, "`pass`", "`fail`", "`inconclusive`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")

check_all("settings-keys", block(skill, "## Settings", r"^## "),
          "`a11y-check.devCommand`", "`a11y-check.baseUrl`", "`''`", "`../setup/references/config.md`")

check_all("reach-step", block(skill, "## 1. Reach the app", r"^## "),
          "`a11y-check.devCommand`", "`a11y-check.baseUrl`", "`inconclusive`", "120 s", "stops the process",
          "names no route", "`## Solution`")

check_all("scan-step", block(skill, "## 2. Scan", r"^## "),
          "axe-core", "playwright", "chromium", "`impact`", "{scratch}/a11y-check/", "naming the tool",
          "`inconclusive`")

check_all("walk-rules", block(skill, "## 3. Keyboard walk", r"^## "),
          *[f"`{rule}`" for rule in RULES], "`../code-standards/Frontend/Accessibility.md`", "`n/a`")

check_all("verdict-step", block(skill, "## 4. Verdict", r"^## "),
          "`critical`", "`serious`", "`moderate`", "`minor`", "`fail`", "`pass`", "`inconclusive`",
          "`## Quality Gate Results`", "`code`", "twice", "`needs-input`", "`Round <n>`")

check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: needs-input`", "### Ending a run")
check_all("log-prefixes", skill, "`relay:`", "`line:`", "`unattended:`", "`a11y-check:`")

found = re.findall(r"^## .*$", skill, re.MULTILINE)
check("section-order", found == SECTIONS, f"headings are {found}")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")
check("no-skill-dir-var", SKILL_MD.exists() and "${CLAUDE_SKILL_DIR}" not in skill,
      "SKILL.md missing or names ${CLAUDE_SKILL_DIR}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

returns = stage.get("return") if isinstance(stage.get("return"), dict) else {}
check("stage-return-code",
      returns.get("fail") == {"to": "code", "limit": 2, "past": "needs-input"} and stage.get("gate") == "auto",
      "stage.json must return fail to code twice, then needs-input, with gate auto")
delivers = stage.get("delivers") if isinstance(stage.get("delivers"), dict) else {}
check("stage-verdicts", delivers.get("verdicts") == ["pass", "fail", "inconclusive"],
      "stage.json verdicts must be pass, fail, inconclusive")
check("stage-exact",
      stage == {
          "spec": "../assembly-line/references/stage-spec.md",
          "takes": ["task", "## Solution"],
          "delivers": {
              "sections": ["## Accessibility", "## Quality Gate Results", "## Decisions", "## Open Questions"],
              "fields": ["lastTouched"],
              "verdicts": ["pass", "fail", "inconclusive"],
          },
          "return": {"fail": {"to": "code", "limit": 2, "past": "needs-input"}},
          "signals": [],
          "gate": "auto",
      },
      "stage.json differs from the card's Interfaces")

check("readme-section", re.search(r"^### a11y-check$", readme, re.MULTILINE), "README has no ### a11y-check")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "skills/a11y-check/scripts/check-a11y-check.py", "check-stage-spec.py skills/a11y-check")

bad_versions = [str(m.relative_to(REPO)) for m in MANIFESTS if '"version": "2.62.0"' not in read(m)]
check("manifests-version", not bad_versions, f"not at 2.62.0: {bad_versions}")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
