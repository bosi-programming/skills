import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SKILLS = SKILL.parent
REPO = SKILLS.parent
SKILL_MD = SKILL / "SKILL.md"
CONFIG_MD = SKILL / "references" / "config.md"
TEMPLATE = SKILL / "assets" / "bosi-skills.md"
WORK_SUMMARY = SKILLS / "work-summary"
WEEK_SUMMARY = SKILLS / "week-summary"
README = REPO / "README.md"
AGENTS = REPO / "AGENTS.md"

KEYS = {
    "work-summary.outputDir": "~/work-sessions",
    "week-summary.reviewsDir": "~/week-reviews",
    "week-summary.weekStart": "saturday",
    "week-summary.proseSkill": "un-ai",
    "week-summary.logicSymbols": "true",
    "week-summary.valuesHeading": "Values",
    "feature-recipe.cardsDir": "./recipes",
    "feature-recipe.defaultMode": "regular",
    "better-code-review.defaultMode": "conversation",
    "feature-recipe.runWorkSummary": "true",
    "feature-recipe.docsDestination": "''",
    "maestri-workflow.planningModel": "''",
    "maestri-workflow.codingModel": "''",
}

DERIVED = [
    "week-summary.workSessionsDir",
    "week-summary.githubLogin",
    "week-summary.email",
    "week-summary.sessionCitation",
]

CONSUMERS = {
    SKILLS / "work-summary" / "SKILL.md": ["work-summary.outputDir"],
    SKILLS / "week-summary" / "SKILL.md": [key for key in KEYS if key.startswith("week-summary.")] + DERIVED,
    SKILLS / "feature-recipe" / "phases" / "phase-0-start.md": [
        "feature-recipe.cardsDir",
        "feature-recipe.defaultMode",
    ],
    SKILLS / "better-code-review" / "SKILL.md": ["better-code-review.defaultMode"],
    SKILLS / "maestri-workflow" / "SKILL.md": [
        "feature-recipe.cardsDir",
        "maestri-workflow.planningModel",
        "maestri-workflow.codingModel",
    ],
    SKILLS / "feature-recipe" / "phases" / "phase-6-documentation.md": [
        "feature-recipe.runWorkSummary",
        "feature-recipe.docsDestination",
    ],
}

PRIVATE = ["~/dev/", "notion.com", "check-kinds", "llm-work-session", "dao-", "core values", "2-areas/", "lattice", "felipe", "always-do-right"]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def read(path):
    return path.read_text() if path.exists() else ""


def flatten(text):
    return " ".join(text.split()).lower()


def frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    return match.group(1) if match else ""


def nested_keys(yaml_text):
    keys, section = set(), None
    for line in yaml_text.splitlines():
        top = re.match(r"^([A-Za-z-]+):\s*$", line)
        child = re.match(r"^  ([A-Za-z]+):", line)
        if top:
            section = top.group(1)
        elif child and section:
            keys.add(f"{section}.{child.group(1)}")
    return keys


def links_from(path, text):
    return [(path.parent / target).resolve() for target in re.findall(r"`(\.\.?/[^`\s]+\.md)`", text)]


skill = read(SKILL_MD)
config = read(CONFIG_MD)
template = read(TEMPLATE)

check("setup-skill-exists", re.search(r"^name: setup$", skill, re.MULTILINE), "skills/setup/SKILL.md must declare name: setup")
check("setup-points-at-contract", "`./references/config.md`" in skill and "`./assets/bosi-skills.md`" in skill,
      "setup must name ./references/config.md and ./assets/bosi-skills.md")

flat = flatten(config)
check("config-names-file", "`.bosi-skills.md`" in config, "config.md must name .bosi-skills.md")
check("config-lookup-order", re.search(r"current folder.*\$home.*default", flat), "config.md must give the order: current folder, $HOME, default")
check("config-per-key", "each setting" in flat, "config.md must say each setting falls back on its own")
missing = [key for key, default in KEYS.items() if f"`{key}`" not in config or f"`{default}`" not in config]
check("config-documents-keys", not missing, f"undocumented key or default: {missing}")

keys = nested_keys(frontmatter(template))
missing = [key for key in KEYS if key not in keys]
check("template-carries-keys", not missing, f"template frontmatter lacks: {missing}")
check("template-is-private-free", not [w for w in PRIVATE if w in template.lower()], "template names private content")

for path, needed in CONSUMERS.items():
    text = read(path)
    name = path.relative_to(SKILLS).as_posix()
    points = CONFIG_MD.resolve() in links_from(path, text)
    absent = [key for key in needed if f"`{key}`" not in text]
    check(f"reads-config:{name}", points and not absent,
          f"needs a relative link to setup/references/config.md and keys {absent}" if not points or absent else "")

missing = [key for key in DERIVED if f"`{key}`" not in config]
check("config-documents-derived-keys", not missing, f"undocumented key: {missing}")


def check_moved_skill(directory, extra=()):
    name = directory.name
    text = read(directory / "SKILL.md")
    check(f"{name}-exists", re.search(rf"^name: {name}$", text, re.MULTILINE), f"skills/{name}/SKILL.md missing")
    evals = sorted((directory / "evals").glob("scenario-*.json"))
    bodies = []
    for path in evals:
        try:
            json.loads(path.read_text())
            bodies.append(path.read_text())
        except ValueError:
            check(f"eval-parses:{name}/{path.name}", False, "not valid JSON")
    check(f"{name}-evals", evals, f"{name}/evals has no scenarios")
    shipped = text + "".join(bodies) + "".join(read(directory / path) for path in extra)
    leaks = [word for word in PRIVATE if word in shipped.lower()]
    check(f"{name}-is-private-free", not leaks, f"private content: {leaks}")
    return text


ws = check_moved_skill(WORK_SUMMARY)
check("work-summary-no-fixed-dir", "work-sessions" not in ws.replace("`~/work-sessions`", ""),
      "work-summary must take its folder from the config, not hard-code it")

wk = check_moved_skill(WEEK_SUMMARY, ["templates/week-review.md"])
check("week-summary-template", "`./templates/week-review.md`" in wk and (WEEK_SUMMARY / "templates" / "week-review.md").exists(),
      "week-summary must point at ./templates/week-review.md and ship it")
check("week-summary-no-fixed-dir", not re.search(r"~/\S*reviews", wk.replace("`~/week-reviews`", "")) and "bosi-programming" not in wk,
      "week-summary must take its folders and login from the config")

readme = read(README)
check("readme-validate-command", "check-config.py" in readme, "README must list check-config.py")

agents = flatten(read(AGENTS))
check("agents-documents-settings", all(phrase in agents for phrase in ["## settings", "config.md", "bosi-skills.md", "check-config.py", "~/.bosi-skills.md"]),
      "AGENTS.md must give the workflow for adding a setting")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
