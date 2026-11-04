#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SKILLS = SKILL.parent
DEFAULT = SKILL / "references" / "line-format.md"
FORMAT = "assembly-line/1"

SECTIONS = {
    "marker": ("## Marker", ["```json", f'"format": "{FORMAT}"']),
    "order": ("## Stages and inputs", ["`stages`", '"stage"', '"with"', "`takes`", "`gate`", "`stage.json`"]),
    "parallel": ("## Parallel groups", ['"parallel"']),
    "latest-wins": ("## More than one line comment", ["created last"]),
    "sub-issues": ("## Sub-issue groups", ['"group"', '"sub-issues"', "`merge`"]),
}

EXAMPLES = {
    "full": "## Example: full line",
    "short": "## Example: short line",
    "parent": "## Example: parent line",
}

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def flatten(text):
    return " ".join(text.split()).lower()


def block(text, start):
    begin = text.find(start + "\n")
    if begin < 0:
        return None
    rest = text[begin + len(start):]
    stop = re.search(r"^## ", rest, re.MULTILINE)
    return rest[:stop.start()] if stop else rest


def stages():
    return {d.name for d in SKILLS.iterdir() if (d / "SKILL.md").is_file()}


def gate(name):
    path = SKILLS / name / "stage.json"
    try:
        return json.loads(path.read_text()).get("gate")
    except (OSError, ValueError):
        return None


def names(items):
    for item in items:
        if isinstance(item, str):
            yield item
        elif isinstance(item, dict) and isinstance(item.get("stage"), str):
            yield item["stage"]
        elif isinstance(item, dict) and isinstance(item.get("parallel"), list):
            yield from names(item["parallel"])


def check_sections(text):
    for name, (heading, phrases) in SECTIONS.items():
        body = block(text, heading)
        if body is None:
            check(f"section-{name}", False, f"no {heading} section")
            continue
        lowered = flatten(body)
        missing = [phrase for phrase in phrases if phrase.lower() not in lowered]
        check(f"section-{name}", not missing, f"missing: {missing}")


def parse(name, body):
    fence = re.search(r"```json\n(.*?)\n```", body, re.DOTALL)
    if not fence:
        check(f"{name}-parses", False, "no ```json block")
        return None
    try:
        line = json.loads(fence.group(1))
    except ValueError as error:
        check(f"{name}-parses", False, str(error))
        return None
    ok = isinstance(line, dict) and isinstance(line.get("stages"), list)
    check(f"{name}-parses", ok, "must be an object with a stages list")
    return line if ok else None


def check_line(name, line):
    items = line["stages"]
    check(f"{name}-format", line.get("format") == FORMAT, f"format is {line.get('format')!r}, want {FORMAT!r}")
    check(f"{name}-ticket", isinstance(line.get("ticket"), str) and line["ticket"], "ticket missing")
    check(f"{name}-first-judge", items[:1] == ["judge"], "the first stage must be judge")
    check(f"{name}-has-merge", "merge" in items, "merge missing from the top level")
    unknown = sorted(set(names(items)) - stages())
    check(f"{name}-known-stages", not unknown, f"not a skill under skills/: {unknown}")
    after = list(names(items[items.index("merge") + 1:])) if "merge" in items else []
    human = [stage for stage in after if gate(stage) != "auto"]
    check(f"{name}-auto-after-merge", not human, f"not gate auto after merge: {human}")
    return items


def check_examples(text):
    for name, heading in EXAMPLES.items():
        body = block(text, heading)
        if body is None:
            if name != "parent":
                check(f"example-{name}", False, f"no {heading} section")
            continue
        check(f"example-{name}", True)
        line = parse(name, body)
        if line is None:
            continue
        items = check_line(name, line)
        if name == "full":
            check("full-has-parallel", any(isinstance(i, dict) and "parallel" in i for i in items),
                  "the full line must hold a parallel group")
        if name == "parent":
            check("parent-has-group", {"group": "sub-issues"} in items, 'the parent line must hold {"group": "sub-issues"}')


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    check("exists", path.is_file(), f"{path} missing")
    if path.is_file():
        text = path.read_text()
        check_sections(text)
        check_examples(text)
    width = max(len(name) for name, _, _ in results)
    for name, ok, detail in results:
        line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
        if detail and not ok:
            line += f"  {detail}"
        print(line)
    failed = [name for name, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
