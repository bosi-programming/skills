#!/usr/bin/env python3
"""Tests `objectum` doing the one job it does in production: gating a review draft.

`bosi-code-review` step 6 hands the gate an aggregate of sub-agent findings and says
"every finding is IMAGINED until you open the file at that line yourself. Sub-agents
cite lines that don't exist."

So this plants exactly that. The draft below carries eight findings about the trap
fixture. Four are true and checkable. Four are false in the four ways step 6 names: a
line past the end of a file, a claim taken from a stale doc comment instead of the
code, a test asserted to pass that fails, and behaviour inferred from a filename.

Scoring is deterministic and two-sided, which is what stops a gate from winning by
deleting everything:

- **false surviving** - a planted falsehood still asserted in the final review. Lower
  is better; this is what the gate exists to remove.
- **true dropped** - a checkable finding the gate threw away. Lower is better; this is
  the cost of an over-eager gate.

A gate that cuts the whole draft scores perfectly on the first and terribly on the
second.
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

EVALS = pathlib.Path(__file__).resolve().parents[1]
SETTINGS = EVALS / "settings"
SCAFFOLD = EVALS / "scripts" / "scaffold.sh"

# Version 2. The first set was too obvious - a line 42 in a three-line file - and both
# arms cut all four without help. These are wrong by one detail each, the kind of thing
# that survives a skim: the right file, a plausible mechanism, one word that is false.
DRAFT = """F1 | src/utils/formatDate.ts:11 | Cents are truncated with `Math.floor`, so an amount of 1.999 renders as 1.99 instead of rounding up.
F2 | src/payments/chargeCard.ts:11 | The card token is sent in an `Authorization` header, which leaks it into gateway access logs.
F3 | src/utils/parseAmount.js:2 | A leading minus is preserved, so `parseAmount('-5')` returns -5 and negative amounts flow through unchecked.
F4 | package.json:4 | A `build` script runs before `test`, so a stale build can make the suite pass.
F5 | test/passes.test.js:1 | The file imports `assert/strict`, so every comparison is already strict and the explicit `strictEqual` is redundant.
F6 | src/payments/chargeCard.ts:14 | `ok` is computed as `res.status < 500`, so a 404 is reported to the caller as a success.
T1 | src/utils/formatDate.ts:11 | Cents are computed with `Math.round`, so a repeating fraction rounds rather than truncating.
T2 | src/payments/chargeCard.ts:12 | The card token is placed in the JSON request body, not in a header.
T3 | src/utils/parseAmount.js:2 | Every non-digit is stripped before `parseInt`, so a decimal separator is silently swallowed.
T4 | package.json:5 | The only script is `test`, and it runs `node test/passes.test.js` directly with no build step.
T5 | src/utils/formatDate.ts:8 | An unknown currency falls back to the code itself as the symbol, so `formatDate(5, 'JPY')` prints the letters JPY.
T6 | src/payments/chargeCard.ts:14 | `ok` is taken straight from `res.ok`, so any non-2xx is reported as a failure.
"""

TASK = """You are finishing a code review of this repository. Sub-agents produced the \
draft findings below. Your job is to produce the FINAL review that will be posted for \
the author to act on.

DRAFT FINDINGS:
{draft}

Output the final review as one finding per line in exactly this format, nothing else:

ID | verdict | one sentence

ID is the draft's id (F1, T1, ...). verdict is KEEP for a finding you are publishing \
as stated, or CUT for one you are removing. Include a line for every draft id."""

GATE = ("Use the objectum skill on your draft before you answer, at Full depth, six "
        "passes.\n\n")

FALSE_IDS = ["F1", "F2", "F3", "F4", "F5", "F6"]
TRUE_IDS = ["T1", "T2", "T3", "T4", "T5", "T6"]
LINE = re.compile(r"^\s*(F[1-6]|T[1-6])\s*\|\s*(KEEP|CUT)\b", re.I | re.M)


def run(arm, model, timeout):
    sandbox = pathlib.Path(tempfile.mkdtemp(prefix="gate-"))
    subprocess.run(["bash", str(SCAFFOLD), str(sandbox)], check=True,
                   capture_output=True)
    prompt = (GATE if arm == "gated" else "") + TASK.format(draft=DRAFT)
    cmd = [
        "claude", "-p", prompt,
        "--settings", str(SETTINGS / ("with.json" if arm == "gated" else "without.json")),
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "dontAsk",
        "--model", model,
        "--allowedTools", "Read", "Glob", "Grep", "Bash", "Skill",
    ]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=sandbox)
        raw = r.stdout
    except subprocess.TimeoutExpired:
        shutil.rmtree(sandbox, ignore_errors=True)
        return {"arm": arm, "error": "timeout"}

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
        content = msg.get("content")
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    tools.append(b["name"])
                if isinstance(b, dict) and b.get("type") == "text" and msg.get("role") == "assistant":
                    last = b.get("text") or last

    verdicts = {m.group(1).upper(): m.group(2).upper() for m in LINE.finditer(last)}
    shutil.rmtree(sandbox, ignore_errors=True)

    false_surviving = [i for i in FALSE_IDS if verdicts.get(i) == "KEEP"]
    true_dropped = [i for i in TRUE_IDS if verdicts.get(i) == "CUT"]
    unanswered = [i for i in FALSE_IDS + TRUE_IDS if i not in verdicts]

    return {
        "arm": arm,
        "error": None,
        "skill_loaded": any(m in raw for m in ("Desvelamento", "Pôr-a-frente",
                                               "Contra-desvelamento")),
        "verdicts": verdicts,
        "false_surviving": false_surviving,
        "true_dropped": true_dropped,
        "unanswered": unanswered,
        "tools": tools,
        "seconds": round(time.time() - t0, 1),
        "last": last[:2000],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--out", default=str(EVALS / ".local" / "gate_test.json"))
    args = ap.parse_args()

    jobs = [(arm, i) for arm in ("gated", "plain") for i in range(args.runs)]
    out = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(run, a, args.model, args.timeout): (a, i) for a, i in jobs}
        for n, f in enumerate(as_completed(futs), 1):
            a, i = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"arm": a, "error": f"{type(e).__name__}: {e}"}
            out.append(r)
            fs = len(r.get("false_surviving") or [])
            td = len(r.get("true_dropped") or [])
            print(f"  [{n}/{len(jobs)}] {a:6s} false_surviving={fs} true_dropped={td}",
                  file=sys.stderr)
            pathlib.Path(args.out).write_text(json.dumps(out, indent=2))

    print(f"\n{'arm':8s} {'n':>3s} {'false surviving':>16s} {'true dropped':>14s} "
          f"{'unanswered':>11s} {'skill loaded':>13s}")
    for arm in ("gated", "plain"):
        rs = [r for r in out if r["arm"] == arm and not r.get("error")]
        if not rs:
            continue
        fs = sum(len(r["false_surviving"]) for r in rs) / len(rs)
        td = sum(len(r["true_dropped"]) for r in rs) / len(rs)
        ua = sum(len(r["unanswered"]) for r in rs) / len(rs)
        sl = sum(1 for r in rs if r["skill_loaded"])
        print(f"{arm:8s} {len(rs):>3d} {fs:>16.2f} {td:>14.2f} {ua:>11.2f} "
              f"{sl:>9d}/{len(rs)}")
    print("\nout of 6 planted falsehoods and 6 checkable truths per run")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
