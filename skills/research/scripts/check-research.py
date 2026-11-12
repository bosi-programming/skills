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
    "## 1. Read the questions",
    "## 2. Answer each question",
    "## 3. Write the findings",
    "## 4. Post the output",
    "## 5. Gate",
    "## Headless",
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

try:
    stage = json.loads(read(STAGE) or "{}")
except ValueError:
    stage = {}

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
check("frontmatter-name", fields.get("name") == "research", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

found = re.findall(r"^## .*$", skill, re.MULTILINE)
check("section-order", found == SECTIONS, f"headings are {found}")

check_all("answers", block(skill, "## 2. Answer each question", r"^## "),
          "source", "claim", "left out", "`open`", "what was tried", "`## Open Questions`",
          "{scratch}/research/", "never commit")

check_all("output-comment", block(skill, "## 4. Post the output", r"^## "),
          "one new comment", "never edit", "opens no tickets", "no tracker tool", "not posted")

check_all("gate", block(skill, "## 5. Gate", r"^## "),
          "`runStatus: gate`", "`approved`", "`changes`", "before the gate")

check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: needs-input`", "### Ending a run")
check_all("log-prefixes", skill, "`relay:`", "`line:`", "`unattended:`", "`research:`")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")
check("no-skill-dir-var", SKILL_MD.exists() and "${CLAUDE_SKILL_DIR}" not in skill,
      "SKILL.md missing or names ${CLAUDE_SKILL_DIR}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

check("stage-exact",
      stage == {
          "spec": "../assembly-line/references/stage-spec.md",
          "takes": ["task"],
          "delivers": {
              "sections": ["## Findings", "## Decisions", "## Open Questions"],
              "fields": ["lastTouched"],
              "verdicts": ["approved", "changes"],
          },
          "return": {"changes": {"to": "research", "limit": 2, "past": "human"}},
          "signals": [],
          "gate": "human",
      },
      "stage.json differs from the card's Interfaces")

check("readme-section", re.search(r"^### research$", readme, re.MULTILINE), "README has no ### research")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "skills/research/scripts/check-research.py", "check-stage-spec.py skills/research")

manifest_versions = {str(m.relative_to(REPO)): json.loads(read(m)).get("version") for m in MANIFESTS}
check("manifests-version", len(set(manifest_versions.values())) == 1 and None not in manifest_versions.values(),
      f"manifest versions differ: {manifest_versions}")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
