#!/usr/bin/env python3
import json
import sys
from pathlib import Path

USAGE = "usage: validate-line.py <line file> [--catalog <path>]"
FORMAT = "assembly-line/1"
START = ("task", "parent", "## Sub-issues")
SHARED_SECTIONS = ("## Decisions", "## Open Questions", "## TDD Test Mapping")
SHARED_FIELDS = ("phase", "phasesCompleted", "lastTouched")
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "references" / "catalog.json"


def parse_args(argv):
    catalog = DEFAULT_CATALOG
    positional = []
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--catalog":
            if not args:
                return None
            catalog = Path(args.pop(0))
        elif arg.startswith("--"):
            return None
        else:
            positional.append(arg)
    if len(positional) != 1:
        return None
    return Path(positional[0]), catalog


def error(stage, rule, message):
    return {"stage": stage, "rule": rule, "message": message}


def is_stage_item(item):
    if isinstance(item, str):
        return True
    if not isinstance(item, dict) or not isinstance(item.get("stage"), str):
        return False
    return set(item) <= {"stage", "with"} and (
        "with" not in item or isinstance(item["with"], dict)
    )


def is_group(item):
    return item == {"group": "sub-issues"}


def is_parallel(item):
    if not isinstance(item, dict) or set(item) != {"parallel"}:
        return False
    branches = item["parallel"]
    return isinstance(branches, list) and bool(branches) and all(map(is_stage_item, branches))


def stage_name(item):
    return item if isinstance(item, str) else item["stage"]


def load_line(path):
    try:
        text = path.read_text()
    except OSError as problem:
        return None, [error(None, "line-parses", f"line file missing or unreadable: {problem}")]
    try:
        return json.loads(text), []
    except ValueError as problem:
        return None, [error(None, "line-parses", f"line file does not parse: {problem}")]


def check_shape(line):
    if not isinstance(line, dict):
        return [error(None, "line-shape", "line must be a JSON object")]
    errors = []
    if line.get("format") != FORMAT:
        errors.append(error(None, "line-shape", f"format must be {FORMAT}"))
    ticket = line.get("ticket")
    if not isinstance(ticket, str) or not ticket:
        errors.append(error(None, "line-shape", "ticket must be a non-empty string"))
    stages = line.get("stages")
    if not isinstance(stages, list) or not stages:
        errors.append(error(None, "line-shape", "stages must be a non-empty list"))
        return errors
    for number, item in enumerate(stages, 1):
        if not (is_stage_item(item) or is_group(item) or is_parallel(item)):
            errors.append(
                error(None, "line-shape", f"item {number} is not a stage, a parallel group or a sub-issue group")
            )
    return errors


def is_name_list(value):
    return value is None or (isinstance(value, list) and all(isinstance(v, str) for v in value))


def valid_entry(entry):
    if not isinstance(entry, dict) or not is_name_list(entry.get("takes")):
        return False
    body = entry.get("delivers")
    if body is not None and not (
        isinstance(body, dict) and is_name_list(body.get("sections")) and is_name_list(body.get("fields"))
    ):
        return False
    returns = entry.get("return")
    if returns is None:
        return True
    return isinstance(returns, dict) and all(isinstance(v, dict) for v in returns.values())


def load_catalog(path):
    try:
        body = json.loads(path.read_text())
    except OSError as problem:
        return None, [error(None, "catalog-parses", f"catalog missing or unreadable: {problem}")]
    except ValueError as problem:
        return None, [error(None, "catalog-parses", f"catalog does not parse: {problem}")]
    if not isinstance(body, dict) or not isinstance(body.get("stages"), dict):
        return None, [error(None, "catalog-parses", "catalog must be an object with a stages object")]
    for name, entry in body["stages"].items():
        if not valid_entry(entry):
            return None, [error(None, "catalog-parses", f"catalog stage {name} is malformed")]
    return body["stages"], []


def branches_of(item):
    if isinstance(item, dict) and "parallel" in item:
        return list(item["parallel"])
    if is_group(item):
        return []
    return [item]


def all_names(items):
    return [stage_name(branch) for item in items for branch in branches_of(item)]


def delivers(entry):
    body = entry.get("delivers") if isinstance(entry.get("delivers"), dict) else {}
    return set(body.get("sections") or []) | set(body.get("fields") or [])


def check_known(items, stages):
    return [
        error(name, "known-stage", f"{name} is not a stage in the catalog")
        for name in all_names(items)
        if name not in stages
    ]


def check_first_judge(items, stages):
    first = items[0]
    if is_group(first) or is_parallel(first):
        return [error(None, "first-judge", "the first item must be judge")]
    name = stage_name(first)
    if name not in stages or name == "judge":
        return []
    return [error(name, "first-judge", "the first item must be judge")]


def merge_index(items):
    for index, item in enumerate(items):
        if is_stage_item(item) and stage_name(item) == "merge":
            return index
    return None


def check_merge(items):
    if merge_index(items) is None:
        return [error("merge", "last-gate-merge", "merge must be on the line at the top level")]
    return []


def check_auto_after_merge(items, stages):
    index = merge_index(items)
    if index is None:
        return []
    errors = []
    for item in items[index + 1:]:
        if is_group(item):
            errors.append(error(None, "auto-after-merge", "a sub-issue group comes after merge"))
            continue
        for branch in branches_of(item):
            name = stage_name(branch)
            if name not in stages:
                continue
            gate = stages[name].get("gate")
            if gate != "auto":
                errors.append(
                    error(name, "auto-after-merge", f"{name} has gate {gate} and comes after merge; only gate auto may")
                )
    return errors


def check_takes(items, stages):
    met = set(START)
    opened = False
    errors = []
    for item in items:
        if is_group(item):
            opened = True
            continue
        known = [stage_name(b) for b in branches_of(item) if stage_name(b) in stages]
        for name in known:
            own = delivers(stages[name])
            for take in stages[name].get("takes") or []:
                if opened or take in met or take in own:
                    continue
                sources = sorted(n for n, entry in stages.items() if take in delivers(entry))
                if sources:
                    detail = f"delivered by: {', '.join(sources)}"
                else:
                    detail = "no stage in the catalog delivers it"
                errors.append(
                    error(name, "takes-met", f"{name} takes {take}, which no earlier stage delivers; {detail}")
                )
        for name in known:
            met |= delivers(stages[name])
    return errors


def check_returns(items, stages):
    if any(is_group(item) for item in items):
        return []
    on_line = set(all_names(items))
    errors = []
    for name in all_names(items):
        if name not in stages:
            continue
        returns = stages[name].get("return")
        if not isinstance(returns, dict):
            continue
        for verdict, target in returns.items():
            role = target.get("to") if isinstance(target, dict) else None
            if role not in on_line:
                errors.append(
                    error(name, "return-target", f"{name} returns {verdict} to {role}, which is not on the line")
                )
    return errors


def check_parallel(items, stages):
    errors = []
    shared = set(SHARED_SECTIONS) | set(SHARED_FIELDS)
    for item in items:
        if not (isinstance(item, dict) and "parallel" in item):
            continue
        names = [stage_name(b) for b in item["parallel"] if stage_name(b) in stages]
        for j, later in enumerate(names):
            for earlier in names[:j]:
                overlap = (delivers(stages[earlier]) & delivers(stages[later])) - shared
                if overlap:
                    errors.append(
                        error(
                            later,
                            "parallel-group",
                            f"{later} and {earlier} both deliver {', '.join(sorted(overlap))}",
                        )
                    )
    return errors


def validate(line_path, catalog_path):
    line, errors = load_line(line_path)
    if errors:
        return errors
    errors = check_shape(line)
    if errors:
        return errors
    stages, errors = load_catalog(catalog_path)
    if errors:
        return errors
    items = line["stages"]
    merge_errors = check_merge(items)
    return (
        check_known(items, stages)
        + check_first_judge(items, stages)
        + merge_errors
        + (check_auto_after_merge(items, stages) if not merge_errors else [])
        + check_takes(items, stages)
        + check_returns(items, stages)
        + check_parallel(items, stages)
    )


def main(argv):
    parsed = parse_args(argv)
    if parsed is None:
        print(USAGE)
        return 2
    line_path, catalog_path = parsed
    errors = validate(line_path, catalog_path)
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
