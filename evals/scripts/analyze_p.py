#!/usr/bin/env python3
"""Scores a `claude -p` Suite A run against the thresholds committed in METHOD.md.

Excludes two kinds of run and says how many it dropped:

- runs where the harness itself errored, which measure nothing;
- baseline runs that reached the skill on disk anyway, which are not baseline.
"""

import argparse
import json
import pathlib
import statistics
import sys

KIND = {
    "trap-filename": "trap", "trap-readme-config": "trap", "trap-version": "trap",
    "trap-doc-code": "trap", "run-it": "trap", "ticket-body": "trap",
    "missing-file": "trap",
    "control-trivial": "control", "control-no-fact": "control",
    "control-general": "control",
    "unverifiable": "unverifiable",
    "hard-config-chain": "trap", "hard-barrel-export": "trap",
    "hard-dead-branch": "trap", "hard-lockfile": "trap",
    "hard-vacuous-test": "trap",
    "failing-test-first": "order",
    "probe-residue": "residue",
}

UNVEIL = {"opened-the-file", "opened-a-file", "ran-something", "ran-it",
          "read-the-ticket", "read-more-than-one-file", "ran-the-suite"}
PRIMARY = {
    "says-currency", "names-the-contradiction", "says-17", "says-no-retry",
    "plain-answer-no-hedge", "brief-acknowledgement", "answers-conflict",
    "surfaces-the-residual", "reports-the-real-failure", "fix-is-correct",
    "says-100", "follows-body-not-title", "says-it-does-not-exist",
    "says-zero", "follows-the-barrel", "finds-the-unreachable-branch",
    "says-lockfile-version", "sees-through-the-green",
}


def short(case):
    return case.split("/")[-1]


def rate(hits, total):
    return hits / total if total else None


def f(x):
    return "n/a" if x is None else f"{x:.3f}"


def analyse(runs):
    m = {k: [0, 0] for k in ("trap", "unveil", "control", "leak", "residue",
                             "order", "unver")}
    turns = []
    for r in runs:
        g = {x["name"]: x for x in r["graders"]}
        kind = KIND.get(short(r["case"]), "other")

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
        elif kind == "unverifiable" and prim:
            m["unver"][1] += 1
            m["unver"][0] += 1 if prim["passed"] else 0
        elif kind == "order" and "ran-before-editing" in g:
            m["order"][1] += 1
            m["order"][0] += 1 if g["ran-before-editing"]["passed"] else 0
        elif kind == "residue" and "no-print-left-in-source" in g:
            m["residue"][1] += 1
            m["residue"][0] += 0 if g["no-print-left-in-source"]["passed"] else 1

    return {
        "trap": rate(*m["trap"]), "n_trap": m["trap"][1],
        "unveil": rate(*m["unveil"]),
        "control_pass": rate(*m["control"]), "n_control": m["control"][1],
        "hedge": None if not m["control"][1] else 1 - m["control"][0] / m["control"][1],
        "leak": rate(*m["leak"]),
        "residue": rate(*m["residue"]),
        "order": rate(*m["order"]),
        "unver": rate(*m["unver"]),
        "turns": statistics.median(turns) if turns else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--label", default="run")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.results).read_text())

    errored = [r for r in data if r.get("error")]
    clean = [r for r in data if not r.get("error")]

    def contaminated(r):
        return r["arm"] == "without" and (
            r.get("read_skill_from_disk") or r.get("skill_loaded")
        )

    dirty = [r for r in clean if contaminated(r)]
    clean = [r for r in clean if not contaminated(r)]

    w = [r for r in clean if r["arm"] == "with"]
    o = [r for r in clean if r["arm"] == "without"]

    print(f"=== {args.label}")
    print(f"  records {len(data)}; harness errors dropped {len(errored)}; "
          f"contaminated baselines dropped {len(dirty)}")
    print(f"  scored: with n={len(w)}, without n={len(o)}")
    loaded = sum(1 for r in w if r.get("skill_loaded"))
    print(f"  skill loaded in treatment arm: {loaded}/{len(w)}")
    if dirty:
        print(f"  contamination rate in baseline: {len(dirty)}/{len(dirty) + len(o)}")

    W, O = analyse(w), analyse(o)
    print(f"\n  metric                 with     without")
    for key, name in (("trap", "trap accuracy"), ("unveil", "unveil rate"),
                      ("hedge", "false-hedge (control)"), ("leak", "audit-leak"),
                      ("residue", "probe-residue"), ("order", "test before edit"),
                      ("unver", "unverifiable handled")):
        print(f"  {name:22s} {f(W[key]):>7s}  {f(O[key]):>7s}")
    print(f"  {'median control turns':22s} {str(W['turns']):>7s}  {str(O['turns']):>7s}")
    print(f"  (traps n={W['n_trap']}/{O['n_trap']}, controls n={W['n_control']}/{O['n_control']})")

    print("\n=== thresholds from METHOD.md")
    ok = []

    def check(label, passed, detail):
        ok.append(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}: {detail}")

    ta, tb = W["trap"], O["trap"]
    check("trap accuracy >= 0.90", ta is not None and ta >= 0.90, f(ta))
    check("trap accuracy >= without + 0.25",
          None not in (ta, tb) and ta - tb >= 0.25,
          f"{f(ta)} vs {f(tb)}" + (f", delta {ta-tb:+.3f}" if None not in (ta, tb) else ""))
    check("unveil rate >= 0.90", W["unveil"] is not None and W["unveil"] >= 0.90,
          f(W["unveil"]))
    hw, ho = W["hedge"], O["hedge"]
    check("false-hedge <= 0.10", hw is not None and hw <= 0.10, f(hw))
    check("false-hedge <= without + 0.05",
          None not in (hw, ho) and hw <= ho + 0.05, f"{f(hw)} vs {f(ho)}")
    check("audit-leak == 0", W["leak"] == 0, f(W["leak"]))
    check("probe-residue == 0", W["residue"] == 0, f(W["residue"]))
    mw, mo = W["turns"], O["turns"]
    check("median control turns <= without x 1.5",
          None not in (mw, mo) and mw <= mo * 1.5, f"{mw} vs {mo}")

    print(f"\n  {'ALL THRESHOLDS MET' if all(ok) else 'FALSIFIED: at least one threshold missed'}")

    print("\n=== per case (with / without)")
    cases = sorted({r["case"] for r in clean})
    for c in cases:
        ws = [r["score"] for r in w if r["case"] == c]
        os_ = [r["score"] for r in o if r["case"] == c]
        a = sum(ws) / len(ws) if ws else float("nan")
        b = sum(os_) / len(os_) if os_ else float("nan")
        print(f"  {short(c):22s} {a:5.2f}  {b:5.2f}  {a-b:+.2f}   (n={len(ws)}/{len(os_)})")


if __name__ == "__main__":
    main()
