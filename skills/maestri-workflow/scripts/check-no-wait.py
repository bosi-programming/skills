import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SKILL_MD = SKILL / "SKILL.md"
RELAY_MD = REPO / "skills" / "recipe-relay" / "SKILL.md"
README = REPO / "README.md"

STOP_PHRASES = [
    "stop and ask",
    "ask the user",
    "tell the user which",
    "goes to the user",
    "ask for every missing input",
    "waiting on a merge",
    "bring the open question to the user",
    "give them a beat",
]
RELAY_PAUSES = [
    "give them a beat",
    "visible checkpoint",
]
RELAY_STOPS = [
    "report the open question to the user",
]
RUNTIME_VARIABLE = re.compile(r"\$\{CLAUDE_SKILL_DIR\}")
RELATIVE_PATH = re.compile(r"(?<![\w/.{}])\.{1,2}/[\w.-][\w./-]*")
SECTION_HEADING = re.compile(r"^## (\d)\.", re.MULTILINE)
FIRST_STEP = re.compile(r"^1\. ", re.MULTILINE)

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def read(path):
    return path.read_text() if path.exists() else ""


def sections(text):
    marks = list(SECTION_HEADING.finditer(text))
    found = {}
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        found[int(mark.group(1))] = text[mark.start():end]
    return found


def preamble(section):
    step = FIRST_STEP.search(section)
    return section[:step.start()] if step else section


def frontmatter_description(text):
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    return match.group(1) if match else ""


def readme_block(text, start, stop_pattern):
    begin = text.find(start)
    if begin < 0:
        return ""
    rest = text[begin + len(start):]
    stop = re.search(stop_pattern, rest, re.MULTILINE)
    return rest[:stop.start()] if stop else rest


def flatten(text):
    return " ".join(text.split()).lower()


def has_all(text, *phrases):
    lowered = flatten(text)
    missing = [phrase for phrase in phrases if phrase.lower() not in lowered]
    return not missing, f"missing: {missing}" if missing else ""


def check_all(name, text, *phrases):
    ok, detail = has_all(text, *phrases)
    check(name, ok, detail)


skill = read(SKILL_MD)
part = sections(skill)
one, two, three, four, five = (part.get(number, "") for number in range(1, 6))
relay = read(RELAY_MD)
readme = read(README)

lowered_skill = flatten(skill)
found_stops = [phrase for phrase in STOP_PHRASES if phrase in lowered_skill]
check("no-stop-phrases", not found_stops, f"found: {found_stops}")

check_all("lanes-default", one, "recommended lanes", "Taken without asking")
check_all("dirty-tree-worktree", two, "git worktree add", "default branch", "untouched")
check_all("worktree-reused-on-resume", two, "git worktree list", "reuse", "resume")
check(
    "work-root-used",
    "{repo root}" not in skill and '--dir "{work root}"' in three,
    "want no {repo root} and --dir \"{work root}\" in section 3",
)
check_all("legacy-rename-logged", two, "legacy.md", "log the move")
check_all("note-headings", two, "Questions and problems", "Taken without asking")
check_all("model-pin-fallback", three, "harness default", "log the model")
check_all("recommendation-taken", three, "New session", "needs-input", "blocked", "take the recommendation")
check_all("note-questions-settled", three, "recommended option", "under the entry")
check_all("single-draft-pr", three, "one draft PR", "no chunks")
check_all("one-way-doors-in-pr-body", four, "one-way door", "never take", "## Left for you", "PR body")
check_all("pr-stays-draft", four, "stays a draft")

check_all("scope-maestri-only", preamble(three), "only under maestri-workflow", "keeps its stop conditions")
found_pauses = [phrase for phrase in RELAY_PAUSES if phrase in flatten(relay)]
check("recipe-relay-no-pause", not found_pauses, f"found: {found_pauses}")
missing_stops = [phrase for phrase in RELAY_STOPS if flatten(phrase) not in flatten(relay)]
check("recipe-relay-keeps-stops", not missing_stops, f"missing: {missing_stops}")

relay_part = sections(relay)
check_all(
    "recipe-relay-review",
    relay_part.get(5, ""),
    "../bosi-code-review/SKILL.md",
    "merge base",
    "asks no questions",
    "skips the HTML report",
    "file:line",
    "failing test first",
)
check("review-not-repeated", "bosi-code-review/SKILL.md" not in skill, "maestri-workflow briefs its own review")
check_all("review-lane", three, "code review", "planning lane")

check_all("report-lists-decisions", five, "draft PR", "default", "fallback", "Taken without asking", "one-way door")

no_pr_four, detail_four = has_all(four, "no remote", "`gh` auth", "the flow ends")
no_pr_five, detail_five = has_all(five, "no PR", "first")
check("no-pr-edge-case", no_pr_four and no_pr_five, f"{detail_four} {detail_five}".strip())
check_all("one-retry-only", three, "re-run the unit once", "stops again", "the flow ends")

check_all("description-no-wait", frontmatter_description(skill), "draft PR", "never stops to ask")
paragraph = readme_block(readme, "### maestri-workflow", r"^### ")
check_all("readme-paragraph", paragraph, "draft PR", "never stops to ask")
check(
    "readme-layout-scripts",
    re.search(r"^\s*maestri-workflow/\s+SKILL\.md \+ scripts/", readme, re.MULTILINE),
    "layout line must list scripts/",
)
validate = readme_block(readme, "## Validate a change", r"^## ")
check_all("readme-validate-command", validate, "check-no-wait.py")

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
