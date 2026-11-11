#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

USAGE = "usage: run-log.py append [--log <path>] --ticket <id> [--kind <kind>] [--line <name>] --stage <stage> --started-at <iso> --ended-at <iso> --verdict <verdict> --loops <n> [--tokens <n>] [--changed-by <signal>]"
DEFAULT_LOG = "~/.bosi-skills/runs.jsonl"
FLAGS = {
    "--log": "log",
    "--ticket": "ticket",
    "--kind": "kind",
    "--line": "line",
    "--stage": "stage",
    "--started-at": "startedAt",
    "--ended-at": "endedAt",
    "--verdict": "verdict",
    "--loops": "loops",
    "--tokens": "tokens",
    "--changed-by": "changedBy",
}
REQUIRED = ("ticket", "stage", "startedAt", "endedAt", "verdict", "loops")
INTEGERS = ("loops", "tokens")
TIMES = ("startedAt", "endedAt")
ORDER = ("ticket", "kind", "line", "stage", "startedAt", "endedAt", "verdict", "loops", "tokens", "changedBy")


def parse_args(argv):
    if not argv or argv[0] != "append":
        return None
    values = {}
    args = list(argv[1:])
    while args:
        flag = args.pop(0)
        if flag not in FLAGS or not args:
            return None
        values[FLAGS[flag]] = args.pop(0)
    for key in REQUIRED:
        if key not in values:
            return None
    for key in INTEGERS:
        if key in values:
            text = values[key]
            if not text.isascii() or not text.isdecimal():
                return None
            values[key] = int(text)
    for key in TIMES:
        try:
            datetime.fromisoformat(values[key].replace("Z", "+00:00"))
        except ValueError:
            return None
    return values


def build_record(values):
    return {key: values.get(key) for key in ORDER}


def append(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = ""
    if path.exists() and path.stat().st_size > 0:
        with path.open("rb") as handle:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                prefix = "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(prefix + json.dumps(record, ensure_ascii=False) + "\n")


def main(argv):
    values = parse_args(argv)
    if values is None:
        print(USAGE)
        return 2
    record = build_record(values)
    path = Path(os.path.expanduser(values.get("log", DEFAULT_LOG)))
    try:
        append(path, record)
        resolved = path.resolve()
    except OSError as problem:
        print(json.dumps({"error": f"run log not written: {problem}"}, indent=2))
        return 1
    print(json.dumps({"log": str(resolved), "record": record}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
