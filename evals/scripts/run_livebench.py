#!/usr/bin/env python3
"""Runs LiveBench reasoning questions with and without the gate.

Why this benchmark. Every fixture written here so far sits at the baseline's ceiling,
so no effect could be measured whether or not one exists. LiveBench is built to avoid
exactly that: the questions are hard, refreshed to stay out of training data, and each
carries a verifiable ground truth, so scoring needs no judge.

What it does and does not test. These are self-contained puzzles. There is no file to
open and no command to run, so `epistemic-action`'s whole repertoire is unavailable
here and nothing in this script speaks to it. What it does reach is one specific line
in `objectum`: "where the draft feels more finished than the evidence supports, narrow
the wording". In a constraint puzzle that means checking a candidate answer against
every clue before committing. A null result here would not falsify either skill; a
positive one is evidence beyond the fixtures.

Answers are compared after normalising case, spacing and markdown emphasis.
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

EVALS = pathlib.Path(__file__).resolve().parents[1]
SETTINGS = EVALS / "settings"
DATA = EVALS / ".local" / "livebench" / "reasoning.json"

GATE = ("Use the objectum skill on your draft answer before you give it, then answer "
        "the question below.\n\n")

BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)


def normalise(s):
    s = (s or "").strip().lower()
    # zebra_puzzle answers arrive wrapped in <solution> tags; the tags are format,
    # not answer, and comparing with them in fails every correct response.
    s = re.sub(r"</?solution>", "", s)
    s = s.replace("*", "").replace("`", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .")


def extract(text, truth):
    """LiveBench answers are wrapped in ** **. Take the last such span; fall back to
    the last line, which is where a model puts a bare answer."""
    spans = BOLD.findall(text or "")
    if spans:
        return normalise(spans[-1])
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return normalise(lines[-1]) if lines else ""


def run_one(q, arm, model, timeout):
    prompt = (GATE if arm == "gated" else "") + q["turns"][0]
    cmd = [
        "claude", "-p", prompt,
        "--settings", str(SETTINGS / ("with.json" if arm == "gated" else "without.json")),
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "dontAsk",
        "--model", model,
        "--allowedTools", "Skill",
    ]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        raw = r.stdout
    except subprocess.TimeoutExpired:
        return {"id": q["question_id"], "task": q["task"], "arm": arm,
                "correct": False, "error": "timeout"}

    last = ""
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
                if isinstance(b, dict) and b.get("type") == "text" and msg.get("role") == "assistant":
                    last = b.get("text") or last

    got, want = extract(last, q["ground_truth"]), normalise(q["ground_truth"])
    return {
        "id": q["question_id"], "task": q["task"], "arm": arm,
        "correct": got == want, "got": got[:120], "want": want[:120],
        "skill_loaded": any(m in raw for m in ("Desvelamento", "Pôr-a-frente",
                                               "Contra-desvelamento")),
        "seconds": round(time.time() - t0, 1), "error": None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="questions per task")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--parallel", type=int, default=6)
    ap.add_argument("--tasks", default="zebra_puzzle,spatial,web_of_lies_v2")
    ap.add_argument("--out", default=str(EVALS / ".local" / "livebench_run.json"))
    args = ap.parse_args()

    data = json.loads(DATA.read_text())
    wanted = args.tasks.split(",")
    picked = []
    for t in wanted:
        picked.extend([q for q in data if q["task"] == t][: args.n])

    jobs = [(q, arm) for q in picked for arm in ("gated", "plain")]
    print(f"{len(picked)} questions x 2 arms = {len(jobs)} runs", file=sys.stderr)

    out = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(run_one, q, a, args.model, args.timeout): (q, a)
                for q, a in jobs}
        for n, f in enumerate(as_completed(futs), 1):
            q, a = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"id": q["question_id"], "task": q["task"], "arm": a,
                     "correct": False, "error": f"{type(e).__name__}: {e}"}
            out.append(r)
            if n % 10 == 0 or n == len(jobs):
                print(f"  [{n}/{len(jobs)}]", file=sys.stderr)
            pathlib.Path(args.out).write_text(json.dumps(out, indent=2))

    print(f"\n{'task':18s} {'gated':>8s} {'plain':>8s} {'delta':>8s}  n")
    for t in wanted:
        rs = [r for r in out if r["task"] == t]
        g = [r for r in rs if r["arm"] == "gated"]
        p = [r for r in rs if r["arm"] == "plain"]
        if not g or not p:
            continue
        ga = sum(r["correct"] for r in g) / len(g)
        pa = sum(r["correct"] for r in p) / len(p)
        print(f"{t:18s} {ga:>8.3f} {pa:>8.3f} {ga-pa:>+8.3f}  {len(g)}")
    g = [r for r in out if r["arm"] == "gated"]
    p = [r for r in out if r["arm"] == "plain"]
    ga = sum(r["correct"] for r in g) / len(g)
    pa = sum(r["correct"] for r in p) / len(p)
    print(f"{'ALL':18s} {ga:>8.3f} {pa:>8.3f} {ga-pa:>+8.3f}  {len(g)}")
    loaded = sum(1 for r in g if r.get("skill_loaded"))
    print(f"\nskill loaded in gated arm: {loaded}/{len(g)}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
