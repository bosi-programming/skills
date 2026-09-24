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
step_three = block(skill, "### 3. Identify the standards sources", r"^### ")
step_four = block(skill, "### 4. Spawn", r"^### ")
step_five = block(skill, "### 5. Aggregate", r"^### ")
headless = block(skill, "\n## Headless\n", r"^## ")

check_all("tooling-read", step_three, "lint", "type-check", "config", "enabled rules")
check("tooling-passed", flatten(step_four).count("enabled rules") >= 2, "Standards and Tests prompts must carry the enabled rules")
check("no-bare-tooling-skip", "skip anything tooling enforces" not in flatten(step_four), "briefs still say skip anything tooling enforces")

check_all("epistemic-linked", step_five, "../epistemic-action/SKILL.md")
check_all("evidence-tags", step_five, "`ran`", "`read`", "`no`")
check_all("runs-project-checks", step_five, "test", "lint", "type-check", "scoped", "Not verified")
check_all("mutation-probe", step_five, "missing test", "tautological", "break the line", "restore", "cut the finding")
check_all("probe-worktree", step_five, "git worktree add", "git worktree remove", "never probe in the user's working tree")
check_all("conditions-recorded", step_five, "commit", "branch")

check_all("headless-verified-levels", headless, "Verified: ran | read | no")
check_all("headless-reviewed-line", headless, "Reviewed: <sha> on <branch>")

check_all("readme-review", block(readme, "### better-code-review", r"^### "), "epistemic-action", "probe")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-evidence.py")

unresolved = [path for path in re.findall(r"\]\((\.\.?/[^)]+)\)", skill) if not (SKILL / path).resolve().exists()]
check("links-resolve", not unresolved, f"unresolved: {unresolved}")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
