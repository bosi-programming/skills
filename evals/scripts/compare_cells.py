#!/usr/bin/env python3
"""Compares the four cells that runs 4 and 5 happen to form.

Run 4 ran while `~/.claude/CLAUDE.md` still carried an abbreviated "Objectum gate";
run 5 ran after it was removed. Each run already had a with-plugin and a no-plugin
arm, so together they make a 2x2:

  A  no plugin, no CLAUDE.md gate   - genuinely uninstructed
  B  no plugin, CLAUDE.md gate      - the short version only
  C  plugin,    no CLAUDE.md gate   - the full skill only
  D  plugin,    CLAUDE.md gate      - both

A against B is the clean one: those two differ in nothing but the CLAUDE.md section.
C against D is not clean, because objectum's SKILL.md was also edited between the runs
to stop the audit leaking. That is flagged rather than hidden.
"""

import argparse
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze_p import KIND, PRIMARY, UNVEIL, short  # noqa: E402


def load(path):
    data = json.loads(pathlib.Path(path).read_text())
    keep = []
    for r in data:
        if r.get("error"):
            continue
        if r["arm"] == "without" and (r.get("read_skill_from_disk") or r.get("skill_loaded")):
            continue
        keep.append(r)
    return keep


def metrics(runs):
    m = {k: [0, 0] for k in ("trap", "unveil", "control", "leak", "order")}
    turns, scores = [], []
    for r in runs:
        g = {x["name"]: x for x in r["graders"]}
        kind = KIND.get(short(r["case"]), "other")
        scores.append(r["score"])
        if "no-audit-leak" in g:
            m["leak"][1] += 1
            m["leak"][0] += 0 if g["no-audit-leak"]["passed"] else 1
        prim = next((g[n] for n in g if n in PRIMARY), None)
        if kind == "trap" and prim:
            m["trap"][1] += 1
            m["trap"][0] += 1 if prim["passed"] else 0
            for n in UNVEIL:
                if n in g:
                    m["unveil"][1] += 1
                    m["unveil"][0] += 1 if g[n]["passed"] else 0
        elif kind == "control" and prim:
            m["control"][1] += 1
            m["control"][0] += 1 if prim["passed"] else 0
            turns.append(r.get("turns") or 0)
        elif kind == "order" and "ran-before-editing" in g:
            m["order"][1] += 1
            m["order"][0] += 1 if g["ran-before-editing"]["passed"] else 0

    def rate(p):
        return p[0] / p[1] if p[1] else None

    return {
        "n": len(runs),
        "mean_score": statistics.mean(scores) if scores else None,
        "trap": rate(m["trap"]),
        "unveil": rate(m["unveil"]),
        "control": rate(m["control"]),
        "leak": rate(m["leak"]),
        "order": rate(m["order"]),
        "turns": statistics.median(turns) if turns else None,
    }


def f(x):
    return "n/a" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-gate", required=True, help="run 4 json (CLAUDE.md gate present)")
    ap.add_argument("--no-gate", required=True, help="run 5 json (gate removed)")
    args = ap.parse_args()

    r4, r5 = load(args.with_gate), load(args.no_gate)
    cells = {
        "A  no plugin, no gate": metrics([r for r in r5 if r["arm"] == "without"]),
        "B  no plugin, gate   ": metrics([r for r in r4 if r["arm"] == "without"]),
        "C  plugin,    no gate": metrics([r for r in r5 if r["arm"] == "with"]),
        "D  plugin,    gate   ": metrics([r for r in r4 if r["arm"] == "with"]),
    }

    cols = ["n", "mean_score", "trap", "unveil", "control", "leak", "order", "turns"]
    print(f"{'cell':24s} " + " ".join(f"{c:>10s}" for c in cols))
    for name, m in cells.items():
        print(f"{name:24s} " + " ".join(f"{f(m[c]):>10s}" for c in cols))

    A, B, C, D = (cells["A  no plugin, no gate"], cells["B  no plugin, gate   "],
                  cells["C  plugin,    no gate"], cells["D  plugin,    gate   "])

    def delta(x, y, k):
        if None in (x[k], y[k]):
            return "n/a"
        return f"{x[k] - y[k]:+.3f}"

    print("\n=== B minus A: what the CLAUDE.md gate alone does")
    print("    (clean: these differ only in that section)")
    for k in ("mean_score", "trap", "unveil", "control", "order"):
        print(f"    {k:12s} {delta(B, A, k)}")

    print("\n=== C minus A: what the full skill alone does")
    for k in ("mean_score", "trap", "unveil", "control", "order"):
        print(f"    {k:12s} {delta(C, A, k)}")

    print("\n=== D minus B: what the skill adds on top of the gate")
    print("    (NOT clean: objectum's SKILL.md was also edited between these runs)")
    for k in ("mean_score", "trap", "unveil", "control", "order"):
        print(f"    {k:12s} {delta(D, B, k)}")


if __name__ == "__main__":
    main()
