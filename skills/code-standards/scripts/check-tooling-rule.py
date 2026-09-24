import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"

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
checking = block(skill, "## Checking code against it", r"^## ")

check_all("tooling-config-read", checking, "lint", "format", "type-check", "config", "enabled rules")
check_all("no-config-skips-nothing", checking, "no such config", "skip nothing")
check("no-bare-tooling-skip", "skip anything a formatter, linter, or type-checker enforces" not in flatten(checking), "still says skip anything a formatter, linter, or type-checker enforces")

catalog = re.findall(r"^- `([^`]+\.md)`", skill, re.MULTILINE)
unresolved = [path for path in catalog if not (SKILL / path).exists()]
check("catalog-resolves", catalog and not unresolved, f"unresolved: {unresolved}")

check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-tooling-rule.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
