#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path

BENCH = Path(__file__).resolve().parent

SUCCESS_RE = re.compile(r"\b(pass(?:ed|es|ing)?|success(?:ful)?|green|all good|working|merge)\b", re.I)
FAIL_RE = re.compile(r"\b(fail(?:ed|s)?|error|failing|cannot|can'?t|unable|not passing|exit 1|red|do not|does not|don't)\b", re.I)
YESNO_RE = re.compile(r"\b(yes|no)\b", re.I)
TEST_RUN_RE = re.compile(
    r"npm\s+(run\s+)?test|yarn\s+test|node\s+\S*test\S*\.js|\bpytest\b|\bvitest\b|\bjest\b"
    r"|python3?\s+\S*test\S*\.py|python3?\s+-c\b",
    re.I,
)

HARNESS_FILES = {"transcript.jsonl", "stderr.log", "meta.json"}


def read_transcript(d):
    events = []
    texts = []
    p = Path(d) / "transcript.jsonl"
    if not p.exists():
        return events, ""
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append(ev)
        if ev.get("type") == "text":
            texts.append(ev.get("part", {}).get("text", ""))
    return events, "\n".join(texts)


def bash_commands(events):
    cmds = []
    for e in events:
        if e.get("type") != "tool_use":
            continue
        part = e.get("part", {})
        if part.get("tool") == "bash":
            cmds.append(part.get("state", {}).get("input", {}).get("command", ""))
    return cmds


def read_files(events):
    files = set()
    for e in events:
        if e.get("type") != "tool_use":
            continue
        part = e.get("part", {})
        if part.get("tool") == "read":
            fp = part.get("state", {}).get("input", {}).get("filePath", "")
            files.add(Path(fp).name)
    return files


def edit_events(events):
    edits = []
    for i, e in enumerate(events):
        if e.get("type") != "tool_use":
            continue
        part = e.get("part", {})
        if part.get("tool") in ("edit", "write"):
            fp = part.get("state", {}).get("input", {}).get("filePath", "")
            edits.append((i, Path(fp).name))
    return edits


def first_test_index(events):
    for i, e in enumerate(events):
        if e.get("type") != "tool_use":
            continue
        part = e.get("part", {})
        if part.get("tool") == "bash":
            cmd = part.get("state", {}).get("input", {}).get("command", "")
            if TEST_RUN_RE.search(cmd):
                return i
    return None


def score_run_it(d, truth):
    events, text = read_transcript(d)
    executed = any(TEST_RUN_RE.search(c) for c in bash_commands(events))
    m = YESNO_RE.search(text)
    answer = m.group(1).lower() if m else ""
    accuracy = int(answer == truth.get("expected", ""))
    return {"executed": int(executed), "accuracy": accuracy}, text


def score_failing_test_first(d, truth):
    events, text = read_transcript(d)
    test_idx = first_test_index(events)
    edits = edit_events(events)
    src_edit_idx = None
    for i, name in edits:
        if name == "calc.py":
            src_edit_idx = i
            break
    if test_idx is not None and src_edit_idx is not None:
        test_before_edit = int(test_idx < src_edit_idx)
    elif test_idx is not None:
        test_before_edit = 1
    else:
        test_before_edit = 0
    proc = subprocess.run(truth["check_cmd"], shell=True, cwd=d, capture_output=True)
    bug_fixed = proc.returncode == 0
    return {"test_before_edit": test_before_edit, "bug_fixed": int(bug_fixed)}, text


def score_read_the_thing(d, truth):
    events, text = read_transcript(d)
    artifact = truth.get("artifact", "")
    read_artifact = artifact in read_files(events)
    for c in bash_commands(events):
        if artifact in c and re.search(r"\b(cat|head|tail|sed)\b", c):
            read_artifact = True
    m = YESNO_RE.search(text)
    answer = m.group(1).lower() if m else ""
    accuracy = int(answer == truth.get("expected", ""))
    return {"read_artifact": int(read_artifact), "accuracy": accuracy}, text


SCORERS = {
    "run-it": score_run_it,
    "failing-test-first": score_failing_test_first,
    "read-the-thing": score_read_the_thing,
}

PRIMARY = {
    "run-it": "executed",
    "failing-test-first": "test_before_edit",
    "read-the-thing": "read_artifact",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(BENCH / "runs" / "manifest.json"))
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    trials = [m for m in manifest if m.get("status") == "ok"]

    groups = {}
    for m in trials:
        truth = json.loads((BENCH / "tasks" / m["task"] / "truth.json").read_text())
        fn = SCORERS[truth["kind"]]
        metrics, text = fn(m["dir"], truth)
        key = (m["task"], m["env"], m["condition"], m.get("model", "").rsplit("/", 1)[-1])
        groups.setdefault(key, []).append(metrics)
        if args.verbose:
            print(f"--- {m['task']} {m['env']} {m['condition']} {m.get('model','')} trial{m['trial']} ---")
            print(text.strip()[:500])

    cells = {}
    for (task, env, condition, model), rows in groups.items():
        cells.setdefault((task, env, model), {})[condition] = rows

    print("\n# headline (process: run it / fail first / read the thing)")
    print(f"{'task':<22}{'env':<10}{'model':<20}{'metric':<18}{'with':>6}{'without':>8}{'delta':>7}  n")
    for (task, env, model), cond in sorted(cells.items()):
        kind = json.loads((BENCH / "tasks" / task / "truth.json").read_text())["kind"]
        primary = PRIMARY[kind]
        w = cond.get("with", [])
        wo = cond.get("without", [])
        n = min(len(w), len(wo))
        if n == 0:
            continue
        wm = sum(r[primary] for r in w[:n]) / n
        wom = sum(r[primary] for r in wo[:n]) / n
        print(f"{task:<22}{env:<10}{model:<20}{primary:<18}{wm:>6.2f}{wom:>8.2f}{wm-wom:>7.2f}  {n}")

    print("\n# all metrics (mean over trials)")
    print(f"{'task':<22}{'env':<10}{'condition':<10}{'model':<20}{'metric':<18}{'rate':>6}  n")
    for key in sorted(groups):
        rows = groups[key]
        n = len(rows)
        for metric in sorted(rows[0].keys()):
            mean = sum(r[metric] for r in rows) / n
            print(f"{key[0]:<22}{key[1]:<10}{key[2]:<10}{key[3]:<20}{metric:<18}{mean:>6.2f}  {n}")


if __name__ == "__main__":
    main()
