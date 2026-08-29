#!/usr/bin/env python3
"""CRUXEval with and without `epistemic-action`.

This benchmark is that skill's thesis stated as a task. Given a Python function and an
input, say what it returns. The model can simulate the code in its head, or it can run
it. `epistemic-action` says plainly: "Acting is cheaper than imagining, not more
expensive", and "predicting means simulate the code, simulate the input, simulate the
output, then act. Acting means run it and read."

So Bash is granted to both arms. The question is not whether running is allowed, it is
whether the model bothers. Two numbers matter and they are reported together:

- **ran it** - the share of runs that actually executed the code.
- **accuracy** - exact match on the returned value after normalising.

If the skill works, both rise together. If accuracy rises without execution rising, the
skill is doing something other than what it claims.
"""

import argparse
import ast
import json
import pathlib
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

EVALS = pathlib.Path(__file__).resolve().parents[1]
SETTINGS = EVALS / "settings"
DATA = EVALS / ".local" / "cruxeval.json"

GATE = ("Use the epistemic-action skill, then answer the question below.\n\n")

TASK = """Here is a Python function:

```python
{code}
```

What does `f({inp})` return?

Put the returned value on the last line of your reply, on its own, as a Python literal \
and nothing else."""

BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)


def norm(s):
    """Compare by value where possible, so [(4, 1)] and [(4,1)] agree."""
    s = (s or "").strip().strip("`").strip()
    s = re.sub(r"^```[a-z]*\n?|```$", "", s).strip()
    try:
        return repr(ast.literal_eval(s))
    except Exception:
        return re.sub(r"\s+", "", s.lower())


def run_one(q, arm, model, timeout):
    prompt = (GATE if arm == "gated" else "") + TASK.format(code=q["code"], inp=q["input"])
    cmd = [
        "claude", "-p", prompt,
        "--settings", str(SETTINGS / ("with.json" if arm == "gated" else "without.json")),
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "dontAsk",
        "--model", model,
        "--allowedTools", "Bash", "Write", "Read", "Skill",
    ]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        raw = r.stdout
    except subprocess.TimeoutExpired:
        return {"id": q["id"], "arm": arm, "correct": False, "ran": False,
                "error": "timeout"}

    last, tools = "", []
    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("type") == "result":
            last = o.get("result") or last
        msg = o.get("message")
        msg = msg if isinstance(msg, dict) else {}
        c = msg.get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    tools.append(b["name"])
                if isinstance(b, dict) and b.get("type") == "text" and msg.get("role") == "assistant":
                    last = b.get("text") or last

    lines = [l for l in (last or "").splitlines() if l.strip()]
    got = norm(lines[-1]) if lines else ""
    if got != norm(q["output"]):
        spans = BOLD.findall(last or "")
        if spans and norm(spans[-1]) == norm(q["output"]):
            got = norm(spans[-1])

    return {
        "id": q["id"], "arm": arm,
        "correct": got == norm(q["output"]),
        "ran": "Bash" in tools,
        "got": got[:120], "want": norm(q["output"])[:120],
        "skill_loaded": any(m in raw for m in ("Tetris rule", "Tetris players",
                                               "probe loop")),
        "seconds": round(time.time() - t0, 1), "error": None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--parallel", type=int, default=5)
    ap.add_argument("--out", default=str(EVALS / ".local" / "cruxeval_run.json"))
    args = ap.parse_args()

    qs = json.loads(DATA.read_text())[: args.n]
    jobs = [(q, a) for q in qs for a in ("gated", "plain")]
    print(f"{len(qs)} problems x 2 arms = {len(jobs)} runs", file=sys.stderr)

    out = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(run_one, q, a, args.model, args.timeout): (q, a)
                for q, a in jobs}
        for n, f in enumerate(as_completed(futs), 1):
            q, a = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"id": q["id"], "arm": a, "correct": False, "ran": False,
                     "error": f"{type(e).__name__}: {e}"}
            out.append(r)
            if n % 20 == 0 or n == len(jobs):
                print(f"  [{n}/{len(jobs)}]", file=sys.stderr)
            pathlib.Path(args.out).write_text(json.dumps(out, indent=2))

    print(f"\n{'arm':8s} {'n':>4s} {'accuracy':>9s} {'ran it':>8s} {'skill':>7s}")
    st = {}
    for arm in ("gated", "plain"):
        rs = [r for r in out if r["arm"] == arm and not r.get("error")]
        if not rs:
            continue
        acc = sum(r["correct"] for r in rs) / len(rs)
        ran = sum(r["ran"] for r in rs) / len(rs)
        sk = sum(1 for r in rs if r.get("skill_loaded"))
        st[arm] = (acc, ran)
        print(f"{arm:8s} {len(rs):>4d} {acc:>9.3f} {ran:>8.3f} {sk:>4d}/{len(rs)}")
    if len(st) == 2:
        print(f"\ndelta (gated - plain): accuracy {st['gated'][0]-st['plain'][0]:+.3f}, "
              f"ran it {st['gated'][1]-st['plain'][1]:+.3f}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
