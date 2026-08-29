#!/usr/bin/env python3
"""Mines labelled Macroscope findings from Acme pull requests.

A Macroscope finding on its own is another model's output, not ground truth. What
turns one into a label is a human replying to it. This script collects the findings,
attaches the human replies, and writes the pair out. It applies a coarse heuristic
label as a starting point and records that the label came from a heuristic; nothing
downstream should treat those as confirmed until a person has read them.

Output goes to evals/.local/macroscope/, which is gitignored. The findings quote
private code and must not reach a commit.
"""

import argparse
import json
import pathlib
import subprocess
import sys

REPOS = ["acme/apps", "acme/services"]
BOT = "macroscopeapp[bot]"
FINDING_MARKER = '"kind":"code_review"'

OUT = pathlib.Path(__file__).resolve().parents[1] / ".local" / "macroscope"

AGREE = [
    "agreed", "agree", "good catch", "nice catch", "you're right", "youre right",
    "fixed", "fixing", "will fix", "done", "addressed", "makes sense", "valid",
]
DISMISS = [
    "not an issue", "false positive", "intentional", "by design", "wontfix",
    "won't fix", "wont fix", "incorrect", "this is wrong", "not applicable",
    "n/a", "disagree", "no, ", "that's not", "thats not",
]


def gh(path):
    r = subprocess.run(
        ["gh", "api", path, "--paginate"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None
    # --paginate concatenates one JSON array per page, so the output is not a
    # single document once a result runs past page one.
    chunks, dec = [], json.JSONDecoder()
    s, i = r.stdout, 0
    while i < len(s):
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s):
            break
        v, i = dec.raw_decode(s, i)
        chunks.extend(v if isinstance(v, list) else [v])
    return chunks


def is_bot(login):
    return login.endswith("[bot]") or login in {"acme-ops"}


def mine(repo, limit):
    prs = gh(f"repos/{repo}/pulls?state=closed&per_page=100") or []
    out = []
    for pr in prs[:limit]:
        n = pr["number"]
        comments = gh(f"repos/{repo}/pulls/{n}/comments?per_page=100") or []
        findings = [
            c for c in comments
            if c["user"]["login"] == BOT and FINDING_MARKER in (c.get("body") or "")
        ]
        if not findings:
            continue
        by_id = {c["id"]: c for c in comments}
        record = {"repo": repo, "pr": n, "head_sha": pr["head"]["sha"], "findings": []}
        for f in findings:
            replies = [
                c for c in comments
                if c.get("in_reply_to_id") == f["id"] and not is_bot(c["user"]["login"])
            ]
            label, why = "unlabelled", None
            if replies:
                text = " ".join((c.get("body") or "").lower() for c in replies)
                if any(k in text for k in DISMISS):
                    label, why = "false_positive", "heuristic"
                elif any(k in text for k in AGREE):
                    label, why = "confirmed", "heuristic"
                else:
                    label, why = "needs_read", "no keyword matched"
            record["findings"].append({
                "id": f["id"],
                "path": f.get("path"),
                "line": f.get("line") or f.get("original_line"),
                "body": f.get("body"),
                "replies": [
                    {"author": c["user"]["login"], "body": c.get("body")} for c in replies
                ],
                "label": label,
                "label_source": why,
            })
        out.append(record)
        print(f"  {repo}#{n}: {len(record['findings'])} finding(s)", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="PRs to sweep per repo")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    everything = []
    for repo in REPOS:
        print(f"sweeping {repo}", file=sys.stderr)
        everything.extend(mine(repo, args.limit))

    (OUT / "findings.json").write_text(json.dumps(everything, indent=2))

    counts = {"confirmed": 0, "false_positive": 0, "needs_read": 0, "unlabelled": 0}
    for rec in everything:
        for f in rec["findings"]:
            counts[f["label"]] += 1
    labelled_prs = [
        r for r in everything
        if any(f["label"] in ("confirmed", "false_positive", "needs_read")
               for f in r["findings"])
    ]

    print(f"\nPRs with findings: {len(everything)}")
    print(f"PRs with a human reply to a finding: {len(labelled_prs)}")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nwrote {OUT / 'findings.json'}")
    if len(labelled_prs) < 10:
        print("\nFewer than 10 labelled PRs. Re-run with a larger --limit.")


if __name__ == "__main__":
    main()
