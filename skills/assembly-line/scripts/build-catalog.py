#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

USAGE = "usage: build-catalog.py [--check] [--skills <dir>]"
FORMAT = "assembly-line-catalog/1"
GENERATED_BY = "skills/assembly-line/scripts/build-catalog.py"
KEPT = ("judge", "merge")
STAGE_KEYS = ("raisedBy", "add", "remove")
WHERE = re.compile(r"^(after|before) (\S+)$")


def parse_args(argv):
    check = False
    skills = Path(__file__).resolve().parents[2]
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--check":
            check = True
        elif arg == "--skills" and args:
            skills = Path(args.pop(0))
        else:
            return None
    return check, skills


def stage_dirs(skills):
    return sorted(
        (d for d in skills.iterdir()
         if d.is_dir() and (d / "SKILL.md").is_file() and (d / "stage.json").is_file()),
        key=lambda d: d.name,
    )


def load_stages(directories, failures):
    stages = {}
    for directory in directories:
        name = directory.name
        try:
            body = json.loads((directory / "stage.json").read_text())
        except ValueError as error:
            failures.append(f"FAIL stage-parses {name}: stage.json does not parse: {error}")
            continue
        if not isinstance(body, dict):
            failures.append(f"FAIL stage-parses {name}: stage.json must hold an object")
            continue
        stages[name] = body
    return stages


def load_signals(path, failures):
    subject = "signals.json"
    if not path.is_file():
        failures.append(f"FAIL signals-parses {subject}: missing")
        return []
    try:
        body = json.loads(path.read_text())
    except ValueError as error:
        failures.append(f"FAIL signals-parses {subject}: does not parse: {error}")
        return []
    if not isinstance(body, dict) or not isinstance(body.get("signals"), list):
        failures.append(f"FAIL signals-parses {subject}: must hold an object with a signals list")
        return []
    rows = body["signals"]
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            failures.append(f"FAIL signals-parses {subject}: row {number} must be an object")
            continue
        for key in (*STAGE_KEYS, "where"):
            if key in row and not isinstance(row[key], str):
                failures.append(f"FAIL signals-parses {subject}: row {number} {key} must be a string")
    return rows


def check_shape(number, row, failures):
    signal = row.get("signal")
    if not isinstance(signal, str) or not signal:
        failures.append(f"FAIL signals-row signals.json: row {number} needs a signal")
    has_add = "add" in row
    has_remove = "remove" in row
    if has_add == has_remove:
        failures.append(f"FAIL signals-row signals.json: row {number} needs exactly one of add or remove")
    elif has_add and "where" not in row:
        failures.append(f"FAIL signals-row signals.json: row {number} add needs where")
    elif has_remove and "where" in row:
        failures.append(f"FAIL signals-row signals.json: row {number} remove takes no where")


def check_declared(number, row, stages, failures):
    raised_by = row.get("raisedBy")
    signal = row.get("signal")
    if not isinstance(raised_by, str) or raised_by not in stages or not isinstance(signal, str):
        return
    declared = stages[raised_by].get("signals")
    if not isinstance(declared, list) or signal not in declared:
        failures.append(
            f"FAIL signals-declared {raised_by}: row {number} signal {signal} is not in {raised_by}'s stage.json signals"
        )


def check_kept(number, row, stages, failures):
    removed = row.get("remove")
    if not isinstance(removed, str):
        return
    human = removed in stages and stages[removed].get("gate") == "human"
    if removed in KEPT or human:
        failures.append(
            f"FAIL signals-kept-stage {removed}: row {number} removes {removed}; judge, merge and human gates stay"
        )


def check_rows(rows, stages, failures):
    names = set(stages)
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            continue
        check_shape(number, row, failures)
        check_declared(number, row, stages, failures)
        check_kept(number, row, stages, failures)
        for key in STAGE_KEYS:
            value = row.get(key)
            if isinstance(value, str) and value not in names:
                failures.append(
                    f"FAIL signals-known-stage {value}: row {number} {key} names {value}, not a stage in the catalog"
                )
        where = row.get("where")
        if not isinstance(where, str):
            continue
        match = WHERE.match(where)
        if not match:
            failures.append(
                f"FAIL signals-where signals.json: row {number} where '{where}' must be \"after <stage>\" or \"before <stage>\""
            )
        elif match.group(2) not in names:
            stage = match.group(2)
            failures.append(
                f"FAIL signals-known-stage {stage}: row {number} where names {stage}, not a stage in the catalog"
            )


def build(skills):
    failures = []
    directories = stage_dirs(skills)
    stages = load_stages(directories, failures)
    rows = load_signals(skills / "assembly-line" / "references" / "signals.json", failures)
    check_rows(rows, stages, failures)
    catalog = {"format": FORMAT, "generatedBy": GENERATED_BY, "stages": stages, "signals": rows}
    return catalog, failures


def render(catalog):
    return json.dumps(catalog, indent=2) + "\n"


def report_drift(path, built):
    try:
        served = json.loads(path.read_text())
    except ValueError:
        served = None
    if not isinstance(served, dict):
        print("FAIL catalog-current catalog.json: does not parse; run build-catalog.py")
    else:
        old = served.get("stages") if isinstance(served.get("stages"), dict) else {}
        new = built["stages"]
        fired = False
        for name in sorted(set(old) | set(new)):
            if name not in old:
                print(f"FAIL catalog-current {name}: in tree but missing from catalog")
            elif name not in new:
                print(f"FAIL catalog-current {name}: in catalog but not in tree")
            elif old[name] != new[name]:
                print(f"FAIL catalog-current {name}: changed since catalog was written")
            else:
                continue
            fired = True
        if served.get("signals") != built["signals"]:
            print("FAIL catalog-current signals: changed since catalog was written")
            fired = True
        if not fired:
            print("FAIL catalog-current catalog.json: differs from the build")
    print("\nrun skills/assembly-line/scripts/build-catalog.py to rewrite it")


def main(argv):
    parsed = parse_args(argv)
    if parsed is None:
        print(USAGE)
        return 2
    check, skills = parsed
    catalog, failures = build(skills)
    if failures:
        print("\n".join(failures))
        print("\ncatalog.json not written")
        return 1
    path = skills / "assembly-line" / "references" / "catalog.json"
    text = render(catalog)
    count = len(catalog["stages"])
    if not check:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f"wrote {path.relative_to(skills.parent)}: {count} stages")
        return 0
    if not path.is_file():
        print("FAIL catalog-exists catalog.json: missing; run build-catalog.py")
        return 1
    if path.read_text() == text:
        print(f"PASS catalog-current {count} stages match catalog.json")
        return 0
    report_drift(path, catalog)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
