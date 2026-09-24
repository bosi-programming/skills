import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
TEMPLATE = SKILL / "assets" / "report-template.html"
CATALOG = REPO / "skills" / "code-standards"
CATALOG_MD = CATALOG / "SKILL.md"
TESTS_STANDARD = CATALOG / "Testing" / "Tests.md"
README = REPO / "README.md"
TASTING = REPO / "skills" / "feature-recipe" / "phases" / "phase-4-tasting.md"
MANIFESTS = [
    REPO / ".claude-plugin" / "plugin.json",
    REPO / ".codex-plugin" / "plugin.json",
]

TEST_RULES = [
    "behaviour, not implementation",
    "scenario",
    "one reason to fail",
    "arrange",
    "deterministic",
    "isolated",
    "mock",
    "specific assertions",
    "error paths",
    "bug fix",
    "tautolog",
]
RED_FLAGS = [".skip", ".only", "commented-out", "no assertion"]

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


standard = read(TESTS_STANDARD)
catalog = read(CATALOG_MD)
skill = read(SKILL_MD)
template = read(TEMPLATE)
readme = read(README)

check("standard-exists", standard, f"{TESTS_STANDARD} missing")
check_all("standard-rules", standard, *TEST_RULES)
check_all("standard-red-flags", block(standard, "## Red flags", r"^## "), *RED_FLAGS)
check_all("catalog-lists-standard", catalog, "Testing/Tests.md", "Five files")
check_all("catalog-description", frontmatter_description(catalog), "tests")

step_three = block(skill, "### 3. Identify the standards sources", r"^### ")
step_four = block(skill, "### 4. Spawn", r"^### ")
step_five = block(skill, "### 5. Aggregate", r"^### ")
headless = block(skill, "\n## Headless\n", r"^## ")

check_all("description-tests-axis", frontmatter_description(skill), "three axes", "Tests")
check_all("intro-tests-axis", block(skill, "---\n\n", r"^## Process"), "**Tests**", "three tabs")
check_all("sources-tests", step_three, "Tests axis", "../code-standards/Testing/Tests.md")
check_all("tests-sub-agent", step_four, "Tests sub-agent prompt", "missing test", "no tests to review")
check_all("aggregate-three", step_five, "`Tests`")
check_all("headless-tests", headless, "Spec | Standards | Tests", "missing test", "Tests <n>", "no tests to review")
check_all("why-three-axes", skill, "## Why three axes")
check("no-two-axis-wording", "two tabs" not in flatten(skill) and "two-axis" not in flatten(skill), "SKILL.md still says two tabs or two-axis")

check_all("template-tab", template, 'id="tab-tests"', 'aria-controls="tests"')
check_all("template-panel", template, '<section id="tests"', 'data-goto="tests"', "card tests")
check_all("template-hash", template, "want === 'tests'")
check("template-board", re.search(r"\.board\{[^}]*repeat\(3,\s*1fr\)", template), "board must have three columns")
check("template-no-two-axis", "two-axis" not in flatten(template), "template still says two-axis")

check_all("readme-review", block(readme, "### better-code-review", r"^### "), "three axes", "Tests")
check_all("readme-catalog", block(readme, "### code-standards", r"^### "), "five files", "Testing/Tests.md")
check_all("readme-validate-command", block(readme, "## Validate a change", r"^## "), "check-tests-axis.py")
check_all("tasting-triages-tests", block(read(TASTING), "## 1. Run the review", r"^## "), "**Tests**", "missing test")
stale = [str(path.relative_to(REPO)) for path in MANIFESTS if "two-axis" in flatten(read(path))]
check("manifests-three-axis", not stale, f"still two-axis: {stale}")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
