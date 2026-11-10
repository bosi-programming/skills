#!/usr/bin/env python3
import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

USAGE = "usage: apply-signals.py <card> <line file> --done <n> [--catalog <path>]"
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "references" / "catalog.json"
VALIDATOR = Path(__file__).resolve().parent / "validate-line.py"
KEPT = ("judge", "merge")
WHERE = re.compile(r"^(after|before) (\S+)$")
SEPARATOR = " — "


class Fatal(Exception):
    pass


def parse_args(argv):
    catalog = DEFAULT_CATALOG
    done = None
    positional = []
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--done":
            if not args:
                return None
            try:
                done = int(args.pop(0))
            except ValueError:
                return None
            if done < 0:
                return None
        elif arg == "--catalog":
            if not args:
                return None
            catalog = Path(args.pop(0))
        elif arg.startswith("--"):
            return None
        else:
            positional.append(arg)
    if len(positional) != 2 or done is None:
        return None
    return Path(positional[0]), Path(positional[1]), done, catalog


def read_json(path, what):
    try:
        return json.loads(path.read_text())
    except OSError as problem:
        raise Fatal(f"{what} unreadable: {problem}")
    except ValueError as problem:
        raise Fatal(f"{what} does not parse: {problem}")


def signals_section(card_text):
    lines = card_text.splitlines()
    section = []
    inside = False
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            inside = line.strip() == "## Signals"
            continue
        if inside:
            section.append(line)
    return "\n".join(section)


def read_signals(card_text):
    text = re.sub(r"<!--.*?-->", "", signals_section(card_text), flags=re.S)
    found = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        body = line[2:] if line.startswith("- ") else line
        parts = body.split(SEPARATOR, 2)
        if len(parts) == 3 and all(part.strip() for part in parts):
            signal, raised_by, evidence = (part.strip() for part in parts)
            found.append({"text": line, "signal": signal, "raisedBy": raised_by, "evidence": evidence})
        else:
            found.append({"text": line, "signal": None, "raisedBy": None, "evidence": None})
    return found


def item_name(item):
    if isinstance(item, str):
        return item
    if isinstance(item, dict) and isinstance(item.get("stage"), str):
        return item["stage"]
    return None


def names_in(stages):
    names = set()
    for item in stages:
        if isinstance(item, dict) and isinstance(item.get("parallel"), list):
            names.update(item_name(branch) for branch in item["parallel"])
        else:
            names.add(item_name(item))
    names.discard(None)
    return names


def remove_stage(rest, name):
    result = []
    for item in rest:
        if isinstance(item, dict) and isinstance(item.get("parallel"), list):
            branches = [b for b in item["parallel"] if item_name(b) != name]
            if branches:
                result.append({**item, "parallel": branches})
        elif item_name(item) != name:
            result.append(item)
    return result


def add_stage(rest, name, where):
    match = WHERE.match(where or "")
    if not match:
        return None
    side, anchor = match.groups()
    for index, item in enumerate(rest):
        if item_name(item) == anchor:
            position = index + 1 if side == "after" else index
            return rest[:position] + [name] + rest[position:]
    return None


def human_gate(catalog, name):
    body = catalog["stages"].get(name)
    return isinstance(body, dict) and body.get("gate") == "human"


def validate(line, stages, catalog_path):
    candidate = {**line, "stages": stages}
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "line.json"
        path.write_text(json.dumps(candidate))
        run = subprocess.run(
            [sys.executable, str(VALIDATOR), str(path), "--catalog", str(catalog_path)],
            capture_output=True,
            text=True,
        )
    try:
        result = json.loads(run.stdout)
    except ValueError:
        return [{"stage": None, "rule": "validator", "message": "validator output did not parse"}]
    if result.get("valid") is True:
        return []
    return result.get("errors") or [{"stage": None, "rule": "validator", "message": "line is not valid"}]


def entry(signal, row, change, name):
    return {
        "text": signal["text"],
        "signal": signal["signal"],
        "raisedBy": signal["raisedBy"],
        "evidence": signal["evidence"],
        "change": change,
        "stage": name,
        "where": row.get("where"),
    }


def apply_row(signal, row, state, done, catalog, catalog_path, report):
    stages = state["stages"]
    head, rest = stages[:done], stages[done:]
    skipped = {"text": signal["text"], "signal": signal["signal"], "raisedBy": signal["raisedBy"]}
    if "remove" in row:
        change, name = "remove", row["remove"]
        if name in KEPT or human_gate(catalog, name):
            report["rejected"].append(
                {**entry(signal, row, change, name),
                 "errors": [{"stage": name, "rule": "kept-stage", "message": f"{name} cannot be removed"}]}
            )
            return
        if name not in names_in(rest):
            report["skipped"].append({**skipped, "reason": "not-on-line"})
            return
        new_rest = remove_stage(rest, name)
    else:
        change, name = "add", row.get("add")
        if name in names_in(rest):
            report["skipped"].append({**skipped, "reason": "already-on-line"})
            return
        new_rest = add_stage(rest, name, row.get("where"))
        if new_rest is None:
            report["skipped"].append({**skipped, "reason": "anchor-missing"})
            return
    candidate = head + new_rest
    errors = validate(state["line"], candidate, catalog_path)
    if errors:
        report["rejected"].append({**entry(signal, row, change, name), "errors": errors})
        return
    state["stages"] = candidate
    report["applied"].append(entry(signal, row, change, name))


def apply(line, done, signal_lines, catalog_path, catalog):
    report = {"applied": [], "rejected": [], "skipped": []}
    state = {"line": line, "stages": copy.deepcopy(line["stages"])}
    rows = catalog.get("signals") if isinstance(catalog.get("signals"), list) else []
    for signal in signal_lines:
        if signal["signal"] is None:
            report["skipped"].append(
                {"text": signal["text"], "signal": None, "raisedBy": None, "reason": "malformed"}
            )
            continue
        matches = [
            row for row in rows
            if isinstance(row, dict)
            and row.get("signal") == signal["signal"]
            and row.get("raisedBy") == signal["raisedBy"]
        ]
        if not matches:
            report["skipped"].append(
                {"text": signal["text"], "signal": signal["signal"],
                 "raisedBy": signal["raisedBy"], "reason": "no-row"}
            )
            continue
        for row in matches:
            apply_row(signal, row, state, done, catalog, catalog_path, report)
    final = {**line, "stages": state["stages"]}
    return {
        "changed": bool(report["applied"]),
        "line": final,
        "applied": report["applied"],
        "rejected": report["rejected"],
        "skipped": report["skipped"],
    }


def main(argv):
    parsed = parse_args(argv)
    if parsed is None:
        print(USAGE)
        return 2
    card, line_path, done, catalog_path = parsed
    try:
        try:
            card_text = card.read_text()
        except OSError as problem:
            raise Fatal(f"card unreadable: {problem}")
        line = read_json(line_path, "line file")
        if not isinstance(line, dict):
            raise Fatal("line file must hold an object")
        if "from" in line:
            raise Fatal("line file holds from; pass the expanded line")
        if not isinstance(line.get("stages"), list) or not line["stages"]:
            raise Fatal("line file needs a non-empty stages list")
        catalog = read_json(catalog_path, "catalog")
        if not isinstance(catalog, dict) or not isinstance(catalog.get("stages"), dict):
            raise Fatal("catalog must hold an object with a stages object")
    except Fatal as problem:
        print(json.dumps({"error": str(problem)}, indent=2))
        return 1
    report = apply(line, done, read_signals(card_text), catalog_path, catalog)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
