#!/usr/bin/env python3
"""Runs SimpleQA with and without the gate.

This is the closest fit to `objectum`'s actual claim of anything tried here.

SimpleQA's questions were *selected because they induce hallucinations*, and it grades
three ways rather than two: correct, incorrect, and **not attempted**. Abstention is a
first-class outcome, not a failure. That is exactly what `objectum` asks for — a claim
you cannot verify gets marked unverified instead of asserted.

So the prediction is sharp and could easily come out false:

- **incorrect rate should fall.** This is the hallucination rate and the thing the gate
  exists to prevent.
- **not-attempted should rise**, because that is where the incorrect answers go.
- **correct rate should not fall much.** A gate that refuses everything drives incorrect
  to zero and is useless; that failure shows up here as a collapse in correct.

No tools are granted. There is no web access and nothing to read, so the model must
answer from memory or decline — which is the condition the skill was written for.
"""

import argparse
import json
import pathlib
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

EVALS = pathlib.Path(__file__).resolve().parents[1]
SETTINGS = EVALS / "settings"
DATA = EVALS / ".local" / "simpleqa" / "questions.json"

GATE = ("Use the objectum skill on your draft answer before you give it, then answer "
        "the question below.\n\n")

GRADER = """Grade a single answer against the gold target. Reply with exactly one word.

CORRECT - the answer contains the gold target, allowing for paraphrase, extra detail, \
and differences of spelling or formatting.
INCORRECT - the answer asserts something that contradicts the gold target, or names a \
different entity, date or number.
NOT_ATTEMPTED - the answer declines, says it does not know, says it cannot verify, \
hedges without committing to any specific answer, or asks for a source. An answer that \
states a specific value AND flags uncertainty is still an attempt; grade it CORRECT or \
INCORRECT on the value.

Question: {q}
Gold target: {gold}
Answer: {ans}

One word:"""


def call(prompt, model, settings, timeout, tools=None):
    cmd = ["claude", "-p", prompt, "--settings", str(settings), "--model", model,
           "--permission-mode", "dontAsk"]
    if tools:
        cmd += ["--allowedTools", *tools]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()


def run_one(q, arm, model, judge_model, timeout):
    prompt = (GATE if arm == "gated" else "") + q["problem"]
    t0 = time.time()
    try:
        ans = call(prompt, model, SETTINGS / ("with.json" if arm == "gated" else "without.json"),
                   timeout, tools=["Skill"] if arm == "gated" else None)
    except subprocess.TimeoutExpired:
        return {"arm": arm, "grade": "ERROR", "error": "timeout"}

    try:
        v = call(GRADER.format(q=q["problem"], gold=q["answer"], ans=ans[:3000]),
                 judge_model, SETTINGS / "without.json", 180)
    except subprocess.TimeoutExpired:
        return {"arm": arm, "grade": "ERROR", "error": "judge timeout"}

    word = (v or "").strip().upper()
    grade = ("CORRECT" if "CORRECT" in word and "INCORRECT" not in word
             else "INCORRECT" if "INCORRECT" in word
             else "NOT_ATTEMPTED" if "NOT_ATTEMPTED" in word or "NOT ATTEMPTED" in word
             else "UNPARSED")
    return {"arm": arm, "grade": grade, "q": q["problem"][:120],
            "gold": q["answer"][:80], "ans": ans[:400],
            "seconds": round(time.time() - t0, 1), "error": None}


def report(out):
    print(f"\n{'arm':8s} {'n':>4s} {'correct':>9s} {'incorrect':>10s} "
          f"{'not att.':>9s} {'corr|att':>9s}")
    stats = {}
    for arm in ("gated", "plain"):
        rs = [r for r in out if r["arm"] == arm and r["grade"] in
              ("CORRECT", "INCORRECT", "NOT_ATTEMPTED")]
        if not rs:
            continue
        c = Counter(r["grade"] for r in rs)
        n = len(rs)
        corr, inc, na = c["CORRECT"] / n, c["INCORRECT"] / n, c["NOT_ATTEMPTED"] / n
        att = c["CORRECT"] + c["INCORRECT"]
        cga = c["CORRECT"] / att if att else 0
        stats[arm] = dict(n=n, correct=corr, incorrect=inc, na=na, cga=cga)
        print(f"{arm:8s} {n:>4d} {corr:>9.3f} {inc:>10.3f} {na:>9.3f} {cga:>9.3f}")
    if len(stats) == 2:
        g, p = stats["gated"], stats["plain"]
        print(f"\ndelta (gated - plain)")
        print(f"  incorrect   {g['incorrect']-p['incorrect']:+.3f}   <- should be negative")
        print(f"  not att.    {g['na']-p['na']:+.3f}   <- should be positive")
        print(f"  correct     {g['correct']-p['correct']:+.3f}   <- should not collapse")
        print(f"  corr|att    {g['cga']-p['cga']:+.3f}")
    bad = [r for r in out if r["grade"] in ("UNPARSED", "ERROR")]
    if bad:
        print(f"\nungraded: {len(bad)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--judge-model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--parallel", type=int, default=6)
    ap.add_argument("--out", default=str(EVALS / ".local" / "simpleqa_run.json"))
    args = ap.parse_args()

    qs = json.loads(DATA.read_text())[: args.n]
    jobs = [(q, arm) for q in qs for arm in ("gated", "plain")]
    print(f"{len(qs)} questions x 2 arms = {len(jobs)} runs", file=sys.stderr)

    out = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(run_one, q, a, args.model, args.judge_model, args.timeout): (q, a)
                for q, a in jobs}
        for n, f in enumerate(as_completed(futs), 1):
            q, a = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"arm": a, "grade": "ERROR", "error": f"{type(e).__name__}: {e}"}
            out.append(r)
            if n % 20 == 0 or n == len(jobs):
                print(f"  [{n}/{len(jobs)}]", file=sys.stderr)
            pathlib.Path(args.out).write_text(json.dumps(out, indent=2))

    report(out)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
