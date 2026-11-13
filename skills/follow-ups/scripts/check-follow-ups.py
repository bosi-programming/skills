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
TEMPLATE = REPO / "skills" / "feature-recipe" / "references" / "recipe-card-template.md"
PLUGINS = [REPO / ".claude-plugin" / "plugin.json", REPO / ".codex-plugin" / "plugin.json"]
MANIFESTS = PLUGINS + [REPO / "package.json"]

PRIVATE = ["~/dev/", "aopost", "felipe", "linear-server", "goto-", "cw new", "controller", "ao-adr"]

SECTIONS = [
    "## Input",
    "## Output",
    "## 1. Read the open items",
    "## 2. Search the tracker first",
    "## 3. Open and link",
    "## 4. Write the follow-ups",
    "## Headless",
]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def read(path):
    return path.read_text() if path.exists() else ""


def load(path):
    try:
        return json.loads(read(path) or "{}")
    except ValueError:
        return {}


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
    check(name, text and not missing, f"missing: {missing}" if missing else "block missing")


skill = read(SKILL_MD)
readme = read(README)
template = read(TEMPLATE)
stage = load(STAGE)

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
check("frontmatter-name", fields.get("name") == "follow-ups", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

found = re.findall(r"^## .*$", skill, re.MULTILINE)
check("section-order", found == SECTIONS, f"headings are {found}")

check_all("reads-items", block(skill, "## 1. Read the open items", r"^## "),
          "`## Open Questions`", "`answer:`", "`## Quality Gate Results`", "`Not verified:`",
          "judgement call", "scope creep", "`medium`", "`low`", "`moderate`", "`minor`", "`none`",
          "`## Decisions`", "`unattended:`", "one ticket for all", "html comment",
          "skip lines that start `unattended: follow-ups`")

check_all("searches-first", block(skill, "## 2. Search the tracker first", r"^## "),
          "`Source:`", "related", "team", "canceled", "matched", "no tracker tool",
          "`runStatus: blocked`", "`blocked`")

check_all("opens-and-links", block(skill, "## 3. Open and link", r"^## "),
          "team and project", "default state", "`follow-up: <summary>`",
          "`Source: <run ticket> — <kind> — <ref>`", "related", "never edit", "never close")

check_all("writes-follow-ups", block(skill, "## 4. Write the follow-ups", r"^## "),
          "`## Follow-ups`", "`- <kind> <ref> — <ticket> <url> — <opened | matched>`",
          "`- none — no open items on the card`", "replaces", "adds the heading",
          "`<prefix> follow-ups — <n> opened, <m> matched`", "`done`", "`lastTouched`")

check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: blocked`", "### Ending a run")
check_all("log-prefixes", skill, "`relay:`", "`line:`", "`unattended:`", "`follow-ups:`",
          "`../feature-recipe/references/recipe-card-template.md`")

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
          "takes": ["task", "## Open Questions", "## Quality Gate Results", "## Decisions"],
          "delivers": {
              "sections": ["## Follow-ups", "## Decisions"],
              "fields": ["lastTouched"],
              "verdicts": ["done", "blocked"],
          },
          "return": {"blocked": {"to": "follow-ups", "limit": 0, "past": "needs-input"}},
          "signals": [],
          "gate": "auto",
      },
      "stage.json differs from the card's Interfaces")

template_block = block(template, "\n## Follow-ups\n", r"^## ")
check("template-section",
      re.search(r"^## Follow-ups$", template, re.MULTILINE) and "follow-ups" in template_block.lower(),
      "card template has no ## Follow-ups section written by follow-ups")
check_all("template-formats", template_block,
          "<kind> <ref> — <ticket> <url> — <opened | matched>", "none — no open items on the card")
headings = re.findall(r"^## .*$", template, re.MULTILINE)
after_pr = headings[headings.index("## PR") + 1] if "## PR" in headings[:-1] else None
check("template-after-pr", after_pr == "## Follow-ups", f"heading after ## PR is {after_pr!r}")

check("readme-section", re.search(r"^### follow-ups$", readme, re.MULTILINE), "README has no ### follow-ups")
check_all("readme-intro", readme, "`follow-ups` opens a ticket for each item a run left open",
          "follow-ups/ SKILL.md + stage.json + scripts/")
check_all("readme-validate-paragraph", block(readme, "## Validate a change", r"^## Falsify"),
          "`check-follow-ups.py` is `follow-ups`' own check")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## Falsify"),
          "skills/follow-ups/scripts/check-follow-ups.py", "check-stage-spec.py skills/follow-ups")

missing_name = [str(m.relative_to(REPO)) for m in PLUGINS
                if "follow-up tickets" not in str(load(m).get("description", "")).lower()]
check("manifests-name-it", not missing_name, f"description lacks 'follow-up tickets': {missing_name}")

manifest_versions = {str(m.relative_to(REPO)): load(m).get("version") for m in MANIFESTS}
check("manifests-version", len(set(manifest_versions.values())) == 1 and None not in manifest_versions.values(),
      f"manifest versions differ: {manifest_versions}")


def minor_of(version):
    match = re.match(r"^(\d+)\.(\d+)\.\d+$", version or "")
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


check("version-bumped", all(minor_of(v) > (2, 64) for v in manifest_versions.values()),
      f"version not past 2.64: {manifest_versions}")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
