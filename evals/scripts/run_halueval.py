#!/usr/bin/env python3
"""HaluEval QA with and without `objectum`.

Each item gives a passage of knowledge, a question, and an answer. Half the answers
contain a hallucination: something the passage does not support. The task is to say
which.

This is `objectum`'s job with the evidence supplied rather than fetched. The gate asks
whether each claim is supported by what was actually read, and this benchmark scores
exactly that judgment against a human label.

Both classes are near enough balanced in the sample, so accuracy is meaningful, but the
two error kinds are reported separately anyway. A gate biased toward suspicion will
catch every hallucination and start calling good answers hallucinated; that shows up as
a rising false-positive rate, not as a lower score.
"""

import argparse
import json
import pathlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

EVALS = pathlib.Path(__file__).resolve().parents[1]
SETTINGS = EVALS / "settings"
DATA = EVALS / ".local" / "halueval_qa.json"

GATE = ("Use the objectum skill on your judgement before you give it, then answer "
        "below.\n\n")

TASK = """You are checking whether an answer is grounded in the knowledge provided.

KNOWLEDGE:
{knowledge}

QUESTION:
{question}

ANSWER:
{answer}

Does the answer contain a hallucination - that is, does it assert something the \
knowledge does not support, or contradict it?

Reply with exactly one word: YES if it contains a hallucination, NO if it does not."""


def run_one(q, arm, model, timeout):
    prompt = (GATE if arm == "gated" else "") + TASK.format(
        knowledge=q["knowledge"], question=q["question"], answer=q["answer"])
    cmd = [
        "claude", "-p", prompt,
        "--settings", str(SETTINGS / ("with.json" if arm == "gated" else "without.json")),
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "dontAsk",
        "--model", model,
    ]
    if arm == "gated":
        cmd += ["--allowedTools", "Skill"]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        raw = r.stdout
    except subprocess.TimeoutExpired:
        return {"arm": arm, "error": "timeout", "correct": False}

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

    t = (last or "").strip().upper()
    pred = "yes" if t.startswith("YES") or "**YES**" in t else (
        "no" if t.startswith("NO") or "**NO**" in t else
        ("yes" if "YES" in t and "NO" not in t else "no" if "NO" in t else "?"))
    gold = q["hallucination"].strip().lower()
    return {
        "arm": arm, "pred": pred, "gold": gold, "correct": pred == gold,
        "skill_loaded": any(m in raw for m in ("Desvelamento", "Pôr-a-frente",
                                               "Contra-desvelamento")),
        "seconds": round(time.time() - t0, 1), "error": None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--parallel", type=int, default=5)
    ap.add_argument("--out", default=str(EVALS / ".local" / "halueval_run.json"))
    args = ap.parse_args()

    qs = json.loads(DATA.read_text())[: args.n]
    jobs = [(q, a) for q in qs for a in ("gated", "plain")]
    print(f"{len(qs)} items x 2 arms = {len(jobs)} runs", file=sys.stderr)

    out = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(run_one, q, a, args.model, args.timeout): (q, a)
                for q, a in jobs}
        for n, f in enumerate(as_completed(futs), 1):
            q, a = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"arm": a, "error": f"{type(e).__name__}: {e}", "correct": False}
            out.append(r)
            if n % 20 == 0 or n == len(jobs):
                print(f"  [{n}/{len(jobs)}]", file=sys.stderr)
            pathlib.Path(args.out).write_text(json.dumps(out, indent=2))

    print(f"\n{'arm':8s} {'n':>4s} {'accuracy':>9s} {'missed hall.':>13s} "
          f"{'false alarm':>12s}")
    st = {}
    for arm in ("gated", "plain"):
        rs = [r for r in out if r["arm"] == arm and not r.get("error") and r.get("pred") != "?"]
        if not rs:
            continue
        acc = sum(r["correct"] for r in rs) / len(rs)
        pos = [r for r in rs if r["gold"] == "yes"]
        neg = [r for r in rs if r["gold"] == "no"]
        miss = sum(1 for r in pos if r["pred"] == "no") / len(pos) if pos else 0
        fa = sum(1 for r in neg if r["pred"] == "yes") / len(neg) if neg else 0
        st[arm] = (acc, miss, fa)
        print(f"{arm:8s} {len(rs):>4d} {acc:>9.3f} {miss:>13.3f} {fa:>12.3f}")
    if len(st) == 2:
        g, p = st["gated"], st["plain"]
        print(f"\ndelta (gated - plain): accuracy {g[0]-p[0]:+.3f}, "
              f"missed {g[1]-p[1]:+.3f}, false alarm {g[2]-p[2]:+.3f}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
