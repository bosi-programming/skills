#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

USAGE = "usage: board.py [--cards <dir>] [--log <path>]"
DEFAULT_CARDS = "./recipes"
DEFAULT_LOG = "~/.bosi-skills/runs.jsonl"
RUNNING = ("running", "needs-input", "blocked", "gate")
KEY_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*)$")
TICKET = re.compile(r"[A-Z][A-Z0-9]*-\d+")


def parse_args(argv):
    values = {"cards": DEFAULT_CARDS, "log": DEFAULT_LOG}
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag not in ("--cards", "--log") or not args:
            return None
        values[flag[2:]] = args.pop(0)
    return values


def fail(message):
    print(json.dumps({"error": message}, indent=2, ensure_ascii=False))
    return 1


def clean_value(raw):
    value = raw.strip()
    if value[:1] in ("'", '"'):
        quote = value[0]
        end = value.find(quote, 1)
        return (value[1:] if end == -1 else value[1:end]).strip()
    return value.split(" #", 1)[0].strip()


def frontmatter(text):
    if not text.startswith("---\n"):
        return None
    keys = {}
    for line in text.split("\n")[1:]:
        if line == "---":
            break
        match = KEY_LINE.match(line)
        if match:
            keys[match.group(1)] = clean_value(match.group(2))
    return keys


def read_cards(cards_dir):
    running = []
    for path in sorted(cards_dir.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        keys = frontmatter(text)
        if keys is None or keys.get("runStatus", "") not in RUNNING:
            continue
        found = TICKET.match(keys.get("task", ""))
        ticket = found.group(0) if found else path.stem
        stage = keys.get("runNext", "")
        if stage.endswith(".md"):
            stage = stage[:-3]
        running.append((ticket, path.name, stage or "unknown", keys["runStatus"]))
    return running


def duration(record):
    started = record.get("startedAt")
    ended = record.get("endedAt")
    if not isinstance(started, str) or not isinstance(ended, str):
        return None
    try:
        seconds = (
            datetime.fromisoformat(ended.replace("Z", "+00:00"))
            - datetime.fromisoformat(started.replace("Z", "+00:00"))
        ).total_seconds()
    except (ValueError, TypeError):
        return None
    return seconds if seconds >= 0 else None


def read_log(log_path):
    durations = {}
    skipped = 0
    if not log_path.exists():
        return durations, skipped
    text = log_path.read_text(encoding="utf-8")
    for line in text.split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            skipped += 1
            continue
        if not isinstance(record, dict) or not isinstance(record.get("stage"), str):
            skipped += 1
            continue
        seconds = duration(record)
        if seconds is not None:
            durations.setdefault(record["stage"], []).append(seconds)
    return durations, skipped


def table(header, rows):
    widths = [max(len(cell) for cell in column) for column in zip(header, *rows)]
    lines = []
    for row in [header] + rows:
        cells = [cell.ljust(width) for cell, width in zip(row, widths)]
        lines.append("  ".join(cells).rstrip())
    return lines


def main(argv):
    values = parse_args(argv)
    if values is None:
        print(USAGE)
        return 2
    cards_dir = Path(os.path.expanduser(values["cards"]))
    log_path = Path(os.path.expanduser(values["log"]))
    if not cards_dir.is_dir():
        return fail(f"cards folder not found: {values['cards']}")
    try:
        durations, skipped = read_log(log_path)
    except (OSError, UnicodeDecodeError) as error:
        return fail(f"cannot read {values['log']}: {error}")

    running = read_cards(cards_dir)
    if not running:
        print(f"No running lines in {cards_dir.resolve()}.")
        return 0

    waiting = {}
    for _, _, stage, _ in running:
        waiting[stage] = waiting.get(stage, 0) + 1
    means = {
        stage: sum(durations[stage]) / len(durations[stage])
        for stage in waiting
        if durations.get(stage)
    }
    order = sorted(
        waiting,
        key=lambda s: (
            -waiting[s],
            0 if s in means else 1,
            -(means.get(s) or 0),
            s,
        ),
    )

    def mean_cell(stage):
        return str(round(means[stage] / 60)) if stage in means else "-"

    tickets = sorted(running, key=lambda r: (r[0], r[1]))
    out = table(["TICKET", "STAGE", "STATUS"], [[t, s, st] for t, _, s, st in tickets])
    out.append("")
    out += table(
        ["STAGE", "WAITING", "MEAN MIN"],
        [[s, str(waiting[s]), mean_cell(s)] for s in order],
    )
    out.append("")
    top = order[0]
    if top in means:
        out.append(f"Bottleneck: {top} ({waiting[top]} waiting, mean {mean_cell(top)} min)")
    else:
        out.append(f"Bottleneck: {top} ({waiting[top]} waiting)")
    if skipped > 0:
        out.append(f"Skipped {skipped} bad log lines.")
    for line in out:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
