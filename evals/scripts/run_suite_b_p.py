#!/usr/bin/env python3
"""Suite B through `claude -p`: two review arms over the same real pull requests.

- arm S: `acme-pr-review` invoked by name. The current internal standard.
- arm G: the same, plus `objectum` and `epistemic-action` invoked by name.

Macroscope already reviewed each of these PRs; its findings are the reference and are
read from the mined file rather than re-run.

SAFETY. `acme-pr-review` can post a review to GitHub on its own. Nothing here may
write to a real pull request, so this runner:

  - never passes --yolo,
  - tells the agent in the prompt to post nothing,
  - grants only read-only tools: no `gh pr review`, no `gh pr comment`,
  - runs with --permission-mode plan, which refuses edits and writes outright.

Run with --dry-run first and read the grants.
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
LOCAL = EVALS / ".local"
SETTINGS = EVALS / "settings"

TASK = """Review pull request {url} for correctness defects.

Do NOT post anything to GitHub. Do not run `gh pr review`, `gh pr comment`, or any
write API call. Report your findings here as text only.

Give every finding on its own line in exactly this format and nothing else:

SEVERITY | path/to/file.ext:LINE | one sentence describing the defect

SEVERITY is high, medium or low. The path must be the real repository path and the
line must exist in that file at this pull request's head commit. If you find no
defects, write: NO FINDINGS"""

ARM_PREFIX = {
    "S": "Use the acme-pr-review skill, then do this:\n\n",
    "G": ("Use the acme-pr-review skill, and also use the objectum and "
          "epistemic-action skills on your own draft before you answer. Every finding "
          "you report must cite a file and line you actually opened and read at this "
          "commit; cut any finding you cannot ground that way.\n\n"),
}

READ_ONLY_TOOLS = [
    "Read", "Glob", "Grep", "Skill",
    "Bash(gh api:*)", "Bash(gh pr view:*)", "Bash(gh pr diff:*)",
    "Bash(git log:*)", "Bash(git show:*)", "Bash(git diff:*)", "Bash(git ls-tree:*)",
]

FINDING_LINE = re.compile(
    r"^\s*(high|medium|low)\s*\|\s*([^|]+?):(\d+)\s*\|\s*(.+)$", re.I | re.M
)


def parse_findings(text):
    return [
        {"severity": m.group(1).lower(), "path": m.group(2).strip(),
         "line": int(m.group(3)), "body": m.group(4).strip()}
        for m in FINDING_LINE.finditer(text or "")
    ]


def run_arm(url, arm, repo_dir, model, timeout):
    prompt = ARM_PREFIX[arm] + TASK.format(url=url)
    cmd = [
        "claude", "-p", prompt,
        "--settings", str(SETTINGS / "with.json"),
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "plan",
        "--model", model,
        "--allowedTools", *READ_ONLY_TOOLS,
    ]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=repo_dir)
    except subprocess.TimeoutExpired:
        return {"raw": "", "last": "", "skills": [], "cost": 0, "turns": 0,
                "seconds": timeout, "error": "timeout"}

    last, skills, cost, turns = "", [], 0.0, 0
    write_attempt = None
    for line in r.stdout.splitlines():
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
                if isinstance(b, dict) and b.get("type") == "tool_use" and b["name"] == "Skill":
                    skills.append((b.get("input") or {}).get("skill"))
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    cmdline = json.dumps(b.get("input") or {})
                    for verb in ("gh pr review", "gh pr comment", "gh api -X POST",
                                 "gh api --method POST", "gh pr merge"):
                        if verb in cmdline:
                            write_attempt = verb
                if isinstance(b, dict) and b.get("type") == "text" and msg.get("role") == "assistant":
                    last = b.get("text") or last

    return {"raw": r.stdout, "last": last, "skills": skills, "cost": cost,
            "turns": turns, "seconds": round(time.time() - t0, 1), "error": None,
            "write_attempt": write_attempt}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prs", type=int, default=10)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--apps-dir", default=str(pathlib.Path.home() / "dev/acme/apps"))
    ap.add_argument("--services-dir", default=str(pathlib.Path.home() / "dev/acme/services"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = json.loads((LOCAL / "macroscope" / "findings.json").read_text())
    selected = [
        r for r in data
        if any(f["label"] in ("confirmed", "false_positive") for f in r["findings"])
    ][: args.prs]

    print(f"{len(selected)} labelled PRs selected", file=sys.stderr)
    if args.dry_run:
        for r in selected:
            labels = [f["label"] for f in r["findings"]]
            print(f"  {r['repo']}#{r['pr']}  {labels}")
        print("\ntools granted per arm:")
        for t in READ_ONLY_TOOLS:
            print(f"  {t}")
        print("\nno --yolo, no GitHub write verbs, --permission-mode plan")
        return

    def one(rec):
        repo_dir = args.apps_dir if rec["repo"].endswith("/apps") else args.services_dir
        url = f"https://github.com/{rec['repo']}/pull/{rec['pr']}"
        row = {"repo": rec["repo"], "pr": rec["pr"], "head_sha": rec["head_sha"]}
        for arm in ("S", "G"):
            res = run_arm(url, arm, repo_dir, args.model, args.timeout)
            row[arm] = {
                "findings": parse_findings(res["last"]),
                "skills_invoked": res["skills"],
                "cost": res["cost"], "turns": res["turns"],
                "seconds": res["seconds"], "error": res["error"],
                "last": res["last"][:4000],
            }
            # A posted review would appear as a tool_use, not merely as text: the
            # prompt itself says "do not run `gh pr review`", and that sentence is
            # echoed back in the stream. Matching raw text flagged every single run.
            if res.get("write_attempt"):
                row[arm]["WARNING"] = f"write verb invoked: {res['write_attempt']}"
        return row

    out = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(one, r): r for r in selected}
        for n, f in enumerate(as_completed(futs), 1):
            rec = futs[f]
            try:
                row = f.result()
            except Exception as e:
                row = {"repo": rec["repo"], "pr": rec["pr"],
                       "error": f"{type(e).__name__}: {e}"}
            out.append(row)
            s = len(row.get("S", {}).get("findings", []))
            g = len(row.get("G", {}).get("findings", []))
            print(f"  [{n}/{len(selected)}] {rec['repo']}#{rec['pr']} S={s} G={g}",
                  file=sys.stderr)
            (LOCAL / "suite_b.json").write_text(json.dumps(out, indent=2))

    (LOCAL / "suite_b.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {LOCAL / 'suite_b.json'}")
    print(f"total cost ${sum((r.get(a) or {}).get('cost') or 0 for r in out for a in 'SG'):.2f}")


if __name__ == "__main__":
    main()
