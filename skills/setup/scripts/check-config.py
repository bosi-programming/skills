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
README = REPO / "README.md"

KEYS = {
    "work-summary.outputDir": "~/work-sessions",
    "feature-recipe.cardsDir": "./recipes",
    "feature-recipe.defaultMode": "regular",
    "better-code-review.defaultMode": "conversation",
}

CONSUMERS = {
    SKILLS / "work-summary" / "SKILL.md": ["work-summary.outputDir"],
    SKILLS / "feature-recipe" / "phases" / "phase-0-start.md": [
        "feature-recipe.cardsDir",
        "feature-recipe.defaultMode",
    ],
    SKILLS / "better-code-review" / "SKILL.md": ["better-code-review.defaultMode"],
    SKILLS / "maestri-workflow" / "SKILL.md": ["feature-recipe.cardsDir"],
}

PRIVATE = ["~/dev/", "notion.com", "check-kinds", "llm-work-session", "dao-142", "core values"]

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

ws = read(WORK_SUMMARY / "SKILL.md")
check("work-summary-exists", re.search(r"^name: work-summary$", ws, re.MULTILINE), "skills/work-summary/SKILL.md missing")
evals = sorted((WORK_SUMMARY / "evals").glob("scenario-*.json"))
bodies = []
for path in evals:
    try:
        json.loads(path.read_text())
        bodies.append(path.read_text())
    except ValueError:
        check(f"eval-parses:{path.name}", False, "not valid JSON")
check("work-summary-evals", evals, "work-summary/evals has no scenarios")
leaks = [w for w in PRIVATE if w in (ws + "".join(bodies)).lower()]
check("work-summary-is-private-free", not leaks, f"private content: {leaks}")
check("work-summary-no-fixed-dir", "work-sessions" not in ws.replace("`~/work-sessions`", ""),
      "work-summary must take its folder from the config, not hard-code it")

readme = read(README)
check("readme-validate-command", "check-config.py" in readme, "README must list check-config.py")

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
