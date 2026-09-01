#!/usr/bin/env python3
"""Trigger harness for the summarize-llm-response skill.

Behaviour tests (run.py) inject SKILL.md unconditionally, so they say
nothing about whether the description makes the skill fire. This installs
the skill into a throwaway project and checks, per prompt, whether Claude
actually invokes it.

Prompts come from trigger_cases.json: `should_fire: true` prompts measure
recall, `false` prompts measure over-triggering. Run with --description to
score a candidate description without editing SKILL.md.
"""
import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
SKILL_MD = EVAL_DIR.parent / "SKILL.md"
SKILL_NAME = "summarize-llm-response"
CASES = json.loads((EVAL_DIR / "trigger_cases.json").read_text())["cases"]
DEFAULT_MODEL = "claude-sonnet-5"


def build_skill(description=None):
    text = SKILL_MD.read_text()
    if description is None:
        return text
    body = text.split("---", 2)[2] if text.startswith("---") else text
    indented = "\n  ".join(description.strip().split("\n"))
    return f"---\nname: {SKILL_NAME}\ndescription: >-\n  {indented}\n---\n{body}"


def fired(stream_lines):
    for line in stream_lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in (event.get("message") or {}).get("content", []) or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                blob = json.dumps(block).lower()
                if SKILL_NAME in blob:
                    return True
    return False


MEMORY_DIRECTIVE = (
    "## Communication\n\n"
    f"- Use the {SKILL_NAME} skill before any communication.\n"
)


def run_case(case, skill_text, model, timeout, memory=False):
    root = Path(tempfile.mkdtemp(prefix="trig-"))
    try:
        skill_dir = root / ".claude" / "skills" / SKILL_NAME
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(skill_text)
        if memory:
            (root / "CLAUDE.md").write_text(MEMORY_DIRECTIVE)

        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        try:
            proc = subprocess.run(
                [
                    "claude", "-p", case["prompt"],
                    "--setting-sources", "project",
                    # Without this the user's MCP servers load and the model
                    # reaches for Linear/Slack directly instead of the skill —
                    # which both wrecks the measurement and risks a real write.
                    "--strict-mcp-config",
                    "--disallowed-tools", "Bash", "Edit", "Write", "NotebookEdit", "WebFetch", "WebSearch",
                    "--model", model,
                    "--output-format", "stream-json",
                    "--verbose",
                    "--no-session-persistence",
                ],
                capture_output=True, text=True, timeout=timeout, cwd=root, env=env,
            )
        except subprocess.TimeoutExpired:
            return case, None
        return case, fired(proc.stdout.splitlines())
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--description", help="candidate description to test instead of SKILL.md's")
    ap.add_argument("--description-file")
    ap.add_argument(
        "--memory", action="store_true",
        help="also drop a CLAUDE.md line telling Claude to run the skill",
    )
    args = ap.parse_args()

    desc = args.description
    if args.description_file:
        desc = Path(args.description_file).read_text()
    skill_text = build_skill(desc)

    work = [c for c in CASES for _ in range(args.trials)]
    tally = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_case, c, skill_text, args.model, args.timeout, args.memory) for c in work]
        for f in concurrent.futures.as_completed(futures):
            case, hit = f.result()
            tally.setdefault(case["id"], []).append(hit)

    tp = fp = fn = tn = 0
    print(f"{'id':<4}{'want':<7}{'fired':<8}prompt")
    for case in CASES:
        hits = tally.get(case["id"], [])
        n_fired = sum(1 for h in hits if h)
        want = case["should_fire"]
        if want:
            tp += n_fired
            fn += len(hits) - n_fired
        else:
            fp += n_fired
            tn += len(hits) - n_fired
        flag = "" if (n_fired == len(hits)) == want or (n_fired == 0) != want else "  <-- MISS"
        print(f"{case['id']:<4}{str(want):<7}{n_fired}/{len(hits):<6}{case['prompt'][:60]}{flag}")

    recall = tp / (tp + fn) if tp + fn else 0
    precision = tp / (tp + fp) if tp + fp else 0
    print(f"\nrecall (fires when it should):     {tp}/{tp + fn} = {recall:.0%}")
    print(f"precision (fires only when right): {tp}/{tp + fp} = {precision:.0%}" if tp + fp else "\nprecision: n/a")
    print(f"false positives: {fp}/{fp + tn}")


if __name__ == "__main__":
    main()
