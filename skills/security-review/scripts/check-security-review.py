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
CHECKS = SKILL / "references" / "checks.md"

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
checks_md = read(CHECKS)

try:
    stage = json.loads(read(STAGE) or "{}")
except ValueError:
    stage = {}

check("skill-exists", SKILL_MD.exists(), f"{SKILL_MD} missing")

frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
fields = dict(re.findall(r"^(\w+): (.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
check("frontmatter-name", fields.get("name") == "security-review", f"name is {fields.get('name')!r}")
check("frontmatter-description", len(fields.get("description", "")) > 40, "description missing or too short")

check_all("input-is-work-card", block(skill, "## Input", r"^## "), "work card", "`task`", "`## Solution`")
check("no-recipe-card-wording", SKILL_MD.exists() and "recipe card" not in flatten(skill), "SKILL.md missing or still says recipe card")
check_all("fixed-point", block(skill, "## 1. Diff", r"^## "), "fixed point", "project rules", "merge-base", "origin/")

output = block(skill, "## Output", r"^## ")
check_all("lists-card-fields", output, "`## Security Review`", "`## Quality Gate Results`", "`## Decisions`",
          "`## Open Questions`", "`lastTouched`")
check_all("lists-verdicts", output, "`pass`", "`fail`")
check_all("leaves-routing-alone", output, "`phase`", "`phasesCompleted`")

check_all("review-step", block(skill, "## 2. Review", r"^## "),
          "one", "sub-agent", "`./references/checks.md`", "never edits", "file", "line", "check id",
          "`critical`", "`high`", "`medium`", "`low`")
check_all("verdict-step", block(skill, "## 3. Verdict", r"^## "),
          "`critical` or `high`", "`fail`", "`medium` and `low`", "`pass`", "empty diff",
          "`## Quality Gate Results`", "`code`", "twice", "`needs-input`", "`Round <n>`")
check_all("keeps-headless", block(skill, "## Headless", r"^## "),
          "unattended:", "`runStatus: needs-input`", "### Ending a run")
check_all("log-prefixes", skill, "`relay:`", "`line:`", "`unattended:`", "`security-review:`")

sections = [m.group(0) for m in re.finditer(r"^## .*$", skill, re.MULTILINE)]
check("section-order",
      [s for s in sections if s in ("## Input", "## Output", "## 1. Diff", "## 2. Review", "## 3. Verdict", "## Headless")]
      == ["## Input", "## Output", "## 1. Diff", "## 2. Review", "## 3. Verdict", "## Headless"],
      f"sections: {sections}")

broken = []
for target in sorted(set(re.findall(r"`(\.{1,2}/[^`\s]+\.md)`", skill))):
    if not (SKILL / target).resolve().exists():
        broken.append(target)
check("links-resolve", SKILL_MD.exists() and not broken, f"broken: {broken}")

leaks = [word for word in PRIVATE if word in skill.lower()]
check("private-free", SKILL_MD.exists() and not leaks, f"private content: {leaks}")

check_all("checks-file", checks_md, "## OWASP Top 10 (2021)", "## OWASP ASVS 4.0.3 level 1", "ASVS 4.0.3", "V2.10.4",
          *[f"A{n:02d}:2021" for n in range(1, 11)])

returns = stage.get("return") if isinstance(stage.get("return"), dict) else {}
check("stage-return-code",
      returns.get("fail") == {"to": "code", "limit": 2, "past": "needs-input"} and stage.get("gate") == "auto",
      "stage.json must return fail to code twice, then needs-input, with gate auto")
delivers = stage.get("delivers") if isinstance(stage.get("delivers"), dict) else {}
check("stage-verdicts", delivers.get("verdicts") == ["pass", "fail"] and stage.get("signals") == [],
      "stage.json verdicts must be pass, fail and signals empty")

check("readme-section", re.search(r"^### security-review$", readme, re.MULTILINE), "README has no ### security-review")
validate = block(readme, "## Validate a change", r"^## ")
check_all("readme-validate-command", validate,
          "skills/security-review/scripts/check-security-review.py",
          "skills/assembly-line/scripts/check-stage-spec.py skills/security-review")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
