#!/usr/bin/env python3
"""Scores Suite B: two review arms against Macroscope's labelled findings.

Three measurements, in order of how much they can be trusted:

1. **Citation validity** — deterministic. Does the cited file:line exist at the PR
   head? This is the direct test of objectum's central claim and needs no judge.
2. **Recall of confirmed defects** — does the arm find what a human agreed was real?
   Matched on file and line proximity, so it is a proxy: two findings at the same
   place are treated as the same finding, which will occasionally be wrong.
3. **Repeat rate of dismissed findings** — does the arm raise something a human
   already rejected? Same matching, same caveat.

Standards findings (Macroscope's checks against the team's written conventions) are
counted apart from correctness defects. An arm hunting bugs should not be marked down
for missing a TSDoc placement rule.
"""

import argparse
import json
import pathlib
import subprocess
import sys

LOCAL = pathlib.Path(__file__).resolve().parents[1] / ".local"
NEAR = 10  # lines; two findings this close are treated as the same place

_tree = {}


def tree(repo_dir, sha):
    key = (repo_dir, sha)
    if key not in _tree:
        r = subprocess.run(["git", "-C", repo_dir, "ls-tree", "-r", "--name-only", sha],
                           capture_output=True, text=True)
        _tree[key] = r.stdout.splitlines() if r.returncode == 0 else []
    return _tree[key]


def resolve(repo_dir, sha, path):
    files = tree(repo_dir, sha)
    if path in files:
        return path
    hits = [f for f in files if f.endswith("/" + path.lstrip("/"))]
    return hits[0] if len(hits) == 1 else None


def line_count(repo_dir, sha, path):
    real = resolve(repo_dir, sha, path)
    if not real:
        return None
    r = subprocess.run(["git", "-C", repo_dir, "show", f"{sha}:{real}"],
                       capture_output=True, text=True)
    return len(r.stdout.splitlines()) if r.returncode == 0 else None


def is_standards(f):
    b = f.get("body") or ""
    return "**Standard:**" in b or "MURMUR_IGNORE" in b


def same_place(a_path, a_line, b_path, b_line):
    if not a_path or not b_path:
        return False
    pa, pb = a_path.split("/")[-1], b_path.split("/")[-1]
    return pa == pb and abs((a_line or 0) - (b_line or 0)) <= NEAR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apps-dir", default=str(pathlib.Path.home() / "dev/acme/apps"))
    ap.add_argument("--services-dir", default=str(pathlib.Path.home() / "dev/acme/services"))
    args = ap.parse_args()

    runs = json.loads((LOCAL / "suite_b.json").read_text())
    mined = {(r["repo"], r["pr"]): r
             for r in json.loads((LOCAL / "macroscope" / "findings.json").read_text())}

    stats = {a: {"cited": 0, "valid": 0, "uncited": 0, "total": 0,
                 "recall_hit": 0, "recall_n": 0, "repeat": 0, "repeat_n": 0,
                 "cost": 0.0, "turns": 0, "skills": 0}
             for a in ("S", "G")}
    warnings = []

    for row in runs:
        if row.get("error"):
            continue
        repo_dir = args.apps_dir if row["repo"].endswith("/apps") else args.services_dir
        sha = row["head_sha"]
        ref = mined.get((row["repo"], row["pr"]), {}).get("findings", [])
        confirmed = [f for f in ref if f["label"] == "confirmed" and not is_standards(f)]
        dismissed = [f for f in ref if f["label"] == "false_positive"]

        for arm in ("S", "G"):
            a = row.get(arm) or {}
            if a.get("WARNING"):
                warnings.append(f"{row['repo']}#{row['pr']} {arm}: {a['WARNING']}")
            s = stats[arm]
            s["cost"] += a.get("cost") or 0
            s["turns"] += a.get("turns") or 0
            s["skills"] += len(a.get("skills_invoked") or [])
            found = a.get("findings") or []
            s["total"] += len(found)

            for f in found:
                n = line_count(repo_dir, sha, f["path"])
                if n is None:
                    s["cited"] += 1
                elif 1 <= f["line"] <= n:
                    s["cited"] += 1
                    s["valid"] += 1
                else:
                    s["cited"] += 1

            s["recall_n"] += len(confirmed)
            for c in confirmed:
                if any(same_place(c.get("path"), c.get("line"), f["path"], f["line"])
                       for f in found):
                    s["recall_hit"] += 1

            s["repeat_n"] += len(dismissed)
            for d in dismissed:
                if any(same_place(d.get("path"), d.get("line"), f["path"], f["line"])
                       for f in found):
                    s["repeat"] += 1

    print(f"PRs scored: {sum(1 for r in runs if not r.get('error'))}")
    if warnings:
        print("\n!! WRITE VERB SEEN IN A TRANSCRIPT:")
        for w in warnings:
            print("  " + w)
    else:
        print("no write verb appeared in any transcript")

    print(f"\n  metric                    arm S     arm G")
    def pct(h, n):
        return "n/a" if not n else f"{h/n:.3f}"
    S, G = stats["S"], stats["G"]
    print(f"  findings raised        {S['total']:>8d}  {G['total']:>8d}")
    print(f"  citation validity      {pct(S['valid'], S['cited']):>8s}  {pct(G['valid'], G['cited']):>8s}")
    print(f"  recall of confirmed    {pct(S['recall_hit'], S['recall_n']):>8s}  {pct(G['recall_hit'], G['recall_n']):>8s}")
    print(f"  repeat of dismissed    {pct(S['repeat'], S['repeat_n']):>8s}  {pct(G['repeat'], G['repeat_n']):>8s}")
    print(f"  skills invoked         {S['skills']:>8d}  {G['skills']:>8d}")
    print(f"  total turns            {S['turns']:>8d}  {G['turns']:>8d}")
    print(f"  cost usd               {S['cost']:>8.2f}  {G['cost']:>8.2f}")

    print("\n=== thresholds from METHOD.md (arm G)")
    cv_g = G["valid"] / G["cited"] if G["cited"] else None
    cv_s = S["valid"] / S["cited"] if S["cited"] else None
    rc_g = G["recall_hit"] / G["recall_n"] if G["recall_n"] else None
    rc_s = S["recall_hit"] / S["recall_n"] if S["recall_n"] else None
    rp_g = G["repeat"] / G["repeat_n"] if G["repeat_n"] else None
    rp_s = S["repeat"] / S["repeat_n"] if S["repeat_n"] else None
    ok = []

    def check(label, passed, detail):
        ok.append(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}: {detail}")

    check("citation validity >= 0.95", cv_g is not None and cv_g >= 0.95,
          "n/a" if cv_g is None else f"{cv_g:.3f}")
    check("citation validity > arm S",
          None not in (cv_g, cv_s) and cv_g > cv_s,
          f"{'n/a' if cv_g is None else f'{cv_g:.3f}'} vs {'n/a' if cv_s is None else f'{cv_s:.3f}'}")
    check("recall >= arm S", None not in (rc_g, rc_s) and rc_g >= rc_s,
          f"{'n/a' if rc_g is None else f'{rc_g:.3f}'} vs {'n/a' if rc_s is None else f'{rc_s:.3f}'}")
    check("repeat of dismissed <= arm S", None not in (rp_g, rp_s) and rp_g <= rp_s,
          f"{'n/a' if rp_g is None else f'{rp_g:.3f}'} vs {'n/a' if rp_s is None else f'{rp_s:.3f}'}")

    print(f"\n  {'ALL THRESHOLDS MET' if all(ok) else 'FALSIFIED: at least one threshold missed'}")


if __name__ == "__main__":
    main()
