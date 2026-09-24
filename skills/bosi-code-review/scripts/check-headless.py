import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"

RUNTIME_VARIABLE = re.compile(r"\$\{CLAUDE_SKILL_DIR\}")
RELATIVE_PATH = re.compile(r"(?<![\w/.{}])\.{1,2}/[\w.-][\w./-]*")
FINDING_FIELDS = ["axis", "hard", "judgement call", "file:line", "fix", "verified"]

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


def frontmatter_description(text):
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    return match.group(1) if match else ""


skill = read(SKILL_MD)
readme = read(README)
headless = block(skill, "\n## Headless\n", r"^## ")
step_one = block(skill, "### 1. Pin the fixed point", r"^### ")
step_two = block(skill, "### 2. Identify the spec source", r"^### ")
step_six = block(skill, "### 6. Render the HTML report", r"^##+ ")

check("headless-section", headless.strip(), "SKILL.md has no ## Headless section")
check_all("headless-entry", headless, "--headless", "\"headless\"")
check_all("headless-never-asks", headless, "never asks")
check_all("headless-fixed-point", headless, "merge base", "default branch")
check_all("headless-no-spec", headless, "no spec available")
check_all("headless-still-verifies", headless, "step 5")
check_all("headless-no-html", headless, "no HTML", "verbose")
check_all("headless-finding-fields", headless, *FINDING_FIELDS)
check_all("headless-closing-lines", headless, "per-axis", "not verified")
check_all("step-one-defers", step_one, "headless")
check_all("step-two-defers", step_two, "headless")
check_all("step-six-defers", step_six, "headless")

check_all("description-headless", frontmatter_description(skill), "headless")
paragraph = block(readme, "### bosi-code-review", r"^### ")
check_all("readme-paragraph", paragraph, "--headless")
check(
    "readme-layout-scripts",
    re.search(r"^\s*bosi-code-review/\s+SKILL\.md .*scripts/", readme, re.MULTILINE),
    "layout line must list scripts/",
)
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-headless.py")

unresolved = sorted(
    {path for path in RELATIVE_PATH.findall(skill) if not (SKILL / path).resolve().exists()}
)
check("relative-paths-resolve", not unresolved, f"unresolved: {unresolved}")
check("no-runtime-variable", not RUNTIME_VARIABLE.search(skill), "SKILL.md names the runtime variable")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
