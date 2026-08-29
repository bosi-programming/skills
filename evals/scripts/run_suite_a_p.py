#!/usr/bin/env python3
"""Runs Suite A directly through `claude -p`.

Why not `claude plugin eval`: that runner will not expand a slash command and gives
no way to see whether the skill's text actually reached the model. Driving `claude -p`
ourselves means the trace is ours — every tool call, and whether the skill loaded or
came back "Unknown skill".

The two arms differ only in a settings file that turns the plugin on or off. The
prompt is identical in both, so the baseline asks for the skill too, fails to find it,
and answers anyway. That is the comparison we want.
"""

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gen_cases  # noqa: E402

EVALS = pathlib.Path(__file__).resolve().parents[1]
SETTINGS = EVALS / "settings"
SCAFFOLD = EVALS / "scripts" / "scaffold.sh"
SCAFFOLD_HARD = EVALS / "scripts" / "scaffold_hard.sh"

# Text that only appears once a skill's body is actually in context.
# Phrases that appear only in the skill's own body. A generic phrase like
# "epistemic action" is one the model writes unprompted, so it cannot serve as
# evidence the skill loaded.
SKILL_MARKERS = {
    "objectum": ["Desvelamento", "Pôr-a-frente", "Contra-desvelamento",
                 "Afeto próprio", "Doação"],
    "epistemic-action": ["Tetris rule", "Tetris players", "probe loop",
                         "unveiling is worth"],
}

# Disabling the plugin hides the skill from the Skill tool. It does not take the file
# off disk, and a baseline run can still find and read it. That contaminates the arm,
# so it is detected here and excluded during analysis rather than ignored.
PLUGIN_PATH_HINTS = ["bosi-programming", "skills/objectum", "skills/epistemic-action"]

JUDGE = """You are grading one response against one criterion. Answer with a single \
word, PASS or FAIL, and nothing else.

CRITERION:
{criteria}

RESPONSE:
{response}

One word:"""


SKILL_FILES = {
    "objectum": EVALS.parent / "skills" / "objectum" / "SKILL.md",
    "epistemic-action": EVALS.parent / "skills" / "epistemic-action" / "SKILL.md",
}


def skill_body(skill):
    """The SKILL.md minus its frontmatter, for the always-on arm."""
    t = SKILL_FILES[skill].read_text()
    return t.split("---", 2)[2].strip() if t.startswith("---") else t


# Four arms:
#   with    - plugin on, prompt says "Use the X skill"
#   without - plugin off, same prompt; it tries, fails, answers anyway
#   plain   - plugin off, plain prompt with no mention of any skill
#   always  - plugin off, plain prompt, skill text pinned in the system prompt
SETTINGS_FOR = {"with": "with", "without": "without", "plain": "without",
                "always": "without"}
NAMES_SKILL = {"with", "without"}


def run_agent(prompt, arm, tools, workdir, model, timeout, skill=None):
    cmd = [
        "claude", "-p", prompt,
        "--settings", str(SETTINGS / f"{SETTINGS_FOR[arm]}.json"),
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "dontAsk",
        "--model", model,
        "--allowedTools", *tools,
    ]
    if arm == "always":
        cmd += ["--append-system-prompt", skill_body(skill)]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=workdir)
        raw = r.stdout
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "last_message": "", "tools": [], "cost": 0,
                "turns": 0, "skill_loaded": False, "seconds": timeout}

    last, tools_used, cost, turns = "", [], 0.0, 0
    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("type") == "result":
            last = o.get("result") or last
            cost = o.get("total_cost_usd") or cost
            turns = o.get("num_turns") or turns
        msg = o.get("message")
        msg = msg if isinstance(msg, dict) else {}
        content = msg.get("content")
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    tools_used.append({"name": b["name"], "input": b.get("input") or {}})
                if isinstance(b, dict) and b.get("type") == "text" and msg.get("role") == "assistant":
                    last = b.get("text") or last

    return {
        "error": None, "last_message": last, "tools": tools_used,
        "cost": cost, "turns": turns, "seconds": round(time.time() - t0, 1),
        "skill_loaded": None, "raw": raw,
    }


def skill_loaded(raw, skill):
    """A Skill call is not a skill load. The baseline calls it and gets
    "Unknown skill", so look for the body's own words instead."""
    if "Unknown skill" in raw:
        pass
    return any(m in raw for m in SKILL_MARKERS[skill])


def grade_regex(g, res, sandbox):
    tgt = g.get("target")
    if isinstance(tgt, dict) and tgt.get("source") == "file":
        f = sandbox / tgt["path"]
        text = f.read_text(errors="replace") if f.exists() else ""
    else:
        text = res["last_message"]
    hit = re.search(g["pattern"], text) is not None
    return hit if g.get("match", "contains") == "contains" else not hit


def grade_tool_used(g, res):
    n = sum(1 for t in res["tools"] if t["name"] == g["tool"])
    lo = g.get("min", 1)
    hi = g.get("max", 10 ** 9)
    return lo <= n <= hi


def grade_tool_order(g, res):
    names = [t["name"] for t in res["tools"]]
    if g["before"] not in names or g["after"] not in names:
        return False
    return names.index(g["before"]) < names.index(g["after"])


def grade_llm(g, res, model, votes):
    prompt = JUDGE.format(criteria=g["criteria"], response=res["last_message"][:6000])
    out = []
    for _ in range(votes):
        r = subprocess.run(["claude", "-p", prompt, "--model", model,
                            "--settings", str(SETTINGS / "without.json")],
                           capture_output=True, text=True, timeout=180)
        w = (r.stdout or "").strip().upper()
        out.append("PASS" in w and "FAIL" not in w)
    return sum(out) > len(out) / 2, out


def run_case(rel, spec, arm, run_idx, args):
    skill = rel.split("/")[0]
    prompt = (f"{gen_cases.SLASH[skill]} {spec['prompt']}"
              if arm in NAMES_SKILL else spec["prompt"])
    sandbox = pathlib.Path(tempfile.mkdtemp(prefix="suiteA-"))
    fixture = SCAFFOLD_HARD if rel in getattr(gen_cases, "HARD_KEYS", set()) else SCAFFOLD
    subprocess.run(["bash", str(fixture), str(sandbox)], check=True,
                   capture_output=True)

    res = run_agent(prompt, arm, spec["tools"], sandbox, args.model, args.timeout,
                    skill=skill)
    res["skill_loaded"] = skill_loaded(res.get("raw", ""), skill)
    blob = json.dumps([t.get("input") for t in res["tools"]])
    res["read_skill_from_disk"] = any(h in blob for h in PLUGIN_PATH_HINTS)

    graded = []
    for g in spec["graders"]:
        t = g["type"]
        if t == "regex":
            ok, ev = grade_regex(g, res, sandbox), None
        elif t == "tool_used":
            ok, ev = grade_tool_used(g, res), None
        elif t == "tool_order":
            ok, ev = grade_tool_order(g, res), None
        elif t == "llm":
            ok, ev = grade_llm(g, res, args.judge_model, args.votes)
        else:
            continue
        graded.append({"name": g["name"], "type": t, "weight": g.get("weight", 1),
                       "passed": bool(ok), "votes": ev})

    total = sum(x["weight"] for x in graded)
    score = sum(x["weight"] for x in graded if x["passed"]) / total if total else 0

    shutil.rmtree(sandbox, ignore_errors=True)
    res.pop("raw", None)
    return {"case": rel, "arm": arm, "run": run_idx, "score": round(score, 3),
            "skill_loaded": res["skill_loaded"],
            "read_skill_from_disk": res["read_skill_from_disk"],
            "turns": res["turns"],
            "cost": res["cost"], "seconds": res["seconds"], "error": res["error"],
            "graders": graded, "last_message": res["last_message"][:1500],
            "tool_sequence": [t["name"] for t in res["tools"]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--judge-model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--votes", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--case", default=None)
    ap.add_argument("--arms", default="with,without",
                    help="comma list of: with, without, plain, always")
    ap.add_argument("--out", default=str(EVALS / ".local" / "suite_a_p.json"))
    args = ap.parse_args()

    jobs = []
    for rel, spec in gen_cases.CASES.items():
        if args.case and args.case not in rel:
            continue
        for arm in args.arms.split(","):
            for i in range(1, args.runs + 1):
                jobs.append((rel, spec, arm, i))

    print(f"{len(jobs)} runs ({args.parallel} at a time)", file=sys.stderr)
    out = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(run_case, *j, args): j for j in jobs}
        for n, f in enumerate(as_completed(futs), 1):
            rel, _, arm, i = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"case": rel, "arm": arm, "run": i, "score": 0,
                     "error": f"{type(e).__name__}: {e}", "graders": [],
                     "skill_loaded": False, "turns": 0, "cost": 0}
            out.append(r)
            flag = "S" if r.get("skill_loaded") else "-"
            print(f"  [{n}/{len(jobs)}] {rel} {arm}#{i} {r['score']:.2f} [{flag}]",
                  file=sys.stderr)
            pathlib.Path(args.out).write_text(json.dumps(out, indent=2))

    pathlib.Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"\nwrote {args.out}")
    print(f"total cost ${sum(r.get('cost') or 0 for r in out):.2f}")


if __name__ == "__main__":
    main()
