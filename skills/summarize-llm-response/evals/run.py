#!/usr/bin/env python3
"""Behaviour harness for the summarize-llm-response skill.

Runs every case in evals.json twice — once with SKILL.md injected, once
without — through headless `claude -p --safe-mode`. Safe mode drops the
user's CLAUDE.md, installed skills, plugins and hooks, so the only
difference between the two arms is the skill itself.

Outputs land in runs/<model>/<case-id>/<condition>/trial<N>/output.md.
Score them with score.py.
"""
import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
SKILL_MD = EVAL_DIR.parent / "SKILL.md"
CASES = json.loads((EVAL_DIR / "evals.json").read_text())
CONDITIONS = ["with", "without"]
DEFAULT_MODEL = "claude-sonnet-5"

# Headless safe mode has no Linear/Slack/Todoist tools, so external-target
# cases need this note or the model stalls on the missing integration. It is
# applied to both arms, and never to in-conversation cases — telling the model
# to "write out what you would post" is what pushed case 1 into issue format.
NO_TOOLS_SUFFIX = (
    "\n\n(You have no external integrations available in this session. "
    "Write out the exact content you would submit, including every field.)"
)


def prompt_for(case):
    if case.get("target", "in-conversation") == "in-conversation":
        return case["prompt"]
    return case["prompt"] + NO_TOOLS_SUFFIX


def skill_body() -> str:
    text = SKILL_MD.read_text()
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


def run_one(case, condition, trial, model, root, timeout):
    dest = root / str(case["id"]) / condition / f"trial{trial}"
    out = dest / "output.md"
    if out.exists():
        return case["id"], condition, trial, "skip"
    dest.mkdir(parents=True, exist_ok=True)

    cmd = [
        "claude", "-p", prompt_for(case),
        "--safe-mode",
        "--model", model,
        "--output-format", "json",
        "--no-session-persistence",
    ]
    if condition == "with":
        cmd += ["--append-system-prompt", skill_body()]

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=dest, env=env,
        )
    except subprocess.TimeoutExpired:
        out.write_text("")
        (dest / "error.log").write_text("TIMEOUT\n")
        return case["id"], condition, trial, "timeout"

    try:
        payload = json.loads(proc.stdout)
        result = payload.get("result", "")
    except json.JSONDecodeError:
        (dest / "error.log").write_text(proc.stdout + "\n" + proc.stderr)
        return case["id"], condition, trial, "unparseable"

    out.write_text(result)
    (dest / "meta.json").write_text(json.dumps({
        "case": case["id"],
        "condition": condition,
        "trial": trial,
        "model": model,
        "cost_usd": payload.get("total_cost_usd"),
        "duration_ms": payload.get("duration_ms"),
        "is_error": payload.get("is_error"),
    }, indent=2))
    return case["id"], condition, trial, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", nargs="*", type=int, default=[c["id"] for c in CASES["evals"]])
    ap.add_argument("--condition", nargs="*", default=CONDITIONS)
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    root = EVAL_DIR / "runs" / args.model.replace("/", "__")
    work = [
        (c, cond, t)
        for c in CASES["evals"] if c["id"] in args.case
        for cond in args.condition
        for t in range(1, args.trials + 1)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(run_one, c, cond, t, args.model, root, args.timeout)
            for c, cond, t in work
        ]
        for f in concurrent.futures.as_completed(futures):
            cid, cond, trial, status = f.result()
            print(f"case {cid} {cond} trial{trial}: {status}", flush=True)

    print(f"\noutputs: {root}")


if __name__ == "__main__":
    sys.exit(main())
