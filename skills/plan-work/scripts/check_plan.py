import argparse
import json
import re
import sys

TAGS = {"unit", "int", "api", "e2e", "ui", "story", "run", "docs", "manual", "design"}
PART_TAGS = {"unit", "int", "story"}
SCREEN_TAGS = {"ui", "story"}
ISSUE_SECTIONS = ["What", "Who notices and how", "Technical design", "Out of scope", "Acceptance criteria"]
DELIVERABLE = "Design deliverable"
DESIGN_TICKET_SECTIONS = ["What", "Who notices and how", DELIVERABLE, "Out of scope", "Acceptance criteria"]
DESIGN_EXEMPT = re.compile(r"^- (No visual change|No design yet):", re.MULTILINE)
FRONTEND_LINE = re.compile(r"^- Frontend ticket:\s*(\S+)", re.MULTILINE)
PART_SECTIONS = ["What", "Technical design", "Repos and key paths", "Acceptance criteria"]
REMOVAL_SECTION = "Removes"
PLACEHOLDER = re.compile(r"\[\[gap\b|<[a-z][^<>\n]*>|\bTBD\b|\bTODO\b")
CRITERION = re.compile(r"^- \[[ x]\] #(\d+) \[([a-z0-9]+)\] \S")
FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
CODE_SPAN = re.compile(r"`([^`\n]*)`")
TEMPLATE_SPANS = {"<repo>", "<key path>"}


def outside_code(body):
    body = FENCE.sub("", body)
    return CODE_SPAN.sub(lambda m: m.group(0) if m.group(1) in TEMPLATE_SPANS else "", body)


class BadInput(Exception):
    pass


def sections(body):
    found, current = {}, None
    for line in body.splitlines():
        heading = re.match(r"^## (.+?)\s*$", line)
        if heading:
            current = heading.group(1)
            found[current] = []
        elif current:
            found[current].append(line)
    return {name: "\n".join(lines) for name, lines in found.items()}


def subsection(text, name):
    match = re.search(rf"^### {re.escape(name)}\s*$(.*?)(?=^### |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


def criteria_lines(body):
    text = sections(body).get("Acceptance criteria", "")
    return [line.rstrip() for line in text.splitlines() if line.startswith("-")]


def parsed_criteria(body):
    result = []
    for line in criteria_lines(body):
        match = CRITERION.match(line)
        if match:
            result.append((int(match.group(1)), match.group(2), line))
    return result


def is_screen_work(body):
    return any(tag in SCREEN_TAGS for _, tag, _ in parsed_criteria(body))


class Linter:
    def __init__(self, feature_flags):
        self.feature_flags = feature_flags
        self.gaps = []

    def gap(self, item, rule, message):
        self.gaps.append({"issue": item, "rule": rule, "message": f"{item} — {rule}: {message}"})

    def required(self, item, body, names):
        present = sections(body)
        missing = [name for name in names if name not in present]
        if missing:
            self.gap(item, "required-sections", f"missing {', '.join(f'## {name}' for name in missing)}")

    def criteria(self, item, body):
        lines = criteria_lines(body)
        if not lines:
            self.gap(item, "criteria-format", "no acceptance criteria")
            return
        for position, line in enumerate(lines, 1):
            match = CRITERION.match(line)
            if not match:
                self.gap(item, "criteria-format", f"'{line}' does not read `- [ ] #<n> [<tag>] <criterion>`")
            elif match.group(2) not in TAGS:
                self.gap(item, "criteria-format", f"unknown tag [{match.group(2)}] in '{line}'")
            elif int(match.group(1)) != position:
                self.gap(item, "criteria-format", f"criterion #{match.group(1)} sits at position {position}")
        for _, tag, line in parsed_criteria(body):
            if tag == "manual" and "because" not in line.lower():
                self.gap(item, "manual-reason", f"'{line}' names no reason it cannot be automated")

    def placeholders(self, item, body):
        found = PLACEHOLDER.findall(outside_code(body))
        if found:
            self.gap(item, "placeholder", f"unfilled: {', '.join(sorted(set(found)))}")

    def one_repo(self, item, body):
        repos = re.findall(r"^- Repo:", sections(body).get("Repos and key paths", ""), re.MULTILINE)
        if len(repos) != 1:
            self.gap(item, "one-repo", f"names {len(repos)} repos; a part works in exactly one")

    def part(self, item, body):
        self.criteria(item, body)
        self.placeholders(item, body)
        self.one_repo(item, body)
        if is_screen_work(body):
            self.design_refs(item, body)

    def design_refs(self, item, body):
        design = sections(body).get("Design")
        if design is None:
            self.gap(item, "design-refs", "screen work needs ## Design: a design link and screenshots, or a No visual change / No design yet line")
        elif not DESIGN_EXEMPT.search(design) and not (re.search(r"^- Link:", design, re.MULTILINE) and "![" in design):
            self.gap(item, "design-refs", "## Design needs a `- Link:` line and screenshots (`![…](…)`) of each changed screen")

    def issue(self, story):
        item, body, children = story["identifier"], story["description"], story["children"]
        if DELIVERABLE in sections(body):
            self.required(item, body, DESIGN_TICKET_SECTIONS)
            self.criteria(item, body)
            self.placeholders(item, body)
            return
        self.required(item, body, ISSUE_SECTIONS + ([] if children else ["Repos and key paths"]))
        if children and is_screen_work(body) and not any("Design" in sections(child["description"]) for child in children):
            self.design_refs(item, body)
        if children:
            self.criteria(item, body)
            self.placeholders(item, body)
            for _, tag, line in parsed_criteria(body):
                if tag in PART_TAGS:
                    self.gap(item, "issue-level-tag", f"[{tag}] proves a part; '{line}' belongs on a sub-issue")
        else:
            self.part(item, body)
        if len(children) == 1:
            self.gap(item, "single-sub-issue", "an issue with one sub-issue is built directly")
        if len(children) >= 2 and subsection(sections(body).get("Technical design", ""), "Contracts") is None:
            self.gap(item, "contracts", "two or more sub-issues need ### Contracts in the Technical design")
        for child in children:
            self.required(child["identifier"], child["description"], PART_SECTIONS)
            self.part(child["identifier"], child["description"])
        self.sub_order(story)

    def sub_order(self, story):
        ids = {child["identifier"] for child in story["children"]}
        edges = {}
        for child in story["children"]:
            for blocker in child.get("blockedBy", []):
                if blocker not in ids:
                    self.gap(child["identifier"], "blocks-dag", f"blocked by {blocker}, not a sub-issue of {story['identifier']}; relate the parent issues")
                else:
                    edges.setdefault(child["identifier"], []).append(blocker)
        self.cycles(edges)

    def cycles(self, edges):
        state = {}

        def visit(node, path):
            state[node] = "open"
            for nxt in edges.get(node, []):
                if state.get(nxt) == "open":
                    loop = path[path.index(nxt):] + [nxt]
                    self.gap(node, "blocks-dag", f"cycle: {' → '.join(loop)}")
                elif nxt not in state:
                    visit(nxt, path + [nxt])
            state[node] = "done"

        for node in list(edges):
            if node not in state:
                visit(node, [node])

    def design_frontend(self, issues):
        by_id = {story["identifier"]: story for story in issues}
        for story in issues:
            deliverable = sections(story["description"]).get(DELIVERABLE)
            if deliverable is None:
                continue
            item = story["identifier"]
            match = FRONTEND_LINE.search(deliverable)
            if not match:
                self.gap(item, "design-frontend", "a design ticket names its frontend ticket: `- Frontend ticket: <id>`")
                continue
            frontend = by_id.get(match.group(1))
            if frontend and item not in frontend["blockedBy"]:
                self.gap(item, "design-frontend", f"{match.group(1)} must be blocked by {item}")

    def flags(self, issues):
        removed = " ".join(
            sections(story["description"]).get(REMOVAL_SECTION, "") + " " + story.get("title", "")
            for story in issues
            if REMOVAL_SECTION in sections(story["description"])
        )
        for story in issues:
            body = story["description"]
            item = story["identifier"]
            declared = subsection(sections(body).get("Technical design", ""), "Feature flags") or ""
            keys = re.findall(r"`([^`]+)`", declared)
            bodies = [body] + [child["description"] for child in story["children"]]
            feature = any("Before → after" in sections(text) for text in bodies)
            if not keys:
                if feature and self.feature_flags:
                    self.gap(item, "flag-parity", "a new Feature goes behind a flag: name it under ### Feature flags")
                continue
            lines = [line for _, _, line in parsed_criteria(body)]
            for child in story["children"]:
                lines += [line for _, _, line in parsed_criteria(child["description"])]
            for key in keys:
                if not any(key in line and re.search(r"\boff\b", line.replace(f"`{key}`", "")) for line in lines):
                    self.gap(item, "flag-parity", f"no criterion proves nothing changes with `{key}` off")
                if key not in removed:
                    self.gap(item, "flag-removal", f"no issue with ## Removes takes `{key}` out")


def validate(story):
    if not isinstance(story, dict) or not story.get("identifier"):
        raise BadInput("each issue needs an identifier")
    if not isinstance(story.get("description"), str) or not story["description"].strip():
        raise BadInput(f"{story['identifier']} has no description")
    story.setdefault("children", [])
    story.setdefault("blockedBy", [])
    if not isinstance(story["children"], list) or not isinstance(story["blockedBy"], list):
        raise BadInput(f"{story['identifier']}: children and blockedBy must be lists")
    for child in story["children"]:
        if not isinstance(child, dict) or not child.get("identifier") or not isinstance(child.get("description"), str):
            raise BadInput(f"a sub-issue of {story['identifier']} lacks identifier or description")
        if not isinstance(child.setdefault("blockedBy", []), list):
            raise BadInput(f"{child['identifier']}: blockedBy must be a list")


def lint(plan, feature_flags=False):
    issues = plan["issues"] if isinstance(plan, dict) and "issues" in plan else [plan]
    if not isinstance(issues, list):
        raise BadInput("issues must be a list")
    for story in issues:
        validate(story)
    linter = Linter(feature_flags)
    for story in issues:
        linter.issue(story)
    linter.cycles({story["identifier"]: list(story["blockedBy"]) for story in issues})
    linter.flags(issues)
    linter.design_frontend(issues)
    return {"ready": not linter.gaps, "gaps": linter.gaps}


def main():
    parser = argparse.ArgumentParser(description="Lint a plan-work plan against the bundled standard.")
    parser.add_argument("--feature-flags", action="store_true")
    parser.add_argument("plan")
    args = parser.parse_args()
    try:
        with open(args.plan) as handle:
            result = lint(json.load(handle), feature_flags=args.feature_flags)
    except (OSError, ValueError, BadInput) as error:
        print(json.dumps({"error": str(error)}))
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()
