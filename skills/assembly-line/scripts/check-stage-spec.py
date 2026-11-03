#!/usr/bin/env python3
import json
import sys
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
KEYS = ("takes", "delivers", "return", "signals", "gate")
GATES = ("auto", "human")
PAST = ("needs-input", "human")
DELIVERS = ("sections", "fields", "verdicts")

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def strings(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def stages():
    return {d.name for d in SKILLS.iterdir() if (d / "SKILL.md").is_file()}


def check_delivers(delivers):
    bad = [key for key in DELIVERS if not strings(delivers.get(key))] if isinstance(delivers, dict) else list(DELIVERS)
    check("delivers", not bad, f"not a list of strings: {bad}")
    return delivers.get("verdicts", []) if not bad else []


def check_return(returns, verdicts):
    if not isinstance(returns, dict) or not returns:
        check("return", False, "must map at least one failing verdict to a role")
        return
    known = stages()
    for verdict, route in returns.items():
        check("return-verdict", verdict in verdicts, f"{verdict!r} is not in delivers.verdicts")
        if not isinstance(route, dict):
            check("return-route", False, f"{verdict!r} must map to an object with to, limit and past")
            continue
        to = route.get("to")
        check("return-to", to in known, f"{verdict!r} returns to {to!r}, which is not a stage in skills/")
        limit = route.get("limit")
        check("return-limit", isinstance(limit, int) and not isinstance(limit, bool) and limit >= 0,
              f"{verdict!r} limit {limit!r} must be an integer >= 0")
        check("return-past", route.get("past") in PAST, f"{verdict!r} past {route.get('past')!r} must be one of {PAST}")


def validate(path):
    check("exists", path.is_file(), f"{path} missing")
    if not path.is_file():
        return
    try:
        spec = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        check("parses", False, str(error))
        return
    check("parses", isinstance(spec, dict), "top level must be an object")
    if not isinstance(spec, dict):
        return
    for key in KEYS:
        check(f"key-{key}", key in spec, f"{key} missing")
    if "takes" in spec:
        check("takes", strings(spec["takes"]), "must be a list of strings")
    verdicts = check_delivers(spec["delivers"]) if "delivers" in spec else []
    if "return" in spec:
        check_return(spec["return"], verdicts)
    if "signals" in spec:
        check("signals", strings(spec["signals"]), "must be a list of strings")
    if "gate" in spec:
        check("gate", spec["gate"] in GATES, f"{spec['gate']!r} must be one of {GATES}")


def main():
    if len(sys.argv) != 2:
        print("usage: check-stage-spec.py <skill dir>")
        return 2
    validate(Path(sys.argv[1]) / "stage.json")
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
