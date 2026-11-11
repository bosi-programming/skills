#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

USAGE = "usage: stats.py --kind <kind> [--log <path>] [--catalog <path>]"
DEFAULT_LOG = "~/.bosi-skills/runs.jsonl"
DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / "assembly-line" / "references" / "catalog.json"
FLAGS = {"--kind": "kind", "--log": "log", "--catalog": "catalog"}
MIN_RUNS = 5
ALWAYS_FAIL = ("blocked", "needs-input", "gate")
KEEP_STAGES = ("judge", "merge")


def parse_args(argv):
    values = {}
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag not in FLAGS or not args:
            return None
        values[FLAGS[flag]] = args.pop(0)
    if not values.get("kind"):
        return None
    return values


def fail(message):
    print(json.dumps({"error": message}, indent=2, ensure_ascii=False))
    sys.exit(1)


def load_catalog(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        fail(f"cannot read catalog {path}: {error}")
    if not isinstance(data, dict) or not isinstance(data.get("stages"), dict):
        fail(f"catalog {path} has no stages object")
    return data["stages"]


def read_log(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except (OSError, UnicodeDecodeError) as error:
        fail(f"cannot read log {path}: {error}")


def parse_line(text):
    try:
        record = json.loads(text)
    except ValueError:
        return None
    if not isinstance(record, dict):
        return None
    for key in ("ticket", "stage", "verdict"):
        if not isinstance(record.get(key), str):
            return None
    loops = record.get("loops")
    if not isinstance(loops, int) or isinstance(loops, bool):
        return None
    return record


def return_keys(stages, stage):
    entry = stages.get(stage)
    if not isinstance(entry, dict):
        return ()
    returns = entry.get("return")
    if not isinstance(returns, dict):
        return ()
    return tuple(returns)


def suggest(stage, runs, fails, added, tickets, kind):
    if runs < MIN_RUNS:
        return None, None
    if added * 2 > runs:
        return "add", f"a signal added `{stage}` in {added} of {runs} runs on {kind} tickets"
    if fails * 4 >= runs:
        return "look", f"`{stage}` failed {fails} of {runs} runs on {kind} tickets"
    if fails == 0 and stage not in KEEP_STAGES:
        return "cut", f"`{stage}` never failed in {runs} runs on {tickets} {kind} tickets"
    return None, None


def main(argv):
    values = parse_args(argv)
    if values is None:
        print(USAGE)
        return 2
    kind = values["kind"]
    log_path = Path(os.path.expanduser(values.get("log", DEFAULT_LOG))).resolve()
    catalog_path = os.path.expanduser(values.get("catalog", str(DEFAULT_CATALOG)))
    stages = load_catalog(catalog_path)
    content = read_log(log_path)
    skipped = 0
    groups = {}
    all_tickets = set()
    for text in content.split("\n"):
        if not text.strip():
            continue
        record = parse_line(text)
        if record is None:
            skipped += 1
            continue
        if record.get("kind") != kind:
            continue
        stage = record["stage"]
        group = groups.setdefault(stage, {"runs": 0, "tickets": set(), "fails": 0, "loops": 0, "added": 0})
        group["runs"] += 1
        group["tickets"].add(record["ticket"])
        all_tickets.add(record["ticket"])
        group["loops"] += record["loops"]
        if record["verdict"] in return_keys(stages, stage) or record["verdict"] in ALWAYS_FAIL:
            group["fails"] += 1
        if record.get("changedBy") is not None:
            group["added"] += 1
    result_stages = []
    for stage in sorted(groups):
        group = groups[stage]
        runs = group["runs"]
        tickets = len(group["tickets"])
        suggestion, because = suggest(stage, runs, group["fails"], group["added"], tickets, kind)
        result_stages.append({
            "stage": stage,
            "runs": runs,
            "tickets": tickets,
            "fails": group["fails"],
            "failRate": round(group["fails"] / runs, 2),
            "meanLoops": round(group["loops"] / runs, 2),
            "added": group["added"],
            "addedRate": round(group["added"] / runs, 2),
            "suggestion": suggestion,
            "because": because,
        })
    result = {
        "log": str(log_path),
        "kind": kind,
        "tickets": len(all_tickets),
        "skipped": skipped,
        "stages": result_stages,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
