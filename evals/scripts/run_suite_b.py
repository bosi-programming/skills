#!/usr/bin/env python3
"""Runs Suite B: two review arms over the same real pull requests.

- arm S: the review skill alone, the current internal standard
- arm G: the same skill with the two epistemic gates loaded

Macroscope's findings are already on each PR and are not re-run; they are read from
the mined file as the reference.

SAFETY. `acme-pr-review --yolo` is built to post its review to GitHub without
asking. Nothing here may write to a real pull request, so this runner:

  - never passes --yolo,
  - tells the agent in the prompt to post nothing,
  - withholds every tool that could write to GitHub, allowing only read-only
    `gh api` and local git reads,
  - runs with --permission-mode plan so edits and writes are refused outright.

Read `--dry-run` output and confirm the tool grants before running this for real.
"""

import argparse
import json
import pathlib
import subprocess
import sys

LOCAL = pathlib.Path(__file__).resolve().parents[1] / ".local"

PROMPT = """Review pull request {url} for correctness defects.

Do NOT post anything to GitHub. Do not run `gh pr review`, `gh pr comment`, or any
write API call. Produce your findings here as text only.

Report every finding in exactly this format, one per line, and nothing else:

SEVERITY | path/to/file.ext:LINE | one sentence describing the defect

Use high, medium or low for SEVERITY. The path must be the real repository path and
the line must be a line that exists in the file at this pull request's head commit.
If you find no defects, write: NO FINDINGS
"""

# Read-only. No `gh pr review`, no `gh pr comment`, no write verbs.
SAFE_TOOLS = [
    "Read", "Glob", "Grep",
    "Bash(gh api:*)",
    "Bash(gh pr view:*)",
    "Bash(gh pr diff:*)",
    "Bash(git log:*)",
    "Bash(git show:*)",
    "Bash(git diff:*)",
    "Bash(git ls-tree:*)",
]

GATES = ["bosi-programming-skills:objectum", "bosi-programming-skills:epistemic-action"]


def run_arm(url, arm, model, repo_dir, timeout):
    prompt = PROMPT.format(url=url)
    if arm == "G":
        prompt = (
            "Before you answer, apply the objectum and epistemic-action gates to your "
            "own draft: every finding you report must cite a file and line you have "
            "actually opened and read at this commit. Cut any finding you cannot "
            "ground that way.\n\n" + prompt
        )
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--permission-mode", "plan",
        "--allowedTools", *SAFE_TOOLS,
    ]
    r = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, cwd=repo_dir
    )
    return r.stdout.strip(), r.returncode


FINDING = None


def parse(text):
    import re
    pat = re.compile(r"^\s*(high|medium|low)\s*\|\s*([^|]+?):(\d+)\s*\|\s*(.+)$",
                     re.I | re.M)
    return [
        {"severity": m.group(1).lower(), "path": m.group(2).strip(),
         "line": int(m.group(3)), "body": m.group(4).strip()}
        for m in pat.finditer(text)
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prs", type=int, default=10)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--apps-dir", default=str(pathlib.Path.home() / "dev/acme/apps"))
    ap.add_argument("--services-dir", default=str(pathlib.Path.home() / "dev/acme/services"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    findings = json.loads((LOCAL / "macroscope" / "findings.json").read_text())
    labelled = [
        r for r in findings
        if any(f["label"] in ("confirmed", "false_positive") for f in r["findings"])
    ][: args.prs]

    print(f"{len(labelled)} labelled PRs selected", file=sys.stderr)
    if args.dry_run:
        for r in labelled:
            kinds = [f["label"] for f in r["findings"]]
            print(f"  {r['repo']}#{r['pr']}  {kinds}")
        print("\ntools granted to each arm:")
        for t in SAFE_TOOLS:
            print(f"  {t}")
        print("\nno --yolo, no write verbs, --permission-mode plan")
        return

    out = []
    for rec in labelled:
        repo_dir = args.apps_dir if rec["repo"].endswith("/apps") else args.services_dir
        url = f"https://github.com/{rec['repo']}/pull/{rec['pr']}"
        row = {"repo": rec["repo"], "pr": rec["pr"], "head_sha": rec["head_sha"]}
        for arm in ("S", "G"):
            print(f"  {url} arm {arm}", file=sys.stderr)
            try:
                text, code = run_arm(url, arm, args.model, repo_dir, args.timeout)
            except subprocess.TimeoutExpired:
                text, code = "", -1
            row[arm] = {"raw": text, "exit": code, "findings": parse(text)}
        out.append(row)
        (LOCAL / "suite_b.json").write_text(json.dumps(out, indent=2))

    print(f"\nwrote {LOCAL / 'suite_b.json'}")


if __name__ == "__main__":
    main()
